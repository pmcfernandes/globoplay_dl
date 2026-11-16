#!/usr/bin/env python3
"""Download videos from Globoplay (globoplay.globo.com) with yt-dlp.

Only downloads content you are allowed to access. DRM-protected and
subscription-gated streams are not supported; respect Globo's terms of
service and copyright law.

Usage:
    python globoplay_dl.py URL [URL ...]
    python globoplay_dl.py URL -q 720 --subtitles
    python globoplay_dl.py --queue list.txt -d downloads
    python globoplay_dl.py URL --cookies-from-browser chrome
"""

from __future__ import annotations

import argparse
import http.cookiejar
import re
import sys
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    sys.exit(
        "yt-dlp is required. Install it with:\n\n    pip install yt-dlp\n"
    )

GLOBOPLAY_URL = re.compile(
    r"^https?://(?:www\.)?(?:globoplay\.globo\.com|globo\.com)/",
    re.IGNORECASE,
)

# Named quality presets -> yt-dlp format selectors.
QUALITY_PRESETS = {
    "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
    "worst": "worstvideo+worstaudio/worst",
    "2160": "bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[height<=2160]",
    "1080": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]",
    "720": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]",
    "480": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]",
    "360": "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360]",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download videos from Globoplay.",
        epilog="Example: python globoplay_dl.py "
        "https://globoplay.globo.com/v/12345678/ -q 720 --subtitles",
    )
    parser.add_argument(
        "urls",
        nargs="*",
        metavar="URL",
        help="Globoplay video URL(s) to download",
    )
    parser.add_argument(
        "--queue",
        metavar="FILE",
        help="text file of URLs to download, one per line (# starts a comment)",
    )
    parser.add_argument(
        "-d",
        "--output-dir",
        metavar="DIR",
        help="directory to save downloads into (created if missing)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="%(title)s [%(id)s].%(ext)s",
        help="output filename template (default: %%(title)s [%%(id)s].%%(ext)s)",
    )
    parser.add_argument(
        "-q",
        "--quality",
        default="best",
        help="quality preset (%s) or a raw yt-dlp format string"
        % ", ".join(QUALITY_PRESETS),
    )
    parser.add_argument(
        "--subtitles",
        action="store_true",
        help="download subtitles along with the video",
    )
    parser.add_argument(
        "--all-subs",
        action="store_true",
        help="download every available subtitle track",
    )
    parser.add_argument(
        "--audio-only",
        action="store_true",
        help="download only the audio track (m4a)",
    )
    parser.add_argument(
        "--list-formats",
        action="store_true",
        help="list available formats and exit without downloading",
    )
    parser.add_argument(
        "--cookies",
        metavar="FILE",
        help="Netscape-format cookies file for logged-in content",
    )
    parser.add_argument(
        "--cookies-from-browser",
        metavar="BROWSER",
        help="read cookies from a browser (chrome, firefox, edge, ...)",
    )
    parser.add_argument(
        "--glbid",
        metavar="TOKEN",
        help="Globo session token (GLBID cookie value) for logged-in content",
    )
    parser.add_argument(
        "--throttle",
        type=float,
        metavar="BYTES",
        help="limit download rate, e.g. 2M for 2 MB/s",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="overwrite existing files instead of skipping them",
    )
    return parser.parse_args(argv)


def validate_urls(urls: list[str]) -> None:
    bad = [u for u in urls if not GLOBOPLAY_URL.match(u)]
    if bad:
        for url in bad:
            print(f"warning: {url!r} does not look like a Globoplay URL", file=sys.stderr)


def build_outtmpl(args: argparse.Namespace) -> str:
    if not args.output_dir:
        return args.output
    return str(Path(args.output_dir) / args.output)


def read_queue(path: str) -> list[str]:
    queue_file = Path(path)
    if not queue_file.is_file():
        sys.exit(f"error: queue file not found: {path}")
    urls = []
    # utf-8-sig: strip a BOM so a leading "# comment" still parses as a comment
    for line in queue_file.read_text(encoding="utf-8-sig").splitlines():
        entry = line.strip()
        if entry and not entry.startswith("#"):
            urls.append(entry)
    return urls


def collect_urls(args: argparse.Namespace) -> list[str]:
    urls = list(args.urls)
    if args.queue:
        urls.extend(read_queue(args.queue))
    return urls


def build_opts(args: argparse.Namespace) -> dict:
    if args.audio_only:
        fmt = "bestaudio[ext=m4a]/bestaudio/best"
    elif args.quality in QUALITY_PRESETS:
        fmt = QUALITY_PRESETS[args.quality]
    else:
        fmt = args.quality

    opts: dict = {
        "format": fmt,
        "outtmpl": build_outtmpl(args),
        "noplaylist": True,
        "ignoreerrors": False,
        "no_warnings": False,
        "retries": 5,
        "fragment_retries": 5,
        "concurrent_fragment_downloads": 4,
        "progress_hooks": [progress_hook],
        "postprocessors": [],
        "quiet": False,
        "noprogress": False,
    }

    if args.audio_only:
        opts["postprocessors"].append(
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "m4a",
            }
        )
    else:
        # Merge to mp4 when ffmpeg is available.
        opts["merge_output_format"] = "mp4"

    if args.all_subs:
        opts["writesubtitles"] = True
        opts["subtitleslangs"] = ["all"]
        opts["postprocessors"].append({"key": "FFmpegEmbedSubtitle"})
    elif args.subtitles:
        opts["writesubtitles"] = True
        opts["subtitleslangs"] = ["pt-BR", "pt", "en"]
        opts["postprocessors"].append({"key": "FFmpegEmbedSubtitle"})

    if args.cookies:
        opts["cookiefile"] = args.cookies
    if args.cookies_from_browser:
        opts["cookiesfrombrowser"] = (args.cookies_from_browser,)

    if args.throttle:
        opts["ratelimit"] = int(args.throttle)

    if args.list_formats:
        opts["listformats"] = True

    if args.overwrite:
        opts["overwrites"] = True
    else:
        opts["nooverwrites"] = True

    return opts


def progress_hook(d: dict) -> None:
    if d["status"] != "downloading":
        return
    total = d.get("total_bytes") or d.get("total_bytes_estimate")
    done = d.get("downloaded_bytes", 0)
    if not total:
        return
    pct = done / total * 100
    speed = d.get("speed")
    eta = d.get("eta")
    parts = [f"  {pct:5.1f}%  {done / 1e6:.1f}/{total / 1e6:.1f} MB"]
    if speed:
        parts.append(f"{speed / 1e6:.2f} MB/s")
    if eta is not None:
        parts.append(f"eta {eta}s")
    print("\r" + "  ".join(parts), end="", flush=True)


def inject_glbid(ydl: "yt_dlp.YoutubeDL", token: str) -> None:
    """Give the extractor a Globo session token so it can authenticate.

    GloboIE reads the GLBID cookie via _get_cookies('https://globo.com') and
    forwards it as a Bearer token to the playback API.
    """
    ydl.cookiejar.set_cookie(
        http.cookiejar.Cookie(
            version=0,
            name="GLBID",
            value=token,
            port=None,
            port_specified=False,
            domain=".globo.com",
            domain_specified=True,
            domain_initial_dot=True,
            path="/",
            path_specified=True,
            secure=True,
            expires=None,
            discard=True,
            comment=None,
            comment_url=None,
            rest={},
            rfc2109=False,
        )
    )


def download(url: str, opts: dict, glbid: str | None = None) -> bool:
    print(f"\n==> {url}")
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            if glbid:
                inject_glbid(ydl, glbid)
            ydl.download([url])
        return True
    except yt_dlp.utils.DownloadError as exc:
        message = str(exc)
        print(f"\nerror: {message}", file=sys.stderr)
        hint = classify_error(message)
        if hint:
            print(f"hint: {hint}", file=sys.stderr)
        return False


def classify_error(message: str) -> str | None:
    lowered = message.lower()
    if "drm" in lowered or "protected" in lowered:
        return (
            "this stream is DRM-protected and cannot be downloaded; "
            "only free, unprotected Globoplay videos are supported"
        )
    if "login-required" in lowered or "401" in lowered or "unauthorized" in lowered:
        return (
            "Globo requires a signed-in session for playback (API said "
            "'login-required'). Log in to globo.com in your browser, then "
            "re-run with --cookies-from-browser <browser> (firefox is the "
            "most reliable on Windows), or pass a cookies file with --cookies, "
            "or the session token alone with --glbid. You need an account "
            "with access to this video."
        )
    if "sign in" in lowered or "login" in lowered or "not available in your country" in lowered:
        return (
            "content may require a Globo account or is geo-blocked; "
            "try --cookies or --cookies-from-browser"
        )
    if "private" in lowered or "subscription" in lowered:
        return "this video is behind a subscription or is private"
    return None


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    urls = collect_urls(args)
    if not urls:
        sys.exit("error: no URLs given. Pass URLs as arguments and/or use --queue FILE.")
    validate_urls(urls)

    if args.output_dir:
        Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    opts = build_opts(args)
    print(f"yt-dlp {yt_dlp.version.__version__}  |  output: {opts['outtmpl']}")

    authenticated = bool(args.glbid or args.cookies or args.cookies_from_browser)
    if not authenticated:
        print(
            "note: no login configured. Globoplay now requires a signed-in "
            "session for playback; if you hit a 401, pass "
            "--cookies-from-browser <browser>, --cookies FILE, or --glbid TOKEN.",
            file=sys.stderr,
        )

    failures = 0
    for url in urls:
        if not download(url, opts, glbid=args.glbid):
            failures += 1

    if failures:
        print(f"\n{failures} of {len(urls)} download(s) failed.", file=sys.stderr)
        return 1
    print(f"\nDone. {len(urls)} download(s) completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Globoplay Downloader

Download videos from [Globoplay](https://globoplay.globo.com) from the command line.

Built on `yt-dlp`'s Globoplay extractor, so it inherits format selection, subtitles, HLS/DASH handling, and cookie-based authentication.

> Use this only for content you are allowed to save, and respect Globo's terms of service and copyright law.

## Requirements

- Python 3.9+ (verified on 3.12)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) (installed via `requirements.txt`)
- [ffmpeg](https://ffmpeg.org/) on your `PATH` — needed to merge video/audio and embed subtitles

  ```powershell
  winget install Gyan.FFmpeg
  ```

## Install

```powershell
pip install -r requirements.txt
```

## Usage

```powershell
python globoplay_dl.py <URL> [<URL> ...]
```

Examples:

```powershell
# Download at the best available quality
python globoplay_dl.py "https://globoplay.globo.com/v/15170205/"

# Cap at 720p and pull subtitles
python globoplay_dl.py "https://globoplay.globo.com/v/15170205/" -q 720 --subtitles

# Audio only (m4a)
python globoplay_dl.py "https://globoplay.globo.com/v/15170205/" --audio-only

# Batch-download a list of URLs into a folder
python globoplay_dl.py --queue list.txt -d downloads

# See what's available before downloading
python globoplay_dl.py "https://globoplay.globo.com/v/15170205/" --list-formats
```

## Authentication

Most Globoplay videos need a signed-in session. Without one, the playback API answers
`401` with `{"code":"login-required"}`.

Sign in to `globo.com` in a browser, then use one of:

```powershell
# Reuse your browser session (firefox is the most reliable on Windows)
python globoplay_dl.py URL --cookies-from-browser firefox

# Or export a Netscape cookies.txt and pass it
python globoplay_dl.py URL --cookies cookies.txt

# Or pass just the GLBID session token (DevTools > Application > Cookies > globo.com)
python globoplay_dl.py URL --glbid <token>
```

Your account needs access to the video you are downloading.

## Options

| Option | Description |
| --- | --- |
| `-d, --output-dir DIR` | Directory to save downloads into (created if missing) |
| `--queue FILE` | Text file of URLs to download, one per line (`#` starts a comment) |
| `-o, --output TEMPLATE` | Output filename template (default `%(title)s [%(id)s].%(ext)s`) |
| `-q, --quality PRESET` | `best`, `worst`, `2160`, `1080`, `720`, `480`, `360`, or a raw yt-dlp format string |
| `--subtitles` | Download subtitles (pt-BR, pt, en) and embed them |
| `--all-subs` | Download and embed every available subtitle track |
| `--audio-only` | Download only the audio track as m4a |
| `--list-formats` | List available formats without downloading |
| `--cookies FILE` | Netscape-format cookies file |
| `--cookies-from-browser BROWSER` | Read cookies from `chrome`, `firefox`, `edge`, ... |
| `--glbid TOKEN` | Globo session token (the `GLBID` cookie value) |
| `--throttle BYTES` | Rate limit, e.g. `2M` for 2 MB/s |
| `--overwrite` | Overwrite existing files (default is to skip them) |

## Limitations

- **DRM-protected streams are not supported.** If Globo flags a stream as DRM-locked, the script refuses rather than working around it.
- **Subscription-gated videos** require an account whose plan includes them.
- **Geo-blocked videos** require a connection from an allowed region.

## Troubleshooting

**`401 Unauthorized` / `login-required`**
No valid session. Use one of the authentication methods above.

**`cookiesfrombrowser` fails on Chrome (Windows)**
Chrome 127+ encrypts cookies with app-bound encryption that yt-dlp cannot read. Use
`--cookies-from-browser firefox`, or export cookies manually and pass `--cookies`.

**`ffmpeg is not installed` / formats fail to merge**
Install ffmpeg and make sure it is on your `PATH` (`ffmpeg -version` should work in a
new terminal).

**`DRM detected`**
The stream is protected and cannot be downloaded.

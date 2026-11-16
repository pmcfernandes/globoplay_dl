#!/usr/bin/env bash
# Create a venv, install requirements, then run globoplay_dl.py with any arguments.

cd "$(dirname "${BASH_SOURCE[0]}")" || exit 1

VENV=".venv"
VENV_PY="$VENV/bin/python"

# --- locate a Python interpreter ---
if command -v python3 >/dev/null 2>&1; then
    PY=python3
elif command -v python >/dev/null 2>&1; then
    PY=python
else
    echo "Python was not found on PATH. Install Python 3 and try again."
    exit 1
fi

# --- create the virtual environment on first run ---
# A failed create (e.g. missing ensurepip) leaves .venv/bin/python behind, so
# also verify pip works before trusting an existing venv.
if [ -x "$VENV_PY" ] && ! "$VENV_PY" -m pip --version >/dev/null 2>&1; then
    echo "The virtual environment in $VENV is incomplete (pip is missing)."
    echo "Remove it and re-run this script:   rm -rf \"$VENV\""
    exit 1
fi

if [ ! -x "$VENV_PY" ]; then
    echo "Creating virtual environment in $VENV ..."
    if ! "$PY" -m venv "$VENV"; then
        echo "Failed to create the virtual environment."
        exit 1
    fi
fi

# --- install / refresh dependencies ---
echo "Installing dependencies ..."
if ! "$VENV_PY" -m pip install --disable-pip-version-check --quiet -r requirements.txt; then
    echo "Failed to install requirements."
    exit 1
fi

# --- no arguments: show how to use it ---
if [ $# -eq 0 ]; then
    echo
    echo "Usage: run.sh <globoplay-url> [options]"
    echo
    echo "Example:"
    echo "  run.sh https://globoplay.globo.com/v/15170205/ -q 720 --subtitles"
    echo
    echo 'Run "run.sh --help" for all options.'
    exit 1
fi

# --- run the downloader, forwarding every argument ---
"$VENV_PY" globoplay_dl.py "$@"
exit $?

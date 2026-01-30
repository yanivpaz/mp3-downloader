#!/usr/bin/env bash
# check_deps.sh - simple dependency checker for mp3-downloader
# Checks for: ffmpeg, yt-dlp (command or Python module), and deno/node (JS runtime optional)

set -euo pipefail

missing=0

echo "Checking dependencies for mp3-downloader..."

echo -n "- ffmpeg: "
if command -v ffmpeg >/dev/null 2>&1; then
  echo "FOUND ($(command -v ffmpeg))"
else
  echo "MISSING"
  echo "  -> Install: sudo apt install ffmpeg  # Debian/Ubuntu"
  missing=1
fi

echo -n "- yt-dlp (cli): "
if command -v yt-dlp >/dev/null 2>&1; then
  echo "FOUND ($(command -v yt-dlp))"
else
  echo "NOT FOUND as a command"
  echo -n "  - yt-dlp as Python module: "
  if python3 -c "import yt_dlp" >/dev/null 2>&1; then
    echo "FOUND as Python module"
  else
    echo "MISSING"
    echo "  -> Install: python3 -m pip install --user yt-dlp"
    echo "  (or use a virtualenv: python3 -m venv .venv && source .venv/bin/activate && pip install yt-dlp)"
    missing=1
  fi
fi

echo -n "- JS runtime (deno/node) (optional, avoids yt-dlp JS runtime warnings): "
if command -v deno >/dev/null 2>&1; then
  echo "deno FOUND ($(command -v deno))"
elif command -v node >/dev/null 2>&1; then
  echo "node FOUND ($(command -v node))"
else
  echo "NOT FOUND (optional)"
  echo "  -> Install to avoid warnings (optional): https://deno.land/ or https://nodejs.org/"
fi

if [ "$missing" -eq 1 ]; then
  echo
  echo "Some required dependencies are missing. Follow the suggestions above and re-run this script."
  exit 2
else
  echo
  echo "All required dependencies are available. You're ready to run ./download_mp3.py"
  exit 0
fi

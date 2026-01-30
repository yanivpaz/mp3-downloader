# mp3-downloader

A small Python utility to download YouTube video(s) or playlists and save them as MP3 files.

## ⚙️ Requirements

- Python 3.8+
- ffmpeg installed and in PATH (e.g., `sudo apt install ffmpeg` on Debian/Ubuntu)
- Python package: `yt-dlp` (install with `pip install yt-dlp`)

## ✅ Installation

1. Install ffmpeg (see your OS package manager).
2. Install `yt-dlp`:

```bash
pip install yt-dlp
```

## 🚀 Usage

```bash
# single video to ./music
python3 download_mp3.py "https://youtu.be/VIDEO_ID" -o ./music

# playlist (downloads all items) to ./albums
python3 download_mp3.py "https://www.youtube.com/playlist?list=..." -o ./albums

# disable playlist handling (download only the supplied video)
python3 download_mp3.py "https://youtu.be/VIDEO_ID" -o ./music --no-playlist

# set mp3 bitrate
python3 download_mp3.py "https://youtu.be/VIDEO_ID" -o ./music --quality 256
```

Files will be saved as `%(playlist_index)s - %(title)s.mp3` (playlist index is omitted for single videos).

> ⚠️ Please ensure you have the right to download and convert the content. This tool is intended for downloading audio you own or have permission to use.

---

## ✅ Tested example

I tested the script on the playlist:

```text
https://www.youtube.com/playlist?list=PL2l4T5NjtOsrwnDXVJ_yL5ON86-4ERK14
```

and saved the MP3s to the mounted Windows folder:

```bash
/mnt/c/mp3
```

Result: **15** items downloaded and converted successfully to MP3.

> Note: during the run `yt-dlp` produced a warning about a missing JS runtime (it used the default `deno`). The download completed fine, but you may install `deno` or `node` to avoid the warning and ensure full extraction support.

## 🔧 Commands used (examples)

- Install system ffmpeg (Debian/Ubuntu):

```bash
sudo apt update && sudo apt install -y ffmpeg
```

- Install `yt-dlp` for current user (no sudo):

```bash
python3 -m pip install --user yt-dlp
```

- Or use the project virtualenv (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install yt-dlp
```

- Download playlist to `/mnt/c/mp3`:

```bash
python3 download_mp3.py "https://www.youtube.com/playlist?list=PL2l4T5NjtOsrwnDXVJ_yL5ON86-4ERK14" -o /mnt/c/mp3
```

## ❓ Troubleshooting

- If you see "FFmpeg not found", install `ffmpeg` and ensure it's in your PATH. The script exits with a helpful message if `ffmpeg` is missing.
- If `yt-dlp` is missing, install it using `pip install --user yt-dlp` or inside a virtualenv.
- If extraction shows a JS runtime warning, install `deno` or `node` and add to your PATH.

## 🔍 Helper: `check_deps.sh`

A small helper script `check_deps.sh` is included to verify common requirements:

```bash
# make executable (if needed)
chmod +x check_deps.sh
# run the check
./check_deps.sh
```

It checks for `ffmpeg`, `yt-dlp` (either as a CLI or Python module), and an optional JS runtime (`deno` or `node`) and prints install hints if something is missing.

---

Made with ❤️ using `yt-dlp` and `ffmpeg`.  
If you'd like, open an issue or send a PR to add features such as metadata embedding, filename sanitization, or a batch mode for URL lists.

---

## 🖥️ Web UI (React)

A small React UI and Flask backend are included to start downloads from your browser.

How to run locally:

1. Install backend deps (recommended inside a virtualenv):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r server_requirements.txt
```

2. Start the server (default port 5000):

```bash
python3 server.py
```

3. Start the frontend (requires Node.js / npm):

```bash
cd web
npm install
npm run dev
```

Open the UI in your browser (Vite prints the local port, usually `http://localhost:5173`). The UI asks for a YouTube URL and a target folder (default: `/mnt/c/mp3`) and starts the download when you click **Download**. You can watch logs in the interface.

### Start / Stop helper scripts

For convenience there are two scripts at the project root to start and stop the services:

```bash
# start both backend (Flask) and frontend (Vite) and save logs/pids
./start_mp3_services.sh

# stop the services
./stop_mp3_services.sh
```

Logs are available in `./logs/` (created by `start_mp3_services.sh`). These scripts were moved to the repository root for easier access and are executable (`chmod +x ./start_mp3_services.sh`).

## API: list jobs

A new endpoint is available to list all jobs and their quick status:

- GET `/jobs` — returns JSON with all jobs:

```json
{
  "jobs": [
    {
      "job_id": "<uuid>",
      "pid": 12345,
      "running": true,
      "returncode": null,
      "log_tail": "...last ~50 lines of log..."
    }
  ]
}
```

This is useful to show a jobs dashboard or to poll status for multiple jobs programmatically.

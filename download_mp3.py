#!/usr/bin/env python3
"""download_mp3.py

Download YouTube video(s) (or playlists) as MP3 files into a target folder.

Examples:
  python3 download_mp3.py https://youtu.be/VIDEO_ID -o ./music
  python3 download_mp3.py PLAYLIST_URL -o ./albums --quality 256
"""

import argparse
import os
import sys
import shutil

try:
    from yt_dlp import YoutubeDL
except Exception:
    print("Missing dependency: yt-dlp. Install with: pip install yt-dlp")
    sys.exit(1)


def check_ffmpeg():
    if shutil.which("ffmpeg") is None:
        print("FFmpeg not found. Install ffmpeg (e.g. 'sudo apt install ffmpeg' or visit https://ffmpeg.org)")
        sys.exit(1)


def progress_hook(d):
    status = d.get('status')
    if status == 'downloading':
        p = d.get('_percent_str', '')
        sp = d.get('_speed_str', '')
        eta = d.get('_eta_str', '')
        fname = os.path.basename(d.get('filename', ''))
        print(f"Downloading {fname} {p} {sp} ETA {eta}", end='\r')
    elif status == 'finished':
        print(f"\nFinished downloading: {d.get('filename')}. Converting to mp3...")


def parse_args():
    parser = argparse.ArgumentParser(description="Download YouTube link(s) as MP3 files into a target folder.")
    parser.add_argument('urls', nargs='+', help='One or more YouTube URLs (video or playlist)')
    parser.add_argument('-o', '--output', default='.', help='Target folder to save MP3 files')
    parser.add_argument('--no-playlist', action='store_true', help='Do not download playlist items; treat input as single video')
    parser.add_argument('--quality', default='192', help='MP3 bitrate (e.g. 128, 192, 256, 320)')
    return parser.parse_args()


def main():
    args = parse_args()
    outdir = os.path.abspath(args.output)
    os.makedirs(outdir, exist_ok=True)

    check_ffmpeg()

    # Output template: keep playlist index if any for ordering
    outtmpl = os.path.join(outdir, '%(playlist_index)s - %(title)s.%(ext)s')

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': outtmpl,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': str(args.quality),
        }],
        'postprocessor_args': ['-ar', '44100'],
        'progress_hooks': [progress_hook],
        'ignoreerrors': True,
        'noplaylist': args.no_playlist,
        'quiet': False,
    }

    with YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download(args.urls)
        except KeyboardInterrupt:
            print('\nCancelled by user')
            sys.exit(1)
        except Exception as e:
            print(f"Error while downloading: {e}")
            sys.exit(1)


if __name__ == '__main__':
    main()

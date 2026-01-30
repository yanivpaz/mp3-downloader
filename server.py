#!/usr/bin/env python3
"""server.py

A lightweight Flask API to trigger `download_mp3.py` jobs from a React UI.

Endpoints:
- POST /download  -> start a job (returns job_id)
- GET  /status/<job_id> -> returns status and last log lines
- GET  /logs/<job_id> -> returns entire log file (if small)
"""

import os
import sys
import uuid
import json
import shutil
import subprocess
import threading
from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS

ROOT = os.path.dirname(os.path.abspath(__file__))
JOBS_DIR = os.path.join(ROOT, 'jobs')
SCRIPT_PATH = os.path.join(ROOT, 'download_mp3.py')

os.makedirs(JOBS_DIR, exist_ok=True)

# In-memory job registry to track Popen objects so we can reap and check status reliably.
# Note: this does not persist across server restarts (fallback checks still use /proc).
JOBS = {}

app = Flask(__name__)
CORS(app)


def check_deps():
    problems = []
    if shutil.which('ffmpeg') is None:
        problems.append('ffmpeg not found')
    try:
        import yt_dlp  # noqa: F401
    except Exception:
        problems.append('yt-dlp Python module not found')
    return problems


@app.route('/download', methods=['POST'])
def download():
    data = request.get_json() or {}
    url = data.get('url')
    out = data.get('output', '/mnt/c/mp3')

    if not url:
        return jsonify({'error': 'missing url parameter'}), 400

    # Check deps before starting
    deps = check_deps()
    if deps:
        return jsonify({'error': 'missing dependencies', 'details': deps}), 500

    os.makedirs(out, exist_ok=True)

    job_id = str(uuid.uuid4())
    job_dir = os.path.join(JOBS_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    log_path = os.path.join(job_dir, 'job.log')
    meta_path = os.path.join(job_dir, 'meta.json')

    # Construct command: use the same python executable running the server
    cmd = [sys.executable, SCRIPT_PATH, url, '-o', out]

    # Start the download process in background, redirecting output to log file
    with open(log_path, 'wb') as logf:
        p = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT, start_new_session=True)

    # Store process in-memory so we can reliably poll it and wait() to reap it.
    JOBS[job_id] = p

    meta = {'pid': p.pid, 'cmd': cmd}
    with open(meta_path, 'w') as f:
        json.dump(meta, f)

    # Start a watcher thread that waits for the process to finish and updates metadata.
    def _watch_job(jid, proc, mpath):
        try:
            rc = proc.wait()
        except Exception:
            rc = None
        try:
            with open(mpath) as mf:
                m = json.load(mf)
        except Exception:
            m = {}
        if rc is not None:
            m['returncode'] = rc
            with open(mpath, 'w') as mf:
                json.dump(m, mf)
        JOBS.pop(jid, None)

    t = threading.Thread(target=_watch_job, args=(job_id, p, meta_path), daemon=True)
    t.start()

    return jsonify({'job_id': job_id, 'pid': p.pid}), 202


def _tail(path, lines=200):
    try:
        with open(path, 'rb') as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            block = 1024
            data = b''
            while size > 0 and lines > 0:
                step = min(block, size)
                f.seek(size - step)
                chunk = f.read(step)
                data = chunk + data
                # crude: count newline occurrences
                lines = 200 - data.count(b'\n')
                size -= step
            return data.decode(errors='replace')
    except FileNotFoundError:
        return ''


@app.route('/status/<job_id>', methods=['GET'])
def status(job_id):
    job_dir = os.path.join(JOBS_DIR, job_id)
    if not os.path.isdir(job_dir):
        return jsonify({'error': 'job not found'}), 404
    meta_path = os.path.join(job_dir, 'meta.json')
    log_path = os.path.join(job_dir, 'job.log')
    if not os.path.exists(meta_path):
        return jsonify({'error': 'job metadata missing'}), 500
    with open(meta_path) as f:
        meta = json.load(f)
    pid = meta.get('pid')

    # Prefer in-memory Popen status (no zombies) when available
    running = False
    if job_id in JOBS:
        p = JOBS[job_id]
        rc = p.poll()
        if rc is None:
            running = True
        else:
            # Process finished; reap it and update metadata with return code
            try:
                p.wait(timeout=0)
            except Exception:
                pass
            meta['returncode'] = rc
            with open(meta_path, 'w') as f:
                json.dump(meta, f)
            # remove from registry to free memory
            JOBS.pop(job_id, None)
    else:
        # Fallback: check /proc for the pid (may be a running process started before server restart)
        running = os.path.exists(f'/proc/{pid}')

    tail = _tail(log_path)
    return jsonify({'job_id': job_id, 'pid': pid, 'running': running, 'returncode': meta.get('returncode'), 'log_tail': tail})


@app.route('/logs/<job_id>', methods=['GET'])
def logs(job_id):
    job_dir = os.path.join(JOBS_DIR, job_id)
    log_path = os.path.join(job_dir, 'job.log')
    if not os.path.exists(log_path):
        return jsonify({'error': 'log not found'}), 404
    # send as text file
    return send_file(log_path, mimetype='text/plain')


@app.route('/jobs', methods=['GET'])
def jobs():
    """List all jobs with basic status info and a short log tail."""
    result = []
    for jid in sorted(os.listdir(JOBS_DIR)):
        job_dir = os.path.join(JOBS_DIR, jid)
        if not os.path.isdir(job_dir):
            continue
        meta_path = os.path.join(job_dir, 'meta.json')
        log_path = os.path.join(job_dir, 'job.log')
        meta = {}
        if os.path.exists(meta_path):
            try:
                with open(meta_path) as f:
                    meta = json.load(f)
            except Exception:
                meta = {}
        pid = meta.get('pid')
        # determine running state
        running = False
        if jid in JOBS:
            p = JOBS[jid]
            rc = p.poll()
            running = (rc is None)
        else:
            running = bool(pid and os.path.exists(f'/proc/{pid}'))
        tail = _tail(log_path, lines=50)
        result.append({
            'job_id': jid,
            'pid': pid,
            'running': running,
            'returncode': meta.get('returncode'),
            'log_tail': tail,
        })

    return jsonify({'jobs': result})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting server on http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port)

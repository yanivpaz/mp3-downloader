#!/usr/bin/env bash
set -euo pipefail

# stop_mp3_services.sh
# Stops the Flask backend and the React (Vite) frontend started by start_mp3_services.sh

PROJECT_DIR="$HOME/mp3-downloader"
SERVER_PID="$PROJECT_DIR/server.pid"
VITE_PID="$PROJECT_DIR/vite.pid"
LOG_DIR="$PROJECT_DIR/logs"

stop_pidfile() {
  pidfile="$1"
  name="$2"
  if [ -f "$pidfile" ]; then
    pid=$(cat "$pidfile")
    if kill -0 "$pid" 2>/dev/null; then
      echo "Stopping $name (pid $pid)..."
      kill "$pid" || true
      sleep 1
      if kill -0 "$pid" 2>/dev/null; then
        echo "$name did not stop, sending SIGKILL..."
        kill -9 "$pid" || true
      fi
    else
      echo "$name process not running (stale pid file)."
    fi
    rm -f "$pidfile"
  else
    echo "No pidfile for $name: $pidfile"
  fi
}

stop_pidfile "$SERVER_PID" "Flask server"
stop_pidfile "$VITE_PID" "Vite dev server"

echo "Stopped services. Logs are in $LOG_DIR (if present)."
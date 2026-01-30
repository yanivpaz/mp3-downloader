#!/usr/bin/env bash
set -euo pipefail

# start_mp3_services.sh
# Starts the Flask backend and the React (Vite) frontend for the mp3-downloader project.
# Writes PID files to the project directory and logs to $PROJECT_DIR/logs

PROJECT_DIR="$HOME/mp3-downloader"
VENV="$PROJECT_DIR/.venv"
FRONTEND_DIR="$PROJECT_DIR/web"
LOG_DIR="$PROJECT_DIR/logs"
SERVER_PID="$PROJECT_DIR/server.pid"
VITE_PID="$PROJECT_DIR/vite.pid"

mkdir -p "$LOG_DIR"

start_server() {
  if [ -f "$SERVER_PID" ] && kill -0 "$(cat "$SERVER_PID")" 2>/dev/null; then
    echo "Flask server already running (pid $(cat "$SERVER_PID"))"
    return
  fi

  if [ -x "$VENV/bin/python" ]; then
    PY="$VENV/bin/python"
  else
    PY="$(command -v python3 || true)"
  fi

  if [ -z "$PY" ]; then
    echo "Python not found. Activate a virtualenv or install Python."
    return
  fi

  echo "Starting Flask server using $PY..."
  nohup "$PY" "$PROJECT_DIR/server.py" > "$LOG_DIR/server.log" 2>&1 &
  echo $! > "$SERVER_PID"
  echo "Flask server started (pid $(cat "$SERVER_PID")), logs: $LOG_DIR/server.log"
}

start_frontend() {
  if [ -f "$VITE_PID" ] && kill -0 "$(cat "$VITE_PID")" 2>/dev/null; then
    echo "Vite already running (pid $(cat "$VITE_PID"))"
    return
  fi

  # load nvm if available so npm uses the desired Node version
  if [ -s "$HOME/.nvm/nvm.sh" ]; then
    # shellcheck disable=SC1090
    . "$HOME/.nvm/nvm.sh"
    nvm use default >/dev/null 2>&1 || true
  fi

  if [ ! -d "$FRONTEND_DIR" ]; then
    echo "Frontend directory not found: $FRONTEND_DIR"
    return
  fi

  echo "Starting Vite dev server in $FRONTEND_DIR..."
  (cd "$FRONTEND_DIR" && nohup npm run dev > "$LOG_DIR/vite.log" 2>&1 &)
  # Wait a fraction for the child to start and capture its pid
  sleep 0.5
  # Find the most recent node process launched from the frontend dir
  VPID=$(pgrep -u "$USER" -f "node .*vite" | head -n 1 || true)
  if [ -n "$VPID" ]; then
    echo "$VPID" > "$VITE_PID"
    echo "Vite started (pid $VPID), logs: $LOG_DIR/vite.log"
  else
    echo "Could not detect Vite PID; check $LOG_DIR/vite.log for details"
  fi
}

start_server
start_frontend

echo "Done. Use ~/stop_mp3_services.sh to stop services."
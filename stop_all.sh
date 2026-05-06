#!/usr/bin/env bash
# stop_all.sh — Ferma backend FastAPI + frontend dev server avviati da start_all.sh.

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

stop_pid_file() {
  local label="$1" pidfile="$2"
  if [ -f "$pidfile" ]; then
    local pid
    pid=$(cat "$pidfile")
    if kill -0 "$pid" 2>/dev/null; then
      echo "→ Fermo $label (PID $pid)"
      kill "$pid" 2>/dev/null || true
      sleep 0.5
      kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null || true
    else
      echo "$label non in esecuzione (PID $pid orfano)"
    fi
    rm -f "$pidfile"
  else
    echo "$label: nessun PID file (non avviato o già fermato)"
  fi
}

stop_pid_file "Backend"  "$DIR/.backend.pid"
stop_pid_file "Frontend" "$DIR/.frontend.pid"

echo ""
echo "Done."

#!/usr/bin/env bash
# Lancia il backend FastAPI in dev mode.
# Uso: ./run.sh   (dalla root tm_project: bash api/run.sh)
set -e
cd "$(dirname "$0")"
if [ ! -f .deps_installed ]; then
  echo "Installing FastAPI deps..."
  ../venv/bin/pip install -r requirements.txt
  touch .deps_installed
fi
echo "Starting backend on http://127.0.0.1:8000"
../venv/bin/uvicorn main:app --reload --port 8000

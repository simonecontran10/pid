#!/usr/bin/env bash
# Avvia un server statico locale per testare il frontend.
# Mappa /data al folder data/ del progetto.
# Uso: bash frontend/serve.sh   poi apri http://127.0.0.1:5173
set -e
cd "$(dirname "$0")/.."
echo "Open http://127.0.0.1:5173/frontend/  in your browser"
python3 -m http.server 5173

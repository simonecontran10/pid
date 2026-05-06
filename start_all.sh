#!/usr/bin/env bash
# start_all.sh — Avvia backend FastAPI + frontend dev server in background.
#
# Uso:
#   bash start_all.sh           # avvia entrambi e apre il browser
#   bash start_all.sh --no-open # senza aprire il browser
#
# Per fermarli:
#   bash stop_all.sh
#
# Logs:
#   logs/backend.log  — output FastAPI
#   logs/frontend.log — output server frontend

set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

mkdir -p logs

NO_OPEN="${1:-}"

# --- 0. Verifica venv: se rotta (shebang sbagliato), ricostruisci ---
ensure_venv() {
  local need_recreate=0
  if [ ! -f "$DIR/venv/bin/python3" ] || [ ! -x "$DIR/venv/bin/python3" ]; then
    echo "→ venv mancante o corrotta — creo..."
    need_recreate=1
  elif ! "$DIR/venv/bin/python3" --version >/dev/null 2>&1; then
    echo "→ venv non funzionante (bad interpreter) — ricreo..."
    need_recreate=1
  elif [ -f "$DIR/venv/bin/pip" ] && ! head -1 "$DIR/venv/bin/pip" | grep -q "$DIR/venv/bin/python"; then
    # shebang del pip non punta alla venv corrente → venv spostata, ricrea
    echo "→ venv ha shebang errato (probabilmente spostata) — ricreo..."
    need_recreate=1
  fi
  if [ $need_recreate -eq 1 ]; then
    rm -rf "$DIR/venv"
    python3 -m venv "$DIR/venv"
    "$DIR/venv/bin/pip" install --upgrade pip > logs/setup.log 2>&1
    rm -f "$DIR/api/.deps_installed"
    rm -f "$DIR/.deps_main_installed"
  fi
  # Installa dipendenze principali (scraper) se mancanti
  if [ ! -f "$DIR/.deps_main_installed" ]; then
    echo "→ Installing scraper deps (requests, bs4, ecc.)..."
    "$DIR/venv/bin/pip" install requests beautifulsoup4 lxml pandas openpyxl >> logs/setup.log 2>&1
    touch "$DIR/.deps_main_installed"
  fi
  # Installa dipendenze API (FastAPI, uvicorn) se mancanti
  if [ ! -f "$DIR/api/.deps_installed" ] || ! "$DIR/venv/bin/python3" -c "import uvicorn" 2>/dev/null; then
    echo "→ Installing FastAPI deps..."
    "$DIR/venv/bin/pip" install -r "$DIR/api/requirements.txt" >> logs/setup.log 2>&1
    touch "$DIR/api/.deps_installed"
  fi
}

ensure_venv

# --- 1. Backend FastAPI (porta 8000) ---
if [ -f "$DIR/.backend.pid" ] && kill -0 "$(cat "$DIR/.backend.pid" 2>/dev/null)" 2>/dev/null; then
  echo "✓ Backend già in esecuzione (PID $(cat "$DIR/.backend.pid"))"
else
  echo "→ Avvio backend su http://127.0.0.1:8000"
  cd api
  nohup ../venv/bin/uvicorn main:app --port 8000 >> ../logs/backend.log 2>&1 &
  echo $! > "$DIR/.backend.pid"
  cd "$DIR"
  sleep 2
fi

# --- 2. Frontend dev server (porta 5173) ---
if [ -f "$DIR/.frontend.pid" ] && kill -0 "$(cat "$DIR/.frontend.pid" 2>/dev/null)" 2>/dev/null; then
  echo "✓ Frontend già in esecuzione (PID $(cat "$DIR/.frontend.pid"))"
else
  echo "→ Avvio frontend su http://127.0.0.1:5173/frontend/"
  cd "$DIR"
  # Server HTTP statico Python (serve la cartella tm_project/, quindi /frontend/ è raggiungibile)
  nohup python3 -m http.server 5173 --bind 127.0.0.1 > logs/frontend.log 2>&1 &
  echo $! > "$DIR/.frontend.pid"
  sleep 1
fi

# --- 3. Healthcheck ---
echo ""
echo "===================="
echo "Stato servizi"
echo "===================="
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/ | grep -q "200"; then
  echo "✓ Backend OK   → http://127.0.0.1:8000"
else
  echo "⚠ Backend non risponde — controlla logs/backend.log"
fi
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5173/frontend/ | grep -q "200"; then
  echo "✓ Frontend OK  → http://127.0.0.1:5173/frontend/"
else
  echo "⚠ Frontend non risponde — controlla logs/frontend.log"
fi
echo ""
echo "PID:  backend=$(cat "$DIR/.backend.pid" 2>/dev/null) frontend=$(cat "$DIR/.frontend.pid" 2>/dev/null)"
echo "Stop: bash stop_all.sh"
echo "Log:  tail -f logs/backend.log  |  tail -f logs/frontend.log"

# --- 4. Apri browser ---
if [ "$NO_OPEN" != "--no-open" ]; then
  sleep 1
  open "http://127.0.0.1:5173/frontend/"
fi

#!/usr/bin/env bash
# run_finalize.sh — Esegue in sequenza tutti gli step post-scrape.
#
# Uso (UNA SOLA RIGA):
#     bash run_finalize.sh
# oppure
#     caffeinate -i bash run_finalize.sh
#
# Cosa fa, in ordine:
#   1) enrich_sortitoutsi.py  (fix club placeholder + foto curate)
#   2) import_wyscout.py      (match Wyscout finale)
#   3) download_photos.py     (foto e loghi mancanti)
#   4) run_stats.py           (presenze stagione)

set -e
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
  echo "[FATAL] venv/ mancante. Crealo: python3 -m venv venv && source venv/bin/activate && pip install requests beautifulsoup4 lxml pandas openpyxl"
  exit 1
fi
source venv/bin/activate

# Verifica/installa dipendenze necessarie
echo "Verifica dipendenze..."
python3 -c "import requests, bs4, lxml, pandas, openpyxl" 2>/dev/null || {
  echo "  installazione dipendenze mancanti..."
  pip install --quiet requests beautifulsoup4 lxml pandas openpyxl
}

step() {
  echo ""
  echo "============================================================"
  echo "  $1"
  echo "============================================================"
}

step "1/4  enrich_sortitoutsi.py  (fix club + foto curate)"
python3 enrich_sortitoutsi.py

step "2/4  import_wyscout.py  (match definitivo con Transfermarkt)"
python3 import_wyscout.py

step "3/4  download_photos.py  (foto e loghi mancanti)"
python3 download_photos.py

step "4/4  run_stats.py  (presenze 24/25 + 25/26)"
python3 run_stats.py

echo ""
echo "============================================================"
echo "  FATTO. Apri il sito con:  bash frontend/serve.sh"
echo "============================================================"

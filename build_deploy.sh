#!/usr/bin/env bash
# build_deploy.sh — Prepara la cartella deploy_dist/ pronta per drag&drop
# su Netlify Drop o Vercel.
#
# Cosa fa:
#   1) Crea deploy_dist/ pulita
#   2) Copia frontend/* dentro
#   3) Copia data/*.json dentro deploy_dist/data/
#   4) Copia data/photos/ dentro deploy_dist/data/photos/
#   5) Modifica DATA_BASE in app.js da "../data" a "./data"
#      (perché in deploy il frontend è la root e data/ è subfolder)
#   6) Stampa istruzioni di deploy
#
# Uso:
#     bash build_deploy.sh
#     # poi vai su https://app.netlify.com/drop  (o Vercel)
#     # e trascina la cartella deploy_dist/

set -e
cd "$(dirname "$0")"

DIST="deploy_dist"
echo "== build deploy =="
echo ""

# 1) cartella pulita
rm -rf "$DIST"
mkdir -p "$DIST/data/photos"

# 2) frontend (HTML + JS + i18n)
cp -r frontend/index.html frontend/i18n.js frontend/app.js "$DIST/"
echo "  frontend copiato"

# 3) JSON essenziali per la UI (no debug)
for f in clubs.json players_unified.json players_main.json players_static.json \
         players_stats.json wyscout_players.json last_update.json; do
  if [ -f "data/$f" ]; then
    cp "data/$f" "$DIST/data/"
  fi
done
echo "  data/*.json copiato"

# 4) Foto e loghi
for d in players_curated clubs_curated players_sots players_tm clubs_sots clubs_tm \
         competitions national players_sots_lookup; do
  if [ -d "data/photos/$d" ]; then
    cp -r "data/photos/$d" "$DIST/data/photos/"
  fi
done
echo "  data/photos/ copiato"

# 5) DATA_BASE: ../data → ./data (per deploy)
sed -i.bak 's|const DATA_BASE = "../data";|const DATA_BASE = "./data";|' "$DIST/app.js"
rm -f "$DIST/app.js.bak"
echo "  DATA_BASE aggiornato a ./data"

# 6) Stats finali
echo ""
echo "============================================================"
SIZE=$(du -sh "$DIST" | cut -f1)
N_FILES=$(find "$DIST" -type f | wc -l | tr -d ' ')
echo "  deploy_dist/ pronta — $SIZE — $N_FILES files"
echo "============================================================"
echo ""
echo "Per deploy GRATIS, in 30 secondi:"
echo ""
echo "  OPZIONE A — Netlify Drop:"
echo "    1) Apri  https://app.netlify.com/drop"
echo "    2) Trascina la cartella ~/Desktop/tm_project/deploy_dist  sulla pagina"
echo "    3) URL pronto: <random-name>.netlify.app"
echo ""
echo "  OPZIONE B — Vercel:"
echo "    1) Apri  https://vercel.com/new  (login richiesto)"
echo "    2) Click 'Import Folder', seleziona deploy_dist/"
echo "    3) URL pronto: <project>.vercel.app"
echo ""
echo "  OPZIONE C — testa in locale prima (consigliato):"
echo "    bash frontend/serve.sh"
echo "    poi apri  http://127.0.0.1:5173/frontend/"
echo ""

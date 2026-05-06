#!/usr/bin/env bash
# update_stats.sh — Lancia run_update.py per aggiornare TUTTO in modo incrementale.
# Da chiamare via launchd Mac (o cron) ogni 3-5 giorni.
#
# Cosa fa run_update.py (in ~5-8 min):
#  - rifà clubs + rosters (rileva nuovi giocatori trasferiti)
#  - scrape profili SOLO dei nuovi giocatori
#  - refresh stats per tutti i sauditi
#  - re-enrich sortitoutsi e Wyscout
#  - download foto SOLO delle nuove
#
# Log: scheduler/last_run.log

set -e
DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$DIR"

source venv/bin/activate

LOG="$DIR/scheduler/last_run.log"
mkdir -p "$DIR/scheduler"
{
  echo "===================="
  echo "Run started: $(date)"
  echo "===================="
  # caffeinate -i: previene lo sleep della macchina mentre lo script gira
  caffeinate -i python3 run_update.py
  echo ""
  echo "Run finished: $(date)"
} > "$LOG" 2>&1

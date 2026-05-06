#!/bin/bash
# auto_update_full.sh — Update completo stagionale (15 giugno + 15 settembre)
#
# Workflow:
#   Identico a auto_update_daily.sh ma lancia run_update.py invece di run_stats.py.
#   run_update.py rifà clubs + rosters + nuovi profili + stats + foto.
#
# Logging: ~/Desktop/pid/logs/full_YYYY-MM-DD.log

set -uo pipefail

PROJECT_DIR="$HOME/Desktop/pid"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/full_$(date +%Y-%m-%d).log"
LOCK_FILE="$PROJECT_DIR/.full_update.lock"
NOTIF_TITLE="PID Auto-Update"

mkdir -p "$LOG_DIR"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

notify() {
  local title="$1"
  local message="$2"
  local sound="${3:-default}"
  osascript -e "display notification \"$message\" with title \"$title\" sound name \"$sound\"" 2>/dev/null || true
}

fail() {
  log "ERROR: $*"
  notify "$NOTIF_TITLE — ❌ Errore Full" "$* — log: $LOG_FILE" "Basso"
  rm -f "$LOCK_FILE"
  exit 1
}

if [ -f "$LOCK_FILE" ]; then
  log "WARN: lock esistente. Esco."
  exit 0
fi
trap 'rm -f "$LOCK_FILE"' EXIT
touch "$LOCK_FILE"

log "==================================================================="
log "AUTO UPDATE FULL — start ($(date +%Y-%m-%d))"
log "==================================================================="

cd "$PROJECT_DIR" || fail "cd $PROJECT_DIR fallito"

if [ -f "venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
  log "venv attivata"
else
  fail "venv non trovata"
fi

STATS_FILE="data/players_stats.json"
PRE_STATS_HASH=""
[ -f "$STATS_FILE" ] && PRE_STATS_HASH=$(md5 -q "$STATS_FILE" 2>/dev/null || md5sum "$STATS_FILE" | cut -d' ' -f1)

# === RUN UPDATE COMPLETO ===
log "Lancio run_update.py (full) ..."
T_START=$(date +%s)
python3 run_update.py >> "$LOG_FILE" 2>&1 || fail "run_update.py exit code $?"
T_END=$(date +%s)
ELAPSED=$((T_END - T_START))
log "run_update.py completato in ${ELAPSED}s ($(( ELAPSED / 60 ))m$((ELAPSED % 60))s)"

# === UPLOAD R2 ===
POST_STATS_HASH=""
[ -f "$STATS_FILE" ] && POST_STATS_HASH=$(md5 -q "$STATS_FILE" 2>/dev/null || md5sum "$STATS_FILE" | cut -d' ' -f1)
if [ "$PRE_STATS_HASH" != "$POST_STATS_HASH" ] && [ -f "$STATS_FILE" ]; then
  log "Upload R2 ..."
  python3 upload_to_r2.py "$STATS_FILE" >> "$LOG_FILE" 2>&1 || fail "upload R2 fallito"
fi

# === GIT PUSH ===
PENDING=$(git status --porcelain | wc -l | tr -d ' ')
if [ "$PENDING" -gt 0 ]; then
  log "git changes ($PENDING file). Commit + push ..."
  git add -A >> "$LOG_FILE" 2>&1
  git commit -m "auto: full update ($(date +%Y-%m-%d))" >> "$LOG_FILE" 2>&1 || fail "git commit fallito"
  git push >> "$LOG_FILE" 2>&1 || fail "git push fallito"
  log "git push OK"
else
  log "no git changes"
fi

log "AUTO UPDATE FULL — DONE"
notify "$NOTIF_TITLE — ✓ Full" "Update completo in $((ELAPSED/60))m. Vercel ridepoloya." "Glass"

exit 0

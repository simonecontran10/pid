#!/bin/bash
# auto_update_daily.sh — Update notturno automatico (lanciato da launchd alle 03:00)
#
# Workflow:
#   1. cd nella root del progetto
#   2. Attiva venv
#   3. Lancia run_stats.py --refresh  (5-7 min, scarica presenze del giorno)
#   4. Se players_stats.json è cambiato → upload R2
#   5. Se last_update.json è cambiato → git add/commit/push
#   6. Notifica macOS (success o errore)
#
# Logging: ~/Desktop/pid/logs/daily_YYYY-MM-DD.log

set -uo pipefail

# === CONFIG ===
PROJECT_DIR="$HOME/Desktop/pid"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/daily_$(date +%Y-%m-%d).log"
LOCK_FILE="$PROJECT_DIR/.daily_update.lock"
NOTIF_TITLE="PID Auto-Update"

mkdir -p "$LOG_DIR"

# === FUNZIONI ===
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
  notify "$NOTIF_TITLE — ❌ Errore" "$* — vedi log: $LOG_FILE" "Basso"
  rm -f "$LOCK_FILE"
  exit 1
}

# === LOCK (evita doppi run) ===
if [ -f "$LOCK_FILE" ]; then
  log "WARN: lock esistente. Esco senza fare nulla."
  exit 0
fi
trap 'rm -f "$LOCK_FILE"' EXIT
touch "$LOCK_FILE"

# === START ===
log "==================================================================="
log "AUTO UPDATE DAILY — start"
log "==================================================================="

cd "$PROJECT_DIR" || fail "cd $PROJECT_DIR fallito"

# === ATTIVA VENV ===
if [ -f "venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
  log "venv attivata"
else
  fail "venv non trovata in $PROJECT_DIR/venv"
fi

# === HASH PRE-RUN ===
STATS_FILE="data/players_stats.json"
LAST_UPDATE_FILE="data/last_update.json"
PRE_STATS_HASH=""
PRE_META_HASH=""
[ -f "$STATS_FILE" ] && PRE_STATS_HASH=$(md5 -q "$STATS_FILE" 2>/dev/null || md5sum "$STATS_FILE" | cut -d' ' -f1)
[ -f "$LAST_UPDATE_FILE" ] && PRE_META_HASH=$(md5 -q "$LAST_UPDATE_FILE" 2>/dev/null || md5sum "$LAST_UPDATE_FILE" | cut -d' ' -f1)

# === RUN STATS ===
log "Lancio run_stats.py --refresh ..."
T_START=$(date +%s)
python3 run_stats.py --refresh >> "$LOG_FILE" 2>&1 || fail "run_stats.py exit code $?"
T_END=$(date +%s)
ELAPSED=$((T_END - T_START))
log "run_stats.py completato in ${ELAPSED}s"

# === HASH POST-RUN ===
POST_STATS_HASH=""
POST_META_HASH=""
[ -f "$STATS_FILE" ] && POST_STATS_HASH=$(md5 -q "$STATS_FILE" 2>/dev/null || md5sum "$STATS_FILE" | cut -d' ' -f1)
[ -f "$LAST_UPDATE_FILE" ] && POST_META_HASH=$(md5 -q "$LAST_UPDATE_FILE" 2>/dev/null || md5sum "$LAST_UPDATE_FILE" | cut -d' ' -f1)

# === UPLOAD R2 SE STATS CAMBIATE ===
if [ "$PRE_STATS_HASH" != "$POST_STATS_HASH" ] && [ -f "$STATS_FILE" ]; then
  log "players_stats.json cambiato → upload R2 ..."
  python3 upload_to_r2.py "$STATS_FILE" >> "$LOG_FILE" 2>&1 || fail "upload R2 fallito"
  log "upload R2 OK"
else
  log "players_stats.json invariato (skip upload R2)"
fi

# === GIT COMMIT + PUSH SE METADATA CAMBIATI ===
GIT_CHANGES=""
if [ "$PRE_META_HASH" != "$POST_META_HASH" ]; then
  GIT_CHANGES="$LAST_UPDATE_FILE"
fi
# Anche altri file potrebbero cambiare in futuro (clubs.json, ij1_clubs.json, ecc.)
# git status include tutto ciò che è tracciato
PENDING=$(git status --porcelain | wc -l | tr -d ' ')
if [ "$PENDING" -gt 0 ]; then
  log "git changes ($PENDING file). Commit + push ..."
  git add -A >> "$LOG_FILE" 2>&1
  git commit -m "auto: daily stats refresh ($(date +%Y-%m-%d))" >> "$LOG_FILE" 2>&1 || fail "git commit fallito"
  git push >> "$LOG_FILE" 2>&1 || fail "git push fallito"
  log "git push OK"
else
  log "no git changes"
fi

# === SUCCESS ===
log "AUTO UPDATE DAILY — DONE"
notify "$NOTIF_TITLE — ✓ Daily" "Stats aggiornate in ${ELAPSED}s. Vercel ridepoloya." "Glass"

exit 0

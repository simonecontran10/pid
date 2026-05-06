#!/usr/bin/env bash
# install_scheduler.sh — Installa il job launchd per auto-update ogni 4 giorni.
#
# Uso:
#     bash scheduler/install_scheduler.sh           # installa
#     bash scheduler/install_scheduler.sh uninstall # rimuove
#     bash scheduler/install_scheduler.sh status    # verifica

set -e
cd "$(dirname "$0")/.."

LABEL="com.saudi-players.update-stats"
PLIST_SRC="scheduler/$LABEL.plist"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"
PLIST_DEST="$LAUNCH_AGENTS/$LABEL.plist"

action="${1:-install}"

case "$action" in

  install)
    echo "== install scheduler =="
    if [ ! -f "$PLIST_SRC" ]; then
      echo "[FATAL] $PLIST_SRC non trovato"
      exit 1
    fi
    mkdir -p "$LAUNCH_AGENTS"
    cp "$PLIST_SRC" "$PLIST_DEST"
    echo "  copiato $PLIST_DEST"

    # Unload se già caricato (evita errore "already loaded")
    launchctl unload "$PLIST_DEST" 2>/dev/null || true

    launchctl load "$PLIST_DEST"
    echo "  caricato"

    if launchctl list | grep -q "$LABEL"; then
      echo ""
      echo "  ✓ scheduler attivo. Si auto-aggiorna ogni 4 giorni."
      echo "  log: scheduler/last_run.log"
      echo "  test manuale:  launchctl start $LABEL"
    else
      echo ""
      echo "  ⚠ Non vedo il job nella lista launchctl. Verifica manualmente."
    fi
    ;;

  uninstall)
    echo "== uninstall scheduler =="
    if [ -f "$PLIST_DEST" ]; then
      launchctl unload "$PLIST_DEST" 2>/dev/null || true
      rm "$PLIST_DEST"
      echo "  rimosso $PLIST_DEST"
    else
      echo "  niente da rimuovere"
    fi
    ;;

  status)
    echo "== status =="
    if [ -f "$PLIST_DEST" ]; then
      echo "  plist installato: $PLIST_DEST"
    else
      echo "  plist NON installato"
    fi
    if launchctl list | grep -q "$LABEL"; then
      echo "  job attivo nel launchctl"
      launchctl list | grep "$LABEL"
    else
      echo "  job NON in esecuzione"
    fi
    if [ -f scheduler/last_run.log ]; then
      echo ""
      echo "  ultimo log (last 10 righe):"
      tail -10 scheduler/last_run.log | sed 's/^/    /'
    fi
    ;;

  *)
    echo "uso: $0 {install|uninstall|status}"
    exit 1
    ;;
esac

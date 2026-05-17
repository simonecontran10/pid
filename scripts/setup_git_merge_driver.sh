#!/usr/bin/env bash
# setup_git_merge_driver.sh - Registra il merge driver `newer-json` in .git/config.
#
# Il merge driver e' referenziato da .gitattributes (versionato) ma la sua
# DEFINIZIONE vive in .git/config, che NON e' versionato. Quindi va installato
# una volta su ogni clone: sul Mac e su ogni runner GitHub Actions (il workflow
# lo chiama come primo step prima di toccare git). Idempotente.
set -euo pipefail

cd "$(dirname "$0")/.."
REPO_ROOT="$(pwd)"
DRIVER_SCRIPT="$REPO_ROOT/scripts/git-merge-newer-json.py"

if [ ! -f "$DRIVER_SCRIPT" ]; then
  echo "[setup-merge-driver] ERRORE: $DRIVER_SCRIPT non trovato" >&2
  exit 1
fi

chmod +x "$DRIVER_SCRIPT" 2>/dev/null || true

PYTHON_BIN="$(command -v python3 || true)"
if [ -z "$PYTHON_BIN" ]; then
  echo "[setup-merge-driver] ERRORE: python3 non trovato nel PATH" >&2
  exit 1
fi

git config merge.newer-json.name "Keep JSON with newest completion timestamp"
git config merge.newer-json.driver "$PYTHON_BIN \"$DRIVER_SCRIPT\" %O %A %B"

echo "[setup-merge-driver] driver 'newer-json' registrato:"
echo "    merge.newer-json.driver = $PYTHON_BIN $DRIVER_SCRIPT %O %A %B"
echo "[setup-merge-driver] .gitattributes presente: $([ -f .gitattributes ] && echo yes || echo NO)"
echo "[setup-merge-driver] OK"

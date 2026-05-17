#!/usr/bin/env python3
"""
git-merge-newer-json — Merge driver custom per file JSON di metadata rigenerabili.

git invoca questo script quando c'è un conflitto di merge/rebase su un file
configurato in .gitattributes con `merge=newer-json`.

Argomenti passati da git (definiti in .git/config merge driver):
  %O = antenato comune (base)
  %A = nostra versione (ours)   <- git scrive QUI il risultato
  %B = loro versione (theirs)

Strategia: per last_update.json e simili, la "verità" è la versione con il
timestamp di completamento più recente (stats_completed_at, poi completed_at,
poi updated_at). Non importa quale ramo: vince il run più recente, perché
tanto il prossimo run rigenererà comunque il file.

Exit code 0 = conflitto risolto, git prosegue il merge/rebase senza intervento.
Exit code 1 = impossibile risolvere (git lascia i marker di conflitto standard).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone


TIMESTAMP_KEYS = ("stats_completed_at", "completed_at", "updated_at", "started_at")


def _parse_ts(value: str) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    v = value.strip()
    # Normalizza la 'Z' finale in +00:00 per fromisoformat
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(v)
    except ValueError:
        return None
    # Rendi tutto timezone-aware (assumi UTC se naive) per confronti sicuri
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _best_timestamp(obj: dict) -> datetime | None:
    """Ritorna il timestamp più informativo dell'oggetto JSON."""
    best = None
    for k in TIMESTAMP_KEYS:
        ts = _parse_ts(obj.get(k, ""))
        if ts and (best is None or ts > best):
            best = ts
    return best


def main() -> int:
    if len(sys.argv) < 4:
        print("usage: git-merge-newer-json <base> <ours> <theirs>", file=sys.stderr)
        return 1

    base_path, ours_path, theirs_path = sys.argv[1], sys.argv[2], sys.argv[3]

    try:
        with open(ours_path, encoding="utf-8") as f:
            ours = json.load(f)
        with open(theirs_path, encoding="utf-8") as f:
            theirs = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        # Se uno dei due non è JSON valido, non possiamo decidere: lascia il conflitto a git
        print(f"[merge-newer-json] parse fallito ({e}); lascio il conflitto a git", file=sys.stderr)
        return 1

    ours_ts = _best_timestamp(ours) if isinstance(ours, dict) else None
    theirs_ts = _best_timestamp(theirs) if isinstance(theirs, dict) else None

    # Decidi il vincitore
    if ours_ts is None and theirs_ts is None:
        # Nessun timestamp: prendi 'theirs' per determinismo (la versione in arrivo dal rebase)
        winner, why = theirs, "nessun timestamp, default=theirs"
    elif ours_ts is None:
        winner, why = theirs, "ours senza timestamp"
    elif theirs_ts is None:
        winner, why = ours, "theirs senza timestamp"
    elif theirs_ts >= ours_ts:
        winner, why = theirs, f"theirs più recente ({theirs_ts} >= {ours_ts})"
    else:
        winner, why = ours, f"ours più recente ({ours_ts} > {theirs_ts})"

    # git si aspetta il risultato nel file 'ours' (%A)
    try:
        with open(ours_path, "w", encoding="utf-8") as f:
            json.dump(winner, f, indent=2, ensure_ascii=False)
            f.write("\n")
    except OSError as e:
        print(f"[merge-newer-json] scrittura risultato fallita: {e}", file=sys.stderr)
        return 1

    print(f"[merge-newer-json] risolto automaticamente: {why}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

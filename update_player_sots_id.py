"""Aggiorna i campi sortitoutsi_* in players_all.json e players_main.json
per un singolo giocatore (tm_player_id), settando sortitoutsi_person_id +
sortitoutsi_face_local_lookup.

Uso:
  python3 update_player_sots_id.py <tm_player_id> <sots_person_id>
  python3 update_player_sots_id.py 369081 78074594
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
FILES = [DATA / "players_all.json", DATA / "players_main.json"]

if len(sys.argv) != 3:
    print(__doc__)
    sys.exit(1)
tm_id = int(sys.argv[1])
sots_id = int(sys.argv[2])
lookup_path = f"photos/players_sots_lookup/{sots_id}.png"

for f in FILES:
    if not f.exists():
        continue
    data = json.loads(f.read_text(encoding="utf-8"))
    updated = 0
    for p in data:
        if p.get("tm_player_id") == tm_id:
            p["sortitoutsi_person_id"] = sots_id
            p["sortitoutsi_face_local_lookup"] = lookup_path
            updated += 1
    if updated:
        f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[{f.name}] aggiornati {updated} record (tm_id={tm_id} → sots_id={sots_id})")
    else:
        print(f"[{f.name}] tm_player_id={tm_id} non trovato")

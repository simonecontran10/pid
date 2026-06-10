"""
backfill_logos_from_disk.py — Scansiona data/photos/clubs_sots/<tm_id>.png e
popola sortitoutsi_logo_local nel clubs.json per i club che hanno il file
fisico ma il campo JSON e' null/disallineato.

Bug fixato: dopo che scrape_sots_competition.py ha popolato
sortitoutsi_team_id per nuovi club + extract_sots_assets.py ha scaricato
i loghi, i campi sortitoutsi_logo_local rimanevano NULL nel JSON perche'
l'extract non riapre clubs.json. Il frontend (clubLogo) si basa su
sortitoutsi_logo_local per costruire l'URL → niente logo visualizzato.

Idempotente: se sortitoutsi_logo_local punta gia' al file corretto, skip.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).parent
CLUBS_FILE = ROOT / "data" / "clubs.json"
LOGOS_DIR = ROOT / "data" / "photos" / "clubs_sots"


def main():
    clubs = json.loads(CLUBS_FILE.read_text(encoding="utf-8"))
    existing_files = {p.stem: p for p in LOGOS_DIR.glob("*.png")}
    print(f"[scan] {len(existing_files)} loghi fisici trovati in {LOGOS_DIR.relative_to(ROOT)}")

    updated = 0
    no_file = 0
    already_ok = 0

    for c in clubs:
        tm_id = c.get("tm_club_id")
        if tm_id is None:
            continue
        key = str(tm_id)
        if key not in existing_files:
            no_file += 1
            continue
        rel_path = f"photos/clubs_sots/{key}.png"
        current = c.get("sortitoutsi_logo_local")
        if current == rel_path:
            already_ok += 1
            continue
        c["sortitoutsi_logo_local"] = rel_path
        updated += 1
        print(f"  + {c.get('name')[:35]:35} tm={tm_id} → {rel_path}")

    print()
    print(f"[result] aggiornati:   {updated}")
    print(f"[result] gia' ok:      {already_ok}")
    print(f"[result] senza file:   {no_file}")

    if updated:
        CLUBS_FILE.write_text(json.dumps(clubs, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[save] data/clubs.json aggiornato.")
    else:
        print("[save] niente da scrivere.")


if __name__ == "__main__":
    main()

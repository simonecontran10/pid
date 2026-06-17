"""
fix_club_urls_to_kader.py — Migra clubs.json verso URL "kader/.../plus/1".

I club aggiunti prima del 12-06-2026 hanno club_url tipo:
    https://www.transfermarkt.com/club/startseite/verein/11
Questo URL serve la pagina "Compact view" che mostra solo 17-22 giocatori
(prima squadra senza riserve, infortunati lungo termine, prestiti out).

Il fix recente in add_club.py usa la "Detailed view":
    https://www.transfermarkt.com/{slug}/kader/verein/{cid}/saison_id/2025/plus/1
che restituisce 25-30 giocatori (rosa completa).

Questo script aggiorna i club_url di tutti i record già esistenti.

Uso:
    python3 fix_club_urls_to_kader.py            # dry-run
    python3 fix_club_urls_to_kader.py --apply    # scrivi clubs.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CLUBS_FILE = ROOT / "data" / "clubs.json"
SEASON = 2025


def build_kader_url(slug: str, cid: int) -> str:
    s = slug or "club"
    return f"https://www.transfermarkt.com/{s}/kader/verein/{cid}/saison_id/{SEASON}/plus/1"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="scrivi clubs.json")
    args = ap.parse_args()

    clubs = json.loads(CLUBS_FILE.read_text(encoding="utf-8"))
    changed = 0
    skipped_already = 0
    skipped_other = 0

    for c in clubs:
        cid = c.get("tm_club_id")
        if not isinstance(cid, int):
            skipped_other += 1
            continue
        url = c.get("club_url") or ""
        # Gia' su kader/plus/1 → skip.
        if "/kader/verein/" in url and "/plus/1" in url:
            skipped_already += 1
            continue
        slug = c.get("slug") or ""
        if not slug:
            # estrai slug dall'URL se possibile
            m = re.search(r"transfermarkt\.[a-z.]+/([^/]+)/", url)
            if m:
                slug = m.group(1)
        new_url = build_kader_url(slug, cid)
        if new_url == url:
            skipped_already += 1
            continue
        print(f"  {cid:>6}  {c.get('name','?')[:30]:30}  →  kader/plus/1/saison_id/{SEASON}")
        c["club_url"] = new_url
        changed += 1

    print()
    print(f"Risultato: {changed} aggiornati, {skipped_already} gia' OK, {skipped_other} senza tm_club_id.")
    if args.apply and changed > 0:
        CLUBS_FILE.write_text(
            json.dumps(clubs, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"[ok] clubs.json scritto ({len(clubs)} record).")
    elif not args.apply:
        print("[dry-run] niente scritto. Usa --apply per scrivere clubs.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

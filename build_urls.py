"""Per ogni club nei 3 file (serie_a, it2, ij1) scrappa la rosa
ed estrae gli URL profilo giocatori. Salva tutto in urls.txt."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _bootstrap  # noqa

from scraper.http_client import TransfermarktClient
from scraper.rosters import parse_club_roster

CLUB_FILES = [
    "data/serie_a_clubs.json",
    "data/it2_clubs.json",
    "data/ij1_clubs.json",
]

client = TransfermarktClient()
all_urls = set()
total_clubs = 0
total_players = 0

for club_file in CLUB_FILES:
    clubs = json.loads(Path(club_file).read_text(encoding="utf-8"))
    print(f"\n=== {club_file} — {len(clubs)} club ===")
    for c in clubs:
        total_clubs += 1
        try:
            html = client.get_html(c["club_url"])
            roster = parse_club_roster(html, c["tm_club_id"], c["name"])
            for p in roster:
                all_urls.add(p["profile_url"])
            total_players += len(roster)
            print(f"  [{total_clubs:>2}] {c['name']:<35} {len(roster)} players (tot urls unici: {len(all_urls)})")
        except Exception as e:
            print(f"  [ERR] {c['name']}: {e}")

# Salva URLs in urls.txt
out = Path("urls.txt")
out.write_text("\n".join(sorted(all_urls)) + "\n", encoding="utf-8")
print(f"\n[saved] {out} con {len(all_urls)} URL unici (giocatori totali scrappati: {total_players})")

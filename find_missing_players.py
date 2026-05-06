"""
find_missing_players.py — Confronta DB attuale con rose TM live.
Per ogni club Serie A/B/Primavera, scarica rosa attuale TM e
identifica giocatori non ancora presenti nel DB.
Output: missing_urls.txt (URL da passare ad add_players.py)
"""
from __future__ import annotations
import sys, time, json, requests
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import _bootstrap  # noqa

from scraper.rosters import parse_club_roster
from scraper.config import USER_AGENTS, SLEEP_BETWEEN_REQUESTS

players = json.load(open("data/players_main.json"))
clubs = json.load(open("data/clubs.json"))

# Set di tm_player_id già nel DB
db_tm_ids = set(p["tm_player_id"] for p in players)
print(f"DB players: {len(db_tm_ids)}")

session = requests.Session()
H = {"User-Agent": USER_AGENTS[0]}

missing_urls = []
missing_by_club = {}

for c in clubs:
    if c.get("league_id") not in ("IT1", "IT2", "IJ1"):
        continue
    url = c.get("club_url")
    if not url:
        continue
    try:
        r = session.get(url, headers=H, timeout=20)
        roster = parse_club_roster(r.text, c["tm_club_id"], c["name"])
    except Exception as e:
        print(f"  [{c['name']}] ERR {e}")
        continue
    
    new = [p for p in roster if p["tm_player_id"] not in db_tm_ids]
    if new:
        missing_by_club[c["name"]] = len(new)
        for p in new:
            missing_urls.append(p["profile_url"])
            db_tm_ids.add(p["tm_player_id"])  # evita duplicati cross-club
    print(f"  {c['name']:<30}  rosa={len(roster):>3}  nuovi={len(new):>3}")
    time.sleep(SLEEP_BETWEEN_REQUESTS)

# Salva
Path("missing_urls.txt").write_text("\n".join(missing_urls), encoding="utf-8")
print()
print(f"=== Riepilogo ===")
print(f"  giocatori da scrappare: {len(missing_urls)}")
print(f"  salvati in missing_urls.txt")
print(f"  tempo stimato add_players.py: ~{len(missing_urls) * 7 // 60} minuti")

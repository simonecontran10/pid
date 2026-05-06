"""
fix_misclassified_clubs.py — Re-popola roster_club_* dai roster live TM,
poi applica fix_club_placeholder per risolvere i placeholder.
"""
from __future__ import annotations
import json
import sys
import time
import requests
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import _bootstrap  # noqa

from scraper.rosters import parse_club_roster
from scraper.config import USER_AGENTS, SLEEP_BETWEEN_REQUESTS

# Riusa la funzione esistente
from enrich_sortitoutsi import fix_club_placeholder

DATA_DIR = Path("data")

# 1. Fetch rose live e costruisci mapping tm_player_id -> (roster_club_id, roster_club_name)
clubs = json.loads((DATA_DIR / "clubs.json").read_text(encoding="utf-8"))
session = requests.Session()
H = {"User-Agent": USER_AGENTS[0]}

roster_by_tm = {}  # tm_player_id -> (club_id, club_name)
print("=== Step 1: scarica rose live ===")
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
    for p in roster:
        # Se un giocatore è in più rose (giovanile + senior), priorità senior (IT1/IT2)
        existing = roster_by_tm.get(p["tm_player_id"])
        if existing and c.get("league_id") == "IJ1":
            # Già assegnato a un club senior, non sovrascrivere
            continue
        roster_by_tm[p["tm_player_id"]] = (c["tm_club_id"], c["name"])
    print(f"  {c['name']:<30}  rosa={len(roster):>3}")
    time.sleep(SLEEP_BETWEEN_REQUESTS)

print(f"\nTotale mapping costruiti: {len(roster_by_tm)}")

# 2. Per ognuno dei 3 JSON, aggiorna roster_club_* + applica fix_club_placeholder
print("\n=== Step 2: aggiorna JSON e applica fix ===")
for fname in ("players_main.json", "players_static.json", "players_all.json"):
    path = DATA_DIR / fname
    if not path.exists():
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    n_roster_set = 0
    n_fixed = 0
    for p in data:
        tm_id = p.get("tm_player_id")
        new_roster = roster_by_tm.get(tm_id)
        if new_roster:
            cid, cname = new_roster
            if p.get("roster_club_id") != cid or p.get("roster_club_name") != cname:
                p["roster_club_id"] = cid
                p["roster_club_name"] = cname
                n_roster_set += 1
        # Applica fix
        if fix_club_placeholder(p):
            n_fixed += 1
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  {fname:<25}  roster_set={n_roster_set:>4}  fixed_placeholder={n_fixed:>4}")

print("\nFatto.")

"""
harvest_sots_rosters.py — Cache locale di tutte le rose SortItOutSi.
Per ogni club con sortitoutsi_team_id, scarica la pagina team e estrae
tutti i giocatori (sots_id, slug, nome). Output: data/sots_rosters.json.
"""
from __future__ import annotations
import json
import re
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import _bootstrap  # noqa

import requests
from bs4 import BeautifulSoup
from scraper.config import CLUBS_FILE, DATA_DIR, USER_AGENTS, SLEEP_BETWEEN_REQUESTS

OUT_FILE = DATA_DIR / "sots_rosters.json"
HEADERS = {"User-Agent": USER_AGENTS[0]}

def fetch_team_roster(team_id: int, slug: str, session: requests.Session):
    """Fetch pagina team SortItOutSi, estrai elenco completo /person/."""
    url = f"https://sortitoutsi.net/football-manager-2026/team/{team_id}/{slug}"
    r = session.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    persons = []
    seen = set()
    for a in soup.select('a[href*="/person/"]'):
        href = a.get("href", "")
        m = re.search(r"/person/(\d+)/([^/?]+)", href)
        if not m:
            continue
        sid = int(m.group(1))
        if sid in seen:
            continue
        seen.add(sid)
        # Nome dal testo del link (a volte è solo il primo nome, a volte completo)
        name = a.get_text(" ", strip=True)
        slug_p = m.group(2)
        persons.append({"sots_id": sid, "slug": slug_p, "name_link": name})
    return persons


def main():
    clubs = json.loads(CLUBS_FILE.read_text(encoding="utf-8"))
    clubs_with_sots = [c for c in clubs if c.get("sortitoutsi_team_id")]
    print(f"Club con sortitoutsi_team_id: {len(clubs_with_sots)}/{len(clubs)}")
    
    rosters = {}
    session = requests.Session()
    
    for i, c in enumerate(clubs_with_sots, 1):
        sid = c["sortitoutsi_team_id"]
        # Costruisci slug dalla URL del logo o dal nome
        slug = c.get("name", "").lower().replace(" ", "-")
        try:
            persons = fetch_team_roster(sid, slug, session)
        except Exception as e:
            print(f"  [{i}/{len(clubs_with_sots)}] {c['name']:<30} ERROR: {e}")
            continue
        rosters[str(sid)] = {
            "club_name": c["name"],
            "tm_club_id": c.get("tm_club_id"),
            "league_id": c.get("league_id"),
            "persons": persons,
        }
        print(f"  [{i}/{len(clubs_with_sots)}] {c['name']:<30} → {len(persons)} giocatori")
        time.sleep(SLEEP_BETWEEN_REQUESTS)
    
    OUT_FILE.write_text(json.dumps(rosters, indent=2, ensure_ascii=False), encoding="utf-8")
    total_persons = sum(len(r["persons"]) for r in rosters.values())
    print(f"\nSalvato {OUT_FILE.name}: {len(rosters)} club, {total_persons} persons totali")

if __name__ == "__main__":
    main()

"""
fix_new_arrival_clubs.py — Re-scrape giocatori con current_club_name="New arrival"
                            per estrarre il vero club corrente (post-fix scraper).

Uso:
  python3 fix_new_arrival_clubs.py           # processa tutti
  python3 fix_new_arrival_clubs.py --limit 10  # solo primi 10 (test)
"""
from __future__ import annotations

import sys, json, time
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
import _bootstrap  # noqa: F401

from scraper.http_client import TransfermarktClient
from scraper.profiles import scrape_player_profile
from scraper.leagues import scrape_club_by_id
from scraper.config import (
    DATA_DIR,
    PLAYERS_SAUDI_FILE,
    PLAYERS_STATIC_FILE,
    CLUBS_FILE,
)

PLAYERS_MAIN_FILE = DATA_DIR / "players_main.json"
PLAYERS_ALL_FILE = DATA_DIR / "players_all.json"


def load(p: Path):
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def save(p: Path, data) -> None:
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    limit = None
    if "--limit" in sys.argv:
        i = sys.argv.index("--limit")
        if i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
    
    # Carico tutti i file da aggiornare
    players_main = load(PLAYERS_MAIN_FILE)
    players_all = load(PLAYERS_ALL_FILE)
    players_static = load(PLAYERS_STATIC_FILE)
    players_saudi = load(PLAYERS_SAUDI_FILE)
    clubs = load(CLUBS_FILE)
    clubs_by_id = {int(c["tm_club_id"]): c for c in clubs if c.get("tm_club_id")}
    
    # Trovo i giocatori broken
    broken = [p for p in players_main if p.get("current_club_name") == "New arrival"]
    if limit:
        broken = broken[:limit]
    
    print(f"Giocatori 'New arrival' da fissare: {len(broken)}")
    if not broken:
        print("Nessun fix necessario.")
        return
    
    client = TransfermarktClient()
    n_fixed = n_failed = 0
    n_clubs_added = 0
    started = time.monotonic()
    
    # Mappa per aggiornare velocemente
    main_by_id = {p["tm_player_id"]: p for p in players_main}
    all_by_id = {p["tm_player_id"]: p for p in players_all}
    static_by_id = {p["tm_player_id"]: p for p in players_static}
    saudi_by_id = {p["tm_player_id"]: p for p in players_saudi}
    
    for i, p in enumerate(broken, 1):
        pid = p["tm_player_id"]
        old_club_id = p.get("current_club_id")
        old_club_name = p.get("current_club_name")
        try:
            new_prof = scrape_player_profile(pid, client)
            new_club_id = new_prof.get("current_club_id")
            new_club_name = new_prof.get("current_club_name")
            
            if not new_club_name or new_club_name == "New arrival":
                print(f"  [{i}/{len(broken)}] {p.get('full_name','?'):<32} STILL BROKEN: name='{new_club_name}'")
                n_failed += 1
                continue
            
            # Aggiorno solo i campi club + roster (NON tutto il profilo)
            for store_by_id in [main_by_id, all_by_id, static_by_id, saudi_by_id]:
                if pid in store_by_id:
                    store_by_id[pid]["current_club_id"] = new_club_id
                    store_by_id[pid]["current_club_name"] = new_club_name
                    store_by_id[pid]["roster_club_id"] = new_club_id
                    store_by_id[pid]["roster_club_name"] = new_club_name
            
            # Auto-creo club se non presente
            if new_club_id and new_club_id not in clubs_by_id:
                try:
                    new_club = scrape_club_by_id(new_club_id, client)
                    if new_club:
                        clubs.append(new_club)
                        clubs_by_id[new_club_id] = new_club
                        n_clubs_added += 1
                        print(f"  + club: {new_club['name']} ({new_club['league_id']})")
                except Exception as e:
                    print(f"  [club fail] {new_club_id}: {e}")
            
            n_fixed += 1
            if i <= 20 or i % 25 == 0:
                print(f"  [{i}/{len(broken)}] {p.get('full_name','?'):<32}  '{old_club_name}' -> '{new_club_name}'")
        
        except Exception as e:
            n_failed += 1
            print(f"  [{i}/{len(broken)}] FAIL pid={pid}: {type(e).__name__}: {e}")
        
        # Salvataggio incrementale ogni 25
        if i % 25 == 0:
            save(PLAYERS_MAIN_FILE, list(main_by_id.values()))
            save(PLAYERS_ALL_FILE, list(all_by_id.values()))
            save(PLAYERS_STATIC_FILE, list(static_by_id.values()))
            save(PLAYERS_SAUDI_FILE, list(saudi_by_id.values()))
            save(CLUBS_FILE, clubs)
    
    # Salvataggio finale
    save(PLAYERS_MAIN_FILE, list(main_by_id.values()))
    save(PLAYERS_ALL_FILE, list(all_by_id.values()))
    save(PLAYERS_STATIC_FILE, list(static_by_id.values()))
    save(PLAYERS_SAUDI_FILE, list(saudi_by_id.values()))
    save(CLUBS_FILE, clubs)
    
    elapsed = int(time.monotonic() - started)
    print(f"\n{'='*60}")
    print(f"  Fixed: {n_fixed}    Failed: {n_failed}    Clubs added: {n_clubs_added}")
    print(f"  Elapsed: {elapsed//60}m{elapsed%60}s")


if __name__ == "__main__":
    main()

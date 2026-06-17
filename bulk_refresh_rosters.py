"""
bulk_refresh_rosters.py — Re-scrape rose dei club usando il nuovo
club_url (kader/.../plus/1) e scarica i profili dei giocatori nuovi.

Use:
    python3 bulk_refresh_rosters.py                    # default: tutti
    python3 bulk_refresh_rosters.py --max 50           # primi 50
    python3 bulk_refresh_rosters.py --league GB1       # solo Premier League
    python3 bulk_refresh_rosters.py --sleep 12         # 12s tra request (default 10)

Output:
    data/players_main.json  — aggiornato in place (salvataggio ogni 20 profili)
    data/bulk_refresh.log   — log timestampato
    data/bulk_refresh_state.json — progress (resume support)

Tempo stimato: ~10s/club + ~6s/profilo nuovo. Per 595 club + ~2000
profili nuovi → 4-6h. Lancia in background:
    nohup python3 bulk_refresh_rosters.py > /tmp/bulk.log 2>&1 &
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
CLUBS_FILE = DATA_DIR / "clubs.json"
PLAYERS_MAIN_FILE = DATA_DIR / "players_main.json"
PLAYERS_ALL_FILE = DATA_DIR / "players_all.json"
LOG_FILE = DATA_DIR / "bulk_refresh.log"
STATE_FILE = DATA_DIR / "bulk_refresh_state.json"

sys.path.insert(0, str(ROOT))
from scraper.http_client import TransfermarktClient
from scraper.rosters import scrape_club_roster
from scraper.profiles import scrape_player_profile


def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_state(s: dict) -> None:
    STATE_FILE.write_text(json.dumps(s, indent=2), encoding="utf-8")


def save_players(main_by_id: dict[int, dict]) -> None:
    out = list(main_by_id.values())
    PLAYERS_MAIN_FILE.write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=0, help="limita primi N club (0=tutti)")
    ap.add_argument("--league", default="", help="filtra per league_id (es. GB1)")
    ap.add_argument("--sleep", type=float, default=10.0, help="sleep tra request (sec)")
    ap.add_argument("--sleep-profile", type=float, default=6.0, help="sleep tra profile (sec)")
    ap.add_argument("--skip-profiles", action="store_true", help="solo rose, no profili")
    ap.add_argument("--reset", action="store_true", help="ignora state file (re-scrape tutto)")
    args = ap.parse_args()

    log(f"=== bulk_refresh_rosters START sleep={args.sleep}s ===")

    clubs = json.loads(CLUBS_FILE.read_text(encoding="utf-8"))
    if args.league:
        clubs = [c for c in clubs if c.get("league_id") == args.league]
    if args.max > 0:
        clubs = clubs[: args.max]
    log(f"Club da processare: {len(clubs)}")

    state = {} if args.reset else load_state()
    done_clubs = set(state.get("done_clubs", []))
    log(f"Club gia' processati (skip): {len(done_clubs)}")

    main_list = json.loads(PLAYERS_MAIN_FILE.read_text(encoding="utf-8"))
    main_by_id: dict[int, dict] = {p["tm_player_id"]: p for p in main_list}
    log(f"Profili gia' in DB: {len(main_by_id)}")

    client = TransfermarktClient()
    new_pids: list[tuple[int, dict]] = []  # (tm_player_id, club_record per current_club_id)

    # === FASE 1: scarica rose ===
    for i, club in enumerate(clubs, 1):
        cid = club.get("tm_club_id")
        if cid in done_clubs:
            continue
        try:
            log(f"[{i}/{len(clubs)}] roster {cid} {club.get('name','?')[:40]}")
            roster = scrape_club_roster(club, client)
            for r in roster:
                pid = r["tm_player_id"]
                if pid not in main_by_id and pid not in [p[0] for p in new_pids]:
                    new_pids.append((pid, club))
            done_clubs.add(cid)
            state["done_clubs"] = list(done_clubs)
            save_state(state)
        except Exception as e:
            log(f"  [ERR] {type(e).__name__}: {e}")
        time.sleep(args.sleep)

    log(f"Profili NUOVI da scaricare: {len(new_pids)}")
    if args.skip_profiles:
        log("--skip-profiles → STOP")
        return 0

    # === FASE 2: scarica profili nuovi ===
    saved_count = 0
    for j, (pid, club) in enumerate(new_pids, 1):
        try:
            log(f"[{j}/{len(new_pids)}] profile {pid}")
            prof = scrape_player_profile(pid, client)
            if prof:
                # popula current_club_* dal club di scoperta
                prof.setdefault("current_club_id", club.get("tm_club_id"))
                prof.setdefault("current_club_name", club.get("name"))
                main_by_id[pid] = prof
                saved_count += 1
                if saved_count % 20 == 0:
                    save_players(main_by_id)
                    log(f"  [save] players_main.json ({len(main_by_id)} record)")
        except Exception as e:
            log(f"  [ERR] {type(e).__name__}: {e}")
        time.sleep(args.sleep_profile)

    save_players(main_by_id)
    log(f"=== bulk_refresh_rosters DONE ({len(main_by_id)} record totali) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
run_static.py — Scrape PRODUZIONE dei dati fissi.

Esegue, in ordine:
1. Lista club delle 2 leghe (SA1 + SA2L) -> data/clubs.json
2. Rosa di ogni club -> data/rosters.json
3. Profilo di OGNI giocatore -> data/players_all.json
4. Filtro target -> data/players_main.json

Resume:
- Ripartenza automatica: se un giocatore è già in players_all.json, viene saltato.
- Si può interrompere con Ctrl+C: il progresso è già salvato.

Tempo previsto: ~25-30 min sul primo run, pochi secondi nei rerun.

Uso:
    source venv/bin/activate
    python3 run_static.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _bootstrap  # noqa: F401  (auto-attiva venv del progetto se necessario)

import json
import time
from datetime import datetime, timezone
from typing import Iterable

from scraper.config import (
    CLUBS_FILE,
    DATA_DIR,
    LAST_UPDATE_FILE,
    PLAYERS_MAIN_FILE,
    PLAYERS_STATIC_FILE,
    ROSTERS_FILE,
)
from scraper.filter_target import filter_target_profiles
from scraper.http_client import TransfermarktClient
from scraper.leagues import scrape_all_leagues
from scraper.profiles import scrape_player_profile
from scraper.rosters import scrape_club_roster

PLAYERS_ALL_FILE = DATA_DIR / "players_all.json"
SAVE_EVERY = 10  # salva su disco ogni N giocatori


def _load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def _save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def step_clubs(client: TransfermarktClient) -> list[dict]:
    print("\n=== STEP 1/4: SCRAPE LEGHE ===")
    if CLUBS_FILE.exists():
        clubs = _load_json(CLUBS_FILE, [])
        print(f"  cache hit: {CLUBS_FILE.name} ({len(clubs)} clubs)")
        return clubs
    clubs = scrape_all_leagues(client)
    _save_json(CLUBS_FILE, clubs)
    print(f"  saved {len(clubs)} clubs to {CLUBS_FILE.name}")
    return clubs


def step_rosters(clubs: list[dict], client: TransfermarktClient) -> dict:
    print("\n=== STEP 2/4: SCRAPE ROSTERS ===")
    rosters = _load_json(ROSTERS_FILE, {})  # {tm_club_id (str) -> [players]}
    saved = 0
    for c in clubs:
        key = str(c["tm_club_id"])
        if key in rosters and rosters[key]:
            continue
        try:
            r = scrape_club_roster(c, client)
            rosters[key] = r
            saved += 1
            if saved % 5 == 0:
                _save_json(ROSTERS_FILE, rosters)
        except Exception as e:
            print(f"  [error] {c['name']}: {e}")
            rosters.setdefault(key, [])
    _save_json(ROSTERS_FILE, rosters)
    total_players = sum(len(v) for v in rosters.values())
    print(f"  done: {len(rosters)}/{len(clubs)} clubs, {total_players} players total")
    return rosters


def _all_player_ids(rosters: dict) -> Iterable[tuple[int, dict]]:
    """Yield (player_id, sample_meta) per ogni giocatore in rosters, dedup."""
    seen: set[int] = set()
    for club_id, players in rosters.items():
        for p in players:
            pid = p.get("tm_player_id")
            if pid is None or pid in seen:
                continue
            seen.add(pid)
            yield pid, p


def step_profiles(rosters: dict, client: TransfermarktClient) -> list[dict]:
    print("\n=== STEP 3/4: SCRAPE PROFILI (lungo) ===")
    profiles_by_id: dict[str, dict] = {}
    if PLAYERS_ALL_FILE.exists():
        loaded = _load_json(PLAYERS_ALL_FILE, [])
        for p in loaded:
            profiles_by_id[str(p["tm_player_id"])] = p
        print(f"  resume from cache: {len(profiles_by_id)} profiles already done")

    pending = [(pid, meta) for pid, meta in _all_player_ids(rosters) if str(pid) not in profiles_by_id]
    total = len(pending)
    print(f"  to fetch: {total} new profiles")

    started = time.monotonic()
    for i, (pid, meta) in enumerate(pending, 1):
        try:
            prof = scrape_player_profile(pid, client)
            # Aggiungi info dal roster (club di provenienza al momento dello scrape rosa)
            prof["roster_club_id"] = meta.get("tm_club_id")
            prof["roster_club_name"] = meta.get("club_name")
            profiles_by_id[str(pid)] = prof
        except Exception as e:
            print(f"    [{i}/{total}] FAIL pid={pid} ({meta.get('name_hint')}): {e}")
            continue

        if i % 10 == 0 or i == total:
            elapsed = time.monotonic() - started
            rate = i / elapsed if elapsed else 0
            eta = (total - i) / rate if rate else 0
            print(f"    [{i}/{total}] {meta.get('name_hint','?'):<28}  ETA: {int(eta//60)}m{int(eta%60):02d}s")
        if i % SAVE_EVERY == 0:
            _save_json(PLAYERS_ALL_FILE, list(profiles_by_id.values()))

    profiles = list(profiles_by_id.values())
    _save_json(PLAYERS_ALL_FILE, profiles)
    print(f"  saved {len(profiles)} profiles total to {PLAYERS_ALL_FILE.name}")
    return profiles


def step_filter_target(profiles: list[dict]) -> list[dict]:
    print("\n=== STEP 4/4: FILTRO TARGET ===")
    target = filter_target_profiles(profiles)
    _save_json(PLAYERS_MAIN_FILE, target)
    # Conserva la versione "static" come alias (sarà la fonte primaria della UI)
    _save_json(PLAYERS_STATIC_FILE, target)
    print(f"  total profiles: {len(profiles)}")
    print(f"  target-eligible: {len(target)} ({len(target)*100/max(len(profiles),1):.1f}%)")
    print(f"  saved to {PLAYERS_MAIN_FILE.name}")
    return target


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    client = TransfermarktClient()
    t0 = time.monotonic()
    try:
        clubs = step_clubs(client)
        rosters = step_rosters(clubs, client)
        profiles = step_profiles(rosters, client)
        target = step_filter_target(profiles)
    except KeyboardInterrupt:
        print("\n\n[INTERROTTO] Il progresso è già salvato. Rilancia per riprendere.")
        sys.exit(130)
    elapsed = int(time.monotonic() - t0)
    _save_json(LAST_UPDATE_FILE, {
        "static_completed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stats_completed_at": None,
        "elapsed_seconds_static": elapsed,
        "n_clubs": len(clubs),
        "n_profiles_total": len(profiles),
        "n_target": len(target),
    })
    print(f"\nDONE in {elapsed//60}m{elapsed%60}s")


if __name__ == "__main__":
    main()

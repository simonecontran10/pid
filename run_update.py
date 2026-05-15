"""
run_update.py — Aggiornamento automatico INCREMENTALE.

Da lanciare ogni 3-5 giorni (anche manualmente o via launchd).

Strategia ottimizzata: rifà solo le cose che cambiano davvero, salta tutto
il resto.

  1. RE-FETCH CLUBS (2 richieste, <1s)
     Rileva nuovi club (promossi/retrocessi) o cambi nome.

  2. RE-FETCH ROSTERS (36 richieste, ~1 min)
     Rileva nuovi giocatori in ogni rosa (trasferiti, promossi giovanili).

  3. SCRAPE PROFILI SOLO PER I NUOVI PLAYER_ID
     Confronta nuovi roster vs players_all.json esistente.
     Skip totale se 0 nuovi giocatori (caso comune nei refresh ravvicinati).

  4. RE-FILTER TARGET
     Aggiorna players_main.json includendo i nuovi giocatori target.

  5. ENRICH SORTITOUTSI + IMPORT WYSCOUT
     Idempotenti, costo ~1s.

  6. REFRESH STATS PER TUTTI I TARGET
     1 chiamata API per giocatore (~250 chiamate, ~5 min).
     Le presenze cambiano ogni giornata, conviene rifarle tutte.

  7. DOWNLOAD FOTO SOLO PER I NUOVI
     skip-se-esiste già attivo.

  8. UPDATE last_update.json con metriche dell'esecuzione.

Uso:
    python3 run_update.py
    python3 run_update.py --no-stats   # salta refresh stats (più veloce)
    python3 run_update.py --no-photos  # salta download foto
"""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _bootstrap  # noqa: F401  (auto-attiva venv del progetto se necessario)

import json
import subprocess
import time
from datetime import datetime
from typing import Optional

from scraper.config import (
    CLUBS_FILE,
    DATA_DIR,
    LAST_UPDATE_FILE,
    PLAYERS_MAIN_FILE,
    PLAYERS_STATIC_FILE,
    PLAYERS_STATS_FILE,
    ROSTERS_FILE,
    SEASONS,
)
from scraper.filter_target import filter_target_profiles
from scraper.http_client import TransfermarktClient
from scraper.leagues import scrape_all_leagues
from scraper.profiles import scrape_player_profile
from scraper.rosters import scrape_club_roster
from scraper.stats import scrape_player_stats

PLAYERS_ALL_FILE = DATA_DIR / "players_all.json"
SAVE_EVERY = 10


def _load(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _section(title: str) -> None:
    bar = "=" * 70
    print(f"\n{bar}\n  {title}\n{bar}")


def step_refresh_clubs(client: TransfermarktClient, prev_clubs: list[dict]) -> tuple[list[dict], int]:
    """Rifà la lista club. Ritorna (clubs, n_new)."""
    _section("STEP 1/7 — REFRESH CLUBS")
    new_clubs = scrape_all_leagues(client)
    prev_ids = {c["tm_club_id"] for c in prev_clubs}
    new_ids = {c["tm_club_id"] for c in new_clubs}
    added = new_ids - prev_ids
    removed = prev_ids - new_ids
    if added:
        print(f"  + nuovi club: {len(added)} ({sorted(added)})")
    if removed:
        print(f"  - club rimossi: {len(removed)} ({sorted(removed)})")
    if not added and not removed:
        print(f"  no changes ({len(new_clubs)} clubs)")
    _save(CLUBS_FILE, new_clubs)
    return new_clubs, len(added)


def step_refresh_rosters(clubs: list[dict], client: TransfermarktClient,
                         prev_rosters: dict) -> tuple[dict, set[int]]:
    """Rifà tutte le rose. Ritorna (rosters, set di nuovi player_id mai visti)."""
    _section("STEP 2/7 — REFRESH ROSTERS")
    # Tutti i player_id già scrapati (in players_all.json)
    prev_profiles = _load(PLAYERS_ALL_FILE, [])
    known_player_ids = {p["tm_player_id"] for p in prev_profiles}

    new_rosters: dict[str, list[dict]] = {}
    new_player_ids: set[int] = set()
    for c in clubs:
        try:
            r = scrape_club_roster(c, client)
            new_rosters[str(c["tm_club_id"])] = r
            for p in r:
                if p["tm_player_id"] not in known_player_ids:
                    new_player_ids.add(p["tm_player_id"])
        except Exception as e:
            print(f"  [error] {c['name']}: {e}")
            new_rosters[str(c["tm_club_id"])] = prev_rosters.get(str(c["tm_club_id"]), [])

    _save(ROSTERS_FILE, new_rosters)
    total = sum(len(v) for v in new_rosters.values())
    print(f"  total players in rosters: {total}")
    print(f"  nuovi giocatori (mai scrapati prima): {len(new_player_ids)}")
    return new_rosters, new_player_ids


def step_scrape_new_profiles(new_ids: set[int], rosters: dict,
                             client: TransfermarktClient) -> int:
    """Scrape profili dei NUOVI giocatori. Ritorna n profili scrapati."""
    _section("STEP 3/7 — SCRAPE PROFILI NUOVI")
    if not new_ids:
        print("  nessun nuovo giocatore da scrapare. SKIP.")
        return 0

    # Lookup roster meta per ogni nuovo id
    meta_by_id: dict[int, dict] = {}
    for club_id, players in rosters.items():
        for p in players:
            if p["tm_player_id"] in new_ids:
                meta_by_id[p["tm_player_id"]] = p

    # Carica profili esistenti per merge
    profiles_by_id: dict[str, dict] = {}
    existing = _load(PLAYERS_ALL_FILE, [])
    for p in existing:
        profiles_by_id[str(p["tm_player_id"])] = p

    print(f"  da scrapare: {len(new_ids)}")
    started = time.monotonic()
    done = 0
    for pid in sorted(new_ids):
        meta = meta_by_id.get(pid, {})
        try:
            prof = scrape_player_profile(pid, client)
            prof["roster_club_id"] = meta.get("tm_club_id")
            prof["roster_club_name"] = meta.get("club_name")
            profiles_by_id[str(pid)] = prof
            done += 1
            print(f"    [{done}/{len(new_ids)}] {prof.get('full_name'):<28}  ({meta.get('club_name')})")
        except Exception as e:
            print(f"    [{done}/{len(new_ids)}] FAIL pid={pid}: {e}")
        if done % SAVE_EVERY == 0:
            _save(PLAYERS_ALL_FILE, list(profiles_by_id.values()))
    _save(PLAYERS_ALL_FILE, list(profiles_by_id.values()))
    elapsed = int(time.monotonic() - started)
    print(f"  done in {elapsed}s")
    return done


def step_refilter_target() -> tuple[int, int]:
    """Riapplica il filtro target su players_all.json. Ritorna (n_target, n_new_target)."""
    _section("STEP 4/7 — RE-FILTER TARGET")
    all_profiles = _load(PLAYERS_ALL_FILE, [])
    target = filter_target_profiles(all_profiles)

    prev_target = _load(PLAYERS_MAIN_FILE, [])
    prev_ids = {p["tm_player_id"] for p in prev_target}
    new_target_count = sum(1 for p in target if p["tm_player_id"] not in prev_ids)

    _save(PLAYERS_MAIN_FILE, target)
    _save(PLAYERS_STATIC_FILE, target)
    print(f"  total target: {len(target)}")
    print(f"  nuovi nello snapshot: {new_target_count}")
    return len(target), new_target_count


def step_enrich_sortitoutsi() -> None:
    _section("STEP 5/7 — ENRICH SORTITOUTSI")
    # Riusa lo stesso modulo
    from enrich_sortitoutsi import main as enrich_main
    enrich_main()


def step_import_wyscout() -> None:
    _section("STEP 5b/7 — IMPORT WYSCOUT")
    try:
        from import_wyscout import main as wyscout_main
        wyscout_main()
    except FileNotFoundError as e:
        print(f"  [skip] Wyscout files non disponibili: {e}")


def step_refresh_stats(seasons: list[int], client: TransfermarktClient,
                       skip: bool = False) -> int:
    _section("STEP 6/7 — REFRESH STATS")
    if skip:
        print("  --no-stats: SKIP")
        return 0
    target = _load(PLAYERS_MAIN_FILE, [])
    if not target:
        print("  no target players. SKIP.")
        return 0
    print(f"  refreshing stats per {len(target)} giocatori")
    started = time.monotonic()
    out: list[dict] = []
    for i, p in enumerate(target, 1):
        pid = p["tm_player_id"]
        try:
            s = scrape_player_stats(pid, client, seasons=seasons)
            out.append(s)
        except Exception as e:
            print(f"    [{i}/{len(target)}] FAIL {p.get('full_name')}: {e}")
            continue
        if i % 25 == 0 or i == len(target):
            elapsed = time.monotonic() - started
            rate = i / elapsed if elapsed else 0
            eta = (len(target) - i) / rate if rate else 0
            print(f"    [{i}/{len(target)}]  ETA {int(eta//60)}m{int(eta%60):02d}s")
    _save(PLAYERS_STATS_FILE, out)
    elapsed = int(time.monotonic() - started)
    print(f"  done in {elapsed//60}m{elapsed%60}s")
    return len(out)


def step_download_photos(skip: bool = False) -> None:
    _section("STEP 7/7 — DOWNLOAD FOTO (skip-se-esiste)")
    if skip:
        print("  --no-photos: SKIP")
        return
    from download_photos import main as photos_main
    photos_main()


def main() -> None:
    no_stats = "--no-stats" in sys.argv
    no_photos = "--no-photos" in sys.argv

    started_at = datetime.utcnow()
    t0 = time.monotonic()
    client = TransfermarktClient()

    metrics = {"started_at": started_at.strftime("%Y-%m-%dT%H:%M:%SZ")}

    try:
        prev_clubs = _load(CLUBS_FILE, [])
        prev_rosters = _load(ROSTERS_FILE, {})

        clubs, n_new_clubs = step_refresh_clubs(client, prev_clubs)
        rosters, new_pids = step_refresh_rosters(clubs, client, prev_rosters)
        n_new_profiles = step_scrape_new_profiles(new_pids, rosters, client)
        n_target, n_new_target = step_refilter_target()
        step_enrich_sortitoutsi()
        step_import_wyscout()
        n_stats = step_refresh_stats(SEASONS, client, skip=no_stats)
        step_download_photos(skip=no_photos)

        metrics.update({
            "n_clubs": len(clubs),
            "n_new_clubs": n_new_clubs,
            "n_new_player_ids_in_rosters": len(new_pids),
            "n_new_profiles_scraped": n_new_profiles,
            "n_target": n_target,
            "n_new_target": n_new_target,
            "n_stats_refreshed": n_stats,
            "elapsed_seconds": int(time.monotonic() - t0),
            "completed_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "result": "ok",
        })
    except KeyboardInterrupt:
        metrics["result"] = "interrupted"
        metrics["elapsed_seconds"] = int(time.monotonic() - t0)
    except Exception as e:
        metrics["result"] = "error"
        metrics["error"] = f"{type(e).__name__}: {e}"
        metrics["elapsed_seconds"] = int(time.monotonic() - t0)
        raise
    finally:
        _save(LAST_UPDATE_FILE, metrics)

    print(f"\n{'='*70}\n  COMPLETATO in {metrics['elapsed_seconds']//60}m{metrics['elapsed_seconds']%60}s\n{'='*70}")
    print(f"  target totali: {metrics.get('n_target')}")
    print(f"  nuovi profili scrapati: {metrics.get('n_new_profiles_scraped')}")
    print(f"  stats aggiornate: {metrics.get('n_stats_refreshed')}")


if __name__ == "__main__":
    main()

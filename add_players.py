"""
add_players.py — Aggiunge nuovi giocatori al DB partendo da una lista di URL
Transfermarkt (un URL per riga, anche con righe vuote).

Per ogni URL:
  1. Estrae tm_player_id
  2. Scrape profilo (nome, foto, anagrafica, ruolo, club, ecc.)
  3. Scrape stats (presenze 24/25 + 25/26, club + nazionale)
  4. Aggiunge a players_all.json + (se saudita) a players_saudi.json
  5. Aggiorna players_stats.json

Alla fine lancia enrich_sortitoutsi + download_photos.

Uso:
  python3 add_players.py urls.txt
  python3 add_players.py            # legge URL da stdin
  python3 add_players.py --apply    # come default, già attivo (no-op flag)
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
import _bootstrap  # noqa: F401  (auto-attiva il venv del progetto)

import json
import re
import subprocess
import time

from scraper.config import (
    DATA_DIR,
    PLAYERS_SAUDI_FILE,
    PLAYERS_STATIC_FILE,
    PLAYERS_STATS_FILE,
    SEASONS,
)
from scraper.filter_target import is_target_eligible as is_saudi_eligible  # alias, da rinominare in cleanup futuro
from scraper.http_client import TransfermarktClient
from scraper.profiles import scrape_player_profile
from scraper.stats import scrape_player_stats

PLAYERS_ALL_FILE = DATA_DIR / "players_all.json"


def _load(p: Path, default):
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def _save(p: Path, data) -> None:
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def extract_tm_id(line: str) -> int | None:
    line = line.strip()
    if not line:
        return None
    m = re.search(r"/spieler/(\d+)", line)
    if m:
        return int(m.group(1))
    if line.isdigit():
        return int(line)
    return None


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args:
        text = Path(args[0]).read_text(encoding="utf-8")
    else:
        print("Incolla gli URL Transfermarkt (Ctrl+D per terminare):")
        text = sys.stdin.read()

    ids: list[int] = []
    seen: set[int] = set()
    for line in text.splitlines():
        tid = extract_tm_id(line)
        if tid and tid not in seen:
            ids.append(tid)
            seen.add(tid)

    print(f"\nTrovati {len(ids)} tm_player_id unici.")

    # Carica DB esistente
    profiles_by_id: dict[int, dict] = {}
    for p in _load(PLAYERS_ALL_FILE, []):
        profiles_by_id[p["tm_player_id"]] = p
    saudi_by_id: dict[int, dict] = {}
    for p in _load(PLAYERS_SAUDI_FILE, []):
        saudi_by_id[p["tm_player_id"]] = p
    stats_by_id: dict[int, dict] = {}
    for s in _load(PLAYERS_STATS_FILE, []):
        stats_by_id[s["tm_player_id"]] = s

    client = TransfermarktClient()
    n_added = n_updated = n_saudi = n_failed = 0
    started = time.monotonic()

    for i, pid in enumerate(ids, 1):
        existing = profiles_by_id.get(pid)
        try:
            prof = scrape_player_profile(pid, client)
            # Mantieni i campi roster_* se esistevano
            if existing:
                prof["roster_club_id"] = existing.get("roster_club_id") or prof.get("current_club_id")
                prof["roster_club_name"] = existing.get("roster_club_name") or prof.get("current_club_name")
                n_updated += 1
            else:
                prof["roster_club_id"] = prof.get("current_club_id")
                prof["roster_club_name"] = prof.get("current_club_name")
                n_added += 1
            profiles_by_id[pid] = prof

            saudi_flag = bool(prof.get("is_saudi_eligible"))
            if saudi_flag:
                saudi_by_id[pid] = prof
                n_saudi += 1
                # scrape stats SOLO per i sauditi
                try:
                    s = scrape_player_stats(pid, client, seasons=SEASONS)
                    stats_by_id[pid] = s
                except Exception as e:
                    print(f"    [stats fail] pid={pid}: {e}")

            tag = "SAUDI ✓" if saudi_flag else "non-saudi"
            print(f"  [{i}/{len(ids)}]  {prof.get('full_name','?'):<32}  ({prof.get('current_club_name') or '-'})  [{tag}]")
        except Exception as e:
            n_failed += 1
            print(f"  [{i}/{len(ids)}]  FAIL pid={pid}: {type(e).__name__}: {e}")

        if i % 10 == 0:
            _save(PLAYERS_ALL_FILE, list(profiles_by_id.values()))
            _save(PLAYERS_SAUDI_FILE, list(saudi_by_id.values()))
            _save(PLAYERS_STATIC_FILE, list(saudi_by_id.values()))
            _save(PLAYERS_STATS_FILE, list(stats_by_id.values()))

    _save(PLAYERS_ALL_FILE, list(profiles_by_id.values()))
    _save(PLAYERS_SAUDI_FILE, list(saudi_by_id.values()))
    _save(PLAYERS_STATIC_FILE, list(saudi_by_id.values()))
    _save(PLAYERS_STATS_FILE, list(stats_by_id.values()))

    elapsed = int(time.monotonic() - started)
    print(f"\n{'='*60}")
    print(f"  Aggiunti: {n_added}    Aggiornati: {n_updated}    Sauditi: {n_saudi}    Falliti: {n_failed}")
    print(f"  Elapsed: {elapsed//60}m{elapsed%60}s")

    print("\n→ enrich_sortitoutsi.py ...")
    subprocess.run([sys.executable, "enrich_sortitoutsi.py"], cwd=ROOT, check=False)
    print("\n→ download_photos.py ...")
    subprocess.run([sys.executable, "download_photos.py"], cwd=ROOT, check=False)
    print("\nFatto. Hard reload del browser (⌘⇧R) per vedere i nuovi giocatori.")


if __name__ == "__main__":
    main()

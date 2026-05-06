"""
run_stats.py — Scrape stats per i giocatori sauditi (presenze stagione).

Riusa data/players_saudi.json (prodotto da run_static.py) e per ogni
giocatore chiama l'API /ceapi/performance-game/{id}, aggregando per
(stagione, competizione, club/nazionale).

Resume:
- Se data/players_stats.json esiste già, le entries esistenti vengono saltate
  a meno che non sia passato --refresh (rifa tutto).

Tempo previsto: ~5-7 min sul primo run, idem per refresh.

Uso:
    source venv/bin/activate
    python3 run_stats.py
    python3 run_stats.py --refresh   # forza refresh di tutti
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _bootstrap  # noqa: F401  (auto-attiva venv del progetto se necessario)

import json
import time
from datetime import datetime, timezone

from scraper.config import (
    LAST_UPDATE_FILE,
    PLAYERS_SAUDI_FILE,
    PLAYERS_STATS_FILE,
    SEASONS,
)
from scraper.http_client import TransfermarktClient
from scraper.stats import scrape_player_stats

SAVE_EVERY = 10


def _load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def _save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    refresh = "--refresh" in sys.argv

    if not PLAYERS_SAUDI_FILE.exists():
        print(f"[FATAL] {PLAYERS_SAUDI_FILE} non esiste. Lancia prima run_static.py")
        sys.exit(1)
    saudi = _load_json(PLAYERS_SAUDI_FILE, [])
    print(f"Saudi players to fetch stats for: {len(saudi)}")

    stats_by_id: dict[str, dict] = {}
    if not refresh and PLAYERS_STATS_FILE.exists():
        loaded = _load_json(PLAYERS_STATS_FILE, [])
        for s in loaded:
            stats_by_id[str(s["tm_player_id"])] = s
        print(f"resume from cache: {len(stats_by_id)} stats already done")

    pending = [p for p in saudi if str(p["tm_player_id"]) not in stats_by_id]
    print(f"to fetch: {len(pending)}")

    client = TransfermarktClient()
    t0 = time.monotonic()
    for i, p in enumerate(pending, 1):
        pid = p["tm_player_id"]
        try:
            s = scrape_player_stats(pid, client, seasons=SEASONS)
            stats_by_id[str(pid)] = s
        except Exception as e:
            print(f"  [{i}/{len(pending)}] FAIL pid={pid} ({p.get('full_name')}): {e}")
            continue
        if i % 10 == 0 or i == len(pending):
            elapsed = time.monotonic() - t0
            rate = i / elapsed if elapsed else 0
            eta = (len(pending) - i) / rate if rate else 0
            print(f"  [{i}/{len(pending)}] {p.get('full_name','?'):<28} ETA: {int(eta//60)}m{int(eta%60):02d}s")
        if i % SAVE_EVERY == 0:
            _save_json(PLAYERS_STATS_FILE, list(stats_by_id.values()))

    _save_json(PLAYERS_STATS_FILE, list(stats_by_id.values()))
    elapsed = int(time.monotonic() - t0)
    print(f"\nDONE in {elapsed//60}m{elapsed%60}s. Saved: {PLAYERS_STATS_FILE.name}")

    # Aggiorna last_update
    last = _load_json(LAST_UPDATE_FILE, {})
    last["stats_completed_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    last["elapsed_seconds_stats"] = elapsed
    last["n_stats"] = len(stats_by_id)
    _save_json(LAST_UPDATE_FILE, last)


if __name__ == "__main__":
    main()

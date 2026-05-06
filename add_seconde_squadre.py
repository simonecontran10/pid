"""
add_seconde_squadre.py — Aggiunge le 4 seconde squadre italiane (Serie C) al DB
come nuova lega `IT3` (Seconde Squadre).

Pipeline:
  1. Crea/aggiorna data/it3_clubs.json con i 4 club hardcoded
  2. Per ogni club:
     a. Scarica la rosa da Transfermarkt (riusa scrape_club_roster)
     b. Per ogni giocatore: scrape_player_profile + (se eligible) scrape_player_stats
     c. Riusa il logo SortItOutSi della prima squadra (Inter/Milan/Juve/Atalanta)
  3. Aggiorna clubs.json master aggregando i 4 nuovi
  4. Salva players_main.json (nuovi giocatori) + players_stats.json
  5. Lancia enrich_sortitoutsi.py + download_photos.py per face/loghi mancanti

Idempotente: rilanciandolo, club già presenti vengono aggiornati senza duplicati.

Uso:
    python3 add_seconde_squadre.py              # esegue la pipeline completa
    python3 add_seconde_squadre.py --dry-run    # mostra solo cosa farebbe
    python3 add_seconde_squadre.py --skip-stats # scarica profili ma non stats (più veloce)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
import _bootstrap  # noqa: F401

from scraper.config import (
    CLUBS_FILE,
    DATA_DIR,
    PLAYERS_MAIN_FILE,
    PLAYERS_STATIC_FILE,
    PLAYERS_STATS_FILE,
    SEASONS,
)
from scraper.http_client import TransfermarktClient
from scraper.profiles import scrape_player_profile
from scraper.rosters import scrape_club_roster
from scraper.stats import scrape_player_stats

PLAYERS_ALL_FILE = DATA_DIR / "players_all.json"
IT3_CLUBS_FILE = DATA_DIR / "it3_clubs.json"

# === Hardcoded: i 4 club delle Seconde Squadre + il loro club di prima squadra ===
# parent_tm_id: usato per riusare il sortitoutsi_team_id del club di prima squadra
# (le seconde squadre non hanno entry SortItOutSi separata)
SECONDE_SQUADRE = [
    {
        "tm_club_id": 41119,
        "name": "Inter U23",
        "slug": "inter-u23",
        "league_id": "IT3",
        "league_name": "Seconde Squadre",
        "club_url": "https://www.transfermarkt.com/inter-u23/startseite/verein/41119/saison_id/2025",
        "parent_tm_id": 46,  # Inter Milan
        "parent_name": "Inter Milan",
    },
    {
        "tm_club_id": 41107,
        "name": "Milan Futuro",
        "slug": "milan-futuro",
        "league_id": "IT3",
        "league_name": "Seconde Squadre",
        "club_url": "https://www.transfermarkt.com/milan-futuro/startseite/verein/41107/saison_id/2025",
        "parent_tm_id": 5,  # AC Milan
        "parent_name": "AC Milan",
    },
    {
        "tm_club_id": 41101,
        "name": "Juventus Next Gen",
        "slug": "juventus-next-gen",
        "league_id": "IT3",
        "league_name": "Seconde Squadre",
        "club_url": "https://www.transfermarkt.com/juventus-next-gen/startseite/verein/41101/saison_id/2025",
        "parent_tm_id": 506,  # Juventus
        "parent_name": "Juventus FC",
    },
    {
        "tm_club_id": 41110,
        "name": "Atalanta U23",
        "slug": "atalanta-u23",
        "league_id": "IT3",
        "league_name": "Seconde Squadre",
        "club_url": "https://www.transfermarkt.com/atalanta-u23/startseite/verein/41110/saison_id/2025",
        "parent_tm_id": 800,  # Atalanta
        "parent_name": "Atalanta BC",
    },
]


def _load(p: Path, default):
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def _save(p: Path, data) -> None:
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def enrich_with_parent_logos(seconde: list[dict], all_clubs: list[dict]) -> None:
    """Per ogni seconda squadra, riusa il sortitoutsi_team_id del club di prima
    squadra (matching via parent_tm_id)."""
    parents_by_id = {c["tm_club_id"]: c for c in all_clubs}
    for s in seconde:
        parent = parents_by_id.get(s["parent_tm_id"])
        if not parent:
            print(f"  [warn] parent {s['parent_name']} (tm={s['parent_tm_id']}) "
                  f"non trovato in clubs.json — logo mancante per {s['name']}")
            continue
        sots_id = parent.get("sortitoutsi_team_id")
        if not sots_id:
            print(f"  [warn] parent {s['parent_name']} senza sortitoutsi_team_id — "
                  f"logo mancante per {s['name']}")
            continue
        s["sortitoutsi_team_id"] = sots_id
        s["sortitoutsi_logo_url"] = parent.get("sortitoutsi_logo_url")
        # Per il logo locale: punta al file della prima squadra (no copia, riferimento)
        # — il frontend leggerà direttamente lo stesso file
        s["sortitoutsi_logo_local"] = parent.get("sortitoutsi_logo_local")
        print(f"  + {s['name']:<25} ← logo da {parent['name']:<20} (sots={sots_id})")


def merge_clubs_master(seconde: list[dict], all_clubs: list[dict]) -> list[dict]:
    """Inserisce/aggiorna le 4 seconde squadre in clubs.json master.
    Posizione: dopo IT2, prima di IJ1 (visualizzazione → l'ordine non conta nel JSON,
    è il frontend che ordina per league_id)."""
    by_id = {c["tm_club_id"]: c for c in all_clubs}
    for s in seconde:
        # Pulisci campi non-master (parent_*, slug)
        s_clean = {k: v for k, v in s.items() if k not in ("parent_tm_id", "parent_name")}
        by_id[s["tm_club_id"]] = s_clean
    # Mantieni l'ordine originale e appendi le nuove in fondo (frontend ordina via league_id)
    existing_ids = {c["tm_club_id"] for c in all_clubs}
    new_clubs = list(all_clubs)
    for s in seconde:
        s_clean = {k: v for k, v in s.items() if k not in ("parent_tm_id", "parent_name")}
        if s["tm_club_id"] in existing_ids:
            # Update in place
            for i, c in enumerate(new_clubs):
                if c["tm_club_id"] == s["tm_club_id"]:
                    new_clubs[i] = s_clean
                    break
        else:
            new_clubs.append(s_clean)
    return new_clubs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="non scrive nulla")
    parser.add_argument("--skip-stats", action="store_true",
                        help="scarica profili giocatori ma salta lo scrape stats (più veloce)")
    parser.add_argument("--skip-photos", action="store_true",
                        help="non lanciare enrich_sortitoutsi e download_photos a fine pipeline")
    args = parser.parse_args()

    # === Step 1 — Crea/aggiorna it3_clubs.json ===
    print("=" * 70)
    print("STEP 1 — data/it3_clubs.json")
    print("=" * 70)

    # Carica master clubs.json per riusare i loghi delle prime squadre
    all_clubs = _load(CLUBS_FILE, [])
    print(f"clubs.json: {len(all_clubs)} club totali")

    enrich_with_parent_logos(SECONDE_SQUADRE, all_clubs)

    if not args.dry_run:
        # Salva versione "leggera" senza parent_* in it3_clubs.json
        it3_clean = [
            {k: v for k, v in s.items() if k not in ("parent_tm_id", "parent_name")}
            for s in SECONDE_SQUADRE
        ]
        _save(IT3_CLUBS_FILE, it3_clean)
        print(f"\n✓ {IT3_CLUBS_FILE.name} salvato ({len(it3_clean)} club)")

    # === Step 2 — Scrape rose + giocatori ===
    print()
    print("=" * 70)
    print("STEP 2 — scrape rose Transfermarkt")
    print("=" * 70)

    client = TransfermarktClient()
    all_roster_pids: list[int] = []
    rosters_by_club: dict[int, list[dict]] = {}

    for club in SECONDE_SQUADRE:
        try:
            roster = scrape_club_roster(club, client=client)
            rosters_by_club[club["tm_club_id"]] = roster
            all_roster_pids.extend(p["tm_player_id"] for p in roster)
        except Exception as e:
            print(f"  [error] roster {club['name']}: {type(e).__name__}: {e}")

    # Dedup
    seen: set[int] = set()
    unique_pids: list[int] = []
    for pid in all_roster_pids:
        if pid not in seen:
            seen.add(pid)
            unique_pids.append(pid)

    print(f"\nTotale giocatori unici da scrappare: {len(unique_pids)}")

    if args.dry_run:
        print("\n[dry-run] mi fermo qui — nessuna scrittura")
        return

    # === Step 3 — Scrape profili + stats ===
    print()
    print("=" * 70)
    print("STEP 3 — profili giocatori + stats")
    print("=" * 70)

    profiles_by_id: dict[int, dict] = {p["tm_player_id"]: p for p in _load(PLAYERS_ALL_FILE, [])}
    main_by_id: dict[int, dict] = {p["tm_player_id"]: p for p in _load(PLAYERS_MAIN_FILE, [])}
    stats_by_id: dict[int, dict] = {s["tm_player_id"]: s for s in _load(PLAYERS_STATS_FILE, [])}

    # Build map pid → club info (per popolare current_club + roster_club correttamente)
    pid_to_club: dict[int, dict] = {}
    for club in SECONDE_SQUADRE:
        for p in rosters_by_club.get(club["tm_club_id"], []):
            pid_to_club[p["tm_player_id"]] = {
                "tm_club_id": club["tm_club_id"],
                "club_name": club["name"],
            }

    n_added = n_updated = n_eligible = n_failed = 0
    started = time.monotonic()

    for i, pid in enumerate(unique_pids, 1):
        existing = profiles_by_id.get(pid)
        try:
            prof = scrape_player_profile(pid, client)

            # Forza current_club_id/name dalla rosa scrappata se TM dice altro
            # (es. giocatore in prestito con squadra diversa nel profilo)
            club_info = pid_to_club.get(pid)
            if club_info:
                # roster_club_* = club della rosa attuale (Inter U23, Milan Futuro, ecc.)
                prof["roster_club_id"] = club_info["tm_club_id"]
                prof["roster_club_name"] = club_info["club_name"]
            elif existing:
                prof["roster_club_id"] = existing.get("roster_club_id") or prof.get("current_club_id")
                prof["roster_club_name"] = existing.get("roster_club_name") or prof.get("current_club_name")
            else:
                prof["roster_club_id"] = prof.get("current_club_id")
                prof["roster_club_name"] = prof.get("current_club_name")

            if existing:
                n_updated += 1
            else:
                n_added += 1
            profiles_by_id[pid] = prof

            eligible = bool(prof.get("is_saudi_eligible"))  # alias storico, in realtà = is_target_eligible
            if eligible:
                main_by_id[pid] = prof
                n_eligible += 1
                if not args.skip_stats:
                    try:
                        s = scrape_player_stats(pid, client, seasons=SEASONS)
                        stats_by_id[pid] = s
                    except Exception as e:
                        print(f"    [stats fail] pid={pid}: {e}")

            tag = "TARGET ✓" if eligible else "non-target"
            club_lbl = prof.get("current_club_name") or "-"
            print(f"  [{i:>3}/{len(unique_pids)}]  "
                  f"{prof.get('full_name','?')[:28]:<28}  "
                  f"({club_lbl[:22]:<22})  [{tag}]")
        except Exception as e:
            n_failed += 1
            print(f"  [{i:>3}/{len(unique_pids)}]  FAIL pid={pid}: {type(e).__name__}: {e}")

        if i % 10 == 0:
            _save(PLAYERS_ALL_FILE, list(profiles_by_id.values()))
            _save(PLAYERS_MAIN_FILE, list(main_by_id.values()))
            _save(PLAYERS_STATIC_FILE, list(main_by_id.values()))
            _save(PLAYERS_STATS_FILE, list(stats_by_id.values()))

    # Final save
    _save(PLAYERS_ALL_FILE, list(profiles_by_id.values()))
    _save(PLAYERS_MAIN_FILE, list(main_by_id.values()))
    _save(PLAYERS_STATIC_FILE, list(main_by_id.values()))
    _save(PLAYERS_STATS_FILE, list(stats_by_id.values()))

    elapsed = int(time.monotonic() - started)
    print(f"\nProfili: aggiunti={n_added} aggiornati={n_updated} "
          f"eligible={n_eligible} falliti={n_failed}  "
          f"({elapsed//60}m{elapsed%60}s)")

    # === Step 4 — clubs.json master ===
    print()
    print("=" * 70)
    print("STEP 4 — merge in clubs.json master")
    print("=" * 70)

    new_clubs = merge_clubs_master(SECONDE_SQUADRE, all_clubs)
    _save(CLUBS_FILE, new_clubs)
    print(f"✓ clubs.json: {len(new_clubs)} club totali "
          f"(+{len(new_clubs) - len(all_clubs)} nuovi)")

    # === Step 5 — enrich_sortitoutsi + download_photos ===
    if not args.skip_photos:
        print()
        print("=" * 70)
        print("STEP 5 — enrich_sortitoutsi + download_photos")
        print("=" * 70)
        for script in ("enrich_sortitoutsi.py", "download_photos.py"):
            print(f"\n→ {script}")
            subprocess.run([sys.executable, script], cwd=ROOT, check=False)

    print()
    print("=" * 70)
    print("✓ FATTO. Ora:")
    print("  1. Aggiorna il frontend (i18n.js, index.html, app.js) per mostrare IT3")
    print("  2. git add -A && git commit -m 'feat: aggiunte 4 seconde squadre' && git push")
    print("=" * 70)


if __name__ == "__main__":
    main()

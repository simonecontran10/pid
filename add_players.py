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
    CLUBS_FILE,
    SEASONS,
)
from scraper.filter_target import is_target_eligible as is_saudi_eligible  # alias, da rinominare in cleanup futuro
from scraper.http_client import TransfermarktClient
from scraper.profiles import scrape_player_profile
from scraper.stats import scrape_player_stats
from scraper.leagues import scrape_club_by_id

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

    # ============ AUTO-CREAZIONE CLUB ============
    # Per ogni giocatore aggiunto/aggiornato, verifico che il suo current_club_id sia in clubs.json
    # Se manca, scrape il club da TM e lo aggiungo
    print("\n→ Verifica club nuovi...")
    clubs_data = _load(CLUBS_FILE, [])
    existing_club_ids = {int(c.get("tm_club_id")) for c in clubs_data if c.get("tm_club_id")}
    
    new_club_ids = set()
    for pid in ids:
        prof = profiles_by_id.get(pid)
        if not prof:
            continue
        ccid = prof.get("current_club_id")
        if ccid and int(ccid) not in existing_club_ids:
            new_club_ids.add(int(ccid))
    
    n_clubs_added = 0
    if new_club_ids:
        print(f"  Trovati {len(new_club_ids)} club nuovi da scrapare")
        for cid in new_club_ids:
            try:
                club = scrape_club_by_id(cid, client)
                if club:
                    clubs_data.append(club)
                    n_clubs_added += 1
                    print(f"  + {club['name']} ({club['league_id']})")
                else:
                    print(f"  ✗ scrape_club_by_id({cid}) fallito")
            except Exception as e:
                print(f"  ✗ club {cid}: {type(e).__name__}: {e}")
        if n_clubs_added > 0:
            _save(CLUBS_FILE, clubs_data)
            print(f"  Salvati {n_clubs_added} nuovi club a {CLUBS_FILE.name}")
    else:
        print("  Nessun club nuovo da aggiungere")

    # === SOTS overrides forniti dall'utente via env SOTS_URLS ===
    # Il workflow add_player.yml espone SOTS_URLS con gli URL SortItOutSi
    # corrispondenti agli URL TM nello stesso ordine (vuoto = no override).
    # Quando presente per un giocatore, applichiamo subito il match SOTS:
    # - estraiamo sots_id dall'URL
    # - scarichiamo la face PNG
    # - aggiorniamo sortitoutsi_person_id + face_url + face_local_lookup + profile_url
    # Questo evita di dover passare per find_more_sots_matches.py settimanale.
    import os as _os
    sots_urls_raw = _os.environ.get("SOTS_URLS", "").strip()
    if sots_urls_raw:
        sots_urls_list = [s.strip() for s in sots_urls_raw.split("\n")]
        # Padding a len(ids) con stringhe vuote per matchare posizionalmente
        while len(sots_urls_list) < len(ids):
            sots_urls_list.append("")
        
        print("\n→ Applicazione override SOTS dall'admin...")
        n_sots_applied = 0
        n_sots_skipped = 0
        
        import requests as _req
        from scraper.config import USER_AGENTS as _UA
        from scraper.sortitoutsi import face_url as _face_url, profile_url as _profile_url
        
        PHOTOS_DIR = ROOT / "data" / "photos" / "players_sots_lookup"
        PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
        session = _req.Session()
        
        # Carico i 3 JSON players per aggiornarli in place
        players_main_data = _load(PLAYERS_SAUDI_FILE, [])
        players_all_data = _load(PLAYERS_ALL_FILE, [])
        players_static_data = _load(PLAYERS_STATIC_FILE, [])
        
        for pid, sots_url in zip(ids, sots_urls_list):
            if not sots_url:
                continue
            m = re.search(r"/person/(\d+)/", sots_url)
            if not m:
                print(f"  ✗ {pid}: URL SOTS non parsabile: {sots_url[:60]}")
                n_sots_skipped += 1
                continue
            sots_id = int(m.group(1))
            
            # Scarica face PNG (idempotente: skip se gia esistente >200 bytes)
            face_path = PHOTOS_DIR / f"{sots_id}.png"
            face_local = f"photos/players_sots_lookup/{sots_id}.png"
            if not (face_path.exists() and face_path.stat().st_size > 200):
                try:
                    cdn_url = f"https://sortitoutsi.b-cdn.net/uploads/face/face_{sots_id}.png"
                    r = session.get(cdn_url, headers={"User-Agent": _UA[0]}, timeout=15)
                    if r.status_code == 200 and r.content and len(r.content) > 200:
                        face_path.write_bytes(r.content)
                        print(f"  ✓ {pid}: face scaricata sots_id={sots_id}")
                    else:
                        print(f"  ⚠ {pid}: face download status {r.status_code} sots_id={sots_id}")
                        face_local = None
                except Exception as e:
                    print(f"  ✗ {pid}: face download error: {e}")
                    face_local = None
            else:
                print(f"  ✓ {pid}: face gia in cache sots_id={sots_id}")
            
            # Aggiorna i 3 JSON nel record del giocatore
            full_name = None
            for data_list in (players_main_data, players_all_data, players_static_data):
                for p_rec in data_list:
                    if p_rec.get("tm_player_id") == pid:
                        full_name = full_name or p_rec.get("full_name")
                        p_rec["sortitoutsi_person_id"] = sots_id
                        p_rec["sortitoutsi_face_url"] = _face_url(sots_id)
                        p_rec["sortitoutsi_profile_url"] = _profile_url(sots_id, p_rec.get("full_name"))
                        if face_local:
                            p_rec["sortitoutsi_face_local_lookup"] = face_local
                        break
            
            n_sots_applied += 1
            time.sleep(0.3)  # gentile con SOTS CDN
        
        # Salva i 3 JSON aggiornati
        if n_sots_applied > 0:
            _save(PLAYERS_SAUDI_FILE, players_main_data)
            _save(PLAYERS_ALL_FILE, players_all_data)
            _save(PLAYERS_STATIC_FILE, players_static_data)
            print(f"  Applicati {n_sots_applied} override SOTS, skippati {n_sots_skipped}")

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

"""
add_players.py — Aggiunge nuovi giocatori al DB partendo da una lista di URL
Transfermarkt (un URL per riga, anche con righe vuote).

Per ogni URL:
  1. Estrae tm_player_id
  2. Scrape profilo (nome, foto, anagrafica, ruolo, club, ecc.)
  3. Scrape stats (presenze 24/25 + 25/26, club + nazionale)
  4. Aggiunge a players_all.json + players_main.json
  5. Aggiorna players_stats.json

Alla fine lancia enrich_sortitoutsi + download_photos.

Uso:
  python3 add_players.py urls.txt
  python3 add_players.py            # legge URL da stdin
  python3 add_players.py --apply    # come default, già attivo (no-op flag)
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
import _bootstrap  # noqa: F401  (auto-attiva il venv del progetto)

import json
import re
import subprocess
import time
import datetime as _dt

from scraper.config import (
    DATA_DIR,
    PLAYERS_MAIN_FILE,
    PLAYERS_STATIC_FILE,
    PLAYERS_STATS_FILE,
    CLUBS_FILE,
    SEASONS,
)
from scraper.filter_target import is_target_eligible
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
    main_by_id: dict[int, dict] = {}
    for p in _load(PLAYERS_MAIN_FILE, []):
        main_by_id[p["tm_player_id"]] = p
    stats_by_id: dict[int, dict] = {}
    for s in _load(PLAYERS_STATS_FILE, []):
        stats_by_id[s["tm_player_id"]] = s

    client = TransfermarktClient()
    n_added = n_updated = n_target = n_failed = 0
    failed_ids: list[int] = []  # tm_id dei giocatori falliti (per report + exit code)
    added_names: list[str] = []  # nomi dei giocatori effettivamente aggiunti
    started = time.monotonic()

    for i, pid in enumerate(ids, 1):
        existing = profiles_by_id.get(pid)
        try:
            prof = scrape_player_profile(pid, client)
            # Mantieni i campi roster_* se esistevano
            if existing:
                prof["roster_club_id"] = existing.get("roster_club_id") or prof.get("current_club_id")
                prof["roster_club_name"] = existing.get("roster_club_name") or prof.get("current_club_name")
                # Preserva added_date se il giocatore era gia' stato aggiunto in passato
                if existing.get("added_date"):
                    prof["added_date"] = existing["added_date"]
                n_updated += 1
            else:
                prof["roster_club_id"] = prof.get("current_club_id")
                prof["roster_club_name"] = prof.get("current_club_name")
                # Data di primo inserimento nel DB (usata dal pannello "Aggiunti di recente"
                # nella Home del frontend). I giocatori pre-esistenti a questa feature
                # non hanno il campo: il pannello li ignora semplicemente.
                prof["added_date"] = _dt.date.today().isoformat()
                n_added += 1
                added_names.append(prof.get("full_name") or f"pid={pid}")
            profiles_by_id[pid] = prof

            target_flag = bool(prof.get("is_target_eligible"))
            if target_flag:
                main_by_id[pid] = prof
                n_target += 1
                # scrape stats SOLO per i giocatori target
                try:
                    s = scrape_player_stats(pid, client, seasons=SEASONS)
                    stats_by_id[pid] = s
                except Exception as e:
                    print(f"    [stats fail] pid={pid}: {e}")

            tag = "✓" if target_flag else "skip"
            print(f"  [{i}/{len(ids)}]  {prof.get('full_name','?'):<32}  ({prof.get('current_club_name') or '-'})  [{tag}]")
        except Exception as e:
            n_failed += 1
            failed_ids.append(pid)
            print(f"  [{i}/{len(ids)}]  FAIL pid={pid}: {type(e).__name__}: {e}")

        if i % 10 == 0:
            _save(PLAYERS_ALL_FILE, list(profiles_by_id.values()))
            _save(PLAYERS_MAIN_FILE, list(main_by_id.values()))
            _save(PLAYERS_STATIC_FILE, list(main_by_id.values()))
            _save(PLAYERS_STATS_FILE, list(stats_by_id.values()))

    _save(PLAYERS_ALL_FILE, list(profiles_by_id.values()))
    _save(PLAYERS_MAIN_FILE, list(main_by_id.values()))
    _save(PLAYERS_STATIC_FILE, list(main_by_id.values()))
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

    elapsed = int(time.monotonic() - started)
    print(f"\n{'='*60}")
    print(f"  Aggiunti: {n_added}    Aggiornati: {n_updated}    In DB: {n_target}    Falliti: {n_failed}")
    print(f"  Elapsed: {elapsed//60}m{elapsed%60}s")

    # Pipeline standard: enrich_sortitoutsi + download_photos PRIMA degli override.
    # Motivo: enrich_sortitoutsi.py tende a resettare sortitoutsi_team_id/logo_url
    # a None per i club che non trova (bug noto diario riga 846/1127). Se applichiamo
    # gli override DOPO i subprocess, restano in place.
    print("\n→ enrich_sortitoutsi.py ...")
    subprocess.run([sys.executable, "enrich_sortitoutsi.py"], cwd=ROOT, check=False)
    print("\n→ download_photos.py ...")
    subprocess.run([sys.executable, "download_photos.py"], cwd=ROOT, check=False)

    # === SOTS overrides forniti dall'utente via env SOTS_URLS + SOTS_TEAM_URLS ===
    # Il workflow add_player.yml espone:
    #   SOTS_URLS:      URL person SortItOutSi giocatori (per face + person_id)
    #   SOTS_TEAM_URLS: URL team SortItOutSi club (per logo + team_id)
    # Entrambi sono posizionali rispetto agli URL TM (vuoto = no override).
    # I team_id sono estratti dall'URL fornito dall'utente, NON dalla pagina person
    # (che e' bloccata da Cloudflare challenge da alcuni IP).
    import os as _os
    sots_urls_raw = _os.environ.get("SOTS_URLS", "").strip()
    sots_team_urls_raw = _os.environ.get("SOTS_TEAM_URLS", "").strip()
    if sots_urls_raw or sots_team_urls_raw:
        sots_urls_list = [s.strip() for s in sots_urls_raw.split("\n")] if sots_urls_raw else []
        sots_team_urls_list = [s.strip() for s in sots_team_urls_raw.split("\n")] if sots_team_urls_raw else []
        while len(sots_urls_list) < len(ids):
            sots_urls_list.append("")
        while len(sots_team_urls_list) < len(ids):
            sots_team_urls_list.append("")
        
        print("\n→ Applicazione override SOTS dall'admin (face + logo club)...")
        n_sots_applied = 0
        n_sots_skipped = 0
        n_clubs_logo_applied = 0
        
        import requests as _req
        from scraper.config import USER_AGENTS as _UA
        from scraper.sortitoutsi import face_url as _face_url, profile_url as _profile_url
        
        PHOTOS_DIR = ROOT / "data" / "photos" / "players_sots_lookup"
        PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
        CLUBS_LOGO_DIR = ROOT / "data" / "photos" / "clubs_sots"
        CLUBS_LOGO_DIR.mkdir(parents=True, exist_ok=True)
        session = _req.Session()
        
        # Ricarica i JSON DOPO i subprocess (enrich/download li hanno potenzialmente modificati)
        players_main_data = _load(PLAYERS_MAIN_FILE, [])
        players_all_data = _load(PLAYERS_ALL_FILE, [])
        players_static_data = _load(PLAYERS_STATIC_FILE, [])
        clubs_data = _load(CLUBS_FILE, [])
        
        for pid, sots_url, sots_team_url in zip(ids, sots_urls_list, sots_team_urls_list):
            if not sots_url and not sots_team_url:
                continue
            
            # Skip se player non esiste nei JSON (es. scrape TM fallito con 502)
            # Senza questo controllo scaricheremmo face PNG orfane non collegate a nessun record.
            player_exists = any(
                p_rec.get("tm_player_id") == pid
                for data_list in (players_main_data, players_all_data, players_static_data)
                for p_rec in data_list
            )
            if not player_exists:
                print(f"  ⚠ {pid}: player non in DB (scrape TM probabilmente fallito), skip override SOTS")
                n_sots_skipped += 1
                continue
            
            # === PARTE 1: SOTS person (face + person_id) ===
            sots_id = None
            face_local = None
            if sots_url:
                m = re.search(r"/person/(\d+)/", sots_url)
                if not m:
                    print(f"  ✗ {pid}: URL SOTS person non parsabile: {sots_url[:60]}")
                    n_sots_skipped += 1
                else:
                    sots_id = int(m.group(1))
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
                                print(f"  ⚠ {pid}: face placeholder o errore (status={r.status_code} bytes={len(r.content)})")
                                face_local = None
                        except Exception as e:
                            print(f"  ✗ {pid}: face download error: {e}")
                            face_local = None
                    else:
                        print(f"  ✓ {pid}: face gia in cache sots_id={sots_id}")
                    
                    # Aggiorna i 3 JSON players nel record del giocatore
                    for data_list in (players_main_data, players_all_data, players_static_data):
                        for p_rec in data_list:
                            if p_rec.get("tm_player_id") == pid:
                                p_rec["sortitoutsi_person_id"] = sots_id
                                p_rec["sortitoutsi_face_url"] = _face_url(sots_id)
                                p_rec["sortitoutsi_profile_url"] = _profile_url(sots_id, p_rec.get("full_name"))
                                if face_local:
                                    p_rec["sortitoutsi_face_local_lookup"] = face_local
                                break
                    n_sots_applied += 1
            
            # === PARTE 2: SOTS team (logo + team_id) ===
            if sots_team_url:
                m_team = re.search(r"/team/(\d+)/", sots_team_url)
                if not m_team:
                    print(f"  ✗ {pid}: URL SOTS team non parsabile: {sots_team_url[:60]}")
                else:
                    sots_team_id = int(m_team.group(1))
                    # Trova tm_club_id del giocatore
                    player_tm_club_id = None
                    for data_list in (players_main_data, players_all_data, players_static_data):
                        for p_rec in data_list:
                            if p_rec.get("tm_player_id") == pid:
                                player_tm_club_id = p_rec.get("current_club_id")
                                break
                        if player_tm_club_id:
                            break
                    
                    if player_tm_club_id:
                        club_rec = next((c for c in clubs_data if c.get("tm_club_id") == int(player_tm_club_id)), None)
                        if club_rec:
                            logo_url = f"https://sortitoutsi.b-cdn.net/uploads/team/{sots_team_id}.png"
                            logo_path = CLUBS_LOGO_DIR / f"{int(player_tm_club_id)}.png"
                            logo_local = f"photos/clubs_sots/{int(player_tm_club_id)}.png"
                            
                            # Setta sempre sortitoutsi_team_id (anche se logo placeholder),
                            # cosi' harvest_sots_rosters.py puo' usarlo per fetchare la rosa.
                            # Logo_url e logo_local invece vengono settati SOLO se il download
                            # ha esito positivo (PNG vero, non placeholder GIF). Motivo: il frontend
                            # clubLogo() fa fallback su sortitoutsi_logo_url se logo_local e' None,
                            # quindi settare l'URL placeholder produrrebbe un quadrato bianco invece
                            # della lettera fallback.
                            club_rec["sortitoutsi_team_id"] = sots_team_id
                            
                            if not (logo_path.exists() and logo_path.stat().st_size > 200):
                                try:
                                    logo_r = session.get(logo_url, headers={"User-Agent": _UA[0]}, timeout=15)
                                    # Skip placeholder GIF (SOTS ritorna 43-byte gif quando logo manca)
                                    ct = logo_r.headers.get("content-type", "")
                                    if logo_r.status_code == 200 and "png" in ct.lower() and len(logo_r.content) > 200:
                                        logo_path.write_bytes(logo_r.content)
                                        club_rec["sortitoutsi_logo_local"] = logo_local
                                        club_rec["sortitoutsi_logo_url"] = logo_url
                                        n_clubs_logo_applied += 1
                                        print(f"  ✓ {pid}: club logo scaricato tm_club_id={player_tm_club_id} sots_team={sots_team_id}")
                                    else:
                                        print(f"  ⚠ {pid}: club logo NON disponibile su SOTS CDN (placeholder/gif). team_id={sots_team_id} comunque settato.")
                                except Exception as e:
                                    print(f"  ✗ {pid}: club logo download error: {e}")
                            else:
                                club_rec["sortitoutsi_logo_local"] = logo_local
                                print(f"  ✓ {pid}: club logo gia in cache tm_club_id={player_tm_club_id}")
                        else:
                            print(f"  ⚠ {pid}: club tm_club_id={player_tm_club_id} non trovato in clubs.json")
                    else:
                        print(f"  ⚠ {pid}: player non trovato nei JSON, skip club logo")
            
            time.sleep(0.3)  # gentile con SOTS CDN
        
        # Salva i JSON aggiornati
        if n_sots_applied > 0 or n_clubs_logo_applied > 0:
            _save(PLAYERS_MAIN_FILE, players_main_data)
            _save(PLAYERS_ALL_FILE, players_all_data)
            _save(PLAYERS_STATIC_FILE, players_static_data)
            _save(CLUBS_FILE, clubs_data)
            print(f"  Applicati {n_sots_applied} face override, {n_clubs_logo_applied} club logo, skippati {n_sots_skipped}")
    print("\nFatto. Hard reload del browser (⌘⇧R) per vedere i nuovi giocatori.")

    # === Report finale + exit code ===
    # Se ci sono stati fallimenti (es. 403/502 da TM), usciamo con codice 1 cosi'
    # il workflow GitHub risulta ROSSO (non verde fuorviante) e parte l'email
    # automatica di notifica. Scriviamo anche un riepilogo su GITHUB_STEP_SUMMARY
    # cosi' nella pagina del run si vede subito chi e' stato inserito e chi no.
    print(f"\n{'='*60}")
    print("  REPORT FINALE")
    if added_names:
        print(f"  ✓ INSERITI ({len(added_names)}): {', '.join(added_names)}")
    if n_updated:
        print(f"  ↻ AGGIORNATI: {n_updated}")
    if failed_ids:
        print(f"  ✗ FALLITI ({len(failed_ids)}): tm_id {', '.join(str(x) for x in failed_ids)}")
        print(f"    → Probabile 403/502 da Transfermarkt (blocco IP runner). Ri-submetti gli stessi URL: GitHub assegnera' un IP diverso.")

    # GITHUB_STEP_SUMMARY: tabella markdown visibile nella pagina del run
    _summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if _summary_path:
        try:
            with open(_summary_path, "a", encoding="utf-8") as _sf:
                _sf.write("## Aggiunta giocatori — Report\n\n")
                _sf.write(f"- **Inseriti**: {n_added}\n")
                _sf.write(f"- **Aggiornati**: {n_updated}\n")
                _sf.write(f"- **Falliti**: {n_failed}\n\n")
                if added_names:
                    _sf.write("### ✓ Inseriti\n")
                    for _nm in added_names:
                        _sf.write(f"- {_nm}\n")
                    _sf.write("\n")
                if failed_ids:
                    _sf.write("### ✗ Falliti (da ri-submettere)\n")
                    for _fid in failed_ids:
                        _sf.write(f"- tm_id `{_fid}` — https://www.transfermarkt.com/-/profil/spieler/{_fid}\n")
                    _sf.write("\n_Causa probabile: 403/502 da Transfermarkt (blocco IP runner temporaneo). "
                              "Ri-submetti gli stessi URL dall'Admin: GitHub assegnera' un IP runner diverso._\n")
        except Exception as _e:
            print(f"  [warn] impossibile scrivere GITHUB_STEP_SUMMARY: {_e}")

    # Exit code: 1 se ci sono fallimenti (workflow rosso + email), 0 altrimenti
    if failed_ids:
        print(f"\n  Exit 1: {len(failed_ids)} giocatori non aggiunti. Vedi sopra.")
        sys.exit(1)


if __name__ == "__main__":
    main()

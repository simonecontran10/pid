"""
add_club.py — Aggiunge un club arbitrario al PID dato un URL Transfermarkt.

Pattern: come `add_seconde_squadre.py` ma generico per UN club arbitrario.

Uso CLI:
    python3 add_club.py "<tm_url>" [--league <code>]
    python3 add_club.py "https://www.transfermarkt.com/real-madrid/kader/verein/418/saison_id/2025" --league ES1

Uso da workflow GitHub Actions (env vars):
    URL="https://..." LEAGUE="ES1" python3 add_club.py

L'URL deve contenere /verein/<id>/. Estrae tm_club_id, slug, nome club, e
scarica:
  - profilo club (nome, logo)
  - rosa giocatori
  - per ogni giocatore: profilo + stats (se eligible)

Output: aggiorna data/clubs.json, players_all.json, players_main.json,
players_stats.json. Idempotente: se il club gia' esiste, aggiorna i dati.

Exit code:
    0 = successo
    1 = errori
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
import _bootstrap  # noqa: F401

from bs4 import BeautifulSoup

from scraper.config import (
    CLUBS_FILE,
    DATA_DIR,
    PLAYERS_MAIN_FILE,
    PLAYERS_STATS_FILE,
    SEASONS,
)
from scraper.http_client import TransfermarktClient
from scraper.profiles import scrape_player_profile
from scraper.rosters import scrape_club_roster
from scraper.stats import scrape_player_stats

PLAYERS_ALL_FILE = DATA_DIR / "players_all.json"


def _load(p: Path, default):
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def _save(p: Path, data) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_tm_url(url: str) -> tuple[int, str]:
    """Estrae (tm_club_id, slug) dall'URL Transfermarkt.

    Formati accettati:
      https://www.transfermarkt.com/real-madrid/startseite/verein/418/saison_id/2025
      https://www.transfermarkt.com/real-madrid/kader/verein/418
      https://www.transfermarkt.com/real-madrid/verein/418
      .../verein/418/
    """
    m = re.search(r"transfermarkt\.[a-z.]+/([^/]+)/(?:startseite|kader|spielplan|leistungsdaten)?/?verein/(\d+)", url)
    if not m:
        # Fallback piu' permissivo
        m = re.search(r"/([^/]+)/.*verein/(\d+)", url)
    if not m:
        raise ValueError(f"URL TM non valido (manca /verein/<id>/): {url}")
    slug = m.group(1)
    cid = int(m.group(2))
    return cid, slug


def fetch_club_name(client: TransfermarktClient, slug: str, cid: int) -> tuple[str, str | None]:
    """Scarica la pagina startseite e estrae il nome del club + league_id se possibile."""
    page_url = f"https://www.transfermarkt.com/{slug}/startseite/verein/{cid}/saison_id/2025"
    print(f"[fetch club] {page_url}")
    html = client.get_html(page_url)
    soup = BeautifulSoup(html, "lxml")

    # Nome club dall'header
    name = None
    h1 = soup.select_one("h1.data-header__headline-wrapper")
    if h1:
        # rimuove children <span> (stelle, ecc.)
        for sp in h1.select("span"):
            sp.decompose()
        name = h1.get_text(strip=True)
    if not name:
        # fallback: <title>
        t = soup.select_one("title")
        if t:
            name = re.sub(r"\s*\|\s*Transfermarkt.*$", "", t.get_text(strip=True))
    if not name:
        name = slug.replace("-", " ").title()

    # Lega (best-effort): cerca link a wettbewerb
    league_id = None
    league_link = soup.select_one("a[href*='/startseite/wettbewerb/']")
    if league_link:
        m = re.search(r"/wettbewerb/([A-Z0-9]+)", league_link.get("href", ""))
        if m:
            league_id = m.group(1)

    return name, league_id


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url", nargs="?", default=os.environ.get("URL", ""),
                    help="URL Transfermarkt del club (anche da env URL)")
    ap.add_argument("--league", default=os.environ.get("LEAGUE", ""),
                    help="Override league_id (default: estratto dalla pagina TM)")
    ap.add_argument("--skip-stats", action="store_true",
                    help="Scarica solo profili, non stats (piu' veloce)")
    args = ap.parse_args()

    if not args.url:
        print("ERRORE: serve URL Transfermarkt (argomento o env URL).")
        print("Uso: python3 add_club.py <url> [--league CODE]")
        return 1

    try:
        cid, slug = parse_tm_url(args.url)
    except ValueError as e:
        print(f"ERRORE: {e}")
        return 1

    print("=" * 70)
    print(f"ADD CLUB — tm_club_id={cid} slug={slug}")
    print("=" * 70)

    client = TransfermarktClient()

    # === Step 1: nome club + lega ===
    try:
        club_name, detected_league = fetch_club_name(client, slug, cid)
    except Exception as e:
        print(f"[error] impossibile leggere pagina club: {type(e).__name__}: {e}")
        return 1

    # Preserve esistente: se il club c'è già in clubs.json, e l'utente non
    # ha passato --league esplicitamente, NON sovrascriviamo league_id /
    # name perché potrebbero essere stati settati manualmente (es. Gubbio
    # già classificato in "IT3B" Serie C Girone B). Altrimenti il club
    # "spariva" dalla griglia originale dopo un re-import.
    clubs_existing = _load(CLUBS_FILE, [])
    existing_club = next((c for c in clubs_existing if c.get("tm_club_id") == cid), None)

    if args.league:
        league_id = args.league
        league_src = "override"
    elif existing_club and existing_club.get("league_id"):
        league_id = existing_club["league_id"]
        league_src = "preserved"
    else:
        league_id = detected_league or "OTHER"
        league_src = "auto"

    # Nome: preservalo se esiste (potrebbe essere stato pulito a mano).
    if existing_club and existing_club.get("name"):
        club_name = existing_club["name"]

    print(f"  nome: {club_name}")
    print(f"  lega: {league_id}  ({league_src})")

    club_record = {
        "tm_club_id": cid,
        "name": club_name,
        "slug": slug,
        "league_id": league_id,
        "league_name": (existing_club or {}).get("league_name") or league_id,
        "club_url": f"https://www.transfermarkt.com/{slug}/startseite/verein/{cid}/saison_id/2025",
        "sortitoutsi_logo_local": f"photos/clubs_sots/{cid}.png",
    }

    # === Step 2: scrape rosa ===
    print()
    print("STEP 2 — scrape rosa")
    print("-" * 70)
    try:
        roster = scrape_club_roster(club_record, client=client)
    except Exception as e:
        print(f"[error] scrape_club_roster: {type(e).__name__}: {e}")
        return 1
    pids = [p["tm_player_id"] for p in roster]
    print(f"  rosa: {len(pids)} giocatori")
    # Guardia: se la rosa è vuota, TM ha probabilmente bloccato la pagina
    # /kader/ (capita su IP server: Vercel, GitHub Actions). Non salviamo
    # il club_record nuovo perché finirebbe in clubs.json senza giocatori,
    # apparendo come "operazione conclusa" nell'UI Admin ma in realtà
    # vuoto. Meglio fallire esplicitamente e suggerire run locale.
    if not pids and existing_club is None:
        print()
        print("[error] rosa VUOTA — probabilmente TM ha bloccato la richiesta")
        print("        /kader/ (IP server bloccato). Esegui add_club.py")
        print("        localmente dal Mac per aggirare il blocco.")
        return 1

    # === Step 3: update clubs.json (upsert) ===
    clubs = _load(CLUBS_FILE, [])
    idx = next((i for i, c in enumerate(clubs) if c.get("tm_club_id") == cid), None)
    if idx is None:
        clubs.append(club_record)
        print(f"  + nuovo club aggiunto a clubs.json")
    else:
        # preserva sortitoutsi_team_id / sortitoutsi_logo_url se gia presenti
        old = clubs[idx]
        merged = {**old, **club_record}
        # Non sovrascrivere il logo SOTS se gia c'e
        if old.get("sortitoutsi_logo_url"):
            merged["sortitoutsi_logo_url"] = old["sortitoutsi_logo_url"]
        if old.get("sortitoutsi_team_id"):
            merged["sortitoutsi_team_id"] = old["sortitoutsi_team_id"]
        clubs[idx] = merged
        print(f"  ~ club aggiornato in clubs.json")
    _save(CLUBS_FILE, clubs)

    # === Step 4: scrape profili + stats ===
    print()
    print("STEP 4 — profili giocatori + stats")
    print("-" * 70)
    profiles_by_id = {p["tm_player_id"]: p for p in _load(PLAYERS_ALL_FILE, [])}
    main_by_id = {p["tm_player_id"]: p for p in _load(PLAYERS_MAIN_FILE, [])}
    stats_by_id = {s["tm_player_id"]: s for s in _load(PLAYERS_STATS_FILE, [])}

    n_added = n_updated = n_eligible = n_failed = 0
    t0 = time.monotonic()
    for i, pid in enumerate(pids, 1):
        existing = profiles_by_id.get(pid)
        try:
            prof = scrape_player_profile(pid, client)
            prof["roster_club_id"] = cid
            prof["roster_club_name"] = club_name
            if existing:
                n_updated += 1
            else:
                n_added += 1
            profiles_by_id[pid] = prof

            if bool(prof.get("is_target_eligible")):
                main_by_id[pid] = prof
                n_eligible += 1
                if not args.skip_stats:
                    try:
                        s = scrape_player_stats(pid, client, seasons=SEASONS)
                        stats_by_id[pid] = s
                    except Exception as e:
                        print(f"    [stats fail] pid={pid}: {e}")
            print(f"  [{i:>3}/{len(pids)}] {prof.get('full_name', '?')[:30]:<30}")
        except Exception as e:
            n_failed += 1
            print(f"  [{i:>3}/{len(pids)}] [FAIL] pid={pid}: {type(e).__name__}: {e}")

    elapsed = int(time.monotonic() - t0)
    print()
    print(f"Profili: +{n_added} nuovi, ~{n_updated} aggiornati, {n_eligible} target, {n_failed} falliti — {elapsed}s")

    # === Step 5: persist ===
    _save(PLAYERS_ALL_FILE, list(profiles_by_id.values()))
    _save(PLAYERS_MAIN_FILE, list(main_by_id.values()))
    _save(PLAYERS_STATS_FILE, list(stats_by_id.values()))

    print()
    print("=" * 70)
    print(f"✓ DONE — club '{club_name}' aggiunto/aggiornato con {len(pids)} giocatori")
    print("=" * 70)
    return 0 if n_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

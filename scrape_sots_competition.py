"""
scrape_sots_competition.py — Backfill sortitoutsi_team_id automatico.

Data una pagina "competition" o "nation" di sortitoutsi.net (es.
  https://sortitoutsi.net/football-manager-2026/competition/11/premier-league
  https://sortitoutsi.net/football-manager-2026/nation/765/england
), parsa tutti i link verso /team/<id>/<slug> + nome team mostrato.

Poi matcha con i club in data/clubs.json (case-insensitive, normalizzato)
e popola sortitoutsi_team_id + sortitoutsi_logo_url per i club che non
ce l'avevano. Idempotente.

Uso:
    python3 scrape_sots_competition.py <URL>
    python3 scrape_sots_competition.py <URL1> <URL2> ...
    python3 scrape_sots_competition.py --dry-run <URL>

Dopo aver popolato gli ID, lanciare:
    python3 extract_sots_assets.py --logos-only
per estrarre i loghi dal megapack (richiede volume BACK UP collegato).
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import time
import unicodedata
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent
CLUBS_FILE = ROOT / "data" / "clubs.json"

# UA Chrome reale: sortitoutsi blocca UA banali con 403 / pagina vuota.
# NOTA: niente "br" in Accept-Encoding — requests gestisce solo gzip/deflate
# nativamente, con br risponde una pagina troncata.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,it;q=0.8",
}


def normalize(s: str) -> str:
    """Lowercase + strip diacritics + remove punctuation. Per match fuzzy."""
    if not s: return ""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower()
    # Rimuovi prefissi/suffissi club comuni
    s = re.sub(r"\b(fc|cf|sc|afc|cfc|sfc|ac|acf|ssc|us|uc|aj|olympique|de)\b", "", s)
    # Rimuovi punteggiatura/spazi
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s


def scrape_page(url: str) -> list[tuple[int, str, str]]:
    """Ritorna lista (sots_id, slug, display_name)."""
    print(f"[fetch] {url}")
    r = requests.get(url, headers=HEADERS, timeout=20)
    if r.status_code != 200:
        print(f"  ERR status {r.status_code}, len {len(r.text)}")
        if r.status_code == 403:
            print("  → 403 Forbidden. Sortitoutsi blocca? Prova a cambiare IP/UA.")
        return []
    soup = BeautifulSoup(r.text, "lxml")
    seen = set()
    teams = []
    # Sortitoutsi usa <a href="/football-manager-2026/team/<id>/<slug>"> dentro
    # tabelle "Teams" della competition page. Il testo dell'<a> è il nome.
    for a in soup.select('a[href*="/team/"]'):
        m = re.search(r"/team/(\d+)/([^/?#]+)", a.get("href", ""))
        if not m:
            continue
        sid = int(m.group(1))
        if sid in seen:
            continue
        seen.add(sid)
        txt = a.get_text(" ", strip=True)
        if not txt or len(txt) < 2:
            # Salta link senza testo (es. icone)
            continue
        teams.append((sid, m.group(2), txt))
    return teams


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urls", nargs="+", help="URL pagina competition o nation di sortitoutsi.net")
    ap.add_argument("--dry-run", action="store_true",
                    help="Non scrivere data/clubs.json — stampa solo cosa farebbe")
    args = ap.parse_args()

    clubs = json.loads(CLUBS_FILE.read_text(encoding="utf-8"))

    # Build lookup: nome_normalizzato → club record (mutabile)
    by_norm = {}
    for c in clubs:
        n = normalize(c.get("name", ""))
        if n:
            by_norm.setdefault(n, []).append(c)

    # Aggrega tutti i team trovati sulle URL
    all_teams: dict[int, tuple[str, str]] = {}  # sots_id → (slug, display)
    for url in args.urls:
        for sid, slug, txt in scrape_page(url):
            if sid not in all_teams:
                all_teams[sid] = (slug, txt)
        time.sleep(1.5)  # rate limit cortese

    print(f"\n[parse] Team unici trovati: {len(all_teams)}")

    matched = []
    unmatched_sots = []
    skipped_already = 0

    for sid, (slug, txt) in all_teams.items():
        n_txt = normalize(txt)
        n_slug = normalize(slug.replace("-", " "))
        # Prova match per display txt, poi per slug
        candidates = by_norm.get(n_txt) or by_norm.get(n_slug) or []
        if not candidates:
            unmatched_sots.append((sid, slug, txt))
            continue
        # Prendi il primo candidato che NON ha già sortitoutsi_team_id
        target = None
        for c in candidates:
            if not c.get("sortitoutsi_team_id"):
                target = c
                break
        if target is None:
            skipped_already += 1
            continue
        # Update
        if not args.dry_run:
            target["sortitoutsi_team_id"] = sid
            target["sortitoutsi_logo_url"] = f"https://sortitoutsi.b-cdn.net/uploads/team/{sid}.png"
        matched.append((target.get("name"), target.get("tm_club_id"), sid, slug))

    print(f"\n[result] Match nuovi:           {len(matched)}")
    print(f"[result] Skippati (gia' ok):    {skipped_already}")
    print(f"[result] Sots senza match locale: {len(unmatched_sots)}")
    print()
    if matched:
        print("Backfillati:")
        for n, tm, sid, slug in matched:
            print(f"  + {n[:35]:35} tm={tm:6} → sots={sid} ({slug})")
    if unmatched_sots:
        print(f"\nSots senza match (primi 10):")
        for sid, slug, txt in unmatched_sots[:10]:
            print(f"  ? sots={sid:10} txt={txt[:40]}")

    if args.dry_run:
        print("\n[dry-run] Niente scritto. Per applicare: rilancia senza --dry-run.")
    elif matched:
        CLUBS_FILE.write_text(json.dumps(clubs, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n[save] data/clubs.json aggiornato.")
        print("Prossimo step: python3 extract_sots_assets.py --logos-only")


if __name__ == "__main__":
    main()

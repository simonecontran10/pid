"""fix_winter_signing_clubs.py — Fix retroattivo dei nomi 'Winter signing'/'Returnee'/'New arrival'.

PROBLEMA:
80 giocatori in players_main.json hanno current_club_name='Winter signing' (o
'Returnee'/'New arrival'). I loro current_club_id puntano a club veri, ma
TM mostra come testo del link il "ribbon" (cluster transizione) invece del
nome vero. Dei 120 totali, 40 sono già stati fixati usando clubs.json (40 club
in Serie A/B/C/IJ1). I restanti 80 sono in club di leghe non scrappate
(Polonia, Danimarca, Croazia, Portogallo, ecc.).

SOLUZIONE:
Per ognuno dei 71 unique club_id mancanti, fetcho la pagina TM
'/startseite/verein/{id}' ed estraggo solo il nome del club. Poi aggiorno
players_main.json + players_static.json + players_all.json per gli 80 vittime.

USO:
  python3 fix_winter_signing_clubs.py             # dry-run (mostra cosa farebbe)
  python3 fix_winter_signing_clubs.py --apply     # apply (fa fetch + scrive)
"""
import json
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent.resolve()
DATA = ROOT / "data"
DRY_RUN = "--apply" not in sys.argv

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
SUSPICIOUS = {"Winter signing", "New arrival", "Returnee"}


def fetch_club_name(club_id: int, session: requests.Session) -> str | None:
    """Fetch della pagina TM del club ed estrae il nome ufficiale."""
    url = f"https://www.transfermarkt.com/-/startseite/verein/{club_id}"
    try:
        r = session.get(url, headers={"User-Agent": USER_AGENT}, timeout=15, allow_redirects=True)
        if r.status_code != 200:
            print(f"    HTTP {r.status_code}")
            return None
        soup = BeautifulSoup(r.text, "lxml")
        # Strategia 1: <h1 class="data-header__headline-wrapper">
        h1 = soup.select_one(".data-header__headline-wrapper")
        if h1:
            # Rimuovi span shirt-number etc.
            for s in h1.select("span"):
                s.decompose()
            name = h1.get_text(" ", strip=True)
            # Rimuovi caratteri sporchi (parentesi, simboli di favorite, etc.)
            name = re.sub(r"\s+", " ", name).strip()
            if name:
                return name
        # Strategia 2: <title> della pagina
        title = soup.select_one("title")
        if title:
            t = title.get_text(strip=True)
            # Pattern tipico: "Nome Club - Klub Profil | Transfermarkt"
            m = re.match(r"^(.+?)\s*[-–]\s*", t)
            if m:
                return m.group(1).strip()
        return None
    except Exception as e:
        print(f"    Exception: {e}")
        return None


def main():
    players_path = DATA / "players_main.json"
    static_path = DATA / "players_static.json"
    all_path = DATA / "players_all.json"

    players = json.loads(players_path.read_text(encoding="utf-8"))

    # 1) Estrai vittime
    unfixable = [p for p in players if p.get("current_club_name") in SUSPICIOUS]
    unique_ids = sorted(set(p.get("current_club_id") for p in unfixable if p.get("current_club_id")))

    print(f"Vittime totali: {len(unfixable)}")
    print(f"Unique club_id da scrappare: {len(unique_ids)}")
    print()

    if DRY_RUN:
        print("🔍 DRY-RUN: ecco i club che scrapperei (primi 10):")
        for cid in unique_ids[:10]:
            n_players = sum(1 for p in unfixable if p.get("current_club_id") == cid)
            sample = next(p for p in unfixable if p.get("current_club_id") == cid)
            print(f"  id={cid:>6}  ({n_players} giocatori)  sample: {sample.get('full_name')[:30]}")
        print()
        print("Per applicare davvero: python3 fix_winter_signing_clubs.py --apply")
        return

    # 2) Fetch
    print(f"Inizio scraping {len(unique_ids)} club...")
    print()

    session = requests.Session()
    club_names: dict[int, str] = {}
    failed: list[int] = []

    for i, cid in enumerate(unique_ids, 1):
        name = fetch_club_name(cid, session)
        if name:
            club_names[cid] = name
            n_players = sum(1 for p in unfixable if p.get("current_club_id") == cid)
            print(f"  [{i:>3}/{len(unique_ids)}] id={cid:>6} → '{name}' ({n_players} giocatori)")
        else:
            failed.append(cid)
            print(f"  [{i:>3}/{len(unique_ids)}] id={cid:>6} → ❌ FALLITO")
        time.sleep(0.5)  # rate limit

    print()
    print(f"✅ Successi: {len(club_names)}/{len(unique_ids)}")
    print(f"❌ Fallimenti: {len(failed)}")
    if failed:
        print(f"   id non risolti: {failed}")

    # 3) Aggiorna i 3 file JSON
    print()
    print("Aggiornamento JSON...")

    def update_file(path: Path):
        if not path.exists():
            print(f"  {path.name}: non esiste, skip")
            return 0
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            print(f"  {path.name}: non è una lista, skip")
            return 0
        n_fixed = 0
        for p in data:
            if p.get("current_club_name") in SUSPICIOUS:
                cid = p.get("current_club_id")
                if cid in club_names:
                    p["current_club_name"] = club_names[cid]
                    if p.get("roster_club_name") in SUSPICIOUS and p.get("roster_club_id") == cid:
                        p["roster_club_name"] = club_names[cid]
                    n_fixed += 1
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return n_fixed

    n1 = update_file(players_path)
    n2 = update_file(static_path)
    n3 = update_file(all_path)

    print(f"  players_main.json:   {n1} fix")
    print(f"  players_static.json: {n2} fix")
    print(f"  players_all.json:    {n3} fix")

    # 4) Verifica finale
    players_after = json.loads(players_path.read_text(encoding="utf-8"))
    remaining = sum(1 for p in players_after if p.get("current_club_name") in SUSPICIOUS)
    print()
    print(f"Vittime rimaste in players_main.json dopo fix: {remaining}")
    print(f"  (target: {len(failed)} = quelli falliti nel fetch)")

    print()
    print("Prossimi step:")
    print("  git add data/players_main.json data/players_static.json data/players_all.json")
    print("  git commit -m 'fix(players): risolvo gli 80 Winter signing residui (re-scrape pagina TM dei 71 club mancanti)'")
    print("  git push")


if __name__ == "__main__":
    main()

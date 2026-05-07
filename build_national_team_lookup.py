"""
build_national_team_lookup.py — Costruisce data/national_team_lookup.json
mappando ogni team_id che compare nei national_career a {country, category}.

Per ogni team_id distinto:
- Fetch https://www.transfermarkt.com/-/startseite/verein/{team_id}
- Estrai dal <h1> il nome (es. "Morocco" / "Italy U21" / "Germany U17" / "Spain Olympic")
- Parsing: split l'ultimo token, se è categoria nota (U17, U18, U19, U20, U21, U22, U23, Olympic) → quello è category, il resto è country
- Salva mapping per ricerca cross-conversioni nei prossimi run frontend

Uso (1 sola volta, lo lanci dal Mac dove TM non blocca):
    source venv/bin/activate
    python3 build_national_team_lookup.py

Tempo stimato: 392 fetch x 0.4s = ~3 min
"""
import json
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

DATA_DIR = ROOT / "data"
STATS_LOCAL = Path("/tmp/stats.json")
STATS_R2 = "https://pub-aa9d173290684b36a9f35e79d4d388c2.r2.dev/players_stats.json"
LOOKUP_FILE = DATA_DIR / "national_team_lookup.json"

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
HEADERS = {"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"}

# Categorie note di nazionali (case-sensitive). L'ordine conta: prima quelle più specifiche.
CATEGORIES = ["Olympic", "U23", "U22", "U21", "U20", "U19", "U18", "U17", "U16", "U15", "U14"]

# Override per casi speciali (varianti di nome TM)
COUNTRY_OVERRIDES = {
    # TM a volte usa "Czech Republic" ma il file bandiera si chiama "Czech-Republic"
    # Per ora mantengo il nome TM e il frontend lo normalizza
}


def parse_team_name(html: str) -> str | None:
    """Estrae il nome team dalla pagina TM."""
    soup = BeautifulSoup(html, "lxml")
    # H1 principale
    h1 = soup.find("h1", class_="data-header__headline-wrapper")
    if h1:
        # Rimuovi span interni con sub-info, prendi solo il testo principale
        for span in h1.find_all("span"):
            span.decompose()
        name = h1.get_text(strip=True)
        if name:
            return name
    # Fallback: title della pagina
    title = soup.find("title")
    if title:
        t = title.get_text(strip=True)
        # "Italy U21 - Detailed squad 24/25 | Transfermarkt"
        m = re.match(r"^(.+?)\s*-", t)
        if m:
            return m.group(1).strip()
    return None


def split_country_category(name: str) -> tuple[str, str]:
    """Split 'Italy U21' → ('Italy', 'U21'), 'Spain Olympic' → ('Spain', 'Olympic'), 'Italy' → ('Italy', 'A')."""
    if not name:
        return ("", "A")
    for cat in CATEGORIES:
        # Match "X U21", "X U21 (women)" ecc — il cat è in fondo o prima di parentesi
        m = re.match(rf"^(.+?)\s+{re.escape(cat)}(\b.*)?$", name, re.IGNORECASE)
        if m:
            country = m.group(1).strip()
            return (country, cat)
    return (name, "A")


def fetch_team_id(team_id: str) -> dict | None:
    url = f"https://www.transfermarkt.com/-/startseite/verein/{team_id}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return None
        name = parse_team_name(r.text)
        if not name:
            return None
        country, category = split_country_category(name)
        return {"name": name, "country": country, "category": category}
    except Exception as e:
        print(f"    [err] {e}")
        return None


def main() -> int:
    # Carica stats per estrarre team_id
    if not STATS_LOCAL.exists():
        print(f"Scarico players_stats da R2…")
        r = requests.get(STATS_R2, timeout=120)
        STATS_LOCAL.write_bytes(r.content)
        print(f"  ✓ {len(r.content):,} bytes")
    stats = json.loads(STATS_LOCAL.read_text(encoding="utf-8"))

    team_ids = set()
    for s in stats:
        for n in s.get("national_career", []):
            tid = n.get("team_id")
            if tid:
                team_ids.add(str(tid))
    print(f"Team_id distinti: {len(team_ids)}")

    # Carica lookup esistente (per riprese parziali)
    lookup = {}
    if LOOKUP_FILE.exists():
        lookup = json.loads(LOOKUP_FILE.read_text(encoding="utf-8"))
        print(f"Lookup esistente: {len(lookup)} entries")

    # Da fare
    todo = sorted(team_ids - set(lookup.keys()))
    print(f"Da scrappare: {len(todo)}")
    print()

    for i, tid in enumerate(todo, 1):
        info = fetch_team_id(tid)
        if info:
            lookup[tid] = info
            print(f"  [{i:>3}/{len(todo)}] tid={tid:<8} → {info['country']:<25} ({info['category']})")
        else:
            print(f"  [{i:>3}/{len(todo)}] tid={tid:<8} ❌")

        # Salva ogni 20 (per non perdere progresso in caso di stop)
        if i % 20 == 0:
            LOOKUP_FILE.write_text(json.dumps(lookup, indent=2, ensure_ascii=False), encoding="utf-8")

        time.sleep(0.3)

    # Salva finale
    LOOKUP_FILE.write_text(json.dumps(lookup, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    print("=" * 70)
    print(f"  ✓ Lookup salvato in {LOOKUP_FILE}: {len(lookup)} entries totali")
    print()

    # Stats: countries unici
    from collections import Counter
    countries = Counter(v["country"] for v in lookup.values())
    print(f"  Countries unici: {len(countries)}")
    print(f"  Top 15 countries:")
    for c, n in countries.most_common(15):
        print(f"    {c:<30} {n} team(s)")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())

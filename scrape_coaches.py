"""
scrape_coaches.py — Estrae il nome e la nazionalità dell'allenatore
per ciascuna delle 48 nazionali WC2026 da Wikipedia.
"""
from __future__ import annotations
import json
import re
import time
from pathlib import Path
import requests
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
HEADERS = {"User-Agent": UA}

# Mapping (FIFA name → Wikipedia URL)
WIKI_URLS = {
    "Algeria": "https://en.wikipedia.org/wiki/Algeria_national_football_team",
    "Argentina": "https://en.wikipedia.org/wiki/Argentina_national_football_team",
    "Australia": "https://en.wikipedia.org/wiki/Australia_men%27s_national_soccer_team",
    "Austria": "https://en.wikipedia.org/wiki/Austria_national_football_team",
    "Belgium": "https://en.wikipedia.org/wiki/Belgium_national_football_team",
    "Bosnia And Herzegovina": "https://en.wikipedia.org/wiki/Bosnia_and_Herzegovina_national_football_team",
    "Brazil": "https://en.wikipedia.org/wiki/Brazil_national_football_team",
    "Canada": "https://en.wikipedia.org/wiki/Canada_men%27s_national_soccer_team",
    "Cape Verde": "https://en.wikipedia.org/wiki/Cape_Verde_national_football_team",
    "Colombia": "https://en.wikipedia.org/wiki/Colombia_national_football_team",
    "Congo DR": "https://en.wikipedia.org/wiki/DR_Congo_national_football_team",
    "Côte D'Ivoire": "https://en.wikipedia.org/wiki/Ivory_Coast_national_football_team",
    "Croatia": "https://en.wikipedia.org/wiki/Croatia_national_football_team",
    "Curaçao": "https://en.wikipedia.org/wiki/Cura%C3%A7ao_national_football_team",
    "Czechia": "https://en.wikipedia.org/wiki/Czech_Republic_national_football_team",
    "Ecuador": "https://en.wikipedia.org/wiki/Ecuador_national_football_team",
    "Egypt": "https://en.wikipedia.org/wiki/Egypt_national_football_team",
    "England": "https://en.wikipedia.org/wiki/England_national_football_team",
    "France": "https://en.wikipedia.org/wiki/France_national_football_team",
    "Germany": "https://en.wikipedia.org/wiki/Germany_national_football_team",
    "Ghana": "https://en.wikipedia.org/wiki/Ghana_national_football_team",
    "Haiti": "https://en.wikipedia.org/wiki/Haiti_national_football_team",
    "IR Iran": "https://en.wikipedia.org/wiki/Iran_national_football_team",
    "Iraq": "https://en.wikipedia.org/wiki/Iraq_national_football_team",
    "Japan": "https://en.wikipedia.org/wiki/Japan_national_football_team",
    "Jordan": "https://en.wikipedia.org/wiki/Jordan_national_football_team",
    "Korea Republic": "https://en.wikipedia.org/wiki/South_Korea_national_football_team",
    "Mexico": "https://en.wikipedia.org/wiki/Mexico_national_football_team",
    "Morocco": "https://en.wikipedia.org/wiki/Morocco_national_football_team",
    "Netherlands": "https://en.wikipedia.org/wiki/Netherlands_national_football_team",
    "New Zealand": "https://en.wikipedia.org/wiki/New_Zealand_men%27s_national_football_team",
    "Norway": "https://en.wikipedia.org/wiki/Norway_national_football_team",
    "Panama": "https://en.wikipedia.org/wiki/Panama_national_football_team",
    "Paraguay": "https://en.wikipedia.org/wiki/Paraguay_national_football_team",
    "Portugal": "https://en.wikipedia.org/wiki/Portugal_national_football_team",
    "Qatar": "https://en.wikipedia.org/wiki/Qatar_national_football_team",
    "Saudi Arabia": "https://en.wikipedia.org/wiki/Saudi_Arabia_national_football_team",
    "Scotland": "https://en.wikipedia.org/wiki/Scotland_national_football_team",
    "Senegal": "https://en.wikipedia.org/wiki/Senegal_national_football_team",
    "South Africa": "https://en.wikipedia.org/wiki/South_Africa_national_football_team",
    "Spain": "https://en.wikipedia.org/wiki/Spain_national_football_team",
    "Sweden": "https://en.wikipedia.org/wiki/Sweden_national_football_team",
    "Switzerland": "https://en.wikipedia.org/wiki/Switzerland_national_football_team",
    "Tunisia": "https://en.wikipedia.org/wiki/Tunisia_national_football_team",
    "Turkey": "https://en.wikipedia.org/wiki/Turkey_national_football_team",
    "United States": "https://en.wikipedia.org/wiki/United_States_men%27s_national_soccer_team",
    "Uruguay": "https://en.wikipedia.org/wiki/Uruguay_national_football_team",
    "Uzbekistan": "https://en.wikipedia.org/wiki/Uzbekistan_national_football_team",
}


def extract_coach(html: str) -> dict:
    """Cerca nell'infobox della pagina nazionale: 'Head coach' / 'Manager' →
    nome + nazionalità (flag prima del nome)."""
    soup = BeautifulSoup(html, "html.parser")
    infobox = soup.find("table", class_=re.compile(r"infobox"))
    if not infobox:
        return {"name": None, "country": None, "raw": None}
    for tr in infobox.find_all("tr"):
        th = tr.find("th")
        if not th:
            continue
        label = th.get_text(" ", strip=True).lower()
        if any(k in label for k in ("head coach", "manager", "coach")):
            td = tr.find("td")
            if not td:
                continue
            # Country: cerca <span class="flagicon"> seguito da <a>
            country = None
            flag = td.find("span", class_=re.compile(r"flag"))
            if flag:
                # Il country è solitamente nell'alt o nel testo del primo <a>
                img = flag.find("img")
                if img and img.get("alt"):
                    country = img["alt"]
                if not country:
                    a = flag.find_next("a")
                    if a:
                        country = a.get_text(strip=True)
            # Name: testo dopo la bandiera (di solito un <a>)
            raw = td.get_text(" ", strip=True)
            # Pulisci: rimuovi country se appare due volte all'inizio
            name = raw
            if country and raw.lower().startswith(country.lower()):
                name = raw[len(country):].strip()
            # Rimuovi suffix tipo "(since X)" o note
            name = re.sub(r"\s*\[.*?\]\s*", "", name).strip()
            name = re.sub(r"\s*\(.*?\)\s*$", "", name).strip()
            return {"name": name, "country": country, "raw": raw}
    return {"name": None, "country": None, "raw": None}


def main():
    out = {}
    for nation, url in WIKI_URLS.items():
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            info = extract_coach(r.text)
            out[nation] = info
            status = "✓" if info["name"] else "❌"
            print(f"  {status} {nation:<25s} → {info.get('name','?')} ({info.get('country','?')})")
            time.sleep(0.3)  # politeness
        except Exception as e:
            print(f"  ❌ {nation}: {e}")
            out[nation] = {"name": None, "country": None, "error": str(e)}

    Path("data/wc2026_coaches.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"\n✓ Salvati {len(out)} allenatori in data/wc2026_coaches.json")

    # Analisi rapida
    print()
    print("=== Allenatori per nazionalità ===")
    from collections import Counter
    nc = Counter(v.get("country", "?") for v in out.values())
    for c, n in nc.most_common():
        print(f"  {n:>2}  {c}")

    print()
    print("=== Nazionali con allenatore STRANIERO ===")
    foreign = []
    for n, v in sorted(out.items()):
        if v.get("country") and v["country"].lower() != n.lower():
            # confronta con varianti note (es. "IR Iran" → "Iran")
            ncl = n.lower().replace("ir ", "")
            ccl = v["country"].lower()
            if ccl not in ncl and ncl not in ccl:
                foreign.append((n, v["name"], v["country"]))
    for n, name, c in foreign:
        print(f"  {n:<25s} → {name} ({c})")


if __name__ == "__main__":
    main()

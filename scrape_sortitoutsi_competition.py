"""
scrape_sortitoutsi_competition.py — Estrae i sortitoutsi_team_id di una
competizione (es. First Division) e aggiorna clubs.json + clubs_list.csv.

Uso:
    python3 scrape_sortitoutsi_competition.py
"""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from scraper.config import CLUBS_FILE, USER_AGENTS

ROOT = Path(__file__).parent
CLUBS_LIST_CSV = ROOT / "clubs_list.csv"

# Pagine competizione sortitoutsi note
COMPETITIONS = {
    "IT1": {
        "url": "https://sortitoutsi.net/football-manager-2026/competition/32/italian-serie-a",
        "league_id": "IT1",
    },
    "IT2": {
        "url": "https://sortitoutsi.net/football-manager-2026/competition/33/serie-bkt",
        "league_id": "IT2",
    },
}

HEADERS = {
    "User-Agent": USER_AGENTS[0],
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _norm(s: str) -> str:
    if not s:
        return ""
    nfkd = unicodedata.normalize("NFKD", s)
    no_acc = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    s = re.sub(r"[^a-zA-Z\s]", " ", no_acc).lower().strip()
    # Rimuovi tokens generici (a, c, f, s, u — sigle dei prefissi tipo "AC", "FC", "SSC")
    # e parole generiche tipo "calcio", "club", "1913" già rimosse dalla regex sopra (i numeri).
    # Inoltre rimuovi parole come "milan", "milano" sono troppo specifiche, le lasciamo.
    DROP_TOKENS = {"ac", "fc", "ssc", "ss", "us", "uc", "acf", "afc"}
    tokens = [t for t in s.split() if t not in DROP_TOKENS and len(t) > 1]
    return " ".join(tokens)


# Alias manuali per club che SortItOutSi e Transfermarkt nominano in modo molto diverso
SOTS_TO_TM_ALIAS = {
    # Serie A
    "internazionale milano": "Inter Milan",
    "atalanta bergamasca calcio": "Atalanta BC",
    "bologna 1909": "Bologna FC 1909",
    "fiorentina": "ACF Fiorentina",
    "milan": "AC Milan",
    "roma": "AS Roma",
    "lazio": "SS Lazio",
    "napoli": "SSC Napoli",
    "torino": "Torino FC",
    "juventus": "Juventus FC",
    "lecce": "US Lecce",
    "cremonese": "US Cremonese",
    "sassuolo calcio": "US Sassuolo",
    "genoa": "Genoa CFC",
    "pisa": "Pisa Sporting Club",
    # Serie B
    "monza": "AC Monza",
    "reggiana 1919": "AC Reggiana 1919",
    "cesena": "Cesena FC",
    "empoli": "FC Empoli",
    "sudtirol": "FC Sudtirol",  # SortItOutSi normalizza Südtirol -> Sudtirol
    "modena 2018": "Modena FC",
    "palermo": "Palermo FC",
    "juve stabia": "SS Juve Stabia",
    "bari": "SSC Bari",
    "sampdoria": "UC Sampdoria",
    "avellino 1912": "US Avellino 1912",
    "catanzaro 1929": "US Catanzaro",
    "venezia": "Venezia FC",
}



def fetch_competition_teams(url: str) -> list[dict]:
    """Estrae lista {sots_team_id, name} dalla pagina competizione."""
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    seen: set[int] = set()
    out: list[dict] = []
    for a in soup.select('a[href*="/team/"]'):
        href = a.get("href", "")
        m = re.search(r"/team/(\d+)/([^/?]+)", href)
        if not m:
            continue
        sid = int(m.group(1))
        if sid in seen:
            continue
        seen.add(sid)
        name = a.get_text(" ", strip=True) or m.group(2).replace("-", " ").title()
        out.append({"sots_team_id": sid, "name": name, "slug": m.group(2)})
    return out


def main() -> None:
    # Carica clubs.json esistente
    clubs = json.loads(CLUBS_FILE.read_text(encoding="utf-8"))
    by_norm_name = {_norm(c["name"]): c for c in clubs}

    # Carica clubs_list.csv esistente per aggiornarlo
    csv_rows: list[dict] = []
    if CLUBS_LIST_CSV.exists():
        with CLUBS_LIST_CSV.open(encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=";")
            csv_rows = list(reader)
    csv_by_name = {(r.get("club") or "").strip(): r for r in csv_rows}

    total_added = 0
    for league_id, info in COMPETITIONS.items():
        print(f"\n=== {league_id} ===")
        try:
            teams = fetch_competition_teams(info["url"])
        except Exception as e:
            print(f"  [error] {e}")
            continue
        print(f"  team trovati: {len(teams)}")

        for t in teams:
            name_n = _norm(t["name"])
            # Match con un nostro club (per nome normalizzato)
            ours = None
            # Prima prova alias diretto
            if name_n in SOTS_TO_TM_ALIAS:
                tm_target = SOTS_TO_TM_ALIAS[name_n]
                for c in clubs:
                    if c["name"] == tm_target:
                        ours = c
                        break
            # Poi fallback su match per nome normalizzato
            if not ours:
                for our_norm, c in by_norm_name.items():
                    if name_n == our_norm or name_n in our_norm or our_norm in name_n:
                        ours = c
                        break
            if not ours:
                print(f"  [no-match] sots {t['sots_team_id']:>10}  {t['name']!r}")
                continue
            # Aggiorna se mancante
            if not ours.get("sortitoutsi_team_id"):
                ours["sortitoutsi_team_id"] = t["sots_team_id"]
                ours["sortitoutsi_logo_url"] = f"https://sortitoutsi.b-cdn.net/uploads/team/{t['sots_team_id']}.png"
                print(f"  + {ours['name']:<28}  →  sots {t['sots_team_id']}")
                total_added += 1
                # Aggiorna anche clubs_list.csv
                csv_row = csv_by_name.get(ours["name"])
                if csv_row:
                    csv_row["sortitoutsi_team_id"] = str(t["sots_team_id"])
                else:
                    csv_rows.append({
                        "club": ours["name"],
                        "sortitoutsi_team_id": str(t["sots_team_id"]),
                        "": "",
                    })

    # Salva clubs.json
    CLUBS_FILE.write_text(json.dumps(clubs, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nclubs.json aggiornato (+{total_added} sortitoutsi_team_id)")

    # Salva clubs_list.csv (preserva header originale)
    if csv_rows:
        # Dedup per nome
        seen = set()
        deduped = []
        for r in csv_rows:
            name = (r.get("club") or "").strip()
            if not name or name in seen:
                continue
            seen.add(name)
            deduped.append(r)
        # Scrivi
        fieldnames = ["club", "sortitoutsi_team_id", ""]
        with CLUBS_LIST_CSV.open("w", encoding="utf-8", newline="") as f:
            f.write("﻿")  # BOM
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
            writer.writeheader()
            for r in deduped:
                writer.writerow({
                    "club": r.get("club", ""),
                    "sortitoutsi_team_id": r.get("sortitoutsi_team_id", ""),
                    "": "",
                })
        print(f"clubs_list.csv aggiornato ({len(deduped)} righe)")


if __name__ == "__main__":
    main()

"""
parse_fifa_squadlist.py — Estrae le 48 rose ufficiali FIFA dal PDF
SquadLists-English.pdf e le salva come wc2026_squads_fifa.json.

Formato output (per nazione):
  {
    "Algeria": {
      "country_code": "ALG",
      "players": [
        {
          "number": 1,
          "position": "GK",
          "short_name": "MASTIL Melvin",
          "first_name": "Melvin Feycal",
          "last_name": "MASTIL",
          "name_on_shirt": "MASTIL",
          "date_of_birth": "2000-02-19",   # ISO
          "club": "FC Stade Nyonnais",
          "club_country": "SUI",
          "height_cm": 194
        },
        ...
      ]
    },
    ...
  }
"""
from __future__ import annotations
import json
import re
from pathlib import Path
import sys
import pdfplumber

PDF = Path("/Users/simone/Downloads/SquadLists-English.pdf")
OUT = Path("data/wc2026_squads_fifa.json")

# Mapping nomi PDF → nomi usati in wc2026_squads_raw.json (Wikipedia)
COUNTRY_NAME_MAP = {
    "USA": "United States",
    "South Korea": "South Korea",
    "Republic of Korea": "South Korea",
    "Iran (Islamic Republic of)": "Iran",
    "Türkiye": "Turkey",
    "Cabo Verde": "Cape Verde",
    "Bosnia and Herzegovina": "Bosnia and Herzegovina",
    "Curaçao": "Curaçao",
    "Czech Republic": "Czech Republic",
    "DR Congo": "DR Congo",
    "Côte d'Ivoire": "Ivory Coast",
    "Ivory Coast": "Ivory Coast",
    "New Zealand": "New Zealand",
    "Saudi Arabia": "Saudi Arabia",
    "South Africa": "South Africa",
    "United States": "United States",
    "DR Congo (Democratic Republic of the Congo)": "DR Congo",
}


def parse_dob(s: str) -> str | None:
    """DD/MM/YYYY → YYYY-MM-DD."""
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", s.strip())
    if not m:
        return None
    d, mn, y = m.groups()
    return f"{y}-{int(mn):02d}-{int(d):02d}"


def parse_country_header(text: str) -> tuple[str, str] | None:
    """Cerca 'Algeria (ALG)' o 'Côte d'Ivoire (CIV)'.
    Ritorna (country_name, code) o None."""
    # match: prima riga col pattern Nazione (CCC)
    for line in text.splitlines():
        m = re.match(r"^\s*(.+?)\s*\(([A-Z]{3})\)\s*$", line)
        if m:
            return m.group(1).strip(), m.group(2)
    return None


def parse_player_row(line: str) -> dict | None:
    """Parse una riga giocatore. Formato:
      # POS PLAYER_NAME FIRST_NAME(S) LAST_NAME(S) NAME_ON_SHIRT DOB CLUB (CC) HEIGHT
    """
    # Pattern molto strict: numero, pos, ..., DOB DD/MM/YYYY, club (CCC), height
    # Esempio:
    #   1 GK MASTIL Melvin Melvin Feycal MASTIL MASTIL 19/02/2000 FC Stade Nyonnais (SUI) 194
    m = re.match(
        r"^\s*(\d{1,2})\s+(GK|DF|MF|FW)\s+"
        r"(.+?)\s+"
        r"(\d{1,2}/\d{1,2}/\d{4})\s+"
        r"(.+?)\s*\(([A-Z]{2,4})\)\s+"
        r"(\d{2,3})\s*$",
        line,
    )
    if not m:
        return None
    number = int(m.group(1))
    pos = m.group(2)
    middle = m.group(3).strip()
    dob = parse_dob(m.group(4))
    club = m.group(5).strip()
    club_country = m.group(6)
    height = int(m.group(7))

    # Il "middle" contiene: SHORT_NAME FIRST_NAMES LAST_NAMES NAME_ON_SHIRT
    # Pattern: SHORT_NAME è "COGNOME Nome" (es. "MASTIL Melvin")
    # FIRST_NAMES (mixed case) + LAST_NAMES (UPPER) + NAME_ON_SHIRT (UPPER, può combaciare con LAST)
    # Strategia: SHORT_NAME è i primi 2 token (UPPER + Title), poi cerco
    # NAME_ON_SHIRT come ultimo blocco UPPER consecutivo.
    # Mantengo il middle blob — analisi piu' fine se serve.
    parts = middle.split()
    # Trova primo token che inizia con maiuscola seguita da minuscola = first_name start
    # Heuristica più semplice: cerco l'ultimo run consecutivo di token tutti UPPER
    upper_runs = []
    cur = []
    for tok in parts:
        # Considera UPPER chi ha solo maiuscole/spazi/apostrofi/punto
        if tok == tok.upper() and any(c.isalpha() for c in tok):
            cur.append(tok)
        else:
            if cur:
                upper_runs.append(cur)
                cur = []
    if cur:
        upper_runs.append(cur)

    name_on_shirt = " ".join(upper_runs[-1]) if upper_runs else ""
    # short_name = primo run UPPER + primo token capitalized dopo
    short_name = ""
    if len(parts) >= 2:
        short_name = " ".join(parts[:2])  # approssimazione
    # full nome (first + last) = middle senza short_name e senza name_on_shirt
    # Per ora salviamo i campi grezzi.
    return {
        "number": number,
        "position": pos,
        "short_name": short_name,
        "raw_names_blob": middle,
        "name_on_shirt": name_on_shirt,
        "date_of_birth": dob,
        "club": club,
        "club_country": club_country,
        "height_cm": height,
    }


# pt69: nazionalità multi-word usate dal PDF FIFA per i coach (servono per
# dedurre dove inizia il country name nel blob "Head coach NAME COUNTRY").
KNOWN_MULTIWORD_COUNTRIES = [
    "Bosnia and Herzegovina", "Bosnia And Herzegovina",
    "Burkina Faso", "Cabo Verde", "Cape Verde",
    "Costa Rica", "Côte d'Ivoire", "Côte D'Ivoire",
    "Czech Republic", "DR Congo",
    "IR Iran", "Ivory Coast", "Korea Republic", "New Zealand",
    "North Macedonia", "Republic of Korea", "Saudi Arabia",
    "Sierra Leone", "South Africa", "South Korea", "United States",
]


def parse_head_coach(line: str) -> dict | None:
    """Parse 'Head coach SHORT FIRST_NAMES LAST_NAMES COUNTRY'."""
    if not line.startswith("Head coach"):
        return None
    rest = line[len("Head coach"):].strip()
    # Cerca suffix country multi-word noto
    country = None
    blob = None
    for mw in KNOWN_MULTIWORD_COUNTRIES:
        if rest.endswith(" " + mw) or rest == mw:
            country = mw
            blob = rest[:-len(mw)].strip()
            break
    if country is None:
        # Fallback: ultimo token è country
        parts = rest.rsplit(" ", 1)
        if len(parts) == 2:
            blob, country = parts[0], parts[1]
        else:
            blob, country = rest, ""
    return {"name_blob": blob, "country": country}


def main():
    out: dict = {}
    with pdfplumber.open(str(PDF)) as pdf:
        for pi, page in enumerate(pdf.pages, 1):
            txt = page.extract_text() or ""
            ch = parse_country_header(txt)
            if not ch:
                print(f"⚠️  Pagina {pi}: nessun header nazione", file=sys.stderr)
                continue
            country_name, code = ch
            mapped = COUNTRY_NAME_MAP.get(country_name, country_name)
            players = []
            head_coach = None
            for line in txt.splitlines():
                p = parse_player_row(line)
                if p:
                    players.append(p)
                    continue
                hc = parse_head_coach(line)
                if hc:
                    head_coach = hc
            out[mapped] = {
                "country_code": code,
                "pdf_page": pi,
                "head_coach": head_coach,
                "players": players,
            }
            coach_str = f" — coach: {head_coach['name_blob']} ({head_coach['country']})" if head_coach else ""
            print(f"  {pi:2d}. {mapped:30s} ({code}) — {len(players)} giocatori{coach_str}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    total = sum(len(v["players"]) for v in out.values())
    print(f"\n✓ Scritto {OUT}: {len(out)} nazionali, {total} giocatori")


if __name__ == "__main__":
    main()

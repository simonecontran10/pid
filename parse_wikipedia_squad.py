"""
parse_wikipedia_squad.py — Estrae rose nazionali per il Mondiale 2026 da Wikipedia.

DEFAULT: importa SOLO rose definitive (final), riconosciute dal testo intro
"called up to the 2026 FIFA World Cup" o "announced their final squad on...".
Le pre-list, le rose "Current squad" generiche senza menzione WC, e le nazionali
"will announce on..." vengono saltate.

Strategia:
La pagina hub Wikipedia (2026_FIFA_World_Cup_squads) ha le tabelle vuote fino a
quando le rose non vengono ufficialmente registrate da FIFA il 2 giugno 2026.
Quindi lo script scarica le 48 PAGINE NAZIONALI Wikipedia (es.
France_national_football_team) e cerca la sezione "Current squad" — chi ha già
annunciato la rosa per il Mondiale la pubblica lì.

Uso:
  # mostra le 48 nazionali tracciate (non scarica niente):
  python3 parse_wikipedia_squad.py --list-countries

  # batch — scarica tutte le 48 pagine nazionali, salva solo le rose final:
  python3 parse_wikipedia_squad.py --all

  # singola nazionale via URL Wikipedia:
  python3 parse_wikipedia_squad.py --url https://en.wikipedia.org/wiki/France_national_football_team

  # paste manuale (Ctrl+D per terminare):
  python3 parse_wikipedia_squad.py --country France

  # forza l'import di rose "Current squad" generiche o pre-list:
  python3 parse_wikipedia_squad.py --all --include-preliminary

Output: data/wc2026_squads_raw.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

DATA_DIR = ROOT / "data"
OUTPUT_FILE = DATA_DIR / "wc2026_squads_raw.json"

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
HEADERS = {"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"}

POSITIONS = {"GK", "DF", "MF", "FW"}
MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12,
}


# ---------------------------------------------------------------------------
# DOB parsing
# ---------------------------------------------------------------------------

def parse_dob(text: str) -> tuple[str | None, int | None]:
    """
    Estrae data nascita ed età da stringhe tipo:
      "3 July 1995 (age 30)"
      "20 December 1998 (age 27)"
      "( 1995-07-03 ) 3 July 1995 (age 30)"  ← formato Wikipedia HTML
    Restituisce (YYYY-MM-DD, age) oppure (None, None).
    """
    # Normalizza NBSP e altri whitespace unicode
    text = text.replace("\u00a0", " ").replace("\u202f", " ")
    # Se c'è una data ISO YYYY-MM-DD all'inizio (formato Wikipedia con `(1995-07-03)`),
    # usala direttamente — è la più affidabile.
    iso_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    age_match = re.search(r"\(age\s+(\d+)\)", text)
    if iso_match:
        y, mo, d = iso_match.group(1), iso_match.group(2), iso_match.group(3)
        try:
            dt.date(int(y), int(mo), int(d))  # valida
            iso = f"{y}-{mo}-{d}"
            age = int(age_match.group(1)) if age_match else None
            return (iso, age)
        except ValueError:
            pass
    # Fallback: parsing del formato "DD MonthName YYYY (age N)"
    m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4}).*?\(age\s+(\d+)\)", text)
    if not m:
        return (None, None)
    day, month_name, year, age = m.group(1), m.group(2), m.group(3), m.group(4)
    month = MONTHS.get(month_name)
    if not month:
        return (None, None)
    try:
        d = dt.date(int(year), month, int(day))
        return (d.isoformat(), int(age))
    except ValueError:
        return (None, None)


# ---------------------------------------------------------------------------
# Parser testo "flat" (copia-incolla)
# ---------------------------------------------------------------------------

# Pattern: numero(1-2) + tab/spazi + POS(GK|DF|MF|FW) + nome + dob (con age) + caps [+ goals opzionale] + club blob
#
# Variante A (pagine nazionali tipo France_national_football_team):
#   "16  GK  Mike Maignan  3 July 1995 (age 30)  38  0  Italian Football Federation Milan"
# Variante B (pagina hub 2026_FIFA_World_Cup_squads):
#   "16  GK  Mike Maignan  3 July 1995 (age 30)  38  Italian Football Federation Milan"  (no Goals)
#
# Strategia: match shirt+pos+name+dob+caps, poi opzionalmente goals (intero corto),
# poi club blob fino al prossimo giocatore o fine.

PLAYER_RE = re.compile(
    r"""
    (\d{1,2})              # 1: shirt number
    \s+
    (GK|DF|MF|FW)          # 2: position
    \s+
    (.+?)                  # 3: name (lazy)
    \s+
    (\d{1,2}\s+[A-Za-z]+\s+\d{4}\s*\(age\s+\d+\))   # 4: dob blob
    \s+
    (\d+)                  # 5: caps
    (?:\s+(\d+))?          # 6: goals (OPZIONALE — manca su pagina hub)
    \s+
    (.+?)                  # 7: club_country + club blob (lazy)
    (?=\s+\d{1,2}\s+(?:GK|DF|MF|FW)\s+|\Z)
    """,
    re.VERBOSE | re.DOTALL,
)


# Federazioni note → country (per separare club_country dal nome club)
# Lista non esaustiva, copre i big-5 europei + altre presenti in rose Mondiale
FEDERATION_TO_COUNTRY = {
    "Italian Football Federation": "Italy",
    "French Football Federation": "France",
    "German Football Association": "Germany",
    "Royal Spanish Football Federation": "Spain",
    "The Football Association": "England",
    "Football Association of Wales": "Wales",
    "Scottish Football Association": "Scotland",
    "Irish Football Association": "Northern Ireland",
    "Football Association of Ireland": "Ireland",
    "Royal Belgian Football Association": "Belgium",
    "Royal Dutch Football Association": "Netherlands",
    "Portuguese Football Federation": "Portugal",
    "Swiss Football Association": "Switzerland",
    "Austrian Football Association": "Austria",
    "Czech-Moravian Football Union": "Czech Republic",
    "Polish Football Association": "Poland",
    "Turkish Football Federation": "Turkey",
    "Greek Football Federation": "Greece",
    "Croatian Football Federation": "Croatia",
    "Serbian Football Association": "Serbia",
    "Football Union of Russia": "Russia",
    "Ukrainian Association of Football": "Ukraine",
    "Saudi Arabian Football Federation": "Saudi Arabia",
    "United Arab Emirates Football Association": "United Arab Emirates",
    "Qatar Football Association": "Qatar",
    "Football Federation of the Islamic Republic of Iran": "Iran",
    "Japan Football Association": "Japan",
    "Korea Football Association": "South Korea",
    "Chinese Football Association": "China",
    "United States Soccer Federation": "United States",
    "Canadian Soccer Association": "Canada",
    "Mexican Football Federation": "Mexico",
    "Brazilian Football Confederation": "Brazil",
    "Argentine Football Association": "Argentina",
    "Uruguayan Football Association": "Uruguay",
    "Colombian Football Federation": "Colombia",
    "Chilean Football Federation": "Chile",
    "Peruvian Football Federation": "Peru",
    "Ecuadorian Football Federation": "Ecuador",
    "Paraguayan Football Association": "Paraguay",
    "Royal Moroccan Football Federation": "Morocco",
    "Algerian Football Federation": "Algeria",
    "Tunisian Football Federation": "Tunisia",
    "Egyptian Football Association": "Egypt",
    "Nigeria Football Federation": "Nigeria",
    "Ghana Football Association": "Ghana",
    "Football Association of Senegal": "Senegal",
    "Fédération Ivoirienne de Football": "Ivory Coast",
    "Cameroonian Football Federation": "Cameroon",
    "South African Football Association": "South Africa",
    "Football Federation Australia": "Australia",
    "New Zealand Football": "New Zealand",
}


def split_club_field(blob: str) -> tuple[str, str]:
    """
    Da 'Italian Football Federation Milan' → ('Italy', 'Milan').
    Strategia: match della federazione più lunga che fa da prefisso.
    Fallback: ('', blob) se non riconosciuta.
    """
    blob = blob.strip()
    # Ordina per lunghezza decrescente per matchare prima quelle più specifiche
    for fed in sorted(FEDERATION_TO_COUNTRY.keys(), key=len, reverse=True):
        if blob.startswith(fed):
            club = blob[len(fed):].strip()
            return (FEDERATION_TO_COUNTRY[fed], club)
    return ("", blob)


def parse_squad_text(text: str) -> list[dict]:
    """Parsa il testo flat di una rosa Wikipedia e restituisce lista di player dict."""
    # Normalizza: tab → spazio, newline multipli → spazio singolo
    flat = re.sub(r"\s+", " ", text).strip()

    players = []
    for m in PLAYER_RE.finditer(flat):
        shirt = int(m.group(1))
        pos = m.group(2)
        name = m.group(3).strip()
        dob_blob = m.group(4)
        caps = int(m.group(5))
        goals = int(m.group(6)) if m.group(6) is not None else None
        club_blob = m.group(7).strip()

        # Pulisci suffissi tipo "(captain)" dal nome
        name = re.sub(r"\s*\(captain\)\s*", "", name).strip()
        # Rimuovi eventuali asterischi/note finali
        name = re.sub(r"[\*†‡]+$", "", name).strip()

        dob, age = parse_dob(dob_blob)
        club_country, club = split_club_field(club_blob)

        players.append({
            "shirt": shirt,
            "pos": pos,
            "name": name,
            "dob": dob,
            "age": age,
            "caps": caps,
            "goals": goals,
            "club": club,
            "club_country": club_country,
        })
    return players


# ---------------------------------------------------------------------------
# Parser HTML Wikipedia (modalità --url)
# ---------------------------------------------------------------------------

def fetch_wikipedia(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text


def _table_is_squad(t) -> bool:
    """Una tabella è 'squad' se l'header contiene No./Pos./Player/Caps."""
    headers_row = t.find("tr")
    if not headers_row:
        return False
    headers_text = " ".join(th.get_text(" ", strip=True) for th in headers_row.find_all(["th", "td"]))
    return (
        re.search(r"\bNo\.?\b", headers_text) is not None
        and "Pos" in headers_text
        and "Player" in headers_text
        and "Caps" in headers_text
    )


def _table_header_columns(t) -> list[str]:
    """Ritorna lista lowercase dei nomi colonna della prima riga."""
    first = t.find("tr")
    if not first:
        return []
    return [th.get_text(" ", strip=True).lower() for th in first.find_all(["th", "td"])]


def _parse_table_rows(t) -> list[dict]:
    """
    Parsa la tabella squad cella per cella usando l'HTML strutturato.
    Molto più robusto del flat-text + regex perché non dipende dalla normalizzazione spazi.

    Supporta entrambi gli schemi:
      - pagina nazionale: No. | Pos. | Player | DOB (age) | Caps | Goals | Club
      - pagina hub:       No. | Pos. | Player | DOB (age) | Caps | Club  (no Goals)
    """
    headers = _table_header_columns(t)
    if not headers:
        return []

    # Mappa indici colonne (con fallback se il nome non corrisponde esattamente)
    def find_col(needles: list[str]) -> int:
        for needle in needles:
            for i, h in enumerate(headers):
                if needle in h:
                    return i
        return -1

    idx_no = find_col(["no.", "no", "#"])
    idx_pos = find_col(["pos."])
    idx_player = find_col(["player"])
    idx_dob = find_col(["date of birth", "dob", "birth"])
    idx_caps = find_col(["caps"])
    idx_goals = find_col(["goals"])
    idx_club = find_col(["club"])

    if idx_player == -1 or idx_dob == -1 or idx_caps == -1 or idx_club == -1:
        return []

    players = []
    for tr in t.find_all("tr")[1:]:  # skip header
        cells = tr.find_all(["td", "th"])
        if not cells or len(cells) < 4:
            continue

        def get(i: int) -> str:
            if i < 0 or i >= len(cells):
                return ""
            return cells[i].get_text(" ", strip=True)

        # Gate: la riga è valida solo se Pos contiene una posizione conosciuta.
        # Pos può venire come "GK" o "1 GK" (Wikipedia mette un numero d'ordinamento).
        pos_raw = get(idx_pos).strip()
        pos_match = re.search(r"\b(GK|DF|MF|FW)\b", pos_raw)
        if not pos_match:
            # Riga separatore (es. "Goalkeepers") o header intermedio
            continue
        pos = pos_match.group(1)

        # Shirt: opzionale. Se mancante (es. rose senza numeri ancora assegnati come
        # Bosnia 11 May 2026), shirt=None — non blocca il salvataggio.
        shirt_str = get(idx_no).strip()
        shirt_match = re.search(r"\d+", shirt_str)
        shirt = int(shirt_match.group(0)) if shirt_match else None

        # Player name: pulisci eventuali wrapping
        name = get(idx_player)
        # Wikipedia HTML può rendere "(captain)" con spazi interni: "( captain )"
        name = re.sub(r"\s*\(\s*captain\s*\)\s*", "", name, flags=re.IGNORECASE).strip()
        name = re.sub(r"[\*†‡]+$", "", name).strip()

        # DOB cell: rimuovi sia "(YYYY-MM-DD)" che "(age N)"
        dob_cell = get(idx_dob)
        dob_cell_clean = re.sub(r"\(\d{4}-\d{2}-\d{2}\)\s*", "", dob_cell)
        dob, age = parse_dob(dob_cell_clean)
        if dob is None:
            # Fallback: prova solo "(age N)" e poi cerca pattern data nella stringa
            m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", dob_cell_clean)
            if m:
                month = MONTHS.get(m.group(2))
                if month:
                    try:
                        d = dt.date(int(m.group(3)), month, int(m.group(1)))
                        dob = d.isoformat()
                    except ValueError:
                        pass

        # Caps / Goals
        caps_str = get(idx_caps)
        try:
            caps = int(re.search(r"\d+", caps_str).group(0)) if re.search(r"\d+", caps_str) else 0
        except Exception:
            caps = 0

        goals = None
        if idx_goals != -1:
            goals_str = get(idx_goals)
            mg = re.search(r"\d+", goals_str)
            if mg:
                goals = int(mg.group(0))

        # Club cell: spesso "Federation Club" o solo "Club" (con flag/icona)
        club_blob = get(idx_club).strip()
        club_country, club = split_club_field(club_blob)
        # Se split_club_field non riconosce federazione, club_blob va tutto in club
        if not club_country and club_blob:
            club = club_blob

        players.append({
            "shirt": shirt,
            "pos": pos,
            "name": name,
            "dob": dob,
            "age": age,
            "caps": caps,
            "goals": goals,
            "club": club,
            "club_country": club_country,
        })

    return players


def _classify_squad_status(intro_text: str) -> str:
    """
    Classifica il testo introduttivo della sezione di una nazionale come:
      - "final"        → "announced their final squad on X" / "called up to the 2026 FIFA World Cup"
      - "preliminary"  → "announced a 55-man preliminary squad" / "provisional"
      - "pending"      → "will announce their final squad on X" (futuro, niente tabella valida)
      - "unknown"      → fallback
    """
    t = intro_text.lower()
    # Pending (futuro) — controllarlo PRIMA di "final" perché contiene la parola "final"
    if "will announce" in t and ("final squad" in t or "squad on" in t):
        return "pending"
    # Final (passato): "announced their final squad on" / "called up to the 2026 FIFA World Cup"
    if re.search(r"announced (?:their |the |a )?final squad", t):
        return "final"
    if "called up to the 2026 fifa world cup" in t:
        return "final"
    # Preliminary
    if re.search(r"\b(preliminary|provisional)\b.*squad", t) or re.search(r"\d+-man (preliminary|provisional)", t):
        return "preliminary"
    return "unknown"


def _extract_country_from_section(prev_elements: list) -> str | None:
    """
    Dato l'insieme di elementi <p> e heading prima di una tabella squad,
    estrai il nome della nazionale.

    Strategia:
    1) Cerca pattern "[Country] national football team" / "Country's final squad..."
    2) Cerca un heading h2/h3/h4 col nome paese
    3) Cerca link a /wiki/Country_national_football_team
    """
    # Pattern 1: testi tipo "Country's final squad" o "Country announced their..."
    for el in prev_elements:
        text = el.get_text(" ", strip=True) if hasattr(el, "get_text") else str(el)
        m = re.search(r"^([A-Z][A-Za-z\s&]+?)(?:'s|\s+announced|\s+will announce)", text)
        if m:
            return m.group(1).strip()

    # Pattern 2: link a Country_national_football_team
    for el in prev_elements:
        if not hasattr(el, "find_all"):
            continue
        for a in el.find_all("a", href=True):
            href = a.get("href", "")
            m = re.search(r"/wiki/([A-Za-z_]+?)(?:_men's)?_national_(?:football|soccer)_team", href)
            if m:
                return m.group(1).replace("_", " ").strip()

    # Pattern 3: heading
    for el in prev_elements:
        if getattr(el, "name", None) in ("h2", "h3", "h4"):
            text = el.get_text(" ", strip=True)
            # Skip heading molto generici
            if text and len(text) < 40 and not any(skip in text.lower() for skip in ("group", "reference", "note", "see also", "key", "summary", "statistics")):
                return text

    return None


def parse_squad_html(html: str, country: str | None = None,
                     only_final: bool = True) -> tuple[list[dict], str]:
    """
    Cerca la tabella squadra nell'HTML Wikipedia.

    Ritorna (players, status) dove status ∈ {"final","preliminary","pending","unknown"}.

    Caso 1 — pagina dedicata (es. France_national_football_team):
        Prendi la prima tabella squad (sezione "Current squad").

    Caso 2 — pagina hub `2026_FIFA_World_Cup_squads`:
        Ci sono 48 sezioni. Trovo tutte le squad_tables e per ognuna risalgo
        ai paragrafi precedenti per identificare la nazione e classificare status.
    """
    soup = BeautifulSoup(html, "lxml")
    all_tables = soup.find_all("table", class_="wikitable")
    squad_tables = [t for t in all_tables if _table_is_squad(t)]

    if not squad_tables:
        return ([], "unknown")

    # Sull'intero documento, cerca il pattern definitivo "rosa Mondiale 2026"
    # Funziona indipendentemente da dove sta nella pagina.
    full_text_lower = soup.get_text(" ", strip=True).lower()
    is_wc2026_final = (
        "called up to the 2026 fifa world cup" in full_text_lower
        or "called up for the 2026 fifa world cup" in full_text_lower
    )
    has_preliminary_wc2026 = (
        "preliminary squad for the 2026 fifa world cup" in full_text_lower
        or "provisional squad for the 2026 fifa world cup" in full_text_lower
    )

    # Pagina nazionale: 1 o 2 tabelle squad (Current squad + eventualmente Recent call-ups)
    # Pagina hub: molte tabelle (>= 5) — solo lì serve il dispatch via country.
    is_hub_page = len(squad_tables) >= 5

    # ---- Caso A: pagina nazionale ----
    if not is_hub_page:
        # Prima tabella squad = "Current squad" (più in alto nella pagina)
        table = squad_tables[0]
        # Status: se nel documento c'è il pattern WC2026 → final
        if is_wc2026_final:
            status = "final"
        elif has_preliminary_wc2026:
            status = "preliminary"
        else:
            status = "unknown"
        if only_final and status != "final":
            return ([], status)
        players = _parse_table_rows(table)
        return (players, status)

    # ---- Caso B: pagina hub ----
    if not country:
        print(f"⚠️  Trovate {len(squad_tables)} tabelle squad; specifica --country per scegliere", file=sys.stderr)
        return ([], "unknown")

    country_norm = country.strip().lower()

    # Per ogni squad_table, ricostruisci la sezione (paragrafi tra la tabella e quella precedente)
    for idx, table in enumerate(squad_tables):
        # Raccogli paragrafi/heading precedenti fino alla tabella precedente (o all'inizio del documento)
        section_elements = []
        prev_table = squad_tables[idx - 1] if idx > 0 else None
        for sib in table.find_all_previous():
            if sib is prev_table:
                break
            if sib.name in ("p", "h2", "h3", "h4"):
                section_elements.insert(0, sib)
            # Limita la risalita per non andare troppo indietro
            if len(section_elements) > 15:
                break

        section_country = _extract_country_from_section(section_elements)
        if not section_country:
            continue

        if section_country.lower() != country_norm:
            continue

        # Trovata sezione del paese richiesto
        intro_text = " ".join(
            el.get_text(" ", strip=True) for el in section_elements if hasattr(el, "get_text")
        )
        status = _classify_squad_status(intro_text)

        if only_final and status != "final":
            return ([], status)

        players = _parse_table_rows(table)
        return (players, status)

    print(f"⚠️  Sezione '{country}' non trovata nella pagina hub", file=sys.stderr)
    return ([], "unknown")


# ---------------------------------------------------------------------------
# I/O su data/wc2026_squads_raw.json
# ---------------------------------------------------------------------------

def load_squads() -> dict:
    if not OUTPUT_FILE.exists():
        return {}
    return json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))


def save_squads(data: dict) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

HUB_URL = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_squads"

# Le 48 nazionali qualificate al Mondiale 2026, con URL della pagina Wikipedia nazionale.
# La pagina hub Wikipedia è strutturalmente inutile per scraping (tabelle vuote, nessun
# heading per nazione). Le pagine nazionali invece hanno la sezione "Current squad" che
# contiene la rosa attuale (per chi l'ha già annunciata) o una rosa recente.
NATIONAL_TEAMS_URLS: dict[str, str] = {
    # Hosts
    "United States": "https://en.wikipedia.org/wiki/United_States_men%27s_national_soccer_team",
    "Canada": "https://en.wikipedia.org/wiki/Canada_men%27s_national_soccer_team",
    "Mexico": "https://en.wikipedia.org/wiki/Mexico_national_football_team",
    # UEFA (16)
    "England": "https://en.wikipedia.org/wiki/England_national_football_team",
    "France": "https://en.wikipedia.org/wiki/France_national_football_team",
    "Croatia": "https://en.wikipedia.org/wiki/Croatia_national_football_team",
    "Norway": "https://en.wikipedia.org/wiki/Norway_national_football_team",
    "Portugal": "https://en.wikipedia.org/wiki/Portugal_national_football_team",
    "Germany": "https://en.wikipedia.org/wiki/Germany_national_football_team",
    "Netherlands": "https://en.wikipedia.org/wiki/Netherlands_national_football_team",
    "Switzerland": "https://en.wikipedia.org/wiki/Switzerland_national_football_team",
    "Scotland": "https://en.wikipedia.org/wiki/Scotland_national_football_team",
    "Spain": "https://en.wikipedia.org/wiki/Spain_national_football_team",
    "Austria": "https://en.wikipedia.org/wiki/Austria_national_football_team",
    "Belgium": "https://en.wikipedia.org/wiki/Belgium_national_football_team",
    "Bosnia and Herzegovina": "https://en.wikipedia.org/wiki/Bosnia_and_Herzegovina_national_football_team",
    "Sweden": "https://en.wikipedia.org/wiki/Sweden_national_football_team",
    "Turkey": "https://en.wikipedia.org/wiki/Turkey_national_football_team",
    "Czech Republic": "https://en.wikipedia.org/wiki/Czech_Republic_national_football_team",
    # CONMEBOL (6)
    "Argentina": "https://en.wikipedia.org/wiki/Argentina_national_football_team",
    "Brazil": "https://en.wikipedia.org/wiki/Brazil_national_football_team",
    "Uruguay": "https://en.wikipedia.org/wiki/Uruguay_national_football_team",
    "Colombia": "https://en.wikipedia.org/wiki/Colombia_national_football_team",
    "Ecuador": "https://en.wikipedia.org/wiki/Ecuador_national_football_team",
    "Paraguay": "https://en.wikipedia.org/wiki/Paraguay_national_football_team",
    # AFC (8)
    "Japan": "https://en.wikipedia.org/wiki/Japan_national_football_team",
    "Iran": "https://en.wikipedia.org/wiki/Iran_national_football_team",
    "South Korea": "https://en.wikipedia.org/wiki/South_Korea_national_football_team",
    "Australia": "https://en.wikipedia.org/wiki/Australia_men%27s_national_soccer_team",
    "Saudi Arabia": "https://en.wikipedia.org/wiki/Saudi_Arabia_national_football_team",
    "Qatar": "https://en.wikipedia.org/wiki/Qatar_national_football_team",
    "Jordan": "https://en.wikipedia.org/wiki/Jordan_national_football_team",
    "Uzbekistan": "https://en.wikipedia.org/wiki/Uzbekistan_national_football_team",
    # CAF (9)
    "Morocco": "https://en.wikipedia.org/wiki/Morocco_national_football_team",
    "Tunisia": "https://en.wikipedia.org/wiki/Tunisia_national_football_team",
    "Egypt": "https://en.wikipedia.org/wiki/Egypt_national_football_team",
    "Algeria": "https://en.wikipedia.org/wiki/Algeria_national_football_team",
    "Ghana": "https://en.wikipedia.org/wiki/Ghana_national_football_team",
    "Senegal": "https://en.wikipedia.org/wiki/Senegal_national_football_team",
    "Ivory Coast": "https://en.wikipedia.org/wiki/Ivory_Coast_national_football_team",
    "South Africa": "https://en.wikipedia.org/wiki/South_Africa_national_football_team",
    "Cape Verde": "https://en.wikipedia.org/wiki/Cape_Verde_national_football_team",
    # CONCACAF (3 oltre agli host)
    "Panama": "https://en.wikipedia.org/wiki/Panama_national_football_team",
    "Haiti": "https://en.wikipedia.org/wiki/Haiti_national_football_team",
    "Curaçao": "https://en.wikipedia.org/wiki/Cura%C3%A7ao_national_football_team",
    # OFC (1)
    "New Zealand": "https://en.wikipedia.org/wiki/New_Zealand_men%27s_national_football_team",
    # Inter-confederation playoff winners
    "DR Congo": "https://en.wikipedia.org/wiki/DR_Congo_national_football_team",
    "Iraq": "https://en.wikipedia.org/wiki/Iraq_national_football_team",
}


def list_hub_countries(html: str) -> list[tuple[str, str]]:
    """
    Estrai (country, status) per ogni sezione della pagina hub.
    Strategia: itera su tutte le squad_tables, per ognuna risale ai paragrafi
    precedenti per identificare nazione + classificare status.
    """
    soup = BeautifulSoup(html, "lxml")
    all_tables = soup.find_all("table", class_="wikitable")
    squad_tables = [t for t in all_tables if _table_is_squad(t)]

    out = []
    for idx, table in enumerate(squad_tables):
        section_elements = []
        prev_table = squad_tables[idx - 1] if idx > 0 else None
        for sib in table.find_all_previous():
            if sib is prev_table:
                break
            if sib.name in ("p", "h2", "h3", "h4"):
                section_elements.insert(0, sib)
            if len(section_elements) > 15:
                break

        country = _extract_country_from_section(section_elements)
        if not country:
            continue
        intro_text = " ".join(
            el.get_text(" ", strip=True) for el in section_elements if hasattr(el, "get_text")
        )
        status = _classify_squad_status(intro_text)
        # Se nessun pattern matcha ma la tabella ha righe → assumiamo final
        if status == "unknown":
            n_rows = len([tr for tr in table.find_all("tr")[1:] if tr.find_all(["td", "th"])])
            if n_rows >= 20:
                status = "final"
        out.append((country, status))
    return out


def process_one(country: str, players: list[dict], status: str,
                wiki_url: str | None, squads: dict, dry_run: bool) -> bool:
    """Stampa report e salva (o no) una rosa. Ritorna True se salvata."""
    print(f"\n--- {country} [{status}] ---")
    if not players:
        if status == "pending":
            print(f"  ⏳ Rosa finale non ancora annunciata. Skip.")
        elif status == "preliminary":
            print(f"  📋 Solo pre-list disponibile (skip, importiamo solo rose final).")
        elif status == "unknown":
            print(f"  ❓ Rosa non riconosciuta come 'final' (testo intro ambiguo). Skip. Usa --include-preliminary per forzare.")
        else:
            print(f"  ❌ Nessun giocatore parsato. Status: {status}")
        return False

    print(f"  ✓ {len(players)} giocatori parsati")
    print(f"  {'#':>3}  {'P':<3} {'NAME':<28} {'DOB':<12} {'CAPS':>5} {'GOALS':>6}  CLUB")
    print("  " + "-" * 90)
    for p in players:
        goals_str = str(p['goals']) if p['goals'] is not None else "—"
        shirt_str = str(p['shirt']) if p['shirt'] is not None else "—"
        print(f"  {shirt_str:>3}  {p['pos']:<3} {p['name']:<28} {p['dob'] or '?':<12} {p['caps']:>5} {goals_str:>6}  {p['club']}")

    n_missing_dob = sum(1 for p in players if not p["dob"])
    n_missing_club = sum(1 for p in players if not p["club"])
    n_missing_shirt = sum(1 for p in players if p.get("shirt") is None)
    if n_missing_dob:
        print(f"  ⚠️  {n_missing_dob} giocatori senza DOB parsata")
    if n_missing_club:
        print(f"  ⚠️  {n_missing_club} giocatori senza club parsato")
    if n_missing_shirt:
        print(f"  ℹ️  {n_missing_shirt} giocatori senza numero maglia (normale se la rosa è appena stata annunciata)")

    if dry_run:
        return False

    # Preserva i campi tm_* dai player già processati da resolve_wc2026_urls.py.
    # Match per nome esatto (campo "name" Wikipedia). Se un player Wikipedia ha
    # un omonimo nella voce precedente, riprende tm_player_id/tm_profile_url/match_method.
    prev_squad = squads.get(country, {})
    prev_players_by_name = {p.get("name"): p for p in prev_squad.get("players", [])}
    for p in players:
        prev = prev_players_by_name.get(p.get("name"))
        if not prev:
            continue
        for k in ("tm_player_id", "tm_profile_url", "match_method"):
            if prev.get(k) is not None and p.get(k) is None:
                p[k] = prev[k]

    squads[country] = {
        "country": country,
        "wiki_url": wiki_url,
        "status": status,
        "imported_at": dt.datetime.now().isoformat(timespec="seconds"),
        "players": players,
    }
    return True


def _debug_page(html: str, country: str) -> None:
    """Stampa diagnostica: quante squad_tables, frasi WC2026 trovate, dimensione tabelle, prime righe."""
    soup = BeautifulSoup(html, "lxml")
    all_tables = soup.find_all("table", class_="wikitable")
    squad_tables = [t for t in all_tables if _table_is_squad(t)]
    full_text_lower = soup.get_text(" ", strip=True).lower()

    print(f"\n[DEBUG] Pagina '{country}':")
    print(f"  - HTML size: {len(html):,} chars")
    print(f"  - <table class='wikitable'>: {len(all_tables)} totali")
    print(f"  - di cui squad (No./Pos./Player/Caps): {len(squad_tables)}")
    for i, t in enumerate(squad_tables):
        n_rows = len([tr for tr in t.find_all('tr')[1:] if tr.find_all(['td', 'th'])])
        headers = _table_header_columns(t)
        print(f"    [{i}] {n_rows} righe — header: {headers}")
        # Dump prime 2 righe non-header per vedere il contenuto reale delle celle
        rows = t.find_all("tr")[1:3]
        for ri, tr in enumerate(rows):
            cells = tr.find_all(["td", "th"])
            print(f"      row[{ri}] {len(cells)} celle:")
            for ci, cell in enumerate(cells):
                txt = cell.get_text(" ", strip=True)
                print(f"        [{ci}] {txt[:80]!r}")
    print(f"  - 'called up to the 2026 fifa world cup': {'YES' if 'called up to the 2026 fifa world cup' in full_text_lower else 'no'}")
    print(f"  - 'called up for the 2026 fifa world cup': {'YES' if 'called up for the 2026 fifa world cup' in full_text_lower else 'no'}")
    print(f"  - 'preliminary squad for the 2026 fifa world cup': {'YES' if 'preliminary squad for the 2026 fifa world cup' in full_text_lower else 'no'}")
    print()


def main() -> int:
    ap = argparse.ArgumentParser(description="Parse Wikipedia WC2026 squad → JSON")
    ap.add_argument("--country", help="Nome nazionale (es. 'France').")
    ap.add_argument("--url", help="URL Wikipedia pagina nazionale (es. France_national_football_team) o pagina hub")
    ap.add_argument("--file", help="Leggi testo da file invece che stdin (modalità paste)")
    ap.add_argument("--all", action="store_true", help="Scarica TUTTE le 48 nazionali WC2026 dalle pagine Wikipedia nazionali (~48 fetch)")
    ap.add_argument("--list-countries", action="store_true", help="Mostra elenco delle 48 nazionali tracciate (non scarica niente)")
    ap.add_argument("--include-preliminary", action="store_true", help="Includi anche pre-list / 'Current squad' non legate al WC (default: solo final)")
    ap.add_argument("--dry-run", action="store_true", help="Non salva, stampa solo il risultato")
    ap.add_argument("--debug", action="store_true", help="Stampa info diagnostiche su cosa il parser trova nella pagina")
    args = ap.parse_args()

    only_final = not args.include_preliminary
    squads = load_squads()
    saved_count = 0
    skipped_count = 0

    # --- Modalità --list-countries: elenca le 48 mappate ---
    if args.list_countries:
        print(f"Le 48 nazionali WC2026 tracciate ({len(NATIONAL_TEAMS_URLS)}):\n")
        for c, url in sorted(NATIONAL_TEAMS_URLS.items()):
            print(f"  {c:<28} {url}")
        return 0

    # --- Modalità --all: cicla su tutte le 48 pagine nazionali ---
    if args.all:
        import time as _time
        print(f"Scarico {len(NATIONAL_TEAMS_URLS)} pagine nazionali Wikipedia...\n")
        for country_name in sorted(NATIONAL_TEAMS_URLS.keys()):
            url = NATIONAL_TEAMS_URLS[country_name]
            try:
                html = fetch_wikipedia(url)
            except Exception as e:
                print(f"\n--- {country_name} ---\n  ❌ Fetch fallito: {e}")
                skipped_count += 1
                continue
            players, status = parse_squad_html(html, country=country_name, only_final=only_final)
            if process_one(country_name, players, status, url, squads, args.dry_run):
                saved_count += 1
            else:
                skipped_count += 1
            _time.sleep(0.5)  # gentilezza con Wikipedia
        wiki_url = None  # multi-source

    # --- Modalità URL singolo ---
    elif args.url:
        country = args.country
        if not country:
            m = re.search(r"/wiki/([A-Za-z_]+?)_(?:men%27s_)?national_(?:football|soccer)_team", args.url)
            if m:
                country = m.group(1).replace("_", " ")
            else:
                print("Errore: --country obbligatorio (impossibile dedurlo dall'URL)", file=sys.stderr)
                return 1
        print(f"Fetch Wikipedia: {args.url}")
        html = fetch_wikipedia(args.url)
        if args.debug:
            _debug_page(html, country)
        players, status = parse_squad_html(html, country=country, only_final=only_final)
        if process_one(country, players, status, args.url, squads, args.dry_run):
            saved_count = 1
        wiki_url = args.url

    # --- Modalità paste ---
    else:
        if not args.country:
            print("Errore: --country obbligatorio in modalità paste (senza --url né --all)", file=sys.stderr)
            return 1
        country = args.country
        if args.file:
            text = Path(args.file).read_text(encoding="utf-8")
        else:
            print(f"Incolla la rosa di {country} (Ctrl+D per terminare):", file=sys.stderr)
            text = sys.stdin.read()
        players = parse_squad_text(text)
        # In modalità paste assumiamo final (l'utente decide cosa incollare)
        status = "final"
        if process_one(country, players, status, None, squads, args.dry_run):
            saved_count = 1
        wiki_url = None

    if not args.dry_run and saved_count > 0:
        save_squads(squads)
        print(f"\n{'='*70}")
        print(f"✓ Salvato in {OUTPUT_FILE}")
        print(f"  Rose importate in questo run: {saved_count}")
        if args.all:
            print(f"  Rose saltate (pending/preliminary): {skipped_count}")
        print(f"  Nazionali totali nel file: {len(squads)}")
    elif args.dry_run:
        print(f"\n[dry-run] non salvo.")

    return 0


if __name__ == "__main__":
    sys.exit(main())

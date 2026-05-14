"""Configurazione globale dello scraper Transfermarkt.

PID — Player Intelligence Database.
Parametri country-specific letti da `data/config.json` (no hardcoded country).
"""

import json
from pathlib import Path

# === Path ===
ROOT_DIR = Path(__file__).resolve().parent.parent  # pid/
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = ROOT_DIR / "raw"
SAMPLES_DIR = ROOT_DIR / "samples"
DATA_DIR.mkdir(exist_ok=True)
RAW_DIR.mkdir(exist_ok=True)

# === Carica config.json ===
PID_CONFIG_FILE = DATA_DIR / "config.json"
try:
    with open(PID_CONFIG_FILE) as f:
        PID_CONFIG = json.load(f)
except FileNotFoundError:
    PID_CONFIG = {}

# === URL Transfermarkt ===
BASE_URL = "https://www.transfermarkt.com"

# === Leghe primary/secondary/youth (urls da popolare in sera 2 quando avremo gli URL veri) ===
# Per ora la mappa è vuota: verrà popolata via add_players.py con URL squadre, oppure
# con scraping leghe quando sarà pronto.
LEAGUES = {
    # Esempio struttura quando verranno aggiunti:
    # "IT1": {
    #     "name": "Serie A",
    #     "url": f"{BASE_URL}/serie-a/startseite/wettbewerb/IT1",
    # },
    # "IT2": {
    #     "name": "Serie B",
    #     "url": f"{BASE_URL}/serie-b/startseite/wettbewerb/IT2",
    # },
}

# === Stagioni da scrapare ===
# Transfermarkt: 2025 = stagione 2025/26, 2024 = 2024/25
SEASONS = [2024, 2025]
CURRENT_SEASON = 2025

# === Filtro target (country focus) ===
# Letto da config.json. Per PID-Italia = "Italy". Per altri paesi cambia in config.
TARGET_NATIONALITY = PID_CONFIG.get("country_label_en", "Italy")

# === HTTP ===
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
]
DEFAULT_HEADERS = {
    "Accept-Language": "en-US,en;q=0.9,it;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}
XHR_HEADERS_EXTRA = {
    "Accept": "application/json, text/plain, */*",
    "X-Requested-With": "XMLHttpRequest",
}
REQUEST_TIMEOUT = 15
SLEEP_BETWEEN_REQUESTS = 1.5
MAX_RETRIES = 3
BACKOFF_BASE = 3
MAX_TOTAL_WAIT_PER_REQUEST = 300  # alzato da 60 per dare spazio ai retry lunghi sul 403

# Gestione 403 Forbidden: spesso e' un blocco IP temporaneo (es. runner GitHub
# bloccato da Transfermarkt anti-bot). A differenza del 404 (pagina inesistente,
# inutile ritentare), il 403 si risolve aspettando: l'IP si sblocca dopo minuti.
# Backoff dedicato piu' lungo: 20s, 40s, 80s, 160s.
RETRY_ON_403 = True
BACKOFF_403_BASE = 20
MAX_RETRIES_403 = 4

# === Output JSON ===
CLUBS_FILE = DATA_DIR / "clubs.json"
ROSTERS_FILE = DATA_DIR / "rosters.json"
PLAYERS_STATIC_FILE = DATA_DIR / "players_static.json"
# Rinominato da PLAYERS_SAUDI_FILE (era player saudita-specifico)
PLAYERS_MAIN_FILE = DATA_DIR / "players_main.json"
PLAYERS_STATS_FILE = DATA_DIR / "players_stats.json"
LAST_UPDATE_FILE = DATA_DIR / "last_update.json"

# === Mappa codici competizione Transfermarkt → nome leggibile ===
COMPETITION_NAMES = {
    # Club - Italia
    "IT1":  "Serie A",
    "IT2":  "Serie B",
    "CIT":  "Coppa Italia",
    "SCI":  "Supercoppa Italiana",
    "PRIM": "Primavera 1",
    # Club - Internazionali
    "CL":   "Champions League",
    "EL":   "Europa League",
    "UECL": "Conference League",
    "KLUB": "Club Friendly",
    # Nazionali (categorie principali)
    "FS":   "International Friendly",
    "WC":   "World Cup",
    "WMQ1": "World Cup Qualification",
    "EMQ":  "Euro Qualification",
    "EM":   "European Championship",
    "NL":   "UEFA Nations League",
    "GOCU": "Gold Cup",
    # Giovanili
    "20WC": "U-20 World Cup",
    "U17W": "U-17 World Cup",
    "OLYM": "Olympic Games",
    "EM21": "U-21 European Championship",
    "U21Q": "U-21 Euro Qualification",
    "U19E": "U-19 European Championship",
    "U17E": "U-17 European Championship",
    # Altre leghe estere (giocatori che hanno militato altrove)
    "GB1":  "Premier League",
    "ES1":  "LaLiga",
    "L1":   "Bundesliga",
    "FR1":  "Ligue 1",
}


def comp_name(code: str) -> str:
    """Nome leggibile di una competizione, fallback al codice."""
    return COMPETITION_NAMES.get(code, code)


# === Categoria di nazionale ===
# TM distingue le nazionali via il clubId del team. PID con giocatori da
# tante nazionalità diverse (Italia, Belgio, Brasile, ecc.) potrebbe avere
# un mapping pieno di id, ma in pratica Transfermarkt espone team_category
# direttamente nei profili giocatore quasi sempre. Lasciamo il mapping vuoto
# e ci affidiamo al valore TM. Se in futuro emergono casi senza team_category
# nel profilo, popoliamo qui.
NATIONAL_CLUB_IDS: dict[str, str] = {
    # Esempio: "3376": "A",  # Italia (senior) — popolare se serve
}

# Fallback se clubId sconosciuto: deduzione via competition_id
NATIONAL_TEAM_CATEGORY_FROM_COMP = {
    "20WC":  "U20",
    "U17W":  "U17",
    "17WC":  "U17",
    "16WC":  "U16",
    "OLYM":  "Olympic",
    "23WC":  "U23",
    "U23A":  "U23",
    "U23W":  "U23",
    "EM21":  "U21",
    "U21Q":  "U21",
    "U19E":  "U19",
    "U17E":  "U17",
}


def _heuristic_category_from_comp(comp_id: str) -> str | None:
    """Pattern heuristic: codici che contengono U17/16/U20/20/U23/23/OLY → categoria."""
    if not comp_id:
        return None
    c = comp_id.upper()
    if "U21" in c or "21" in c:
        return "U21"
    if "U17" in c or "17" in c:
        return "U17"
    if "U16" in c or "16" in c:
        return "U16"
    if "U20" in c or "20" in c:
        return "U20"
    if "U23" in c or "23" in c:
        return "U23"
    if "U19" in c or "19" in c:
        return "U19"
    if "OLYM" in c or "OLY" in c:
        return "Olympic"
    return None


def national_team_category_from_club(club_id) -> str | None:
    if club_id is None:
        return None
    return NATIONAL_CLUB_IDS.get(str(club_id))


def national_team_category_from_comp(competition_id: str) -> str:
    if competition_id in NATIONAL_TEAM_CATEGORY_FROM_COMP:
        return NATIONAL_TEAM_CATEGORY_FROM_COMP[competition_id]
    h = _heuristic_category_from_comp(competition_id)
    if h:
        return h
    return "A"


def national_team_category(club_id, competition_id: str) -> str:
    """Determina categoria nazionale: prima da clubId (fonte primaria), poi fallback da competition."""
    cat = national_team_category_from_club(club_id)
    if cat:
        return cat
    return national_team_category_from_comp(competition_id)


def national_team_label(category: str, country: str = None) -> str:
    """Costruisce il nome della nazionale.

    Per PID multi-nazionalità: il country viene passato dal chiamante, basato
    sulla nazionalità del giocatore. Se non passato, usa il TARGET_NATIONALITY
    dal config.json (= 'Italy' di default per PID-Italia).

    'A' → 'Italy'; 'U20' → 'Italy U20'; 'Olympic' → 'Italy Olympic'.
    """
    country = country or TARGET_NATIONALITY
    if category == "A":
        return country
    if category == "Olympic":
        return f"{country} Olympic"
    return f"{country} {category}"


# === Compatibilità retroattiva (alias) ===
# Mantengo i vecchi nomi per non rompere import esistenti durante la migrazione.
# Da rimuovere quando tutti i moduli scraper sono migrati.
SAUDI_NATIONALITY = TARGET_NATIONALITY  # alias deprecato
PLAYERS_SAUDI_FILE = PLAYERS_MAIN_FILE  # alias deprecato

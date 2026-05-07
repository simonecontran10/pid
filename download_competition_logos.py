"""
download_competition_logos.py — Scarica i loghi delle competizioni da TM CDN
e arricchisce COMP_LABEL in app.js con i nomi italianizzati delle competizioni.

Strategia:
  1. Scarica players_stats da R2 (o usa cache locale)
  2. Aggrega tutti i codici TM competizione che compaiono almeno 3 volte
  3. Per ogni codice, prova a scaricare da CDN TM:
     https://tmssl.akamaized.net/images/logo/homepageWappen150x150/{code_lower}.png
  4. Salva in data/photos/competitions/{code}.png se valido (>500 bytes)
  5. Stampa lista chiavi per aggiornamento manuale di COMP_LABEL e competitionLogo() in app.js

Uso:
    source venv/bin/activate
    python3 download_competition_logos.py [--all]    # default scarica solo i top usati
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

import requests

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
COMPETITIONS_DIR = DATA_DIR / "photos" / "competitions"
COMPETITIONS_DIR.mkdir(parents=True, exist_ok=True)

R2_PUBLIC_URL = "https://pub-aa9d173290684b36a9f35e79d4d388c2.r2.dev"
TMSSL_PATTERNS = [
    "https://tmssl.akamaized.net/images/logo/homepageWappen150x150/{code}.png",
    "https://tmssl.akamaized.net/images/logo/medium/{code}.png",
    "https://tmssl.akamaized.net/images/logo/header/{code}.png",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Referer": "https://www.transfermarkt.com/",
}

# Override manuali per codici dove TM CDN non ha il logo (es. Bundesliga BL1)
# o dove vogliamo usare un nome più conciso/italianizzato.
# Format: code → (full_name_it, short_name, force_url|None)
COMP_OVERRIDES = {
    # Top 5 europei
    "BL1":  ("Bundesliga",            "BL1",  "https://upload.wikimedia.org/wikipedia/en/thumb/d/df/Bundesliga_logo_%282017%29.svg/200px-Bundesliga_logo_%282017%29.svg.png"),
    "BL2":  ("2. Bundesliga",         "2BL",  None),
    "BL3":  ("3. Liga",               "3LIG", None),
    "DFB":  ("DFB-Pokal",             "DFB",  None),
    "DFL":  ("DFL-Supercup",          "DFL",  None),
    "DFBJ": ("DFB-Pokal Junioren",    "DFBJ", None),
    "GB1":  ("Premier League",        "PL",   None),
    "GB2":  ("Championship",          "CHA",  None),
    "GB3":  ("League One",            "L1G",  None),
    "GB4":  ("League Two",            "L2G",  None),
    "FAC":  ("FA Cup",                "FA",   None),
    "FAYC": ("FA Youth Cup",          "FAY",  None),
    "FACS": ("Community Shield",      "CS",   None),
    "ES1":  ("La Liga",               "LL",   None),
    "ES2":  ("La Liga 2",             "LL2",  None),
    "ES3A": ("Primera RFEF Group 1",  "P1",   None),
    "ES3B": ("Primera RFEF Group 2",  "P2",   None),
    "ES3C": ("Tercera RFEF",          "T3",   None),
    "ES3D": ("Tercera RFEF",          "T3",   None),
    "ES3E": ("Tercera RFEF",          "T3",   None),
    "CDR":  ("Copa del Rey",          "CDR",  None),
    "FR1":  ("Ligue 1",               "L1",   None),
    "FR2":  ("Ligue 2",               "L2",   None),
    "FRC":  ("Coupe de France",       "CDF",  None),
    "L1":   ("Ligue 1",               "L1",   None),
    "L2":   ("Ligue 2",               "L2",   None),
    "L3":   ("National 1",            "N1",   None),
    "NL1":  ("Eredivisie",            "ERE",  None),
    "NL2":  ("Eerste Divisie",        "ED",   None),
    "NLC":  ("KNVB Beker",            "KNVB", None),
    "NLP":  ("KNVB Beker (giovanili)","NLP",  None),
    "PO1":  ("Liga Portugal Betclic", "LP1",  None),
    "PO2":  ("Liga Portugal 2",       "LP2",  None),
    "POCC": ("Taça de Portugal",      "TDP",  None),
    "PUSB": ("Liga Portugal Betclic","LP1",  None),
    # UEFA
    "CL":   ("UEFA Champions League",  "UCL",  None),
    "CLQ":  ("UCL Qualifying",         "UCLQ", None),
    "EL":   ("UEFA Europa League",     "UEL",  None),
    "ELQ":  ("UEL Qualifying",         "UELQ", None),
    "UCOL": ("UEFA Conference League", "UECL", None),
    "ECLQ": ("UECL Qualifying",        "UECLQ",None),
    "UEFA": ("UEFA Super Cup",         "USC",  None),
    "19YL": ("UEFA Youth League",      "UYL",  None),
    # Italia
    "IT1":  ("Serie A",                "SA",   None),
    "IT2":  ("Serie B",                "SB",   None),
    "IT3A": ("Serie C Girone A",       "C-A",  None),
    "IT3B": ("Serie C Girone B",       "C-B",  None),
    "IT3C": ("Serie C Girone C",       "C-C",  None),
    "IT3O": ("Serie C Coppa",          "C-CP", None),
    "IT3P": ("Serie C Playoff",        "C-PO", None),
    "CIT":  ("Coppa Italia",           "CIT",  None),
    "CITP": ("Coppa Italia Serie C",   "CITP", None),
    "SCI":  ("Supercoppa Italiana",    "SCI",  None),
    "SCIC": ("Supercoppa Serie C",     "SCC",  None),
    "SCIJ": ("Supercoppa Primavera",   "SCJ",  None),
    "ITPO": ("Italia Playoff",         "ITPO", None),
    "IJ1":  ("Primavera 1",            "P1",   None),
    "IJ2A": ("Primavera 2 A",          "P2A",  None),
    "IJ2B": ("Primavera 2 B",          "P2B",  None),
    "IJSC": ("Coppa Primavera",        "CP",   None),
    "ITJ1": ("Under 17 Italia",        "U17",  None),
    "ITJ2": ("Under 16 Italia",        "U16",  None),
    "ITJ3": ("Under 15 Italia",        "U15",  None),
    "ITJ4": ("Under 18 Italia",        "U18",  None),
    "ITJ5": ("Under 17 Coppa",         "U17C", None),
    "ITJ6": ("Under 18 Coppa",         "U18C", None),
    "ITJ7": ("Under 16 Coppa",         "U16C", None),
    "ITJE": ("Under Italia (group E)", "ITJE", None),
    "ITJF": ("Under Italia (group F)", "ITJF", None),
    "ITJP": ("Under Italia Playoff",   "ITJP", None),
    "IT18": ("Under 18 Italia",        "U18",  None),
    "ITC4": ("Coppa Italia Serie D",   "ITC4", None),
    # Polonia
    "PL1":  ("Ekstraklasa",            "EKS",  None),
    "PL2":  ("1 Liga (Polonia)",       "1L",   None),
    "PL2L": ("1 Liga Promotion",       "1LP",  None),
    "PL31": ("2 Liga Group 1",         "2L1",  None),
    "PL32": ("2 Liga Group 2",         "2L2",  None),
    "PL33": ("2 Liga Group 3",         "2L3",  None),
    "PL34": ("2 Liga Group 4",         "2L4",  None),
    "PLSC": ("Ekstraklasa Cup",        "EKSC", None),
    "PLIC": ("Polish Pro League Int Cup","PLIC", None),
    "PLZJ": ("Polish Junior League",   "PLZJ", None),
    "POPU": ("Polish Cup (Puchar)",    "PUC",  None),
    "POSB": ("Polish Lower Div",       "POSB", None),
    "BAPO": ("Polish Reg League",      "BAPO", None),
    "BAPL": ("Polish Reg League",      "BAPL", None),
    # Belgio
    "BE1":  ("Pro League",             "BE1",  None),
    "BE2":  ("Challenger Pro League",  "BE2",  None),
    "CCB":  ("Croky Cup",              "CCB",  None),
    # Italiane minori
    "IT4":  ("Serie D",                "SD",   None),
    "IT4A": ("Serie D Girone A",       "D-A",  None),
    "IT4B": ("Serie D Girone B",       "D-B",  None),
    "IT4C": ("Serie D Girone C",       "D-C",  None),
    "IT4D": ("Serie D Girone D",       "D-D",  None),
    "IT4E": ("Serie D Girone E",       "D-E",  None),
    "IT4F": ("Serie D Girone F",       "D-F",  None),
    "IT4G": ("Serie D Girone G",       "D-G",  None),
    "IT4H": ("Serie D Girone H",       "D-H",  None),
    "IT4I": ("Serie D Girone I",       "D-I",  None),
    "IT4P": ("Serie D Playoff",        "D-PO", None),
    # National TEAM (mostrate sempre con logo PID logo come default ora)
    "WMQ1": ("Qualificazioni Mondiali UEFA", "WMQ", None),
    "WMQ2": ("Qualificazioni Mondiali",     "WMQ", None),
    "WMQ3": ("Qualificazioni Mondiali",     "WMQ", None),
    "WMQ4": ("Qualificazioni Mondiali",     "WMQ", None),
    "WMQ5": ("Qualificazioni Mondiali",     "WMQ", None),
    "WMQ6": ("Qualificazioni Mondiali",     "WMQ", None),
    "EURO": ("UEFA Euro",                   "EU",  None),
    "EMQ":  ("Qualificazioni Euro",         "EMQ", None),
    "21EU": ("Under 21 Euro",               "U21", None),
    "U21Q": ("Under 21 Qualifying",         "U21Q",None),
    "19EU": ("Under 19 Euro",               "U19", None),
    "U19Q": ("Under 19 Qualifying",         "U19Q",None),
    "17EU": ("Under 17 Euro",               "U17", None),
    "U17Q": ("Under 17 Qualifying",         "U17Q",None),
    "20WC": ("Mondiali Under 20",           "U20W",None),
    "17WC": ("Mondiali Under 17",           "U17W",None),
    "WC":   ("Mondiali",                    "WC",  None),
    "FIWC": ("FIFA Confederations Cup",     "FCC", None),
    "UNLA": ("UEFA Nations League A",       "UNLA",None),
    "UNLB": ("UEFA Nations League B",       "UNLB",None),
    "FS":   ("Friendly",                    "FRD", None),
    "23AF": ("AFC U23 Asian Cup",           "AFC23",None),
    "23OF": ("OFC U23",                     "OFC23",None),
    "OLYM": ("Olimpiadi",                   "OLYM",None),
    "AGUC": ("Arabian Gulf Cup",            "AGUC",None),
    "GOCU": ("Gulf Cup of Nations",         "GOCU",None),
    "AFAC": ("AFC Asian Cup",               "AFAC",None),
    "ACQA": ("AFC Asian Cup Qualifying",    "ACQA",None),
    "ARCP": ("Arab Cup",                    "ARC", None),
}


def download(url: str, dest: Path) -> tuple[bool, int]:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200 or len(r.content) < 500:
            return False, len(r.content)
        dest.write_bytes(r.content)
        return True, len(r.content)
    except Exception as e:
        return False, 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Scarica TUTTI i codici trovati nei dati (incluso quelli con freq=1)")
    parser.add_argument("--min-freq", type=int, default=3)
    args = parser.parse_args()

    # Carica stats
    stats_path = Path("/tmp/stats.json")
    if not stats_path.exists():
        print("Scarico players_stats.json da R2…")
        r = requests.get(f"{R2_PUBLIC_URL}/players_stats.json", timeout=120)
        stats_path.write_bytes(r.content)
        print(f"  ✓ {len(r.content):,} bytes")
    stats = json.loads(stats_path.read_text(encoding="utf-8"))

    # Frequenza codici
    freq = Counter()
    for s in stats:
        cbc = s.get("career_by_competition", {}).get("club", {}) or {}
        cbn = s.get("career_by_competition", {}).get("national", {}) or {}
        for k in cbc: freq[k] += 1
        for k in cbn: freq[k] += 1

    # Codici da scaricare
    if args.all:
        targets = list(freq.keys())
    else:
        targets = [c for c, f in freq.items() if f >= args.min_freq]

    # Aggiungi tutti gli override anche se non frequenti (per garantire copertura sui top)
    for code in COMP_OVERRIDES:
        if code not in targets:
            targets.append(code)

    print(f"Target: {len(targets)} codici (freq >={args.min_freq} OR in COMP_OVERRIDES)")
    print()

    # Già presenti
    existing = {p.stem for p in COMPETITIONS_DIR.glob("*.png")}
    print(f"Già presenti: {len(existing)} loghi")
    print()

    new_downloaded = 0
    skipped_existing = 0
    failed = 0
    failed_codes = []

    for code in sorted(targets):
        dest = COMPETITIONS_DIR / f"{code}.png"
        if code in existing and dest.stat().st_size > 500:
            skipped_existing += 1
            continue

        # 1) Override URL (es. Bundesliga BL1 da Wikipedia)
        override = COMP_OVERRIDES.get(code, (None, None, None))
        if override[2]:
            ok, size = download(override[2], dest)
            if ok:
                print(f"  ✓ {code:<8} (override)         {size:>6}b")
                new_downloaded += 1
                continue

        # 2) CDN TM (3 path varianti)
        ok = False
        for pattern in TMSSL_PATTERNS:
            url = pattern.format(code=code.lower())
            ok, size = download(url, dest)
            if ok:
                print(f"  ✓ {code:<8} (TM CDN, freq={freq.get(code,0):>3}) {size:>6}b")
                new_downloaded += 1
                break

        if not ok:
            failed += 1
            failed_codes.append((code, freq.get(code, 0)))

        time.sleep(0.05)

    print()
    print("=" * 70)
    print(f"  ✓ Nuovi loghi scaricati: {new_downloaded}")
    print(f"  ↺ Già presenti, skippati: {skipped_existing}")
    print(f"  ❌ Falliti: {failed}")
    if failed_codes[:15]:
        print(f"\n  Top 15 falliti (potrebbero non avere logo TM CDN):")
        for c, f in sorted(failed_codes, key=lambda x: -x[1])[:15]:
            print(f"     {c:<8} freq={f}")
    print("=" * 70)

    print()
    print("Generazione COMP_LABEL aggiornato per app.js…")
    new_overrides = []
    for code in sorted(targets):
        dest = COMPETITIONS_DIR / f"{code}.png"
        if not dest.exists() or dest.stat().st_size < 500:
            continue
        info = COMP_OVERRIDES.get(code)
        if not info or not info[0]:
            continue
        full, short, _ = info
        new_overrides.append(f'  {code}: {{ short: "{short}", full: "{full}" }},')

    out = "// Auto-generated COMP_LABEL extension (genera con download_competition_logos.py)\n"
    out += "const COMP_LABEL_AUTO = {\n"
    out += "\n".join(new_overrides)
    out += "\n};"
    (DATA_DIR / "comp_label_auto.js").write_text(out, encoding="utf-8")
    print(f"  ✓ Salvato in data/comp_label_auto.js ({len(new_overrides)} entries)")

    return 0


if __name__ == "__main__":
    sys.exit(main())

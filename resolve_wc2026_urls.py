"""
resolve_wc2026_urls.py — Risolve i giocatori del Mondiale 2026 in URL Transfermarkt.

Legge data/wc2026_squads_raw.json (output di parse_wikipedia_squad.py) e per ogni
giocatore cerca su Transfermarkt via Schnellsuche, disambiguando con la DOB.

Strategia matching (in ordine):
  1) DOB esatta + nome contiene token → AUTO ACCEPT (match_method='dob_exact')
  2) DOB ±1 giorno + nome contiene token → AUTO ACCEPT (match_method='dob_tolerant')
     (gestisce errori dati timezone/Wikipedia vs TM)
  3) Singolo risultato Schnellsuche con nome esatto → AUTO ACCEPT
     (match_method='name_unique', usato quando TM non ha DOB nella search row)
  4) Nessun match affidabile → UNRESOLVED (CSV per revisione manuale)

Output:
  - urls_wc2026.txt          → input per `python3 add_players.py urls_wc2026.txt`
  - data/wc2026_unresolved.csv → giocatori non risolti, con candidati TM trovati
  - data/wc2026_squads_raw.json viene arricchito con tm_player_id/tm_profile_url/match_method

Uso:
  python3 resolve_wc2026_urls.py                          # tutti i giocatori
  python3 resolve_wc2026_urls.py --country France         # solo una nazionale
  python3 resolve_wc2026_urls.py --country "Bosnia and Herzegovina"
  python3 resolve_wc2026_urls.py --dry-run                # non scrive output
  python3 resolve_wc2026_urls.py --reresolve              # rifai matching anche per giocatori già risolti
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import quote_plus

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
import _bootstrap  # noqa: F401

from bs4 import BeautifulSoup

from scraper.config import DATA_DIR
from scraper.http_client import TransfermarktClient

SQUADS_FILE = DATA_DIR / "wc2026_squads_raw.json"
URLS_FILE = ROOT / "urls_wc2026.txt"
UNRESOLVED_FILE = DATA_DIR / "wc2026_unresolved.csv"

TM_SEARCH_URL = "https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?query={q}"


# ---------------------------------------------------------------------------
# Normalizzazione nomi (per match robusto)
# ---------------------------------------------------------------------------

def normalize_name(s: str) -> str:
    """
    Normalizza nome per matching: lower, no accenti, no punteggiatura.
    'Kylian Mbappé' → 'kylian mbappe', "N'Golo Kanté" → 'ngolo kante'.
    """
    if not s:
        return ""
    # Decompose Unicode, rimuovi diacritici
    nfkd = unicodedata.normalize("NFKD", s)
    no_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    # Lower + spazi normalizzati + rimuovi apostrofi/trattini
    no_accents = no_accents.lower()
    no_accents = re.sub(r"['\u2019\-]", "", no_accents)  # apostrofi vari, trattini
    no_accents = re.sub(r"[^\w\s]", " ", no_accents)
    no_accents = re.sub(r"\s+", " ", no_accents).strip()
    return no_accents


def name_tokens(s: str) -> set[str]:
    """Token set di un nome normalizzato. Ignora token <2 char."""
    return {t for t in normalize_name(s).split() if len(t) >= 2}


# ---------------------------------------------------------------------------
# Parsing pagina Schnellsuche
# ---------------------------------------------------------------------------

# Sulla pagina di Schnellsuche, la tabella "Players" (Spieler) ha colonne:
#   Player (foto+nome+link profilo) | Position | Age (calc) | Nat. | Club | Market Value
# La DOB NON è direttamente in tabella, ma "Age" è calcolata. Per ottenere DOB
# esatta occorre fetch del profilo. Strategia: prima identifica candidati per
# nome+età (Age è "33 (Aug 21, 2002)" o "23" a seconda della view), poi se DOB
# non compare in search-row scarichiamo il profilo del top candidate.

AGE_DATE_RE = re.compile(r"(?:Age:\s*)?(?:\d{1,2})\s*\((\w+\s+\d{1,2},\s*\d{4})\)")
SHORT_DATE_RE = re.compile(r"(\w+)\s+(\d{1,2}),?\s+(\d{4})")
MONTHS_SHORT = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
    "January": 1, "February": 2, "March": 3, "April": 4, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12,
}


def parse_short_date(text: str) -> str | None:
    """'Jul 3, 1995' / 'July 3, 1995' → '1995-07-03'."""
    if not text:
        return None
    m = SHORT_DATE_RE.search(text)
    if not m:
        return None
    month = MONTHS_SHORT.get(m.group(1))
    if not month:
        return None
    try:
        return dt.date(int(m.group(3)), month, int(m.group(2))).isoformat()
    except ValueError:
        return None


def parse_schnellsuche(html: str) -> list[dict]:
    """
    Estrae i candidati dalla pagina Schnellsuche.
    Per ogni player ritorna {name, tm_id, profile_url, position, age, nat, club}.
    DOB potrebbe non essere disponibile nella search row — verrà recuperata
    dal profilo separatamente se serve.
    """
    soup = BeautifulSoup(html, "lxml")
    candidates = []

    # Tabella "Players" (Spieler). Cerco le righe con link a /profil/spieler/
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        m = re.search(r"/([^/]+)/profil/spieler/(\d+)", href)
        if not m:
            continue
        tm_id = int(m.group(2))
        if any(c["tm_id"] == tm_id for c in candidates):
            continue  # dedup (TM mette il link più volte per la stessa riga)

        # Risali alla riga <tr> contenente questo link
        tr = a.find_parent("tr")
        if not tr:
            continue

        # Estrai testo cells per la riga
        cells = tr.find_all("td")
        cells_text = [c.get_text(" ", strip=True) for c in cells]

        # Il nome è nel link stesso (o nel titolo)
        name = a.get_text(strip=True) or a.get("title", "")
        if not name:
            continue

        # Cerca pattern "Age (Mon DD, YYYY)" in qualunque cella
        dob_iso = None
        for ct in cells_text:
            m_age = AGE_DATE_RE.search(ct)
            if m_age:
                dob_iso = parse_short_date(m_age.group(1))
                break

        # Position, Nat, Club: best-effort dai testi cella
        position = ""
        nat = ""
        club = ""
        # Layout tipico: [foto] [nome+pos] [age/dob] [nat/flag] [club] [valore]
        # I testi delle cells variano: prendiamo euristicamente
        for ct in cells_text:
            if not position and re.search(r"\b(?:Goalkeeper|Defender|Midfield|Forward|Centre-Back|Right-Back|Left-Back|Striker|Winger|Attack|Defence)\b", ct, re.I):
                position = ct
            elif not club and ct and len(ct) > 2 and not re.search(r"\d", ct[:5]):
                # club è una stringa text-only; questa euristica è grezza
                # ma serve solo per debug nel CSV unresolved
                if "k €" in ct.lower() or "m €" in ct.lower() or "€" in ct:
                    continue
                club = ct

        profile_url = "https://www.transfermarkt.com" + href.split("#")[0] if href.startswith("/") else href

        candidates.append({
            "name": name,
            "tm_id": tm_id,
            "profile_url": profile_url,
            "dob": dob_iso,
            "position": position,
            "club": club,
        })

    return candidates


# ---------------------------------------------------------------------------
# Recupero DOB da profilo (fallback se non in search row)
# ---------------------------------------------------------------------------

def _val_text_from_info_table(soup: BeautifulSoup, label: str) -> str | None:
    """
    Estrae il valore associato a un label nella info-table del profilo TM.
    Replica la logica di scraper/profiles.py: l'info-table ha righe tipo
      <span class="info-table__content info-table__content--regular">Date of birth/Age:</span>
      <span class="info-table__content info-table__content--bold">19/08/1991 (34)</span>
    """
    # Cerca lo span/elemento il cui testo è il label, poi prendi il successivo
    for el in soup.find_all(["span", "th", "td"]):
        text = el.get_text(" ", strip=True).rstrip(":").strip()
        if text.lower() == label.lower():
            # Prendi il successivo elemento con testo
            nxt = el.find_next_sibling()
            if nxt:
                val = nxt.get_text(" ", strip=True)
                if val:
                    return val
            # Fallback: prendi l'elemento padre e cerca il prossimo span/td
            parent = el.parent
            if parent:
                for sib in el.find_all_next(["span", "td"], limit=3):
                    val = sib.get_text(" ", strip=True)
                    if val and val.lower() != label.lower() and not val.startswith(label):
                        return val
    return None


def fetch_dob_from_profile(client: TransfermarktClient, profile_url: str) -> str | None:
    """
    Scarica il profilo TM e estrae la DOB dalla info-table 'Date of birth/Age'.
    Formato TM: '19/08/1991 (34)' → '1991-08-19'.
    """
    try:
        html = client.get_html(profile_url)
    except Exception as e:
        print(f"      [warn] fetch profilo fallito: {e}")
        return None
    soup = BeautifulSoup(html, "lxml")
    val = _val_text_from_info_table(soup, "Date of birth/Age")
    if not val:
        # Fallback: cerca pattern DD/MM/YYYY in tutto il testo della pagina (più rischioso)
        text = soup.get_text(" ", strip=True)
        m = re.search(r"Date of birth[^:]*[:\s]+(\d{1,2})/(\d{1,2})/(\d{4})", text)
        if m:
            try:
                return dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat()
            except ValueError:
                return None
        return None
    # Parse 'DD/MM/YYYY (AGE)'
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", val)
    if not m:
        return None
    try:
        return dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat()
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Matching logic
# ---------------------------------------------------------------------------

def days_diff(a: str, b: str) -> int | None:
    try:
        da = dt.date.fromisoformat(a)
        db = dt.date.fromisoformat(b)
        return abs((da - db).days)
    except (ValueError, TypeError):
        return None


def match_player(client: TransfermarktClient, player: dict, *,
                 fetch_dob: bool = True,
                 validate_unique: bool = False) -> tuple[dict | None, str, list[dict]]:
    """
    Cerca su TM il giocatore e ritorna (best_candidate, method, all_candidates).
    method ∈ {'dob_exact', 'dob_tolerant', 'name_unique', 'unresolved'}.
    Se validate_unique=True, fa fetch profilo anche per name_unique e conferma
    che la DOB matchi (downgrade a dob_exact, o promote a unresolved se mismatch).
    """
    name = player.get("name", "")
    target_dob = player.get("dob")
    if not name:
        return (None, "unresolved", [])

    # Schnellsuche
    url = TM_SEARCH_URL.format(q=quote_plus(name))
    try:
        html = client.get_html(url)
    except Exception as e:
        print(f"      [err] Schnellsuche failed: {e}")
        return (None, "unresolved", [])

    candidates = parse_schnellsuche(html)
    if not candidates:
        return (None, "unresolved", [])

    target_tokens = name_tokens(name)

    # Filtra candidati per token-overlap minimo
    min_overlap = min(len(target_tokens), 2)
    name_matches = []
    for c in candidates:
        c_tokens = name_tokens(c["name"])
        overlap = len(target_tokens & c_tokens)
        if overlap >= min_overlap:
            c["_name_overlap"] = overlap
            name_matches.append(c)

    if not name_matches:
        return (None, "unresolved", candidates)

    # Pass 1: DOB exact match (su candidati che hanno già DOB nella search row)
    if target_dob:
        for c in name_matches:
            if c.get("dob") == target_dob:
                return (c, "dob_exact", candidates)

    # Pass 2: fetch DOB dal profilo se manca in search row, poi confronta
    if target_dob and fetch_dob:
        for c in name_matches[:5]:
            if c.get("dob"):
                continue
            dob_from_profile = fetch_dob_from_profile(client, c["profile_url"])
            if dob_from_profile:
                c["dob"] = dob_from_profile
                if dob_from_profile == target_dob:
                    return (c, "dob_exact", candidates)

    # Pass 3: DOB tolerant (±1 giorno)
    if target_dob:
        for c in name_matches:
            if c.get("dob"):
                diff = days_diff(c["dob"], target_dob)
                if diff is not None and diff <= 1:
                    return (c, "dob_tolerant", candidates)

    # Pass 4: nome esatto normalizzato + un solo candidato
    target_norm = normalize_name(name)
    exact_name_matches = [c for c in name_matches if normalize_name(c["name"]) == target_norm]
    if len(exact_name_matches) == 1:
        cand = exact_name_matches[0]
        # Paranoia mode: valida DOB con profile fetch anche per name_unique
        if validate_unique and target_dob:
            if not cand.get("dob"):
                cand["dob"] = fetch_dob_from_profile(client, cand["profile_url"])
            if cand.get("dob") == target_dob:
                return (cand, "dob_exact", candidates)
            if cand.get("dob"):
                diff = days_diff(cand["dob"], target_dob)
                if diff is not None and diff <= 1:
                    return (cand, "dob_tolerant", candidates)
            # DOB mismatch: rifiuto il match per sicurezza
            return (None, "unresolved", candidates)
        return (cand, "name_unique", candidates)

    # Pass 5 (rescue): se ci sono pochi candidati totali (<=3) e abbiamo target DOB,
    # prova fetch profilo per TUTTI anche se il nome ha similarity bassa.
    # Gestisce casi di translitterazione (Hashim vs Hashem, etc).
    if target_dob and fetch_dob and 0 < len(candidates) <= 3:
        for c in candidates:
            if c.get("dob") is None:
                c["dob"] = fetch_dob_from_profile(client, c["profile_url"])
            if c.get("dob") == target_dob:
                return (c, "dob_exact", candidates)
            if c.get("dob"):
                diff = days_diff(c["dob"], target_dob)
                if diff is not None and diff <= 1:
                    return (c, "dob_tolerant", candidates)

    return (None, "unresolved", candidates)


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------

def load_squads() -> dict:
    if not SQUADS_FILE.exists():
        print(f"❌ {SQUADS_FILE} non trovato. Lancia prima `parse_wikipedia_squad.py`.", file=sys.stderr)
        sys.exit(1)
    return json.loads(SQUADS_FILE.read_text(encoding="utf-8"))


def save_squads(data: dict) -> None:
    SQUADS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_overrides() -> dict:
    """
    Carica data/wc2026_overrides.json se esiste.
    Struttura: {"Country|Player Name": tm_player_id, ...}
    Esempio:
      {
        "Iraq|Frans Putros": 217073,
        "Iraq|Ahmed Maknzi": 945000
      }
    """
    overrides_file = DATA_DIR / "wc2026_overrides.json"
    if not overrides_file.exists():
        return {}
    return json.loads(overrides_file.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Risolvi nomi WC2026 → URL Transfermarkt")
    ap.add_argument("--country", help="Risolvi solo una nazionale (es. 'France')")
    ap.add_argument("--reresolve", action="store_true", help="Rifai matching anche per giocatori già risolti")
    ap.add_argument("--no-fetch-dob", action="store_true", help="Non scaricare profilo TM per DOB mancante (più veloce, più unresolved)")
    ap.add_argument("--validate-all", action="store_true", help="Valida DOB via profile fetch ANCHE per name_unique (paranoia mode, più lento ma evita falsi positivi)")
    ap.add_argument("--dry-run", action="store_true", help="Non scrivere file di output")
    args = ap.parse_args()

    squads = load_squads()

    if args.country:
        if args.country not in squads:
            print(f"❌ Nazionale '{args.country}' non in {SQUADS_FILE}. Disponibili: {list(squads.keys())}", file=sys.stderr)
            return 1
        target_countries = [args.country]
    else:
        target_countries = list(squads.keys())

    client = TransfermarktClient()
    overrides = load_overrides()
    if overrides:
        print(f"📋 Caricati {len(overrides)} override manuali da data/wc2026_overrides.json\n")
    resolved_urls: set[str] = set()
    unresolved_rows: list[dict] = []
    stats = {"dob_exact": 0, "dob_tolerant": 0, "name_unique": 0, "unresolved": 0, "already_resolved": 0}

    started = dt.datetime.now()
    total_players = sum(len(squads[c]["players"]) for c in target_countries)
    print(f"Risoluzione TM URL per {total_players} giocatori in {len(target_countries)} nazionali\n")

    idx = 0
    for country in target_countries:
        squad = squads[country]
        print(f"\n=== {country} ({len(squad['players'])} giocatori) ===")
        for p in squad["players"]:
            idx += 1
            name = p.get("name", "?")
            dob = p.get("dob", "?")

            # Già risolto?
            if not args.reresolve and p.get("tm_player_id"):
                resolved_urls.add(p["tm_profile_url"])
                stats["already_resolved"] += 1
                print(f"  [{idx:>3}/{total_players}] ✓ già risolto: {name} → tm_id={p['tm_player_id']}")
                continue

            # Override manuale?
            override_key = f"{country}|{name}"
            if override_key in overrides:
                tm_id = overrides[override_key]
                profile_url = f"https://www.transfermarkt.com/-/profil/spieler/{tm_id}"
                p["tm_player_id"] = tm_id
                p["tm_profile_url"] = profile_url
                p["match_method"] = "manual_override"
                resolved_urls.add(profile_url)
                stats.setdefault("manual_override", 0)
                stats["manual_override"] += 1
                print(f"  [{idx:>3}/{total_players}] ✓ override manuale: {name} → tm_id={tm_id}")
                continue

            print(f"  [{idx:>3}/{total_players}] {name} (DOB {dob})...", end=" ", flush=True)

            best, method, all_cands = match_player(
                client, p,
                fetch_dob=not args.no_fetch_dob,
                validate_unique=args.validate_all,
            )

            if best:
                p["tm_player_id"] = best["tm_id"]
                p["tm_profile_url"] = best["profile_url"]
                p["match_method"] = method
                resolved_urls.add(best["profile_url"])
                stats[method] += 1
                marker = "✓" if method == "dob_exact" else "~"
                print(f"{marker} {method} → tm_id={best['tm_id']} ({best['name']})")
            else:
                p["tm_player_id"] = None
                p["tm_profile_url"] = None
                p["match_method"] = "unresolved"
                stats["unresolved"] += 1
                cand_preview = " | ".join(f"{c['name']} (tm_id={c['tm_id']}, dob={c.get('dob') or '?'})" for c in all_cands[:3])
                print(f"❌ unresolved ({len(all_cands)} cand: {cand_preview[:120]})")
                unresolved_rows.append({
                    "country": country,
                    "name": name,
                    "dob": dob,
                    "pos": p.get("pos", ""),
                    "club": p.get("club", ""),
                    "num_candidates": len(all_cands),
                    "candidates": " | ".join(
                        f"{c['name']}|tm_id={c['tm_id']}|dob={c.get('dob') or '?'}|{c['profile_url']}"
                        for c in all_cands[:5]
                    ),
                })

    elapsed = (dt.datetime.now() - started).total_seconds()

    # Report finale
    print("\n" + "=" * 70)
    print(f"  Tempo:                {elapsed:.0f}s")
    print(f"  Già risolti:          {stats['already_resolved']}")
    if stats.get('manual_override'):
        print(f"  Manual override:      {stats['manual_override']}")
    print(f"  DOB exact match:      {stats['dob_exact']}")
    print(f"  DOB tolerant (±1d):   {stats['dob_tolerant']}")
    print(f"  Name unique:          {stats['name_unique']}")
    print(f"  ❌ Unresolved:         {stats['unresolved']}")
    total_resolved = (stats['already_resolved'] + stats.get('manual_override', 0)
                      + stats['dob_exact'] + stats['dob_tolerant'] + stats['name_unique'])
    print(f"  TOTALE risolti:       {total_resolved}/{total_players} ({total_resolved*100//max(total_players,1)}%)")
    print("=" * 70)

    if args.dry_run:
        print("\n[dry-run] non scrivo file.")
        return 0

    # Salva JSON arricchito
    save_squads(squads)
    print(f"\n✓ {SQUADS_FILE} aggiornato con tm_player_id/tm_profile_url/match_method")

    # Scrive urls_wc2026.txt
    if resolved_urls:
        URLS_FILE.write_text("\n".join(sorted(resolved_urls)) + "\n", encoding="utf-8")
        print(f"✓ {URLS_FILE} scritto ({len(resolved_urls)} URL unici)")
    else:
        print(f"⚠️  Nessun URL risolto, {URLS_FILE} non scritto")

    # Scrive CSV unresolved
    if unresolved_rows:
        with UNRESOLVED_FILE.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["country", "name", "dob", "pos", "club", "num_candidates", "candidates"])
            writer.writeheader()
            writer.writerows(unresolved_rows)
        print(f"⚠️  {UNRESOLVED_FILE} scritto ({len(unresolved_rows)} unresolved da revisionare manualmente)")

    print("\n→ Prossimo step:")
    print(f"   python3 add_players.py {URLS_FILE.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

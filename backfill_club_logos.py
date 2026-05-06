"""
backfill_club_logos.py — Arricchisce clubs.json con sortitoutsi_team_id e
sortitoutsi_logo_url per i club Primavera (IJ1) e i club polacchi (PL1/PL2).

Strategia:
  - **IJ1 (Primavera)**: SortItOutSi non ha le squadre Primavera dedicate.
    Riusiamo il sortitoutsi_team_id del club di prima squadra (Serie A/B).
    Esempio: "Inter Milan Primavera" → riusa l'id di "Inter Milan".

  - **PL1 (Ekstraklasa) e PL2 (1 Liga)**: scrappiamo le pagine competizione
    SortItOutSi e mappiamo per nome con i club nei JSON.

Effetti:
  - Aggiorna `data/clubs.json` (campi sortitoutsi_team_id, sortitoutsi_logo_url,
    league_name)
  - Aggiorna anche `data/pl1_clubs.json`, `data/pl2_clubs.json`,
    `data/ij1_clubs.json`
  - Scarica i loghi in `data/photos/clubs_sots/{tm_club_id}.png` e popola
    `sortitoutsi_logo_local` se il download riesce.

Uso:
    python3 backfill_club_logos.py [--dry-run]
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
DATA_DIR = ROOT / "data"
CLUBS_FILE = DATA_DIR / "clubs.json"
PL1_FILE = DATA_DIR / "pl1_clubs.json"
PL2_FILE = DATA_DIR / "pl2_clubs.json"
IJ1_FILE = DATA_DIR / "ij1_clubs.json"
LOGOS_DIR = DATA_DIR / "photos" / "clubs_sots"

# Alias manuali per club che SortItOutSi e Transfermarkt nominano in modo diverso,
# e per club non presenti nella pagina competizione (cercati direttamente per ID).
SOTS_MANUAL_OVERRIDES = {
    # PL2 — non presenti nella pagina competizione FM26 ma esistenti su SortItOutSi
    "Wieczysta Krakow": 2000028546,    # /team/2000028546/wieczysta-krakow
    # PL2 — varianti di nome
    "LKS Lodz": 1454,                  # SortItOutSi: lodzki-klub-sportowy
    "Polonia Warsaw": 1300879,         # SortItOutSi: polonia-warszawa
    # Pogon Grodzisk Mazowiecki: NON presente su SortItOutSi FM26 (promosso di recente)
    # → resta senza logo, mostrerà l'iniziale. Aggiungere a mano se in futuro
    # SortItOutSi lo include.
}
SOTS_COMPETITIONS = {
    "PL1": {
        "url": "https://sortitoutsi.net/football-manager-2026/competition/129558/pko-bank-polski-ekstraklasa",
        "league_name": "Ekstraklasa",
    },
    "PL2": {
        "url": "https://sortitoutsi.net/football-manager-2026/competition/129559/polish-first-division",
        "league_name": "1 Liga",
    },
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
}

LOGO_URL_TEMPLATE = "https://sortitoutsi.b-cdn.net/uploads/team/{sots_id}.png"


def _norm(s: str) -> str:
    """Normalizza un nome club per matching tollerante."""
    if not s:
        return ""
    # Mapping espliciti per lettere che NFKD non scompone (ł/Ł non sono accenti combinanti)
    POLISH_MAP = str.maketrans({
        "ł": "l", "Ł": "L",
        "ø": "o", "Ø": "O",
        "đ": "d", "Đ": "D",
        "ß": "s",
    })
    s = s.translate(POLISH_MAP)
    nfkd = unicodedata.normalize("NFKD", s)
    no_acc = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    s = re.sub(r"[^a-zA-Z\s]", " ", no_acc).lower().strip()
    DROP_TOKENS = {
        "ac", "fc", "ssc", "ss", "us", "uc", "acf", "afc",
        "calcio", "club", "primavera", "sporting", "delfino",
        "u19", "u20", "u21", "u23",
        "kghm", "pko", "bp", "betclic",  # sponsor / prefissi non semantici
    }
    tokens = [t for t in s.split() if t not in DROP_TOKENS and len(t) > 1]
    return " ".join(tokens)


def fetch_competition_teams(url: str) -> list[dict]:
    """Estrae lista {sots_team_id, name, slug} dalla pagina competizione SortItOutSi.
    Usa requests, con fallback su curl se requests viene bloccato (403)."""
    print(f"  GET {url}")
    html = None
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        html = r.text
    except requests.HTTPError as e:
        if r.status_code == 403:
            print(f"  [warn] 403 da requests, ritento con curl…")
            html = _fetch_via_curl(url)
        else:
            raise
    if not html:
        raise RuntimeError("nessun contenuto HTML restituito")
    soup = BeautifulSoup(html, "lxml")
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


def _fetch_via_curl(url: str) -> str | None:
    """Fallback: usa curl come sottoprocesso quando requests viene bloccato."""
    import subprocess
    cmd = [
        "curl", "-sSL",
        "-H", f"User-Agent: {HEADERS['User-Agent']}",
        "-H", f"Accept: {HEADERS['Accept']}",
        "-H", f"Accept-Language: {HEADERS['Accept-Language']}",
        "--compressed",
        "-m", "20",
        url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout:
            return result.stdout
        print(f"  [error] curl exit {result.returncode}: {result.stderr[:200]}")
    except FileNotFoundError:
        print("  [error] curl non installato — installa curl o usa una versione di requests più recente")
    except Exception as e:
        print(f"  [error] curl failed: {e}")
    return None


def download_logo(sots_id: int, tm_club_id: int, dry_run: bool = False) -> bool:
    """Scarica il logo SortItOutSi e lo salva in data/photos/clubs_sots/{tm_club_id}.png.
    Ritorna True se scaricato/già presente."""
    out_path = LOGOS_DIR / f"{tm_club_id}.png"
    if out_path.exists() and out_path.stat().st_size > 200:
        return True
    if dry_run:
        return False
    LOGOS_DIR.mkdir(parents=True, exist_ok=True)
    url = LOGO_URL_TEMPLATE.format(sots_id=sots_id)
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        if len(r.content) < 200:
            # Placeholder / GIF 1x1 — scartato
            return False
        out_path.write_bytes(r.content)
        return True
    except Exception as e:
        print(f"    [warn] download {sots_id} failed: {e}")
        return False


def update_club(club: dict, sots_id: int, league_name: str | None, dry_run: bool) -> bool:
    """Aggiorna i campi SortItOutSi su un dict club. Ritorna True se ha modificato qualcosa."""
    changed = False
    if club.get("sortitoutsi_team_id") != sots_id:
        club["sortitoutsi_team_id"] = sots_id
        club["sortitoutsi_logo_url"] = LOGO_URL_TEMPLATE.format(sots_id=sots_id)
        changed = True
    if league_name and club.get("league_name") != league_name:
        club["league_name"] = league_name
        changed = True
    # Download logo
    tm_id = club.get("tm_club_id")
    if tm_id and download_logo(sots_id, tm_id, dry_run=dry_run):
        local_path = f"photos/clubs_sots/{tm_id}.png"
        if club.get("sortitoutsi_logo_local") != local_path:
            club["sortitoutsi_logo_local"] = local_path
            changed = True
    return changed


def backfill_primavera(clubs: list[dict], dry_run: bool) -> int:
    """Per ogni club IJ1, riusa il sortitoutsi_team_id del club di prima squadra
    (Serie A/B) di cui è la Primavera."""
    print("\n=== IJ1 (Primavera) — riuso da prima squadra ===")
    ij1 = [c for c in clubs if c.get("league_id") == "IJ1"]
    senior_by_norm = {
        _norm(c["name"]): c
        for c in clubs
        if c.get("league_id") in ("IT1", "IT2") and c.get("sortitoutsi_team_id")
    }
    n_updated = 0
    for c in ij1:
        # Rimuovi suffisso Primavera/U19/U20 e normalizza
        base_name = c["name"]
        for suffix in (" Primavera", " U19", " U20", " U21"):
            base_name = base_name.replace(suffix, "")
        key = _norm(base_name)
        senior = senior_by_norm.get(key)
        if not senior:
            # Match per substring
            for sk, sc in senior_by_norm.items():
                if key and (key in sk or sk in key):
                    senior = sc
                    break
        if not senior:
            print(f"  [no-match] {c['name']:<30}  (norm: {key!r})")
            continue
        sots_id = senior["sortitoutsi_team_id"]
        if update_club(c, sots_id, league_name="Primavera 1", dry_run=dry_run):
            n_updated += 1
            print(f"  + {c['name']:<30}  ←  {senior['name']:<25}  sots={sots_id}")
    print(f"  totale aggiornati: {n_updated}/{len(ij1)}")
    return n_updated


def backfill_polonia(clubs: list[dict], dry_run: bool) -> int:
    """Per PL1/PL2, scrappa SortItOutSi e fa match per nome normalizzato."""
    n_updated = 0
    for league_id, info in SOTS_COMPETITIONS.items():
        print(f"\n=== {league_id} ({info['league_name']}) — scrape SortItOutSi ===")
        try:
            teams = fetch_competition_teams(info["url"])
        except Exception as e:
            print(f"  [error] fetch failed: {e}")
            continue
        print(f"  teams trovati su SortItOutSi: {len(teams)}")
        teams_by_norm: dict[str, dict] = {}
        for t in teams:
            teams_by_norm[_norm(t["name"])] = t

        league_clubs = [c for c in clubs if c.get("league_id") == league_id]
        print(f"  club nel DB per {league_id}: {len(league_clubs)}")
        league_updated = 0
        for c in league_clubs:
            key = _norm(c["name"])
            t = teams_by_norm.get(key)
            if not t:
                # Match per substring (in entrambe le direzioni)
                for tk, tt in teams_by_norm.items():
                    if key and (key in tk or tk in key):
                        t = tt
                        break
            sots_id = t["sots_team_id"] if t else SOTS_MANUAL_OVERRIDES.get(c["name"])
            sots_name = t["name"] if t else (
                f"manual override id={sots_id}" if sots_id else None
            )
            if not sots_id:
                print(f"  [no-match] {c['name']:<30}  (norm: {key!r})")
                continue
            if update_club(c, sots_id, league_name=info["league_name"], dry_run=dry_run):
                n_updated += 1
                league_updated += 1
                print(f"  + {c['name']:<30}  ←  sots={sots_id}  ({sots_name!r})")
            time.sleep(0.05)  # Rate limit gentile sul download loghi
        print(f"  {league_id} aggiornati: {league_updated}/{len(league_clubs)}")
    return n_updated


def sync_individual_files(clubs: list[dict], dry_run: bool) -> None:
    """Sincronizza i campi sortitoutsi_* anche su pl1_clubs.json, pl2_clubs.json,
    ij1_clubs.json per consistenza."""
    individual = {
        "PL1": PL1_FILE,
        "PL2": PL2_FILE,
        "IJ1": IJ1_FILE,
    }
    by_id = {c["tm_club_id"]: c for c in clubs}
    for league_id, path in individual.items():
        if not path.exists():
            continue
        league_clubs = json.loads(path.read_text(encoding="utf-8"))
        n_synced = 0
        for c in league_clubs:
            master = by_id.get(c.get("tm_club_id"))
            if not master:
                continue
            for field in ("sortitoutsi_team_id", "sortitoutsi_logo_url",
                          "sortitoutsi_logo_local", "league_name"):
                if master.get(field) is not None and c.get(field) != master.get(field):
                    c[field] = master[field]
                    n_synced += 1
        if n_synced and not dry_run:
            path.write_text(
                json.dumps(league_clubs, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            print(f"  {path.name}: {n_synced} field aggiornati")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="non scrive su disco, mostra solo le modifiche")
    args = parser.parse_args()

    if not CLUBS_FILE.exists():
        print(f"❌ {CLUBS_FILE} non trovato. Lancia dallo script dalla root del progetto pid.")
        return 1

    clubs = json.loads(CLUBS_FILE.read_text(encoding="utf-8"))
    print(f"clubs.json: {len(clubs)} club totali")

    n1 = backfill_primavera(clubs, dry_run=args.dry_run)
    n2 = backfill_polonia(clubs, dry_run=args.dry_run)

    print(f"\nTotale aggiornati: {n1 + n2}")

    if args.dry_run:
        print("\n[dry-run] nessuna modifica scritta")
        return 0

    # Salva clubs.json
    CLUBS_FILE.write_text(
        json.dumps(clubs, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\n✓ {CLUBS_FILE.name} salvato")

    # Sincronizza i file individuali
    print("\n=== sync ij1_clubs.json / pl1_clubs.json / pl2_clubs.json ===")
    sync_individual_files(clubs, dry_run=False)

    return 0


if __name__ == "__main__":
    sys.exit(main())

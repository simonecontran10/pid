"""
resolve_wc2026_from_squad.py — Resolver alternativo per nazionali con nomi
non-latini (Corea, Iran, Arabia Saudita, Giappone, ecc.) dove la Schnellsuche
per nome di resolve_wc2026_urls.py fallisce per romanizzazione/ordine nome.

Approccio: invece di cercare ogni giocatore per nome, scarica la pagina rosa
TM della nazionale (table.items con 26 righe), estrae (tm_id, dob) per tutti,
e fa match per DOB con i giocatori Wikipedia gia' parsati in
data/wc2026_squads_raw.json per quella nazionale.

Vantaggio: la DOB e' un identificatore forte e indipendente dalla
romanizzazione del nome. 26 giocatori, 26 DOB nella pagina rosa, match 1:1.

Uso:
    python3 resolve_wc2026_from_squad.py "South Korea" "https://www.transfermarkt.com/south-korea/kader/verein/3589/plus/1/galerie/0?saison_id=2026"
    python3 resolve_wc2026_from_squad.py "South Korea" <URL> --dry-run

Dopo il run, rigenerare urls_wc2026.txt totale come al solito:
    python3 -c "import json; d=json.load(open('data/wc2026_squads_raw.json')); \
        urls=sorted({p['tm_profile_url'] for v in d.values() for p in v['players'] if p.get('tm_profile_url')}); \
        open('urls_wc2026.txt','w').write(chr(10).join(urls)+chr(10)); print(len(urls))"
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from bs4 import BeautifulSoup

from scraper.http_client import TransfermarktClient

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
SQUADS_FILE = DATA_DIR / "wc2026_squads_raw.json"

TM_BASE = "https://www.transfermarkt.com"


# ---------------------------------------------------------------------------
# Parsing pagina rosa TM nazionale
# ---------------------------------------------------------------------------

def parse_tm_squad_page(html: str) -> list[dict]:
    """
    Estrae [(tm_id, name_tm, dob_iso, shirt, role), ...] dalla table.items.

    Struttura (verificata su South Korea, 15 mag 2026):
      cell[0]  numero maglia
      cell[3]  nome (formato TM)
      cell[4]  ruolo
      cell[5]  DOB 'DD/MM/YYYY (age)'
      link href: /slug/profil/spieler/{tm_id}
    """
    soup = BeautifulSoup(html, "lxml")
    table = soup.select_one("table.items")
    if not table:
        return []

    out: list[dict] = []
    seen_ids: set[int] = set()

    for tr in table.select("tbody > tr"):
        link = tr.select_one("a[href*='/profil/spieler/']")
        if not link:
            continue
        href = link.get("href", "")
        m = re.search(r"/spieler/(\d+)", href)
        if not m:
            continue
        tm_id = int(m.group(1))
        if tm_id in seen_ids:
            continue  # foto + nome puntano allo stesso player: dedup

        cells = tr.find_all("td")
        if len(cells) < 6:
            continue

        name_tm = cells[3].get_text(" ", strip=True) if len(cells) > 3 else link.get_text(strip=True)
        role = cells[4].get_text(" ", strip=True) if len(cells) > 4 else ""
        dob_raw = cells[5].get_text(" ", strip=True) if len(cells) > 5 else ""
        shirt_raw = cells[0].get_text(" ", strip=True) if cells else ""

        dob_iso = None
        dm = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", dob_raw)
        if dm:
            try:
                dob_iso = dt.date(int(dm.group(3)), int(dm.group(2)), int(dm.group(1))).isoformat()
            except ValueError:
                dob_iso = None

        shirt = None
        if shirt_raw.isdigit():
            shirt = int(shirt_raw)

        seen_ids.add(tm_id)
        out.append({
            "tm_id": tm_id,
            "name_tm": name_tm,
            "dob": dob_iso,
            "shirt": shirt,
            "role": role,
            "profile_url": f"{TM_BASE}{href.split('?')[0]}",
        })

    return out


# ---------------------------------------------------------------------------
# Match per DOB
# ---------------------------------------------------------------------------

def _norm(s: str) -> str:
    if not s:
        return ""
    nfkd = unicodedata.normalize("NFKD", s)
    no_acc = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", no_acc.lower()).strip()


def _name_tokens(s: str) -> set[str]:
    return {t for t in _norm(s).split() if len(t) >= 2}


def match_by_dob(wiki_players: list[dict], tm_players: list[dict]) -> tuple[int, list[str]]:
    """
    Per ogni player Wikipedia, trova il TM con la stessa DOB.
    Se piu' TM hanno la stessa DOB, disambigua per overlap nome (token).
    Ritorna (n_matched, warnings).
    """
    warnings: list[str] = []

    # Indice TM per DOB
    tm_by_dob: dict[str, list[dict]] = {}
    for t in tm_players:
        if t["dob"]:
            tm_by_dob.setdefault(t["dob"], []).append(t)

    def _dob_pm1(iso: str) -> list[str]:
        """Ritorna [iso-1, iso, iso+1] per tolleranza ±1 giorno."""
        try:
            d = dt.date.fromisoformat(iso)
        except (ValueError, TypeError):
            return [iso]
        return [
            (d - dt.timedelta(days=1)).isoformat(),
            iso,
            (d + dt.timedelta(days=1)).isoformat(),
        ]

    used_tm_ids: set[int] = set()
    matched = 0
    for wp in wiki_players:
        wdob = wp.get("dob")
        if not wdob:
            warnings.append(f"  ⚠️  {wp.get('name')}: nessuna DOB Wikipedia, skip")
            continue

        cands = tm_by_dob.get(wdob, [])
        if not cands:
            # Fallback: prova ±1 giorno (timezone / errori dati tra fonti)
            for alt in _dob_pm1(wdob):
                if alt == wdob:
                    continue
                alt_cands = tm_by_dob.get(alt, [])
                if alt_cands:
                    cands = alt_cands
                    warnings.append(f"  ~ {wp.get('name')}: match DOB tolerant ±1g ({wdob} ≈ {alt})")
                    break
        if not cands:
            warnings.append(f"  ❌ {wp.get('name')} (DOB {wdob}): nessun TM con questa DOB (±1g incluso)")
            continue

        if len(cands) == 1:
            chosen = cands[0]
        else:
            # Piu' candidati stessa DOB: disambigua per overlap nome
            wtok = _name_tokens(wp.get("name", ""))
            best = None
            best_ov = -1
            for c in cands:
                ov = len(wtok & _name_tokens(c["name_tm"]))
                if ov > best_ov:
                    best_ov = ov
                    best = c
            chosen = best
            warnings.append(
                f"  ~ {wp.get('name')} (DOB {wdob}): {len(cands)} TM stessa DOB, "
                f"scelto {chosen['name_tm']} (overlap nome {best_ov})"
            )

        wp["tm_player_id"] = chosen["tm_id"]
        wp["tm_profile_url"] = chosen["profile_url"]
        wp["match_method"] = "tm_squad_dob"
        used_tm_ids.add(chosen["tm_id"])
        matched += 1

    # Report dei TM nella rosa NON usati: utili per override manuale dei mismatch
    unused = [t for t in tm_players if t["tm_id"] not in used_tm_ids]
    if unused:
        warnings.append("")
        warnings.append(f"  --- {len(unused)} giocatori TM in rosa NON matchati (per override manuale) ---")
        for t in unused:
            warnings.append(
                f"    TM: {t['name_tm']:<28} DOB={t['dob']} id={t['tm_id']} "
                f"{t['profile_url']}"
            )

    return matched, warnings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("country", help="Nome nazionale esatto come in wc2026_squads_raw.json (es. 'South Korea')")
    ap.add_argument("squad_url", help="URL pagina rosa TM (es. https://www.transfermarkt.com/south-korea/kader/verein/3589/...)")
    ap.add_argument("--dry-run", action="store_true", help="Non salva, mostra solo il risultato")
    args = ap.parse_args()

    if not SQUADS_FILE.exists():
        print(f"❌ {SQUADS_FILE} non esiste. Lancia prima parse_wikipedia_squad.py", file=sys.stderr)
        return 1

    squads = json.loads(SQUADS_FILE.read_text(encoding="utf-8"))
    if args.country not in squads:
        print(f"❌ '{args.country}' non in wc2026_squads_raw.json. Disponibili: {sorted(squads.keys())}", file=sys.stderr)
        return 1

    wiki_players = squads[args.country].get("players", [])
    print(f"Nazionale: {args.country} — {len(wiki_players)} giocatori Wikipedia\n")

    client = TransfermarktClient()
    print(f"Fetch rosa TM: {args.squad_url}")
    try:
        html = client.get_html(args.squad_url)
    except Exception as e:
        print(f"❌ Fetch fallito: {e}", file=sys.stderr)
        return 1

    tm_players = parse_tm_squad_page(html)
    print(f"Estratti {len(tm_players)} giocatori dalla pagina rosa TM\n")

    if not tm_players:
        print("❌ Nessun giocatore estratto. La struttura HTML potrebbe essere cambiata.", file=sys.stderr)
        return 1

    matched, warnings = match_by_dob(wiki_players, tm_players)

    for w in warnings:
        print(w)

    print(f"\n{'='*70}")
    print(f"  Match per DOB: {matched}/{len(wiki_players)}")
    print(f"  Non risolti:   {len(wiki_players) - matched}")
    print(f"{'='*70}")

    if args.dry_run:
        print("\n[dry-run] non salvo wc2026_squads_raw.json")
        return 0

    squads[args.country]["players"] = wiki_players
    SQUADS_FILE.write_text(json.dumps(squads, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n✓ {SQUADS_FILE} aggiornato per {args.country}")
    print("\n→ Rigenera urls_wc2026.txt totale:")
    print('   python3 -c "import json; d=json.load(open(\'data/wc2026_squads_raw.json\')); '
          'urls=sorted({p[chr(39)+\'tm_profile_url\'+chr(39)] for v in d.values() for p in v[chr(39)+\'players\'+chr(39)] '
          'if p.get(chr(39)+\'tm_profile_url\'+chr(39))}); '
          'open(chr(39)+\'urls_wc2026.txt\'+chr(39),chr(39)+\'w\'+chr(39)).write(chr(10).join(urls)+chr(10)); print(len(urls))"')
    return 0


if __name__ == "__main__":
    sys.exit(main())

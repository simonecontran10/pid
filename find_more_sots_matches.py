"""
find_more_sots_matches.py — Cerca match SortItOutSi per TUTTI i giocatori
ancora senza sortitoutsi_person_id, anche cross-club (utile per Primavera,
"New arrival", prestiti). DOB-verify per evitare falsi positivi.

Strategia:
  1. Lista unmatched = giocatori senza sortitoutsi_person_id
  2. Per ognuno, cerca in tutte le rose SortItOutSi (5669 persons)
  3. Match per slug:
     - slug esatto -> candidato priorità 1
     - tutti i token TM presenti nello slug SortItOutSi (>=2 token) -> priorità 2
  4. Per ogni candidato, fetch pagina person, estrai DOB
  5. Accetta solo match con DOB esatta
  6. Output:
     - sots_more_matches_confirmed.xlsx (DOB verificata, da applicare)
     - sots_more_matches_dob_mismatch.xlsx (candidati DOB diversa)
     - sots_more_matches_no_candidate.xlsx (nessun candidato slug)
"""
from __future__ import annotations
import json
import re
import sys
import time
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _bootstrap  # noqa

import requests
from openpyxl import Workbook

from scraper.config import USER_AGENTS, SLEEP_BETWEEN_REQUESTS

DATA_DIR = Path("data")
ROSTERS_FILE = DATA_DIR / "sots_rosters.json"
PLAYERS_MAIN = DATA_DIR / "players_main.json"
LOOKUP_FILE = DATA_DIR / "sortitoutsi_id_lookup.json"

CONFIRMED_XLSX = DATA_DIR / "sots_more_matches_confirmed.xlsx"
MISMATCH_XLSX = DATA_DIR / "sots_more_matches_dob_mismatch.xlsx"
NOCAND_XLSX = DATA_DIR / "sots_more_matches_no_candidate.xlsx"


def slugify(s: str) -> str:
    if not s:
        return ""
    # Pre-traduzione di caratteri speciali NON decomponibili da NFKD
    # (Ł/ł polacche, Ø/ø nordiche, Đ/đ slave, Æ/æ, ß tedesca, Þ/þ islandesi)
    SPECIAL = str.maketrans({
        "Ł": "L", "ł": "l",
        "Ø": "O", "ø": "o",
        "Đ": "D", "đ": "d",
        "Æ": "AE", "æ": "ae",
        "ß": "ss",
        "Þ": "Th", "þ": "th",
        "Ð": "D", "ð": "d",
    })
    s = s.translate(SPECIAL)
    nfkd = unicodedata.normalize("NFKD", s)
    no_acc = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    out = []
    for ch in no_acc.lower():
        if ch.isalnum():
            out.append(ch)
        elif ch in (" ", "-", "_", "'", "."):
            out.append("-")
    s = "".join(out)
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-")


def fetch_dob(sots_id, slug, session):
    url = f"https://sortitoutsi.net/football-manager-2026/person/{sots_id}/{slug}"
    try:
        r = session.get(url, headers={"User-Agent": USER_AGENTS[0]}, timeout=15)
        if r.status_code != 200:
            return None
        m = re.search(r"DOB</dt>\s*<dd[^>]*>(\d{4}-\d{2}-\d{2})</dd>", r.text)
        return m.group(1) if m else None
    except Exception:
        return None


def main():
    rosters = json.loads(ROSTERS_FILE.read_text(encoding="utf-8"))
    players = json.loads(PLAYERS_MAIN.read_text(encoding="utf-8"))
    lookup = json.loads(LOOKUP_FILE.read_text(encoding="utf-8"))

    matched_tm = set(int(k) for k in lookup.keys())

    # 1) Unmatched
    unmatched = [p for p in players if p.get("tm_player_id") not in matched_tm and not p.get("sortitoutsi_person_id")]
    print(f"Giocatori senza sortitoutsi_person_id: {len(unmatched)}")

    # 2) Indice persons -> slug
    # (sots_id, slug) coppie su tutti i club
    all_persons = []
    by_slug = {}
    for sots_team_id, roster in rosters.items():
        for person in roster["persons"]:
            all_persons.append({
                "sots_id": person["sots_id"],
                "slug": person["slug"],
                "name_link": person.get("name_link", ""),
                "club_name": roster["club_name"],
            })
            by_slug.setdefault(person["slug"], []).append(person["sots_id"])
    print(f"Persons SortItOutSi totali (40 rose): {len(all_persons)}")

    # 3) Match candidati
    print("\n=== Step 1: cerca candidati per slug/token (offline) ===")
    candidates = []
    for u in unmatched:
        full_slug = slugify(u.get("full_name", ""))
        if not full_slug:
            continue
        tokens = [t for t in full_slug.split("-") if len(t) > 1]
        if not tokens:
            continue

        # Match esatto slug
        cands = []
        for p in all_persons:
            slug_p = p["slug"]
            slug_tokens = slug_p.split("-")
            if slug_p == full_slug:
                cands.append((1.0, "slug_esatto", p))
            elif len(tokens) >= 2 and all(t in slug_tokens for t in tokens):
                cands.append((0.85, "all_tokens", p))
        if not cands:
            continue
        # Dedup per sots_id (un giocatore può apparire in più club)
        seen_sids = set()
        uniq = []
        for c in cands:
            if c[2]["sots_id"] in seen_sids:
                continue
            seen_sids.add(c[2]["sots_id"])
            uniq.append(c)
        candidates.append({
            "tm_id": u["tm_player_id"],
            "name": u.get("full_name", ""),
            "tm_dob": str(u.get("date_of_birth", ""))[:10],
            "tm_club": u.get("current_club_name", ""),
            "candidates": uniq[:5],  # max 5 candidati
        })

    print(f"  giocatori con almeno 1 candidato: {len(candidates)}")

    # 4) Verifica DOB per ogni candidato
    print("\n=== Step 2: verifica DOB (fetch pagina person) ===")
    session = requests.Session()
    confirmed = []
    mismatched = []
    no_dob = []

    n_fetch = 0
    for i, c in enumerate(candidates, 1):
        # Prova candidati in ordine di score
        chosen = None
        for score, why, p in c["candidates"]:
            sots_dob = fetch_dob(p["sots_id"], p["slug"], session)
            n_fetch += 1
            time.sleep(SLEEP_BETWEEN_REQUESTS)
            if not sots_dob:
                continue
            if sots_dob == c["tm_dob"]:
                chosen = (score, why, p, sots_dob)
                break
            else:
                # Salva mismatch ma continua
                mismatched.append({
                    "name": c["name"], "tm_id": c["tm_id"], "tm_club": c["tm_club"],
                    "score": score, "why": why,
                    "sots_id": p["sots_id"], "slug": p["slug"], "sots_club": p["club_name"],
                    "tm_dob": c["tm_dob"], "sots_dob": sots_dob,
                })
        if chosen:
            score, why, p, sots_dob = chosen
            confirmed.append({
                "name": c["name"], "tm_id": c["tm_id"], "tm_club": c["tm_club"],
                "score": score, "why": why,
                "sots_id": p["sots_id"], "slug": p["slug"], "sots_club": p["club_name"],
                "dob": sots_dob,
            })
            print(f"  [{i}/{len(candidates)}] {c['name']:<32} OK -> sots {p['sots_id']} (sots_club={p['club_name']})")
        else:
            print(f"  [{i}/{len(candidates)}] {c['name']:<32} no DOB match")

    print(f"\n=== Risultati ===")
    print(f"  confermati DOB: {len(confirmed)}")
    print(f"  DOB mismatch:   {len(mismatched)}")
    print(f"  fetch totali:   {n_fetch}")

    # Salva confirmed
    wb = Workbook()
    ws = wb.active
    ws.title = "confirmed"
    ws.append(["name", "tm_player_id", "club_name", "score", "why", "sots_id", "url", "dob"])
    for r in confirmed:
        url = f"https://sortitoutsi.net/football-manager-2026/person/{r['sots_id']}/{r['slug']}"
        ws.append([r["name"], r["tm_id"], r["tm_club"], r["score"], r["why"], r["sots_id"], url, r["dob"]])
    for col in "ABCDEFGH":
        ws.column_dimensions[col].width = 22
    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["G"].width = 60
    wb.save(CONFIRMED_XLSX)

    # Salva mismatch (utili per controllo manuale di omonimi)
    wb = Workbook()
    ws = wb.active
    ws.title = "mismatch"
    ws.append(["name", "tm_player_id", "tm_club", "tm_dob", "sots_dob", "sots_id", "slug", "sots_club", "url"])
    for r in mismatched:
        url = f"https://sortitoutsi.net/football-manager-2026/person/{r['sots_id']}/{r['slug']}"
        ws.append([r["name"], r["tm_id"], r["tm_club"], r["tm_dob"], r["sots_dob"],
                   r["sots_id"], r["slug"], r["sots_club"], url])
    for col in "ABCDEFGHI":
        ws.column_dimensions[col].width = 22
    wb.save(MISMATCH_XLSX)

    print(f"\nSalvato {CONFIRMED_XLSX.name}")
    print(f"Salvato {MISMATCH_XLSX.name}")


if __name__ == "__main__":
    main()

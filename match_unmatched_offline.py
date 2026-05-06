"""
match_unmatched_offline.py — Match aggressivo offline degli unmatched.
Usa i dati già scaricati in data/sots_rosters.json. Niente rete.

Strategia per ogni giocatore unmatched (in club con sortitoutsi_team_id):
  1. Costruisci slug atteso da full_name TM (lowercase, no accenti, trattini)
  2. Cerca nel rosters[sots_team_id]:
     a) slug esatto -> score 1.0
     b) cognome match -> score 0.7
     c) primo+ultimo token match -> score 0.6
  3. Score >= 0.7 -> patch automatico
  4. Altrimenti -> esporta in sots_unmatched_review.xlsx
"""
from __future__ import annotations
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _bootstrap  # noqa

from openpyxl import Workbook

DATA_DIR = Path("data")
ROSTERS_FILE = DATA_DIR / "sots_rosters.json"
PLAYERS_MAIN = DATA_DIR / "players_main.json"
LOOKUP_FILE = DATA_DIR / "sortitoutsi_id_lookup.json"
CLUBS_FILE = DATA_DIR / "clubs.json"
REVIEW_XLSX = DATA_DIR / "sots_unmatched_review.xlsx"


def slugify(s: str) -> str:
    if not s:
        return ""
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


def normalize_name(s: str) -> str:
    """Normalizza per confronto: lowercase, no accenti, no punteggiatura."""
    if not s:
        return ""
    nfkd = unicodedata.normalize("NFKD", s)
    no_acc = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    return re.sub(r"[^a-z]", "", no_acc.lower())


def main():
    rosters = json.loads(ROSTERS_FILE.read_text(encoding="utf-8"))
    players = json.loads(PLAYERS_MAIN.read_text(encoding="utf-8"))
    lookup = json.loads(LOOKUP_FILE.read_text(encoding="utf-8"))
    clubs = json.loads(CLUBS_FILE.read_text(encoding="utf-8"))

    # Map nome club -> sortitoutsi_team_id
    club_to_sots = {c["name"]: c.get("sortitoutsi_team_id") for c in clubs if c.get("sortitoutsi_team_id")}

    # Set di tm_id già matchati
    matched_tm = set(int(k) for k in lookup.keys())

    # Trova unmatched in club con sots_team_id
    unmatched = []
    for p in players:
        tm_id = p.get("tm_player_id")
        if tm_id in matched_tm:
            continue
        club_name = p.get("current_club_name") or p.get("roster_club_name")
        sots_team_id = club_to_sots.get(club_name)
        if not sots_team_id:
            continue
        unmatched.append({
            "tm_player_id": tm_id,
            "name": p.get("full_name", ""),
            "club_name": club_name,
            "sots_team_id": sots_team_id,
            "year_birth": str(p.get("date_of_birth", ""))[:4],
        })

    print(f"Unmatched in club con sots_team_id: {len(unmatched)}")

    # Per ogni unmatched, cerca nella rosa SortItOutSi
    auto_matched = []  # score >= 0.7
    review = []        # score < 0.7 (manual review)

    for u in unmatched:
        full_slug = slugify(u["name"])
        tokens = full_slug.split("-")
        nameless_norm = normalize_name(u["name"])
        last_token = tokens[-1] if tokens else ""
        first_token = tokens[0] if tokens else ""

        roster = rosters.get(str(u["sots_team_id"]))
        if not roster:
            continue

        candidates = []
        for person in roster["persons"]:
            slug_p = person["slug"]
            slug_tokens = slug_p.split("-")
            score = 0.0
            why = ""
            # 1.0: slug esatto
            if slug_p == full_slug:
                score = 1.0
                why = "slug_esatto"
            # 0.85: tutti i token TM presenti nel slug SortItOutSi (in qualsiasi ordine)
            elif tokens and all(t in slug_tokens for t in tokens):
                score = 0.85
                why = "all_tokens_match"
            # 0.7: cognome match
            elif last_token and last_token in slug_tokens:
                # Se anche il primo nome match -> 0.85
                if first_token and first_token in slug_tokens:
                    score = 0.85
                    why = "first_last_match"
                else:
                    score = 0.7
                    why = "lastname_match"
            # 0.5: primo nome match (debole)
            elif first_token and first_token in slug_tokens:
                score = 0.5
                why = "firstname_only"

            if score > 0:
                candidates.append({
                    "score": score,
                    "why": why,
                    "sots_id": person["sots_id"],
                    "slug": slug_p,
                    "name_link": person.get("name_link", ""),
                })

        # Ordina per score
        candidates.sort(key=lambda c: c["score"], reverse=True)
        u["candidates"] = candidates[:3]
        u["best"] = candidates[0] if candidates else None

        if u["best"] and u["best"]["score"] >= 0.7:
            auto_matched.append(u)
        else:
            review.append(u)

    print(f"\n=== Risultati match offline ===")
    print(f"  auto-matched (score>=0.7): {len(auto_matched)}")
    print(f"  review necessaria:         {len(review)}")

    # Stampa primi 10 auto-match
    print(f"\n=== Primi 10 auto-match ===")
    for u in auto_matched[:10]:
        b = u["best"]
        print(f"  {u['name']:<30}  ({u['club_name']:<20}) -> sots {b['sots_id']} {b['slug']} [{b['why']}, {b['score']}]")

    # Stampa primi 10 review
    print(f"\n=== Primi 10 review (score basso o nessun candidato) ===")
    for u in review[:10]:
        if u["best"]:
            b = u["best"]
            print(f"  {u['name']:<30}  ({u['club_name']:<20}) -> top: {b['sots_id']} {b['slug']} [{b['why']}, {b['score']}]")
        else:
            print(f"  {u['name']:<30}  ({u['club_name']:<20}) -> nessun candidato")

    # Esporta Excel di review
    wb = Workbook()
    ws = wb.active
    ws.title = "review"
    headers = ["name", "tm_player_id", "club_name", "year_birth", "best_score", "best_why",
               "candidate1_url", "candidate1_slug",
               "candidate2_url", "candidate2_slug",
               "candidate3_url", "candidate3_slug",
               "confirmed_url"]
    ws.append(headers)
    for u in review:
        c = u["candidates"]
        row = [u["name"], u["tm_player_id"], u["club_name"], u["year_birth"]]
        if c:
            row.extend([c[0]["score"], c[0]["why"]])
        else:
            row.extend(["", ""])
        for i in range(3):
            if i < len(c):
                slug = c[i]["slug"]
                sid = c[i]["sots_id"]
                row.append(f"https://sortitoutsi.net/football-manager-2026/person/{sid}/{slug}")
                row.append(slug)
            else:
                row.extend(["", ""])
        row.append("")  # confirmed_url
        ws.append(row)
    
    # Larghezze colonne
    for col in "ABCDEFGHIJKLM":
        ws.column_dimensions[col].width = 22
    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["G"].width = 60
    ws.column_dimensions["I"].width = 60
    ws.column_dimensions["K"].width = 60
    ws.column_dimensions["M"].width = 60

    wb.save(REVIEW_XLSX)
    print(f"\nSalvato {REVIEW_XLSX} con {len(review)} righe per review manuale")

    # Salva auto_matched come Excel separato (così l'utente può vedere prima di applicare)
    AUTO_XLSX = DATA_DIR / "sots_auto_matched_preview.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "auto"
    ws.append(["name", "tm_player_id", "club_name", "score", "why", "sots_id", "url"])
    for u in auto_matched:
        b = u["best"]
        url = f"https://sortitoutsi.net/football-manager-2026/person/{b['sots_id']}/{b['slug']}"
        ws.append([u["name"], u["tm_player_id"], u["club_name"], b["score"], b["why"], b["sots_id"], url])
    for col in "ABCDEFG":
        ws.column_dimensions[col].width = 22
    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["G"].width = 60
    wb.save(AUTO_XLSX)
    print(f"Salvato {AUTO_XLSX} con {len(auto_matched)} auto-match (preview, NON applicato)")


if __name__ == "__main__":
    main()

"""
scrape_sortitoutsi_ids.py — Auto-popola sortitoutsi_person_id dei giocatori
navigando le pagine ROSA di sortitoutsi.net.

Strategia (molto più efficiente della search per nome):
  1. Per ogni club che ha sortitoutsi_team_id (23 su 36, curati a mano):
     fetch https://sortitoutsi.net/football-manager-2026/team/{id}/{slug}
  2. Estrai dalla pagina tutti i link /person/{id}/{slug}
  3. Match per nome con i giocatori Transfermarkt che hanno quel club
  4. Salva mapping tm_player_id -> sortitoutsi_person_id
  5. Scarica face_{id}.png

Output:
  data/sortitoutsi_id_lookup.json  (mapping completo)
  data/photos/players_sots_lookup/{sots_id}.png  (face scaricate)

Aggiorna in-place players_saudi.json e players_all.json con i nuovi sortitoutsi_*.

Uso:
    source venv/bin/activate
    python3 scrape_sortitoutsi_ids.py
    python3 scrape_sortitoutsi_ids.py --limit 3   # solo primi 3 club (test)
"""

from __future__ import annotations

import json
import re
import sys
import time
import unicodedata
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

from scraper.config import (
    CLUBS_FILE,
    DATA_DIR,
    PLAYERS_SAUDI_FILE,
    PLAYERS_STATIC_FILE,
    SLEEP_BETWEEN_REQUESTS,
    USER_AGENTS,
)
from scraper.sortitoutsi import face_url, profile_url

LOOKUP_FILE = DATA_DIR / "sortitoutsi_id_lookup.json"
PLAYERS_ALL_FILE = DATA_DIR / "players_all.json"
PHOTOS_DIR = DATA_DIR / "photos"
SOTS_LOOKUP_DIR = PHOTOS_DIR / "players_sots_lookup"
SOTS_LOOKUP_DIR.mkdir(parents=True, exist_ok=True)

TEAM_URL_TEMPLATE = "https://sortitoutsi.net/football-manager-2026/team/{sots_id}/{slug}"
SEARCH_URL_TEMPLATE = "https://sortitoutsi.net/search/database?search={name}&type="

HEADERS = {
    "User-Agent": USER_AGENTS[0],
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def search_by_name(name: str, club_name: Optional[str], session: requests.Session) -> Optional[int]:
    """Fallback per giocatori non trovati nelle rose team. Cerca via /search/database."""
    if not name:
        return None
    from urllib.parse import quote_plus
    url = SEARCH_URL_TEMPLATE.format(name=quote_plus(name))
    try:
        r = session.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return None
    except Exception:
        return None
    soup = BeautifulSoup(r.text, "lxml")
    name_norm = _norm(name)
    name_tokens = set(name_norm.split())
    club_norm = _norm(club_name or "")
    # Estrai candidati da link /person/{id}/{slug}
    candidates: list[tuple[float, int, str]] = []
    seen: set[int] = set()
    for a in soup.select('a[href*="/person/"]'):
        href = a.get("href", "")
        m = re.search(r"/person/(\d+)/", href)
        if not m:
            continue
        sid = int(m.group(1))
        if sid in seen:
            continue
        seen.add(sid)
        link_text = a.get_text(" ", strip=True)
        link_norm = _norm(link_text)
        link_tokens = set(link_norm.split())
        if not link_tokens:
            continue
        # score: overlap tokens nome + bonus se nel context appare il club
        overlap = len(name_tokens & link_tokens) / max(len(name_tokens), 1)
        score = overlap
        # cerca il context del row del result per club hint
        parent = a.find_parent("tr") or a.find_parent("li") or a.find_parent("div")
        if parent and club_norm:
            ctx = _norm(parent.get_text(" ", strip=True))
            if club_norm in ctx:
                score += 0.3
        if score >= 0.6:
            candidates.append((score, sid, link_text))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def _norm(s: str) -> str:
    """Normalizza per matching: lowercase, no accenti, no punteggiatura, single spaces."""
    if not s:
        return ""
    nfkd = unicodedata.normalize("NFKD", s)
    no_acc = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    cleaned = re.sub(r"[^a-zA-Z\s]", " ", no_acc).lower()
    return re.sub(r"\s+", " ", cleaned).strip()


def _slug(s: str) -> str:
    n = _norm(s)
    return n.replace(" ", "-")


def _load(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def _save(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def fetch_team_roster(sots_team_id: int, club_name: str, session: requests.Session) -> list[dict]:
    """Scarica la pagina rosa del club e ritorna lista di {sots_id, name}."""
    slug = _slug(club_name).replace("al-", "al-")
    url = TEAM_URL_TEMPLATE.format(sots_id=sots_team_id, slug=slug)
    try:
        r = session.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        if r.status_code != 200:
            print(f"    [HTTP {r.status_code}] {url}")
            return []
    except Exception as e:
        print(f"    [error] {type(e).__name__}: {e}")
        return []
    soup = BeautifulSoup(r.text, "lxml")
    out: list[dict] = []
    seen: set[int] = set()
    for a in soup.select('a[href*="/person/"]'):
        href = a.get("href", "")
        m = re.search(r"/person/(\d+)/([^/?]+)", href)
        if not m:
            continue
        sid = int(m.group(1))
        if sid in seen:
            continue
        seen.add(sid)
        name = a.get_text(" ", strip=True)
        if not name:
            # fallback dallo slug
            name = m.group(2).replace("-", " ").title()
        out.append({"sots_id": sid, "name": name, "slug": m.group(2)})
    return out


def download_face(sots_id: int, session: requests.Session) -> Optional[Path]:
    if not sots_id:
        return None
    dest = SOTS_LOOKUP_DIR / f"{sots_id}.png"
    if dest.exists() and dest.stat().st_size > 200:
        return dest
    url = face_url(sots_id)
    try:
        r = session.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200 and len(r.content) > 200:
            dest.write_bytes(r.content)
            return dest
    except Exception:
        pass
    return None


def match_players(tm_players_in_club: list[dict], sots_roster: list[dict]) -> list[tuple[dict, dict, float]]:
    """Match nome tra giocatori TM e sortitoutsi del club. Ritorna lista (tm, sots, score)."""
    matches = []
    used_sots: set[int] = set()
    for tm in tm_players_in_club:
        tm_norm = _norm(tm.get("full_name") or "")
        if not tm_norm:
            continue
        tm_tokens = set(tm_norm.split())
        best = None  # (score, sots_entry)
        for s in sots_roster:
            if s["sots_id"] in used_sots:
                continue
            s_norm = _norm(s["name"])
            if not s_norm:
                continue
            if tm_norm == s_norm:
                best = (1.0, s)
                break
            s_tokens = set(s_norm.split())
            common = tm_tokens & s_tokens
            if not common:
                continue
            score = len(common) / max(len(tm_tokens | s_tokens), 1)
            if best is None or score > best[0]:
                best = (score, s)
        if best and best[0] >= 0.6:
            matches.append((tm, best[1], best[0]))
            used_sots.add(best[1]["sots_id"])
    return matches


def main() -> None:
    limit = None
    if "--limit" in sys.argv:
        i = sys.argv.index("--limit")
        if i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])

    saudi = _load(PLAYERS_SAUDI_FILE, [])
    clubs = _load(CLUBS_FILE, [])
    if not saudi or not clubs:
        print("[FATAL] data/players_saudi.json o data/clubs.json mancanti.")
        return

    # Indicizza giocatori per club
    by_club: dict[int, list[dict]] = {}
    for p in saudi:
        cid = p.get("current_club_id")
        if cid:
            by_club.setdefault(cid, []).append(p)

    # Solo club con sortitoutsi_team_id
    clubs_with_sots = [c for c in clubs if c.get("sortitoutsi_team_id")]
    if limit:
        clubs_with_sots = clubs_with_sots[:limit]

    print(f"Club con sortitoutsi_team_id: {len(clubs_with_sots)}/{len(clubs)}")
    total_saudi_in_those = sum(len(by_club.get(c["tm_club_id"], [])) for c in clubs_with_sots)
    print(f"Saudi in quei club: {total_saudi_in_those}")
    print()

    lookup = _load(LOOKUP_FILE, {})
    session = requests.Session()
    started = time.monotonic()
    total_matched = 0
    total_unmatched_tm = 0
    total_face_dl = 0
    total_face_fail = 0

    for i, club in enumerate(clubs_with_sots, 1):
        cid_tm = club["tm_club_id"]
        sots_team = club["sortitoutsi_team_id"]
        club_name = club["name"]
        tm_players = by_club.get(cid_tm, [])
        print(f"[{i}/{len(clubs_with_sots)}] {club_name}  (TM saudi: {len(tm_players)}, sots_team: {sots_team})")

        sots_roster = fetch_team_roster(sots_team, club_name, session)
        time.sleep(SLEEP_BETWEEN_REQUESTS)
        if not sots_roster:
            print("    rosa sortitoutsi vuota, skip")
            continue
        print(f"    rosa sortitoutsi: {len(sots_roster)} giocatori")

        matches = match_players(tm_players, sots_roster)
        print(f"    match: {len(matches)}/{len(tm_players)}")

        for tm, sots, score in matches:
            entry = {
                "sots_id": sots["sots_id"],
                "name": tm["full_name"],
                "club": club_name,
                "match_score": round(score, 3),
                "matched_via": "team_roster",
            }
            face_path = download_face(sots["sots_id"], session)
            if face_path:
                entry["face_local"] = face_path.relative_to(DATA_DIR).as_posix()
                total_face_dl += 1
            else:
                total_face_fail += 1
            lookup[str(tm["tm_player_id"])] = entry
            total_matched += 1
            time.sleep(0.3)

        unmatched = len(tm_players) - len(matches)
        total_unmatched_tm += unmatched

        if i % 5 == 0 or i == len(clubs_with_sots):
            _save(LOOKUP_FILE, lookup)

    _save(LOOKUP_FILE, lookup)

    # ===== FASE 2: fallback search per gli unmatched =====
    print(f"\n=== Fallback search per giocatori non trovati nelle rose ===")
    unmatched = [p for p in saudi if str(p["tm_player_id"]) not in lookup]
    print(f"  da cercare: {len(unmatched)} giocatori")
    if "--no-search" in sys.argv:
        print("  --no-search: salto questa fase")
    else:
        search_found = 0
        search_failed = 0
        search_face_dl = 0
        for j, p in enumerate(unmatched, 1):
            name = p.get("full_name") or ""
            club_name = p.get("current_club_name") or p.get("roster_club_name") or ""
            sid = search_by_name(name, club_name, session)
            time.sleep(SLEEP_BETWEEN_REQUESTS)
            if sid:
                entry = {
                    "sots_id": sid, "name": name, "club": club_name,
                    "match_score": 0.7, "matched_via": "search",
                }
                face_path = download_face(sid, session)
                if face_path:
                    entry["face_local"] = face_path.relative_to(DATA_DIR).as_posix()
                    search_face_dl += 1
                lookup[str(p["tm_player_id"])] = entry
                search_found += 1
                time.sleep(0.3)
            else:
                search_failed += 1
            if j % 20 == 0 or j == len(unmatched):
                _save(LOOKUP_FILE, lookup)
                print(f"  [{j}/{len(unmatched)}] found={search_found}  no_match={search_failed}  face_dl={search_face_dl}")
        _save(LOOKUP_FILE, lookup)
        print(f"\n  fase 2 fatta: +{search_found} match via search, +{search_face_dl} face")

    # Aggiorna i JSON con sortitoutsi_*
    print("\nAggiorno players_saudi.json e players_all.json ...")
    for path in (PLAYERS_SAUDI_FILE, PLAYERS_STATIC_FILE, PLAYERS_ALL_FILE):
        if not path.exists():
            continue
        data = _load(path, [])
        for p in data:
            entry = lookup.get(str(p["tm_player_id"]))
            if not entry or not entry.get("sots_id"):
                continue
            sid = entry["sots_id"]
            if not p.get("sortitoutsi_person_id"):
                p["sortitoutsi_person_id"] = sid
                p["sortitoutsi_face_url"] = face_url(sid)
                p["sortitoutsi_profile_url"] = profile_url(sid, p.get("full_name"))
            if entry.get("face_local") and not p.get("sortitoutsi_face_local_lookup"):
                p["sortitoutsi_face_local_lookup"] = entry["face_local"]
        _save(path, data)

    elapsed = int(time.monotonic() - started)
    print(f"\n{'='*60}")
    print(f"  DONE in {elapsed}s")
    print(f"  match trovati: {total_matched}")
    print(f"  TM unmatched : {total_unmatched_tm} (giocatori senza match nel club rosa)")
    print(f"  face scaricate: {total_face_dl}, fallite: {total_face_fail}")
    print(f"  saved -> {LOOKUP_FILE.name}")


if __name__ == "__main__":
    main()

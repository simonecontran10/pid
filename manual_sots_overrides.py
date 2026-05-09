"""
manual_sots_overrides.py — Applica override manuali sots_id da una lista hardcoded
di URL forniti dall'utente. Per giocatori che `find_more_sots_matches.py` non
matchava (vari motivi: nome troppo diverso da slug, no DOB su SortItOutSi,
giocatore non in cache rosters perché in club che non è in PID, ecc).

Per ogni voce:
  - Estrae sots_id dall'URL (regex /person/{id}/...)
  - Trova il giocatore PID per nome (con normalizzazione tollerante)
  - Aggiorna sortitoutsi_id, sortitoutsi_face_url, sortitoutsi_profile_url, sortitoutsi_face_local_lookup
  - Scarica la face in data/photos/players_sots_lookup/{sots_id}.png
  - Aggiorna sortitoutsi_id_lookup.json
"""
from __future__ import annotations

import json
import re
import sys
import time
import unicodedata
from pathlib import Path

import requests

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
PHOTOS_DIR = DATA_DIR / "photos" / "players_sots_lookup"
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)

PLAYERS_FILES = [
    DATA_DIR / "players_main.json",
    DATA_DIR / "players_static.json",
    DATA_DIR / "players_all.json",
]
LOOKUP_FILE = DATA_DIR / "sortitoutsi_id_lookup.json"

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

# === Lista override forniti dall'utente (8 mag 2026) ===
OVERRIDES = [
    ("Gabriel Charpentier",  "https://sortitoutsi.net/football-manager-2026/person/49047842/gabriel-charpentier"),
    ("Joseph Liteta",        "https://sortitoutsi.net/football-manager-2026/person/2000241198/joseph-liteta"),
    ("Kacper Urbański",      "https://sortitoutsi.net/football-manager-2026/person/96161950/kacper-urbanski"),
    ("Lorenzo Torriani",     "https://sortitoutsi.net/football-manager-2026/person/2000103120/lorenzo-torriani"),
    ("Mateusz Praszelik",    "https://sortitoutsi.net/football-manager-2026/person/96105431/mateusz-praszelik"),
    ("Antonio Čolak",        "https://sortitoutsi.net/football-manager-2026/person/91105244/antonio-colak"),
    ("Arkadiusz Reca",       "https://sortitoutsi.net/football-manager-2026/person/96048686/arkadiusz-reca"),
    ("Indrit Mavraj",        "https://sortitoutsi.net/football-manager-2026/person/2000227896/indrit-mavraj"),
    ("Przemysław Szymiński", "https://sortitoutsi.net/football-manager-2026/person/96043133/przemyslaw-szyminski"),
    ("Przemysław Wiśniewski","https://sortitoutsi.net/football-manager-2026/person/96136102/przemyslaw-wisniewski"),
    ("Alessandro Longoni",   "https://sortitoutsi.net/football-manager-2026/person/2000336209/alessandro-longoni"),
    ("Grady Makiobo",        "https://sortitoutsi.net/football-manager-2026/person/2000307484/grady-makiobo"),
    ("Mateusz Skoczylas",    "https://sortitoutsi.net/football-manager-2026/person/2000193451/mateusz-skoczylas"),
    ("Mattia Brugarello",    "https://sortitoutsi.net/football-manager-2026/person/2000098492/mattia-brugarello"),
    ("Simone Cinquegrano",   "https://sortitoutsi.net/football-manager-2026/person/2000124322/simone-cinquegrano"),
    ("Andrea Caucci",        "https://sortitoutsi.net/football-manager-2026/person/2000266831/andrea-caucci"),
    ("Bilal Brusdeilins",    "https://sortitoutsi.net/football-manager-2026/person/2000310760/bilal-brusdeilins"),
    ("Daniel Mikołajewski",  "https://sortitoutsi.net/football-manager-2026/person/2000150888/daniel-mikolajewski"),
    ("Eddy Kouadio",         "https://sortitoutsi.net/football-manager-2026/person/2000184141/eddy-kouadio"),
    ("Grigorios Politakis",  "https://sortitoutsi.net/football-manager-2026/person/2000204708/grigoris-politakis"),
    ("Henry Camara",         "https://sortitoutsi.net/football-manager-2026/person/2000198110/henry-camara"),
    ("Hjalte Lærke",         "https://sortitoutsi.net/football-manager-2026/person/2000384675/hjalte-laerke"),
    ("Ioan Vermeșan",        "https://sortitoutsi.net/football-manager-2026/person/2000157324/ioan-vermesan"),
    ("Marco Tiozzo",         "https://sortitoutsi.net/football-manager-2026/person/2000386592/marco-tiozzo-pagio"),
    ("Michael Zeppieri",     "https://sortitoutsi.net/football-manager-2026/person/2000269983/michael-zeppieri"),
    ("Nadir El Jamali",      "https://sortitoutsi.net/football-manager-2026/person/2000297870/nadir-el-jamali"),
]


def _norm(s: str) -> str:
    if not s:
        return ""
    POL = str.maketrans({"ł": "l", "Ł": "L", "ø": "o", "Ø": "O", "ș": "s", "Ș": "S", "ț": "t", "Ț": "T"})
    s = s.translate(POL)
    nfkd = unicodedata.normalize("NFKD", s)
    no_acc = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", no_acc.lower()).strip()


def extract_sots_id(url: str) -> int | None:
    m = re.search(r"/person/(\d+)/", url)
    return int(m.group(1)) if m else None


def find_player(players: list[dict], target_name: str) -> dict | None:
    """Trova il giocatore con normalizzazione tollerante. Match per ordine inverso (cognome prima)."""
    target_norm = _norm(target_name)
    target_tokens = set(target_norm.split())
    if not target_tokens:
        return None

    # Strategia 1: match esatto sul nome normalizzato
    for p in players:
        if _norm(p.get("full_name", "")) == target_norm:
            return p

    # Strategia 2: tutti i token del target presenti nel candidato
    candidates = []
    for p in players:
        c_tokens = set(_norm(p.get("full_name", "")).split())
        if target_tokens.issubset(c_tokens):
            candidates.append((p, len(c_tokens)))
    if candidates:
        # Più stretto = meno token in più = più probabile match
        candidates.sort(key=lambda x: x[1])
        return candidates[0][0]

    # Strategia 3: cognome (ultimo token) e almeno 1 token nome
    last_token = list(target_tokens)[-1] if len(target_tokens) > 1 else None
    if last_token:
        for p in players:
            c_tokens = set(_norm(p.get("full_name", "")).split())
            if last_token in c_tokens and len(c_tokens & target_tokens) >= 2:
                return p

    return None


def download_face(sots_id: int, dest: Path) -> tuple[bool, int]:
    if dest.exists() and dest.stat().st_size > 200:
        return True, dest.stat().st_size
    url = f"https://sortitoutsi.b-cdn.net/uploads/face/face_{sots_id}.png"
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=20)
        if r.status_code != 200:
            return False, 0
        if len(r.content) < 200:
            return False, len(r.content)
        dest.write_bytes(r.content)
        return True, len(r.content)
    except Exception as e:
        print(f"  [download err] {e}")
        return False, 0


def main() -> int:
    # Carica tutti i 3 JSON
    data_files = {}
    for f in PLAYERS_FILES:
        if f.exists():
            data_files[f] = json.loads(f.read_text(encoding="utf-8"))
        else:
            print(f"  [skip] {f.name} non esiste")

    # Per matching, uso players_main.json come fonte canonica
    primary = data_files.get(PLAYERS_FILES[0])
    if primary is None:
        print(f"❌ {PLAYERS_FILES[0].name} non trovato")
        return 1

    lookup = json.loads(LOOKUP_FILE.read_text(encoding="utf-8")) if LOOKUP_FILE.exists() else {}

    matched = []
    not_found = []
    faces_downloaded = 0
    faces_failed = 0

    for name, url in OVERRIDES:
        sots_id = extract_sots_id(url)
        if not sots_id:
            print(f"  ❌ {name}: impossibile estrarre sots_id da {url}")
            continue

        p = find_player(primary, name)
        if not p:
            not_found.append((name, sots_id))
            print(f"  ❌ {name} (sots={sots_id}): giocatore non trovato in players_main.json")
            continue

        tm_id = p["tm_player_id"]
        full = p.get("full_name")
        print(f"  ✓ {name:<28} → tm={tm_id:<8} sots={sots_id}  (DB: {full})")

        # Aggiorna in tutti i 3 JSON
        for f, data in data_files.items():
            for q in data:
                if q.get("tm_player_id") == tm_id:
                    q["sortitoutsi_id"] = sots_id
                    q["sortitoutsi_face_url"] = f"https://sortitoutsi.b-cdn.net/uploads/face/face_{sots_id}.png"
                    q["sortitoutsi_profile_url"] = url
                    q["sortitoutsi_face_local_lookup"] = f"photos/players_sots_lookup/{sots_id}.png"
                    # Compat field name (apply_confirmed_matches usa "sortitoutsi_person_id")
                    q["sortitoutsi_person_id"] = sots_id

        # Aggiorna lookup
        lookup[str(tm_id)] = {
            "sots_id": sots_id,
            "name": name,
            "match_score": 1.0,
            "matched_via": "manual_override_8mag",
        }

        # Scarica face
        dest = PHOTOS_DIR / f"{sots_id}.png"
        ok, size = download_face(sots_id, dest)
        if ok:
            faces_downloaded += 1
            print(f"      face ✓ ({size} bytes)")
        else:
            faces_failed += 1
            print(f"      face ❌ ({size} bytes)")

        matched.append((name, tm_id, sots_id))
        time.sleep(0.2)

    # Salva tutto
    for f, data in data_files.items():
        f.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n  {f.name} salvato")

    LOOKUP_FILE.write_text(json.dumps(lookup, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  {LOOKUP_FILE.name} salvato ({len(lookup)} entries)")

    print()
    print("=" * 70)
    print(f"  ✓ Matched: {len(matched)}/{len(OVERRIDES)}")
    print(f"  ✓ Faces scaricate: {faces_downloaded}")
    print(f"  ❌ Faces fallite (placeholder SortItOutSi): {faces_failed}")
    if not_found:
        print(f"\n  ❌ Non trovati nel DB ({len(not_found)}):")
        for n, sid in not_found:
            print(f"     - {n} (sots={sid})")
    print("=" * 70)
    print()
    print("Push con:")
    print("  git add -A && git commit -m 'fix: foto manuali per 25 giocatori' && git push")

    return 0


if __name__ == "__main__":
    sys.exit(main())

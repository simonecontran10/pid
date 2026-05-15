"""
enrich_sortitoutsi.py — Post-processing dei dati scrapati.

Da lanciare DOPO run_static.py. Esegue:

1. FIX CLUB PLACEHOLDER
   Transfermarkt mostra 'New arrival' / 'Winter signing' / 'Returnee' per giocatori
   in transizione. Sostituiamo con il roster_club (il club da cui abbiamo scrapato
   la rosa) per avere sempre il club corretto.

2. ENRICH SORTITOUTSI
   Aggiunge URL foto FM-style (face) ai profili e URL logo ai club.

3. INTEGRA ASSET CURATED
   Se data/photos/players_curated/{sots_id}.png esiste -> usa la foto curata.
   Se data/photos/clubs_curated/{sots_team_id}.png esiste -> usa il logo curato.

Aggiorna in-place: data/clubs.json, data/players_all.json, data/players_main.json,
data/players_static.json. Riusabile (idempotente).

Uso:
    python3 enrich_sortitoutsi.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _bootstrap  # noqa: F401  (auto-attiva venv del progetto se necessario)

import json

from scraper.config import (
    CLUBS_FILE,
    DATA_DIR,
    PLAYERS_MAIN_FILE,
    PLAYERS_STATIC_FILE,
)
from scraper.sortitoutsi import (
    enrich_club,
    enrich_profile,
    is_placeholder_club,
    load_sortitoutsi_mapping,
    load_sortitoutsi_team_mapping,
)

PHOTOS_DIR = DATA_DIR / "photos"
PLAYERS_CURATED_DIR = PHOTOS_DIR / "players_curated"
CLUBS_CURATED_DIR = PHOTOS_DIR / "clubs_curated"
COMPETITIONS_DIR = PHOTOS_DIR / "competitions"
NATIONAL_DIR = PHOTOS_DIR / "national"

ROOT = Path(__file__).parent
PLAYERS_LIST_CSV = ROOT / "players_list.csv"
CLUBS_LIST_CSV = ROOT / "clubs_list.csv"
PLAYERS_ALL_FILE = DATA_DIR / "players_all.json"
PLAYER_NAME_OVERRIDES_FILE = DATA_DIR / "player_name_overrides.json"


def load_name_overrides() -> dict[str, dict]:
    """Carica overrides nome giocatore (TM alias errati). Filtra meta keys (_comment)."""
    if not PLAYER_NAME_OVERRIDES_FILE.exists():
        return {}
    raw = json.loads(PLAYER_NAME_OVERRIDES_FILE.read_text(encoding="utf-8"))
    return {k: v for k, v in raw.items() if not k.startswith("_") and isinstance(v, dict)}


def apply_name_override(p: dict, overrides: dict) -> bool:
    """Applica override nome a un giocatore. Ritorna True se modificato."""
    pid = str(p.get("tm_player_id"))
    if pid not in overrides:
        return False
    ov = overrides[pid]
    changed = False
    if "full_name" in ov and p.get("full_name") != ov["full_name"]:
        p["full_name"] = ov["full_name"]
        changed = True
    if "name_arabic" in ov and p.get("name_arabic") != ov["name_arabic"]:
        p["name_arabic"] = ov["name_arabic"]
        changed = True
    return changed


def _load(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _curated_player_face(sots_id=None, tm_id=None, lookup_path: str | None = None) -> str | None:
    """Cerca foto curata: per sots_id, lookup-id estratto dal path lookup, e tm_id come fallback."""
    candidates = []
    if sots_id:
        candidates.append(str(sots_id))
    if lookup_path:
        # estrae es. "23293811" da "photos/players_sots_lookup/23293811.png"
        import re
        m = re.search(r"(\d+)\.png$", str(lookup_path))
        if m:
            candidates.append(m.group(1))
    if tm_id:
        candidates.append(str(tm_id))
    for cand in candidates:
        p = PLAYERS_CURATED_DIR / f"{cand}.png"
        if p.exists():
            return p.relative_to(DATA_DIR).as_posix()
    return None


def _curated_club_logo(sots_team_id: int | None) -> str | None:
    if not sots_team_id:
        return None
    p = CLUBS_CURATED_DIR / f"{sots_team_id}.png"
    if p.exists():
        return p.relative_to(DATA_DIR).as_posix()
    return None


_CLUBS_INDEX_CACHE = None


def _build_clubs_index() -> dict:
    """Indicizza clubs.json per nome normalizzato → (tm_club_id, name)."""
    global _CLUBS_INDEX_CACHE
    if _CLUBS_INDEX_CACHE is not None:
        return _CLUBS_INDEX_CACHE
    clubs = _load(CLUBS_FILE) or []
    idx = {}
    for c in clubs:
        n = (c.get("name") or "").strip()
        if not n:
            continue
        idx[n.lower()] = (c["tm_club_id"], n)
        # senza suffissi tipo "FC", "SC", "SFC", "Club"
        n2 = n
        for suf in (" SFC", " FC", " SC", " Club"):
            n2 = n2.replace(suf, "")
        idx[n2.strip().lower()] = (c["tm_club_id"], n)
    _CLUBS_INDEX_CACHE = idx
    return idx


def _resolve_internal_transfer(name: str) -> tuple[int, str] | None:
    """Estrae es. 'Al-Nassr FC' da 'Internal transfer: Al-Nassr FC U17; date: 01/07/2025'
    e cerca match in clubs.json. Ritorna (tm_club_id, club_name) o None."""
    if not name:
        return None
    n = name.strip()
    for prefix in ("Internal transfer:", "Loan transfer:"):
        if n.startswith(prefix):
            n = n[len(prefix):].strip()
            break
    else:
        return None
    # rimuovi "; date: ..."
    if ";" in n:
        n = n.split(";", 1)[0].strip()
    # rimuovi suffissi categoria giovanile
    for suf in (" U14", " U15", " U16", " U17", " U18", " U19", " U20", " U21", " U23", " B"):
        if n.endswith(suf):
            n = n[: -len(suf)].strip()
    if not n:
        return None
    idx = _build_clubs_index()
    # match esatto
    if n.lower() in idx:
        return idx[n.lower()]
    # senza suffissi club
    n2 = n
    for suf in (" SFC", " FC", " SC", " Club"):
        n2 = n2.replace(suf, "")
    n2 = n2.strip().lower()
    if n2 in idx:
        return idx[n2]
    return None


def _resolve_youth_suffix(name: str) -> tuple[int, str] | None:
    """Se 'name' ha un suffisso giovanile (U17/U18/U19/U20/U21/U23/B), prova a matchare il senior.
    Es. 'Al-Qadsiah FC U18' → match con 'Al-Qadsiah FC' in clubs.json.
    """
    if not name:
        return None
    n = name.strip()
    suffix_found = False
    for suf in (" U14", " U15", " U16", " U17", " U18", " U19", " U20", " U21", " U23", " B"):
        if n.endswith(suf):
            n = n[: -len(suf)].strip()
            suffix_found = True
            break
    if not suffix_found or not n:
        return None
    idx = _build_clubs_index()
    if n.lower() in idx:
        return idx[n.lower()]
    n2 = n
    for suf in (" SFC", " FC", " SC", " Club"):
        n2 = n2.replace(suf, "")
    n2 = n2.strip().lower()
    if n2 in idx:
        return idx[n2]
    return None


_CLUB_OVERRIDES_CACHE = None
_PLAYER_OVERRIDES_CACHE = None


def _load_club_overrides() -> dict:
    """Carica data/club_overrides.json: mappa cid (str) -> {tm_club_id, name}."""
    global _CLUB_OVERRIDES_CACHE
    if _CLUB_OVERRIDES_CACHE is not None:
        return _CLUB_OVERRIDES_CACHE
    path = DATA_DIR / "club_overrides.json"
    out = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for k, v in data.items():
                if k.startswith("_"):
                    continue
                if not isinstance(v, dict):
                    continue
                tid = v.get("tm_club_id")
                name = v.get("name")
                if tid and name:
                    out[str(k)] = {"tm_club_id": tid, "name": name}
        except Exception as e:
            print(f"  [club_overrides.json] error: {e}")
    _CLUB_OVERRIDES_CACHE = out
    return out


def _load_player_overrides() -> dict:
    """Carica data/player_club_overrides.json: mappa tm_player_id (str) -> {tm_club_id, name}."""
    global _PLAYER_OVERRIDES_CACHE
    if _PLAYER_OVERRIDES_CACHE is not None:
        return _PLAYER_OVERRIDES_CACHE
    path = DATA_DIR / "player_club_overrides.json"
    out = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for k, v in data.items():
                if k.startswith("_"):
                    continue
                if not isinstance(v, dict):
                    continue
                tid = v.get("tm_club_id")
                name = v.get("name")
                if tid and name:
                    out[str(k)] = {"tm_club_id": tid, "name": name}
        except Exception as e:
            print(f"  [player_club_overrides.json] error: {e}")
    _PLAYER_OVERRIDES_CACHE = out
    return out


def fix_club_placeholder(profile: dict) -> bool:
    """Se current_club è placeholder o ha suffisso giovanile, prova a risolvere.

    Strategia in ordine:
      0. Override manuale via data/club_overrides.json (cid → senior tm_club_id+name)
      1. 'Internal transfer: X; date: Y' → parsa X e match con clubs.json
      2. 'X U18/U19/U20/U21/U23' → match con senior team
      3. Fallback: usa roster_club_id/name se disponibile e diverso dal placeholder
    """
    cur_name = profile.get("current_club_name")
    cur_id = profile.get("current_club_id")
    pid = profile.get("tm_player_id")

    # 0a. Override per-giocatore (priorità massima)
    player_overrides = _load_player_overrides()
    pov = player_overrides.get(str(pid)) if pid is not None else None
    if pov:
        if profile.get("current_club_id") != pov["tm_club_id"]:
            profile["current_club_id_original"] = profile.get("current_club_id")
            profile["current_club_name_original"] = profile.get("current_club_name")
        profile["current_club_id"] = pov["tm_club_id"]
        profile["current_club_name"] = pov["name"]
        return True

    # 0b. Override per current_club_id
    overrides = _load_club_overrides()
    ov = overrides.get(str(cur_id)) if cur_id is not None else None
    if ov:
        if profile.get("current_club_id") != ov["tm_club_id"]:
            profile["current_club_id_original"] = profile.get("current_club_id")
            profile["current_club_name_original"] = profile.get("current_club_name")
        profile["current_club_id"] = ov["tm_club_id"]
        profile["current_club_name"] = ov["name"]
        return True

    # 1. Internal transfer pattern
    resolved = _resolve_internal_transfer(cur_name) if cur_name else None
    if not resolved and is_placeholder_club(cur_name):
        resolved = _resolve_internal_transfer(profile.get("roster_club_name") or "")

    # 2. Youth suffix pattern (senza "Internal transfer:")
    if not resolved and cur_name:
        resolved = _resolve_youth_suffix(cur_name)

    if resolved:
        cid, cname = resolved
        profile["current_club_id_original"] = profile.get("current_club_id")
        profile["current_club_name_original"] = profile.get("current_club_name")
        profile["current_club_id"] = cid
        profile["current_club_name"] = cname
        return True

    # 3. Fallback su roster_club se non placeholder e current è placeholder
    if is_placeholder_club(cur_name):
        roster_id = profile.get("roster_club_id")
        roster_name = profile.get("roster_club_name")
        if roster_id and roster_name and not is_placeholder_club(roster_name):
            profile["current_club_id_original"] = profile.get("current_club_id")
            profile["current_club_name_original"] = profile.get("current_club_name")
            profile["current_club_id"] = roster_id
            profile["current_club_name"] = roster_name
            return True
    return False


def main() -> None:
    print(f"Loading lookups from CSV...")
    sots_player_lookup = load_sortitoutsi_mapping(PLAYERS_LIST_CSV)
    sots_team_lookup = load_sortitoutsi_team_mapping(CLUBS_LIST_CSV)
    name_overrides = load_name_overrides()
    print(f"  players mapping: {len(sots_player_lookup)} entries")
    print(f"  clubs mapping  : {len(sots_team_lookup)} entries")
    print(f"  name overrides : {len(name_overrides)} entries")

    # CLUBS
    clubs = _load(CLUBS_FILE)
    if clubs:
        for c in clubs:
            enrich_club(c, sots_team_lookup)
            curated = _curated_club_logo(c.get("sortitoutsi_team_id"))
            if curated:
                c["sortitoutsi_logo_local_curated"] = curated
            elif c.get("sortitoutsi_logo_local_curated"):
                c.pop("sortitoutsi_logo_local_curated", None)
        _save(CLUBS_FILE, clubs)
        n_with_id = sum(1 for c in clubs if c.get("sortitoutsi_team_id"))
        n_curated = sum(1 for c in clubs if c.get("sortitoutsi_logo_local_curated"))
        print(f"  clubs.json: {n_with_id}/{len(clubs)} con sortitoutsi_team_id, {n_curated} con logo curato")

    def enrich_dataset(players: list[dict]) -> dict:
        n_face = n_face_curated = n_fix_club = n_name_override = 0
        for p in players:
            enrich_profile(p, sots_player_lookup)
            # Applica override nome (TM alias errati)
            if apply_name_override(p, name_overrides):
                n_name_override += 1
            # Pulisci stale entries: anche club_logo se file rimosso
            curated = _curated_player_face(
                sots_id=p.get("sortitoutsi_person_id"),
                tm_id=p.get("tm_player_id"),
                lookup_path=p.get("sortitoutsi_face_local_lookup"),
            )
            # Sincronizza il flag: rimuovi se file curato non esiste più
            if not curated and p.get("sortitoutsi_face_local_curated"):
                p.pop("sortitoutsi_face_local_curated", None)
            if curated:
                p["sortitoutsi_face_local_curated"] = curated
                n_face_curated += 1
            if p.get("sortitoutsi_face_url"):
                n_face += 1
            if fix_club_placeholder(p):
                n_fix_club += 1
        return {"face": n_face, "face_curated": n_face_curated, "fix_club": n_fix_club, "name_override": n_name_override}

    # ALL PROFILES
    players_all = _load(PLAYERS_ALL_FILE)
    if players_all:
        s = enrich_dataset(players_all)
        _save(PLAYERS_ALL_FILE, players_all)
        print(f"  players_all.json: {s['face']}/{len(players_all)} face URL, "
              f"{s['face_curated']} face curate, {s['fix_club']} club fixed, "
              f"{s['name_override']} name overrides")

    # MAIN
    main = _load(PLAYERS_MAIN_FILE)
    if main:
        s = enrich_dataset(main)
        _save(PLAYERS_MAIN_FILE, main)
        _save(PLAYERS_STATIC_FILE, main)
        print(f"  players_main.json: {s['face']}/{len(main)} face URL, "
              f"{s['face_curated']} face curate, {s['fix_club']} club fixed")

    print("\nFatto.")


if __name__ == "__main__":
    main()

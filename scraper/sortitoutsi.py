"""
Arricchimento profili con URL foto da sortitoutsi.net (face FM-style).

L'utente ha curato a mano un mapping tm_player_id -> sortitoutsi_person_id
in players_list.csv. Questo modulo:

- Carica il mapping dal CSV
- Costruisce l'URL face: https://sortitoutsi.b-cdn.net/uploads/face/face_{sotsId}.png
- Aggiunge ai profili scrapati i campi:
    sortitoutsi_person_id (int o None)
    sortitoutsi_face_url   (str  o None)
    sortitoutsi_profile_url (str o None)
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional


def _slugify(name: str) -> str:
    """Slug pulito per URL sortitoutsi: lowercase, spazi -> trattini."""
    if not name:
        return ""
    s = name.lower().strip()
    s = s.replace("'", "").replace(".", "")
    out = []
    for ch in s:
        if ch.isalnum():
            out.append(ch)
        elif ch in (" ", "-", "_"):
            out.append("-")
    slug = "".join(out)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


def load_sortitoutsi_mapping(csv_path: Path) -> dict[int, int]:
    """
    Legge players_list.csv (separatore ;) e ritorna {tm_player_id: sortitoutsi_person_id}.
    Salta righe senza sortitoutsi_person_id valido.
    """
    mapping: dict[int, int] = {}
    if not csv_path.exists():
        return mapping
    with csv_path.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            tm_id_raw = (row.get("tm_player_id") or "").strip()
            sots_raw = (row.get("sortitoutsi_person_id") or "").strip()
            if not tm_id_raw or not sots_raw:
                continue
            try:
                tm_id = int(tm_id_raw)
                sots_id = int(sots_raw)
            except ValueError:
                continue
            mapping[tm_id] = sots_id
    return mapping


def load_sortitoutsi_team_mapping(csv_path: Path) -> dict[str, int]:
    """
    Legge clubs_list.csv (separatore ;) e ritorna {club_name: sortitoutsi_team_id}.
    """
    mapping: dict[str, int] = {}
    if not csv_path.exists():
        return mapping
    with csv_path.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            name = (row.get("club") or "").strip()
            sots_raw = (row.get("sortitoutsi_team_id") or "").strip()
            if not name or not sots_raw:
                continue
            try:
                mapping[name] = int(sots_raw)
            except ValueError:
                continue
    return mapping


PLACEHOLDER_CLUB_NAMES = {
    "New arrival",
    "Winter signing",
    "Returnee",
    "",
}


def is_placeholder_club(name: Optional[str]) -> bool:
    if name is None:
        return True
    n = name.strip()
    if n in PLACEHOLDER_CLUB_NAMES:
        return True
    # Pattern come "Internal transfer: Al-Hilal U19; date: 01/07/2025"
    if n.startswith("Internal transfer:") or n.startswith("Loan transfer:"):
        return True
    return False


def face_url(sots_id: Optional[int]) -> Optional[str]:
    if not sots_id:
        return None
    return f"https://sortitoutsi.b-cdn.net/uploads/face/face_{sots_id}.png"


def team_logo_url(sots_team_id: Optional[int]) -> Optional[str]:
    if not sots_team_id:
        return None
    return f"https://sortitoutsi.b-cdn.net/uploads/team/{sots_team_id}.png"


def profile_url(sots_id: Optional[int], full_name: Optional[str]) -> Optional[str]:
    if not sots_id:
        return None
    slug = _slugify(full_name or "")
    base = f"https://sortitoutsi.net/football-manager-2026/person/{sots_id}"
    return f"{base}/{slug}" if slug else base


def enrich_profile(profile: dict, sots_id_lookup: dict[int, int]) -> dict:
    """Aggiunge i campi sortitoutsi al profilo (in-place + ritorna)."""
    pid = profile.get("tm_player_id")
    sots_id = sots_id_lookup.get(int(pid)) if pid is not None else None
    profile["sortitoutsi_person_id"] = sots_id
    profile["sortitoutsi_face_url"] = face_url(sots_id)
    profile["sortitoutsi_profile_url"] = profile_url(sots_id, profile.get("full_name"))
    return profile


def enrich_club(club: dict, sots_team_lookup: dict[str, int]) -> dict:
    name = club.get("name") or ""
    sots_team_id = sots_team_lookup.get(name)
    club["sortitoutsi_team_id"] = sots_team_id
    club["sortitoutsi_logo_url"] = team_logo_url(sots_team_id)
    return club

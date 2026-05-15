"""
download_photos.py — Scarica in locale foto giocatori e loghi club.

Per ogni giocatore in data/players_main.json scarica:
- photo_url di Transfermarkt        -> data/photos/players_tm/{tm_player_id}.<ext>
- sortitoutsi_face_url               -> data/photos/players_sots/{tm_player_id}.png

Per ogni club in data/clubs.json scarica:
- logo_url di Transfermarkt          -> data/photos/clubs_tm/{tm_club_id}.<ext>
- sortitoutsi_logo_url                -> data/photos/clubs_sots/{tm_club_id}.png

Aggiunge ai JSON i campi *_local con il path relativo (es. "photos/players_tm/195332.png").

Resume:
- Skip automatico se il file esiste già e ha dimensione > 200 byte (non placeholder).
- Lanciabile più volte: scarica solo i mancanti.

Uso:
    source venv/bin/activate
    python3 download_photos.py
    python3 download_photos.py --refresh   # forza re-download
"""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _bootstrap  # noqa: F401  (auto-attiva venv del progetto se necessario)

import json
import time
from typing import Optional

import requests

from scraper.config import (
    CLUBS_FILE,
    DATA_DIR,
    PLAYERS_MAIN_FILE,
    PLAYERS_STATIC_FILE,
    SLEEP_BETWEEN_REQUESTS,
    USER_AGENTS,
)

PHOTOS_DIR = DATA_DIR / "photos"
DIRS = {
    "players_tm":   PHOTOS_DIR / "players_tm",
    "players_sots": PHOTOS_DIR / "players_sots",
    "clubs_tm":     PHOTOS_DIR / "clubs_tm",
    "clubs_sots":   PHOTOS_DIR / "clubs_sots",
}
PLAYERS_CURATED_DIR = PHOTOS_DIR / "players_curated"
CLUBS_CURATED_DIR = PHOTOS_DIR / "clubs_curated"
for d in DIRS.values():
    d.mkdir(parents=True, exist_ok=True)


def _has_curated_face(sots_id) -> bool:
    if not sots_id:
        return False
    return (PLAYERS_CURATED_DIR / f"{sots_id}.png").exists()


def _has_curated_logo(sots_team_id) -> bool:
    if not sots_team_id:
        return False
    return (CLUBS_CURATED_DIR / f"{sots_team_id}.png").exists()

PLAYERS_ALL_FILE = DATA_DIR / "players_all.json"

# Considera "default photo" se ha pattern URL Transfermarkt 'default' (placeholder)
TM_DEFAULT_MARKERS = ("/portrait/header/default.", "/wappen/tiny/default.", "default.png")
MIN_FILE_SIZE = 200  # bytes; sotto è probabilmente errore o redirect a placeholder


def _ext_from_url(url: str) -> str:
    url_clean = url.split("?")[0].lower()
    for ext in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
        if url_clean.endswith(ext):
            return ext
    return ".png"


def _is_default_url(url: Optional[str]) -> bool:
    if not url:
        return True
    return any(m in url for m in TM_DEFAULT_MARKERS)


def _load(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


class Downloader:
    def __init__(self, sleep: float = 0.4) -> None:
        self.session = requests.Session()
        self.sleep = sleep
        self.stats = {"downloaded": 0, "cached": 0, "skipped": 0, "failed": 0}

    def fetch(self, url: str, dest: Path, *, refresh: bool = False) -> Optional[Path]:
        if dest.exists() and dest.stat().st_size > MIN_FILE_SIZE and not refresh:
            self.stats["cached"] += 1
            return dest
        if _is_default_url(url):
            self.stats["skipped"] += 1
            return None
        try:
            headers = {
                "User-Agent": USER_AGENTS[0],
                "Accept": "image/webp,image/png,image/jpeg,*/*",
                "Referer": "https://www.transfermarkt.com/",
            }
            r = self.session.get(url, headers=headers, timeout=20)
            if r.status_code != 200:
                self.stats["failed"] += 1
                return None
            data = r.content
            if len(data) < MIN_FILE_SIZE:
                self.stats["skipped"] += 1
                return None
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            self.stats["downloaded"] += 1
            time.sleep(self.sleep)
            return dest
        except Exception as e:
            print(f"    [error] {url}: {type(e).__name__}: {e}")
            self.stats["failed"] += 1
            return None


def relative_path(p: Path) -> str:
    """Path relativo a DATA_DIR usato dal frontend."""
    return p.relative_to(DATA_DIR).as_posix()


def download_player_photos(players: list[dict], dl: Downloader, refresh: bool) -> None:
    print(f"\n=== Download foto giocatori ({len(players)}) ===")
    for i, p in enumerate(players, 1):
        pid = p.get("tm_player_id")
        if not pid:
            continue

        # TM photo
        photo_url = p.get("photo_url")
        if photo_url and not _is_default_url(photo_url):
            ext = _ext_from_url(photo_url)
            dest = DIRS["players_tm"] / f"{pid}{ext}"
            res = dl.fetch(photo_url, dest, refresh=refresh)
            if res or dest.exists():
                p["photo_local"] = relative_path(dest)

        # Sortitoutsi face — SKIP se foto curata locale già presente
        sots_id = p.get("sortitoutsi_person_id")
        if not _has_curated_face(sots_id):
            sots_url = p.get("sortitoutsi_face_url")
            if sots_url:
                dest = DIRS["players_sots"] / f"{pid}.png"
                # Se è cambiato il sots_id, l'URL nel JSON contiene il nuovo id ma il file
                # potrebbe essere quello vecchio. Cancella il file se è "sospetto"
                # (più piccolo del minimo o data di creazione molto vecchia rispetto all'URL).
                # Pattern conservativo: se la mappatura tracker dice che il file è obsoleto,
                # il caller può passare --refresh.
                res = dl.fetch(sots_url, dest, refresh=refresh)
                if res or dest.exists():
                    p["sortitoutsi_face_local"] = relative_path(dest)

        if i % 25 == 0 or i == len(players):
            print(f"  [{i}/{len(players)}]  dl={dl.stats['downloaded']} cached={dl.stats['cached']} "
                  f"skip={dl.stats['skipped']} fail={dl.stats['failed']}")


def download_club_logos(clubs: list[dict], dl: Downloader, refresh: bool) -> None:
    print(f"\n=== Download loghi club ({len(clubs)}) ===")
    for c in clubs:
        cid = c.get("tm_club_id")
        if not cid:
            continue

        # TM logo
        logo = c.get("logo_url")
        if logo and not _is_default_url(logo):
            ext = _ext_from_url(logo)
            dest = DIRS["clubs_tm"] / f"{cid}{ext}"
            res = dl.fetch(logo, dest, refresh=refresh)
            if res or dest.exists():
                c["logo_local"] = relative_path(dest)

        # Sortitoutsi logo — SKIP se logo curato locale già presente
        sots_team_id = c.get("sortitoutsi_team_id")
        if not _has_curated_logo(sots_team_id):
            sots_logo = c.get("sortitoutsi_logo_url")
            if sots_logo:
                dest = DIRS["clubs_sots"] / f"{cid}.png"
                res = dl.fetch(sots_logo, dest, refresh=refresh)
                if res or dest.exists():
                    c["sortitoutsi_logo_local"] = relative_path(dest)

    print(f"  done: dl={dl.stats['downloaded']} cached={dl.stats['cached']} "
          f"skip={dl.stats['skipped']} fail={dl.stats['failed']}")


def main() -> None:
    refresh = "--refresh" in sys.argv
    dl = Downloader(sleep=0.4)

    # Players (main)
    main = _load(PLAYERS_MAIN_FILE) or []
    download_player_photos(main, dl, refresh)
    _save(PLAYERS_MAIN_FILE, main)
    _save(PLAYERS_STATIC_FILE, main)

    # Players (tutti — per coerenza, anche fuori-target possono comparire altrove)
    all_players = _load(PLAYERS_ALL_FILE) or []
    if all_players:
        # Riusa stesso downloader; i main sono già cached.
        download_player_photos(all_players, dl, refresh)
        _save(PLAYERS_ALL_FILE, all_players)

    # Clubs
    clubs = _load(CLUBS_FILE) or []
    download_club_logos(clubs, dl, refresh)
    _save(CLUBS_FILE, clubs)

    print(f"\n{'='*60}")
    print(f"Totale: dl={dl.stats['downloaded']}  cached={dl.stats['cached']}  "
          f"skip={dl.stats['skipped']}  fail={dl.stats['failed']}")


if __name__ == "__main__":
    main()

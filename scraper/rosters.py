"""Estrae la rosa di un club (lista di tm_player_id)."""

import re
from typing import Optional

from bs4 import BeautifulSoup

from .config import BASE_URL
from .http_client import TransfermarktClient


def parse_club_roster(html: str, club_id: int, club_name: str) -> list[dict]:
    """Parsa la pagina rosa di un club."""
    soup = BeautifulSoup(html, "lxml")
    out: list[dict] = []
    seen: set[int] = set()

    table = soup.find("table", class_="items")
    if table is None:
        return out

    for row in table.select("tbody > tr"):
        link = row.select_one('a[href*="/profil/spieler/"]')
        if not link:
            continue
        href = link.get("href", "") or ""
        m = re.search(r"/profil/spieler/(\d+)", href)
        if not m:
            continue
        pid = int(m.group(1))
        if pid in seen:
            continue
        name_hint = link.get_text(strip=True)
        # Numero di maglia
        shirt_el = row.select_one('.rn_nummer, [class*="rueckennummer"]')
        shirt = shirt_el.get_text(strip=True) if shirt_el else None
        out.append({
            "tm_player_id": pid,
            "name_hint": name_hint,
            "tm_club_id": club_id,
            "club_name": club_name,
            "profile_url": (BASE_URL + href) if href.startswith("/") else href,
            "shirt_number_hint": shirt,
        })
        seen.add(pid)
    return out


def scrape_club_roster(
    club: dict,
    client: Optional[TransfermarktClient] = None,
) -> list[dict]:
    """Scarica e parsa la rosa di un club. `club` è un dict da scrape_all_leagues."""
    client = client or TransfermarktClient()
    print(f"[roster] {club['name']}")
    html = client.get_html(club["club_url"])
    roster = parse_club_roster(html, club["tm_club_id"], club["name"])
    print(f"[roster] {club['name']}: {len(roster)} players")
    return roster

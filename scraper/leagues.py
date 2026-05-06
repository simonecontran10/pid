"""Estrae la lista club di una lega (Saudi Pro League, First Division)."""

import re
from typing import Optional

from bs4 import BeautifulSoup

from .config import BASE_URL, LEAGUES
from .http_client import TransfermarktClient


def parse_league_clubs(html: str, league_id: str, league_name: str) -> list[dict]:
    """Parsa la tabella della lega ed estrae i club."""
    soup = BeautifulSoup(html, "lxml")
    out: list[dict] = []
    seen: set[str] = set()

    table = soup.find("table", class_="items")
    if table is None:
        return out

    for row in table.select("tbody > tr"):
        for a in row.select('a[href*="/startseite/verein/"]'):
            href = a.get("href", "") or ""
            m = re.search(r"/verein/(\d+)", href)
            if not m:
                continue
            club_id = m.group(1)
            name = (a.get("title") or a.get_text(strip=True)).strip()
            if not name or club_id in seen:
                continue
            # Logo del club: prima img dentro il link
            logo_img = a.find("img")
            logo_url = None
            if logo_img:
                logo_url = logo_img.get("src") or logo_img.get("data-src")
                if logo_url and logo_url.startswith("//"):
                    logo_url = "https:" + logo_url
            out.append({
                "tm_club_id": int(club_id),
                "name": name,
                "league_id": league_id,
                "league_name": league_name,
                "club_url": BASE_URL + href if href.startswith("/") else href,
                "logo_url": logo_url,
            })
            seen.add(club_id)
    return out


def scrape_all_leagues(client: Optional[TransfermarktClient] = None) -> list[dict]:
    """Scarica e parsa entrambe le leghe (SA1, SA2)."""
    client = client or TransfermarktClient()
    all_clubs: list[dict] = []
    for league_id, info in LEAGUES.items():
        print(f"[league] fetching {league_id} {info['name']}")
        html = client.get_html(info["url"])
        clubs = parse_league_clubs(html, league_id, info["name"])
        print(f"[league] {league_id}: found {len(clubs)} clubs")
        all_clubs.extend(clubs)
    return all_clubs

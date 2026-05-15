"""Estrae la lista club di una lega da Transfermarkt."""

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


def scrape_club_by_id(tm_club_id: int, client=None) -> dict | None:
    """Scrape dettagli di un singolo club dato il tm_club_id.
    
    Restituisce dict compatibile con clubs.json, oppure None se fallisce.
    Usato da add_players.py per auto-creare club non presenti nel DB.
    """
    from bs4 import BeautifulSoup
    import re
    client = client or TransfermarktClient()
    
    # URL placeholder con slug 'unknown' (TM redirige al canonical)
    url = f"{BASE_URL}/club/startseite/verein/{tm_club_id}"
    try:
        html = client.get_html(url)
    except Exception as e:
        print(f"[club {tm_club_id}] fetch failed: {e}")
        return None
    
    soup = BeautifulSoup(html, "lxml")
    
    # Nome club: dal data-header
    name_el = soup.select_one("h1.data-header__headline-wrapper, h1.data-header__headline")
    name = name_el.get_text(strip=True) if name_el else None
    
    # League: cerca DENTRO il blocco data-header (info principale del club)
    # NON usare select_one('a[href*="/wettbewerb/"]') generico perché beccherebbe
    # il PRIMO link wettbewerb della pagina che e' sempre /uefa-champions-league/wettbewerb/CL
    # (banner top-nav di TM, presente su OGNI pagina club).
    # Fix 11 mag 2026: usa data-header come scope + fallback most_common.
    league_name = None
    league_id = None
    header = soup.select_one('header.data-header, .data-header')
    if header:
        # Cerca tutti i link wettbewerb dentro data-header
        # Il primo a volte ha text=vuoto (e' un logo-only link), quello dopo ha il nome.
        # Strategia: prendo league_id dal primo link, e league_name dal primo link CON testo.
        links = header.select('a[href*="/wettbewerb/"]')
        for a in links:
            href = a.get("href", "")
            if not league_id:
                m = re.search(r"/wettbewerb/([A-Z0-9]+)", href)
                if m:
                    league_id = m.group(1)
            if not league_name:
                txt = a.get_text(strip=True) or a.get("title") or ""
                # Skippa label tipo "17", "Second Tier" che sono campi statistici, non nomi lega
                if txt and not txt.isdigit() and txt.lower() not in ("first tier", "second tier", "third tier", "fourth tier"):
                    league_name = txt
            if league_id and league_name:
                break
    # Fallback: most common wettbewerb id sull'intera pagina
    # (la lega del club appare 5+ volte, le top-nav league solo 1-2)
    if not league_id:
        from collections import Counter
        matches = re.findall(r"/wettbewerb/([A-Z0-9]+)", str(soup))
        if matches:
            c = Counter(matches)
            league_id = c.most_common(1)[0][0]
            # Cerca un link con quel league_id per estrarre il nome
            link = soup.select_one(f'a[href*="/wettbewerb/{league_id}"]')
            if link and not league_name:
                league_name = link.get_text(strip=True) or link.get("title")
    
    # Logo del club: dal data-header
    logo_el = soup.select_one('.data-header__profile-image, .dataBild img, img.dataBild')
    logo_url = None
    if logo_el:
        logo_url = logo_el.get("src") or logo_el.get("data-src")
        if logo_url and logo_url.startswith("//"):
            logo_url = "https:" + logo_url
    
    # Slug dall'URL canonico (cerco un link self)
    slug = None
    canonical = soup.select_one('link[rel="canonical"]')
    if canonical:
        href = canonical.get("href", "")
        m = re.search(r"/([a-z0-9-]+)/startseite/verein/", href)
        if m:
            slug = m.group(1)
    
    if not name:
        print(f"[club {tm_club_id}] failed to extract name")
        return None
    
    return {
        "tm_club_id": int(tm_club_id),
        "name": name,
        "league_id": league_id or "UNKNOWN",
        "league_name": league_name or "Unknown",
        "club_url": url,
        "slug": slug,
        "sortitoutsi_team_id": None,
        "sortitoutsi_logo_url": None,
        "sortitoutsi_logo_local": None,
        "logo_url": logo_url,
    }


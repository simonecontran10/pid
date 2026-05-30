"""
Scarica i top trasferimenti TM per le ultime N stagioni.

Output: CSV con colonne
  season, rank, name, role, age, market_value, nat1, nat2,
  from_club, from_league, to_club, to_league, fee
"""
from __future__ import annotations
import csv
import sys
import re
from pathlib import Path
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent))
from scraper.http_client import TransfermarktClient  # noqa: E402

BASE_URL = (
    "https://www.transfermarkt.com/transfers/saisontransfers/statistik/top"
    "/saison_id/{season}/transferfenster/alle/plus/1/galerie/0/page/{page}"
)

PER_PAGE = 25  # TM mostra 25 righe per pagina


def parse_page(html: str, season: str) -> list[dict]:
    """Estrae le righe trasferimento da una pagina TM."""
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", class_="items")
    if not table:
        return []
    rows = []
    for tr in table.find_all("tr", class_=["odd", "even"]):
        cells = tr.find_all("td", recursive=False)
        if len(cells) < 8:
            continue
        # rank
        rank = cells[0].get_text(strip=True)
        # player: link "hauptlink" → nome; ruolo nella riga sotto.
        # Estraggo anche tm_player_id da href tipo "/player-slug/profil/spieler/123".
        name_a = cells[1].find("a", class_=lambda c: c and "hauptlink" in c) or cells[1].find("a")
        name = name_a.get_text(strip=True) if name_a else ""
        tm_player_id = ""
        if name_a:
            href = name_a.get("href", "") or ""
            m = re.search(r"/spieler/(\d+)", href)
            if m:
                tm_player_id = m.group(1)
        # Ruolo: cerca un <td> figlio della tabella nested con testo "ruolo"
        role = ""
        nested = cells[1].find("table")
        if nested:
            # ultima riga della tabella nested ha il ruolo
            trs = nested.find_all("tr")
            if len(trs) >= 2:
                role = trs[-1].get_text(strip=True)
        # age
        age = cells[2].get_text(strip=True)
        # market value
        mv = cells[3].get_text(strip=True)
        # nationalities: img title (può essere più di una)
        nat_imgs = cells[4].find_all("img")
        nats = [img.get("title", "").strip() for img in nat_imgs if img.get("title")]
        nat1 = nats[0] if nats else ""
        nat2 = nats[1] if len(nats) > 1 else ""
        # from club / league
        from_club, from_league = _split_club_league(cells[5])
        # to club / league
        to_club, to_league = _split_club_league(cells[6])
        # fee
        fee = cells[7].get_text(strip=True)
        rows.append({
            "season": season,
            "rank": rank,
            "tm_player_id": tm_player_id,
            "name": name,
            "role": role,
            "age": age,
            "market_value": mv,
            "nat1": nat1,
            "nat2": nat2,
            "from_club": from_club,
            "from_league": from_league,
            "to_club": to_club,
            "to_league": to_league,
            "fee": fee,
        })
    return rows


def _split_club_league(cell) -> tuple[str, str]:
    """In una cella TM del 'da/a club' ci sono 3 <a>:
       - link col logo (text vuoto, solo <img>)
       - link col nome club (text)
       - link con nome lega (text)
       Filtro solo i link con testo non vuoto: primo=club, secondo=lega.
    """
    text_links = [a for a in cell.find_all("a") if a.get_text(strip=True)]
    if len(text_links) >= 2:
        return text_links[0].get_text(strip=True), text_links[1].get_text(strip=True)
    if len(text_links) == 1:
        return text_links[0].get_text(strip=True), ""
    return "", ""


def scrape(seasons: list[int], rows_per_season: int, output_csv: Path) -> None:
    client = TransfermarktClient()
    pages_per_season = (rows_per_season + PER_PAGE - 1) // PER_PAGE
    all_rows: list[dict] = []
    for season in seasons:
        season_label = f"{season}/{(season + 1) % 100:02d}"
        print(f"=== Stagione {season_label} ({pages_per_season} pagine) ===")
        season_rows: list[dict] = []
        for page in range(1, pages_per_season + 1):
            url = BASE_URL.format(season=season, page=page)
            print(f"  Pagina {page}…", end=" ", flush=True)
            try:
                html = client.get_html(url)
                rows = parse_page(html, season_label)
                season_rows.extend(rows)
                print(f"+{len(rows)} (totale stagione: {len(season_rows)})")
            except Exception as e:
                print(f"ERR {type(e).__name__}: {e}")
                continue
            if len(season_rows) >= rows_per_season:
                break
        # tronco al numero richiesto
        season_rows = season_rows[:rows_per_season]
        all_rows.extend(season_rows)
        print(f"  → {len(season_rows)} trasferimenti raccolti")

    # Scrivo CSV
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as fp:
        fieldnames = [
            "season", "rank", "tm_player_id", "name", "role", "age", "market_value",
            "nat1", "nat2", "from_club", "from_league",
            "to_club", "to_league", "fee",
        ]
        w = csv.DictWriter(fp, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(all_rows)
    print(f"\n✓ {len(all_rows)} righe → {output_csv}")


if __name__ == "__main__":
    # Ultime 3 stagioni: 2025/26, 2024/25, 2023/24
    seasons = [2025, 2024, 2023]
    rows_per_season = 150
    output = Path("/Users/simone/Desktop/transfers_top_3seasons.csv")
    scrape(seasons, rows_per_season, output)

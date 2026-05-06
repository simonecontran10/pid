"""Scrappa la pagina di una lega Transfermarkt e tira fuori i club.
Uso: python3 scrape_league_clubs.py <slug-url> <league_code>
Es:  python3 scrape_league_clubs.py serie-b IT2
     python3 scrape_league_clubs.py campionato-primavera-1 PRIM
"""
import re, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import _bootstrap  # noqa

from bs4 import BeautifulSoup
from scraper.http_client import TransfermarktClient
from scraper.config import BASE_URL

if len(sys.argv) < 3:
    print("Uso: python3 scrape_league_clubs.py <slug-url> <league_code>")
    sys.exit(1)

slug = sys.argv[1]
code = sys.argv[2]
url = f"{BASE_URL}/{slug}/startseite/wettbewerb/{code}/saison_id/2025"

print(f"[fetch] {url}")
client = TransfermarktClient()
html = client.get_html(url)

soup = BeautifulSoup(html, "lxml")
clubs, seen = [], set()
for a in soup.select("table.items a[href*='/startseite/verein/']"):
    href = a.get("href", "")
    m = re.search(r"/([^/]+)/startseite/verein/(\d+)", href)
    if not m: continue
    slug_c, cid = m.group(1), int(m.group(2))
    if cid in seen: continue
    name = a.get_text(strip=True)
    if not name: continue
    seen.add(cid)
    clubs.append({
        "tm_club_id": cid,
        "name": name,
        "slug": slug_c,
        "league_id": code,
        "club_url": f"{BASE_URL}{href}" if href.startswith("/") else href,
    })

print(f"\n[result] trovati {len(clubs)} club ({code}):")
for c in clubs:
    print(f"  {c['tm_club_id']:>6}  {c['name']}")

out = Path(f"data/{code.lower()}_clubs.json")
out.write_text(json.dumps(clubs, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\n[saved] {out}")

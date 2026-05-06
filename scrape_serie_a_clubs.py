"""Scrappa la pagina della Serie A 2025/26 da Transfermarkt e tira fuori
la lista dei 20 club con tm_club_id, nome e URL pagina rosa."""
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import _bootstrap  # noqa

from bs4 import BeautifulSoup
from scraper.http_client import TransfermarktClient
from scraper.config import BASE_URL

# URL pagina lega
LEAGUE_URL = f"{BASE_URL}/serie-a/startseite/wettbewerb/IT1/saison_id/2025"

client = TransfermarktClient()
print(f"[fetch] {LEAGUE_URL}")
html = client.get_html(LEAGUE_URL)

soup = BeautifulSoup(html, "lxml")
clubs = []
seen = set()

# Cerca tutti i link a pagine club nella tabella squadre
for a in soup.select("table.items a[href*='/startseite/verein/']"):
    href = a.get("href", "")
    m = re.search(r"/([^/]+)/startseite/verein/(\d+)", href)
    if not m:
        continue
    slug = m.group(1)
    cid = int(m.group(2))
    if cid in seen:
        continue
    name = a.get_text(strip=True)
    if not name:
        continue
    seen.add(cid)
    clubs.append({
        "tm_club_id": cid,
        "name": name,
        "slug": slug,
        "club_url": f"{BASE_URL}{href}" if href.startswith("/") else href,
    })

print(f"\n[result] trovati {len(clubs)} club:")
for c in clubs:
    print(f"  {c['tm_club_id']:>6}  {c['name']}")

# Salva
out = Path("data/serie_a_clubs.json")
out.parent.mkdir(exist_ok=True)
import json
out.write_text(json.dumps(clubs, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\n[saved] {out}")

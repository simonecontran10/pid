"""Scarica i loghi competizione da Transfermarkt."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import _bootstrap  # noqa

import requests
from scraper.http_client import TransfermarktClient

# URL diretti dei loghi competizione TM
LOGOS = {
    "IT1":  "https://tmssl.akamaized.net/images/logo/header/it1.png",
    "IT2":  "https://tmssl.akamaized.net/images/logo/header/it2.png",
    "IJ1":  "https://tmssl.akamaized.net/images/logo/header/ij1.png",
    "CIT":  "https://tmssl.akamaized.net/images/logo/header/cit.png",
    "SCI":  "https://tmssl.akamaized.net/images/logo/header/sci.png",
    "CL":   "https://tmssl.akamaized.net/images/logo/header/cl.png",
    "EL":   "https://tmssl.akamaized.net/images/logo/header/el.png",
    "UECL": "https://tmssl.akamaized.net/images/logo/header/uecl.png",
}

out_dir = Path("data/photos/competitions")
out_dir.mkdir(parents=True, exist_ok=True)

# Pulisco i vecchi loghi sauditi non più usati
for old in ["SA1.png", "SA2L.png", "SAKC.png", "SASS.png", "SAU21.png", "SDL.png", "23AF.png"]:
    p = out_dir / old
    if p.exists():
        p.unlink()
        print(f"  rm {old}")

client = TransfermarktClient()
for code, url in LOGOS.items():
    out = out_dir / f"{code}.png"
    if out.exists():
        print(f"  cached {code}")
        continue
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        r.raise_for_status()
        out.write_bytes(r.content)
        print(f"  ✓ {code} ({len(r.content)} bytes)")
    except Exception as e:
        print(f"  ✗ {code}: {e}")

print()
print("=== Loghi competizione finali ===")
for f in sorted(out_dir.iterdir()):
    print(f"  {f.name:>15}  {f.stat().st_size:>6} bytes")

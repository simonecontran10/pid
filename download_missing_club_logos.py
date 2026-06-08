"""Scarica i loghi TM ufficiali per tutti i club senza logo locale.

Endpoint TM: https://tmssl.akamaized.net/images/wappen/head/<tm_club_id>.png
Output: data/photos/clubs_sots/<tm_club_id>.png (mantiene cartella esistente)

Idempotente: skippa club che hanno già il file.
"""
import json, time, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
OUT = DATA / "photos" / "clubs_sots"
OUT.mkdir(parents=True, exist_ok=True)

clubs = json.loads((DATA / "clubs.json").read_text(encoding="utf-8"))
todo = []
for c in clubs:
    tm_id = c.get("tm_club_id")
    if not tm_id:
        continue
    out = OUT / f"{tm_id}.png"
    if out.exists() and out.stat().st_size > 500:
        continue
    todo.append((tm_id, c.get("name", "?")))

print(f"Da scaricare: {len(todo)}/{len(clubs)} club")
ok = fail = 0
for i, (tm_id, name) in enumerate(todo, 1):
    url = f"https://tmssl.akamaized.net/images/wappen/head/{tm_id}.png"
    out = OUT / f"{tm_id}.png"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            if len(data) < 500:  # placeholder TM è ~200 bytes
                fail += 1
                continue
            out.write_bytes(data)
            ok += 1
    except Exception as e:
        fail += 1
    if i % 20 == 0 or i == len(todo):
        print(f"  [{i:>4}/{len(todo)}] ok={ok} fail={fail}")
    time.sleep(0.2)  # be nice to TM CDN

print(f"\nDONE: ok={ok} fail={fail}")

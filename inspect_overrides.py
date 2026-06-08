"""
inspect_overrides.py — Mostra il formato esatto di wc2026_overrides.json
(i 13 override di ieri) per capire come scrivere i nuovi.

Uso:
    cd ~/Desktop/pid
    python3 inspect_overrides.py
"""
import json
from pathlib import Path

p = Path("data/wc2026_overrides.json")
d = json.loads(p.read_text(encoding="utf-8"))

print(f"Tipo radice: {type(d).__name__}")
print(f"Numero override: {len(d)}")
print("\n--- TUTTE le 13 voci (chiave -> valore, con tipo valore) ---")
for k, v in d.items():
    print(f"  KEY  {k!r}")
    print(f"  VAL  ({type(v).__name__}) {v!r}")
    print()

# Come lo script consuma gli override
print("--- Come resolve_wc2026_from_squad.py carica/usa gli override ---")
src = Path("resolve_wc2026_from_squad.py").read_text(encoding="utf-8")
for i, line in enumerate(src.splitlines(), 1):
    low = line.lower()
    if "override" in low or "wc2026_overrides" in low:
        print(f"  {i}: {line}")

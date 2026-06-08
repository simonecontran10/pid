"""
diag_overrides.py — Diagnostica il meccanismo override WC2026.

1. Stato attuale wc2026_overrides.json (quante voci, le 8 nuove ci sono?)
2. Quale/i script del progetto LEGGONO wc2026_overrides.json
   (grep su tutti i .py della root)
3. Come quegli script lo usano (righe rilevanti)

Solo lettura. Non modifica niente.

Uso:
    cd ~/Desktop/pid
    python3 diag_overrides.py
"""
import json
import glob
import re
from pathlib import Path

OVF = Path("data/wc2026_overrides.json")

NEW_KEYS = [
    "Portugal|Diogo Costa",
    "Portugal|Rúben Dias",
    "Portugal|Nélson Semedo",
    "DR Congo|Gédéon Kalulu",
    "DR Congo|Gaël Kakuta",
    "Scotland|Findlay Curtis",
    "Cape Verde|Sidny Lopes Cabral",
    "Bosnia and Herzegovina|Arjan Malić",
]


def main():
    print("=" * 60)
    print("1. STATO wc2026_overrides.json")
    print("=" * 60)
    if not OVF.exists():
        print("  *** FILE NON ESISTE ***")
        return 1
    d = json.loads(OVF.read_text(encoding="utf-8"))
    print(f"  Totale voci: {len(d)}")
    print("  Le 8 nuove:")
    present = 0
    for k in NEW_KEYS:
        val = d.get(k)
        if val is not None:
            present += 1
            print(f"    OK  {k!r}: {val}")
        else:
            print(f"    --  {k!r}: ASSENTE")
    print(f"  => {present}/8 presenti  (se 0/8 -> add_overrides non e' stato eseguito)")

    print()
    print("=" * 60)
    print("2. QUALI script .py leggono wc2026_overrides.json")
    print("=" * 60)
    hits = []
    for pyf in sorted(glob.glob("*.py")) + sorted(glob.glob("scripts/*.py")):
        try:
            txt = Path(pyf).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if "wc2026_overrides" in txt or "wc2026_overrides.json" in txt:
            hits.append(pyf)
    if not hits:
        print("  NESSUNO script .py della root/scripts legge wc2026_overrides.json")
        print("  -> il meccanismo override potrebbe essere in un altro stadio")
        print("     (es. import nel DB, build players_all, ecc.)")
    else:
        for h in hits:
            print(f"  >>> {h}")
            txt = Path(h).read_text(encoding="utf-8", errors="ignore")
            for i, line in enumerate(txt.splitlines(), 1):
                if "override" in line.lower() or "wc2026_overrides" in line:
                    print(f"      {i}: {line.strip()[:110]}")

    print()
    print("=" * 60)
    print("3. Cerca dove wc2026_overrides e' referenziato (anche .md/.txt/.yml)")
    print("=" * 60)
    for pat in ["*.py", "*.md", "*.txt", "*.sh", ".github/workflows/*.yml"]:
        for f in sorted(glob.glob(pat)):
            try:
                t = Path(f).read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if "wc2026_overrides" in t:
                # mostra solo nome file + prima riga di contesto
                for i, ln in enumerate(t.splitlines(), 1):
                    if "wc2026_overrides" in ln:
                        print(f"  {f}:{i}: {ln.strip()[:100]}")
                        break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

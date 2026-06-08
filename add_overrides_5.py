"""
add_overrides_5.py — Aggiunge 5 override a data/wc2026_overrides.json
per chiudere a 496/496 le 19 nazionali.

tm_id recuperati e verificati via Transfermarkt:
  - Portugal|Bernardo Silva   241641  (DOB 1994-08-10 OK)
  - Portugal|Cristiano Ronaldo  8198  (DOB 1985-02-05 OK)
  - Portugal|Rafael Leão      357164  (DOB 1999-06-10 OK)
  - Croatia|Toni Fruk         432758  (identita' certa; DOB Wiki
                                       2001-04-09 vs TM 2001-03-09)
  - Ivory Coast|Emmanuel Agbadou 683895 (identita' certa; DOB Wiki
                                       1997-06-07 vs TM 1997-06-17)

Sicuro/idempotente: backup; ABORT se chiave gia' presente con
valore diverso.

Uso:
    cd ~/Desktop/pid
    python3 add_overrides_5.py
"""
import json
import time
from pathlib import Path

F = Path("data/wc2026_overrides.json")

NEW = {
    "Portugal|Bernardo Silva": 241641,
    "Portugal|Cristiano Ronaldo": 8198,
    "Portugal|Rafael Leão": 357164,
    "Croatia|Toni Fruk": 432758,
    "Ivory Coast|Emmanuel Agbadou": 683895,
}


def main():
    if not F.exists():
        print("ERRORE: data/wc2026_overrides.json non trovato")
        return 1

    d = json.loads(F.read_text(encoding="utf-8"))
    print(f"Override attuali: {len(d)}")

    conflicts = [(k, d[k], v) for k, v in NEW.items()
                 if k in d and d[k] != v]
    if conflicts:
        print("⚠️  CONFLITTI:")
        for k, old, new in conflicts:
            print(f"   {k!r}: esistente={old} proposto={new}")
        print("ABORT, nessuna modifica.")
        return 1

    to_add = [(k, v) for k, v in NEW.items() if k not in d]
    already = [k for k in NEW if k in d]
    if already:
        print(f"Gia' presenti identici: {already}")
    if not to_add:
        print("Nulla da aggiungere.")
        return 0

    print(f"Da aggiungere ({len(to_add)}):")
    for k, v in to_add:
        print(f"  + {k!r}: {v}")

    ts = time.strftime("%Y%m%d_%H%M%S")
    bak = F.with_suffix(f".json.bak-add5-{ts}")
    bak.write_text(F.read_text(encoding="utf-8"), encoding="utf-8")

    for k, v in to_add:
        d[k] = v
    F.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n",
                 encoding="utf-8")

    chk = json.loads(F.read_text(encoding="utf-8"))
    for k, v in NEW.items():
        assert chk.get(k) == v, f"verifica fallita {k}"

    print(f"\nOK: {len(to_add)} override aggiunti. Totale: {len(chk)}")
    print(f"Backup: {bak.name}")
    print("\nProssimo: resolve_wc2026_urls.py --country per Portugal,")
    print("Croatia, Ivory Coast (SENZA --reresolve) per applicarli.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""
add_overrides_wc2026.py — Aggiunge gli 8 override mancanti a
data/wc2026_overrides.json (formato esistente: "Nazione|Nome": tm_id_int).

I tm_id sono stati recuperati e verificati via Transfermarkt.
6/8 con DOB combaciante con il nostro JSON; 2/8 (Findlay Curtis,
Sidny Lopes Cabral) con identita' CERTA ma DOB divergente tra le
fonti (motivo per cui il match automatico falliva -> override manuale).

Sicuro/idempotente: backup prima; non sovrascrive override gia presenti
con valore diverso senza segnalarlo.

Uso:
    cd ~/Desktop/pid
    python3 add_overrides_wc2026.py
"""
import json
import time
from pathlib import Path

F = Path("data/wc2026_overrides.json")

NEW = {
    "Portugal|Diogo Costa": 357153,
    "Portugal|Rúben Dias": 258004,
    "Portugal|Nélson Semedo": 231572,
    "DR Congo|Gédéon Kalulu": 395685,
    "DR Congo|Gaël Kakuta": 74297,
    "Scotland|Findlay Curtis": 1082993,
    "Cape Verde|Sidny Lopes Cabral": 611855,
    "Bosnia and Herzegovina|Arjan Malić": 805534,
}


def main():
    if not F.exists():
        print(f"ERRORE: {F} non trovato (sei in ~/Desktop/pid?)")
        return 1

    d = json.loads(F.read_text(encoding="utf-8"))
    print(f"Override attuali: {len(d)}")

    conflicts = []
    to_add = []
    already_ok = []
    for k, v in NEW.items():
        if k in d:
            if d[k] == v:
                already_ok.append(k)
            else:
                conflicts.append((k, d[k], v))
        else:
            to_add.append((k, v))

    if conflicts:
        print("\n⚠️  CONFLITTI (chiave gia presente con valore DIVERSO):")
        for k, old, new in conflicts:
            print(f"   {k!r}: esistente={old}  proposto={new}")
        print("   ABORT: risolvi manualmente i conflitti prima. Nessuna modifica.")
        return 1

    if already_ok:
        print(f"\nGia presenti e identici ({len(already_ok)}): {already_ok}")

    if not to_add:
        print("\nNessun nuovo override da aggiungere. Nothing to do.")
        return 0

    print(f"\nDa aggiungere ({len(to_add)}):")
    for k, v in to_add:
        print(f"  + {k!r}: {v}")

    # Backup
    ts = time.strftime("%Y%m%d_%H%M%S")
    bak = F.with_suffix(f".json.bak-addov-{ts}")
    bak.write_text(F.read_text(encoding="utf-8"), encoding="utf-8")

    for k, v in to_add:
        d[k] = v

    F.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Verifica rilettura
    chk = json.loads(F.read_text(encoding="utf-8"))
    for k, v in NEW.items():
        assert chk.get(k) == v, f"verifica fallita per {k}"

    print(f"\nOK: {len(to_add)} override aggiunti. Totale ora: {len(chk)}")
    print(f"Backup: {bak.name}")
    print("\nProssimo step: rilanciare resolve_wc2026_from_squad.py sulle 5")
    print("nazionali interessate (Portugal, DR Congo, Scotland, Cape Verde,")
    print("Bosnia) per applicare gli override e arrivare a 393/393.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

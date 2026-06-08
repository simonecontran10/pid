"""
rigen_urls_wc2026.py — Rigenera urls_wc2026.txt COMPLETO da
data/wc2026_squads_raw.json (tutti i tm_profile_url di TUTTE le
15 nazionali), riparando il file che resolve_wc2026_urls.py
--country ha sovrascritto con la sola ultima nazione (Bosnia).

Logica identica al comando suggerito da resolve_wc2026_from_squad.py:
  set di tutti i p['tm_profile_url'] non vuoti, ordinati, uno per riga.

Backup del file danneggiato prima di sovrascriverlo.

Uso:
    cd ~/Desktop/pid
    python3 rigen_urls_wc2026.py
"""
import json
import time
from pathlib import Path

RAW = Path("data/wc2026_squads_raw.json")
OUT = Path("urls_wc2026.txt")


def main():
    if not RAW.exists():
        print("ERRORE: data/wc2026_squads_raw.json non trovato")
        return 1

    d = json.loads(RAW.read_text(encoding="utf-8"))

    urls = set()
    total_players = 0
    with_url = 0
    for country, v in d.items():
        players = v.get("players", []) if isinstance(v, dict) else []
        for p in players:
            total_players += 1
            u = p.get("tm_profile_url")
            if u:
                urls.add(u)
                with_url += 1

    urls_sorted = sorted(urls)
    print(f"Nazionali: {len(d)}")
    print(f"Giocatori totali: {total_players}")
    print(f"Con tm_profile_url: {with_url}")
    print(f"URL unici: {len(urls_sorted)}")

    if len(urls_sorted) < 300:
        print(f"\n⚠️  ATTENZIONE: solo {len(urls_sorted)} URL (attesi ~393).")
        print("   Qualcosa non torna. NON sovrascrivo. Verifica prima.")
        return 1

    # Backup del file attuale (danneggiato) prima di ripararlo
    if OUT.exists():
        ts = time.strftime("%Y%m%d_%H%M%S")
        bak = OUT.with_suffix(f".txt.bak-broken-{ts}")
        bak.write_text(OUT.read_text(encoding="utf-8"), encoding="utf-8")
        old_n = len(OUT.read_text(encoding="utf-8").splitlines())
        print(f"\nBackup file attuale ({old_n} righe, danneggiato): {bak.name}")

    OUT.write_text("\n".join(urls_sorted) + "\n", encoding="utf-8")
    new_n = len(OUT.read_text(encoding="utf-8").splitlines())
    print(f"urls_wc2026.txt rigenerato: {new_n} righe")
    print("\nOK: file riparato con TUTTI gli URL delle 15 nazionali.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

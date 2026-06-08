"""
safe_apply_overrides_test.py — Test PROTETTO di resolve_wc2026_urls.py
su UNA SOLA nazione (Portugal), per applicare gli override SENZA
--reresolve, verificando che i tm_id gia risolti NON vengano persi.

Flusso:
  1. Backup wc2026_squads_raw.json
  2. Snapshot PRE: tm_id risolti per OGNI nazione (tutte e 15)
  3. DRY-RUN: resolve_wc2026_urls.py --country Portugal --dry-run
     (NON scrive - solo per vedere cosa farebbe)
  4. Mostra cosa direbbe il dry-run
  5. STOP: l'utente decide se procedere al run reale guardando l'output

NON lancia mai --reresolve. NON lancia il run reale (solo dry-run).
Il run reale sara' un secondo script separato, solo dopo verifica.

Uso:
    cd ~/Desktop/pid
    source venv/bin/activate
    python3 safe_apply_overrides_test.py
"""
import json
import subprocess
import sys
import time
from pathlib import Path

RAW = Path("data/wc2026_squads_raw.json")
TEST_COUNTRY = "Portugal"


def snapshot():
    d = json.loads(RAW.read_text(encoding="utf-8"))
    snap = {}
    for c, v in d.items():
        pl = v.get("players", []) if isinstance(v, dict) else []
        r = sum(1 for p in pl if p.get("tm_player_id"))
        snap[c] = (r, len(pl))
    return snap


def main():
    if not RAW.exists():
        print("ERRORE: data/wc2026_squads_raw.json non trovato")
        return 1

    ts = time.strftime("%Y%m%d_%H%M%S")
    bak = RAW.with_suffix(f".json.bak-preov-{ts}")
    bak.write_text(RAW.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"[1] Backup: {bak.name}")

    pre = snapshot()
    print(f"[2] Snapshot PRE (15 nazionali) - tm_id risolti:")
    for c in sorted(pre):
        r, t = pre[c]
        print(f"    {c}: {r}/{t}")

    print(f"\n[3] DRY-RUN resolve_wc2026_urls.py --country {TEST_COUNTRY} --dry-run")
    print("    (NON scrive nulla, solo simulazione)")
    proc = subprocess.run(
        [sys.executable, "resolve_wc2026_urls.py",
         "--country", TEST_COUNTRY, "--dry-run"],
        capture_output=True, text=True
    )
    print("    --- STDOUT (ultime 30 righe) ---")
    for ln in proc.stdout.splitlines()[-30:]:
        print("    " + ln)
    if proc.stderr.strip():
        print("    --- STDERR ---")
        for ln in proc.stderr.splitlines()[-15:]:
            print("    " + ln)
    print(f"    exit code: {proc.returncode}")

    # Verifica che il dry-run NON abbia scritto (snapshot invariato)
    post = snapshot()
    changed = [c for c in pre if pre[c] != post.get(c)]
    print(f"\n[4] Verifica: il dry-run NON deve aver modificato il file.")
    if changed:
        print(f"    ⚠️  ATTENZIONE: cambiate {changed} - il dry-run HA scritto?!")
        print(f"    Rollback: cp {bak} {RAW}")
    else:
        print("    ✓ File invariato (dry-run corretto, nulla scritto)")

    print("\n[5] DECISIONE:")
    print("    Guarda l'output del dry-run sopra. Se mostra che applicherebbe")
    print(f"    gli override a {TEST_COUNTRY} (Diogo Costa/Ruben Dias/Nelson")
    print("    Semedo) SENZA azzerare i 25 gia risolti, allora il run reale")
    print("    e' sicuro. Altrimenti STOP.")
    print(f"\n    Backup pronto per rollback: {bak.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

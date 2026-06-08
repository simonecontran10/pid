"""
apply_overrides_real.py — Applica gli override alle 5 nazioni con
giocatori non risolti, via resolve_wc2026_urls.py --country X
(SENZA --reresolve, mai). Backup + verifica prima/dopo.

5 nazioni: Portugal, DR Congo, Scotland, Cape Verde,
           Bosnia and Herzegovina

Garanzie:
  - mai --reresolve (solo --country, processa i non risolti)
  - backup prima di toccare
  - snapshot PRE/POST di TUTTE le 15 nazioni
  - ALLARME se una delle 10 nazioni NON-target perde tm_id
  - ALLARME se una nazione target cala invece di salire

Uso:
    cd ~/Desktop/pid
    source venv/bin/activate
    python3 apply_overrides_real.py
"""
import json
import subprocess
import sys
import time
from pathlib import Path

RAW = Path("data/wc2026_squads_raw.json")
TARGETS = ["Portugal", "DR Congo", "Scotland",
           "Cape Verde", "Bosnia and Herzegovina"]


def snapshot():
    d = json.loads(RAW.read_text(encoding="utf-8"))
    s = {}
    for c, v in d.items():
        pl = v.get("players", []) if isinstance(v, dict) else []
        s[c] = (sum(1 for p in pl if p.get("tm_player_id")), len(pl))
    return s


def main():
    if not RAW.exists():
        print("ERRORE: data/wc2026_squads_raw.json non trovato")
        return 1

    ts = time.strftime("%Y%m%d_%H%M%S")
    bak = RAW.with_suffix(f".json.bak-applyov-{ts}")
    bak.write_text(RAW.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"[1] Backup: {bak.name}\n")

    pre = snapshot()
    print("[2] PRE (15 nazionali):")
    for c in sorted(pre):
        print(f"    {c}: {pre[c][0]}/{pre[c][1]}")

    print("\n[3] Run reale per-nazione (--country, MAI --reresolve):")
    for country in TARGETS:
        print(f"\n  >>> {country}")
        proc = subprocess.run(
            [sys.executable, "resolve_wc2026_urls.py", "--country", country],
            capture_output=True, text=True
        )
        for ln in proc.stdout.splitlines():
            if ("override manuale" in ln or "TOTALE risolti" in ln
                    or "Unresolved" in ln or "scrivo" in ln
                    or "salvat" in ln.lower()):
                print("     " + ln.strip())
        if proc.returncode != 0:
            print(f"     ⚠️ exit {proc.returncode}")
            if proc.stderr.strip():
                print("     STDERR:", proc.stderr.splitlines()[-3:])

    post = snapshot()
    print("\n[4] VERIFICA prima/dopo (15 nazionali):")
    alarm = False
    for c in sorted(pre):
        pr, pt = pre[c]
        qr, qt = post.get(c, (0, 0))
        if c in TARGETS:
            arrow = "OK" if qr >= pr else "*** CALATO ***"
            if qr < pr:
                alarm = True
            print(f"    [target] {c}: {pr}/{pt} -> {qr}/{qt}  {arrow}")
        else:
            if qr < pr or qt < pt:
                alarm = True
                print(f"    [ALTRO ] {c}: {pr}/{pt} -> {qr}/{qt}  *** PERSO?! ***")
            else:
                print(f"    [ALTRO ] {c}: {pr}/{pt} -> {qr}/{qt}  OK (intatta)")

    tot_r = sum(v[0] for v in post.values())
    tot_p = sum(v[1] for v in post.values())
    print(f"\n    TOTALE: {tot_r}/{tot_p}")

    if alarm:
        print("\n  🚨 ALLARME: qualcosa e' calato. Controlla sopra.")
        print(f"     Rollback: cp {bak} {RAW}")
        return 2
    print("\n  ✅ Tutte le non-target INTATTE, target salite. Override applicati.")
    print(f"     Backup: {bak.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

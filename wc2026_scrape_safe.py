"""
wc2026_scrape_safe.py — Esegue lo scrape WC2026 in modo sicuro:

  1. Backup di wc2026_squads_raw.json (timestamp)
  2. Snapshot PRE-scrape dei tm_id risolti per le 9 nazionali gia fatte
  3. Lancia parse_wikipedia_squad.py --all (scrape reale)
  4. Verifica POST-scrape: le 9 esistenti devono avere ANCORA i loro tm_id
     (patch anti-overwrite). Se anche una sola e' stata azzerata -> ALLARME
     + istruzioni di rollback, e l'utente decide.
  5. Report delle nuove nazionali final entrate (tm_id ancora da risolvere)

NON modifica nulla oltre a ciò che fa parse_wikipedia_squad.py.
Il backup permette rollback immediato in caso di overwrite.

Uso:
    cd ~/Desktop/pid
    source venv/bin/activate
    python3 wc2026_scrape_safe.py
"""
import json
import subprocess
import sys
import time
from pathlib import Path

RAW = Path("data/wc2026_squads_raw.json")
OLD9 = ['Bosnia and Herzegovina', 'France', 'Iraq', 'Japan', 'New Zealand',
        'Belgium', 'Haiti', 'Tunisia', 'South Korea']
NEW_EXPECTED = ['Austria', 'Cape Verde', 'Curaçao', 'DR Congo', 'Portugal', 'Scotland']


def resolved_count(d, country):
    v = d.get(country, {})
    pl = v.get('players', []) if isinstance(v, dict) else []
    res = sum(1 for p in pl if p.get('tm_player_id'))
    return res, len(pl)


def snapshot(d):
    return {c: resolved_count(d, c) for c in OLD9}


def main():
    if not RAW.exists():
        print(f"ERRORE: {RAW} non trovato (sei in ~/Desktop/pid?)")
        return 1

    # 1. Backup
    ts = time.strftime("%Y%m%d_%H%M%S")
    bak = RAW.with_suffix(f".json.bak-scrape-{ts}")
    bak.write_text(RAW.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"[1/5] Backup creato: {bak.name}")

    # 2. Snapshot pre-scrape
    d_pre = json.loads(RAW.read_text(encoding="utf-8"))
    pre = snapshot(d_pre)
    print("[2/5] Snapshot PRE-scrape (9 esistenti):")
    for c in OLD9:
        r, t = pre[c]
        print(f"      {c}: {r}/{t}")

    # 3. Scrape reale
    print("\n[3/5] Lancio parse_wikipedia_squad.py --all (puo' richiedere 1-3 min)...")
    proc = subprocess.run(
        [sys.executable, "parse_wikipedia_squad.py", "--all"],
        capture_output=True, text=True
    )
    tail = "\n".join(proc.stdout.splitlines()[-12:])
    print("      --- ultime righe output scrape ---")
    print("      " + tail.replace("\n", "\n      "))
    print(f"      exit code scrape: {proc.returncode}")
    if proc.returncode != 0:
        print("\n⚠️  Lo scrape e' uscito con errore. STDERR:")
        print(proc.stderr[-800:])
        print(f"\nFile NON verificato. Backup intatto: {bak.name}")
        print(f"Rollback se serve: cp {bak} {RAW}")
        return 1

    # 4. Verifica anti-overwrite
    d_post = json.loads(RAW.read_text(encoding="utf-8"))
    post = snapshot(d_post)
    print("\n[4/5] VERIFICA ANTI-OVERWRITE (9 esistenti devono restare uguali):")
    overwrite_detected = False
    for c in OLD9:
        pr, pt = pre[c]
        qr, qt = post[c]
        if qr < pr or qt < pt or qr == 0:
            print(f"      ❌ {c}: PRIMA {pr}/{pt} -> DOPO {qr}/{qt}  *** AZZERATO/RIDOTTO ***")
            overwrite_detected = True
        else:
            print(f"      ✓ {c}: {pr}/{pt} -> {qr}/{qt} OK")

    if overwrite_detected:
        print("\n" + "=" * 60)
        print("🚨 OVERWRITE RILEVATO — la patch anti-overwrite NON ha tenuto.")
        print("   Come il bug del 15 mag. NON procedere al resolve.")
        print(f"   ROLLBACK IMMEDIATO:  cp {bak} {RAW}")
        print("=" * 60)
        return 2

    # 5. Report nuove nazionali
    print("\n[5/5] Nuove nazionali entrate (tm_id da risolvere col prossimo step):")
    all_countries = list(d_post.keys())
    new_countries = [c for c in all_countries if c not in OLD9]
    for c in sorted(new_countries):
        r, t = resolved_count(d_post, c)
        print(f"      {c}: {t} giocatori, {r} risolti")
    print(f"\n      Totale nazionali nel file: {len(all_countries)} (erano 9)")
    print(f"      Nuove: {len(new_countries)}")

    print("\n✅ Scrape OK, le 9 esistenti INTATTE (patch anti-overwrite funziona).")
    print("   Prossimo step: resolve_wc2026_from_squad.py per risolvere i tm_id")
    print("   delle nuove nazionali (NON usare resolve_wc2026_urls.py --reresolve).")
    print(f"   Backup di sicurezza: {bak.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

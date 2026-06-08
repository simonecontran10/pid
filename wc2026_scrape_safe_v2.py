"""
wc2026_scrape_safe_v2.py — Scrape WC2026 sicuro, versione aggiornata
per proteggere le 15 nazionali GIA risolte (393/393 al commit 6f19129).

Attese 4 nuove final: Brazil, Ivory Coast, Sweden, Croatia
(rose definitive annunciate 12-18 mag, non cambiano piu').

Flusso:
  1. Backup wc2026_squads_raw.json
  2. Snapshot PRE delle 15 esistenti (devono restare ai loro numeri)
  3. parse_wikipedia_squad.py --all (scrape reale)
  4. Verifica anti-overwrite: nessuna delle 15 deve perdere tm_id
     su un giocatore ancora in rosa (un calo per cambio-rosa
     legittimo NON e' allarme, come Belgium stamattina)
  5. Report nuove nazionali entrate

Uso:
    cd ~/Desktop/pid
    source venv/bin/activate
    python3 wc2026_scrape_safe_v2.py
"""
import json
import subprocess
import sys
import time
from pathlib import Path

RAW = Path("data/wc2026_squads_raw.json")
OLD15 = ['Austria', 'Belgium', 'Bosnia and Herzegovina', 'Cape Verde',
         'Curaçao', 'DR Congo', 'France', 'Haiti', 'Iraq', 'Japan',
         'New Zealand', 'Portugal', 'Scotland', 'South Korea', 'Tunisia']
EXPECTED_NEW = ['Brazil', 'Ivory Coast', 'Sweden', 'Croatia']


def players_map(d, country):
    """nome -> tm_id per i giocatori di country."""
    v = d.get(country, {})
    pl = v.get('players', []) if isinstance(v, dict) else []
    out = {}
    for p in pl:
        nm = p.get('name') or p.get('player_name') or '?'
        out[nm] = p.get('tm_player_id')
    return out


def resolved(d, country):
    v = d.get(country, {})
    pl = v.get('players', []) if isinstance(v, dict) else []
    return sum(1 for p in pl if p.get('tm_player_id')), len(pl)


def main():
    if not RAW.exists():
        print("ERRORE: data/wc2026_squads_raw.json non trovato")
        return 1

    ts = time.strftime("%Y%m%d_%H%M%S")
    bak = RAW.with_suffix(f".json.bak-scrape2-{ts}")
    bak.write_text(RAW.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"[1/5] Backup: {bak.name}")

    d_pre = json.loads(RAW.read_text(encoding="utf-8"))
    pre_maps = {c: players_map(d_pre, c) for c in OLD15}
    print("[2/5] Snapshot PRE (15 esistenti):")
    for c in OLD15:
        r, t = resolved(d_pre, c)
        print(f"      {c}: {r}/{t}")

    print("\n[3/5] parse_wikipedia_squad.py --all (1-3 min)...")
    proc = subprocess.run(
        [sys.executable, "parse_wikipedia_squad.py", "--all"],
        capture_output=True, text=True
    )
    for ln in proc.stdout.splitlines()[-8:]:
        print("      " + ln)
    print(f"      exit: {proc.returncode}")
    if proc.returncode != 0:
        print("\n⚠️  scrape fallito. STDERR:")
        print(proc.stderr[-600:])
        print(f"Backup intatto: {bak.name}")
        return 1

    d_post = json.loads(RAW.read_text(encoding="utf-8"))
    print("\n[4/5] VERIFICA ANTI-OVERWRITE (15 esistenti):")
    real_overwrite = False
    for c in OLD15:
        post_map = players_map(d_post, c)
        pre_map = pre_maps[c]
        common = [n for n in post_map if n in pre_map]
        lost = [n for n in common if pre_map[n] and not post_map[n]]
        pr, pt = resolved(d_pre, c)
        qr, qt = resolved(d_post, c)
        if lost:
            real_overwrite = True
            print(f"      ❌ {c}: {pr}/{pt}->{qr}/{qt} - PERSI tm_id: {lost}")
        elif qt != pt:
            print(f"      ⚠️  {c}: {pr}/{pt}->{qr}/{qt} - rosa cambiata "
                  f"(no tm_id persi su comuni: OK legittimo)")
        else:
            print(f"      ✓ {c}: {pr}/{pt}->{qr}/{qt} OK")

    if real_overwrite:
        print("\n🚨 OVERWRITE REALE (tm_id persi su giocatori in rosa).")
        print(f"   ROLLBACK: cp {bak} {RAW}")
        return 2

    print("\n[5/5] Nuove nazionali entrate:")
    new_countries = [c for c in d_post if c not in OLD15]
    for c in sorted(new_countries):
        r, t = resolved(d_post, c)
        flag = " <-- ATTESA" if c in EXPECTED_NEW else ""
        print(f"      {c}: {t} giocatori, {r} risolti{flag}")
    print(f"\n      Totale nazionali: {len(d_post)} (erano 15)")
    print("\n✅ Scrape OK, 15 esistenti SALVE. Prossimo: resolve per-nazione")
    print("   delle nuove (resolve_wc2026_from_squad.py, mai --reresolve).")
    print(f"   Backup: {bak.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Migrazione completa Serie C → 3 gironi (IT3A/IT3B/IT3C).

USO:
  python3 migrate_serie_c.py             # DRY-RUN: stampa cosa farebbe, non scrive niente
  python3 migrate_serie_c.py --apply     # APPLY: esegue le modifiche

COSA FA:
  1. Mergia data/it3a_clubs.json + it3b + it3c con data/clubs.json
  2. Sposta Inter U23, Atalanta U23, Juventus Next Gen al girone giusto (IT3A/B/C)
  3. Sposta Milan Futuro a league_id=OTHER (Serie D, fuori da Serie C)
  4. Conserva sortitoutsi_team_id + logo dei 4 club già presenti
  5. Aggiunge i 56 club nuovi (59 totali Serie C - 3 già esistenti)
  6. Aggiorna app.js (KNOWN_LEAGUES, dropdown, sezione Club, isKnownLeague, getCompColor)
  7. Aggiorna i18n.js (rimuove league_it3, aggiunge league_it3a/b/c)
  8. Aggiorna scrape_sortitoutsi_competition.py (3 nuove competizioni FM26)
  9. Backup automatico di tutti i file modificati con suffisso .before_serie_c

DOPO IL --apply:
  - Lancia: python3 scrape_sortitoutsi_competition.py per i loghi dei 56 club nuovi
  - Lancia: python3 scrape_sortitoutsi_ids.py --no-search (loghi club_sots locali)
  - Verifica frontend
  - Commit + push
"""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
DATA = ROOT / "data"
FRONTEND = ROOT / "frontend"

# Args
DRY_RUN = "--apply" not in sys.argv

# Codici dei 4 club esistenti (da it3_clubs.json)
EXISTING_CLUBS = {
    41119: "IT3A",   # Inter U23 → Girone A
    41101: "IT3B",   # Juventus Next Gen → Girone B
    41110: "IT3C",   # Atalanta U23 → Girone C
    41107: "OTHER",  # Milan Futuro → Serie D (esce da Serie C)
}

# Mapping league_id → league_name (italiano)
LEAGUE_NAMES_IT3 = {
    "IT3A": "Serie C - Girone A",
    "IT3B": "Serie C - Girone B",
    "IT3C": "Serie C - Girone C",
}

# ============================================================
# UTILITY
# ============================================================

def banner(title):
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)


def log(level, msg):
    icons = {"info": "ℹ️ ", "ok": "✅", "warn": "⚠️ ", "err": "❌", "dry": "🔍"}
    print(f"{icons.get(level, '  ')} {msg}")


def backup_file(path: Path):
    if DRY_RUN:
        log("dry", f"backup {path.name} → {path.name}.before_serie_c (skipped)")
        return
    bk = path.with_suffix(path.suffix + ".before_serie_c")
    if bk.exists():
        log("info", f"backup esistente: {bk.name} (non sovrascrivo)")
        return
    shutil.copy2(path, bk)
    log("ok", f"backup creato: {bk.name}")


def write_json(path: Path, data):
    if DRY_RUN:
        log("dry", f"scriverei {path.name} ({len(data) if isinstance(data, list) else 'dict'} elementi)")
        return
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    log("ok", f"salvato {path.name}")


def write_text(path: Path, text):
    if DRY_RUN:
        log("dry", f"scriverei {path.name} ({len(text)} caratteri)")
        return
    path.write_text(text, encoding="utf-8")
    log("ok", f"salvato {path.name}")


# ============================================================
# FASE 1: merge JSON club
# ============================================================

def phase_1_merge_clubs():
    banner("FASE 1 — Merge clubs.json + it3a/b/c_clubs.json")

    clubs_path = DATA / "clubs.json"
    if not clubs_path.exists():
        log("err", "clubs.json non trovato"); sys.exit(1)
    backup_file(clubs_path)

    clubs = json.loads(clubs_path.read_text())
    log("info", f"clubs.json: {len(clubs)} club esistenti")

    # Carica i 3 file Serie C nuovi
    new_clubs_by_code = {}
    for code in ["IT3A", "IT3B", "IT3C"]:
        f = DATA / f"{code.lower()}_clubs.json"
        if not f.exists():
            log("err", f"{f.name} non trovato"); sys.exit(1)
        new_clubs_by_code[code] = json.loads(f.read_text())
        log("info", f"{f.name}: {len(new_clubs_by_code[code])} club ({code})")

    total_new = sum(len(v) for v in new_clubs_by_code.values())
    log("info", f"Totale Serie C nuovi: {total_new}")

    # Indice per tm_club_id
    clubs_by_id = {c["tm_club_id"]: c for c in clubs}

    # Step 1: aggiorna i 4 club esistenti (4 actions)
    log("info", "")
    log("info", "Step 1: aggiorno i 4 club esistenti (Inter U23, Atalanta U23, Juventus Next Gen, Milan Futuro)")
    for cid, new_league in EXISTING_CLUBS.items():
        if cid not in clubs_by_id:
            log("warn", f"  tm_club_id={cid} NON trovato in clubs.json (skip)")
            continue
        old_league = clubs_by_id[cid].get("league_id")
        old_name_lega = clubs_by_id[cid].get("league_name", "")
        clubs_by_id[cid]["league_id"] = new_league
        if new_league == "OTHER":
            # Per Milan Futuro: rimuovo league_name (resta NULL)
            clubs_by_id[cid].pop("league_name", None)
            log("info", f"  {cid:>6} {clubs_by_id[cid]['name']:30} {old_league} → {new_league} (rimossa league_name)")
        else:
            clubs_by_id[cid]["league_name"] = LEAGUE_NAMES_IT3[new_league]
            log("info", f"  {cid:>6} {clubs_by_id[cid]['name']:30} {old_league}/{old_name_lega!r} → {new_league}/{LEAGUE_NAMES_IT3[new_league]!r}")

    # Step 2: aggiungi i club Serie C nuovi (NON ancora presenti)
    log("info", "")
    log("info", "Step 2: aggiungo i club Serie C non ancora presenti")
    added_count = 0
    skipped_count = 0
    for code in ["IT3A", "IT3B", "IT3C"]:
        for new_c in new_clubs_by_code[code]:
            cid = new_c["tm_club_id"]
            if cid in clubs_by_id:
                # Già esiste: lo lascio (è stato aggiornato sopra)
                skipped_count += 1
                continue
            # Aggiungo, settando il league_name corretto
            new_c["league_name"] = LEAGUE_NAMES_IT3[code]
            clubs_by_id[cid] = new_c
            added_count += 1
    log("ok", f"Aggiunti: {added_count} club nuovi")
    log("info", f"Skippati (già presenti): {skipped_count}")

    # Step 3: ricostruisci la lista
    new_clubs = list(clubs_by_id.values())
    log("info", "")
    log("info", f"Risultato: {len(new_clubs)} club totali")

    # Stat per lega
    from collections import Counter
    counter = Counter(c.get("league_id") for c in new_clubs)
    log("info", "Per lega:")
    for k, v in sorted(counter.items(), key=lambda x: (x[0] is None, x[0])):
        log("info", f"  {k or '(nessuna)':>10}: {v}")

    write_json(clubs_path, new_clubs)
    return clubs_by_id


# ============================================================
# FASE 2: aggiorna it3_clubs.json (rimuovi Milan Futuro, aggiorna i 3 al girone)
# ============================================================

def phase_2_update_it3_legacy(clubs_by_id):
    banner("FASE 2 — Aggiorna it3_clubs.json (legacy)")

    it3_path = DATA / "it3_clubs.json"
    if not it3_path.exists():
        log("warn", "it3_clubs.json non esiste, skip")
        return
    backup_file(it3_path)

    # Lo svuoto: ora è obsoleto (i club sono nei nuovi 3 file)
    # Lo lascio come array vuoto per backward-compat / non rompere import che lo cercano
    log("info", "it3_clubs.json: lo svuoto (i club sono ora nei nuovi 3 file it3a/b/c_clubs.json)")
    write_json(it3_path, [])


# ============================================================
# FASE 3: app.js patch
# ============================================================

def phase_3_appjs():
    banner("FASE 3 — Patch frontend/app.js")

    appjs_path = FRONTEND / "app.js"
    if not appjs_path.exists():
        log("err", "app.js non trovato"); sys.exit(1)
    backup_file(appjs_path)

    t = appjs_path.read_text()
    original = t
    changes = []

    # PATCH 3.1: KNOWN_LEAGUES (riga ~512 e ~625) — sostituisci IT3 con IT3A/IT3B/IT3C
    old_set = 'new Set(["IT1", "IT2", "IT3", "IJ1", "PL1", "PL2"])'
    new_set = 'new Set(["IT1", "IT2", "IT3A", "IT3B", "IT3C", "IJ1", "PL1", "PL2"])'
    cnt_set = t.count(old_set)
    if cnt_set > 0:
        t = t.replace(old_set, new_set)
        changes.append(f"KNOWN_LEAGUES aggiornato in {cnt_set} punti")

    # PATCH 3.2: isKnownLeague checks (riga ~2104, ~3111)
    old_check = '(lg === "IT1" || lg === "IT2" || lg === "IT3" || lg === "IJ1" || lg === "PL1" || lg === "PL2")'
    new_check = '(lg === "IT1" || lg === "IT2" || lg === "IT3A" || lg === "IT3B" || lg === "IT3C" || lg === "IJ1" || lg === "PL1" || lg === "PL2")'
    cnt_check = t.count(old_check)
    if cnt_check > 0:
        t = t.replace(old_check, new_check)
        changes.append(f"isKnownLeague check aggiornato in {cnt_check} punti")

    # PATCH 3.3: sezione Club (riga ~621): const it3 = ... → splitto in 3
    old_it3_filter = '  const it3 = sortClubs(state.clubs.filter(c => c.league_id === "IT3"));'
    new_it3_filter = '''  const it3a = sortClubs(state.clubs.filter(c => c.league_id === "IT3A"));
  const it3b = sortClubs(state.clubs.filter(c => c.league_id === "IT3B"));
  const it3c = sortClubs(state.clubs.filter(c => c.league_id === "IT3C"));'''
    if old_it3_filter in t:
        t = t.replace(old_it3_filter, new_it3_filter)
        changes.append("sezione Club: const it3 → it3a/it3b/it3c")

    # PATCH 3.4: dropdown filter <option value="IT3"> (3 occorrenze: home riga 4427, lista 4427, callup 2234)
    old_opt = '<option value="IT3" ${f.league==="IT3"?"selected":""}>${t("league_it3")}</option>'
    new_opt = '''<option value="IT3A" ${f.league==="IT3A"?"selected":""}>${t("league_it3a")}</option>
            <option value="IT3B" ${f.league==="IT3B"?"selected":""}>${t("league_it3b")}</option>
            <option value="IT3C" ${f.league==="IT3C"?"selected":""}>${t("league_it3c")}</option>'''
    cnt_opt = t.count(old_opt)
    if cnt_opt > 0:
        t = t.replace(old_opt, new_opt)
        changes.append(f"dropdown filter <option> sostituiti in {cnt_opt} punti")

    # PATCH 3.5: getCompColor "IT3" → IT3A/B/C
    old_color = 'if (code === "IT3") return "var(--comp-it3)";'
    new_color = '''if (code === "IT3A" || code === "IT3B" || code === "IT3C") return "var(--comp-it3)";'''
    if old_color in t:
        t = t.replace(old_color, new_color)
        changes.append("getCompColor IT3 → IT3A/B/C")

    # PATCH 3.6: it3Logo (riga ~658) — uso lo stesso logo per i 3 gironi
    old_logo = '  const it3Logo = _photoUrl("photos/competitions/IT3.png");'
    new_logo = '''  const it3Logo = _photoUrl("photos/competitions/IT3.png");
  const it3aLogo = it3Logo;
  const it3bLogo = it3Logo;
  const it3cLogo = it3Logo;'''
    if old_logo in t and "it3aLogo" not in t:
        t = t.replace(old_logo, new_logo)
        changes.append("it3Logo: aggiunti alias it3aLogo/it3bLogo/it3cLogo")

    # PATCH 3.7: render sezione Club — devo sostituire la riga `it3.length ? sectionHtml(t("league_it3")...`
    # Cerco "league_it3" nel render Club. Pattern atteso (può essere su una riga):
    # (it3.length ? sectionHtml(t("league_it3"), it3Logo, it3, ...) : "") +
    pattern_render = re.compile(r'\(it3\.length \? sectionHtml\(t\("league_it3"\), it3Logo, it3, ([^)]+)\) : ""\) \+')
    m = pattern_render.search(t)
    if m:
        replacement = (
            '(it3a.length ? sectionHtml(t("league_it3a"), it3aLogo, it3a, ' + m.group(1) + ') : "") +\n'
            '    (it3b.length ? sectionHtml(t("league_it3b"), it3bLogo, it3b, ' + m.group(1) + ') : "") +\n'
            '    (it3c.length ? sectionHtml(t("league_it3c"), it3cLogo, it3c, ' + m.group(1) + ') : "") +'
        )
        t = pattern_render.sub(replacement, t)
        changes.append("render sezione Club: it3 → it3a/it3b/it3c")

    if t != original:
        write_text(appjs_path, t)
        for c in changes:
            log("ok", f"  {c}")
    else:
        log("warn", "Nessuna modifica applicata a app.js (forse già patchato)")


# ============================================================
# FASE 4: i18n.js patch
# ============================================================

def phase_4_i18njs():
    banner("FASE 4 — Patch frontend/i18n.js")

    i18n_path = FRONTEND / "i18n.js"
    if not i18n_path.exists():
        log("err", "i18n.js non trovato"); sys.exit(1)
    backup_file(i18n_path)

    t = i18n_path.read_text()
    original = t

    # Cerco le 2 occorrenze di league_it3: "..." (IT + EN block)
    # Pattern: league_it3:\s*"([^"]+)",
    matches = list(re.finditer(r'(\s+)league_it3:\s*"([^"]+)",', t))
    if not matches:
        log("warn", "league_it3 non trovato in i18n.js, skip")
        return

    # Sostituisco la prima occorrenza con le 3 chiavi italiane, la seconda con le 3 inglesi
    if len(matches) >= 2:
        # Faccio le sostituzioni dalla fine all'inizio per non rompere gli offset
        matches.reverse()
        for i, m in enumerate(matches):
            indent = m.group(1)  # whitespace originale
            # i==0 è l'occorrenza più in basso = blocco EN (perché ho fatto reverse)
            # i==1 è la prima del file = blocco IT
            if i == 0:
                # EN
                replacement = (
                    f'{indent}league_it3a: "Serie C - Group A",'
                    f'{indent}league_it3b: "Serie C - Group B",'
                    f'{indent}league_it3c: "Serie C - Group C",'
                )
            else:
                # IT
                replacement = (
                    f'{indent}league_it3a: "Serie C - Girone A",'
                    f'{indent}league_it3b: "Serie C - Girone B",'
                    f'{indent}league_it3c: "Serie C - Girone C",'
                )
            t = t[:m.start()] + replacement + t[m.end():]

        if t != original:
            write_text(i18n_path, t)
            log("ok", f"league_it3 → league_it3a/b/c in 2 blocchi (IT + EN)")
        else:
            log("warn", "i18n.js: nessuna modifica applicata")
    else:
        log("warn", f"i18n.js: trovata solo {len(matches)} occorrenza di league_it3 (mi aspettavo 2)")


# ============================================================
# FASE 5: scrape_sortitoutsi_competition.py patch
# ============================================================

def phase_5_sots_competitions():
    banner("FASE 5 — Patch scrape_sortitoutsi_competition.py (loghi)")

    sots_path = ROOT / "scrape_sortitoutsi_competition.py"
    if not sots_path.exists():
        log("err", "scrape_sortitoutsi_competition.py non trovato"); sys.exit(1)
    backup_file(sots_path)

    t = sots_path.read_text()
    original = t

    # Aggiungo le 3 nuove competizioni alla mappa COMPETITIONS
    # I link sortitoutsi:
    # IT3A: https://sortitoutsi.net/football-manager-2026/competition/43127172/italian-serie-ca
    # IT3B: https://sortitoutsi.net/football-manager-2026/competition/43127173/italian-serie-cb
    # IT3C: https://sortitoutsi.net/football-manager-2026/competition/43127174/italian-serie-cc

    # Cerco dove finisce la dict COMPETITIONS = { ... }
    # Strategia: cerco una linea che contiene "Serie B" o "competition/33" e aggiungo le 3 dopo

    # Pattern ipotizzato: una entry di Serie B esistente
    new_entries = '''    "IT3A": {
        "name": "Serie C - Girone A",
        "url": "https://sortitoutsi.net/football-manager-2026/competition/43127172/italian-serie-ca",
    },
    "IT3B": {
        "name": "Serie C - Girone B",
        "url": "https://sortitoutsi.net/football-manager-2026/competition/43127173/italian-serie-cb",
    },
    "IT3C": {
        "name": "Serie C - Girone C",
        "url": "https://sortitoutsi.net/football-manager-2026/competition/43127174/italian-serie-cc",
    },
'''

    if '"IT3A"' in t:
        log("info", "IT3A già presente in scrape_sortitoutsi_competition.py, skip")
        return

    # Cerco la chiusura di COMPETITIONS = {...}: line `}` dopo `"IT2": {...}` o simili
    # Strategia robusta: cerco la sequenza '"IT2"' e poi aggiungo dopo la sua chiusura `},`
    pattern = re.compile(r'(\s*"IT2"\s*:\s*\{[^}]+\},)', re.DOTALL)
    m = pattern.search(t)
    if m:
        insert_at = m.end()
        t = t[:insert_at] + "\n" + new_entries + t[insert_at:]
        write_text(sots_path, t)
        log("ok", "Aggiunte 3 competizioni IT3A/IT3B/IT3C dopo IT2")
    else:
        log("warn", "Pattern IT2 non trovato in scrape_sortitoutsi_competition.py — patch saltata")
        log("info", "Aggiungi MANUALMENTE le 3 entries alla dict COMPETITIONS:")
        print()
        print(new_entries)


# ============================================================
# MAIN
# ============================================================

def main():
    print()
    print("┌─────────────────────────────────────────────────────────────────┐")
    print(f"│  MIGRAZIONE SERIE C — 3 GIRONI                                  │")
    print(f"│  Modalità: {'DRY-RUN (nessuna modifica)':<53}│")
    print("└─────────────────────────────────────────────────────────────────┘")
    if DRY_RUN:
        print()
        print("⚠️  DRY-RUN attivo. Per applicare davvero, lancia:")
        print(f"   python3 {Path(__file__).name} --apply")
        print()

    clubs_by_id = phase_1_merge_clubs()
    phase_2_update_it3_legacy(clubs_by_id)
    phase_3_appjs()
    phase_4_i18njs()
    phase_5_sots_competitions()

    banner("RIEPILOGO")
    if DRY_RUN:
        print()
        log("warn", "DRY-RUN completato. NESSUN file è stato modificato.")
        log("info", "Lancia con --apply per eseguire davvero la migrazione:")
        log("info", f"   python3 {Path(__file__).name} --apply")
    else:
        log("ok", "Migrazione completata!")
        print()
        log("info", "PROSSIMI STEP:")
        log("info", "  1. python3 scrape_sortitoutsi_competition.py  (loghi 56 club nuovi)")
        log("info", "  2. python3 scrape_sortitoutsi_ids.py --no-search  (download immagini logo)")
        log("info", "  3. Verifica frontend (localhost o vercel)")
        log("info", "  4. git add -A && git commit -m 'feat(clubs): Serie C in 3 gironi (IT3A/IT3B/IT3C)' && git push")


if __name__ == "__main__":
    main()

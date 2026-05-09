"""Patch app.js per Commit 1 — fix veloci.

USO:
  python3 patch_commit1.py             # dry-run
  python3 patch_commit1.py --apply

COSA FA:
  1. Estende _CLUB_DISPLAY_MAP in app.js con 56 mappature Serie C
  2. Aggiunge fallback "Winter signing" → "—" in prettyClubName
  3. Aggiunge divisore visuale (border-top) tra "Osservazioni" e "Statistiche club" nel modal giocatore
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
APPJS = ROOT / "frontend" / "app.js"
DRY_RUN = "--apply" not in sys.argv


def main():
    print(f"{'='*60}")
    print(f"  COMMIT 1 — Patch fix veloci ({'DRY-RUN' if DRY_RUN else 'APPLY'})")
    print(f"{'='*60}\n")

    if not APPJS.exists():
        print(f"❌ {APPJS} non trovato"); sys.exit(1)

    t = APPJS.read_text()
    original = t

    # ============================================================
    # PATCH 1: estende _CLUB_DISPLAY_MAP con 56 club Serie C
    # ============================================================
    print("PATCH 1 — Estende _CLUB_DISPLAY_MAP con i 56 club Serie C")

    # Aggiungo PRIMA della chiusura della map (dopo "Sassuolo Primavera": "Sassuolo Primavera")
    old_anchor = '  "Torino Primavera": "Torino Primavera",\n};'
    new_block = '''  "Torino Primavera": "Torino Primavera",
  // Serie C — Girone A
  "LR Vicenza": "Vicenza",
  "Union Brescia": "Brescia",
  "AS Cittadella": "Cittadella",
  "Calcio Lecco 1912": "Lecco",
  "AC Trento": "Trento",
  "Dolomiti Bellunesi": "Dolomiti Bellunesi",
  "Alcione Milano": "Alcione Milano",
  "FC Pro Vercelli 1892": "Pro Vercelli",
  "Novara FC": "Novara",
  "FC Lumezzane": "Lumezzane",
  "AC Renate": "Renate",
  "Virtusvecomp Verona": "Virtusvecomp Verona",
  "AS Giana Erminio": "Giana Erminio",
  "UC AlbinoLeffe": "AlbinoLeffe",
  "Arzignano Valchiampo": "Arzignano",
  "Aurora Pro Patria": "Pro Patria",
  "CPR Ospitaletto": "Ospitaletto",
  "US Pergolettese 1932": "Pergolettese",
  "US Triestina": "Triestina",
  // Serie C — Girone B
  "SS Arezzo": "Arezzo",
  "Ascoli Calcio": "Ascoli",
  "Ternana Calcio": "Ternana",
  "Ravenna FC": "Ravenna",
  "US Livorno 1915": "Livorno",
  "Forlì FC": "Forlì",
  "Vis Pesaro 1898": "Vis Pesaro",
  "Guidonia Montecelio 1937 FC": "Guidonia Montecelio",
  "AC Perugia Calcio": "Perugia",
  "US Sambenedettese": "Sambenedettese",
  "Pineto Calcio": "Pineto",
  "US Città di Pontedera": "Pontedera",
  "AS Gubbio 1910": "Gubbio",
  "Campobasso FC": "Campobasso",
  "SEF Torres 1903": "Torres",
  "AC Carpi": "Carpi",
  "US Pianese": "Pianese",
  "AC Bra": "Bra",
  // Serie C — Girone C
  "Benevento Calcio": "Benevento",
  "US Salernitana 1919": "Salernitana",
  "Catania FC": "Catania",
  "Cosenza Calcio": "Cosenza",
  "Casertana FC": "Casertana",
  "Potenza Calcio": "Potenza",
  "Casarano Calcio": "Casarano",
  "FC Crotone": "Crotone",
  "Calcio Foggia 1920": "Foggia",
  "Giugliano Calcio 1928": "Giugliano",
  "FC Trapani 1905": "Trapani",
  "Latina Calcio 1932": "Latina",
  "SS Monopoli 1966": "Monopoli",
  "Audace Cerignola": "Cerignola",
  "ASD Team Altamura": "Team Altamura",
  "Cavese 1919": "Cavese",
  "AZ Picerno": "Picerno",
  "Sorrento 1945": "Sorrento",
  "Siracusa Calcio": "Siracusa",
  // Seconde Squadre (in Serie C ma altre leghe)
  "Inter U23": "Inter U23",
  "Juventus Next Gen": "Juventus Next Gen",
  "Atalanta U23": "Atalanta U23",
  "Milan Futuro": "Milan Futuro",
};'''

    if "Serie C — Girone A" in t:
        print("  ℹ️  PATCH 1 già applicata, skip\n")
    elif old_anchor in t:
        t = t.replace(old_anchor, new_block)
        print("  ✅ 56 mappature Serie C aggiunte a _CLUB_DISPLAY_MAP\n")
    else:
        print("  ❌ PATCH 1: pattern non trovato")
        print(f"  cercavo: {old_anchor!r}\n")

    # ============================================================
    # PATCH 2: workaround Winter signing in prettyClubName
    # ============================================================
    print("PATCH 2 — Workaround \"Winter signing\" in prettyClubName")

    old_fn = '''function prettyClubName(name) {
  if (!name) return name;
  return _CLUB_DISPLAY_MAP[name] || name;
}'''

    new_fn = '''function prettyClubName(name) {
  if (!name) return name;
  // Workaround bug TM: i giocatori in trasferimento vengono scrappati con
  // current_club_name="Winter signing" / "New arrival" / "Returnee" (tutti
  // pseudo-club fittizi). Mostra "—" finché non viene rifatto lo scraping.
  if (name === "Winter signing" || name === "New arrival" || name === "Returnee") return "—";
  return _CLUB_DISPLAY_MAP[name] || name;
}'''

    if 'name === "Winter signing"' in t:
        print("  ℹ️  PATCH 2 già applicata, skip\n")
    elif old_fn in t:
        t = t.replace(old_fn, new_fn)
        print("  ✅ Workaround \"Winter signing\"/\"New arrival\"/\"Returnee\" → \"—\"\n")
    else:
        print("  ❌ PATCH 2: pattern prettyClubName non trovato\n")

    # ============================================================
    # PATCH 3: linea divisoria tra Osservazioni e Statistiche club
    # ============================================================
    # La sezione Osservazioni è iniettata in app.js riga ~989 dopo apertura div padding 22px
    # Pattern: subito prima del blocco "club_stats" header
    print("PATCH 3 — Linea divisoria visiva tra Osservazioni e Statistiche club")

    old_div = '''    <div style="padding: 22px 28px;">
      ${typeof window.renderObservationsSection === "function" ? window.renderObservationsSection(pid) : ""}
      ${(clubBlocks || hasU21Current) ? `'''

    new_div = '''    <div style="padding: 22px 28px;">
      ${typeof window.renderObservationsSection === "function" ? window.renderObservationsSection(pid) : ""}
      ${(clubBlocks || hasU21Current) ? `
        <div style="margin-top: 22px; padding-top: 18px; border-top: 0.5px solid var(--border);"></div>
        `: ""}
      ${(clubBlocks || hasU21Current) ? `'''

    if "border-top: 0.5px solid var(--border)" in t and "padding-top: 18px" in t:
        print("  ℹ️  PATCH 3 già applicata, skip\n")
    elif old_div in t:
        t = t.replace(old_div, new_div)
        print("  ✅ Linea divisoria aggiunta tra Osservazioni e Statistiche club\n")
    else:
        print("  ❌ PATCH 3: pattern non trovato\n")

    # ============================================================
    # SAVE
    # ============================================================
    if t == original:
        print("⚠️  Nessuna modifica applicata. Forse tutte le patch erano già presenti?")
        return

    # Sanity check
    g = t.count("{") - t.count("}")
    p = t.count("(") - t.count(")")
    print(f"\nSintassi: graffe diff={g}, parentesi diff={p}")
    if g != 0 or p != 0:
        print("❌ ERRORE SINTASSI! Non scrivo il file. Fix manuale necessario.")
        sys.exit(1)

    if DRY_RUN:
        print(f"\n🔍 DRY-RUN: app.js NON modificato. Lancia con --apply per applicare.")
    else:
        APPJS.write_text(t)
        print(f"\n✅ app.js salvato (+{len(t)-len(original)} caratteri)")


if __name__ == "__main__":
    main()

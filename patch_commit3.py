"""Patch app.js per Sub-commit 3 — bottoni '+ Osservazione' nelle Ultime partite e grafico minuti.

USO:
  python3 patch_commit3.py             # dry-run
  python3 patch_commit3.py --apply

COSA FA:
  1. Aggiunge una colonna icona "+" alla fine di ogni riga di "Ultime 12 partite"
  2. Aggiunge la stessa icona "+" al drill-down del grafico minuti per mese
  3. Click → apre form osservazione con data/avversario/competizione/minuti precompilati
  4. Aggiunge keys i18n it/en per il tooltip "Aggiungi osservazione"
  5. Wira gli event listener una volta sola (delegato sul container del modal giocatore)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
APPJS = ROOT / "frontend" / "app.js"
DRY_RUN = "--apply" not in sys.argv


def main():
    print(f"{'='*60}")
    print(f"  COMMIT 3 — Bottoni '+ Osservazione' ({'DRY-RUN' if DRY_RUN else 'APPLY'})")
    print(f"{'='*60}\n")

    if not APPJS.exists():
        print(f"❌ {APPJS} non trovato"); sys.exit(1)

    t = APPJS.read_text()
    original = t

    # ============================================================
    # PATCH 1: aggiungo icona "+" all'ultima colonna di renderRecentMatches
    # Modifico la grid-template-columns: 64px 22px 1fr 70px 28px 60px → aggiungo 24px alla fine
    # ============================================================
    print("PATCH 1 — Bottone '+ osservazione' su Ultime 12 partite")

    old_recent_row = '''      <div style="display: grid; grid-template-columns: 64px 22px 1fr 70px 28px 60px; gap: 10px; align-items: center; padding: 10px 12px; border-bottom: 0.5px solid var(--border);">
        <span class="stat-cell" style="font-size: 12px; color: var(--text-3);">${fmtDate(m.date)}</span>
        ${compLogo ? `<img src="${compLogo}" style="width: 18px; height: 18px; object-fit: contain;"/>` : `<span></span>`}
        <div style="display: flex; align-items: center; gap: 6px; min-width: 0;">
          ${venue}
          ${oppLogoUrl ? `<img src="${oppLogoUrl}" style="width: 16px; height: 16px; object-fit: contain; flex-shrink: 0;"/>` : `<span style="width: 16px; height: 16px; flex-shrink: 0;"></span>`}
          <span class="truncate" style="font-size: 13px; color: var(--text-1);">${escapeHtml(oppName)}</span>
        </div>
        <span class="stat-cell" style="font-size: 13px; font-weight: 600; color: var(--text-1); text-align: center;">${score}</span>
        <span class="stat-cell" style="display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; border-radius: 5px; background: ${resultBg}; color: ${resultColor}; font-weight: 700; font-size: 11px; border: 0.5px solid ${resultColor}40;">${resultLetter}</span>
        <div style="display: flex; align-items: center; gap: 5px; justify-content: flex-end;">
          ${goals ? `<span class="stat-cell" style="font-size: 11px; color: var(--hot); font-weight: 700;">⚽${goals}</span>` : ""}
          ${assists ? `<span class="stat-cell" style="font-size: 11px; color: var(--accent); font-weight: 700;">${assists}A</span>` : ""}
          <span class="stat-cell" style="font-size: 13px; font-weight: 700; color: ${m.minutes ? "var(--accent)" : "var(--text-3)"}; font-variant-numeric: tabular-nums; padding: 2px 6px; border-radius: 4px; background: ${m.minutes ? "rgba(111,224,168,0.08)" : "transparent"};">${m.minutes||0}'</span>
        </div>
      </div>`;'''

    new_recent_row = '''      <div style="display: grid; grid-template-columns: 64px 22px 1fr 70px 28px 60px 26px; gap: 10px; align-items: center; padding: 10px 12px; border-bottom: 0.5px solid var(--border);">
        <span class="stat-cell" style="font-size: 12px; color: var(--text-3);">${fmtDate(m.date)}</span>
        ${compLogo ? `<img src="${compLogo}" style="width: 18px; height: 18px; object-fit: contain;"/>` : `<span></span>`}
        <div style="display: flex; align-items: center; gap: 6px; min-width: 0;">
          ${venue}
          ${oppLogoUrl ? `<img src="${oppLogoUrl}" style="width: 16px; height: 16px; object-fit: contain; flex-shrink: 0;"/>` : `<span style="width: 16px; height: 16px; flex-shrink: 0;"></span>`}
          <span class="truncate" style="font-size: 13px; color: var(--text-1);">${escapeHtml(oppName)}</span>
        </div>
        <span class="stat-cell" style="font-size: 13px; font-weight: 600; color: var(--text-1); text-align: center;">${score}</span>
        <span class="stat-cell" style="display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; border-radius: 5px; background: ${resultBg}; color: ${resultColor}; font-weight: 700; font-size: 11px; border: 0.5px solid ${resultColor}40;">${resultLetter}</span>
        <div style="display: flex; align-items: center; gap: 5px; justify-content: flex-end;">
          ${goals ? `<span class="stat-cell" style="font-size: 11px; color: var(--hot); font-weight: 700;">⚽${goals}</span>` : ""}
          ${assists ? `<span class="stat-cell" style="font-size: 11px; color: var(--accent); font-weight: 700;">${assists}A</span>` : ""}
          <span class="stat-cell" style="font-size: 13px; font-weight: 700; color: ${m.minutes ? "var(--accent)" : "var(--text-3)"}; font-variant-numeric: tabular-nums; padding: 2px 6px; border-radius: 4px; background: ${m.minutes ? "rgba(111,224,168,0.08)" : "transparent"};">${m.minutes||0}'</span>
        </div>
        <button class="add-obs-from-match" data-pid="${pid}" data-date="${escapeHtml(_matchDateString(m) || "")}" data-opponent="${escapeHtml(oppName)}" data-competition="${escapeHtml(_compName(m.competition_id, m.competition_name) || "")}" data-minutes="${m.minutes||0}" title="${t("add_obs_from_match")}" style="display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 5px; background: rgba(111,224,168,0.08); color: var(--accent); font-size: 16px; line-height: 1; cursor: pointer; border: 0.5px solid rgba(111,224,168,0.25); padding: 0;">+</button>
      </div>`;'''

    if "add-obs-from-match" in t:
        print("  ℹ️  PATCH 1 già applicata, skip\n")
    elif old_recent_row in t:
        t = t.replace(old_recent_row, new_recent_row)
        print("  ✅ Bottone '+' aggiunto a renderRecentMatches\n")
    else:
        print("  ❌ PATCH 1: pattern grid recent_matches non trovato\n")
        return

    # ============================================================
    # PATCH 2: stesso bottone in _renderDrillDownMatch (grafico minuti)
    # ============================================================
    print("PATCH 2 — Bottone '+ osservazione' nel drill-down grafico minuti")

    old_drill = '''  return `
    <div style="display: grid; grid-template-columns: 56px minmax(140px, 180px) 1fr 60px 22px 64px; gap: 8px; align-items: center; padding: 6px 8px; background: rgba(255,255,255,0.02); border-radius: 6px;">
      <span class="stat-cell" style="font-size: 11px; color: var(--text-3);">${escapeHtml(date)}</span>
      <div style="display: flex; align-items: center; gap: 5px; min-width: 0;" title="${escapeHtml(compName)}">
        ${compLogo ? `<img src="${compLogo}" style="width: 16px; height: 16px; object-fit: contain; flex-shrink: 0;"/>` : `<span style="width: 16px; flex-shrink: 0;"></span>`}
        <span class="truncate" style="font-size: 11px; color: var(--text-2);">${escapeHtml(compName)}</span>
      </div>
      ${opponentBlock}
      <span class="stat-cell" style="font-size: 12px; font-weight: 600; color: var(--text-1); text-align: center;">${score}</span>
      <span class="stat-cell" style="display: inline-flex; align-items: center; justify-content: center; width: 20px; height: 20px; border-radius: 4px; background: ${resBg}; color: ${resColor}; font-weight: 700; font-size: 10px; border: 0.5px solid ${resColor}40;">${resLetter}</span>
      <span class="stat-cell" style="font-size: 12px; font-weight: 700; color: ${m.minutes?'var(--accent)':'var(--text-3)'}; text-align: right; padding: 2px 6px; border-radius: 4px; background: ${m.minutes?'rgba(111,224,168,0.08)':'transparent'};">${m.minutes||0}'</span>
    </div>`;
}'''

    new_drill = '''  const pid = stats?.tm_player_id;
  return `
    <div style="display: grid; grid-template-columns: 56px minmax(140px, 180px) 1fr 60px 22px 64px 24px; gap: 8px; align-items: center; padding: 6px 8px; background: rgba(255,255,255,0.02); border-radius: 6px;">
      <span class="stat-cell" style="font-size: 11px; color: var(--text-3);">${escapeHtml(date)}</span>
      <div style="display: flex; align-items: center; gap: 5px; min-width: 0;" title="${escapeHtml(compName)}">
        ${compLogo ? `<img src="${compLogo}" style="width: 16px; height: 16px; object-fit: contain; flex-shrink: 0;"/>` : `<span style="width: 16px; flex-shrink: 0;"></span>`}
        <span class="truncate" style="font-size: 11px; color: var(--text-2);">${escapeHtml(compName)}</span>
      </div>
      ${opponentBlock}
      <span class="stat-cell" style="font-size: 12px; font-weight: 600; color: var(--text-1); text-align: center;">${score}</span>
      <span class="stat-cell" style="display: inline-flex; align-items: center; justify-content: center; width: 20px; height: 20px; border-radius: 4px; background: ${resBg}; color: ${resColor}; font-weight: 700; font-size: 10px; border: 0.5px solid ${resColor}40;">${resLetter}</span>
      <span class="stat-cell" style="font-size: 12px; font-weight: 700; color: ${m.minutes?'var(--accent)':'var(--text-3)'}; text-align: right; padding: 2px 6px; border-radius: 4px; background: ${m.minutes?'rgba(111,224,168,0.08)':'transparent'};">${m.minutes||0}'</span>
      ${pid ? `<button class="add-obs-from-match" data-pid="${pid}" data-date="${escapeHtml(_matchDateString(m) || "")}" data-opponent="${escapeHtml(oppName)}" data-competition="${escapeHtml(compName || "")}" data-minutes="${m.minutes||0}" title="${t("add_obs_from_match")}" style="display: inline-flex; align-items: center; justify-content: center; width: 20px; height: 20px; border-radius: 4px; background: rgba(111,224,168,0.08); color: var(--accent); font-size: 14px; line-height: 1; cursor: pointer; border: 0.5px solid rgba(111,224,168,0.25); padding: 0;">+</button>` : ""}
    </div>`;
}'''

    if old_drill in t:
        t = t.replace(old_drill, new_drill)
        print("  ✅ Bottone '+' aggiunto a _renderDrillDownMatch\n")
    else:
        print("  ❌ PATCH 2: pattern drill-down non trovato\n")
        return

    # ============================================================
    # PATCH 3: aggiungo handler delegato per .add-obs-from-match
    # Lo metto in fondo a wirePlayerCardClicks o all'inizio del bootstrap. 
    # Strategia: delego sul body, così funziona ovunque (modal giocatore + drill-down).
    # ============================================================
    print("PATCH 3 — Event handler delegato per bottoni '+'")

    # Cerco una funzione che venga chiamata al boot per attaccare event listener globali
    # Pattern: bootstrap o init handler
    old_init = '''document.addEventListener("DOMContentLoaded", () => {'''

    new_init = '''// Handler delegato per bottoni "+ osservazione" nelle ultime partite e drill-down
document.addEventListener("click", (e) => {
  const btn = e.target.closest(".add-obs-from-match");
  if (!btn) return;
  e.preventDefault();
  e.stopPropagation();
  const pid = parseInt(btn.dataset.pid);
  if (!pid) return;
  if (typeof window.openObservationCompose !== "function") {
    console.warn("[obs] openObservationCompose non disponibile");
    return;
  }
  // Pre-fill data che viene letto dal form modale
  window._obsPrefill = {
    match_date: btn.dataset.date || null,
    opponent: btn.dataset.opponent || null,
    competition: btn.dataset.competition || null,
    minutes_played: btn.dataset.minutes ? parseInt(btn.dataset.minutes, 10) : null,
  };
  window.openObservationCompose(pid);
});

document.addEventListener("DOMContentLoaded", () => {'''

    if 'window._obsPrefill' in t:
        print("  ℹ️  PATCH 3 già applicata, skip\n")
    elif old_init in t:
        t = t.replace(old_init, new_init, 1)
        print("  ✅ Handler delegato '.add-obs-from-match' aggiunto\n")
    else:
        print("  ⚠️  PATCH 3: DOMContentLoaded non trovato — provo append in fondo")
        t += "\n\n// Handler delegato per bottoni '+ osservazione' (Sub-commit 3)\ndocument.addEventListener('click', (e) => {\n  const btn = e.target.closest('.add-obs-from-match');\n  if (!btn) return;\n  e.preventDefault(); e.stopPropagation();\n  const pid = parseInt(btn.dataset.pid);\n  if (!pid || typeof window.openObservationCompose !== 'function') return;\n  window._obsPrefill = {\n    match_date: btn.dataset.date || null,\n    opponent: btn.dataset.opponent || null,\n    competition: btn.dataset.competition || null,\n    minutes_played: btn.dataset.minutes ? parseInt(btn.dataset.minutes, 10) : null,\n  };\n  window.openObservationCompose(pid);\n});\n"
        print("  ✅ Handler aggiunto in fondo a app.js\n")

    # ============================================================
    # PATCH 4: aggiungo chiave i18n per tooltip
    # ============================================================
    print("PATCH 4 — Chiavi i18n add_obs_from_match (IT/EN)")

    # Cerca dove le strings i18n di app.js sono definite
    # Pattern presunto: dict it={} en={}, oppure singola map con chiavi multiple
    # Best effort: append alla mappa "recent_matches" che esiste già
    
    if "add_obs_from_match" in t:
        print("  ℹ️  PATCH 4 già applicata, skip\n")
    else:
        # Cerco una chiave esistente vicina, es. "recent_matches" 
        old_it = '''recent_matches: "Ultime partite",'''
        new_it = '''recent_matches: "Ultime partite",
    add_obs_from_match: "Aggiungi osservazione",'''
        old_en = '''recent_matches: "Recent matches",'''
        new_en = '''recent_matches: "Recent matches",
    add_obs_from_match: "Add observation",'''

        ok_it = old_it in t
        ok_en = old_en in t

        if ok_it:
            t = t.replace(old_it, new_it)
            print("  ✅ chiave IT add_obs_from_match aggiunta")
        else:
            print("  ⚠️  PATCH 4 IT: pattern recent_matches IT non trovato")

        if ok_en:
            t = t.replace(old_en, new_en)
            print("  ✅ chiave EN add_obs_from_match aggiunta")
        else:
            print("  ⚠️  PATCH 4 EN: pattern recent_matches EN non trovato")
        print()

    # ============================================================
    # SAVE
    # ============================================================
    if t == original:
        print("⚠️  Nessuna modifica applicata.")
        return

    g = t.count("{") - t.count("}")
    par = t.count("(") - t.count(")")
    print(f"Sintassi: graffe diff={g}, parentesi diff={par}")
    if g != 0 or par != 0:
        print("❌ ERRORE SINTASSI! Non scrivo il file. Fix manuale necessario.")
        sys.exit(1)

    if DRY_RUN:
        print(f"\n🔍 DRY-RUN: app.js NON modificato. Lancia con --apply per applicare.")
    else:
        APPJS.write_text(t)
        print(f"\n✅ app.js salvato (+{len(t)-len(original)} caratteri)")
        print(f"\nDopo il save, devi anche aggiornare observations_ui.js per leggere window._obsPrefill")


if __name__ == "__main__":
    main()

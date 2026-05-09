/**
 * observations_ui.js — Fase 3 v2 (revisione 9 mag 2026)
 *
 * Modifiche rispetto a v1:
 *  1. Voce "Scouting" nella sidebar (anticipata Fase 4 — vista globale base)
 *  2. Modal opaco (overlay più scuro, card non trasparente)
 *  3. Layout modal 2 colonne: form sinistra + campo SVG ruoli destra (rimpicciolito)
 *  4. prettyClubName applicato all'autocomplete avversario
 *  5. Ordine evaluation tags invertito: NON IDONEO → DA MONITORARE → SECONDA → PRIMA
 *  6. Chip forze verdi / debolezze rosse, layout 2 colonne side-by-side
 *  7. 37 voci categorizzate (TATTICA, TECNICA, COMPORTAMENTI, FISICO, PORTIERE)
 *  8. Dashboard compatta sotto "Stagione corrente": tabella + footer media/%
 *
 * Da appendere o caricato come <script> separato dopo app.js.
 *
 * Espone:
 *  - window.renderObservationsSection(pid)        → HTML dashboard sotto stagione corrente
 *  - window.wireObservationsHandlers(pid)         → aggancia event listener
 *  - window.openObservationCompose(pid, obsId?)   → modal nuova/modifica
 *  - window.renderScoutingPanel()                 → HTML pannello sidebar Scouting
 *  - window.wireScoutingPanel()                   → aggancia eventi pannello sidebar
 */

// ============================================================
//  COSTANTI: liste valori (canoniche in italiano)
// ============================================================

// 37 caratteristiche categorizzate (ordine alfabetico dentro ogni categoria)
window.OBSERVATION_TRAITS_BY_CATEGORY = {
  "TATTICA": [
    "Fase difensiva",
    "Fase offensiva",
    "Intelligenza tattica",
    "Letture tattiche",
    "Transizioni difensive",
    "Transizioni offensive",
  ],
  "TECNICA": [
    "Assist",
    "Conduzione palla",
    "Cross",
    "Dribbling 1c1",
    "Finalizzazione",
    "Inizio manovra",
    "Passaggi Chiave",
    "Rifinitura",
    "Tecnica",
    "Tiro/Calcio",
    "Visione di gioco",
  ],
  "COMPORTAMENTI": [
    "Aggressività",
    "Agonismo",
    "Gioco per la squadra",
    "Intensità",
    "Personalità",
  ],
  "FISICO": [
    "1vs1 difensivo",
    "Ampiezza",
    "Area di rigore offensiva",
    "Dinamismo",
    "Duelli difensivi",
    "Forza fisica",
    "Gioco aereo",
    "Inserimenti senza palla",
    "Jolly",
    "Profondità",
    "Progressione",
    "Rapidità primi metri",
    "Recupero palloni",
    "Spazi stretti",
    "Velocità",
  ],
  "PORTIERE": [
    "Uscite",
  ],
};

// Lista flat (per validazione e iterazioni rapide)
window.OBSERVATION_TRAITS = Object.values(window.OBSERVATION_TRAITS_BY_CATEGORY).flat();

// Etichette di valutazione globale: ordine PEGGIORE → MIGLIORE (sx → dx)
window.OBSERVATION_TAGS = [
  { value: "NON VALUTABILE",  color: "#9CA3AF" }, // grigio (escluso da medie)
  { value: "NON IDONEO",      color: "#EF4444" }, // rosso
  { value: "DA MONITORARE",   color: "#F97316" }, // arancione
  { value: "SECONDA SCELTA",  color: "#EAB308" }, // giallo
  { value: "PRIMA SCELTA",    color: "#22C55E" }, // verde
];

// Competizioni preset
window.OBSERVATION_COMPETITIONS = [
  "Serie A", "Serie B", "Serie C", "Primavera 1", "Primavera 2",
  "Coppa Italia", "Supercoppa Italiana",
  "UEFA Champions League", "UEFA Europa League", "UEFA Conference League",
  "Premier League", "La Liga", "Bundesliga", "Ligue 1", "Eredivisie",
  "Liga Portugal", "Pro League (BEL)", "Süper Lig (TUR)",
  "Ekstraklasa", "1 Liga (POL)",
  "Saudi Pro League", "Saudi First Division",
  "Amichevole",
  "Altro",
];

// 15 ruoli con coordinate sul campo SVG
window.OBSERVATION_ROLE_DEFS = [
  { code: "PP",     it: "Punta",                     en: "Striker",                cx: 190, cy: 65  },
  { code: "AS",     it: "Ala sinistra",              en: "Left winger",            cx: 115, cy: 145 },
  { code: "TRQ",    it: "Trequartista",              en: "Attacking midfielder",   cx: 190, cy: 165 },
  { code: "AD",     it: "Ala destra",                en: "Right winger",           cx: 265, cy: 145 },
  { code: "AES",    it: "Quinto sinistro",           en: "Left wing-back",         cx: 45,  cy: 215 },
  { code: "AED",    it: "Quinto destro",             en: "Right wing-back",        cx: 335, cy: 215 },
  { code: "CIS",    it: "Centrocampista interno sx", en: "Left central midfielder",cx: 130, cy: 280 },
  { code: "CC",     it: "Centrocampista centrale",   en: "Central midfielder",     cx: 190, cy: 305 },
  { code: "CID",    it: "Centrocampista interno dx", en: "Right central midfielder",cx: 250, cy: 280 },
  { code: "LAT_SN", it: "Terzino sinistro",          en: "Left-back",              cx: 60,  cy: 365 },
  { code: "LAT_DX", it: "Terzino destro",            en: "Right-back",             cx: 320, cy: 365 },
  { code: "DCS",    it: "Difensore centrale sx",     en: "Left centre-back",       cx: 140, cy: 420 },
  { code: "DC",     it: "Difensore centrale",        en: "Centre-back",            cx: 190, cy: 440 },
  { code: "DCD",    it: "Difensore centrale dx",     en: "Right centre-back",      cx: 240, cy: 420 },
  { code: "POR",    it: "Portiere",                  en: "Goalkeeper",             cx: 190, cy: 500 },
];

// ============================================================
//  Mapping IT → EN per visualizzazione
// ============================================================
window.OBSERVATION_I18N_EN = {
  // Categorie
  "TATTICA": "TACTICAL", "TECNICA": "TECHNICAL", "COMPORTAMENTI": "BEHAVIORS",
  "FISICO": "PHYSICAL", "PORTIERE": "GOALKEEPER",
  // Traits
  "1vs1 difensivo": "Defensive 1vs1", "Aggressività": "Aggressiveness",
  "Agonismo": "Combativeness", "Ampiezza": "Width",
  "Area di rigore offensiva": "Box presence", "Assist": "Assists",
  "Conduzione palla": "Ball carrying", "Cross": "Crossing",
  "Dinamismo": "Dynamism", "Dribbling 1c1": "Dribbling 1v1",
  "Duelli difensivi": "Defensive duels", "Fase difensiva": "Defensive phase",
  "Fase offensiva": "Offensive phase", "Finalizzazione": "Finishing",
  "Forza fisica": "Physical strength", "Gioco aereo": "Aerial play",
  "Gioco per la squadra": "Team play", "Inizio manovra": "Build-up play",
  "Inserimenti senza palla": "Off-ball runs", "Intelligenza tattica": "Tactical intelligence",
  "Intensità": "Intensity", "Jolly": "Versatility",
  "Letture tattiche": "Tactical reading", "Passaggi Chiave": "Key passes",
  "Personalità": "Personality", "Profondità": "Depth runs",
  "Progressione": "Progression", "Rapidità primi metri": "Acceleration",
  "Recupero palloni": "Ball recovery", "Rifinitura": "Final pass",
  "Spazi stretti": "Tight spaces", "Tecnica": "Technique",
  "Tiro/Calcio": "Shooting", "Transizioni difensive": "Defensive transitions",
  "Transizioni offensive": "Offensive transitions", "Uscite": "Goalkeeper exits",
  "Velocità": "Speed", "Visione di gioco": "Game vision",
  // Tags
  "PRIMA SCELTA":   "FIRST CHOICE",
  "SECONDA SCELTA": "SECOND CHOICE",
  "DA MONITORARE":  "MONITOR",
  "NON IDONEO":     "REJECT",
  "NON VALUTABILE": "N/A",
};

window.obsLocalize = function(itValue) {
  if (!itValue) return "";
  if (typeof currentLang === "undefined" || currentLang === "it") return itValue;
  return window.OBSERVATION_I18N_EN[itValue] || itValue;
};

window.obsT = function(key) {
  const dict = {
    it: {
      section_title: "Osservazioni",
      no_obs: "Nessuna osservazione",
      new_obs: "+ Nuova",
      edit_obs: "Modifica osservazione",
      new_obs_title: "Nuova osservazione",
      delete_confirm: "Eliminare questa osservazione? L'azione è irreversibile.",
      th_date: "Data", th_opponent: "Avversario", th_competition: "Competizione", th_role: "Posizione", th_mode: "Mod.", th_scout: "Scout", th_perf: "Performance", th_verdict: "Giudizio",
      f_viewing_mode: "Visione",
      f_viewing_live: "Live",
      f_viewing_tv: "TV/Video",
      footer_avg: "Media performance",
      footer_distrib: "Distribuzione giudizi",
      f_match_date: "Data partita",
      f_opponent: "Avversario",
      f_opponent_ph: "Es. Sassuolo",
      f_competition: "Competizione",
      f_competition_other: "Specifica competizione",
      f_roles: "Ruoli giocati",
      f_roles_hint: "Clicca i cerchi sul campo",
      f_rating: "Performance rating",
      f_tag: "Valutazione",
      f_strengths: "Punti di forza",
      f_weaknesses: "Punti di debolezza",
      f_notes: "Note",
      f_notes_ph: "Osservazioni libere sulla prestazione…",
      btn_save: "Salva", btn_cancel: "Annulla", btn_delete: "Elimina",
      err_required: "Compila tutti i campi obbligatori",
      err_no_role: "Seleziona almeno un ruolo",
      err_no_tag: "Seleziona un giudizio (anche 'Non valutabile')",
      err_duplicate: "Esiste già un'osservazione per questo giocatore in questa partita",
      // Pannello scouting sidebar
      scouting_title: "Scouting",
      scouting_summary: "giocatori visionati",
      scouting_total_obs: "osservazioni totali",
      scouting_no_obs: "Nessuna osservazione registrata. Apri la scheda di un giocatore per aggiungerne una.",
      scouting_filter_all: "Tutti",
      scouting_filter_player: "Per giocatore",
      scouting_n_obs: "oss.",
    },
    en: {
      section_title: "Observations",
      no_obs: "No observations",
      new_obs: "+ New",
      edit_obs: "Edit observation",
      new_obs_title: "New observation",
      delete_confirm: "Delete this observation? This action is irreversible.",
      th_date: "Date", th_opponent: "Opponent", th_competition: "Competition", th_role: "Role", th_mode: "Mode", th_scout: "Scout", th_perf: "Performance", th_verdict: "Verdict",
      f_viewing_mode: "Viewing",
      f_viewing_live: "Live",
      f_viewing_tv: "TV/Video",
      footer_avg: "Average performance",
      footer_distrib: "Verdict distribution",
      f_match_date: "Match date",
      f_opponent: "Opponent",
      f_opponent_ph: "e.g. Sassuolo",
      f_competition: "Competition",
      f_competition_other: "Specify competition",
      f_roles: "Roles played",
      f_roles_hint: "Click circles on the pitch",
      f_rating: "Performance rating",
      f_tag: "Verdict",
      f_strengths: "Strengths",
      f_weaknesses: "Weaknesses",
      f_notes: "Notes",
      f_notes_ph: "Free observations on the performance…",
      btn_save: "Save", btn_cancel: "Cancel", btn_delete: "Delete",
      err_required: "Fill in all required fields",
      err_no_role: "Select at least one role",
      err_no_tag: "Select an evaluation tag (also 'N/A')",
      err_duplicate: "An observation already exists for this player in this match",
      scouting_title: "Scouting",
      scouting_summary: "players observed",
      scouting_total_obs: "total observations",
      scouting_no_obs: "No observations yet. Open a player's card to add one.",
      scouting_filter_all: "All",
      scouting_filter_player: "By player",
      scouting_n_obs: "obs.",
    },
  };
  const lang = (typeof currentLang !== "undefined") ? currentLang : "it";
  return (dict[lang] && dict[lang][key]) || (dict.it[key]) || key;
};

// ============================================================
//  DASHBOARD COMPATTA (sotto "Stagione corrente" del modal)
// ============================================================

window._obsCache = window._obsCache || {};
// Cache globale per pannello Scouting (lista completa di tutte le osservazioni)
window._obsAllCache = null;

window.renderObservationsSection = function(pid) {
  return `
    <div id="obs-section-${pid}" style="margin-top: 22px; padding-top: 16px; border-top: 0.5px solid var(--border);">
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <div style="width: 3px; height: 14px; background: var(--accent); border-radius: 2px;"></div>
          <span style="font-size: 13px; font-weight: 500; color: var(--text-1); text-transform: uppercase; letter-spacing: 0.06em;">${window.obsT("section_title")}</span>
        </div>
        <button id="obs-new-btn-${pid}" type="button"
          style="font-size: 12px; padding: 5px 12px; border-radius: 8px; background: var(--accent-bg); color: var(--accent); border: 0.5px solid var(--accent); cursor: pointer; font-weight: 500;">
          ${window.obsT("new_obs")}
        </button>
      </div>
      <div id="obs-dashboard-${pid}" style="font-size: 12px; color: var(--text-3);">…</div>
    </div>
  `;
};

/**
 * Renderizza la dashboard compatta (tabella + footer riassuntivo).
 * Chiamata async dopo l'inserimento del modal.
 */
window.renderObservationsList = async function(pid) {
  const wrapper = document.getElementById(`obs-dashboard-${pid}`);
  if (!wrapper) return;

  try {
    const obsList = await window.fetchObservations({ tm_player_id: pid });
    window._obsCache[pid] = obsList;

    if (!obsList.length) {
      wrapper.innerHTML = `<div style="font-size: 12px; color: var(--text-3); padding: 6px 0;">${window.obsT("no_obs")}</div>`;
      return;
    }

    // Tabella compatta
    const dateLocale = (typeof currentLang !== "undefined" && currentLang === "it") ? "it-IT" : "en-GB";
    const rowsHtml = obsList.map(o => {
      const dateFmt = new Date(o.match_date).toLocaleDateString(dateLocale, { day: "2-digit", month: "2-digit", year: "2-digit" });
      const tagDef = window.OBSERVATION_TAGS.find(t => t.value === o.evaluation_tags?.[0]);
      const tagHtml = tagDef
        ? `<span style="font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 999px; background: ${tagDef.color}22; color: ${tagDef.color}; border: 0.5px solid ${tagDef.color};">${escapeHtml(window.obsLocalize(tagDef.value))}</span>`
        : `<span style="color: var(--text-3); font-size: 11px;">—</span>`;
      const ratingHtml = o.performance_rating != null
        ? `<span style="font-weight: 600; color: var(--accent);">${o.performance_rating.toFixed(1)}</span>`
        : `<span style="color: var(--text-3);">—</span>`;
      const scout = (o.author_username || "").split("@")[0];
      const opponentRaw = o.opponent || "";
      const opponentPretty = (typeof prettyClubName === "function") ? prettyClubName(opponentRaw) : opponentRaw;
      const opponentTrunc = opponentPretty.length > 18 ? opponentPretty.slice(0, 17) + "…" : opponentPretty;
      const rolesArr = Array.isArray(o.roles_played) ? o.roles_played : [];
      const rolesShown = rolesArr.slice(0, 3).map(r => r.replace("_", " ")).join(" · ");
      const rolesExtra = rolesArr.length > 3 ? ` +${rolesArr.length - 3}` : "";
      const rolesHtml = rolesArr.length
        ? `<span style="color: var(--text-2); font-size: 11px; font-weight: 500;">${escapeHtml(rolesShown)}${rolesExtra}</span>`
        : `<span style="color: var(--text-3); font-size: 11px;">—</span>`;
      const compTrunc = (o.competition || "").length > 16 ? (o.competition || "").slice(0, 15) + "…" : (o.competition || "");
      let modeHtml = `<span style="color: var(--text-3); font-size: 11px;">—</span>`;
      if (o.viewing_mode === "LIVE") {
        modeHtml = `<span style="display: inline-flex; align-items: center; gap: 5px; padding: 3px 8px 3px 5px; border-radius: 999px; background: rgba(34,197,94,0.15); color: #22C55E; font-size: 10px; font-weight: 600; letter-spacing: 0.04em;"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><line x1="3" y1="12" x2="21" y2="12"/><circle cx="12" cy="12" r="2" fill="currentColor"/></svg>LIVE</span>`;
      } else if (o.viewing_mode === "TV") {
        modeHtml = `<span style="display: inline-flex; align-items: center; gap: 5px; padding: 3px 8px 3px 5px; border-radius: 999px; background: rgba(96,165,250,0.15); color: #60A5FA; font-size: 10px; font-weight: 600; letter-spacing: 0.04em;"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="14" rx="2"/><line x1="8" y1="22" x2="16" y2="22"/></svg>TV/VIDEO</span>`;
      }
      return `
        <tr class="obs-row" data-obs-id="${o.id}" style="cursor: pointer; border-bottom: 0.5px solid var(--border);">
          <td style="padding: 7px 8px; color: var(--text-2); font-size: 12px; white-space: nowrap;">${dateFmt}</td>
          <td style="padding: 7px 8px; color: var(--text-1); font-size: 12px; font-weight: 500;">${escapeHtml(opponentTrunc)}</td>
          <td class="obs-col-comp" style="padding: 7px 8px; color: var(--text-2); font-size: 12px;">${escapeHtml(compTrunc)}</td>
          <td class="obs-col-role" style="padding: 7px 8px;">${rolesHtml}</td>
          <td class="obs-col-mode" style="padding: 7px 8px;">${modeHtml}</td>
          <td class="obs-col-scout" style="padding: 7px 8px; color: var(--text-2); font-size: 12px;">${escapeHtml(scout)}</td>
          <td style="padding: 7px 8px; font-size: 13px;">${ratingHtml}</td>
          <td style="padding: 7px 8px;">${tagHtml}</td>
        </tr>
      `;
    }).join("");

    // Footer: media performance + distribuzione giudizi
    // ⚠️  Escludiamo le osservazioni con tag NON VALUTABILE da media performance e distribuzione %
    const isEvaluable = (obs) => obs.evaluation_tags?.[0] !== "NON VALUTABILE";
    const evaluableObs = obsList.filter(isEvaluable);
    const ratings = evaluableObs.map(o => o.performance_rating).filter(r => r != null);
    const avg = ratings.length ? (ratings.reduce((a, b) => a + b, 0) / ratings.length) : null;

    // Distribuzione giudizi (in %) — solo osservazioni con tag valutativo (escludo NON VALUTABILE)
    const tagCounts = {};
    evaluableObs.forEach(o => {
      const tag = o.evaluation_tags?.[0];
      if (tag) tagCounts[tag] = (tagCounts[tag] || 0) + 1;
    });
    const totalTagged = Object.values(tagCounts).reduce((a, b) => a + b, 0);
    let distribHtml = "";
    if (totalTagged > 0) {
      // Ordine: PRIMA → SECONDA → MONITOR → REJECT (migliore a sinistra nel footer per leggibilità)
      const orderedTags = ["PRIMA SCELTA", "SECONDA SCELTA", "DA MONITORARE", "NON IDONEO"]; // NON VALUTABILE escluso da distribuzione %
      distribHtml = orderedTags
        .filter(tag => tagCounts[tag])
        .map(tag => {
          const def = window.OBSERVATION_TAGS.find(t => t.value === tag);
          const pct = Math.round((tagCounts[tag] / totalTagged) * 100);
          return `<span style="color: ${def.color}; font-weight: 600;">${escapeHtml(window.obsLocalize(tag))} ${pct}%</span>`;
        })
        .join(`<span style="color: var(--text-3); margin: 0 6px;">·</span>`);
    } else {
      distribHtml = `<span style="color: var(--text-3);">—</span>`;
    }

    wrapper.innerHTML = `
      <style>
        @media (max-width: 700px) {
          #obs-dashboard-${pid} .obs-col-comp,
          #obs-dashboard-${pid} .obs-col-role,
          #obs-dashboard-${pid} .obs-col-scout { display: none; }
        }
      </style>
      <table style="width: 100%; border-collapse: collapse; margin-bottom: 10px;">
        <thead>
          <tr style="border-bottom: 0.5px solid var(--border);">
            <th style="padding: 6px 8px; text-align: left; font-size: 10px; font-weight: 500; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.05em;">${window.obsT("th_date")}</th>
            <th style="padding: 6px 8px; text-align: left; font-size: 10px; font-weight: 500; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.05em;">${window.obsT("th_opponent")}</th>
            <th class="obs-col-comp" style="padding: 6px 8px; text-align: left; font-size: 10px; font-weight: 500; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.05em;">${window.obsT("th_competition")}</th>
            <th class="obs-col-role" style="padding: 6px 8px; text-align: left; font-size: 10px; font-weight: 500; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.05em;">${window.obsT("th_role")}</th>
            <th class="obs-col-mode" style="padding: 6px 8px; text-align: left; font-size: 10px; font-weight: 500; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.05em;">${window.obsT("th_mode")}</th>
            <th class="obs-col-scout" style="padding: 6px 8px; text-align: left; font-size: 10px; font-weight: 500; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.05em;">${window.obsT("th_scout")}</th>
            <th style="padding: 6px 8px; text-align: left; font-size: 10px; font-weight: 500; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.05em;">${window.obsT("th_perf")}</th>
            <th style="padding: 6px 8px; text-align: left; font-size: 10px; font-weight: 500; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.05em;">${window.obsT("th_verdict")}</th>
          </tr>
        </thead>
        <tbody>
          ${rowsHtml}
        </tbody>
      </table>
      <div style="display: flex; gap: 16px; flex-wrap: wrap; padding: 10px 8px; background: rgba(255,255,255,0.03); border-radius: 8px; font-size: 11px;">
        <div>
          <span style="color: var(--text-3); text-transform: uppercase; letter-spacing: 0.05em; font-size: 10px;">${window.obsT("footer_avg")}:</span>
          <span style="color: var(--accent); font-weight: 700; font-size: 14px; margin-left: 6px;">${avg != null ? avg.toFixed(2) : "—"}</span>
        </div>
        <div style="flex: 1; min-width: 200px;">
          <span style="color: var(--text-3); text-transform: uppercase; letter-spacing: 0.05em; font-size: 10px;">${window.obsT("footer_distrib")}:</span>
          <span style="margin-left: 6px;">${distribHtml}</span>
        </div>
      </div>
    `;

    // Wire click su righe → apre modal di modifica
    wrapper.querySelectorAll(".obs-row").forEach(row => {
      row.addEventListener("click", () => {
        window.openObservationCompose(pid, row.dataset.obsId);
      });
      // Hover effect
      row.addEventListener("mouseenter", () => row.style.background = "rgba(255,255,255,0.04)");
      row.addEventListener("mouseleave", () => row.style.background = "transparent");
    });
  } catch (e) {
    console.warn("[obs-ui] dashboard error:", e);
    wrapper.innerHTML = `<div style="font-size: 12px; color: #EF4444;">Errore caricamento osservazioni</div>`;
  }
};

window.wireObservationsHandlers = function(pid) {
  const newBtn = document.getElementById(`obs-new-btn-${pid}`);
  if (newBtn) newBtn.addEventListener("click", () => window.openObservationCompose(pid));
  window.renderObservationsList(pid);
};

// ============================================================
//  MODAL "Nuova / Modifica Osservazione" — layout 2 colonne
// ============================================================

window._obsCompose = { pid: null, editId: null, selectedRoles: [], selectedTag: null, selectedStrengths: [], selectedWeaknesses: [], selectedViewingMode: null };

window.openObservationCompose = async function(pid, obsId = null) {
  const player = state.players.find(p => p.tm_player_id === pid);
  if (!player) return;

  let editing = null;
  if (obsId) {
    const list = window._obsCache[pid] || await window.fetchObservations({ tm_player_id: pid });
    editing = list.find(o => o.id === obsId);
    if (!editing) {
      alert("Osservazione non trovata");
      return;
    }
  }

  window._obsCompose = {
    pid: pid,
    editId: obsId,
    selectedRoles: editing ? [...(editing.roles_played || [])] : [],
    selectedTag: editing ? (editing.evaluation_tags?.[0] || null) : null,
    selectedStrengths: editing ? [...(editing.strengths || [])] : [],
    selectedWeaknesses: editing ? [...(editing.weaknesses || [])] : [],
    selectedViewingMode: editing ? (editing.viewing_mode || null) : null,
  };

  document.getElementById("obs-compose-overlay")?.remove();
  document.body.insertAdjacentHTML("beforeend", _obsComposeHtml(player, editing));
  setTimeout(() => _wireObsCompose(player, editing), 0);
};

function _obsComposeHtml(player, editing) {
  const isEdit = !!editing;
  const title = isEdit ? window.obsT("edit_obs") : window.obsT("new_obs_title");
  const pName = escapeHtml((typeof prettyClubName === "function" ? player.full_name : player.full_name) || `#${player.tm_player_id}`);
  const today = new Date().toISOString().slice(0, 10);

  const v = {
    match_date: editing?.match_date || today,
    opponent: editing?.opponent || "",
    competition: editing?.competition || "",
    competition_is_other: editing && !window.OBSERVATION_COMPETITIONS.includes(editing.competition),
    rating: editing?.performance_rating != null ? editing.performance_rating : 6.0,
    notes: editing?.notes || "",
  };

  const competitionOptions = window.OBSERVATION_COMPETITIONS.map(c => {
    const sel = (v.competition === c || (v.competition_is_other && c === "Altro")) ? " selected" : "";
    return `<option value="${escapeHtml(c)}"${sel}>${escapeHtml(c)}</option>`;
  }).join("");

  const fieldSvg = _renderRoleFieldSvg(window._obsCompose.selectedRoles);

  // Tag chips: ordine da peggiore a migliore
  const tagChips = window.OBSERVATION_TAGS.map(tg => {
    const isOn = window._obsCompose.selectedTag === tg.value;
    return `<button type="button" class="obs-tag-chip" data-tag="${escapeHtml(tg.value)}"
      style="font-size: 11px; font-weight: 600; padding: 5px 12px; border-radius: 999px; cursor: pointer; border: 0.5px solid ${tg.color}; background: ${isOn ? tg.color : "transparent"}; color: ${isOn ? "#fff" : tg.color}; white-space: nowrap;">${escapeHtml(window.obsLocalize(tg.value))}</button>`;
  }).join(" ");

  // Trait chips per categorie (per strengths in verde, per weaknesses in rosso)
  const renderCategorizedChips = (selected, accentColor) => {
    return Object.entries(window.OBSERVATION_TRAITS_BY_CATEGORY).map(([cat, traits]) => {
      const chipsHtml = traits.map(t => {
        const isOn = selected.includes(t);
        return `<button type="button" class="obs-chip" data-trait="${escapeHtml(t)}"
          style="font-size: 10px; padding: 3px 8px; border-radius: 999px; cursor: pointer; border: 0.5px solid ${isOn ? accentColor : "var(--border)"}; background: ${isOn ? accentColor + "22" : "transparent"}; color: ${isOn ? accentColor : "var(--text-2)"}; white-space: nowrap;">${escapeHtml(window.obsLocalize(t))}</button>`;
      }).join(" ");
      return `
        <div style="margin-bottom: 8px;">
          <div style="font-size: 9px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px; font-weight: 600;">${escapeHtml(window.obsLocalize(cat))}</div>
          <div style="display: flex; flex-wrap: wrap; gap: 3px;">${chipsHtml}</div>
        </div>
      `;
    }).join("");
  };

  // Datalist avversari con prettyClubName
  const opponentOptions = (state.clubs || [])
    .map(c => {
      const raw = c.name || c.club_name || "";
      const pretty = (typeof prettyClubName === "function") ? prettyClubName(raw) : raw;
      return pretty;
    })
    .filter(n => n)
    .filter((n, i, arr) => arr.indexOf(n) === i)
    .sort()
    .map(n => `<option value="${escapeHtml(n)}">`)
    .join("");

  return `
  <div id="obs-compose-overlay"
    style="position: fixed; inset: 0; background: rgba(0,0,0,0.85); z-index: 100; display: flex; align-items: flex-start; justify-content: center; overflow-y: auto; padding: 20px;">
    <style>
      .obs-compose-card {
        background: #1a1d24;
        color: var(--text-1);
        width: 100%;
        max-width: 1080px;
        border-radius: 16px;
        padding: 22px;
        border: 1px solid var(--border);
        margin: 20px 0;
        box-shadow: 0 20px 60px rgba(0,0,0,0.5);
      }
      .obs-compose-grid {
        display: grid;
        grid-template-columns: 1.4fr 1fr;
        gap: 24px;
      }
      @media (max-width: 900px) {
        .obs-compose-grid { grid-template-columns: 1fr; }
      }
      .obs-traits-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
      }
      @media (max-width: 700px) {
        .obs-traits-grid { grid-template-columns: 1fr; }
      }
      .obs-input-base {
        width: 100%; padding: 8px 10px; border-radius: 8px;
        background: rgba(255,255,255,0.06); color: var(--text-1);
        border: 0.5px solid var(--border); font-size: 13px;
      }
      .obs-label {
        font-size: 11px; color: var(--text-3); display: block; margin-bottom: 4px;
        text-transform: uppercase; letter-spacing: 0.05em; font-weight: 500;
      }
    </style>

    <div class="obs-compose-card">
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 18px;">
        <div>
          <div style="font-size: 11px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.1em;">${pName}</div>
          <div style="font-size: 18px; font-weight: 600; margin-top: 2px;">${title}</div>
        </div>
        <button type="button" id="obs-cancel-btn" style="font-size: 22px; background: transparent; border: none; color: var(--text-3); cursor: pointer; padding: 4px 8px;">✕</button>
      </div>

      <!-- LAYOUT 2 COLONNE -->
      <div class="obs-compose-grid">

        <!-- COLONNA SINISTRA: form -->
        <div>
          <!-- VISIONE: LIVE / TV-VIDEO (obbligatorio) -->
          <div style="margin-bottom: 12px;">
            <label class="obs-label">${window.obsT("f_viewing_mode")} *</label>
            <div id="obs-viewing-chips" style="display: flex; gap: 8px;">
              <button type="button" class="obs-viewing-chip" data-mode="LIVE"
                style="flex: 1; display: flex; align-items: center; justify-content: center; gap: 6px; font-size: 12px; font-weight: 600; padding: 8px 14px; border-radius: 8px; cursor: pointer; border: 0.5px solid ${window._obsCompose.selectedViewingMode === "LIVE" ? "#22C55E" : "var(--border)"}; background: ${window._obsCompose.selectedViewingMode === "LIVE" ? "rgba(34,197,94,0.15)" : "transparent"}; color: ${window._obsCompose.selectedViewingMode === "LIVE" ? "#22C55E" : "var(--text-2)"};">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><line x1="3" y1="12" x2="21" y2="12"/><circle cx="12" cy="12" r="2.5" fill="currentColor"/><line x1="3" y1="5" x2="21" y2="5"/></svg>
                ${window.obsT("f_viewing_live")}
              </button>
              <button type="button" class="obs-viewing-chip" data-mode="TV"
                style="flex: 1; display: flex; align-items: center; justify-content: center; gap: 6px; font-size: 12px; font-weight: 600; padding: 8px 14px; border-radius: 8px; cursor: pointer; border: 0.5px solid ${window._obsCompose.selectedViewingMode === "TV" ? "#60A5FA" : "var(--border)"}; background: ${window._obsCompose.selectedViewingMode === "TV" ? "rgba(96,165,250,0.15)" : "transparent"}; color: ${window._obsCompose.selectedViewingMode === "TV" ? "#60A5FA" : "var(--text-2)"};">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="14" rx="2"/><line x1="8" y1="22" x2="16" y2="22"/><line x1="12" y1="18" x2="12" y2="22"/></svg>
                ${window.obsT("f_viewing_tv")}
              </button>
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px;">
            <div>
              <label class="obs-label">${window.obsT("f_match_date")} *</label>
              <input id="obs-match-date" type="date" value="${v.match_date}" class="obs-input-base">
            </div>
            <div>
              <label class="obs-label">${window.obsT("f_opponent")} *</label>
              <input id="obs-opponent" type="text" placeholder="${window.obsT("f_opponent_ph")}" list="obs-opponent-list" class="obs-input-base" autocomplete="off">
              <datalist id="obs-opponent-list">${opponentOptions}</datalist>
            </div>
          </div>

          <div style="margin-bottom: 12px;">
            <label class="obs-label">${window.obsT("f_competition")} *</label>
            <select id="obs-competition" class="obs-input-base">
              <option value="">—</option>
              ${competitionOptions}
            </select>
            <input id="obs-competition-other" type="text" placeholder="${window.obsT("f_competition_other")}"
              value="${v.competition_is_other ? escapeHtml(v.competition) : ""}"
              class="obs-input-base"
              style="display: ${v.competition_is_other ? "block" : "none"}; margin-top: 8px;">
          </div>

          <div style="margin-bottom: 12px;">
            <label class="obs-label">${window.obsT("f_notes")}</label>
            <textarea id="obs-notes" rows="10" placeholder="${window.obsT("f_notes_ph")}"
              style="width: 100%; padding: 10px; border-radius: 8px; background: rgba(255,255,255,0.06); color: var(--text-1); border: 0.5px solid var(--border); font-size: 13px; resize: vertical; font-family: inherit; min-height: 200px;">${escapeHtml(v.notes)}</textarea>
          </div>

          <div style="margin-bottom: 12px;">
            <label class="obs-label">${window.obsT("f_rating")}</label>
            <div style="display: flex; align-items: center; gap: 12px;">
              <input id="obs-rating" type="range" min="0" max="10" step="0.5" value="${v.rating}"
                style="flex: 1; accent-color: var(--accent);">
              <div id="obs-rating-display" style="font-size: 22px; font-weight: 700; color: var(--accent); width: 50px; text-align: center;">${v.rating.toFixed(1)}</div>
            </div>
          </div>

          <div style="margin-bottom: 12px;">
            <label class="obs-label">${window.obsT("f_tag")}</label>
            <div id="obs-tag-chips" style="display: flex; flex-wrap: wrap; gap: 6px;">${tagChips}</div>
          </div>
        </div>

        <!-- COLONNA DESTRA: campo grafico ruoli (rimpicciolito) -->
        <div>
          <label class="obs-label">${window.obsT("f_roles")} *</label>
          <div style="font-size: 10px; color: var(--text-3); margin-bottom: 6px;">${window.obsT("f_roles_hint")}</div>
          <div id="obs-field-wrap" style="display: flex; justify-content: center; padding: 10px; background: rgba(255,255,255,0.03); border-radius: 12px; border: 0.5px solid var(--border);">
            ${fieldSvg}
          </div>
        </div>
      </div>

      <!-- STRENGTHS / WEAKNESSES SIDE BY SIDE -->
      <div class="obs-traits-grid" style="margin-top: 18px;">
        <div>
          <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 8px;">
            <div style="width: 3px; height: 14px; background: #22C55E; border-radius: 2px;"></div>
            <span style="font-size: 12px; font-weight: 700; color: #22C55E; text-transform: uppercase; letter-spacing: 0.06em;">${window.obsT("f_strengths")}</span>
          </div>
          <div id="obs-strengths-chips">${renderCategorizedChips(window._obsCompose.selectedStrengths, "#22C55E")}</div>
        </div>
        <div>
          <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 8px;">
            <div style="width: 3px; height: 14px; background: #EF4444; border-radius: 2px;"></div>
            <span style="font-size: 12px; font-weight: 700; color: #EF4444; text-transform: uppercase; letter-spacing: 0.06em;">${window.obsT("f_weaknesses")}</span>
          </div>
          <div id="obs-weaknesses-chips">${renderCategorizedChips(window._obsCompose.selectedWeaknesses, "#EF4444")}</div>
        </div>
      </div>

      <!-- ERROR + BUTTONS -->
      <div id="obs-error" style="display: none; padding: 8px 12px; margin-top: 16px; border-radius: 8px; background: rgba(239,68,68,0.15); color: #EF4444; font-size: 12px; border: 0.5px solid rgba(239,68,68,0.4);"></div>

      <div style="display: flex; gap: 8px; justify-content: flex-end; margin-top: 18px;">
        <button type="button" id="obs-cancel-btn-2"
          style="font-size: 13px; padding: 8px 16px; border-radius: 8px; background: transparent; color: var(--text-2); border: 0.5px solid var(--border); cursor: pointer;">${window.obsT("btn_cancel")}</button>
        <button type="button" id="obs-save-btn"
          style="font-size: 13px; padding: 8px 18px; border-radius: 8px; background: var(--accent); color: #fff; border: none; cursor: pointer; font-weight: 500;">${window.obsT("btn_save")}</button>
      </div>
    </div>
  </div>
  `;
}

/**
 * SVG campo rimpicciolito (220px circa).
 */
function _renderRoleFieldSvg(selectedRoles) {
  const W = 380, H = 540;
  const lines = `
    <rect width="${W}" height="${H}" fill="#1B7A3E" rx="4"/>
    <rect x="20" y="20" width="${W-40}" height="${H-40}" fill="none" stroke="#fff" stroke-width="1.5" opacity="0.55"/>
    <line x1="20" y1="${H/2}" x2="${W-20}" y2="${H/2}" stroke="#fff" stroke-width="1.5" opacity="0.55"/>
    <circle cx="${W/2}" cy="${H/2}" r="50" fill="none" stroke="#fff" stroke-width="1.5" opacity="0.55"/>
    <circle cx="${W/2}" cy="${H/2}" r="2" fill="#fff" opacity="0.55"/>
    <rect x="${W/2-80}" y="20" width="160" height="65" fill="none" stroke="#fff" stroke-width="1.5" opacity="0.55"/>
    <rect x="${W/2-40}" y="20" width="80" height="25" fill="none" stroke="#fff" stroke-width="1.5" opacity="0.55"/>
    <rect x="${W/2-80}" y="${H-85}" width="160" height="65" fill="none" stroke="#fff" stroke-width="1.5" opacity="0.55"/>
    <rect x="${W/2-40}" y="${H-45}" width="80" height="25" fill="none" stroke="#fff" stroke-width="1.5" opacity="0.55"/>
  `;
  const circles = window.OBSERVATION_ROLE_DEFS.map(r => {
    const isOn = selectedRoles.includes(r.code);
    const fill = isOn ? "#FBBF24" : "rgba(255,255,255,0.85)";
    const txt = isOn ? "#000" : "#1B7A3E";
    const stroke = isOn ? "#000" : "rgba(0,0,0,0.3)";
    return `
      <g class="obs-role-circle" data-role="${r.code}" style="cursor: pointer;">
        <circle cx="${r.cx}" cy="${r.cy}" r="22" fill="${fill}" stroke="${stroke}" stroke-width="1.5"/>
        <text x="${r.cx}" y="${r.cy + 4}" text-anchor="middle" font-size="10" font-weight="700" fill="${txt}" pointer-events="none">${r.code.replace("_", " ")}</text>
      </g>
    `;
  }).join("");
  // viewBox originale ma rendering size più piccolo (responsive)
  return `<svg viewBox="0 0 ${W} ${H}" style="width: 100%; max-width: 240px; height: auto; display: block;" xmlns="http://www.w3.org/2000/svg">${lines}${circles}</svg>`;
}

function _redrawField() {
  const wrap = document.getElementById("obs-field-wrap");
  if (wrap) wrap.innerHTML = _renderRoleFieldSvg(window._obsCompose.selectedRoles);
  _wireFieldClicks();
}

function _wireFieldClicks() {
  document.querySelectorAll(".obs-role-circle").forEach(g => {
    g.addEventListener("click", () => {
      const code = g.dataset.role;
      const idx = window._obsCompose.selectedRoles.indexOf(code);
      if (idx >= 0) window._obsCompose.selectedRoles.splice(idx, 1);
      else window._obsCompose.selectedRoles.push(code);
      _redrawField();
    });
  });
}

function _wireObsCompose(player, editing) {
  document.getElementById("obs-cancel-btn")?.addEventListener("click", _closeObsCompose);
  document.getElementById("obs-cancel-btn-2")?.addEventListener("click", _closeObsCompose);
  document.getElementById("obs-compose-overlay")?.addEventListener("click", (e) => {
    if (e.target.id === "obs-compose-overlay") _closeObsCompose();
  });

  // Fix bug input avversario non modificabile in edit mode:
  // settiamo il valore via JS DOPO il render invece che inline su `value=""` HTML
  // (il combo `<input value list>` di HTML5 ha glitch noti in edit mode)
  const opponentInput = document.getElementById("obs-opponent");
  if (opponentInput && editing && editing.opponent) {
    opponentInput.value = editing.opponent;
  }

  _wireFieldClicks();

  const slider = document.getElementById("obs-rating");
  const display = document.getElementById("obs-rating-display");
  slider?.addEventListener("input", () => {
    display.textContent = parseFloat(slider.value).toFixed(1);
  });

  const compSel = document.getElementById("obs-competition");
  const compOther = document.getElementById("obs-competition-other");
  compSel?.addEventListener("change", () => {
    if (compSel.value === "Altro") {
      compOther.style.display = "block";
      compOther.focus();
    } else {
      compOther.style.display = "none";
      compOther.value = "";
    }
  });

  // Wire chip LIVE/TV (single-select obbligatorio)
  document.querySelectorAll(".obs-viewing-chip").forEach(btn => {
    btn.addEventListener("click", () => {
      const mode = btn.dataset.mode;
      window._obsCompose.selectedViewingMode = (window._obsCompose.selectedViewingMode === mode) ? null : mode;
      // Re-render entrambe le chip
      document.querySelectorAll(".obs-viewing-chip").forEach(b => {
        const m = b.dataset.mode;
        const isOn = window._obsCompose.selectedViewingMode === m;
        const color = m === "LIVE" ? "#22C55E" : "#60A5FA";
        const bgRgba = m === "LIVE" ? "rgba(34,197,94,0.15)" : "rgba(96,165,250,0.15)";
        b.style.borderColor = isOn ? color : "var(--border)";
        b.style.background = isOn ? bgRgba : "transparent";
        b.style.color = isOn ? color : "var(--text-2)";
      });
    });
  });

  document.querySelectorAll(".obs-tag-chip").forEach(btn => {
    btn.addEventListener("click", () => {
      const v = btn.dataset.tag;
      window._obsCompose.selectedTag = (window._obsCompose.selectedTag === v) ? null : v;
      document.querySelectorAll(".obs-tag-chip").forEach(b => {
        const tg = window.OBSERVATION_TAGS.find(t => t.value === b.dataset.tag);
        const on = window._obsCompose.selectedTag === b.dataset.tag;
        b.style.background = on ? tg.color : "transparent";
        b.style.color = on ? "#fff" : tg.color;
      });
    });
  });

  function _wireTraitChips(containerId, listKey, accentColor) {
    document.getElementById(containerId)?.querySelectorAll(".obs-chip").forEach(btn => {
      btn.addEventListener("click", () => {
        const trait = btn.dataset.trait;
        const list = window._obsCompose[listKey];
        const idx = list.indexOf(trait);
        if (idx >= 0) list.splice(idx, 1);
        else list.push(trait);
        const isOn = idx < 0;
        btn.style.borderColor = isOn ? accentColor : "var(--border)";
        btn.style.background = isOn ? accentColor + "22" : "transparent";
        btn.style.color = isOn ? accentColor : "var(--text-2)";
      });
    });
  }
  _wireTraitChips("obs-strengths-chips", "selectedStrengths", "#22C55E");
  _wireTraitChips("obs-weaknesses-chips", "selectedWeaknesses", "#EF4444");

  document.getElementById("obs-save-btn")?.addEventListener("click", () => _saveObsFromForm(player, editing));

  // Bottone elimina (solo edit mode)
  if (editing) {
    const cancelBtn2 = document.getElementById("obs-cancel-btn-2");
    if (cancelBtn2 && !document.getElementById("obs-delete-btn")) {
      const delBtn = document.createElement("button");
      delBtn.type = "button";
      delBtn.id = "obs-delete-btn";
      delBtn.textContent = window.obsT("btn_delete");
      delBtn.style.cssText = "font-size: 13px; padding: 8px 16px; border-radius: 8px; background: transparent; color: #EF4444; border: 0.5px solid rgba(239,68,68,0.4); cursor: pointer; margin-right: auto;";
      delBtn.addEventListener("click", async () => {
        if (!confirm(window.obsT("delete_confirm"))) return;
        const r = await window.deleteObservation(editing.id);
        if (r.ok) {
          _closeObsCompose();
          window.renderObservationsList(player.tm_player_id);
          window._obsAllCache = null; // invalida cache pannello scouting
        } else {
          alert(r.error || "Errore eliminazione");
        }
      });
      cancelBtn2.parentElement.insertBefore(delBtn, cancelBtn2);
    }
  }
}

function _closeObsCompose() {
  document.getElementById("obs-compose-overlay")?.remove();
}

async function _saveObsFromForm(player, editing) {
  const errEl = document.getElementById("obs-error");
  const showErr = (msg) => { errEl.textContent = msg; errEl.style.display = "block"; };
  const hideErr = () => { errEl.style.display = "none"; };
  hideErr();

  const matchDate = document.getElementById("obs-match-date").value;
  const opponent = document.getElementById("obs-opponent").value.trim();
  const compSel = document.getElementById("obs-competition").value;
  const compOther = document.getElementById("obs-competition-other").value.trim();
  const competition = (compSel === "Altro") ? compOther : compSel;
  const rating = parseFloat(document.getElementById("obs-rating").value);
  const notes = document.getElementById("obs-notes").value.trim();

  if (!matchDate || !opponent || !competition) {
    showErr(window.obsT("err_required"));
    return;
  }
  if (!window._obsCompose.selectedViewingMode) {
    showErr(window.obsT("err_required"));
    return;
  }
  if (!window._obsCompose.selectedRoles.length) {
    showErr(window.obsT("err_no_role"));
    return;
  }
  if (!window._obsCompose.selectedTag) {
    showErr(window.obsT("err_no_tag"));
    return;
  }

  const payload = {
    tm_player_id: player.tm_player_id,
    match_date: matchDate,
    opponent: opponent,
    competition: competition,
    viewing_mode: window._obsCompose.selectedViewingMode,
    performance_rating: rating,
    roles_played: window._obsCompose.selectedRoles,
    evaluation_tags: window._obsCompose.selectedTag ? [window._obsCompose.selectedTag] : [],
    strengths: window._obsCompose.selectedStrengths,
    weaknesses: window._obsCompose.selectedWeaknesses,
    notes: notes || null,
  };

  let result;
  if (editing) {
    result = await window.updateObservation(editing.id, payload);
  } else {
    result = await window.saveObservation(payload);
  }

  if (result.error) {
    if (result.error === "duplicato" || (result.error.code === "23505")) {
      showErr(window.obsT("err_duplicate"));
    } else {
      showErr(result.error);
    }
    return;
  }

  _closeObsCompose();
  window._obsAllCache = null; // invalida cache pannello scouting
  if (typeof window.renderObservationsList === "function") {
    window.renderObservationsList(player.tm_player_id);
  }
}

// ============================================================
//  PANNELLO "SCOUTING" SIDEBAR (Fase 4 base anticipata)
//  Vista globale di tutte le osservazioni dell'utente.
// ============================================================

/**
 * HTML del pannello principale Scouting (per il main content quando si seleziona la voce sidebar).
 * Layout: tabella stile Lista. Foto + Nome+Anno | Età | Ruolo | Piede | Media | Distribuzione % con label | Oss | ▼
 * Click sul nome → modal giocatore. Click sul resto della riga → espande/collassa osservazioni inline allineate alle colonne.
 */
window.renderScoutingPanel = function() {
  return `
    <div id="scouting-panel" style="padding: 24px;">
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
        <div style="display: flex; align-items: center; gap: 12px;">
          <div style="width: 4px; height: 24px; background: var(--accent); border-radius: 2px;"></div>
          <h2 style="font-size: 22px; font-weight: 600; margin: 0; color: var(--text-1);">${window.obsT("scouting_title")}</h2>
        </div>
        <div id="scouting-summary-chip" style="font-size: 12px; color: var(--text-3);">…</div>
      </div>
      <div id="scouting-content">…</div>
    </div>
  `;
};

window.wireScoutingPanel = async function() {
  const contentEl = document.getElementById("scouting-content");
  const summaryEl = document.getElementById("scouting-summary-chip");
  if (!contentEl) return;

  try {
    if (!window._obsAllCache) {
      window._obsAllCache = await window.fetchObservations();
    }
    const all = window._obsAllCache;

    if (!all.length) {
      summaryEl.textContent = "";
      contentEl.innerHTML = `<div style="padding: 40px; text-align: center; color: var(--text-3); font-size: 13px; background: rgba(255,255,255,0.03); border-radius: 12px; border: 0.5px solid var(--border);">${window.obsT("scouting_no_obs")}</div>`;
      return;
    }

    // Raggruppa per giocatore
    const byPlayer = {};
    all.forEach(o => {
      if (!byPlayer[o.tm_player_id]) byPlayer[o.tm_player_id] = [];
      byPlayer[o.tm_player_id].push(o);
    });
    const playerIds = Object.keys(byPlayer);

    summaryEl.innerHTML = `
      <span style="color: var(--accent); font-weight: 600;">${playerIds.length}</span> ${window.obsT("scouting_summary")} · 
      <span style="color: var(--accent); font-weight: 600;">${all.length}</span> ${window.obsT("scouting_total_obs")}
    `;

    const dateLocale = (typeof currentLang !== "undefined" && currentLang === "it") ? "it-IT" : "en-GB";
    const isIt = (typeof currentLang !== "undefined" && currentLang === "it");
    const localize = (val) => (typeof localizeRole === "function") ? localizeRole(val) : val;

    // Localizzazione piede
    const localizeFoot = (foot) => {
      if (!foot) return "—";
      const f = String(foot).toLowerCase();
      const dictIt = { right: "Destro", left: "Sinistro", both: "Entrambi" };
      const dictEn = { right: "Right", left: "Left", both: "Both" };
      const dict = isIt ? dictIt : dictEn;
      return dict[f] || foot;
    };

    // Sort giocatori: media performance desc, poi nome
    playerIds.sort((aPid, bPid) => {
      const aRatings = byPlayer[aPid].filter(x => x.evaluation_tags?.[0] !== "NON VALUTABILE").map(o => o.performance_rating).filter(r => r != null);
      const bRatings = byPlayer[bPid].filter(x => x.evaluation_tags?.[0] !== "NON VALUTABILE").map(o => o.performance_rating).filter(r => r != null);
      const aAvg = aRatings.length ? aRatings.reduce((a, b) => a + b, 0) / aRatings.length : -1;
      const bAvg = bRatings.length ? bRatings.reduce((a, b) => a + b, 0) / bRatings.length : -1;
      if (Math.abs(bAvg - aAvg) > 0.001) return bAvg - aAvg;
      const aP = state.players.find(p => p.tm_player_id === parseInt(aPid));
      const bP = state.players.find(p => p.tm_player_id === parseInt(bPid));
      return (aP?.full_name || "").localeCompare(bP?.full_name || "");
    });

    // Grid layout: foto(48) | nome+anno(2fr) | età(60) | ruolo(140) | piede(80) | media(80) | distribuzione(2fr) | oss(60) | espandi(28)
    const GRID = "48px 2fr 60px 140px 80px 80px 2fr 60px 28px";

    const headerRow = `
      <div style="display: grid; grid-template-columns: ${GRID}; gap: 10px; align-items: center; padding: 10px 14px; border-bottom: 0.5px solid var(--border); font-size: 10px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.06em; font-weight: 500;">
        <span></span>
        <span>${isIt ? "Giocatore" : "Player"}</span>
        <span style="text-align: center;">${isIt ? "Età" : "Age"}</span>
        <span>${isIt ? "Ruolo" : "Role"}</span>
        <span style="text-align: center;">${isIt ? "Piede" : "Foot"}</span>
        <span style="text-align: center;">${isIt ? "Media" : "Avg"}</span>
        <span>${isIt ? "Distribuzione giudizi" : "Verdict distribution"}</span>
        <span style="text-align: center;">${isIt ? "Oss." : "Obs."}</span>
        <span></span>
      </div>
    `;

    const playerRowsHtml = playerIds.map(pid => {
      const obsForPlayer = byPlayer[pid].sort((a, b) => new Date(b.match_date) - new Date(a.match_date));
      const player = state.players.find(p => p.tm_player_id === parseInt(pid));
      const playerName = player ? (player.full_name || `#${pid}`) : `#${pid}`;
      // Foto: usa playerPhoto globale (stessa funzione della Lista)
      const photoSrc = (player && typeof playerPhoto === "function") ? playerPhoto(player) : "";
      const birthY = player ? (typeof birthYear === "function" ? birthYear(player) : "") : "";
      const age = player?.age || "—";
      const roleSpec = player?.position_specific || player?.position_general || "—";
      const foot = player?.foot;

      // Media performance (esclude NON VALUTABILE)
      const evaluableObs = obsForPlayer.filter(o => o.evaluation_tags?.[0] !== "NON VALUTABILE");
      const ratings = evaluableObs.map(o => o.performance_rating).filter(r => r != null);
      const avg = ratings.length ? (ratings.reduce((a, b) => a + b, 0) / ratings.length) : null;

      // Distribuzione giudizi (5 categorie)
      const tagCounts = {};
      obsForPlayer.forEach(o => {
        const t = o.evaluation_tags?.[0];
        if (t) tagCounts[t] = (tagCounts[t] || 0) + 1;
      });
      const totalTagged = Object.values(tagCounts).reduce((a, b) => a + b, 0);

      // Barra segmentata (sinistra→destra: peggiore→migliore)
      const tagOrder = ["NON VALUTABILE", "NON IDONEO", "DA MONITORARE", "SECONDA SCELTA", "PRIMA SCELTA"];
      // Label corte per la barra (per non occupare troppo spazio)
      // Etichette per esteso (con percentuale se segmento abbastanza largo)
      const fullLabelIt = {
        "NON VALUTABILE": "NON VALUTABILE",
        "NON IDONEO":     "NON IDONEO",
        "DA MONITORARE":  "DA MONITORARE",
        "SECONDA SCELTA": "SECONDA SCELTA",
        "PRIMA SCELTA":   "PRIMA SCELTA",
      };
      const fullLabelEn = {
        "NON VALUTABILE": "NOT EVALUABLE",
        "NON IDONEO":     "REJECT",
        "DA MONITORARE":  "MONITOR",
        "SECONDA SCELTA": "SECOND CHOICE",
        "PRIMA SCELTA":   "FIRST CHOICE",
      };
      const shortLabel = isIt ? fullLabelIt : fullLabelEn;

      let distribBarHtml = "";
      if (totalTagged > 0) {
        const segs = tagOrder
          .filter(tag => tagCounts[tag])
          .map(tag => {
            const def = window.OBSERVATION_TAGS.find(t => t.value === tag);
            const pct = (tagCounts[tag] / totalTagged) * 100;
            const pctRounded = Math.round(pct);
            const lbl = shortLabel[tag];
            // Etichette per esteso ("PRIMA SCELTA"=12 chars). Soglie più ampie:
            // >=33% → "LABEL XX%"; >=18% → solo "XX%"; <18% → solo tooltip
            let inner = "";
            if (pct >= 33) inner = `${lbl} ${pctRounded}%`;
            else if (pct >= 18) inner = `${pctRounded}%`;
            return `<div title="${escapeHtml(window.obsLocalize(tag))} ${pctRounded}%" style="flex: ${pct}; min-width: 0; height: 100%; background: ${def.color}; display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: 700; color: #0E1116; overflow: hidden; white-space: nowrap; padding: 0 4px;">${inner}</div>`;
          }).join("");
        distribBarHtml = `<div style="display: flex; height: 20px; border-radius: 4px; overflow: hidden; background: rgba(255,255,255,0.05);">${segs}</div>`;
      } else {
        distribBarHtml = `<span style="color: var(--text-3); font-size: 11px;">—</span>`;
      }

      // Righe osservazioni: layout allineato alle colonne header (stessa GRID)
      const obsExpandedRowsHtml = obsForPlayer.map(o => {
        const dateFmt = new Date(o.match_date).toLocaleDateString(dateLocale, { day: "2-digit", month: "2-digit", year: "2-digit" });
        const tagDef = window.OBSERVATION_TAGS.find(t => t.value === o.evaluation_tags?.[0]);
        const tagDot = tagDef ? `<span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: ${tagDef.color}; flex-shrink: 0;"></span>` : `<span style="display: inline-block; width: 8px; height: 8px;"></span>`;
        const tagLabel = tagDef
          ? `<span style="font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 999px; background: ${tagDef.color}22; color: ${tagDef.color}; border: 0.5px solid ${tagDef.color}; white-space: nowrap;">${escapeHtml(window.obsLocalize(tagDef.value))}</span>`
          : `<span style="color: var(--text-3); font-size: 11px;">—</span>`;
        const ratingStr = o.performance_rating != null ? o.performance_rating.toFixed(1) : "—";
        const opponentStr = (typeof prettyClubName === "function") ? prettyClubName(o.opponent) : o.opponent;
        // Ruoli giocati in questa osservazione
        const rolesArr = Array.isArray(o.roles_played) ? o.roles_played : [];
        const rolesShown = rolesArr.slice(0, 3).map(r => r.replace("_", " ")).join(" · ");
        const rolesExtra = rolesArr.length > 3 ? ` +${rolesArr.length - 3}` : "";
        const rolesObsHtml = rolesArr.length
          ? `<span style="color: var(--text-2); font-size: 11px;">${escapeHtml(rolesShown)}${rolesExtra}</span>`
          : `<span style="color: var(--text-3); font-size: 11px;">—</span>`;
        // Mode badge
        let modeBadge = `<span style="color: var(--text-3); font-size: 11px;">—</span>`;
        if (o.viewing_mode === "LIVE") {
          modeBadge = `<span style="font-size: 9px; font-weight: 700; padding: 2px 8px; border-radius: 999px; background: rgba(34,197,94,0.15); color: #22C55E;">LIVE</span>`;
        } else if (o.viewing_mode === "TV") {
          modeBadge = `<span style="font-size: 9px; font-weight: 700; padding: 2px 8px; border-radius: 999px; background: rgba(96,165,250,0.15); color: #60A5FA;">TV</span>`;
        }
        return `
          <div class="scouting-obs-row" data-pid="${pid}" data-obs-id="${o.id}" style="display: grid; grid-template-columns: ${GRID}; gap: 10px; align-items: center; padding: 8px 14px; border-bottom: 0.5px solid var(--border); cursor: pointer; transition: background 0.1s; background: rgba(255,255,255,0.015);">
            <div style="display: flex; justify-content: center;">${tagDot}</div>
            <div style="font-size: 12px; color: var(--text-2); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
              <span style="color: var(--text-3); margin-right: 6px;">${dateFmt}</span>vs ${escapeHtml(opponentStr)}<span style="color: var(--text-3); margin: 0 6px;">·</span><span style="color: var(--text-3); font-size: 11px;">${escapeHtml(o.competition || "")}</span>
            </div>
            <div></div>
            <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${rolesObsHtml}</div>
            <div style="text-align: center;">${modeBadge}</div>
            <div style="text-align: center; font-size: 14px; font-weight: 700; color: var(--accent);">${ratingStr}</div>
            <div>${tagLabel}</div>
            <div></div>
            <div></div>
          </div>
        `;
      }).join("");

      return `
        <div class="scouting-player-block" data-pid="${pid}">
          <div class="scouting-player-row" data-pid="${pid}" style="display: grid; grid-template-columns: ${GRID}; gap: 10px; align-items: center; padding: 10px 14px; border-bottom: 0.5px solid var(--border); cursor: pointer; transition: background 0.1s;">
            <img src="${photoSrc}" alt="" style="width: 44px; height: 44px; border-radius: 8px; object-fit: cover; background: var(--surface-2);"
              onerror="this.onerror=null;this.src='https://ui-avatars.com/api/?name=${encodeURIComponent(playerName)}&size=128&background=1A1F26&color=6FE0A8&bold=true&font-size=0.45'"/>
            <div class="scouting-player-name" data-pid="${pid}" style="min-width: 0; cursor: pointer;">
              <div style="font-size: 13px; font-weight: 600; color: var(--text-1); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(playerName)}</div>
              <div style="font-size: 11px; color: var(--text-3);">${escapeHtml(String(birthY || ""))}</div>
            </div>
            <div style="text-align: center; font-size: 12px; color: var(--text-2);">${age}</div>
            <div style="font-size: 12px; color: var(--text-2); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(localize(roleSpec))}</div>
            <div style="text-align: center; font-size: 12px; color: var(--text-2);">${escapeHtml(localizeFoot(foot))}</div>
            <div style="text-align: center;">
              ${avg != null
                ? `<span style="font-size: 18px; font-weight: 700; color: var(--accent);">${avg.toFixed(1)}</span>`
                : `<span style="color: var(--text-3); font-size: 12px;">—</span>`}
            </div>
            <div style="min-width: 0;">${distribBarHtml}</div>
            <div style="text-align: center; font-size: 12px; color: var(--text-2); font-weight: 500;">${obsForPlayer.length}</div>
            <div class="scouting-expand-icon" style="text-align: center; color: var(--text-3); font-size: 12px; transition: transform 0.2s;">▼</div>
          </div>
          <div class="scouting-obs-list" data-pid="${pid}" style="display: none; background: rgba(255,255,255,0.02);">
            ${obsExpandedRowsHtml}
          </div>
        </div>
      `;
    }).join("");

    contentEl.innerHTML = `
      <div style="background: rgba(255,255,255,0.03); border: 0.5px solid var(--border); border-radius: 12px; overflow: hidden;">
        ${headerRow}
        ${playerRowsHtml}
      </div>
    `;

    // Click sul nome → scheda giocatore (NON espande)
    contentEl.querySelectorAll(".scouting-player-name").forEach(el => {
      el.addEventListener("click", (e) => {
        e.stopPropagation();
        const pid = parseInt(el.dataset.pid);
        if (typeof openPlayerModal === "function") openPlayerModal(pid);
      });
      el.addEventListener("mouseenter", () => el.style.textDecoration = "underline");
      el.addEventListener("mouseleave", () => el.style.textDecoration = "none");
    });

    // Click sulla riga → espande/collassa osservazioni
    contentEl.querySelectorAll(".scouting-player-row").forEach(rowEl => {
      rowEl.addEventListener("click", () => {
        const pid = rowEl.dataset.pid;
        const obsList = contentEl.querySelector(`.scouting-obs-list[data-pid="${pid}"]`);
        const icon = rowEl.querySelector(".scouting-expand-icon");
        if (!obsList) return;
        const isOpen = obsList.style.display !== "none";
        obsList.style.display = isOpen ? "none" : "block";
        if (icon) icon.style.transform = isOpen ? "rotate(0deg)" : "rotate(180deg)";
      });
      rowEl.addEventListener("mouseenter", () => rowEl.style.background = "rgba(255,255,255,0.03)");
      rowEl.addEventListener("mouseleave", () => rowEl.style.background = "transparent");
    });

    // Click sulla riga osservazione → modifica
    contentEl.querySelectorAll(".scouting-obs-row").forEach(el => {
      el.addEventListener("mouseenter", () => el.style.background = "rgba(255,255,255,0.05)");
      el.addEventListener("mouseleave", () => el.style.background = "rgba(255,255,255,0.015)");
      el.addEventListener("click", (e) => {
        e.stopPropagation();
        const pid = parseInt(el.dataset.pid);
        const obsId = el.dataset.obsId;
        if (typeof window.openObservationCompose === "function") {
          window.openObservationCompose(pid, obsId);
        }
      });
    });

  } catch (e) {
    console.warn("[obs-ui] scouting panel error:", e);
    contentEl.innerHTML = `<div style="padding: 24px; color: #EF4444; font-size: 13px;">Errore caricamento: ${escapeHtml(String(e))}</div>`;
  }
};

console.log("[obs-ui] Fase 3 v2 modulo caricato");

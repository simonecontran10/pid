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
  { code: "AES",    it: "Esterno-quinto sinistro",   en: "Left wing-back",         cx: 45,  cy: 215 },
  { code: "AED",    it: "Esterno-quinto destro",     en: "Right wing-back",        cx: 335, cy: 215 },
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
      f_player_team: "Squadra giocatore",
      f_player_team_ph: "Es. Atalanta",
      th_player_team: "Squadra",
      th_match: "Match",
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
      f_minutes: "Minuti giocati (opzionale)",
      f_minutes_ph: "Es. 90", btn_edit: "Modifica",
      th_minutes: "Minuti",
      inserted_on: "Inserita il",
      no_notes: "Nessuna nota",
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
      f_player_team: "Player team",
      f_player_team_ph: "e.g. Atalanta",
      th_player_team: "Team",
      th_match: "Match",
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
      f_minutes: "Minutes played (optional)",
      f_minutes_ph: "e.g. 90", btn_edit: "Edit",
      th_minutes: "Minutes",
      inserted_on: "Created",
      no_notes: "No notes",
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
      // Match cell: player_team (snapshot storico) vs opponent, entrambi con logo
      const playerTeamRaw = o.player_team || "";
      const matchHtml = playerTeamRaw
        ? `${_obsRenderTeamInline(playerTeamRaw)}<span style="margin: 0 5px; color: var(--text-3); font-size: 10px;">vs</span>${_obsRenderTeamInline(opponentRaw)}`
        : _obsRenderTeamInline(opponentRaw);
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
          <td style="padding: 7px 8px; color: var(--text-1); font-size: 12px; font-weight: 500; white-space: nowrap;">${matchHtml}</td>
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
            <th style="padding: 6px 8px; text-align: left; font-size: 10px; font-weight: 500; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.05em;">${window.obsT("th_match")}</th>
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

  // Pre-fill da window._obsPrefill (impostato dal bottone "+ osservazione" sulle partite)
  // Solo per NUOVA osservazione (non per modifica)
  let prefill = null;
  if (!editing && window._obsPrefill) {
    prefill = window._obsPrefill;
    window._obsPrefill = null; // consume one-shot
  }

  document.getElementById("obs-compose-overlay")?.remove();
  document.body.insertAdjacentHTML("beforeend", _obsComposeHtml(player, editing, prefill));
  setTimeout(() => _wireObsCompose(player, editing), 0);
};

// ====================================================================
// HELPER: lookup club per nome (case-insensitive, match diretto o pretty)
// Cache lazy: ricostruita la prima volta che viene chiesta.
// Usata per renderizzare logo + nome per opponent e player_team
// (entrambi sono stringhe nel DB, non FK numerici).
// ====================================================================
let _obsClubsByNameCache = null;
function _obsGetClubByName(name) {
  if (!name || typeof name !== "string") return null;
  if (!_obsClubsByNameCache) {
    _obsClubsByNameCache = new Map();
    const clubs = (typeof state !== "undefined" && state.clubs) ? state.clubs : [];
    for (const c of clubs) {
      const raw = c.name || c.club_name || "";
      if (raw) _obsClubsByNameCache.set(raw.toLowerCase(), c);
      const pretty = (typeof prettyClubName === "function") ? prettyClubName(raw) : raw;
      if (pretty && pretty !== raw) _obsClubsByNameCache.set(pretty.toLowerCase(), c);
    }
  }
  return _obsClubsByNameCache.get(name.toLowerCase()) || null;
}

// Render inline "[logo] Nome" usato in tabella + sidebar.
// Stile coerente con il resto: logo 14x14, nome testo normale.
function _obsRenderTeamInline(name) {
  if (!name) return '<span style="color: var(--text-3);">—</span>';
  const pretty = (typeof prettyClubName === "function") ? prettyClubName(name) : name;
  const club = _obsGetClubByName(name);
  const logo = (club && typeof clubLogo === "function") ? clubLogo(club) : "";
  const logoHtml = logo
    ? '<img src="' + logo + '" alt="" style="width: 14px; height: 14px; object-fit: contain; flex-shrink: 0;" onerror="this.style.display=\'none\'"/>'
    : "";
  return '<span style="display: inline-flex; align-items: center; gap: 5px; vertical-align: middle;">' + logoHtml + '<span>' + escapeHtml(pretty) + '</span></span>';
}

function _obsComposeHtml(player, editing, prefill) {
  const isEdit = !!editing;
  const title = isEdit ? window.obsT("edit_obs") : window.obsT("new_obs_title");
  const pName = escapeHtml((typeof prettyClubName === "function" ? player.full_name : player.full_name) || `#${player.tm_player_id}`);
  const today = new Date().toISOString().slice(0, 10);

  const v = {
    match_date: editing?.match_date || prefill?.match_date || today,
    player_team: editing?.player_team || prefill?.player_team || (player?.current_club_name || ""),
    opponent: editing?.opponent || prefill?.opponent || "",
    competition: editing?.competition || prefill?.competition || "",
    competition_is_other: editing
      ? !window.OBSERVATION_COMPETITIONS.includes(editing.competition)
      : (prefill?.competition && !window.OBSERVATION_COMPETITIONS.includes(prefill.competition)),
    rating: editing?.performance_rating != null ? editing.performance_rating : 6.0,
    minutes_played: editing?.minutes_played != null
      ? editing.minutes_played
      : (prefill?.minutes_played != null ? prefill.minutes_played : null),
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

          <!-- MINUTI GIOCATI (opzionale) -->
          <div style="margin-bottom: 12px;">
            <label class="obs-label">${window.obsT("f_minutes")}</label>
            <input id="obs-minutes" type="number" min="0" max="150" step="1" placeholder="${window.obsT("f_minutes_ph")}" value="${v.minutes_played != null ? v.minutes_played : ""}" class="obs-input-base" style="max-width: 200px;">
          </div>

          <div style="display: grid; grid-template-columns: 1fr; gap: 10px; margin-bottom: 12px;">
            <div>
              <label class="obs-label">${window.obsT("f_match_date")} *</label>
              <input id="obs-match-date" type="date" value="${v.match_date}" class="obs-input-base">
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px;">
            <div>
              <label class="obs-label">${window.obsT("f_player_team")} *</label>
              <input id="obs-player-team" type="text" placeholder="${window.obsT("f_player_team_ph")}" list="obs-player-team-list" class="obs-input-base" autocomplete="off">
              <datalist id="obs-player-team-list">${opponentOptions}</datalist>
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
        <button id="obs-export-pdf-btn" type="button" data-pid="${player.tm_player_id}" data-obs-id="${editing?.id || ''}"
          style="font-size: 13px; padding: 8px 14px; border-radius: 8px; background: rgba(96,165,250,0.10); color: #60A5FA; border: 0.5px solid rgba(96,165,250,0.30); cursor: pointer; font-weight: 500; ${editing?.id ? '' : 'display:none;'}"
          title="${window.obsT("pdf_export_btn")}">📄 PDF</button>
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

  // Fix bug input avversario / player_team non modificabili in edit mode:
  // settiamo il valore via JS DOPO il render invece che inline su `value=""` HTML
  // (il combo `<input value list>` di HTML5 ha glitch noti in edit mode)
  const playerTeamInput = document.getElementById("obs-player-team");
  if (playerTeamInput) {
    // In edit: usa player_team dell'osservazione
    // In nuovo: usa current_club_name del giocatore (default ragionevole)
    const initialPT = (editing && editing.player_team)
      ? editing.player_team
      : (player?.current_club_name || "");
    if (initialPT) playerTeamInput.value = initialPT;
  }
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
  const playerTeam = document.getElementById("obs-player-team").value.trim();
  const opponent = document.getElementById("obs-opponent").value.trim();
  const compSel = document.getElementById("obs-competition").value;
  const compOther = document.getElementById("obs-competition-other").value.trim();
  const competition = (compSel === "Altro") ? compOther : compSel;
  const rating = parseFloat(document.getElementById("obs-rating").value);
  const notes = document.getElementById("obs-notes").value.trim();

  if (!matchDate || !playerTeam || !opponent || !competition) {
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

  // Estrai minutes_played (opzionale, range 0-150)
  const minutesEl = document.getElementById("obs-minutes");
  let minutesPlayed = null;
  if (minutesEl && minutesEl.value !== "") {
    const m = parseInt(minutesEl.value, 10);
    if (!isNaN(m) && m >= 0 && m <= 150) {
      minutesPlayed = m;
    }
  }

  const payload = {
    tm_player_id: player.tm_player_id,
    match_date: matchDate,
    player_team: playerTeam,
    opponent: opponent,
    competition: competition,
    viewing_mode: window._obsCompose.selectedViewingMode,
    performance_rating: rating,
    minutes_played: minutesPlayed,
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
    const GRID = "48px 2fr 60px 180px 80px 80px 2fr 60px 28px";

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
      // Club: logo + nome (riga giocatore, sotto al nome)
      const clubObj = player ? state.clubsById?.get(player.current_club_id) : null;
      const clubLogoSrc = (clubObj && typeof clubLogo === "function") ? clubLogo(clubObj) : "";
      const clubName = player ? ((typeof prettyClubName === "function") ? prettyClubName(player.current_club_name || "") : (player.current_club_name || "")) : "";

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
        const matchInline = o.player_team
          ? `${_obsRenderTeamInline(o.player_team)}<span style="margin: 0 4px; color: var(--text-3); font-size: 10px;">vs</span>${_obsRenderTeamInline(o.opponent)}`
          : `<span style="color: var(--text-3); margin-right: 4px;">vs</span>${_obsRenderTeamInline(o.opponent)}`;
        // Ruoli giocati in questa osservazione
        const rolesArr = Array.isArray(o.roles_played) ? o.roles_played : [];
        // Risolvo sigla → nome esteso (it o en) usando OBSERVATION_ROLE_DEFS
        const roleName = (code) => {
          const def = window.OBSERVATION_ROLE_DEFS?.find(r => r.code === code);
          if (!def) return code.replace("_", " ");
          return isIt ? def.it : def.en;
        };
        const rolesShown = rolesArr.slice(0, 2).map(roleName).join(" · ");
        const rolesExtra = rolesArr.length > 2 ? ` +${rolesArr.length - 2}` : "";
        const rolesObsHtml = rolesArr.length
          ? `<span style="color: var(--text-2); font-size: 11px;" title="${escapeHtml(rolesArr.map(roleName).join(", "))}">${escapeHtml(rolesShown)}${rolesExtra}</span>`
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
              <span style="color: var(--text-3); margin-right: 6px;">${dateFmt}</span>${matchInline}<span style="color: var(--text-3); margin: 0 6px;">·</span><span style="color: var(--text-3); font-size: 11px;">${escapeHtml(o.competition || "")}</span>
            </div>
            <div style="text-align: center; font-size: 11px; color: ${o.minutes_played != null ? "var(--text-1)" : "var(--text-3)"}; font-variant-numeric: tabular-nums;">${o.minutes_played != null ? o.minutes_played + "'" : "—"}</div>
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
              <div style="font-size: 11px; color: var(--text-3); display: flex; align-items: center; gap: 6px; min-width: 0; margin-top: 1px;">
                <span style="flex-shrink: 0;">${escapeHtml(String(birthY || ""))}</span>
                ${clubLogoSrc ? `<span style="color: var(--text-3); opacity: 0.5;">·</span><img src="${clubLogoSrc}" alt="" style="width: 14px; height: 14px; object-fit: contain; flex-shrink: 0;" onerror="this.style.display='none'"/>` : ""}
                <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(clubName)}</span>
              </div>
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


// ============================================================
// EXPORT PDF — singola osservazione + dossier giocatore (v2)
// ============================================================

const PDF_LOGO_URL = "../data/photos/branding/pid_logo_pdf.png";

function _pdfT(key, fallback) {
  // Usa la global "t" del file i18n.js (non window.t — non esiste come window.t)
  if (typeof t === "function") {
    const val = t(key);
    if (val && val !== key) return val;
  }
  return fallback || key;
}

function _pdfPlayerData(player) {
  if (!player) return {};
  const heightCm = player.height_cm || (player.height ? player.height : null);
  const rawRole = player.position_specific || player.position || player.position_general || "—";
  const role = _pdfTranslatePosition(rawRole);
  const dob = player.date_of_birth || "";
  const year = dob ? dob.substring(0, 4) : "—";
  const age = player.age != null ? String(player.age) : "—";
  const club = player.current_club_name || "—";
  const foot = _pdfTranslateFoot(player.foot);
  // Path locali (no CORS) come priorità, poi URL CDN come fallback
  const photoPaths = [];
  // PRIORITÀ: SOTS locale > TM locale > URL CDN (no CORS)
  if (player.sortitoutsi_person_id) photoPaths.push("../data/photos/players_sots_lookup/" + player.sortitoutsi_person_id + ".png");
  if (player.photo_local) photoPaths.push("../data/" + player.photo_local);
  if (player.sortitoutsi_face_url) photoPaths.push(player.sortitoutsi_face_url);
  if (player.photo_url) photoPaths.push(player.photo_url);
  return {
    name: player.full_name || player.name || "—",
    year, age, club, foot,
    height: heightCm ? `${heightCm} cm` : "—",
    role,
    photoPaths,
    clubId: player.current_club_id || null,
  };
}

function _pdfClubLogoPaths(clubId) {
  // Ritorna i path possibili per il logo del club (priorità: locale)
  if (!clubId) return [];
  const clubs = (typeof state !== "undefined" && state.clubs) ? state.clubs : [];
  const club = clubs.find(c => c.tm_club_id === clubId);
  const paths = [];
  if (club) {
    if (club.sortitoutsi_logo_local) paths.push("../data/" + club.sortitoutsi_logo_local);
    if (club.logo_local) paths.push("../data/" + club.logo_local);
    if (club.sortitoutsi_logo_url) paths.push(club.sortitoutsi_logo_url);
    if (club.logo_url) paths.push(club.logo_url);
  }
  // Fallback path standard
  paths.push("../data/photos/clubs_sots/" + clubId + ".png");
  paths.push("../data/photos/clubs_tm/" + clubId + ".png");
  return paths;
}

async function _pdfFetchImage(url) {
  if (!url) return null;
  try {
    const res = await fetch(url, { mode: "cors" });
    if (!res.ok) return null;
    const blob = await res.blob();
    return await new Promise((resolve, reject) => {
      const r = new FileReader();
      r.onloadend = () => resolve(r.result);
      r.onerror = () => reject(r.error);
      r.readAsDataURL(blob);
    });
  } catch (e) {
    return null;
  }
}

async function _pdfFetchFirstAvailable(urls) {
  // Prova gli URL in ordine, ritorna il primo che funziona
  for (const url of urls) {
    if (!url) continue;
    const data = await _pdfFetchImage(url);
    if (data) return data;
  }
  return null;
}

function _pdfFmtDate(s) {
  if (!s) return "—";
  const m = String(s).match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!m) return s;
  return `${m[3]}/${m[2]}/${m[1]}`;
}

function _pdfTagLabel(tag) {
  const map = {
    "PRIMA SCELTA": { label: "Prima scelta", color: [34, 197, 94] },
    "SECONDA SCELTA": { label: "Seconda scelta", color: [251, 191, 36] },
    "DA MONITORARE": { label: "Da monitorare", color: [96, 165, 250] },
    "DA SEGUIRE": { label: "Da seguire", color: [96, 165, 250] },
    "NON IDONEO": { label: "Non idoneo", color: [239, 68, 68] },
    "NON VALUTABILE": { label: "Non valutabile", color: [180, 180, 180] },
    "DA SCARTARE": { label: "Da scartare", color: [239, 68, 68] },
  };
  if (Array.isArray(tag) && tag.length > 0) tag = tag[0];
  if (!tag) return null;
  const t = String(tag).toUpperCase().trim();
  return map[t] || { label: tag, color: [180, 180, 180] };
}

function _pdfRoleExtended(roleCode) {
  // Mappa codice posizione → nome esteso italiano (rispecchia OBSERVATION_ROLES)
  const map = {
    "POR": "Portiere",
    "DCD": "Difensore centrale destro",
    "DC": "Difensore centrale",
    "DCS": "Difensore centrale sinistro",
    "TD": "Terzino destro",
    "TS": "Terzino sinistro",
    "ED": "Esterno destro a tutta fascia",
    "ES": "Esterno sinistro a tutta fascia",
    "MED": "Mediano",
    "REG": "Regista",
    "MEZD": "Mezzala destra",
    "MEZS": "Mezzala sinistra",
    "TQT": "Trequartista",
    "TQTD": "Trequartista destro",
    "TQTS": "Trequartista sinistro",
    "AD": "Ala destra",
    "AS": "Ala sinistra",
    "AT": "Attaccante",
    "ATD": "Seconda punta",
    "PUNTA": "Punta",
  };
  return map[String(roleCode).toUpperCase()] || roleCode;
}

function _pdfDrawMiniField(pdf, x, y, w, h, roles) {
  // Mini-campo da calcio con pallino sulle posizioni giocate.
  // Coordinate logiche del campo (da OBSERVATION_ROLE_DEFS): 0..380 width, 0..560 height
  // Mappiamo a (x, y, w, h) PDF
  const FW = 380, FH = 560;
  const tx = (cx) => x + (cx / FW) * w;
  const ty = (cy) => y + (cy / FH) * h;

  // Sfondo verde campo
  pdf.setFillColor(40, 100, 60);
  pdf.roundedRect(x, y, w, h, 1, 1, "F");

  // Linee bianche del campo
  pdf.setDrawColor(220, 240, 230);
  pdf.setLineWidth(0.2);
  // Bordo
  pdf.roundedRect(x, y, w, h, 1, 1, "S");
  // Linea metà campo
  pdf.line(x, y + h / 2, x + w, y + h / 2);
  // Cerchio centrale
  pdf.circle(x + w / 2, y + h / 2, w * 0.10, "S");
  // Area di rigore alta (in alto = attacco)
  const penW = w * 0.55;
  const penH = h * 0.16;
  pdf.rect(x + (w - penW) / 2, y, penW, penH, "S");
  // Area piccola alta
  const smallW = w * 0.30;
  const smallH = h * 0.08;
  pdf.rect(x + (w - smallW) / 2, y, smallW, smallH, "S");
  // Area di rigore bassa (difesa)
  pdf.rect(x + (w - penW) / 2, y + h - penH, penW, penH, "S");
  // Area piccola bassa
  pdf.rect(x + (w - smallW) / 2, y + h - smallH, smallW, smallH, "S");

  // Mappa codice → coordinate (presa da OBSERVATION_ROLE_DEFS)
  const ROLE_COORDS = {
    "PP": [190, 65], "AS": [115, 145], "TRQ": [190, 165], "AD": [265, 145],
    "AES": [45, 215], "AED": [335, 215],
    "CIS": [130, 280], "CC": [190, 305], "CID": [250, 280],
    "LAT_SN": [60, 365], "LAT_DX": [320, 365],
    "DCS": [140, 420], "DC": [190, 440], "DCD": [240, 420],
    "POR": [190, 500],
  };

  // Disegna pallino su ogni ruolo giocato
  if (Array.isArray(roles)) {
    roles.forEach(r => {
      const code = String(r).toUpperCase();
      const c = ROLE_COORDS[code];
      if (!c) return;
      const px = tx(c[0]);
      const py = ty(c[1]);
      // Cerchio giallo accent
      pdf.setFillColor(250, 204, 21);
      pdf.circle(px, py, 1.6, "F");
      pdf.setDrawColor(40, 80, 40);
      pdf.setLineWidth(0.3);
      pdf.circle(px, py, 1.6, "S");
      // Etichetta codice sotto il cerchio
      pdf.setTextColor(255, 255, 255);
      pdf.setFontSize(5.5);
      pdf.setFont("helvetica", "bold");
      const tw = pdf.getTextWidth(code);
      pdf.text(code, px - tw / 2, py + 3.3);
    });
  }
}



async function _pdfHeader(pdf, title, leftMargin, topY, logoData) {
  // Logo PID immagine (se disponibile) + titolo
  if (logoData) {
    try {
      pdf.addImage(logoData, "PNG", leftMargin, topY - 1, 9, 9);
    } catch (e) {
      try { pdf.addImage(logoData, "JPEG", leftMargin, topY - 1, 9, 9); } catch (e2) {}
    }
  }
  pdf.setTextColor(40, 40, 40);
  pdf.setFontSize(13);
  pdf.setFont("helvetica", "bold");
  pdf.text("PID", leftMargin + 12, topY + 4);
  pdf.setFontSize(7);
  pdf.setFont("helvetica", "normal");
  pdf.setTextColor(140, 140, 140);
  pdf.text("Players Intelligence Database", leftMargin + 12, topY + 7.5);
  // Titolo a destra
  pdf.setFontSize(9);
  pdf.setTextColor(100, 100, 100);
  const titleW = pdf.getTextWidth(title);
  pdf.text(title, 210 - leftMargin - titleW, topY + 5);
  pdf.setDrawColor(200, 200, 200);
  pdf.setLineWidth(0.3);
  pdf.line(leftMargin, topY + 10, 210 - leftMargin, topY + 10);
}

async function _pdfDrawPlayerCard(pdf, player, leftMargin, topY) {
  const data = _pdfPlayerData(player);
  const cardW = 210 - 2 * leftMargin;
  const cardH = 38;
  pdf.setFillColor(248, 248, 248);
  pdf.roundedRect(leftMargin, topY, cardW, cardH, 2, 2, "F");

  // Foto giocatore
  const photoX = leftMargin + 3;
  const photoY = topY + 3;
  const photoSize = 32;
  const photoData = await _pdfFetchFirstAvailable(data.photoPaths);
  if (photoData) {
    try {
      pdf.addImage(photoData, "PNG", photoX, photoY, photoSize, photoSize);
    } catch (e) {
      try { pdf.addImage(photoData, "JPEG", photoX, photoY, photoSize, photoSize); } catch (e2) {
        pdf.setFillColor(220, 220, 220);
        pdf.rect(photoX, photoY, photoSize, photoSize, "F");
      }
    }
  } else {
    pdf.setFillColor(230, 230, 230);
    pdf.rect(photoX, photoY, photoSize, photoSize, "F");
    pdf.setTextColor(140, 140, 140);
    pdf.setFontSize(7);
    pdf.text("no photo", photoX + 8, photoY + 18);
  }

  // Logo club (sopra il nome)
  const txtX = photoX + photoSize + 6;
  let y = topY + 7;
  const clubLogoData = await _pdfFetchFirstAvailable(_pdfClubLogoPaths(data.clubId));

  // Nome giocatore
  pdf.setTextColor(20, 20, 20);
  pdf.setFontSize(13);
  pdf.setFont("helvetica", "bold");
  pdf.text(data.name, txtX, y);
  y += 6;
  // Riga 1: anno · età · [logo club] club
  pdf.setFontSize(9);
  pdf.setFont("helvetica", "normal");
  pdf.setTextColor(80, 80, 80);
  let row1 = `${_pdfT("pdf_field_year", "Anno")}: ${data.year}  ·  ${_pdfT("pdf_field_age", "Età")}: ${data.age}  ·  `;
  pdf.text(row1, txtX, y);
  let row1W = pdf.getTextWidth(row1);
  // Logo club inline
  let clubLabelX = txtX + row1W;
  if (clubLogoData) {
    try { pdf.addImage(clubLogoData, "PNG", clubLabelX, y - 3.5, 4.5, 4.5); clubLabelX += 5.5; }
    catch (e) { try { pdf.addImage(clubLogoData, "JPEG", clubLabelX, y - 3.5, 4.5, 4.5); clubLabelX += 5.5; } catch(e2) {} }
  }
  pdf.text(data.club, clubLabelX, y);
  y += 5;
  // Riga 2: altezza · piede · ruolo
  pdf.text(`${_pdfT("pdf_field_height", "Altezza")}: ${data.height}  ·  ${_pdfT("pdf_field_foot", "Piede")}: ${data.foot}  ·  ${_pdfT("pdf_field_role", "Ruolo")}: ${data.role}`, txtX, y);
  return topY + cardH + 4;
}

async function exportObservationPDF(observationId, playerId) {
  if (!window.jspdf) { alert(_pdfT("pdf_loading_lib", "Caricamento libreria PDF...")); return; }
  const { jsPDF } = window.jspdf;
  const pdf = new jsPDF({ unit: "mm", format: "a4", orientation: "portrait" });
  const leftMargin = 12;

  const player = state.players.find(p => p.tm_player_id === playerId);
  if (!player) { alert("Giocatore non trovato."); return; }
  const allObs = window._obsAllCache || (await window.fetchObservations());
  const obs = (allObs || []).find(o => o.id === observationId);
  if (!obs) { alert("Osservazione non trovata."); return; }

  // Pre-fetch logo PID
  const logoData = await _pdfFetchImage(PDF_LOGO_URL);

  await _pdfHeader(pdf, _pdfT("pdf_observation_section", "Osservazione"), leftMargin, 12, logoData);
  let y = await _pdfDrawPlayerCard(pdf, player, leftMargin, 25);
  y += 4;

  // Sezione osservazione
  pdf.setFillColor(245, 250, 247);
  pdf.roundedRect(leftMargin, y, 210 - 2 * leftMargin, 9, 1.5, 1.5, "F");
  pdf.setTextColor(50, 100, 70);
  pdf.setFontSize(10);
  pdf.setFont("helvetica", "bold");
  const _pdfMatchStr = obs.player_team ? `${obs.player_team} vs ${obs.opponent}` : `vs ${obs.opponent}`;
  pdf.text(`${_pdfT("pdf_observation_section", "Osservazione").toUpperCase()} — ${_pdfFmtDate(obs.match_date)} · ${_pdfMatchStr} · ${obs.competition || ""}`, leftMargin + 3, y + 6);
  y += 13;

  pdf.setTextColor(40, 40, 40);
  pdf.setFontSize(9);
  pdf.setFont("helvetica", "normal");

  const col1X = leftMargin;
  const col2X = leftMargin + 95;
  const lineH = 5.5;
  const drawTwoCol = (l1, v1, l2, v2) => {
    pdf.setFont("helvetica", "bold");
    pdf.setTextColor(100, 100, 100);
    pdf.text(`${l1}:`, col1X, y);
    pdf.setFont("helvetica", "normal");
    pdf.setTextColor(30, 30, 30);
    pdf.text(String(v1 || "—"), col1X + 30, y);
    pdf.setFont("helvetica", "bold");
    pdf.setTextColor(100, 100, 100);
    pdf.text(`${l2}:`, col2X, y);
    pdf.setFont("helvetica", "normal");
    pdf.setTextColor(30, 30, 30);
    pdf.text(String(v2 || "—"), col2X + 28, y);
    y += lineH;
  };

  drawTwoCol(
    _pdfT("pdf_field_mode", "Modalità"), obs.viewing_mode || "—",
    _pdfT("pdf_field_minutes", "Minuti"), obs.minutes_played != null ? `${obs.minutes_played}'` : "—"
  );

  // Posizione: codice + nome esteso (es. "DCS · Difensore centrale sinistro")
  const roles = Array.isArray(obs.roles_played) && obs.roles_played.length ? obs.roles_played : [];
  let posLine;
  if (roles.length === 0) {
    posLine = "—";
  } else if (roles.length === 1) {
    const ext = _pdfRoleExtended(roles[0]);
    posLine = ext === roles[0] ? roles[0] : `${roles[0]} · ${ext}`;
  } else {
    posLine = roles.map(r => {
      const ext = _pdfRoleExtended(r);
      return ext === r ? r : `${r} (${ext})`;
    }).join(", ");
  }
  // Posizione (testo) + mini-campo a destra
  pdf.setFont("helvetica", "bold");
  pdf.setTextColor(100, 100, 100);
  pdf.text(`${_pdfT("pdf_field_position", "Posizione")}:`, col1X, y);
  pdf.setFont("helvetica", "normal");
  pdf.setTextColor(30, 30, 30);
  const posLines = pdf.splitTextToSize(posLine, 110);
  const posStartY = y;
  posLines.forEach((line, idx) => { pdf.text(line, col1X + 30, y); y += lineH; });

  // Mini-campo a destra del testo posizione (60mm wide × 42mm high)
  const fieldX = col2X + 30;
  const fieldY = posStartY - 4;
  const fieldW = 30;
  const fieldH = 42;
  _pdfDrawMiniField(pdf, fieldX, fieldY, fieldW, fieldH, roles);

  // Assicura che y avanzi almeno fino a fine campo
  if (y < fieldY + fieldH + 2) y = fieldY + fieldH + 2;

  // Performance (font grande) + Tag, su riga propria sotto il mini-campo per evitare collisioni
  y += 4;
  const perfStr = obs.performance_rating != null ? String(obs.performance_rating) : "—";
  const tag = _pdfTagLabel(obs.evaluation_tags);
  pdf.setFont("helvetica", "bold");
  pdf.setFontSize(9);
  pdf.setTextColor(100, 100, 100);
  pdf.text(`${_pdfT("pdf_field_performance", "Performance")}:`, col1X, y + 2);
  // Performance numero GRANDE
  pdf.setFontSize(18);
  pdf.setTextColor(20, 130, 90);
  pdf.text(perfStr, col1X + 30, y + 3);
  // Tag a destra del numero performance, ben dimensionato
  if (tag) {
    pdf.setFontSize(10);
    const tagPad = 8;
    const tagW = pdf.getTextWidth(tag.label) + tagPad * 2;
    const tagH = 7;
    const tagX = col1X + 50;
    const tagY = y - 2;
    pdf.setFillColor(tag.color[0], tag.color[1], tag.color[2]);
    pdf.roundedRect(tagX, tagY, tagW, tagH, 1.5, 1.5, "F");
    pdf.setTextColor(255, 255, 255);
    pdf.setFont("helvetica", "bold");
    pdf.text(tag.label, tagX + tagPad, tagY + 5);
  }
  pdf.setFontSize(9);
  y += 9;

  // Strengths
  y += 3;
  if (Array.isArray(obs.strengths) && obs.strengths.length) {
    pdf.setFont("helvetica", "bold");
    pdf.setTextColor(34, 130, 90);
    pdf.text(`${_pdfT("pdf_field_strengths", "Punti di forza")}:`, col1X, y);
    y += lineH;
    pdf.setFont("helvetica", "normal");
    pdf.setTextColor(30, 30, 30);
    const strLines = pdf.splitTextToSize(obs.strengths.join(" · "), 210 - 2 * leftMargin);
    strLines.forEach(line => { pdf.text(line, col1X + 3, y); y += lineH; });
    y += 1;
  }
  // Weaknesses
  if (Array.isArray(obs.weaknesses) && obs.weaknesses.length) {
    pdf.setFont("helvetica", "bold");
    pdf.setTextColor(180, 60, 60);
    pdf.text(`${_pdfT("pdf_field_weaknesses", "Punti deboli")}:`, col1X, y);
    y += lineH;
    pdf.setFont("helvetica", "normal");
    pdf.setTextColor(30, 30, 30);
    const wLines = pdf.splitTextToSize(obs.weaknesses.join(" · "), 210 - 2 * leftMargin);
    wLines.forEach(line => { pdf.text(line, col1X + 3, y); y += lineH; });
    y += 1;
  }

  // Note
  if (obs.notes) {
    y += 2;
    pdf.setFont("helvetica", "bold");
    pdf.setTextColor(80, 80, 80);
    pdf.text(`${_pdfT("pdf_field_notes", "Note")}:`, col1X, y);
    y += lineH;
    pdf.setFont("helvetica", "normal");
    pdf.setTextColor(30, 30, 30);
    pdf.setFillColor(252, 252, 252);
    pdf.setDrawColor(220, 220, 220);
    const noteLines = pdf.splitTextToSize(obs.notes, 210 - 2 * leftMargin - 6);
    const noteH = noteLines.length * lineH + 4;
    pdf.roundedRect(col1X, y - 4, 210 - 2 * leftMargin, noteH, 1, 1, "FD");
    noteLines.forEach(line => { pdf.text(line, col1X + 3, y); y += lineH; });
  }

  // Footer
  const footerY = 287;
  pdf.setDrawColor(220, 220, 220);
  pdf.setLineWidth(0.2);
  pdf.line(leftMargin, footerY, 210 - leftMargin, footerY);
  pdf.setFontSize(8);
  pdf.setTextColor(140, 140, 140);
  const insertedBy = obs.author_username || "—";
  const createdAt = obs.created_at ? _pdfFmtDate(obs.created_at) : "";
  pdf.text(`${_pdfT("pdf_field_scout", "Inserita da")}: ${insertedBy}  ·  ${createdAt}`, leftMargin, footerY + 4);
  const exportTs = new Date().toLocaleDateString();
  const exportTxt = `Export: ${exportTs}`;
  pdf.text(exportTxt, 210 - leftMargin - pdf.getTextWidth(exportTxt), footerY + 4);

  const safeName = String(player.full_name || "obs").replace(/[^a-z0-9_-]/gi, "_");
  pdf.save(`${_pdfT("pdf_filename_obs", "osservazione")}_${safeName}_${obs.match_date}.pdf`);
}

async function exportPlayerDossierPDF(playerId) {
  if (!window.jspdf) { alert(_pdfT("pdf_loading_lib", "")); return; }
  const { jsPDF } = window.jspdf;
  const pdf = new jsPDF({ unit: "mm", format: "a4", orientation: "portrait" });
  const leftMargin = 12;

  const player = state.players.find(p => p.tm_player_id === playerId);
  if (!player) { alert("Giocatore non trovato."); return; }
  const all = window._obsAllCache || (await window.fetchObservations());
  const obsList = (all || []).filter(o => o.tm_player_id === playerId)
    .sort((a, b) => (b.match_date || "").localeCompare(a.match_date || ""));

  if (obsList.length === 0) {
    alert(_pdfT("pdf_no_observations", "Nessuna osservazione per questo giocatore."));
    return;
  }

  const logoData = await _pdfFetchImage(PDF_LOGO_URL);

  await _pdfHeader(pdf, _pdfT("pdf_export_dossier", "Dossier"), leftMargin, 12, logoData);
  let y = await _pdfDrawPlayerCard(pdf, player, leftMargin, 25);
  y += 4;

  // Distribuzione giudizi
  const tagCount = {};
  let totalRated = 0;
  obsList.forEach(o => {
    const t = _pdfTagLabel(o.evaluation_tags);
    if (t) { tagCount[t.label] = (tagCount[t.label] || 0) + 1; totalRated++; }
  });
  if (totalRated > 0) {
    pdf.setFontSize(9);
    pdf.setFont("helvetica", "bold");
    pdf.setTextColor(80, 80, 80);
    pdf.text(`${_pdfT("pdf_field_judgement", "Distribuzione giudizi")}:`, leftMargin, y);
    y += 5;
    // Barra distribuzione (210 - 2*12 = 186 mm di larghezza)
    const barW = 210 - 2 * leftMargin;
    const barH = 6;
    let cursorX = leftMargin;
    const tagOrder = ["Prima scelta", "Seconda scelta", "Da monitorare", "Da seguire", "Non valutabile", "Non idoneo", "Da scartare"];
    const orderedTags = tagOrder.filter(t => tagCount[t]).concat(Object.keys(tagCount).filter(t => !tagOrder.includes(t)));
    for (const tagName of orderedTags) {
      const n = tagCount[tagName];
      const pct = n / totalRated;
      const segW = barW * pct;
      const colorMap = {
        "Prima scelta": [34, 197, 94],
        "Seconda scelta": [251, 191, 36],
        "Da monitorare": [96, 165, 250],
        "Da seguire": [96, 165, 250],
        "Non valutabile": [180, 180, 180],
        "Non idoneo": [239, 68, 68],
        "Da scartare": [239, 68, 68],
      };
      const col = colorMap[tagName] || [150, 150, 150];
      pdf.setFillColor(col[0], col[1], col[2]);
      pdf.rect(cursorX, y, segW, barH, "F");
      cursorX += segW;
    }
    y += barH + 2;
    // Legenda sotto la barra
    pdf.setFontSize(7.5);
    pdf.setFont("helvetica", "normal");
    let legX = leftMargin;
    for (const tagName of orderedTags) {
      const n = tagCount[tagName];
      const pct = Math.round((n / totalRated) * 100);
      const colorMap = {
        "Prima scelta": [34, 197, 94],
        "Seconda scelta": [251, 191, 36],
        "Da monitorare": [96, 165, 250],
        "Da seguire": [96, 165, 250],
        "Non valutabile": [180, 180, 180],
        "Non idoneo": [239, 68, 68],
        "Da scartare": [239, 68, 68],
      };
      const col = colorMap[tagName] || [150, 150, 150];
      pdf.setFillColor(col[0], col[1], col[2]);
      pdf.circle(legX + 1.5, y + 1.5, 1.2, "F");
      pdf.setTextColor(80, 80, 80);
      const txt = `${tagName} ${pct}%`;
      pdf.text(txt, legX + 4, y + 2.5);
      legX += pdf.getTextWidth(txt) + 9;
      if (legX > 210 - leftMargin - 30) { legX = leftMargin; y += 4.5; }
    }
    y += 6;
  }

  // Sezione visionature
  pdf.setFillColor(245, 250, 247);
  pdf.roundedRect(leftMargin, y, 210 - 2 * leftMargin, 9, 1.5, 1.5, "F");
  pdf.setTextColor(50, 100, 70);
  pdf.setFontSize(10);
  pdf.setFont("helvetica", "bold");
  pdf.text(`${_pdfT("pdf_observations_section", "Visionature").toUpperCase()} (${obsList.length})`, leftMargin + 3, y + 6);
  y += 13;

  const tableX = leftMargin;
  const tableW = 210 - 2 * leftMargin;
  const cols = [
    { key: "date", label: _pdfT("pdf_field_date", "Data"), w: 22 },
    { key: "opp",  label: _pdfT("pdf_field_opponent", "Avversario"), w: 36 },
    { key: "comp", label: _pdfT("pdf_field_competition", "Competiz."), w: 30 },
    { key: "pos",  label: _pdfT("pdf_field_position", "Posizione"), w: 38 },
    { key: "mode", label: _pdfT("pdf_field_mode", "Mod"), w: 12 },
    { key: "min",  label: _pdfT("pdf_field_minutes", "Min"), w: 12 },
    { key: "perf", label: _pdfT("pdf_field_performance", "Perf"), w: 14 },
    { key: "tag",  label: "Tag", w: tableW - 22 - 36 - 30 - 38 - 12 - 12 - 14 },
  ];
  const drawTableHeader = (yy) => {
    pdf.setFillColor(40, 50, 45);
    pdf.rect(tableX, yy - 4, tableW, 6, "F");
    pdf.setTextColor(220, 230, 225);
    pdf.setFontSize(8);
    pdf.setFont("helvetica", "bold");
    let cx = tableX + 2;
    cols.forEach(c => { pdf.text(c.label, cx, yy); cx += c.w; });
    return yy + 4;
  };
  y = drawTableHeader(y);

  pdf.setFont("helvetica", "normal");
  pdf.setFontSize(8);
  let totalMin = 0, sumPerf = 0;
  let totRated = 0;
  for (const o of obsList) {
    if (y > 270) { pdf.addPage(); y = 20; y = drawTableHeader(y); }
    pdf.setDrawColor(230, 230, 230);
    pdf.setLineWidth(0.1);
    pdf.line(tableX, y - 1, tableX + tableW, y - 1);
    pdf.setTextColor(40, 40, 40);
    let cx = tableX + 2;
    pdf.text(_pdfFmtDate(o.match_date), cx, y + 3); cx += cols[0].w;
    pdf.text(String(o.opponent || "").substring(0, 20), cx, y + 3); cx += cols[1].w;
    pdf.text(String(o.competition || "").substring(0, 18), cx, y + 3); cx += cols[2].w;
    const pos = Array.isArray(o.roles_played) && o.roles_played.length ? o.roles_played.join(",").substring(0, 22) : "—";
    pdf.text(pos, cx, y + 3); cx += cols[3].w;
    pdf.text(String(o.viewing_mode || "—"), cx, y + 3); cx += cols[4].w;
    if (o.minutes_played != null) totalMin += o.minutes_played;
    pdf.text(o.minutes_played != null ? `${o.minutes_played}'` : "—", cx, y + 3); cx += cols[5].w;
    if (o.performance_rating != null) {
      pdf.setFont("helvetica", "bold");
      pdf.setTextColor(20, 130, 90);
      pdf.text(String(o.performance_rating), cx, y + 3);
      pdf.setFont("helvetica", "normal");
      pdf.setTextColor(40, 40, 40);
      sumPerf += o.performance_rating;
      totRated++;
    } else {
      pdf.text("—", cx, y + 3);
    }
    cx += cols[6].w;
    const tag = _pdfTagLabel(o.evaluation_tags);
    if (tag) {
      pdf.setFillColor(tag.color[0], tag.color[1], tag.color[2]);
      const tw = pdf.getTextWidth(tag.label) + 4;
      pdf.roundedRect(cx, y - 1, Math.min(tw, cols[7].w - 2), 5, 0.8, 0.8, "F");
      pdf.setTextColor(255, 255, 255);
      pdf.setFontSize(7);
      pdf.setFont("helvetica", "bold");
      pdf.text(tag.label, cx + 2, y + 2.5);
      pdf.setFontSize(8);
      pdf.setFont("helvetica", "normal");
      pdf.setTextColor(40, 40, 40);
    }
    y += 7;
  }
  // Riga totali
  if (y > 268) { pdf.addPage(); y = 20; }
  pdf.setDrawColor(160, 160, 160);
  pdf.setLineWidth(0.4);
  pdf.line(tableX, y - 1, tableX + tableW, y - 1);
  pdf.setFillColor(245, 250, 247);
  pdf.rect(tableX, y - 0.5, tableW, 6, "F");
  pdf.setTextColor(40, 80, 60);
  pdf.setFont("helvetica", "bold");
  pdf.setFontSize(8);
  pdf.text(_pdfT("pdf_field_total", "TOTALE"), tableX + 2, y + 3);
  pdf.text(`${obsList.length} ${obsList.length === 1 ? "partita" : "partite"}`, tableX + 22 + 2, y + 3);
  pdf.text(`${totalMin}'`, tableX + 22 + 36 + 30 + 38 + 12 + 2, y + 3);
  if (totRated > 0) {
    const avg = (sumPerf / totRated).toFixed(2);
    pdf.text(avg, tableX + 22 + 36 + 30 + 38 + 12 + 12 + 2, y + 3);
  }
  y += 9;

  const footerY = 287;
  pdf.setDrawColor(220, 220, 220);
  pdf.setLineWidth(0.2);
  pdf.line(leftMargin, footerY, 210 - leftMargin, footerY);
  pdf.setFontSize(8);
  pdf.setTextColor(140, 140, 140);
  const exportTs = new Date().toLocaleDateString();
  pdf.text(`PID Dossier · ${exportTs}`, leftMargin, footerY + 4);
  pdf.text(`${obsList.length} osservazion${obsList.length === 1 ? "e" : "i"}`, 210 - leftMargin - 30, footerY + 4);

  const safeName = String(player.full_name || "dossier").replace(/[^a-z0-9_-]/gi, "_");
  pdf.save(`${_pdfT("pdf_filename_dossier", "dossier")}_${safeName}.pdf`);
}

document.addEventListener("click", (e) => {
  const btn = e.target.closest("#obs-export-pdf-btn");
  if (!btn) return;
  e.preventDefault();
  e.stopPropagation();
  const obsId = btn.dataset.obsId;
  const pid = parseInt(btn.dataset.pid);
  if (!obsId || !pid) return;
  exportObservationPDF(obsId, pid).catch(err => {
    console.warn("[pdf] export obs failed", err);
    alert("Errore esportazione PDF: " + err.message);
  });
});

document.addEventListener("click", (e) => {
  const btn = e.target.closest(".scouting-export-pdf-btn");
  if (!btn) return;
  e.preventDefault();
  e.stopPropagation();
  const pid = parseInt(btn.dataset.pid);
  if (!pid) return;
  exportPlayerDossierPDF(pid).catch(err => {
    console.warn("[pdf] export dossier failed", err);
    alert("Errore esportazione dossier: " + err.message);
  });
});

window.exportObservationPDF = exportObservationPDF;
window.exportPlayerDossierPDF = exportPlayerDossierPDF;

(function _setupScoutingPdfBtns() {
  if (typeof MutationObserver === "undefined") return;
  const observe = () => {
    const root = document.getElementById("observations-scouting-content") || document.getElementById("scouting-content") || document.body;
    if (!root) return;
    const mo = new MutationObserver(() => {
      root.querySelectorAll(".scouting-player-row").forEach(row => {
        if (row.dataset.pdfBtnInjected === "1") return;
        const pid = row.dataset.pid;
        if (!pid) return;
        const btn = document.createElement("button");
        btn.className = "scouting-export-pdf-btn";
        btn.dataset.pid = pid;
        btn.title = (typeof window.t === "function" && window.t("pdf_export_dossier")) || "Dossier PDF";
        btn.textContent = "📄";
        btn.style.cssText = "position: absolute; right: 38px; top: 50%; transform: translateY(-50%); width: 24px; height: 24px; border-radius: 6px; background: rgba(96,165,250,0.10); color: #60A5FA; border: 0.5px solid rgba(96,165,250,0.30); cursor: pointer; font-size: 12px; line-height: 1; padding: 0; z-index: 2;";
        if (getComputedStyle(row).position === "static") row.style.position = "relative";
        row.appendChild(btn);
        row.dataset.pdfBtnInjected = "1";
      });
    });
    mo.observe(root, { childList: true, subtree: true });
  };
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", observe);
  } else {
    observe();
  }
})();

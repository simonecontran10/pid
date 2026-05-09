/**
 * observations_ui.js — Fase 3: UI sezione Osservazioni
 *
 * Da appendere in fondo a frontend/app.js (oppure caricato come <script> separato
 * dopo app.js — purché cloud_sync.js sia già caricato).
 *
 * Espone:
 *   - renderObservationsSection(pid)  → ritorna HTML stringa, da inserire nel modal giocatore
 *   - openObservationCompose(pid, obsId?) → apre modal di creazione/modifica
 *   - wireObservationsHandlers(pid)   → aggancia event listener (chiama dopo l'inserimento HTML)
 *
 * Dipende da:
 *   - window.fetchObservations / saveObservation / updateObservation / deleteObservation
 *   - window.OBSERVATION_ROLES
 *   - window.cloudAuth.user
 *   - currentLang (variabile globale di app.js per IT/EN)
 *   - state.players, state.clubsById (per autocomplete avversario)
 */

// ============================================================
//  COSTANTI: liste valori (canoniche in italiano)
// ============================================================

// 37 caratteristiche tecnico/tattiche, ordine alfabetico, condivise tra forze e debolezze
window.OBSERVATION_TRAITS = [
  "1vs1 difensivo", "Aggressività", "Agonismo", "Ampiezza", "Area di rigore offensiva",
  "Assist", "Conduzione palla", "Cross", "Dinamismo", "Dribbling 1c1",
  "Duelli difensivi", "Fase difensiva", "Fase offensiva", "Finalizzazione", "Forza fisica",
  "Gioco aereo", "Gioco per la squadra", "Inizio manovra", "Inserimenti senza palla",
  "Intelligenza tattica", "Intensità", "Jolly", "Letture tattiche", "Passaggi Chiave",
  "Personalità", "Profondità", "Progressione", "Rapidità primi metri", "Recupero palloni",
  "Rifinitura", "Spazi stretti", "Tecnica", "Tiro/Calcio", "Transizioni difensive",
  "Transizioni offensive", "Uscite", "Velocità", "Visione di gioco",
];

// Etichette di valutazione globale (con colore associato)
window.OBSERVATION_TAGS = [
  { value: "PRIMA SCELTA",    color: "#22C55E" }, // verde
  { value: "SECONDA SCELTA",  color: "#EAB308" }, // giallo
  { value: "DA MONITORARE",   color: "#F97316" }, // arancione
  { value: "NON IDONEO",      color: "#EF4444" }, // rosso
];

// Competizioni preset (più "Altro" libero)
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

// Sigle ruolo con label IT/EN e coordinate sul campo (svg viewBox 0 0 380 540)
window.OBSERVATION_ROLE_DEFS = [
  // Attacco
  { code: "PP",     it: "Punta",                      en: "Striker",                cx: 190, cy: 65  },
  // Trequarti
  { code: "AS",     it: "Ala sinistra",               en: "Left winger",            cx: 115, cy: 145 },
  { code: "TRQ",    it: "Trequartista",               en: "Attacking midfielder",   cx: 190, cy: 165 },
  { code: "AD",     it: "Ala destra",                 en: "Right winger",           cx: 265, cy: 145 },
  // Centrocampo larghi
  { code: "AES",    it: "Quinto sinistro",            en: "Left wing-back",         cx: 45,  cy: 215 },
  { code: "AED",    it: "Quinto destro",              en: "Right wing-back",        cx: 335, cy: 215 },
  // Centrocampo
  { code: "CIS",    it: "Centrocampista interno sx",  en: "Left central midfielder",cx: 130, cy: 280 },
  { code: "CC",     it: "Centrocampista centrale",    en: "Central midfielder",     cx: 190, cy: 305 },
  { code: "CID",    it: "Centrocampista interno dx",  en: "Right central midfielder",cx: 250, cy: 280 },
  // Difesa esterni
  { code: "LAT_SN", it: "Terzino sinistro",           en: "Left-back",              cx: 60,  cy: 365 },
  { code: "LAT_DX", it: "Terzino destro",             en: "Right-back",             cx: 320, cy: 365 },
  // Difesa centrale
  { code: "DCS",    it: "Difensore centrale sx",      en: "Left centre-back",       cx: 140, cy: 420 },
  { code: "DC",     it: "Difensore centrale",         en: "Centre-back",            cx: 190, cy: 440 },
  { code: "DCD",    it: "Difensore centrale dx",      en: "Right centre-back",      cx: 240, cy: 420 },
  // Porta
  { code: "POR",    it: "Portiere",                   en: "Goalkeeper",             cx: 190, cy: 500 },
];

// ============================================================
//  Mapping traduzione IT → EN per traits, tags, competitions
//  (le voci sono salvate in italiano nel DB, qui solo per visualizzazione EN)
// ============================================================
window.OBSERVATION_I18N_EN = {
  // Traits (37)
  "1vs1 difensivo": "Defensive 1vs1",
  "Aggressività": "Aggressiveness",
  "Agonismo": "Combativeness",
  "Ampiezza": "Width",
  "Area di rigore offensiva": "Box presence",
  "Assist": "Assists",
  "Conduzione palla": "Ball carrying",
  "Cross": "Crossing",
  "Dinamismo": "Dynamism",
  "Dribbling 1c1": "Dribbling 1v1",
  "Duelli difensivi": "Defensive duels",
  "Fase difensiva": "Defensive phase",
  "Fase offensiva": "Offensive phase",
  "Finalizzazione": "Finishing",
  "Forza fisica": "Physical strength",
  "Gioco aereo": "Aerial play",
  "Gioco per la squadra": "Team play",
  "Inizio manovra": "Build-up play",
  "Inserimenti senza palla": "Off-ball runs",
  "Intelligenza tattica": "Tactical intelligence",
  "Intensità": "Intensity",
  "Jolly": "Versatility",
  "Letture tattiche": "Tactical reading",
  "Passaggi Chiave": "Key passes",
  "Personalità": "Personality",
  "Profondità": "Depth runs",
  "Progressione": "Progression",
  "Rapidità primi metri": "Acceleration",
  "Recupero palloni": "Ball recovery",
  "Rifinitura": "Final pass",
  "Spazi stretti": "Tight spaces",
  "Tecnica": "Technique",
  "Tiro/Calcio": "Shooting",
  "Transizioni difensive": "Defensive transitions",
  "Transizioni offensive": "Offensive transitions",
  "Uscite": "Goalkeeper exits",
  "Velocità": "Speed",
  "Visione di gioco": "Game vision",
  // Tags
  "PRIMA SCELTA":   "FIRST CHOICE",
  "SECONDA SCELTA": "SECOND CHOICE",
  "DA MONITORARE":  "MONITOR",
  "NON IDONEO":     "REJECT",
};

// Helper: traduzione IT → lingua corrente
window.obsLocalize = function(itValue) {
  if (!itValue) return "";
  if (typeof currentLang === "undefined" || currentLang === "it") return itValue;
  return window.OBSERVATION_I18N_EN[itValue] || itValue;
};

// Helper: lingua corrente per stringhe del modulo Osservazioni
window.obsT = function(key) {
  const dict = {
    it: {
      section_title: "Osservazioni",
      no_obs: "Nessuna osservazione per questo giocatore.",
      new_obs: "+ Nuova osservazione",
      edit_obs: "Modifica osservazione",
      new_obs_title: "Nuova osservazione",
      delete_confirm: "Eliminare questa osservazione? L'azione è irreversibile.",
      // Form labels
      f_match_date: "Data partita",
      f_opponent: "Avversario",
      f_opponent_ph: "Es. Inter Milan",
      f_competition: "Competizione",
      f_competition_other: "Specifica competizione",
      f_roles: "Ruoli giocati",
      f_roles_hint: "Clicca sui cerchi del campo per selezionare uno o più ruoli",
      f_rating: "Performance rating",
      f_tag: "Valutazione",
      f_strengths: "Punti di forza",
      f_weaknesses: "Punti di debolezza",
      f_notes: "Note",
      f_notes_ph: "Osservazioni libere sulla prestazione…",
      btn_save: "Salva",
      btn_cancel: "Annulla",
      btn_delete: "Elimina",
      err_required: "Compila tutti i campi obbligatori",
      err_no_role: "Seleziona almeno un ruolo",
      err_duplicate: "Esiste già un'osservazione per questo giocatore in questa partita",
      ok_saved: "Osservazione salvata",
      ok_updated: "Osservazione aggiornata",
      ok_deleted: "Osservazione eliminata",
      author: "Autore",
      created: "Inserita il",
    },
    en: {
      section_title: "Observations",
      no_obs: "No observations for this player yet.",
      new_obs: "+ New observation",
      edit_obs: "Edit observation",
      new_obs_title: "New observation",
      delete_confirm: "Delete this observation? This action is irreversible.",
      f_match_date: "Match date",
      f_opponent: "Opponent",
      f_opponent_ph: "e.g. Inter Milan",
      f_competition: "Competition",
      f_competition_other: "Specify competition",
      f_roles: "Roles played",
      f_roles_hint: "Click circles on the pitch to select one or more roles",
      f_rating: "Performance rating",
      f_tag: "Verdict",
      f_strengths: "Strengths",
      f_weaknesses: "Weaknesses",
      f_notes: "Notes",
      f_notes_ph: "Free observations on the performance…",
      btn_save: "Save",
      btn_cancel: "Cancel",
      btn_delete: "Delete",
      err_required: "Fill in all required fields",
      err_no_role: "Select at least one role",
      err_duplicate: "An observation already exists for this player in this match",
      ok_saved: "Observation saved",
      ok_updated: "Observation updated",
      ok_deleted: "Observation deleted",
      author: "Author",
      created: "Created on",
    },
  };
  const lang = (typeof currentLang !== "undefined") ? currentLang : "it";
  return (dict[lang] && dict[lang][key]) || (dict.it[key]) || key;
};

// ============================================================
//  RENDER: sezione "Osservazioni" in fondo al modal giocatore
// ============================================================

// Cache locale delle osservazioni (per giocatore corrente, evita refetch su re-render rapidi)
window._obsCache = window._obsCache || {};

/**
 * HTML della sezione Osservazioni (placeholder con loader; popolato async).
 * Inserita in fondo al modal in app.js (vedi patch).
 */
window.renderObservationsSection = function(pid) {
  return `
    <div id="obs-section-${pid}" style="margin-top: 24px; padding-top: 16px; border-top: 0.5px solid var(--border);">
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <div style="width: 3px; height: 14px; background: var(--accent); border-radius: 2px;"></div>
          <span style="font-size: 13px; font-weight: 500; color: var(--text-1); text-transform: uppercase; letter-spacing: 0.06em;">${window.obsT("section_title")}</span>
        </div>
        <button id="obs-new-btn-${pid}" type="button"
          style="font-size: 12px; padding: 6px 12px; border-radius: 8px; background: var(--accent-bg); color: var(--accent); border: 0.5px solid var(--accent); cursor: pointer; font-weight: 500;">
          ${window.obsT("new_obs")}
        </button>
      </div>
      <div id="obs-list-${pid}" style="display: flex; flex-direction: column; gap: 8px;">
        <div style="font-size: 12px; color: var(--text-3); padding: 8px;">…</div>
      </div>
    </div>
  `;
};

/**
 * Renderizza una singola card osservazione.
 */
function _obsCardHtml(obs) {
  const tagDef = window.OBSERVATION_TAGS.find(t => t.value === obs.evaluation_tags?.[0]);
  const tagLabel = tagDef ? window.obsLocalize(tagDef.value) : null;
  const tagColor = tagDef ? tagDef.color : null;

  const rolesLabels = (obs.roles_played || []).map(code => {
    const def = window.OBSERVATION_ROLE_DEFS.find(r => r.code === code);
    return def ? def.code : code;
  }).join(" · ");

  const rating = obs.performance_rating != null
    ? `<span style="font-size: 18px; font-weight: 600; color: var(--accent);">${obs.performance_rating.toFixed(1)}</span>`
    : "";

  const dateLocale = (typeof currentLang !== "undefined" && currentLang === "it") ? "it-IT" : "en-GB";
  const dateFmt = new Date(obs.match_date).toLocaleDateString(dateLocale, { day: "2-digit", month: "short", year: "numeric" });

  const strengthsHtml = (obs.strengths || []).map(s =>
    `<span style="font-size: 10px; padding: 2px 6px; border-radius: 4px; background: rgba(34,197,94,0.15); color: #22C55E;">${escapeHtml(window.obsLocalize(s))}</span>`
  ).join(" ");
  const weaknessesHtml = (obs.weaknesses || []).map(s =>
    `<span style="font-size: 10px; padding: 2px 6px; border-radius: 4px; background: rgba(239,68,68,0.15); color: #EF4444;">${escapeHtml(window.obsLocalize(s))}</span>`
  ).join(" ");

  return `
    <div class="obs-card" data-obs-id="${obs.id}"
      style="padding: 12px; border-radius: 10px; background: rgba(255,255,255,0.03); border: 0.5px solid var(--border); cursor: pointer;">
      <div style="display: flex; align-items: flex-start; gap: 12px; margin-bottom: 6px;">
        <div style="flex: 1; min-width: 0;">
          <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 4px;">
            <span style="font-size: 13px; font-weight: 500; color: var(--text-1);">${escapeHtml(obs.opponent)}</span>
            <span style="font-size: 11px; color: var(--text-3);">·</span>
            <span style="font-size: 12px; color: var(--text-2);">${escapeHtml(obs.competition)}</span>
            <span style="font-size: 11px; color: var(--text-3);">·</span>
            <span style="font-size: 12px; color: var(--text-3);">${dateFmt}</span>
            ${tagLabel ? `<span style="font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 999px; background: ${tagColor}22; color: ${tagColor}; border: 0.5px solid ${tagColor};">${tagLabel}</span>` : ""}
          </div>
          ${rolesLabels ? `<div style="font-size: 11px; color: var(--text-3); margin-bottom: 6px;">${escapeHtml(rolesLabels)}</div>` : ""}
        </div>
        ${rating}
      </div>
      ${(strengthsHtml || weaknessesHtml) ? `<div style="display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px;">${strengthsHtml}${strengthsHtml && weaknessesHtml ? " " : ""}${weaknessesHtml}</div>` : ""}
      ${obs.notes ? `<div style="font-size: 12px; color: var(--text-2); margin-top: 8px; line-height: 1.5; white-space: pre-wrap;">${escapeHtml(obs.notes)}</div>` : ""}
      <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 8px; font-size: 10px; color: var(--text-3);">
        <span>${escapeHtml(obs.author_username || "")}</span>
        <div style="display: flex; gap: 6px;">
          <button type="button" class="obs-edit-btn" data-obs-id="${obs.id}"
            style="font-size: 11px; padding: 3px 8px; border-radius: 6px; background: transparent; color: var(--text-2); border: 0.5px solid var(--border); cursor: pointer;">✎</button>
          <button type="button" class="obs-delete-btn" data-obs-id="${obs.id}"
            style="font-size: 11px; padding: 3px 8px; border-radius: 6px; background: transparent; color: #EF4444; border: 0.5px solid rgba(239,68,68,0.4); cursor: pointer;">🗑</button>
        </div>
      </div>
    </div>
  `;
}

/**
 * Carica + renderizza la lista per il giocatore. Chiamata async dopo il render del modal.
 */
window.renderObservationsList = async function(pid) {
  const listEl = document.getElementById(`obs-list-${pid}`);
  if (!listEl) return;
  try {
    const obsList = await window.fetchObservations({ tm_player_id: pid });
    window._obsCache[pid] = obsList;
    if (!obsList.length) {
      listEl.innerHTML = `<div style="font-size: 12px; color: var(--text-3); padding: 8px;">${window.obsT("no_obs")}</div>`;
      return;
    }
    listEl.innerHTML = obsList.map(_obsCardHtml).join("");

    // Wire bottoni edit/delete
    listEl.querySelectorAll(".obs-edit-btn").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        window.openObservationCompose(pid, btn.dataset.obsId);
      });
    });
    listEl.querySelectorAll(".obs-delete-btn").forEach(btn => {
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        if (!confirm(window.obsT("delete_confirm"))) return;
        const r = await window.deleteObservation(btn.dataset.obsId);
        if (r.ok) {
          window.renderObservationsList(pid); // re-render lista
        } else {
          alert(r.error || "Errore eliminazione");
        }
      });
    });
  } catch (e) {
    console.warn("[obs-ui] renderObservationsList error:", e);
    listEl.innerHTML = `<div style="font-size: 12px; color: #EF4444; padding: 8px;">Errore caricamento osservazioni</div>`;
  }
};

/**
 * Aggancia il bottone "+ Nuova osservazione" del modal giocatore.
 */
window.wireObservationsHandlers = function(pid) {
  const newBtn = document.getElementById(`obs-new-btn-${pid}`);
  if (newBtn) newBtn.addEventListener("click", () => window.openObservationCompose(pid));
  // Carica + render lista in background
  window.renderObservationsList(pid);
};

// ============================================================
//  MODAL "Nuova / Modifica Osservazione"
// ============================================================

// Stato interno del compose
window._obsCompose = { pid: null, editId: null, selectedRoles: [], selectedTag: null, selectedStrengths: [], selectedWeaknesses: [] };

/**
 * Apre il modal di creazione (obsId omesso) o modifica (obsId presente).
 */
window.openObservationCompose = async function(pid, obsId = null) {
  const player = state.players.find(p => p.tm_player_id === pid);
  if (!player) return;

  // Se editing, recupera l'osservazione dalla cache (già caricata da renderObservationsList)
  let editing = null;
  if (obsId) {
    const list = window._obsCache[pid] || await window.fetchObservations({ tm_player_id: pid });
    editing = list.find(o => o.id === obsId);
    if (!editing) {
      alert("Osservazione non trovata");
      return;
    }
  }

  // Inizializza stato
  window._obsCompose = {
    pid: pid,
    editId: obsId,
    selectedRoles: editing ? [...(editing.roles_played || [])] : [],
    selectedTag: editing ? (editing.evaluation_tags?.[0] || null) : null,
    selectedStrengths: editing ? [...(editing.strengths || [])] : [],
    selectedWeaknesses: editing ? [...(editing.weaknesses || [])] : [],
  };

  // Render modal
  const overlay = document.getElementById("obs-compose-overlay");
  if (overlay) overlay.remove(); // safety: rimuovi precedenti

  const html = _obsComposeHtml(player, editing);
  document.body.insertAdjacentHTML("beforeend", html);

  // Wire eventi
  setTimeout(() => _wireObsCompose(player, editing), 0);
};

function _obsComposeHtml(player, editing) {
  const isEdit = !!editing;
  const title = isEdit ? window.obsT("edit_obs") : window.obsT("new_obs_title");
  const pName = escapeHtml(player.full_name || `#${player.tm_player_id}`);
  const today = new Date().toISOString().slice(0, 10);

  // Pre-popolazione (solo edit)
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

  // Campo grafico SVG (15 cerchi)
  const fieldSvg = _renderRoleFieldSvg(window._obsCompose.selectedRoles);

  // Multi-select chips per traits, evaluation_tags
  const traitChips = (selected) => window.OBSERVATION_TRAITS.map(t => {
    const isOn = selected.includes(t);
    return `<button type="button" class="obs-chip" data-trait="${escapeHtml(t)}"
      style="font-size: 11px; padding: 4px 9px; border-radius: 999px; cursor: pointer; border: 0.5px solid ${isOn ? "var(--accent)" : "var(--border)"}; background: ${isOn ? "var(--accent-bg)" : "transparent"}; color: ${isOn ? "var(--accent)" : "var(--text-2)"};">${escapeHtml(window.obsLocalize(t))}</button>`;
  }).join(" ");

  const tagChips = window.OBSERVATION_TAGS.map(tg => {
    const isOn = window._obsCompose.selectedTag === tg.value;
    return `<button type="button" class="obs-tag-chip" data-tag="${escapeHtml(tg.value)}"
      style="font-size: 11px; font-weight: 600; padding: 5px 12px; border-radius: 999px; cursor: pointer; border: 0.5px solid ${tg.color}; background: ${isOn ? tg.color : "transparent"}; color: ${isOn ? "#fff" : tg.color};">${escapeHtml(window.obsLocalize(tg.value))}</button>`;
  }).join(" ");

  return `
  <div id="obs-compose-overlay"
    style="position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 100; display: flex; align-items: flex-start; justify-content: center; overflow-y: auto; padding: 20px;">
    <div style="background: var(--bg-1); color: var(--text-1); width: 100%; max-width: 720px; border-radius: 16px; padding: 22px; border: 0.5px solid var(--border); margin: 20px 0;">

      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
        <div>
          <div style="font-size: 11px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.1em;">${pName}</div>
          <div style="font-size: 18px; font-weight: 600; margin-top: 2px;">${title}</div>
        </div>
        <button type="button" id="obs-cancel-btn" style="font-size: 22px; background: transparent; border: none; color: var(--text-3); cursor: pointer;">✕</button>
      </div>

      <!-- DATA + AVVERSARIO + COMPETIZIONE -->
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 14px;">
        <div>
          <label style="font-size: 11px; color: var(--text-3); display: block; margin-bottom: 4px;">${window.obsT("f_match_date")} *</label>
          <input id="obs-match-date" type="date" value="${v.match_date}" style="width: 100%; padding: 8px 10px; border-radius: 8px; background: rgba(255,255,255,0.05); color: var(--text-1); border: 0.5px solid var(--border); font-size: 13px;">
        </div>
        <div>
          <label style="font-size: 11px; color: var(--text-3); display: block; margin-bottom: 4px;">${window.obsT("f_opponent")} *</label>
          <input id="obs-opponent" type="text" value="${escapeHtml(v.opponent)}" placeholder="${window.obsT("f_opponent_ph")}" list="obs-opponent-list" style="width: 100%; padding: 8px 10px; border-radius: 8px; background: rgba(255,255,255,0.05); color: var(--text-1); border: 0.5px solid var(--border); font-size: 13px;">
          <datalist id="obs-opponent-list">${(state.clubs || []).map(c => `<option value="${escapeHtml(c.club_name || c.name || "")}">`).join("")}</datalist>
        </div>
      </div>

      <div style="margin-bottom: 14px;">
        <label style="font-size: 11px; color: var(--text-3); display: block; margin-bottom: 4px;">${window.obsT("f_competition")} *</label>
        <select id="obs-competition" style="width: 100%; padding: 8px 10px; border-radius: 8px; background: rgba(255,255,255,0.05); color: var(--text-1); border: 0.5px solid var(--border); font-size: 13px;">
          <option value="">—</option>
          ${competitionOptions}
        </select>
        <input id="obs-competition-other" type="text" placeholder="${window.obsT("f_competition_other")}"
          value="${v.competition_is_other ? escapeHtml(v.competition) : ""}"
          style="display: ${v.competition_is_other ? "block" : "none"}; width: 100%; margin-top: 8px; padding: 8px 10px; border-radius: 8px; background: rgba(255,255,255,0.05); color: var(--text-1); border: 0.5px solid var(--border); font-size: 13px;">
      </div>

      <!-- CAMPO GRAFICO RUOLI -->
      <div style="margin-bottom: 14px;">
        <label style="font-size: 11px; color: var(--text-3); display: block; margin-bottom: 4px;">${window.obsT("f_roles")} *</label>
        <div style="font-size: 10px; color: var(--text-3); margin-bottom: 8px;">${window.obsT("f_roles_hint")}</div>
        <div id="obs-field-wrap" style="display: flex; justify-content: center; padding: 12px; background: rgba(255,255,255,0.02); border-radius: 12px; border: 0.5px solid var(--border);">
          ${fieldSvg}
        </div>
      </div>

      <!-- RATING SLIDER -->
      <div style="margin-bottom: 14px;">
        <label style="font-size: 11px; color: var(--text-3); display: block; margin-bottom: 4px;">${window.obsT("f_rating")}</label>
        <div style="display: flex; align-items: center; gap: 14px;">
          <input id="obs-rating" type="range" min="0" max="10" step="0.5" value="${v.rating}"
            style="flex: 1; accent-color: var(--accent);">
          <div id="obs-rating-display" style="font-size: 22px; font-weight: 700; color: var(--accent); width: 56px; text-align: center;">${v.rating.toFixed(1)}</div>
        </div>
      </div>

      <!-- TAG VALUTAZIONE -->
      <div style="margin-bottom: 14px;">
        <label style="font-size: 11px; color: var(--text-3); display: block; margin-bottom: 6px;">${window.obsT("f_tag")}</label>
        <div id="obs-tag-chips" style="display: flex; flex-wrap: wrap; gap: 6px;">${tagChips}</div>
      </div>

      <!-- STRENGTHS -->
      <div style="margin-bottom: 14px;">
        <label style="font-size: 11px; color: var(--text-3); display: block; margin-bottom: 6px;">${window.obsT("f_strengths")}</label>
        <div id="obs-strengths-chips" style="display: flex; flex-wrap: wrap; gap: 4px;">${traitChips(window._obsCompose.selectedStrengths)}</div>
      </div>

      <!-- WEAKNESSES -->
      <div style="margin-bottom: 14px;">
        <label style="font-size: 11px; color: var(--text-3); display: block; margin-bottom: 6px;">${window.obsT("f_weaknesses")}</label>
        <div id="obs-weaknesses-chips" style="display: flex; flex-wrap: wrap; gap: 4px;">${traitChips(window._obsCompose.selectedWeaknesses)}</div>
      </div>

      <!-- NOTES -->
      <div style="margin-bottom: 16px;">
        <label style="font-size: 11px; color: var(--text-3); display: block; margin-bottom: 4px;">${window.obsT("f_notes")}</label>
        <textarea id="obs-notes" rows="4" placeholder="${window.obsT("f_notes_ph")}"
          style="width: 100%; padding: 10px; border-radius: 8px; background: rgba(255,255,255,0.05); color: var(--text-1); border: 0.5px solid var(--border); font-size: 13px; resize: vertical; font-family: inherit;">${escapeHtml(v.notes)}</textarea>
      </div>

      <!-- ERROR -->
      <div id="obs-error" style="display: none; padding: 8px 12px; margin-bottom: 12px; border-radius: 8px; background: rgba(239,68,68,0.15); color: #EF4444; font-size: 12px; border: 0.5px solid rgba(239,68,68,0.4);"></div>

      <!-- BUTTONS -->
      <div style="display: flex; gap: 8px; justify-content: flex-end;">
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
 * Renderizza l'SVG del campo con i 15 cerchi cliccabili.
 */
function _renderRoleFieldSvg(selectedRoles) {
  const W = 380, H = 540;
  const lines = `
    <!-- Sfondo campo -->
    <rect width="${W}" height="${H}" fill="#1B7A3E" rx="4"/>
    <!-- Linee bianche -->
    <rect x="20" y="20" width="${W-40}" height="${H-40}" fill="none" stroke="#fff" stroke-width="1.5" opacity="0.55"/>
    <line x1="20" y1="${H/2}" x2="${W-20}" y2="${H/2}" stroke="#fff" stroke-width="1.5" opacity="0.55"/>
    <circle cx="${W/2}" cy="${H/2}" r="50" fill="none" stroke="#fff" stroke-width="1.5" opacity="0.55"/>
    <circle cx="${W/2}" cy="${H/2}" r="2" fill="#fff" opacity="0.55"/>
    <!-- Aree -->
    <rect x="${W/2-80}" y="20" width="160" height="65" fill="none" stroke="#fff" stroke-width="1.5" opacity="0.55"/>
    <rect x="${W/2-40}" y="20" width="80" height="25" fill="none" stroke="#fff" stroke-width="1.5" opacity="0.55"/>
    <rect x="${W/2-80}" y="${H-85}" width="160" height="65" fill="none" stroke="#fff" stroke-width="1.5" opacity="0.55"/>
    <rect x="${W/2-40}" y="${H-45}" width="80" height="25" fill="none" stroke="#fff" stroke-width="1.5" opacity="0.55"/>
  `;

  const circles = window.OBSERVATION_ROLE_DEFS.map(r => {
    const isOn = selectedRoles.includes(r.code);
    const fillColor = isOn ? "#FBBF24" : "rgba(255,255,255,0.85)";
    const textColor = isOn ? "#000" : "#1B7A3E";
    const strokeColor = isOn ? "#000" : "rgba(0,0,0,0.3)";
    return `
      <g class="obs-role-circle" data-role="${r.code}" style="cursor: pointer;" tabindex="0">
        <circle cx="${r.cx}" cy="${r.cy}" r="22" fill="${fillColor}" stroke="${strokeColor}" stroke-width="1.5"/>
        <text x="${r.cx}" y="${r.cy + 4}" text-anchor="middle" font-size="10" font-weight="700" fill="${textColor}" pointer-events="none">${r.code.replace("_", " ")}</text>
      </g>
    `;
  }).join("");

  return `<svg viewBox="0 0 ${W} ${H}" width="320" height="455" xmlns="http://www.w3.org/2000/svg">${lines}${circles}</svg>`;
}

/**
 * Aggiorna l'SVG del campo dopo un click su un cerchio (re-render parziale).
 */
function _redrawField() {
  const wrap = document.getElementById("obs-field-wrap");
  if (wrap) wrap.innerHTML = _renderRoleFieldSvg(window._obsCompose.selectedRoles);
  _wireFieldClicks();
}

/**
 * Aggancia event listener ai cerchi del campo (chiamato dopo ogni redraw).
 */
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

/**
 * Aggancia tutti gli eventi del modal compose.
 */
function _wireObsCompose(player, editing) {
  // Cancel
  document.getElementById("obs-cancel-btn")?.addEventListener("click", _closeObsCompose);
  document.getElementById("obs-cancel-btn-2")?.addEventListener("click", _closeObsCompose);
  // Click su overlay (fuori dalla card) chiude
  document.getElementById("obs-compose-overlay")?.addEventListener("click", (e) => {
    if (e.target.id === "obs-compose-overlay") _closeObsCompose();
  });

  // Campo grafico ruoli
  _wireFieldClicks();

  // Rating slider live update
  const slider = document.getElementById("obs-rating");
  const display = document.getElementById("obs-rating-display");
  slider?.addEventListener("input", () => {
    display.textContent = parseFloat(slider.value).toFixed(1);
  });

  // Competizione "Altro" → mostra input libero
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

  // Tag chips (single-select)
  document.querySelectorAll(".obs-tag-chip").forEach(btn => {
    btn.addEventListener("click", () => {
      const v = btn.dataset.tag;
      window._obsCompose.selectedTag = (window._obsCompose.selectedTag === v) ? null : v;
      // Re-render solo le chip tag (no re-render globale)
      document.querySelectorAll(".obs-tag-chip").forEach(b => {
        const tg = window.OBSERVATION_TAGS.find(t => t.value === b.dataset.tag);
        const on = window._obsCompose.selectedTag === b.dataset.tag;
        b.style.background = on ? tg.color : "transparent";
        b.style.color = on ? "#fff" : tg.color;
      });
    });
  });

  // Trait chips (multi-select) — strengths e weaknesses
  function _wireTraitChips(containerId, listKey) {
    document.getElementById(containerId)?.querySelectorAll(".obs-chip").forEach(btn => {
      btn.addEventListener("click", () => {
        const trait = btn.dataset.trait;
        const list = window._obsCompose[listKey];
        const idx = list.indexOf(trait);
        if (idx >= 0) list.splice(idx, 1);
        else list.push(trait);
        const isOn = idx < 0; // post-toggle
        btn.style.borderColor = isOn ? "var(--accent)" : "var(--border)";
        btn.style.background = isOn ? "var(--accent-bg)" : "transparent";
        btn.style.color = isOn ? "var(--accent)" : "var(--text-2)";
      });
    });
  }
  _wireTraitChips("obs-strengths-chips", "selectedStrengths");
  _wireTraitChips("obs-weaknesses-chips", "selectedWeaknesses");

  // Save
  document.getElementById("obs-save-btn")?.addEventListener("click", () => _saveObsFromForm(player, editing));
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

  // Validazioni
  if (!matchDate || !opponent || !competition) {
    showErr(window.obsT("err_required"));
    return;
  }
  if (!window._obsCompose.selectedRoles.length) {
    showErr(window.obsT("err_no_role"));
    return;
  }

  const payload = {
    tm_player_id: player.tm_player_id,
    match_date: matchDate,
    opponent: opponent,
    competition: competition,
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
  // Re-render lista nel modal giocatore
  if (typeof window.renderObservationsList === "function") {
    window.renderObservationsList(player.tm_player_id);
  }
}

console.log("[obs-ui] Fase 3 modulo caricato");

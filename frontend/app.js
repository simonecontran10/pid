/**
 * Player Intelligence Database (PID) — frontend dark high-contrast.
 *
 * Modalità statica: legge JSON da ../data/. In deploy build_deploy.sh sostituisce
 * DATA_BASE con "./data".
 */

const DATA_BASE = "../data";

const state = {
  clubs: [],
  players: [],
  stats: [],
  statsById: new Map(),
  clubsById: new Map(),
  filtered: [],
  activeTab: "players",
  filters: { league: "IT1", club: "", role: "", sort: "name", q: "", yearMin: null, yearMax: null },
  compareIds: [null, null],
  lastUpdate: null,
  favorites: new Set(),
};

// ============ FAVORITES ============
const FAVORITES_STORAGE_KEY = "pid_favorites";
function loadFavorites() {
  try {
    const raw = localStorage.getItem(FAVORITES_STORAGE_KEY);
    if (!raw) return;
    const arr = JSON.parse(raw);
    if (Array.isArray(arr)) state.favorites = new Set(arr.map(Number).filter(Boolean));
  } catch {}
}
function saveFavorites() {
  try {
    localStorage.setItem(FAVORITES_STORAGE_KEY, JSON.stringify([...state.favorites]));
  } catch {}
}
function isFavorite(pid) {
  return state.favorites.has(Number(pid));
}
function toggleFavorite(pid) {
  pid = Number(pid);
  if (!pid) return false;
  if (state.favorites.has(pid)) state.favorites.delete(pid);
  else state.favorites.add(pid);
  saveFavorites();
  updateFavoritesBadge();
  return state.favorites.has(pid);
}
function updateFavoritesBadge() {
  const badge = document.getElementById("favorites-badge");
  if (!badge) return;
  const n = state.favorites.size;
  if (n > 0) { badge.textContent = String(n); badge.style.display = ""; }
  else { badge.style.display = "none"; }
}
// SVG stella - aperta (preferito off) e piena (preferito on, fill via CSS)
const FAV_STAR_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>';

// ============ FETCH ============
// File pesanti hostati su Cloudflare R2 (escluso da git/Vercel per limite 100MB)
const R2_OVERRIDES = {
  "players_stats": "https://pub-aa9d173290684b36a9f35e79d4d388c2.r2.dev/players_stats.json",
};
async function loadJSON(name) {
  // Se il file è hostato esternamente su R2, usa l'URL completo
  if (R2_OVERRIDES[name]) {
    const url = R2_OVERRIDES[name] + "?_=" + Date.now();
    try {
      const r = await fetch(url, { cache: "no-store" });
      if (!r.ok) throw new Error(`HTTP ${r.status} on ${url}`);
      return await r.json();
    } catch (e) {
      console.warn("Failed to load", name, "from R2", e);
      return null;
    }
  }
  const isHttp = DATA_BASE.startsWith("http");
  const base = isHttp
    ? `${DATA_BASE}/${name === "clubs" ? "clubs" : name === "players" ? "players?limit=999" : name}`
    : `${DATA_BASE}/${name}.json`;
  // Cache buster per evitare che il browser serva una versione stale del JSON dopo un refresh dello scrape
  const url = base + (base.includes("?") ? "&" : "?") + "_=" + Date.now();
  try {
    const r = await fetch(url, { cache: "no-store" });
    if (!r.ok) throw new Error(`HTTP ${r.status} on ${url}`);
    return await r.json();
  } catch (e) {
    console.warn("Failed to load", name, e);
    return null;
  }
}

async function bootstrap() {
  const [clubs, main, unified, stats, lastUpdate, oppNames] = await Promise.all([
    loadJSON("clubs"),
    loadJSON("players_main"),
    loadJSON("players_unified"),
    loadJSON("players_stats"),
    loadJSON("last_update"),
    loadJSON("opponent_club_names"),
  ]);
  state.opponentNames = oppNames || {};
  state.clubs = clubs || [];
  // PID: modulo U21 disattivato (era specifico Saudi U21 Excel).
  // Map vuota per compatibilità con eventuali chiamate residue a state.u21MatchesByTmid.
  state.u21MatchesByTmid = new Map();
  const wyscoutByTm = new Map();
  if (Array.isArray(unified)) {
    for (const u of unified) {
      if (u.tm_player_id && u.wyscout) wyscoutByTm.set(u.tm_player_id, u.wyscout);
    }
  }
  state.players = (main || []).map(p => {
    if (wyscoutByTm.has(p.tm_player_id)) p.wyscout = wyscoutByTm.get(p.tm_player_id);
    return p;
  });
  state.stats = stats || [];
  state.statsById = new Map(state.stats.map(s => [s.tm_player_id, s]));
  // Chiavi sia int che string per essere compatibile con opponent_club_id (string da API)
  state.clubsById = new Map();
  for (const c of state.clubs) {
    state.clubsById.set(c.tm_club_id, c);
    state.clubsById.set(String(c.tm_club_id), c);
  }
  state.lastUpdate = lastUpdate;

  document.getElementById("stat-players").textContent = state.players.length;
  document.getElementById("stat-clubs").textContent = state.clubs.length;
  renderLastUpdate();

  populateClubFilter();
  applyFilters();
  renderClubs();
}

// ============ LAST UPDATE ============
function renderLastUpdate() {
  const lu = state.lastUpdate;
  const el = document.getElementById("stat-last-update");
  const sb = document.getElementById("sidebar-last-update");
  if (!lu) {
    console.warn("renderLastUpdate: state.lastUpdate è null/undefined — il file last_update.json non è stato caricato");
    return;
  }
  // Fallback chain: completed_at → stats_completed_at → static_completed_at → started_at
  const ts = lu.completed_at || lu.stats_completed_at || lu.static_completed_at || lu.started_at;
  if (!ts) {
    console.warn("renderLastUpdate: nessun timestamp trovato in last_update.json", lu);
    return;
  }
  const d = new Date(ts);
  if (isNaN(d.getTime())) {
    console.warn("renderLastUpdate: timestamp non parsabile:", ts);
    return;
  }
  const opts = { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" };
  const locale = currentLang === "it" ? "it-IT" : "en-GB";
  if (el) el.textContent = d.toLocaleString(locale, opts);
  if (sb) sb.textContent = d.toLocaleString(locale, opts);
}

// ============ HELPERS ============
function escapeHtml(s) {
  if (s == null) return "";
  return String(s).replace(/[&<>"]/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[ch]));
}

function fmtNum(v, decimals = 2) {
  if (v == null || v === "" || isNaN(v)) return "—";
  return Number(v).toFixed(decimals);
}
function fmtPct(v) {
  if (v == null || v === "" || isNaN(v)) return "—";
  return `${Number(v).toFixed(0)}%`;
}
function fmtInt(v) {
  if (v == null || v === "" || isNaN(v)) return "—";
  return Math.round(Number(v)).toString();
}

// Cache-buster generato all'avvio dell'app per forzare il browser a ricaricare le foto
// quando il dataset è stato aggiornato (i file curated possono essere sovrascritti senza
// cambiare il path, quindi il browser cache li bloccherebbe). Si rinnova ad ogni reload.
const _PHOTO_CACHE_BUST = `?v=${Date.now()}`;

function _photoUrl(localPath) {
  if (!localPath) return null;
  return `${DATA_BASE}/${localPath}${_PHOTO_CACHE_BUST}`;
}

function birthYear(p) {
  // Estrae l'anno di nascita (es. "1991") dalla data ISO "1991-08-19".
  if (!p) return null;
  const dob = p.date_of_birth || "";
  const m = String(dob).match(/^(\d{4})/);
  return m ? m[1] : null;
}

// Abbreviazione piede localizzata (S/D/E in IT, L/R/B in EN)
function footShort(f) {
  const v = (f || "").toLowerCase();
  if (v === "left")  return t("foot_short_left");
  if (v === "right") return t("foot_short_right");
  if (v === "both")  return t("foot_short_both");
  return "";
}

// Parola intera del piede localizzata (Sinistro/Destro/Entrambi in IT, Left/Right/Both in EN)
function footFull(f) {
  const v = (f || "").toLowerCase();
  if (v === "left")  return t("foot_left");
  if (v === "right") return t("foot_right");
  if (v === "both")  return t("foot_both");
  return "";
}

// Coordinate (x, y in 0–100) su campo verticale con attacco in ALTO (y=100).
// Lo usa renderMiniPositionField() per disegnare un dot sulla posizione specifica del giocatore.
const POSITION_COORDS = {
  "Goalkeeper":          { x: 50, y: 8  },
  "Centre-Back":         { x: 50, y: 22 },
  "Left-Back":           { x: 18, y: 26 },
  "Right-Back":          { x: 82, y: 26 },
  "Defensive Midfield":  { x: 50, y: 38 },
  "Central Midfield":    { x: 50, y: 50 },   // esattamente al centro del campo
  "Attacking Midfield":  { x: 50, y: 62 },
  "Left Midfield":       { x: 20, y: 50 },
  "Right Midfield":      { x: 80, y: 50 },
  "Left Winger":         { x: 18, y: 76 },
  "Right Winger":        { x: 82, y: 76 },
  "Centre-Forward":      { x: 50, y: 88 },
  "Second Striker":      { x: 50, y: 76 },
};

// SVG mini campo verticale con cerchio sulla posizione principale (più grande)
// e cerchi outline più piccoli su quelle secondarie. Stile coerente con Griglie.
// Dimensioni QUADRATE (size×size) per garantire cerchi perfetti (no distorsione).
function renderMiniPositionField(positionSpecific, otherPositions = [], size = 132) {
  const main = POSITION_COORDS[positionSpecific];
  if (!main) return "";
  const yToCy = (y) => 2 + (100 - y) * 0.96;
  const others = (Array.isArray(otherPositions) ? otherPositions : [])
    .map(r => ({ role: r, c: POSITION_COORDS[r] }))
    .filter(o => o.c && o.role !== positionSpecific);
  const otherCircles = others.map(o => `
        <circle cx="${o.c.x}" cy="${yToCy(o.c.y)}" r="3.5" fill="rgba(111,224,168,0.20)" stroke="var(--accent)" stroke-width="0.9"/>
      `).join("");
  const otherLabels = others.length
    ? `<div style="margin-top: 6px; display: flex; flex-direction: column; align-items: center; gap: 2px;">
         <span style="font-size: 8px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-3); font-weight: 600;">${currentLang==="it"?"Altri":"Other"}</span>
         ${others.map(o => `<span style="font-size: 10px; color: var(--text-2); line-height: 1.2;">${escapeHtml(localizeRole(o.role))}</span>`).join("")}
       </div>`
    : "";
  return `
    <div style="display: flex; flex-direction: column; align-items: center; gap: 5px; padding: 12px 14px; border-radius: 12px; background: rgba(255,255,255,0.04); border: 0.5px solid var(--border); flex-shrink: 0;" title="${escapeHtml(localizeRole(positionSpecific))}">
      <span style="font-size: 9px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text-3); font-weight: 600;">${currentLang==="it"?"Posizione":"Position"}</span>
      <svg viewBox="0 0 100 100" style="width: ${size}px; height: ${size}px; display: block;" preserveAspectRatio="xMidYMid meet">
        <defs>
          <linearGradient id="pitch-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#0f4d2a" stop-opacity="0.65"/>
            <stop offset="100%" stop-color="#0c3a20" stop-opacity="0.55"/>
          </linearGradient>
        </defs>
        <rect x="2" y="2" width="96" height="96" fill="url(#pitch-grad)" stroke="rgba(255,255,255,0.35)" stroke-width="0.6"/>
        <line x1="2" y1="50" x2="98" y2="50" stroke="rgba(255,255,255,0.35)" stroke-width="0.5"/>
        <!-- Cerchio centrocampo: rx=ry → perfettamente rotondo (SVG ora quadrato) -->
        <circle cx="50" cy="50" r="10" fill="none" stroke="rgba(255,255,255,0.35)" stroke-width="0.5"/>
        <circle cx="50" cy="50" r="0.9" fill="rgba(255,255,255,0.6)"/>
        <rect x="22" y="2" width="56" height="14" fill="none" stroke="rgba(255,255,255,0.35)" stroke-width="0.5"/>
        <rect x="34" y="2" width="32" height="6" fill="none" stroke="rgba(255,255,255,0.30)" stroke-width="0.4"/>
        <rect x="22" y="84" width="56" height="14" fill="none" stroke="rgba(255,255,255,0.35)" stroke-width="0.5"/>
        <rect x="34" y="92" width="32" height="6" fill="none" stroke="rgba(255,255,255,0.30)" stroke-width="0.4"/>
        ${otherCircles}
        <!-- Cerchio posizione principale (grande, evidenziato) -->
        <circle cx="${main.x}" cy="${yToCy(main.y)}" r="8" fill="var(--accent)" stroke="rgba(14,17,22,0.9)" stroke-width="1.2"/>
        <circle cx="${main.x}" cy="${yToCy(main.y)}" r="3" fill="rgba(14,17,22,0.6)"/>
      </svg>
      <span style="font-size: 11px; color: var(--accent); font-weight: 700; text-align: center; max-width: ${size + 24}px; line-height: 1.2;">${escapeHtml(localizeRole(positionSpecific))}</span>
      ${otherLabels}
    </div>`;
}

// Localizza ruoli generici e specifici da Transfermarkt → italiano (o lascia EN)
const ROLE_TRANSLATIONS = {
  it: {
    "Goalkeeper": "Portiere",
    "Defender": "Difensore",
    "Midfield": "Centrocampista",
    "Attack": "Attaccante",
    "Centre-Back": "Difensore centrale",
    "Left-Back": "Terzino sinistro",
    "Right-Back": "Terzino destro",
    "Defensive Midfield": "Mediano",
    "Central Midfield": "Centrocampista centrale",
    "Attacking Midfield": "Trequartista",
    "Left Midfield": "Esterno sinistro",
    "Right Midfield": "Esterno destro",
    "Left Winger": "Ala sinistra",
    "Right Winger": "Ala destra",
    "Centre-Forward": "Punta centrale",
    "Second Striker": "Seconda punta",
  },
  fr: {
    "Goalkeeper": "Gardien",
    "Defender": "Défenseur",
    "Midfield": "Milieu",
    "Attack": "Attaquant",
    "Centre-Back": "Défenseur central",
    "Left-Back": "Arrière gauche",
    "Right-Back": "Arrière droit",
    "Defensive Midfield": "Milieu défensif",
    "Central Midfield": "Milieu central",
    "Attacking Midfield": "Milieu offensif",
    "Left Midfield": "Milieu gauche",
    "Right Midfield": "Milieu droit",
    "Left Winger": "Ailier gauche",
    "Right Winger": "Ailier droit",
    "Centre-Forward": "Avant-centre",
    "Second Striker": "Second attaquant",
  },
  ar: {
    "Goalkeeper": "حارس مرمى",
    "Defender": "مدافع",
    "Midfield": "وسط",
    "Attack": "مهاجم",
    "Centre-Back": "قلب دفاع",
    "Left-Back": "ظهير أيسر",
    "Right-Back": "ظهير أيمن",
    "Defensive Midfield": "وسط دفاعي",
    "Central Midfield": "وسط محوري",
    "Attacking Midfield": "صانع ألعاب",
    "Left Midfield": "وسط أيسر",
    "Right Midfield": "وسط أيمن",
    "Left Winger": "جناح أيسر",
    "Right Winger": "جناح أيمن",
    "Centre-Forward": "مهاجم صريح",
    "Second Striker": "مهاجم ثانٍ",
  },
};
function localizeRole(role) {
  if (!role) return "";
  const dict = ROLE_TRANSLATIONS[currentLang];
  if (dict && dict[role]) return dict[role];
  return role; // EN o lingua senza mapping → fallback originale
}

// Normalizza una stringa per la ricerca: lowercase, no diacritici, trattini/punti → spazi.
// Es. "Ahmed Al-Siyahi" → "ahmed al siyahi" (così cercando "siyahi" matcha anche "Al-Siyahi").
function _normalizeText(s) {
  return String(s == null ? "" : s)
    .toLowerCase()
    .normalize("NFD").replace(/[̀-ͯ]/g, "")
    .replace(/[-_'.]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

// Match ricerca tollerante su un giocatore. Tutti i token della query devono comparire nel
// blob normalizzato (full_name + name_arabic + club + position_general + position_specific).
// Cerca anche per cognome puro (es. "siyahi" → "Ahmed Al-Siyahi" perché blob normalizzato è "ahmed al siyahi").
function matchPlayer(p, q) {
  if (!q) return true;
  const ql = _normalizeText(q);
  if (!ql) return true;
  const tokens = ql.split(/\s+/).filter(Boolean);
  const blob = _normalizeText([
    p.full_name,
    p.name_arabic,
    p.current_club_name,
    p.position_general,
    p.position_specific,
  ].filter(Boolean).join(" "));
  return tokens.every(tok => blob.includes(tok));
}

// Match ricerca tollerante su un club (nome + league_name + lega abbreviata IT1/IT2).
function matchClub(c, q) {
  if (!q) return true;
  const ql = _normalizeText(q);
  if (!ql) return true;
  const tokens = ql.split(/\s+/).filter(Boolean);
  const blob = _normalizeText([c.name, c.league_name, c.league_id].filter(Boolean).join(" "));
  return tokens.every(tok => blob.includes(tok));
}

function _isDefaultTMPhoto(url) {
  if (!url) return true;
  return url.includes("/portrait/header/default.") || url.includes("/portrait/big/default.") || url.includes("default.png");
}

function playerPhoto(p) {
  // Cascade: sortitoutsi prima (curata > lookup > local), poi Transfermarkt (locale > remoto), infine avatar generato.
  const tmLocal = _isDefaultTMPhoto(p.photo_local) ? null : _photoUrl(p.photo_local);
  const tmRemote = _isDefaultTMPhoto(p.photo_url) ? null : p.photo_url;
  return _photoUrl(p.sortitoutsi_face_local_curated)
      || _photoUrl(p.sortitoutsi_face_local_lookup)
      || _photoUrl(p.sortitoutsi_face_local)
      || tmLocal
      || tmRemote
      || `https://ui-avatars.com/api/?name=${encodeURIComponent(p.full_name||"?")}&size=256&background=1A1F26&color=6FE0A8&bold=true&font-size=0.45`;
}

function nationFlag(p) {
  const cs = (p && p.citizenships) || [];
  if (!cs.length) return null;
  const country = String(cs[0]).trim();
  if (!country) return null;
  // Normalizza nome → filename: "Cote d'Ivoire" → "Cote-dIvoire", "Korea, South" → "Korea-South"
  const fname = country
    .replace(/'/g, "")
    .replace(/,/g, "")
    .replace(/\s+/g, "-");
  return _photoUrl("photos/national/" + fname + ".png");
}

function clubLogo(c) {
  if (!c) return null;
  return _photoUrl(c.sortitoutsi_logo_local_curated)
      || _photoUrl(c.sortitoutsi_logo_local)
      || c.sortitoutsi_logo_url
      || _photoUrl(c.logo_local)
      || c.logo_url
      || null;
}

function competitionLogo(compCode) {
  if (!compCode) return null;
  const known = { IT1: "png", IT2: "png", IJ1: "png", PL1: "png", PL2: "png", SDL: "png", CIT: "png", SCI: "png", "23AF": "png", ACLE: "svg", ACL2: "svg", ES1: "svg" };
  // SA2P (Saudi Second Division League) → usa il logo curato SDL.png
  // ES1 → riusa il logo di ACL2
  const code = compCode === "ES1" ? "ACL2" : compCode === "SA2P" ? "SDL" : compCode;
  const ext = known[code];
  if (ext) return _photoUrl(`photos/competitions/${code}.${ext}`);
  const nationalCodes = ["FS","WMQ1","AFAC","ACQA","ARCP","FIWC","AGUC","WAF1","WC","20WC","U17W","OLYM","GOCU"];
  if (nationalCodes.includes(compCode)) return _photoUrl("photos/branding/logo.png");
  return null;
}

function totalGoals2025(pid) {
  const s = state.statsById.get(pid);
  if (!s) return 0;
  const season = s.seasons?.["2025"] || {};
  return Object.values({ ...season.club, ...season.national }).reduce((a, b) => a + (b.goals || 0), 0);
}

// ============ FILTERING ============
function populateClubFilter() {
  const sel = document.getElementById("filter-club");
  const opts = [...state.clubs]
    .sort((a,b) => (a.name||"").localeCompare(b.name||""))
    .map(c => `<option value="${c.tm_club_id}">${escapeHtml(c.name)}</option>`);
  sel.innerHTML = `<option value="">${t("filter_all_clubs")}</option>${opts.join("")}`;
}

function applyFilters() {
  const { league, club, role, sort, q, yearMin, yearMax } = state.filters;
  let items = [...state.players];
  if (yearMin || yearMax) {
    items = items.filter(p => {
      const yr = parseInt(birthYear(p));
      if (!yr) return false;
      if (yearMin && yr < yearMin) return false;
      if (yearMax && yr > yearMax) return false;
      return true;
    });
  }
  if (league === "OTHER") {
    // Club senza league_id riconosciuta (fallback per dati legacy)
    const KNOWN_LEAGUES = new Set(["IT1", "IT2", "IJ1", "PL1", "PL2"]);
    const knownClubIds = new Set(state.clubs.filter(c => KNOWN_LEAGUES.has(c.league_id)).map(c => c.tm_club_id));
    items = items.filter(p => !knownClubIds.has(p.current_club_id));
  } else if (league) {
    // Filtra giocatori il cui current_club_id appartiene a un club della lega
    const leagueClubIds = new Set(state.clubs.filter(c => c.league_id === league).map(c => c.tm_club_id));
    items = items.filter(p => leagueClubIds.has(p.current_club_id));
  }
  if (club) items = items.filter(p => String(p.current_club_id) === String(club));
  if (role) items = items.filter(p => (p.position_general||"").toLowerCase() === role.toLowerCase());
  if (q) {
    const ql = q.toLowerCase();
    items = items.filter(p =>
      (p.full_name||"").toLowerCase().includes(ql) ||
      (p.current_club_name||"").toLowerCase().includes(ql)
    );
  }
  if (sort === "age_asc") items.sort((a,b) => (a.age||999) - (b.age||999));
  else if (sort === "age_desc") items.sort((a,b) => (b.age||0) - (a.age||0));
  else if (sort === "club") items.sort((a,b) => (a.current_club_name||"").localeCompare(b.current_club_name||""));
  else if (sort === "goals_desc") items.sort((a,b) => totalGoals2025(b.tm_player_id) - totalGoals2025(a.tm_player_id));
  else items.sort((a,b) => (a.full_name||"").localeCompare(b.full_name||""));

  state.filtered = items;
  renderPlayers();
  document.getElementById("count-info").textContent = t("n_players", items.length);
}

// ============ RENDER PLAYERS (card piccole + logo club) ============
function renderPlayers() {
  const grid = document.getElementById("players-grid");
  if (!state.filtered.length) {
    grid.innerHTML = `<div class="col-span-full text-center py-12" style="color: var(--text-3);">${t("no_results")}</div>`;
    return;
  }
  grid.innerHTML = state.filtered.map(p => {
    const club = state.clubsById.get(p.current_club_id);
    const logo = clubLogo(club);
    const goals = totalGoals2025(p.tm_player_id);
    const goalsBadge = goals > 0
      ? `<span class="absolute top-1 right-1 px-1 py-0.5 text-[10px] rounded font-bold stat-cell" title="${currentLang==='it'?goals+' gol nella stagione 25/26':goals+' goals season 25/26'}" style="background: rgba(251,191,36,0.20); color: #FBBF24; border: 0.5px solid rgba(251,191,36,0.30);">⚽${goals}</span>`
      : "";
    const shirt = p.shirt_number
      ? `<div class="absolute top-1 left-1" title="${currentLang==='it'?'Maglia '+p.shirt_number:'Shirt '+p.shirt_number}" style="width: 26px; height: 30px; filter: drop-shadow(0 1px 2px rgba(0,0,0,0.6));">
          <svg viewBox="0 0 26 30" xmlns="http://www.w3.org/2000/svg" style="width: 100%; height: 100%;">
            <path d="M 5 1 L 9 1 Q 13 4 17 1 L 21 1 L 25 6 L 21 9 L 21 28 Q 21 29 20 29 L 6 29 Q 5 29 5 28 L 5 9 L 1 6 Z" fill="#1A1F26" stroke="#6FE0A8" stroke-width="0.8"/>
            <text x="13" y="20" text-anchor="middle" font-family="-apple-system, sans-serif" font-size="11" font-weight="700" fill="#6FE0A8">${p.shirt_number}</text>
          </svg>
        </div>`
      : "";
    return `
    <button class="player-card text-left rounded-xl overflow-hidden relative" data-pid="${p.tm_player_id}" style="background: var(--surface); border: 0.5px solid var(--border);">
      <div class="overflow-hidden relative" style="aspect-ratio: 1/1; background: linear-gradient(180deg, #21262E 0%, #14181E 100%);">
        ${shirt}${goalsBadge}
        <span class="fav-star ${isFavorite(p.tm_player_id) ? 'is-fav' : ''}" data-fav="${p.tm_player_id}" title="${t(isFavorite(p.tm_player_id) ? 'remove_from_favorites' : 'add_to_favorites')}">${FAV_STAR_SVG}</span>
        ${(() => { const fl = nationFlag(p); return fl ? `<div class="absolute bottom-1 left-1 w-8 h-8 flex items-center justify-center" style="filter: drop-shadow(0 1px 3px rgba(0,0,0,0.6));"><img src="${fl}" alt="" class="w-8 h-8 object-contain" loading="lazy" onerror="this.parentElement.style.display='none'"/></div>` : ""; })()}
        <img src="${playerPhoto(p)}" alt="${escapeHtml(p.full_name)}" class="w-full h-full object-contain" loading="lazy"
             style="padding: 14px;"
             onerror="(function(img){var fb=${JSON.stringify(p.photo_url || '')};var av='https://ui-avatars.com/api/?name=${encodeURIComponent(p.full_name||'?')}&size=256&background=1A1F26&color=6FE0A8&bold=true&font-size=0.45';if(fb && img.src!==fb && fb.indexOf('default')<0){img.src=fb;img.onerror=function(){img.onerror=null;img.src=av;};}else{img.onerror=null;img.src=av;}})(this)"/>
        ${logo ? `<div class="absolute bottom-1 right-1 w-8 h-8 flex items-center justify-center" style="filter: drop-shadow(0 1px 3px rgba(0,0,0,0.6));"><img src="${logo}" alt="" class="w-8 h-8 object-contain" loading="lazy"/></div>` : ""}
      </div>
      <div class="px-2 py-2">
        <div class="text-[13px] font-semibold leading-tight truncate" style="color: var(--text-1);">${escapeHtml(p.full_name)||"—"}</div>
        <div class="flex items-center justify-between mt-1.5 gap-1">
          <span class="text-[10px] px-1.5 py-0.5 rounded truncate" style="background: var(--accent-bg); color: var(--accent);">${escapeHtml(localizeRole(p.position_specific || p.position_general))}</span>
          <span class="text-[10px] stat-cell flex-shrink-0" style="color: var(--text-3);">${birthYear(p) || (p.age || "")}</span>
        </div>
      </div>
    </button>`;
  }).join("");
  grid.querySelectorAll("[data-pid]").forEach(el => el.addEventListener("click", (ev) => {
    // Se il click è sulla stella, gestiscila e non aprire il modal
    const star = ev.target.closest("[data-fav]");
    if (star) {
      ev.stopPropagation();
      ev.preventDefault();
      const pid = parseInt(star.dataset.fav);
      const nowFav = toggleFavorite(pid);
      star.classList.toggle("is-fav", nowFav);
      star.title = t(nowFav ? "remove_from_favorites" : "add_to_favorites");
      // Se siamo nel pannello favorites, refresh
      if (state.activeTab === "favorites") renderFavoritesPanel();
      return;
    }
    openPlayerModal(parseInt(el.dataset.pid));
  }));
}

// ============ RENDER CLUBS (diviso per lega) ============
state.clubsSort = state.clubsSort || "name";

function renderClubs() {
  const container = document.getElementById("clubs-content");
  if (!state.clubs.length) {
    container.innerHTML = `<div class="text-center py-12" style="color: var(--text-3);">${t("no_results")}</div>`;
    return;
  }

  const playersByClubCount = (cid) => state.players.filter(p => p.current_club_id === cid).length;
  const sortClubs = (clubs) => {
    const arr = [...clubs];
    if (state.clubsSort === "by_count_desc") arr.sort((a,b) => playersByClubCount(b.tm_club_id) - playersByClubCount(a.tm_club_id));
    else if (state.clubsSort === "by_count_asc") arr.sort((a,b) => playersByClubCount(a.tm_club_id) - playersByClubCount(b.tm_club_id));
    else arr.sort((a,b) => (a.name||"").localeCompare(b.name||""));
    return arr;
  };

  const it1 = sortClubs(state.clubs.filter(c => c.league_id === "IT1"));
  const it2 = sortClubs(state.clubs.filter(c => c.league_id === "IT2"));
  const ij1 = sortClubs(state.clubs.filter(c => c.league_id === "IJ1"));
  const pl1 = sortClubs(state.clubs.filter(c => c.league_id === "PL1"));
  const pl2 = sortClubs(state.clubs.filter(c => c.league_id === "PL2"));
  const KNOWN_LEAGUES = new Set(["IT1", "IT2", "IJ1", "PL1", "PL2"]);
  const others = sortClubs(state.clubs.filter(c => !KNOWN_LEAGUES.has(c.league_id)));

  const renderClubCard = (c) => {
    const logo = clubLogo(c);
    const nPlayers = state.players.filter(p => p.current_club_id === c.tm_club_id).length;
    return `
      <button class="player-card rounded-lg flex flex-col items-center justify-center text-center gap-1 p-2" data-cid="${c.tm_club_id}" style="background: var(--surface); border: 0.5px solid var(--border);">
        ${logo
          ? `<img src="${logo}" alt="${escapeHtml(c.name)}" class="w-10 h-10 object-contain flex-shrink-0" loading="lazy"/>`
          : `<div class="w-10 h-10 rounded flex items-center justify-center font-bold text-base flex-shrink-0" style="background: var(--accent-bg); color: var(--accent);">${(c.name||"?")[0]}</div>`
        }
        <div class="flex flex-col items-center justify-center min-w-0 w-full">
          <div class="text-[10px] font-semibold leading-tight truncate w-full" style="color: var(--text-1);">${escapeHtml(c.name)}</div>
          <div class="text-[9px] mt-0.5 stat-cell" style="color: var(--accent);">${nPlayers}</div>
        </div>
      </button>`;
  };

  const sectionHtml = (title, leagueLogo, clubs, accentVar) => `
    <section class="mb-6">
      <div class="flex items-center gap-2 mb-3 pb-1.5" style="border-bottom: 0.5px solid var(--border);">
        ${leagueLogo ? `<img src="${leagueLogo}" alt="" class="w-9 h-9 object-contain"/>` : ""}
        <h3 class="text-sm font-bold tracking-tight" style="color: var(--text-1);">${escapeHtml(title)}</h3>
        <span class="ml-auto text-[10px] stat-cell px-1.5 py-0.5 rounded-full" style="background: ${accentVar}; color: var(--text-2); border: 0.5px solid var(--border);">${clubs.length} club</span>
      </div>
      <div class="grid grid-cols-3 sm:grid-cols-5 md:grid-cols-7 lg:grid-cols-9 xl:grid-cols-9 gap-1.5">
        ${clubs.map(renderClubCard).join("")}
      </div>
    </section>`;

  const it1Logo = _photoUrl("photos/competitions/IT1.png");
  const it2Logo = _photoUrl("photos/competitions/IT2.png");
  const ij1Logo = _photoUrl("photos/competitions/IJ1.png");
  const pl1Logo = _photoUrl("photos/competitions/PL1.png");
  const pl2Logo = _photoUrl("photos/competitions/PL2.png");

  // Toolbar di ordinamento
  const sortBar = `
    <div class="flex items-center gap-2 mb-4">
      <label style="font-size: 11px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.06em;">${currentLang==="it"?"Ordina":"Sort"}:</label>
      <select id="clubs-sort" class="filter-select" style="font-size: 12px;">
        <option value="name" ${state.clubsSort==="name"?"selected":""}>${currentLang==="it"?"Nome A-Z":"Name A-Z"}</option>
        <option value="by_count_desc" ${state.clubsSort==="by_count_desc"?"selected":""}>${currentLang==="it"?"Più giocatori":"Most players"}</option>
        <option value="by_count_asc" ${state.clubsSort==="by_count_asc"?"selected":""}>${currentLang==="it"?"Meno giocatori":"Fewest players"}</option>
      </select>
    </div>`;

  container.innerHTML = sortBar +
    (it1.length ? sectionHtml(t("league_it1"), it1Logo, it1, "rgba(111,224,168,0.08)") : "") +
    (it2.length ? sectionHtml(t("league_it2"), it2Logo, it2, "rgba(251,146,60,0.08)") : "") +
    (ij1.length ? sectionHtml(t("league_ij1"), ij1Logo, ij1, "rgba(192,132,252,0.08)") : "") +
    (pl1.length ? sectionHtml(t("league_pl1"), pl1Logo, pl1, "rgba(239,68,68,0.08)") : "") +
    (pl2.length ? sectionHtml(t("league_pl2"), pl2Logo, pl2, "rgba(96,165,250,0.08)") : "") +
    (others.length ? sectionHtml(t("league_other"), null, others, "rgba(255,255,255,0.06)") : "");

  // Aggiorna contatore "leghe" nella stats bar
  const leaguesCount = [it1, it2, ij1, pl1, pl2].filter(arr => arr.length).length;
  const statLeagues = document.getElementById("stat-leagues");
  if (statLeagues) statLeagues.textContent = leaguesCount;

  document.getElementById("clubs-sort")?.addEventListener("change", e => {
    state.clubsSort = e.target.value;
    renderClubs();
  });

  container.querySelectorAll("[data-cid]").forEach(el => el.addEventListener("click", () => {
    state.filters.club = el.dataset.cid;
    document.getElementById("filter-club").value = el.dataset.cid;
    setActiveTab("home");
    applyFilters();
  }));
}

// ============ PLAYER MODAL (dark redesign) ============
function openPlayerModal(pid) {
  const p = state.players.find(x => x.tm_player_id === pid);
  if (!p) return;
  const stats = state.statsById.get(pid);
  const seasons = stats?.seasons || {};
  const club = state.clubsById.get(p.current_club_id);
  const clubLogoUrl = clubLogo(club);

  const seasonKeys = Object.keys(seasons).sort().reverse();
  // Stagione corrente: sempre 2025/26 (anche se il giocatore non ha ancora dati per questa stagione)
  const currentKey = "2025";
  const currentSeason = seasons[currentKey] || { club: {}, national: {} };
  const currentSeasonHasData = !!seasons[currentKey];
  const sumSeason = (sec) => Object.values(sec || {}).reduce(
    (acc, s) => ({ apps: acc.apps + (s.apps||0), goals: acc.goals + (s.goals||0),
                   assists: acc.assists + (s.assists||0), minutes: acc.minutes + (s.minutes_played||0) }),
    { apps: 0, goals: 0, assists: 0, minutes: 0 }
  );
  const cur = (() => {
    const c = sumSeason(currentSeason.club);
    const n = sumSeason(currentSeason.national);
    // Aggiunge i totali U21 dell'Excel (Saudi U21 Elite League) per la stagione corrente
    const u21 = (() => {
      const list = _u21MatchesNormalized(pid);
      let apps = 0, minutes = 0;
      for (const m of list) {
        const ds = (m.date || "").slice(0, 10);
        if (!ds) continue;
        const [y, mo] = ds.split("-").map(Number);
        // Stagione corrente: luglio 2025 → giugno 2026
        if ((y === 2025 && mo >= 7) || (y === 2026 && mo <= 6)) {
          apps += 1;
          minutes += (m.minutes || 0);
        }
      }
      return { apps, minutes };
    })();
    return {
      apps:    c.apps + n.apps + u21.apps,
      goals:   c.goals + n.goals,
      assists: c.assists + n.assists,
      minutes: c.minutes + n.minutes + u21.minutes,
    };
  })();
  // Forza il blocco stagionale a renderizzare anche se TM non ha dati (es. solo U21 Excel)
  const hasU21Current = pid != null && _u21MatchesNormalized(pid).some(m => {
    const ds = (m.date || "").slice(0,10);
    if (!ds) return false;
    const [y, mo] = ds.split("-").map(Number);
    return (y === 2025 && mo >= 7) || (y === 2026 && mo <= 6);
  });

  // ----- Renderer riga competizione (stile pulito) -----
  const compColor = (code, isNational) => {
    if (isNational) return "var(--comp-nat)";
    if (code === "IT1") return "var(--comp-seriea)";
    if (code === "IT2") return "var(--comp-serieb)";
    if (code === "IJ1") return "var(--comp-ij1)";
    if (code === "PL1") return "var(--comp-pl1)";
    if (code === "PL2") return "var(--comp-pl2)";
    if (code === "ACLE" || code === "ACL2" || code === "ES1") return "var(--comp-acl)";
    if (code === "CIT" || code === "SCI") return "var(--comp-cup)";
    return "var(--text-3)";
  };

  const teamCatLabel = (cat) => {
    if (!cat) return null;
    if (cat === "A") return currentLang === "it" ? "Prima squadra" : "Senior";
    if (cat === "U23") return "U23";
    if (cat === "U22") return "U22";
    if (cat === "U20") return "U20";
    if (cat === "U19") return "U19";
    if (cat === "U18") return "U18";
    if (cat === "U17") return "U17";
    if (cat === "U16") return "U16";
    if (cat === "U15") return "U15";
    if (cat === "Olympic") return currentLang === "it" ? "Olimpica" : "Olympic";
    return cat;
  };
  const teamCatColor = (cat) => {
    if (cat === "A") return "var(--accent)";
    if (cat === "Olympic") return "#FBBF24";
    if (cat === "U23" || cat === "U22") return "#60A5FA";
    if (cat === "U20" || cat === "U19") return "#A78BFA";
    if (cat === "U18" || cat === "U17") return "#F472B6";
    if (cat === "U16" || cat === "U15") return "#FB923C";
    return "var(--text-3)";
  };
  const renderRow = (code, s, opts = {}) => {
    const { isNational = false, seasonPrefix = null, dim = false } = opts;
    const color = compColor(code, isNational);
    const goalsHot = s.goals >= 5;
    const assistsHot = s.assists >= 5;
    const catLabel = isNational ? teamCatLabel(s.team_category) : null;
    const catColor = isNational ? teamCatColor(s.team_category) : null;
    const compLogo = competitionLogo(code);
    return `
      <div style="display: grid; grid-template-columns: 1fr 38px 38px 38px 64px; gap: 12px; align-items: center; padding: 8px 14px; border-bottom: 0.5px solid var(--border);">
        <div style="display: flex; align-items: center; gap: 10px; min-width: 0; flex-wrap: wrap;">
          ${seasonPrefix ? `<span class="stat-cell" style="font-size: 10px; color: var(--text-3); min-width: 36px;">${seasonPrefix}</span>` : ""}
          ${compLogo
            ? `<img src="${compLogo}" alt="" style="width: 18px; height: 18px; object-fit: contain; flex-shrink: 0;"/>`
            : `<span style="width: 3px; height: 14px; background: ${color}; border-radius: 2px; flex-shrink: 0;"></span>`}
          ${catLabel ? `<span class="stat-cell" style="font-size: 10px; padding: 2px 7px; border-radius: 999px; background: ${catColor}1A; color: ${catColor}; font-weight: 600; flex-shrink: 0;">${catLabel}</span>` : ""}
          <span class="truncate" style="font-size: 13px; color: ${dim ? "var(--text-2)" : "var(--text-1)"};">${escapeHtml(_compName(code, s.competition_name))}</span>
        </div>
        <span class="stat-cell" style="font-size: 14px; font-weight: 600; color: ${s.apps ? "var(--text-1)" : "var(--text-3)"}; text-align: center; font-variant-numeric: tabular-nums;">${s.apps || 0}</span>
        <span class="stat-cell" style="font-size: 14px; font-weight: 600; color: ${goalsHot ? "var(--hot)" : (s.goals ? "var(--text-1)" : "var(--text-3)")}; text-align: center; font-variant-numeric: tabular-nums;">${s.goals || 0}</span>
        <span class="stat-cell" style="font-size: 14px; font-weight: 600; color: ${assistsHot ? "var(--hot)" : (s.assists ? "var(--text-1)" : "var(--text-3)")}; text-align: center; font-variant-numeric: tabular-nums;">${s.assists || 0}</span>
        <span class="stat-cell" style="font-size: 13px; font-weight: 700; color: ${s.minutes_played ? "var(--accent)" : "var(--text-3)"}; text-align: right; font-variant-numeric: tabular-nums; padding: 2px 6px; border-radius: 4px; background: ${s.minutes_played ? "rgba(111,224,168,0.08)" : "transparent"};">${s.minutes_played ? (s.minutes_played + "'") : "0'"}</span>
      </div>`;
  };

  // Header allineato sulla stessa grid della renderRow
  const tableHeader = `
    <div style="display: grid; grid-template-columns: 1fr 38px 38px 38px 64px; gap: 12px; align-items: center; padding: 4px 14px 8px;">
      <span></span>
      <span class="stat-cell" style="font-size: 10px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.06em; text-align: center; font-weight: 600;">${t("apps")}</span>
      <span class="stat-cell" style="font-size: 10px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.06em; text-align: center; font-weight: 600;">${t("goals")}</span>
      <span class="stat-cell" style="font-size: 10px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.06em; text-align: center; font-weight: 600;">${t("assists")}</span>
      <span class="stat-cell" style="font-size: 10px; color: var(--accent); text-transform: uppercase; letter-spacing: 0.06em; text-align: right; font-weight: 700;">${t("col_min")}</span>
    </div>`;

  // CLUB blocks: una sezione per stagione, separate da divider sottile
  const clubBlocksArr = seasonKeys.map(season => {
    const rows = Object.entries(seasons[season].club || {});
    if (!rows.length) return null;
    return `
      <div>
        <div style="font-size: 11px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.08em; font-weight: 500; margin-bottom: 6px; padding: 0 4px;">${t("season_label", season)}</div>
        <div style="background: rgba(255,255,255,0.03); border-radius: 10px; overflow: hidden;">
          ${rows.map(([code, s]) => renderRow(code, s, { isNational: false })).join("")}
        </div>
      </div>`;
  }).filter(Boolean);
  const clubBlocks = clubBlocksArr.join(`<div style="height: 1px; background: var(--border-strong); margin: 18px 0;"></div>`);

  // NATIONAL: tutte le righe in un blocco unico, prefisso stagione su ogni riga
  const natRows = seasonKeys.flatMap(season =>
    Object.entries(seasons[season].national || {}).map(([code, s]) => ({ code, s, season }))
  );
  const natBlock = natRows.length ? `
    <div style="background: rgba(255,255,255,0.03); border-radius: 10px; overflow: hidden;">
      ${natRows.map(({ code, s, season }) => renderRow(code, s, { isNational: true, seasonPrefix: t("season_label", season).slice(-5), dim: false })).join("")}
    </div>` : "";

  const wy = p.wyscout;
  const wyHtml = wy ? renderWyscoutStats(wy, p.position_general) : "";

  const compareIdx = state.compareIds.indexOf(pid);
  const inCompare = compareIdx >= 0;

  const footMap = { left: t("foot_left"), right: t("foot_right"), both: t("foot_both") };
  const footLabel = footMap[p.foot] || p.foot || "";
  const footPref = (p.foot || "").toLowerCase(); // "left", "right", "both"
  const heightLabel = p.height_cm ? p.height_cm + " cm" : null;

  // Splitta name_arabic in nome arabo + nome esteso latino se contiene virgola
  const _arabicMatch = (s) => /[؀-ۿ]/.test(s || "");
  let nameExtended = null;
  let nameArabicPure = null;
  if (p.name_arabic) {
    const parts = p.name_arabic.split(",").map(s => s.trim()).filter(Boolean);
    if (parts.length >= 2) {
      // es: "Abbas bin Sadiq bin Nasser Al-Hassan, عباس الحسن"
      const ar = parts.find(_arabicMatch);
      const lat = parts.find(s => !_arabicMatch(s));
      nameArabicPure = ar || null;
      nameExtended = lat || null;
    } else if (_arabicMatch(p.name_arabic)) {
      nameArabicPure = p.name_arabic;
    } else {
      nameExtended = p.name_arabic;
    }
  }

  const footWidget = footLabel
    ? `<span style="font-size: 12px; padding: 4px 10px; border-radius: 999px; background: rgba(255,255,255,0.05); color: var(--text-2);">${escapeHtml(footLabel)}</span>`
    : "";

  const html = `
    <div style="position: relative; padding: 28px 28px 24px; background: linear-gradient(135deg, #1A2D24 0%, #0E1116 60%); border-bottom: 0.5px solid var(--border);">
      <div style="display: flex; gap: 22px; align-items: flex-start; flex-wrap: wrap;">
        <img src="${playerPhoto(p)}" alt="${escapeHtml(p.full_name)}" style="width: 144px; height: 144px; border-radius: 12px; object-fit: cover; background: var(--surface-2); flex-shrink: 0; border: 0.5px solid var(--border-strong);"
             onerror="(function(img){var fb=${JSON.stringify(p.photo_url || '')};var av='https://ui-avatars.com/api/?name=${encodeURIComponent(p.full_name||'?')}&size=256&background=1A1F26&color=6FE0A8&bold=true&font-size=0.45';if(fb && img.src!==fb && fb.indexOf('default')<0){img.src=fb;img.onerror=function(){img.onerror=null;img.src=av;};}else{img.onerror=null;img.src=av;}})(this)"/>
        <div style="flex: 1; min-width: 0;">
          <div style="display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap;">
            <h2 style="font-size: 28px; font-weight: 500; color: var(--text-1); letter-spacing: -0.02em; margin: 0;">${escapeHtml(p.full_name || "")}</h2>
            ${p.shirt_number ? `<span class="stat-cell" style="font-size: 18px; font-weight: 500; color: var(--accent);">#${p.shirt_number}</span>` : ""}
          </div>
          ${nameExtended ? `<div style="font-size: 13px; color: var(--text-2); margin-top: 2px;">${escapeHtml(nameExtended)}</div>` : ""}
          ${nameArabicPure ? `<div style="font-size: 16px; color: var(--text-2); margin-top: 4px; text-align: left;"><span dir="rtl">${escapeHtml(nameArabicPure)}</span></div>` : ""}

          <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; align-items: center;">
            <span style="font-size: 12px; padding: 4px 10px; border-radius: 999px; background: var(--accent-bg); color: var(--accent); font-weight: 500;">${escapeHtml(localizeRole(p.position_specific || p.position_general))}</span>
            ${(() => {
              const ageSuffix = currentLang === "it" ? "anni" : "yrs";
              if (p.date_of_birth) {
                const m = String(p.date_of_birth).match(/^(\d{4})-(\d{2})-(\d{2})/);
                const dobLabel = m ? `${m[3]}/${m[2]}/${m[1]}` : escapeHtml(p.date_of_birth);
                return `<span class="stat-cell" style="font-size: 12px; padding: 4px 10px; border-radius: 999px; background: rgba(255,255,255,0.05); color: var(--text-2);">${dobLabel}${p.age?` · ${p.age} ${ageSuffix}`:""}</span>`;
              }
              if (p.age) return `<span class="stat-cell" style="font-size: 12px; padding: 4px 10px; border-radius: 999px; background: rgba(255,255,255,0.05); color: var(--text-2);">${p.age} ${ageSuffix}</span>`;
              return "";
            })()}
            ${heightLabel ? `<span class="stat-cell" style="font-size: 12px; padding: 4px 10px; border-radius: 999px; background: rgba(255,255,255,0.05); color: var(--text-2);">${escapeHtml(heightLabel)}</span>` : ""}
            ${footWidget}
          </div>

        </div>
        ${(() => {
          const flagUrl = nationFlag(p);
          const country = (p.citizenships && p.citizenships[0]) || "";
          if (!flagUrl || !country) return "";
          return `
          <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px; padding: 14px 18px; border-radius: 12px; background: rgba(255,255,255,0.04); border: 0.5px solid var(--border); flex-shrink: 0; min-width: 130px;">
            <img src="${flagUrl}" style="width: 64px; height: 64px; object-fit: contain;" alt="" onerror="this.style.display='none'"/>
            <div style="text-align: center;">
              <div style="font-size: 14px; font-weight: 600; color: var(--text-1); line-height: 1.2;">${escapeHtml(country)}</div>
              <div style="font-size: 11px; color: var(--text-3); line-height: 1.2; margin-top: 3px;">${currentLang==="it"?"Nazionalità":"Nationality"}</div>
              ${(p.citizenships && p.citizenships.length > 1) ? `<div style="font-size: 11px; color: var(--text-2); line-height: 1.2; margin-top: 4px; font-style: italic;">+ ${escapeHtml(p.citizenships.slice(1).join(", "))}</div>` : ""}
            </div>
          </div>`;
        })()}
        ${p.current_club_name ? `
          <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px; padding: 14px 18px; border-radius: 12px; background: rgba(255,255,255,0.04); border: 0.5px solid var(--border); flex-shrink: 0; min-width: 150px;">
            ${clubLogoUrl ? `<img src="${clubLogoUrl}" style="width: 64px; height: 64px; object-fit: contain;" alt=""/>` : `<div style="width: 64px; height: 64px; border-radius: 8px; background: var(--accent-bg); color: var(--accent); display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: 700;">${(p.current_club_name||"?")[0]}</div>`}
            <div style="text-align: center;">
              <div style="font-size: 14px; font-weight: 600; color: var(--text-1); line-height: 1.2;">${escapeHtml(p.current_club_name)}</div>
              <div style="font-size: 11px; color: var(--text-3); line-height: 1.2; margin-top: 3px;">${escapeHtml(club?.league_name || "")}</div>
            </div>
          </div>` : ""}
        ${renderMiniPositionField(p.position_specific, p.position_others || [])}
        <div style="display: flex; flex-direction: column; gap: 8px; align-items: flex-end; flex-shrink: 0;">
          <button id="modal-close" style="width: 32px; height: 32px; border-radius: 8px; background: rgba(255,255,255,0.06); color: var(--text-1); border: 0.5px solid var(--border-strong); font-size: 16px; line-height: 1; cursor: pointer;">×</button>
          <button id="compare-toggle" style="padding: 5px 10px; border-radius: 8px; background: transparent; color: var(--accent); border: 0.5px solid rgba(111,224,168,0.30); font-size: 11px; cursor: pointer; white-space: nowrap;">
            ${inCompare ? t("remove_from_compare") : t("add_to_compare")}
          </button>
          <button id="modal-fav-toggle" style="padding: 5px 10px; border-radius: 8px; background: ${isFavorite(pid)?"rgba(251,191,36,0.18)":"transparent"}; color: var(--hot); border: 0.5px solid ${isFavorite(pid)?"rgba(251,191,36,0.50)":"rgba(251,191,36,0.30)"}; font-size: 11px; cursor: pointer; white-space: nowrap; display: inline-flex; align-items: center; gap: 4px;">
            <span style="font-size: 12px;">${isFavorite(pid) ? "★" : "☆"}</span>
            ${isFavorite(pid) ? t("remove_from_favorites") : t("add_to_favorites")}
          </button>
          <button id="callup-add-from-modal" style="padding: 5px 10px; border-radius: 8px; background: ${state.callup.currentIds.includes(pid)?"rgba(239,68,68,0.10)":"var(--accent-bg)"}; color: ${state.callup.currentIds.includes(pid)?"#EF4444":"var(--accent)"}; border: 0.5px solid ${state.callup.currentIds.includes(pid)?"rgba(239,68,68,0.30)":"rgba(111,224,168,0.30)"}; font-size: 11px; cursor: pointer; white-space: nowrap; font-weight: 600;">
            ${state.callup.currentIds.includes(pid) ? (currentLang==="it"?"− Rimuovi convocazione":"− Remove call-up") : (currentLang==="it"?"+ Convoca":"+ Call up")}
          </button>
          <button id="modal-notes-toggle" style="padding: 5px 10px; border-radius: 8px; background: transparent; color: var(--info); border: 0.5px solid rgba(96,165,250,0.30); font-size: 11px; cursor: pointer; white-space: nowrap;">
            📝 ${currentLang==="it"?"Note":"Notes"}${(state.playerNotes && state.playerNotes[pid]) ? ` <span class="stat-cell" style="color: var(--accent); font-size: 9px;">●</span>` : ""}
          </button>
        </div>
      </div>
    </div>

    <!-- Pannello Note (collassabile) -->
    <div id="modal-notes-panel" class="hidden" style="padding: 12px 28px; background: rgba(96,165,250,0.04); border-bottom: 0.5px solid var(--border);">
      <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
        <span style="font-size: 11px; color: var(--info); text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600;">📝 ${currentLang==="it"?"Note giocatore":"Player notes"}</span>
        <span class="ml-auto text-[10px]" style="color: var(--text-3);">${currentLang==="it"?"Salvate localmente":"Saved locally"}</span>
      </div>
      <textarea id="modal-notes-text" rows="4"
                placeholder="${currentLang==="it"?"Scrivi qui le tue note (caratteristiche, valutazioni, comportamento, ecc.)...":"Write your notes here (traits, ratings, behavior, etc.)..."}"
                style="width: 100%; outline: none; padding: 10px 12px; border-radius: 8px; background: var(--surface-2); border: 0.5px solid var(--border); color: var(--text-1); font-size: 13px; font-family: inherit; resize: vertical; min-height: 80px;">${escapeHtml((state.playerNotes && state.playerNotes[pid]) || "")}</textarea>
      <div style="display: flex; gap: 8px; margin-top: 8px;">
        <button id="modal-notes-save" class="px-3 py-1.5 text-xs font-semibold rounded-md" style="background: var(--accent); color: #0E1116;">${currentLang==="it"?"Salva":"Save"}</button>
        <button id="modal-notes-clear" class="px-3 py-1.5 text-xs rounded-md" style="background: rgba(239,68,68,0.10); color: #EF4444; border: 0.5px solid rgba(239,68,68,0.20);">${currentLang==="it"?"Elimina":"Delete"}</button>
        <span id="modal-notes-status" class="ml-2 text-xs self-center" style="color: var(--text-3);"></span>
      </div>
    </div>

    <div id="modal-season-block" style="padding: 16px 28px; background: rgba(255,255,255,0.02); border-bottom: 0.5px solid var(--border);">
      <!-- Riempito dinamicamente da renderSeasonBlock() -->
    </div>
    <div id="modal-last-match" style="padding: 12px 28px; background: rgba(96,165,250,0.04); border-bottom: 0.5px solid var(--border);">
      <!-- Riempito dinamicamente con ultima partita + minuti 30gg -->
    </div>

    <div style="padding: 22px 28px;">
      ${(clubBlocks || hasU21Current) ? `
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 14px; flex-wrap: wrap;">
          <div style="width: 3px; height: 14px; background: var(--accent); border-radius: 2px;"></div>
          <span style="font-size: 13px; font-weight: 500; color: var(--text-1); text-transform: uppercase; letter-spacing: 0.06em;">${t("club_stats")}</span>
          <div id="modal-club-stats-filter" class="flex flex-wrap gap-1 ml-auto"></div>
        </div>
        ${tableHeader}
        <div id="modal-club-blocks">${clubBlocks}</div>
      ` : ""}

      ${natBlock && (clubBlocks || hasU21Current) ? `<div style="height: 1px; background: var(--border-strong); margin: 24px 0;"></div>` : ""}

      ${natBlock ? `
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 14px; flex-wrap: wrap;">
          <div style="width: 3px; height: 14px; background: var(--comp-nat); border-radius: 2px;"></div>
          <span style="font-size: 13px; font-weight: 500; color: var(--text-1); text-transform: uppercase; letter-spacing: 0.06em;">${t("national_stats")}</span>
          <div id="modal-nat-stats-filter" class="flex flex-wrap gap-1 ml-auto"></div>
        </div>
        ${tableHeader}
        <div id="modal-nat-blocks">${natBlock}</div>
      ` : ""}

      ${!clubBlocks && !natBlock ? `<div style="color: var(--text-3); font-size: 14px;">${t("no_data")}</div>` : ""}

      ${renderNationalCareer(stats)}
      ${renderCareerByCompetition(stats)}
      ${renderRecentMatches(stats)}
      ${renderMonthlyChart(stats)}

      <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 22px; padding-top: 16px; border-top: 0.5px solid var(--border);">
        ${p.tm_profile_url ? `<a href="${p.tm_profile_url}" target="_blank" rel="noopener" style="font-size: 11px; padding: 5px 11px; border-radius: 8px; background: rgba(255,255,255,0.05); color: var(--text-2); text-decoration: none; border: 0.5px solid var(--border);">Transfermarkt ↗</a>` : ""}
        ${p.sortitoutsi_profile_url ? `<a href="${p.sortitoutsi_profile_url}" target="_blank" rel="noopener" style="font-size: 11px; padding: 5px 11px; border-radius: 8px; background: rgba(255,255,255,0.05); color: var(--text-2); text-decoration: none; border: 0.5px solid var(--border);">sortitoutsi ↗</a>` : ""}
        ${p.date_of_birth ? `<span style="font-size: 11px; padding: 5px 11px; border-radius: 8px; background: transparent; color: var(--text-3);">${escapeHtml(p.date_of_birth)}${p.place_of_birth ? " · " + escapeHtml(p.place_of_birth) : ""}</span>` : ""}
      </div>
    </div>`;
  document.getElementById("player-modal-content").innerHTML = html;
  const modal = document.getElementById("player-modal");
  modal.classList.remove("hidden");
  document.getElementById("modal-close").addEventListener("click", closeModal);

  // ---- Monthly chart: filtri stagione + click sulle barre per drill-down ----
  const _wireMonthlyChart = () => {
    document.querySelectorAll(".month-chart-season-btn").forEach(b => b.addEventListener("click", () => {
      state.monthChart.season = b.dataset.season;
      state.monthChart.month = null; // reset drill-down al cambio stagione
      openPlayerModal(pid); // re-render
    }));
    document.querySelectorAll("#monthly-chart-block .chart-bar-group").forEach(g => g.addEventListener("click", () => {
      const k = g.dataset.month;
      if (!k) return;
      // Toggle drill-down: stesso mese → chiudi
      state.monthChart.month = state.monthChart.month === k ? null : k;
      openPlayerModal(pid);
    }));
    document.getElementById("month-chart-close")?.addEventListener("click", () => {
      state.monthChart.month = null;
      openPlayerModal(pid);
    });
  };
  setTimeout(_wireMonthlyChart, 0);

  // ---- + Convoca / − Rimuovi convocazione ----
  state.playerNotes = state.playerNotes || JSON.parse(localStorage.getItem("pid_player_notes") || "{}");
  document.getElementById("callup-add-from-modal")?.addEventListener("click", () => {
    if (!state.callup.currentIds.includes(pid)) {
      state.callup.currentIds.push(pid);
    } else {
      state.callup.currentIds = state.callup.currentIds.filter(x => x !== pid);
    }
    if (typeof _saveCallup === "function") _saveCallup();
    else localStorage.setItem("pid_callup_active", JSON.stringify(state.callup.currentIds || []));
    // Riapri modal per riflettere stato del bottone
    openPlayerModal(pid);
    if (typeof renderCallupPanel === "function") renderCallupPanel();
  });

  // ---- Note giocatore: AUTO-SAVE persistente in localStorage (resta finché non cancelli) ----
  const notesPanel = document.getElementById("modal-notes-panel");
  const notesText = document.getElementById("modal-notes-text");
  document.getElementById("modal-notes-toggle")?.addEventListener("click", () => {
    notesPanel.classList.toggle("hidden");
    if (!notesPanel.classList.contains("hidden")) {
      setTimeout(() => notesText?.focus(), 50);
    }
  });
  // Auto-save su ogni keystroke (con piccolo debounce per non saturare localStorage)
  let _notesSaveTimer = null;
  const persistNote = () => {
    const text = (notesText.value || "").trim();
    if (text) state.playerNotes[pid] = text;
    else delete state.playerNotes[pid];
    localStorage.setItem("pid_player_notes", JSON.stringify(state.playerNotes));
    const status = document.getElementById("modal-notes-status");
    if (status) {
      status.textContent = currentLang === "it" ? "✓ Salvato automaticamente" : "✓ Auto-saved";
      status.style.color = "var(--accent)";
      clearTimeout(_notesSaveTimer);
      _notesSaveTimer = setTimeout(() => { if (status) status.textContent = ""; }, 1500);
    }
    const toggle = document.getElementById("modal-notes-toggle");
    if (toggle) toggle.innerHTML = `📝 ${currentLang==="it"?"Note":"Notes"}${text ? ` <span class="stat-cell" style="color: var(--accent); font-size: 9px;">●</span>` : ""}`;
  };
  let _notesDebounce = null;
  notesText?.addEventListener("input", () => {
    clearTimeout(_notesDebounce);
    _notesDebounce = setTimeout(persistNote, 350);
  });
  // Salva subito anche se l'utente perde focus o chiude il modal
  notesText?.addEventListener("blur", persistNote);
  // Bottone Salva (opzionale, per esplicita conferma immediata)
  document.getElementById("modal-notes-save")?.addEventListener("click", () => {
    clearTimeout(_notesDebounce);
    persistNote();
  });
  document.getElementById("modal-notes-clear")?.addEventListener("click", () => {
    if (!confirm(currentLang==="it"?"Eliminare le note di questo giocatore?":"Delete this player's notes?")) return;
    delete state.playerNotes[pid];
    localStorage.setItem("pid_player_notes", JSON.stringify(state.playerNotes));
    if (notesText) notesText.value = "";
    const status = document.getElementById("modal-notes-status");
    if (status) { status.textContent = currentLang==="it"?"Eliminate":"Deleted"; status.style.color="#EF4444"; setTimeout(()=>{status.textContent="";}, 2000); }
    const toggle = document.getElementById("modal-notes-toggle");
    if (toggle) toggle.innerHTML = `📝 ${currentLang==="it"?"Note":"Notes"}`;
  });

  // ---- Season block (4 stat box, sempre 2025/26 — non filtrabile qui) ----
  const renderSeasonBlock = () => {
    const sd = seasons[currentKey] || { club: {}, national: {} };
    const c = sumSeason(sd.club);
    const n = sumSeason(sd.national);
    // Aggrega le partite U21 (Excel) della stagione corrente (luglio 2025 → giugno 2026)
    const u21 = (() => {
      const list = pid != null ? _u21MatchesNormalized(pid) : [];
      let apps = 0, minutes = 0;
      for (const m of list) {
        const ds = (m.date || "").slice(0, 10); if (!ds) continue;
        const [y, mo] = ds.split("-").map(Number);
        if ((y === 2025 && mo >= 7) || (y === 2026 && mo <= 6)) {
          apps += 1;
          minutes += (m.minutes || 0);
        }
      }
      return { apps, minutes };
    })();
    const tot = {
      apps: c.apps + n.apps + u21.apps,
      goals: c.goals + n.goals,
      assists: c.assists + n.assists,
      minutes: c.minutes + n.minutes + u21.minutes,
    };
    const block = document.getElementById("modal-season-block");
    // Mostra il messaggio "Nessuna partita" solo se NÉ TM NÉ U21 hanno dati per la stagione
    if (!currentSeasonHasData && u21.apps === 0) {
      block.innerHTML = `
        <div style="font-size: 11px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 10px; font-weight: 500;">${t("current_season")} — ${t("season_label", currentKey)}</div>
        <div style="padding: 22px; text-align: center; border: 0.5px dashed var(--border-strong); border-radius: 10px; background: rgba(255,255,255,0.02);">
          <div style="font-size: 14px; color: var(--text-2); font-weight: 500;">${currentLang==="it"?"Nessuna partita":"No matches played"}</div>
          <div style="font-size: 11px; color: var(--text-3); margin-top: 4px;">${t("season_label", currentKey)}</div>
        </div>`;
      return;
    }
    block.innerHTML = `
      <div style="font-size: 11px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 10px; font-weight: 500;">${t("current_season")} — ${t("season_label", currentKey)}</div>
      <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;">
        <div style="text-align: center;"><div class="stat-cell" style="font-size: 28px; font-weight: 500; color: var(--text-1); line-height: 1;">${tot.apps}</div><div style="font-size: 10px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.08em; margin-top: 4px;">${t("apps")}</div></div>
        <div style="text-align: center;"><div class="stat-cell" style="font-size: 28px; font-weight: 500; color: ${tot.goals>=5?"var(--hot)":"var(--text-1)"}; line-height: 1;">${tot.goals}</div><div style="font-size: 10px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.08em; margin-top: 4px;">${t("goals")}</div></div>
        <div style="text-align: center;"><div class="stat-cell" style="font-size: 28px; font-weight: 500; color: ${tot.assists>=5?"var(--hot)":"var(--text-1)"}; line-height: 1;">${tot.assists}</div><div style="font-size: 10px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.08em; margin-top: 4px;">${t("assists")}</div></div>
        <div style="text-align: center;"><div class="stat-cell" style="font-size: 28px; font-weight: 500; color: var(--text-1); line-height: 1;">${tot.minutes}</div><div style="font-size: 10px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.08em; margin-top: 4px;">${t("minutes_short")}</div></div>
      </div>`;
  };
  renderSeasonBlock();

  // ---- Filtro stagione SU STATISTICHE CLUB (default: 2025/26 sempre) ----
  if (!state.modalSeasonFilter || (state.modalSeasonFilter !== "all" && state.modalSeasonFilter !== currentKey && !seasonKeys.includes(state.modalSeasonFilter))) {
    state.modalSeasonFilter = currentKey;
  }
  const renderClubStatsFilter = () => {
    const filterEl = document.getElementById("modal-club-stats-filter");
    if (!filterEl) return;
    // currentKey "2025" sempre presente come opzione anche se il giocatore non ha dati per questa stagione
    const allKeys = ["all", currentKey, ...seasonKeys.filter(k => k !== currentKey)];
    filterEl.innerHTML = allKeys.map(k => {
      const sel = state.modalSeasonFilter === k;
      const label = k === "all" ? (currentLang === "it" ? "Tutte" : "All") : t("season_label", k);
      return `<button class="modal-season-btn px-2.5 py-1 text-[11px] rounded-md font-semibold" data-key="${k}"
              style="background: ${sel?'var(--accent-bg)':'rgba(255,255,255,0.04)'}; color: ${sel?'var(--accent)':'var(--text-2)'}; border: 0.5px solid ${sel?'rgba(111,224,168,0.30)':'var(--border)'};">${label}</button>`;
    }).join("");
    filterEl.querySelectorAll(".modal-season-btn").forEach(b => b.addEventListener("click", () => {
      state.modalSeasonFilter = b.dataset.key;
      // Re-render dei blocchi club per applicare il filtro
      renderClubBlocksFiltered();
      renderClubStatsFilter();
    }));
  };
  // Aggrega le partite U21 dell'Excel per stagione (luglio→giugno)
  const _u21BySeason = (() => {
    const out = new Map();
    if (pid == null) return out;
    for (const m of _u21MatchesNormalized(pid)) {
      const ds = (m.date || "").slice(0, 10); if (!ds) continue;
      const [y, mo] = ds.split("-").map(Number);
      const seasonKey = String(mo >= 7 ? y : y - 1);
      if (!out.has(seasonKey)) out.set(seasonKey, { apps: 0, minutes: 0 });
      const e = out.get(seasonKey);
      e.apps += 1;
      e.minutes += (m.minutes || 0);
    }
    return out;
  })();

  // Ricostruisce i blocchi club applicando il filtro
  const renderClubBlocksFiltered = () => {
    const cont = document.getElementById("modal-club-blocks");
    if (!cont) return;
    const filter = state.modalSeasonFilter || currentKey;
    // Stagioni TM + stagioni con SOLO partite U21 (non presenti in seasons[]).
    let filteredKeys;
    if (filter === "all") {
      filteredKeys = [...new Set([...seasonKeys, ..._u21BySeason.keys()])].sort().reverse();
    } else {
      filteredKeys = seasonKeys.includes(filter) || _u21BySeason.has(filter) ? [filter] : [];
    }
    const blocks = filteredKeys.map(season => {
      const rows = Object.entries(seasons[season]?.club || {});

      if (!rows.length) return null;
      return `
        <div>
          <div style="font-size: 11px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.08em; font-weight: 500; margin-bottom: 6px; padding: 0 4px;">${t("season_label", season)}</div>
          <div style="background: rgba(255,255,255,0.03); border-radius: 10px; overflow: hidden;">
            ${rows.map(([code, s]) => renderRow(code, s, { isNational: false })).join("")}
          </div>
        </div>`;
    }).filter(Boolean);
    cont.innerHTML = blocks.join(`<div style="height: 1px; background: var(--border-strong); margin: 18px 0;"></div>`)
      || `<div style="padding: 22px; text-align: center; border: 0.5px dashed var(--border-strong); border-radius: 10px; background: rgba(255,255,255,0.02); color: var(--text-2); font-size: 13px;">${currentLang==="it"?"Nessuna partita":"No matches played"}<div style="font-size: 11px; color: var(--text-3); margin-top: 4px;">${filter === "all" ? "" : t("season_label", filter)}</div></div>`;
  };
  setTimeout(() => { renderClubStatsFilter(); renderClubBlocksFiltered(); }, 0);

  // ---- Filtro stagione SU STATISTICHE NAZIONALE (default: 2025/26 sempre) ----
  if (!state.modalNatSeasonFilter || (state.modalNatSeasonFilter !== "all" && state.modalNatSeasonFilter !== currentKey && !seasonKeys.includes(state.modalNatSeasonFilter))) {
    state.modalNatSeasonFilter = currentKey;
  }
  const renderNatStatsFilter = () => {
    const filterEl = document.getElementById("modal-nat-stats-filter");
    if (!filterEl) return;
    const allKeys = ["all", currentKey, ...seasonKeys.filter(k => k !== currentKey)];
    filterEl.innerHTML = allKeys.map(k => {
      const sel = state.modalNatSeasonFilter === k;
      const label = k === "all" ? (currentLang === "it" ? "Tutte" : "All") : t("season_label", k);
      return `<button class="modal-nat-season-btn px-2.5 py-1 text-[11px] rounded-md font-semibold" data-key="${k}"
              style="background: ${sel?'rgba(244,114,182,0.15)':'rgba(255,255,255,0.04)'}; color: ${sel?'var(--comp-nat)':'var(--text-2)'}; border: 0.5px solid ${sel?'rgba(244,114,182,0.30)':'var(--border)'};">${label}</button>`;
    }).join("");
    filterEl.querySelectorAll(".modal-nat-season-btn").forEach(b => b.addEventListener("click", () => {
      state.modalNatSeasonFilter = b.dataset.key;
      renderNatBlocksFiltered();
      renderNatStatsFilter();
    }));
  };
  const renderNatBlocksFiltered = () => {
    const cont = document.getElementById("modal-nat-blocks");
    if (!cont) return;
    const filter = state.modalNatSeasonFilter || currentKey;
    const filteredKeys = filter === "all" ? seasonKeys : seasonKeys.filter(k => k === filter);
    const rows = filteredKeys.flatMap(season =>
      Object.entries(seasons[season]?.national || {}).map(([code, s]) => ({ code, s, season }))
    );
    if (!rows.length) {
      cont.innerHTML = `<div style="padding: 22px; text-align: center; border: 0.5px dashed var(--border-strong); border-radius: 10px; background: rgba(255,255,255,0.02); color: var(--text-2); font-size: 13px;">${currentLang==="it"?"Nessuna partita":"No matches played"}<div style="font-size: 11px; color: var(--text-3); margin-top: 4px;">${filter === "all" ? "" : t("season_label", filter)}</div></div>`;
      return;
    }
    cont.innerHTML = `<div style="background: rgba(255,255,255,0.03); border-radius: 10px; overflow: hidden;">
      ${rows.map(({ code, s, season }) => renderRow(code, s, { isNational: true, seasonPrefix: t("season_label", season).slice(-5), dim: false })).join("")}
    </div>`;
  };
  setTimeout(() => { renderNatStatsFilter(); renderNatBlocksFiltered(); }, 0);

  // ---- Ultima partita + minuti 30 giorni ----
  const renderLastMatchBlock = () => {
    const list = stats?.recent_matches;
    const block = document.getElementById("modal-last-match");
    if (!Array.isArray(list) || !list.length) { block.style.display = "none"; return; }
    // ordina per data discendente
    const parseDate = (m) => {
      let raw = m.date;
      if (raw && typeof raw === "object") raw = raw.dateTimeUTC || raw.dateTimeLocalized;
      const d = new Date(typeof raw === "number" ? raw : Date.parse(raw));
      return isNaN(d.getTime()) ? null : d;
    };
    const sorted = list.map(m => ({ m, d: parseDate(m) })).filter(x => x.d).sort((a,b) => b.d - a.d);
    if (!sorted.length) { block.style.display = "none"; return; }
    const last = sorted[0];
    const lastDateStr = last.d.toLocaleDateString(currentLang === "it" ? "it-IT" : "en-GB", { day: "2-digit", month: "2-digit", year: "numeric" });
    // opponent
    const oppC = state.clubsById.get(last.m.opponent_club_id);
    let oppName = oppC ? oppC.name : null;
    if (!oppName) {
      const cid = last.m.opponent_club_id != null ? String(last.m.opponent_club_id) : null;
      if (cid && state.opponentNames && state.opponentNames[cid]) oppName = state.opponentNames[cid];
    }
    if (!oppName && last.m.is_national && last.m.competition_name) {
      oppName = currentLang === "it" ? `Nazionale · ${last.m.competition_name}` : `National · ${last.m.competition_name}`;
    }
    if (!oppName) oppName = "—";
    const score = (last.m.result_for != null && last.m.result_against != null) ? `${last.m.result_for}-${last.m.result_against}` : "";
    const lastMins = last.m.minutes || 0;
    const venueStr = last.m.venue === "home" ? (currentLang==="it"?"Casa":"Home") : (last.m.venue === "away" ? (currentLang==="it"?"Trasferta":"Away") : "");
    // minuti negli ultimi 30 giorni
    const now = new Date();
    const thirtyAgo = new Date(now.getTime() - 30*24*60*60*1000);
    const minutes30d = sorted.filter(x => x.d >= thirtyAgo).reduce((a, x) => a + (x.m.minutes || 0), 0);
    const matches30d = sorted.filter(x => x.d >= thirtyAgo).length;

    block.innerHTML = `
      <div style="display: flex; align-items: center; gap: 16px; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 200px;">
          <div style="font-size: 10px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px;">${currentLang==="it"?"Ultima partita giocata":"Last match played"}</div>
          <div style="font-size: 14px; color: var(--text-1); font-weight: 500;">
            <span class="stat-cell" style="color: var(--info);">${lastDateStr}</span>
            <span style="margin: 0 6px; color: var(--text-3);">·</span>
            <span>vs ${escapeHtml(oppName)}</span>
            ${score ? `<span class="stat-cell" style="margin-left: 8px; padding: 2px 8px; background: rgba(255,255,255,0.06); border-radius: 6px; font-size: 12px;">${score}</span>` : ""}
            ${venueStr ? `<span style="margin-left: 8px; font-size: 11px; color: var(--text-3);">${venueStr}</span>` : ""}
            <span style="margin-left: 8px; font-size: 12px; color: var(--text-3);">${lastMins}'</span>
          </div>
        </div>
        <div style="text-align: right;">
          <div style="font-size: 10px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px;">${currentLang==="it"?"Minuti ultimi 30 giorni":"Minutes last 30 days"}</div>
          <div class="stat-cell" style="font-size: 22px; font-weight: 500; color: ${minutes30d>0?'var(--accent)':'var(--text-3)'}; line-height: 1;">${minutes30d}'</div>
          <div style="font-size: 10px; color: var(--text-3); margin-top: 2px;">${matches30d} ${currentLang==="it"?(matches30d===1?"partita":"partite"):(matches30d===1?"match":"matches")}</div>
        </div>
      </div>`;
  };
  renderLastMatchBlock();
  document.getElementById("compare-toggle").addEventListener("click", () => {
    if (inCompare) state.compareIds[compareIdx] = null;
    else {
      const slot = state.compareIds.indexOf(null);
      if (slot >= 0) state.compareIds[slot] = pid;
    }
    closeModal();
    setActiveTab("compare");
    renderCompare();
  });
  document.getElementById("modal-fav-toggle")?.addEventListener("click", () => {
    toggleFavorite(pid);
    // Re-render del modal per aggiornare lo stato del bottone (sempre con stesso pid)
    openPlayerModal(pid);
    // Refresh la home grid e il pannello favoriti per riflettere lo stato della stella
    if (state.activeTab === "home") applyFilters();
    else if (state.activeTab === "favorites") renderFavoritesPanel();
  });
  // Click sull'overlay (fuori dalla card) chiude la scheda
  modal.onclick = (e) => { if (e.target === modal) closeModal(); };
  // ESC chiude
  if (!window._modalKeyBound) {
    window._modalKeyBound = true;
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !document.getElementById("player-modal").classList.contains("hidden")) {
        closeModal();
      }
    });
  }
}

function closeModal() {
  document.getElementById("player-modal").classList.add("hidden");
}

// ============ WYSCOUT (dark) ============
function renderWyscoutStats(wy, positionGeneral) {
  const isGK = (positionGeneral || "").toLowerCase() === "goalkeeper";
  const tile = (label, value, sub) => `<div class="p-3 rounded-lg" style="background: var(--surface-2); border: 0.5px solid var(--border);">
    <div class="text-[10px] uppercase tracking-wider" style="color: var(--text-3);">${label}</div>
    <div class="text-lg font-semibold stat-cell mt-0.5" style="color: var(--text-1);">${value}</div>
    ${sub ? `<div class="text-[10px] stat-cell mt-0.5" style="color: var(--accent);">${sub}</div>` : ""}
  </div>`;

  const bar = (label, value, color) => {
    const pct = Number(value) || 0;
    const c = pct >= 60 ? "var(--accent)" : pct >= 40 ? "var(--hot)" : "#FB923C";
    return `<div class="grid items-center gap-2.5" style="grid-template-columns: 110px 1fr 36px;">
      <span class="text-[11px]" style="color: var(--text-2);">${label}</span>
      <div class="h-1.5 rounded-full overflow-hidden" style="background: rgba(255,255,255,0.05);">
        <div class="h-full rounded-full" style="width:${Math.min(pct,100)}%; background:${c};"></div>
      </div>
      <span class="text-[11px] font-medium stat-cell text-right" style="color: var(--text-1);">${fmtPct(pct)}</span>
    </div>`;
  };

  let topTiles, bars;
  if (isGK) {
    topTiles = [
      tile("Clean sheets", fmtInt(wy.wyscout_clean_sheets)),
      tile("Conceded", fmtInt(wy.wyscout_conceded), `${fmtNum(wy.conceded_p90)} /90`),
      tile("xG against", fmtNum(wy.xg_against_total), `${fmtNum(wy.xg_against_p90)} /90`),
      tile("Prevented", fmtNum(wy.prevented_goals_total), `${fmtNum(wy.prevented_goals_p90)} /90`),
    ].join("");
    bars = [
      bar("Save rate", wy.save_rate_pct),
    ].join("");
  } else {
    topTiles = [
      tile("xG", fmtNum(wy.xg_total), `${fmtNum(wy.xg_p90)} /90`),
      tile("xA", fmtNum(wy.xa_total), `${fmtNum(wy.xa_p90)} /90`),
      tile("Goal conv.", fmtPct(wy.goal_conversion_pct), `${fmtNum(wy.shots_p90)} sh /90`),
      tile("Touches box", fmtNum(wy.touches_in_box_p90), "/ 90"),
    ].join("");
    bars = [
      bar("Duels won", wy.duels_won_pct),
      bar("Off. duels won", wy.off_duels_won_pct),
      bar("Dribble succ.", wy.dribbles_success_pct),
      bar("Pass accuracy", wy.passes_accuracy_pct),
      bar("Cross accuracy", wy.crosses_accuracy_pct),
    ].join("");
  }

  const youthBadge = (() => {
    const t = wy.wyscout_team || "";
    const m = t.match(/U(\d{2})/i);
    return m ? `<span class="ml-2 px-1.5 py-0.5 text-[10px] rounded" style="background: rgba(251,191,36,0.18); color: var(--hot);">${m[0]}</span>` : "";
  })();

  return `
    <div class="mt-5 pt-4" style="border-top: 0.5px solid var(--border);">
      <div class="flex items-center gap-2 mb-3">
        <span class="text-xs uppercase tracking-wider font-medium" style="color: var(--text-2);">${currentLang === "it" ? "Statistiche avanzate" : "Advanced stats"}</span>
        <span class="text-[9px] px-1.5 py-0.5 rounded uppercase tracking-wider font-medium" style="background: rgba(96,165,250,0.18); color: #93C5FD;">Wyscout</span>
        ${youthBadge}
      </div>
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3">${topTiles}</div>
      <div class="space-y-1.5">${bars}</div>
    </div>`;
}

// ============ CAREER SECTION (Club + Nazionale, 2 box affiancati) ============
function _renderClubCareerBox(stats) {
  const club = stats?.career_by_competition?.club || {};
  const pid = stats?.tm_player_id;
  // Aggrega AFC Champions League (AFCL) + AFC Champions League Elite (ACLE) sotto un'unica voce.
  // ES1 (AFC Champions League 2) resta separato. Rimuove KLUB (Club Friendly).
  const merged = {};
  for (const [code, s] of Object.entries(club)) {
    if (CLUB_EXCLUDE.has(code)) continue; // KLUB / FIC1 / ARCP / PLIC filtrate
    let outCode = code;
    if (code === "AFCL" || code === "ACLE") outCode = "ACLE";
    if (code === "BPO4" || code === "POBE") outCode = "BE1";
    if (!merged[outCode]) {
      merged[outCode] = {
        ...s,
        competition_name: _compName(outCode, s.competition_name),
      };
    } else {
      merged[outCode].apps = (merged[outCode].apps||0) + (s.apps||0);
      merged[outCode].goals = (merged[outCode].goals||0) + (s.goals||0);
      merged[outCode].assists = (merged[outCode].assists||0) + (s.assists||0);
      merged[outCode].yellow_cards = (merged[outCode].yellow_cards||0) + (s.yellow_cards||0);
      merged[outCode].red_cards = (merged[outCode].red_cards||0) + (s.red_cards||0);
      merged[outCode].minutes_played = (merged[outCode].minutes_played||0) + (s.minutes_played||0);
    }
  }
  // Aggiungi voce Saudi U21 Elite League dall'Excel (all-time)
  const u21List = pid != null ? _u21MatchesNormalized(pid) : [];
  if (u21List.length) {
    const apps = u21List.length;
    const minutes = u21List.reduce((a, m) => a + (m.minutes || 0), 0);

  }
  if (!Object.keys(merged).length) return "";
  const sorted = Object.entries(merged).sort((a, b) => (b[1].apps||0) - (a[1].apps||0));
  // Grid identica alla tabella stats stagione (1fr 38px 38px 38px 64px) per coerenza visiva
  const GRID_TPL = "1fr 38px 38px 38px 64px";
  const rows = sorted.map(([code, s]) => {
    const logo = competitionLogo(code);
    const goalsHot = (s.goals||0) >= 5;
    const assistsHot = (s.assists||0) >= 5;
    return `
      <div style="display: grid; grid-template-columns: ${GRID_TPL}; gap: 12px; align-items: center; padding: 8px 12px; border-bottom: 0.5px solid var(--border);">
        <div style="display: flex; align-items: center; gap: 8px; min-width: 0;">
          ${logo ? `<img src="${logo}" style="width: 20px; height: 20px; object-fit: contain; flex-shrink: 0;"/>` : `<span style="width: 3px; height: 14px; background: var(--text-3); border-radius: 2px; flex-shrink: 0;"></span>`}
          <span class="truncate" style="font-size: 13px; color: var(--text-1);">${escapeHtml(_compName(code, s.competition_name))}</span>
        </div>
        <span class="stat-cell" style="font-size: 14px; font-weight: 600; color: ${s.apps?"var(--text-1)":"var(--text-3)"}; text-align: center; font-variant-numeric: tabular-nums;">${s.apps||0}</span>
        <span class="stat-cell" style="font-size: 14px; font-weight: 600; color: ${goalsHot?"var(--hot)":(s.goals?"var(--text-1)":"var(--text-3)")}; text-align: center; font-variant-numeric: tabular-nums;">${s.goals||0}</span>
        <span class="stat-cell" style="font-size: 14px; font-weight: 600; color: ${assistsHot?"var(--hot)":(s.assists?"var(--text-1)":"var(--text-3)")}; text-align: center; font-variant-numeric: tabular-nums;">${s.assists||0}</span>
        <span class="stat-cell" style="font-size: 13px; font-weight: 700; color: ${s.minutes_played?"var(--accent)":"var(--text-3)"}; text-align: right; font-variant-numeric: tabular-nums; padding: 2px 6px; border-radius: 4px; background: ${s.minutes_played?"rgba(111,224,168,0.08)":"transparent"};">${s.minutes_played?(s.minutes_played+"'"):"0'"}</span>
      </div>`;
  }).join("");
  return `
    <div style="background: rgba(111,224,168,0.04); border: 0.5px solid rgba(111,224,168,0.20); border-radius: 12px; padding: 14px 14px 4px;">
      <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
        <div style="width: 3px; height: 14px; background: var(--accent); border-radius: 2px;"></div>
        <span style="font-size: 12px; font-weight: 600; color: var(--text-1); text-transform: uppercase; letter-spacing: 0.06em;">${t("career_by_competition")}</span>
        <span style="font-size: 9px; color: var(--text-3); margin-left: auto;">all-time · club</span>
      </div>
      <div style="display: grid; grid-template-columns: ${GRID_TPL}; gap: 12px; align-items: center; padding: 4px 12px 8px;">
        <span></span>
        <span class="stat-cell" style="font-size: 10px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.06em; text-align: center; font-weight: 600;">${t("apps")}</span>
        <span class="stat-cell" style="font-size: 10px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.06em; text-align: center; font-weight: 600;">${t("goals")}</span>
        <span class="stat-cell" style="font-size: 10px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.06em; text-align: center; font-weight: 600;">${t("assists")}</span>
        <span class="stat-cell" style="font-size: 10px; color: var(--accent); text-transform: uppercase; letter-spacing: 0.06em; text-align: right; font-weight: 700;">${t("col_min")}</span>
      </div>
      <div>${rows}</div>
    </div>`;
}

function _renderNationalCareerBox(stats) {
  const list = stats?.national_career;
  if (!Array.isArray(list) || !list.length) return "";
  const flagUrl = _photoUrl("photos/branding/logo.png");
  // Ordinamento gerarchico fisso: A → U23 → U22 → U21 → U20 → U19 → U18 → U17 → U16 → U15 → Olympic → altre
  const CAT_ORDER = { "A": 0, "U23": 1, "U22": 2, "U21": 3, "U20": 4, "U19": 5, "U18": 6, "U17": 7, "U16": 8, "U15": 9, "Olympic": 10 };
  const sorted = [...list].sort((a, b) => {
    const ra = CAT_ORDER[a.category] ?? 99;
    const rb = CAT_ORDER[b.category] ?? 99;
    if (ra !== rb) return ra - rb;
    return (b.caps || 0) - (a.caps || 0);  // tie-breaker: più caps prima
  });
  // Grid identica alla tabella stats nazionale (1fr 38px 38px 64px) — no colonna assist
  const GRID_TPL = "1fr 38px 38px 64px";
  const rows = sorted.map(nt => {
    const goalsHot = (nt.goals||0) >= 5;
    return `
    <div style="display: grid; grid-template-columns: ${GRID_TPL}; gap: 12px; align-items: center; padding: 8px 12px; border-bottom: 0.5px solid var(--border);">
      <div style="display: flex; align-items: center; gap: 8px; min-width: 0;">
        ${flagUrl ? `<img src="${flagUrl}" style="width: 20px; height: 20px; object-fit: cover; border-radius: 3px; flex-shrink: 0;"/>` : ""}
        <span class="truncate" style="font-size: 13px; color: var(--text-1); font-weight: 500;">${escapeHtml(nt.team_name)}</span>
      </div>
      <span class="stat-cell" style="font-size: 14px; font-weight: 600; color: ${nt.caps?"var(--text-1)":"var(--text-3)"}; text-align: center; font-variant-numeric: tabular-nums;">${nt.caps||0}</span>
      <span class="stat-cell" style="font-size: 14px; font-weight: 600; color: ${goalsHot?"var(--hot)":(nt.goals?"var(--text-1)":"var(--text-3)")}; text-align: center; font-variant-numeric: tabular-nums;">${nt.goals||0}</span>
      <span class="stat-cell" style="font-size: 13px; font-weight: 700; color: ${nt.minutes?"var(--accent)":"var(--text-3)"}; text-align: right; font-variant-numeric: tabular-nums; padding: 2px 6px; border-radius: 4px; background: ${nt.minutes?"rgba(111,224,168,0.08)":"transparent"};">${nt.minutes?(nt.minutes+"'"):"0'"}</span>
    </div>`;
  }).join("");
  return `
    <div style="background: rgba(244,114,182,0.04); border: 0.5px solid rgba(244,114,182,0.20); border-radius: 12px; padding: 14px 14px 4px;">
      <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
        <div style="width: 3px; height: 14px; background: var(--comp-nat); border-radius: 2px;"></div>
        <span style="font-size: 12px; font-weight: 600; color: var(--text-1); text-transform: uppercase; letter-spacing: 0.06em;">${t("national_career")}</span>
        <span style="font-size: 9px; color: var(--text-3); margin-left: auto;">all-time</span>
      </div>
      <div style="display: grid; grid-template-columns: ${GRID_TPL}; gap: 12px; align-items: center; padding: 4px 12px 8px;">
        <span></span>
        <span class="stat-cell" style="font-size: 10px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.06em; text-align: center; font-weight: 600;">${t("caps")}</span>
        <span class="stat-cell" style="font-size: 10px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.06em; text-align: center; font-weight: 600;">${t("goals")}</span>
        <span class="stat-cell" style="font-size: 10px; color: var(--accent); text-transform: uppercase; letter-spacing: 0.06em; text-align: right; font-weight: 700;">${t("col_min")}</span>
      </div>
      <div>${rows}</div>
    </div>`;
}

function renderCareerByCompetition(stats) {
  // Adesso questa funzione ritorna i 2 box affiancati (club a sinistra, nazionale a destra)
  const clubBox = _renderClubCareerBox(stats);
  const natBox = _renderNationalCareerBox(stats);
  if (!clubBox && !natBox) return "";
  return `
    <div style="height: 1px; background: var(--border-strong); margin: 24px 0;"></div>
    <div style="display: grid; grid-template-columns: ${clubBox && natBox ? "1.4fr 1fr" : "1fr"}; gap: 14px;">
      ${clubBox || ""}
      ${natBox || ""}
    </div>`;
}

// Mantenuto come no-op per backward-compat (rimosso dalla cascata principale)
function renderNationalCareer(_stats) { return ""; }

// ============ MONTHLY CHART (histogram presenze/minuti per mese, luglio→giugno) ============
// Stato modale: stagione selezionata + mese aperto per il drill-down
state.monthChart = state.monthChart || { season: "2025", month: null }; // season: "2025" | "2024" | "all"

function _monthMeta(season) {
  // Ritorna i 12 mesi della stagione luglio→giugno con etichette i18n e periodo (year-month)
  // season "2025" → 2025-07 ... 2026-06
  // season "2024" → 2024-07 ... 2025-06
  const startYear = parseInt(season);
  const months = [];
  const labelKeys = ["month_jul","month_aug","month_sep","month_oct","month_nov","month_dec","month_jan","month_feb","month_mar","month_apr","month_may","month_jun"];
  for (let i = 0; i < 12; i++) {
    const offset = i + 6; // 6=luglio, 7=agosto, ..., 11=dicembre, 12=gennaio (anno+1)
    const year = startYear + (offset >= 12 ? 1 : 0);
    const month = (offset % 12) + 1; // 1-based
    months.push({
      key: `${year}-${String(month).padStart(2,"0")}`,
      label: t(labelKeys[i]),
    });
  }
  return months;
}

function _matchDateString(m) {
  let raw = m.date;
  if (raw && typeof raw === "object") raw = raw.dateTimeUTC || raw.dateTimeLocalized || raw.timestamp;
  if (!raw) return null;
  if (typeof raw === "number") {
    const dt = new Date(raw > 1e10 ? raw : raw * 1000);
    return isNaN(dt.getTime()) ? null : dt.toISOString().slice(0, 10);
  }
  if (typeof raw === "string") return raw.slice(0, 10);
  return null;
}

// Normalizza le partite U21 dell'Excel (build_u21_player_matches.py) in formato compatibile
// con `recent_matches` di Transfermarkt. Esclude i codici 'B', 'nc', 'nci', 'ncd' (non giocato).
function _u21MatchesNormalized(pid) {
  // PID: modulo U21 disattivato (era specifico Saudi U21 Excel).
  // Quando servirà un modulo Primavera 1 simile, ricostruire qui.
  return [];
}

// Restituisce recent_matches estesi con le partite U21 per il giocatore (deduplicate per data+opponent).
function _allMatchesForPlayer(stats, pid) {
  const tm = Array.isArray(stats?.recent_matches) ? stats.recent_matches : [];
  const u21 = pid != null ? _u21MatchesNormalized(pid) : [];
  if (!u21.length) return tm;
  // Dedupe sicura: TM non ha le partite U21 quindi unione semplice è sufficiente
  return [...tm, ...u21];
}

function renderMonthlyChart(stats) {
  const pid = stats?.tm_player_id;
  const list = _allMatchesForPlayer(stats, pid);
  if (!list.length) return "";

  let sel = state.monthChart.season || "2025";
  if (sel === "all") sel = "2025"; // fallback retrocompat
  const months = _monthMeta(sel);

  // Filtra le partite per stagione: usa SEMPRE la data per determinare la stagione (luglio-giugno).
  // Non usare m.season perché Transfermarkt a volte etichetta i tornei nella stagione "sbagliata"
  // (es. U20 World Cup ottobre 2025 → m.season=2024 invece di 2025)
  const inSeason = (m) => {
    const ds = _matchDateString(m);
    if (!ds) return false;
    const [y, mo] = ds.split("-").map(Number);
    const startYear = parseInt(sel);
    // luglio-dicembre di startYear OPPURE gennaio-giugno di startYear+1
    if (y === startYear && mo >= 7) return true;
    if (y === startYear + 1 && mo <= 6) return true;
    return false;
  };

  const filtered = list.filter(inSeason);

  // Aggrega per mese: somma minuti, presenze, gol, assist
  const byMonth = new Map();
  filtered.forEach(m => {
    const ds = _matchDateString(m);
    if (!ds) return;
    const ym = ds.slice(0, 7);
    if (!byMonth.has(ym)) byMonth.set(ym, { minutes: 0, apps: 0, goals: 0, assists: 0, matches: [] });
    const e = byMonth.get(ym);
    e.minutes += (m.minutes || 0);
    e.apps += 1;
    e.goals += (m.goals || 0);
    e.assists += (m.assists || 0);
    e.matches.push(m);
  });

  if (byMonth.size === 0) {
    // Suggerimento: se l'altra stagione ha dati, propongo lo switch con un bottone clic
    const altSeason = sel === "2025" ? "2024" : "2025";
    const altCount = list.filter(m => {
      const ds = _matchDateString(m); if (!ds) return false;
      const [y, mo] = ds.split("-").map(Number);
      const start = parseInt(altSeason);
      return (y === start && mo >= 7) || (y === start + 1 && mo <= 6);
    }).length;
    const suggestionBtn = altCount > 0 ? `
      <button class="month-chart-season-btn" data-season="${altSeason}"
              style="margin-top: 10px; padding: 6px 14px; border-radius: 8px; background: var(--accent-bg); color: var(--accent); border: 0.5px solid rgba(111,224,168,0.30); font-size: 12px; font-weight: 700; cursor: pointer;">
        → ${escapeHtml(t("season_label", altSeason))} (${altCount} ${currentLang==="it"?"partite":"matches"})
      </button>` : "";
    return `
      <div style="height: 1px; background: var(--border-strong); margin: 24px 0;"></div>
      <div id="monthly-chart-block">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
          <div style="width: 3px; height: 14px; background: var(--accent); border-radius: 2px;"></div>
          <span style="font-size: 13px; font-weight: 500; color: var(--text-1); text-transform: uppercase; letter-spacing: 0.06em;">${t("monthly_chart_title")}</span>
        </div>
        ${_renderMonthlySeasonFilter()}
        <div style="padding: 22px 18px; text-align: center; border: 0.5px dashed var(--border-strong); border-radius: 10px; background: rgba(255,255,255,0.02); color: var(--text-3); font-size: 13px; margin-top: 10px;">
          <div>${t("chart_no_matches")}</div>
          ${suggestionBtn}
        </div>
      </div>`;
  }

  // Sempre 12 mesi luglio→giugno della stagione selezionata
  const displayMonths = months;

  // Calcola scala asse Y (minuti)
  const maxMinutes = Math.max(...displayMonths.map(m => byMonth.get(m.key)?.minutes || 0), 90);
  // Arrotonda max al multiplo di 90 superiore
  const yMax = Math.ceil(maxMinutes / 90) * 90;

  // Dimensioni SVG
  const W = 660; // viewbox: scaleable
  const H = 220;
  const padL = 36, padR = 12, padT = 12, padB = 36;
  const chartW = W - padL - padR;
  const chartH = H - padT - padB;
  const colW = chartW / displayMonths.length;
  const barW = Math.min(colW * 0.65, 48);

  // Y-axis: 4 linee orizzontali (0, 1/3, 2/3, max)
  const yTicks = [0, Math.round(yMax/3), Math.round(2*yMax/3), yMax];
  const ySvg = (val) => padT + chartH - (val / yMax) * chartH;

  // Bars
  const bars = displayMonths.map((mo, i) => {
    const data = byMonth.get(mo.key);
    const mins = data?.minutes || 0;
    const apps = data?.apps || 0;
    const x = padL + i * colW + (colW - barW) / 2;
    const h = (mins / yMax) * chartH;
    const y = padT + chartH - h;
    const isActive = state.monthChart.month === mo.key;
    const hasData = mins > 0;
    const fill = hasData
      ? (isActive ? "var(--accent)" : "rgba(111,224,168,0.55)")
      : "rgba(255,255,255,0.05)";
    const stroke = isActive ? "var(--accent)" : (hasData ? "rgba(111,224,168,0.30)" : "transparent");
    return `
      <g class="chart-bar-group" data-month="${escapeHtml(mo.key)}" style="cursor: ${hasData?'pointer':'default'};">
        <rect x="${padL + i * colW}" y="${padT}" width="${colW}" height="${chartH}" fill="transparent"/>
        <rect x="${x}" y="${y}" width="${barW}" height="${Math.max(h, 1)}" fill="${fill}" stroke="${stroke}" stroke-width="1" rx="3" ry="3"/>
        ${hasData ? `<text x="${x + barW/2}" y="${y - 4}" text-anchor="middle" font-size="10" font-weight="700" fill="var(--accent)" style="font-variant-numeric: tabular-nums;">${mins}'</text>` : ""}
        ${apps > 0 ? `<text x="${x + barW/2}" y="${y + h/2 + 3}" text-anchor="middle" font-size="9" font-weight="700" fill="#0E1116" style="font-variant-numeric: tabular-nums; pointer-events: none;">${apps}</text>` : ""}
        <text x="${padL + i * colW + colW/2}" y="${H - 18}" text-anchor="middle" font-size="10" font-weight="500" fill="${isActive?'var(--accent)':'var(--text-3)'}" style="text-transform: uppercase; letter-spacing: 0.04em;">${escapeHtml(mo.label)}</text>
      </g>`;
  }).join("");

  // Y axis ticks
  const ticks = yTicks.map(v => `
    <line x1="${padL}" x2="${W - padR}" y1="${ySvg(v)}" y2="${ySvg(v)}" stroke="var(--border)" stroke-width="0.5"/>
    <text x="${padL - 6}" y="${ySvg(v) + 3}" text-anchor="end" font-size="9" fill="var(--text-3)" style="font-variant-numeric: tabular-nums;">${v}</text>
  `).join("");

  // Drill-down: partite del mese selezionato
  const selectedMonthKey = state.monthChart.month;
  const selectedMonthData = selectedMonthKey ? byMonth.get(selectedMonthKey) : null;
  const labelKeysAll = ["month_jan","month_feb","month_mar","month_apr","month_may","month_jun","month_jul","month_aug","month_sep","month_oct","month_nov","month_dec"];
  const monthLabel = selectedMonthKey
    ? `${t(labelKeysAll[parseInt(selectedMonthKey.slice(5,7))-1])} ${selectedMonthKey.slice(0,4)}`
    : "";

  const drillDown = selectedMonthData ? `
    <div class="rounded-lg mt-3" style="background: rgba(111,224,168,0.04); border: 0.5px solid rgba(111,224,168,0.20); padding: 10px 12px;">
      <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
        <span style="font-size: 11px; color: var(--accent); font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em;">${t("chart_month_matches")} ${escapeHtml(monthLabel)}</span>
        <span class="ml-auto stat-cell" style="font-size: 11px; color: var(--text-3);">${selectedMonthData.apps} • ${selectedMonthData.minutes}'</span>
        <button id="month-chart-close" style="background: rgba(239,68,68,0.10); color: #EF4444; border: 0.5px solid rgba(239,68,68,0.20); width: 20px; height: 20px; border-radius: 5px; font-size: 12px; line-height: 1; cursor: pointer;">×</button>
      </div>
      <div style="display: flex; flex-direction: column; gap: 4px;">
        ${[...selectedMonthData.matches].sort((a,b) => (_matchDateString(b)||"").localeCompare(_matchDateString(a)||"")).map(m => _renderDrillDownMatch(m, stats)).join("")}
      </div>
    </div>` : "";

  return `
    <div style="height: 1px; background: var(--border-strong); margin: 24px 0;"></div>
    <div id="monthly-chart-block">
      <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
        <div style="width: 3px; height: 14px; background: var(--accent); border-radius: 2px;"></div>
        <span style="font-size: 13px; font-weight: 500; color: var(--text-1); text-transform: uppercase; letter-spacing: 0.06em;">${t("monthly_chart_title")}</span>
        <span class="ml-auto stat-cell" style="font-size: 11px; color: var(--text-3);">${filtered.length} ${currentLang==="it"?"partite":"matches"} • ${filtered.reduce((a,m)=>a+(m.minutes||0),0)}'</span>
      </div>
      ${_renderMonthlySeasonFilter()}
      <div style="background: rgba(255,255,255,0.02); border-radius: 10px; padding: 8px 4px; margin-top: 10px;">
        <svg viewBox="0 0 ${W} ${H}" style="width: 100%; height: auto; display: block;" preserveAspectRatio="xMidYMid meet">
          ${ticks}
          ${bars}
        </svg>
      </div>
      ${drillDown}
    </div>`;
}

function _renderMonthlySeasonFilter() {
  // Solo le 2 stagioni: 2025/26 (default) e 2024/25 — niente "All" perché
  // l'histogram mostra sempre la stagione completa luglio→giugno
  const opts = [
    { v: "2025", label: t("season_label", "2025") },
    { v: "2024", label: t("season_label", "2024") },
  ];
  // Migrazione difensiva: se è ancora salvato "all", riporta a "2025"
  if (state.monthChart.season === "all") state.monthChart.season = "2025";
  return `
    <div class="flex gap-1">
      ${opts.map(o => {
        const sel = state.monthChart.season === o.v;
        return `<button class="month-chart-season-btn px-2.5 py-1 text-[11px] rounded-md font-semibold" data-season="${o.v}"
                style="background: ${sel?'var(--accent-bg)':'rgba(255,255,255,0.04)'}; color: ${sel?'var(--accent)':'var(--text-2)'}; border: 0.5px solid ${sel?'rgba(111,224,168,0.30)':'var(--border)'};">${escapeHtml(o.label)}</button>`;
      }).join("")}
    </div>`;
}

// Restituisce il nome della squadra nazionale per una partita nazionale,
// usando la nazionalità reale del giocatore (es. "Italia", "Belgio", "Brasile")
// + team_category presa da seasons[m.season].national[m.competition_id].
// "A" → "{Country}"; "U23" → "{Country} U23"; "Olympic" → "{Country} Olympic"; ecc.
function _nationalTeamName(m, stats) {
  if (!m?.is_national) return null;
  const seasons = stats?.seasons || {};
  const seasonKey = String(m.season ?? "");
  const cat = seasons?.[seasonKey]?.national?.[m.competition_id]?.team_category;
  if (!cat) return null;
  // Nazionalità del giocatore: priorità a stats.nationality, fallback su profile dal Map
  const pid = stats?.tm_player_id;
  const profile = pid != null ? state.players.find(x => x.tm_player_id === pid) : null;
  const country = stats?.nationality || profile?.nationality || profile?.citizenship || "National";
  if (cat === "A") return country;
  if (cat === "Olympic") return `${country} Olympic`;
  return `${country} ${cat}`;
}
// Alias di compatibilità (codice esistente potrebbe ancora chiamare il vecchio nome)
const _saudiNationalTeamName = _nationalTeamName;

function _natCatColor(cat) {
  if (cat === "A") return "var(--accent)";
  if (cat === "Olympic") return "#FBBF24";
  if (cat === "U23" || cat === "U22") return "#60A5FA";
  if (cat === "U20" || cat === "U19") return "#A78BFA";
  if (cat === "U18" || cat === "U17") return "#F472B6";
  if (cat === "U16" || cat === "U15") return "#FB923C";
  return "var(--comp-nat)";
}

function _renderDrillDownMatch(m, stats) {
  const ds = _matchDateString(m) || "";
  const date = ds ? `${ds.slice(8,10)}/${ds.slice(5,7)}/${ds.slice(2,4)}` : "—";
  const me = Number(m.result_for ?? 0);
  const opp = Number(m.result_against ?? 0);
  let resLetter = "—", resColor = "var(--text-3)", resBg = "rgba(255,255,255,0.05)";
  if (m.result_for != null && m.result_against != null) {
    if (me > opp) { resLetter = "V"; resColor = "#10B981"; resBg = "rgba(16,185,129,0.15)"; }
    else if (me === opp) { resLetter = "P"; resColor = "#FBBF24"; resBg = "rgba(251,191,36,0.15)"; }
    else { resLetter = "S"; resColor = "#EF4444"; resBg = "rgba(239,68,68,0.15)"; }
  }
  const oppC = state.clubsById?.get(m.opponent_club_id);
  const oppLogo = oppC ? clubLogo(oppC) : null;
  let oppName = oppC?.name;
  if (!oppName && m.opponent_name) oppName = m.opponent_name;  // U21 Excel: opponent name fornito direttamente
  if (!oppName && m.opponent_club_id != null && state.opponentNames?.[String(m.opponent_club_id)]) {
    oppName = state.opponentNames[String(m.opponent_club_id)];
  }
  if (!oppName && m.is_national && m.competition_name) {
    oppName = `${currentLang==="it"?"Naz.":"Nat."} ${m.competition_name}`;
  }
  if (!oppName) oppName = m.opponent_club_id ? `Club #${m.opponent_club_id}` : "—";
  const compLogo = competitionLogo(m.competition_id);
  const compName = _compName(m.competition_id, m.competition_name);
  const score = (m.result_for != null && m.result_against != null) ? `${m.result_for}-${m.result_against}` : "";

  // Per partite nazionali: nome nazionale (A / U23 / U20 / Olympic ...) su riga separata, con paese del giocatore
  const natTeam = _saudiNationalTeamName(m, stats);
  const natCat = m.is_national ? (stats?.seasons?.[String(m.season ?? "")]?.national?.[m.competition_id]?.team_category) : null;
  const natColor = natCat ? _natCatColor(natCat) : "var(--comp-nat)";
  const opponentBlock = m.is_national && natTeam
    ? `<div style="display: flex; flex-direction: column; gap: 1px; min-width: 0;">
         <span class="truncate" style="font-size: 10px; font-weight: 700; color: ${natColor}; line-height: 1.1;">${escapeHtml(natTeam)}</span>
         <div style="display: flex; align-items: center; gap: 5px; min-width: 0;">
           ${oppLogo ? `<img src="${oppLogo}" style="width: 14px; height: 14px; object-fit: contain; flex-shrink: 0;"/>` : ""}
           <span class="truncate" style="font-size: 12px; color: var(--text-1);">${escapeHtml(oppName)}</span>
         </div>
       </div>`
    : `<div style="display: flex; align-items: center; gap: 5px; min-width: 0;">
         ${oppLogo ? `<img src="${oppLogo}" style="width: 14px; height: 14px; object-fit: contain; flex-shrink: 0;"/>` : ""}
         <span class="truncate" style="font-size: 12px; color: var(--text-1);">${escapeHtml(oppName)}</span>
       </div>`;

  return `
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
}

// ============ RECENT MATCHES (lista) ============
function renderRecentMatches(stats) {
  const pid = stats?.tm_player_id;
  const allMatches = _allMatchesForPlayer(stats, pid);
  if (!Array.isArray(allMatches) || !allMatches.length) return "";

  // Ordina per data desc (gestendo sia stringhe ISO che oggetti TM e date "YYYY-MM-DD")
  const matches = [...allMatches].sort((a, b) => {
    const da = _matchDateString(a) || "";
    const db = _matchDateString(b) || "";
    return db.localeCompare(da);
  }).slice(0, 12);

  const fmtDate = (d) => {
    // Il campo date può essere: stringa ISO, timestamp numero, oppure oggetto {dateTimeUTC,dateTimeLocalized}
    let raw = d;
    if (raw && typeof raw === "object") {
      raw = raw.dateTimeUTC || raw.dateTimeLocalized || raw.timestamp;
    }
    if (!raw) return "—";
    try {
      const dt = new Date(typeof raw === "number" ? raw : Date.parse(raw));
      if (isNaN(dt.getTime())) return "—";
      return dt.toLocaleDateString(currentLang === "it" ? "it-IT" : "en-GB", { day: "2-digit", month: "2-digit", year: "2-digit" });
    } catch { return "—"; }
  };

  const opponentName = (m) => {
    const c = state.clubsById.get(m.opponent_club_id);
    if (c) return c.name;
    // Fallback diretto fornito dal record (es. partite U21 dall'Excel)
    if (m.opponent_name) return m.opponent_name;
    // Lookup nei nomi scrapati esterni
    const cid = m.opponent_club_id != null ? String(m.opponent_club_id) : null;
    if (cid && state.opponentNames && state.opponentNames[cid]) return state.opponentNames[cid];
    // Fallback migliore: per partite di nazionale, usa il nome competizione invece dell'ID grezzo
    if (m.is_national && m.competition_name) {
      return currentLang === "it" ? `Nazionale · ${m.competition_name}` : `National · ${m.competition_name}`;
    }
    return cid ? `Club #${cid}` : "—";
  };

  const rows = matches.map(m => {
    const me = Number(m.result_for ?? 0);
    const opp = Number(m.result_against ?? 0);
    let resultLetter, resultColor, resultBg;
    if (m.result_for == null || m.result_against == null) {
      resultLetter = "—"; resultColor = "var(--text-3)"; resultBg = "rgba(255,255,255,0.05)";
    } else if (me > opp) {
      resultLetter = "V"; resultColor = "#10B981"; resultBg = "rgba(16,185,129,0.15)";
    } else if (me === opp) {
      resultLetter = "P"; resultColor = "#FBBF24"; resultBg = "rgba(251,191,36,0.15)";
    } else {
      resultLetter = "S"; resultColor = "#EF4444"; resultBg = "rgba(239,68,68,0.15)";
    }
    const venue = m.venue === "home"
      ? `<span style="font-size: 10px; padding: 1px 5px; border-radius: 3px; background: rgba(111,224,168,0.10); color: var(--accent); font-weight: 600;">${currentLang==="it"?"C":"H"}</span>`
      : (m.venue === "away"
        ? `<span style="font-size: 10px; padding: 1px 5px; border-radius: 3px; background: rgba(96,165,250,0.10); color: var(--info); font-weight: 600;">${currentLang==="it"?"T":"A"}</span>`
        : "");
    const compLogo = competitionLogo(m.competition_id);
    const goals = m.goals || 0;
    const assists = m.assists || 0;
    const oppName = opponentName(m);
    const oppC = state.clubsById.get(m.opponent_club_id);
    const oppLogoUrl = oppC ? clubLogo(oppC) : null;
    const score = (m.result_for != null && m.result_against != null) ? `${m.result_for}-${m.result_against}` : "";

    return `
      <div style="display: grid; grid-template-columns: 64px 22px 1fr 70px 28px 60px; gap: 10px; align-items: center; padding: 10px 12px; border-bottom: 0.5px solid var(--border);">
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
      </div>`;
  }).join("");

  return `
    <div style="height: 1px; background: var(--border-strong); margin: 24px 0;"></div>
    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
      <div style="width: 3px; height: 14px; background: var(--info); border-radius: 2px;"></div>
      <span style="font-size: 13px; font-weight: 500; color: var(--text-1); text-transform: uppercase; letter-spacing: 0.06em;">${t("recent_matches")}</span>
      <span style="font-size: 10px; color: var(--text-3); margin-left: 4px;">${t("last_n", matches.length)}</span>
    </div>
    <div style="background: rgba(255,255,255,0.03); border-radius: 10px; overflow: hidden;">
      ${rows}
    </div>`;
}

// ============ CALLUP (convocazione) ============
const CALLUP_STORAGE_KEY = "saudi_callups_v1";

function loadCallups() {
  try {
    const raw = localStorage.getItem(CALLUP_STORAGE_KEY);
    if (!raw) return { lists: {}, currentName: "" };
    return JSON.parse(raw);
  } catch { return { lists: {}, currentName: "" }; }
}

function saveCallups(data) {
  try { localStorage.setItem(CALLUP_STORAGE_KEY, JSON.stringify(data)); } catch {}
}

state.callup = state.callup || {
  store: loadCallups(),
  currentIds: [], // tm_player_ids in convocazione
  filters: {
    yearMin: null, yearMax: null,
    role: "",
    roleSpecific: "",
    club: "",
    league: "",   // IT1 | IT2 | OTHER | ""=tutti
    minutesMin: null,  // minuti minimi giocati in stagione corrente
    q: "",
    preset: "A",
  },
};
// Migrazione: assicura che i nuovi filtri esistano anche su state.callup già esistente
if (state.callup.filters.league === undefined) state.callup.filters.league = "";
if (state.callup.filters.minutesMin === undefined) state.callup.filters.minutesMin = null;
if (state.callup.filters.roleSpecific === undefined) state.callup.filters.roleSpecific = "";

function ageGroupBounds(preset) {
  // Restituisce [yearMin, yearMax] per nascita.
  const seasonStart = parseInt(window.CURRENT_SEASON_YEAR || new Date().getMonth() >= 7 ? new Date().getFullYear() : new Date().getFullYear() - 1);
  // U17: nati < 17 anni alla data del 1° gennaio dell'anno della stagione
  const map = { U17: 17, U19: 19, U20: 20, U21: 21, U23: 23 };
  const limit = map[preset];
  if (limit) {
    const minYear = seasonStart - limit + 1;
    return [minYear, null];
  }
  return [null, null]; // "A" = tutti
}

function applyCallupFilters(players) {
  const f = state.callup.filters;
  const _seasonMins = (pid) => {
    const s = state.statsById.get(pid)?.seasons?.["2025"] || {};
    let total = Object.values({ ...s.club, ...s.national }).reduce((a, x) => a + (x.minutes_played || 0), 0);
    // Aggiungi minuti U21 Excel della stagione corrente (luglio 2025 → giugno 2026)
    try {
      const u21 = _u21MatchesNormalized(pid);
      for (const m of u21) {
        const ds = (m.date || "").slice(0, 10);
        if (!ds) continue;
        const [y, mo] = ds.split("-").map(Number);
        if ((y === 2025 && mo >= 7) || (y === 2026 && mo <= 6)) total += (m.minutes || 0);
      }
    } catch {}
    return total;
  };
  return players.filter(p => {
    const by = parseInt(birthYear(p));
    if (f.yearMin != null && (!by || by < f.yearMin)) return false;
    if (f.yearMax != null && (!by || by > f.yearMax)) return false;
    if (f.role && (p.position_general || "").toLowerCase() !== f.role.toLowerCase()) return false;
    if (f.roleSpecific && (p.position_specific || "") !== f.roleSpecific) return false;
    if (f.club && String(p.current_club_id) !== String(f.club)) return false;
    if (f.league) {
      const club = state.clubsById.get(p.current_club_id) || state.clubsById.get(String(p.current_club_id));
      const lg = String(club?.league_id || "OTHER");
      const isKnownLeague = (lg === "IT1" || lg === "IT2" || lg === "IJ1" || lg === "PL1" || lg === "PL2");
      const match = (f.league === "OTHER") ? !isKnownLeague : (lg === f.league);
      if (!match) return false;
    }
    if (f.minutesMin && _seasonMins(p.tm_player_id) < f.minutesMin) return false;
    if (f.q && !matchPlayer(p, f.q)) return false;
    return true;
  });
}

function renderCallupPanel() {
  const panel = document.getElementById("callup-panel");
  if (!panel) return;
  const f = state.callup.filters;
  const filtered = applyCallupFilters(state.players);
  const callupSet = new Set(state.callup.currentIds);
  // Ordine ruoli per la lista convocati: GK → DEF → MID → ATT
  const ROLE_ORDER = { "Goalkeeper": 0, "Defender": 1, "Midfield": 2, "Attack": 3 };
  const callupList = state.callup.currentIds
    .map(id => state.players.find(p => p.tm_player_id === id))
    .filter(Boolean)
    .sort((a, b) => {
      const ra = ROLE_ORDER[a.position_general] ?? 99;
      const rb = ROLE_ORDER[b.position_general] ?? 99;
      if (ra !== rb) return ra - rb;
      return (a.full_name||"").localeCompare(b.full_name||"");
    });
  // Conteggio per ruolo (per il summary in alto)
  const roleCounts = callupList.reduce((acc, p) => {
    const r = p.position_general || "—";
    acc[r] = (acc[r] || 0) + 1;
    return acc;
  }, {});

  // Aggregati
  const totalGoals = callupList.reduce((a, p) => a + totalGoals2025(p.tm_player_id), 0);
  const avgAge = callupList.length
    ? Math.round(callupList.reduce((a, p) => a + (p.age || 0), 0) / callupList.length)
    : 0;
  const totalMinutes = callupList.reduce((a, p) => {
    const s = state.statsById.get(p.tm_player_id)?.seasons?.["2025"] || {};
    return a + Object.values({ ...s.club, ...s.national }).reduce((x, c) => x + (c.minutes_played || 0), 0);
  }, 0);
  // Media caps nazionale A (senior) tra i convocati
  const capsA = callupList.map(p => {
    const nc = state.statsById.get(p.tm_player_id)?.national_career || [];
    const a = nc.find(n => n.category === "A");
    return a ? (a.caps || 0) : 0;
  });
  const avgCapsA = callupList.length
    ? Math.round(capsA.reduce((a, c) => a + c, 0) / callupList.length)
    : 0;

  const presets = [
    { v: "A", label: "A" },
    { v: "U23", label: "U23" },
    { v: "U21", label: "U21" },
    { v: "U20", label: "U20" },
    { v: "U19", label: "U19" },
    { v: "U17", label: "U17" },
  ];

  const savedNames = Object.keys(state.callup.store.lists).sort();

  const seasonMins = (pid) => {
    const s = state.statsById.get(pid)?.seasons?.["2025"] || {};
    return Object.values({ ...s.club, ...s.national }).reduce((a, x) => a + (x.minutes_played || 0), 0);
  };
  const renderPlayerRow = (p, inCallup) => {
    const club = state.clubsById.get(p.current_club_id);
    const logo = clubLogo(club);
    const mins = seasonMins(p.tm_player_id);
    return `
      <div class="callup-player-row flex items-center gap-3 p-2.5 rounded-md hover:bg-white/5" data-pid="${p.tm_player_id}" style="cursor: pointer;">
        <img src="${playerPhoto(p)}" class="w-12 h-12 rounded-full object-cover flex-shrink-0" style="background: var(--surface-2);"/>
        <div class="flex-1 min-w-0">
          <div class="text-sm font-semibold truncate" style="color: var(--text-1);">${escapeHtml(p.full_name)}</div>
          <div class="text-xs truncate flex items-center gap-1.5 mt-0.5" style="color: var(--text-3);">
            ${logo ? `<img src="${logo}" class="w-4 h-4 object-contain"/>` : ""}
            <span class="truncate">${escapeHtml(p.current_club_name||"")}</span>
            <span class="ml-1 stat-cell">${birthYear(p)||""}</span>
            <span class="ml-1 px-1.5 py-0.5 rounded" style="background: var(--accent-bg); color: var(--accent); font-size: 11px;">${escapeHtml(localizeRole(p.position_general))}</span>
          </div>
        </div>
        <div class="flex flex-col items-end gap-1 mr-1">
          <span class="stat-cell text-xs font-semibold" style="color: ${mins>0?'var(--accent)':'var(--text-3)'};" title="${currentLang==='it'?'Minuti giocati 25/26':'Minutes played 25/26'}">${mins}'</span>
          <span class="text-[9px] uppercase" style="color: var(--text-3); letter-spacing: 0.05em;">25/26</span>
        </div>
        <button class="text-base font-bold w-8 h-8 rounded ${inCallup ? "remove-btn" : "add-btn"}" style="${inCallup ? "background: rgba(239,68,68,0.15); color: #EF4444;" : "background: var(--accent-bg); color: var(--accent);"}">${inCallup ? "−" : "+"}</button>
      </div>`;
  };

  panel.innerHTML = `
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">

      <!-- LEFT: filtri + lista filtrata -->
      <div class="rounded-xl p-4" style="background: var(--surface); border: 0.5px solid var(--border);">
        <div class="flex items-center gap-2 mb-3">
          <h3 class="text-base font-bold" style="color: var(--text-1);">${currentLang==="it"?"Filtra giocatori":"Filter players"}</h3>
          <span class="ml-auto text-xs stat-cell" style="color: var(--text-3);">${filtered.length} / ${state.players.length}</span>
        </div>

        <!-- Preset categorie -->
        <div class="flex gap-1 mb-3 flex-wrap">
          ${presets.map(pr => `
            <button class="callup-preset-btn px-2.5 py-1 text-[11px] rounded-md font-semibold ${f.preset===pr.v?"active-preset":""}" data-preset="${pr.v}"
                    style="background: ${f.preset===pr.v?"var(--accent-bg)":"rgba(255,255,255,0.04)"}; color: ${f.preset===pr.v?"var(--accent)":"var(--text-2)"}; border: 0.5px solid ${f.preset===pr.v?"rgba(111,224,168,0.30)":"var(--border)"};">
              ${pr.label}
            </button>`).join("")}
        </div>

        <!-- Filtri secondari -->
        <div class="flex flex-wrap gap-2 mb-3">
          <input id="callup-search" type="text" placeholder="${currentLang==="it"?"Cerca nome/club...":"Search name/club..."}" value="${escapeHtml(f.q||"")}"
                 class="flex-1 min-w-[160px] outline-none text-sm px-3 py-1.5 rounded-md" style="background: var(--surface-2); border: 0.5px solid var(--border); color: var(--text-1);"/>
          <select id="callup-role" class="filter-select" style="font-size: 12px;">
            <option value="">${t("filter_all_roles")}</option>
            <option value="Goalkeeper" ${f.role==="Goalkeeper"?"selected":""}>${t("role_gk")}</option>
            <option value="Defender" ${f.role==="Defender"?"selected":""}>${t("role_def")}</option>
            <option value="Midfield" ${f.role==="Midfield"?"selected":""}>${t("role_mid")}</option>
            <option value="Attack" ${f.role==="Attack"?"selected":""}>${t("role_att")}</option>
          </select>
          <select id="callup-role-specific" class="filter-select" style="font-size: 12px;">
            <option value="">${t("filter_all_specific_roles")}</option>
            ${[...new Set(state.players.map(p => p.position_specific).filter(Boolean))].sort().map(r => `<option value="${escapeHtml(r)}" ${f.roleSpecific===r?"selected":""}>${escapeHtml(r)}</option>`).join("")}
          </select>
          <select id="callup-league" class="filter-select" style="font-size: 12px;">
            <option value="">${t("filter_all_leagues")}</option>
            <option value="IT1" ${f.league==="IT1"?"selected":""}>${t("league_it1")}</option>
            <option value="IT2" ${f.league==="IT2"?"selected":""}>${t("league_it2")}</option>
            <option value="IJ1" ${f.league==="IJ1"?"selected":""}>${t("league_ij1")}</option>
            <option value="PL1" ${f.league==="PL1"?"selected":""}>${t("league_pl1")}</option>
            <option value="PL2" ${f.league==="PL2"?"selected":""}>${t("league_pl2")}</option>
          </select>
          <select id="callup-club" class="filter-select" style="font-size: 12px;">
            <option value="">${t("filter_all_clubs")}</option>
            ${[...state.clubs].sort((a,b)=>(a.name||"").localeCompare(b.name||"")).map(c => `<option value="${c.tm_club_id}" ${String(f.club)===String(c.tm_club_id)?"selected":""}>${escapeHtml(c.name)}</option>`).join("")}
          </select>
          <input id="callup-year-min" type="text" inputmode="numeric" pattern="[0-9]*" maxlength="4" placeholder="${t("filter_year_min")}" value="${f.yearMin||""}"
                 class="w-24 outline-none text-sm px-2 py-1.5 rounded-md stat-cell" style="background: var(--surface-2); border: 0.5px solid var(--border); color: var(--text-1);"/>
          <input id="callup-year-max" type="text" inputmode="numeric" pattern="[0-9]*" maxlength="4" placeholder="${t("filter_year_max")}" value="${f.yearMax||""}"
                 class="w-24 outline-none text-sm px-2 py-1.5 rounded-md stat-cell" style="background: var(--surface-2); border: 0.5px solid var(--border); color: var(--text-1);"/>
          <input id="callup-minutes-min" type="text" inputmode="numeric" pattern="[0-9]*" maxlength="5" placeholder="${t("filter_minutes_min_ex")}" value="${f.minutesMin||""}"
                 class="w-32 outline-none text-sm px-2 py-1.5 rounded-md stat-cell" style="background: var(--surface-2); border: 0.5px solid var(--border); color: var(--text-1);"/>
        </div>

        <!-- Lista giocatori filtrati -->
        <div id="callup-list-scroll" class="overflow-y-auto" style="max-height: 60vh;">
          ${[...filtered].sort((a, b) => seasonMins(b.tm_player_id) - seasonMins(a.tm_player_id)).slice(0, 200).map(p => renderPlayerRow(p, callupSet.has(p.tm_player_id))).join("") || `<div class="text-center text-sm py-8" style="color: var(--text-3);">${t("no_results")}</div>`}
        </div>
      </div>

      <!-- RIGHT: convocazione attiva -->
      <div class="rounded-xl p-4" style="background: var(--surface); border: 0.5px solid var(--border);">
        <div class="flex items-center gap-2 mb-3">
          <h3 class="text-base font-bold" style="color: var(--text-1);">${currentLang==="it"?"Convocati":"Called up"}</h3>
          <span class="ml-auto text-xs stat-cell px-2 py-0.5 rounded-full" style="background: var(--accent-bg); color: var(--accent);">${callupList.length}</span>
        </div>

        <!-- Save controls -->
        <div class="flex gap-1 mb-3">
          <input id="callup-list-name" type="text" placeholder="${currentLang==="it"?"Nome lista (es. U23-2025)":"List name (e.g. U23-2025)"}"
                 value="${escapeHtml(state.callup.store.currentName||"")}"
                 class="flex-1 outline-none text-xs px-2 py-1.5 rounded-md" style="background: var(--surface-2); border: 0.5px solid var(--border); color: var(--text-1);"/>
          <button id="callup-save" class="px-2.5 py-1.5 text-xs font-semibold rounded-md" style="background: var(--accent); color: #0E1116;">${currentLang==="it"?"Salva":"Save"}</button>
        </div>

        ${savedNames.length ? `
          <div class="mb-3">
            <div class="text-[10px] uppercase tracking-wider mb-1" style="color: var(--text-3);">${currentLang==="it"?"Liste salvate":"Saved lists"}</div>
            <div class="flex flex-wrap gap-1">
              ${savedNames.map(n => `
                <span class="inline-flex items-center gap-1 px-2 py-0.5 text-[11px] rounded-md"
                      style="background: ${state.callup.store.currentName===n?"var(--accent-bg)":"rgba(255,255,255,0.04)"}; color: ${state.callup.store.currentName===n?"var(--accent)":"var(--text-2)"}; border: 0.5px solid var(--border);">
                  <button class="callup-load-btn" data-name="${escapeHtml(n)}" style="background: none; border: none; padding: 0; color: inherit; font-size: inherit; cursor: pointer;">
                    ${escapeHtml(n)} <span class="stat-cell" style="color: var(--text-3); font-size: 9px;">(${state.callup.store.lists[n].length})</span>
                  </button>
                  <button class="callup-delete-btn" data-name="${escapeHtml(n)}" title="${currentLang==='it'?'Cancella lista':'Delete list'}"
                          style="background: none; border: none; padding: 0 2px; color: var(--text-3); font-size: 14px; line-height: 1; cursor: pointer; margin-left: 2px;">×</button>
                </span>`).join("")}
            </div>
          </div>` : ""}

        <!-- Aggregati -->
        ${callupList.length ? `
          <div class="grid grid-cols-3 gap-1 mb-3">
            <div class="p-2 rounded text-center" style="background: var(--surface-2);">
              <div class="text-[9px] uppercase" style="color: var(--text-3);">${currentLang==="it"?"Età media":"Avg age"}</div>
              <div class="text-sm font-bold stat-cell" style="color: var(--text-1);">${avgAge||"—"}</div>
            </div>
            <div class="p-2 rounded text-center" style="background: var(--surface-2);">
              <div class="text-[9px] uppercase" style="color: var(--text-3);">${currentLang==="it"?"Gol 25/26":"Goals 25/26"}</div>
              <div class="text-sm font-bold stat-cell" style="color: var(--hot);">${totalGoals}</div>
            </div>
            <div class="p-2 rounded text-center" style="background: var(--surface-2);">
              <div class="text-[9px] uppercase" style="color: var(--text-3);">${currentLang==="it"?"Club":"Clubs"}</div>
              <div class="text-sm font-bold stat-cell" style="color: var(--text-1);">${new Set(callupList.map(p => p.current_club_id).filter(Boolean)).size}</div>
            </div>
            <div class="p-2 rounded text-center" style="background: var(--surface-2);">
              <div class="text-[9px] uppercase" style="color: var(--text-3);">${currentLang==="it"?"Min 25/26":"Min 25/26"}</div>
              <div class="text-sm font-bold stat-cell" style="color: var(--text-1);">${totalMinutes}</div>
            </div>
            <div class="p-2 rounded text-center col-span-2" style="background: var(--surface-2);">
              <div class="text-[9px] uppercase" style="color: var(--text-3);">${currentLang==="it"?"Media presenze naz. A":"Avg caps national A"}</div>
              <div class="text-sm font-bold stat-cell" style="color: var(--accent);">${avgCapsA||"—"}</div>
            </div>
          </div>` : ""}

        <!-- Riepilogo conteggi per ruolo -->
        ${callupList.length ? `
          <div class="flex flex-wrap gap-1 mb-3">
            ${[
              { code: "Goalkeeper", label: currentLang==="it"?"Portieri":"Goalkeepers", color: "#FBBF24" },
              { code: "Defender",   label: currentLang==="it"?"Difensori":"Defenders",  color: "#60A5FA" },
              { code: "Midfield",   label: currentLang==="it"?"Centrocampisti":"Midfielders", color: "#A78BFA" },
              { code: "Attack",     label: currentLang==="it"?"Attaccanti":"Strikers", color: "#F472B6" },
            ].map(r => {
              const n = roleCounts[r.code] || 0;
              return `<span class="inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-[11px]" style="background: ${r.color}1A; color: ${r.color}; border: 0.5px solid ${r.color}40; font-weight: 600;">
                ${escapeHtml(r.label)} <span class="stat-cell" style="font-size: 13px;">${n}</span>
              </span>`;
            }).join("")}
          </div>` : ""}

        <!-- Lista convocati ordinati per ruolo (GK > DEF > MID > ATT) con numerazione progressiva -->
        <div class="overflow-y-auto" style="max-height: 50vh;">
          ${callupList.length ? callupList.map((p, i) => `
            <div class="flex items-center gap-2">
              <span class="stat-cell flex-shrink-0 w-7 text-center font-bold" style="font-size: 14px; color: var(--accent);">${i+1}</span>
              <div class="flex-1 min-w-0">${renderPlayerRow(p, true)}</div>
            </div>`).join("") : `<div class="text-center text-xs py-8" style="color: var(--text-3);">${currentLang==="it"?"Nessun giocatore convocato. Clicca + sulla lista a sinistra.":"No called up players. Click + on the left list."}</div>`}
        </div>

        ${callupList.length ? `
          <div class="flex gap-1 mt-3 pt-3" style="border-top: 0.5px solid var(--border);">
            <button id="callup-clear" class="flex-1 px-2 py-1.5 text-[11px] rounded-md" style="background: rgba(239,68,68,0.10); color: #EF4444; border: 0.5px solid rgba(239,68,68,0.20);">${currentLang==="it"?"Svuota":"Clear"}</button>
            <button id="callup-export-pdf" class="flex-1 px-2 py-1.5 text-[11px] rounded-md font-semibold" style="background: rgba(96,165,250,0.10); color: var(--info); border: 0.5px solid rgba(96,165,250,0.20);">${currentLang==="it"?"Esporta PDF":"Export PDF"}</button>
            <button id="callup-export" class="flex-1 px-2 py-1.5 text-[11px] rounded-md" style="background: rgba(255,255,255,0.04); color: var(--text-2); border: 0.5px solid var(--border);">${currentLang==="it"?"Esporta CSV":"Export CSV"}</button>
          </div>` : ""}
      </div>
    </div>`;

  // Listeners
  panel.querySelectorAll(".callup-preset-btn").forEach(b => b.addEventListener("click", () => {
    const preset = b.dataset.preset;
    state.callup.filters.preset = preset;
    const [yMin, yMax] = ageGroupBounds(preset);
    state.callup.filters.yearMin = yMin;
    state.callup.filters.yearMax = yMax;
    renderCallupPanel();
  }));
  document.getElementById("callup-search")?.addEventListener("input", e => {
    state.callup.filters.q = e.target.value;
    renderCallupPanel();
    const newInput = document.getElementById("callup-search");
    if (newInput) {
      newInput.focus();
      const len = newInput.value.length;
      newInput.setSelectionRange(len, len);
    }
  });
  document.getElementById("callup-role")?.addEventListener("change", e => { state.callup.filters.role = e.target.value; renderCallupPanel(); });
  document.getElementById("callup-role-specific")?.addEventListener("change", e => { state.callup.filters.roleSpecific = e.target.value; renderCallupPanel(); });
  document.getElementById("callup-club")?.addEventListener("change", e => { state.callup.filters.club = e.target.value; renderCallupPanel(); });
  document.getElementById("callup-league")?.addEventListener("change", e => { state.callup.filters.league = e.target.value; renderCallupPanel(); });
  document.getElementById("callup-year-min")?.addEventListener("input", e => {
    const cleaned = (e.target.value || "").replace(/\D/g, "").slice(0, 4);
    state.callup.filters.yearMin = cleaned ? parseInt(cleaned) : null;
    renderCallupPanel();
    const i = document.getElementById("callup-year-min");
    if (i) { i.focus(); const l = i.value.length; i.setSelectionRange(l, l); }
  });
  document.getElementById("callup-year-max")?.addEventListener("input", e => {
    const cleaned = (e.target.value || "").replace(/\D/g, "").slice(0, 4);
    state.callup.filters.yearMax = cleaned ? parseInt(cleaned) : null;
    renderCallupPanel();
    const i = document.getElementById("callup-year-max");
    if (i) { i.focus(); const l = i.value.length; i.setSelectionRange(l, l); }
  });
  document.getElementById("callup-minutes-min")?.addEventListener("input", e => {
    const cleaned = (e.target.value || "").replace(/\D/g, "").slice(0, 5);
    state.callup.filters.minutesMin = cleaned ? parseInt(cleaned) : null;
    renderCallupPanel();
    const i = document.getElementById("callup-minutes-min");
    if (i) { i.focus(); const l = i.value.length; i.setSelectionRange(l, l); }
  });

  panel.querySelectorAll(".callup-player-row").forEach(row => {
    row.addEventListener("click", e => {
      const pid = parseInt(row.dataset.pid);
      // Preserva lo scroll della lista filtrata sx (evita jump in cima dopo +/−)
      const scrollEl = document.getElementById("callup-list-scroll");
      const savedScroll = scrollEl ? scrollEl.scrollTop : 0;
      const idx = state.callup.currentIds.indexOf(pid);
      if (idx >= 0) state.callup.currentIds.splice(idx, 1);
      else state.callup.currentIds.push(pid);
      renderCallupPanel();
      // Ripristina scroll subito dopo il re-render (DOM nuovo)
      const newScrollEl = document.getElementById("callup-list-scroll");
      if (newScrollEl) newScrollEl.scrollTop = savedScroll;
    });
  });

  panel.querySelectorAll(".callup-load-btn").forEach(b => b.addEventListener("click", () => {
    const name = b.dataset.name;
    state.callup.currentIds = [...(state.callup.store.lists[name] || [])];
    state.callup.store.currentName = name;
    saveCallups(state.callup.store);
    renderCallupPanel();
  }));

  panel.querySelectorAll(".callup-delete-btn").forEach(b => b.addEventListener("click", e => {
    e.stopPropagation();
    const name = b.dataset.name;
    if (!confirm(currentLang==="it"?`Cancellare definitivamente la lista "${name}"?`:`Delete list "${name}" permanently?`)) return;
    delete state.callup.store.lists[name];
    if (state.callup.store.currentName === name) {
      state.callup.store.currentName = "";
    }
    saveCallups(state.callup.store);
    renderCallupPanel();
  }));

  document.getElementById("callup-save")?.addEventListener("click", () => {
    const name = (document.getElementById("callup-list-name")?.value || "").trim();
    if (!name) { alert(currentLang==="it"?"Dai un nome alla lista":"Give the list a name"); return; }
    state.callup.store.lists[name] = [...state.callup.currentIds];
    state.callup.store.currentName = name;
    saveCallups(state.callup.store);
    renderCallupPanel();
  });

  document.getElementById("callup-clear")?.addEventListener("click", () => {
    if (!confirm(currentLang==="it"?"Svuotare la convocazione corrente?":"Clear current call-up?")) return;
    state.callup.currentIds = [];
    renderCallupPanel();
  });

  document.getElementById("callup-export")?.addEventListener("click", () => {
    const rows = [["Name","Club","Position","Year of birth","Age","Foot","Height (cm)","TM ID"]];
    callupList.forEach(p => {
      rows.push([
        p.full_name||"", p.current_club_name||"", p.position_specific||p.position_general||"",
        birthYear(p)||"", p.age||"", p.foot||"", p.height_cm||"", p.tm_player_id
      ]);
    });
    const csv = rows.map(r => r.map(c => `"${String(c).replace(/"/g,'""')}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `convocazione_${state.callup.store.currentName||"export"}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  });

  document.getElementById("callup-export-pdf")?.addEventListener("click", async () => {
    await exportCallupPDF(callupList);
  });
}

// ============ EXPORT CALLUP PDF (A4 verticale: foto + nome + anno + club + piede) ============
async function exportCallupPDF(callupList) {
  if (!window.jspdf) { alert(currentLang==="it"?"Libreria PDF non caricata.":"PDF library not loaded."); return; }
  const btn = document.getElementById("callup-export-pdf");
  if (btn) { btn.disabled = true; btn.textContent = currentLang==="it"?"Genero...":"Generating..."; }

  // Carica le foto come dataURL per embedding affidabile (evita CORS/cache-buster issue)
  const loadImageAsDataURL = (url, opts = {}) => new Promise(resolve => {
    if (!url) return resolve(null);
    const { circular = false, size = 64 } = opts;
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      try {
        const c = document.createElement("canvas");
        c.width = size; c.height = size;
        const ctx = c.getContext("2d");
        if (circular) {
          ctx.beginPath();
          ctx.arc(size/2, size/2, size/2, 0, Math.PI*2);
          ctx.closePath();
          ctx.clip();
        }
        ctx.drawImage(img, 0, 0, size, size);
        resolve(c.toDataURL("image/png"));
      } catch (e) { resolve(null); }
    };
    img.onerror = () => resolve(null);
    img.src = url;
  });

  try {
    // Ordina come nel pannello: GK → DEF → MID → ATT → alfabetico
    const ROLE_ORDER = { Goalkeeper: 0, Defender: 1, Midfield: 2, Attack: 3 };
    const sorted = [...callupList].sort((a, b) => {
      const ra = ROLE_ORDER[a.position_general] ?? 99;
      const rb = ROLE_ORDER[b.position_general] ?? 99;
      if (ra !== rb) return ra - rb;
      return (a.full_name||"").localeCompare(b.full_name||"");
    });

    // Pre-carica le foto giocatore (cerchio) e i loghi club come dataURL
    const photos = await Promise.all(sorted.map(p => loadImageAsDataURL(playerPhoto(p), { circular: true, size: 64 })));
    const clubLogos = await Promise.all(sorted.map(p => {
      const club = state.clubsById.get(p.current_club_id);
      const logoUrl = club ? clubLogo(club) : null;
      return loadImageAsDataURL(logoUrl, { circular: false, size: 64 });
    }));

    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF({ unit: "mm", format: "a4", orientation: "portrait" });
    const pageW = 210, pageH = 297;
    const margin = 12;

    // Header
    const title = state.callup.store.currentName || t("pdf_call_up");
    pdf.setFont("helvetica", "bold"); pdf.setFontSize(18); pdf.setTextColor(20,20,20);
    pdf.text(title, margin, margin + 6);

    pdf.setFont("helvetica", "normal"); pdf.setFontSize(11); pdf.setTextColor(80,80,80);
    // Conteggio per ruolo
    const roleCounts = sorted.reduce((acc, p) => {
      const r = p.position_general || "—";
      acc[r] = (acc[r] || 0) + 1;
      return acc;
    }, {});
    const gk = roleCounts["Goalkeeper"] || 0;
    const def = roleCounts["Defender"] || 0;
    const mid = roleCounts["Midfield"] || 0;
    const att = roleCounts["Attack"] || 0;
    pdf.text(t("pdf_count_breakdown", sorted.length, gk, def, mid, att), margin, margin + 13);

    const localeMap = { en: "en-GB", it: "it-IT", fr: "fr-FR", ar: "ar-SA" };
    const dateStr = new Date().toLocaleDateString(localeMap[currentLang] || "en-GB");
    pdf.text(dateStr, pageW - margin, margin + 13, { align: "right" });

    pdf.setDrawColor(200,200,200);
    pdf.line(margin, margin + 17, pageW - margin, margin + 17);

    // Header tabella
    let y = margin + 24;
    pdf.setFont("helvetica","bold"); pdf.setFontSize(8); pdf.setTextColor(120,120,120);
    pdf.text("#", margin + 2, y);
    pdf.text(t("pdf_player"), margin + 22, y);
    pdf.text(t("pdf_year"), margin + 100, y);
    pdf.text(t("pdf_club"), margin + 120, y);
    pdf.text(t("pdf_foot"), pageW - margin - 14, y);
    y += 2;
    pdf.setDrawColor(200,200,200); pdf.line(margin, y, pageW - margin, y);
    y += 5;

    const footMap = { left: t("foot_left"), right: t("foot_right"), both: t("foot_both") };
    const rowH = 13;
    let prevRoleGroup = null;

    for (let i = 0; i < sorted.length; i++) {
      const p = sorted[i];
      const role = p.position_general || "—";
      // Page break se necessario
      if (y + rowH > pageH - margin - 8) {
        pdf.addPage();
        y = margin;
      }
      // Header gruppo ruolo (cambia)
      if (role !== prevRoleGroup) {
        const roleLabel = role === "Goalkeeper" ? t("pdf_role_gk_pl")
          : role === "Defender" ? t("pdf_role_def_pl")
          : role === "Midfield" ? t("pdf_role_mid_pl")
          : role === "Attack" ? t("pdf_role_att_pl") : role;
        if (prevRoleGroup !== null) y += 3;
        pdf.setFillColor(245, 245, 245);
        pdf.rect(margin, y - 4, pageW - margin*2, 6, "F");
        pdf.setFont("helvetica","bold"); pdf.setFontSize(9); pdf.setTextColor(15, 110, 86);
        pdf.text(roleLabel.toUpperCase(), margin + 2, y);
        y += 5;
        prevRoleGroup = role;
      }

      // Numero progressivo
      pdf.setFont("helvetica","bold"); pdf.setFontSize(11); pdf.setTextColor(15, 110, 86);
      pdf.text(`${i+1}`, margin + 2, y + 5);

      // Foto cerchio
      const ph = photos[i];
      if (ph) {
        try { pdf.addImage(ph, "PNG", margin + 11, y - 1, 9, 9); } catch (e) {}
      }

      // Nome (bold)
      pdf.setFont("helvetica","bold"); pdf.setFontSize(10); pdf.setTextColor(20,20,20);
      const fullName = p.full_name || "";
      const nameMaxW = 75;
      pdf.text(fullName, margin + 22, y + 4, { maxWidth: nameMaxW });
      // Ruolo specifico sotto al nome
      if (p.position_specific || p.position_general) {
        pdf.setFont("helvetica","normal"); pdf.setFontSize(7); pdf.setTextColor(120,120,120);
        pdf.text(p.position_specific || p.position_general, margin + 22, y + 8);
      }

      // Anno di nascita
      pdf.setFont("helvetica","normal"); pdf.setFontSize(10); pdf.setTextColor(60,60,60);
      const yr = (birthYear(p) || "").toString();
      pdf.text(yr, margin + 100, y + 5);

      // Club: logo + nome
      const cLogo = clubLogos[i];
      if (cLogo) {
        try { pdf.addImage(cLogo, "PNG", margin + 119, y + 0.5, 7, 7); } catch (e) {}
      }
      pdf.setFont("helvetica","normal"); pdf.setFontSize(10); pdf.setTextColor(60,60,60);
      const clubName = (p.current_club_name || "").slice(0, 20);
      const clubX = cLogo ? (margin + 128) : (margin + 120);
      pdf.text(clubName, clubX, y + 5, { maxWidth: pageW - margin - clubX - 18 });

      // Piede
      pdf.setFont("helvetica","normal"); pdf.setFontSize(9); pdf.setTextColor(80,80,80);
      pdf.text(footMap[(p.foot||"").toLowerCase()] || "—", pageW - margin - 14, y + 5);

      y += rowH;
      // Linea separatrice tenue
      pdf.setDrawColor(235,235,235);
      pdf.line(margin, y - 3, pageW - margin, y - 3);
    }

    // ============ Tabella riassuntiva club (count giocatori per club) ============
    // Aggrega per current_club_id
    const clubAgg = new Map();
    sorted.forEach(p => {
      const cid = p.current_club_id || 0;
      if (!clubAgg.has(cid)) {
        const cl = state.clubsById.get(cid);
        clubAgg.set(cid, {
          name: p.current_club_name || (cl?.name) || "—",
          logoUrl: cl ? clubLogo(cl) : null,
          count: 0,
        });
      }
      clubAgg.get(cid).count++;
    });
    const clubsList = [...clubAgg.values()].sort((a, b) => b.count - a.count);
    // Pre-carica i loghi club dell'aggregato (potrebbero coincidere con clubLogos già caricati ma li ricarico per sicurezza)
    const clubSummaryLogos = await Promise.all(
      clubsList.map(c => loadImageAsDataURL(c.logoUrl, { circular: false, size: 64 }))
    );

    // Layout: 2 colonne (mezza pagina ciascuna)
    const COL_W = (pageW - 2*margin - 6) / 2;     // 6mm gap tra colonne
    const COL_X = [margin, margin + COL_W + 6];
    const ROW_H = 8;
    const HEADER_H = 9;
    const totalRows = Math.ceil(clubsList.length / 2);
    const tableHeight = HEADER_H + totalRows * ROW_H + 4;

    // Spazio tra ultima riga giocatori e tabella club
    y += 6;
    if (y + tableHeight > pageH - margin - 14) {
      pdf.addPage();
      y = margin;
    }

    // Header tabella club
    pdf.setFillColor(240, 240, 242);
    pdf.rect(margin, y, pageW - 2*margin, HEADER_H, "F");
    pdf.setFont("helvetica","bold"); pdf.setFontSize(9); pdf.setTextColor(40, 110, 80);
    pdf.text(t("pdf_clubs_summary").toUpperCase(), margin + 3, y + 6);
    pdf.setFont("helvetica","normal"); pdf.setFontSize(8); pdf.setTextColor(120,120,120);
    pdf.text(`${clubsList.length} club`, pageW - margin - 3, y + 6, { align: "right" });
    y += HEADER_H + 1;

    // Righe (2 colonne)
    pdf.setFont("helvetica","normal"); pdf.setFontSize(9); pdf.setTextColor(40, 40, 50);
    for (let i = 0; i < clubsList.length; i++) {
      const col = i % 2;
      const row = Math.floor(i / 2);
      const rx = COL_X[col];
      const ry = y + row * ROW_H;
      // page break interna se serve
      if (ry + ROW_H > pageH - margin - 10) {
        pdf.addPage();
        y = margin;
        // Re-disegna l'header per la pagina successiva
        pdf.setFillColor(240, 240, 242);
        pdf.rect(margin, y, pageW - 2*margin, HEADER_H, "F");
        pdf.setFont("helvetica","bold"); pdf.setFontSize(9); pdf.setTextColor(40, 110, 80);
        pdf.text(t("pdf_clubs_summary").toUpperCase() + " (cont.)", margin + 3, y + 6);
        y += HEADER_H + 1;
      }
      const c = clubsList[i];
      const logo = clubSummaryLogos[i];
      // sfondo zebra
      if (row % 2 === 1) {
        pdf.setFillColor(252, 252, 253);
        pdf.rect(rx, ry, COL_W, ROW_H, "F");
      }
      if (logo) {
        try { pdf.addImage(logo, "PNG", rx + 1, ry + 1, 6, 6); } catch {}
      }
      pdf.setFont("helvetica","normal"); pdf.setFontSize(9); pdf.setTextColor(40,40,50);
      const clubLine = (c.name || "").length > 28 ? c.name.slice(0, 26) + "…" : c.name;
      pdf.text(clubLine, rx + 9, ry + 5.2);
      // Count a destra della colonna, in verde
      pdf.setFont("helvetica","bold"); pdf.setFontSize(10); pdf.setTextColor(15, 110, 86);
      pdf.text(String(c.count), rx + COL_W - 3, ry + 5.5, { align: "right" });
      // Linea sottile sotto la riga
      pdf.setDrawColor(238,238,240);
      pdf.line(rx, ry + ROW_H, rx + COL_W, ry + ROW_H);
    }

    // ============ Box riassuntivo rosa (totale minuti, media, totale goal) ============
    // Calcola le stat aggregate sull'intera rosa
    const rosterMinutes = sorted.reduce((acc, p) => {
      const s = state.statsById.get(p.tm_player_id)?.seasons?.["2025"] || {};
      return acc + Object.values({ ...s.club, ...s.national }).reduce((x, c) => x + (c.minutes_played || 0), 0);
    }, 0);
    const rosterGoals = sorted.reduce((acc, p) => acc + totalGoals2025(p.tm_player_id), 0);
    const rosterAvgMin = sorted.length ? Math.round(rosterMinutes / sorted.length) : 0;

    // Posiziona subito dopo la tabella club
    const lastRosterY = y + Math.ceil(clubsList.length / 2) * ROW_H + 4;
    let yRoster = lastRosterY;
    const rosterBoxH = 22;
    if (yRoster + rosterBoxH > pageH - margin - 10) {
      pdf.addPage();
      yRoster = margin;
    }

    // Header
    pdf.setFillColor(240, 240, 242);
    pdf.rect(margin, yRoster, pageW - 2*margin, HEADER_H, "F");
    pdf.setFont("helvetica","bold"); pdf.setFontSize(9); pdf.setTextColor(40, 110, 80);
    pdf.text(t("pdf_roster_totals").toUpperCase(), margin + 3, yRoster + 6);
    pdf.setFont("helvetica","normal"); pdf.setFontSize(8); pdf.setTextColor(120,120,120);
    pdf.text(`${sorted.length} ${t("pdf_players_count")}`, pageW - margin - 3, yRoster + 6, { align: "right" });
    yRoster += HEADER_H + 2;

    // 3 stat box affiancate (Total Minutes, Avg Minutes, Total Goals)
    const cellW = (pageW - 2*margin - 8) / 3;  // 4mm gap × 2
    const cellGap = 4;
    const cellH = 12;
    const cells = [
      { label: t("pdf_total_minutes"), value: rosterMinutes.toLocaleString(localeMap[currentLang] || "en-GB") },
      { label: t("pdf_avg_minutes"),   value: rosterAvgMin.toLocaleString(localeMap[currentLang] || "en-GB") },
      { label: t("pdf_total_goals"),   value: String(rosterGoals) },
    ];
    cells.forEach((cell, idx) => {
      const cx = margin + idx * (cellW + cellGap);
      pdf.setFillColor(250, 250, 252);
      pdf.rect(cx, yRoster, cellW, cellH, "F");
      pdf.setDrawColor(228, 228, 232);
      pdf.rect(cx, yRoster, cellW, cellH, "S");
      // Label
      pdf.setFont("helvetica","normal"); pdf.setFontSize(7); pdf.setTextColor(120,120,120);
      pdf.text(cell.label.toUpperCase(), cx + 3, yRoster + 4);
      // Valore
      pdf.setFont("helvetica","bold"); pdf.setFontSize(13); pdf.setTextColor(15, 110, 86);
      pdf.text(cell.value, cx + cellW - 3, yRoster + 9.5, { align: "right" });
    });

    // Footer
    pdf.setFontSize(8); pdf.setFont("helvetica","normal"); pdf.setTextColor(150,150,150);
    pdf.text("Saudi Players Hub", margin, pageH - 6);
    pdf.text(dateStr, pageW - margin, pageH - 6, { align: "right" });

    const safeName = (title || "callup").replace(/[^a-zA-Z0-9_-]/g, "_");
    pdf.save(`${safeName}.pdf`);
  } catch (e) {
    console.error("Callup PDF error:", e);
    alert(t("pdf_export_error") + ": " + (e.message || e));
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = t("export_pdf"); }
  }
}

// ============ GRIDS (campo tattico) ============
// Posizioni in % (x=0..100 sinistra→destra, y=0..100 porta nostra→avanti)
// Y bassa = portiere/difesa nostra, Y alta = attacco
const FORMATIONS = {
  "4-3-3": [
    { id: "GK",  x: 50, y: 8,  label: "GK"  },
    { id: "RB", x: 88, y: 31, label: "RB"  },
    { id: "RCB", x: 62, y: 25, label: "CB"  },
    { id: "LCB", x: 38, y: 25, label: "CB"  },
    { id: "LB", x: 12, y: 31, label: "LB"  },
    { id: "RCM", x: 82, y: 52, label: "CM"  },
    { id: "CM",  x: 50, y: 46, label: "CM"  },
    { id: "LCM", x: 18, y: 52, label: "CM"  },
    { id: "RW",  x: 86, y: 76, label: "RW"  },
    { id: "ST",  x: 50, y: 84, label: "ST"  },
    { id: "LW",  x: 14, y: 76, label: "LW"  },
  ],
  "4-4-2": [
    { id: "GK",  x: 50, y: 8,  label: "GK" },
    { id: "RB", x: 88, y: 31, label: "RB" },
    { id: "RCB", x: 62, y: 25, label: "CB" },
    { id: "LCB", x: 38, y: 25, label: "CB" },
    { id: "LB", x: 12, y: 31, label: "LB" },
    { id: "RM",  x: 86, y: 52, label: "RM" },
    { id: "RCM", x: 62, y: 50, label: "CM" },
    { id: "LCM", x: 38, y: 50, label: "CM" },
    { id: "LM",  x: 14, y: 52, label: "LM" },
    { id: "RST", x: 66, y: 82, label: "ST" },
    { id: "LST", x: 34, y: 82, label: "ST" },
  ],
  "3-5-2": [
    { id: "GK",  x: 50, y: 8,  label: "GK"  },
    { id: "RCB", x: 70, y: 25, label: "CB"  },
    { id: "CB", x: 50, y: 23, label: "CB"  },
    { id: "LCB", x: 30, y: 25, label: "CB"  },
    { id: "RWB", x: 88, y: 39, label: "RWB" },
    { id: "RCM", x: 70, y: 50, label: "CM"  },
    { id: "CM",  x: 50, y: 46, label: "CM"  },
    { id: "LCM", x: 30, y: 50, label: "CM"  },
    { id: "LWB", x: 12, y: 39, label: "LWB" },
    { id: "RST", x: 60, y: 82, label: "ST"  },
    { id: "LST", x: 40, y: 82, label: "ST"  },
  ],
  "4-2-3-1": [
    { id: "GK",  x: 50, y: 8,  label: "GK"   },
    { id: "RB", x: 88, y: 31, label: "RB"   },
    { id: "RCB", x: 62, y: 25, label: "CB"   },
    { id: "LCB", x: 38, y: 25, label: "CB"   },
    { id: "LB", x: 12, y: 31, label: "LB"   },
    { id: "RDM", x: 66, y: 42, label: "DM"   },
    { id: "LDM", x: 34, y: 42, label: "DM"   },
    { id: "RAM", x: 90, y: 65, label: "RAM"  },
    { id: "CAM", x: 50, y: 64, label: "CAM"  },
    { id: "LAM", x: 10, y: 65, label: "LAM"  },
    { id: "ST",  x: 50, y: 86, label: "ST"   },
  ],
  "3-4-3": [
    { id: "GK",  x: 50, y: 8,  label: "GK" },
    { id: "RCB", x: 70, y: 25, label: "CB" },
    { id: "CB", x: 50, y: 23, label: "CB" },
    { id: "LCB", x: 30, y: 25, label: "CB" },
    { id: "RM",  x: 88, y: 50, label: "RM" },
    { id: "RCM", x: 60, y: 48, label: "CM" },
    { id: "LCM", x: 40, y: 48, label: "CM" },
    { id: "LM",  x: 12, y: 50, label: "LM" },
    { id: "RW",  x: 86, y: 80, label: "RW" },
    { id: "ST",  x: 50, y: 84, label: "ST" },
    { id: "LW",  x: 14, y: 80, label: "LW" },
  ],
};

state.grids = state.grids || {
  formation: "4-3-3",
  assigned: {},  // role_id -> [tm_player_id, ...]  (titolare = primo, riserve a seguire)
  filterQ: "",
  filterClub: "",
  filterRole: "",
  filterRoleSpecific: "",
  filterLeague: "",   // IT1 | IT2 | OTHER | ""=tutti
  filterYearMin: null,
  filterYearMax: null,
  filterMinutesMin: null,  // minuti minimi giocati in stagione corrente
  selectedSlot: null, // role_id quando si è cliccato uno slot
};
// Migrazione: assicura che i nuovi campi esistano anche su state.grids già esistente
state.grids.filterClub = state.grids.filterClub || "";
state.grids.filterRole = state.grids.filterRole || "";
if (state.grids.filterRoleSpecific === undefined) state.grids.filterRoleSpecific = "";
if (state.grids.filterLeague === undefined) state.grids.filterLeague = "";
if (state.grids.filterYearMin === undefined) state.grids.filterYearMin = null;
if (state.grids.filterYearMax === undefined) state.grids.filterYearMax = null;
if (state.grids.filterMinutesMin === undefined) state.grids.filterMinutesMin = null;

// Helper: assicura che assigned[role] sia sempre un array (migrazione da vecchio formato scalar)
function _gridsAssignedFor(roleId) {
  const v = state.grids.assigned[roleId];
  if (Array.isArray(v)) return v;
  if (v == null) return [];
  return [v]; // migrazione singolo id → array
}
function _gridsAssignedAll() {
  const out = [];
  for (const role of Object.keys(state.grids.assigned)) {
    for (const pid of _gridsAssignedFor(role)) {
      if (pid) out.push(pid);
    }
  }
  return out;
}

// Mappa uno slot della formazione al suo macro-ruolo (per l'import convocazione)
function _slotRoleGeneral(slot) {
  const id = slot.id;
  const lab = slot.label || id;
  if (id === "GK" || lab === "GK") return "Goalkeeper";
  if (lab === "CB" || lab === "LB" || lab === "RB" || lab === "RWB" || lab === "LWB") return "Defender";
  if (["CM","RM","LM","DM","CAM","RAM","LAM","RDM","LDM"].includes(lab)) return "Midfield";
  if (["RW","LW","ST"].includes(lab)) return "Attack";
  return null;
}

// Importa una convocazione salvata nei selezionati di Minutaggi
function importCallupToMinutes(callupName) {
  const ids = state.callup?.store?.lists?.[callupName] || [];
  if (!ids.length) return 0;
  // Sostituisce la selezione corrente
  state.minutes.selectedIds = [...ids];
  try { localStorage.setItem(MINUTES_STORAGE_KEY, JSON.stringify(state.minutes.selectedIds)); } catch {}
  return ids.length;
}

// Importa una convocazione salvata nella griglia tattica corrente:
// distribuisce i giocatori per macroruolo nei slot della formazione (round-robin)
function importCallupToGrid(callupName) {
  const ids = state.callup?.store?.lists?.[callupName] || [];
  if (!ids.length) return 0;
  const positions = FORMATIONS[state.grids.formation] || FORMATIONS["4-3-3"];
  // Raggruppa slot per macroruolo, mantenendo l'ordine dichiarato
  const slotsByRole = { Goalkeeper: [], Defender: [], Midfield: [], Attack: [] };
  positions.forEach(pos => {
    const r = _slotRoleGeneral(pos);
    if (slotsByRole[r]) slotsByRole[r].push(pos.id);
  });
  // Raggruppa giocatori convocati per macroruolo
  const playersByRole = { Goalkeeper: [], Defender: [], Midfield: [], Attack: [] };
  for (const pid of ids) {
    const p = state.players.find(x => x.tm_player_id === pid);
    if (!p) continue;
    const r = p.position_general;
    if (playersByRole[r]) playersByRole[r].push(pid);
    else playersByRole["Midfield"].push(pid); // fallback prudente
  }
  // Reset assegnazioni e popola round-robin (titolari + depth chart)
  state.grids.assigned = {};
  for (const role of Object.keys(playersByRole)) {
    const players = playersByRole[role];
    const slots = slotsByRole[role];
    if (!slots.length) continue;
    players.forEach((pid, idx) => {
      const slot = slots[idx % slots.length];
      if (!state.grids.assigned[slot]) state.grids.assigned[slot] = [];
      state.grids.assigned[slot].push(pid);
    });
  }
  _saveGrids();
  return ids.length;
}

// Persistenza estesa: stato corrente + liste salvate (nominate)
state.grids.store = state.grids.store || { lists: {}, currentName: "" };

function _saveGrids() {
  try {
    const data = {
      formation: state.grids.formation,
      assigned: state.grids.assigned,
      store: state.grids.store,
    };
    localStorage.setItem("pid_grids_v1", JSON.stringify(data));
  } catch {}
}
(() => { try {
  const raw = localStorage.getItem("pid_grids_v1");
  if (!raw) return;
  const parsed = JSON.parse(raw);
  if (parsed.formation) state.grids.formation = parsed.formation;
  if (parsed.assigned) state.grids.assigned = parsed.assigned;
  if (parsed.store) state.grids.store = parsed.store;
} catch {} })();

function renderGridsPanel() {
  const panel = document.getElementById("grids-panel");
  if (!panel) return;

  const positions = FORMATIONS[state.grids.formation] || FORMATIONS["4-3-3"];
  const assignedSet = new Set(_gridsAssignedAll());

  // Lista filtrabile (esclude i già assegnati)
  const ql = (state.grids.filterQ || "").toLowerCase();
  const fClub = state.grids.filterClub || "";
  const fRole = state.grids.filterRole || "";
  const fYrMin = state.grids.filterYearMin;
  const fYrMax = state.grids.filterYearMax;
  const fMinMin = state.grids.filterMinutesMin;
  const fLeague = state.grids.filterLeague || "";
  const fRoleSpec = state.grids.filterRoleSpecific || "";
  const _seasonMins = (pid) => {
    const s = state.statsById.get(pid)?.seasons?.["2025"] || {};
    let total = Object.values({ ...s.club, ...s.national }).reduce((a, x) => a + (x.minutes_played || 0), 0);
    // Aggiungi minuti U21 Excel della stagione corrente (luglio 2025 → giugno 2026)
    try {
      const u21 = _u21MatchesNormalized(pid);
      for (const m of u21) {
        const ds = (m.date || "").slice(0, 10);
        if (!ds) continue;
        const [y, mo] = ds.split("-").map(Number);
        if ((y === 2025 && mo >= 7) || (y === 2026 && mo <= 6)) total += (m.minutes || 0);
      }
    } catch {}
    return total;
  };
  // Lista dinamica dei ruoli specifici (popolata dai giocatori esistenti)
  const roleSpecificOptions = [...new Set(state.players.map(p => p.position_specific).filter(Boolean))].sort();
  const available = state.players.filter(p => {
    if (assignedSet.has(p.tm_player_id)) return false;
    if (fClub && String(p.current_club_id) !== String(fClub)) return false;
    if (fRole && (p.position_general||"").toLowerCase() !== fRole.toLowerCase()) return false;
    if (fRoleSpec && (p.position_specific||"") !== fRoleSpec) return false;
    if (fLeague) {
      const club = state.clubsById.get(p.current_club_id) || state.clubsById.get(String(p.current_club_id));
      const lg = String(club?.league_id || "OTHER");
      const isKnownLeague = (lg === "IT1" || lg === "IT2" || lg === "IJ1" || lg === "PL1" || lg === "PL2");
      const match = (fLeague === "OTHER") ? !isKnownLeague : (lg === fLeague);
      if (!match) return false;
    }
    const yr = parseInt(birthYear(p));
    if (fYrMin && (!yr || yr < fYrMin)) return false;
    if (fYrMax && (!yr || yr > fYrMax)) return false;
    if (fMinMin && _seasonMins(p.tm_player_id) < fMinMin) return false;
    return matchPlayer(p, state.grids.filterQ);
  })
  .sort((a, b) => _seasonMins(b.tm_player_id) - _seasonMins(a.tm_player_id))  // minuti decrescenti
  .slice(0, 200);

  // Render slot sul campo: titolare grande + depth chart inline ancorato sotto
  const renderSlot = (pos) => {
    const ids = _gridsAssignedFor(pos.id);
    const titularPid = ids[0];
    const p = titularPid ? state.players.find(x => x.tm_player_id === titularPid) : null;
    const selected = state.grids.selectedSlot === pos.id;
    const baseStyle = `position: absolute; left: ${pos.x}%; top: ${100 - pos.y}%; transform: translate(-50%, -50%); cursor: pointer; user-select: none;`;

    // Depth chart popup (no foto grande sul campo, no shirt number, font più grande)
    let depthHtml = "";
    if (ids.length > 0) {
      const clubAbbrev = (name) => {
        if (!name) return "";
        return name.replace(/\s(SFC|FC|SC|Club|Riad)\b.*$/, "").slice(0, 16);
      };
      const seasonMinutes = (pid) => {
        const s = state.statsById.get(pid)?.seasons?.["2025"] || {};
        let total = Object.values({ ...s.club, ...s.national }).reduce((a, x) => a + (x.minutes_played || 0), 0);
        try {
          const u21 = _u21MatchesNormalized(pid);
          for (const m of u21) {
            const ds = (m.date || "").slice(0, 10);
            if (!ds) continue;
            const [y, mo] = ds.split("-").map(Number);
            if ((y === 2025 && mo >= 7) || (y === 2026 && mo <= 6)) total += (m.minutes || 0);
          }
        } catch {}
        return total;
      };
      const yrShort = (full) => full ? `'${full.slice(-2)}` : "";
      depthHtml = `
        <div class="grid-depth-popup" style="margin-top: 4px; background: rgba(14,17,22,0.94); border: 0.5px solid rgba(255,255,255,0.10); border-radius: 5px; padding: 3px; backdrop-filter: blur(4px); min-width: 230px; max-width: 270px;">
          ${ids.map((pid, idx) => {
            const pl = state.players.find(x => x.tm_player_id === pid);
            if (!pl) return "";
            const isStarter = idx === 0;
            const yr = yrShort(birthYear(pl) || "");
            const club = clubAbbrev(pl.current_club_name || "");
            const mins = seasonMinutes(pid);
            const foot = footShort(pl.foot);
            const subParts = [];
            if (yr) subParts.push(`<span style="color: var(--text-2); font-weight: 600;">${yr}</span>`);
            if (club) subParts.push(escapeHtml(club));
            if (foot) subParts.push(`<span style="color: var(--text-2); font-weight: 600;">${foot}</span>`);
            const subLine = subParts.join(" · ");
            return `
              <div class="grid-depth-item" data-slot="${pos.id}" data-idx="${idx}"
                   style="display: flex; align-items: center; gap: 5px; padding: 2px 3px; border-radius: 4px; ${isStarter?'background: rgba(111,224,168,0.12);':''}; margin-bottom: 2px;">
                <span class="stat-cell" style="flex-shrink: 0; width: 16px; height: 32px; font-size: 13px; font-weight: 700; color: ${isStarter?'var(--accent)':'var(--text-3)'}; display: flex; align-items: center; justify-content: center;">${idx+1}</span>
                <img src="${playerPhoto(pl)}" style="flex-shrink: 0; width: 32px; height: 32px; border-radius: 50%; object-fit: cover; background: var(--surface-2); display: block;"/>
                <div style="flex: 1; min-width: 0; display: flex; flex-direction: column; justify-content: center; height: 32px;">
                  <div style="font-size: 13px; color: var(--text-1); font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; line-height: 1.25;">${escapeHtml(pl.full_name||"")}</div>
                  <div style="font-size: 10px; color: var(--text-3); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; line-height: 1.3; margin-top: 2px;">${subLine}</div>
                </div>
                <span class="stat-cell" style="flex-shrink: 0; font-size: 11px; font-weight: 700; color: ${mins>0?'var(--accent)':'var(--text-3)'}; min-width: 42px; text-align: right;">${mins}'</span>
                <button class="grid-depth-remove" data-slot="${pos.id}" data-idx="${idx}" style="flex-shrink: 0; background: rgba(239,68,68,0.10); border: none; color: #EF4444; font-size: 11px; line-height: 1; padding: 1px 4px; border-radius: 3px; cursor: pointer; align-self: center;">×</button>
              </div>`;
          }).join("")}
        </div>`;
    }

    // Sempre cerchio-label posizione (no foto grande). Verde pieno se assegnato, dashed se vuoto.
    const filled = ids.length > 0;
    const circleStyle = filled
      ? `width: 36px; height: 36px; border-radius: 50%; border: 2px solid ${selected?'var(--hot)':'var(--accent)'}; background: ${selected?'rgba(251,191,36,0.18)':'rgba(111,224,168,0.18)'}; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; color: ${selected?'var(--hot)':'var(--accent)'}; backdrop-filter: blur(2px);`
      : `width: 44px; height: 44px; border-radius: 50%; border: 2px dashed ${selected?'var(--hot)':'rgba(255,255,255,0.30)'}; background: ${selected?'rgba(251,191,36,0.15)':'rgba(255,255,255,0.05)'}; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 700; color: ${selected?'var(--hot)':'rgba(255,255,255,0.55)'}; backdrop-filter: blur(2px);`;
    return `
      <div class="grid-slot ${filled?'filled':'empty'}" data-slot="${pos.id}" style="${baseStyle}">
        <div style="display: flex; flex-direction: column; align-items: center; gap: 2px;">
          <div style="${circleStyle}">${pos.label}</div>
          ${depthHtml}
        </div>
      </div>`;
  };

  // Render depth chart: per ogni posizione, lista titolare + riserve con ↑/↓/×
  const renderDepthChart = () => {
    const sections = positions.map(pos => {
      const ids = _gridsAssignedFor(pos.id);
      if (!ids.length) return null;
      const rows = ids.map((pid, idx) => {
        const p = state.players.find(x => x.tm_player_id === pid);
        if (!p) return "";
        const isTitular = idx === 0;
        return `
          <div class="grid-depth-row flex items-center gap-2 p-1.5 rounded-md" style="background: ${isTitular?'rgba(111,224,168,0.06)':'rgba(255,255,255,0.02)'};">
            <span class="stat-cell" style="font-size: 10px; font-weight: 700; color: ${isTitular?'var(--accent)':'var(--text-3)'}; min-width: 18px; text-align: center;">${idx+1}</span>
            <img src="${playerPhoto(p)}" class="w-7 h-7 rounded-full object-cover flex-shrink-0" style="background: var(--surface-2);"/>
            <div class="flex-1 min-w-0">
              <div class="text-xs font-medium truncate" style="color: var(--text-1);">${escapeHtml(p.full_name)}</div>
              <div class="text-[10px] truncate" style="color: var(--text-3);">${escapeHtml(p.current_club_name||"")}</div>
            </div>
            <button class="grid-move-up" data-slot="${pos.id}" data-idx="${idx}" ${idx===0?"disabled":""} title="${currentLang==='it'?'su':'up'}"
                    style="width: 22px; height: 22px; border-radius: 4px; background: rgba(255,255,255,0.05); border: 0.5px solid var(--border); color: ${idx===0?'var(--text-3)':'var(--text-2)'}; cursor: ${idx===0?'not-allowed':'pointer'}; font-size: 11px;">↑</button>
            <button class="grid-move-down" data-slot="${pos.id}" data-idx="${idx}" ${idx===ids.length-1?"disabled":""} title="${currentLang==='it'?'giù':'down'}"
                    style="width: 22px; height: 22px; border-radius: 4px; background: rgba(255,255,255,0.05); border: 0.5px solid var(--border); color: ${idx===ids.length-1?'var(--text-3)':'var(--text-2)'}; cursor: ${idx===ids.length-1?'not-allowed':'pointer'}; font-size: 11px;">↓</button>
            <button class="grid-remove" data-slot="${pos.id}" data-idx="${idx}" title="${currentLang==='it'?'rimuovi':'remove'}"
                    style="width: 22px; height: 22px; border-radius: 4px; background: rgba(239,68,68,0.10); border: 0.5px solid rgba(239,68,68,0.20); color: #EF4444; cursor: pointer; font-size: 11px;">×</button>
          </div>`;
      }).join("");
      return `
        <div class="mb-2">
          <div class="flex items-center gap-2 mb-1 px-1">
            <span class="text-[10px] font-bold uppercase tracking-wider" style="color: var(--accent);">${pos.id}</span>
            <span class="text-[10px]" style="color: var(--text-3);">${pos.label}</span>
            <span class="ml-auto text-[10px] stat-cell" style="color: var(--text-3);">${ids.length}</span>
          </div>
          <div class="space-y-1">${rows}</div>
        </div>`;
    }).filter(Boolean).join("");
    if (!sections) return `<div class="text-xs text-center py-6" style="color: var(--text-3);">${currentLang==="it"?"Nessun giocatore assegnato":"No players assigned"}</div>`;
    return sections;
  };

  // SVG campo da calcio (verticale)
  const pitchSvg = `
    <svg viewBox="0 0 100 100" preserveAspectRatio="none" style="position: absolute; inset: 0; width: 100%; height: 100%;">
      <defs>
        <pattern id="grass" width="100" height="10" patternUnits="userSpaceOnUse">
          <rect width="100" height="10" fill="#0f4d2a"/>
          <rect width="100" height="5" fill="#0d4426" y="5"/>
        </pattern>
      </defs>
      <rect width="100" height="100" fill="url(#grass)"/>
      <rect x="2" y="2" width="96" height="96" fill="none" stroke="rgba(255,255,255,0.5)" stroke-width="0.3"/>
      <line x1="2" y1="50" x2="98" y2="50" stroke="rgba(255,255,255,0.5)" stroke-width="0.3"/>
      <!-- Cerchio centrocampo: ellipse con rx/ry = 10/9 ≈ 1.111 per compensare aspect-ratio 9/10 (campo leggermente più basso) -->
      <ellipse cx="50" cy="50" rx="10" ry="9" fill="none" stroke="rgba(255,255,255,0.5)" stroke-width="0.3"/>
      <ellipse cx="50" cy="50" rx="0.89" ry="0.8" fill="rgba(255,255,255,0.6)"/>
      <rect x="22" y="2" width="56" height="14" fill="none" stroke="rgba(255,255,255,0.5)" stroke-width="0.3"/>
      <rect x="34" y="2" width="32" height="6" fill="none" stroke="rgba(255,255,255,0.5)" stroke-width="0.3"/>
      <rect x="22" y="84" width="56" height="14" fill="none" stroke="rgba(255,255,255,0.5)" stroke-width="0.3"/>
      <rect x="34" y="92" width="32" height="6" fill="none" stroke="rgba(255,255,255,0.5)" stroke-width="0.3"/>
    </svg>`;

  const selectedLabel = state.grids.selectedSlot
    ? (positions.find(p => p.id === state.grids.selectedSlot)?.label || state.grids.selectedSlot)
    : null;

  const savedGridNames = Object.keys(state.grids.store.lists || {}).sort();

  panel.innerHTML = `
    <div class="grid gap-4" style="grid-template-columns: minmax(0, 1fr) 270px; align-items: start;">
      <!-- LEFT: Pitch + controlli -->
      <div class="rounded-xl p-3" style="background: var(--surface); border: 0.5px solid var(--border);">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          <h3 class="text-base font-bold" style="color: var(--text-1);">${t("formation_label")}</h3>
          <select id="grids-formation" class="filter-select" style="font-size: 13px;">
            ${Object.keys(FORMATIONS).map(f => `<option value="${f}" ${state.grids.formation===f?"selected":""}>${f}</option>`).join("")}
          </select>
          <span class="ml-auto text-xs stat-cell" style="color: var(--text-3);">${positions.filter(p => _gridsAssignedFor(p.id).length > 0).length} / 11</span>
          <button id="grids-to-callup" class="text-[11px] px-2 py-1 rounded-md" style="background: var(--accent-bg); color: var(--accent); border: 0.5px solid rgba(111,224,168,0.30); font-weight: 600;">${t("add_to_callup")}</button>
          <button id="grids-export-pdf" class="text-[11px] px-2 py-1 rounded-md" style="background: rgba(96,165,250,0.10); color: var(--info); border: 0.5px solid rgba(96,165,250,0.20);">${t("export_pdf")}</button>
          <button id="grids-clear" class="text-[11px] px-2 py-1 rounded-md" style="background: rgba(239,68,68,0.10); color: #EF4444; border: 0.5px solid rgba(239,68,68,0.20);">${t("clear_btn")}</button>
        </div>

        <!-- Save/load toolbar (come Convocazione) -->
        <div class="flex items-center gap-1 mb-3 flex-wrap">
          <input id="grids-list-name" type="text" placeholder="${t("grid_name_placeholder")}"
                 value="${escapeHtml(state.grids.store.currentName||"")}"
                 class="flex-1 min-w-[160px] outline-none text-xs px-2 py-1.5 rounded-md" style="background: var(--surface-2); border: 0.5px solid var(--border); color: var(--text-1);"/>
          <button id="grids-save" class="px-2.5 py-1.5 text-xs font-semibold rounded-md" style="background: var(--accent); color: #0E1116;">${t("save_btn")}</button>
          <select id="grids-import-callup" class="filter-select" style="font-size: 11px; padding: 4px 8px; max-width: 180px;" title="${escapeHtml(t("import_callup"))}">
            <option value="">⤓ ${escapeHtml(t("import_callup"))}</option>
            ${Object.keys(state.callup?.store?.lists || {}).sort().map(n => `<option value="${escapeHtml(n)}">${escapeHtml(n)} (${(state.callup.store.lists[n]||[]).length})</option>`).join("")}
          </select>
        </div>

        ${savedGridNames.length ? `
          <div class="mb-3 flex flex-wrap gap-1">
            ${savedGridNames.map(n => {
              const data = state.grids.store.lists[n];
              const count = data && data.assigned ? Object.keys(data.assigned).filter(k => (Array.isArray(data.assigned[k]) ? data.assigned[k].length : !!data.assigned[k])).length : 0;
              const isCurrent = state.grids.store.currentName === n;
              return `
                <span class="inline-flex items-center gap-1 px-2 py-0.5 text-[11px] rounded-md"
                      style="background: ${isCurrent?'var(--accent-bg)':'rgba(255,255,255,0.04)'}; color: ${isCurrent?'var(--accent)':'var(--text-2)'}; border: 0.5px solid var(--border);">
                  <button class="grid-load-btn" data-name="${escapeHtml(n)}" style="background: none; border: none; padding: 0; color: inherit; font-size: inherit; cursor: pointer;">
                    ${escapeHtml(n)} <span class="stat-cell" style="color: var(--text-3); font-size: 9px;">${data?.formation||""} · ${count}/11</span>
                  </button>
                  <button class="grid-delete-btn" data-name="${escapeHtml(n)}" title="${currentLang==='it'?'Cancella':'Delete'}" style="background: none; border: none; padding: 0 2px; color: var(--text-3); font-size: 14px; line-height: 1; cursor: pointer; margin-left: 2px;">×</button>
                </span>`;
            }).join("")}
          </div>` : ""}
        <div id="grids-pitch" style="position: relative; width: 100%; aspect-ratio: 9/10; border-radius: 12px; overflow: visible; box-shadow: inset 0 0 40px rgba(0,0,0,0.4);">
          ${pitchSvg}
          ${positions.map(renderSlot).join("")}
        </div>
      </div>

      <!-- RIGHT: Lista giocatori (stretta, scrollabile) -->
      <div id="grids-list-wrap" class="rounded-xl p-3" style="background: var(--surface); border: 0.5px solid var(--border); position: sticky; top: 12px; max-height: calc(100vh - 24px); overflow: hidden; display: flex; flex-direction: column;">
        <div class="flex items-center gap-2 mb-2 flex-wrap">
          <h3 class="text-sm font-bold" style="color: var(--text-1);">${t("filter_players_title")}</h3>
          <span class="ml-auto text-xs stat-cell" style="color: var(--text-3);">${available.length}</span>
        </div>
        ${selectedLabel ? `<div class="text-[11px] mb-2 px-2 py-1 rounded-md" style="background: rgba(251,191,36,0.15); color: var(--hot); border: 0.5px solid rgba(251,191,36,0.30);">${t("grid_add_to")}: <strong>${selectedLabel}</strong></div>` : `<div class="text-[10px] mb-2" style="color: var(--text-3);">${t("grid_click_slot")}</div>`}
        <input id="grids-search" type="text" placeholder="${t("search_name_club_role")}" value="${escapeHtml(state.grids.filterQ||"")}"
               class="w-full outline-none text-sm px-2 py-1.5 rounded-md mb-1.5" style="background: var(--surface-2); border: 0.5px solid var(--border); color: var(--text-1);"/>
        <div class="flex flex-wrap gap-1 mb-1.5">
          <select id="grids-filter-role" class="filter-select flex-1 min-w-[100px]" style="font-size: 11px; padding: 4px 6px;">
            <option value="">${t("filter_all_roles")}</option>
            <option value="Goalkeeper" ${state.grids.filterRole==="Goalkeeper"?"selected":""}>${t("role_gk")}</option>
            <option value="Defender" ${state.grids.filterRole==="Defender"?"selected":""}>${t("role_def")}</option>
            <option value="Midfield" ${state.grids.filterRole==="Midfield"?"selected":""}>${t("role_mid")}</option>
            <option value="Attack" ${state.grids.filterRole==="Attack"?"selected":""}>${t("role_att")}</option>
          </select>
          <select id="grids-filter-league" class="filter-select flex-1 min-w-[100px]" style="font-size: 11px; padding: 4px 6px;">
            <option value="">${t("filter_all_leagues")}</option>
            <option value="IT1" ${state.grids.filterLeague==="IT1"?"selected":""}>${t("league_short_it1")}</option>
            <option value="IT2" ${state.grids.filterLeague==="IT2"?"selected":""}>${t("league_short_it2")}</option>
            <option value="IJ1" ${state.grids.filterLeague==="IJ1"?"selected":""}>${t("league_short_ij1")}</option>
            <option value="PL1" ${state.grids.filterLeague==="PL1"?"selected":""}>${t("league_short_pl1")}</option>
            <option value="PL2" ${state.grids.filterLeague==="PL2"?"selected":""}>${t("league_short_pl2")}</option>
          </select>
        </div>
        <div class="flex flex-wrap gap-1 mb-1.5">
          <select id="grids-filter-role-specific" class="filter-select flex-1 min-w-[100px]" style="font-size: 11px; padding: 4px 6px;">
            <option value="">${t("filter_all_specific_roles")}</option>
            ${roleSpecificOptions.map(r => `<option value="${escapeHtml(r)}" ${state.grids.filterRoleSpecific===r?"selected":""}>${escapeHtml(r)}</option>`).join("")}
          </select>
          <select id="grids-filter-club" class="filter-select flex-1 min-w-[100px]" style="font-size: 11px; padding: 4px 6px;">
            <option value="">${t("filter_all_clubs")}</option>
            ${[...state.clubs].sort((a,b)=>(a.name||"").localeCompare(b.name||"")).map(c => `<option value="${c.tm_club_id}" ${String(state.grids.filterClub)===String(c.tm_club_id)?"selected":""}>${escapeHtml(c.name)}</option>`).join("")}
          </select>
        </div>
        <div class="flex gap-1 mb-1.5">
          <input id="grids-filter-year-min" type="text" inputmode="numeric" pattern="[0-9]*" maxlength="4" placeholder="${t("filter_year_min_ex")}" value="${state.grids.filterYearMin||""}"
                 class="w-1/2 outline-none text-xs px-2 py-1 rounded-md stat-cell" style="background: var(--surface-2); border: 0.5px solid var(--border); color: var(--text-1);"/>
          <input id="grids-filter-year-max" type="text" inputmode="numeric" pattern="[0-9]*" maxlength="4" placeholder="${t("filter_year_max_ex")}" value="${state.grids.filterYearMax||""}"
                 class="w-1/2 outline-none text-xs px-2 py-1 rounded-md stat-cell" style="background: var(--surface-2); border: 0.5px solid var(--border); color: var(--text-1);"/>
        </div>
        <div class="flex gap-1 mb-2">
          <input id="grids-filter-minutes-min" type="text" inputmode="numeric" pattern="[0-9]*" maxlength="5" placeholder="${t("filter_minutes_min_ex")}" value="${state.grids.filterMinutesMin||""}"
                 class="w-full outline-none text-xs px-2 py-1 rounded-md stat-cell" style="background: var(--surface-2); border: 0.5px solid var(--border); color: var(--text-1);"/>
        </div>
        <div class="overflow-y-auto flex-1" style="min-height: 0;">
          <div class="flex flex-col gap-1">
            ${available.length ? available.map(p => {
              const s = state.statsById.get(p.tm_player_id)?.seasons?.["2025"] || {};
              const mins = Object.values({ ...s.club, ...s.national }).reduce((a, x) => a + (x.minutes_played || 0), 0);
              return `
              <div class="grid-player-row flex items-center gap-2 p-1.5 rounded-md hover:bg-white/5 cursor-pointer" data-pid="${p.tm_player_id}" style="background: rgba(255,255,255,0.02);">
                <img src="${playerPhoto(p)}" class="w-9 h-9 rounded-full object-cover flex-shrink-0" style="background: var(--surface-2);"/>
                <div class="flex-1 min-w-0">
                  <div class="text-xs font-medium truncate flex items-center gap-1.5" style="color: var(--text-1);">
                    <span class="truncate">${escapeHtml(p.full_name)}</span>
                    ${birthYear(p) ? `<span class="stat-cell flex-shrink-0" style="color: var(--text-3); font-weight: 400; font-size: 10px;">'${birthYear(p).slice(-2)}</span>` : ""}
                  </div>
                  <div class="text-[10px] truncate" style="color: var(--text-3);">${escapeHtml(localizeRole(p.position_general))} · ${escapeHtml(p.current_club_name||"")}</div>
                </div>
                <span class="stat-cell flex-shrink-0" style="font-size: 11px; font-weight: 600; color: ${mins>0?'var(--accent)':'var(--text-3)'}; min-width: 38px; text-align: right;">${mins}'</span>
              </div>`;
            }).join("") : `<div class="text-xs text-center py-6" style="color: var(--text-3);">${t("no_results")}</div>`}
          </div>
        </div>
      </div>
    </div>`;

  // Listeners
  document.getElementById("grids-formation")?.addEventListener("change", e => {
    state.grids.formation = e.target.value;
    state.grids.assigned = {}; // reset perché slot diversi
    state.grids.selectedSlot = null;
    _saveGrids();
    renderGridsPanel();
  });
  document.getElementById("grids-clear")?.addEventListener("click", () => {
    if (!confirm(currentLang==="it"?"Svuotare tutta la formazione?":"Clear the whole formation?")) return;
    state.grids.assigned = {};
    state.grids.selectedSlot = null;
    _saveGrids();
    renderGridsPanel();
  });

  // Esporta PDF A4 verticale (campo + tabella riserve)
  document.getElementById("grids-export-pdf")?.addEventListener("click", async () => {
    await exportGridPDF();
  });

  // Porta tutti i giocatori della griglia in Convocazione (titolari + riserve, deduplicati)
  document.getElementById("grids-to-callup")?.addEventListener("click", () => {
    const allIds = _gridsAssignedAll();
    if (!allIds.length) {
      alert(currentLang==="it"?"La griglia è vuota.":"Grid is empty.");
      return;
    }
    const before = state.callup.currentIds.length;
    const set = new Set(state.callup.currentIds);
    let added = 0;
    for (const id of allIds) {
      if (!set.has(id)) { set.add(id); state.callup.currentIds.push(id); added++; }
    }
    if (typeof _saveCallup === "function") _saveCallup();
    else localStorage.setItem("pid_callup_active", JSON.stringify(state.callup.currentIds || []));
    alert(currentLang==="it"
      ? `Aggiunti ${added} nuovi giocatori in convocazione (totale: ${state.callup.currentIds.length}).`
      : `Added ${added} new players to call-up (total: ${state.callup.currentIds.length}).`);
  });

  // Save current grid as named list
  document.getElementById("grids-save")?.addEventListener("click", () => {
    const name = (document.getElementById("grids-list-name")?.value || "").trim();
    if (!name) { alert(currentLang==="it"?"Dai un nome alla griglia":"Give the grid a name"); return; }
    state.grids.store.lists[name] = {
      formation: state.grids.formation,
      assigned: JSON.parse(JSON.stringify(state.grids.assigned)),
    };
    state.grids.store.currentName = name;
    _saveGrids();
    renderGridsPanel();
  });

  // Importa una convocazione salvata nella griglia (round-robin per macroruolo)
  document.getElementById("grids-import-callup")?.addEventListener("change", e => {
    const name = e.target.value;
    if (!name) return;
    const lists = state.callup?.store?.lists || {};
    if (!lists[name] || !lists[name].length) {
      alert(t("import_callup_empty"));
      e.target.value = "";
      return;
    }
    const n = importCallupToGrid(name);
    e.target.value = "";
    renderGridsPanel();
    console.info(t("import_callup_done").replace("{n}", n).replace("{name}", name));
  });

  // Load a saved grid
  panel.querySelectorAll(".grid-load-btn").forEach(b => b.addEventListener("click", () => {
    const name = b.dataset.name;
    const data = state.grids.store.lists[name];
    if (!data) return;
    state.grids.formation = data.formation || "4-3-3";
    state.grids.assigned = JSON.parse(JSON.stringify(data.assigned || {}));
    state.grids.selectedSlot = null;
    state.grids.store.currentName = name;
    _saveGrids();
    renderGridsPanel();
  }));

  // Delete a saved grid
  panel.querySelectorAll(".grid-delete-btn").forEach(b => b.addEventListener("click", e => {
    e.stopPropagation();
    const name = b.dataset.name;
    if (!confirm(currentLang==="it"?`Cancellare la griglia "${name}"?`:`Delete grid "${name}"?`)) return;
    delete state.grids.store.lists[name];
    if (state.grids.store.currentName === name) state.grids.store.currentName = "";
    _saveGrids();
    renderGridsPanel();
  }));
  document.getElementById("grids-search")?.addEventListener("input", e => {
    state.grids.filterQ = e.target.value;
    renderGridsPanel();
    // Ripristina focus E caret alla fine del testo dopo il re-render
    const newInput = document.getElementById("grids-search");
    if (newInput) {
      newInput.focus();
      const len = newInput.value.length;
      newInput.setSelectionRange(len, len);
    }
  });
  document.getElementById("grids-filter-role")?.addEventListener("change", e => {
    state.grids.filterRole = e.target.value;
    renderGridsPanel();
  });
  document.getElementById("grids-filter-club")?.addEventListener("change", e => {
    state.grids.filterClub = e.target.value;
    renderGridsPanel();
  });
  document.getElementById("grids-filter-league")?.addEventListener("change", e => {
    state.grids.filterLeague = e.target.value;
    renderGridsPanel();
  });
  document.getElementById("grids-filter-role-specific")?.addEventListener("change", e => {
    state.grids.filterRoleSpecific = e.target.value;
    renderGridsPanel();
  });
  document.getElementById("grids-filter-year-min")?.addEventListener("input", e => {
    // sanitize: solo cifre
    const cleaned = (e.target.value || "").replace(/\D/g, "").slice(0, 4);
    state.grids.filterYearMin = cleaned ? parseInt(cleaned) : null;
    renderGridsPanel();
    const i = document.getElementById("grids-filter-year-min");
    if (i) { i.focus(); const l = i.value.length; i.setSelectionRange(l, l); }
  });
  document.getElementById("grids-filter-year-max")?.addEventListener("input", e => {
    const cleaned = (e.target.value || "").replace(/\D/g, "").slice(0, 4);
    state.grids.filterYearMax = cleaned ? parseInt(cleaned) : null;
    renderGridsPanel();
    const i = document.getElementById("grids-filter-year-max");
    if (i) { i.focus(); const l = i.value.length; i.setSelectionRange(l, l); }
  });
  document.getElementById("grids-filter-minutes-min")?.addEventListener("input", e => {
    const cleaned = (e.target.value || "").replace(/\D/g, "").slice(0, 5);
    state.grids.filterMinutesMin = cleaned ? parseInt(cleaned) : null;
    renderGridsPanel();
    const i = document.getElementById("grids-filter-minutes-min");
    if (i) { i.focus(); const l = i.value.length; i.setSelectionRange(l, l); }
  });

  // Click slot: toggle selezione + scroll alla lista in basso e focus search
  panel.querySelectorAll(".grid-slot").forEach(el => {
    // Evita che il click sui depth-remove × propaghi al slot
    el.addEventListener("click", e => {
      if (e.target.closest(".grid-depth-remove")) return;
      const slotId = el.dataset.slot;
      state.grids.selectedSlot = state.grids.selectedSlot === slotId ? null : slotId;
      renderGridsPanel();
      // Auto-scroll + focus
      if (state.grids.selectedSlot) {
        setTimeout(() => {
          const list = document.getElementById("grids-list-wrap");
          const search = document.getElementById("grids-search");
          if (list) list.scrollIntoView({ behavior: "smooth", block: "start" });
          if (search) {
            search.focus();
            const len = search.value.length;
            search.setSelectionRange(len, len);
          }
        }, 50);
      }
    });
  });

  // Click × inline (rimuovi giocatore dal depth chart inline al campo)
  panel.querySelectorAll(".grid-depth-remove").forEach(b => b.addEventListener("click", e => {
    e.stopPropagation();
    const slot = b.dataset.slot, idx = parseInt(b.dataset.idx);
    const arr = _gridsAssignedFor(slot);
    arr.splice(idx, 1);
    if (arr.length) state.grids.assigned[slot] = arr;
    else delete state.grids.assigned[slot];
    _saveGrids();
    renderGridsPanel();
  }));

  // Click giocatore: aggiunge alla coda dello slot selezionato (riserve)
  panel.querySelectorAll(".grid-player-row").forEach(el => el.addEventListener("click", () => {
    if (window._gdndJustDropped && Date.now() < window._gdndJustDropped) return;
    const pid = parseInt(el.dataset.pid);
    let target = state.grids.selectedSlot;
    if (!target) {
      // Niente slot selezionato → trova prima posizione vuota (no titolare)
      const firstFree = positions.find(p => _gridsAssignedFor(p.id).length === 0);
      target = firstFree ? firstFree.id : null;
    }
    if (!target) return;
    const arr = _gridsAssignedFor(target);
    if (!arr.includes(pid)) arr.push(pid);
    state.grids.assigned[target] = arr;
    _saveGrids();
    renderGridsPanel();
  }));

  // ============ DRAG & DROP ============
  if (!window._gdndPlaceholder) {
    const ph = document.createElement("div");
    ph.id = "gdnd-placeholder";
    ph.style.cssText = "height: 36px; margin-bottom: 2px; border-radius: 4px; border: 2px dashed var(--accent); background: rgba(111,224,168,0.12); box-sizing: border-box;";
    window._gdndPlaceholder = ph;
  }
  const _gdndPh = window._gdndPlaceholder;
  const _gdndRemovePh = () => { if (_gdndPh.parentNode) _gdndPh.parentNode.removeChild(_gdndPh); };
  const _gdndUpdatePh = (slot, clientY) => {
    const popup = slot.querySelector(".grid-depth-popup");
    if (!popup) { _gdndRemovePh(); return; }
    const items = Array.from(popup.querySelectorAll(".grid-depth-item"))
      .filter(it => it.style.opacity !== "0.4");
    let insertBefore = null;
    for (const it of items) {
      const r = it.getBoundingClientRect();
      if (clientY < r.top + r.height / 2) { insertBefore = it; break; }
    }
    if (insertBefore) popup.insertBefore(_gdndPh, insertBefore);
    else popup.appendChild(_gdndPh);
  };
  // Drag dalla lista giocatori (destra) -> slot del campo
  // Drag tra card della formazione -> altro slot
  panel.querySelectorAll(".grid-player-row").forEach(el => {
    el.setAttribute("draggable", "true");
    el.querySelectorAll("img").forEach(img => img.setAttribute("draggable", "false"));
    el.addEventListener("dragstart", e => {
      const pid = parseInt(el.dataset.pid);
      window._gdndDrag = { kind: "add", pid };
      try { e.dataTransfer.effectAllowed = "copy"; e.dataTransfer.setData("text/plain", String(pid)); } catch {}
      el.style.opacity = "0.4";
    });
    el.addEventListener("dragend", () => { el.style.opacity = ""; _gdndRemovePh(); });
  });
  panel.querySelectorAll(".grid-depth-item").forEach(el => {
    el.setAttribute("draggable", "true");
    el.querySelectorAll("img").forEach(img => img.setAttribute("draggable", "false"));
    el.addEventListener("dragstart", e => {
      const slot = el.dataset.slot, idx = parseInt(el.dataset.idx);
      const arr = _gridsAssignedFor(slot);
      const pid = arr[idx];
      if (!pid) { e.preventDefault(); return; }
      window._gdndDrag = { kind: "move", pid, fromSlot: slot, fromIdx: idx };
      try { e.dataTransfer.effectAllowed = "move"; e.dataTransfer.setData("text/plain", String(pid)); } catch {}
      el.style.opacity = "0.4";
    });
    el.addEventListener("dragend", () => { el.style.opacity = ""; _gdndRemovePh(); });
  });
  panel.querySelectorAll(".grid-slot").forEach(slot => {
    slot.addEventListener("dragover", e => {
      if (!window._gdndDrag) return;
      e.preventDefault();
      try { e.dataTransfer.dropEffect = window._gdndDrag.kind === "add" ? "copy" : "move"; } catch {}
      slot.style.outline = "2px dashed var(--accent)";
      slot.style.outlineOffset = "3px";
      _gdndUpdatePh(slot, e.clientY);
    });
    slot.addEventListener("dragleave", e => {
      if (!slot.contains(e.relatedTarget)) {
        slot.style.outline = "";
        slot.style.outlineOffset = "";
      }
    });
    slot.addEventListener("drop", e => {
      const d = window._gdndDrag;
      if (!d) return;
      e.preventDefault();
      e.stopPropagation();
      slot.style.outline = "";
      slot.style.outlineOffset = "";
      const dest = slot.dataset.slot;
      const a = state.grids.assigned;
      if (d.kind === "move") {
        if (d.fromSlot === dest) {
          // riordino interno: usa posizione del placeholder
          const arr = (a[d.fromSlot] || []).slice();
          const i = arr.indexOf(d.pid);
          if (i !== -1) arr.splice(i, 1);
          let insertAt = arr.length;
          if (_gdndPh.parentNode) {
            const popup = slot.querySelector(".grid-depth-popup");
            if (popup) {
              const all = Array.from(popup.children);
              const phIdx = all.indexOf(_gdndPh);
              let count = 0;
              for (let k = 0; k < phIdx; k++) {
                const ch = all[k];
                if (ch.classList && ch.classList.contains("grid-depth-item") &&
                    parseInt(ch.dataset.idx) !== d.fromIdx) count++;
              }
              insertAt = count;
            }
          }
          _gdndRemovePh();
          arr.splice(insertAt, 0, d.pid);
          a[d.fromSlot] = arr;
        } else {
          const srcArr = (a[d.fromSlot] || []).slice();
          const si = srcArr.indexOf(d.pid);
          if (si !== -1) srcArr.splice(si, 1);
          if (srcArr.length) a[d.fromSlot] = srcArr; else delete a[d.fromSlot];
          const dst = (a[dest] || []).slice();
          const exi = dst.indexOf(d.pid);
          if (exi !== -1) dst.splice(exi, 1);
          // posizione di inserimento = dove c'è il placeholder
          let insertAt = dst.length;
          if (_gdndPh.parentNode) {
            const popup = slot.querySelector(".grid-depth-popup");
            if (popup) {
              const all = Array.from(popup.children);
              const phIdx = all.indexOf(_gdndPh);
              let count = 0;
              for (let k = 0; k < phIdx; k++) {
                const ch = all[k];
                if (ch.classList && ch.classList.contains("grid-depth-item")) count++;
              }
              insertAt = count;
            }
          }
          _gdndRemovePh();
          dst.splice(insertAt, 0, d.pid);
          a[dest] = dst;
        }
      } else if (d.kind === "add") {
        // Rimuovi da eventuale altro slot
        Object.keys(a).forEach(k => {
          const arr = a[k] || [];
          const i = arr.indexOf(d.pid);
          if (i !== -1) { arr.splice(i, 1); if (arr.length) a[k] = arr; else delete a[k]; }
        });
        const dst = (a[dest] || []).slice();
        let insertAt = dst.length;
        if (_gdndPh.parentNode) {
          const popup = slot.querySelector(".grid-depth-popup");
          if (popup) {
            const all = Array.from(popup.children);
            const phIdx = all.indexOf(_gdndPh);
            let count = 0;
            for (let k = 0; k < phIdx; k++) {
              const ch = all[k];
              if (ch.classList && ch.classList.contains("grid-depth-item")) count++;
            }
            insertAt = count;
          }
        }
        _gdndRemovePh();
        dst.splice(insertAt, 0, d.pid);
        a[dest] = dst;
      }
      window._gdndDrag = null;
      window._gdndJustDropped = Date.now() + 600;
      state.grids.selectedSlot = null;  // chiude pannello "Add to"
      _saveGrids();
      renderGridsPanel();
    });
  });

  // Depth chart: ↑ ↓ ×
  panel.querySelectorAll(".grid-move-up").forEach(b => b.addEventListener("click", () => {
    const slot = b.dataset.slot, idx = parseInt(b.dataset.idx);
    const arr = _gridsAssignedFor(slot);
    if (idx <= 0) return;
    [arr[idx-1], arr[idx]] = [arr[idx], arr[idx-1]];
    state.grids.assigned[slot] = arr;
    _saveGrids();
    renderGridsPanel();
  }));
  panel.querySelectorAll(".grid-move-down").forEach(b => b.addEventListener("click", () => {
    const slot = b.dataset.slot, idx = parseInt(b.dataset.idx);
    const arr = _gridsAssignedFor(slot);
    if (idx >= arr.length - 1) return;
    [arr[idx+1], arr[idx]] = [arr[idx], arr[idx+1]];
    state.grids.assigned[slot] = arr;
    _saveGrids();
    renderGridsPanel();
  }));
  panel.querySelectorAll(".grid-remove").forEach(b => b.addEventListener("click", () => {
    const slot = b.dataset.slot, idx = parseInt(b.dataset.idx);
    const arr = _gridsAssignedFor(slot);
    arr.splice(idx, 1);
    if (arr.length) state.grids.assigned[slot] = arr;
    else delete state.grids.assigned[slot];
    _saveGrids();
    renderGridsPanel();
  }));
}

// ============ EXPORT GRID PDF (A4 verticale via html2canvas + jsPDF) ============
// Cattura l'esatto pannello Griglie come appare a schermo (cards Wyscout-style con foto)
async function exportGridPDF() {
  if (!window.jspdf) {
    alert(currentLang==="it"?"Libreria PDF non caricata.":"PDF library not loaded.");
    return;
  }
  const btn = document.getElementById("grids-export-pdf");
  if (btn) { btn.disabled = true; btn.textContent = currentLang==="it"?"Genero...":"Generating..."; }

  // Helper: carica immagine come dataURL (con opzione cerchio)
  const loadImg = (url, opts = {}) => new Promise(resolve => {
    if (!url) return resolve(null);
    const { circular = false, size = 64 } = opts;
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      try {
        const c = document.createElement("canvas");
        c.width = size; c.height = size;
        const ctx = c.getContext("2d");
        if (circular) { ctx.beginPath(); ctx.arc(size/2,size/2,size/2,0,Math.PI*2); ctx.closePath(); ctx.clip(); }
        ctx.drawImage(img, 0, 0, size, size);
        resolve(c.toDataURL("image/png"));
      } catch (e) { resolve(null); }
    };
    img.onerror = () => resolve(null);
    img.src = url;
  });

  try {
    // Sync state.grids.formation se non valido (es. "5-3-2" rimosso): forza il primo modulo disponibile
    if (!FORMATIONS[state.grids.formation]) {
      state.grids.formation = Object.keys(FORMATIONS)[0];
    }
    const positions = FORMATIONS[state.grids.formation] || FORMATIONS["4-3-3"];
    // Raccogli tutti i giocatori con metadata
    const allPlayers = [];
    for (const pos of positions) {
      const ids = _gridsAssignedFor(pos.id);
      for (let i = 0; i < ids.length; i++) {
        const pl = state.players.find(x => x.tm_player_id === ids[i]);
        if (pl) allPlayers.push({ pl, posId: pos.id, posLabel: pos.label, isStarter: i === 0, depthIdx: i });
      }
    }

    // Pre-carica foto giocatori e loghi club
    const photos = await Promise.all(allPlayers.map(x => loadImg(playerPhoto(x.pl), { circular: true, size: 64 })));
    const clubLogos = await Promise.all(allPlayers.map(x => {
      const club = state.clubsById.get(x.pl.current_club_id);
      return loadImg(club ? clubLogo(club) : null, { circular: false, size: 64 });
    }));
    // Mappa rapida: tm_player_id → indice in allPlayers (per recuperare foto/logo dopo)
    const idxByPid = new Map(allPlayers.map((x, i) => [x.pl.tm_player_id, i]));

    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF({ unit: "mm", format: "a4", orientation: "portrait" });
    const pageW = 210, pageH = 297;
    const margin = 8;

    // ====== HEADER (compatto in alto) ======
    const title = state.grids.store.currentName || (currentLang==="it"?"Formazione":"Formation");
    pdf.setFont("helvetica","bold"); pdf.setFontSize(14); pdf.setTextColor(255,255,255);

    const seasonMins = (pid) => {
      const s = state.statsById.get(pid)?.seasons?.["2025"] || {};
      return Object.values({ ...s.club, ...s.national }).reduce((a, x) => a + (x.minutes_played || 0), 0);
    };
    const footMap = { left: currentLang==="it"?"S":"L", right: currentLang==="it"?"D":"R", both: currentLang==="it"?"E":"B" };
    const dateStr = new Date().toLocaleDateString(currentLang==="it"?"it-IT":"en-GB");

    // ====== CAMPO A TUTTA PAGINA ======
    const pitchX = margin;
    const pitchY = margin;
    const pitchW = pageW - margin*2;
    const pitchH = pageH - margin*2;

    // Sfondo verde con striature alternate (effetto rasatura)
    pdf.setFillColor(15, 77, 42);
    pdf.rect(pitchX, pitchY, pitchW, pitchH, "F");
    // 5 striature alternate più chiare
    pdf.setFillColor(13, 68, 38);
    for (let s = 0; s < 5; s++) {
      const sH = pitchH / 10;
      pdf.rect(pitchX, pitchY + (2*s + 1) * sH, pitchW, sH, "F");
    }

    // Linee bianche perimetro
    pdf.setDrawColor(255,255,255); pdf.setLineWidth(0.4);
    pdf.rect(pitchX + 2, pitchY + 2, pitchW - 4, pitchH - 4);
    pdf.line(pitchX + 2, pitchY + pitchH/2, pitchX + pitchW - 2, pitchY + pitchH/2);
    // Cerchio centrocampo (ellisse)
    pdf.ellipse(pitchX + pitchW/2, pitchY + pitchH/2, pitchW * 0.10, pitchH * 0.06);
    pdf.setFillColor(255,255,255);
    pdf.circle(pitchX + pitchW/2, pitchY + pitchH/2, 0.6, "F");
    // Aree di rigore
    pdf.rect(pitchX + pitchW*0.22, pitchY + 2, pitchW*0.56, pitchH*0.13);
    pdf.rect(pitchX + pitchW*0.34, pitchY + 2, pitchW*0.32, pitchH*0.05);
    pdf.rect(pitchX + pitchW*0.22, pitchY + pitchH*0.87 - 2, pitchW*0.56, pitchH*0.13);
    pdf.rect(pitchX + pitchW*0.34, pitchY + pitchH*0.95 - 2, pitchW*0.32, pitchH*0.05);

    // Header sopra (titolo + data + modulo) renderizzato sopra il campo
    pdf.setFillColor(0, 0, 0, 0.45); // semi-transparent? jsPDF non supporta alpha direttamente, useremo overlay
    pdf.setFillColor(14, 17, 22);
    pdf.rect(pitchX, pitchY, pitchW, 11, "F");
    pdf.setFont("helvetica","bold"); pdf.setFontSize(13); pdf.setTextColor(255,255,255);
    pdf.text(title, pitchX + 4, pitchY + 7);
    pdf.setFont("helvetica","normal"); pdf.setFontSize(9); pdf.setTextColor(180,200,190);
    pdf.text(`${state.grids.formation}`, pitchX + pitchW/2, pitchY + 7, { align: "center" });
    pdf.text(dateStr, pitchX + pitchW - 4, pitchY + 7, { align: "right" });

    // ====== POSIZIONI + DEPTH CHART (card sotto ogni posizione) ======
    // Card più strette per non sovrapporsi tra posizioni vicine
    const cardW = 42;
    const playerRowH = 6;
    const cardHeaderH = 4;

    // Aree usabili: dal sotto-header al fondo (pitchY + 11 → pitchY + pitchH - 4)
    const innerTop = pitchY + 13;
    const innerBottom = pitchY + pitchH - 4;
    const innerH = innerBottom - innerTop;

    // Override SOLO per il PDF: spread più ampio sulle x per le posizioni vicine
    // Stretching simmetrico attorno al centro: nuovo_x = 50 + (x - 50) * 1.10
    const pdfPosX = (x) => Math.max(8, Math.min(92, 50 + (x - 50) * 1.10));
    // Compressione verticale: GK più basso possibile lasciando spazio per la sua card
    const Y_TOP_PAD = 0.04;
    const Y_SCALE = 0.88; // spazio utile per le posizioni
    // → posizioni mappate dentro [0.04, 0.92] dell'innerH, lasciando ~8% di spazio sotto il GK

    for (const pos of positions) {
      const ids = _gridsAssignedFor(pos.id);
      // posiziona il cerchio nel campo. y=0 → porta nostra (basso), y=100 → top
      const cx = pitchX + pitchW * (pdfPosX(pos.x) / 100);
      const yFrac = Y_TOP_PAD + Y_SCALE * ((100 - pos.y) / 100);
      const cy = innerTop + innerH * yFrac;

      // Cerchio posizione (titolare = verde pieno, vuoto = outline)
      const titularPid = ids[0];
      const p = titularPid ? state.players.find(x => x.tm_player_id === titularPid) : null;
      const circleR = 4;
      if (p) {
        pdf.setFillColor(111, 224, 168); pdf.setDrawColor(111, 224, 168); pdf.setLineWidth(0.3);
        pdf.circle(cx, cy, circleR, "F");
        pdf.setTextColor(14,17,22); pdf.setFont("helvetica","bold"); pdf.setFontSize(6);
        pdf.text(pos.label, cx, cy + 0.5, { align: "center" });
      } else {
        pdf.setDrawColor(255,255,255); pdf.setLineWidth(0.3);
        pdf.setFillColor(15,77,42);
        pdf.circle(cx, cy, circleR);
        pdf.setTextColor(255,255,255); pdf.setFont("helvetica","bold"); pdf.setFontSize(6);
        pdf.text(pos.label, cx, cy + 0.5, { align: "center" });
      }

      if (!ids.length) continue;

      // Card depth chart: SEMPRE sotto il cerchio della posizione (anche per GK)
      const cardH = cardHeaderH + ids.length * playerRowH + 1;
      let cardX = cx - cardW / 2;
      let cardY = cy + circleR + 1;

      // Clamp orizzontale dentro al campo
      if (cardX < pitchX + 3) cardX = pitchX + 3;
      if (cardX + cardW > pitchX + pitchW - 3) cardX = pitchX + pitchW - 3 - cardW;
      // Clamp verticale: la card può sborderare leggermente fuori dal campo (max footer-edge)
      const maxBottomY = pageH - margin - 1; // appena sopra il footer
      if (cardY + cardH > maxBottomY) {
        // Sposta la card più in alto, ma mantienila sotto il cerchio se possibile
        cardY = maxBottomY - cardH;
        // Se la card si sovrappone troppo al cerchio, mettila sopra
        if (cardY < cy + circleR - 0.5) {
          cardY = cy - circleR - 1 - cardH;
          if (cardY < innerTop) cardY = innerTop;
        }
      }

      // Sfondo card scuro semi-opaco simulato
      pdf.setFillColor(14, 17, 22);
      pdf.roundedRect(cardX, cardY, cardW, cardH, 1.5, 1.5, "F");
      pdf.setDrawColor(60, 70, 65); pdf.setLineWidth(0.2);
      pdf.roundedRect(cardX, cardY, cardW, cardH, 1.5, 1.5);

      // Header card: posizione + count
      pdf.setFont("helvetica","bold"); pdf.setFontSize(6); pdf.setTextColor(111, 224, 168);
      pdf.text(pos.label, cardX + 2, cardY + 3);
      pdf.setFont("helvetica","normal"); pdf.setFontSize(5); pdf.setTextColor(150, 170, 160);
      pdf.text(`${ids.length} ${currentLang==="it"?"giocator"+(ids.length===1?"e":"i"):"player"+(ids.length===1?"":"s")}`, cardX + cardW - 2, cardY + 3, { align: "right" });

      // Righe giocatori
      for (let i = 0; i < ids.length; i++) {
        const idx = idxByPid.get(ids[i]);
        if (idx == null) continue;
        const pl = allPlayers[idx].pl;
        const isStarter = i === 0;
        const yr = (birthYear(pl) || "").toString().slice(-2);
        const club = state.clubsById.get(pl.current_club_id);
        const clubAbbr = (pl.current_club_name || "").replace(/\s(SFC|FC|SC|Club|Riad)\b.*$/, "").slice(0, 12);
        const mins = seasonMins(pl.tm_player_id);
        const foot = footMap[(pl.foot||"").toLowerCase()] || "—";

        const rowY = cardY + cardHeaderH + i * playerRowH;
        // Sfondo titolare (sottile verde tenue)
        if (isStarter) {
          pdf.setFillColor(28, 50, 38);
          pdf.rect(cardX + 1, rowY + 0.3, cardW - 2, playerRowH - 0.5, "F");
        }

        // Numero depth
        pdf.setFont("helvetica","bold"); pdf.setFontSize(6); pdf.setTextColor(isStarter ? 111 : 130, isStarter ? 224 : 145, isStarter ? 168 : 150);
        pdf.text(`${i+1}`, cardX + 3, rowY + 4);

        // Foto cerchio (4mm)
        const ph = photos[idx];
        if (ph) { try { pdf.addImage(ph, "PNG", cardX + 5.5, rowY + 1.2, 4, 4); } catch (e) {} }

        // Nome (cognome)
        const lastName = (pl.full_name || "").split(" ").slice(-1)[0] || pl.full_name;
        pdf.setFont("helvetica","bold"); pdf.setFontSize(7); pdf.setTextColor(255,255,255);
        pdf.text(`${lastName} '${yr}`, cardX + 11, rowY + 3, { maxWidth: 22 });

        // Sub: club abbr + foot + min
        pdf.setFont("helvetica","normal"); pdf.setFontSize(5.5); pdf.setTextColor(170, 180, 175);
        const subParts = [];
        if (clubAbbr) subParts.push(clubAbbr);
        if (foot) subParts.push(foot);
        pdf.text(subParts.join(" · "), cardX + 11, rowY + 5.4, { maxWidth: 24 });

        // Logo club a destra
        const cLogo = clubLogos[idx];
        if (cLogo) { try { pdf.addImage(cLogo, "PNG", cardX + cardW - 11.5, rowY + 1, 4, 4); } catch (e) {} }

        // Minuti
        pdf.setFont("helvetica","bold"); pdf.setFontSize(5.8);
        if (mins > 0) pdf.setTextColor(111, 224, 168); else pdf.setTextColor(150,160,155);
        pdf.text(`${mins}'`, cardX + cardW - 2, rowY + 4.8, { align: "right" });
      }
    }

    // Footer compatto in basso (sopra il campo)
    pdf.setFillColor(14, 17, 22);
    pdf.rect(pitchX, pitchY + pitchH - 5, pitchW, 5, "F");
    pdf.setFontSize(6); pdf.setFont("helvetica","normal"); pdf.setTextColor(150,170,160);
    pdf.text("Saudi Players Hub", pitchX + 4, pitchY + pitchH - 1.5);
    pdf.text(dateStr, pitchX + pitchW - 4, pitchY + pitchH - 1.5, { align: "right" });

    const safeName = (title || "formazione").replace(/[^a-zA-Z0-9_-]/g, "_");
    pdf.save(`${safeName}.pdf`);
  } catch (e) {
    console.error("PDF export error:", e);
    alert(currentLang==="it"?"Errore durante l'export PDF: "+e.message:"PDF export error: "+e.message);
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = currentLang==="it"?"Esporta PDF":"Export PDF"; }
  }
}

// ============ LIST (elenco verticale ranking-style) ============
state.list = state.list || {
  filters: { q: "", role: "", club: "", sort: "goals_desc",
             league: "", minutesMin: null, yearMin: null, yearMax: null },
};
// Migrazione: assicura che i nuovi filtri esistano anche su state.list già esistente
if (state.list.filters.league === undefined) state.list.filters.league = "";
if (state.list.filters.minutesMin === undefined) state.list.filters.minutesMin = null;
if (state.list.filters.yearMin === undefined) state.list.filters.yearMin = null;
if (state.list.filters.yearMax === undefined) state.list.filters.yearMax = null;

function renderListPanel() {
  const panel = document.getElementById("list-panel");
  if (!panel) return;
  const f = state.list.filters;

  // Helper per stats stagione (definito prima del filter così posso usarlo nel filtro minuti)
  const seasonAgg = (pid, key) => {
    const s = state.statsById.get(pid)?.seasons?.["2025"] || {};
    return Object.values({ ...s.club, ...s.national }).reduce((a, x) => a + (x[key] || 0), 0);
  };

  // Filtraggio
  let items = state.players.filter(p => {
    if (f.role && (p.position_general || "").toLowerCase() !== f.role.toLowerCase()) return false;
    if (f.club && String(p.current_club_id) !== String(f.club)) return false;
    if (f.league) {
      const club = state.clubsById.get(p.current_club_id) || state.clubsById.get(String(p.current_club_id));
      const lg = String(club?.league_id || "OTHER");
      const isKnownLeague = (lg === "IT1" || lg === "IT2" || lg === "IJ1" || lg === "PL1" || lg === "PL2");
      const match = (f.league === "OTHER") ? !isKnownLeague : (lg === f.league);
      if (!match) return false;
    }
    const yr = parseInt(birthYear(p));
    if (f.yearMin != null && (!yr || yr < f.yearMin)) return false;
    if (f.yearMax != null && (!yr || yr > f.yearMax)) return false;
    if (f.minutesMin && seasonAgg(p.tm_player_id, "minutes_played") < f.minutesMin) return false;
    if (f.q && !matchPlayer(p, f.q)) return false;
    return true;
  });

  // Ordinamento
  if (f.sort === "goals_desc") items.sort((a,b) => totalGoals2025(b.tm_player_id) - totalGoals2025(a.tm_player_id));
  else if (f.sort === "assists_desc") items.sort((a,b) => seasonAgg(b.tm_player_id, "assists") - seasonAgg(a.tm_player_id, "assists"));
  else if (f.sort === "apps_desc") items.sort((a,b) => seasonAgg(b.tm_player_id, "apps") - seasonAgg(a.tm_player_id, "apps"));
  else if (f.sort === "minutes_desc") items.sort((a,b) => seasonAgg(b.tm_player_id, "minutes_played") - seasonAgg(a.tm_player_id, "minutes_played"));
  else if (f.sort === "age_asc") items.sort((a,b) => (a.age||999) - (b.age||999));
  else if (f.sort === "age_desc") items.sort((a,b) => (b.age||0) - (a.age||0));
  else if (f.sort === "club") items.sort((a,b) => (a.current_club_name||"").localeCompare(b.current_club_name||""));
  else items.sort((a,b) => (a.full_name||"").localeCompare(b.full_name||""));

  // Colonne: rank · foto · #maglia · nome+anno · ruolo · club · apps · gol · ass · min · piede · età
  const GRID = "36px 44px 44px 1fr 130px 170px 56px 56px 56px 64px 78px 46px";

  const renderRow = (p, rank) => {
    const club = state.clubsById.get(p.current_club_id);
    const clubLogoUrl = clubLogo(club);
    const goals = totalGoals2025(p.tm_player_id);
    const stats = state.statsById.get(p.tm_player_id);
    const season = stats?.seasons?.["2025"] || {};
    const apps = Object.values({...season.club, ...season.national}).reduce((a,s)=>a+(s.apps||0), 0);
    const assists = Object.values({...season.club, ...season.national}).reduce((a,s)=>a+(s.assists||0), 0);
    const minutes = Object.values({...season.club, ...season.national}).reduce((a,s)=>a+(s.minutes_played||0), 0);

    const rankColor = rank <= 3 ? "var(--accent)" : (rank <= 10 ? "var(--text-1)" : "var(--text-3)");
    return `
      <div class="list-row" data-pid="${p.tm_player_id}" style="display: grid; grid-template-columns: ${GRID}; gap: 10px; align-items: center; padding: 8px 14px; border-bottom: 0.5px solid var(--border); cursor: pointer;">
        <span class="stat-cell" style="font-size: 16px; font-weight: 700; color: ${rankColor}; text-align: right;">#${rank}</span>
        <img src="${playerPhoto(p)}" alt="" class="rounded-md object-cover" style="width: 36px; height: 36px; background: var(--surface-2);"
             onerror="this.onerror=null;this.src='https://ui-avatars.com/api/?name=${encodeURIComponent(p.full_name||'?')}&size=128&background=1A1F26&color=6FE0A8&bold=true&font-size=0.45'"/>
        <span class="stat-cell" style="text-align: center; font-size: 13px; font-weight: 700; color: ${p.shirt_number?'var(--accent)':'var(--text-3)'};">${p.shirt_number ? '#'+p.shirt_number : "—"}</span>
        <div style="min-width: 0;">
          <div class="truncate" style="font-size: 13px; font-weight: 600; color: var(--text-1);">${escapeHtml(p.full_name)}</div>
          <div class="truncate text-[11px] stat-cell" style="color: var(--text-3);">${birthYear(p) || ""}</div>
        </div>
        <span class="truncate" style="font-size: 12px; color: var(--text-2);">${escapeHtml(localizeRole(p.position_specific || p.position_general))}</span>
        <div class="flex items-center gap-2 min-w-0">
          ${clubLogoUrl ? `<img src="${clubLogoUrl}" class="w-5 h-5 object-contain flex-shrink-0"/>` : ""}
          <span class="truncate text-[12px]" style="color: var(--text-2);">${escapeHtml(p.current_club_name||"")}</span>
        </div>
        <div class="text-center stat-cell" style="font-size: 13px; color: var(--text-1);">${apps}</div>
        <div class="text-center stat-cell" style="font-size: 13px; font-weight: 600; color: ${goals>=5?'var(--hot)':(goals?'var(--text-1)':'var(--text-3)')};">${goals}</div>
        <div class="text-center stat-cell" style="font-size: 13px; color: ${assists?'var(--text-1)':'var(--text-3)'};">${assists}</div>
        <div class="text-center stat-cell" style="font-size: 12px; color: ${minutes?'var(--text-2)':'var(--text-3)'};">${minutes}'</div>
        <div class="text-center stat-cell" style="font-size: 12px; font-weight: 600; color: ${p.foot?'var(--text-2)':'var(--text-3)'};">${footFull(p.foot) || "—"}</div>
        <div class="text-right stat-cell" style="font-size: 11px; color: var(--text-3);">${p.age||""}</div>
      </div>`;
  };

  // Header colonne cliccabili per ordinare
  const sortFor = (col) => {
    // Mappa colonna → sort key
    const map = {
      name: "name",
      club: "club",
      apps: "apps_desc",
      goals: "goals_desc",
      assists: "assists_desc",
      minutes: "minutes_desc",
      age: f.sort === "age_asc" ? "age_desc" : "age_asc",
    };
    return map[col];
  };
  const arrow = (col) => {
    const target = sortFor(col);
    if (f.sort === target) return ` <span style="color: var(--accent);">↓</span>`;
    if (col === "age" && (f.sort === "age_asc" || f.sort === "age_desc")) {
      return f.sort === "age_asc"
        ? ` <span style="color: var(--accent);">↑</span>`
        : ` <span style="color: var(--accent);">↓</span>`;
    }
    return "";
  };
  const headerCell = (label, col, align="center") => {
    const isActive = f.sort === sortFor(col) || (col === "age" && (f.sort === "age_asc" || f.sort === "age_desc"));
    const color = isActive ? "var(--accent)" : "var(--text-3)";
    return `<button class="sort-header" data-col="${col}" style="font-size: 10px; color: ${color}; text-transform: uppercase; letter-spacing: 0.06em; text-align: ${align}; background: none; border: none; cursor: pointer; padding: 0; font-weight: 500;">${label}${arrow(col)}</button>`;
  };

  const headerRow = `
    <div style="display: grid; grid-template-columns: ${GRID}; gap: 10px; align-items: center; padding: 6px 14px; border-bottom: 0.5px solid var(--border-strong);">
      <span style="font-size: 10px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.06em; text-align: right;">#</span>
      <span></span>
      <span style="font-size: 10px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.06em; text-align: center;">${t("shirt")}</span>
      ${headerCell(t("col_player"), "name", "left")}
      <span style="font-size: 10px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.06em; text-align: left;">${t("position")}</span>
      ${headerCell(t("club"), "club", "left")}
      ${headerCell(t("apps"), "apps")}
      ${headerCell(t("goals"), "goals")}
      ${headerCell(t("assists"), "assists")}
      ${headerCell(t("col_min"), "minutes")}
      <span style="font-size: 10px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.06em; text-align: center;">${t("col_foot")}</span>
      ${headerCell(t("col_age"), "age", "right")}
    </div>`;

  const clubOptions = [...state.clubs].sort((a,b)=>(a.name||"").localeCompare(b.name||""))
    .map(c => `<option value="${c.tm_club_id}" ${String(f.club)===String(c.tm_club_id)?"selected":""}>${escapeHtml(c.name)}</option>`).join("");

  panel.innerHTML = `
    <div class="rounded-xl mb-4 p-4" style="background: var(--surface); border: 0.5px solid var(--border);">
      <div class="flex items-center gap-2 mb-3">
        <h3 class="text-base font-bold" style="color: var(--text-1);">${currentLang==="it"?"Lista giocatori":"Player list"}</h3>
        <span class="ml-auto text-xs stat-cell" style="color: var(--text-3);">${items.length} ${currentLang==="it"?"giocatori":"players"}</span>
      </div>
      <div class="flex flex-wrap gap-2">
        <input id="list-search" type="text" placeholder="${currentLang==="it"?"Cerca nome o club...":"Search name or club..."}" value="${escapeHtml(f.q||"")}"
               class="flex-1 min-w-[180px] outline-none text-sm px-3 py-1.5 rounded-md" style="background: var(--surface-2); border: 0.5px solid var(--border); color: var(--text-1);"/>
        <select id="list-role" class="filter-select" style="font-size: 12px;">
          <option value="">${t("filter_all_roles")}</option>
          <option value="Goalkeeper" ${f.role==="Goalkeeper"?"selected":""}>${t("role_gk")}</option>
          <option value="Defender" ${f.role==="Defender"?"selected":""}>${t("role_def")}</option>
          <option value="Midfield" ${f.role==="Midfield"?"selected":""}>${t("role_mid")}</option>
          <option value="Attack" ${f.role==="Attack"?"selected":""}>${t("role_att")}</option>
        </select>
        <select id="list-league" class="filter-select" style="font-size: 12px;">
          <option value="">${t("filter_all_leagues")}</option>
          <option value="IT1" ${f.league==="IT1"?"selected":""}>${t("league_it1")}</option>
          <option value="IT2" ${f.league==="IT2"?"selected":""}>${t("league_it2")}</option>
          <option value="IJ1" ${f.league==="IJ1"?"selected":""}>${t("league_ij1")}</option>
          <option value="PL1" ${f.league==="PL1"?"selected":""}>${t("league_pl1")}</option>
          <option value="PL2" ${f.league==="PL2"?"selected":""}>${t("league_pl2")}</option>
        </select>
        <select id="list-club" class="filter-select" style="font-size: 12px;">
          <option value="">${t("filter_all_clubs")}</option>
          ${clubOptions}
        </select>
        <input id="list-year-min" type="text" inputmode="numeric" pattern="[0-9]*" maxlength="4" placeholder="${t("filter_year_min")}" value="${f.yearMin||""}"
               class="w-24 outline-none text-sm px-2 py-1.5 rounded-md stat-cell" style="background: var(--surface-2); border: 0.5px solid var(--border); color: var(--text-1);"/>
        <input id="list-year-max" type="text" inputmode="numeric" pattern="[0-9]*" maxlength="4" placeholder="${t("filter_year_max")}" value="${f.yearMax||""}"
               class="w-24 outline-none text-sm px-2 py-1.5 rounded-md stat-cell" style="background: var(--surface-2); border: 0.5px solid var(--border); color: var(--text-1);"/>
        <input id="list-minutes-min" type="text" inputmode="numeric" pattern="[0-9]*" maxlength="5" placeholder="${t("filter_minutes_min")}" value="${f.minutesMin||""}"
               class="w-28 outline-none text-sm px-2 py-1.5 rounded-md stat-cell" style="background: var(--surface-2); border: 0.5px solid var(--border); color: var(--text-1);"/>
        <select id="list-sort" class="filter-select" style="font-size: 12px;">
          <option value="goals_desc" ${f.sort==="goals_desc"?"selected":""}>${t("sort_goals")}</option>
          <option value="assists_desc" ${f.sort==="assists_desc"?"selected":""}>${t("sort_assists")}</option>
          <option value="apps_desc" ${f.sort==="apps_desc"?"selected":""}>${t("sort_apps")}</option>
          <option value="minutes_desc" ${f.sort==="minutes_desc"?"selected":""}>${t("sort_minutes")}</option>
          <option value="name" ${f.sort==="name"?"selected":""}>${t("sort_name")}</option>
          <option value="age_asc" ${f.sort==="age_asc"?"selected":""}>${t("sort_age_asc")}</option>
          <option value="age_desc" ${f.sort==="age_desc"?"selected":""}>${t("sort_age_desc")}</option>
          <option value="club" ${f.sort==="club"?"selected":""}>${t("sort_club")}</option>
        </select>
      </div>
    </div>

    <div class="rounded-xl overflow-hidden" style="background: var(--surface); border: 0.5px solid var(--border);">
      ${headerRow}
      <div style="max-height: 70vh; overflow-y: auto;">
        ${items.length ? items.map((p,i) => renderRow(p, i+1)).join("") : `<div class="text-center py-12" style="color: var(--text-3);">${t("no_results")}</div>`}
      </div>
    </div>`;

  // Listeners
  document.getElementById("list-search")?.addEventListener("input", e => {
    state.list.filters.q = e.target.value;
    renderListPanel();
    const newInput = document.getElementById("list-search");
    if (newInput) {
      newInput.focus();
      const len = newInput.value.length;
      newInput.setSelectionRange(len, len);
    }
  });
  document.getElementById("list-role")?.addEventListener("change", e => { state.list.filters.role = e.target.value; renderListPanel(); });
  document.getElementById("list-club")?.addEventListener("change", e => { state.list.filters.club = e.target.value; renderListPanel(); });
  document.getElementById("list-league")?.addEventListener("change", e => { state.list.filters.league = e.target.value; renderListPanel(); });
  document.getElementById("list-sort")?.addEventListener("change", e => { state.list.filters.sort = e.target.value; renderListPanel(); });
  document.getElementById("list-year-min")?.addEventListener("input", e => {
    const cleaned = (e.target.value || "").replace(/\D/g, "").slice(0, 4);
    state.list.filters.yearMin = cleaned ? parseInt(cleaned) : null;
    renderListPanel();
    const i = document.getElementById("list-year-min");
    if (i) { i.focus(); const l = i.value.length; i.setSelectionRange(l, l); }
  });
  document.getElementById("list-year-max")?.addEventListener("input", e => {
    const cleaned = (e.target.value || "").replace(/\D/g, "").slice(0, 4);
    state.list.filters.yearMax = cleaned ? parseInt(cleaned) : null;
    renderListPanel();
    const i = document.getElementById("list-year-max");
    if (i) { i.focus(); const l = i.value.length; i.setSelectionRange(l, l); }
  });
  document.getElementById("list-minutes-min")?.addEventListener("input", e => {
    const cleaned = (e.target.value || "").replace(/\D/g, "").slice(0, 5);
    state.list.filters.minutesMin = cleaned ? parseInt(cleaned) : null;
    renderListPanel();
    const i = document.getElementById("list-minutes-min");
    if (i) { i.focus(); const l = i.value.length; i.setSelectionRange(l, l); }
  });
  panel.querySelectorAll(".list-row").forEach(row => row.addEventListener("click", () => openPlayerModal(parseInt(row.dataset.pid))));
  panel.querySelectorAll(".sort-header").forEach(btn => btn.addEventListener("click", () => {
    const col = btn.dataset.col;
    state.list.filters.sort = sortFor(col);
    renderListPanel();
  }));
}

// ============ COMPARE ============
function renderCompare() {
  // Helper per estrarre stat aggregate del giocatore (stesse logiche usate nei card)
  const getCompareStats = (pid) => {
    const sd = state.statsById.get(pid)?.seasons?.["2025"] || {};
    const sumSec = (sec) => Object.values(sec || {}).reduce((acc, s) => ({
      apps: (acc.apps||0) + (s.apps||0),
      goals: (acc.goals||0) + (s.goals||0),
      assists: (acc.assists||0) + (s.assists||0),
      minutes: (acc.minutes||0) + (s.minutes_played||0),
    }), { apps:0, goals:0, assists:0, minutes:0 });
    const cClub = sumSec(sd.club);
    const cNat = sumSec(sd.national);
    const natCareer = state.statsById.get(pid)?.national_career || [];
    return {
      seasonApps: cClub.apps + cNat.apps,
      seasonGoals: cClub.goals + cNat.goals,
      seasonAssists: cClub.assists + cNat.assists,
      seasonMinutes: cClub.minutes + cNat.minutes,
      natTotalCaps: natCareer.reduce((a, n) => a + (n.caps || 0), 0),
      natTotalGoals: natCareer.reduce((a, n) => a + (n.goals || 0), 0),
      natACaps: (natCareer.find(n => n.category === "A")?.caps) || 0,
    };
  };

  const slots = document.querySelectorAll(".compare-slot");
  slots.forEach((slot, i) => {
    const pid = state.compareIds[i];
    const p = pid ? state.players.find(x => x.tm_player_id === pid) : null;
    if (!p) {
      slot.innerHTML = `<div class="flex-1 flex flex-col items-center justify-center py-12" style="color: var(--text-3);">
        <div class="w-14 h-14 rounded-full flex items-center justify-center text-2xl" style="background: var(--surface-2);">+</div>
        <div class="mt-3 text-xs">${t("compare_drag")}</div>
      </div>`;
      return;
    }
    // Aggregati stagione 25/26
    const sd = state.statsById.get(p.tm_player_id)?.seasons?.["2025"] || {};
    const sumSec = (sec) => Object.values(sec || {}).reduce((acc, s) => ({
      apps: (acc.apps||0) + (s.apps||0),
      goals: (acc.goals||0) + (s.goals||0),
      assists: (acc.assists||0) + (s.assists||0),
      minutes: (acc.minutes||0) + (s.minutes_played||0),
    }), { apps:0, goals:0, assists:0, minutes:0 });
    const cClub = sumSec(sd.club);
    const cNat = sumSec(sd.national);
    const seasonApps = cClub.apps + cNat.apps;
    const seasonGoals = cClub.goals + cNat.goals;
    const seasonAssists = cClub.assists + cNat.assists;
    const seasonMinutes = cClub.minutes + cNat.minutes;
    // Caps nazionale all-time (somma di tutte le categorie)
    const natCareer = state.statsById.get(p.tm_player_id)?.national_career || [];
    const natTotalCaps = natCareer.reduce((a, n) => a + (n.caps || 0), 0);
    const natTotalGoals = natCareer.reduce((a, n) => a + (n.goals || 0), 0);
    const natACaps = (natCareer.find(n => n.category === "A")?.caps) || 0;
    const club = state.clubsById.get(p.current_club_id);
    const clubLogoUrl = clubLogo(club);
    slot.innerHTML = `
      <div class="flex items-center gap-3">
        <img src="${playerPhoto(p)}" class="w-14 h-14 rounded-lg object-cover" style="background: var(--surface-2);"/>
        <div class="flex-1 min-w-0">
          <div class="font-semibold text-sm truncate" style="color: var(--text-1);">${escapeHtml(p.full_name)} <span class="stat-cell" style="color: var(--text-3); font-weight: 400; font-size: 12px;">${birthYear(p) ? "'"+birthYear(p).slice(-2) : ""}</span></div>
          <div class="text-xs truncate flex items-center gap-1.5" style="color: var(--text-3);">
            ${clubLogoUrl ? `<img src="${clubLogoUrl}" class="w-3.5 h-3.5 object-contain flex-shrink-0"/>` : ""}
            <span class="truncate">${escapeHtml(p.current_club_name||"")}</span>
            <span class="ml-1 px-1 py-0.5 rounded" style="background: var(--accent-bg); color: var(--accent); font-size: 10px;">${escapeHtml(localizeRole(p.position_specific||p.position_general))}</span>
          </div>
        </div>
        <button class="text-lg" style="color: var(--text-3);" data-remove="${i}">×</button>
      </div>

      <!-- Anagrafica -->
      <div class="grid grid-cols-3 gap-2 mt-3 text-center">
        <div class="p-2 rounded" style="background: var(--surface-2);"><div class="text-[10px] uppercase tracking-wider" style="color: var(--text-3);">${t("age")}</div><div class="font-semibold stat-cell" style="color: var(--text-1);">${p.age||"—"}</div></div>
        <div class="p-2 rounded" style="background: var(--surface-2);"><div class="text-[10px] uppercase tracking-wider" style="color: var(--text-3);">${t("height")}</div><div class="font-semibold stat-cell" style="color: var(--text-1);">${p.height_cm ? p.height_cm+"cm" : "—"}</div></div>
        <div class="p-2 rounded" style="background: var(--surface-2);"><div class="text-[10px] uppercase tracking-wider" style="color: var(--text-3);">${t("foot")}</div><div class="font-semibold" style="color: var(--text-1);">${({left: t("foot_left"), right: t("foot_right"), both: t("foot_both")})[p.foot] || "—"}</div></div>
      </div>

      <!-- Stagione 25/26: presenze + minuti -->
      <div class="mt-3">
        <div class="text-[10px] uppercase tracking-wider mb-1.5" style="color: var(--text-3); font-weight: 500;">${currentLang==="it"?"Stagione 25/26":"Season 25/26"}</div>
        <div class="grid grid-cols-4 gap-1.5 text-center">
          <div class="p-1.5 rounded" style="background: rgba(111,224,168,0.06); border: 0.5px solid rgba(111,224,168,0.15);">
            <div class="text-[9px] uppercase" style="color: var(--text-3);">${t("apps")}</div>
            <div class="font-bold stat-cell text-base" style="color: var(--text-1); line-height: 1;">${seasonApps}</div>
          </div>
          <div class="p-1.5 rounded" style="background: rgba(251,191,36,0.06); border: 0.5px solid rgba(251,191,36,0.15);">
            <div class="text-[9px] uppercase" style="color: var(--text-3);">${t("goals")}</div>
            <div class="font-bold stat-cell text-base" style="color: ${seasonGoals>=5?'var(--hot)':'var(--text-1)'}; line-height: 1;">${seasonGoals}</div>
          </div>
          <div class="p-1.5 rounded" style="background: rgba(96,165,250,0.06); border: 0.5px solid rgba(96,165,250,0.15);">
            <div class="text-[9px] uppercase" style="color: var(--text-3);">${t("assists")}</div>
            <div class="font-bold stat-cell text-base" style="color: var(--text-1); line-height: 1;">${seasonAssists}</div>
          </div>
          <div class="p-1.5 rounded" style="background: rgba(167,139,250,0.06); border: 0.5px solid rgba(167,139,250,0.15);">
            <div class="text-[9px] uppercase" style="color: var(--text-3);">${t("minutes_short")}</div>
            <div class="font-bold stat-cell text-base" style="color: var(--text-1); line-height: 1;">${seasonMinutes}</div>
          </div>
        </div>
      </div>

      <!-- Carriera nazionale: caps totali + caps senior -->
      <div class="mt-3">
        <div class="text-[10px] uppercase tracking-wider mb-1.5" style="color: var(--text-3); font-weight: 500;">${currentLang==="it"?"Carriera nazionale (all-time)":"National career (all-time)"}</div>
        <div class="grid grid-cols-3 gap-1.5 text-center">
          <div class="p-1.5 rounded" style="background: rgba(244,114,182,0.06); border: 0.5px solid rgba(244,114,182,0.20);">
            <div class="text-[9px] uppercase" style="color: var(--text-3);">${currentLang==="it"?"Pres. tot":"Total caps"}</div>
            <div class="font-bold stat-cell text-base" style="color: var(--comp-nat); line-height: 1;">${natTotalCaps}</div>
          </div>
          <div class="p-1.5 rounded" style="background: rgba(111,224,168,0.06); border: 0.5px solid rgba(111,224,168,0.20);">
            <div class="text-[9px] uppercase" style="color: var(--text-3);">${currentLang==="it"?"Pres. naz. A":"Senior caps"}</div>
            <div class="font-bold stat-cell text-base" style="color: var(--accent); line-height: 1;">${natACaps}</div>
          </div>
          <div class="p-1.5 rounded" style="background: rgba(251,191,36,0.06); border: 0.5px solid rgba(251,191,36,0.20);">
            <div class="text-[9px] uppercase" style="color: var(--text-3);">${currentLang==="it"?"Gol naz.":"Nat. goals"}</div>
            <div class="font-bold stat-cell text-base" style="color: ${natTotalGoals>=5?'var(--hot)':'var(--text-1)'}; line-height: 1;">${natTotalGoals}</div>
          </div>
        </div>
      </div>
    `;
    slot.querySelector("[data-remove]")?.addEventListener("click", () => {
      state.compareIds[i] = null;
      renderCompare();
    });
  });

  // ============ HEAD-TO-HEAD (riepilogo "vincitore" sotto i 2 slot) ============
  const h2hCont = document.getElementById("compare-stats");
  if (!h2hCont) return;
  const pid0 = state.compareIds[0];
  const pid1 = state.compareIds[1];
  const p0 = pid0 ? state.players.find(x => x.tm_player_id === pid0) : null;
  const p1 = pid1 ? state.players.find(x => x.tm_player_id === pid1) : null;
  if (!p0 || !p1) {
    h2hCont.innerHTML = "";
    return;
  }
  const s0 = getCompareStats(pid0);
  const s1 = getCompareStats(pid1);

  // Lista metriche da confrontare. higherIsBetter = true (più è alto, meglio è).
  // Per "age" si potrebbe fare l'opposto, ma non lo includiamo qui.
  const metrics = [
    { key: "seasonApps",    label: t("apps"),                color: "var(--accent)" },
    { key: "seasonGoals",   label: t("goals"),               color: "var(--hot)" },
    { key: "seasonAssists", label: t("assists"),             color: "var(--info)" },
    { key: "seasonMinutes", label: t("minutes_short"),       color: "#A78BFA" },
    { key: "natTotalCaps",  label: t("compare_total_caps"),  color: "var(--comp-nat)" },
    { key: "natACaps",      label: t("compare_senior_caps"), color: "var(--accent)" },
    { key: "natTotalGoals", label: t("compare_nat_goals"),   color: "var(--hot)" },
  ];

  // Conteggio vittorie per giocatore
  let wins0 = 0, wins1 = 0, ties = 0;
  metrics.forEach(m => {
    const v0 = s0[m.key], v1 = s1[m.key];
    if (v0 > v1) wins0++;
    else if (v1 > v0) wins1++;
    else ties++;
  });
  const overallWinner = wins0 > wins1 ? 0 : wins1 > wins0 ? 1 : -1; // -1 = pari

  // Costruzione tabella
  const cellWinStyle = "background: rgba(111,224,168,0.14); color: var(--accent); border: 0.5px solid rgba(111,224,168,0.45); font-weight: 800;";
  const cellLoseStyle = "background: rgba(255,255,255,0.02); color: var(--text-3); border: 0.5px solid var(--border);";
  const cellTieStyle = "background: rgba(96,165,250,0.08); color: var(--info); border: 0.5px solid rgba(96,165,250,0.30); font-weight: 700;";

  const rows = metrics.map(m => {
    const v0 = s0[m.key], v1 = s1[m.key];
    const eq = v0 === v1;
    const w = eq ? -1 : (v0 > v1 ? 0 : 1);
    const minutesSuffix = m.key === "seasonMinutes" ? "'" : "";
    return `
      <div style="display: grid; grid-template-columns: 1fr 60px 1fr; gap: 8px; align-items: center; padding: 6px 10px; border-bottom: 0.5px solid var(--border);">
        <div class="stat-cell" style="text-align: right; padding: 6px 10px; border-radius: 8px; ${eq ? cellTieStyle : (w===0 ? cellWinStyle : cellLoseStyle)}; font-size: 16px;">${v0}${minutesSuffix}${eq ? "" : (w===0 ? " ★" : "")}</div>
        <div style="text-align: center; font-size: 10px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.06em; font-weight: 600;">${escapeHtml(m.label)}</div>
        <div class="stat-cell" style="text-align: left; padding: 6px 10px; border-radius: 8px; ${eq ? cellTieStyle : (w===1 ? cellWinStyle : cellLoseStyle)}; font-size: 16px;">${eq ? "" : (w===1 ? "★ " : "")}${v1}${minutesSuffix}</div>
      </div>`;
  }).join("");

  // Header con avatar dei 2 giocatori e indicatore vincitore globale
  const winnerName = overallWinner === 0 ? p0.full_name : overallWinner === 1 ? p1.full_name : t("compare_tied");
  const winnerLabel = overallWinner === -1
    ? `<span style="background: rgba(96,165,250,0.10); color: var(--info); padding: 4px 10px; border-radius: 999px; border: 0.5px solid rgba(96,165,250,0.30); font-size: 12px; font-weight: 700;">${escapeHtml(t("compare_tied"))} · ${wins0}–${wins1}</span>`
    : `<span style="background: var(--accent-bg); color: var(--accent); padding: 4px 10px; border-radius: 999px; border: 0.5px solid rgba(111,224,168,0.40); font-size: 12px; font-weight: 700;">★ ${escapeHtml(winnerName)} · ${overallWinner===0 ? wins0 : wins1}–${overallWinner===0 ? wins1 : wins0}</span>`;

  h2hCont.innerHTML = `
    <div class="rounded-xl mt-2" style="background: var(--surface); border: 0.5px solid var(--border); overflow: hidden;">
      <div style="display: grid; grid-template-columns: 1fr auto 1fr; gap: 12px; align-items: center; padding: 14px 16px; background: linear-gradient(135deg, rgba(111,224,168,0.04) 0%, rgba(96,165,250,0.03) 100%); border-bottom: 0.5px solid var(--border-strong);">
        <div style="display: flex; align-items: center; gap: 8px; justify-content: flex-end; min-width: 0;">
          <span class="font-semibold truncate" style="color: var(--text-1); font-size: 13px;">${escapeHtml(p0.full_name)}</span>
          <img src="${playerPhoto(p0)}" class="w-7 h-7 rounded-full object-cover flex-shrink-0" style="background: var(--surface-2);"/>
        </div>
        <div style="text-align: center;">
          <div style="font-size: 9px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px;">${t("compare_h2h")}</div>
          ${winnerLabel}
        </div>
        <div style="display: flex; align-items: center; gap: 8px; min-width: 0;">
          <img src="${playerPhoto(p1)}" class="w-7 h-7 rounded-full object-cover flex-shrink-0" style="background: var(--surface-2);"/>
          <span class="font-semibold truncate" style="color: var(--text-1); font-size: 13px;">${escapeHtml(p1.full_name)}</span>
        </div>
      </div>
      ${rows}
    </div>`;
}

// ============ MINUTAGGI (per competizione, stagione corrente) ============
const MINUTES_STORAGE_KEY = "saudi_minutes_v1";
state.minutes = state.minutes || {
  selectedIds: (() => { try { return JSON.parse(localStorage.getItem(MINUTES_STORAGE_KEY) || "[]"); } catch { return []; } })(),
  filters: { q: "", role: "", league: "", club: "", yearMin: null, yearMax: null },
  sortBy: "minutes", // minutes | role | club | age
};
// Migrazione difensiva: garantisce che sortBy esista
if (!state.minutes.sortBy) state.minutes.sortBy = "minutes";
function _saveMinutesSelection() {
  try { localStorage.setItem(MINUTES_STORAGE_KEY, JSON.stringify(state.minutes.selectedIds || [])); } catch {}
}

// Aggrega le competizioni del giocatore nella stagione corrente.
// Ritorna [{code, name, type:"club"|"national", apps, minutes}, ...] ordinato per minuti desc.
// Mappatura codici TM → label leggibile e nome esteso (per tooltip/PDF)
const COMP_LABEL = {
  IT1: { short: "SA",   full: "Serie A" },
  IT2: { short: "SB",   full: "Serie B" },
  IJ1: { short: "P1",   full: "Primavera 1" },
  PL1: { short: "EKS",  full: "Ekstraklasa" },
  PL2: { short: "1L",   full: "1 Liga (Polonia)" },
  CIT: { short: "CIT",  full: "Coppa Italia" },
  SCI: { short: "SCI",  full: "Supercoppa Italiana" },
  ACLE: { short: "UCL", full: "UEFA Champions League" },
  ACL2: { short: "UEL", full: "UEFA Europa League" },
  ES1:  { short: "UECL", full: "UEFA Conference League" },
  // Codici noti (per tooltip; non hanno colonna dedicata, finiscono in ESTERO)
  BOS1: { short: "BOS1", full: "Bosnia Premijer Liga" },
  BIHP: { short: "BIHP", full: "Bosnia Kup BiH" },
  CR19: { short: "CR19", full: "Croatia Prva HNL — Juniori" },
  AGUC: { short: "AGUC", full: "Arabian Gulf Cup" },
  GOCU: { short: "GOCU", full: "Gulf Cup of Nations" },
  BE1:  { short: "BE1",  full: "Belgium Jupiler Pro League" },
  CCB:  { short: "CCB",  full: "Belgium Croky Cup" },
  FR1:  { short: "FR1",  full: "France Ligue 1" },
  FR2:  { short: "FR2",  full: "France Ligue 2" },
  FRC:  { short: "FRC",  full: "Coupe de France" },
  EL:   { short: "EL",   full: "UEFA Europa League" },
  "23AF": { short: "U23 AC", full: "AFC U23 Asian Cup" },
  AL21: { short: "AL21", full: "Albania Kategoria Superiore U21" },
  ALB1: { short: "ALB1", full: "Albania Kategoria Superiore" },
};
// Codici club esclusi del tutto (non mostrati)
// KLUB=Club Friendly, FIC1=Club Friendly Cup, ARCP=Arab Cup, PLIC=Pro League International Cup
const CLUB_EXCLUDE = new Set(["KLUB", "FIC1", "ARCP", "PLIC"]);
// Override testo competizione: usa il nome curato in COMP_LABEL.full se disponibile, altrimenti il valore dal dataset
function _compName(code, fallback) {
  if (COMP_LABEL[code]?.full) return COMP_LABEL[code].full;
  return fallback || code;
}
// Codici club che hanno colonna dedicata; tutto il resto va sotto "ESTERO"
const KNOWN_CLUB_CODES = new Set(["IT1", "IT2", "IJ1", "PL1", "PL2", "ACLE", "ACL2", "CIT", "SCI"]);
const FOREIGN_CODE = "ESTERO";
// Ordine fisso colonne club: Serie A → Serie B → Primavera → Ekstraklasa → 1 Liga → UCL → UEL → UECL → Coppa Italia → Supercoppa → Estero
const CLUB_PRIORITY_ORDER = ["IT1", "IT2", "IJ1", "PL1", "PL2", "ACLE", "ACL2", "CIT", "SCI", FOREIGN_CODE];
// Ordine team_category nazionali
const NAT_CATEGORY_ORDER = ["A", "U23", "U22", "U21", "U20", "U19", "U18", "U17", "U16", "U15", "Olympic"];

function _minutesByCompetition(pid) {
  const stats = state.statsById.get(pid);
  const seasons = stats?.seasons || {};
  // SOLO la stagione 2025/26: se il giocatore non ha dati 2025/26 → mostra zeri (no fallback alla stagione precedente)
  const cur = seasons["2025"] || { club: {}, national: {} };
  const out = [];
  // Club: aggrega ACLE/AFCL, BE1+BPO4+POBE (Belgio: campionato + play-off + spareggi),
  // escludi KLUB/FIC1/ARCP/PLIC, raggruppa altri sotto ESTERO
  const clubMerged = {};
  for (const [code, s] of Object.entries(cur.club || {})) {
    if (CLUB_EXCLUDE.has(code)) continue;
    let outCode = code;
    if (code === "AFCL" || code === "ACLE") outCode = "ACLE";
    if (code === "BPO4" || code === "POBE") outCode = "BE1";
    if (!KNOWN_CLUB_CODES.has(outCode)) outCode = FOREIGN_CODE;
    if (!clubMerged[outCode]) {
      const label = COMP_LABEL[outCode];
      const fullName = outCode === FOREIGN_CODE
        ? (currentLang === "it" ? "Campionati esteri" : "Foreign leagues")
        : (label?.full || s.competition_name || outCode);
      clubMerged[outCode] = { name: fullName, apps: 0, minutes: 0 };
    }
    clubMerged[outCode].apps += (s.apps || 0);
    clubMerged[outCode].minutes += (s.minutes_played || 0);
  }
  for (const [code, agg] of Object.entries(clubMerged)) {
    out.push({ code, name: agg.name, type: "club", apps: agg.apps, minutes: agg.minutes });
  }
  // Nazionale: MERGE per team_category (es. tutte le partite U23 in un'unica colonna)
  const natMerged = {};
  for (const [code, s] of Object.entries(cur.national || {})) {
    const cat = s.team_category || "?";
    if (!natMerged[cat]) natMerged[cat] = { apps: 0, minutes: 0 };
    natMerged[cat].apps += (s.apps || 0);
    natMerged[cat].minutes += (s.minutes_played || 0);
  }
  for (const [cat, agg] of Object.entries(natMerged)) {
    out.push({
      code: cat,  // direttamente la categoria (A, U23, U21, ...)
      name: (currentLang === "it" ? `Nazionale ${cat}` : `National ${cat}`),
      type: "national",
      category: cat,
      apps: agg.apps,
      minutes: agg.minutes,
    });
  }
  // Filtra entry a zero (no apps E no minuti)
  return out.filter(x => (x.apps || 0) > 0 || (x.minutes || 0) > 0);
}

// Ordina i record di colonne secondo il layout richiesto:
// CLUB priority (SPL → SFD → SSL → CHAMP → CHAMP 2 → King's Cup → Supercup → Estero) → nazionali per categoria
function _sortMinutesCols(cols) {
  return [...cols].sort((a, b) => {
    if (a.type !== b.type) return a.type === "club" ? -1 : 1;
    if (a.type === "club") {
      const ra = CLUB_PRIORITY_ORDER.indexOf(a.code);
      const rb = CLUB_PRIORITY_ORDER.indexOf(b.code);
      if (ra >= 0 || rb >= 0) {
        if (ra < 0) return 1;
        if (rb < 0) return -1;
        return ra - rb;
      }
      return (b.totalMinutes || 0) - (a.totalMinutes || 0);
    }
    // entrambi nazionali → ordine categoria
    const ra = NAT_CATEGORY_ORDER.indexOf(a.category);
    const rb = NAT_CATEGORY_ORDER.indexOf(b.category);
    if (ra < 0 && rb < 0) return (a.category || "").localeCompare(b.category || "");
    if (ra < 0) return 1;
    if (rb < 0) return -1;
    return ra - rb;
  });
}

// Label colonna (può contenere \n per line break)
function _minutesColLabel(col) {
  if (col.type === "national") return col.category || "?"; // solo la categoria: A, U23, U20, ...
  if (col.code === FOREIGN_CODE) return currentLang === "it" ? "Estero" : "Foreign";
  return COMP_LABEL[col.code]?.short || col.code;
}
// Tooltip / nome esteso
function _minutesColFull(col) {
  if (col.type === "national") {
    return currentLang === "it" ? `Nazionale ${col.category || "?"}` : `National ${col.category || "?"}`;
  }
  if (col.code === FOREIGN_CODE) return currentLang === "it" ? "Campionati esteri" : "Foreign leagues";
  return COMP_LABEL[col.code]?.full || col.name || col.code;
}

function _minutesPlayerTotals(pid) {
  const list = _minutesByCompetition(pid);
  return {
    apps: list.reduce((a, x) => a + (x.apps || 0), 0),
    minutes: list.reduce((a, x) => a + (x.minutes || 0), 0),
    breakdown: list,
  };
}

function _applyMinutesFilters(players) {
  const f = state.minutes.filters;
  return players.filter(p => {
    const by = parseInt(birthYear(p));
    if (f.yearMin != null && (!by || by < f.yearMin)) return false;
    if (f.yearMax != null && (!by || by > f.yearMax)) return false;
    if (f.role && (p.position_general || "").toLowerCase() !== f.role.toLowerCase()) return false;
    if (f.club && String(p.current_club_id) !== String(f.club)) return false;
    if (f.league) {
      const club = state.clubsById.get(p.current_club_id) || state.clubsById.get(String(p.current_club_id));
      const lg = String(club?.league_id || "OTHER");
      const isKnownLeague = (lg === "IT1" || lg === "IT2" || lg === "IJ1" || lg === "PL1" || lg === "PL2");
      const match = (f.league === "OTHER") ? !isKnownLeague : (lg === f.league);
      if (!match) return false;
    }
    if (f.q && !matchPlayer(p, f.q)) return false;
    return true;
  });
}

function renderMinutesPanel() {
  const panel = document.getElementById("minutes-panel");
  if (!panel) return;
  const f = state.minutes.filters;
  const filtered = _applyMinutesFilters(state.players);
  const selectedSet = new Set(state.minutes.selectedIds);
  const seasonMinsTotal = (pid) => _minutesPlayerTotals(pid).minutes;

  // Funzione di ordinamento condivisa: minuti / ruolo / club / età
  const ROLE_ORDER = { Goalkeeper: 0, Defender: 1, Midfield: 2, Attack: 3 };
  const sortMode = state.minutes.sortBy || "minutes";
  // Se sortMode è "comp:<key>", estraggo la chiave della competizione su cui ordinare
  const compSortKey = sortMode.startsWith("comp:") ? sortMode.slice(5) : null;
  // Cache: minuti per giocatore nella competizione di sort (evita ricalcoli durante il sort)
  const _compMinsCache = new Map();
  const _minsForComp = (pid, key) => {
    let pc = _compMinsCache.get(pid);
    if (!pc) {
      pc = new Map();
      _minutesByCompetition(pid).forEach(c => pc.set(`${c.type}:${c.code}:${c.name}`, c.minutes || 0));
      _compMinsCache.set(pid, pc);
    }
    return pc.get(key) || 0;
  };
  const sortPlayers = (list) => {
    const arr = [...list];
    arr.sort((a, b) => {
      if (compSortKey) {
        // Ordina per minuti nella competizione specificata (desc)
        const ma = _minsForComp(a.tm_player_id, compSortKey);
        const mb = _minsForComp(b.tm_player_id, compSortKey);
        if (ma !== mb) return mb - ma;
        return (a.full_name || "").localeCompare(b.full_name || "");
      }
      if (sortMode === "minutes") {
        return seasonMinsTotal(b.tm_player_id) - seasonMinsTotal(a.tm_player_id);
      }
      if (sortMode === "role") {
        const ra = ROLE_ORDER[a.position_general] ?? 99;
        const rb = ROLE_ORDER[b.position_general] ?? 99;
        if (ra !== rb) return ra - rb;
        return (a.full_name || "").localeCompare(b.full_name || "");
      }
      if (sortMode === "club") {
        const ca = (a.current_club_name || "").toLowerCase();
        const cb = (b.current_club_name || "").toLowerCase();
        if (ca !== cb) return ca.localeCompare(cb);
        return (a.full_name || "").localeCompare(b.full_name || "");
      }
      if (sortMode === "age") {
        // Più giovani prima → birthYear desc
        const ya = parseInt(birthYear(a)) || 0;
        const yb = parseInt(birthYear(b)) || 0;
        if (ya !== yb) return yb - ya;
        return (a.full_name || "").localeCompare(b.full_name || "");
      }
      return 0;
    });
    return arr;
  };

  // Lista giocatori selezionati ordinata secondo sortBy
  const selectedList = sortPlayers(
    state.minutes.selectedIds
      .map(id => state.players.find(p => p.tm_player_id === id))
      .filter(Boolean)
  );

  // Card piccola per ogni giocatore nella lista a sinistra
  const renderLeftRow = (p) => {
    const club = state.clubsById.get(p.current_club_id);
    const logo = clubLogo(club);
    const inSel = selectedSet.has(p.tm_player_id);
    const mins = seasonMinsTotal(p.tm_player_id);
    return `
      <div class="minutes-row flex items-center gap-2 p-1.5 rounded-md hover:bg-white/5" data-pid="${p.tm_player_id}" style="cursor: pointer;">
        <img src="${playerPhoto(p)}" class="w-9 h-9 rounded-full object-cover flex-shrink-0" style="background: var(--surface-2);"/>
        <div class="flex-1 min-w-0">
          <div class="text-[12px] font-semibold truncate" style="color: var(--text-1); line-height: 1.2;">${escapeHtml(p.full_name)}</div>
          <div class="text-[10px] truncate flex items-center gap-1 mt-0.5" style="color: var(--text-3); line-height: 1.2;">
            ${logo ? `<img src="${logo}" class="w-3 h-3 object-contain"/>` : ""}
            <span class="truncate">${escapeHtml(p.current_club_name||"")}</span>
          </div>
        </div>
        <span class="stat-cell text-[10px] font-semibold" style="color: ${mins>0?'var(--accent)':'var(--text-3)'};">${mins}'</span>
        <button class="minutes-toggle text-base font-bold w-6 h-6 rounded flex items-center justify-center" style="${inSel?"background: rgba(239,68,68,0.15); color: #EF4444;":"background: var(--accent-bg); color: var(--accent);"}; font-size: 14px; line-height: 1;">${inSel?"−":"+"}</button>
      </div>`;
  };

  // ============ TABELLA: header competizioni + righe giocatore + somma/media ============
  // Costruisco l'unione delle competizioni giocate dai selezionati
  const compMap = new Map();
  selectedList.forEach(p => {
    _minutesByCompetition(p.tm_player_id).forEach(c => {
      const key = `${c.type}:${c.code}:${c.name}`;
      if (!compMap.has(key)) compMap.set(key, { key, code: c.code, name: c.name, type: c.type, category: c.category, totalMinutes: 0, totalApps: 0 });
      const e = compMap.get(key);
      e.totalApps += c.apps || 0;
      e.totalMinutes += c.minutes || 0;
    });
  });
  // Ordinamento custom: club priority (SPL → SFD → CHAMP → CHAMP 2 → King's Cup → Supercup) → altri club desc → nazionali (A → U23 → U22 → ...)
  const cols = _sortMinutesCols([...compMap.values()]);
  // Indice della prima colonna nazionale → per applicare il divider visivo
  const firstNatIdx = cols.findIndex(c => c.type === "national");

  // Per cella: cerco match in player breakdown via stessa chiave (type:code:name)
  const playerKeyed = new Map(selectedList.map(p => {
    const m = new Map();
    _minutesByCompetition(p.tm_player_id).forEach(c => m.set(`${c.type}:${c.code}:${c.name}`, c));
    return [p.tm_player_id, m];
  }));

  // Totali per giocatore
  const playerTotals = new Map(selectedList.map(p => [p.tm_player_id, _minutesPlayerTotals(p.tm_player_id)]));

  // Somma/media globali
  const sumApps = [...playerTotals.values()].reduce((a, t) => a + t.apps, 0);
  const sumMin  = [...playerTotals.values()].reduce((a, t) => a + t.minutes, 0);
  const avgApps = selectedList.length ? Math.round(sumApps / selectedList.length) : 0;
  const avgMin  = selectedList.length ? Math.round(sumMin / selectedList.length) : 0;

  // Stile divider sx (border più marcato + padding extra) sulla prima colonna nazionale
  const dividerLeft = (idx) => idx === firstNatIdx ? "border-left: 1.5px solid var(--border-strong); padding-left: 12px;" : "";

  // Header celle competizione (sticky-top per restare visibili durante lo scroll verticale)
  // Cliccabili: ordinano la tabella per minuti in quella competizione (toggle).
  const HEADER_STICKY = "position: sticky; top: 0; z-index: 3; background: var(--surface);";
  const headerCols = cols.map((col, idx) => {
    const logo = competitionLogo(col.code);
    const flag = col.type === "national" ? _photoUrl("photos/branding/logo.png") : null;
    const label = _minutesColLabel(col);
    const isActiveSort = compSortKey === col.key;
    const activeBg = isActiveSort
      ? "background: linear-gradient(180deg, rgba(111,224,168,0.18) 0%, rgba(111,224,168,0.06) 100%); border-bottom: 2px solid var(--accent);"
      : "";
    const indicator = isActiveSort
      ? `<span class="stat-cell" style="font-size: 11px; color: var(--accent); font-weight: 800; line-height: 1;">↓</span>`
      : "";
    return `
      <th class="minutes-col-header" data-col-key="${escapeHtml(col.key)}" title="${escapeHtml(_minutesColFull(col))} — ${escapeHtml(t("sort_by"))} ${escapeHtml(t("sort_by_minutes"))}" style="padding: 8px 6px; border-bottom: 0.5px solid var(--border); vertical-align: bottom; min-width: 64px; cursor: pointer; user-select: none; ${dividerLeft(idx)} ${HEADER_STICKY} ${activeBg}">
        <div style="display: flex; flex-direction: column; align-items: center; gap: 4px;">
          ${logo ? `<img src="${logo}" style="width: 26px; height: 26px; object-fit: contain;"/>`
                 : flag ? `<img src="${flag}" style="width: 26px; height: 26px; object-fit: cover; border-radius: 4px;"/>`
                        : `<div style="width: 26px; height: 26px; border-radius: 4px; background: rgba(255,255,255,0.04); display: flex; align-items: center; justify-content: center; color: var(--text-3); font-size: 11px;">·</div>`}
          <div style="display: flex; align-items: center; gap: 3px;">
            ${indicator}
            <span class="stat-cell" style="font-size: 9px; color: ${isActiveSort?'var(--accent)':'var(--text-3)'}; text-transform: uppercase; letter-spacing: 0.04em; font-weight: ${isActiveSort?'800':'600'}; max-width: 80px; line-height: 1.15; text-align: center; white-space: pre-line;">${escapeHtml(label)}</span>
          </div>
        </div>
      </th>`;
  }).join("");

  // Cella numerica (apps sopra, min' sotto)
  const numCell = (apps, mins, idx, extraStyle = "") => {
    const div = dividerLeft(idx);
    if (!apps && !mins) {
      return `<td style="padding: 8px 6px; text-align: center; border-bottom: 0.5px solid var(--border); color: var(--text-3); font-size: 13px; ${div}${extraStyle}">—</td>`;
    }
    return `
      <td style="padding: 8px 6px; text-align: center; border-bottom: 0.5px solid var(--border); ${div}${extraStyle}">
        <div class="stat-cell" style="font-size: 14px; font-weight: 700; color: var(--text-1); font-variant-numeric: tabular-nums; line-height: 1;">${apps}</div>
        <div class="stat-cell" style="font-size: 12px; font-weight: 700; color: var(--accent); font-variant-numeric: tabular-nums; line-height: 1; margin-top: 3px;">${mins}'</div>
      </td>`;
  };

  // Riga giocatore
  const renderPlayerRow = (p) => {
    const tot = playerTotals.get(p.tm_player_id);
    const breakdown = playerKeyed.get(p.tm_player_id);
    const club = state.clubsById.get(p.current_club_id);
    const clubLogoUrl = clubLogo(club);
    const yr = birthYear(p);
    const cells = cols.map((col, idx) => {
      const c = breakdown.get(col.key);
      return numCell(c?.apps || 0, c?.minutes || 0, idx);
    }).join("");
    return `
      <tr>
        <td style="padding: 8px 12px; border-bottom: 0.5px solid var(--border); min-width: 220px; max-width: 280px;">
          <div style="display: flex; align-items: center; gap: 10px; min-width: 0;">
            <img src="${playerPhoto(p)}" class="w-9 h-9 rounded-full object-cover flex-shrink-0" style="background: var(--surface-2); border: 0.5px solid var(--border-strong);"/>
            <div class="min-w-0 flex-1">
              <div class="flex items-baseline gap-1.5 min-w-0">
                <button class="minutes-open-modal truncate" data-pid="${p.tm_player_id}" style="background: none; border: none; padding: 0; color: var(--text-1); font-size: 13px; font-weight: 700; cursor: pointer; text-align: left; line-height: 1.2; min-width: 0;">${escapeHtml(p.full_name)}</button>
                ${yr ? `<span class="stat-cell flex-shrink-0" style="font-size: 11px; color: var(--text-3); font-weight: 500;">'${yr.slice(-2)}</span>` : ""}
              </div>
              <div class="flex items-center gap-1.5 mt-0.5 text-[10px]" style="color: var(--text-3); line-height: 1.2;">
                ${clubLogoUrl ? `<img src="${clubLogoUrl}" class="w-3 h-3 object-contain flex-shrink-0"/>` : ""}
                <span class="truncate">${escapeHtml(p.current_club_name||"")}</span>
                <span>·</span>
                <span style="color: var(--accent); font-weight: 500; white-space: nowrap;">${escapeHtml(localizeRole(p.position_general))}</span>
              </div>
            </div>
            <button class="minutes-remove flex-shrink-0" data-pid="${p.tm_player_id}" title="${currentLang==='it'?'Rimuovi':'Remove'}" style="background: rgba(239,68,68,0.10); color: #EF4444; border: 0.5px solid rgba(239,68,68,0.20); width: 20px; height: 20px; border-radius: 5px; font-size: 12px; line-height: 1; cursor: pointer;">×</button>
          </div>
        </td>
        ${cells}
        <td style="padding: 8px 10px; text-align: center; border-bottom: 0.5px solid var(--border); border-left: 0.5px solid var(--border); background: rgba(111,224,168,0.04);">
          <div class="stat-cell" style="font-size: 16px; font-weight: 800; color: var(--text-1); font-variant-numeric: tabular-nums; line-height: 1;">${tot.apps}</div>
          <div class="stat-cell" style="font-size: 14px; font-weight: 800; color: var(--accent); font-variant-numeric: tabular-nums; line-height: 1; margin-top: 3px;">${tot.minutes}'</div>
        </td>
      </tr>`;
  };

  // Riga somma e media (per ogni competizione + totale finale)
  // bottomOffset: pixel da sotto (0 per AVG, ~46 per SUM se AVG presente) → sticky bottom
  const buildAggRow = (label, getApps, getMin, totApps, totMin, accentRow = false, bottomOffset = 0) => {
    // Background opaco per sticky (no see-through)
    const bg = accentRow ? "#1A2540" : "#1F242D";
    const labelBg = accentRow ? "#1A2942" : "#21272F";
    const totBg = accentRow ? "#1B3A2C" : "#1D3328";
    const stickyStyle = `position: sticky; bottom: ${bottomOffset}px; z-index: 2;`;
    const cells = cols.map((col, idx) => {
      const a = getApps(col);
      const m = getMin(col);
      const div = dividerLeft(idx);
      if (!a && !m) return `<td style="padding: 8px 6px; text-align: center; border-top: 0.5px solid var(--border-strong); color: var(--text-3); font-size: 13px; background: ${bg}; ${div}${stickyStyle}">—</td>`;
      return `
        <td style="padding: 8px 6px; text-align: center; border-top: 0.5px solid var(--border-strong); background: ${bg}; ${div}${stickyStyle}">
          <div class="stat-cell" style="font-size: 14px; font-weight: 800; color: var(--text-1); font-variant-numeric: tabular-nums; line-height: 1;">${a}</div>
          <div class="stat-cell" style="font-size: 12px; font-weight: 800; color: var(--accent); font-variant-numeric: tabular-nums; line-height: 1; margin-top: 3px;">${m}'</div>
        </td>`;
    }).join("");
    return `
      <tr>
        <td style="padding: 10px 12px; border-top: 0.5px solid var(--border-strong); background: ${labelBg}; font-size: 11px; color: var(--text-2); text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700; ${stickyStyle}">
          ${escapeHtml(label)}
        </td>
        ${cells}
        <td style="padding: 8px 10px; text-align: center; border-top: 0.5px solid var(--border-strong); border-left: 0.5px solid var(--border); background: ${totBg}; ${stickyStyle}">
          <div class="stat-cell" style="font-size: 15px; font-weight: 800; color: var(--text-1); font-variant-numeric: tabular-nums; line-height: 1;">${totApps}</div>
          <div class="stat-cell" style="font-size: 13px; font-weight: 800; color: var(--accent); font-variant-numeric: tabular-nums; line-height: 1; margin-top: 3px;">${totMin}'</div>
        </td>
      </tr>`;
  };
  // Quando ci sono entrambe SUM e AVG (≥2 giocatori): SUM va sopra AVG, quindi SUM ha bottom=AVG_height
  const AGG_ROW_PX = 46;
  const hasAvg = selectedList.length >= 2;
  const sumRow = buildAggRow(
    currentLang==="it"?"Somma":"Total",
    (col) => col.totalApps,
    (col) => col.totalMinutes,
    sumApps, sumMin, false,
    hasAvg ? AGG_ROW_PX : 0
  );
  const avgRow = buildAggRow(
    currentLang==="it"?"Media":"Avg",
    (col) => Math.round(col.totalApps / selectedList.length),
    (col) => Math.round(col.totalMinutes / selectedList.length),
    avgApps, avgMin, true,
    0
  );

  // Tabella completa con scroll interno (sticky header + sticky SUM/AVG in fondo)
  const renderTable = () => `
    <div class="rounded-xl" style="background: var(--surface); border: 0.5px solid var(--border); overflow: auto; max-height: calc(100vh - 200px);">
      <table style="width: 100%; border-collapse: collapse; min-width: ${220 + cols.length * 70 + 90}px;">
        <thead>
          <tr>
            <th style="padding: 12px 12px 10px; text-align: left; border-bottom: 0.5px solid var(--border); font-size: 10px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.06em; font-weight: 700; min-width: 220px; ${HEADER_STICKY}">
              ${currentLang==="it"?"Giocatore":"Player"}
            </th>
            ${headerCols}
            <th style="padding: 12px 10px 10px; text-align: center; border-bottom: 0.5px solid var(--border); border-left: 0.5px solid var(--border); font-size: 10px; color: var(--accent); text-transform: uppercase; letter-spacing: 0.06em; font-weight: 800; min-width: 90px; background: rgba(20,30,24,0.95); ${HEADER_STICKY}">
              ${currentLang==="it"?"Totale":"Total"}
            </th>
          </tr>
        </thead>
        <tbody>
          ${selectedList.map(renderPlayerRow).join("")}
          ${selectedList.length >= 1 ? sumRow : ""}
          ${hasAvg ? avgRow : ""}
        </tbody>
      </table>
    </div>`;

  panel.innerHTML = `
    <div style="display: grid; grid-template-columns: 240px 1fr; gap: 14px; align-items: start;">

      <!-- COLONNA SINISTRA stretta: filtri + lista -->
      <div class="rounded-xl p-3" style="background: var(--surface); border: 0.5px solid var(--border); position: sticky; top: 12px; max-height: calc(100vh - 24px); overflow: hidden; display: flex; flex-direction: column;">
        <div class="flex items-center gap-2 mb-2">
          <h3 class="text-sm font-bold" style="color: var(--text-1);">${currentLang==="it"?"Giocatori":"Players"}</h3>
          <span class="ml-auto text-[10px] stat-cell" style="color: var(--text-3);">${filtered.length}</span>
        </div>

        <input id="minutes-search" type="text" placeholder="${currentLang==="it"?"Cerca…":"Search…"}" value="${escapeHtml(f.q||"")}"
               class="outline-none text-xs px-2 py-1.5 rounded-md mb-1.5" style="background: var(--surface-2); border: 0.5px solid var(--border); color: var(--text-1);"/>

        <select id="minutes-role" class="filter-select mb-1.5" style="font-size: 11px; padding: 4px 8px;">
          <option value="">${t("filter_all_roles")}</option>
          <option value="Goalkeeper" ${f.role==="Goalkeeper"?"selected":""}>${t("role_gk")}</option>
          <option value="Defender" ${f.role==="Defender"?"selected":""}>${t("role_def")}</option>
          <option value="Midfield" ${f.role==="Midfield"?"selected":""}>${t("role_mid")}</option>
          <option value="Attack" ${f.role==="Attack"?"selected":""}>${t("role_att")}</option>
        </select>

        <select id="minutes-league" class="filter-select mb-1.5" style="font-size: 11px; padding: 4px 8px;">
          <option value="">${t("filter_all_leagues")}</option>
          <option value="IT1" ${f.league==="IT1"?"selected":""}>${t("league_it1")}</option>
          <option value="IT2" ${f.league==="IT2"?"selected":""}>${t("league_it2")}</option>
          <option value="IJ1" ${f.league==="IJ1"?"selected":""}>${t("league_ij1")}</option>
          <option value="PL1" ${f.league==="PL1"?"selected":""}>${t("league_pl1")}</option>
          <option value="PL2" ${f.league==="PL2"?"selected":""}>${t("league_pl2")}</option>
        </select>

        <select id="minutes-club" class="filter-select mb-1.5" style="font-size: 11px; padding: 4px 8px;">
          <option value="">${t("filter_all_clubs")}</option>
          ${[...state.clubs].sort((a,b)=>(a.name||"").localeCompare(b.name||"")).map(c => `<option value="${c.tm_club_id}" ${String(f.club)===String(c.tm_club_id)?"selected":""}>${escapeHtml(c.name)}</option>`).join("")}
        </select>

        <div class="flex gap-1 mb-2">
          <input id="minutes-year-min" type="text" inputmode="numeric" pattern="[0-9]*" maxlength="4" placeholder="${t("filter_year_min")}" value="${f.yearMin||""}"
                 class="flex-1 min-w-0 outline-none text-xs px-2 py-1 rounded-md stat-cell" style="background: var(--surface-2); border: 0.5px solid var(--border); color: var(--text-1);"/>
          <input id="minutes-year-max" type="text" inputmode="numeric" pattern="[0-9]*" maxlength="4" placeholder="${t("filter_year_max")}" value="${f.yearMax||""}"
                 class="flex-1 min-w-0 outline-none text-xs px-2 py-1 rounded-md stat-cell" style="background: var(--surface-2); border: 0.5px solid var(--border); color: var(--text-1);"/>
        </div>

        <div id="minutes-list-scroll" class="overflow-y-auto" style="flex: 1; min-height: 0;">
          ${[...filtered].sort((a, b) => seasonMinsTotal(b.tm_player_id) - seasonMinsTotal(a.tm_player_id)).slice(0, 200).map(renderLeftRow).join("") || `<div class="text-center text-xs py-6" style="color: var(--text-3);">${t("no_results")}</div>`}
        </div>
      </div>

      <!-- COLONNA DESTRA larga: tabella competizioni × giocatori -->
      <div style="display: flex; flex-direction: column; gap: 10px;">
        ${selectedList.length === 0 ? `
          <div class="rounded-xl p-10 text-center" style="background: var(--surface); border: 0.5px dashed var(--border-strong); color: var(--text-3); font-size: 14px;">
            ${currentLang==="it"
              ? "Aggiungi giocatori dalla colonna a sinistra per vedere presenze e minuti per ogni competizione giocata in stagione."
              : "Add players from the left column to see appearances and minutes per competition this season."}
          </div>
        ` : `
          <!-- Dropdown "Ordina per" (applica solo alla tabella sotto) -->
          <div class="rounded-md flex items-center gap-2 flex-wrap" style="background: rgba(111,224,168,0.06); border: 0.5px solid rgba(111,224,168,0.20); padding: 6px 10px;">
            <span style="font-size: 10px; color: var(--accent); text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700;">${escapeHtml(t("sort_by"))}</span>
            <select id="minutes-sort" class="filter-select" style="font-size: 12px; padding: 4px 8px; font-weight: 600;">
              <option value="minutes" ${state.minutes.sortBy==="minutes"?"selected":""}>⏱ ${t("sort_by_minutes")}</option>
              <option value="role"    ${state.minutes.sortBy==="role"   ?"selected":""}>👥 ${t("sort_by_role")}</option>
              <option value="club"    ${state.minutes.sortBy==="club"   ?"selected":""}>🏛 ${t("sort_by_club")}</option>
              <option value="age"     ${state.minutes.sortBy==="age"    ?"selected":""}>🎂 ${t("sort_by_age")}</option>
            </select>
            <span style="font-size: 10px; color: var(--text-3);">·</span>
            <span style="font-size: 10px; color: var(--accent); text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700;">${escapeHtml(t("import_callup"))}</span>
            <select id="minutes-import-callup" class="filter-select" style="font-size: 12px; padding: 4px 8px; font-weight: 600; max-width: 200px;">
              <option value="">${escapeHtml(t("import_callup_placeholder"))}</option>
              ${Object.keys(state.callup?.store?.lists || {}).sort().map(n => `<option value="${escapeHtml(n)}">${escapeHtml(n)} (${(state.callup.store.lists[n]||[]).length})</option>`).join("")}
            </select>
            <span class="ml-auto" style="font-size: 10px; color: var(--text-3);">${selectedList.length} ${currentLang==="it"?"selezionati":"selected"}</span>
          </div>
          ${renderTable()}
          <div class="flex justify-end gap-2">
            <button id="minutes-export-pdf" class="px-3 py-1.5 text-[11px] rounded-md font-semibold" style="background: rgba(96,165,250,0.10); color: var(--info); border: 0.5px solid rgba(96,165,250,0.20);">${currentLang==="it"?"Esporta PDF":"Export PDF"}</button>
            <button id="minutes-clear" class="px-3 py-1.5 text-[11px] rounded-md" style="background: rgba(239,68,68,0.10); color: #EF4444; border: 0.5px solid rgba(239,68,68,0.20);">${currentLang==="it"?"Svuota selezione":"Clear selection"}</button>
          </div>
        `}
      </div>
    </div>`;

  // ============ Listeners ============
  const refocus = (id) => {
    const el = document.getElementById(id);
    if (el) { el.focus(); const l = (el.value || "").length; try { el.setSelectionRange(l, l); } catch {} }
  };

  document.getElementById("minutes-search")?.addEventListener("input", e => {
    state.minutes.filters.q = e.target.value;
    renderMinutesPanel(); refocus("minutes-search");
  });
  document.getElementById("minutes-role")?.addEventListener("change", e => { state.minutes.filters.role = e.target.value; renderMinutesPanel(); });
  document.getElementById("minutes-league")?.addEventListener("change", e => { state.minutes.filters.league = e.target.value; renderMinutesPanel(); });
  document.getElementById("minutes-club")?.addEventListener("change", e => { state.minutes.filters.club = e.target.value; renderMinutesPanel(); });
  document.getElementById("minutes-sort")?.addEventListener("change", e => { state.minutes.sortBy = e.target.value; renderMinutesPanel(); });
  document.getElementById("minutes-import-callup")?.addEventListener("change", e => {
    const name = e.target.value;
    if (!name) return;
    const lists = state.callup?.store?.lists || {};
    if (!lists[name] || !lists[name].length) {
      alert(t("import_callup_empty"));
      e.target.value = "";
      return;
    }
    const n = importCallupToMinutes(name);
    e.target.value = "";
    renderMinutesPanel();
    // Feedback breve
    const msg = t("import_callup_done").replace("{n}", n).replace("{name}", name);
    console.info(msg);
  });

  // Click sugli header competizione → ordina per minuti in quella colonna (toggle)
  panel.querySelectorAll(".minutes-col-header").forEach(th => {
    th.addEventListener("click", () => {
      const key = th.dataset.colKey;
      if (!key) return;
      const target = `comp:${key}`;
      // Toggle: se è già attivo lo stesso → torna al default minutes; altrimenti attivalo
      state.minutes.sortBy = (state.minutes.sortBy === target) ? "minutes" : target;
      renderMinutesPanel();
    });
  });
  document.getElementById("minutes-year-min")?.addEventListener("input", e => {
    const cleaned = (e.target.value || "").replace(/\D/g, "").slice(0, 4);
    state.minutes.filters.yearMin = cleaned ? parseInt(cleaned) : null;
    renderMinutesPanel(); refocus("minutes-year-min");
  });
  document.getElementById("minutes-year-max")?.addEventListener("input", e => {
    const cleaned = (e.target.value || "").replace(/\D/g, "").slice(0, 4);
    state.minutes.filters.yearMax = cleaned ? parseInt(cleaned) : null;
    renderMinutesPanel(); refocus("minutes-year-max");
  });

  // Toggle add/remove dalla lista a sinistra (preserva la scroll-position della lista)
  panel.querySelectorAll(".minutes-row").forEach(row => {
    row.addEventListener("click", () => {
      const pid = parseInt(row.dataset.pid);
      const scrollEl = document.getElementById("minutes-list-scroll");
      const savedScroll = scrollEl ? scrollEl.scrollTop : 0;
      const i = state.minutes.selectedIds.indexOf(pid);
      if (i >= 0) state.minutes.selectedIds.splice(i, 1);
      else state.minutes.selectedIds.push(pid);
      _saveMinutesSelection();
      renderMinutesPanel();
      // Ripristina scroll subito dopo il re-render (DOM nuovo)
      const newScrollEl = document.getElementById("minutes-list-scroll");
      if (newScrollEl) newScrollEl.scrollTop = savedScroll;
    });
  });

  // Bottone × per rimuovere dalla card destra
  panel.querySelectorAll(".minutes-remove").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const pid = parseInt(btn.dataset.pid);
      state.minutes.selectedIds = state.minutes.selectedIds.filter(x => x !== pid);
      _saveMinutesSelection();
      renderMinutesPanel();
    });
  });

  // Apri modal scheda giocatore cliccando il nome
  panel.querySelectorAll(".minutes-open-modal").forEach(b => b.addEventListener("click", (e) => {
    e.stopPropagation();
    openPlayerModal(parseInt(b.dataset.pid));
  }));

  // Svuota tutta la selezione
  document.getElementById("minutes-clear")?.addEventListener("click", () => {
    state.minutes.selectedIds = [];
    _saveMinutesSelection();
    renderMinutesPanel();
  });

  // Export PDF
  document.getElementById("minutes-export-pdf")?.addEventListener("click", async () => {
    await exportMinutesPDF(selectedList);
  });
}

// ============ EXPORT PDF MINUTAGGI (A4 landscape, jsPDF nativo) ============
async function exportMinutesPDF(selectedList) {
  if (!window.jspdf) { alert(currentLang==="it"?"Libreria PDF non caricata.":"PDF library not loaded."); return; }
  if (!selectedList?.length) return;
  const btn = document.getElementById("minutes-export-pdf");
  if (btn) { btn.disabled = true; btn.textContent = currentLang==="it"?"Genero…":"Generating…"; }

  const loadImageAsDataURL = (url, opts = {}) => new Promise(resolve => {
    if (!url) return resolve(null);
    const { circular = false, size = 64 } = opts;
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      try {
        const c = document.createElement("canvas");
        c.width = size; c.height = size;
        const ctx = c.getContext("2d");
        if (circular) {
          ctx.beginPath();
          ctx.arc(size/2, size/2, size/2, 0, Math.PI*2);
          ctx.closePath();
          ctx.clip();
        }
        ctx.drawImage(img, 0, 0, size, size);
        resolve(c.toDataURL("image/png"));
      } catch { resolve(null); }
    };
    img.onerror = () => resolve(null);
    img.src = url;
  });

  try {
    // Costruisci union competizioni dalla selezione (stessa logica del render UI)
    const compMap = new Map();
    selectedList.forEach(p => {
      _minutesByCompetition(p.tm_player_id).forEach(c => {
        const key = `${c.type}:${c.code}:${c.name}`;
        if (!compMap.has(key)) compMap.set(key, { key, code: c.code, name: c.name, type: c.type, category: c.category, totalMinutes: 0, totalApps: 0 });
        const e = compMap.get(key);
        e.totalApps += c.apps || 0;
        e.totalMinutes += c.minutes || 0;
      });
    });
    const cols = _sortMinutesCols([...compMap.values()]);
    const firstNatIdx = cols.findIndex(c => c.type === "national");

    const playerKeyed = new Map(selectedList.map(p => {
      const m = new Map();
      _minutesByCompetition(p.tm_player_id).forEach(c => m.set(`${c.type}:${c.code}:${c.name}`, c));
      return [p.tm_player_id, m];
    }));
    const playerTotals = new Map(selectedList.map(p => [p.tm_player_id, _minutesPlayerTotals(p.tm_player_id)]));
    const sumApps = [...playerTotals.values()].reduce((a, t) => a + t.apps, 0);
    const sumMin  = [...playerTotals.values()].reduce((a, t) => a + t.minutes, 0);
    const avgApps = selectedList.length ? Math.round(sumApps / selectedList.length) : 0;
    const avgMin  = selectedList.length ? Math.round(sumMin / selectedList.length) : 0;

    // Pre-carica immagini come dataURL
    const photos = await Promise.all(selectedList.map(p => loadImageAsDataURL(playerPhoto(p), { circular: true, size: 64 })));
    const clubLogos = await Promise.all(selectedList.map(p => {
      const club = state.clubsById.get(p.current_club_id);
      return loadImageAsDataURL(club ? clubLogo(club) : null, { size: 64 });
    }));
    const compLogos = await Promise.all(cols.map(col => {
      const url = col.type === "national" ? _photoUrl("photos/branding/logo.png") : competitionLogo(col.code);
      return loadImageAsDataURL(url, { circular: col.type === "national", size: 64 });
    }));

    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF({ unit: "mm", format: "a4", orientation: "landscape" });
    const pageW = 297, pageH = 210;
    const margin = 10;

    // Header
    pdf.setFont("helvetica", "bold"); pdf.setFontSize(16); pdf.setTextColor(20, 20, 20);
    pdf.text(currentLang==="it" ? "Minutaggi 2025/26" : "Minutes 2025/26", margin, margin + 5);

    pdf.setFont("helvetica", "normal"); pdf.setFontSize(9); pdf.setTextColor(110, 110, 110);
    const today = new Date().toLocaleDateString(currentLang==="it" ? "it-IT" : "en-GB");
    pdf.text(
      `${selectedList.length} ${currentLang==="it"?"giocatori":"players"}  ·  ${cols.length} ${currentLang==="it"?"competizioni":"competitions"}  ·  ${today}`,
      margin, margin + 11
    );

    // Layout tabella
    const tableTop = margin + 16;
    const playerColW = 52;
    const totalColW = 22;        // TOT FINALE (verde scuro)
    const subTotalColW = 20;     // TOT CLUB / TOT NAZ
    // Numero di competizioni club e nazionali
    const nClubCols = firstNatIdx >= 0 ? firstNatIdx : cols.length;
    const nNatCols = firstNatIdx >= 0 ? cols.length - firstNatIdx : 0;
    const hasClubSubtotal = nClubCols > 0;
    const hasNatSubtotal  = nNatCols > 0;
    const subtotalsW = (hasClubSubtotal ? subTotalColW : 0) + (hasNatSubtotal ? subTotalColW : 0);
    const compArea = pageW - 2*margin - playerColW - totalColW - subtotalsW;
    const compColW = Math.max(13, compArea / Math.max(cols.length, 1));
    const headerH = 16;
    const rowH = 11;

    // Coordinate X di ogni elemento (dipendono da quali subtotal esistono)
    const clubColsStartX = margin + playerColW;
    const totClubX  = hasClubSubtotal ? (clubColsStartX + nClubCols * compColW) : null;
    const natColsStartX = clubColsStartX + nClubCols * compColW + (hasClubSubtotal ? subTotalColW : 0);
    const totNatX   = hasNatSubtotal ? (natColsStartX + nNatCols * compColW) : null;
    const totalX    = pageW - margin - totalColW;
    // Coordinate X di ogni colonna competizione (skipping subtotal)
    const colX = (i) => {
      if (i < nClubCols) return clubColsStartX + i * compColW;
      return natColsStartX + (i - nClubCols) * compColW;
    };
    // X del divider verticale tra club e nazionali (cade in coincidenza col TOT CLUB)
    const dividerX = hasClubSubtotal && hasNatSubtotal ? (totClubX + subTotalColW) : (firstNatIdx >= 0 ? colX(firstNatIdx) : null);

    // Disegna header
    const drawHeader = () => {
      pdf.setFillColor(245, 247, 250);
      pdf.rect(margin, tableTop, pageW - 2*margin, headerH, "F");

      pdf.setFont("helvetica", "bold"); pdf.setFontSize(8);
      pdf.setTextColor(80, 80, 90);
      pdf.text(currentLang==="it"?"GIOCATORE":"PLAYER", margin + 2, tableTop + 9);

      cols.forEach((col, i) => {
        const cx = colX(i) + compColW/2;
        if (compLogos[i]) {
          try { pdf.addImage(compLogos[i], "PNG", cx - 4, tableTop + 1, 8, 8); } catch {}
        }
        pdf.setFont("helvetica", "bold"); pdf.setFontSize(6.5);
        pdf.setTextColor(80, 80, 90);
        // Label può contenere "\n" per due righe (es. "King's\nCup")
        const label = _minutesColLabel(col);
        const lines = String(label).split("\n");
        if (lines.length > 1) {
          pdf.text(lines[0], cx, tableTop + 12, { align: "center" });
          pdf.text(lines[1], cx, tableTop + 14.5, { align: "center" });
        } else {
          pdf.text(label, cx, tableTop + 13, { align: "center" });
        }
      });

      // TOT CLUB header (subtotale competizioni club, dopo le competizioni di club)
      if (hasClubSubtotal) {
        pdf.setFillColor(232, 240, 250);
        pdf.rect(totClubX, tableTop, subTotalColW, headerH, "F");
        pdf.setFont("helvetica", "bold"); pdf.setFontSize(7.5);
        pdf.setTextColor(40, 70, 130);
        pdf.text(currentLang==="it"?"TOT CLUB":"TOT CLUB", totClubX + subTotalColW/2, tableTop + 9, { align: "center" });
      }

      // TOT NAZ header (subtotale nazionali)
      if (hasNatSubtotal) {
        pdf.setFillColor(252, 232, 244);
        pdf.rect(totNatX, tableTop, subTotalColW, headerH, "F");
        pdf.setFont("helvetica", "bold"); pdf.setFontSize(7.5);
        pdf.setTextColor(140, 40, 90);
        pdf.text(currentLang==="it"?"TOT NAZ":"TOT NAT", totNatX + subTotalColW/2, tableTop + 9, { align: "center" });
      }

      // TOTAL header (verde scuro più marcato per distinguerlo dai subtotali)
      pdf.setFillColor(15, 110, 86);
      pdf.rect(totalX, tableTop, totalColW, headerH, "F");
      pdf.setFont("helvetica", "bold"); pdf.setFontSize(8);
      pdf.setTextColor(255, 255, 255);
      pdf.text(currentLang==="it"?"TOTALE":"TOTAL", totalX + totalColW/2, tableTop + 9, { align: "center" });

      pdf.setDrawColor(220, 220, 220);
      pdf.line(margin, tableTop + headerH, pageW - margin, tableTop + headerH);
    };

    // Cella numerica con apps e min
    const drawNumCell = (apps, mins, cx, cy, accentBg = false, fontApps = 8.5, fontMin = 8) => {
      if (!apps && !mins) {
        pdf.setFont("helvetica", "normal"); pdf.setFontSize(9);
        pdf.setTextColor(190, 190, 190);
        pdf.text("—", cx, cy + 4, { align: "center" });
        return;
      }
      pdf.setFont("helvetica", "bold"); pdf.setFontSize(fontApps);
      pdf.setTextColor(20, 20, 20);
      pdf.text(String(apps), cx, cy + 2, { align: "center" });
      pdf.setFont("helvetica", "bold"); pdf.setFontSize(fontMin);
      pdf.setTextColor(40, 130, 90);
      pdf.text(`${mins}'`, cx, cy + 7, { align: "center" });
    };

    drawHeader();
    let y = tableTop + headerH;

    // Rows giocatore
    for (let i = 0; i < selectedList.length; i++) {
      const p = selectedList[i];
      // Page break (lascio spazio per SUM + AVG sotto)
      if (y + rowH > pageH - margin - 24) {
        pdf.addPage();
        y = tableTop;
        // Header non ridisegnato in pagine successive per semplicità (può essere aggiunto)
      }

      // Riga zebra
      if (i % 2 === 1) {
        pdf.setFillColor(252, 252, 253);
        pdf.rect(margin, y, pageW - 2*margin, rowH, "F");
      }

      // Foto giocatore
      if (photos[i]) {
        try { pdf.addImage(photos[i], "PNG", margin + 1, y + 1.5, 8, 8); } catch {}
      }

      // Nome + club/role
      pdf.setFont("helvetica", "bold"); pdf.setFontSize(9);
      pdf.setTextColor(20, 20, 20);
      const name = p.full_name || "";
      const nameTrim = name.length > 28 ? name.slice(0, 26) + "…" : name;
      pdf.text(nameTrim, margin + 11, y + 5);

      pdf.setFont("helvetica", "normal"); pdf.setFontSize(7);
      pdf.setTextColor(120, 120, 130);
      const sub = `${p.current_club_name || ""} · ${localizeRole(p.position_general) || ""}`;
      const subTrim = sub.length > 36 ? sub.slice(0, 34) + "…" : sub;
      pdf.text(subTrim, margin + 11, y + 9);

      // Cells
      const breakdown = playerKeyed.get(p.tm_player_id);
      const tot = playerTotals.get(p.tm_player_id);
      // Calcola subtotali per il giocatore corrente
      let pClubApps = 0, pClubMin = 0, pNatApps = 0, pNatMin = 0;
      cols.forEach((col, idx) => {
        const c = breakdown.get(col.key);
        const xCell = colX(idx);
        drawNumCell(c?.apps || 0, c?.minutes || 0, xCell + compColW/2, y + 2.5);
        if (col.type === "club") { pClubApps += c?.apps || 0; pClubMin += c?.minutes || 0; }
        else { pNatApps += c?.apps || 0; pNatMin += c?.minutes || 0; }
      });

      // TOT CLUB cell (sfondo blu tenue)
      if (hasClubSubtotal) {
        pdf.setFillColor(232, 240, 250);
        pdf.rect(totClubX, y, subTotalColW, rowH, "F");
        pdf.setFont("helvetica", "bold"); pdf.setFontSize(9.5);
        pdf.setTextColor(20, 20, 20);
        pdf.text(String(pClubApps), totClubX + subTotalColW/2, y + 4.5, { align: "center" });
        pdf.setFont("helvetica", "bold"); pdf.setFontSize(8.5);
        pdf.setTextColor(40, 70, 130);
        pdf.text(`${pClubMin}'`, totClubX + subTotalColW/2, y + 9, { align: "center" });
      }

      // TOT NAZ cell (sfondo rosa tenue)
      if (hasNatSubtotal) {
        pdf.setFillColor(252, 232, 244);
        pdf.rect(totNatX, y, subTotalColW, rowH, "F");
        pdf.setFont("helvetica", "bold"); pdf.setFontSize(9.5);
        pdf.setTextColor(20, 20, 20);
        pdf.text(String(pNatApps), totNatX + subTotalColW/2, y + 4.5, { align: "center" });
        pdf.setFont("helvetica", "bold"); pdf.setFontSize(8.5);
        pdf.setTextColor(140, 40, 90);
        pdf.text(`${pNatMin}'`, totNatX + subTotalColW/2, y + 9, { align: "center" });
      }

      // Total cell con sfondo verde scuro (highlight)
      pdf.setFillColor(208, 240, 224);
      pdf.rect(totalX, y, totalColW, rowH, "F");
      pdf.setFont("helvetica", "bold"); pdf.setFontSize(10);
      pdf.setTextColor(15, 80, 56);
      pdf.text(String(tot.apps), totalX + totalColW/2, y + 4.5, { align: "center" });
      pdf.setFont("helvetica", "bold"); pdf.setFontSize(9);
      pdf.setTextColor(15, 110, 86);
      pdf.text(`${tot.minutes}'`, totalX + totalColW/2, y + 9, { align: "center" });

      // Row divider
      pdf.setDrawColor(232, 232, 235);
      pdf.line(margin, y + rowH, pageW - margin, y + rowH);

      y += rowH;
    }

    // Subtotali aggregati per la riga SOMMA
    const sumClubApps = cols.filter(c => c.type === "club").reduce((a, c) => a + c.totalApps, 0);
    const sumClubMin  = cols.filter(c => c.type === "club").reduce((a, c) => a + c.totalMinutes, 0);
    const sumNatApps  = cols.filter(c => c.type === "national").reduce((a, c) => a + c.totalApps, 0);
    const sumNatMin   = cols.filter(c => c.type === "national").reduce((a, c) => a + c.totalMinutes, 0);

    // Riga SUM
    pdf.setFillColor(238, 244, 252);
    pdf.rect(margin, y, pageW - 2*margin, rowH, "F");
    pdf.setFont("helvetica", "bold"); pdf.setFontSize(8.5);
    pdf.setTextColor(60, 60, 90);
    pdf.text(currentLang==="it"?"SOMMA":"TOTAL", margin + 2, y + 7);

    cols.forEach((col, i) => {
      drawNumCell(col.totalApps, col.totalMinutes, colX(i) + compColW/2, y + 2.5);
    });
    // TOT CLUB SUM
    if (hasClubSubtotal) {
      pdf.setFillColor(220, 232, 248);
      pdf.rect(totClubX, y, subTotalColW, rowH, "F");
      pdf.setFont("helvetica", "bold"); pdf.setFontSize(9.5);
      pdf.setTextColor(20, 20, 20);
      pdf.text(String(sumClubApps), totClubX + subTotalColW/2, y + 4.5, { align: "center" });
      pdf.setFont("helvetica", "bold"); pdf.setFontSize(8.5);
      pdf.setTextColor(40, 70, 130);
      pdf.text(`${sumClubMin}'`, totClubX + subTotalColW/2, y + 9, { align: "center" });
    }
    // TOT NAZ SUM
    if (hasNatSubtotal) {
      pdf.setFillColor(248, 220, 236);
      pdf.rect(totNatX, y, subTotalColW, rowH, "F");
      pdf.setFont("helvetica", "bold"); pdf.setFontSize(9.5);
      pdf.setTextColor(20, 20, 20);
      pdf.text(String(sumNatApps), totNatX + subTotalColW/2, y + 4.5, { align: "center" });
      pdf.setFont("helvetica", "bold"); pdf.setFontSize(8.5);
      pdf.setTextColor(140, 40, 90);
      pdf.text(`${sumNatMin}'`, totNatX + subTotalColW/2, y + 9, { align: "center" });
    }
    // TOTAL SUM (verde scuro pieno)
    pdf.setFillColor(15, 110, 86);
    pdf.rect(totalX, y, totalColW, rowH, "F");
    pdf.setFont("helvetica", "bold"); pdf.setFontSize(10);
    pdf.setTextColor(255, 255, 255);
    pdf.text(String(sumApps), totalX + totalColW/2, y + 4.5, { align: "center" });
    pdf.setFont("helvetica", "bold"); pdf.setFontSize(9);
    pdf.setTextColor(220, 250, 240);
    pdf.text(`${sumMin}'`, totalX + totalColW/2, y + 9, { align: "center" });

    pdf.setDrawColor(200, 210, 220);
    pdf.line(margin, y, pageW - margin, y);
    y += rowH;

    // Riga AVG (solo se 2+ giocatori)
    if (selectedList.length >= 2) {
      const n = selectedList.length;
      pdf.setFillColor(228, 240, 252);
      pdf.rect(margin, y, pageW - 2*margin, rowH, "F");
      pdf.setFont("helvetica", "bold"); pdf.setFontSize(8.5);
      pdf.setTextColor(60, 60, 90);
      pdf.text(currentLang==="it"?"MEDIA":"AVG", margin + 2, y + 7);

      cols.forEach((col, i) => {
        const a = Math.round(col.totalApps / n);
        const m = Math.round(col.totalMinutes / n);
        drawNumCell(a, m, colX(i) + compColW/2, y + 2.5);
      });
      // TOT CLUB AVG
      if (hasClubSubtotal) {
        pdf.setFillColor(220, 232, 248);
        pdf.rect(totClubX, y, subTotalColW, rowH, "F");
        pdf.setFont("helvetica", "bold"); pdf.setFontSize(9.5);
        pdf.setTextColor(20, 20, 20);
        pdf.text(String(Math.round(sumClubApps / n)), totClubX + subTotalColW/2, y + 4.5, { align: "center" });
        pdf.setFont("helvetica", "bold"); pdf.setFontSize(8.5);
        pdf.setTextColor(40, 70, 130);
        pdf.text(`${Math.round(sumClubMin / n)}'`, totClubX + subTotalColW/2, y + 9, { align: "center" });
      }
      // TOT NAZ AVG
      if (hasNatSubtotal) {
        pdf.setFillColor(248, 220, 236);
        pdf.rect(totNatX, y, subTotalColW, rowH, "F");
        pdf.setFont("helvetica", "bold"); pdf.setFontSize(9.5);
        pdf.setTextColor(20, 20, 20);
        pdf.text(String(Math.round(sumNatApps / n)), totNatX + subTotalColW/2, y + 4.5, { align: "center" });
        pdf.setFont("helvetica", "bold"); pdf.setFontSize(8.5);
        pdf.setTextColor(140, 40, 90);
        pdf.text(`${Math.round(sumNatMin / n)}'`, totNatX + subTotalColW/2, y + 9, { align: "center" });
      }
      // TOTAL AVG (verde scuro pieno)
      pdf.setFillColor(15, 110, 86);
      pdf.rect(totalX, y, totalColW, rowH, "F");
      pdf.setFont("helvetica", "bold"); pdf.setFontSize(10);
      pdf.setTextColor(255, 255, 255);
      pdf.text(String(avgApps), totalX + totalColW/2, y + 4.5, { align: "center" });
      pdf.setFont("helvetica", "bold"); pdf.setFontSize(9);
      pdf.setTextColor(220, 250, 240);
      pdf.text(`${avgMin}'`, totalX + totalColW/2, y + 9, { align: "center" });
    }

    // Divider verticale tra club e nazionali (su tutta l'altezza della tabella)
    if (dividerX !== null) {
      pdf.setDrawColor(180, 190, 200);
      pdf.setLineWidth(0.4);
      pdf.line(dividerX, tableTop, dividerX, y);
      pdf.setLineWidth(0.2);
    }

    // Footer
    pdf.setFont("helvetica", "italic"); pdf.setFontSize(7);
    pdf.setTextColor(150, 150, 160);
    pdf.text("Saudi Players Hub", margin, pageH - 4);
    pdf.text(today, pageW - margin, pageH - 4, { align: "right" });

    const fname = `minutes_${new Date().toISOString().slice(0,10)}.pdf`;
    pdf.save(fname);
  } catch (e) {
    console.error("PDF export error:", e);
    alert("PDF: " + (e.message || e));
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = currentLang==="it"?"Esporta PDF":"Export PDF"; }
  }
}

// ============ FAVORITES PANEL ============
function renderFavoritesPanel() {
  const panel = document.getElementById("favorites-panel");
  if (!panel) return;
  const favIds = state.favorites;
  const items = state.players.filter(p => favIds.has(Number(p.tm_player_id)));
  if (items.length === 0) {
    panel.innerHTML = `
      <div class="text-center py-16" style="color: var(--text-3);">
        <div style="font-size: 48px; line-height: 1; margin-bottom: 12px; opacity: 0.4;">⭐</div>
        <div class="text-base font-semibold mb-1" style="color: var(--text-2);">${escapeHtml(t("favorites_title"))}</div>
        <div class="text-sm" style="max-width: 360px; margin: 0 auto;">${escapeHtml(t("favorites_empty"))}</div>
      </div>`;
    return;
  }
  // Ordinamento alfabetico predefinito
  items.sort((a,b) => (a.full_name||"").localeCompare(b.full_name||""));

  const renderCard = (p) => {
    const club = state.clubsById.get(p.current_club_id);
    const logo = clubLogo(club);
    const goals = totalGoals2025(p.tm_player_id);
    const goalsBadge = goals > 0
      ? `<div class="absolute top-2 left-2 z-10 flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold stat-cell" style="background: rgba(251,191,36,0.18); color: var(--hot); backdrop-filter: blur(4px); border: 0.5px solid rgba(251,191,36,0.30);">⚽ ${goals}</div>`
      : "";
    const shirt = p.shirt_number
      ? `<div class="absolute top-2 right-10 z-10">
          <svg width="26" height="26" viewBox="0 0 26 26" xmlns="http://www.w3.org/2000/svg">
            <circle cx="13" cy="13" r="11" fill="rgba(14,17,22,0.85)" stroke="rgba(111,224,168,0.30)" stroke-width="0.6"/>
            <text x="13" y="17" text-anchor="middle" font-family="-apple-system, sans-serif" font-size="11" font-weight="700" fill="#6FE0A8">${p.shirt_number}</text>
          </svg>
        </div>`
      : "";
    return `
    <button class="player-card text-left rounded-xl overflow-hidden relative" data-pid="${p.tm_player_id}" style="background: var(--surface); border: 0.5px solid var(--border);">
      <div class="overflow-hidden relative" style="aspect-ratio: 1/1; background: linear-gradient(180deg, #21262E 0%, #14181E 100%);">
        ${shirt}${goalsBadge}
        <span class="fav-star is-fav" data-fav="${p.tm_player_id}" title="${t('remove_from_favorites')}">${FAV_STAR_SVG}</span>
        ${(() => { const fl = nationFlag(p); return fl ? `<div class="absolute bottom-1 left-1 w-8 h-8 flex items-center justify-center" style="filter: drop-shadow(0 1px 3px rgba(0,0,0,0.6));"><img src="${fl}" alt="" class="w-8 h-8 object-contain" loading="lazy" onerror="this.parentElement.style.display='none'"/></div>` : ""; })()}
        <img src="${playerPhoto(p)}" alt="${escapeHtml(p.full_name)}" class="w-full h-full object-contain" loading="lazy" style="padding: 14px;"
             onerror="(function(img){var fb=${JSON.stringify(p.photo_url || '')};var av='https://ui-avatars.com/api/?name=${encodeURIComponent(p.full_name||'?')}&size=256&background=1A1F26&color=6FE0A8&bold=true&font-size=0.45';if(fb && img.src!==fb && fb.indexOf('default')<0){img.src=fb;img.onerror=function(){img.onerror=null;img.src=av;};}else{img.onerror=null;img.src=av;}})(this)"/>
        ${logo ? `<div class="absolute bottom-1 right-1 w-8 h-8 flex items-center justify-center" style="filter: drop-shadow(0 1px 3px rgba(0,0,0,0.6));"><img src="${logo}" alt="" class="w-8 h-8 object-contain" loading="lazy"/></div>` : ""}
      </div>
      <div class="px-2 py-2">
        <div class="text-[13px] font-semibold leading-tight truncate" style="color: var(--text-1);">${escapeHtml(p.full_name)||"—"}</div>
        <div class="flex items-center justify-between mt-1.5 gap-1">
          <span class="text-[10px] px-1.5 py-0.5 rounded truncate" style="background: var(--accent-bg); color: var(--accent);">${escapeHtml(localizeRole(p.position_specific || p.position_general))}</span>
          <span class="text-[10px] stat-cell flex-shrink-0" style="color: var(--text-3);">${birthYear(p) || (p.age || "")}</span>
        </div>
      </div>
    </button>`;
  };

  panel.innerHTML = `
    <div class="flex items-center gap-2 mb-4 pb-2" style="border-bottom: 0.5px solid var(--border);">
      <svg viewBox="0 0 24 24" width="20" height="20" fill="var(--hot)" stroke="var(--hot)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
      <h2 class="text-base font-bold" style="color: var(--text-1);">${escapeHtml(t("favorites_title"))}</h2>
      <span class="ml-auto text-xs stat-cell" style="color: var(--text-3);">${items.length}</span>
    </div>
    <div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-7 xl:grid-cols-8 gap-1.5">
      ${items.map(renderCard).join("")}
    </div>`;

  panel.querySelectorAll("[data-pid]").forEach(el => el.addEventListener("click", (ev) => {
    const star = ev.target.closest("[data-fav]");
    if (star) {
      ev.stopPropagation();
      ev.preventDefault();
      const pid = parseInt(star.dataset.fav);
      toggleFavorite(pid);
      renderFavoritesPanel(); // refresh per togliere il giocatore dalla lista
      return;
    }
    openPlayerModal(parseInt(el.dataset.pid));
  }));
}

// ============ ROUTING (sidebar) ============
function setActiveTab(route) {
  if (route === "players") route = "home"; // backward-compat
  state.activeTab = route;
  document.querySelectorAll(".nav-item").forEach(b => b.classList.toggle("active", b.dataset.route === route));
  // Show/hide via classList (rimuove .hidden di Tailwind)
  const setVisible = (id, show) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.toggle("hidden", !show);
  };
  setVisible("players-grid", route === "home");
  setVisible("list-panel", route === "list");
  setVisible("favorites-panel", route === "favorites");
  setVisible("clubs-content", route === "clubs");
  setVisible("compare-panel", route === "compare");
  setVisible("callup-panel", route === "callup");
  setVisible("grids-panel", route === "grids");
  setVisible("minutes-panel", route === "minutes");
  setVisible("filters", route === "home");
  setVisible("stats-bar", route === "home");
  if (route === "compare") renderCompare();
  if (route === "callup") renderCallupPanel();
  if (route === "list") renderListPanel();
  if (route === "favorites") renderFavoritesPanel();
  if (route === "grids") renderGridsPanel();
  if (route === "minutes") renderMinutesPanel();
}

// ============ SEARCH ============
function debounce(fn, ms) {
  let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
}

function setupSearch() {
  const input = document.getElementById("search-input");
  const results = document.getElementById("search-results");
  const clear = document.getElementById("search-clear");

  const doSearch = debounce(() => {
    const q = input.value.trim().toLowerCase();
    clear.classList.toggle("hidden", !q);
    if (!q) { results.classList.add("hidden"); state.filters.q = ""; applyFilters(); return; }

    const pl = state.players.filter(p => matchPlayer(p, q)).slice(0, 8);
    const cl = state.clubs.filter(c => matchClub(c, q)).slice(0, 4);

    if (!pl.length && !cl.length) {
      results.innerHTML = `<div class="px-4 py-3 text-sm" style="color: var(--text-3);">${t("no_results")}</div>`;
    } else {
      results.innerHTML = `
        ${pl.length ? `<div class="px-4 py-2 text-[10px] uppercase tracking-wider" style="color: var(--text-3); border-bottom: 0.5px solid var(--border);">${t("players")}</div>` : ""}
        ${pl.map(p => {
          const yr = birthYear(p);
          return `<button class="w-full text-left px-4 py-2 flex items-center gap-3 hover:bg-white/5" data-pid="${p.tm_player_id}">
          <img src="${playerPhoto(p)}" class="w-7 h-7 rounded-full object-cover flex-shrink-0" style="background: var(--surface-2);"/>
          <div class="min-w-0 flex-1">
            <div class="text-sm font-medium truncate" style="color: var(--text-1);">${escapeHtml(p.full_name)}${yr ? ` <span class="stat-cell" style="color: var(--text-3); font-weight: 400;">'${yr.slice(-2)}</span>` : ""}</div>
            <div class="text-[10px] truncate" style="color: var(--text-3);">${escapeHtml(p.current_club_name||"")} · ${escapeHtml(localizeRole(p.position_specific||p.position_general))}</div>
          </div>
        </button>`;
        }).join("")}
        ${cl.length ? `<div class="px-4 py-2 text-[10px] uppercase tracking-wider" style="color: var(--text-3); border-bottom: 0.5px solid var(--border);">${t("clubs")}</div>` : ""}
        ${cl.map(c => {
          const logo = clubLogo(c);
          return `<button class="w-full text-left px-4 py-2 flex items-center gap-3 hover:bg-white/5" data-cid="${c.tm_club_id}">
            ${logo ? `<img src="${logo}" class="w-7 h-7 object-contain flex-shrink-0"/>` : `<div class="w-7 h-7 rounded flex items-center justify-center text-xs font-bold" style="background: var(--accent-bg); color: var(--accent);">${(c.name||"?")[0]}</div>`}
            <div class="text-sm" style="color: var(--text-1);">${escapeHtml(c.name)}</div>
          </button>`;
        }).join("")}
      `;
      results.querySelectorAll("[data-pid]").forEach(el => el.addEventListener("click", () => {
        results.classList.add("hidden");
        input.value = ""; clear.classList.add("hidden");
        openPlayerModal(parseInt(el.dataset.pid));
      }));
      results.querySelectorAll("[data-cid]").forEach(el => el.addEventListener("click", () => {
        results.classList.add("hidden");
        input.value = ""; clear.classList.add("hidden");
        state.filters.club = el.dataset.cid;
        document.getElementById("filter-club").value = el.dataset.cid;
        setActiveTab("players");
        applyFilters();
      }));
    }
    results.classList.remove("hidden");
  }, 150);

  input.addEventListener("input", doSearch);
  clear.addEventListener("click", () => { input.value = ""; doSearch(); });
  document.addEventListener("click", e => {
    if (!results.contains(e.target) && e.target !== input) results.classList.add("hidden");
  });
}

// ============ "AGGIORNA ORA" BUTTON ============
// Endpoint backend FastAPI (default localhost:8000). Se non risponde, mostra istruzioni.
const UPDATE_API_BASE = "http://127.0.0.1:8000";

async function _apiPost(path) {
  const r = await fetch(UPDATE_API_BASE + path, { method: "POST" });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}
async function _apiGet(path) {
  const r = await fetch(UPDATE_API_BASE + path);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

// Parsing del log_tail di run_update.py per inferire % e ETA.
// Mappa peso step (somma 100):
//   STEP 1/7 REFRESH CLUBS         →  1
//   STEP 2/7 REFRESH ROSTERS       → 12
//   STEP 3/7 SCRAPE PROFILI NUOVI  →  3 (di solito 0 in refresh ravvicinati)
//   STEP 4/7 RE-FILTER SAUDI       →  1
//   STEP 5/7 ENRICH SORTITOUTSI    →  2
//   STEP 5b/7 IMPORT WYSCOUT       →  1
//   STEP 6/7 REFRESH STATS         → 72 (è il più lungo)
//   STEP 7/7 DOWNLOAD FOTO         →  8
const _UPDATE_STEPS = [
  { id: "1", weight: 1,  label: "clubs" },
  { id: "2", weight: 12, label: "rosters" },
  { id: "3", weight: 3,  label: "profili" },
  { id: "4", weight: 1,  label: "saudi filter" },
  { id: "5", weight: 2,  label: "sortitoutsi" },
  { id: "5b",weight: 1,  label: "wyscout" },
  { id: "6", weight: 72, label: "stats" },
  { id: "7", weight: 8,  label: "foto" },
];
function _stepCumulative(stepId) {
  let total = 0;
  for (const s of _UPDATE_STEPS) {
    if (s.id === stepId) return total;
    total += s.weight;
  }
  return 100;
}
function _stepWeight(stepId) {
  const s = _UPDATE_STEPS.find(x => x.id === stepId);
  return s ? s.weight : 0;
}

// Ritorna { percent: 0-100, etaSeconds: number|null, currentStep: string|null }
function _parseUpdateProgress(s) {
  const log = s.log_tail || [];
  const elapsed = s.elapsed_seconds || 0;
  let currentStep = null;
  let stepFraction = 0;     // 0..1, frazione del solo step corrente
  let etaSeconds = null;
  // Trova ultimo "STEP X/7" (anche "STEP 5b/7")
  for (let i = log.length - 1; i >= 0; i--) {
    const line = log[i];
    const m = line.match(/STEP\s+(\d+b?)\/7/i);
    if (m) { currentStep = m[1]; break; }
  }
  if (!currentStep) {
    // Nessuno step ancora → primissimi secondi, mostra 1%
    return { percent: Math.min(elapsed * 0.5, 5), etaSeconds: null, currentStep: null };
  }
  // Per STEP 6 cerca "[i/total]" o "ETA Xm Ys" nelle righe più recenti
  if (currentStep === "6") {
    for (let i = log.length - 1; i >= 0; i--) {
      const line = log[i];
      const mProg = line.match(/\[(\d+)\/(\d+)\]/);
      if (mProg) {
        const i_done = parseInt(mProg[1]);
        const total = parseInt(mProg[2]);
        if (total > 0) stepFraction = i_done / total;
      }
      const mEta = line.match(/ETA\s+(\d+)m(\d+)s/);
      if (mEta) {
        etaSeconds = parseInt(mEta[1]) * 60 + parseInt(mEta[2]);
      }
      if (stepFraction > 0 && etaSeconds !== null) break;
    }
  } else {
    // Step "completato" appena entrati nel successivo
    stepFraction = 0.5; // assume metà dello step
  }
  // Percentuale complessiva: cumulativo prima + frazione * peso step corrente
  const cum = _stepCumulative(currentStep);
  const sw = _stepWeight(currentStep);
  let percent = cum + (stepFraction * sw);
  percent = Math.max(0, Math.min(99, percent));
  // ETA fallback: stima basata su 100% / percent attuale
  if (etaSeconds === null && percent > 1) {
    const totalEstimated = (elapsed / (percent / 100));
    etaSeconds = Math.max(0, Math.round(totalEstimated - elapsed));
  }
  return { percent: Math.round(percent), etaSeconds, currentStep };
}

function _formatEta(seconds) {
  if (seconds == null || !isFinite(seconds)) return "—";
  if (seconds < 60) return `${seconds}s`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}m${String(s).padStart(2,"0")}s`;
}

function setupUpdateButton() {
  const btn = document.getElementById("sidebar-update-btn");
  const icon = document.getElementById("sidebar-update-icon");
  const label = document.getElementById("sidebar-update-label");
  const progress = document.getElementById("sidebar-update-progress");
  const pct = document.getElementById("sidebar-update-pct");
  const eta = document.getElementById("sidebar-update-eta");
  const bar = document.getElementById("sidebar-update-bar");
  if (!btn) return;
  label.textContent = t("update_now");

  let pollInterval = null;

  const setRunning = (running) => {
    btn.disabled = running;
    icon.style.animation = running ? "spin 1s linear infinite" : "";
    label.textContent = running ? t("update_running") : t("update_now");
    progress.style.display = running ? "block" : "none";
  };

  const stopPolling = () => {
    if (pollInterval) { clearInterval(pollInterval); pollInterval = null; }
  };

  const setProgress = (p, etaSec) => {
    pct.textContent = `${p}%`;
    bar.style.width = p + "%";
    if (etaSec == null) {
      eta.textContent = "·  —";
    } else {
      const mins = Math.ceil(etaSec / 60);
      const label = currentLang === "it"
        ? (etaSec < 60 ? `· ${etaSec}s` : `· ~${mins} min`)
        : (etaSec < 60 ? `· ${etaSec}s left` : `· ~${mins} min left`);
      eta.textContent = label;
    }
  };

  const pollStatus = async () => {
    try {
      const s = await _apiGet("/update/status");
      const { percent, etaSeconds } = _parseUpdateProgress(s);
      setProgress(percent, etaSeconds);
      if (!s.running && s.completed_at) {
        stopPolling();
        if (s.exit_code === 0) {
          setProgress(100, 0);
          label.textContent = t("update_completed");
          icon.style.animation = "";
          setTimeout(() => location.reload(), 3000);
        } else {
          setRunning(false);
          label.textContent = t("update_failed");
          pct.style.color = "#EF4444";
          bar.style.background = "#EF4444";
          setTimeout(() => {
            pct.style.color = "";
            bar.style.background = "";
            label.textContent = t("update_now");
            progress.style.display = "none";
          }, 6000);
        }
      }
    } catch (e) {
      stopPolling();
      setRunning(false);
      label.textContent = t("update_backend_unavailable");
      setTimeout(() => { label.textContent = t("update_now"); }, 5000);
    }
  };

  btn.addEventListener("click", async () => {
    if (btn.disabled) return;
    try {
      await _apiPost("/update");
      setRunning(true);
      setProgress(0, null);
      pollInterval = setInterval(pollStatus, 2000);
    } catch (e) {
      label.textContent = t("update_backend_unavailable");
      setTimeout(() => { label.textContent = t("update_now"); }, 5000);
    }
  });

  // Al boot: health-check del backend.
  // Se NON è raggiungibile (deploy Vercel: solo statico) → nascondi il pulsante e mostra info "auto-update".
  // Se è raggiungibile (locale con `bash api/run.sh`) → bottone normale + ripristina eventuale job in corso.
  _apiGet("/update/status").then(s => {
    btn.style.display = ""; // visibile (default)
    if (s.running) {
      setRunning(true);
      const { percent, etaSeconds } = _parseUpdateProgress(s);
      setProgress(percent, etaSeconds);
      pollInterval = setInterval(pollStatus, 2000);
    }
  }).catch(() => {
    // Backend non disponibile → nascondi il bottone e mostra info auto-update statica
    btn.style.display = "none";
    if (progress) progress.style.display = "none";
    const updateBox = btn.parentElement;
    if (updateBox && !document.getElementById("auto-update-info")) {
      const info = document.createElement("div");
      info.id = "auto-update-info";
      info.className = "sidebar-label";
      info.style.cssText = "margin-top: 8px; padding: 6px 8px; background: rgba(255,255,255,0.03); color: var(--text-3); border: 0.5px solid var(--border); border-radius: 6px; font-size: 10px; line-height: 1.3; text-align: center;";
      info.innerHTML = `<div style="font-weight: 600; color: var(--text-2); margin-bottom: 2px;">⏱ ${currentLang==="it"?"Auto-update":"Auto-update"}</div><div>${currentLang==="it"?"ogni 2 giorni":"every 2 days"}</div>`;
      updateBox.appendChild(info);
    }
  });
}

// ============ INIT ============
document.addEventListener("DOMContentLoaded", () => {
  loadFavorites();
  bootstrap().then(() => {
    setupSearch();
    setupUpdateButton();
    document.querySelectorAll(".nav-item").forEach(b => b.addEventListener("click", () => setActiveTab(b.dataset.route)));
    setActiveTab("home");
    updateFavoritesBadge();
    document.getElementById("filter-league").addEventListener("change", e => { state.filters.league = e.target.value; applyFilters(); });
    document.getElementById("filter-club").addEventListener("change", e => { state.filters.club = e.target.value; applyFilters(); });
    document.getElementById("filter-role").addEventListener("change", e => { state.filters.role = e.target.value; applyFilters(); });
    document.getElementById("filter-sort").addEventListener("change", e => { state.filters.sort = e.target.value; applyFilters(); });
    document.getElementById("filter-year-min")?.addEventListener("input", e => {
      const v = (e.target.value || "").replace(/\D/g, "").slice(0, 4);
      e.target.value = v;
      state.filters.yearMin = v ? parseInt(v) : null;
      applyFilters();
    });
    document.getElementById("filter-year-max")?.addEventListener("input", e => {
      const v = (e.target.value || "").replace(/\D/g, "").slice(0, 4);
      e.target.value = v;
      state.filters.yearMax = v ? parseInt(v) : null;
      applyFilters();
    });
    document.addEventListener("lang-changed", () => {
      populateClubFilter();
      renderPlayers();
      renderClubs();
      renderCompare();
      renderLastUpdate();
      // re-localizza il bottone update
      const lbl = document.getElementById("sidebar-update-label");
      if (lbl) lbl.textContent = t("update_now");
    });
  });
});

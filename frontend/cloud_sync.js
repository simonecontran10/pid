/**
 * cloud_sync.js — Auth + sincronizzazione cloud (Supabase) per PID.
 *
 * Cosa fa:
 *  1. Inizializza il client Supabase (publishable key, sicura da esporre).
 *  2. Mostra l'auth-gate fullscreen all'apertura del sito (login obbligatorio).
 *  3. Sync automatico LS↔cloud per:
 *       - pid_callup_active     → user_state.callups.currentIds
 *       - saudi_callups_v1      → user_state.callups.store     (chiave LS legacy mantenuta)
 *       - pid_player_notes      → user_state.notes
 *       - pid_grids_v1          → user_state.grids
 *       - saudi_minutes_v1      → user_state.minutes           (chiave LS legacy mantenuta)
 *       - pid_favorites         → user_state.favorites
 *  4. Migrazione dati legacy: al primo avvio, se trova dati su chiavi `saudi_*` orfane
 *     (player_notes, grids, callup_active), li migra silenziosamente alle chiavi `pid_*`.
 *  5. Migrazione first-sign-in: cloud vuoto → upload LS al cloud; cloud non vuoto → download.
 *
 * Caricato in index.html DOPO supabase-js CDN e PRIMA di app.js.
 */
const SUPABASE_URL = "https://mbghahzykbsaudcpybdh.supabase.co";
const SUPABASE_PUBLISHABLE_KEY = "sb_publishable_f9w-q3c7PPCJZYvx2kCYmg_rG271ipU";

const _supa = window.supabase
  ? window.supabase.createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, {
      auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
    })
  : null;
window._supa = _supa;  // espongo per uso in app.js (admin panel)

window.cloudAuth = { user: null, ready: false };

// Mappatura keys localStorage → colonne user_state e relativi parser
const LS_TO_CLOUD = {
  pid_callup_active: { col: "callups", path: "currentIds", parse: (v) => JSON.parse(v || "[]") },
  saudi_callups_v1:  { col: "callups", path: "store",      parse: (v) => JSON.parse(v || '{"lists":{},"currentName":""}') },
  pid_player_notes:  { col: "notes",   path: null,         parse: (v) => JSON.parse(v || "{}") },
  pid_grids_v1:      { col: "grids",   path: null,         parse: (v) => JSON.parse(v || '{"formation":"4-3-3","assigned":{},"store":{"lists":{},"currentName":""}}') },
  saudi_minutes_v1:  { col: "minutes", path: null,         parse: (v) => JSON.parse(v || "[]") },
  pid_favorites:     { col: "favorites", path: null,       parse: (v) => JSON.parse(v || "[]") },
};

// Migrazione one-shot: chiavi saudi_* legacy → pid_*
const LEGACY_RENAMES = {
  saudi_player_notes:  "pid_player_notes",
  saudi_grids_v1:      "pid_grids_v1",
  saudi_callup_active: "pid_callup_active",
  // Nota: saudi_callups_v1 e saudi_minutes_v1 sono ancora usate "as-is" da app.js → non rinominare
};

function _migrateLegacyKeys() {
  let migrated = 0;
  for (const [oldKey, newKey] of Object.entries(LEGACY_RENAMES)) {
    const oldVal = localStorage.getItem(oldKey);
    const newVal = localStorage.getItem(newKey);
    if (oldVal && !newVal) {
      localStorage.setItem(newKey, oldVal);
      migrated++;
      console.log(`[cloud_sync] migrated ${oldKey} → ${newKey}`);
    }
  }
  if (migrated) console.log(`[cloud_sync] legacy migration: ${migrated} keys moved to pid_*`);
}

// ============ AUTH GATE ============
function _showAuthGate() {
  const gate = document.getElementById("auth-gate");
  if (gate) gate.style.display = "flex";
  document.body.style.overflow = "hidden";
}

function _hideAuthGate() {
  const gate = document.getElementById("auth-gate");
  if (gate) gate.style.display = "none";
  document.body.style.overflow = "";
}

async function cloudInitAuth() {
  try { _migrateLegacyKeys(); } catch (e) { console.warn("legacy migration:", e); }

  if (!_supa) {
    // Senza Supabase → bloccato (cambio policy: prima si sbloccava)
    console.error("[cloud_sync] Supabase JS non caricato. Login obbligatorio NON disponibile.");
    const gate = document.getElementById("auth-gate");
    const msg = document.getElementById("auth-gate-msg");
    if (gate) gate.style.display = "flex";
    if (msg) {
      msg.textContent = "Errore connessione al servizio di autenticazione. Ricarica la pagina o riprova tra qualche minuto.";
      msg.style.color = "#EF4444";
    }
    document.body.style.overflow = "hidden";
    return;
  }

  const { data: { session } } = await _supa.auth.getSession();
  window.cloudAuth.user = session?.user || null;
  if (window._toggleAdminNav) window._toggleAdminNav();
  window.cloudAuth.ready = true;
  _renderAuthUI();

  if (window.cloudAuth.user) {
    _hideAuthGate();
  } else {
    _showAuthGate();
  }

  _wireAuthGateForm();

  _supa.auth.onAuthStateChange(async (event, session) => {
    const wasUser = window.cloudAuth.user;
    window.cloudAuth.user = session?.user || null;
  if (window._toggleAdminNav) window._toggleAdminNav();
    _renderAuthUI();
    if (event === "SIGNED_IN" && !wasUser) {
      _hideAuthGate();
      await _onFirstSignIn();
    } else if (event === "SIGNED_OUT") {
      _showAuthGate();
      _onSignedOut();
    }
  });
}

async function cloudSignInWithEmail(email) {
  const { error } = await _supa.auth.signInWithOtp({
    email,
    options: { emailRedirectTo: window.location.href },
  });
  if (error) throw error;
}

async function cloudSignInWithPassword(email, password) {
  const { error } = await _supa.auth.signInWithPassword({ email, password });
  if (error) throw error;
}

async function cloudSignUpWithPassword(email, password) {
  const { error } = await _supa.auth.signUp({
    email, password,
    options: { emailRedirectTo: window.location.href },
  });
  if (error) throw error;
}

async function cloudResetPassword(email) {
  const { error } = await _supa.auth.resetPasswordForEmail(email, {
    redirectTo: window.location.href,
  });
  if (error) throw error;
}

async function cloudSignOut() {
  await _supa.auth.signOut();
}

// ============ CLOUD I/O ============
async function _cloudLoad() {
  if (!window.cloudAuth.user) return null;
  const { data, error } = await _supa
    .from("user_state")
    .select("*")
    .eq("user_id", window.cloudAuth.user.id)
    .maybeSingle();
  if (error) {
    console.warn("[cloud_sync] load error:", error.message);
    return null;
  }
  return data;
}

async function _cloudSaveColumn(col, value) {
  if (!window.cloudAuth.user) return;
  const update = { [col]: value, updated_at: new Date().toISOString() };
  const { error } = await _supa
    .from("user_state")
    .upsert(
      { user_id: window.cloudAuth.user.id, ...update },
      { onConflict: "user_id" }
    );
  if (error) console.warn(`[cloud_sync] save ${col} error:`, error.message);
}

function _buildColumnValue(col) {
  if (col === "callups") {
    return {
      currentIds: JSON.parse(localStorage.getItem("pid_callup_active") || "[]"),
      store:      JSON.parse(localStorage.getItem("saudi_callups_v1") || '{"lists":{},"currentName":""}'),
    };
  }
  if (col === "notes")     return JSON.parse(localStorage.getItem("pid_player_notes") || "{}");
  if (col === "grids")     return JSON.parse(localStorage.getItem("pid_grids_v1") || '{"formation":"4-3-3","assigned":{},"store":{"lists":{},"currentName":""}}');
  if (col === "minutes")   return JSON.parse(localStorage.getItem("saudi_minutes_v1") || "[]");
  if (col === "favorites") return JSON.parse(localStorage.getItem("pid_favorites") || "[]");
  return null;
}

const _saveTimers = {};
function _scheduleSaveColumn(col) {
  if (!window.cloudAuth.user) return;
  clearTimeout(_saveTimers[col]);
  _saveTimers[col] = setTimeout(() => _cloudSaveColumn(col, _buildColumnValue(col)), 1200);
}

const _origSetItem = Storage.prototype.setItem;
Storage.prototype.setItem = function (key, value) {
  _origSetItem.call(this, key, value);
  if (this === localStorage && LS_TO_CLOUD[key]) {
    _scheduleSaveColumn(LS_TO_CLOUD[key].col);
  }
};

// ============ LOGIN/LOGOUT EVENTS ============
async function _onFirstSignIn() {
  console.log("[cloud_sync] sign-in:", window.cloudAuth.user.email);
  const cloud = await _cloudLoad();
  const hasCloudData =
    cloud && (
      (cloud.callups?.currentIds?.length > 0) ||
      Object.keys(cloud.callups?.store?.lists || {}).length > 0 ||
      Object.keys(cloud.notes || {}).length > 0 ||
      Object.keys(cloud.grids?.store?.lists || {}).length > 0 ||
      (cloud.minutes?.length > 0) ||
      (cloud.favorites?.length > 0)
    );

  if (hasCloudData) {
    if (cloud.callups?.store)      _origSetItem.call(localStorage, "saudi_callups_v1", JSON.stringify(cloud.callups.store));
    if (cloud.callups?.currentIds) _origSetItem.call(localStorage, "pid_callup_active", JSON.stringify(cloud.callups.currentIds));
    if (cloud.notes)               _origSetItem.call(localStorage, "pid_player_notes", JSON.stringify(cloud.notes));
    if (cloud.grids)               _origSetItem.call(localStorage, "pid_grids_v1", JSON.stringify(cloud.grids));
    if (cloud.minutes)             _origSetItem.call(localStorage, "saudi_minutes_v1", JSON.stringify(cloud.minutes));
    if (cloud.favorites)           _origSetItem.call(localStorage, "pid_favorites", JSON.stringify(cloud.favorites));
    setTimeout(() => location.reload(), 500);
  } else {
    const upload = {
      user_id: window.cloudAuth.user.id,
      callups:   _buildColumnValue("callups"),
      notes:     _buildColumnValue("notes"),
      grids:     _buildColumnValue("grids"),
      minutes:   _buildColumnValue("minutes"),
      favorites: _buildColumnValue("favorites"),
    };
    await _supa.from("user_state").upsert(upload, { onConflict: "user_id" });
    console.log("[cloud_sync] migrated localStorage to cloud.");
  }
}

function _onSignedOut() {
  console.log("[cloud_sync] sign-out");
  setTimeout(() => location.reload(), 300);
}

// ============ UI ============
function _renderAuthUI() {
  const lbl = document.getElementById("auth-user-email");
  if (lbl) lbl.textContent = window.cloudAuth.user?.email || "";
  const btn = document.getElementById("auth-logout");
  if (btn) btn.style.display = window.cloudAuth.user ? "" : "none";

  // Bottone sidebar: quando loggato mostra l'username (parte prima della @) + onclick logout.
  // Quando non loggato è cosmetico (l'auth-gate fullscreen blocca comunque l'accesso).
  const sidebarAuthBtn = document.getElementById("sidebar-auth-btn");
  const sidebarAuthLabel = document.getElementById("sidebar-auth-label");
  if (sidebarAuthBtn && sidebarAuthLabel) {
    if (window.cloudAuth.user) {
      const email = window.cloudAuth.user.email || "";
      const username = email.split("@")[0] || email;
      const shortName = username.length > 16 ? username.slice(0, 14) + "…" : username;
      sidebarAuthLabel.textContent = `👤 ${shortName}`;
      sidebarAuthBtn.title = `${email} — clicca per uscire`;
      sidebarAuthBtn.onclick = async () => {
        if (confirm(`Vuoi disconnetterti da ${email}?`)) {
          await cloudSignOut();
        }
      };
    } else {
      sidebarAuthBtn.style.display = "none";
    }
  }
}

function _wireAuthGateForm() {
  const email = document.getElementById("auth-gate-email");
  const pass = document.getElementById("auth-gate-password");
  const submit = document.getElementById("auth-gate-submit");
  const msg = document.getElementById("auth-gate-msg");
  const linkSignup = document.getElementById("auth-gate-link-signup");
  const linkMagic = document.getElementById("auth-gate-link-magic");
  const linkReset = document.getElementById("auth-gate-link-reset");
  if (!email || !pass || !submit || !msg) return;

  email.focus();

  const tx = (key, fallback) => (typeof t === "function" ? t(key) : null) || fallback;
  const showErr = (txt) => { msg.textContent = txt; msg.style.color = "#EF4444"; };
  const showOk  = (txt) => { msg.textContent = txt; msg.style.color = "var(--accent,#6FE0A8)"; };

  const doLogin = async () => {
    const e = email.value.trim();
    const p = pass.value;
    if (!e || !e.includes("@")) return showErr(tx("gate_email_invalid", "Inserisci un email valido"));
    if (p.length < 6) return showErr(tx("gate_password_min", "Password di almeno 6 caratteri"));
    submit.disabled = true; submit.textContent = tx("gate_please_wait", "Attendere…");
    try {
      await cloudSignInWithPassword(e, p);
    } catch (err) {
      showErr(tx("gate_error", "Errore") + ": " + (err.message || err));
      submit.disabled = false; submit.textContent = tx("gate_signin", "Accedi");
    }
  };

  submit.onclick = doLogin;
  email.addEventListener("keydown", (ev) => { if (ev.key === "Enter") pass.focus(); });
  pass.addEventListener("keydown", (ev) => { if (ev.key === "Enter") doLogin(); });

  if (linkSignup) linkSignup.onclick = (ev) => { ev.preventDefault(); _showLoginModal({ forced: true, mode: "signup" }); };
  if (linkMagic)  linkMagic.onclick  = (ev) => { ev.preventDefault(); _showLoginModal({ forced: true, mode: "magic" }); };
  if (linkReset)  linkReset.onclick  = (ev) => { ev.preventDefault(); _showLoginModal({ forced: true, mode: "reset" }); };
}

function _showLoginModal({ forced = false, mode = "signin" } = {}) {
  const tx = (key, fallback) => (typeof t === "function" ? t(key) : null) || fallback;
  const modal = document.createElement("div");
  modal.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,0.7);z-index:300;display:flex;align-items:center;justify-content:center;padding:24px;";
  const card = document.createElement("div");
  card.style.cssText = "background:var(--surface,#1A1F26);padding:28px;border-radius:14px;width:100%;max-width:420px;border:0.5px solid var(--border,#2A3038);";
  modal.appendChild(card);

  const titleByMode = {
    signin: tx("gate_signin", "Accedi"),
    signup: tx("gate_create_account", "Crea account"),
    magic:  tx("gate_magic_link", "Magic link"),
    reset:  tx("gate_forgot_password", "Reimposta password"),
  };
  let currentMode = mode;
  let showPassword = ["signin", "signup"].includes(mode);

  const $ = (id) => document.getElementById(id);

  const render = () => {
    showPassword = ["signin", "signup"].includes(currentMode);
    card.innerHTML = `
      <h3 style="margin:0 0 16px;font-size:18px;color:var(--text-1,#F2F4F7);">${titleByMode[currentMode]}</h3>
      <input id="auth-email" type="email" placeholder="email@example.com"
        style="width:100%;padding:12px;border-radius:8px;background:var(--bg,#0E1116);color:var(--text-1);border:0.5px solid var(--border);font-size:14px;margin-bottom:10px;"/>
      ${showPassword ? `<input id="auth-password" type="password" placeholder="password (min 6 caratteri)"
        style="width:100%;padding:12px;border-radius:8px;background:var(--bg,#0E1116);color:var(--text-1);border:0.5px solid var(--border);font-size:14px;margin-bottom:10px;"/>` : ""}
      <div id="auth-msg" style="font-size:12px;color:var(--text-3);min-height:18px;margin-bottom:12px;"></div>
      <button id="auth-submit" style="width:100%;padding:12px;border-radius:8px;background:var(--accent,#6FE0A8);color:#0E1116;border:none;font-weight:600;cursor:pointer;font-size:14px;">${titleByMode[currentMode]}</button>
      <div style="display:flex;justify-content:space-between;margin-top:14px;font-size:12px;flex-wrap:wrap;gap:8px;">
        ${currentMode !== "signin" ? `<a href="#" id="auth-link-signin" style="color:var(--text-3);text-decoration:none;">${tx("gate_signin", "Accedi")}</a>` : ""}
        ${currentMode !== "signup" ? `<a href="#" id="auth-link-signup" style="color:var(--text-3);text-decoration:none;">${tx("gate_create_account", "Crea account")}</a>` : ""}
        ${currentMode !== "magic" ? `<a href="#" id="auth-link-magic" style="color:var(--text-3);text-decoration:none;">${tx("gate_magic_link", "Magic link")}</a>` : ""}
        ${currentMode !== "reset" ? `<a href="#" id="auth-link-reset" style="color:var(--text-3);text-decoration:none;">${tx("gate_forgot_password", "Forgot?")}</a>` : ""}
      </div>
    `;
    ["signin","signup","magic","reset"].forEach(m => {
      const el = $("auth-link-" + m);
      if (el) el.onclick = (e) => { e.preventDefault(); currentMode = m; render(); };
    });

    const showErr = (txt) => { const m = $("auth-msg"); m.textContent = txt; m.style.color = "#EF4444"; };
    const showOk  = (txt) => { const m = $("auth-msg"); m.textContent = txt; m.style.color = "var(--accent)"; };
    const submit = async () => {
      const eVal = $("auth-email").value.trim();
      const pVal = showPassword ? $("auth-password").value : null;
      if (!eVal || !eVal.includes("@")) return showErr(tx("gate_email_invalid","Email non valido"));
      if (showPassword && pVal.length < 6) return showErr(tx("gate_password_min","Password >= 6 caratteri"));
      $("auth-submit").disabled = true;
      try {
        if (currentMode === "signin") await cloudSignInWithPassword(eVal, pVal);
        else if (currentMode === "signup") {
          await cloudSignUpWithPassword(eVal, pVal);
          showOk("Account creato! Controlla la tua email per confermarlo.");
        } else if (currentMode === "magic") {
          await cloudSignInWithEmail(eVal);
          showOk("Email inviata! Controlla la tua casella e clicca sul link.");
        } else if (currentMode === "reset") {
          await cloudResetPassword(eVal);
          showOk("Email per reset password inviata.");
        }
        if (currentMode === "signin") setTimeout(cleanup, 300);
      } catch (err) {
        showErr(tx("gate_error","Errore") + ": " + (err.message || err));
      } finally {
        if ($("auth-submit")) $("auth-submit").disabled = false;
      }
    };
    $("auth-submit").onclick = submit;
    $("auth-email").addEventListener("keydown", (e) => { if (e.key === "Enter" && !showPassword) submit(); });
    if ($("auth-password")) $("auth-password").addEventListener("keydown", (e) => { if (e.key === "Enter") submit(); });
  };

  document.body.appendChild(modal);
  const cleanup = () => modal.remove();
  if (!forced) {
    modal.addEventListener("click", (e) => { if (e.target === modal) cleanup(); });
    document.addEventListener("keydown", function esc(e) {
      if (e.key === "Escape") { cleanup(); document.removeEventListener("keydown", esc); }
    });
  }
  render();
}

// === Init ===
document.addEventListener("DOMContentLoaded", () => {
  cloudInitAuth();
});

// ============================================================
//  PLAYER OVERRIDES — modifiche manuali admin che sovrascrivono
//  i dati Transfermarkt. Caricate ad ogni bootstrap.
// ============================================================
async function fetchPlayerOverrides() {
  if (!_supa) return [];
  try {
    const { data, error } = await _supa
      .from("player_overrides")
      .select("tm_player_id, overrides");
    if (error) {
      console.warn("[overrides] fetch error:", error);
      return [];
    }
    return data || [];
  } catch (e) {
    console.warn("[overrides] fetch exception:", e);
    return [];
  }
}

function applyOverridesToPlayers(players, overridesList) {
  if (!Array.isArray(players) || !Array.isArray(overridesList)) return players;
  const overrideMap = {};
  for (const row of overridesList) {
    if (row && row.tm_player_id != null) {
      overrideMap[String(row.tm_player_id)] = row.overrides || {};
    }
  }
  let count = 0;
  for (const p of players) {
    const ov = overrideMap[String(p.tm_player_id)];
    if (ov && Object.keys(ov).length > 0) {
      Object.assign(p, ov);
      count++;
    }
  }
  if (count > 0) console.log(`[overrides] applied ${count} player overrides`);
  return players;
}

window.fetchPlayerOverrides = fetchPlayerOverrides;
window.applyOverridesToPlayers = applyOverridesToPlayers;

// ============================================================
//  Detect ADMIN
// ============================================================
window.ADMIN_EMAIL = "simonecontran10@gmail.com";
window.isAdmin = function() {
  return window.cloudAuth && window.cloudAuth.user && 
         window.cloudAuth.user.email === window.ADMIN_EMAIL;
};

// ============================================================
//  Toggle visibility nav item Admin (visibile solo per admin)
// ============================================================
function _toggleAdminNav() {
  const navAdmin = document.getElementById("nav-admin");
  if (!navAdmin) return;
  if (window.isAdmin && window.isAdmin()) {
    navAdmin.style.display = "";
  } else {
    navAdmin.style.display = "none";
  }
}
window._toggleAdminNav = _toggleAdminNav;


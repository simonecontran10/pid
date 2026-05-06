/**
 * cloud_sync.js — Auth + sincronizzazione cloud (Supabase) per Saudi Players Hub.
 *
 * Cosa fa:
 *  1. Inizializza il client Supabase (publishable key, sicura da esporre).
 *  2. Mostra modale login con email magic link (sidebar bottone "Login").
 *  3. Sync automatico LS↔cloud per:
 *       - saudi_callups_v1   → user_state.callups.store
 *       - saudi_callup_active → user_state.callups.currentIds
 *       - saudi_player_notes  → user_state.notes
 *       - saudi_grids_v1      → user_state.grids
 *  4. Migrazione: al primo login, sale i dati LS al cloud. Login successivi:
 *     scarica dal cloud e sovrascrive LS, poi reload.
 *
 * Caricato in index.html DOPO supabase-js CDN e PRIMA di app.js.
 */
const SUPABASE_URL = "https://akhmipddijvbphhguuvw.supabase.co";
const SUPABASE_PUBLISHABLE_KEY = "sb_publishable_hqhs7JFWT7Mj2b5Zu4QfjQ_xVxIPjRs";

const _supa = window.supabase
  ? window.supabase.createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, {
      auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
    })
  : null;

// Stato auth
window.cloudAuth = { user: null, ready: false };

// Mappatura keys localStorage → colonne user_state e relativi parser
const LS_TO_CLOUD = {
  saudi_callup_active: { col: "callups", path: "currentIds", parse: (v) => JSON.parse(v || "[]") },
  saudi_callups_v1:    { col: "callups", path: "store",      parse: (v) => JSON.parse(v || '{"lists":{},"currentName":""}') },
  saudi_player_notes:  { col: "notes",   path: null,         parse: (v) => JSON.parse(v || "{}") },
  saudi_grids_v1:      { col: "grids",   path: null,         parse: (v) => JSON.parse(v || '{"formation":"4-3-3","assigned":{},"store":{"lists":{},"currentName":""}}') },
};

// ============ AUTH ============
function _showAuthGate() {
  const gate = document.getElementById("auth-gate");
  if (gate) gate.style.display = "flex";
  // disabilita scroll body sotto al gate
  document.body.style.overflow = "hidden";
}

function _hideAuthGate() {
  const gate = document.getElementById("auth-gate");
  if (gate) gate.style.display = "none";
  document.body.style.overflow = "";
}

async function cloudInitAuth() {
  if (!_supa) {
    console.warn("Supabase JS non caricato. Cloud sync disabilitato.");
    // Senza Supabase non possiamo proteggere → nascondi gate per non bloccare tutto
    _hideAuthGate();
    return;
  }
  const { data: { session } } = await _supa.auth.getSession();
  window.cloudAuth.user = session?.user || null;
  window.cloudAuth.ready = true;
  _renderAuthUI();

  if (window.cloudAuth.user) {
    _hideAuthGate();
  } else {
    _showAuthGate();
  }

  // Wire form inline del gate
  _wireAuthGateForm();

  _supa.auth.onAuthStateChange(async (event, session) => {
    const wasUser = window.cloudAuth.user;
    window.cloudAuth.user = session?.user || null;
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
    email,
    password,
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

// ============ STATE LOAD/SAVE ============
async function _cloudLoad() {
  if (!window.cloudAuth.user) return null;
  const { data, error } = await _supa
    .from("user_state")
    .select("callups,notes,grids,updated_at")
    .eq("user_id", window.cloudAuth.user.id)
    .maybeSingle();
  if (error) {
    console.warn("Cloud load error:", error);
    return null;
  }
  return data;
}

async function _cloudSaveColumn(col, value) {
  if (!window.cloudAuth.user) return;
  const update = { [col]: value };
  const { error } = await _supa
    .from("user_state")
    .upsert({ user_id: window.cloudAuth.user.id, ...update }, { onConflict: "user_id" });
  if (error) console.warn("Cloud save error:", error);
}

// Helper: legge LS attuale e ricostruisce il valore della colonna cloud
function _buildColumnValue(col) {
  if (col === "callups") {
    return {
      currentIds: JSON.parse(localStorage.getItem("saudi_callup_active") || "[]"),
      store: JSON.parse(localStorage.getItem("saudi_callups_v1") || '{"lists":{},"currentName":""}'),
    };
  }
  if (col === "notes") {
    return JSON.parse(localStorage.getItem("saudi_player_notes") || "{}");
  }
  if (col === "grids") {
    return JSON.parse(localStorage.getItem("saudi_grids_v1") || '{"formation":"4-3-3","assigned":{},"store":{"lists":{},"currentName":""}}');
  }
}

// Debounce per non spammare il DB
const _saveTimers = {};
function _scheduleSaveColumn(col) {
  if (!window.cloudAuth.user) return;
  clearTimeout(_saveTimers[col]);
  _saveTimers[col] = setTimeout(() => _cloudSaveColumn(col, _buildColumnValue(col)), 1200);
}

// Override globale di localStorage.setItem per intercettare le 4 keys
const _origSetItem = Storage.prototype.setItem;
Storage.prototype.setItem = function (key, value) {
  _origSetItem.call(this, key, value);
  if (this === localStorage && LS_TO_CLOUD[key]) {
    _scheduleSaveColumn(LS_TO_CLOUD[key].col);
  }
};

// ============ LOGIN/LOGOUT EVENTS ============
async function _onFirstSignIn() {
  console.log("Cloud sign-in:", window.cloudAuth.user.email);
  const cloud = await _cloudLoad();
  const hasCloudData =
    cloud && (
      (cloud.callups?.currentIds?.length > 0) ||
      Object.keys(cloud.callups?.store?.lists || {}).length > 0 ||
      Object.keys(cloud.notes || {}).length > 0 ||
      Object.keys(cloud.grids?.store?.lists || {}).length > 0
    );

  if (hasCloudData) {
    // Cloud ha dati → sovrascrivi LS e ricarica
    if (cloud.callups?.store) _origSetItem.call(localStorage, "saudi_callups_v1", JSON.stringify(cloud.callups.store));
    if (cloud.callups?.currentIds) _origSetItem.call(localStorage, "saudi_callup_active", JSON.stringify(cloud.callups.currentIds));
    if (cloud.notes) _origSetItem.call(localStorage, "saudi_player_notes", JSON.stringify(cloud.notes));
    if (cloud.grids) _origSetItem.call(localStorage, "saudi_grids_v1", JSON.stringify(cloud.grids));
    setTimeout(() => location.reload(), 500);
  } else {
    // Cloud vuoto → migra LS attuale al cloud
    const upload = {
      user_id: window.cloudAuth.user.id,
      callups: _buildColumnValue("callups"),
      notes:   _buildColumnValue("notes"),
      grids:   _buildColumnValue("grids"),
    };
    await _supa.from("user_state").upsert(upload, { onConflict: "user_id" });
    console.log("Cloud: migrated localStorage to cloud.");
  }
}

function _onSignedOut() {
  console.log("Cloud sign-out");
  setTimeout(() => location.reload(), 300);
}

// ============ UI ============
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

  const showErr = (txt) => { msg.textContent = txt; msg.style.color = "#EF4444"; };
  const showOk = (txt) => { msg.textContent = txt; msg.style.color = "var(--accent,#6FE0A8)"; };

  const doLogin = async () => {
    const e = email.value.trim();
    const p = pass.value;
    if (!e || !e.includes("@")) return showErr(t("gate_email_invalid"));
    if (p.length < 6) return showErr(t("gate_password_min"));
    submit.disabled = true; submit.textContent = t("gate_please_wait");
    try {
      await cloudSignInWithPassword(e, p);
      // SIGNED_IN handler will hide the gate
    } catch (err) {
      showErr(t("gate_error") + ": " + (err.message || err));
      submit.disabled = false; submit.textContent = t("gate_signin");
    }
  };

  submit.onclick = doLogin;
  email.addEventListener("keydown", (ev) => { if (ev.key === "Enter") pass.focus(); });
  pass.addEventListener("keydown", (ev) => { if (ev.key === "Enter") doLogin(); });

  if (linkSignup) linkSignup.onclick = (ev) => { ev.preventDefault(); _showLoginModal({ forced: true, mode: "signup" }); };
  if (linkMagic)  linkMagic.onclick  = (ev) => { ev.preventDefault(); _showLoginModal({ forced: true, mode: "magic" }); };
  if (linkReset)  linkReset.onclick  = (ev) => { ev.preventDefault(); _showLoginModal({ forced: true, mode: "reset" }); };
}

function _renderAuthUI() {
  const btn = document.getElementById("sidebar-auth-btn");
  const lbl = document.getElementById("sidebar-auth-label");
  if (!btn || !lbl) return;
  if (window.cloudAuth.user) {
    const name = (window.cloudAuth.user.email || "user").split("@")[0];
    lbl.textContent = "👤 " + name;
    btn.title = window.cloudAuth.user.email;
    btn.onclick = () => { if (confirm(t("sign_out_q"))) cloudSignOut(); };
  } else {
    lbl.textContent = t("sidebar_signin");
    btn.title = t("gate_signin");
    btn.onclick = _showLoginModal;
  }
}

function _showLoginModal(opts) {
  if (document.getElementById("auth-modal")) return;
  const forced = !!(opts && opts.forced);
  let mode = (opts && opts.mode) || "login"; // login | signup | magic | reset

  const modal = document.createElement("div");
  modal.id = "auth-modal";
  modal.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,0.7);z-index:300;display:flex;align-items:center;justify-content:center;backdrop-filter:blur(4px);";

  const render = () => {
    const titles = { login: t("gate_signin"), signup: t("gate_signup_title"), magic: t("gate_magic_title"), reset: t("gate_reset_title") };
    const desc = {
      login:  t("gate_signin_desc"),
      signup: t("gate_signup_desc"),
      magic:  t("gate_magic_desc"),
      reset:  t("gate_reset_desc"),
    };
    const btnLabel = { login: t("gate_signin"), signup: t("gate_btn_signup"), magic: t("gate_btn_magic"), reset: t("gate_btn_reset") };
    const showPassword = mode === "login" || mode === "signup";

    modal.innerHTML = `
      <div style="background:var(--surface,#1A1F26);padding:28px;border-radius:14px;border:0.5px solid var(--border-strong,rgba(255,255,255,0.10));max-width:380px;width:90%;box-shadow:0 20px 60px rgba(0,0,0,0.4);">
        <h2 style="font-size:18px;font-weight:600;color:var(--text-1,#fff);margin:0 0 6px;">${titles[mode]}</h2>
        <p style="font-size:12.5px;color:var(--text-3,#6B7585);margin:0 0 18px;line-height:1.5;">${desc[mode]}</p>

        <input id="auth-email" type="email" placeholder="${t("gate_email_ph")}" autocomplete="email"
               style="width:100%;padding:10px 12px;border-radius:8px;background:var(--surface-2,#21262E);border:0.5px solid var(--border,rgba(255,255,255,0.06));color:var(--text-1,#fff);font-size:14px;outline:none;box-sizing:border-box;margin-bottom:8px;"/>

        ${showPassword ? `
          <input id="auth-password" type="password" placeholder="${t("gate_password_ph")}" autocomplete="${mode==='signup'?'new-password':'current-password'}"
                 style="width:100%;padding:10px 12px;border-radius:8px;background:var(--surface-2,#21262E);border:0.5px solid var(--border,rgba(255,255,255,0.06));color:var(--text-1,#fff);font-size:14px;outline:none;box-sizing:border-box;"/>
        ` : ""}

        <div id="auth-msg" style="font-size:11.5px;color:var(--text-3,#6B7585);min-height:16px;margin:10px 0 14px;line-height:1.4;"></div>

        <div style="display:flex;gap:8px;margin-bottom:12px;">
          ${forced ? "" : `<button id="auth-cancel" style="flex:1;padding:10px;border-radius:8px;background:transparent;color:var(--text-2,#B5BDCB);border:0.5px solid var(--border,rgba(255,255,255,0.10));font-size:13px;cursor:pointer;font-weight:500;">${t("gate_cancel")}</button>`}
          <button id="auth-submit" style="flex:1;padding:10px;border-radius:8px;background:var(--accent,#6FE0A8);color:#0E1116;border:none;font-size:13px;cursor:pointer;font-weight:600;">${btnLabel[mode]}</button>
        </div>

        <div style="font-size:11px;color:var(--text-3,#6B7585);text-align:center;line-height:1.6;">
          ${mode === "login" ? `
            <a href="#" id="link-signup" style="color:var(--accent,#6FE0A8);text-decoration:none;">${t("gate_create_account")}</a>
            <span style="margin:0 6px;">·</span>
            <a href="#" id="link-magic" style="color:var(--info,#60A5FA);text-decoration:none;">${t("gate_magic_link")}</a>
            <span style="margin:0 6px;">·</span>
            <a href="#" id="link-reset" style="color:var(--text-3,#6B7585);text-decoration:none;">${t("gate_forgot_password")}</a>
          ` : `
            <a href="#" id="link-back" style="color:var(--accent,#6FE0A8);text-decoration:none;">${t("gate_back")}</a>
          `}
        </div>
      </div>`;

    // Listeners
    const $ = (id) => document.getElementById(id);
    if ($("auth-cancel")) $("auth-cancel").onclick = cleanup;
    $("auth-email").focus();

    if ($("link-signup")) $("link-signup").onclick = (e) => { e.preventDefault(); mode = "signup"; render(); };
    if ($("link-magic"))  $("link-magic").onclick  = (e) => { e.preventDefault(); mode = "magic";  render(); };
    if ($("link-reset"))  $("link-reset").onclick  = (e) => { e.preventDefault(); mode = "reset";  render(); };
    if ($("link-back"))   $("link-back").onclick   = (e) => { e.preventDefault(); mode = "login";  render(); };

    const submit = async () => {
      const email = $("auth-email").value.trim();
      const password = $("auth-password") ? $("auth-password").value : "";
      const msg = $("auth-msg");
      const btn = $("auth-submit");
      msg.style.color = "var(--text-3,#6B7585)";
      if (!email || !email.includes("@")) { msg.textContent = "Please enter a valid email"; msg.style.color = "#EF4444"; return; }
      if (showPassword && password.length < 6) { msg.textContent = "Password must be at least 6 characters"; msg.style.color = "#EF4444"; return; }
      btn.disabled = true; btn.textContent = "Please wait…";
      try {
        if (mode === "login") {
          await cloudSignInWithPassword(email, password);
          cleanup();
        } else if (mode === "signup") {
          await cloudSignUpWithPassword(email, password);
          msg.textContent = "✓ Account created! Confirm your email if required, then sign in.";
          msg.style.color = "var(--accent,#6FE0A8)";
          setTimeout(cleanup, 4000);
        } else if (mode === "magic") {
          await cloudSignInWithEmail(email);
          msg.textContent = "✓ Magic link sent. Check your inbox.";
          msg.style.color = "var(--accent,#6FE0A8)";
          setTimeout(cleanup, 4000);
        } else if (mode === "reset") {
          await cloudResetPassword(email);
          msg.textContent = "✓ Recovery email sent.";
          msg.style.color = "var(--accent,#6FE0A8)";
          setTimeout(cleanup, 4000);
        }
      } catch (e) {
        msg.textContent = "Error: " + (e.message || e);
        msg.style.color = "#EF4444";
        btn.disabled = false; btn.textContent = btnLabel[mode];
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

// Init
document.addEventListener("DOMContentLoaded", () => {
  cloudInitAuth();
});

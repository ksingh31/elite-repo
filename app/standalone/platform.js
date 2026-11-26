/* EliteCraft calculator – platform adapter for the standalone (AWS / any host) build.
 *
 * The app was written as a Claude artifact. It only ever touches the host through
 *   window.claude.use('artifact')  -> { publish(html) }           team save of the whole page (store JSON inside)
 *   window.claude.use('downloads') -> { save({filename, data}) }  file downloads (export JSON, PDFs)
 *   window.claude.use('mcp')       -> { callTool(server, tool, input) }  Google Sheets / Google Drive connectors
 * This file implements exactly that surface on top of a small HTTP API, so the app code stays byte-for-byte the same.
 *
 * Boot order (the build makes the app's main <script> inert as type="text/x-elite-app"):
 *   1. sign in (Cognito hosted UI, OAuth code + PKCE) unless config.auth.mode === 'none'
 *   2. GET  {apiBase}/store  -> { store, version }   and write the JSON into <script id="store">
 *   3. run the app script (it reads <script id="store"> synchronously, like in the artifact)
 * Save:   publish(html) -> PUT {apiBase}/store { store, baseVersion }  (409 = someone else saved first -> {code:'conflict'})
 * Sheets: callTool(...) -> POST {apiBase}/mcp { server, tool, input } -> { payload }  (same shape the Claude connector returns)
 */
(function () {
  'use strict';
  var CFG = window.ELITE_CONFIG || {};
  var API = (CFG.apiBase || '/api').replace(/\/$/, '');
  var AUTH = CFG.auth || { mode: 'none' };
  var version = null;            // store version (S3 ETag) we last loaded or saved
  var TK = 'elite-auth';         // localStorage key for tokens

  // ---------------------------------------------------------------- auth (Cognito hosted UI, code + PKCE)
  function b64url(buf) {
    var s = btoa(String.fromCharCode.apply(null, new Uint8Array(buf)));
    return s.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  }
  function randomStr(n) { var a = new Uint8Array(n); crypto.getRandomValues(a); return b64url(a); }
  function tokens() { try { return JSON.parse(localStorage.getItem(TK) || 'null'); } catch (_) { return null; } }
  function saveTokens(t) { try { localStorage.setItem(TK, JSON.stringify(t)); } catch (_) {} }
  function redirectUri() { return AUTH.redirectUri || (location.origin + location.pathname); }
  async function tokenCall(body) {
    var r = await fetch('https://' + AUTH.domain + '/oauth2/token', {
      method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams(body).toString()
    });
    if (!r.ok) throw new Error('sign-in failed (' + r.status + ')');
    var j = await r.json();
    return { access: j.access_token, id: j.id_token, refresh: j.refresh_token || body.refresh_token, exp: Date.now() + (j.expires_in || 3600) * 1000 - 60000 };
  }
  async function login() {
    var verifier = randomStr(48);
    var digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier));
    var state = randomStr(16);
    sessionStorage.setItem('elite-pkce', JSON.stringify({ verifier: verifier, state: state, hash: location.hash }));
    location.assign('https://' + AUTH.domain + '/oauth2/authorize?' + new URLSearchParams({
      response_type: 'code', client_id: AUTH.clientId, redirect_uri: redirectUri(), scope: 'openid email',
      state: state, code_challenge_method: 'S256', code_challenge: b64url(digest)
    }).toString());
    return new Promise(function () {}); // never resolves: the page is leaving
  }
  async function accessToken(force) {
    if (AUTH.mode === 'none') return null;
    var q = new URLSearchParams(location.search);
    if (q.get('code')) {
      var pk = JSON.parse(sessionStorage.getItem('elite-pkce') || '{}');
      sessionStorage.removeItem('elite-pkce');
      if (pk.state && pk.state === q.get('state')) {
        var t0 = await tokenCall({ grant_type: 'authorization_code', client_id: AUTH.clientId, code: q.get('code'), redirect_uri: redirectUri(), code_verifier: pk.verifier });
        saveTokens(t0);
      }
      history.replaceState(null, '', location.pathname + (pk.hash || ''));
    }
    var t = tokens();
    if (t && !force && t.access && t.exp > Date.now()) return t.access;
    if (t && t.refresh) {
      try { var t2 = await tokenCall({ grant_type: 'refresh_token', client_id: AUTH.clientId, refresh_token: t.refresh }); saveTokens(t2); return t2.access; } catch (_) {}
    }
    return login();
  }
  window.eliteSignOut = function () {
    localStorage.removeItem(TK);
    if (AUTH.mode !== 'none') location.assign('https://' + AUTH.domain + '/logout?' + new URLSearchParams({ client_id: AUTH.clientId, logout_uri: redirectUri() }).toString());
  };

  async function api(method, path, body) {
    for (var attempt = 0; attempt < 2; attempt++) {
      var tok = await accessToken(attempt > 0);
      var h = { 'Content-Type': 'application/json' };
      if (tok) h.Authorization = 'Bearer ' + tok;
      var r = await fetch(API + path, { method: method, headers: h, body: body == null ? undefined : JSON.stringify(body), cache: 'no-store' });
      if (r.status === 401 && attempt === 0 && AUTH.mode !== 'none') continue;
      var j = null; try { j = await r.json(); } catch (_) {}
      if (!r.ok) { var e = (j && j.error) || {}; throw { code: e.code || ('http_' + r.status), message: e.message || ('HTTP ' + r.status), status: r.status }; }
      return j;
    }
  }

  // ---------------------------------------------------------------- the window.claude surface
  var STORE_RE = /<script id="store" type="application\/json">([\s\S]*?)<\/script>/;
  var artifact = {
    publish: async function (html) {
      var m = STORE_RE.exec(String(html || ''));
      if (!m) throw { code: 'bad_request', message: 'no store in the published page' };
      var store = JSON.parse(m[1]);
      try {
        var r = await api('PUT', '/store', { store: store, baseVersion: version });
        version = r.version;
        return { ok: true };
      } catch (e) {
        if (e && (e.status === 409 || e.status === 412)) {
          // same behaviour as the artifact host: the app says "The page reloads to their version." and the page reloads
          setTimeout(function () { location.reload(); }, 2500);
          throw { code: 'conflict', message: 'Someone saved a newer version' };
        }
        if (e && e.status === 403) throw { code: 'not_writer', message: e.message };
        throw e;
      }
    }
  };
  var downloads = {
    save: async function (o) {
      var name = (o && o.filename) || 'download';
      var type = /\.pdf$/i.test(name) ? 'application/pdf' : /\.json$/i.test(name) ? 'application/json' : 'application/octet-stream';
      var blob = o.data instanceof Blob ? o.data : new Blob([o.data], { type: type });
      var a = document.createElement('a');
      a.href = URL.createObjectURL(blob); a.download = name; document.body.appendChild(a); a.click();
      setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
      return { ok: true };
    }
  };
  var mcp = {
    callTool: async function (server, tool, input) {
      return api('POST', '/mcp', { server: server, tool: tool, input: input || {} }); // -> { payload }
    }
  };
  window.claude = {
    use: function (name) {
      if (name === 'artifact') return Promise.resolve(artifact);
      if (name === 'downloads') return Promise.resolve(downloads);
      if (name === 'mcp') return CFG.sheets === false ? Promise.reject({ code: 'unavailable' }) : Promise.resolve(mcp);
      return Promise.reject({ code: 'unavailable' });
    }
  };

  // ---------------------------------------------------------------- boot
  function fail(msg) {
    var d = document.createElement('div');
    d.setAttribute('role', 'alert');
    d.style.cssText = 'position:fixed;inset:auto 16px 16px 16px;padding:14px 16px;background:#7a1d1d;color:#fff;border-radius:10px;font:15px/1.4 system-ui;z-index:99999';
    d.textContent = msg;
    document.body.appendChild(d);
  }
  async function boot() {
    try {
      var r = await api('GET', '/store');
      version = r.version || null;
      var el = document.getElementById('store');
      el.textContent = JSON.stringify(r.store).replace(/</g, '\\u003c');
    } catch (e) {
      fail('Could not load the calculator data: ' + ((e && e.message) || e) + '. Refresh to try again.');
      return;
    }
    var src = document.getElementById('elite-app');
    var s = document.createElement('script');
    s.textContent = src.textContent;
    document.body.appendChild(s);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();

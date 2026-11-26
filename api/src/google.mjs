// Minimal Google Sheets v4 / Drive v3 client (no dependencies).
// Credentials JSON (from SSM Parameter Store SecureString):
//   - a service account key ({"type":"service_account", client_email, private_key, token_uri}), or
//   - an OAuth user refresh token ({"type":"authorized_user", client_id, client_secret, refresh_token}).
// Errors are thrown as {code, message} in the same style the Claude Google connectors use, because the app's
// retry / error text logic matches on them (e.g. "No sheet with id", "Unable to parse range", "denied").
import crypto from 'node:crypto';

const SCOPES = 'https://www.googleapis.com/auth/spreadsheets https://www.googleapis.com/auth/drive';
const SHEETS = 'https://sheets.googleapis.com/v4/spreadsheets/';
const DRIVE = 'https://www.googleapis.com/drive/v3/files';
const b64u = (b) => Buffer.from(b).toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

export function makeGoogle({ loadCredentials, impersonate = '', fetchFn = globalThis.fetch, sleep = (ms) => new Promise((r) => setTimeout(r, ms)) }) {
  let tok = null;
  async function accessToken() {
    if (tok && tok.exp > Date.now() + 60000) return tok.value;
    const cred = await loadCredentials();
    let body;
    if (cred.type === 'service_account') {
      const now = Math.floor(Date.now() / 1000);
      const claims = { iss: cred.client_email, scope: SCOPES, aud: cred.token_uri || 'https://oauth2.googleapis.com/token', iat: now, exp: now + 3600, ...(impersonate ? { sub: impersonate } : {}) };
      const unsigned = b64u(JSON.stringify({ alg: 'RS256', typ: 'JWT' })) + '.' + b64u(JSON.stringify(claims));
      const sig = crypto.createSign('RSA-SHA256').update(unsigned).sign(cred.private_key);
      body = new URLSearchParams({ grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer', assertion: unsigned + '.' + b64u(sig) });
    } else if (cred.type === 'authorized_user') {
      body = new URLSearchParams({ grant_type: 'refresh_token', client_id: cred.client_id, client_secret: cred.client_secret, refresh_token: cred.refresh_token });
    } else throw { code: 'server_not_connected', message: 'Google credentials are missing or of an unknown type' };
    const r = await fetchFn(cred.token_uri || 'https://oauth2.googleapis.com/token', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: body.toString() });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) throw { code: 'needs_reauth', message: 'Google sign-in failed: ' + (j.error_description || j.error || r.status) };
    tok = { value: j.access_token, exp: Date.now() + (j.expires_in || 3600) * 1000 };
    return tok.value;
  }

  async function call(method, url, body) {
    let last;
    for (const wait of [0, 1000, 3000, 8000]) {
      if (wait) await sleep(wait);
      const r = await fetchFn(url, { method, headers: { Authorization: 'Bearer ' + (await accessToken()), 'Content-Type': 'application/json' }, body: body == null ? undefined : JSON.stringify(body) });
      if (r.ok) return r.status === 204 ? {} : r.json();
      const j = await r.json().catch(() => ({}));
      const msg = (j.error && (j.error.message || j.error.status)) || ('HTTP ' + r.status);
      last = { code: r.status === 403 ? 'denied' : r.status === 401 ? 'needs_reauth' : 'tool_error', message: msg, status: r.status };
      if (r.status === 401) tok = null;
      if (!(r.status === 429 || r.status >= 500 || r.status === 401)) break;
    }
    throw last;
  }
  const enc = encodeURIComponent;
  return {
    getValues: (id, range) => call('GET', SHEETS + enc(id) + '/values/' + enc(range)),
    updateValues: (id, range, values) => call('PUT', SHEETS + enc(id) + '/values/' + enc(range) + '?valueInputOption=USER_ENTERED', { range, majorDimension: 'ROWS', values }),
    // RAW: restore-point parts are arbitrary JSON slices and must never be parsed as formulas or numbers
    appendValues: (id, range, values) => call('POST', SHEETS + enc(id) + '/values/' + enc(range) + ':append?valueInputOption=RAW&insertDataOption=INSERT_ROWS', { range, majorDimension: 'ROWS', values }),
    batchUpdate: (id, requests) => call('POST', SHEETS + enc(id) + ':batchUpdate', { requests }),
    batchClear: (id, ranges) => call('POST', SHEETS + enc(id) + '/values:batchClear', { ranges }),
    getSpreadsheet: (id, fields) => call('GET', SHEETS + enc(id) + (fields ? '?fields=' + enc(fields) : '')),
    driveSearch: (q, pageSize = 10) => call('GET', DRIVE + '?' + new URLSearchParams({ q, pageSize: String(pageSize), fields: 'files(id,name,parents)', supportsAllDrives: 'true', includeItemsFromAllDrives: 'true' })),
    driveCreate: (meta) => call('POST', DRIVE + '?supportsAllDrives=true&fields=id,name,parents', meta),
    driveGet: (id) => call('GET', DRIVE + '/' + enc(id) + '?supportsAllDrives=true&fields=id,name,parents,mimeType'),
  };
}

export function ssmCredentialsLoader(paramName) {
  let cache = null;
  return async () => {
    if (cache) return cache;
    if (!paramName) throw { code: 'server_not_connected', message: 'Google is not configured (GOOGLE_CREDENTIALS_PARAM is empty)' };
    const m = await import('@aws-sdk/client-ssm');
    const r = await new m.SSMClient({}).send(new m.GetParameterCommand({ Name: paramName, WithDecryption: true }));
    cache = JSON.parse(r.Parameter.Value);
    return cache;
  };
}

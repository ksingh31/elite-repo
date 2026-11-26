// Lambda entry points.
//   handler       API Gateway HTTP API (payload v2) behind CloudFront at /api/*
//     GET  /api/health                  -> { ok }                                   (no auth)
//     GET  /api/store[?versionId=]      -> { store, version }                       (version = S3 ETag)
//     PUT  /api/store  {store, baseVersion} -> { version } | 409 {error:{code:'conflict'}}
//     GET  /api/store/history           -> { versions:[{versionId, at, size}] }     (S3 object versions = server-side restore points)
//     POST /api/mcp    {server, tool, input} -> { payload } | 4xx {error:{code, message}}
//   dailyHandler  EventBridge Scheduler -> runDailyBackup()
import { loadConfig } from './config.mjs';
import { S3Repo, ConflictError } from './storeRepo.mjs';
import { makeGoogle, ssmCredentialsLoader } from './google.mjs';
import { makeGuard, WRITE_TOOLS } from './guard.mjs';
import { callTool } from './tools.mjs';
import { runDailyBackup } from './backup.mjs';
import { SEED_STORE } from './seed.mjs';

const json = (statusCode, body) => ({ statusCode, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' }, body: JSON.stringify(body) });
const err = (statusCode, code, message) => json(statusCode, { error: { code, message } });

export function validStore(s) {
  return !!(s && typeof s === 'object' && s.v === 4 && Array.isArray(s.projects) && s.projects.length && Array.isArray(s.budgets || []));
}

export function createApp({ cfg, repo, gapi, guard, log = console.log }) {
  const canWrite = (claims) => {
    if (!cfg.writersGroup) return true;
    const g = claims['cognito:groups'];
    const groups = Array.isArray(g) ? g : String(g || '').replace(/^\[|\]$/g, '').split(/[\s,]+/);
    return groups.includes(cfg.writersGroup);
  };
  return async function handle(event) {
    const method = event.requestContext?.http?.method || event.httpMethod || 'GET';
    const path = (event.rawPath || event.path || '/').replace(/\/+$/, '') || '/';
    const claims = event.requestContext?.authorizer?.jwt?.claims || {};
    const who = claims.email || claims.username || claims['cognito:username'] || claims.sub || 'local';
    let body = null;
    if (event.body) {
      try { body = JSON.parse(event.isBase64Encoded ? Buffer.from(event.body, 'base64').toString('utf8') : event.body); }
      catch (_) { return err(400, 'bad_request', 'body is not JSON'); }
    }
    try {
      if (path === '/api/health') return json(200, { ok: true });
      if (path === '/api/store' && method === 'GET') {
        const vid = event.queryStringParameters?.versionId;
        const r = await repo.get(vid);
        if (!r) return vid ? err(404, 'not_found', 'no such version') : json(200, { store: SEED_STORE, version: null });
        return json(200, r);
      }
      if (path === '/api/store' && method === 'PUT') {
        if (!canWrite(claims)) return err(403, 'not_writer', 'You can view this calculator but not save it.');
        if (!body || !validStore(body.store)) return err(400, 'bad_request', 'not a calculator store (v:4 with projects)');
        const size = Buffer.byteLength(JSON.stringify(body.store));
        if (size > cfg.maxStoreBytes) return err(413, 'too_large', 'store is ' + size + ' bytes');
        const r = await repo.put(body.store, body.baseVersion || null, { savedBy: who });
        log(JSON.stringify({ event: 'store.saved', by: who, savedAt: body.store.savedAt, size, version: r.version }));
        return json(200, r);
      }
      if (path === '/api/store/history' && method === 'GET') return json(200, { versions: await repo.history(50) });
      if (path === '/api/mcp' && method === 'POST') {
        if (!body || !body.server || !body.tool) return err(400, 'bad_request', 'server and tool are required');
        if ((WRITE_TOOLS.has(body.tool) || body.tool === 'create_file') && !canWrite(claims)) return err(403, 'denied', 'You can view this calculator but not change its sheets.');
        const r = await callTool(body, { gapi, guard });
        if (WRITE_TOOLS.has(body.tool) || body.tool === 'create_file') log(JSON.stringify({ event: 'sheets.write', by: who, tool: body.tool, id: body.input?.spreadsheetId, range: body.input?.range }));
        return json(200, r);
      }
      return err(404, 'not_found', method + ' ' + path);
    } catch (e) {
      if (e instanceof ConflictError) return err(409, 'conflict', 'Someone saved a newer version');
      if (e && e.code) {
        const st = e.code === 'denied' ? 403 : e.code === 'needs_reauth' || e.code === 'server_not_connected' ? 502 : 400;
        return err(st, e.code, e.message || e.code);
      }
      log(JSON.stringify({ event: 'error', message: String(e && e.stack || e) }));
      return err(500, 'server_error', 'Unexpected server error');
    }
  };
}

// ---- real wiring (Lambda) ----
let app = null, deps = null;
function realDeps() {
  if (deps) return deps;
  const cfg = loadConfig();
  const repo = new S3Repo({ bucket: cfg.dataBucket, key: cfg.storeKey });
  const gapi = makeGoogle({ loadCredentials: ssmCredentialsLoader(cfg.googleParam), impersonate: cfg.googleImpersonate });
  const guard = makeGuard({ cfg, gapi });
  deps = { cfg, repo, gapi, guard };
  return deps;
}
export const handler = async (event) => { if (!app) app = createApp(realDeps()); return app(event); };

export const dailyHandler = async () => {
  const { cfg, repo, gapi, guard } = realDeps();
  const cur = await repo.get();
  if (!cur) return { status: 'no store yet' };
  const m = await import('@aws-sdk/client-s3');
  const r = await new m.S3Client({}).send(new m.GetObjectCommand({ Bucket: cfg.siteBucket, Key: cfg.appKey }));
  const appHtml = await r.Body.transformToString();
  const results = await runDailyBackup({ store: cur.store, appHtml, gapi, guard, cfg });
  if (results.some((x) => x.status === 'failed')) throw new Error('daily backup failed for: ' + results.filter((x) => x.status === 'failed').map((x) => x.budget + ' (' + x.why + ')').join('; '));
  return results;
};

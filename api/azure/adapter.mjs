// OPTIONAL Azure Functions (v4 programming model) wrapper around the same API code. NOT TESTED in this repo's CI.
// Deploy this folder together with ../src as a Node 20 function app, with dependencies:
//   npm i @azure/functions @azure/storage-blob @azure/identity
// Routes mirror the Lambda: /api/health, /api/store (GET/PUT), /api/store/history, /api/mcp (POST).
// Auth: turn on App Service Authentication (Microsoft Entra ID) on the function app and require sign-in; the
// signed-in user's name arrives in x-ms-client-principal-name. Daily backup: timer at :37 every hour, runs only when it
// is 22:xx in Edmonton (Linux consumption plans have no time-zone setting for timers).
import { app } from '@azure/functions';
import { BlobServiceClient } from '@azure/storage-blob';
import { DefaultAzureCredential } from '@azure/identity';
import { createApp } from '../src/handler.mjs';
import { ConflictError } from '../src/storeRepo.mjs';
import { makeGoogle } from '../src/google.mjs';
import { makeGuard } from '../src/guard.mjs';
import { loadConfig } from '../src/config.mjs';
import { runDailyBackup } from '../src/backup.mjs';
import { zonedNow } from '../src/engine.mjs';

class BlobRepo {
  constructor() {
    const svc = new BlobServiceClient(`https://${process.env.STORE_ACCOUNT}.blob.core.windows.net`, new DefaultAzureCredential());
    this.blob = svc.getContainerClient(process.env.STORE_CONTAINER || 'store').getBlockBlobClient(process.env.STORE_KEY || 'store/store.json');
  }
  async get(versionId) {
    try {
      const b = versionId ? this.blob.withVersion(versionId) : this.blob;
      const r = await b.download();
      const chunks = []; for await (const c of r.readableStreamBody) chunks.push(c);
      return { store: JSON.parse(Buffer.concat(chunks).toString('utf8')), version: r.etag };
    } catch (e) { if (e.statusCode === 404) return null; throw e; }
  }
  async put(store, baseVersion, meta = {}) {
    const body = JSON.stringify(store);
    try {
      const r = await this.blob.upload(body, Buffer.byteLength(body), {
        blobHTTPHeaders: { blobContentType: 'application/json' }, metadata: { savedby: String(meta.savedBy || '').slice(0, 200) },
        conditions: baseVersion ? { ifMatch: baseVersion } : { ifNoneMatch: '*' },
      });
      return { version: r.etag };
    } catch (e) { if (e.statusCode === 412 || e.statusCode === 409) throw new ConflictError(); throw e; }
  }
  async history() { return []; } // list versions with ContainerClient.listBlobsFlat({includeVersions:true}) if needed
}

const cfg = loadConfig();
const gapi = makeGoogle({ loadCredentials: async () => JSON.parse(process.env.GOOGLE_CREDENTIALS_JSON || '{}') });
const deps = { cfg, repo: new BlobRepo(), gapi, guard: makeGuard({ cfg, gapi }) };
const handle = createApp(deps);

app.http('api', {
  route: '{*path}', methods: ['GET', 'PUT', 'POST'], authLevel: 'anonymous',
  handler: async (req) => {
    const url = new URL(req.url);
    const r = await handle({
      rawPath: url.pathname, requestContext: { http: { method: req.method }, authorizer: { jwt: { claims: { email: req.headers.get('x-ms-client-principal-name') || '' } } } },
      queryStringParameters: Object.fromEntries(url.searchParams), body: req.method === 'GET' ? null : await req.text(),
    });
    return { status: r.statusCode, headers: r.headers, body: r.body };
  },
});

app.timer('dailyBackup', {
  schedule: '0 37 * * * *',
  handler: async () => {
    if (!/ 22:3\d$/.test(zonedNow(cfg.timeZone))) return; // fires hourly at :37; only the 22:37 Edmonton run works
    const cur = await deps.repo.get(); if (!cur) return;
    const appHtml = await (await fetch(process.env.APP_URL)).text();
    const res = await runDailyBackup({ store: cur.store, appHtml, gapi, guard: deps.guard, cfg });
    if (res.some((x) => x.status === 'failed')) throw new Error('daily backup failed: ' + JSON.stringify(res));
  },
});

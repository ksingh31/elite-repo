#!/usr/bin/env node
// Local dev server: serves the standalone build and the same /api routes as the Lambda.
//   node api/local-server.mjs [--port 8787] [--dir app/standalone] [--store data/store.json]
// Store: file-backed (default data/store.json, seeded from samples/store.sample.json; gitignored).
// Google: in-memory fake by default. Set GOOGLE_CREDENTIALS_FILE=/path/key.json (+ BACKUP_FOLDER_ID, DENY_SHEET_IDS)
// to talk to real Google Sheets with the same write guard as production.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createApp } from './src/handler.mjs';
import { FileRepo } from './src/storeRepo.mjs';
import { makeGuard } from './src/guard.mjs';
import { makeGoogle } from './src/google.mjs';
import { makeFakeGoogle } from './src/fakeGoogle.mjs';
import { loadConfig } from './src/config.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const a = Object.fromEntries(process.argv.slice(2).reduce((acc, x, i, all) => (x.startsWith('--') ? [...acc, [x.slice(2), all[i + 1]]] : acc), []));
const PORT = +(a.port || process.env.PORT || 8787);
const DIR = path.resolve(root, a.dir || 'app/standalone');
const STORE = path.resolve(root, a.store || 'data/store.json');
if (!fs.existsSync(STORE)) { fs.mkdirSync(path.dirname(STORE), { recursive: true }); fs.copyFileSync(path.join(root, 'samples/store.sample.json'), STORE); }

const cfg = loadConfig({ BACKUP_FOLDER_ID: 'FOLDER', ...process.env });
const gapi = process.env.GOOGLE_CREDENTIALS_FILE
  ? makeGoogle({ loadCredentials: async () => JSON.parse(fs.readFileSync(process.env.GOOGLE_CREDENTIALS_FILE, 'utf8')) })
  : makeFakeGoogle({ folderId: cfg.backupFolderId });
if (!process.env.GOOGLE_CREDENTIALS_FILE) {
  // the sample store's budget points at SAMPLE-BACKUP-SHEET-ID: make it a sheet inside the fake backup folder
  const b = gapi.book('SAMPLE-BACKUP-SHEET-ID'); b.name = 'Sample budget – backup';
}
const repo = new FileRepo(STORE);
const app = createApp({ cfg, repo, gapi, guard: makeGuard({ cfg, gapi }), log: () => {} });
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.json': 'application/json', '.css': 'text/css' };

http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x');
  if (url.pathname.startsWith('/api/')) {
    let body = ''; for await (const c of req) body += c;
    const r = await app({ rawPath: url.pathname, requestContext: { http: { method: req.method } }, queryStringParameters: Object.fromEntries(url.searchParams), body: body || null });
    res.writeHead(r.statusCode, r.headers); res.end(r.body); return;
  }
  const f = path.join(DIR, url.pathname === '/' ? 'index.html' : path.normalize(url.pathname).replace(/^(\.\.[/\\])+/, ''));
  if (!f.startsWith(DIR) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); res.end('not found'); return; }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
  fs.createReadStream(f).pipe(res);
}).listen(PORT, () => console.log(`calculator on http://localhost:${PORT}  (store: ${path.relative(root, STORE)}, google: ${process.env.GOOGLE_CREDENTIALS_FILE ? 'real' : 'fake'})`));

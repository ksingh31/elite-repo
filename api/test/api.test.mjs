import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { createApp } from '../src/handler.mjs';
import { MemoryRepo } from '../src/storeRepo.mjs';
import { makeGuard } from '../src/guard.mjs';
import { makeFakeGoogle } from '../src/fakeGoogle.mjs';
import { loadConfig } from '../src/config.mjs';

const sample = JSON.parse(fs.readFileSync(new URL('../../samples/store.sample.json', import.meta.url)));
const ev = (method, path, body, claims) => ({ rawPath: path, requestContext: { http: { method }, authorizer: claims ? { jwt: { claims } } : undefined }, body: body ? JSON.stringify(body) : null });
const setup = (env = {}) => {
  const cfg = loadConfig({ BACKUP_FOLDER_ID: 'FOLDER', DENY_SHEET_IDS: 'INVOICE,MASTER', ...env });
  const gapi = makeFakeGoogle({ folderId: 'FOLDER' });
  const repo = new MemoryRepo();
  return { cfg, gapi, repo, app: createApp({ cfg, repo, gapi, guard: makeGuard({ cfg, gapi }), log: () => {} }) };
};
const J = (r) => JSON.parse(r.body);

test('GET /api/store returns the seed store when nothing is saved yet', async () => {
  const { app } = setup();
  const r = await app(ev('GET', '/api/store'));
  assert.equal(r.statusCode, 200);
  assert.equal(J(r).version, null);
  assert.equal(J(r).store.v, 4);
});

test('PUT /api/store: first save, then optimistic concurrency', async () => {
  const { app } = setup();
  const r1 = await app(ev('PUT', '/api/store', { store: sample, baseVersion: null }));
  assert.equal(r1.statusCode, 200);
  const v1 = J(r1).version;
  const r2 = await app(ev('PUT', '/api/store', { store: { ...sample, savedAt: 'x' }, baseVersion: v1 }));
  assert.equal(r2.statusCode, 200);
  // a second person still on v1 gets a conflict, nothing is overwritten
  const r3 = await app(ev('PUT', '/api/store', { store: { ...sample, savedAt: 'y' }, baseVersion: v1 }));
  assert.equal(r3.statusCode, 409);
  assert.equal(J(r3).error.code, 'conflict');
  const g = J(await app(ev('GET', '/api/store')));
  assert.equal(g.store.savedAt, 'x');
  const h = J(await app(ev('GET', '/api/store/history')));
  assert.equal(h.versions.length, 2);
});

test('PUT /api/store rejects things that are not a store', async () => {
  const { app } = setup();
  assert.equal((await app(ev('PUT', '/api/store', { store: { v: 3, projects: [] } }))).statusCode, 400);
  assert.equal((await app(ev('PUT', '/api/store', { store: { v: 4, projects: [] } }))).statusCode, 400);
});

test('WRITERS_GROUP: viewers cannot save or write sheets', async () => {
  const { app } = setup({ WRITERS_GROUP: 'writers' });
  const r = await app(ev('PUT', '/api/store', { store: sample }, { email: 'v@x', 'cognito:groups': ['viewers'] }));
  assert.equal(r.statusCode, 403);
  assert.equal(J(r).error.code, 'not_writer');
  const ok = await app(ev('PUT', '/api/store', { store: sample }, { email: 'w@x', 'cognito:groups': '[writers]' }));
  assert.equal(ok.statusCode, 200);
  const m = await app(ev('POST', '/api/mcp', { server: 'Google Sheets', tool: 'update_values', input: { spreadsheetId: 'S', range: "'Budget'!A1:A1", values: [['x']] } }, { 'cognito:groups': ['viewers'] }));
  assert.equal(m.statusCode, 403);
});

test('POST /api/mcp proxies tools with the connector payload shape', async () => {
  const { app, gapi } = setup();
  const b = gapi.book('S1'); b.tabs.push({ sheetId: 5, title: 'Budget' });
  let r = await app(ev('POST', '/api/mcp', { server: 'Google Sheets', tool: 'update_values', input: { spreadsheetId: 'S1', range: "'Budget'!A1:B1", values: [['a', 'b']] } }));
  assert.equal(r.statusCode, 200);
  r = await app(ev('POST', '/api/mcp', { server: 'Google Sheets', tool: 'get_values', input: { spreadsheetId: 'S1', range: "'Budget'!A1:B" } }));
  assert.deepEqual(J(r).payload.values, [['a', 'b']]);
  r = await app(ev('POST', '/api/mcp', { server: 'Google Sheets', tool: 'get_spreadsheet', input: { spreadsheetId: 'S1', fields: ['sheets.properties.sheetId', 'sheets.properties.title'] } }));
  assert.deepEqual(J(r).payload.sheets.map((s) => s.properties.title), ['Sheet1', 'Budget']);
  r = await app(ev('POST', '/api/mcp', { server: 'Google Sheets', tool: 'get_values', input: { spreadsheetId: 'S1', range: "'To check'!A3:L" } }));
  assert.equal(r.statusCode, 400);
  assert.match(J(r).error.message, /Unable to parse range/);
});

test('POST /api/mcp: Drive search uses the v2-style query of the app and create_file lands in the folder', async () => {
  const { app } = setup();
  let r = await app(ev('POST', '/api/mcp', { server: 'Google Drive', tool: 'create_file', input: { title: 'B – backup', contentMimeType: 'application/vnd.google-apps.spreadsheet', parentId: 'FOLDER' } }));
  assert.equal(r.statusCode, 200);
  const id = J(r).payload.id;
  r = await app(ev('POST', '/api/mcp', { server: 'Google Drive', tool: 'search_files', input: { query: "parentId = 'FOLDER' and title = 'B – backup' and trashed = false", pageSize: 5 } }));
  assert.equal(J(r).payload.files[0].id, id);
  r = await app(ev('POST', '/api/mcp', { server: 'Google Drive', tool: 'create_file', input: { title: 'x', contentMimeType: 'application/vnd.google-apps.spreadsheet', parentId: 'ELSEWHERE' } }));
  assert.equal(r.statusCode, 403);
});

test('unknown route is 404, bad JSON is 400', async () => {
  const { app } = setup();
  assert.equal((await app(ev('GET', '/api/nope'))).statusCode, 404);
  assert.equal((await app({ rawPath: '/api/store', requestContext: { http: { method: 'PUT' } }, body: '{bad' })).statusCode, 400);
});

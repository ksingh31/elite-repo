import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { runDailyBackup } from '../src/backup.mjs';
import { loadEngine, storeFromHtml, zonedNow } from '../src/engine.mjs';
import { makeGuard } from '../src/guard.mjs';
import { makeFakeGoogle } from '../src/fakeGoogle.mjs';
import { loadConfig } from '../src/config.mjs';

const html = fs.readFileSync(new URL('../../app/artifact/index.html', import.meta.url), 'utf8');
const store = storeFromHtml(html);
const cfg = loadConfig({ BACKUP_FOLDER_ID: 'FOLDER', DENY_SHEET_IDS: 'INVOICE' });
const mk = () => { const gapi = makeFakeGoogle({ folderId: 'FOLDER' }); return { gapi, guard: makeGuard({ cfg, gapi }) }; };
const quiet = { log: () => {}, sleep: async () => {} };

test('engine markers load calc() and buildSheets() from the app HTML', () => {
  const { calc, buildSheets } = loadEngine(html);
  const p = store.projects[0];
  const r = calc(p, p.co);
  assert.ok(Number.isFinite(r.profit0));
  assert.equal(r.opts.length, 5);
  assert.equal(typeof buildSheets, 'function');
});

test('zonedNow formats Edmonton time like the app', () => {
  assert.equal(zonedNow('America/Edmonton', new Date('2026-07-01T04:37:00Z')), '2026-06-30 22:37');
});

test('daily backup: safe swap writes the data tabs, keeps other tabs, appends restore point + log', async () => {
  const { gapi, guard } = mk();
  const sid = store.budgets[0].sheetId;
  const b = gapi.book(sid); b.tabs.push({ sheetId: 77, title: 'To check' }); b.cells.set('To check|3', ['keep me']);
  const now = new Date('2026-11-27T05:37:00Z');
  const res = await runDailyBackup({ store, appHtml: html, gapi, guard, cfg, now, ...quiet });
  assert.equal(res[0].status, 'backed up', JSON.stringify(res));
  const titles = b.tabs.map((t) => t.title);
  for (const t of ['Read me', 'Summary', 'Budget', 'To check', 'Backup log', 'Backup data']) assert.ok(titles.includes(t), t + ' in ' + titles);
  assert.ok(!titles.some((t) => / \(updating\)$/.test(t)));
  assert.deepEqual(b.cells.get('To check|3'), ['keep me']);
  assert.match(String(b.cells.get('Summary|2')[0]), new RegExp(zonedNow('America/Edmonton', now)));
  assert.equal(b.log.filter((r) => /^\d{4}/.test(r[0])).length, 1);
  assert.equal(b.data.filter((r) => /^\d{4}/.test(r[0])).length, 1);
  // the restore point is the full store JSON in 40,000-character parts
  const row = b.data.find((r) => /^\d{4}/.test(r[0]));
  assert.deepEqual(JSON.parse(row.slice(3, 3 + row[2]).join('')), store);

  // run again 30 min later: skipped (someone just backed up)
  const r2 = await runDailyBackup({ store, appHtml: html, gapi, guard, cfg, now: new Date(now.getTime() + 30 * 60000), ...quiet });
  assert.equal(r2[0].status, 'skipped');
  // a day later, same savedAt: nothing changed -> skipped
  const r3 = await runDailyBackup({ store, appHtml: html, gapi, guard, cfg, now: new Date(now.getTime() + 24 * 3600000), ...quiet });
  assert.equal(r3[0].status, 'skipped');
  assert.match(r3[0].why, /nothing changed/);
  // after a save, it backs up again
  const r4 = await runDailyBackup({ store: { ...store, savedAt: '2099-01-01T00:00:00.000Z' }, appHtml: html, gapi, guard, cfg, now: new Date(now.getTime() + 25 * 3600000), ...quiet });
  assert.equal(r4[0].status, 'backed up', JSON.stringify(r4));
});

test('daily backup: a budget without a sheet gets one made in the backup folder (reported, store untouched)', async () => {
  const { gapi, guard } = mk();
  const s2 = JSON.parse(JSON.stringify(store)); delete s2.budgets[0].sheetId;
  const res = await runDailyBackup({ store: s2, appHtml: html, gapi, guard, cfg, now: new Date('2026-11-27T05:37:00Z'), ...quiet });
  assert.equal(res[0].status, 'backed up');
  assert.equal(res[0].created, true);
  assert.ok(!s2.budgets[0].sheetId);
});

test('daily backup never writes a denied sheet', async () => {
  const { gapi, guard } = mk();
  const s2 = JSON.parse(JSON.stringify(store)); s2.budgets[0].sheetId = 'INVOICE'; gapi.book('INVOICE');
  const res = await runDailyBackup({ store: s2, appHtml: html, gapi, guard, cfg, now: new Date('2026-11-27T05:37:00Z'), ...quiet });
  assert.equal(res[0].status, 'failed');
  assert.match(res[0].why, /write policy/);
  assert.deepEqual(gapi.book('INVOICE').tabs.map((t) => t.title), ['Sheet1']);
});

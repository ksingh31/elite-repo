// Daily backup (EventBridge Scheduler, 22:37 America/Edmonton). Server-side twin of the Claude scheduled task
// "Daily calculator backup" (docs/daily-backup-task.md): same steps, same safe swap, same skip rules.
//
// For each budget in the team store:
//   1. find its sheet: budget.sheetId, else a Drive search in the backup folder for "<budget name> – backup", else create it
//   2. skip if the last dated 'Backup log' row is < 2 hours old (someone just saved) or its column G equals store.savedAt (nothing changed)
//   3. plan = buildSheets(store, calc, 'Daily backup', when, existingTabs, {budget: id}, {})   (the app's own code)
//   4. safe swap: add hidden "<tab> (updating)" tabs, write values (250 rows / call) and formats (400 requests / call),
//      check 'Summary (updating)'!A2 is not empty, delete the old data tabs + rename/unhide the new ones in ONE batchUpdate,
//      check 'Summary'!A2 shows this backup time, then append the restore point ('Backup data') and the log line ('Backup log')
// Never touches any other tab; never changes the store (a new sheet id is reported, like the Claude task does).
import { loadEngine, zonedNow } from './engine.mjs';
import { callTool } from './tools.mjs';

const colL = (n) => { let s = ''; while (n > 0) { const r = (n - 1) % 26; s = String.fromCharCode(65 + r) + s; n = (n - 1 - r) / 26; } return s; };
const vals = (r) => (r && r.payload && r.payload.values) || [];
const tabsOf = (r) => ((r && r.payload && r.payload.sheets) || []).map((s) => s.properties || s).filter((p) => p && p.title != null);
const minutesBetween = (a, b) => { const p = (s) => { const m = String(s).match(/^(\d{4})-(\d{2})-(\d{2}) (\d{1,2}):(\d{2})/); return m ? Date.UTC(+m[1], m[2] - 1, +m[3], +m[4], +m[5]) : NaN; }; return (p(b) - p(a)) / 60000; };

async function withRetry(fn, sleep) {
  let last;
  for (const w of [0, 2000, 6000, 15000]) {
    if (w) await sleep(w);
    try { return await fn(); } catch (e) { last = e; if (e && (e.code === 'denied' || e.code === 'tool_error')) throw e; }
  }
  throw last;
}

export async function runDailyBackup({ store, appHtml, gapi, guard, cfg, now = new Date(), sleep = (ms) => new Promise((r) => setTimeout(r, ms)), log = console.log }) {
  const { calc, buildSheets } = loadEngine(appHtml);
  const when = zonedNow(cfg.timeZone, now);
  const S = (tool, input) => withRetry(() => callTool({ server: 'Google Sheets', tool, input }, { gapi, guard }), sleep);
  const D = (tool, input) => withRetry(() => callTool({ server: 'Google Drive', tool, input }, { gapi, guard }), sleep);
  const results = [];
  for (const b of (store.budgets || []).filter((x) => x.versions && x.versions.length)) {
    const res = { budget: b.name, id: b.id };
    try {
      // 1. find the sheet
      let sid = b.sheetId || null;
      if (!sid && cfg.backupFolderId) {
        const title = b.name + ' – backup';
        const r = await D('search_files', { query: "parentId = '" + cfg.backupFolderId + "' and title = '" + title.replace(/'/g, "\\'") + "' and trashed = false", pageSize: 5 });
        sid = (r.payload.files[0] || {}).id || null;
        if (!sid) { sid = (await D('create_file', { title, contentMimeType: 'application/vnd.google-apps.spreadsheet', parentId: cfg.backupFolderId })).payload.id; res.created = true; }
        res.note = 'sheet not remembered in the calculator: click Back up now or Save for team so it stores the sheet id';
      }
      if (!sid) throw { step: 'finding the sheet', message: 'no sheet id and no backup folder configured' };
      res.sheet = 'https://docs.google.com/spreadsheets/d/' + sid + '/edit';
      // 2. skip checks
      let logRows = [];
      try { logRows = vals(await S('get_values', { spreadsheetId: sid, range: "'Backup log'!A1:G" })); } catch (_) {}
      const last = logRows.filter((r) => /^\d{4}-\d{2}-\d{2}/.test(String(r[0] || ''))).pop();
      if (last) {
        const age = minutesBetween(String(last[0]), when);
        if (age >= 0 && age < 120) { results.push({ ...res, status: 'skipped', why: 'backed up ' + Math.round(age) + ' min ago' }); continue; }
        if (store.savedAt && String(last[6] || '') === store.savedAt) { results.push({ ...res, status: 'skipped', why: 'nothing changed since the last backup' }); continue; }
      }
      // 3. plan
      const ex = tabsOf(await S('get_spreadsheet', { spreadsheetId: sid, fields: ['sheets.properties.sheetId', 'sheets.properties.title'] }));
      const plan = buildSheets(store, calc, 'Daily backup', when, ex, { budget: b.id }, {});
      // 4. safe swap
      if (plan.structure.length) await S('update_spreadsheet', { spreadsheetId: sid, requests: plan.structure });
      for (const t of plan.perTab) {
        const w = t.values[0] ? t.values[0].length : 1, q = "'" + t.title.replace(/'/g, "''") + "'!";
        for (let r = 0; r < t.values.length; r += 250) {
          const part = t.values.slice(r, r + 250);
          await S('update_values', { spreadsheetId: sid, range: q + 'A' + (r + 1) + ':' + colL(w) + (r + part.length), values: part });
        }
        for (let k = 0; k < t.requests.length; k += 400) await S('update_spreadsheet', { spreadsheetId: sid, requests: t.requests.slice(k, k + 400) });
      }
      const stg = plan.perTab.find((t) => t.final === 'Summary');
      if (stg) {
        const cv = vals(await S('get_values', { spreadsheetId: sid, range: "'" + stg.title + "'!A2" }));
        if (!String((cv[0] || [])[0] || '').trim()) throw { step: 'checking the new tabs', message: 'Summary (updating) came back empty; the old tabs were kept' };
      }
      const cur = tabsOf(await S('get_spreadsheet', { spreadsheetId: sid, fields: ['sheets.properties.sheetId', 'sheets.properties.title'] }));
      const staged = plan.perTab.filter((t) => t.final);
      if (staged.some((t) => !cur.some((s) => s.title === t.title))) throw { step: 'swapping in the new tabs', message: 'another backup ran at the same time' };
      const finals = new Set(staged.map((t) => t.final));
      const reqs = cur.filter((s) => s.sheetId !== 0 && finals.has(s.title)).map((s) => ({ deleteSheet: { sheetId: s.sheetId } })).concat(plan.finalize.filter((r) => !r.deleteSheet));
      await S('update_spreadsheet', { spreadsheetId: sid, requests: reqs });
      const cv2 = vals(await S('get_values', { spreadsheetId: sid, range: "'Summary'!A2" }));
      if (!String((cv2[0] || [])[0] || '').includes(when)) throw { step: 'checking the result', message: 'Summary does not show this backup time' };
      await S('append_values', { spreadsheetId: sid, range: "'Backup data'!A1", values: plan.data });
      await S('append_values', { spreadsheetId: sid, range: "'Backup log'!A1", values: plan.log });
      results.push({ ...res, status: 'backed up', when });
    } catch (e) {
      results.push({ ...res, status: 'failed', step: e && e.step, why: (e && (e.message || e.code)) || String(e) });
    }
  }
  results.forEach((r) => log(JSON.stringify(r)));
  return results;
}

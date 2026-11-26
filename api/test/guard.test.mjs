import test from 'node:test';
import assert from 'node:assert/strict';
import { makeGuard } from '../src/guard.mjs';
import { makeFakeGoogle } from '../src/fakeGoogle.mjs';
import { loadConfig } from '../src/config.mjs';

const cfg = loadConfig({ BACKUP_FOLDER_ID: 'FOLDER', DENY_SHEET_IDS: 'INVOICE, MASTER', ALLOW_SHEET_IDS: 'EXTRA' });
const gapi = makeFakeGoogle({ folderId: 'FOLDER' });
gapi.book('BK').tabs.push({ sheetId: 1, title: 'Summary' }, { sheetId: 2, title: 'To check' }, { sheetId: 3, title: 'Budget (updating)' }, { sheetId: 4, title: 'My notes' });
const inv = gapi.book('INVOICE'); inv.parents = ['FOLDER']; // even inside the folder, the deny list wins
gapi.book('OTHER').parents = ['SOMEWHERE'];
const guard = makeGuard({ cfg, gapi });
const W = (id, extra = {}) => ({ spreadsheetId: id, range: "'Summary'!A1:B2", values: [['x']], ...extra });
const denied = (p) => assert.rejects(p, (e) => e.code === 'denied');

test('reads are allowed anywhere', async () => {
  await guard.check('Google Sheets', 'get_values', { spreadsheetId: 'INVOICE', range: 'A1' });
  await guard.check('Google Sheets', 'get_spreadsheet', { spreadsheetId: 'OTHER' });
});
test('deny list always wins (invoice sheet, master sheet)', async () => {
  await denied(guard.check('Google Sheets', 'update_values', W('INVOICE')));
  await denied(guard.check('Google Sheets', 'append_values', { spreadsheetId: 'MASTER', range: "'Backup log'!A1", values: [] }));
});
test('only sheets in the backup folder (or the allow list) can be written', async () => {
  await guard.check('Google Sheets', 'update_values', W('BK'));
  await guard.check('Google Sheets', 'update_values', W('EXTRA'));
  await denied(guard.check('Google Sheets', 'update_values', W('OTHER')));
  await denied(guard.check('Google Sheets', 'update_values', W('UNKNOWN')));
});
test('update_spreadsheet: only the request types the calculator uses; deleteSheet only for data tabs', async () => {
  await guard.check('Google Sheets', 'update_spreadsheet', { spreadsheetId: 'BK', requests: [{ deleteSheet: { sheetId: 1 } }, { deleteSheet: { sheetId: 3 } }, { addSheet: { properties: { sheetId: 9, title: 'x' } } }] });
  await denied(guard.check('Google Sheets', 'update_spreadsheet', { spreadsheetId: 'BK', requests: [{ deleteSheet: { sheetId: 2 } }] }));
  await denied(guard.check('Google Sheets', 'update_spreadsheet', { spreadsheetId: 'BK', requests: [{ deleteSheet: { sheetId: 4 } }] }));
  await denied(guard.check('Google Sheets', 'update_spreadsheet', { spreadsheetId: 'BK', requests: [{ deleteDimension: {} }] }));
});
test('To check: only one row of K:L', async () => {
  await guard.check('Google Sheets', 'update_values', W('BK', { range: "'To check'!K7:L7" }));
  await guard.check('Google Sheets', 'update_values', W('BK', { range: "'To check'!K3:L3" }));
  await denied(guard.check('Google Sheets', 'update_values', W('BK', { range: "'To check'!A7:L7" })));
  await denied(guard.check('Google Sheets', 'update_values', W('BK', { range: "'To check'!K7:L9" })));
  await denied(guard.check('Google Sheets', 'update_values', W('BK', { range: "'To check'!K2:L2" })));
});
test('Backup data / log: append only (plus the header row the app writes when it creates them)', async () => {
  await guard.check('Google Sheets', 'append_values', { spreadsheetId: 'BK', range: "'Backup data'!A1", values: [] });
  await guard.check('Google Sheets', 'update_values', W('BK', { range: "'Backup log'!A1:G1" }));
  await denied(guard.check('Google Sheets', 'update_values', W('BK', { range: "'Backup data'!A5:L5" })));
  await denied(guard.check('Google Sheets', 'append_values', { spreadsheetId: 'BK', range: "'Summary'!A1", values: [] }));
});
test('create_file only as a Google Sheet in the backup folder', async () => {
  await guard.check('Google Drive', 'create_file', { title: 't', contentMimeType: 'application/vnd.google-apps.spreadsheet', parentId: 'FOLDER' });
  await denied(guard.check('Google Drive', 'create_file', { title: 't', contentMimeType: 'text/plain', parentId: 'FOLDER' }));
  await denied(guard.check('Google Drive', 'create_file', { title: 't', contentMimeType: 'application/vnd.google-apps.spreadsheet', parentId: 'X' }));
});

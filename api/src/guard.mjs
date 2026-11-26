// Server-side write policy for Google Sheets / Drive. Mirrors the team's standing rule:
//   every sheet the team provided is an ORIGINAL and READ-ONLY; the only sheets that may be written are the
//   calculator's own backup sheets (one per budget, kept in the backup Drive folder).
// Enforced here even though the app has its own checks, so a bug or a hand-edited store can never write elsewhere.
//
// A write (update_values, append_values, update_spreadsheet, batch_clear_values) is allowed only when:
//   1. the spreadsheet id is NOT in DENY_SHEET_IDS (invoice sheet, retired master sheet...)   -> always wins
//   2. AND it is in ALLOW_SHEET_IDS, or the file's parent folder is BACKUP_FOLDER_ID (looked up in Drive, cached)
//   3. AND the request itself is one the calculator makes:
//      - update_spreadsheet: only addSheet / deleteSheet / updateSheetProperties / repeatCell / updateBorders /
//        updateDimensionProperties / setBasicFilter / addConditionalFormatRule; deleteSheet only for the six data tabs
//        (Summary, Budget, Trade, Material, Service, Other) or their " (updating)" copies
//      - update_values to the "To check" tab: only one row of columns K:L (Status, Resolution), row >= 3
//      - append_values: only to 'Backup data' or 'Backup log'
// create_file (Drive) is allowed only as a Google Sheet inside BACKUP_FOLDER_ID.
export const DATA_TABS = ['Summary', 'Budget', 'Trade', 'Material', 'Service', 'Other'];
const OK_REQUESTS = new Set(['addSheet', 'deleteSheet', 'updateSheetProperties', 'repeatCell', 'updateBorders', 'updateDimensionProperties', 'setBasicFilter', 'addConditionalFormatRule']);
export const WRITE_TOOLS = new Set(['update_values', 'append_values', 'update_spreadsheet', 'batch_clear_values']);

const deny = (message) => { throw { code: 'denied', message: 'Refused by the server write policy: ' + message }; };
const tabOf = (range) => { const m = String(range || '').match(/^'((?:[^']|'')*)'!|^([^!']+)!/); return m ? (m[1] != null ? m[1].replace(/''/g, "'") : m[2]) : ''; };

export function makeGuard({ cfg, gapi }) {
  const parentCache = new Map();
  async function inBackupFolder(id) {
    if (!cfg.backupFolderId) return false;
    if (!parentCache.has(id)) {
      try { const f = await gapi.driveGet(id); parentCache.set(id, (f.parents || []).includes(cfg.backupFolderId)); }
      catch (_) { return false; }
    }
    return parentCache.get(id);
  }
  async function checkSheet(id) {
    if (!id) deny('no spreadsheet id');
    if (cfg.denySheetIds.has(id)) deny('this spreadsheet is read-only (deny list)');
    if (cfg.allowSheetIds.has(id)) return;
    if (await inBackupFolder(id)) return;
    deny('only the calculator\'s own backup sheets (in the backup folder) can be written');
  }
  return {
    async check(server, tool, input = {}) {
      if (server === 'Google Drive') {
        if (tool === 'create_file') {
          if (!cfg.backupFolderId || input.parentId !== cfg.backupFolderId) deny('new files can only be made in the backup folder');
          if (input.contentMimeType !== 'application/vnd.google-apps.spreadsheet') deny('only Google Sheets can be created');
        }
        return;
      }
      if (!WRITE_TOOLS.has(tool)) return; // reads are fine
      await checkSheet(input.spreadsheetId);
      if (tool === 'update_spreadsheet') {
        const reqs = Array.isArray(input.requests) ? input.requests : [];
        let titles = null;
        for (const r of reqs) {
          const kinds = Object.keys(r || {});
          if (kinds.length !== 1 || !OK_REQUESTS.has(kinds[0])) deny('request type ' + kinds.join('+') + ' is not allowed');
          if (r.deleteSheet) {
            if (!titles) {
              const s = await gapi.getSpreadsheet(input.spreadsheetId, 'sheets.properties(sheetId,title)');
              titles = new Map((s.sheets || []).map((x) => [x.properties.sheetId, x.properties.title]));
            }
            const t = titles.get(r.deleteSheet.sheetId);
            if (t == null) continue; // Google will answer "No sheet with id" itself
            const base = String(t).replace(/ \(updating\)$/, '');
            if (!DATA_TABS.includes(base)) deny('the tab "' + t + '" can never be deleted');
          }
        }
      }
      if (tool === 'update_values' || tool === 'batch_clear_values') {
        const ranges = tool === 'update_values' ? [input.range] : (input.ranges || []);
        for (const range of ranges) {
          const tab = tabOf(range);
          if (tab === 'To check') {
            const m = String(range).match(/^'To check'!K(\d+):L(\d+)$/);
            if (tool !== 'update_values' || !m || m[1] !== m[2] || +m[1] < 3) deny('only one row of the Status / Resolution columns (K:L) of To check can be written');
          }
          if (tab === 'Backup data' || tab === 'Backup log') {
            // the app only writes their header row when it creates them
            if (tool !== 'update_values' || !/!A1:[A-Z]+1$/.test(String(range))) deny('restore points and the backup log are append-only');
          }
          if (tab === 'Read me' && tool !== 'update_values') deny('Read me can only be rewritten by a backup');
        }
      }
      if (tool === 'append_values') {
        const tab = tabOf(input.range);
        if (tab !== 'Backup data' && tab !== 'Backup log') deny('appends are only allowed to Backup data / Backup log');
      }
    },
  };
}

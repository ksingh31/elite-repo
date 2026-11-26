// In-memory stand-in for the Google Sheets / Drive REST API (same interface as makeGoogle()).
// Used by the unit tests and by the local dev server (api/local-server.mjs) when no real credentials are set.
export function makeFakeGoogle({ folderId = 'FOLDER' } = {}) {
  const books = {}; // id -> { name, parents, tabs:[{sheetId,title,hidden}], cells: Map("'Tab'|row" -> array), data:[], log:[] }
  let n = 0;
  const book = (id) => books[id] || (books[id] = { name: id, parents: [folderId], tabs: [{ sheetId: 0, title: 'Sheet1' }], cells: new Map(), data: [], log: [] });
  const fail = (message, status = 400) => { throw { code: status === 404 ? 'tool_error' : 'tool_error', message, status }; };
  const tabName = (range) => { const m = String(range).match(/^'((?:[^']|'')*)'!|^([^!]+)!/); return m ? (m[1] != null ? m[1].replace(/''/g, "'") : m[2]) : String(range); };
  const rows = (b, tab) => [...b.cells.entries()].filter(([k]) => k.startsWith(tab + '|')).map(([k, v]) => [+k.split('|')[1], v]).sort((a, c) => a[0] - c[0]);
  return {
    books, book,
    async getValues(id, range) {
      const b = book(id), tab = tabName(range);
      if (tab === 'Backup data' || tab === 'Backup log') {
        if (!b.tabs.some((t) => t.title === tab)) fail("Unable to parse range: " + range);
        const L = tab === 'Backup data' ? b.data : b.log;
        const m = String(range).match(/!A(\d+)(?::[A-Z]+(\d+)?)?$/);
        const from = m ? +m[1] : 1, to = m && m[2] ? +m[2] : L.length;
        return { values: L.slice(from - 1, to) };
      }
      if (!b.tabs.some((t) => t.title === tab)) fail('Unable to parse range: ' + range);
      const m = String(range).match(/!A(\d+)(?::[A-Z]+(\d+)?)?$/);
      const from = m ? +m[1] : 1, to = m && m[2] ? +m[2] : 1e9;
      return { values: rows(b, tab).filter(([r]) => r >= from && r <= to).map(([, v]) => v) };
    },
    async updateValues(id, range, values) {
      const b = book(id), tab = tabName(range);
      if (!b.tabs.some((t) => t.title === tab)) fail('Unable to parse range: ' + range);
      const m = String(range).match(/!([A-Z]+)(\d+)/);
      const r0 = m ? +m[2] : 1;
      values.forEach((row, k) => b.cells.set(tab + '|' + (r0 + k), m && m[1] !== 'A' ? Object.assign([], b.cells.get(tab + '|' + (r0 + k)) || [], Object.fromEntries(row.map((v, j) => [m[1].charCodeAt(0) - 65 + j, v]))) : row));
      return { updatedRows: values.length };
    },
    async appendValues(id, range, values) {
      const b = book(id), tab = tabName(range);
      if (!b.tabs.some((t) => t.title === tab)) fail('Unable to parse range: ' + range);
      (tab === 'Backup data' ? b.data : tab === 'Backup log' ? b.log : []).push(...values);
      return { updates: { updatedRows: values.length } };
    },
    async batchUpdate(id, requests) {
      const b = book(id), T = JSON.parse(JSON.stringify(b.tabs));
      for (const r of requests) {
        if (r.addSheet) { const p = r.addSheet.properties; if (T.some((z) => z.sheetId === p.sheetId || z.title === p.title)) fail('Invalid requests: duplicate sheet ' + p.title); T.push({ sheetId: p.sheetId, title: p.title, hidden: !!p.hidden }); }
        if (r.deleteSheet) { const x = T.find((z) => z.sheetId === r.deleteSheet.sheetId); if (!x) fail('No sheet with id: ' + r.deleteSheet.sheetId); T.splice(T.indexOf(x), 1); for (const k of [...b.cells.keys()]) if (k.startsWith(x.title + '|')) b.cells.delete(k); }
        if (r.updateSheetProperties) {
          const p = r.updateSheetProperties.properties, x = T.find((z) => z.sheetId === p.sheetId); if (!x) fail('No sheet with id: ' + p.sheetId);
          if (p.title != null && p.title !== x.title) { for (const [k, v] of [...b.cells.entries()]) if (k.startsWith(x.title + '|')) { b.cells.delete(k); b.cells.set(p.title + '|' + k.split('|')[1], v); } x.title = p.title; }
          if (p.hidden != null) x.hidden = p.hidden;
        }
      }
      b.tabs = T;
      return { replies: requests.map(() => ({})) };
    },
    async batchClear(id, ranges) { return { clearedRanges: ranges }; },
    async getSpreadsheet(id) { const b = book(id); return { properties: { title: b.name }, sheets: b.tabs.map((p) => ({ properties: { ...p } })) }; },
    async driveSearch(q) {
      const m = q.match(/'([^']+)' in parents and name = '((?:[^'\\]|\\.)*)'/);
      const files = m ? Object.entries(books).filter(([, b]) => b.parents.includes(m[1]) && b.name === m[2].replace(/\\'/g, "'")).map(([id, b]) => ({ id, name: b.name, parents: b.parents })) : [];
      return { files };
    },
    async driveCreate(meta) { const id = 'NEWSHEET' + (++n); const b = book(id); b.name = meta.name; b.parents = meta.parents || []; return { id, name: meta.name }; },
    async driveGet(id) { if (!books[id]) fail('File not found: ' + id, 404); return { id, name: books[id].name, parents: books[id].parents }; },
  };
}

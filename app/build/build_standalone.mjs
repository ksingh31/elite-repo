#!/usr/bin/env node
// Regenerates the standalone (AWS / any static host) build from the Claude-artifact HTML.
// The app code is copied unchanged; only the wrapper changes:
//   - <script src="config.js"> + <script src="platform.js"> are added at the top of <head>
//   - the embedded store is emptied (the data is loaded from the API at runtime)
//   - the app's main <script> becomes type="text/x-elite-app" id="elite-app"; platform.js runs it after the store is loaded
//   - optional: public id placeholders (YOUR_BACKUP_FOLDER_ID, ...) are replaced from a private ids file
//
// usage: node app/build/build_standalone.mjs [--in app/artifact/index.html] [--out app/standalone]
//                                            [--ids config/private.json] [--config config.json]
//   --config writes <out>/config.js from a JSON file ({apiBase, auth:{mode,domain,clientId,redirectUri}, sheets})
//   (deploy.sh generates that JSON from the stack outputs). Without --config a local-dev config.js is written.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const args = Object.fromEntries(process.argv.slice(2).reduce((a, x, i, all) => (x.startsWith('--') ? [...a, [x.slice(2), all[i + 1]]] : a), []));
const IN = args.in || path.join(here, '..', 'artifact', 'index.html');
const OUT = args.out || path.join(here, '..', 'standalone');

export function toStandalone(html, ids = {}) {
  const STORE = /(<script id="store" type="application\/json">)[\s\S]*?(<\/script>)/;
  if (!STORE.test(html)) throw new Error('no <script id="store"> found');
  let out = html.replace(STORE, (_, a, b) => a + '{}' + b);
  // main app script: the first plain <script> after the store
  const i = out.indexOf('</script>', out.search(STORE)) + '</script>'.length;
  const j = out.indexOf('<script>', i);
  if (j < 0) throw new Error('app <script> not found');
  out = out.slice(0, j) + '<script type="text/x-elite-app" id="elite-app">' + out.slice(j + '<script>'.length);
  const head = out.indexOf('<head>');
  if (head < 0) throw new Error('<head> not found');
  const inject = '<head><script src="config.js"></script><script src="platform.js"></script>';
  out = out.slice(0, head) + inject + out.slice(head + '<head>'.length);
  const MAP = { YOUR_BACKUP_FOLDER_ID: ids.BACKUP_FOLDER_ID, YOUR_INVOICE_SHEET_ID: ids.INVOICE_SHEET_ID, YOUR_RETIRED_MASTER_SHEET_ID: ids.MASTER_SHEET_ID };
  for (const [ph, v] of Object.entries(MAP)) if (v) out = out.split(ph).join(v);
  if (ids.NAME_HINT) out = out.replace('placeholder="e.g. Alex"', `placeholder="e.g. ${ids.NAME_HINT}"`);
  if (ids.NOTE_HINT) out = out.replace('e.g. Checked with Jordan,', `e.g. Checked with ${ids.NOTE_HINT},`);
  return out;
}

if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  const ids = args.ids && fs.existsSync(args.ids) ? JSON.parse(fs.readFileSync(args.ids, 'utf8')) : {};
  const html = toStandalone(fs.readFileSync(IN, 'utf8'), ids);
  fs.mkdirSync(OUT, { recursive: true });
  fs.writeFileSync(path.join(OUT, 'index.html'), html);
  fs.copyFileSync(path.join(here, '..', 'platform', 'platform.js'), path.join(OUT, 'platform.js'));
  const cfg = args.config ? JSON.parse(fs.readFileSync(args.config, 'utf8')) : { apiBase: '/api', auth: { mode: 'none' }, sheets: true };
  fs.writeFileSync(path.join(OUT, 'config.js'), 'window.ELITE_CONFIG=' + JSON.stringify(cfg, null, 1) + ';\n');
  console.log('standalone build written to', OUT, `(${html.length} bytes)`);
}

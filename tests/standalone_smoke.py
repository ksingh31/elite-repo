# Smoke test of the standalone (AWS) build against the local API server (api/local-server.mjs, fake Google):
# load -> edit -> Save for team -> reload -> the edit persisted; a stale second tab gets a conflict; Back up now writes the sheet.
import json, os, subprocess, sys, time, urllib.request, shutil, tempfile
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = int(os.environ.get('SMOKE_PORT', '8799'))
tmp = tempfile.mkdtemp()
store = os.path.join(tmp, 'store.json')
shutil.copy(os.path.join(ROOT, 'samples', 'store.sample.json'), store)
srv = subprocess.Popen(['node', os.path.join(ROOT, 'api', 'local-server.mjs'), '--port', str(PORT), '--store', store], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
res = []
def ok(n, c, d=''):
    res.append(bool(c)); print(('PASS ' if c else 'FAIL ') + n, '' if c else d)
try:
    for _ in range(50):
        try: urllib.request.urlopen(f'http://localhost:{PORT}/api/health'); break
        except Exception: time.sleep(0.1)
    URL = f'http://localhost:{PORT}/'
    with sync_playwright() as p:
        b = p.chromium.launch(); ctx = b.new_context(viewport={'width': 1300, 'height': 900})
        pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(URL); pg.wait_for_selector('input[data-p="sell"]'); pg.wait_for_timeout(500)
        ok('loads the store from the API (project list filled)', pg.locator('#proj option').count() == len(json.load(open(store))['projects']))
        ok('starts clean', pg.inner_text('#savestate') == 'All changes saved', pg.inner_text('#savestate'))
        # a second tab opened now will be stale after the first saves
        pg2 = ctx.new_page(); pg2.goto(URL); pg2.wait_for_selector('input[data-p="sell"]'); pg2.wait_for_timeout(400)
        i = pg.locator('input[data-p="sell"]'); i.fill('2,777,000'); i.press('Tab'); pg.wait_for_timeout(200)
        ok('edit marks unsaved', pg.inner_text('#savestate') == 'Unsaved changes')
        pg.click('header [data-act="save"]'); pg.wait_for_function("document.getElementById('savestate').textContent==='All changes saved'", timeout=15000)
        saved = json.load(open(store))
        ok('saved to the API store file', any(x['sell'] == 2777000 for x in saved['projects']), [x['sell'] for x in saved['projects']])
        pg.reload(); pg.wait_for_selector('input[data-p="sell"]'); pg.wait_for_timeout(400)
        ok('reload shows the saved value', pg.locator('input[data-p="sell"]').input_value().replace(',', '') == '2777000', pg.locator('input[data-p="sell"]').input_value())
        ok('reload is clean', pg.inner_text('#savestate') == 'All changes saved')
        # stale tab: edit + save -> conflict message, nothing overwritten
        j = pg2.locator('input[data-p="lot"]'); j.fill('123,456'); j.press('Tab'); pg2.wait_for_timeout(200)
        pg2.click('header [data-act="save"]'); pg2.wait_for_timeout(1500)
        ok('stale tab gets the conflict message', 'Someone saved at the same time' in pg2.inner_text('#toasts'), pg2.inner_text('#toasts'))
        after = json.load(open(store))
        ok('conflict did not overwrite the newer save', any(x['sell'] == 2777000 for x in after['projects']) and not any(x['lot'] == 123456 for x in after['projects']))
        # backups window works through the API proxy
        pg.click('[data-act="bk-open"]'); pg.wait_for_timeout(300); pg.click('[data-act="bk-now"]')
        pg.wait_for_function("/Done\\.|failed|Backup/.test(document.getElementById('bkmsg').textContent)", timeout=20000)
        ok('Back up now succeeds via /api/mcp', pg.inner_text('#bkmsg').startswith('Done'), pg.inner_text('#bkmsg'))
        pg.wait_for_timeout(500)
        ok('restore points listed', pg.locator('#bklist li').count() >= 1, pg.inner_text('#bklist'))
        ok('no page errors', not errs, errs)
        b.close()
finally:
    srv.terminate(); shutil.rmtree(tmp, ignore_errors=True)
print(sum(res), '/', len(res))
sys.exit(0 if all(res) else 1)

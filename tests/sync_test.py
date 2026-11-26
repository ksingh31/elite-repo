import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *
import json
from playwright.sync_api import sync_playwright
tabs=json.load(open(os.path.join(HERE,'fixtures','sync_tabs.json')))

INIT=INIT.replace("  if(t==='get_values'){","  if(t==='get_values'&&i.spreadsheetId==='SAMPLE-BACKUP-SHEET-ID'&&!/Backup data/.test(i.range)){const nm=i.range.split('!')[0].replace(/'/g,'');return {payload:{values:(window.__T[nm]||[])}};}\n  if(t==='get_values'){",1)
INIT="window.__T="+json.dumps(tabs)+";"+INIT
res=[]
def ok(n,c,d=''):res.append(c);print(('PASS ' if c else 'FAIL ')+n,'' if c else d)
with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':1300,'height':900});errs=[]
  pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script(INIT)
  pg.goto(APP_URL);pg.wait_for_timeout(700)
  pg.click('[data-act="bk-open"]');pg.wait_for_timeout(400)
  ok('budget preselected and check enabled',pg.eval_on_selector('#bkbud','e=>e.selectedOptions[0].textContent')=='Maple Grove - North budget' and not pg.eval_on_selector('#syncgo','e=>e.disabled'))
  pg.click('#syncgo');pg.wait_for_timeout(600)
  txt=pg.inner_text('#syncres');print(txt)
  ok('budget amount change found','New home warranty: budget $100.00 → $150.00' in txt)
  ok('invoice amount change found','Juniper Concrete' in txt and '$32,681.38' in txt)
  ok('paid change found','Quarry Doors' in txt and 'paid $9,995.70 → $10,995.70' in txt)
  ok('new row found','New trade invoice: New Fence Guy $1,000.00 in Landscaping' in txt)
  ok('unknown line flagged','no budget line called "Nonexistent line"' in txt)
  n=txt.count('\n')
  ok('few false differences',len(pg.locator('[data-sync]').all())<=6,len(pg.locator('[data-sync]').all()))
  pg.click('[data-act="sync-apply"]');pg.wait_for_timeout(300)
  ok('applied message','Applied' in pg.inner_text('#syncres'))
  pg.click('[data-act="bk-close"]');pg.click('.tabs a[href="#budget"]');pg.wait_for_timeout(300)
  land=pg.locator('button.actbtn[aria-label="Invoices for Landscaping"]').inner_text()
  ok('new invoice added','$33,857.03' in land and '42 invoices' in land,land)
  print('vis',pg.locator('button.actbtn[aria-label="Invoices for Drywall/ mudtape"]').is_visible(), pg.evaluate("[...document.querySelectorAll('.modal')].filter(m=>!m.hidden).map(m=>m.id)"), pg.evaluate('document.querySelector(\'button.actbtn[aria-label="Invoices for Drywall/ mudtape"]\').getBoundingClientRect().height'))
  ok('budget amount applied','150' in pg.locator('#v-budget').inner_html())
  pg.locator('button.actbtn[aria-label="Invoices for Drywall/ mudtape"]').dispatch_event('click');pg.wait_for_timeout(200)
  ok('payment added','$27,479.04' in pg.inner_text('#pbody'),pg.inner_text('#pbody')[:200])
  ok('unsaved state',pg.inner_text('#savestate')=='Unsaved changes')
  # guard: sheet older than the calculator -> warn, nothing ticked, source sheet shown
  pg.evaluate("()=>{document.querySelectorAll('#toasts .toast').forEach(t=>t.remove());['pmodal','modal','dmodal'].forEach(id=>{const m=document.getElementById(id);if(m)m.hidden=true;});}");pg.wait_for_timeout(200)
  if pg.locator('#d-discard').is_visible(): pg.click('#d-discard')
  pg.evaluate("()=>{window.__T['Backup log']=[['When','What','P','B','Pay','Size','Saved'],['2026-11-20 10:00','Back up now','5','1','1','1','2000-01-01T00:00:00.000Z']];}")
  pg.click('[data-act="bk-open"]');pg.wait_for_timeout(400);pg.click('#syncgo');pg.wait_for_timeout(800)
  t2=pg.inner_text('#syncres')
  ok('shows which sheet it compared with','Compared with' in t2 and 'last backup 2026-11-20 10:00' in t2,t2[:200])
  ok('stale sheet warning shown','older than the calculator' in t2)
  ok('stale: nothing pre-ticked',pg.locator('[data-sync]:checked').count()==0)
  pg.click('[data-act="sync-all"]');ok('tick all works',pg.locator('[data-sync]:checked').count()==pg.locator('[data-sync]:not([disabled])').count()>0,(pg.locator('[data-sync]:checked').count(),pg.locator('[data-sync]').count()))
  ok('no errors',not errs,errs)
  b.close()
print(sum(res),'/',len(res))

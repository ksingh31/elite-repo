import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *
from playwright.sync_api import sync_playwright

res=[]
def ok(n,c,d=''):res.append(c);print(('PASS ' if c else 'FAIL ')+n,'' if c else d)
G="(()=>{const p=__dbg.P();return __dbg.effP(p).build})()"
with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':1300,'height':1300});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script(INIT);pg.goto(APP_URL);pg.wait_for_timeout(700)
  t0=pg.evaluate("__dbg.calc(__dbg.effP(__dbg.P()),__dbg.P().co).sel.profit")
  pg.locator('input[data-bl="use"]').first.check();pg.wait_for_timeout(400)
  ok('new link defaults to Projected',pg.is_checked('input[data-radio="budget.src"][value="proj"]'))
  ok('projected build = 1,156,583.00',abs(pg.evaluate(G)-1156583.00)<0.01,pg.evaluate(G))
  pg.click('input[data-radio="budget.src"][value="budget"]');pg.wait_for_timeout(300)
  ok('budget estimate = 1,085,600.00',abs(pg.evaluate(G)-1085600.00)<0.01)
  ok('warning suggests Projected','Consider Projected' in pg.inner_text('.bcpanel'))
  pg.click('input[data-radio="budget.src"][value="inv"]');pg.wait_for_timeout(300)
  ok('invoiced = 1,138,085.94',abs(pg.evaluate(G)-1138085.94)<0.01)
  pg.click('input[data-radio="budget.src"][value="manual"]');pg.wait_for_timeout(300)
  i=pg.locator('input[data-p="budget.manual"]');i.fill('1200000');i.press('Tab');pg.wait_for_timeout(300)
  ok('manual = 1,200,000 and shown in build cost',abs(pg.evaluate(G)-1200000)<0.01 and '1,200,000' in pg.inner_text('#c-bud'))
  ok('profit uses the build cost',abs(pg.evaluate("__dbg.calc(__dbg.effP(__dbg.P()),__dbg.P().co).profit0")-pg.evaluate("__dbg.calc({...__dbg.P(),build:1200000},__dbg.P().co).profit0"))<0.01)
  pg.click('input[data-radio="budget.src"][value="proj"]');pg.wait_for_timeout(300)
  c=pg.locator('input[data-p="budget.cont"]');c.fill('10');c.press('Tab');pg.wait_for_timeout(300)
  ok('contingency adds 10% of budget not yet invoiced',abs(pg.evaluate(G)-(1156583.00+0.1*18497.06))<2,pg.evaluate(G))
  c=pg.locator('input[data-p="budget.cont"]');c.fill('0');c.press('Tab');pg.wait_for_timeout(300)
  # finished line on budget page lowers projected (Staging budget 8,700 vs invoiced 4,292.66)
  pg.click('[data-act="save"]');pg.wait_for_timeout(1500)
  pg.click('.tabs a[href="#budget"]');pg.wait_for_timeout(600)
  ok('projected tile on budget page','Projected final cost' in pg.inner_text('#v-budget'))
  row=pg.locator('#v-budget tr',has_text='Staging').first
  row.locator('input[data-done]').check();pg.wait_for_timeout(400)
  ok('finished Staging: projected drops by 4,407.34',abs(pg.evaluate(G)-(1156583.00-4407.34))<0.01,pg.evaluate(G))
  ok('used-by shows source','Projected' in pg.inner_text('#v-budget'))
  ok('no errors',not errs,errs)
  b.close()
print(sum(res),'/',len(res))

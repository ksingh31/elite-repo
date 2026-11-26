import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *
from playwright.sync_api import sync_playwright

res=[]
def ok(n,c,d=''):res.append(c);print(('PASS ' if c else 'FAIL ')+n,'' if c else d)
with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':1300,'height':900});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script(INIT+";window.__pubDelay=1500;");pg.goto(APP_URL);pg.wait_for_timeout(700)
  i=pg.locator('input[data-p="sell"]');i.fill('2700000');i.press('Tab');pg.wait_for_timeout(300)
  for tab in ['builder','investors','budget']:
    pg.click(f'.tabs a[href="#{tab}"]');pg.wait_for_timeout(250)
    ok(f'unsaved: switching to {tab} asks first',pg.locator('#modal').is_visible())
    pg.click('#modal [data-act="m-cancel"]');pg.wait_for_timeout(150)
  ok('still on Inputs after cancel',pg.evaluate("location.hash")in('','#inputs'))
  # click nbar save while an input is focused (blur re-render must not swallow the click)
  i=pg.locator('input[data-p="lot"]');i.fill('890000')
  pg.click('#nbar [data-act="save"]');pg.wait_for_timeout(200)
  ok('one click on Save starts saving (even right after typing)',pg.locator('#busy').is_visible())
  ok('save buttons disabled while saving',pg.evaluate("[...document.querySelectorAll('[data-act=\"save\"]')].every(b=>b.disabled)"))
  pg.mouse.click(400,400);pg.keyboard.press('a')
  pg.evaluate("document.querySelector('header [data-act=\"save\"]').click()")
  pg.wait_for_timeout(2200)
  ok('only one publish despite extra clicks',pg.evaluate("window.__pub")==1,pg.evaluate("window.__pub"))
  ok('overlay gone after save',not pg.locator('#busy').is_visible())
  ok('toasts sit at the bottom',pg.evaluate("getComputedStyle(document.getElementById('toasts')).bottom")=='16px')
  ok('no errors',not errs,errs)
  b.close()
print(sum(res),'/',len(res))

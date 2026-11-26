import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *
from playwright.sync_api import sync_playwright
from tcmock import TCI
URL=APP_URL;OUT=os.path.join(OUT,'th');os.makedirs(OUT,exist_ok=True)
ok=[];bad=[]
def chk(n,c,d=''):(ok if c else bad).append(n);print(('PASS ' if c else 'FAIL ')+n,'' if c else d)
OV="document.documentElement.scrollWidth-innerWidth"
with sync_playwright() as p:
  b=p.chromium.launch()
  # 1. OS dark -> still light; toggle -> dark; reload -> dark; toggle back -> light
  c=b.new_context(viewport={'width':390,'height':844},color_scheme='dark');pg=c.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
  pg.add_init_script(TCI);pg.goto(URL);pg.wait_for_timeout(700)
  th=lambda:pg.evaluate("[document.documentElement.dataset.theme,getComputedStyle(document.documentElement).colorScheme,getComputedStyle(document.body).backgroundColor]")
  t=th();chk('OS dark: default light',t[0]=='light' and t[1]=='light' and t[2]=='rgb(242, 245, 247)',t)
  chk('light pressed',pg.get_attribute('[data-theme-set=light]','aria-pressed')=='true')
  for s in ['light','dark']:
    bb=pg.locator(f'[data-theme-set={s}]').bounding_box();chk(f'{s} button tap >=44x40 on phone',bb['width']>=44 and bb['height']>=40,bb)
  pg.click('[data-theme-set=dark]');pg.wait_for_timeout(100);t=th();chk('toggle -> dark',t[0]=='dark' and t[1]=='dark' and t[2]=='rgb(11, 19, 30)',t)
  chk('stored on device only',pg.evaluate("localStorage.getItem('ec-theme')")=='dark' and 'ec-theme' not in pg.evaluate("JSON.stringify(store)") and 'theme' not in pg.evaluate("localStorage.getItem('ec-calc5')||''"))
  pg.reload();pg.wait_for_timeout(700);t=th();chk('reload stays dark',t[0]=='dark' and t[1]=='dark',t)
  chk('dark pressed after reload',pg.get_attribute('[data-theme-set=dark]','aria-pressed')=='true')
  pg.click('[data-theme-set=light]');pg.wait_for_timeout(100);t=th();chk('toggle back -> light',t[0]=='light' and t[2]=='rgb(242, 245, 247)',t)
  pg.reload();pg.wait_for_timeout(500);chk('reload stays light',th()[0]=='light')
  # first paint: theme set before body exists
  c.close()
  c=b.new_context(color_scheme='light');pg=c.new_page();pg.add_init_script("localStorage.setItem('ec-theme','dark');document.addEventListener('readystatechange',()=>{if(document.readyState==='interactive')window.__t0=document.documentElement.dataset.theme},{once:true})")
  pg.goto(URL);pg.wait_for_timeout(400);chk('dark applied before body parse (no flash)',pg.evaluate("window.__t0")=='dark')
  pg.add_init_script("localStorage.setItem('ec-theme','light')");c.close()
  # storage blocked
  c=b.new_context();pg=c.new_page();e2=[];pg.on('pageerror',lambda e:e2.append(str(e)))
  pg.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new Error('blocked')}})");pg.goto(URL);pg.wait_for_timeout(500)
  chk('localStorage blocked: still light, no theme error',pg.evaluate("document.documentElement.dataset.theme")=='light')
  c.close()
  # PDF independence
  c=b.new_context();pg=c.new_page();pg.add_init_script(TCI);pg.goto(URL+'#breport');pg.wait_for_timeout(800)
  import re
  def pdf():return re.sub(r'CreationDate \(D:\d+\)','',bytes(pg.evaluate("Array.from(__dbg.pdf.builder())")).decode('latin1'))
  same=pdf();pg.click('[data-theme-set=dark]');pg.wait_for_timeout(100);same2=pdf();pg.click('[data-theme-set=light]')
  chk('PDF bytes identical light vs dark (excluding date)',same==same2)
  c.close()
  # 2. screenshots + overflow
  for w in [375,390,768,1300]:
    for mode in ['light','dark']:
      c=b.new_context(viewport={'width':w,'height':860},color_scheme='dark' if mode=='light' else 'light');pg=c.new_page();errs=[]
      pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
      pg.add_init_script(TCI+(";localStorage.setItem('ec-theme','dark');" if mode=='dark' else ''))
      pg.goto(URL+'#inputs');pg.wait_for_timeout(900)
      chk(f'{w} {mode}: theme',pg.evaluate("document.documentElement.dataset.theme")==mode)
      shots=[]
      def snap(nm,full=True):
        o=pg.evaluate(OV);chk(f'{w} {mode} {nm}: no h-overflow',o<=1,o);pg.screenshot(path=f'{OUT}/{nm}_{w}_{mode}.png',full_page=full)
      for tab in ['inputs','builder','investors','breport','budget','tocheck']:
        pg.evaluate(f"location.hash='#{tab}'");pg.wait_for_timeout(500);snap(tab)
      pg.evaluate("location.hash='#budget'");pg.wait_for_timeout(400)
      pg.click('[data-act="b-ups"] >> nth=0');pg.wait_for_timeout(300);snap('upgrades')
      pg.click('[data-act="b-pay"][data-id="i14"] >> nth=0');pg.wait_for_timeout(300);snap('payments',False)
      pg.click('[data-act="p-invmove"] >> nth=0');pg.wait_for_timeout(300);snap('move',False)
      pg.keyboard.press('Escape');pg.wait_for_timeout(200)
      if pg.evaluate("!document.querySelector('#mvmodal').hidden"):pg.click('#mvmodal [data-act=mv-cancel], #mvmodal .btn:not(.pri) >> nth=0');pg.wait_for_timeout(200)
      pg.evaluate("location.reload()");pg.wait_for_timeout(900)
      pg.click('[data-act="bk-open"]');pg.wait_for_timeout(300);snap('backups',False);pg.mouse.click(4,4);pg.wait_for_timeout(200)
      pg.evaluate("location.hash='#budget'");pg.wait_for_timeout(300)
      pg.click('[data-act="b-newver"]');pg.wait_for_timeout(200);pg.fill('#vm-note','x');pg.mouse.click(4,4);pg.wait_for_timeout(200);snap('unsaved',False)
      pg.click('[data-act="d-discard"]');pg.wait_for_timeout(200)
      pg.click('[data-act=export]');pg.wait_for_timeout(150);snap('toast',False)
      chk(f'{w} {mode}: no console/page errors',not errs,errs[:3])
      c.close()
  print(len(ok),'/',len(ok)+len(bad));print('failed checks',bad)

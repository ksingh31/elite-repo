import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *

from tcmock import TCI
from playwright.sync_api import sync_playwright
bad=[]
with sync_playwright() as p:
  b=p.chromium.launch()
  for w in [375,390,768,1300]:
    for th in ['light','dark']:
      pg=b.new_page(viewport={'width':w,'height':860},color_scheme=th);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
      pg.add_init_script(TCI);pg.goto(APP_URL+'#tocheck');pg.wait_for_timeout(1300)
      # stage one + select two for bulk bar + open resolved
      pg.click('#tc-r5 [data-act=tc-do][data-k=keepboth]');pg.wait_for_timeout(100)
      pg.click('#tc-r8 '+('.cbw .cb' if w<=640 else '.ck .cb'));pg.click('#tc-r9 '+('.cbw .cb' if w<=640 else '.ck .cb'));pg.wait_for_timeout(200)
      ov=pg.evaluate("document.scrollingElement.scrollWidth-innerWidth")
      small=pg.evaluate("""[...document.querySelectorAll('#v-tocheck button,#v-tocheck a,#v-tocheck input,#tcpbar button,#tcbulk button,#v-tocheck summary')].filter(e=>e.offsetParent&&!e.closest('.hist ol')).map(e=>{const r=e.getBoundingClientRect();const cb=e.classList.contains('cb');return [e.textContent.trim().slice(0,25)||e.id||e.className,cb?44:r.height,r.width]}).filter(x=>x[1]<43.5)""") if w<=640 else []
      trunc=pg.evaluate("[...document.querySelectorAll('#v-tocheck .mn,#v-tocheck .amt span,#v-tocheck .sumgrid .v')].filter(e=>e.offsetParent&&e.scrollWidth>e.clientWidth+1).map(e=>e.textContent)")
      print(w,th,'overflow',ov,'small',small[:6],'trunc',trunc[:4],errs)
      if ov>0 or small or trunc or errs:bad.append((w,th))
      pg.screenshot(path=f'{OUT}/L_{w}_{th}.png',full_page=False)
      pg.evaluate("document.querySelector('#tc-r9').scrollIntoView()");pg.screenshot(path=f'{OUT}/L2_{w}_{th}.png')
      pg.click('#tc-r7 [data-act=tc-do][data-k=split]');pg.wait_for_timeout(200);pg.screenshot(path=f'{OUT}/D_{w}_{th}.png');pg.click('[data-act=tc-dlgclose]')
      pg.click('.tabs a[href="#budget"]');pg.wait_for_timeout(200);pg.screenshot(path=f'{OUT}/V_{w}_{th}.png');pg.click('#tcleave [data-act=tc-lvdiscard]');pg.wait_for_timeout(400)
      ov2=pg.evaluate("document.scrollingElement.scrollWidth-innerWidth")
      pg.evaluate("document.querySelector('.tcchip')&&document.querySelector('.tcchip').scrollIntoView({block:'center'})");pg.screenshot(path=f'{OUT}/B_{w}_{th}.png')
      if ov2>0:bad.append((w,th,'budget overflow'))
      pg.close()
print('BAD',bad)

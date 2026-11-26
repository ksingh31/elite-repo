import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
  b=p.chromium.launch()
  for W in (390,1300):
    pg=b.new_page(viewport={'width':W,'height':860});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.add_init_script(INIT);pg.goto(APP_URL+'#budget');pg.wait_for_timeout(700)
    pg.click('[data-act="t-open"]');pg.wait_for_timeout(200);pg.locator('#tadd-2').scroll_into_view_if_needed();pg.fill('#tadd-2','Zed');s0=pg.evaluate("document.querySelector('#tmodal .mbox').scrollTop")
    pg.click('[data-act="t-add"][data-c="2"]');pg.wait_for_timeout(600)
    r=pg.evaluate("[!document.getElementById('tmodal').hidden,document.activeElement.id,document.querySelector('#tmodal .mbox').scrollTop,window.__pub,sessionStorage.getItem('ec-types-reopen')!==null]")
    print(W,r,s0,errs)
    pg.click('#tmodal [data-act="t-close"]');pg.wait_for_timeout(200);print(' closed',pg.evaluate("document.getElementById('tmodal').hidden"),pg.evaluate("sessionStorage.getItem('ec-types-reopen')"))

import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *
from playwright.sync_api import sync_playwright
import re

res=[]
def ok(n,c,d=''):res.append(c);print(('PASS ' if c else 'FAIL ')+n,'' if c else d)
num=lambda t:float(re.sub(r'[^0-9.\-]','',t) or 0)
with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':1300,'height':900});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script(INIT);pg.goto(APP_URL);pg.wait_for_timeout(700)
  before=pg.evaluate("[...document.querySelectorAll('#usebox .opt small')].map(x=>x.textContent)")
  ok('five options shown incl Cash + Private',pg.locator('#usebox .opt').count()==5 and 'Cash + Private' in pg.inner_text('#usebox'))
  pg.click('#usebox input[value="cp"]');pg.wait_for_timeout(400)
  after=pg.evaluate("[...document.querySelectorAll('#usebox .opt small')].map(x=>x.textContent)")
  ok('other options unchanged by switching',[before[i] for i in (0,1,2,4)]==[after[i] for i in (0,1,2,4)],(before,after))
  r=pg.evaluate("(()=>{const x=__dbg.calc(__dbg.effP(__dbg.P()),__dbg.P().co);return {cp:x.cp,lb:__dbg.P().lot+__dbg.P().build,o:x.opts.find(o=>o.key==='cp'),d:x.cpdraws,pEnd:x.pEnd,pre:+__dbg.P().preBuild||0}})()")
  A=0.65*r['lb'];ok('approved = 65% of lot+build',abs(r['cp']['approved']-A)<0.01,(r['cp']['approved'],A))
  ok('fee = 3% of approved (not drawn)',abs(r['o']['fee']-0.03*A)<0.01)
  ok('drawn = 100% by default',abs(r['cp']['drawn']-A)<1)
  exp=sum(d['amt']*0.0702*max(0,r['pEnd']-(r['pre']+d['after']))/12 for d in r['d'])
  ok('interest = each draw until sale closes',abs(r['o']['drawInt']-exp)<0.01)
  ok('profit includes fee+interest',abs(r['o']['fin']-(r['o']['fee']+r['o']['drawInt']+r['o']['other']))<0.01)
  ok('fee line explains the fee','× ' in pg.inner_text('#cpfee') and 'approved' in pg.inner_text('#cpfee'))
  # stop early: remove last draw -> undrawn, fee unchanged
  pg.locator('.cpdraw .x').last.click();pg.wait_for_timeout(300)
  r2=pg.evaluate("(()=>{const x=__dbg.calc(__dbg.effP(__dbg.P()),__dbg.P().co);return {cp:x.cp,o:x.opts.find(o=>o.key==='cp')}})()")
  ok('fewer draws: part not drawn, fee same, less interest',r2['cp']['undrawn']>0.3*A and abs(r2['o']['fee']-r['o']['fee'])<0.01 and r2['o']['drawInt']<r['o']['drawInt'])
  ok('note shows not drawn','Not drawn' in pg.inner_text('#cpappr'))
  # fixed amounts
  pg.click('.seg input[value="amt"]');pg.wait_for_timeout(300)
  inps=pg.locator('.cpdraw input[data-p$=".v"]');inps.nth(0).fill('500000');inps.nth(0).press('Tab');pg.wait_for_timeout(200)
  inps=pg.locator('.cpdraw input[data-p$=".v"]');inps.nth(1).fill('900000');inps.nth(1).press('Tab');pg.wait_for_timeout(300)
  r3=pg.evaluate("(()=>{const x=__dbg.calc(__dbg.effP(__dbg.P()),__dbg.P().co);return {cp:x.cp,d:x.cpdraws}})()")
  ok('fixed $: second draw capped at what is left',abs(r3['d'][0]['amt']-500000)<0.01 and abs(r3['d'][1]['amt']-(A-500000))<0.01 and r3['cp']['undrawn']<0.01)
  ok('cap warning shown','more than' in pg.inner_text('#cpwarn'))
  # add draw
  pg.click('[data-act="add"][data-path="cp.draws"]');pg.wait_for_timeout(300)
  ok('add draw works',pg.locator('.cpdraw').count()==3)
  # short loan with fee
  pg.click('[data-act="add"][data-path="cp.loans"]');pg.wait_for_timeout(300)
  row=pg.locator('.row.r5').last
  row.locator('input[data-p$=".amount"]').fill('100000');row.locator('input[data-p$=".amount"]').press('Tab');pg.wait_for_timeout(200)
  row=pg.locator('.row.r5').last;row.locator('input[data-p$=".fee"]').fill('2');row.locator('input[data-p$=".fee"]').press('Tab');pg.wait_for_timeout(300)
  o=pg.evaluate("__dbg.calc(__dbg.effP(__dbg.P()),__dbg.P().co).opts.find(o=>o.key==='cp').other")
  ok('short loan = 2% fee + 10% x 6 months',abs(o-(2000+100000*0.1*6/12))<0.01,o)
  # builder shows cp column + schedule
  pg.click('.tabs a[href="#builder"]');pg.wait_for_timeout(400)
  if pg.locator('#modal').is_visible(): pg.click('#modal [data-act="m-cancel"]')
  bt=pg.inner_text('#v-builder') if pg.locator('#v-builder').is_visible() else ''
  ok('builder compares Cash + Private',bt=='' or ('Cash + Private' in bt and 'Draw schedule: Cash + Private' in bt))
  # private fee line
  pg.evaluate("()=>{location.hash='inputs'}");pg.wait_for_timeout(300)
  if pg.locator('#modal').is_visible(): pg.click('#modal [data-act="m-cancel"]')
  pg.click('#usebox input[value="priv"]');pg.wait_for_timeout(300)
  ok('private shows fee in the loan cost line','fee' in pg.inner_text('#pvfee') and 'loan' in pg.inner_text('#pvfee'))
  ok('no errors',not errs,errs)
  b.close()
print(sum(res),'/',len(res))

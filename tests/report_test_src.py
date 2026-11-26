import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *
import re,os,subprocess,base64,json
from playwright.sync_api import sync_playwright

INIT=INIT.replace("n==='downloads'?{save:async()=>{}}","n==='downloads'?{save:async o=>{window.__saved=window.__saved||[];const d=o.data instanceof Uint8Array?o.data:new Uint8Array(o.data);window.__saved.push({filename:o.filename,b64:btoa(Array.from(d,c=>String.fromCharCode(c)).join(''))});if(window.__decline)throw {code:'declined'};}}")
URL=APP_URL

ok=[];bad=[]
def chk(n,c,extra=''):
  (ok if c else bad).append(n);print(('PASS ' if c else 'FAIL ')+n+(' '+str(extra) if (extra and not c) else ''))

import math
def m0(v):
  s='$'+format(math.floor(abs(v)+0.5),',');return ('-' if v<0 else '')+s
def pcf(v): return '%.2f%%'%(v*100)

def validate_pdf(b,name):
  chk(name+': starts with %PDF-1.',b[:7]==b'%PDF-1.')
  sx=b.rfind(b'startxref');off=int(b[sx+9:].split()[0])
  chk(name+': startxref points at xref',b[off:off+4]==b'xref')
  lines=b[off:].split(b'\n');n=int(lines[1].split()[1]);good=True
  for i in range(1,n):
    o=int(lines[2+i][:10])
    if not b[o:].startswith(('%d 0 obj'%i).encode()):good=False
  chk(name+': every xref offset correct',good)
  chk(name+': entries are 20 bytes',all(len(lines[2+i])+1==20 for i in range(n)))
  chk(name+': trailer present',b'trailer' in b and b'/Root 1 0 R' in b and b.rstrip().endswith(b'%%EOF'))
  pc=int(re.search(rb'/Count (\d+)',b).group(1));chk(name+': page count > 0',pc>0)
  # stream lengths
  okl=True
  for mm in re.finditer(rb'<< /Length (\d+) >>\nstream\n',b):
    L=int(mm.group(1));e=mm.end()
    if b[e+L:e+L+10]!=b'\nendstream':okl=False
  chk(name+': stream lengths correct',okl)
  chk(name+': no unmapped characters (no "?" placeholders)',b'?' not in b)
  if 'cp' in name or 'investor' in name: chk(name+': range en dash kept as WinAnsi 0x96',b' \x96 ' in b)
  return pc

with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':1300,'height':900});errs=[]
  pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script(INIT);pg.goto(URL);pg.wait_for_timeout(700)
  chk('Builder report tab in nav after Investor report',pg.evaluate("[...document.querySelectorAll('.tabs a')].map(a=>a.getAttribute('href')).join(',')")=='#inputs,#builder,#investors,#breport,#budget,#tocheck')
  for key,proj in [('ap','birch'),('priv','p1795641367331'),('cash','maple'),('lot','p1795639960151'),('cp','maple')]:
    pg.click('.tabs a[href="#inputs"]');pg.wait_for_timeout(150)
    pg.select_option('#proj',proj);pg.wait_for_timeout(250)
    if pg.evaluate("__dbg.P().use")!=key:
      pg.click(f'#usebox input[value="{key}"]');pg.wait_for_timeout(200)
      pg.click('.tabs a[href="#breport"]');pg.wait_for_timeout(250)
      chk(f'[{key}] unsaved financing change: guard asks first',not pg.evaluate("document.querySelector('#modal').hidden"))
      pg.click('[data-act="m-cancel"]');pg.wait_for_timeout(100)
      pg.evaluate("document.querySelector('#v-breport').classList.add('on');document.querySelector('#v-inputs').classList.remove('on')")  # view the (already rendered) report for checks
    else:
      pg.click('.tabs a[href="#breport"]');pg.wait_for_timeout(250)
    chk(f'[{key}] view shown',pg.evaluate("document.querySelector('#v-breport').classList.contains('on')"))
    C=pg.evaluate("(()=>{const c=__dbg.calc(__dbg.effP(__dbg.P()),__dbg.P().co);return {sel:c.sel,coNet:c.coNet,coCash:c.coCash,coRoi:c.coRoi,coAnn:c.coAnn,profit0:c.profit0,invEarn:c.invEarn,name:__dbg.P().name,D:c.D}})()")
    s=C['sel'];chk(f'[{key}] selected option is {key}',s['key']==key)
    tiles=pg.evaluate("[...document.querySelectorAll('#v-breport .tile')].map(t=>[t.querySelector('.lbl').textContent,t.querySelector('.v').textContent])")
    T=dict(tiles)
    chk(f'[{key}] 5 tiles',[t[0] for t in tiles]==['Builder earnings','Builder cash in','Return on builder cash','Annualized return','Profit after financing'],tiles)
    chk(f'[{key}] builder earnings tile',m0(C['coNet']) in T['Builder earnings'],(m0(C['coNet']),T['Builder earnings']))
    chk(f'[{key}] builder cash tile',m0(C['coCash']) in T['Builder cash in'],(C['coCash'],T['Builder cash in']))
    chk(f'[{key}] ROI tile',(pcf(C['coRoi']) if C['coRoi'] is not None else 'n/a') in T['Return on builder cash'],T['Return on builder cash'])
    chk(f'[{key}] annualized tile',(pcf(C['coAnn']) if C['coAnn'] is not None else 'n/a') in T['Annualized return'],T['Annualized return'])
    chk(f'[{key}] profit after financing tile',m0(s['profit']) in T['Profit after financing'],(s['profit'],T['Profit after financing']))
    head=pg.inner_text('#v-breport .rephead')
    chk(f'[{key}] header has project, option, length',C['name'] in head and s['name'] in head and 'Builder report' in head and 'mo' in head,head)
    h2=pg.evaluate("[...document.querySelectorAll('#v-breport .rep h2')].map(x=>x.textContent)")
    chk(f'[{key}] sections',h2==['Project profit before financing','Financing: '+s['name'],'Builder breakdown'],h2)
    h3=pg.evaluate("[...document.querySelectorAll('#v-breport .rep h3')].map(x=>x.textContent)")
    want={'ap':'Draw schedule: A Lender + Private','priv':'Draw schedule: Private','cp':'Draw schedule: Cash + Private'}
    others=[v for k2,v in want.items() if k2!=key]
    chk(f'[{key}] only its own draw schedule',(want.get(key) in h3 if key in want else not any(x.startswith('Draw schedule') for x in h3)) and not any(o in h3 for o in others),h3)
    txt=pg.inner_text('#v-breport .rep')
    fin=s['fin'];
    chk(f'[{key}] total financing cost shown',('Total financing cost' in txt) and (('$%s'%format(round(fin,2),',.2f')) in txt),fin)
    if key=='cash': chk('[cash] says no financing','no loans' in txt.lower())
    if key=='lot': chk('[lot] lot mortgage details','Lot mortgage' in txt and 'Term' in txt)
    chk(f'[{key}] investor payout row',('$%s'%format(round(C['invEarn'],2),',.2f')) in txt)
    md=pg.evaluate("__dbg.repModel(document.querySelector('#v-breport'))")
    chk(f'[{key}] model has tables',sum(1 for x in md['blocks'] if x['t']=='table')>=4)
    if key in ('ap','priv','cp'):
      pg.screenshot(path=f'{OUT}/breport_{key}_1300.png',full_page=True)
      bb=bytes(pg.evaluate("Array.from(__dbg.pdf.builder())"));open(f'{OUT}/builder_{key}.pdf','wb').write(bb);validate_pdf(bb,f'builder pdf {key}')
  pg.select_option('#proj','maple');pg.wait_for_timeout(250)
  if not pg.evaluate("document.querySelector('#modal').hidden"): pg.click('[data-act="m-discard"]');pg.wait_for_timeout(300)
  chk('discarded: back to maple cash',pg.evaluate("__dbg.P().id+__dbg.P().use")=='maplecash')
  # investor pdf
  bb=bytes(pg.evaluate("Array.from(__dbg.pdf.investor())"));open(f'{OUT}/investor.pdf','wb').write(bb);validate_pdf(bb,'investor pdf')
  # download via button
  pg.click('.tabs a[href="#breport"]');pg.wait_for_timeout(200)
  chk('pdf button enabled with downloads',pg.evaluate("!document.querySelector('#v-breport [data-act=pdf]').disabled"))
  pg.click('#v-breport [data-act="pdf"]');pg.wait_for_timeout(400)
  sv=pg.evaluate("window.__saved||[]")
  chk('download saved with filename',len(sv)==1 and sv[0]['filename'].endswith(' - Builder report.pdf'),[x['filename'] for x in sv])
  chk('saved bytes are a PDF',len(sv)==1 and base64.b64decode(sv[0]['b64'])[:5]==b'%PDF-')
  chk('success toast',('PDF saved' in pg.inner_text('#toasts')))
  pg.click('.tabs a[href="#investors"]');pg.wait_for_timeout(200)
  pg.evaluate("window.__decline=1");pg.click('#v-investors [data-act="pdf"]');pg.wait_for_timeout(400)
  sv=pg.evaluate("window.__saved");chk('investor download filename',sv[-1]['filename'].endswith(' - Investor report.pdf'))
  chk('declined: quiet message',('cancelled' in pg.inner_text('#toasts')))
  pg.screenshot(path=f'{OUT}/investor_1300.png',full_page=True)
  # guard
  pg.click('.tabs a[href="#inputs"]');pg.wait_for_timeout(200)
  f=pg.locator('input[data-p="sell"]').first;f.fill('2700000');f.dispatch_event('input');pg.wait_for_timeout(200)
  pg.click('.tabs a[href="#breport"]');pg.wait_for_timeout(250)
  chk('guard modal on Builder report tab when dirty',not pg.evaluate("document.querySelector('#modal').hidden") and 'Builder report' in pg.inner_text('#mtext'),pg.inner_text('#mtext'))
  chk('stays on inputs',pg.evaluate("document.querySelector('#v-inputs').classList.contains('on')"))
  pg.click('[data-act="m-cancel"]')
  pg.evaluate("location.hash='breport'");pg.wait_for_timeout(250)
  chk('guard on hash navigation too',not pg.evaluate("document.querySelector('#modal').hidden"))
  pg.click('[data-act="m-discard"]');pg.wait_for_timeout(300)
  chk('after discard goes to Builder report',pg.evaluate("document.querySelector('#v-breport').classList.contains('on')"))
  chk('no page errors',not errs,errs)
  # dark + mobile
  for nm,kw in [('dark_1300',dict(viewport={'width':1300,'height':900},color_scheme='dark')),('m390',dict(viewport={'width':390,'height':844},device_scale_factor=2)),('m390_dark',dict(viewport={'width':390,'height':844},color_scheme='dark'))]:
    c=b.new_context(**kw);q=c.new_page();q.add_init_script(INIT+(";localStorage.setItem('ec-theme','dark');" if kw.get('color_scheme')=='dark' else ''));q.goto(URL+'#breport');q.wait_for_timeout(700)
    q.screenshot(path=f'{OUT}/breport_{nm}.png',full_page=True)
    chk(nm+': no horizontal page overflow',q.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
    c.close()
  # no downloads capability
  c=b.new_context();q=c.new_page();q.add_init_script("window.claude={use:n=>Promise.reject(new Error('no'))};");q.goto(URL+'#breport');q.wait_for_timeout(500)
  chk('no downloads: button disabled with tooltip',q.evaluate("(()=>{const b=document.querySelector('#v-breport [data-act=pdf]');return b.disabled&&/not available/.test(b.title)})()"))
  c.close();b.close()
print(len(ok),'/',len(ok)+len(bad))

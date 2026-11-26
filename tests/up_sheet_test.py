import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *
# Upgrades in the backup sheet (sub-rows, Summary, sync, restore) + empty-panel bug. Mock Sheets only.
import json,re
from playwright.sync_api import sync_playwright
from common import INIT,SEED
INIT=INIT.replace("  if(t==='get_values'){","  if(t==='get_values'&&window.__T&&!/Backup/.test(i.range)){const nm=i.range.split('!')[0].replace(/'/g,'');return {payload:{values:(window.__T[nm]||[])}};}\n  if(t==='get_values'){",1)
src=open(APP).read();i=src.rindex('\n}\n</script>')
open(OUT+'/_h_ups.html','w').write(src[:i]+'\nwindow.__S=()=>store;window.__D=()=>dirty;\n'+src[i:])
URL='file://'+OUT+'/_h_ups.html'

ok=[];bad=[]
def chk(n,c,d=''):(ok if c else bad).append(n);print(('PASS ' if c else 'FAIL ')+n,'' if c else d)
def tab(pg,name):
  T=pg.evaluate(f"(()=>{{const o=[];Object.entries(window.__cells).forEach(([k,v])=>{{const m=k.match(/^{K}\\|'(.*)'\\|(\\d+)$/);if(m&&m[1]==={json.dumps(name)})o[+m[2]-1]=v;}});return o.map(r=>r||[]);}})()")
  return [[x[1:] if isinstance(x,str) and x[:1]=="'" else x for x in r] for r in T]
def f(x):
  try:return float(x)
  except:return 0.0
def backup(pg):
  pg.click('[data-act="bk-open"]');pg.wait_for_timeout(300);pg.select_option('#bkbud','b-demo');pg.click('[data-act="bk-now"]');pg.wait_for_timeout(2500)
  return pg.inner_text('#bkmsg')
def sync(pg):
  pg.evaluate(f"""(()=>{{const T={{}};Object.entries(window.__cells).forEach(([k,v])=>{{const m=k.match(/^{K}\\|'(.*)'\\|(\\d+)$/);if(!m)return;(T[m[1]]=T[m[1]]||[])[+m[2]-1]=v.map(x=>typeof x==='string'&&x[0]==="'"?x.slice(1):x);}});Object.values(T).forEach(a=>{{for(let i=0;i<a.length;i++)if(!a[i])a[i]=[];}});window.__T=T;}})()""")
  pg.click('#syncgo');pg.wait_for_timeout(900);st=pg.inner_text('#syncres');pg.evaluate("window.__T=null");return st
with sync_playwright() as p:
  b=p.chromium.launch();errs=[]
  # ---- 1. panel bug at 390 and 1300 ----
  for w in [390,1300]:
    pg=b.new_page(viewport={'width':w,'height':900});pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.add_init_script(INIT);pg.goto(URL+'#budget');pg.wait_for_timeout(700)
    r=pg.locator('#v-budget tr.bitem').first;iid=r.get_attribute('data-iid')
    r.locator('[data-act="b-ups"]').click();pg.wait_for_timeout(200)
    up=pg.locator('#v-budget tr.uprow')
    chk(f'{w}: empty panel shows message but no Base/Line total summary','No upgrades on this line yet' in up.inner_text() and up.locator('.upmath').count()==0)
    pg.click('#v-budget tr.uprow [data-act="b-upadd"]');pg.wait_for_timeout(200);pg.keyboard.type('Temp');pg.keyboard.press('Tab');pg.wait_for_timeout(200)
    pg.click('#v-budget tr.uprow [data-act="b-upyn"][data-v="1"]');pg.wait_for_timeout(200)
    chk(f'{w}: with an upgrade the summary shows',pg.locator('#v-budget tr.uprow .upmath').count()==1)
    pg.screenshot(path=f'{OUT}/upbug_{w}_with.png')
    pg.click('#v-budget tr.uprow [data-act="b-uprm"]');pg.wait_for_timeout(300)
    r=pg.locator(f'#v-budget tr.bitem[data-iid="{iid}"]')
    chk(f'{w}: removing the last upgrade collapses the panel',pg.locator('#v-budget tr.uprow').count()==0)
    chk(f'{w}: chip back to + Upgrade, collapsed and focused','+ Upgrade' in r.locator('.uchip').inner_text() and r.locator('.uchip').get_attribute('aria-expanded')=='false' and pg.evaluate("document.activeElement.dataset.act")=='b-ups')
    chk(f'{w}: line not marked Edited after add + delete','Edited' not in r.inner_text() and not r.evaluate("e=>e.classList.contains('chg')"))
    chk(f'{w}: no unsaved changes after add + delete',not pg.evaluate("__D()") and not pg.locator('#nbar').is_visible())
    pg.screenshot(path=f'{OUT}/upbug_{w}_after.png')
    pg.close()
  # ---- 2. sheet with several upgrades ----
  pg=b.new_page(viewport={'width':1300,'height':900});pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script(INIT);pg.goto(URL+'#budget');pg.wait_for_timeout(500);pg.evaluate(SEED);pg.reload();pg.wait_for_timeout(800)
  ups0=pg.evaluate("JSON.stringify(__S().budgets.find(b=>b.id==='b-demo').versions.at(-1).items.map(i=>i.ups||null))")
  base=pg.evaluate("__S().budgets.find(b=>b.id==='b-demo').versions.at(-1).items.reduce((t,i)=>t+(+i.amt||0),0)")
  chk('backup with upgrades done',backup(pg).startswith('Done'))
  B=tab(pg,'Budget');S=tab(pg,'Summary')
  print('    Budget rows around Windows and doors:');k=[j for j,r in enumerate(B) if str(r[0]).strip().startswith('Windows and doors')][0]
  for r in B[k:k+6]:print('     ',r)
  chk('header has 10 columns, no K-N',len(B[0])==10 and 'Item id' in B[0][9])
  W=B[k:k+5]
  chk('line row: name (base), base amount, invoices count, id',W[0][0].strip()=='Windows and doors (base)' and f(W[0][1])==64950 and W[0][2]=='' and re.match(r'^i',str(W[0][9])))
  chk('Yes upgrade sub-row: ↳ label, price in Budget',W[1][0].startswith('   ↳ Upgrade: Black exterior frames (Buyer · Approved · Yes)') and f(W[1][1])==1200 and W[1][8]=='Change order signed Apr 14' and str(W[1][9]).startswith('up:'))
  chk('No upgrade sub-row: 0 and "not added"',W[2][0].startswith('   ↳ Upgrade: Triple-pane glazing (Buyer · Declined · No)') and f(W[2][1])==0 and '6,500.00 not added' in W[2][0])
  chk('third upgrade row (No, Quoted)','Oversized patio slider' in W[3][0] and f(W[3][1])==0)
  chk('line total row: base + Yes upgrades with invoiced and variance',W[4][0].strip().startswith('Line total: Windows and doors') and f(W[4][1])==66150 and abs(f(W[4][3])-(f(W[4][2])-66150))<0.01 and W[4][9]=='sub:'+W[0][9])
  cat=[r for r in B if r and r[0]=='Structure and envelope'][0];cat2=[r for r in B if r and r[0]=='Interior finishes'][0];tot=[r for r in B if r and r[0]=='Total'][0]
  lines=lambda c0:[r for r in B[B.index(c0)+1:] ]
  def catsum(c0):
    o=0
    for r in B[B.index(c0)+1:]:
      if not r or not str(r[0]).startswith(' '):break
      if str(r[9]).startswith('up:') or str(r[9]).startswith('sub:'):continue
      sid='sub:'+str(r[9]);sub=[x for x in B if x and x[9]==sid]
      o+=f(sub[0][1]) if sub else f(r[1])
    return o
  sbase=pg.evaluate("__S().budgets.find(b=>b.id==='b-demo').versions.at(-1).items.filter(i=>i.cat==='Structure and envelope').reduce((t,i)=>t+(+i.amt||0),0)")
  chk('category subtotal includes Yes upgrades (Structure = base + 5,700, = sum of line totals)',abs(f(cat[1])-catsum(cat))<0.01 and abs(f(cat[1])-sbase-5700)<0.01,(cat[1],sbase))
  chk('Interior finishes subtotal includes +4,200 Yes only',abs(f(cat2[1])-catsum(cat2))<0.01)
  chk('grand total = base + 9,900 Yes upgrades',abs(f(tot[1])-(base+9900))<0.01,(tot[1],base))
  chk('upgrade rows styled (italic sub-part)',pg.evaluate("window.__calls.some(c=>c[1]==='update_spreadsheet'&&JSON.stringify(c[2]).includes('\"italic\":true'))"))
  flat=[str(x) for r in S for x in r]
  ti=[j for j,r in enumerate(S) if r and r[0]=='Budget base'][0]
  print('    Summary tiles:',S[ti],S[ti+1])
  chk('Summary: Budget base / Upgrades (Yes) / total / projected',S[ti][:4]==['Budget base','Upgrades (Yes)','Budget total (incl. upgrades)','Projected final cost (incl. upgrades)'] and abs(f(S[ti+1][0])-base)<0.01 and f(S[ti+1][1])==9900 and abs(f(S[ti+1][2])-base-9900)<0.01 and f(S[ti+1][3])>=f(S[ti+1][2]))
  proj=pg.evaluate("(()=>{const v=__S().budgets.find(b=>b.id==='b-demo').versions.at(-1);let p=0;v.items.forEach(i=>{const a=(+i.amt||0)+(i.ups||[]).reduce((t,u)=>t+(u.yes?+u.amt:0),0),x=+i.act||0;p+=i.done?x:Math.max(a,x);});return p})()")
  chk('Summary projected final cost matches the app formula (incl. upgrades)',abs(f(S[ti+1][3])-proj)<0.01)
  chk('Summary first tile row: Budget (with upgrades) = total','Budget (with upgrades)' in flat)
  ch=[j for j,r in enumerate(S) if r and r[:4]==['Category','Budget base','Upgrades (Yes)','Budget (with upgrades)']]
  chk('Summary by category has base / upgrades / with upgrades / projected',bool(ch) and S[ch[0]][-1]=='Projected final cost')
  if ch:
    st=[r for r in S[ch[0]:] if r and r[0]=='Structure and envelope'][0];tt=[r for r in S[ch[0]:] if r and r[0]=='Total'][0]
    chk('Summary category: Structure upgrades 5,700, total upgrades 9,900',f(st[2])==5700 and f(tt[2])==9900 and abs(f(tt[3])-base-9900)<0.01)
  uh=[j for j,r in enumerate(S) if r and r[:3]==['Category','Budget line','Upgrade']]
  chk('Summary Upgrades section lists all 6 upgrades',bool(uh) and len([r for r in S[uh[0]+1:uh[0]+7] if r and r[1]])==6)
  if uh:
    U=S[uh[0]+1:uh[0]+8];print('    Upgrades section:');[print('     ',r) for r in U]
    chk('Upgrades section: Yes counted, No 0; totals',U[0][5]=='Yes' and f(U[0][7])==1200 and U[1][5]=='No' and f(U[1][7])==0 and f(U[6][6])==23100 and f(U[6][7])==9900 and U[6][0]=='All upgrades (6)')
  st=sync(pg);print('    sync:',st[:140].replace('\n',' '))
  chk('sync after backup with upgrade sub-rows: No differences','No differences' in st)
  # edit the base amount in the sheet, and an upgrade row amount: only the base edit is reported
  pg.evaluate(f"""(()=>{{const pre='{K}|\\'Budget\\'|';const ks=Object.keys(window.__cells).filter(k=>k.startsWith(pre));ks.forEach(k=>{{const r=window.__cells[k];if(String(r[9]).startsWith('up:')||String(r[9]).startsWith('sub:'))r[1]=999999;}});}})()""")
  st=sync(pg);chk('sync ignores edits on upgrade / line total rows','No differences' in st,st[:200])
  # restore round trip
  pg.click('[data-act="bk-close"]');pg.wait_for_timeout(200)
  pg.click('#nbar [data-act="nb-discard"]');pg.wait_for_timeout(300)
  if pg.locator('#qmok').is_visible(): pg.click('#qmok');pg.wait_for_timeout(400)
  chk('discard removed upgrades',pg.evaluate("__S().budgets.every(b=>b.versions.every(v=>v.items.every(i=>!i.ups)))"))
  pg.click('[data-act="bk-open"]');pg.wait_for_timeout(300);pg.select_option('#bkbud','b-demo');pg.wait_for_timeout(600)
  pg.click('#bklist [data-act="bk-load"] >> nth=0');pg.wait_for_timeout(300);pg.click('#qmok');pg.wait_for_timeout(800)
  ups1=pg.evaluate("JSON.stringify(__S().budgets.find(b=>b.id==='b-demo').versions.at(-1).items.map(i=>i.ups||null))")
  chk('restore brings back every upgrade exactly',ups1==ups0)
  pg.close()
  # ---- 3. budget without upgrades ----
  pg=b.new_page(viewport={'width':1300,'height':900});pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script(INIT);pg.goto(URL+'#budget');pg.wait_for_timeout(700)
  chk('backup without upgrades done',backup(pg).startswith('Done'))
  B=tab(pg,'Budget');S=tab(pg,'Summary')
  chk('no upgrades: header A-J with plain "Budget", no sub/upgrade rows',B[0][1]=='Budget' and len(B[0])==10 and not any(str(r[9]).startswith(('up:','sub:')) for r in B if len(r)>9) and not any('(base)' in str(r[0]) for r in B))
  chk('no upgrades: Summary unchanged (no upgrade sections)',not any(r and r[0] in ('Budget base','Budget and upgrades') for r in S) and any(r and r[:2]==['Category','Budget'] for r in S))
  st=sync(pg);chk('no upgrades: sync No differences','No differences' in st)
  pg.close()
  chk('no page errors',not errs,errs)
  b.close()
print(len(ok),'/',len(ok)+len(bad))

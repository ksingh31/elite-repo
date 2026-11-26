import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *
# Upgrades story: functional tests (uses the mock INIT for Google Sheets).
import json,re
from playwright.sync_api import sync_playwright
from common import INIT
INIT=INIT.replace("  if(t==='get_values'){","  if(t==='get_values'&&window.__T&&!/Backup/.test(i.range)){const nm=i.range.split('!')[0].replace(/'/g,'');return {payload:{values:(window.__T[nm]||[])}};}\n  if(t==='get_values'){",1)
src=open(APP).read();i=src.rindex('\n}\n</script>')
open(OUT+'/_h_up.html','w').write(src[:i]+'\nwindow.__S=()=>store;window.__bud=()=>{const b=store.budgets.find(x=>x.id===\'b-demo\');return b;};\n'+src[i:])
URL='file://'+OUT+'/_h_up.html'
ok=[];bad=[]
def chk(n,c):(ok if c else bad).append(n);print(('PASS ' if c else 'FAIL ')+n)
money=lambda s:float(re.sub(r'[^0-9.\-]','',s.replace('−','-')) or 0)

W='Windows and doors'
def row(pg,name):return pg.locator('#v-budget tr.bitem',has=pg.locator('select option[selected]',has_text=name)).first
def item(pg,name,vi=-1):return pg.evaluate(f"(()=>{{const b=__bud();const v=b.versions.at({vi});return JSON.parse(JSON.stringify(v.items.find(i=>i.name==={json.dumps(name)})))}})()")
with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':1300,'height':900});errs=[]
  pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script(INIT);pg.goto(URL+'#budget');pg.wait_for_timeout(700)
  # link Maple Grove - North project to this budget (projected) so the build cost follows it
  pg.select_option('#blink','maple');pg.click('[data-act="b-link"]');pg.wait_for_timeout(300)
  tile0=money(pg.inner_text('#v-budget .tiles .tile >> nth=0 >> .v'))
  proj0=money(pg.locator('#v-budget .tiles .tile').last.locator('.v').inner_text())
  build0=pg.evaluate("__dbg.effP(__S().projects.find(p=>p.id==='maple')).build")
  r=row(pg,W)
  chk('line without upgrades shows "+ Upgrade"','+ Upgrade' in r.locator('.uchip').inner_text())
  r.locator('[data-act="b-ups"]').click();pg.wait_for_timeout(200)
  chk('panel opens under the line with empty message',pg.locator('#v-budget tr.uprow').count()==1 and 'No upgrades on this line yet' in pg.inner_text('#v-budget tr.uprow'))
  pg.click('#v-budget tr.uprow [data-act="b-upadd"]');pg.wait_for_timeout(200)
  f=pg.evaluate("document.activeElement.dataset.up||''")
  chk('new upgrade row focuses its name',f.endswith(':name'))
  pg.keyboard.type('Triple-pane upgrade');pg.keyboard.press('Tab');pg.wait_for_timeout(200)
  pg.locator('#v-budget tr.uprow input[data-up$=":amt"]').fill('4200');pg.locator('#v-budget tr.uprow input[data-up$=":amt"]').press('Tab');pg.wait_for_timeout(250)
  it=item(pg,W);u=it['ups'][0]
  chk('upgrade saved on the version item with defaults',u['name']=='Triple-pane upgrade' and u['amt']==4200 and u['yes'] is False and u['status']=='Quoted' and u['by']=='Buyer')
  chk('price shown with commas',pg.locator('#v-budget tr.uprow input[data-up$=":amt"]').input_value()=='4,200')
  chk('No adds $0: tile unchanged',money(pg.inner_text('#v-budget .tiles .tile >> nth=0 >> .v'))==tile0)
  pg.click('#v-budget tr.uprow [data-act="b-upyn"][data-v="1"]');pg.wait_for_timeout(250)
  it=item(pg,W);u=it['ups'][0]
  chk('Yes marks Quoted -> Approved',u['yes'] is True and u['status']=='Approved')
  chk('focus stays on Yes after re-render',pg.evaluate("document.activeElement.dataset.v")=='1')
  r=row(pg,W)
  lt=money(r.locator('td.c-lt b').inner_text())
  chk('line total = base + Yes upgrades (69,150)',abs(lt-69150)<0.01)
  chk('chip shows 1 and +$4,200','+$4,200' in r.locator('.uchip').inner_text() and '1' in r.locator('.uchip .n').inner_text())
  ou=r.locator('td.c-ou').inner_text();chk('over/under vs line total (66,628.44 - 69,150 = -2,521.56)','2,521.56' in ou and ('−' in ou or '-' in ou))
  t1=money(pg.inner_text('#v-budget .tiles .tile >> nth=0 >> .v'));chk('Budget total tile +4,200',abs(t1-tile0-4200)<1)
  chk('Budget total tile shows base + upgrades','+ $4,200 upgrades' in pg.inner_text('#v-budget .tiles .tile >> nth=0'))
  proj1=money(pg.locator('#v-budget .tiles .tile').last.locator('.v').inner_text())
  chk('projected final cost up by 69,150-66,628.44',abs(proj1-proj0-(69150-66628.44))<1.01)
  build1=pg.evaluate("__dbg.effP(__S().projects.find(p=>p.id==='maple')).build")
  chk('project build cost (Projected) up by 2,521.56',abs(build1-build0-2521.56)<0.01)
  for src,delta in [('budget',4200),('inv',0),('manual',None)]:
    d=pg.evaluate(f"(()=>{{const p=JSON.parse(JSON.stringify(__S().projects.find(p=>p.id==='maple')));p.budget.src='{src}';const a=__dbg.effP(p).build;const s=__S();const it=s.budgets.find(x=>x.id==='b-demo').versions.at(-1).items.find(i=>i.name==={json.dumps(W)});const y=it.ups[0].yes;it.ups[0].yes=false;const b=__dbg.effP(p).build;it.ups[0].yes=y;return a-b;}})()")
    if delta is not None: chk(f'build cost source {src}: upgrade adds {delta}',abs(d-delta)<0.01)
  cat=pg.locator('#v-budget tr.cat',has_text='Structure and envelope')
  chk('category row shows upgrades +$4,200.00 and line total','+$4,200.00' in cat.locator('td.c-ups').inner_text())
  tot=pg.locator('#v-budget tr.tot');chk('total row line total = tile',abs(money(tot.locator('td.c-lt').inner_text())-t1)<1)
  chk('summary card: 1 upgrade on 1 line, 1 approved','1 upgrade on 1 line' in pg.inner_text('#v-budget .upsum') and '1 approved' in pg.inner_text('#v-budget .upsum'))
  # reports
  rep1=pg.text_content('#v-breport')
  # status rules
  sel=pg.locator('#v-budget tr.uprow select[data-up$=":status"]');sel.select_option('Declined');pg.wait_for_timeout(250)
  u=item(pg,W)['ups'][0];chk('Declined sets No',u['yes'] is False and u['status']=='Declined')
  chk('declined row greyed/struck',pg.locator('#v-budget tr.uprow .ug.declined.off').count()==1)
  chk('No: line total back to base',abs(money(row(pg,W).locator('td.c-lt b').inner_text())-64950)<0.01)
  rep2=pg.text_content('#v-breport')
  chk('builder report changes with the upgrade (build cost)',rep1!=rep2)
  inv2=pg.text_content('#v-investors')
  pg.click('#v-budget tr.uprow [data-act="b-upyn"][data-v="1"]');pg.wait_for_timeout(250)
  u=item(pg,W)['ups'][0];chk('Yes on Declined -> Approved',u['yes'] and u['status']=='Approved')
  inv3=pg.text_content('#v-investors')
  chk('investor report changes with the upgrade',inv2!=inv3)
  pg.click('#v-budget tr.uprow [data-act="b-upyn"][data-v="0"]');pg.wait_for_timeout(250)
  u=item(pg,W)['ups'][0];chk('No on Approved -> Quoted',not u['yes'] and u['status']=='Quoted')
  pg.locator('#v-budget tr.uprow select[data-up$=":status"]').select_option('Approved');pg.wait_for_timeout(250)
  u=item(pg,W)['ups'][0];chk('Approved sets Yes',u['yes'])
  pg.locator('#v-budget tr.uprow select[data-up$=":by"]').select_option('Builder');pg.wait_for_timeout(200)
  pg.locator('#v-budget tr.uprow input[data-up$=":note"]').fill('Signed Nov 26');pg.locator('#v-budget tr.uprow input[data-up$=":note"]').press('Tab');pg.wait_for_timeout(200)
  u=item(pg,W)['ups'][0];chk('requested by + note saved',u['by']=='Builder' and u['note']=='Signed Nov 26')
  # second upgrade then remove
  pg.click('#v-budget tr.uprow [data-act="b-upadd"]');pg.wait_for_timeout(200);pg.keyboard.type('Temp');pg.keyboard.press('Tab');pg.wait_for_timeout(200)
  chk('two upgrades listed',pg.locator('#v-budget tr.uprow .ug').count()==2)
  pg.locator('#v-budget tr.uprow [data-act="b-uprm"]').nth(1).click();pg.wait_for_timeout(200)
  chk('remove works',pg.locator('#v-budget tr.uprow .ug').count()==1 and len(item(pg,W)['ups'])==1)
  # line edited highlight + see what changed
  chk('line marked Edited',row(pg,W).evaluate("e=>e.classList.contains('chg')"))
  pg.click('#savestate');pg.wait_for_timeout(300);ch=pg.inner_text('#chbody')
  chk('See what changed lists the upgrade in plain words','new upgrade “Triple-pane upgrade” +$4,200.00 (Yes)' in ch);print('   ',[l for l in ch.split('\n') if 'upgrade' in l][:3])
  pg.click('#chmodal [data-act="ch-close"]');pg.wait_for_timeout(200)
  chk('unsaved bar shown (leave warning)',pg.evaluate("(()=>{const e=new Event('beforeunload',{cancelable:true});dispatchEvent(e);return e.defaultPrevented;})()"))
  # show upgrades toggle: label text must not toggle
  lab=pg.locator('#v-budget label.chk:has(#bups)');bb=lab.bounding_box();pg.mouse.click(bb['x']+bb['width']-20,bb['y']+bb['height']/2);pg.wait_for_timeout(200)
  chk('clicking the label text does not toggle Show upgrades',pg.is_checked('#bups'))
  pg.click('#bups');pg.wait_for_timeout(200)
  chk('toggle off: no upgrades column',pg.locator('#v-budget td.c-ups').count()==0)
  chk('toggle off: budget column shows line total incl. upgrades','$69,150.00' in row(pg,W).locator('td.c-amt').inner_text() and 'incl. +$4,200 upgrades' in row(pg,W).locator('td.c-amt').inner_text())
  chk('toggle off: other lines still editable inputs',row(pg,'Framing').locator('td.c-amt input').count()==1)
  pg.click('#bups');pg.wait_for_timeout(200)
  # new version copies, old keeps; compare
  pg.click('[data-act="b-newver"]');pg.wait_for_timeout(200);pg.click('[data-act="b-vcreate"]');pg.wait_for_timeout(400)
  v2=item(pg,W);v1=item(pg,W,0)
  chk('new version copies upgrades',len(v2['ups'])==1 and v2['ups'][0]['name']=='Triple-pane upgrade')
  chk('compare column shows v1 total',pg.locator('#v-budget .btable thead th',has_text='v1 total').count()==1)
  r=row(pg,W);r.locator('[data-act="b-ups"]').click() if pg.locator('#v-budget tr.uprow').count()==0 else None;pg.wait_for_timeout(200)
  pg.click('#v-budget tr.uprow [data-act="b-upyn"][data-v="0"]');pg.wait_for_timeout(250)
  pg.locator('#v-budget tr.uprow input[data-up$=":amt"]').fill('5,000');pg.locator('#v-budget tr.uprow input[data-up$=":amt"]').press('Tab');pg.wait_for_timeout(250)
  chg=row(pg,W).locator('td.c-chg').inner_text();print('    change cell:',chg.replace('\n',' | '))
  chk('compare shows line-total change and upgrade change','4,200' in chg and 'Upgrades' in chg and 'changed' in chg)
  chk('older version keeps its upgrades',item(pg,W,0)['ups'][0]['yes'] is True and item(pg,W,0)['ups'][0]['amt']==4200)
  pg.click('#savestate');pg.wait_for_timeout(300);ch=pg.inner_text('#chbody');pg.click('#chmodal [data-act="ch-close"]')
  pg.click('[data-act="b-view"] >> nth=0');pg.wait_for_timeout(300)
  r=row(pg,W) if row(pg,W).count() else pg.locator('#v-budget tr.bitem',has_text=W).first
  r=pg.locator('#v-budget tr.bitem',has_text=W).first
  if pg.locator('#v-budget tr.uprow').count()==0: r.locator('[data-act="b-ups"]').click();pg.wait_for_timeout(200)
  up=pg.inner_text('#v-budget tr.uprow');chk('locked v1 shows upgrades read-only',pg.locator('#v-budget tr.uprow input').count()==0 and 'Triple-pane upgrade' in up and 'Yes' in up)
  pg.click('[data-act="b-view"] >> nth=-1');pg.wait_for_timeout(300)
  # backup write + restore round trip
  pg.click('[data-act="bk-open"]');pg.wait_for_timeout(300);pg.select_option('#bkbud','b-demo');pg.click('[data-act="bk-now"]');pg.wait_for_timeout(2500)
  chk('backup done',pg.inner_text('#bkmsg').startswith('Done'))
  hdr=pg.evaluate(f"window.__cells['{K}|\\'Budget\\'|1']")
  chk('backup Budget tab: 10 columns A-J, item id in J, no K-N upgrade columns',len(hdr)==10 and hdr[1].startswith('Budget') and 'Item id' in hdr[9])
  rows=[v for k,v in pg.evaluate(f"Object.entries(window.__cells).filter(([k])=>k.startsWith('{K}|\\'Budget\\'|'))")]
  wr=[r for r in rows if r and str(r[0]).strip()==W+' (base)']
  print('    sheet row:',wr[0] if wr else None)
  chk('backup Budget line row: base in B, item id in J',wr and float(wr[0][1])==64950 and wr[0][9]==v2['id'])
  ur=[r for r in rows if r and str(r[9]).startswith('up:'+v2['id']+':')]
  print('    upgrade row:',ur[0] if ur else None)
  chk('backup Budget upgrade sub-row: No upgrade = 0, label shows by/status/No and price',ur and float(ur[0][1] or 0)==0 and 'Upgrade: Triple-pane upgrade (Builder · Quoted · No)' in ur[0][0] and '5,000.00 not added' in ur[0][0] and ur[0][8]=='Signed Nov 26')
  sr=[r for r in rows if r and str(r[9])=='sub:'+v2['id']]
  chk('backup Budget line total row = base (No upgrade not counted)',sr and float(sr[0][1])==64950 and 'Line total' in sr[0][0])
  data=pg.evaluate(f"window.__books['{K}'].data.at(-1)");js=''.join(data[3:3+int(data[2])])
  chk('backup data JSON holds the upgrades','Triple-pane upgrade' in js and '"ups"' in js)
  summ=[v for k,v in pg.evaluate(f"Object.entries(window.__cells).filter(([k])=>k.startsWith('{K}|\\'Summary\\'|'))")]
  chk('backup Summary says Budget (with upgrades)',any('Budget (with upgrades)' in [str(x) for x in r] for r in summ if r))
  pg.evaluate(f"""(()=>{{const T={{}};Object.entries(window.__cells).forEach(([k,v])=>{{const m=k.match(/^{K}\\|'(.*)'\\|(\\d+)$/);if(!m)return;(T[m[1]]=T[m[1]]||[])[+m[2]-1]=v.map(x=>typeof x==='string'&&x[0]==="'"?x.slice(1):x);}});Object.values(T).forEach(a=>{{for(let i=0;i<a.length;i++)if(!a[i])a[i]=[];}});window.__T=T;}})()""")
  pg.click('#syncgo');pg.wait_for_timeout(800);st=pg.inner_text('#syncres');print('    sync:',st[:160].replace('\n',' '))
  chk('sync from sheet: Budget tab with upgrade columns gives no differences','No differences' in st)
  pg.evaluate("window.__T=null")
  pg.click('[data-act="bk-close"]');pg.wait_for_timeout(200)
  # remove upgrade, then restore from backup brings it back
  r=pg.locator('#v-budget tr.bitem',has_text=W).first
  if pg.locator('#v-budget tr.uprow').count()==0: r.locator('[data-act="b-ups"]').click();pg.wait_for_timeout(200)
  pg.locator('#v-budget tr.uprow [data-act="b-uprm"]').first.click();pg.wait_for_timeout(200)
  chk('upgrade removed before restore','ups' not in item(pg,W))
  pg.click('[data-act="bk-open"]');pg.wait_for_timeout(300);pg.select_option('#bkbud','b-demo');pg.wait_for_timeout(600)
  pg.click('#bklist [data-act="bk-load"] >> nth=0');pg.wait_for_timeout(300);pg.click('#qmok');pg.wait_for_timeout(800)
  it=item(pg,W);chk('restore brings the upgrades back exactly',it.get('ups') and it['ups'][0]['amt']==5000 and it['ups'][0]['by']=='Builder' and it['ups'][0]['note']=='Signed Nov 26' and item(pg,W,0)['ups'][0]['amt']==4200)
  # sync-from-sheet: a Budget tab with the new columns gives no false differences
  # discard returns to live store (no ups)
  pg.evaluate("document.querySelector('[data-act=\"bk-close\"]')&&document.querySelector('[data-act=\"bk-close\"]').click()")
  pg.click('#nbar [data-act="nb-undo"]');pg.wait_for_timeout(500)
  chk('undo restore returns to the pre-restore state (upgrade removed on v2)','ups' not in item(pg,W) and item(pg,W,0)['ups'][0]['amt']==4200)
  pg.click('#nbar [data-act="nb-discard"]') if pg.locator('#nbar [data-act="nb-discard"]').count() else None;pg.wait_for_timeout(200)
  if pg.locator('#qmok').is_visible(): pg.click('#qmok');pg.wait_for_timeout(500)
  print("    nbar:",pg.inner_text("#nbar")[:200]);chk("discard removes all upgrade edits",pg.evaluate("__S().budgets.every(b=>b.versions.every(v=>v.items.every(i=>!i.ups)))"))
  chk('no page errors',not errs);print(errs)
  # mobile checks
  for w in [375,390]:
    m=b.new_page(viewport={'width':w,'height':900});m.add_init_script(INIT);m.goto(URL+'#budget');m.wait_for_timeout(700)
    r=m.locator('#v-budget tr.bitem',has_text=W).first;r.locator('[data-act="b-ups"]').click();m.wait_for_timeout(200)
    m.click('#v-budget tr.uprow [data-act="b-upadd"]');m.wait_for_timeout(200);m.keyboard.type('Test');m.keyboard.press('Tab');m.wait_for_timeout(200)
    m.click('#v-budget tr.uprow [data-act="b-upyn"][data-v="1"]');m.wait_for_timeout(200)
    small=m.evaluate("""[...document.querySelectorAll('#v-budget tr.uprow button,#v-budget tr.uprow input,#v-budget tr.uprow select,#v-budget .uchip')].filter(e=>e.offsetParent).map(e=>[e.dataset.act||e.dataset.up||e.className,Math.round(e.getBoundingClientRect().height),Math.round(e.getBoundingClientRect().width)]).filter(x=>x[1]<44||x[2]<44)""")
    chk(f'{w}: all upgrade controls >=44px',not small);small and print(small)
    chk(f'{w}: no horizontal scroll',m.evaluate("document.documentElement.scrollWidth")==w)
    hs=m.evaluate("[...document.querySelectorAll('#v-budget .uchip')].map(e=>e.getBoundingClientRect().height)")
    chk(f'{w}: chips equal height with and without upgrades',len(set(round(h) for h in hs))==1)
    tr=m.evaluate("[...document.querySelectorAll('#v-budget .btable td.c-lt b,#v-budget .btable td.c-amt b')].filter(e=>e.scrollWidth>e.clientWidth+1).length")
    chk(f'{w}: no truncated money',tr==0)
    m.close()
  b.close()
print(len(ok),'/',len(ok)+len(bad))

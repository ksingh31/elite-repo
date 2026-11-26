import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *
import sys,json,re
from tcmock import TCI
from playwright.sync_api import sync_playwright
URL=APP_URL
ok=[];bad=[]
def chk(n,c):(ok if c else bad).append(n);print(('PASS ' if c else 'FAIL ')+n,flush=True)
J=lambda pg,js:pg.evaluate(js)
def item(pg,name):return J(pg,f"(()=>{{const b=__tcdbg.store().budgets.find(x=>x.id==='b-demo');const v=b.versions[b.versions.length-1];const i=v.items.find(i=>i.name==={json.dumps(name)});return i?JSON.parse(JSON.stringify(i)):null}})()")
def act(pg,r,k):pg.click(f'#tc-r{r} [data-act=tc-do][data-k={k}]');pg.wait_for_timeout(150)
def save(pg,r):pg.click(f'#tc-r{r} [data-act=tc-saveone]');pg.wait_for_timeout(500)
def W(pg):return J(pg,'window.__tcW')
def staged(pg,r):return pg.locator(f'#tc-r{r}.staged').count()==1
def new(b,extra='',w=1300,h=900,th='light',hash='#tocheck'):
  pg=b.new_page(viewport={'width':w,'height':h},color_scheme=th);pg.errs=[];pg.on('pageerror',lambda e:pg.errs.append(str(e)))
  pg.add_init_script(TCI+extra+(";localStorage.setItem('ec-theme','dark');" if th=='dark' else ''));pg.goto(URL+hash);pg.wait_for_timeout(1300);return pg
with sync_playwright() as p:
  b=p.chromium.launch();allerr=[]
  pg=new(b)
  chk('17 rows shown (TOTALS row skipped)',pg.locator('#v-tocheck article.tc').count()==17)
  chk('tab count 17',pg.inner_text('#tccnt').strip()=='17')
  fc={g:pg.inner_text(f'[data-act=tc-grp][data-g={g}] .c') for g in ['all','dup','cat','det','oth']}
  chk('filter counts dup2 cat8 det4 oth3 '+str(fc),fc=={'all':'17','dup':'2','cat':'8','det':'4','oth':'3'})
  chk('read range A3:L of To check',J(pg,'window.__tcGets')>=1)
  chk('why text from column J shown','likely entered twice' in pg.inner_text('#tc-r4'))
  chk('"Why is this here?" disclosure',pg.locator('#tc-r4 details.whyrule').count()==1)
  # --- duplicate
  g0=item(pg,'Garbage truck')
  act(pg,4,'deldup')
  chk('dup: staged "Resolved — not saved"',staged(pg,4) and 'Resolved — not saved' in pg.inner_text('#tc-r4'))
  chk('dup: staged shows effect preview','Garbage truck −$452.67' in pg.inner_text('#tc-r4'))
  chk('dup: nothing written / budget unchanged before save',W(pg)==[] and item(pg,'Garbage truck')['act']==g0['act'])
  chk('pending bar Save all (1)','Save all (1)' in pg.inner_text('#tcpbar'))
  save(pg,4)
  w=W(pg);print(w)
  chk('header K3:L3 written first',w[0]['range']=="'To check'!K3:L3" and w[0]['values']==[['Status','Resolution']])
  chk('row K4:L4 = Resolved + resolution text',w[1]['range']=="'To check'!K4:L4" and w[1]['values'][0][0]=='Resolved' and 'Deleted the duplicate' in w[1]['values'][0][1])
  g1=item(pg,'Garbage truck')
  chk('dup: invoice entry deleted, act -452.67',len(g1['invs'])==len(g0['invs'])-1 and abs(g0['act']-g1['act']-452.67)<0.01 and len(g1['pays'])==len(g0['pays'])-1)
  chk('budget change is an unsaved change (yellow bar)',pg.inner_text('#savestate')=='Unsaved changes' and pg.is_visible('#nbar'))
  chk('resolved card with Reopen',pg.locator('#tc-r4 [data-act=tc-reopen]').count()==1)
  chk('tab count 16',pg.inner_text('#tccnt').strip()=='16')
  # reopen
  pg.click('#tc-r4 [data-act=tc-reopen]');pg.wait_for_timeout(150)
  chk('reopen staged',staged(pg,4) and 'Reopen — not saved' in pg.inner_text('#tc-r4') and 'Garbage truck +$452.67' in pg.inner_text('#tc-r4'))
  save(pg,4);w=W(pg)[-1]
  chk('reopen: K=Open, history appended in L',w['values'][0][0]=='Open' and w['values'][0][1].count('\n')==1 and 'Reopened' in w['values'][0][1])
  g2=item(pg,'Garbage truck')
  chk('reopen: invoice + payment restored',len(g2['invs'])==len(g0['invs']) and abs(g2['act']-g0['act'])<0.005 and g2['invs']==g0['invs'])
  chk('reopen: record removed',J(pg,"!(__tcdbg.store().budgets[0].toCheck||{}).r4"))
  # --- bulk move: Star Interiors
  fl0=item(pg,'Flooring');mi0=item(pg,'Miscellaneous')
  pg.click('#tc-r8 .ck .cb');pg.click('#tc-r9 .ck .cb');pg.wait_for_timeout(150)
  chk('bulk bar shows same-kind action',pg.is_visible('#tcbulk') and 'Move all to Miscellaneous' in pg.inner_text('#tcbulk'))
  pg.click('#tcbulk [data-act=tc-bulkdo][data-k=sugmove]');pg.wait_for_timeout(150)
  chk('bulk: both staged',staged(pg,8) and staged(pg,9))
  pg.click('#tcpbar [data-act=tc-saveall]');pg.wait_for_timeout(700)
  fl1=item(pg,'Flooring');mi1=item(pg,'Miscellaneous')
  chk('save all: Flooring -539.98, Misc +539.98',abs(fl0['act']-fl1['act']-539.98)<0.01 and abs(mi1['act']-mi0['act']-539.98)<0.01)
  chk('save all: rows 8 and 9 marked Resolved',[x['range'] for x in W(pg)[-2:]]==["'To check'!K8:L8","'To check'!K9:L9"])
  # --- split Redstone Surveys Group
  la0=item(pg,'Landscaping');lu0=item(pg,'Lumber + truss package')
  act(pg,7,'split');chk('split dialog open',pg.is_visible('#tcdlg'))
  lid=J(pg,"__tcdbg.store().budgets[0].versions[0].items.find(i=>i.name==='Lumber + truss package').id")
  pg.select_option('#tcsl1',lid);pg.fill('#tcsa0','5000');pg.fill('#tcsa1','2942.19');pg.wait_for_timeout(100)
  chk('split preview live','Lumber + truss package +$2,942.19' in pg.inner_text('#tcprev'))
  pg.click('[data-act=tc-dlgok]');pg.wait_for_timeout(150);save(pg,7)
  la1=item(pg,'Landscaping');lu1=item(pg,'Lumber + truss package')
  chk('split: Landscaping -2942.19, Lumber +2942.19',abs(la0['act']-la1['act']-2942.19)<0.01 and abs(lu1['act']-lu0['act']-2942.19)<0.01)
  pl=sum(x['amt'] for x in lu1['pays'])-sum(x['amt'] for x in lu0['pays'])
  chk('split: paid share moved too',abs(pl-2942.19)<0.02)
  # --- move via picker (framing company row) -> Construction fence
  cf0=item(pg,'Construction fence')
  act(pg,6,'move');pg.fill('#tcq','fence');pg.wait_for_timeout(100)
  pg.click('#tcplist [data-act=tc-pick]:has-text("Construction fence")');pg.wait_for_timeout(100)
  pg.fill('#tcdn','Checked with Jordan');pg.click('[data-act=tc-dlgok]');pg.wait_for_timeout(150)
  chk('move staged with note','Checked with Jordan' in pg.inner_text('#tc-r6'))
  save(pg,6);cf1=item(pg,'Construction fence')
  chk('move: Construction fence +8740.59',abs(cf1['act']-cf0['act']-8740.59)<0.01)
  chk('move: note + name in L','Note: Checked with Jordan' in W(pg)[-1]['values'][0][1])
  # --- sheet changed
  act(pg,17,'usesheet');save(pg,17)
  qv=[i for i in item(pg,'Construction fence')['invs'] if 'Willow Doors' in i['vendor']][0]
  chk('sheet changed: invoice no 128 + note fence deck',qv['no']=='128' and qv['note']=='fence deck')
  # --- date
  act(pg,10,'save');save(pg,10)
  iv=[i for i in item(pg,'Appliances')['invs'] if i['vendor']=='Rosewood Lighting Ltd.'][0]
  chk('date: suggested Nov 1 saved',iv['date']=='2026-11-01')
  n0=len(W(pg));act(pg,11,'asis');save(pg,11)
  chk('date as is: row written, no budget change',len(W(pg))==n0+1 and [i for i in item(pg,'Outside railing')['invs']][0]['date']=='2026-12-01')
  # --- nocat create line / assign / keep
  act(pg,14,'create');pg.fill('#tccn','Engineering and survey');pg.wait_for_timeout(100);pg.click('[data-act=tc-dlgok]');pg.wait_for_timeout(150);save(pg,14)
  es=item(pg,'Engineering and survey')
  chk('create new line: line exists with the invoice',es and abs(es['act']-529.21)<0.01 and es['cat']=='Soft costs')
  act(pg,13,'assign');pg.click('#tcplist [data-act=tc-pick]:has-text("Staging")');pg.click('[data-act=tc-dlgok]');pg.wait_for_timeout(150);save(pg,13)
  chk('assign: Cobalt Lighting on Staging',any('Cobalt Lighting' in i['vendor'] for i in item(pg,'Staging')['invs']))
  act(pg,12,'keep');save(pg,12)
  chk('keep: row resolved',J(pg,"__tcdbg.TC().items.find(i=>i.key==='r12').status")=='resolved')
  # --- ownline merge + reopen
  m0=item(pg,'Miscellaneous')
  act(pg,16,'merge');save(pg,16)
  chk('merge: Corner Coffee Co. line removed, Misc +1041.72',item(pg,'Site refreshments (coffee)') is None and abs(item(pg,'Miscellaneous')['act']-m0['act']-1041.72)<0.01)
  pg.click('#tc-r16 [data-act=tc-reopen]');pg.wait_for_timeout(100);save(pg,16)
  th=item(pg,'Site refreshments (coffee)')
  chk('merge reopened: line back with 64 receipts',th and len(th['invs'])==64 and abs(item(pg,'Miscellaneous')['act']-m0['act'])<0.01)
  # --- estimate
  act(pg,19,'keepest');save(pg,19)
  ml=[i for i in item(pg,'Lumber + truss package')['invs'] if 'Missing' in i['vendor']][0]
  chk('keep estimate: marked',ml.get('est') is True and ml['note'].startswith('Estimate'))
  pg.click('#tc-r19 [data-act=tc-reopen]');save(pg,19)
  lu2=item(pg,'Lumber + truss package')
  act(pg,19,'remove');save(pg,19)
  chk('remove placeholder: -27924',abs(lu2['act']-item(pg,'Lumber + truss package')['act']-27924)<0.01)
  pg.click('#tc-r19 [data-act=tc-reopen]');save(pg,19)
  act(pg,19,'replace');pg.fill('#tcrv','Meridian Tile Ltd.');pg.fill('#tcri','INV-0042');pg.fill('#tcrd','2026-08-28');pg.fill('#tcra','27336.50');pg.wait_for_timeout(100)
  chk('replace preview shows -587.50','−$587.50' in pg.inner_text('#tcprev'))
  pg.click('[data-act=tc-dlgok]');save(pg,19)
  rv=[i for i in item(pg,'Lumber + truss package')['invs'] if i['no']=='INV-0042']
  chk('replace: placeholder became the real invoice',rv and rv[0]['amt']==27336.5 and rv[0]['date']=='2026-08-28')
  # --- payments
  act(pg,20,'match');pg.click('#tcdlg [data-act=tc-mpick]:has-text("INV-0042")');pg.click('[data-act=tc-dlgok]');save(pg,20)
  py=[x for x in item(pg,'Lumber + truss package')['pays'] if x['id']=='p0390'][0]
  chk('match payment: linked to invoice',py['inv']==rv[0]['id'])
  act(pg,21,'deposit');save(pg,21)
  py=[x for x in item(pg,'Lumber + truss package')['pays'] if x['id']=='p0389'][0]
  chk('deposit: payment marked',py.get('deposit') is True and py['ref'].startswith('Deposit'))
  # --- undo / discard
  act(pg,5,'keepboth');pg.click('#tc-r5 [data-act=tc-discardone]');pg.wait_for_timeout(100)
  chk('undo staged: back to open',not staged(pg,5) and pg.locator('#tc-r5 [data-act=tc-do]').count()>0)
  act(pg,5,'keepboth');act(pg,15,'keep');pg.click('[data-act=tc-discardall]');pg.wait_for_timeout(100)
  chk('discard all',J(pg,"__tcdbg.TC().items.filter(i=>i.pending).length")==0)
  # checkbox rule
  pg.click('#v-tocheck .selall .cbtxt');pg.wait_for_timeout(100)
  chk('checkbox label text not clickable',not pg.is_checked('#tcselall'))
  # --- leave popup
  act(pg,5,'keepboth');pg.click('.tabs a[href="#budget"]');pg.wait_for_timeout(150)
  chk('leave popup shown',pg.is_visible('#tcleave') and 'Save your resolutions?' in pg.inner_text('#tcleave'))
  chk('leave popup buttons',[x.strip() for x in pg.locator('#tcleave button').all_inner_texts()]==['Save all and continue','Discard and continue','Go back'])
  pg.click('#tcleave [data-act=tc-lvback]');pg.wait_for_timeout(100)
  chk('go back keeps staged + view',not pg.is_visible('#tcleave') and staged(pg,5) and 'tocheck' in pg.url)
  pg.click('.tabs a[href="#inputs"]');pg.click('#tcleave [data-act=tc-lvdiscard]');pg.wait_for_timeout(200)
  chk('discard and continue: staged gone, app unsaved popup next (dirty)',J(pg,"__tcdbg.TC().items.find(i=>i.key==='r5').pending")==None and pg.is_visible('#modal'))
  pg.click('#modal [data-act=m-cancel]');pg.wait_for_timeout(100)
  act(pg,5,'keepboth');pg.click('.tabs a[href="#inputs"]');pg.click('#tcleave [data-act=tc-lvsave]');pg.wait_for_timeout(700)
  chk('save all and continue: row written',W(pg)[-1]['range']=="'To check'!K5:L5" and pg.is_visible('#modal'))
  pg.click('#modal [data-act=m-cancel]');pg.wait_for_timeout(100)
  # back-button/hash route with staged
  act(pg,15,'keep');pg.evaluate("location.hash='#budget'");pg.wait_for_timeout(300)
  chk('hash change with staged shows popup',pg.is_visible('#tcleave') and 'tocheck' in pg.url)
  pg.click('#tcleave [data-act=tc-lvback]')
  # budget switch guarded
  pg.evaluate("const s=document.querySelector('#bsel');s.value=s.options[s.options.length-1].value;s.dispatchEvent(new Event('change',{bubbles:true}))");pg.wait_for_timeout(150)
  chk('budget switch with staged shows popup',pg.is_visible('#tcleave'));pg.click('#tcleave [data-act=tc-lvback]')
  pg.click('#tc-r15 [data-act=tc-discardone]')
  # --- writes audit
  w=W(pg)
  chk('all sheet writes only K:L of To check in the budget backup sheet ('+str(len(w))+')',all(x['id']==K and re.fullmatch(r"'To check'!K(\d+):L\1",x['range']) for x in w))
  calls=J(pg,'window.__calls.map(c=>[c[1],c[2].spreadsheetId||"",c[2].range||""])')
  chk('no other write to any sheet from To check work',not any(c[0] in('update_values','append_values','update_spreadsheet','batch_clear_values') for c in calls))
  chk('never the invoice/master sheet',not any(('YOUR_INVOICE' in c[1] or 'YOUR_RETIRED' in c[1]) for c in calls) and not any('YOUR_INVOICE' in x['id'] for x in w))
  for args,nm in [(["YOUR_INVOICE_SHEET_ID","'To check'!K4:L4",[['a','b']]],'invoice sheet'),(["YOUR_RETIRED_MASTER_SHEET_ID","'To check'!K4:L4",[['a','b']]],'master sheet'),([K,"'To check'!A4:B4",[['a','b']]],'other columns'),([K,"'Budget'!K4:L4",[['a','b']]],'other tab'),([K,"'To check'!K4:L9",[['a','b']]],'multi-row'),(["SOMEOTHER","'To check'!K4:L4",[['a','b']]],'unknown sheet')]:
    r=J(pg,f"__tcdbg.tcWrite(...{json.dumps(args)}).then(()=>'wrote',e=>e.code)")
    chk('guard refuses '+nm,r=='blocked')
  chk('refused writes never reached Sheets',len(W(pg))==len(w))
  # --- budget page banner + chips
  pg.click('.tabs a[href="#budget"]');pg.wait_for_timeout(200)
  if pg.is_visible('#modal'):pg.click('#modal [data-act=m-cancel]')
  # navigate by hash with navOK? use JS
  pg.evaluate("document.querySelector('#modal').hidden=true");
  openN=J(pg,"__tcdbg.TC().items.filter(i=>i.status!=='resolved').length")
  pg.evaluate("location.hash='#budget'");pg.wait_for_timeout(300)
  if pg.is_visible('#modal'):pg.click('#modal [data-act=m-discard]') if False else None
  print('url',pg.url,'open',openN)
  # --- discard calculator changes reverts sheet rows with budget effects
  nW=len(W(pg));kl=J(pg,'JSON.stringify(window.__tcKL)')
  pg.evaluate("document.querySelector('#modal').hidden=true");
  pg.click('#nbar [data-act=nb-discard]');pg.wait_for_timeout(100);pg.click('#qmok');pg.wait_for_timeout(1500)
  kl2=J(pg,'window.__tcKL')
  chk('discard: rows with budget changes back to before in sheet',kl2['6'][0]=='' and kl2['8'][0]=='' and kl2['19'][0]=='' )
  chk('discard: rows without budget change stay Resolved',kl2['11'][0]=='Resolved' and kl2['5'][0]=='Resolved' and kl2['12'][0]=='Resolved')
  chk('discard: reverts also only K:L',all(re.fullmatch(r"'To check'!K(\d+):L\1",x['range']) for x in W(pg)[nW:]))
  allerr+=pg.errs;pg.close()
  # --- budget banner/chips, save for team clears session list
  pg=new(b,hash='#budget')
  chk('budget banner with count + Review now','17 invoice rows to check' in pg.inner_text('#tcban') and pg.locator('#tcban a.tcgo').count()==1)
  ch=pg.locator('#v-budget .tcchip[data-tcline="Landscaping"]')
  chk('chip on Landscaping (3 to check)',ch.count()>=1 and ch.first.inner_text().replace('\n',' ').startswith('3'))
  chk('chip on Flooring',pg.locator('#v-budget .tcchip[data-tcline="Flooring"]').count()>=1)
  ch.first.click();pg.wait_for_timeout(300)
  chk('chip opens To check filtered by line','tocheck' in pg.url and pg.locator('#v-tocheck article.tc').count()==3 and 'Line: Landscaping' in pg.inner_text('#v-tocheck .filters'))
  pg.click('[data-act=tc-clearline]');pg.wait_for_timeout(100)
  act(pg,7,'keep');save(pg,7);act(pg,8,'sugmove');save(pg,8)
  chk('session writes tracked',J(pg,'__tcdbg.writes().length')==1)
  pg.click('[data-act=save]');pg.wait_for_timeout(1500)
  chk('save for team clears session list',J(pg,'__tcdbg.writes().length')==0 and J(pg,'window.__pub')>=1)
  chk('saved store keeps resolution record','"toCheck"' in J(pg,'window.__html||""'))
  allerr+=pg.errs;pg.close()
  # --- write failure
  pg=new(b,";window.__tcFailWrite=1;")
  g0=item(pg,'Garbage truck');act(pg,4,'deldup');save(pg,4);pg.wait_for_timeout(2500)
  chk('write failure: stays staged, budget unchanged',staged(pg,4) and item(pg,'Garbage truck')['act']==g0['act'] and pg.inner_text('#savestate')=='All changes saved')
  allerr+=pg.errs;pg.close()
  # --- error states
  pg=new(b,";window.__noMcp=1;");chk('no connector: friendly message',"Google Sheets isn’t connected" in pg.inner_text('#v-tocheck'));allerr+=pg.errs;pg.close()
  pg=new(b,";window.__tcFailRead='Unable to parse range: \\'To check\\'!A3:L';");chk('no To check tab: friendly message','has no “To check” tab' in pg.inner_text('#v-tocheck'));allerr+=pg.errs;pg.close()
  pg=new(b,";window.__tcFailRead='Internal error';",hash='#tocheck');pg.wait_for_timeout(2500);chk('read error: friendly message + Refresh',"Couldn’t read" in pg.inner_text('#v-tocheck') and pg.locator('[data-act=tc-reload]').count()==1);allerr+=pg.errs;pg.close()
  pg=new(b);pg.evaluate("__tcdbg.store().budgets[0].sheetId=null");pg.click('[data-act=tc-reload]');pg.wait_for_timeout(300)
  t=pg.inner_text('#v-tocheck');chk('budget without sheet: friendly message','no backup sheet yet' in t or 'No budget' in t)
  allerr+=pg.errs;pg.close()
  chk('no script errors '+str(allerr[:3]),not allerr)
print(len(ok),'/',len(ok)+len(bad));[print('FAILED:',x) for x in bad]

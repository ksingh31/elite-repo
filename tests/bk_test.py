import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *
import asyncio,json
from playwright.async_api import async_playwright
INIT=r'''
window.__calls=[];window.__pub=0;window.__cells={};window.__books={};window.__found={};
const book=id=>window.__books[id]||(window.__books[id]={tabs:[{sheetId:0,title:'Sheet1'}],data:[],log:[]});
const mcp={callTool:async(s,t,i)=>{window.__calls.push([s,t,i]);
  if(s==='Google Drive'&&t==='search_files'){const m=i.query.match(/title = '(.*)' and trashed/);const id=m&&window.__found[m[1].replace(/\\'/g,"'")];return {payload:{files:id?[{id}]:[]}};}
  if(s==='Google Drive'&&t==='create_file'){const id='NEWFILE'+window.__calls.length;book(id);return {payload:{id}};}
  const B=book(i.spreadsheetId||'');
  if(t==='update_spreadsheet'){const T=JSON.parse(JSON.stringify(B.tabs)),C=Object.assign({},window.__cells);const pre=(i.spreadsheetId||'')+'|';
    for(const r of (i.requests||[])){
      if(r.addSheet){const p=r.addSheet.properties;if(T.some(z=>z.sheetId===p.sheetId||z.title===p.title))throw {code:'tool_error',message:'duplicate sheet '+p.sheetId};T.push(Object.assign({},p));}
      if(r.deleteSheet){const x=T.find(z=>z.sheetId===r.deleteSheet.sheetId);if(!x)throw {code:'tool_error',message:'No sheet with id: '+r.deleteSheet.sheetId};T.splice(T.indexOf(x),1);Object.keys(C).forEach(k=>{if(k.startsWith(pre+"'"+x.title+"'|"))delete C[k];});}
      if(r.updateSheetProperties){const p=r.updateSheetProperties.properties;const x=T.find(z=>z.sheetId===p.sheetId);if(!x)throw {code:'tool_error',message:'No sheet with id: '+p.sheetId};
        if(p.title!=null&&p.title!==x.title){Object.keys(C).forEach(k=>{if(k.startsWith(pre+"'"+x.title+"'|")){C[k.replace(pre+"'"+x.title+"'|",pre+"'"+p.title+"'|")]=C[k];delete C[k];}});x.title=p.title;}
        if(p.hidden!=null)x.hidden=p.hidden;}
      ['repeatCell','updateBorders','updateDimensionProperties','setBasicFilter','addConditionalFormatRule'].forEach(k=>{if(r[k]){const ids=[];JSON.stringify(r[k],(kk,v)=>{if(kk==='sheetId')ids.push(v);return v;});ids.forEach(id=>{if(!T.some(z=>z.sheetId===id))throw {code:'tool_error',message:'No grid with id: '+id};});}});}
    if(window.__failOn&&i.requests.some(window.__failOn))throw {code:'tool_error',message:'Invalid requests[0]: simulated failure'};
    B.tabs=T;window.__cells=C;return {payload:{}};}
  if(t==='append_values'){if(i.range.includes('Backup data'))B.data.push(...i.values);else B.log.push(...i.values);return {payload:{}};}
  if(t==='update_values'){const m=i.range.match(/^(.*)!A(\d+):/);if(m)i.values.forEach((r,k)=>{window.__cells[(i.spreadsheetId||'')+'|'+m[1]+'|'+(+m[2]+k)]=r;});return {payload:{}};}
  if(t==='get_spreadsheet')return {payload:{sheets:B.tabs.map(p=>({properties:p}))}};
  if(t==='get_values'){
    {const m=i.range.match(/^('.*')!A(\d+)$/);if(m){const r=window.__cells[(i.spreadsheetId||'')+'|'+m[1]+'|'+m[2]];return {payload:{values:r?[r]:[]}};}}
    if(/Backup data'!A1:C$/.test(i.range))return {payload:{values:[['When','What triggered it','Parts'],...B.data.map(r=>r.slice(0,3))]}};
    if(/Backup data'!A2:C$/.test(i.range))return {payload:{values:B.data.map(r=>r.slice(0,3))}};
    const m=i.range.match(/Backup data'!A(\d+):L/);if(m)return {payload:{values:[B.data[+m[1]-2]]}};
    if(/Backup log'!A1:G$/.test(i.range))return {payload:{values:B.log}};return {payload:{values:[]}};}
  return {payload:{}};}};
window.claude={use:n=>Promise.resolve(n==='mcp'?mcp:n==='artifact'?{publish:async h=>{await new Promise(r=>setTimeout(r,window.__pubDelay||0));window.__pub++;window.__html=h;}}:n==='downloads'?{save:async()=>{}}:null)};
'''

def main():
  from playwright.sync_api import sync_playwright
  ok=[];bad=[]
  def chk(n,c):(ok if c else bad).append(n);print(('PASS ' if c else 'FAIL ')+n)
  with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.add_init_script(INIT)
    pg.goto(APP_URL);pg.wait_for_timeout(700)
    
    # budget page link
    pg.click('.tabs a[href="#budget"]');pg.wait_for_timeout(300)
    href=pg.get_attribute('#bsheet','href') or ''
    chk('budget page has Open Google Sheet link to sample sheet',K in href and not pg.evaluate("document.querySelector('#bsheet').hidden"))
    pg.click('[data-act="bk-open"]');pg.wait_for_timeout(300)
    chk('backup window preselects current budget',pg.eval_on_selector('#bkbud','e=>e.value')=='b-demo')
    chk('open-sheet button points at that budget sheet',K in (pg.get_attribute('#bklink','href') or ''))
    pg.click('[data-act="bk-now"]');pg.wait_for_timeout(1500)
    msg=pg.inner_text('#bkmsg');print('msg:',msg)
    chk('backup done message',msg.startswith('Done'))
    calls=pg.evaluate('window.__calls.map(c=>[c[0],c[1],c[2].spreadsheetId||"",c[2].range||""])')
    chk('no master sheet used',not any('YOUR_RETIRED' in c[2] for c in calls))
    chk('no Drive create for existing sheet',not any(c[1]=='create_file' for c in calls))
    tabs=pg.evaluate("window.__books['"+K+"'].tabs.map(t=>t.title)");print('tabs',tabs)
    chk('book has Summary/Budget/types/Backup tabs',all(t in tabs for t in ['Read me','Summary','Budget','Trade','Material','Service','Other','Backup log','Backup data']))
    chk('restore point appended in the budget sheet',pg.evaluate("window.__books['"+K+"'].data.length")>=1)
    pg.wait_for_timeout(300)
    chk('restore points listed',pg.locator('#bklist [data-act="bk-load"]').count()>=1)
    # new budget: no sheetId -> search -> create
    pg.evaluate("document.querySelector('[data-act=\"bk-close\"]').click()")
    pg.evaluate("document.querySelector('[data-act=\"b-new\"]')&&document.querySelector('[data-act=\"b-new\"]').click()");pg.wait_for_timeout(400)
    if pg.locator('#d-discard').is_visible(): pg.click('#d-discard');pg.wait_for_timeout(300)
    nb=pg.evaluate("document.querySelector('#bsheet').hidden");chk('new budget has no sheet link yet',nb)
    pg.click('[data-act="bk-open"]');pg.wait_for_timeout(300)
    chk('new budget shows "No sheet yet"','No sheet yet' in pg.inner_text('#bklink'))
    n0=pg.evaluate('window.__calls.length')
    pg.click('[data-act="bk-now"]');pg.wait_for_timeout(2000)
    msg=pg.inner_text('#bkmsg');print('msg2:',msg)
    new=pg.evaluate("window.__calls.slice("+str(n0)+").filter(c=>c[1]==='create_file').length")
    chk('one new sheet created for the new budget',new==1)
    chk('message asks to Save for team','Save for team' in msg)
    chk('link now shown for new budget',not pg.evaluate("document.querySelector('#bsheet').hidden") and 'NEWFILE' in (pg.get_attribute('#bklink','href') or ''))
    # second backup should not create again
    n1=pg.evaluate('window.__calls.length');pg.click('[data-act="bk-now"]');pg.wait_for_timeout(1800)
    chk('second backup reuses sheet',pg.evaluate("window.__calls.slice("+str(n1)+").filter(c=>c[1]==='create_file').length")==0)
    # restore from list: confirm, banner, undo
    pg.click('#bklist [data-act="bk-load"] >> nth=0');pg.wait_for_timeout(400)
    chk('restore asks first (confirm window)',pg.locator('#qmodal').is_visible() and 'Undo restore' in pg.inner_text('#qmx'))
    chk('confirm mentions unsaved changes are kept for undo','unsaved changes' in pg.inner_text('#qmx'))
    pg.click('#qmodal [data-act="q-cancel"]');pg.wait_for_timeout(200)
    chk('cancel keeps backup window open, nothing loaded',not pg.locator('#qmodal').is_visible() and 'Showing the restore point' not in (pg.inner_text('#nbar') if pg.locator('#nbar').is_visible() else ''))
    nb_before=pg.evaluate("JSON.parse(localStorage.getItem('ec-calc5')).data.budgets.length")
    pg.select_option('#bkbud','b-demo');pg.wait_for_timeout(400)
    pg.click('#bklist [data-act="bk-load"] >> nth=-1');pg.wait_for_timeout(300);pg.click('#qmok');pg.wait_for_timeout(700)
    chk('banner shows restore point',pg.locator('#nbar').is_visible() and 'Showing the restore point' in pg.inner_text('#nbar'))
    chk('restore replaced data (older copy has fewer budgets)',pg.evaluate("JSON.parse(localStorage.getItem('ec-calc5')).data.budgets.length")<nb_before)
    pg.click('#nbar [data-act="nb-undo"]');pg.wait_for_timeout(500)
    chk('undo brings back exactly what was there (incl. unsaved new budget)',pg.evaluate("JSON.parse(localStorage.getItem('ec-calc5')).data.budgets.length")==nb_before)
    chk('after undo banner shows unsaved changes, not restore','unsaved change' in pg.inner_text('#nbar') and 'restore point' not in pg.inner_text('#nbar'))
    # review changes window
    pg.click('#savestate');pg.wait_for_timeout(300)
    chk('review window lists the new budget','New budget' in pg.inner_text('#chbody'))
    pg.click('#chmodal [data-act="ch-close"]');pg.wait_for_timeout(200)
    # leave warning
    chk('leaving with unsaved changes asks first',pg.evaluate("(()=>{const e=new Event('beforeunload',{cancelable:true});dispatchEvent(e);return e.defaultPrevented;})()"))
    # refresh keeps changes and says so
    pg.reload();pg.wait_for_timeout(900)
    chk('after refresh: bar says changes kept on this device','kept on this device' in pg.inner_text('#nbar'))
    # discard asks, then clears
    pg.click('#nbar [data-act="nb-discard"]');pg.wait_for_timeout(200)
    chk('discard asks to confirm',pg.locator('#qmodal').is_visible())
    pg.click('#qmok');pg.wait_for_timeout(500)
    print('after discard:',pg.locator('#nbar').is_visible(),pg.inner_text('#nbar')[:150],pg.inner_text('#savestate'))
    chk('discard clears bar and state',not pg.locator('#nbar').is_visible() and pg.inner_text('#savestate')=='All changes saved')
    chk('no leave warning when clean',not pg.evaluate("(()=>{const e=new Event('beforeunload',{cancelable:true});dispatchEvent(e);return e.defaultPrevented;})()"))
    # edited budget line is highlighted
    pg.click('.tabs a[href="#budget"]');pg.wait_for_timeout(300)
    inp=pg.locator('#v-budget input[data-k$=":amt"], #v-budget input[data-p^="item:"]').first
    if inp.count()==0: inp=pg.locator('#v-budget td.num input').first
    inp.fill('123');inp.press('Tab');pg.wait_for_timeout(400)
    chk('edited line highlighted',pg.locator('#v-budget tr.chg').count()>=1 and 'Edited' in pg.locator('#v-budget tr.chg').first.inner_text())
    # stale draft: someone else saved since
    pg.evaluate("(()=>{const d=JSON.parse(localStorage.getItem('ec-calc5'));d.base='2000-01-01';localStorage.setItem('ec-calc5',JSON.stringify(d));})()")
    pg.reload();pg.wait_for_timeout(900)
    chk('stale draft: bar offers download instead of silently dropping','weren’t loaded' in pg.inner_text('#nbar') and pg.locator('#nbar [data-act="nb-dl"]').count()==1)
    pg.click('#nbar [data-act="nb-dismiss"]');pg.wait_for_timeout(200)
    # safety: failure while swapping keeps old tabs; user tabs are never deleted
    pg.click('[data-act="bk-open"]');pg.wait_for_timeout(300);pg.select_option('#bkbud','b-demo');pg.click('[data-act="bk-now"]');pg.wait_for_timeout(2500);pg.evaluate("document.querySelector('[data-act=\"bk-close\"]').click()")
    pg.evaluate("(()=>{const B=window.__books['"+K+"'];B.tabs.push({sheetId:777,title:'To check'});window.__cells['"+K+"|\\'To check\\'|1']=['keep me'];})()")
    pg.evaluate("()=>{window.__failOn=r=>!!r.deleteSheet}")
    pg.click('[data-act="bk-open"]');pg.wait_for_timeout(300);pg.select_option('#bkbud','b-demo');pg.click('[data-act="bk-now"]');pg.wait_for_timeout(2500)
    msg=pg.inner_text('#bkmsg');print('fail msg:',msg)
    chk('failure message says which step and that nothing was lost','swapping in the new tabs' in msg and 'nothing was lost' in msg)
    trade=pg.evaluate("window.__cells['"+K+"|\\'Trade\\'|1']")
    chk('old Trade tab still has its data after a failed backup',bool(trade and trade[0]))
    pg.evaluate("()=>{window.__failOn=null}");pg.click('[data-act="bk-now"]');pg.wait_for_timeout(2500)
    tabs=pg.evaluate("window.__books['"+K+"'].tabs.map(t=>t.title)");print(tabs)
    chk('next backup cleans up and succeeds',pg.inner_text('#bkmsg').startswith('Done') and not any('(updating)' in t for t in tabs))
    chk('user tab To check kept with its content','To check' in tabs and pg.evaluate("window.__cells['"+K+"|\\'To check\\'|1']")==['keep me'])
    # save for team clears everything
    pg.evaluate("document.querySelector('[data-act=\"bk-close\"]').click()")
    pg.click('[data-act="save"]');pg.wait_for_timeout(2500)
    html=pg.evaluate('window.__html||""')
    chk('published',pg.evaluate('window.__pub')>=1)
    chk('published store keeps sample sheetId',K in html)
    chk('after save: clean state and no leave warning',pg.inner_text('#savestate')=='All changes saved' and not pg.evaluate("(()=>{const e=new Event('beforeunload',{cancelable:true});dispatchEvent(e);return e.defaultPrevented;})()"))
    chk('no page errors',not errs);print(errs)
    b.close()
  print(len(ok),'/',len(ok)+len(bad))
main()

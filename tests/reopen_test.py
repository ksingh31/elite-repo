import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *
import sys
from playwright.sync_api import sync_playwright

HOST=r'''window.claude={use:n=>Promise.resolve(n==='mcp'?null:n==='artifact'?{publish:async h=>{await new Promise(r=>setTimeout(r,150));await window.__hostPub(h);setTimeout(()=>location.reload(),30);await new Promise(r=>setTimeout(r,500));}}:n==='downloads'?{save:async()=>{}}:null)};'''
URL='http://app.test/index.html'
res=[]
def ok(n,c,d=''):res.append(c);print(('PASS ' if c else 'FAIL ')+n,'' if c else d)
with sync_playwright() as p:
  b=p.chromium.launch()
  for W,H in [(390,844),(1300,900)]:
    print('==',W)
    import re,json
    h0=open(APP).read()
    m=re.search(r'(<script id="store" type="application/json">)([\s\S]*?)(</script>)',h0);sj=json.loads(m.group(2));sj['catalog'].append({'cat':'Temp category','items':['Alpha','Beta']})
    h0=h0[:m.start(2)]+json.dumps(sj).replace('<','\\u003c')+h0[m.end(2):]
    cur={'html':h0,'n':0}
    ctx=b.new_context(viewport={'width':W,'height':H});pg=ctx.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('http://app.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=cur['html']))
    def pub(h):cur['html']=h;cur['n']+=1
    pg.expose_function('__hostPub',pub)
    pg.add_init_script(INIT+';'+HOST)
    pg.goto(URL+'#budget');pg.wait_for_timeout(700)
    vis=lambda:pg.evaluate("!document.getElementById('tmodal').hidden")
    st=lambda:pg.evaluate("document.querySelector('#tmodal .mbox').scrollTop")
    act=lambda:pg.evaluate("(()=>{const a=document.activeElement;return a.id||a.dataset.type||a.dataset.act||a.tagName})()")
    toasts=lambda:pg.evaluate("[...document.querySelectorAll('#toasts .toast span')].map(x=>x.textContent).join(' | ')")
    def waitreload(n0):
      for _ in range(60):
        pg.wait_for_timeout(100)
        try:
          if cur['n']>n0 and pg.evaluate("!window.__old"): break
        except Exception: pass
      for _ in range(60):
        pg.wait_for_timeout(100)
        try:
          if cur['n']>n0 and pg.evaluate("document.readyState=='complete'&&!!window.__dbg"): break
        except Exception: pass
      pg.wait_for_timeout(500)
    # unsaved other change: rename budget-line amount via Inputs? use a simple store edit: change company via draft -> edit first budget amount input
    pg.click('[data-act="t-open"]');pg.wait_for_timeout(200)
    # make another unsaved change outside the types window first
    pg.keyboard.press('Escape');pg.wait_for_timeout(150)
    f=pg.locator('#v-budget [data-b="ver:note"]').first;f.fill("Test note keep me");f.press('Tab');pg.wait_for_timeout(300)
    dirty0=pg.evaluate("document.getElementById('savestate').textContent");ok('other change is unsaved',dirty0=='Unsaved changes',dirty0)
    v0=f.input_value()
    if pg.evaluate("!document.getElementById('dmodal').hidden") or pg.evaluate("!document.getElementById('modal').hidden"):print('guard shown')
    pg.click('[data-act="t-open"]');pg.wait_for_timeout(200)
    ncat=pg.evaluate("document.querySelectorAll('#tbody section.tcat').length")
    # ADD in a category further down, after scrolling
    ci=min(3,ncat-1)
    pg.locator(f'#tadd-{ci}').scroll_into_view_if_needed();pg.fill(f'#tadd-{ci}','Geotech report');s0=st()
    pg.evaluate('window.__old=1');n0=cur['n'];pg.click(f'[data-act="t-add"][data-c="{ci}"]');waitreload(n0)
    ok('add: page actually reloaded with new html',cur['n']==n0+1 and 'Geotech report' in pg.content())
    ok('add: window reopened',vis())
    ok('add: scroll kept',abs(st()-s0)<=2,(st(),s0))
    ok('add: focus on that add input',act()==f'tadd-{ci}',act())
    ok('add: Saved toast after reload','Saved for the team' in toasts(),toasts())
    ok('add: on Budget tab',pg.evaluate("location.hash")=='#budget')
    ok('add: other unsaved change survived',pg.evaluate("document.getElementById('savestate').textContent")=='Unsaved changes' and 'other changes are still unsaved' in toasts(),toasts())
    ok('flag cleared',pg.evaluate("sessionStorage.getItem('ec-types-reopen')") is None)
    # DELETE TYPE (the one just added, unused)
    rows=pg.evaluate(f"[...document.querySelectorAll('#tbody input[data-type^=\"{ci}:\"]')].map(x=>x.value)")
    ti=rows.index('Geotech report')
    s0=st();pg.evaluate('window.__old=1');n0=cur['n'];pg.click(f'[data-act="t-del"][data-c="{ci}"][data-t="{ti}"]');pg.wait_for_timeout(200)
    pg.fill('#cmtype','delete');pg.click('#cmok');waitreload(n0)
    ok('del type: reloaded',cur['n']==n0+1 and 'Geotech report' not in cur['html'].split('id="store"')[1][:200000])
    ok('del type: window reopened',vis() and pg.evaluate("document.getElementById('cmodal').hidden"))
    ok('del type: scroll kept',abs(st()-s0)<=40,(st(),s0))
    a=act();ok('del type: focus in same category',a.startswith(f'{ci}:') or a==f'tadd-{ci}',a)
    ok('del type: Saved toast','Item type Geotech report deleted. Saved for the team' in toasts(),toasts())
    # RENAME
    nm=pg.input_value(f'[data-type="{ci}:0"]')
    s0=st();pg.evaluate('window.__old=1');n0=cur['n'];inp=pg.locator(f'[data-type="{ci}:0"]');inp.fill(nm+' X');inp.press('Tab');waitreload(n0)
    ok('rename: reloaded',cur['n']==n0+1 and (nm+' X') in pg.content())
    ok('rename: window reopened',vis())
    ok('rename: scroll kept',abs(st()-s0)<=40,(st(),s0))
    ok('rename: focus on renamed input',act()==f'{ci}:0',act())
    ok('rename: toast','Renamed' in toasts() and 'Saved for the team' in toasts(),toasts())
    # DELETE CATEGORY: add an empty category? find a deletable one
    dc=pg.evaluate("(()=>{const b=document.querySelector('[data-act=\"t-delcat\"]');return b?+b.dataset.c:-1})()")
    if dc<0:
      print('no deletable category; creating one via store edit+save')
    else:
      cat=pg.evaluate(f"document.querySelectorAll('#tbody section.tcat h3')[{dc}].textContent")
      pg.locator(f'[data-act="t-delcat"][data-c="{dc}"]').scroll_into_view_if_needed();s0=st()
      pg.evaluate('window.__old=1');n0=cur['n'];pg.click(f'[data-act="t-delcat"][data-c="{dc}"]');pg.wait_for_timeout(200);pg.fill('#cmtype','delete');pg.click('#cmok');waitreload(n0)
      ok('del cat: reloaded',cur['n']==n0+1)
      ok('del cat: window reopened',vis())
      ok('del cat: scroll kept (within clamp)',abs(st()-s0)<=60 or st()==pg.evaluate("(()=>{const b=document.querySelector('#tmodal .mbox');return b.scrollHeight-b.clientHeight})()"),(st(),s0))
      a=act();ok('del cat: focus restored in window',pg.evaluate("document.getElementById('tmodal').contains(document.activeElement)"),a)
      ok('del cat: toast','Category '+cat+' deleted. Saved for the team' in toasts(),toasts())
    # other change still there
    pg.keyboard.press('Escape');pg.wait_for_timeout(300)
    ok('Close/Escape closes it',not vis() and pg.evaluate("document.getElementById('dmodal').hidden"))
    ok('flag cleared on close',pg.evaluate("sessionStorage.getItem('ec-types-reopen')") is None)
    pg.reload();pg.wait_for_timeout(800)
    ok('manual reload after close does not reopen',not vis())
    ok('other unsaved value still there',pg.locator('#v-budget [data-b="ver:note"]').first.input_value()==v0,(pg.locator('#v-budget [data-b="ver:note"]').first.input_value(),v0))
    ok('no stale-draft bar',pg.evaluate("localStorage.getItem('ec-calc5-stale')") is None)
    pg.screenshot(path=f'{OUT}/after_{W}.png')
    ok('no page errors',not errs,errs)
    ctx.close()
  b.close()
print('ALL PASS' if all(res) else 'SOME FAIL', sum(res),'/',len(res))

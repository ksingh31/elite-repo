import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *
from playwright.sync_api import sync_playwright
import json,sys

AUD=r'''()=>{
 const parse=c=>{const m=c.match(/rgba?\(([^)]+)\)/);if(!m)return null;const p=m[1].split(',').map(x=>parseFloat(x));return {r:p[0],g:p[1],b:p[2],a:p.length>3?p[3]:1};};
 const lum=c=>{const f=v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)};return .2126*f(c.r)+.7152*f(c.g)+.0722*f(c.b)};
 const bgOf=el=>{let e=el;while(e){const c=parse(getComputedStyle(e).backgroundColor);if(c&&c.a>0.5)return c;e=e.parentElement;}return {r:255,g:255,b:255,a:1}};
 const out=[];const seen=new Set();
 document.querySelectorAll('button,a,label,span,td,th,h2,h3,p,div.v,div.lbl,small,b,strong,option,input,select').forEach(el=>{
  const r=el.getBoundingClientRect();if(r.width<2||r.height<2)return;const cs=getComputedStyle(el);if(cs.visibility==='hidden'||cs.display==='none'||parseFloat(cs.opacity)<0.2)return;
  let p=el;while(p){if(p.hidden||getComputedStyle(p).display==='none')return;p=p.parentElement;}
  const txt=(el.tagName==='INPUT'||el.tagName==='SELECT')?(el.value||''):[...el.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent).join('').trim();
  if(!txt)return;const fg=parse(cs.color),bg=bgOf(el);if(!fg)return;
  const L1=lum(fg),L2=lum(bg),cr=(Math.max(L1,L2)+.05)/(Math.min(L1,L2)+.05);
  if(cr<3){const k=el.tagName+txt.slice(0,30);if(!seen.has(k)){seen.add(k);out.push({tag:el.tagName,txt:txt.slice(0,40),cr:Math.round(cr*100)/100});}}});
 // ctrl rows: buttons heights differ
 const mis=[];document.querySelectorAll('.ctrl').forEach(c=>{const kids=[...c.children].filter(k=>/BUTTON|A/.test(k.tagName)&&k.getBoundingClientRect().width>0);if(kids.length<2)return;const hs=kids.map(k=>Math.round(k.getBoundingClientRect().height)),ts=kids.map(k=>Math.round(k.getBoundingClientRect().top));
   if(Math.max(...hs)-Math.min(...hs)>6&&new Set(ts).size===1)mis.push(kids.map(k=>(k.textContent||'').trim().slice(0,20)+':'+Math.round(k.getBoundingClientRect().height)).join(' | '));});
 return {low:out,mis,overflow:document.documentElement.scrollWidth>window.innerWidth+1};}'''
res={}
def audit(pg,name):
  r=pg.evaluate(AUD)
  hov=[]
  btns=pg.locator('.modal:not([hidden]) button:visible, .modal:not([hidden]) a.btn:visible')
  for i in range(min(btns.count(),25)):
    bt=btns.nth(i)
    try:
      bt.hover(timeout=500)
      x=bt.evaluate('''el=>{const p=c=>{const m=c.match(/rgba?\(([^)]+)\)/);const q=m[1].split(',').map(Number);return q};const cs=getComputedStyle(el);let e=el,bg=null;while(e){const c=p(getComputedStyle(e).backgroundColor);if((c[3]===undefined||c[3]>0.5)){bg=c;break;}e=e.parentElement;}const f=p(cs.color);const L=c=>{const g=v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)};return .2126*g(c[0])+.7152*g(c[1])+.0722*g(c[2])};const a=L(f),b=L(bg||[255,255,255]);return [(el.textContent||'').trim().slice(0,30),(Math.max(a,b)+.05)/(Math.min(a,b)+.05)]}''')
      if x[0] and x[1]<3: hov.append(x)
    except Exception as e: pass
  pg.mouse.move(1,1)
  r['hover_low']=hov;res[name]=r
  pg.screenshot(path=f'{OUT}/aud/{name}.png')
os.makedirs(OUT+'/aud',exist_ok=True)
w=int(sys.argv[1]) if len(sys.argv)>1 else 1300
with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':w,'height':900});errs=[]
  pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script(INIT+";window.__data=[['2026-11-25 22:38','Save for team','1','{}'],['2026-11-25 22:17','Back up now','1','{}']];")
  pg.goto(APP_URL);pg.wait_for_timeout(700)
  for tab in ['inputs','builder','investor','budget']:
    l=pg.locator(f'.tabs a[href="#{tab}"]')
    if l.count(): l.first.click();pg.wait_for_timeout(300);audit(pg,'tab_'+tab)
  pg.click('[data-act="bk-open"]');pg.wait_for_timeout(300);audit(pg,'m_backups');pg.keyboard.press('Escape');pg.wait_for_timeout(100)
  pg.click('.tabs a[href="#budget"]');pg.wait_for_timeout(200)
  pg.click('[data-act="t-open"]');pg.wait_for_timeout(300);audit(pg,'m_types');pg.keyboard.press('Escape');pg.wait_for_timeout(100)
  pg.locator('button.actbtn').nth(5).click();pg.wait_for_timeout(300);audit(pg,'m_pay')
  pg.click('[data-act="p-showinv"]');pg.wait_for_timeout(100);audit(pg,'m_pay_addinv')
  pg.click('[data-act="p-showpay"]');pg.wait_for_timeout(100);audit(pg,'m_pay_addpay')
  pg.locator('[data-act="p-invedit"]').first.click();pg.wait_for_timeout(100);audit(pg,'m_pay_edit')
  pg.keyboard.press('Escape');pg.wait_for_timeout(100)
  pg.keyboard.press('Escape');pg.wait_for_timeout(100)  # 1st Esc now cancels the inline edit
  pg.click('[data-act="b-newver"]');pg.wait_for_timeout(200);audit(pg,'m_version');pg.keyboard.press('Escape')
  json.dump(res,open(OUT+"/aud/res.json","w"));print("errors",errs)
  b.close()

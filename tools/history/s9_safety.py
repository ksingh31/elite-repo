import re
p='/home/claude/calc/index.html';s=open(p).read()
def rep(old,new,cnt=1):
    global s
    assert old in s,old[:80]
    s=s.replace(old,new,cnt)

# ---------- markup ----------
rep('<span id="savestate" class="savestate clean" role="status" aria-live="polite">All changes saved</span>',
    '<button type="button" id="savestate" class="savestate clean" data-act="ch-open" aria-live="polite">All changes saved</button>')
rep('<main>','''<div id="nbar" class="nbar" hidden role="region" aria-label="Unsaved changes"></div>
<main>''')
rep('<div id="cmodal" class="modal" hidden>','''<div id="qmodal" class="modal" hidden><div class="mbox" role="alertdialog" aria-modal="true" aria-labelledby="qmt"><h2 id="qmt"></h2><div id="qmx"></div>
  <div class="ctrl" style="margin-top:14px"><button class="btn pri" data-act="q-ok" id="qmok">OK</button><button class="ghost" data-act="q-cancel">Cancel</button></div></div></div>
<div id="chmodal" class="modal" hidden><div class="mbox wide" role="dialog" aria-modal="true" aria-labelledby="cht"><h2 id="cht">Your unsaved changes</h2><div id="chbody"></div>
  <div class="ctrl" style="margin-top:14px" id="chbtns"><button class="btn pri" data-act="ch-save">Save for team</button><button class="ghost" data-act="ch-discard">Discard all changes</button><button class="ghost" data-act="ch-close">Close</button></div></div></div>
<div id="cmodal" class="modal" hidden>''')

# ---------- css ----------
rep('</style></head>','''.savestate{border:0;cursor:pointer;font-family:inherit}.savestate.dirty:hover{filter:brightness(.95)}
.nbar{display:flex;flex-wrap:wrap;align-items:center;gap:8px 14px;padding:10px 24px;background:#fff4dc;color:#4a2e00;border-bottom:1px solid #e8c77a;font-size:14px;position:sticky;top:0;z-index:40}
.nbar.info{background:#e6f2f1;color:#0b3d3a;border-color:#a9d3cf}.nbar b{font-weight:800}.nbar .sp{flex:1 1 auto;min-width:200px}
.nbar button{min-height:34px;padding:0 12px;border-radius:8px;border:1px solid #c9a24c;background:#fff;color:#3b2500;font:inherit;font-weight:700;cursor:pointer}
.nbar.info button{border-color:#7fb8b3;color:#0b3d3a}.nbar button.p{background:#14a39a;border-color:#14a39a;color:#06231f}
tr.chg>td:first-child{box-shadow:inset 4px 0 #e0a100}.tag.chgtag{background:#ffe7ad;color:#4a2e00}
.chlist{max-height:55vh;overflow:auto;border:1px solid var(--line);border-radius:10px;margin:8px 0}.chlist h4{margin:0;padding:8px 12px;background:var(--bg);font-size:13px;position:sticky;top:0}
.chlist div{padding:7px 12px;border-top:1px solid var(--line);font-size:14px}.chlist .add{color:#0a6b3d}.chlist .del{color:#b42318}
@media(max-width:640px){.nbar{padding:10px 12px}}
</style></head>''')

# ---------- draft load ----------
rep("""try{const d=JSON.parse(localStorage.getItem('ec-calc5')||'null');if(d&&d.base===store.savedAt&&d.data&&d.data.v===4){store=migrate(d.data);dirty=true;}else if(d)localStorage.removeItem('ec-calc5');localStorage.removeItem('ec-calc5');}catch(e){}""",
"""let draftAt=null,draftLoaded=false,restoreMark=null;
try{const d=JSON.parse(localStorage.getItem('ec-calc5')||'null');
  if(d&&d.base===store.savedAt&&d.data&&d.data.v===4){store=migrate(d.data);dirty=true;draftLoaded=true;draftAt=d.at||null;restoreMark=d.restore||null;}
  else if(d&&d.data){try{localStorage.setItem('ec-calc5-stale',JSON.stringify({at:d.at||null,data:d.data}));}catch(_){}localStorage.removeItem('ec-calc5');localStorage.removeItem('ec-calc5-undo');}}catch(e){}""")
rep("""function persist(){dirty=true;try{localStorage.setItem('ec-calc5',JSON.stringify({base:store.savedAt,data:store}));}catch(e){}markDirty();}""",
"""function persist(){dirty=true;draftAt=new Date().toISOString();try{localStorage.setItem('ec-calc5',JSON.stringify({base:store.savedAt,data:store,at:draftAt,restore:restoreMark}));}catch(e){}markDirty();}""")
rep("""e.title=dirty?'Only on this device until you click Save for team':'Everyone sees the same numbers';}""",
"""e.title=dirty?'Only on this device until you click Save for team. Click to see what changed.':'Everyone sees the same numbers';try{renderNbar();}catch(_){}}""")

# ---------- discard clears restore/undo ----------
rep("""function discard(){const cur=store.cur""","""function discard(){restoreMark=null;try{localStorage.removeItem('ec-calc5-undo');}catch(_){}const cur=store.cur""")

# ---------- save: clear flags so leaving after a save doesn't warn ----------
rep("""    try{await artifact.publish(html);try{localStorage.removeItem('ec-calc5');}catch(_){}}""",
"""    try{await artifact.publish(html);dirty=false;restoreMark=null;try{localStorage.removeItem('ec-calc5');localStorage.removeItem('ec-calc5-undo');}catch(_){}markDirty();}""")

# ---------- restore flow ----------
a=s.index("async function loadBackup(row){");b=s.index("async function saveTeam()",a)
s=s[:a]+r"""async function loadBackup(row){const x=bkRows.find(r=>r.row===row);if(!x)return;
  const go=async()=>{$('#bkmsg').textContent='Loading the restore point from '+x.when+'…';
    try{const v=vals(await sheetsCall('get_values',{spreadsheetId:x.sid,range:"'Backup data'!A"+row+':L'+row}))[0]||[];
      const n=+v[2]||0,parts=v.slice(3,3+n).map(String);let d;
      try{d=JSON.parse(parts.join(''));}catch(_){d=JSON.parse(parts.map(p=>p.replace(/^'/,'')).join(''));}
      if(d.v!==4||!Array.isArray(d.projects))throw {msg:'This restore point isn’t in a format this calculator reads.'};
      const ids={};(store.budgets||[]).forEach(b=>{if(b.sheetId)ids[b.id]=b.sheetId;});(d.budgets||[]).forEach(b=>{if(!b.sheetId&&ids[b.id])b.sheetId=ids[b.id];});
      // keep exactly what was on screen (including unsaved edits) so Undo can bring it back
      try{localStorage.setItem('ec-calc5-undo',JSON.stringify({data:store,dirty,restore:restoreMark,at:new Date().toISOString()}));}catch(_){}
      const cur=store.cur,cb=store.curBudget;d.savedAt=store.savedAt;store=migrate(d);
      if(store.projects.some(p=>p.id===cur))store.cur=cur;else if(!store.projects.some(p=>p.id===store.cur))store.cur=store.projects[0].id;
      if(store.budgets.some(b=>b.id===cb))store.curBudget=cb;
      restoreMark={when:x.when,source:x.source};persist();rerender();
      $('#bkmodal').hidden=true;status('Loaded the restore point from '+x.when+'. Nothing is saved yet: use the yellow bar to Undo or Save for team.');}
    catch(e){$('#bkmsg').textContent=e&&e.msg?e.msg:(e instanceof SyntaxError?'This restore point’s data is damaged and can’t be read.':bkErr(e));}};
  askQ('Load the restore point from '+x.when+'?',
    '<p>This puts the copy taken at <b>'+esc(x.when)+'</b> ('+esc(x.source)+') on your screen, replacing <b>all budgets and projects</b> you see now.</p><p>Nothing changes for the team until you click <b>Save for team</b>. Until then you can click <b>Undo restore</b> to get back exactly what you had'+(dirty?', including your unsaved changes':'')+'.</p>',
    'Load it',go);}
function undoRestore(){let u=null;try{u=JSON.parse(localStorage.getItem('ec-calc5-undo')||'null');}catch(_){}
  if(!u||!u.data){status('There is nothing to undo.','warn');return;}
  store=migrate(u.data);restoreMark=u.restore||null;
  if(u.dirty)persist();else{dirty=false;try{localStorage.removeItem('ec-calc5');}catch(_){}markDirty();}
  try{localStorage.removeItem('ec-calc5-undo');}catch(_){}rerender();status('Restore undone. You’re back to what you had before.');}
function rerender(){try{buildForm();}catch(_){}try{renderBudget();}catch(_){}try{refresh();}catch(_){}markDirty();}
"""+s[b:]

# ---------- review / notice bar / diff ----------
block=r"""
// ---------- unsaved changes: what changed, notice bar, leave warning ----------
let qFn=null;
function askQ(title,html,ok,fn){qFn=fn;$('#qmt').textContent=title;$('#qmx').innerHTML=html;$('#qmok').textContent=ok;$('#qmodal').hidden=false;$('#qmok').focus();}
const words=k=>({sell:'sale price',lot:'lot price',build:'build cost',close:'closing months',lawyer:'lawyer fees',buildGst:'GST on build',sale:'sale type',taxWait:'tax timing',taxOv:'tax override',buildMonths:'build months',sched:'draw schedule',use:'financing',lotLoan:'lot loan',ap:'A&P loan',priv:'private loan',extras:'extra costs',investors:'investors',ohOv:'overhead override',co:'company settings',budget:'linked budget',preBuild:'months before build',name:'name'}[k]||k.replace(/([A-Z])/g,' $1').toLowerCase());
function diffStores(A,B){const out=[],items=new Set(),J=x=>JSON.stringify(x==null?null:x);const add=(g,t,c,iid)=>{out.push({g,t,c:c||''});if(iid)items.add(iid);};
  if(J(A.company)!==J(B.company))add('Company','Company settings changed');
  if(J(A.catalog)!==J(B.catalog))add('Budgets','Item types (Manage item types) changed');
  const pa=new Map((A.projects||[]).map(p=>[p.id,p])),pb=new Map((B.projects||[]).map(p=>[p.id,p]));
  (B.projects||[]).forEach(p=>{const o=pa.get(p.id);if(!o){add('Projects','New project: '+p.name,'add');return;}
    const ks=[...new Set([...Object.keys(o),...Object.keys(p)])].filter(k=>J(o[k])!==J(p[k]));
    if(ks.length)add('Projects',(o.name!==p.name?o.name+' → '+p.name:p.name)+': '+ks.map(words).join(', ')+' changed');});
  (A.projects||[]).forEach(p=>{if(!pb.has(p.id))add('Projects','Deleted project: '+p.name,'del');});
  const ba=new Map((A.budgets||[]).map(b=>[b.id,b])),bb=new Map((B.budgets||[]).map(b=>[b.id,b]));
  const inv=iv=>(iv.vendor||'Invoice')+(iv.no?' #'+iv.no:'')+' '+m(+iv.amt||0);
  (B.budgets||[]).forEach(b=>{const o=ba.get(b.id),G='Budget: '+b.name;if(!o){add(G,'New budget','add');return;}
    if(o.name!==b.name)add(G,'Renamed from '+o.name);
    const va=new Map(o.versions.map(v=>[v.id,v]));
    b.versions.forEach(v=>{const ov=va.get(v.id);if(!ov){add(G,'New version '+v.label,'add');return;}
      const pre=o.versions.length>1||b.versions.length>1?v.label+' · ':'';
      ['label','date','note','above','base','rate'].forEach(k=>{if(J(ov[k])!==J(v[k]))add(G,pre+'Version '+(k==='note'?'“what changed” note':k)+' changed');});
      const ia=new Map(ov.items.map(i=>[i.id,i]));const ib=new Set(v.items.map(i=>i.id));
      v.items.forEach(i=>{const oi=ia.get(i.id);if(!oi){add(G,pre+'New item: '+i.name+' ('+i.cat+') '+m(+i.amt||0),'add',i.id);return;}
        if((+oi.amt||0)!==(+i.amt||0))add(G,pre+i.name+': budget '+m(+oi.amt||0)+' → '+m(+i.amt||0),'',i.id);
        if(oi.name!==i.name)add(G,pre+'Item renamed: '+oi.name+' → '+i.name,'',i.id);
        if(oi.cat!==i.cat)add(G,pre+i.name+': moved from '+oi.cat+' to '+i.cat,'',i.id);
        if((oi.note||'')!==(i.note||''))add(G,pre+i.name+': note changed','',i.id);
        const xa=new Map((oi.invs||[]).map(x=>[x.id,x])),xb=new Set((i.invs||[]).map(x=>x.id));
        (i.invs||[]).forEach(x=>{const ox=xa.get(x.id);if(!ox){add(G,pre+i.name+': new invoice '+inv(x),'add',i.id);return;}
          const f=['vendor','no','date','kind','amt','note'].filter(k=>J(ox[k])!==J(x[k]));
          if(f.length)add(G,pre+i.name+': invoice '+inv(ox)+' — '+f.map(k=>k==='amt'?'amount → '+m(+x.amt||0):k==='no'?'invoice no.':k==='kind'?'type → '+x.kind:k).join(', '),'',i.id);});
        (oi.invs||[]).forEach(x=>{if(!xb.has(x.id))add(G,pre+i.name+': deleted invoice '+inv(x),'del',i.id);});
        const ya=new Map((oi.pays||[]).map(x=>[x.id,x])),yb=new Set((i.pays||[]).map(x=>x.id));
        (i.pays||[]).forEach(y=>{const oy=ya.get(y.id);if(!oy){add(G,pre+i.name+': new payment '+m(+y.amt||0)+(y.method?' ('+y.method+')':''),'add',i.id);return;}
          if(J(oy)!==J(y))add(G,pre+i.name+': payment '+m(+oy.amt||0)+' changed'+((+oy.amt||0)!==(+y.amt||0)?' to '+m(+y.amt||0):''),'',i.id);});
        (oi.pays||[]).forEach(y=>{if(!yb.has(y.id))add(G,pre+i.name+': deleted payment '+m(+y.amt||0),'del',i.id);});});
      ov.items.forEach(i=>{if(!ib.has(i.id))add(G,pre+'Deleted item: '+i.name+' '+m(+i.amt||0),'del');});});
    o.versions.forEach(v=>{if(!b.versions.some(x=>x.id===v.id))add(G,'Deleted version '+v.label,'del');});});
  (A.budgets||[]).forEach(b=>{if(!bb.has(b.id))add('Budget: '+b.name,'Deleted budget','del');});
  return {list:out,items};}
let _dc={k:null,v:null};
function curDiff(){if(!dirty)return {list:[],items:new Set()};const k=JSON.stringify(store);if(_dc.k===k)return _dc.v;let base;try{base=migrate(JSON.parse(PRISTINE));}catch(_){base={projects:[],budgets:[]};}
  const v=diffStores(base,store);_dc={k,v};return v;}
const when2=iso=>{if(!iso)return '';try{return new Date(iso).toLocaleString('en-CA',{timeZone:'America/Edmonton',month:'short',day:'numeric',hour:'numeric',minute:'2-digit'});}catch(_){return '';}};
function renderNbar(){const el=$('#nbar');if(!el)return;let stale=null;try{stale=JSON.parse(localStorage.getItem('ec-calc5-stale')||'null');}catch(_){}
  if(dirty){const n=curDiff().list.length;
    if(n===0&&!restoreMark){el.hidden=true;return;}
    el.className='nbar';
    if(restoreMark)el.innerHTML='<span class="sp"><b>Showing the restore point from '+esc(restoreMark.when)+'</b> ('+esc(restoreMark.source||'')+'). Nothing is saved for the team yet'+(n?' · '+n+' difference'+(n>1?'s':'')+' from the saved version':'')+'.</span><button type="button" data-act="nb-undo">Undo restore</button><button type="button" data-act="ch-open">See what changed</button><button type="button" class="p" data-act="save">Save for team</button>';
    else el.innerHTML='<span class="sp"><b>'+n+' unsaved change'+(n>1?'s':'')+'</b>'+(draftLoaded&&draftAt?' from '+esc(when2(draftAt))+', kept on this device':'')+'. Only you can see '+(n>1?'them':'it')+' until you save.</span><button type="button" data-act="ch-open">See what changed</button><button type="button" class="p" data-act="save">Save for team</button><button type="button" data-act="nb-discard">Discard</button>';
    el.hidden=false;return;}
  if(stale&&stale.data){el.className='nbar';el.innerHTML='<span class="sp"><b>Your unsaved changes'+(stale.at?' from '+esc(when2(stale.at)):'')+' weren’t loaded</b> because someone saved a newer version since. Download them to compare or re-import, or dismiss.</span><button type="button" data-act="nb-dl">Download my changes</button><button type="button" data-act="nb-dismiss">Dismiss</button>';el.hidden=false;return;}
  el.hidden=true;}
function openChanges(){const d=curDiff();const b=$('#chbody');
  if(!dirty||!d.list.length){b.innerHTML='<p>'+(restoreMark?'The restore point you loaded is the same as the saved version.':'No unsaved changes. Everyone sees the same numbers.')+'</p>';$('#chbtns').querySelectorAll('[data-act="ch-save"],[data-act="ch-discard"]').forEach(x=>x.hidden=!dirty);}
  else{const groups={};d.list.forEach(x=>(groups[x.g]=groups[x.g]||[]).push(x));
    b.innerHTML='<p class="note" style="margin:0">'+(restoreMark?'Differences between the restore point from '+esc(restoreMark.when)+' and the last team save.':'Changes since the last team save'+(draftAt?' (last change '+esc(when2(draftAt))+')':'')+'. They are only on this device.')+' Edited budget lines are marked with a yellow bar on the Budget page.</p><div class="chlist">'+Object.keys(groups).map(g=>'<h4>'+esc(g)+' · '+groups[g].length+'</h4>'+groups[g].slice(0,300).map(x=>'<div class="'+x.c+'">'+esc(x.t)+'</div>').join('')+(groups[g].length>300?'<div>…and '+(groups[g].length-300)+' more</div>':'')).join('')+'</div>';
    $('#chbtns').querySelectorAll('button').forEach(x=>x.hidden=false);
    const dbtn=$('#chbtns [data-act="ch-discard"]');dbtn.textContent=restoreMark?'Undo restore':'Discard all changes';}
  $('#chmodal').hidden=false;}
function askDiscardAll(){askQ('Discard your unsaved changes?','<p>This throws away '+(curDiff().list.length||'all')+' unsaved change'+(curDiff().list.length===1?'':'s')+' and goes back to the last team save. It can’t be undone.</p>','Discard changes',()=>{discard();});}
document.addEventListener('click',e=>{const t=e.target.closest('[data-act]');if(!t)return;const a=t.dataset.act;
  if(a==='q-ok'){const f=qFn;qFn=null;$('#qmodal').hidden=true;if(f)f();}
  else if(a==='q-cancel'){qFn=null;$('#qmodal').hidden=true;}
  else if(a==='ch-open')openChanges();
  else if(a==='ch-close')$('#chmodal').hidden=true;
  else if(a==='ch-save'){$('#chmodal').hidden=true;saveTeam();}
  else if(a==='ch-discard'){$('#chmodal').hidden=true;if(restoreMark&&localStorage.getItem('ec-calc5-undo'))undoRestore();else askDiscardAll();}
  else if(a==='nb-undo')undoRestore();
  else if(a==='nb-discard')askDiscardAll();
  else if(a==='nb-dismiss'){try{localStorage.removeItem('ec-calc5-stale');}catch(_){}renderNbar();}
  else if(a==='nb-dl'){let st=null;try{st=JSON.parse(localStorage.getItem('ec-calc5-stale')||'null');}catch(_){}if(!st)return;
    if(!downloads){status('Download isn’t available in this view.','warn');return;}
    downloads.save({filename:'my-unsaved-changes.json',data:JSON.stringify(st.data,null,1)}).then(()=>status('Downloaded. Use Import to load it again.')).catch(()=>status('Download was cancelled.'));}});
addEventListener('beforeunload',e=>{if(dirty&&curDiff().list.length){e.preventDefault();e.returnValue='';return '';}});
"""
rep("addEventListener('hashchange',route);route();buildForm();markDirty();",block+"addEventListener('hashchange',route);route();buildForm();markDirty();")

# Escape / outside-click handling for the new modals
rep("for(const id of ['dmodal','cmodal','modal',","for(const id of ['qmodal','chmodal','dmodal','cmodal','modal',")
rep("  if(id==='dmodal'){$('#dmodal').hidden=true;dFn=null;return;}","  if(id==='qmodal'){$('#qmodal').hidden=true;qFn=null;return;}\n  if(id==='chmodal'){$('#chmodal').hidden=true;return;}\n  if(id==='dmodal'){$('#dmodal').hidden=true;dFn=null;return;}")

# highlight edited rows in the budget table
rep("      return `<tr><td>${nameCell(i,c)}${cmp&&!inC?","      return `<tr${CHG.has(i.id)?' class=\"chg\"':''}><td>${nameCell(i,c)}${CHG.has(i.id)?'<span class=\"tag chgtag\">Edited</span>':''}${cmp&&!inC?")
open(p,'w').write(s)
print('ok')

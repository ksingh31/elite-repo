h=open('/home/claude/calc/index.html').read()
def rep(a,b,cnt=1):
    global h
    assert h.count(a)==cnt,(a[:70],h.count(a)); h=h.replace(a,b)
# CSS fixes
rep('.btn.pri{background:#2bb3a8;border-color:#2bb3a8;color:#06231f}','.btn.pri{background:#2bb3a8;border-color:#2bb3a8;color:#06231f}.btn.pri:hover{background:#25a096;border-color:#25a096}\n.modal .btn:not(.pri){color:var(--ink);background:#fff;border:1px solid var(--line)}.modal .btn:not(.pri):hover{background:#eef3f2;border-color:#0d7a75}.modal a.btn{display:inline-flex;align-items:center;text-decoration:none}.modal .ctrl{align-items:center}\n#dmodal{z-index:35}#dmodal .mbox{max-width:420px}')
# discard dialog markup
rep('<div id="modal" class="modal" hidden>','<div id="dmodal" class="modal" hidden><div class="mbox" role="alertdialog" aria-modal="true" aria-labelledby="dmt"><h2 id="dmt">Discard what you typed?</h2><p id="dmx">You started filling in a form in this window. If you close it now, what you typed there is lost. Changes you already made are kept.</p><div class="ctrl"><button class="btn pri" data-act="d-discard">Discard and close</button><button class="ghost" data-act="d-keep">Keep editing</button></div></div></div>\n<div id="modal" class="modal" hidden>')
JS=r'''
let dFn=null;
function askDiscard(fn){dFn=fn;$('#dmodal').hidden=false;const b=$('#dmodal [data-act="d-keep"]');if(b)b.focus();}
const typed=sel=>[...document.querySelectorAll(sel)].some(x=>String(x.value||'').trim()!=='');
function payPending(){return typed('#in-vendor,#in-no,#in-amt,#pn-amt,#pn-ref');}
function typesPending(){return typed('#tbody input[id^="tadd-"]');}
function verPending(){return typed('#vm-note');}
function requestClose(id){
  if(id==='dmodal'){$('#dmodal').hidden=true;dFn=null;return;}
  if(id==='cmodal'){closeConfirm();return;}
  if(id==='modal'){closeModal();return;}
  if(id==='bkmodal'){$('#bkmodal').hidden=true;return;}
  if(id==='vmodal'){const go=()=>{$('#vmodal').hidden=true;};verPending()?askDiscard(go):go();return;}
  if(id==='tmodal'){const go=()=>{$('#tmodal').hidden=true;renderBudget();};typesPending()?askDiscard(go):go();return;}
  if(id==='pmodal'){payPending()?askDiscard(closePay):closePay();return;}}
document.addEventListener('mousedown',e=>{const m=e.target;if(m&&m.classList&&m.classList.contains('modal')&&!m.hidden){m.dataset.down='1';}},true);
document.addEventListener('click',e=>{const m=e.target;if(m&&m.classList&&m.classList.contains('modal')&&!m.hidden&&m.dataset.down==='1'){m.dataset.down='';requestClose(m.id);}document.querySelectorAll('.modal[data-down]').forEach(x=>{if(x!==m)x.dataset.down='';});},true);
'''
rep('function closeConfirm(){',JS+'function closeConfirm(){')
# Escape: route through requestClose (topmost first)
rep("document.addEventListener('keydown',e=>{if(e.key==='Escape'){if(!$('#cmodal').hidden){closeConfirm();return;}if(!$('#modal').hidden)closeModal();$('#vmodal').hidden=true;closePay();}});",
"document.addEventListener('keydown',e=>{if(e.key!=='Escape')return;for(const id of ['dmodal','cmodal','modal','vmodal','tmodal','bkmodal','pmodal']){const el=$('#'+id);if(el&&!el.hidden){requestClose(id);return;}}});")
# buttons routed
rep("  if(a==='p-close'){closePay();return;}","  if(a==='p-close'){requestClose('pmodal');return;}\n  if(a==='d-keep'){$('#dmodal').hidden=true;dFn=null;return;}\n  if(a==='d-discard'){$('#dmodal').hidden=true;const f=dFn;dFn=null;if(f)f();return;}")
rep("b-vcancel'){$('#vmodal').hidden=true;return;}","b-vcancel'){requestClose('vmodal');return;}")
rep("  if(a==='t-close'){$('#tmodal').hidden=true;renderBudget();return;}","  if(a==='t-close'){requestClose('tmodal');return;}")
rep("  if(a==='bk-close')$('#bkmodal').hidden=true;","  if(a==='bk-close')requestClose('bkmodal');")
# move Manage item types out of the crowded top bar into the Versions toolbar
rep('    <button class="btn" data-act="t-open">Manage item types</button>\n','')
rep('b-newver">+ New version</button>','b-newver">+ New version</button><button class="ghost" data-act="t-open">Manage item types</button>')
open('/home/claude/calc/index.html','w').write(h);print('modals ok')

h=open('/home/claude/calc/index.html').read()
def rep(a,b,cnt=1):
    global h
    assert h.count(a)==cnt,(a[:70],h.count(a)); h=h.replace(a,b)
rep('    <button class="btn danger" data-act="b-del">Delete budget</button>\n','    <button class="btn danger" data-act="b-del">Delete budget</button>\n    <button class="btn" data-act="t-open">Manage item types</button>\n')
rep('<div id="bkmodal" class="modal" hidden>','<div id="tmodal" class="modal" hidden><div class="mbox wide" role="dialog" aria-modal="true" aria-labelledby="tmt"><div id="tbody"></div></div></div>\n<div id="bkmodal" class="modal" hidden>')
rep("  if(a&&a.startsWith('b-')){budgetAct(a,b);return;}","  if(a&&a.startsWith('b-')){budgetAct(a,b);return;}\n  if(a&&a.startsWith('t-')){typesAct(a,b);return;}")
rep("  if(t.dataset.inv){","  if(t.dataset.type){const [ci,ti]=t.dataset.type.split(':').map(Number);renameType(ci,ti,t.value);return;}\n  if(t.dataset.inv){")
rep('let pFocusInv=null;',open('/home/claude/backup/types_js.js').read()+'let pFocusInv=null;')
open('/home/claude/calc/index.html','w').write(h);print('types ok')

import re
h=open('index.html').read()
def rep(a,b,cnt=1):
    global h
    assert h.count(a)==cnt,(a[:70],h.count(a)); h=h.replace(a,b)
# replace renderPay + addPay
s=h.index('function renderPay(){'); e=h.index('let pending=null;')
h=h[:s]+open('/home/claude/backup/inv_js.js').read()+h[e:]
rep("if(!Array.isArray(i.pays))i.pays=[];","if(!Array.isArray(i.pays))i.pays=[];if(!Array.isArray(i.invs))i.invs=[];")
rep("  if(a==='p-add'){addPay();return;}\n  if(a==='p-rest'){const {it}=payCtx();if(it)addPay((+it.act||0)-paid(it));return;}",
"""  if(a==='p-add'){addPay();return;}
  if(a==='p-rest'){addPay(pnRemaining());return;}
  if(a==='p-invadd'){addInv();return;}
  if(a==='p-invpay'){pFocusInv=b.dataset.id;renderPay();const f=$('#pn-amt');if(f){f.focus();f.scrollIntoView({block:'center'});}return;}
  if(a==='p-invdel'){const {it}=payCtx();const iv=it&&it.invs.find(x=>x.id===b.dataset.id);if(!iv)return;const n=it.pays.filter(p=>p.inv===iv.id).length;
    confirmBox('Delete this invoice?','This removes the '+m(+iv.amt||0)+' invoice'+(iv.vendor?' from '+iv.vendor:'')+(iv.no?' (#'+iv.no+')':'')+' on "'+it.name+'".'+(n?' Its '+n+' payment'+(n>1?'s stay':' stays')+' but won\\u2019t be tied to an invoice.':'')+' You can still discard this until you click Save for team.','Delete invoice',()=>{it.invs=it.invs.filter(x=>x!==iv);it.pays.forEach(p=>{if(p.inv===iv.id)p.inv=null;});it.act=r2(it.invs.reduce((t,v)=>t+(+v.amt||0),0));if(pFocusInv===iv.id)pFocusInv=null;persist();renderPay();renderBudget();refresh();status('Invoice deleted.');});return;}""")
rep("  if(t.dataset.pact){","""  if(t.dataset.inv){const {it}=payCtx();const [id,f]=t.dataset.inv.split(':');const iv=it&&it.invs.find(x=>x.id===id);if(iv){iv[f]=f==='amt'?r2(numIn(t.value)):t.value.trim();syncAct(it);persist();renderPay();renderBudget();refresh();}return;}
  if(t.id==='pn-inv'){pFocusInv=t.value||null;const r=pnRemaining(),bt=$('#pn-rest');$('#pn-amt').placeholder=r>0?String(r):'0';if(bt){bt.hidden=!(r>0.004);bt.textContent='Pay remaining '+m(Math.max(0,r));}return;}
  if(t.dataset.pact){""")
rep("py[f]=f==='amt'?(parseFloat(t.value.replace(/[$,\\s]/g,''))||0):t.value;","py[f]=f==='amt'?(parseFloat(t.value.replace(/[$,\\s]/g,''))||0):f==='inv'?(t.value||null):t.value;")
rep("${bshowAct?`<td class=\"num\">${inp('item:'+i.id+':act',ac,1)}</td>","${bshowAct?`<td class=\"num\">${(i.invs&&i.invs.length)?`<button class=\"actbtn\" data-act=\"b-pay\" data-id=\"${esc(i.id)}\" aria-label=\"Invoices for ${esc(i.name)}\">${m(ac)}<small>${i.invs.length} invoice${i.invs.length>1?'s':''}</small></button>`:inp('item:'+i.id+':act',ac,1)}</td>")
rep('.mbox.wide{','.ptable tr.hl td{background:#fff7e6}.ghost.sm{padding:4px 10px;font-size:13px;min-height:0}.ptable td.acts{white-space:nowrap;display:flex;gap:6px;align-items:center;justify-content:flex-end}.fields.addrow{grid-template-columns:repeat(auto-fit,minmax(150px,1fr))}.ktable th[scope=row]{font-weight:600;color:var(--ink);background:none}.actbtn{background:none;border:0;padding:0;font:inherit;color:inherit;text-align:right;cursor:pointer;text-decoration:underline dotted;display:inline-flex;flex-direction:column;align-items:flex-end}.actbtn small{font-size:11px;color:var(--mute);text-decoration:none}\n.mbox.wide{')
open('index.html','w').write(h);print('ok')

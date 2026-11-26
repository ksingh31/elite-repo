h=open('/home/claude/calc/index.html').read()
def rep(a,b,cnt=1):
    global h
    assert h.count(a)==cnt,(a[:70],h.count(a)); h=h.replace(a,b)
s=h.index('function renderPay(){');e=h.index('function allVendors(){')
h=h[:s]+open('/home/claude/steps/render_pay.js').read()+h[e:]
rep("  if(a==='p-invpay'){pFocusInv=b.dataset.id;renderPay();const f=$('#pn-amt');if(f){f.focus();f.scrollIntoView({block:'center'});}return;}",
"""  if(a==='p-invpay'){pFocusInv=b.dataset.id;pForm='pay';pEdit=null;renderPay();const f=$('#pn-amt');if(f){f.focus();f.scrollIntoView({block:'center'});}return;}
  if(a==='p-invedit'){pEdit='i:'+b.dataset.id;renderPay();return;}
  if(a==='p-payedit'){pEdit='p:'+b.dataset.id;renderPay();return;}
  if(a==='p-done'){pEdit=null;renderPay();return;}
  if(a==='p-showinv'){pForm=pForm==='inv'?null:'inv';renderPay();const f=$('#in-vendor');if(f)f.focus();return;}
  if(a==='p-showpay'){pForm=pForm==='pay'?null:'pay';pFocusInv=null;renderPay();const f=$('#pn-inv');if(f)f.focus();return;}
  if(a==='p-formclose'){pForm=null;pFocusInv=null;renderPay();return;}""")
rep("function closePay(){$('#pmodal').hidden=true;pItem=null;}","function closePay(){$('#pmodal').hidden=true;pItem=null;pEdit=null;pForm=null;pFocusInv=null;}")
rep("  pFocusInv=null;persist();renderPay();renderBudget();status(m(a)+' payment added to '+it.name+'.');}","  pFocusInv=null;pForm=null;persist();renderPay();renderBudget();status(m(a)+' payment added to '+it.name+'.');}")
rep("  syncAct(it);persist();renderPay();renderBudget();refresh();status('Invoice from '","  syncAct(it);pForm=null;persist();renderPay();renderBudget();refresh();status('Invoice from '")
css=""".icard{border:1px solid rgba(20,38,61,.14);border-radius:10px;margin:10px 0;background:#fff;overflow:hidden}.icard.hl{box-shadow:0 0 0 2px #e8a33d}.icard.loose{border-style:dashed}
.ihead{display:flex;gap:16px;align-items:center;padding:12px 14px;background:#f5f8f8;flex-wrap:wrap}.iwho{flex:1 1 240px;min-width:0}.iv{font-weight:700;font-size:16px;color:var(--ink)}.imeta{color:var(--mute);font-size:13px;margin-top:2px;overflow-wrap:anywhere}
.inums{display:flex;gap:18px;align-items:center}.inums>div{display:flex;flex-direction:column;align-items:flex-end}.inums span{font-size:11px;color:var(--mute);text-transform:uppercase;letter-spacing:.04em}.inums b{font-size:16px}.inums .st{min-width:110px}
.pill{display:inline-block;border-radius:999px;padding:3px 10px;font-size:12px;font-weight:600;white-space:nowrap}.pill.ok{background:#e3f4ee;color:#0d6b52}.pill.due{background:#fdecdc;color:#a24a07}.pill.k{background:#e8edf3;color:#3b4b60;font-weight:500;vertical-align:2px;margin-left:6px}
.pacts{display:flex;gap:8px;align-items:center}.lnk{background:none;border:0;color:#0d7a75;font:inherit;font-weight:600;cursor:pointer;padding:4px 6px;text-decoration:underline}.btn.sm,.ghost.sm{padding:5px 12px;font-size:13px;min-height:0}.danger-t{color:#b42318}
.plist{padding:2px 14px 6px}.pline{display:grid;grid-template-columns:110px 120px 1fr 120px 60px;gap:12px;align-items:center;padding:8px 0;border-top:1px solid rgba(20,38,61,.07);font-size:14px}.pline:first-child{border-top:0}
.pline .pd{color:var(--ink)}.pline .pm{color:var(--mute)}.pline .pr{color:var(--mute);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.pline .pa{text-align:right;font-weight:600}.pline.none{display:block;color:var(--mute);font-style:italic}
.pline.edit,.ihead.edit{display:flex;flex-wrap:wrap;gap:10px;align-items:flex-end}.pline.edit label,.ihead.edit label{display:flex;flex-direction:column;font-size:12px;color:var(--mute);gap:3px;flex:0 1 140px}.pline.edit label.w,.ihead.edit label.w{flex:1 1 200px}
.pline.edit input,.pline.edit select,.ihead.edit input,.ihead.edit select{padding:7px 9px;border:1px solid rgba(20,38,61,.25);border-radius:7px;font:inherit;font-size:14px;color:var(--ink);background:#fff}
.pbtns{margin:14px 0 4px;gap:10px}.btn.on{background:#e3f4ee;border-color:#0d7a75}.addbox{border:1px solid rgba(13,122,117,.35);background:#f6fbfa;border-radius:10px;padding:12px 14px;margin:8px 0}.addbox h3{margin:0 0 8px}
.kchips{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0 0}.kchip{border:1px solid rgba(20,38,61,.12);border-radius:10px;padding:8px 12px;display:flex;gap:12px;font-size:13px;align-items:baseline;flex-wrap:wrap}.kchip span{color:var(--mute)}.okt{color:#0d6b52!important}.duet{color:#a24a07!important;font-weight:600}
@media(max-width:640px){.pline{grid-template-columns:1fr auto;}.pline .pm,.pline .pr{grid-column:1/-1}.inums{width:100%;justify-content:space-between}}
"""
rep('#pmodal .mbox.wide{max-width:1240px}','#pmodal .mbox.wide{max-width:980px}'+css)
open('/home/claude/calc/index.html','w').write(h);print('cards ok')

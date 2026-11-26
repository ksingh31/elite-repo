p='/home/claude/calc/index.html';s=open(p).read()
def rep(old,new,cnt=1):
    global s
    assert s.count(old)>=1,old[:90]
    s=s.replace(old,new,cnt)
# ---- CSS ----
rep("@media(max-width:600px){.r3,.r4{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}.r3 .x,.r4 .x{grid-column:span 2;width:100%}",
    "@media(max-width:600px){.r3,.r4,.r5{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}.r3 .x,.r4 .x,.r5 .x{grid-column:span 2;width:100%}.cpdraw{grid-template-columns:minmax(0,1fr) minmax(0,1fr) 44px}")
rep("</style></head>",""".r5{grid-template-columns:minmax(0,1.5fr) minmax(0,1.2fr) minmax(0,.9fr) minmax(0,.9fr) minmax(0,.9fr) 44px}
.cpdraw{display:grid;grid-template-columns:70px minmax(0,1fr) minmax(0,1fr) 44px;gap:10px;align-items:end;margin-top:8px}.cpdraw>b{padding-bottom:12px;font-size:14px}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:10px;overflow:hidden;margin:4px 0 2px}.seg label{display:flex;align-items:center;gap:6px;padding:8px 14px;cursor:pointer;font-weight:600;font-size:14px}.seg label.on{background:var(--teal);color:#fff}.seg input{accent-color:#fff}
.feeline{margin-top:10px;padding:10px 12px;border-radius:10px;background:var(--bg);font-size:14px;line-height:1.5}
</style></head>""")
# ---- migrate defaults ----
rep("if(!p.budget)p.budget={use:false,id:null,ver:'latest'};",
    "if(!p.budget)p.budget={use:false,id:null,ver:'latest'};if(!p.cp)p.cp={base:'lb',ltv:0.65,fee:0.03,rate:0.0702,mode:'pct',draws:[{at:3,v:0.3333},{at:6,v:0.3333},{at:9,v:0.3334}],loans:[]};")
# ---- engine ----
rep("const otherCost=ls=>sum((ls||[]).map(x=>(+x.amount||0)*(+x.rate||0)*(+x.months||0)/12));",
    "const otherCost=ls=>sum((ls||[]).map(x=>(+x.amount||0)*((+x.rate||0)*(+x.months||0)/12+(+x.fee||0))));")
rep("""  const pvInt=pdraws.reduce((t,d)=>t+d.int,0);""","""  const pvInt=pdraws.reduce((t,d)=>t+d.int,0);
  // Cash + Private: lot (and early build) in cash; a private draw loan approved as a % of lot + build (or build only),
  // drawn at months after build start, as % of the approval or fixed amounts. Fee is on the approved amount, interest only on what is drawn, until the sale closes.
  const C=p.cp||{},cpBase=C.base==='build'?(+p.build||0):lb,cpA=Math.max(0,(+C.ltv||0)*cpBase),cpRate=+C.rate||0;
  let cpLeft=cpA;const cpdraws=(C.draws||[]).map((d,i)=>{const want=Math.max(0,C.mode==='amt'?(+d.v||0):(+d.v||0)*cpA),amt=Math.min(want,cpLeft);cpLeft-=amt;
    const after=Math.max(0,+d.at||0),at=pre+after,out=Math.max(0,pEnd-at);return {label:'Draw '+(i+1),after,want,amt,at,out,int:amt*cpRate*out/12,late:at>=pEnd&&amt>0};});
  const cpDrawn=sum(cpdraws.map(d=>d.amt)),cpInt=sum(cpdraws.map(d=>d.int)),cpWant=sum(cpdraws.map(d=>d.want)),cpFee=cpA*(+C.fee||0);
  const cp={approved:cpA,base:cpBase,drawn:cpDrawn,undrawn:Math.max(0,cpA-cpDrawn),over:Math.max(0,cpWant-cpA),fee:cpFee,int:cpInt};
  {let before=0;const spendAt=t=>p.lot+upOther+buildNet*(bm>0?Math.min(1,Math.max(0,(t-pre)/bm)):1);cp.peakPts=cpdraws.map(d=>{const v=spendAt(d.at)+(before>0?cpFee:0)-before;before+=d.amt;return v;});}""")
rep("""    mk('cash','All cash',0,0,0,0,[],0,0,0)];""","""    mk('cp','Cash + Private',cpDrawn,cpFee,0,cpInt,C.loans,cpDrawn*cpRate/12,0,0),
    mk('cash','All cash',0,0,0,0,[],0,0,0)];
  {const o=opts.find(x=>x.key==='cp');o.peak=Math.max(o.cash,...cp.peakPts);o.roiPeak=o.peak>0?o.profit/o.peak:0;o.annPeak=ann(o.roiPeak);}""")
rep("T,buildM,bm,done,loanAt,prePeak,draws,drawTotal,pdraws,pDown,pEnd,opts,","T,buildM,bm,done,loanAt,prePeak,draws,drawTotal,pdraws,pDown,pEnd,cpdraws,cp,opts,")
# ---- short loans: fee field ----
rep("""<div class="row r4">${F('Lender',`${key}.loans.${i}.label`,'t')}${F('Amount',`${key}.loans.${i}.amount`,'m')}${F('Rate',`${key}.loans.${i}.rate`,'p')}${F('Months',`${key}.loans.${i}.months`,'n',{u:'mo'})}${X(key+'.loans',i)}</div>""",
    """<div class="row r5">${F('Lender',`${key}.loans.${i}.label`,'t')}${F('Amount',`${key}.loans.${i}.amount`,'m')}${F('Fixed fee',`${key}.loans.${i}.fee`,'p')}${F('Rate',`${key}.loans.${i}.rate`,'p')}${F('Months',`${key}.loans.${i}.months`,'n',{u:'mo'})}${X(key+'.loans',i)}</div>""")
rep("loans:{label:'Private loan',amount:0,rate:0.1,months:6}};","loans:{label:'Private loan',amount:0,fee:0,rate:0.1,months:6},cpd:{at:0,v:0}};")
# add handler: cp.draws uses blank.cpd
rep("arr.push(k==='draws'?0:k==='ms'?1:structuredClone(blank[k]));",
    "arr.push(b.dataset.path==='cp.draws'?{at:(arr.length?(+arr[arr.length-1].at||0)+2:0),v:P().cp.mode==='amt'?0:0}:k==='draws'?0:k==='ms'?1:structuredClone(blank[k]));")
# ---- UI: financing card ----
old="""<p class="note">Lot is paid in cash. The draw loan is ${pc(get('priv.ltv'))} of lot + build.</p>`}"""
rep(old,"""${p.use==='cp'?`<p class="note">Lot and early build are paid in cash. A private draw loan starts after the build begins.</p>`:`<p class="note">Lot is paid in cash. The draw loan is ${pc(get('priv.ltv'))} of lot + build.</p>`}`}""")
old="""`:`<div class="lender"><h3>Private <span>Loan starts at lot purchase</span></h3>"""
rep(old,"""`:p.use==='cp'?cpBlock(p):`<div class="lender"><h3>Private <span>Loan starts at lot purchase</span></h3>""")
rep("""<p class="note">The Builder page compares all four options.""","""<p class="note">The Builder page compares all the options.""")
# cpBlock helper (before buildField)
rep("function buildField(){","""function cpBlock(p){const c=p.cp,amt=c.mode==='amt';
  return `<div class="lender"><h3>Cash + Private <span>Lot in cash · loan drawn after the build starts</span></h3>
    <div class="fields">${B('cp')}${F('Loan approved','cp.ltv','p',{hint:'% of what the loan is based on'})}${F('Fixed fee','cp.fee','p',{hint:'Charged once on the approved amount, drawn or not'})}${F('Interest on drawn amount','cp.rate','p',{hint:'Each draw pays interest until the sale closes'})}</div>
    <p class="note" id="cpappr"></p>
    <h3>Draws</h3><div class="seg" role="radiogroup" aria-label="Enter draws as">
      <label class="${amt?'':'on'}"><input type="radio" name="cpmode" data-radio="cp.mode" value="pct"${amt?'':' checked'}> % of approved loan</label>
      <label class="${amt?'on':''}"><input type="radio" name="cpmode" data-radio="cp.mode" value="amt"${amt?' checked':''}> Fixed $ amount</label></div>
    <p class="note" style="margin-top:4px">Add as many draws as you need. You don’t have to draw the whole loan: anything not drawn has no interest (the fee is still on the approved amount).</p>
    ${(c.draws||[]).map((d,i)=>`<div class="cpdraw"><b>Draw ${i+1}</b>${F('Months after build starts',`cp.draws.${i}.at`,'n',{u:'mo'})}${amt?F('Amount',`cp.draws.${i}.v`,'m'):F('% of approved loan',`cp.draws.${i}.v`,'p')}${X('cp.draws',i)}</div>`).join('')||'<div class="empty" style="margin-top:8px">No draws yet: the loan is approved but nothing is taken.</div>'}
    <button class="add" data-act="add" data-path="cp.draws">Add draw</button><div id="cpwarn"></div>
    <div class="scroll" style="margin-top:12px"><table><thead><tr><th>Draw</th><th>Amount</th><th>Taken at</th><th>Interest for</th><th>Interest</th></tr></thead><tbody id="cpplan"></tbody></table></div>
    <div class="feeline" id="cpfee"></div>${loansBlock('cp')}</div>`;}
function buildField(){""")
# ---- refreshForm: cp plan, fee lines for priv/ap too ----
rep("""  const dw=$('#drawwarn');""","""  const cpp=$('#cpplan');if(cpp){const c=R.cp,cd=R.cpdraws;
    cpp.innerHTML=(cd.length?cd.map((d,i)=>`<tr><td>Draw ${i+1}${RL.cpdraws[i].want>RL.cpdraws[i].amt+0.005?' <span class="tag">capped</span>':''}</td><td>${m(d.amt)}</td><td>month ${rnum(d.after)} of build</td><td>${mo(d.out)}</td><td>${m(d.int)}</td></tr>`).join(''):'<tr><td colspan="5">No draws</td></tr>')+`<tr class="tot"><td>Total drawn</td><td>${m(c.drawn)}</td><td></td><td></td><td>${m(c.int)}</td></tr>`;
    q('cpappr',`Approved loan: ${m(c.approved)} (${pc(P().cp.ltv)} of ${P().cp.base==='build'?'build':'lot + build'} ${m(c.base)}). Drawn: ${m(c.drawn)}. Not drawn: ${m(c.undrawn)}.`);
    const cf=$('#cpfee');if(cf)cf.innerHTML=`Loan cost counted in profit: fee ${pc(P().cp.fee)} × ${m(c.approved)} approved = <b>${m(c.fee)}</b> + interest on draws <b>${m(c.int)}</b>${RL.opts.find(o=>o.key==='cp').other?` + short loans <b>${m(R.opts.find(o=>o.key==='cp').other)}</b>`:''} = <b>${m(R.opts.find(o=>o.key==='cp').fin)}</b>. Loan is paid off when the sale closes, ${mo(R.pEnd)} after lot purchase.`;
    const w=$('#cpwarn');if(w){const late=RL.cpdraws.filter(d=>d.late).length;w.innerHTML=(RL.cp.over>0.5?`<div class="warn">Draws add up to ${m(RL.cp.over+RL.cp.approved)}, more than the ${m(RL.cp.approved)} approved. Later draws are capped at what is left.</div>`:'')+(late?`<div class="warn">${late} draw${late>1?'s are':' is'} after the sale closes and would pay no interest. Check the months.</div>`:'');}}
  const pvf=$('#pvfee');if(pvf){const o=R.opts.find(x=>x.key==='priv');pvf.innerHTML=`Loan cost counted in profit: fee ${pc(P().priv.fee)} × ${m(o.loan)} loan = <b>${m(o.fee)}</b> + interest on draws <b>${m(o.drawInt)}</b>${RL.opts.find(x=>x.key==='priv').other?` + short loans <b>${m(o.other)}</b>`:''} = <b>${m(o.fin)}</b>.`;}
  const apf=$('#apfee');if(apf){const o=R.opts.find(x=>x.key==='ap');apf.innerHTML=`Loan cost counted in profit: fee ${pc(P().ap.fee)} × ${m(o.loan)} loan = <b>${m(o.fee)}</b> + lot mortgage interest <b>${m(o.lotInt)}</b> + draw interest <b>${m(o.drawInt)}</b>${RL.opts.find(x=>x.key==='ap').other?` + short loans <b>${m(o.other)}</b>`:''} = <b>${m(o.fin)}</b>.`;}
  const dw=$('#drawwarn');""")
# Private: refer by key not index (index 2 still priv; keep) ; add fee line after pvplan table
rep("""<tbody id="pvplan"></tbody></table></div>${loansBlock('priv')}</div>`}""","""<tbody id="pvplan"></tbody></table></div><div class="feeline" id="pvfee"></div>${loansBlock('priv')}</div>`}""")
rep("""${F('Interest on drawn amount','ap.rate','p')}</div>${loansBlock('ap')}</div>""","""${F('Interest on drawn amount','ap.rate','p')}</div><div class="feeline" id="apfee"></div>${loansBlock('ap')}</div>""")
# ---- Builder: cp schedule card after Private card ----
old="""  <div class="card"><h2>Project profit before financing</h2><div class="scroll"><table><thead><tr><th>Line</th><th>Amount</th><th>Paid up front</th></tr></thead><tbody>"""
rep(old,"""  <div class="card"><h2>Draw schedule: Cash + Private</h2><p class="lead">Lot and early build in cash. Approved ${m(R.cp.approved)} (${pc(p.cp.ltv)} of ${p.cp.base==='build'?'build':'lot + build'}); fee ${pc(p.cp.fee)} on the approved amount = ${m(R.cp.fee)}. Drawn ${m(R.cp.drawn)}, not drawn ${m(R.cp.undrawn)}. Paid off when the sale closes.</p><div class="scroll"><table>
  <thead><tr><th>Draw</th><th>Amount</th><th>Taken at</th><th>Interest for</th><th>Interest</th></tr></thead><tbody>
  ${R.cpdraws.map((d,i)=>`<tr><td>Draw ${i+1}</td><td>${m(d.amt)}</td><td>month ${rnum(d.after)} of build</td><td>${mo(d.out)}</td><td>${m(d.int)}</td></tr>`).join('')||'<tr><td colspan="5">No draws</td></tr>'}
  <tr class="tot"><td>Draw interest</td><td>${m(R.cp.drawn)}</td><td></td><td></td><td>${m(R.cp.int)}</td></tr></tbody></table></div></div>
"""+old)
open(p,'w').write(s);print('ok')

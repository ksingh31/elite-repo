p='/home/claude/calc/index.html';s=open(p).read()
def rep(old,new,cnt=1):
    global s
    assert old in s,old[:100]
    s=s.replace(old,new,cnt)
SRC={'proj':'Projected','budget':'Budget estimate','inv':'Invoiced so far','manual':'Entered by hand'}
# ---- figures + resolve ----
rep("const resolveBudget=p=>{","""// Build cost figures for a budget version. proj = each line's budget, or its invoices if higher (finished lines use invoices), plus contingency on budget not yet invoiced.
const budFigs=(v,cont)=>{let est=0,inv=0,proj=0,left=0,over=0,overN=0;(v.items||[]).forEach(i=>{const a=+i.amt||0,x=+i.act||0;est+=a;inv+=x;if(x>a+0.005){over+=x-a;overN++;}
  if(i.done)proj+=x;else{proj+=Math.max(a,x);left+=Math.max(0,a-x);}});return {est,inv,proj:proj+left*(+cont||0),left,over,overN,cont:left*(+cont||0)};};
const SRCNAME={proj:'Projected',budget:'Budget estimate',inv:'Invoiced so far',manual:'Entered by hand'};
const budSrc=bl=>SRCNAME[bl&&bl.src]?bl.src:'budget';
const resolveBudget=p=>{""")
old_end="return {bud,v,total:vTotal(v),latest:v===latest};};"
rep(old_end,"""const f=budFigs(v,p.budget.cont),src=budSrc(p.budget),man=p.budget.manual;const total=src==='proj'?f.proj:src==='inv'?f.inv:src==='manual'?(man!=null&&man!==''&&!isNaN(man)?+man:f.proj):f.est;
  return {bud,v,total,figs:f,src,latest:v===latest};};""")
# ---- sheets builder resolve ----
rep("""    const L=b.versions[b.versions.length-1],v=bl.ver==='latest'?L:(b.versions.find(x=>x.id===bl.ver)||L);return {b,v,total:vTot(v)};};""",
"""    const L=b.versions[b.versions.length-1],v=bl.ver==='latest'?L:(b.versions.find(x=>x.id===bl.ver)||L);
    let est=0,inv=0,pj=0,left=0;v.items.forEach(i=>{const a=+i.amt||0,x=+i.act||0;est+=a;inv+=x;if(i.done)pj+=x;else{pj+=Math.max(a,x);left+=Math.max(0,a-x);}});pj+=left*(+bl.cont||0);
    const src=['proj','inv','manual'].includes(bl.src)?bl.src:'budget',man=bl.manual,total=src==='proj'?pj:src==='inv'?inv:src==='manual'?(man!=null&&man!==''&&!isNaN(man)?+man:pj):est;
    return {b,v,total,src:{proj:'projected',budget:'budget estimate',inv:'invoiced so far',manual:'entered by hand'}[src]};};""")
rep("r?txt(r.b.name+' · '+r.v.label):'Typed in'","r?txt(r.b.name+' · '+r.v.label+' · '+r.src):'Typed in'")
# ---- build field UI ----
a=s.index("function buildField(){");b=s.index("function budPick(",a)
s=s[:a]+r"""function buildField(){const p=P(),bl=p.budget,r=resolveBudget(p);
  const chk=`<label class="chk"><input type="checkbox" data-bl="use"${bl.use?' checked':''}> Use a budget for build cost</label>`;
  const typed=note=>`<div class="bcwrap">${F('Build cost','build','m')}${chk}</div>${note?`<div style="grid-column:1/-1">${note}</div>`:''}`;
  if(!bl.use||!r)return typed('');
  if(r.missing)return store.budgets.length?typed(`<div class="warn">Pick a budget below. Until then the typed build cost is used.</div>${budPick(p,true)}`)
    :typed(`<div class="warn">There are no budgets yet, so the typed build cost is used. <a href="#budget">Create a budget on the Budget tab</a>.</div>`);
  const f=r.figs,src=r.src,card=(k,title,amt,desc,extra)=>`<label class="opt${src===k?' on':''}"><input type="radio" name="bcsrc" data-radio="budget.src" value="${k}"${src===k?' checked':''}><span><b>${title}</b>${amt!=null?`<span class="amt">${m0(amt)}</span>`:''}<small>${desc}</small>${extra||''}</span></label>`;
  return `<div class="bcwrap"><div class="f"><span>Build cost</span><div class="in ro" aria-live="polite"><b id="c-bud">${m(r.total)}</b><small>${esc(SRCNAME[src])}</small></div></div>${chk}</div>
  <div class="bcpanel" style="grid-column:1/-1"><h3>Build cost from budget <span class="lbl">sets the Build cost above</span></h3>
    ${budPick(p)}
    <p class="note" style="margin:8px 0 6px">Which number should this project use? <span id="c-budv" hidden></span></p>
    <div class="choice bcsrc">
      ${card('proj','Projected <span class="tag rec">Recommended</span>',f.proj,'Each line uses its budget, or its invoices if they are higher. Lines marked finished use their invoices.')}
      ${card('budget','Budget estimate',f.est,'The budget amounts in '+esc(r.v.label)+', ignoring invoices.')}
      ${card('inv','Invoiced so far',f.inv,'Invoices only. Best once the build is finished.')}
      ${card('manual','Enter by hand',null,'Your own number.',src==='manual'?`<span class="in m bcman" data-u=""><input data-p="budget.manual" data-t="m" inputmode="decimal" aria-label="Build cost entered by hand" value="${esc(bl.manual==null?'':show(bl.manual,'m'))}" placeholder="${esc(Math.round(f.proj))}"></span>`:'')}
    </div>
    ${src==='proj'?`<div class="fields" style="margin-top:10px">${F('Contingency on budget not yet invoiced','budget.cont','p',{hint:`Adds a cushion on the ${m0(f.left)} of budget still to be invoiced${f.cont?': +'+m0(f.cont):''}`})}</div>`:''}
    ${f.inv>f.est+0.5?`<div class="warn" style="margin-top:10px">Invoices (${m0(f.inv)}) are already ${m0(f.inv-f.est)} over the budget estimate (${m0(f.est)}). ${f.overN} line${f.overN===1?' is':'s are'} over budget.${src==='budget'?' Consider Projected so the build cost reflects this.':''}</div>`:''}
    <p class="note" style="margin-top:8px">To change the numbers, edit the budget or mark lines finished on the Budget page (<a href="#budget" data-act="b-open">open budget</a>), or untick the box to type a build cost.</p></div>`;}
"""+s[b:]
# move lot price to next line: break after Sell price
rep("${F('Project name','name','t')}${F('Sell price (incl. GST)','sell','m')}${F('Lot price','lot','m')}${buildField()}",
    "${F('Project name','name','t')}${F('Sell price (incl. GST)','sell','m')}<div class=\"brk\" aria-hidden=\"true\"></div>${F('Lot price','lot','m')}${buildField()}")
# turning on a budget / linking defaults to projected
rep("if(k==='use'){if(t.checked){bl.use=true;","if(k==='use'){if(t.checked){bl.use=true;bl.src='proj';")
rep("p.budget={use:true,id:bud.id,ver:'latest'};","p.budget={use:true,id:bud.id,ver:'latest',src:'proj'};")
# refreshForm c-bud: keep text (already rendered); make it show total
rep("q('c-bud',m(r.total));q('c-budv',r.v.label+(P().budget.ver==='latest'?' (latest)':' (pinned)'));","q('c-bud',m(r.total));")
# used-by table: show source
rep("</select></span></td><td>${m(r.total)}</td><td><button class=\"ghost\" style=\"min-height:36px\" data-act=\"b-unlink\"",
    "</select></span></td><td>${m(r.total)}<small style=\"display:block;color:var(--mute)\">${esc(SRCNAME[r.src])}</small></td><td><button class=\"ghost\" style=\"min-height:36px\" data-act=\"b-unlink\"")
# budget page tile
rep("""    <div class="tile"><div class="lbl">Still owed on invoices</div><div class="v">${m0(Math.max(0,TA-TP))}</div></div></div>""",
"""    <div class="tile"><div class="lbl">Still owed on invoices</div><div class="v">${m0(Math.max(0,TA-TP))}</div></div>
    <div class="tile"><div class="lbl">Projected final cost <span title="Each line: budget, or invoices if higher. Finished lines use invoices.">ⓘ</span></div><div class="v">${m0(budFigs(v,0).proj)}</div></div></div>""")
# finished tick under actual cell
rep("""<small>${i.invs.length} invoice${i.invs.length>1?'s':''}</small></button>`:inp('item:'+i.id+':act',ac,1)}""",
    """<small>${i.invs.length} invoice${i.invs.length>1?'s':''}</small></button>`:inp('item:'+i.id+':act',ac,1)}${ed?`<label class="donechk"><input type="checkbox" data-done="${esc(i.id)}"${i.done?' checked':''}> Finished</label>`:(i.done?'<small class="lbl">Finished</small>':'')}""")
# change handler for data-done
rep("  if(t.dataset.bl){const bl=P().budget,k=t.dataset.bl;","""  if(t.dataset.done){const b0=curBud(),v0=b0&&(b0.versions.find(x=>x.id===bview)||b0.versions[b0.versions.length-1]),it=v0&&v0.items.find(x=>x.id===t.dataset.done);if(it){it.done=t.checked;persist();renderBudget();refresh();status(it.name+(t.checked?' marked finished: Projected cost now uses its invoices.':' is no longer marked finished.'));}return;}
  if(t.dataset.bl){const bl=P().budget,k=t.dataset.bl;""")
# css
rep("</style></head>",""".brk{grid-column:1/-1;height:0;margin:0;padding:0}
.bcwrap{display:flex;flex-direction:column;gap:2px;min-width:0}.bcwrap .chk{min-height:36px}
.in.ro{display:flex;align-items:baseline;justify-content:space-between;gap:8px;background:var(--bg);cursor:default}.in.ro b{font-variant-numeric:tabular-nums;font-size:16px}.in.ro small{color:var(--teal);font-weight:700;font-size:12px}
.bcpanel{border:1px solid var(--line);border-left:4px solid var(--teal);border-radius:12px;padding:14px 16px;margin-top:2px}.bcpanel h3{margin:0 0 4px;display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}.bcpanel h3 .lbl{font-weight:500}
.bcsrc .opt .amt{display:block;font-size:17px;font-weight:800;font-variant-numeric:tabular-nums;margin:2px 0}.tag.rec{background:#d8efe9;color:#0b4f48;margin-left:4px}
.bcman{margin-top:6px;max-width:220px}.donechk{display:flex;gap:6px;align-items:center;justify-content:flex-end;font-size:12px;color:var(--mute);margin-top:4px;cursor:pointer}.donechk input{accent-color:var(--teal);width:16px;height:16px}
</style></head>""")
open(p,'w').write(s);print('ok')

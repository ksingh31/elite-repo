p='/home/claude/calc/index.html';s=open(p).read()
a=s.index("function renderLive(){");b=s.index("function renderBuilder(){",a)
new=r"""function renderLive(){const s=R.sel,sum=x=>lo(x)+hi(x)!==0,sub=(l,v)=>`<div class="kv sub"><span>${l}</span><b>${m0(neg(v))}</b></div>`;
  $('#live').innerHTML=`<div class="sec"><div class="lbl">Profit before financing</div><div class="big">${m0(R.profit0)}</div>
  <div class="kv"><span>Investor return</span><b>${pc(R.rate0)}</b></div><div class="kv"><span>Investor return, annualized</span><b>${R.annInv==null?'n/a':pc(R.annInv)}</b></div><div class="kv"><span>Project cost</span><b>${m0(R.base)}</b></div>
  <div class="kv"><span>Investor cash</span><b>${m0(R.invCash)}</b></div><div class="kv"><span>Investor earnings</span><b>${m0(R.invEarn)}</b></div></div>
  <div class="selbox"><div class="selhd"><span>After financing</span><b>${esc(s.name)}</b></div>
    <div class="lbl">Profit after financing</div><div class="big${hi(s.profit)<0?' neg':''}">${m0(s.profit)}</div>
    <div class="kv"><span>Profit before financing</span><b>${m0(R.profit0)}</b></div>
    ${sum(s.fee)?sub('Lender fees',s.fee):''}${sum(s.interest)?sub('Interest',s.interest):''}${sum(s.other)?sub('Short private loans',s.other):''}
    <div class="kv tot"><span>Financing cost</span><b>${m0(neg(s.fin))}</b></div>
    <div class="kv"><span>Cash needed</span><b>${m0(s.cash)}</b></div>
    <div class="kv"><span>ROI on cash</span><b>${pc(s.roi)}</b></div>
    <div class="kv"><span>ROI, annualized</span><b>${s.annRoi==null?'n/a':pc(s.annRoi)}</b></div></div>
  <div class="selbox co"><div class="selhd"><span>Builder (EliteCraft)</span><b>${esc(s.name)}</b></div>
    <div class="lbl">Builder earnings</div><div class="big${hi(R.coNet)<0?' neg':''}">${m0(R.coNet)}</div>
    <div class="kv"><span>Profit after financing</span><b>${m0(s.profit)}</b></div>
    ${R.inv.length?sub('Paid to investors',R.invEarn):''}
    <div class="kv"><span>Builder cash in</span><b>${m0(R.coCash)}</b></div>
    <div class="kv"><span>Return on builder cash</span><b>${R.coRoi==null?'n/a':pc(R.coRoi)}</b></div>
    <div class="kv"><span>Return, annualized</span><b>${R.coAnn==null?'n/a':pc(R.coAnn)}</b></div></div>
  <h3>Compare financing</h3><p class="note" style="margin:0 0 6px">Click one to switch.</p><div class="cmp">
  ${R.opts.map(x=>`<button type="button" class="crow${x===s?' on':''}" data-pick="${x.key}" aria-pressed="${x===s}"><span>${esc(x.name)}</span><span>${m0(x.profit)}</span><span>${pc(x.roi)}</span></button>`).join('')}</div>`;}

"""
s=s[:a]+new+s[b:]
s=s.replace("</style></head>",""".live .sec{margin-bottom:6px}
.selbox{margin:14px 0 4px;padding:14px;border-radius:12px;background:light-dark(#e8f4f2,#10302d);border:1px solid light-dark(#a9d3cf,#245650)}
.selbox.co{background:light-dark(#eef2f7,#16243a);border-color:light-dark(#c4d0de,#2c4060)}
.selhd{display:flex;justify-content:space-between;gap:8px;align-items:baseline;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--mute);margin-bottom:6px}.selhd b{text-transform:none;letter-spacing:0;font-size:14px;color:var(--ink);text-align:right}
.selbox .big{font-size:clamp(26px,3.2vw,34px)}.selbox .big.neg{color:#b42318}
.selbox .kv{border-color:light-dark(rgba(0,0,0,.08),rgba(255,255,255,.1))}.kv.sub span{padding-left:12px;color:var(--mute)}.kv.tot{font-weight:700}
.cmp{display:grid;gap:4px}.crow{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr) minmax(0,.7fr);gap:8px;align-items:center;width:100%;padding:8px 10px;border-radius:8px;border:1px solid transparent;background:none;color:var(--ink);font:inherit;font-size:14px;text-align:left;cursor:pointer;min-height:40px}
.crow span:not(:first-child){text-align:right;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}.crow:hover{background:var(--bg)}.crow.on{background:light-dark(#e8f4f2,#10302d);border-color:var(--teal);font-weight:700;color:var(--teal)}
</style></head>""",1)
# click handler for data-pick
old="try{window.__dbg={calc,effP,P};}catch(_){}"
s=s.replace(old,"""document.addEventListener('click',e=>{const t=e.target.closest('[data-pick]');if(!t)return;if(P().use===t.dataset.pick)return;P().use=t.dataset.pick;persist();buildForm();refresh();});
"""+old,1)
open(p,'w').write(s);print('ok')

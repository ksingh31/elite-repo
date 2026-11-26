h=open('/home/claude/calc/index.html').read()
def rep(a,b,cnt=1):
    global h
    assert h.count(a)==cnt,(a[:70],h.count(a)); h=h.replace(a,b)
rep("const B=[],IT=[],PAY=[],cur=[];","const B=[],IT=[],PAY=[],IV=[],cur=[];")
rep("""        (i.pays||[]).forEach(py=>PAY.push([txt(b.name),txt(v.label),txt(c),txt(i.name),py.date||'',py.method||'',n(py.amt),txt(py.ref||'')]));}));});});""",
"""        const ivs=i.invs||[],lab=iv=>iv?[iv.vendor||'',iv.no?'#'+iv.no:''].filter(Boolean).join(' · '):'';
        ivs.forEach(iv=>{const q2=IV.length+2,pd=(i.pays||[]).reduce((t,p)=>t+(p.inv===iv.id?n(p.amt):0),0);
          IV.push([txt(b.name),txt(v.label),txt(c),txt(i.name),txt(iv.vendor||''),(/^[\\d.\\-\\/ ]+$/.test(iv.no||'')?"'"+iv.no:txt(iv.no||'')),iv.date||'',iv.kind||'Other',n(iv.amt),Math.round(pd*100)/100,'=I'+q2+'-J'+q2]);});
        (i.pays||[]).forEach(py=>PAY.push([txt(b.name),txt(v.label),txt(c),txt(i.name),py.date||'',py.method||'',n(py.amt),txt(py.ref||''),txt(lab(ivs.find(x=>x.id===py.inv)))]));}));});});""")
rep("projects:P,investors:INV,budgets:B,items:IT,payments:PAY,","projects:P,investors:INV,budgets:B,items:IT,payments:PAY,invoices:IV,")
open('/home/claude/calc/index.html','w').write(h)
s=h.index('/*BACKUP*/');e=h.index('/*ENDBACKUP*/')+len('/*ENDBACKUP*/')
open('/home/claude/backup/backupfn.js','w').write(h[s:e]+'\n');print('backup ok')

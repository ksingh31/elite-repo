import difflib,json,re
import sys;old=open(sys.argv[1] if len(sys.argv)>1 else 'index.preswap.html').read();new=open(sys.argv[2] if len(sys.argv)>2 else 'index.html').read()
def strip(s):
    m=re.search(r'(<script id="store" type="application/json">)([\s\S]*?)(</script>)',s);return s[:m.start(2)]+'@@STORE@@'+s[m.end(2):]
o=strip(old);n=strip(new)
ol=o.splitlines(True);nl=n.splitlines(True)
sm=difflib.SequenceMatcher(None,ol,nl,autojunk=False)
# char offsets
oo=[0];[oo.append(oo[-1]+len(x)) for x in ol]
no=[0];[no.append(no[-1]+len(x)) for x in nl]
edits=[]
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal':continue
    a,b=oo[i1],oo[i2];c,d=no[j1],no[j2]
    # trim common prefix/suffix inside the changed block
    while a<b and c<d and o[a]==n[c]:a+=1;c+=1
    while a<b and c<d and o[b-1]==n[d-1]:b-=1;d-=1
    pad=40
    while True:
        s0=max(0,a-pad);e0=min(len(o),b+pad)
        if o.count(o[s0:e0])==1:break
        pad+=40
    edits.append([s0,e0,a,b,c,d])
# merge overlapping windows
edits.sort();m=[]
for e in edits:
    if m and e[0]<=m[-1][1]:
        p=m[-1];m[-1]=[p[0],max(p[1],e[1]),p[2],e[3],p[4],e[5]]
    else:m.append(e)
out=[]
for s0,e0,a,b,c,d in m:
    ot=o[s0:e0];nt=o[s0:a]+n[c:d]+o[b:e0];out.append({'old_text':ot,'new_text':nt})
t=o
for e in out:
    assert t.count(e['old_text'])==1;t=t.replace(e['old_text'],e['new_text'])
print(len(out),'edits', 'ok' if t==n else 'MISMATCH', sum(len(e['old_text']) for e in out), sum(len(e['new_text']) for e in out))
json.dump(out,open('/tmp/edits.json','w'))

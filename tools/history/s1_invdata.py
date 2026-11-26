import json,re,csv,io
h=open('/home/claude/calc/index.html').read()
m=re.search(r'(<script id="store" type="application/json">)(.*?)(</script>)',h,re.S)
st=json.loads(m.group(2)); items=st['budgets'][0]['versions'][0]['items']; N={i['name']:i for i in items}
txt=open('/mnt/user-data/uploads/a14eadf8-Updated_Invoices_2631').read()
secs={}
for part in txt.split('## Sheet name: ')[1:]:
    name,body=part.split('\n',1); secs[name.strip()]=list(csv.reader(io.StringIO(body)))
chk=json.load(open('/home/claude/backup/check_out.json'))[1:]
MI={'Trade':7,'Fixed expenses':7,'Supplier':7,'Documentation':7,'Miscelenous':6,'Supplier B':6,'Coffee':4}
def method(mode,amt):
    if amt<0: return 'Refund / credit'
    u=(mode or '').upper()
    if 'CHQ' in u or 'CHEQUE' in u or 'CHECK' in u: return 'Cheque'
    if 'VISA' in u: return 'Visa'
    if 'MASTER' in u: return 'Mastercard'
    if 'AMEX' in u: return 'Amex'
    if 'DEBIT' in u: return 'Debit'
    if 'CASH' in u: return 'Cash'
    if any(k in u for k in ('TRANSFER','TARNSFER','ETF','E-T','INTERAC')): return 'E-transfer'
    return 'Not recorded'
MAT={'hardware store a','hardware store b','online store','supplier c','supplier d'}  # real store names removed
def kind(tab,vendor):
    v=vendor.lower().strip()
    if 'wages' in v: return 'Trade'
    if tab=='Trade': return 'Trade'
    if tab in('Supplier','Supplier B'): return 'Material'
    if tab in('Fixed expenses','Documentation'): return 'Service'
    if tab=='Miscelenous': return 'Material' if v in MAT else ('Service' if v=='leap express cargo ltd' else 'Other')
    return 'Other'
old={i['name']:(round(i['act'],2),round(sum(p['amt'] for p in i['pays']),2)) for i in items}
for i in items: i['invs']=[]; i['pays']=[]
n=[0]
def uid(p): n[0]+=1; return f'{p}{n[0]:04d}'
for s,item,cat,tab,row,vendor,no,date,tot,pd,note in chk:
    it=N[item]; src=secs[tab][row-1]
    mode=src[MI[tab]].strip() if len(src)>MI[tab] else ''
    no=no.lstrip("'"); iv=None
    if tot!=0:
        iv={'id':uid('v'),'vendor':vendor,'no':no,'date':date,'kind':kind(tab,vendor),'amt':tot,'note':note}
        it['invs'].append(iv)
    if pd!=0:
        ref=' · '.join(x for x in [vendor if not iv else '', ('Inv '+no) if no and not iv else '', mode] if x)
        it['pays'].append({'id':uid('p'),'date':date,'method':method(mode,pd),'amt':pd,'ref':ref,'inv':iv['id'] if iv else None})
bad=[]
for i in items:
    a=round(sum(v['amt'] for v in i['invs']),2); p=round(sum(x['amt'] for x in i['pays']),2)
    if i['invs']: i['act']=a
    if (a,p)!=old[i['name']] and not (not i['invs'] and p==old[i['name']][1]): bad.append((i['name'],old[i['name']],(a,p)))
print('mismatch',bad,'invoices',sum(len(i['invs']) for i in items),'payments',sum(len(i['pays']) for i in items))
st['savedAt']='2026-11-26T05:30:00.000Z'
h=h[:m.start(2)]+json.dumps(st,separators=(',',':'),ensure_ascii=False).replace('</','<\\/')+h[m.end(2):]
open('/home/claude/calc/index.html','w').write(h)

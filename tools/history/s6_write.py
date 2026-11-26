h=open('/home/claude/calc/index.html').read()
s=h.index('async function writeBackup(source,data){');e=h.index('async function backupNow(){')
h=h[:s]+r'''async function writeBackup(source,data){
  const info=await sheetCall('get_spreadsheet',{fields:['sheets.properties.sheetId','sheets.properties.title']});
  const pl=info&&info.payload,shs=(pl&&(pl.sheets||(pl.content&&pl.content.sheets)))||[];
  const ex=shs.map(s=>s.properties||s).filter(p=>p&&p.title!=null);
  if(!ex.length)throw {code:'Could not read the backup sheet’s tabs'};
  const plan=buildSheets(data,calc,source,edmNow(),ex);
  await sheetCall('update_spreadsheet',{requests:plan.structure});
  for(const t of plan.perTab){const w=t.values[0]?t.values[0].length:1,q="'"+t.title.replace(/'/g,"''")+"'!";
    for(let r=0;r<t.values.length;r+=250){const part=t.values.slice(r,r+250);await sheetCall('update_values',{range:q+'A'+(r+1)+':'+colL(w)+(r+part.length),values:part});}
    for(let k=0;k<t.requests.length;k+=400)await sheetCall('update_spreadsheet',{requests:t.requests.slice(k,k+400)});}
  await sheetCall('append_values',{range:"'Backup data'!A1",values:plan.data});
  await sheetCall('append_values',{range:"'Backup log'!A1",values:plan.log});
  return plan.head;}
'''+h[e:]
h=h.replace('.ptable tr.hl td{background:#fff7e6}','.ptable tr.hl td{background:#fff7e6}.itable tr.irow td{border-top:2px solid rgba(20,38,61,.18);background:#f3f7f6}.itable tr.prow td{font-size:13px;padding-top:4px;padding-bottom:4px}.itable tr.prow td:first-child{border-left:3px solid #0d7a75}.itable td.none{color:var(--mute);text-align:left;font-style:italic}',1)
open('/home/claude/calc/index.html','w').write(h);print('write ok')

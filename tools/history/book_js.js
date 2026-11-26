const BACKUP_FOLDER='YOUR_BACKUP_FOLDER_ID',FOLDER_URL='https://drive.google.com/drive/folders/'+BACKUP_FOLDER;
const sheetUrl=id=>'https://docs.google.com/spreadsheets/d/'+id+'/edit';
const tabsOf=r=>{const pl=r&&r.payload,shs=(pl&&(pl.sheets||(pl.content&&pl.content.sheets)))||[];return shs.map(s=>s.properties||s).filter(p=>p&&p.title!=null);};
async function sheetsCall(tool,input){const go=()=>mcp.callTool('Google Sheets',tool,input);try{return await go();}catch(e){const c=String(e&&(e.code||e.message)||'');if(/server_not_connected|needs_reauth|denied|not_granted|consent/.test(c))throw e;await new Promise(r=>setTimeout(r,1500));return go();}}
async function writePlan(id,plan){
  if(plan.structure.length)await sheetsCall('update_spreadsheet',{spreadsheetId:id,requests:plan.structure});
  for(const t of plan.perTab){const w=t.values[0]?t.values[0].length:1,q="'"+t.title.replace(/'/g,"''")+"'!";
    for(let r=0;r<t.values.length;r+=250){const part=t.values.slice(r,r+250);await sheetsCall('update_values',{spreadsheetId:id,range:q+'A'+(r+1)+':'+colL(w)+(r+part.length),values:part});}
    for(let k=0;k<t.requests.length;k+=400)await sheetsCall('update_spreadsheet',{spreadsheetId:id,requests:t.requests.slice(k,k+400)});}}
// find or create the Google Sheet for a budget; remembers it in the budget (b.sheetId)
async function sheetFor(b){if(b.sheetId)return {id:b.sheetId,isNew:false};
  const title=b.name+' – backup';
  try{const r=await mcp.callTool('Google Drive','search_files',{query:"parentId = '"+BACKUP_FOLDER+"' and title = '"+String(title).replace(/'/g,"\\'")+"' and trashed = false",pageSize:5,excludeContentSnippets:true});
    const p=r&&r.payload,fs=(p&&(p.files||(p.content&&p.content.files)))||[];if(fs[0]&&fs[0].id)return {id:String(fs[0].id),isNew:true};}catch(_){}
  let drive;try{drive=await mcp.callTool('Google Drive','create_file',{title,contentMimeType:'application/vnd.google-apps.spreadsheet',parentId:BACKUP_FOLDER});}
  catch(e){throw {code:'Could not create a sheet for '+b.name+' ('+String(e&&(e.code||e.message)||'')+'). Is the Google Drive connector on?'};}
  const p=drive&&drive.payload,id=p&&(p.id||(p.content&&p.content.id));if(!id)throw {code:'Google Drive did not return a sheet for '+b.name};return {id:String(id),isNew:true};}
async function writeBackup(source,data){
  const when=edmNow();let created=0,head='';
  const list=(data.budgets||[]).filter(b=>b.versions&&b.versions.length);
  if(!list.length)throw {code:'There is no budget to back up yet'};
  for(const b of list){const f=await sheetFor(b);if(f.isNew||b.sheetId!==f.id){b.sheetId=f.id;created++;}
    const ex=tabsOf(await sheetsCall('get_spreadsheet',{spreadsheetId:f.id,fields:['sheets.properties.sheetId','sheets.properties.title']}));
    const plan=buildSheets(data,calc,source,when,ex,{budget:b.id});
    await writePlan(f.id,plan);
    const cv=vals(await sheetsCall('get_values',{spreadsheetId:f.id,range:"'Summary'!A2"}));
    if(!String((cv[0]||[])[0]||'').includes(when))throw {code:'The '+b.name+' sheet didn’t keep the new data. Try Back up now again'};
    await sheetsCall('append_values',{spreadsheetId:f.id,range:"'Backup data'!A1",values:plan.data});
    await sheetsCall('append_values',{spreadsheetId:f.id,range:"'Backup log'!A1",values:plan.log});head=plan.head;}
  if(created&&data===store)persist();
  return head+(created?'. A new sheet was made for '+created+' budget'+(created>1?'s':'')+'; click Save for team so the calculator remembers it':'');}
function bkBudget(){return (store.budgets||[]).find(b=>b.id===$('#bkbud').value);}
function bkUpdate(){const b=bkBudget(),a=$('#bklink');
  if(b&&b.sheetId){a.href=sheetUrl(b.sheetId);a.removeAttribute('aria-disabled');a.classList.remove('off');a.textContent='Open '+b.name+' sheet';}
  else{a.removeAttribute('href');a.setAttribute('aria-disabled','true');a.classList.add('off');a.textContent='No sheet yet: click Back up now';}
  $('#syncgo').disabled=!(b&&b.sheetId);$('#syncres').innerHTML='';listBackups();}
async function backupNow(){const msg=$('#bkmsg');msg.textContent='Backing up every budget…';
  try{const h=await writeBackup('Back up now',store);msg.textContent='Done. '+h+'.'+(dirty?' This includes your unsaved changes.':'');status('Backed up to Google Sheets.');bkUpdate();updSheetLink();}
  catch(e){msg.textContent=bkErr(e);status('Backup failed.','warn');}}
async function listBackups(){const el=$('#bklist'),b=bkBudget();
  if(!mcp||!b||!b.sheetId){el.textContent='';return;}
  el.textContent='Loading restore points…';
  try{const v=vals(await sheetsCall('get_values',{spreadsheetId:b.sheetId,range:"'Backup data'!A2:C"}));
    bkRows=v.map((x,k)=>({row:k+2,when:String(x[0]||''),source:String(x[1]||''),sid:b.sheetId})).filter(x=>x.when).reverse().slice(0,30);
    if(!bkRows.length){el.textContent='No restore points in this sheet yet.';return;}
    el.innerHTML='<h3 style="margin:14px 0 6px">Restore points</h3><p class="note" style="margin:0 0 8px">Each one is a full copy of the calculator (all budgets and projects) taken at that time.</p><table><thead><tr><th>When (Edmonton time)</th><th>What triggered it</th><th></th></tr></thead><tbody>'+bkRows.map(x=>'<tr data-row="'+x.row+'"><td>'+esc(x.when)+'</td><td>'+esc(x.source)+'</td><td class="r"><button class="btn" data-act="bk-load">Load this backup</button></td></tr>').join('')+'</tbody></table>';}
  catch(e){el.textContent=bkErr(e);}}
function openBackups(budgetId){const sel=$('#bkbud');const L=store.budgets||[];
  sel.innerHTML=L.map(b=>`<option value="${esc(b.id)}">${esc(b.name)}</option>`).join('')||'<option value="">No budgets yet</option>';
  sel.value=budgetId||store.curBudget||(L[0]&&L[0].id)||'';
  $('#bkmsg').textContent=mcp?'':bkErr({code:'unavailable'});$('#bkmodal').hidden=false;bkUpdate();}
async function loadBackup(row){const x=bkRows.find(r=>r.row===row);if(!x)return;
  const go=async()=>{$('#bkmodal').hidden=false;$('#bkmsg').textContent='Loading the backup from '+x.when+'…';
    try{const v=vals(await sheetsCall('get_values',{spreadsheetId:x.sid,range:"'Backup data'!A"+row+':L'+row}))[0]||[];
      const n=+v[2]||0,parts=v.slice(3,3+n).map(String);let d;
      try{d=JSON.parse(parts.join(''));}catch(_){d=JSON.parse(parts.map(p=>p.replace(/^'/,'')).join(''));}
      if(d.v!==4||!Array.isArray(d.projects))throw {msg:'This backup isn’t in a format this calculator reads.'};
      const ids={};(store.budgets||[]).forEach(b=>{if(b.sheetId)ids[b.id]=b.sheetId;});(d.budgets||[]).forEach(b=>{if(!b.sheetId&&ids[b.id])b.sheetId=ids[b.id];});
      d.savedAt=store.savedAt;store=migrate(d);if(!store.projects.some(p=>p.id===store.cur))store.cur=store.projects[0].id;
      persist();buildForm();try{renderBudget();refresh();}catch(_){}
      $('#bkmodal').hidden=true;status('Loaded the backup from '+x.when+'. Check it, then click Save for team to keep it, or Discard changes.');}
    catch(e){$('#bkmsg').textContent=e&&e.msg?e.msg:(e instanceof SyntaxError?'This backup’s data is damaged and can’t be read.':bkErr(e));}};
  if(dirty){$('#bkmodal').hidden=true;guard(go,{what:'loading a backup'});}else go();}
function updSheetLink(){const a=$('#bsheet');if(!a)return;const b=(store.budgets||[]).find(x=>x.id===store.curBudget);
  if(b&&b.sheetId){a.href=sheetUrl(b.sheetId);a.hidden=false;}else a.hidden=true;}

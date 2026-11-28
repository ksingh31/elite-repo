try{localStorage.setItem('ec-cats','open');}catch(_){}
// window.claude mock used by every Playwright suite: artifact.publish counts publishes, downloads.save is a no-op,
// mcp.callTool emulates the Google Sheets / Drive connectors in memory (window.__books, window.__cells).
window.__calls=[];window.__pub=0;window.__cells={};window.__books={};window.__found={};
const book=id=>window.__books[id]||(window.__books[id]={tabs:[{sheetId:0,title:'Sheet1'}],data:[],log:[]});
const mcp={callTool:async(s,t,i)=>{window.__calls.push([s,t,i]);
  if(s==='Google Drive'&&t==='search_files'){const m=i.query.match(/title = '(.*)' and trashed/);const id=m&&window.__found[m[1].replace(/\\'/g,"'")];return {payload:{files:id?[{id}]:[]}};}
  if(s==='Google Drive'&&t==='create_file'){const id='NEWFILE'+window.__calls.length;book(id);return {payload:{id}};}
  const B=book(i.spreadsheetId||'');
  if(t==='update_spreadsheet'){const T=JSON.parse(JSON.stringify(B.tabs)),C=Object.assign({},window.__cells);const pre=(i.spreadsheetId||'')+'|';
    for(const r of (i.requests||[])){
      if(r.addSheet){const p=r.addSheet.properties;if(T.some(z=>z.sheetId===p.sheetId||z.title===p.title))throw {code:'tool_error',message:'duplicate sheet '+p.sheetId};T.push(Object.assign({},p));}
      if(r.deleteSheet){const x=T.find(z=>z.sheetId===r.deleteSheet.sheetId);if(!x)throw {code:'tool_error',message:'No sheet with id: '+r.deleteSheet.sheetId};T.splice(T.indexOf(x),1);Object.keys(C).forEach(k=>{if(k.startsWith(pre+"'"+x.title+"'|"))delete C[k];});}
      if(r.updateSheetProperties){const p=r.updateSheetProperties.properties;const x=T.find(z=>z.sheetId===p.sheetId);if(!x)throw {code:'tool_error',message:'No sheet with id: '+p.sheetId};
        if(p.title!=null&&p.title!==x.title){Object.keys(C).forEach(k=>{if(k.startsWith(pre+"'"+x.title+"'|")){C[k.replace(pre+"'"+x.title+"'|",pre+"'"+p.title+"'|")]=C[k];delete C[k];}});x.title=p.title;}
        if(p.hidden!=null)x.hidden=p.hidden;}
      ['repeatCell','updateBorders','updateDimensionProperties','setBasicFilter','addConditionalFormatRule'].forEach(k=>{if(r[k]){const ids=[];JSON.stringify(r[k],(kk,v)=>{if(kk==='sheetId')ids.push(v);return v;});ids.forEach(id=>{if(!T.some(z=>z.sheetId===id))throw {code:'tool_error',message:'No grid with id: '+id};});}});}
    if(window.__failOn&&i.requests.some(window.__failOn))throw {code:'tool_error',message:'Invalid requests[0]: simulated failure'};
    B.tabs=T;window.__cells=C;return {payload:{}};}
  if(t==='append_values'){if(i.range.includes('Backup data'))B.data.push(...i.values);else B.log.push(...i.values);return {payload:{}};}
  if(t==='update_values'){const m=i.range.match(/^(.*)!A(\d+):/);if(m)i.values.forEach((r,k)=>{window.__cells[(i.spreadsheetId||'')+'|'+m[1]+'|'+(+m[2]+k)]=r;});return {payload:{}};}
  if(t==='get_spreadsheet')return {payload:{sheets:B.tabs.map(p=>({properties:p}))}};
  if(t==='get_values'){
    {const m=i.range.match(/^('.*')!A(\d+)$/);if(m){const r=window.__cells[(i.spreadsheetId||'')+'|'+m[1]+'|'+m[2]];return {payload:{values:r?[r]:[]}};}}
    if(/Backup data'!A1:C$/.test(i.range))return {payload:{values:[['When','What triggered it','Parts'],...B.data.map(r=>r.slice(0,3))]}};
    if(/Backup data'!A2:C$/.test(i.range))return {payload:{values:B.data.map(r=>r.slice(0,3))}};
    const m=i.range.match(/Backup data'!A(\d+):L/);if(m)return {payload:{values:[B.data[+m[1]-2]]}};
    if(/Backup log'!A1:G$/.test(i.range))return {payload:{values:B.log}};return {payload:{values:[]}};}
  return {payload:{}};}};
window.claude={use:n=>Promise.resolve(n==='mcp'?mcp:n==='artifact'?{publish:async h=>{await new Promise(r=>setTimeout(r,window.__pubDelay||0));window.__pub++;window.__html=h;}}:n==='downloads'?{save:async()=>{}}:null)};

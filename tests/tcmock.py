import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *
import json
ROWS=json.load(open(os.path.join(HERE,'fixtures','tc_rows.json')))

TCI=INIT+r'''
window.__tcRows=%s;window.__tcKL={};window.__tcW=[];window.__tcGets=0;
{const _use=window.claude.use;window.claude.use=n=>_use(n).then(x=>{if(n!=='mcp'||window.__noMcp)return n==='mcp'&&window.__noMcp?Promise.reject({code:'unavailable'}):x;return {callTool:async(s,t,i)=>{
  const r=i&&i.range||'';
  if(s==='Google Sheets'&&r.startsWith("'To check'")){
    if(t==='get_values'){window.__tcGets++;if(window.__tcFailRead)throw {code:'tool_error',message:window.__tcFailRead};
      return {payload:{values:window.__tcRows.map((row,k)=>{const kl=window.__tcKL[3+k];const out=row.slice();if(kl){while(out.length<10)out.push('');out.push(kl[0],kl[1]);}return out;})}};}
    if(t==='update_values'){window.__tcW.push({id:i.spreadsheetId,range:r,values:i.values});if(window.__tcFailWrite)throw {code:'tool_error',message:'simulated write failure'};
      const m=r.match(/K(\d+):L/);window.__tcKL[+m[1]]=i.values[0];return {payload:{}};}
  }
  return x.callTool(s,t,i);}};});}
'''%json.dumps(ROWS)

/*SHEETS*/
function buildSheets(store,calc,source,when,existing,opt,files){
  opt=opt||{main:true};files=files||{};
  const bk=buildBackup(store,calc,source,when);
  const n=x=>+x||0,r2=x=>Math.round(n(x)*100)/100;
  const KINDS=['Trade','Material','Service','Other'];
  const METHODS=['Cheque','E-transfer','Visa','Mastercard','Amex','Debit','Cash','Refund / credit','Other','Not recorded'];
  const NAVY={red:0.078,green:0.149,blue:0.239},TEAL={red:0.051,green:0.478,blue:0.459},TEAL_L={red:0.886,green:0.941,blue:0.937},
    MUTE={red:0.42,green:0.46,blue:0.52},WHITE={red:1,green:1,blue:1},RED={red:0.64,green:0.29,blue:0.03},GREEN={red:0.05,green:0.42,blue:0.32};
  const MONEY='$#,##0.00;-$#,##0.00;"-"',PCT='0.0%;-0.0%;"-"';
  const unq=v=>typeof v==='string'&&v[0]==="'"&&/^[=+\-@]/.test(v.slice(1))?v.slice(1):v;
  const used=new Set(['read me','summary','projects','investors','to check','category check','backup log','backup data']);
  const safeTitle=s=>{let t=String(s||'Budget').replace(/[\[\]\*\?\/\\:]/g,' ').replace(/\s+/g,' ').trim().slice(0,90)||'Budget';let u=t,k=2;while(used.has(u.toLowerCase()))u=t+' ('+(k++)+')';used.add(u.toLowerCase());return u;};
  const latest=b=>b.versions[b.versions.length-1];
  const usedBy=b=>(store.projects||[]).filter(p=>p.budget&&p.budget.use&&p.budget.id===b.id).map(p=>p.name).join(', ');
  const invPays=(i,iv)=>(i.pays||[]).filter(p=>p.inv===iv.id);
  const paidOf=i=>(i.pays||[]).reduce((t,p)=>t+n(p.amt),0);
  const loose=i=>(i.pays||[]).filter(p=>!p.inv||!(i.invs||[]).some(x=>x.id===p.inv));
  const catsOf=v=>[...(v.cats||[]),...[...new Set(v.items.map(i=>i.cat))].filter(c=>!(v.cats||[]).includes(c))];
  const norm=x=>String(x||'').toLowerCase().replace(/[^a-z]/g,'').replace('etransfer','etransfer');
  const mode=ps=>ps.map(p=>{const r=(p.ref||'').trim(),m=p.method||'';const nm=norm(m),nr=norm(r);
    const same=!r||nr===nm||(nm&&nr.includes(nm))||(m==='Cheque'&&/chq|cheque/i.test(r))||(m==='E-transfer'&&/e-?t[ra]+nsfer|etf/i.test(r));
    return same?(r&&m!=='Not recorded'&&nr!==nm?r:(m==='Not recorded'?(r||''):m)):(m&&m!=='Not recorded'?m+' · '+r:r);}).filter(Boolean).join(', ');
  const tabs=[];
  const T=(id,title,o)=>{const t={id,title,rows:[],fmt:[],widths:[],frozenRows:0,frozenCols:0,color:null,filter:null,...o};tabs.push(t);return t;};
  const R=(t,r0,r1,c0,c1)=>({sheetId:t.id,startRowIndex:r0,endRowIndex:r1,startColumnIndex:c0,endColumnIndex:c1});
  const fmt=(t,r0,r1,c0,c1,f)=>t.fmt.push({repeatCell:{range:R(t,r0,r1,c0,c1),cell:{userEnteredFormat:f},fields:Object.keys(f).map(k=>'userEnteredFormat.'+k).join(',')}});
  const head=(t,r,c1)=>fmt(t,r,r+1,0,c1,{backgroundColorStyle:{rgbColor:NAVY},textFormat:{bold:true,foregroundColorStyle:{rgbColor:WHITE}},wrapStrategy:'WRAP',verticalAlignment:'MIDDLE'});
  const num=(t,r0,r1,c0,c1,p)=>fmt(t,r0,r1,c0,c1,{numberFormat:{type:'NUMBER',pattern:p}});
  const bold=(t,r,c1,bg)=>fmt(t,r,r+1,0,c1,{textFormat:{bold:true},backgroundColorStyle:{rgbColor:bg||TEAL_L}});
  const titleRows=(t,a,b)=>{t.rows.push([a]);fmt(t,0,1,0,1,{textFormat:{bold:true,fontSize:16}});t.rows.push([b||'']);fmt(t,1,2,0,1,{textFormat:{foregroundColorStyle:{rgbColor:MUTE}}});t.rows.push([]);};
  const section=(t,s)=>{const r=t.rows.length;t.rows.push([s]);fmt(t,r,r+1,0,1,{textFormat:{bold:true,fontSize:12,foregroundColorStyle:{rgbColor:TEAL}}});};
  const table=(t,hdr,rows,pats,total)=>{const r=t.rows.length;t.rows.push(hdr);head(t,r,hdr.length);rows.forEach(x=>t.rows.push(x));let end=t.rows.length;
    if(total){t.rows.push(total);bold(t,end,hdr.length);end++;}
    for(let c=0;c<(pats||[]).length;){const p=pats[c];let e=c+1;while(e<pats.length&&pats[e]===p)e++;if(p)num(t,r+1,end,c,e,p);c=e;}return r;};
  const cond=(t,r0,r1,c0,c1,gt,b)=>t.fmt.push({addConditionalFormatRule:{index:0,rule:{ranges:[R(t,r0,r1,c0,c1)],booleanRule:{condition:{type:'NUMBER_GREATER',values:[{userEnteredValue:String(gt)}]},format:{textFormat:{bold:!!b,foregroundColorStyle:{rgbColor:RED}}}}}}});
  const GROUP={red:0.878,green:0.937,blue:0.929};
  const grp=(t,r,c1)=>{fmt(t,r,r+1,0,c1,{textFormat:{bold:true,foregroundColorStyle:{rgbColor:NAVY}},backgroundColorStyle:{rgbColor:GROUP}});
    t.fmt.push({updateBorders:{range:R(t,r,r+1,0,c1),top:{style:'SOLID_MEDIUM',colorStyle:{rgbColor:TEAL}}}});};
  const condRanges=(t,ranges,c0,c1,b)=>{if(!ranges.length)return;t.fmt.push({addConditionalFormatRule:{index:0,rule:{ranges:ranges.map(([a,z])=>R(t,a,z,c0,c1)),booleanRule:{condition:{type:'NUMBER_GREATER',values:[{userEnteredValue:'0.5'}]},format:{textFormat:{bold:!!b,foregroundColorStyle:{rgbColor:RED}}}}}}});};
  const sumCol=(rows,c)=>rows.reduce((s,x)=>s+n(x[c]),0);
  const bigTiles=(t,labels,vals,pats)=>{const r=t.rows.length;t.rows.push(labels);t.rows.push(vals);
    fmt(t,r,r+1,0,labels.length,{textFormat:{bold:true,foregroundColorStyle:{rgbColor:WHITE}},backgroundColorStyle:{rgbColor:TEAL}});
    fmt(t,r+1,r+2,0,labels.length,{textFormat:{bold:true,fontSize:14},backgroundColorStyle:{rgbColor:TEAL_L}});
    num(t,r+1,r+2,0,pats.length,pats[0]);t.rows.push([]);};
  // ---------- main backup sheet: list of project files ----------
  if(opt.main){const S=T(20,'Project files',{color:TEAL,frozenRows:4});
    titleRows(S,'EliteCraft – project backup files','Each budget is backed up to its own Google Sheet (latest version only). Last backup: '+when+' ('+source+').');
    S.rows.pop();
    const BR=[];(store.budgets||[]).forEach(b=>{const v=latest(b);if(!v)return;const tot=v.items.reduce((s,i)=>s+n(i.amt),0),inv=v.items.reduce((s,i)=>s+n(i.act),0),pd=v.items.reduce((s,i)=>s+paidOf(i),0);const f=files[b.id]||{};
      BR.push([f.id?'=HYPERLINK("https://docs.google.com/spreadsheets/d/'+f.id+'/edit","'+String(b.name).replace(/"/g,"'")+'")':b.name,usedBy(b)||'Not linked',v.label,tot,inv,pd,inv-pd,when,b.id,f.id||'']);});
    S.rows.push([]);
    table(S,['Budget (click to open its sheet)','Project','Version','Budget','Invoiced','Paid','Balance due','Last backup','Budget id','Sheet id'],BR,[null,null,null,MONEY,MONEY,MONEY,MONEY]);
    fmt(S,4,4+BR.length+1,8,10,{textFormat:{foregroundColorStyle:{rgbColor:MUTE},fontSize:8}});
    S.widths=[300,200,80,130,130,130,130,130,110,110];}
  // ---------- per budget ----------
  const allPay=[];
  (store.budgets||[]).forEach((b,bi)=>{const v=latest(b);if(!v||opt.main||b.id!==opt.budget)return;
    const short=String(b.name).replace(/\s+budget$/i,'').trim()||b.name;
    const base=1,proj=usedBy(b)||'not linked to a project';
    const items=v.items,cats=catsOf(v);
    const tot=items.reduce((s,i)=>s+n(i.amt),0),inv=items.reduce((s,i)=>s+n(i.act),0),pd=items.reduce((s,i)=>s+paidOf(i),0);
    // type rows (like the invoice sheet tabs)
    const typeRows={Trade:[],Material:[],Service:[],Other:[]};
    items.forEach(i=>{(i.invs||[]).forEach(iv=>{const ps=invPays(i,iv),p=ps.reduce((s,x)=>s+n(x.amt),0);
        const md=mode(ps),nt=(iv.note||'').trim();(typeRows[iv.kind]||typeRows.Other).push([iv.vendor||'',i.name,iv.no||'',iv.date||'',n(iv.amt),r2(p),r2(n(iv.amt)-p),md,nt&&nt.toLowerCase()!==md.toLowerCase()&&!ps.some(x=>(x.ref||'').trim().toLowerCase()===nt.toLowerCase())?nt:'',iv.id]);});
      const L=loose(i);if(L.length){const k=((i.invs||[]).find(x=>x.kind)||{}).kind||'Other';L.forEach(p=>(typeRows[k]||typeRows.Other).push([(p.ref||'Payment')+' (no invoice)',i.name,'',p.date||'','',n(p.amt),-n(p.amt),mode([p]),'Deposit or payment not tied to an invoice','pay:'+p.id]));}
      (i.pays||[]).forEach(py=>{const iv=(i.invs||[]).find(x=>x.id===py.inv);allPay.push([b.name,i.cat,i.name,py.date||'',py.method||'',n(py.amt),iv?[iv.vendor||'',iv.no?'#'+iv.no:''].filter(Boolean).join(' · '):'(no invoice)',py.ref||'']);});});
    Object.values(typeRows).forEach(L=>L.sort((a,c)=>String(a[0]).toLowerCase().localeCompare(String(c[0]).toLowerCase())||String(a[3]).localeCompare(String(c[3]))));
    // Summary tab for the budget
    const BS=T(base,'Summary',{color:TEAL});
    titleRows(BS,b.name,'Project: '+proj+' · latest version '+v.label+(v.date?' ('+v.date+')':'')+' · last backup '+when+'. Made from the calculator; anything typed here is replaced at the next backup.');
    bigTiles(BS,['Total amount invoiced','Total amount paid','Balance due','Budget','Invoiced vs budget'],[inv,pd,inv-pd,tot,inv-tot],[MONEY,MONEY,MONEY,MONEY,MONEY]);
    section(BS,'By type (each has its own tab at the bottom)');
    const KR=KINDS.map(k=>{const L=typeRows[k];return [k,L.filter(x=>x[4]!=='').length,sumCol(L,4),sumCol(L,5),sumCol(L,6)];}).filter(x=>x[1]||x[3]);
    table(BS,['Type','Invoices','Total amount','Amount paid','Balance due'],KR,[null,null,MONEY,MONEY,MONEY],['All types',sumCol(KR,1),sumCol(KR,2),sumCol(KR,3),sumCol(KR,4)]);
    BS.rows.push([]);section(BS,'By category');
    const CR=cats.map(c=>{const L=items.filter(i=>i.cat===c);const cb=L.reduce((s,i)=>s+n(i.amt),0),ci=L.reduce((s,i)=>s+n(i.act),0),cp=L.reduce((s,i)=>s+paidOf(i),0);return [c,cb,ci,cp,ci-cp,ci-cb];}).filter(x=>x[1]||x[2]);
    table(BS,['Category','Budget','Total invoiced','Amount paid','Balance due','Variance (invoiced − budget)'],CR,[null,MONEY,MONEY,MONEY,MONEY,MONEY],['Total',sumCol(CR,1),sumCol(CR,2),sumCol(CR,3),sumCol(CR,4),sumCol(CR,5)]);
    BS.rows.push([]);section(BS,'Payments by method');
    const MR=METHODS.map(mt=>{let c=0,a=0;items.forEach(i=>(i.pays||[]).forEach(p=>{if((p.method||'Not recorded')===mt){c++;a+=n(p.amt);}}));return [mt,c,a];}).filter(x=>x[1]);
    table(BS,['Method','Payments','Amount'],MR,[null,null,MONEY],['All methods',sumCol(MR,1),sumCol(MR,2)]);
    BS.widths=[230,150,150,150,150,190];
    // Budget tab (like the Budget tab in the invoice sheet, grouped by category)
    const BB=T(base+1,'Budget',{color:NAVY,frozenRows:1,frozenCols:1});
    const hdrB=['Item','Budget','Actual invoiced','Variance','Variance %','Amount paid','Balance due','Invoices','Notes','Item id (don’t edit)'];
    BB.rows.push(hdrB);head(BB,0,hdrB.length);
    cats.forEach(c=>{const L=items.filter(i=>i.cat===c);if(!L.length)return;const cb=L.reduce((s,i)=>s+n(i.amt),0),ci=L.reduce((s,i)=>s+n(i.act),0),cp=L.reduce((s,i)=>s+paidOf(i),0);
      if(BB.rows.length>1)BB.rows.push([]);
      const cr=BB.rows.length;BB.rows.push([c,cb,ci,ci-cb,cb?(ci-cb)/cb:0,cp,ci-cp,L.length+' item'+(L.length===1?'':'s'),'']);grp(BB,cr,9);BB.blocks=(BB.blocks||[]);BB.blocks.push([cr+1,cr+1+L.length]);
      L.forEach(i=>{const a=n(i.amt),ac=n(i.act),p=paidOf(i),r=BB.rows.length;BB.rows.push(['    '+i.name,a,ac,ac-a,a?(ac-a)/a:0,p,ac-p,(i.invs||[]).length,i.note||'',i.id]);
});});
    const er=BB.rows.length;BB.rows.push(['Total',tot,inv,inv-tot,tot?(inv-tot)/tot:0,pd,inv-pd,items.reduce((s,i)=>s+(i.invs||[]).length,0),'']);bold(BB,er,9);
    condRanges(BB,BB.blocks||[],3,4,false);condRanges(BB,BB.blocks||[],6,7,true);num(BB,1,er+1,1,4,MONEY);num(BB,1,er+1,4,5,PCT);num(BB,1,er+1,5,7,MONEY);fmt(BB,1,er+1,8,9,{wrapStrategy:'CLIP'});
    fmt(BB,1,er+1,9,10,{textFormat:{foregroundColorStyle:{rgbColor:MUTE},fontSize:8}});BB.widths=[330,120,130,120,95,120,120,80,360,90];
    // Type tabs (same columns as the invoice sheet: Name, Category, Invoice no., Date, Total, Amount paid, Balance due, Mode of payment, Notes)
    const KLAB={Trade:'Trade (contractors and labour)',Material:'Material (suppliers and stores)',Service:'Service (permits, insurance, utilities, rentals, design)',Other:'Other (small site costs)'};
    KINDS.forEach((k,j)=>{const L=typeRows[k];if(!L.length)return;
      const t=T(base+2+j,k,{frozenRows:5,frozenCols:0,color:k==='Trade'?{red:0.85,green:0.55,blue:0.1}:k==='Material'?{red:0.2,green:0.5,blue:0.8}:{red:0.55,green:0.55,blue:0.6}});
      titleRows(t,b.name+' – '+KLAB[k],'Grouped by budget category. Use the filter arrows on the blue heading row to show one category, vendor or only unpaid invoices.');
      t.rows.pop();
      const nInv=L.filter(x=>x[4]!=='').length;
      const tr=t.rows.length;t.rows.push(['Total amount','Amount paid','Balance due','Invoices']);t.rows.push([sumCol(L,4),sumCol(L,5),sumCol(L,6),nInv]);
      fmt(t,tr,tr+1,0,4,{textFormat:{bold:true,foregroundColorStyle:{rgbColor:WHITE}},backgroundColorStyle:{rgbColor:TEAL}});
      fmt(t,tr+1,tr+2,0,4,{textFormat:{bold:true,fontSize:13},backgroundColorStyle:{rgbColor:TEAL_L}});num(t,tr+1,tr+2,0,3,MONEY);
      const hr=t.rows.length;const hdr=['Category','Name','Invoice no.','Date','Total amount','Amount paid','Balance due','Mode of payment','Notes','Row id (don’t edit)'];t.rows.push(hdr);head(t,hr,10);
      const order=cats.filter(c=>L.some(x=>(items.find(i=>i.name===x[1])||{}).cat===c));
      const byItem={};L.forEach(x=>{(byItem[x[1]]=byItem[x[1]]||[]).push(x);});
      const itemOrder=[];order.forEach(c=>items.filter(i=>i.cat===c).forEach(i=>{if(byItem[i.name])itemOrder.push(i.name);}));Object.keys(byItem).forEach(nm=>{if(!itemOrder.includes(nm))itemOrder.push(nm);});
      itemOrder.forEach(nm=>{const R2=byItem[nm].slice().sort((a,c)=>String(a[3]||'9999').localeCompare(String(c[3]||'9999')));
        if(t.rows.length>hr+1)t.rows.push([]);
        const gr=t.rows.length,cnt=R2.filter(x=>x[4]!=='').length;
        t.rows.push([nm,cnt+' invoice'+(cnt===1?'':'s'),'','',sumCol(R2,4),sumCol(R2,5),sumCol(R2,6),'','']);
        grp(t,gr,9);(t.blocks=t.blocks||[]).push([gr+1,gr+1+R2.length]);
        R2.forEach(x=>t.rows.push([nm,x[0],x[2],x[3],x[4],x[5],x[6],x[7],x[8],x[9]||'']));
        fmt(t,gr+1,t.rows.length,0,1,{textFormat:{foregroundColorStyle:{rgbColor:MUTE},fontSize:9}});});
      const end=t.rows.length;
      num(t,hr+1,end,4,7,MONEY);fmt(t,hr+1,end,7,9,{wrapStrategy:'CLIP'});condRanges(t,t.blocks||[],6,7,true);
      fmt(t,hr+1,end,9,10,{textFormat:{foregroundColorStyle:{rgbColor:MUTE},fontSize:8}});t.filter=[hr,end,10];t.widths=[170,250,140,95,115,115,115,230,300,90];});});
  // ---------- requests ----------
  const ex=existing||[];
  const dynamic=s=>s.sheetId!==0&&!/^(read me|to check|category check|backup log|backup data)$/i.test(s.title);
  const structure=[];
  ex.filter(dynamic).forEach(s=>structure.push({deleteSheet:{sheetId:s.sheetId}}));
  if(!opt.main){const s0=ex.find(s=>s.sheetId===0);if(s0&&s0.title!=='Read me')structure.push({updateSheetProperties:{properties:{sheetId:0,title:'Read me'},fields:'title'}});}
  tabs.forEach((t,k)=>structure.push({addSheet:{properties:{sheetId:t.id,title:t.title,index:1+k,gridProperties:{rowCount:Math.max(50,t.rows.length+20),columnCount:Math.max(10,...t.rows.map(r=>r.length)),frozenRowCount:t.frozenRows,frozenColumnCount:t.frozenCols},...(t.color?{tabColorStyle:{rgbColor:t.color}}:{})}}}));
  const extra=[];
  if(!opt.main){[['Backup log',90,['When','What triggered it','Projects','Budgets','Payments','Data size (characters)','Calculator saved at']],['Backup data',91,['When','What triggered it','Parts','Data part 1','Data part 2','Data part 3','Data part 4','Data part 5','Data part 6','Data part 7','Data part 8','Data part 9']]].forEach(([tt,id,hd])=>{
    if(!ex.some(s=>s.title===tt)){structure.push({addSheet:{properties:{sheetId:id,title:tt,hidden:true,gridProperties:{rowCount:2000,columnCount:12}}}});extra.push({title:tt,range:"'"+tt+"'!A1:"+String.fromCharCode(64+hd.length)+'1',values:[hd],requests:[]});}});}
  ex.filter(s=>!dynamic(s)&&s.sheetId!==0).forEach((s,k)=>structure.push({updateSheetProperties:{properties:{sheetId:s.sheetId,index:1+tabs.length+k},fields:'index'}}));
  const uv=v=>{if(v==null)return '';if(typeof v==='number')return isFinite(v)?Math.round(v*1e6)/1e6:0;let x=String(unq(v));
    if(/^=HYPERLINK\(/.test(x))return x;    if(/^\d{4}-\d{2}-\d{2}$/.test(x))return x;if(/^[=+\-@]/.test(x)||/^[\d.,\-\/ $%#]+$/.test(x)||/^0\d/.test(x))return "'"+x;return x;};
  const colL=k=>{let s='';k++;while(k>0){const r=(k-1)%26;s=String.fromCharCode(65+r)+s;k=(k-1-r)/26;}return s;};
  const perTab=tabs.map(t=>{const w=Math.max(1,...t.rows.map(r=>r.length));
    const values=t.rows.map(r=>{const o=r.map(uv);while(o.length<w)o.push('');return o;});
    const req=t.fmt.slice();
    for(let c=0;c<t.widths.length;){let e=c+1;while(e<t.widths.length&&t.widths[e]===t.widths[c])e++;req.push({updateDimensionProperties:{range:{sheetId:t.id,dimension:'COLUMNS',startIndex:c,endIndex:e},properties:{pixelSize:t.widths[c]},fields:'pixelSize'}});c=e;}
    if(t.filter)req.push({setBasicFilter:{filter:{range:{sheetId:t.id,startRowIndex:t.filter[0],endRowIndex:t.filter[1],startColumnIndex:0,endColumnIndex:t.filter[2]}}}});
    return {title:t.title,range:"'"+t.title.replace(/'/g,"''")+"'!A1:"+colL(w-1)+values.length,values,requests:req};});
  if(!opt.main){const b=(store.budgets||[]).find(x=>x.id===opt.budget)||{};perTab.push({title:'Read me',range:"'Read me'!A1:B8",values:[[b.name||'Budget backup',''],['What this is','A read-only copy of this budget from the Project profit calculator (latest version only). Make changes in the calculator, not here.'],['Summary','Totals: invoiced, paid, balance due, by type, by category and by payment method.'],['Budget','Every item grouped by category with budget, actual invoiced, variance, paid and balance due.'],['Trade / Material / Service / Other','Invoices grouped by budget item, like the Trade and Supplier tabs in the invoice sheet. Use the filter arrows to narrow down.'],['When it updates','Every Save for team, Back up now, and once a day.'],['Last backup',when+' ('+source+')'],['Editing here','You can change amounts, dates, vendors, invoice numbers, amount paid and notes, move a row to another type tab, or add a row (budget item name in Category, Row id empty). Then in the calculator: Backups, Bring changes back, Check for changes. Don\u2019t edit the Row id column. Hidden tabs (Backup log, Backup data) hold the restore copies.']],requests:[{repeatCell:{range:{sheetId:0,startRowIndex:0,endRowIndex:1,startColumnIndex:0,endColumnIndex:1},cell:{userEnteredFormat:{textFormat:{bold:true,fontSize:16}}},fields:'userEnteredFormat.textFormat'}},{repeatCell:{range:{sheetId:0,startRowIndex:1,endRowIndex:8,startColumnIndex:0,endColumnIndex:1},cell:{userEnteredFormat:{textFormat:{bold:true},verticalAlignment:'TOP'}},fields:'userEnteredFormat.textFormat,userEnteredFormat.verticalAlignment'}},{repeatCell:{range:{sheetId:0,startRowIndex:1,endRowIndex:8,startColumnIndex:1,endColumnIndex:2},cell:{userEnteredFormat:{wrapStrategy:'WRAP',verticalAlignment:'TOP'}},fields:'userEnteredFormat.wrapStrategy,userEnteredFormat.verticalAlignment'}},{updateDimensionProperties:{range:{sheetId:0,dimension:'COLUMNS',startIndex:0,endIndex:1},properties:{pixelSize:230},fields:'pixelSize'}},{updateDimensionProperties:{range:{sheetId:0,dimension:'COLUMNS',startIndex:1,endIndex:2},properties:{pixelSize:640},fields:'pixelSize'}}]});}
  extra.forEach(x=>perTab.push(x));
  return {structure,perTab,log:bk.log.map(r=>[...r,store.savedAt||'']),data:bk.data,head:'Last backup: '+when+' ('+source+')',tabs:tabs.map(t=>t.title)};}
/*ENDSHEETS*/
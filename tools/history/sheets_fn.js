/*SHEETS*/
function buildSheets(store,calc,source,when,existing){
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
  const mode=ps=>ps.map(p=>{const r=(p.ref||'').trim();return r&&r.toLowerCase()!==(p.method||'').toLowerCase()?(p.method&&p.method!=='Not recorded'?p.method+' '+r:r):(p.method||'');}).filter(Boolean).join(', ');
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
  const sumCol=(rows,c)=>rows.reduce((s,x)=>s+n(x[c]),0);
  const bigTiles=(t,labels,vals,pats)=>{const r=t.rows.length;t.rows.push(labels);t.rows.push(vals);
    fmt(t,r,r+1,0,labels.length,{textFormat:{bold:true,foregroundColorStyle:{rgbColor:WHITE}},backgroundColorStyle:{rgbColor:TEAL}});
    fmt(t,r+1,r+2,0,labels.length,{textFormat:{bold:true,fontSize:14},backgroundColorStyle:{rgbColor:TEAL_L}});
    num(t,r+1,r+2,0,pats.length,pats[0]);t.rows.push([]);};
  // ---------- overall Summary ----------
  const S=T(1,'Summary',{color:TEAL});
  titleRows(S,'EliteCraft – all projects','Last backup: '+when+' ('+source+'). Made from the calculator; anything typed here is replaced at the next backup.');
  const BR=[];(store.budgets||[]).forEach(b=>{const v=latest(b);if(!v)return;const tot=v.items.reduce((s,i)=>s+n(i.amt),0),inv=v.items.reduce((s,i)=>s+n(i.act),0),pd=v.items.reduce((s,i)=>s+paidOf(i),0);BR.push([b.name,usedBy(b)||'Not linked',v.label,tot,inv,pd,inv-pd,inv-tot]);});
  bigTiles(S,['Total amount invoiced','Total amount paid','Balance due'],[sumCol(BR,4),sumCol(BR,5),sumCol(BR,6)],[MONEY,MONEY,MONEY]);
  section(S,'Budgets (latest version of each). Each budget has its own tabs: Summary, Budget, Trade, Material, Service and Other.');
  table(S,['Budget','Project','Version','Budget','Invoiced','Paid','Balance due','Invoiced vs budget'],BR,[null,null,null,MONEY,MONEY,MONEY,MONEY,MONEY],['All budgets','','',sumCol(BR,3),sumCol(BR,4),sumCol(BR,5),sumCol(BR,6),sumCol(BR,7)]);
  S.rows.push([]);section(S,'Projects');
  const PR=bk.projects.map(p=>[unq(p[0]),p[1],p[13],p[14],p[15]===''?'':Math.min(n(p[15]),n(p[16])),p[18],p[19],p[20]]);
  table(S,['Project','Financing used','Profit before financing','Investor return','Annualized return','Profit after financing','Cash needed','ROI on cash'],PR,[null,null,MONEY,PCT,PCT,MONEY,MONEY,PCT]);
  S.widths=[230,180,150,150,150,150,150,150];
  // Projects & Investors
  const PJ=T(2,'Projects',{frozenRows:1,frozenCols:1});
  table(PJ,['Project','Financing used','Sell price (incl. GST)','Net sell (before GST)','Lot','Build cost','Build cost from','Lot held before build (months)','Build time (months)','Months to close','Realtor','Overhead','Project cost','Profit before financing','Investor return','Annualized (high)','Annualized (low)','Financing cost','Profit after financing','Cash needed','ROI on cash','Investor cash','Investor earnings'],
    bk.projects.map(r=>r.map(unq)),[null,null,MONEY,MONEY,MONEY,MONEY,null,null,null,null,null,MONEY,MONEY,MONEY,PCT,PCT,PCT,MONEY,MONEY,MONEY,PCT,MONEY,MONEY]);
  PJ.widths=[200,150,120,120,110,110,220,110,100,100,120,110,120,130,110,110,110,120,130,120,100,120,120];
  const IN=T(3,'Investors',{frozenRows:1});
  table(IN,['Project','Investor','Cash in','Return','Earnings','Payout (cash + earnings)'],bk.investors.map(r=>[unq(r[0]),unq(r[1]),n(r[2]),n(r[3]),n(r[4]),n(r[2])+n(r[4])]),[null,null,MONEY,PCT,MONEY,MONEY]);
  IN.widths=[200,180,130,110,130,170];
  // ---------- per budget ----------
  const allPay=[];
  (store.budgets||[]).forEach((b,bi)=>{const v=latest(b);if(!v)return;
    const short=String(b.name).replace(/\s+budget$/i,'').trim()||b.name;
    const base=1000+bi*10,proj=usedBy(b)||'not linked to a project';
    const items=v.items,cats=catsOf(v);
    const tot=items.reduce((s,i)=>s+n(i.amt),0),inv=items.reduce((s,i)=>s+n(i.act),0),pd=items.reduce((s,i)=>s+paidOf(i),0);
    // type rows (like the invoice sheet tabs)
    const typeRows={Trade:[],Material:[],Service:[],Other:[]};
    items.forEach(i=>{(i.invs||[]).forEach(iv=>{const ps=invPays(i,iv),p=ps.reduce((s,x)=>s+n(x.amt),0);
        (typeRows[iv.kind]||typeRows.Other).push([iv.vendor||'',i.name,iv.no||'',iv.date||'',n(iv.amt),r2(p),r2(n(iv.amt)-p),mode(ps),iv.note||'']);});
      const L=loose(i);if(L.length){const k=((i.invs||[]).find(x=>x.kind)||{}).kind||'Other';L.forEach(p=>(typeRows[k]||typeRows.Other).push([(p.ref||'Payment')+' (no invoice)',i.name,'',p.date||'','',n(p.amt),-n(p.amt),mode([p]),'Deposit or payment not tied to an invoice']));}
      (i.pays||[]).forEach(py=>{const iv=(i.invs||[]).find(x=>x.id===py.inv);allPay.push([b.name,i.cat,i.name,py.date||'',py.method||'',n(py.amt),iv?[iv.vendor||'',iv.no?'#'+iv.no:''].filter(Boolean).join(' · '):'(no invoice)',py.ref||'']);});});
    Object.values(typeRows).forEach(L=>L.sort((a,c)=>String(a[0]).toLowerCase().localeCompare(String(c[0]).toLowerCase())||String(a[3]).localeCompare(String(c[3]))));
    // Summary tab for the budget
    const BS=T(base,safeTitle(short+' – Summary'),{color:TEAL});
    titleRows(BS,b.name+' – summary','Project: '+proj+' · latest version '+v.label+(v.date?' ('+v.date+')':'')+' · last backup '+when);
    bigTiles(BS,['Total amount invoiced','Total amount paid','Balance due','Budget','Invoiced vs budget'],[inv,pd,inv-pd,tot,inv-tot],[MONEY,MONEY,MONEY,MONEY,MONEY]);
    section(BS,'By type (each has its own tab)');
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
    const BB=T(base+1,safeTitle(short+' – Budget'),{color:NAVY,frozenRows:1,frozenCols:1});
    const hdrB=['Item','Budget','Actual invoiced','Variance','Variance %','Amount paid','Balance due','Invoices','Notes'];
    BB.rows.push(hdrB);head(BB,0,hdrB.length);
    cats.forEach(c=>{const L=items.filter(i=>i.cat===c);if(!L.length)return;const cb=L.reduce((s,i)=>s+n(i.amt),0),ci=L.reduce((s,i)=>s+n(i.act),0),cp=L.reduce((s,i)=>s+paidOf(i),0);
      const cr=BB.rows.length;BB.rows.push([c,cb,ci,ci-cb,cb?(ci-cb)/cb:0,cp,ci-cp,'','']);fmt(BB,cr,cr+1,0,9,{textFormat:{bold:true,foregroundColorStyle:{rgbColor:WHITE}},backgroundColorStyle:{rgbColor:TEAL}});
      L.forEach(i=>{const a=n(i.amt),ac=n(i.act),p=paidOf(i),r=BB.rows.length;BB.rows.push(['    '+i.name,a,ac,ac-a,a?(ac-a)/a:0,p,ac-p,(i.invs||[]).length,i.note||'']);
});});
    const er=BB.rows.length;BB.rows.push(['Total',tot,inv,inv-tot,tot?(inv-tot)/tot:0,pd,inv-pd,items.reduce((s,i)=>s+(i.invs||[]).length,0),'']);bold(BB,er,9);
    cond(BB,1,er,3,4,0.5,false);cond(BB,1,er,6,7,0.5,true);num(BB,1,er+1,1,4,MONEY);num(BB,1,er+1,4,5,PCT);num(BB,1,er+1,5,7,MONEY);fmt(BB,1,er+1,8,9,{wrapStrategy:'CLIP'});
    BB.widths=[330,120,130,120,95,120,120,80,360];
    // Type tabs (same columns as the invoice sheet: Name, Category, Invoice no., Date, Total, Amount paid, Balance due, Mode of payment, Notes)
    const KLAB={Trade:'Trade (contractors and labour)',Material:'Material (suppliers and stores)',Service:'Service (permits, insurance, utilities, rentals, design)',Other:'Other (small site costs)'};
    KINDS.forEach((k,j)=>{const L=typeRows[k];if(!L.length)return;
      const t=T(base+2+j,safeTitle(short+' – '+k),{frozenRows:5,frozenCols:0,color:k==='Trade'?{red:0.85,green:0.55,blue:0.1}:k==='Material'?{red:0.2,green:0.5,blue:0.8}:{red:0.55,green:0.55,blue:0.6}});
      titleRows(t,b.name+' – '+KLAB[k],'Grouped by budget category. Use the filter arrows on the blue heading row to show one category, vendor or only unpaid invoices.');
      t.rows.pop();
      const nInv=L.filter(x=>x[4]!=='').length;
      const tr=t.rows.length;t.rows.push(['Total amount','Amount paid','Balance due','Invoices']);t.rows.push([sumCol(L,4),sumCol(L,5),sumCol(L,6),nInv]);
      fmt(t,tr,tr+1,0,4,{textFormat:{bold:true,foregroundColorStyle:{rgbColor:WHITE}},backgroundColorStyle:{rgbColor:TEAL}});
      fmt(t,tr+1,tr+2,0,4,{textFormat:{bold:true,fontSize:13},backgroundColorStyle:{rgbColor:TEAL_L}});num(t,tr+1,tr+2,0,3,MONEY);
      const hr=t.rows.length;const hdr=['Category','Name','Invoice no.','Date','Total amount','Amount paid','Balance due','Mode of payment','Notes'];t.rows.push(hdr);head(t,hr,9);
      const order=cats.filter(c=>L.some(x=>(items.find(i=>i.name===x[1])||{}).cat===c));
      const byItem={};L.forEach(x=>{(byItem[x[1]]=byItem[x[1]]||[]).push(x);});
      const itemOrder=[];order.forEach(c=>items.filter(i=>i.cat===c).forEach(i=>{if(byItem[i.name])itemOrder.push(i.name);}));Object.keys(byItem).forEach(nm=>{if(!itemOrder.includes(nm))itemOrder.push(nm);});
      itemOrder.forEach(nm=>{const R2=byItem[nm].slice().sort((a,c)=>String(a[3]||'9999').localeCompare(String(c[3]||'9999')));
        const gr=t.rows.length,cnt=R2.filter(x=>x[4]!=='').length;
        t.rows.push([nm,cnt+' invoice'+(cnt===1?'':'s'),'','',sumCol(R2,4),sumCol(R2,5),sumCol(R2,6),'','']);
        fmt(t,gr,gr+1,0,9,{textFormat:{bold:true,foregroundColorStyle:{rgbColor:WHITE}},backgroundColorStyle:{rgbColor:TEAL}});
        R2.forEach(x=>t.rows.push([nm,x[0],x[2],x[3],x[4],x[5],x[6],x[7],x[8]]));
        fmt(t,gr+1,t.rows.length,0,1,{textFormat:{foregroundColorStyle:{rgbColor:MUTE},fontSize:9}});});
      const end=t.rows.length;
      num(t,hr+1,end,4,7,MONEY);fmt(t,hr+1,end,7,9,{wrapStrategy:'CLIP'});cond(t,hr+1,end,6,7,0.5,true);
      t.filter=[hr,end,9];t.widths=[170,250,140,95,115,115,115,230,300];});});
  // ---------- requests ----------
  const ex=existing||[];
  const dynamic=s=>s.sheetId!==0&&!/^(read me|to check|category check|backup log|backup data)$/i.test(s.title);
  const structure=[];
  ex.filter(dynamic).forEach(s=>structure.push({deleteSheet:{sheetId:s.sheetId}}));
  tabs.forEach((t,k)=>structure.push({addSheet:{properties:{sheetId:t.id,title:t.title,index:1+k,gridProperties:{rowCount:Math.max(50,t.rows.length+20),columnCount:Math.max(10,...t.rows.map(r=>r.length)),frozenRowCount:t.frozenRows,frozenColumnCount:t.frozenCols},...(t.color?{tabColorStyle:{rgbColor:t.color}}:{})}}}));
  ex.filter(s=>!dynamic(s)&&s.sheetId!==0).forEach((s,k)=>structure.push({updateSheetProperties:{properties:{sheetId:s.sheetId,index:1+tabs.length+k},fields:'index'}}));
  const uv=v=>{if(v==null)return '';if(typeof v==='number')return isFinite(v)?Math.round(v*1e6)/1e6:0;let x=String(unq(v));
    if(/^\d{4}-\d{2}-\d{2}$/.test(x))return x;if(/^[=+\-@]/.test(x)||/^[\d.,\-\/ $%#]+$/.test(x)||/^0\d/.test(x))return "'"+x;return x;};
  const colL=k=>{let s='';k++;while(k>0){const r=(k-1)%26;s=String.fromCharCode(65+r)+s;k=(k-1-r)/26;}return s;};
  const perTab=tabs.map(t=>{const w=Math.max(1,...t.rows.map(r=>r.length));
    const values=t.rows.map(r=>{const o=r.map(uv);while(o.length<w)o.push('');return o;});
    const req=t.fmt.slice();
    for(let c=0;c<t.widths.length;){let e=c+1;while(e<t.widths.length&&t.widths[e]===t.widths[c])e++;req.push({updateDimensionProperties:{range:{sheetId:t.id,dimension:'COLUMNS',startIndex:c,endIndex:e},properties:{pixelSize:t.widths[c]},fields:'pixelSize'}});c=e;}
    if(t.filter)req.push({setBasicFilter:{filter:{range:{sheetId:t.id,startRowIndex:t.filter[0],endRowIndex:t.filter[1],startColumnIndex:0,endColumnIndex:t.filter[2]}}}});
    return {title:t.title,range:"'"+t.title.replace(/'/g,"''")+"'!A1:"+colL(w-1)+values.length,values,requests:req};});
  return {structure,perTab,log:bk.log.map(r=>[...r,store.savedAt||'']),data:bk.data,head:'Last backup: '+when+' ('+source+')',tabs:tabs.map(t=>t.title)};}
/*ENDSHEETS*/

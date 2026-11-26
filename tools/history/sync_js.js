let syncFiles={},syncChanges=[];
const money2=v=>{let s=String(v==null?'':v).trim();if(!s||s==='-')return 0;const neg=/^\(.*\)$/.test(s)||/^-/.test(s)||/^\$-/.test(s);s=s.replace(/[^0-9.]/g,'');const x=parseFloat(s);return isNaN(x)?0:(neg?-x:x);};
const txt2=v=>String(v==null?'':v).trim();
async function syncLoadFiles(){syncFiles={};try{vals(await sheetCall('get_values',{range:"'Project files'!I5:J"})).forEach(r=>{if(r[0]&&r[1])syncFiles[r[0]]=String(r[1]);});}catch(_){}
  const sel=$('#syncb');if(!sel)return;const opts=(store.budgets||[]).filter(b=>syncFiles[b.id]);
  sel.innerHTML=opts.length?opts.map(b=>`<option value="${esc(b.id)}">${esc(b.name)}</option>`).join(''):'<option value="">No project sheets yet: click Back up now first</option>';
  $('#syncgo').disabled=!opts.length;}
async function syncCheck(){const bid=$('#syncb').value,b=(store.budgets||[]).find(x=>x.id===bid),fid=syncFiles[bid];const out=$('#syncres');
  if(!b||!fid){out.textContent='Pick a budget that has a project sheet.';return;}
  const v=b.versions[b.versions.length-1];out.textContent='Reading '+b.name+' sheet…';
  try{const call=(range)=>sheetsCall('get_values',{spreadsheetId:fid,range}).then(vals).catch(()=>[]);
    const [bud,...types]=await Promise.all(["'Budget'!A1:J400",...KINDS.map(k=>"'"+k+"'!A1:J2000")].map(call));
    const ch=[];const byId={};v.items.forEach(i=>(i.invs||[]).forEach(iv=>{byId[iv.id]={i,iv};}));
    const itemsById={};v.items.forEach(i=>{itemsById[i.id]=i;});
    const itemByName=nm=>v.items.find(i=>i.name.trim().toLowerCase()===String(nm||'').trim().toLowerCase());
    // budget tab: amounts and notes
    bud.slice(1).forEach(r=>{const id=txt2(r[9]);const it=id&&itemsById[id];if(!it)return;
      const a=money2(r[1]),note=txt2(r[8]);
      if(Math.abs(a-(+it.amt||0))>0.004)ch.push({k:'item-amt',it,from:+it.amt||0,to:a,label:it.name+': budget '+m(+it.amt||0)+' → '+m(a),on:true});
      if(note!==txt2(it.note))ch.push({k:'item-note',it,to:note,label:it.name+': note changed',on:true});});
    // type tabs
    const seen=new Set();
    types.forEach((rows,ti)=>{const kind=KINDS[ti];const hr=rows.findIndex(r=>txt2(r[0])==='Category'&&txt2(r[1])==='Name');if(hr<0)return;
      rows.slice(hr+1).forEach(r=>{const id=txt2(r[9]),cat=txt2(r[0]),name=txt2(r[1]);if(!cat&&!name)return;
        if(id.startsWith('pay:'))return;
        if(id){seen.add(id);const hit=byId[id];if(!hit)return;const {i,iv}=hit;const diffs=[],upd={};
          const no=txt2(r[2]),date=txt2(r[3]),amt=money2(r[4]),paidS=money2(r[5]),note=txt2(r[8]);
          if(name!==txt2(iv.vendor)){diffs.push('vendor');upd.vendor=name;}
          if(no!==txt2(iv.no)){diffs.push('invoice no.');upd.no=no;}
          if(date!==txt2(iv.date)){diffs.push('date');upd.date=date;}
          if(Math.abs(amt-(+iv.amt||0))>0.004){diffs.push('amount '+m(+iv.amt||0)+' → '+m(amt));upd.amt=amt;}
          if(kind!==(iv.kind||'Other')){diffs.push('type → '+kind);upd.kind=kind;}
          if(note&&note!==txt2(iv.note)){diffs.push('notes');upd.note=note;}
          if(diffs.length)ch.push({k:'inv-upd',i,iv,upd,label:(iv.vendor||'Invoice')+(iv.no?' #'+iv.no:'')+' ('+i.name+'): '+diffs.join(', '),on:true});
          const pd=invPaid(i,iv);if(Math.abs(paidS-pd)>0.004)ch.push({k:'inv-paid',i,iv,diff:r2(paidS-pd),label:(iv.vendor||'Invoice')+(iv.no?' #'+iv.no:'')+': paid '+m(pd)+' → '+m(paidS)+' (adds a '+m(paidS-pd)+' payment)',on:true});
          return;}
        if(/^\d+ invoices?$/.test(name))return;
        const amt=money2(r[4]);if(!amt&&!money2(r[5]))return;
        const it=itemByName(cat);
        ch.push({k:'inv-new',it,cat,row:{vendor:name,no:txt2(r[2]),date:txt2(r[3]),kind,amt,paid:money2(r[5]),note:txt2(r[8])},label:'New '+kind.toLowerCase()+' invoice: '+(name||'?')+' '+m(amt)+(it?' in '+it.name:' — no budget line called "'+cat+'"'),on:!!it,bad:!it});});});
    Object.keys(byId).forEach(id=>{if(!seen.has(id)&&types.some(t=>t.length)){const {i,iv}=byId[id];ch.push({k:'inv-del',i,iv,label:'Not in the sheet any more: '+(iv.vendor||'Invoice')+(iv.no?' #'+iv.no:'')+' '+m(+iv.amt||0)+' ('+i.name+'). Delete it here too?',on:false});}});
    syncChanges=ch;
    if(!ch.length){out.innerHTML='<p class="note">No differences. The calculator and the '+esc(b.name)+' sheet match.</p>';return;}
    out.innerHTML='<p class="note">'+ch.length+' difference'+(ch.length>1?'s':'')+' found. Tick the ones to bring into the calculator. They load as unsaved changes; click Save for team to keep them.</p><div class="synclist">'+ch.map((c,k)=>`<label class="syncrow${c.bad?' bad':''}"><input type="checkbox" data-sync="${k}"${c.on?' checked':''}${c.bad?' disabled':''}><span>${esc(c.label)}</span></label>`).join('')+'</div><div class="ctrl" style="margin-top:10px"><button class="btn pri" data-act="sync-apply">Apply selected</button></div>';}
  catch(e){out.textContent=bkErr(e);}}
function syncApply(){const bid=$('#syncb').value,b=(store.budgets||[]).find(x=>x.id===bid);if(!b)return;const v=b.versions[b.versions.length-1];
  const pick=[...document.querySelectorAll('[data-sync]')].filter(x=>x.checked).map(x=>syncChanges[+x.dataset.sync]);if(!pick.length){status('Nothing selected.');return;}
  const touched=new Set();
  pick.forEach(c=>{if(c.k==='item-amt')c.it.amt=c.to;else if(c.k==='item-note')c.it.note=c.to;
    else if(c.k==='inv-upd'){Object.assign(c.iv,c.upd);touched.add(c.i);}
    else if(c.k==='inv-paid'){c.i.pays.push({id:uid(),date:today(),method:c.diff<0?'Refund / credit':'Not recorded',amt:c.diff,ref:'From project sheet',inv:c.iv.id});}
    else if(c.k==='inv-new'&&c.it){if(!Array.isArray(c.it.invs))c.it.invs=[];const iv={id:uid(),vendor:c.row.vendor,no:c.row.no,date:c.row.date,kind:c.row.kind,amt:r2(c.row.amt),note:c.row.note};c.it.invs.push(iv);
      if(c.row.paid)c.it.pays.push({id:uid(),date:c.row.date||today(),method:'Not recorded',amt:r2(c.row.paid),ref:'From project sheet',inv:iv.id});touched.add(c.it);}
    else if(c.k==='inv-del'){c.i.invs=c.i.invs.filter(x=>x!==c.iv);c.i.pays.forEach(p=>{if(p.inv===c.iv.id)p.inv=null;});touched.add(c.i);}});
  touched.forEach(i=>{i.act=r2((i.invs||[]).reduce((t,x)=>t+(+x.amt||0),0));});
  persist();try{renderBudget();refresh();}catch(_){}
  $('#syncres').innerHTML='<p class="note">Applied '+pick.length+' change'+(pick.length>1?'s':'')+'. Check the Budget page, then click Save for team to keep them.</p>';status('Brought '+pick.length+' change'+(pick.length>1?'s':'')+' in from the sheet.');}

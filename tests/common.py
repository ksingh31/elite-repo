import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *
from playwright.sync_api import sync_playwright

SEED="""(()=>{const store=JSON.parse(document.getElementById('store').textContent);const b=store.budgets.find(x=>x.id==='b-demo');const v=b.versions[b.versions.length-1];const it=n=>v.items.find(i=>i.name===n);
let k=0;const U=(name,amt,yes,status,by,note)=>({id:'u'+(++k),name,amt,yes,by,status,note:note||''});
it('Windows and doors').ups=[U('Black exterior frames',1200,true,'Approved','Buyer','Change order signed Apr 14'),U('Triple-pane glazing',6500,false,'Declined','Buyer','Buyer chose double-pane'),U('Oversized patio slider (12 ft)',3800,false,'Quoted','Buyer','Evergreen Lighting Group quote, valid to Dec 15')];
it('Stone').ups=[U('Full stone front elevation',4500,true,'Approved','Buyer','')];
it('Kitchen cabinets').ups=[U('Uppers to ceiling with crown',4200,true,'Approved','Buyer',''),U('Walnut island',2900,false,'Quoted','Buyer','Waiting on buyer')];
localStorage.setItem('ec-calc5',JSON.stringify({base:store.savedAt,data:store,at:new Date().toISOString()}));})()"""

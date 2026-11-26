// node plan2.js page.html "Source" '<existing json>' main|<budgetId> '<files json>'
const fs=require('fs');const h=fs.readFileSync(process.argv[2],'utf8');
const calc=new Function(h.split('/*ENGINE*/')[1].split('/*END*/')[0]+';return calc;')();
const src=h.split('/*BACKUP*/')[1].split('/*ENDBACKUP*/')[0]+h.split('/*SHEETS*/')[1].split('/*ENDSHEETS*/')[0];
const buildSheets=new Function(src+';return buildSheets;')();
const store=JSON.parse(h.split('<script id="store" type="application/json">')[1].split('</script>')[0]);
const f=new Intl.DateTimeFormat('en-CA',{timeZone:'America/Edmonton',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(new Date()),g=t=>(f.find(x=>x.type===t)||{}).value;
const when=process.env.WHEN||(g('year')+'-'+g('month')+'-'+g('day')+' '+g('hour')+':'+g('minute'));
const which=process.argv[5]||'main';
if(which==='list'){process.stdout.write(JSON.stringify((store.budgets||[]).map(b=>({id:b.id,name:b.name,sheetId:b.sheetId||null}))));process.exit(0);}
const opt=which==='main'?{main:true}:{budget:which};
process.stdout.write(JSON.stringify(buildSheets(store,calc,process.argv[3]||'Daily backup',when,JSON.parse(process.argv[4]||'[]'),opt,JSON.parse(process.argv[6]||'{}'))));

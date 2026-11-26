# Daily backup scheduled task (Claude) — and its AWS twin

The live artifact is backed up every night by a **Claude scheduled task** ("Daily calculator backup",
id `trig_01CxgMgXFeY3u2jomGeCi1fi`). In the AWS build the same job is the `DailyBackupFunction` Lambda
(`api/src/backup.mjs`), triggered by EventBridge Scheduler with the same schedule.

| Setting | Value |
|---|---|
| Schedule | `CRON_TZ=America/Edmonton 37 22 * * *` (every day 22:37 Edmonton) |
| Connectors | Google Sheets, Google Drive, Claude Docs, Claude Code Remote |
| Permission mode | auto (runs without approvals) |
| Model | claude-opus-5-5 |
| Persistent session | no (fresh session each run) |
| Notifications | none |

It extracts the ENGINE / BACKUP / SHEETS sections from the live artifact HTML (markers `/*ENGINE*/…/*END*/`,
`/*BACKUP*/…/*ENDBACKUP*/`, `/*SHEETS*/…/*ENDSHEETS*/`), so builder changes in the app propagate automatically and the
prompt never needs to change when the sheet layout changes.

## Prompt (verbatim; ids replaced by placeholders)
Placeholders: `<ARTIFACT_SLUG>` = the artifact's slug, `<MASTER_SHEET_ID>` = retired master sheet,
`<INVOICE_SHEET_ID>` = the team's invoice sheet, `<BACKUP_FOLDER_ID>` = backup Drive folder. Real values are in the
team's private config (`config/private.json`, never committed) — see [config.md](config.md).

````text
Daily backup of the "Project profit calculator" artifact (slug <ARTIFACT_SLUG>) to Google Sheets. Each budget has its OWN Google Sheet. There is NO master sheet: never write to spreadsheet <MASTER_SHEET_ID>, and never touch <INVOICE_SHEET_ID> (the team's own invoice sheet, read-only forever). Do not change the artifact. NEVER delete any tab except the six data tabs (Summary, Budget, Trade, Material, Service, Other) and their " (updating)" copies; "To check", "Read me", "Backup log", "Backup data" and any other tab must be left alone.

Steps:
1. Read the artifact with read_artifact (all parts, using offset/limit if needed) and save the exact HTML to page.html. Write this runner to plan2.js:
```
const fs=require('fs');const h=fs.readFileSync(process.argv[2],'utf8');
const calc=new Function(h.split('/*ENGINE*/')[1].split('/*END*/')[0]+';return calc;')();
const src=h.split('/*BACKUP*/')[1].split('/*ENDBACKUP*/')[0]+h.split('/*SHEETS*/')[1].split('/*ENDSHEETS*/')[0];
const buildSheets=new Function(src+';return buildSheets;')();
const store=JSON.parse(h.split('<script id="store" type="application/json">')[1].split('</script>')[0]);
const f=new Intl.DateTimeFormat('en-CA',{timeZone:'America/Edmonton',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(new Date()),g=t=>(f.find(x=>x.type===t)||{}).value;
const when=process.env.WHEN||(g('year')+'-'+g('month')+'-'+g('day')+' '+g('hour')+':'+g('minute'));
const which=process.argv[5];
if(which==='list'){process.stdout.write(JSON.stringify((store.budgets||[]).map(b=>({id:b.id,name:b.name,sheetId:b.sheetId||null,savedAt:store.savedAt}))));process.exit(0);}
process.stdout.write(JSON.stringify(buildSheets(store,calc,process.argv[3]||'Daily backup',when,JSON.parse(process.argv[4]||'[]'),{budget:which},{})));
```
2. Run `node plan2.js page.html "Daily backup" '[]' list` to get the budgets. For each budget, find its sheet: use sheetId if set; otherwise Google Drive search_files with query `parentId = '<BACKUP_FOLDER_ID>' and title = '<budget name> – backup' and trashed = false` (en dash); otherwise create it with Google Drive create_file {title:'<budget name> – backup', contentMimeType:'application/vnd.google-apps.spreadsheet', parentId:'<BACKUP_FOLDER_ID>'}.
3. Skip check per sheet: get_values 'Backup log'!A1:G on that sheet (ignore errors if the tab doesn't exist). If the last dated row's time (column A, Edmonton time "YYYY-MM-DD H:MM") is less than 2 hours old, skip that budget (someone just saved). If column G of that row equals the store savedAt, nothing changed: skip too.
4. Otherwise: get_spreadsheet with fields ["sheets.properties.sheetId","sheets.properties.title"], pass the list of {sheetId,title} as JSON to `node plan2.js page.html "Daily backup" '<existing>' <budgetId>` and parse the output plan {structure, perTab, finalize, log, data}.
5. Write (safe swap, so a failure never leaves empty tabs): if plan.structure is non-empty, update_spreadsheet with requests=plan.structure (this adds hidden "<tab> (updating)" tabs). For each perTab entry t: update_values of t.values to range "'<t.title>'!A1:<lastcol><rows>" in chunks of 250 rows, then update_spreadsheet with t.requests in chunks of 400. Then get_values "'Summary (updating)'!A2" and confirm it is not empty (if empty, stop for this budget; the old tabs are still intact). Then get_spreadsheet again and call update_spreadsheet with: a deleteSheet for each current tab whose title is exactly one of the perTab t.final values (Summary, Budget, Trade, Material, Service, Other), followed by every request in plan.finalize that is NOT a deleteSheet. Then get_values 'Summary'!A2 and confirm it contains the backup time. Then append_values plan.data to 'Backup data'!A1 and plan.log to 'Backup log'!A1 on that same sheet.
6. If a Google call fails with a temporary error, wait and retry up to 3 times. Finish with one short line per budget: backed up / skipped (why) / failed (why, and which step), plus the sheet link https://docs.google.com/spreadsheets/d/<id>/edit. If a sheet had to be created, say so and remind the team to click Back up now or Save for team in the calculator so it remembers the new sheet.
````

The runner above is also kept as `tools/artifact/plan2.js` (the older variant used by the coordinator, with a `main`
option and a files map argument).

## Re-creating the task
In a Claude Code session with the Claude Code Remote connector: create a scheduled task named "Daily calculator backup",
cron `CRON_TZ=America/Edmonton 37 22 * * *`, connectors Google Sheets + Google Drive (+ Claude Docs, Claude Code Remote),
permission mode auto, and paste the prompt above with the real ids filled in.

## AWS twin (`DailyBackupFunction`)
Same steps without an AI in the loop: reads `store/store.json` from the data bucket and the deployed `index.html` from the
site bucket (engine markers), runs `buildSheets` with source `Daily backup`, applies the same skip rules and safe swap
through the same write guard, retries temporary Google errors (0/2/6/15 s), logs one JSON line per budget and **fails the
invocation** (→ CloudWatch alarm → email) if any budget failed. It never changes the store; a newly created sheet is
reported in the log ("click Back up now or Save for team so it stores the sheet id"). Manual run:
`aws lambda invoke --function-name <DailyBackupFunctionName> out.json && cat out.json`.

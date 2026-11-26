# Architecture

The product is **one self-contained HTML file** (`app/artifact/index.html`, ~540 KB): CSS, markup, all JavaScript and the
team's data (`<script id="store" type="application/json">`). It runs in two hosts with the same code:

| | Claude artifact (original, live today) | Standalone / AWS (this repo) |
|---|---|---|
| Page | published artifact HTML | `app/standalone/index.html` on S3 + CloudFront |
| Data | embedded store; **Save for team** republishes the whole page | `GET/PUT /api/store` → S3 `store/store.json` (versioned, ETag `If-Match`) |
| Host API | `window.claude.use('artifact'|'downloads'|'mcp')` | `platform.js` implements the same three objects |
| Google Sheets / Drive | Claude connectors (`mcp.callTool('Google Sheets', …)`) | `POST /api/mcp` → Lambda → Google REST with a service account, behind a write guard |
| Sign-in | Claude account + artifact sharing | Cognito user pool (hosted UI, code + PKCE), JWT authorizer on the HTTP API |
| Daily backup | Claude scheduled task, 22:37 Edmonton | EventBridge Scheduler → Lambda, 22:37 America/Edmonton |

## Code map of the single file
```
<head> <style> … design system, page CSS, story blocks (Scope A/B, upgrades, To check, QA) … </style>
<body> header (brand, pickers, save state, tabs) · sections #v-inputs #v-builder #v-investors #v-breport #v-budget #v-tocheck
       modals (#modal #dmodal #qmodal #chmodal #cmodal #vmodal #pmodal #mvmodal #tmodal #bkmodal #tcleave #busy) · #toasts
<script id="store" type="application/json"> { v:4, … } </script>
<script> {                                   // one block scope
  formatting + ranges (Rg, mkR, mergeR)
  /*ENGINE*/ function calc(p, co) … /*END*/                      → docs/logic/01-calc-engine.md
  /*BACKUP*/ function buildBackup(…) … /*ENDBACKUP*/             → docs/logic/07-backups-sheets.md
  /*SHEETS*/ function buildSheets(…) … /*ENDSHEETS*/
  template + migrate() + upgrades helpers + budFigs/resolveBudget/effP     → 03, 04
  load store / device draft · persist / markDirty                          → 06
  Inputs form, sidebar, Builder, Investor, /*BREPORT*/ report + PDF /*ENDBREPORT*/ → 02
  Budget page, upgrades UI, Backups (sheetsCall, writePlan, sheetFor, writeBackup, sync, restore) → 03, 04, 07
  saveTeam, budget actions, invoices & payments, move, item types (saveTypes, tReopen) → 03, 06
  dialogs, guard, routing, diffStores / nbar                               → 06, 08
  To check (tc*)                                                           → 05
  boot: route(); buildForm(); markDirty(); tReopen(); claude.use(...)
} </script>
```
The markers `/*ENGINE*/ /*END*/ /*BACKUP*/ /*ENDBACKUP*/ /*SHEETS*/ /*ENDSHEETS*/` are an interface: the daily backup
(Claude task and Lambda) cuts those functions out of the live page with `new Function(...)`.

## System diagram (AWS)
```mermaid
flowchart LR
  U[Team browser] -->|HTTPS| CF[CloudFront<br/>PriceClass_100]
  CF -->|/* OAC| S3S[(S3 site bucket<br/>index.html, platform.js, config.js)]
  CF -->|/api/* + Authorization| API[API Gateway HTTP API<br/>JWT authorizer]
  U -->|hosted UI, code + PKCE| COG[Cognito user pool]
  API --> L[Lambda api<br/>Node, arm64]
  L -->|GET / PUT If-Match| S3D[(S3 data bucket, versioned<br/>store/store.json)]
  L -->|GetParameter| SSM[(SSM SecureString<br/>Google credentials)]
  L -->|Sheets v4 / Drive v3<br/>write guard| G[Google backup sheets<br/>one per budget]
  EB[EventBridge Scheduler<br/>22:37 America/Edmonton] --> LD[Lambda daily backup]
  LD --> S3D
  LD -->|reads engine markers| S3S
  LD --> SSM
  LD --> G
  L & LD --> CW[CloudWatch logs + alarms] --> SNS[SNS email]
  BUD[AWS Budget] --> SNS
```

## Save (optimistic concurrency)
```mermaid
sequenceDiagram
  participant App as App (unchanged code)
  participant P as platform.js
  participant API as /api (Lambda)
  participant S3 as S3 store.json
  App->>P: claude.use('artifact').publish(html with store JSON)
  P->>P: extract <script id="store"> JSON
  P->>API: PUT /api/store {store, baseVersion: ETag from load}
  API->>S3: PutObject If-Match: baseVersion
  alt nobody saved since
    S3-->>API: 200 new ETag
    API-->>P: {version}
    P-->>App: ok → "Saved for the team"
  else someone saved first
    S3-->>API: 412 PreconditionFailed
    API-->>P: 409 {code:'conflict'}
    P-->>App: throw {code:'conflict'} → "Someone saved at the same time. The page reloads to their version."
    P->>P: reload after 2.5 s (device draft becomes a "stale draft" with Download)
  end
```

## Back up now / Save for team backup
```mermaid
sequenceDiagram
  participant App
  participant G as Google (via connector or /api/mcp)
  App->>G: find sheet (budget.sheetId / Drive search in folder / create)
  App->>G: get_spreadsheet (tabs)
  App->>App: plan = buildSheets(store, calc, source, when, tabs, {budget})
  App->>G: update_spreadsheet(structure)  -- hidden "<Tab> (updating)" tabs
  loop each tab
    App->>G: update_values (250 rows/call) + update_spreadsheet formats (400/call)
  end
  App->>G: get_values 'Summary (updating)'!A2  (must not be empty)
  App->>G: update_spreadsheet: delete old data tabs + rename/unhide new ones (one call)
  App->>G: get_values 'Summary'!A2 (must show this backup time)
  App->>G: append_values 'Backup data' (full JSON restore point), 'Backup log'
```

## Data flow of a number
`input` event → `set(path)` → `persist()` (device draft) → `refresh()` → `effP(P())` (linked budget total via
`budFigs`) → `calc()` twice (low/high ranges) → `mergeR` → renderers (sidebar, Builder, reports) → Save for team →
backup sheet + team copy.

## Cost (AWS, ca-central-1, internal use: ~5 users, ~1 MB store, a few hundred saves/backups a month)
| Service | Usage | Monthly |
|---|---|---|
| CloudFront | < 1 GB, < 100k requests (always-free tier: 1 TB + 10M requests) | $0 |
| S3 site + data | < 50 MB incl. 1 year of store versions, few thousand requests | ~$0.01–0.05 |
| API Gateway HTTP API | ~20k requests ($1.00 per million; first 1M free in year 1) | ~$0.02 |
| Lambda arm64 | ~20k invocations, < 2k GB-s (free tier 1M req + 400k GB-s, permanent) | $0 |
| Cognito Lite | < 10 users (first 10,000 MAU free) | $0 |
| SSM Parameter Store | 1 standard SecureString (aws/ssm key) | $0 |
| EventBridge Scheduler | 30 invocations (14M free) | $0 |
| CloudWatch Logs | < 100 MB, 30/90-day retention (5 GB free) | $0 |
| AWS Budgets / SNS email / 2 alarms | 2 budgets free, 10 alarms free | $0 |
| **Total** | | **≈ $0.05 – $1 / month** (no NAT, no RDS, no always-on compute) |
Without the free tier the same usage stays under ~$1–2/month. The budget alarm (default $5) catches surprises.
The estimate is per environment (a `dev` stack with the samconfig defaults costs about the same or less: no daily backup,
7/14-day logs, 30-day store versions). All settings above (price class, retention, memory, schedule, budget) are template
parameters: [operations.md](operations.md#parameters). Split the bill with the `App` / `Env` / `CostCenter` tags.

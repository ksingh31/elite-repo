# Data model (store v4)

Formal schema: [`schemas/store.schema.json`](../schemas/store.schema.json) (JSON Schema 2020-12; the sample store and the
team's real store both validate). Made-up example: [`samples/store.sample.json`](../samples/store.sample.json) —
same shape as the real data (5 projects covering every financing option, one budget with 55 lines, ~380 invoices and
~340 payments) with all names, vendors, invoice numbers, notes and amounts invented. **Never commit the real store.**

Rules: the store only ever changes **additively**. Old data without a new field must load and calculate exactly as
before; `migrate()` fills what is missing at load time without rewriting saved values.

## Tree
```
store
├─ v: 4                       format version (drafts / restore points with another v are refused)
├─ savedAt: ISO | null        set on every Save for team; drafts load only when draft.base === savedAt
├─ cur, curBudget             selection when saved (each device also keeps its own view)
├─ company {…}                defaults copied into new projects
├─ projects[]                 ≥ 1
│   ├─ id, name, sell, lot, build, lawyer, buildGst, sale 'hd'|'both', taxWait, taxOv|null, ohOv|null
│   ├─ preBuild[,preBuildMax], buildMonths[,buildMonthsMax], close[,closeMax]   timing (+ optional "to" range)
│   ├─ use 'lot'|'ap'|'priv'|'cp'|'cash'                                          selected financing
│   ├─ lotLoan {ltv, rate, months, loans[]}         A Lender (also the lot part of A Lender + Private)
│   ├─ sched {before, draws[]}                      A Lender + Private draw schedule
│   ├─ ap {lotMonths, ltv, fee, rate, loans[]}      A Lender + Private draw mortgage
│   ├─ priv {ltv, fee, rate, first, ms[], loans[]}  Private
│   ├─ cp {base 'lb'|'build', ltv, fee, rate, mode 'pct'|'amt', draws[{at, v}], loans[]}   Cash + Private
│   ├─ extras[{label, amount, up}]   investors[{name, amount}]
│   ├─ co {…company}                project's own rates / overhead
│   └─ budget {use, id, ver 'latest'|versionId, src 'proj'|'budget'|'inv'|'manual', manual, cont}
├─ budgets[]
│   ├─ id, name, sheetId?           its own Google backup sheet
│   ├─ toCheck? {'r<row>': {vendor, label, ops[], by, at, py?}}   reversible To check resolutions
│   └─ versions[]                   oldest → newest; last = current
│       ├─ id, label, date, note, above (sq ft), base (basement sq ft), rate (basement $/sq ft), cats[]
│       └─ items[]
│           ├─ id, cat, name, amt (base), act (invoiced), note, done?
│           ├─ invs[{id, vendor, no, date, kind 'Trade'|'Material'|'Service'|'Other', amt, note, est?}]
│           ├─ pays[{id, date, method, amt, ref, inv: invoiceId|null, deposit?}]
│           └─ ups?[{id, name, amt, yes, by 'Buyer'|'Builder', status 'Quoted'|'Approved'|'Declined', note}]
└─ catalog[{cat, items[]}]          item types per category (Manage item types)
```

## Field notes
| Field | Meaning / rule |
|---|---|
| `company.ohMode` | `calc` = (salary·(1+raise)+office+misc)/projects, `flat` = ohFlat. migrate default `{ohMode:'calc', ohFlat:50000}` |
| rates | always fractions (0.05 = 5 %). Percent inputs divide by 100 |
| `project.build` | typed build cost incl. GST (when buildGst). Ignored (kept) while `budget.use` |
| `project.budget` | migrate default `{use:false, id:null, ver:'latest'}`; new links `src:'proj'`; absent src = budget estimate |
| `project.cp` | migrate default `{base:'lb', ltv:0.65, fee:0.03, rate:0.0702, mode:'pct', draws:[{at:3,v:0.3333},{at:6,v:0.3333},{at:9,v:0.3334}], loans:[]}` |
| `project.priv.first / ms` | migrate defaults 200000 / [0.3, 0.6, 1] |
| `project.ohOv` | migrate adds `null` when absent |
| `project.co` | migrate: `{...store.company, ...p.co}` |
| `item.act` | equals round2(Σ invs.amt) whenever the line has invoices (re-synced after every invoice change); typed otherwise |
| `item.pays / invs` | migrate ensures arrays |
| `item.done` | finished: projected uses invoiced |
| `item.ups` | optional; deleted when empty |
| `invoice.amt` | negative = refund / credit |
| `payment.method` | one of Cheque, E-transfer, Visa, Mastercard, Amex, Debit, Cash, Refund / credit, Other, Not recorded |
| `payment.inv` | linked invoice id or null ("not tied to an invoice") |
| `budget.sheetId` | set by the first backup that finds/creates the sheet (then Save for team to remember it) |
| `catalog` | migrate builds it from the template when missing and adds every category / item name used by any version |

## Defaults for new things
* New project: copy of company defaults; `sched {before:4, draws:[0.3333,0.3333,0.3334]}`, `lotLoan {ltv:0.8, rate:0.04,
  months:18}`, `ap {lotMonths:6, ltv:0.65, fee:0.03, rate:0.0702}`, `priv {ltv:0.65, fee:0.04, rate:0.0902, first:200000, ms:[0.3,0.6,1]}`.
* New budget: `{id, name:'New budget', versions:[blankVersion()]}`; blank version = every catalog item at 0, `rate:120`.
* New line: first unused item type of that category, `{amt:0, act:0, note:'', pays:[]}`.
* New upgrade: `{name, amt, yes:false, status:'Quoted', by:'Buyer', note:''}`.

## Where the store lives
* Artifact: inside the page (`<script id="store">`, `<` escaped as `<`). `tools/store_tool.py extract|inject`.
* AWS: `s3://<data bucket>/store/store.json` (versioned; every save is a version, kept 365 days).
* Every backup: full JSON in the budget sheet's `Backup data` tab (40,000-character parts) = restore points.
* Device: drafts in localStorage (see [logic/06-save-drafts-undo.md](logic/06-save-drafts-undo.md)).

# 7. Google Sheets backups, restore points, sync check, daily backup

**Permission rule (standing):** every sheet the team provided is an ORIGINAL and READ-ONLY. The only sheets ever written
are the calculator's own backup sheets: **one Google Sheet per budget**, named `<budget name> – backup` (en dash), inside
the backup Drive folder (`BACKUP_FOLDER` constant in the app; placeholder `YOUR_BACKUP_FOLDER_ID` in this repo). The
invoice sheet and the retired master sheet are never written (`TC_RO`, and the server deny list in the AWS build). There
is no master backup sheet any more (`opt.main` code path is kept but unused).

## 7.1 When backups run
* **Save for team** → backs up every budget first (failure = warning only, save continues).
* **Back up now** (Backups window) → every budget, includes unsaved changes ("This includes your unsaved changes").
* **Daily** at 22:37 America/Edmonton: Claude scheduled task ([../daily-backup-task.md](../daily-backup-task.md)) or, in
  the AWS build, the EventBridge Scheduler Lambda (`api/src/backup.mjs`). Skips a budget whose last log row is < 2 h old
  or whose log column G equals the store `savedAt` (nothing changed).

## 7.2 Pure builders (shared by app, daily task and Lambda)
`buildBackup(store, calc, source, when)` between `/*BACKUP*/ … /*ENDBACKUP*/` and
`buildSheets(store, calc, source, when, existing, opt, files)` between `/*SHEETS*/ … /*ENDSHEETS*/`.
`when` = Edmonton time `YYYY-MM-DD HH:MM` (`edmNow()`), `existing` = `[{sheetId, title}]` of the target sheet,
`opt = {budget: id}`. Output `{structure, perTab, finalize, log, data, head, tabs}`.

`buildBackup` also computes per-project rows (name, option, sell, net sell, lot, build, budget source, ranges, sale type,
overhead, cost, profit before financing, investor return lo/hi annualized, financing, profit, cash, ROI, investor cash and
earnings), investors, budgets/items/payments/invoices tables (with SUMIFS formulas) for the historical full-workbook
layout; today only `log` and `data` of it are used by the per-budget sheets:
* `log` row: `[when, source, #projects, #budgets, #payments, json length, store.savedAt]` → **Backup log** tab
  (header: When, What triggered it, Projects, Budgets, Payments, Data size (characters), Calculator saved at).
* `data` row: `[when, source, partsCount, part1, part2, …]` = the **whole store JSON** split in 40,000-character parts →
  **Backup data** tab (a restore point; header When, What triggered it, Parts, Data part 1…9).

Text cells that start with `= + - @` are prefixed with `'` (`txt`) so Sheets never treats them as formulas; `uv()` also
quotes numeric-looking strings / leading zeros, keeps `YYYY-MM-DD` and `=HYPERLINK(`.

## 7.3 Per-budget sheet layout (latest version only)
Tab order after a backup: `Read me` (sheet id 0, renamed from Sheet1), `Summary`, `Budget`, `Trade`, `Material`,
`Service`, `Other` (type tabs only when they have rows), then any other tabs (To check, the team's own tabs), hidden
`Backup log`, `Backup data`.

**Summary** (teal): title = budget name; sub line "Project: <linked projects> · latest version vN (date) · last backup
<when>. Made from the calculator; anything typed here is replaced at the next backup." (row 2 — used to verify a backup);
big tiles Total amount invoiced / Total amount paid / Balance due / Budget (with upgrades when any) / Invoiced vs budget;
**Budget and upgrades** tiles (only with upgrades): Budget base, Upgrades (Yes), Budget total (incl. upgrades), Projected
final cost (incl. upgrades), Upgrades set to No (not counted); **By type** table (Type, Invoices, Total, Paid, Balance + All
types); **By category** (without upgrades: Category, Budget, Total invoiced, Amount paid, Balance due, Variance; with
upgrades: Category, Budget base, Upgrades (Yes), Budget (with upgrades), Total invoiced, Amount paid, Balance due,
Variance (invoiced − budget with upgrades), Projected final cost) + Total; **Upgrades** section (with upgrades): Category,
Budget line, Upgrade, Requested by, Status, Added to total, Price, Counted in budget, Note, total row "All upgrades (n) … n
Yes", No rows greyed; **Payments by method** (Method, Payments, Amount + All methods).

<a id="budget-tab"></a>**Budget** (navy, frozen row 1 + column 1): columns A–J = Item, Budget (header "Budget (lines: base, ↳
upgrades, line total)" when upgrades exist), Actual invoiced, Variance, Variance %, Amount paid, Balance due, Invoices,
Notes, Item id (don’t edit). Per category: a group row (category, Σ line totals, invoiced, variance, %, paid, balance,
"N items"), then per line:
* no upgrades: one row `    <name>` with base budget, invoiced, variance, %, paid, balance, #invoices, note, **item id**.
* with upgrades: `    <name> (base)` row (base in B, #invoices, note, item id), one italic sub-row per upgrade
  `   ↳ Upgrade: <name> (<by> · <status> · Yes|No)` (+ ` – $x not added` when No; B = price when Yes, 0 when No; I = note;
  **J = `up:<itemId>:<upgradeId>`**; No rows grey), then a bold `    Line total: <name> (base + Yes upgrades)` row with line
  total, invoiced, variance, %, paid, balance and **J = `sub:<itemId>`**.
* Final `Total` row: Σ line totals, invoiced, variance, %, paid, balance, #invoices. Conditional formats: variance > 0.5
  red, balance due > 0.5 bold red. Money `$#,##0.00;-$#,##0.00;"-"`, percent `0.0%`.

**Trade / Material / Service / Other** (one per invoice `kind`, colour per type, frozen 5 rows): title + filter hint,
totals block (Total amount, Amount paid, Balance due, Invoices), header (Category, Name, Invoice no., Date, Total amount,
Amount paid, Balance due, Mode of payment, Notes, Row id (don’t edit)) with a basic filter, rows grouped by budget line in
category order (group row "<line> · N invoices" with sums), invoices sorted by date. Row id = invoice id, or `pay:<id>` for
payments not tied to an invoice ("<ref> (no invoice)", negative balance, note "Deposit or payment not tied to an invoice",
placed in the line's first invoice kind). Mode of payment = methods/refs of the linked payments (`mode()` merges method
and reference sensibly); Notes = invoice note unless it repeats the mode/ref.

**Read me** (A1:B8): what this is, what each tab means, when it updates, last backup.

## 7.4 Safe swap (`writePlan`) — a failure never leaves empty tabs
1. `structure`: delete leftover `… (updating)` tabs of ours, rename sheet 0 to `Read me`, add every new tab hidden as
   `<Tab> (updating)` (sheet ids chosen to avoid existing ones: base id + 5000*n), add `Backup log` / `Backup data` (hidden,
   2000×12) when missing (+ their header rows).
2. For each `perTab`: `update_values` in chunks of **250 rows** (`'<title>'!A<r>:<lastCol><r+n-1>`), then the formatting
   requests in chunks of **400** (`repeatCell`, `updateBorders`, `updateDimensionProperties`, `setBasicFilter`,
   `addConditionalFormatRule`, all with remapped sheet ids).
3. Check `'Summary (updating)'!A2` is not empty (else stop: old tabs are intact).
4. Re-read tabs; if a staged tab is missing ("another backup ran at the same time") stop.
5. ONE `batchUpdate`: `deleteSheet` for the current tabs named exactly Summary/Budget/Trade/Material/Service/Other, then
   every `finalize` request except deletes (rename staged tabs to final names, unhide, order them from index 1, move other
   tabs after them).
6. Verify `'Summary'!A2` contains `when`; append `data` to `'Backup data'!A1` and `log` to `'Backup log'!A1`.
Only these six data tabs (and their "(updating)" copies) are ever deleted. "To check", "Read me", "Backup log", "Backup
data" and any team tab are left alone.

Sheet discovery (`sheetFor(b)`): `b.sheetId`, else Drive search `parentId = '<folder>' and title = '<name> – backup' and
trashed = false`, else `create_file` (Google Sheet in the folder). A new id is stored on the budget (unsaved change: "click
Save for team so the calculator remembers it").

Error text (`bkErr`) maps connector errors to plain words (connector not available, needs reconnect, etc.). Retries:
0 / 2 / 6 / 15 s, not for permanent errors (`server_not_connected|needs_reauth|denied|not_granted|consent`,
`invalid request|no sheet with|no grid with|already exists|duplicate`).

## 7.5 Backups window (`#bkmodal`)
Budget picker, Open sheet ↗ (or "No sheet yet"), **Back up now**, message line, **Restore points** list (last 30 rows of
`Backup data` with a date in A, newest first, "Latest" tag, source) each with a primary **Restore this copy** button →
confirmation (see 6.6). **Bring changes back from the sheet** (sync check).

## 7.6 Sync check (`syncCheck` / `syncApply`) — edits made in the backup sheet
Reads `Budget!A1:J400`, `Summary!A2`, `Backup log!A1:G`, each type tab `A1:J2000`, the spreadsheet title.
* Refuses old sheets without row ids (type tab header column J not "Row id").
* Budget tab rows whose J is an item id: amount (B) differs → `item-amt`; note (I) differs → `item-note`. Rows with J
  `up:…` / `sub:…` are made by the calculator and **never read back**.
* Type tab rows with an invoice id: vendor / invoice no. / date / amount / type (tab) / notes differences → `inv-upd`;
  paid (F) differs → `inv-paid` (adds a payment of the difference, method "Refund / credit" if negative else "Not recorded",
  ref "From project sheet"). Rows with `pay:` ids are skipped; group rows ("N invoices") skipped.
* Rows without id with an amount → `inv-new` (needs a budget line named like column A; otherwise flagged and not tickable).
* Invoices in the calculator not found in any type tab → `inv-del` (unticked by default).
* If the sheet's last log "Calculator saved at" is older than the store's `savedAt` (stale sheet) or there are > 40
  differences, nothing is pre-ticked and a warning explains why. "Compared with <sheet title> (last backup <when>)".
* Apply selected → changes are unsaved edits; `act` recomputed on touched lines.

## 7.7 Server-side guard (AWS build)
`api/src/guard.mjs` enforces the same rules for every write coming through `/api/mcp` and for the daily Lambda: deny list
always wins; target must be in the backup folder (Drive parent check) or the explicit allow list; only the request types
above; `deleteSheet` only for the six data tabs (or their "(updating)" copies); To check only one K:L row; Backup data / log
append-only; `create_file` only as a Google Sheet in the backup folder.


Designs (budget.designs) are not written to the backup sheet as their own tab: only the six data tabs may be deleted
by a backup, so the calculator adds no new builder-owned tabs. Designs are kept in the store (and the S3 store versions).

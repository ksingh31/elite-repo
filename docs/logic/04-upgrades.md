# 4. Upgrades (Pattern A: inline rows under the budget line)

Story: `stories/upgrades_story.md`; approved mockup: `mockups/upgrades_mockup.html`.

## Data
`item.ups = [{id, name, amt, yes, by: 'Buyer'|'Builder', status: 'Quoted'|'Approved'|'Declined'|'', note}]`, stored on the
version's items (per version). Optional and additive: old data without `ups` loads and calculates exactly as before; the
array is deleted (not left empty) when its last upgrade is removed. New version copies them (structuredClone of the source
version); older versions keep theirs.

## Rules
* **Yes** adds `amt` to the line; **No** adds $0 (kept as a greyed record).
* Switching to Yes turns `Quoted` into `Approved`; picking `Declined` sets No. Quoted + Yes counts.
* `lineTot = amt + Σ yes amounts`. Everywhere the base was used, the line total is used: category totals, tiles
  (Budget total shows "$base base + $ups upgrades"), Budget total, Projected (per line `max(lineTot, act)`, finished →
  `act`), Over/under (`act − lineTot`), and the build cost sent to projects for **all** sources (budFigs uses lineTot).
* Buyer upgrades do **not** change the sale price (open question for the team). No markup.
* New upgrade defaults: `{name, amt, yes:false, status:'Quoted', by:'Buyer', note:''}`.

## UI
* Line shows Base, a "+ Upgrade" control or a chip "N · +$X" (count, Yes total; `upChip`), Line total. Expand → upgrades
  panel (`upPanel`) with rows: name, price (money with commas), Yes/No, Requested by, Status, Note, remove. The panel stays
  open after deleting the last upgrade; alignment identical for lines with zero or several upgrades.
* Summary card above the table: "N upgrades on M lines · Approved / Quoted / Declined" (`upSummary`).
* "Show upgrades" toggle: off = compact table where the budget column shows the line total with "incl. +$X upgrades".
* Version compare shows the line-total change and upgrade changes (`upCmpCap`: added / removed / changed).
* "See what changed" lists upgrade changes in plain words, e.g. `new upgrade “Triple-pane upgrade” +$4,200.00 (Yes)`.
* Edits are normal unsaved changes. They use `persistClean()`: if an edit brings the store back to exactly the saved
  version (e.g. add then delete an upgrade) the page is clean again (no "Edited" tag).

## In the Google Sheet backup (Budget tab)
See [07-backups-sheets.md](07-backups-sheets.md#budget-tab): line row "(base)", one "↳ Upgrade" sub-row per upgrade
(price when Yes, 0 and greyed "– $x not added" when No; column J `up:<item>:<upgrade>`), then a bold "Line total: … (base + Yes
upgrades)" row (column J `sub:<item>`) carrying invoiced / variance / paid / balance. The sync check ignores `up:`/`sub:` rows.
Restore points (`Backup data`) hold the full JSON, so restore round-trips upgrades exactly.

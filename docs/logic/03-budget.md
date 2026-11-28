# 3. Budget page, budget figures, invoices and payments, move entries, item types

## 3.1 Model recap
`store.budgets[] → versions[] (oldest first; last = current, editable; older = locked) → items[]`. Each item:
`amt` base budget, `act` invoiced, `invs[]`, `pays[]`, optional `ups[]` (upgrades, [04-upgrades.md](04-upgrades.md)),
optional `done` (finished). See [../data-model.md](../data-model.md).

Helpers: `upYes(i)` = Σ amt of upgrades with `yes`; `lineTot(i) = amt + upYes(i)`; `vTotal(v) = Σ lineTot`;
`paid(i) = Σ pays.amt`; `syncAct(it)`: when a line has invoices, `act = round2(Σ invs.amt)` (lines without invoices keep a typed `act`).

## 3.2 Budget figures — `budFigs(v, cont)`
```
for each item i:  a = lineTot(i); x = +i.act
  est += a; inv += x
  if x > a + 0.005: over += x − a; overN++
  if i.done: proj += x                       // finished lines use what was invoiced
  else:      proj += max(a, x); left += max(0, a − x)
contingency = left * cont
return {est, inv, proj: proj + contingency, left, over, overN, cont: contingency}
```
* **Budget estimate** = `est`, **Invoiced so far** = `inv`, **Projected final cost** = `proj` (+ contingency),
  **Finished** lines: projected uses invoiced; **Over budget** = lines invoiced above their line total.

## 3.3 Build cost sources (project ↔ budget link)
`project.budget = {use, id, ver:'latest'|versionId, src, manual, cont}`. `resolveBudget(p)` → `{bud, v, total, figs, src, latest}`
or `{missing:true}` when the budget was deleted:
| `src` | label (`SRCNAME`) | total |
|---|---|---|
| `proj` (default for new links) | Projected | `figs.proj` (incl. contingency `cont`) |
| `budget` (default when absent) | Budget estimate | `figs.est` |
| `inv` | Invoiced so far | `figs.inv` |
| `manual` | Entered by hand | `+manual` if a number, else `figs.proj` |

`effP(p)` = `{...p, build: total}` whenever linked (the typed `p.build` is kept underneath). Linking from the Budget page
(`b-link`) sets `{use:true, id, ver:'latest', src:'proj'}`; unlinking (`b-unlink`) or deleting the budget copies the current
total into `p.build` (rounded to cents) so the project's numbers don't jump. The Inputs build field shows the source radio
group, version picker (latest or pinned), contingency %, manual amount, an "Open budget" link and a warning when the
estimate is below what is already invoiced ("Consider Projected").

The backup's `buildBackup.resolve` repeats this logic (upgrades included) for the Projects tab.

## 3.4 Budget page (`#v-budget`, `renderBudget`)
* **Toolbar** (`#budbar`): budget picker `#bsel`, Rename budget, New budget (from template `BTEMPLATE`: 7 categories,
  52 items, amounts blank), Duplicate (new budget with a copy of the latest version), Delete budget (typed confirm; linked
  projects switch to a typed build cost), Open Google Sheet (`#bsheet`, when `sheetId`), Backups.
* **Version row**: version picker (`b-view`), Compare with (`bcmp`; previous version by default, or none), New version
  (modal `#vmodal`: label `vN`, date, "What changed" note, copy from any version → becomes latest, projects on "latest"
  follow it), Delete version (latest only, typed confirm; projects pinned to it go back to latest), Link project select +
  button (same height as the select), Manage item types.
* **Tiles**: Budget total (vN) (with "base + upgrades" sub line), Change from <compare>, Invoiced so far, Paid so far,
  Still owed on invoices, Projected final cost, Per sq ft above grade = `(total − base*rate)/above`, Per sq ft all floors =
  `total/(above+base)` (version fields `above` sq ft, `base` basement sq ft, `rate` basement $/sq ft, default 120).
* **Upgrades summary card** (when any) and **To check banner** (when the sheet has open rows).
* **Table** grouped by category (collapsible `b-toggle`): Item (item-type select limited to unused names of that
  category + "New item type…"), Budget (money input), [Upgrades chip / Line total when "Show upgrades"], Invoiced (button →
  Invoices & payments window, shows count; typed when no invoices), Over/under (`act − lineTot`, with %), Paid / owed
  (`Paid in full` / `$x owed` / `$x overpaid`), Finished checkbox (compact, only the box clickable, hint "finished lines use
  the invoiced amount in Projected"), Notes, delete. Changed rows (vs saved) get a marker. Compare mode shows the other
  version's values and up/down arrows. Category subtotal rows. Add item per category (`b-additem` picks the first unused
  type or opens the new-type input), Add category (`#bnewcat`).
* Older versions are read only (no inputs).
* Table fits at ~1300 px with upgrades + invoices shown (columns reflow; Notes not cut off). Phones: rows become cards.

## 3.5 Invoices & payments window (`#pmodal`, `renderPay`)
Per line: header totals (invoiced, paid, owed), "By type" chips (Trade / Material / Service / Other), invoice cards
(vendor with autocomplete from all vendors, invoice no., date, type, amount, note; paid status `PAID` / `$x DUE`),
per-invoice **Pay** (pre-selects the invoice; amount placeholder = remaining; "Pay the rest" `#pn-rest`), payments list
(date, method from `METHODS`, amount, reference, linked invoice or "not tied to an invoice"), add invoice / add payment
forms, inline edit with **Cancel** (snapshot on entering edit `pEditStart`, restore on Cancel/Esc `pEditCancel`), delete
invoice (typed confirm; its payments become unlinked), **Move** buttons. Any change runs `syncAct`. Closing with typed but
not added values asks (`requestClose`).

## 3.6 Move entries (`moveEntry(o)`, `#mvmodal`)
Moves an **invoice** (with its linked payments), a **single payment**, or a **whole line** (to another category and/or item
type), latest version only. `o.dry:true` computes on a clone for the live preview.
* Invoice: removed from F with its payments, pushed to T; `F.act = Σ F.invs`, `T.act = Σ T.invs`. Warning when T had a typed
  invoiced amount and no invoices (it switches to invoice-based).
* Payment: moved to T, linked to `toInvId` or unlinked; warning if it was tied to an invoice that stays.
* Line: `cat`/`name` change; refuses duplicates in the target category; adds the category to `v.cats`.
* Preview lines: each line "invoiced a → b · paid a → b · owed/overpaid", invoice paid status before/after, category
  subtotals, and **Projected final cost before → after** (`budFigs(V,0).proj`). Result `{ok, kind, title, summary, lines, warn,
  from, to, projBefore, projAfter, applied}`. The window has search (`#mv-q`), the current line disabled, Confirm disabled
  until a target is picked, Cancel.

## 3.7 Item types (Manage item types, `#tmodal`)
Edits `store.catalog` (categories and names). Shows usage counts (`typeUse`, `catUse`); used types can't be deleted;
rename renames matching budget lines in every budget; delete asks for a typed confirmation. **Saves to the team instantly**
(`saveTypes`): it applies the same mutation to a fresh copy of the saved store (`PRISTINE`) and publishes only that, so other
unsaved changes stay unsaved on the device (the device draft is re-based on the new `savedAt`). The window **stays open**:
before publishing it writes `sessionStorage['ec-types-reopen']` (scroll, focus target, half-typed names, message, savedAt);
if the host reloads the page, `tReopen()` (on load, < 2 min old) reopens the window, restores scroll/focus/typed text and
shows "Saved for the team". Failure keeps the change as an unsaved change. Without team save it stays on the device.

## 3.8 Inline edit rules
Money inputs show thousands separators and are never truncated; numbers parse by stripping `$ , % spaces`. Budget cell
edits use `data-b="item:<id>:<field>"` → `setB()`; version fields `v:<field>`. Every edit is an unsaved change.

## 3.9 Designs (`b.designs`, `b.built`, `project.budget.design`)
Designs are the different homes that could be built (e.g. Bungalow, 2 storey front garage), compared **before**
building. Versions (3.4) stay exactly as before: revisions over time of the budget that is being built. All fields are
additive and optional; a budget without `designs` looks and works as before.

* `budget.designs[] = {id, name, note, above, base, rate, sell?, cats[], items[{id, cat, name, amt, note, ups?}]}`;
  `budget.built` = id of the design the budget was made from.
* **Designs card** (`dCard`, above Versions; entry point "+ Compare designs" in the Versions header when there are none):
  one card per design (total, lowest, per sq ft above grade, selling price − budget, Edit, Build this design / Switch to
  this), "+ Add design" (start from current budget, a copy of a design, or the empty template), editor (`dEditor`: fields
  + lines by category, add/remove line, Delete design, Done; `data-d` inputs → `dSet`), and the **Compare designs** table
  (`dCmp`: category totals, tap to show lines, "Lines that differ"/"All lines", Total with lowest, per sq ft, selling
  price, selling price − budget). Open by default until a design is built, then folds to "Building: <name>".
* **Build this design** (`dBuild`, asks first via `askQ`): when the budget has one empty version (no amounts, invoices,
  payments, upgrades, finished), the design's lines replace it; otherwise a new version vN+1 is made from the design and
  invoices, payments, upgrades, finished ticks and typed actuals of the latest version are **copied** to matching lines
  (cat + name; missing lines added at $0). The previous version is unchanged. `built` is set, projects' `design` picks
  are cleared (they follow the latest version as usual).
* **Projects before building**: the Version dropdown (Inputs and Used by) has a "Designs (before building)" group;
  `project.budget.design` makes `resolveBudget` (and the backup's resolve) use that design's lines. Ignored once built.
* **Compare with** defaults to No comparison; lines are matched by id, else by category + name.
* **Actual invoiced** cell: a button (`b-payinv`) that opens the Invoices & payments window with the invoice form; amounts
  are no longer typed in the table.
* Upgrades stay on each version's lines ("Upgrades in vN"); building a design copies the design lines' upgrades.

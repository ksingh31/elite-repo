# 5. To check (resolve rows from the backup sheet's "To check" tab)

Mockup: `mockups/to_check_mockup.html`. Page `#tocheck` (`tcPage`, `tcPaint`).

## Source and the ONLY write
* Read: the selected budget's backup sheet (`b.sheetId`), tab **To check**, range `A3:L` (row 3 = header, data from row 4).
  Columns: A invoice-sheet tab, B row, C vendor, D invoice no., E date, F total, G paid, H category in invoice sheet,
  I budget line in calculator, J what to check (free text), K Status, L Resolution (history, one line per answer).
  Rows whose tab is "Budget tab", vendor "TOTAL(S)" or empty vendor are skipped. Missing tab → "This budget’s backup sheet
  has no “To check” tab yet".
* Write (`tcWrite`): **only** `'To check'!K<r>:L<r>` (one row, two cells, row ≥ 3) of a sheet that is some budget's own
  `sheetId`, never the read-only ids in `TC_RO` (invoice sheet, retired master sheet). Header K3:L3 = `Status, Resolution` is
  written first if missing. The AWS backend enforces the same rule ([../../api/src/guard.mjs](../../api/src/guard.mjs)).
* The invoice sheet itself is never touched (its category is never changed by the calculator).

## Classification (`tcType(x)`, from column J text)
| type | rule (first match) | pill / group |
|---|---|---|
| `dup` | /twice\|duplicate/ | Likely duplicate / Duplicates |
| `sheet` | /now shows\|update (the calculator )?to match\|sheet changed/ | Invoice sheet changed / Details |
| `nopay` | /payment with no invoice\|isn.t linked\|not linked\|no invoice total/ or (no total and paid > 0) | Payment with no invoice / Other |
| `est` | /placeholder\|estimate/ | Placeholder / Other |
| `date` | /in the future\|odd date/ | Odd date / Details |
| `ownline` | /no line for\|own (budget )?line/ | Own line / Other |
| `nocat` | /no category/ or column H is "(none)" | No category / Category |
| `cat` | /filed under\|belong\|is it all\|similar .*under\|category\|budget line/ | Check the budget line / Category |
| `other` | anything else | Other |
Filters: All / Duplicates / Category / Details / Other, plus a budget-line filter. Status: K = "Resolved" → resolved, else open.

## Finding the row in the calculator (`tcFind`)
Latest version. `tcLineItem` matches column I to a line by normalized name (exact, then contains). For invoices: among all
lines (matched line first), invoices with the same amount (±0.005) scored: vendor equal 4 / contains 3 (else skip), invoice
no. equal +2, date equal +1, on the matched line +1; best wins. Payments (`nopay`): the payment recorded in a previous
resolution, else an unlinked payment with the same amount (and date when both have one). `ownline` → just the line.

## Actions per type (`tcActs`) and their effects (`ops`, reversible)
* not found → "Mark as resolved" (no change).
* `dup`: Delete the copy (`del` the chosen duplicate invoice and its payments; pick which copy to keep) · Both are real.
* `cat` / `other`: Keep on <line> · Move to <suggested line> (`tcSugLine`) · Move to another line… (picker / new line) ·
  Split across lines… (amount parts; paid share moves proportionally).
* `nocat`: Keep on <line> · Assign another line… · Create new line… (`newline` + `move`).
* `date`: Save details (suggested date `tcSugDate`, e.g. Dec 1 → Nov 1; field edits) · It’s correct as is.
* `sheet`: Use invoice sheet values (parses "shows invoice X" and "note '…'" from J: `field` ops for `no` / `note`) · Keep ours.
* `est`: Replace with the real invoice… (vendor, no., date, amount; preview shows the difference) · Keep as an estimate
  (`est:true`, note "Estimate · …") · Remove it.
* `nopay`: Match to an invoice… (`pfield inv`) · Record as a deposit / prepayment (`ref`, `deposit:true`) · Leave for now.
* `ownline`: Keep as its own line · Merge into Miscellaneous (`mvall` + `dropline`) · Merge into another line… · Exclude from budget (`dropline`).

Op types handled by `tcApply(v, ops, dir)` (dir −1 = undo, in reverse order, using snapshots stored on the op):
`newline, move, del, field, pfield, split, mvall, dropline`; afterwards `act` is recomputed from invoices on touched lines.
Each action shows its effect preview (`tcEffect`: "Garbage truck −$452.67", category changes, etc.).

## Stage → save → (reopen / discard)
* Choosing an action **stages** it ("Resolved — not saved", undo per row, pending bar "Save all (n)", bulk select with a
  same-kind action e.g. "Move all to Miscellaneous"). Optional note per row; "Your name" (`ec-tc-name`, device) is saved with
  each answer.
* `tcSave(keys)`: for each staged row write K/L: K = `Resolved` (or `Open` for reopen), L = previous L + new line
  `[YYYY-MM-DD HH:MM] Resolved by <name>: <label> · Budget: <effect> · Note: <note>` (Edmonton time). Then apply the ops to
  the latest version and record `b.toCheck['r<row>'] = {vendor, label, ops, by, at, py}` so **Reopen** can reverse exactly.
  Budget changes become normal unsaved changes ("click Save for team to share them"). Errors stop the batch and say how
  many were saved.
* **Reopen**: K → Open, L gets "Reopened by … took back “…”", ops reversed, record deleted.
* **Discard** of the calculator's unsaved changes also rewrites the K/L of the sheet rows those changes came from back to
  their previous values (`tcOnDiscard`, `tcWrites`).
* Leaving the page with staged rows asks (Save all / Discard / Go back, `tcGuard`, `#tcleave`).
* Budget page: banner with open count and chips on lines that have open rows.
* Not built (follow-up): a "Waiting / Ask someone" status (sheet K holds only Open / Resolved).

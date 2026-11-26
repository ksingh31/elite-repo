> Historical working brief from the Nov 26 build session (paths refer to the build workspace, not this repo).

# Story: Upgrades on budget lines

**As** the builder, **I want** to record upgrades on any budget line (e.g. Windows and doors: "Triple-pane upgrade", +$4,200, Yes/No) in the same budget and version, **so that** the build cost, projected cost and profit include the upgrades I've said Yes to, and I can see what each line's base vs upgrades are.

Approved design: /home/claude/mock/upgrades_mockup.html (desktop + mobile approved; Pattern A "inline rows" is the default). Build it into the real app: /home/claude/wu/index.html (copy of the live file).

## Defaults (user can change later; keep them easy to change)
- Layout A (inline): each line shows Base, "+ Upgrade" control / summary chip, Line total; an expandable upgrades panel under the line. Also add the summary card ("N upgrades on M lines · Approved/Quoted/Declined") above the items table.
- Upgrade fields: name, extra price (money, commas), Yes/No, requested by (Buyer / Builder), status (Quoted / Approved / Declined, optional), note.
- Yes adds the price; No adds $0 (kept as a record, greyed). Switching to Yes marks Quoted -> Approved; picking Declined sets No. Quoted + Yes counts.
- Line total = base + Yes upgrades. Category totals, tiles, Budget total, Projected final cost (per line max(line total, invoices); Finished lines use invoices), Over/under (invoices vs line total) and the build cost sent to projects (all sources: Projected / Budget estimate / Invoiced / manual) use the line total where the base was used before.
- Per version: upgrades are stored on the version's items (`item.ups=[{id,name,amt,yes,by,status,note}]`). New version copies them; older versions keep theirs. Version compare shows the line-total change and upgrade changes.
- Buyer upgrades do NOT change the sale price (open question for user). No markup.
- "Show upgrades" toggle: off = today's compact table, budget column shows line total with "incl. +$X upgrades".
- Data model change is additive only: old data without `ups` must load and calculate exactly as before (migrate adds nothing or `ups:[]` lazily). Never rewrite existing store values.
- Google Sheets backup: the backup Budget tab should show base, upgrades and line total (add columns after existing ones so restore/sync keeps working); restore from backup must round-trip upgrades (they're in the full JSON "Backup data" already if the store JSON is saved there — verify). The sync-from-sheet feature must ignore/handle the new columns safely.
- "See what changed" lists upgrade changes in plain words.
- Unsaved-changes flow: upgrades edits are normal unsaved changes (Save for team / Discard).

## Standing rules
- Only the checkbox box is clickable, never its label text.
- Must work on mobile (375/390) and desktop: aligned rows, equal-height boxes, no truncated money, no horizontal scroll, ≥44px tap targets, identical alignment for lines with zero vs several upgrades.
- Don't change other calculations or existing behaviour.

## Acceptance
- Add/edit/toggle/remove upgrades on a line; totals, projected, over/under, project build cost and builder/investor reports update.
- Old store data gives identical numbers to before (regression suite unchanged + a new test that loads the live store and compares totals before/after).
- New version copies upgrades; compare shows them.
- Backup write + restore round-trips upgrades (use the mock).
- All existing tests pass (copy /home/claude/t5/*.py + run.sh, repoint /home/claude/merge/mAB.html -> your file and /home/claude/t5/ -> your test dir) plus new upgrades tests.
- Screenshots at 375/390/768/1300 light+dark, looked at and clean.

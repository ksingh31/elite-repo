> Historical working brief from the Nov 26 build session (paths refer to the build workspace, not this repo).

# Open user-reported issues (must ALL be fixed and verified in the live file)

Live/published file = /home/claude/merge/base_ab.html (your copy starts identical). Screenshots the user sent are *.png in your workspace (open the recent ones to see each problem).

## Standing rules (apply everywhere, now and for future work)
- R1. Checkboxes: ONLY the box itself is clickable; label text must not toggle (already implemented globally — keep it; make boxes touch-friendly by enlarging the box itself, not the label).
- R2. Every UI change must work on mobile (375/390px) AND desktop; nothing truncated, no horizontal scroll, aligned rows.
- R3. Don't change calculations, data model, saving logic, or Google Sheets logic. Don't edit the store JSON.
- R4. Money inputs show commas; values must never be cut off ("$ 797,0(" is a bug).

## Scope A — Inputs page (agent A)
- A1. Sidebar order: builder's ACTUAL profit (after financing for the selected option, with interest/fees deducted, selected-financing details) on TOP; investor-level "Profit before financing" (with investor return, annualized, etc.) in its OWN separate box at the BOTTOM. Both visible, clean, UX friendly. Also on the mobile sticky mini-summary.
- A2. "From … to …" month inputs: smaller but visibly one grouped control, clean.
- A3. Mobile input rows: short private loan row (Lender / Amount / Fixed fee / Rate / Months / ×) is crammed into one row on phones ("Priva", "$ 2(") with × dropping to a giant row — stack in a tidy 2-col grid, labels above, small aligned remove button. Same for Cash+Private draw rows (Months after build starts / Amount / ×), Private draws, A Lender draws, extra costs, investors, lot loans — every multi-input row.
- A4. Draw schedule tables on mobile: first-column labels break awkwardly ("Draw\n1", "Total\ndrawn") — keep labels on one line / readable.
- A5. Phone header (top bar with project picker, save state, tabs): too tall and tabs wrap badly on phones — make compact (e.g. horizontally scrollable tab strip, actions compact) without hiding functionality.
- A6. Seg radio controls ("% of approved loan / Fixed $ amount") look fine but make sure they don't wrap into 2 lines awkwardly on phones.

## Scope B — Budget page + Backups (agent B)
- B1. "Finished" control on each budget line: intent unclear, too big, misaligned. Redesign from the user's perspective (e.g. a compact, clearly labelled "Finished" checkbox, aligned in its cell, with a tooltip/short hint that finished lines use invoiced amount in Projected). Keep R1 (only the box clickable).
- B2. "Link project" button: alignment and height must match the select next to it.
- B3. "Compare with" label/select placement looks random — put it in a clean toolbar row with the version controls.
- B4. Budget page header (budget picker, version, link project, compare, Manage item types, New version, sheet link, buttons) is not mobile friendly — wrap cleanly on phones: full-width selects, tidy button grid, no overflow.
- B5. Budget items on mobile (item rows/cards, sub-items, Finished, invoice buttons, amounts): readable, no truncated money, sensible stacking.
- B6. Version name / Date / What changed fields row: fine on desktop; check mobile.
- B7. Backups window: "Load this backup"/restore must be a clear call-to-action button; clicking it must open an "Are you sure? Your current changes will be replaced…" confirmation (use the existing askQ dialog) before restoring; overall redesign so it's clean (list of restore points with date, source, clear primary action per row), mobile friendly.
- B8. Green tiles: already fixed (smaller, one line) — verify it stays fixed, don't change.
- B9. Manage item types: already changed to save to the team immediately with no "Keep changes?" prompt on close — verify still true, don't change.

## Verification (both agents)
- Playwright with the mock INIT from /home/claude/bk_test.py (reuse /home/claude/qa/h*.py helper style). Screens at 375, 390, 768, 1300; light+dark. Programmatic checks: no horizontal overflow, no input with scrollWidth>clientWidth for its value, row label tops aligned, tap targets ≥40px.
- Regression tests: copy /home/claude/t3/*.py + run.sh into your workspace, rewrite the path /home/claude/merge/m4.html -> your file and /home/claude/t3/ -> your test dir; all must pass (38,17,20,19,17,12,10, audit errors [], 124).
- Keep edits localized (CSS in a new block named for your scope just before the LAST `</style>`; minimal JS/markup edits) because the two agents' files are 3-way merged.
- Write a status table to <workspace>/status.md: each item id → fixed / already OK (with evidence screenshot path).

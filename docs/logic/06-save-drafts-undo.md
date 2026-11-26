# 6. Unsaved changes, drafts, stale drafts, undo restore, save flow

## 6.1 Where data lives
| what | where | who sees it |
|---|---|---|
| Team copy | artifact: `<script id="store">` of the published page · AWS: S3 `store/store.json` (versioned) | everyone |
| `PRISTINE` | the team copy as loaded/saved (string) — baseline for diffs and Discard | this tab |
| Device draft | `localStorage['ec-calc5'] = {base: savedAt, data: store, at, restore}` | this device |
| Stale draft | `localStorage['ec-calc5-stale'] = {at, data}` | this device |
| Undo restore | `localStorage['ec-calc5-undo'] = {data, dirty, restore, at}` | this device |
| View | `localStorage['ec-view'] = {cur, bud}` (project/budget being looked at) | this device |
| To check name | `localStorage['ec-tc-name']` | this device |
| Colour mode | `localStorage['ec-theme'] = 'light' \| 'dark'` (absent = light) | this device |
| Item types reopen | `sessionStorage['ec-types-reopen']` | this tab |
| Next view after reload | `sessionStorage['ec-next'] = {proj, bud, hash, at}` | this tab |

## 6.2 Load
`store = migrate(JSON.parse(PRISTINE))`. If a device draft exists with `base === store.savedAt` and `data.v === 4` →
load it (`dirty = true`, `draftLoaded`, `draftAt`, `restoreMark`). If a draft exists but its base differs (someone saved
since) → move it to `ec-calc5-stale` and drop it (+ the undo copy). Without a draft, the device view (`ec-view`) picks
the project/budget.

## 6.3 Editing
`persist()` sets `dirty`, writes the device draft and repaints the save state (`#savestate`: "Unsaved changes" /
"All changes saved", click → See what changed). `persistClean()` (upgrades) clears `dirty` when the store equals the saved
copy again. `curDiff()` = `diffStores(migrate(PRISTINE), store)` (cached by JSON key) → plain-language list grouped by
Company / Projects / Budgets (project field words via `words`, money/months formatting, budget line edits, invoices,
payments, upgrades, versions, item types) and the set of changed item ids (row markers on the Budget page).

**Notice bar** (`#nbar`, `renderNbar`):
* dirty: "N unsaved changes (from <time>, kept on this device). Only you can see them until you save." [See what changed]
  [Save for team] [Discard]
* after a restore: "Showing the restore point from <when> (<source>). Nothing is saved for the team yet · N differences"
  [Undo restore] [See what changed] [Save for team]
* stale draft: "Your unsaved changes from <time> weren’t loaded because someone saved a newer version since."
  [Download my changes] (`my-unsaved-changes.json`) [Dismiss]

## 6.4 Leave / switch guards (same popup style everywhere)
* Changing page, project, budget, making/duplicating a budget while dirty → `guard(fn)` modal `#modal`
  "Save or discard your changes first": **Save for team / Discard changes / Cancel** (then continues with the action).
* Closing a window with typed-but-not-added values (`requestClose`: invoices & payments, item types, new version) →
  `#dmodal` "Discard what you typed?": **Discard and close / Undo my changes and close / Keep editing** (the second also
  restores the window's snapshot taken when it opened).
* Discard all → `askQ` "Discard your unsaved changes?" (lists the count) → `discard()` = reload `PRISTINE`, clear draft
  and undo, re-render, and `tcOnDiscard()`.
* Browser leave (`beforeunload`) warns while dirty (with real differences) and not saving, and while To check rows are staged.
* See what changed (`#chmodal`): the list + **Save for team / Discard all changes / Close**.
* Destructive actions (delete project/budget/version/item/invoice/type) use `confirmBox` with a typed word (`delete`).

## 6.5 Save for team (`saveTeam`)
1. If team save isn't available → toast "Changes stay on this device".
2. Busy overlay (`setBusy`: all save/backup/discard buttons disabled; double clicks ignored).
3. If Google Sheets is available: **back up first** (`writeBackup('Save for team', store)`); a backup failure is only a
   warning toast — the save continues.
4. `savedAt = now ISO`; `json = JSON.stringify({...store, savedAt})` with `<` escaped as `<`;
   `html = TEMPLATE` with the store script replaced → `artifact.publish(html)`.
5. Success: `store.savedAt = savedAt; PRISTINE = json;` clear diff cache, `dirty = false`, `restoreMark = null`, remove draft /
   undo / stale → "Saved for the team. Everyone now sees these numbers."
6. Errors: `not_granted|not_writer` → "You can view this calculator but not save it"; `conflict` → "Someone saved at the
   same time. The page reloads to their version." (the AWS adapter reloads after 2.5 s; the draft then becomes a stale
   draft with Download); otherwise "Save failed. Your changes are still on this device."

AWS build: `publish(html)` extracts the JSON and `PUT /api/store {store, baseVersion}`; S3 `If-Match` makes concurrent
saves safe (409 → `conflict`). See [../architecture.md](../architecture.md).

## 6.6 Restore and Undo restore
Backups window → restore point → `askQ('Are you sure?' …)` → `loadBackup(row)`: reads `'Backup data'!A<row>:L<row>`,
joins parts `D..` (count in C; tolerates a leading `'`), requires `v === 4` and `projects[]`, keeps sheet ids the current
budgets know, saves the current screen (incl. unsaved edits) to `ec-calc5-undo`, keeps `savedAt` (so it is a draft on top of
the current team copy), migrates, keeps the selected project/budget when they exist, sets `restoreMark = {when, source}`,
persists → yellow bar. **Undo restore** puts back exactly the previous screen (dirty or clean). Nothing reaches the team
until Save for team.

## 6.7 Checkbox rule
Global handler: only the checkbox box itself toggles; clicking label text does nothing (applies to all current and future
checkboxes). Boxes are enlarged for touch instead of making labels clickable.

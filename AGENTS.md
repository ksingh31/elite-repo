# AGENTS.md — standing rules for AI agents (and humans) working on this repo

Project: **EliteCraft project profit calculator** — an internal single-file web app for a home builder (projects,
financing options, investor/builder returns, budgets with invoices/payments/upgrades, Google Sheets backups, To check
review). Live today as a Claude artifact; this repo also deploys it to AWS. Read `README.md`, `docs/architecture.md`
and the section doc in `docs/logic/` before changing anything.

## Product rules (from the team — apply to all current and future work)
1. **Checkboxes**: only the box itself is clickable, never the label text. Make boxes touch-friendly by enlarging the box.
2. **Mobile and desktop**: every change works at 375 / 390 (phones) and 768 / 1300 (desktop), **light and dark**.
   Rows aligned with and without optional content; **no truncated money** ("$ 797,0(" is a bug); no horizontal scroll;
   tap targets ≥ 44 px on phones; money inputs show commas.
3. **Unsaved changes**: same popup style (Save / Discard / Go back) wherever unsaved state can be lost.
4. **Google Sheets permission**: every sheet the team provided is an ORIGINAL and **READ-ONLY**. The ONLY sheets that may
   be written are the calculator's own backup sheets (one per budget, in the backup Drive folder). Any other sheet: read
   only — no writes, no formatting, no new tabs. **Never modify the invoice sheet or the retired master sheet** (their ids
   are `YOUR_INVOICE_SHEET_ID` / `YOUR_RETIRED_MASTER_SHEET_ID` placeholders here; real values in the private config).
   In the backup sheets, only the six data tabs (Summary, Budget, Trade, Material, Service, Other) and their
   " (updating)" copies may ever be deleted; "To check" only gets K:L (Status, Resolution) written.
5. **Don't change calculations, data, saving or Sheets logic unless the story requires it.** Data-model changes are
   **additive only**: old data must load and calculate exactly as before. Don't edit the team's store data except when
   necessary.
6. Keep the `/*ENGINE*/ /*END*/ /*BACKUP*/ /*ENDBACKUP*/ /*SHEETS*/ /*ENDSHEETS*/` markers and keep those functions
   self-contained: the daily backup (Claude task and AWS Lambda) cuts them out of the live page.

## Public repository rules
* **Never commit real data**: the team store (real financials, vendors, invoices), real Google ids, credentials, the
  artifact slug. Use `samples/store.sample.json` and placeholders. Put real values in `config/private.json` (gitignored).
* Run `make scan` before every push (CI runs it too).

## How work runs (the team's process)
* Each bug fix / story is merged and published **as soon as it is done and tested** (don't batch).
* A coordinator manages (spawns agents, tracks, merges, tests, publishes); agents build.
* Publishing the artifact: code-only `edit_version` edits generated with `tools/artifact/mkedits2.py old new`; strip a
  `</head><body>\n<header class="top` suffix from style edits (anchor at `</style>`); retry 409 with the live version;
  never anchor across a bare `hidden>` attribute (live HTML normalizes it to `hidden=""`); edit sets > 40 KB go through a
  delegated agent. 3-way merge agent copies with `git merge-file` against the base they started from; after CSS conflicts
  check the `<style>` brace balance is 0 and run **every** feature test, not just the regression suite.
* Story CSS goes in a new named block just before the LAST `</style>`; keep JS/markup edits minimal and localized.
* After each artifact publish, re-export the repo copy: `make export LIVE=<live.html>` and commit.

## Tests (must all pass)
* `python3 tests/run_all.py` (Playwright: regression + features + standalone smoke; uses the `window.claude` mock in
  `tests/mock_init.js`), `cd api && npm test`, `make lint`.
* Tests run against `app/artifact/index.html` (sample store). `APP_HTML=/path/to/other.html` tests another copy. The
  numeric expectations are calibrated to the sample store.
* Screenshots of every change at 375/390/768/1300 light+dark go to `tests/out/` (gitignored) — look at them.

## Map
`app/artifact/index.html` (the app) · `app/platform/platform.js` + `app/build/build_standalone.mjs` → `app/standalone/` ·
`api/` (Lambda API, Google proxy + guard, daily backup) · `infra/aws/` (SAM template, deploy/teardown) · `infra/azure/`
(optional Bicep) · `docs/` (architecture, data model, logic per section, operations, decisions, rebuild runbook) ·
`schemas/` · `samples/` · `tests/` · `tools/` · `mockups/` · `stories/`.

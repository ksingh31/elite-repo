# Changelog

## 2026-11-26 — AWS-only infrastructure as code
* **Removed Azure / Bicep** (`infra/azure/`, `api/azure/`) and every mention of it: the team is on AWS and Bicep only
  targets Azure.
* IaC is AWS SAM / CloudFormation (decision D10): every tunable is a template parameter with a cheap default (env name,
  cost center, custom domain + ACM cert, CloudFront price class, backup hour/minute/time zone, budget, log retention,
  Lambda memory/timeout/runtime, API throttling, store version retention, write-guard ids); `infra/aws/samconfig.toml`
  with `dev` and `prod`; every resource tagged `App` / `Env` / `CostCenter`; resource names include the env so dev and
  prod can share an account.
* `make plan` (change set preview, nothing changes) → `make deploy` (preview, confirm, apply with automatic rollback,
  upload app), `make outputs`, `make drift`, `make events`, `make teardown` (asks for the stack name).
* Fixed a circular dependency (HTTP API ↔ user pool client ↔ CloudFront) by declaring the HTTP API as plain
  `AWS::ApiGatewayV2` resources; `make lint` also runs `sam validate --lint` when the SAM CLI is installed.

## 2026-11-26 — repository
* Rebuildable repo: verbatim app (sample data, id placeholders), standalone AWS build + `platform.js` adapter and
  re-export script, Lambda API (S3 store with ETag concurrency, Google Sheets/Drive proxy with server-side write guard,
  daily backup twin), SAM template + one-command deploy/teardown, JSON Schema + sample store,
  logic docs per section, operations / decisions / rebuild runbook, AGENTS.md, CI.

## 2026-11-25/26 — features published to the live artifact (overnight session)
* **Builder report + PDF**: new Builder report page (selected financing option: facts, draw tables, financing cost,
  builder cash and returns, breakdown); PDF download for Builder and Investor reports built from the on-screen report
  (hand-written PDF, Helvetica, page breaks, footer).
* **Readability**: calmer typography, number alignment, contrast fixes (audit ≥ 3:1).
* **Inputs sidebar + mobile** (Scope A): builder's actual profit after financing on top, investor-level profit before
  financing in its own box at the bottom (also on the phone mini summary); grouped from/to month inputs; multi-input rows
  stack in a 2-column grid on phones; draw tables keep labels on one line; compact phone header with scrolling tabs;
  seg controls don't wrap.
* **Budget + Backups redesign** (Scope B): compact "Finished" checkbox with hint; Link project button height; clean
  toolbar with version / compare; mobile-friendly budget header and item cards; Backups window lists restore points with
  a clear "Restore this copy" button and an "Are you sure?" confirmation.
* **Manage item types**: saves to the team instantly (only the item-type change; other unsaved edits stay unsaved);
  window stays open after add / delete / rename and **reopens after the host reloads** (sessionStorage state).
* **Upgrades** on budget lines (Pattern A inline rows): Yes/No, requested by, status, note; line total = base + Yes
  upgrades used everywhere (totals, projected, over/under, build cost); summary card; Show upgrades toggle; compare and
  See what changed; panel stays open after deleting the last upgrade; add+delete leaves the page clean (`persistClean`).
* **Upgrades in the backup sheet**: Budget tab sub-rows (`↳ Upgrade`, `Line total`, column J `up:`/`sub:`), Summary
  "Budget and upgrades" tiles and Upgrades section, category table with base / upgrades / projected; sync skips sub-rows.
* **To check** page: resolve rows of the backup sheet's To check tab (duplicates, category, no category, odd date,
  invoice sheet changed, placeholders, unlinked payments, own line) with staged answers, bulk actions, reversible budget
  effects, history in column L; only K:L written.
* **Move entries**: move an invoice (with its payments), a single payment or a whole line, with live preview incl.
  projected cost; **Cancel** on inline edits in the Invoices & payments window.
* **Table fit**: Budget table fits at ~1300 px with upgrades and invoices shown (Notes no longer cut off).
* **QA sweep**: all tabs and modals at 375–1440, light + dark; 9 bugs fixed (incl. card dropdown under the Move button).

## Not done / follow-ups
* To check "Not sure yet / Ask someone" (Waiting status) — sheet K holds only Open / Resolved.

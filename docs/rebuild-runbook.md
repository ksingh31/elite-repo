# Rebuild from scratch (with AI agents)

Goal: if everything is lost (artifact deleted, AWS account gone, laptop gone), rebuild **exactly** the same calculator.
Three levels, fastest first.

## Level 1 — restore the existing file (minutes)
The code in `app/artifact/index.html` is byte-identical to the live artifact (only public placeholders and the sample
store differ).
1. `cp config/private.example.json config/private.json` and fill the real ids (team password manager / notes).
2. Get the real store: latest restore point in any budget's backup sheet (`Backup data` tab, row with the newest date,
   columns D… joined = JSON), or the S3 data bucket (`store/store.json`, any version), or an Export file.
   Quick extraction from a sheet: copy cells D..L of the row into a text file and join them (no separators).
3. ```bash
   python3 tools/store_tool.py privatize app/artifact/index.html config/private.json /tmp/live.html
   python3 tools/store_tool.py inject /tmp/live.html real-store.json /tmp/live.html
   ```
4. Claude artifact: create a new HTML artifact with `/tmp/live.html` (it uses `window.claude` artifact/downloads/mcp;
   connect Google Sheets + Google Drive connectors; share with the team). Re-create the daily task
   ([daily-backup-task.md](daily-backup-task.md)) with the new artifact slug.
   **Or** AWS: `STORE_FILE=real-store.json IDS_FILE=config/private.json ... make deploy ENV=prod` (see README).

## Level 2 — redeploy the infrastructure (≈ 15 minutes)
`make plan ENV=prod` previews the CloudFormation change set; `make deploy ENV=prod` (`infra/aws/deploy.sh`) is
idempotent: creates/updates the stack from `infra/aws/template.yaml` + `infra/aws/samconfig.toml`, uploads the app built
from `app/artifact/index.html`, uploads the store only if none exists. Then add users in Cognito and store the Google
credentials (docs/config.md). Parameters / rollback / drift: [operations.md](operations.md#aws-infrastructure).

## Level 3 — re-implement from the docs (AI agents)
Use when the HTML itself must be rewritten (another stack, or the file is corrupt). The docs are written as a
specification; the tests are the acceptance criteria.

### Inputs for the agents
* Spec: `docs/data-model.md` + `schemas/store.schema.json`, `docs/logic/01…08`, `docs/architecture.md`.
* Visual reference: `app/artifact/index.html` (open in a browser with `samples/store.sample.json`), `mockups/`,
  `docs/logic/08-ui.md`.
* Acceptance: `tests/` (Playwright, mock of `window.claude` in `tests/mock_init.js`), `api/test/`.
* Rules: `AGENTS.md`.

### Suggested agent plan (coordinator + workers, each worker gets one section + the rules)
1. **Skeleton + data**: single HTML file, `<script id="store">`, `migrate()`, device draft / `persist()` / `markDirty()`
   (06), routing and tabs (02, 08). Load the sample store.
2. **Engine**: implement `calc()` exactly per 01 between the `/*ENGINE*/ /*END*/` markers. Verify with `cp_test`,
   `report_test_src` (every figure is recomputed there).
3. **Inputs page + sidebar + mini summary** (02.1), ranges (01.6).
4. **Builder + investor, Investor report, Builder report + PDF** (02.2–02.5).
5. **Budget page**: budFigs, sources and link (03.2–03.4), invoices & payments (03.5), move entries (03.6), item types
   with instant save + reopen (03.7). Tests: `bc_test`, `inv_test`, `move_test`, `reopen_test`, `noreload_test`.
6. **Upgrades** (04): `up_test`.
7. **Backups**: `buildBackup` / `buildSheets` between the markers (07.2–07.3), safe swap `writePlan` (07.4), Backups
   window + restore + undo (07.5, 06.6), sync check (07.6). Tests: `bk_test`, `sync_test`, `up_sheet_test`.
8. **To check** (05): `tc_test`, `lay_test`.
9. **Unsaved changes model**: diff list, notice bar, guards, Save for team (06). Tests: `save_test`, `modal_test`.
10. **QA sweep**: `audit.py`, every page at 375/390/768/1300 light+dark (08 rules).
11. Standalone adapter + AWS: `app/platform/platform.js`, `app/build/build_standalone.mjs`, `api/`, `infra/aws/`
    (already generic: re-use as is). Test: `standalone_smoke`.

### Prompt template for a worker
> You are rebuilding section N of the EliteCraft project profit calculator. Read AGENTS.md (standing rules), the section
> doc docs/logic/0N-*.md, docs/data-model.md and the existing code around the markers named there. Implement it in the
> single file app/artifact/index.html without changing calculations, data or saving logic outside your section. Keep
> data changes additive. Test on 375/390/768/1300, light and dark. Run `python3 tests/run_all.py` (and the section's
> tests); all must pass. Report what changed and the test counts.

### Definition of done
`python3 tests/run_all.py` → ALL PASSED, `cd api && npm test` → pass, `make lint` clean (cfn-lint + `sam validate --lint`),
numbers on every page equal the old app for the same store (load the real store into both and compare the Builder
report PDFs / backup sheet values).

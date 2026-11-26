# EliteCraft project profit calculator

Internal tool for a home builder: per-project profit and returns under five financing options, investor and builder
reports (with PDF), budgets with invoices / payments / upgrades, Google Sheets backups with restore points, and a
"To check" review page. It is **one self-contained HTML file** that runs today as a Claude artifact; this repository
holds everything needed to restore it 1:1, deploy it to AWS (or Azure), and rebuild it from scratch.

> This repo is public. It contains **made-up sample data** and placeholder ids only. Real data and ids live in the
> team's private config / storage (see [docs/config.md](docs/config.md)).

## What's here
```
app/
  artifact/index.html        the live app, code byte-identical to the artifact (sample store + id placeholders)
  platform/platform.js       window.claude adapter for non-Claude hosts (save → API, downloads, Sheets → API proxy)
  build/build_standalone.mjs regenerates app/standalone from the artifact HTML
  standalone/                generated build for AWS / any static host (index.html, platform.js, config.js)
api/                         Lambda API (store + optimistic concurrency, Google proxy with write guard, daily backup)
  src/  test/  local-server.mjs  azure/adapter.mjs (optional)
infra/aws/                   SAM/CloudFormation template, deploy.sh, teardown.sh   ← primary deployment
infra/azure/                 main.bicep (optional alternative, not validated)
docs/                        architecture, data model, logic per section, operations, decisions, config, rebuild runbook
schemas/store.schema.json    JSON Schema of the store        samples/store.sample.json   made-up example data
tests/                       Playwright suites (+ window.claude mock), run_all.py, fixtures
tools/                       store_tool.py (extract/inject/privatize), scan_public.py, artifact helpers, history
mockups/  stories/           approved designs and story briefs
AGENTS.md  CLAUDE.md         standing rules for AI agents
```

## Quick start (local)
Requirements: Node ≥ 20, Python 3.10+, `pip install playwright jsonschema cfn-lint && playwright install chromium`.
```bash
make serve            # http://localhost:8787 — standalone build + local API (file store in data/, fake Google)
make test             # API unit tests + all Playwright suites (≈ 6 min)
open app/artifact/index.html   # the artifact build also opens directly (no save / Sheets outside Claude)
```

## Deploy to AWS (cheapest viable, ≈ $0–1/month)
S3 + CloudFront (static app and `/api` on one domain) · API Gateway HTTP API + Lambda (arm64) · store JSON in a
**versioned S3 bucket** with ETag optimistic concurrency · Cognito user pool (hosted sign-in) · Google service account in
SSM SecureString · EventBridge Scheduler daily backup 22:37 America/Edmonton · cost budget + alarms. Details and cost
table: [docs/architecture.md](docs/architecture.md); why: [docs/decisions.md](docs/decisions.md).
```bash
cp config/private.example.json config/private.json        # fill real ids (never commit)
ALERT_EMAIL=ops@company.com COGNITO_DOMAIN_PREFIX=elitecraft-calc ADMIN_EMAIL=you@company.com \
GOOGLE_CREDENTIALS_FILE=./google-key.json STORE_FILE=./real-store.json \
REGION=ca-central-1 ./infra/aws/deploy.sh
```
Needs AWS CLI v2 (credentials with CloudFormation/IAM rights), Node, Python. Re-running updates the app; the store is
only uploaded when none exists. Teardown: `./infra/aws/teardown.sh` (keeps the data bucket unless `DELETE_DATA=yes`).
Google setup (service account, share only the backup folder): [docs/config.md](docs/config.md).

## Restore the Claude artifact 1:1 / rebuild
* Same file with real ids and data: `tools/store_tool.py privatize` + `inject` → [docs/rebuild-runbook.md](docs/rebuild-runbook.md) level 1.
* Re-export after publishing a new artifact version: `make export LIVE=/path/to/live.html`.
* Rebuild from the specification with AI agents: [docs/rebuild-runbook.md](docs/rebuild-runbook.md) level 3.

## Documentation
| | |
|---|---|
| [docs/architecture.md](docs/architecture.md) | hosts, code map of the single file, diagrams, cost |
| [docs/data-model.md](docs/data-model.md) | every store field, defaults, migrate rules |
| [docs/logic/](docs/logic/README.md) | each section's logic and formulas (engine, pages, budget, upgrades, To check, save model, backups, UI) |
| [docs/operations.md](docs/operations.md) | backups, restore, daily task, users, updates, troubleshooting |
| [docs/daily-backup-task.md](docs/daily-backup-task.md) | the Claude scheduled task prompt (verbatim) and its AWS twin |
| [docs/config.md](docs/config.md) | where ids and secrets go |
| [docs/decisions.md](docs/decisions.md) | architecture decisions |
| [CHANGELOG.md](CHANGELOG.md) | what changed |

## Tests
`python3 tests/run_all.py` runs 17 suites (bk, sync, inv, modal, cp, bc, save, audit, report, tc, reopen, noreload, move,
up, up_sheet, lay, standalone smoke) against `app/artifact/index.html` with the sample store; `APP_HTML=…` tests another
copy. `tests/run.sh` = regression set, `tests/all.sh` = features + smoke. CI (`.github/workflows/ci.yml`) runs the scan,
lint, API tests and all suites on every push.

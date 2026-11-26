# Operations

## Daily use
* Edit → yellow bar → **Save for team** (backs up to Google Sheets, then saves). Nothing is shared until saved.
* Backups window: **Back up now**, restore points, bring changes back from the sheet.
* The daily backup runs at 22:37 Edmonton (Claude task, or the AWS Lambda).

## AWS infrastructure
Infrastructure as code: `infra/aws/template.yaml` (AWS SAM / CloudFormation, decision D10). Per-environment values:
`infra/aws/samconfig.toml` (`[default.*]` = **dev** → stack `elite-calc-dev`, `[prod.*]` = **prod** → stack
`elite-calc-prod`, region `ca-central-1`). The template itself is region-agnostic. Real emails / ids are **not** put in
samconfig (public repo): pass them as environment variables (`ALERT_EMAIL`, `ADMIN_EMAIL`, `COGNITO_DOMAIN_PREFIX`,
`DOMAIN_NAME`, `CERTIFICATE_ARN`, `GOOGLE_CREDENTIALS_FILE`) and `config/private.json`; any other parameter:
`PARAMS_EXTRA="ApiMemoryMb=512 BackupHour=23"`.

| Step | Command | What happens |
|---|---|---|
| Plan | `make plan ENV=prod` | packages the Lambda code, creates a CloudFormation **change set** and prints every resource that would be added / modified / removed and whether it is **replaced**. Nothing changes. |
| Deploy | `make deploy ENV=prod` | same preview, asks "Apply?" (`YES=1` skips the question, e.g. CI), executes the change set, then stores the Google key in SSM, builds + uploads the app, uploads the store only if none exists, refreshes CloudFront. |
| Outputs | `make outputs ENV=prod` | stack status + outputs: `AppUrl`, `CloudFrontUrl`, buckets, user pool + client, Cognito domain, function names, alert topic. |
| Rollback | automatic | if any resource fails during an update, CloudFormation restores the previous working state by itself (`make events ENV=prod` shows why). To undo a *successful* change: `git checkout <previous commit> -- infra/aws` and `make deploy`. Stuck in `UPDATE_ROLLBACK_FAILED`: `aws cloudformation continue-update-rollback --stack-name elite-calc-prod`. Cancel an update in progress: `aws cloudformation cancel-update-stack --stack-name elite-calc-prod`. App-only rollback: deploy the previous commit (the data is never touched by deploy). |
| Drift | `make drift ENV=prod` | lists resources edited outside CloudFormation (console / CLI) and which properties differ. Fix by re-deploying (template wins) or by moving the change into the template / samconfig. |
| Teardown | `make teardown ENV=prod` | asks for the stack name, downloads a final store copy to `backups/`, deletes the stack. The **data bucket is kept** (`DeletionPolicy: Retain`) unless `DELETE_DATA=yes`; the SSM key is kept. |

SAM CLI (optional, `pip install aws-sam-cli`): `cd infra/aws && sam validate --lint` and
`sam deploy --config-env prod --parameter-overrides AlertEmail=… CognitoDomainPrefix=…` deploy the infrastructure only
(SAM shows the change set and asks before applying); run `make deploy` afterwards to upload the app.

Cost tracking: every resource carries the tags `App`, `Env`, `CostCenter` (stack tags + explicit resource tags).
Activate them once in Billing → Cost allocation tags to split Cost Explorer by app / environment. Monthly estimate
(≈ $0.05–1 per environment): [architecture.md](architecture.md#cost-aws-ca-central-1-internal-use-5-users-1-mb-store-a-few-hundred-savesbackups-a-month).

### Parameters
Defaults are the cheapest sensible values; samconfig overrides them per environment (dev: no daily backup, short log
and version retention, $3 budget).

| Parameter | Default | What it controls |
|---|---|---|
| `AppName` | `elite-calc` | prefix of resource names, `App` tag |
| `Env` | `prod` | `dev` / `test` / `prod`; part of resource names (envs can share an account), `Env` tag |
| `CostCenter` | `internal-tools` | `CostCenter` tag |
| `AlertEmail` | — (required) | budget + alarm emails (SNS subscription must be confirmed) |
| `AdminEmail` | empty | first Cognito user (gets a temporary password) |
| `MonthlyBudgetUsd` | `5` | AWS Budget; alerts at 80 % actual, 100 % forecast |
| `CognitoDomainPrefix` | — (required) | hosted sign-in page prefix (globally unique) |
| `WritersGroup` | empty | Cognito group required to save; empty = all signed-in users |
| `DomainName` / `CertificateArn` | empty | optional custom domain; the ACM certificate must be in **us-east-1** |
| `CloudFrontPriceClass` | `PriceClass_100` | edge locations; `PriceClass_100` is cheapest (North America + Europe) |
| `GoogleCredentialsParam` | `/elite-calc/google-credentials` | SSM SecureString with the Google key (samconfig: `/elite-calc/<env>/…`) |
| `BackupFolderId` | empty | the only Drive folder whose sheets may be written |
| `AllowSheetIds` | empty | extra writable backup sheets outside the folder |
| `DenySheetIds` | empty | never written (invoice sheet, retired master sheet, originals) |
| `DailyBackupEnabled` | `true` | daily backup schedule on/off |
| `BackupHour` / `BackupMinute` | `22` / `37` | daily backup time |
| `BackupTimeZone` | `America/Edmonton` | schedule time zone and backup timestamps |
| `LambdaRuntime` | `nodejs24.x` | `nodejs20.x` / `nodejs22.x` / `nodejs24.x` |
| `ApiMemoryMb` / `ApiTimeoutSeconds` | `256` / `29` | API Lambda (HTTP API caps requests at 30 s) |
| `BackupMemoryMb` / `BackupTimeoutSeconds` | `512` / `600` | daily backup Lambda |
| `ApiThrottleRate` / `ApiThrottleBurst` | `20` / `50` | API requests per second / burst (caps cost if a token leaks) |
| `ApiLogRetentionDays` / `BackupLogRetentionDays` | `30` / `90` | CloudWatch Logs retention |
| `StoreVersionRetentionDays` | `365` | how long replaced store versions (S3 restore points) are kept |

## Backups — what exists
| Copy | Where | Retention |
|---|---|---|
| Restore points | each budget's backup sheet, hidden tab `Backup data` (full store JSON per row) | until deleted by hand |
| Backup log | `Backup log` tab (when, source, counts, data size, store savedAt) | forever |
| Readable copy | `Summary`, `Budget`, `Trade`, `Material`, `Service`, `Other` tabs (latest version) | replaced each backup |
| Store versions (AWS) | S3 data bucket object versions of `store/store.json` | `StoreVersionRetentionDays` (365 in prod) |
| Device drafts | browser localStorage | until saved / discarded |

## Restore
* **From the app** (normal): Backups → pick the budget → Restore this copy → Are you sure? → the copy loads as unsaved
  changes (yellow bar). Check it, then Save for team, or **Undo restore**.
* **AWS, from S3 versions** (if the sheets are unavailable):
  ```bash
  aws s3api list-object-versions --bucket <DataBucket> --prefix store/store.json --query 'Versions[].[VersionId,LastModified,Size]' --output table
  aws s3api get-object --bucket <DataBucket> --key store/store.json --version-id <id> old.json
  # make it current again (a new version on top; nothing is lost)
  aws s3 cp old.json s3://<DataBucket>/store/store.json --content-type application/json
  ```
  or `GET /api/store?versionId=<id>` / `GET /api/store/history` with a signed-in token. Open tabs will get a conflict on
  their next save and reload (by design).
* **Claude artifact**: inject the JSON into the page (`tools/store_tool.py inject`) and republish (see rebuild-runbook).

## Daily backup — checks
* Claude: scheduled tasks list → "Daily calculator backup" → last run status / transcript (one line per budget).
* AWS: CloudWatch log group `/aws/lambda/<DailyBackupFunction>` (one JSON line per budget: backed up / skipped (why) /
  failed (step, why)); alarm email when any budget failed. Manual run:
  `aws lambda invoke --function-name <DailyBackupFunctionName> /tmp/out.json; cat /tmp/out.json`.
* Pause: `DAILY_BACKUP=false make deploy ENV=prod` (schedule disabled; or set `DailyBackupEnabled=false` in
  samconfig.toml) or disable the Claude task. Change the time: `BackupHour` / `BackupMinute` / `BackupTimeZone`.

## Users (AWS)
```bash
POOL=$(aws cloudformation describe-stacks --stack-name elite-calc-prod --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" --output text)
aws cognito-idp admin-create-user --user-pool-id $POOL --username person@company.com      # emails a temporary password
aws cognito-idp admin-disable-user --user-pool-id $POOL --username person@company.com
# optional read-only people: deploy with WRITERS_GROUP=writers and add savers to that group
aws cognito-idp create-group --user-pool-id $POOL --group-name writers
aws cognito-idp admin-add-user-to-group --user-pool-id $POOL --username person@company.com --group-name writers
```

## Updating the app
1. Change the live artifact (or `app/artifact/index.html`), run the tests (`python3 tests/run_all.py`).
2. Re-export into the repo after an artifact publish: `make export LIVE=/path/to/live.html` (publicize ids, sample store,
   rebuild standalone) → commit.
3. AWS: `make deploy ENV=prod` (uploads the new standalone build; data untouched). The daily Lambda reads the deployed
   page's engine markers, so backups follow automatically.

## Troubleshooting
| Symptom | Cause / fix |
|---|---|
| "Someone saved at the same time. The page reloads to their version." | Another person saved first. After reload the yellow bar offers **Download my changes** (stale draft); re-apply what is still needed. |
| "Your unsaved changes … weren’t loaded" | Same as above, from an older session on this device. Download or dismiss. |
| "Backups need the Google Sheets connector…" | Claude: connect Google Sheets/Drive connectors for the artifact. AWS: SSM parameter missing/invalid (`GOOGLE_CREDENTIALS_PARAM`), APIs not enabled, or the folder isn't shared with the service account. |
| "Refused by the server write policy" | A write targeted a sheet outside the backup folder / on the deny list. Check `BACKUP_FOLDER_ID`, or add a backup sheet that lives elsewhere to `ALLOW_SHEET_IDS`. Never add the invoice or master sheet. |
| New sheet creation fails (AWS) "storage quota" | Service accounts have no Drive quota: use a Shared drive folder, create the sheet by hand (`<budget name> – backup`), or use an OAuth refresh token (docs/config.md). |
| "another backup of this sheet ran at the same time" | Two backups overlapped; the sheet is fine. Run Back up now again in a minute. |
| "the new Summary tab came back empty, so the old tabs were kept" | Google returned an incomplete write; old tabs are intact. Retry. Leftover hidden "(updating)" tabs are cleaned by the next backup. |
| "This sheet was made by an older version of the calculator" (sync) | Back up now first, then edit the refreshed sheet. |
| To check: "no “To check” tab yet" | The tab is created by hand / by the review process in the backup sheet (row 3 header, data from row 4). |
| 401 loop on AWS | Cognito callback URL must equal the CloudFront URL with trailing `/`; clear site data; check `config.js`. |
| Cost alert | Check CloudWatch metrics for unusual API traffic; WAF is not included (internal app) — add AWS WAF if exposed widely. |

## Security notes
* Public repo: no secrets, no real ids, no real data. `make scan` (also in CI) looks for Google-id-like strings, keys and, when `config/private.json` exists locally, any of its values.
* Google: least privilege by sharing only the backup folder with the service account; the server guard blocks writes to
  anything else and to the deny list even if shared.
* S3 buckets are private (OAC for the site, Lambda-only for data), TLS-only bucket policies, SSE-S3 encryption, versioning.
* Cognito: admin-created users only, 12+ character passwords, tokens 1 h (refresh 30 days).

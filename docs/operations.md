# Operations

## Daily use
* Edit → yellow bar → **Save for team** (backs up to Google Sheets, then saves). Nothing is shared until saved.
* Backups window: **Back up now**, restore points, bring changes back from the sheet.
* The daily backup runs at 22:37 Edmonton (Claude task, or the AWS Lambda).

## Backups — what exists
| Copy | Where | Retention |
|---|---|---|
| Restore points | each budget's backup sheet, hidden tab `Backup data` (full store JSON per row) | until deleted by hand |
| Backup log | `Backup log` tab (when, source, counts, data size, store savedAt) | forever |
| Readable copy | `Summary`, `Budget`, `Trade`, `Material`, `Service`, `Other` tabs (latest version) | replaced each backup |
| Store versions (AWS) | S3 data bucket object versions of `store/store.json` | 365 days (lifecycle) |
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
* Pause: `DAILY_BACKUP=false ./infra/aws/deploy.sh` (schedule disabled) or disable the Claude task.

## Users (AWS)
```bash
POOL=$(aws cloudformation describe-stacks --stack-name elite-calc --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" --output text)
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
3. AWS: `./infra/aws/deploy.sh` (uploads the new standalone build; data untouched). The daily Lambda reads the deployed
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

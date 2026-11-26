# Configuration: ids, secrets, where they go

This repository is **public**. It contains no real Google ids, no credentials and no real business data. Real values live
in places that are never committed:

| Value | What it is | Where it goes |
|---|---|---|
| Backup Drive folder id | folder holding one backup sheet per budget | `config/private.json` → `BACKUP_FOLDER_ID` (build replaces `YOUR_BACKUP_FOLDER_ID` in the app; deploy passes it to Lambda env `BACKUP_FOLDER_ID`) |
| Invoice sheet id | the team's own invoice sheet: **read-only forever** | `config/private.json` → `INVOICE_SHEET_ID` (replaces `YOUR_INVOICE_SHEET_ID` in `TC_RO`; deploy adds it to `DENY_SHEET_IDS`) |
| Retired master sheet id | old combined backup sheet: never written | `config/private.json` → `MASTER_SHEET_ID` (same as above) |
| Name hints | example names in the To check "Your name" field and note placeholder | `config/private.json` → `NAME_HINT`, `NOTE_HINT` (public copy says "e.g. Alex" / "Checked with Jordan") |
| Budget backup sheet ids | e.g. the first budget's backup sheet | inside the team store (`budget.sheetId`), never in code |
| Google credentials | service account key JSON (or OAuth refresh token JSON) | SSM Parameter Store SecureString (`/elite-calc/google-credentials`), uploaded by `deploy.sh` from `GOOGLE_CREDENTIALS_FILE`; local dev: env `GOOGLE_CREDENTIALS_FILE` |
| Team store | real projects, budgets, invoices | S3 data bucket (AWS) / the artifact page (Claude) / Google `Backup data` restore points |
| Artifact slug | the live Claude artifact | team notes only |

`config/private.example.json` shows the format. `.gitignore` excludes `config/private.json`, `*.key.json`, `data/`,
`backups/`, `google-credentials*.json`.

## Restoring the exact live artifact (1:1)
```bash
python3 tools/store_tool.py privatize app/artifact/index.html config/private.json /tmp/live.html   # real ids back in
python3 tools/store_tool.py inject /tmp/live.html /path/to/real-store.json /tmp/live.html            # real data back in
```
The code is byte-identical to the live artifact; the store JSON is identical in content (the app writes compact JSON).
The real store comes from: the latest `Backup data` row of a budget's backup sheet (Backups → Restore this copy, then
Export), the S3 data bucket, or the app's **Export** (`elitecraft-projects.json`).

## Google service account setup (AWS build)
1. Google Cloud project → enable **Google Sheets API** and **Google Drive API** → create a service account → key (JSON).
2. Share the **backup folder** with the service account email as *Editor*. Share nothing else (it then cannot even see
   the invoice sheet). If the To check tab or sync needs other sheets, share them as *Viewer* only.
3. Service accounts have no Drive storage quota of their own: new backup sheets must be created in a **Shared drive**
   folder, or create each budget's sheet by hand in the folder (named `<budget name> – backup`) so the backend only edits
   it. Alternative: store an OAuth refresh token of a team Google account instead
   (`{"type":"authorized_user","client_id","client_secret","refresh_token"}`), then files are owned by that user.
4. `GOOGLE_CREDENTIALS_FILE=key.json ./infra/aws/deploy.sh` (stored as SecureString; delete the local file after).

## Lambda environment (set by the template)
`DATA_BUCKET, STORE_KEY=store/store.json, SITE_BUCKET, APP_KEY=index.html, GOOGLE_CREDENTIALS_PARAM, BACKUP_FOLDER_ID,
ALLOW_SHEET_IDS, DENY_SHEET_IDS, WRITERS_GROUP, BACKUP_TIME_ZONE=America/Edmonton` (+ optional `GOOGLE_IMPERSONATE` for
domain-wide delegation, `MAX_STORE_BYTES`).

## Frontend config (`config.js`, generated)
```js
window.ELITE_CONFIG = { apiBase: '/api', auth: { mode: 'cognito', domain: '<prefix>.auth.<region>.amazoncognito.com',
  clientId: '<app client id>', redirectUri: 'https://<distribution>/' }, sheets: true };
```
`auth.mode: 'none'` for the local server; `sheets: false` hides Google features (the app shows "not available in this view").

# Decisions (ADR log)

## D1. Keep the single-file app and adapt the host, not the app
The app is proven (tests, team habits) and built as a Claude artifact. The AWS build reuses the exact HTML and adds
`platform.js`, which implements the three `window.claude` capabilities the app uses (`artifact.publish`,
`downloads.save`, `mcp.callTool`). Zero changes to app logic → one source of truth, artifact and AWS can't drift, and
`build_standalone.mjs` re-exports any future artifact version automatically.

## D2. Store in S3 (versioned) rather than DynamoDB
* The store is one JSON document (~100 KB today, growing with invoices). DynamoDB items are capped at **400 KB** — it would
  need splitting. S3 has no practical limit.
* S3 conditional writes (`If-Match` ETag / `If-None-Match: *`) give the same optimistic concurrency as a DynamoDB
  condition expression.
* Versioning gives free server-side restore points (365-day lifecycle).
* Cost: a few cents a month either way; S3 is simpler (no table, no capacity settings).

## D3. CloudFront in front of both the site and the API
One origin for the browser → no CORS, one URL, HTTPS everywhere, S3 bucket stays private (OAC). `/api/*` uses a cache
policy with TTL 0/0/1 that includes the `Authorization` header (required to forward it; responses are `no-store`).
PriceClass_100 is the cheapest.

## D4. HTTP API + Lambda (not REST API, not containers)
HTTP API is ~70 % cheaper than REST API and has a native JWT authorizer for Cognito. Lambda arm64 (Graviton) is the
cheapest compute; no idle cost. Runtime: the code targets Node ≥ 20 (as requested); the template defaults to
`nodejs24.x` because AWS ended support for `nodejs20.x` on 2026-04-30 (parameter `LambdaRuntime` allows 20/22/24).
No dependencies: `@aws-sdk/client-s3` / `client-ssm` come with the runtime; the Google client is ~80 lines of `fetch` +
`crypto` (JWT RS256).

## D5. Cognito user pool (Lite tier) with hosted UI
Free for < 10,000 MAU, managed sign-in page, admin-only sign-up, JWTs validated by API Gateway. Alternative for very
small teams: CloudFront + a shared secret / IP allow list (not chosen: weaker, no per-person audit). Optional
`WRITERS_GROUP` adds read-only users.

## D6. Google access via a service account in SSM, behind a server-side guard
Claude connectors act as the signed-in user; on AWS the backend needs its own identity. Service account key in an SSM
**SecureString** (free, encrypted with the AWS-managed key) — Secrets Manager costs $0.40/secret/month and rotation isn't
needed for this key. Created by `deploy.sh` (CloudFormation can't create SecureStrings). OAuth refresh token supported as
an alternative (service accounts can't own Drive files outside Shared drives). The guard (D7) makes the "originals are
read-only" rule a hard server rule.

## D7. Enforce write rules in the backend
Writes only to sheets in the backup folder (or an explicit allow list); deny list (invoice sheet, master sheet) always
wins; only the request types the calculator uses; deleteSheet only for the six data tabs; To check only K:L of one row;
restore points append-only. The app's own checks stay as a second layer.

## D8. Daily backup as a Lambda that reads the deployed page
Same as the Claude task: the engine/builders are cut out of the page by markers, so layout changes in the app need no
backend change. EventBridge Scheduler supports time zones natively (`America/Edmonton`, DST-safe).

## D9. Public repo hygiene
The real store (financials, vendors, invoices) and real Google ids are never committed. The artifact copy carries a
made-up sample store (same shape, invented names/amounts) and placeholders (`YOUR_BACKUP_FOLDER_ID`, …) that
`tools/store_tool.py privatize` / `build_standalone.mjs --ids` replace from a gitignored `config/private.json`.
Test expectations were recalibrated to the sample data (same checks, different numbers).

## D10. IaC choice: AWS SAM / CloudFormation
The team runs on AWS only. `infra/aws/template.yaml` is a
SAM template deployed by CloudFormation, with per-environment values in `infra/aws/samconfig.toml`.
* **Why**: free (no charge for CloudFormation itself); AWS-native, every service used here is supported on day one;
  **no state file to host or lock** (AWS keeps the stack state); **change sets** show exactly what will be added,
  modified or replaced before anything happens (`make plan`); **automatic rollback** when an update fails; **drift
  detection** for console edits (`make drift`); stack **outputs** feed the deploy script; stack tags propagate to every
  resource (`App` / `Env` / `CostCenter` for cost tracking). Every tunable is a Parameter with a cheap default, so the
  template never has to be edited to change a setting.
* **Terraform / OpenTofu — not chosen**: needs a remote state backend (S3 bucket + DynamoDB lock table, or a paid
  service) that itself has to be created, secured and backed up outside the code; provider version upgrades to track;
  no server-side rollback.
* **AWS CDK — not chosen**: synthesizes to the same CloudFormation, but adds a build step and a programming-language
  toolchain (node_modules, `cdk bootstrap` stack) for a template of this size; the reviewed artifact is generated, not
  written.
* SAM CLI is optional: `deploy.sh` uses only the AWS CLI (`cloudformation package` / change sets); `sam deploy
  --config-env prod` and `sam validate --lint` work with the same files.
* The HTTP API is written as plain `AWS::ApiGatewayV2::*` resources rather than `AWS::Serverless::HttpApi`: SAM embeds
  the JWT authorizer (and so the user pool client) in the API definition, which made API → client → CloudFront
  (callback URL) → API a circular dependency (cfn-lint E3004).

## D11. Upgrades in the backup sheet as sub-rows
Columns A–J keep their meaning (so restore/sync keep working); upgrades are extra rows marked in column J (`up:`, `sub:`)
that sync ignores. Summary gains "Budget and upgrades" tiles and an Upgrades section only when upgrades exist.

## D12. To check writes only K:L
The review sheet's other columns belong to the reviewer; the calculator records Status + a history line per answer, and
keeps a reversible record in `budget.toCheck` so Reopen and Discard can undo budget effects and sheet rows.

#!/usr/bin/env bash
# One-command deploy of the calculator to AWS (needs: aws CLI v2 with credentials, node >= 20, python3).
#
#   ALERT_EMAIL=you@company.com COGNITO_DOMAIN_PREFIX=elitecraft-calc ./infra/aws/deploy.sh
#
# Optional environment:
#   STACK=elite-calc  REGION=ca-central-1  ADMIN_EMAIL=first.user@company.com
#   GOOGLE_CREDENTIALS_FILE=./google-key.json   stored as SSM SecureString $GOOGLE_PARAM (never committed)
#   GOOGLE_PARAM=/elite-calc/google-credentials
#   IDS_FILE=config/private.json                backup folder / invoice sheet / master sheet ids (gitignored, see config/private.example.json)
#   STORE_FILE=./store.json                     initial team data; uploaded ONLY if the data bucket has no store yet
#                                               (default: samples/store.sample.json, made-up data)
#   MONTHLY_BUDGET_USD=5  WRITERS_GROUP=  DAILY_BACKUP=true  LAMBDA_RUNTIME=nodejs24.x
set -euo pipefail
cd "$(dirname "$0")/../.."
ROOT=$(pwd)
STACK=${STACK:-elite-calc}
REGION=${REGION:-ca-central-1}
GOOGLE_PARAM=${GOOGLE_PARAM:-/$STACK/google-credentials}
IDS_FILE=${IDS_FILE:-config/private.json}
: "${ALERT_EMAIL:?set ALERT_EMAIL}"
: "${COGNITO_DOMAIN_PREFIX:?set COGNITO_DOMAIN_PREFIX (globally unique, lowercase)}"
command -v aws >/dev/null || { echo "aws CLI v2 is required"; exit 1; }
command -v node >/dev/null || { echo "node >= 20 is required"; exit 1; }
export AWS_REGION=$REGION AWS_DEFAULT_REGION=$REGION
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)

json_get() { python3 -c "import json,sys;d=json.load(open('$IDS_FILE'));print(d.get('$1',''))" 2>/dev/null || true; }
BACKUP_FOLDER_ID=${BACKUP_FOLDER_ID:-$( [ -f "$IDS_FILE" ] && json_get BACKUP_FOLDER_ID )}
DENY_SHEET_IDS=${DENY_SHEET_IDS:-$( [ -f "$IDS_FILE" ] && python3 -c "import json;d=json.load(open('$IDS_FILE'));print(','.join(x for x in [d.get('INVOICE_SHEET_ID'),d.get('MASTER_SHEET_ID')]+d.get('EXTRA_DENY_SHEET_IDS',[]) if x))" )}
[ -n "${BACKUP_FOLDER_ID:-}" ] || echo "WARNING: no BACKUP_FOLDER_ID: Google Sheets writes will be refused until you set it."

echo "== 1/6 Google credentials -> SSM SecureString $GOOGLE_PARAM"
if [ -n "${GOOGLE_CREDENTIALS_FILE:-}" ]; then
  aws ssm put-parameter --name "$GOOGLE_PARAM" --type SecureString --overwrite --value "file://$GOOGLE_CREDENTIALS_FILE" >/dev/null
  echo "   stored"
else
  echo "   skipped (GOOGLE_CREDENTIALS_FILE not set; backups need it)"
fi

echo "== 2/6 package Lambda code"
ART="${STACK}-artifacts-${ACCOUNT}-${REGION}"
aws s3api head-bucket --bucket "$ART" 2>/dev/null || {
  if [ "$REGION" = us-east-1 ]; then aws s3api create-bucket --bucket "$ART" >/dev/null; else aws s3api create-bucket --bucket "$ART" --create-bucket-configuration LocationConstraint="$REGION" >/dev/null; fi
  aws s3api put-public-access-block --bucket "$ART" --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
  aws s3api put-bucket-lifecycle-configuration --bucket "$ART" --lifecycle-configuration '{"Rules":[{"ID":"expire","Status":"Enabled","Filter":{},"Expiration":{"Days":30}}]}'
}
mkdir -p infra/aws/.build
aws cloudformation package --template-file infra/aws/template.yaml --s3-bucket "$ART" --s3-prefix lambda --output-template-file infra/aws/.build/packaged.yaml >/dev/null

echo "== 3/6 deploy stack $STACK ($REGION)"
aws cloudformation deploy --stack-name "$STACK" --template-file infra/aws/.build/packaged.yaml \
  --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND --no-fail-on-empty-changeset \
  --parameter-overrides AppName="$STACK" AlertEmail="$ALERT_EMAIL" AdminEmail="${ADMIN_EMAIL:-}" \
    CognitoDomainPrefix="$COGNITO_DOMAIN_PREFIX" GoogleCredentialsParam="$GOOGLE_PARAM" \
    BackupFolderId="${BACKUP_FOLDER_ID:-}" DenySheetIds="${DENY_SHEET_IDS:-}" AllowSheetIds="${ALLOW_SHEET_IDS:-}" \
    WritersGroup="${WRITERS_GROUP:-}" MonthlyBudgetUsd="${MONTHLY_BUDGET_USD:-5}" DailyBackupEnabled="${DAILY_BACKUP:-true}" \
    LambdaRuntime="${LAMBDA_RUNTIME:-nodejs24.x}"
out() { aws cloudformation describe-stacks --stack-name "$STACK" --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text; }
URL=$(out AppUrl); SITE=$(out SiteBucketName); DATA=$(out DataBucketName); DIST=$(out DistributionId)
CLIENT=$(out UserPoolClientId); DOMAIN=$(out CognitoDomain)

echo "== 4/6 build the standalone app"
cat > infra/aws/.build/config.json <<EOF
{"apiBase":"/api","auth":{"mode":"cognito","domain":"$DOMAIN","clientId":"$CLIENT","redirectUri":"$URL"},"sheets":true}
EOF
node app/build/build_standalone.mjs --out infra/aws/.build/site --config infra/aws/.build/config.json $( [ -f "$IDS_FILE" ] && echo "--ids $IDS_FILE" )

echo "== 5/6 upload app + initial data"
for f in index.html platform.js config.js; do
  aws s3 cp "infra/aws/.build/site/$f" "s3://$SITE/$f" --cache-control "no-cache" --only-show-errors
done
if ! aws s3api head-object --bucket "$DATA" --key store/store.json >/dev/null 2>&1; then
  SRC=${STORE_FILE:-samples/store.sample.json}
  aws s3api put-object --bucket "$DATA" --key store/store.json --body "$SRC" --content-type application/json --if-none-match '*' >/dev/null
  echo "   initial store uploaded from $SRC"
else
  echo "   store already exists: left untouched"
fi

echo "== 6/6 refresh CDN"
aws cloudfront create-invalidation --distribution-id "$DIST" --paths /index.html /config.js /platform.js >/dev/null
echo
echo "Done. Calculator: $URL"
echo "Sign-in users: aws cognito-idp admin-create-user --user-pool-id $(out UserPoolId) --username name@company.com"
echo "Confirm the SNS alert subscription email sent to $ALERT_EMAIL."

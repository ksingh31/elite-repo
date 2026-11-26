#!/usr/bin/env bash
# Deploy the calculator to AWS with CloudFormation (needs: aws CLI v2 with credentials, node >= 20, python3 >= 3.11).
# Every deploy first creates a CHANGE SET and prints exactly what will be added / modified / replaced / removed.
#
#   ./infra/aws/deploy.sh --plan            preview only (= make plan): change set is created and shown, nothing changes
#   ./infra/aws/deploy.sh                   preview, ask "Apply?", apply, then build + upload the app (= make deploy)
#   YES=1 ./infra/aws/deploy.sh             same without the question (CI)
#
# Settings: ENV=dev|prod picks the section of infra/aws/samconfig.toml (stack name, region, parameters, tags).
# Real values come from the environment (never commit them):
#   ALERT_EMAIL=ops@company.com COGNITO_DOMAIN_PREFIX=elitecraft-calc   (required unless set in samconfig)
#   ADMIN_EMAIL=first.user@company.com  DOMAIN_NAME=calc.company.com CERTIFICATE_ARN=arn:aws:acm:us-east-1:...
#   GOOGLE_CREDENTIALS_FILE=./google-key.json   stored as SSM SecureString (GoogleCredentialsParam; never committed)
#   IDS_FILE=config/private.json                backup folder / invoice sheet / master sheet ids (gitignored)
#   STORE_FILE=./store.json                     initial team data; uploaded ONLY if the data bucket has no store yet
#                                               (default: samples/store.sample.json, made-up data)
#   PARAMS_EXTRA="ApiMemoryMb=512 BackupHour=23" any other template parameter (list: docs/operations.md)
#   STACK / REGION                              override samconfig
set -euo pipefail
cd "$(dirname "$0")/../.."
PLAN=no; [ "${1:-}" = "--plan" ] && PLAN=yes
IDS_FILE=${IDS_FILE:-config/private.json}
command -v aws >/dev/null || { echo "aws CLI v2 is required"; exit 1; }
command -v node >/dev/null || { echo "node >= 20 is required"; exit 1; }

if [ -f "$IDS_FILE" ]; then
  BACKUP_FOLDER_ID=${BACKUP_FOLDER_ID:-$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('BACKUP_FOLDER_ID',''))" "$IDS_FILE")}
  DENY_SHEET_IDS=${DENY_SHEET_IDS:-$(python3 -c "import json,sys;d=json.load(open(sys.argv[1]));print(','.join(x for x in [d.get('INVOICE_SHEET_ID'),d.get('MASTER_SHEET_ID')]+d.get('EXTRA_DENY_SHEET_IDS',[]) if x))" "$IDS_FILE")}
  export BACKUP_FOLDER_ID DENY_SHEET_IDS
fi
# shellcheck source=infra/aws/env.sh
source infra/aws/env.sh
ALERT=$(param AlertEmail); PREFIX=$(param CognitoDomainPrefix); GOOGLE_PARAM=$(param GoogleCredentialsParam)
case "$ALERT" in ''|*@example.com) echo "set ALERT_EMAIL (samconfig has a placeholder)"; exit 1;; esac
case "$PREFIX" in ''|change-me*) echo "set COGNITO_DOMAIN_PREFIX (globally unique, lowercase; samconfig has a placeholder)"; exit 1;; esac
[ -n "$(param BackupFolderId)" ] || echo "WARNING: no BACKUP_FOLDER_ID: Google Sheets writes will be refused until you set it."
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
echo "Stack $STACK  env $ENV  region $REGION  account $ACCOUNT"

echo "== 1/7 package Lambda code"
ART="${STACK}-artifacts-${ACCOUNT}-${REGION}"
aws s3api head-bucket --bucket "$ART" 2>/dev/null || {
  if [ "$REGION" = us-east-1 ]; then aws s3api create-bucket --bucket "$ART" >/dev/null; else aws s3api create-bucket --bucket "$ART" --create-bucket-configuration LocationConstraint="$REGION" >/dev/null; fi
  aws s3api put-public-access-block --bucket "$ART" --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
  aws s3api put-bucket-lifecycle-configuration --bucket "$ART" --lifecycle-configuration '{"Rules":[{"ID":"expire","Status":"Enabled","Filter":{},"Expiration":{"Days":30}}]}'
  aws s3api put-bucket-tagging --bucket "$ART" --tagging "{\"TagSet\":[$(for t in "${TAGS[@]}"; do printf '{"Key":"%s","Value":"%s"},' "${t%%=*}" "${t#*=}"; done | sed 's/,$//')]}"
}
mkdir -p infra/aws/.build
aws cloudformation package --template-file infra/aws/template.yaml --s3-bucket "$ART" --s3-prefix lambda --output-template-file infra/aws/.build/packaged.yaml >/dev/null

echo "== 2/7 change set (preview)"
# drop stale, never-applied previews so the one shown below is this run's
for cs in $(aws cloudformation list-change-sets --stack-name "$STACK" --query "Summaries[?ExecutionStatus=='AVAILABLE'].ChangeSetName" --output text 2>/dev/null || true); do
  aws cloudformation delete-change-set --stack-name "$STACK" --change-set-name "$cs"
done
BEFORE=$(aws cloudformation describe-stacks --stack-name "$STACK" --query "Stacks[0].StackStatus" --output text 2>/dev/null || echo NONE)
aws cloudformation deploy --stack-name "$STACK" --template-file infra/aws/.build/packaged.yaml \
  --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND --no-fail-on-empty-changeset --no-execute-changeset \
  --parameter-overrides "${PARAMS[@]}" --tags "${TAGS[@]}" >/dev/null
CS=$(aws cloudformation list-change-sets --stack-name "$STACK" --query "sort_by(Summaries[?ExecutionStatus=='AVAILABLE'],&CreationTime)[-1].ChangeSetName" --output text 2>/dev/null || echo None)
if [ "$CS" = None ] || [ -z "$CS" ]; then
  echo "   no infrastructure changes"
else
  aws cloudformation describe-change-set --stack-name "$STACK" --change-set-name "$CS" \
    --query "Changes[].ResourceChange.{Action:Action,Resource:LogicalResourceId,Type:ResourceType,Replace:Replacement}" --output table
  if [ "$PLAN" = yes ]; then
    echo "Plan only: nothing changed. Apply with: make deploy ENV=$ENV   (or discard: aws cloudformation delete-change-set --stack-name $STACK --change-set-name $CS)"
    exit 0
  fi
  if [ "${YES:-}" != 1 ]; then
    [ -t 0 ] || { echo "not a terminal: set YES=1 to apply without the question"; exit 1; }
    read -r -p "Apply these changes to $STACK? [y/N] " a; [ "$a" = y ] || [ "$a" = Y ] || { echo "cancelled (change set $CS kept for review)"; exit 1; }
  fi
  echo "== 3/7 apply (CloudFormation rolls back automatically if anything fails)"
  aws cloudformation execute-change-set --stack-name "$STACK" --change-set-name "$CS"
  case "$BEFORE" in NONE|REVIEW_IN_PROGRESS) aws cloudformation wait stack-create-complete --stack-name "$STACK";; *) aws cloudformation wait stack-update-complete --stack-name "$STACK";; esac
fi
[ "$PLAN" = yes ] && exit 0

echo "== 4/7 Google credentials -> SSM SecureString $GOOGLE_PARAM"
if [ -n "${GOOGLE_CREDENTIALS_FILE:-}" ]; then
  aws ssm put-parameter --name "$GOOGLE_PARAM" --type SecureString --overwrite --value "file://$GOOGLE_CREDENTIALS_FILE" >/dev/null
  echo "   stored"
else
  echo "   skipped (GOOGLE_CREDENTIALS_FILE not set; backups need it)"
fi

out() { aws cloudformation describe-stacks --stack-name "$STACK" --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text; }
URL=$(out AppUrl); SITE=$(out SiteBucketName); DATA=$(out DataBucketName); DIST=$(out DistributionId)
CLIENT=$(out UserPoolClientId); DOMAIN=$(out CognitoDomain)

echo "== 5/7 build the standalone app"
cat > infra/aws/.build/config.json <<EOF
{"apiBase":"/api","auth":{"mode":"cognito","domain":"$DOMAIN","clientId":"$CLIENT","redirectUri":"$URL"},"sheets":true}
EOF
node app/build/build_standalone.mjs --out infra/aws/.build/site --config infra/aws/.build/config.json $( [ -f "$IDS_FILE" ] && echo "--ids $IDS_FILE" )

echo "== 6/7 upload app + initial data"
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

echo "== 7/7 refresh CDN"
aws cloudfront create-invalidation --distribution-id "$DIST" --paths /index.html /config.js /platform.js >/dev/null
echo
echo "Done. Calculator: $URL"
echo "Sign-in users: aws cognito-idp admin-create-user --user-pool-id $(out UserPoolId) --username name@company.com"
echo "Confirm the SNS alert subscription email sent to $ALERT."

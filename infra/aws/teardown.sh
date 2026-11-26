#!/usr/bin/env bash
# Removes the stack. The team data bucket is RETAINED by default (DeletionPolicy: Retain) so data can't be lost by accident.
#   ./infra/aws/teardown.sh                    delete the stack, keep the data bucket (a final store copy is downloaded first)
#   DELETE_DATA=yes ./infra/aws/teardown.sh    also delete the data bucket and every saved version (irreversible)
set -euo pipefail
cd "$(dirname "$0")/../.."
STACK=${STACK:-elite-calc}
REGION=${REGION:-ca-central-1}
export AWS_REGION=$REGION AWS_DEFAULT_REGION=$REGION
out() { aws cloudformation describe-stacks --stack-name "$STACK" --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text; }
SITE=$(out SiteBucketName); DATA=$(out DataBucketName)
mkdir -p backups
aws s3 cp "s3://$DATA/store/store.json" "backups/store-$(date +%Y%m%d-%H%M%S).json" --only-show-errors && echo "store copy saved in backups/ (gitignored? add it: it contains real data)"

empty_bucket() { # deletes every object version + delete marker
  local b=$1
  python3 - "$b" <<'PY'
import json, subprocess, sys
b = sys.argv[1]
while True:
    r = json.loads(subprocess.check_output(['aws', 's3api', 'list-object-versions', '--bucket', b, '--max-items', '1000', '--output', 'json']) or b'{}')
    objs = [{'Key': o['Key'], 'VersionId': o['VersionId']} for o in (r.get('Versions') or []) + (r.get('DeleteMarkers') or [])]
    if not objs: break
    subprocess.check_call(['aws', 's3api', 'delete-objects', '--bucket', b, '--delete', json.dumps({'Objects': objs, 'Quiet': True})])
PY
}
empty_bucket "$SITE"
aws cloudformation delete-stack --stack-name "$STACK"
aws cloudformation wait stack-delete-complete --stack-name "$STACK"
echo "stack deleted"
if [ "${DELETE_DATA:-no}" = yes ]; then
  empty_bucket "$DATA" && aws s3api delete-bucket --bucket "$DATA" && echo "data bucket deleted"
else
  echo "data bucket kept: $DATA"
fi
echo "SSM parameter /$STACK/google-credentials is kept; remove with: aws ssm delete-parameter --name /$STACK/google-credentials"

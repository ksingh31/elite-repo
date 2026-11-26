#!/usr/bin/env bash
# Day-2 commands for the stack picked by ENV (samconfig.toml section; default dev).
#   ./infra/aws/ops.sh outputs   stack status + outputs (app URL, bucket names, user pool, function names)   = make outputs
#   ./infra/aws/ops.sh drift     detect resources changed outside CloudFormation (console edits) and list them = make drift
#   ./infra/aws/ops.sh events    last 25 stack events (why a deploy failed / rolled back)                    = make events
set -euo pipefail
cd "$(dirname "$0")/../.."
# shellcheck source=infra/aws/env.sh
source infra/aws/env.sh
case "${1:-outputs}" in
  outputs)
    aws cloudformation describe-stacks --stack-name "$STACK" --query "Stacks[0].[StackName,StackStatus,LastUpdatedTime||CreationTime]" --output text
    aws cloudformation describe-stacks --stack-name "$STACK" --query "Stacks[0].Outputs[].[OutputKey,OutputValue]" --output table ;;
  drift)
    ID=$(aws cloudformation detect-stack-drift --stack-name "$STACK" --query StackDriftDetectionId --output text)
    while [ "$(aws cloudformation describe-stack-drift-detection-status --stack-drift-detection-id "$ID" --query DetectionStatus --output text)" = DETECTION_IN_PROGRESS ]; do sleep 3; done
    aws cloudformation describe-stack-drift-detection-status --stack-drift-detection-id "$ID" --query "[StackDriftStatus,DriftedStackResourceCount]" --output text
    aws cloudformation describe-stack-resource-drifts --stack-name "$STACK" --stack-resource-drift-status-filters MODIFIED DELETED \
      --query "StackResourceDrifts[].{Resource:LogicalResourceId,Status:StackResourceDriftStatus,Diff:PropertyDifferences[].PropertyPath|join(', ',@)}" --output table
    echo "Fix drift by re-applying the template (make deploy ENV=$ENV) or by putting the console change into the template." ;;
  events)
    aws cloudformation describe-stack-events --stack-name "$STACK" --max-items 25 \
      --query "StackEvents[].[Timestamp,LogicalResourceId,ResourceStatus,ResourceStatusReason]" --output table ;;
  *) echo "usage: $0 outputs|drift|events"; exit 1 ;;
esac

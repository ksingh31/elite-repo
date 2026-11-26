#!/usr/bin/env bash
# Sourced by deploy.sh / ops.sh / teardown.sh. Reads infra/aws/samconfig.toml for ENV (default dev) and sets:
#   STACK  REGION  TAGS (array, Key=Value)  PARAMS (array, Key=Value: samconfig, then env-var overrides, then $PARAMS_EXTRA)
# Env-var overrides (so real values never go into the public samconfig): ALERT_EMAIL ADMIN_EMAIL COGNITO_DOMAIN_PREFIX
#   BACKUP_FOLDER_ID ALLOW_SHEET_IDS DENY_SHEET_IDS WRITERS_GROUP MONTHLY_BUDGET_USD DAILY_BACKUP LAMBDA_RUNTIME
#   DOMAIN_NAME CERTIFICATE_ARN GOOGLE_PARAM COST_CENTER; any other parameter: PARAMS_EXTRA="Key=Value Key2=Value2".
# STACK / REGION env vars override the samconfig stack_name / region.
ENV=${ENV:-dev}
SAMCONFIG=${SAMCONFIG:-infra/aws/samconfig.toml}
eval "$(ENV="$ENV" SAMCONFIG="$SAMCONFIG" python3 - <<'PY'
import os, shlex, sys, tomllib
env = os.environ['ENV']; section = 'default' if env == 'dev' else env
cfg = tomllib.load(open(os.environ['SAMCONFIG'], 'rb'))
if section not in cfg:
    sys.exit(f'echo "unknown ENV={env}: no [{section}] section in samconfig.toml" >&2; exit 1')
d = cfg[section].get('deploy', {}).get('parameters', {})
po = d.get('parameter_overrides', [])
po = po if isinstance(po, list) else shlex.split(po)
params = dict(p.split('=', 1) for p in po)
m = {'ALERT_EMAIL': 'AlertEmail', 'ADMIN_EMAIL': 'AdminEmail', 'COGNITO_DOMAIN_PREFIX': 'CognitoDomainPrefix',
     'BACKUP_FOLDER_ID': 'BackupFolderId', 'ALLOW_SHEET_IDS': 'AllowSheetIds', 'DENY_SHEET_IDS': 'DenySheetIds',
     'WRITERS_GROUP': 'WritersGroup', 'MONTHLY_BUDGET_USD': 'MonthlyBudgetUsd', 'DAILY_BACKUP': 'DailyBackupEnabled',
     'LAMBDA_RUNTIME': 'LambdaRuntime', 'DOMAIN_NAME': 'DomainName', 'CERTIFICATE_ARN': 'CertificateArn',
     'GOOGLE_PARAM': 'GoogleCredentialsParam', 'COST_CENTER': 'CostCenter'}
for k, p in m.items():
    if os.environ.get(k):
        params[p] = os.environ[k]
for p in shlex.split(os.environ.get('PARAMS_EXTRA', '')):
    k, v = p.split('=', 1); params[k] = v
tags = dict(t.split('=', 1) for t in shlex.split(d.get('tags', '')))
if 'CostCenter' in params: tags['CostCenter'] = params['CostCenter']
q = shlex.quote
print(f"STACK=${{STACK:-{q(d.get('stack_name', 'elite-calc-' + env))}}}")
print(f"REGION=${{REGION:-{q(d.get('region', 'ca-central-1'))}}}")
print('PARAMS=(' + ' '.join(q(f'{k}={v}') for k, v in params.items()) + ')')
print('TAGS=(' + ' '.join(q(f'{k}={v}') for k, v in tags.items()) + ')')
PY
)"
param() { local p; for p in "${PARAMS[@]}"; do [ "${p%%=*}" = "$1" ] && { echo "${p#*=}"; return; }; done; }
export AWS_REGION=$REGION AWS_DEFAULT_REGION=$REGION

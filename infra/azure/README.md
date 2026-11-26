# Azure (optional alternative, not validated)

AWS (`infra/aws`) is the primary, tested deployment. This folder is a minimal Azure equivalent requested as a Bicep
option. **It was not compiled or deployed in the build environment** (no Azure CLI / Bicep CLI available there); run
`az bicep build --file infra/azure/main.bicep` first and expect small fixes.

| AWS | Azure (main.bicep) |
|---|---|
| S3 + CloudFront | Static Web App, Free tier |
| API Gateway HTTP API + Lambda | Function App, Linux consumption (Y1), Node 20, `api/azure/adapter.mjs` |
| S3 versioned store, `If-Match` | Blob container `store`, versioning on, `ifMatch` ETag |
| SSM SecureString | Key Vault secret `google-credentials` (Key Vault reference in app settings) |
| Cognito | App Service Authentication (Microsoft Entra ID) on the Function App — configure in the portal / `az webapp auth` |
| EventBridge Scheduler 22:37 Edmonton | Timer trigger every hour at :37, runs when Edmonton time is 22:37 |
| CloudWatch + Budget | Application Insights; add a Cost Management budget in the portal |

Cost: Static Web Apps Free $0, Functions consumption free grant (1M executions), Storage LRS cents, Key Vault
~$0.03/10k operations → **≈ $0–1/month**.

## Deploy (outline)
```bash
az group create -n elite-calc -l canadacentral
az deployment group create -g elite-calc -f infra/azure/main.bicep \
  -p backupFolderId=<folder> denySheetIds=<invoice>,<master> adminObjectId=$(az ad signed-in-user show --query id -o tsv)
az keyvault secret set --vault-name <keyVaultName> -n google-credentials --file google-key.json
# API: package api/src + api/azure with @azure/functions @azure/storage-blob @azure/identity, then
func azure functionapp publish <functionAppName>
# Web: build with apiBase pointing at the function app and auth mode 'none' (EasyAuth cookie on the API domain)
echo '{"apiBase":"https://<functionAppName>.azurewebsites.net/api","auth":{"mode":"none"},"sheets":true}' > /tmp/cfg.json
node app/build/build_standalone.mjs --out /tmp/site --config /tmp/cfg.json --ids config/private.json
npx @azure/static-web-apps-cli deploy /tmp/site --deployment-token <token>
# upload the initial store
az storage blob upload --account-name <storage> -c store -n store/store.json -f samples/store.sample.json --auth-mode login
```
Cross-origin note: with the Free Static Web App the API is on another domain, so the Entra sign-in cookie must be sent
cross-site (`fetch(..., {credentials:'include'})` in `platform.js` and CORS `supportCredentials`). The simplest robust
setup is a Static Web App **Standard** plan with the Function App linked as its backend (same origin, ~$9/month).

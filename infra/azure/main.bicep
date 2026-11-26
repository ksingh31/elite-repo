// OPTIONAL Azure alternative to infra/aws (AWS is the primary, tested deployment).
// Minimal equivalent: Static Web App (Free) for the standalone build, Azure Functions (Linux consumption, Node 20)
// running the same API code through api/azure/adapter.mjs, a Storage account (blob container "store" with ETag
// concurrency + blob versioning = restore points), Key Vault for the Google credentials JSON, Application Insights.
// Not deployed or validated in the build environment (no Azure CLI there). See README.md in this folder.
targetScope = 'resourceGroup'

@description('Short lowercase name used in resource names')
@minLength(3)
@maxLength(12)
param appName string = 'elitecalc'

param location string = resourceGroup().location

@description('Static Web Apps is only offered in some regions')
param swaLocation string = 'centralus'

@description('Google Drive folder that holds the per-budget backup sheets')
param backupFolderId string = ''

@description('Comma separated sheet ids that must never be written (invoice sheet, retired master sheet)')
param denySheetIds string = ''

@description('Comma separated extra backup sheet ids that may be written')
param allowSheetIds string = ''

@description('Object id of the person/group that may set the Key Vault secret')
param adminObjectId string

var suffix = uniqueString(resourceGroup().id)
var storageName = toLower('${appName}${take(suffix, 8)}')

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    supportsHttpsTrafficOnly: true
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
  properties: {
    isVersioningEnabled: true            // every save is a version (restore points)
    deleteRetentionPolicy: { enabled: true, days: 30 }
  }
}

resource storeContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: 'store'
  properties: { publicAccess: 'None' }
}

resource lifecycle 'Microsoft.Storage/storageAccounts/managementPolicies@2023-05-01' = {
  parent: storage
  name: 'default'
  properties: {
    policy: {
      rules: [
        {
          name: 'old-versions-1-year'
          enabled: true
          type: 'Lifecycle'
          definition: {
            filters: { blobTypes: [ 'blockBlob' ], prefixMatch: [ 'store/' ] }
            actions: { version: { delete: { daysAfterCreationGreaterThan: 365 } } }
          }
        }
      ]
    }
  }
}

resource insights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${appName}-ai'
  location: location
  kind: 'web'
  properties: { Application_Type: 'web', RetentionInDays: 30 }
}

resource plan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: '${appName}-plan'
  location: location
  sku: { name: 'Y1', tier: 'Dynamic' }   // consumption: pay per execution, generous free grant
  kind: 'functionapp'
  properties: { reserved: true }          // Linux
}

resource vault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: '${appName}-kv-${take(suffix, 6)}'
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: { family: 'A', name: 'standard' }
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
  }
}

resource func 'Microsoft.Web/sites@2023-12-01' = {
  name: '${appName}-api-${take(suffix, 6)}'
  location: location
  kind: 'functionapp,linux'
  identity: { type: 'SystemAssigned' }
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'Node|20'
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      cors: { allowedOrigins: [ 'https://${swa.properties.defaultHostname}' ] }
      appSettings: [
        { name: 'AzureWebJobsStorage', value: 'DefaultEndpointsProtocol=https;AccountName=${storage.name};AccountKey=${storage.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}' }
        { name: 'FUNCTIONS_EXTENSION_VERSION', value: '~4' }
        { name: 'FUNCTIONS_WORKER_RUNTIME', value: 'node' }
        { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: insights.properties.ConnectionString }
        { name: 'STORE_ACCOUNT', value: storage.name }
        { name: 'STORE_CONTAINER', value: 'store' }
        { name: 'STORE_KEY', value: 'store/store.json' }
        { name: 'GOOGLE_CREDENTIALS_JSON', value: '@Microsoft.KeyVault(VaultName=${vault.name};SecretName=google-credentials)' }
        { name: 'BACKUP_FOLDER_ID', value: backupFolderId }
        { name: 'DENY_SHEET_IDS', value: denySheetIds }
        { name: 'ALLOW_SHEET_IDS', value: allowSheetIds }
        { name: 'BACKUP_TIME_ZONE', value: 'America/Edmonton' }
        { name: 'APP_URL', value: 'https://${swa.properties.defaultHostname}/' }
      ]
    }
  }
}

// Function identity: read/write the store blobs, read the Google secret
resource blobRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, func.id, 'blob-contrib')
  scope: storage
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe') // Storage Blob Data Contributor
    principalId: func.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource kvRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(vault.id, func.id, 'kv-secrets-user')
  scope: vault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6') // Key Vault Secrets User
    principalId: func.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource kvAdminRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(vault.id, adminObjectId, 'kv-secrets-officer')
  scope: vault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7') // Key Vault Secrets Officer
    principalId: adminObjectId
  }
}

resource swa 'Microsoft.Web/staticSites@2023-12-01' = {
  name: '${appName}-web'
  location: swaLocation
  sku: { name: 'Free', tier: 'Free' }
  properties: {}
}

output webUrl string = 'https://${swa.properties.defaultHostname}/'
output apiUrl string = 'https://${func.properties.defaultHostName}/api'
output functionAppName string = func.name
output keyVaultName string = vault.name
output storageAccountName string = storage.name

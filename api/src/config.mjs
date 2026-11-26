// Runtime configuration, all from environment variables (set by infra/aws/template.yaml).
const list = (s) => String(s || '').split(/[\s,]+/).map((x) => x.trim()).filter(Boolean);

export function loadConfig(env = process.env) {
  return {
    dataBucket: env.DATA_BUCKET || '',
    storeKey: env.STORE_KEY || 'store/store.json',
    siteBucket: env.SITE_BUCKET || '',
    appKey: env.APP_KEY || 'index.html',
    googleParam: env.GOOGLE_CREDENTIALS_PARAM || '',          // SSM SecureString holding the Google credentials JSON
    googleImpersonate: env.GOOGLE_IMPERSONATE || '',           // optional: domain-wide delegation subject
    backupFolderId: env.BACKUP_FOLDER_ID || '',                // Drive folder that holds the per-budget backup sheets
    allowSheetIds: new Set(list(env.ALLOW_SHEET_IDS)),         // extra sheets that may be written (backup sheets outside the folder)
    denySheetIds: new Set(list(env.DENY_SHEET_IDS)),           // never written, whatever else says (invoice sheet, retired master sheet)
    writersGroup: env.WRITERS_GROUP || '',                     // optional Cognito group required to save / write sheets
    maxStoreBytes: +env.MAX_STORE_BYTES || 5 * 1024 * 1024,
    timeZone: env.BACKUP_TIME_ZONE || 'America/Edmonton',
  };
}

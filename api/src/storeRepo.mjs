// Where the team's store JSON lives, with optimistic concurrency.
// S3 (production): one object, versioned bucket. version = ETag. PUT uses If-Match (or If-None-Match:* for the first save),
// so two people saving from the same base can never overwrite each other: the second gets a conflict.
// Memory / file repos implement the same interface for unit tests and the local dev server.
import crypto from 'node:crypto';
import fs from 'node:fs';

export class ConflictError extends Error {
  constructor(msg = 'conflict') { super(msg); this.code = 'conflict'; }
}
const etagOf = (body) => '"' + crypto.createHash('md5').update(body).digest('hex') + '"';

export class MemoryRepo {
  constructor(initial = null) { this.versions = []; if (initial) this._write(JSON.stringify(initial), {}); }
  _write(body, meta) { const v = { body, version: etagOf(body) + ':' + this.versions.length, at: new Date().toISOString(), meta }; this.versions.push(v); return v; }
  async get(versionId) {
    const v = versionId ? this.versions.find((x) => x.version === versionId) : this.versions[this.versions.length - 1];
    return v ? { store: JSON.parse(v.body), version: v.version } : null;
  }
  async put(store, baseVersion, meta = {}) {
    const cur = this.versions[this.versions.length - 1];
    if ((cur ? cur.version : null) !== (baseVersion || null)) throw new ConflictError();
    return { version: this._write(JSON.stringify(store), meta).version };
  }
  async history(limit = 50) {
    return this.versions.slice().reverse().slice(0, limit).map((v) => ({ versionId: v.version, at: v.at, size: v.body.length, savedBy: v.meta.savedBy || '' }));
  }
}

// File-backed repo for the local dev server: data/store.json + data/history/*.json
export class FileRepo extends MemoryRepo {
  constructor(file) {
    super(null); this.file = file;
    if (fs.existsSync(file)) this.versions.push({ body: fs.readFileSync(file, 'utf8'), version: etagOf(fs.readFileSync(file)) + ':0', at: new Date().toISOString(), meta: {} });
  }
  async put(store, baseVersion, meta) { const r = await super.put(store, baseVersion, meta); fs.writeFileSync(this.file, JSON.stringify(store)); return r; }
}

export class S3Repo {
  constructor({ bucket, key, client }) { this.bucket = bucket; this.key = key; this.client = client; }
  async s3() {
    if (!this.client) {
      const m = await import('@aws-sdk/client-s3'); // provided by the Lambda Node.js runtime
      this.client = new m.S3Client({}); this.m = m;
    } else if (!this.m) this.m = await import('@aws-sdk/client-s3');
    return this.client;
  }
  async get(versionId) {
    const c = await this.s3();
    try {
      const r = await c.send(new this.m.GetObjectCommand({ Bucket: this.bucket, Key: this.key, ...(versionId ? { VersionId: versionId } : {}) }));
      const body = await r.Body.transformToString();
      return { store: JSON.parse(body), version: r.ETag };
    } catch (e) {
      if (e && (e.name === 'NoSuchKey' || e.$metadata?.httpStatusCode === 404)) return null;
      throw e;
    }
  }
  async put(store, baseVersion, meta = {}) {
    const c = await this.s3();
    const body = JSON.stringify(store);
    try {
      const r = await c.send(new this.m.PutObjectCommand({
        Bucket: this.bucket, Key: this.key, Body: body, ContentType: 'application/json',
        Metadata: { 'saved-by': String(meta.savedBy || '').slice(0, 200), 'saved-at': String(store.savedAt || '') },
        ...(baseVersion ? { IfMatch: baseVersion } : { IfNoneMatch: '*' }),
      }));
      return { version: r.ETag };
    } catch (e) {
      const s = e && e.$metadata && e.$metadata.httpStatusCode;
      if (s === 412 || s === 409 || e.name === 'PreconditionFailed' || e.name === 'ConditionalRequestConflict') throw new ConflictError();
      throw e;
    }
  }
  async history(limit = 50) {
    const c = await this.s3();
    const r = await c.send(new this.m.ListObjectVersionsCommand({ Bucket: this.bucket, Prefix: this.key, MaxKeys: limit }));
    return (r.Versions || []).filter((v) => v.Key === this.key).map((v) => ({ versionId: v.VersionId, at: v.LastModified, size: v.Size, latest: !!v.IsLatest }));
  }
}

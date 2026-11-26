#!/usr/bin/env python3
"""Helpers for the single-file app (stdlib only).

  extract  <app.html>                       print the embedded store JSON
  inject   <app.html> <store.json> <out>    put a store JSON into the app (same escaping as the app's own save)
  privatize <app.html> <private.json> <out> replace the public placeholders with the team's real ids
  publicize <app.html> <private.json> <out> the reverse: real ids -> placeholders (run before committing)
  check    <file>...                        fail if a file contains a value from config/private.json (needs it)

private.json (NEVER commit; see config/private.example.json):
  {"BACKUP_FOLDER_ID": "...", "INVOICE_SHEET_ID": "...", "MASTER_SHEET_ID": "...", "NAME_HINT": "...", "NOTE_HINT": "..."}
"""
import json, re, sys

STORE_RE = re.compile(r'(<script id="store" type="application/json">)([\s\S]*?)(</script>)')
# placeholder -> (key in private.json, literal used in the app code)
PLACEHOLDERS = {
    'YOUR_BACKUP_FOLDER_ID': 'BACKUP_FOLDER_ID',
    'YOUR_INVOICE_SHEET_ID': 'INVOICE_SHEET_ID',
    'YOUR_RETIRED_MASTER_SHEET_ID': 'MASTER_SHEET_ID',
}
NAME_HINT_PUBLIC = 'placeholder="e.g. Alex"'
NOTE_HINT_PUBLIC = 'e.g. Checked with Jordan,'


def read(p):
    return open(p, encoding='utf-8').read()


def write(p, s):
    open(p, 'w', encoding='utf-8').write(s)


def extract(html):
    m = STORE_RE.search(html)
    if not m:
        sys.exit('no <script id="store"> in this file')
    return m.group(2)


def _jsnum(o):
    # JSON.stringify writes 100 for 100.0: keep byte-identical output with the app's own save
    if isinstance(o, float) and o.is_integer() and abs(o) < 1e15:
        return int(o)
    if isinstance(o, list):
        return [_jsnum(x) for x in o]
    if isinstance(o, dict):
        return {k: _jsnum(v) for k, v in o.items()}
    return o


def inject(html, store_json):
    data = _jsnum(json.loads(store_json))
    js = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    m = STORE_RE.search(html)
    return html[:m.start(2)] + js + html[m.end(2):]


def privatize(html, priv):
    for ph, key in PLACEHOLDERS.items():
        if priv.get(key):
            html = html.replace(ph, priv[key])
    if priv.get('NAME_HINT'):
        html = html.replace(NAME_HINT_PUBLIC, 'placeholder="e.g. %s"' % priv['NAME_HINT'])
    if priv.get('NOTE_HINT'):
        html = html.replace(NOTE_HINT_PUBLIC, 'e.g. Checked with %s,' % priv['NOTE_HINT'])
    return html


def publicize(html, priv):
    for ph, key in PLACEHOLDERS.items():
        if priv.get(key):
            html = html.replace(priv[key], ph)
    if priv.get('NAME_HINT'):
        html = html.replace('placeholder="e.g. %s"' % priv['NAME_HINT'], NAME_HINT_PUBLIC)
    if priv.get('NOTE_HINT'):
        html = html.replace('e.g. Checked with %s,' % priv['NOTE_HINT'], NOTE_HINT_PUBLIC)
    return html


def main(a):
    if len(a) < 2:
        sys.exit(__doc__)
    cmd = a[0]
    if cmd == 'extract':
        sys.stdout.write(extract(read(a[1])))
    elif cmd == 'inject':
        write(a[3], inject(read(a[1]), read(a[2])))
    elif cmd in ('privatize', 'publicize'):
        priv = json.loads(read(a[2]))
        write(a[3], (privatize if cmd == 'privatize' else publicize)(read(a[1]), priv))
    elif cmd == 'check':
        priv = json.loads(read('config/private.json'))
        bad = 0
        for f in a[1:]:
            s = read(f)
            for k, v in priv.items():
                if v and len(v) > 8 and v in s:
                    print('LEAK', f, k)
                    bad = 1
        sys.exit(bad)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main(sys.argv[1:])

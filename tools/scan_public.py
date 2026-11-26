#!/usr/bin/env python3
"""Fails if the repo (tracked + new files) contains things that must never be public:
   - Google file ids (33/44-character Drive/Sheets ids) other than the allowed placeholders
   - private keys, AWS access keys, Google API keys
   - any value of config/private.json (when that gitignored file exists locally)"""
import json, os, re, subprocess, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
files = subprocess.check_output(['git', 'ls-files', '-co', '--exclude-standard'], cwd=root, text=True).split()
PATTERNS = {
    'google-id': re.compile(r'(?<![A-Za-z0-9_-])1[A-Za-z0-9_-]{32}(?:[A-Za-z0-9_-]{11})?(?![A-Za-z0-9_-])'),
    'private-key': re.compile(r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----'),
    'aws-key': re.compile(r'(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])'),
    'google-api-key': re.compile(r'AIza[0-9A-Za-z_-]{35}'),
}
priv = {}
p = os.path.join(root, 'config', 'private.json')
if os.path.exists(p):
    priv = {k: v for k, v in json.load(open(p)).items() if isinstance(v, str) and len(v) >= 8}
bad = 0
for f in files:
    if f.startswith('config/private') or not os.path.isfile(os.path.join(root, f)):
        continue
    try:
        s = open(os.path.join(root, f), encoding='utf-8').read()
    except Exception:
        continue
    for name, rx in PATTERNS.items():
        for m in rx.finditer(s):
            tok = m.group(0)
            if name == 'google-id' and (not re.search(r'[A-Z]', tok) or not re.search(r'[a-z]', tok) or not re.search(r'\d.*\d', tok)):
                continue  # words / long lowercase identifiers, not ids
            print(f'{f}: {name}: {tok[:12]}…'); bad = 1
    for k, v in priv.items():
        if v in s:
            print(f'{f}: contains private value {k}'); bad = 1
print('scan: clean' if not bad else 'scan: FOUND PROBLEMS')
sys.exit(bad)

#!/usr/bin/env python3
"""Runs the Playwright suites and fails if any check fails.
   python3 tests/run_all.py                 every suite (regression + features + standalone smoke)
   python3 tests/run_all.py regression      the original regression set (run.sh)
   python3 tests/run_all.py features        feature suites (all.sh)
   APP_HTML=/path/to/app.html python3 tests/run_all.py    test another copy of the app (e.g. a new artifact export)
Each suite prints PASS/FAIL lines and ends with "N / M" (or "errors []" / "BAD []" for the audit / layout sweeps)."""
import os, re, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
REGRESSION = ['bk_test', 'sync_test', 'inv_test', 'modal_test', 'cp_test', 'bc_test', 'save_test', 'audit', 'report_test_src']
FEATURES = ['tc_test', 'reopen_test', 'noreload_test', 'move_test', 'up_test', 'up_sheet_test', 'lay_test']
SMOKE = ['standalone_smoke']
sel = sys.argv[1] if len(sys.argv) > 1 else 'all'
suites = {'regression': REGRESSION, 'features': FEATURES, 'smoke': SMOKE}.get(sel, REGRESSION + FEATURES + SMOKE)
failed = []
for s in suites:
    t0 = time.time()
    p = subprocess.run([sys.executable, os.path.join(HERE, s + '.py')], capture_output=True, text=True, timeout=1200)
    out = p.stdout + p.stderr
    fails = [l for l in out.splitlines() if l.startswith('FAIL')]
    counts = re.findall(r'(\d+) ?/ ?(\d+)\s*$', out, re.M)
    ok = p.returncode == 0 and not fails and 'Traceback' not in out
    if counts:
        a, b = counts[-1]; ok = ok and a == b
    if s == 'audit': ok = ok and 'errors []' in out
    if s == 'lay_test': ok = ok and 'BAD []' in out
    if s == 'noreload_test': ok = ok and out.count('[True,') == 2 and ' closed True None' in out
    summary = (counts[-1][0] + '/' + counts[-1][1]) if counts else ''
    print(('ok   ' if ok else 'FAIL ') + s.ljust(18) + summary.ljust(10) + '%5.0fs' % (time.time() - t0), flush=True)
    if not ok:
        failed.append(s)
        print('\n'.join(('    ' + l) for l in (fails or out.strip().splitlines()[-15:])))
print('\nALL PASSED' if not failed else '\nFAILED: ' + ', '.join(failed))
sys.exit(1 if failed else 0)

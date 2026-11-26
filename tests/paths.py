# Shared paths for the Playwright suites (repo-relative; override with env vars).
#   APP_HTML   the single-file app under test (default: app/artifact/index.html with the sample store)
#   TEST_OUT   where screenshots / PDFs / harness pages go (default: tests/out, gitignored)
import os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
APP = os.path.abspath(os.environ.get('APP_HTML', os.path.join(ROOT, 'app', 'artifact', 'index.html')))
APP_URL = 'file://' + APP
OUT = os.path.abspath(os.environ.get('TEST_OUT', os.path.join(HERE, 'out')))
os.makedirs(OUT, exist_ok=True)
# window.claude mock (artifact.publish / downloads / mcp Google Sheets + Drive in memory); see tests/mock_init.js
INIT = open(os.path.join(HERE, 'mock_init.js')).read()
# the sample store's budget backup sheet id
K = os.environ.get('TEST_SHEET_ID', 'SAMPLE-BACKUP-SHEET-ID')

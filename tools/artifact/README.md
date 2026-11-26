# Artifact publishing helpers

The live app is a Claude artifact. These are the helpers used to publish code changes to it.

* `mkedits2.py old.html new.html` — turns the difference between two versions of the page (ignoring the embedded store)
  into a minimal list of `{old_text, new_text}` edits with unique anchors (written to `/tmp/edits.json`) for the
  artifact `edit_version` tool. Rules from experience: strip a `</head><body>\n<header class="top` suffix from style edits
  (anchor at `</style>`); the live HTML normalizes boolean attributes (`hidden` → `hidden=""`), so never anchor across a
  bare `hidden>`; on a 409 conflict re-read the live version and retry; edit sets > 40 KB are published by a delegated agent.
* `mkedits.py` — older variant.
* `plan2.js page.html "Source" '<existing tabs json>' main|<budgetId>|list '<files json>'` — runs the page's own
  `calc` + `buildSheets` (cut out by the `/*ENGINE*/`, `/*BACKUP*/`, `/*SHEETS*/` markers) and prints the backup plan
  (used by the daily backup task; see docs/daily-backup-task.md). `plan.js` — older variant.
* After publishing, re-export the repo copy: `python3 tools/store_tool.py publicize <live.html> config/private.json /tmp/p.html`
  then `python3 tools/store_tool.py inject /tmp/p.html samples/store.sample.json app/artifact/index.html` and
  `node app/build/build_standalone.mjs` (or just `make export LIVE=<live.html>`).

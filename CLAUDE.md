# CLAUDE.md

All standing rules for agents are in **[AGENTS.md](AGENTS.md)** — read it first. The essentials:

- Checkboxes: only the box is clickable. Every UI change: 375/390/768/1300, light + dark, no truncated money, no
  horizontal scroll, ≥ 44 px taps. Same Save / Discard / Go back popup wherever unsaved state can be lost.
- Google Sheets: originals are READ-ONLY; only the calculator's own per-budget backup sheets may be written. Never the
  invoice sheet or the retired master sheet. Only the six data tabs may be deleted; To check gets K:L only.
- Don't change calculations / data / saving / Sheets logic unless the story requires it; data changes additive only.
  Keep the `/*ENGINE*/ /*BACKUP*/ /*SHEETS*/` markers intact.
- Public repo: no real store data, no real Google ids, no secrets (`make scan`).
- Done = `python3 tests/run_all.py` ALL PASSED + `cd api && npm test` + `make lint`.
- Spec for every section: `docs/logic/`. Rebuild guide: `docs/rebuild-runbook.md`.

# Build history helpers (reference only)

Scripts the coordinator / agents used while building the live artifact (Nov 2026), kept so the history of each edit is
understandable. They point at old scratch paths (`/home/claude/...`) and old page copies and are **not** part of the
build; real vendor/tab names were replaced. Current tooling: `tools/store_tool.py`, `tools/artifact/`, `app/build/`.

| file | what it did |
|---|---|
| s1_invdata.py, s2_invui.py | imported invoices/payments from the invoice sheet tabs into the budget; invoice UI |
| s3_types.py | Manage item types |
| s4_backup.py, s5_sheets.py, s6_write.py, sheets_*.js, book_js.js | Google Sheets backup builder iterations |
| s7_cards.py, s8_modals.py | mobile cards, modal behaviour |
| s9_safety.py | safe swap, restore points, unsaved-changes safety |
| s10_cp.py | Cash + Private financing option |
| s11_side.py | Inputs sidebar order |
| s12_bc.py | budget → build cost sources (Projected / estimate / invoiced / manual, contingency) |
| render_pay.js | invoices & payments window renderer draft |
| sync_js.js | "bring changes back from the sheet" draft |

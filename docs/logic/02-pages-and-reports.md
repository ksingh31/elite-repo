# 2. Pages: Inputs, Builder + investor, Investor report, Builder report (+ PDF)

Navigation is hash based: `#inputs` (default), `#builder`, `#investors`, `#breport`, `#budget`, `#tocheck`
(`VIEWS`, `route()`). Leaving a page with unsaved changes asks first (see [06-save-drafts-undo.md](06-save-drafts-undo.md)).
The top bar shows `#projbar` (project picker, Rename project, New/Duplicate/Delete project, save state, Save for team)
on project pages and `#budbar` (budget picker etc.) on Budget / To check.

`refresh()` is the single recompute: saves the device view (`ec-view`), computes `RL/RH/R` (ranges, see 1.6), then
`fillBar(); renderLive(); renderMini(); renderBuilder(); renderInvestor(); renderBuilderReport(); refreshForm();`
and marks range tiles (`.rg`). Every input fires `input` → `set(path, value)` → `persist()` → `refresh()` → `markField()`.

## 2.1 Inputs (`#v-inputs`, `buildForm()`)
Cards (in order):
1. **Project**: name, sell price (incl. GST), lot price, build cost (or the budget link panel, `buildField()`), lawyer fee,
   three month ranges (`FR()`: "Lot held before building", "Build time", "Months to close after built"; each a grouped
   *from … to* control, "to" optional). Project length line (`#c-len`).
2. **Who sells the house?** radio cards Honest Door / Outside realtors (with amounts), net sell price, GST in sell price,
   GST credits, net GST, checkbox "Build cost includes GST", property tax line, checkbox "Add tax on the finished home while
   it waits to close", overhead line; details "Enter overhead or property tax by hand" (`ohOv`, `taxOv`, blank = calculated).
3. **Financing**: option cards (`#usebox`: A Lender, A Lender + Private, Private, Cash + Private, All cash) then the
   fields of the selected option only (others keep their settings):
   * A Lender: % of lot financed, rate, months until paid off, short private loans.
   * A Lender + Private: lot mortgage (% of lot, rate, months until the draw loan starts), draw schedule (`sched.before`
     "Draw loan starts N months before finish", draw % rows with *when* labels, add/remove draw, total warning),
     draw mortgage (% of lot + build, fixed fees, interest on drawn amount, fee line), short private loans.
   * Private: % financed, fees, rate, extra in first draw, later draws at completion points (% built), plan table
     (Draw / Amount / Taken at / Interest for / Interest), fee line, short loans.
   * Cash + Private (`cpBlock`): approval base (Lot + build / Build only), % approved, fee, rate, draws as % or fixed $
     (seg control), rows "Months after build starts / Amount", over-approval and late-draw warnings, draw table, short loans.
   * All cash: note only.
4. **Extra costs** rows (Cost / Amount / Paid up front %), **Investors** rows (Name / Cash invested) with the
   "investor cash is more than this project needs" warning.
5. **Rates and overhead for this project** (details): Make default for new projects / Reset to company defaults;
   overhead Calculate vs Flat; realtor tier and rates, Honest Door fee; GST, property tax, lawyer up-front share.
6. **How it is calculated** (details): the plain-language formulas (mirrors [01-calc-engine.md](01-calc-engine.md)).

Field types (`F(label, path, t)`): `t` text, `m` money (commas shown), `p` percent (stored /100), `n` number, `o` optional
money (blank = null). Inline check `fieldIssue()` never blocks typing; it says how the value will be read.
Removing a row: `×` button `data-act="rm"`; adding: `data-act="add"` with `blank` templates
(`extras {label:'',amount:0,up:1}`, `investors {name:'',amount:0}`, `loans {label:'Private loan',amount:0,fee:0,rate:0.1,months:6}`, `cpd {at:0,v:0}`).

**Sidebar** (`#live`, `renderLive`): TOP box = builder profit for the selected option (profit after financing, the
financing deductions: lender fee, lot mortgage interest, draw interest, short loans, with their rate/base notes; builder
earnings and return). BOTTOM separate box = investor-level "Profit before financing" (project cost, investor return,
annualized). On phones a sticky mini summary (`#mlive`, `renderMini`) shows Profit · option, tap = scroll to the sidebar.

## 2.2 Builder + investor (`#v-builder`, `renderBuilder`)
Tiles: Net sell price (before GST), Profit before financing, Profit after financing, Builder earnings.
Sections: Project profit before financing (cost lines with Paid up front), Financing comparison table (all five options as
columns; rows: Draw loan amount, Lot mortgage, Fixed fees, Lot mortgage interest, Draw loan interest, Short private loans,
**Total financing cost**, Total spent, **Profit**, Peak cash before first draw, Cash needed after loan, **ROI on cash needed**,
ROI on peak cash, **Annualized ROI on cash needed**, Annualized ROI on peak cash, Interest per extra month) with profit
bars, the selected option's draw schedule, Settlement on the selected option (Party / Cash in / Earnings / Payout / Return /
Annualized for each investor and the company: investors earn `rate0`, company gets `coNet`).

## 2.3 Investor report (`#v-investors`, `renderInvestor`)
Report header "ELITECRAFT / REAL ESTATE · Investor return report · <project> | Returns on project profit only, no
financing costs". Picker All investors / one investor, Copy summary (clipboard text), PDF button. Tiles: Cash invested,
Net earnings, investor return (annualized), etc. Table per investor (Share, Cash in, Return, Earnings, Payout).

## 2.4 Builder report (`#v-breport`, `renderBuilderReport`)
Same report frame. Lead sentence and facts depend on the selected option (`k`): e.g. A Lender = "A mortgage on the lot
only… Interest runs for N mo" with facts Lot price, Lot mortgage (% of lot), Interest rate, Term, Interest per extra month.
Sections: Project profit before financing, **Financing: <option>** (facts, draw table `dtab` for ap/priv/cp, fee and
interest lines, short loans text), **Financing cost** total, **Builder cash and returns** (tiles: Profit after financing,
Builder cash in, Builder earnings, Return on builder cash, Annualized return), Builder breakdown. Negative numbers get
`.neg` (red). Ranges print as low – high.

## 2.5 PDF generator (no library)
`savePdf(k)` (k = `builder` | `investor`) → `pdfBytes(k)` → `repModel(section)` → `pdfFrom(model, footer)` → `downloads.save({filename, data})`.
* `repModel` reads the **on-screen report DOM**: header (brand, title, sub lines), then each child of `.rep` as a block:
  `tiles` (label, value, negative flag), `h2`/`h3`, `table` (head cells, rows with cells {text without `<small>`, small
  note, colspan, neg}, total rows), notes/paragraphs. So the PDF always matches the screen.
* `pdfFrom` writes a PDF 1.4 by hand: US Letter 612×792 pt, margin 40, Helvetica / Helvetica-Bold (standard 14 fonts,
  WinAnsi encoding; `HW/HB` AFM width tables for text measuring, `winA()` maps Unicode to WinAnsi, unknown chars dropped),
  colours NAVY `#14263d`, TEAL `#0d7a75`, INK, MUTE, LINE, ALT row `#f4f7f9`, tile bg `#e2f0ef`, RED `#b42318`; navy header
  band, tiles grid, zebra tables with right-aligned numbers, word wrap (`pdfWrap`), automatic page breaks with repeated
  table heads, footer "<project> · page n of N".
* File name: `<project name sanitized> - Builder report.pdf` / `- Investor report.pdf`. Buttons are disabled with a
  tooltip when `downloads` is unavailable. `tests/report_test_src.py` checks text extraction of the generated PDFs.

## 2.6 Projects
`New project` (copies company defaults into `co`), Duplicate, Delete (typed confirmation), Rename (inline input,
Enter/Escape/blur), "Make these the default for new projects" (`setdef`), "Reset to company defaults" (`resetco`).
Project picker `#proj` (switching asks to save/discard when dirty).

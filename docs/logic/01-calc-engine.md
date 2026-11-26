# 1. Calculation engine (`calc(p, co)`)

Source: `app/artifact/index.html`, between the markers `/*ENGINE*/` and `/*END*/` (one pure function, no DOM).
The same text is loaded by the server-side daily backup (`api/src/engine.mjs`) and by the Claude daily task,
so **never remove the markers** and keep `calc` free of outside references.

Inputs: `p` = an *effective* project (`effP(P())`: the project with `build` replaced by the linked budget total when a
budget is linked, see [03-budget.md](03-budget.md)), `co` = the project's rates (`p.co`). All rates are fractions.
Helpers: `sum`, `isNum(v)` = not null/''/undefined and not NaN.

## 1.1 Sale side, GST, realtor

| Name | Formula |
|---|---|
| `g` | `co.gstRate` |
| `netSell` | `p.sell / (1+g)` (sell price includes GST) |
| `gstIn` | `p.sell − netSell` |
| `buildGst` | `p.buildGst !== false` |
| `buildNet` | `buildGst ? p.build/(1+g) : p.build` |
| `gstCredit` | `buildGst ? p.build − buildNet : p.build*g` |
| `gstNet` | `gstIn − gstCredit` (net GST sent to CRA at closing; display only) |
| `side` | `co.tier*co.firstRate + max(0, netSell − co.tier)*co.restRate` (commission per side, on the net sell price) |
| `realtorBoth` | `2*side*(1+g)` |
| `realtorHD` | `(co.hdFlat + side)*(1+g)` (Honest Door flat fee + buyer's agent side) |
| `realtor` | `p.sale==='hd' ? realtorHD : realtorBoth` |

## 1.2 Tax, overhead, costs

* `taxAuto = p.lot*co.taxRate + (p.taxWait ? netSell*co.taxRate*p.close/12 : 0)`; `tax = isNum(p.taxOv) ? +p.taxOv : taxAuto`
* `ohCalc = co.projects ? (co.salary*(1+co.raise) + co.office + co.misc)/co.projects : 0`
* `ohCo = co.ohMode==='flat' ? (+co.ohFlat||0) : ohCalc`; `overhead = isNum(p.ohOv) ? +p.ohOv : ohCo`
* `costs` (label, value `v`, up-front share `up`, `lb` = part of lot+build):

| label | v | up | lb |
|---|---|---|---|
| Lot price | `p.lot` | 1 | yes |
| Build cost (before GST) / Build cost | `buildNet` | 1 | yes |
| Lawyer fee | `p.lawyer` | `co.lawyerUp` | |
| Overhead | `overhead` | 1 | |
| Realtor (Honest Door, incl. GST) / Realtor, both sides (incl. GST) | `realtor` | 0 | |
| Property tax | `tax` | 1 | |
| each extra cost | `+e.amount` | `+e.up` | |

* `base = Σ costs.v` (project cost), `profit0 = netSell − base` (profit before financing), `rate0 = base ? profit0/base : 0` (investor return)
* `upOther = Σ (v*up)` over costs that are **not** lot/build (cash paid up front besides lot and build)

## 1.3 Timing and annualizing

* `pre = +p.preBuild||0`, `bm = +p.buildMonths||0`, `close = +p.close||0`
* `D = pre + bm + close` (project months, lot purchase → sale closing)
* `ann(r) = (r==null || D<=0 || r<=−1) ? null : (1+r)^(12/D) − 1`
* `annInv = ann(rate0)`

## 1.4 Financing options (all five are always computed; `p.use` picks the selected one)

Common builder `mk(key, name, loan, fee, lotInt, drawInt, loans, perMonth, draw, lotAmt)`:

```
interest = lotInt + drawInt
other    = Σ loans: amount*(rate*months/12 + fee)       // short private loans
fin      = fee + interest + other                       // total financing cost
spent    = base + fin
profit   = netSell − spent
cash     = base − loan + fin                            // cash needed after loan
peak     = draw ? max(cash, prePeak − lotAmt + lotInt) : cash
roi      = cash>0 ? profit/cash : 0;      roiPeak = peak>0 ? profit/peak : 0
annRoi   = ann(roi);                      annPeak = ann(roiPeak)
```
with `prePeak = p.lot + buildNet*done + upOther`, `done = bm>0 ? clamp((bm − sched.before)/bm, 0, 1) : 0`
(share of the build paid in cash before the A Lender + Private draw loan starts).

| key | name | loan | fee | lotInt | drawInt | loans | perMonth | draw |
|---|---|---|---|---|---|---|---|---|
| `lot` | A Lender | `lotLoan = L.ltv*p.lot` | 0 | `lotLoan*L.rate*L.months/12` | 0 | `lotLoan.loans` | `lotLoan*L.rate/12` | 0 |
| `ap` | A Lender + Private | `apLoan = ap.ltv*(lot+build)` | `apLoan*ap.fee` | `lotLoan*L.rate*ap.lotMonths/12` | `apLoan*ap.rate*yrs` | `ap.loans` | `apLoan*ap.rate/12` | 1 (lotAmt = lotLoan) |
| `priv` | Private | `pvLoan = priv.ltv*(lot+build)` | `pvLoan*priv.fee` | 0 | `pvInt` | `priv.loans` | `pvLoan*priv.rate/12` | 0 |
| `cp` | Cash + Private | `cpDrawn` | `cpFee` | 0 | `cpInt` | `cp.loans` | `cpDrawn*cp.rate/12` | 0 (peak overridden) |
| `cash` | All cash | 0 | 0 | 0 | 0 | none | 0 | 0 |

Note: `build` in `lot+build` is the typed/linked build **including** GST (not `buildNet`).

### A Lender + Private draws (`sched`)
`before = max(0, sched.before)`, `T = before + p.close`, `N = draws.length`. Draw k is taken at
`at_k = N>1 ? k*before/(N−1) : 0` months after the loan starts and is outstanding `out_k = max(0, T − at_k)` months.
`yrs = Σ share_k*out_k/12` (shares are fractions, warned when they don't add to 100 %). `drawInt = apLoan*ap.rate*yrs`.

### Private draws
```
pEnd   = pre + bm + close;  pDown = (lot+build) − pvLoan        // you pay pDown at purchase
pFirst = min(pvLoan, max(0, lot − pDown) + priv.first)          // draw 1 at purchase
pMs    = priv.ms (default [0.3,0.6,1]) clamped to 0..1
pEach  = max(0, pvLoan − pFirst)/pMs.length
draws  = [{At lot purchase, pFirst, at 0}, ...pMs.map(f => {At f% built, pEach, at pre + f*bm})]
each:  out = max(0, pEnd − at), int = amt*priv.rate*out/12;   pvInt = Σ int
```

### Cash + Private (`cp`)
```
cpBase = cp.base==='build' ? build : lot+build;  cpA = max(0, cp.ltv*cpBase)  // approved
left = cpA; for each draw i: want = max(0, mode==='amt' ? v : v*cpA); amt = min(want, left); left −= amt
        after = max(0, at); at' = pre + after; out = max(0, pEnd − at'); int = amt*cp.rate*out/12
        late = at' >= pEnd && amt > 0          // drawn after the sale closes: warned
cpDrawn = Σ amt; cpInt = Σ int; cpFee = cpA*cp.fee (fee on the approval, interest only on what is drawn)
cp = {approved, base, drawn, undrawn = max(0, cpA − drawn), over = max(0, Σwant − cpA), fee, int}
peak points: spendAt(t) = lot + upOther + buildNet*(bm>0 ? clamp((t−pre)/bm,0,1) : 1)
             for each draw (in order): point = spendAt(at') + (drawnBefore>0 ? cpFee : 0) − drawnBefore
opt.cp.peak = max(cash, ...points); roiPeak / annPeak recomputed from it
```

### Short private loans
Any option's `loans[]`: cost = `amount*(rate*months/12 + fee)`; added to `fin` as `other`.
Default new row: `{label:'Private loan', amount:0, fee:0, rate:0.1, months:6}`.

## 1.5 Investors and company split
```
inv[i]  = {name, cash: +amount, earn: amount*rate0}        // investors earn the project return on their cash, no financing
invCash = Σ cash, invEarn = Σ earn
sel     = opts.find(o => o.key===p.use) || opts[0]
coCash  = sel.cash − invCash                                // company cash
coNet   = profit0 − invEarn − sel.fin                       // company (builder) earnings
coRoi   = coCash>0 ? coNet/coCash : null;  coAnn = coCash>0 ? ann(coRoi) : null
```
Warnings: investor cash more than the option needs (`coCash < 0`).

## 1.6 Ranges (low – high)
Any timing field can have a "to" value (`preBuildMax`, `buildMonthsMax`, `closeMax`). `refresh()` runs the engine twice:
`RL = calc(effP, co)` and `RH = calc(hiP(effP), co)` where `hiP` swaps in the Max values (`pickMax(mx, mn)` = mx when a
number else mn). `R = mergeR(RL, RH)` walks both results; every number pair becomes `mkR(a,b)`: equal (|a−b|<1e-9) → a
number, else an `Rg{lo,hi}` object. Formatters (`m`, `m0`, `pc`, `mo`, `rnum`) print `Rg` as "low – high" (sorted), and
`add/neg/lo/hi` do arithmetic on ranges. `R.sel` = the merged option with `RL.sel.key`.

## 1.7 Return values used by the UI
`side, realtorBoth, realtorHD, realtor, netSell, gstIn, gstCredit, gstNet, buildNet, buildGst, tax, taxAuto, ohCalc, ohCo,
overhead, costs, base, profit0, rate0, upOther, T, buildM, bm, done, loanAt, prePeak, draws, drawTotal, pdraws, pDown, pEnd,
cpdraws, cp, opts, inv, invCash, invEarn, sel, coCash, coNet, coRoi, coAnn, D, annInv`.

## 1.8 Worked check (from the tests)
`tests/cp_test.py` asserts: drawn = 100 % by default; draw interest = Σ amt*0.0702*max(0, pEnd − (pre+after))/12; fixed-$
draws capped at what is left; a short loan of 100,000 at 10 % for 6 months with 2 % fee costs 2,000 + 5,000.
`tests/report_test_src.py` recomputes every Builder report figure for each option against `calc()`.

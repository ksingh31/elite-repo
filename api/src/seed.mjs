// Store returned when the data bucket has no store yet (first deploy without an initial upload).
// Same shape the app's migrate() expects: one blank project, no budgets. The app fills the catalog on load.
const co = { ohMode: 'flat', ohFlat: 45000, salary: 70000, raise: 0.035, office: 10000, misc: 6000, projects: 1.5, gstRate: 0.05, taxRate: 0.0068, lawyerUp: 0.5, tier: 100000, firstRate: 0.035, restRate: 0.015, hdFlat: 750 };
export const SEED_STORE = {
  v: 4, savedAt: null, cur: 'p1', company: co, curBudget: null, budgets: [],
  projects: [{
    id: 'p1', name: 'New project', sell: 0, lot: 0, build: 0, close: 0, lawyer: 0, buildGst: true, sale: 'hd', taxWait: false, taxOv: null,
    buildMonths: 10, sched: { before: 4, draws: [0.3333, 0.3333, 0.3334] }, use: 'lot',
    lotLoan: { ltv: 0.8, rate: 0.04, months: 18, loans: [] }, ap: { lotMonths: 6, ltv: 0.65, fee: 0.03, rate: 0.0702, loans: [] },
    priv: { ltv: 0.65, fee: 0.04, rate: 0.0902, loans: [], first: 200000, ms: [0.3, 0.6, 1] },
    extras: [], investors: [], ohOv: null, co: { ...co }, budget: { use: false, id: null, ver: 'latest' },
  }],
};

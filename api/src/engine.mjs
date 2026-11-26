// Loads the calculator's own engine and backup builders out of the app HTML, exactly like the Claude daily task's plan2.js:
//   calc()         between /*ENGINE*/ and /*END*/
//   buildBackup()  between /*BACKUP*/ and /*ENDBACKUP*/
//   buildSheets()  between /*SHEETS*/ and /*ENDSHEETS*/
// so any change to the app's calculations or sheet layout is picked up by the server-side daily backup automatically.
export function loadEngine(html) {
  const cut = (a, b) => {
    const i = html.indexOf(a), j = html.indexOf(b, i + a.length);
    if (i < 0 || j < 0) throw new Error('marker ' + a + ' / ' + b + ' not found in the app HTML');
    return html.slice(i + a.length, j);
  };
  const calc = new Function(cut('/*ENGINE*/', '/*END*/') + ';return calc;')();
  const buildSheets = new Function(cut('/*BACKUP*/', '/*ENDBACKUP*/') + cut('/*SHEETS*/', '/*ENDSHEETS*/') + ';return buildSheets;')();
  return { calc, buildSheets };
}

export function storeFromHtml(html) {
  const m = html.match(/<script id="store" type="application\/json">([\s\S]*?)<\/script>/);
  return m ? JSON.parse(m[1]) : null;
}

// "YYYY-MM-DD HH:MM" in the backup time zone (America/Edmonton), same format the app writes in Backup log column A
export function zonedNow(timeZone = 'America/Edmonton', d = new Date()) {
  const f = new Intl.DateTimeFormat('en-CA', { timeZone, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).formatToParts(d);
  const g = (t) => (f.find((x) => x.type === t) || {}).value;
  return g('year') + '-' + g('month') + '-' + g('day') + ' ' + g('hour') + ':' + g('minute');
}

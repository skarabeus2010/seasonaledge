/**
 * twin_probe.js — fuehrt die ECHTE landing/js/seasonal-compute.js aus und gibt
 * die Ergebnisse als JSON auf stdout aus.
 *
 * WARUM: verify_seasonal_twins.py bildete die JS-Logik frueher als Python-Nachbau
 * ab. Ein Nachbau kann aber selbst von der Quelle driften — dann zertifiziert der
 * Waechter eine Fiktion. Hier laeuft die Originaldatei; ein `window`-Stub genuegt,
 * weil das Modul nur `window.SA` setzt.
 *
 * Aufruf: node scripts/js/twin_probe.js <pfad-zu-seasonal-compute.js>
 */
const fs = require('fs');
const path = process.argv[2];
const src = fs.readFileSync(path, 'utf8');

// Minimaler Browser-Kontext. SA.i18n fehlt bewusst -> getMonthNames faellt auf DE.
const sandbox = { window: {} };
new Function('window', src + '\nreturn window.SA;')(sandbox.window);
const S = sandbox.window.SA.seasonal;

function rowsAusCloses(closes, startDatum) {
  // Baut [{date, close, log_return}] mit log_return = LN(close/prev) wie in der DB.
  const out = [];
  let d = new Date(startDatum + 'T00:00:00Z');
  for (let i = 0; i < closes.length; i++) {
    const prev = i === 0 ? null : closes[i - 1];
    out.push({
      date: d.toISOString().slice(0, 10),
      close: closes[i],
      log_return: prev === null ? null : Math.log(closes[i] / prev)
    });
    d = new Date(d.getTime() + 86400000);
  }
  return out;
}

const ergebnis = {};

// 1) Interpolation — direkt aufrufbar
ergebnis.interp = [
  { days: [364, 365, 366], values: [110, 115, 120] },
  { days: [363, 364, 365], values: [110, 115, 118] },
  { days: [1, 100, 200],   values: [100, 105, 108] },
  { days: [1, 200, 365],   values: [100, 110, 120] }
].map(c => ({ days: c.days, slot365: S._interpolateTo365(c.days, c.values)[364] }));

// 2) Turn-of-Month — echte Fensterbildung inkl. Monatsgruppierung/Sortierung.
//    Januar 2024 mit +5 % am ERSTEN Handelstag des Februars.
//    Ist die Gruppierung lexikografisch, zieht der Januar Oktober-Daten.
{
  const rows = [];
  const push = (datum, close) => rows.push({ date: datum, close: close, log_return: null });
  for (let t = 29; t <= 31; t++) push('2024-01-' + t, 100);   // Ende Januar
  push('2024-02-01', 105); push('2024-02-02', 105);            // Februar: +5 %
  for (let t = 1; t <= 3; t++) push('2024-03-0' + t, 105);
  for (let t = 1; t <= 3; t++) push('2024-10-0' + t, 50);      // Oktober: -50 %, Falle
  for (let t = 1; t <= 3; t++) push('2024-11-0' + t, 50);
  // log_return aus den Closes nachziehen
  for (let i = 1; i < rows.length; i++) rows[i].log_return = Math.log(rows[i].close / rows[i - 1].close);
  rows[0].log_return = 0;
  const r = S.analyzeTurnOfMonth(rows, 1, 1, [1], [2024]);
  ergebnis.tom_januar = r ? r.avg_curve : null;
}

// 3) buildYearData — Normalisierung + last_actual_day + Verwerfen-Semantik
{
  const mach = (closes, start) => {
    const rows = rowsAusCloses(closes, start);
    rows[0].log_return = Math.log(closes[0] / 100);  // Jahreswechsel-Return
    return rows;
  };
  const closes = [];
  for (let i = 0; i < 25; i++) closes.push(110 + i);
  const yd = S.buildYearData(mach(closes, '2024-01-02'));
  const jahr = Object.keys(yd)[0];
  ergebnis.build = jahr ? {
    jahr: jahr,
    erster: yd[jahr].full_365[0],
    last_actual_day: yd[jahr].last_actual_day
  } : null;

  // Unreparierbarer Close -> Jahr MUSS verworfen werden (kein stilles lr = 0)
  const kaputt = mach(closes.slice(), '2024-01-02');
  kaputt[5].close = 0; kaputt[5].log_return = null;
  kaputt[6].log_return = null;
  ergebnis.build_kaputt_jahre = Object.keys(S.buildYearData(kaputt)).length;
}

// 4) Mondphasen — dieselbe Fenster-Mathematik wie ToM, eigene Funktion.
//    In PR #271 wurde hier derselbe Off-by-one behoben; ohne Test bliebe eine
//    erneute Verschiebung gruen.
{
  const rows = [
    { date: '2024-03-10', close: 100, log_return: 0 },
    { date: '2024-03-11', close: 105, log_return: Math.log(1.05) },
    { date: '2024-03-12', close: 105, log_return: 0 }
  ];
  // t0 = mittlere Zeile; die Bewegung liegt AUF t0, also muss t-1 darunter liegen.
  const r = S.analyzeMoonEffect(rows, [{ date: '2024-03-11', phase: 'Neumond' }], 1, 1);
  ergebnis.moon = r ? { curve: r.all_curves[0].curve, total: r.all_curves[0].total_return } : null;
}

// 5) Volle ToM-Kurve fuer den Vergleich gegen Python — nicht nur ein Element.
//    Ein verschobenes JS koennte [0,5,5] liefern und einen Test bestehen, der
//    nur curve[2] === 5 prueft.
{
  const rows = [
    { date: '2024-01-30', close: 100, log_return: 0 },
    { date: '2024-01-31', close: 100, log_return: 0 },
    { date: '2024-02-01', close: 105, log_return: Math.log(1.05) }
  ];
  const r = S.analyzeTurnOfMonth(rows, 1, 1, [1], [2024]);
  ergebnis.tom_voll = r ? r.all_curves[0].curve : null;
}

// 6) yearEndRef/yearCovers — die Sperren gegen Zirkelschluss.
{
  const mk = (lad) => ({ last_actual_day: lad, full_365: new Array(365).fill(100) });
  const f = (yd, jetzt) => {
    const ref = S.yearEndRef(yd, jetzt);
    return { ref: ref, akzeptiert: Object.keys(yd).filter(y => S.yearCovers(yd[y], 365, ref)) };
  };
  ergebnis.yearcovers = {
    nur_laufendes:   f({ 2026: mk(250) }, 2026),
    alle_kurz:       f({ 2025: mk(250), 2026: mk(250) }, 2026),
    dez_delisting:   f({ 2024: mk(349) }, 2026),
    // Einziges Jahr ist das LAUFENDE, aber schon bei Tag 364: ohne die
    // Sperre 'nur abgeschlossene Jahre stiften die Referenz' wuerde es
    // sich selbst beglaubigen. Es gibt kein abgeschlossenes Jahr als
    // Massstab -> streng bleiben.
    nur_laufendes_spaet: f({ 2026: mk(364) }, 2026),
    voll_plus_kurz:  f({ 2023: mk(364), 2024: mk(364), 2026: mk(250) }, 2026)
  };
}

process.stdout.write(JSON.stringify(ergebnis, null, 1));

/**
 * feiertag_ereignismarkt.js — MESSUNG, kein Umbau.
 *
 * Frage (Nutzerentscheidung 2026-10-20: „erst messen, dann entscheiden"):
 * Die Strategien „Feiertag 1-Tag" (`calc_one_day_holiday`) und „UHTS"
 * (`calc_uhts`) nehmen den Handelsanlass heute aus `_nyseHolidays(y)` — fest
 * NYSE, unabhaengig vom gewaehlten Ticker. SAP.DE handelt damit um Thanksgiving
 * und den 4. Juli, nicht um den 3. Oktober. Lohnt die Umstellung auf den
 * Kalender der Tickerboerse?
 *
 *   node scripts/research/feiertag_ereignismarkt.js <kurse.json> [stichtag=YYYY-MM-DD]
 *
 * Vorgehen:
 *  - Die Module werden in der Reihenfolge geladen, in der /plain-vanilla sie
 *    laedt (Liste aus dem HTML, nicht von Hand gepflegt) — derselbe Weg wie
 *    scripts/js/probe_plain_vanilla_messlauf.js. Dazu `boersenkalender.js` fuer
 *    die Ereignisarten.
 *  - Variante A (Bestand): `_nyseHolidays` unveraendert.
 *  - Variante B (lokal): `_nyseHolidays(y)` liefert die Schliessungen der
 *    TICKERBOERSE. Gefiltert wird auf `art in {feiertag, ersatztag}` und das
 *    WIRKSAME Datum: `sonderschliessung` ist kein vorhersehbarer Handelsanlass
 *    (so wie im Bestand), und ein `halbtag` ist eine OFFENE Sitzung, also kein
 *    Feiertag.
 *  - Kennzahlen kommen aus `SA.strategy.auswerten`, dem gemeinsamen Rechenweg
 *    der Seite — nicht aus einer eigenen Statistik.
 *
 * Es wird NICHTS geaendert und nichts geschrieben ausser der Ausgabe.
 */
'use strict';
const fs = require('fs');
const path = require('path');

const REPO = path.resolve(__dirname, '..', '..');
const [kursDatei, stichtagArg] = process.argv.slice(2);
if (!kursDatei) {
  console.error('Aufruf: node scripts/research/feiertag_ereignismarkt.js <kurse.json> [stichtag]');
  process.exit(2);
}

const BROWSER_ONLY = new Set(['auth.js', 'i18n.js', 'app.js', 'charts.js', 'tour-config.js', 'tour.js']);
const html = fs.readFileSync(path.join(REPO, 'landing/pages/plain-vanilla.html'), 'utf8');
const srcs = [...html.matchAll(/<script src="\/landing\/js\/([^"?]+)/g)].map((m) => m[1]);

const window = {};
require('../js/release_harness').bereite(window);
const geladen = [];
for (const f of srcs.concat(['boersenkalender.js'])) {
  if (BROWSER_ONLY.has(f) || geladen.includes(f)) continue;
  const p = path.join(REPO, 'landing/js', f);
  if (!fs.existsSync(p)) continue;
  const code = fs.readFileSync(p, 'utf8');
  new Function('window', 'var SA = window.SA || {};\n' + code + '\nwindow.SA = SA;')(window);
  geladen.push(f);
}
const SA = window.SA;
for (const pflicht of ['strategy-compute.js', 'holidays.js', 'boersenkalender.js']) {
  if (!geladen.includes(pflicht)) throw new Error('[Aufbau] ' + pflicht + ' nicht geladen');
}
if (!SA.strategy || !SA.STRATEGIES || !SA.boersenkalender) throw new Error('[Aufbau] Module unvollstaendig');

// ── Ereignisarten pruefen, statt sie anzunehmen ────────────────────────────
const probe = SA.boersenkalender.ereignisse(2026, 'NYSE');   // Jahr ZUERST (JS-Vertrag)
if (!Array.isArray(probe) || !probe.length) throw new Error('[Aufbau] ereignisse() leer');
for (const feld of ['art', 'wirksam']) {
  if (!(feld in probe[0])) throw new Error('[Aufbau] Ereignis ohne Feld ' + feld + ': ' + Object.keys(probe[0]));
}
const ARTEN_SCHLIESSUNG = new Set(['feiertag', 'ersatztag']);

function lokaleSchliessungen(jahr, boerse) {
  return SA.boersenkalender.ereignisse(jahr, boerse)
    .filter((e) => ARTEN_SCHLIESSUNG.has(e.art))
    .map((e) => e.wirksam)
    .filter((d) => !!d)
    .sort();
}

// ── Daten ──────────────────────────────────────────────────────────────────
const kurse = JSON.parse(fs.readFileSync(kursDatei, 'utf8'));
const STRATEGIEN = ['one_day_holiday', 'uhts'];

function stichtagVon(rows) {
  if (stichtagArg) return stichtagArg;
  return rows.length ? rows[rows.length - 1].date : null;
}

function zahl(v, n) { return v == null ? '—' : (typeof v === 'number' ? v.toFixed(n) : String(v)); }
// node formatiert `%-9s` NICHT (nur %s/%d/%f). Die erste Fassung gab die
// Formatzeichenkette woertlich aus — Spaltenbreite also selbst setzen.
function sp(v, b, rechts) {
  var t = v == null ? '—' : String(v);
  while (t.length < b) t = rechts ? ' ' + t : t + ' ';
  return t;
}

console.log('Messung: Ereignismarkt der Feiertagsstrategien (Variante A = Bestand NYSE, B = Tickerboerse)');
console.log('Kennzahlen aus SA.strategy.auswerten, dem gemeinsamen Rechenweg der Seite.');
console.log('');

const zeilen = [];
for (const ticker of Object.keys(kurse)) {
  const rows = kurse[ticker] || [];
  if (rows.length < 500) { console.log('  %s uebersprungen (%d Zeilen)', ticker, rows.length); continue; }
  const boerse = SA.holidays.detect(ticker);
  const stichtag = stichtagVon(rows);
  const jahre = [...new Set(rows.map((r) => +String(r.date).slice(0, 4)))].sort();

  // Variante B vorbereiten und PRUEFEN, dass sie ueberhaupt eine andere Menge ist.
  // Nur Jahre, in denen der Kalender der TICKERBOERSE `belegt` ist. Ohne diese
  // Grenze ruht der Vergleich fuer ^GDAXI auf 43 von 68 Jahren mit ungepruefter
  // XETRA-Historie (belegt erst ab 2002) — und genau dort faellt das Ergebnis am
  // guenstigsten aus. Eine Aenderung, die die eigenen Zahlen verbessert, braucht
  // mehr Pruefung, nicht weniger. BEIDE Varianten laufen auf derselben
  // Jahresmenge, damit nicht die Jahreswahl den Unterschied macht.
  const belegteJahre = jahre.filter(function (j) {
    try { return SA.boersenkalender.status(boerse, j) === 'belegt'; } catch (e) { return false; }
  });
  const nurBelegt = new Set(belegteJahre);
  const lokal = {};
  let anzLokal = 0, anzNyse = 0;
  for (const j of belegteJahre) {
    try { lokal[j] = lokaleSchliessungen(j, boerse); } catch (e) { lokal[j] = []; }
    anzLokal += lokal[j].length;
    try { anzNyse += SA.strategy._nyseHolidays(j).length; } catch (e) { /* Kalenderbereich */ }
  }

  const echt = SA.strategy._nyseHolidays;
  for (const key of STRATEGIEN) {
    const ergebnis = {};
    // A: Bestand — aber auf derselben Jahresmenge wie B
    SA.strategy._nyseHolidays = function (y) {
      return nurBelegt.has(y) ? echt.call(SA.strategy, y) : [];
    };
    ergebnis.A = SA.strategy.auswerten(rows, key, { stichtag: stichtag, boerse: boerse });
    // B: lokal
    SA.strategy._nyseHolidays = function (y) { return (lokal[y] || []).slice(); };
    ergebnis.B = SA.strategy.auswerten(rows, key, { stichtag: stichtag, boerse: boerse });
    SA.strategy._nyseHolidays = echt;

    const a = (ergebnis.A && ergebnis.A.stats) || {}, b = (ergebnis.B && ergebnis.B.stats) || {};
    zeilen.push({
      ticker: ticker, boerse: boerse, strategie: key,
      jahre: jahre.length, belegte_jahre: belegteJahre.length,
      schliessungen_nyse: anzNyse, schliessungen_lokal: anzLokal,
      a_n: a.n_trades, b_n: b.n_trades,
      a_wr: a.win_rate, b_wr: b.win_rate,
      a_pf: a.profit_factor, b_pf: b.profit_factor,
      a_sh: a.sharpe, b_sh: b.sharpe,
      a_avg: a.avg_return, b_avg: b.avg_return,
    });
  }
}

const K = ['ticker', 'boerse', 'strategie'];
console.log(sp('Ticker', 9) + ' ' + sp('Boerse', 8) + ' ' + sp('Strategie', 16) + ' '
  + sp('A n', 5, 1) + ' ' + sp('B n', 5, 1) + '  | ' + sp('A WR%', 6, 1) + ' ' + sp('B WR%', 6, 1)
  + '  | ' + sp('A PF', 5, 1) + ' ' + sp('B PF', 5, 1) + '  | ' + sp('A Sh', 5, 1) + ' ' + sp('B Sh', 5, 1));
for (const z of zeilen) {
  console.log(sp(z.ticker, 9) + ' ' + sp(z.boerse, 8) + ' ' + sp(z.strategie, 16) + ' '
    + sp(z.a_n, 5, 1) + ' ' + sp(z.b_n, 5, 1) + '  | ' + sp(zahl(z.a_wr, 1), 6, 1) + ' '
    + sp(zahl(z.b_wr, 1), 6, 1) + '  | ' + sp(zahl(z.a_pf, 2), 5, 1) + ' '
    + sp(zahl(z.b_pf, 2), 5, 1) + '  | ' + sp(zahl(z.a_sh, 2), 5, 1) + ' ' + sp(zahl(z.b_sh, 2), 5, 1));
}
console.log('');
console.log('Schliessungen im Datenbereich je Ticker (A = NYSE, B = Tickerboerse):');
const gesehen = new Set();
for (const z of zeilen) {
  if (gesehen.has(z.ticker)) continue;
  gesehen.add(z.ticker);
  console.log('  ' + sp(z.ticker, 9) + ' ' + sp(z.boerse, 8) + ' ' + sp(z.jahre, 4, 1)
    + ' Jahre Daten, ' + sp(z.belegte_jahre, 4, 1) + ' davon mit belegtem Kalender'
    + '  | Schliessungen A ' + sp(z.schliessungen_nyse, 4, 1) + '  B ' + sp(z.schliessungen_lokal, 4, 1));
}
console.log('');
console.log('MESSUNG-ENDE ' + zeilen.length + ' Zeilen');

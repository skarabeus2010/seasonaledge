/**
 * probe_tdom_nenner.js — die beiden Nenner der Dashboard-Kacheln, an den ECHTEN
 * Seitenfunktionen gemessen (aus landing/pages/dashboard.html geschnitten, nicht
 * nachgebaut).
 *
 * (1) "TDOM 15 / 23": der Nenner war das historische Maximum ueber alle Jahre statt der
 *     Handelstage des laufenden Monats. Oktober 2026 hat 22 Handelstage.
 * (2) "Rang 5 / 23": ein `return` in der .map-Rueckruffunktion warf die Phase
 *     Dezember H2 fuer ALLE Jahre weg, sobald EIN Jahr vor dem 31.12. endete.
 *     Der Methodiktext sagt "Rang (1-24)".
 *
 * Aufruf: node scripts/js/probe_tdom_nenner.js
 * Exit 0 gruen, 1 rot.
 */
'use strict';
const fs = require('fs');
const path = require('path');

const WURZEL = path.resolve(__dirname, '..', '..');
const SEITE = path.join(WURZEL, 'landing', 'pages', 'dashboard.html');
const html = fs.readFileSync(SEITE, 'utf8');

let fehler = 0;
let anzahl = 0;
function pruef(name, ok, info) {
  anzahl++;
  console.log('  ' + (ok ? 'ok  ' : 'FAIL') + ' ' + name + (info !== undefined ? '  ->  ' + info : ''));
  if (!ok) fehler++;
}

/** Eine Funktion woertlich aus der Seite schneiden. */
function schneide(name) {
  const start = html.indexOf('function ' + name + '(');
  if (start < 0) throw new Error('Funktion nicht gefunden: ' + name);
  let i = html.indexOf('{', start), tiefe = 0;
  for (let j = i; j < html.length; j++) {
    if (html[j] === '{') tiefe++;
    else if (html[j] === '}') { tiefe--; if (tiefe === 0) return html.slice(start, j + 1); }
  }
  throw new Error('Funktionsende nicht gefunden: ' + name);
}

// ── Kalender: echte Fassung aus landing/js/ ────────────────────────────────────────
const sandbox = { console, Math, Date, Object, Number, String, Array, JSON, parseInt, parseFloat, isNaN, isFinite };
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
const vm = require('vm');
vm.createContext(sandbox);
sandbox.SA = { __release: function () {}, kalenderMethode: 'alt' };
vm.runInContext(fs.readFileSync(path.join(WURZEL, 'landing', 'js', 'holidays.js'), 'utf8'), sandbox);

// Hilfen, die die geschnittenen Funktionen brauchen
vm.runInContext(`
  // woertlich aus landing/pages/dashboard.html geschnitten, nicht nachgebaut:
  function _clean(arr){var o=[];for(var i=0;i<arr.length;i++){var v=arr[i];if(v!=null&&typeof v==='number'&&!isNaN(v)&&isFinite(v))o.push(v);}return o;}
  function mean(a){var v=_clean(a);if(!v.length)return 0;var s=0;for(var i=0;i<v.length;i++)s+=v[i];return s/v.length;}
  function stdev(a){var v=_clean(a);if(v.length<2)return 0;var m=mean(v),sq=0;for(var i=0;i<v.length;i++)sq+=(v[i]-m)*(v[i]-m);return Math.sqrt(sq/v.length);}
  function pad2(n){return n<10?'0'+n:''+n;}
  var MONTHS_DE = ['Januar','Februar','Maerz','April','Mai','Juni','Juli','August','September','Oktober','November','Dezember'];
  var MONTHS_DE_SHORT = ['Jan','Feb','Mrz','Apr','Mai','Jun','Jul','Aug','Sep','Okt','Nov','Dez'];
  var WEEKDAYS_DE = ['So','Mo','Di','Mi','Do','Fr','Sa'];
  var MONTH_START_DOY = [1,32,60,91,121,152,182,213,244,274,305,335];
  var currentTicker = 'QQQ';

`, sandbox);


for (const fn of ['calcIntramonthCurve', 'calcTdomPositionStreak', 'getTdomMiniStats',
                  'computeTwoWeekPhases', 'todayDoy']) {
  try { vm.runInContext(schneide(fn), sandbox); } catch (e) {
    console.log('  FAIL Funktion ' + fn + ' nicht ladbar: ' + e.message); fehler++;
  }
}

// ── (1) Nenner der TDOM-Kachel ────────────────────────────────────────────────────
// Handelstage je Oktober unabhaengig bestimmt (aus dem Kalender der Seite selbst, aber
// ueber einen anderen Weg als die zu pruefende Funktion: hier Tag fuer Tag gezaehlt).
function handelstage(jahr, monat) {
  const letzter = new Date(jahr, monat, 0).getDate();
  let n = 0;
  for (let d = 1; d <= letzter; d++) {
    const s = jahr + '-' + (monat < 10 ? '0' : '') + monat + '-' + (d < 10 ? '0' : '') + d;
    if (sandbox.SA.holidays.isTradingDay(s, 'NYSE')) n++;
  }
  return n;
}

const HT_OKT_2026 = handelstage(2026, 10);
pruef('[Aufbau] Oktober 2026 hat 22 Handelstage', HT_OKT_2026 === 22, HT_OKT_2026);

// Kurszeilen bauen: 27 Oktober mit JE EIGENER Laenge (21 bis 23 Handelstage), damit das
// historische Maximum (23) vom laufenden Monat (22) abweicht — genau der Fall, den der
// alte Nenner verwechselt hat.
const zeilen = [];
for (let jahr = 1999; jahr <= 2026; jahr++) {
  const letzter = new Date(jahr, 10, 0).getDate();
  let t = 0;
  for (let d = 1; d <= letzter; d++) {
    const s = jahr + '-10-' + (d < 10 ? '0' : '') + d;
    if (!sandbox.SA.holidays.isTradingDay(s, 'NYSE')) continue;
    t++;
    if (jahr === 2026 && t > 15) break;          // laufender Monat bis TDOM 15
    zeilen.push({ date: s, close: 100 + t, log_return: 0.001, year: jahr, month: 10, tdom: t });
  }
}
const maxHistorisch = Math.max.apply(null, zeilen.filter(z => z.year < 2026).map(z => z.tdom));
pruef('[Aufbau] hoechster TDOM aller Vorjahre ist 23 (weicht von 22 ab)',
      maxHistorisch === 23, maxHistorisch);

const jahre = [];
for (let j = 1999; j <= 2026; j++) jahre.push(j);
const mini = sandbox.getTdomMiniStats(zeilen, new Date(2026, 9, 21), jahre, {});
pruef('TDOM-Kachel: Zaehler ist die Position im laufenden Monat',
      mini && mini.tdom === 15, mini && mini.tdom);
pruef('TDOM-Kachel: Nenner sind die Handelstage DIESES Monats (22), nicht das historische Maximum (23)',
      mini && mini.maxTdom === HT_OKT_2026, mini && mini.maxTdom);

// ── (2) Rang-Nenner der Zwei-Wochen-Kachel ───────────────────────────────────────
// 27 Jahre, davon acht mit letztem Handelstag VOR dem 31.12. — wie im Bestand.
const yearData = {};
for (let j = 1999; j <= 2025; j++) {
  const kurve = new Array(365);
  for (let i = 0; i < 365; i++) kurve[i] = 100 + i * 0.05;
  const frueh = [2000, 2005, 2006, 2011, 2016, 2017, 2022, 2023].indexOf(j) >= 0;
  yearData[j] = { full_365: kurve, last_actual_day: frueh ? 363 : 365 };
}
const tw = sandbox.computeTwoWeekPhases(yearData, 2026);
pruef('Zwei-Wochen-Kachel: alle 24 Phasen bekommen einen Wert (Dezember H2 faellt nicht weg)',
      tw && tw.total === 24, tw && tw.total);

console.log('PROBE-ENDE ' + anzahl);
if (fehler) { console.log('\n[FEHLER] ' + fehler + ' Pruefung(en) rot'); process.exit(1); }
console.log('\n[OK] alle Pruefungen gruen');

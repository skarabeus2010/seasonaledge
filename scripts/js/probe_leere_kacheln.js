/**
 * probe_leere_kacheln.js — eine leere Kachel sagt, WARUM sie leer ist.
 *
 * Nutzerwunsch 2026-10-22. Vorher stand an vier Stellen derselbe Satz "Nicht genug
 * Daten" — der beantwortet nichts: zu wenig wovon, und ab wann reicht es?
 *
 * Geprueft werden die ECHTEN Rechenfunktionen aus landing/pages/dashboard.html. Jeder
 * Fall wird so gebaut, dass genau EIN Grund zutrifft, und der Grund muss die Zahl
 * nennen, an der es scheitert.
 *
 * Aufruf: node scripts/js/probe_leere_kacheln.js   — Exit 0 gruen, 1 rot.
 */
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const WURZEL = path.resolve(__dirname, '..', '..');
const html = fs.readFileSync(path.join(WURZEL, 'landing', 'pages', 'dashboard.html'), 'utf8');
const de = JSON.parse(fs.readFileSync(path.join(WURZEL, 'landing', 'i18n', 'de.json'), 'utf8'));
const en = JSON.parse(fs.readFileSync(path.join(WURZEL, 'landing', 'i18n', 'en.json'), 'utf8'));

let fehler = 0, anzahl = 0;
function pruef(name, ok, info) {
  anzahl++;
  console.log('  ' + (ok ? 'ok  ' : 'FAIL') + ' ' + name + (info !== undefined ? '  ->  ' + info : ''));
  if (!ok) fehler++;
}

function schneide(name, art) {
  const muster = (art === 'var') ? ('var ' + name + ' = [') : ('function ' + name + '(');
  const start = html.indexOf(muster);
  if (start < 0) throw new Error('nicht gefunden: ' + name);
  if (art === 'var') return html.slice(start, html.indexOf('\n    ];', start) + 7);
  let tiefe = 0;
  for (let j = html.indexOf('{', start); j < html.length; j++) {
    if (html[j] === '{') tiefe++;
    else if (html[j] === '}') { tiefe--; if (tiefe === 0) return html.slice(start, j + 1); }
  }
  throw new Error('kein Ende: ' + name);
}

const box = { console, Math, Date, Object, Number, Array, String, isFinite, isNaN, parseInt, parseFloat };
box.window = box;
box.localStorage = { getItem() { return null; }, setItem() {} };
box.SA = { __release() {}, kalenderMethode: 'alt' };
vm.createContext(box);
vm.runInContext(fs.readFileSync(path.join(WURZEL, 'landing', 'js', 'holidays.js'), 'utf8'), box);
vm.runInContext(
  "function mean(a){return a.reduce(function(s,x){return s+x;},0)/a.length;}"
  + "function _clean(a){return a.filter(function(x){return x!=null&&!isNaN(x);});}"
  + "function stdev(a){var v=_clean(a);if(v.length<2)return 0;var m=mean(v),s=0;"
  + "for(var i=0;i<v.length;i++)s+=(v[i]-m)*(v[i]-m);return Math.sqrt(s/v.length);}"
  + "function pad2(n){return n<10?'0'+n:''+n;}"
  + "function _t(k,d){return d;}"
  + "var MONTHS_DE=['Januar','Februar','Maerz','April','Mai','Juni','Juli','August','September','Oktober','November','Dezember'];"
  + "var WEEKDAYS_DE=['Sonntag','Montag','Dienstag','Mittwoch','Donnerstag','Freitag','Samstag'];"
  + "var WEEKDAYS_SHORT=['So','Mo','Di','Mi','Do','Fr','Sa'];"
  + "var currentTicker='QQQ';", box);
vm.runInContext(schneide('TDOM_METHODEN', 'var'), box);
for (const fn of ['_zahl', 'calcTdomMethoden', 'besteTdomMethode', 'tdomSerie',
                  'tdomMethodeGewaehlt', 'tdomMethodeName', 'calcIntramonthCurve',
                  'calcTdomPositionStreak', 'getTdomMiniStats', 'calcWeekdayStatsSingle',
                  'calcCurrentMonthPerf', 'calcOvernightStats']) {
  vm.runInContext(schneide(fn), box);
}

function zahlDrin(txt) { return /\d/.test(txt || ''); }

// ── Wochentag: zu wenige Beobachtungen ──────────────────────────────────────────
let info = {};
const wenig = [];
for (let i = 0; i < 20; i++) {
  const d = new Date(Date.UTC(2026, 0, 5 + i));          // Mo .. nur wenige je Wochentag
  wenig.push({ date: d.toISOString().slice(0, 10), close: 100 + i });
}
// Die ERWARTETE Anzahl unabhaengig zaehlen: der Grund muss GENAU sie nennen.
// "enthaelt eine Ziffer" waere eine Scheinpruefung — der Text traegt die Schwelle "5"
// ohnehin und bliebe gruen, wenn statt der Zahl ein Wort eingesetzt wuerde.
let erwartet = 0;
for (let i = 1; i < wenig.length; i++) {
  const d = new Date(wenig[i].date + 'T00:00:00Z');
  let w = d.getUTCDay(); w = (w === 0) ? 6 : w - 1;
  if (w === 0) erwartet++;
}
const wd = box.calcWeekdayStatsSingle(wenig, 0, 25, info);
pruef('[Aufbau] die Fixture hat genau ' + erwartet + ' Montage (und 5 waeren die Schwelle)',
      erwartet > 0 && erwartet < 5 && erwartet !== 5, erwartet);
pruef('Wochentag mit zu wenigen Beobachtungen -> Grund nennt die GEMESSENE Anzahl',
      wd === null && !!info.grund
      // Ohne RegExp-Konstruktor: dort ging der Backslash beim Schreiben verloren und
      // aus \D wurde ein woertliches D — die Pruefung konnte nie zutreffen.
      && String(info.grund).split(/[^0-9]+/).indexOf(String(erwartet)) >= 0, info.grund);

// ── Monatsperformance: kein abgeschlossener Monat ───────────────────────────────
info = {};
const mp = box.calcCurrentMonthPerf(
  [{ date: '2026-01-05', close: 100 }, { date: '2026-01-06', close: 101 }], 25, info);
pruef('Monatsperformance ohne abgeschlossenes Jahr -> leer MIT Grund',
      mp === null && info.grund && info.grund.length > 30, info.grund);

// ── Overnight: drei verschiedene Gruende, die sich UNTERSCHEIDEN muessen ────────
info = {};
box.calcOvernightStats([{ date: '2026-01-05', open: 1, close: 1 }], 25, 3, info);
const g1 = info.grund;
info = {};
const viele = [];
for (let i = 0; i < 400; i++) {
  const d = new Date(Date.UTC(2024, 0, 1 + i));
  viele.push({ date: d.toISOString().slice(0, 10), open: 100, close: 101 });
}
box.calcOvernightStats(viele, 25, 0, info);           // Sonntag
const g2 = info.grund;
pruef('Overnight: zu kurze Historie -> eigener Grund', !!g1, g1);
pruef('Overnight: Wochenende -> eigener Grund', !!g2, g2);
pruef('die beiden Overnight-Gruende sind verschieden', g1 !== g2);

// ── TDOM: kein Handelstag ───────────────────────────────────────────────────────
info = {};
const tdomRows = [];
for (let jahr = 2000; jahr <= 2025; jahr++) {
  for (let t = 1; t <= 20; t++) {
    tdomRows.push({ date: jahr + '-10-' + pad(t), open: 100, close: 101,
                    log_return: 0.001, year: jahr, month: 10, tdom: t });
  }
}
function pad(n) { return n < 10 ? '0' + n : '' + n; }
const jahre = []; for (let j = 2000; j <= 2026; j++) jahre.push(j);
const methTab = box.calcTdomMethoden(tdomRows, 10, jahre);

const samstag = new Date(2026, 9, 24);                 // 24.10.2026 ist ein Samstag
pruef('[Aufbau] 24.10.2026 ist kein NYSE-Handelstag',
      !box.SA.holidays.isTradingDay('2026-10-24', 'NYSE'));
info = {};
const m1 = box.getTdomMiniStats(tdomRows, samstag, jahre, {}, methTab, info);
pruef('TDOM am Wochenende -> leer MIT Grund', m1 === null && !!info.grund, info.grund);

// ── TDOM: Position ohne Vergleichsjahre ─────────────────────────────────────────
info = {};
const spaet = new Date(2026, 9, 30);                   // TDOM 22 — die Fixture endet bei 20
const m2 = box.getTdomMiniStats(tdomRows, spaet, jahre, {}, methTab, info);
pruef('TDOM-Position ohne Vergleichsjahre -> leer MIT Grund und Positionsnummer',
      m2 === null && info.grund && zahlDrin(info.grund), info.grund);

// ── Jeder Grund in beiden Sprachen vorhanden ───────────────────────────────────
const SCHLUESSEL = ['dash.leer_unbekannt', 'dash.leer_wochentag', 'dash.leer_monat',
  'dash.leer_on_kurse', 'dash.leer_on_we', 'dash.leer_on_n', 'dash.leer_kein_ht',
  'dash.leer_tdom_pos', 'dash.leer_meth_n', 'dash.leer_meth', 'dash.leer_phase',
  'dash.leer_on_fehler', 'dash.leer_kein_folgetag'];
for (const k of SCHLUESSEL) {
  pruef('[i18n] ' + k + ' in DE und EN',
        typeof de[k] === 'string' && de[k].length > 15
        && typeof en[k] === 'string' && en[k].length > 15);
}

// Kein Grund darf der alte Allgemeinplatz sein.
pruef('kein Grund lautet mehr "Nicht genug Daten"',
      SCHLUESSEL.every(k => (de[k] || '').indexOf('Nicht genug Daten') < 0));
// Die Platzhalter muessen in beiden Sprachen dieselben sein, sonst bleibt im EN ein
// {n} stehen.
for (const k of SCHLUESSEL) {
  // Fehlt ein Schluessel, hat die Pruefung darueber das schon gemeldet — hier darf die
  // Probe daran nicht STERBEN: ein Absturz ist kein Nachweis.
  if (typeof de[k] !== 'string' || typeof en[k] !== 'string') continue;
  const pd = (de[k].match(/\{[a-z]\}/g) || []).sort().join(',');
  const pe = (en[k].match(/\{[a-z]\}/g) || []).sort().join(',');
  if (pd || pe) pruef('[i18n] ' + k + ': gleiche Platzhalter in DE und EN', pd === pe, pd + ' / ' + pe);
}

console.log('PROBE-ENDE ' + anzahl);
if (fehler) { console.log('\n[FEHLER] ' + fehler + ' Pruefung(en) rot'); process.exit(1); }
console.log('\n[OK] alle Pruefungen gruen');

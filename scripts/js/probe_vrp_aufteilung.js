/**
 * probe_vrp_aufteilung.js — die VRP-Kachel auf /skew.
 *
 * Nutzerbefund 2026-10-21: "die negativen Werte fehlen". Nachgemessen an den Live-Daten
 * fehlten sie NICHT — von 163 Tickern hatten 14 ein negatives VRP, aber keiner davon
 * gehoert zu Mag7, und dort war die Kategorie gewaehlt. Die leere linke Haelfte war
 * also ein Ergebnis, kein Defekt.
 *
 * Diese Probe haelt beides fest:
 *   1. renderVRP verwirft KEINEN Wert nach dem Vorzeichen — negative Ticker bekommen
 *      einen Balken auf der linken Seite.
 *   2. Die Kachel nennt die Aufteilung, damit eine leere Haelfte nicht wie ein
 *      fehlender Balken aussieht.
 *
 * Geprueft wird an der ECHTEN Funktion aus landing/pages/skew.html, mit einem
 * DOM-Ersatz; die Fixture bildet den gemessenen Live-Stand nach (Mag7 nur positiv,
 * Finanzen gemischt).
 *
 * Aufruf: node scripts/js/probe_vrp_aufteilung.js   — Exit 0 gruen, 1 rot.
 */
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const WURZEL = path.resolve(__dirname, '..', '..');
const html = fs.readFileSync(path.join(WURZEL, 'landing', 'pages', 'skew.html'), 'utf8');

let fehler = 0, anzahl = 0;
function pruef(name, ok, info) {
  anzahl++;
  console.log('  ' + (ok ? 'ok  ' : 'FAIL') + ' ' + name + (info !== undefined ? '  ->  ' + info : ''));
  if (!ok) fehler++;
}

function schneide(name) {
  const start = html.indexOf('function ' + name + '(');
  if (start < 0) throw new Error('nicht gefunden: ' + name);
  let tiefe = 0;
  for (let j = html.indexOf('{', start); j < html.length; j++) {
    if (html[j] === '{') tiefe++;
    else if (html[j] === '}') { tiefe--; if (tiefe === 0) return html.slice(start, j + 1); }
  }
  throw new Error('kein Ende: ' + name);
}

// Schlanker DOM-Ersatz: die Funktion schreibt in innerHTML und haengt Klickhandler an.
function element() {
  const e = {
    innerHTML: '',
    querySelectorAll() { return []; },
  };
  return e;
}
const elemente = { 'sk-vrp-chart': element(), 'sk-vrp-cat': element() };

const box = { console, Math, Number, String, Array, Object, parseInt, parseFloat, isNaN, isFinite };
box.window = box;
box.document = { getElementById: function (id) { return elemente[id] || null; } };
vm.createContext(box);
vm.runInContext(
  "var ACC='#e8a820';"
  + "var KAT='alle';"
  + "function T(k,f){ return f; }"
  + "function _catName(){ return KAT; }"
  + "var _KAT_TICKER=null;"
  + "function _inCat(tk){ return !_KAT_TICKER || _KAT_TICKER.indexOf(tk)>=0; }"
  + "function selectTicker(){}", box);
vm.runInContext(schneide('_setCatTag'), box);
vm.runInContext(schneide('renderVRP'), box);

// Fixture nach dem gemessenen Live-Stand vom 21.10.2026.
const MAG7 = [
  { ticker: 'NVDA', vrp_pts: 16.37 }, { ticker: 'GOOGL', vrp_pts: 14.77 },
  { ticker: 'TSLA', vrp_pts: 13.73 }, { ticker: 'AMZN', vrp_pts: 11.61 },
  { ticker: 'AAPL', vrp_pts: 10.96 }, { ticker: 'MSFT', vrp_pts: 10.39 },
  { ticker: 'META', vrp_pts: 6.98 },
];
const FINANZEN = [
  { ticker: 'BLK', vrp_pts: 5.20 }, { ticker: 'WFC', vrp_pts: -6.05 },
  { ticker: 'SCHW', vrp_pts: -4.05 }, { ticker: 'PGR', vrp_pts: -1.37 },
];

// ── Fall 1: Kategorie ohne negative Werte (der Fall aus dem Nutzerbefund) ─────────
box.KAT = 'Mag7';
box._KAT_TICKER = MAG7.map(t => t.ticker);
box.renderVRP(MAG7);
let chart = elemente['sk-vrp-chart'].innerHTML;
let tag = elemente['sk-vrp-cat'].innerHTML;

pruef('alle sieben Mag7-Ticker bekommen eine Zeile',
      (chart.match(/sk-vrp-zeile/g) || []).length === 7,
      (chart.match(/sk-vrp-zeile/g) || []).length);
pruef('keine Zeile liegt links (kein negativer Wert in dieser Kategorie)',
      chart.indexOf('sk-vrp-bar dn') < 0);
pruef('die Kachel nennt die Aufteilung: 7 positiv, 0 negativ',
      /7 positiv/.test(tag) && /0 negativ/.test(tag), tag.replace(/<[^>]+>/g, ''));

// ── Fall 2: gemischte Kategorie — negative Werte MUESSEN erscheinen ───────────────
box.KAT = 'Finanzen';
box._KAT_TICKER = FINANZEN.map(t => t.ticker);
box.renderVRP(FINANZEN);
chart = elemente['sk-vrp-chart'].innerHTML;
tag = elemente['sk-vrp-cat'].innerHTML;

pruef('gemischte Kategorie: alle vier Ticker erscheinen',
      (chart.match(/sk-vrp-zeile/g) || []).length === 4,
      (chart.match(/sk-vrp-zeile/g) || []).length);
pruef('die drei negativen bekommen einen Balken auf der linken Seite',
      (chart.match(/sk-vrp-bar dn/g) || []).length === 3,
      (chart.match(/sk-vrp-bar dn/g) || []).length);
pruef('kein Wert wird nach dem Vorzeichen verworfen (WFC, SCHW, PGR sichtbar)',
      chart.indexOf('WFC') >= 0 && chart.indexOf('SCHW') >= 0 && chart.indexOf('PGR') >= 0);
pruef('die Kachel nennt die Aufteilung: 1 positiv, 3 negativ',
      /1 positiv/.test(tag) && /3 negativ/.test(tag), tag.replace(/<[^>]+>/g, ''));

// ── Fall 3: nur negative Werte — dann ist die RECHTE Haelfte leer ────────────────
box.KAT = 'nur negativ';
box._KAT_TICKER = ['WFC', 'SCHW'];
box.renderVRP(FINANZEN);
chart = elemente['sk-vrp-chart'].innerHTML;
tag = elemente['sk-vrp-cat'].innerHTML;
pruef('nur negative Werte: keine Zeile rechts, Aufteilung 0 positiv / 2 negativ',
      chart.indexOf('sk-vrp-bar up') < 0 && /0 positiv/.test(tag) && /2 negativ/.test(tag),
      tag.replace(/<[^>]+>/g, ''));

// ── Fall 4: die Achse bleibt symmetrisch um die Null ─────────────────────────────
pruef('Achse symmetrisch um die Null (Kategorien bleiben vergleichbar)',
      /<span>&minus;\d+<\/span><span>0<\/span><span>\+\d+<\/span>/.test(chart),
      (chart.match(/sk-vrp-achse[\s\S]{0,80}/) || [''])[0].replace(/<[^>]+>/g, ' ').trim());

console.log('PROBE-ENDE ' + anzahl);
if (fehler) { console.log('\n[FEHLER] ' + fehler + ' Pruefung(en) rot'); process.exit(1); }
console.log('\n[OK] alle Pruefungen gruen');

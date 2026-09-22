/* Faehrt das inline-JS von /skew gegen die ECHTEN Daten und prueft die
   Heatmap-Tabelle.

   Zwei Dinge stehen hier zur Debatte, beide vom Nutzer angestossen:
   (1) Die Farbskala darf keine RICHTUNG behaupten. Die Spalten messen
       Betraege und Preise; gruen/rot liest sich als Kauf-/Verkaufsempfehlung.
       Geprueft wird deshalb, dass jede Zelle dieselbe Farbe traegt und sich
       nur die Deckkraft unterscheidet.
   (2) Jede Spaltenueberschrift traegt ihre Definition als Tooltip.

   Das JS wird aus der SEITE gezogen, nicht aus einer Kopie. */
const fs = require('fs');
const path = require('path');

const REPO = path.resolve(__dirname, '..', '..');
const SEITE = path.join(REPO, 'landing/pages/skew.html');
const DATEN = {
  '/landing/data/options_skew.json': 'options_skew.json',
  '/landing/data/gex_summary.json': 'gex_summary.json',
  '/landing/data/options_skew_history.json': 'options_skew_history.json'
};

const el = {};
function neu(id) {
  const o = {
    id, _html: '', _text: '', value: '', style: {}, dataset: {},
    classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
    appendChild() {}, addEventListener() {}, scrollIntoView() {},
    querySelectorAll() { return []; }, querySelector() { return null; },
    closest() { return null; }, getAttribute() { return null; },
    setAttribute() {}, removeAttribute() {}, focus() {}
  };
  Object.defineProperty(o, 'innerHTML', { get() { return this._html; }, set(v) { this._html = v; } });
  Object.defineProperty(o, 'textContent', { get() { return this._text; }, set(v) { this._text = v; } });
  return o;
}
function hole(id) { return el[id] || (el[id] = neu(id)); }

global.ApexCharts = class { constructor() {} render() {} updateOptions() {} destroy() {} };
global.document = {
  readyState: 'complete',
  getElementById: hole,
  createElement: () => neu('x'),
  querySelectorAll: () => [],
  querySelector: () => null,
  addEventListener() {}
};
global.window = { SA: null, scrollTo() {}, addEventListener() {}, location: { search: '' } };
global.loadComponent = function () {};
global.fetch = (u) => {
  const f = DATEN[u];
  if (!f) return Promise.resolve({ ok: false, status: 404, json: () => Promise.reject(new Error(u)) });
  const d = JSON.parse(fs.readFileSync(path.join(REPO, 'landing/data', f), 'utf8'));
  return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(d) });
};

const html = fs.readFileSync(SEITE, 'utf8');
const bloecke = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
eval(bloecke.reduce((a, b) => (b.length > a.length ? b : a)));

setTimeout(() => {
  let fehler = 0;
  const pruefe = (b, was) => { console.log((b ? '  ok   ' : '  FEHL ') + was); if (!b) fehler++; };
  const t = hole('sk-table')._html;

  console.log('Tabelle gerendert:');
  pruefe(t.length > 500, t.length + ' Zeichen');
  // Die Tabelle startet bewusst auf der Kategorie 'Mag7' (7 Titel), nicht auf
  // 'Alle' — die Zeilenzahl ist also klein, und das ist richtig so.
  const zeilen = (t.match(/<tr data-tk=/g) || []).length;
  pruefe(zeilen >= 7, zeilen + ' Ticker-Zeilen (Standardfilter Mag7)');
  pruefe(!t.includes('undefined') && !t.includes('NaN'), 'kein undefined/NaN');

  console.log('Tooltips auf den Spaltenueberschriften:');
  const titel = [...t.matchAll(/<th[^>]*title="([^"]*)"/g)].map(m => m[1]);
  pruefe(titel.length === 11, titel.length + ' von 11 Spalten mit Tooltip');
  pruefe(titel.every(x => x.length > 60), 'alle Tooltips substanziell (>60 Zeichen)');
  pruefe(new Set(titel).size === titel.length, 'keine zwei Spalten mit demselben Text');
  // Ein leerer Fallback waere der stille Fehlerfall: title="" faellt nicht auf.
  pruefe(titel.every(x => x.trim().length > 0), 'kein leerer Tooltip');

  console.log('Farbskala:');
  const farben = [...t.matchAll(/background:rgba\(([^)]*)\)/g)].map(m => m[1].split(',').map(s => s.trim()));
  pruefe(farben.length > 50, farben.length + ' eingefaerbte Zellen');
  const hues = new Set(farben.map(c => c.slice(0, 3).join(',')));
  pruefe(hues.size === 1, hues.size === 1
    ? 'genau EINE Farbe (' + [...hues][0] + '), nur die Deckkraft variiert'
    : 'MEHRERE Farben: ' + [...hues].slice(0, 5).join(' | '));
  const alphas = [...new Set(farben.map(c => +c[3]))].sort((a, b) => a - b);
  pruefe(alphas.length > 5 && alphas[0] >= 0.05 && alphas[alphas.length - 1] <= 0.35,
    alphas.length + ' Deckkraft-Stufen von ' + alphas[0] + ' bis ' + alphas[alphas.length - 1]);

  console.log('');
  console.log(fehler === 0 ? 'ALLE PRUEFUNGEN BESTANDEN' : fehler + ' FEHLER');
  process.exit(fehler === 0 ? 0 : 1);
}, 600);

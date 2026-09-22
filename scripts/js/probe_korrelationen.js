/* Faehrt das inline-JS von /korrelationen gegen die ECHTEN Daten.

   DIE WICHTIGSTE PRUEFUNG hier ist nicht, ob etwas gezeichnet wird, sondern ob
   die Frontend-Formel DIESELBEN Zahlen liefert wie das Python-Skript, das die
   Daten erzeugt hat. Das sind zwei Implementierungen derselben Mathematik —
   genau die Konstellation, die in diesem Projekt schon zwei Black-Scholes-
   Kopien mit verschiedenen Zinssaetzen hervorgebracht hat.

   Das JS wird aus der SEITE gezogen, nicht aus einer Kopie. */
const fs = require('fs');
const path = require('path');

const REPO = path.resolve(__dirname, '..', '..');
const SEITE = path.join(REPO, 'landing/pages/korrelationen.html');
const DATEN = path.join(REPO, 'landing/data/korrelationen.json');
const daten = JSON.parse(fs.readFileSync(DATEN, 'utf8'));

const el = {};
function neu(id) {
  const o = {
    id, _html: '', _text: '', value: '', style: {},
    classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
    appendChild() {}, addEventListener() {}, scrollIntoView() {},
    closest() { return null; }, getAttribute() { return null; }
  };
  Object.defineProperty(o, 'innerHTML', { get() { return this._html; }, set(v) { this._html = v; } });
  Object.defineProperty(o, 'textContent', { get() { return this._text; }, set(v) { this._text = v; } });
  return o;
}
for (const id of ['error-banner', 'sel-a', 'sel-b', 'chart', 'kpis', 'tbl',
                  'btn-63', 'btn-252', 'btn-beide']) el[id] = neu(id);

let chartOpts = null;
global.ApexCharts = class { constructor(node, opts) { chartOpts = opts; } render() {} };
global.document = {
  readyState: 'complete',
  getElementById: (id) => el[id] || neu(id),
  createElement: () => neu('x'),
  addEventListener() {}
};
global.window = { SA: null, scrollTo() {} };
global.loadComponent = function () {};
global.fetch = () => Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(daten) });

const warnungen = [];
const echteWarn = console.warn;
console.warn = (...a) => { warnungen.push(a.join(' ')); };

function inlineJs() {
  const html = fs.readFileSync(SEITE, 'utf8');
  const bloecke = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
  if (!bloecke.length) throw new Error('kein inline-<script> in ' + SEITE);
  return bloecke.reduce((a, b) => (b.length > a.length ? b : a));
}
eval(inlineJs());

setTimeout(() => {
  console.warn = echteWarn;
  let fehler = 0;
  const pruefe = (b, was) => {
    console.log((b ? '  ok   ' : '  FEHL ') + was);
    if (!b) fehler++;
  };

  console.log('Gegenprobe gegen die Python-Referenz:');
  pruefe(warnungen.length === 0,
    warnungen.length === 0
      ? daten.referenz.length + ' Referenzwerte stimmen (Abweichung unter 0,002)'
      : 'ABWEICHUNG: ' + warnungen.join(' | '));

  console.log('Chart:');
  pruefe(chartOpts !== null, 'ApexCharts wurde aufgerufen');
  const reihe = chartOpts && chartOpts.series && chartOpts.series[0].data;
  pruefe(reihe && reihe.length > 200, (reihe ? reihe.length : 0) + ' Punkte gezeichnet');
  pruefe(reihe && reihe.every(p => p[1] >= -1 && p[1] <= 1),
    'alle Werte im gueltigen Band -1 bis +1');
  pruefe(chartOpts && chartOpts.yaxis && chartOpts.yaxis.min === -1 && chartOpts.yaxis.max === 1,
    'Y-Achse fest auf -1 bis +1 (kein Auto-Zoom, der kleine Schwankungen aufblaest)');

  console.log('KPIs:');
  const k = el['kpis']._html;
  pruefe(k.length > 100, 'KPI-Block gefuellt');
  pruefe(!k.includes('undefined') && !k.includes('NaN'), 'kein undefined/NaN');
  pruefe(/Perzentil/i.test(k), 'Perzentil wird ausgewiesen');

  console.log('Tabelle:');
  const t = el['tbl']._html;
  const zeilen = (t.match(/<tr data-a=/g) || []).length;
  pruefe(zeilen > 20, zeilen + ' Paare gelistet');
  pruefe(!t.includes('undefined') && !t.includes('NaN'), 'kein undefined/NaN');

  console.log('');
  console.log(fehler === 0 ? 'ALLE PRUEFUNGEN BESTANDEN' : fehler + ' FEHLER');
  process.exit(fehler === 0 ? 0 : 1);
}, 400);

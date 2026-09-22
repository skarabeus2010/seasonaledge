/* Faehrt das inline-JS von /vola-saisonalitaet gegen die ECHTEN Daten, mit
   einem DOM- und ApexCharts-Stub. "node --check" sagt nur, dass die Datei sich
   parsen laesst; hier soll herauskommen, ob Chart, KPIs und Tabelle
   tatsaechlich mit Inhalt gefuellt werden.

   Das JS wird aus der SEITE gezogen, nicht aus einer Kopie — eine Kopie waere
   genau der Fehler, den dieser Waechter verhindern soll. */
const fs = require('fs');
const path = require('path');

const REPO = path.resolve(__dirname, '..', '..');
const SEITE = path.join(REPO, 'landing/pages/vola-saisonalitaet.html');
const DATEN = path.join(REPO, 'landing/data/vol_saisonalitaet.json');
const daten = JSON.parse(fs.readFileSync(DATEN, 'utf8'));

const el = {};
function neu(id) {
  const o = {
    id, _html: '', _text: '', value: '', style: {},
    children: [],
    classList: { add() {}, remove() {}, contains() { return false; } },
    appendChild(c) { this.children.push(c); },
    addEventListener() {}, scrollIntoView() {}, closest() { return null; },
    getAttribute() { return null; }
  };
  Object.defineProperty(o, 'innerHTML', {
    get() { return this._html; }, set(v) { this._html = v; }
  });
  Object.defineProperty(o, 'textContent', {
    get() { return this._text; }, set(v) { this._text = v; }
  });
  return o;
}
for (const id of ['error-banner', 'verdict-big', 'tk', 'tk-list', 'sel-grp',
                  'chart', 'kpis', 'tbl']) el[id] = neu(id);

let chartOpts = null;
global.ApexCharts = function (node, opts) { chartOpts = opts; };
global.ApexCharts.prototype = {};
global.ApexCharts = class { constructor(node, opts) { chartOpts = opts; } render() {} };

global.document = {
  readyState: 'complete',
  getElementById: (id) => el[id] || neu(id),
  createElement: () => neu('opt'),
  addEventListener() {}
};
global.window = { SA: null, scrollTo() {} };
global.loadComponent = function () {};
global.fetch = () => Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(daten) });

function inlineJs() {
  const html = fs.readFileSync(SEITE, 'utf8');
  const bloecke = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
  if (!bloecke.length) throw new Error('kein inline-<script> in ' + SEITE);
  return bloecke.reduce((a, b) => (b.length > a.length ? b : a));
}
eval(inlineJs());

setTimeout(() => {
  let fehler = 0;
  const pruefe = (b, was) => {
    console.log((b ? '  ok   ' : '  FEHL ') + was);
    if (!b) fehler++;
  };

  console.log('Chart:');
  pruefe(chartOpts !== null, 'ApexCharts wurde aufgerufen');
  const reihe = chartOpts && chartOpts.series && chartOpts.series[0].data;
  pruefe(reihe && reihe.length === 12, '12 Monatswerte: ' + JSON.stringify(reihe));
  pruefe(reihe && reihe.filter(x => x != null).length >= 10,
    reihe.filter(x => x != null).length + ' Monate belegt');
  pruefe(reihe && reihe.every(x => x == null || (x > 0.3 && x < 3)),
    'alle Werte in plausiblem Band 0,3 bis 3');

  console.log('Verdikt und KPIs:');
  pruefe(el['verdict-big']._text.length > 10,
    'Verdikt gesetzt: "' + el['verdict-big']._text + '"');
  const k = el['kpis']._html;
  pruefe(k.includes('SPY'), 'KPI nennt den Ticker');
  pruefe(!k.includes('undefined') && !k.includes('NaN'), 'kein undefined/NaN in den KPIs');

  console.log('Tabelle:');
  const t = el['tbl']._html;
  const zeilen = (t.match(/<tr data-tk=/g) || []).length;
  pruefe(zeilen > 10, zeilen + ' Zeilen');
  pruefe(!t.includes('undefined') && !t.includes('NaN'), 'kein undefined/NaN in der Tabelle');
  pruefe(t.includes('data-tk="SPY"'), 'SPY steht in der Tabelle');

  console.log('Gruppen-Auswahl:');
  pruefe(el['sel-grp']._html.includes('<option'), 'Gruppen gefuellt');
  pruefe(el['tk-list'].children.length > 100,
    el['tk-list'].children.length + ' Ticker in der Vorschlagsliste');

  console.log('');
  console.log(fehler === 0 ? 'ALLE PRUEFUNGEN BESTANDEN' : fehler + ' FEHLER');
  process.exit(fehler === 0 ? 0 : 1);
}, 200);

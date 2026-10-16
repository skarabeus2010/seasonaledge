/* /skew liest Rang/Percentile aus dem Snapshot (Plan B3). Fuehrt das inline-JS der Seite aus der Datei aus
   (DOM-Attrappe wie probe_skew_tabelle.js) und faengt ab, was in den Radar-Chart geht.
   Aufruf: node probe_skew_rang_seite.js <snapshot.json>   Ausgabe: JSON {punkte, tabelle, quadText} */
const fs = require('fs');
const path = require('path');
const REPO = path.resolve(__dirname, '..', '..');
const snap = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const modus = process.argv[3] || 'pctl';     // pctl | rank
const ansicht = process.argv[4] || 'rr_iv';  // rr_iv | cs_ps
const fenster = process.argv[5] || '365';

const el = {}, charts = {};
function neu(id) {
  const o = {
    id, _html: '', style: {}, dataset: {}, value: '', textContent: '',
    classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
    appendChild() {}, addEventListener() {}, scrollIntoView() {}, setAttribute() {}, getAttribute() { return null; },
    querySelector() { return null; }, closest() { return null; }, insertBefore() {},
    querySelectorAll(sel) {
      if (sel !== 'button') return [];
      return (o._btns = [...o._html.matchAll(/data-v="([^"]+)"/g)].map((m) => ({ v: m[1], getAttribute: () => m[1] })));
    }
  };
  Object.defineProperty(o, 'innerHTML', { get() { return this._html; }, set(v) { this._html = String(v); } });
  return o;
}
const hole = (id) => el[id] || (el[id] = neu(id));
global.ApexCharts = class { constructor(e, o) { charts[e.id] = o; } render() { return Promise.resolve(); } updateOptions() {} destroy() {} };
global.document = { readyState: 'complete', getElementById: hole, createElement: () => neu('x'), body: { appendChild() {} },
                    querySelectorAll: () => [], querySelector: () => null, addEventListener() {} };
global.window = { SA: null, scrollTo() {}, addEventListener() {}, location: { search: '' } };
global.loadComponent = function () {};
global.fetch = (u) => {
  const k = u.split('?')[0];
  if (k === '/landing/data/options_skew.json') return Promise.resolve({ ok: true, json: () => Promise.resolve(JSON.parse(JSON.stringify(snap))) });
  return Promise.resolve({ ok: false, status: 404, json: () => Promise.reject(new Error(u)) });
};
const html = fs.readFileSync(path.join(REPO, 'landing/pages/skew.html'), 'utf8');
const bloecke = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
eval(bloecke.reduce((a, b) => (b.length > a.length ? b : a)));

function klick(boxId, wert) {
  const b = (hole(boxId)._btns || []).find((x) => x.v === wert);
  if (b && b.onclick) b.onclick();
}
setTimeout(() => {
  klick('sk-cat', 'cat:Alle');
  klick('sk-mode', modus);
  klick('sk-view', ansicht);
  klick('sk-win', fenster);
  setTimeout(() => {
    const o = charts['sk-quad'];
    const punkte = o && o.series && o.series[0] ? o.series[0].data.map((p) => ({ tk: p.tk, x: p.x, y: p.y })) : [];
    process.stdout.write(JSON.stringify({ punkte, quadText: hole('sk-quad').innerHTML.slice(0, 200),
                                          tabelle: hole('sk-table').innerHTML }));
    process.exit(0);
  }, 300);
}, 500);

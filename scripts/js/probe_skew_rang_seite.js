/* /skew liest Rang/Percentile aus dem Snapshot (Plan B3). Fuehrt das inline-JS der Seite aus der Datei aus
   (DOM-Attrappe wie probe_skew_tabelle.js) und faengt ab, was in den Radar-Chart geht.
   Aufruf: node probe_skew_rang_seite.js <snapshot.json> [modus ansicht fenster]   Ausgabe: JSON {punkte, tabelle,
   quadText, extrem}. Umgebung: SA_PROBE_KAT = Kategorie statt „Alle“; SA_PROBE_ZWEITER = zweiter Snapshot, der nach
   dem ersten im selben DOM gezeichnet wird (B3b: keine alten Einträge duerfen stehen bleiben); SA_PROBE_I18N = EN-
   Woerterbuch nach den Daten laden und sa:i18n-bereit ausloesen. */
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
const hoerer = {};   // document-Ereignisse (sa:i18n-bereit) werden gespeichert, nicht verworfen
global.document = { readyState: 'complete', getElementById: hole, createElement: () => neu('x'), body: { appendChild() {} },
                    querySelectorAll: () => [], querySelector: () => null,
                    addEventListener(typ, fn) { (hoerer[typ] = hoerer[typ] || []).push(fn); } };
global.window = { SA: null, scrollTo() {}, addEventListener() {}, location: { search: '' } };
global.loadComponent = function () {};
global.fetch = (u) => {
  const k = u.split('?')[0];
  if (k === '/landing/data/options_skew.json') return Promise.resolve({ ok: true, json: () => Promise.resolve(JSON.parse(JSON.stringify(snap))) });
  return Promise.resolve({ ok: false, status: 404, json: () => Promise.reject(new Error(u)) });
};
const html = fs.readFileSync(path.join(REPO, 'landing/pages/skew.html'), 'utf8');
const bloecke = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
// renderSkew liegt im IIFE der Seite; fuer den Zweit-Snapshot-Test nur NACH aussen reichen (Logik unveraendert).
const _haupt = bloecke.reduce((a, b) => (b.length > a.length ? b : a));
if (_haupt.indexOf('    function init(){') < 0) throw new Error('Anker function init() fehlt');
eval(_haupt.replace('    function init(){', '    globalThis.__renderSkew = renderSkew; function init(){'));

function klick(boxId, wert) {
  const b = (hole(boxId)._btns || []).find((x) => x.v === wert);
  if (b && b.onclick) b.onclick();
}
setTimeout(() => {
  klick('sk-cat', 'cat:' + (process.env.SA_PROBE_KAT || 'Alle'));
  klick('sk-mode', modus);
  klick('sk-view', ansicht);
  klick('sk-win', fenster);
  if (process.env.SA_PROBE_I18N) {   // Woerterbuch kommt NACH den Daten: EN aus en.json, dann das Ereignis der Seite
    const en = JSON.parse(fs.readFileSync(path.join(REPO, 'landing/i18n/en.json'), 'utf8'));
    global.SA = window.SA = { i18n: { t: (k, de) => (k in en ? en[k] : de) } };
    (hoerer['sa:i18n-bereit'] || []).forEach((fn) => fn());
  }
  if (process.env.SA_PROBE_ZWEITER) globalThis.__renderSkew(JSON.parse(fs.readFileSync(process.env.SA_PROBE_ZWEITER, 'utf8')));
  setTimeout(() => {
    const o = charts['sk-quad'];
    const punkte = o && o.series && o.series[0] ? o.series[0].data.map((p) => ({ tk: p.tk, x: p.x, y: p.y })) : [];
    process.stdout.write(JSON.stringify({ punkte, quadText: hole('sk-quad').innerHTML.slice(0, 200),
                                          tabelle: hole('sk-table').innerHTML, extrem: hole('sk-extrem').innerHTML }));
    process.exit(0);
  }, 300);
}, 500);

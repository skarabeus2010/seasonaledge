/* Faehrt das inline-JS von /skew mit einem Woerterbuch, das NACH den Daten kommt (Codex-Befund 2026-10-14):
   (1) Vor dem Woerterbuch stehen Legende und Untertitel im deutschen Fallback — das ist erwartet.
   (2) Der Nutzer schaltet vorher auf Rank.
   (3) Das Woerterbuch kommt (sa:i18n-bereit, danach _applyDOM wie in landing/js/i18n.js):
       Legende und Untertitel muessen englisch sein UND im Modus Rank bleiben.
   Dazu der Normalfall: Woerterbuch vor den Daten, Standard Percentile.
   Das JS wird aus der SEITE gezogen, nicht aus einer Kopie. Daten: landing/data (wie probe_skew_tabelle.js). */
const fs = require('fs');
const path = require('path');

const REPO = path.resolve(__dirname, '..', '..');
const html = fs.readFileSync(path.join(REPO, 'landing/pages/skew.html'), 'utf8');
const EN = JSON.parse(fs.readFileSync(path.join(REPO, 'landing/i18n/en.json'), 'utf8'));
const DATEN = {
  '/landing/data/options_skew.json': 'options_skew.json',
  '/landing/data/gex_summary.json': 'gex_summary.json',
  '/landing/data/options_skew_history.json': 'options_skew_history.json'
};
// Statisches HTML: Schluessel des Untertitels so, wie die Seite ihn ausliefert
const STATISCH = (html.match(/id="sk-quad-sub" data-i18n-html="([^"]+)"/) || [])[1];

function lauf(woerterbuchZuerst) {
  return new Promise((fertig) => {
    const el = {}, hoerer = {};
    let dict = woerterbuchZuerst ? EN : null;
    function neu(id) {
      const o = {
        id, _html: '', _attr: {}, value: '', style: {}, dataset: {},
        classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
        appendChild() {}, addEventListener() {}, scrollIntoView() {},
        // Buttons aus dem gesetzten HTML erzeugen, damit die Seite ihre onclick-Handler anhaengen kann
        querySelectorAll(sel) {
          if (sel !== 'button') return [];
          return (o._btns = [...o._html.matchAll(/data-v="([^"]+)"/g)].map((m) => ({ v: m[1], getAttribute: () => m[1] })));
        },
        querySelector() { return null; }, closest() { return null; },
        getAttribute(k) { return k in o._attr ? o._attr[k] : null; },
        setAttribute(k, v) { o._attr[k] = String(v); }, removeAttribute(k) { delete o._attr[k]; }, focus() {}
      };
      Object.defineProperty(o, 'innerHTML', { get() { return this._html; }, set(v) { this._html = String(v); } });
      Object.defineProperty(o, 'innerText', { get() { return this._html.replace(/<[^>]+>/g, ''); } });
      Object.defineProperty(o, 'textContent', { get() { return this._html; }, set(v) { this._html = String(v); } });
      return o;
    }
    const hole = (id) => el[id] || (el[id] = neu(id));
    const sub = hole('sk-quad-sub');
    sub._attr['data-i18n-html'] = STATISCH;
    global.ApexCharts = class { constructor() {} render() {} updateOptions() {} destroy() {} };
    global.document = {
      readyState: 'complete', getElementById: hole, createElement: () => neu('x'),
      querySelectorAll: () => [], querySelector: () => null,
      addEventListener(n, f) { (hoerer[n] = hoerer[n] || []).push(f); }
    };
    const t = (k, de) => (dict && k in dict ? dict[k] : (de === undefined ? k : de));
    global.window = { SA: { i18n: { t, isEN: () => true } }, scrollTo() {}, addEventListener() {}, location: { search: '' } };
    global.SA = global.window.SA;
    global.loadComponent = function () {};
    global.fetch = (u) => {
      const f = DATEN[u.split('?')[0]];
      if (!f) return Promise.resolve({ ok: false, status: 404, json: () => Promise.reject(new Error(u)) });
      const d = JSON.parse(fs.readFileSync(path.join(REPO, 'landing/data', f), 'utf8'));
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(d) });
    };
    const bloecke = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
    eval(bloecke.reduce((a, b) => (b.length > a.length ? b : a)));

    setTimeout(() => {
      const r = { vorher: { legende: hole('sk-quad-legend').innerText, sub: sub.innerText } };
      if (!woerterbuchZuerst) {
        const rank = (hole('sk-mode')._btns || []).find((b) => b.v === 'rank');
        if (rank && rank.onclick) rank.onclick();
        r.rankGeklickt = !!(rank && rank.onclick);
        dict = EN;                                                   // Woerterbuch kommt jetzt
        (hoerer['sa:i18n-bereit'] || []).forEach((f) => f());
      }
      const k = sub.getAttribute('data-i18n-html');                  // _applyDOM aus i18n.js nachstellen
      if (k && k in EN) sub.innerHTML = EN[k];
      r.nachher = { legende: hole('sk-quad-legend').innerText, sub: sub.innerText };
      fertig(r);
    }, 800);
  });
}

(async () => {
  let fehler = 0;
  const pruefe = (b, was) => { console.log((b ? '  ok   ' : '  FEHL ') + was); if (!b) fehler++; };
  pruefe(STATISCH === 'skew.quad_sub_pctl', 'statischer Untertitel = Percentile (' + STATISCH + ')');

  console.log('Woerterbuch vor den Daten (Standard):');
  const a = await lauf(true);
  pruefe(/^How to read/.test(a.nachher.legende), 'Legende englisch: ' + a.nachher.legende.slice(0, 40));
  pruefe(/IV Percentile/.test(a.nachher.legende), 'Legende im Modus Percentile');
  pruefe(/Risk-Reversal Percentile/.test(a.nachher.sub), 'Untertitel englisch, Percentile');

  console.log('Woerterbuch NACH den Daten, vorher auf Rank geschaltet:');
  const b = await lauf(false);
  pruefe(/^Lesart/.test(b.vorher.legende), 'vorher deutscher Fallback (erwartet)');
  pruefe(b.rankGeklickt, 'Rank-Schalter gefunden und betaetigt');
  pruefe(/^How to read/.test(b.nachher.legende), 'Legende danach englisch: ' + b.nachher.legende.slice(0, 40));
  pruefe(/IV Rank/.test(b.nachher.legende), 'Legende bleibt im Modus Rank');
  pruefe(/Risk-Reversal Rank/.test(b.nachher.sub), 'Untertitel englisch und Rank (nicht auf Percentile zurueck): '
    + b.nachher.sub.slice(0, 60));

  console.log('');
  console.log(fehler === 0 ? 'ALLE PRUEFUNGEN BESTANDEN' : fehler + ' FEHLER');
  process.exit(fehler === 0 ? 0 : 1);
})();

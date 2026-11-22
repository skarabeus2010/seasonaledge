// Probe für /event-chart (Wächter: scripts/verify_event_chart.py).
//
//   node probe_event_chart.js rechne <compute.js> <faelle.json>
//       führt SA.eventChart.durchschnitt/achse/idxAb aus dem ECHTEN Rechenkern aus, Ausgabe JSON je Fall
//   node probe_event_chart.js seite <landing-Wurzel> <de|en> <ticker> <fixtures.json>
//       lädt die echte Seite (DE oder gebaute EN) in jsdom, Kurse über einen PostgREST-Nachbau, ApexCharts als
//       Attrappe, die Optionen aufzeichnet; Ausgabe: Seitenfehler, Banner, Charts, KPIs, Liste, nächste Termine
'use strict';
process.env.TZ = process.env.SA_TZ || 'Europe/Berlin';
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const MODUS = process.argv[2];

if (MODUS === 'rechne') {
  const code = fs.readFileSync(process.argv[3], 'utf8');
  const faelle = JSON.parse(fs.readFileSync(process.argv[4], 'utf8'));
  const window = { SA: { __release() {} } };
  vm.runInNewContext(code, { window });
  const E = window.SA.eventChart;
  const aus = faelle.map((f) => {
    try {
      const r = E.durchschnitt(f.daten, f.schluss, f.termine, f.opts);
      const a = E.achse(f.daten, f.bis);
      return { n: r.n, nBasis: r.nBasis, start: r.start, anker: r.anker, mittel: r.mittel, median: r.median, q1: r.q1, q3: r.q3,
               basis: r.basis, achseLaenge: a.length, achseEnde: a[a.length - 1], idx: (f.idx || []).map((d) => E.idxAb(a, d)) };
    } catch (e) { return { fehler: String(e && e.message || e) }; }
  });
  process.stdout.write(JSON.stringify(aus));
  process.exit(0);
}

const { JSDOM, ResourceLoader, VirtualConsole } = require(path.join(__dirname, '..', 'perf', 'node_modules', 'jsdom'));
const [WURZEL, SPRACHE, TICKER, FIXDATEI, WECHSEL] = process.argv.slice(3);   // WECHSEL: danach per Eingabe + Enter
const DATEN = JSON.parse(fs.readFileSync(FIXDATEI, 'utf8'));
const UHR = Date.UTC(2026, 10, 22, 12, 0, 0);

function antwort(status, body) {
  const text = typeof body === 'string' ? body : JSON.stringify(body);
  return { ok: status >= 200 && status < 300, status, statusText: String(status), headers: { get: () => null },
           json: () => Promise.resolve(JSON.parse(text)), text: () => Promise.resolve(text) };
}
function preise(url) {
  const q = url.split('?')[1] || '';
  const p = { gte: null, gt: null, limit: 1000, select: ['date', 'close'], ticker: null };
  for (const teil of q.split('&')) {
    const k = teil.slice(0, teil.indexOf('=')), v = decodeURIComponent(teil.slice(k.length + 1));
    if (k === 'ticker') p.ticker = v.replace(/^eq\./, '');
    else if (k === 'select') p.select = v.split(',');
    else if (k === 'limit') p.limit = +v;
    else if (k === 'date' && v.startsWith('gte.')) p.gte = v.slice(4);
    else if (k === 'date' && v.startsWith('gt.')) p.gt = v.slice(3);
  }
  if (!DATEN[p.ticker]) return antwort(500, { message: 'unbekannt' });
  let z = DATEN[p.ticker].filter((x) => (p.gte === null || x.date >= p.gte) && (p.gt === null || x.date > p.gt)).slice(0, Math.min(p.limit, 1000));
  z = z.map((x) => { const o = {}; for (const f of p.select) o[f] = x[f] === undefined ? null : x[f]; return o; });
  return antwort(200, z);
}
function datei(pfad) {
  const rel = pfad.replace(/\?.*$/, '').replace(/^\/landing\//, '');
  const f = path.join(WURZEL, rel);
  return fs.existsSync(f) ? fs.readFileSync(f, 'utf8') : null;
}
function netz(url) {
  url = String(url);
  return new Promise((res) => setTimeout(res, 2)).then(() => {
    if (url.startsWith('https://stub/rest/v1/prices')) return preise(url);
    if (url.startsWith('https://stub/')) return antwort(200, []);
    const pfad = url.replace(/^https:\/\/seasonalpha\.ai/, '');
    if (pfad.startsWith('/landing/')) { const t = datei(pfad); return t === null ? antwort(404, 'x') : antwort(200, t); }
    return antwort(404, 'x');
  });
}
const APEX = `
window.__charts = [];
window.ApexCharts = function (el, opts) {
  window.__charts.push({ el: (el && el.id) || '?', typ: opts && opts.chart && opts.chart.type,
    punkte: opts && opts.series ? opts.series.map(function (s) { return s.data.length; }) : [],
    annotationen: opts && opts.annotations && opts.annotations.xaxis ? opts.annotations.xaxis.map(function (a) { return [a.x, a.label && a.label.text]; }) : [] });
  this.render = function () { return Promise.resolve(); };
  this.updateSeries = this.updateOptions = function () { return Promise.resolve(); };
  this.destroy = function () {};
};
window.ApexCharts.exec = function () {};`;
class Lader extends ResourceLoader {
  fetch(url) {
    if (/apexcharts/.test(url)) return Promise.resolve(Buffer.from(APEX));
    if (/supabase-js/.test(url)) return Promise.resolve(Buffer.from(''));
    const pfad = url.replace(/^https:\/\/seasonalpha\.ai/, '');
    if (pfad.startsWith('/landing/')) { const t = datei(pfad); if (t !== null) return Promise.resolve(Buffer.from(t)); }
    return Promise.resolve(Buffer.from(''));
  }
}
const EN = SPRACHE === 'en';
const seite = EN ? path.join(WURZEL, 'en', 'event-chart.html') : path.join(WURZEL, 'pages', 'event-chart.html');
const html = fs.readFileSync(seite, 'utf8').replace('%%SUPABASE_URL%%', 'https://stub').replace('%%SUPABASE_ANON_KEY%%', 'k');
const fehler = [];
const vk = new VirtualConsole();
vk.on('jsdomError', (e) => fehler.push(String(e && (e.detail && e.detail.stack || e.stack || e.message) || e).slice(0, 300)));
const dom = new JSDOM(html, {
  url: (EN ? 'https://seasonalpha.ai/en/event-chart' : 'https://seasonalpha.ai/event-chart') + '?t=' + encodeURIComponent(TICKER),
  runScripts: 'dangerously', resources: new Lader(), pretendToBeVisual: true, virtualConsole: vk,
  beforeParse(window) {
    const Echt = window.Date;
    class Uhr extends Echt { constructor(...a) { if (a.length === 0) super(UHR); else super(...a); } static now() { return UHR; } }
    window.Date = Uhr;
    window.fetch = netz;
    window.scrollTo = function () {};
    window.matchMedia = window.matchMedia || function () { return { matches: true, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} }; };
    window.IntersectionObserver = function () { return { observe() {}, unobserve() {}, disconnect() {} }; };
    window.ResizeObserver = function () { return { observe() {}, unobserve() {}, disconnect() {} }; };
  }
});
const W = dom.window;
const txt = (sel) => { const el = W.document.querySelector(sel); return el ? el.textContent.replace(/\s+/g, ' ').trim() : null; };
let warte = 0, gewechselt = !WECHSEL;
(function pruefe() {
  const fertig = W.document.getElementById('loading') && W.document.getElementById('loading').style.display === 'none' && W.__charts && W.__charts.length >= 2 &&
    (gewechselt ? (!WECHSEL || txt('#title-ticker') === WECHSEL) : true);
  if (!fertig && warte++ < 300) { setTimeout(pruefe, 30); return; }
  if (!gewechselt) {
    gewechselt = true;
    const inp = W.document.getElementById('ticker-input');
    inp.value = WECHSEL;
    inp.dispatchEvent(new W.KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    setTimeout(pruefe, 30); return;
  }
  setTimeout(() => {
    const banner = W.document.getElementById('error-banner');
    const liste = [...W.document.querySelectorAll('#ec-liste .ec-ev')].map((l) => ({ kz: l.querySelector('.kz').textContent, an: l.querySelector('input').checked, name: l.querySelector('.name').firstChild.textContent }));
    process.stdout.write(JSON.stringify({
      fehler,
      banner: banner && banner.style.display === 'block' ? banner.textContent : null,
      titel: txt('#title-ticker'), avgTitel: txt('#avg-titel'),
      charts: W.__charts,
      kpis: [...W.document.querySelectorAll('#ec-kpis .ec-kpi')].map((k) => [txt.call(null, null) || '', k.querySelector('.l').textContent, k.querySelector('.v').textContent, k.querySelector('.s').textContent]),
      tabelle: [...W.document.querySelectorAll('#ec-tab tbody tr')].map((r) => r.textContent.replace(/\s+/g, ' ').trim()),
      liste,
      naechste: [...W.document.querySelectorAll('#ec-next li time')].map((t) => t.getAttribute('datetime')),
      seiteText: W.document.querySelector('main').textContent.replace(/\s+/g, ' ').slice(0, 4000)
    }));
    process.exit(0);
  }, 200);
})();

// Bibliotheksprobe (V1b, Codex Code-R1): ändert methode.js den NORMALBETRIEB der echten Bibliotheken? Lädt die
// echte ApexCharts 4.7.0 und das echte supabase-js 2.117.3 (feste Versionen, scripts/perf/package.json) in jsdom —
// einmal ohne, einmal mit methode.js — und gibt die beobachteten Ergebnisse aus; der Wächter verlangt Gleichheit.
// Im Modus `mit` zusätzlich: nach einer Sperre keine Netzanfrage aus supabase-js, render/Konstruktor lehnen ab.
//
// Aufruf: node probe_release_bibliotheken.js <landing-Wurzel> <ohne|mit>  → JSON + PROBE-ENDE
'use strict';
const fs = require('fs');
const path = require('path');
const NM = path.join(__dirname, '..', 'perf', 'node_modules');
const { JSDOM, ResourceLoader, VirtualConsole } = require(path.join(NM, 'jsdom'));

const [WURZEL, MODUS] = process.argv.slice(2);
const MIT = MODUS === 'mit' || MODUS === 'mit_spaet';
const fehlerSeite = [];
process.on('unhandledRejection', (e) => fehlerSeite.push('[unbehandelt] ' + String(e && e.message || e).slice(0, 160)));

const APEX = fs.readFileSync(path.join(NM, 'apexcharts', 'dist', 'apexcharts.min.js'), 'utf8');
const SUPA = fs.readFileSync(path.join(NM, '@supabase', 'supabase-js', 'dist', 'umd', 'supabase.js'), 'utf8');
const METHODE = fs.readFileSync(path.join(WURZEL, 'js', 'methode.js'), 'utf8');

const NETZ = { anfragen: [], nachSperre: 0 };
let W = null;
function netz(url, init) {
  const roh = typeof url === 'string' ? url : (url && url.url) || String(url);
  NETZ.anfragen.push(roh);
  if (W && W.SA && W.SA.__gesperrt) NETZ.nachSperre++;
  const zeilen = [{ date: '2026-10-07', close: 1.5 }, { date: '2026-10-08', close: 2.5 }];
  return new Promise(r => setTimeout(r, 2)).then(() => new Response(JSON.stringify(zeilen),
    { status: 200, headers: { 'content-type': 'application/json', 'content-range': '0-1/*' } }));
}
class Lader extends ResourceLoader {
  fetch(url) {
    if (/apex/.test(url)) return Promise.resolve(Buffer.from(APEX));
    if (/supabase/.test(url)) return Promise.resolve(Buffer.from(SUPA));
    if (/methode\.js/.test(url)) return Promise.resolve(Buffer.from(METHODE));
    return Promise.resolve(Buffer.from(''));
  }
}
const html = '<!doctype html><html lang="de"><head></head><body><div id="c" style="width:400px;height:300px"></div>' +
  "<script>window.__SA_RELEASE='%%RELEASE%%';window.__SA_METHODE='alt';</script>" +
  // mit_spaet: methode.js VOR den Bibliotheken (31 Seiten laden ApexCharts erst danach → Setter-Pfad)
  (MODUS === 'mit_spaet' ? '<script src="https://seasonalpha.ai/landing/js/methode.js"></script>' : '') +
  '<script src="https://cdn.example/apexcharts.min.js"></script>' +
  '<script src="https://cdn.example/supabase.js"></script>' +
  (MODUS === 'mit' ? '<script src="https://seasonalpha.ai/landing/js/methode.js"></script>' : '') +
  '</body></html>';
const vk = new VirtualConsole();
vk.on('jsdomError', (e) => fehlerSeite.push(String(e && (e.detail && e.detail.message || e.message) || e).slice(0, 160)));
const dom = new JSDOM(html, {
  url: 'https://seasonalpha.ai/probe', runScripts: 'dangerously', resources: new Lader(), pretendToBeVisual: true,
  virtualConsole: vk,
  beforeParse(window) {
    W = window;
    window.fetch = netz;
    window.__saNeuladen = () => {};
    // jsdom kennt keine SVG-Messung — gleiche Ersatzwerte in BEIDEN Läufen, verfälscht den Vergleich nicht
    const SP = window.SVGElement.prototype;
    SP.getBBox = function () { return { x: 0, y: 0, width: 40, height: 12 }; };
    SP.getComputedTextLength = function () { return 40; };
    SP.getScreenCTM = function () { return { a: 1, b: 0, c: 0, d: 1, e: 0, f: 0, inverse() { return this; } }; };
    window.ResizeObserver = function () { return { observe() {}, unobserve() {}, disconnect() {} }; };
  }
});
const warte = (ms) => new Promise(r => setTimeout(r, ms));

(async function () {
  await warte(500);
  const aus = { modus: MODUS, normal: {}, sperre: {} };
  if (!W.ApexCharts || !W.supabase || (MIT && !(W.SA && W.SA.__release))) {
    process.stdout.write('[Absturz] Aufbau: Bibliothek oder methode.js nicht geladen ' + fehlerSeite.slice(0, 2).join(' | ') + '\n');
    process.exit(2);
  }
  // supabase-js: Abfrage im Normalbetrieb
  const client = W.supabase.createClient('https://stub.supabase.co', 'k');
  const r = await client.from('prices').select('date,close').eq('ticker', 'SPY').limit(2);
  aus.normal.supabase = { data: r.data, error: r.error ? String(r.error.message || r.error) : null, anfragen: NETZ.anfragen.length };
  // ApexCharts: render, update
  let chartFehler = null, svg = 0, pfade = 0;
  try {
    const ch = new W.ApexCharts(W.document.getElementById('c'), {
      chart: { type: 'line', animations: { enabled: false }, toolbar: { show: false } },
      series: [{ name: 'a', data: [1, 3, 2, 5] }], xaxis: { categories: ['w', 'x', 'y', 'z'] } });
    await ch.render();
    await ch.updateSeries([{ name: 'a', data: [2, 2, 4, 1] }]);
    svg = W.document.querySelectorAll('#c svg').length;
    pfade = W.document.querySelectorAll('#c path').length;
    aus.normal.chartStatic = typeof W.ApexCharts.exec === 'function' && typeof W.ApexCharts.getChartByID === 'function';
    W.__chart = ch;
  } catch (e) { chartFehler = String(e && e.message || e).slice(0, 120); }
  aus.normal.chart = { fehler: chartFehler, svg, pfade };
  if (MIT) {
    W.SA.__sperre('Probe');
    const n0 = NETZ.anfragen.length;
    const r2 = await client.from('prices').select('date,close').eq('ticker', 'QQQ').limit(2).then(x => x, e => ({ data: null, error: e }));
    aus.sperre.supabaseAnfragen = NETZ.anfragen.length - n0;
    aus.sperre.supabaseDaten = r2.data;
    let renderFehler = null;
    try { await W.__chart.render(); } catch (e) { renderFehler = e && e.name; }
    aus.sperre.renderFehler = renderFehler;
    let neuFehler = null;
    try { new W.ApexCharts(W.document.createElement('div'), { series: [] }); } catch (e) { neuFehler = e && e.name; }
    aus.sperre.neuFehler = neuFehler;
    aus.sperre.nachSperre = NETZ.nachSperre;
  }
  aus.seitenfehler = fehlerSeite.slice(0, 3);
  process.stdout.write(JSON.stringify(aus) + '\nPROBE-ENDE\n');
  process.exit(0);
})().catch(e => { process.stdout.write('[Absturz] ' + (e && e.stack) + '\n'); process.exit(2); });

// Seitenprobe Header (Kalender V2): lädt die ECHTE Seite mit ihren echten Skripten in jsdom, feste Uhr, und liest
// #trading-day-header. Optional Tickerwechsel A→B→A über #ticker-input.
//
//   node scripts/js/probe_header_seiten.js <repo-Wurzel> <seite> <methode> <uhr_iso> [A,B,A]
//   seite 'converter': seo/tools/trading-day-converter.html (wie nginx /tools/ ausliefert); dann ist die Folge
//   eine Liste "Datum|Börse" und gelesen wird #result.
//
// methode 'kalender_v1': methode.js und die Seitenkennung werden in der Probe auf kalender_v1 gestellt (sonst
// sperrt die Seite, V1b). Kurse: deterministische Mo–Fr-Zeilen für jeden Ticker (die Kalenderanzeige hängt nicht an
// Kurswerten). Ausgabe: {"header": [nach Start, nach A, nach B, nach A …], "fehler": [...]}.
'use strict';
const fs = require('fs');
const path = require('path');
const { JSDOM, ResourceLoader, VirtualConsole } = require(path.join(__dirname, '..', 'perf', 'node_modules', 'jsdom'));

const [WURZEL, SEITE, METHODE, UHR_ISO, WECHSEL] = process.argv.slice(2);
const UHR = Date.parse(UHR_ISO);
const folge = WECHSEL ? WECHSEL.split(',') : [];

function kurse(ticker) {
  let s = 7;
  for (const c of ticker) s = (s * 31 + c.charCodeAt(0)) >>> 0;
  const aus = [];
  let close = 100, t = Date.UTC(2015, 0, 1);
  const ende = UHR - 86400000;
  while (t <= ende) {
    const d = new Date(t);
    if (d.getUTCDay() !== 0 && d.getUTCDay() !== 6) {
      s = (s * 1664525 + 1013904223) >>> 0;
      const neu = Math.round(close * Math.exp((s / 4294967296 - 0.48) * 0.03) * 100) / 100;
      aus.push({ date: d.toISOString().slice(0, 10), open: close, high: Math.max(close, neu) + 0.5,
                 low: Math.min(close, neu) - 0.5, close: neu, log_return: aus.length ? Math.log(neu / close) : null,
                 tdom: null, tdoy: null, volume: 1000 });
      close = neu;
    }
    t += 86400000;
  }
  return aus;
}
const CACHE = {};
function antwort(status, body, kopf) {
  const text = typeof body === 'string' ? body : JSON.stringify(body);
  return { ok: status >= 200 && status < 300, status, statusText: String(status),
           headers: { get: (n) => (kopf || {})[n.toLowerCase()] ?? null },
           json: () => Promise.resolve(JSON.parse(text)), text: () => Promise.resolve(text) };
}
function preise(url, init) {
  const h = (init && init.headers) || {};
  const q = url.split('?')[1] || '';
  const p = { gte: null, gt: null, lte: null, limit: null, select: null, ticker: null };
  for (const teil of q.split('&')) {
    const k = teil.slice(0, teil.indexOf('='));
    const v = decodeURIComponent(teil.slice(k.length + 1));
    if (k === 'ticker') p.ticker = v.replace(/^eq\./, '');
    else if (k === 'select') p.select = v.split(',');
    else if (k === 'limit') p.limit = +v;
    else if (k === 'date' && v.startsWith('gte.')) p.gte = v.slice(4);
    else if (k === 'date' && v.startsWith('gt.')) p.gt = v.slice(3);
    else if (k === 'date' && v.startsWith('lte.')) p.lte = v.slice(4);
  }
  const alle = CACHE[p.ticker] || (CACHE[p.ticker] = kurse(p.ticker || 'X'));
  let z = alle.filter(x => (p.gte === null || x.date >= p.gte) && (p.gt === null || x.date > p.gt) &&
                           (p.lte === null || x.date <= p.lte));
  const gesamt = z.length;
  let von = 0;
  if (h.Range) { const [a, b] = h.Range.split('-').map(Number); von = a; z = z.slice(a, b + 1); }
  z = z.slice(0, Math.min(p.limit || 1000, 1000));
  const sel = p.select || ['date', 'close'];
  z = z.map(x => { const o = {}; for (const f of sel) o[f] = x[f] === undefined ? null : x[f]; return o; });
  const cr = (z.length ? von + '-' + (von + z.length - 1) : '*') + '/' + (h.Prefer === 'count=exact' ? gesamt : '*');
  return antwort(200, z, { 'content-range': cr });
}
function datei(pfad) {
  const rel = pfad.replace(/\?.*$/, '').replace(/^\/landing\//, '');
  const f = path.join(WURZEL, 'landing', rel);
  if (!fs.existsSync(f)) return null;
  let t = fs.readFileSync(f, 'utf8');
  if (METHODE === 'kalender_v1' && rel === 'js/methode.js') t = t.replace("var METHODE = 'alt';", "var METHODE = 'kalender_v1';");
  return t;
}
let OFFEN = 0, LETZTE = Date.now();
function netz(url, init) {
  url = String(url);
  OFFEN++; LETZTE = Date.now();
  const fertig = (x) => { OFFEN--; LETZTE = Date.now(); return x; };
  return new Promise(res => setTimeout(res, 2)).then(() => {
    if (url.startsWith('https://stub/rest/v1/prices')) return preise(url, init);
    if (url.startsWith('https://stub/')) return antwort(200, []);
    const pfad = url.replace(/^https:\/\/seasonalpha\.ai/, '');
    if (pfad.startsWith('/landing/')) { const t = datei(pfad); return t === null ? antwort(404, '') : antwort(200, t); }
    return antwort(404, '');
  }).then(fertig, (e) => { fertig(); throw e; });
}
const APEX = `window.ApexCharts = function () { this.render = function () { return Promise.resolve(); };
  this.updateSeries = this.updateOptions = function () { return Promise.resolve(); }; this.destroy = function () {};
  this.toggleSeries = this.showSeries = this.hideSeries = function () {}; }; window.ApexCharts.exec = function () {};`;
class Lader extends ResourceLoader {
  fetch(url) {
    if (/apexcharts/.test(url)) return Promise.resolve(Buffer.from(APEX));
    if (/supabase-js/.test(url)) return Promise.resolve(Buffer.from(''));
    const pfad = url.replace(/^https:\/\/seasonalpha\.ai/, '');
    if (pfad.startsWith('/landing/')) { const t = datei(pfad); if (t !== null) return Promise.resolve(Buffer.from(t)); }
    return Promise.resolve(Buffer.from(''));
  }
}
const KONV = SEITE === 'converter';
let html = fs.readFileSync(path.join(WURZEL, KONV ? 'seo/tools/trading-day-converter.html' : 'landing/pages/' + SEITE + '.html'), 'utf8')
  .replace('%%SUPABASE_URL%%', 'https://stub').replace('%%SUPABASE_ANON_KEY%%', 'k');
if (METHODE === 'kalender_v1') html = html.replace("window.__SA_METHODE='alt'", "window.__SA_METHODE='kalender_v1'");
const fehler = [];
const vk = new VirtualConsole();
vk.on('jsdomError', (e) => fehler.push(String(e && (e.detail && e.detail.stack || e.stack || e.message) || e).slice(0, 300)));
const dom = new JSDOM(html, {
  url: 'https://seasonalpha.ai/' + (KONV ? 'tools/trading-day-converter' : SEITE), runScripts: 'dangerously', resources: new Lader(), pretendToBeVisual: true,
  virtualConsole: vk,
  beforeParse(window) {
    const Echt = window.Date;
    class Uhr extends Echt {
      constructor(...a) { if (a.length === 0) super(UHR); else super(...a); }
      static now() { return UHR; }
    }
    window.Date = Uhr;
    window.fetch = netz;
    window.scrollTo = function () {};
    // jsdom ohne canvas-Paket: ein Zeichenkontext, der jede Methode annimmt (die Seite zeichnet, wir lesen nur den Header)
    const leer = new Proxy(function () {}, { get: (z, k) => (k === 'canvas' ? null : leer), apply: () => leer, set: () => true });
    window.HTMLCanvasElement.prototype.getContext = function () { return leer; };
    window.matchMedia = function () { return { matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} }; };
    window.IntersectionObserver = function () { return { observe() {}, unobserve() {}, disconnect() {} }; };
    window.ResizeObserver = function () { return { observe() {}, unobserve() {}, disconnect() {} }; };
  }
});
const W = dom.window;
const header = () => { const e = W.document.getElementById(KONV ? 'result' : 'trading-day-header'); return e ? (KONV ? e.innerHTML : e.textContent) : null; };
function ruhe(maxMs) {
  return new Promise((ok) => {
    const start = Date.now();
    (function blick() {
      if ((OFFEN === 0 && Date.now() - LETZTE > 1200) || Date.now() - start > maxMs) return ok();
      setTimeout(blick, 100);
    })();
  });
}
(async function () {
  await ruhe(30000);
  const aus = [header()];
  for (const t of folge) {
    if (KONV) {
      const [ds, b] = t.split('|');
      const wahl = W.document.getElementById('boerse');
      if (b && wahl) { wahl.value = b; wahl.dispatchEvent(new W.Event('change')); }
      const dp = W.document.getElementById('datepicker');
      dp.value = ds; dp.dispatchEvent(new W.Event('change'));
      aus.push(header());
      continue;
    }
    const inp = W.document.getElementById('ticker-input');
    if (!inp) { aus.push('kein #ticker-input'); break; }
    inp.value = t;
    inp.dispatchEvent(new W.KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    await ruhe(30000);
    // Die Seiten rendern gestaffelt (setTimeout): warten, bis der neue Ticker im Header steht (höchstens 20 s)
    for (let i = 0; i < 200 && (header() || '').indexOf(' ' + t + ' ') < 0; i++) await new Promise(r => setTimeout(r, 100));
    aus.push(header());
  }
  process.stdout.write(JSON.stringify({ header: aus, fehler }), () => process.exit(0));
})().catch(e => process.stdout.write(JSON.stringify({ absturz: String(e && e.stack || e) }), () => process.exit(0)));

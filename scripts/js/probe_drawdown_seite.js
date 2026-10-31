// Seitenprobe /drawdown (Bauplan docs/review_prompts/2026-10-31_drawdown_seite_plan_v3.md, Wächter
// scripts/verify_drawdown.py): lädt die ECHTE Seite (DE oder gebaute EN) mit ihren echten Skripten in jsdom, liefert
// Kurse über einen PostgREST-Nachbau aus eingefrorenen Reihen und zeichnet sichtbaren Text, Kacheln, Chartserien
// und Kursanfragen auf.
//
// Aufruf: node probe_drawdown_seite.js <landing-Wurzel> <fall> <fixtures-json>
//   fixtures-json: {TICKER: [{date, close, log_return}, ...], ...}
//   fall: normal | hoch | kurz | luecke | fehler | fehler_nach_erfolg | wechsel | en
// Feste Uhr 2026-10-31 12:00 UTC (E = 30.10.2026 für NYSE), Zone Europe/Berlin.
'use strict';
process.env.TZ = process.env.SA_TZ || 'Europe/Berlin';
const fs = require('fs');
const path = require('path');
const { JSDOM, ResourceLoader, VirtualConsole } = require(path.join(__dirname, '..', 'perf', 'node_modules', 'jsdom'));

const [WURZEL, FALL, FIXDATEI] = process.argv.slice(2);
const DATEN = JSON.parse(fs.readFileSync(FIXDATEI, 'utf8'));
const UHR = Date.UTC(2026, 9, 31, 12, 0, 0);
const ANFRAGEN = [];
const LANGSAM = {};
let FEHLER = {};                              // Ticker → true: Kursabfrage scheitert (HTTP 500)

function antwort(status, body, kopf) {
  const text = typeof body === 'string' ? body : JSON.stringify(body);
  return { ok: status >= 200 && status < 300, status, statusText: String(status),
           headers: { get: (n) => (kopf || {})[n.toLowerCase()] ?? null },
           json: () => Promise.resolve(JSON.parse(text)), text: () => Promise.resolve(text) };
}
function preise(url, init) {
  const h = (init && init.headers) || {};
  const q = url.split('?')[1] || '';
  const p = { gte: null, gt: null, limit: null, select: null, ticker: null };
  for (const teil of q.split('&')) {
    const k = teil.slice(0, teil.indexOf('='));
    const v = decodeURIComponent(teil.slice(k.length + 1));
    if (k === 'ticker') p.ticker = v.replace(/^eq\./, '');
    else if (k === 'select') p.select = v.split(',');
    else if (k === 'limit') p.limit = +v;
    else if (k === 'date' && v.startsWith('gte.')) p.gte = v.slice(4);
    else if (k === 'date' && v.startsWith('gt.')) p.gt = v.slice(3);
  }
  ANFRAGEN.push(decodeURIComponent(url.replace(/^https:\/\/stub/, '')));
  if (FEHLER[p.ticker]) return antwort(500, { message: 'statement timeout' });
  let z = (DATEN[p.ticker] || []).filter(x => (p.gte === null || x.date >= p.gte) && (p.gt === null || x.date > p.gt));
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
  const f = path.join(WURZEL, rel);
  return fs.existsSync(f) ? fs.readFileSync(f, 'utf8') : null;
}
let OFFEN = 0, LETZTE = Date.now();
function netz(url, init) {
  url = String(url);
  const tm = /ticker=eq\.([^&]+)/.exec(url);
  const extra = tm ? (LANGSAM[decodeURIComponent(tm[1])] || 0) : 0;
  OFFEN++; LETZTE = Date.now();
  const fertig = (x) => { OFFEN--; LETZTE = Date.now(); return x; };
  return new Promise(res => setTimeout(res, 2 + extra)).then(() => {
    if (url.startsWith('https://stub/rest/v1/prices')) return preise(url, init);
    if (url.startsWith('https://stub/')) return antwort(200, []);
    const pfad = url.replace(/^https:\/\/seasonalpha\.ai/, '');
    if (pfad.startsWith('/landing/')) { const t = datei(pfad); return t === null ? antwort(404, 'x') : antwort(200, t); }
    return antwort(404, 'x');
  }).then(fertig, (e) => { fertig(); throw e; });
}
const APEX = `
window.__charts = [];
window.ApexCharts = function (el, opts) {
  var id = (el && el.id) || '?';
  window.__charts.push({ el: id, series: JSON.stringify(opts && opts.series), annotations: JSON.stringify(opts && opts.annotations || null) });
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

const EN = FALL === 'en';
const seite = EN ? path.join(WURZEL, 'en', 'drawdown.html') : path.join(WURZEL, 'pages', 'drawdown.html');
const START = { normal: 'QQQ', hoch: 'HOCH', kurz: 'KURZ', luecke: 'LUECKE', fehler: 'QQQ', fehler_nach_erfolg: 'QQQ', wechsel: 'QQQ', en: 'QQQ',
                kurz_nach_erfolg: 'QQQ', n0: 'N0', n1: 'N1', schwelle: 'S5', null: 'NULL' }[FALL];
if (FALL === 'fehler') FEHLER.QQQ = true;
const html = fs.readFileSync(seite, 'utf8').replace('%%SUPABASE_URL%%', 'https://stub').replace('%%SUPABASE_ANON_KEY%%', 'k');
const fehlerSeite = [];
const vk = new VirtualConsole();
vk.on('jsdomError', (e) => fehlerSeite.push(String(e && (e.detail && e.detail.stack || e.stack || e.message) || e).slice(0, 300)));
const dom = new JSDOM(html, {
  url: (EN ? 'https://seasonalpha.ai/en/drawdown' : 'https://seasonalpha.ai/drawdown') + '?t=' + encodeURIComponent(START),
  runScripts: 'dangerously', resources: new Lader(), pretendToBeVisual: true, virtualConsole: vk,
  beforeParse(window) {
    const Echt = window.Date;
    class Uhr extends Echt { constructor(...a) { if (a.length === 0) super(UHR); else super(...a); } static now() { return UHR; } }
    window.Date = Uhr;
    window.fetch = netz;
    window.scrollTo = function () {};
    window.matchMedia = window.matchMedia || function () { return { matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} }; };
    window.IntersectionObserver = function () { return { observe() {}, unobserve() {}, disconnect() {} }; };
    window.ResizeObserver = function () { return { observe() {}, unobserve() {}, disconnect() {} }; };
  }
});
const W = dom.window;
const text = (id) => { const el = W.document.getElementById(id); return el ? el.textContent.replace(/\s+/g, ' ').trim() : null; };
function kurseAktiv() {
  const K = W.SA && W.SA.kurse && W.SA.kurse._intern;
  if (!K) return false;
  const ko = K.koordinatoren();
  return K.aktiv() > 0 || (K.eigene && K.eigene() > 0) || Object.keys(ko).some(t => ko[t].laufend || ko[t].wartend);
}
function warteRuhe(maxMs) {
  return new Promise((ok) => {
    const start = Date.now(); let n = -1, seit = Date.now();
    (function blick() {
      const ladend = OFFEN > 0 || kurseAktiv();
      if (ANFRAGEN.length !== n) { n = ANFRAGEN.length; seit = Date.now(); }
      seit = Math.max(seit, LETZTE);
      if ((!ladend && Date.now() - seit > 1200) || Date.now() - start > maxMs) return ok(Date.now() - start < maxMs);
      setTimeout(blick, 100);
    })();
  });
}
function tickerWahl(t) {
  const inp = W.document.getElementById('ticker-input');
  inp.value = t;
  inp.dispatchEvent(new W.KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
}
function zustand() {
  return {
    titel: text('title-ticker'), status_dd: text('s-dd'), peak: text('s-peak'), dauer: text('s-dauer'), trough: text('s-trough'),
    e: text('s-e'), antwort: text('dd-antwort'), hinweis: text('dd-hinweis'), kacheln: text('dd-kacheln'),
    fehler: (W.document.getElementById('error-banner') || {}).style ? W.document.getElementById('error-banner').style.display !== 'none' && text('error-banner') : null,
    tabelle_zeilen: W.document.querySelectorAll('#tab-ep tbody tr').length, fr_zeilen: W.document.querySelectorAll('#tab-fr tbody tr').length,
    fr: text('tab-fr'), fr_neg: Array.from(W.document.querySelectorAll('#tab-fr td.neg')).filter(function (t) { return t.textContent.trim() !== '–'; }).length, tabelle: text('tab-ep'), grenz: text('t-grenz'),
    charts: (W.__charts || []).map(c => ({ el: c.el, series: c.series, annotations: c.annotations }))
  };
}

(async function () {
  let ruhig = await warteRuhe(60000);
  const aus = { fall: FALL };
  if (FALL === 'fehler_nach_erfolg') {
    aus.vorher = zustand();
    FEHLER.SPY = true;
    tickerWahl('SPY');
    ruhig = (await warteRuhe(60000)) && ruhig;
  }
  if (FALL === 'kurz_nach_erfolg') {
    aus.vorher = zustand();
    tickerWahl('KURZ');
    ruhig = (await warteRuhe(60000)) && ruhig;
  }
  if (FALL === 'wechsel') {
    LANGSAM.HOCH = 1500;
    tickerWahl('HOCH');
    await new Promise(r => setTimeout(r, 30));
    tickerWahl('LUECKE');
    ruhig = (await warteRuhe(60000)) && ruhig;
    await new Promise(r => setTimeout(r, 2000));
    ruhig = (await warteRuhe(60000)) && ruhig;
  }
  Object.assign(aus, zustand(), { ruhig, kursanfragen: ANFRAGEN, seitenfehler: fehlerSeite, ende: true });
  process.stdout.write(JSON.stringify(aus), () => process.exit(0));
})().catch(e => process.stdout.write(JSON.stringify({ absturz: String(e && e.stack || e) }), () => process.exit(0)));

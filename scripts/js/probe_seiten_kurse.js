// Seitenprobe (docs/TICKER_LADEN.md, Abnahme A4): lädt die ECHTE Seite mit ihren echten Skripten in jsdom und
// zeichnet auf, was sie anzeigt — sichtbarer Text des Inhaltsbereichs und alle an die Charts übergebenen Serien —
// sowie jede Kursanfrage. Der Wächter (scripts/verify_seiten_kurse.py) fährt dieselbe Probe einmal gegen den Stand
// VOR der Umstellung und einmal gegen den Arbeitsbaum und verlangt gleiche Anzeige.
//
// Aufruf: node probe_seiten_kurse.js <landing-Wurzel> <seite> <fall> [--ohne-obergrenze]
//   fall: normal | vollfehler | ttl | blockfehler
//   --ohne-obergrenze: der Nachbau liefert eine Abfrage OHNE Range/limit vollständig statt nach 1000 Zeilen
//   abzuschneiden — so rechnet der ALTE Code auf vollständigen Daten (Soll für die Overnight-Korrektur).
// Feste Uhr (2026-10-09 14:00 UTC, Zone Europe/Berlin), leerer Speicher, deterministische Kurse.
'use strict';
process.env.TZ = 'Europe/Berlin';
const fs = require('fs');
const path = require('path');
const { JSDOM, ResourceLoader, VirtualConsole } = require(path.join(__dirname, '..', 'perf', 'node_modules', 'jsdom'));

const [WURZEL, SEITE, FALL] = process.argv.slice(2);
const OHNE_OBERGRENZE = process.argv.includes('--ohne-obergrenze');
const UHR_START = Date.UTC(2026, 9, 9, 14, 0, 0);
let uhrVersatz = 0;

// ── deterministische Kurse (Mo–Fr), wie PostgREST sie liefert ──────────────────────────────────────────────────
function kurse(ticker, startJahr) {
  let s = 0;
  for (const c of ticker) s = (s * 31 + c.charCodeAt(0)) >>> 0;
  const zufall = () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
  const aus = [];
  let t = Date.UTC(startJahr, 0, 1), close = 100, mon = -1, tdom = 0, jahr = -1, tdoy = 0;
  const ende = Date.UTC(2026, 9, 8);
  while (t <= ende) {
    const d = new Date(t);
    if (d.getUTCDay() !== 0 && d.getUTCDay() !== 6) {
      if (d.getUTCFullYear() !== jahr) { jahr = d.getUTCFullYear(); tdoy = 0; }
      if (d.getUTCMonth() !== mon) { mon = d.getUTCMonth(); tdom = 0; }
      tdom++; tdoy++;
      const r = (zufall() - 0.48) * 0.03;
      const neu = Math.round(close * Math.exp(r) * 100) / 100;
      const open = Math.round(close * (1 + (zufall() - 0.5) * 0.006) * 100) / 100;
      aus.push({ date: d.toISOString().slice(0, 10), open, high: Math.max(open, neu) + 0.5, low: Math.min(open, neu) - 0.5,
                 close: neu, log_return: aus.length ? Math.log(neu / close) : null, tdom, tdoy });
      close = neu;
    }
    t += 86400000;
  }
  return aus;
}
const DATEN = {};
function daten(t) { return DATEN[t] || (DATEN[t] = kurse(t, t === 'SPY' ? 1993 : 1960)); }

// ── Netz: PostgREST-Nachbau (Range + count=exact UND Keyset) + statische Dateien aus der Wurzel ─────────────────
const ANFRAGEN = [];
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
  ANFRAGEN.push({ url: decodeURIComponent(url.replace(/^https:\/\/stub/, '')), range: h.Range || null, prefer: h.Prefer || null,
                  t: Date.now() });
  // Fall „vollfehler": jede Abfrage der GANZEN Historie (ohne Untergrenze) scheitert serverseitig
  if (FEHLER_VOLL && p.gte === null) return antwort(500, { message: 'statement timeout' });
  // Fall „blockfehler": jeder zweite und spätere Block einer Ladung scheitert dauerhaft
  if (FALL === 'blockfehler' && (p.gt !== null || (h.Range && !/^0-/.test(h.Range)))) return antwort(500, { message: 'Fehler im Block' });
  let z = daten(p.ticker).filter(x => (p.gte === null || x.date >= p.gte) && (p.gt === null || x.date > p.gt) &&
                                              (p.lte === null || x.date <= p.lte));
  const gesamt = z.length;
  let von = 0;
  if (h.Range) { const [a, b] = h.Range.split('-').map(Number); von = a; z = z.slice(a, b + 1); }
  if (!(OHNE_OBERGRENZE && !h.Range && !p.limit)) z = z.slice(0, Math.min(p.limit || 1000, 1000));
  const sel = p.select || ['date', 'close'];
  z = z.map(x => { const o = {}; for (const f of sel) o[f] = x[f] === undefined ? null : x[f]; return o; });
  const cr = (z.length ? von + '-' + (von + z.length - 1) : '*') + '/' + (h.Prefer === 'count=exact' ? gesamt : '*');
  return antwort(200, z, { 'content-range': cr });
}
let FEHLER_VOLL = FALL === 'vollfehler';
function datei(pfad) {
  const rel = pfad.replace(/\?.*$/, '').replace(/^\/landing\//, '');
  const f = path.join(WURZEL, rel);
  return fs.existsSync(f) ? fs.readFileSync(f, 'utf8') : null;
}
let OFFEN = 0, LETZTE = Date.now();
function netz(url, init) {
  url = String(url);
  OFFEN++; LETZTE = Date.now();
  const fertig = (x) => { OFFEN--; LETZTE = Date.now(); return x; };
  return new Promise(res => setTimeout(res, 2)).then(() => {
    if (url.startsWith('https://stub/rest/v1/prices')) return preise(url, init);
    if (url.startsWith('https://stub/')) return antwort(200, []);        // übrige Tabellen: leer
    const pfad = url.replace(/^https:\/\/seasonalpha\.ai/, '');
    if (pfad.startsWith('/landing/')) {
      const t = datei(pfad);
      return t === null ? antwort(404, 'nicht gefunden') : antwort(200, t);
    }
    return antwort(404, 'nicht gefunden');
  }).then(fertig, (e) => { fertig(); throw e; });
}

// ── Skripte: eigene aus der Wurzel, ApexCharts als aufzeichnender Stub, Supabase-SDK leer ──────────────────────
const APEX = `
window.__charts = [];
window.ApexCharts = function (el, opts) {
  var id = (el && el.id) || (el && el.parentNode && el.parentNode.id) || '?';
  var eintrag = { el: id, series: JSON.stringify(opts && opts.series), updates: [] };
  window.__charts.push(eintrag);
  this.render = function () { return Promise.resolve(); };
  this.updateSeries = function (s) { eintrag.updates.push(JSON.stringify(s)); return Promise.resolve(); };
  this.updateOptions = function (o) { if (o && o.series) eintrag.updates.push(JSON.stringify(o.series)); return Promise.resolve(); };
  this.destroy = function () {};
  this.toggleSeries = this.showSeries = this.hideSeries = function () {};
};
window.ApexCharts.exec = function () {};
`;
class Lader extends ResourceLoader {
  fetch(url) {
    if (/apexcharts/.test(url)) return Promise.resolve(Buffer.from(APEX));
    if (/supabase-js/.test(url)) return Promise.resolve(Buffer.from(''));
    const pfad = url.replace(/^https:\/\/seasonalpha\.ai/, '');
    if (pfad.startsWith('/landing/')) {
      const t = datei(pfad);
      if (t !== null) return Promise.resolve(Buffer.from(t));
    }
    return Promise.resolve(Buffer.from(''));
  }
}

const SEITEN = {
  dashboard: { datei: 'pages/dashboard.html', adresse: 'https://seasonalpha.ai/dashboard' },
  jahreszyklus: { datei: 'pages/jahreszyklus.html', adresse: 'https://seasonalpha.ai/jahreszyklus' },
  'ki-saisonalitaet': { datei: 'pages/ki-saisonalitaet.html', adresse: 'https://seasonalpha.ai/ki-saisonalitaet' },
  risikozyklus: { datei: 'pages/risikozyklus.html', adresse: 'https://seasonalpha.ai/risikozyklus' },
  overnight: { datei: 'pages/overnight.html', adresse: 'https://seasonalpha.ai/overnight' },
  'tdom-analyse': { datei: 'pages/tdom-analyse.html', adresse: 'https://seasonalpha.ai/tdom-analyse' },
  wochentage: { datei: 'pages/wochentage.html', adresse: 'https://seasonalpha.ai/wochentage' },
  'backtest-engine': { datei: 'pages/backtest-engine.html', adresse: 'https://seasonalpha.ai/backtest-engine' },
  opex: { datei: 'pages/opex.html', adresse: 'https://seasonalpha.ai/opex' },
  vixpiration: { datei: 'pages/vixpiration.html', adresse: 'https://seasonalpha.ai/vixpiration' },
  'spot-vol-beta': { datei: 'pages/spot-vol-beta.html', adresse: 'https://seasonalpha.ai/spot-vol-beta' },
  embed: { datei: 'embed.html', adresse: 'https://seasonalpha.ai/embed?ticker=SPY&years=15' }
};
const S = SEITEN[SEITE];
if (!S) { process.stdout.write(JSON.stringify({ absturz: 'unbekannte Seite ' + SEITE })); process.exit(0); }
let html = fs.readFileSync(path.join(WURZEL, S.datei), 'utf8')
  .replace('%%SUPABASE_URL%%', 'https://stub').replace('%%SUPABASE_ANON_KEY%%', 'k');

const fehlerSeite = [];
const vk = new VirtualConsole();
vk.on('jsdomError', (e) => fehlerSeite.push(String(e && (e.detail && e.detail.stack || e.stack || e.message) || e).slice(0, 300)));
const dom = new JSDOM(html, {
  url: S.adresse, runScripts: 'dangerously', resources: new Lader(), pretendToBeVisual: true, virtualConsole: vk,
  beforeParse(window) {
    const Echt = window.Date;
    class Uhr extends Echt {
      constructor(...a) { if (a.length === 0) super(UHR_START + uhrVersatz); else super(...a); }
      static now() { return UHR_START + uhrVersatz; }
    }
    window.Date = Uhr;
    window.fetch = netz;
    window.scrollTo = function () {};
    window.matchMedia = window.matchMedia || function () { return { matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} }; };
    window.IntersectionObserver = function () { return { observe() {}, unobserve() {}, disconnect() {} }; };
    window.ResizeObserver = function () { return { observe() {}, unobserve() {}, disconnect() {} }; };
  }
});
const W = dom.window;

function inhaltText() {
  const b = W.document.body.cloneNode(true);
  ['nav-container', 'footer-container'].forEach(id => { const e = b.querySelector('#' + id); if (e) e.remove(); });
  b.querySelectorAll('script,style').forEach(e => e.remove());
  return b.textContent.replace(/\s+/g, ' ').trim();
}
function text(id) {
  const el = W.document.getElementById(id);
  return el ? el.textContent.replace(/\s+/g, ' ').trim() : null;
}
// Der neue Lader wartet zwischen Wiederholungen ohne offene Anfrage (bis ~1,7 s) — das ist keine Ruhe.
function kurseAktiv() {
  const K = W.SA && W.SA.kurse && W.SA.kurse._intern;
  if (!K) return false;
  const ko = K.koordinatoren();
  return K.aktiv() > 0 || (K.eigene && K.eigene() > 0) || Object.keys(ko).some(t => ko[t].laufend || ko[t].wartend);
}
function warteRuhe(maxMs) {
  // fertig, wenn 1,5 s lang keine Kursanfrage mehr kam und keine Ladeanzeige mehr im Inhalt steht
  return new Promise((ok) => {
    const start = Date.now(); let n = -1, seit = Date.now();
    (function blick() {
      // genau die Platzhalter der Seite („Wird berechnet …"), nicht Wörter wie „Ladefehler" im Fehlertext
      const ladend = /Wird berechnet|Calculating/.test(text('anomaly-content') || '') ||
                     /Wird berechnet|Calculating/.test(text('ki-content') || '') || OFFEN > 0 || kurseAktiv();
      if (ANFRAGEN.length !== n) { n = ANFRAGEN.length; seit = Date.now(); }
      seit = Math.max(seit, LETZTE);
      if ((!ladend && Date.now() - seit > 1500) || Date.now() - start > maxMs) return ok(Date.now() - start < maxMs);
      setTimeout(blick, 100);
    })();
  });
}

(async function () {
  let ruhig = await warteRuhe(40000);
  const ersteAnfragen = ANFRAGEN.length;
  if (FALL === 'ttl') {
    // 16 Minuten später, die ganze Historie scheitert jetzt; der Zeitraum-Regler zeichnet neu (Score + Radar laden nach)
    uhrVersatz = 16 * 60 * 1000;
    FEHLER_VOLL = true;
    const sel = W.document.getElementById('sel-years');
    sel.dispatchEvent(new W.Event('change'));
    ruhig = (await warteRuhe(40000)) && ruhig;
  }
  const inhalt = inhaltText();
  const aus = {
    seite: SEITE, fall: FALL, ruhig,
    inhalt,
    charts: W.__charts || [],
    kursanfragen: ANFRAGEN.map(a => a.url + (a.range ? ' [Range ' + a.range + ']' : '') + (a.prefer ? ' [' + a.prefer + ']' : '')),
    erste_phase_anfragen: ersteAnfragen,
    seitenfehler: fehlerSeite,
    ende: true
  };
  process.stdout.write(JSON.stringify(aus), () => process.exit(0));
})().catch(e => process.stdout.write(JSON.stringify({ absturz: String(e && e.stack || e) }), () => process.exit(0)));

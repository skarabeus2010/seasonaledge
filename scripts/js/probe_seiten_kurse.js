// Seitenprobe (docs/TICKER_LADEN.md, Abnahme A4): lädt die ECHTE Seite mit ihren echten Skripten in jsdom und
// zeichnet auf, was sie anzeigt — sichtbarer Text des Inhaltsbereichs und alle an die Charts übergebenen Serien —
// sowie jede Kursanfrage. Der Wächter (scripts/verify_seiten_kurse.py) fährt dieselbe Probe einmal gegen den Stand
// VOR der Umstellung und einmal gegen den Arbeitsbaum und verlangt gleiche Anzeige.
//
// Aufruf: node probe_seiten_kurse.js <landing-Wurzel> <seite> <fall> [--ohne-obergrenze]
//   fall: normal | vollfehler | ttl | blockfehler | wechsel | direkt
//   wechsel: nach dem Start Ticker A wählen (antwortet langsam), sofort danach B — die Anzeige muss B zeigen.
//   direkt:  nach dem Start nur B wählen (Soll für „wechsel").
//   rueckwechsel: A (langsam), sofort zurück zum Start-Ticker — Soll: „normal".
//   zeitraum / zeitraum_direkt (Dashboard): 16 min später scheitert jede Abfrage der ganzen Historie und der
//   30 Jahre (langsam); Zeitraum 30 → sofort 5 Jahre, bzw. nur 5 — beide müssen gleich enden.
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
function daten(t) {
  if (DATEN[t]) return DATEN[t];
  // LUECKE (True Seasonal): ab 2010, in 2017–2020 fehlt jeweils der März (Lücke > 14 Tage) → nur 6 vollständige
  // Vorjahre im 10-Jahres-Fenster; /embed lädt ab 2015, die Seite ab 2016 — der Rückfall muss trotzdem gleich sein.
  if (t === 'LUECKE') return (DATEN[t] = kurse(t, 2010).filter(x => !(x.date >= '2017' && x.date < '2021' && x.date.slice(5, 7) === '03')));
  return (DATEN[t] = kurse(t, t === 'SPY' ? 1993 : 1960));
}

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
  if (ZEITRAUM_AKTIV && zeitraumTrifft(url)) return antwort(500, { message: 'statement timeout' });
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
let ZEITRAUM_AKTIV = false;
function zeitraumTrifft(url) { return url.indexOf('date=gte.') < 0 || url.indexOf('date=gte.1996-10-09') >= 0; }
function datei(pfad) {
  const rel = pfad.replace(/\?.*$/, '').replace(/^\/landing\//, '');
  const f = path.join(WURZEL, rel);
  return fs.existsSync(f) ? fs.readFileSync(f, 'utf8') : null;
}
let OFFEN = 0, LETZTE = Date.now();
const LANGSAM = {};      // Ticker → zusätzliche Antwortzeit in ms (Fall „wechsel")
function netz(url, init) {
  url = String(url);
  const tm = /ticker=eq\.([^&]+)/.exec(url);
  const lg = tm ? LANGSAM[decodeURIComponent(tm[1])] : null;
  // {ms, ausser}: langsam außer den Anfragen mit dieser Untergrenze (die erste Ladung kommt schnell)
  const extra = (ZEITRAUM_AKTIV && /rest\/v1\/prices/.test(url) && zeitraumTrifft(url) ? 1500 : 0) +
    (!lg ? 0 : (typeof lg === 'number' ? lg : (url.indexOf('date=gte.' + lg.ausser) >= 0 ? 0 : lg.ms)));
  OFFEN++; LETZTE = Date.now();
  const fertig = (x) => { OFFEN--; LETZTE = Date.now(); return x; };
  return new Promise(res => setTimeout(res, 2 + extra)).then(() => {
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
  if (window.__titelMerken) eintrag.titel = opts && opts.title && opts.title.text;   // nur Embed-True-Seasonal-Fälle
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

function tickerWahl(t) {
  const inp = W.document.getElementById('ticker-input');
  inp.value = t;
  inp.dispatchEvent(new W.KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
}
function auswahl(id) {
  return function (t) { const el = W.document.getElementById(id); el.value = t; el.dispatchEvent(new W.Event('change')); };
}
const WECHSEL = {
  // Dashboard: A erscheint (30-J-Ladung schnell), seine Nachladungen kommen langsam, dann B (Codex M2 R1)
  dashboard: { a: 'QQQ', b: 'IWM', waehle: tickerWahl, start: '^GSPC', langsam: { ms: 1500, ausser: '1996-10-09' }, nachAnzeige: 'title-ticker' },
  wochentage: { a: 'QQQ', b: 'IWM', waehle: tickerWahl, start: '^GSPC' },
  'backtest-engine': { a: 'QQQ', b: 'IWM', waehle: tickerWahl, start: '^GSPC' },
  opex: { a: 'QQQ', b: 'IWM', waehle: tickerWahl, start: 'SPY' },
  vixpiration: { a: 'QQQ', b: 'IWM', waehle: tickerWahl, start: 'SPY' },
  'spot-vol-beta': { a: 'SPY', b: '^GSPC', waehle: auswahl('sel-spot') }
};
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
// /embed mit True Seasonal (verify_true_seasonal_seite.py): embed_true = SPY 10 J., embed_true_wenig = LUECKE
if (S && SEITE === 'embed' && FALL === 'embed_true') S.adresse = 'https://seasonalpha.ai/embed?ticker=SPY&years=10&saison=true';
if (S && SEITE === 'embed' && FALL === 'embed_true_wenig') S.adresse = 'https://seasonalpha.ai/embed?ticker=LUECKE&years=10&saison=true';
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
    // True Seasonal (verify_true_seasonal_seite.py): gemerkter Modus vor dem ersten Skript
    if (FALL === 'saison_true' || FALL === 'saison_true_neu') { try { window.localStorage.setItem('sa.jahreszyklus.saison', 'true'); } catch (e) {} }
    if (FALL === 'embed_true' || FALL === 'embed_true_wenig') window.__titelMerken = true;
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
  if (FALL === 'rueckwechsel') {
    const W2 = WECHSEL[SEITE];
    LANGSAM[W2.a] = 1500;
    W2.waehle(W2.a);
    await new Promise(r => setTimeout(r, 30));
    W2.waehle(W2.start);
    ruhig = (await warteRuhe(40000)) && ruhig;
    await new Promise(r => setTimeout(r, 2000));
    ruhig = (await warteRuhe(40000)) && ruhig;
  }
  if (FALL === 'zeitraum' || FALL === 'zeitraum_direkt') {
    uhrVersatz = 16 * 60 * 1000;
    ZEITRAUM_AKTIV = true;
    const sel = W.document.getElementById('sel-years');
    if (FALL === 'zeitraum') { sel.value = '30'; sel.dispatchEvent(new W.Event('change')); await new Promise(r => setTimeout(r, 30)); }
    sel.value = '5'; sel.dispatchEvent(new W.Event('change'));
    ruhig = (await warteRuhe(60000)) && ruhig;
    await new Promise(r => setTimeout(r, 2000));
    ruhig = (await warteRuhe(60000)) && ruhig;
  }
  if (FALL === 'wechsel' || FALL === 'direkt') {
    const W2 = WECHSEL[SEITE];
    if (!W2) { process.stdout.write(JSON.stringify({ absturz: 'kein Wechsel für ' + SEITE })); process.exit(0); }
    if (FALL === 'wechsel') {
      LANGSAM[W2.a] = W2.langsam || 1500;
      W2.waehle(W2.a);
      if (W2.nachAnzeige) {
        // erst wenn A angezeigt ist (Nachladungen von A — Overnight, Radar, Score — laufen noch, langsam)
        for (let i = 0; i < 200 && text(W2.nachAnzeige) !== W2.a; i++) await new Promise(r => setTimeout(r, 25));
      } else {
        await new Promise(r => setTimeout(r, 30));
      }
    }
    W2.waehle(W2.b);
    ruhig = (await warteRuhe(40000)) && ruhig;
    await new Promise(r => setTimeout(r, 2000));   // die langsame Antwort ist sicher da
    ruhig = (await warteRuhe(40000)) && ruhig;
  }
  if (FALL === 'ttl') {
    // 16 Minuten später, die ganze Historie scheitert jetzt; der Zeitraum-Regler zeichnet neu (Score + Radar laden nach)
    uhrVersatz = 16 * 60 * 1000;
    FEHLER_VOLL = true;
    const sel = W.document.getElementById('sel-years');
    sel.dispatchEvent(new W.Event('change'));
    ruhig = (await warteRuhe(40000)) && ruhig;
  }
  // ── True Seasonal / Rückblick auf /jahreszyklus (Plan docs/review_prompts/2026-10-16_true_seasonal_plan_v3.md) ──
  //   rueckblick:          nach dem Start den Rückblick aufklappen (lädt die volle Historie)
  //   rueckblick_wechsel:  volle Historie von SPY langsam, aufklappen, sofort QQQ wählen — Soll: rueckblick_direkt
  //   rueckblick_direkt:   QQQ wählen, dann aufklappen
  //   rueckblick_fehler:   volle Historie scheitert; danach „Erneut laden" ohne Fehler
  let rbStatusVorher = null;
  const aufklappen = () => { const s = W.document.getElementById('sec-rueckblick'); s.open = true; s.dispatchEvent(new W.Event('toggle')); };
  if (FALL === 'rueckblick' || FALL === 'rueckblick_fehler') {
    if (FALL === 'rueckblick_fehler') FEHLER_VOLL = true;
    aufklappen();
    ruhig = (await warteRuhe(60000)) && ruhig;
    if (FALL === 'rueckblick_fehler') {
      rbStatusVorher = text('rb-status');
      FEHLER_VOLL = false;
      const b = W.document.querySelector('#rb-status button');
      if (b) b.dispatchEvent(new W.MouseEvent('click', { bubbles: true }));
      ruhig = (await warteRuhe(60000)) && ruhig;
    }
  }
  if (FALL === 'saison_true_neu') {   // Reihe LUECKE: True Seasonal fällt auf den Durchschnitt zurück (Soll für /embed)
    tickerWahl('LUECKE');
    ruhig = (await warteRuhe(60000)) && ruhig;
  }
  if (FALL === 'rueckblick_wechsel') {
    LANGSAM.SPY = { ms: 1500, ausser: '2015-01-01' };   // Hauptabruf (ab 2015) schnell, volle Historie langsam
    aufklappen();
    await new Promise(r => setTimeout(r, 30));
    tickerWahl('QQQ');
    ruhig = (await warteRuhe(60000)) && ruhig;
    await new Promise(r => setTimeout(r, 2000));
    ruhig = (await warteRuhe(60000)) && ruhig;
  }
  if (FALL === 'rueckblick_direkt') {
    tickerWahl('QQQ');
    ruhig = (await warteRuhe(60000)) && ruhig;
    aufklappen();
    ruhig = (await warteRuhe(60000)) && ruhig;
  }
  const inhalt = inhaltText();
  const aus = {
    rb_status: text('rb-status'), rb_status_vorher: rbStatusVorher, ts_hinweis: text('ts-hinweis'),
    caption: text('page-caption'), titel: text('title-ticker'),
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

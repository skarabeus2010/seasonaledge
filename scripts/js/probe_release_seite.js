// Sperrprobe (V1b, Plan v6–v9 + Entwurf v1–v6): lädt das ECHTE Dashboard mit seinen echten Skripten in jsdom und
// prüft, was nach einer Release-Sperre noch geschieht. Kennungen je Datei frei wählbar (Platzhalter %%RELEASE%%
// wird beim Ausliefern ersetzt), ApexCharts als Stub mit Methoden auf dem PROTOTYP und verzögertem render(), das
// Serienknoten in sein Ziel hängt (wie die echte Bibliothek asynchron zeichnet).
//
// Aufruf: node probe_release_seite.js <landing-Wurzel> <fall>    → JSON {fall, pruefungen:[…]} + PROBE-ENDE
// Jeder Fall in eigenem Prozess. Zu jedem Sperrfall prüft ein Gegenlauf (Fall `gleich` bzw. `…:kontrolle`), dass die
// beobachtete Wirkung ohne Sperre tatsächlich eintritt (positive Kontrolle).
'use strict';
process.env.TZ = 'Europe/Berlin';
const fs = require('fs');
const path = require('path');
const { JSDOM, ResourceLoader, VirtualConsole } = require(path.join(__dirname, '..', 'perf', 'node_modules', 'jsdom'));

const [WURZEL, FALL_ROH, SEITE_ARG] = process.argv.slice(2);
const SEITE = SEITE_ARG || 'dashboard';   // dashboard | backtest-engine
const [FALL, MODUS] = FALL_ROH.split(':');
const KONTROLLE = MODUS === 'kontrolle';
const ERG = [];
const pruefe = (name, ok, detail) => ERG.push({ name, ok: !!ok, detail: detail === undefined ? '' : String(detail) });
const warte = (ms) => new Promise(r => setTimeout(r, ms));

// ── Kennungen je Fall ─────────────────────────────────────────────────────────────────────────────────────────
const K = { html: 'r1', dateien: {} };            // Standard: alle r1
if (!KONTROLLE) {
  if (FALL === 'a_skript_neu') K.dateien['kurse.js'] = 'r2';          // HTML alt, ein Skript neu
  if (FALL === 'b_html_neu') { K.html = 'r2'; }                       // HTML neu, Skripte alt (methode.js prüft sich zuletzt)
}
const kennungFuer = (datei) => K.dateien[datei] || 'r1';

// ── Kurse + Netz ──────────────────────────────────────────────────────────────────────────────────────────────
function kurse(ticker) {
  let s = 0; for (const c of ticker) s = (s * 31 + c.charCodeAt(0)) >>> 0;
  const z = () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
  const aus = []; let t = Date.UTC(1990, 0, 1), close = 100, mon = -1, tdom = 0, jahr = -1, tdoy = 0;
  while (t <= Date.UTC(2026, 9, 8)) {
    const d = new Date(t);
    if (d.getUTCDay() % 6 !== 0) {
      if (d.getUTCFullYear() !== jahr) { jahr = d.getUTCFullYear(); tdoy = 0; }
      if (d.getUTCMonth() !== mon) { mon = d.getUTCMonth(); tdom = 0; }
      tdom++; tdoy++;
      const neu = Math.round(close * Math.exp((z() - 0.48) * 0.03) * 100) / 100;
      aus.push({ date: d.toISOString().slice(0, 10), open: close, high: neu + 1, low: neu - 1, close: neu,
                 log_return: aus.length ? Math.log(neu / close) : null, tdom, tdoy });
      close = neu;
    }
    t += 86400000;
  }
  return aus;
}
const DATEN = {};
const NETZ = { anfragen: 0, nachSperre: [], langsam: 0, tor: null };
function antwort(status, body) {
  const text = typeof body === 'string' ? body : JSON.stringify(body);
  return { ok: status >= 200 && status < 300, status, headers: { get: () => null },
           json: () => Promise.resolve(JSON.parse(text)), text: () => Promise.resolve(text) };
}
function datei(pfad) {
  const rel = pfad.replace(/\?.*$/, '').replace(/^\/landing\//, '');
  const f = path.join(WURZEL, rel);
  if (!fs.existsSync(f)) return null;
  let t = fs.readFileSync(f, 'utf8');
  if (/\.js$/.test(f)) t = t.split('%%RELEASE%%').join(kennungFuer(path.basename(f)));
  return t;
}
let W = null;
function netz(url) {
  url = String(url);
  NETZ.anfragen++;
  if (W && W.SA && W.SA.__gesperrt) NETZ.nachSperre.push(url.slice(0, 120));
  const tor = NETZ.tor && NETZ.tor(url);
  const verzug = 2 + (/rest\/v1\/prices/.test(url) ? NETZ.langsam : 0);
  return (tor || new Promise(res => setTimeout(res, verzug))).then(() => {
    if (url.startsWith('https://stub/rest/v1/prices')) {
      const p = {}; (url.split('?')[1] || '').split('&').forEach(t => { const k = t.slice(0, t.indexOf('=')); p[k] = decodeURIComponent(t.slice(k.length + 1)); });
      const tk = (p.ticker || '').replace(/^eq\./, '');
      const gte = p.date && p.date.startsWith('gte.') ? p.date.slice(4) : null;
      const gt = (url.match(/date=gt\.([0-9-]+)/) || [])[1] || null;
      const sel = (p.select || 'date,close').split(',');
      const zs = (DATEN[tk] || (DATEN[tk] = kurse(tk))).filter(x => (!gte || x.date >= gte) && (!gt || x.date > gt)).slice(0, 1000)
        .map(x => { const o = {}; sel.forEach(f => { o[f] = x[f] === undefined ? null : x[f]; }); return o; });
      return antwort(200, zs);
    }
    if (url.startsWith('https://stub/')) return antwort(200, []);
    if (/\/landing\/data\/langsam\.json/.test(url)) {      // Body kommt verzögert (Sperre WÄHREND des Lesens)
      return { ok: true, status: 200, headers: { get: () => null },
               text: () => new Promise(r => setTimeout(() => r('{"x":1}'), 300)),
               json: () => new Promise(r => setTimeout(() => r({ x: 1 }), 300)) };
    }
    const pfad = url.replace(/^https:\/\/seasonalpha\.ai/, '');
    const t = pfad.startsWith('/landing/') ? datei(pfad) : null;
    return t === null ? antwort(404, 'nicht gefunden') : antwort(200, t);
  });
}

// ── ApexCharts-Stub: Prototyp-Methoden, render() zeichnet verzögert Serienknoten ins Ziel ────────────────────
const APEX = `
window.__charts = [];
function ApexStub(el, opts) { this.el = el; this.opts = opts; window.__charts.push(this); }
ApexStub.prototype.render = function () {
  var self = this;
  return new Promise(function (ok) {
    setTimeout(function () {
      try {
        var d = document.createElement('div');
        d.className = 'apx-serie';
        d.textContent = JSON.stringify((self.opts && self.opts.series) || []).slice(0, 40);
        self.el.appendChild(d);
      } catch (e) { window.__renderFehler = (window.__renderFehler || 0) + 1; }
      ok();
    }, window.__renderVerzug || 50);
  });
};
ApexStub.prototype.updateSeries = function () { return this.render(); };
ApexStub.prototype.updateOptions = function () { return this.render(); };
ApexStub.prototype.destroy = function () { this.zerstoert = true; };
ApexStub.prototype.toggleSeries = ApexStub.prototype.showSeries = ApexStub.prototype.hideSeries = function () {};
ApexStub.exec = function () {};
window.ApexCharts = ApexStub;
`;
const RESSOURCEN = { nachSperre: [] };
class Lader extends ResourceLoader {
  fetch(url) {
    if (W && W.SA && W.SA.__gesperrt) RESSOURCEN.nachSperre.push(url);
    if (/apexcharts/.test(url)) return Promise.resolve(Buffer.from(APEX));
    if (/supabase-js/.test(url)) return Promise.resolve(Buffer.from(''));
    const pfad = url.replace(/^https:\/\/seasonalpha\.ai/, '');
    if (pfad.startsWith('/landing/')) { const t = datei(pfad); if (t !== null) return Promise.resolve(Buffer.from(t)); }
    return Promise.resolve(Buffer.from(''));
  }
}

// ── Seite aufbauen ────────────────────────────────────────────────────────────────────────────────────────────
const NEULADEN = [];
const SPEICHER = { nachSperre: [] };
let html = fs.readFileSync(path.join(WURZEL, 'pages', SEITE + '.html'), 'utf8')
  .replace('%%SUPABASE_URL%%', 'https://stub').replace('%%SUPABASE_ANON_KEY%%', 'k')
  .split("window.__SA_RELEASE='%%RELEASE%%'").join("window.__SA_RELEASE='" + K.html + "'");
const fehlerSeite = [];
// Nach der Sperre finden Seitenrechner ihre Ziele nicht mehr (null) und werfen — im Browser ein Konsolenfehler,
// hier darf das den Prozess nicht beenden. Protokolliert, nicht verschluckt.
process.on('unhandledRejection', (e) => fehlerSeite.push('[unbehandelt] ' + String(e && e.message || e).slice(0, 160)));
process.on('uncaughtException', (e) => fehlerSeite.push('[ungefangen] ' + String(e && e.message || e).slice(0, 160)));
const vk = new VirtualConsole();
vk.on('jsdomError', (e) => fehlerSeite.push(String(e && (e.detail && e.detail.stack || e.stack || e.message) || e).slice(0, 200)));
const dom = new JSDOM(html, {
  url: 'https://seasonalpha.ai/' + SEITE, runScripts: 'dangerously', resources: new Lader(), pretendToBeVisual: true,
  virtualConsole: vk,
  beforeParse(window) {
    W = window;
    window.fetch = netz;
    window.__saNeuladen = (u) => NEULADEN.push(u);
    window.scrollTo = function () {};
    window.matchMedia = function () { return { matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} }; };
    window.IntersectionObserver = function () { return { observe() {}, unobserve() {}, disconnect() {} }; };
    window.ResizeObserver = function () { return { observe() {}, unobserve() {}, disconnect() {} }; };
    // Zähler UNTER der Speicher-Hülle von methode.js: was hier ankommt, hat die Hülle passiert
    const P = window.Storage.prototype;
    ['setItem', 'removeItem', 'clear'].forEach(m => {
      const o = P[m];
      P[m] = function (k) {
        if (window.SA && window.SA.__gesperrt && k !== 'sa-release-neuladen') SPEICHER.nachSperre.push(m + ':' + k);
        return o.apply(this, arguments);
      };
    });
    if (FALL === 'd_zweiter_versuch' && !KONTROLLE) window.sessionStorage.setItem('sa-release-neuladen', String(Date.now() - 10000));
    if (FALL === 'd_zweiter_versuch' && KONTROLLE) window.sessionStorage.setItem('sa-release-neuladen', String(Date.now() - 200000));
    if (FALL === 'e_speicherfehler') {
      Object.defineProperty(window, 'sessionStorage', { configurable: true, get() { throw new Error('SecurityError'); } });
    }
  }
});

function seriennachweis() { return W.document.querySelectorAll('.apx-serie').length; }
function nurHinweis() {
  const b = W.document.body;
  return b.children.length === 1 && b.children[0].getAttribute('data-sa-release-sperre') === '1';
}
function sperrbeobachtungen(nameZusatz, erwartetNeuladen) {
  const z = nameZusatz ? ' ' + nameZusatz : '';
  pruefe('gesperrt' + z, W.SA && W.SA.__gesperrt === true);
  pruefe('Dokument enthält nur den Hinweis' + z, nurHinweis(), W.document.body.children.length);
  pruefe('kein Chart mit Serien im Dokument' + z, seriennachweis() === 0, seriennachweis());
  pruefe('keine Datenanfrage nach der Sperre' + z, NETZ.nachSperre.length === 0, NETZ.nachSperre.slice(0, 3).join(' | '));
  pruefe('kein Speicher-Schreibzugriff nach der Sperre' + z, SPEICHER.nachSperre.length === 0, SPEICHER.nachSperre.slice(0, 3).join(','));
  pruefe('Neuladen ' + erwartetNeuladen + 'x' + z, NEULADEN.length === erwartetNeuladen, NEULADEN.length);
}
async function bisRuhe(ms) { const ende = Date.now() + ms; while (Date.now() < ende) await warte(100); }

(async function () {
  await warte(300);
  // Aufbau-Nachweis: lädt methode.js nicht (Syntaxfehler, fehlende Datei), ist JEDES Ergebnis wertlos — Abbruch
  // ohne Endmarker statt einer roten Prüfung, die wie ein gefangener Fehler aussähe (Beweisregel: Absturz ≠ Nachweis).
  if (!(W.SA && typeof W.SA.__release === 'function' && typeof W.SA.__sperre === 'function')) {
    process.stdout.write('[Absturz] Aufbau: methode.js nicht geladen\n' + fehlerSeite.slice(0, 2).join('\n') + '\n');
    process.exit(2);
  }
  switch (FALL) {
    case 'gleich': {                                   // positive Kontrolle: gleiche Kennungen → Seite rechnet
      await bisRuhe(8000);
      pruefe('Kontrolle: nicht gesperrt', W.SA && W.SA.__gesperrt === false);
      pruefe('Kontrolle: Charts mit Serien gezeichnet', seriennachweis() > 0, seriennachweis());
      pruefe('Kontrolle: Datenanfragen fanden statt', NETZ.anfragen > 0, NETZ.anfragen);
      pruefe('Kontrolle: kein Neuladen', NEULADEN.length === 0);
      break;
    }
    case 'a_skript_neu':
    case 'b_html_neu': {
      await bisRuhe(4000);
      if (KONTROLLE) { pruefe('Kontrolle: Seite rechnet', !W.SA.__gesperrt && seriennachweis() > 0, seriennachweis()); break; }
      sperrbeobachtungen('', 1);
      pruefe('Hinweis kündigt Neuladen an', /wird neu geladen/.test(W.document.body.textContent));
      break;
    }
    case 'c_spaet': {                                  // Abweichung während laufender Rechnung (Kurse langsam)
      NETZ.langsam = 400;
      W.__renderVerzug = 600;                          // ein render() läuft über die Sperre hinaus
      await warte(900);
      const vorher = { anfragen: NETZ.anfragen, charts: (W.__charts || []).length };
      if (!KONTROLLE) { try { W.SA.__release('spaete-andere-kennung'); } catch (e) { /* ReleaseFehler erwartet */ } }
      await bisRuhe(5000);
      if (KONTROLLE) { pruefe('Kontrolle: ohne Abweichung erscheinen Serien', seriennachweis() > 0, seriennachweis()); break; }
      pruefe('(c) Rechnung lief bereits (Anfragen vor der Sperre)', vorher.anfragen > 0, JSON.stringify(vorher));
      sperrbeobachtungen('(c)', 1);
      break;
    }
    case 'd_zweiter_versuch': {
      try { W.SA.__release('andere'); } catch (e) { /* erwartet */ }
      await warte(200);
      if (KONTROLLE) { pruefe('Kontrolle: Marke älter als 120 s → automatisches Neuladen', NEULADEN.length === 1, NEULADEN.length); break; }
      pruefe('(d) Marke jünger als 120 s → kein automatisches Neuladen', NEULADEN.length === 0, NEULADEN.length);
      pruefe('(d) Hinweis „bitte neu laden"', /bitte neu laden/.test(W.document.body.textContent));
      pruefe('(d) Seite trotzdem gesperrt', W.SA.__gesperrt === true && nurHinweis());
      break;
    }
    case 'e_speicherfehler': {
      try { W.SA.__release('andere'); } catch (e) { /* erwartet */ }
      await warte(200);
      pruefe('(e) Speicher nicht nutzbar → kein Neuladen', NEULADEN.length === 0, NEULADEN.length);
      pruefe('(e) Sperre und Hinweis trotzdem', W.SA.__gesperrt === true && nurHinweis() && /bitte neu laden/.test(W.document.body.textContent));
      break;
    }
    case 'f_fetch_phasen': {                           // direkter Abruf: Header da → Sperre → Body
      await bisRuhe(3000);
      const r1 = await W.fetch('/landing/data/tickers.json');            // Header erfüllt
      if (!KONTROLLE) W.SA.__sperre('Probe');
      let wert = null, fehler = null;
      try { wert = await r1.text(); } catch (e) { fehler = e; }
      if (KONTROLLE) { pruefe('Kontrolle: Body lesbar ohne Sperre', wert !== null); break; }
      pruefe('(i) Body nach Sperre liefert keinen Wert', wert === null && fehler && fehler.name === 'ReleaseFehler', fehler && fehler.name);
      break;
    }
    case 'f2_body_waehrend': {                         // Sperre WÄHREND des Body-Lesens (Body kommt verzögert)
      await bisRuhe(3000);
      const r2 = await W.fetch('/landing/data/langsam.json');
      const lesen = r2.text().then(v => ({ wert: v }), e => ({ fehler: e }));
      await warte(50);
      if (!KONTROLLE) W.SA.__sperre('Probe');
      const e2 = await lesen;
      if (KONTROLLE) { pruefe('Kontrolle: verzögerter Body ohne Sperre lesbar', e2.wert === '{"x":1}', e2.wert); break; }
      pruefe('(ii) Sperre während des Body-Lesens: kein Wert, ReleaseFehler', !e2.wert && e2.fehler && e2.fehler.name === 'ReleaseFehler',
             e2.fehler && e2.fehler.name);
      let f2 = null; try { await W.fetch('/landing/data/tickers.json'); } catch (e) { f2 = e; }
      pruefe('neuer fetch nach Sperre: ReleaseFehler ohne Anfrage', f2 && f2.name === 'ReleaseFehler' && NETZ.nachSperre.length === 0);
      break;
    }
    case 'g_nach_sperre': {                            // Skript, Einfügung, Speicher, Lader nach der Sperre
      await bisRuhe(3000);
      if (!KONTROLLE) W.SA.__sperre('Probe');
      // nachgeladenes eigenes Skript: erste Anweisung prüft (Vorrang __gesperrt)
      const quelle = datei('/landing/js/charts.js') + '\n;window.__skriptLief = true;';
      let skriptFehler = null;
      try { new W.Function(quelle)(); } catch (e) { skriptFehler = e; }
      // Einfügung, Speicher
      let einfFehler = null; try { W.document.head.appendChild(W.document.createElement('script')); } catch (e) { einfFehler = e; }
      let speicherFehler = null; try { W.localStorage.setItem('sa-test', '1'); } catch (e) { speicherFehler = e; }
      let htmlFehler = null; try { W.document.createElement('div').innerHTML = '<img src="/x.png">'; } catch (e) { htmlFehler = e; }
      let chartFehler = null; try { new W.ApexCharts(W.document.createElement('div'), { series: [1] }); } catch (e) { chartFehler = e; }
      // Analytics-Verbraucher mit BEREITS erfülltem Body (Entwurf v4 Probe iii / v5): der Abruf lief vor der Sperre,
      // nachgestellt durch einen fetch, der den fertigen Body liefert; dann läuft der echte loadAnalytics().
      // Tour-Lader (driver.js + CSS vom CDN) nach der Sperre: nichts eingehängt, nichts geladen
      const vorTour = W.document.querySelectorAll('link[data-sa-tour-css], script[src*="driver.js"]').length;
      if (W.SA.tour && typeof W.SA.tour.start === 'function') { try { W.SA.tour.start(0); } catch (e) { /* gesperrt */ } }
      await warte(300);
      const tourKnoten = W.document.querySelectorAll('link[data-sa-tour-css], script[src*="driver.js"]').length - vorTour;
      const ANALYTICS = 'https://analytics.example/x.js';
      const echtFetch = W.fetch;
      W.fetch = () => Promise.resolve({ text: () => Promise.resolve('<script src="' + ANALYTICS + '" defer></script>') });
      const vorKnoten = W.document.querySelectorAll('script[src="' + ANALYTICS + '"]').length;
      if (typeof W.loadAnalytics === 'function') W.loadAnalytics();
      await warte(300);
      W.fetch = echtFetch;
      const knoten = W.document.querySelectorAll('script[src="' + ANALYTICS + '"]').length - vorKnoten;
      const geladen = RESSOURCEN.nachSperre.filter(u => u.indexOf('analytics.example') >= 0).length;
      if (KONTROLLE) {
        pruefe('Kontrolle: Skript läuft', W.__skriptLief === true);
        pruefe('Kontrolle: Einfügen, Speichern, innerHTML, Chart möglich', !einfFehler && !speicherFehler && !htmlFehler && !chartFehler);
        pruefe('Kontrolle: loadAnalytics hängt das Skript ein', typeof W.loadAnalytics === 'function' && knoten === 1, knoten);
        pruefe('Kontrolle: Tour lädt driver.js/CSS', tourKnoten >= 1, tourKnoten);
        break;
      }
      pruefe('Analytics nach Sperre (Body schon erfüllt): kein Skriptknoten, keine Ladung', knoten === 0 && geladen === 0,
             knoten + ' / ' + geladen);
      pruefe('Tour nach Sperre: kein driver.js/CSS eingehängt', tourKnoten === 0 &&
             RESSOURCEN.nachSperre.filter(u => /driver\.js/.test(u)).length === 0, tourKnoten);
      pruefe('nachgeladenes eigenes Skript läuft nicht (erste Anweisung wirft)', W.__skriptLief !== true && skriptFehler && skriptFehler.name === 'ReleaseFehler', skriptFehler && skriptFehler.name);
      pruefe('Einfügung nach Sperre wirft synchron', einfFehler && einfFehler.name === 'ReleaseFehler');
      pruefe('localStorage.setItem nach Sperre wirft', speicherFehler && speicherFehler.name === 'ReleaseFehler');
      pruefe('innerHTML an abgehängtem Element nach Sperre wirft', htmlFehler && htmlFehler.name === 'ReleaseFehler');
      pruefe('neues Chart nach Sperre wirft', chartFehler && chartFehler.name === 'ReleaseFehler', chartFehler && chartFehler.name);
      break;
    }
    default: throw new Error('[Aufbau] unbekannter Fall ' + FALL);
  }
  process.stdout.write(JSON.stringify({ fall: FALL_ROH, pruefungen: ERG, seitenfehler: fehlerSeite.slice(0, 5) }) + '\nPROBE-ENDE\n');
  process.exit(0);
})().catch(e => { process.stdout.write('[Absturz] ' + (e && e.stack) + '\n'); process.exit(2); });

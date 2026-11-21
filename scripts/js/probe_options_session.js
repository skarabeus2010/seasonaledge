/* Faehrt das inline-JS von /key-levels und /dealer-positioning gegen synthetische Daten (Plan v4 B2, Codex-Befunde
   2026-10-14):
   (1) /key-levels: der kopierbare Level-Text traegt die SESSION der Daten, nicht den Lauftag (`generated`).
   (2) /dealer-positioning: ein Profil einer anderen Session als die Summary wird nicht gezeigt; dasselbe Profil mit
       passender Session schon.
   Das JS wird aus der SEITE gezogen, nicht aus einer Kopie. Keine Netz-, keine Dateizugriffe ausser den Seiten. */
const fs = require('fs');
const path = require('path');
const REPO = path.resolve(__dirname, '..', '..');

function umgebung(daten) {
  const el = {};
  function neu(id) {
    const o = {
      id, _html: '', style: {}, dataset: {}, value: '', textContent: '',
      classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
      appendChild() {}, addEventListener() {}, scrollIntoView() {}, setAttribute() {}, getAttribute() { return null; },
      querySelectorAll() { return []; }, querySelector() { return null; }, closest() { return null; }, select() {}
    };
    Object.defineProperty(o, 'innerHTML', { get() { return this._html; }, set(v) { this._html = String(v); } });
    return o;
  }
  const hole = (id) => el[id] || (el[id] = neu(id));
  const kopiert = [];
  global.ApexCharts = class { constructor(h, o) { umgebung.letzteOptionen = o; } render() { return Promise.resolve(); } updateOptions() {} destroy() {} };
  global.document = {
    readyState: 'complete', getElementById: hole, createElement: () => neu('x'), body: { appendChild() {}, removeChild() {} },
    querySelectorAll: () => [], querySelector: () => null, addEventListener() {}, execCommand() { return true; }
  };
  global.window = { SA: null, ApexCharts: global.ApexCharts, scrollTo() {}, addEventListener() {}, location: { search: '' } };
  // Node >= 21 hat ein schreibgeschuetztes globales navigator — ueberschreiben statt zuweisen.
  Object.defineProperty(globalThis, 'navigator', { configurable: true, writable: true,
    value: { clipboard: { writeText: (t) => { kopiert.push(t); return Promise.resolve(); } } } });
  global.loadComponent = function () {};
  global.fetch = (u) => {
    const k = u.split('?')[0];
    if (!(k in daten)) return Promise.resolve({ ok: false, status: 404, json: () => Promise.reject(new Error(u)) });
    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(JSON.parse(JSON.stringify(daten[k]))) });
  };
  return { hole, kopiert };
}

function lade(seite) {
  const html = fs.readFileSync(path.join(REPO, 'landing/pages', seite), 'utf8');
  const bloecke = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
  eval(bloecke.reduce((a, b) => (b.length > a.length ? b : a)));
}

const warte = (ms) => new Promise((r) => setTimeout(r, ms));
let fehler = 0;
const pruefe = (ok, was) => { console.log((ok ? '  ok   ' : '  FEHL ') + was); if (!ok) fehler++; };

(async () => {
  console.log('/key-levels:');
  const kl = umgebung({
    '/landing/data/key_levels.json': {
      generated: '2026-10-17', session: '2026-10-16', gex_status: 'ok', source: 'x',
      tickers: [{ ticker: 'SPY', cats: [], spot: 700, vol_trigger: 690, call_wall: 720, put_wall: 680,
                  max_pain: 700, exp: '2026-10-23', pc_oi_ratio: 1.1, top_call_oi: [], top_put_oi: [] }]
    }
  });
  lade('key-levels.html');
  await warte(400);
  const btn = kl.hole('kl-copy-btn');
  if (btn.onclick) btn.onclick();
  await warte(50);
  pruefe(kl.kopiert.length === 1, "Kopierknopf gefunden und betaetigt");
  pruefe(/SPY\s+\(2026-10-16\)/.test(kl.kopiert[0] || ''), 'Level-Text traegt die Session: ' + (kl.kopiert[0] || '').split('\n')[0]);

  console.log('/dealer-positioning:');
  const summary = { date: '2026-10-16', session: '2026-10-16', stempel_art: 'session', gamma_index: null,
                    tickers: [{ ticker: 'SPY', spot: 700, net_gex_usd_bn: 1, net_vanna_usd_mn: 1, net_charm_usd_mn_per_day: 1,
                                regime: 'long_gamma', zero_gamma: 690, call_wall: 720, put_wall: 680, skew: 1 }] };
  const prof = (s) => ({ ticker: 'SPY', date: s, session: s, profile: { by_strike: [{ strike: 700, gex: 1, vanna: 1, charm: 1 }],
                                                                        by_term: [{ exp: '2026-10-23', gex: 1, vanna: 1, charm: 1 }] } });
  for (const [s, soll, was] of [['2026-10-15', false, 'Profil der Vorsession wird NICHT gezeigt'],
                                ['2026-10-16', true, 'Profil derselben Session wird gezeigt']]) {
    const dp = umgebung({ '/landing/data/gex_summary.json': summary, '/landing/data/gex_profile_SPY.json': prof(s) });
    lade('dealer-positioning.html');
    await warte(500);
    const chart = dp.hole('chart').innerHTML, hz = dp.hole('chart-horizon').innerHTML;
    const gezeigt = /Horizont: 1 Verf/.test(hz) && !/Kein Profil/.test(chart);
    pruefe(gezeigt === soll, was + ' (Horizont: ' + (hz || '—').slice(0, 40) + ')');
  }

  // (3) Marker der by-Strike-Ansicht: numerische Achse, Linie am WERT (nicht als Pixel, nicht auf eine Kategorie
  //     gerundet), jede Linie innerhalb des Ausschnitts; was weiter als 20 % vom Spot liegt, steht im Text statt im Bild.
  //     Anlass 2026-11-21: Spot 689.81 und Call-Wall 775 lagen auf einer Kategorie-Achse bei 689/775 PIXELN.
  console.log('/dealer-positioning Marker:');
  {
    const sum = { date: '2026-11-20', session: '2026-11-20', stempel_art: 'session', gamma_index: null,
                  tickers: [{ ticker: 'SPY', spot: 689.81, net_gex_usd_bn: -1, net_vanna_usd_mn: 1, net_charm_usd_mn_per_day: 1,
                              regime: 'short_gamma', zero_gamma: 737.02, call_wall: 775, put_wall: 500, skew: 1 }] };
    const strikes = []; for (let k = 450; k <= 900; k += 5) strikes.push({ strike: k, gex: -1, vanna: 1, charm: 1 });
    const p = { ticker: 'SPY', date: '2026-11-20', session: '2026-11-20',
                profile: { by_strike: strikes, by_term: [{ exp: '2026-11-27', gex: 1, vanna: 1, charm: 1 }] } };
    const dp = umgebung({ '/landing/data/gex_summary.json': sum, '/landing/data/gex_profile_SPY.json': p });
    lade('dealer-positioning.html');
    await warte(500);
    const o = umgebung.letzteOptionen || {}, xa = o.xaxis || {}, ann = ((o.annotations || {}).xaxis) || [];
    const bei = (t) => (ann.find((a) => a.label && a.label.text.indexOf(t) === 0) || {}).x;
    pruefe(xa.type === 'numeric' && !xa.categories, 'Strike-Achse numerisch, ohne Kategorien');
    pruefe(bei('Spot') === 689.81, 'Spot-Linie bei 689.81 (nicht gerundet, nicht als Pixel): ' + bei('Spot'));
    pruefe(bei('Flip') === 737.02, 'Flip-Linie bei 737.02: ' + bei('Flip'));
    pruefe(bei('Call-Wall') === 775, 'Call-Wall-Linie bei 775 (>8 %, <=20 % vom Spot, Ausschnitt erweitert): ' + bei('Call-Wall'));
    pruefe(ann.every((a) => a.x >= xa.min && a.x <= xa.max), 'jede Linie liegt im Ausschnitt [' + xa.min + ', ' + xa.max + ']');
    pruefe(bei('Put-Wall') === undefined && /Put-Wall 500/.test(dp.hole('chart-horizon').innerHTML),
           'Put-Wall 500 (>20 % vom Spot) nicht als Linie, sondern im Text genannt');
    const daten = ((o.series || [])[0] || {}).data || [];
    pruefe(daten.length > 0 && daten.every((d) => Array.isArray(d) && d[0] >= xa.min && d[0] <= xa.max),
           'Balken als [Strike, Wert] im Ausschnitt (' + daten.length + ')');
  }

  // (4) Nachtraege aus Codex 2026-11-21: Balkenwerte und Vollstaendigkeit, 20-%-Grenze VOR der Rundung,
  //     Spot 0 ungueltig, ungleiche Strike-Abstaende.
  async function dealerLauf(t, strikes) {
    const sum = { date: '2026-11-20', session: '2026-11-20', stempel_art: 'session', gamma_index: null,
                  tickers: [Object.assign({ ticker: 'SPY', net_gex_usd_bn: -1, net_vanna_usd_mn: 1,
                                            net_charm_usd_mn_per_day: 1, regime: 'short_gamma', skew: 1 }, t)] };
    const p = { ticker: 'SPY', date: '2026-11-20', session: '2026-11-20',
                profile: { by_strike: strikes, by_term: [{ exp: '2026-11-27', gex: 1, vanna: 1, charm: 1 }] } };
    umgebung.letzteOptionen = null;
    const dp = umgebung({ '/landing/data/gex_summary.json': sum, '/landing/data/gex_profile_SPY.json': p });
    lade('dealer-positioning.html');
    await warte(500);
    const o = umgebung.letzteOptionen || {};
    return { o, xa: o.xaxis || {}, ann: ((o.annotations || {}).xaxis) || [],
             daten: ((o.series || [])[0] || {}).data || [], hz: dp.hole('chart-horizon').innerHTML };
  }
  console.log('/dealer-positioning Werte und Grenzen:');
  {
    // ungleiche Abstaende: 1er um den Spot, 5er weiter weg; Werte eindeutig je Strike
    const strikes = [];
    for (let k = 60; k <= 140; k += (k >= 95 && k < 105 ? 1 : 5))
      strikes.push({ strike: k, gamma_usd_mn: Math.round((k - 100) * 7.3 + 0.5 * (k % 3)), vanna_usd_mn: 1, charm_usd_mn: 1 });
    const r = await dealerLauf({ spot: 100, zero_gamma: 120, call_wall: 120.5, put_wall: 95 }, strikes);
    const soll = strikes.filter((s) => s.strike >= r.xa.min && s.strike <= r.xa.max);
    const werteOk = r.daten.length === soll.length &&
      soll.every((s, i) => r.daten[i] && r.daten[i][0] === s.strike && r.daten[i][1] === s.gamma_usd_mn);
    pruefe(werteOk, 'jeder Strike im Ausschnitt mit seinem Gamma-Wert, keiner fehlt (' + r.daten.length + '/' + soll.length + ')');
    pruefe(r.daten.some((d) => d[0] === 101) && r.daten.some((d) => d[0] === 110),
           'ungleiche Abstaende: 1er- und 5er-Strikes beide gezeichnet');
    const linie = (t) => r.ann.some((a) => a.label && a.label.text.indexOf(t) === 0);
    pruefe(linie('Flip 120'), 'Flip bei genau 20 % als Linie');
    pruefe(!linie('Call-Wall') && /Call-Wall 120\.5/.test(r.hz),
           'Call-Wall bei 20,5 % nicht als Linie, auch wenn sie im gerundeten Ausschnitt laege (Ausschnitt bis ' + r.xa.max + ')');
    const r0 = await dealerLauf({ spot: 0, zero_gamma: 120, call_wall: 130, put_wall: 90 }, strikes);
    pruefe(!r0.ann.some((a) => a.label && /^Spot/.test(a.label.text)), 'Spot 0 erzeugt keine Spot-Linie');
  }

  // (5) /polymarket: Erwartungswert der Fed-Verteilung ist eine Bruchzahl -> numerische Achse (gleiche Fehlerklasse,
  //     Codex 2026-11-21). Echte polymarket.js, gleiche ApexCharts-Attrappe.
  console.log('/polymarket Fed-Verteilung:');
  {
    umgebung({});
    global.window = {};
    require('./release_harness').bereite(global.window);   // echte methode.js zuerst (Releasekennung)
    eval(fs.readFileSync(path.join(REPO, 'landing/js/polymarket.js'), 'utf8'));
    const SAg = global.window.SA;
    SAg.chartTheme = { chart: {}, grid: {}, xaxis: { labels: { style: { colors: '#999' } } }, yaxis: {} };
    SAg.COLORS = { accent: '#e8a820', green: '#2c2' };
    SAg.i18n = { t: (k, f) => f || k, isEN: () => false };
    global.SA = SAg;
    umgebung.letzteOptionen = null;
    SAg.polymarket.renderFedDistChart('x', { distNorm: { '0': 0.1, '1': 0.2, '2': 0.3, '3': 0.4 }, expectedCuts: 2.37, istUntergrenze: false });
    const o = umgebung.letzteOptionen || {}, xa = o.xaxis || {}, a = (((o.annotations || {}).xaxis) || [])[0] || {};
    const d = ((o.series || [])[0] || {}).data || [];
    pruefe(xa.type === 'numeric' && !xa.categories, 'Fed-Achse numerisch');
    pruefe(a.x === 2.37 && a.x > xa.min && a.x < xa.max, 'Erwartungswert-Linie bei 2.37 im Achsenbereich');
    pruefe(d.length === 13 && d[2].x === 2 && Math.abs(d[2].y - 30) < 1e-9, 'Balken bei x = Anzahl Cuts mit ihrem Wert');
    pruefe(xa.labels && xa.labels.formatter && xa.labels.formatter(12) === '12+' && xa.labels.formatter(-1) === '',
           'Achsenbeschriftung 0..11, 12+, Raender leer');
  }

  console.log('');
  console.log(fehler === 0 ? 'ALLE PRUEFUNGEN BESTANDEN' : fehler + ' FEHLER');
  process.exit(fehler === 0 ? 0 : 1);
})();

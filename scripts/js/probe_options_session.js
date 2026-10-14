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
  global.ApexCharts = class { constructor() {} render() { return Promise.resolve(); } updateOptions() {} destroy() {} };
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

  console.log('');
  console.log(fehler === 0 ? 'ALLE PRUEFUNGEN BESTANDEN' : fehler + ' FEHLER');
  process.exit(fehler === 0 ? 0 : 1);
})();

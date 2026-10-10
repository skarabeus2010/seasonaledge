// Probe für scripts/verify_kurse.py: liefern die neuen Hüllen (SA.fetchAllPrices in app.js, ladeVollHistorie in
// decade-compute.js) JE AUFRUF dieselben Zeilen wie die alten Lader? Die alten stehen wörtlich in
// scripts/fixtures/kurse_alte_lader.js (Stand vor der Umstellung). Beide laufen gegen denselben PostgREST-Nachbau,
// der Range + count=exact (alter Weg) UND Keyset (neuer Weg) bedient.
// Die Hüllen werden aus den ECHTEN Dateien geschnitten (app.js ist an den DOM gebunden und als Ganzes nicht
// lauffähig): fetchAllPrices aus app.js, ladeVollHistorie aus decade-compute.js — der Schnitt ist streng (genau
// ein Treffer), sonst bricht die Probe ab.
// Aufruf: node probe_kurse_huellen.js → JSON {pruefungen, ende}
'use strict';
const fs = require('fs');
const path = require('path');
const W = path.join(__dirname, '..', '..');

global.window = { SA: { supabase: { url: 'https://stub', key: 'k' } } };
global.SA = global.window.SA;
global.localStorage = { length: 0, key: () => null, removeItem() {}, getItem: () => null, setItem() {} };

function reihe(n, start) {
  const aus = [];
  let t = Date.UTC(start || 1990, 0, 1);
  for (let i = 0; i < n; i++) {
    aus.push({ date: new Date(t).toISOString().slice(0, 10), open: 1 + i, close: i % 13 === 0 ? 0 : 100 + i / 7,
               log_return: i === 0 ? null : (i % 9) / 1000, tdom: (i % 21) + 1, tdoy: i % 17 === 0 ? null : (i % 252) + 1 });
    t += 86400000;
  }
  return aus;
}
let DATEN = [];
global.fetch = function (url, init) {
  const q = url.split('?')[1].split('&');
  const p = { gte: null, gt: null, limit: null };
  for (const teil of q) {
    const k = teil.slice(0, teil.indexOf('='));
    const v = decodeURIComponent(teil.slice(k.length + 1));
    if (k === 'select') p.select = v.split(',');
    else if (k === 'limit') p.limit = +v;
    else if (k === 'date' && v.startsWith('gte.')) p.gte = v.slice(4);
    else if (k === 'date' && v.startsWith('gt.')) p.gt = v.slice(3);
  }
  const h = (init && init.headers) || {};
  let z = DATEN.filter(x => (p.gte === null || x.date >= p.gte) && (p.gt === null || x.date > p.gt));
  const gesamt = z.length;
  let von = 0;
  if (h.Range) { const [a, b] = h.Range.split('-').map(Number); von = a; z = z.slice(a, b + 1); }
  if (p.limit) z = z.slice(0, Math.min(p.limit, 1000)); else z = z.slice(0, 1000);
  z = z.map(x => { const o = {}; for (const f of p.select) o[f] = x[f] === undefined ? null : x[f]; return o; });
  const cr = (z.length ? von + '-' + (von + z.length - 1) : '*') + '/' + (h.Prefer === 'count=exact' ? gesamt : '*');
  return Promise.resolve({ ok: true, status: 200, headers: { get: (n) => (n.toLowerCase() === 'content-range' ? cr : null) },
                           json: () => Promise.resolve(z) });
};

// alt
const ALT = require(path.join(W, 'scripts', 'fixtures', 'kurse_alte_lader.js'))({ supabase: SA.supabase, cache: null });

// neu: echte kurse.js + die Hüllen aus den echten Dateien
require(path.join(W, 'landing', 'js', 'kurse.js'));
function schnitt(datei, anfang, ende) {
  const s = fs.readFileSync(path.join(W, datei), 'utf8');
  const a = s.indexOf(anfang);
  if (a < 0 || s.indexOf(anfang, a + 1) >= 0) throw new Error('Schnitt nicht eindeutig: ' + datei + ' ' + anfang);
  const b = s.indexOf(ende, a);
  if (b < 0) throw new Error('Schnittende fehlt: ' + datei + ' ' + ende);
  return s.slice(a, b);
}
new Function('SA', schnitt('landing/js/app.js', 'SA.FELDER_STANDARD = ', '// ── Trading Day Header'))(SA);
const dc = new Function('SA', 'window', 'return {' +
  schnitt('landing/js/decade-compute.js', '  ladeVollHistorie: function(ticker) {', '  mitHistorie: function(rows, ticker) {') + '};')(SA, global.window);
const NEU = { fetchAllPrices: SA.fetchAllPrices, ladeVollHistorie: dc.ladeVollHistorie.bind(dc) };

const P = [];
function pruefe(name, ok, detail) { P.push({ name, ok: !!ok, detail: detail === undefined ? '' : String(detail) }); }

(async function () {
  const faelle = [];
  for (const n of [0, 1, 999, 1000, 1001, 2000, 2500, 33739]) {
    const d = reihe(n);
    const mitte = n ? d[Math.floor(n / 2)].date : '1990-06-01';
    faelle.push([n, d, [undefined, '', '&date=gte.1895-01-01', '&date=gte.' + mitte, '&date=gte.2100-01-01',
                        '&date=gte.' + (n ? d[0].date : '1990-01-01'), '&date=gte.' + (n ? d[n - 1].date : '1990-01-01')]]);
  }
  for (const [n, d, filter] of faelle) {
    DATEN = d;
    for (const f of filter) {
      SA.kurse._intern.zuruecksetzen();
      const alt = await ALT.fetchAllPrices('T', f), neu = await NEU.fetchAllPrices('T', f);
      pruefe('fetchAllPrices gleich: n=' + n + ' ' + (f || '(ohne)'), JSON.stringify(alt) === JSON.stringify(neu),
             alt.length + ' / ' + neu.length);
    }
    SA.kurse._intern.zuruecksetzen();
    const va = await ALT.ladeVollHistorie('T' + n), vn = await NEU.ladeVollHistorie('T' + n);
    pruefe('ladeVollHistorie gleich: n=' + n, JSON.stringify(va) === JSON.stringify(vn), va.length + ' / ' + vn.length);
  }
  // nicht unterstützter Filter lehnt ab statt still ignoriert zu werden
  let fehler = null;
  try { await NEU.fetchAllPrices('T', '&date=lte.2000-01-01'); } catch (e) { fehler = e; }
  pruefe('unbekannter Filter lehnt ab', fehler && /nicht unterstützt/.test(fehler.message), fehler && fehler.message);
  process.stdout.write(JSON.stringify({ pruefungen: P, ende: true }), () => process.exit(0));
})().catch(e => process.stdout.write(JSON.stringify({ pruefungen: P, absturz: String(e && e.stack || e) }), () => process.exit(0)));

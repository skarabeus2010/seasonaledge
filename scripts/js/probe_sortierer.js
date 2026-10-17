/* Sortierung von Tabellen mit echter DOM-Implementierung (jsdom):
   1. SA.makeSortable aus landing/js/app.js: eine per innerHTML gebaute <table><tr><th>… (Browser legt ein implizites
      <tbody> um alle Zeilen) — nach dem Sortieren muss die Kopfzeile oben bleiben (Fehler bis 2026-10-17: sie wanderte
      ans Ende, auf /skew verschwanden die Überschriften).
   2. /skew Vol-Kennzahlen: zwei Tabellen (zweispaltig) mit eigener Sortierung über ALLE Zeilen; Klick auf eine
      Überschrift sortiert beide Hälften gemeinsam, beide Köpfe bleiben, der allgemeine Sortierer greift nicht.
   Aufruf: node scripts/js/probe_sortierer.js   (Exit 0 grün, 1 rot) */
const fs = require('fs');
const path = require('path');
const REPO = path.resolve(__dirname, '..', '..');
const { JSDOM } = require(path.join(REPO, 'scripts', 'perf', 'node_modules', 'jsdom'));

let fehler = 0;
const pruefe = (b, was) => { console.log((b ? '  ok   ' : '  FEHL ') + was); if (!b) fehler++; };

// ── 1. SA.makeSortable ──────────────────────────────────────────────────────────────────────────────────────────────
console.log('app.js SA.makeSortable:');
const app = fs.readFileSync(path.join(REPO, 'landing/js/app.js'), 'utf8');
const a0 = app.indexOf('SA.makeSortable = function');
const a1 = app.indexOf('\n};', a0) + 3;
if (a0 < 0) { console.log('  FEHL Anker SA.makeSortable fehlt'); process.exit(1); }
const dom = new JSDOM('<!doctype html><div id="c"></div>', { runScripts: 'outside-only' });
const w = dom.window;
w.SA = {};
w.eval(app.slice(a0, a1));
w.document.getElementById('c').innerHTML =
  '<table id="t"><tr><th>Name</th><th>Wert</th></tr><tr><td>b</td><td>2</td></tr><tr><td>a</td><td>10</td></tr><tr><td>c</td><td>1</td></tr></table>';
const t = w.document.getElementById('t');
pruefe(!!t.querySelector('tbody') && t.querySelector('tbody').querySelector('th'), 'Ausgangslage: implizites <tbody> enthält die Kopfzeile');
w.SA.makeSortable(t);
t.querySelectorAll('th')[1].dispatchEvent(new w.Event('click'));
const reihen = () => [...t.querySelectorAll('tr')].map(r => r.textContent.replace(/[▲▼\s]/g, ''));
pruefe(reihen()[0] === 'NameWert', 'nach Klick (absteigend): Kopfzeile bleibt oben — ' + reihen().join(' | '));
pruefe(reihen().slice(1).join(',') === 'a10,b2,c1', 'Datenzeilen nach Wert absteigend sortiert');
t.querySelectorAll('th')[1].dispatchEvent(new w.Event('click'));
pruefe(reihen()[0] === 'NameWert' && reihen().slice(1).join(',') === 'c1,b2,a10', 'zweiter Klick (aufsteigend): Kopf oben, Reihenfolge umgekehrt');

// ── 2. /skew Vol-Kennzahlen ─────────────────────────────────────────────────────────────────────────────────────────
console.log('/skew Vol-Kennzahlen:');
const html = fs.readFileSync(path.join(REPO, 'landing/pages/skew.html'), 'utf8');
const bloecke = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const haupt = bloecke.reduce((x, y) => (y.length > x.length ? y : x));
const tick = (tk, skew, vrp) => ({ ticker: tk, cats: ['X'], skew_pts: skew, iv_atm: skew == null ? null : 0.3, vrp_pts: vrp });
const snap = { session: '2026-10-16', rang_session: '2026-10-16', categories: ['X'], rang: {},
  tickers: [tick('AAA', 5, 1), tick('BBB', 1, 9), tick('CCC', 3, -2), tick('DDD', 4, 4), tick('EEE', 2, 0.5),
            tick('LEER', null, null), Object.assign(tick('NUR_NE', null, null), { skew_ne_pts: 1.88 })] };
// Vol-Trigger: aktuelle Session Mo 19.10., Archiv vom Fr 16.10. (direkte Vorsession) — oder nur vom 15.10. (Ausfall)
const gex = { session: '2026-10-19', date: '2026-10-19', gamma_index: {}, tickers: [
  { ticker: 'AAA', spot: 100, zero_gamma: 99, regime: 'long_gamma', call_wall: 400, put_wall: 99.5 }] };
const archiv = { '2026-10-16': { session: '2026-10-16', tickers: [{ ticker: 'AAA', call_wall: 380, put_wall: 100 }] },
                 '2026-10-15': { session: '2026-10-15', tickers: [{ ticker: 'AAA', call_wall: 390, put_wall: 100 }] } };
let archivTage = ['2026-10-16', '2026-10-15'];
const d2 = new JSDOM(html.replace(/<script[\s\S]*?<\/script>/g, ''), { runScripts: 'outside-only' });
const w2 = d2.window;
const antwort = (x) => Promise.resolve({ ok: true, headers: { get: () => null }, json: () => Promise.resolve(JSON.parse(JSON.stringify(x))) });
w2.fetch = (u) => {
  const k = u.split('?')[0];
  if (k === '/landing/data/options_skew.json') return antwort(snap);
  if (k === '/landing/data/gex_summary.json') return antwort(gex);
  const m = k.match(/gex_history_session\/(\d{4}-\d{2}-\d{2})\.json$/);
  if (m && archivTage.includes(m[1])) return antwort(archiv[m[1]]);
  return Promise.resolve({ ok: false, status: 404, json: () => Promise.reject(new Error(u)) });
};
w2.ApexCharts = class { render() { return Promise.resolve(); } updateOptions() {} destroy() {} };
w2.eval(haupt);
setTimeout(() => {
  const box = w2.document.getElementById('sk-table');
  const tabellen = () => [...box.querySelectorAll('table')];
  const ticker = () => tabellen().map(tb => [...tb.querySelectorAll('tr[data-tk]')].map(r => r.getAttribute('data-tk')).join(','));
  pruefe(tabellen().length === 2, 'zwei Tabellen nebeneinander');
  pruefe(!ticker().join(',').includes('LEER'), 'Ticker ohne Werte ausgeblendet');
  pruefe(ticker().join(' / ') === 'AAA,DDD,CCC / EEE,BBB,NUR_NE', 'Standard: 25Δ-Skew absteigend über beide Hälften — ' + ticker().join(' / '));
  pruefe(tabellen().every(tb => tb.dataset.noSort === '1'), 'allgemeiner Sortierer abgeschaltet (data-no-sort)');
  box.querySelector('th[data-k="vrp"]').dispatchEvent(new w2.Event('click'));
  pruefe(ticker().join(' / ') === 'BBB,DDD,AAA / EEE,CCC,NUR_NE', 'Klick VRP: absteigend über ALLE Zeilen neu verteilt — ' + ticker().join(' / '));
  pruefe(tabellen().every(tb => tb.querySelector('thead th[data-k="vrp"]') && tb.querySelector('thead').textContent.includes('▼')),
    'beide Köpfe bleiben stehen, aktive Spalte mit ▼');
  box.querySelector('th[data-k="vrp"]').dispatchEvent(new w2.Event('click'));
  pruefe(ticker().join(' / ') === 'CCC,EEE,AAA / DDD,BBB,NUR_NE', 'zweiter Klick: aufsteigend — ' + ticker().join(' / '));
  const ct = w2.document.getElementById('sk-table-cat').textContent;
  pruefe(/6 Ticker/.test(ct) && /1 ohne Werte ausgeblendet/.test(ct) && ticker().join(',').includes('NUR_NE'),
    'nur ganz leere Zeilen ausgeblendet, Zeile mit NE-Skew bleibt — ' + ct);

  console.log('/skew Vol-Trigger Walls:');
  const zelle = () => [...w2.document.querySelectorAll('#sk-vt-body tr[data-tk="AAA"] td')].map(td => td.textContent);
  const z = zelle();
  pruefe(z[5] === '400 (+20)', 'Call-Wall 380 → 400: „400 (+20)“ — ' + z[5]);
  pruefe(z[6] === '99.5 (−0.5)', 'Put-Wall 100 → 99,5: Halbschritt sichtbar, Abnahme — ' + z[6]);
  const farbe = [...w2.document.querySelectorAll('#sk-vt-body tr[data-tk="AAA"] td span[title]')].map(s => s.style.color);
  pruefe(farbe.length === 2 && /48, 232, 120|30e878/.test(farbe[0]) && /255, 77, 94|ff4d5e/.test(farbe[1]), 'grün höher, rot tiefer — ' + farbe);
  pruefe(!w2.document.getElementById('sk-vt-head').textContent.includes('*'), 'direkte Vorsession: keine Kennzeichnung');

  // zweiter Lauf: Archiv vom 16.10. fehlt → Vergleich mit dem 15.10. muss gekennzeichnet sein
  archivTage = ['2026-10-15'];
  const d3 = new JSDOM(html.replace(/<script[\s\S]*?<\/script>/g, ''), { runScripts: 'outside-only' });
  d3.window.fetch = w2.fetch;
  d3.window.ApexCharts = w2.ApexCharts;
  d3.window.eval(haupt);
  setTimeout(() => {
    const z3 = [...d3.window.document.querySelectorAll('#sk-vt-body tr[data-tk="AAA"] td')].map(td => td.textContent);
    const kopf = d3.window.document.getElementById('sk-vt-head').textContent;
    pruefe(z3[5] === '400 (+10*)' && /15\.10\.2026/.test(kopf) && kopf.includes('*'),
      'Vorsession fehlt im Archiv: Vergleich mit dem 15.10. gekennzeichnet — ' + z3[5] + ' | ' + kopf.slice(0, 80));
    console.log(fehler ? fehler + ' FEHLER' : 'ALLE PRUEFUNGEN BESTANDEN');
    process.exit(fehler ? 1 : 0);
  }, 600);
}, 600);

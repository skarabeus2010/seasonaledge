// Momentaufnahme der öffentlichen Ausgabe von SA.holidays (landing/js/holidays.js) — Kalender V2, Prüfung
// „Momentaufnahme alt" (docs/review_prompts/2026-10-18_kalender_v2_entwurf*.md).
//
//   node scripts/js/holidays_alt_probe.js <repo> [methode]
//
// Lädt landing/js/holidays.js (und, falls vorhanden, landing/js/boersenkalender.js davor) in einen frischen
// Kontext, setzt SA.kalenderMethode = methode (Vorgabe 'alt') und gibt je Prüfgruppe eine Prüfsumme aus.
// Jeder Aufruf wird einzeln abgefangen: eine Ausnahme ist ein Ergebnis ("ERR:<Name>"), kein Abbruch.
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm'), crypto = require('crypto');

const repo = process.argv[2];
const methode = process.argv[3] || 'alt';
const ctx = { console: { log() {}, warn() {}, error() {} } };
ctx.window = ctx; ctx.globalThis = ctx;
ctx.SA = { __release() {}, kalenderMethode: methode };
vm.createContext(ctx);
const bundle = path.join(repo, 'landing/js/boersenkalender.js');
if (fs.existsSync(bundle)) vm.runInContext(fs.readFileSync(bundle, 'utf8'), ctx, { filename: 'boersenkalender.js' });
vm.runInContext(fs.readFileSync(path.join(repo, 'landing/js/holidays.js'), 'utf8'), ctx, { filename: 'holidays.js' });
const H = ctx.SA.holidays;

function r(fn) {
  try {
    const v = fn();
    return v === undefined ? 'undef' : JSON.stringify(v);
  } catch (e) {
    return 'ERR:' + (e && e.name ? e.name : typeof e);
  }
}
function h(teile) { return crypto.createHash('sha256').update(teile.join('\n')).digest('hex').slice(0, 24); }
const pad = (n) => (n < 10 ? '0' : '') + n;
const tageImMonat = (y, m) => [31, (y % 4 === 0 && (y % 100 !== 0 || y % 400 === 0)) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1];

const VON = 1990, BIS = 2035;
const BOERSEN = ['NYSE', 'XETRA', 'LSE', 'NONE', undefined, 'EURONEXT'];   // undefined = Vorgabe, EURONEXT = unbekannt für alt
const aus = { methode, gruppen: {} };
const g = aus.gruppen;

for (const b of BOERSEN) {
  const bn = String(b);
  for (let y = VON; y <= BIS; y++) {
    const offen = [], next = [], monat = [];
    for (let m = 1; m <= 12; m++) {
      const n = tageImMonat(y, m);
      for (let d = 1; d <= n; d++) {
        const ds = y + '-' + pad(m) + '-' + pad(d);
        offen.push(r(() => H.isTradingDay(ds, b)));
        next.push(r(() => H.nextTradingDay(y, m, d, b)));
      }
      next.push(r(() => H.nextTradingDay(y, m, 0, b)), r(() => H.nextTradingDay(y, m, n + 1, b)));
      for (const k of [-1, 0, 1, 2, 3, 5, 10, 15, 19, 20, 21, 22, 23, 24, 25]) {
        monat.push(r(() => H.nthTradingDay(y, m, k, b)), r(() => H.lastTradingDay(y, m, k, b)));
      }
      monat.push(r(() => H.lastTradingDay(y, m, undefined, b)));
    }
    const jahr = [];
    for (const k of [-1, 0, 1, 2, 100, 200, 240, 245, 248, 249, 250, 251, 252, 253, 254, 255, 260, 261, 262, 366, 367]) {
      jahr.push(r(() => H.nthTradingDayOfYear(y, k, b)));
    }
    g[bn + '|' + y] = [
      h([r(() => H.get(y, b))]), h([r(() => Object.keys(H.getMap(y, b)).sort())]),
      h(offen), h(next), h(monat), h(jahr),
    ];
  }
}

// Datumsarithmetik (bleibt in beiden Methoden)
const arith = [];
for (let y = VON; y <= BIS; y++) {
  arith.push(r(() => H.easter(y)), r(() => H.goodFriday(y)), r(() => H.easterMonday(y)), r(() => H.whitMonday(y)),
    r(() => H.thanksgiving(y)), r(() => H._ds(y, 3, 7)));
  for (let m = 1; m <= 12; m++) {
    for (let dow = 0; dow <= 6; dow++) {
      arith.push(r(() => H._lastDow(y, m, dow)));
      for (const n of [1, 2, 3, 4, 5]) arith.push(r(() => H._nthDow(y, m, dow, n)));
    }
  }
}
g['arithmetik'] = [h(arith)];

// Sonderlisten (unter alt lesbar)
g['sonderlisten'] = [h([r(() => H._NYSE_SONDER), r(() => H._XETRA_SONDER)])];

// detect: alle Ticker + Randfälle
const ticker = JSON.parse(fs.readFileSync(path.join(repo, 'landing/data/tickers.json'), 'utf8')).map((x) => x.t).sort();
const rand = ['', null, undefined, '^FOO', 'X.YY', 'btc-usd', 'eurusd=x', '11 Sektoren', 'AZN', 'ASML', 'ENR.F', 'NEL.OL',
  '^N225', '^HSI', '^KS11', 'SAP.DE', 'NVDA', 'GC=F', 'ES=F', 'FOO.BAR'];
g['detect'] = [h(ticker.map((t) => t + '=' + r(() => H.detect(t)))), h(rand.map((t) => String(t) + '=' + r(() => H.detect(t))))];

// Fehlerverhalten bei kaputten Eingaben
g['eingaben'] = [h([
  r(() => H.isTradingDay(undefined, 'NYSE')), r(() => H.isTradingDay('2026-02-30', 'NYSE')),
  r(() => H.isTradingDay('20260101', 'NYSE')), r(() => H.get('2026', 'NYSE')), r(() => H.nthTradingDay(2026, 13, 1, 'NYSE')),
  r(() => H.nthTradingDay(2026, 1, 1.5, 'NYSE')), r(() => H.nextTradingDay(2026, 12, 31, 'NYSE')),
  r(() => H.isTradingDay('1885-01-02', 'NYSE')), r(() => H.isTradingDay('2101-01-03', 'NYSE')),
])];

process.stdout.write(JSON.stringify(aus));

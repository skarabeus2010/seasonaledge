// Probe der Fassade SA.holidays unter der Methode 'kalender_v1' (Kalender V2, scripts/verify_holidays_fassade.py).
//
//   node scripts/js/holidays_fassade_probe.js <repo> < anfragen.json
//
// Lädt boersenkalender.js und holidays.js wie eine Seite (Bundle vor Fassade), SA.kalenderMethode = 'kalender_v1'.
// Eingabe: {"aufrufe": [[ziel, funktion, ...argumente], ...], "raster": {"von": J, "bis": J}}
//   ziel 'H' = SA.holidays, 'K' = SA.boersenkalender. Ergebnis je Aufruf: {"w": wert} oder {"e": Fehlername}.
//   Ein Argument "__undefined__" wird als undefined übergeben (ausgelassenes Argument).
// "raster": Delegationsvergleich Fassade = Bundle für jede öffentliche Funktion, jeden Tag, jede Börse.
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');

const repo = process.argv[2];
const eingabe = JSON.parse(fs.readFileSync(0, 'utf8'));
const ctx = { console: { log() {}, warn() {}, error() {} } };
ctx.window = ctx; ctx.globalThis = ctx;
ctx.SA = { __release() {}, kalenderMethode: 'kalender_v1' };
vm.createContext(ctx);
for (const f of ['landing/js/boersenkalender.js', 'landing/js/holidays.js']) {
  vm.runInContext(fs.readFileSync(path.join(repo, f), 'utf8'), ctx, { filename: f });
}
const H = ctx.SA.holidays, K = ctx.SA.boersenkalender;

function ruf(ziel, fn, args) {
  const o = ziel === 'H' ? H : K;
  try {
    // JSON kennt kein undefined: das Argument "__undefined__" steht für ein ausgelassenes Argument.
    args = args.map((a) => (a === '__undefined__' ? undefined : a));
    const v = typeof o[fn] === 'function' ? o[fn].apply(o, args) : o[fn];
    return { w: v === undefined ? '__undefined__' : JSON.parse(JSON.stringify(v)) };
  } catch (e) {
    return { e: (e && e.name) || typeof e };
  }
}

const aus = { ergebnisse: (eingabe.aufrufe || []).map((a) => ruf(a[0], a[1], a.slice(2))) };

if (eingabe.raster) {
  const pad = (n) => (n < 10 ? '0' : '') + n;
  const mt = (y, m) => [31, (y % 4 === 0 && (y % 100 !== 0 || y % 400 === 0)) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30,
    31, 30, 31][m - 1];
  const gleich = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  // Börsenliste und Ticker kommen aus der Eingabe (nicht aus dem Bundle abgeleitet).
  const abw = [];
  let n = 0;
  for (const b of eingabe.raster.boersen) {
    for (let y = eingabe.raster.von; y <= eingabe.raster.bis; y++) {
      if (!gleich(ruf('H', 'get', [y, b]), ruf('K', 'feiertagsmenge', [y, b]))) abw.push(['get', b, y]);
      n++;
      for (let m = 1; m <= 12; m++) {
        for (const k of [1, 2, 5, 10, 15, 19, 20, 21, 22, 23, 24]) {
          n += 2;
          if (!gleich(ruf('H', 'nthTradingDay', [y, m, k, b]), ruf('K', 'nteImMonat', [y, m, k, b]))) abw.push(['nth', b, y, m, k]);
          if (!gleich(ruf('H', 'lastTradingDay', [y, m, k, b]), ruf('K', 'nteVonHintenImMonat', [y, m, k, b]))) abw.push(['last', b, y, m, k]);
        }
        for (let d = 1; d <= mt(y, m); d++) {
          const ds = y + '-' + pad(m) + '-' + pad(d);
          n += 2;
          if (!gleich(ruf('H', 'isTradingDay', [ds, b]), ruf('K', 'istHandelstag', [ds, b]))) abw.push(['offen', b, ds]);
          if (!gleich(ruf('H', 'nextTradingDay', [y, m, d, b]), ruf('K', 'naechste', [ds, b, true]))) abw.push(['next', b, ds]);
        }
      }
      for (const k of [1, 100, 240, 245, 248, 250, 252, 254, 260, 365, 366]) {
        n++;
        if (!gleich(ruf('H', 'nthTradingDayOfYear', [y, k, b]), ruf('K', 'nteImJahr', [y, k, b]))) abw.push(['jahr', b, y, k]);
      }
    }
  }
  for (const t of eingabe.raster.ticker) {
    n++;
    if (!gleich(ruf('H', 'detect', [t]), ruf('K', 'boerse', [t]))) abw.push(['detect', t]);
  }
  aus.raster = { vergleiche: n, abweichungen: abw.length, beispiele: abw.slice(0, 10) };
}

process.stdout.write(JSON.stringify(aus));

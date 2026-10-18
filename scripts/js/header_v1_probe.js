// Probe des Headers unter 'kalender_v1' (SA._headerKalenderV1 aus landing/js/app.js) mit injizierter Uhr.
//
//   node scripts/js/header_v1_probe.js <repo> < faelle.json     faelle: [[uhr_iso, ticker, kalenderTicker|null, en], …]
//
// Lädt boersenkalender.js + holidays.js und aus app.js genau die Funktion SA._headerKalenderV1 (app.js braucht
// sonst ein DOM). Ausgabe: Liste der Headertexte.
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const repo = process.argv[2];
const faelle = JSON.parse(fs.readFileSync(0, 'utf8'));
const ctx = { console: { log() {}, warn() {}, error() {} } };
ctx.window = ctx; ctx.globalThis = ctx;
ctx.SA = { __release() {}, kalenderMethode: 'kalender_v1' };
vm.createContext(ctx);
for (const f of ['landing/js/boersenkalender.js', 'landing/js/holidays.js']) {
  vm.runInContext(fs.readFileSync(path.join(repo, f), 'utf8'), ctx, { filename: f });
}
const app = fs.readFileSync(path.join(repo, 'landing/js/app.js'), 'utf8');
const von = app.indexOf('SA._headerKalenderV1 = function'), bis = app.indexOf('// ── Sortable Tables');
if (von < 0 || bis < von) throw new Error('SA._headerKalenderV1 nicht gefunden');
vm.runInContext(app.slice(von, bis), ctx, { filename: 'app.js#_headerKalenderV1' });
const en = JSON.parse(fs.readFileSync(path.join(repo, 'landing/i18n/en.json'), 'utf8'));
ctx.SA.i18n = { t: (k, de) => (k in en ? en[k] : de) };
const aus = faelle.map(([uhr, ticker, kt, isEN]) => {
  ctx.SA.__uhr = () => Date.parse(uhr);
  const el = {};
  ctx.SA._headerKalenderV1(el, ticker, kt || undefined, !!isEN);
  return el.textContent;
});
process.stdout.write(JSON.stringify(aus));

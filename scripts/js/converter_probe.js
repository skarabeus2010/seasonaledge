// Probe des Trading Day Converters (seo/tools/trading-day-converter.html) — Kalender V2, Schritt 6.
//
//   node scripts/js/converter_probe.js <repo> <methode> < daten.json     daten: [["YYYY-MM-DD", boerse|null], …]
//
// Führt die Inline-Skripte der AUSGELIEFERTEN Seite (nginx liefert /tools/ direkt aus seo/tools/) in einem
// Minimal-DOM aus; lädt boersenkalender.js nur, wenn die Seite es einbindet. Ausgabe: innerHTML/textContent von
// #result je Datum.
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const repo = process.argv[2], methode = process.argv[3] || 'alt';
const daten = JSON.parse(fs.readFileSync(0, 'utf8'));
const html = fs.readFileSync(path.join(repo, 'seo/tools/trading-day-converter.html'), 'utf8');

const elemente = {};
function element(id) {
  if (!elemente[id]) {
    // textContent und innerHTML überschreiben sich gegenseitig wie im echten DOM
    let inhalt = '';
    elemente[id] = { id, value: '', style: {}, hidden: false, _l: {},
      get textContent() { return inhalt.replace(/<[^>]*>/g, ''); }, set textContent(v) { inhalt = String(v).replace(/</g, '&lt;'); },
      get innerHTML() { return inhalt; }, set innerHTML(v) { inhalt = String(v); },
      addEventListener(t, f) { (this._l[t] = this._l[t] || []).push(f); },
      dispatch(t) { (this._l[t] || []).forEach((f) => f({ target: this })); } };
  }
  return elemente[id];
}
const ctx = { console: { log() {}, warn() {}, error() {} } };
ctx.window = ctx; ctx.globalThis = ctx;
ctx.document = { getElementById: element, querySelector: () => null, querySelectorAll: () => [] };
ctx.SA = { __release() {}, kalenderMethode: methode };
element('boerse').value = 'NYSE';   // wie ein echtes <select>: erste Option vorgewählt
vm.createContext(ctx);
if (/<script[^>]*src="\/landing\/js\/boersenkalender\.js/.test(html)) {
  vm.runInContext(fs.readFileSync(path.join(repo, 'landing/js/boersenkalender.js'), 'utf8'), ctx);
}
// Inline-Skripte (ohne src, ohne JSON-LD), in Reihenfolge
const inline = [...html.matchAll(/<script(?![^>]*\bsrc=)(?![^>]*application\/ld\+json)[^>]*>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
for (const code of inline) {
  // Bootstrap-Zeile setzt __SA_RELEASE/__SA_METHODE — die Methode der Probe gilt
  if (/__SA_RELEASE/.test(code)) continue;
  vm.runInContext(code, ctx);
}
const aus = daten.map(([ds, boerse]) => {
  const p = element('datepicker');
  p.value = ds;
  if (boerse !== null) { element('boerse').value = boerse; element('boerse').dispatch('change'); }
  p.dispatch('change');
  const r = element('result');
  return r.innerHTML;
});
process.stdout.write(JSON.stringify(aus));

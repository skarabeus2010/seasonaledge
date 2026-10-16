/**
 * true_seasonal_probe.js — Williams True Seasonal auf dem ECHTEN Code (Plan v3:
 * docs/review_prompts/2026-10-16_true_seasonal_plan_v3.md).
 *
 * Führt landing/js/seasonal-compute.js und outlier.js aus und zieht aus jahreszyklus.html den Builder
 * (buildExtendedYearData), applyOutlierFilter und trueSeasonalModell. Die Fälle (Kurszeilen) erzeugt
 * verify_seasonal_twins.py (Block 8) und vergleicht die Ausgabe mit shared/true_seasonal.py und mit fachlichen Sollwerten.
 *
 * Aufruf: node scripts/js/true_seasonal_probe.js <seasonal-compute.js> <outlier.js> <jahreszyklus.html> <faelle.json>
 */
const fs = require('fs');
const window = {};
require('./release_harness').bereite(window);
new Function('window', fs.readFileSync(process.argv[2], 'utf8') + '\nreturn window.SA;')(window);
const SA = window.SA;
SA.i18n = { t: (k, fb) => fb || k, isEN: () => false };
new Function('window', fs.readFileSync(process.argv[3], 'utf8'))(window);
const jzHtml = fs.readFileSync(process.argv[4], 'utf8');
const eingabe = JSON.parse(fs.readFileSync(process.argv[5], 'utf8'));

function zieheBlock(html, kopf) {
  const start = html.indexOf(kopf);
  if (start < 0) throw new Error(kopf + ' nicht gefunden');
  let i = html.indexOf('{', start + kopf.length - 1), tiefe = 0;
  for (; i < html.length; i++) {
    if (html[i] === '{') tiefe++;
    else if (html[i] === '}' && --tiefe === 0) break;
  }
  return html.substring(start, i + 1);
}
const seite = new Function('SA', ['function buildExtendedYearData(', 'function applyOutlierFilter(',
  'function trueSeasonalModell('].map(k => zieheBlock(jzHtml, k)).join('\n') +
  '\nreturn { build: buildExtendedYearData, modell: trueSeasonalModell };')(SA);

const S = SA.seasonal, aus = {};
for (const f of eingabe.faelle) {
  const ydG = S.buildYearData(f.rows), ydS = seite.build(f.rows);
  const e = { jahre: {}, ts: {}, rueckblick: {}, modellwahl: {} };
  const alle = new Set([...Object.keys(ydG), ...Object.keys(ydS)]);
  for (const y of alle) {
    const g = ydG[y], s = ydS[y];
    let gleich = !!g === !!s;
    if (g && s) for (let d = 0; d < 365 && gleich; d++) gleich = Math.abs(g.full_365[d] - s.full_365[d]) <= 1e-9;
    e.jahre[y] = { gemeinsam: !!g, seite: !!s, gleich: gleich,
                   voll: g ? S.jahrVollstaendig(g, +y, f.stichtag) : null,
                   voll_seite: s ? S.jahrVollstaendig(s, +y, f.stichtag) : null,
                   full: g ? g.full_365 : null,
                   aend: s ? S.monatsAenderungen(s.full_365) : null };
  }
  for (const [ziel, n] of f.ts_auftraege) {
    const j = S.trueSeasonalJahre(ydS, ziel, n);
    e.ts[ziel + '|' + n] = { jahre: j, kurve: S.mittelKurve(ydS, j) };
  }
  for (const n of f.fenster) {
    e.rueckblick[String(n)] = S.rueckblick(ydS, f.stichtag, n);
    const w = seite.modell(ydS, f.stichtag, n, f.methode || 'off');
    e.modellwahl[String(n)] = { jahre: Object.keys(w.modell).map(Number).sort((a, b) => a - b), n: w.n,
                                mindest: w.mindest, ok: w.ok };
  }
  aus[f.name] = e;
}
// Kennzahl: konstante Reihe -> r null; Treffer zählt 0 nicht; Vorzeichen.
const flach = new Array(365).fill(100), auf = Array.from({ length: 365 }, (_, i) => 100 + i / 10);
aus._kennzahl = { konstant: S.vergleich12(flach, auf), flach: S.vergleich12(flach, flach), gleich: S.vergleich12(auf, auf) };
// analytischer Fall: Kurven mit vorgegebenen zwölf Änderungen (Python berechnet Soll unabhängig)
if (eingabe.kennzahl) {
  aus._kennzahl.analytisch = S.vergleich12(eingabe.kennzahl.ist, eingabe.kennzahl.modell);
  aus._kennzahl.aenderungen_ist = S.monatsAenderungen(eingabe.kennzahl.ist);
}
process.stdout.write(JSON.stringify(aus));

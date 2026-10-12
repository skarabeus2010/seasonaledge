// Probe für scripts/verify_sitzungen.py — führt die ECHTE landing/js/boersenkalender.js aus (Sitzungshelfer V1d).
// Aufruf: node probe_sitzungen.js <Zeitzone> <Auftrag.json>
// Raster je Börse als kompakte Zeichenketten: je Tag die Tagesabstände der vier Suchen (naechste/vorherige ×
// einschließlich/strikt), 'E' für gewollten Fehler, 'X' für Absturz.
'use strict';
process.env.TZ = process.argv[2];
const fs = require('fs');
const path = require('path');
const A = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const offsets = [new Date(2026, 0, 15).getTimezoneOffset(), new Date(2026, 6, 15).getTimezoneOffset()];
global.window = {};
require('./release_harness').bereite(global.window);
require(path.join(__dirname, '..', '..', 'landing', 'js', 'boersenkalender.js'));
const K = global.window.SA.boersenkalender;

function tag(iso) { return Date.UTC(+iso.slice(0, 4), +iso.slice(5, 7) - 1, +iso.slice(8, 10)) / 86400000; }
function art(f) {
  try { return { ok: f() }; } catch (e) { return { fehler: (e instanceof K.Fehler) ? 'api' : 'absturz', text: String(e && e.message) }; }
}
function abstand(f, basis) {
  try { return String(tag(f()) - basis); } catch (e) { return (e instanceof K.Fehler) ? 'E' : 'X'; }
}

const out = { zone: process.argv[2], offsets: offsets, raster: {}, sitzungen: {}, verschiebe: {}, positionen: {}, faelle: [] };
if (A.raster) {
  for (const b of A.raster.boersen) {
    const teile = [];
    for (const d of A.raster.tage) {
      const t = tag(d);
      teile.push([abstand(() => K.naechste(d, b, true), t), abstand(() => K.naechste(d, b, false), t),
                  abstand(() => K.vorherige(d, b, true), t), abstand(() => K.vorherige(d, b, false), t)].join(','));
    }
    out.raster[b] = teile.join(';');
    out.sitzungen[b] = K.sitzungen(A.raster.tage[0], A.raster.tage[A.raster.tage.length - 1], b).join(';');
    const v = [];
    for (const [d, n] of A.verschiebe[b]) v.push(abstand(() => K.verschiebe(d, n, b), tag(d)));
    out.verschiebe[b] = v.join(';');
    const p = [];
    for (const c of A.positionen[b]) {
      const r = art(() => c[0] === 'm' ? K.nteImMonat(c[1], c[2], c[3], b)
                         : c[0] === 'h' ? K.nteVonHintenImMonat(c[1], c[2], c[3], b) : K.nteImJahr(c[1], c[3], b));
      p.push('ok' in r ? (r.ok === null ? 'N' : r.ok) : (r.fehler === 'api' ? 'E' : 'X'));
    }
    out.positionen[b] = p.join(';');
  }
}
for (const c of A.faelle || []) {
  const f = K[c.f];
  out.faelle.push(art(() => {
    const r = f.apply(null, c.a);
    return (r && typeof r === 'object' && !Array.isArray(r)) ? Object.assign({}, r) : r;
  }));
}
process.stdout.write(JSON.stringify(out));
process.stdout.write('\nPROBE-ENDE\n');

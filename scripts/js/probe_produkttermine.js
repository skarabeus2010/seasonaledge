// Probe für scripts/verify_produkttermine.py — führt die ECHTE landing/js/boersenkalender.js aus.
// Aufruf: node probe_produkttermine.js <Zeitzone> <Auftrag.json>   (Auftrag: {pruefdaten: [...]})
'use strict';
process.env.TZ = process.argv[2];
const fs = require('fs');
const path = require('path');
const auftrag = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const offsets = [new Date(2026, 0, 15).getTimezoneOffset(), new Date(2026, 6, 15).getTimezoneOffset()];
global.window = {};
require('./release_harness').bereite(global.window);
require(path.join(__dirname, '..', '..', 'landing', 'js', 'boersenkalender.js'));
const K = global.window.SA.boersenkalender;

function art(f) {
  try { f(); return 'kein_fehler'; } catch (e) { return (e instanceof K.Fehler) ? 'api' : 'absturz'; }
}
const out = { zone: process.argv[2], offsets: offsets, produktversion: K.produktversion, je: {},
  fehler: { ohne_pruefdatum: art(() => K.produkttermine('2025-01', '2025-12', 'opex')),
            ohne_pruefdatum_abdeckung: art(() => K.abdeckung()),
            falsche_art: art(() => K.produkttermine('2025-01', '2025-12', 'foo', '2026-10-12')),
            nach_bereich: art(() => K.produkttermine('2100-12', '2100-12', 'vix', '2026-10-12')) } };
for (const p of auftrag.pruefdaten) {
  out.je[p] = { opex: K.produkttermine('2015-01', '2100-12', 'opex', p), vix: K.produkttermine('2015-01', '2100-11', 'vix', p),
                abdeckung: K.abdeckung(p) };
}
const e = K.produkttermine('2025-04', '2025-04', 'opex', '2026-10-12')[0];
let eingefroren = Object.isFrozen(e);
try { e.verfallstermin = '1900-01-01'; } catch (x) { /* strict */ }
out.eingefroren = eingefroren && K.produkttermine('2025-04', '2025-04', 'opex', '2026-10-12')[0].verfallstermin !== '1900-01-01';
process.stdout.write(JSON.stringify(out));
process.stdout.write('\nPROBE-ENDE\n');

// Probe für scripts/verify_boersenereignisse.py — führt die ECHTE landing/js/boersenkalender.js aus und gibt den
// vollständigen Ereigniskatalog, die Schließungsprojektion, die Identität und die Versionen als JSON aus.
// Aufruf: node probe_boersenereignisse.js <Zeitzone> <Auftrag.json>   (Auftrag: {boersen, von, bis})
'use strict';
process.env.TZ = process.argv[2];
const fs = require('fs');
const path = require('path');
const auftrag = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));

const offsets = [new Date(2026, 0, 15).getTimezoneOffset(), new Date(2026, 6, 15).getTimezoneOffset()];
global.window = {};
require('./release_harness').bereite(global.window);   // echte methode.js zuerst (Releasekennung, V1b)
require(path.join(__dirname, '..', '..', 'landing', 'js', 'boersenkalender.js'));
const K = global.window.SA.boersenkalender;

const out = { zone: process.argv[2], offsets: offsets, ereignisversion: K.ereignisversion,
              kalenderversion: K.kalenderversion, boersen: {} };
for (const b of auftrag.boersen) {
  const r = { ereignisse: {}, schliessungen: {}, identitaet: {}, halbtag_status: {} };
  for (let j = auftrag.von; j <= auftrag.bis; j++) {
    const liste = K.ereignisse(j, b);
    if (liste.length) r.ereignisse[j] = liste.map(e => Object.assign({}, e));
    const s = K.schliessungen(j, b);
    if (s.length) r.schliessungen[j] = s;
    r.identitaet[j] = K.identitaet(b, j);
    r.halbtag_status[j] = K.halbtag_status(b, j);
  }
  out.boersen[b] = r;
}
// Alias und Unveränderlichkeit
const nasdaq = K.ereignisse(2025, 'NASDAQ'), nyse = K.ereignisse(2025, 'NYSE');
out.alias_gleich = JSON.stringify(nasdaq) === JSON.stringify(nyse);
let eingefroren = true;
try { nyse[0].wirksam = '1900-01-01'; } catch (e) { /* strict: TypeError erwartet */ }
if (K.ereignisse(2025, 'NYSE')[0].wirksam === '1900-01-01') eingefroren = false;
out.eingefroren = eingefroren && Object.isFrozen(K.ereignisse(2025, 'NYSE')[0]);
process.stdout.write(JSON.stringify(out));
process.stdout.write('\nPROBE-ENDE\n');

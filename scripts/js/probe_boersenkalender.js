// Probe für scripts/verify_boersenkalender_js.py — führt die ECHTE landing/js/boersenkalender.js aus.
// Aufruf: node probe_boersenkalender.js <Zeitzone> <Auftrag.json>   → JSON auf stdout
// Die Zone wird VOR jeder Date-Nutzung und vor dem Laden gesetzt (Codex R6, Antwort 3); der Nachweis,
// dass sie wirkt, geht als Januar-/Juli-Offset mit zurück.
'use strict';
process.env.TZ = process.argv[2];
const fs = require('fs');
const path = require('path');
const auftrag = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));

const offsets = [new Date(2026, 0, 15).getTimezoneOffset(), new Date(2026, 6, 15).getTimezoneOffset()];
global.window = {};
require(path.join(__dirname, '..', '..', 'landing', 'js', 'boersenkalender.js'));
const K = global.window.SA.boersenkalender;

// Art jeder Ausnahme über die KLASSE: 'api' = gewollter KalenderFehler, 'absturz' = alles andere.
function versuch(f) {
  try { return { ok: f() }; } catch (e) {
    return { fehler: String((e && e.message) || e), art: (e instanceof K.Fehler) ? 'api' : 'absturz' };
  }
}

const out = { zone: process.argv[2], offsets: offsets, version: K.version, ergebnisse: {} };
for (const [name, a] of Object.entries(auftrag)) {
  if (a.art === 'tage') {
    // alle Kalendertage eines Bereichs: offen + nummern je Börse, kompakt als Zeichenkette
    const r = {};
    for (const b of a.boersen) {
      const n = K.nummern(a.daten, b);
      r[b] = n.map(x => (x.offen ? 1 : 0) + ':' + x.tdom + ':' + x.tdoy + ':' + x.tdom_rev + ':' + x.tdoy_rev).join(',');
      r[b + '|ist'] = a.daten.map(d => (K.istHandelstag(d, b) ? 1 : 0)).join('');
    }
    out.ergebnisse[name] = r;
  } else if (a.art === 'aufrufe') {
    out.ergebnisse[name] = a.aufrufe.map(c => versuch(() => K[c[0]].apply(null, c.slice(1))));
  }
}
process.stdout.write(JSON.stringify(out));

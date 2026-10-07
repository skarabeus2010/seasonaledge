/* Führt landing/js/wahlen-compute.js (die echte Datei, keine Kopie) auf einer Studie aus.

   Aufruf: node probe_wahlen.js <studie.json> <optionen.json>
   Ausgabe: JSON-Liste der Ergebnisse je Optionssatz (kurven, kennzahlen, live, offsets,
   ausgeschlossen-Zahl) — verglichen von scripts/verify_wahlen_twin.py gegen Python. */
const fs = require('fs');
const path = require('path');

global.window = {};
// WAHLEN_JS erlaubt dem Mutationstest, eine veränderte Kopie zu laden.
require(process.env.WAHLEN_JS || path.resolve(__dirname, '..', '..', 'landing', 'js', 'wahlen-compute.js'));
const W = global.window.SA.wahlen;

const st = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const optionen = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const aus = optionen.map((o) => {
  const r = W.auswerten(st, o);
  return {
    opts: o, kurven: r.kurven, kennzahlen: r.kennzahlen, live: r.live, offsets: r.offsets,
    ausgeschlossen: r.ausgeschlossen,
    einzel: r.wahlen.map((e) => ({ id: e.id, t0: e.t0, kurve: e.kurve, nachlauf: e.nachlauf,
                                  vorlauf: e.vorlauf, fenster: e.fenster, basisDatum: e.basisDatum })),
  };
});
process.stdout.write(JSON.stringify(aus));

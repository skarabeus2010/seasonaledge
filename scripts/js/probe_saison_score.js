/**
 * probe_saison_score.js — führt die ECHTE landing/js/saison-score.js aus (mit seasonal-compute.js und
 * decade-compute.js, wie auf den Seiten).
 *
 * Aufruf: node scripts/js/probe_saison_score.js <seasonal-compute.js> <decade-compute.js> <saison-score.js> <eingabe.json>
 *   eingabe.json: {reihen: {name: [{date, close}]}, faelle: [{id, ticker, reihe | rows, as_of?}]}
 *   stdout: {faelle: [{id, ergebnis} | {id, fehler}], rundung: [...]}   (eingabe.rundung: Zahlen für _runden1)
 */
const fs = require('fs');
const window = { location: { pathname: '/' } };
for (const datei of process.argv.slice(2, 5)) {
  new Function('window', fs.readFileSync(datei, 'utf8') + '\nreturn window.SA;')(window);
}
const SA = window.SA;
const ein = JSON.parse(fs.readFileSync(process.argv[5], 'utf8'));
const reihen = ein.reihen || {};
const out = (ein.faelle || []).map(f => {
  try {
    const e = SA.saisonScore.berechne(f.rows || reihen[f.reihe], f.ticker, f.as_of ? { as_of: f.as_of } : undefined);
    return { id: f.id, ergebnis: e };
  } catch (err) {
    return { id: f.id, fehler: String(err && err.message || err) };
  }
});
const rundung = (ein.rundung || []).map(x => SA.saisonScore._runden1(x));
process.stdout.write(JSON.stringify({ faelle: out, rundung }));

/**
 * probe_stress_ampel.js — führt die ECHTE landing/js/dash-compute.js aus und gibt die Stress-Reihe für vorgegebene
 * Eingaben aus (Zwillingsvergleich mit shared/stress_score.py im Wächter scripts/verify_stress_ampel.py).
 *
 *   node scripts/js/probe_stress_ampel.js <basisordner> <eingabe.json>
 *
 * eingabe.json: {faelle: {name: [{date, close}, …]}, anzeige: [{name, db: [...], n}]}
 * Ausgabe: eine JSON-Zeile {reihen: {name: [[date, score, s, ampel, vol5, vol20, dd20, referenz_n], …]},
 *          aktuell: {name: {...}}, anzeige: {name: {quelle, daten}}, hilfs: {...}} und als letzte Zeile ENDE.
 */
const fs = require('fs');
const path = require('path');
const BASIS = path.resolve(process.argv[2]);
const window = {};
new Function('window', 'var SA = window.SA || {};\n' + fs.readFileSync(path.join(BASIS, 'landing/js/dash-compute.js'), 'utf8') + '\nwindow.SA = SA;')(window);
const D = window.SA.dashCompute;
if (!D || !D.stressReihe || !D.computeStress || !D.stressAnzeigeWerte) throw new Error('[Aufbau] dash-compute.js ohne Stress-Funktionen');
const ein = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const out = { reihen: {}, aktuell: {}, anzeige: {}, hilfs: {} };
for (const [name, rows] of Object.entries(ein.faelle || {})) {
  out.reihen[name] = D.stressReihe(rows).map(z => [z.date, z.score, z.s, z.ampel, z.vol5, z.vol20, z.dd20, z.referenz_n]);
  const a = D.computeStress(rows);
  out.aktuell[name] = { status: a.status, date: a.date || null, score: a.risk_score, ampel: a.traffic_light, anzeige: a.anzeige,
                        n_kurse: a.n_kurse };
}
for (const fall of (ein.anzeige || [])) {
  const r = D.stressAnzeigeWerte(D.stressReihe(ein.faelle[fall.reihe]), fall.db, fall.n);
  out.anzeige[fall.name] = { quelle: r.quelle, scores: r.zeilen.map(z => [z.date, z.score]) };
}
out.hilfs.ampel = [69.99999, 70, 89.96, 90, null].map(D.stressAmpel);
out.hilfs.anzeige = [89.96, 90, 69.99999, Math.fround(89.96), 25.753968253968253].map(D.stressAnzeige);
out.hilfs.konstanten = D.STRESS;
process.stdout.write(JSON.stringify(out) + '\nENDE\n');

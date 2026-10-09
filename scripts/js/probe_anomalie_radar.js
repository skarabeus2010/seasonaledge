/**
 * probe_anomalie_radar.js — führt die ECHTE landing/js/decade-compute.js aus (Anomalie-Radar, Plan v3 Teil C).
 *
 * Aufruf: node scripts/js/probe_anomalie_radar.js <decade-compute.js> <eingabe.json> [en.json]
 *   eingabe.json: {reihen: {name: [{date,close}]}, faelle: [{id, ticker, reihe | rows, as_of?, ohne_html?, en?}],
 *                  status_z: [z, …]}
 *   stdout: {faelle: [{id, ergebnis, html_zeile?, html_karte?}], status: [[z, status], …]}
 *   Reihen nur einmal übergeben (sonst ERR_STRING_TOO_LONG). `en: true` rendert mit en.json (englische Seite).
 * Ein Wurf in anomalie() (z. B. fehlender Ticker) wird als {fehler} zurückgegeben, nicht verschluckt.
 */
const fs = require('fs');
const window = { location: { pathname: '/' } };
// Minimaler DOM-Stub: zählt, ob die Darstellung ihr CSS selbst einbindet (Dashboard ruft nur anomalieHtml).
const styles = [];
global.document = { head: { appendChild: el => styles.push(el.id) },
  getElementById: id => (styles.indexOf(id) >= 0 ? {} : null),
  createElement: () => ({}) };
const SA = new Function('window', fs.readFileSync(process.argv[2], 'utf8') + '\nreturn window.SA;')(window);
const ein = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const EN = process.argv[4] ? JSON.parse(fs.readFileSync(process.argv[4], 'utf8')) : {};
const reihen = ein.reihen || {};
const faelle = (ein.faelle || []).map(f => {
  try {
    SA.i18n = f.en ? { isEN: () => true, t: (k, d) => (k in EN ? EN[k] : d) } : undefined;
    const rows = f.rows || reihen[f.reihe];
    const e = SA.decadeCompute.anomalie(rows, f.ticker, f.as_of ? { as_of: f.as_of } : undefined);
    const o = { id: f.id, ergebnis: e };
    if (!f.ohne_html) {
      o.html_zeile = SA.decadeCompute.anomalieHtml(e, f.ticker, 'zeile');
      o.html_karte = SA.decadeCompute.anomalieHtml(e, f.ticker, 'karte');
    }
    return o;
  } catch (err) {
    return { id: f.id, fehler: String(err && err.message || err) };
  }
});
const status = (ein.status_z || []).map(z => [z, SA.decadeCompute.anomalieStatus(z)]);
process.stdout.write(JSON.stringify({ faelle, status, css: styles }));

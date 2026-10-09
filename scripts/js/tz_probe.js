/**
 * tz_probe.js — Tagesnummern und Jahreskurven unabhängig von der Zeitzone? (Schritt U, 2026-10-09)
 *
 * Führt die ECHTEN landing/js/seasonal-compute.js und decade-compute.js unter einer vorgegebenen Zeitzone aus und
 * gibt Tagesnummern aller Tage 1990–2035 sowie eine Jahreskurve als JSON aus. verify_seasonal_twins.py ruft das unter
 * mehreren Zeitzonen auf und vergleicht gegen pandas `dayofyear`.
 *
 * Hintergrund: `new Date("YYYY-MM-DD")` ist UTC-Mitternacht, `new Date(jahr, 0, 0)` LOKALE Mitternacht. Westlich von
 * UTC lag damit jede Tagesnummer um eins daneben (in New York bekam der 1. Januar Tag 365).
 *
 * Aufruf: node scripts/js/tz_probe.js <zeitzone> <seasonal-compute.js> <decade-compute.js> [seite.html …]
 * Die Zeitzone wird IM Prozess gesetzt (Git Bash biegt TZ=Europe/Berlin sonst als Pfad um).
 */
process.env.TZ = process.argv[2];
const fs = require('fs');
const window = {};
new Function('window', fs.readFileSync(process.argv[3], 'utf8') + '\nreturn window.SA;')(window);
const SA = window.SA;
new Function('window', 'SA', fs.readFileSync(process.argv[4], 'utf8') + '\nreturn window.SA;')(window, SA);

const tageSeasonal = [], tageDecade = [];
for (let t = Date.UTC(1990, 0, 1); t <= Date.UTC(2035, 11, 31); t += 86400000) {
  const iso = new Date(t).toISOString().substring(0, 10);
  tageSeasonal.push(SA.seasonal.tagNummer(iso));
  tageDecade.push(SA.decadeCompute._dayOfYear(iso));
}

// Jahreskurve: 40 Handelstage ab 02.01.2023 (Mo–Fr), +1 % je Tag — Tagesachse muss überall gleich sein
const rows = [];
let c = 100;
for (let t = Date.UTC(2023, 0, 2), n = 0; n < 40; t += 86400000) {
  const wt = new Date(t).getUTCDay();
  if (wt === 0 || wt === 6) continue;
  rows.push({ date: new Date(t).toISOString().substring(0, 10), close: c, log_return: n ? Math.log(1.01) : null });
  c *= 1.01; n++;
}
const yd = SA.seasonal.buildYearData(rows);

// Die Inline-Kopien buildExtendedYearData (jahreszyklus.html, risikozyklus.html) direkt aus der Seite gezogen:
// Codex U+C R1 — der erste Kurstag rechnete dort weiter gegen lokale Mitternacht (New York: Tag 365 statt 1).
function zieheFunktion(html, name) {
  const start = html.indexOf('function ' + name + '(');
  if (start < 0) throw new Error(name + ' nicht gefunden');
  let i = html.indexOf('{', start), tiefe = 0;
  for (; i < html.length; i++) {
    if (html[i] === '{') tiefe++;
    else if (html[i] === '}' && --tiefe === 0) break;
  }
  return html.substring(start, i + 1);
}
const extra = {};
const januar = [];   // 20 Kalendertage ab 01.01.2023 (inkl. Wochenende, wie im Codex-Fall), Schlusskurse 100…119
for (let k = 0; k < 20; k++) januar.push({ date: '2023-01-' + String(k + 1).padStart(2, '0'), close: 100 + k, log_return: k ? Math.log((100 + k) / (99 + k)) : null });
for (const seite of process.argv.slice(5)) {
  const fn = new Function('SA', zieheFunktion(fs.readFileSync(seite, 'utf8'), 'buildExtendedYearData') + '\nreturn buildExtendedYearData;')(SA);
  const e1 = fn(rows), e2 = fn(januar);
  extra[seite.split(/[\\/]/).pop()] = {
    w: e1[2023] ? { lad: e1[2023].last_actual_day, k: e1[2023].full_365.slice(0, 70) } : null,
    jan: e2[2023] ? { lad: e2[2023].last_actual_day, k: [e2[2023].full_365[0], e2[2023].full_365[20], e2[2023].full_365[364]] } : null,
  };
}
process.stdout.write(JSON.stringify({
  tz: process.env.TZ,
  offset_jan: new Date(2023, 0, 15).getTimezoneOffset(),
  tage_seasonal: tageSeasonal,
  tage_decade: tageDecade,
  kurve_2023: yd[2023] ? { lad: yd[2023].last_actual_day, k: yd[2023].full_365.slice(0, 70) } : null,
  extra: extra,
}));

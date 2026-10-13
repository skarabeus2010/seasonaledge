/**
 * zyklus_probe.js — Jahresende-Regel, Präsidentenzyklus-Signifikanz, Schaltjahr und Heatmap auf dem ECHTEN Code
 * (Plan docs/review_prompts/2026-10-13_zyklus_signifikanz_plan_v3.md).
 *
 * Führt landing/js/seasonal-compute.js und significance.js aus und zieht die Inline-Funktionen direkt aus
 * jahreszyklus.html / risikozyklus.html (buildExtendedYearData, periodStats, buildMonthlyHeatmap,
 * JZ.renderSignificance). Der Stichtag wird injiziert — das Ergebnis hängt nicht vom Rechnerdatum ab.
 * verify_seasonal_twins.py (Block 7) bewertet die Ausgabe gegen fachliche Erwartungen und gegen Python.
 *
 * Aufruf: node scripts/js/zyklus_probe.js <seasonal-compute.js> <significance.js> <jahreszyklus.html> <risikozyklus.html>
 */
const fs = require('fs');
const window = {};
require('./release_harness').bereite(window);   // echte methode.js zuerst (Releasekennung)
new Function('window', fs.readFileSync(process.argv[2], 'utf8') + '\nreturn window.SA;')(window);
const SA = window.SA;
SA.i18n = { t: (k, fb) => fb || k, isEN: () => false };
new Function('window', 'SA', fs.readFileSync(process.argv[3], 'utf8') + '\nreturn window.SA;')(window, SA);
const jzHtml = fs.readFileSync(process.argv[4], 'utf8');
const rzHtml = fs.readFileSync(process.argv[5], 'utf8');

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
function zieheZeile(html, kopf) {
  const start = html.indexOf(kopf);
  if (start < 0) throw new Error(kopf + ' nicht gefunden');
  return html.substring(start, html.indexOf('\n', start));
}
const konst = ['var MONTHS_DE =', 'var MONTH_BOUNDS =', 'var QUARTER_BOUNDS =', 'var CYCLE_LABELS ='].map(k => zieheZeile(jzHtml, k)).join('\n');
const funkt = ['function _clean(', 'function mean(', 'function median(', 'function cycleOf(', 'function periodStats(',
  'function buildMonthlyHeatmap(', 'function buildExtendedYearData('].map(k => zieheBlock(jzHtml, k)).join('\n');
const dom = {};
const document = { getElementById: (id) => (dom[id] = dom[id] || { innerHTML: '', style: {} }) };
const JZ = new Function('SA', 'document', konst + '\n' + funkt + '\n' +
  'var JZ = { cycleOf: cycleOf };\n' + zieheBlock(jzHtml, 'JZ.renderSignificance = function(') + ';\n' +
  'return { JZ: JZ, periodStats: periodStats, buildMonthlyHeatmap: buildMonthlyHeatmap, buildExtendedYearData: buildExtendedYearData };'
)(SA, document);
const rzBuild = new Function('SA', zieheBlock(rzHtml, 'function buildExtendedYearData(') + '\nreturn buildExtendedYearData;')(SA);

const S = SA.seasonal, erg = {};

// 1) yearCovers — Fälle [lad, endDoy, jahr, stichtagJahr]; Python rechnet dieselben Fälle mit year_covers.
erg.yearcovers_faelle = [
  [365, 365, 2025, 2026], [363, 365, 2023, 2026], [364, 365, 2025, 2026],  // Jahresende 365/363 (NYSE), 364 (XETRA)
  [362, 365, 2024, 2026], [359, 365, 2024, 2026], [358, 365, 2024, 2026],  // Toleranzgrenze 359
  [365, 365, 2026, 2026], [364, 365, 2026, 2026], [359, 365, 2026, 2026],  // laufendes Jahr nie
  [365, 365, 2027, 2026],                                                  // zukünftiges Jahr nie
  [181, 181, 2026, 2026], [180, 181, 2026, 2026], [280, 31, 2026, 2026],   // abgeschlossene Monate des laufenden Jahres
  [349, 365, 2024, 2026], [250, 365, 2024, 2026],                          // abgeschnittene Jahre
  [null, 31, 2024, 2026], [null, 365, 2024, 2026]                          // fehlende Metadaten -> abgelehnt
].map(([lad, e, j, st]) => ({ lad, e, j, st, ok: S.yearCovers(lad === null ? { full_365: [] } : { last_actual_day: lad }, e, j, st) }));
// Ein weiteres Jahr ändert die Entscheidung über ein Jahr nicht mehr (vorher: Maximum über alle Jahre).
erg.unabhaengig = [S.yearCovers({ last_actual_day: 363 }, 365, 2023, 2026)];

// 2) Schaltjahr: Dezember 2024, Bewegung NUR am 31.12. (Tag 366) von 100 auf 110 — alle drei Builder.
const dez = [];
for (let t = Date.UTC(2024, 11, 2); t <= Date.UTC(2024, 11, 31); t += 86400000) {
  const wt = new Date(t).getUTCDay(); if (wt === 0 || wt === 6) continue;
  const iso = new Date(t).toISOString().substring(0, 10), c = iso === '2024-12-31' ? 110 : 100;
  dez.push({ date: iso, close: c, log_return: dez.length ? Math.log(c / dez[dez.length - 1].close) : null });
}
const endwert = (yd) => yd && yd[2024] ? +yd[2024].full_365[364].toFixed(6) : null;
erg.schaltjahr = { gemeinsam: endwert(S.buildYearData(dez)), jahreszyklus: endwert(JZ.buildExtendedYearData(dez)),
                   risikozyklus: endwert(rzBuild(dez)), lad_jz: JZ.buildExtendedYearData(dez)[2024].last_actual_day };

// Synthetische Jahre: Kurve 100 -> 100+k über das Jahr, letzte echte Kurszeile `lad`.
const jahr = (lad, k) => ({ last_actual_day: lad, full_365: Array.from({ length: 365 }, (_, i) => 100 + (k || 5) * i / 364) });

// 3) periodStats mit injiziertem Stichtag: 2023 (363), 2024 (365), 2025 (364) zählen; 2026 (laufend, 365) nicht.
erg.periodstats_jahr = (JZ.periodStats({ 2023: jahr(363), 2024: jahr(365), 2025: jahr(364), 2026: jahr(365) }, 1, 365, 2026) || {}).total_years;
erg.periodstats_juni = (JZ.periodStats({ 2025: jahr(364), 2026: jahr(181) }, 152, 181, 2026) || {}).total_years;

// 4) Heatmap: Stichtag 13.10.2026, Daten 2026 nur bis 30.06. (Tag 181) -> Juli–Sep leer; zukünftiges Jahr leer.
const zeile = (serie, name) => (serie.find(s => s.name === name) || { data: [] }).data.map(z => z.y !== null);
let hm = JZ.buildMonthlyHeatmap({ 2025: jahr(364), 2026: jahr(181), 2027: jahr(40) }, { jahr: 2026, monat: 10 });
erg.heatmap_2026 = zeile(hm, '2026');
erg.heatmap_2025 = zeile(hm, '2025');
erg.heatmap_2027 = zeile(hm, '2027');
// Schaltjahr-Grenze: Stichtag 29.02.2024 -> Februar läuft noch (leer); 01.03.2024 mit Kurs am 29.02. -> Februar da.
erg.heatmap_feb_2902 = zeile(JZ.buildMonthlyHeatmap({ 2024: jahr(60) }, { jahr: 2024, monat: 2 }), '2024')[1];
erg.heatmap_feb_0103 = zeile(JZ.buildMonthlyHeatmap({ 2024: jahr(60) }, { jahr: 2024, monat: 3 }), '2024')[1];
erg.heatmap_feb_0103_ohne_daten = zeile(JZ.buildMonthlyHeatmap({ 2024: jahr(31) }, { jahr: 2024, monat: 3 }), '2024')[1];

// 5) Präsidentenzyklus-Karten auf dem echten renderSignificance.
const zyklus = (vonJahr, bisJahr, lad) => {
  const yd = {};
  for (let y = vonJahr; y <= bisJahr; y++) yd[y] = jahr(lad, (y % 7) - 3);
  yd[2026] = jahr(280);                                         // laufendes Jahr — darf nie mitzählen
  dom['content-cycle-sig'] = null;
  JZ.JZ.renderSignificance(yd, 'cycle', 2026);
  const h = dom['content-cycle-sig'].innerHTML;
  const namen = ['Post-Election', 'Midterm', 'Pre-Election', 'Election Year'];
  return { reihenfolge: namen.map(n => h.indexOf('>' + n + '<')), grau: (h.match(/sig-zu-wenig/g) || []).length,
           n: (h.match(/n=\d+/g) || []), nan: /NaN|undefined/.test(h), sorry: /Sorry|Zu wenig Daten/.test(h) };
};
erg.zyklus_20 = zyklus(2006, 2025, 363);   // 20 abgeschlossene Jahre, alle enden am 29.12. -> je 5, keine graue Karte
erg.zyklus_10 = zyklus(2016, 2025, 364);   // je 2–3 -> alle vier grau, trotzdem vier Karten
erg.zyklus_leer = zyklus(2025, 2024, 364); // keine abgeschlossenen Jahre -> vier graue Karten mit n=0

// 6) runSignificanceTest + renderSection: Gruppen n=0..5.
const gr = { n0: [], n1: [1], n2: [1, 2], n3: [1, 2, -1], n4: [1, 2, -1, 3], n5: [1, 2, -1, 3, 0.5] };
const res = SA.significance.runSignificanceTest(gr, 0, { mindestN: 5 });
const html = SA.significance.renderSection(res, 4, Object.keys(gr), { mindestN: 5 });
erg.sig_gruppen = { zu_wenig: res.filter(r => r.zu_wenig).map(r => r.name + ':' + r.n),
                    getestet: res.filter(r => !r.zu_wenig).map(r => r.name), nan: /NaN|undefined/.test(html),
                    grau: (html.match(/sig-zu-wenig/g) || []).length };

// 7) Monats- und Quartalszweig von renderSignificance: das laufende Jahr (Daten bis Tag 181) darf nur Jan–Jun und
//    Q1/Q2 beitragen; Dezember/Q4 nur vergangene Jahre. Fallzahlen je Karte aus dem gerenderten HTML.
const zweig = (kind, id) => {
  const yd = {};
  for (let y = 2019; y <= 2025; y++) yd[y] = jahr(y % 2 ? 363 : 364, y - 2021);
  yd[2026] = jahr(181, 4);
  dom[id] = null;
  JZ.JZ.renderSignificance(yd, kind, 2026);
  const h = dom[id].innerHTML;
  return (h.match(/>([A-Za-zÄÖÜäöüé0-9 ]+)<\/div>[\s\S]*?n=(\d+)/g) || []).map(s => {
    const m = s.match(/>([^<]+)<\/div>[\s\S]*?n=(\d+)/); return m[1] + ':' + m[2];
  });
};
erg.zweig_monat = zweig('month', 'content-monthly-sig');
erg.zweig_quartal = zweig('quarter', 'content-quarterly-sig');

// 8) Abweichende Mindestzahl muss bis in Test UND Karte wirken (kein festes 5).
const res3 = SA.significance.runSignificanceTest({ a: [1, 2], b: [1, 2, 3], c: [1, -2, 3, 4] }, 0, { mindestN: 3 });
const html3 = SA.significance.renderSection(res3, 4, ['a', 'b', 'c'], { mindestN: 3, einheit: 'X-Einheit' });
erg.mindest3 = { zu_wenig: res3.filter(r => r.zu_wenig).map(r => r.name), getestet: res3.filter(r => !r.zu_wenig).map(r => r.name),
                 text_3: /mindestens 3 erforderlich/.test(html3), text_5: /mindestens 5/.test(html3), einheit: /X-Einheit/.test(html3) };

// 9) Englisch: graue Karte mit dem echten Wörterbuch (en.json) statt deutscher Ersatztexte.
const en = JSON.parse(fs.readFileSync(process.argv[4].replace(/pages[\\/]jahreszyklus\.html$/, 'i18n/en.json'), 'utf8'));
SA.i18n = { t: (k, fb) => (k in en ? en[k] : (fb || k)), isEN: () => true };
const htmlEn = SA.significance.renderSection(SA.significance.runSignificanceTest({ Midterm: [1, 2] }, 0, { mindestN: 5 }), 4, null,
  { mindestN: 5, einheit: SA.i18n.t('jz.sig_unit_years', 'abgeschlossene Jahre') });
erg.englisch = { not_evaluated: /Not evaluated/.test(htmlEn), einheit: /completed years/.test(htmlEn),
                 at_least: /at least 5 required/.test(htmlEn), deutsch: /Nicht ausgewertet|mindestens|erforderlich|abgeschlossene/.test(htmlEn) };
SA.i18n = { t: (k, fb) => fb || k, isEN: () => false };

process.stdout.write(JSON.stringify(erg));

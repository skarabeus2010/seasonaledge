/* Prueft die Fed-Verteilung auf /polymarket (Codex-Befund 14).

   Vier Teile, alle am Code bestaetigt und hier einzeln geprueft:

     1. Die Balken liefen auf ROHEN Preisen, der Erwartungswert auf der durch
        die Preissumme normierten Verteilung — zwei Grundlagen in einem Bild.
        Gemessen: rohe Summe 0,650, die Balken zeigten 10/20/30/5 %, waehrend
        der Erwartungswert bereits normiert rechnete.
     2. `12+` wog mit genau 12. Liegt dort Wahrscheinlichkeit, ist der
        Erwartungswert eine UNTERGRENZE — der Kontrakt sagt „12 oder mehr".
     3. Die Linien waren geglaettet UND ohne Nullwerte: ein fehlender Tag fehlte
        einfach, die Linie verband darueber hinweg und erfand dazu eine
        Kruemmung.
     4. Die Spalte „7d Δ" nahm den naechstgelegenen Punkt vor dem Stichtag, egal
        wie alt. Bei lueckenhafter Historie stand dort ein 60-Tage-Delta.

   REGEL ZUR KENNUNG `[Aufbau]`: nur an Pruefungen ueber die TESTVORRICHTUNG,
   nie an einer Aussage ueber den Produktivcode — dort macht sie den
   Mutationstest blind. Dieser Fehler ist in diesem Projekt dreimal passiert.

   Die Funktionen werden aus der Seite bzw. dem Modul gezogen, nicht nachgebaut. */
const fs = require('fs');
const path = require('path');

const REPO = path.resolve(__dirname, '..', '..');
const SEITE = path.join(REPO, 'landing/pages/polymarket.html');

let fehler = 0;
let anzahl = 0;
const pruefe = (b, was) => {
  anzahl++;
  console.log((b ? '  ok   ' : '  FEHL ') + was);
  if (!b) fehler++;
};

const el = () => ({ innerHTML: '', style: {}, textContent: '',
                    appendChild() {}, setAttribute() {}, getAttribute: () => null,
                    classList: { add() {}, remove() {}, contains: () => false } });
global.document = {
  getElementById: el, createElement: el,
  createTextNode: (t) => ({ nodeValue: String(t) }),
  querySelector: () => null, querySelectorAll: () => [], addEventListener() {}
};
global.window = {};
let letzteOptionen = null;
global.ApexCharts = class {
  constructor(_e, o) { letzteOptionen = o; }
  render() {} updateOptions() {} destroy() {}
};

eval(fs.readFileSync(path.join(REPO, 'landing/js/polymarket.js'), 'utf8'));
const PM = SA.polymarket;
SA.chartTheme = { chart: {}, grid: {}, xaxis: {}, yaxis: {} };
SA.COLORS = { accent: '#e8a820' };
SA.i18n = { t: (k, f) => f || k, isEN: () => false };
global.SA = SA;

const seite = fs.readFileSync(SEITE, 'utf8');
function ausSeite(name) {
  const a = seite.indexOf('function ' + name + '(');
  if (a < 0) throw new Error('nicht gefunden: ' + name);
  let t = 0;
  for (let j = seite.indexOf('{', a); j < seite.length; j++) {
    if (seite[j] === '{') t++;
    else if (seite[j] === '}') { t--; if (t === 0) return seite.slice(a, j + 1); }
  }
  throw new Error('Klammern nicht ausgeglichen: ' + name);
}

// ── 1 und 2: Verteilung und Erwartungswert ─────────────────────────────────
console.log('Balken und Erwartungswert auf derselben Grundlage:');
const maerkte = [], preise = {};
// Summe bewusst 0,65 — weit unter 1, damit roh und normiert auseinanderliegen.
[['0', 0.10], ['1', 0.20], ['2', 0.30], ['12plus', 0.05]].forEach(([k, v], i) => {
  maerkte.push({ slug: 'fed-cuts-2026-' + k, condition_id: 'c' + i });
  preise['c' + i] = { yes_price: v };
});
const st = PM.computeFedDistribution(maerkte, preise);
pruefe(Math.abs(st.totalProb - 0.65) < 1e-12,
  '[Aufbau] die Preissumme liegt bei 0,65 und damit weit unter 1');
pruefe(st.distNorm != null, 'eine normierte Verteilung wird geliefert');
// Nicht an einem fehlenden Feld sterben: ein Absturz ist kein Befund, sondern
// ein Abbruch, und dann waere der beabsichtigte Fall nie geprueft worden.
const normFeld = st.distNorm || {};
const summeNorm = Object.keys(normFeld).reduce((a, k) => a + normFeld[k], 0);
pruefe(Math.abs(summeNorm - 1) < 1e-9,
  'die normierte Verteilung summiert zu 1 (' + summeNorm.toFixed(6) + ')');
pruefe(Math.abs((normFeld['2'] || 0) - 0.30 / 0.65) < 1e-12,
  'jeder Balken ist durch die Preissumme geteilt');
pruefe(st.totalProb !== 1,
  'die rohe Preissumme bleibt erhalten und ist nicht stillschweigend 1');

console.log('Der Erwartungswert ist eine Untergrenze, wenn 12+ Masse traegt:');
pruefe(st.istUntergrenze === true, 'mit 5 % auf 12+ ist es eine Untergrenze');
const ohneTail = PM.computeFedDistribution(
  maerkte.filter(m => !/12plus$/.test(m.slug)), preise);
pruefe(ohneTail.istUntergrenze === false, 'ohne Masse auf 12+ ist es exakt');

// Das Feld allein genuegt nicht: es muss auch SICHTBAR werden. Codex hat
// gemessen, dass das Entfernen des ≥-Zeichens aus der KPI-Zeile hier mit
// Exit 0 durchlief — die Probe prueefte nur den Rueckgabewert. Der KPI-Block
// liegt inline in der Seite und haengt an zu viel DOM, um ihn hier
// auszufuehren; geprueft wird deshalb die Verdrahtung in der Quelle. Der
// Mutationstest zeigt, dass diese Pruefung reisst, wenn sie wegfaellt.
const seitenQuelle = fs.readFileSync(SEITE, 'utf8');
pruefe(/var vorz = fedStats\.istUntergrenze \? '≥ ' : '';/.test(seitenQuelle),
  'das ≥-Zeichen wird aus istUntergrenze abgeleitet');
pruefe((seitenQuelle.match(/vorz \+ exp/g) || []).length === 2,
  'es steht vor BEIDEN Erwartungswert-Kennzahlen (gefunden: '
  + (seitenQuelle.match(/vorz \+ exp/g) || []).length + ')');

console.log('Die Chart-Annotation traegt die Untergrenze mit:')
// Zweiter Ausgabepfad desselben Erwartungswerts. Die KPI-Zeile trug das ≥
// schon, die Annotation nicht (Codex, Abnahme Runde 2) — dort stand derselbe
// Wert ohne Vorbehalt.
letzteOptionen = null;
PM.renderFedDistChart('x', st);
const ann = ((((letzteOptionen.annotations || {}).xaxis || [])[0] || {}).label || {}).text || '';
pruefe(ann.indexOf('≥') === 0,
  'mit Masse auf 12+ beginnt die Annotation mit dem Groesser-gleich: ' + JSON.stringify(ann));
letzteOptionen = null;
PM.renderFedDistChart('x', ohneTail);
const annOhne = ((((letzteOptionen.annotations || {}).xaxis || [])[0] || {}).label || {}).text || '';
pruefe(annOhne.indexOf('≥') < 0,
  'ohne Masse auf 12+ steht kein Groesser-gleich davor: ' + JSON.stringify(annOhne));

console.log('Das Chart zeichnet die NORMIERTE Verteilung:');
letzteOptionen = null;
PM.renderFedDistChart('x', st);
const balken = (letzteOptionen.series || [{}])[0].data || [];
pruefe(balken.length === 13, '[Aufbau] 13 Balken gezeichnet');
pruefe(Math.abs(balken[2] - (0.30 / 0.65) * 100) < 1e-9,
  'der Balken fuer 2 Cuts zeigt ' + balken[2].toFixed(2) + ' % (normiert), nicht 30 %');

// ── 3: Luecken brechen die Linie ───────────────────────────────────────────
console.log('Luecken in der Zeitreihe brechen die Linie:');
const tag = 86400000, t0 = Date.UTC(2026, 0, 1);
letzteOptionen = null;
PM.renderFedTrendChart('x', [{ slug: 'fed-cuts-2026-2', condition_id: 'c1' }], [
  { condition_id: 'c1', ts: new Date(t0).toISOString(), yes_price: 0.30 },
  { condition_id: 'c1', ts: new Date(t0 + tag).toISOString(), yes_price: 0.31 },
  { condition_id: 'c1', ts: new Date(t0 + 9 * tag).toISOString(), yes_price: 0.50 }
]);
const reihe = (letzteOptionen.series || [{}])[0].data || [];
pruefe(reihe.length === 4,
  '3 Messungen + 1 Lueckenpunkt = ' + reihe.length + ' Punkte');
pruefe(reihe.filter(p => p.y === null).length === 1,
  'genau ein Nullwert, und zwar an der Luecke');
pruefe(reihe[2] && reihe[2].y === null,
  'der Nullwert steht zwischen dem 2. und 3. Messpunkt');
pruefe(letzteOptionen.stroke.curve === 'straight',
  'die Linie erfindet keine Kruemmung (curve=' + letzteOptionen.stroke.curve + ')');

// Derselbe Vorbehalt gilt fuer den ALLGEMEINEN Historien-Renderer. Der war
// nicht geprueft und verband weiter ueber Luecken hinweg (Codex, Abnahme
// 2026-10-08): ein Waechter, der nur einen von zwei Erzeugern kennt, deckt die
// Fehlerklasse nicht ab.
console.log('Auch der allgemeine Historien-Renderer bricht an Luecken:');
letzteOptionen = null;
PM.renderHistoryMulti('x', [{ condition_id: 'c1', slug: 'irgendein-markt',
                              question: 'Irgendein Markt?' }], [
  { condition_id: 'c1', ts: new Date(t0).toISOString(), yes_price: 0.30 },
  { condition_id: 'c1', ts: new Date(t0 + tag).toISOString(), yes_price: 0.31 },
  { condition_id: 'c1', ts: new Date(t0 + 9 * tag).toISOString(), yes_price: 0.50 }
]);
const reihe2 = (letzteOptionen.series || [{}])[0].data || [];
pruefe(reihe2.length === 4,
  '3 Messungen + 1 Lueckenpunkt = ' + reihe2.length + ' Punkte (allgemein)');
pruefe(reihe2[2] && reihe2[2].y === null,
  'der Nullwert steht an der Luecke, auch im allgemeinen Renderer');
pruefe(letzteOptionen.stroke && letzteOptionen.stroke.curve === 'straight',
  'auch hier keine erfundene Kruemmung');

console.log('Eine lueckenlose Reihe bekommt KEINEN Nullwert:');
letzteOptionen = null;
PM.renderFedTrendChart('x', [{ slug: 'fed-cuts-2026-2', condition_id: 'c1' }], [
  { condition_id: 'c1', ts: new Date(t0).toISOString(), yes_price: 0.30 },
  { condition_id: 'c1', ts: new Date(t0 + tag).toISOString(), yes_price: 0.31 },
  { condition_id: 'c1', ts: new Date(t0 + 2 * tag).toISOString(), yes_price: 0.32 }
]);
const dicht = (letzteOptionen.series || [{}])[0].data || [];
pruefe(dicht.length === 3 && dicht.every(p => p.y !== null),
  'drei Messungen an drei Tagen, kein eingefuegter Nullwert');

// ── 4: Die Grundlinie der Spalte „7d Δ" ────────────────────────────────────
console.log('Die 7-Tage-Grundlinie hat eine Altersgrenze:');
let uebergeben = null;
PM.renderMarketsTable = (id, m, lp, g) => { uebergeben = g; };
const jetzt = Date.now();
global.state = {
  markets: [], latest: {},
  history: [
    { condition_id: 'nah', ts: new Date(jetzt - 8 * tag).toISOString(), yes_price: 0.4 },
    { condition_id: 'alt', ts: new Date(jetzt - 60 * tag).toISOString(), yes_price: 0.2 },
    { condition_id: 'zuJung', ts: new Date(jetzt - 2 * tag).toISOString(), yes_price: 0.5 }
  ]
};
eval(ausSeite('renderTable'));
renderTable();
pruefe(uebergeben != null, '[Aufbau] renderTable hat eine Grundlinie uebergeben');
pruefe(!!uebergeben['nah'], 'ein 8 Tage alter Punkt gilt als Grundlinie');
pruefe(!uebergeben['alt'],
  'ein 60 Tage alter Punkt gilt NICHT — sonst heisst ein 60-Tage-Delta „7d"');
pruefe(!uebergeben['zuJung'],
  'ein 2 Tage alter Punkt gilt nicht, er liegt nach dem Stichtag');

console.log('');
console.log(fehler === 0 ? 'ALLE PRUEFUNGEN BESTANDEN' : fehler + ' FEHLER');
console.log('PROBE-ENDE ' + anzahl + ' Pruefungen, ' + fehler + ' Fehler');
process.exit(fehler === 0 ? 0 : 1);

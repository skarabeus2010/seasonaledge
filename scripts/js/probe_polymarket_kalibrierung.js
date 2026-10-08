/* Prueft die Kalibrierungs-Aussagen auf /polymarket (Codex-Befund 12).

   Was hier NICHT geprueft werden kann, und das steht bewusst zuerst: ob ein Text
   zu viel behauptet, laesst sich nicht messen. Ein Suchmuster unterscheidet
   „0,15–0,20 = gut kalibriert" (Behauptung) nicht von „ein festes Band wie
   0,15–0,20 gilt nicht allgemein" (Widerlegung) — beide enthalten dieselben
   Zeichen. Mir ist genau das beim Pruefen dieses Befundes passiert. Der Wortlaut
   bleibt deshalb Sache des Lesens, nicht des Tests.

   Geprueft wird das Nachpruefbare:

     1. **Die Einstufung kommt aus den Daten.** Befund 12 beanstandete, dass
        „Polymarket schlaegt die Basisrate deutlich" fest eingebaut war. Die
        Seite rechnet aber eine Einstufung aus `baseline - brier` — und die muss
        den Zahlen folgen, in jede Richtung. Das ist der substanzielle Teil.
     2. **Die Basisrate ist richtig beschriftet.** `outcomes` kommt in
        compute_brier_stats.py aus `flatten_forecasts(markets, snapshots)` mit
        TAGES-Snapshots. Die Rate ist also der Anteil YES je PROGNOSETAG und
        nicht je Aufloesung — die alte Beschriftung war sachlich falsch.
     3. **Die Offenlegung der Stichprobe ist in beiden Sprachen vorhanden.**

   REGEL ZUR KENNUNG `[Aufbau]`: nur fuer Eigenschaften der Testvorrichtung. */
const fs = require('fs');
const path = require('path');

const REPO = path.resolve(__dirname, '..', '..');
const SEITE = path.join(REPO, 'landing/pages/polymarket.html');
const EN = path.join(REPO, 'landing/i18n/en.json');

let fehler = 0;
let anzahl = 0;
const pruefe = (b, was) => {
  anzahl++;
  console.log((b ? '  ok   ' : '  FEHL ') + was);
  if (!b) fehler++;
};

const kasten = { innerHTML: '', style: {} };
global.document = {
  getElementById: () => kasten,
  createElement: () => ({ style: {}, appendChild() {} }),
  createTextNode: (t) => ({ nodeValue: String(t) }),
  querySelector: () => null, querySelectorAll: () => [], addEventListener() {}
};
global.window = {};
global.ApexCharts = class { constructor() {} render() {} updateOptions() {} destroy() {} };

eval(fs.readFileSync(path.join(REPO, 'landing/js/polymarket.js'), 'utf8'));
SA.chartTheme = { chart: {}, grid: {}, xaxis: {}, yaxis: {} };
SA.COLORS = { accent: '#e8a820' };
// Die Uebersetzung gibt hier den Schluessel zurueck, damit sich pruefen laesst,
// WELCHER Schluessel verwendet wird — und nicht nur, dass irgendein Text kommt.
SA.i18n = { t: (k) => k, isEN: () => false };
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
eval(ausSeite('renderBrierKpis'));

// ── 1: Die Einstufung folgt den Zahlen ─────────────────────────────────────
// Drei Datensaetze, die bewusst in verschiedene Richtungen zeigen. Waere die
// Einstufung fest eingebaut, saehen alle drei gleich aus.
function einstufung(brier, baseline) {
  kasten.innerHTML = '';
  renderBrierKpis({ brier: brier, baseline_brier: baseline,
                    random_50_50_brier: 0.25, base_rate: 0.5 });
  const h = kasten.innerHTML;
  if (h.indexOf('pmjs.brier_informativ') >= 0 && h.indexOf('pmjs.brier_schwach') < 0) return 'informativ';
  if (h.indexOf('pmjs.brier_schwach') >= 0) return 'schwach';
  if (h.indexOf('pmjs.brier_nicht_besser') >= 0) return 'nicht_besser';
  return '(keine)';
}

console.log('Die Einstufung kommt aus den Daten, nicht aus dem Text:');
pruefe(kasten.innerHTML === '', '[Aufbau] der Kasten ist vor dem Lauf leer');
const deutlich = einstufung(0.18, 0.25);   // Abstand 0,07 -> deutlich besser
const knapp = einstufung(0.249, 0.25);     // Abstand 0,001 -> knapp besser
const schlechter = einstufung(0.30, 0.25); // schlechter als die Basisrate
pruefe(deutlich === 'informativ',
  'Brier 0,18 gegen Basisrate 0,25 ergibt „informativ" (' + deutlich + ')');
pruefe(knapp === 'schwach',
  'Brier 0,249 gegen 0,25 ergibt nur „schwach informativ" (' + knapp + ')');
pruefe(schlechter === 'nicht_besser',
  'Brier 0,30 gegen 0,25 ergibt „nicht besser als Basisrate" (' + schlechter + ')');
pruefe(new Set([deutlich, knapp, schlechter]).size === 3,
  'alle drei Datensaetze fuehren zu VERSCHIEDENEN Einstufungen');

console.log('Die Basisrate-Baseline der Stichprobe wird mit angezeigt:');
kasten.innerHTML = '';
renderBrierKpis({ brier: 0.18, baseline_brier: 0.25,
                  random_50_50_brier: 0.25, base_rate: 0.42 });
const h = kasten.innerHTML;
pruefe(h.indexOf('pmjs.brier_vs_basis') >= 0,
  'der Abstand zur Basisrate ist eine eigene Kennzahl');
pruefe(h.indexOf('0.070') >= 0 || h.indexOf('0.07') >= 0,
  'der Abstand 0,25 - 0,18 = 0,07 steht in der Ausgabe');

// ── 2: Die Basisrate ist richtig beschriftet ───────────────────────────────
console.log('Die Basisrate ist als Groesse je PROGNOSETAG beschriftet:');
pruefe(h.indexOf('pmjs.brier_anteil') >= 0,
  '[Aufbau] die Beschriftung laeuft ueber einen i18n-Schluessel');
const enText = JSON.parse(fs.readFileSync(EN, 'utf8'));
const anteil = enText['pmjs.brier_anteil'] || '';
pruefe(anteil.length > 0, '[Aufbau] der EN-Wert existiert');
pruefe(!/resolution/i.test(anteil),
  'die EN-Beschriftung sagt NICHT „resolutions" — die Rate ist je Prognosetag: '
  + JSON.stringify(anteil));
pruefe(/forecast day/i.test(anteil),
  'die EN-Beschriftung nennt den Prognosetag');

// ── 3: Die Offenlegung der Stichprobe ──────────────────────────────────────
// ── 2b: Kein absolutes Qualitaetsband ──────────────────────────────────────
// Der Urzustand von Befund 12 war NICHT die Einstufung (die war schon
// gerechnet, das hat Codex an HEAD widerlegt), sondern ein fester Bereich im
// Fliesstext: «0.15–0.20 = gut kalibriert». Eine Qualitaetsaussage ohne
// Bezug auf die Basisrate der Stichprobe.
//
// GRENZE DIESER PRUEFUNG, ausdruecklich: sie trifft die BEHAUPTENDE Form
// („… = gut kalibriert" hinter einem Bereich). Der heutige Text zitiert
// dasselbe Band, um es zu widerlegen („ein fester Bereich wie «0,15–0,20 =
// gut» gilt nicht allgemein") — und genau daran scheitert ein naiveres
// Muster. Eine Umformulierung der Behauptung faengt sie NICHT; der Wortlaut
// bleibt Sache des Lesens.
console.log('Kein absolutes Qualitaetsband im Fliesstext:');
// Der Zwischenraum darf Markup enthalten — im Urzustand stand ein
// </span> zwischen Bereich und Aussage. Mit [^<] traf das Muster NICHT,
// und der [Aufbau]-Fall hat genau das gemeldet.
const band = /0[.,]\d+\s*(?:&ndash;|&mdash;|–|-)\s*0[.,]\d+[\s\S]{0,60}?=\s*gut kalibriert/i;
pruefe(band.test('0.15&ndash;0.20</span> = gut kalibriert'),
  '[Aufbau] das Muster trifft die behauptende Form aus dem Urzustand');
pruefe(!band.test(seite),
  'die Seite behauptet keinen festen Bereich als „gut kalibriert"');

console.log('Die Stichprobe ist offengelegt, in beiden Sprachen:');
pruefe(seite.indexOf('data-i18n-html="pm.calibration_stichprobe"') >= 0,
  'die deutsche Seite traegt den Offenlegungsblock');
const stich = enText['pm.calibration_stichprobe'] || '';
pruefe(stich.length > 200, 'der EN-Wert ist vorhanden und substanziell ('
  + stich.length + ' Zeichen)');
// Die vier Auswahlkriterien aus scripts/polymarket_scrape_resolved.py muessen
// darin stehen — sonst ist es keine Offenlegung, sondern eine Floskel.
[['10,000', 'die Volumenschwelle'],
 ['500', 'die Obergrenze je Kategorie'],
 ['2024', 'der Beginn des Aufloesungsfensters'],
 ['forecast day', 'die Gewichtung je Prognosetag']].forEach(function(paar) {
  pruefe(stich.indexOf(paar[0]) >= 0, 'EN nennt ' + paar[1] + ' (' + paar[0] + ')');
});

// ── 4: Kein zweites Diagramm im selben Ziel ────────────────────────────────
// Codex, Abnahme Runde 5: beim Neuzeichnen (jetzt moeglich, weil die Seite auf
// `sa:i18n-bereit` reagiert) entstanden zusaetzliche ApexCharts-Instanzen im
// selben Ziel, und die deutsche Erstfassung blieb darunter stehen. Gemessen
// wird deshalb mit instrumentiertem Konstruktor: Instanzen und destroy-Aufrufe.
console.log('Ein zweiter Aufbau zerstoert das alte Diagramm:');
let erzeugt = 0, zerstoert = 0;
global.ApexCharts = class {
  constructor() { erzeugt++; }
  render() {}
  updateOptions() {}
  destroy() { zerstoert++; }
};
const zustand = { charts: {} };
global.state = zustand;
eval(ausSeite('destroyChart'));
eval(ausSeite('renderCalibrationChart'));
const punkte = [{ count: 10, avg_prob: 0.4, observed_freq: 0.5 },
                { count: 12, avg_prob: 0.7, observed_freq: 0.6 }];
renderCalibrationChart(punkte);
pruefe(erzeugt === 1, '[Aufbau] der erste Aufbau erzeugt ein Diagramm (' + erzeugt + ')');
renderCalibrationChart(punkte);
pruefe(erzeugt === 2, '[Aufbau] der zweite Aufbau erzeugt eines (' + erzeugt + ')');
pruefe(zerstoert === 1,
  'und zerstoert dabei genau das alte (destroy-Aufrufe: ' + zerstoert + ')');

// Dasselbe fuer das zweite Brier-Diagramm. Ohne diesen Fall blieb die Mutation
// am Zeitfaecher-Diagramm unbemerkt — gemeldet vom eigenen Mutationstest.
erzeugt = 0; zerstoert = 0;
eval(ausSeite('renderTimeBucketsChart'));
const faecher = [{ bucket: '0-7', count: 10, brier: 0.18 },
                 { bucket: '8-30', count: 12, brier: 0.21 }];
renderTimeBucketsChart(faecher);
pruefe(erzeugt === 1, '[Aufbau] Zeitfaecher: erster Aufbau (' + erzeugt + ')');
renderTimeBucketsChart(faecher);
pruefe(zerstoert === 1,
  'Zeitfaecher: der zweite Aufbau zerstoert das alte (destroy-Aufrufe: '
  + zerstoert + ')');

console.log('');
console.log(fehler === 0 ? 'ALLE PRUEFUNGEN BESTANDEN' : fehler + ' FEHLER');
console.log('PROBE-ENDE ' + anzahl + ' Pruefungen, ' + fehler + ' Fehler');
process.exit(fehler === 0 ? 0 : 1);

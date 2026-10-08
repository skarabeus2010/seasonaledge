/* Prueft die Divergenz-Analyse auf /polymarket (Codex-Befund 13).

   Was hier NICHT geprueft werden kann, und das steht bewusst zuerst: ob ein
   Text zu viel behauptet. Ein Suchmuster trennt „Markt unterschaetzt" (eine
   Behauptung) nicht von „der Abstand sagt nicht, welche Zahl richtig liegt"
   (ihre Widerlegung) — beide enthalten dieselben Woerter. Genau das ist mir bei
   Befund 12 passiert: mein Kontrollausdruck fand meinen eigenen widerlegenden
   Satz. Der Wortlaut bleibt Sache des Lesens.

   Geprueft wird das Nachpruefbare an der GERECHNETEN Tabelle:

     1. **Die Fallzahl steht an der Zahl.** Ein Anteil ohne k und n laesst sich
        nicht einordnen: 40 % aus 2 von 5 Jahren ist etwas anderes als 40 % aus
        40 von 100.
     2. **Der Prior steht in ganzen Prozent.** Bei n=5 kann er nur 0, 20, 40 …
        sein; eine Dezimalstelle behauptet Genauigkeit, die es nicht gibt.
     3. **Die Schwelle kommt aus dem Vertrag**, nicht aus einer Zahl im Code —
        und sie entscheidet messbar: ein Abstand knapp darunter ergibt eine
        andere Bewertung als einer knapp darueber.
     4. **Die drei Bewertungen sind verschieden** und folgen den Zahlen.
     5. **Ein unvollstaendiges Vergleichsjahr zaehlt nicht mit** (der
        substanzielle Teil des Befundes, hier an der Tabelle statt am
        Zwillingstest).

   REGEL ZUR KENNUNG `[Aufbau]`: nur fuer Eigenschaften der Testvorrichtung,
   nie fuer Aussagen ueber den Produktivcode. */
const fs = require('fs');
const path = require('path');

const REPO = path.resolve(__dirname, '..', '..');

let fehler = 0;
let anzahl = 0;
const pruefe = (b, was) => {
  anzahl++;
  console.log((b ? '  ok   ' : '  FEHL ') + was);
  if (!b) fehler++;
};

const kasten = { innerHTML: '' };
global.document = {
  getElementById: () => kasten,
  createElement: () => ({ style: {}, appendChild() {} }),
  createTextNode: (t) => ({ nodeValue: String(t) }),
  querySelector: () => null, querySelectorAll: () => [], addEventListener() {}
};
global.window = {};
global.ApexCharts = class { constructor() {} render() {} updateOptions() {} destroy() {} };

eval(fs.readFileSync(path.join(REPO, 'landing/js/polymarket.js'), 'utf8'));
const PM = global.window.SA.polymarket;
// Die Uebersetzung gibt den Ersatztext zurueck wie im deutschen Betrieb.
SA.i18n = { t: (k, f) => (f === undefined ? k : f), isEN: () => false };
SA.chartTheme = { chart: {}, grid: {}, xaxis: {}, yaxis: {} };
SA.COLORS = { accent: '#e8a820' };

// ── Vorrichtung: eine Kursreihe, die den Prior STEUERBAR macht ─────────────
// Stichtag ist „heute"; jedes Vergleichsjahr liefert genau ein Fenster vom
// heutigen Kalendertag bis zum 31.12. Fuenf Jahre, davon zwei mit +50 % und
// drei mit +5 % — damit ist der Prior fuer ein Ziel von +25 % genau 2/5.
const heute = new Date();
// UTC-Getter, nicht die lokalen: `collectYearEndReturns` liest den Stichtag
// per getUTCMonth/getUTCDate (VERTRAG, Punkt 1). Mit den lokalen Feldern lag
// die Testreihe in New York um 00:30 UTC einen Tag daneben und die Probe wurde
// rot — ein Test, dessen Ergebnis von der Zeitzone abhaengt, ist kein Test
// (Codex, Abnahme Runde 2).
const mm = String(heute.getUTCMonth() + 1).padStart(2, '0');
const dd = String(heute.getUTCDate()).padStart(2, '0');
const JAHRE = [
  [heute.getUTCFullYear() - 5, 1.50],
  [heute.getUTCFullYear() - 4, 1.50],
  [heute.getUTCFullYear() - 3, 1.05],
  [heute.getUTCFullYear() - 2, 1.05],
  [heute.getUTCFullYear() - 1, 1.05]
];
function reihe(extra) {
  const aus = [];
  JAHRE.forEach(function (p) {
    aus.push({ date: p[0] + '-' + mm + '-' + dd, close: 100.0 });
    aus.push({ date: p[0] + '-12-31', close: 100.0 * p[1] });
  });
  (extra || []).forEach(function (z) { aus.push(z); });
  return aus;
}

function tabelle(zielK, marktPreis, extraZeilen) {
  kasten.innerHTML = '';
  PM.renderCryptoDivergence(
    'x', 'BTC-USD',
    [{ slug: 'btc-above-' + zielK + 'k-2026', condition_id: 'c1' }],
    { c1: { yes_price: marktPreis } },
    reihe(extraZeilen),
    100000   // aktueller Kurs: Ziel 125k => +25 % benoetigt
  );
  return kasten.innerHTML;
}

// ── 1 + 2: Fallzahl und Rundung ────────────────────────────────────────────
console.log('Der Prior traegt seine Fallzahl und steht in ganzen Prozent:');
const h = tabelle(125, 0.10);
pruefe(h.indexOf('<table') >= 0, '[Aufbau] eine Tabelle wurde gebaut');
pruefe(/\(2\/5\)/.test(h),
  'die Fallzahl 2/5 steht an der Zahl: ' + (/\((\d+\/\d+)\)/.exec(h) || ['', 'keine'])[1]);
pruefe(/>40%/.test(h) || />\s*40%/.test(h),
  'der Prior steht als 40% da (2 von 5)');
pruefe(!/40\.0%|40,0%/.test(h),
  'keine Dezimalstelle am Prior — bei n=5 waere sie Schein');

// ── 3: Die Schwelle entscheidet messbar ────────────────────────────────────
console.log('Die redaktionelle Schwelle entscheidet, und zwar aus dem Vertrag:');
// Prior 40 %. Markt 0,38 => Abstand 2 pp (unter der Schwelle), Markt 0,36 =>
// 4 pp (darueber). Die Vorrichtung trifft den Fall damit woertlich.
const knapp = tabelle(125, 0.38);
const klar = tabelle(125, 0.36);
function urteil(html) {
  if (html.indexOf('nahe beieinander') >= 0) return 'nahe';
  if (html.indexOf('Prior über Markt') >= 0) return 'prior_hoeher';
  if (html.indexOf('Markt über Prior') >= 0) return 'markt_hoeher';
  return '(keines)';
}
pruefe(urteil(knapp) === 'nahe',
  'Abstand 2 pp bleibt ohne Richtung (' + urteil(knapp) + ')');
pruefe(urteil(klar) === 'prior_hoeher',
  'Abstand 4 pp nennt eine Richtung (' + urteil(klar) + ')');
// Dass die Schwelle im VERTRAG steht, ist nachpruefbar: nur dann aendert eine
// Aenderung dort das Urteil. Der Mutationstest fuehrt genau das vor.
const quelle = fs.readFileSync(path.join(REPO, 'landing/js/polymarket.js'), 'utf8');
pruefe(/VERTRAG\.divergenzSchwellePp/.test(quelle),
  'die Schwelle wird aus dem Vertrag gelesen, nicht als Zahl eingesetzt');

// ── 4: Die drei Bewertungen sind verschieden ───────────────────────────────
console.log('Die Bewertung folgt den Zahlen, in beide Richtungen:');
const hoch = tabelle(125, 0.90);   // Markt 90 % gegen Prior 40 %
const drei = [urteil(klar), urteil(knapp), urteil(hoch)];
pruefe(urteil(hoch) === 'markt_hoeher',
  'Markt 90 % gegen Prior 40 % ergibt „Markt über Prior" (' + urteil(hoch) + ')');
pruefe(new Set(drei).size === 3,
  'alle drei Datensaetze fuehren zu VERSCHIEDENEN Bewertungen: ' + drei.join('/'));

// ── 5: Ein unvollstaendiges Vergleichsjahr zaehlt nicht ────────────────────
console.log('Ein im Juni endendes Jahr geht nicht als Jahresende ein:');
// Dieser Fall laeuft bewusst NICHT ueber die Tabelle, sondern direkt gegen
// `collectYearEndReturns` mit FESTEM Stichtag. Grund, von Codex gefunden:
// `renderCryptoDivergence` nimmt `new Date()`, und ein unvollstaendiges Jahr
// laesst sich gegen einen Dezember-Stichtag gar nicht bauen — jede Zeile ab
// dem Stichtag liegt dann selbst im Dezember. Meine erste Fassung haette die
// Probe im Dezember rot gemacht und das Deploy blockiert. Ein Test, dessen
// Ergebnis vom Kalender abhaengt, ist kein Test.
const FEST = new Date(Date.UTC(2026, 2, 15));   // 15.03.2026
function festeReihe(letzterTag) {
  const aus = [];
  [[2021, 1.50], [2022, 1.50], [2023, 1.05], [2024, 1.05], [2025, 1.05]].forEach(function (p) {
    aus.push({ date: p[0] + '-03-15', close: 100.0 });
    aus.push({ date: p[0] + '-12-31', close: 100.0 * p[1] });
  });
  // Das sechste Jahr endet am uebergebenen Tag und zeigte +50 %. Zaehlte es
  // mit, waere die Fallzahl 3/6 statt 2/5.
  aus.push({ date: '2020-03-15', close: 100.0 });
  aus.push({ date: '2020-' + letzterTag, close: 150.0 });
  return aus;
}
const ohneJuni = PM.collectYearEndReturns(festeReihe('06-30'), FEST);
const mitDez = PM.collectYearEndReturns(festeReihe('12-31'), FEST);
pruefe(mitDez.n === 6,
  '[Aufbau] endet das sechste Jahr im Dezember, zaehlt es mit (n=' + mitDez.n + ')');
pruefe(ohneJuni.n === 5,
  'endet es im Juni, zaehlt es NICHT (n=' + ohneJuni.n + ', erwartet 5)');
pruefe(PM.empiricalAboveCount(ohneJuni.samples, 0.25) === 2,
  'die Trefferzahl fuer +25 % bleibt 2, nicht 3 ('
  + PM.empiricalAboveCount(ohneJuni.samples, 0.25) + ')');

console.log('');
console.log(fehler === 0 ? 'ALLE PRUEFUNGEN BESTANDEN' : fehler + ' FEHLER');
console.log('PROBE-ENDE ' + anzahl + ' Pruefungen, ' + fehler + ' Fehler');
process.exit(fehler === 0 ? 0 : 1);

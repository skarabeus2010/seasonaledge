/* Probe fuer `loadLatestPrices` in landing/js/polymarket.js — der ECHTE Lader.

   Warum als eigene Probe: der Waechter hat den Lader zuerst nur ueber Textfragmente
   geprueft („enthaelt rpc/…", „enthaelt Array.isArray"). Codex hat dagegen eine
   Gegenprobe gefahren: ein `return Promise.resolve({});` direkt am Funktionsanfang,
   restlicher Text unveraendert — der Waechter blieb gruen, obwohl der RPC nie
   gerufen wurde. Ein Textfund ist kein Nachweis einer Wirkung.

   Hier laeuft die Funktion wirklich, gegen eine fetch-Attrappe. Geprueft wird:
     1. Der Pfad ist `rpc/polymarket_latest_prices`, und das Array-Argument kommt
        kodiert mit.
     2. Eine gueltige Antwort wird je Markt auf die erste Zeile reduziert.
     3. Ein PostgREST-FEHLEROBJEKT (HTTP 400 mit {code,message}) fuehrt zur
        ABLEHNUNG, nicht zu einem leeren Erfolg.
     4. `null` als Antwortkoerper ebenso.
     5. Ein Netzfehler ebenso.
     6. In KEINEM dieser Faelle wird `polymarket_prices` abgefragt — kein
        stiller Rueckfall.
     7. Eine leere ID-Liste fragt gar nicht (ein leeres Array heisst bei der
        Datenbankfunktion NICHT „alle" — am 2026-10-20 gemessen).
*/
'use strict';
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

global.document = {
  getElementById: () => null,
  createElement: () => ({ style: {}, appendChild() {} }),
  querySelector: () => null, querySelectorAll: () => [], addEventListener() {}
};
global.window = {};
require('./release_harness').bereite(global.window);
global.ApexCharts = class { constructor() {} render() {} updateOptions() {} destroy() {} };

eval(fs.readFileSync(path.join(REPO, 'landing/js/polymarket.js'), 'utf8'));
const SA = global.window.SA;
const PM = SA.polymarket;
SA.i18n = { t: (k, f) => (f === undefined ? k : f), isEN: () => false };

// ── fetch-Attrappe, die den echten SA.supabase.get traegt ──────────────────
let abrufe = [];
let antwort = null;

SA.supabase = SA.supabase || {};
SA.supabase.url = 'https://beispiel.invalid';
SA.supabase.key = 'k';
// Der echte get aus app.js ist hier nicht geladen; er ist bewusst nachgebildet
// GENAU so, wie er sich verhaelt: `r.json()` ohne `r.ok`-Pruefung. Dass er so
// ist, haelt der Waechter am Quelltext von app.js fest — hier geht es darum,
// dass der LADER damit zurechtkommt.
SA.supabase.get = function (tabelle, query) {
  abrufe.push(tabelle + (query ? '?' + query : ''));
  if (antwort && antwort.netzfehler) return Promise.reject(new Error('Netzfehler'));
  return Promise.resolve(antwort ? antwort.koerper : null);
};

function lauf(ids, ant) {
  abrufe = [];
  antwort = ant;
  return PM.loadLatestPrices(ids).then(
    (w) => ({ ok: true, wert: w, abrufe: abrufe.slice() }),
    (e) => ({ ok: false, fehler: String(e && e.message || e), abrufe: abrufe.slice() })
  );
}

const IDS = ['0xAA', '0xBB'];

(async function () {
  // 1 + 2: gueltige Antwort
  let r = await lauf(IDS, { koerper: [
    { condition_id: '0xAA', ts: '2026-10-20T00:00:00Z', yes_price: 0.6 },
    { condition_id: '0xAA', ts: '2026-10-19T00:00:00Z', yes_price: 0.5 },
    { condition_id: '0xBB', ts: '2026-10-20T00:00:00Z', yes_price: 0.3 }
  ] });
  pruefe(r.ok, '[Aufbau] der gueltige Fall laeuft durch');
  pruefe(r.abrufe.length === 1 && r.abrufe[0].indexOf('rpc/polymarket_latest_prices') === 0,
    'der Lader ruft rpc/polymarket_latest_prices (' + (r.abrufe[0] || 'nichts') + ')');
  pruefe(r.abrufe[0] && r.abrufe[0].indexOf('p_condition_ids=') > 0,
    'mit dem Argument p_condition_ids');
  pruefe(r.abrufe[0] && r.abrufe[0].indexOf(encodeURIComponent('{0xAA,0xBB}')) > 0,
    'und zwar als kodiertes Array (' + (r.abrufe[0] || '').slice(-40) + ')');
  pruefe(r.ok && Object.keys(r.wert).length === 2,
    'zwei Maerkte im Ergebnis (' + (r.ok ? Object.keys(r.wert).length : '—') + ')');
  pruefe(r.ok && r.wert['0xAA'] && r.wert['0xAA'].yes_price === 0.6,
    'je Markt die ERSTE Zeile (0,6 statt 0,5)');

  // 3: PostgREST-Fehlerobjekt
  r = await lauf(IDS, { koerper: { code: '42883', message: 'function does not exist' } });
  pruefe(!r.ok, 'ein Fehlerobjekt fuehrt zur ABLEHNUNG, nicht zu leerem Erfolg');
  pruefe(!r.ok && r.fehler.indexOf('polymarket_latest_prices') >= 0,
    'und die Meldung nennt die Funktion (' + (r.fehler || '') + ')');
  pruefe(r.abrufe.filter((a) => a.indexOf('polymarket_prices?') === 0).length === 0,
    'KEIN Rueckfall auf die Tabelle polymarket_prices');

  // 4: null
  r = await lauf(IDS, { koerper: null });
  pruefe(!r.ok, '`null` fuehrt zur Ablehnung (vorher waere es ein leerer Erfolg)');
  pruefe(r.abrufe.filter((a) => a.indexOf('polymarket_prices?') === 0).length === 0,
    'auch hier kein Rueckfall');

  // 5: Netzfehler
  r = await lauf(IDS, { netzfehler: true });
  pruefe(!r.ok, 'ein Netzfehler fuehrt zur Ablehnung');
  pruefe(r.abrufe.filter((a) => a.indexOf('polymarket_prices?') === 0).length === 0,
    'und ebenfalls nicht zum Rueckfall');

  // 7: leere Liste fragt nicht
  r = await lauf([], { koerper: [] });
  pruefe(r.ok && Object.keys(r.wert).length === 0,
    'eine leere ID-Liste ergibt ein leeres Ergebnis');
  pruefe(r.abrufe.length === 0,
    'und fragt gar nicht — `{}` wuerde bei der Funktion 0 Zeilen liefern, nicht alle');

  console.log('');
  console.log(fehler === 0 ? 'ALLE PRUEFUNGEN BESTANDEN' : fehler + ' FEHLER');
  console.log('PROBE-ENDE ' + anzahl + ' Pruefungen, ' + fehler + ' Fehler');
  process.exit(fehler === 0 ? 0 : 1);
})().catch(function (e) {
  console.log('[Ausnahme] ' + (e && e.stack || e));
  console.log('PROBE-ENDE ' + anzahl + ' Pruefungen, ' + (fehler + 1) + ' Fehler');
  process.exit(3);
});

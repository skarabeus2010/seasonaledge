// verify_prefs.js — Waechter fuer SA.prefs (Ticker- und Zeitraum-Gedaechtnis).
//
//   node scripts/js/verify_prefs.js        Exit 1 bei Abweichung
//
// Geprueft wird die echte landing/js/app.js gegen einen minimalen DOM-Stub,
// kein Nachbau — ein Waechter, der einen Nachbau prueft, prueft eine Fiktion.
// Ob dieser Waechter ueberhaupt rot werden kann, prueft
// scripts/verify_prefs_mutation.py.
// Prueft SA.prefs gegen einen minimalen DOM-Stub.
// Die vom Review gefundenen Fehler stehen als eigene Faelle drin (B1, B2, B5),
// damit sie nicht stillschweigend zurueckkehren.
var store = {};
global.localStorage = {
  getItem: function(k){ return k in store ? store[k] : null; },
  setItem: function(k,v){ store[k]=String(v); },
  removeItem: function(k){ delete store[k]; }
};
var DOM = {};
global.Event = function(typ, o){ this.type=typ; this.bubbles=!!(o&&o.bubbles); };
global.document = {
  getElementById: function(id){ return DOM[id] || null; },
  addEventListener: function(){},
  querySelector: function(){ return null; },
  querySelectorAll: function(){ return []; },
  createElement: function(){ return {style:{},setAttribute:function(){},addEventListener:function(){},appendChild:function(){}}; },
  createEvent: function(){ return {initEvent:function(){}}; },
  body: {appendChild:function(){},classList:{add:function(){},toggle:function(){},contains:function(){return false;}}}
};
global.window = {addEventListener:function(){}, innerWidth:1400, location:{search:''}};
global.fetch = function(){ return Promise.resolve({json:function(){return Promise.resolve([]);}}); };
require(require('path').join(__dirname, '..', '..', 'landing', 'js', 'app.js'));
var SA = global.window.SA;

var fehler = 0, faelle = 0;
function ist(name, a, b){
  faelle++;
  var ok = String(a) === String(b);
  if (!ok) fehler++;
  console.log((ok?'  ok  ':'  FEHL') + '  ' + name + '  ->  ' + a + (ok?'':'   (erwartet ' + b + ')'));
}
function sel(id, vals){
  DOM[id] = {tagName:'SELECT', value:'', addEventListener:function(){},
             options: vals.map(function(v){ return {value:String(v)}; })};
  return DOM[id];
}
function slider(id, lo, hi){
  // Nachbildung von wochentage.html / backtest-engine.html: ein statisches
  // Zahl-Label, das nur ein 'input'-Listener pflegt.
  var el = {tagName:'INPUT', min:String(lo), max:String(hi), value:'', label:null,
            _h:{}, addEventListener:function(t,f){ this._h[t]=f; },
            dispatchEvent:function(e){ if (this._h[e.type]) this._h[e.type].call(this); return true; }};
  DOM[id] = el;
  el.addEventListener('input', function(){ el.label = el.value; });
  return el;
}
function feld(id){ DOM[id] = {tagName:'INPUT', value:'', addEventListener:function(){}}; return DOM[id]; }
function reset(){ store = {}; DOM = {}; global.window.location.search = ''; SA._tickerCache = null; }

console.log('-- Ticker --');
reset();
ist('ohne Speicher = Standard', SA.prefs.ticker('SPY'), 'SPY');
SA.prefs.setTicker('^gdaxi');
ist('setTicker normalisiert auf Grossbuchstaben', SA.prefs.ticker('SPY'), '^GDAXI');
ist('ohne Kategorie bleibt art() leer', SA.prefs.art(), 'null');
SA.prefs.setTicker('SAP.DE', 'EU-Aktie');
ist('Kategorie wird mitgespeichert', SA.prefs.art(), 'EU-Aktie');
SA.prefs.setTicker('');
ist('leerer setTicker aendert nichts', SA.prefs.ticker('SPY'), 'SAP.DE');
SA.prefs.vergessen();
ist('vergessen() loescht den Ticker', SA.prefs.ticker('SPY'), 'SPY');
ist('vergessen() loescht die Kategorie', SA.prefs.art(), 'null');

console.log('-- Zeitraum: naechstliegender vorhandener Wert --');
reset();
SA.prefs.setYears('25');
sel('a', [1,3,5,10,20,'max']);
ist('25 -> naechstliegend 20', SA.prefs.applyYears('a'), '20');
sel('b', [1,3,5,10,15,20,25,30]);
ist('25 exakt vorhanden', SA.prefs.applyYears('b'), '25');
SA.prefs.setYears('max');
ist('max nicht vorhanden -> groesste Zahl', SA.prefs.applyYears('b'), '30');
sel('c', [1,3,5,10,20,'max']);
ist('max vorhanden -> max', SA.prefs.applyYears('c'), 'max');
SA.prefs.setYears('7');
sel('d', [5,10]);
ist('7 -> 5 (Abstand 2 < 3)', SA.prefs.applyYears('d'), '5');
sel('leer', []);
ist('Select ohne Optionen -> null', SA.prefs.applyYears('leer'), 'null');
SA.prefs.setYears('10');
ist('fehlendes Select -> null, kein Absturz', SA.prefs.applyYears('gibtsnicht'), 'null');
// Optionen ohne value-Attribut (monatswechsel/mondphasen/trifecta/plain-vanilla):
// der Browser liefert dort den Textinhalt als .value -- genau das bildet sel() ab.
sel('f', [5,10,20]);
ist('Optionen ohne value-Attribut', SA.prefs.applyYears('f'), '10');

console.log('-- B1: Slider-Label muss mitlaufen (war der Fehler) --');
reset();
SA.prefs.setYears('25');
var sl = slider('sl-years', 1, 30);
ist('Slider wird gesetzt', SA.prefs.applyYears('sl-years'), '25');
ist('Label laeuft mit, statt auf dem Startwert zu bleiben', sl.label, '25');
SA.prefs.setYears('50');
slider('sl2', 1, 30);
ist('Slider klemmt auf max', SA.prefs.applyYears('sl2'), '30');
ist('geklemmtes Label passt zum Slider', DOM['sl2'].label, '30');
SA.prefs.setYears('2');
slider('sl3', 5, 50);
ist('Slider klemmt auf min', SA.prefs.applyYears('sl3'), '5');
SA.prefs.setYears('max');
var sl4 = slider('sl4', 1, 30);
sl4.value = '17';
ist('Slider kennt kein "max" -> unveraendert', SA.prefs.applyYears('sl4'), 'null');
ist('und der Wert bleibt stehen', sl4.value, '17');

console.log('-- applyTicker: URL > gemerkt > Standard --');
reset();
store['sa-prefs-ticker'] = 'SAP.DE';
feld('ti');
ist('nimmt den gemerkten', SA.prefs.applyTicker('ti','SPY'), 'SAP.DE');
ist('schreibt ins Feld', DOM['ti'].value, 'SAP.DE');
global.window.location.search = '?t=tsla';
ist('URL-Parameter gewinnt', SA.prefs.applyTicker('ti','SPY'), 'TSLA');
ist('URL-Parameter setzt die Erinnerung', store['sa-prefs-ticker'], 'TSLA');
global.window.location.search = '';
ist('fehlendes Feld -> kein Absturz', SA.prefs.applyTicker('gibtsnicht','SPY'), 'TSLA');

console.log('-- B2: nurAktien entscheidet ueber die Kategorie (war der Fehler) --');
reset(); feld('ti');
SA.prefs.setTicker('SPY', 'US-ETF');
ist('ETF bleibt auf normaler Seite', SA.prefs.applyTicker('ti','^GSPC'), 'SPY');
ist('ETF raus auf Earnings (die Regex liess SPY durch)', SA.prefs.applyTicker('ti','AAPL',{nurAktien:true}), 'AAPL');
SA.prefs.setTicker('BTC-USD', 'Krypto');
ist('Krypto raus', SA.prefs.applyTicker('ti','AAPL',{nurAktien:true}), 'AAPL');
SA.prefs.setTicker('HYG', 'Anleihen');
ist('Anleihen-ETF raus', SA.prefs.applyTicker('ti','AAPL',{nurAktien:true}), 'AAPL');
SA.prefs.setTicker('^GSPC', 'US-Index');
ist('Index raus', SA.prefs.applyTicker('ti','AAPL',{nurAktien:true}), 'AAPL');
SA.prefs.setTicker('SAP.DE', 'EU-Aktie');
ist('EU-Aktie bleibt', SA.prefs.applyTicker('ti','AAPL',{nurAktien:true}), 'SAP.DE');
SA.prefs.setTicker('AAPL', 'US-Aktie');
ist('US-Aktie bleibt', SA.prefs.applyTicker('ti','MSFT',{nurAktien:true}), 'AAPL');
// Rueckfall, wenn keine Kategorie gespeichert ist (?t=-Link, Alt-Eintrag)
reset(); feld('ti');
store['sa-prefs-ticker'] = '^GSPC';
ist('ohne Kategorie faengt die Heuristik den Index', SA.prefs.applyTicker('ti','AAPL',{nurAktien:true}), 'AAPL');
store['sa-prefs-ticker'] = 'CL=F';
ist('ohne Kategorie faengt sie den Future', SA.prefs.applyTicker('ti','AAPL',{nurAktien:true}), 'AAPL');
store['sa-prefs-ticker'] = 'ETH-USD';
ist('ohne Kategorie faengt sie Krypto', SA.prefs.applyTicker('ti','AAPL',{nurAktien:true}), 'AAPL');
store['sa-prefs-ticker'] = 'MSFT';
ist('ohne Kategorie bleibt eine Aktie', SA.prefs.applyTicker('ti','AAPL',{nurAktien:true}), 'MSFT');

console.log('-- B5: unbekannter Ticker wird nachtraeglich vergessen --');
reset();
SA._tickerCache = [{t:'AAPL',n:'Apple',k:'US-Aktie'},{t:'SPY',n:'SPDR',k:'US-ETF'}];
store['sa-prefs-ticker'] = 'FOO';
SA._pruefeGemerkten();
ist('unbekannter Ticker wird vergessen', SA.prefs.ticker('SPY'), 'SPY');
store['sa-prefs-ticker'] = 'SPY';
SA._pruefeGemerkten();
ist('bekannter Ticker bleibt', SA.prefs.ticker('AAPL'), 'SPY');
ist('und die Kategorie wird nachgetragen', SA.prefs.art(), 'US-ETF');
ist('_tickerFind findet case-insensitiv', (SA._tickerFind('aapl')||{}).k, 'US-Aktie');
SA._tickerCache = null;
ist('ohne geladene Liste findet _tickerFind nichts', SA._tickerFind('AAPL'), 'null');

console.log('-- localStorage faellt aus --');
reset();
global.localStorage = {
  getItem: function(){ throw new Error('SecurityError'); },
  setItem: function(){ throw new Error('QuotaExceeded'); },
  removeItem: function(){ throw new Error('nope'); }
};
feld('ti'); sel('a',[5,10,20]);
ist('ticker() faellt auf den Standard zurueck', SA.prefs.ticker('SPY'), 'SPY');
ist('setTicker() wirft nicht durch', (function(){ SA.prefs.setTicker('AAPL','US-Aktie'); return 'ok'; })(), 'ok');
ist('applyTicker() liefert den Standard', SA.prefs.applyTicker('ti','SPY'), 'SPY');
ist('applyYears() liefert null', SA.prefs.applyYears('a'), 'null');
ist('autoYears() wirft nicht durch', (function(){ SA.prefs.autoYears(); return 'ok'; })(), 'ok');

console.log(fehler ? '\nFEHLER: ' + fehler + ' von ' + faelle
                   : '\nalle ' + faelle + ' Faelle gruen');
process.exit(fehler ? 1 : 0);

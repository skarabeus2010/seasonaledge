/* Prueft die Stellen, an denen FREMDE Daten in HTML geschrieben werden.

   Warum unbedingt: die Marktfragen kommen von Polymarket ueber
   scripts/polymarket_refresh.py in die Supabase-Tabellen und von dort in den
   Browser. Wir schreiben den Text nicht, wir geben ihn weiter. Ob heute jemand
   eine boesartige Frage dort unterbringen kann, ist offen — die Ausgabe zu
   maskieren kostet nichts und macht die Frage unerheblich.

   Geprueft wird mit einem Wert, der nach korrektem Maskieren kein Tag und kein
   Ereignis-Attribut mehr ergeben darf. Auf die STRUKTUR pruefen, nicht auf ein
   Teilwort: nach dem Maskieren steht "onload=" als harmloser Text in der Zelle,
   und ein Test, der die Zeichenkette irgendwo sucht, faellt dann faelschlich
   durch. */
const fs = require('fs');
const path = require('path');

const REPO = path.resolve(__dirname, '..', '..');

/* ── Minimales DOM ──────────────────────────────────────────────────────── */
const el = {};
function neu(id) {
  const o = {
    id, _html: '', _text: '', style: {}, dataset: {},
    classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
    appendChild() {}, addEventListener() {},
    querySelectorAll() { return []; }, querySelector() { return null; },
    getAttribute() { return null; }, setAttribute() {}
  };
  Object.defineProperty(o, 'innerHTML', { get() { return this._html; }, set(v) { this._html = v; } });
  Object.defineProperty(o, 'textContent', { get() { return this._text; }, set(v) { this._text = v; } });
  return o;
}
function hole(id) { return el[id] || (el[id] = neu(id)); }

/* Im Browser IST `window` das globale Objekt — `window.SA = …` erzeugt dort
   dieselbe Bindung wie ein globales `SA`. watchlist.js verlaesst sich darauf
   (es setzt `window.SA`, liest aber blankes `SA`). Ein eigenes window-Objekt
   bricht das, also zeigt window hier auf global, wie im Browser. */
global.window = global;
global.location = { pathname: '/polymarket', search: '', hash: '' };
global.addEventListener = function () {};
global.document = {
  getElementById: hole,
  querySelector() { return null; },
  querySelectorAll() { return []; },
  addEventListener() {},
  createElement(tag) { const o = neu('neu-' + tag); o.tagName = tag.toUpperCase(); return o; }
};
global.ApexCharts = class { constructor() {} render() {} updateOptions() {} destroy() {} };

let fehler = 0;
function pruefe(name, bedingung, zusatz) {
  if (bedingung) { console.log('[OK  ] ' + name); return; }
  console.log('[FEHL] ' + name + (zusatz ? ' — ' + zusatz : ''));
  fehler++;
}

const GIFT = '"><svg onload=alert(1)>';
/* Nach korrektem Maskieren darf keines davon in der Ausgabe stehen. */
function pruefeAusgabe(name, aus) {
  pruefe(name + ': kein <svg aus Fremddaten', !/<svg/i.test(aus));
  pruefe(name + ': kein Ereignis-Attribut in einem Tag',
    !/<[^>]*\bon[a-z]+\s*=/i.test(aus));
  /* Praezise statt schlau: der Giftwert darf nicht WOERTLICH in der Ausgabe
     stehen. Ein erster Entwurf versuchte, einen Attributausbruch per Regex zu
     erkennen, und traf dabei legitime Attribute wie <td style="…"> — HTML per
     Muster zu pruefen erzeugt eine Luecke oder einen Fehlalarm pro Runde
     (dieselbe Lesson wie v65.6). */
  pruefe(name + ': der Giftwert steht nicht unmaskiert in der Ausgabe',
    !aus.includes(GIFT));
}

/* ── polymarket.js: renderMarketsTable ─────────────────────────────────── */
const pmQuelle = fs.readFileSync(path.join(REPO, 'landing/js/polymarket.js'), 'utf8');
// eslint-disable-next-line no-new-func
require('vm').runInThisContext(pmQuelle, { filename: 'polymarket.js' });
const PM = global.window.SA && global.window.SA.polymarket;

if (!PM || typeof PM.renderMarketsTable !== 'function') {
  pruefe('polymarket.js exportiert renderMarketsTable', false,
    'nicht gefunden — wenn die Datei umgebaut wurde, muss diese Probe mitgezogen werden');
} else {
  PM.renderMarketsTable('pm-tabelle', [{
    slug: GIFT, category: GIFT, question: GIFT,
    condition_id: 'x', liquidity_usd: 1000
  }], { x: { yes_price: 0.5 } }, {});
  pruefeAusgabe('renderMarketsTable', hole('pm-tabelle').innerHTML);
}

/* ── watchlist.js: Quellpruefung des Tickers ───────────────────────────── */
global.localStorage = (function () {
  const m = {};
  return {
    getItem(k) { return k in m ? m[k] : null; },
    setItem(k, v) { m[k] = String(v); },
    removeItem(k) { delete m[k]; }
  };
})();
const wlQuelle = fs.readFileSync(path.join(REPO, 'landing/js/watchlist.js'), 'utf8');
require('vm').runInThisContext(wlQuelle, { filename: 'watchlist.js' });
const WL = global.window.SA && global.window.SA.watchlist;

if (!WL || typeof WL.add !== 'function') {
  pruefe('watchlist.js exportiert add()', false, 'nicht gefunden');
} else {
  /* Die Quelle muss verwerfen, was kein Ticker ist. Das schuetzt JEDEN
     Verbraucher — es gibt drei Darstellungspfade. */
  const GUELTIG = ['SPY', '^GSPC', 'BTC-USD', 'SAP.DE', 'EURUSD=X', 'BRK-B', 'HG=F'];
  const UNGUELTIG = [GIFT, '<svg onload=alert(1)>', 'A"B', "A'B", 'A B',
    'VIEL-ZU-LANGER-TICKER-NAME', 'a<b'];

  GUELTIG.forEach(function (t) {
    const ok = WL.add(t);
    pruefe('watchlist nimmt gueltigen Ticker an: ' + t, ok === true,
      'add() gab ' + ok + ' zurueck');
    WL.remove(t);
  });
  UNGUELTIG.forEach(function (t) {
    pruefe('watchlist verwirft: ' + JSON.stringify(t).slice(0, 40),
      WL.add(t) === false, 'add() hat ihn angenommen');
  });
}

console.log(fehler === 0
  ? '\nAlle Faelle bestanden.'
  : '\n' + fehler + ' Fall/Faelle durchgefallen.');
process.exit(fehler === 0 ? 0 : 1);

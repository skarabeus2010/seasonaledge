/* Faehrt das inline-JS von /congress mit BOESARTIGEN Daten und prueft, dass
   nichts davon als HTML oder als ausfuehrbares Linkziel in der Seite landet.

   Warum diese Seite: ihre Daten kommen aus einem fremden XML (House-Clerk) ueber
   einen Cron in eine JSON-Datei und von dort in den Browser. Wer den Netzwerkpfad
   des Importers kontrolliert, bestimmt den Inhalt — die Senke ist damit erreichbar,
   nicht nur vorhanden.

   Geprueft wird dreierlei, je mit einem Fall, der VOR der Korrektur durchfaellt:
   (1) esc() maskiert auch Anfuehrungszeichen. Ohne das bricht ein Wert aus einem
       Attribut aus, und esc() wird hier in Attributen benutzt.
   (2) Jedes eingesetzte Feld laeuft durch esc() — auch die Datumsfelder, die
       vorher ungeprueft eingesetzt wurden.
   (3) Ein pdf_url, das nicht auf den erwarteten Host zeigt, wird NICHT zum Link.
       Das ist die eigentliche Schranke: ein javascript:-Ziel darf sie nie passieren.

   Das JS wird aus der SEITE gezogen, nicht aus einer Kopie. */
const fs = require('fs');
const path = require('path');

const REPO = path.resolve(__dirname, '..', '..');
const SEITE = path.join(REPO, 'landing/pages/congress.html');

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

global.document = {
  getElementById: hole,
  querySelector() { return null; },
  querySelectorAll() { return []; },
  addEventListener() {},
  createElement(tag) { const o = neu('neu-' + tag); o.tagName = tag.toUpperCase(); return o; }
};
global.window = { location: { pathname: '/congress' }, addEventListener() {} };
global.fetch = () => Promise.reject(new Error('kein Netz im Test'));

/* ── Inline-JS der Seite laden ──────────────────────────────────────────── */
const html = fs.readFileSync(SEITE, 'utf8');
const bloecke = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const kern = bloecke.find(b => b.includes('renderTable') && b.includes('esc'));
if (!kern) {
  console.error('FEHLER: der Block mit renderTable/esc wurde in der Seite nicht gefunden.');
  console.error('Wenn die Seite umgebaut wurde, muss diese Probe mitgezogen werden —');
  console.error('eine Probe, die ihren Pruefgegenstand nicht findet, ist kein Test.');
  process.exit(1);
}

/* Die Funktionen sind in einer IIFE gekapselt. Statt sie nachzubauen (das waere
   eine Fiktion, siehe Lesson aus v58) wird der Quelltext um einen Export ergaenzt
   und dann ausgefuehrt. */
const exportiert = kern.replace(
  /\}\s*\(\s*\)\s*;?\s*$/,
  'global.__PROBE = { esc: esc, renderTable: renderTable, ' +
  'pdfhref: (typeof pdfhref === "function" ? pdfhref : null), ' +
  'tklink: tklink };\n}();'
);
try {
  // eslint-disable-next-line no-new-func
  new Function(exportiert)();
} catch (e) {
  console.error('FEHLER beim Ausfuehren des Seiten-JS:', e.message);
  process.exit(1);
}
const P = global.__PROBE;
if (!P || typeof P.esc !== 'function') {
  console.error('FEHLER: esc/renderTable nicht exportierbar.');
  process.exit(1);
}

/* ── Faelle ─────────────────────────────────────────────────────────────── */
let fehler = 0;
function pruefe(name, bedingung, zusatz) {
  if (bedingung) { console.log('[OK  ] ' + name); return; }
  console.log('[FEHL] ' + name + (zusatz ? ' — ' + zusatz : ''));
  fehler++;
}

// (1) esc() muss Anfuehrungszeichen maskieren — es wird in Attributen benutzt.
const roh = `a"b'c<d>e&f`;
const maskiert = P.esc(roh);
pruefe('esc maskiert doppelte Anfuehrungszeichen',
  !maskiert.includes('"'), 'Ergebnis: ' + maskiert);
pruefe('esc maskiert einfache Anfuehrungszeichen',
  !maskiert.includes("'"), 'Ergebnis: ' + maskiert);
pruefe('esc maskiert spitze Klammern',
  !maskiert.includes('<') && !maskiert.includes('>'), 'Ergebnis: ' + maskiert);

// (3) pdf_url: nur der erwartete Host darf zum Link werden.
const ZIELE = [
  ['javascript:alert(1)', false],
  ['data:text/html,<svg onload=alert(1)>', false],
  ['https://boeser-host.example/x.pdf', false],
  ['//boeser-host.example/x.pdf', false],
  ['https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2026/20019999.pdf', true],
];
if (typeof P.pdfhref === 'function') {
  ZIELE.forEach(function (z) {
    const erlaubt = P.pdfhref(z[0]) !== '';
    pruefe('pdfhref ' + (z[1] ? 'erlaubt' : 'verwirft') + ': ' + z[0].slice(0, 44),
      erlaubt === z[1], 'ergab ' + (erlaubt ? 'erlaubt' : 'verworfen'));
  });
} else {
  pruefe('pdfhref existiert und prueft das Linkziel', false,
    'keine solche Funktion in der Seite — das Linkziel wird ungeprueft eingesetzt');
}

// (2) Vollstaendiger Durchlauf mit boesartigen Werten: nichts davon darf
//     unmaskiert in der Tabelle landen.
const GIFT = '"><svg onload=alert(1)>';
const daten = {
  trades: [{
    filing_date: GIFT, tx_date: GIFT, politician: GIFT, district: GIFT,
    action: GIFT, asset_type: GIFT, amount_range: GIFT, owner: GIFT,
    ticker: GIFT, is_buy: true,
    pdf_url: 'javascript:alert(1)'
  }],
  roster: [], kpis: {}
};
try {
  P.renderTable(daten);
  const aus = hole('ct-body').innerHTML;
  pruefe('renderTable laesst kein <svg aus Fremddaten durch',
    !/<svg/i.test(aus), 'gefunden in der Ausgabe');
  /* Auf die STRUKTUR pruefen, nicht auf das Teilwort. Nach korrektem Maskieren
     steht "onload=" als harmloser Text in der Zelle, weil das < maskiert ist —
     ein Test, der die Zeichenkette irgendwo sucht, faellt dann faelschlich durch
     und sagt nichts ueber die Gefahr. Gefaehrlich ist ein Ereignis-Attribut
     INNERHALB eines echten Tags. */
  pruefe('renderTable erzeugt kein Ereignis-Attribut in einem Tag',
    !/<[^>]*\bon[a-z]+\s*=/i.test(aus), 'gefunden in der Ausgabe');
  pruefe('renderTable setzt kein javascript:-Linkziel',
    !/javascript:/i.test(aus), 'gefunden in der Ausgabe');
} catch (e) {
  pruefe('renderTable laeuft mit boesartigen Daten durch', false, e.message);
}

console.log(fehler === 0
  ? '\nAlle Faelle bestanden.'
  : '\n' + fehler + ' Fall/Faelle durchgefallen.');
process.exit(fehler === 0 ? 0 : 1);

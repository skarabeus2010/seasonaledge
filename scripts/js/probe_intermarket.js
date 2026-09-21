/* Faehrt das inline-JS von /intermarket gegen die ECHTEN Daten, mit einem
   DOM-Stub. "node --check" sagt nur, dass es sich parsen laesst — hier soll
   herauskommen, ob die Matrix tatsaechlich Zellen erzeugt und die Detailansicht
   ohne Fehler durchlaeuft. */
const fs = require('fs');
const path = require('path');

const REPO = path.resolve(__dirname, '..', '..');
const SEITE = path.join(REPO, 'landing/pages/intermarket.html');
const DATEN = path.join(REPO, 'landing/data/intermarket_matrix.json');
const daten = JSON.parse(fs.readFileSync(DATEN, 'utf8'));

/* Das JS wird aus der SEITE gezogen, nicht aus einer Kopie. Eine Kopie waere
   genau der Fehler, den dieser Waechter verhindern soll: er wuerde dann eine
   Fiktion pruefen und gruen bleiben, waehrend die echte Seite kaputt ist. */
function inlineJs() {
  const html = fs.readFileSync(SEITE, 'utf8');
  const bloecke = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
  if (!bloecke.length) throw new Error('kein inline-<script> in ' + SEITE);
  return bloecke.reduce((a, b) => (b.length > a.length ? b : a));
}

const elemente = {};
function macheElement(id) {
  return {
    id: id,
    _html: '',
    _text: '',
    style: {},
    value: '',
    classList: { add() {}, remove() {}, contains() { return false; } },
    set innerHTML(v) { this._html = v; },
    get innerHTML() { return this._html; },
    set textContent(v) { this._text = v; },
    get textContent() { return this._text; },
    addEventListener() {},
    scrollIntoView() {},
    closest() { return null; }
  };
}
for (const id of ['error-banner', 'kpis', 'verdict-big', 'mx', 'legend', 'detail',
                  'hint-tbl', 'btn-auf', 'btn-ab', 'sel-view']) {
  elemente[id] = macheElement(id);
}

global.document = {
  readyState: 'complete',
  getElementById: (id) => elemente[id] || macheElement(id),
  addEventListener() {}
};
global.window = { SA: null };
global.loadComponent = function () {};
global.fetch = function () {
  return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(daten) });
};

eval(inlineJs());

setTimeout(() => {
  let fehler = 0;
  const pruefe = (bedingung, was) => {
    if (bedingung) { console.log('  ok   ' + was); }
    else { console.log('  FEHL ' + was); fehler++; }
  };

  const mx = elemente['mx']._html;
  const zellen = (mx.match(/class="cell[^"]*"/g) || []).length;
  const leer = (mx.match(/class="cell na"/g) || []).length;
  const hinweise = (mx.match(/class="cell hint"/g) || []).length;

  console.log('Matrix:');
  pruefe(mx.length > 1000, 'Matrix-HTML erzeugt (' + mx.length + ' Zeichen)');
  pruefe(zellen > 200, zellen + ' Zellen gezeichnet, davon ' + leer + ' leer, ' + hinweise + ' Hinweise');
  pruefe(mx.includes('Anleihen 20J+'), 'Zeilenkopf "Anleihen 20J+" vorhanden');
  pruefe(mx.includes('rgba(232,168,32'), 'Farbskala angewendet');
  pruefe(!mx.includes('undefined'), 'kein "undefined" im Matrix-HTML');
  pruefe(!mx.includes('NaN'), 'kein "NaN" im Matrix-HTML');

  console.log('KPIs und Verdikt:');
  const k = elemente['kpis']._html;
  pruefe(k.includes(String(daten.n_zellen)), 'KPI zeigt ' + daten.n_zellen + ' geprüfte Paare');
  pruefe(k.includes(String(daten.n_primaer)), 'KPI zeigt Primärfamilie ' + daten.n_primaer);
  pruefe(!k.includes('undefined'), 'kein "undefined" in den KPIs');
  pruefe(elemente['verdict-big']._text.includes(String(daten.n_primaer)),
    'Verdikt nennt die Zahl: "' + elemente['verdict-big']._text + '"');

  console.log('Hinweis-Tabelle:');
  const h = elemente['hint-tbl']._html;
  const zeilen = (h.match(/<tr>/g) || []).length - 1;
  pruefe(zeilen > 5, zeilen + ' Hinweis-Zeilen');
  pruefe(h.includes('Silber'), 'stärkste Zelle (Silber) steht drin');
  pruefe(!h.includes('undefined'), 'kein "undefined" in der Tabelle');
  pruefe(!h.includes('NaN'), 'kein "NaN" in der Tabelle');

  console.log('Legende:');
  pruefe(elemente['legend']._html.includes('Stärke'), 'Legende erklärt Farbe = Stärke');

  console.log('');
  console.log(fehler === 0 ? 'ALLE PRUEFUNGEN BESTANDEN' : fehler + ' FEHLER');
  process.exit(fehler === 0 ? 0 : 1);
}, 200);

/* Prueft die Abschnittsschaltung und die Ladegeneration auf /polymarket.

   REGEL ZUR KENNUNG `[Ausnahme]`: eine Zeile, die nur sagt, dass der
   Produktivcode geworfen hat. Der Mutationstest verwirft sie — ein
   Absturz ist kein Nachweis einer Wirkung.

   REGEL ZUR KENNUNG `[Aufbau]`: sie steht NUR an Pruefungen, die eine
   Eigenschaft der TESTVORRICHTUNG behaupten (traegt die Seite vier Kennungen?
   haengt Lauf A wirklich?). Niemals an einer Aussage ueber den Produktivcode —
   dort macht sie den Mutationstest blind, weil ein Reissen als „Geruest
   zerstoert" gilt. Dieser Fehler ist mir in dieser Datei DREIMAL unterlaufen
   (gleiche Trefferzahl, Lauf D raeumt die Meldung, Fed sichtbar), und jedes Mal
   hat erst der Mutationstest ihn gemeldet.

   Anlass: Codex-Befund 15. Der Kategorienwechsel liess Altes stehen — im
   else-Zweig stand `renderFedPath(state.history)`, der Fed-Pfad wurde also aus
   dem GEFILTERTEN Katalog gerechnet und blieb sichtbar; bei den uebrigen
   Abschnitten passierte gar nichts, die Kacheln der vorigen Kategorie blieben
   stehen.

   Diese Probe faehrt `reload()` ECHT, mit steuerbaren Versprechen. Der
   Ueberholfall tritt damit wirklich ein: Lauf A wird angehalten, Lauf B laeuft
   durch, dann wird A freigegeben. Eine Nachbildung der Reihenfolge wuerde
   nichts ueber die Produktion sagen — in diesem Projekt ist das dreimal
   teuer geworden.

   Beim Schreiben dieser Probe sind zwei Fehler im Fix selbst aufgefallen: die
   Generationspruefung stand hinter der ersten Zustandsaenderung, und nach dem
   zweiten asynchronen Sprung fehlte sie ganz.

   Aufbaupruefungen tragen `[Aufbau]`; reisst eine davon, hat eine Mutation das
   Geruest zerstoert und ihr Rot beweist nichts (Mechanik aus Phase D). */
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
function sicher(was, fn) {
  try { fn(); return true; }
  catch (e) { pruefe(false, was + ' warf eine Ausnahme: ' + e.message); return false; }
}

// ── DOM-Attrappe mit echter Geschwisterkette ───────────────────────────────
// Die Kette ist der Kern: `abschnittSichtbar` laeuft von seiner Ueberschrift
// ueber `nextElementSibling` bis zur naechsten Ueberschrift. Eine Attrappe
// ohne echte Reihenfolge wuerde die Abbruchbedingung nicht pruefen.
function el(tag, klassen, id) {
  const o = {
    tagName: tag, id: id || '', _html: '', _text: '', value: '',
    style: {}, dataset: {}, _attr: {}, _kinder: [], checked: false, type: '',
    nextElementSibling: null,
    classList: {
      _k: new Set(klassen || []),
      add(c) { this._k.add(c); }, remove(c) { this._k.delete(c); },
      toggle() {}, contains(c) { return this._k.has(c); }
    },
    appendChild(k) { this._kinder.push(k); return k; },
    addEventListener() {}, removeAttribute() {},
    setAttribute(n, v) { this._attr[n] = v; },
    getAttribute(n) { return n in this._attr ? this._attr[n] : null; },
    querySelectorAll() { return []; }, querySelector() { return null; },
    closest() { return null; }, focus() {}
  };
  Object.defineProperty(o, 'innerHTML', {
    get() { return this._html; }, set(v) { this._html = String(v); }
  });
  Object.defineProperty(o, 'textContent', {
    get() { return this._text; }, set(v) { this._text = String(v); this._kinder = []; }
  });
  return o;
}

// Die Abschnittsnamen kommen aus der SEITE, nicht aus einer Liste hier. Sonst
// pruefte die Attrappe ihre eigene Annahme: eine umbenannte Kennung in der
// Seite erreichte sie nicht, und die Schaltung haette still verpuffen koennen,
// ohne dass die Probe rot wird. Genau das hat der Mutationstest gemeldet.
const seiteRoh = fs.readFileSync(SEITE, 'utf8');
const abschnittsNamen = [...seiteRoh.matchAll(/class="section-hdr" data-abschnitt="([^"]+)"/g)]
  .map(m => m[1]);

const kette = [];
const koepfe = {};
for (const name of abschnittsNamen) {
  const kopf = el('H2', ['section-hdr']);
  kopf.setAttribute('data-abschnitt', name);
  koepfe[name] = kopf;
  const a = el('P'), b = el('DIV');
  a._marke = name + '-inhalt-1';
  b._marke = name + '-inhalt-2';
  kette.push(kopf, a, b);
}
for (let i = 0; i < kette.length - 1; i++) kette[i].nextElementSibling = kette[i + 1];

const nachId = {};
const holeId = (id) => nachId[id] || (nachId[id] = el('DIV', [], id));
nachId['sel-history'] = el('SELECT', [], 'sel-history'); nachId['sel-history'].value = '90';
nachId['sel-category'] = el('SELECT', [], 'sel-category'); nachId['sel-category'].value = 'all';

const zuhoerer = {};
global.document = {
  readyState: 'complete',
  getElementById: holeId,
  createElement: (t) => el(t),
  createTextNode: (t) => ({ _istText: true, nodeValue: String(t) }),
  querySelector: (sel) => {
    const m = /^\.section-hdr\[data-abschnitt="([^"]+)"\]$/.exec(sel);
    return m ? (koepfe[m[1]] || null) : null;
  },
  querySelectorAll: (sel) => (sel === '.section-hdr' ? Object.values(koepfe) : []),
  // Die Zuhoerer werden MITGESCHRIEBEN, nicht verworfen: nur so laesst
  // sich pruefen, ob die Seite auf `sa:i18n-bereit` reagiert.
  addEventListener(typ, fn) {
    (zuhoerer[typ] = zuhoerer[typ] || []).push(fn);
  }
};
global.window = { SA: null, addEventListener() {}, location: { search: '' } };
global.ApexCharts = class { constructor() {} render() {} updateOptions() {} destroy() {} };

// ── Modul laden, damit SA.polymarket.esc und SA.i18n existieren ────────────
// Keine eigene SA-Bindung: das evaluierte Modul legt `var SA` bereits in
// DIESEN Bereich und es traegt das richtige Objekt. Eine zweite Deklaration
// waere ein Syntaxfehler, eine Kopie ein zweiter Zustand.
eval(fs.readFileSync(path.join(REPO, 'landing/js/polymarket.js'), 'utf8'));
SA.chartTheme = { chart: {}, grid: {}, xaxis: {}, yaxis: {} };
SA.i18n = { t: (k, f) => f || k };
global.SA = SA;

// ── Funktionen aus der Seite schneiden ─────────────────────────────────────
function ausSeite(quelle, name) {
  const start = quelle.indexOf('function ' + name + '(');
  if (start < 0) throw new Error('nicht gefunden: ' + name);
  let tiefe = 0;
  for (let j = quelle.indexOf('{', start); j < quelle.length; j++) {
    if (quelle[j] === '{') tiefe++;
    else if (quelle[j] === '}') { tiefe--; if (tiefe === 0) return quelle.slice(start, j + 1); }
  }
  throw new Error('Klammern nicht ausgeglichen: ' + name);
}
const seite = seiteRoh;

// Die Ladegeneration ist eine Modulvariable der Seite, nicht Teil einer
// Funktion — sie wird hier mit derselben Zeile aus der Seite uebernommen.
const genZeile = /var ladeGeneration = 0;/.exec(seite);
if (!genZeile) { console.log('  FEHL [Aufbau] ladeGeneration nicht in der Seite gefunden'); process.exit(1); }
eval(genZeile[0]);

const state = { markets: [], allMarkets: [], selectedCids: new Set(), latest: {}, history: [] };
global.state = state;
for (const n of ['abschnittSichtbar', 'applyCategoryFilter', 'reload', 'showError',
                 'clearError', 'showLoading', 'hideLoading', 'renderCheckboxes']) {
  eval(ausSeite(seite, n));
}
// Die uebrigen Renderer sind fuer diese Probe ohne Belang; sie werden gezaehlt,
// damit sich pruefen laesst, was NICHT gerechnet wurde.
const gerechnet = [];
global.renderFedPath = () => gerechnet.push('fed');
global.renderRisk = () => gerechnet.push('risiko');
global.renderCrypto = () => gerechnet.push('krypto');
global.renderHistoryChart = () => {};
// `starteSeite()` verweist darauf; ohne Stub stirbt die Probe an einem
// ReferenceError statt den Fall zu pruefen.
global.loadBrierStats = () => {};
global.renderTable = () => {};

// ── Steuerbare Datenquelle ─────────────────────────────────────────────────
let halteKatalog = null, haltePreise = null;
const katalog = [
  { condition_id: 'f1', slug: 'fed-1', question: 'Fed 1', category: 'fed', active: true },
  { condition_id: 'c1', slug: 'btc-1', question: 'BTC 1', category: 'crypto', active: true }
];
SA.polymarket.loadCatalog = () => new Promise(r => {
  if (halteKatalog) halteKatalog.push(() => r(katalog)); else r(katalog);
});
SA.polymarket.loadLatestPrices = () => new Promise(r => {
  if (haltePreise) haltePreise.push(() => r({})); else r({});
});
SA.polymarket.loadHistory = () => new Promise(r => {
  if (haltePreise) haltePreise.push(() => r([])); else r([]);
});

// Beide vertragen einen unbekannten Namen. Sonst stirbt die Probe an einem
// TypeError, sobald eine Kennung in der Seite umbenannt wurde — und ein
// Absturz ist kein Befund, sondern ein Abbruch: der beabsichtigte Fall waere
// nie geprueft worden.
const sichtbar = (name) => {
  const k = koepfe[name];
  return !!k && k.style.display !== 'none';
};
const inhaltSichtbar = (name) => {
  const teile = kette.filter(e => e._marke && e._marke.startsWith(name));
  return teile.length > 0 && teile.every(e => e.style.display !== 'none');
};

// ── Pruefungen ─────────────────────────────────────────────────────────────
(async () => {
  console.log('Abschnittsschaltung:');
  pruefe(abschnittsNamen.length === 4,
    '[Aufbau] die Seite traegt 4 Abschnittskennungen: ' + abschnittsNamen.join(', '));
  sicher('abschnittSichtbar(false)', () => abschnittSichtbar('risiko', false));
  pruefe(!sichtbar('risiko'), 'Ueberschrift verborgen');
  pruefe(!inhaltSichtbar('risiko'), 'Inhalt des Abschnitts verborgen');
  // Die Abbruchbedingung: der Nachbarabschnitt darf NICHT mitverborgen werden.
  pruefe(sichtbar('krypto'), 'der naechste Abschnitt bleibt sichtbar');
  pruefe(sichtbar('fed'), 'der vorige Abschnitt bleibt sichtbar');
  sicher('abschnittSichtbar(true)', () => abschnittSichtbar('risiko', true));
  pruefe(sichtbar('risiko') && inhaltSichtbar('risiko'), 'wieder einschaltbar');
  sicher('unbekannter Abschnitt', () => abschnittSichtbar('gibtsnicht', false));
  pruefe(abschnittSichtbar('gibtsnicht', false) === false,
    'unbekannter Abschnitt meldet false statt still zu verpuffen');
  // Ohne diese Pruefung bleibt eine umbenannte Kennung unbemerkt: die Schaltung
  // tut dann gar nichts, und alle Aussagen darueber sind leer. Von der
  // Gegenprobe des Mutationstests aufgedeckt.
  pruefe(['fed', 'risiko', 'krypto', 'divergenz'].every(n => abschnittSichtbar(n, true) === true),
    'alle vier Abschnitte sind ueber ihre Kennung auffindbar');

  console.log('Kategorie Crypto: Fed wird weder gezeigt noch gerechnet:');
  gerechnet.length = 0;
  nachId['sel-category'].value = 'crypto';
  await reload();
  pruefe(gerechnet.length > 0, '[Aufbau] ueberhaupt etwas gerechnet');
  pruefe(!gerechnet.includes('fed'), 'renderFedPath NICHT gerufen');
  pruefe(!sichtbar('fed'), 'Fed-Abschnitt verborgen');
  pruefe(gerechnet.includes('krypto') && sichtbar('krypto'), 'Krypto gerechnet und sichtbar');
  pruefe(sichtbar('divergenz'), 'Divergenz-Abschnitt sichtbar (haengt an Krypto)');

  console.log('Kategorie Fed: Krypto UND Divergenz verborgen:');
  nachId['sel-category'].value = 'fed';
  await reload();
  pruefe(sichtbar('fed'), 'Fed-Abschnitt sichtbar bei Kategorie fed');
  pruefe(!sichtbar('krypto'), 'Krypto-Abschnitt verborgen');
  pruefe(!sichtbar('divergenz'), 'Divergenz-Abschnitt verborgen (haengt an Krypto)');

  console.log('Leere Kategorie: alle datengetriebenen Abschnitte verborgen:');
  nachId['sel-category'].value = 'gibtsnicht';
  await reload();
  pruefe(!sichtbar('fed') && !sichtbar('risiko') && !sichtbar('krypto')
         && !sichtbar('divergenz'),
    'nichts aus der vorigen Kategorie bleibt stehen');
  pruefe(holeId('error-banner').style.display === 'block', 'Meldung sichtbar');
  pruefe(holeId('error-banner').textContent.length > 0, '[Aufbau] Meldung hat Text');

  console.log('Fehlermeldung bleibt bis zum naechsten Erfolg:');
  nachId['sel-category'].value = 'all';
  await reload();
  pruefe(holeId('error-banner').style.display === 'none', 'nach Erfolg geraeumt');

  console.log('Ladegeneration: der ueberholte Lauf schreibt NICHT:');
  // Lauf A anhalten, Lauf B vollstaendig durchlaufen lassen, dann A freigeben.
  nachId['sel-category'].value = 'fed';
  const angehalten = [];
  halteKatalog = angehalten;
  const laufA = reload();
  pruefe(angehalten.length === 1, '[Aufbau] Lauf A haengt am Katalog');
  halteKatalog = null;
  nachId['sel-category'].value = 'crypto';
  await reload();
  const nachB = state.markets.map(m => m.condition_id).join(',');
  pruefe(nachB === 'c1', '[Aufbau] Lauf B hat geschrieben: ' + nachB);
  // Jetzt A freigeben. Er darf den Zustand von B nicht mehr anfassen.
  gerechnet.length = 0;
  angehalten.forEach(fn => fn());   // gibt Lauf A frei
  await laufA;
  pruefe(state.markets.map(m => m.condition_id).join(',') === 'c1',
    'A hat state.markets NICHT ueberschrieben');
  pruefe(!gerechnet.includes('fed'), 'A hat nicht nachtraeglich gerendert');

  console.log('Der ueberholte Lauf schreibt auch hinter dem ZWEITEN Sprung nicht:');
  // Jetzt wird nicht der Katalog angehalten, sondern die PREISE. Damit kommt
  // Lauf E durch die erste Sperre und bleibt hinter ihr haengen — genau die
  // Stelle, an der die zweite Sperre sitzt.
  nachId['sel-category'].value = 'fed';
  const angehalten2 = [];
  haltePreise = angehalten2;
  const laufE = reload();
  // Der Katalog laeuft frei durch, also muessen hier BEIDE Abrufe (Preise und
  // Historie) haengen.
  await new Promise(r => setTimeout(r, 0));
  pruefe(angehalten2.length === 2,
    '[Aufbau] Lauf E haengt an Preisen und Historie (' + angehalten2.length + ')');
  haltePreise = null;
  nachId['sel-category'].value = 'crypto';
  await reload();
  pruefe(state.markets.map(m => m.condition_id).join(',') === 'c1',
    '[Aufbau] Lauf F hat geschrieben');
  state.latest = { MARKE: 'von F' };
  gerechnet.length = 0;
  angehalten2.forEach(fn => fn());   // gibt Lauf E frei
  await laufE;
  pruefe(state.latest && state.latest.MARKE === 'von F',
    'E hat state.latest NICHT ueberschrieben (jetzt: '
    + JSON.stringify(state.latest) + ')');
  pruefe(!gerechnet.includes('fed'),
    'E hat hinter dem zweiten Sprung nicht nachtraeglich gerendert');

  console.log('Verspaetetes SCHEITERN von Lauf A ueberschreibt B nicht:');
  // Von Codex an den unveraenderten Seitenfunktionen reproduziert: die
  // Generationspruefung im Erfolgspfad allein genuegte nicht — der Fehlerpfad
  // hatte keine, und eine spaete Ablehnung von A setzte die Fehlermeldung
  // ueber den Erfolg von B.
  nachId['sel-category'].value = 'fed';
  const ablehner = [];
  SA.polymarket.loadCatalog = () => new Promise((_, ab) => ablehner.push(ab));
  const laufC = reload();
  pruefe(ablehner.length === 1, '[Aufbau] Lauf C haengt und kann scheitern');
  SA.polymarket.loadCatalog = () => Promise.resolve(katalog);
  nachId['sel-category'].value = 'all';
  await reload();
  pruefe(holeId('error-banner').style.display === 'none',
    'Lauf D raeumt die Meldung (Vorbedingung des naechsten Falls)');
  ablehner[0](new Error('verspaeteter Fehler von C'));
  await laufC;
  pruefe(holeId('error-banner').style.display === 'none',
    'die verspaetete Ablehnung setzt KEINE Fehlermeldung ueber den Erfolg');

  // ── Die Divergenz-Tabelle hat ihre EIGENE asynchrone Stufe ───────────────
  // Die Pruefungen oben stubben renderCrypto() weg, also war dieser Pfad
  // ungeprueft — Codex hat das in der Abnahme beanstandet. Hier laeuft die
  // echte Seitenfunktion, mit einer steuerbaren Kursabfrage.
  console.log('Die Divergenz-Tabelle schreibt nicht, wenn sie ueberholt wurde:');
  eval(ausSeite(seite, 'renderDivergenceFor'));
  const ziel = { innerHTML: '' };
  nachId['divergence-btc'] = ziel;
  let kursAufloeser = null;
  SA.fetchAllPrices = () => new Promise(r => { kursAufloeser = r; });
  // Wirft die Seitenfunktion in ihrem then-Zweig, wird daraus eine
  // unbehandelte Ablehnung und node beendet den Lauf, BEVOR das Urteil steht.
  // Ein Absturz ist kein Befund — er wird hier eingefangen und als Fehler
  // DIESER Pruefung gemeldet.
  let rendererFehler = null;
  process.on('unhandledRejection', (e) => { rendererFehler = e; });
  // Eine Tabelle zu bauen braucht Markets; ohne sie meldet die Funktion „keine
  // Markets" — auch das ist ein Schreibvorgang, also taugt der Fall.
  state.markets = [{ condition_id: 'c1', slug: 'btc-above-150k-2026' }];
  renderDivergenceFor('BTC-USD', 'btc', 'divergence-btc');
  pruefe(typeof kursAufloeser === 'function',
    '[Aufbau] die Kursabfrage haengt und ist steuerbar');
  ladeGeneration++;                       // der Nutzer klickt weiter
  ziel.innerHTML = 'NEUER INHALT';
  kursAufloeser([{ date: '2024-03-15', close: 100 },
                 { date: '2024-12-31', close: 150 }]);
  await new Promise(r => setTimeout(r, 0));
  // Zwei GETRENNTE Aussagen. Die Ausnahme bekommt die Kennung `[Ausnahme]`,
  // damit der Mutationstest sie verwirft statt sie als gefangene Mutation zu
  // zaehlen: ein ReferenceError beweist nicht, dass die Sperre wirkt — er
  // beweist nur, dass der Code nicht mehr laeuft (Codex, Abnahme Runde 2).
  pruefe(!rendererFehler,
    '[Ausnahme] der Renderer lief ohne zu werfen'
    + (rendererFehler ? ' — warf: ' + rendererFehler.message : ''));
  pruefe(ziel.innerHTML === 'NEUER INHALT',
    'die verspaetete Antwort ueberschreibt den neuen Inhalt NICHT (jetzt: '
    + JSON.stringify(ziel.innerHTML.slice(0, 30)) + ')');

  // Der FEHLERPFAD der Divergenz-Tabelle. Codex, Abnahme Runde 2: das
  // Entfernen dieser Sperre lief gruen durch, weil die Probe nur den
  // Erfolgspfad stellte.
  console.log('Auch eine ueberholte ABLEHNUNG schreibt nicht:');
  const ziel2 = { innerHTML: '' };
  nachId['divergence-eth'] = ziel2;
  let kursAblehner = null;
  SA.fetchAllPrices = () => new Promise((_, ab) => { kursAblehner = ab; });
  renderDivergenceFor('ETH-USD', 'eth', 'divergence-eth');
  pruefe(typeof kursAblehner === 'function',
    '[Aufbau] die Kursabfrage haengt und kann scheitern');
  ladeGeneration++;
  ziel2.innerHTML = 'ZWEITER INHALT';
  kursAblehner(new Error('verspaeteter Kursfehler'));
  await new Promise(r => setTimeout(r, 0));
  pruefe(!rendererFehler,
    '[Ausnahme] der Fehlerpfad lief ohne selbst zu werfen'
    + (rendererFehler ? ' — warf: ' + rendererFehler.message : ''));
  pruefe(ziel2.innerHTML === 'ZWEITER INHALT',
    'die verspaetete Ablehnung setzt KEINE Fehlermeldung (jetzt: '
    + JSON.stringify(ziel2.innerHTML.slice(0, 30)) + ')');

  // ── Die Uebersetzung kommt spaeter als der erste Aufbau ──────────────────
  // Codex, Abnahme Runde 4: die Seite startet per Zeitgeber (200/400 ms).
  // Ist das Woerterbuch dann noch nicht da, liefert `SA.i18n.t` den deutschen
  // Ersatztext — und ohne Neuausgabe bleibt er stehen, auch wenn EN eine
  // Sekunde spaeter ankommt. `landing/js/i18n.js` sendet dafuer
  // `sa:i18n-bereit` (Zeile ~475).
  console.log('Die Seite rendert neu, wenn das Woerterbuch spaeter kommt:');
  // Die Verdrahtung liegt in einer eigenen Funktion, damit sie hier
  // ausfuehrbar ist; im DOMContentLoaded-Block waere sie unerreichbar.
  //
  // Die Einbindung wird AUSGEFUEHRT, nicht gesucht. Eine Quellpruefung liess
  // `// verdrahteUebersetzung();` und `if (false) verdrahteUebersetzung();`
  // durch (Codex, Abnahme Runde 6) — und meine Angabe ihrer Grenze war dazu
  // noch falsch. Hier laeuft der echte Start der Seite.
  eval(ausSeite(seite, 'verdrahteUebersetzung'));
  eval(ausSeite(seite, 'starteSeite'));
  // Die Zeitgeber des Starts werden verworfen: reload() und loadBrierStats()
  // wurden oben schon geprueft, und ein zweiter Lauf wuerde die Zaehler
  // dieses Falls verfaelschen.
  const echterTimeout = global.setTimeout;
  global.setTimeout = () => 0;
  delete zuhoerer['sa:i18n-bereit'];
  try {
    starteSeite();
  } finally {
    global.setTimeout = echterTimeout;
  }
  pruefe((zuhoerer['sa:i18n-bereit'] || []).length === 1,
    'der AUSGEFUEHRTE Start registriert den Uebersetzungs-Zuhoerer ('
    + (zuhoerer['sa:i18n-bereit'] || []).length + ')');
  // Die letzte Meile: DASS der Start ueberhaupt gerufen wird, prueft diese
  // Probe nicht ausfuehrend, weil sie `starteSeite()` selbst ruft. Hier stand
  // zuerst, das sei ohne Netz und Cron-Daten gar nicht moeglich — das ist
  // FALSCH, und Codex hat es in Runde 7 widerlegt: er hat den ganzen
  // Seiten-Block mit DOM-Attrappe und abgefangenen Zeitgebern ausgewertet und
  // DOMContentLoaded ueber EventTarget ausgeloest. Es ist also eine bewusste
  // Beschraenkung dieser Probe und keine Unmoeglichkeit — wer sie aufheben
  // will, hat damit den Weg. Geprueft wird einstweilen die eine
  // Registrierungszeile in der Quelle.
  // GRENZE, benannt statt behauptet: eine BEDINGTE Registrierung
  // (`if (x) document.addEventListener('DOMContentLoaded', starteSeite)`)
  // wuerde dieses Muster weiter erfuellen. Erkannt wird das Entfernen der
  // Zeile und ein anderes Ereignis.
  pruefe(/document\.addEventListener\('DOMContentLoaded', starteSeite\);/.test(seite),
    'die Quelle registriert starteSeite auf DOMContentLoaded');
  const bereitZuhoerer = (zuhoerer['sa:i18n-bereit'] || []);
  pruefe(bereitZuhoerer.length >= 1,
    'die Seite registriert einen Zuhoerer auf sa:i18n-bereit ('
    + bereitZuhoerer.length + ')');
  if (bereitZuhoerer.length) {
    gerechnet.length = 0;
    let brierNeu = 0;
    const alteBrier = global.loadBrierStats;
    global.loadBrierStats = () => { brierNeu++; };
    bereitZuhoerer.forEach(fn => fn(new Event('sa:i18n-bereit')));
    await new Promise(r => setTimeout(r, 0));
    pruefe(gerechnet.length > 0,
      'der Zuhoerer stoesst den Aufbau erneut an (gerechnet: '
      + JSON.stringify(gerechnet) + ')');
    pruefe(brierNeu === 1,
      'und die Brier-Ausgabe ebenfalls, genau einmal (' + brierNeu + ')');
    global.loadBrierStats = alteBrier;
  }

  console.log('');
  console.log(fehler === 0 ? 'ALLE PRUEFUNGEN BESTANDEN' : fehler + ' FEHLER');
  console.log('PROBE-ENDE ' + anzahl + ' Pruefungen, ' + fehler + ' Fehler');
  process.exit(fehler === 0 ? 0 : 1);
})().catch(e => {
  console.log('  FEHL Probe abgebrochen: ' + e.message);
  console.log('PROBE-ENDE ' + anzahl + ' Pruefungen, ' + (fehler + 1) + ' Fehler');
  process.exit(1);
});

/* Prueft, dass externe Texte auf /polymarket maskiert bei der Ausgabe ankommen.

   Anlass: Codex-Befund 8. ApexCharts schreibt Legendennamen und Tooltip-Titel per
   `innerHTML` — am ausgelieferten Bundle nachgeprueft:

     x.classList.add("apexcharts-legend-text"), x.innerHTML = ... l

   Damit ist der Seriennamen ein HTML-Pfad, und `question` kam dort roh an.

   ZWEI Dinge, die diese Probe bewusst anders macht:

   (1) Sie prueft den WERT, nicht ein Wort. „Die Nutzlast kommt im Text nicht vor"
       waere eine falsche Behauptung: nach korrekter Maskierung steht `onerror=`
       weiter als Teilstring in `&lt;img src=x onerror=alert(1)&gt;` da. Geprueft
       wird deshalb, dass die oeffnende Klammer maskiert ist — `&lt;img` ja,
       `<img` nein.

   (2) Sie braucht KEINE Cron-Daten. Die anderen JS-Proben dieses Projekts
       (probe_skew_tabelle, probe_korrelationen, probe_wahlen_seite) laden
       gitignorierte Cron-Ausgaben und koennen deshalb nur auf dem Server laufen —
       was der Grund dafuer ist, dass keine von ihnen einen automatischen Aufrufer
       hat. Diese hier arbeitet mit synthetischen Eingaben und laeuft ueberall.

   Der Code wird aus den ECHTEN Dateien gezogen, nicht nachgebaut. */
const fs = require('fs');
const path = require('path');

const REPO = path.resolve(__dirname, '..', '..');
const MODUL = path.join(REPO, 'landing/js/polymarket.js');
const SEITE = path.join(REPO, 'landing/pages/polymarket.html');

// ── Nutzlasten ───────────────────────────────────────────────────────────────
// Jede traegt eine oeffnende Klammer oder ein Anfuehrungszeichen — genau die
// Zeichen, deren Maskierung hier zur Debatte steht.
const P_FRAGE = '<img src=x onerror=alert(1)>Erreicht BTC 95k';
const P_SLUG  = '<svg onload=alert(2)>btc-95k';
const P_CID   = 'cid1" onmouseover="alert(3)';
const P_KAT   = '<b onclick=alert(4)>Krypto';

// ── DOM-Attrappe ─────────────────────────────────────────────────────────────
function neu(id) {
  const o = {
    id, _html: '', _text: '', _attr: {}, _kinder: [], type: '', checked: false,
    style: {}, dataset: {},
    classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
    appendChild(k) { this._kinder.push(k); return k; },
    addEventListener() {}, removeAttribute() {},
    setAttribute(n, v) { this._attr[n] = v; },
    getAttribute(n) { return n in this._attr ? this._attr[n] : null; },
    querySelectorAll() { return []; }, querySelector() { return null; },
    closest() { return null; }, focus() {}
  };
  Object.defineProperty(o, 'innerHTML', {
    get() { return this._html; },
    set(v) { this._html = String(v); this._htmlGesetzt = true; }
  });
  Object.defineProperty(o, 'textContent', {
    get() { return this._text; },
    set(v) { this._text = String(v); this._kinder = []; }
  });
  return o;
}
const el = {};
const hole = (id) => el[id] || (el[id] = neu(id));

// Ein Textknoten ist KEIN HTML-Pfad; sein Inhalt bleibt deshalb unmaskiert
// richtig. Die Attrappe haelt ihn als solchen auseinander.
function textKnoten(t) { return { _istText: true, nodeValue: String(t) }; }

global.document = {
  readyState: 'complete',
  getElementById: hole,
  createElement: (tag) => neu(tag),
  createTextNode: textKnoten,
  querySelectorAll: () => [], querySelector: () => null, addEventListener() {}
};
global.window = { SA: null, addEventListener() {}, location: { search: '' } };
global.ApexCharts = class {
  constructor(_el, opt) { global.__letzteApexOptionen = opt; }
  render() {} updateOptions() {} destroy() {}
};
global.fetch = () => Promise.resolve({ ok: false, status: 404, json: () => Promise.reject(new Error('kein Netz in der Probe')) });

// ── Modul laden ──────────────────────────────────────────────────────────────
eval(fs.readFileSync(MODUL, 'utf8'));
const PM = global.window.SA.polymarket;

// Das Thema kommt aus charts.js und ist fuer die Maskierung ohne Belang — hier
// stehen deshalb leere Objekte. Wird ein neues Thema-Feld benutzt, bricht die
// Probe mit einem klaren TypeError ab und fordert die Ergaenzung ein; sie
// meldet dann NICHT still gruen.
global.window.SA.chartTheme = { chart: {}, grid: {}, xaxis: {}, yaxis: {} };
// Die Uebersetzung verhaelt sich wie im deutschen Betrieb: sie gibt den
// Ersatztext zurueck. Ohne diesen Stub warf `renderCategoryTable` einen
// TypeError, sobald die Tabellenkoepfe uebersetzbar wurden — die Probe
// hat das gemeldet, statt still gruen zu bleiben.
global.window.SA.i18n = { t: (k, f) => (f === undefined ? k : f),
                          isEN: () => false };

// ── Eine benannte Funktion aus dem Inline-JS der Seite schneiden ─────────────
// Gezielt statt den ganzen Block zu evaluieren: der Block startet die Seite und
// wuerde Netz und Cron-Daten brauchen.
function funktionAusSeite(quelle, name) {
  const start = quelle.indexOf('function ' + name + '(');
  if (start < 0) throw new Error('Funktion nicht gefunden: ' + name);
  let i = quelle.indexOf('{', start), tiefe = 0;
  for (let j = i; j < quelle.length; j++) {
    if (quelle[j] === '{') tiefe++;
    else if (quelle[j] === '}') { tiefe--; if (tiefe === 0) return quelle.slice(start, j + 1); }
  }
  throw new Error('Klammern nicht ausgeglichen bei ' + name);
}

const seite = fs.readFileSync(SEITE, 'utf8');
// Keine eigene SA-Bindung: das evaluierte Modul hat `var SA` bereits in DIESEN
// Bereich gelegt und es traegt das richtige Objekt. Eine zweite Deklaration
// waere ein Syntaxfehler, und eine Kopie waere ein zweiter Zustand.
global.SA = global.window.SA;
const state = { markets: [], selectedCids: new Set() };
global.state = state;
global.showError = function () {};
eval(funktionAusSeite(seite, 'renderCheckboxes'));
eval(funktionAusSeite(seite, 'renderCategoryTable'));

// ── Pruefungen ───────────────────────────────────────────────────────────────
let fehler = 0;
let anzahlPruefungen = 0;
const pruefe = (b, was) => {
  anzahlPruefungen++;
  console.log((b ? '  ok   ' : '  FEHL ') + was);
  if (!b) fehler++;
};

// Jeder Aufruf in den Produktivcode laeuft hierueber: eine Ausnahme wird als
// BEFUND gemeldet und die Probe laeuft weiter. Sonst stirbt sie mitten im
// Durchlauf, und dann sagt ihr Rot nichts darueber aus, ob der beabsichtigte
// Fall geprueft wurde — der Mutationstest verlangt genau deshalb einen
// vollstaendigen Durchlauf (Codex-Befund, Runde 2).
function sicher(was, fn) {
  try {
    fn();
    return true;
  } catch (e) {
    pruefe(false, was + ' warf eine Ausnahme: ' + e.message);
    return false;
  }
}

// Direkt geprueft, nicht nur indirekt: das Inline-JS der Seite maskiert ueber
// `SA.polymarket.esc`. Fehlt der Export, soll das als eigener Befund erscheinen
// und nicht als Ausnahme irgendwo weiter unten.
console.log('Maskierungsfunktion am Modul:');
pruefe(typeof PM.esc === 'function', 'SA.polymarket.esc ist exportiert');
pruefe(typeof PM.esc === 'function' && PM.esc('<b>&"') === '&lt;b&gt;&amp;&quot;',
  'esc maskiert <, >, & und " vollstaendig');

console.log('Seriennamen im Verlaufs-Chart (ApexCharts-Legende, innerHTML-Pfad):');
sicher('renderHistoryMulti (Nutzlast)', () => PM.renderHistoryMulti('pm-hist', [{ condition_id: 'c1', question: P_FRAGE, slug: P_SLUG }],
  [{ condition_id: 'c1', ts: '2026-10-01T00:00:00Z', yes_price: 0.5 },
   { condition_id: 'c1', ts: '2026-10-02T00:00:00Z', yes_price: 0.6 }]));
const serien = (global.__letzteApexOptionen || {}).series || [];
pruefe(serien.length === 1, '[Aufbau] ' + serien.length + ' Serie(n) gebaut');
const sName = String((serien[0] || {}).name || '');
pruefe(sName.length > 0, '[Aufbau] Seriennamen gesetzt');
pruefe(!sName.includes('<img'), 'keine rohe oeffnende Klammer im Seriennamen');
pruefe(sName.includes('&lt;img'), 'oeffnende Klammer maskiert (&lt;img)');
// Der 40-Zeichen-Schnitt darf keine Entitaet zerschneiden: ein "&" am Ende ohne
// abschliessendes ";" waere genau dieser Fehler.
pruefe(!/&[a-z]{0,6}$/i.test(sName), 'keine abgeschnittene Entitaet am Ende');

// Eigener Fall fuer die REIHENFOLGE, denn die Nutzlast oben trifft ihn nicht:
// ihr maskierter Text hat an Position 40 keine Entitaet. Hier liegt das "&"
// bewusst an Stelle 37, damit "&amp;" die Positionen 36..40 belegt und ein
// Schnitt NACH dem Maskieren "&amp" stehen liesse.
const P_AMP = 'Erreicht BTC 95000 USD bis Jahresend&Ende';
// Vorbedingung pruefen statt Zeichen zu zaehlen: eine Probe, deren Aufbau
// stillschweigend daneben liegt, prueft nichts.
pruefe(P_AMP[36] === '&', '[Aufbau] das & liegt an Position 37 (Index 36)');
global.__letzteApexOptionen = null;
sicher('renderHistoryMulti (Entitaet)', () => PM.renderHistoryMulti('pm-hist-amp', [{ condition_id: 'c3', question: P_AMP, slug: 'x' }],
  [{ condition_id: 'c3', ts: '2026-10-01T00:00:00Z', yes_price: 0.5 }]));
const ampName = String(((global.__letzteApexOptionen || {}).series || [{}])[0].name || '');
// Vorbedingung, ohne die die beiden folgenden Pruefungen nichts aussagen: ein
// LEERER Name reisst sie ebenfalls, ohne dass die Maskierung nachgegeben hat.
// Genau darueber konnte eine Ausnahme hier indirekt als gefangene Mutation
// gelten (Codex-Befund, Runde 3).
pruefe(ampName.length > 0, '[Aufbau] Entitaets-Name wurde erzeugt');
pruefe(ampName.includes('&amp;'), 'das & ist vollstaendig maskiert: ' + JSON.stringify(ampName.slice(-12)));
pruefe(!/&(?:[a-z]{1,6}|#\d{0,6})?$/i.test(ampName), 'Entitaet am Schnittpunkt nicht zerschnitten');

// Der Seriennamen hat ZWEI Quellen: `question || slug`. Die Nutzlast oben
// kommt immer ueber `question`, also blieb eine Maskierung, die nur diesen
// Zweig abdeckt, unbemerkt gruen (von Codex an Phase D gefunden). Hier ist
// `question` leer, damit der Rueckfall wirklich gefahren wird.
console.log('Rueckfall auf den slug, wenn question leer ist:');
global.__letzteApexOptionen = null;
sicher('renderHistoryMulti (Rueckfall)', () => PM.renderHistoryMulti('pm-hist-slug', [{ condition_id: 'c4', question: '', slug: P_SLUG }],
  [{ condition_id: 'c4', ts: '2026-10-01T00:00:00Z', yes_price: 0.5 }]));
const slugName = String(((global.__letzteApexOptionen || {}).series || [{}])[0].name || '');
pruefe(slugName.length > 0, '[Aufbau] Rueckfall hat einen Namen gesetzt');
pruefe(!slugName.includes('<svg'), 'keine rohe oeffnende Klammer im Rueckfall');
pruefe(slugName.includes('&lt;svg'), 'oeffnende Klammer im Rueckfall maskiert');

console.log('Markt-Checkboxen in der Seitenleiste:');
state.markets = [{ condition_id: P_CID, slug: P_SLUG }];
state.selectedCids = new Set();
sicher('renderCheckboxes', () => renderCheckboxes());
const box = hole('market-checkboxes');
// Der Defekt WAR eine Zeichenketten-Verkettung in innerHTML. Wird sie wieder
// eingebaut, ist innerHTML gesetzt — das ist die Wirkung, die hier zaehlt.
pruefe(!box._htmlGesetzt, 'Liste nicht per innerHTML gebaut');
pruefe(box._kinder.length === 1, '[Aufbau] ' + box._kinder.length + ' Label-Element(e) angehaengt');
const label = box._kinder[0] || { _kinder: [] };
const eingabe = (label._kinder || []).find(k => !k._istText) || { _attr: {} };
pruefe(eingabe._attr['data-cid'] === P_CID, 'condition_id als Attributwert, nicht als Markup');
const sichtbar = (label._kinder || []).filter(k => k._istText).map(k => k.nodeValue).join('');
pruefe(sichtbar.includes(P_SLUG), 'slug als Textknoten (dort ist er unmaskiert richtig)');

console.log('Brier-Kategorietabelle:');
// Mit try/catch, damit ein Absturz als BEFUND gemeldet wird und nicht als
// Abbruch der Probe. Ohne das war „die Probe wurde rot" kein Beweis dafuer,
// dass eine Pruefung angesprochen hat — zum Beispiel wenn `SA.polymarket.esc`
// fehlt und der Aufruf an einem TypeError stirbt.
pruefe(sicher('renderCategoryTable', () => renderCategoryTable([{ category: P_KAT, markets: 3, forecasts: 9, brier: 0.2, baseline: 0.25 }])),
  '[Aufbau] Tabelle ohne Ausnahme gerendert');
const kat = hole('brier-categories')._html;
pruefe(kat.length > 100, '[Aufbau] ' + kat.length + ' Zeichen gerendert');
pruefe(!kat.includes('<b onclick'), 'keine rohe oeffnende Klammer in der Kategorie');
pruefe(kat.includes('&lt;b'), 'oeffnende Klammer maskiert (&lt;b)');

// ── Gegenprobe: harmlose Eingaben muessen unveraendert durchgehen ────────────
// Ohne sie koennte die Maskierung auch alles zerstoeren und die Probe bliebe
// gruen. Sie ist zugleich die gruene Grundlinie fuer den Mutationstest.
console.log('Gegenprobe mit harmlosen Eingaben:');
global.__letzteApexOptionen = null;
sicher('renderHistoryMulti (harmlos)', () => PM.renderHistoryMulti('pm-hist2', [{ condition_id: 'c2', question: 'Erreicht BTC 95k?', slug: 'btc-95k' }],
  [{ condition_id: 'c2', ts: '2026-10-01T00:00:00Z', yes_price: 0.5 }]));
const sauber = String(((global.__letzteApexOptionen || {}).series || [{}])[0].name || '');
// Auch die Gegenprobe braucht ihre Vorbedingung: ein LEERER Name reisst die
// folgende Pruefung ebenfalls, ohne dass die Maskierung etwas falsch gemacht
// hat. Ueber genau diese Luecke konnte eine Mutation, die nur fuer `c2` eine
// Ausnahme wirft, als gefangen gelten (Codex-Befund, Runde 4 — dritte Fundstelle
// derselben Klasse, deshalb jetzt fuer JEDE inhaltliche Pruefung).
pruefe(sauber.length > 0, '[Aufbau] harmloser Name wurde erzeugt');
pruefe(sauber === 'Erreicht BTC 95k?', 'harmloser Name unveraendert: ' + JSON.stringify(sauber));
// Das Und-Zeichen ist Absicht: nur damit ist diese Gegenprobe ueberhaupt
// empfindlich fuer UEBERMASKIERUNG. Mit 'Krypto' allein war sie es nicht — eine
// doppelte Maskierung blieb dort unsichtbar, und der Mutationstest hat das
// aufgedeckt, als jede Mutation ihre erwartete Pruefung benennen musste.
pruefe(sicher('renderCategoryTable (harmlos)', () => renderCategoryTable([{ category: 'Krypto & Co', markets: 3, forecasts: 9, brier: 0.2, baseline: 0.25 }])),
  '[Aufbau] harmlose Tabelle ohne Ausnahme gerendert');
const katSauber = hole('brier-categories')._html;
pruefe(katSauber.length > 100, '[Aufbau] ' + katSauber.length + ' Zeichen in der harmlosen Tabelle');
pruefe(katSauber.includes('<b>Krypto &amp; Co</b>'), 'harmlose Kategorie genau einmal maskiert');
pruefe(!katSauber.includes('&amp;amp;'), 'harmlose Kategorie nicht doppelt maskiert');

console.log('');
console.log(fehler === 0 ? 'ALLE PRUEFUNGEN BESTANDEN' : fehler + ' FEHLER');
// Endmarker. Der Mutationstest verlangt ihn, weil eine FEHL-Zeile allein nicht
// beweist, dass die Probe ihre Faelle durchlaufen hat: eine Mutation kann eine
// Ausnahme ausloesen, die in einem try/catch als FEHL gemeldet wird, und die
// Probe stirbt danach an der naechsten Stelle. Dann zaehlte sie als „gefangen",
// obwohl der beabsichtigte Fall nie geprueft wurde (Codex-Befund, Runde 2).
console.log('PROBE-ENDE ' + anzahlPruefungen + ' Pruefungen, ' + fehler + ' Fehler');
process.exit(fehler === 0 ? 0 : 1);

// Probe für scripts/verify_kurse.py — führt die ECHTE landing/js/kurse.js gegen einen PostgREST-Nachbau aus.
// Aufruf: node probe_kurse.js   → JSON {pruefungen:[{name, ok, detail}]} auf stdout
// Der Nachbau verhält sich wie PostgREST bei /rest/v1/prices: Filter ticker=eq., date=gte./gt. (UND-verknüpft),
// select=<Felder> (nur diese Schlüssel, Werte unverändert), order=date.asc, limit=<n>; fehlende Werte bleiben null.
'use strict';
const path = require('path');

global.window = { SA: { supabase: { url: 'https://stub', key: 'k' } } };
global.SA = global.window.SA;

// ── Daten ────────────────────────────────────────────────────────────────────────────────────────────────
function reihe(n, start) {
  const aus = [];
  let t = Date.UTC(start || 1900, 0, 1);
  for (let i = 0; i < n; i++) {
    const d = new Date(t).toISOString().slice(0, 10);
    aus.push({ date: d, open: i % 7 === 0 ? null : 100 + i, high: 101 + i, low: 99 + i, close: i % 11 === 0 ? 0 : 100 + i,
               log_return: i === 0 ? null : 0.001 * (i % 5), tdom: (i % 21) + 1, tdoy: (i % 252) + 1 });
    t += 86400000;
  }
  return aus;
}
const DATEN = {};
const VERTRAG = []; let VERTRAG_N = 0;
function setze(ticker, zeilen) { DATEN[ticker] = zeilen; }

// ── fetch-Nachbau ────────────────────────────────────────────────────────────────────────────────────────
const NETZ = { anfragen: [], gleichzeitig: 0, maxGleichzeitig: 0, regeln: [] };
// Regel: {ticker, nr (n-te Anfrage dieses Tickers, 1-basiert) | wenn(fn), antwort: 'status:500' | 'haengt' | fn}
function antworte(status, body, kopf) {
  return Promise.resolve({
    ok: status >= 200 && status < 300, status,
    headers: { get: (h) => (kopf || {})[h.toLowerCase()] ?? null },
    json: () => Promise.resolve(body)
  });
}
function parse(url) {
  const q = url.split('?')[1].split('&');
  const p = { gte: null, gt: null };
  for (const teil of q) {
    const [k, v] = teil.split('=');
    const w = decodeURIComponent(teil.slice(k.length + 1));
    if (k === 'ticker') p.ticker = w.replace(/^eq\./, '');
    else if (k === 'select') p.select = w.split(',');
    else if (k === 'limit') p.limit = +w;
    else if (k === 'order') p.order = w;
    else if (k === 'date' && w.startsWith('gte.')) p.gte = w.slice(4);
    else if (k === 'date' && w.startsWith('gt.')) p.gt = w.slice(3);
    void v;
  }
  return p;
}
global.fetch = function (url, init) {
  const p = parse(url);
  const nr = NETZ.anfragen.filter(a => a.ticker === p.ticker).length + 1;
  NETZ.anfragen.push({ ticker: p.ticker, url, nr });
  // Request-Vertrag (über den ganzen Lauf, nicht je Fall zurückgesetzt): Keyset aufsteigend, 1000er-Blöcke, nur
  // apikey + Authorization — kein Prefer (count=exact), kein Range (Codex S1 R1, Befund 3).
  const kopf = Object.keys((init && init.headers) || {}).sort().join(',');
  if (p.order !== 'date.asc' || p.limit !== 1000 || p.select[0] !== 'date' || kopf !== 'Authorization,apikey' ||
      /count|offset/.test(url)) VERTRAG.push(url + ' [' + kopf + ']');
  VERTRAG_N++;
  NETZ.gleichzeitig++;
  NETZ.maxGleichzeitig = Math.max(NETZ.maxGleichzeitig, NETZ.gleichzeitig);
  const fertig = (x) => { NETZ.gleichzeitig--; return x; };
  for (const r of NETZ.regeln) {
    if (r.ticker !== p.ticker) continue;
    if (r.nr !== undefined && r.nr !== nr) continue;
    if (r.wenn && !r.wenn(p, nr)) continue;
    if (typeof r.antwort === 'string' && r.antwort.startsWith('spaet:')) {
      // ignoriert den Abbruch und antwortet erst nach der Frist — der Transport bleibt so lange offen
      const ms = +r.antwort.slice(6);
      const z = (DATEN[p.ticker] || []).filter(x => (p.gte === null || x.date >= p.gte) && (p.gt === null || x.date > p.gt))
        .slice(0, p.limit).map(x => { const o = {}; for (const f of p.select) o[f] = x[f] ?? null; return o; });
      return new Promise(res => setTimeout(res, ms)).then(() => fertig(antworte(200, z)));
    }
    if (r.antwort === 'nie') return new Promise(function () {});
    if (r.antwort === 'jsonfehler') {
      return new Promise(res => setTimeout(res, 1)).then(() => fertig({ ok: true, status: 200, headers: { get: () => null },
        json: () => Promise.reject(new SyntaxError('Unexpected end of JSON input')) }));
    }
    if (r.antwort === 'haengt') {
      return new Promise((ok, nein) => {
        if (init && init.signal) init.signal.addEventListener('abort', () => { NETZ.gleichzeitig--; nein(new Error('abgebrochen')); });
      });
    }
    if (typeof r.antwort === 'function') return new Promise(res => setTimeout(res, NETZ.verzoegerung || 1)).then(() => fertig(r.antwort(p, nr)));
    const [s, ra] = String(r.antwort).replace('status:', '').split('|');
    return new Promise(res => setTimeout(res, NETZ.verzoegerung || 1)).then(() => fertig(antworte(+s, { message: 'Fehler' }, ra ? { 'retry-after': ra } : {})));
  }
  const alle = DATEN[p.ticker] || [];
  const z = alle.filter(x => (p.gte === null || x.date >= p.gte) && (p.gt === null || x.date > p.gt))
    .slice(0, p.limit || 1000)
    .map(x => { const o = {}; for (const f of p.select) o[f] = (x[f] === undefined ? null : x[f]); return o; });
  return new Promise(res => setTimeout(res, NETZ.verzoegerung || 1)).then(() => fertig(antworte(200, z, { 'content-range': '0-' + (z.length - 1) + '/*' })));
};

require(path.join(__dirname, '..', '..', 'landing', 'js', 'kurse.js'));
const KU = global.window.SA.kurse;
const I = KU._intern;
I.K.TIMEOUT_MS = 60;
let JETZT = 1e12;
I.setzeUhr(() => JETZT);

function neu() {
  I.zuruecksetzen();
  NETZ.anfragen = []; NETZ.regeln = []; NETZ.gleichzeitig = 0; NETZ.maxGleichzeitig = 0; NETZ.verzoegerung = 1;
  JETZT = 1e12;
}
const P = [];
function pruefe(name, ok, detail) { P.push({ name, ok: !!ok, detail: detail === undefined ? '' : String(detail) }); }
// Eine Ausnahme, die KEIN KursFehler ist, ist ein Absturz des Produktivcodes — auch wenn ein Fall sie abfängt, gilt
// sie nie als Nachweis (fünfte Beweisregel, v66.4). Sie wird gesammelt und vom Wächter als [Ausnahme] gemeldet.
const AUSNAHMEN = [];
async function fehlerVon(p) {
  try { await p; return null; } catch (e) {
    if (!e || e.name !== 'KursFehler') AUSNAHMEN.push(String(e && e.stack || e).slice(0, 300));
    return e;
  }
}
function istKursFehler(e) { return !!e && e.name === 'KursFehler'; }
/** Ergebnis ODER Fehler — wie fehlerVon erfasst es jeden Nicht-KursFehler als [Ausnahme]. Nie `.catch(x => x)`. */
async function ergebnisOderFehler(p) {
  try { return await p; } catch (e) {
    if (!e || e.name !== 'KursFehler') AUSNAHMEN.push(String(e && e.stack || e).slice(0, 300));
    return e;
  }
}

let e, f, t0, dt, ab;
const ABSCHNITTE = [];
ABSCHNITTE.push(['1 Sollmengen und Anfragezahl', async function () {
  // 1 Sollmengen und Anfragezahl
  for (const n of [0, 999, 1000, 1001, 2000, 33739]) {
    neu(); setze('T', reihe(n));
    const e = await KU.laden('T', { felder: ['close'], ab: null });
    const soll = Math.floor(n / 1000) + 1;
    pruefe('Sollmenge ' + n, e.zeilen.length === n && NETZ.anfragen.length === soll,
           e.zeilen.length + ' Zeilen, ' + NETZ.anfragen.length + ' Anfragen (soll ' + soll + ')');
    const ordnung = e.zeilen.every((z, i) => i === 0 || e.zeilen[i - 1].date < z.date);
    pruefe('aufsteigend ' + n, ordnung);
  }
  // kein count=exact, Keyset
  neu(); setze('T', reihe(2500));
  await KU.laden('T', { felder: ['close'], ab: null });
  pruefe('Keyset ohne Zählung', NETZ.anfragen[1].url.includes('date=gt.') && !NETZ.anfragen.some(a => /count/.test(a.url)),
         NETZ.anfragen.map(a => a.url).join(' | '));

}]);
ABSCHNITTE.push(['2 Projektion exakt, null und 0 bleiben, Grenze inklusive', async function () {
  // 2 Projektion exakt, null und 0 bleiben, Grenze inklusive
  neu(); setze('T', reihe(50));
  ab = DATEN.T[10].date;
  e = await KU.laden('T', { felder: ['open', 'close', 'log_return'], ab });
  pruefe('Grenze inklusive', e.zeilen[0].date === ab && e.zeilen.length === 40, e.zeilen[0].date + ' / ' + e.zeilen.length);
  pruefe('Projektion exakt', e.zeilen.every(z => Object.keys(z).sort().join() === 'close,date,log_return,open'),
         Object.keys(e.zeilen[0]).join());
  const z14 = e.zeilen.find(z => z.date === DATEN.T[14].date), z11 = e.zeilen.find(z => z.date === DATEN.T[11].date);
  pruefe('null bleibt null', z14.open === null, z14.open);
  pruefe('0 bleibt 0', z11.close === 0, z11.close);
  pruefe('Werte unverändert', e.zeilen.every(z => { const o = DATEN.T.find(x => x.date === z.date); return o.close === z.close && o.log_return === z.log_return; }));

  //   Kopie: Veränderung des Ergebnisses ändert den Bestand nicht
  e.zeilen[0].close = -1; e.zeilen.pop();
  const e2 = await KU.laden('T', { felder: ['open', 'close', 'log_return'], ab });
  pruefe('Ergebnis ist Kopie', e2.zeilen[0].close === DATEN.T[10].close && e2.zeilen.length === 40);
  pruefe('Bestand bedient ohne Netz', NETZ.anfragen.length === 1, NETZ.anfragen.length);

}]);
ABSCHNITTE.push(['4 Teilfehler: zweiter Block scheitert dauerhaft → Ablehnung, nichts ge', async function () {
  // 4 Teilfehler: zweiter Block scheitert dauerhaft → Ablehnung, nichts gecacht
  neu(); setze('T', reihe(2500));
  NETZ.regeln.push({ ticker: 'T', wenn: (p) => p.gt !== null, antwort: 'status:500|0' });
  f = await fehlerVon(KU.laden('T', { felder: ['close'], ab: null }));
  pruefe('Teilfehler lehnt ab', istKursFehler(f), f && f.message);
  pruefe('Teilfehler: kein Bestand', !I.koordinatoren().T.bestand);
  NETZ.regeln = [];
  e = await KU.laden('T', { felder: ['close'], ab: null });
  pruefe('nach Teilfehler neu geladen', e.zeilen.length === 2500);

}]);
ABSCHNITTE.push(['5 Fehler bei abgelaufenem Bestand: alter Bestand bleibt, Frische wird ', async function () {
  // 5 Fehler bei abgelaufenem Bestand: alter Bestand bleibt, Frische wird nicht verlängert
  neu(); setze('T', reihe(1500));
  const g1 = await KU.laden('T', { felder: ['close'], ab: null });
  JETZT += I.K.TTL_MS + 1;
  NETZ.regeln.push({ ticker: 'T', antwort: 'status:503|0' });
  f = await fehlerVon(KU.laden('T', { felder: ['close'], ab: null }));
  const best = I.koordinatoren().T.bestand;
  pruefe('abgelaufen + Fehler lehnt ab', istKursFehler(f));
  pruefe('alter Bestand bleibt ohne Frischeverlängerung', best && best.generation === g1.generation && best.geladenUm === g1.geladenUm);
  NETZ.regeln = [];
  const g2 = await KU.laden('T', { felder: ['close'], ab: null });
  pruefe('danach neu geladen, neue Generation', g2.generation > g1.generation, g1.generation + ' → ' + g2.generation);

}]);
ABSCHNITTE.push(['6 TTL: frischer Bestand ohne Netz, abgelaufener lädt neu', async function () {
  // 6 TTL: frischer Bestand ohne Netz, abgelaufener lädt neu
  neu(); setze('T', reihe(10));
  await KU.laden('T', { felder: ['close'], ab: null });
  JETZT += I.K.TTL_MS - 1;
  await KU.laden('T', { felder: ['close'], ab: null });
  const vorTTL = NETZ.anfragen.length;
  JETZT += 2;
  await KU.laden('T', { felder: ['close'], ab: null });
  pruefe('TTL: frisch aus Bestand, abgelaufen neu', vorTTL === 1 && NETZ.anfragen.length === 2, vorTTL + ' / ' + NETZ.anfragen.length);

}]);
ABSCHNITTE.push(['7 429 mit Retry-After, Netzfehler, Zeitüberschreitung', async function () {
  // 7 429 mit Retry-After, Netzfehler, Zeitüberschreitung
  neu(); setze('T', reihe(10));
  NETZ.regeln.push({ ticker: 'T', nr: 1, antwort: 'status:429|0' });
  e = await KU.laden('T', { felder: ['close'], ab: null });
  pruefe('429 + Retry-After wiederholt', e.zeilen.length === 10 && NETZ.anfragen.length === 2);
  neu(); setze('T', reihe(10));
  NETZ.regeln.push({ ticker: 'T', nr: 1, antwort: 'haengt' });
  e = await KU.laden('T', { felder: ['close'], ab: null });
  pruefe('Zeitüberschreitung wiederholt', e.zeilen.length === 10 && NETZ.anfragen.length === 2, NETZ.anfragen.length);
  neu(); setze('T', reihe(10));
  NETZ.regeln.push({ ticker: 'T', antwort: 'status:404' });
  f = await fehlerVon(KU.laden('T', { felder: ['close'], ab: null }));
  pruefe('404 ohne Wiederholung abgelehnt', istKursFehler(f) && NETZ.anfragen.length === 1, NETZ.anfragen.length);
  neu(); setze('T', reihe(10));
  NETZ.regeln.push({ ticker: 'T', antwort: 'status:500|0' });
  f = await fehlerVon(KU.laden('T', { felder: ['close'], ab: null }));
  pruefe('500 nach Wiederholungen abgelehnt', istKursFehler(f) && NETZ.anfragen.length === I.K.MAX_WIEDERHOLUNGEN + 1, NETZ.anfragen.length);

}]);
ABSCHNITTE.push(['8 Blockprüfung: Cursor ohne Fortschritt, nicht aufsteigend, ungültiges', async function () {
  // 8 Blockprüfung: Cursor ohne Fortschritt, nicht aufsteigend, ungültiges Datum, fehlendes Feld, kein Array
  const kaputt = {
    // zweiter Block beginnt MIT dem Cursor-Datum (Überlappung), ist in sich aufsteigend und kürzer als 1000 —
    // nur die Cursor-Prüfung fängt das, nicht die Blockgrenze und nicht die Ordnung im Block
    'Cursor ohne Fortschritt': (p, nr) => antworte(200, (nr === 1 ? reihe(1000) : reihe(1001).slice(999))
      .map(z => ({ date: z.date, close: z.close }))),
    'nicht aufsteigend': () => antworte(200, [{ date: '2000-01-02', close: 1 }, { date: '2000-01-01', close: 1 }]),
    'Duplikat': () => antworte(200, [{ date: '2000-01-01', close: 1 }, { date: '2000-01-01', close: 1 }]),
    'ungültiges Datum': () => antworte(200, [{ date: '2000-02-30', close: 1 }]),
    'Zeitstempel statt Datum': () => antworte(200, [{ date: '2000-01-01T00:00:00', close: 1 }]),
    'Feld fehlt': () => antworte(200, [{ date: '2000-01-01' }]),
    'kein Array': () => antworte(200, { message: 'x' }),
    'Zeile vor Grenze': () => antworte(200, [{ date: '1899-01-01', close: 1 }])
  };
  for (const [name, fn] of Object.entries(kaputt)) {
    neu();
    NETZ.regeln.push({ ticker: 'T', antwort: fn });
    f = await fehlerVon(KU.laden('T', { felder: ['close'], ab: name === 'Zeile vor Grenze' ? '1900-01-01' : null }));
    pruefe('Block abgelehnt: ' + name, istKursFehler(f) && !I.koordinatoren().T.bestand, f && f.message);
  }
  // Blockgrenze
  neu(); setze('T', reihe(3000));
  I.K.MAX_BLOECKE = 2;
  f = await fehlerVon(KU.laden('T', { felder: ['close'], ab: null }));
  I.K.MAX_BLOECKE = 61;
  pruefe('zu viele Blöcke abgelehnt', istKursFehler(f), f && f.message);

}]);
ABSCHNITTE.push(['9 geteilte Ladung: zwei gleiche Anfragen gleichzeitig = ein Netzaufruf', async function () {
  // 9 geteilte Ladung: zwei gleiche Anfragen gleichzeitig = ein Netzaufruf
  neu(); setze('T', reihe(500));
  const [a1, a2] = await Promise.all([KU.laden('T', { felder: ['close'], ab: null }), KU.laden('T', { felder: ['close'], ab: '1900-06-01' })]);
  pruefe('geteilte Ladung', NETZ.anfragen.length === 1 && a1.zeilen.length === 500 && a2.zeilen[0].date === '1900-06-01');
  pruefe('gleiche Generation bei geteilter Ladung', a1.generation === a2.generation);

}]);
ABSCHNITTE.push(['10 größerer Bedarf während laufender Ladung → wartet, Vereinigung lädt', async function () {
  // 10 größerer Bedarf während laufender Ladung → wartet, Vereinigung lädt danach; Abschlussreihenfolge
  neu(); setze('T', reihe(1500)); NETZ.verzoegerung = 20;
  const pA = KU.laden('T', { felder: ['close'], ab: '1902-01-01' });
  await new Promise(r => setTimeout(r, 5));
  const pB = KU.laden('T', { felder: ['open'], ab: null });
  const pC = KU.laden('T', { felder: ['close'], ab: '1901-01-01' });   // wartet ebenfalls
  const [rA, rB, rC] = await Promise.all([pA, pB, pC]);
  const urls = NETZ.anfragen.map(x => x.url);
  pruefe('wartende Vereinigung', rA.zeilen.length === 1500 - 365 - 365 && rB.zeilen.length === 1500 && rC.zeilen[0].date === '1901-01-01',
         rA.zeilen.length + '/' + rB.zeilen.length + '/' + rC.zeilen.length);
  pruefe('Vereinigung lädt beide Felder ab null', urls.slice(1).every(u => u.includes('select=date,open,close') && !u.includes('gte')), urls.join(' | '));
  pruefe('wartende Ladung höchstens eine', NETZ.anfragen.length === 1 + 2, NETZ.anfragen.length);
  pruefe('Generation steigt', rB.generation > rA.generation && rC.generation === rB.generation);
  const nB = NETZ.anfragen.length;
  await KU.laden('T', { felder: ['close', 'open'], ab: '1903-01-01' });
  pruefe('danach aus vereinigtem Bestand', NETZ.anfragen.length === nB);

}]);
ABSCHNITTE.push(['10b zwei Grenzen vereinigt: die früheste gewinnt', async function () {
  // laufend ab 1903, wartend ab 1902, dann wächst die wartende auf 1901 — alle drei sehen ab ihrer Grenze
  setze('T', reihe(1500)); NETZ.verzoegerung = 20;
  const pA = KU.laden('T', { felder: ['close'], ab: '1903-01-01' });
  await new Promise(r => setTimeout(r, 5));
  const pB = ergebnisOderFehler(KU.laden('T', { felder: ['close', 'open'], ab: '1902-01-01' }));
  const pC = ergebnisOderFehler(KU.laden('T', { felder: ['close', 'open'], ab: '1901-01-01' }));
  const [rA, rB, rC] = await Promise.all([pA, pB, pC]);
  pruefe('wartende Vereinigung zweier Grenzen', rA.zeilen[0].date === '1903-01-01' && rB.zeilen && rB.zeilen[0].date === '1902-01-01' &&
         rC.zeilen && rC.zeilen[0].date === '1901-01-01', (rC && rC.message) || (rC.zeilen && rC.zeilen[0].date));
}]);
ABSCHNITTE.push(['10c Generation global monoton, auch über Ticker und nach Verdrängung', async function () {
  const gen = [];
  for (const t of ['G1', 'G2', 'G1x']) { setze(t, reihe(5)); gen.push((await KU.laden(t, { felder: ['close'], ab: null })).generation); }
  for (let i = 0; i < 13; i++) { setze('F' + i, reihe(3)); await KU.laden('F' + i, { felder: ['close'], ab: null }); }
  const g1neu = (await KU.laden('G1', { felder: ['close'], ab: null })).generation;
  pruefe('Generation über Ticker streng steigend', gen[0] < gen[1] && gen[1] < gen[2], gen.join(','));
  pruefe('Generation nach Verdrängung nicht wiederverwendet', NETZ.anfragen.filter(a => a.ticker === 'G1').length === 2 &&
         gen.indexOf(g1neu) < 0 && g1neu > gen[2], g1neu + ' gegen ' + gen.join(','));
}]);
ABSCHNITTE.push(['11Bestand schrumpft nicht: ganzer Bestand + neues Feld mit späterer G', async function () {
  // 11 Bestand schrumpft nicht: ganzer Bestand + neues Feld mit späterer Grenze → Ladung ab null
  neu(); setze('T', reihe(1200));
  await KU.laden('T', { felder: ['close'], ab: null });
  await KU.laden('T', { felder: ['tdom'], ab: '1902-01-01' });
  const letzte = NETZ.anfragen[NETZ.anfragen.length - 1].url;
  pruefe('Bestand schrumpft nicht', !NETZ.anfragen.slice(1).some(x => x.url.includes('gte')) && letzte.includes('close') && letzte.includes('tdom'),
         NETZ.anfragen.slice(1).map(x => x.url).join(' | '));
  const nachher = NETZ.anfragen.length;
  await KU.laden('T', { felder: ['close'], ab: null });
  pruefe('alte Anfrage weiter aus Bestand', NETZ.anfragen.length === nachher);

}]);
ABSCHNITTE.push(['12 laufende Ladung scheitert, wartende startet trotzdem und gelingt', async function () {
  // 12 laufende Ladung scheitert, wartende startet trotzdem und gelingt
  neu(); setze('T', reihe(800)); NETZ.verzoegerung = 15;
  NETZ.regeln.push({ ticker: 'T', wenn: (p) => !p.select.includes('open'), antwort: 'status:400' });
  const pF = fehlerVon(KU.laden('T', { felder: ['close'], ab: null }));
  await new Promise(r => setTimeout(r, 3));
  const pW = KU.laden('T', { felder: ['open'], ab: null });
  const fF = await pF, rW = await pW;
  pruefe('laufende scheitert, wartende gelingt', istKursFehler(fF) && rW.zeilen.length === 800);

}]);
ABSCHNITTE.push(['13 TTL läuft während laufender Ladung ab → Anfrage wartet auf die lauf', async function () {
  // 13 TTL läuft während laufender Ladung ab → Anfrage wartet auf die laufende
  neu(); setze('T', reihe(300)); NETZ.verzoegerung = 15;
  const pL = KU.laden('T', { felder: ['close'], ab: null });
  await new Promise(r => setTimeout(r, 3));
  JETZT += I.K.TTL_MS + 5;
  const pL2 = KU.laden('T', { felder: ['close'], ab: null });
  await Promise.all([pL, pL2]);
  pruefe('TTL während laufender Ladung: ein Netzaufruf', NETZ.anfragen.length === 1, NETZ.anfragen.length);

}]);
ABSCHNITTE.push(['14 Abdeckung = angeforderte Grenze, nicht frühestes Datum (CRWV ab 199', async function () {
  // 14 Abdeckung = angeforderte Grenze, nicht frühestes Datum (CRWV ab 1990 → vollständig)
  neu(); setze('CRWV', reihe(400, 2025));
  e = await KU.laden('CRWV', { felder: ['close'], ab: '1990-01-01' });
  await KU.laden('CRWV', { felder: ['close'], ab: '2000-01-01' });
  pruefe('kurze Reihe: Abdeckung ab angeforderter Grenze', e.abdeckungAb === '1990-01-01' && NETZ.anfragen.length === 1, e.abdeckungAb);
  neu(); setze('LEER', []);
  e = await KU.laden('LEER', { felder: ['close'], ab: '2020-01-01' });
  await KU.laden('LEER', { felder: ['close'], ab: '2021-01-01' });
  pruefe('leere Reihe gilt als vollständig', e.zeilen.length === 0 && NETZ.anfragen.length === 1);

}]);
ABSCHNITTE.push(['15 LRU: höchstens 12 ruhende Koordinatoren, laufende werden nicht verd', async function () {
  // 15 LRU: höchstens 12 ruhende Koordinatoren, laufende werden nicht verdrängt
  neu();
  for (let i = 0; i < 14; i++) { setze('L' + i, reihe(5)); await KU.laden('L' + i, { felder: ['close'], ab: null }); }
  const namen = Object.keys(I.koordinatoren());
  pruefe('LRU-Grenze', namen.length === 12 && !namen.includes('L0') && !namen.includes('L1') && namen.includes('L13'), namen.join());
  neu(); NETZ.verzoegerung = 30;
  const laeufe = [];
  for (let i = 0; i < 14; i++) { setze('M' + i, reihe(5)); laeufe.push(KU.laden('M' + i, { felder: ['close'], ab: null })); }
  await new Promise(r => setTimeout(r, 5));
  const waehrend = Object.keys(I.koordinatoren()).length;
  await Promise.all(laeufe);
  pruefe('laufende nicht verdrängt', waehrend === 14 && Object.keys(I.koordinatoren()).length === 12, waehrend);

}]);
ABSCHNITTE.push(['16 Pool: höchstens 4 gleichzeitige Netzanfragen', async function () {
  // 16 Pool: höchstens 4 gleichzeitige Netzanfragen
  neu(); NETZ.verzoegerung = 10;
  const viele = [];
  for (let i = 0; i < 9; i++) { setze('P' + i, reihe(2100)); viele.push(KU.laden('P' + i, { felder: ['close'], ab: null })); }
  await Promise.all(viele);
  pruefe('Pool höchstens 4', NETZ.maxGleichzeitig === I.K.POOL, NETZ.maxGleichzeitig);

}]);
ABSCHNITTE.push(['17 Eingaben', async function () {
  // 17 Eingaben
  neu();
  for (const [name, args] of [['unbekanntes Feld', ['T', { felder: ['volume'], ab: null }]],
                              ['ab kein Datum', ['T', { felder: ['close'], ab: '2020-13-01' }]],
                              ['ab Zeitstempel', ['T', { felder: ['close'], ab: '2020-01-01T00:00' }]],
                              ['felder leer', ['T', { felder: [], ab: null }]],
                              ['ticker leer', ['', { felder: ['close'], ab: null }]]]) {
    f = await fehlerVon(KU.laden.apply(null, args));
    pruefe('Eingabe abgelehnt: ' + name, istKursFehler(f) && NETZ.anfragen.length === 0, f && f.message);
  }
  neu(); setze('T', reihe(3));
  e = await KU.laden('T', { felder: ['close'] });
  pruefe('date immer enthalten, ab fehlt = null', e.zeilen.length === 3 && 'date' in e.zeilen[0] && e.abdeckungAb === null);

  // ── Codex S1 R1 Auflagen ─────────────────────────────────────────────────────────────────────────────────
}]);
ABSCHNITTE.push(['18 Retry-After in Sekunden und als HTTP-Datum: die Wartezeit muss die ', async function () {
  // 18 Retry-After in Sekunden und als HTTP-Datum: die Wartezeit muss die verlangte sein (Standard wäre 350–650 ms)
  neu(); setze('T', reihe(10));
  NETZ.regeln.push({ ticker: 'T', nr: 1, antwort: 'status:503|1' });
  t0 = Date.now();
  await KU.laden('T', { felder: ['close'], ab: null });
  dt = Date.now() - t0;
  pruefe('Retry-After Sekunden eingehalten', dt >= 950 && NETZ.anfragen.length === 2, dt + ' ms');
  neu(); setze('T', reihe(10));
  NETZ.regeln.push({ ticker: 'T', nr: 1, antwort: 'status:429|' + new Date(JETZT + 1000).toUTCString() });
  t0 = Date.now();
  await KU.laden('T', { felder: ['close'], ab: null });
  dt = Date.now() - t0;
  pruefe('Retry-After HTTP-Datum eingehalten', dt >= 950 && NETZ.anfragen.length === 2, dt + ' ms');

}]);
ABSCHNITTE.push(['19 Pool hält den Platz bis zum Ende des Transports: Server antwortet e', async function () {
  // 19 Pool hält den Platz bis zum Ende des Transports: Server antwortet erst nach der Frist und ignoriert den Abbruch
  neu();
  const spaet = [];
  for (let i = 0; i < 8; i++) {
    setze('S' + i, reihe(20));
    NETZ.regeln.push({ ticker: 'S' + i, nr: 1, antwort: 'spaet:150' });
    spaet.push(KU.laden('S' + i, { felder: ['close'], ab: null }));
  }
  await new Promise(r => setTimeout(r, 250));
  const frueh = Object.keys(I.koordinatoren()).filter(t => I.koordinatoren()[t].bestand);
  pruefe('verspätete Antwort veröffentlicht nichts', frueh.length === 0, frueh.join(','));
  const rs = await Promise.all(spaet);
  pruefe('verspätete Antworten: Pool höchstens 4 offene Anfragen', NETZ.maxGleichzeitig <= I.K.POOL, NETZ.maxGleichzeitig);
  pruefe('verspätete Antworten: Ergebnisse vollständig', rs.every(r => r.zeilen.length === 20));
  await new Promise(r => setTimeout(r, 200));
  pruefe('verspätete Antworten: Pool wieder leer', I.aktiv() === 0, I.aktiv());

}]);
ABSCHNITTE.push(['19b Schlange: vier Transporte enden nie, die fünfte Anfrage scheitert an der Frist statt zu hängen', async function () {
  I.K.MAX_WIEDERHOLUNGEN = 0;
  for (const ohneAbbruch of [false, true]) {
    neu(); I.K.MAX_WIEDERHOLUNGEN = 0;
    const AC = global.AbortController;
    if (ohneAbbruch) global.AbortController = undefined;
    for (let i = 0; i < 4; i++) { setze('H' + i, reihe(5)); NETZ.regeln.push({ ticker: 'H' + i, antwort: 'nie' }); }
    setze('Q', reihe(5));
    const vier = [0, 1, 2, 3].map(i => fehlerVon(KU.laden('H' + i, { felder: ['close'], ab: null })));
    const t0 = Date.now();
    const fuenf = await fehlerVon(KU.laden('Q', { felder: ['close'], ab: null }));
    const dt = Date.now() - t0;
    await Promise.all(vier);
    global.AbortController = AC;
    const v = ohneAbbruch ? 'ohne AbortController' : 'Abbruch ignoriert';
    pruefe('Schlange mit Frist (' + v + ')', istKursFehler(fuenf) && /Zeitüberschreitung/.test(fuenf.message) && dt < 1000,
           (fuenf && fuenf.message) + ' nach ' + dt + ' ms');
    pruefe('abgelaufene Wartende belegen keinen Platz (' + v + ')', I.aktiv() === 4 && NETZ.anfragen.filter(a => a.ticker === 'Q').length === 0,
           'aktiv ' + I.aktiv() + ', Q-Anfragen ' + NETZ.anfragen.filter(a => a.ticker === 'Q').length);
  }
}]);
ABSCHNITTE.push(['19c abgelaufene Wartende nehmen keinen Platz, wenn die Transporte später doch enden', async function () {
  I.K.MAX_WIEDERHOLUNGEN = 0;
  for (let i = 0; i < 4; i++) { setze('H' + i, reihe(5)); NETZ.regeln.push({ ticker: 'H' + i, antwort: 'spaet:300' }); }
  setze('Q', reihe(5));
  const vier = [0, 1, 2, 3].map(i => fehlerVon(KU.laden('H' + i, { felder: ['close'], ab: null })));
  const fuenf = await fehlerVon(KU.laden('Q', { felder: ['close'], ab: null }));
  await Promise.all(vier);
  await new Promise(r => setTimeout(r, 450));         // die vier Transporte sind jetzt zu Ende, Plätze frei
  pruefe('abgelaufene Wartende fragt später nicht an', istKursFehler(fuenf) && NETZ.anfragen.filter(a => a.ticker === 'Q').length === 0 &&
         I.aktiv() === 0, 'Q-Anfragen ' + NETZ.anfragen.filter(a => a.ticker === 'Q').length + ', aktiv ' + I.aktiv());
}]);
ABSCHNITTE.push(['20 JSON-Fehler: einmal → Wiederholung, dauerhaft → Ablehnung', async function () {
  // 20 JSON-Fehler: einmal → Wiederholung, dauerhaft → Ablehnung
  neu(); setze('T', reihe(10));
  NETZ.regeln.push({ ticker: 'T', nr: 1, antwort: 'jsonfehler' });
  e = await KU.laden('T', { felder: ['close'], ab: null });
  pruefe('JSON-Fehler einmal: wiederholt', e.zeilen.length === 10 && NETZ.anfragen.length === 2);
  neu(); setze('T', reihe(10));
  NETZ.regeln.push({ ticker: 'T', antwort: 'jsonfehler' });
  f = await fehlerVon(KU.laden('T', { felder: ['close'], ab: null }));
  pruefe('JSON-Fehler dauerhaft: abgelehnt', istKursFehler(f) && !I.koordinatoren().T.bestand, f && f.message);

}]);
ABSCHNITTE.push(['21 wartende Ladung scheitert: ihre Anfragen lehnen ab, der Bestand der', async function () {
  // 21 wartende Ladung scheitert: ihre Anfragen lehnen ab, der Bestand der laufenden bleibt
  neu(); setze('T', reihe(600)); NETZ.verzoegerung = 15;
  NETZ.regeln.push({ ticker: 'T', wenn: (p) => p.select.includes('open'), antwort: 'status:400' });
  const pOk = KU.laden('T', { felder: ['close'], ab: null });
  await new Promise(r => setTimeout(r, 3));
  const pWf = fehlerVon(KU.laden('T', { felder: ['open'], ab: null }));
  const rOk = await pOk, fW = await pWf;
  pruefe('wartende scheitert: ihre Anfrage lehnt ab', istKursFehler(fW), fW && fW.message);
  pruefe('wartende scheitert: Bestand der laufenden bleibt',
         rOk.zeilen.length === 600 && I.koordinatoren().T.bestand.generation === rOk.generation);
  e = await KU.laden('T', { felder: ['close'], ab: '1900-02-01' });
  pruefe('wartende scheitert: alte Anfrage weiter aus Bestand', e.generation === rOk.generation);

}]);
ABSCHNITTE.push(['22 Übergang: Anfrage genau beim Abschluss der laufenden Ladung (im Abs', async function () {
  // 22 Übergang: Anfrage genau beim Abschluss der laufenden Ladung (im Abschluss-Callback des Verbrauchers)
  neu(); setze('T', reihe(300)); NETZ.verzoegerung = 5;
  let uebergang = null;
  const pU = KU.laden('T', { felder: ['close'], ab: null }).then(function (r) {
    uebergang = KU.laden('T', { felder: ['close', 'tdom'], ab: null });
    return r;
  });
  await pU;
  const rU = await uebergang;
  pruefe('Übergangsanfrage bekommt eigenen Bedarf', rU.zeilen.length === 300 && 'tdom' in rU.zeilen[0] && NETZ.anfragen.length === 2,
         NETZ.anfragen.length);
  neu(); setze('T', reihe(300)); NETZ.verzoegerung = 5;
  let uebergang2 = null;
  await KU.laden('T', { felder: ['close'], ab: null }).then(function () {
    uebergang2 = KU.laden('T', { felder: ['close'], ab: null });
  });
  await uebergang2;
  pruefe('Übergangsanfrage mit gedecktem Bedarf ohne Netz', NETZ.anfragen.length === 1, NETZ.anfragen.length);

}]);
ABSCHNITTE.push(['23 TTL-Ablauf eines VORHANDENEN Bestands, weitere Anfrage während der ', async function () {
  // 23 TTL-Ablauf eines VORHANDENEN Bestands, weitere Anfrage während der Neuladung
  neu(); setze('T', reihe(400)); NETZ.verzoegerung = 15;
  const alt = await KU.laden('T', { felder: ['close'], ab: null });
  JETZT += I.K.TTL_MS + 1;
  const pN1 = KU.laden('T', { felder: ['close'], ab: null });
  await new Promise(r => setTimeout(r, 3));
  const pN2 = KU.laden('T', { felder: ['close'], ab: '1900-03-01' });
  const [n1, n2] = await Promise.all([pN1, pN2]);
  pruefe('abgelaufener Bestand: eine Neuladung für beide', NETZ.anfragen.length === 2 && n1.generation === n2.generation &&
         n1.generation > alt.generation, NETZ.anfragen.length);


}]);

// Genau EIN Abschnitt je Prozess (Codex S1 R2, Befund 4): ein Abschnitt, der hängt oder nach seinem Ende weiterläuft,
// kann so keinen späteren beeinflussen. Die Frist setzt der Wächter von außen (Prozess-Timeout). Bricht der Abschnitt
// ab, ist das ein benannter Fehlschlag — außer die Ausnahme stammt aus landing/js/kurse.js und ist kein KursFehler:
// dann ist es ein Absturz des Produktivcodes und kein Nachweis ([Ausnahme], fünfte Beweisregel).
let AUSGEGEBEN = false, LAUFEND = null;
function ausgeben(obj) {
  AUSGEGEBEN = true;
  process.stdout.write(JSON.stringify(obj), function () { process.exit(0); });
}
// Wartet ein Abschnitt auf ein Versprechen, das nie erfüllt wird, und läuft kein Timer mehr, beendet node den Prozess
// still mit Exit 0 — das ist ein Hänger und wird als solcher gemeldet, nicht als leere Ausgabe.
// Eine Ablehnung, die niemand behandelt, ist ein Fehler des Laders (im Browser eine Konsolenwarnung, in node ein
// Prozessabbruch). Ein KursFehler wird zum benannten Befund des Abschnitts, alles andere zum [Ausnahme]-Absturz.
process.on('unhandledRejection', function (e) {
  if (e && e.name === 'KursFehler') pruefe('unbehandelte Ablehnung: ' + LAUFEND, false, e.message);
  else AUSNAHMEN.push(String(e && e.stack || e).slice(0, 300));
});
process.on('beforeExit', function () {
  if (!AUSGEGEBEN) ausgeben({ abschnitt: LAUFEND, haengt: true, pruefungen: P, ausnahmen: AUSNAHMEN, ende: true });
});
(async function () {
  const arg = process.argv[2];
  if (arg === '--liste') return ausgeben({ abschnitte: ABSCHNITTE.map(a => a[0]) });
  const nr = Number(process.argv[3]);
  if (arg !== '--abschnitt' || !Number.isInteger(nr) || !ABSCHNITTE[nr]) {
    return ausgeben({ absturz: 'Aufruf: node probe_kurse.js --liste | --abschnitt <nr>' });
  }
  const [name, fn] = ABSCHNITTE[nr];
  LAUFEND = name;
  neu();
  try {
    await fn();
  } catch (err) {
    const st = String(err && err.stack || err);
    if (err && err.name !== 'KursFehler' && /[\\/]landing[\\/]js[\\/]kurse\.js/.test(st.split('\n').slice(0, 3).join(' '))) AUSNAHMEN.push(st.slice(0, 300));
    else pruefe('Abschnitt abgebrochen: ' + name, false, st.split('\n')[0]);
  }
  // Request-Vertrag je Abschnitt über ALLE seine Anfragen (Codex S1 R1, Befund 3)
  pruefe('Request-Vertrag: ' + name, VERTRAG.length === 0 && VERTRAG_N > 0,
         VERTRAG_N + ' Anfragen, ' + VERTRAG.slice(0, 2).join(' | '));
  // unhandledRejection feuert erst nach dem Mikrotask-Durchlauf — vor dem Abschluss zwei Makrotasks abwarten
  await new Promise(r => setTimeout(r, 20));
  await new Promise(r => setImmediate(r));
  ausgeben({ abschnitt: name, pruefungen: P, ausnahmen: AUSNAHMEN, ende: true });
})().catch(function (e) {
  ausgeben({ pruefungen: P, ausnahmen: AUSNAHMEN, absturz: String(e && e.stack || e) });
});

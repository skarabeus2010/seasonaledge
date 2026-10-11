// Probe für scripts/verify_release_sperre.py — Transportsperre (Plan v9): echte landing/js/methode.js, echte
// landing/js/kurse.js und der wörtliche SA.supabase-Abschnitt aus landing/js/app.js gegen einen fetch-Nachbau.
// Aufruf: node probe_release_transport.js <fall> [basisordner]  → JSON {fall, pruefungen:[{name, ok, detail}]}
// Jeder Fall läuft in einem EIGENEN Prozess (die Sperre ist nicht rücksetzbar). Zu jedem Sperrfall gibt es einen
// Gegenlauf ohne Sperre (positive Kontrolle): dort MUSS die Anfrage bzw. der Rückfall stattfinden.
'use strict';
const fs = require('fs');
const path = require('path');

const FALL = process.argv[2];
const OHNE_HUELLE = (FALL || '').split(':')[2] === 'ohne_huelle';
const BASIS = path.resolve(process.argv[3] || path.join(__dirname, '..', '..'));
const ERG = [];
const pruefe = (name, ok, detail) => ERG.push({ name, ok: !!ok, detail: detail === undefined ? '' : String(detail) });

// ── Netz-Nachbau (vor methode.js, damit die Hülle ihn umschließt wie im Browser) ─────────────────────────────
const NETZ = { anfragen: [], regeln: {} };
function reihe(n) {
  const aus = []; let t = Date.UTC(1990, 0, 1);
  for (let i = 0; i < n; i++) { aus.push({ date: new Date(t).toISOString().slice(0, 10), open: 1, close: 1, log_return: 0, tdom: 1, tdoy: 1 }); t += 86400000; }
  return aus;
}
const DATEN = { A: reihe(2500), B: reihe(300), C: reihe(10), D: reihe(10), E: reihe(10) };
function antwort(status, body) {
  return { ok: status >= 200 && status < 300, status, headers: { get: () => null }, json: () => Promise.resolve(body) };
}
global.window = global;
global.fetch = function (url, init) {
  // auch ein Request-Objekt annehmen (fetch(new Request(u, {signal})))
  const roh = typeof url === 'string' ? url : (url && url.url) || String(url);
  NETZ.anfragen.push(roh);
  const m = /ticker=eq\.([^&]+)/.exec(roh);
  const ticker = m ? decodeURIComponent(m[1]) : null;
  const nr = NETZ.anfragen.filter(u => u.indexOf('ticker=eq.' + ticker) >= 0).length;
  const regel = NETZ.regeln[ticker];
  const signal = (init && init.signal) || (url && typeof url === 'object' && url.signal) || null;
  if (regel) {
    const r = regel(nr, roh);
    if (r === 'haengt') {
      return new Promise((ok, nein) => { if (signal) signal.addEventListener('abort', () => nein(Object.assign(new Error('abgebrochen'), { name: 'AbortError' }))); });
    }
    if (typeof r === 'number') return new Promise(res => setTimeout(res, 2)).then(() => antwort(r, { message: 'x' }));
    if (r && r.zeilen) return new Promise(res => setTimeout(res, 2)).then(() => antwort(200, r.zeilen));
  }
  if (/\/rest\/v1\/prices\?/.test(roh)) {
    const sel = /select=([^&]+)/.exec(roh)[1].split(',');
    const gt = /date=gt\.([0-9-]+)/.exec(roh);
    const z = (DATEN[ticker] || []).filter(x => !gt || x.date > gt[1]).slice(0, 1000)
      .map(x => { const o = {}; sel.forEach(f => { o[f] = x[f] === undefined ? null : x[f]; }); return o; });
    return new Promise(res => setTimeout(res, 2)).then(() => antwort(200, z));
  }
  // supabase.get-Pfad (Tabelle `tabelle`): erste Seite = NETZ.tabelle (1000 Zeilen), danach leer
  const nTab = NETZ.anfragen.filter(u => /\/rest\/v1\/tabelle/.test(u)).length;
  const body = (nTab === 1 && NETZ.tabelle) ? NETZ.tabelle : [];
  return new Promise(res => setTimeout(res, 2)).then(() => antwort(200, body));
};

global.SA = { supabase: { url: 'https://stub', key: 'k' } };
const rohFetch = global.fetch;
require('./release_harness').bereite(global, BASIS);
// ohne Hülle: die zweite Linie (methode.js) abschalten, damit der Vertrag des Laders SELBST geprüft wird
if (OHNE_HUELLE) global.fetch = rohFetch;
require(path.join(BASIS, 'landing', 'js', 'kurse.js'));
// SA.supabase wörtlich aus app.js (Abschnitt zwischen `SA.supabase = {` und dem Ende des Objekts)
const app = fs.readFileSync(path.join(BASIS, 'landing', 'js', 'app.js'), 'utf8');
const a0 = app.indexOf('SA.supabase = {');
const a1 = app.indexOf('\n};', a0);
if (a0 < 0 || a1 < 0) throw new Error('[Aufbau] SA.supabase-Abschnitt nicht gefunden');
new Function('SA', 'window', 'fetch', app.slice(a0, a1 + 3))(global.SA, global, global.fetch);
global.SA.supabase.url = 'https://stub'; global.SA.supabase.key = 'k';
const KU = global.SA.kurse;
KU._intern.K.TIMEOUT_MS = 5000;

function sperrGetter(zeilen, beiIndex) {
  // löst die Sperre beim ersten Lesen von zeilen[beiIndex].date aus — NACH der Body-Übernahme, VOR der nächsten Aktion
  const z = zeilen.map(o => Object.assign({}, o));
  const ziel = z[beiIndex]; const wert = ziel.date; let aus = false;
  Object.defineProperty(ziel, 'date', { enumerable: true, configurable: true,
    get() { if (!aus) { aus = true; SA.__sperre('Probe'); } return wert; } });
  return z;
}
const istRelease = (e) => !!(e && (e.releaseFehler === true || e.name === 'ReleaseFehler'));
const warte = (ms) => new Promise(r => setTimeout(r, ms));
async function ergebnis(p) { try { return { wert: await p }; } catch (e) { return { fehler: e }; } }

const FAELLE = {
  // (a) Sperre zwischen Block 1 und 2: danach keine Anfrage mehr, Ablehnung mit ReleaseFehler
  async a_zwischen_bloecken(sperren) {
    if (sperren) NETZ.regeln.A = (nr) => nr === 1 ? { zeilen: sperrGetter(DATEN.A.slice(0, 1000), 999) } : null;
    const r = await ergebnis(KU.laden('A', { felder: ['close'] }));
    const n = NETZ.anfragen.length;
    if (!sperren) return pruefe('Kontrolle: ohne Sperre drei Blöcke', n === 3 && r.wert && r.wert.zeilen.length === 2500, n);
    pruefe('(a) keine Anfrage nach der Sperre zwischen den Blöcken', n === 1, n);
    pruefe('(a) Ablehnung ist ReleaseFehler', istRelease(r.fehler), r.fehler && r.fehler.message);
    pruefe('(a) kein Bestand veröffentlicht', !KU._intern.koordinatoren().A || !KU._intern.koordinatoren().A.bestand);
  },
  // (b) Sperre während Poolwartezeit: der fünfte Lader wartet auf einen Platz und fragt danach NICHT an
  async b_poolwarte(sperren) {
    ['B', 'C', 'D', 'E'].forEach(t => { NETZ.regeln[t] = () => 'haengt'; });
    const ps = ['B', 'C', 'D', 'E', 'A'].map(t => ergebnis(KU.laden(t, { felder: ['close'] })));
    await warte(20);
    const vorher = NETZ.anfragen.length;
    if (!sperren) {
      pruefe('Kontrolle: Pool voll, fünfter wartet', vorher === 4, vorher);
      ['B', 'C', 'D', 'E'].forEach(t => { NETZ.regeln[t] = null; });
      return;
    }
    SA.__sperre('Probe');
    const r = await Promise.all(ps);
    await warte(30);
    pruefe('(b) nach der Sperre keine weitere Anfrage (Pool-Wartender)', NETZ.anfragen.length === vorher, NETZ.anfragen.length + ' / ' + vorher);
    pruefe('(b) alle fünf lehnen mit ReleaseFehler ab', r.every(x => istRelease(x.fehler)), r.map(x => x.fehler && x.fehler.name).join(','));
  },
  // (c) Sperre während einer Wiederholungspause: keine Wiederholung
  async c_wiederholung(sperren) {
    NETZ.regeln.C = (nr) => nr === 1 ? 500 : null;
    const p = ergebnis(KU.laden('C', { felder: ['close'] }));
    await warte(60);                                   // erste Antwort 500 ist da, die Pause (≥350 ms) läuft
    if (sperren) SA.__sperre('Probe');
    const r = await p;
    const n = NETZ.anfragen.length;
    if (!sperren) return pruefe('Kontrolle: ohne Sperre wiederholt', n === 2 && r.wert, n);
    pruefe('(c) keine Wiederholung nach der Sperre', n === 1, n);
    pruefe('(c) Ablehnung ist ReleaseFehler', istRelease(r.fehler), r.fehler && r.fehler.message);
  },
  // (d) Sperre während einer Rückfall-Ladung: die gemeinsame Ladung scheitert (400), der Rückfall hängt → Sperre
  async d_rueckfall(sperren) {
    NETZ.regeln.D = (nr) => nr === 1 ? 400 : (sperren ? 'haengt' : null);
    const p = ergebnis(KU.laden('D', { felder: ['close'] }));
    await warte(40);
    const vorher = NETZ.anfragen.length;
    if (!sperren) { const r = await p; return pruefe('Kontrolle: ohne Sperre Rückfall-Ladung', vorher === 2 && r.wert && KU._intern.eigene() === 0, vorher); }
    pruefe('(d) Rückfall-Ladung lief (zweite Anfrage)', vorher === 2 && KU._intern.eigene() === 1, vorher);
    SA.__sperre('Probe');
    const r = await p;
    await warte(20);
    pruefe('(d) Rückfall abgebrochen, keine weitere Anfrage', NETZ.anfragen.length === 2, NETZ.anfragen.length);
    pruefe('(d) Ablehnung ist ReleaseFehler', istRelease(r.fehler), r.fehler && r.fehler.message);
  },
  // (d2) Sperre während der GEMEINSAMEN Ladung: sie scheitert mit ReleaseFehler — kein Rückfall darf starten
  async d2_kein_rueckfall(sperren) {
    // Kontrolle: dieselbe gemeinsame Ladung scheitert ohne Sperre (400) → der Rückfall MUSS starten
    NETZ.regeln.D = (nr) => nr === 1 ? (sperren ? 'haengt' : 400) : null;
    const vorher = KU._intern.eigeneGesamt();
    const p = ergebnis(KU.laden('D', { felder: ['close'] }));
    await warte(30);
    if (sperren) { SA.__sperre('Probe'); KU._abbrechenAlle(); }
    const r = await p;
    await warte(30);
    if (!sperren) return pruefe('Kontrolle: abgebrochene gemeinsame Ladung → Rückfall startet', KU._intern.eigeneGesamt() === vorher + 1, KU._intern.eigeneGesamt() - vorher);
    pruefe('(d2) kein Rückfall nach der Sperre', KU._intern.eigeneGesamt() === vorher, KU._intern.eigeneGesamt() - vorher);
    pruefe('(d2) Ablehnung ist ReleaseFehler', istRelease(r.fehler), r.fehler && r.fehler.message);
  },
  // (g) Abbruchsignal eines Request-Objekts erreicht den Transport (die Hülle darf es nicht ersetzen) — ohne Sperre
  async g_request_signal(sperren) {
    NETZ.regeln.G = () => 'haengt';
    const ac = new AbortController();
    const p = ergebnis(global.fetch(new Request('https://stub/rest/v1/prices?ticker=eq.G&select=date', { signal: ac.signal })));
    await warte(20);
    if (!sperren) {                                    // Kontrolle: ohne Abbruch hängt die Anfrage weiter
      const r = await Promise.race([p, warte(150).then(() => 'offen')]);
      return pruefe('Kontrolle: ohne Abbruch bleibt die Anfrage offen', r === 'offen');
    }
    ac.abort();
    const r = await Promise.race([p, warte(500).then(() => ({ offen: true }))]);
    pruefe('(g) Abbruch über das Request-Signal erreicht den Transport', !r.offen && r.fehler && r.fehler.name === 'AbortError',
           r.offen ? 'hängt' : (r.fehler && r.fehler.name));
  },
  // (e) Sperre nach dem letzten Block vor der Übernahme: kein Bestand, keine Sicht
  async e_vor_uebernahme(sperren) {
    if (sperren) NETZ.regeln.E = () => ({ zeilen: sperrGetter(DATEN.E, 9) });
    const r = await ergebnis(KU.laden('E', { felder: ['close'] }));
    const k = KU._intern.koordinatoren().E;
    if (!sperren) return pruefe('Kontrolle: ohne Sperre Bestand veröffentlicht', r.wert && k && k.bestand);
    pruefe('(e) kein Bestand veröffentlicht', !k || !k.bestand);
    pruefe('(e) Ablehnung ist ReleaseFehler', istRelease(r.fehler), r.fehler && r.fehler.message);
  },
  // (f) SA.supabase.get / getAll: keine Anfrage nach der Sperre, keine Übernahme nach Sperre im Body
  async f_supabase(sperren) {
    const seite = Array.from({ length: 1000 }, (_, i) => ({ i }));
    let gelesen = false;
    const rows = new Proxy(seite, { get(t, k) { if (sperren && k === 'length' && !gelesen) { gelesen = true; SA.__sperre('Probe'); } return t[k]; } });
    NETZ.tabelle = rows;
    // getAll: die zweite Seite darf nach der Sperre nicht angefragt werden
    let n0 = NETZ.anfragen.length;
    const r = await ergebnis(SA.supabase.getAll('tabelle', 'order=id.asc'));
    const n = NETZ.anfragen.length - n0;
    if (!sperren) return pruefe('Kontrolle: getAll ohne Sperre lädt zwei Seiten', n === 2 && r.wert && r.wert.length === 1000, n);
    pruefe('(f) getAll: keine Seite nach der Sperre', n <= 1, n);
    n0 = NETZ.anfragen.length;
    const r2 = await ergebnis(SA.supabase.get('tabelle', 'x=1'));
    pruefe('(f) get nach Sperre: keine Anfrage, ReleaseFehler', NETZ.anfragen.length === n0 && istRelease(r2.fehler), NETZ.anfragen.length - n0);
    const r3 = await ergebnis(KU.laden('B', { felder: ['close'] }));
    pruefe('(f) laden nach Sperre: keine Anfrage, ReleaseFehler', NETZ.anfragen.length === n0 && istRelease(r3.fehler));
  }
};

(async () => {
  const [name, modus] = FALL.split(':');
  if (!FAELLE[name]) throw new Error('[Aufbau] unbekannter Fall ' + FALL);
  await FAELLE[name](modus !== 'kontrolle');
  process.stdout.write(JSON.stringify({ fall: FALL, pruefungen: ERG }) + '\nPROBE-ENDE\n');
})().catch(e => { process.stdout.write('[Absturz] ' + (e && e.stack) + '\n'); process.exit(2); });

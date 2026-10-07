/* Führt das Inline-Skript von /wahlen (aus der SEITE gezogen, keine Kopie) mit dem echten
   landing/js/wahlen-compute.js gegen eine Studie aus — ohne Browser, mit DOM-/Chart-/fetch-Stubs.

   Aufruf: node probe_wahlen_seite.js <studie.json>      (WAHLEN_SEITE=<html> für Mutationen)
   Läufe: Deutsch (Grundfunktionen), Englisch (Zahlen/Datum/Parteinamen, Neuzeichnen nach
   'sa:i18n-bereit'), HTML im Namen (wird escaped), Snapshot gültig / ungültig / fehlend.
   Exit 1 bei Fehler. */
const fs = require('fs');
const path = require('path');

const REPO = path.resolve(__dirname, '..', '..');
const html = fs.readFileSync(process.env.WAHLEN_SEITE || path.join(REPO, 'landing/pages/wahlen.html'), 'utf8');
const STUDIE = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const EN_DICT = JSON.parse(fs.readFileSync(path.join(REPO, 'landing/i18n/en.json'), 'utf8'));
const seite = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]).find((s) => s.includes('SA.wahlen.auswerten'));
const fehler = [];
global.window = {};
require(path.join(REPO, 'landing/js/wahlen-compute.js'));
const KERN = global.window.SA.wahlen;

function neu(id) {
  const lauscher = {};
  const o = {
    id, value: '', style: {}, _html: '', _text: '',
    classList: { _s: new Set(), add(c) { this._s.add(c); }, remove(c) { this._s.delete(c); }, contains(c) { return this._s.has(c); } },
    addEventListener(t, f) { (lauscher[t] = lauscher[t] || []).push(f); },
    feuer(t, ev) { (lauscher[t] || []).forEach((f) => f(ev || { target: o })); },
    getAttribute() { return null; },
  };
  Object.defineProperty(o, 'innerHTML', { get() { return this._html; }, set(v) { this._html = String(v); } });
  Object.defineProperty(o, 'textContent', { get() { return this._text; }, set(v) { this._text = String(v); } });
  return o;
}

/** Ein Seitenlauf. cfg: {en, bereitSpaet, suche, dateien:{url: obj|null}, keinAbruf} */
function lauf(name, cfg) {
  return new Promise((ende) => {
    const el = {}, docLauscher = {};
    const werte = { 'sel-reihe': '^GSPC', 'sel-typ': 'midterm', 'rng-x': '20', 'rng-y': '20', 'sel-ab': '', 'sel-wechsel': 'alle' };
    for (const id of ['error-banner', 'live-box', 'live-titel', 'live-sub', 'chart', 'kpis', 'tbl', 'ausg', 'stand',
                      'val-x', 'val-y', 'btn-t0', 'btn-tx', 'btn-haupt', ...Object.keys(werte)]) {
      el[id] = neu(id);
      if (werte[id] !== undefined) el[id].value = werte[id];
    }
    const ctx = { el, opts: null, abrufe: [], fehler: [] };
    let bereit = !cfg.bereitSpaet;
    global.SA = { wahlen: KERN, i18n: {
      t: (k, d) => (cfg.en && bereit && EN_DICT[k] !== undefined ? EN_DICT[k] : d),
      isEN: () => !!cfg.en, bereit: () => bereit } };
    global.window = { SA: global.SA };
    global.location = { search: cfg.suche || '' };
    global.ApexCharts = class { constructor(n, o) { ctx.opts = o; } render() {} destroy() {} };
    global.document = {
      readyState: 'complete',
      getElementById: (id) => el[id] || (ctx.fehler.push('unbekannte id ' + id), neu(id)),
      addEventListener: (t, f) => { (docLauscher[t] = docLauscher[t] || []).push(f); },
    };
    ctx.feuerDoc = (t) => (docLauscher[t] || []).forEach((f) => f());
    ctx.setzeBereit = () => { bereit = true; };
    global.fetch = (url) => {
      ctx.abrufe.push(url);
      const d = Object.prototype.hasOwnProperty.call(cfg.dateien, url) ? cfg.dateien[url] : undefined;
      setTimeout(() => ende(ctx), 20);
      if (d === undefined || d === null) return Promise.resolve({ ok: false, status: 404, json: () => Promise.reject(new Error('404')) });
      return Promise.resolve({ ok: true, json: () => Promise.resolve(JSON.parse(JSON.stringify(d))) });
    };
    try { new Function(seite)(); } catch (e) { ctx.fehler.push('Seitenskript wirft: ' + e.message); setTimeout(() => ende(ctx), 0); }
    if (cfg.keinAbruf) setTimeout(() => ende(ctx), 20);
  }).then((ctx) => { ctx.fehler.forEach((f) => fehler.push(name + ': ' + f)); return ctx; });
}

function soll(name, b, text) { if (!b) fehler.push(name + ': ' + text); }
const LIVE = '/landing/data/wahlen_study.json';
const namen = (c) => ((c.opts && c.opts.series) || []).map((s) => s.name);

(async () => {
  if (!seite) { console.log('Seitenskript nicht gefunden'); process.exit(1); }

  // 1) Deutsch: Grundfunktionen
  let c = await lauf('DE', { dateien: { [LIVE]: STUDIE } });
  const el = c.el;
  soll('DE', el['error-banner'].style.display !== 'block', 'Fehlerbanner: ' + el['error-banner'].textContent);
  soll('DE', namen(c).length >= 4, 'Chart ohne Grundserien: ' + namen(c));
  soll('DE', c.opts && c.opts.series[1].data.find((p) => p.x === 0).y === 0, 'Mittel bei t0 nicht 0 %');
  soll('DE', /Wahlen im Fenster/.test(el.kpis.innerHTML) && /Pp\./.test(el.kpis.innerHTML), 'KPIs/Differenz in Pp. fehlen');
  soll('DE', (el.tbl.innerHTML.match(/<tr data-id=/g) || []).length > 20, 'Tabelle leer');
  soll('DE', /Datenstand/.test(el.stand.textContent) && /Hauptfenster 20\/20/.test(el.stand.textContent), 'Datenstand/Hauptfenster fehlt: ' + el.stand.textContent);
  soll('DE', / \*<\/td>/.test(el.tbl.innerHTML) && /vor 1971/.test(el.ausg.textContent), 'Kalender-Kennzeichnung vor 1971 fehlt');
  soll('DE', el['live-box'].style.display === 'block' && /t0/.test(el['live-sub'].textContent), 'Live-Box ohne t0');
  el['btn-tx'].feuer('click');
  soll('DE', namen(c).some((n) => /^Live/.test(n)), 'Live-Linie fehlt in „Start = 0 %“');
  soll('DE', c.opts.series[1].data[0].y === 0, 'Fensterbeginn nicht 0 %');
  const id = (el.tbl.innerHTML.match(/data-id="([^"]+)"/) || [])[1];
  el.tbl.feuer('click', { target: { closest: () => ({ getAttribute: () => id }) } });
  soll('DE', namen(c).some((n) => n.startsWith(id.slice(-4)) && /t0/.test(n)), 'Einzelwahl ohne Wahltermin/t0 im Namen');
  el['rng-x'].value = '33'; el['rng-x'].feuer('input');
  soll('DE', /Exploration/.test(el.stand.textContent), 'Exploration nicht gekennzeichnet');
  el['btn-haupt'].feuer('click');
  soll('DE', el['rng-x'].value === '20' && /Hauptfenster/.test(el.stand.textContent), 'Knopf Hauptfenster wirkungslos');
  el['sel-wechsel'].value = 'ja'; el['sel-wechsel'].feuer('change');
  soll('DE', /Datenstand/.test(el.stand.textContent), 'Datenstand verschwindet bei Ergebnisfilter');

  // 2) Englisch, Wörterbuch kommt nach den Daten
  c = await lauf('EN', { en: true, bereitSpaet: true, dateien: { [LIVE]: STUDIE } });
  soll('EN', c.el.tbl.innerHTML === '', 'rendert vor dem Wörterbuch (wäre deutsch)');
  c.setzeBereit(); c.feuerDoc('sa:i18n-bereit');
  soll('EN', /Republicans|Democrats/.test(c.el.tbl.innerHTML) && !/Republikaner|Demokraten/.test(c.el.tbl.innerHTML), 'Parteinamen nicht englisch');
  soll('EN', /\+\d+\.\d\d %/.test(c.el.tbl.innerHTML) && !/\d,\d\d %/.test(c.el.tbl.innerHTML), 'Zahlenformat nicht englisch');
  soll('EN', /\d{4}-\d\d-\d\d/.test(c.el.tbl.innerHTML), 'Datum nicht ISO');

  // 3) HTML im Namen wird escaped
  const boese = JSON.parse(JSON.stringify(STUDIE));
  boese.wahlen.forEach((w) => { if (w.type === 'president' && w.winner) w.winner = '<img src=x onerror=alert(1)>'; });
  c = await lauf('XSS', { dateien: { [LIVE]: boese } });
  c.el['sel-typ'].value = 'president'; c.el['sel-typ'].feuer('change');
  soll('XSS', !/<img/.test(c.el.tbl.innerHTML) && /&lt;img/.test(c.el.tbl.innerHTML), 'Name nicht escaped');
  const xid = (c.el.tbl.innerHTML.match(/data-id="([^"]+)"/) || [])[1];
  c.el.tbl.feuer('click', { target: { closest: () => ({ getAttribute: () => xid }) } });
  soll('XSS', namen(c).every((n) => !/<img/.test(n)), 'Serienname der Einzelwahl nicht escaped (Legende nutzt innerHTML)');

  // 3b) Verspätetes Ergebnis 2000 wird mit Datum genannt
  const w2000 = STUDIE.wahlen.find((w) => w.id === 'us-president-2000');
  soll('2000', w2000 && w2000.result_decided === '2000-12-12', 'Studie ohne result_decided für 2000 (neu bauen)');
  c = await lauf('2000', { dateien: { [LIVE]: STUDIE } });
  c.el['sel-typ'].value = 'president'; c.el['sel-typ'].feuer('change');
  soll('2000', /Ergebnis erst am 12\.12\.2000/.test(c.el.tbl.innerHTML), 'Hinweis auf spätes Ergebnis 2000 fehlt');

  // 4) Snapshot: gültig lädt NUR das Paket und übernimmt die Ansicht
  const snap = Object.assign(JSON.parse(JSON.stringify(STUDIE)), { snapshot_id: 'midterm-2026-test',
    ansicht: { reihe: '^DJI', typ: 'president', x: 10, y: 15, basis: 't0' } });
  const SNAP_URL = '/landing/data/wahlen_snapshots/midterm-2026-test.json';
  c = await lauf('Snapshot', { suche: '?snapshot=midterm-2026-test', dateien: { [SNAP_URL]: snap, [LIVE]: STUDIE } });
  soll('Snapshot', c.abrufe.length === 1 && c.abrufe[0] === SNAP_URL, 'lädt nicht ausschliesslich das Paket: ' + c.abrufe);
  soll('Snapshot', c.el['sel-reihe'].value === '^DJI' && c.el['rng-y'].value === '15', 'Ansicht nicht übernommen');
  soll('Snapshot', /midterm-2026-test/.test(c.el.stand.textContent), 'Snapshot nicht gekennzeichnet');
  c = await lauf('Snapshot fehlt', { suche: '?snapshot=gibt-es-nicht', dateien: { [LIVE]: STUDIE } });
  soll('Snapshot fehlt', c.el['error-banner'].style.display === 'block' && c.abrufe.every((u) => u !== LIVE), 'fällt auf aktuelle Datei zurück');
  for (const suche of ['?snapshot=..%2Fgeheim', '?snapshot', '?snapshot=', '?snapshot=%', '?a=1&snapshot&b=2']) {
    c = await lauf('Snapshot ungültig ' + suche, { suche, dateien: { [LIVE]: STUDIE }, keinAbruf: true });
    soll('Snapshot ungültig ' + suche, c.abrufe.length === 0 && c.el['error-banner'].style.display === 'block', 'nicht abgewiesen: ' + c.abrufe);
  }
  // Fehler vor dem Wörterbuch wird nachträglich übersetzt (Codex 1b-2 R2)
  c = await lauf('Fehler EN', { en: true, bereitSpaet: true, suche: '?snapshot=gibt-es-nicht', dateien: {} });
  c.setzeBereit(); c.feuerDoc('sa:i18n-bereit');
  soll('Fehler EN', /does not exist/.test(c.el['error-banner'].textContent), 'Fehlermeldung bleibt deutsch: ' + c.el['error-banner'].textContent);

  for (const f of fehler) console.log('  FEHLER ' + f);
  console.log(`probe_wahlen_seite: ${fehler.length} Fehler`);
  process.exit(fehler.length ? 1 : 0);
})();
setTimeout(() => { console.log('Zeitüberschreitung. ' + fehler.join(' | ')); process.exit(1); }, 30000);

/**
 * probe_plain_vanilla_messlauf.js — Messlauf der Seite /plain-vanilla: führt die ECHTEN Module der Seite in der
 * Reihenfolge aus, in der die Seite sie lädt, und schreibt Trades + Kennzahlen aller Strategien als JSON.
 *
 *   node scripts/js/probe_plain_vanilla_messlauf.js <kurs-snapshot-ordner> <ausgabe.json> [zeitraeume=10,max] [stops=aus,fixed8,trailing8]
 *
 * - Die Script-Liste wird aus landing/pages/plain-vanilla.html gelesen (lokale <script src>), nicht von Hand gepflegt:
 *   ein erster Lauf ohne indicators.js ließ LBR still auf Sell in May zurückfallen und lieferte identische Zahlen.
 *   Module, die einen Browser brauchen (auth/i18n/app/charts/tour), werden übersprungen und in der Ausgabe genannt.
 * - Nachbildung der Seitenlogik: Zeitraum in Jahren ab Stichtag des Snapshots (nicht ab heute — sonst ändert ein
 *   späterer Lauf die Ergebnisse ohne Codeänderung), optional Stop-Loss wie calcStrategy().
 * - Ausgabe enthält Hash des Kurs-Snapshots, Stichtag und Hash der geladenen Module.
 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const [kursOrdner, ausgabe, zArg, sArg, basisArg] = process.argv.slice(2);
// optional: Basisordner mit landing/… (z. B. alter Stand per git archive) — sonst das Repo
const REPO = path.resolve(basisArg || path.join(__dirname, '..', '..'));

const BROWSER_ONLY = new Set(['auth.js', 'i18n.js', 'app.js', 'charts.js', 'tour-config.js', 'tour.js']);
const html = fs.readFileSync(path.join(REPO, 'landing/pages/plain-vanilla.html'), 'utf8');
const srcs = [...html.matchAll(/<script src="\/landing\/js\/([^"?]+)/g)].map(m => m[1]);
const geladen = [], uebersprungen = [];
const window = {};
const modulHash = crypto.createHash('sha256');
for (const f of srcs) {
  if (BROWSER_ONLY.has(f)) { uebersprungen.push(f); continue; }
  const code = fs.readFileSync(path.join(REPO, 'landing/js', f), 'utf8');
  modulHash.update(f + '\0' + code);
  new Function('window', 'var SA = window.SA || {};\n' + code + '\nwindow.SA = SA;')(window);
  geladen.push(f);
}
const SA = window.SA;
for (const pflicht of ['strategy-compute.js', 'indicators.js', 'holidays.js']) {
  if (!geladen.includes(pflicht)) throw new Error('[Aufbau] Seite lädt ' + pflicht + ' nicht mehr oder Liste nicht lesbar');
}
if (!SA.strategy || !SA.STRATEGIES || !SA.indicators || !SA.indicators.calcMACD) throw new Error('[Aufbau] Module unvollständig');

const meta = JSON.parse(fs.readFileSync(path.join(kursOrdner, 'snapshot.json'), 'utf8'));
// Hash neu rechnen (dasselbe Verfahren wie plain_vanilla_kurse.snapshot_hash) — veränderter Snapshot = Abbruch
{
  const h = crypto.createHash('sha256');
  for (const f of fs.readdirSync(kursOrdner).filter(f => f.endsWith('.json') && f !== 'snapshot.json').sort()) {
    h.update(Buffer.concat([Buffer.from(f), Buffer.from([0]), fs.readFileSync(path.join(kursOrdner, f))]));
  }
  const ist = h.digest('hex').slice(0, 16);
  if (ist !== meta.hash) throw new Error('[Aufbau] Kurs-Snapshot verändert: ' + ist + ' ≠ ' + meta.hash);
}
const stichtag = meta.stichtag;
const zeitraeume = (zArg || '10,max').split(',');
const stops = (sArg || 'aus').split(',');

// Wie getFilteredRows() der Seite: ab 1. Januar des Jahres (Stichtagsjahr − Zeitraum)
function filtern(rows, z) {
  if (z === 'max') return rows;
  const grenze = (parseInt(stichtag.slice(0, 4), 10) - parseInt(z, 10)) + '-01-01';
  return rows.filter(r => r.date >= grenze);
}

function mitStop(rows, trades, s) {
  if (s === 'aus') return trades;
  const m = /^(fixed|trailing)(\d+(?:\.\d+)?)$/.exec(s);
  if (!m) throw new Error('[Aufbau] unbekannter Stop ' + s);
  return m[1] === 'trailing' ? SA.strategy.applyTrailingStop(rows, trades, +m[2]) : SA.strategy.applyStopLoss(rows, trades, +m[2]);
}

const ergebnis = { stichtag, kurs_hash: meta.hash, modul_hash: modulHash.digest('hex').slice(0, 16),
                   module: geladen, uebersprungen, zeitraeume, stops, ticker: {} };
for (const datei of fs.readdirSync(kursOrdner).filter(f => f.endsWith('.json') && f !== 'snapshot.json').sort()) {
  const ticker = datei.replace(/\.json$/, '').replace(/^_/, '^');
  const rows = JSON.parse(fs.readFileSync(path.join(kursOrdner, datei), 'utf8')).filter(r => r.date <= stichtag);
  rows.forEach(r => { r.close = parseFloat(r.close); if (r.log_return != null) r.log_return = parseFloat(r.log_return); });
  const out = ergebnis.ticker[ticker] = { zeilen: rows.length, letzte: rows.length ? rows[rows.length - 1].date : null, je: {} };
  for (const z of zeitraeume) {
    const sub = filtern(rows, z);
    for (const s of stops) {
      const je = {};
      for (const [key, st] of Object.entries(SA.STRATEGIES)) {
        SA.strategy._dateIdx = null;
        let trades = [], stats = null, fehler = null, protokoll = [], unvollstaendig = [], veraltet = null;
        const boerse = SA.holidays.detect(ticker);
        try {
          if (SA.strategy.auswerten) {
            // derselbe Pfad wie die Seite (Codex Code-R1 Befund 10): Strategie → Stop → Datenende → Kennzahlen
            const m = /^(fixed|trailing)(\d+(?:\.\d+)?)$/.exec(s);
            const r = SA.strategy.auswerten(sub, key, { stichtag, boerse, stop: m ? { typ: m[1], pct: +m[2] } : null });
            trades = r.trades; stats = r.stats; protokoll = r.protokoll || [];
            unvollstaendig = r.unvollstaendig || []; veraltet = r.veraltet;
          } else {
            // alter Stand ohne auswerten(): Strategie + Stop + Statistik direkt
            trades = mitStop(sub, SA.strategy[st.func](sub) || [], s);
            stats = SA.strategy.computeStats(trades);
          }
        } catch (e) { fehler = String(e && e.message || e); }
        const tupel = t => [t.entry_date, t.exit_date, t.entry_price, t.exit_price, t.return_pct, t.open ? 1 : 0,
                            t.stopped ? 1 : 0, t.leverage || 1, t.zustand_ausstieg || '', t.zustand_einstieg || '',
                            t.regeltermin_ausstieg || ''];
        je[key] = { n: trades.length, offen: trades.filter(t => t.open).length, stats, fehler, veraltet,
                    trades: trades.map(tupel), unvollstaendig: unvollstaendig.map(tupel),
                    protokoll: protokoll.map(p => [p.grund, p.datum]),
                    protokoll_zaehler: protokoll.reduce((a, p) => (a[p.grund] = (a[p.grund] || 0) + 1, a), {}) };
      }
      out.je[z + '|' + s] = je;
    }
  }
}
ergebnis.fehler = [];
for (const [tk, o] of Object.entries(ergebnis.ticker)) for (const [k, je] of Object.entries(o.je))
  for (const [st, v] of Object.entries(je)) if (v.fehler) ergebnis.fehler.push([tk, k, st, v.fehler]);
ergebnis.gueltig = ergebnis.fehler.length === 0;
fs.writeFileSync(ausgabe, JSON.stringify(ergebnis));
if (!ergebnis.gueltig) { console.error('UNGÜLTIG: Strategiefehler', ergebnis.fehler.slice(0, 5)); process.exitCode = 1; }
console.log('Module:', geladen.join(' '), '| übersprungen:', uebersprungen.join(' '));
console.log('Messlauf fertig, Stichtag', stichtag, 'Kurs-Hash', meta.hash, '→', ausgabe);
console.log('ENDE');

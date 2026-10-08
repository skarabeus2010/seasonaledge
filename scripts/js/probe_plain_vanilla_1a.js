/**
 * probe_plain_vanilla_1a.js — fachliche Prüffälle Phase 1A /plain-vanilla gegen die ECHTEN Module.
 *
 *   node scripts/js/probe_plain_vanilla_1a.js [basisordner]
 *
 * basisordner: Ordner mit landing/js/… (Standard: Repo); der Mutationstest übergibt eine mutierte Kopie.
 * Ausgabe: eine JSON-Zeile {pruefungen: {name: true | "Fehlertext"}} und als letzte Zeile ENDE. Fehlt ENDE, ist die
 * Probe abgebrochen — das gilt nie als Nachweis. Prüfungen mit Präfix [Aufbau] testen das Gerüst, nicht das Verhalten.
 * Fälle: Codex-Review Runde 1 (Befunde 1–13) und Plan v5 E1–E9, Eingaben wörtlich aus den Befunden.
 */
const fs = require('fs');
const path = require('path');
const BASIS = path.resolve(process.argv[2] || path.join(__dirname, '..', '..'));

const window = {};
for (const f of ['holidays.js', 'indicators.js', 'strategy-compute.js', 'seasonal-compute.js']) {
  new Function('window', 'var SA = window.SA || {};\n' + fs.readFileSync(path.join(BASIS, 'landing/js', f), 'utf8') + '\nwindow.SA = SA;')(window);
}
const SA = window.SA, S = SA.strategy;
const P = {};
function pruefe(name, fn) {
  try { const r = fn(); P[name] = r === true ? true : String(r); }
  catch (e) { P[name] = 'Ausnahme: ' + (e && e.message || e); }
}
function gleich(ist, soll, was) { return ist === soll ? true : was + ': ist ' + JSON.stringify(ist) + ', soll ' + JSON.stringify(soll); }
function nah(ist, soll, was) { return Math.abs(ist - soll) < 1e-9 ? true : was + ': ist ' + ist + ', soll ' + soll; }

/** NYSE-Sitzungen von..bis mit Schlusskurs aus fn(datum, index) */
function sitzungen(von, bis, fn, boerse) {
  const out = [];
  let d = new Date(von + 'T12:00:00Z');
  const e = new Date(bis + 'T12:00:00Z');
  for (; d <= e; d.setUTCDate(d.getUTCDate() + 1)) {
    const s = d.toISOString().slice(0, 10);
    if (SA.holidays.isTradingDay(s, boerse || 'NYSE')) out.push({ date: s, close: fn(s, out.length) });
  }
  return out;
}
function mitKontext(stichtag, fn) { S.setKontext({ stichtag, boerse: 'NYSE' }); try { return fn(); } finally { S.setKontext(null); } }

pruefe('[Aufbau] module', () => (S && S.auswerten && S.streak && S.regeltermine && S.formatPF && SA.seasonal && SA.seasonal._quantil) ? true : 'Funktionen fehlen');

// Befund 1: September-Vermeidung, Kurse 30.09.–08.10.2025 = 100…160 → Ausstieg 2026 noch nicht fällig → offen
pruefe('sep_offen', () => {
  const rows = sitzungen('2025-09-30', '2025-10-08', (s, i) => 100 + 10 * i);
  const tr = mitKontext('2025-10-08', () => S.calc_september_avoid(rows));
  if (tr.length !== 1) return 'erwartet 1 Trade, ist ' + tr.length;
  if (!tr[0].open) return 'Trade ist geschlossen (' + tr[0].exit_date + ', ' + tr[0].return_pct + ' %) statt offen';
  if (tr[0].zustand_ausstieg !== 'noch_nicht_faellig') return 'Zustand ' + tr[0].zustand_ausstieg;
  return gleich(S.computeStats(tr), null, 'Statistik nur aus offenen Trades');
});

// Befund 1 (Month-End): kein Einstieg am 06.10.2026 als „vorletzter Handelstag Oktober"
pruefe('month_end_rand', () => {
  const rows = sitzungen('2026-08-03', '2026-10-07', (s, i) => 100 + i);
  const tr = mitKontext('2026-10-07', () => S.calc_month_end(rows));
  const falsch = tr.filter(t => t.entry_date >= '2026-10-01');
  if (falsch.length) return 'Einstieg im laufenden Oktober: ' + falsch.map(t => t.entry_date).join(',');
  // Hier entscheidet NUR der Kalender am Monatsrand: Daten bis Mo 28.12.2026, letzter Dezember-Handelstag ist der
  // 31.12. → Post-Christmas muss offen sein. Aus den Zeilen gelesen wäre der 28.12. „der letzte" (geschlossen).
  const dez = sitzungen('2026-12-01', '2026-12-28', (s, i) => 100 + i);
  const pc = mitKontext('2026-12-28', () => S.calc_post_christmas(dez));
  if (pc.length !== 1) return 'Post-Christmas: erwartet 1 Trade, ist ' + pc.length;
  return pc[0].open ? true : 'Post-Christmas am 28.12. geschlossen statt offen';
});

// Befund 3: LBR entscheidet mit dem Vortag — Histogramm fest vorgegeben (gleicher Vektor wie die Python-Gegenprobe)
pruefe('lbr_vortag', () => {
  const rows = sitzungen('2024-09-03', '2025-07-01', () => 100);
  const iOkt = rows.findIndex(r => r.date === '2024-10-01'), iApr = rows.findIndex(r => r.date === '2025-04-01');
  const hist = rows.map((r, i) => (i >= iOkt && i < iApr) ? 1 : (i >= iApr ? -1 : 0));
  const orig = SA.indicators.calcMACD;
  SA.indicators.calcMACD = () => ({ histogram: hist });
  try {
    const tr = mitKontext('2025-07-01', () => S.calc_lbr_november_mai(rows));
    if (tr.length !== 1) return 'erwartet 1 Trade, ist ' + tr.length;
    const e = gleich(tr[0].entry_date, rows[iOkt + 1].date, 'Einstieg');
    if (e !== true) return e;
    return gleich(tr[0].exit_date, rows[iApr + 1].date, 'Ausstieg');
  } finally { SA.indicators.calcMACD = orig; }
});

// N1: ohne Indikatormodul kein stiller Rückfall auf Sell in May
pruefe('n1_kein_rueckfall', () => {
  const orig = SA.indicators.calcMACD;
  delete SA.indicators.calcMACD;
  try { S.calc_lbr_november_mai(sitzungen('2024-09-03', '2024-12-31', () => 100)); return 'kein Fehler geworfen'; }
  catch (e) { return /calcMACD/.test(e.message) ? true : 'falscher Fehler: ' + e.message; }
  finally { SA.indicators.calcMACD = orig; }
});

// Befund 6: Santa 2024 — dritte Sitzung streng vor Thanksgiving = 25.11.2024
pruefe('santa_2024', () => {
  const rows = sitzungen('2024-11-01', '2025-01-10', s => s < '2024-11-25' ? 100 : 110);
  const tr = mitKontext('2025-01-10', () => S.calc_santa_claus(rows));
  const t = tr.find(t => t.entry_date.startsWith('2024'));
  if (!t) return 'kein Trade 2024';
  const e = gleich(t.entry_date, '2024-11-25', 'Einstieg');
  return e !== true ? e : nah(t.return_pct, 0, 'Rendite');
});

// Befund 10: fehlender Ausstiegskurs (NaN) → kein Trade, keine NaN-Statistik
pruefe('nan_exit', () => {
  const rows = sitzungen('2024-10-01', '2025-05-09', () => 100);
  const i3 = rows.filter(r => r.date.startsWith('2025-05')).map(r => rows.indexOf(r))[2];
  rows[i3].close = parseFloat(null);
  const tr = mitKontext('2025-05-09', () => S.calc_sell_in_may(rows));
  return tr.length === 0 ? true : 'Trade trotz NaN-Ausstieg: ' + JSON.stringify(tr[0]);
});

// Befund 10: Profit-Faktor ohne Verlust = null, Anzeige „—"; ungerundete Rendite 100 → 100,004 ist ein Gewinn
pruefe('pf_null', () => {
  const st = S.computeStats([{ entry_date: '2020-01-02', exit_date: '2020-02-03', return_pct: 1 },
                             { entry_date: '2021-01-04', exit_date: '2021-02-01', return_pct: 2 }]);
  const a = gleich(st.profit_factor, null, 'PF'); if (a !== true) return a;
  const b = gleich(S.formatPF(null), '—', 'formatPF(null)'); if (b !== true) return b;
  return gleich(S.formatPF(1.234), '1.23', 'formatPF(1.234)');
});
// Sharpe erst ab MIN_TRADES_SHARPE geschlossenen Trades (zwei Trades mit 11,847/11,845 % ergaben 6855)
pruefe('sharpe_min', () => {
  const tr = (rs) => rs.map((r, i) => ({ entry_date: (2010 + i) + '-01-04', exit_date: (2010 + i) + '-06-01', return_pct: r }));
  const zwei = S.computeStats(tr([11.847357614314383, 11.845068971653427]));
  const a = gleich(zwei.sharpe, null, 'Sharpe aus 2 Trades'); if (a !== true) return a;
  const fuenf = S.computeStats(tr([1, 2, 3, -1, 2]));
  if (typeof fuenf.sharpe !== 'number') return 'Sharpe aus 5 Trades fehlt';
  return gleich(S.formatZahl(null, 2), '\u2014', 'formatZahl(null)');
});
pruefe('ungerundet', () => {
  const rows = [{ date: '2025-10-31', close: 100 }, { date: '2025-11-03', close: 100.004 }];
  const t = S._makeTrade(rows, 0, 1);
  const a = nah(t.return_pct, 0.004, 'Rendite'); if (a !== true) return a;
  return gleich(S.computeStats([t]).win_rate, 100, 'Trefferquote');
});

// Punkt 7: fehlender Indikatorwert → false für jeden Operator
pruefe('sma_warmup', () => {
  const m = SA.indicators.applyFilter([100, 100, 100], [{ type: 'SMA', condition: 'Close > SMA', period: 200 }]);
  const a = gleich(JSON.stringify(m), '[false,false,false]', 'SMA-Maske'); if (a !== true) return a;
  const r = SA.indicators.applyFilter([100, 101, 102, 103], [{ type: 'Regime', condition: 'Regime != Bear', period: 20 }]);
  return gleich(JSON.stringify(r), '[false,false,false,false]', 'Regime != Bear ohne Regime');
});

// Befund 2 / E4 / E5: Stops im Close-Modus
const T0 = (o) => Object.assign({ entry_date: '2025-01-02', exit_date: '2025-01-06', entry_price: 100, exit_price: 110, return_pct: 10 }, o || {});
const R3 = (c1, c2) => [{ date: '2025-01-02', close: 100 }, { date: '2025-01-03', close: c1 }, { date: '2025-01-06', close: c2 }];
pruefe('stop_gap', () => {
  const t = S.applyStopLoss(R3(80, 110), [T0()], 8)[0];
  if (!t.stopped) return 'nicht gestoppt';
  const a = nah(t.exit_price, 80, 'Ausstiegskurs'); return a !== true ? a : nah(t.return_pct, -20, 'Rendite');
});
pruefe('stop_am_exit', () => {
  const t = S.applyStopLoss(R3(95, 91), [T0({ exit_price: 91, return_pct: -9 })], 8);
  if (t.length !== 1 || !t[0].stopped) return 'erwartet genau 1 gestoppten Trade';
  const a = gleich(t[0].exit_date, '2025-01-06', 'Ausstiegstag'); return a !== true ? a : nah(t[0].return_pct, -9, 'Rendite');
});
pruefe('stop_offen', () => {
  const t = S.applyStopLoss(R3(80, 85), [T0({ open: true, zustand_ausstieg: 'noch_nicht_faellig', exit_price: 85, return_pct: -15 })], 8)[0];
  return (t.stopped && !t.open && t.zustand_ausstieg === 'gefunden' && !t.regeltermin_ausstieg) ? true : 'gestoppter Trade nicht geschlossen: ' + JSON.stringify(t);
});
pruefe('stop_hebel', () => {
  const t = S.applyStopLoss(R3(80, 110), [T0({ leverage: 1.5, return_pct: 15 })], 8)[0];
  const a = gleich(t.leverage, 1.5, 'Hebel'); return a !== true ? a : nah(t.return_pct, -30, 'Rendite × Hebel');
});
pruefe('trailing_close', () => {
  const t = S.applyTrailingStop(R3(120, 109), [T0({ exit_price: 109, return_pct: 9 })], 8)[0];
  if (!t.stopped) return 'nicht gestoppt (Peak 120, Close 109 < 110,4)';
  return nah(t.exit_price, 109, 'Ausstieg zum Close');
});

// E7: Datenbestand veraltet (> 10 Sitzungen) → offene Kandidaten raus, gestoppte bleiben
SA.STRATEGIES.__probe = { name: 'probe', func: 'calc__probe', cat: 'x' };
S.calc__probe = function(rows) { return [this._makeTrade(rows, 0, -2)]; };
const ROWS_E7 = [{ date: '2025-03-03', close: 100 }, { date: '2025-03-04', close: 80 }, { date: '2025-03-05', close: 82 }];
const stichtagNach = n => S._kalenderSchritt('2025-03-05', n, 'NYSE');
pruefe('datenende_veraltet', () => {
  const zehn = S.auswerten(ROWS_E7, '__probe', { stichtag: stichtagNach(10), boerse: 'NYSE' });
  const elf = S.auswerten(ROWS_E7, '__probe', { stichtag: stichtagNach(11), boerse: 'NYSE' });
  if (zehn.veraltet || zehn.trades.length !== 1 || !zehn.trades[0].open) return '10 Sitzungen: offener Trade erwartet';
  if (!elf.veraltet || elf.trades.length !== 0 || elf.unvollstaendig.length !== 1) return '11 Sitzungen: Trade muss in unvollstaendig';
  const mitStop = S.auswerten(ROWS_E7, '__probe', { stichtag: stichtagNach(11), boerse: 'NYSE', stop: { typ: 'fixed', pct: 8 } });
  if (mitStop.trades.length !== 1 || !mitStop.trades[0].stopped) return 'gestoppter Trade bei veraltetem Bestand verloren';
  return nah(mitStop.trades[0].return_pct, -20, 'gestoppte Rendite');
});

// E2: Einstieg auf der letzten Kurszeile → offene Position mit 0 %
pruefe('einstieg_letzte_zeile', () => {
  const rows = sitzungen('2025-10-01', '2025-10-31', () => 100);
  const tr = mitKontext('2025-10-31', () => S.calc_sell_in_may(rows));
  if (tr.length !== 1 || !tr[0].open) return 'erwartet 1 offenen Trade, ist ' + JSON.stringify(tr);
  return nah(tr[0].return_pct, 0, 'Rendite');
});

// Befund 13 / E9: Streak aus der konfigurierten Auswertung, offene Trades zählen nicht; Stop verändert die Streak
SA.STRATEGIES.__streak = { name: 'streak', func: 'calc__streak', cat: 'x' };
S.calc__streak = function(rows) {
  return [this._makeTrade(rows, 0, 1), this._makeTrade(rows, 2, -2)];   // +10 % geschlossen, dann offen
};
const ROWS_ST = [{ date: '2025-02-03', close: 100 }, { date: '2025-02-04', close: 110 }, { date: '2025-02-05', close: 100 },
                 { date: '2025-02-06', close: 80 }];
pruefe('streak_konfig', () => {
  const ohne = S.auswerten(ROWS_ST, '__streak', { stichtag: '2025-02-06', boerse: 'NYSE' });
  const a = gleich(JSON.stringify(ohne.streak), JSON.stringify({ typ: 'gewinn', n: 1 }), 'Streak ohne Stop'); if (a !== true) return a;
  const mit = S.auswerten(ROWS_ST, '__streak', { stichtag: '2025-02-06', boerse: 'NYSE', stop: { typ: 'fixed', pct: 8 } });
  return gleich(JSON.stringify(mit.streak), JSON.stringify({ typ: 'verlust', n: 1 }), 'Streak mit Stop');
});

// Befund 12: Median mit Interpolation
pruefe('median', () => {
  const a = gleich(SA.seasonal._quantil([10, 30], 0.5), 20, 'Median [10,30]'); if (a !== true) return a;
  return gleich(SA.seasonal._quantil([1, 2, 3, 4], 0.25), 1.75, 'Quantil 0,25');
});

// Befund 5: Regeltermin Sell-in-May-Ausstieg = 3. Handelstag Mai
pruefe('regeltermine', () => {
  const r = S.regeltermine('2026-01-02', 'NYSE').filter(x => x.key === 'sell_in_may' && x.type === 'exit' && x.date.startsWith('2026'));
  return gleich(r.map(x => x.date).join(','), '2026-05-05', 'Sell-in-May-Ausstieg 2026');
});

// Codex Code-R1 Befund 1: Sonderschließungen (9/11) sind keine Feiertags-Handelsanlässe
pruefe('sonder_kein_feiertag', () => {
  const rows = sitzungen('2001-08-01', '2001-12-31', (s, i) => 100 + i);
  const tr = mitKontext('2001-12-31', () => S.calc_one_day_holiday(rows));
  const ein = tr.map(t => t.entry_date);
  if (new Set(ein).size !== ein.length) return 'doppelte Trades: ' + ein.filter((d, i) => ein.indexOf(d) !== i).join(',');
  return ein.indexOf('2001-09-07') < 0 ? true : 'Trade vor 9/11 (Sonderschließung) erzeugt';
});

// Befund 2: historischer Termin im letzten Datenmonat bleibt zeilenbasiert (Lücke am 01.10. → wie bisher)
pruefe('rand_historisch', () => {
  const rows = sitzungen('2026-09-01', '2026-10-07', (s, i) => 100 + i).filter(r => r.date !== '2026-10-01');
  const tr = mitKontext('2026-10-07', () => S.calc_second_trading_day(rows));
  return tr.some(t => t.entry_date === '2026-10-02' && t.exit_date === '2026-10-05' && !t.open) ? true
    : 'Trade 02.10.→05.10. fehlt: ' + JSON.stringify(tr.filter(t => t.entry_date >= '2026-10-01'));
});

// Befund 3: Stops ignorieren ungültige Kurse (0, null)
pruefe('stop_ungueltig', () => {
  for (const kurs of [0, null]) {
    for (const art of ['fixed', 'trailing']) {
      const fn = art === 'fixed' ? S.applyStopLoss : S.applyTrailingStop;
      const t = fn.call(S, R3(kurs, 110), [T0()], 8)[0];
      if (t.stopped) return art + '-Stop löst bei Kurs ' + kurs + ' aus (' + t.return_pct + ' %)';
    }
  }
  return true;
});

// Befund 9 / E8: Zustandsfelder am Trade und Regeltermin im Protokoll
pruefe('e8_felder', () => {
  const rows = sitzungen('2025-09-30', '2025-10-08', (s, i) => 100 + 10 * i);
  const t = mitKontext('2025-10-08', () => S.calc_september_avoid(rows))[0];
  const soll = { zustand_einstieg: 'gefunden', zustand_ausstieg: 'noch_nicht_faellig', regeltermin_ausstieg: '2026-08-31',
                 bewertungsstichtag: '2025-10-08', letzte_kurszeile: '2025-10-08' };
  for (const k in soll) if (t[k] !== soll[k]) return k + ': ist ' + t[k] + ', soll ' + soll[k];
  SA.STRATEGIES.__e8 = { name: 'e8', func: 'calc_month_end', cat: 'x' };
  const r = S.auswerten(sitzungen('2026-08-03', '2026-10-07', (s, i) => 100 + i), '__e8', { stichtag: '2026-10-07', boerse: 'NYSE' });
  const p = r.protokoll.find(x => x.grund === 'einstieg_noch_nicht_faellig');
  return (p && p.datum === '2026-10-29') ? true : 'Protokoll ohne Regeltermin: ' + JSON.stringify(r.protokoll.slice(0, 3));
});

// Codex Code-R2 Befund 1: vorletzter Handelstag im unvollständigen Monat aus dem Kalender (29.10.2026, nicht 28.10.)
pruefe('month_end_unvollstaendig', () => {
  const rows = sitzungen('2026-09-01', '2026-10-29', (s) => s === '2026-10-29' ? 110 : 100);
  const tr = mitKontext('2026-10-29', () => S.calc_month_end(rows)).filter(t => t.entry_date >= '2026-10-01');
  if (tr.length !== 1) return 'erwartet 1 Oktober-Trade, ist ' + tr.length;
  const a = gleich(tr[0].entry_date, '2026-10-29', 'Einstieg'); if (a !== true) return a;
  return tr[0].open ? true : 'Trade nicht offen';
});

// Codex Code-R2 Befund 2 (JS-Seite, Sollwerte für den Python-Vergleich): Monthly 10 bis 21.10.2026
pruefe('monthly10_rand', () => {
  const rows = sitzungen('2026-10-01', '2026-10-21', (s, i) => 100 + i);
  const tr = mitKontext('2026-10-21', () => S.calc_monthly_10(rows)).filter(t => !t.open);
  return gleich(tr.map(t => t.entry_date + '>' + t.exit_date).join(','), '2026-10-01>2026-10-06,2026-10-13>2026-10-16', 'geschlossene Blöcke');
});

process.stdout.write(JSON.stringify({ pruefungen: P }) + '\nENDE\n');

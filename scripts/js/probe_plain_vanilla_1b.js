/**
 * probe_plain_vanilla_1b.js — fachliche Prüffälle Phase 1B /plain-vanilla gegen die ECHTEN Module.
 *
 *   node scripts/js/probe_plain_vanilla_1b.js [basisordner]
 *
 * Plan: docs/review_prompts/2026-10-08_plain_vanilla_1b_plan.md (v3, Codex-Freigabe Runde 3). Ausgabe wie die
 * 1A-Probe: eine JSON-Zeile {pruefungen, werte} und als letzte Zeile ENDE (fehlt ENDE, ist die Probe abgebrochen —
 * nie ein Nachweis). `werte` liefert dem Python-Teil die JS-Ergebnisse derselben Fälle für den Zwillingsvergleich.
 * Prüfungen mit Präfix [Aufbau] testen das Gerüst, nicht das Verhalten.
 */
const fs = require('fs');
const path = require('path');
const BASIS = path.resolve(process.argv[2] || path.join(__dirname, '..', '..'));

const window = {};
for (const f of ['holidays.js', 'indicators.js', 'strategy-compute.js']) {
  new Function('window', 'var SA = window.SA || {};\n' + fs.readFileSync(path.join(BASIS, 'landing/js', f), 'utf8') + '\nwindow.SA = SA;')(window);
}
const SA = window.SA, S = SA.strategy;
const P = {}, W = {};
function pruefe(name, fn) {
  try { const r = fn(); P[name] = r === true ? true : String(r); }
  catch (e) { P[name] = 'Ausnahme: ' + (e && e.message || e); }
}
function nah(ist, soll, was, tol) { return Math.abs(ist - soll) <= (tol || 1e-9) ? true : was + ': ist ' + ist + ', soll ' + soll; }
function sitzungen(von, bis, fn, boerse) {
  const out = [];
  const d = new Date(von + 'T12:00:00Z'), e = new Date(bis + 'T12:00:00Z');
  for (; d <= e; d.setUTCDate(d.getUTCDate() + 1)) {
    const s = d.toISOString().slice(0, 10);
    if (SA.holidays.isTradingDay(s, boerse || 'NYSE')) out.push({ date: s, close: fn(s, out.length) });
  }
  return out;
}
function mitKontext(stichtag, boerse, fn) { S.setKontext({ stichtag, boerse }); try { return fn(); } finally { S.setKontext(null); } }
const tg24 = t => t.entry_date >= '2024-11-01' && t.entry_date <= '2024-11-30';

pruefe('[Aufbau] module', () => (S && S._hebelPfad && S.tagesEquity && S._lueckenMarkieren && S.auswerten && SA.holidays._XETRA_SONDER)
  ? true : 'Funktionen fehlen');

// T2: Thanksgiving 28.11.2024 — UHTS S⁻3 → S⁺3 = 25.11. → 03.12. (1A lieferte 04.12.); One-Day S⁻2 → S⁻1 unverändert
pruefe('t_thanksgiving', () => {
  const rows = sitzungen('2024-11-01', '2024-12-31', () => 100);
  const u = mitKontext('2024-12-31', 'NYSE', () => S.calc_uhts(rows)).filter(tg24);
  if (u.length !== 1) return 'UHTS: erwartet 1 Trade um Thanksgiving, ist ' + u.length;
  if (u[0].entry_date !== '2024-11-25' || u[0].exit_date !== '2024-12-03') return 'UHTS ' + u[0].entry_date + '→' + u[0].exit_date + ', soll 2024-11-25→2024-12-03';
  const o = mitKontext('2024-12-31', 'NYSE', () => S.calc_one_day_holiday(rows)).filter(tg24);
  return (o.length === 1 && o[0].entry_date === '2024-11-26' && o[0].exit_date === '2024-11-27') ? true
    : 'One-Day ' + JSON.stringify(o.map(t => t.entry_date + '→' + t.exit_date));
});

// T3: XETRA handelt an Thanksgiving — Intervall S⁻1 (27.11.) → F (28.11.) trägt bereits 2x
pruefe('t_xetra_feiertag_offen', () => {
  const rows = sitzungen('2024-11-01', '2024-12-31', () => 100, 'XETRA');
  const u = mitKontext('2024-12-31', 'XETRA', () => S.calc_uhts(rows)).filter(tg24);
  if (u.length !== 1) return 'erwartet 1 Trade, ist ' + u.length;
  const h = {}; u[0].hebel.forEach(x => { h[x[0]] = x[1]; });
  if (u[0].entry_date !== '2024-11-25' || u[0].exit_date !== '2024-12-03') return 'Termine ' + u[0].entry_date + '→' + u[0].exit_date;
  return (h['2024-11-27'] === 1 && h['2024-11-28'] === 2) ? true : 'Hebel 27.11.=' + h['2024-11-27'] + ', 28.11.=' + h['2024-11-28'] + ' (soll 1 und 2)';
});

// H: Kurstreppe von Hand — 25.11.=100, 26.=110, 27.=99, 29.=108.9, 02.12.=119.79, 03.12.=107.811
//    1x: +10 %, −10 %; ab Schluss 27.11. 2x: +10 % → 1,2; +10 % → 1,2; −10 % → 0,8 → Π = 1,14048 → +14,048 %
const TREPPE = { '2024-11-25': 100, '2024-11-26': 110, '2024-11-27': 99, '2024-11-29': 108.9, '2024-12-02': 119.79, '2024-12-03': 107.811 };
pruefe('h_treppe', () => {
  const rows = sitzungen('2024-11-01', '2024-12-31', s => TREPPE[s] || 100);
  const u = mitKontext('2024-12-31', 'NYSE', () => S.calc_uhts(rows)).filter(tg24)[0];
  if (!u) return 'kein Trade';
  W.h_treppe = u.return_pct;
  return nah(u.return_pct, (1.1 * 0.9 * 1.2 * 1.2 * 0.8 - 1) * 100, 'Rendite', 1e-9);
});

// H3/S2: Stop am ersten 2x-Tag (29.11. Close 90): 1,01 · 100/101 · (1 + 2·(−0,1)) − 1 = −20 %, Pfad gekürzt
const STOPKURS = { '2024-11-25': 100, '2024-11-26': 101, '2024-11-27': 100, '2024-11-29': 90 };
pruefe('h_stop', () => {
  const rows = sitzungen('2024-11-01', '2024-12-31', s => STOPKURS[s] || 90);
  for (const typ of ['fixed', 'trailing']) {
    SA.STRATEGIES.__uhts = { name: 'u', func: 'calc_uhts', cat: 'x' };
    const r = S.auswerten(rows, '__uhts', { stichtag: '2024-12-31', boerse: 'NYSE', stop: { typ, pct: 8 } });
    const t = r.trades.filter(tg24)[0];
    if (!t || !t.stopped || t.exit_date !== '2024-11-29') return typ + ': kein Stop am 29.11. (' + JSON.stringify(t && [t.exit_date, t.stopped]) + ')';
    const n = nah(t.return_pct, -20, typ + ' Rendite'); if (n !== true) return n;
    if (t.hebel.length !== 3 || t.hebel[2][1] !== 2) return typ + ': Pfad nicht gekürzt (' + t.hebel.length + ' Intervalle)';
    W['h_stop_' + typ] = t.return_pct;
  }
  return true;
});

// H4: offener UHTS am Datenrand — Kurse bis 26.11.2024, Stichtag 26.11. → offen, nicht in Kennzahlen/Tageskurve
pruefe('h_offen_rand', () => {
  const rows = sitzungen('2024-11-01', '2024-11-26', (s, i) => 100 + i);
  SA.STRATEGIES.__uhts = { name: 'u', func: 'calc_uhts', cat: 'x' };
  const r = S.auswerten(rows, '__uhts', { stichtag: '2024-11-26', boerse: 'NYSE' });
  const t = r.trades.filter(tg24)[0];
  if (!t || !t.open) return 'kein offener Trade';
  if (t.hebel.some(x => x[1] !== 1)) return 'Hebel vor der Aufstockung ≠ 1';
  return r.stats === null || (r.stats.n_trades === r.trades.filter(x => !x.open).length) ? true : 'offener Trade in den Kennzahlen';
});

// L1: fehlende Sitzung 14.01.2015 (echter Handelstag) → 1; vor 2000 Abstand 5 Tage → 1, 4 Tage → 0
pruefe('l_2015', () => {
  const rows = sitzungen('2015-01-12', '2015-01-16', () => 100).filter(r => r.date !== '2015-01-14');
  const t = { entry_date: '2015-01-12', exit_date: '2015-01-16', entry_price: 100, exit_price: 100, return_pct: 0 };
  mitKontext('2015-01-16', 'NYSE', () => S._lueckenMarkieren(rows, [t]));
  W.l_2015 = [t.fehlende_sitzungen, t.auffaellige_abstaende];
  return (t.fehlende_sitzungen === 1 && t.auffaellige_abstaende === 0) ? true : 'fehlend ' + t.fehlende_sitzungen + ', Abstand ' + t.auffaellige_abstaende;
});
pruefe('l_vor2000', () => {
  // Fr 06.01.1995 → Mi 11.01.1995 = 5 Tage (Abstand); Fr 13.01.1995 → Di 17.01.1995 = 4 Tage (kein Abstand)
  const rows = [{ date: '1995-01-05', close: 100 }, { date: '1995-01-06', close: 100 }, { date: '1995-01-11', close: 100 },
                { date: '1995-01-13', close: 100 }, { date: '1995-01-17', close: 100 }];
  const a = { entry_date: '1995-01-05', exit_date: '1995-01-11', entry_price: 100, exit_price: 100, return_pct: 0 };
  const b = { entry_date: '1995-01-13', exit_date: '1995-01-17', entry_price: 100, exit_price: 100, return_pct: 0 };
  mitKontext('1995-01-17', 'NYSE', () => S._lueckenMarkieren(rows, [a, b]));
  W.l_vor2000 = [a.auffaellige_abstaende, b.auffaellige_abstaende];
  return (a.auffaellige_abstaende === 1 && b.auffaellige_abstaende === 0 && a.fehlende_sitzungen === 0) ? true
    : '5 Tage → ' + a.auffaellige_abstaende + ', 4 Tage → ' + b.auffaellige_abstaende;
});
pruefe('l_jahreswechsel', () => {
  // 30.12.1999 fehlt (vor 2000: nur Heuristik, 2 Tage → nichts), 04.01.2000 fehlt (geprüfter Bereich → 1)
  const rows = [{ date: '1999-12-28', close: 100 }, { date: '1999-12-29', close: 100 }, { date: '1999-12-31', close: 100 },
                { date: '2000-01-03', close: 100 }, { date: '2000-01-05', close: 100 }];
  const t = { entry_date: '1999-12-28', exit_date: '2000-01-05', entry_price: 100, exit_price: 100, return_pct: 0 };
  mitKontext('2000-01-05', 'NYSE', () => S._lueckenMarkieren(rows, [t]));
  W.l_jahreswechsel = [t.fehlende_sitzungen, t.auffaellige_abstaende];
  return (t.fehlende_sitzungen === 1 && t.auffaellige_abstaende === 0) ? true : 'fehlend ' + t.fehlende_sitzungen + ', Abstand ' + t.auffaellige_abstaende;
});

// V1: Näherung bei gehebeltem Trade mit Lücke. (a) 27.11.2024 fehlt: S⁻1 nach Zeilenzählung (1A/L4) = 26.11.,
// Ersatzintervall 26.→29.11. mit 2x: 1 + 2·0,21 → +42 %. (b) 26.11. fehlt: Lücke im 1x-Teil, Hebel später → Näherung.
pruefe('l_naeherung', () => {
  const ka = { '2024-11-22': 100, '2024-11-25': 100, '2024-11-26': 100, '2024-11-29': 121 };
  const ra = sitzungen('2024-11-01', '2024-12-31', s => ka[s] || 121).filter(r => r.date !== '2024-11-27');
  SA.STRATEGIES.__uhts = { name: 'u', func: 'calc_uhts', cat: 'x' };
  const a = S.auswerten(ra, '__uhts', { stichtag: '2024-12-31', boerse: 'NYSE' }).trades.filter(tg24)[0];
  if (!a || !a.naeherung || a.fehlende_sitzungen !== 1) return '(a) naeherung ' + (a && a.naeherung) + ', fehlend ' + (a && a.fehlende_sitzungen);
  const n = nah(a.return_pct, 42, '(a) Rendite'); if (n !== true) return n;
  W.l_naeherung_a = [a.entry_date, a.exit_date, a.return_pct];
  const rb = sitzungen('2024-11-01', '2024-12-31', () => 100).filter(r => r.date !== '2024-11-26');
  const b = S.auswerten(rb, '__uhts', { stichtag: '2024-12-31', boerse: 'NYSE' }).trades.filter(tg24)[0];
  if (!b) return '(b) kein Trade';
  const lueckeH = b.hebel.filter(x => x[0] === '2024-11-27')[0];
  if (!lueckeH || lueckeH[1] !== 1) return '(b) Lückenintervall nicht 1x: ' + JSON.stringify(lueckeH);
  return b.naeherung ? true : '(b) Lücke im 1x-Teil eines gehebelten Trades ohne Näherung';
});
pruefe('l_1x_exakt', () => {
  const rows = sitzungen('2024-11-01', '2024-12-31', () => 100).filter(r => r.date !== '2024-11-26');
  const t = mitKontext('2024-12-31', 'NYSE', () => S._lueckenMarkieren(rows, S.calc_one_day_holiday(rows))).filter(tg24);
  return t.every(x => !x.naeherung) ? true : '1x-Trade über Lücke als Näherung markiert';
});

// E3: überlappende Fenster 1x und 2x → Exposure 2x (nicht 3x); Stop nur eines Fensters
pruefe('e_ueberlappung', () => {
  const rows = [{ date: '2024-01-02', close: 100 }, { date: '2024-01-03', close: 110 }, { date: '2024-01-04', close: 121 }];
  const t1 = { entry_date: '2024-01-02', exit_date: '2024-01-04', entry_price: 100, exit_price: 121, return_pct: 21 };
  const t2 = { entry_date: '2024-01-02', exit_date: '2024-01-04', entry_price: 100, exit_price: 121, return_pct: 44,
               leverage: 2, hebel: [['2024-01-03', 2], ['2024-01-04', 2]] };
  const e = mitKontext('2024-01-04', 'NYSE', () => S.tagesEquity(rows, [t1, t2], 1000));
  const a = nah(e.final_equity, 1000 * 1.2 * 1.2, 'Endwert 2x', 1e-6); if (a !== true) return a;
  // Fenster 2x am 03.01. gestoppt, 1x-Fenster läuft weiter → 03.01. 2x, 04.01. 1x
  const t3 = { entry_date: '2024-01-02', exit_date: '2024-01-03', entry_price: 100, exit_price: 110, return_pct: 20,
               leverage: 2, hebel: [['2024-01-03', 2]], stopped: true };
  const f = mitKontext('2024-01-04', 'NYSE', () => S.tagesEquity(rows, [t1, t3], 1000));
  W.e_ueberlappung = [e.final_equity, f.final_equity];
  return nah(f.final_equity, 1000 * 1.2 * 1.1, 'Endwert nach Stop eines Fensters', 1e-6);
});
// E4: −30 % Zwischentief, +5 % Ausstieg → täglich −30 %, Trade-DD 0; offener Trade zählt nicht in die Tageskurve
pruefe('e_zwischentief', () => {
  const rows = [{ date: '2024-01-02', close: 100 }, { date: '2024-01-03', close: 70 }, { date: '2024-01-04', close: 105 },
                { date: '2024-01-05', close: 50 }];
  const t = { entry_date: '2024-01-02', exit_date: '2024-01-04', entry_price: 100, exit_price: 105, return_pct: 5 };
  const offen = { entry_date: '2024-01-04', exit_date: '2024-01-05', entry_price: 105, exit_price: 50, return_pct: -52.38, open: true };
  const e = mitKontext('2024-01-05', 'NYSE', () => S.tagesEquity(rows, [t, offen], 1000));
  const st = S.computeStats([t, offen]);
  W.e_zwischentief = [e.max_dd, e.final_equity];
  if (st.max_drawdown !== 0) return 'Trade-DD ' + st.max_drawdown + ', soll 0';
  const a = nah(e.max_dd, -30, 'täglicher DD', 1e-9); if (a !== true) return a;
  return nah(e.final_equity, 1050, 'Endwert ohne offenen Trade', 1e-9);
});
// V3: Hebel ohne täglichen Pfad → taeglich null (kein 1x-Kontowert)
pruefe('e_hebel_ohne_pfad', () => {
  const rows = [{ date: '2024-01-02', close: 100 }, { date: '2024-01-03', close: 110 }];
  const t = { entry_date: '2024-01-02', exit_date: '2024-01-03', entry_price: 100, exit_price: 110, return_pct: 15, leverage: 1.5 };
  return mitKontext('2024-01-03', 'NYSE', () => S.tagesEquity(rows, [t], 1000)) === null ? true : 'Tageskurve trotz Hebel ohne Pfad';
});
// E2: Ergebnisvertrag — alte Schlüssel unverändert trade-basiert, Tageswerte unter taeglich
pruefe('e_vertrag', () => {
  const rows = sitzungen('2023-01-02', '2024-12-31', (s, i) => 100 + Math.sin(i / 7) * 10);
  const r = S.auswerten(rows, 'sell_in_may', { stichtag: '2024-12-31', boerse: 'NYSE' });
  const alt = S.computeStats(r.trades);
  if (!r.stats.taeglich || typeof r.stats.taeglich.max_dd !== 'number') return 'taeglich fehlt';
  for (const k of ['max_drawdown', 'final_equity', 'total_return', 'cagr']) if (r.stats[k] !== alt[k]) return k + ' hat die Bedeutung gewechselt';
  return (r.stats.luecken && r.stats.luecken.von === r.trades.filter(t => !t.open).length) ? true : 'luecken-Zähler fehlt';
});

// Codex Code-R1 1B Befund 1: ungültiger Zwischenkurs (0 / NaN). Trade 02.→05.01.2024 1x, Closes 100, x, 110, 121:
// Tageskurve überbrückt den ungültigen Kurs (Endwert 1.210 wie die Trade-Rendite +21 %), Lücke wird gezählt;
// wechselt das Exposure über den ungültigen Kurs, setzen die Tageswerte mit Grund aus.
pruefe('e_ungueltiger_kurs', () => {
  for (const x of [0, NaN, null]) {
    const rows = [{ date: '2024-01-02', close: 100 }, { date: '2024-01-03', close: x }, { date: '2024-01-04', close: 110 },
                  { date: '2024-01-05', close: 121 }];
    const t = { entry_date: '2024-01-02', exit_date: '2024-01-05', entry_price: 100, exit_price: 121, return_pct: 21 };
    mitKontext('2024-01-05', 'NYSE', () => S._lueckenMarkieren(rows, [t]));
    if (t.fehlende_sitzungen !== 1) return 'Close ' + x + ': fehlende Sitzungen ' + t.fehlende_sitzungen + ', soll 1';
    const e = mitKontext('2024-01-05', 'NYSE', () => S.tagesEquity(rows, [t], 1000));
    const a = nah(e && e.final_equity, 1210, 'Close ' + x + ' Endwert', 1e-9); if (a !== true) return a;
    // Exposure-Wechsel über den ungültigen Kurs: 1x-Trade 02.→04., 2x-Fenster 03.→05.
    const t2 = { entry_date: '2024-01-03', exit_date: '2024-01-05', entry_price: 100, exit_price: 121, return_pct: 0,
                 leverage: 2, hebel: [['2024-01-04', 2], ['2024-01-05', 2]] };
    const t1 = { entry_date: '2024-01-02', exit_date: '2024-01-04', entry_price: 100, exit_price: 110, return_pct: 10 };
    const info = {};
    const f = mitKontext('2024-01-05', 'NYSE', () => S.tagesEquity(rows, [t1, t2], 1000, info));
    if (f !== null || info.grund !== 'ungueltiger_kurs') return 'Close ' + x + ': Exposure-Wechsel nicht ausgesetzt (' + JSON.stringify(info) + ')';
  }
  W.e_ungueltiger_kurs = 1210;
  return true;
});

// Snapshot (optional, argv[3] = SPY-Kursdatei): Monthly 10 auf SPY 1994–2025 für den Referenzvergleich im Python-Teil
if (process.argv[3]) {
  const roh = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
  const rows = roh.filter(r => r.date >= '1994-01-01' && r.date <= '2025-12-31').map(r => ({ date: r.date, close: parseFloat(r.close) }));
  const r = S.auswerten(rows, 'monthly_10', { stichtag: '2025-12-31', boerse: 'NYSE' });
  const tg = r.stats.taeglich;
  W.m10 = { faktor: tg.final_equity / 1000, max_dd: tg.max_dd, cagr: tg.cagr, offen: r.trades.filter(t => t.open).length,
            n: r.trades.length };
}

// Werte für den Python-Zwillingsvergleich (dieselben Eingaben im Python-Teil)
W.anker = {};
for (let y = 2000; y <= 2035; y++) W.anker[y] = S._nyseHolidays(y).slice().sort();

process.stdout.write(JSON.stringify({ pruefungen: P, werte: W }) + '\nENDE\n');

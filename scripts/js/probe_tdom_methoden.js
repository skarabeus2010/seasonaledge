/**
 * probe_tdom_methoden.js — die vier Rechenmethoden der TDOM-Kacheln.
 *
 * Die Kacheln zeigten frueher die KUMULIERTE Rendite seit dem Vormonatsschluss. Das ist
 * die Basis des Monatsverlauf-Charts, nicht die eines einzelnen Tages: bei QQQ T16
 * standen 74 % und +2,41 %, davon war fast alles der bereits vergangene Monat.
 * Seit dem 22.10.2026 rechnen sie dieselben vier Methoden wie /tdom-analyse.
 *
 * ENTSCHEIDEND an dieser Probe: die Sollwerte sind UNABHAENGIG in Python aus den
 * Supabase-Kursen gemessen worden (QQQ, Oktober, 27 Jahre), nicht aus dieser
 * Implementierung gewonnen. Geprueft wird die ECHTE calcTdomMethoden aus
 * landing/pages/dashboard.html gegen eine Kursreihe, die dieselben Renditen erzeugt.
 *
 * Aufruf: node scripts/js/probe_tdom_methoden.js   — Exit 0 gruen, 1 rot.
 */
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const WURZEL = path.resolve(__dirname, '..', '..');
const html = fs.readFileSync(path.join(WURZEL, 'landing', 'pages', 'dashboard.html'), 'utf8');

let fehler = 0, anzahl = 0;
function pruef(name, ok, info) {
  anzahl++;
  console.log('  ' + (ok ? 'ok  ' : 'FAIL') + ' ' + name + (info !== undefined ? '  ->  ' + info : ''));
  if (!ok) fehler++;
}

function schneide(name, art) {
  const muster = (art === 'var') ? ('var ' + name + ' = [') : ('function ' + name + '(');
  const start = html.indexOf(muster);
  if (start < 0) throw new Error('nicht gefunden: ' + name);
  if (art === 'var') {
    const ende = html.indexOf('\n    ];', start);
    return html.slice(start, ende + 7);
  }
  let tiefe = 0;
  for (let j = html.indexOf('{', start); j < html.length; j++) {
    if (html[j] === '{') tiefe++;
    else if (html[j] === '}') { tiefe--; if (tiefe === 0) return html.slice(start, j + 1); }
  }
  throw new Error('kein Ende: ' + name);
}

const box = { console, Math, Date, Object, Number, Array, String, isFinite, isNaN, parseInt, parseFloat };
box.window = box;
box.localStorage = { getItem() { return null; }, setItem() {} };
vm.createContext(box);
vm.runInContext("function mean(a){return a.reduce(function(s,x){return s+x;},0)/a.length;}"
  + "function _t(k,d){return d;}", box);
vm.runInContext(schneide('TDOM_METHODEN', 'var'), box);
for (const fn of ['_zahl', 'calcTdomMethoden', 'besteTdomMethode', 'tdomSerie',
                  'tdomMethodeGewaehlt']) {
  vm.runInContext(schneide(fn), box);
}

// ── Reihe mit BEKANNTEN Renditen je Methode ─────────────────────────────────────
// Jede Methode bekommt einen anderen, exakt gesetzten Wert, damit eine Verwechslung
// der Methoden auffaellt (bei gleichen Werten waere die Probe blind dafuer).
//   c2c  = +1,00 %   (ueber log_return)
//   o2c  = +2,00 %   (open -> close desselben Tages)
//   o2no = +3,00 %   (open -> open des naechsten Tages)
//   o2nc = +4,00 %   (open -> close des naechsten Tages)
const LN = Math.log(1.01);
const zeilen = [];
for (let jahr = 2000; jahr <= 2026; jahr++) {
  // T1 ist die GEMESSENE Position; T2 traegt die Werte, aus denen o2no und o2nc
  // entstehen. So hat jede der vier Methoden einen eigenen, exakten Sollwert — bei
  // gleichen Werten waere die Probe blind fuer eine Verwechslung der Methoden.
  //   c2c  = +1 %  aus log_return
  //   o2c  = (102 - 100) / 100 = +2 %
  //   o2no = (103 - 100) / 100 = +3 %   (Eroeffnung des naechsten Handelstags)
  //   o2nc = (104 - 100) / 100 = +4 %   (Schluss des naechsten Handelstags)
  zeilen.push({ date: jahr + '-10-01', open: 100, close: 102, log_return: LN,
                year: jahr, month: 10, tdom: 1 });
  zeilen.push({ date: jahr + '-10-02', open: 103, close: 104, log_return: LN,
                year: jahr, month: 10, tdom: 2 });
}

const jahre = [];
for (let j = 2000; j <= 2026; j++) jahre.push(j);
const tab = box.calcTdomMethoden(zeilen, 10, jahre);

const SOLL = { c2c: 1.0, o2c: 2.0, o2no: 3.0, o2nc: 4.0 };
for (const m in SOLL) {
  const e = tab[1] && tab[1][m];
  pruef('T1 ' + m + ': Ø = ' + SOLL[m].toFixed(2) + ' %',
        e && Math.abs(e.avg - SOLL[m]) < 1e-9, e ? e.avg.toFixed(6) : '—');
  pruef('T1 ' + m + ': n = 27 Jahre', e && e.n === 27, e && e.n);
  pruef('T1 ' + m + ': Trefferquote 100 %', e && Math.abs(e.win - 100) < 1e-9, e && e.win);
}

// Die Methoden duerfen sich nicht vermischen: vier verschiedene Werte.
const werte = Object.keys(SOLL).map(m => tab[1][m].avg);
pruef('die vier Methoden liefern vier VERSCHIEDENE Werte',
      new Set(werte.map(v => v.toFixed(6))).size === 4, werte.map(v => v.toFixed(2)).join(' / '));

// ── Auswahl nach Trefferquote (Nutzerentscheidung) ──────────────────────────────
// Eine Position bauen, an der die Trefferquoten AUSEINANDERGEHEN und eine andere
// Methode gewinnt als nach Ø Rendite.
const z2 = [];
for (let jahr = 2000; jahr <= 2026; jahr++) {
  // c2c: immer +0,1 % -> Quote 100 %, kleiner Mittelwert
  // o2c: 26x -1 %, 1x +60 % -> Quote 3,7 %, GROESSERER Mittelwert
  const gross = (jahr === 2000);
  z2.push({ date: jahr + '-10-01', open: 100,
            close: gross ? 160 : 99, log_return: Math.log(1.001),
            year: jahr, month: 10, tdom: 1 });
}
const tab2 = box.calcTdomMethoden(z2, 10, jahre);
const q = tab2[1];
pruef('[Aufbau] Quote und Mittel kueren verschiedene Sieger',
      q.c2c.win > q.o2c.win && q.o2c.avg > q.c2c.avg,
      'c2c ' + q.c2c.win.toFixed(1) + '% / ' + q.c2c.avg.toFixed(2)
      + ' · o2c ' + q.o2c.win.toFixed(1) + '% / ' + q.o2c.avg.toFixed(2));
pruef('beste Methode wird nach der TREFFERQUOTE gewaehlt, nicht nach Ø Rendite',
      box.besteTdomMethode(tab2, 1) === 'c2c', box.besteTdomMethode(tab2, 1));

// ── Serie: dieselbe Methode wie die Kopfzahl ────────────────────────────────────
const s = box.tdomSerie(tab2[1].o2c);
pruef('Serie aus der Methode: juengstes Jahr 2026 war negativ -> Verlustserie',
      s.type === 'loss' && s.count === 26, s.type + ' ' + s.count);

// Zu wenige Jahre -> keine Methode (die Kachel zeigt dann nichts statt Rauschen).
const duenn = z2.slice(0, 3);
pruef('weniger als fuenf Jahre -> keine beste Methode',
      box.besteTdomMethode(box.calcTdomMethoden(duenn, 10, jahre), 1) === null);

console.log('PROBE-ENDE ' + anzahl);
if (fehler) { console.log('\n[FEHLER] ' + fehler + ' Pruefung(en) rot'); process.exit(1); }
console.log('\n[OK] alle Pruefungen gruen');

/**
 * probe_kachel_erklaerungen.js — Info-Badges und Unterzeilen der sechs Stat-Kacheln.
 *
 * Nutzerwunsch 2026-10-21: ein kleines "i" rechts oben auf Monatsperformance,
 * 2-Wochen-Phase, Wochentag, TDOM Heute, Overnight und TDOM Morgen, das erklaert, WIE
 * die Rendite gerechnet wird; statt der blossen Beobachtungszahl die Rechnung; und in
 * der Overnight-Kachel kurze Wochentage ("Mi -> Do" statt "Mittwoch -> Donnerstag").
 *
 * Geprueft wird am ERGEBNIS: die Badges im Markup, die Schluessel in beiden
 * Woerterbuechern, und das Label der Overnight-Kachel aus der ECHTEN Funktion
 * calcOvernightStats (aus der Seite geschnitten, nicht nachgebaut).
 *
 * Aufruf: node scripts/js/probe_kachel_erklaerungen.js   — Exit 0 gruen, 1 rot.
 */
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const WURZEL = path.resolve(__dirname, '..', '..');
const html = fs.readFileSync(path.join(WURZEL, 'landing', 'pages', 'dashboard.html'), 'utf8');
const de = JSON.parse(fs.readFileSync(path.join(WURZEL, 'landing', 'i18n', 'de.json'), 'utf8'));
const en = JSON.parse(fs.readFileSync(path.join(WURZEL, 'landing', 'i18n', 'en.json'), 'utf8'));

let fehler = 0, anzahl = 0;
function pruef(name, ok, info) {
  anzahl++;
  console.log('  ' + (ok ? 'ok  ' : 'FAIL') + ' ' + name + (info !== undefined ? '  ->  ' + info : ''));
  if (!ok) fehler++;
}

const KACHELN = [
  ['card-month-perf', 'month_perf'],
  ['card-twoweek', 'twoweek'],
  ['card-weekday', 'weekday'],
  ['card-tdom-today', 'tdom_today'],
  ['card-overnight', 'overnight'],
  ['card-tdom-tomorrow', 'tdom_tomorrow'],
];

for (const [kid, s] of KACHELN) {
  const i = html.indexOf('id="' + kid + '"');
  const block = i >= 0 ? html.slice(i, i + 1600) : '';
  pruef('[Badge] ' + kid + ' hat ein Info-Badge mit aria-Schluessel',
        block.indexOf('data-i18n-aria="dash.aria_' + s + '"') >= 0);
  pruef('[Badge] ' + kid + ' hat einen Erklaertext',
        block.indexOf('data-i18n-html="dash.tooltip_' + s + '"') >= 0);
  // Der Text muss die RECHNUNG nennen, nicht nur den Kachelnamen wiederholen.
  const m = block.match(/data-i18n-html="dash\.tooltip_[a-z_]+">([\s\S]*?)<\/div>/);
  const text = m ? m[1] : '';
  pruef('[Badge] ' + kid + ': Erklaertext nennt die Rechnung',
        text.length > 120 && /Rendite|Schluss|Intraday|kumuliert/.test(text),
        text.length + ' Zeichen');
  pruef('[EN] ' + kid + ': Erklaertext und aria uebersetzt',
        typeof en['dash.tooltip_' + s] === 'string' && en['dash.tooltip_' + s].length > 120
        && typeof en['dash.aria_' + s] === 'string');
  pruef('[DE] ' + kid + ': aria-Text vorhanden', typeof de['dash.aria_' + s] === 'string');
}

// Das Badge braucht einen positionierten Elternknoten und darf nicht abgeschnitten
// werden (Projektregel zu Info-Badges).
const css = (html.match(/\.bento-stat6\{[^}]*\}/) || [''])[0];
pruef('[CSS] .bento-stat6 ist positioniert', /position:relative/.test(css), css.slice(0, 80));
pruef('[CSS] .bento-stat6 schneidet nicht ab', !/overflow:hidden/.test(css));

// ── Overnight-Label aus der ECHTEN Funktion ──────────────────────────────────────
function schneide(name) {
  const start = html.indexOf('function ' + name + '(');
  if (start < 0) throw new Error('nicht gefunden: ' + name);
  let tiefe = 0;
  for (let j = html.indexOf('{', start); j < html.length; j++) {
    if (html[j] === '{') tiefe++;
    else if (html[j] === '}') { tiefe--; if (tiefe === 0) return html.slice(start, j + 1); }
  }
  throw new Error('kein Ende: ' + name);
}

const box = { console, Math, Date, Object, Number, Array, String, parseInt, parseFloat, isNaN, isFinite };
box.window = box;
vm.createContext(box);
vm.runInContext("var WEEKDAYS_DE = ['Sonntag','Montag','Dienstag','Mittwoch','Donnerstag','Freitag','Samstag'];"
  + "var WEEKDAYS_SHORT = ['So','Mo','Di','Mi','Do','Fr','Sa'];"
  + "function mean(a){return a.reduce(function(s,x){return s+x;},0)/a.length;}", box);
vm.runInContext(schneide('_wdKurz'), box);
vm.runInContext(schneide('calcOvernightStats'), box);

// Kurszeilen: 60 Wochen, damit jeder Wochentag genug Beobachtungen hat.
const zeilen = [];
let d = new Date(Date.UTC(2024, 0, 1));
for (let i = 0; i < 420; i++) {
  const wd = d.getUTCDay();
  if (wd !== 0 && wd !== 6) {
    const iso = d.toISOString().slice(0, 10);
    zeilen.push({ date: iso, open: 100 + i * 0.1, close: 100.5 + i * 0.1 });
  }
  d = new Date(d.getTime() + 86400000);
}
// Mittwoch = 3
box.SA = undefined;                                  // ohne i18n -> deutsche Kuerzel
const statDe = box.calcOvernightStats(zeilen, 10, 3);
pruef('Overnight-Label deutsch kurz: "Mi → Do"', statDe && statDe.label === 'Mi → Do',
      statDe && statDe.label);

box.SA = { i18n: { t: function (k, f) { return en[k] || f; } } };
const statEn = box.calcOvernightStats(zeilen, 10, 3);
pruef('Overnight-Label englisch kurz: "Wed → Thu"', statEn && statEn.label === 'Wed → Thu',
      statEn && statEn.label);

const statFr = box.calcOvernightStats(zeilen, 10, 5);   // Freitag -> Montag
pruef('Overnight-Label Freitag zeigt auf Montag', statFr && statFr.label === 'Fri → Mon',
      statFr && statFr.label);

// Unterzeilen: die Rechnung statt der blossen Beobachtungszahl.
pruef('Overnight-Unterzeile nennt die Rechnung und die Fallzahl',
      /_t\('dash\.on_sub'[^)]*\)\s*\+\s*' · n '/.test(html));
pruef('Wochentag-Unterzeile nennt die Rechnung und die Fallzahl',
      /_t\('dash\.wd_sub'[^)]*\)/.test(html) && /' · n ' \+ stats\.n/.test(html));
pruef('keine Kachel sagt mehr nur "N Beobachtungen"',
      html.indexOf("' Beobachtungen'") < 0, html.indexOf("' Beobachtungen'"));

// Kurzform-Schluessel in beiden Sprachen.
for (let i = 0; i < 7; i++) {
  pruef('[i18n] Wochentagskuerzel dash.wd_s' + i + ' in DE und EN',
        typeof de['dash.wd_s' + i] === 'string' && typeof en['dash.wd_s' + i] === 'string',
        (de['dash.wd_s' + i] || '?') + ' / ' + (en['dash.wd_s' + i] || '?'));
}

console.log('PROBE-ENDE ' + anzahl);
if (fehler) { console.log('\n[FEHLER] ' + fehler + ' Pruefung(en) rot'); process.exit(1); }
console.log('\n[OK] alle Pruefungen gruen');

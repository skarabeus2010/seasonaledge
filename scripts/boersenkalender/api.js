/*
 * SA.boersenkalender — Börsenkalender und Handelstag-Nummern für die Seiten.
 *
 * Quelle: ausschließlich Python (shared/exchange_holidays.py, shared/symbols.py). Diese Datei ist der
 * API-Teil; scripts/build_boersenkalender_js.py setzt sie mit den Daten zu landing/js/boersenkalender.js
 * zusammen. Nicht von Hand in landing/js/ ändern.
 *
 * Bis zur gemeinsamen Umschaltung (Plan v6, Weg A) bindet KEINE Seite diese Datei ein; holidays.js bleibt
 * der Kalender der Seiten. Der Wächter scripts/verify_boersenkalender_js.py prüft das.
 *
 * Zeitzonenfrei: alle Rechnungen auf ganzen Zahlen (Jahr, Monat, Tag, Tageszähler). Kein Date-Objekt —
 * new Date("YYYY-MM-DD") ist UTC, new Date(j, m, t) lokal, und in Pacific/Apia fehlt der 30.12.2011
 * (Codex Runde 5/6).
 */
(function (global) {
  'use strict';
  var SA = global.SA = global.SA || {};
  var DATEN = /*__DATEN__*/null;
  if (!DATEN || DATEN.schema !== 1) throw new Error('boersenkalender: Daten fehlen oder Schema unbekannt');

  var ALIAS = { NASDAQ: 'NYSE' };
  var ISO = /^[0-9]{4}-[0-9]{2}-[0-9]{2}$/;

  // Eigene Fehlerklasse für GEWOLLTE Fehler (ungültige Eingabe, Datenende). Aufrufer und Wächter
  // unterscheiden damit einen Kalenderfehler von einem Absturz — über die Klasse, nicht über den Text
  // (ein Meldungspräfix ließ sich unterlaufen, Codex P1b R2).
  function KalenderFehler(text) {
    this.name = 'KalenderFehler';
    this.message = 'boersenkalender: ' + text;
    this.stack = (new Error(this.message)).stack;
  }
  KalenderFehler.prototype = Object.create(Error.prototype);
  KalenderFehler.prototype.constructor = KalenderFehler;
  function fehler(text) { throw new KalenderFehler(text); }

  function istSchaltjahr(j) { return (j % 4 === 0 && j % 100 !== 0) || j % 400 === 0; }
  function monatsTage(j, m) { return [31, istSchaltjahr(j) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]; }

  // Tage seit 1970-01-01 (proleptisch gregorianisch, Howard Hinnant) — nur ganze Zahlen.
  function tagNr(j, m, t) {
    var y = m <= 2 ? j - 1 : j;
    var era = Math.floor(y / 400);
    var yoe = y - era * 400;
    var doy = Math.floor((153 * (m + (m > 2 ? -3 : 9)) + 2) / 5) + t - 1;
    var doe = yoe * 365 + Math.floor(yoe / 4) - Math.floor(yoe / 100) + doy;
    return era * 146097 + doe - 719468;
  }
  // Wochentag 0 = Montag … 6 = Sonntag (wie Python date.weekday()); 1970-01-01 war ein Donnerstag.
  function wochentag(j, m, t) { return ((tagNr(j, m, t) % 7) + 7 + 3) % 7; }
  function zweistellig(n) { return (n < 10 ? '0' : '') + n; }
  function iso(j, m, t) { return j + '-' + zweistellig(m) + '-' + zweistellig(t); }

  function boerseNormalisieren(b) {
    if (typeof b !== 'string' || !b.trim()) fehler('Börse fehlt oder ist kein Text: ' + b);
    var e = b.trim().toUpperCase();
    e = ALIAS[e] || e;
    if (!Object.prototype.hasOwnProperty.call(DATEN.woche, e)) fehler('Unbekannte Börse: ' + b);
    return e;
  }

  function ganzzahl(x, name) {
    if (typeof x !== 'number' || !isFinite(x) || Math.floor(x) !== x) fehler(name + ' muss eine ganze Zahl sein: ' + x);
    return x;
  }

  function jahrPruefen(j) {
    ganzzahl(j, 'Jahr');
    if (j < DATEN.von || j > DATEN.bis) fehler('Jahr außerhalb des Rechenbereichs ' + DATEN.von + '–' + DATEN.bis + ': ' + j);
    return j;
  }

  function datumZerlegen(x) {
    if (typeof x !== 'string' || !ISO.test(x)) fehler('Datum nicht im Format YYYY-MM-DD: ' + x);
    var j = +x.slice(0, 4), m = +x.slice(5, 7), t = +x.slice(8, 10);
    if (m < 1 || m > 12 || t < 1 || t > monatsTage(j, m)) fehler('Kein gültiges Datum: ' + x);
    jahrPruefen(j);
    return [j, m, t];
  }

  // Schließtage je (Börse, Jahr) als Menge 'MMDD' — direkt aus den Daten.
  var schliessCache = {};
  function schliessMenge(b, j) {
    var k = b + '|' + j, s = schliessCache[k];
    if (s) return s;
    s = {};
    var roh = (DATEN.schliessungen[b] || {})[String(j)] || '';
    for (var i = 0; i < roh.length; i += 4) s[roh.slice(i, i + 4)] = true;
    schliessCache[k] = s;
    return s;
  }

  function offen(b, j, m, t) {
    if (DATEN.woche[b] === 'taeglich') return true;
    if (wochentag(j, m, t) >= 5) return false;
    return !schliessMenge(b, j)[zweistellig(m) + zweistellig(t)];
  }

  // Nummern je Kalendertag eines Jahres — wie Python _jahresnummern.
  var jahrCache = {};
  function jahresTabelle(b, j) {
    var k = b + '|' + j, tab = jahrCache[k];
    if (tab) return tab;
    var tage = [], jahrSumme = 0, monatSumme = {}, m, t;
    for (m = 1; m <= 12; m++) {
      monatSumme[m] = 0;
      for (t = 1; t <= monatsTage(j, m); t++) {
        var o = offen(b, j, m, t);
        tage.push([m, t, o]);
        if (o) { jahrSumme++; monatSumme[m]++; }
      }
    }
    tab = {};
    var tdoy = 0, tdom = 0, monat = 0;
    for (var i = 0; i < tage.length; i++) {
      m = tage[i][0]; t = tage[i][1];
      if (m !== monat) { monat = m; tdom = 0; }
      if (tage[i][2]) {
        tdoy++; tdom++;
        tab[iso(j, m, t)] = Object.freeze({ tdom: tdom, tdoy: tdoy, tdom_rev: -(monatSumme[m] - tdom + 1),
                                            tdoy_rev: -(jahrSumme - tdoy + 1), offen: true });
      } else {
        tab[iso(j, m, t)] = Object.freeze({ tdom: tdom, tdoy: tdoy, tdom_rev: null, tdoy_rev: null, offen: false });
      }
    }
    jahrCache[k] = tab;
    return tab;
  }

  var API = {
    version: DATEN.version,
    schema: DATEN.schema,
    pruefdatum: DATEN.pruefdatum,
    von: DATEN.von,
    bis: DATEN.bis,
    /** Klasse der gewollten Fehler: `e instanceof SA.boersenkalender.Fehler`. */
    Fehler: KalenderFehler,

    /** Kanonische Börse eines Tickers — dieselbe Regel wie shared.symbols.get_exchange_for_holidays. */
    boerse: function (ticker) {
      if (typeof ticker !== 'string' || !ticker.trim()) fehler('Ticker fehlt: ' + ticker);
      var t = ticker.trim().toUpperCase();
      if (/-USDT?$/.test(t)) return 'CRYPTO';
      if (/=X$/.test(t)) return 'FOREX';
      if (Object.prototype.hasOwnProperty.call(DATEN.ticker, t)) return DATEN.ticker[t];
      for (var i = 0; i < DATEN.suffix.length; i++) {
        var suf = DATEN.suffix[i][0];
        if (t.slice(-suf.length) === suf) return DATEN.suffix[i][1];   // wie Python str.endswith
      }
      if (t.charAt(0) === '^' || t.indexOf('.') >= 0 || t.indexOf('=') >= 0) fehler('Kein Börsenkalender für unbekannten Ticker ' + ticker);
      return 'NYSE';
    },

    istHandelstag: function (datum, boerse) {
      var b = boerseNormalisieren(boerse), d = datumZerlegen(datum);
      return offen(b, d[0], d[1], d[2]);
    },

    /** Wie Python handelstag_nummern: Börse zuerst, Reihenfolge und Duplikate bleiben, unveränderliche Objekte. */
    nummern: function (daten, boerse) {
      var b = boerseNormalisieren(boerse);
      if (!Array.isArray(daten)) fehler('Daten müssen eine Liste sein');
      var zerlegt = daten.map(datumZerlegen), out = [];
      for (var i = 0; i < zerlegt.length; i++) out.push(jahresTabelle(b, zerlegt[i][0])[daten[i]]);
      return out;
    },

    /** n-ter Handelstag (n ≥ 1) eines Monats; null, wenn es ihn nicht gibt. */
    nterHandelstag: function (j, m, n, boerse) {
      var b = boerseNormalisieren(boerse);
      jahrPruefen(j); ganzzahl(m, 'Monat'); ganzzahl(n, 'Position');
      if (m < 1 || m > 12) fehler('Monat außerhalb 1–12: ' + m);
      if (n < 1) fehler('Position muss ≥ 1 sein: ' + n);
      var tab = jahresTabelle(b, j);
      for (var t = 1; t <= monatsTage(j, m); t++) {
        var x = tab[iso(j, m, t)];
        if (x.offen && x.tdom === n) return iso(j, m, t);
      }
      return null;
    },

    /** n-ter Handelstag von hinten (1 = letzter) eines Monats; null, wenn es ihn nicht gibt. */
    letzterHandelstag: function (j, m, nVonHinten, boerse) {
      var b = boerseNormalisieren(boerse);
      jahrPruefen(j); ganzzahl(m, 'Monat'); ganzzahl(nVonHinten, 'Position');
      if (m < 1 || m > 12) fehler('Monat außerhalb 1–12: ' + m);
      if (nVonHinten < 1) fehler('Position muss ≥ 1 sein: ' + nVonHinten);
      var tab = jahresTabelle(b, j);
      for (var t = monatsTage(j, m); t >= 1; t--) {
        var x = tab[iso(j, m, t)];
        if (x.offen && x.tdom_rev === -nVonHinten) return iso(j, m, t);
      }
      return null;
    },

    /** n-ter Handelstag (n ≥ 1) eines Jahres; null, wenn es ihn nicht gibt. */
    nterHandelstagImJahr: function (j, n, boerse) {
      var b = boerseNormalisieren(boerse);
      jahrPruefen(j); ganzzahl(n, 'Position');
      if (n < 1) fehler('Position muss ≥ 1 sein: ' + n);
      var tab = jahresTabelle(b, j);
      for (var m = 1; m <= 12; m++) {
        for (var t = 1; t <= monatsTage(j, m); t++) {
          var x = tab[iso(j, m, t)];
          if (x.offen && x.tdoy === n) return iso(j, m, t);
        }
      }
      return null;
    },

    /** Erster Handelstag AB EINSCHLIESSLICH datum; über Jahresgrenzen; Datenende → Fehler. */
    naechsterHandelstag: function (datum, boerse) {
      var b = boerseNormalisieren(boerse), d = datumZerlegen(datum);
      var j = d[0], m = d[1], t = d[2];
      for (;;) {
        if (offen(b, j, m, t)) return iso(j, m, t);
        t++;
        if (t > monatsTage(j, m)) { t = 1; m++; }
        if (m > 12) { m = 1; j++; }
        if (j > DATEN.bis) fehler('Kein Handelstag bis zum Datenende ' + DATEN.bis + ' (ab ' + datum + ')');
      }
    },

    /** Schließtage eines Jahres als neue Liste 'YYYY-MM-DD' (wie Python get_holidays, sortiert). */
    schliessungen: function (j, boerse) {
      var b = boerseNormalisieren(boerse);
      jahrPruefen(j);
      var roh = (DATEN.schliessungen[b] || {})[String(j)] || '', out = [];
      for (var i = 0; i < roh.length; i += 4) out.push(j + '-' + roh.slice(i, i + 2) + '-' + roh.slice(i + 2, i + 4));
      return out;
    },

    /** 'belegt' | 'annahme' | 'ungeprueft' | 'konvention' — wie Python kalender_status. */
    status: function (boerse, j) {
      var b = boerseNormalisieren(boerse);
      ganzzahl(j, 'Jahr');
      var s = DATEN.status[b];
      for (var i = 0; i < s[1].length; i++) if (s[1][i][0] <= j && j <= s[1][i][1]) return s[1][i][2];
      return s[0];
    }
  };

  SA.boersenkalender = Object.freeze(API);
})(typeof window !== 'undefined' ? window : globalThis);

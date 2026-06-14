/**
 * SeasonAlpha — Holiday Calendar (Global Module)
 * ================================================
 * Exchange-spezifische Feiertags-Berechnung fuer alle Pages.
 *
 * Unterstuetzte Exchanges:
 *   NYSE   — 10 US-Feiertage (inkl. Karfreitag via Gauss-Algorithmus)
 *   XETRA  — 8 DE-Feiertage (inkl. Karfreitag + Ostermontag, Tag der Arbeit)
 *   LSE    — 8 UK-Feiertage (Bank Holidays)
 *   NONE   — Keine Feiertage (Crypto, Forex)
 *
 * Nutzung:
 *   SA.holidays.detect(ticker)          → 'NYSE' | 'XETRA' | 'LSE' | 'NONE'
 *   SA.holidays.get(year, exchange)     → ['2026-01-01', '2026-04-03', ...]
 *   SA.holidays.getMap(year, exchange)  → {'2026-01-01': true, ...}
 *   SA.holidays.isTradingDay(dateStr, exchange) → true/false
 *   SA.holidays.nthTradingDay(y, m, n, exchange) → '2026-05-04' (n-ter HT)
 *   SA.holidays.lastTradingDay(y, m, nFromEnd, exchange) → '2026-04-29'
 *   SA.holidays.nextTradingDay(y, m, d, exchange) → naechster HT ab Datum
 *   SA.holidays.easter(year)            → [month, day] Ostersonntag
 *   SA.holidays.goodFriday(year)        → 'YYYY-MM-DD'
 *   SA.holidays.thanksgiving(year)      → 'YYYY-MM-DD'
 *
 * Wird genutzt von: plain-vanilla.html, strategy-compute.js,
 *   monatswechsel.html, mondphasen.html, feiertags-page (geplant)
 */

var SA = window.SA || {};

SA.holidays = {

  // ── Helpers ──────────────────────────────────────────────────────────────

  _pad2: function(n) { return n < 10 ? '0' + n : '' + n; },
  _ds: function(y, m, d) { return y + '-' + this._pad2(m) + '-' + this._pad2(d); },

  /** N-ter Wochentag im Monat (z.B. 3. Montag = _nthDow(y, m, 1, 3)) */
  _nthDow: function(y, m, dow, n) {
    var first = new Date(y, m - 1, 1).getDay();
    var day = 1 + ((dow - first + 7) % 7) + (n - 1) * 7;
    return day;
  },

  /** Letzter bestimmter Wochentag im Monat */
  _lastDow: function(y, m, dow) {
    var lastDay = new Date(y, m, 0).getDate();
    var lastDow = new Date(y, m - 1, lastDay).getDay();
    return lastDay - ((lastDow - dow + 7) % 7);
  },

  // ── Ostern (Gauss-Algorithmus) ───────────────────────────────────────────

  /**
   * Ostersonntag berechnen (Gauss/Computus).
   * @returns {Array} [month, day] (1-basiert)
   */
  easter: function(y) {
    var a = y % 19, b = Math.floor(y / 100), c = y % 100;
    var d = Math.floor(b / 4), e = b % 4;
    var f = Math.floor((b + 8) / 25), g = Math.floor((b - f + 1) / 3);
    var h = (19 * a + b - d - g + 15) % 30;
    var i = Math.floor(c / 4), k = c % 4;
    var l = (32 + 2 * e + 2 * i - h - k) % 7;
    var m = Math.floor((a + 11 * h + 22 * l) / 451);
    var eMonth = Math.floor((h + l - 7 * m + 114) / 31);
    var eDay = ((h + l - 7 * m + 114) % 31) + 1;
    return [eMonth, eDay];
  },

  /** Karfreitag (Ostersonntag - 2) */
  goodFriday: function(y) {
    var e = this.easter(y);
    var dt = new Date(y, e[0] - 1, e[1]);
    dt.setDate(dt.getDate() - 2);
    return this._ds(dt.getFullYear(), dt.getMonth() + 1, dt.getDate());
  },

  /** Ostermontag (Ostersonntag + 1) */
  easterMonday: function(y) {
    var e = this.easter(y);
    var dt = new Date(y, e[0] - 1, e[1]);
    dt.setDate(dt.getDate() + 1);
    return this._ds(dt.getFullYear(), dt.getMonth() + 1, dt.getDate());
  },

  /** Pfingstmontag (Ostersonntag + 50) */
  whitMonday: function(y) {
    var e = this.easter(y);
    var dt = new Date(y, e[0] - 1, e[1]);
    dt.setDate(dt.getDate() + 50);
    return this._ds(dt.getFullYear(), dt.getMonth() + 1, dt.getDate());
  },

  /** Thanksgiving: 4. Donnerstag im November */
  thanksgiving: function(y) {
    return this._ds(y, 11, this._nthDow(y, 11, 4, 4));
  },

  // ── Exchange-spezifische Feiertage ───────────────────────────────────────

  /**
   * NYSE-Feiertage (10 Stueck, USA).
   * Neujahr, MLK Day, Presidents Day, Karfreitag, Memorial Day,
   * Juneteenth, Independence Day, Labor Day, Thanksgiving, Weihnachten.
   */
  _nyse: function(y) {
    return [
      this._ds(y, 1, 1),                                    // Neujahr
      this._ds(y, 1, this._nthDow(y, 1, 1, 3)),             // MLK Day: 3. Mo Jan
      this._ds(y, 2, this._nthDow(y, 2, 1, 3)),             // Presidents Day: 3. Mo Feb
      this.goodFriday(y),                                    // Karfreitag
      this._ds(y, 5, this._lastDow(y, 5, 1)),               // Memorial Day: letzter Mo Mai
      this._ds(y, 6, 19),                                   // Juneteenth
      this._ds(y, 7, 4),                                    // Independence Day
      this._ds(y, 9, this._nthDow(y, 9, 1, 1)),             // Labor Day: 1. Mo Sep
      this.thanksgiving(y),                                  // Thanksgiving: 4. Do Nov
      this._ds(y, 12, 25)                                   // Weihnachten
    ];
  },

  /**
   * XETRA-Feiertage (8 Stueck, Deutschland).
   * Neujahr, Karfreitag, Ostermontag, Tag der Arbeit,
   * Heiligabend, 1. Weihnachtstag, 2. Weihnachtstag, Silvester.
   */
  _xetra: function(y) {
    // Offizielle Xetra-Handelsfreitage (Deutsche Börse): NUR diese 8 Tage.
    // Xetra HANDELT an Pfingstmontag UND am 3. Oktober (Dt. Einheit)! Kein
    // Observed-Shift. (Muss mit shared/exchange_holidays.py::_compute_xetra_holidays
    // übereinstimmen.)
    return [
      this._ds(y, 1, 1),                                    // Neujahr
      this.goodFriday(y),                                    // Karfreitag
      this.easterMonday(y),                                  // Ostermontag
      this._ds(y, 5, 1),                                    // Tag der Arbeit
      this._ds(y, 12, 24),                                  // Heiligabend
      this._ds(y, 12, 25),                                  // 1. Weihnachtstag
      this._ds(y, 12, 26),                                  // 2. Weihnachtstag
      this._ds(y, 12, 31)                                   // Silvester
    ];
  },

  /**
   * LSE-Feiertage (8 Stueck, UK).
   * Neujahr, Karfreitag, Ostermontag, Early May Bank Holiday,
   * Spring Bank Holiday, Summer Bank Holiday, Weihnachten, Boxing Day.
   */
  _lse: function(y) {
    return [
      this._ds(y, 1, 1),                                    // Neujahr
      this.goodFriday(y),                                    // Karfreitag
      this.easterMonday(y),                                  // Ostermontag
      this._ds(y, 5, this._nthDow(y, 5, 1, 1)),             // Early May: 1. Mo Mai
      this._ds(y, 5, this._lastDow(y, 5, 1)),               // Spring: letzter Mo Mai
      this._ds(y, 8, this._lastDow(y, 8, 1)),               // Summer: letzter Mo Aug
      this._ds(y, 12, 25),                                  // Weihnachten
      this._ds(y, 12, 26)                                   // Boxing Day
    ];
  },

  // ── Public API ───────────────────────────────────────────────────────────

  /**
   * Exchange erkennen anhand des Tickers.
   * @param {string} ticker
   * @returns {string} 'NYSE' | 'XETRA' | 'LSE' | 'NONE'
   */
  detect: function(ticker) {
    if (!ticker) return 'NYSE';
    // Crypto → keine Feiertage
    if (/BTC|ETH|BNB|SOL|ADA|XRP|DOGE|DOT|AVAX|MATIC|LINK|UNI/i.test(ticker) && /USD/.test(ticker)) return 'NONE';
    // Forex → keine Feiertage (24/5)
    if (/=X$/.test(ticker)) return 'NONE';
    // DE: .DE Suffix oder deutsche Indizes
    if (/\.DE$/i.test(ticker) || /\^(GDAXI|SDAXI|MDAXI|TECDAX)/i.test(ticker)) return 'XETRA';
    // UK: .L Suffix oder FTSE
    if (/\.L$/i.test(ticker) || /\^FTSE/i.test(ticker)) return 'LSE';
    // Default: NYSE (US-Indizes, US-Aktien, Futures)
    return 'NYSE';
  },

  /**
   * Feiertage fuer ein Jahr + Exchange als Array.
   * @param {number} year
   * @param {string} exchange - 'NYSE' | 'XETRA' | 'LSE' | 'NONE'
   * @returns {Array<string>} Sortierte Liste von 'YYYY-MM-DD'
   */
  get: function(year, exchange) {
    exchange = exchange || 'NYSE';
    if (exchange === 'NONE') return [];
    if (exchange === 'XETRA') return this._xetra(year).sort();
    if (exchange === 'LSE') return this._lse(year).sort();
    return this._nyse(year).sort();
  },

  /**
   * Feiertage als Lookup-Map (schneller fuer isTradingDay).
   * @returns {Object} {'2026-01-01': true, ...}
   */
  getMap: function(year, exchange) {
    var list = this.get(year, exchange);
    var map = {};
    for (var i = 0; i < list.length; i++) map[list[i]] = true;
    return map;
  },

  /** Cache fuer getMap (vermeidet Neuberechnung) */
  _cache: {},
  _getCachedMap: function(year, exchange) {
    var key = year + '|' + exchange;
    if (!this._cache[key]) this._cache[key] = this.getMap(year, exchange);
    return this._cache[key];
  },

  /**
   * Ist ein Datum ein Handelstag? (Mo-Fr, kein Feiertag)
   * @param {string} dateStr - 'YYYY-MM-DD'
   * @param {string} exchange - 'NYSE' | 'XETRA' | 'LSE' | 'NONE'
   * @returns {boolean}
   */
  isTradingDay: function(dateStr, exchange) {
    if (exchange === 'NONE') return true; // Crypto: 24/7
    var d = new Date(dateStr.substring(0, 4) + '/' + dateStr.substring(5, 7) + '/' + dateStr.substring(8, 10));
    var dow = d.getDay();
    if (dow === 0 || dow === 6) return false;
    var year = parseInt(dateStr.substring(0, 4));
    var map = this._getCachedMap(year, exchange);
    return !map[dateStr];
  },

  /**
   * N-ter Handelstag eines Monats (1-basiert).
   * @returns {string|null} 'YYYY-MM-DD' oder null
   */
  nthTradingDay: function(y, m, n, exchange) {
    var count = 0;
    var lastDay = new Date(y, m, 0).getDate();
    for (var d = 1; d <= lastDay; d++) {
      var ds = this._ds(y, m, d);
      if (this.isTradingDay(ds, exchange)) {
        count++;
        if (count === n) return ds;
      }
    }
    return null;
  },

  /**
   * Letzter (oder n-ter von hinten) Handelstag eines Monats.
   * @param {number} nFromEnd - 1 = letzter, 2 = vorletzter, etc.
   * @returns {string|null}
   */
  lastTradingDay: function(y, m, nFromEnd, exchange) {
    nFromEnd = nFromEnd || 1;
    var lastDay = new Date(y, m, 0).getDate();
    var found = [];
    for (var d = 1; d <= lastDay; d++) {
      var ds = this._ds(y, m, d);
      if (this.isTradingDay(ds, exchange)) found.push(ds);
    }
    return found.length >= nFromEnd ? found[found.length - nFromEnd] : null;
  },

  /**
   * N-ter Handelstag eines Jahres (TDoY).
   * @param {number} y - Jahr
   * @param {number} n - TDoY-Nummer (1 = 1. HT des Jahres, ...)
   * @returns {string|null} 'YYYY-MM-DD'
   */
  nthTradingDayOfYear: function(y, n, exchange) {
    var count = 0;
    var dt = new Date(y, 0, 1);
    while (dt.getFullYear() === y) {
      var ds = this._ds(dt.getFullYear(), dt.getMonth() + 1, dt.getDate());
      if (this.isTradingDay(ds, exchange)) {
        count++;
        if (count === n) return ds;
      }
      dt.setDate(dt.getDate() + 1);
    }
    return null;
  },

  /**
   * Naechster Handelstag ab einem Datum.
   * @returns {string}
   */
  nextTradingDay: function(y, m, d, exchange) {
    for (var i = 0; i < 10; i++) {
      var dt = new Date(y, m - 1, d + i);
      var ds = this._ds(dt.getFullYear(), dt.getMonth() + 1, dt.getDate());
      if (this.isTradingDay(ds, exchange)) return ds;
    }
    return this._ds(y, m, d);
  }
};

window.SA = SA;

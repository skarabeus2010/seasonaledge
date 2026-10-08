/**
 * SeasonAlpha — Strategy Compute (Port von shared/strategies/plain_vanilla.py)
 * =============================================================================
 * 24 Plain Vanilla Saisonale Trading-Strategien.
 * Trade-Format: {entry_date, exit_date, entry_price, exit_price, return_pct}
 */

var SA = window.SA || {};

SA.strategy = {

  // ══════════════════════════════════════════════════════
  // HELPERS
  // ══════════════════════════════════════════════════════

  /** Index: date → position in rows (lazy, cached per ticker) */
  _dateIdx: null,
  _dateIdxTicker: null,

  _buildDateIdx: function(rows) {
    var idx = {};
    for (var i = 0; i < rows.length; i++) idx[rows[i].date] = i;
    return idx;
  },

  /** Alle Handelstage eines Monats als Indizes in rows */
  _getTradingDays: function(rows, year, month) {
    var yStr = String(year);
    var mStr = month < 10 ? '0' + month : String(month);
    var prefix = yStr + '-' + mStr;
    var result = [];
    for (var i = 0; i < rows.length; i++) {
      if (rows[i].date.substring(0, 7) === prefix) result.push(i);
    }
    return result;
  },

  // ── Datenrand und Bewertungsstichtag (Plan /plain-vanilla v5, E1/E2/E8) ───────────
  // Ein Regeltermin, der nicht als Kurszeile vorliegt, bekommt einen Zustandscode statt still die letzte Zeile:
  //   -1 fehlt (historisch, Verhalten wie bisher)
  //   -2 noch_nicht_faellig: Regeltermin liegt nach dem Bewertungsstichtag
  //   -3 kurs_ausstehend:   Regeltermin <= Stichtag, aber nach der letzten Kurszeile
  // Der Kalender (SA.holidays) wird nur am Datenrand und nur im geprüften Bereich 2000–2035 befragt
  // (Kalendervertrag JS = Python, scripts/verify_kalender_zwilling.py); historisch bleibt die Zeilenzählung.
  FEHLT: -1, NOCH_NICHT_FAELLIG: -2, KURS_AUSSTEHEND: -3,
  KALENDER_VON: 2000, KALENDER_BIS: 2035,
  _kontext: null,
  /** {stichtag:'YYYY-MM-DD', boerse:'NYSE'|'XETRA'|...}; ohne Kontext: Stichtag = letzte Kurszeile, NYSE */
  setKontext: function(k) { this._kontext = k || null; this._termine = {}; this._naechsterCode = -10; },
  _ctx: function(rows) {
    var k = this._kontext || {};
    var letzte = rows.length ? rows[rows.length - 1].date : null;
    return { stichtag: k.stichtag || letzte, boerse: k.boerse || 'NYSE', letzte: letzte };
  },
  /** Zustände tragen ihren Regeltermin (E8): jeder Zustand bekommt einen eindeutigen Code <= -10, der in
   *  _termine auf {code: -2|-3, datum} zeigt. Alle Vergleiche „< 0" bleiben gültig. */
  _termine: {},
  _naechsterCode: -10,
  _zustand: function(code, datum) {
    var id = this._naechsterCode--;
    this._termine[id] = { code: code, datum: datum };
    return id;
  },
  /** Grundcode (-1/-2/-3 oder Index) und Regeltermin eines Ergebnisses */
  _aufloesen: function(x) {
    var z = this._termine[x];
    return z ? z : { code: x, datum: null };
  },
  _zustandName: function(code) {
    code = this._aufloesen(code).code;
    return code === -2 ? 'noch_nicht_faellig' : code === -3 ? 'kurs_ausstehend' : code === -1 ? 'fehlt' : 'gefunden';
  },
  _imKalender: function(ds) {
    var y = parseInt(ds.slice(0, 4), 10);
    return y >= this.KALENDER_VON && y <= this.KALENDER_BIS;
  },
  /** Index der Kurszeile mit genau diesem Datum, sonst -1 */
  _exakt: function(rows, ds) {
    var lo = 0, hi = rows.length - 1;
    while (lo <= hi) {
      var mid = (lo + hi) >> 1;
      if (rows[mid].date === ds) return mid;
      if (rows[mid].date < ds) lo = mid + 1; else hi = mid - 1;
    }
    return -1;
  },
  /** Regeltermin (Datum einer Handelssitzung) → Index oder Zustandscode */
  _terminZustand: function(rows, ds) {
    if (ds == null) return -1;
    var c = this._ctx(rows);
    if (c.letzte && ds <= c.letzte) return this._exakt(rows, ds);
    return this._zustand(ds > c.stichtag ? -2 : -3, ds);
  },
  /** Ausstiegsfenster bis fensterEnde: noch nicht vorbei → Zustand (offen), vorbei → -1 */
  _fensterOffen: function(rows, fensterEnde) {
    var c = this._ctx(rows);
    if (!c.letzte || fensterEnde <= c.letzte) return -1;
    return this._zustand(fensterEnde > c.stichtag ? -2 : -3, fensterEnde);
  },

  /** Datum ± n Kalendertage (UTC, ohne Zeitzonenfalle) */
  _plusTage: function(ds, n) {
    var d = new Date(Date.UTC(+ds.slice(0, 4), +ds.slice(5, 7) - 1, +ds.slice(8, 10) + n));
    return d.toISOString().slice(0, 10);
  },
  /** Erste Kalender-Sitzung >= ds (richtung 1) bzw. <= ds (richtung -1) */
  _kalenderSitzung: function(ds, richtung, boerse) {
    for (var i = 0; i < 20; i++) {
      if (SA.holidays.isTradingDay(ds, boerse)) return ds;
      ds = this._plusTage(ds, richtung);
    }
    return null;
  },
  /** k Kalender-Sitzungen weiter (k < 0: zurück), ds muss eine Sitzung sein */
  _kalenderSchritt: function(ds, k, boerse) {
    var schritt = k < 0 ? -1 : 1;
    for (var n = Math.abs(k); n > 0; n--) {
      ds = this._plusTage(ds, schritt);
      ds = this._kalenderSitzung(ds, schritt, boerse);
      if (ds == null) return null;
    }
    return ds;
  },
  /** Sitzung mit Abstand k zu einem Bezugstermin: Basis = erste Sitzung >= datum ('nach') bzw. letzte <= datum
   *  ('vor'). Historisch wie bisher über die Kurszeilen; reicht Basis oder Ziel über den Datenrand, über den
   *  Kalender und Zustandscode. */
  _sitzung: function(rows, datum, k, richtung) {
    var c = this._ctx(rows);
    if (!c.letzte) return -1;
    if (datum <= c.letzte) {
      var basis = richtung === 'vor' ? this._nearestBackward(rows, datum) : this._nearestForward(rows, datum);
      if (basis < 0) return -1;
      var ziel = basis + k;
      if (ziel < 0) return -1;
      if (ziel < rows.length) return ziel;
      if (!this._imKalender(c.letzte)) return -1;
      return this._terminZustand(rows, this._kalenderSchritt(c.letzte, ziel - (rows.length - 1), c.boerse));
    }
    if (!this._imKalender(datum)) return -1;
    var b = this._kalenderSitzung(datum, richtung === 'vor' ? -1 : 1, c.boerse);
    return b == null ? -1 : this._terminZustand(rows, this._kalenderSchritt(b, k, c.boerse));
  },
  /** Zeile idx + k; hinter dem Datenrand über den Kalender (Zustandscode) */
  _offset: function(rows, idx, k) {
    if (idx < 0) return idx;
    if (idx + k < rows.length) return idx + k < 0 ? -1 : idx + k;
    var c = this._ctx(rows);
    if (!this._imKalender(c.letzte)) return -1;
    return this._terminZustand(rows, this._kalenderSchritt(c.letzte, idx + k - (rows.length - 1), c.boerse));
  },

  /** Monat liegt am oder hinter dem Datenrand (und im geprüften Kalenderbereich) */
  _amRand: function(rows, year, month) {
    var c = this._ctx(rows);
    if (!c.letzte) return false;
    var ym = year + '-' + this._pad2(month);
    return ym >= c.letzte.slice(0, 7) && this._imKalender(ym + '-01');
  },

  /** Alle Kalender-Sitzungen eines Monats (Börse aus dem Kontext) */
  _kalenderMonat: function(y, m) {
    var b = this._ctx([]).boerse, out = [], tage = new Date(y, m, 0).getDate();
    for (var d = 1; d <= tage; d++) {
      var ds = this._dateStr(y, m, d);
      if (SA.holidays.isTradingDay(ds, b)) out.push(ds);
    }
    return out;
  },

  /** Am Datenrand: Kalendertermin d. Liegt d schon in der Vergangenheit der Kurszeilen, bleibt das bisherige
   *  zeilenbasierte Ergebnis (E1: historisch keine neue Kalenderentscheidung, auch im letzten Datenmonat). */
  _randTermin: function(rows, d, zeilenbasiert) {
    var c = this._ctx(rows);
    if (d == null) return zeilenbasiert();
    if (d <= c.letzte) return zeilenbasiert();
    return this._terminZustand(rows, d);
  },

  _nthTradingDay: function(rows, year, month, n) {
    var self = this;
    var zeilen = function() { var days = self._getTradingDays(rows, year, month); return days.length >= n ? days[n - 1] : -1; };
    if (this._amRand(rows, year, month)) {
      return this._randTermin(rows, SA.holidays.nthTradingDay(year, month, n, this._ctx(rows).boerse), zeilen);
    }
    var days = this._getTradingDays(rows, year, month);
    return days.length >= n ? days[n - 1] : -1;
  },

  /** Letzter Handelstag des Monats. Am Datenrand aus dem Kalender — die letzte VORHANDENE Zeile eines laufenden
   *  Monats ist nicht sein letzter Handelstag (Befund 1). */
  _lastTradingDay: function(rows, year, month) {
    var self = this;
    var zeilen = function() { var days = self._getTradingDays(rows, year, month); return days.length > 0 ? days[days.length - 1] : -1; };
    if (this._amRand(rows, year, month)) {
      return this._randTermin(rows, SA.holidays.lastTradingDay(year, month, 1, this._ctx(rows).boerse), zeilen);
    }
    var days = this._getTradingDays(rows, year, month);
    return days.length > 0 ? days[days.length - 1] : -1;
  },

  _nthLastTradingDay: function(rows, year, month, n) {
    var self = this;
    var zeilen = function() { var days = self._getTradingDays(rows, year, month); return days.length >= n ? days[days.length - n] : -1; };
    if (this._amRand(rows, year, month)) {
      var b = this._ctx(rows).boerse, d = SA.holidays.lastTradingDay(year, month, n, b);
      // Zählt vom Monatsende: ist der Monat in den Kurszeilen noch nicht vollständig (letzte Monatssitzung nach der
      // letzten Zeile), ist die zeilenbasierte Zählung falsch — dann gilt der Kalendertermin (Codex Code-R2).
      var monatsEnde = SA.holidays.lastTradingDay(year, month, 1, b);
      if (d != null && monatsEnde != null && monatsEnde > this._ctx(rows).letzte) return this._terminZustand(rows, d);
      return this._randTermin(rows, d, zeilen);
    }
    var days = this._getTradingDays(rows, year, month);
    return days.length >= n ? days[days.length - n] : -1;
  },

  /** Naechster Handelstag >= target (binary search); hinter dem Datenrand über den Kalender (Zustandscode) */
  _nearestForward: function(rows, dateStr) {
    var c = this._ctx(rows);
    if (c.letzte && dateStr > c.letzte && this._imKalender(dateStr)) {
      return this._terminZustand(rows, this._kalenderSitzung(dateStr, 1, c.boerse));
    }
    var lo = 0, hi = rows.length - 1, best = -1;
    while (lo <= hi) {
      var mid = (lo + hi) >> 1;
      if (rows[mid].date >= dateStr) { best = mid; hi = mid - 1; }
      else lo = mid + 1;
    }
    return best;
  },

  /** Letzter Handelstag <= target; liegt target hinter dem Datenrand, entscheidet der Kalender, ob diese Sitzung
   *  schon stattgefunden hat (sonst würde die letzte vorhandene Zeile als Termin genommen — Befund 1). */
  _nearestBackward: function(rows, dateStr) {
    var c = this._ctx(rows);
    if (c.letzte && dateStr > c.letzte && this._imKalender(dateStr)) {
      var t = this._kalenderSitzung(dateStr, -1, c.boerse);
      if (t != null && t > c.letzte) return this._terminZustand(rows, t);
    }
    var lo = 0, hi = rows.length - 1, best = -1;
    while (lo <= hi) {
      var mid = (lo + hi) >> 1;
      if (rows[mid].date <= dateStr) { best = mid; lo = mid + 1; }
      else hi = mid - 1;
    }
    return best;
  },

  /** Ausschlussprotokoll eines Laufs (auswerten() setzt es; sonst wird nichts notiert) */
  _protokoll: null,
  _notiere: function(grund, datum) { if (this._protokoll) this._protokoll.push({ grund: grund, datum: datum || null }); },

  /** Trade aus Ein- und Ausstiegsindex bzw. Zustandscode (E2/E8):
   *  - Einstieg ohne Kurszeile (fehlt / noch nicht fällig / Kurs ausstehend) → kein Trade, protokolliert
   *  - Ausstieg noch nicht fällig oder Kurs ausstehend → offener Trade, bewertet zum letzten Kurs; ein Einstieg auf
   *    der letzten Zeile ergibt eine offene Position mit 0 %
   *  - Ausstieg historisch fehlend (-1) → kein Trade (vorher: still „offen" zum letzten Kurs) */
  _makeTrade: function(rows, entryIdx, exitIdx) {
    var ein = this._aufloesen(entryIdx), aus = this._aufloesen(exitIdx);
    if (ein.code < 0 || ein.code >= rows.length) {
      if (ein.code === -2 || ein.code === -3) this._notiere('einstieg_' + this._zustandName(entryIdx), ein.datum);
      return null;
    }
    entryIdx = ein.code;
    var open = false, zustand = 'gefunden', regeltermin = null;
    if (aus.code === -2 || aus.code === -3 || aus.code >= rows.length) {
      zustand = aus.code === -3 ? 'kurs_ausstehend' : 'noch_nicht_faellig';
      regeltermin = aus.datum;
      exitIdx = rows.length - 1;
      open = true;
    } else if (aus.code < 0) {
      this._notiere('ausstieg_fehlt', rows[entryIdx].date);
      return null;
    }
    if (exitIdx < entryIdx || (exitIdx === entryIdx && !open)) return null;
    var pe = rows[entryIdx].close, px = rows[exitIdx].close;
    // Nur endliche, positive Preise (Befund 10): parseFloat(null) = NaN lief sonst als Trade durch
    if (!(typeof pe === 'number' && isFinite(pe) && pe > 0 && typeof px === 'number' && isFinite(px) && px > 0)) {
      this._notiere('preis_ungueltig', rows[entryIdx].date);
      return null;
    }
    // Ungerundet speichern — gerundet wird erst in der Anzeige (Befund 10/9: 100 → 100,004 war sonst 0 %)
    var trade = {
      entry_date: rows[entryIdx].date, exit_date: rows[exitIdx].date,
      entry_price: pe, exit_price: px,
      return_pct: (px - pe) / pe * 100
    };
    // E8: Zustände, Regeltermin, Bewertungsstichtag und letztes Kursdatum am Trade
    var c = this._ctx(rows);
    trade.zustand_einstieg = 'gefunden';
    trade.zustand_ausstieg = zustand;
    trade.bewertungsstichtag = c.stichtag;
    trade.letzte_kurszeile = c.letzte;
    if (open) { trade.open = true; trade.regeltermin_ausstieg = regeltermin; }
    return trade;
  },

  /** Signal-only Version: gibt auch Entry/Exit zurueck wenn der andere fehlt */
  _makeSignalPair: function(rows, entryIdx, exitIdx) {
    var result = [];
    if (entryIdx >= 0 && entryIdx < rows.length) {
      result.push({ type: 'entry', date: rows[entryIdx].date, idx: entryIdx });
    }
    if (exitIdx >= 0 && exitIdx < rows.length) {
      result.push({ type: 'exit', date: rows[exitIdx].date, idx: exitIdx });
    }
    return result;
  },

  _pad2: function(n) { return n < 10 ? '0' + n : '' + n; },
  _dateStr: function(y, m, d) { return y + '-' + this._pad2(m) + '-' + this._pad2(d); },

  _getYears: function(rows) {
    var s = {};
    rows.forEach(function(r) { s[r.date.substring(0, 4)] = true; });
    return Object.keys(s).map(Number).sort(function(a, b) { return a - b; });
  },

  /** Praesidentenzyklus (1:1 Port) */
  _presidentialCycle: function(year) {
    var pos = ((year - 2024) % 4 + 4) % 4;
    if (pos === 0) return 4; // Election
    if (pos === 1) return 1; // Post-Election
    if (pos === 2) return 2; // Midterm
    return 3; // Pre-Election
  },

  /** Karfreitag — delegiert an SA.holidays */
  _goodFriday: function(y) { return SA.holidays.goodFriday(y); },

  /** NYSE-Feiertage — delegiert an SA.holidays */
  _nyseHolidays: function(y) {
    // Nur reguläre Feiertage: eine Sonderschließung (9/11, Staatstrauer) ist kein vorhersehbarer Handelsanlass —
    // 9/11 erzeugte sonst vier identische Trades (Codex Code-R1)
    var sonder = SA.holidays._NYSE_SONDER || [];
    return SA.holidays.get(y, 'NYSE').filter(function(d) { return sonder.indexOf(d) < 0; });
  },

  /** Thanksgiving — delegiert an SA.holidays */
  _thanksgiving: function(y) { return SA.holidays.thanksgiving(y); },

  /** Election Day: 1. Dienstag nach 1. Montag im November */
  _electionDay: function(year) {
    var nov1 = new Date(year, 10, 1);
    var dow = nov1.getDay();
    var firstMon = 1 + ((1 - dow + 7) % 7);
    return this._dateStr(year, 11, firstMon + 1);
  },

  // ══════════════════════════════════════════════════════
  // STRATEGIEN
  // ══════════════════════════════════════════════════════

  /** 1. Sell in May */
  calc_sell_in_may: function(rows) {
    var trades = [], years = this._getYears(rows);
    for (var i = 0; i < years.length; i++) {
      var entry = this._lastTradingDay(rows, years[i], 10);
      var exit = this._nthTradingDay(rows, years[i] + 1, 5, 3);
      var t = this._makeTrade(rows, entry, exit);
      if (t) trades.push(t);
    }
    return trades;
  },

  /** 3. Nasdaq-Trend (Nov-Jun) */
  calc_nasdaq_trend: function(rows) {
    var trades = [], years = this._getYears(rows);
    for (var i = 0; i < years.length; i++) {
      var entry = this._lastTradingDay(rows, years[i], 10);
      var exit = this._lastTradingDay(rows, years[i] + 1, 6);
      var t = this._makeTrade(rows, entry, exit);
      if (t) trades.push(t);
    }
    return trades;
  },

  /** 4. Month-End */
  calc_month_end: function(rows) {
    var trades = [], years = this._getYears(rows);
    for (var i = 0; i < years.length; i++) {
      for (var m = 1; m <= 12; m++) {
        var entry = this._nthLastTradingDay(rows, years[i], m, 2);
        var ny = m === 12 ? years[i] + 1 : years[i];
        var nm = m === 12 ? 1 : m + 1;
        var exit = this._nthTradingDay(rows, ny, nm, 4);
        var t = this._makeTrade(rows, entry, exit);
        if (t) trades.push(t);
      }
    }
    return trades;
  },

  /** 6. Santa Claus Rally */
  calc_santa_claus: function(rows) {
    var trades = [], years = this._getYears(rows);
    for (var i = 0; i < years.length; i++) {
      // Einstieg: dritte Handelssitzung STRENG vor Thanksgiving (Registry „3 HT vor Thanksgiving", Befund 6).
      // Basis = erste Sitzung >= Thanksgiving; drei davor sind die drei Sitzungen vor dem Feiertag — auch wenn
      // der Handelsplatz an Thanksgiving handelt oder die Sitzung davor kein Mittwoch ist.
      var thxDate = this._thanksgiving(years[i]);
      if (rows.length && thxDate < rows[0].date) continue;
      var entry = this._sitzung(rows, thxDate, -3, 'nach');
      var exit = this._nthTradingDay(rows, years[i] + 1, 1, 5);
      var t = this._makeTrade(rows, entry, exit);
      if (t) trades.push(t);
    }
    return trades;
  },

  /** 7. 212-Wochen-Zyklus */
  calc_212_week_cycle: function(rows) {
    var trades = [];
    var refMs = new Date(1938, 4, 16).getTime(); // 16. Mai 1938
    var cycleDays = 1484, holdDays = 182;
    var startMs = new Date(rows[0].date).getTime();
    var endMs = new Date(rows[rows.length - 1].date).getTime();
    var msPerDay = 86400000;

    var cur = refMs;
    while (cur < startMs) cur += cycleDays * msPerDay;
    while (cur < endMs) {
      var d = new Date(cur);
      var ds = this._dateStr(d.getFullYear(), d.getMonth() + 1, d.getDate());
      var entry = this._nearestForward(rows, ds);
      var exitDate = new Date(cur + holdDays * msPerDay);
      var es = this._dateStr(exitDate.getFullYear(), exitDate.getMonth() + 1, exitDate.getDate());
      var exit = this._nearestForward(rows, es);
      var t = this._makeTrade(rows, entry, exit);
      if (t) trades.push(t);
      cur += cycleDays * msPerDay;
    }
    return trades;
  },

  /** 8. 40-Wochen-Zyklus */
  calc_40_week_cycle: function(rows) {
    var trades = [];
    var refMs = new Date(1967, 3, 21).getTime(); // 21. Apr 1967
    var cycleDays = 280, holdDays = 140;
    var startMs = new Date(rows[0].date).getTime();
    var endMs = new Date(rows[rows.length - 1].date).getTime();
    var msPerDay = 86400000;

    var cur = refMs;
    while (cur < startMs) cur += cycleDays * msPerDay;
    while (cur < endMs) {
      var d = new Date(cur);
      var ds = this._dateStr(d.getFullYear(), d.getMonth() + 1, d.getDate());
      var entry = this._nearestForward(rows, ds);
      var exitDate = new Date(cur + holdDays * msPerDay);
      var es = this._dateStr(exitDate.getFullYear(), exitDate.getMonth() + 1, exitDate.getDate());
      var exit = this._nearestForward(rows, es);
      var t = this._makeTrade(rows, entry, exit);
      if (t) trades.push(t);
      cur += cycleDays * msPerDay;
    }
    return trades;
  },

  /** 9. Midterm Election */
  calc_midterm_election: function(rows) {
    var trades = [], years = this._getYears(rows), self = this;
    years.forEach(function(y) {
      if (self._presidentialCycle(y) !== 2) return;
      var elDate = self._electionDay(y);
      // 5 Sitzungen vor der letzten Sitzung <= Wahltag → 3 Sitzungen nach der ersten Sitzung >= Wahltag
      var entry = self._sitzung(rows, elDate, -5, 'vor');
      var exit = self._sitzung(rows, elDate, 3, 'nach');
      var t = self._makeTrade(rows, entry, exit);
      if (t) trades.push(t);
    });
    return trades;
  },

  /** 10. September-Vermeidung */
  calc_september_avoid: function(rows) {
    var trades = [], years = this._getYears(rows);
    for (var i = 0; i < years.length; i++) {
      var entry = this._nearestForward(rows, this._dateStr(years[i], 9, 30));
      var exit = this._nearestBackward(rows, this._dateStr(years[i] + 1, 8, 31));
      var t = this._makeTrade(rows, entry, exit);
      if (t) trades.push(t);
    }
    return trades;
  },

  /** 14. First Five Days of January */
  calc_first_five_days: function(rows) {
    var trades = [], years = this._getYears(rows);
    for (var i = 0; i < years.length; i++) {
      var jan = this._getTradingDays(rows, years[i], 1);
      if (jan.length < 5) continue;
      if (rows[jan[4]].close > rows[jan[0]].close) {
        var entry = this._nthTradingDay(rows, years[i], 2, 1);
        var exit = this._lastTradingDay(rows, years[i], 12);
        var t = this._makeTrade(rows, entry, exit);
        if (t) trades.push(t);
      }
    }
    return trades;
  },

  /** 15. Last Five Days of January */
  calc_last_five_days: function(rows) {
    var trades = [], years = this._getYears(rows);
    for (var i = 0; i < years.length; i++) {
      var jan = this._getTradingDays(rows, years[i], 1);
      if (jan.length < 5) continue;
      if (rows[jan[jan.length - 1]].close > rows[jan[jan.length - 5]].close) {
        var entry = this._nthTradingDay(rows, years[i], 2, 1);
        var exit = this._lastTradingDay(rows, years[i], 12);
        var t = this._makeTrade(rows, entry, exit);
        if (t) trades.push(t);
      }
    }
    return trades;
  },

  /** 16. Januar-Barometer */
  calc_january_barometer: function(rows) {
    var trades = [], years = this._getYears(rows);
    for (var i = 0; i < years.length; i++) {
      var jan = this._getTradingDays(rows, years[i], 1);
      if (jan.length < 10) continue;
      if (rows[jan[jan.length - 1]].close > rows[jan[0]].close) {
        var entry = this._nthTradingDay(rows, years[i], 2, 1);
        var exit = this._lastTradingDay(rows, years[i], 12);
        var t = this._makeTrade(rows, entry, exit);
        if (t) trades.push(t);
      }
    }
    return trades;
  },

  /** 17. Ein-Tages-Feiertag (NYSE-Feiertage, dynamisch berechnet) */
  calc_one_day_holiday: function(rows) {
    var trades = [], years = this._getYears(rows), self = this;
    years.forEach(function(y) {
      var hols = self._nyseHolidays(y);
      hols.forEach(function(holDate) {
        var t = self._makeTrade(rows, self._sitzung(rows, holDate, -2, 'nach'), self._sitzung(rows, holDate, -1, 'nach'));
        if (t) trades.push(t);
      });
    });
    return trades;
  },

  /** 18. UHTS (Ultimate Holiday Trading System, NYSE-Feiertage) */
  calc_uhts: function(rows) {
    var trades = [], years = this._getYears(rows), self = this;
    years.forEach(function(y) {
      self._nyseHolidays(y).forEach(function(F) {
        // Plan 1B T2: Einstieg S⁻3 (3. Sitzung vor F), Ausstieg S⁺3 (3. Sitzung strikt NACH F). 1A rechnete
        // _sitzung(F, 3) mit Basis >= F und landete bei geschlossenem F auf S⁺4 (Codex Plan-R1).
        var t = self._makeTrade(rows, self._sitzung(rows, F, -3, 'nach'), self._sitzung(rows, self._plusTage(F, 1), 2, 'nach'));
        if (!t) return;
        // T3: Aufstockung auf 2x zum Schluss von S⁻1 (letzte Sitzung vor F)
        var s1 = self._aufloesen(self._sitzung(rows, F, -1, 'nach'));
        var aufstock = (s1.code >= 0 && s1.code < rows.length) ? rows[s1.code].date : s1.datum;
        if (self._hebelPfad(rows, t, aufstock)) trades.push(t);
      });
    });
    return trades;
  },

  /** Gehebelter Pfad eines Trades (Plan 1B T3): je Kursintervall a → b gilt der Hebel NACH dem Schluss von a —
   *  1x solange a vor der Aufstockung liegt, sonst 2x; Rendite = Π(1 + h·(b/a − 1)). Tägliches Rebalancing, keine
   *  Finanzierungskosten. Über eine Kurslücke wird das beobachtete Intervall einmal bewertet (Näherung, L/V1).
   *  Setzt return_pct, leverage = 2, hebel = [[datum_b, h], …], aufstockung. false bei ungültigem Kurs im Pfad. */
  _hebelPfad: function(rows, t, aufstock) {
    var i0 = this._exakt(rows, t.entry_date), i1 = this._exakt(rows, t.exit_date);
    if (i0 < 0 || i1 < i0) return false;
    var f = 1, hebel = [];
    for (var i = i0 + 1; i <= i1; i++) {
      var a = rows[i - 1].close, b = rows[i].close;
      if (!(typeof a === 'number' && isFinite(a) && a > 0 && typeof b === 'number' && isFinite(b) && b > 0)) {
        this._notiere('preis_ungueltig', rows[i].date);
        return false;
      }
      var h = (aufstock != null && rows[i - 1].date >= aufstock) ? 2 : 1;
      f *= 1 + h * (b / a - 1);
      hebel.push([rows[i].date, h]);
    }
    t.return_pct = (f - 1) * 100;
    t.leverage = 2;
    t.hebel = hebel;
    t.aufstockung = aufstock;
    return true;
  },

  /** 19. Nach-Weihnachten bis Silvester */
  calc_post_christmas: function(rows) {
    var trades = [], years = this._getYears(rows);
    for (var i = 0; i < years.length; i++) {
      var entry = this._nearestForward(rows, this._dateStr(years[i], 12, 26));
      var exit = this._lastTradingDay(rows, years[i], 12);
      var t = this._makeTrade(rows, entry, exit);
      if (t) trades.push(t);
    }
    return trades;
  },

  /** 20. Zweiter Handelstag */
  calc_second_trading_day: function(rows) {
    var trades = [], years = this._getYears(rows);
    for (var i = 0; i < years.length; i++) {
      for (var m = 1; m <= 12; m++) {
        var entry = this._nthTradingDay(rows, years[i], m, 1);
        var exit = this._nthTradingDay(rows, years[i], m, 2);
        var t = this._makeTrade(rows, entry, exit);
        if (t) trades.push(t);
      }
    }
    return trades;
  },

  /** 21. Mid-Decade Rallye */
  calc_mid_decade: function(rows) {
    var trades = [], years = this._getYears(rows);
    for (var i = 0; i < years.length; i++) {
      if (years[i] % 10 !== 4) continue;
      var entry = this._nearestForward(rows, this._dateStr(years[i], 9, 30));
      var exit = this._nearestBackward(rows, this._dateStr(years[i] + 2, 3, 31));
      var t = this._makeTrade(rows, entry, exit);
      if (t) trades.push(t);
    }
    return trades;
  },

  /** 22. 20-Jahres-Zyklus */
  calc_20_year_cycle: function(rows) {
    var trades = [], years = this._getYears(rows);
    for (var i = 0; i < years.length; i++) {
      var y = years[i];
      if (y % 10 !== 2 || Math.floor(y / 10) % 2 !== 0) continue;
      var entry = this._nearestForward(rows, this._dateStr(y, 9, 30));
      var exit = this._nearestBackward(rows, this._dateStr(y + 3, 12, 31));
      var t = this._makeTrade(rows, entry, exit);
      if (t) trades.push(t);
    }
    return trades;
  },

  /** 23. Wahljahr letzte 7 Monate */
  calc_election_year_7months: function(rows) {
    var trades = [], years = this._getYears(rows), self = this;
    years.forEach(function(y) {
      if (self._presidentialCycle(y) !== 4) return;
      var entry = self._nearestForward(rows, self._dateStr(y, 5, 31));
      var exit = self._lastTradingDay(rows, y, 12);
      var t = self._makeTrade(rows, entry, exit);
      if (t) trades.push(t);
    });
    return trades;
  },

  /** 24. UECS (Ultimate Election Cycle System) */
  calc_uecs: function(rows) {
    var trades = [], years = this._getYears(rows), self = this;
    years.forEach(function(y) {
      var cycle = self._presidentialCycle(y);
      // Phase 1: Midterm 5 HT vor bis 3 HT nach
      if (cycle === 2) {
        var elDate = self._electionDay(y);
        var t1 = self._makeTrade(rows, self._sitzung(rows, elDate, -5, 'vor'), self._sitzung(rows, elDate, 3, 'nach'));
        if (t1) trades.push(t1);
      }
      // Phase 2: Mar-Jul Vorwahljahr
      if (cycle === 3) {
        var t2 = self._makeTrade(rows, self._nthTradingDay(rows, y, 3, 1), self._lastTradingDay(rows, y, 7));
        if (t2) trades.push(t2);
      }
      // Phase 3: Okt Midterm bis Sep Vorwahljahr
      if (cycle === 2) {
        var t3 = self._makeTrade(rows, self._nthTradingDay(rows, y, 10, 1), self._lastTradingDay(rows, y + 1, 9));
        if (t3) trades.push(t3);
      }
      // Phase 4: Nov-Dez Vorwahljahr
      if (cycle === 3) {
        var t4 = self._makeTrade(rows, self._nthTradingDay(rows, y, 11, 1), self._lastTradingDay(rows, y, 12));
        if (t4) trades.push(t4);
      }
      // Phase 5: Jun-Dez Wahljahr
      if (cycle === 4) {
        var t5 = self._makeTrade(rows, self._nthTradingDay(rows, y, 6, 1), self._lastTradingDay(rows, y, 12));
        if (t5) trades.push(t5);
      }
      // Phase 6: Post-Election auf "5" endend
      if (cycle === 1 && y % 10 === 5) {
        var t6 = self._makeTrade(rows, self._nthTradingDay(rows, y, 1, 1), self._lastTradingDay(rows, y, 12));
        if (t6) trades.push(t6);
      }
    });
    // Ueberlappungen mergen
    trades.sort(function(a, b) { return a.entry_date < b.entry_date ? -1 : 1; });
    var cleaned = [];
    trades.forEach(function(t) {
      if (cleaned.length && t.entry_date < cleaned[cleaned.length - 1].exit_date) {
        var last = cleaned[cleaned.length - 1];
        if (t.exit_date > last.exit_date) {
          last.exit_date = t.exit_date;
          last.exit_price = t.exit_price;
          last.return_pct = (last.exit_price - last.entry_price) / last.entry_price * 100;
          if (t.open) { last.open = true; last.zustand_ausstieg = t.zustand_ausstieg; }
        }
      } else cleaned.push(t);
    });
    return cleaned;
  },

  /** 5. Monthly 10 (TDOM 1-4, 9-12, letzte 2) */
  calc_monthly_10: function(rows) {
    var trades = [], years = this._getYears(rows), self = this;
    years.forEach(function(y) {
      for (var m = 1; m <= 12; m++) {
        // Laufender Monat (Datenrand): Sitzungen aus dem Kalender, nicht aus den schon vorhandenen Zeilen —
        // sonst wären „die letzten zwei" Sitzungen die letzten zwei BISHER gehandelten (Plan v5, E2).
        var days = self._getTradingDays(rows, y, m);
        if (self._amRand(rows, y, m)) {
          var letzte = self._ctx(rows).letzte;
          days = days.concat(self._kalenderMonat(y, m).filter(function(d) { return d > letzte; })
                             .map(function(d) { return self._terminZustand(rows, d); }));
        }
        // continue, NICHT return: `return` verlaesst den forEach-Callback und damit
        // das GANZE Jahr. Ein angebrochener erster Monat (Datenreihe startet
        // Monatsmitte) loeschte so alle uebrigen 11 Monate dieses Jahres aus dem
        // Backtest. Die Python-Referenz (etf_seasonal_scan.py::S_monthly_10) nutzt
        // continue, ebenso die Geschwister in dieser Datei (Z. 287/303/319).
        if (days.length < 10) continue;
        var maxTdom = days.length;
        // Aktive TDOMs
        var active = {};
        for (var d = 1; d <= 4; d++) active[d] = true;
        for (var d = 9; d <= 12; d++) active[d] = true;
        active[maxTdom] = true;
        active[maxTdom - 1] = true;
        // Bloecke
        var sorted = Object.keys(active).map(Number).sort(function(a, b) { return a - b; });
        var blockStart = sorted[0], prev = sorted[0];
        for (var k = 1; k < sorted.length; k++) {
          if (sorted[k] !== prev + 1) {
            var t = self._makeTrade(rows, days[blockStart - 1], days[prev - 1]);
            if (t) trades.push(t);
            blockStart = sorted[k];
          }
          prev = sorted[k];
        }
        var t = self._makeTrade(rows, days[blockStart - 1], days[prev - 1]);
        if (t) trades.push(t);
      }
    });
    return trades;
  },

  /** 2. LBR November-Mai: Einstieg ab 1. Okt am ersten Tag i mit LBR-Histogramm(i-1) > 0, Ausstieg ab 1. Apr am
   *  ersten Tag i mit Histogramm(i-1) < 0, ausgeführt jeweils zum Close von i. Die Entscheidung nutzt nur den
   *  Vortag (Befund 3, Plan /plain-vanilla v5): am Ausführungstag ist dessen Schlusskurs noch nicht bekannt. */
  calc_lbr_november_mai: function(rows) {
    // Kein stiller Rückfall (Befund N1): ohne Indikatormodul wäre das Ergebnis Sell in May unter falschem Namen.
    if (!SA.indicators || !SA.indicators.calcMACD) throw new Error('LBR: SA.indicators.calcMACD fehlt (indicators.js nicht geladen)');
    var closes = rows.map(function(r) { return r.close; });
    var macd = SA.indicators.calcMACD(closes, 3, 10, 16);
    var hist = macd.histogram;
    var gueltig = function(v) { return typeof v === 'number' && isFinite(v); };
    var trades = [], years = this._getYears(rows), self = this;
    years.forEach(function(y) {
      var octStart = self._nearestForward(rows, self._dateStr(y, 10, 1));
      if (octStart < 0) return;
      var entry = -1;
      for (var i = Math.max(octStart, 1); i < rows.length; i++) {
        if (rows[i].date > self._dateStr(y + 1, 3, 31)) break;
        if (gueltig(hist[i - 1]) && hist[i - 1] > 0) { entry = i; break; }
      }
      if (entry < 0) return;
      var aprStart = self._nearestForward(rows, self._dateStr(y + 1, 4, 1));
      var fensterEnde = self._dateStr(y + 1, 6, 30);
      var exit = -1;
      if (aprStart >= 0) {
        for (var i = Math.max(aprStart, 1); i < rows.length; i++) {
          if (rows[i].date > fensterEnde) break;
          if (gueltig(hist[i - 1]) && hist[i - 1] < 0) { exit = i; break; }
        }
      }
      if (exit < 0) {
        // Einstieg erfolgt, kein Ausstieg beobachtet: offen, solange das Ausstiegsfenster nicht vorbei ist
        exit = self._fensterOffen(rows, fensterEnde);
        if (exit === -1) return;   // Fenster vorbei ohne Signal → kein Trade (wie bisher)
      }
      var t = self._makeTrade(rows, entry, exit);
      if (t) trades.push(t);
    });
    return trades;
  },

  // ══════════════════════════════════════════════════════
  // PORTFOLIO & STATISTIK
  // ══════════════════════════════════════════════════════

  /** Equity-Kurve aus Trades */
  buildEquityCurve: function(trades, startCapital) {
    startCapital = startCapital || 1000;
    if (!trades || !trades.length) return [];
    // Offene Trades fliessen NICHT in die Equity-Kurve ein (mark-to-market wuerde verzerren)
    var closed = trades.filter(function(t) { return !t.open; });
    if (!closed.length) return [];
    var sorted = closed.slice().sort(function(a, b) { return a.entry_date < b.entry_date ? -1 : 1; });
    var equity = startCapital;
    var curve = [{ date: sorted[0].entry_date, value: equity }];
    sorted.forEach(function(t) {
      equity *= (1 + t.return_pct / 100);
      curve.push({ date: t.exit_date, value: Math.round(equity * 100) / 100 });
    });
    return curve;
  },

  // ══════════════════════════════════════════════════════
  // GEMEINSAME AUSWERTUNG (Plan /plain-vanilla v5, E7/E9) — Kennzahlen, Signalansicht und Dashboard rufen nur das
  // ══════════════════════════════════════════════════════

  /** Heutiges Datum in der Zeitzone der Börse (Bewertungsstichtag der Seite) */
  heute: function(boerse) {
    var tz = boerse === 'XETRA' ? 'Europe/Berlin' : boerse === 'LSE' ? 'Europe/London' : 'America/New_York';
    try { return new Intl.DateTimeFormat('en-CA', { timeZone: tz, year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date()); }
    catch (e) { var d = new Date(); return this._dateStr(d.getFullYear(), d.getMonth() + 1, d.getDate()); }
  },

  /** Datenbestand veraltet: mehr als 10 Handelssitzungen zwischen letzter Kurszeile und Stichtag (E1) */
  _datenVeraltet: function(rows) {
    var c = this._ctx(rows);
    if (!c.letzte || c.stichtag <= c.letzte || !this._imKalender(c.letzte)) return false;
    var n = 0, ds = c.letzte;
    while (n <= 10) {
      ds = this._kalenderSitzung(this._plusTage(ds, 1), 1, c.boerse);
      if (ds == null || ds > c.stichtag) return false;
      n++;
    }
    return true;
  },

  /** Strategie rechnen → Stop anwenden → offene Trades eines veralteten Datenbestands herausnehmen → Kennzahlen +
   *  Streak. Reihenfolge verbindlich (E7): ein durch den Stop geschlossener Trade bleibt realisiert; erst danach
   *  fallen verbliebene offene Kandidaten bei veraltetem Bestand aus der Darstellung (in `unvollstaendig`).
   *  opts: {stichtag, boerse, stop: {typ:'fixed'|'trailing', pct}} — der Zeitraum wird über `rows` gewählt. */
  auswerten: function(rows, key, opts) {
    opts = opts || {};
    var s = SA.STRATEGIES && SA.STRATEGIES[key];
    if (!s || !this[s.func]) return null;
    var protokoll = [];
    this._protokoll = protokoll;
    this.setKontext({ stichtag: opts.stichtag, boerse: opts.boerse });
    try {
      var trades = this[s.func](rows) || [];
      if (opts.stop && opts.stop.pct > 0) {
        trades = opts.stop.typ === 'trailing' ? this.applyTrailingStop(rows, trades, opts.stop.pct)
                                              : this.applyStopLoss(rows, trades, opts.stop.pct);
      }
      this._lueckenMarkieren(rows, trades);   // nach dem Stop: Lücken bis zum tatsächlichen Ausstieg (S2)
      var veraltet = this._datenVeraltet(rows), unvollstaendig = [];
      if (veraltet) {
        unvollstaendig = trades.filter(function(t) { return t.open; });
        trades = trades.filter(function(t) { return !t.open; });
        unvollstaendig.forEach(function(t) { protokoll.push({ grund: 'datenbestand_veraltet', datum: t.entry_date }); });
      }
      var stats = this.computeStats(trades);
      if (stats) {
        // Ergebnisvertrag 1B/E2: alte Schlüssel behalten ihre trade-basierte Bedeutung, Tageswerte nur unter taeglich
        var tgInfo = {};
        stats.taeglich = this.tagesEquity(rows, trades, 1000, tgInfo);
        stats.taeglich_grund = tgInfo.grund || null;
        var zu = trades.filter(function(t) { return !t.open; });
        stats.luecken = { von: zu.length,
          fehlende: zu.filter(function(t) { return t.fehlende_sitzungen > 0; }).length,
          abstand: zu.filter(function(t) { return t.auffaellige_abstaende > 0; }).length,
          naeherung: zu.filter(function(t) { return t.naeherung; }).length };
      }
      return { trades: trades, stats: stats, streak: this.streak(trades),
               unvollstaendig: unvollstaendig, veraltet: veraltet, protokoll: protokoll };
    } finally {
      this._protokoll = null;
      this.setKontext(null);
    }
  },

  /** Serie gleicher Vorzeichen am Ende der GESCHLOSSENEN Trades (offene zählen nicht, Befund 13) */
  streak: function(trades) {
    var zu = (trades || []).filter(function(t) { return !t.open && typeof t.return_pct === 'number' && isFinite(t.return_pct); })
      .sort(function(a, b) { return a.exit_date < b.exit_date ? -1 : a.exit_date > b.exit_date ? 1 : 0; });
    if (!zu.length) return { typ: null, n: 0 };
    var typ = zu[zu.length - 1].return_pct > 0 ? 'gewinn' : 'verlust', n = 0;
    for (var i = zu.length - 1; i >= 0; i--) {
      if ((zu[i].return_pct > 0) === (typ === 'gewinn')) n++; else break;
    }
    return { typ: typ, n: n };
  },

  /** Kalendertermine der nächsten Regeltermine (Dashboard). Vereinfachte Terminliste ohne Bedingungen — die
   *  regelgetreue Ableitung bedingter Strategien folgt in Phase 2. heute: 'YYYY-MM-DD'. */
  regeltermine: function(heute, boerse) {
    var H = SA.holidays, ex = (!boerse || boerse === 'NONE') ? 'NYSE' : boerse, self = this;
    var Y = parseInt(heute.slice(0, 4), 10), M = parseInt(heute.slice(5, 7), 10), out = [];
    function add(key, type, date) { if (date) out.push({ key: key, type: type, date: date }); }
    function last(y, m, n) { return H.lastTradingDay(y, m, n || 1, ex); }
    function nth(y, m, n) { return H.nthTradingDay(y, m, n, ex); }
    function fwd(y, m, d) { return H.nextTradingDay(y, m, d, ex); }
    [Y, Y + 1].forEach(function(y) {
      add('sell_in_may', 'entry', last(y, 10));
      add('sell_in_may', 'exit', nth(y, 5, 3));   // 3. Handelstag Mai (war 3*5 = 15., Befund 5)
      add('first_five_days', 'entry', nth(y, 1, 1));
      add('first_five_days', 'exit', nth(y, 1, 5));
      add('last_five_days', 'entry', last(y, 1, 5));
      add('last_five_days', 'exit', last(y, 1));
      add('january_barometer', 'entry', nth(y, 2, 1));
      add('january_barometer', 'exit', last(y, 12));
      if (boerse !== 'NONE') {   // wie bisher im Dashboard: Feiertagsstrategien nur mit Börsenkalender
        add('santa_claus', 'exit', nth(y, 1, 5));
        add('post_christmas', 'entry', fwd(y, 12, 26));
        add('post_christmas', 'exit', last(y, 12));
      }
    });
    add('lbr_november_mai', 'entry', last(Y, 10));
    add('lbr_november_mai', 'exit', last(Y, 4));
    add('nasdaq_trend', 'entry', last(Y, 10));
    add('nasdaq_trend', 'exit', last(Y, 6));
    add('september_avoid', 'entry', fwd(Y, 9, 30));
    add('september_avoid', 'exit', last(Y, 8));
    if (Y % 4 === 0 || (Y + 1) % 4 === 0) {
      var ey = Y % 4 === 0 ? Y : Y + 1;
      add('election_7months', 'entry', fwd(ey, 5, 31));
      add('election_7months', 'exit', last(ey, 12));
    }
    if (boerse !== 'NONE') {
      // Santa Claus: drei Sitzungen streng vor Thanksgiving (wie calc_santa_claus)
      var b = self._kalenderSitzung(H.thanksgiving(Y), 1, ex);
      add('santa_claus', 'entry', b && self._kalenderSchritt(b, -3, ex));
    }
    for (var mi = 0; mi < 3; mi++) {
      var fm = M + mi, mm = ((fm - 1) % 12) + 1, yy = Y + Math.floor((fm - 1) / 12);
      var nm = mm === 12 ? 1 : mm + 1, ny = mm === 12 ? yy + 1 : yy;
      add('month_end', 'entry', last(yy, mm, 2));
      add('month_end', 'exit', nth(ny, nm, 4));
      add('second_trading_day', 'entry', nth(yy, mm, 1));
      add('second_trading_day', 'exit', nth(yy, mm, 2));
      add('monthly_10', 'entry', nth(yy, mm, 1));
      add('monthly_10', 'exit', nth(yy, mm, 4));
      add('downmonth_tom', 'entry', nth(yy, mm, 14));
      add('downmonth_tom', 'exit', nth(ny, nm, 5));
    }
    return out;
  },

  /** Mindestzahl geschlossener Trades für eine Sharpe-Ratio */
  MIN_TRADES_SHARPE: 5,

  /** Zahl mit festen Nachkommastellen, nicht definiert → „—" */
  formatZahl: function(v, stellen) { return (typeof v === 'number' && isFinite(v)) ? v.toFixed(stellen) : '\u2014'; },

  /** Anzeige des Profit-Faktors: nicht definiert (kein Verlusttrade) → „—", nie „∞" (Befund 10) */
  formatPF: function(pf) { return (typeof pf === 'number' && isFinite(pf)) ? pf.toFixed(2) : '—'; },

  /** KPI-Statistiken */
  computeStats: function(trades, startCapital) {
    startCapital = startCapital || 1000;
    if (!trades || !trades.length) return null;
    // Offene Trades aus Statistik ausschliessen (CAGR/Sharpe/PF nur fuer geschlossene Trades)
    trades = trades.filter(function(t) { return !t.open && typeof t.return_pct === 'number' && isFinite(t.return_pct); });
    if (!trades.length) return null;
    var returns = trades.map(function(t) { return t.return_pct; });
    var n = returns.length;
    var wins = returns.filter(function(r) { return r > 0; }).length;
    var sum = returns.reduce(function(s, v) { return s + v; }, 0);
    var avg = sum / n;

    // Equity + Max DD
    var equity = [startCapital];
    returns.forEach(function(r) { equity.push(equity[equity.length - 1] * (1 + r / 100)); });
    var final = equity[equity.length - 1];
    var peak = equity[0], maxDD = 0;
    equity.forEach(function(v) {
      if (v > peak) peak = v;
      var dd = (v - peak) / peak * 100;
      if (dd < maxDD) maxDD = dd;
    });

    // CAGR
    var firstDate = new Date(trades[0].entry_date);
    var lastDate = new Date(trades[trades.length - 1].exit_date);
    var yearsSpan = (lastDate - firstDate) / (365.25 * 86400000);
    var cagr = yearsSpan > 0 ? (Math.pow(final / startCapital, 1 / yearsSpan) - 1) * 100 : 0;

    // Sharpe
    var stdRet = Math.sqrt(returns.reduce(function(s, v) { return s + (v - avg) * (v - avg); }, 0) / n);
    var tradesPerYear = yearsSpan > 0 ? n / yearsSpan : 1;
    // Unter MIN_TRADES_SHARPE geschlossenen Trades ist die Streuung keine Schätzung, sondern Zufall: zwei Trades mit
    // 11,847 % und 11,845 % ergaben Sharpe 6855 (gerundet vorher 0). Dann null, Anzeige „—".
    var sharpe = (n >= this.MIN_TRADES_SHARPE && stdRet > 0) ? (avg / stdRet) * Math.sqrt(tradesPerYear) : null;

    // Profit Factor
    var grossProfit = returns.filter(function(r) { return r > 0; }).reduce(function(s, v) { return s + v; }, 0);
    var grossLoss = Math.abs(returns.filter(function(r) { return r < 0; }).reduce(function(s, v) { return s + v; }, 0));

    return {
      total_return: Math.round((final / startCapital - 1) * 1000) / 10,
      cagr: Math.round(cagr * 100) / 100,
      max_drawdown: Math.round(maxDD * 10) / 10,
      win_rate: Math.round(wins / n * 1000) / 10,
      n_trades: n,
      avg_return: Math.round(avg * 100) / 100,
      sharpe: sharpe == null ? null : Math.round(sharpe * 100) / 100,
      final_equity: Math.round(final * 100) / 100,
      years_span: Math.round(yearsSpan * 10) / 10,
      // Ohne Verlusttrade ist der Profit-Faktor nicht definiert (auch 0/0) → null, Anzeige „—" (Befund 10)
      profit_factor: grossLoss > 0 ? Math.round(grossProfit / grossLoss * 100) / 100 : null
    };
  },

  /** Gestoppten Trade zum Close der Zeile i schliessen. Close-Modus der Seite (Plan v5, E4/E5): Auslösung am
   *  Close, Ausführung am Close — nicht am Stopniveau, das an einem Gap-Tag gar nicht handelbar war (Befund 2).
   *  Alle Metadaten bleiben erhalten (Hebel!), der Trade ist danach geschlossen, auch wenn er offen war;
   *  Rendite (Plan 1B S2/V3): mit Hebelpfad der bis zum Stop-Tag gekürzte Pfad; Hebel ohne Pfad → Kursrendite ×
   *  leverage (Ersatzrechnung, die Tageskurve ist dann null); sonst Kursrendite. */
  _stopAusstieg: function(t, rows, i) {
    var c = rows[i].close, neu = {};
    for (var k in t) if (Object.prototype.hasOwnProperty.call(t, k)) neu[k] = t[k];
    delete neu.open; delete neu.regeltermin_ausstieg;
    neu.zustand_ausstieg = 'gefunden';
    neu.exit_date = rows[i].date;
    neu.exit_price = c;
    if (t.hebel) this._hebelPfad(rows, neu, t.aufstockung);
    else neu.return_pct = (c / t.entry_price - 1) * 100 * (t.leverage || 1);
    neu.stopped = true;
    return neu;
  },

  /** Hat der Trade irgendwo einen Hebel ≠ 1? (Regelpfad oder leverage ohne Pfad) */
  _gehebelt: function(t) {
    if (t.hebel) { for (var i = 0; i < t.hebel.length; i++) if (t.hebel[i][1] !== 1) return true; return false; }
    return t.leverage != null && t.leverage !== 1;
  },

  /** Geprüfter Kalenderbereich (Kalendervertrag 1A): NYSE/XETRA 2000–2035 */
  _geprueft: function(ds, boerse) { return (boerse === 'NYSE' || boerse === 'XETRA') && this._imKalender(ds); },

  _tageZwischen: function(a, b) {
    return Math.round((Date.UTC(+b.slice(0, 4), +b.slice(5, 7) - 1, +b.slice(8, 10)) -
                       Date.UTC(+a.slice(0, 4), +a.slice(5, 7) - 1, +a.slice(8, 10))) / 86400000);
  },

  /** Kurslücken je Trade markieren (Plan 1B L1/V1), je Kursintervall a → b bis Ausstieg bzw. Stop-Tag:
   *  im geprüften Bereich fehlende Kalendersitzungen strikt zwischen a und b, sonst ein auffälliger Abstand bei mehr
   *  als 4 Kalendertagen (Warnheuristik). naeherung = Hebel ≠ 1 irgendwo im Trade UND mindestens ein Lückenintervall —
   *  auch ein übersprungener Hebelwechsel ist ohne Zwischenkurs nicht rekonstruierbar. Trades bleiben erhalten (L3). */
  _gueltigerKurs: function(c) { return typeof c === 'number' && isFinite(c) && c > 0; },

  _lueckenMarkieren: function(rows, trades) {
    var b = this._ctx(rows).boerse, self = this;
    (trades || []).forEach(function(t) {
      var i0 = self._exakt(rows, t.entry_date), i1 = self._exakt(rows, t.exit_date), fs = 0, aa = 0, vor = i0;
      for (var i = i0 + 1; i0 >= 0 && i <= i1; i++) {
        // Zeile mit ungültigem Kurs (0, null, NaN) zählt wie eine fehlende Bewertung (Codex Code-R1 1B)
        if (!self._gueltigerKurs(rows[i].close)) continue;
        var a = rows[vor].date, z = rows[i].date;
        vor = i;
        if (self._geprueft(a, b) && self._geprueft(z, b)) {
          var d = self._kalenderSitzung(self._plusTage(a, 1), 1, b);
          while (d != null && d < z) { fs++; d = self._kalenderSitzung(self._plusTage(d, 1), 1, b); }
        } else if (self._tageZwischen(a, z) > 4) {
          aa++;
        }
      }
      t.fehlende_sitzungen = fs;
      t.auffaellige_abstaende = aa;
      t.naeherung = self._gehebelt(t) && (fs + aa) > 0;
    });
    return trades;
  },

  /** Tägliche Equity eines Kontos (Plan 1B E1/V3): nur geschlossene Trades; je Kursintervall Exposure = größter Hebel
   *  aller Trades, die das Intervall halten (keine Stapelung — ein Konto, höchstens die größte gleichzeitige
   *  Position). null, wenn ein Trade einen Hebel ohne täglichen Pfad hat (kein scheinbar gültiger 1x-Kontowert).
   *  Werte ungerundet; Kurve als [{date, value}] ab dem ersten Einstieg.
   *  Ungültige Kurse (0, null, NaN) sind fehlende Bewertungen: bewertet wird zwischen gültigen Schlusskursen, wenn das
   *  Exposure über die übersprungenen Intervalle gleich bleibt; sonst null mit info.grund = 'ungueltiger_kurs'
   *  (Codex Code-R1 1B). info.grund = 'hebel_ohne_pfad' bei Hebel ohne täglichen Pfad. */
  tagesEquity: function(rows, trades, start, info) {
    info = info || {};
    start = start || 1000;
    var zu = (trades || []).filter(function(t) { return !t.open && typeof t.return_pct === 'number' && isFinite(t.return_pct); });
    if (!zu.length) return null;
    var exp = [], erst = -1, letzt = -1, ersterEin = null, letzterAus = null, self = this;
    for (var n = 0; n < zu.length; n++) {
      var t = zu[n];
      if (!t.hebel && t.leverage != null && t.leverage !== 1) { info.grund = 'hebel_ohne_pfad'; return null; }
      var i0 = this._exakt(rows, t.entry_date), i1 = this._exakt(rows, t.exit_date);
      if (i0 < 0 || i1 < i0) continue;
      for (var i = i0 + 1; i <= i1; i++) {
        var h = t.hebel ? t.hebel[i - i0 - 1][1] : 1;
        if (!(exp[i] >= h)) exp[i] = h;
      }
      if (erst < 0 || i0 < erst) erst = i0;
      if (i1 > letzt) letzt = i1;
      if (ersterEin == null || t.entry_date < ersterEin) ersterEin = t.entry_date;
      if (letzterAus == null || t.exit_date > letzterAus) letzterAus = t.exit_date;
    }
    if (erst < 0) return null;
    var e = 1, peak = 1, maxdd = 0, kurve = [{ date: rows[erst].date, value: start }], vor = erst;
    for (var j = erst + 1; j <= letzt; j++) {
      if (!this._gueltigerKurs(rows[j].close)) continue;
      var h = exp[vor + 1] || 0;
      for (var k = vor + 2; k <= j; k++) {
        if ((exp[k] || 0) !== h) { info.grund = 'ungueltiger_kurs'; return null; }
      }
      e *= 1 + h * (rows[j].close / rows[vor].close - 1);
      vor = j;
      if (e > peak) peak = e;
      if (e / peak - 1 < maxdd) maxdd = e / peak - 1;
      kurve.push({ date: rows[j].date, value: start * e });
    }
    var jahre = self._tageZwischen(ersterEin, letzterAus) / 365.25;
    return { max_dd: maxdd * 100, final_equity: start * e, total_return: (e - 1) * 100,
             cagr: jahre > 0 ? (Math.pow(e, 1 / jahre) - 1) * 100 : 0, kurve: kurve };
  },

  /** Fixed Stop-Loss: Auslösung, wenn ein Close (einschliesslich des regulären Ausstiegstags) <= Einstieg × (1−p) */
  applyStopLoss: function(rows, trades, stopPct) {
    if (!(stopPct > 0)) return trades;
    var self = this;
    return trades.map(function(t) {
      var entryIdx = self._exakt(rows, t.entry_date), exitIdx = self._exakt(rows, t.exit_date);
      if (entryIdx < 0 || exitIdx < 0) return t;
      var stopPrice = t.entry_price * (1 - stopPct / 100);
      for (var i = entryIdx + 1; i <= exitIdx; i++) {
        var c = rows[i].close;
        if (!(typeof c === 'number' && isFinite(c) && c > 0)) { self._notiere('stop_kurs_ungueltig', rows[i].date); continue; }
        if (c <= stopPrice) return self._stopAusstieg(t, rows, i);
      }
      return t;
    });
  },

  /** Down-Month Turn-of-Month Reversal: 21d-Rückgang vor ToM → Bounce (SPY validiert, Sharpe 0.34) */
  calc_downmonth_tom: function(rows) {
    var trades = [], years = this._getYears(rows);
    var STREV = 21, ENTRY_TDOM = 14, HOLD = 13;
    for (var i = 0; i < years.length; i++) {
      for (var m = 1; m <= 12; m++) {
        var entryIdx = this._nthTradingDay(rows, years[i], m, ENTRY_TDOM);
        if (entryIdx < STREV + 1) continue;
        var prevIdx = entryIdx - 1;
        var revIdx  = prevIdx - STREV;
        if (revIdx < 0 || rows[revIdx].close <= 0) continue;
        if (rows[prevIdx].close / rows[revIdx].close >= 1) continue;
        var exitIdx = this._offset(rows, entryIdx, HOLD);
        var t = this._makeTrade(rows, entryIdx, exitIdx);
        if (t) trades.push(t);
      }
    }
    return trades;
  },

  /** Trailing Stop-Loss im Close-Modus: Peak aus Schlusskursen, Auslösung am Close <= Peak × (1−p), Ausführung
   *  am Close; einschliesslich des regulären Ausstiegstags (E5). */
  applyTrailingStop: function(rows, trades, stopPct) {
    if (!(stopPct > 0)) return trades;
    var self = this;
    return trades.map(function(t) {
      var entryIdx = self._exakt(rows, t.entry_date), exitIdx = self._exakt(rows, t.exit_date);
      if (entryIdx < 0 || exitIdx < 0) return t;
      var peak = t.entry_price;
      for (var i = entryIdx + 1; i <= exitIdx; i++) {
        var c = rows[i].close;
        if (!(typeof c === 'number' && isFinite(c) && c > 0)) { self._notiere('stop_kurs_ungueltig', rows[i].date); continue; }
        if (c > peak) peak = c;
        if (c <= peak * (1 - stopPct / 100)) return self._stopAusstieg(t, rows, i);
      }
      return t;
    });
  }
};

// ══════════════════════════════════════════════════════
// STRATEGY REGISTRY
// ══════════════════════════════════════════════════════

(function() {
  var _en = !!(SA.i18n && SA.i18n.isEN && SA.i18n.isEN());

  SA.STRATEGIES = {
    sell_in_may:       { name:'Sell in May',       icon:'📅', cat:'saisonal',   func:'calc_sell_in_may',       desc: _en ? SA.i18n.t('strat.sell_in_may_desc')         : 'Letzter HT Okt → 3. HT Mai' },
    lbr_november_mai:  { name:'LBR Nov-Mai',       icon:'📊', cat:'saisonal',   func:'calc_lbr_november_mai',  desc: _en ? SA.i18n.t('strat.lbr_nov_mai_desc')         : 'Ab Okt LBR>0 → Ab Apr LBR<0' },
    nasdaq_trend:      { name:'Nasdaq-Trend',      icon:'📈', cat:'saisonal',   func:'calc_nasdaq_trend',      desc: _en ? SA.i18n.t('strat.nasdaq_trend_desc')        : 'Letzter HT Okt → Letzter HT Jun' },
    september_avoid:   { name: _en ? SA.i18n.t('strat.sep_avoid_name')     : 'Sep-Vermeidung',    icon:'🚫', cat:'saisonal',   func:'calc_september_avoid',   desc: _en ? SA.i18n.t('strat.sep_avoid_desc')           : '30. Sep → 31. Aug (11 Mon)' },
    election_7months:  { name: _en ? SA.i18n.t('strat.election_7m_name')   : 'Wahljahr 7 Mon',    icon:'🗳️', cat:'saisonal', func:'calc_election_year_7months', desc: _en ? SA.i18n.t('strat.election_7m_desc')     : '31. Mai → 31. Dez Wahljahr' },

    first_five_days:   { name:'First Five Days',   icon:'5️⃣', cat:'januar',    func:'calc_first_five_days',   desc: _en ? SA.i18n.t('strat.first_five_days_desc')     : 'Erste 5 Jan-HT positiv → Long' },
    last_five_days:    { name:'Last Five Days',    icon:'🔚', cat:'januar',     func:'calc_last_five_days',    desc: _en ? SA.i18n.t('strat.last_five_days_desc')      : 'Letzte 5 Jan-HT positiv → Long' },
    january_barometer: { name: _en ? SA.i18n.t('strat.jan_barometer_name') : 'Jan-Barometer',     icon:'🌡️', cat:'januar', func:'calc_january_barometer', desc: _en ? SA.i18n.t('strat.jan_barometer_desc')   : 'Januar positiv → Long Feb-Dez' },

    santa_claus:       { name:'Santa Claus',       icon:'🎅', cat:'feiertag',   func:'calc_santa_claus',       desc: _en ? SA.i18n.t('strat.santa_claus_desc')         : '3 HT vor Thanksgiving → 5. HT Jan' },
    one_day_holiday:   { name: _en ? SA.i18n.t('strat.one_day_holiday_name') : 'Feiertag 1-Tag',    icon:'🎆', cat:'feiertag',   func:'calc_one_day_holiday',   desc: _en ? SA.i18n.t('strat.one_day_holiday_desc') : '2 HT vor Feiertag → 1 HT vor' },
    uhts:              { name:'UHTS (Hebel)',       icon:'🎇', cat:'feiertag',   func:'calc_uhts',              desc: _en ? SA.i18n.t('strat.uhts_desc')                : '3 HT vor → 3 HT nach (2x ab Vortag)' },
    post_christmas:    { name: _en ? SA.i18n.t('strat.post_christmas_name') : 'Nach Weihnachten',  icon:'🎄', cat:'feiertag',   func:'calc_post_christmas',    desc: _en ? SA.i18n.t('strat.post_christmas_desc')  : '26. Dez → Silvester' },

    month_end:         { name:'Month-End',         icon:'🔄', cat:'monat',      func:'calc_month_end',         desc: _en ? SA.i18n.t('strat.month_end_desc')           : 'Vorletzter HT → 4. HT Folgemonat' },
    monthly_10:        { name:'Monthly 10',        icon:'📆', cat:'monat',      func:'calc_monthly_10',        desc: _en ? SA.i18n.t('strat.monthly_10_desc')          : 'TDOM 1-4, 9-12, letzte 2' },
    second_trading_day:{ name: _en ? SA.i18n.t('strat.second_trading_day_name') : '2. Handelstag',     icon:'2️⃣', cat:'monat',     func:'calc_second_trading_day', desc: _en ? SA.i18n.t('strat.second_trading_day_desc') : 'Close TDOM 1 → Close TDOM 2' },
    downmonth_tom:     { name:'Down-Month ToM',    icon:'📉', cat:'monat',      func:'calc_downmonth_tom',     desc: _en ? '21d drop before ToM → reversal (SPY validated)' : '21d < 0 → ToM-Bounce (SPY validiert)' },

    cycle_40_week:     { name: _en ? SA.i18n.t('strat.cycle_40_week_name')  : '40-Wochen',         icon:'⚡',       cat:'zyklus',     func:'calc_40_week_cycle',     desc: _en ? SA.i18n.t('strat.cycle_40_week_desc')       : '280d-Zyklus, 140d investiert' },
    cycle_212_week:    { name: _en ? SA.i18n.t('strat.cycle_212_week_name') : '212-Wochen',        icon:'🔁', cat:'zyklus',     func:'calc_212_week_cycle',    desc: _en ? SA.i18n.t('strat.cycle_212_week_desc')      : '1.484d-Zyklus, 182d investiert' },
    mid_decade:        { name:'Mid-Decade',        icon:'📆', cat:'zyklus',     func:'calc_mid_decade',        desc: _en ? SA.i18n.t('strat.mid_decade_desc')          : 'Okt x4 → Mär x6 (18 Mon)' },
    cycle_20_year:     { name: _en ? SA.i18n.t('strat.cycle_20_year_name')  : '20-Jahres',         icon:'🔄', cat:'zyklus',     func:'calc_20_year_cycle',     desc: _en ? SA.i18n.t('strat.cycle_20_year_desc')       : 'Sep x2 → Dez x5 (27 Mon)' },

    uecs:              { name:'Election Cycle',    icon:'🇺🇸', cat:'wahlzyklus', func:'calc_uecs', desc: _en ? SA.i18n.t('strat.uecs_desc')               : '6 Phasen Präsidentenzyklus' },
    midterm_election:  { name:'Midterm Election',  icon:'🏛️', cat:'wahlzyklus', func:'calc_midterm_election', desc: _en ? SA.i18n.t('strat.midterm_election_desc') : '5 HT vor → 3 HT nach Midterm' }
  };

  SA.STRATEGY_CATEGORIES = {
    saisonal:   { label: _en ? SA.i18n.t('strat.cat_seasonal')    : 'Saisonale Klassiker', order:1 },
    januar:     { label: _en ? SA.i18n.t('strat.cat_january')     : 'Januar-Signale',      order:2 },
    feiertag:   { label: _en ? SA.i18n.t('strat.cat_holiday')     : 'Feiertage',           order:3 },
    monat:      { label: _en ? SA.i18n.t('strat.cat_monthly')     : 'Monatsmuster',        order:4 },
    zyklus:     { label: _en ? SA.i18n.t('strat.cat_cycles')      : 'Zyklen',              order:5 },
    wahlzyklus: { label: _en ? SA.i18n.t('strat.cat_election')    : 'Wahlzyklus',          order:6 }
  };
})();

window.SA = SA;

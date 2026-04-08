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

  _nthTradingDay: function(rows, year, month, n) {
    var days = this._getTradingDays(rows, year, month);
    return days.length >= n ? days[n - 1] : -1;
  },

  _lastTradingDay: function(rows, year, month) {
    var days = this._getTradingDays(rows, year, month);
    return days.length > 0 ? days[days.length - 1] : -1;
  },

  _nthLastTradingDay: function(rows, year, month, n) {
    var days = this._getTradingDays(rows, year, month);
    return days.length >= n ? days[days.length - n] : -1;
  },

  /** Naechster Handelstag >= target (binary search) */
  _nearestForward: function(rows, dateStr) {
    var lo = 0, hi = rows.length - 1, best = -1;
    while (lo <= hi) {
      var mid = (lo + hi) >> 1;
      if (rows[mid].date >= dateStr) { best = mid; hi = mid - 1; }
      else lo = mid + 1;
    }
    return best;
  },

  /** Letzter Handelstag <= target */
  _nearestBackward: function(rows, dateStr) {
    var lo = 0, hi = rows.length - 1, best = -1;
    while (lo <= hi) {
      var mid = (lo + hi) >> 1;
      if (rows[mid].date <= dateStr) { best = mid; lo = mid + 1; }
      else hi = mid - 1;
    }
    return best;
  },

  _makeTrade: function(rows, entryIdx, exitIdx) {
    if (entryIdx < 0 || entryIdx >= rows.length) return null;
    // Exit in der Zukunft → offener Trade, Mark-to-Market mit letztem verfuegbaren Kurs
    var open = false;
    if (exitIdx < 0 || exitIdx >= rows.length) {
      exitIdx = rows.length - 1;
      open = true;
    }
    if (exitIdx <= entryIdx) return null;
    var pe = rows[entryIdx].close, px = rows[exitIdx].close;
    if (pe <= 0) return null;
    var trade = {
      entry_date: rows[entryIdx].date, exit_date: rows[exitIdx].date,
      entry_price: Math.round(pe * 100) / 100,
      exit_price: Math.round(px * 100) / 100,
      return_pct: Math.round((px - pe) / pe * 10000) / 100
    };
    if (open) trade.open = true;
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
  _nyseHolidays: function(y) { return SA.holidays.get(y, 'NYSE'); },

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
      var thxDate = this._thanksgiving(years[i]);
      var thxIdx = this._nearestBackward(rows, thxDate);
      if (thxIdx < 3) continue;
      var entry = thxIdx - 3;
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
      var elIdx = self._nearestBackward(rows, elDate);
      if (elIdx < 5) return;
      var entry = elIdx - 5;
      var afterIdx = self._nearestForward(rows, elDate);
      if (afterIdx < 0 || afterIdx + 3 >= rows.length) return;
      var exit = afterIdx + 3;
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
        var holIdx = self._nearestForward(rows, holDate);
        if (holIdx < 2) return;
        var t = self._makeTrade(rows, holIdx - 2, holIdx - 1);
        if (t) trades.push(t);
      });
    });
    return trades;
  },

  /** 18. UHTS (Ultimate Holiday Trading System, NYSE-Feiertage) */
  calc_uhts: function(rows) {
    var trades = [], years = this._getYears(rows), self = this;
    years.forEach(function(y) {
      var hols = self._nyseHolidays(y);
      hols.forEach(function(holDate) {
        var holIdx = self._nearestForward(rows, holDate);
        if (holIdx < 3 || holIdx + 3 >= rows.length) return;
        var entry = holIdx - 3, exit = holIdx + 3;
        var t = self._makeTrade(rows, entry, exit);
        if (t) {
          t.return_pct = Math.round(t.return_pct * 1.5 * 100) / 100;
          t.leverage = 1.5;
          trades.push(t);
        }
      });
    });
    return trades;
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
        var elIdx = self._nearestBackward(rows, elDate);
        if (elIdx >= 5) {
          var afterIdx = self._nearestForward(rows, elDate);
          if (afterIdx >= 0 && afterIdx + 3 < rows.length) {
            var t1 = self._makeTrade(rows, elIdx - 5, afterIdx + 3);
            if (t1) trades.push(t1);
          }
        }
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
          last.return_pct = Math.round((last.exit_price - last.entry_price) / last.entry_price * 10000) / 100;
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
        var days = self._getTradingDays(rows, y, m);
        if (days.length < 10) return;
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

  /** 2. LBR November-Mai (simplified: nutzt indicators.js wenn vorhanden) */
  calc_lbr_november_mai: function(rows) {
    // Fallback auf einfaches Sell-in-May wenn kein Indikator-Modul
    if (!SA.indicators || !SA.indicators.calcMACD) return this.calc_sell_in_may(rows);
    var closes = rows.map(function(r) { return r.close; });
    var macd = SA.indicators.calcMACD(closes, 3, 10, 16);
    var hist = macd.histogram;
    var trades = [], years = this._getYears(rows), self = this;
    years.forEach(function(y) {
      // Entry: ab Okt wenn Histogram > 0
      var octStart = self._nearestForward(rows, self._dateStr(y, 10, 1));
      if (octStart < 0) return;
      var entry = -1;
      for (var i = octStart; i < rows.length; i++) {
        if (rows[i].date > self._dateStr(y + 1, 3, 31)) break;
        if (hist[i] > 0) { entry = i; break; }
      }
      if (entry < 0) return;
      // Exit: ab Apr wenn Histogram < 0
      var aprStart = self._nearestForward(rows, self._dateStr(y + 1, 4, 1));
      if (aprStart < 0) return;
      var exit = -1;
      for (var i = aprStart; i < rows.length; i++) {
        if (rows[i].date > self._dateStr(y + 1, 6, 30)) break;
        if (hist[i] < 0) { exit = i; break; }
      }
      if (exit < 0) return;
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

  /** KPI-Statistiken */
  computeStats: function(trades, startCapital) {
    startCapital = startCapital || 1000;
    if (!trades || !trades.length) return null;
    // Offene Trades aus Statistik ausschliessen (CAGR/Sharpe/PF nur fuer geschlossene Trades)
    trades = trades.filter(function(t) { return !t.open; });
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
    var sharpe = stdRet > 0 ? (avg / stdRet) * Math.sqrt(tradesPerYear) : 0;

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
      sharpe: Math.round(sharpe * 100) / 100,
      final_equity: Math.round(final * 100) / 100,
      years_span: Math.round(yearsSpan * 10) / 10,
      profit_factor: grossLoss > 0 ? Math.round(grossProfit / grossLoss * 100) / 100 : 999
    };
  },

  /** Fixed Stop-Loss anwenden */
  applyStopLoss: function(rows, trades, stopPct) {
    if (stopPct <= 0) return trades;
    var self = this;
    return trades.map(function(t) {
      var entryIdx = self._nearestForward(rows, t.entry_date);
      var exitIdx = self._nearestForward(rows, t.exit_date);
      if (entryIdx < 0 || exitIdx < 0) return t;
      var stopPrice = t.entry_price * (1 - stopPct / 100);
      for (var i = entryIdx + 1; i <= exitIdx; i++) {
        if (rows[i].close <= stopPrice) {
          return {
            entry_date: t.entry_date, exit_date: rows[i].date,
            entry_price: t.entry_price, exit_price: Math.round(stopPrice * 100) / 100,
            return_pct: -Math.round(stopPct * 100) / 100,
            stopped: true
          };
        }
      }
      return t;
    });
  },

  /** Trailing Stop-Loss — Stop folgt dem Kurs nach oben */
  applyTrailingStop: function(rows, trades, stopPct) {
    if (stopPct <= 0) return trades;
    var self = this;
    return trades.map(function(t) {
      var entryIdx = self._nearestForward(rows, t.entry_date);
      var exitIdx = self._nearestForward(rows, t.exit_date);
      if (entryIdx < 0 || exitIdx < 0) return t;
      var peak = t.entry_price;
      for (var i = entryIdx + 1; i <= exitIdx; i++) {
        var c = parseFloat(rows[i].close);
        if (c > peak) peak = c;
        var stopPrice = peak * (1 - stopPct / 100);
        if (c <= stopPrice) {
          return {
            entry_date: t.entry_date, exit_date: rows[i].date,
            entry_price: t.entry_price, exit_price: Math.round(c * 100) / 100,
            return_pct: Math.round((c / t.entry_price - 1) * 10000) / 100,
            stopped: true
          };
        }
      }
      return t;
    });
  }
};

// ══════════════════════════════════════════════════════
// STRATEGY REGISTRY
// ══════════════════════════════════════════════════════

SA.STRATEGIES = {
  sell_in_may:       { name:'Sell in May',       icon:'\uD83D\uDCC5', cat:'saisonal',   func:'calc_sell_in_may',       desc:'Letzter HT Okt \u2192 3. HT Mai' },
  lbr_november_mai:  { name:'LBR Nov-Mai',       icon:'\uD83D\uDCCA', cat:'saisonal',   func:'calc_lbr_november_mai',  desc:'Ab Okt LBR>0 \u2192 Ab Apr LBR<0' },
  nasdaq_trend:      { name:'Nasdaq-Trend',      icon:'\uD83D\uDCC8', cat:'saisonal',   func:'calc_nasdaq_trend',      desc:'Letzter HT Okt \u2192 Letzter HT Jun' },
  september_avoid:   { name:'Sep-Vermeidung',    icon:'\uD83D\uDEAB', cat:'saisonal',   func:'calc_september_avoid',   desc:'30. Sep \u2192 31. Aug (11 Mon)' },
  election_7months:  { name:'Wahljahr 7 Mon',    icon:'\uD83D\uDDF3\uFE0F', cat:'saisonal', func:'calc_election_year_7months', desc:'31. Mai \u2192 31. Dez Wahljahr' },

  first_five_days:   { name:'First Five Days',   icon:'5\uFE0F\u20E3', cat:'januar',    func:'calc_first_five_days',   desc:'Erste 5 Jan-HT positiv \u2192 Long' },
  last_five_days:    { name:'Last Five Days',    icon:'\uD83D\uDD1A', cat:'januar',     func:'calc_last_five_days',    desc:'Letzte 5 Jan-HT positiv \u2192 Long' },
  january_barometer: { name:'Jan-Barometer',     icon:'\uD83C\uDF21\uFE0F', cat:'januar', func:'calc_january_barometer', desc:'Januar positiv \u2192 Long Feb-Dez' },

  santa_claus:       { name:'Santa Claus',       icon:'\uD83C\uDF85', cat:'feiertag',   func:'calc_santa_claus',       desc:'3 HT vor Thanksgiving \u2192 5. HT Jan' },
  one_day_holiday:   { name:'Feiertag 1-Tag',    icon:'\uD83C\uDF86', cat:'feiertag',   func:'calc_one_day_holiday',   desc:'2 HT vor Feiertag \u2192 1 HT vor' },
  uhts:              { name:'UHTS (Hebel)',       icon:'\uD83C\uDF87', cat:'feiertag',   func:'calc_uhts',              desc:'3 HT vor \u2192 3 HT nach (1.5x)' },
  post_christmas:    { name:'Nach Weihnachten',  icon:'\uD83C\uDF84', cat:'feiertag',   func:'calc_post_christmas',    desc:'26. Dez \u2192 Silvester' },

  month_end:         { name:'Month-End',         icon:'\uD83D\uDD04', cat:'monat',      func:'calc_month_end',         desc:'Vorletzter HT \u2192 4. HT Folgemonat' },
  monthly_10:        { name:'Monthly 10',        icon:'\uD83D\uDCC6', cat:'monat',      func:'calc_monthly_10',        desc:'TDOM 1-4, 9-12, letzte 2' },
  second_trading_day:{ name:'2. Handelstag',     icon:'2\uFE0F\u20E3', cat:'monat',     func:'calc_second_trading_day', desc:'Close TDOM 1 \u2192 Close TDOM 2' },

  cycle_40_week:     { name:'40-Wochen',         icon:'\u26A1',       cat:'zyklus',     func:'calc_40_week_cycle',     desc:'280d-Zyklus, 140d investiert' },
  cycle_212_week:    { name:'212-Wochen',        icon:'\uD83D\uDD01', cat:'zyklus',     func:'calc_212_week_cycle',    desc:'1.484d-Zyklus, 182d investiert' },
  mid_decade:        { name:'Mid-Decade',        icon:'\uD83D\uDCC6', cat:'zyklus',     func:'calc_mid_decade',        desc:'Okt x4 \u2192 M\u00E4r x6 (18 Mon)' },
  cycle_20_year:     { name:'20-Jahres',         icon:'\uD83D\uDD04', cat:'zyklus',     func:'calc_20_year_cycle',     desc:'Sep x2 \u2192 Dez x5 (27 Mon)' },

  uecs:              { name:'Election Cycle',    icon:'\uD83C\uDDFA\uD83C\uDDF8', cat:'wahlzyklus', func:'calc_uecs', desc:'6 Phasen Pr\u00E4sidentenzyklus' },
  midterm_election:  { name:'Midterm Election',  icon:'\uD83C\uDFDB\uFE0F', cat:'wahlzyklus', func:'calc_midterm_election', desc:'5 HT vor \u2192 3 HT nach Midterm' }
};

SA.STRATEGY_CATEGORIES = {
  saisonal:   { label:'Saisonale Klassiker', order:1 },
  januar:     { label:'Januar-Signale',      order:2 },
  feiertag:   { label:'Feiertage',           order:3 },
  monat:      { label:'Monatsmuster',        order:4 },
  zyklus:     { label:'Zyklen',              order:5 },
  wahlzyklus: { label:'Wahlzyklus',          order:6 }
};

window.SA = SA;

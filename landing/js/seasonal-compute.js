/**
 * SeasonAlpha — Seasonal Compute (Port von shared/calculations.py)
 * =================================================================
 * Kern-Berechnungen fuer saisonale Analysen.
 * Wird von: Monatswechsel, Mondphasen, Jahreszyklus, Monatszyklus, Wochentage genutzt.
 */

var SA = window.SA || {};

SA.seasonal = {

  MONTH_NAMES_DE: ['Januar','Februar','M\u00E4rz','April','Mai','Juni',
                   'Juli','August','September','Oktober','November','Dezember'],

  /**
   * Praesidentenzyklus-Position (1:1 Port von get_presidential_cycle_year)
   * @param {number} year
   * @returns {string}
   */
  getPresidentialCycleYear: function(year) {
    var pos = ((year - 2024) % 4 + 4) % 4; // Sicher positiv
    if (pos === 0) return 'Year 4 (Election Year)';
    if (pos === 1) return 'Year 1 (Post-Election)';
    if (pos === 2) return 'Year 2 (Midterm Election)';
    return 'Year 3 (Pre-Election)';
  },

  /**
   * Turn-of-Month Analyse (1:1 Port von analyze_turn_of_month)
   * @param {Array} rows - [{date, close, log_return, ...}] sortiert nach Datum
   * @param {number} daysBefore - Handelstage vor Monatsende (default 3)
   * @param {number} daysAfter - Handelstage nach Monatswechsel (default 3)
   * @param {Array} selectedMonths - [1..12] oder null fuer alle
   * @param {Array} selectedYears - [2000, 2001, ...] oder null fuer alle
   * @returns {Object|null} {avg_curve, all_curves, labels, stats, best, worst}
   */
  analyzeTurnOfMonth: function(rows, daysBefore, daysAfter, selectedMonths, selectedYears) {
    daysBefore = daysBefore || 3;
    daysAfter = daysAfter || 3;
    var windowSize = daysBefore + 1 + daysAfter;

    // Nach Jahr+Monat gruppieren
    var ymGroups = {};
    for (var i = 0; i < rows.length; i++) {
      var r = rows[i];
      var y = parseInt(r.date.substring(0, 4));
      var m = parseInt(r.date.substring(5, 7));
      var key = y + '-' + m;
      if (!ymGroups[key]) ymGroups[key] = { year: y, month: m, rows: [] };
      ymGroups[key].rows.push(r);
    }

    var allCurves = [];

    var keys = Object.keys(ymGroups).sort();
    for (var ki = 0; ki < keys.length - 1; ki++) {
      var cur = ymGroups[keys[ki]];
      var nxt = ymGroups[keys[ki + 1]];

      // Filter: ausgewaehlte Monate
      if (selectedMonths && selectedMonths.indexOf(cur.month) < 0) continue;
      // Filter: ausgewaehlte Jahre
      if (selectedYears && selectedYears.indexOf(cur.year) < 0) continue;

      // Pre-Window: letzte (daysBefore + 1) Tage des aktuellen Monats
      var pre = cur.rows.slice(-(daysBefore + 1));
      if (pre.length < daysBefore + 1) continue;

      // Post-Window: erste daysAfter Tage des naechsten Monats
      var post = nxt.rows.slice(0, daysAfter);
      if (post.length < daysAfter) continue;

      // Fenster zusammenbauen
      var window = pre.concat(post);
      if (window.length !== windowSize) continue;

      // Log-Returns extrahieren (1:1 wie Python: tom_window["log_return"].values)
      var logRets = [];
      for (var wi = 0; wi < window.length; wi++) {
        var lr = window[wi].log_return != null
          ? window[wi].log_return
          : (wi > 0 && window[wi - 1].close > 0 ? Math.log(window[wi].close / window[wi - 1].close) : 0);
        logRets.push(lr);
      }

      // Kumulative Kurve (1:1 wie Python: cum_log = cumsum(insert(log_rets, 0, 0)[:-1]))
      // insert(log_rets, 0, 0) = [0, lr0, lr1, ...], dann [:-1] = [0, lr0, lr1, ..., lr_{n-2}]
      var cumLog = [0];
      for (var ci = 0; ci < logRets.length - 1; ci++) {
        cumLog.push(cumLog[ci] + logRets[ci]);
      }
      // raw_curve = 100 * exp(cum_log)
      var rawCurve = cumLog.map(function(v) { return 100 * Math.exp(v); });

      // Normierung auf t0: curve = (raw / raw[t0] - 1) * 100
      var t0Idx = daysBefore;
      var t0Val = rawCurve[t0Idx];
      var curve = rawCurve.map(function(v) { return Math.round((v / t0Val - 1) * 10000) / 100; });

      var totalReturn = curve[curve.length - 1] - curve[0];

      allCurves.push({
        year: cur.year,
        month: cur.month,
        curve: curve,
        total_return: Math.round(totalReturn * 100) / 100
      });
    }

    if (allCurves.length === 0) return null;

    // Durchschnittskurve
    var avgCurve = new Array(windowSize).fill(0);
    for (var ai = 0; ai < allCurves.length; ai++) {
      for (var aj = 0; aj < windowSize; aj++) {
        avgCurve[aj] += (allCurves[ai].curve[aj] || 0);
      }
    }
    avgCurve = avgCurve.map(function(v) { return Math.round(v / allCurves.length * 100) / 100; });

    // Labels: t-3, t-2, t-1, t0, t+1, t+2, t+3
    var labels = [];
    for (var li = -daysBefore; li <= daysAfter; li++) {
      labels.push(li === 0 ? 't0' : (li < 0 ? 't' + li : 't+' + li));
    }

    // Statistiken
    var returns = allCurves.map(function(c) { return c.total_return; });
    returns.sort(function(a, b) { return a - b; });
    var sum = returns.reduce(function(s, v) { return s + v; }, 0);
    var avg = sum / returns.length;
    var med = returns[Math.floor(returns.length / 2)];
    var winning = returns.filter(function(r) { return r > 0; }).length;
    var variance = returns.reduce(function(s, v) { return s + (v - avg) * (v - avg); }, 0) / returns.length;

    // Best/Worst
    var best = allCurves[0], worst = allCurves[0];
    for (var bi = 1; bi < allCurves.length; bi++) {
      if (allCurves[bi].total_return > best.total_return) best = allCurves[bi];
      if (allCurves[bi].total_return < worst.total_return) worst = allCurves[bi];
    }

    return {
      avg_curve: avgCurve,
      all_curves: allCurves,
      labels: labels,
      stats: {
        avg_return: Math.round(avg * 100) / 100,
        median_return: Math.round(med * 100) / 100,
        win_rate: Math.round(winning / returns.length * 10000) / 100,
        std_dev: Math.round(Math.sqrt(variance) * 100) / 100,
        max_gain: Math.round(returns[returns.length - 1] * 100) / 100,
        max_loss: Math.round(returns[0] * 100) / 100,
        total_windows: allCurves.length,
        winning: winning,
        losing: returns.length - winning
      },
      best: { year: best.year, month: best.month, total_return: best.total_return },
      worst: { year: worst.year, month: worst.month, total_return: worst.total_return }
    };
  },

  /**
   * Monatliche Performance-Statistiken
   * @param {Array} rows - [{date, close}]
   * @returns {Array} [{month, avg, median, winRate, maxGain, maxLoss, n}]
   */
  buildMonthlyStats: function(rows) {
    var monthData = {};
    for (var m = 1; m <= 12; m++) monthData[m] = [];

    // Nach Jahr+Monat gruppieren, Monatsrendite berechnen
    var ymGroups = {};
    for (var i = 0; i < rows.length; i++) {
      var y = parseInt(rows[i].date.substring(0, 4));
      var m = parseInt(rows[i].date.substring(5, 7));
      var key = y + '-' + m;
      if (!ymGroups[key]) ymGroups[key] = { month: m, rows: [] };
      ymGroups[key].rows.push(rows[i]);
    }

    for (var k in ymGroups) {
      var g = ymGroups[k];
      if (g.rows.length < 10) continue;
      var first = g.rows[0].close;
      var last = g.rows[g.rows.length - 1].close;
      if (first > 0) {
        monthData[g.month].push((last / first - 1) * 100);
      }
    }

    var result = [];
    for (var m = 1; m <= 12; m++) {
      var rets = monthData[m];
      if (rets.length === 0) {
        result.push({ month: m, avg: 0, median: 0, winRate: 0, maxGain: 0, maxLoss: 0, n: 0 });
        continue;
      }
      rets.sort(function(a, b) { return a - b; });
      var sum = rets.reduce(function(s, v) { return s + v; }, 0);
      var wins = rets.filter(function(r) { return r > 0; }).length;
      result.push({
        month: m,
        avg: Math.round(sum / rets.length * 100) / 100,
        median: Math.round(rets[Math.floor(rets.length / 2)] * 100) / 100,
        winRate: Math.round(wins / rets.length * 1000) / 10,
        maxGain: Math.round(rets[rets.length - 1] * 100) / 100,
        maxLoss: Math.round(rets[0] * 100) / 100,
        n: rets.length
      });
    }
    return result;
  },

  /**
   * TOM-Heatmap: Monat × Jahr Matrix
   * @param {Object} tomResult - Ergebnis von analyzeTurnOfMonth
   * @param {number} nYears - Letzte N Jahre anzeigen (default 10)
   * @returns {Object} {years, months, matrix}
   */
  buildTOMHeatmap: function(tomResult, nYears) {
    nYears = nYears || 10;
    if (!tomResult || !tomResult.all_curves) return null;

    // Alle (year, month) → return
    var ymMap = {};
    var allYears = {};
    for (var i = 0; i < tomResult.all_curves.length; i++) {
      var c = tomResult.all_curves[i];
      ymMap[c.year + '-' + c.month] = c.total_return;
      allYears[c.year] = true;
    }
    var years = Object.keys(allYears).map(Number).sort(function(a, b) { return a - b; });
    years = years.slice(-nYears);

    var matrix = [];
    for (var mi = 0; mi < 12; mi++) {
      var row = [];
      for (var yi = 0; yi < years.length; yi++) {
        var key = years[yi] + '-' + (mi + 1);
        row.push(ymMap[key] !== undefined ? Math.round(ymMap[key] * 100) / 100 : null);
      }
      matrix.push(row);
    }
    return { years: years, months: SA.seasonal.MONTH_NAMES_DE.map(function(n) { return n.substring(0, 3); }), matrix: matrix };
  },

  /**
   * Window-Optimierung: Matrix daysBefore × daysAfter → avg return
   * @param {Array} rows
   * @param {Array} selectedMonths
   * @param {Array} selectedYears
   * @param {number} maxWindow - max Fenster (default 7)
   * @returns {Object} {matrix, bestBefore, bestAfter, bestReturn}
   */
  calcWindowOptimization: function(rows, selectedMonths, selectedYears, maxWindow) {
    maxWindow = maxWindow || 7;
    var matrix = [];
    var bestReturn = -Infinity, bestBefore = 1, bestAfter = 1;

    for (var db = 1; db <= maxWindow; db++) {
      var row = [];
      for (var da = 1; da <= maxWindow; da++) {
        var result = SA.seasonal.analyzeTurnOfMonth(rows, db, da, selectedMonths, selectedYears);
        var avg = result && result.stats ? result.stats.avg_return : 0;
        row.push(Math.round(avg * 100) / 100);
        if (avg > bestReturn) { bestReturn = avg; bestBefore = db; bestAfter = da; }
      }
      matrix.push(row);
    }
    return { matrix: matrix, bestBefore: bestBefore, bestAfter: bestAfter, bestReturn: Math.round(bestReturn * 100) / 100 };
  },

  // ── Jahreskurven (Port von build_year_data + calculate_seasonal_average) ──

  /**
   * Normalisiert Jahreskurven: Start=100, kumulative Log-Returns, interpoliert auf 365 Tage.
   * (Port von build_year_data + normalize_year + interpolate_to_365)
   * @param {Array} rows - [{date, close, log_return}]
   * @returns {Object} {year: {full_365: [365 values], simpleReturn: %}}
   */
  buildYearData: function(rows) {
    var yearGroups = {};
    for (var i = 0; i < rows.length; i++) {
      var y = parseInt(rows[i].date.substring(0, 4));
      if (!yearGroups[y]) yearGroups[y] = [];
      yearGroups[y].push(rows[i]);
    }
    var result = {};
    for (var year in yearGroups) {
      var yRows = yearGroups[year];
      if (yRows.length < 20) continue;
      // Log-Returns kumulieren → normalisiert auf 100
      var cumulative = [100];
      for (var j = 1; j < yRows.length; j++) {
        var lr = yRows[j].log_return != null ? yRows[j].log_return
          : (yRows[j - 1].close > 0 ? Math.log(yRows[j].close / yRows[j - 1].close) : 0);
        cumulative.push(cumulative[j - 1] * Math.exp(lr));
      }
      // Day-of-Year fuer jeden Eintrag
      var days = yRows.map(function(r) {
        var d = new Date(r.date);
        var jan1 = new Date(d.getFullYear(), 0, 0);
        return Math.floor((d - jan1) / 86400000);
      });
      // Interpolieren auf 365 Kalendertage
      var full365 = SA.seasonal._interpolateTo365(days, cumulative);
      var simpleReturn = full365[364] > 0 ? (full365[364] / full365[0] - 1) * 100 : 0;
      result[parseInt(year)] = { full_365: full365, simpleReturn: Math.round(simpleReturn * 100) / 100 };
    }
    return result;
  },

  /**
   * Saisonaler Durchschnitt ueber alle Jahre (Port von calculate_seasonal_average).
   * @param {Object} yearData - von buildYearData
   * @returns {Object} {avg: [365], std: [365]}
   */
  calculateSeasonalAverage: function(yearData) {
    var years = Object.keys(yearData);
    if (years.length === 0) return { avg: [], std: [] };
    var curves = years.map(function(y) { return yearData[y].full_365; });
    var avg = [], std = [];
    for (var d = 0; d < 365; d++) {
      var vals = curves.map(function(c) { return c[d]; });
      var sum = vals.reduce(function(s, v) { return s + v; }, 0);
      var mean = sum / vals.length;
      var variance = vals.reduce(function(s, v) { return s + (v - mean) * (v - mean); }, 0) / vals.length;
      avg.push(Math.round(mean * 100) / 100);
      std.push(Math.round(Math.sqrt(variance) * 100) / 100);
    }
    return { avg: avg, std: std };
  },

  /** Interpoliert auf 365 Kalendertage (Port von interpolate_to_365). */
  _interpolateTo365: function(days, values) {
    var full = [];
    for (var target = 1; target <= 365; target++) {
      var idx = days.indexOf(target);
      if (idx >= 0) { full.push(values[idx]); continue; }
      if (target < days[0]) { full.push(values[0]); continue; }
      if (target > days[days.length - 1]) { full.push(values[values.length - 1]); continue; }
      // Interpolieren
      var prevIdx = -1, nextIdx = -1;
      for (var j = 0; j < days.length; j++) {
        if (days[j] < target) prevIdx = j;
        if (days[j] > target && nextIdx < 0) nextIdx = j;
      }
      if (prevIdx >= 0 && nextIdx >= 0) {
        var w = (target - days[prevIdx]) / (days[nextIdx] - days[prevIdx]);
        full.push(values[prevIdx] + w * (values[nextIdx] - values[prevIdx]));
      } else {
        full.push(values[values.length - 1]);
      }
    }
    return full;
  },

  // ── Mondphasen (Port von shared/central_banks.py) ──

  /** Bekannter Neumond + Synodischer Monat */
  _KNOWN_NEW_MOON: new Date(2000, 0, 6, 18, 14), // 6. Jan 2000 UTC
  _SYNODIC_MONTH: 29.530588853,
  _ANOMALISTIC_MONTH: 27.554551,

  /**
   * Berechnet Voll-/Neumond-Daten (Meeus-Algorithmus, ±1 Tag).
   * @param {number} startYear
   * @param {number} endYear
   * @param {string} filter - "full", "new", oder "all" (default)
   * @returns {Array} [{date: "YYYY-MM-DD", phase: "full"/"new"}, ...]
   */
  getMoonDates: function(startYear, endYear, filter) {
    filter = filter || 'all';
    var results = [];
    var known = SA.seasonal._KNOWN_NEW_MOON.getTime();
    var syn = SA.seasonal._SYNODIC_MONTH;
    var msPerDay = 86400000;

    var startMs = new Date(startYear, 0, 1).getTime();
    var endMs = new Date(endYear + 1, 0, 1).getTime();
    var kStart = Math.floor((startMs - known) / (syn * msPerDay)) - 1;
    var kEnd = Math.ceil((endMs - known) / (syn * msPerDay)) + 1;

    for (var k = kStart; k <= kEnd; k++) {
      // Neumond
      var newMs = known + k * syn * msPerDay;
      var newD = new Date(newMs);
      var newY = newD.getFullYear();
      if (newY >= startYear && newY <= endYear && filter !== 'full') {
        results.push({ date: SA.seasonal._fmtDate(newD), phase: 'new' });
      }
      // Vollmond = Neumond + halber synodischer Monat
      var fullMs = newMs + syn / 2 * msPerDay;
      var fullD = new Date(fullMs);
      var fullY = fullD.getFullYear();
      if (fullY >= startYear && fullY <= endYear && filter !== 'new') {
        results.push({ date: SA.seasonal._fmtDate(fullD), phase: 'full' });
      }
    }
    results.sort(function(a, b) { return a.date < b.date ? -1 : a.date > b.date ? 1 : 0; });
    // Duplikate entfernen
    var seen = {};
    return results.filter(function(r) { var k = r.date + r.phase; if (seen[k]) return false; seen[k] = true; return true; });
  },

  /** Supermond-Klassifizierung (Perigaeum-Naehe). */
  isSupermoon: function(dateStr) {
    var d = new Date(dateStr);
    var deltaDays = (d.getTime() - SA.seasonal._KNOWN_NEW_MOON.getTime()) / 86400000;
    var anomalyPhase = (deltaDays % SA.seasonal._ANOMALISTIC_MONTH) / SA.seasonal._ANOMALISTIC_MONTH;
    if (anomalyPhase < 0) anomalyPhase += 1;
    return anomalyPhase < 0.10 || anomalyPhase > 0.90;
  },

  /**
   * Mondphasen-Effekt Analyse (Port von analyze_moon_effect).
   * @param {Array} rows - [{date, close, log_return}] sortiert
   * @param {Array} moonDates - [{date, phase}] von getMoonDates
   * @param {number} daysBefore
   * @param {number} daysAfter
   * @returns {Object|null} {avg_curve, all_curves, labels, stats, best, worst}
   */
  analyzeMoonEffect: function(rows, moonDates, daysBefore, daysAfter) {
    daysBefore = daysBefore || 5;
    daysAfter = daysAfter || 5;
    var windowSize = daysBefore + 1 + daysAfter;
    var t0Idx = daysBefore;

    // Index: date → position in rows
    var dateIdx = {};
    for (var i = 0; i < rows.length; i++) dateIdx[rows[i].date] = i;

    var allCurves = [];

    for (var mi = 0; mi < moonDates.length; mi++) {
      var moon = moonDates[mi];
      // t0 = Mondtag oder vorheriger Handelstag
      var t0Pos = dateIdx[moon.date];
      if (t0Pos === undefined) {
        // Binaere Suche: naechsten vorherigen Handelstag finden
        var lo = 0, hi = rows.length - 1;
        while (lo <= hi) {
          var mid = (lo + hi) >> 1;
          if (rows[mid].date <= moon.date) lo = mid + 1;
          else hi = mid - 1;
        }
        t0Pos = hi >= 0 ? hi : undefined;
      }
      if (t0Pos === undefined) continue;

      var startPos = t0Pos - daysBefore;
      var endPos = t0Pos + daysAfter + 1;
      if (startPos < 0 || endPos > rows.length) continue;

      var window = rows.slice(startPos, endPos);
      if (window.length !== windowSize) continue;

      // Log-Returns kumulieren (1:1 wie Python)
      var logRets = [];
      for (var wi = 0; wi < window.length; wi++) {
        logRets.push(window[wi].log_return != null ? window[wi].log_return
          : (wi > 0 && window[wi - 1].close > 0 ? Math.log(window[wi].close / window[wi - 1].close) : 0));
      }
      var cumLog = [0];
      for (var ci = 0; ci < logRets.length - 1; ci++) cumLog.push(cumLog[ci] + logRets[ci]);
      var rawCurve = cumLog.map(function(v) { return 100 * Math.exp(v); });

      var t0Val = rawCurve[t0Idx];
      var curve = rawCurve.map(function(v) { return Math.round((v / t0Val - 1) * 10000) / 100; });
      var totalReturn = curve[curve.length - 1] - curve[0];

      allCurves.push({
        year: parseInt(moon.date.substring(0, 4)),
        date: moon.date,
        phase: moon.phase,
        curve: curve,
        total_return: Math.round(totalReturn * 100) / 100
      });
    }

    if (allCurves.length === 0) return null;

    // Durchschnittskurve
    var avgCurve = new Array(windowSize).fill(0);
    for (var ai = 0; ai < allCurves.length; ai++)
      for (var aj = 0; aj < windowSize; aj++) avgCurve[aj] += (allCurves[ai].curve[aj] || 0);
    avgCurve = avgCurve.map(function(v) { return Math.round(v / allCurves.length * 100) / 100; });

    // Labels
    var labels = [];
    for (var li = -daysBefore; li <= daysAfter; li++)
      labels.push(li === 0 ? 't0' : (li < 0 ? 't' + li : 't+' + li));

    // Statistiken
    var returns = allCurves.map(function(c) { return c.total_return; });
    returns.sort(function(a, b) { return a - b; });
    var sum = returns.reduce(function(s, v) { return s + v; }, 0);
    var avg = sum / returns.length;
    var med = returns[Math.floor(returns.length / 2)];
    var winning = returns.filter(function(r) { return r > 0; }).length;
    var variance = returns.reduce(function(s, v) { return s + (v - avg) * (v - avg); }, 0) / returns.length;

    var best = allCurves[0], worst = allCurves[0];
    for (var bi = 1; bi < allCurves.length; bi++) {
      if (allCurves[bi].total_return > best.total_return) best = allCurves[bi];
      if (allCurves[bi].total_return < worst.total_return) worst = allCurves[bi];
    }

    return {
      avg_curve: avgCurve, all_curves: allCurves, labels: labels,
      stats: {
        avg_return: Math.round(avg * 100) / 100, median_return: Math.round(med * 100) / 100,
        win_rate: Math.round(winning / returns.length * 10000) / 100,
        std_dev: Math.round(Math.sqrt(variance) * 100) / 100,
        max_gain: Math.round(returns[returns.length - 1] * 100) / 100,
        max_loss: Math.round(returns[0] * 100) / 100,
        total_windows: allCurves.length, winning: winning, losing: returns.length - winning
      },
      best: best, worst: worst
    };
  },

  _fmtDate: function(d) {
    var m = d.getMonth() + 1;
    var day = d.getDate();
    return d.getFullYear() + '-' + (m < 10 ? '0' : '') + m + '-' + (day < 10 ? '0' : '') + day;
  }
};

window.SA = SA;

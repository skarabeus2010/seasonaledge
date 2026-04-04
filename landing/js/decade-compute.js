/**
 * SeasonAlpha — Dekadenzyklus Client-Side Computation
 * =====================================================
 * Berechnet alle Dekaden-Daten aus rohen Supabase-Preisdaten.
 * Erzeugt dasselbe D-Objekt-Format wie generate_decade_data.py.
 *
 * Nutzt: date, close, log_return (aus DB), tdom, tdoy (aus DB)
 */

var SA = window.SA || {};

SA.decadeCompute = {

  /**
   * Berechnet komplette Dekadendaten aus Supabase-Rows.
   * @param {Array} rows - [{date, close, log_return, tdom, tdoy}, ...]
   * @param {string} ticker - Ticker-Symbol
   * @param {number} volaWindow - Rolling-Vola Fenster (Tage)
   * @returns {Object} D-Objekt (identisch zum JSON-Format)
   */
  fromPrices: function(rows, ticker, volaWindow) {
    volaWindow = volaWindow || 20;

    // Sortieren nach Datum
    rows.sort(function(a, b) { return a.date < b.date ? -1 : a.date > b.date ? 1 : 0; });

    var currentYear = new Date().getFullYear();
    var currentDigit = currentYear % 10;

    // Nach Jahr gruppieren
    var yearGroups = {};
    for (var i = 0; i < rows.length; i++) {
      var r = rows[i];
      var y = parseInt(r.date.substring(0, 4));
      if (!yearGroups[y]) yearGroups[y] = [];
      yearGroups[y].push(r);
    }

    // Gueltige Jahre (>=200 Handelstage, Close > 0)
    var validYears = [];
    for (var y in yearGroups) {
      if (yearGroups[y].length >= 200 && yearGroups[y][0].close > 0) {
        validYears.push(parseInt(y));
      }
    }
    validYears.sort(function(a, b) { return a - b; });

    // Dekaden-Kohorten berechnen
    var decades = {};
    for (var digit = 0; digit < 10; digit++) {
      var yearsInCohort = validYears.filter(function(y) { return y % 10 === digit; });
      var curves = [];
      var returns = [];
      var individualCurves = [];

      for (var yi = 0; yi < yearsInCohort.length; yi++) {
        var year = yearsInCohort[yi];
        var yRows = yearGroups[year];
        if (!yRows || yRows.length < 200) continue;

        var closes = yRows.map(function(r) { return r.close; });
        if (closes[0] <= 0) continue;

        // Log-Returns normiert auf 0%
        var logBase = Math.log(closes[0]);
        var logCurve = closes.map(function(c) { return (Math.log(c) - logBase) * 100; });

        // Interpolieren auf 252 Punkte
        logCurve = SA.decadeCompute._interpolate(logCurve, 252);

        curves.push(logCurve);
        individualCurves.push(logCurve.map(function(v) { return Math.round(v * 10) / 10; }));
        returns.push(Math.round(logCurve[251] * 100) / 100);
      }

      var n = curves.length;
      if (n === 0) {
        decades[digit] = {
          years: [], n: 0, avg_curve: [], std_curve: [],
          avg_return: 0, median_return: 0, win_rate: 0,
          volatility: 0, returns: [], individual_curves: [],
          dd_avg_curve: [], dd_worst: 0, vola_avg_curve: []
        };
        continue;
      }

      // Avg + Std Kurven
      var avgCurve = SA.decadeCompute._meanAxis0(curves);
      var stdCurve = SA.decadeCompute._stdAxis0(curves);

      // Smoothing (5-Tage MA)
      var avgSmooth = SA.decadeCompute._movingAvg(avgCurve, 5);

      // Drawdown pro Jahr -> Durchschnitt
      var ddCurves = curves.map(function(c) { return SA.decadeCompute.computeDrawdown(c, 100); });
      var ddAvg = SA.decadeCompute._meanAxis0(ddCurves);
      var ddWorst = -Infinity;
      for (var di = 0; di < ddCurves.length; di++) {
        var minDD = Math.min.apply(null, ddCurves[di]);
        if (minDD < ddWorst) ddWorst = minDD;
      }

      // Rolling Vola pro Jahr -> Durchschnitt
      var volaCurves = [];
      for (var vi = 0; vi < yearsInCohort.length; vi++) {
        var vyear = yearsInCohort[vi];
        var vyRows = yearGroups[vyear];
        if (!vyRows || vyRows.length < volaWindow + 10) continue;

        // Nutze log_return aus DB wenn vorhanden, sonst berechnen
        var dailyRet = [];
        for (var ri = 1; ri < vyRows.length; ri++) {
          if (vyRows[ri].log_return != null) {
            dailyRet.push(vyRows[ri].log_return * 100);
          } else {
            var prev = vyRows[ri - 1].close;
            dailyRet.push(prev > 0 ? (vyRows[ri].close / prev - 1) * 100 : 0);
          }
        }

        var rollingVola = SA.decadeCompute._rollingStd(dailyRet, volaWindow);
        // Annualisieren
        var sqrt252 = Math.sqrt(252);
        var annualized = rollingVola.map(function(v) { return v * sqrt252; });

        if (annualized.length > 0) {
          volaCurves.push(SA.decadeCompute._interpolate(annualized, 252));
        }
      }
      var volaAvg = volaCurves.length > 0 ? SA.decadeCompute._meanAxis0(volaCurves) : [];

      // Statistiken
      var sortedRet = returns.slice().sort(function(a, b) { return a - b; });
      var medianReturn = sortedRet[Math.floor(sortedRet.length / 2)];
      var avgReturn = returns.reduce(function(s, v) { return s + v; }, 0) / n;
      var winRate = returns.filter(function(r) { return r > 0; }).length / n * 100;
      var retMean = avgReturn;
      var retVariance = returns.reduce(function(s, v) { return s + (v - retMean) * (v - retMean); }, 0) / n;
      var volatility = Math.sqrt(retVariance);

      decades[digit] = {
        years: yearsInCohort,
        n: n,
        avg_curve: avgSmooth.map(function(v) { return Math.round(v * 100) / 100; }),
        std_curve: stdCurve.map(function(v) { return Math.round(v * 100) / 100; }),
        avg_return: Math.round(avgReturn * 100) / 100,
        median_return: Math.round(medianReturn * 100) / 100,
        win_rate: Math.round(winRate * 10) / 10,
        volatility: Math.round(volatility * 100) / 100,
        returns: returns,
        individual_curves: individualCurves,
        dd_avg_curve: ddAvg.map(function(v) { return Math.round(v * 100) / 100; }),
        dd_worst: Math.round(ddWorst * 10) / 10,
        vola_avg_curve: volaAvg.map(function(v) { return Math.round(v * 10) / 10; })
      };
    }

    // Aktuelles Jahr
    var currentCurve = [];
    var currentDD = [];
    var cyRows = yearGroups[currentYear];
    if (cyRows && cyRows.length >= 10) {
      var cCloses = cyRows.map(function(r) { return r.close; });
      if (cCloses[0] > 0) {
        var cLogBase = Math.log(cCloses[0]);
        currentCurve = cCloses.map(function(c) { return Math.round((Math.log(c) - cLogBase) * 10000) / 100; });
        currentDD = SA.decadeCompute.computeDrawdown(currentCurve, 100).map(function(v) { return Math.round(v * 100) / 100; });
      }
    }

    // Monats-Heatmap (echte Monate aus date)
    var monthlyHeatmap = {};
    for (var digit = 0; digit < 10; digit++) {
      var mYears = validYears.filter(function(y) { return y % 10 === digit; });
      var monthReturns = [];
      for (var m = 1; m <= 12; m++) {
        var rets = [];
        for (var myi = 0; myi < mYears.length; myi++) {
          var myear = mYears[myi];
          var mRows = (yearGroups[myear] || []).filter(function(r) {
            return parseInt(r.date.substring(5, 7)) === m;
          });
          if (mRows.length >= 10) {
            var mFirst = mRows[0].close;
            var mLast = mRows[mRows.length - 1].close;
            if (mFirst > 0) rets.push((mLast / mFirst - 1) * 100);
          }
        }
        monthReturns.push(rets.length > 0 ? Math.round(rets.reduce(function(s, v) { return s + v; }, 0) / rets.length * 100) / 100 : 0);
      }
      monthlyHeatmap[digit] = monthReturns;
    }

    // DD-Monats-Heatmap (aus dd_avg_curve, je 21 Tage pro Monat)
    var ddMonthlyHeatmap = {};
    for (var digit = 0; digit < 10; digit++) {
      var d = decades[digit];
      if (d.n === 0 || d.dd_avg_curve.length < 252) {
        ddMonthlyHeatmap[digit] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
        continue;
      }
      var mdd = [];
      for (var m = 0; m < 12; m++) {
        var start = m * 21;
        var end = Math.min((m + 1) * 21, 252);
        var slice = d.dd_avg_curve.slice(start, end);
        mdd.push(Math.round(Math.min.apply(null, slice) * 10) / 10);
      }
      ddMonthlyHeatmap[digit] = mdd;
    }

    // Worst-DD-Tabelle (Top 25)
    var worstDDTable = [];
    for (var digit = 0; digit < 10; digit++) {
      var d = decades[digit];
      for (var wi = 0; wi < d.years.length; wi++) {
        if (wi >= d.individual_curves.length) break;
        var wCurve = d.individual_curves[wi];
        var wDD = SA.decadeCompute.computeDrawdown(wCurve.map(Number), 100);
        var maxDD = Math.min.apply(null, wDD);
        if (maxDD < -10) {
          var troughIdx = wDD.indexOf(maxDD);
          var peakIdx = 0;
          var peakVal = -Infinity;
          for (var pi = 0; pi <= troughIdx; pi++) {
            if (wCurve[pi] > peakVal) { peakVal = wCurve[pi]; peakIdx = pi; }
          }
          worstDDTable.push({
            digit: digit,
            year: d.years[wi],
            max_dd: Math.round(maxDD * 10) / 10,
            peak_day: peakIdx,
            trough_day: troughIdx
          });
        }
      }
    }
    worstDDTable.sort(function(a, b) { return a.max_dd - b.max_dd; });
    worstDDTable = worstDDTable.slice(0, 25);

    // Anomalie (vereinfachter Z-Score, kein Isolation Forest client-seitig)
    var anomaly = { score: 0, status: 'normal', return_10d: 0, avg_10d: 0, n_comparisons: 0 };
    if (cyRows && cyRows.length >= 10) {
      var last10 = cyRows.slice(-10);
      var ret10d = last10.length >= 2
        ? (last10[last10.length - 1].close / last10[0].close - 1) * 100 : 0;

      // Historische 10d-Returns am gleichen Kalenderzeitpunkt
      var lastDate = cyRows[cyRows.length - 1].date;
      var doy = SA.decadeCompute._dayOfYear(lastDate);
      var histReturns = [];
      for (var hy = 0; hy < validYears.length; hy++) {
        var hYear = validYears[hy];
        if (hYear === currentYear) continue;
        var hRows = yearGroups[hYear];
        if (!hRows) continue;
        // Finde naechsten Tag zum gleichen DOY
        var hIdx = -1;
        for (var hi = 0; hi < hRows.length; hi++) {
          if (SA.decadeCompute._dayOfYear(hRows[hi].date) >= doy - 5) { hIdx = hi; break; }
        }
        if (hIdx >= 10) {
          var h10 = hRows.slice(hIdx - 10, hIdx);
          if (h10.length >= 2 && h10[0].close > 0) {
            histReturns.push((h10[h10.length - 1].close / h10[0].close - 1) * 100);
          }
        }
      }

      if (histReturns.length >= 5) {
        var hMean = histReturns.reduce(function(s, v) { return s + v; }, 0) / histReturns.length;
        var hVar = histReturns.reduce(function(s, v) { return s + (v - hMean) * (v - hMean); }, 0) / histReturns.length;
        var hStd = Math.sqrt(hVar) || 1;
        var zScore = Math.abs((ret10d - hMean) / hStd);
        var score = Math.min(Math.round(zScore * 30), 100);
        anomaly = {
          score: score,
          status: score >= 40 ? 'anomal' : 'normal',
          return_10d: Math.round(ret10d * 100) / 100,
          avg_10d: Math.round(hMean * 100) / 100,
          n_comparisons: histReturns.length
        };
      }
    }

    return {
      ticker: ticker,
      data_start: validYears.length > 0 ? validYears[0] : 0,
      data_end: validYears.length > 0 ? validYears[validYears.length - 1] : 0,
      total_years: validYears.length,
      current_year: currentYear,
      current_digit: currentDigit,
      vola_window: volaWindow,
      decades: decades,
      current_year_curve: currentCurve,
      current_year_dd: currentDD,
      monthly_heatmap: monthlyHeatmap,
      dd_monthly_heatmap: ddMonthlyHeatmap,
      anomaly: anomaly,
      worst_dd_table: worstDDTable,
      generated_at: new Date().toISOString()
    };
  },

  /**
   * Berechnet Drawdown-Serie aus kumulierter Kurve.
   * @param {Array} curve - Log-Return Kurve (startend bei 0)
   * @param {number} base - Basis (default 100)
   * @returns {Array} Drawdown-Werte (negativ)
   */
  computeDrawdown: function(curve, base) {
    base = base || 100;
    var dd = [];
    var peak = -Infinity;
    for (var i = 0; i < curve.length; i++) {
      var cum = curve[i] + base;
      if (cum > peak) peak = cum;
      dd.push((cum - peak) / peak * 100);
    }
    return dd;
  },

  /**
   * Berechnet Rolling Vola aus DB log_return Spalte.
   * @param {Array} rows - Supabase-Rows fuer ein Jahr
   * @param {number} window - Fenster
   * @returns {Array} Annualisierte Vola-Kurve (252 Punkte)
   */
  computeRollingVola: function(rows, window) {
    var dailyRet = [];
    for (var i = 0; i < rows.length; i++) {
      if (rows[i].log_return != null) {
        dailyRet.push(rows[i].log_return * 100);
      } else if (i > 0 && rows[i - 1].close > 0) {
        dailyRet.push((rows[i].close / rows[i - 1].close - 1) * 100);
      }
    }
    var rollingVola = SA.decadeCompute._rollingStd(dailyRet, window);
    var sqrt252 = Math.sqrt(252);
    var annualized = rollingVola.map(function(v) { return v * sqrt252; });
    return annualized.length > 0 ? SA.decadeCompute._interpolate(annualized, 252) : [];
  },

  /**
   * Berechnet Perzentil-Statistiken.
   * @param {number} value - Aktueller Wert
   * @param {Array} distribution - Historische Werte
   * @returns {Object} {rank, zscore, mean, delta, n}
   */
  computePercentile: function(value, distribution) {
    if (!distribution || distribution.length === 0) {
      return { rank: 50, zscore: 0, mean: 0, delta: 0, n: 0 };
    }
    var n = distribution.length;
    var mean = distribution.reduce(function(s, v) { return s + v; }, 0) / n;
    var variance = distribution.reduce(function(s, v) { return s + (v - mean) * (v - mean); }, 0) / n;
    var std = Math.sqrt(variance) || 1;
    var below = distribution.filter(function(v) { return v <= value; }).length;
    return {
      rank: Math.round(below / n * 100),
      zscore: Math.round((value - mean) / std * 100) / 100,
      mean: Math.round(mean * 100) / 100,
      delta: Math.round((value - mean) * 100) / 100,
      n: n
    };
  },

  // ── Hilfsfunktionen ──

  /** Interpoliert Array auf targetLen Punkte. */
  _interpolate: function(arr, targetLen) {
    var n = arr.length;
    if (n === targetLen) return arr;
    var result = [];
    for (var i = 0; i < targetLen; i++) {
      var pos = i / (targetLen - 1) * (n - 1);
      var lo = Math.floor(pos);
      var hi = Math.min(lo + 1, n - 1);
      var frac = pos - lo;
      result.push(arr[lo] * (1 - frac) + arr[hi] * frac);
    }
    return result;
  },

  /** Mittelwert entlang Achse 0 (Array von Arrays gleicher Laenge). */
  _meanAxis0: function(arrays) {
    if (arrays.length === 0) return [];
    var len = arrays[0].length;
    var result = new Array(len);
    for (var i = 0; i < len; i++) {
      var sum = 0;
      for (var j = 0; j < arrays.length; j++) sum += arrays[j][i];
      result[i] = sum / arrays.length;
    }
    return result;
  },

  /** Standardabweichung entlang Achse 0. */
  _stdAxis0: function(arrays) {
    if (arrays.length === 0) return [];
    var len = arrays[0].length;
    var mean = SA.decadeCompute._meanAxis0(arrays);
    var result = new Array(len);
    for (var i = 0; i < len; i++) {
      var sumSq = 0;
      for (var j = 0; j < arrays.length; j++) {
        var d = arrays[j][i] - mean[i];
        sumSq += d * d;
      }
      result[i] = Math.sqrt(sumSq / arrays.length);
    }
    return result;
  },

  /** Zentrierter Moving Average. */
  _movingAvg: function(arr, window) {
    var half = Math.floor(window / 2);
    var result = [];
    for (var i = 0; i < arr.length; i++) {
      var start = Math.max(0, i - half);
      var end = Math.min(arr.length, i + half + 1);
      var sum = 0;
      for (var j = start; j < end; j++) sum += arr[j];
      result.push(sum / (end - start));
    }
    return result;
  },

  /** Rolling Standard-Abweichung (Population). */
  _rollingStd: function(arr, window) {
    var result = [];
    for (var i = window - 1; i < arr.length; i++) {
      var slice = arr.slice(i - window + 1, i + 1);
      var mean = slice.reduce(function(s, v) { return s + v; }, 0) / window;
      var variance = slice.reduce(function(s, v) { return s + (v - mean) * (v - mean); }, 0) / window;
      result.push(Math.sqrt(variance));
    }
    return result;
  },

  /** Tag des Jahres aus "YYYY-MM-DD" String. */
  _dayOfYear: function(dateStr) {
    var d = new Date(dateStr);
    var start = new Date(d.getFullYear(), 0, 0);
    return Math.floor((d - start) / 86400000);
  }
};

window.SA = SA;

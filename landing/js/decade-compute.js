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
        // Simple Return fuer Statistiken (nie < -100%, intuitiver als Log-Return)
        var simpleReturn = (closes[closes.length - 1] / closes[0] - 1) * 100;
        returns.push(Math.round(simpleReturn * 100) / 100);
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

      // Kein Hardcoded-Smoothing mehr — Smoothing ist UI-gesteuert (Sidebar-Slider in dekadenzyklus.html)
      var avgSmooth = avgCurve;

      // Drawdown pro Jahr -> Durchschnitt
      var ddCurves = curves.map(function(c) { return SA.decadeCompute.computeDrawdown(c, 100); });
      var ddAvg = SA.decadeCompute._meanAxis0(ddCurves);
      var ddWorst = 0;
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

    // Worst-DD-Tabelle (Top 25) — echte Rohdaten + Recovery UEBER Jahresende hinaus
    var worstDDTable = [];
    for (var wyi = 0; wyi < validYears.length; wyi++) {
      var wyear = validYears[wyi];
      var wRows = yearGroups[wyear];
      if (!wRows || wRows.length < 50) continue;
      var wCloses = wRows.map(function(r) { return r.close; });
      // Max DD innerhalb des Jahres berechnen
      var wPeak = 0, wMaxDD = 0, wPeakIdx = 0, wTroughIdx = 0;
      for (var wi = 0; wi < wCloses.length; wi++) {
        if (wCloses[wi] > wPeak) { wPeak = wCloses[wi]; wPeakIdx = wi; }
        var dd = (wCloses[wi] - wPeak) / wPeak * 100;
        if (dd < wMaxDD) { wMaxDD = dd; wTroughIdx = wi; }
      }
      if (wMaxDD > -10) continue; // Nur signifikante DDs
      // Peak-Datum = hoechster Kurs VOR dem Trough
      var realPeakIdx = 0, realPeakVal = 0;
      for (var rpi = 0; rpi <= wTroughIdx; rpi++) {
        if (wCloses[rpi] > realPeakVal) { realPeakVal = wCloses[rpi]; realPeakIdx = rpi; }
      }
      var peakDate = wRows[realPeakIdx].date;
      var troughDate = wRows[wTroughIdx].date;
      var peakPrice = wCloses[realPeakIdx];
      // Recovery: UEBER Jahresende hinaus suchen (wie Python compute_real_recovery)
      var recoveryDays = 0;
      var recovered = false;
      // Ab Trough-Datum in ALLEN Rows suchen (nicht nur aktuelles Jahr)
      for (var ryi = wyi; ryi < validYears.length && !recovered; ryi++) {
        var rRows = yearGroups[validYears[ryi]];
        if (!rRows) continue;
        for (var rri = 0; rri < rRows.length; rri++) {
          if (rRows[rri].date < troughDate) continue;
          if (rRows[rri].date === troughDate) continue; // Trough selbst ueberspringen
          recoveryDays++;
          if (rRows[rri].close >= peakPrice) { recovered = true; break; }
        }
      }
      // Formatierung: >12 Mon → Jahre + Monate + Tage
      var recStr = SA.decadeCompute._formatRecovery(recoveryDays, recovered);

      worstDDTable.push({
        digit: wyear % 10,
        year: wyear,
        max_dd: Math.round(wMaxDD * 10) / 10,
        peak_date: SA.decadeCompute._formatDate(peakDate),
        trough_date: SA.decadeCompute._formatDate(troughDate),
        recovery_str: recStr,
        recovered: recovered
      });
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
        // Perzentil-Rang der aktuellen 10d-Rendite in der Verteilung historischer 10d-Returns
        var sortedHist = histReturns.slice().sort(function(a, b) { return a - b; });
        var rankCount = 0;
        for (var ri = 0; ri < sortedHist.length; ri++) { if (sortedHist[ri] <= ret10d) rankCount = ri + 1; }
        var percentileRank = Math.round(rankCount / sortedHist.length * 100);
        anomaly = {
          score: score,
          status: score >= 40 ? 'anomal' : 'normal',
          return_10d: Math.round(ret10d * 100) / 100,
          avg_10d: Math.round(hMean * 100) / 100,
          n_comparisons: histReturns.length,
          percentile_rank: percentileRank
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

  /** Recovery-Tage formatieren: "3T", "2M 5T", "1J 3M 25T", "nicht erholt (>2J 1M)" */
  _formatRecovery: function(days, recovered) {
    var _en = !!(SA.i18n && SA.i18n.isEN && SA.i18n.isEN());
    var totalMon = Math.floor(days / 21);
    var restDays = days % 21;
    var years = Math.floor(totalMon / 12);
    var months = totalMon % 12;
    var parts = [];
    if (years > 0) parts.push(years + (_en ? 'Y' : 'J'));
    if (months > 0) parts.push(months + 'M');
    if (restDays > 0 || parts.length === 0) parts.push(restDays + (_en ? 'd' : 'T'));
    var str = parts.join(' ');
    return recovered ? str : (_en ? SA.i18n.t('dc.not_recovered') : 'nicht erholt') + ' (>' + str + ')';
  },

  /** "YYYY-MM-DD" → "DD.MM.YYYY" */
  _formatDate: function(dateStr) {
    if (!dateStr || dateStr.length < 10) return dateStr || '';
    return dateStr.substring(8, 10) + '.' + dateStr.substring(5, 7) + '.' + dateStr.substring(0, 4);
  },

  /** Tag des Jahres aus "YYYY-MM-DD" String. */
  _dayOfYear: function(dateStr) {
    var d = new Date(dateStr);
    var start = new Date(d.getFullYear(), 0, 0);
    return Math.floor((d - start) / 86400000);
  },

  // ═══════════════════════════════════════════════════════════════════
  // Shared Anomalie-Radar Renderer (wiederverwendbar auf allen Pages)
  // ═══════════════════════════════════════════════════════════════════

  /** CSS fuer Anomalie-Sektion einmalig in den Head injizieren. Idempotent. */
  _ensureAnomalyCss: function() {
    if (document.getElementById('sa-anomaly-css')) return;
    var css = [
      '.sa-anom-row{display:grid;grid-template-columns:repeat(5,minmax(min(140px,100%),1fr));gap:.75rem;margin-bottom:0}',
      '@media(max-width:900px){.sa-anom-row{grid-template-columns:repeat(auto-fit,minmax(min(140px,100%),1fr))}}',
      '@media(max-width:640px){.sa-anom-row{grid-template-columns:repeat(2,minmax(0,1fr));gap:.5rem}}',
      '@media(max-width:380px){.sa-anom-row{grid-template-columns:1fr}}',
      '.sa-anom-sum{position:relative}',
      '.sa-anom-badge{display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:50%;background:rgba(232,168,32,.15);border:1px solid rgba(232,168,32,.5);color:var(--accent);font-size:.75rem;font-weight:700;font-family:var(--f-d);margin-left:.5rem;cursor:help;vertical-align:middle;line-height:1;user-select:none}',
      '.sa-anom-badge:hover,.sa-anom-badge:focus,.sa-anom-badge:focus-visible{background:rgba(232,168,32,.28);border-color:var(--accent);outline:none}',
      '.sa-anom-tooltip{position:absolute;top:calc(100% + .4rem);right:1rem;left:auto;width:min(420px,calc(100vw - 2rem));max-width:calc(100vw - 2rem);background:var(--elevated,#111115);border:1px solid rgba(232,168,32,.35);border-radius:10px;padding:.85rem 1rem;font-size:.75rem;line-height:1.55;color:var(--dim,#e8e0d0);box-shadow:0 12px 32px rgba(0,0,0,.6);z-index:50;opacity:0;visibility:hidden;transform:translateY(-4px);transition:opacity .15s ease,transform .15s ease,visibility .15s ease;pointer-events:none;font-weight:400;text-transform:none;letter-spacing:normal}',
      '.sa-anom-badge:hover ~ .sa-anom-tooltip,.sa-anom-tooltip:hover{opacity:1;visibility:visible;transform:translateY(0);pointer-events:auto}',
      '@media(hover:none){.sa-anom-badge:focus ~ .sa-anom-tooltip,.sa-anom-badge:focus-visible ~ .sa-anom-tooltip{opacity:1;visibility:visible;transform:translateY(0);pointer-events:auto}}',
      '.sa-anom-tooltip b{color:var(--text,#fff);font-weight:700}',
      '.sa-anom-tooltip p{margin:0 0 .5rem 0}',
      '.sa-anom-tooltip p:last-child{margin-bottom:0}',
      // Perzentil-Slider (rot → gold → grün → gold → rot)
      '.sa-anom-prank{display:flex;flex-direction:column;align-items:stretch;gap:.35rem;margin-top:.15rem}',
      '.sa-anom-prank-bar{position:relative;height:8px;border-radius:4px;background:linear-gradient(90deg,#ff4040 0%,#ff4040 10%,#e8a820 20%,#30e878 30%,#30e878 70%,#e8a820 80%,#ff4040 90%,#ff4040 100%);box-shadow:inset 0 1px 2px rgba(0,0,0,.4)}',
      '.sa-anom-prank-mark{position:absolute;top:-3px;width:3px;height:14px;background:#fff;border-radius:2px;box-shadow:0 0 0 1px rgba(0,0,0,.6),0 0 6px rgba(255,255,255,.5);transform:translateX(-50%);transition:left .3s ease}',
      '.sa-anom-prank-label{font-family:var(--f-d,sans-serif);font-size:1rem;font-weight:700;text-align:center;line-height:1}',
      '.sa-anom-prank-scale{display:flex;justify-content:space-between;font-size:.625rem;color:var(--muted,#a89878);font-family:var(--f-m,monospace);margin-top:.1rem}'
    ].join('\n');
    var style = document.createElement('style');
    style.id = 'sa-anomaly-css';
    style.textContent = css;
    document.head.appendChild(style);
  },

  /** Info-Badge ins <summary> des umgebenden <details> einfuegen (idempotent). */
  _injectAnomalySummaryBadge: function(containerEl) {
    if (!containerEl || !containerEl.closest) return;
    var details = containerEl.closest('details');
    if (!details) return;
    var summary = details.querySelector('summary');
    if (!summary) return;
    if (summary.querySelector('.sa-anom-badge')) return; // schon drin → idempotent
    summary.classList.add('sa-anom-sum');
    var _isEN = window.location.pathname.indexOf('/en/') === 0 || window.location.pathname === '/en';
    var tooltipHtml = _isEN
      ? '<p><b>Methodology:</b> Z-score comparison of the last 10-day return vs. all historical 10d-returns at the same calendar point.</p>' +
        '<p>The <b>Score</b> measures how many standard deviations the current trajectory is from the historical mean (&ge;40 = slightly anomalous, &ge;70 = strongly anomalous).</p>' +
        '<p>The <b>Percentile Rank</b> shows where the current 10d-return stands in the historical distribution — the 90th percentile means: higher than 90&nbsp;% of all comparable historical windows.</p>' +
        '<p>A high score or extreme percentile does not mean bullish or bearish — it only means &ldquo;the current trajectory is unusual&rdquo;.</p>'
      : '<p><b>Methodik:</b> Z-Score-Vergleich der letzten 10-Tages-Rendite gegen alle historischen 10d-Returns am gleichen Kalenderzeitpunkt.</p>' +
        '<p>Der <b>Score</b> misst wie viele Standardabweichungen der aktuelle Verlauf vom historischen Mittel entfernt ist (&ge;40 = leicht anomal, &ge;70 = stark anomal).</p>' +
        '<p>Der <b>Perzentil-Rang</b> zeigt komplementär, wo die aktuelle 10d-Rendite in der historischen Verteilung steht &mdash; das 90. Perzentil bedeutet: höher als 90&nbsp;% aller vergleichbaren historischen Fenster.</p>' +
        '<p>Ein hoher Score oder extremer Perzentil bedeutet nicht bullish oder bearish, sondern nur &bdquo;der Verlauf ist ungewöhnlich".</p>';
    var badge = document.createElement('span');
    badge.className = 'sa-anom-badge';
    badge.setAttribute('aria-label', _isEN ? 'Anomaly Radar methodology' : 'Methodik des Anomalie-Radars');
    badge.setAttribute('tabindex', '0'); // Touch-Focus für Mobile
    badge.setAttribute('role', 'button');
    badge.textContent = '\u24D8'; // ⓘ
    var tooltip = document.createElement('span');
    tooltip.className = 'sa-anom-tooltip';
    tooltip.innerHTML = tooltipHtml;
    summary.appendChild(badge);
    summary.appendChild(tooltip);
  },

  /**
   * Haupt-Entry-Point: Rendert den kompletten Anomalie-Radar (5 KPI-Cards +
   * Info-Badge im Summary des umgebenden <details>) in das angegebene Container-Element.
   * @param {string} containerId - ID des Ziel-divs (z.B. 'content-anomaly')
   * @param {Array} rows - Preisrows [{date, close, log_return?}, ...]
   * @param {string} ticker - Ticker fuer KPI-Label
   */
  renderAnomalyInto: function(containerId, rows, ticker) {
    var el = document.getElementById(containerId);
    if (!el) return;
    this._ensureAnomalyCss();
    this._injectAnomalySummaryBadge(el);

    var anom = null;
    try {
      if (rows && rows.length >= 200) {
        var dec = this.fromPrices(rows.slice(), ticker);
        anom = dec ? dec.anomaly : null;
      }
    } catch (e) { console.warn('[anomaly] compute failed:', e); }

    var _en = !!(SA.i18n && SA.i18n.isEN && SA.i18n.isEN());
    if (!anom || anom.n_comparisons === 0) {
      el.innerHTML = '<p style="color:var(--muted);font-size:.875rem;margin:0">' +
        (_en ? SA.i18n.t('dc.anomaly_unavailable') : 'Anomalie-Score nicht berechenbar (zu wenig historische Vergleichsfenster).') +
        '</p>';
      return;
    }

    var fmtPct = function(v) { if (v == null || isNaN(v)) return '–'; return (v >= 0 ? '+' : '') + v.toFixed(2) + '%'; };
    var scoreCls = anom.score >= 70 ? 'red' : anom.score >= 40 ? 'gold' : 'green';
    var statusLabel = _en
      ? (anom.score >= 70 ? SA.i18n.t('dc.status_strongly_anomalous') : anom.score >= 40 ? SA.i18n.t('dc.status_slightly_anomalous') : SA.i18n.t('dc.status_normal'))
      : (anom.score >= 70 ? 'Stark anomal' : anom.score >= 40 ? 'Leicht anomal' : 'Normal');
    var retCls = anom.return_10d >= 0 ? 'green' : 'red';

    var pRank = anom.percentile_rank;
    var pRankCell;
    var _pRankLabel = _en ? SA.i18n.t('dc.percentile_rank') : 'Perzentil-Rang';
    if (pRank == null) {
      pRankCell = '<div class="kpi"><div class="kpi-label">' + _pRankLabel + '</div><div class="kpi-value">&ndash;</div></div>';
    } else {
      var pRankCls = (pRank < 10 || pRank > 90) ? 'red' : (pRank < 20 || pRank > 80) ? 'gold' : 'green';
      var pRankText = _en ? pRank + SA.i18n.t('dc.percentile_suffix') : pRank + '. Perzentil';
      pRankCell = '<div class="kpi"><div class="kpi-label">' + _pRankLabel + '</div>' +
        '<div class="sa-anom-prank">' +
          '<div class="sa-anom-prank-label ' + pRankCls + '">' + pRankText + '</div>' +
          '<div class="sa-anom-prank-bar" title="' + pRankText + '">' +
            '<div class="sa-anom-prank-mark" style="left:' + pRank + '%"></div>' +
          '</div>' +
          '<div class="sa-anom-prank-scale"><span>0</span><span>50</span><span>100</span></div>' +
        '</div>' +
      '</div>';
    }

    var _retLabel = _en ? SA.i18n.t('dc.return_10d') + ' ' : '10d-Rendite ';
    var _avgLabel = _en ? SA.i18n.t('dc.historical_avg') : 'Historisch &Oslash;';
    var html = '<div class="sa-anom-row">' +
      '<div class="kpi"><div class="kpi-label">Score</div><div class="kpi-value ' + scoreCls + '">' + anom.score + ' / 100</div></div>' +
      '<div class="kpi"><div class="kpi-label">Status</div><div class="kpi-value ' + scoreCls + '">' + statusLabel + '</div></div>' +
      '<div class="kpi"><div class="kpi-label">' + _retLabel + (ticker || '') + '</div><div class="kpi-value ' + retCls + '">' + fmtPct(anom.return_10d) + '</div></div>' +
      '<div class="kpi"><div class="kpi-label">' + _avgLabel + '</div><div class="kpi-value">' + fmtPct(anom.avg_10d) + '</div></div>' +
      pRankCell +
    '</div>';
    el.innerHTML = html;
  }
};

window.SA = SA;

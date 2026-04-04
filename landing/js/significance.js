/**
 * SeasonAlpha — Significance Tests (Port von shared/significance_gauge.py)
 * =========================================================================
 * t-Test, Cohen's d, Relevanz-Score + HTML Gauge Rendering.
 * Wird von: Monatswechsel, Mondphasen, Wochentage, Monatszyklus genutzt.
 */

var SA = window.SA || {};

SA.significance = {

  /**
   * Fuehrt einen 1-Sample t-Test fuer jede Gruppe durch.
   * (1:1 Port von run_significance_test)
   *
   * @param {Object} groups - {"Montag": [0.1, -0.2, ...], "Freitag": [...]}
   * @param {number} testValue - Vergleichswert (default 0)
   * @returns {Array} [{name, avg_return, win_rate, n, t_stat, p_value, cohens_d, relevance}]
   *                  sortiert nach Relevanz (absteigend)
   */
  runSignificanceTest: function(groups, testValue) {
    testValue = testValue || 0;
    var results = [];

    for (var name in groups) {
      var returns = groups[name].filter(function(r) { return r !== null && r !== undefined && !isNaN(r); });
      if (returns.length < 5) continue;

      var n = returns.length;
      var sum = 0;
      for (var i = 0; i < n; i++) sum += returns[i];
      var avg = sum / n;

      // Std (ddof=1, sample std)
      var sumSq = 0;
      for (var i = 0; i < n; i++) sumSq += (returns[i] - avg) * (returns[i] - avg);
      var std = Math.sqrt(sumSq / (n - 1));

      var wins = 0;
      for (var i = 0; i < n; i++) if (returns[i] > 0) wins++;

      // t-Statistik: t = (mean - test_value) / (std / sqrt(n))
      var tStat = std > 0 ? (avg - testValue) / (std / Math.sqrt(n)) : 0;

      // p-Wert (two-tailed) aus t-Verteilung
      var pValue = SA.significance._tTestPValue(Math.abs(tStat), n - 1);

      // Cohen's d
      var cohensD = std > 0 ? Math.abs(avg - testValue) / std : 0;

      // Relevanz-Score (gewichtet wie Python)
      var significance = Math.max(0, 1 - pValue);
      var winComponent = wins / n;
      var effectComponent = Math.min(cohensD, 1.0);
      var relevance = 0.5 * significance + 0.3 * winComponent + 0.2 * effectComponent;

      results.push({
        name: name,
        avg_return: Math.round(avg * 10000) / 10000,
        win_rate: Math.round(wins / n * 1000) / 10,
        n: n,
        t_stat: Math.round(tStat * 1000) / 1000,
        p_value: Math.round(pValue * 10000) / 10000,
        cohens_d: Math.round(cohensD * 1000) / 1000,
        relevance: Math.round(relevance * 1000) / 1000
      });
    }

    results.sort(function(a, b) { return b.relevance - a.relevance; });
    return results;
  },

  /**
   * Signifikanz-Label aus p-Wert.
   */
  sigLabel: function(pValue) {
    if (pValue < 0.01) return { text: 'Hochsignifikant', color: '#00d4aa' };
    if (pValue < 0.05) return { text: 'Signifikant', color: '#00d4aa' };
    if (pValue < 0.10) return { text: 'Grenzwertig', color: '#e8a425' };
    return { text: 'Nicht signifikant', color: '#ff4757' };
  },

  /**
   * Farbverlauf fuer Score: 0=Rot → 0.5=Orange → 1=Gruen
   */
  scoreToColor: function(score) {
    score = Math.max(0, Math.min(1, score));
    var r, g, b;
    if (score <= 0.5) {
      var t = score / 0.5;
      r = Math.round(204 + (232 - 204) * t);
      g = Math.round(0 + (164 - 0) * t);
      b = Math.round(0 + (37 - 0) * t);
    } else {
      var t = (score - 0.5) / 0.5;
      r = Math.round(232 + (0 - 232) * t);
      g = Math.round(164 + (212 - 164) * t);
      b = Math.round(37 + (170 - 37) * t);
    }
    return 'rgb(' + r + ',' + g + ',' + b + ')';
  },

  /**
   * Rendert eine Signifikanz-Sektion als HTML (Gauges + Stats).
   *
   * @param {Array} results - von runSignificanceTest()
   * @param {number} colsPerRow - Gauges pro Reihe (default 4)
   * @returns {string} HTML-String
   */
  /**
   * @param {Array} results
   * @param {number} colsPerRow
   * @param {Array} sortOrder - optionale feste Reihenfolge (Array von Namen)
   */
  renderSection: function(results, colsPerRow, sortOrder) {
    colsPerRow = colsPerRow || 4;
    if (!results || results.length === 0) return '';
    // Feste Reihenfolge statt Relevanz-Sortierung
    if (sortOrder) {
      var orderMap = {};
      for (var oi = 0; oi < sortOrder.length; oi++) orderMap[sortOrder[oi]] = oi;
      results = results.slice().sort(function(a, b) {
        var ia = orderMap[a.name] !== undefined ? orderMap[a.name] : 999;
        var ib = orderMap[b.name] !== undefined ? orderMap[b.name] : 999;
        return ia - ib;
      });
    }

    var html = '<div style="display:flex;flex-wrap:wrap;gap:.75rem;margin-bottom:1rem">';
    for (var i = 0; i < results.length; i++) {
      var r = results[i];
      var sig = SA.significance.sigLabel(r.p_value);
      var gaugeColor = SA.significance.scoreToColor(r.relevance);
      var avgColor = r.avg_return >= 0 ? '#00d4aa' : '#ff4757';

      var deg = Math.round(r.relevance * 180);

      html += '<div style="flex:1 1 ' + Math.floor(100 / colsPerRow - 2) + '%;min-width:170px;max-width:' + Math.floor(100 / colsPerRow) + '%;background:var(--card,#0a0a0e);border:1px solid var(--border,rgba(232,168,32,.1));border-radius:10px;padding:1rem;text-align:center">';
      // Name
      html += '<div style="color:#e8e0d0;font-weight:700;font-size:.9375rem;margin-bottom:.625rem">' + r.name + '</div>';
      // CSS Gauge (Halbkreis — groesser, Tacho-Stil)
      html += '<div style="position:relative;width:140px;height:75px;margin:0 auto;overflow:hidden">';
      html += '<div style="width:140px;height:140px;border-radius:50%;background:conic-gradient(' + gaugeColor + ' 0deg,' + gaugeColor + ' ' + deg + 'deg,rgba(255,255,255,.06) ' + deg + 'deg,rgba(255,255,255,.06) 360deg);transform:rotate(-90deg)"></div>';
      html += '<div style="position:absolute;bottom:0;left:50%;transform:translateX(-50%);width:100px;height:50px;border-radius:0 0 100px 100px;background:var(--card,#0a0a0e)"></div>';
      html += '<div style="position:absolute;bottom:4px;left:50%;transform:translateX(-50%);font-size:1.375rem;font-weight:700;color:#fff;font-family:var(--f-m,monospace)">' + r.relevance.toFixed(2) + '</div>';
      html += '</div>';
      // Signifikanz-Label (groesser, gut lesbar)
      html += '<div style="color:' + sig.color + ';font-weight:700;font-size:.9375rem;margin-top:.5rem">' + sig.text + '</div>';
      // Stats (weiss, groesser)
      html += '<div style="color:#c8d6e5;font-size:.8125rem;margin-top:.375rem;font-family:var(--f-m,monospace);line-height:1.6">';
      html += 't=' + r.t_stat.toFixed(2) + '  p=' + r.p_value.toFixed(4);
      html += '<br><span style="color:' + avgColor + '">\u00D8 ' + (r.avg_return >= 0 ? '+' : '') + r.avg_return.toFixed(2) + '%</span>  Win ' + r.win_rate.toFixed(0) + '%  n=' + r.n;
      html += '</div></div>';
    }
    html += '</div>';

    // Erklaertext
    html += '<p style="color:#c8d6e5;font-size:.6875rem;border-top:1px solid rgba(255,255,255,.06);padding-top:.5rem">';
    html += '<b>Relevanz-Score</b> = 50% Signifikanz (1-p) + 30% Win-Rate + 20% Effect Size (Cohen\u2019s d). ';
    html += '<b>t-Statistik</b>: Signalst\u00E4rke vs. Null. ';
    html += '<b>p-Wert</b>: Wahrscheinlichkeit f\u00FCr Zufallsergebnis (p&lt;0.05 = signifikant). ';
    html += '<span style="color:#00d4aa"><b>Gr\u00FCn</b></span> = statistisch valide, ';
    html += '<span style="color:#ff4757"><b>Rot</b></span> = wahrscheinlich Zufall.</p>';
    return html;
  },

  // ── t-Verteilung p-Wert (Approximation) ──

  /**
   * Two-tailed p-Wert aus t-Statistik und Freiheitsgraden.
   * Nutzt die Regularized Incomplete Beta Function Approximation.
   */
  _tTestPValue: function(tAbs, df) {
    // Approximation via Beta-Funktion: p = I_x(df/2, 1/2) wobei x = df/(df+t^2)
    var x = df / (df + tAbs * tAbs);
    return SA.significance._regularizedBeta(x, df / 2, 0.5);
  },

  /**
   * Regularized Incomplete Beta Function I_x(a, b).
   * Continued fraction approximation (Lentz's method).
   */
  _regularizedBeta: function(x, a, b) {
    if (x <= 0) return 0;
    if (x >= 1) return 1;

    // Verwende Symmetrie wenn noetig
    if (x > (a + 1) / (a + b + 2)) {
      return 1 - SA.significance._regularizedBeta(1 - x, b, a);
    }

    var lnBeta = SA.significance._lnGamma(a) + SA.significance._lnGamma(b) - SA.significance._lnGamma(a + b);
    var front = Math.exp(Math.log(x) * a + Math.log(1 - x) * b - lnBeta) / a;

    // Continued fraction (Lentz)
    var f = 1, c = 1, d = 1 - (a + b) * x / (a + 1);
    if (Math.abs(d) < 1e-30) d = 1e-30;
    d = 1 / d;
    f = d;

    for (var m = 1; m <= 200; m++) {
      // Even step
      var num = m * (b - m) * x / ((a + 2 * m - 1) * (a + 2 * m));
      d = 1 + num * d; if (Math.abs(d) < 1e-30) d = 1e-30; d = 1 / d;
      c = 1 + num / c; if (Math.abs(c) < 1e-30) c = 1e-30;
      f *= d * c;

      // Odd step
      num = -(a + m) * (a + b + m) * x / ((a + 2 * m) * (a + 2 * m + 1));
      d = 1 + num * d; if (Math.abs(d) < 1e-30) d = 1e-30; d = 1 / d;
      c = 1 + num / c; if (Math.abs(c) < 1e-30) c = 1e-30;
      f *= d * c;

      if (Math.abs(d * c - 1) < 1e-8) break;
    }

    return front * f;
  },

  /** Log-Gamma (Lanczos approximation). */
  _lnGamma: function(z) {
    if (z < 0.5) return Math.log(Math.PI / Math.sin(Math.PI * z)) - SA.significance._lnGamma(1 - z);
    z -= 1;
    var g = 7;
    var coef = [0.99999999999980993, 676.5203681218851, -1259.1392167224028,
                771.32342877765313, -176.61502916214059, 12.507343278686905,
                -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7];
    var x = coef[0];
    for (var i = 1; i < g + 2; i++) x += coef[i] / (z + i);
    var t = z + g + 0.5;
    return 0.5 * Math.log(2 * Math.PI) + (z + 0.5) * Math.log(t) - t + Math.log(x);
  }
};

window.SA = SA;

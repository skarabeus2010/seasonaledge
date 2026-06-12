/**
 * landing/js/dash-compute.js — Dashboard Compute-Kern
 *
 * Wiederverwendbare Berechnungs-Funktionen die ursprünglich inline in
 * dashboard.html standen. Extrahiert für Wiederverwendung durch:
 *   - dashboard.html (Single-Ticker Bento)
 *   - watchlist.html (N-Ticker Compact-Cards)
 *   - spätere Pages die KI-Score/Crash-Ampel brauchen
 *
 * Math/Render-Trennung: dieses Modul macht NUR Berechnungen, keine DOM-Arbeit.
 *
 * Namespace: window.SA.dashCompute
 *
 * Funktionen:
 *   - findMatchingYears(yearData, currentYear, method, topN)
 *       Findet die ähnlichsten Jahre via Pearson-Korrelation oder Euklid.
 *   - computeTruePath(matches, smoothing)
 *       Gewichteter Ø aus den Match-Jahren, geglättet.
 *   - computeKiScore(yearData, matches, currentYear, avg, truepath)
 *       Composite Score 0-10 aus 4 Sub-Scores. Liefert {score, signal, subs}.
 *   - computeRegime(rows)
 *       Crash-Ampel (green/yellow/red + risk_score 0-100 + features).
 *
 * Helper die mit-exportiert werden (weil sie Dashboard-intern genutzt werden):
 *   - mean, stdev, median, corrcoef, euclidean, _clean
 *   - todayDoy, presidentialCycleYear
 *   - MONTH_START_DOY, CYCLE_NAMES
 *
 * HINWEIS: Die Originale in dashboard.html werden durch dieses Modul ersetzt,
 * bleiben aber funktional identisch. Kein Logik-Change.
 */
(function() {
  window.SA = window.SA || {};

  var MONTH_START_DOY = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335];

  function getCycleNames() {
    var _en = !!(SA.i18n && SA.i18n.isEN && SA.i18n.isEN());
    return {
      1: _en ? SA.i18n.t('dc2.cycle_election')     : 'Wahljahr',
      2: _en ? SA.i18n.t('dc2.cycle_post_election') : 'Nachwahljahr',
      3: _en ? SA.i18n.t('dc2.cycle_midterm')       : 'Zwischenwahljahr',
      4: _en ? SA.i18n.t('dc2.cycle_pre_election')  : 'Vorwahljahr'
    };
  }

  // Backward-compat static reference (resolved at access time via getter)
  var CYCLE_NAMES = { 1: 'Wahljahr', 2: 'Nachwahljahr', 3: 'Zwischenwahljahr', 4: 'Vorwahljahr' };

  // ── Array-Helpers (NaN-safe) ──────────────────────────────────
  function _clean(arr) {
    var out = [];
    for (var i = 0; i < arr.length; i++) {
      var v = arr[i];
      if (v != null && typeof v === 'number' && !isNaN(v) && isFinite(v)) out.push(v);
    }
    return out;
  }

  function mean(a) {
    var v = _clean(a);
    if (!v.length) return 0;
    var s = 0;
    for (var i = 0; i < v.length; i++) s += v[i];
    return s / v.length;
  }

  function median(a) {
    var v = _clean(a).slice().sort(function(x, y) { return x - y; });
    if (!v.length) return 0;
    var m = Math.floor(v.length / 2);
    return v.length % 2 ? v[m] : (v[m - 1] + v[m]) / 2;
  }

  function stdev(a) {
    var v = _clean(a);
    if (v.length < 2) return 0;
    var m = mean(v), sq = 0;
    for (var i = 0; i < v.length; i++) sq += (v[i] - m) * (v[i] - m);
    return Math.sqrt(sq / v.length);
  }

  function corrcoef(a, b) {
    var n = Math.min(a.length, b.length);
    if (n < 2) return 0;
    var ma = mean(a.slice(0, n)), mb = mean(b.slice(0, n)), cov = 0, va = 0, vb = 0;
    for (var i = 0; i < n; i++) {
      cov += (a[i] - ma) * (b[i] - mb);
      va += (a[i] - ma) * (a[i] - ma);
      vb += (b[i] - mb) * (b[i] - mb);
    }
    if (va === 0 || vb === 0) return 0;
    return cov / Math.sqrt(va * vb);
  }

  function euclidean(a, b) {
    var n = Math.min(a.length, b.length), s = 0;
    for (var i = 0; i < n; i++) s += (a[i] - b[i]) * (a[i] - b[i]);
    return Math.sqrt(s);
  }

  function todayDoy() {
    var n = new Date();
    return Math.min(365, Math.floor((n - new Date(n.getFullYear(), 0, 0)) / 86400000));
  }

  function presidentialCycleYear(y) {
    return ((y - 2020) % 4 + 4) % 4 + 1;
  }

  // ── Match-Finding + TruePath ──────────────────────────────────
  function findMatchingYears(yearData, currentYear, method, topN) {
    if (!yearData[currentYear]) return [];
    var current = yearData[currentYear].full_365;
    var td = todayDoy();
    var currentSeg = current.slice(0, td);
    if (currentSeg.length < 10) return [];
    var matches = [];
    for (var y in yearData) {
      y = parseInt(y);
      if (y === currentYear) continue;
      var hist = yearData[y].full_365;
      var histSeg = hist.slice(0, td);
      var sim;
      if (method === 'correlation') {
        var c = corrcoef(currentSeg, histSeg);
        sim = Math.max(0, (c + 1) / 2 * 100);
      } else {
        var cm = mean(currentSeg), hm = mean(histSeg), cs = stdev(currentSeg) || 1, hs = stdev(histSeg) || 1;
        var an = currentSeg.map(function(v) { return (v - cm) / cs; });
        var bn = histSeg.map(function(v) { return (v - hm) / hs; });
        var dist = euclidean(an, bn);
        sim = Math.max(0, 100 - dist * 5);
      }
      var fullRet = hist[364] > 0 ? (hist[364] / hist[0] - 1) * 100 : 0;
      matches.push({
        year: y,
        similarity: Math.round(sim * 10) / 10,
        full365: hist,
        returnPct: Math.round(fullRet * 10) / 10,
        cycle: presidentialCycleYear(y)
      });
    }
    matches.sort(function(a, b) { return b.similarity - a.similarity; });
    return matches.slice(0, topN);
  }

  function computeTruePath(matches, smoothing) {
    if (!matches.length) return null;
    var simSum = matches.reduce(function(s, m) { return s + m.similarity; }, 0);
    if (simSum <= 0) return null;
    var truepath = new Array(365).fill(0);
    for (var d = 0; d < 365; d++) {
      var w = 0, sum = 0;
      for (var i = 0; i < matches.length; i++) {
        var m = matches[i], v = m.full365[d];
        if (v != null && isFinite(v)) { sum += v * m.similarity; w += m.similarity; }
      }
      truepath[d] = w > 0 ? sum / w : 100;
    }
    // Glättung
    if (smoothing > 1) {
      var sm = new Array(365);
      var half = Math.floor(smoothing / 2);
      for (var d = 0; d < 365; d++) {
        var s = 0, c = 0;
        for (var k = Math.max(0, d - half); k <= Math.min(364, d + half); k++) { s += truepath[k]; c++; }
        sm[d] = s / c;
      }
      truepath = sm;
    }
    return truepath;
  }

  // ── KI Composite Score ────────────────────────────────────────
  function computeKiScore(yearData, matches, currentYear, avg, truepath) {
    var now = new Date(), currentMonth = now.getMonth() + 1, td = todayDoy();
    var currentCurve = yearData[currentYear] ? yearData[currentYear].full_365 : [];

    // 1) Musterpfad-Qualität
    var posMatches = matches.filter(function(m) { return m.returnPct > 0; }).length;
    var subMusterpfad = matches.length ? posMatches / matches.length : 0.5;

    // 2) Trend-Projektion
    var subTrend = 0.5, trendRet = 0;
    if (truepath && td > 0 && td + 30 < 365) {
      var tpNow = truepath[td], tpFut = truepath[Math.min(364, td + 30)];
      if (tpNow > 0) {
        trendRet = (tpFut - tpNow) / tpNow * 100;
        subTrend = Math.max(0, Math.min(1, (trendRet + 3) / 6));
      }
    }

    // 3) Win-Rate aktueller Monat
    var monStart = MONTH_START_DOY[currentMonth - 1] - 1;
    var monEnd = currentMonth < 12 ? MONTH_START_DOY[currentMonth] - 1 : 365;
    var wins = 0, total = 0, avgMonthRet = 0;
    for (var y in yearData) {
      if (parseInt(y) === currentYear) continue;
      var c = yearData[y].full_365;
      if (c[monStart] > 0 && c[monEnd - 1] > 0) {
        var r = (c[monEnd - 1] / c[monStart] - 1) * 100;
        avgMonthRet += r;
        if (r > 0) wins++;
        total++;
      }
    }
    var subWinRate = total ? wins / total : 0.5;
    avgMonthRet = total ? avgMonthRet / total : 0;

    // 4) Tracking-Qualität
    var subTracking = 0.5, trackingCorr = 0;
    if (currentCurve.length && avg.length && td >= 10) {
      var n = Math.min(td, currentCurve.length, avg.length);
      var c1 = currentCurve.slice(0, n), c2 = avg.slice(0, n);
      trackingCorr = corrcoef(c1, c2);
      var corrScore = Math.max(0, trackingCorr);
      var avgRange = Math.max.apply(null, c2) - Math.min.apply(null, c2);
      var mae = 0;
      if (avgRange > 0) {
        for (var i = 0; i < n; i++) mae += Math.abs(c1[i] - c2[i]);
        mae /= n;
      }
      var normMae = avgRange > 0 ? Math.min(1, mae / avgRange) : 0;
      subTracking = Math.max(0, Math.min(1, 0.7 * corrScore + 0.3 * (1 - normMae)));
    }

    var composite = (subMusterpfad + subTrend + subWinRate + subTracking) * 2.5;
    composite = Math.round(composite * 10) / 10;
    composite = Math.max(0, Math.min(10, composite));
    var signal = composite >= 6.5 ? 'Bullish' : (composite <= 3.5 ? 'Bearish' : 'Neutral');

    return {
      score: composite,
      signal: signal,
      subs: {
        musterpfad: { score: subMusterpfad, posCount: posMatches, total: matches.length },
        trend: { score: subTrend, returnPct: trendRet },
        winRate: { score: subWinRate, wins: wins, total: total, avgReturn: avgMonthRet },
        tracking: { score: subTracking, correlation: trackingCorr }
      }
    };
  }

  // ── Crash-Ampel / Regime ──────────────────────────────────────
  function computeRegime(rows) {
    if (!rows || rows.length < 100) return { traffic_light: 'grey', risk_score: 0, features: {} };
    var n = rows.length, closes = rows.map(function(r) { return r.close; });
    var ret1d = closes[n - 1] / closes[n - 2] - 1;
    var ret5d = closes[n - 1] / closes[Math.max(0, n - 6)] - 1;
    var ret20d = closes[n - 1] / closes[Math.max(0, n - 21)] - 1;

    function vol(window) {
      var rets = [];
      for (var i = Math.max(1, n - window); i < n; i++) rets.push(closes[i] / closes[i - 1] - 1);
      var m = rets.reduce(function(s, v) { return s + v; }, 0) / rets.length;
      var v2 = rets.reduce(function(s, v) { return s + (v - m) * (v - m); }, 0) / rets.length;
      return Math.sqrt(v2) * 100;
    }

    var vol5 = vol(5), vol10 = vol(10), vol20 = vol(20);
    var high20 = 0;
    for (var i = Math.max(0, n - 20); i < n; i++) if (closes[i] > high20) high20 = closes[i];
    var drawdown = (closes[n - 1] - high20) / high20 * 100;

    // Historische Perzentile
    var histScores = [];
    for (var t = Math.max(60, n - 252); t < n; t++) {
      var hr = [];
      for (var j = Math.max(1, t - 5); j <= t; j++) hr.push(closes[j] / closes[j - 1] - 1);
      var hm = hr.reduce(function(s, v) { return s + v; }, 0) / hr.length;
      var hv5 = Math.sqrt(hr.reduce(function(s, v) { return s + (v - hm) * (v - hm); }, 0) / hr.length) * 100;
      hr = [];
      for (var j = Math.max(1, t - 20); j <= t; j++) hr.push(closes[j] / closes[j - 1] - 1);
      hm = hr.reduce(function(s, v) { return s + v; }, 0) / hr.length;
      var hv20 = Math.sqrt(hr.reduce(function(s, v) { return s + (v - hm) * (v - hm); }, 0) / hr.length) * 100;
      var hh = 0;
      for (var j = Math.max(0, t - 20); j <= t; j++) if (closes[j] > hh) hh = closes[j];
      var hdd = (closes[t] - hh) / hh * 100;
      histScores.push(hv5 * 0.3 + hv20 * 0.3 + Math.abs(hdd) * 0.4);
    }

    var currentScore = vol5 * 0.3 + vol20 * 0.3 + Math.abs(drawdown) * 0.4;
    var below = histScores.filter(function(s) { return s < currentScore; }).length;
    var riskScore = Math.round(below / histScores.length * 100);
    var traffic = 'green';
    if (riskScore >= 70) traffic = 'red';
    else if (riskScore >= 40) traffic = 'yellow';

    return {
      traffic_light: traffic,
      risk_score: riskScore,
      features: {
        vol_5d: vol5,
        vol_10d: vol10,
        vol_20d: vol20,
        drawdown: drawdown,
        ret_1d: ret1d * 100,
        ret_5d: ret5d * 100,
        ret_20d: ret20d * 100
      }
    };
  }

  // ── Exports ───────────────────────────────────────────────────
  SA.dashCompute = {
    // Compute (Kern)
    findMatchingYears: findMatchingYears,
    computeTruePath: computeTruePath,
    computeKiScore: computeKiScore,
    computeRegime: computeRegime,
    // Math-Helper (wieder-verwendbar von Consumer-Pages)
    mean: mean,
    median: median,
    stdev: stdev,
    corrcoef: corrcoef,
    euclidean: euclidean,
    _clean: _clean,
    // Time-Helper
    todayDoy: todayDoy,
    presidentialCycleYear: presidentialCycleYear,
    // Konstanten
    MONTH_START_DOY: MONTH_START_DOY,
    CYCLE_NAMES: CYCLE_NAMES,
    getCycleNames: getCycleNames
  };
})();

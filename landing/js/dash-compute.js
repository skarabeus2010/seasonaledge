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
 *   - computeStress(rows) / stressReihe(rows)
 *       Stress-Ampel (green/yellow/red/grey + Score 0-100 + features), Zwilling von shared/stress_score.py.
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

  // ── Stress-Ampel ──────────────────────────────────────────────
  // Zwilling von shared/stress_score.py (gleiche Formel, gleiche Rechenreihenfolge → bitgleiche Werte).
  // Plan mit Codex-Freigabe: docs/review_prompts/2026-10-09_stress_ampel_plan.md (v5).
  //   S_t = 0,3·vol5 + 0,3·vol20 + 0,4·|dd20|; score = Rang von S_t gegen bis zu 2520 FRÜHERE Tage (½ bei Gleichstand,
  //   ε = 1e-9), erst ab 756 Referenzwerten (777. Schluss); Ampel aus dem ungerundeten Score: gelb ab 70, rot ab 90.
  //   Heuristisches Stress-Maß, keine Prognose. Ersetzt die frühere „Crash-Ampel" (Rang gegen 252 Tage, 40/70).
  var STRESS = { GEWICHTE: [0.3, 0.3, 0.4], REF_MAX: 2520, REF_MIN: 756, ERSTER_KURS: 777, VOLL_KURS: 2541,
                 EPS: 1e-9, GELB: 70, ROT: 90, STELLEN_SCORE: 10, SIGNIFIKANT_S: 15 };
  // Gespeicherte Genauigkeit wie shared/stress_score.py: Score und S gerundet, bevor die Farbe entschieden wird
  // (PostgREST liefert double precision nur auf 15 Stellen zurück).
  function _runden(x, stellen) { var f = Math.pow(10, stellen); return Math.round(x * f) / f; }

  function stressAmpel(score) {
    if (score == null) return 'grey';
    if (score >= STRESS.ROT) return 'red';
    if (score >= STRESS.GELB) return 'yellow';
    return 'green';
  }
  /** Auf eine Nachkommastelle abgeschnitten (89,96 → 89,9) — die Zahl widerspricht nie der Farbe. */
  function stressAnzeige(score) { return score == null ? null : Math.floor(score * 10) / 10; }

  function _stressBereinigen(rows) {
    var je = {}, dup = 0;
    (rows || []).forEach(function(r) {
      var c = typeof r.close === 'number' ? r.close : parseFloat(r.close);
      if (!(typeof c === 'number' && isFinite(c) && c > 0) || !r.date) return;
      var d = String(r.date).slice(0, 10);
      if (Object.prototype.hasOwnProperty.call(je, d)) dup++;
      je[d] = c;
    });
    var ds = Object.keys(je).sort();
    return { daten: ds, closes: ds.map(function(d) { return je[d]; }), duplikate: dup };
  }

  function _stressStd(r, von, bis) {
    var n = bis - von + 1, m = 0, q = 0, i;
    for (i = von; i <= bis; i++) m += r[i];
    m = m / n;
    for (i = von; i <= bis; i++) q += (r[i] - m) * (r[i] - m);
    return Math.sqrt(q / (n - 1));
  }
  function _lowerBound(a, x) { var lo = 0, hi = a.length; while (lo < hi) { var mid = (lo + hi) >> 1; if (a[mid] < x) lo = mid + 1; else hi = mid; } return lo; }
  function _upperBound(a, x) { var lo = 0, hi = a.length; while (lo < hi) { var mid = (lo + hi) >> 1; if (a[mid] <= x) lo = mid + 1; else hi = mid; } return lo; }

  /** Eine Zeile je bereinigtem Kurs: date, close, vol5, vol10, vol20, dd20, s, score, ampel, referenz_n, ret1d/5d/20d. */
  function stressReihe(rows) {
    var b = _stressBereinigen(rows), daten = b.daten, c = b.closes, n = c.length;
    var r = [null], i, k;
    for (i = 1; i < n; i++) r.push((c[i] / c[i - 1] - 1) * 100);
    var out = [], fenster = [], sFolge = [];
    for (i = 0; i < n; i++) {
      var vol5 = i >= 5 ? _stressStd(r, i - 4, i) : null;
      var vol10 = i >= 10 ? _stressStd(r, i - 9, i) : null;
      var vol20 = i >= 20 ? _stressStd(r, i - 19, i) : null;
      var dd20 = null;
      if (i >= 19) {
        var hoch = c[i - 19];
        for (k = i - 18; k <= i; k++) if (c[k] > hoch) hoch = c[k];
        dd20 = (c[i] / hoch - 1) * 100;
      }
      var s = null;
      if (vol5 != null && vol20 != null && dd20 != null) s = STRESS.GEWICHTE[0] * vol5 + STRESS.GEWICHTE[1] * vol20 + STRESS.GEWICHTE[2] * Math.abs(dd20);
      var score = null, refN = fenster.length;
      if (s != null && refN >= STRESS.REF_MIN) {
        var kleiner = _lowerBound(fenster, s - STRESS.EPS), bisGleich = _upperBound(fenster, s + STRESS.EPS);
        score = _runden(100.0 * (kleiner + 0.5 * (bisGleich - kleiner)) / refN, STRESS.STELLEN_SCORE);
      }
      out.push({ date: daten[i], close: c[i], vol5: vol5, vol10: vol10, vol20: vol20, dd20: dd20,
                 s: s == null ? null : Number(s.toPrecision(STRESS.SIGNIFIKANT_S)), score: score,
                 ampel: stressAmpel(score), referenz_n: s != null ? refN : 0,
                 ret1d: i >= 1 ? r[i] : null, ret5d: i >= 5 ? (c[i] / c[i - 5] - 1) * 100 : null,
                 ret20d: i >= 20 ? (c[i] / c[i - 20] - 1) * 100 : null });
      // Referenz endet bei t−1: S_t erst nach dem Rang hinein, S_{t−2520} heraus
      sFolge.push(s);
      if (s != null) {
        fenster.splice(_lowerBound(fenster, s), 0, s);
        var altI = i - STRESS.REF_MAX;
        if (altI >= 0 && sFolge[altI] != null) fenster.splice(_lowerBound(fenster, sFolge[altI]), 1);
      }
    }
    return out;
  }

  /** Anzeigewerte für die letzten n Kurse (Plan W2): Werte des veröffentlichten DB-Laufs nur, wenn sie für JEDEN Tag mit
   *  Score im Zeitraum vorliegen und der letzte Kurstag dabei ist; sonst die Browserrechnung. Rückgabe {zeilen, quelle}. */
  function stressAnzeigeWerte(reihe, dbZeilen, n) {
    var anzeige = reihe.slice(-n), db = {};
    if (!anzeige.length || !dbZeilen || !dbZeilen.length) return { zeilen: anzeige, quelle: 'browser' };
    dbZeilen.forEach(function(z) { db[String(z.date).slice(0, 10)] = z; });
    var letzte = anzeige[anzeige.length - 1];
    var voll = anzeige.every(function(z) { return z.score == null || db[z.date]; });
    if (!voll || !db[letzte.date]) return { zeilen: anzeige, quelle: 'browser' };
    function f(v) { return v == null ? null : parseFloat(v); }
    return { quelle: 'db', zeilen: anzeige.map(function(z) {
      var d = db[z.date];
      if (!d) return z;
      return { date: z.date, close: z.close, score: f(d.score), ampel: d.ampel, s: f(d.s), vol5: f(d.vol5), vol10: f(d.vol10),
               vol20: f(d.vol20), dd20: f(d.dd20), ret1d: f(d.ret1d), ret5d: f(d.ret5d), ret20d: f(d.ret20d),
               referenz_n: z.referenz_n };
    }) };
  }

  /** Aktueller Stand (letzte Zeile) im Format der früheren computeRegime-Ausgabe plus Status. */
  function computeStress(rows) {
    var reihe = stressReihe(rows);
    if (!reihe.length) return { status: 'leer', n_kurse: 0, traffic_light: 'grey', risk_score: null, anzeige: null, features: {} };
    var z = reihe[reihe.length - 1];
    return {
      status: z.score != null ? 'ok' : 'zu_kurz', n_kurse: reihe.length, benoetigt: STRESS.ERSTER_KURS,
      date: z.date, traffic_light: z.ampel, risk_score: z.score, anzeige: stressAnzeige(z.score),
      s: z.s, referenz_n: z.referenz_n,
      features: { vol_5d: z.vol5, vol_10d: z.vol10, vol_20d: z.vol20, drawdown: z.dd20,
                  ret_1d: z.ret1d, ret_5d: z.ret5d, ret_20d: z.ret20d }
    };
  }

  // ── Exports ───────────────────────────────────────────────────
  SA.dashCompute = {
    // Compute (Kern)
    findMatchingYears: findMatchingYears,
    computeTruePath: computeTruePath,
    computeKiScore: computeKiScore,
    computeStress: computeStress,
    stressReihe: stressReihe,
    stressAnzeigeWerte: stressAnzeigeWerte,
    stressAmpel: stressAmpel,
    stressAnzeige: stressAnzeige,
    STRESS: STRESS,
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

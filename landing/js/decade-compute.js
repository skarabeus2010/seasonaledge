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

    // Anomalie-Radar: EINE Rechnung (anomalie), nicht mehr hier im Dekaden-Zusammenbau
    var anomaly;
    try { anomaly = SA.decadeCompute.anomalie(rows, ticker); }
    catch (eA) { anomaly = { status: 'nicht_berechenbar', grund_code: 'fehler', grund: String(eA && eA.message || eA) }; }

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
    // rein in UTC aus dem Datumstext (wie SA.seasonal.tagNummer) — lokale Mitternacht verschob westlich von UTC um 1
    var s = String(dateStr).substring(0, 10);
    var y = +s.substring(0, 4), m = +s.substring(5, 7), d = +s.substring(8, 10);
    return Math.round((Date.UTC(y, m - 1, d) - Date.UTC(y, 0, 0)) / 86400000);
  },

  // ═══════════════════════════════════════════════════════════════════
  // Shared Anomalie-Radar Renderer (wiederverwendbar auf allen Pages)
  // ═══════════════════════════════════════════════════════════════════

  /** CSS fuer Anomalie-Sektion einmalig in den Head injizieren. Idempotent. */
  // ── Anomalie-Radar (Plan v3 Teil C, Codex-Freigabe 2026-10-09) ──────────
  // EINE Rechnung für alle Seiten (der Python-Zwilling ist gelöscht). Vertrag:
  //  * Eingabe: vollständige Kursreihe + Ticker (Pflicht). Bereinigt: nicht-endlich/≤0 raus, doppelte Daten → letzter.
  //  * as_of = letzte Kurszeile (oder opts.as_of: Reihe wird ZUERST darauf abgeschnitten → präfixinvariant).
  //  * Aktuelles Fenster = 11 Kurszeilen bis as_of = 10 Tagesrenditen.
  //  * Vergleich je früherem Jahr y: Endpunkt = letzte Kurszeile ≤ (Monat/Tag von as_of in y; 29.02. → 28.02.),
  //    11 Kurszeilen bis dorthin über die ganze Reihe (Jahreswechsel erlaubt).
  //  * Plausibilität (HEURISTIK, keine Sitzungsprüfung): Endpunkt höchstens T Kalendertage vor dem Ziel und kein
  //    Abstand zwischen zwei Kurszeilen im Fenster > T; T = 1 Krypto, 3 Forex, 7 Börse. Erkennt grobe Datenlücken,
  //    nicht eine einzelne fehlende Sitzung. Börse 7 statt der geplanten 5: XETRA 23.12.→29.12.2025 sind 6 KT ohne
  //    fehlende Sitzung (24.–26.12. Mi–Fr), asiatische Feiertagsblöcke sind länger — gemessen am DAX 12.01.2026.
  //  * Bis zu 30 gültige Vergleichsjahre (die jüngsten), mindestens 10. z mit Stichproben-Std (n−1), Rang als
  //    Mittelrang bei Gleichstand. Status: |z| < 4/3 normal, ≥ 4/3 auffällig, ≥ 7/3 stark auffällig (gesetzt).
  ANOMALIE: { FENSTER: 10, MAX_JAHRE: 30, MIN_JAHRE: 10, AUFFAELLIG: 4 / 3, STARK: 7 / 3,
              TOLERANZ: { krypto: 1, forex: 3, boerse: 7 } },

  /** Marktklasse aus dem Ticker — wortgleich in shared/saison_score.py. Kein Ticker → Fehler (kein stiller Standard). */
  marktklasse: function(ticker) {
    if (ticker == null || String(ticker).trim() === '') throw new Error('Ticker fehlt');
    var t = String(ticker).trim().toUpperCase();
    if (/-USD$/.test(t)) return 'krypto';
    if (/=X$/.test(t)) return 'forex';
    return 'boerse';
  },

  /** Kalendertag seit 1970 (UTC) aus "YYYY-MM-DD". */
  _epochTag: function(iso) {
    return Math.round(Date.UTC(+iso.substring(0, 4), +iso.substring(5, 7) - 1, +iso.substring(8, 10)) / 86400000);
  },

  /** Zieltag (Monat/Tag) in Jahr y als Kalendertag seit 1970; existiert der Tag nicht (29.02.), der letzte des Monats. */
  _zielTag: function(y, m, d) {
    var letzter = new Date(Date.UTC(y, m, 0)).getUTCDate();
    return Math.round(Date.UTC(y, m - 1, Math.min(d, letzter)) / 86400000);
  },

  /** Bereinigte, sortierte Reihe [{date, close}] — wie stress_score.bereinigen. */
  _bereinigen: function(rows, asOf) {
    var m = {};
    for (var i = 0; i < (rows || []).length; i++) {
      var r = rows[i];
      if (!r || r.date == null) continue;
      var c = +r.close, d = String(r.date).substring(0, 10);
      if (!isFinite(c) || c <= 0) continue;
      if (asOf && d > asOf) continue;
      m[d] = c;
    }
    return Object.keys(m).sort().map(function(d) { return { date: d, close: m[d] }; });
  },

  /**
   * Radar mit eigener Historie: die Seiten laden je nach Zeitraum-Regler oft nur 10 Jahre — das Radar braucht aber bis
   * zu 30 Vergleichsjahre plus Fenster. Reichen die übergebenen Kurse nicht 31 Jahre vor das letzte Datum zurück, wird
   * über SA.fetchAllPrices (15-min-Cache) ab diesem Datum nachgeladen. Ergebnis unabhängig vom Regler.
   * Schlägt das Nachladen fehl, rechnet es mit den übergebenen Kursen — die angezeigte Basis (n Jahre) zeigt das.
   */
  /**
   * Die VOLLE Kurshistorie des Tickers (ladeVollHistorie, 15-min-Cache). Eindeutige Rangfolge: die Vollhistorie gewinnt an jedem Tag, den sie enthält; die übergebenen
   * Zeilen verlängern nur das Datenende NACH ihrem letzten Tag (Codex D3/D4 R2 Befund 1 — vorher konnte ein älterer
   * Zeitraum-Cache korrigierte Kurse überschreiben, und der Regler wirkte wieder auf den Score). Für Rechnungen, deren
   * Ergebnis nicht vom Zeitraum-Regler abhängen darf (Saison-Score): Nightly und Watchlist rechnen ebenfalls auf der
   * vollen Historie, und die 20 gültigen Vergleichsjahre können weiter zurückreichen als jede feste Jahreszahl
   * (Codex D3/D4 R1 Befund 1). Ein Ladefehler wird NICHT durch die übergebenen Kurse ersetzt — er lehnt ab, und der
   * Aufrufer zeigt „Kurse nicht ladbar" statt eines Scores auf verkürzter Basis (Befund 2).
   */
  _vollCache: {},
  /**
   * Volle Kurshistorie per Datums-Blättern (date=gt.<letztes Datum>, 1000 je Abruf, OHNE count=exact). Grund: der
   * gemeinsame Lader SA.fetchAllPrices zählt bei JEDEM Block exakt mit; bei langen Reihen (^GSPC ab 1895, 35 000
   * Zeilen) bricht Supabase das mit HTTP 500 ab (gemessen 2026-10-09 nach 28 s). Blättern über den Index
   * (ticker, date) braucht keine Zählung und keinen wachsenden Offset. Fehler oder kein Array → Ablehnung.
   */
  ladeVollHistorie: function(ticker) {
    var self = this, jetzt = Date.now(), c = this._vollCache[ticker];
    if (c && jetzt - c.zeit < 15 * 60 * 1000) return Promise.resolve(c.zeilen);
    if (!(window.SA && SA.supabase && SA.supabase.url)) return Promise.reject(new Error('Kursquelle nicht verfügbar'));
    var alle = [];
    function seite(nach, versuch) {
      var q = 'ticker=eq.' + encodeURIComponent(ticker) + '&select=date,close,log_return,tdom,tdoy&order=date.asc&limit=1000' +
              (nach ? '&date=gt.' + nach : '');
      return fetch(SA.supabase.url + '/rest/v1/prices?' + q, {
        headers: { 'apikey': SA.supabase.key, 'Authorization': 'Bearer ' + SA.supabase.key }
      }).then(function(r) {
        if (!r.ok) {
          if ((r.status === 429 || r.status >= 500) && (versuch || 0) < 3) {
            return new Promise(function(res) { setTimeout(res, 400 * ((versuch || 0) + 1)); })
              .then(function() { return seite(nach, (versuch || 0) + 1); });
          }
          throw new Error('prices ' + r.status + ' (' + ticker + ')');
        }
        return r.json().then(function(z) {
          if (!Array.isArray(z)) throw new Error('prices non-array (' + ticker + ')');
          alle = alle.concat(z);
          return z.length === 1000 ? seite(z[z.length - 1].date, 0) : alle;
        });
      });
    }
    return seite(null, 0).then(function(z) { self._vollCache[ticker] = { zeit: Date.now(), zeilen: z }; return z; });
  },

  mitHistorie: function(rows, ticker) {
    return this.ladeVollHistorie(ticker).then(function(voll) {
      if (!voll || !voll.length) throw new Error('keine Kurse geladen');
      var ende = voll[voll.length - 1].date;
      return voll.concat((rows || []).filter(function(z) { return z && z.date > ende; }));
    });
  },

  RADAR_HISTORIE_JAHRE: 31,
  anomalieMitHistorie: function(rows, ticker) {
    var self = this, r = this._bereinigen(rows);
    var rechne = function(x) { return self.anomalie(x, ticker); };
    if (!r.length) return Promise.resolve().then(function() { return rechne(rows); });
    var letzte = r[r.length - 1].date;
    var start = new Date(this._zielTag(+letzte.substring(0, 4) - this.RADAR_HISTORIE_JAHRE, +letzte.substring(5, 7),
                                       +letzte.substring(8, 10)) * 86400000).toISOString().substring(0, 10);
    if (r[0].date <= start || !(window.SA && SA.fetchAllPrices)) return Promise.resolve().then(function() { return rechne(rows); });
    return SA.fetchAllPrices(ticker, '&date=gte.' + start).then(function(voll) {
      // zusammenführen statt ersetzen: ein älterer Cache-Stand darf das jüngere Datenende nicht verdrängen
      return rechne((voll || []).concat(rows || []));
    }, function() { return rechne(rows); });
  },

  /** Status aus z — eigene Funktion, damit die Grenzen exakt testbar sind (|z| = 4/3 bzw. 7/3 gehört zur höheren Stufe). */
  anomalieStatus: function(z) {
    var az = Math.abs(z), K = this.ANOMALIE;
    return az >= K.STARK ? 'stark_auffaellig' : (az >= K.AUFFAELLIG ? 'auffaellig' : 'normal');
  },

  anomalie: function(rows, ticker, opts) {
    var K = this.ANOMALIE, self = this;
    var klasse = this.marktklasse(ticker), T = K.TOLERANZ[klasse];
    var asOfOpt = opts && opts.as_of ? String(opts.as_of).substring(0, 10) : null;
    var r = this._bereinigen(rows, asOfOpt);
    var n = r.length, F = K.FENSTER;
    var aus = function(code, grund, extra) {
      var o = { status: 'nicht_berechenbar', grund_code: code, grund: grund, as_of: n ? r[n - 1].date : null, marktklasse: klasse };
      for (var k in (extra || {})) o[k] = extra[k];
      return o;
    };
    if (n < F + 1) return aus('zu_wenige_kurse', 'zu wenige Kurse');
    var tage = r.map(function(z) { return self._epochTag(z.date); });
    var fensterOk = function(e) {
      if (e < F) return false;
      for (var i = e - F + 1; i <= e; i++) if (tage[i] - tage[i - 1] > T) return false;
      return true;
    };
    if (!fensterOk(n - 1)) return aus('luecke_aktuell', 'Kurslücke im aktuellen Fenster');
    var R = (r[n - 1].close / r[n - 1 - F].close - 1) * 100;
    var asOf = r[n - 1].date, yA = +asOf.substring(0, 4), mA = +asOf.substring(5, 7), dA = +asOf.substring(8, 10);
    var hist = [], e = n - 1;
    for (var y = yA - 1; hist.length < K.MAX_JAHRE; y--) {
      var ziel = this._zielTag(y, mA, dA);
      while (e >= 0 && tage[e] > ziel) e--;      // letzte Kurszeile ≤ Ziel (Ziele fallen monoton)
      if (e < F) break;                           // davor reicht die Reihe nicht mehr
      if (ziel - tage[e] > T || !fensterOk(e)) continue;
      hist.push({ jahr: y, rendite: (r[e].close / r[e - F].close - 1) * 100 });
    }
    if (hist.length < K.MIN_JAHRE) return aus('zu_wenige_jahre', 'weniger als ' + K.MIN_JAHRE + ' Vergleichsjahre', { n: hist.length, rendite: R });
    var nh = hist.length, sum = 0;
    for (var i = 0; i < nh; i++) sum += hist[i].rendite;
    var mittel = sum / nh, q = 0;
    for (i = 0; i < nh; i++) q += (hist[i].rendite - mittel) * (hist[i].rendite - mittel);
    var s = Math.sqrt(q / (nh - 1));
    if (!(s > 0)) return aus('keine_streuung', 'keine Streuung in den Vergleichsjahren', { n: nh, rendite: R });
    var z = (R - mittel) / s, kleiner = 0, gleich = 0;
    for (i = 0; i < nh; i++) { if (hist[i].rendite < R) kleiner++; else if (hist[i].rendite === R) gleich++; }
    return {
      status: this.anomalieStatus(z),
      grund: null, as_of: asOf, marktklasse: klasse,
      z: z, rendite: R, mittel: mittel, std: s, rang: 100 * (kleiner + 0.5 * gleich) / nh,
      n: nh, jahr_von: hist[nh - 1].jahr, jahr_bis: hist[0].jahr
    };
  },

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
      // Rang-Balken einfarbig: Ränder = selten, Mitte = üblich (keine Gut/Schlecht-Farbe)
      '.sa-anom-prank{display:flex;flex-direction:column;align-items:stretch;gap:.35rem;margin-top:.15rem}',
      '.sa-anom-prank-bar{position:relative;height:8px;border-radius:4px;background:linear-gradient(90deg,rgba(232,168,32,.55) 0%,rgba(232,168,32,.12) 50%,rgba(232,168,32,.55) 100%);box-shadow:inset 0 1px 2px rgba(0,0,0,.4)}',
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
      ? '<p><b>Method:</b> return of the last 10 trading days compared with the same calendar window in up to 30 prior years (at least 10).</p>' +
        '<p><b>z</b> = distance from the historical mean in standard deviations, with sign. From |z| 1.33 the window counts as unusual, from 2.33 as strongly unusual — set thresholds, not probabilities.</p>' +
        '<p><b>Rank</b> = share of comparison years with a lower 10-day return (ties count half).</p>' +
        '<p>Describes the recent move; it says nothing about what comes next. A window is dropped if two prices in it are more than 7 calendar days apart (crypto 1, forex 3) — a heuristic: a single missing session is not detected.</p>'
      : '<p><b>Methodik:</b> Rendite der letzten 10 Handelstage gegen dasselbe Kalenderfenster in bis zu 30 Vorjahren (mindestens 10).</p>' +
        '<p><b>z</b> = Abstand zum historischen Mittel in Standardabweichungen, mit Vorzeichen. Ab |z| 1,33 gilt das Fenster als auffällig, ab 2,33 als stark auffällig &mdash; gesetzte Schwellen, keine Wahrscheinlichkeiten.</p>' +
        '<p><b>Rang</b> = Anteil der Vergleichsjahre mit niedrigerer 10-Tage-Rendite (Gleichstände zählen halb).</p>' +
        '<p>Beschreibt die jüngste Bewegung, sagt nichts über die nächste. Ein Fenster fällt aus, wenn zwei Kurse darin mehr als 7 Kalendertage auseinanderliegen (Krypto 1, Devisen 3) &mdash; eine Heuristik: eine einzelne fehlende Sitzung wird nicht erkannt.</p>';
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
    var self = this, marke = String(Date.now()) + Math.random();
    el.setAttribute('data-radar-marke', marke);   // ein späterer Aufruf (Tickerwechsel) gewinnt — kein veraltetes Ergebnis
    el.innerHTML = this.anomalieLadeHtml();       // das Ergebnis des vorigen Tickers nicht stehen lassen
    var zeige = function(a) { if (el.getAttribute('data-radar-marke') === marke) el.innerHTML = self.anomalieHtml(a, ticker, 'zeile'); };
    var fehler = function(e) { return { status: 'nicht_berechenbar', grund_code: 'fehler', grund: String(e && e.message || e) }; };
    try { this.anomalieMitHistorie(rows, ticker).then(zeige, function(e) { zeige(fehler(e)); }); }
    catch (e) { zeige(fehler(e)); }
  },

  anomalieLadeHtml: function() {
    var _en = !!(window.SA && SA.i18n && SA.i18n.isEN && SA.i18n.isEN());
    return '<p class="sa-anom-laden" style="color:var(--muted);font-size:.875rem;margin:0">' +
      (_en ? SA.i18n.t('dc.anom_laden', 'Calculating…') : 'Wird berechnet …') + '</p>';
  },

  /** Eine Darstellung für beide Orte (Seiten-Abschnitt 'zeile', Dashboard-Karte 'karte'). Einfarbig Gold. */
  anomalieHtml: function(a, ticker, form) {
    // CSS gehört zur Darstellung, nicht zum Aufrufer — sonst fehlt der Rang-Balken dort, wo nur die Karte rendert
    // (Dashboard, Codex U+C R2).
    if (typeof document !== 'undefined' && document.head) this._ensureAnomalyCss();
    var _en = !!(window.SA && SA.i18n && SA.i18n.isEN && SA.i18n.isEN());
    var t = function(k, de) { return _en ? SA.i18n.t(k, de) : de; };
    var esc = function(v) { return String(v == null ? '' : v).replace(/[&<>"']/g, function(c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
    var dez = function(v, k) { var s = (v >= 0 ? '+' : '\u2212') + Math.abs(v).toFixed(k); return _en ? s : s.replace('.', ','); };
    if (!a || a.status === 'nicht_berechenbar') {
      return '<p class="sa-anom-leer" style="color:var(--muted);font-size:.875rem;margin:0">' +
        esc(t('dc.anom_nicht', 'Nicht berechenbar')) +
        (a && a.grund ? ': ' + esc(a.grund_code ? t('dc.anom_g_' + a.grund_code, a.grund) : a.grund) : '') + '</p>';
    }
    var stufe = a.status === 'stark_auffaellig' ? 2 : a.status === 'auffaellig' ? 1 : 0;
    var label = stufe === 2 ? t('dc.anom_stark', 'Stark auffällig') : stufe === 1 ? t('dc.anom_auffaellig', 'Auffällig') : t('dc.anom_normal', 'Normal');
    var richtung = stufe === 0 ? '' : (a.z > 0 ? t('dc.anom_hoch', 'ungewöhnlich stark') : t('dc.anom_tief', 'ungewöhnlich schwach'));
    var gold = ['var(--muted,#a89878)', 'rgba(232,168,32,.85)', 'var(--accent,#e8a820)'][stufe];
    var zTxt = 'z = ' + dez(a.z, 1);
    var basis = t('dc.anom_basis', 'Basis') + ': ' + a.n + ' ' + t('dc.anom_jahre', 'Vergleichsjahre') + ' (' + a.jahr_von + '\u2013' + a.jahr_bis + '), ' + t('dc.anom_stand', 'Stand') + ' ' + esc(a.as_of);
    var rang = Math.round(a.rang);
    var rangHtml = '<div class="sa-anom-prank"><div class="sa-anom-prank-label">' + rang + ' / 100</div>' +
      '<div class="sa-anom-prank-bar" title="' + rang + '"><div class="sa-anom-prank-mark" style="left:' + rang + '%"></div></div></div>';
    if (form === 'karte') {
      // kompakt: z und Status in einer Zeile, Rendite/Vergleich/Rang nebeneinander (Dashboard-Kachel, 2026-10-09)
      return '<div class="anomaly-kopf"><div class="anomaly-score-big sa-anom-z" style="color:' + gold + '">' + zTxt + '</div>' +
        '<div class="anomaly-status sa-anom-status" style="color:' + gold + '">' + esc(label) + (richtung ? ' \u00b7 ' + esc(richtung) : '') + '</div></div>' +
        '<div class="kpi-row-mini">' +
          '<div class="kpi"><div class="kpi-label">' + esc(t('dc.anom_rendite', 'Rendite 10 Handelstage')) + '</div><div class="kpi-value">' + dez(a.rendite, 2) + '%</div></div>' +
          '<div class="kpi"><div class="kpi-label">' + esc(t('dc.anom_mittel', 'Ø Vergleichsjahre')) + '</div><div class="kpi-value">' + dez(a.mittel, 2) + '%</div></div>' +
        '<div class="kpi sa-anom-rang"><div class="kpi-label">' + esc(t('dc.anom_rang', 'Rang')) + '</div>' + rangHtml + '</div>' +
        '</div>' +
        '<p class="sa-anom-basis" style="color:#8899aa;font-size:.6875rem;margin:.45rem 0 0">' + basis + '</p>';
    }
    return '<div class="sa-anom-row">' +
      '<div class="kpi"><div class="kpi-label">' + esc(t('dc.anom_abweichung', 'Abweichung')) + '</div><div class="kpi-value sa-anom-z" style="color:' + gold + '">' + zTxt + '</div></div>' +
      '<div class="kpi"><div class="kpi-label">Status</div><div class="kpi-value sa-anom-status" style="color:' + gold + '">' + esc(label) + '</div>' + (richtung ? '<div style="font-size:.75rem;color:var(--muted)">' + esc(richtung) + '</div>' : '') + '</div>' +
      '<div class="kpi"><div class="kpi-label">' + esc(t('dc.anom_rendite', 'Rendite 10 Handelstage')) + ' ' + esc(ticker || '') + '</div><div class="kpi-value">' + dez(a.rendite, 2) + '%</div></div>' +
      '<div class="kpi"><div class="kpi-label">' + esc(t('dc.anom_mittel', 'Ø Vergleichsjahre')) + '</div><div class="kpi-value">' + dez(a.mittel, 2) + '%</div></div>' +
      '<div class="kpi"><div class="kpi-label">' + esc(t('dc.anom_rang', 'Rang')) + '</div>' + rangHtml + '</div>' +
    '</div><p class="sa-anom-basis" style="color:var(--muted);font-size:.75rem;margin:.5rem 0 0">' + basis + '</p>';
  }
};

window.SA = SA;

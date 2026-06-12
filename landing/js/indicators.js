/**
 * SeasonAlpha — Technische Indikatoren & Filter-Engine
 * (Port von shared/indicators.py + shared/indicator_filter_ui.py)
 * =====================================================
 * Berechnet: SMA, EMA, RSI, Bollinger Bands, MACD, LBR Oscillator
 * Filter-Engine: applyIndicatorFilter() gibt Boolean-Array zurueck.
 * UI: renderFilterSidebar() rendert Sidebar-Controls.
 */

var SA = window.SA || {};

SA.indicators = {

  // ── Berechnungen (1:1 Port der Python-Funktionen) ──

  /** Simple Moving Average */
  calcSMA: function(closes, period) {
    var result = new Array(closes.length).fill(null);
    for (var i = period - 1; i < closes.length; i++) {
      var sum = 0;
      for (var j = i - period + 1; j <= i; j++) sum += closes[j];
      result[i] = sum / period;
    }
    return result;
  },

  /** Exponential Moving Average */
  calcEMA: function(closes, period) {
    var result = new Array(closes.length).fill(null);
    var k = 2 / (period + 1);
    // Seed: SMA der ersten 'period' Werte
    var sum = 0;
    for (var i = 0; i < period && i < closes.length; i++) sum += closes[i];
    if (closes.length < period) return result;
    result[period - 1] = sum / period;
    for (var i = period; i < closes.length; i++) {
      result[i] = closes[i] * k + result[i - 1] * (1 - k);
    }
    return result;
  },

  /** Relative Strength Index (0-100) */
  calcRSI: function(closes, period) {
    var result = new Array(closes.length).fill(null);
    if (closes.length < period + 1) return result;

    var gains = [], losses = [];
    for (var i = 1; i < closes.length; i++) {
      var d = closes[i] - closes[i - 1];
      gains.push(d > 0 ? d : 0);
      losses.push(d < 0 ? -d : 0);
    }

    // Erste Durchschnitte (SMA)
    var avgGain = 0, avgLoss = 0;
    for (var i = 0; i < period; i++) { avgGain += gains[i]; avgLoss += losses[i]; }
    avgGain /= period; avgLoss /= period;
    var rs = avgLoss > 0 ? avgGain / avgLoss : 100;
    result[period] = 100 - 100 / (1 + rs);

    // Weitere Werte (EMA-Glaettung)
    for (var i = period; i < gains.length; i++) {
      avgGain = (avgGain * (period - 1) + gains[i]) / period;
      avgLoss = (avgLoss * (period - 1) + losses[i]) / period;
      rs = avgLoss > 0 ? avgGain / avgLoss : 100;
      result[i + 1] = 100 - 100 / (1 + rs);
    }
    return result;
  },

  /** Bollinger Bands → {middle, upper, lower} */
  calcBollinger: function(closes, period, numStd) {
    numStd = numStd || 2.0;
    var middle = SA.indicators.calcSMA(closes, period);
    var upper = new Array(closes.length).fill(null);
    var lower = new Array(closes.length).fill(null);

    for (var i = period - 1; i < closes.length; i++) {
      if (middle[i] === null) continue;
      var sumSq = 0;
      for (var j = i - period + 1; j <= i; j++) sumSq += (closes[j] - middle[i]) * (closes[j] - middle[i]);
      var std = Math.sqrt(sumSq / period);
      upper[i] = middle[i] + numStd * std;
      lower[i] = middle[i] - numStd * std;
    }
    return { middle: middle, upper: upper, lower: lower };
  },

  /** MACD → {macd, signal, histogram} */
  calcMACD: function(closes, fast, slow, signal) {
    fast = fast || 12; slow = slow || 26; signal = signal || 9;
    var emaFast = SA.indicators.calcEMA(closes, fast);
    var emaSlow = SA.indicators.calcEMA(closes, slow);
    var macdLine = new Array(closes.length).fill(null);
    for (var i = 0; i < closes.length; i++) {
      if (emaFast[i] !== null && emaSlow[i] !== null) macdLine[i] = emaFast[i] - emaSlow[i];
    }
    // Signal = EMA der MACD-Line
    var validMacd = [];
    var startIdx = -1;
    for (var i = 0; i < macdLine.length; i++) {
      if (macdLine[i] !== null) { if (startIdx < 0) startIdx = i; validMacd.push(macdLine[i]); }
    }
    var sigEMA = SA.indicators.calcEMA(validMacd, signal);
    var signalLine = new Array(closes.length).fill(null);
    for (var i = 0; i < sigEMA.length; i++) signalLine[startIdx + i] = sigEMA[i];

    var histogram = new Array(closes.length).fill(null);
    for (var i = 0; i < closes.length; i++) {
      if (macdLine[i] !== null && signalLine[i] !== null) histogram[i] = macdLine[i] - signalLine[i];
    }
    return { macd: macdLine, signal: signalLine, histogram: histogram };
  },

  /** LBR Oscillator (Linda Bradford Raschke) → {fastline, slowline, histogram} */
  calcLBR: function(closes, fast, slow, smoothing) {
    fast = fast || 3; slow = slow || 10; smoothing = smoothing || 16;
    var r = SA.indicators.calcMACD(closes, fast, slow, smoothing);
    return { fastline: r.macd, slowline: r.signal, histogram: r.histogram };
  },

  // ── Filter-Engine (1:1 Port von apply_indicator_filter) ──

  /** Registry: Indikatoren + Parameter + Bedingungen */
  REGISTRY: {
    SMA:       { label: 'SMA', params: [{ name: 'period', label: 'Periode', min: 10, max: 400, def: 200 }],
                 conditions: ['Close > SMA', 'Close < SMA'] },
    EMA:       { label: 'EMA', params: [{ name: 'period', label: 'Periode', min: 10, max: 400, def: 200 }],
                 conditions: ['Close > EMA', 'Close < EMA'] },
    RSI:       { label: 'RSI', params: [{ name: 'period', label: 'Periode', min: 5, max: 30, def: 14 },
                                         { name: 'threshold', label: 'Schwelle', min: 0, max: 100, def: 50 }],
                 conditions: ['RSI > Threshold', 'RSI < Threshold'] },
    Bollinger: { label: 'Bollinger', params: [{ name: 'period', label: 'Periode', min: 10, max: 50, def: 20 },
                                               { name: 'num_std', label: 'Std', min: 1, max: 3, def: 2, step: 0.5 }],
                 conditions: ['Close > Upper Band', 'Close < Lower Band', 'Close inside Bands'] },
    MACD:      { label: 'MACD', params: [{ name: 'fast', label: 'Fast', min: 5, max: 26, def: 12 },
                                          { name: 'slow', label: 'Slow', min: 12, max: 50, def: 26 },
                                          { name: 'signal', label: 'Signal', min: 5, max: 20, def: 9 }],
                 conditions: ['MACD > Signal (bullish)', 'MACD < Signal (bearish)'] },
    LBR:       { label: 'LBR (Raschke)', params: [{ name: 'fast', label: 'Fast', min: 2, max: 10, def: 3 },
                                                    { name: 'slow', label: 'Slow', min: 5, max: 20, def: 10 },
                                                    { name: 'smoothing', label: 'Smoothing', min: 5, max: 30, def: 16 }],
                 conditions: ['LBR > 0 (bullish)', 'LBR < 0 (bearish)'] }
  },

  /**
   * Bewertet einen einzelnen Filter → Boolean-Array.
   * Nutzt shift(1) um Look-Ahead-Bias zu vermeiden.
   */
  _evalSingleFilter: function(closes, f) {
    var n = closes.length;
    var mask = new Array(n).fill(false);
    var type = f.type, cond = f.condition;

    if (type === 'SMA') {
      var sma = SA.indicators.calcSMA(closes, f.period || 200);
      for (var i = 1; i < n; i++) mask[i] = cond === 'Close > SMA' ? closes[i - 1] > sma[i - 1] : closes[i - 1] < sma[i - 1];
    } else if (type === 'EMA') {
      var ema = SA.indicators.calcEMA(closes, f.period || 200);
      for (var i = 1; i < n; i++) if (ema[i - 1] !== null) mask[i] = cond === 'Close > EMA' ? closes[i - 1] > ema[i - 1] : closes[i - 1] < ema[i - 1];
    } else if (type === 'RSI') {
      var rsi = SA.indicators.calcRSI(closes, f.period || 14);
      var thr = f.threshold || 50;
      for (var i = 1; i < n; i++) if (rsi[i - 1] !== null) mask[i] = cond === 'RSI > Threshold' ? rsi[i - 1] > thr : rsi[i - 1] < thr;
    } else if (type === 'Bollinger') {
      var bb = SA.indicators.calcBollinger(closes, f.period || 20, f.num_std || 2.0);
      for (var i = 1; i < n; i++) {
        if (bb.upper[i - 1] === null) continue;
        if (cond === 'Close > Upper Band') mask[i] = closes[i - 1] > bb.upper[i - 1];
        else if (cond === 'Close < Lower Band') mask[i] = closes[i - 1] < bb.lower[i - 1];
        else mask[i] = closes[i - 1] >= bb.lower[i - 1] && closes[i - 1] <= bb.upper[i - 1];
      }
    } else if (type === 'MACD') {
      var macd = SA.indicators.calcMACD(closes, f.fast || 12, f.slow || 26, f.signal || 9);
      for (var i = 1; i < n; i++) if (macd.macd[i - 1] !== null && macd.signal[i - 1] !== null) mask[i] = cond.indexOf('bullish') >= 0 ? macd.macd[i - 1] > macd.signal[i - 1] : macd.macd[i - 1] < macd.signal[i - 1];
    } else if (type === 'LBR') {
      var lbr = SA.indicators.calcLBR(closes, f.fast || 3, f.slow || 10, f.smoothing || 16);
      for (var i = 1; i < n; i++) if (lbr.fastline[i - 1] !== null) mask[i] = cond.indexOf('bullish') >= 0 ? lbr.fastline[i - 1] > 0 : lbr.fastline[i - 1] < 0;
    } else {
      mask.fill(true);
    }
    return mask;
  },

  /**
   * Wendet alle Filter mit UND-Verknuepfung an.
   * @param {Array} closes - Close-Preise
   * @param {Array} filters - [{type, condition, period, ...}]
   * @returns {Array} Boolean-Array (true = Tag erfuellt alle Bedingungen)
   */
  applyFilter: function(closes, filters) {
    if (!filters || filters.length === 0) return new Array(closes.length).fill(true);
    var mask = new Array(closes.length).fill(true);
    for (var fi = 0; fi < filters.length; fi++) {
      var fMask = SA.indicators._evalSingleFilter(closes, filters[fi]);
      for (var i = 0; i < mask.length; i++) mask[i] = mask[i] && fMask[i];
    }
    return mask;
  },

  // ── UI: Sidebar Filter-Controls ──

  /**
   * Rendert Indikator-Filter Controls in einem Container.
   * @param {string} containerId - ID des Containers
   * @param {function} onChange - Callback wenn Filter sich aendern
   * @returns {function} getFilters() — liest aktuelle Filter aus
   */
  renderFilterUI: function(containerId, onChange) {
    var el = document.getElementById(containerId);
    if (!el) return function() { return []; };

    var _en = !!(SA.i18n && SA.i18n.isEN && SA.i18n.isEN());
    var filterCount = 0;
    var REG = SA.indicators.REGISTRY;
    var types = Object.keys(REG);

    function rebuild() {
      var html = '';
      for (var i = 0; i < filterCount; i++) {
        html += '<div style="background:rgba(255,255,255,.03);border-radius:6px;padding:.5rem;margin-bottom:.5rem">';
        html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.25rem">';
        html += '<b style="font-size:.75rem;color:var(--dim)">Filter ' + (i + 1) + '</b>';
        html += '<button data-rm="' + i + '" style="background:none;border:none;color:var(--red);cursor:pointer;font-size:.875rem">\u2715</button></div>';
        // Typ
        html += '<select data-idx="' + i + '" data-field="type" style="width:100%;margin-bottom:.25rem">';
        for (var t = 0; t < types.length; t++) html += '<option value="' + types[t] + '">' + REG[types[t]].label + '</option>';
        html += '</select>';
        // Bedingung
        html += '<select data-idx="' + i + '" data-field="condition" style="width:100%;margin-bottom:.25rem" id="ind_cond_' + i + '"></select>';
        // Parameter
        html += '<div id="ind_params_' + i + '"></div>';
        html += '</div>';
      }
      html += '<button id="ind_add_btn" style="width:100%;padding:.375rem;background:rgba(232,168,32,.1);border:1px solid rgba(232,168,32,.15);border-radius:6px;color:var(--accent);cursor:pointer;font-size:.75rem">' + (_en ? SA.i18n.t('ind.btn_add_filter') : '+ Filter hinzuf\u00FCgen') + '</button>';
      if (filterCount > 0) {
        var closes = []; // Placeholder
        html += '<div id="ind_badge" style="margin-top:.5rem;font-size:.6875rem;color:var(--accent);text-align:center"></div>';
      }
      el.innerHTML = html;

      // Events binden
      document.getElementById('ind_add_btn').addEventListener('click', function() { filterCount++; rebuild(); if (onChange) onChange(); });
      el.querySelectorAll('button[data-rm]').forEach(function(btn) {
        btn.addEventListener('click', function() { filterCount--; rebuild(); if (onChange) onChange(); });
      });
      el.querySelectorAll('select[data-field="type"]').forEach(function(sel) {
        sel.addEventListener('change', function() { updateConditions(parseInt(sel.dataset.idx)); if (onChange) onChange(); });
        updateConditions(parseInt(sel.dataset.idx));
      });
      el.querySelectorAll('select[data-field="condition"]').forEach(function(sel) {
        sel.addEventListener('change', function() { if (onChange) onChange(); });
      });
    }

    function updateConditions(idx) {
      var typeSel = el.querySelector('select[data-idx="' + idx + '"][data-field="type"]');
      var condSel = document.getElementById('ind_cond_' + idx);
      var paramDiv = document.getElementById('ind_params_' + idx);
      if (!typeSel || !condSel) return;

      var reg = REG[typeSel.value];
      condSel.innerHTML = '';
      for (var c = 0; c < reg.conditions.length; c++) {
        var opt = document.createElement('option');
        opt.value = reg.conditions[c]; opt.textContent = reg.conditions[c];
        condSel.appendChild(opt);
      }

      // Parameter
      var pHtml = '';
      for (var p = 0; p < reg.params.length; p++) {
        var pr = reg.params[p];
        var step = pr.step || 1;
        var prLabel = pr.label;
        if (_en) {
          if (pr.label === 'Periode')  prLabel = SA.i18n.t('ind.param_period');
          if (pr.label === 'Schwelle') prLabel = SA.i18n.t('ind.param_threshold');
        }
        pHtml += '<label style="font-size:.6875rem;color:var(--muted)">' + prLabel +
          ' <input type="number" data-idx="' + idx + '" data-param="' + pr.name + '" value="' + pr.def +
          '" min="' + pr.min + '" max="' + pr.max + '" step="' + step +
          '" style="width:60px;font-size:.75rem"></label> ';
      }
      paramDiv.innerHTML = pHtml;
      paramDiv.querySelectorAll('input').forEach(function(inp) {
        inp.addEventListener('change', function() { if (onChange) onChange(); });
      });
    }

    rebuild();

    // Getter: aktuelle Filter auslesen
    return function getFilters() {
      var filters = [];
      for (var i = 0; i < filterCount; i++) {
        var typeSel = el.querySelector('select[data-idx="' + i + '"][data-field="type"]');
        var condSel = document.getElementById('ind_cond_' + i);
        if (!typeSel || !condSel) continue;
        var f = { type: typeSel.value, condition: condSel.value };
        var params = el.querySelectorAll('input[data-idx="' + i + '"]');
        params.forEach(function(inp) {
          f[inp.dataset.param] = parseFloat(inp.value);
        });
        filters.push(f);
      }
      return filters;
    };
  }
};

window.SA = SA;

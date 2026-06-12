/**
 * SeasonAlpha — Outlier Filter (Port von shared/outlier_manager.py)
 * ==================================================================
 * Erkennt und filtert Ausreisser in Event-Renditen.
 * Methoden: IQR (mild/streng), Winsorize (3σ).
 * Wird von: Monatswechsel, Mondphasen, Wochentage etc. genutzt.
 */

var SA = window.SA || {};

SA.outlier = {

  METHODS: {
    off:        'Aus',
    iqr:        'IQR (1.5x)',
    iqr_strict: 'IQR (3x, streng)',
    winsorize:  'Winsorize (3σ)'
  },

  /**
   * Erkennt Ausreisser via IQR.
   * @param {Array} values - Rendite-Werte
   * @param {number} factor - IQR-Multiplikator (1.5 oder 3.0)
   * @returns {Array} Boolean-Array (true = Ausreisser)
   */
  detectIQR: function(values, factor) {
    factor = factor || 1.5;
    if (values.length < 4) return new Array(values.length).fill(false);
    var sorted = values.slice().sort(function(a, b) { return a - b; });
    var n = sorted.length;
    var q1 = sorted[Math.floor(n * 0.25)];
    var q3 = sorted[Math.floor(n * 0.75)];
    var iqr = q3 - q1;
    var lower = q1 - factor * iqr;
    var upper = q3 + factor * iqr;
    return values.map(function(v) { return v < lower || v > upper; });
  },

  /**
   * Winsorize: Clippt Werte auf mean ± sigma*std.
   * @param {Array} values
   * @param {number} sigma
   * @returns {Array} geclippte Werte
   */
  winsorize: function(values, sigma) {
    sigma = sigma || 3.0;
    if (values.length < 3) return values.slice();
    var sum = 0;
    for (var i = 0; i < values.length; i++) sum += values[i];
    var mean = sum / values.length;
    var sumSq = 0;
    for (var i = 0; i < values.length; i++) sumSq += (values[i] - mean) * (values[i] - mean);
    var std = Math.sqrt(sumSq / values.length);
    if (std === 0) return values.slice();
    var lower = mean - sigma * std;
    var upper = mean + sigma * std;
    return values.map(function(v) { return Math.max(lower, Math.min(upper, v)); });
  },

  /**
   * Filtert all_curves Array nach Outlier-Methode.
   * @param {Array} allCurves - [{total_return, ...}]
   * @param {string} method - "off", "iqr", "iqr_strict", "winsorize"
   * @returns {Object} {filtered: Array, removed: number, method: string}
   */
  filterCurves: function(allCurves, method) {
    if (!method || method === 'off' || !allCurves || allCurves.length < 4) {
      return { filtered: allCurves, removed: 0, method: 'off' };
    }

    var returns = allCurves.map(function(c) { return c.total_return; });

    if (method === 'winsorize') {
      var clipped = SA.outlier.winsorize(returns, 3.0);
      var result = allCurves.map(function(c, i) {
        var copy = {};
        for (var k in c) copy[k] = c[k];
        copy.total_return = clipped[i];
        return copy;
      });
      var changed = 0;
      for (var i = 0; i < returns.length; i++) if (returns[i] !== clipped[i]) changed++;
      return { filtered: result, removed: changed, method: method };
    }

    // IQR
    var factor = method === 'iqr_strict' ? 3.0 : 1.5;
    var isOutlier = SA.outlier.detectIQR(returns, factor);
    var filtered = allCurves.filter(function(_, i) { return !isOutlier[i]; });
    var removed = allCurves.length - filtered.length;
    return { filtered: filtered, removed: removed, method: method };
  },

  /**
   * Rendert Outlier-Filter Sidebar Controls.
   * @param {string} containerId
   * @param {function} onChange
   * @returns {function} getMethod() → "off"|"iqr"|"iqr_strict"|"winsorize"
   */
  renderFilterUI: function(containerId, onChange) {
    var _en = !!(SA.i18n && SA.i18n.isEN && SA.i18n.isEN());
    var el = document.getElementById(containerId);
    if (!el) return function() { return 'off'; };

    var methodLabels = _en ? {
      off:        SA.i18n.t('out.method_off'),
      iqr:        SA.i18n.t('out.method_iqr'),
      iqr_strict: SA.i18n.t('out.method_iqr_strict'),
      winsorize:  SA.i18n.t('out.method_winsorize')
    } : SA.outlier.METHODS;

    var html = '<select id="outlier-select" style="width:100%">';
    for (var key in SA.outlier.METHODS) {
      html += '<option value="' + key + '">' + methodLabels[key] + '</option>';
    }
    html += '</select>';
    html += '<div id="outlier-badge" style="font-size:.6875rem;color:var(--accent);margin-top:.25rem"></div>';
    el.innerHTML = html;

    document.getElementById('outlier-select').addEventListener('change', function() {
      if (onChange) onChange();
    });

    return function() {
      var sel = document.getElementById('outlier-select');
      return sel ? sel.value : 'off';
    };
  }
};

window.SA = SA;

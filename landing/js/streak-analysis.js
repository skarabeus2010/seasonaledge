/**
 * SeasonAlpha — Streak Analysis (Port von shared/streak_analysis.py)
 * ===================================================================
 * W/L-Serien Berechnung + HTML-Tabelle.
 * Wird von: Monatswechsel, Wochentage, Mondphasen genutzt.
 */

var SA = window.SA || {};

SA.streaks = {

  /**
   * Berechnet Streaks aus TOM/Event-Ergebnislisten.
   * (Port von compute_streaks_from_list)
   *
   * @param {Array} data - [{year, month, total_return}, ...]
   * @param {string} groupKey - Feld zum Gruppieren (z.B. "month")
   * @param {string} returnKey - Feld mit Rendite (z.B. "total_return")
   * @param {string} yearKey - Feld zum Sortieren (z.B. "year")
   * @param {Object} labelMap - {1: "Jan → Feb", ...} (optional)
   * @returns {Array} [{label, entries: [{date, ret}]}]
   */
  computeStreaksFromList: function(data, groupKey, returnKey, yearKey, labelMap) {
    yearKey = yearKey || 'year';
    var groups = {};
    for (var i = 0; i < data.length; i++) {
      var d = data[i];
      var g = d[groupKey];
      if (!groups[g]) groups[g] = [];
      groups[g].push({ date: d[yearKey], ret: d[returnKey] });
    }

    var result = [];
    var sortedKeys = Object.keys(groups).sort(function(a, b) { return a - b; });
    for (var ki = 0; ki < sortedKeys.length; ki++) {
      var key = sortedKeys[ki];
      var entries = groups[key].slice();
      // Sortieren: neueste zuerst
      entries.sort(function(a, b) { return b.date - a.date; });
      var label = labelMap ? (labelMap[key] || 'x' + key) : 'x' + key;
      result.push({ label: label, entries: entries });
    }
    return result;
  },

  /**
   * Aktuelle Streak zaehlen (vom neuesten Eintrag aus).
   * @param {Array} entries - [{date, ret}] (neueste zuerst)
   * @returns {Object} {type: "win"|"loss", count: N}
   */
  currentStreak: function(entries) {
    if (!entries || entries.length === 0) return { type: 'none', count: 0 };
    var type = entries[0].ret > 0 ? 'win' : 'loss';
    var count = 1;
    for (var i = 1; i < entries.length; i++) {
      var isWin = entries[i].ret > 0;
      if ((type === 'win' && isWin) || (type === 'loss' && !isWin)) {
        count++;
      } else {
        break;
      }
    }
    return { type: type, count: count };
  },

  /**
   * Rendert eine Streak-Tabelle als HTML.
   * (Port von render_streak_table)
   *
   * @param {Array} groups - [{label, entries}] (von computeStreaksFromList)
   * @param {string} colHeader - Spaltenheader (default "Gruppe")
   * @param {number} nBlocks - Anzahl W/L-Bloecke (default 10)
   * @returns {string} HTML-String
   */
  renderStreakTable: function(groups, colHeader, nBlocks) {
    var _en = !!(SA.i18n && SA.i18n.isEN && SA.i18n.isEN());
    colHeader = colHeader || (_en ? SA.i18n.t('str.col_group') : 'Gruppe');
    nBlocks = nBlocks || 10;
    var C = SA.COLORS || { green: '#00d4aa', red: '#ff4757' };

    var html = '<table data-no-sort="1" style="width:100%;border-collapse:collapse;font-size:.8125rem">';
    html += '<tr><th style="text-align:left;padding:.5rem;color:var(--muted,#a89878);border-bottom:1px solid rgba(255,255,255,.06)">' + colHeader + '</th>';
    html += '<th style="text-align:left;padding:.5rem;color:var(--muted,#a89878);border-bottom:1px solid rgba(255,255,255,.06)">' + (_en ? SA.i18n.t('str.current_streak') : 'Aktuelle Serie') + '</th>';
    html += '<th style="text-align:left;padding:.5rem;color:var(--muted,#a89878);border-bottom:1px solid rgba(255,255,255,.06)">' + (_en ? SA.i18n.t('str.last_n').replace('{n}', nBlocks) : 'Letzte ' + nBlocks) + '</th></tr>';

    for (var gi = 0; gi < groups.length; gi++) {
      var g = groups[gi];
      var streak = SA.streaks.currentStreak(g.entries);
      var streakColor = streak.type === 'win' ? C.green : C.red;
      var streakText = streak.count + 'x ' + (streak.type === 'win'
        ? (_en ? SA.i18n.t('str.win') : 'Gewinn')
        : (_en ? SA.i18n.t('str.loss') : 'Verlust'));

      // W/L Bloecke (chronologisch: aelteste links, neueste rechts)
      var blocks = g.entries.slice(0, nBlocks).reverse();
      var blocksHtml = '';
      for (var bi = 0; bi < blocks.length; bi++) {
        var b = blocks[bi];
        var isWin = b.ret > 0;
        var bgColor = isWin ? C.green : C.red;
        var label = isWin ? 'W' : 'L';
        var retFmt = (b.ret >= 0 ? '+' : '') + b.ret.toFixed(2) + '%';
        blocksHtml += '<span title="' + b.date + ': ' + retFmt + '" style="display:inline-block;width:32px;height:26px;line-height:26px;text-align:center;background:' + bgColor + ';color:#fff;font-size:10px;font-weight:700;border-radius:4px;margin:1px">' + label + '</span>';
      }

      html += '<tr style="border-bottom:1px solid rgba(255,255,255,.03)">';
      html += '<td style="padding:.4rem .5rem;color:var(--dim,#e8e0d0)">' + g.label + '</td>';
      html += '<td style="padding:.4rem .5rem;color:' + streakColor + ';font-weight:600">' + streakText + '</td>';
      html += '<td style="padding:.4rem .5rem">' + blocksHtml + '</td>';
      html += '</tr>';
    }
    html += '</table>';
    return html;
  }
};

window.SA = SA;

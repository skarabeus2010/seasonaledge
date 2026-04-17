/**
 * SeasonAlpha — Polymarket Integration
 * =====================================
 * Shared Data-Loader + Chart-Renderer fuer Fed-Path, Crypto-Divergenz
 * und Risiko-Ampel. Wird von der Haupt-Page /polymarket genutzt sowie
 * in Dashboard, Zentralbanken und Crash-Fruehwarnung fuer Teaser-Blocks.
 *
 * Daten kommen aus Supabase-Tabellen `polymarket_markets` und
 * `polymarket_prices` (von scripts/polymarket_refresh.py gefuettert).
 */

var SA = window.SA || {};

SA.polymarket = (function() {
  'use strict';

  // ── Data-Loader ───────────────────────────────────────────────────────────

  /** Alle aktiven Markets aus dem Katalog (bereits nach category,slug sortiert). */
  function loadCatalog() {
    return SA.supabase.get(
      'polymarket_markets',
      'active=eq.true&order=category,slug'
    );
  }

  /**
   * Neueste Preise pro condition_id.
   * Supabase REST hat keine eingebaute "latest per group"-Query — wir ziehen
   * die letzten 10×n Zeilen und reduzieren client-side.
   */
  function loadLatestPrices(conditionIds) {
    if (!conditionIds || !conditionIds.length) return Promise.resolve({});
    var idsParam = conditionIds.join(',');
    return SA.supabase.get(
      'polymarket_prices',
      'condition_id=in.(' + idsParam + ')&order=ts.desc&limit=' + (conditionIds.length * 5)
    ).then(function(rows) {
      var latest = {};
      (rows || []).forEach(function(r) {
        if (!latest[r.condition_id]) latest[r.condition_id] = r;
      });
      return latest;
    });
  }

  /** Historie ueber N Tage fuer gegebene condition_ids. */
  function loadHistory(conditionIds, days) {
    if (!conditionIds || !conditionIds.length) return Promise.resolve([]);
    var since = new Date();
    since.setDate(since.getDate() - (days || 90));
    var sinceIso = since.toISOString();
    var idsParam = conditionIds.join(',');
    return SA.supabase.get(
      'polymarket_prices',
      'condition_id=in.(' + idsParam + ')&ts=gte.' + sinceIso + '&order=ts.asc&limit=10000'
    );
  }


  // ── Fed-Path Mathematik ───────────────────────────────────────────────────

  /**
   * Fed-Cuts-Verteilung aus Cuts-Markets extrahieren.
   * Returns { '0': prob, '1': prob, ..., '12plus': prob } + expectedBps + expectedCuts.
   */
  function computeFedDistribution(markets, latestPrices) {
    var dist = {};
    var totalProb = 0, weighted = 0;
    markets.forEach(function(m) {
      var match = /^fed-cuts-2026-(\d+|12plus)$/.exec(m.slug || '');
      if (!match) return;
      var key = match[1];
      var snap = latestPrices[m.condition_id];
      var p = snap ? (snap.yes_price || 0) : 0;
      dist[key] = p;
      var cuts = (key === '12plus') ? 12 : parseInt(key, 10);
      weighted += cuts * p;
      totalProb += p;
    });
    var normalized = totalProb > 0 ? (weighted / totalProb) : 0;
    return {
      dist: dist,
      totalProb: totalProb,
      expectedCuts: normalized,
      expectedBps: normalized * 25
    };
  }


  // ── Renderers: Fed-Path ───────────────────────────────────────────────────

  /**
   * Balken-Chart der 13 Cuts-Outcomes.
   * @param elementId  DIV-ID fuer ApexCharts
   * @param fedStats   Output von computeFedDistribution()
   */
  function renderFedDistChart(elementId, fedStats) {
    var order = ['0','1','2','3','4','5','6','7','8','9','10','11','12plus'];
    var cats = order.map(function(c) { return c === '12plus' ? '12+' : c; });
    var probs = order.map(function(c) { return (fedStats.dist[c] || 0) * 100; });

    // Farbgebung: Rot-Grün-Gradient nach Wahrscheinlichkeit (nicht nach "gut/schlecht" —
    // neutrale Verteilungs-Darstellung). Akzent-Gold fuer den Balken mit hoechster Prob.
    var maxProb = Math.max.apply(null, probs);
    var colors = probs.map(function(p) {
      return p >= maxProb - 0.01 ? SA.COLORS.accent : 'rgba(232,168,32,0.35)';
    });

    var cfg = {
      series: [{ name: 'Wahrscheinlichkeit', data: probs }],
      chart: Object.assign({ type: 'bar', height: 360, toolbar: { show: false } }, SA.chartTheme.chart),
      colors: [SA.COLORS.accent],
      plotOptions: {
        bar: {
          borderRadius: 4, columnWidth: '70%', distributed: true
        }
      },
      grid: SA.chartTheme.grid,
      tooltip: {
        theme: 'dark',
        y: { formatter: function(v) { return v.toFixed(1) + '%'; } },
        x: { formatter: function(v, opts) {
          var n = opts.dataPointIndex;
          var label = cats[n];
          var cuts = (label === '12+') ? 12 : parseInt(label, 10);
          return label + ' Cuts — ' + (cuts * 25) + ' bps';
        } }
      },
      xaxis: Object.assign({
        categories: cats,
        title: { text: 'Anzahl Fed-Cuts 2026', style: { color: '#a89878', fontSize: '11px' } }
      }, SA.chartTheme.xaxis),
      yaxis: Object.assign({}, SA.chartTheme.yaxis, {
        labels: { style: { colors: '#a89878', fontSize: '11px' },
                  formatter: function(v) { return v.toFixed(0) + '%'; } },
        title: { text: 'Implizite Wahrscheinlichkeit', style: { color: '#a89878', fontSize: '11px' } }
      }),
      dataLabels: {
        enabled: true, style: { colors: ['#fff'], fontSize: '11px', fontWeight: 700 },
        formatter: function(v) { return v < 1 ? '' : v.toFixed(0) + '%'; }
      },
      legend: { show: false },
      annotations: {
        xaxis: [{
          x: fedStats.expectedCuts,
          borderColor: SA.COLORS.green,
          strokeDashArray: 4,
          label: {
            text: 'E[Cuts] = ' + fedStats.expectedCuts.toFixed(2),
            style: { color: '#000', background: SA.COLORS.green, fontSize: '11px', fontWeight: 700 }
          }
        }]
      },
      colors: colors
    };
    var chart = new ApexCharts(document.getElementById(elementId), cfg);
    chart.render();
    return chart;
  }

  /**
   * Multi-Line Historien-Chart der 13 Cuts-Markets — eine Linie pro Outcome.
   * Zeigt, wie sich die Verteilung ueber Zeit verschoben hat.
   */
  function renderFedTrendChart(elementId, markets, history) {
    var order = ['0','1','2','3','4','5','6','7','8','9','10','11','12plus'];
    var cidBySlug = {}, slugByCid = {};
    markets.forEach(function(m) {
      var match = /^fed-cuts-2026-(\d+|12plus)$/.exec(m.slug);
      if (match) {
        cidBySlug[match[1]] = m.condition_id;
        slugByCid[m.condition_id] = match[1];
      }
    });

    // Gruppiere Historie nach slug
    var byKey = {};
    (history || []).forEach(function(row) {
      var key = slugByCid[row.condition_id];
      if (!key) return;
      if (!byKey[key]) byKey[key] = [];
      byKey[key].push({ x: new Date(row.ts).getTime(), y: row.yes_price * 100 });
    });

    // Farbpalette: vom Wahrscheinlichen (Gold) zum Unwahrscheinlichen (fade)
    var palette = ['#e8a820','#d97706','#4d9fff','#51cf66','#cc5de8',
                   '#ff6b6b','#ffd43b','#ff922b','#20c997','#e64980',
                   '#748ffc','#f06595','#a78bfa'];

    var series = order.map(function(c, i) {
      return {
        name: (c === '12plus' ? '12+' : c) + ' cuts',
        data: byKey[c] || [],
        color: palette[i]
      };
    }).filter(function(s) { return s.data.length > 0; });

    var cfg = {
      series: series,
      chart: Object.assign({ type: 'line', height: 340, zoom: { enabled: false } }, SA.chartTheme.chart),
      stroke: { width: 2, curve: 'smooth' },
      grid: SA.chartTheme.grid,
      tooltip: { theme: 'dark', x: { format: 'dd. MMM yy' }, y: { formatter: function(v) { return v.toFixed(1) + '%'; } } },
      xaxis: { type: 'datetime', labels: { style: { colors: '#a89878', fontSize: '11px' } } },
      yaxis: Object.assign({}, SA.chartTheme.yaxis, {
        labels: { style: { colors: '#a89878' }, formatter: function(v) { return v.toFixed(0) + '%'; } },
        min: 0
      }),
      legend: { show: true, position: 'top', horizontalAlign: 'left',
                labels: { colors: '#a89878' }, fontSize: '11px' }
    };
    var chart = new ApexCharts(document.getElementById(elementId), cfg);
    chart.render();
    return chart;
  }


  // ── Renderer: Risiko-Kacheln ──────────────────────────────────────────────

  /**
   * Rendert KPI-Kacheln fuer Fed-Hike, Emergency-Cut, Recession, GDP-negativ.
   * @param elementId  Container (bekommt kpi-row-Klassen-Kind)
   */
  function renderRiskGauges(elementId, markets, latestPrices) {
    var targets = [
      { slug: 'fed-hike-2026',          label: 'Fed Hike 2026',      sevAt: 0.20 },
      { slug: 'fed-emergency-cut-2027', label: 'Emergency Cut',      sevAt: 0.15 },
      { slug: 'us-recession-2026',      label: 'US Recession 2026',  sevAt: 0.35 },
      { slug: 'us-gdp-negative-2026',   label: 'Neg. GDP 2026',      sevAt: 0.15 }
    ];
    var bySlug = {};
    markets.forEach(function(m) { bySlug[m.slug] = m; });

    var html = targets.map(function(t) {
      var mkt = bySlug[t.slug];
      var p = 0;
      if (mkt) {
        var snap = latestPrices[mkt.condition_id];
        if (snap) p = snap.yes_price || 0;
      }
      var pct = (p * 100).toFixed(1);
      var cls = p >= t.sevAt ? 'red' : (p >= t.sevAt * 0.6 ? '' : 'green');
      return '<div class="kpi">' +
             '<span class="kpi-label">' + t.label + '</span>' +
             '<span class="kpi-value ' + cls + '">' + pct + '%</span>' +
             '</div>';
    }).join('');

    var el = document.getElementById(elementId);
    if (el) el.innerHTML = html;
  }


  // ── Renderer: Crypto-Ladder ───────────────────────────────────────────────

  /**
   * Horizontaler Balken mit Target->Wahrscheinlichkeit fuer BTC oder ETH.
   * Extrahiert Ziel-Wert aus dem slug (btc-above-150k-2026 -> $150k).
   */
  function renderCryptoLadder(elementId, markets, latestPrices, asset) {
    asset = (asset || 'btc').toLowerCase();
    var prefix = asset + '-above-';
    var entries = [];
    markets.forEach(function(m) {
      if (!(m.slug || '').startsWith(prefix)) return;
      var match = /^(btc|eth)-above-(\d+)k-2026$/.exec(m.slug);
      if (!match) return;
      var k = parseInt(match[2], 10);
      var snap = latestPrices[m.condition_id];
      var p = snap ? (snap.yes_price || 0) : 0;
      entries.push({ k: k, label: '$' + k + 'k', prob: p * 100, condId: m.condition_id });
    });
    entries.sort(function(a, b) { return a.k - b.k; });

    var cats = entries.map(function(e) { return e.label; });
    var probs = entries.map(function(e) { return parseFloat(e.prob.toFixed(1)); });

    var color = asset === 'btc' ? '#f7931a' : '#627eea';
    var cfg = {
      series: [{ name: 'Wahrscheinlichkeit', data: probs }],
      chart: Object.assign({ type: 'bar', height: 280, toolbar: { show: false } }, SA.chartTheme.chart),
      colors: [color],
      plotOptions: { bar: { horizontal: true, borderRadius: 4, barHeight: '65%' } },
      grid: SA.chartTheme.grid,
      tooltip: { theme: 'dark', y: { formatter: function(v) { return v.toFixed(1) + '%'; } } },
      xaxis: Object.assign({ categories: cats, max: 100 }, SA.chartTheme.xaxis, {
        labels: { style: { colors: '#a89878', fontSize: '11px' },
                  formatter: function(v) { return v.toFixed(0) + '%'; } }
      }),
      yaxis: { labels: { style: { colors: '#fff', fontSize: '12px', fontWeight: 700 } } },
      dataLabels: {
        enabled: true, style: { colors: ['#fff'], fontSize: '11px', fontWeight: 700 },
        formatter: function(v) { return v.toFixed(1) + '%'; }
      },
      legend: { show: false },
      title: {
        text: (asset === 'btc' ? 'Bitcoin' : 'Ethereum') + ' — Ziel-Wahrscheinlichkeiten 2026',
        align: 'left', style: { color: color, fontSize: '13px', fontWeight: 700 }
      }
    };
    var chart = new ApexCharts(document.getElementById(elementId), cfg);
    chart.render();
    return chart;
  }


  // ── Renderer: Historien-Multi-Line ────────────────────────────────────────

  /**
   * Multi-Line fuer beliebige ausgewaehlte Markets.
   * @param elementId
   * @param markets     ausgefilterte Market-Metadata
   * @param history     Zeilen aus polymarket_prices
   */
  function renderHistoryMulti(elementId, markets, history) {
    var byCid = {};
    markets.forEach(function(m) { byCid[m.condition_id] = m; });

    var buckets = {};
    (history || []).forEach(function(row) {
      if (!byCid[row.condition_id]) return;
      if (!buckets[row.condition_id]) buckets[row.condition_id] = [];
      buckets[row.condition_id].push({
        x: new Date(row.ts).getTime(),
        y: row.yes_price * 100
      });
    });

    var palette = ['#e8a820','#4d9fff','#51cf66','#ff6b6b','#cc5de8',
                   '#ffd43b','#ff922b','#20c997','#e64980','#748ffc'];
    var series = Object.keys(buckets).slice(0, 10).map(function(cid, i) {
      return {
        name: (byCid[cid].question || byCid[cid].slug).slice(0, 40),
        data: buckets[cid],
        color: palette[i % palette.length]
      };
    });

    var cfg = {
      series: series,
      chart: Object.assign({ type: 'line', height: 380, zoom: { enabled: false } }, SA.chartTheme.chart),
      stroke: { width: 2, curve: 'smooth' },
      grid: SA.chartTheme.grid,
      tooltip: { theme: 'dark', x: { format: 'dd. MMM yy' }, y: { formatter: function(v) { return v.toFixed(1) + '%'; } } },
      xaxis: { type: 'datetime', labels: { style: { colors: '#a89878', fontSize: '11px' } } },
      yaxis: Object.assign({}, SA.chartTheme.yaxis, {
        labels: { style: { colors: '#a89878' }, formatter: function(v) { return v.toFixed(0) + '%'; } },
        min: 0, max: 100
      }),
      legend: { show: true, position: 'top', horizontalAlign: 'left',
                labels: { colors: '#a89878' }, fontSize: '11px' }
    };
    var chart = new ApexCharts(document.getElementById(elementId), cfg);
    chart.render();
    return chart;
  }


  // ── Renderer: Tabelle aller Markets ───────────────────────────────────────

  function renderMarketsTable(elementId, markets, latestPrices, history7d) {
    // history7d: {condition_id: [{ts, yes_price}, ...]} fuer Trend-Pfeil
    var byCidHist = history7d || {};

    var rows = markets.map(function(m) {
      var snap = latestPrices[m.condition_id];
      var p = snap ? (snap.yes_price || 0) : 0;

      // 7d-Change bestimmen
      var histRows = byCidHist[m.condition_id] || [];
      var earliest = histRows.length ? histRows[0].yes_price : null;
      var delta = (earliest != null) ? (p - earliest) : null;

      var pct = (p * 100).toFixed(1) + '%';
      var deltaStr = (delta == null) ? '—'
        : (delta >= 0 ? '+' : '') + (delta * 100).toFixed(1) + ' pp';
      var deltaCls = (delta == null) ? '' : (delta >= 0 ? 'pos' : 'neg');

      var liq = m.liquidity_usd ? '$' + (m.liquidity_usd / 1000).toFixed(0) + 'k' : '—';
      return '<tr>' +
             '<td>' + (m.slug || '') + '</td>' +
             '<td>' + (m.category || '') + '</td>' +
             '<td>' + (m.question || '').slice(0, 60) + '</td>' +
             '<td style="text-align:right;font-weight:700;color:#fff">' + pct + '</td>' +
             '<td style="text-align:right" class="' + deltaCls + '">' + deltaStr + '</td>' +
             '<td style="text-align:right">' + liq + '</td>' +
             '</tr>';
    }).join('');

    var html = '<table class="perf-table" data-no-sort="0">' +
               '<thead><tr>' +
               '<th>Slug</th>' +
               '<th>Kategorie</th>' +
               '<th>Frage</th>' +
               '<th style="text-align:right">YES</th>' +
               '<th style="text-align:right">7d Δ</th>' +
               '<th style="text-align:right">Liquiditaet</th>' +
               '</tr></thead><tbody>' + rows + '</tbody></table>';

    var el = document.getElementById(elementId);
    if (el) {
      el.innerHTML = html;
      if (SA.makeSortable) { SA.makeSortable(el.querySelector('table')); }
    }
  }


  // ── Public API ────────────────────────────────────────────────────────────

  return {
    loadCatalog: loadCatalog,
    loadLatestPrices: loadLatestPrices,
    loadHistory: loadHistory,
    computeFedDistribution: computeFedDistribution,
    renderFedDistChart: renderFedDistChart,
    renderFedTrendChart: renderFedTrendChart,
    renderRiskGauges: renderRiskGauges,
    renderCryptoLadder: renderCryptoLadder,
    renderHistoryMulti: renderHistoryMulti,
    renderMarketsTable: renderMarketsTable
  };
})();

window.SA = SA;

/**
 * SeasonAlpha — ApexCharts Theme + Helpers
 * ==========================================
 * Gemeinsame Chart-Config fuer alle Pages.
 * Nutzt V3 Ultra Palette (Black + Gold).
 */

var SA = window.SA || {};

// ── Farben ──────────────────────────────────────────────────────────────────

SA.COLORS = {
  bg: '#000000',
  surface: '#050505',
  card: '#0a0a0e',
  border: 'rgba(232,168,32,.1)',
  accent: '#e8a820',
  text: '#ffffff',
  dim: '#e8e0d0',
  muted: '#a89878',
  green: '#30e878',
  red: '#ff4040',
  gold: '#FFE600',
};

SA.DECADE_COLORS = [
  '#4d9fff', '#ff6b6b', '#51cf66', '#ffd43b', '#cc5de8',
  '#ff922b', '#20c997', '#e64980', '#748ffc', '#f06595'
];

SA.MONTHS = ['Jan','Feb','M\u00e4r','Apr','Mai','Jun','Jul','Aug','Sep','Okt','Nov','Dez'];
SA.DECADE_LABELS = ['x0','x1','x2','x3','x4','x5','x6','x7','x8','x9'];


// ── ApexCharts Base Theme ───────────────────────────────────────────────────

SA.chartTheme = {
  chart: {
    background: 'transparent',
    foreColor: SA.COLORS.muted,
    fontFamily: 'DM Sans, sans-serif',
    toolbar: { show: false },
    animations: { enabled: true, easing: 'easeinout', speed: 400 }
  },
  grid: {
    borderColor: 'rgba(255,255,255,.04)',
    strokeDashArray: 3
  },
  tooltip: {
    theme: 'dark',
    style: { fontSize: '12px' }
  },
  xaxis: {
    labels: { style: { colors: SA.COLORS.muted, fontSize: '11px' } },
    axisBorder: { color: 'rgba(255,255,255,.06)' },
    axisTicks: { color: 'rgba(255,255,255,.06)' }
  },
  yaxis: {
    labels: {
      style: { colors: SA.COLORS.muted, fontSize: '11px' },
      formatter: function(v) { return v.toFixed(1) + '%'; }
    }
  },
  legend: {
    position: 'top',
    horizontalAlign: 'left',
    labels: { colors: SA.COLORS.muted },
    fontSize: '11px',
    markers: { size: 4 }
  }
};


// ── Chart Factory Helpers ───────────────────────────────────────────────────

/**
 * Erstellt einen Line-Chart (Dekaden-Kurven, Drawdown, Volatilitaet).
 */
SA.lineChart = function(elementId, series, opts) {
  opts = opts || {};
  var config = {
    series: series,
    chart: Object.assign({ type: 'line', height: opts.height || 420 }, SA.chartTheme.chart),
    stroke: { width: opts.strokeWidth || 1.5, curve: 'smooth' },
    grid: SA.chartTheme.grid,
    tooltip: SA.chartTheme.tooltip,
    xaxis: Object.assign({
      categories: Array.from({ length: 252 }, function(_, i) { return i + 1; }),
      tickAmount: 12,
      labels: Object.assign({}, SA.chartTheme.xaxis.labels, {
        formatter: function(v) { var m = Math.floor((v - 1) / 21); return SA.MONTHS[m] || ''; }
      })
    }, SA.chartTheme.xaxis),
    yaxis: Object.assign({}, SA.chartTheme.yaxis, opts.yaxis || {}),
    legend: SA.chartTheme.legend,
    title: opts.title ? { text: opts.title, style: { color: '#fff', fontSize: '14px', fontFamily: 'Sora,sans-serif', fontWeight: 700 } } : undefined
  };
  return new ApexCharts(document.getElementById(elementId), config).render();
};

/**
 * Erstellt einen Bar-Chart (Dekaden-Rendite).
 */
SA.barChart = function(elementId, categories, data, opts) {
  opts = opts || {};
  var config = {
    series: [{ name: opts.seriesName || 'Wert', data: data }],
    chart: Object.assign({ type: 'bar', height: opts.height || 320 }, SA.chartTheme.chart),
    colors: data.map(function(v) { return v >= 0 ? SA.COLORS.green : SA.COLORS.red; }),
    plotOptions: { bar: { borderRadius: 4, distributed: true, columnWidth: '60%' } },
    grid: SA.chartTheme.grid,
    tooltip: SA.chartTheme.tooltip,
    xaxis: Object.assign({ categories: categories }, SA.chartTheme.xaxis),
    yaxis: SA.chartTheme.yaxis,
    legend: { show: false },
    dataLabels: { enabled: true, style: { fontSize: '11px', colors: ['#fff'] }, formatter: function(v) { return v.toFixed(1) + '%'; } }
  };
  return new ApexCharts(document.getElementById(elementId), config).render();
};

/**
 * Erstellt eine Heatmap (Monats-Rendite, Drawdown).
 */
SA.heatmapChart = function(elementId, series, opts) {
  opts = opts || {};
  var config = {
    series: series,
    chart: Object.assign({ type: 'heatmap', height: opts.height || 380 }, SA.chartTheme.chart),
    colors: [opts.negativeOnly ? SA.COLORS.red : SA.COLORS.red],
    colorScale: opts.negativeOnly
      ? undefined
      : { ranges: [
          { from: -100, to: -0.01, color: SA.COLORS.red, name: 'Negativ' },
          { from: 0, to: 0, color: '#333', name: 'Neutral' },
          { from: 0.01, to: 100, color: SA.COLORS.green, name: 'Positiv' }
        ] },
    grid: SA.chartTheme.grid,
    tooltip: SA.chartTheme.tooltip,
    xaxis: SA.chartTheme.xaxis,
    dataLabels: { enabled: true, style: { fontSize: '10px', colors: ['#fff'] }, formatter: function(v) { return v.toFixed(1); } },
    plotOptions: { heatmap: { radius: 4, enableShades: opts.negativeOnly ? true : false } }
  };
  return new ApexCharts(document.getElementById(elementId), config).render();
};

/**
 * Erstellt einen Box-Plot.
 */
SA.boxPlotChart = function(elementId, data, opts) {
  opts = opts || {};
  var config = {
    series: [{ type: 'boxPlot', data: data }],
    chart: Object.assign({ type: 'boxPlot', height: opts.height || 350 }, SA.chartTheme.chart),
    colors: [SA.COLORS.accent],
    plotOptions: { boxPlot: { colors: { upper: SA.COLORS.accent, lower: '#4d9fff' } } },
    grid: SA.chartTheme.grid,
    tooltip: SA.chartTheme.tooltip,
    xaxis: SA.chartTheme.xaxis,
    yaxis: SA.chartTheme.yaxis
  };
  return new ApexCharts(document.getElementById(elementId), config).render();
};

window.SA = SA;

/**
 * SeasonAlpha — ApexCharts Theme + Helpers
 * ==========================================
 * Gemeinsame Chart-Config fuer alle Pages.
 * Nutzt V3 Ultra Palette (Black + Gold).
 */

window.SA.__release('%%RELEASE%%');   // Releasekennung (landing/js/methode.js) — muss erste Anweisung bleiben
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

// Tour-Mode (aus app.js) → Animations aus, spart ~400ms pro Chart
var _animEnabled = !(SA.TOUR_MODE);

SA.chartTheme = {
  chart: {
    background: 'transparent',
    foreColor: SA.COLORS.muted,
    fontFamily: 'DM Sans, sans-serif',
    toolbar: { show: false },
    zoom: { enabled: false },
    selection: { enabled: false },
    animations: { enabled: _animEnabled, easing: 'easeinout', speed: _animEnabled ? 400 : 0 }
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


// ── Monatsachse für 365-Tag-Charts ──────────────────────────────────────────
// Wie die Kategorie-Achse der Monats-Performance: Trennstriche an den Monatsgrenzen, Monatsname mittig im Monat.
// Eine numerische ApexCharts-Achse kennt nur gleich weite Ticks, Monate sind aber 28–31 Tage lang — deshalb
// zeichnet SA.monatsAchse Striche und Namen nach jedem Rendern selbst ins SVG. Datenindex 0 = 1. Januar.
SA.monatsAchse = (function () {
  var NAMEN = ['Jan', 'Feb', 'M\u00e4r', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'];
  var STARTS = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335];   // Kalendertag des Monatsersten
  var FARBE_STRICH = '#e0e0e0';   // wie axisBorder/axisTicks der Kategorie-Achse (ApexCharts-Standard)
  var FARBE_TEXT = '#a89878';

  function zeichnen(ctx) {
    var g = ctx && ctx.w && ctx.w.globals, svg = ctx && ctx.el && ctx.el.querySelector('svg.apexcharts-svg');
    if (!g || !svg || !(g.gridWidth > 0) || !(g.maxX > g.minX)) return;
    var alt = svg.querySelector('g.sa-monatsachse');
    if (alt) alt.parentNode.removeChild(alt);
    var NS = 'http://www.w3.org/2000/svg', grp = document.createElementNS(NS, 'g');
    grp.setAttribute('class', 'sa-monatsachse');
    grp.setAttribute('transform', 'translate(' + g.translateX + ',' + g.translateY + ')');
    var minX = g.minX, maxX = g.maxX, H = g.gridHeight;
    function px(x) { return (Math.min(Math.max(x, minX), maxX) - minX) / (maxX - minX) * g.gridWidth; }
    // Grenze zwischen letztem Tag eines Monats und erstem des nächsten: Index (Monatserster − 1) − 0,5
    var grenzen = [minX];
    for (var m = 1; m < 12; m++) grenzen.push(STARTS[m] - 1.5);
    grenzen.push(maxX);
    for (var i = 0; i < grenzen.length; i++) {
      var x = px(grenzen[i]), strich = document.createElementNS(NS, 'line');
      strich.setAttribute('x1', x); strich.setAttribute('x2', x);
      strich.setAttribute('y1', H); strich.setAttribute('y2', H + 6);
      strich.setAttribute('stroke', FARBE_STRICH); strich.setAttribute('stroke-width', '1');
      grp.appendChild(strich);
    }
    for (var k = 0; k < 12; k++) {
      var t = document.createElementNS(NS, 'text');
      t.setAttribute('x', (px(grenzen[k]) + px(grenzen[k + 1])) / 2);
      t.setAttribute('y', H + 21);
      t.setAttribute('text-anchor', 'middle');
      t.setAttribute('fill', FARBE_TEXT);
      t.setAttribute('font-size', '11px');
      t.setAttribute('font-family', 'DM Sans, sans-serif');
      t.textContent = NAMEN[k];
      grp.appendChild(t);
    }
    svg.appendChild(grp);
  }

  return {
    /** xaxis-Optionen: numerisch 0..364; eingebaute Beschriftung bleibt als leerer Platzhalter (gleiche Höhe). */
    xaxis: function () {
      return {
        type: 'numeric', min: 0, max: 364, tickAmount: 11,
        labels: { style: { colors: FARBE_TEXT, fontSize: '11px' }, formatter: function () { return '\u00a0'; },
                  rotate: 0, showDuplicates: false, hideOverlappingLabels: true },
        axisTicks: { show: false },
        tooltip: { enabled: false }
      };
    },
    /** Hängt das Zeichnen an die chart-Optionen (mounted + updated) und gibt sie zurück. */
    mit: function (chartOpts) {
      chartOpts.events = Object.assign({}, chartOpts.events, {
        mounted: function (ctx) { zeichnen(ctx); },
        updated: function (ctx) { zeichnen(ctx); }
      });
      return chartOpts;
    },
    zeichnen: zeichnen
  };
})();


// ── Chart Factory Helpers ───────────────────────────────────────────────────

/**
 * Erstellt einen Line-Chart (Dekaden-Kurven, Drawdown, Volatilitaet).
 */
SA.lineChart = function(elementId, series, opts) {
  opts = opts || {};
  var config = {
    series: series,
    chart: Object.assign({ type: 'line', height: opts.height || 420 }, SA.chartTheme.chart),
    stroke: { width: opts.strokeWidth || 1.5, curve: 'straight' },
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

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

  /* ── Gemeinsamer Vertrag mit der Python-Seite (Codex-Befund 10) ───────────
     Dieselbe Rechnung lief hier und in shared/weekly_report.py, und sie kam zu
     verschiedenen Zahlen. Fuenf Abweichungen, alle am Code bestaetigt:

       1. Zeitrahmen: `new Date("2024-03-15")` parst UTC-Mitternacht, aber
          `getFullYear/getMonth/getDate` lesen LOKAL. In New York verschob das
          auf den Vortag — dieselbe Eingabe ergab in Berlin 50,0 % und in New
          York 36,4 % (Messung von Codex). Python rechnet mit `date`, also mit
          einem Kalenderdatum ohne Zone. Der Vertrag ist deshalb das
          UTC-KALENDERDATUM, und hier wird durchgaengig `getUTC*` benutzt.
       2. Schalttag: `new Date(2023, 1, 29)` rollt auf den 1. Maerz, Python
          nimmt den 28. Februar. Der Vertrag ist der 28. — er haelt den
          Vergleich im selben Monat. Eine Modellwahl, kein Naturgesetz.
       3. Mindeststichprobe: Python verlangt 3 Jahre, hier genuegte EINES.
       4. Preisfrische: Python laedt nur Zeilen der letzten 7 Tage, hier gab es
          keine Altersgrenze.
       5. Von mir dazugefunden: Python verwirft einen Endpreis <= 0, hier
          genuegte `!= null`.

     Die Gleichheit erzwingt scripts/verify_polymarket_zwillinge.py — es
     fuettert BEIDE Seiten mit denselben Eingaben und vergleicht die Zahlen.
     Ein gemeinsamer Vertrag als Datei kaeme nicht in den Browser, ohne einen
     Bauschritt einzufuehren; der Zwillingstest ist die kleinere Mechanik. */
  var VERTRAG = {
    minStichprobe: 3,      // = POLY_DIV_MIN_SAMPLES in shared/weekly_report.py
    preisFrischeTage: 7,   // = timedelta(days=7) in shared/supabase_client.py
    schalttagErsatz: 28,   // 29.02. in einem Nicht-Schaltjahr -> 28.02.
    // Ab welcher Luecke eine Linie BRECHEN muss. Die Kadenz ist ein
    // Snapshot pro Tag; zwei Tage sind also schon eine Luecke und keine
    // Schwankung. Vorher verband die Linie durch, und `curve: 'smooth'`
    // erfand dazu noch eine Kruemmung (Codex-Befund 14).
    lueckeTage: 2,
    // In welchem Monat die Reihe eines Vergleichsjahres enden MUSS, damit
    // sie als Jahresende gilt (11 = Dezember). Vorher wurde die letzte
    // Zeile des Jahres genommen, egal wann: eine Reihe, die im Juni
    // endete, lieferte eine Juni-Rendite unter der Beschriftung
    // „Jahresende" (gemessen: 0,200 neben 0,500 fuer vollstaendige
    // Jahre). Ein unvollstaendiges Vergleichsfenster ist kein Vergleich
    // (Codex-Befund 13).
    jahresendeMonat: 11,
    // Ab welchem Abstand in Prozentpunkten die Bewertung ueberhaupt eine
    // Richtung nennt. REDAKTIONELL GESETZT, nicht aus den Daten geschaetzt —
    // bei Stichproben von drei bis gut einem Dutzend Jahren gibt es keine
    // Grundlage fuer eine statistische Schwelle. Die Seite weist das aus.
    // „nahe beieinander" heisst |Abstand| < 3 pp; genau 3 pp zaehlt schon als
    // Richtung (Codex-Befund 13).
    divergenzSchwellePp: 3
  };

  /**
   * Maskiert einen Wert fuer die Ausgabe in HTML — inklusive Anfuehrungszeichen,
   * damit er auch in einem Attribut nicht ausbrechen kann.
   *
   * Noetig, weil die Marktfragen, Slugs und Kategorien NICHT von uns stammen:
   * sie kommen von Polymarket ueber scripts/polymarket_refresh.py in die
   * Supabase-Tabellen und von dort hierher. Wir geben fremden Text weiter, und
   * das heisst maskieren — unabhaengig davon, ob heute jemand dort etwas
   * unterbringen kann.
   */
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function(c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

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

  /**
   * Historie ueber N Tage fuer gegebene condition_ids.
   * Nutzt getAll() fuer Offset-Pagination — sonst trunkiert PostgREST auf 1000 Rows
   * und bei 26 Markets + ~200 Snapshots/Market bekommen wir nur die aeltesten Batches.
   */
  function loadHistory(conditionIds, days) {
    if (!conditionIds || !conditionIds.length) return Promise.resolve([]);
    var since = new Date();
    since.setDate(since.getDate() - (days || 90));
    var sinceIso = since.toISOString();
    var idsParam = conditionIds.join(',');
    return SA.supabase.getAll(
      'polymarket_prices',
      'condition_id=in.(' + idsParam + ')&ts=gte.' + sinceIso + '&order=ts.asc'
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

    // Die Balken liefen auf ROHEN Preisen, der Erwartungswert auf der durch
    // `totalProb` normierten Verteilung — zwei verschiedene Grundlagen in einem
    // Bild (Codex-Befund 14). `distNorm` ist die Grundlage, auf der auch der
    // Erwartungswert steht; `dist` bleibt fuer alles erhalten, was die rohen
    // Preise braucht.
    var distNorm = {};
    Object.keys(dist).forEach(function(k) {
      distNorm[k] = totalProb > 0 ? dist[k] / totalProb : 0;
    });

    // `12plus` wiegt mit genau 12. Liegt dort Wahrscheinlichkeit, ist der
    // Erwartungswert eine UNTERGRENZE und kein exakter Wert — der Kontrakt
    // sagt „12 oder mehr", und wie viel mehr, sagt er nicht.
    var tail = dist['12plus'] || 0;

    return {
      dist: dist,
      distNorm: distNorm,
      totalProb: totalProb,
      expectedCuts: normalized,
      expectedBps: normalized * 25,
      // Wahr, sobald im offenen Ende Wahrscheinlichkeit liegt.
      istUntergrenze: tail > 0,
      tailProb: tail
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
    // Normierte Verteilung, damit Balken und Erwartungswert auf derselben
    // Grundlage stehen. Wie weit die Preissumme von 1 entfernt ist, steht als
    // eigene Angabe daneben — sie ist die Information, die beim Normieren
    // verloren geht.
    var quelle = fedStats.distNorm || fedStats.dist || {};
    var probs = order.map(function(c) { return (quelle[c] || 0) * 100; });

    // Farbgebung: Rot-Grün-Gradient nach Wahrscheinlichkeit (nicht nach "gut/schlecht" —
    // neutrale Verteilungs-Darstellung). Akzent-Gold fuer den Balken mit hoechster Prob.
    var maxProb = Math.max.apply(null, probs);
    var colors = probs.map(function(p) {
      return p >= maxProb - 0.01 ? SA.COLORS.accent : 'rgba(232,168,32,0.35)';
    });

    var _en = !!(SA.i18n && SA.i18n.isEN && SA.i18n.isEN());
    var cfg = {
      series: [{ name: _en ? SA.i18n.t('pmjs.probability') : 'Wahrscheinlichkeit', data: probs }],
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
        title: { text: _en ? SA.i18n.t('pmjs.fed_cuts_2026') : 'Anzahl Fed-Cuts 2026', style: { color: '#a89878', fontSize: '11px' } }
      }, SA.chartTheme.xaxis),
      yaxis: Object.assign({}, SA.chartTheme.yaxis, {
        labels: { style: { colors: '#a89878', fontSize: '11px' },
                  formatter: function(v) { return v.toFixed(0) + '%'; } },
        title: { text: _en ? SA.i18n.t('pmjs.implied_probability') : 'Implizite Wahrscheinlichkeit', style: { color: '#a89878', fontSize: '11px' } }
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
            // Zweiter Ausgabepfad desselben Werts. Die KPI-Zeile trug das
            // ≥ schon, die Chart-Annotation nicht — derselbe
            // Erwartungswert stand dort ohne den Vorbehalt
            // (Codex, Abnahme Runde 2). Eine Regel, die nur einen von
            // zwei Ausgabepfaden kennt, ist keine Regel.
            text: (fedStats.istUntergrenze ? '\u2265 ' : '')
                  + 'E[Cuts] = ' + fedStats.expectedCuts.toFixed(2),
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
   * Setzt an jede Luecke einen Nullpunkt, damit die Linie dort BRICHT.
   *
   * Die Reihen kommen als {x,y}-Paare ohne Nullwerte: ein fehlender Tag fehlt
   * einfach, und die Linie verbindet darueber hinweg. Der Leser sieht dann eine
   * durchgehende Entwicklung, wo keine Messung vorliegt. Ein Nullwert zwischen
   * den Punkten ist das Einzige, was ApexCharts als Unterbrechung zeichnet.
   */
  function mitLuecken(punkte) {
    if (!punkte || punkte.length < 2) return punkte || [];
    var grenze = VERTRAG.lueckeTage * 86400000;
    var sortiert = punkte.slice().sort(function(a, b) { return a.x - b.x; });
    var aus = [sortiert[0]];
    for (var i = 1; i < sortiert.length; i++) {
      if (sortiert[i].x - sortiert[i - 1].x > grenze) {
        aus.push({ x: sortiert[i - 1].x + 1, y: null });
      }
      aus.push(sortiert[i]);
    }
    return aus;
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
        data: mitLuecken(byKey[c] || []),
        color: palette[i]
      };
    }).filter(function(s) { return s.data.length > 0; });

    var cfg = {
      series: series,
      chart: Object.assign({ type: 'line', height: 340, zoom: { enabled: false } }, SA.chartTheme.chart),
      stroke: { width: 2, curve: 'straight' },
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

    var _en = !!(SA.i18n && SA.i18n.isEN && SA.i18n.isEN());
    var color = asset === 'btc' ? '#f7931a' : '#627eea';
    var cfg = {
      series: [{ name: _en ? SA.i18n.t('pmjs.probability') : 'Wahrscheinlichkeit', data: probs }],
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
        text: (asset === 'btc' ? 'Bitcoin' : 'Ethereum') + (_en ? SA.i18n.t('pmjs.target_probs_2026') : ' — Ziel-Wahrscheinlichkeiten 2026'),
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
        // ApexCharts schreibt Legendennamen und Tooltip-Titel per innerHTML (am
        // ausgelieferten Bundle geprueft) -> der Name muss maskiert ankommen.
        // Reihenfolge: ERST kuerzen, DANN maskieren, sonst zerschneidet der
        // 40-Zeichen-Schnitt eine Entitaet wie "&amp;" zu "&a".
        name: esc((byCid[cid].question || byCid[cid].slug).slice(0, 40)),
        // Dieselbe Lueckenregel wie im Fed-Trend-Chart. Sie fehlte hier, und
        // der Waechter prueefte nur den Fed-Renderer (Codex, Abnahme
        // 2026-10-08) — eine Linie verband also weiter ueber fehlende Tage
        // hinweg und behauptete Messwerte, die es nicht gibt.
        data: mitLuecken(buckets[cid]),
        color: palette[i % palette.length]
      };
    });

    // Dynamische Y-Achse: Min/Max aus allen Punkten + 5pp Padding, clamp [0,100].
    // Sonst werden z.B. Kurven im Bereich 35-80% auf 0-100 gezeichnet und sind
    // optisch platt.
    var yMin = Infinity, yMax = -Infinity;
    series.forEach(function(s) {
      (s.data || []).forEach(function(p) {
        if (p && typeof p.y === 'number' && !isNaN(p.y)) {
          if (p.y < yMin) yMin = p.y;
          if (p.y > yMax) yMax = p.y;
        }
      });
    });
    if (!isFinite(yMin) || !isFinite(yMax)) { yMin = 0; yMax = 100; }
    var range = yMax - yMin;
    var pad = Math.max(2, range * 0.08);
    yMin = Math.max(0, Math.floor(yMin - pad));
    yMax = Math.min(100, Math.ceil(yMax + pad));
    if (yMax - yMin < 5) { yMax = Math.min(100, yMin + 5); }  // Mindest-Range

    var cfg = {
      series: series,
      chart: Object.assign({ type: 'line', height: 380, zoom: { enabled: false } }, SA.chartTheme.chart),
      stroke: { width: 2, curve: 'straight' },
      grid: SA.chartTheme.grid,
      tooltip: { theme: 'dark', x: { format: 'dd. MMM yy' }, y: { formatter: function(v) { return v.toFixed(1) + '%'; } } },
      xaxis: { type: 'datetime', labels: { style: { colors: '#a89878', fontSize: '11px' } } },
      yaxis: Object.assign({}, SA.chartTheme.yaxis, {
        labels: { style: { colors: '#a89878' }, formatter: function(v) { return v.toFixed(0) + '%'; } },
        min: yMin, max: yMax, forceNiceScale: true
      }),
      legend: { show: true, position: 'top', horizontalAlign: 'left',
                labels: { colors: '#a89878' }, fontSize: '11px' }
    };
    var chart = new ApexCharts(document.getElementById(elementId), cfg);
    chart.render();
    return chart;
  }


  // ── Divergenz: Saisonale Historien-Prior vs Polymarket ───────────────────

  /**
   * Historische Wahrscheinlichkeit dass `ticker` vom `referenceDate` bis
   * Year-End mindestens `requiredReturn` macht. Nutzt rolling windows
   * "heutiges Tagesdatum im Vorjahr bis 31. Dezember Vorjahr" fuer jeden
   * vergangenen Kalenderjahres, fuer den Daten vorhanden sind.
   *
   * @param priceRows    Array {date, close} sortiert aufsteigend
   * @param asOfDate     Date — Referenz-Stichtag (i.d.R. today)
   * @returns {samples: [{year, yStart, yEnd, ret}], n: int}
   */
  function collectYearEndReturns(priceRows, asOfDate) {
    if (!priceRows || !priceRows.length) return { samples: [], n: 0, zuDuenn: true };
    var ref = asOfDate || new Date();
    // UTC durchgaengig — siehe VERTRAG, Punkt 1.
    var refMonth = ref.getUTCMonth();   // 0-11
    var refDay = ref.getUTCDate();

    var byYear = {};
    priceRows.forEach(function(r) {
      // Dieselbe Verwerfungsregel wie shared/weekly_report.py: eine Zeile ohne
      // Datum, ohne Kurs oder mit nicht lesbarem Kurs faellt heraus. Vorher
      // nahm JS sie mit — eine Zeile mit `close: null` am Stichtag wurde zum
      // Startpreis, und derselbe Datensatz ergab in Python drei Renditen und
      // in JS keine einzige (Codex, Abnahme 2026-10-08). Zwei Rechenwege mit
      // verschiedenen Eingangsfiltern sind keine Zwillinge.
      if (!r || !r.date || r.close === null || r.close === undefined) return;
      // Der Leerstring ist KEIN Kurs: `Number('')` ist 0, und 0 ist
      // endlich — die Zeile waere also durchgekommen und haette als
      // Startpreis 0 das ganze Jahr verworfen, waehrend Python sie
      // uebersprang und den Folgetag nahm. Gemessen: Python [0.5, 0.5,
      // 0.5], JS [] (Codex, Abnahme Runde 2).
      if (typeof r.close === 'string' && r.close.trim() === '') return;
      var close = Number(r.close);
      if (!isFinite(close)) return;
      var d = new Date(r.date);
      if (isNaN(d.getTime())) return;
      var y = d.getUTCFullYear();
      if (!byYear[y]) byYear[y] = [];
      byYear[y].push({ d: d, close: close });
    });

    var samples = [];
    var currentYear = ref.getUTCFullYear();
    Object.keys(byYear).forEach(function(y) {
      var yearInt = parseInt(y, 10);
      if (yearInt >= currentYear) return; // nur Vergangenheit
      var rows = byYear[y].sort(function(a, b) { return a.d - b.d; });

      // Stichtag im Vergleichsjahr, als UTC-Kalenderdatum. Der Schalttag faellt
      // auf den 28., statt auf den 1. Maerz zu rollen (VERTRAG, Punkt 2).
      var tag = refDay;
      if (refMonth === 1 && refDay === 29) {
        var schalt = new Date(Date.UTC(yearInt, 1, 29));
        if (schalt.getUTCMonth() !== 1) tag = VERTRAG.schalttagErsatz;
      }
      var refInYear = new Date(Date.UTC(yearInt, refMonth, tag));
      var startPrice = null;
      for (var i = 0; i < rows.length; i++) {
        if (rows[i].d >= refInYear) { startPrice = rows[i].close; break; }
      }
      // Das Vergleichsfenster muss VOLLSTAENDIG sein: die letzte Zeile des
      // Jahres muss im Jahresendmonat liegen. Sonst ist es keine
      // Jahresend-Rendite, auch wenn sie so heisst.
      var letzte = rows.length ? rows[rows.length - 1] : null;
      var endPrice = (letzte && letzte.d.getUTCMonth() === VERTRAG.jahresendeMonat)
        ? letzte.close : null;
      // Beide Preise muessen positiv sein (VERTRAG, Punkt 5).
      if (startPrice != null && startPrice > 0 && endPrice != null && endPrice > 0) {
        samples.push({
          year: yearInt,
          yStart: startPrice,
          yEnd: endPrice,
          ret: endPrice / startPrice - 1
        });
      }
    });
    // `zuDuenn` statt stillem Durchlassen: unter der Mindeststichprobe gibt es
    // keinen Prior (VERTRAG, Punkt 3). Vorher rechnete die Seite schon mit
    // EINEM Jahr, waehrend der Newsletter drei verlangte.
    return {
      samples: samples,
      n: samples.length,
      zuDuenn: samples.length < VERTRAG.minStichprobe
    };
  }

  /**
   * Prozent der Samples mit Return >= target. Lineare Interpolation
   * zwischen dem letzten Sample unter und dem ersten ueber target
   * (fuer feineren Prior bei kleinem n).
   */
  function empiricalAboveProbability(samples, targetReturn) {
    if (!samples.length) return null;
    return empiricalAboveCount(samples, targetReturn) / samples.length;
  }

  /** Die Fallzahl hinter dem Anteil. Eine Haeufigkeit ohne k und n laesst sich
   *  nicht einordnen: 40 % aus 2 von 5 Jahren ist etwas anderes als 40 % aus
   *  40 von 100. Bewusst eine eigene Funktion, damit der Rueckgabewert von
   *  `empiricalAboveProbability` unveraendert bleibt — er steht im
   *  Zwillingsvertrag mit shared/weekly_report.py. */
  function empiricalAboveCount(samples, targetReturn) {
    return samples.filter(function(s) { return s.ret >= targetReturn; }).length;
  }

  /**
   * Baut Divergenz-Tabelle fuer Crypto-Targets.
   * @param elementId    Container
   * @param ticker       'BTC-USD' oder 'ETH-USD'
   * @param assetMarkets polymarket markets fuer diesen Asset
   * @param latestPrices snapshots dict
   * @param priceRows    Preis-Historie fuer den Ticker (aus Supabase)
   * @param currentPrice aktueller Kurs (letzter close)
   */
  function renderCryptoDivergence(elementId, ticker, assetMarkets, latestPrices, priceRows, currentPrice) {
    var today = new Date();
    var histData = collectYearEndReturns(priceRows, today);

    var _en = !!(SA.i18n && SA.i18n.isEN && SA.i18n.isEN());
    var rows = assetMarkets.map(function(m) {
      var match = /^(btc|eth)-above-(\d+)k-2026$/.exec(m.slug);
      if (!match) return null;
      var targetK = parseInt(match[2], 10);
      var targetPrice = targetK * 1000;
      var requiredRet = currentPrice > 0 ? (targetPrice / currentPrice - 1) : null;
      // Kein Prior bei zu duenner Stichprobe — sonst steht auf der Seite eine
      // Zahl, die der Newsletter aus denselben Daten verweigert.
      var priorProb = (requiredRet != null && !histData.zuDuenn)
        ? empiricalAboveProbability(histData.samples, requiredRet) : null;
      var priorK = (priorProb != null)
        ? empiricalAboveCount(histData.samples, requiredRet) : null;

      var snap = latestPrices[m.condition_id];
      var marketProb = snap ? (snap.yes_price || 0) : 0;

      return {
        target: '$' + targetK + 'k',
        requiredRet: requiredRet,
        marketProb: marketProb,
        priorProb: priorProb,
        priorK: priorK,
        priorN: histData.n
      };
    }).filter(function(r) { return r; }).sort(function(a, b) {
      return parseInt(a.target.replace(/\D/g, ''), 10) - parseInt(b.target.replace(/\D/g, ''), 10);
    });

    var tbody = rows.map(function(r) {
      var mkt = (r.marketProb * 100).toFixed(1) + '%';
      // Ganze Prozent plus Fallzahl. Eine Dezimalstelle auf drei bis gut einem
      // Dutzend Jahren ist Schein: bei n=5 kann der Anteil nur 0, 20, 40 … sein,
      // „40,0 %" suggeriert eine Genauigkeit, die es nicht gibt.
      var pri = r.priorProb != null
        ? (Math.round(r.priorProb * 100) + '% <span style="color:var(--muted)">('
           + r.priorK + '/' + r.priorN + ')</span>')
        : '—';
      var reqRet = r.requiredRet != null ? ((r.requiredRet >= 0 ? '+' : '') + (r.requiredRet * 100).toFixed(1) + '%') : '—';

      var diverge = null, verdict = '—', cls = '';
      if (r.priorProb != null) {
        diverge = (r.priorProb - r.marketProb) * 100;
        // Nur die Richtung des ABSTANDS, kein Urteil darueber, welche der
        // beiden Zahlen richtig liegt. „Markt unterschaetzt" behauptete
        // genau das — und der Prior ist eine Haeufigkeit auf wenigen Jahren
        // (Codex-Befund 13).
        if (Math.abs(diverge) < VERTRAG.divergenzSchwellePp) {
          verdict = SA.i18n.t('pmjs.verdict_aligned', 'nahe beieinander'); cls = '';
        } else if (diverge > 0) {
          verdict = SA.i18n.t('pmjs.verdict_seasonal_above', 'Prior über Markt'); cls = 'pos';
        } else {
          verdict = SA.i18n.t('pmjs.verdict_market_above', 'Markt über Prior'); cls = 'neg';
        }
      }
      var divStr = diverge == null ? '—' : ((diverge >= 0 ? '+' : '') + diverge.toFixed(1) + 'pp');

      return '<tr>' +
             '<td>' + r.target + '</td>' +
             '<td style="text-align:right">' + reqRet + '</td>' +
             '<td style="text-align:right;font-weight:700;color:#fff">' + mkt + '</td>' +
             '<td style="text-align:right">' + pri + '</td>' +
             '<td style="text-align:right" class="' + cls + '">' + divStr + '</td>' +
             '<td class="' + cls + '" style="font-size:.75rem">' + verdict + '</td>' +
             '</tr>';
    }).join('');

    var label = (ticker === 'BTC-USD' ? 'Bitcoin' : 'Ethereum');
    var html =
      '<div style="font-size:.75rem;color:var(--muted);margin-bottom:.5rem">' +
        '<b style="color:var(--accent)">' + label + '</b> — ' +
        (_en
          ? (SA.i18n.t('pmjs.history_label') + ': ' + histData.n + ' ' + SA.i18n.t('pmjs.years_samples') + ' · ' + SA.i18n.t('pmjs.current_price') + ': $' +
            (currentPrice >= 10000 ? Math.round(currentPrice).toLocaleString() : currentPrice.toFixed(0)) +
            ' · ' + SA.i18n.t('pmjs.seasonal_prior_desc'))
          : ('Historie: ' + histData.n + ' vollständige Jahre · aktueller Kurs: $' +
            (currentPrice >= 10000 ? Math.round(currentPrice).toLocaleString() : currentPrice.toFixed(0)) +
            ' · Saisonal-Prior = Anteil dieser Jahre, in denen der benötigte Return ab dem heutigen'
            + ' Kalendertag bis Jahresende erreicht wurde. Jedes Jahr liefert genau ein Fenster;'
            + ' die Jahre sind nicht garantiert vergleichbar, weil sich das Marktregime ändert.')) +
      '</div>' +
      '<table class="perf-table" data-no-sort="1">' +
      '<thead><tr>' +
        '<th>' + (_en ? SA.i18n.t('pmjs.col_target_2026') : 'Ziel 2026') + '</th>' +
        '<th style="text-align:right">' + (_en ? SA.i18n.t('pmjs.col_required') : 'Benötigt') + '</th>' +
        '<th style="text-align:right">' + (_en ? SA.i18n.t('pmjs.col_market_yes') : 'Markt YES') + '</th>' +
        '<th style="text-align:right">' + (_en ? SA.i18n.t('pmjs.col_seasonal_prior') : 'Saisonal-Prior') + '</th>' +
        '<th style="text-align:right">' + (_en ? SA.i18n.t('pmjs.col_divergence') : 'Divergenz') + '</th>' +
        '<th>' + (_en ? SA.i18n.t('pmjs.col_assessment') : 'Bewertung') + '</th>' +
      '</tr></thead><tbody>' + tbody + '</tbody></table>';
    var el = document.getElementById(elementId);
    if (el) el.innerHTML = html;
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
             '<td>' + esc(m.slug) + '</td>' +
             '<td>' + esc(m.category) + '</td>' +
             '<td>' + esc(String(m.question || '').slice(0, 60)) + '</td>' +
             '<td style="text-align:right;font-weight:700;color:#fff">' + pct + '</td>' +
             '<td style="text-align:right" class="' + deltaCls + '">' + deltaStr + '</td>' +
             '<td style="text-align:right">' + liq + '</td>' +
             '</tr>';
    }).join('');

    var _en = !!(SA.i18n && SA.i18n.isEN && SA.i18n.isEN());
    var html = '<table class="perf-table" data-no-sort="0">' +
               '<thead><tr>' +
               '<th>Slug</th>' +
               '<th>' + (_en ? SA.i18n.t('pmjs.col_category') : 'Kategorie') + '</th>' +
               '<th>' + (_en ? SA.i18n.t('pmjs.col_question') : 'Frage') + '</th>' +
               '<th style="text-align:right">YES</th>' +
               '<th style="text-align:right">7d Δ</th>' +
               '<th style="text-align:right">' + (_en ? SA.i18n.t('pmjs.col_liquidity') : 'Liquiditaet') + '</th>' +
               '</tr></thead><tbody>' + rows + '</tbody></table>';

    var el = document.getElementById(elementId);
    if (el) {
      el.innerHTML = html;
      if (SA.makeSortable) { SA.makeSortable(el.querySelector('table')); }
    }
  }


  // ── Public API ────────────────────────────────────────────────────────────

  return {
    // Bewusst exportiert, damit das Inline-JS der Seite nicht eine ZWEITE
    // Maskierung mitschleppt — zwei Fassungen derselben Regel driften.
    esc: esc,
    loadCatalog: loadCatalog,
    loadLatestPrices: loadLatestPrices,
    loadHistory: loadHistory,
    computeFedDistribution: computeFedDistribution,
    collectYearEndReturns: collectYearEndReturns,
    empiricalAboveProbability: empiricalAboveProbability,
    empiricalAboveCount: empiricalAboveCount,
    renderFedDistChart: renderFedDistChart,
    renderFedTrendChart: renderFedTrendChart,
    renderRiskGauges: renderRiskGauges,
    renderCryptoLadder: renderCryptoLadder,
    renderCryptoDivergence: renderCryptoDivergence,
    renderHistoryMulti: renderHistoryMulti,
    renderMarketsTable: renderMarketsTable
  };
})();

window.SA = SA;

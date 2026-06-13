# UI-Patterns & Statistik-Gotchas — SeasonAlpha

> Detailregeln ausgelagert aus CLAUDE.md (Frontend-Charts/UI + Statistik/Math).
> Die wichtigsten 4-5 stehen als Kurzfassung weiter in CLAUDE.md.
> Plotly-Theme-Details (Streamlit, `shared/charts.py`): siehe [CHARTS.md](CHARTS.md).

## Charts & UI

### Streamlit / Plotly
- Charts via `apply_se_theme()`, Heatmaps via `apply_se_heatmap_theme()`
  (+ `tickformat=None` auf Kategorie-Achsen). **Inline `update_layout` VERBOTEN.**
- Plotly: `title=dict(text=..., font=dict(...))` statt `titlefont`.
  `add_shape`+`add_annotation` statt `add_vline` (crasht mit Strings).
- Heatmap Jahreslabels `f" {y} "` padden (erzwingt Kategorie), `text`+`texttemplate`
  statt Annotations.
- Heatmap (Monatszyklus): `apply_se_theme` + `dtick=1` (nicht
  `apply_se_heatmap_theme` + `type="category"`).
- Drawdown-Heatmap: `SE_DRAWDOWN_COLORSCALE` (Rot-Gradient, zmin=worst, zmax=0,
  NICHT symmetrisch).
- `st.metric` vermeiden → HTML-Flex-Karten (10px Label, 14px Wert).
- `significance_gauge` bei Mehrfach-Aufruf: `key_prefix`. `percentile_bar` unter
  Hauptcharts. `ticker_select()` statt direkte Selects (global persistiert).

### Frontend (ApexCharts, kein Plotly.js)
- Multi-Serie-Charts: **plain arrays mit null**, NICHT `{x,y}`-Objekte (bricht
  ApexCharts v4). Kein Mix `line`+`area`.
- ApexCharts v4 Multi-Axis: `seriesName`-Array unzuverlässig → separate
  Chart-Instanzen mit `chart.group:'xxx'` synchronisieren.
- Mixed Bar+Line Per-Wert-Coloring: `plotOptions.bar.colors.ranges:[{from:-Inf,
  to:-0.0001,color:RED},{from:0,to:Inf,color:GREEN}]`.
- Dynamische Y-Achse: explizite yMin/yMax aus Daten + `forceNiceScale:true`
  (ApexCharts auto-scale kann zu groß ausschlagen).
- Last-solid-Tag-Filter: `detectAnomalyEnd` + `computeDayCounts` — gelbe „wenige
  Daten"-Linie am Jahresrand.
- Sortierbare Tabellen: Auto via `SA.makeSortable` + MutationObserver. Opt-out:
  `<table data-no-sort="1">`.

### UI / Design (V3 Ultra)
- Farbschema: Pure Black + Signal Gold (#e8a820) + Neon Red/Green. Dark Mode First.
- Dashboard-Cards: `background:var(--card)` (#0a0a0e), `border:1px solid
  var(--border)`, `padding:1rem`. KEIN `linear-gradient(135deg,#0f1923,#131d2a)`.
- KPI-Standard: globale Klasse `.kpi`/`.kpi-label`/`.kpi-value` (+ `green`/`red`/
  `gold`) aus `landing/css/app.css`. Keine lokalen `.kpi-card`-Definitionen.
- Info-Badge + Hover-Tooltip: pure CSS via `.info-badge:hover ~ .info-tooltip`.
  Parent MUSS `position:relative`, KEIN `overflow:hidden`. Gradient-`::before` mit
  `border-radius:inherit`.
- Footer: 5 Expander (Impressum, Datenschutz, Legal Notice EN, Financial
  Disclaimer, Risk) via `shared/footer.py`.

## Statistik / Math

- **Quantile NIE via Floor-Indexing.** Lineare Interpolation wie numpy:
  `pos=q*(n-1); lo=floor(pos); hi=ceil(pos); return vals[lo]+(pos-lo)*(vals[hi]-vals[lo])`.
- Perzentil-Bänder Stable-Range-Trim: max-Sample-pro-Tag bestimmen, Rand
  abschneiden bis Sample ≥90% des Max — verhindert Spikes durch Sample-Set-Wechsel.
- Rolling Vola: ALLE Jahre konkatenieren → 1 Rolling-Std → wieder pro `(year, doy)`
  einsortieren. Sonst Warmup-NaN am Jahresanfang.
- `Math.min.apply(null, arr)` ist NaN-unsafe → manuelle Loop.
- TDOM-Statistiken mit n<10: ⚠ + 40% Opacity. MIN_N nur bei UNTERSCHIEDLICHEN n
  pro Punkt — bei Aggregat-Bars (Woche/Monat) hat jeder Balken gleiche n → immer
  rot/grün nach Vorzeichen, n im Tooltip.
- Stats null vs constant-fill: `avg/std/Detrend` nutzen full_365 direkt
  (constant-fill). `Perzentil/Drawdown/Heatmap` müssen
  `if (d >= yo.last_actual_day) continue` filtern.
- Heatmap `last_actual_day`-Filter NUR für CURRENT YEAR (sonst markiert Dezember
  fälschlich unvollständig wenn 31.12. Wochenende).
- **Backtest-Filter look-ahead-bias-frei:** `filterMask[entryIdx-1]`, NICHT
  `entryIdx`.
- Plain Vanilla offene Trades: Mark-to-Market mit `trade.open=true` → aus
  Stats/Equity/Significance filtern, in Tabelle zeigen.

## KI / Anomalie / Patterns

- Anomalie-Radar misst NUR 10 Tage (nicht YTD/Drawdown/Gesamt). Shared-Renderer
  `SA.decadeCompute.renderAnomalyInto(containerId, rows, ticker)` — einmal bauen,
  4× nutzen.
- KI Composite 4 Sub-Scores à 0-2.5 → 0-10. Bullish ≥6.5, Bearish ≤3.5.
  Client-side, vanilla JS.
- Musterpfad: `findMatchingYears` (Pearson/Euklid) + `computeTruePath`
  (gewichteter Ø + Glättung) + `computeProjection` (± σ-Cone).
- Präsidentenzyklus: 1=Wahl, 2=Nach, 3=Zwischen (NICHT „Mitte"!), 4=Vor. Formel
  `((year-2020)%4+4)%4+1`.

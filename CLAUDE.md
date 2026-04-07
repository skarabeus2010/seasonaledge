# CLAUDE.md — SeasonAlpha

> Version 27.4 | 2026-04-07 | Details → `docs/`


## Projekt

**SeasonAlpha** — Web-Plattform für saisonale Finanzmarkt-Analyse (ETFs, Aktien, Futures, Crypto).
Freemium + Premium. Phase 1: Streamlit + Supabase + Stripe.

## Entwicklung

```
Pfad:   C:\Dev\Seasonaledge\
Start:  py -m streamlit run seasonal_app.py
Python: PowerShell → immer `py -m` (nicht `python`)
```

## Projektstruktur

```
seasonal_app.py          ← Startseite
shared/                  ← Berechnungen, Daten, Utilities
  yahoo_downloader.py    ← HTTP-Downloader + Stooq-Fallback + OHLC Split+Dividend-Adjustierung (einziger Cache!)
  data.py                ← Supabase-First Daten-Layer + OHLC-Konsistenzcheck (Split+Dividend)
  calculations.py        ← Kern-Berechnungen
  charts.py              ← Plotly Theme (apply_se_theme)
  ki_score.py            ← KI Seasonal Score Engine (4 Sub-Scores → 0-10)
  tdom_analysis.py       ← TDoM Berechnungen (3 Strategien, Ranges, Heatmap)
  ai_models.py           ← DTW, Prophet, Isolation Forest, Claude API, KI-Summary, Anomalie-Heatmap
  anomaly_engine.py      ← Anomalie-Radar, Crash-Ampel, TDoM-Anomalien, Muster-Brueche
  mstl_decomposition.py  ← Multi-Saisonalitaets-Zerlegung (Trend/Woche/Jahr/Residual)
  chronos_forecast.py    ← Chronos-Bolt-Tiny 30d-Forecast mit Konfidenzbaendern
  neural_prophet_forecast.py ← NeuralProphet Saisonalitaets-Komponenten
  spot_vol_beta.py       ← Spot-Vol Beta (SPX vs VIX, Daily + Rolling + Regime-Wendepunkte)
  outlier_manager.py     ← Outlier-Filter (IQR, Winsorize, Isolation Forest)
  market_calendar.py     ← Feiertage/OPEX/Zentralbank → Supabase sync
  cache_manager.py       ← Computed Values Cache (DB → Fallback → Store)
  split_slider.py        ← 3-Layer Split-Slider
  supabase_client.py     ← DB-Connector + Subscriber + Market Events + Cache
  logger.py              ← 3 Log-Kanäle (app/error/access)
  cpi_data.py            ← CPI-Daten (BLS/FRED), Inflationsbereinigung
  shock_analysis.py      ← Shock Analyzer (Trigger→Target)
  sector_rotation.py     ← Sektor-Rotation Analyse
  significance_gauge.py  ← Signifikanztest (t-Test, Cohen's d) + Radial Gauge (key_prefix Support)
  percentile_bar.py      ← Perzentil Stat-Ribbon (Micro-Gauge, %ile, Z-Score)
  streak_analysis.py     ← Wiederverwendbare Streak-Analyse (W/L-Serien, HTML-Tabelle)
  footer.py              ← Footer: Blog-Links, Impressum, Datenschutz, Legal Notice EN, Financial Disclaimer, Risk Disclosure
  info_badge.py          ← ⓘ-Badge für Expander (DEPRECATED — nur noch in _disabled/ Pages)
  info_texts.yaml        ← Zentrale Erklärungs-Texte DE/EN (51 Einträge) → Datenquelle für 10_Methodik
  i18n.py                ← Internationalisierung DE/EN: t(), get_lang(), lang_toggle() (JS-basiert)
  ticker_autocomplete.py ← Search-as-you-type Ticker-Suche (Supabase + Debounce)
  indicators.py          ← Technische Indikatoren (SMA, EMA, RSI, BB, MACD, LBR)
  indicator_filter_ui.py ← Sidebar UI fuer Indikator-Filter (Pulldowns, Badges)
  tdoy_analysis.py       ← TDoY Berechnungen (9 Funktionen, dynamisch Aktien ~252 / Crypto ~365)
  trading_day_header.py  ← Trading Day Header (TDOM/TDOY Anzeige) + Converter Widget
  drawdown_analysis.py   ← Saisonaler Drawdown + Rolling Volatilitaet (DD-Serie, KPI, Heatmap, Recovery)
  strategies/            ← Strategie-Module
    plain_vanilla.py     ← 24 Plain Vanilla Strategien (Sell in May, KTI, UECS etc.)
    definitions.py       ← Strategie-Metadaten (65+ Eintraege)
    kaeppel.py           ← Jay Kaeppel Strategien
landing/                 ← Professionelle Landing Page (statisches HTML/CSS)
  index.html             ← Komplette Landing Page (inline CSS + vanilla JS)
  content.md             ← Content-Quelle (Markdown, wie Blog-Workflow)
  assets/                ← Fonts, Images (OG, Favicon)
  components/            ← Shared Nav + Footer (JS-Include)
    nav.html
    footer.html
  css/
    app.css              ← Gemeinsames Design System (V3 Ultra)
  js/
    app.js               ← Component-Loader + Supabase Client + Ticker-Autocomplete
    charts.js            ← ApexCharts Theme + Helpers (curve:'straight'!)
    seasonal-compute.js  ← Saisonale Berechnungen (buildYearData, TOM, Moon, etc.)
    decade-compute.js    ← Dekaden-Berechnungen (Drawdown, Percentile, Vola)
    strategy-compute.js  ← 22 Trading-Strategien + Equity + Stats + StopLoss + TrailingStop
    streak-analysis.js   ← Streak-Analyse (W/L-Serien, Tabelle)
    significance.js      ← Signifikanztest (t-Test, Cohen's d, CSS Gauges)
    indicators.js        ← Technische Indikatoren (SMA/EMA/RSI/BB/MACD/LBR)
    outlier.js           ← Outlier-Filter (IQR, Winsorize)
    holidays.js          ← Globaler Feiertags-Kalender (NYSE/XETRA/LSE, Gauss-Ostern)
  pages/
    dekadenzyklus.html   ← Dekaden-Analyse (12 Sektionen, Ticker-Wechsel)
    monatswechsel.html   ← Turn of the Month (TOM, Heatmap, Streak, Signifikanz)
    mondphasen.html      ← Mondphasen-Effekt (Voll/Neu/Supermond)
    kriegszeiten.html    ← 11 Kriege, Event-Window, Ukraine+Iran live
    crash-fruehwarnung.html ← Regime-Ampel + Risk-Score Backtest (IF aus DB)
    plain-vanilla.html   ← 22 Strategien, Equity, Signale, Signifikanz, Trailing Stop
    intermarket-shocks.html ← Intermarket Shock-Analyse (Trigger→Target, Scatter+Regression)
    sektor-rotation.html ← Sektor-Rotation (23 US-ETFs, Heatmap, Top/Flop, Win-Rate)
    overnight.html       ← Overnight vs. Intraday (OHLC, Signifikanz, Indikator-Filter)
    zentralbanken.html   ← Zentralbank-Effekt (Fed/EZB/BoE/BoJ, Event-Window, Streak)
    feiertage.html       ← Feiertags-Effekt (Exchange-aware, Ranking, Heatmap, Streak)
    apex-demo.html       ← Chart-Demo
  data/
    DJI-decade.json      ← Vorberechnete Dekaden-Daten
    chart-data.json      ← Landing-Slider Daten
  rechtliches.html       ← Impressum + Datenschutz + Risk
seo/                     ← Programmatic SEO Engine
  programmatic_seo_builder.py ← Generator: 94 Pages + Sitemap + Disclaimer
  seo_template.html        ← Jinja2 Landingpage-Template
  output/                  ← Generierte HTML + sitemap.xml + robots.txt
  tools/                   ← Tool-Landingpages (statisches HTML)
    trading-day-converter.html ← SEO-Landingpage: CDOY/TDOM/TDOY Converter (JS-Client)
blog/                    ← Blog Engine (Markdown → statisches HTML)
  blog_builder.py          ← Generator: MD → HTML + Charts + Social + YouTube
  templates/               ← Jinja2 Blog-Templates (Post, Index, Kategorie)
  posts/                   ← Markdown Blog-Posts (Frontmatter + Content)
  posts/images/            ← Blog-Screenshots (committed, wird beim Build nach output/ kopiert)
  prompts/                 ← Claude API Prompt-Templates (6 Templates)
  calendar.yaml            ← Redaktionsplan
  output/                  ← Generierte HTML (.gitignore)
.claude/
  blog-tutorial.md         ← Blog-Skill: SEO-optimierte Tutorial-Artikel schreiben (force-committed)
scripts/                 ← Batch-Jobs
  nightly_refresh.py     ← Nightly DB Refresh (5 Phasen: Calendar, Ticker, Health, Regime, Log)
  intraday_refresh.py    ← Intraday Kurs-Updates (EU/US/Asien/FX/Crypto, alle 30 Min)
  compute_regime_scores.py ← Isolation Forest Regime-Scoring (SPY, --full / --incremental)
  create_market_tables.sql ← SQL-Schema für Cache-Tabellen
  create_regime_scores.sql ← SQL-Schema für regime_scores Tabelle
pages/                   ← Light Live + Premium Pages
  Light Live (aktiv, 10 Pages):
    00_Home              ← Startseite (Hero, 3x3 Kacheln, Slider, Stats, Newsletter)
    01_Dekadenzyklus     ← 131 Jahre DJI, Dekaden-Kohorten, Anomalie-Radar,
                            Perzentil-Statusbar, Kontext-Panel (kompakte Karten),
                            Heatmap Dekade×Monat, Box-Plot (alle in Expandern)
    02_Jahreszyklus      ← Saisonaler Jahresverlauf, Pressure Chart, Detrend,
                            Anomalie-Radar, Praesidentenzyklus, Outlier Manager,
                            Monats-Signifikanz (12 Tachos), Quartals-Signifikanz,
                            Praesidentenzyklus-Signifikanz (4 Tachos),
                            Praesidentenzyklus Best Match (DTW + Korrelation),
                            Perzentil-Statusbar, Perzentil-Baender (25./75.),
                            Monats-/Quartals-Perf, 10J-Heatmap, We-are-here Marker
    03_Monatszyklus      ← Intra-Monat TDOM-Verlauf, Detrend-Indikator (Expander),
                            Wochen-/Monats-/Two-Week-Performance, 10J-Heatmap,
                            We-are-here TDOM-Marker, Praesidentenzyklus-Filter,
                            Perzentil-Statusbar, Outlier, Live-Chart Overlay,
                            Seasonal Match (Korrelation + DTW), Cycle Match,
                            Two-Week Heatmap/Ranking/Momentum/Signifikanz
    04_Wochentage        ← Wochentag-Renditen (Expander), Praesidentenzyklus,
                            Heatmap (gelber Rahmen, 2 Nachkommastellen),
                            Signifikanztest (Expander),
                            Alle-Modi-Signifikanz (4 Rendite-Modi × 5 Tage),
                            Kumulierter Wochenverlauf, Overnight/Intraday Split,
                            Konsekutiv-Analyse, Quartals-Performance, Volatilitaet,
                            Monat×Wochentag Heatmap, Top-10 Kombinationen,
                            **Indikator-Filter** (SMA/EMA/RSI/BB/MACD/LBR)
    05_Monatswechsel     ← Turn of the Month, TOM Heatmap (apply_se_heatmap_theme),
                            Signifikanztest (Expander), Streak-Analyse,
                            Perzentil-Statusbar, TOM Stats (kompakte Karten),
                            Window-Optimierung, Praesidentenzyklus-TOM,
                            **Indikator-Filter** (SMA/EMA/RSI/BB/MACD/LBR)
    06_Mondphasen        ← Voll-/Neumond-/Supermond-Effekt,
                            Signifikanztest (Expander, Default ON),
                            Mond-Heatmap (Monat × Phase),
                            Perzentil-Statusbar, naechste Mondphasen,
                            Lunar-Kalender, Supermond-Vergleich,
                            **Indikator-Filter** (SMA/EMA/RSI/BB/MACD/LBR)
    07_Januar_Trifecta   ← Premium Ampelsystem (Glow-Karten, Badges),
                            Ø-Verlauf je Signal + Aktuelles-Jahr-Overlay (gold),
                            Max Drawdown (kompakte Karten),
                            Jahresrendite nach Signal, Historische Tabelle
    08_Kriegszeiten      ← Krieg vs. Frieden Saisonalitaet (disabled)
    10_Methodik          ← Methodik & Erklärungen: alle Analyse-Methoden zentral
                            (ersetzt verteiltes ⓘ-Badge-System, Quelle: info_texts.yaml)
    11_Saisonal_Events_Kalender ← Fed/EZB/OPEX/Mond/Feiertage 12 Monate (disabled)
  Disabled (pages/_disabled/):
    09_Crash_Fruehwarnung← KI-Ampel: Isolation Forest Regime-Erkennung
    91_Uebernacht_Strategien ← Overnight vs Intraday
    98_Datenschutz       ← (jetzt im Footer-Expander)
    99_Impressum         ← (jetzt im Footer-Expander)
  Premium (inaktiv):
    80-92                ← Erweiterte Analyse, Feiertag, Zentralbanken, TruePath,
                            OPEX, Shock, Sector, KI Score, Scanner, Premium, TDOM,
                            Spot-Vol Beta
  unsubscribe.py         ← Newsletter-Abmeldung
docs/                    ← Ausgelagerte Dokumentation
```

## Kern-Methodik: NORMALISIERTE RENDITEN

Prozentuale Renditen normiert auf 100 — NICHT absolute Preisänderungen.
Jedes Jahr startet bei 100, tägliche Returns kumulieren darauf.
**Niemals** TradingView-Methode (priceChange = close - close[lookback]).

## Import-Header (PFLICHT in jeder Page)

```python
import sys, os, pathlib
try:
    _project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
except NameError:
    _project_dir = os.getcwd()
if not os.path.isdir(os.path.join(_project_dir, "shared")):
    for _candidate in [os.getcwd(), os.path.dirname(os.path.abspath(sys.argv[-1])) if sys.argv else ""]:
        if os.path.isdir(os.path.join(_candidate, "shared")):
            _project_dir = _candidate
            break
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)
```

## Kritische Regeln

| Regel | Details |
|-------|---------|
| `import yfinance` VERBOTEN | `from shared.yahoo_downloader import download_data` |
| Cache NUR in `yahoo_downloader.py` | Kein `@st.cache_data` anderswo |
| `df.index[0].strftime()` verboten | `df['Date'].iloc[0].strftime()` |
| Plotly `titlefont` deprecated | `title=dict(text=..., font=dict(...))` |
| Plotly `add_vline` mit Strings crasht | `add_shape` + `add_annotation` |
| `print()` für Debug verboten | `app_logger.debug()` verwenden |
| API-Keys niemals in Code | `os.environ["KEY"]` + Streamlit Secrets |
| `logs/` niemals in Git | Steht in `.gitignore` |
| Split-Slider: 3-Layer-Architektur | Achsen in eigenem Layer ohne clip-path |
| Handelstage, nicht Kalendertage | Immer Trading Days zählen |
| Charts: immer `apply_se_theme()` | `from shared.charts import apply_se_theme` |
| Heatmaps: `apply_se_heatmap_theme()` | + `tickformat=None` auf Kategorie-Achsen |
| Inline `update_layout` VERBOTEN | Nur `apply_se_theme()` + chart-spezifische Overrides |
| `significance_gauge`: key_prefix | Bei Mehrfach-Aufruf `key_prefix` übergeben |
| `st.metric` für kompakte Karten vermeiden | HTML-Karten (10px Label, 14px Wert) verwenden |
| Perzentil-Bar unter Hauptcharts | `from shared.percentile_bar import render_percentile_bar` |
| Ticker-Auswahl: `ticker_select()` | Speichert global in `session_state` → bleibt bei Page-Wechsel |
| Indikator-Filter: `indicator_filter_sidebar()` | `from shared.indicator_filter_ui import indicator_filter_sidebar` |
| TDOY: `from shared.tdoy_analysis import ...` | Dynamisch: Aktien ~252, Crypto ~365 Handelstage |
| Trading Day Header: `render_trading_day_header(df)` | `from shared.trading_day_header import render_trading_day_header` |
| Drawdown: `from shared.drawdown_analysis import ...` | base=100.0 fuer alle Kurven (auch Log-Return bei 0 startend) |
| Drawdown-Heatmap: `SE_DRAWDOWN_COLORSCALE` | Rot-Gradient, zmin=worst, zmax=0 (NICHT symmetrisch) |
| Recovery: `compute_real_recovery(df, year)` | Echte Tage bis Peak-Preis ueberschritten, auch ueber Jahresende |
| SEO Tools: `seo/tools/*.html` | Statisches HTML, Nginx /tools/ Route, JS-Client |
| Stooq: Session-Cookie erforderlich | `session.get("https://stooq.com/")` vor CSV-Download |
| Indikator-Berechnung: `indicators.py` | SMA, EMA, RSI, Bollinger, MACD, LBR + `apply_indicator_filter()` |
| Blog: `blog/blog_builder.py` | `--build` (HTML) oder `--generate` (KI-Entwurf) |
| Blog-Screenshots: `blog/posts/images/` | Committed → wird beim Build nach output/ kopiert |
| i18n: `from shared.i18n import t, lang_toggle, get_lang` | `lang_toggle()` VOR sidebar-Blöcken aufrufen |
| Heatmap (Monatszyklus): `apply_se_theme` + `dtick=1` | Nicht `apply_se_heatmap_theme` + `type="category"` |
| Heatmap Jahreslabels: `f" {y} "` padden | Plotly interpretiert `"2021"` als Zahl → Leerzeichen erzwingt Kategorie |
| Heatmap Text: `text`+`texttemplate` | Statt `_add_heatmap_annotations` → bessere Positionierung |
| Overnight/Intraday: Residual-Ansatz | `overnight = total - intraday` (NICHT `Open/Close.shift(1)`) |
| OHLC Cross-Day Berechnung verboten | `Open[t]/Close[t-1]` mischt verschiedene adj_factors → Dividend-Bias |
| Nightly-Refresh: nur 5 Tage | Historische Daten bleiben unveraendert in Supabase |
| Nightly-Refresh Phasen | A=Calendar, B=Ticker-Daten, C=Health-Check, E=Regime-Scores, D=Log, Z=Heartbeat |
| Regime-Scores: Isolation Forest | `compute_regime_scores.py --full` (historisch) / Phase E (inkrementell) |
| regime_scores Tabelle | RLS enabled, anon=SELECT only, Schreiben via GRANT ALL |
| `log_return` Spalte in Supabase | Vorberechnet, wird von preprocess() genutzt wenn vorhanden |
| `from shared.data import download_data` | NICHT `from shared.yahoo_downloader` (Supabase-First!) |
| TDOM/TDOY: boersenspezifisch | `render_trading_day_header(df, ticker=ticker)` — IMMER ticker uebergeben |
| Holiday-Kalender: `symbols.py` | `get_exchange_for_holidays(ticker)` → NYSE/XETRA/LSE/EURONEXT/TSE |
| TDOM/TDOY +1 Logik | `is_trading_day(today, exchange)` — NICHT `weekday < 5` |
| Intraday Refresh: Zeitfenster | Boerse offen → laden. KEINE festen Zeitslots mehr |
| FOREX Exchange: `is_trading_day()` | Mo-Fr, keine Feiertage (Karfreitag = offen) |
| CRYPTO Exchange: `is_trading_day()` | Immer True (24/7 inkl. Wochenende) |
| Frontend Feiertage: `holidays.js` | `SA.holidays.detect(ticker)` → NYSE/XETRA/LSE/NONE |
| Karfreitag: Gauss-Algorithmus | `SA.holidays.goodFriday(year)` / `SA.holidays.easter(year)` |
| Feiertags-Signale: Exchange-aware | Nur NYSE-Feiertage fuer US-Ticker, XETRA fuer DE-Ticker |
| Landing Page: statisches HTML | `landing/`, nginx liefert direkt aus |
| Streamlit App: unter `/app/` | nginx proxy_pass mit trailing slash |
| Neue HTML-Pages: `landing/pages/` | Nutzen `app.css` + `app.js` + `charts.js` |
| Nav + Footer: JS-Include | `/landing/components/nav.html`, `footer.html` |
| Frontend-Charts: ApexCharts (CDN) | Theme in `charts.js`, kein Plotly.js im Frontend |
| Daten: Pre-computed JSON | `landing/data/`, Generator-Scripts in `scripts/` |
| Docker JSON-Transfer | Im Container generieren, `docker cp` auf Host fuer nginx |
| Sortierbare Tabellen | `SA.makeSortable(table)` + MutationObserver Auto-Init in app.js — alle `<table>` mit `<thead>` oder erster Zeile mit `<th>` sind automatisch sortierbar. Opt-out: `<table data-no-sort="1">` |
| OPEX-Datum (Aktien/Index) | `SA.holidays._nthDow(y, m, 5, 3)` = Kalender-3.Fr. Bei NYSE-Feiertag (Good Friday, Juneteenth, ...) auf **vorherigen Handelstag** vorverlegt (meist Do). Pro Jahr ~1 Verschiebung. Triple Witching = Mar/Jun/Sep/Dez (`TRIPLE_MONTHS=[3,6,9,12]`) |
| VIXpiration (CBOE-Regel) | Settlement = **Kalender-3.Freitag − 30 Kalendertage** (ergibt Mi). Ist ENTWEDER Basis-Freitag ODER Settlement-Mittwoch ein Feiertag → Settlement −1 HT (→ Di). Letzter VIX-HT = Settlement −1 HT. Wichtige Faelle: 04/2025 (Good Friday) → VIX 18.03 Di, 06/2026 (Juneteenth) → VIX 19.05 Di |
| KPI-Funktion `kpi(l,v,c)` | PFLICHT: `<div class="kpi"><div class="kpi-label">..</div><div class="kpi-value ..">..</div></div>` — NICHT `<span>`-basiert (kein Leerzeichen zwischen Label/Wert sichtbar). Classes: `green` / `red` / `gold` (in `app.css`). Regex-Auto-Reduktion: `kpi__value--green` → `green`. |
| `SA.streaks.renderStreakTable(groups, colHeader, nBlocks)` | `nBlocks` MUSS eine Zahl sein! Wird `nBlocks` als String übergeben, liefert `slice(0, "string")` → `[]` und keine W/L-Kacheln erscheinen. IMMER `10` explizit als 3. Argument. Subtitle als separates `<p>` davor rendern. |
| Dynamische Y-Achse (Backtest Bar) | Min/Max explizit aus Daten: `yMin=min(rets)-range*0.12, yMax=max(rets)+range*0.12, forceNiceScale:true`. ApexCharts auto-scale kann gross ausschlagen (z.B. ±10% bei ±1% Range). |
| Monats-Checkboxen Mask-Pattern | Für Multi-Month-Filter (OPEX, VIX): 12-Bool-Array `xxxMonthsMask`, sidebar-checkboxen mit `data-month`-Attribut, `All`/`None`-Buttons. Filter wirkt auf **alle** Render-Funktionen (KPIs, Heatmap, Backtest, Signifikanz, Streak) + versteckt Charts im Grid. |
| Mode-basiertes Layout | Exklusives Radio `<input type="radio" name="mode">` für Top-Level-Umschaltung (OPEX/VIX). Sidebar-Optionen via `#opts-xxx`-Divs mit `display:none` gesteuert. `showSections()` steuert Sichtbarkeit der `<details>`-Sektionen je Modus. |
| Mini-Chart-Grid `chart-grid-12` | CSS-Grid 4/3/2 Spalten responsiv. Pattern: `miniCharts[]`-Array, `container.innerHTML=''` + loop mit `wrap.className='mini-chart'` + `container.appendChild(wrap)` + `new ApexCharts(wrap, {...})` + `miniCharts.push(chart)`. `destroyAll()` muss das Array durchlaufen. |
| Kumulierte Verlaufs-Charts | Helper `toCumSeries(means)` startet bei 0, akkumuliert; `makeCumLabels(before, after)` liefert `['Start','t-3',...,'t=0',...,'t+3']`. Für Event-Windows: Verlauf statt Bar-Chart. |
| Badge-Styles (brighter) | Für Tabellen-Badges auf dunklem BG: `background:rgba(color,.35); color:#ffffff; border:1px solid rgba(color,.7); text-shadow:0 1px 2px rgba(0,0,0,.3)`. NICHT dunkle Farbe auf transparentem BG (schlecht lesbar). |
| Signifikanz mode-aware | `renderSignificance(windows, label, viewContext)` mit viewContext `'triple'`/`'monthly'`/`'vix'`. Liefert passende Anzahl Spalten (5/7/dynamisch) und respektiert `xxxMonthsMask`. |
| Info-Badge + Hover-Tooltip (pure CSS) | Für Karten mit Erklärungsbedarf: `.info-badge` (22px Kreis mit "i", absolute top:.75rem right:.75rem) + `.info-tooltip` (340px Popup, position:absolute, top:2.65rem). Trigger via `.info-badge:hover ~ .info-tooltip` Sibling-Selektor, ohne JS. Parent MUSS `position:relative` haben und darf KEIN `overflow:hidden` setzen (sonst wird Tooltip geclippt); Gradient-`::before` stattdessen mit `border-radius:inherit`. Tooltip bleibt sichtbar bei `.info-tooltip:hover` → User kann Text lesen. |
| Multi-Serie Line-Chart (robust) | IMMER plain arrays von fester Länge (365 für Jahresverläufe) mit `null` für fehlende Punkte — NICHT `{x,y}`-Objekte (bricht Rendering in ApexCharts v4). Serien-Typ durchgehend `line` (kein Mix mit `area`). Per-Serie stroke width + dashArray über parallele Arrays. x-Achse `type:'category'` mit String-Kategorien `'1'..'365'`. Tooltip-Formatter nutzt `opts.dataPointIndex` für robuste Tag-Mapping. |
| Musterpfad / TruePath Pattern | `findMatchingYears(yearData, currentYear, method, topN)` via Pearson-Korrelation oder normalisierter Euklid-Distanz über aktueller Jahresverlauf (bis Heute). `computeTruePath(matches, smoothing)` = gewichteter Ø der Top-N Jahre (Ähnlichkeit als Gewicht) mit Rolling-Mean-Glättung. `computeProjection(matches, fromDoy, projDays)` = Forward-Projektion mit Upper/Lower Standard-Deviation-Cone. |
| KI Composite Score Pattern | 4 Sub-Scores à 0-2.5 Punkte → Total 0-10. Signal-Thresholds: Bullish ≥6.5, Neutral, Bearish ≤3.5. Client-side pragmatische Sub-Scores: (1) Anteil positiver Match-Jahre, (2) Musterpfad 30d-Forward-Return → `clip((x+3)/6, 0, 1)`, (3) Win-Rate aktueller Monat, (4) Tracking = 0.7×corr + 0.3×(1-normMAE). Keine Python/Prophet-Abhängigkeit, rein Vanilla-JS. |
| Radar-Chart via ApexCharts | `chart.type:'radar'`, Serien als einfaches Array mit Werten, `xaxis.categories` für Achsen-Labels, `yaxis.min/max` für feste Skala (0-2.5). `plotOptions.radar.polygons` für dezente Hintergrund-Polygone. `dataLabels.background.foreColor:'#000'` + gold Border für Kontrast auf dunklem BG. |
| Präsidentenzyklus-Labels | Standard-Mapping: 1=Wahljahr, 2=Nachwahljahr, 3=Zwischenwahljahr (NICHT "Mitte"!), 4=Vorwahljahr. Formel: `((year - 2020) % 4 + 4) % 4 + 1`. Englisch: Election / Post-Election / Midterm / Pre-Election Year. |
| Constant-Fill für full_365 | Python-kompatibel: Tage NACH `last_actual_day` werden mit dem letzten echten Wert konstant gefüllt (nicht null). Sonst springt avg() am Jahresende wenn unvollständige Jahre wegfallen. JEDES year-Objekt hat ein `last_actual_day` Feld, das Stats-Funktionen zum Filtern nutzen. |
| Stats null vs constant filtering | avg/std/Detrend nutzen full_365 direkt (constant-fill, smooth wie Python). Perzentil/Drawdown/Heatmap müssen `if (d >= yo.last_actual_day) continue` filtern, sonst verzerren extrapolierte Konstanten die Verteilung (DJI percentile flat-line bug von früher). |
| ApexCharts v4 Multi-Axis Workaround | `seriesName`-Array auf einer yaxis funktioniert in v4 für Line-Charts NICHT zuverlässig — Chart rendert leer. Stattdessen: separate ApexCharts-Instanzen mit `chart.group:'mygroup'` synchronisieren. Jede hat eigene auto-skalierte Y-Achse, x-Achse + Hover sind synchron. Beispiel: `jahreszyklus.html` rendert avg/bands im Hauptchart, Einzeljahre + Gann Pressurechart in separaten Sub-Charts darunter — 3 ApexCharts-Instanzen via `chart.group:'jzklus-sync'`. |
| Quantile-Berechnung NIE Floor-Indexing | `vals[Math.floor(n*0.75)]` ist FALSCH — bei n=4 gibt es das Maximum statt 75%-Perzentil. IMMER lineare Interpolation wie numpy: `pos = q*(n-1); lo=floor(pos); hi=ceil(pos); return vals[lo] + (pos-lo)*(vals[hi]-vals[lo])`. Beispiel: `jahreszyklus.html` `quantile()` helper für Perzentil-Bänder. |
| Perzentil-Bänder Stable-Range-Trim | Bei wechselnden Sample-Größen pro DOY (Wochenende/Feiertage am Jahresrand) entstehen visuelle Spikes. Fix: maximales Sample pro Tag bestimmen, dann Rand beidseits abschneiden bis zum ersten/letzten Tag wo Sample ≥ 90% des Maximums. Plus min-N ≥ 80% der Jahre. Verhindert Quantil-Sprünge durch Sample-Set-Wechsel. |
| Rolling Vola jahresgrenzen-übergreifend | Pro-Jahr-Rolling hat Warmup-NaN am Jahresanfang → Januar-Vola unrealistisch. Fix: log_returns aller Jahre KONKATENIEREN, dann eine einzige Rolling-Std über die Gesamtserie, anschließend pro `(year, day_of_year)` in eine `yearVolaMap` einsortieren. Damit nutzt z.B. die 20d-Vola am 5. Januar automatisch Dezember-Vorjahres-Daten. Beispiel: `avgRollingVolatility` in `jahreszyklus.html`. |
| Heatmap last_actual_day Filter | Nur für CURRENT YEAR anwenden! Vergangene Jahre haben oft last_actual_day=363 weil 31.12. ein Wochenende war — `b[1]=365 > 363` würde Dezember fälschlich als unvollständig markieren. Vergleich: `(d+1) > yo.last_actual_day` (d ist 0-basiert, last_actual_day 1-basiert). |
| `Math.min.apply(null, arr)` ist NaN-unsicher | Wenn ein einziges Element NaN ist, gibt `Math.min.apply` NaN zurück → propagiert in alle abhängigen Berechnungen. Für robuste Min/Max immer **manuelle Loop** mit `_clean()`-Filter oder direkte NaN-Prüfung verwenden. Beispiel: `computeDetrend` in jahreszyklus. |
| `splitSolidWeak(arr, lastSolid)` Pattern | Splittet eine 365-Tag-Serie in zwei Teile: solid (Tag ≤ lastSolid) und weak (Tag > lastSolid). Beide haben 365 Punkte mit nulls in den inverse-Bereichen. Der letzte solide Punkt wird ZUSÄTZLICH in der weak-Serie gehalten (Bridge), damit die Linien visuell verbunden sind. Wird im Jahreszyklus für die gelbe „⚠ wenige Daten" Linie genutzt. |
| `detectAnomalyEnd(arr)` für visuelle Sprünge | Erkennt vertikale Sprünge am rechten Rand: berechnet 95-Perzentil der Day-to-Day Deltas im Mittelteil (Tag 30-330), Anomalie-Schwellwert = `max(p95 * 4, 0.5)`. Scannt vom Ende rückwärts, gibt 1-basierten letzten stabilen Tag zurück. Kombiniert mit count-based threshold via `Math.min(dc.lastSolid, anomalyEnd)`. |
| `computeDayCounts(yearData)` Schwellwert | Python-konform: zählt **echte** Handelstage aus `days[]` (nicht interpolierte full_365). minN = max(nYears × 50%, 3). Iteriert vom Tag 365 rückwärts, findet ersten Tag mit count ≥ minN als `lastSolid`. Für SPY/^DJI mit normalen Zeiträumen typischerweise lastSolid=365 (keine gelbe Linie). |
| Math vs Rendering Trennung | Rendering-Funktionen (`renderXxx`) sollten KEINE Math machen. Statt inline Berechnung: erst eine `compute*()`-Funktion aufrufen die ein pures Datenobjekt zurückgibt, dann das Objekt rendern. Beispiel: `JZ.computeDetrend(avg)` statt inline raw/min/max im Renderer. Erlaubt Wiederverwendung + Tests. |
| Frontend Trading Day Header | `SA.renderTradingDayHeader(el, ticker, rows)` — wenn heute Handelstag → frisch vom Monats-/Jahresanfang berechnen (via SA.holidays), NICHT aus DB-Rows lesen |
| TDOM-Strategie Cross-Month | Entry negativ + Exit positiv → Exit im nächsten Monat suchen (Turn-of-the-Month-Muster) |
| MIN_N = 10 Threshold | TDoM/TDoY-Statistiken mit n<10 mit ⚠ + 40% Opacity markieren (aus `03_Monatszyklus.py`) |
| MIN_N nur fuer per-Punkt-Filterung | MIN_N=10 macht nur Sinn wo Punkte UNTERSCHIEDLICHE n haben (TDOM-Charts mit Solid/Weak Split). Bei Aggregat-Bars (Wochen/Monats/Two-Week-Performance) hat JEDER Balken die GLEICHE n — Filter fuehrt zu "alle grau" bei kurzem Zeitraum. Loesung: Immer nach Vorzeichen rot/gruen, n im Tooltip. |
| Trading Day Header zentrales Modul | `SA.renderTradingDayHeader(elementOrId, ticker, rows)` in `landing/js/app.js`. Akzeptiert SOWOHL String-ID als auch Element-Objekt. Format: `Heute: Di 07.04.2026 · ^GSPC · TDOM 4/21 · TWOY 15/53 · TDOY 65/252 · Q2 · MidTerm`. Reihenfolge: TDOM → TWOY → TDOY → Q → Cycle. Berechnet alles boersenspezifisch via `SA.holidays.detect()` — JEDE Page muss `holidays.js` laden! Quartal+Cycle aus `new Date()` zur Render-Zeit (dynamisch). |
| Multi-Month-Filter Pattern | 12 Checkboxen + Master-Toggle "Alle/Keine" wie Monatswechsel/Wochentage. `getSelectedMonths()` Helper, default alle aktiv. Filter wird via `monthFilter.length < 12` aktiv (sonst no-op). Wirkt NICHT auf Sektionen die schon monatsspezifisch sind (Heatmaps, Weekend-Effekt) — Top/Flop Tabellen wuerden sonst verfaelscht. |
| KPI-Card Standard-Style | `.kpi-card` mit `linear-gradient(135deg,#0f1923,#131d2a)`, Border `rgba(232,168,32,.12)` mit Hover `.3`, `border-radius:12px`, `padding:.85rem 1.1rem`, `text-align:center`. Label `.lbl` 10.5px #a89878 uppercase letter-spacing .08em, Value `.val` 1.25rem font-weight 800 #e2e8f0 monospace. Niemals plain dunkel ohne Akzente — gold-Border ist das Markenzeichen. |
| KPI Standard via app.css | **PFLICHT**: nutze die zentrale `.kpi` / `.kpi-label` / `.kpi-value` Klasse aus `landing/css/app.css`. Color-Classes: `green` / `red` / `gold`. Helper-Pattern: `<div class="kpi"><div class="kpi-label">..</div><div class="kpi-value green">..</div></div>`. KEINE lokalen `.kpi-card` Definitionen — die produzieren "Streamlit-Style" der vom Standard abweicht. Backtest Engine hatte den Bug — bewusst auf die globale Klasse umgestellt. |
| Backtest Filter look-ahead-bias-frei | Technische Filter im Backtest werden auf `filterMask[entryIdx-1]` (Vortag!) geprüft, NICHT auf `entryIdx` selbst. Sonst hätte man Look-Ahead-Bias: Filter würde Information vom Trade-Tag nutzen die eigentlich erst beim Close verfügbar wird. Pattern: `filterMask = SA.indicators.applyFilter(closes, filters); if (mask && entryIdx > 0 && !mask[entryIdx-1]) continue;` |
| FOMC-Daten als JS-Array | FOMC-Termine sind nicht algorithmisch berechenbar (Fed entscheidet ad-hoc). Lösung: `landing/js/fomc-dates.js` mit allen Daten 2000-2026 als JS-Array eingebettet (224 Einträge, ~5KB). Per Jahr gefiltert via `window.SA_FOMC_DATES.filter(d => d[0] === year)`. Update jährlich aus `shared/fed_dates.py` regenerieren via `py -c "from shared.fed_dates import FOMC_MEETING_DATES; ..."`. |
| Custom Tab-Navigation Pattern | Statt `<details>`-Tabs für komplexe Pages: Custom Tab-Bar mit `.tab-nav button` (gold-accent active) + `.tab-content` divs. Active-Toggle via `classList.add/remove('active')`. Beispiel: Backtest Engine mit 4 Tabs (Single, Optimization, Walk-Forward, Event-Relevance). Sauberer als nested details. |
| ApexCharts Mixed Bar+Line Coloring | `colors:[seriesColorBar, seriesColorLine]` faerbt nur Serien-weise. Fuer per-Wert Bar-Coloring (rot/gruen nach Vorzeichen) in Mixed Bar+Line Charts: `plotOptions.bar.colors.ranges:[{from:-Inf,to:-0.0001,color:RED},{from:0,to:Inf,color:GREEN}]`. Linie behaelt ihre Serien-Farbe. |
| ApexCharts Marker Hover-only | `markers:{size:0, hover:{size:4-5}}` zeigt Marker nur beim Hover. Sauberer fuer Linien-Charts mit vielen Punkten. Statt `size:4` was permanent Punkte zeichnet. |
| Tacho-Karten Schrift-Standards | `.mc-name` 14px font-weight:700 #e2e8f0 (Tacho-Titel). `.mc-details` 12px #cbd5e1 (Stats unter Tacho — NICHT #64748b, das ist zu dunkel auf dunklem BG). Numerischer Wert IM Tacho (1.2rem #fff), Status-Label UNTER dem Tacho mit `text-align:center;font-size:.875rem;font-weight:700` in Status-Farbe. Niemals lange Text-Strings wie "Signifikant abweichend" im Tacho — die ueberlagern den Halbkreis. |

## Architektur-Prinzipien

- Berechnungen → `shared/`, UI → `pages/`
- Kein Copy-Paste von Logik zwischen Pages
- Wiederverwendbare Charts → `distribution_charts.py`
- Signifikanztests → `significance_gauge.py` (t-Test + Gauge, key_prefix bei Mehrfach-Nutzung)
- Perzentil-Statusbar → `percentile_bar.py` (Micro-Gauge Ribbon unter Charts)
- Chart-Styling NUR via `apply_se_theme()` — keine inline Layouts
- Heatmaps → `apply_se_heatmap_theme()` + `tickformat=None` auf Kategorie-Achsen
- Footer (Impressum/Datenschutz/Legal Notice/Financial Disclaimer/Risk) → `shared/footer.py` als 5 Expander
- Mehrsprachigkeit → `shared/i18n.py`: `t("key")` für Strings, `lang_toggle()` für DE/US-Flaggen (JS-basiert, VOR sidebar)
- Kompakte Karten statt `st.metric` → HTML-Flex-Karten (Dark Mode, farbcodiert)
- Alle Sektionen in Expander verpacken (Default ON/OFF je nach Relevanz)
- Ticker-Auswahl → `ticker_select()` (speichert global, bleibt bei Page-Wechsel)
- Indikator-Filter → `indicator_filter_ui.py` (Sidebar, 0-4 Filter, UND-Verknuepfung)
- Blog → `blog/blog_builder.py` (Markdown → HTML + Charts + Social + YouTube)
- Methodik-Erklärungen → `pages/10_Methodik.py` (zentrale Referenz, Quelle: `info_texts.yaml`)
- `render_info_badge()` NICHT mehr verwenden → Erklärungen gehören auf die Methodik-Page
- TDOY-Analyse → `tdoy_analysis.py` (Handelstag des Jahres, dynamisch Aktien/Crypto)
- Trading Day Header → `trading_day_header.py` (TDOM/TDOY Anzeige auf allen Pages)
- Streak-Analyse → `streak_analysis.py` (W/L-Serien, wiederverwendbar fuer alle Pages)
- Drawdown-Analyse → `drawdown_analysis.py` (DD-Kurven, Heatmaps, Recovery, Rolling Vola)
- Drawdown-Heatmaps → `SE_DRAWDOWN_COLORSCALE` (Rot-Gradient, NICHT symmetrisch)
- Page-Layout: Rendite-Sektionen oben, Drawdown/Risiko unten (visuell getrennt)
- Live-Close → `append_today_if_missing()` in data.py (Yahoo-Fallback + Supabase-Write)
- SEO-Tools → `seo/tools/` (statisches HTML mit JS-Client, Nginx /tools/ Route)
- Secrets in `.streamlit/secrets.toml` (in `.gitignore`)
- Daten-Layer → `shared/data.py` (Supabase-First, Yahoo-Fallback, OHLC-Konsistenzcheck)
- OHLC-Adjustierung → `yahoo_downloader.py` adj_factor (Split+Dividend auf Open/High/Low)
- Overnight/Intraday → Residual-Ansatz: `overnight = total - intraday` (nie cross-day OHLC mischen)
- Heatmaps mit Jahreslabels → Leerzeichen-Padding `f" {y} "` + `categoryorder="array"`
- Nightly-Refresh → nur letzte 5 Tage (historische Daten bleiben unveraendert)
- HTML-Pages → `landing/pages/` mit modularem Framework (Nav/Footer JS-Include, app.css, charts.js)
- Frontend-Charts → ApexCharts (120KB CDN) statt Plotly.js (3MB), Theme in `charts.js`
- Pre-computed JSON → `landing/data/` fuer Default-Ticker, Generator in `scripts/`
- Component-Loader → JS fetch+inject fuer Nav/Footer (kein Copy-Paste)
- Docker JSON-Transfer → `docker cp` Container→Host (nginx liest vom Host-Volume)

## Design-Regeln (PFLICHT bei allen UI-Arbeiten)

| Regel | Details |
|-------|---------|
| `frontend-design` Skill nutzen | Fuer alle HTML/CSS Pages, Components, Layouts — Bold, distinctive Choices |
| `ui-ux-pro-max` Skill nutzen | Design System Generierung: Farben, Typography, Spacing, Accessibility |
| `21dev` fuer Component Inspiration | Moderne Component-Patterns als Referenz |
| Keine generische AI-Aesthetics | NIEMALS: Inter/Arial/Roboto, Purple-Gradients-on-White, Cookie-Cutter Layouts |
| Bold, distinctive Design Choices | Klare aesthetische Richtung, intentional, NICHT "safe" oder generisch |
| Performance-optimiert | Inline Critical CSS, font-display:swap, lazy-load, keine unnuetzen Requests |
| SVG Icons (Lucide) | Keine Emojis, keine Icon-Fonts — immer inline SVG |
| Distinctive Typography | Sora (Display) + DM Sans (Body) fuer Landing; Plus Jakarta Sans fuer App |
| Accessibility CRITICAL | Kontrast 4.5:1, focus-visible Rings, aria-labels, prefers-reduced-motion |
| Touch Targets ≥ 44px | Buttons, Links, interaktive Elemente — minimum 44x44px |
| Animation 150-300ms | transform/opacity only, ease-out enter, ease-in exit, staggered reveals |
| Dark Mode First | V3 Ultra Palette: bg #000, card #0a0a0e, accent #e8a820 (Signal Gold) |
| 21st.dev Magic MCP | Component Inspiration via `/ui` Prompt — generiert moderne UI-Patterns |
| Farbschema V3 Ultra | Pure Black + Signal Gold + Neon Red/Green. Maximaler Kontrast. |

## UI-Komponenten (Premium Dark Mode)

| Komponente | Modul | Verwendung |
|-----------|-------|------------|
| Signifikanz-Tachos | `significance_gauge.py` | t-Test + Radial Gauge pro Gruppe |
| Perzentil Stat-Ribbon | `percentile_bar.py` | Einzeilig: Wert, Ø, Delta, Micro-Gauge, %ile, σ |
| Kompakte Karten | Inline HTML | Flex-Row, 10px Label, 14px Wert, farbcodiert |
| Best Match | Inline HTML | DTW + Korrelation, Pokal-Icon beim besten Match |
| Premium Ampel | Inline HTML | Glow-Effekt, Badges statt massive Farbflächen |
| Trading Day Header | `trading_day_header.py` | Gelber Einzeiler: Datum · TDOM · TDOY |
| Trading Day Converter | `trading_day_header.py` | Datepicker + Inline-Ergebnis auf Home |
| Drawdown-Kurve | `drawdown_analysis.py` | Ø DD pro Tag, Fill nach unten, Gold aktuelles Jahr |
| Drawdown-Heatmap | `drawdown_analysis.py` | Monat × Dekade/Jahr, SE_DRAWDOWN_COLORSCALE |
| Worst-DD-Tabelle | `drawdown_analysis.py` | Top 25 Extremjahre mit Peak/Tief/Recovery |
| Rolling Volatilität | `drawdown_analysis.py` | Einstellbares Fenster (5-60d), Kohorten-Filter |

## Code Style

```
snake_case        → Variablen, Funktionen
UPPER_CASE        → Konstanten
# ── Abschnitt ──  → Section Headers
```

## Arbeitsprotokoll & Kontinuität

> GEHE DAVON AUS, DASS EINE UNTERBRECHUNG JEDERZEIT PASSIEREN KANN.

| Regel | Wann |
|-------|------|
| **Auto Memory aktualisieren** | Nach jeder größeren Änderung (neues Modul, Bug-Fix, Feature) |
| **CLAUDE.md TODOs pflegen** | Erledigte Punkte mit `[x]` + Datum markieren, neue hinzufügen |
| **Commit-Messages aussagekräftig** | Jeder Commit beschreibt WAS und WARUM (nicht nur Dateinamen) |
| **Nach Compaction: /memory prüfen** | Auto Memory kann veralten — kritische Infos aktualisieren |
| **Vor Deploy: Syntax-Check** | `py -c "import ast; ast.parse(open(f).read())"` für alle geänderten Dateien |
| **Vor Deploy: Funktionstest** | Mindestens 1 Import-Test + 1 Daten-Test pro neuem Modul |

### Was in Auto Memory gehört
- Aktuelle Architektur-Entscheidungen die nicht in CLAUDE.md stehen
- Bekannte Bugs / Workarounds die noch nicht gefixt sind
- User-Präferenzen (z.B. "immer Umlaute", "gelbe Farbe für Highlights")
- Letzte Session: Was wurde gemacht, was ist offen

### Was in CLAUDE.md gehört
- Projektstruktur, Module, Regeln (dauerhaft gültig)
- Erledigte + offene TODOs mit Datum
- Kritische Regeln (Import-Verbote, Styling, Architektur)

## HTML-Migration Plan (Landing Pages)

Streamlit → statisches HTML. 8 wiederverwendbare JS-Module.

### Fertige JS-Module (9 Module)

| Modul | Zeilen | Python-Quelle | Kern-Funktionen | Genutzt von |
|-------|--------|---------------|-----------------|-------------|
| `app.js` | 360 | — (original) | `initTickerInput`, `fetchAllPrices`, `renderTradingDayHeader`, `makeSortable` (Auto-Sort aller Tabellen via MutationObserver), Supabase REST | **Alle Pages** |
| `charts.js` | 166 | — (original) | `lineChart`, `barChart`, `heatmapChart`, `boxPlotChart`, Theme | **Alle Pages** |
| `decade-compute.js` | 495 | `calculations_decade.py` + `generate_decade_data.py` | `fromPrices`, `computeDrawdown`, `computePercentile`, `computeRollingVola` | Dekadenzyklus |
| `seasonal-compute.js` | 531 | `calculations.py` + `central_banks.py` | `buildYearData`, `calculateSeasonalAverage`, `analyzeTurnOfMonth`, `analyzeMoonEffect`, `getMoonDates`, `isSupermoon`, `buildMonthlyStats`, `buildTOMHeatmap`, `calcWindowOptimization`, `getPresidentialCycleYear` | Monatswechsel, Mondphasen, Kriegszeiten, *+4 Pages* |
| `streak-analysis.js` | 114 | `streak_analysis.py` | `computeStreaksFromList`, `currentStreak`, `renderStreakTable` | Monatswechsel, Mondphasen, *+2 Pages* |
| `significance.js` | 243 | `significance_gauge.py` | `runSignificanceTest` (t-Test, Cohen's d, Relevanz), `renderSection` (CSS Gauges), `scoreToColor` | Monatswechsel, Mondphasen, *+3 Pages* |
| `indicators.js` | 306 | `indicators.py` + `indicator_filter_ui.py` | `calcSMA/EMA/RSI/Bollinger/MACD/LBR`, `applyFilter`, `renderFilterUI`, `REGISTRY` | Monatswechsel, Mondphasen, *+3 Pages* |
| `outlier.js` | 123 | `outlier_manager.py` | `detectIQR`, `winsorize`, `filterCurves`, `renderFilterUI` | Monatswechsel, Mondphasen, *+3 Pages* |
| `strategy-compute.js` | 700 | `strategies/plain_vanilla.py` | 22 Strategie-Funktionen, `buildEquityCurve`, `computeStats`, `applyStopLoss`, `applyTrailingStop`, `STRATEGIES` Registry | Plain Vanilla, *Trifecta* |
| `holidays.js` | 240 | `exchange_holidays.py` + `nyse_holidays.py` | `easter`, `goodFriday`, `thanksgiving`, `get(year,exchange)`, `isTradingDay`, `nthTradingDay`, `lastTradingDay`, `nextTradingDay`, `detect(ticker)` | **Alle Pages** (NYSE/XETRA/LSE/NONE) |

### Fertige HTML-Pages
| Page | URL | Module genutzt | Inline-Funktionen |
|------|-----|---------------|-------------------|
| Dekadenzyklus | `/dekadenzyklus` | app, charts, decade-compute | — |
| Monatswechsel | `/monatswechsel` | app, charts, seasonal-compute, streak, significance, indicators, outlier | — |
| Mondphasen | `/mondphasen` | app, charts, seasonal-compute, streak, significance, indicators, outlier | — |
| Kriegszeiten | `/kriegszeiten` | app, charts, seasonal-compute | `computeEventWindow`, `smooth`, `toPairs`, Monatslabel-Formatter, Min-HT-Filter |
| Crash-Frühwarnung | `/crash-fruehwarnung` | app, charts | Regime-Scores aus Supabase (IF), JS-Fallback, Risk-Score Backtest-Chart |
| Plain Vanilla | `/plain-vanilla` | app, charts, indicators, holidays, strategy-compute, significance | Naechste Signale (24 Strategien), Signifikanztest, Trailing Stop, Profit Factor |
| Trifecta | `/trifecta` | app, charts, seasonal-compute | Ampel (SCR+FFD+JanB), Durchschnittsverlauf, DD-KPIs, Jahresrendite-Bar |
| Intermarket Shocks | `/intermarket-shocks` | app, charts | Trigger→Target Analyse, Scatter+Regression, Saisonaler Breakdown, T=0 |
| Sektor-Rotation | `/sektor-rotation` | app, charts | 23 US-ETFs, Heatmap, Top/Flop, Jahresverlauf, Win-Rate + Streak |
| Overnight vs. Intraday | `/overnight` | app, charts, significance, indicators | OHLC-Analyse, Signifikanz (6 Tachos), Indikator-Filter |
| Zentralbanken | `/zentralbanken` | app, charts, significance, indicators, streak | Fed/EZB/BoE/BoJ Event-Window, Streak, Termine aus Supabase |
| Feiertags-Effekt | `/feiertage` | app, charts, holidays, significance, streak | Exchange-aware (NYSE/XETRA/LSE), Ranking, Heatmap, Streak |
| TDOM Analyse | `/tdom-analyse` | app, charts, holidays, outlier, indicators, streak, strategy-compute | 3 Strategien (Intraday/Overnight/C2C), Vorwärts/Rückwärts, Heatmap Monat×TDoM, TDOM-Strategie Tester (Entry/Exit mit Cross-Month Support, Stop-Loss, CAGR/Sharpe/MaxDD/PF), TDoY Top 25 mit Datum 2026 (sortierbar), Streak pro TDoM, MIN_N=10 Warnung, "We are here" Marker |
| Spot-Vol Beta | `/spot-vol-beta` | app, charts, holidays | 3 Subplots (Spot + Daily Beta + Vol, synchronisiert), Scatter + OLS-Regression + "We are here", Rolling Beta mit Gesamt-Beta Referenz, Regime-Wendepunkte (VIX Spikes / Complacency / Beta Stress) mit Forward Returns 5/10/20/60d, historischer Spot-Chart |
| OPEX Analyse | `/opex` | app, charts, holidays, indicators, streak, strategy-compute, significance, outlier | **Modus-basiert** OPEX/VIX exklusiv. OPEX-Ansichten: Triple Witching (kumul. Linie + 4 Q-Monats-Checkboxen) / Monatlich (12 Mini-Charts + 12 Monats-Checkboxen). VIXpiration: 12 Mini-Charts Grid (Kalender-3.Fr−30d, CBOE-konform, Feiertags-Adjustierung) + 12 Monats-Checkboxen. Heatmap Monat×Offset, Streak (W/L-Kacheln) direkt unter Heatmap, Signifikanztest mode-aware (Alle+Monate in passender Spaltenzahl), Backtest via `SA.strategy.computeStats` (8 KPIs inkl. Profit Factor, dynamische Y-Achse, $1000 Compounding Equity-Kurve), Outlier-Filter (IQR/Winsorize auf cumReturn), Kalender mit hellen Badges (Standard/Triple Witching/VIX Settlement) |
| KI-Saisonalität | `/ki-saisonalitaet` | app, charts, seasonal-compute | **Musterpfad** (rekalibrierte Saisonalität via Top-N ähnlichster Jahre, gewichteter Ø) + **KI Composite Score 1–10** aus 4 Sub-Scores (Musterpfad-Qualität, Trend-Projektion, Win-Rate aktueller Monat, Tracking-Qualität). Hero-Bereich: Score + farbcodiertes Signal-Badge (Bullish≥6.5/Neutral/Bearish≤3.5) links, Radar-Chart mit 4 Sub-Scores rechts. Main-Chart: Klassischer Ø + Match-Jahre (togglebar) + Musterpfad + aktuelles Jahr + fette grüne Solid-Projektion ab "Heute". Sidebar: Ähnlichkeitsmethode (Korrelation/Euklid), Top-N (3-10), Glättung (1-21), Projektion (0-120d), Chart-Anzeige-Toggles. Match-Jahre-Tabelle mit Ähnlichkeits-Bar + Jahres-Rendite + Präsidentenzyklus-Badge. Info-Badges mit Hover-Tooltip für Score- und Radar-Erklärung. |
| Jahreszyklus | `/jahreszyklus` | app, charts, holidays, significance, outlier | **13 Sektionen** Port von `pages/02_Jahreszyklus.py` (1595 Zeilen). Hauptchart Saisonal-Ø + 25./75. Perzentil + ±1σ + Cycles + Aktuelles Jahr (Single-Y-Axis, KISS). **Einzeljahre + Gann Pressurechart** als separate Sub-Charts unten via `chart.group:'jzklus-sync'` (ApexCharts v4 Multi-Axis Workaround). Pressurechart: Σ-Lookback Ø-Kurven + aktueller Jahresverlauf (kumulierte Tagesrenditen %), gleiche Höhe wie Hauptchart. Perzentil-Bänder mit **Stable-Range-Trim** (≥80% Sample, Spike-frei). Rolling Vola **jahresgrenzen-übergreifend** (rollt über konkatenierte log_returns aller Jahre → korrekte Januar-Werte inkl. Vorjahres-Daten). Detrend-Indikator, Monats/Quartals-Performance + Tabellen + Signifikanz (Bar-Labels nur `%` außerhalb), Quartals-/Cycle-Tachos in 1 Reihe (Empty-State "Sorry, zu wenig Daten!" bei <4 Cycles), 10-Jahres Heatmap (last_actual_day-Filter NUR für current year), Drawdown-Verlauf + KPIs, Rolling-Volatilität + KPIs, Drawdown nach Zyklus. **Alle Helper modular im `window._SA_JZ` Modul** (computeDetrend, computeDayCounts, splitSolidWeak, detectAnomalyEnd, drawdownSeries, avgRollingVolatility, computePressureCurve, etc.) — Math/Render strikt getrennt. |
| Monatszyklus | `/monatszyklus` | app, charts, seasonal-compute, significance, outlier, holidays | **14 Sektionen** Port von `pages/03_Monatszyklus.py` (1412 Zeilen). Intra-Monat-Hauptchart (TDOM-Verlauf, TDOM 0 = 0% Vormonatsschluss-Basis, Solid/Weak Split bei n<10, Konfidenzband ±1σ, Perzentil-Bänder 25./75. optional, aktuelles Jahr in gold). **Einzeljahre als separates Sub-Chart** unter dem Hauptchart via `chart.group:'mz-sync'` (eigene Y-Achse, vermeidet Y-Skala-Verzerrung). Marker auf allen Linien-Charts `size:0` mit `hover:size:4-5` (saubere Linien, Punkte nur beim Hover). Detrend-Indikator (0-100, Midline 50). **Saisonal Match** (3 Tachos: Korrelation, DTW Shape, Abweichungstest mit numerischem Wert im Tacho + Label darunter). **Präsidentenzyklus Best-Match** (5 Tachos mit Medaillen). Wochen-Performance (5 Bars). Monats-Performance (12 Bars + Tabelle). Two-Week Performance (24 Bars sortiert). Two-Week Heatmap (12×2). Two-Week Aktuelles Jahr Overlay (Bar+Line, **Bars per `plotOptions.bar.colors.ranges` rot/grün** statt einheitlich). Best Two-Weeks Ranking (horizontal Top 24, helle/große Achsen-Labels). Momentum-Check (1st→2nd Wahrscheinlichkeiten). Two-Week Signifikanztest (2 Tachos, Label unter Tacho). 10-Jahres Monats-Heatmap. Sidebar: Ticker, Zeitraum 3-30/Max, Monat-Selektor, 4 Toggles (current/individual/bands/percentile), Cycle-Filter, Two-Week Slider, Outlier-Filter. **Alle Helper modular im `window._SA_MZ` Modul** — Math/Render strikt getrennt. |
| Wochentage | `/wochentage` | app, charts, seasonal-compute, significance, streak, indicators, holidays | **12 Sektionen** Port von `pages/04_Wochentage.py` (1670 Zeilen). 4 Rendite-Modi (cc/co/oc/oc1) **mode-aware** auf Wochenverlauf+Bars+Heatmap. Sidebar: Ticker, Zeitraum 1-30, Modus-Radio, **Multi-Select 12 Monats-Checkboxen** (Alle/Keine), Cycle-Filter, Aktuelle Woche Toggle, Technische Filter (`SA.indicators.renderFilterUI`). Sektion-Reihenfolge: 1. Kumulierter Wochenverlauf Mo→Fr (mode-aware, +aktuelle Woche overlay), 2. Ø Rendite + Win-Rate Bars, 3. Signifikanztest (5 Wochentage + **6. "Gesamt" Tacho** für Drift-Check), 4. Statistik-Tabelle, 5. **Streak-Analyse**, 6. Overnight vs Intraday (NUR Aktien), 7. Konsekutiv-Analyse (P(Folgetag↑) Heatmap), 8. Quartals-Heatmaps Q1-Q4 × Mo-Fr, 9. Monat × Wochentag Heatmap (`reversed:true` Jan oben), 10. Top/Flop Top 10 Kombinationen, 11. **Weekend-Effekt** ganz unten (NUR Aktien, 5 KPI-Cards mit Gold-Border + Hover, Bar pro Monat, Sig pro Monat, Heatmap Monat×Jahr mit kontinuierlichem Year-Range, Cycle-Bars **alle 4 Cycles** auch bei n=0), 12. Methodik. Math-Helper im `window._SA_WD` Modul. **OHLC fetch** via `fetchOHLC` (`select=date,open,close`). Crypto-Detection automatisch. Volatilitäts-Profil weggelassen (kein high/low). Monats-Filter wirkt auf 8 Sektionen — NICHT auf Weekend/Heatmap/Top-Flop. |
| Backtest Engine | `/backtest-engine` | app, charts, holidays, seasonal-compute, significance, outlier, indicators, fomc-dates | **4 Tabs** Port von `pages/12_Backtest_Engine.py` + `shared/backtest_engine.py` (~1278 Zeilen Python). **Tab 1 Einzelner Backtest**: days_before/after Slider, **7 KPI-Cards** (Total Return, Sharpe, Calmar, Profit Factor, Win-Rate, Max DD, Trades) mit Standard `.kpi` Klasse, Equity-Kurve (type:'area' + gradient), Trade-Tabelle. **Tab 2 Parameter-Optimierung**: Range-Min↔Max Inputs (gold-Border), Objective-Dropdown (5 Optionen inkl. **Profit Factor**), Grid-Search, Heatmap days_before×days_after, Top 10 Tabelle. **Tab 3 Walk-Forward**: Folds + In-Sample-Ratio + Objective, Expanding Window mit Grid-Search auf In-Sample und OOS-Test, OOS-Aggregat KPIs + Fold-Details. **Tab 4 Event-Relevanz (KI)**: t-Test + Cohen's d + Win-Rate → Relevance-Score, Tabelle + Tachos pro Event mit Top-Event Banner. Sidebar: Ticker, Zeitraum 5-50, Event-Typ (6 Optionen), Entry/Exit Radio (Close/Open), Stop-Loss Block (Toggle + % + fixed/trailing), Outlier-Filter, **Technische Filter** (look-ahead-bias-frei: filterMask wird auf entryIdx-1 geprüft). Tab-Navigation als Custom UI mit Gold-Akzent. Math-Helper im `window._SA_BT` Modul: runBacktest, computeStats, applyStopLoss (close-basiert approximiert), optimizeParameters, walkForward, scoreEventRelevance, detectOutlierYears. **Eigene t-Distribution Implementation** (Regularized Incomplete Beta) ohne scipy. Event-Generators: makeHolidayEvents (10 NYSE-Holidays via SA.holidays), makeFomcEvents (224 Daten 2000-2026 in `landing/js/fomc-dates.js`), makeOpexEvents (3. Freitag via _nthDow), makeMoonEvents (SA.seasonal.getMoonDates). Stop-Loss approximiert close-basiert (kein high/low in DB). Auto-Run beim Ticker-Wechsel. |

### HTML-Migration komplett (19 von 18) ✓ — Backtest Engine als Bonus

Streamlit-App `/app/` ist Legacy. Bug-Reports IMMER auf landing/pages/*.html.

### Landing-Struktur (Stand 07.04.2026)
**Nav (4 Dropdowns):**
- **Zyklen**: Dekadenzyklus, Jahreszyklus, Monatszyklus, Wochentage, Monatswechsel, Mondphasen
- **Events**: Notenbanken (Zentralbanken), OPEX, Feiertage, Shock-Analyser (Intermarket Shocks)
- **Strategien**: Januar Trifecta, Plain Vanilla, Backtest Engine
- **Mehr**: Kriegszeiten, Crash-Frühwarnung, Sektor-Rotation, Overnight, TDoM, Spot-Vol, KI-Saisonalität

**Footer (5 Spalten + Brand):** Brand · Zyklen · Events · Strategien · Mehr · Rechtliches
- CSS: `foot__grid: 1.4fr repeat(5, 1fr)` + `@1100px` Breakpoint (3 Spalten) damit es auf Tablets nicht zerbricht

**Alle `/app/` Links entfernt:** "Zur Analyse" CTAs zeigen jetzt auf `/jahreszyklus`, "Jahres-Indikatoren" Card auf `/backtest-engine`, "Methodik" komplett entfernt (jede HTML-Page hat eigene Methodik-Section). Streamlit ist nur noch direkt via URL erreichbar.

## Tägliche Prüfungen (bei Session-Start)

| Was | SQL / Befehl | Erwartung |
|-----|-------------|-----------|
| **Nightly Refresh** | `SELECT run_date, duration_seconds, tickers_success, tickers_missing, errors FROM refresh_log ORDER BY run_date DESC LIMIT 3;` | Letzter Run = gestern/heute, errors = `[]` |
| **Regime-Scores** | `SELECT date, risk_score, traffic_light FROM regime_scores WHERE ticker='SPY' ORDER BY date DESC LIMIT 3;` | Letztes Datum = letzter Handelstag, Score 0–100 |
| **Preise aktuell** | `SELECT ticker, max(date) as last_date FROM prices WHERE ticker IN ('SPY','^DJI','AAPL') GROUP BY ticker;` | Alle 3 = gestern/heute |
| **Crash-Frühwarnung** | https://seasonalpha.ai/crash-fruehwarnung | Keine Stale-Warning, Ampel + Chart konsistent |

Bei Fehlern:
- `ssh root@178.104.75.46` → `docker logs seasonalpha-app --tail 50`
- Manueller Refresh: `docker exec -it seasonalpha-app python3 scripts/nightly_refresh.py`
- Regime-Scores: `docker exec -it seasonalpha-app python3 scripts/compute_regime_scores.py --full`

## Docs (bei Bedarf lesen)

- `docs/ARCHITECTURE.md` — Datenfluss, Supabase-Schema, Module, Deployment, Blog
- `docs/CHARTS.md` — Plotly Theme, Split-Slider, Distribution Charts
- `docs/AI_MODELS.md` — Technische KI-Dokumentation (Code + API)
- `docs/KI_FEATURES.md` — Alle 15 KI-Features mit Beschreibung (fuer Home Page)
- `docs/SEO_ENGINE.md` — Programmatic SEO + Blog Engine
- `docs/BLOG_WORKFLOW.md` — Blog + Social Media + YouTube Workflow-Anleitung
- `docs/REFRESH_MONITORING.md` — Kurs-Ueberwachung, Health-Check, Troubleshooting
- `docs/MIGRATION.md` — Next.js + FastAPI + Highcharts Migrationspfad
- `.claude/blog-tutorial.md` — Skill: SEO-Blog-Artikel schreiben (DE, SeasonAlpha-Kontext)

# CLAUDE.md — SeasonAlpha

> Version 27.0 | 2026-04-04 | Details → `docs/`


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
| `app.js` | 249 | — (original) | `initTickerInput`, `fetchAllPrices`, `renderTradingDayHeader`, Supabase REST | **Alle Pages** |
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

### Offene HTML-Migrationen
| # | Page | Zeilen | Charts | Status |
|---|------|--------|--------|--------|
| 8 | Disabled Pages (Shock✅, Rest offen) | 300-500 | 6-8 | naechste |
| 12 | Jahreszyklus | 1595 | 20 | |
| 13 | Monatszyklus | 1412 | 26 | |
| 14 | Wochentage | 1670 | 29 | |

## Offene TODOs

- [ ] Premium Dashboard: TDOY Sektion freischalten
- [ ] AI Chat Page (Kunde fragt: "Was geht morgen bei TSLA?")
- [ ] Split-Slider: Ticker-Auswahl (aktuell nur ^DJI)
- [ ] Outlier Manager in alle Pages integrieren
- [ ] KI-Zusammenfassung in weitere Pages integrieren
- [ ] Stripe Freemium/Abo-Integration
- [ ] Supabase User-Auth
- [ ] Anthropic API-Key einrichten (KI-Zusammenfassung)
- [ ] SEO Landingpages: Echte Berechnungen + Charts statt Platzhalter
- [ ] Blog: Claude API Integration + OG-Image + YouTube Thumbnails
- [ ] Saisonalitaets-Stabilitaet (Rolling 10J-Fenster)
- [ ] Bull/Bear Regime-Split (VIX >25 vs <25)
- [ ] Landing Page: OG-Image + Inter Font self-hosted
- [ ] Wochentage Heatmap: Modus-Wechsel Bug
- [ ] Weekend-Effekt + TOM Heatmap: Rendering-Bug
- [ ] Tickers-Tabelle in Supabase (holiday_cal, exchange, kategorie)

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

# CLAUDE.md — SeasonAlpha

> Version 21.0 | 2026-03-31 | Details → `docs/`

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
  yahoo_downloader.py    ← HTTP-Downloader + Stooq-Fallback + OHLC Split-Adjustierung (einziger Cache!)
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
  nightly_refresh.py     ← Nightly DB Refresh (Calendar + Ticker-Daten)
  intraday_refresh.py    ← Intraday Kurs-Updates (EU/US/Asien/FX/Crypto, alle 30 Min)
  create_market_tables.sql ← SQL-Schema für Cache-Tabellen
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
- Drawdown-Analyse → `drawdown_analysis.py` (DD-Kurven, Heatmaps, Recovery, Rolling Vola)
- Drawdown-Heatmaps → `SE_DRAWDOWN_COLORSCALE` (Rot-Gradient, NICHT symmetrisch)
- Page-Layout: Rendite-Sektionen oben, Drawdown/Risiko unten (visuell getrennt)
- SEO-Tools → `seo/tools/` (statisches HTML mit JS-Client, Nginx /tools/ Route)
- Secrets in `.streamlit/secrets.toml` (in `.gitignore`)

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

## Offene TODOs

- [ ] **PRIO 1: Pages auf Supabase-Daten umstellen (statt Yahoo-Live-Fetch)**
      Alle 6 Analysis-Pages (01-06) laden Kursdaten live von Yahoo Finance.
      Die Supabase `prices`-Tabelle wird vom Nightly-Job befuellt, aber nie gelesen.
      Refactoring: `shared/data.py` → erst `fetch_prices()` aus Supabase, Fallback Yahoo.
      Betrifft: Dekadenzyklus, Jahreszyklus, Monatszyklus, Wochentage, Monatswechsel, Mondphasen.
      Vorteil: Schnellere Ladezeit, weniger Yahoo-Rate-Limits, Stooq-Daten (DJI 130J) sofort verfuegbar.
- [ ] `shared/download_manager.py` fertigstellen
- [x] Premium Dashboard: TDOM freigeschaltet (2026-03-19)
- [ ] Premium Dashboard: TDOY Sektion freischalten
- [ ] AI Chat Page (Kunde fragt: "Was geht morgen bei TSLA?")
- [ ] Split-Slider: Ticker-Auswahl (aktuell nur ^DJI)
- [x] Outlier Manager (IQR, Winsorize, Isolation Forest) (2026-03-19)
- [x] Market Calendar DB + Computed Values Cache (2026-03-19)
- [x] KI-Zusammenfassung pro Page (Claude API) (2026-03-19)
- [x] Anomalie-Heatmap (Isolation Forest Monat x Dekade) (2026-03-19)
- [x] Anomaly Engine: Radar, Crash-Ampel, TDoM-Anomalien, Muster-Brueche (2026-03-19)
- [x] MSTL Saisonalitaets-Zerlegung (statsmodels) (2026-03-20)
- [x] Chronos-Bolt-Tiny Forecast (Amazon) (2026-03-20)
- [x] NeuralProphet Saisonalitaet (2026-03-20)
- [x] Spot-Vol Beta Page + DB-Tabelle + Regime-Wendepunkte (2026-03-20)
- [x] Stooq-Fallback in yahoo_downloader (DJI 131 Jahre) (2026-03-20)
- [x] OHLC Split-Adjustierung (Open/High/Low) (2026-03-20)
- [x] Trifecta numpy.bool Fix + Ampelverlauf-Charts (2026-03-20)
- [x] Yearly Seasonality Page (Jahreszyklus) (2026-03-21)
- [x] Kriegszeiten Page (Krieg vs. Frieden) (2026-03-21)
- [x] Crash-Fruehwarnung eigene Page (2026-03-21)
- [x] Saisonal-Events Kalender Page (2026-03-21)
- [x] Home Page Redesign: SeasonalAlpha, Glasmorphismus, SVG Hero (2026-03-21)
- [x] Split-Slider: Achsen-Fix, Monatslabels, Start=links (2026-03-21)
- [x] Page-Umbenennung: Deutsch, keine Nummern sichtbar (2026-03-21)
- [x] Domain: SeasonalAlpha.ai (gesichert 2026-03-20)
- [x] Nightly Refresh Job (GitHub Actions) (2026-03-19)
- [x] Jahreszyklus Rewrite: Pressure Chart, Detrend, Anomalie-Radar, Praesidentenzyklus, Outlier, Heatmap (2026-03-21)
- [x] Home: 3x3 Kacheln, klickbar, Stat-Kacheln Update, Tooltip "seit 1896" (2026-03-21)
- [x] Disabled Pages aktiviert (Dekadenzyklus, Trifecta, Kriegszeiten, Events) (2026-03-21)
- [x] Uebernacht-Strategien + Crash-Fruehwarnung nach _disabled verschoben (2026-03-21)
- [x] Monatszyklus Rewrite: Detrend-Expander, TDOM-Marker, 10J-Heatmap, Kontrastfarben (2026-03-25)
- [ ] Outlier Manager in alle Pages integrieren (aktuell: Jahreszyklus + Erweiterte Analyse)
- [ ] KI-Zusammenfassung in weitere Pages integrieren
- [ ] Anomaly Engine in weitere Pages integrieren
- [x] Ticker-Datenbank erweitert: 53 → 94 Ticker (EU-Aktien, Anleihen, EM, Sektor-ETFs) (2026-03-22)
- [x] Ticker-Datenbank erweitert: 94 → 163 Ticker (69 neue EU-Aktien Top 75 Marktkapitalisierung) (2026-04-01)
- [x] Ticker-Datenbank erweitert: 163 → 263 Ticker (100 neue US-Aktien Top S&P 500) (2026-04-01)
- [x] Bulk-Download EU + US: Alle 169 neue Ticker in Supabase geladen (2026-04-01)
- [x] Backtest Engine + Optimierer (Grid-Search, Walk-Forward, KI Event-Relevanz) (2026-03-21)
- [x] Stooq-Fallback erweitert: 5 → 10 Indizes (CAC, Euro Stoxx, SMI, HSI, KOSPI) (2026-03-22)
- [x] VPS Deployment: Hetzner CPX22, Docker + Nginx + SSL (2026-03-22)
- [x] Auto-Deploy: GitHub Action → SSH-Key → git pull + docker rebuild (2026-03-22)
- [x] App live unter http://178.104.75.46 (2026-03-22)
- [x] DNS: seasonalpha.ai → 178.104.75.46 (STRATO A-Record + CNAME www) (2026-03-25)
- [x] SSL (HTTPS) eingerichtet: Let's Encrypt + Certbot (2026-03-25)
- [x] SEO Engine: 94 Landingpages aus SYMBOLS, Sitemap, robots.txt, Disclaimer (2026-03-25)
- [x] SEO Nginx-Deployment: /analyse/, /disclaimer, /sitemap.xml Routen (2026-03-25)
- [x] Google Search Console: Verifizierung (DNS-TXT + Meta-Tag), Sitemap eingereicht (2026-03-25)
- [x] Achsenbeschriftungen global weiss, max 2 Nachkommastellen (2026-03-21)
- [x] "We are here!" Helper zentral ausgelagert (shared/we_are_here.py) (2026-03-21)
- [x] "X" → "x" bei Dekaden-Endziffern global (2026-03-21)
- [ ] Streamlit Cloud Deployment
- [ ] Stripe Freemium/Abo-Integration
- [ ] Supabase User-Auth
- [ ] Anthropic API-Key einrichten (KI-Zusammenfassung)
- [x] CPI-Inflationsbereinigung: Kriegszeiten Page + shared/cpi_data.py + DB-Tabelle (2026-03-25)
- [x] Wochentage Rewrite: Heatmap-Design, Praesidentenzyklus, gelber Rahmen, Outlier entfernt (2026-03-25)
- [x] Backtest Engine: Tab-Styling, Radial Fill Gauge (Gradient), KI-Erklaertext (2026-03-25)
- [x] Signifikanztest-Modul: shared/significance_gauge.py (t-Test + Gauge) (2026-03-25)
- [x] Signifikanztest integriert: Wochentage, Monatswechsel, Mondphasen (optionaler Expander) (2026-03-25)
- [x] Wochentage: Alle-Modi-Signifikanz (4 Rendite-Modi × 5 Tage als Tachos) (2026-03-26)
- [x] Wochentage: Kumulierter Wochenverlauf als oberster Expander (2026-03-26)
- [x] Wochentage: Balkendiagramm in Expander verschoben (2026-03-26)
- [x] Wochentage: Heatmap Colorbar weisse Schrift + 2 Nachkommastellen (2026-03-26)
- [x] Wochentage: DuplicateElementId Fix (key_prefix in significance_gauge) (2026-03-26)
- [x] Monatswechsel: TOM Heatmap Fix (apply_se_heatmap_theme, tickformat=None) (2026-03-26)
- [x] Trifecta: Aktuelles-Jahr-Overlay (goldene Linie, nur bis heute) (2026-03-26)
- [x] Trifecta: Premium Redesign (Glow-Ampel, Badges, kompakte Karten) (2026-03-26)
- [x] Footer: Impressum + Datenschutz als Expander (vollständige Rechtstexte) (2026-03-26)
- [x] Footer: Risk Disclosure DE + EN (2026-03-26)
- [x] Perzentil Stat-Ribbon: shared/percentile_bar.py (Micro-Gauge, %ile, Z-Score) (2026-03-26)
- [x] Perzentil-Bar integriert: Jahreszyklus, Monatszyklus, Dekadenzyklus, Trifecta (2026-03-26)
- [x] Dekadenzyklus: Premium Redesign mit Expandern + kompakten HTML-Karten (2026-03-26)
- [x] Jahreszyklus: Monats-Signifikanz (12 Tachos) + Quartals-Signifikanz (2026-03-26)
- [x] Jahreszyklus: Praesidentenzyklus-Signifikanz (4 Tachos) (2026-03-26)
- [x] Jahreszyklus: Praesidentenzyklus Best Match (DTW + Korrelation, 5 Karten) (2026-03-26)
- [x] Jahreszyklus: Perzentil-Baender (25./75. Perzentil) im Hauptchart (2026-03-26)
- [x] Mondphasen: Supermond-Effekt in Sidebar + Berechnung (2026-03-26)
- [x] Mondphasen: Mond-Heatmap (Monat × Phase) (2026-03-26)
- [x] Mondphasen: Expander-Reorganisation (Signifikanz Default ON) (2026-03-26)
- [x] Monatswechsel: Perzentil-Statusbar + TOM Stats als kompakte Karten (2026-03-26)
- [x] Monatswechsel: Signifikanz-Reihenfolge Fix (Jan→Feb bis Dez→Jan) (2026-03-26)
- [x] Ticker-Autocomplete: Search-as-you-type mit Supabase (shared/ticker_autocomplete.py) (2026-03-26)
- [x] Ticker-Persistenz: Gewaehlter Ticker bleibt bei Page-Wechsel erhalten (session_state) (2026-03-26)
- [x] Indikator-Filter: shared/indicators.py + indicator_filter_ui.py (6 Indikatoren, 5 Pages) (2026-03-27)
- [x] LBR Oscillator (Linda Bradford Raschke) als Indikator-Filter (2026-03-27)
- [x] Blog Engine: Markdown → HTML + Charts + Social + YouTube (2026-03-27)
- [x] Blog: 3 Beispiel-Posts (Education, Marktausblick, Tutorial) (2026-03-27)
- [x] Blog: KI-Prompt-Templates (6 Templates fuer Content + Social + YouTube) (2026-03-27)
- [x] Blog: Nginx /blog/ Route + Deploy-Action + Sitemap (2026-03-27)
- [x] Blog-Links: Footer (alle Pages) + Home Page Blog-Kacheln (2026-03-27)
- [x] Docs: ARCHITECTURE.md komplett ueberarbeitet (2026-03-27)
- [x] Fix: 10-Jahres Heatmap Monatszyklus (Jahreszyklus-Variante: text/texttemplate + dtick=1) (2026-03-28)
- [x] Blog: Skill blog-tutorial.md SEO-optimiert + ins Repo committed (.claude/) (2026-03-28)
- [x] Blog: Tutorial Wochentag-Signifikanztest Siemens + Screenshot-Support (posts/images/) (2026-03-28)
- [x] Blog: Tutorial Overnight vs. Intraday Split (Google) (2026-03-28)
- [x] Blog: Tutorial Box-Plot Dekadenzyklus (Dow Jones) (2026-03-28)
- [x] i18n: shared/i18n.py Grundgeruest (t(), get_lang(), lang_toggle(), TRANSLATIONS dict DE/EN) (2026-03-28)
- [x] i18n: Flaggen-Toggle via JS window.parent.document.body (SVG-Flags, position:fixed) (2026-03-28)
- [x] i18n: Home Page vollstaendig uebersetzt (Kacheln, Slider, Stats, Newsletter, Blog) (2026-03-28)
- [x] Footer: Legal Notice EN (§5 DDG auf Englisch) + Financial Disclaimer (2026-03-28)
- [x] Info-Badge: shared/info_badge.py + info_texts.yaml (~40 Einträge DE/EN) (2026-03-30)
- [x] Info-Badge: MutationObserver-Strategie (physisch in <summary> verschoben, 49 Badges, 11 Pages) (2026-03-30)
- [x] Detrend-Indikator: Skalierung 0–100 (Midline 50), grün/rot Fill, korrigierte Beschreibung (2026-03-30)
- [x] Info-Badge ENTFERNT: eigene "10_Methodik" Page ersetzt 68 verteilte Badges (2026-03-31)
- [x] Home: Market Regime Ampel entfernt, Methodik-Kachel hinzugefügt, Grid 3×4 (2026-03-31)
- [x] Split-Slider: Startposition 0 (zeigt Einzeljahre + goldenes aktuelles Jahr) (2026-03-31)
- [x] Monatswechsel: DuplicateElementId Fix (key_prefix="tom_sig") (2026-03-31)
- [x] Nightly Refresh: Supabase Heartbeat gegen Free-Tier Pausing (2026-03-31)
- [x] Blog: Monatswechsel DAX März → April (Marktausblick, Screenshot) (2026-03-31)
- [ ] SEO Landingpages: Platzhalter-Statistiken durch echte Berechnungen ersetzen (Supabase)
- [ ] SEO Landingpages: Statische Saisonalitaets-Charts generieren (Plotly write_image)
- [ ] Blog: Claude API Integration fuer automatische Content-Generierung
- [ ] Blog: OG-Image Generierung (Plotly write_image, 1200x630)
- [ ] Blog: YouTube Thumbnail Generierung (1280x720)
- [ ] Saisonalitaets-Stabilitaet (Rolling 10J-Fenster: Pattern-Veraenderung ueber Jahrzehnte)
- [x] Drawdown-Saisonalitaet (Wann starten/enden groesste Drawdowns im Jahr?) (2026-04-01)
- [ ] Bull/Bear Regime-Split (Saisonalitaet getrennt fuer VIX >25 vs <25)
- [x] TDOY-Modul: shared/tdoy_analysis.py (9 Funktionen, dynamisch Aktien/Crypto) (2026-04-01)
- [x] TDOY in preprocess(): tdoy-Spalte in jedem DataFrame (2026-04-01)
- [x] tdoy_stats DB-Tabelle + Supabase-Funktionen + Nightly-Refresh (2026-04-01)
- [x] Trading Day Header: "Heute: DD.MM.YYYY · TDOM X · TDOY Y" auf 6 Pages (2026-04-01)
- [x] Trading Day Converter: Datepicker auf Home-Page (kompakter Einzeiler, gelb) (2026-04-01)
- [x] SEO-Landingpage: /tools/trading-day-converter (JS-Client, Schema.org, FAQ) (2026-04-01)
- [x] Nginx /tools/ Route + Docker-Volume + Sitemap-Eintrag (2026-04-01)
- [x] Newsletter-Fix: Supabase-Insert auch bei Brevo-Fehler (2026-04-01)
- [x] Stooq-Fix: Session-Cookie fuer DJI 130 Jahre (2026-04-01)
- [x] Drawdown-Modul: shared/drawdown_analysis.py (DD-Serie, Avg-Kurve, KPI, Heatmap, Vola) (2026-04-01)
- [x] Drawdown + Vola in Dekadenzyklus: 3 Expander + Worst-DD-Tabelle + Methodik (2026-04-01)
- [x] Drawdown + Vola in Jahreszyklus: 3 Expander + Perzentil-Bar + Aktuelles-Jahr (2026-04-01)
- [x] Dekadenzyklus Layout: Rendite/Drawdown getrennt, Anomalie-Radar nach oben (2026-04-01)
- [x] Recovery-Berechnung: Echte Handelstage bis Peak-Preis ueberschritten (auch ueber Jahresende) (2026-04-01)
- [x] Dekadenzyklus Methodik: Ausfuehrliche Erklaerungen Rendite + Drawdown + Vola + Anomalie (2026-04-01)
- [x] Supabase-First Daten-Layer: shared/data.py liest erst Supabase, Fallback Yahoo (2026-04-01)
- [x] Nightly Refresh: Schreibt letzte 60 Tage Preise in Supabase (2026-04-01)
- [x] Jahreszyklus: DD nach Praesidentenzyklus (Chart + 4 Karten: Avg/Best/Worst) (2026-04-01)
- [x] Jahreszyklus: DD-Fix base=100→0 (full_365 startet bei 100) (2026-04-01)
- [x] Jahreszyklus: Layout Rendite/Risiko getrennt (wie Dekadenzyklus) (2026-04-01)
- [x] Jahreszyklus: DD-Heatmap entfernt (Rendite-Heatmap reicht) (2026-04-01)
- [x] Blog: Drawdown Crashjahre + Recovery (Education) (2026-04-01)
- [x] Blog: Rendite vs Drawdown erklaert (Education, mit Screenshots) (2026-04-01)
- [x] Blog: Midterm-Drawdown 2026 Marktausblick (Praesidentenzyklus) (2026-04-01)
- [x] Blog-Template: Tabellen-Styling (Dark Mode, Linien, Hover) (2026-04-01)
- [x] Blog-Builder: Markdown-Tabellen → HTML Converter (2026-04-01)
- [x] Jahreszyklus: Methodik-Expander (Rendite + Drawdown + Vola) (2026-04-01)
- [x] Wochentage: Crypto-Support 7 Tage (Mo-So, Overnight ausgeblendet, Konsekutiv 7 Paare) (2026-04-01)
- [x] Wochentage: Sidebar "Aktuellen Chart anzeigen" (gelber Rahmen immer, Overlay togglebar) (2026-04-01)
- [x] Wochentage + Monatszyklus: Dual Y-Achse (Ø links, aktuell rechts) (2026-04-01)
- [x] Monatszyklus: Goldener Stern bei TDOM 1 (erster Tag im Monat) (2026-04-01)
- [x] Intraday-Refresh: Schreibt Preise in Supabase (vorher nur Cache) (2026-04-01)
- [x] Supabase fetch_prices: Paginierung (1000-Row-Limit gefixt) (2026-04-01)
- [x] Nightly Jobs: 22:00→22:30 MESZ (amtliche Schlusskurse) (2026-04-01)
- [x] Ticker-Datenbank erweitert: 163 → 263 Ticker (100 neue US-Aktien Top S&P 500) (2026-04-01)
- [x] Bulk-Download EU + US: Alle 169 neue Ticker in Supabase geladen (2026-04-01)
- [x] SEO-Landingpages: 94 → 263 Pages neu generiert + Sitemap aktualisiert (2026-04-01)
- [x] Plain Vanilla Strategien: 24 saisonale Trading-Strategien in 6 Tab-Kategorien (2026-04-01)
- [x] Strategien-Backend: shared/strategies/plain_vanilla.py (24 Funktionen + Registry + Helpers) (2026-04-01)
- [x] Strategien-Frontend: pages/09_Plain_Vanilla_Strategien.py (Tabs, Kacheln, Equity, Trades) (2026-04-01)
- [x] Strategien Lazy Loading: Nur ausgewaehlte Strategie berechnen (Performance-Fix) (2026-04-01)
- [x] Wochentage: Heatmap 3 Nachkommastellen (2026-04-01)
- [x] Monatszyklus: Goldener Stern bei TDOM 1 (2026-04-01)
- [x] Nightly Jobs: 22:00→22:30 MESZ fuer amtliche Schlusskurse (2026-04-01)
- [x] Intraday-Refresh: Schreibt Preise in Supabase (2026-04-01)
- [x] Supabase fetch_prices: Paginierung 1000-Row-Limit gefixt (2026-04-01)

## Docs (bei Bedarf lesen)

- `docs/ARCHITECTURE.md` — Datenfluss, Supabase-Schema, Module, Deployment, Blog
- `docs/CHARTS.md` — Plotly Theme, Split-Slider, Distribution Charts
- `docs/AI_MODELS.md` — Technische KI-Dokumentation (Code + API)
- `docs/KI_FEATURES.md` — Alle 15 KI-Features mit Beschreibung (fuer Home Page)
- `docs/SEO_ENGINE.md` — Programmatic SEO + Blog Engine
- `docs/BLOG_WORKFLOW.md` — Blog + Social Media + YouTube Workflow-Anleitung
- `docs/MIGRATION.md` — Next.js + FastAPI + Highcharts Migrationspfad
- `.claude/blog-tutorial.md` — Skill: SEO-Blog-Artikel schreiben (DE, SeasonAlpha-Kontext)

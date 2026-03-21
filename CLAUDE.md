# CLAUDE.md — SeasonalEdge

> Version 13.0 | 2026-03-21 | Details → `docs/`

## Projekt

**SeasonalEdge** — Web-Plattform für saisonale Finanzmarkt-Analyse (ETFs, Aktien, Futures, Crypto).
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
  shock_analysis.py      ← Shock Analyzer (Trigger→Target)
  sector_rotation.py     ← Sektor-Rotation Analyse
  strategies/            ← 65+ Strategien
scripts/                 ← Batch-Jobs
  nightly_refresh.py     ← Nightly DB Refresh (Calendar + Ticker-Daten)
  create_market_tables.sql ← SQL-Schema für Cache-Tabellen
pages/                   ← Light Live + Premium Pages
  Light Live (aktiv, 9 Pages):
    00_Home              ← Startseite (Hero, 3x3 Kacheln, Slider, Stats, Newsletter)
    01_Dekadenzyklus     ← 131 Jahre DJI, Dekaden-Kohorten + KI (disabled)
    02_Jahreszyklus      ← Saisonaler Jahresverlauf, Pressure Chart, Detrend,
                            Anomalie-Radar, Praesidentenzyklus, Outlier Manager,
                            Monats-/Quartals-Perf, 10J-Heatmap, We-are-here Marker
    03_Monatszyklus      ← Monats-Heatmap, Boxplots + Outlier
    04_Wochentage        ← Wochentag-Renditen + Outlier
    05_Monatswechsel     ← Turn of the Month + Outlier
    06_Mondphasen        ← Voll-/Neumond-Effekt + Outlier
    07_Januar_Trifecta   ← Ampelsystem + Verlauf je Signal + Drawdown (disabled)
    08_Kriegszeiten      ← Krieg vs. Frieden Saisonalitaet (disabled)
    11_Saisonal_Events_Kalender ← Fed/EZB/OPEX/Mond/Feiertage 12 Monate (disabled)
  Disabled (pages/_disabled/):
    09_Crash_Fruehwarnung← KI-Ampel: Isolation Forest Regime-Erkennung
    91_Uebernacht_Strategien ← Overnight vs Intraday
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
| Inline `update_layout` VERBOTEN | Nur `apply_se_theme()` + chart-spezifische Overrides |

## Architektur-Prinzipien

- Berechnungen → `shared/`, UI → `pages/`
- Kein Copy-Paste von Logik zwischen Pages
- Wiederverwendbare Charts → `distribution_charts.py`
- Chart-Styling NUR via `apply_se_theme()` — keine inline Layouts
- Secrets in `.streamlit/secrets.toml` (in `.gitignore`)

## Code Style

```
snake_case        → Variablen, Funktionen
UPPER_CASE        → Konstanten
# ── Abschnitt ──  → Section Headers
```

## Offene TODOs

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
- [ ] Outlier Manager in alle Pages integrieren (aktuell: Jahreszyklus + Erweiterte Analyse)
- [ ] KI-Zusammenfassung in weitere Pages integrieren
- [ ] Anomaly Engine in weitere Pages integrieren
- [ ] Fehlende 42 Ticker nachladen (ETFs, Aktien, Krypto)
- [ ] Streamlit Cloud Deployment
- [ ] Stripe Freemium/Abo-Integration
- [ ] Supabase User-Auth
- [ ] Anthropic API-Key einrichten (KI-Zusammenfassung)

## Docs (bei Bedarf lesen)

- `docs/ARCHITECTURE.md` — Datenfluss, Supabase-Schema, Download-Manager, Logger, Cache
- `docs/CHARTS.md` — Plotly Theme, Split-Slider, Distribution Charts
- `docs/AI_MODELS.md` — Technische KI-Dokumentation (Code + API)
- `docs/KI_FEATURES.md` — Alle 15 KI-Features mit Beschreibung (fuer Home Page)
- `docs/SEO_ENGINE.md` — Programmatic SEO: Template, Builder, Deployment
- `docs/MIGRATION.md` — Next.js + FastAPI + Highcharts Migrationspfad

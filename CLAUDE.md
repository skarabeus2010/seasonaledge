# CLAUDE.md — SeasonalEdge

> Version 10.0 | 2026-03-19 | Details → `docs/`

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
  yahoo_downloader.py    ← HTTP-Downloader + Stooq-Fallback (einziger Cache!)
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
pages/                   ← 19 Streamlit-Pages (0–18)
  0–12                   ← Basis-Analysen (Yearly, Monthly, Weekday, ToM, etc.)
  13_Shock_Analyzer      ← Öl→DAX, VIX→S&P etc.
  14_Sector_Rotation     ← US/EU Sektor-Heatmap + Rotation
  15_KI_Score            ← Einzelticker KI Score (Radar + Details)
  16_Market_Scanner      ← Multi-Ticker Scanner mit Rankings
  17_Premium_Dashboard   ← Seasonax-Style Einzeltitel-Übersicht
  18_TDOM_Analyse        ← Trading Day of the Month (3 Strategien)
  19_Spot_Vol_Beta       ← Spot-Vol Beta (SPX vs VIX, Regime-Wendepunkte)
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
- [x] Spot-Vol Beta Page + DB-Tabelle (2026-03-20)
- [x] Nightly Refresh Job (GitHub Actions) (2026-03-19)
- [ ] Outlier Manager in alle Pages integrieren (aktuell: Erweiterte Analyse)
- [ ] KI-Zusammenfassung in weitere Pages integrieren
- [ ] Anomaly Engine in weitere Pages integrieren
- [ ] Fehlende 42 Ticker nachladen (ETFs, Aktien, Krypto)
- [ ] Streamlit Cloud Deployment
- [ ] Stripe Freemium/Abo-Integration
- [ ] Supabase User-Auth
- [ ] Domain: seasonaledge.app

## Docs (bei Bedarf lesen)

- `docs/ARCHITECTURE.md` — Datenfluss, Supabase-Schema, Download-Manager, Logger, Cache
- `docs/CHARTS.md` — Plotly Theme, Split-Slider, Distribution Charts
- `docs/AI_MODELS.md` — Technische KI-Dokumentation (Code + API)
- `docs/KI_FEATURES.md` — Alle 11 KI-Features mit Beschreibung (fuer Home Page)
- `docs/MIGRATION.md` — Next.js + FastAPI + Highcharts Migrationspfad

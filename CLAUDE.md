# CLAUDE.md — SeasonalEdge

> Version 9.0 | 2026-03-19 | Details → `docs/`

## Projekt

**SeasonalEdge** — Web-Plattform für saisonale Finanzmarkt-Analyse (ETFs, Aktien, Futures, Crypto).
Freemium + Premium. Phase 1: Streamlit + Supabase + Stripe.

## Entwicklung

```
Pfad:   C:\Dev\Claude\Seasonaledge\
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
  split_slider.py        ← 3-Layer Split-Slider
  supabase_client.py     ← DB-Connector
  logger.py              ← 3 Log-Kanäle (app/error/access)
  strategies/            ← 65+ Strategien
pages/                   ← 13 Streamlit-Pages (0–12)
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
- [ ] `use_container_width` → `width='stretch'`
- [ ] Split-Slider: Ticker-Auswahl (aktuell nur ^DJI)
- [ ] TDOM Backtesting Page
- [ ] Outlier Management (Winsorize 3σ)
- [ ] Streamlit Cloud Deployment
- [ ] Stripe Freemium/Abo-Integration
- [ ] Domain: seasonaledge.app

## Docs (bei Bedarf lesen)

- `docs/ARCHITECTURE.md` — Datenfluss, Supabase-Schema, Download-Manager, Logger
- `docs/CHARTS.md` — Plotly Theme, Split-Slider, Distribution Charts
- `docs/AI_MODELS.md` — DTW, Prophet, Isolation Forest, Claude API
- `docs/MIGRATION.md` — Next.js + FastAPI + Highcharts Migrationspfad

# Seasonal Trading Tool - Development Skill

## Overview
This skill contains best practices, patterns, and domain knowledge for developing and maintaining the SeasonalEdge trading tool — aktuell Streamlit-Prototyp (v8.4), geplante Migration zu Next.js + FastAPI + Highcharts.

**Beim Start jeder Session:** Diesen Skill zuerst lesen, dann PROJEKT_SAISON_STRUKTUR.md. Kein Code schreiben ohne beide Dateien gelesen zu haben.

---

## Core Methodology

### Calculation Method: NORMALIZED RETURNS (Not Price Deltas)

**Critical Decision:**
We use **percentage returns normalized to 100** — NOT absolute price changes like TradingView.

**Why:**
- ✅ Comparable across different price levels (SPY $200 vs $600)
- ✅ No detrending needed (each year starts at 100)
- ✅ Intuitive for retail traders (direct % gain visible)
- ✅ Works across decades without bias

**Code Pattern:**
```python
# CORRECT - Our Method:
for year in available_years:
    cumulative = []
    cum_return = 0
    for i in range(len(year_df)):
        if i == 0:
            cumulative.append(100)
        else:
            daily_ret = year_df.iloc[i]["return"]
            cum_return += daily_ret * 100
            cumulative.append(100 + cum_return)
    year_data[year] = cumulative

avg = np.mean([year_data[y][day] for y in years])
```

**AVOID:**
```python
# WRONG - TradingView Method:
priceChange = close - close[lookback]  # Absolute $ — needs detrending!
```

---

## New Modules (v8.4) — Immer verwenden

### Logging — shared/logger.py
```python
from shared.logger import app_logger, error_logger, access_logger

app_logger.info(f"Download gestartet: {ticker}")
error_logger.error(f"Download fehlgeschlagen: {ticker}", exc_info=True)
access_logger.info(f"LOGIN | user={email} | status=success")
```
- ❌ NIEMALS `print()` für Debugging — immer logger verwenden
- ❌ NIEMALS Passwörter/API-Keys in Logs schreiben
- ❌ NIEMALS `logs/` in Git committen

### Supabase — shared/supabase_client.py
```python
from shared.supabase_client import fetch_seasonality, upsert_prices

data = fetch_seasonality("SPY")       # Vorberechnete Saisonalität lesen
upsert_prices(records)                 # Kursdaten schreiben
```
- Secrets IMMER via `os.environ["SUPABASE_URL"]` — niemals hardcoded
- Lokal: `.streamlit/secrets.toml` (in .gitignore!)
- Streamlit Cloud: Settings → Secrets

### Download-Manager — shared/download_manager.py
```python
from shared.download_manager import DownloadManager

dm = DownloadManager(project_dir)
df = dm.get(ticker="SPY")             # Einzelner Ticker (Cache + DB-Fallback)
results = dm.batch(tickers=[...])     # Batch für Nacht-Job
```
- Ersetzt alle ad-hoc Downloads direkt in Pages
- Nacht-Job via GitHub Actions (Mo–Fr 20:00 UTC)

### Plotly Theme — shared/charts.py
```python
from shared.charts import apply_se_theme

fig = go.Figure(...)
fig = apply_se_theme(fig, title="SPY · Saisonal 1993–2025")
st.plotly_chart(fig, use_container_width=True)
```
- **EINE Zeile** pro Chart — niemals manuell Layout-Properties setzen
- Farben immer aus `SE_COLORS` dict — keine hardcodierten Hex-Werte

### E-Mail — shared/email_brevo.py
```python
from shared.email_brevo import send_transactional

send_transactional(email, template_id=1, params={"name": "Heiko"})
# Template IDs: 1=Willkommen, 2=Passwort-Reset, 3=Premium, 4=Newsletter, 5=Admin-Alert
```

### KI-Modelle — shared/ai_models.py
```python
from shared.ai_models import find_similar_years, forecast_seasonal
from shared.ai_models import detect_outlier_years, generate_seasonal_commentary

# DTW Pattern Matching (Phase 1 — sofort verfügbar)
similar = find_similar_years(current_pattern, all_years_data, top_n=3)

# Prophet Prognose (Phase 1)
forecast = forecast_seasonal(df_prices, periods=60)

# Isolation Forest Ausreißer (Phase 1)
outliers = detect_outlier_years(year_returns_matrix)

# Claude API Kommentar (Phase 1)
comment = generate_seasonal_commentary(ticker, month, avg_return, win_rate, similar)
```

---

## SE_COLORS — Farb-Palette (NIEMALS abweichen)

```python
SE_COLORS = {
    "bg":         "#080c12",
    "surface":    "#0e1520",
    "grid":       "#1c2636",
    "accent":     "#00e5c3",    # Primärakzent Teal
    "accent2":    "#ff6b35",    # Sekundärakzent Orange
    "text":       "#e8edf5",
    "muted":      "#4a5568",
    "positive":   "#00e5c3",
    "negative":   "#ff4757",
    "current_yr": "rgba(232,164,37,0.90)",
    "other_yr":   "rgba(200,220,255,0.40)",
}
```

---

## Architektur-Regeln

### Logik vs. UI — IMMER trennen
- Berechnungen → `shared/`
- UI-Rendering → `pages/`
- Kein Copy-Paste von Berechnungslogik zwischen Pages

### Datenfluss (v8.4)
```
download_manager.py → yahoo_downloader.py / Stooq
        ↓                      ↓
  supabase_client.py       logger.py
        ↓
    data.py (Wrapper — kein Cache!)
        ↓
  calculations.py / ai_models.py
        ↓
  distribution_charts.py + apply_se_theme()
        ↓
     pages/*.py
```

### Import-Header (CRITICAL — in jede Page kopieren)
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

### .gitignore — Pflichteinträge
```
.env
.streamlit/secrets.toml
logs/
*.log
__pycache__/
*.pyc
.venv/
venv/
```

---

## Data Structure Standards

### Year Data Storage
```python
year_data_stacked = {
    2024: {
        "days": [1, 2, 3, ..., 365],
        "cumulative": [100, 100.5, ...],
        "df": year_df
    }, ...
}
```

### Interpolation for Missing Days
```python
for target_day in range(1, 366):
    if target_day in year_days:
        value = year_cum[year_days.index(target_day)]
    else:
        prev_day = max([d for d in year_days if d < target_day])
        next_day = min([d for d in year_days if d > target_day])
        weight = (target_day - prev_day) / (next_day - prev_day)
        value = interpolate(prev_val, next_val, weight)
    full_year_cum.append(value)
```

---

## Feature Implementation Patterns

### 1. Smoothing
```python
smoothing_window = 5
avg_smooth = pd.Series(avg_cumulative).rolling(
    smoothing_window, center=True, min_periods=1
).mean().tolist()
```

### 2. Confidence Bands
```python
std_cumulative = [np.std([year[i] for year in normalized_years]) for i in range(365)]
upper = [avg[i] + std_cumulative[i] for i in range(365)]
lower = [avg[i] - std_cumulative[i] for i in range(365)]
```

### 3. Future Projection
```python
future_days = 60
fig.add_trace(go.Scatter(
    x=list(range(366, 366 + future_days)),
    y=avg_cumulative[:future_days],
    line=dict(dash="dash", color=SE_COLORS["accent2"])
))
```

### 4. Presidential Cycle Filter
```python
def get_presidential_cycle_year(year):
    cycle_position = (year - 2024) % 4
    if cycle_position == 0:   return "Year 4 (Election Year)"
    elif cycle_position == 1: return "Year 1 (Post-Election)"
    elif cycle_position == 2: return "Year 2 (Midterm Election)"
    else:                     return "Year 3 (Pre-Election)"
```

---

## Trading Days & TDoM

**CRITICAL:** Immer echte Handelstage zählen, niemals Kalendertage.

```python
def count_trading_days(start_day, end_day):
    days = []
    for year in available_years:
        df = year_data_stacked[year]["df"]
        period = df[(df["day_of_year"] >= start_day) & (df["day_of_year"] <= end_day)]
        if len(period) > 0:
            days.append(len(period))
    return int(np.mean(days)) if days else 0
```

**TDoM-System:**
- Forward: TDoM 1 = erster Handelstag, TDoM 2 = zweiter, etc.
- Backward: TDoM -1 = letzter Handelstag, TDoM -2 = vorletzter, etc.

---

## Split-Slider (shared/split_slider.py — v7)

```
Layer 1 (layer-axes)  z-index:1  KEIN clip-path  → Achsen IMMER sichtbar
Layer 2 (layer-b)     z-index:2  clip LINKS       → Ø Saisonal-Kurve
Layer 3 (layer-a)     z-index:3  clip RECHTS      → Spaghetti-Einzeljahre
```

```python
from shared.split_slider import render_split_slider
render_split_slider(df, height=520, info="77 Jahre · Live + Hist.")
# df: year, trading_day, cum_return_pct
```

**NICHT tun:**
- ❌ `fill: "toself"` / `"tozeroy"` — deaktiviert Konfidenzband
- ❌ `@st.cache_data` auf `load_dj_data`
- ❌ Beide Kurven in einem Layer

---

## KI-Modelle Übersicht

| Modell | Phase | Priorität | Einsatz |
|--------|-------|-----------|---------|
| DTW Pattern Matching | 1 | ✅ Sofort | Ähnliche Jahre finden |
| Prophet | 1 | ✅ Sofort | 60-Tage-Prognose |
| Isolation Forest | 1 | ✅ Sofort | Ausreißer erkennen |
| Claude API | 1 | ✅ Sofort | NL Markt-Kommentar |
| XGBoost | 2 | ⏳ Später | Multi-Feature Prognose |
| LSTM | 2 | ⏳ Später | Deep Learning Muster |
| Transformer | 3 | ⏳ Phase 3 | Komplexe Mustererkennung |

---

## Supabase Schema (Überblick)

```sql
prices        — ticker, date, OHLCV, source (yahoo|stooq)
seasonality   — ticker, day_of_year, avg_return, std_dev, win_rate, n_years
app_logs      — level, channel, message, user_email, created_at
```

---

## Bekannte Bugs & Fixes

| Bug | Fix |
|-----|-----|
| Yahoo `period="max"` → nur monatl. Daten | `period1=0&period2=now` |
| Yahoo `Open` nicht split-adjustiert | IMMER `Close.iloc[0]` als Basis |
| `import yfinance` | ❌ VERBOTEN — `from shared.yahoo_downloader import download_data` |
| Plotly `titlefont` deprecated | `title=dict(text=..., font=dict(...))` |
| `add_vline` mit String-Labels crasht | `add_shape` + `add_annotation` |
| `fillcolor` Hex→rgba | `int(hex[1:3], 16)` manuell |
| Plotly Typed Arrays (v2.x) | `json.dumps()` + `Plotly.newPlot` |
| Doppelter `@st.cache_data` | Cache nur in `yahoo_downloader.py` |
| `df.index[0].strftime()` | `df['Date'].iloc[0].strftime()` |
| Split-Slider Achsen weggeclippt | 3-Layer-Architektur |
| `use_container_width` deprecated | `width='stretch'` (Deadline Ende 2025) |
| Logs in Git | `logs/` in .gitignore |
| API-Keys im Code | `os.environ["KEY"]` + Streamlit Secrets |

---

## Plotly Dual-Axis Pattern

```python
layout = {
    "yaxis":  {"side": "left"},
    "yaxis2": {"side": "right", "overlaying": "y"},
}
# Trace auf rechter Achse: {"yaxis": "y2", ...}
```

---

## Stooq-Fallback

- `^DJI` → `^dji`: ab ~1928
- `^GSPC` → `^spx`: ab ~1928
- `^GDAXI` / `^DAX` → `^dax`: ab ~1959

---

## Migrations-Stufenplan

```
Phase 1 (jetzt):    Streamlit + Supabase + Stripe + Brevo
Phase 2 (~500 User):Next.js Landingpage (SEO) + LSTM/XGBoost
Phase 3 (~Wachstum):FastAPI Backend
Phase 4 (>500 Abo): Next.js Dashboard + Highcharts (ab ~€400/Jahr Lizenz)
```

**Wann Highcharts kaufen:** Erst ab >500 zahlenden Abonnenten (ROI gesichert).

---

## Code Style

```python
# Variables/Functions: snake_case
start_day, end_day, avg_cumulative
def calculate_stats(...): ...

# Constants: UPPER_CASE
SMOOTHING_WINDOW = 5
DEFAULT_TICKER = "SPY"

# Section Headers:
# ── Abschnitt ──────────────────────────────────────────────
```

---

## Resources

- **yahoo_downloader:** Direkter Yahoo Finance HTTP-Downloader (kein yfinance!)
- **Core Stack:** pandas, plotly, streamlit, numpy, scipy, fastdtw, prophet, sklearn
- **KI:** anthropic (Claude API), tensorflow (LSTM Phase 2), xgboost (Phase 2)
- **Services:** Supabase, Brevo, Stripe, GitHub Actions
- **Inspiration:** Seasonax.com
- **Alpha Vantage API Key:** `SEVZUPQC0UL2O4RF` (Vollhistorie = Premium)

---

## Contact & Updates

**Skill Maintainer:** Claude + Heiko
**Last Updated:** 2026-03-17
**Version:** 8.4

**Changelog:**
- v8.4: Neue Module dokumentiert: logger.py (3 Kanäle), supabase_client.py (Schema), download_manager.py (Queue+Nacht-Job), apply_se_theme() Drop-in, email_brevo.py (5 Templates), ai_models.py (7 Modelle: DTW/Prophet/IsolationForest/ClaudeAPI/XGBoost/LSTM/Transformer). SE_COLORS Palette. .gitignore Pflichteinträge. Datenfluss-Diagramm aktualisiert.
- v8.3: Split-Slider v7 (3-Layer). dj_data.py v3. Home-Page v1. Next.js/FastAPI/Highcharts Stufenplan.
- v8.2: calculations_decade.py, distribution_charts.py, Intra_Decade Page, Stooq-Fallback.
- v8.0: Feiertags-Architektur, Yahoo-Bug-Fixes.
- v7.0: yahoo_downloader.py (kein yfinance).
- v6.0: shared/strategies/.
- v5.0: Weekday, Monthly, Zentralbanken, Mondphasen, TruePath.
- v4.0: Multipage, Turn-of-Month, Feiertags-Effekt.

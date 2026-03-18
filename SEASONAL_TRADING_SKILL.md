# Seasonal Trading Tool - Development Skill

## Overview
This skill contains best practices, patterns, and domain knowledge for developing and maintaining the SeasonalEdge trading tool — aktuell Streamlit-Prototyp, geplante Migration zu Next.js + FastAPI + Highcharts.

---

## Core Methodology

### Calculation Method: NORMALIZED RETURNS (Not Price Deltas)

**Critical Decision:**
We use **percentage returns normalized to 100** - NOT absolute price changes like TradingView.

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
            cumulative.append(100)  # Always start at 100
        else:
            daily_ret = year_df.iloc[i]["return"]
            cum_return += daily_ret * 100
            cumulative.append(100 + cum_return)
    
    year_data[year] = cumulative

# Then average normalized curves:
avg = np.mean([year_data[y][day] for y in years])
```

**AVOID:**
```python
# WRONG - TradingView Method (Price Deltas):
priceChange = close - close[lookback]  # Absolute $
seasonal += priceChange  # Needs detrending!
```

---

## Data Structure Standards

### Year Data Storage
```python
year_data_stacked = {
    2024: {
        "days": [1, 2, 3, ..., 365],      # Day of year
        "cumulative": [100, 100.5, ...],  # Normalized returns
        "df": year_df                      # Original dataframe
    },
    2023: {...},
    ...
}
```

### Interpolation for Missing Days
```python
# Always interpolate to full 365-day calendar:
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

### 1. Smoothing (Moving Average)
```python
smoothing_window = 5
avg_smooth = pd.Series(avg_cumulative).rolling(
    smoothing_window, 
    center=True,
    min_periods=1
).mean().tolist()
```

### 2. Confidence Bands (Standard Deviation)
```python
std_cumulative = []
for day_idx in range(365):
    day_values = [year[day_idx] for year in normalized_years]
    std_cumulative.append(np.std(day_values))

upper = [avg[i] + std[i] for i in range(365)]
lower = [avg[i] - std[i] for i in range(365)]
```

### 3. Future Projection
```python
future_days = 60
future_projection = avg_cumulative[:future_days]
future_x = list(range(366, 366 + future_days))

fig.add_trace(go.Scatter(
    x=future_x,
    y=future_projection,
    line=dict(dash="dash", color="orange")
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

## Trading Days Calculation

**CRITICAL:** Count actual trading days, not calendar days.

```python
def count_trading_days(start_day, end_day):
    trading_days_per_year = []
    for year in available_years:
        year_df = year_data_stacked[year]["df"]
        period_df = year_df[
            (year_df["day_of_year"] >= start_day) & 
            (year_df["day_of_year"] <= end_day)
        ]
        if len(period_df) > 0:
            trading_days_per_year.append(len(period_df))
    return int(np.mean(trading_days_per_year)) if trading_days_per_year else 0
```

---

## Trading Day of Month (TDoM) System

**Forward counting:** TDoM 1 = first trading day, TDoM 2 = second, etc.  
**Backward counting:** TDoM -1 = last trading day, TDoM -2 = second-to-last, etc.

**Why TDoM matters:**
- Pension fund rebalancing clusters around TDoM 1 and TDoM -1
- Options expiration effects are TDoM-based, not calendar-based
- Month-end window dressing by fund managers

---

## Split-Slider Komponente (shared/split_slider.py — v7)

### Architektur: 3-Layer-System

**Problem:** Plotly rendert Achsenbeschriftungen als SVG *innerhalb* des Chart-Divs.
Ein `clip-path` auf dem Layer-Div schneidet daher auch die Achsen mit ab.

**Lösung — 3 überlagerte Divs:**
```
Layer 1 (layer-axes)  z-index:1  KEIN clip-path  → Achsen + Grid IMMER sichtbar
Layer 2 (layer-b)     z-index:2  clip links       → nur Saisonal-Kurve (yaxis2)
Layer 3 (layer-a)     z-index:3  clip rechts      → nur Spaghetti-Kurven (yaxis)
```

Alle 3 Plotly-Charts teilen **exakt dasselbe Layout** → pixel-genaue Überlagerung.
Der Achsen-Chart hat nur unsichtbare Dummy-Traces (opacity=0), rendert aber vollständig
beide Y-Achsen, Grid-Lines und die X-Achse.

**Layout-Konvention:**
- Links (Slider = 0%): `Ø Saisonal` sichtbar
- Rechts (Slider = 100%): `Einzeljahre` sichtbar
- Linke Y-Achse: Einzeljahre % (weiß-blau)
- Rechte Y-Achse: Ø Saisonal % (blau #4d9fff)

**Zero-Alignment (duale Achsen):**
```python
def _align_zero(a_vals, b_vals, pad=0.06):
    # Relative 0-Position berechnen
    pos = max(zero_pos(a_min, a_max), zero_pos(b_min, b_max))
    pos = min(max(pos, 0.15), 0.85)
    # Beide Ranges auf gleiche 0-Position normieren
    y1 = [-pos * a_span, (1-pos) * a_span]
    y2 = [-pos * b_span, (1-pos) * b_span]
```

**Clip-Path Formeln:**
```javascript
// Layer B (Saisonal) sichtbar LINKS vom Divider:
layerB.style.clipPath = `inset(0 ${100-pct}% 0 0)`;
// Layer A (Einzeljahre) sichtbar RECHTS vom Divider:
layerA.style.clipPath = `inset(0 0 0 ${pct}%)`;
```

### NICHT tun bei Split-Slider:
- ❌ `fill: "toself"` oder `fill: "tozeroy"` — Konfidenzband deaktiviert
- ❌ `@st.cache_data` auf `load_dj_data` — friert Exceptions ein
- ❌ Beide Kurven in einem Layer — Achsen werden weggeclippt
- ❌ Nur 1 Layout für 2 Layer — führt zu Rendering-Konflikten

---

## dj_data.py (shared/dj_data.py — v3)

**Architektur:**
- `_DJ_ANNUAL: dict[int, float]` — eingebettete DOW-Jahresrenditen 1950–2024
- `_synthetic_df()` — realistischer Backfill mit Monatsmuster + Normalverteilungs-Rauschen
- `_get_downloader(project_dir)` — importiert yahoo_downloader via 2 Wege
- `load_dj_data(project_dir)` — **kein @st.cache_data** — merged Live + synthetischen Backfill
  - Returns: `(df, source)` wobei source = `"live+synthetic"` | `"synthetic"`
  - df-Spalten: `year, trading_day, cum_return_pct`

**Synthetische Daten:**
```python
# Historisches DOW-Monatsmuster + Rauschen (seed=42, reproduzierbar)
# Jahresendwert wird exakt auf _DJ_ANNUAL[yr] normiert
```

---

## Plotly Best Practices

### Bekannte Bugs & Fixes

| Bug | Fix |
|-----|-----|
| `titlefont` als direkte Property deprecated | `title=dict(text="...", font=dict(...))` |
| `add_vline(x=string_label)` crasht | `add_shape` + `add_annotation` verwenden |
| `fillcolor` Hex→rgba via String-Replace | `int(color[1:3], 16)` manuell konvertieren |
| Plotly Typed Arrays (ab v2.x) | Daten via `json.dumps()` + `Plotly.newPlot` manuell aufrufen |
| `staticPlot: True` deaktiviert Rendering | Entfernen |
| `overflow:hidden` + `position:absolute` → Plotly misst width=0 | Explizite px-Höhe + `Plotly.relayout` nach 150ms |

### Dual-Axis Pattern (Overlaying)
```python
layout = {
    "yaxis":  {"side": "left",  ...},
    "yaxis2": {"side": "right", "overlaying": "y", ...},
}
# Trace auf rechter Achse:
{"yaxis": "y2", ...}
```

---

## Yahoo Finance & Daten

**WICHTIG: yfinance ist aus dem Projekt entfernt.**
Niemals `import yfinance as yf` verwenden. Immer:
```python
from shared.yahoo_downloader import download_data, preprocess
```

### Bekannte Yahoo-Bugs

| Bug | Fix |
|-----|-----|
| `period="max"` → nur monatliche Daten | `period1=0&period2=now` verwenden |
| `Open` nicht split-adjustiert | IMMER `Close.iloc[0]` als Basis |
| `^DJI` liefert nur 1-2 Jahre | Stooq-Fallback `^dji` ab 1928 |

### Stooq-Fallback
- `^DJI` → `^dji`: ab ~1928
- `^GSPC` → `^spx`: ab ~1928
- `^GDAXI` → `^dax`: ab ~1959

---

## Streamlit Patterns

### Import-Header (CRITICAL — sys.path Fix)
```python
import sys, os, pathlib
try:
    _project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
except NameError:
    _project_dir = os.getcwd()
if not os.path.isdir(os.path.join(_project_dir, "shared")):
    for _candidate in [os.getcwd(), ...]:
        if os.path.isdir(os.path.join(_candidate, "shared")):
            _project_dir = _candidate
            break
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)
```

### Bekannte Streamlit-Bugs

| Bug | Fix |
|-----|-----|
| Doppelter `@st.cache_data` friert Daten ein | Cache nur in `yahoo_downloader.py` |
| URL-Konflikt bei Rename | Alte Datei mit `Remove-Item` löschen |
| `df.index[0].strftime(...)` → AttributeError | `df['Date'].iloc[0].strftime(...)` |
| `use_container_width` deprecated | `width='stretch'` (Deadline 2025-12-31) |

---

## Architektur-Prinzipien

- Neue Berechnungen → `shared/`
- UI-Rendering → `pages/`
- Kein Copy-Paste von Berechnungslogik zwischen Pages
- Wiederverwendbare UI-Komponenten → `distribution_charts.py`

### Datenfluss
```
yahoo_downloader.py  ←→  Stooq-Fallback
        ↓
    data.py (Wrapper, kein Cache!)
        ↓
  calculations.py / calculations_decade.py
        ↓
  distribution_charts.py (Visualisierung)
        ↓
     pages/*.py (UI)
```

---

## Umstellungsplan: Next.js + FastAPI + Highcharts

### Empfohlene Strategie (realistisch für Solo-Entwickler)

**NICHT:** Sofort alles umschreiben → 3-6 Monate bis zum heutigen Funktionsstand.  
**STATTDESSEN:** Stufenplan mit parallelem Betrieb:

```
Phase 1 (jetzt):     Streamlit weiter betreiben + stabilisieren
Phase 2 (~500 User): Next.js Landingpage für SEO + Brevo-Newsletter
Phase 3 (~Wachstum): FastAPI-Backend für die rechenintensiven Analysen
Phase 4 (>500 Abo):  Vollständige Migration auf Next.js + Highcharts
```

### Phase 1: Streamlit stabilisieren (aktuell)
- [ ] Streamlit Cloud Deployment
- [ ] Supabase für User-Auth (streamlit-authenticator)
- [ ] Stripe Freemium/Abo
- [ ] GitHub Actions CI/CD

### Phase 2: Next.js Landingpage (parallel)
**Ziel:** Google-Ranking, Newsletter, DSGVO
- **Setup:** Next.js 14+ App Router unter `C:\Dev\SeasonalEdge\frontend\`
- **SEO:** Metadata-API, sitemap.xml, robots.txt
- **DSGVO:** Impressum, Datenschutz, `react-cookie-consent`
- **Newsletter:** Brevo-Formular (server-side)
- **Design:** TailwindCSS + shadcn/ui, Dark Mode, Mobile-First

### Phase 3: FastAPI-Backend
**Ziel:** Rechenlogik aus Streamlit herauslösen
- **Ordnerstruktur:** `C:\Dev\SeasonalEdge\backend\`
  ```
  app/
  ├── api/routers/    ← Endpunkte
  ├── models/         ← Pydantic-Schemas
  ├── services/       ← Berechnungslogik (aus shared/ portiert)
  └── tests/          ← pytest
  ```
- **JSON-Format:** Highcharts-kompatibel via `to_dict(orient='records')`
- **CORS:** Aktiviert für Next.js Frontend
- **Async:** FastAPI Background Tasks für Daten-Updates
- **Tests:** pytest für alle Service-Funktionen

### Phase 4: Next.js Dashboard + Highcharts
**Ziel:** Premium-UI, professionelle Charts
- **Highcharts:** `highcharts-react-official`, SSR-Kompatibel, Lazy-Loading
  ```typescript
  // Highcharts-äquivalent zu unserem Split-Slider:
  // Highcharts.chart('container', {
  //   series: [{ data: spaghettiData, yAxis: 0 }, { data: avgData, yAxis: 1 }],
  //   yAxis: [{ title: 'Einzeljahre %' }, { title: 'Ø Saisonal %', opposite: true }]
  // })
  ```
- **Auth:** Supabase Auth mit MFA + RBAC (Freemium vs. Premium)
- **Dashboard:** shadcn/ui Tabs, Charts, Modals
- **Monitoring:** Sentry + Prometheus

### Technischer Ziel-Stack
```
Frontend:  Next.js 14+, React 18, TailwindCSS, shadcn/ui, Highcharts 11+
Backend:   FastAPI 0.100+, Python 3.11+, Pydantic, SQLAlchemy, Supabase
Daten:     Yahoo Finance, Stooq (Backfill), Alpha Vantage (Premium)
Services:  Stripe (Payments), Brevo (Newsletter), GitHub Actions (CI/CD)
Deploy:    Vercel (Next.js), Railway/Fly.io (FastAPI), Supabase (DB/Auth)
```

### Highcharts vs. Plotly — Wichtige Unterschiede
| Feature | Plotly (aktuell) | Highcharts (Ziel) |
|---------|-----------------|-------------------|
| Lizenz | Open Source | Commercial (benötigt Kauf) |
| Performance | Gut | Sehr gut (v8+ Stock Charts) |
| Dual Y-Axis | `yaxis2` + `overlaying:"y"` | `yAxis: [{}, {opposite:true}]` |
| Clip/Split | Manuell via CSS clip-path | Nativ: `plotBands` + Custom Renderer |
| Bundle Size | ~3MB | ~1MB (tree-shakeable) |
| SSR | Eingeschränkt | Vollständig via `highcharts/node` |

### Wann umstellen?
- **Next.js Landingpage:** Sofort (SEO-Vorteil)
- **FastAPI Backend:** Ab ~100 tägl. Nutzern (Performance)
- **Highcharts Migration:** Ab ~500 zahlenden Abonnenten (ROI rechtfertigt Lizenzkosten)
- **Vollständige Migration:** Ab nachgewiesenem Product-Market-Fit

---

## Code Style Guidelines

```python
# Variables: snake_case
start_day, end_day, avg_cumulative

# Functions: snake_case mit Verben
def calculate_stats(...):
def get_presidential_cycle(...):

# Constants: UPPER_CASE
SMOOTHING_WINDOW = 5
DEFAULT_TICKER = "SPY"

# Kommentare: Section Headers
# ── Section Headers ────────────────────────────────────────
```

---

## Resources & References

- **yahoo_downloader**: Direkter Yahoo Finance HTTP-Downloader
- **pandas, plotly, streamlit, numpy, scipy, fastdtw**: Core Stack
- **Highcharts 11+**: Ziel-Charting-Library (Next.js Migration)
- **Seasonax.com**: Pattern visualization inspiration
- **Alpha Vantage API Key:** `SEVZUPQC0UL2O4RF` (Vollhistorie = Premium)

---

## Contact & Updates

**Skill Maintainer:** Claude + Heiko  
**Last Updated:** 2026-03-13  
**Version:** 8.3  

**Changelog:**
- v8.3: Split-Slider v7 (3-Layer-Architektur, Achsen immer sichtbar, Zero-Alignment, Kein Konfidenzband). dj_data.py v3 (Live+synthetischer Backfill, kein Cache). Home-Page v1 (Split-Slider Integration). Umstellungsplan Next.js+FastAPI+Highcharts eingearbeitet (Stufenplan empfohlen: Landingpage sofort, Backend ab 100 User, Highcharts ab 500 Abo).
- v8.2: Neue shared-Module calculations_decade.py + distribution_charts.py. Neue Page 11_📊_Intra_Decade_Seasonality.py. Stooq-Fallback in yahoo_downloader.py. Box-Plot + Heatmap + Kontext-Panel. Monthly Seasonals: Vola als 2. Y-Achse. _hex_to_rgba Fix.
- v8.0: Neue Feiertags-Architektur (nyse_holidays.py, exchange_holidays.py), Yahoo Finance Bug-Fixes.
- v7.0: yahoo_downloader.py (direkter HTTP ohne yfinance), data.py als dünner Wrapper.
- v6.0: shared/strategies/ Untermodul (definitions.py mit 65+ Strategien).
- v5.0: Weekday-Analyse, Monthly Performance, Zentralbanken, Mondphasen, TruePath KI.
- v4.0: Multipage-Architektur, Turn-of-Month, Feiertags-Effekt.

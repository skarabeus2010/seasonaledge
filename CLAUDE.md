# CLAUDE.md — SeasonalEdge Projekt-Kontext

> Diese Datei liegt im Repo-Root und wird von Claude Code automatisch gelesen.
> Lege sie ab unter: `C:\Dev\Claude\Saisonalcharts\CLAUDE.md`
> Version: 8.4 | Stand: 2026-03-17

---

## 1. Vision & Geschäftsmodell

**SeasonalEdge** ist eine Web-Plattform zur Analyse saisonaler Muster in Finanzinstrumenten (ETFs, Aktien, Futures, Crypto). Kombination aus klassischer Saisonalitätsanalyse und KI-gestützten Methoden.

- **Freemium:** Basis-Charts kostenlos + rotierender "Freier Tag" mit Vollzugriff
- **Premium:** KI-Analysen, Stooq-Langzeitdaten, alle Indikatoren
- **Phase 1 Deploy:** Streamlit Cloud + Supabase PostgreSQL + Stripe
- **Phase 4 Deploy:** Next.js + FastAPI + Highcharts (ab ~500 Abo)

---

## 2. Lokale Entwicklungsumgebung

```
Pfad:    C:\Dev\Claude\Saisonalcharts\
Start:   py -m streamlit run seasonal_app.py
Python:  PowerShell → immer `py -m` verwenden (nicht `python`)
```

---

## 3. Aktuelle Projektstruktur (v8.4)

```
Saisonalcharts/
├── seasonal_app.py                        ← Dashboard / Startseite
├── CLAUDE.md                              ← Diese Datei
├── shared/
│   ├── __init__.py
│   ├── constants.py
│   ├── data.py                            ← Wrapper (KEIN Cache hier!)
│   ├── yahoo_downloader.py                ← HTTP-Downloader + Stooq-Fallback
│   ├── download_manager.py                ← Zentraler Download-Manager
│   ├── dj_data.py                         ← DOW-Daten für Split-Slider
│   ├── split_slider.py                    ← Split-Slider Komponente (v7)
│   ├── calculations.py
│   ├── calculations_decade.py
│   ├── distribution_charts.py
│   ├── charts.py                          ← Plotly Custom Theme (apply_se_theme)
│   ├── holidays.py
│   ├── nyse_holidays.py
│   ├── exchange_holidays.py
│   ├── central_banks.py
│   ├── fed_dates.py
│   ├── symbols.py
│   ├── supabase_client.py                 ← Supabase DB-Connector
│   ├── logger.py                          ← Zentrales Logging-Modul
│   ├── email_brevo.py                     ← Brevo E-Mail-Integration
│   ├── ai_models.py                       ← KI-Modelle (DTW, LLM, Prophet)
│   └── strategies/
│       ├── __init__.py
│       ├── definitions.py                 ← 65+ Strategien
│       ├── januar_trifecta.py
│       └── kaeppel.py
├── logs/                                  ← NICHT in Git!
│   ├── app.log
│   ├── error.log
│   └── access.log
└── pages/
    ├── 0_🏠_Home.py
    ├── 1_📊_Yearly_Seasonals.py
    ├── 2_📆_Monthly_Seasonals.py
    ├── 3_📅_Weekday_Seasonals.py
    ├── 4_🔄_Turn_of_the_Month.py
    ├── 5_📅_Feiertags_Effekt.py
    ├── 6_🏛️_Zentralbanken.py
    ├── 7_🌕_Mondphasen.py
    ├── 8_🔮_TruePath.py
    ├── 9_🚦_Strategien.py
    ├── 10_📅_OPEX.py
    ├── 11_📊_Intra_Decade_Seasonality.py
    └── 12_🌙_Overnight_vs_Intraday.py
```

---

## 4. Datenfluss (v8.4)

```
download_manager.py  ←→  yahoo_downloader.py  ←→  Stooq-Fallback
        ↓                          ↓
  supabase_client.py          logger.py (app.log)
        ↓
    data.py (Wrapper, kein Cache!)
        ↓
  calculations.py / calculations_decade.py
        ↓                          ↓
  distribution_charts.py      ai_models.py
        ↓                          ↓
     pages/*.py (UI)         apply_se_theme()
```

---

## 5. Kern-Methodik: NORMALISIERTE RENDITEN

**Wir verwenden prozentuale Renditen normiert auf 100 — NICHT absolute Preisänderungen.**

```python
# CORRECT — SeasonalEdge Methode:
for year in available_years:
    cumulative = []
    cum_return = 0
    for i in range(len(year_df)):
        if i == 0:
            cumulative.append(100)  # Immer bei 100 starten
        else:
            daily_ret = year_df.iloc[i]["return"]
            cum_return += daily_ret * 100
            cumulative.append(100 + cum_return)
    year_data[year] = cumulative

# Durchschnitt über alle Jahre:
avg = np.mean([year_data[y][day] for y in years])

# WRONG — TradingView Methode (niemals verwenden):
# priceChange = close - close[lookback]  → braucht Detrending!
```

---

## 6. Import-Header (CRITICAL — sys.path Fix)

**Jede Page muss mit diesem Block starten:**

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

---

## 7. Kritische Bugs & Fixes

| Bug | Fix |
|-----|-----|
| Yahoo `period="max"` → nur monatliche Daten | `period1=0&period2=now` verwenden |
| Yahoo `Open` nicht split-adjustiert | IMMER `Close.iloc[0]` als Basis |
| `import yfinance` — VERBOTEN | `from shared.yahoo_downloader import download_data` |
| Plotly `titlefont` deprecated | `title=dict(text=..., font=dict(...))` |
| Plotly `add_vline` mit String-Labels crasht | `add_shape` + `add_annotation` |
| Plotly `fillcolor` Hex→rgba | `int(hex[1:3], 16)` manuell konvertieren |
| Plotly Typed Arrays (v2.x) | `json.dumps()` + `Plotly.newPlot` manuell |
| Doppelter `@st.cache_data` friert Daten ein | Cache NUR in `yahoo_downloader.py` |
| `@st.cache_data` auf `load_dj_data` | Entfernen — friert Exceptions ein |
| Streamlit URL-Konflikt bei Rename | Alte Datei mit `Remove-Item` löschen |
| `df.index[0].strftime()` → AttributeError | `df['Date'].iloc[0].strftime()` |
| Split-Slider: Achsen werden weggeclippt | 3-Layer-Architektur (layer-axes ohne clip) |
| Clip-Path Richtung falsch | Layer B: `inset(0 right% 0 0)`, A: `inset(0 0 0 pct%)` |
| `use_container_width` deprecated | `width='stretch'` (Deadline Ende 2025) |
| Logs in Git committet | `logs/` in `.gitignore` eintragen |
| API-Keys im Code | Immer `os.environ["KEY"]` + Streamlit Secrets |
| `print()` für Debugging | `app_logger.debug()` / `error_logger.error()` |

---

## 8. Yahoo Finance & Stooq

**WICHTIG: yfinance ist aus dem Projekt entfernt. Niemals `import yfinance as yf` verwenden.**

```python
from shared.yahoo_downloader import download_data, preprocess
```

### Stooq-Fallback (Langzeitdaten ab 1928)
| Yahoo Ticker | Stooq Ticker | Daten ab |
|---|---|---|
| `^DJI` | `^dji` | ~1928 |
| `^GSPC` | `^spx` | ~1928 |
| `^GDAXI` / `^DAX` | `^dax` | ~1959 |

---

## 9. shared/logger.py — Logging-System

### 3 Log-Kanäle
```
logs/app.log      ← INFO + WARNING: App-Events (Starts, Downloads, Berechnungen)
logs/error.log    ← ERROR + CRITICAL: Exceptions + Tracebacks
logs/access.log   ← INFO: Logins, Seitenaufrufe, Ticker-Anfragen
```

### Setup
```python
# shared/logger.py
import logging, os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

def _make_handler(filename, level):
    h = RotatingFileHandler(
        os.path.join(LOG_DIR, filename),
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5
    )
    h.setLevel(level)
    h.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    return h

app_logger    = logging.getLogger("seasonaledge.app")
error_logger  = logging.getLogger("seasonaledge.error")
access_logger = logging.getLogger("seasonaledge.access")

app_logger.addHandler(_make_handler("app.log",    logging.INFO))
error_logger.addHandler(_make_handler("error.log", logging.ERROR))
access_logger.addHandler(_make_handler("access.log", logging.INFO))
```

### Verwendung
```python
from shared.logger import app_logger, error_logger, access_logger

app_logger.info(f"Download gestartet: {ticker}")
app_logger.warning(f"Yahoo Rate-Limit, Stooq-Fallback aktiv")

try:
    df = download_data(ticker)
except Exception as e:
    error_logger.error(f"Download fehlgeschlagen: {ticker}", exc_info=True)

access_logger.info(f"LOGIN | user={email} | ip={ip} | status=success")
access_logger.info(f"PAGE  | user={email} | page=Yearly_Seasonals | ticker={ticker}")
```

### Regeln
- ❌ `print()` für Debugging — immer Logger verwenden
- ❌ Passwörter / API-Keys / Nutzerdaten in Logs
- ❌ `logs/` ins Git-Repo committen
- Auf Streamlit Cloud: Logs in Supabase `app_logs` Tabelle spiegeln

---

## 10. shared/supabase_client.py — Datenbank

### Tabellen-Schema
```sql
-- Kursdaten
CREATE TABLE prices (
    id         BIGSERIAL PRIMARY KEY,
    ticker     TEXT NOT NULL,
    date       DATE NOT NULL,
    open       FLOAT, high FLOAT, low FLOAT,
    close      FLOAT NOT NULL,
    volume     BIGINT,
    source     TEXT DEFAULT 'yahoo',
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(ticker, date)
);

-- Vorberechnete Saisonalität
CREATE TABLE seasonality (
    id          BIGSERIAL PRIMARY KEY,
    ticker      TEXT NOT NULL,
    day_of_year INT NOT NULL,
    avg_return  FLOAT,
    std_dev     FLOAT,
    win_rate    FLOAT,
    n_years     INT,
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(ticker, day_of_year)
);

-- Logging in DB (für Streamlit Cloud, kein persistentes Filesystem)
CREATE TABLE app_logs (
    id         BIGSERIAL PRIMARY KEY,
    level      TEXT,
    channel    TEXT,
    message    TEXT,
    user_email TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Connector
```python
# shared/supabase_client.py
from supabase import create_client
import os

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

_client = None

def get_client():
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client

def fetch_seasonality(ticker: str) -> list[dict]:
    return get_client().table("seasonality").select("*").eq("ticker", ticker).execute().data

def upsert_prices(records: list[dict]):
    get_client().table("prices").upsert(records, on_conflict="ticker,date").execute()
```

### Secrets (niemals in Code!)
```toml
# .streamlit/secrets.toml  (lokal, in .gitignore!)
SUPABASE_URL = "https://xyz.supabase.co"
SUPABASE_KEY = "eyJ..."
```

---

## 11. shared/download_manager.py

### Architektur
```
download_manager.py
    ├── TickerQueue     — priorisierte Download-Warteschlange
    ├── RateLimiter     — Yahoo: max. 2000 Req/h, Stooq: max. 500 Req/h
    ├── CacheLayer      — lokaler In-Memory-Cache (TTL 6h)
    └── DBSync          — schreibt fertige Daten nach Supabase
```

### API
```python
from shared.download_manager import DownloadManager

dm = DownloadManager(project_dir)
df = dm.get(ticker="SPY", start="1993-01-01")           # Einzelner Ticker
results = dm.batch(tickers=["SPY", "QQQ"], workers=4)   # Batch
status = dm.status()  # {"queued": 42, "done": 958, "failed": 0}
```

### Priorisierung
```
Priorität 1: Ticker die gerade im Frontend angefragt werden (Live)
Priorität 2: Top-100 Ticker (täglich)
Priorität 3: Alle weiteren 900 Ticker (wöchentlich)
```

### Nacht-Job (GitHub Actions)
```yaml
# .github/workflows/nightly_update.yml
name: Nightly Data Update
on:
  schedule:
    - cron: '0 20 * * 1-5'   # Mo–Fr 20:00 UTC (22:00 MEZ)
jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt
      - run: python -m shared.download_manager --batch-all
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
```

---

## 12. shared/charts.py — Plotly Custom Theme

### Farb-Palette
```python
SE_COLORS = {
    "bg":         "#080c12",
    "surface":    "#0e1520",
    "grid":       "#1c2636",
    "accent":     "#00e5c3",    # Teal
    "accent2":    "#ff6b35",    # Orange
    "text":       "#e8edf5",
    "muted":      "#4a5568",
    "positive":   "#00e5c3",
    "negative":   "#ff4757",
    "current_yr": "rgba(232,164,37,0.90)",
    "other_yr":   "rgba(200,220,255,0.40)",
}
```

### Drop-in Funktion
```python
def apply_se_theme(fig, title: str = "", height: int = 420) -> go.Figure:
    """1 Zeile pro Chart — einheitliches Theme."""
    fig.update_layout(
        paper_bgcolor=SE_COLORS["bg"],
        plot_bgcolor=SE_COLORS["bg"],
        height=height,
        font=dict(family="DM Mono, monospace", color=SE_COLORS["muted"], size=11),
        title=dict(text=title, font=dict(color=SE_COLORS["text"], size=14), x=0.01),
        margin=dict(t=40, r=20, b=40, l=52),
        hovermode="x unified",
        hoverlabel=dict(bgcolor=SE_COLORS["surface"], bordercolor=SE_COLORS["accent"],
                        font=dict(color=SE_COLORS["text"], size=12)),
        legend=dict(bgcolor="rgba(14,21,32,0.8)", bordercolor=SE_COLORS["grid"],
                    borderwidth=1, font=dict(color=SE_COLORS["muted"], size=10)),
        xaxis=dict(gridcolor=SE_COLORS["grid"], linecolor=SE_COLORS["grid"],
                   tickcolor=SE_COLORS["grid"], zeroline=False),
        yaxis=dict(gridcolor=SE_COLORS["grid"], linecolor=SE_COLORS["grid"],
                   tickcolor=SE_COLORS["grid"], zeroline=True,
                   zerolinecolor="#2d3f57", zerolinewidth=1)
    )
    return fig

# Verwendung:
# fig = go.Figure(...)
# fig = apply_se_theme(fig, title="SPY · Saisonal 1993–2025")
# st.plotly_chart(fig, use_container_width=True)
```

### Dual-Axis Pattern
```python
layout = {
    "yaxis":  {"side": "left"},
    "yaxis2": {"side": "right", "overlaying": "y"},
}
# Trace auf rechter Achse: {"yaxis": "y2", ...}
```

---

## 13. shared/split_slider.py — v7 (3-Layer-Architektur)

### Problem & Lösung
Plotly rendert Achsenbeschriftungen als SVG *innerhalb* des Chart-Divs.
Ein `clip-path` auf dem Layer-Div schneidet daher auch Achsen ab.

**Lösung — 3 überlagerte Divs:**
```
Layer 1 (layer-axes)  z-index:1  KEIN clip-path  → Achsen IMMER sichtbar
Layer 2 (layer-b)     z-index:2  clip LINKS       → Ø Saisonal-Kurve (yaxis2)
Layer 3 (layer-a)     z-index:3  clip RECHTS      → Spaghetti-Einzeljahre (yaxis)
```

### Clip-Path Formeln
```javascript
layerB.style.clipPath = `inset(0 ${100-pct}% 0 0)`;  // Layer B: sichtbar links
layerA.style.clipPath = `inset(0 0 0 ${pct}%)`;       // Layer A: sichtbar rechts
```

### Zero-Alignment (duale Achsen)
```python
def _align_zero(a_vals, b_vals, pad=0.06):
    pos = max(zero_pos(a_min, a_max), zero_pos(b_min, b_max))
    pos = min(max(pos, 0.15), 0.85)
    y1 = [-pos * a_span, (1-pos) * a_span]
    y2 = [-pos * b_span, (1-pos) * b_span]
```

### API
```python
from shared.split_slider import render_split_slider
render_split_slider(df, height=520, info="77 Jahre · Live + Hist.")
# df muss Spalten haben: year, trading_day, cum_return_pct
```

### Design-Regeln
- Links (0%) = Ø Saisonal (#4d9fff), Rechts (100%) = Einzeljahre
- Aktuelles Jahr: `rgba(232,164,37,0.90)`, width=2.5
- Andere Jahre: `rgba(200,220,255,0.40)`, width=1.0
- ❌ `fill: "toself"` / `fill: "tozeroy"` — Konfidenzband deaktiviert
- ❌ `@st.cache_data` auf `load_dj_data`
- ❌ Beide Kurven in einem Layer

---

## 14. shared/dj_data.py — v3

```python
from shared.dj_data import load_dj_data
df, source = load_dj_data(project_dir)
# source: "live+synthetic" | "synthetic"
# df-Spalten: year, trading_day, cum_return_pct
# KEIN @st.cache_data!
```

Architektur:
- `_DJ_ANNUAL: dict[int, float]` — eingebettete DOW-Jahresrenditen 1950–2024
- `_synthetic_df()` — realistischer Backfill (Monatsmuster + Normalverteilungs-Rauschen, seed=42)
- `load_dj_data()` — merged Live + synthetischen Backfill

---

## 15. shared/ai_models.py — KI-Modelle

| Modell | Use Case | Priorität |
|--------|----------|-----------|
| DTW Pattern Matching | Ähnliche historische Jahre | ✅ Phase 1 |
| Prophet | Saisonale Prognose 60 Tage | ✅ Phase 1 |
| Isolation Forest | Ausreißer-Jahre erkennen | ✅ Phase 1 |
| Claude API | Natural Language Kommentar | ✅ Phase 1 |
| LSTM | Komplexe Mustererkennung | ⏳ Phase 2 |
| XGBoost | Multi-Feature Renditeprognose | ⏳ Phase 2 |
| Transformer | Attention-basierte Analyse | ⏳ Phase 3 |

### DTW Pattern Matching
```python
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean

def find_similar_years(current_pattern, all_years_data, top_n=3):
    scores = {}
    for year, pattern in all_years_data.items():
        dist, _ = fastdtw(current_pattern, pattern, dist=euclidean)
        scores[year] = dist
    return sorted(scores.items(), key=lambda x: x[1])[:top_n]
```

### Prophet
```python
from prophet import Prophet

def forecast_seasonal(df_prices, periods=60):
    m = Prophet(yearly_seasonality=True, weekly_seasonality=False)
    m.fit(df_prices.rename(columns={"Date": "ds", "Close": "y"}))
    future = m.make_future_dataframe(periods=periods)
    return m.predict(future)[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(periods)
```

### Isolation Forest
```python
from sklearn.ensemble import IsolationForest

def detect_outlier_years(year_returns_matrix):
    clf = IsolationForest(contamination=0.1, random_state=42)
    labels = clf.fit_predict(year_returns_matrix)
    return [y for y, l in zip(years, labels) if l == -1]
```

### Claude API (Natural Language Kommentar)
```python
import anthropic

def generate_seasonal_commentary(ticker, month, avg_return, win_rate, similar_years):
    client = anthropic.Anthropic()
    prompt = f"""
    Analysiere kurz das saisonale Muster für {ticker} im Monat {month}:
    - Durchschnittliche Rendite: {avg_return:.1f}%
    - Win-Rate: {win_rate:.0f}%
    - Ähnlichste historische Jahre: {similar_years}
    Antworte in 2-3 Sätzen auf Deutsch. Keine Anlageempfehlung.
    """
    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text
```

---

## 16. shared/email_brevo.py

```python
import requests, os
from shared.logger import app_logger

BREVO_API_KEY = os.environ["BREVO_API_KEY"]
SENDER = {"name": "SeasonalEdge", "email": "noreply@seasonaledge.app"}

def send_transactional(to_email: str, template_id: int, params: dict):
    resp = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={"api-key": BREVO_API_KEY, "Content-Type": "application/json"},
        json={"sender": SENDER, "to": [{"email": to_email}],
              "templateId": template_id, "params": params}
    )
    resp.raise_for_status()
    app_logger.info(f"E-Mail gesendet: template={template_id} to={to_email}")
```

### Template-IDs
```
ID 1: Willkommen / E-Mail-Bestätigung
ID 2: Passwort zurücksetzen
ID 3: Premium-Buchungsbestätigung
ID 4: Wöchentlicher Newsletter
ID 5: Admin-Alert (Systemfehler)
```

---

## 17. Feature-Implementierungen

### Smoothing (Moving Average)
```python
avg_smooth = pd.Series(avg_cumulative).rolling(5, center=True, min_periods=1).mean().tolist()
```

### Confidence Bands
```python
std_cumulative = [np.std([year[i] for year in normalized_years]) for i in range(365)]
upper = [avg[i] + std_cumulative[i] for i in range(365)]
lower = [avg[i] - std_cumulative[i] for i in range(365)]
```

### Presidential Cycle Filter
```python
def get_presidential_cycle_year(year):
    cycle_position = (year - 2024) % 4
    if cycle_position == 0:   return "Year 4 (Election Year)"
    elif cycle_position == 1: return "Year 1 (Post-Election)"
    elif cycle_position == 2: return "Year 2 (Midterm Election)"
    else:                     return "Year 3 (Pre-Election)"
```

### Trading Days (CRITICAL: Handelstage, keine Kalendertage)
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

### TDoM (Trading Day of Month)
- Forward: TDoM 1 = erster Handelstag, TDoM 2 = zweiter usw.
- Backward: TDoM -1 = letzter Handelstag, TDoM -2 = vorletzter usw.

---

## 18. shared/distribution_charts.py — Funktionsübersicht

| Funktion | Beschreibung |
|----------|-------------|
| `build_box_plot(groups, ...)` | Generischer Box-Plot |
| `build_monthly_heatmap(df, years, ticker)` | Heatmap Jahre × Monate |
| `build_decade_monthly_heatmap(df, ticker)` | Heatmap Dekaden × Monate |
| `build_monthly_bar_with_vola(month_stats, ...)` | Balken + Vola als 2. Y-Achse |
| `get_current_context_stats(returns, label, all_returns)` | Statistiken + Rating |
| `render_boxplot_explanation()` | Leseanleitung als `st.caption()` |
| `_hex_to_rgba(hex_color, alpha)` | Hilfsfunktion Hex→rgba |

---

## 19. .gitignore (Pflicht)

```gitignore
# Secrets
.env
.streamlit/secrets.toml

# Logs (NIEMALS in Git!)
logs/
*.log

# Python
__pycache__/
*.pyc
.venv/
venv/

# OS
.DS_Store
Thumbs.db
```

---

## 20. Migrationspfad: Next.js + FastAPI + Highcharts

```
Phase 1 (jetzt):     Streamlit stabilisieren + Deployment
Phase 2 (~500 User): Next.js Landingpage (SEO + Newsletter)
Phase 3 (~Wachstum): FastAPI-Backend für Berechnungslogik
Phase 4 (>500 Abo):  Vollmigration Next.js + Highcharts
```

### Technischer Ziel-Stack (Phase 4)
```
Frontend:  Next.js 14+, React 18, TailwindCSS, shadcn/ui, Highcharts 11+
Backend:   FastAPI 0.100+, Python 3.11+, Pydantic, SQLAlchemy, Supabase
KI:        LSTM, XGBoost, Transformer, Claude API
Services:  Stripe, Brevo, GitHub Actions, Sentry, Docker
Deploy:    Vercel (Next.js), Railway/Fly.io (FastAPI), Supabase (DB/Auth)
```

### Highcharts vs. Plotly
| Feature | Plotly (aktuell) | Highcharts (Ziel) |
|---------|-----------------|-------------------|
| Lizenz | Open Source | Commercial (~€400/Jahr) |
| Dual Y-Axis | `yaxis2` + `overlaying:"y"` | `yAxis: [{}, {opposite:true}]` |
| Clip/Split | Manuell via CSS clip-path | Nativ: `plotBands` + Custom Renderer |
| Bundle Size | ~3MB | ~1MB (tree-shakeable) |
| SSR | Eingeschränkt | Vollständig via `highcharts/node` |

**Wann umstellen:**
- Next.js Landingpage: Sofort (SEO-Vorteil)
- FastAPI Backend: Ab ~100 tägl. Nutzern
- Highcharts: Ab ~500 zahlenden Abonnenten

---

## 21. Architektur-Prinzipien

- Neue Berechnungen → `shared/`
- UI-Rendering → `pages/`
- ❌ Kein Copy-Paste von Berechnungslogik zwischen Pages
- Wiederverwendbare UI-Komponenten → `distribution_charts.py`
- Cache NUR in `yahoo_downloader.py`

---

## 22. API-Keys & Secrets

```
Alpha Vantage:  SEVZUPQC0UL2O4RF  (Vollhistorie = Premium)
Supabase URL:   in .streamlit/secrets.toml  → os.environ["SUPABASE_URL"]
Supabase Key:   in .streamlit/secrets.toml  → os.environ["SUPABASE_KEY"]
Brevo API Key:  in .streamlit/secrets.toml  → os.environ["BREVO_API_KEY"]
Anthropic Key:  in .streamlit/secrets.toml  → os.environ["ANTHROPIC_API_KEY"]
```

---

## 23. Offene Roadmap

### Kurzfristig (nächste Sessions)
- [ ] `shared/logger.py` anlegen + in alle Module einbinden
- [ ] `shared/supabase_client.py` anlegen + Tabellen-Schema deployen
- [ ] `shared/download_manager.py` anlegen
- [ ] `shared/charts.py` → `apply_se_theme()` Drop-in ergänzen
- [ ] `shared/ai_models.py` anlegen (DTW + Prophet + Claude API)
- [ ] `shared/email_brevo.py` anlegen
- [ ] `logs/` Verzeichnis + `.gitignore` anlegen
- [ ] `use_container_width` → `width='stretch'` (Deadline Ende 2025)
- [ ] `seasonal_app.py` Zeile 243+: `df.index[...]` → `df['Date'].iloc[...]`
- [ ] Split-Slider: Ticker-Auswahl (aktuell nur ^DJI)
- [ ] TDOM Backtesting Page
- [ ] Outlier Management (Winsorize 3σ, Exclude Years Widget)

### Phase 1: Deployment
- [ ] GitHub-Repo anlegen
- [ ] Streamlit Cloud Deployment
- [ ] Supabase PostgreSQL + User-Auth
- [ ] Nightly GitHub Action (Download-Manager Batch)
- [ ] Stripe Freemium/Abo-Integration
- [ ] Brevo-Newsletter-Anbindung
- [ ] Domain: seasonaledge.app (INWX.de, ~15 EUR/Jahr)

---

## 24. Code Style

```python
# Variables:    snake_case         → start_day, avg_cumulative
# Functions:    snake_case Verben  → calculate_stats(), get_presidential_cycle()
# Constants:    UPPER_CASE         → SMOOTHING_WINDOW = 5
# Section Headers:
# ── Abschnitt ─────────────────────────────────────
```

---

**Maintainer:** Claude + Heiko
**Version:** 8.4
**Stand:** 2026-03-17

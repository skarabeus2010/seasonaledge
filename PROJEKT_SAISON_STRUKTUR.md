# Projekt-Kontext: SeasonalEdge (v8.4)

## 1. Vision & Kernzweck
SeasonalEdge ist eine Web-Plattform zur Analyse saisonaler Muster in Finanzinstrumenten (ETFs, Aktien, Futures, Crypto). Die Plattform kombiniert klassische Saisonalitätsanalyse mit KI-gestützten Methoden, um lukrative saisonale Zyklen zu identifizieren.

## 2. Geschäftsmodell
- **Freemium-Modell:** Freier Bereich mit Basis-Charts + rotierender "Freier Tag" mit Vollzugriff
- **Premium-Modell:** Vollständiger Zugriff auf KI-Analysen, Stooq-Langzeitdaten, alle Indikatoren
- **Deployment-Ziel (Phase 1):** Streamlit Cloud + Supabase PostgreSQL + Stripe
- **Deployment-Ziel (Phase 4):** Next.js + FastAPI + Highcharts (ab ~500 Abo)

## 3. Lokale Entwicklungsumgebung
- **Pfad:** `C:\Dev\Claude\Saisonalcharts\`
- **Start:** `py -m streamlit run seasonal_app.py` (aus Saisonalcharts-Verzeichnis)
- **Python:** PowerShell kann Python nicht direkt aufrufen → immer `py -m` verwenden

## 4. Aktuelle Projektstruktur (v8.4)

```
Saisonalcharts/
├── seasonal_app.py                        ← Dashboard / Startseite
├── shared/
│   ├── __init__.py
│   ├── constants.py
│   ├── data.py                            ← Wrapper (kein Cache hier!)
│   ├── yahoo_downloader.py                ← HTTP-Downloader + Stooq-Fallback
│   ├── download_manager.py                ← NEU v8.4: Zentraler Download-Manager
│   ├── dj_data.py                         ← DOW-Daten für Split-Slider
│   ├── split_slider.py                    ← Split-Slider Komponente (v7)
│   ├── calculations.py
│   ├── calculations_decade.py
│   ├── distribution_charts.py
│   ├── charts.py                          ← Plotly Custom Theme (v8.4)
│   ├── holidays.py
│   ├── nyse_holidays.py
│   ├── exchange_holidays.py
│   ├── central_banks.py
│   ├── fed_dates.py
│   ├── symbols.py
│   ├── supabase_client.py                 ← NEU v8.4: Supabase DB-Connector
│   ├── logger.py                          ← NEU v8.4: Zentrales Logging-Modul
│   ├── email_brevo.py                     ← NEU v8.4: Brevo E-Mail-Integration
│   ├── ai_models.py                       ← NEU v8.4: KI-Modelle (DTW, LLM, Prophet)
│   └── strategies/
│       ├── __init__.py
│       ├── definitions.py
│       ├── januar_trifecta.py
│       └── kaeppel.py
├── logs/                                  ← NEU v8.4: Log-Verzeichnis
│   ├── app.log                            ← Allgemeines App-Log
│   ├── error.log                          ← Fehler-Protokoll
│   └── access.log                         ← Login / Zugriffs-Log
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

## 5. shared/logger.py — Logging-System (NEU v8.4)

### Architektur: 3 Log-Kanäle

```
logs/app.log      ← INFO + WARNING: alle App-Events (Starts, Berechnungen, Downloads)
logs/error.log    ← ERROR + CRITICAL: Exceptions, Tracebacks, Fehlerzustände
logs/access.log   ← INFO: Logins, Logouts, Seitenaufrufe, Ticker-Anfragen
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
        maxBytes=5 * 1024 * 1024,  # 5 MB pro Datei
        backupCount=5               # app.log, app.log.1, ..., app.log.5
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

app_logger.addHandler(_make_handler("app.log", logging.INFO))
error_logger.addHandler(_make_handler("error.log", logging.ERROR))
access_logger.addHandler(_make_handler("access.log", logging.INFO))
```

### Verwendung in allen Modulen
```python
from shared.logger import app_logger, error_logger, access_logger

# App-Events
app_logger.info(f"Download gestartet: {ticker}")
app_logger.warning(f"Yahoo Rate-Limit erreicht, Stooq-Fallback aktiv")

# Fehler (immer mit exc_info=True für Traceback)
try:
    df = download_data(ticker)
except Exception as e:
    error_logger.error(f"Download fehlgeschlagen: {ticker}", exc_info=True)

# Zugriffs-Events
access_logger.info(f"LOGIN | user={email} | ip={ip} | status=success")
access_logger.info(f"PAGE  | user={email} | page=Yearly_Seasonals | ticker={ticker}")
access_logger.info(f"LOGOUT| user={email}")
```

### Log-Rotation
- Jede Datei max. 5 MB, dann wird rotiert (5 Backups = max. 30 MB pro Kanal)
- Auf Streamlit Cloud: Logs in Supabase-Tabelle `app_logs` spiegeln (kein persistentes Filesystem)

### NICHT tun
- ❌ `print()` für Debugging verwenden — immer `app_logger.debug()` / `error_logger.error()`
- ❌ Passwörter, API-Keys oder Nutzerdaten in Logs schreiben
- ❌ Log-Dateien ins Git-Repo committen (`.gitignore` eintragen)

---

## 6. shared/supabase_client.py — Datenbank (NEU v8.4)

### Warum Supabase
- PostgreSQL-basiert, DSGVO-konform (EU-Server wählbar), kostenloser Free Tier (500 MB)
- Visuelles Dashboard — Tabellen wie Excel einsehbar
- Eingebaute Auth (User-Management ohne eigenen Code)
- Realtime-Subscriptions für spätere Live-Features

### Tabellen-Schema

```sql
-- Kursdaten (Primärquelle)
CREATE TABLE prices (
    id          BIGSERIAL PRIMARY KEY,
    ticker      TEXT NOT NULL,
    date        DATE NOT NULL,
    open        FLOAT,
    high        FLOAT,
    low         FLOAT,
    close       FLOAT NOT NULL,
    volume      BIGINT,
    source      TEXT DEFAULT 'yahoo',   -- 'yahoo' | 'stooq'
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(ticker, date)
);

-- Vorberechnete Saisonalität (für schnelle Abfragen im Frontend)
CREATE TABLE seasonality (
    id          BIGSERIAL PRIMARY KEY,
    ticker      TEXT NOT NULL,
    day_of_year INT NOT NULL,           -- 1–365
    avg_return  FLOAT,                  -- Durchschnittliche kum. Rendite
    std_dev     FLOAT,                  -- Standardabweichung
    win_rate    FLOAT,                  -- % positive Jahre
    n_years     INT,                    -- Anzahl ausgewertete Jahre
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(ticker, day_of_year)
);

-- User-Zugriffe (Logging in DB statt nur File)
CREATE TABLE app_logs (
    id          BIGSERIAL PRIMARY KEY,
    level       TEXT,                   -- INFO | WARNING | ERROR
    channel     TEXT,                   -- app | error | access
    message     TEXT,
    user_email  TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

### Connector
```python
# shared/supabase_client.py
from supabase import create_client
import os

SUPABASE_URL = os.environ["SUPABASE_URL"]   # in Streamlit Secrets hinterlegen
SUPABASE_KEY = os.environ["SUPABASE_KEY"]   # Service Role Key (nicht anon!)

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

# Streamlit Cloud: Settings → Secrets → gleiche Keys eintragen
```

---

## 7. shared/download_manager.py — Download-Manager (NEU v8.4)

### Aufgabe
Zentraler Manager für alle Daten-Downloads. Ersetzt ad-hoc-Downloads in den Pages.
Koordiniert Yahoo Finance, Stooq-Fallback, Caching und Supabase-Synchronisation.

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

# Einzelner Ticker (mit Cache-Prüfung + DB-Fallback)
df = dm.get(ticker="SPY", start="1993-01-01")

# Batch-Download (für Nacht-Job: 1.000 Ticker)
results = dm.batch(tickers=["SPY", "QQQ", ...], workers=4)

# Status abfragen
status = dm.status()  # {"queued": 42, "done": 958, "failed": 0}
```

### Priorisierung
```
Priorität 1: Ticker die gerade im Frontend angefragt werden (Live)
Priorität 2: Top-100 Ticker (täglich aktualisieren)
Priorität 3: Alle weiteren 900 Ticker (wöchentlich)
```

### Nacht-Job (GitHub Actions)
```yaml
# .github/workflows/nightly_update.yml
name: Nightly Data Update
on:
  schedule:
    - cron: '0 20 * * 1-5'   # Mo–Fr um 20:00 UTC (22:00 MEZ)
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

## 8. shared/email_brevo.py — E-Mail (NEU v8.4)

### Warum Brevo
- Kostenlos bis 300 E-Mails/Tag (reicht für Phase 1)
- DSGVO-konform, EU-Server, Double-Opt-In integriert
- Transaktionale E-Mails (Willkommen, Passwort-Reset) + Newsletter

### Use Cases
| Trigger | E-Mail |
|---------|--------|
| Neuer User registriert | Willkommen + Aktivierungslink |
| Passwort vergessen | Reset-Link (Ablauf 1h) |
| Premium-Abo gebucht | Bestätigung + Rechnung |
| Wöchentlicher Newsletter | Top-Saisonalmuster der Woche |
| Fehler im System | Admin-Alert bei CRITICAL-Errors |

### API
```python
# shared/email_brevo.py
import requests, os

BREVO_API_KEY = os.environ["BREVO_API_KEY"]
SENDER = {"name": "SeasonalEdge", "email": "noreply@seasonaledge.app"}

def send_transactional(to_email: str, template_id: int, params: dict):
    """Sendet eine Brevo-Template-E-Mail."""
    resp = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={"api-key": BREVO_API_KEY, "Content-Type": "application/json"},
        json={
            "sender": SENDER,
            "to": [{"email": to_email}],
            "templateId": template_id,
            "params": params
        }
    )
    resp.raise_for_status()
    app_logger.info(f"E-Mail gesendet: template={template_id} to={to_email}")

# Beispiele:
# send_transactional(email, template_id=1, params={"name": "Heiko", "link": url})
# send_transactional(email, template_id=2, params={"reset_link": url})
```

### Template-IDs (in Brevo Dashboard erstellen)
```
ID 1: Willkommen / E-Mail-Bestätigung
ID 2: Passwort zurücksetzen
ID 3: Premium-Buchungsbestätigung
ID 4: Wöchentlicher Newsletter
ID 5: Admin-Alert (Systemfehler)
```

---

## 9. shared/charts.py — Plotly Custom Theme (v8.4)

### Design-Philosophie
Einheitliches dunkles Theme über alle Charts. Eine Funktion — ein Aufruf pro Chart.

### Farb-Palette
```python
SE_COLORS = {
    "bg":         "#080c12",    # Chart-Hintergrund
    "surface":    "#0e1520",    # Panel-Hintergrund
    "grid":       "#1c2636",    # Gridlines
    "accent":     "#00e5c3",    # Primärakzent (Teal)
    "accent2":    "#ff6b35",    # Sekundärakzent (Orange)
    "text":       "#e8edf5",    # Haupttext
    "muted":      "#4a5568",    # Nebentext / Achsen
    "positive":   "#00e5c3",    # Positive Renditen
    "negative":   "#ff4757",    # Negative Renditen
    "current_yr": "rgba(232,164,37,0.90)",  # Aktuelles Jahr
    "other_yr":   "rgba(200,220,255,0.40)", # Andere Jahre
}
```

### Drop-in Funktion
```python
# shared/charts.py
def apply_se_theme(fig, title: str = "", height: int = 420) -> go.Figure:
    """Wendet das SeasonalEdge-Theme auf jeden Plotly-Chart an. 1 Zeile pro Chart."""
    fig.update_layout(
        paper_bgcolor=SE_COLORS["bg"],
        plot_bgcolor=SE_COLORS["bg"],
        height=height,
        font=dict(family="DM Mono, monospace", color=SE_COLORS["muted"], size=11),
        title=dict(text=title, font=dict(color=SE_COLORS["text"], size=14), x=0.01),
        margin=dict(t=40, r=20, b=40, l=52),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=SE_COLORS["surface"],
            bordercolor=SE_COLORS["accent"],
            font=dict(color=SE_COLORS["text"], size=12)
        ),
        legend=dict(
            bgcolor="rgba(14,21,32,0.8)",
            bordercolor=SE_COLORS["grid"],
            borderwidth=1,
            font=dict(color=SE_COLORS["muted"], size=10)
        ),
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

---

## 10. shared/ai_models.py — KI-Modelle (NEU v8.4)

### Übersicht: Empfohlene KI-Modelle für SeasonalEdge

| Modell | Methode | Use Case | Komplexität | Priorität |
|--------|---------|----------|-------------|-----------|
| **DTW Pattern Matching** | Dynamic Time Warping | Ähnliche Historische Jahre finden | Niedrig | ✅ Phase 1 |
| **Prophet** | Facebook Time Series | Saisonale Prognose | Niedrig | ✅ Phase 1 |
| **Isolation Forest** | Anomalie-Erkennung | Ausreißer-Jahre identifizieren | Niedrig | ✅ Phase 1 |
| **Claude API** | LLM (Anthropic) | Natural Language Markt-Kommentar | Mittel | ✅ Phase 1 |
| **LSTM** | Deep Learning | Mustererkennung Zeitreihen | Hoch | ⏳ Phase 2 |
| **XGBoost** | Gradient Boosting | Rendite-Vorhersage (multi-feature) | Mittel | ⏳ Phase 2 |
| **Transformer** | Attention-Modell | Komplexe Mustererkennung | Sehr hoch | ⏳ Phase 3 |

### Detailbeschreibung

#### DTW Pattern Matching (bereits in TruePath — ausbauen)
```python
# Findet die 3 Jahre die dem aktuellen Kursmuster am ähnlichsten sind
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean

def find_similar_years(current_pattern, all_years_data, top_n=3):
    scores = {}
    for year, pattern in all_years_data.items():
        dist, _ = fastdtw(current_pattern, pattern, dist=euclidean)
        scores[year] = dist
    return sorted(scores.items(), key=lambda x: x[1])[:top_n]
# Output: [(2019, 0.82), (2015, 0.79), (2011, 0.71)]
```

#### Prophet (Facebook) — Saisonale Prognose
```python
# Prognostiziert die nächsten 60 Tage basierend auf saisonalen Mustern
from prophet import Prophet

def forecast_seasonal(df_prices, periods=60):
    m = Prophet(yearly_seasonality=True, weekly_seasonality=False)
    m.fit(df_prices.rename(columns={"Date": "ds", "Close": "y"}))
    future = m.make_future_dataframe(periods=periods)
    forecast = m.predict(future)
    return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(periods)
```

#### Isolation Forest — Ausreißer-Erkennung
```python
# Erkennt Jahre die stark vom typischen Muster abweichen (z.B. 2008, 2020)
from sklearn.ensemble import IsolationForest

def detect_outlier_years(year_returns_matrix):
    clf = IsolationForest(contamination=0.1, random_state=42)
    labels = clf.fit_predict(year_returns_matrix)
    outlier_years = [y for y, l in zip(years, labels) if l == -1]
    return outlier_years
# Verwendung: Outlier optional aus Ø-Berechnung ausschließen
```

#### Claude API — Natural Language Kommentar
```python
# Generiert einen kurzen KI-Kommentar zum aktuellen Saisonalmuster
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

#### LSTM — Zeitreihen-Deep-Learning (Phase 2)
```python
# Erkennt komplexe nicht-lineare Muster in Kurszeitreihen
# Benötigt: tensorflow oder pytorch
# Input: Letzte 60 Handelstage
# Output: Wahrscheinlichkeit für positive Rendite nächste 20 Tage
# Training: Einmalig offline, Modell als .h5 gespeichert
```

#### XGBoost — Multi-Feature Prognose (Phase 2)
```python
# Kombiniert saisonale Features mit technischen Indikatoren
# Features: day_of_year, month, presidential_cycle_year,
#           rsi_14, sma_50_distance, vix_level, yield_spread
# Output: Rendite-Erwartung + Confidence Score
```

### KI-Ausgabe im Frontend

**TruePath Page (Page 8) — Erweiterung:**
```
🤖 AI Pattern Match — SPY
─────────────────────────────────────────
Ähnlichste Jahre:    2019 (87%) · 2015 (83%) · 2011 (79%)
Ø Folgerendite:      +4.2% (nächste 60 Tage)
Confidence:          ████████░░ 78%
Ausreißer erkannt:   2020 ausgeschlossen (COVID-Anomalie)
─────────────────────────────────────────
📝 KI-Kommentar: "Das aktuelle Muster zeigt eine typische
Frühjahrsstärke mit überdurchschnittlicher Win-Rate im
April/Mai-Bereich. Ähnliche Konstellationen 2019 und 2015
endeten mit positiven Renditen bis zum Sommer."
```

---

## 11. shared/split_slider.py — v7 (3-Layer-Architektur)

### Kernproblem gelöst
Plotly rendert Achsenbeschriftungen als SVG *innerhalb* des Chart-Divs.
CSS `clip-path` schneidet daher Achsen mit weg.

### Lösung
```
Layer 1 (layer-axes)  z-index:1  KEIN clip-path  → Achsen IMMER sichtbar
Layer 2 (layer-b)     z-index:2  clip LINKS       → Ø Saisonal-Kurve
Layer 3 (layer-a)     z-index:3  clip RECHTS      → Spaghetti-Einzeljahre
```
Alle 3 Charts teilen **exakt dasselbe Layout** → identische Achsenpositionen.

### API
```python
from shared.split_slider import render_split_slider
render_split_slider(df, height=520, info="77 Jahre · Live + Hist.")
# df muss Spalten haben: year, trading_day, cum_return_pct
```

### Design-Regeln
- Kein Konfidenzband (fill: toself/tozeroy deaktiviert)
- Zero-Alignment: beide 0-Linien auf gleicher Höhe
- Links = Ø Saisonal (blau #4d9fff), Rechts = Einzeljahre (weiß-blau)
- Aktuelles Jahr: orange rgba(232,164,37,0.90), width=2.5
- Andere Jahre: rgba(200,220,255,0.40), width=1.0

---

## 12. shared/dj_data.py — v3

```python
from shared.dj_data import load_dj_data
df, source = load_dj_data(project_dir)
# source: "live+synthetic" | "synthetic"
# df: year, trading_day, cum_return_pct
# Kein @st.cache_data! (friert Exceptions ein)
```

---

## 13. shared/distribution_charts.py — Funktionsübersicht

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

## 14. Stooq-Fallback (yahoo_downloader.py)
- `^DJI` → `^dji` (Stooq): Daten ab ~1928
- `^GSPC` → `^spx` (Stooq): Daten ab ~1928
- `^GDAXI` / `^DAX` → `^dax` (Stooq): Daten ab ~1959

---

## 15. Architektur-Prinzipien

### Logik vs. UI trennen
- Neue Berechnungen → `shared/`
- UI-Rendering → `pages/`
- Kein Copy-Paste von Berechnungslogik zwischen Pages

### Datenfluss (v8.4)
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

### Import-Header (CRITICAL — sys.path Fix)
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

## 16. Kritische Bugs (dokumentiert)

| Bug | Fix |
|-----|-----|
| Yahoo `period="max"` → nur monatliche Daten | `period1=0&period2=now` |
| Yahoo `Open` nicht split-adjustiert | IMMER `Close.iloc[0]` als Basis |
| yfinance nicht verwenden | `from shared.yahoo_downloader import download_data` |
| Plotly `titlefont` deprecated | `title=dict(text=..., font=dict(...))` |
| Plotly `add_vline` mit String-Labels crasht | `add_shape` + `add_annotation` |
| Plotly `fillcolor` Hex→rgba via String-Replace | `int(hex[1:3], 16)` manuell |
| Plotly Typed Arrays (v2.x) | `json.dumps()` + `Plotly.newPlot` manuell |
| Doppelter `@st.cache_data` friert Daten ein | Cache nur in `yahoo_downloader.py` |
| Streamlit URL-Konflikt bei Rename | Alte Datei mit `Remove-Item` löschen |
| `df.index[0].strftime()` → AttributeError | `df['Date'].iloc[0].strftime()` |
| Split-Slider Achsen werden weggeclippt | 3-Layer-Architektur (layer-axes ohne clip) |
| Clip-Path Richtung falsch | Layer B: `inset(0 right% 0 0)`, A: `inset(0 0 0 pct%)` |
| Logs in Git committet | `logs/` in `.gitignore` eintragen |
| API-Keys im Code | Immer `os.environ["KEY"]` + Streamlit Secrets |

---

## 17. .gitignore (Pflicht-Einträge)

```gitignore
# Secrets & Keys
.env
.streamlit/secrets.toml

# Logs (niemals in Git!)
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

## 18. Roadmap

### Kurzfristig (nächste Sessions)
- [ ] `shared/logger.py` anlegen + in alle Module einbinden
- [ ] `shared/supabase_client.py` anlegen + Tabellen-Schema deployen
- [ ] `shared/download_manager.py` anlegen (ersetzt ad-hoc Downloads)
- [ ] `shared/charts.py` → `apply_se_theme()` Drop-in ergänzen
- [ ] `shared/ai_models.py` anlegen (DTW + Prophet + Claude API)
- [ ] `shared/email_brevo.py` anlegen
- [ ] `logs/` Verzeichnis + `.gitignore` anlegen
- [ ] `use_container_width` → `width='stretch'` (Deadline Ende 2025)
- [ ] `seasonal_app.py` Zeile 243+: `df.index[...]` → `df['Date'].iloc[...]`
- [ ] Split-Slider: Ticker-Auswahl (aktuell nur ^DJI)
- [ ] TDOM Backtesting Page
- [ ] Outlier Management (Winsorize 3σ, Exclude Years Widget)

### Phase 1: Deployment (Streamlit)
- [ ] GitHub-Repo anlegen
- [ ] Streamlit Cloud Deployment
- [ ] Supabase PostgreSQL + User-Auth
- [ ] Nightly GitHub Action (Download-Manager Batch)
- [ ] Stripe Freemium/Abo-Integration
- [ ] Brevo-Newsletter-Anbindung
- [ ] Domain (seasonaledge.app — INWX.de, ~15 EUR/Jahr)

### Phase 2: Next.js Landingpage (SEO)
- [ ] Next.js 14+ Setup unter `C:\Dev\SeasonalEdge\frontend\`
- [ ] TailwindCSS + shadcn/ui Dark Mode
- [ ] Metadata-API, sitemap.xml, robots.txt
- [ ] DSGVO: react-cookie-consent
- [ ] Brevo-Formular (server-side)
- [ ] Google Lighthouse Score > 90
- [ ] LSTM + XGBoost Modelle trainieren

### Phase 3: FastAPI-Backend
- [ ] `C:\Dev\SeasonalEdge\backend\` anlegen
- [ ] Python-Berechnungslogik aus shared/ portieren
- [ ] Pydantic-Modelle für alle Responses
- [ ] Highcharts-kompatibles JSON-Format
- [ ] pytest für alle Services
- [ ] CORS für Next.js Frontend

### Phase 4: Next.js Dashboard + Highcharts (ab ~500 Abo)
- [ ] Highcharts 11+ (`highcharts-react-official`, SSR)
- [ ] Supabase Auth mit MFA + RBAC
- [ ] shadcn/ui Dashboard
- [ ] Stripe Webhooks
- [ ] Sentry + Monitoring
- [ ] Docker-Deployment (Vercel + Railway)
- [ ] Transformer-Modell für komplexe Mustererkennung

---

## 19. Technischer Stack

### Aktuell (Phase 1)
- **Frontend:** Python, Streamlit, Plotly (Custom Theme v8.4)
- **Daten:** pandas, numpy, scipy, yahoo_downloader (HTTP), Stooq
- **DB:** Supabase PostgreSQL (NEU v8.4)
- **Logging:** Python logging + RotatingFileHandler (NEU v8.4)
- **E-Mail:** Brevo API (NEU v8.4)
- **KI:** fastdtw, Prophet, sklearn, Claude API (NEU v8.4)
- **Umgebung:** Windows, PowerShell, Python Virtual Environment
- **Alpha Vantage API Key:** `SEVZUPQC0UL2O4RF` (Vollhistorie = Premium)

### Ziel (Phase 4)
- **Frontend:** Next.js 14+, React 18, TailwindCSS, shadcn/ui, Highcharts 11+
- **Backend:** FastAPI, Python 3.11+, Pydantic, SQLAlchemy, Supabase
- **KI:** LSTM, XGBoost, Transformer, Claude API
- **Services:** Stripe, Brevo, GitHub Actions, Sentry, Docker
- **Deploy:** Vercel (Next.js), Railway/Fly.io (FastAPI), Supabase (DB/Auth)

### Highcharts Lizenz-Hinweis
- Community Edition: kostenlos für nicht-kommerzielle Nutzung
- Commercial: ~€400/Jahr für 1 Entwickler
- **Empfehlung:** Erst kaufen wenn >500 zahlende Abonnenten (ROI gesichert)

---

**Skill Maintainer:** Claude + Heiko
**Last Updated:** 2026-03-17
**Version:** 8.4

**Changelog:**
- v8.4: Logging-System (logger.py, 3 Kanäle, RotatingFileHandler). Supabase-Schema (prices, seasonality, app_logs). Download-Manager (TickerQueue, RateLimiter, Nacht-Job). Plotly Custom Theme Drop-in (apply_se_theme). Brevo E-Mail-Integration (5 Templates). KI-Modelle dokumentiert (DTW, Prophet, Isolation Forest, Claude API, LSTM, XGBoost, Transformer). .gitignore Pflichteinträge.
- v8.3: Split-Slider v7 (3-Layer-Architektur). dj_data.py v3. Home-Page v1. Umstellungsplan Next.js+FastAPI+Highcharts.
- v8.2: calculations_decade.py + distribution_charts.py. Intra_Decade Page. Stooq-Fallback. Box-Plot + Heatmap.
- v8.0: Feiertags-Architektur, Yahoo Finance Bug-Fixes.
- v7.0: yahoo_downloader.py (direkter HTTP ohne yfinance).
- v6.0: shared/strategies/ Untermodul.
- v5.0: Weekday, Monthly, Zentralbanken, Mondphasen, TruePath KI.
- v4.0: Multipage-Architektur, Turn-of-Month, Feiertags-Effekt.

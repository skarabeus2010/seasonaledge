# Architektur — SeasonalEdge

## Datenfluss

```
download_manager.py  ←→  yahoo_downloader.py  ←→  Stooq-Fallback
        ↓                          ↓
  supabase_client.py          logger.py (app.log)
        ↓                          ↓
  cache_manager.py ←→ market_calendar.py ←→ nightly_refresh.py
        ↓
    data.py (Wrapper, kein Cache!)
        ↓
  calculations.py / calculations_decade.py
        ↓                          ↓
  distribution_charts.py      ai_models.py (DTW, Prophet, IF, Claude)
        ↓                          ↓
  outlier_manager.py      KI-Summary + Anomalie-Heatmap
        ↓                          ↓
     pages/*.py (UI)         apply_se_theme()
```

## Yahoo Finance & Stooq

yfinance ist entfernt. Immer: `from shared.yahoo_downloader import download_data`

Yahoo `period="max"` liefert nur monatliche Daten → `period1=0&period2=now` verwenden.
Yahoo `Open` nicht split-adjustiert → IMMER `Close.iloc[0]` als Basis.

### Stooq-Fallback (Langzeitdaten)
| Yahoo Ticker | Stooq Ticker | Daten ab |
|---|---|---|
| `^DJI` | `^dji` | ~1928 |
| `^GSPC` | `^spx` | ~1928 |
| `^GDAXI` | `^dax` | ~1959 |

## Supabase Tabellen-Schema

```sql
CREATE TABLE prices (
    id BIGSERIAL PRIMARY KEY, ticker TEXT NOT NULL, date DATE NOT NULL,
    open FLOAT, high FLOAT, low FLOAT, close FLOAT NOT NULL,
    volume BIGINT, source TEXT DEFAULT 'yahoo',
    updated_at TIMESTAMPTZ DEFAULT NOW(), UNIQUE(ticker, date)
);

CREATE TABLE seasonality (
    id BIGSERIAL PRIMARY KEY, ticker TEXT NOT NULL, day_of_year INT NOT NULL,
    avg_return FLOAT, std_dev FLOAT, win_rate FLOAT, n_years INT,
    updated_at TIMESTAMPTZ DEFAULT NOW(), UNIQUE(ticker, day_of_year)
);

CREATE TABLE app_logs (
    id BIGSERIAL PRIMARY KEY, level TEXT, channel TEXT,
    message TEXT, user_email TEXT, created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE subscribers (
    id BIGSERIAL PRIMARY KEY, email TEXT NOT NULL UNIQUE,
    status TEXT DEFAULT 'active' CHECK (status IN ('active','unsubscribed','bounced','complained')),
    source TEXT DEFAULT 'website', subscribed_at TIMESTAMPTZ DEFAULT NOW(),
    unsubscribed_at TIMESTAMPTZ, no_emails BOOLEAN DEFAULT FALSE,
    brevo_synced BOOLEAN DEFAULT FALSE, ip_address TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

-- Market Calendar + Computed Values Cache (scripts/create_market_tables.sql)
CREATE TABLE market_events (
    id BIGSERIAL PRIMARY KEY, event_date DATE NOT NULL,
    event_type TEXT NOT NULL, event_name TEXT NOT NULL,
    exchange TEXT NOT NULL, subtype TEXT, meta JSONB DEFAULT '{}',
    year INT NOT NULL, updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(event_date, event_type, event_name, exchange)
);

CREATE TABLE monthly_stats (
    id BIGSERIAL PRIMARY KEY, ticker TEXT NOT NULL,
    month INT NOT NULL, years_back INT NOT NULL,
    avg_return FLOAT, median_return FLOAT, win_rate FLOAT,
    std_dev FLOAT, max_gain FLOAT, max_loss FLOAT, total_years INT,
    updated_at TIMESTAMPTZ DEFAULT NOW(), UNIQUE(ticker, month, years_back)
);

CREATE TABLE ki_scores (
    id BIGSERIAL PRIMARY KEY, ticker TEXT NOT NULL,
    score FLOAT NOT NULL, signal TEXT NOT NULL,
    dtw_score FLOAT, prophet_score FLOAT, win_rate_score FLOAT, tracking_score FLOAT,
    details JSONB DEFAULT '{}', computed_date DATE NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(), UNIQUE(ticker, computed_date)
);

CREATE TABLE scanner_results (
    id BIGSERIAL PRIMARY KEY, ticker TEXT NOT NULL,
    score FLOAT NOT NULL, signal TEXT NOT NULL,
    win_rate FLOAT, avg_return FLOAT, deviation FLOAT,
    scan_date DATE NOT NULL, updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(ticker, scan_date)
);

CREATE TABLE spot_vol_beta (
    id BIGSERIAL PRIMARY KEY, event_date DATE NOT NULL,
    spx_close FLOAT, vix_close FLOAT,
    spx_ret FLOAT, vix_chg FLOAT,
    daily_beta FLOAT, rolling_beta_60 FLOAT,
    updated_at TIMESTAMPTZ DEFAULT NOW(), UNIQUE(event_date)
);

CREATE TABLE tdom_stats (
    id BIGSERIAL PRIMARY KEY, ticker TEXT NOT NULL,
    tdom INT NOT NULL, direction TEXT NOT NULL, strategy TEXT NOT NULL,
    avg_return FLOAT, median_return FLOAT, win_rate FLOAT,
    std_dev FLOAT, count INT, updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(ticker, tdom, direction, strategy)
);
```

Secrets in `.streamlit/secrets.toml` → `os.environ["SUPABASE_URL"]` / `os.environ["SUPABASE_KEY"]`

### Subscriber-Management (supabase_client.py)
```python
subscribe_email(email, source, ip_address)  # Neu anlegen / reaktivieren
unsubscribe_email(email)                     # no_emails=True, status='unsubscribed'
get_subscriber(email)                        # Einzelnen Subscriber holen
get_active_subscribers()                     # Alle aktiven (für Newsletter)
count_subscribers()                          # {"active": N, "total": N, "unsubscribed": N}
```

## Logger (shared/logger.py)

3 Kanäle mit RotatingFileHandler (5 MB, 5 Backups):
- `logs/app.log` — INFO: App-Events, Downloads, Berechnungen
- `logs/error.log` — ERROR: Exceptions + Tracebacks
- `logs/access.log` — INFO: Logins, Seitenaufrufe, Ticker-Anfragen

```python
from shared.logger import app_logger, error_logger, access_logger
app_logger.info(f"Download: {ticker}")
error_logger.error(f"Fehler: {ticker}", exc_info=True)
```

## Download-Manager (shared/download_manager.py)

Architektur: TickerQueue + RateLimiter + CacheLayer + DBSync

```python
from shared.download_manager import DownloadManager
dm = DownloadManager(project_dir)
df = dm.get(ticker="SPY", start="1993-01-01")
results = dm.batch(tickers=["SPY", "QQQ"], workers=4)
```

Prioritäten: 1=Live-Frontend, 2=Top-100 täglich, 3=Rest wöchentlich.

Nacht-Job: GitHub Actions Mo–Fr 20:00 UTC → `python -m shared.download_manager --batch-all`

## E-Mail (shared/email_brevo.py)

Template-IDs: 1=Willkommen, 2=Passwort-Reset, 3=Premium-Bestätigung, 4=Newsletter, 5=Admin-Alert

## Feature-Patterns

### Smoothing
```python
avg_smooth = pd.Series(avg_cumulative).rolling(5, center=True, min_periods=1).mean().tolist()
```

### Presidential Cycle
```python
cycle_position = (year - 2024) % 4  # 0=Election, 1=Post, 2=Midterm, 3=Pre
```

### TDoM (Trading Day of Month)
Forward: TDoM 1 = erster Handelstag. Backward: TDoM -1 = letzter Handelstag.

## TDoM Analyse (shared/tdom_analysis.py)

3 Strategien: Intraday (Open→Close), Overnight (Open→NextOpen), Close-to-Close.

```python
from shared.tdom_analysis import build_tdom_stats, calc_tdom_range_return

# Statistiken pro TDoM
stats = build_tdom_stats(df, "open_to_close", "forward", selected_months=[1,2,3])

# Multi-Day Range: Kaufe TDoM 1, verkaufe TDoM -1
range_df = calc_tdom_range_return(df, entry_tdom=1, exit_tdom=-1, entry_price="Open", exit_price="Close")
```

## dj_data.py

```python
from shared.dj_data import load_dj_data
df, source = load_dj_data(project_dir)  # KEIN @st.cache_data!
# df-Spalten: year, trading_day, cum_return_pct
```

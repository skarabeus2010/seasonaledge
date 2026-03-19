# Architektur — SeasonalEdge

## Datenfluss

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
```

Secrets in `.streamlit/secrets.toml` → `os.environ["SUPABASE_URL"]` / `os.environ["SUPABASE_KEY"]`

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

## dj_data.py

```python
from shared.dj_data import load_dj_data
df, source = load_dj_data(project_dir)  # KEIN @st.cache_data!
# df-Spalten: year, trading_day, cum_return_pct
```

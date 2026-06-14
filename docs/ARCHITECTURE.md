# Architektur — SeasonAlpha

> Stand: 2026-06-13

## Frontend-Architektur (wichtig)

**Das gesamte Frontend = statische HTML-App unter `landing/`** (nginx serviert direkt).
Die Charts/Analysen werden **client-seitig in JS** gerechnet (`landing/js/*-compute.js`,
ApexCharts), gespeist aus vorberechnetem JSON (`landing/data/`) + direkten
Supabase-Reads (anon). EN-Version statisch vorgerendert nach `landing/en/`.

**Streamlit wird produktseitig NICHT (mehr) genutzt** — `landing/` verlinkt nirgends auf
`/app/`. `seasonal_app.py` + `pages/*.py` existieren nur noch, weil der `streamlit run`-
Prozess der **Haupt-/Keep-alive-Prozess des `app`-Containers** ist (hält ihn am Leben,
damit die Crons via `docker exec` reinkommen). Der nginx-`/app/`-Proxy ist vestigial.

## Daten-Pipeline (Backend)

```
yahoo_downloader.py (+ Stooq-Fallback, einziger Cache)
        ↓  download_data / preprocess (log_return, TDOM/TDOY)
supabase_client.py  →  prices  (Quelle der Wahrheit: shared/symbols.py = 324 Ticker)
        ↓
nightly_refresh.py (Mo–Fr) — Phasen A..Z: market_events, monthly_stats, ki_scores,
   tdom/tdoy_stats, Health-Check (Gap-Fill), regime_scores, spot_vol_beta, refresh_log,
   Weekly-Newsletter, Polymarket, Brier
intraday_refresh.py (stündlich) — nur prices, gruppen-/zeitfenster-gesteuert
        ↓
abgeleitete Tabellen  →  Frontend (landing/js, client-seitige Berechnung + Supabase-Reads)
```

⚠️ ML-Pipeline (DTW/Prophet/NeuralProphet/Chronos) wurde KW16 stillgelegt; `ki_score.py`
= aktuelle Engine (4 Sub-Scores → 0–10, auch client-seitig in `landing/js/ki-*`).

## Yahoo Finance & Stooq

yfinance ist entfernt. Immer: `from shared.yahoo_downloader import download_data`

Yahoo `period="max"` liefert nur monatliche Daten → `period1=0&period2=now` verwenden.
Yahoo `Open` wird jetzt in `yahoo_downloader.py` automatisch split-adjustiert (adj_factor = adjclose/close auf Open/High/Low angewendet).

### Stooq-Fallback (Langzeitdaten)

Direkt in `yahoo_downloader.py` integriert. Automatisch aktiv wenn Yahoo < 40 Jahre liefert.

| Yahoo Ticker | Stooq Ticker | Daten ab |
|---|---|---|
| `^DJI` | `^dji` | ~1896 (131 Jahre) |
| `^GSPC` | `^spx` | ~1928 |
| `^GDAXI` | `^dax` | ~1959 |
| `^FTSE` | `^ukx` | ~1984 |
| `^N225` | `^nkx` | ~1965 |
| `^FCHI` | `^cac` | ~1990 |
| `^STOXX50E` | `^sx5e` | ~1987 |
| `^SSMI` | `^ssmi` | ~1990 |
| `^HSI` | `^hsi` | ~1986 |
| `^KS11` | `^kospi` | ~1997 |

## Supabase

| Eigenschaft | Wert |
|-------------|------|
| Projekt | **SeasonAlpha** |
| Projekt-ID | `dkrebzobcwxyagximuxy` |
| URL | `https://dkrebzobcwxyagximuxy.supabase.co` |
| Plan | Free |
| Region | EU (Frankfurt) |
| VPS `.env` | `SUPABASE_URL` + `SUPABASE_KEY` (anon/public) |

### Tabellen-Schema

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

_(Die SQL oben zeigt nur die Kern-Tabellen. Vollständige DDL: `scripts/create_*.sql`.)_

### Alle Tabellen (Übersicht, Stand 2026-06-13)

| Tabelle | Key | Zweck |
|---------|-----|-------|
| **prices** | (ticker,date) | OHLCV + `log_return` + `tdom`/`tdoy`. Quelle der Wahrheit = `symbols.py` (324) |
| **tickers** | ticker | Stammdaten-Registry (Spiegel von `symbols.py`) |
| **historical_cpi** | year | US-CPI Jahresmittel (Inflationsbereinigung) |
| seasonality | (ticker,doy) | ⚠️ leer/Legacy — Saisonalität wird client-seitig gerechnet |
| ki_scores | (ticker,computed_date) | ⚠️ dünn/Legacy — KI-Score ist client-seitig |
| monthly_stats | (ticker,month,years_back) | Monats-Saisonalität |
| scanner_results | (ticker,scan_date) | Full-Scanner (wöchentlich) |
| tdom_stats | (ticker,tdom,direction,strategy) | ~92 Zeilen/Ticker |
| tdoy_stats | (ticker,tdoy,direction,strategy) | ~1016 Zeilen/Ticker |
| regime_scores | (ticker,date) | Crash-Ampel (Isolation Forest); täglich nur SPY + Subset |
| spot_vol_beta | event_date | SPX vs VIX (nur SPX); Nightly-Phase E1b |
| market_events | (event_date,event_type,event_name,exchange) | Feiertage/OPEX/Zentralbank |
| central_bank_dates | (bank,date) | FOMC/EZB/BoE/BoJ |
| dividend_events | (ticker,ex_date) | Aktien — Ex-Dividenden |
| earnings_events | (ticker,report_date) | Aktien — Earnings |
| polymarket_markets / _prices | condition_id / (condition_id,ts) | Prognosemärkte (aktiv) |
| polymarket_resolved_markets / _prices | condition_id / (condition_id,ts) | Prognosemärkte (Archiv) |
| subscribers | email | Weekly Newsletter |
| daily_subscribers | email | Daily Morning Briefing |
| user_subscriptions | user_id | Premium-Tier / Stripe |
| user_watchlists | (user_id,ticker) | Cloud-Watchlist (RLS owner-only) |
| refresh_log | (run_date,run_type) | Cron-Monitoring (nightly/intraday/event_data/daily_newsletter/completeness) |
| app_logs | — | App-/Error-Logging |

RPC: **`distinct_price_tickers()`** — server-seitiger Loose-Index-Scan für den Orphan-Detektor (`SELECT DISTINCT ticker` timeoutet). DDL: `scripts/create_distinct_price_tickers_rpc.sql`.

Secrets in `.streamlit/secrets.toml` / `.env` → `os.environ["SUPABASE_URL"]` / `os.environ["SUPABASE_KEY"]`

### Subscriber-Management (supabase_client.py)
```python
subscribe_email(email, source, ip_address)  # Neu anlegen / reaktivieren
unsubscribe_email(email)                     # no_emails=True, status='unsubscribed'
get_subscriber(email)                        # Einzelnen Subscriber holen
get_active_subscribers()                     # Alle aktiven (für Newsletter)
count_subscribers()                          # {"active": N, "total": N, "unsubscribed": N}
```

## Shared Module (Uebersicht)

### Kern-Module

| Modul | Beschreibung |
|-------|-------------|
| `yahoo_downloader.py` | HTTP-Downloader + Stooq-Fallback + OHLC Split-Adjustierung (einziger Cache!) |
| `calculations.py` | Kern-Berechnungen (normalisierte Renditen, Saisonalitaet) |
| `charts.py` | Plotly Theme (`apply_se_theme`, `apply_se_heatmap_theme`) |
| `data.py` | Daten-Wrapper (kein Cache!) |
| `constants.py` | Globale Konstanten, Farbpaletten, Heatmap-Colorscales |
| `symbols.py` | **324 Ticker** in 12+ Kategorien (= einzige Quelle der Wahrheit; `get_all_tickers()`). Neuaufnahme NUR via `scripts/onboard_ticker.py`. Vollständigkeit: `scripts/check_db_completeness.py` (Orphan-/Stale-Tail-Erkennung) |

### KI & Analyse

| Modul | Beschreibung |
|-------|-------------|
| `ki_score.py` | KI Seasonal Score Engine (4 Sub-Scores → 0-10) — auch client-seitig |
| `ai_models.py` | ⚠️ Legacy (ML-Pipeline KW16 stillgelegt) |
| `anomaly_engine.py` | Anomalie-Radar, Crash-Ampel, TDoM-Anomalien, Muster-Brueche |
| `outlier_manager.py` | Outlier-Filter (IQR, Winsorize, Isolation Forest) |
| `significance_gauge.py` | Signifikanztest (t-Test, Cohen's d) + Radial Gauge |
| `tdom_analysis.py` / `tdoy_analysis.py` | TDoM/TDoY Berechnungen (3 Strategien, Ranges, Heatmap) |
| `spot_vol_beta.py` | Spot-Vol Beta (SPX vs VIX, Daily + Rolling) — Nightly Phase E1b |
| `backtest_engine.py` | Event-/Strategie-Backtest (Walk-Forward, Grid-Search, look-ahead-bias-frei) |
| `drawdown_analysis.py` / `streak_analysis.py` | Drawdown/Recovery + Streak-/Konsekutiv-Analyse |
| `shock_analysis.py` / `sector_rotation.py` | Shock Analyzer (Trigger→Target) + Sektor-Rotation |
| `brier_score.py` / `polymarket_data.py` | Polymarket: Brier-Kalibrierung + Daten-Fetch |
| `cpi_data.py` | CPI-Daten (BLS/FRED), Inflationsbereinigung |

### UI-Komponenten

| Modul | Beschreibung |
|-------|-------------|
| `footer.py` | Zentraler Footer (Impressum, Datenschutz, Risk Disclosure DE+EN) |
| `ticker_select.py` | Autocomplete Ticker-Auswahl (globaler Session State) |
| `percentile_bar.py` | Percentile-Ribbon (Micro-Gauge, Z-Score, Delta) |
| `split_slider.py` | 3-Layer Split-Slider (Einzeljahre vs. Durchschnitt) |
| `we_are_here.py` | Globaler "We are here!" Marker fuer Charts |
| `design.py` | CSS-Styles, Glasmorphismus |
| `assets.py` | SVG Hero, Icons |

### Infrastruktur

| Modul | Beschreibung |
|-------|-------------|
| `supabase_client.py` | DB-Connector + Subscriber + Market Events + Cache + Retry |
| `env_loader.py` | lädt `.env` in `os.environ` (Auto-Import via `shared/__init__.py`) |
| `exchange_holidays.py` / `holidays.py` / `nyse_holidays.py` | Börsen-Feiertagskalender, `is_trading_day()`, OPEX/VIXpiration |
| `fed_dates.py` / `central_banks.py` | Zentralbank-Termine (FOMC/EZB/…) |
| `cache_manager.py` | Computed Values Cache (DB → Fallback → Store) |
| `market_calendar.py` | Feiertage/OPEX/Zentralbank → Supabase sync |
| `daily_report.py` / `weekly_report.py` | Aggregation für Daily Briefing / Weekly Newsletter |
| `email_brevo.py` / `unsubscribe_token.py` | Brevo-Versand + HMAC-Unsubscribe-Token |
| `i18n.py` | Python-Side i18n (Streamlit) |
| `logger.py` | 3 Log-Kanaele (app/error/access) |
| `download_manager.py` | Batch-Downloads mit Queue + Rate Limiter |

## Logger (shared/logger.py)

3 Kanaele mit RotatingFileHandler (5 MB, 5 Backups):
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

Prioritaeten: 1=Live-Frontend, 2=Top-100 taeglich, 3=Rest woechentlich.

Nacht-Job: GitHub Actions Mo-Fr 20:00 UTC → `python -m shared.download_manager --batch-all`

## E-Mail (shared/email_brevo.py)

Template-IDs: 1=Willkommen, 2=Passwort-Reset, 3=Premium-Bestaetigung, 4=Newsletter, 5=Admin-Alert

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

## Signifikanztest (shared/significance_gauge.py)

T-Test + Cohen's d + Radial Gauge fuer statistische Signifikanz.

```python
from shared.significance_gauge import run_significance_test, render_significance_section

# Berechnung
results = run_significance_test(groups)  # groups = [{"label": "Mo", "values": [...]}]
# → [{"label": "Mo", "t_stat": 2.1, "p_value": 0.03, "cohens_d": 0.4, "relevance": 0.72, ...}]

# Rendering (als optionaler Expander)
render_significance_section(results, expander_title="Statistische Signifikanz", cols_per_row=4)
```

Integriert in: Wochentage, Monatswechsel, Mondphasen, Monatszyklus (Two-Week).

## Percentile Bar (shared/percentile_bar.py)

Kompakte Stat-Ribbon mit Micro-Gauge, Percentile, Z-Score.

```python
from shared.percentile_bar import render_percentile_bar

render_percentile_bar(
    current_value=1.2,
    hist_values=[0.5, 0.8, 1.1, 1.5, 2.0],
    label="Monatsrendite",
    value_fmt="+.2f", suffix="%"
)
```

## Footer (shared/footer.py)

Zentraler Footer fuer alle Pages mit Links zu Impressum, Datenschutz und Risk Disclosure (DE + EN).

```python
from shared.footer import render_footer
render_footer()  # Am Ende jeder Page aufrufen
```

## Ticker-Auswahl (shared/ticker_select.py)

Autocomplete Sidebar-Widget mit globalem Session State.

```python
from shared.ticker_select import ticker_select
ticker = ticker_select(key="page_ticker")  # → "SPY", "AAPL", "RHM.DE" etc.
```

## Indikator-Filter (shared/indicators.py + indicator_filter_ui.py)

6 technische Indikatoren als Berechnungs-Filter. Nur Tage mit erfuellter Bedingung
fliessen in die Saisonalitaets-Berechnung ein. Mehrfachauswahl mit UND-Verknuepfung.

```python
from shared.indicator_filter_ui import indicator_filter_sidebar, render_filter_badge
from shared.indicators import apply_indicator_filter

# Sidebar (in with st.sidebar:)
filters = indicator_filter_sidebar(key_prefix="mp")

# Vor Berechnung anwenden
if filters:
    mask = apply_indicator_filter(df, filters)
    df = df[mask].copy()
    render_filter_badge(filters, total_days, filtered_days)
```

Indikatoren: SMA, EMA, RSI, Bollinger Bands, MACD, LBR Oscillator (Raschke).
Integriert in: Mondphasen, Wochentage, Monatswechsel, OPEX, Zentralbanken.

## Blog Engine (blog/blog_builder.py)

Markdown → statisches HTML mit eingebetteten Charts, Social-Media und YouTube-Generierung.

```bash
python blog/blog_builder.py --build                    # Alle Posts bauen
python blog/blog_builder.py --generate "Titel" --ticker ^GSPC --category marktausblick
```

3 Kategorien: Education, Marktausblick, Tutorials.
Scheduled Publishing: Posts mit `status: scheduled` + `publish_date` erscheinen automatisch.
Pro Post generiert: HTML + 3 Tweets + LinkedIn-Post + Video-Script + Shorts + YouTube-Description.
Details: `docs/BLOG_WORKFLOW.md`

## Intraday Price Updates (scripts/intraday_refresh.py)

Lightweight-Script fuer untertaegige Kurs-Updates. Nur Preise, keine KI-Berechnungen.
GitHub Actions Workflow `intraday_update.yml` triggert **stündlich um :17** (24/7, off-peak).
Das Script entscheidet anhand der UTC-Zeit welche Gruppen aktiv sind.

### Zeitplan (MESZ / UTC+2)

| Gruppe | Ticker | Zeiten (MESZ) | Tage |
|--------|--------|---------------|------|
| EU (Indizes + Aktien) | 25 | 9:15, 9:35, 11:00, 13:00, 15:00, 17:00, 17:35 | Mo-Fr |
| US (Indizes, ETFs, Aktien, Commodities) | 50 | 15:35, 16:15, 17:00, 18:00, 19:00, 20:00, 21:30, 22:05 | Mo-Fr |
| Asien | 3 | 3:00, 5:00, 8:00 | Mo-Fr |
| FX | 7 | 8:00, 12:00, 15:30, 18:00, 22:00 | Mo-Fr |
| Crypto | 6 | Stuendlich (0:00-23:00) | Mo-So |

```bash
python scripts/intraday_refresh.py              # Normaler Lauf
python scripts/intraday_refresh.py --dry-run    # Nur anzeigen
python scripts/intraday_refresh.py --group eu   # Nur EU-Ticker
```

### GitHub Actions Budget
~1.370 Min/Monat von 2.000 Free Tier (Intraday + Nightly + Deploy).

## Batch-Jobs & Tooling (`scripts/`)

| Skript | Zweck |
|--------|-------|
| `nightly_refresh.py` | Voller Nightly-Lauf (Phasen A..Z) |
| `intraday_refresh.py` | Untertägige Kurs-Updates (gruppen-/zeitfenster-gesteuert) |
| `full_scanner_run.py` | scanner_results + ki_scores für alle Ticker (`--only`/`--resume`) |
| **`onboard_ticker.py`** | **Neuen Ticker aufnehmen** (validieren→backfill→tickers.json→DB→verify) — Pflichtweg, verhindert Orphans |
| **`check_db_completeness.py`** | DB-Vollständigkeits-Audit (freshness/coverage/gaps/events + Orphan-/Stale-Tail-Erkennung; `--fix`) |
| `backfill_new_ticker.py` | Voll-Historie eines Tickers (OHLC + log_return + TDOM/TDOY) |
| `fix_missing_days.py` / `backfill_tdoy.py` / `backfill_ohlc.py` / `backfill_log_return.py` | Gezielte Backfills (Lücken/TDOM/OHLC/log_return) |
| `fetch_event_data.py` | Dividenden + Earnings (Yahoo Crumb-Auth) |
| `compute_regime_scores.py` | Regime/Crash-Ampel (Isolation Forest) |
| `generate_tickers_json.py` / `generate_landing_chart.py` / `generate_decade_data.py` | Vorberechnete JSON für `landing/data/` |
| `daily_health_check.py` / `daily_newsletter.py` / `weekly_newsletter.py` | Health-Mail / Daily Briefing / Weekly Newsletter |
| `polymarket_refresh.py` / `polymarket_backfill.py` / `compute_brier_stats.py` | Polymarket-Pipeline |
| `restore_tickers_table.sql` / `create_*.sql` | Schema-DDL (Supabase SQL-Editor, idempotent) |

Lokal IMMER `py -3.14` (= Container-Version; Default-`py` = 3.9 scheitert an `X | None`-Syntax) + bei Datei-Umleitung `PYTHONUTF8=1`.

## Deployment

### VPS (Hetzner CPX22)
- Docker + Nginx + SSL (Let's Encrypt)
- Domain: seasonalpha.ai (STRATO A-Record + CNAME www)
- Auto-Deploy: GitHub Action → SSH → git pull + docker rebuild

### GitHub Actions Workflows

Alle Workflows laufen via SSH auf dem VPS (`appleboy/ssh-action` + `docker exec`).

| Workflow | Datei | Zeitplan (UTC) | Funktion |
|----------|-------|----------|----------|
| Deploy | `deploy.yml` | Push auf master | git pull + SEO + Blog + Decade- & Landing-Chart-Daten + `build_en.py` + docker rebuild |
| Intraday Update | `intraday_update.yml` | `17 * * * *` (stündl., 24/7) | Kurs-Updates (EU/US/Asien/FX/Crypto), zeitfenster-gesteuert |
| Nightly Refresh | `nightly_refresh.yml` | `30 20 * * 1-5` | Voller Refresh: prices, monthly/ki/tdom/tdoy/regime/spot_vol, Gap-Fill, refresh_log; So zusätzl. Newsletter/Brier |
| Nightly Update | `nightly_update.yml` | `0 21 * * 1-5` | Batch-Download aller Ticker |
| Event Data | `event_data_daily.yml` | `15 22 * * *` | Dividenden + Earnings (Yahoo Crumb-Auth) |
| Daily Briefing | `daily_newsletter.yml` | `0 6 * * 1-5` | Daily Morning Briefing (Brevo) |
| Daily Health | `daily_health.yml` | `0 5 * * *` | System-Health-Mail (refresh_log/Freshness) |
| **DB Completeness** | `db_completeness.yml` | `0 5 * * 0` (So) | 4-Dim-Audit + Orphan-/Stale-Erkennung + Auto-Fix + Mail |
| Full Scanner | `full_scanner.yml` | `0 3 * * 0` (So) | scanner_results + ki_scores für alle Ticker |
| Brier Compute | `brier_compute.yml` | `0 2 * * 0` (So) | Polymarket-Brier-Kalibrierung |
| Polymarket Daily/Intraday | `polymarket_daily.yml` / `polymarket_intraday.yml` | `30 21 * * *` / `23 * * *` | Prognosemarkt-Snapshots (Intraday FOMC-Fenster) |
| Weekly Newsletter (manuell) | `weekly_newsletter_manual.yml` | `workflow_dispatch` | test/dry-run/live |

### Streamlit Cache
- `yahoo_downloader.py`: `@st.cache_data(ttl=900)` — 15 Min TTL
- Intraday-Updates werden spaetestens 15 Min nach Refresh in der App sichtbar

### Routing (Nginx)
| URL | Ziel |
|-----|------|
| `/` + Feature-Slugs (`/dashboard`, `/jahreszyklus`, …) | `landing/pages/*.html` (statisch, **Haupt-Frontend**) |
| `/en/*` | dieselben Pages, statisch vorgerendert aus `landing/en/` (Deploy-Build) |
| `/landing/*.{css,js,json}` | Assets (`max-age=0` + ETag bzw. `?v=<git-sha>` Cache-Bust) |
| `/blog/`, `/en/blog/` | `blog/output/` (DE/EN, serverseitig gebaut) |
| `/analyse/{slug}` | `seo/output/{slug}.html` (programmatic SEO) |
| `/sitemap.xml`, `/robots.txt` | `seo/output/` |
| `/app/` | Streamlit (vestigial — produktseitig ungenutzt; läuft nur als Container-Keep-alive) |

⚠️ Nginx-Config-Änderung aktivieren: `docker compose restart nginx` (NICHT `nginx -s reload` — Single-File-Bind-Mount hängt am alten Inode). Reine HTML/Asset-Änderungen: `git pull` reicht.

## dj_data.py

```python
from shared.dj_data import load_dj_data
df, source = load_dj_data(project_dir)  # KEIN @st.cache_data!
# df-Spalten: year, trading_day, cum_return_pct
```

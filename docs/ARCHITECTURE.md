# Architektur — SeasonAlpha

> Stand: 2026-06-13

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
  significance_gauge.py   percentile_bar.py
        ↓                          ↓
     pages/*.py (UI)  ←  footer.py + ticker_select.py + apply_se_theme()
```

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

Secrets in `.streamlit/secrets.toml` → `os.environ["SUPABASE_URL"]` / `os.environ["SUPABASE_KEY"]`

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
| `ki_score.py` | KI Seasonal Score Engine (4 Sub-Scores → 0-10) |
| `ai_models.py` | DTW, Prophet, Isolation Forest, Claude API, KI-Summary, Anomalie-Heatmap |
| `anomaly_engine.py` | Anomalie-Radar, Crash-Ampel, TDoM-Anomalien, Muster-Brueche |
| `outlier_manager.py` | Outlier-Filter (IQR, Winsorize, Isolation Forest) |
| `significance_gauge.py` | Signifikanztest (t-Test, Cohen's d) + Radial Gauge |
| `tdom_analysis.py` | TDoM Berechnungen (3 Strategien, Ranges, Heatmap) |
| `spot_vol_beta.py` | Spot-Vol Beta (SPX vs VIX, Daily + Rolling + Regime-Wendepunkte) |
| `shock_analysis.py` | Shock Analyzer (Trigger→Target) |
| `sector_rotation.py` | Sektor-Rotation Analyse |
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
| `supabase_client.py` | DB-Connector + Subscriber + Market Events + Cache |
| `cache_manager.py` | Computed Values Cache (DB → Fallback → Store) |
| `market_calendar.py` | Feiertage/OPEX/Zentralbank → Supabase sync |
| `logger.py` | 3 Log-Kanaele (app/error/access) |
| `download_manager.py` | Batch-Downloads mit Queue + Rate Limiter |
| `email_brevo.py` | E-Mail-Versand via Brevo API |

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
GitHub Actions Workflow `intraday_update.yml` triggert alle 30 Min.
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

## Deployment

### VPS (Hetzner CPX22)
- Docker + Nginx + SSL (Let's Encrypt)
- Domain: seasonalpha.ai (STRATO A-Record + CNAME www)
- Auto-Deploy: GitHub Action → SSH → git pull + docker rebuild

### GitHub Actions Workflows

Alle Workflows laufen via SSH auf dem VPS (`appleboy/ssh-action` + `docker exec`).

| Workflow | Datei | Zeitplan | Funktion |
|----------|-------|----------|----------|
| Deploy | `deploy.yml` | Push auf master | git pull + SEO + Blog + docker rebuild |
| Intraday Update | `intraday_update.yml` | `*/30 * * * *` (24/7) | Kurs-Updates (EU/US/Asien/FX/Crypto) |
| Nightly Refresh | `nightly_refresh.yml` | `0 20 * * 1-5` | Voller Refresh + KI-Scores + TDOM + Calendar |
| Nightly Update | `nightly_update.yml` | `30 20 * * 1-5` | Batch-Download aller Ticker |

### Streamlit Cache
- `yahoo_downloader.py`: `@st.cache_data(ttl=900)` — 15 Min TTL
- Intraday-Updates werden spaetestens 15 Min nach Refresh in der App sichtbar

### Routing (Nginx)
| URL | Ziel |
|-----|------|
| `/blog/` | `blog/output/` (Blog-Index + Posts) |
| `/blog/{slug}/` | `blog/output/{slug}/index.html` |
| `/analyse/{slug}` | `seo/output/{slug}.html` (94 Landingpages) |
| `/disclaimer` | `seo/output/disclaimer.html` |
| `/sitemap.xml` | `seo/output/sitemap.xml` |
| `/robots.txt` | `seo/output/robots.txt` |
| `/` (alles andere) | Streamlit App (Reverse Proxy) |

## dj_data.py

```python
from shared.dj_data import load_dj_data
df, source = load_dj_data(project_dir)  # KEIN @st.cache_data!
# df-Spalten: year, trading_day, cum_return_pct
```

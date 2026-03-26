-- SeasonalEdge: Market Calendar + Computed Values Cache
-- Run in Supabase SQL Editor

-- ── Market Events (Feiertage, OPEX, Zentralbank-Termine) ──────────────────────

CREATE TABLE IF NOT EXISTS market_events (
    id BIGSERIAL PRIMARY KEY,
    event_date DATE NOT NULL,
    event_type TEXT NOT NULL,        -- 'holiday','opex','central_bank','market_event'
    event_name TEXT NOT NULL,
    exchange TEXT NOT NULL,           -- 'NYSE','XETRA','LSE','EURONEXT','TSE','ALL'
    subtype TEXT,                     -- 'bond_closed','early_close','rate_decision','minutes','triple_witching'
    meta JSONB DEFAULT '{}',
    year INT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(event_date, event_type, event_name, exchange)
);

CREATE INDEX IF NOT EXISTS idx_market_events_date ON market_events (event_date);
CREATE INDEX IF NOT EXISTS idx_market_events_type ON market_events (event_type);
CREATE INDEX IF NOT EXISTS idx_market_events_exchange ON market_events (exchange);
CREATE INDEX IF NOT EXISTS idx_market_events_year ON market_events (year);

-- ── Monthly Stats (900 Ticker x 12 Monate x years_back Varianten) ─────────────

CREATE TABLE IF NOT EXISTS monthly_stats (
    id BIGSERIAL PRIMARY KEY,
    ticker TEXT NOT NULL,
    month INT NOT NULL,
    years_back INT NOT NULL,
    avg_return FLOAT,
    median_return FLOAT,
    win_rate FLOAT,
    std_dev FLOAT,
    max_gain FLOAT,
    max_loss FLOAT,
    total_years INT,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(ticker, month, years_back)
);

CREATE INDEX IF NOT EXISTS idx_monthly_stats_ticker ON monthly_stats (ticker);

-- ── KI Scores (900 Ticker x 1 Datum) ──────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ki_scores (
    id BIGSERIAL PRIMARY KEY,
    ticker TEXT NOT NULL,
    score FLOAT NOT NULL,
    signal TEXT NOT NULL,
    dtw_score FLOAT,
    prophet_score FLOAT,
    win_rate_score FLOAT,
    tracking_score FLOAT,
    details JSONB DEFAULT '{}',
    computed_date DATE NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(ticker, computed_date)
);

CREATE INDEX IF NOT EXISTS idx_ki_scores_ticker ON ki_scores (ticker);
CREATE INDEX IF NOT EXISTS idx_ki_scores_date ON ki_scores (computed_date);

-- ── Scanner Results (900 Ticker x 1 Datum) ────────────────────────────────────

CREATE TABLE IF NOT EXISTS scanner_results (
    id BIGSERIAL PRIMARY KEY,
    ticker TEXT NOT NULL,
    score FLOAT NOT NULL,
    signal TEXT NOT NULL,
    win_rate FLOAT,
    avg_return FLOAT,
    deviation FLOAT,
    scan_date DATE NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(ticker, scan_date)
);

CREATE INDEX IF NOT EXISTS idx_scanner_results_date ON scanner_results (scan_date);

-- ── TDoM Stats (900 Ticker x ~46 TDoM-Werte) ─────────────────────────────────

CREATE TABLE IF NOT EXISTS tdom_stats (
    id BIGSERIAL PRIMARY KEY,
    ticker TEXT NOT NULL,
    tdom INT NOT NULL,
    direction TEXT NOT NULL,          -- 'forward' oder 'backward'
    strategy TEXT NOT NULL,           -- 'open_to_close','open_to_next_open','close_to_next_close'
    avg_return FLOAT,
    median_return FLOAT,
    win_rate FLOAT,
    std_dev FLOAT,
    count INT,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(ticker, tdom, direction, strategy)
);

CREATE INDEX IF NOT EXISTS idx_tdom_stats_ticker ON tdom_stats (ticker);

-- ── Spot-Vol Beta (taeglich) ──────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS spot_vol_beta (
    id BIGSERIAL PRIMARY KEY,
    event_date DATE NOT NULL,
    spx_close FLOAT,
    vix_close FLOAT,
    spx_ret FLOAT,
    vix_chg FLOAT,
    daily_beta FLOAT,
    rolling_beta_60 FLOAT,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(event_date)
);

CREATE INDEX IF NOT EXISTS idx_spot_vol_beta_date ON spot_vol_beta (event_date);

-- ── Historical CPI (Jahresdurchschnitte, 1886–heute) ────────────────────────

CREATE TABLE IF NOT EXISTS historical_cpi (
    id BIGSERIAL PRIMARY KEY,
    year INT NOT NULL,
    cpi FLOAT NOT NULL,
    source TEXT DEFAULT 'bls_embedded',   -- 'bls_historical','fred_cpiaucsl','bls_embedded'
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(year)
);

CREATE INDEX IF NOT EXISTS idx_historical_cpi_year ON historical_cpi (year);

-- ── Ticker-Stammdaten (Symboldatenbank) ─────────────────────────────────────

CREATE TABLE IF NOT EXISTS tickers (
    ticker       TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    kategorie    TEXT NOT NULL,
    waehrung     TEXT DEFAULT 'USD',
    exchange     TEXT,
    beschreibung TEXT,
    aktiv        BOOLEAN DEFAULT TRUE,
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tickers_kategorie ON tickers (kategorie);
CREATE INDEX IF NOT EXISTS idx_tickers_name ON tickers (name);

-- RPC: Ticker-Suche (fuer zukuenftige API-Nutzung)
CREATE OR REPLACE FUNCTION search_tickers(q TEXT, lim INT DEFAULT 10)
RETURNS TABLE(ticker TEXT, name TEXT, kategorie TEXT) AS $$
  SELECT t.ticker, t.name, t.kategorie FROM tickers t
  WHERE t.aktiv = TRUE
    AND (t.ticker ILIKE q || '%' OR t.name ILIKE '%' || q || '%')
  ORDER BY
    CASE WHEN t.ticker ILIKE q THEN 0
         WHEN t.ticker ILIKE q || '%' THEN 1
         ELSE 2 END,
    t.name
  LIMIT lim;
$$ LANGUAGE sql STABLE;

-- ══════════════════════════════════════════════════════════════════════════════
-- Row Level Security (RLS)
-- Ohne RLS kann jeder mit dem anon-Key alle Daten lesen/schreiben/loeschen!
-- service_role bypassed RLS automatisch (Backend/Nightly Jobs).
-- ══════════════════════════════════════════════════════════════════════════════

-- ── RLS aktivieren ───────────────────────────────────────────────────────────

ALTER TABLE prices ENABLE ROW LEVEL SECURITY;
ALTER TABLE seasonality ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscribers ENABLE ROW LEVEL SECURITY;
ALTER TABLE market_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE monthly_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE ki_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE scanner_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE tdom_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE spot_vol_beta ENABLE ROW LEVEL SECURITY;
ALTER TABLE historical_cpi ENABLE ROW LEVEL SECURITY;
ALTER TABLE tickers ENABLE ROW LEVEL SECURITY;

-- ── Policies: Marktdaten read-only fuer anon ────────────────────────────────

CREATE POLICY "anon_read" ON prices FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON seasonality FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON market_events FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON monthly_stats FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON ki_scores FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON scanner_results FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON tdom_stats FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON spot_vol_beta FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON historical_cpi FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON tickers FOR SELECT TO anon USING (true);

-- ── Policies: Subscribers + Logs nur Insert fuer anon ───────────────────────

CREATE POLICY "anon_subscribe" ON subscribers FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "anon_log" ON app_logs FOR INSERT TO anon WITH CHECK (true);

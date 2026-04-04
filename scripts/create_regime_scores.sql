-- regime_scores: Isolation Forest Markt-Regime-Scoring
-- Historische + tagesaktuelle Risk-Scores pro Ticker

CREATE TABLE IF NOT EXISTS regime_scores (
    id          BIGSERIAL PRIMARY KEY,
    ticker      TEXT NOT NULL,
    date        DATE NOT NULL,
    risk_score  REAL NOT NULL,               -- 0-100 (Percentile)
    traffic_light TEXT NOT NULL DEFAULT 'grey', -- green/yellow/red/grey
    vol_5d      REAL,
    vol_10d     REAL,
    vol_20d     REAL,
    drawdown    REAL,
    ret_1d      REAL,
    ret_5d      REAL,
    ret_20d     REAL,
    anomaly_score REAL,                       -- Raw Isolation Forest Score
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(ticker, date)
);

CREATE INDEX IF NOT EXISTS idx_regime_scores_ticker ON regime_scores (ticker);
CREATE INDEX IF NOT EXISTS idx_regime_scores_date ON regime_scores (ticker, date DESC);

-- RLS
ALTER TABLE regime_scores ENABLE ROW LEVEL SECURITY;
CREATE POLICY "anon_read_regime" ON regime_scores FOR SELECT TO anon USING (true);

-- Service-Role darf schreiben
CREATE POLICY "service_write_regime" ON regime_scores FOR ALL
    TO service_role USING (true) WITH CHECK (true);

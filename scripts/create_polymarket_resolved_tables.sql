-- ============================================================
-- scripts/create_polymarket_resolved_tables.sql
-- ============================================================
-- Tabellen fuer historisch bereits aufgeloeste Polymarket-Markets.
-- Getrennt vom live-Set (polymarket_markets / _prices), weil die Daten
-- nie geupdated werden und eine andere Semantik haben (Resolution-Outcome
-- statt laufender YES-Preis).
--
-- Verwendung: Brier-Score & Kalibrierungs-Analyse auf /polymarket.
-- Pro resolved market:
--   - Kopf-Row in polymarket_resolved_markets (Frage, Outcome, Kategorie)
--   - N Zeilen in polymarket_resolved_prices (YES-Preis-Historie bis zur
--     Resolution, typisch 1 Punkt pro Tag aus CLOB prices-history)
--
-- In Supabase SQL-Editor ausfuehren.
-- ============================================================

-- ── Markt-Katalog (Kopf-Row) ────────────────────────────────
CREATE TABLE IF NOT EXISTS polymarket_resolved_markets (
    id               BIGSERIAL PRIMARY KEY,
    condition_id     TEXT UNIQUE NOT NULL,
    slug             TEXT,
    question         TEXT,
    category         TEXT,                    -- fed, macro, crypto, politics, sports, other
    event_id         BIGINT,                  -- Gamma event_id (Gruppierung)
    end_date         TIMESTAMPTZ,             -- Resolution-Deadline
    resolution_date  TIMESTAMPTZ,             -- echter Resolution-Zeitpunkt (= endDateIso)
    outcome_yes      BOOLEAN NOT NULL,        -- true = YES resolved, false = NO resolved
    volume_total_usd NUMERIC,
    meta             JSONB DEFAULT '{}'::jsonb,
    scraped_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pm_resolved_markets_category   ON polymarket_resolved_markets (category);
CREATE INDEX IF NOT EXISTS idx_pm_resolved_markets_resolution ON polymarket_resolved_markets (resolution_date);
CREATE INDEX IF NOT EXISTS idx_pm_resolved_markets_event      ON polymarket_resolved_markets (event_id);

-- ── Preis-Historie ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS polymarket_resolved_prices (
    id               BIGSERIAL PRIMARY KEY,
    condition_id     TEXT NOT NULL REFERENCES polymarket_resolved_markets(condition_id) ON DELETE CASCADE,
    ts               TIMESTAMPTZ NOT NULL,
    yes_price        NUMERIC NOT NULL CHECK (yes_price >= 0 AND yes_price <= 1),
    UNIQUE (condition_id, ts)
);

CREATE INDEX IF NOT EXISTS idx_pm_resolved_prices_cid_ts ON polymarket_resolved_prices (condition_id, ts DESC);

-- ── RLS: Lesen fuer alle, Schreiben nur service_role ────────
ALTER TABLE polymarket_resolved_markets ENABLE ROW LEVEL SECURITY;
ALTER TABLE polymarket_resolved_prices  ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_read"           ON polymarket_resolved_markets;
DROP POLICY IF EXISTS "service_write"       ON polymarket_resolved_markets;
DROP POLICY IF EXISTS "anon_read_prices"    ON polymarket_resolved_prices;
DROP POLICY IF EXISTS "service_write_prices" ON polymarket_resolved_prices;

CREATE POLICY "anon_read" ON polymarket_resolved_markets
    FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "service_write" ON polymarket_resolved_markets
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "anon_read_prices" ON polymarket_resolved_prices
    FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "service_write_prices" ON polymarket_resolved_prices
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ── GRANTs (RLS allein reicht nicht) ────────────────────────
GRANT SELECT ON polymarket_resolved_markets TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON polymarket_resolved_markets TO service_role;
GRANT USAGE, SELECT ON SEQUENCE polymarket_resolved_markets_id_seq TO service_role;

GRANT SELECT ON polymarket_resolved_prices TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON polymarket_resolved_prices TO service_role;
GRANT USAGE, SELECT ON SEQUENCE polymarket_resolved_prices_id_seq TO service_role;

-- ── Verifikation ────────────────────────────────────────────
-- SELECT COUNT(*) FROM polymarket_resolved_markets;
-- SELECT category, COUNT(*) FROM polymarket_resolved_markets GROUP BY category;

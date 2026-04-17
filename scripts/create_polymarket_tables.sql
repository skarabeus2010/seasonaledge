-- SeasonAlpha: Polymarket Prediction Markets
-- Run in Supabase SQL Editor
--
-- Zwei Tabellen:
--   polymarket_markets — Katalog der kuratierten Maerkte (Metadata)
--   polymarket_prices  — Zeitreihe der YES-Probabilities (Snapshots + Backfill)

-- ── Market-Katalog ──────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS polymarket_markets (
    id BIGSERIAL PRIMARY KEY,
    condition_id TEXT NOT NULL UNIQUE,   -- Polymarket Condition-ID (0x...)
    slug TEXT NOT NULL UNIQUE,           -- Stabiler URL-Slug (z.B. 'fed-cut-may-2026')
    question TEXT NOT NULL,              -- Original-Frage des Marktes
    category TEXT NOT NULL,              -- 'fed','macro','index','events','crypto'
    end_date TIMESTAMPTZ,                -- Erwartete Resolution
    yes_token_id TEXT,                   -- CLOB Token-ID fuer YES-Share
    no_token_id TEXT,                    -- CLOB Token-ID fuer NO-Share
    resolution TEXT,                     -- NULL=offen, 'yes'|'no'|'invalid'
    resolved_at TIMESTAMPTZ,
    liquidity_usd NUMERIC,
    volume_total_usd NUMERIC,
    meta JSONB DEFAULT '{}',             -- Raw tags, gamma_id, etc.
    active BOOLEAN DEFAULT TRUE,         -- false = aus UI entfernen (resolvt/stale)
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pm_markets_category ON polymarket_markets (category);
CREATE INDEX IF NOT EXISTS idx_pm_markets_active ON polymarket_markets (active);
CREATE INDEX IF NOT EXISTS idx_pm_markets_end_date ON polymarket_markets (end_date);

-- ── Preis-Zeitreihe ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS polymarket_prices (
    id BIGSERIAL PRIMARY KEY,
    condition_id TEXT NOT NULL,
    ts TIMESTAMPTZ NOT NULL,             -- Zeitpunkt des Snapshots / Backfills
    yes_price NUMERIC NOT NULL,          -- 0.00 - 1.00 (implied probability)
    volume_24h NUMERIC,
    spread NUMERIC,                      -- best_ask - best_bid (aus Orderbook, optional)
    source TEXT DEFAULT 'clob',          -- 'clob','prices-history','backfill'
    UNIQUE(condition_id, ts)
);

CREATE INDEX IF NOT EXISTS idx_pm_prices_cid_ts ON polymarket_prices (condition_id, ts DESC);
CREATE INDEX IF NOT EXISTS idx_pm_prices_ts ON polymarket_prices (ts DESC);

-- ── Row Level Security ─────────────────────────────────────────────────────

ALTER TABLE polymarket_markets ENABLE ROW LEVEL SECURITY;
ALTER TABLE polymarket_prices  ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_read" ON polymarket_markets FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON polymarket_prices  FOR SELECT TO anon USING (true);

-- Hinweis: Schreib-Zugriff nur via service_role (Nightly-/Hourly-Jobs).
-- service_role bypasst RLS automatisch.

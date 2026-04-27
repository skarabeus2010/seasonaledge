-- ══════════════════════════════════════════════════════════════
-- create_event_tables.sql
-- Dividenden- und Earnings-Ereignisse für Event-Window-Analyse
-- Ausführen in Supabase SQL Editor
-- ══════════════════════════════════════════════════════════════

-- ── dividend_events ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dividend_events (
  ticker      text    NOT NULL,
  ex_date     date    NOT NULL,
  amount      numeric,
  currency    text    DEFAULT 'USD',
  created_at  timestamptz DEFAULT now(),
  PRIMARY KEY (ticker, ex_date)
);

ALTER TABLE dividend_events ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_read_dividends"    ON dividend_events;
DROP POLICY IF EXISTS "service_write_dividends" ON dividend_events;

CREATE POLICY "anon_read_dividends"
  ON dividend_events FOR SELECT TO anon USING (true);

GRANT ALL ON dividend_events TO service_role;

CREATE INDEX IF NOT EXISTS idx_dividend_events_ticker ON dividend_events(ticker);
CREATE INDEX IF NOT EXISTS idx_dividend_events_ex_date ON dividend_events(ex_date);

-- ── earnings_events ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS earnings_events (
  ticker        text    NOT NULL,
  report_date   date    NOT NULL,
  eps_actual    numeric,
  eps_estimate  numeric,
  surprise_pct  numeric,
  created_at    timestamptz DEFAULT now(),
  PRIMARY KEY (ticker, report_date)
);

ALTER TABLE earnings_events ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_read_earnings"    ON earnings_events;
DROP POLICY IF EXISTS "service_write_earnings" ON earnings_events;

CREATE POLICY "anon_read_earnings"
  ON earnings_events FOR SELECT TO anon USING (true);

GRANT ALL ON earnings_events TO service_role;

CREATE INDEX IF NOT EXISTS idx_earnings_events_ticker ON earnings_events(ticker);
CREATE INDEX IF NOT EXISTS idx_earnings_events_report_date ON earnings_events(report_date);

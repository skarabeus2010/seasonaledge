-- Tabelle fuer Zentralbank-Sitzungstermine
-- Wird von zentralbanken.html gelesen (Supabase REST API)
-- Refresh: alle 2 Monate per scripts/refresh_central_bank_dates.py

CREATE TABLE IF NOT EXISTS central_bank_dates (
    id BIGSERIAL PRIMARY KEY,
    bank TEXT NOT NULL,          -- 'fomc', 'ecb', 'boe', 'boj'
    date DATE NOT NULL,
    label TEXT DEFAULT '',       -- z.B. 'FOMC', 'ECB Rate Decision'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(bank, date)
);

-- Index fuer schnelle Abfragen
CREATE INDEX IF NOT EXISTS idx_cbd_bank_date ON central_bank_dates(bank, date);

-- RLS: anon darf lesen
ALTER TABLE central_bank_dates ENABLE ROW LEVEL SECURITY;
CREATE POLICY "anon_read_cbd" ON central_bank_dates FOR SELECT TO anon USING (true);

-- Schreibrechte fuer authenticated (Refresh-Script)
GRANT ALL ON central_bank_dates TO authenticated;
GRANT ALL ON central_bank_dates TO anon;
GRANT USAGE, SELECT ON SEQUENCE central_bank_dates_id_seq TO anon;

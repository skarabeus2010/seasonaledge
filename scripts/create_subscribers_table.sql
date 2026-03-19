-- ══════════════════════════════════════════════════════════
-- SeasonalEdge — subscribers Tabelle
-- In Supabase SQL-Editor ausführen
-- ══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS subscribers (
    id              BIGSERIAL PRIMARY KEY,
    email           TEXT NOT NULL UNIQUE,
    status          TEXT NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'unsubscribed', 'bounced', 'complained')),
    source          TEXT DEFAULT 'website',          -- website, import, admin
    subscribed_at   TIMESTAMPTZ DEFAULT NOW(),
    unsubscribed_at TIMESTAMPTZ,                     -- wann ausgetragen
    no_emails       BOOLEAN NOT NULL DEFAULT FALSE,  -- Master-Flag: keine E-Mails
    brevo_synced    BOOLEAN NOT NULL DEFAULT FALSE,   -- in Brevo eingetragen?
    ip_address      TEXT,                             -- DSGVO: Nachweis Einwilligung
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Index für schnelle Lookups
CREATE INDEX IF NOT EXISTS idx_subscribers_email ON subscribers (email);
CREATE INDEX IF NOT EXISTS idx_subscribers_status ON subscribers (status);

-- Auto-Update von updated_at
CREATE OR REPLACE FUNCTION update_subscribers_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_subscribers_updated ON subscribers;
CREATE TRIGGER trg_subscribers_updated
    BEFORE UPDATE ON subscribers
    FOR EACH ROW
    EXECUTE FUNCTION update_subscribers_timestamp();

-- RLS aktivieren (Row Level Security)
ALTER TABLE subscribers ENABLE ROW LEVEL SECURITY;

-- Policy: Service-Key darf alles
CREATE POLICY "service_full_access" ON subscribers
    FOR ALL
    USING (TRUE)
    WITH CHECK (TRUE);

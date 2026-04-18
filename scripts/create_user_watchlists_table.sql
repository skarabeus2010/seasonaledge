-- SeasonAlpha: User-gebundene Watchlist
-- Run in Supabase SQL Editor
--
-- Zweck: Ersetzt / ergänzt die localStorage-Watchlist (SA.watchlist) durch
-- eine Cloud-Variante. Eingeloggte User bekommen automatische Sync zwischen
-- Browsern/Geräten. Gast-User nutzen weiterhin localStorage.

CREATE TABLE IF NOT EXISTS user_watchlists (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    ticker TEXT NOT NULL,
    added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    note TEXT NOT NULL DEFAULT '',
    UNIQUE(user_id, ticker)
);

CREATE INDEX IF NOT EXISTS idx_user_watchlists_user ON user_watchlists(user_id);
CREATE INDEX IF NOT EXISTS idx_user_watchlists_added_at ON user_watchlists(user_id, added_at DESC);

-- ── Row Level Security ──────────────────────────────────────────────────────
-- Jeder authentifizierte User sieht + ändert nur seine eigenen Einträge.
ALTER TABLE user_watchlists ENABLE ROW LEVEL SECURITY;

-- Table-Level GRANTs (ohne die scheitert auch RLS-erlaubter Zugriff)
GRANT SELECT, INSERT, UPDATE, DELETE ON user_watchlists TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE user_watchlists_id_seq TO authenticated;

GRANT SELECT, INSERT, UPDATE, DELETE ON user_watchlists TO service_role;
GRANT USAGE, SELECT ON SEQUENCE user_watchlists_id_seq TO service_role;

-- RLS Policies: User = eigene Zeilen via auth.uid()
DROP POLICY IF EXISTS "user_read_own" ON user_watchlists;
DROP POLICY IF EXISTS "user_insert_own" ON user_watchlists;
DROP POLICY IF EXISTS "user_update_own" ON user_watchlists;
DROP POLICY IF EXISTS "user_delete_own" ON user_watchlists;

CREATE POLICY "user_read_own"   ON user_watchlists FOR SELECT TO authenticated
    USING (auth.uid() = user_id);
CREATE POLICY "user_insert_own" ON user_watchlists FOR INSERT TO authenticated
    WITH CHECK (auth.uid() = user_id);
CREATE POLICY "user_update_own" ON user_watchlists FOR UPDATE TO authenticated
    USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "user_delete_own" ON user_watchlists FOR DELETE TO authenticated
    USING (auth.uid() = user_id);

-- Hinweis: anon kann nichts. Nur eingeloggte User dürfen lesen/schreiben.
-- service_role bypasst RLS sowieso (für Admin-/Cron-Scripts bei Bedarf).

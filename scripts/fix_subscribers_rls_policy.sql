-- ============================================================
-- scripts/fix_subscribers_rls_policy.sql
-- ============================================================
-- Fix fuer die urspruengliche Policy in create_subscribers_table.sql:
--
--   CREATE POLICY "service_full_access" ON subscribers
--       FOR ALL USING (TRUE) WITH CHECK (TRUE);
--
-- Ohne TO-Clause greift die Policy auf PUBLIC = jede Rolle, inkl. `anon`.
-- Konsequenz: Mit dem Anon-Key koennte jeder Browser-Request beliebig
-- SELECT/INSERT/UPDATE/DELETE auf subscribers ausfuehren.
--
-- Dieser Patch:
--   1. DROP der offenen Policy
--   2. Neue Policy nur fuer `service_role` (RLS-Bypass auch ohne Policy,
--      aber wir machen es explizit und auditierbar)
--
-- Zugriff aus dem Frontend laeuft damit ausschliesslich ueber SECURITY
-- DEFINER RPCs:
--   - unsubscribe_with_token()     (anon, Token-validiert)
--   - get_my_newsletter_status()   (authenticated, JWT-email)
--   - toggle_my_newsletter(bool)   (authenticated, JWT-email)
--
-- Subscribe-Formular auf der Startseite nutzt weiterhin subscribe_email()
-- im Python-Backend (service_role), nicht den direkten REST-Write.
--
-- In Supabase SQL-Editor ausfuehren.
-- ============================================================

DROP POLICY IF EXISTS "service_full_access" ON subscribers;

CREATE POLICY "service_role_full_access" ON subscribers
    FOR ALL
    TO service_role
    USING (TRUE)
    WITH CHECK (TRUE);

-- ── Verifikation ────────────────────────────────────────────────
-- SELECT polname, polroles::regrole[] FROM pg_policy
--   WHERE polrelid = 'public.subscribers'::regclass;
-- Erwartung: polroles enthaelt nur {service_role}.

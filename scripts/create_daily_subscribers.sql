-- ══════════════════════════════════════════════════════════
-- SeasonalEdge — daily_subscribers Tabelle + RPCs
-- Komplett getrennt von `subscribers` (Weekly) damit Daily ein
-- eigenes Opt-In hat. User können beides unabhängig abonnieren.
-- In Supabase SQL-Editor ausführen.
-- ══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS daily_subscribers (
    id              BIGSERIAL PRIMARY KEY,
    email           TEXT NOT NULL UNIQUE,
    status          TEXT NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'unsubscribed', 'bounced', 'complained')),
    source          TEXT DEFAULT 'profile',           -- profile, landing, api, admin
    subscribed_at   TIMESTAMPTZ DEFAULT NOW(),
    unsubscribed_at TIMESTAMPTZ,
    no_emails       BOOLEAN NOT NULL DEFAULT FALSE,
    brevo_synced    BOOLEAN NOT NULL DEFAULT FALSE,
    ip_address      TEXT,
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_daily_subscribers_email  ON daily_subscribers (email);
CREATE INDEX IF NOT EXISTS idx_daily_subscribers_status ON daily_subscribers (status);

-- Auto-Update updated_at (eigener Trigger-Name, parallel zu subscribers)
CREATE OR REPLACE FUNCTION update_daily_subscribers_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_daily_subscribers_updated ON daily_subscribers;
CREATE TRIGGER trg_daily_subscribers_updated
    BEFORE UPDATE ON daily_subscribers
    FOR EACH ROW
    EXECUTE FUNCTION update_daily_subscribers_timestamp();

ALTER TABLE daily_subscribers ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "service_full_access" ON daily_subscribers;
CREATE POLICY "service_full_access" ON daily_subscribers
    FOR ALL
    USING (TRUE)
    WITH CHECK (TRUE);


-- ════════════════════════════════════════════════════════════
-- RPC 1: Token-basierter Unsubscribe (analog unsubscribe_with_token)
-- Wird aus landing/pages/unsubscribe.html mit ?type=daily aufgerufen.
-- Secret identisch zu shared/unsubscribe_token.py.
-- ════════════════════════════════════════════════════════════

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA extensions;

CREATE OR REPLACE FUNCTION daily_unsubscribe_with_token(
    p_email TEXT,
    p_token TEXT
)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, extensions, pg_temp
AS $$
DECLARE
    v_secret TEXT := 'seasonaledge-unsub-2026';
    v_expected TEXT;
    v_normalized TEXT;
    v_found BOOLEAN;
BEGIN
    IF p_email IS NULL OR p_token IS NULL THEN
        RETURN json_build_object('ok', false, 'error', 'missing_params');
    END IF;

    v_normalized := LOWER(TRIM(p_email));
    v_expected := SUBSTRING(
        ENCODE(extensions.digest(v_normalized || v_secret, 'sha256'), 'hex'),
        1, 16
    );

    IF LOWER(TRIM(p_token)) <> v_expected THEN
        RETURN json_build_object('ok', false, 'error', 'invalid_token');
    END IF;

    SELECT EXISTS(SELECT 1 FROM daily_subscribers WHERE email = v_normalized) INTO v_found;
    IF NOT v_found THEN
        RETURN json_build_object('ok', false, 'error', 'not_found');
    END IF;

    UPDATE daily_subscribers
    SET status = 'unsubscribed',
        no_emails = TRUE,
        unsubscribed_at = NOW(),
        updated_at = NOW()
    WHERE email = v_normalized;

    RETURN json_build_object('ok', true, 'email', v_normalized);
END;
$$;

GRANT EXECUTE ON FUNCTION daily_unsubscribe_with_token(TEXT, TEXT) TO anon;
GRANT EXECUTE ON FUNCTION daily_unsubscribe_with_token(TEXT, TEXT) TO authenticated;


-- ════════════════════════════════════════════════════════════
-- RPC 2 + 3: Profile-Toggle (analog get_my_newsletter_status / toggle_my_newsletter)
-- ════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION get_my_daily_status()
RETURNS JSON
LANGUAGE sql
SECURITY DEFINER
STABLE
SET search_path = public, pg_temp
AS $$
    WITH ae AS (
        SELECT LOWER(TRIM(COALESCE(auth.jwt() ->> 'email', ''))) AS email
    )
    SELECT CASE
        WHEN (SELECT email FROM ae) = '' THEN
            json_build_object('ok', false, 'error', 'not_authenticated')
        ELSE COALESCE(
            (SELECT json_build_object(
                        'ok', true,
                        'email', s.email,
                        'subscribed', (s.status = 'active' AND NOT COALESCE(s.no_emails, false)),
                        'status', s.status,
                        'subscribed_at', s.subscribed_at,
                        'unsubscribed_at', s.unsubscribed_at
                    )
             FROM daily_subscribers s, ae
             WHERE s.email = ae.email
             LIMIT 1),
            (SELECT json_build_object(
                        'ok', true,
                        'email', email,
                        'subscribed', false,
                        'status', 'none'
                    ) FROM ae)
        )
    END;
$$;


CREATE OR REPLACE FUNCTION toggle_my_daily(p_subscribe BOOLEAN)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    v_email TEXT := LOWER(TRIM(COALESCE(auth.jwt() ->> 'email', '')));
BEGIN
    IF v_email = '' THEN
        RETURN json_build_object('ok', false, 'error', 'not_authenticated');
    END IF;

    IF p_subscribe THEN
        INSERT INTO daily_subscribers (email, status, source, subscribed_at, no_emails, updated_at)
        VALUES (v_email, 'active', 'profile', NOW(), FALSE, NOW())
        ON CONFLICT (email) DO UPDATE
        SET status = 'active',
            no_emails = FALSE,
            unsubscribed_at = NULL,
            updated_at = NOW();
    ELSE
        INSERT INTO daily_subscribers (email, status, source, no_emails, unsubscribed_at, updated_at)
        VALUES (v_email, 'unsubscribed', 'profile', TRUE, NOW(), NOW())
        ON CONFLICT (email) DO UPDATE
        SET status = 'unsubscribed',
            no_emails = TRUE,
            unsubscribed_at = NOW(),
            updated_at = NOW();
    END IF;

    RETURN (
        SELECT json_build_object(
                   'ok', true,
                   'email', s.email,
                   'subscribed', (s.status = 'active' AND NOT COALESCE(s.no_emails, false)),
                   'status', s.status
               )
        FROM daily_subscribers s
        WHERE s.email = v_email
    );
END;
$$;

REVOKE EXECUTE ON FUNCTION get_my_daily_status()         FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION toggle_my_daily(BOOLEAN)      FROM PUBLIC;
GRANT EXECUTE ON FUNCTION get_my_daily_status()          TO authenticated;
GRANT EXECUTE ON FUNCTION toggle_my_daily(BOOLEAN)       TO authenticated;


-- ── Verifikation (manuell) ──────────────────────────────────
-- INSERT INTO daily_subscribers (email) VALUES ('heiko.seibel@gmail.com');
-- SELECT count(*) FROM daily_subscribers;
-- SELECT get_my_daily_status();      -- nach Login
-- SELECT toggle_my_daily(true);
-- SELECT toggle_my_daily(false);

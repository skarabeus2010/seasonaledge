-- ============================================================
-- scripts/create_unsubscribe_rpc.sql
-- ============================================================
-- PostgreSQL-Funktion für Token-basierten Unsubscribe.
--
-- Der Token wird client-seitig aus dem Weekly-Newsletter-Script
-- (shared/unsubscribe_token.py) generiert als:
--     SUBSTRING(SHA256(lower(email) || secret), 1, 16)
--
-- Diese Funktion validiert den Token serverseitig und setzt
-- status='unsubscribed' + no_emails=true nur bei Match.
--
-- Das Secret muss als Postgres-Settings gesetzt werden ODER via
-- app.settings extension. Für den Start: hardcoded Fallback
-- 'seasonaledge-unsub-2026' (identisch mit shared/unsubscribe_token.py
-- DEFAULT_SECRET).
--
-- WICHTIG: Secret an 3 Stellen synchron halten:
--   1. Env-Var UNSUBSCRIBE_SECRET auf dem Server
--   2. DEFAULT_SECRET in shared/unsubscribe_token.py
--   3. Der Default hier in dieser Funktion
-- ============================================================

CREATE OR REPLACE FUNCTION unsubscribe_with_token(
    p_email TEXT,
    p_token TEXT
)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    v_secret TEXT := 'seasonaledge-unsub-2026';
    v_expected TEXT;
    v_normalized TEXT;
    v_found BOOLEAN;
BEGIN
    -- 1. Eingaben normalisieren
    IF p_email IS NULL OR p_token IS NULL THEN
        RETURN json_build_object('ok', false, 'error', 'missing_params');
    END IF;

    v_normalized := LOWER(TRIM(p_email));

    -- 2. Erwarteten Token berechnen (erste 16 Hex-Zeichen von SHA-256)
    v_expected := SUBSTRING(
        ENCODE(DIGEST(v_normalized || v_secret, 'sha256'), 'hex'),
        1, 16
    );

    -- 3. Token prüfen
    IF LOWER(TRIM(p_token)) <> v_expected THEN
        RETURN json_build_object('ok', false, 'error', 'invalid_token');
    END IF;

    -- 4. Subscriber existiert?
    SELECT EXISTS(SELECT 1 FROM subscribers WHERE email = v_normalized) INTO v_found;
    IF NOT v_found THEN
        RETURN json_build_object('ok', false, 'error', 'not_found');
    END IF;

    -- 5. Unsubscribe durchführen
    UPDATE subscribers
    SET
        status = 'unsubscribed',
        no_emails = TRUE,
        unsubscribed_at = NOW(),
        updated_at = NOW()
    WHERE email = v_normalized;

    RETURN json_build_object('ok', true, 'email', v_normalized);
END;
$$;

-- ── Permissions ──────────────────────────────────────────────
-- Anon-Rolle darf die Funktion aufrufen (für unsubscribe.html ohne Login)
GRANT EXECUTE ON FUNCTION unsubscribe_with_token(TEXT, TEXT) TO anon;
GRANT EXECUTE ON FUNCTION unsubscribe_with_token(TEXT, TEXT) TO authenticated;

-- ── Verifikation (manuell in Supabase SQL-Editor nach Deploy) ───
-- SELECT unsubscribe_with_token('test@example.com', '64f0ba2b0c093da7');
-- Erwartung bei test@example.com + Default-Secret:
--   {"ok": false, "error": "not_found"}  (wenn Subscriber nicht in DB)
--   {"ok": true,  "email": "test@example.com"}  (wenn erfolgreich)

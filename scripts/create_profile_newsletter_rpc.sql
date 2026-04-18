-- ============================================================
-- scripts/create_profile_newsletter_rpc.sql
-- ============================================================
-- Newsletter-Toggle für die Profile-Seite.
--
-- Zwei Funktionen für authentifizierte User (Google OAuth):
--   - get_my_newsletter_status() liefert den Status
--   - toggle_my_newsletter(p_subscribe) setzt subscribed / unsubscribed
--
-- Die Email wird aus dem JWT (auth.jwt() ->> 'email') gelesen — kein
-- Parameter nötig, daher kann der User nur seinen eigenen Status toggeln.
-- Beide Funktionen laufen mit SECURITY DEFINER, der RLS-Bypass auf
-- `subscribers` ist damit bewusst auf genau diese zwei Operationen
-- für den eigenen Account limitiert.
--
-- In Supabase SQL-Editor ausführen.
-- ============================================================

CREATE OR REPLACE FUNCTION get_my_newsletter_status()
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    v_email  TEXT;
    v_result JSON;
BEGIN
    v_email := LOWER(TRIM(COALESCE(auth.jwt() ->> 'email', '')));
    IF v_email = '' THEN
        RETURN json_build_object('ok', false, 'error', 'not_authenticated');
    END IF;

    -- JSON direkt im SELECT bauen — vermeidet PL/pgSQL-Variablenreferenzen
    -- in json_build_object, die in Supabase-Postgres als Relationen geparst
    -- werden koennen ("relation v_xxx does not exist").
    SELECT json_build_object(
               'ok', true,
               'email', v_email,
               'subscribed', (s.status = 'active' AND NOT COALESCE(s.no_emails, false)),
               'status', s.status,
               'subscribed_at', s.subscribed_at,
               'unsubscribed_at', s.unsubscribed_at
           )
    INTO v_result
    FROM subscribers s
    WHERE s.email = v_email
    LIMIT 1;

    IF v_result IS NULL THEN
        v_result := json_build_object(
            'ok', true,
            'email', v_email,
            'subscribed', false,
            'status', 'none'
        );
    END IF;

    RETURN v_result;
END;
$$;


CREATE OR REPLACE FUNCTION toggle_my_newsletter(p_subscribe BOOLEAN)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    v_email  TEXT;
    v_exists BOOLEAN;
BEGIN
    v_email := LOWER(TRIM(COALESCE(auth.jwt() ->> 'email', '')));
    IF v_email = '' THEN
        RETURN '{"ok":false,"error":"not_authenticated"}'::json;
    END IF;

    SELECT EXISTS(SELECT 1 FROM subscribers WHERE email = v_email) INTO v_exists;

    IF p_subscribe THEN
        IF v_exists THEN
            UPDATE subscribers
            SET status = 'active',
                no_emails = FALSE,
                unsubscribed_at = NULL,
                updated_at = NOW()
            WHERE email = v_email;
        ELSE
            INSERT INTO subscribers (email, status, source, subscribed_at)
            VALUES (v_email, 'active', 'profile', NOW());
        END IF;
    ELSE
        IF v_exists THEN
            UPDATE subscribers
            SET status = 'unsubscribed',
                no_emails = TRUE,
                unsubscribed_at = NOW(),
                updated_at = NOW()
            WHERE email = v_email;
        END IF;
    END IF;

    -- Resultat aus der Tabelle zuruecklesen (vermeidet Variablen-Referenz
    -- in json_build_object, siehe get_my_newsletter_status).
    RETURN (
        SELECT json_build_object(
                   'ok', true,
                   'email', s.email,
                   'subscribed', (s.status = 'active' AND NOT COALESCE(s.no_emails, false)),
                   'status', s.status
               )
        FROM subscribers s
        WHERE s.email = v_email
    );
END;
$$;


-- ── Permissions ──────────────────────────────────────────────
-- Nur authentifizierte User (eingeloggt via Supabase Auth) dürfen rufen.
-- anon ist bewusst ausgeschlossen — Guest-Mode hat keine Profile-Seite.
REVOKE EXECUTE ON FUNCTION get_my_newsletter_status() FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION toggle_my_newsletter(BOOLEAN) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION get_my_newsletter_status() TO authenticated;
GRANT EXECUTE ON FUNCTION toggle_my_newsletter(BOOLEAN) TO authenticated;


-- ── Verifikation (manuell in Supabase SQL-Editor nach Login als Test-User) ───
-- SELECT get_my_newsletter_status();
-- SELECT toggle_my_newsletter(true);
-- SELECT toggle_my_newsletter(false);

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

-- Pure-SQL-Funktion — umgeht PL/pgSQL-Quirks mit SELECT-INTO-Variablen,
-- die in Supabase als "relation v_xxx does not exist" fehlschlagen.
CREATE OR REPLACE FUNCTION get_my_newsletter_status()
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
             FROM subscribers s, ae
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


CREATE OR REPLACE FUNCTION toggle_my_newsletter(p_subscribe BOOLEAN)
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
        INSERT INTO subscribers (email, status, source, subscribed_at, no_emails, updated_at)
        VALUES (v_email, 'active', 'profile', NOW(), FALSE, NOW())
        ON CONFLICT (email) DO UPDATE
        SET status = 'active',
            no_emails = FALSE,
            unsubscribed_at = NULL,
            updated_at = NOW();
    ELSE
        INSERT INTO subscribers (email, status, source, no_emails, unsubscribed_at, updated_at)
        VALUES (v_email, 'unsubscribed', 'profile', TRUE, NOW(), NOW())
        ON CONFLICT (email) DO UPDATE
        SET status = 'unsubscribed',
            no_emails = TRUE,
            unsubscribed_at = NOW(),
            updated_at = NOW();
    END IF;

    -- Resultat aus der Tabelle zuruecklesen. Keine PL/pgSQL-Variablen in
    -- json_build_object, nur Column-Referenzen.
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

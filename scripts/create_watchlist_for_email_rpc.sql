-- ════════════════════════════════════════════════════════════
-- scripts/create_watchlist_for_email_rpc.sql
-- ════════════════════════════════════════════════════════════
-- RPC zum Lesen der Watchlist eines Users via Email — für Server-side
-- Newsletter-Personalisierung. SECURITY DEFINER, weil auth.users sonst
-- nicht aus public-Code zugreifbar ist.
--
-- Permission: nur service_role darf rufen (kein anon/authenticated),
-- damit kein User die Watchlist eines anderen lesen kann.
-- ════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION get_watchlist_by_email(p_email TEXT)
RETURNS JSON
LANGUAGE sql
SECURITY DEFINER
STABLE
SET search_path = public, auth, pg_temp
AS $$
    WITH u AS (
        SELECT id FROM auth.users
        WHERE LOWER(email) = LOWER(TRIM(p_email))
        LIMIT 1
    )
    SELECT COALESCE(
        json_agg(
            json_build_object(
                'ticker',    w.ticker,
                'note',      w.note,
                'added_at',  w.added_at
            )
            ORDER BY w.added_at DESC
        ),
        '[]'::json
    )
    FROM user_watchlists w
    WHERE w.user_id = (SELECT id FROM u);
$$;

REVOKE EXECUTE ON FUNCTION get_watchlist_by_email(TEXT) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION get_watchlist_by_email(TEXT) FROM anon;
REVOKE EXECUTE ON FUNCTION get_watchlist_by_email(TEXT) FROM authenticated;
GRANT EXECUTE ON FUNCTION get_watchlist_by_email(TEXT) TO service_role;

-- Verifikation (manuell, mit service-role-Key):
-- SELECT get_watchlist_by_email('heiko.seibel@gmail.com');

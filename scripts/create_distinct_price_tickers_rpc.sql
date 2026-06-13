-- SeasonAlpha: RPC für den Orphan-Detektor im Vollständigkeits-Audit
-- Run einmalig im Supabase SQL Editor.
--
-- Zweck: liefert die distinct Ticker aus prices SERVER-SEITIG (Index-Scan,
-- kein PostgREST-Full-Scan → kein statement timeout). check_db_completeness.py
-- gleicht das gegen shared/symbols.py ab und meldet "Orphans" — Ticker mit
-- Preisdaten, die NICHT in der Registry stehen (würden weder auditiert noch
-- refreshed → veralten still, wie SMH 2026-04..06).

-- WICHTIG: `SELECT DISTINCT ticker FROM prices` macht einen Full-Scan über die
-- Millionen-Zeilen-Tabelle und timeoutet (57014). Stattdessen Loose-Index-Scan
-- (Skip-Scan) per rekursivem CTE über den (ticker,date)-Index — springt von
-- Distinct-Wert zu Distinct-Wert, O(#ticker · log n).
CREATE OR REPLACE FUNCTION public.distinct_price_tickers()
RETURNS TABLE(ticker text)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  WITH RECURSIVE walk AS (
    (SELECT p.ticker FROM prices p ORDER BY p.ticker LIMIT 1)
    UNION ALL
    SELECT (SELECT p.ticker FROM prices p WHERE p.ticker > walk.ticker
            ORDER BY p.ticker LIMIT 1)
    FROM walk
    WHERE walk.ticker IS NOT NULL
  )
  SELECT walk.ticker FROM walk WHERE walk.ticker IS NOT NULL ORDER BY walk.ticker
$$;

GRANT EXECUTE ON FUNCTION public.distinct_price_tickers() TO anon, authenticated, service_role;

NOTIFY pgrst, 'reload schema';

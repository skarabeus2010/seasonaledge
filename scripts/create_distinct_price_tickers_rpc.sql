-- SeasonAlpha: RPC für den Orphan-Detektor im Vollständigkeits-Audit
-- Run einmalig im Supabase SQL Editor.
--
-- Zweck: liefert die distinct Ticker aus prices SERVER-SEITIG (Index-Scan,
-- kein PostgREST-Full-Scan → kein statement timeout). check_db_completeness.py
-- gleicht das gegen shared/symbols.py ab und meldet "Orphans" — Ticker mit
-- Preisdaten, die NICHT in der Registry stehen (würden weder auditiert noch
-- refreshed → veralten still, wie SMH 2026-04..06).

CREATE OR REPLACE FUNCTION public.distinct_price_tickers()
RETURNS TABLE(ticker text)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT DISTINCT ticker FROM prices ORDER BY ticker
$$;

GRANT EXECUTE ON FUNCTION public.distinct_price_tickers() TO anon, authenticated, service_role;

NOTIFY pgrst, 'reload schema';

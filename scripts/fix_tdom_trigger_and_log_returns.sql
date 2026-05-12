-- =============================================================================
-- Fix 1: moddatetime-Trigger auf tdom_stats + tdoy_stats
-- Ohne diesen Trigger bleibt updated_at auf dem INSERT-Datum stehen.
-- _is_stale() gibt dann immer True zurück → Nightly recomputed alle Stats
-- unnötig bei jedem Lauf (~30% Zeitverlust pro Run).
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS moddatetime SCHEMA extensions;

DROP TRIGGER IF EXISTS handle_updated_at ON tdom_stats;
CREATE TRIGGER handle_updated_at
  BEFORE UPDATE ON tdom_stats
  FOR EACH ROW EXECUTE FUNCTION extensions.moddatetime(updated_at);

DROP TRIGGER IF EXISTS handle_updated_at ON tdoy_stats;
CREATE TRIGGER handle_updated_at
  BEFORE UPDATE ON tdoy_stats
  FOR EACH ROW EXECUTE FUNCTION extensions.moddatetime(updated_at);

-- Nach dem Trigger-Anlegen: updated_at aller alten Stats auf gestern setzen
-- → zwingt den nächsten Nightly zu einem einmaligen Recompute, danach stabil.
UPDATE tdom_stats SET updated_at = NOW() - INTERVAL '1 day'
WHERE updated_at < NOW() - INTERVAL '7 days';

UPDATE tdoy_stats SET updated_at = NOW() - INTERVAL '1 day'
WHERE updated_at < NOW() - INTERVAL '7 days';

-- =============================================================================
-- Fix 2: log_return für DAX ^GDAXI Mai 5 + Mai 6
-- ln(close_t / close_{t-1}) — Rows waren NULL obwohl Kurse vorhanden
-- Mai 5: ln(24401.70 / 23991.27) = 0.01696760
-- Mai 6: ln(24918.69 / 24401.70) = 0.02096835
-- =============================================================================

-- Mai 5
UPDATE prices p
SET log_return = LN(p.close / prev.close)
FROM (SELECT close FROM prices WHERE ticker = '^GDAXI' AND date = '2026-05-04') AS prev
WHERE p.ticker = '^GDAXI'
  AND p.date  = '2026-05-05'
  AND p.log_return IS NULL;

-- Mai 6
UPDATE prices p
SET log_return = LN(p.close / prev.close)
FROM (SELECT close FROM prices WHERE ticker = '^GDAXI' AND date = '2026-05-05') AS prev
WHERE p.ticker = '^GDAXI'
  AND p.date  = '2026-05-06'
  AND p.log_return IS NULL;

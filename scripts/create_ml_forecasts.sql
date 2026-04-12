-- ============================================================
-- ml_forecasts: Pre-computed ML Model Results
-- ============================================================
-- Speichert Ergebnisse von Chronos, MSTL, NeuralProphet
-- pro Ticker. Wird vom Nightly-Refresh (Phase G) befüllt.
--
-- Ausführen im Supabase SQL Editor:
--   https://supabase.com/dashboard/project/dkrebzobcwxyagximuxy/sql
-- ============================================================

-- 1. Tabelle anlegen
CREATE TABLE IF NOT EXISTS ml_forecasts (
    ticker TEXT NOT NULL,
    model TEXT NOT NULL,              -- 'chronos' | 'mstl' | 'neuralprophet'
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data JSONB NOT NULL,              -- Modell-spezifische Ergebnisse
    PRIMARY KEY (ticker, model)
);

-- 2. Index für schnelle Abfragen
CREATE INDEX IF NOT EXISTS idx_ml_forecasts_model ON ml_forecasts (model);
CREATE INDEX IF NOT EXISTS idx_ml_forecasts_computed ON ml_forecasts (computed_at DESC);

-- 3. RLS aktivieren + anon darf lesen
ALTER TABLE ml_forecasts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_read_ml_forecasts" ON ml_forecasts;
CREATE POLICY "anon_read_ml_forecasts" ON ml_forecasts
    FOR SELECT USING (true);

-- 4. Schreib-Zugriff für den Service-Role (Nightly-Script)
GRANT ALL ON ml_forecasts TO authenticated;
GRANT ALL ON ml_forecasts TO service_role;

-- 5. Kommentar
COMMENT ON TABLE ml_forecasts IS 'Pre-computed ML forecasts (Chronos, MSTL, NeuralProphet) für KI-Saisonalität + Dashboard';
COMMENT ON COLUMN ml_forecasts.model IS 'chronos = 30d probabilistischer Forecast, mstl = saisonale Dekomposition, neuralprophet = gelernte Saisonalitäts-Komponenten';
COMMENT ON COLUMN ml_forecasts.data IS 'JSON mit modell-spezifischen Ergebnissen (Forecast-Arrays, Stärke-Metriken, Komponenten)';

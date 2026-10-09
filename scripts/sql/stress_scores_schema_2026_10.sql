-- SeasonAlpha — Stress-Ampel: versionierte Läufe (Plan docs/review_prompts/2026-10-09_stress_ampel_plan.md, v5)
--
-- IM SUPABASE-SQL-EDITOR AUSFÜHREN (SeasonAlpha-Projekt, nicht das Schwesterprojekt). Einmal; wiederholtes
-- Ausführen ist unschädlich (IF NOT EXISTS / CREATE OR REPLACE).
--
-- REIN ERGÄNZEND: zwei neue Tabellen, ein Index, drei Funktionen. `regime_scores` (alte Isolation-Forest-Werte,
-- Vorzeichen vertauscht) wird weder verändert noch gelöscht — sie ist die Sicherung des alten Stands und wird nach
-- dem Deploy von keinem Code mehr gelesen oder geschrieben. Löschen bleibt eine spätere Entscheidung.
--
-- Prinzip: Jeder Schreiblauf ist ein Vollauf mit eigener lauf_id. Sichtbar ist nur der jüngste Lauf mit
-- status = 'fertig'. Höchstens ein Lauf je Ticker darf 'laeuft' sein (Unique-Index, von der Datenbank erzwungen).
-- Veröffentlichen gelingt nur, solange der eigene Lauf noch 'laeuft' und seine Lease nicht abgelaufen ist; ein
-- verdrängter Prozess kann daher nie sichtbar werden. Ein fertiger Lauf wird nie mehr verändert.

BEGIN;

CREATE TABLE IF NOT EXISTS stress_laeufe (
    lauf_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker         TEXT NOT NULL,
    status         TEXT NOT NULL CHECK (status IN ('laeuft', 'fertig', 'abgebrochen')),
    gestartet_am   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    laeuft_bis     TIMESTAMPTZ NOT NULL,
    fertig_am      TIMESTAMPTZ,
    n_kurse        INTEGER,
    n_scores       INTEGER,
    erstes_datum   DATE,
    letztes_datum  DATE,
    kurse_bis      DATE,
    kurse_hash     TEXT,
    methode        TEXT NOT NULL DEFAULT 'stress_v1'
);

-- höchstens ein laufender Lauf je Ticker
CREATE UNIQUE INDEX IF NOT EXISTS stress_laeufe_ein_laufender ON stress_laeufe (ticker) WHERE status = 'laeuft';
CREATE INDEX IF NOT EXISTS stress_laeufe_fertig ON stress_laeufe (ticker, status, fertig_am DESC);

CREATE TABLE IF NOT EXISTS stress_scores (
    lauf_id     UUID NOT NULL REFERENCES stress_laeufe (lauf_id),
    ticker      TEXT NOT NULL,
    date        DATE NOT NULL,
    score       DOUBLE PRECISION,           -- 0–100, Rang gegen bis zu 2520 frühere Tage; NULL = zu kurze Historie
    ampel       TEXT NOT NULL,              -- green / yellow / red / grey, aus dem ungerundeten Score
    s           DOUBLE PRECISION,           -- Stress-Maß 0,3·vol5 + 0,3·vol20 + 0,4·|dd20|
    vol5        DOUBLE PRECISION,
    vol10       DOUBLE PRECISION,
    vol20       DOUBLE PRECISION,
    dd20        DOUBLE PRECISION,
    ret1d       DOUBLE PRECISION,
    ret5d       DOUBLE PRECISION,
    ret20d      DOUBLE PRECISION,
    referenz_n  INTEGER,
    PRIMARY KEY (lauf_id, date)
);
CREATE INDEX IF NOT EXISTS stress_scores_ticker ON stress_scores (ticker, lauf_id, date);

-- RLS: lesen öffentlich (wie regime_scores), schreiben nur service_role
ALTER TABLE stress_laeufe ENABLE ROW LEVEL SECURITY;
ALTER TABLE stress_scores ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "anon_read_stress_laeufe" ON stress_laeufe;
DROP POLICY IF EXISTS "anon_read_stress_scores" ON stress_scores;
DROP POLICY IF EXISTS "service_write_stress_laeufe" ON stress_laeufe;
DROP POLICY IF EXISTS "service_write_stress_scores" ON stress_scores;
CREATE POLICY "anon_read_stress_laeufe" ON stress_laeufe FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read_stress_scores" ON stress_scores FOR SELECT TO anon USING (true);
CREATE POLICY "service_write_stress_laeufe" ON stress_laeufe FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_write_stress_scores" ON stress_scores FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Lauf starten: abgelaufene Leases dieses Tickers abbrechen, dann neuen Lauf anlegen (30 min Lease).
-- Gibt NULL zurück, wenn ein gültiger Lauf existiert (Unique-Index).
CREATE OR REPLACE FUNCTION stress_lauf_starten(p_ticker TEXT) RETURNS UUID
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE v_id UUID;
BEGIN
    UPDATE stress_laeufe SET status = 'abgebrochen'
     WHERE ticker = p_ticker AND status = 'laeuft' AND laeuft_bis < NOW();
    BEGIN
        INSERT INTO stress_laeufe (ticker, status, laeuft_bis)
        VALUES (p_ticker, 'laeuft', NOW() + INTERVAL '30 minutes')
        RETURNING lauf_id INTO v_id;
    EXCEPTION WHEN unique_violation THEN
        RETURN NULL;
    END;
    RETURN v_id;
END $$;

-- Veröffentlichen: nur der eigene, noch laufende Lauf mit gültiger Lease; sonst false.
CREATE OR REPLACE FUNCTION stress_lauf_veroeffentlichen(
    p_lauf UUID, p_n INTEGER, p_erstes DATE, p_letztes DATE, p_kurse_bis DATE, p_n_kurse INTEGER, p_hash TEXT
) RETURNS BOOLEAN
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE v_anz INTEGER;
BEGIN
    UPDATE stress_laeufe
       SET status = 'fertig', fertig_am = NOW(), n_scores = p_n, erstes_datum = p_erstes, letztes_datum = p_letztes,
           kurse_bis = p_kurse_bis, n_kurse = p_n_kurse, kurse_hash = p_hash
     WHERE lauf_id = p_lauf AND status = 'laeuft' AND laeuft_bis > NOW();
    GET DIAGNOSTICS v_anz = ROW_COUNT;
    RETURN v_anz = 1;
END $$;

-- Abbrechen: ausschließlich laeuft → abgebrochen; ein fertiger Lauf bleibt unverändert.
CREATE OR REPLACE FUNCTION stress_lauf_abbrechen(p_lauf UUID) RETURNS BOOLEAN
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE v_anz INTEGER;
BEGIN
    UPDATE stress_laeufe SET status = 'abgebrochen' WHERE lauf_id = p_lauf AND status = 'laeuft';
    GET DIAGNOSTICS v_anz = ROW_COUNT;
    RETURN v_anz = 1;
END $$;

REVOKE ALL ON FUNCTION stress_lauf_starten(TEXT) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION stress_lauf_veroeffentlichen(UUID, INTEGER, DATE, DATE, DATE, INTEGER, TEXT) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION stress_lauf_abbrechen(UUID) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION stress_lauf_starten(TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION stress_lauf_veroeffentlichen(UUID, INTEGER, DATE, DATE, DATE, INTEGER, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION stress_lauf_abbrechen(UUID) TO service_role;

COMMIT;

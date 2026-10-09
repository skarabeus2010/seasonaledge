-- scripts/sql/scanner_saison_score_2026_10.sql
--
-- Saison-Score (Nachfolger des „KI-Score"), Plan v1–v3 mit Codex-Freigabe 2026-10-09, Abschnitt D3.
-- REIN ERGÄNZEND und idempotent. Im SeasonAlpha-SQL-Editor ausführen (NICHT im Projekt des Schwesterprojekts).
--
-- 1) scanner_results: Score und Signal dürfen NULL sein (nicht berechenbare Ticker werden als Zeile mit Status und
--    Grund gespeichert, Richtungsetiketten gibt es nicht mehr); neue Spalten für Methode, Status, Grund, Bausteine,
--    Datenstand. Alte Zeilen (methode IS NULL) bleiben unangetastet und werden von keinem Leser mehr verwendet.
-- 2) saison_score_protokoll: unveränderliches Protokoll für die prospektive Bestätigung (frühestens 2027-10).
--    Nur INSERT; je (methode, ticker, as_of) zählt der ERSTE Lauf. Kein UPDATE/DELETE — auch nicht für service_role
--    (Tabellenrecht entzogen UND Trigger, weil service_role RLS umgeht).

BEGIN;

-- ── 1) scanner_results ──────────────────────────────────────────────────────
ALTER TABLE scanner_results ALTER COLUMN score  DROP NOT NULL;
ALTER TABLE scanner_results ALTER COLUMN signal DROP NOT NULL;
ALTER TABLE scanner_results ADD COLUMN IF NOT EXISTS methode   TEXT;
ALTER TABLE scanner_results ADD COLUMN IF NOT EXISTS status    TEXT;
ALTER TABLE scanner_results ADD COLUMN IF NOT EXISTS grund     TEXT;
ALTER TABLE scanner_results ADD COLUMN IF NOT EXISTS bausteine JSONB;
ALTER TABLE scanner_results ADD COLUMN IF NOT EXISTS as_of     DATE;
DO $$ BEGIN
  ALTER TABLE scanner_results ADD CONSTRAINT scanner_results_status_chk
    CHECK (status IS NULL OR status IN ('ok', 'nicht_berechenbar'));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  -- eine neue Zeile ist entweder berechnet (Score da) oder trägt einen Grund
  ALTER TABLE scanner_results ADD CONSTRAINT scanner_results_status_score_chk
    CHECK (methode IS NULL OR (status = 'ok' AND score IS NOT NULL) OR (status = 'nicht_berechenbar' AND score IS NULL AND grund IS NOT NULL));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
CREATE INDEX IF NOT EXISTS idx_scanner_results_methode_datum ON scanner_results (methode, scan_date);

-- ── 2) saison_score_protokoll ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS saison_score_protokoll (
    protokoll_id  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    methode       TEXT        NOT NULL,
    code_version  TEXT        NOT NULL,     -- Git-Kurz-SHA des Containers
    erstellt_am   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ticker        TEXT        NOT NULL,
    as_of         DATE        NOT NULL,
    kurse_bis     DATE        NOT NULL,
    kurse_hash    TEXT        NOT NULL,
    status        TEXT        NOT NULL CHECK (status IN ('ok', 'nicht_berechenbar')),
    grund         TEXT,
    score         DOUBLE PRECISION,
    bausteine     JSONB,
    UNIQUE (methode, ticker, as_of)
);

ALTER TABLE saison_score_protokoll ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON saison_score_protokoll FROM PUBLIC, anon, authenticated;
REVOKE UPDATE, DELETE, TRUNCATE ON saison_score_protokoll FROM service_role;
GRANT SELECT, INSERT ON saison_score_protokoll TO service_role;

CREATE OR REPLACE FUNCTION saison_score_protokoll_unveraenderlich() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'saison_score_protokoll ist unveränderlich (% verweigert)', TG_OP;
END $$;
DROP TRIGGER IF EXISTS saison_score_protokoll_sperre ON saison_score_protokoll;
CREATE TRIGGER saison_score_protokoll_sperre BEFORE UPDATE OR DELETE ON saison_score_protokoll
  FOR EACH ROW EXECUTE FUNCTION saison_score_protokoll_unveraenderlich();

COMMIT;

NOTIFY pgrst, 'reload schema';

-- ── Abnahme (alle erwartet wie angegeben) ───────────────────────────────────
-- a) score/signal nullable (erwartet: YES, YES)
SELECT column_name, is_nullable FROM information_schema.columns
 WHERE table_name = 'scanner_results' AND column_name IN ('score', 'signal') ORDER BY column_name;
-- b) neue Spalten vorhanden (erwartet: 5)
SELECT count(*) FROM information_schema.columns
 WHERE table_name = 'scanner_results' AND column_name IN ('methode', 'status', 'grund', 'bausteine', 'as_of');
-- c) Rechte service_role auf dem Protokoll (erwartet: INSERT, SELECT — kein UPDATE/DELETE/TRUNCATE)
SELECT privilege_type FROM information_schema.role_table_grants
 WHERE table_name = 'saison_score_protokoll' AND grantee = 'service_role' ORDER BY privilege_type;
-- d) anon/authenticated ohne Rechte (erwartet: keine Zeile)
SELECT grantee, privilege_type FROM information_schema.role_table_grants
 WHERE table_name = 'saison_score_protokoll' AND grantee IN ('anon', 'authenticated');

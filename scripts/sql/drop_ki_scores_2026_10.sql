-- scripts/sql/drop_ki_scores_2026_10.sql
--
-- Löscht die Tabelle `ki_scores` (alter „KI-Composite-Score", ersetzt durch den Saison-Score; Validierung ohne
-- Vorhersagekraft, Rangkorrelation 0,019). Nutzerentscheidung 2026-10-09.
-- Nachfolger: `scanner_results` mit methode = 'saison_v1' + `saison_score_protokoll`
-- (scripts/sql/scanner_saison_score_2026_10.sql).
--
-- Seit Commit 2b37d85 liest und schreibt kein Code die Tabelle mehr (ki_score.py, ai_models.py, computeKiScore
-- gelöscht; Vollständigkeitsprüfung zählt sie nicht mehr).
--
-- Bewusst OHNE CASCADE: hängt noch eine View oder Funktion an der Tabelle, bricht der Befehl ab und nennt das
-- abhängige Objekt — dann erst nachsehen, nicht blind mitlöschen. Die Lese-Policy `anon_read` gehört zur Tabelle
-- und verschwindet mit ihr.
-- Im SeasonAlpha-SQL-Editor ausführen (NICHT im Projekt des Schwesterprojekts).

-- 1. Vorher: abhängige Views (erwartet: keine Zeile)
SELECT dependent_view.relname AS abhaengig
FROM pg_depend
JOIN pg_rewrite ON pg_depend.objid = pg_rewrite.oid
JOIN pg_class AS dependent_view ON pg_rewrite.ev_class = dependent_view.oid
JOIN pg_class AS source_table ON pg_depend.refobjid = source_table.oid
WHERE source_table.relname = 'ki_scores' AND dependent_view.relname <> 'ki_scores';

-- 2. Löschen
DROP TABLE IF EXISTS public.ki_scores;

-- 3. PostgREST-Schema neu laden (sonst kennt die REST-Schicht die Tabelle noch aus dem Speicher)
NOTIFY pgrst, 'reload schema';

-- 4. Abnahme (erwartet: false)
SELECT to_regclass('public.ki_scores') IS NOT NULL AS ki_scores_existiert;

-- scripts/sql/drop_regime_scores_2026_10.sql
--
-- Löscht die Tabelle `regime_scores` (alte „Crash-Ampel": Isolation Forest, Vorzeichen vertauscht —
-- Lehman 15.10.2008 und Corona 16.03.2020 standen dort auf 0/grün). Nutzerentscheidung 2026-10-09.
-- Nachfolger: `stress_laeufe` / `stress_scores` (scripts/sql/stress_scores_schema_2026_10.sql).
--
-- Seit Commit 85f212b liest und schreibt kein Code die Tabelle mehr; seit diesem Commit steht die Ampel
-- auch in keiner Mail mehr.
--
-- Bewusst OHNE CASCADE: hängt noch eine View, Funktion oder Policy an der Tabelle, bricht der Befehl ab
-- und nennt das abhängige Objekt — dann erst nachsehen, nicht blind mitlöschen.
-- Im SeasonAlpha-SQL-Editor ausführen (NICHT im Projekt des Schwesterprojekts).

-- 1. Vorher: abhängige Objekte (erwartet: keine Zeile)
SELECT dependent_view.relname AS abhaengig
FROM pg_depend
JOIN pg_rewrite ON pg_depend.objid = pg_rewrite.oid
JOIN pg_class AS dependent_view ON pg_rewrite.ev_class = dependent_view.oid
JOIN pg_class AS source_table ON pg_depend.refobjid = source_table.oid
WHERE source_table.relname = 'regime_scores' AND dependent_view.relname <> 'regime_scores';

-- 2. Löschen
DROP TABLE IF EXISTS public.regime_scores;

-- 3. PostgREST-Schema neu laden (sonst kennt die REST-Schicht die Tabelle noch aus dem Speicher)
NOTIFY pgrst, 'reload schema';

-- 4. Abnahme (erwartet: false)
SELECT to_regclass('public.regime_scores') IS NOT NULL AS regime_scores_existiert;

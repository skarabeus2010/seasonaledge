# Code-Review Runde 1: Präsidentenzyklus-Signifikanz + Jahresende (Umsetzung von Plan v3)

Read-only, Repo `C:\dev\Seasonaledge`, **Arbeitsbaum** (nicht committet) gegen `HEAD` `1e84da2`. `git diff` zeigt alles.
Plan: `docs/review_prompts/2026-10-13_zyklus_signifikanz_plan_v3.md` (deine Freigabe Runde 3).
Wirkungsbericht: `docs/review_prompts/2026-10-13_zyklus_signifikanz_wirkung.md`.
Deutsch, echte Umlaute, Datei:Zeile, am Ende **FREIGABE (Code): ja/nein**.

## Geändert
- `shared/calculations.py`: `year_end_reference` entfernt, `year_covers(yd, end_day, jahr, stichtag_jahr)`,
  `calculate_period_stats(…, stichtag_jahr=None)`.
- `landing/js/seasonal-compute.js`: `yearEndRef` entfernt, `yearCovers(yd, endDoy, jahr, stichtagJahr)`.
- `landing/js/significance.js`: `runSignificanceTest(groups, testValue, opts)` liefert `{name,n,zu_wenig}`,
  `renderSection(…, opts)` + `_karteZuWenig`.
- `landing/pages/jahreszyklus.html`: Builder über `SA.seasonal._interpolateTo365`, `periodStats(…, stichtagJahr)`,
  `buildMonthlyHeatmap(yearData, stichtag)` (Abdeckung + Kalendermonat), `JZ.renderSignificance(…, stichtagJahr)`
  mit immer vier Zyklusgruppen, `JZ.stichtag()` einmal je Darstellung durchgereicht.
- `landing/pages/risikozyklus.html`: Builder über die gemeinsame Interpolation, `last_actual_day` geklammert.
- `blog/blog_builder.py`: Heatmap/Monatsmittel mit `stichtag`, `.items()`, None-Beschriftung.
- i18n: `sig.not_evaluated/min_required/required/unit_obs` (de+en), `jz.sig_no_data/sig_unit_years` (en),
  `_JSON_VER` v15.
- Wächter: `scripts/js/zyklus_probe.js` (neu), `verify_seasonal_twins.py` Block 7 + Python-Fälle + Blog-Fall,
  alter Block 6 in `twin_probe.js` entfernt; `verify_twins_mutation.py` 32 Mutationen (alle erkannt).
- Deploy-Vorlagen `scripts/fixtures/kurse_vorher/pages/{jahreszyklus,risikozyklus}.html` nachgezogen
  (`verify_seiten_kurse` 313 bestanden).

## Prüffragen
1. Setzt der Code Plan v3 vollständig und korrekt um (B1–B9)? Fehler, Lücken, Abweichungen?
2. Gibt es Aufrufer von `yearCovers`/`year_covers`/`yearEndRef`/`year_end_reference`/`runSignificanceTest`/
   `renderSection`, die ich übersehen habe (auch EN-Build, andere Seiten, Skripte)?
3. Prüft der Wächter die Wirkung (nicht nur Text)? Fehlende Mutationen?
4. Ist der Wirkungsbericht als Gate ausreichend und stimmig? Auffällig: die laufende Monatszelle der Heatmap
   (Oktober 2026) verschwindet — gewollt laut B6.

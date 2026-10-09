# Code-Review Saison-Score D3/D4 + Migration — Runde 3

Read-only, Repo `C:\dev\Seasonaledge`, uncommitteter Arbeitsbaum. Deine Runde 2:
`docs/review_prompts/2026-10-09_saison_score_d3d4_antwort2.md` (10 bestätigt, 2 Befunde, FREIGABE nein).
Deutsch, echte Umlaute, Datei:Zeile, am Ende **FREIGABE: ja/nein**.

## Korrekturen

1. **Rangfolge beim Zusammenführen** (`landing/js/decade-compute.js`, `mitHistorie`): Die Vollhistorie aus
   `SA.fetchAllPrices(ticker)` gewinnt an jedem Tag, den sie enthält; die übergebenen Zeilen werden nur
   angehängt, wenn ihr Datum NACH dem letzten Tag der Vollhistorie liegt. Damit kann ein älterer Zeitraum-Cache
   keinen korrigierten Kurs überschreiben, und der Regler wirkt nur noch, falls die Zeitraumabfrage jüngere Tage
   hat als die Vollhistorie (dann ist sie die frischere Quelle). Node-Probe mit Stub: Überlappung → Wert der
   Vollhistorie, jüngerer Tag angehängt, Ladefehler und leere Antwort lehnen ab.
2. **Abgleich nach dem Schreiben** (`shared/saison_score_betrieb.py`, `schreibe`): erst Protokoll-Insert
   (Konflikt → nichts), dann Rücklesen des gespeicherten Eintrags und Vergleich in
   `kurse_hash/status/score/code_version`; fehlt der Eintrag nach dem Schreiben → `RuntimeError` (Lauf rot).
   Danach Scanner-Upsert. Damit meldet auch der zweite von zwei gleichzeitigen Writern seine Abweichung.

Bitte prüfe außerdem, ob der Rücklesevergleich bei `score` an der Transportgenauigkeit scheitern kann
(PostgREST liefert double precision auf 15 signifikante Stellen; Spaltentyp siehe Migration) und ob
`code_version` als Abgleichfeld einen Fehlalarm bei jedem Code-Update erzeugt (das wäre gewollt: eine neue
Code-Version mit gleichem `as_of` IST eine Abweichung, die erste Zeile bleibt).

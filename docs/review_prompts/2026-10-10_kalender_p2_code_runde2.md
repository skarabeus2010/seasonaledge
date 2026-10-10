# P2 Schreiber — Code-Review Runde 2 (Abnahme)

Runde 1: [Prompt](2026-10-10_kalender_p2_code.md) · [Antwort](2026-10-10_kalender_p2_code_antwort1.md) — keine Freigabe.

<task>Prüfe, ob die drei Befunde behoben sind und nichts Neues kaputtging. Read-only. `git diff` + neue Dateien.</task>

## Umsetzung
1. **[P1] Gemischter Upsert** — Korrektur beim **Erzeuger**: `shared/supabase_client.upsert_prices` gruppiert die
   Datensätze nach ihrem Spaltensatz (`frozenset(keys)`) und sendet jede Gruppe als eigene Anfrage. Damit enthält
   keine Anfrage eine Spalte, die nicht alle ihre Datensätze tragen; nicht gesendete Spalten bleiben unverändert
   (schützt auch `open/high/low` bei Yahoo-NaN, das vorher gemischt gesendet wurde). Onboarding unverändert
   (Bestandszeilen ohne tdom/tdoy).
   Wächter: läuft jetzt über das **echte** `upsert_prices`; der Client-Stub bildet PostgREST nach (Spaltenliste =
   Vereinigung aller Schlüssel der Anfrage, fehlende Werte NULL, merge-duplicates in eine gespeicherte Tabelle).
   Neue Prüfung „Onboarding Bestand behält seine Nummern (echter Transport)“ mit Marke (99, 999) auf 1100
   Bestandszeilen. Mit dem alten `upsert_prices` (per `git stash`): **100 Bestandszeilen → (None, None)**, rot.
2. **[P2] Exakte Schreibmenge**: `vergleiche(..., soll_daten=...)` prüft die vollständige, unabhängig festgelegte
   Datumsliste (sortiert, mit Duplikaten) — Nightly (Fenster aus den Testdaten, nicht aus den Records), Lücke,
   Intraday, Onboarding, Lückenfüller. Onboarding jetzt mit 1593 Zeilen: 1100 Bestand (Lesen über 1000er-Seiten),
   4 Chunks, Teilfehler in Anfrage 3 → `ok=False`, `rows == 1593 − 500`. Neue Mutation „Nightly schreibt nur die
   letzte Zeile“ → gefangen.
3. **[P2] Abstürze über die Klasse**: `sys.monitoring` (RAISE) über die acht Schreiber-/Kalenderdateien; gewertet
   wird nur der **Ursprung** einer Ausnahme (erstes Auftreten — RAISE feuert in jedem Frame der Propagation; ein
   Stub-Fehler aus dieser Datei, der durch `upsert_prices` läuft, ist kein Absturz). Erlaubt: `ValueError`,
   `StopIteration`. Regex auf die Ausgabe entfernt. Gegenproben (abgefangen) in Onboarding, Intraday,
   Nightly-Lückenfüller, `backfill_tdoy` + ein nicht abgefangener → alle richtig verworfen. Saison-Stub im
   Nightly wirft jetzt `ValueError` statt einen `TypeError` in der Produktivdatei auszulösen.
Ergebnis: Wächter **35/35** (auch in leerer 3.12-Umgebung mit numpy/pandas/tzdata); Mutationen **20/20** in zwei
Läufen; Gegenproben **6/6**. Fehlerweitergabe 15/15.

## Fragen
1. Befunde behoben? 2. Hat die Gruppierung in `upsert_prices` Nebenwirkungen für andere Aufrufer (Reihenfolge,
Teilerfolg bei mehreren Gruppen, Leistung)? 3. Sonst etwas vor dem Commit?

## Ausgabevertrag
**Urteil** · **Befunde** · **Antworten**. ≤ 40 Zeilen.

# P2 Schreiber — Code-Review Runde 3 (Abnahme)

Runde 2: [Prompt](2026-10-10_kalender_p2_code_runde2.md) · [Antwort](2026-10-10_kalender_p2_code_antwort2.md) — Freigabe mit Auflage.

<task>Prüfe, ob die Auflage erfüllt ist und nichts Neues kaputtging. Read-only. `git diff` + neue Dateien.</task>

## Umsetzung
- `shared/supabase_client.upsert_prices`: scheitert eine Gruppe, wird `UpsertTeilfehler(geschrieben, ursache)` (Unterklasse
  von `RuntimeError`, `raise … from e`) mit der Zahl der davor **bestätigten** Datensätze geworfen.
  `backfill_new_ticker` und `fix_missing_days` zählen `getattr(e, "geschrieben", 0)` im Fehlerzweig mit.
- Wächter: neue Prüfung „Onboarding Teilfehler in einer Chunk-Gruppe zählt den bestätigten Teil“ — Chunk 3 (Zeilen
  1000–1499) zerfällt in Bestand (100, ohne Nummern) und neue Zeilen (400); nur die zweite Anfrage scheitert
  (`fehler_wenn` über die Datensätze) → `ok=False`, `rows == len − 400`. Mutationen: „upsert_prices meldet den
  bestätigten Teil nicht“ (`UpsertTeilfehler(0, e)`) und „Onboarding zählt den bestätigten Teil nicht“ — beide gefangen.
  Die Mutation „mischt Spaltensätze“ setzt jetzt an der Gruppierung an (`frozenset()` → eine Gruppe), weil der
  alte Anker nach dem `try` nicht mehr traf (korrekt als ungültig gemeldet).
- Absturzwache: eine Ausnahme mit `__cause__`, die schon gesehen wurde (`raise … from e`), gilt als Umhüllung,
  nicht als neuer Ursprung (sonst wäre `UpsertTeilfehler` eines Stub-Fehlers ein „Absturz“).
Ergebnis: Wächter **36/36**; Mutationen **22/22** in zwei Läufen; Gegenproben 6/6.

## Fragen
1. Auflage erfüllt? 2. Kann die Umhüllungsregel der Absturzwache einen echten Absturz verdecken (z. B. Produktivcode
wirft `X from e` mit `e` aus einem Stub)? 3. Sonst etwas vor dem Commit?

## Ausgabevertrag
**Urteil** · **Befunde** · **Antworten**. ≤ 30 Zeilen.

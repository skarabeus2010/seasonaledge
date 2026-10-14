# Code-Review Paket B1, Runde 2

Deine Antwort Runde 1: `docs/review_prompts/2026-10-14_options_b1_code_antwort1.md` (nein, drei Befunde). Prompt R1:
`…_b1_code.md`. Code uncommittet im Arbeitsbaum. Python wie dort. Read-only, Deutsch, **FREIGABE (Code): ja/nein**.

## Umsetzung
1. **P1 Reparatur traf alle Zeilen desselben Datums.** `scripts/backfill_skew_vrp.py`: Zielzeilen werden über ihre
   **Position** im Ticker-Array identifiziert (`_ziel_positionen`, Reihenfolge = Reihenfolge im Diff, Datumsabgleich
   der Positionen gegen den Diff), nicht mehr über ein Datumsdictionary. `reparatur_pruefen` lehnt doppelte Daten im
   Bereich ab (Trockenlauf: kein Bericht), und `reparatur_anwenden` ruft die Prüfung unter der Sperre selbst noch
   einmal auf. Fixtures: dein Fall (cm + single am selben Datum) → Trockenlauf Exit 2 ohne Bericht; direkter Aufruf
   `reparatur_anwenden` mit doppeltem Datum → RuntimeError, Objekt unverändert.
2. **P2 fehlendes `vrp_pts`.** Die Invariante setzt beim Zurücksetzen fehlende Schlüssel nicht mehr auf `null`, sondern
   entfernt sie. Fixture: eine Zielzeile ohne `vrp_pts`, eine mit `vrp_pts: null` → Trockenlauf + Schreiben Exit 0,
   beide gesetzt.
3. **P2 Nachweis „Snapshot unter Sperre“.** Linux-Probe: ein Prozess hält die Sperre in `danach` (2,5 s), ein zweiter
   Schreiber bekommt mit Frist 0,5 s `SperreBelegt`. Mutation „Sperre vor danach lösen“ (nur Linux).

Mutationstest: neu „doppelte Daten nicht geprüft“, „fehlendes Feld wird zu null“, „Zeilen über das Datum statt über die
Position“ (dein Fall), „Sperre vor danach gelöst“; Anker der Feld-Mutation nachgezogen.

## Nachweise
- `verify_skew_historie_sperre.py`: Windows grün (Parallelität ungeprüft), **Linux `--streng` grün**.
- Mutationstest **Linux `--streng` 22/22**; Windows 19/19 + 3 nur-Linux ungeprüft.
- Unverändert grün: `verify_session_stamp`, `verify_skew_anzeige`, `verify_skew_laufzeiten`, `verify_basisabweichung`
  (+ Mutation 24/24).

## Zu deinem Hinweis Health/SperreBelegt
Bei `SperreBelegt` endet der Cron mit Exit 1, der Workflow wird rot — das ist der Alarm. Dass der Health-Check erst
nach drei Tagen wegen Frische abwertet, bleibt so (gleiches Verhalten wie bei jedem anderen Cron-Ausfall); notiert als
Folgeposten zusammen mit B2 (Frische in Sessions).

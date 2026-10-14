# Entwurf v4 (Delta zu v3): B1 und B2 nach deiner Antwort

v3: `docs/review_prompts/2026-10-14_options_sofortreparaturen_plan_v3.md`, deine Antwort:
`…_plan_v3_antwort.md` (B3 frei). Hier nur die Änderungen; der Rest von v3 gilt. Read-only,
**FREIGABE (Plan): B1 ja/nein · B2 ja/nein**.

## B1 — geändert

1. **Snapshot schon in B1 unter derselben Sperre.** `compute_options_skew.build()` schreibt `options_skew.json` nicht
   mehr bei `:1223`, sondern im Sperrblock: History frisch lesen → zusammenführen → History schreiben → Snapshot
   schreiben → Sperre lösen. Ist die History defekt oder die Sperre belegt, wird **keine** der beiden Dateien
   geschrieben (Exit ≠ 0). B3 fügt nur die Rangrechnung zwischen Zusammenführen und Schreiben ein.
   Fixture: defekte History → Snapshot-Datei byte-gleich wie vorher.
2. **Reparatur mit verbindlicher Freigabedatei.**
   - Trockenlauf `--reparatur --ticker ETHA --von 2026-09-30 --bis 2026-10-13` schreibt **keine Produktionsdaten**, aber
     den Bericht `logs/reparatur/vrp_<ticker>_<von>_<bis>_<zeit>.json`: Ticker, Bereich, je Zeile Datum, cm_mode,
     iv_atm, vrp alt, RV neu, vrp neu, dazu SHA-256 des kanonischen Inhalts der Zielzeilen vor der Änderung.
   - Schreiblauf `--reparatur … --schreiben --freigabe-datei <bericht.json>`: Ticker/Bereich müssen dem Bericht
     gleichen; unter der Sperre wird der Diff auf dem frisch gelesenen Stand neu gebildet und **vollständig** gegen den
     Bericht geprüft (Zielzeilen-Hash, alle Ausgangswerte, neue RV und neue VRP je Zeile, Zeilenmenge). Jede Abweichung
     → Abbruch, nichts geschrieben.
   - Invariante: frisch gesperrter Ausgangsstand gegen Ergebnis — außer `vrp_pts` der Zielzeilen ist alles gleich.
     Legitime Cron-Ergänzungen außerhalb des Bereichs zwischen Trocken- und Schreiblauf bleiben dadurch erhalten
     (sie stehen in beiden Ständen).
   - Fixtures: geänderte Zielzeile zwischen den Läufen, geänderte RV (andere Kurse), andere Bereichsangabe, fehlende
     Freigabedatei → jeweils Abbruch; neuer Cron-Punkt außerhalb des Bereichs → Schreiben erlaubt, Punkt erhalten.
3. `backfill_skew_massive.anwenden(arr_frisch, neue, overwrite)` bestimmt `n_purge` aus dem frischen Bestand.
4. `backfill_skew_history.py` (marketdata, stillgelegt) wird **gelöscht**; Verweise in Doku/Skripten werden angepasst
   (`verify_skew_iv.py` importiert nichts mehr daraus — seit v55.1).

## B2 — ergänzt

1. **EOD-Schutz für alle drei Erzeuger** (`snapshot_gex_massive`, `compute_key_levels`, `compute_iv_surface`): je
   Erzeuger `S = letzte_session("NYSE")` einmal am Start, `pruefe_eod_fenster(job)` **vor dem ersten Datenabruf**,
   sofern geschrieben wird (`--no-write`/lesend erlaubt). Fixtures: Lauf in der Handelszeit → MarktOffen, keine
   Abfrage, keine Datei; je Erzeuger.
2. **Key Levels übernimmt GEX nur zur selben Session.** `_load_gex()` liefert zusätzlich `session`/`bewertung`/
   `stempel_art`; Flip/Walls werden nur übernommen, wenn `stempel_art == "session"` und `session == S`. Sonst fallen die
   GEX-Felder weg, Feld `gex_status: "fehlt"|"andere_session:<datum>"|"alter_stempel"`, Ausgabe im Lauf. Fixture: GEX
   der Vorsession + aktuelle Chain → keine Walls/Flip, Status gesetzt.
3. **Health-Check:** die bestehende Abdeckungsbewertung bleibt erhalten; die Session-Bewertung kann nur
   **verschlechtern**: Status = schlechter aus (Abdeckung, Session-Alter); „alter Stempel“ ist gelb, verbessert aber nie
   ein Rot. Fixtures: aktuelles Datum + 3 Ticker → rot; alter Stempel + 3 Ticker → rot.
4. **Uhrzeit-Gegenprobe** mit eingefrorenen Chain-/Spot-Eingaben (Attrappe für `_get`), Lauf bei 22:30 UTC und bei
   01:30 UTC (Folgetag) derselben Session; verglichen wird die Ausgabe ohne `generated_at`/`generated` → identisch.
   Dazu ein Freitag mit Wochenverfall (verfallene Kontrakte sind in beiden Läufen draußen).

## B3 — Umsetzungshinweise übernommen
„Gültig“ = endliche Zahl vom Typ int/float, kein bool, nicht None (Python: `isinstance(x,(int,float)) and not
isinstance(x,bool) and math.isfinite(x)`; JS-Referenz: `typeof x === 'number' && isFinite(x)`). Put-Zeta-Fallback
`(put_iv − iv_atm)·100`, Call-Zeta `(call_iv − iv_atm)·100`.

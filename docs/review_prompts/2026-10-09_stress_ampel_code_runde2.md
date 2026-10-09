# Code-Review Stress-Ampel, Runde 2

Repo `C:\dev\Seasonaledge`, Arbeitsstand. Vorgeschichte: `..._code_runde1.md` + `..._code_antwort1.md`. Prüfe die
Korrekturen zu deinen drei Befunden und den Code auf neue Fehler. Antwort auf Deutsch: je Befund Schwere + Datei:Zeile +
konkreter Eingabefall + Änderung; am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.
Python: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`. Snapshot wie in Runde 1.

## Korrekturen
1. `shared/stress_score.vollauf`: Sperre (`stress_lauf_starten`) **vor** dem Laden; Laden, Sollmenge, Schreiben,
   Rücklesen und Veröffentlichen im selben `try`; jeder Fehler → `stress_lauf_abbrechen`, Exit über die Ausnahme.
   Ein Lauf kann damit nur Kurse veröffentlichen, die er nach dem Sperrerwerb geladen hat; parallel startet kein zweiter.
2. `scripts/check_db_completeness.py`: `stress_scores` über `letzter_fertiger_lauf(…, "SPY")` und das jüngste Datum
   **dieses** Laufs; ohne fertigen Lauf rot. Unveröffentlichte Zeilen und andere Ticker zählen nicht.
3. `aufraeumen`: Metadaten paginiert (`order lauf_id`, `range` je 1000), die zwei neuesten fertigen Läufe global über alle
   Seiten, abgebrochene und ältere fertige Läufe werden samt Zeilen **und** Laufeintrag entfernt (Laufeintrag nur, wenn
   nicht `laeuft`).

## Belege
`scripts/verify_stress_ampel.py --snapshot …` **32/32**, neu: `db_sperre_vor_laden` (Ereignisfolge im Fake: RPC vor dem
ersten `prices`-Zugriff; Ladefehler nach Sperrerwerb → `abgebrochen`), `db_aufraeumen_paginiert` (1003 fertige Läufe,
Fake liefert ohne Range höchstens 1000 Zeilen wie PostgREST → genau die zwei neuesten bleiben, Metadaten und Zeilen),
`completeness_nur_fertig`; angepasst: `db_unvollstaendige_eingabe` (Lauf existiert, aber abgebrochen, keine Zeilen).
`--mutationen` **23/23** + 3/3 untaugliche verworfen (neu: Sperre nach dem Laden, Aufräumen ohne Paginierung,
Completeness über alle Zeilen). Ablauf nach Freigabe wie in Runde 1; Schritt 3 stoppt, wenn `verify_stress_sql_live.py`
nicht besteht.

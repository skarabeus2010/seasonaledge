# Code-Review Phase 1B /plain-vanilla, Runde 2

Repo `C:\dev\Seasonaledge`, Arbeitsstand. Vorgeschichte: `..._1b_code_runde1.md` + `..._1b_code_antwort1.md`. Prüfe die
Korrekturen zu deinen drei Befunden und den Code auf neue Fehler. Antwort auf Deutsch: je Befund Schwere + Datei:Zeile +
konkreter Eingabefall + Änderung; am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.
Python: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`. Snapshot wie in Runde 1.

## Korrekturen
1. **Ungültige Zwischenkurse** (JS `strategy-compute.js`, Python `plain_vanilla.py`, gleich):
   - neu `_gueltigerKurs` / `_gueltiger_kurs` (endlich und > 0);
   - `_lueckenMarkieren` / `_luecken_markieren`: Zeilen mit ungültigem Kurs werden übersprungen, Intervalle laufen
     zwischen gültigen Schlusskursen → im geprüften Bereich zählt der Tag als fehlende Sitzung, sonst greift die
     Abstandsheuristik;
   - `tagesEquity` / `tages_equity`: bewertet zwischen gültigen Schlusskursen; ist das Exposure über alle übersprungenen
     Intervalle gleich, `Equity · (1 + h · (b/a − 1))`, sonst **null** mit `info.grund = 'ungueltiger_kurs'`
     (`hebel_ohne_pfad` für V3). `auswerten` setzt `stats.taeglich_grund`; Seite und Streamlit zeigen den Grund
     („Ungültige Kurse bei wechselnder Position: … ausgesetzt"), i18n DE+EN.
   - Dein Fall: Trade 02.→05.01.2024 1x, Closes 100, 0 | NaN | null, 110, 121 → Endwert **1.210**, 1 fehlende Sitzung;
     Exposure-Wechsel über den ungültigen Kurs (1x-Trade 02.→04., 2x-Fenster 03.→05.) → null, Grund gesetzt.
     Hinweis: Strategien mit Hebelpfad (UHTS) verwerfen einen Trade mit ungültigem Kurs im Pfad schon bei der Erzeugung
     (`_hebelPfad` → false, protokolliert `preis_ungueltig`), wie in 1A für Ein-/Ausstieg.
2. `docs/TRADING_CALENDAR_RULES.md`: XETRA-Regel ab 2001, 24.12.2001 als dokumentierte Annahme, Sonderliste, „handelt in
   der Regel" an Pfingstmontag/3. Oktober (beide Stellen).
3. Streamlit-Erklärung UHTS: S⁻3 1x, Aufstockung zum Schluss von S⁻1 auf 2x, Ausstieg S⁺3, tägliches Rebalancing, ohne
   Finanzierungskosten. Plan-Text V1 auf +42 % berichtigt.

## Belege
`verify_plain_vanilla_1b.py --snapshot …` **43/43** (neu `e_ungueltiger_kurs`, `py_e_ungueltiger_kurs`),
`--mutationen` **32/32** + 3/3 untaugliche verworfen (neu: ungültiger Kurs als Rendite null / Exposure-Wechsel nicht
ausgesetzt / ohne Lückenmarke, je JS und Python). `verify_plain_vanilla_1a.py` 52/52, `verify_kalender_zwilling.py`
0 Fehler. Zu deiner Anmerkung aus Runde 1: Mutationen und Snapshot-Teil schreiben Temp-Dateien und laufen deshalb nicht
unter `-s read-only`; die Zahlen oben stammen aus meinen Läufen.

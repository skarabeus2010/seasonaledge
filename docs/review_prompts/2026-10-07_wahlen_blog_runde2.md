# Review-Auftrag: Blogartikel Midterm 2026, Runde 2

Repo `C:\dev\Seasonaledge`. Vorgeschichte: `docs/review_prompts/2026-10-07_wahlen_blog_runde1.md` (deine acht Befunde).
Prüfe den Arbeitsstand. Antwort auf Deutsch, je Befund Schwere + Datei:Zeile + Änderung, am Ende genau eine Zeile
`FREIGABE: ja` oder `FREIGABE: nein`. Python: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`.

## Umsetzung deiner Befunde
1. **Kausalaussagen:** „was die Wahl selbst beiträgt", „mehr Marktumfeld als Wahlergebnis", „freundlicher November ist der
   übliche Novemberverlauf", „wenn es einen Wahleffekt gibt" → als beobachteter Unterschied formuliert, Kausalität
   ausdrücklich offen; „November eher freundlich" ersetzt durch den Bezug auf die gemessenen Vergleichswochen.
2. **Stichproben:** Gesamtmittel (31 Wahlen, +0,56 %) und gepaarter Vergleich (30 Tripel: +0,72 % gegen +0,39 %,
   +0,33 Pp) überall getrennt; ebenso Präsident (32 Tripel: +0,49/+0,17/+0,32) und Dow (30 Tripel: +0,85/+0,68/+0,17).
   Satz zum Chart: goldene Linien = 31 Wahlen, graue = 30 Tripel, Abstand ≠ gepaarte Differenz.
   `wahlen_fakten.py::gepaart()` liefert die gepaarten Werte; der Wächter prüft, dass ihr Abstand gleich
   `aggregiere()['differenz_mittel']` ist.
3./4. **Wächter neu** (`scripts/verify_wahlen_blog.py`): nur sichtbarer Text (Kommentare entfernt); JEDE Zahl mit
   %/Pp/pp/Prozentpunkt/percentage point muss ein Faktenblatt-Wert sein (Vorzeichen, genau 2 Stellen bei Renditen,
   Quoten 0/1 Stelle, Dezimaltrenner der Sprache); 31 Pflichtaussagen; Fallzahlen „X von Y"/„n = X"; Snapshot-Links
   exakt; Bildpfade aufgelöst. Mutationen 25/25 inkl. deiner Fälle in DE und EN.
5. **Rückrechnung vor 1957, Samstagssitzungen bis 1952** im Methodenteil; „tatsächlich" gestrichen.
6. **Renditebasis:** Nachlauf t0→t+20, Vorlauf t−20→t0, Chart t0 = 0 % getrennt beschrieben.
7. **Marktreaktion:** „Kursbewegungen nach der Wahlnacht erfasst der nächste Handelstag; das endgültige Ergebnis kann
   später feststehen" (Text + FAQ, DE+EN).
8. **Dow:** jetzt gepaart +0,85 % (Gesamtmittel-Wert entfällt).

## Bekannt, NICHT Teil dieses Auftrags (als TODO notiert)
Die Seite `/wahlen` zeigt dieselbe Mischung (KPI „Ø nachher" über alle Wahlen neben „Differenz" über Tripel); die
Korrektur betrifft den Rechenkern-Zwilling (JS+Python) und wird separat gebaut.

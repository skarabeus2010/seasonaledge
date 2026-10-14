**B2 ist noch nicht freigabefähig.** Die Session-Umstellung der Berechnungen passt, aber bei Anzeige und Health bleiben Lücken.

1. **Mittel — Key Levels verwendet weiterhin den Lauftag als Datum.**  
   [key-levels.html:279](C:/dev/Seasonaledge/landing/pages/key-levels.html:279) setzt `KL_DATE=d.generated`; der kopierbare Level-Text verwendet dieses Datum bei [Zeile 263](C:/dev/Seasonaledge/landing/pages/key-levels.html:263). Ein Lauf am 17.10. für Session 16.10. gibt damit weiterhin den 17.10. aus. Hier `session` verwenden; einen Altbestand ohne Session gegebenenfalls ausdrücklich kennzeichnen.

2. **Mittel — Zukünftige und ungültige Sessiondaten werden grün.**  
   [daily_health_check.py:888](C:/dev/Seasonaledge/scripts/daily_health_check.py:888) setzt den Rückstand für jedes `date >= erwartet` auf null. Read-only an der unveränderten Funktion reproduziert:
   - `20.10.` gegen erwarteten `19.10.` → grün, „aktuelle Session“.
   - Samstag `17.10.` gegen Freitag `16.10.` → ebenfalls grün.
   - Feiertag `03.07.` gegen `02.07.` → ebenfalls grün.

   Datum nach der erwarteten Session sowie Nicht-Handelstage mit Session-Stempel müssen als ungültig erkannt werden. Der reguläre Feiertagsabstand funktioniert: 02.07. → 06.07. ergibt korrekt eine Session Rückstand.

3. **Mittel — Alte Profile können unter einem neuen Sessiondatum erscheinen.**  
   [snapshot_gex_massive.py:274](C:/dev/Seasonaledge/scripts/snapshot_gex_massive.py:274) aktualisiert nur erfolgreiche Chart-Ticker. Bei einem zulässigen Teilausfall bleibt deren bisheriges Profil liegen. [dealer-positioning.html:329](C:/dev/Seasonaledge/landing/pages/dealer-positioning.html:329) übernimmt es ohne Vergleich mit der Summary-Session; oben steht bereits deren neues Datum. Der Leser muss abweichende Profil-Sessions verwerfen oder separat datieren. Dieser bestehende Pfad ist insbesondere beim neu möglichen Ausfall einzelner Session-Tagesbalken relevant.

4. **Niedrig — Archivherkunft wird nicht sichtbar ausgegeben.**  
   `_from_snapshot` liefert `_herkunft`, aber [compare_flashalpha_gex.py:263](C:/dev/Seasonaledge/scripts/compare_flashalpha_gex.py:263) zeigt weiterhin nur „Stand … (EOD)“. Damit bleibt beim alten Archiv verborgen, dass das Datum ein Lauftag ist. Die Herkunft in die Konsolenausgabe aufnehmen.

Die übrigen Prüfaufträge:

- **Erzeuger:** DTE, Horizont und GEX-Metadaten verwenden die Session. Verbliebene `generated`/`generated_at` sind Laufzeitfelder. Der Workflow erzeugt keinen zusätzlichen Datenstempel; sein Archiv-Kommentar ist allerdings veraltet.
- **Spot/Reißleine:** Ein fehlender oder falsch datierter Tagesbalken führt korrekt zum Tickerausfall. Unter 60 % Erfolg erfolgt der Abbruch vor dem Schreiben; der Workflow überspringt anschließend Key Levels. Das ist richtig. Die tatsächliche Verfügbarkeit um 22:15 UTC ist durch die Attrappen nicht nachgewiesen. Im Winter liegt dieser Termin nur 75 Minuten nach regulärem Schluss.
- **Wächter:** Sie rufen echte `main`-/`build`-Funktionen und den echten EOD-Schutz auf. Die Einbindung ist damit substanziell. Es fehlen insbesondere Fälle für zukünftige/feiertägliche Health-Daten, veraltete Profile bei Teilausfall und die Key-Levels-Datumsanzeige. Außerdem enthält die Mutationsliste entgegen der zusammenfassenden Beschreibung keine IV-Surface-Horizontmutation.

Keine Dateien geändert. Die vollständigen Wächter habe ich wegen ihrer temporären Schreibzugriffe unter der strikt read-only Umgebung nicht ausgeführt; der Mutationstest verändert zusätzlich Produktionsquellen. Die gemeldeten **20/20** sind daher nicht unabhängig bestätigt.

**FREIGABE (Code): nein**

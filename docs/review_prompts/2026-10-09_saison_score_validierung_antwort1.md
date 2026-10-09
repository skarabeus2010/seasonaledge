# Codex-Antwort (Schlussantwort; Rohprotokoll nicht im Repo)

Nur lesend geprüft; kein Validierungslauf gestartet, keine Dateien geändert.

1. **Hoch — [saison_score_validierung.py:140](C:/dev/Seasonaledge/scripts/research/saison_score_validierung.py:140): Explorative Kennzahlen beeinflussen den primären Test.**  
   **Fall:** Ist beispielsweise B3 in einer gezogenen Stichprobe konstant, verwirft `any(...)` die gesamte Ziehung, obwohl Score und Ziel für jede Reihe definiert sind. Dadurch ändern sich primäres Intervall und Verwerfungsanteil aufgrund explorativer Bausteine. Auch der Vergleichsscore wirkt als zusätzlicher Filter.  
   **Änderung:** Dieselben 2000 Jahresziehungen verwenden, aber Gültigkeit getrennt bestimmen: primär anhand Score/Ziel, gepaart anhand beider Scores/Ziel, explorativ je Baustein. Verwerfungen und Auswertbarkeit getrennt berichten; diese Regel vorab protokollieren.

2. **Hoch — [saison_score_validierung.py:167](C:/dev/Seasonaledge/scripts/research/saison_score_validierung.py:167) und [saison_score_validierung.py:185](C:/dev/Seasonaledge/scripts/research/saison_score_validierung.py:185): Die Validierungslogik selbst ist nicht festgeschrieben.**  
   **Fall:** Commit `b7b01da` enthält weder Validierungsskript noch Protokoll; beide sind unversioniert. Geprüft werden ausschließlich Kern- und Datenhashes. Änderungen beispielsweise an Seed, Raster oder Bootstrap passieren die Sperre. Die entsprechenden JSON-Vorgaben werden beim Lauf auch nicht eingelesen oder gegen die Konstanten geprüft.  
   **Änderung:** Vor dem Lauf das geprüfte Validierungsskript versionieren und seinen Hash im Protokoll festhalten und prüfen. Auswertungsparameter aus dem Protokoll beziehen oder vollständig auf Übereinstimmung prüfen. Das endgültige Protokoll ebenfalls versionieren.

3. **Mittel — [saison_score_validierung.py:229](C:/dev/Seasonaledge/scripts/research/saison_score_validierung.py:229) und [saison_score_validierung.py:237](C:/dev/Seasonaledge/scripts/research/saison_score_validierung.py:237): „Nicht auswertbar“ wird als negatives Ergebnis ausgegeben.**  
   **Fall:** Bei mehr als 100 verworfenen Ziehungen steht zwar `auswertbar=false` im JSON, gleichzeitig aber `rangzusammenhang=false`; die Konsolenausgabe meldet ausdrücklich „nein“. Das verwechselt fehlende Auswertbarkeit mit einem auswertbaren negativen Befund.  
   **Änderung:** Bei Überschreiten der Grenze `rangzusammenhang=null` und ausdrücklich „nicht auswertbar“ ausgeben. Für den gepaarten Vergleich ebenfalls einen eigenen Auswertbarkeitsstatus vorsehen.

4. **Mittel — [saison_score_validierung.py:217](C:/dev/Seasonaledge/scripts/research/saison_score_validierung.py:217): Die vorgesehene Positivrate fehlt.**  
   **Fall:** D5 nennt „Immer positiv“ als Basis der Positivrate. Ausgegeben werden lediglich Korrelationen und mittlere Quintilrenditen; weder positive Ziele noch deren Anteil werden berichtet.  
   **Änderung:** Vorab die Positivrate als Anteil `ziel > 0` auf denselben Bewertungstagen festhalten und mindestens je Reihe mit Zähler und Nenner ausgeben. Eine etwaige Aggregation ebenfalls vor dem Lauf definieren.

Die ausdrücklich hervorgehobenen Punkte sind ansonsten korrekt: Jahresmehrfachziehungen vervielfachen die Beobachtungen tatsächlich; verwendet wird `score_roh`; `rank().corr(rank())` berechnet Mittelränge und anschließend Pearson. Dezember-Ziele bleiben dem Jahr von `as_of` zugeordnet. Universum und Mindestanforderungen werden einmal auf den Originalbeobachtungen bestimmt. Abschnitt B bleibt getrennt.

Das Manifest enthält genau 43 Reihen; alle 43 Datenhashes und drei Kernhashes stimmen aktuell überein. Endpunkt-, Reife- und Lückenprüfung entsprechen dem freigegebenen Kern einschließlich der später dokumentierten Börsentoleranz von **7 Kalendertagen**. Das Raster beginnt jeweils beim ersten vorhandenen Handelstag im Abschnitt und nimmt anschließend jeden fünften.

FREIGABE: nein

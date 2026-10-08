# Codex-Antwort: Plan /plain-vanilla, Runde 4


codex
**Phase 1A ist noch nicht vollständig freigabefähig.** Die Vorrangregel für E1–E6 berücksichtigt die alten Formulierungen ausreichend; diese werte ich nicht nochmals als Widersprüche. Geprüft wurden die Vorreviews und die betroffenen Repository-Stellen. Keine Dateien geändert.

1. **Hoch — E1/E2 und Punkt 6: Reihenfolge von Datenende-Behandlung und Stops fehlt.**  
   „Datenbestand beendet: keine offenen Trades“ kann einen Trade entfernen, bevor die nachgeschaltete Stopfunktion seinen bereits erfolgten Ausstieg erkennt. Beispiel: Einstieg 100, danach Close 80, regulärer Exit noch nicht erreicht, letzte Kurszeile inzwischen mehr als zehn Sitzungen alt. Mit Fixed-Stop 8 % muss der geschlossene Trade mit −20 % erhalten bleiben. Die gegenwärtige Seitenlogik berechnet zunächst Strategietrades und wendet danach Stops an.

   **Änderung:** Verbindlich festlegen: zunächst Trade-Kandidaten bis zum letzten vorhandenen Kurs erzeugen, dann Stops anwenden, anschließend verbleibende offene Kandidaten bei veraltetem Datenbestand aus der aktiven Darstellung ausschließen und als unvollständig protokollieren. Keine fingierte Schließung; tatsächlich geschlossene Trades bleiben erhalten. Wächterfälle mit und ohne Stop sowie für genau zehn und elf fehlende Sitzungen ergänzen.

2. **Mittel — E1/E2 und Messrahmen 0: Die neuen Zustände sind noch nicht durchgängig vereinbart.**  
   E1 führt `kurs_ausstehend` ein; Abschnitt 0 verschiebt Kalender-/Lückenstatus dagegen ausdrücklich nach 1B. Damit lässt sich im Differenzbericht nicht unterscheiden, ob ein offener Trade auf einen zukünftigen Exit oder auf einen bereits fälligen, fehlenden Kurs wartet. Für einen **Einstieg** mit `kurs_ausstehend` fehlt außerdem die ausdrückliche Konsequenz; „wie offen behandelt“ darf dort keinen Trade erzeugen.

   **Änderung:** Bereits in 1A die Zustände `noch_nicht_faellig`, `kurs_ausstehend` und `datenbestand_veraltet` im Messformat samt Regeltermin, Bewertungsdatum und letztem Kursdatum führen. Einstieg ohne vorhandenen Ausführungskurs → kein Trade, protokollierter Grund. Nur ein tatsächlich erfolgter Einstieg kann eine offene Position erzeugen. Das umfassende historische Lückenmodell bleibt in 1B.

3. **Mittel — E6 und Wächter: Der Streak-Test belegt die Übergabe der konfigurierten Trades noch nicht.**  
   Ein Funktionstest für `streak(trades)` plus statischer Nachweis ihres Seitenaufrufs reicht nicht: Auch `SA.strategy.streak(rawTrades)` erfüllt beides. Genau die falsche Herkunft der Trades ist Teil von Befund 13. Aktuell erstellt die Signalansicht einen eigenen Strategie-Cache.

   **Änderung:** Zusätzlich den tatsächlichen Konsumentenpfad ausführen oder die gemeinsame Auswahl-/Stop-Aufbereitung in eine getestete, von Kennzahlen und Signalansicht verwendete Funktion ziehen. Zeitraumwechsel und Stopwechsel müssen erwartbar Kennzahlen **und** Streak verändern. Die bereits angekündigte Mutation „ungefilterte Trades übergeben“ muss an dieser Prüfung scheitern.

Die übrigen zentralen Entscheidungen tragen: Historische Lücken und das Hebelmodell können mit den genannten Vergleichsausnahmen in 1B bleiben. Punkt 5 trägt durch E1 als **Kalenderauflösung plus getrennte Stichtags- und Kursprüfung**, nicht allein durch „nach letzter Zeile“. Der Kalendervergleich 2000–2035 muss dabei auch die bereits in Python enthaltenen NYSE-Sonderschließungen erfassen.

E5 löst den Stop am regulären Ausstiegstag eindeutig: gleicher Close, gleiche Rendite, genau ein geschlossener Trade, zusätzlich `stopped:true`. Hier besteht kein weiterer Einwand.

FREIGABE: nein

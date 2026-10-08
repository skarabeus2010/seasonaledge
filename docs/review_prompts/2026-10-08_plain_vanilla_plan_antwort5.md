# Codex-Antwort: Plan /plain-vanilla, Runde 5


codex
**Phase 1A ist freigabefähig.** Geprüft wurden die vier bisherigen Planreviews, die ursprünglichen Befunde und die betroffenen Codepfade. Keine Dateien geändert. Die Vorrangfestlegungen E1–E9 lösen die überholten Formulierungen weiter unten ausreichend auf.

Die drei Einwände aus Runde 4 sind geschlossen:

1. **Zuvor hoch – E7 / Datenende und Stops.** Die Reihenfolge erhält tatsächlich gestoppte Trades als realisiert und entfernt erst anschließend verbleibende offene Kandidaten aus der aktiven Darstellung. Die Fälle mit und ohne Stop sowie zehn/elf Sitzungen decken den Fehler ab. **Weitere Änderung: keine.**

2. **Zuvor mittel – E8 / Messformat und Einstieg.** Die Zustände samt Regeltermin, Stichtag und letztem Kursdatum sind bereits für 1A verbindlich. Ein fehlender Einstiegskurs erzeugt ausdrücklich keinen Trade. **Weitere Änderung: keine.**

3. **Zuvor mittel – E9 / Streak-Konsumentenpfad.** Die gemeinsame Auswertung für Kennzahlen und Signalansicht beseitigt die getrennte Berechnungsquelle. Die angekündigten Wechsel- und Mutationstests prüfen auch die tatsächliche Übergabe. **Weitere Änderung: keine.**

Ein nicht blockierender Präzisierungspunkt bleibt:

4. **Niedrig – E1/N2 / XETRA-Kalendervergleich.** Im vorhandenen Code behandelt JS den 24. und 31. Dezember durchgehend als Feiertage; Python erst ab 2011 (`shared/exchange_holidays.py`). Der zugesagte vollständige Sitzungsvergleich 2000–2035 erfasst diese Abweichung bereits verbindlich. **Änderung:** Diese beiden Jahresgrenzen ausdrücklich in die N2-Korrekturliste und die gezielten Wächterfälle aufnehmen. Die bloße Übernahme der aufgezählten NYSE-Korrekturen würde den Kalendervertrag noch nicht erfüllen.

Zu den besonders angefragten Punkten:

- **Abgrenzung:** Historische Lücken und Hebel können in 1B bleiben. Die Ausnahmen für UHTS, Python-OHLC-Stops und die noch unterschiedlichen LBR-Indikatoren begrenzen die Gleichheitszusage ausreichend.
- **Punkt 5:** Er trägt durch E1/E2/E8: zuerst den Regeltermin bestimmen, dann Stichtag und Kursverfügbarkeit getrennt prüfen. „Nach letzter Kurszeile“ allein wäre weiterhin unzureichend, ist aber ausdrücklich übersteuert.
- **Stop am regulären Exit:** E5 ist eindeutig: gleicher Close, gleiche Rendite, genau ein geschlossener Trade und zusätzlich `stopped:true`.

Die Freigabe erlaubt den Beginn der Umsetzung von **1A**. Sie bestätigt weder bereits implementierten Code noch Phase 1B oder spätere Phasen.

FREIGABE: ja

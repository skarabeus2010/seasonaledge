# Codex-Antwort (Schlussantwort; Rohprotokoll nicht im Repo)

Die v3-Ergänzungen schließen die vier bisherigen Befunde auf Planungsebene. Nur gelesen; keine Dateien geändert.

1. **HOCH — Abschnitt 0/C2/D2 — geschlossen.**  
   **Fall:** Dieselbe Kurslücke muss je Marktklasse unterschiedlich bewertet werden.  
   **Änderung:** Pflichtparameter `ticker`, gemeinsame Zuordnung, Fehler bei fehlendem Ticker und marktübergreifende Zwillingstests machen den Vertrag eindeutig.

2. **HOCH — U/D1/D2 — geschlossen.**  
   **Fall:** Lokale Datumsarithmetik verschiebt Jahreskurven; Tag 366 überschreitet die Matching-Achse.  
   **Änderung:** Vorgelagerte UTC-Korrektur beider Jahreskurvenbauer, echte Mehrzeitzonentests samt Mutationstest und Begrenzung auf 365 lösen beide Punkte.

3. **HOCH — D5 — geschlossen.**  
   **Fall:** Junge Reihen oder undefinierte Bootstrap-Korrelationen machen den gleich gewichteten Mittelwert unbestimmt.  
   **Änderung:** Vorab festgelegte Mindestdaten, festes Universum, vollständiges Verwerfen ungültiger Ziehungen, 5-%-Grenze und gepaarte Beobachtungen definieren die Auswertung ausreichend.

4. **MITTEL — D3/D5 — geschlossen.**  
   **Fall:** Wiederholungsläufe überschreiben bereits gespeicherte Ergebnisse.  
   **Änderung:** Separate Protokolltabelle, erster Lauf je Schlüssel, Codeversion und Datenhash sowie entzogene Änderungsrechte schließen diese Lücke. Die Rechte müssen im Migrationsreview mit der tatsächlich verwendeten Nightly-Rolle geprüft werden.

Die Freigabe betrifft den Plan; die vorgesehenen Implementierungsreviews und Tests bleiben erforderlich.

FREIGABE: ja

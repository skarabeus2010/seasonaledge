**Urteil: tragfähig als Plan.** V3 erfüllt die fünf Auflagen aus Runde 2: vollständige Sitzungsachse, fester Historienbeginn, Frischeprüfung ohne Rückfall, Entfernung des zweiten Rechenwegs und definierte degenerierte Fälle.

Ein kleiner Befund bleibt:

- **Niedrig – falscher API-Name:** [Plan v3:9](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-19_spot_vol_beta_plan_v3.md:9) nennt `SA.boersenkalender.detect`. Diese Funktion existiert nicht; korrekt ist `SA.boersenkalender.boerse(ticker)`. In Node geprüft: Alle acht genannten Ticker ergeben damit `NYSE`. **Auflage:** beim Bau korrigieren.

**R2-4 ist vertretbar.** Die Aufrufersuche bestätigt keinen fachlichen Leser der Tabelle. Die vorgesehenen Anpassungen an Nightly, Client, Vollständigkeitsprüfung und Teststub decken die gefundenen Abhängigkeiten ab. Die Tabelle kann bestehen bleiben.

Die Frischeregel habe ich mit dem echten Kalender ausgeführt: regulärer Sitzungstag um 15:00/16:45 New York, Sonntag sowie Halbtag unmittelbar vor/ab Schlusszeit plus 30 Minuten ergeben die erwarteten Sitzungen. **Den Halbtag-Grenzfall zusätzlich verbindlich in den Wächter aufnehmen.**

Keine weiteren blockierenden Planlücken gefunden. Dies ist eine Planfreigabe; Implementierung und Wächter sind anschließend gesondert abzunehmen. Read-only geprüft, keine Dateien geändert.
tokens used
81.549

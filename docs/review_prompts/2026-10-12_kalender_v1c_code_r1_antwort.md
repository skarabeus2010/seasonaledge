# Antwort Codex — V1c-1 Code-Runde 1 (2026-10-12)

Zu: [Prompt](2026-10-12_kalender_v1c_code_r1.md)

**Urteil**
V1c-1 noch nicht freigegeben: zwei P2-Befunde. Die neuen v4-Felder einschließlich `verlegt` sind vollständig; Snapshot, Versionsänderungstests und Tabellen-Abnahmelücken sind bestätigt.

**Befunde**

- **P2 — Ereignissen fehlt `kalenderversion`:** [shared/boersenereignisse.py:79](/C:/dev/SeasonalEdge/shared/boersenereignisse.py:79), [scripts/boersenkalender/api.js:148](/C:/dev/SeasonalEdge/scripts/boersenkalender/api.js:148). Modell und ausgegebene Objekte tragen sie nicht; die globale API-Eigenschaft erfüllt den geerbten Vertrag aus v2 §4/B4.1 nicht. Der vollständige Objektvergleich übersieht die gemeinsame Auslassung.
- **P2 — Jubiläumsidentitäten unzureichend abgesichert:** [scripts/verify_boersenereignisse.py:157](/C:/dev/SeasonalEdge/scripts/verify_boersenereignisse.py:157). Geprüft wird nur 2022. Eine schreibfreie Gegenprobe vertauschte 2002 Spring Bank und Golden Jubilee: sämtliche 121 direkt ausgeführten Prüfungen, Snapshot und vollständiger Objektvergleich blieben grün. Korrekt sind Spring Bank am 4.6. und der zusätzliche Jubiläumstag am 3.6. ([Proklamation](https://www.thegazette.co.uk/notice/L-56043-1001)).

**Auflagen**

- `kalenderversion` an Python-/JS-Ereignisobjekten ergänzen; beim Ereignishash ausschließen und unabhängig auf Vorhandensein/Richtigkeit prüfen.
- Quellenbasierte Identitäts-Sollfälle für 2002 und 2012 ergänzen; Vertauschungen bei unveränderter Schließungsmenge nach Bundle-Neuerzeugung gezielt abfangen.
- Nachgewiesen: 122 Python-Prüfungen bestanden, vollständige Python-/JS-Gleichheit unter UTC/Adak; Snapshot entspricht unverändert HEAD über 3024 Börsenjahre.
- Read-only geprüft, keine Dateien geschrieben. Den dateischreibenden Mutationstest habe ich nicht ausgeführt.

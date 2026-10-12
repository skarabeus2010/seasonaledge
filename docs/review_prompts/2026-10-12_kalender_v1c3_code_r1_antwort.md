# Antwort Codex — V1c-3 Code-Runde 1 (2026-10-12)

Zu: [Prompt](2026-10-12_kalender_v1c3_code_r1.md)

**Urteil:** V1c-3 noch nicht freigegeben; zwei Belegauflagen aus v2 fehlen. Kein P1.

**Befunde**

- **P2 – [shared/kalender_quellen.py:65](/C:/dev/SeasonalEdge/shared/kalender_quellen.py:65):** Der Quellenstand ist nur durch URL und Abrufdatum bezeichnet. Ein gesicherter Inhalt oder unveränderlicher Archivbeleg fehlt, insbesondere für die wechselnde NYSE-Kalenderseite. Der Stand vom 12.10.2026 ist damit später nicht reproduzierbar nachprüfbar.
- **P2 – [shared/halbtage_belege.py:62](/C:/dev/SeasonalEdge/shared/halbtage_belege.py:62):** `jahre_vollstaendig` enthält lediglich Jahreszahlen. Die im Entwurf verlangte eigene Quellenzuordnung samt Abrufdatum je Jahresabdeckung fehlt; Quellen einzelner Ereignisse belegen nicht automatisch die Vollständigkeit eines Jahres.
- Prüfung: Diff und neue Review-Dateien gelesen; 453 Python-Prüfungen bestanden, Momentaufnahme über 3 024 Börsen-Jahre unverändert, Bundle aktuell, 23 865 Python-/JS-Ereignisse samt Schließungen und Halbtagstatus identisch.
- 2016 bleibt korrekt ungeprüft; Zeit, Zone und Sitzung werden unabhängig geprüft. Mutationstest statisch geprüft, wegen Read-only nicht ausgeführt.

**Auflagen**

- Quelleninhalte reproduzierbar sichern und mit den Belegen verknüpfen.
- Jahresabdeckung als eigenen Beleg mit Quelle und Abrufdatum führen und im Wächter prüfen.
- Anschließend erneute Abnahme mit wirksamem Mutationsnachweis.

# Antwort Codex — V1c-2 Code-Runde 1 (2026-10-12)

Zu: [Prompt](2026-10-12_kalender_v1c2_code_r1.md)

**Urteil:** Noch keine Freigabe. Die v6-Kernauflagen bestehen; zwei P2-Befunde bleiben.

**Befunde**

- **P2 – Produktversion unvollständig:** [shared/produkttermine.py:203](/C:/dev/SeasonalEdge/shared/produkttermine.py:203) hasht Termine und Belege, aber nicht sämtliche Produktregeln. Gegenprobe: falsche Triple-Witching-Monate ändern das Ereignis, während `produktversion` selbst nach Cache-Leerung gleich bleibt.
- **P2 – Unsicherheit und Herkunft fehlen am Objekt:** [shared/produkttermine.py:127](/C:/dev/SeasonalEdge/shared/produkttermine.py:127) und [:151](/C:/dev/SeasonalEdge/shared/produkttermine.py:151): Die Kalenderannahme „Cboe-RTH = NYSE“ erhält keinen maschinenlesbaren Status; VIX-Ereignisse tragen zudem keine Quellenzuordnung je Feldgruppe. Beide Zwillinge teilen diese Auslassung.

**Auflagen**

- Versionshash um die fehlenden Produktregeln ergänzen; entsprechende Mutationen müssen gezielt scheitern.
- Kalenderannahme und Quellen je Feldgruppe in Python und JS ausgeben und unabhängig prüfen.
- Monatsbelege abschließend gegen die Quellen bestätigen: Alle sieben Cboe-Jahreskalender sind erreichbar, ihre farbigen Markierungen und die 142 VX-Dateiinhalte waren hier nicht vollständig auswertbar. Die 310 Belege sind deshalb **nicht vollständig unabhängig bestätigt**.
- „HTTP 403 = nicht gelistet“ in [shared/produkttermine_listung.py:8](/C:/dev/SeasonalEdge/shared/produkttermine_listung.py:8) durch „kein positiver Listungsnachweis“ ersetzen.

Nachgewiesen: **85/85 Wächterprüfungen**, Auftrag ausschließlich im Speicher; vollständige Python/JS-Gleichheit für vier Prüfdaten in zwei Zeitzonen. Beide Python-Einstufungsmutationen scheitern gezielt; den schreibenden 15er-Mutationslauf habe ich nicht ausgeführt. Die VIX-ODER-Regel entspricht dem [CFE-Filing](https://cdn.cboe.com/resources/regulation/rule_filings/approved/2015/SR-CFE-2015-023.pdf).

Bestandsschutz für dieses Paket erfüllt: Altverbraucher unverändert, sämtliche bisherigen Bundle-Daten bis auf den Gesamthash identisch. Die OPEX-Momentaufnahme muss spätestens **vor dem V3-Umbau** eingefroren werden. Arbeitsbaum einschließlich neuer Dateien geprüft; keine Dateien oder DB-Daten geändert.

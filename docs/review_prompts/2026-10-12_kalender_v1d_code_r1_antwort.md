# Antwort Codex — V1d Code-Runde 1 (2026-10-12)

Zu: [Prompt](2026-10-12_kalender_v1d_code_r1.md). Erster Lauf scheiterte am Werkzeug (setup refresh), dies ist die Wiederholung.

**Urteil:** Keine Freigabe. Die Auflagen sind noch nicht vollständig erfüllt. Read-only geprüft, nichts geändert.

**Befunde**

- **P2 – [api.js:293](/C:/dev/SeasonalEdge/scripts/boersenkalender/api.js:293):** `heute` akzeptiert `2026-02-30T12:00:00Z` und liefert den 2. März. Epoch `8640000000000001` wirft `RangeError` statt `KalenderFehler`. Ungültige Zeitpunkte vor der Umrechnung prüfen.
- **P2 – [verify_sitzungen_mutation.py:19](/C:/dev/SeasonalEdge/scripts/verify_sitzungen_mutation.py:19):** Die übernommene Mutationsauswertung zählt abgefangene Abstürze als Nachweis. Gegenprobe: absichtlicher `RuntimeError` → `ABSTURZ` im Sollfall → Urteil „gefangen“. Solche Läufe müssen als ungültig gelten.
- **P2 – [verify_sitzungen.py:322](/C:/dev/SeasonalEdge/scripts/verify_sitzungen.py:322):** Der vollständige Referenzvergleich fehlt für die öffentliche JS-Funktion `sitzungen`; nur Python wird vollständig geprüft. JS erhält lediglich einen kurzen Juli-Sollfall.

**Auflagen**

Die drei Befunde beheben und durch wirksame Gegenproben absichern; anschließend Wächter und Mutationstest erneut ausführen.
Bestätigt: Sitzungswächter **399/399**, bestehender Kalenderwächter **62/62**; Dateiübergabe schreibfrei im Speicher.
Generator entspricht dem Arbeitsbaum; die HEAD-Abweichung ist beim uncommitteten Stand erwartbar. Beide Wächter sind im Gate eingebunden.

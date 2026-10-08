# Codex-Antwort: Code 1B, Runde 1

codex
1. **Hoch – Ungültige Zwischenkurse verfälschen die Tageswerte.** [strategy-compute.js:1096](C:/dev/Seasonaledge/landing/js/strategy-compute.js:1096), [plain_vanilla.py:1473](C:/dev/Seasonaledge/shared/strategies/plain_vanilla.py:1473).  
   **Eingabefall:** Monthly 10, 02.–05.01.2024, Closes `100, 0, 110, 121`, ohne Stop. Reproduziert: Trade-Rendite **+21 %**, Tages-Endwert aber **1.100 statt 1.210** bei Startkapital 1.000. Beide Intervalle neben dem ungültigen Close erhalten Rendite null; außerdem erscheint kein Lückenhinweis. Mit `NaN` dasselbe Problem.  
   **Änderung:** Ungültige Zwischenkurse als fehlende Bewertungen behandeln. Bei durchgehendem 1x-Exposure die Bewegung zwischen gültigen Closes erhalten und die Lücke kennzeichnen; bei nicht rekonstruierbarem Exposure Tageswerte ausdrücklich aussetzen. Regressionstest in beiden Sprachen ergänzen.

2. **Niedrig – Verbindliche Kalenderspezifikation widerspricht der Umsetzung; K2 fehlt dort.** [TRADING_CALENDAR_RULES.md:76](C:/dev/Seasonaledge/docs/TRADING_CALENDAR_RULES.md:76).  
   **Eingabefall:** 24.12.2001 oder 25.05.2015: Die Spezifikation nennt weiterhin „seit 2011“ beziehungsweise pauschal Handel an Pfingstmontag. Die Implementierung behandelt beide Tage als geschlossen.  
   **Änderung:** Grenze ab 2001, Sonderliste und ausdrücklich nicht primär belegte Annahme für den 24.12.2001 dokumentieren; weitere pauschale Aussagen im Dokument angleichen.

3. **Niedrig – Streamlit erklärt weiterhin den alten UHTS-Hebel.** [09_Plain_Vanilla_Strategien.py:428](C:/dev/Seasonaledge/pages/09_Plain_Vanilla_Strategien.py:428).  
   **Eingabefall:** UHTS auswählen und Strategieerklärung öffnen: Dort steht Aufstockung auf „~1,5x“, gerechnet wird jetzt mit 2x.  
   **Änderung:** Aufstockung zum Schluss von S⁻1 auf 2x, tägliches Rebalancing und fehlende Finanzierungskosten korrekt beschreiben.

Die gemeldete **+42-%-Abweichung akzeptiere ich als konsistente Anwendung von L4**; den widersprüchlichen 21-%-Wächtertext im Plan entsprechend berichtigen.

Verifiziert: 36 schreibfrei ausführbare 1B-Prüfungen, Kalendervergleich sowie Monthly-10-Referenz und DAX-Lückenmessung bestanden. Den vollständigen 41/41-Lauf und die Mutationen konnte ich wegen der Schreibsperre für temporäre Dateien nicht bestätigen. Keine Dateien geändert.

FREIGABE: nein

# Codex-Antwort: Code 1A, Runde 2


codex
44/44 Prüfungen bestanden; Kalendervergleich über stdin ohne Abweichungen; EN-Prüfung: FAIL 0. Drei Befunde bleiben:

1. **P2 – Month-End-Einstieg verschiebt sich rückwirkend.** [strategy-compute.js:203](C:/dev/Seasonaledge/landing/js/strategy-compute.js:203), ebenso [plain_vanilla.py:187](C:/dev/Seasonaledge/shared/strategies/plain_vanilla.py:187).  
   **Eingabe:** Lückenlose NYSE-Kurse bis 29.10.2026, Close am 28.10. = 100, am 29.10. = 110. Month-End erzeugt einen offenen Trade ab **28.10. mit +10 %**, obwohl der vorletzte Oktober-Handelstag der **29.10.** ist. Mit der Kurszeile vom 30.10. springt der Einstieg auf den 29.10.  
   **Änderung:** Beim Rückwärtszählen im noch unvollständigen Monat die ausstehenden Monatssitzungen berücksichtigen, beispielsweise wie bei Monthly 10 vorhandene Zeilen um zukünftige Kalendertermine ergänzen. Nicht vom letzten vorhandenen Kurs zurückzählen.

2. **P2 – Python-Monthly-10 hat weiterhin das falsche Monatsende.** [plain_vanilla.py:394](C:/dev/Seasonaledge/shared/strategies/plain_vanilla.py:394).  
   **Eingabe:** NYSE-DataFrame 01.–21.10.2026 mit `Close`, `year`, `month`. Python erzeugt zusätzlich einen abgeschlossenen Trade **20.10.→21.10.** als „letzte zwei Handelstage“. JavaScript liefert korrekt nur die beiden abgeschlossenen Blöcke 01.10.→06.10. und 13.10.→16.10.; der letzte Block beginnt erst am 29.10.  
   **Änderung:** Die Monthly-10-Randkorrektur auch nach Python übertragen, einschließlich Zuständen für ausstehende Blocktermine. Das bloße Durchlaufen aller Strategien prüft diese Ergebnisabweichung nicht.

3. **P2 – Der Messlauf verwirft die nachgerüsteten Regeltermine ausgeschlossener Einstiege.** [probe_plain_vanilla_messlauf.js:109](C:/dev/Seasonaledge/scripts/js/probe_plain_vanilla_messlauf.js:109).  
   **Eingabe:** Monthly 10, Kurse und Stichtag bis 07.10.2026. `auswerten()` protokolliert neun zukünftige Einstiege mit konkreten Daten, darunter 13.10. und 29.10. Der Messlauf speichert davon lediglich `{"einstieg_noch_nicht_faellig":9}`. Damit fehlen im Messformat weiterhin die nach E8 erforderlichen Regeltermine der nicht ausgeführten Einstiege.  
   **Änderung:** Die einzelnen Protokolleinträge samt Datum erhalten; aggregierte Grundzähler nur zusätzlich ausgeben.

FREIGABE: nein

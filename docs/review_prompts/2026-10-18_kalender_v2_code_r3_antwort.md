# Kalender V2 — Antwort Codex auf Code Runde 3 (2026-10-18)

**Urteil**

Noch keine Freigabe für V2. Alle 57 Statusfälle sind für beide Anzeigen nachgewiesen; die Monatsreferenz-Auflagen bleiben teilweise offen.

**Befunde**

- **P2 – Unabhängiger Monatsüberlauf weiterhin unvollständig:** [verify_holidays_fassade.py:375](/C:/dev/SeasonalEdge/scripts/verify_holidays_fassade.py:375) akzeptiert für Mailand jedes spätere Monat, beispielsweise auch Dezember 2027. Ein exakter Nachfolger fehlt. LSE bleibt zudem ausdrücklich ohne Börsenbeleg ([Referenz:120](/C:/dev/SeasonalEdge/scripts/fixtures/kalender_monatslisten_2026.json:120)). Die Kennzeichnung dieser Lücken ersetzt die vereinbarte Referenzprüfung nicht.
- **P2 – Schaltjahrreferenz überspringt den Schalttag:** [verify_holidays_fassade.py:339](/C:/dev/SeasonalEdge/scripts/verify_holidays_fassade.py:339) setzt Februar immer auf 28 Tage. Für CRYPTO 02/2028 werden Offenheit, Nummern und Nachfolger am **29.02.2028** dadurch nicht gegen die unabhängige Liste geprüft.

**Auflagen**

- Belegte Monatsreferenzen mit exaktem Nachfolger vervollständigen; nötigenfalls einen anderen Referenzmonat wählen.
- Monatslänge schaltjahrgerecht bestimmen und den 29.02.2028 vollständig prüfen.
- Nachweis: **1.866 gezielte Prüfungen bestanden**, darunter sämtliche 114 Statusanzeigen; zusätzlich **20 lesende Einbindungsprüfungen bestanden**. Kein bestätigter Gesamtlauf; keine Mutationstests ausgeführt, keine Projektdateien geändert.

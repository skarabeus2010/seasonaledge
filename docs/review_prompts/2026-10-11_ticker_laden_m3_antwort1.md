**Urteil**

Keine Deployfreigabe für Schritt 3.

**Befunde**

- **P1 – Rückwechsel bleibt ungeschützt:** [wochentage.html](C:/dev/SeasonalEdge/landing/pages/wochentage.html:1799) und [backtest-engine.html](C:/dev/SeasonalEdge/landing/pages/backtest-engine.html:1650) kehren beim angezeigten Ticker vor der Kennungsvergabe zurück. Reproduziert auf beiden Seiten: `^GSPC → QQQ langsam → ^GSPC` endet mit Eingabe `^GSPC`, aber QQQ-Titel, Kennzahlen und Charts.
- **P1 – Dashboard-Zeitraumwechsel:** [renderAll](C:/dev/SeasonalEdge/landing/pages/dashboard.html:2024) übernimmt dieselbe Abrufkennung für mehrere Darstellungen. Reproduziert nach TTL-Ablauf: 30→5 Jahre; die 5-Jahre-Anfrage gelingt, danach scheitert die ältere 30-Jahre-Anfrage. Ihr [Fehlerabschluss](C:/dev/SeasonalEdge/landing/pages/dashboard.html:2205) überschreibt die Karte mit „Nicht genug Daten“.
- **P2 – Wechseltest kann unvollständige Läufe akzeptieren:** Der neue [Testzweig](C:/dev/SeasonalEdge/scripts/verify_seiten_kurse.py:124) überspringt Prüfungen auf Ruhe, Seitenfehler, vollständige Anzeige und Mindestzahl gefüllter Charts. Ein Endmarker allein genügt dort.
- Unabhängig bestätigt: einfache A→B-Wechsel bestehen auf **6/6 Seiten**, jeweils mit Ruhe, ohne Seitenfehler und gleichen finalen Texten/Chart-Serien. Dashboard-Overnight wird nach TTL-Ablauf tatsächlich asynchron; bei anschließendem Tickerwechsel greift die neue Prüfung.

**Auflagen**

- Auf Wochentage und Backtest-Engine die zweistellige `start(ticker, angezeigt)`-Form vor dem Gleichheits-Return verwenden; Rückwechsel als Seitenprobe ergänzen.
- Dashboard-Overnight zusätzlich gegen eine Kennung jeder neuen Darstellung absichern, einschließlich Zeitraumwechsel und Fehlerabschluss.
- Wechseltests um vollständige Abschluss- und Inhaltsprüfungen ergänzen; beide reproduzierten Fehlerfälle müssen bestehen.

Nichts geschrieben; Mutationstests nicht ausgeführt.

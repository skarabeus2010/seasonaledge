# Daily Briefing auf systemd-Timer — Codex-Antwort Runde 2

**Urteil:** keine Freigabe. Deploy-Sperre, Timer und Modustrennung sind umgesetzt; Versandsicherheit und Fristüberwachung haben noch Lücken.

**Befunde**

- **P1 – Doppelversand bei Wiederaufnahme:** [scripts/daily_newsletter.py:279](/C:/dev/SeasonalEdge/scripts/daily_newsletter.py:279): Zwischen erfolgreicher Mailannahme und `notieren()` kann der Prozess enden. Gegenprobe: Wiederaufnahme versendet denselben Empfänger erneut. Journalschreibfehler werden außerdem bei Zeile 287 als gewöhnliche Versandfehler abgefangen.
- **P2 – Frist ohne Live-Zeile wirkungslos:** [scripts/daily_health_check.py:715](/C:/dev/SeasonalEdge/scripts/daily_health_check.py:715): Leere Ergebnisse oder ausschließlich Testzeilen bleiben nach 10 Uhr gelb, obwohl `frist_rot=True`. Beide Fälle reproduziert.
- **P2 – Fristprüfung nicht zuverlässig eingeplant:** [.github/workflows/daily_health.yml:10](/C:/dev/SeasonalEdge/.github/workflows/daily_health.yml:10): Der automatische Health-Lauf startet um 05:00 UTC, vor der Berliner 10-Uhr-Frist. Ohne verspäteten oder manuellen Lauf erfolgt keine heutige Fristwarnung.
- **P2 – Wächter übersieht diese Wirkungen:** [scripts/verify_briefing_versand.py:134](/C:/dev/SeasonalEdge/scripts/verify_briefing_versand.py:134) bricht vor der Mailannahme ab; Zeile 263 prüft die Health-Integration nur per Regex. Die elf Health-Prüfungen bestehen trotz des reproduzierten Statusfehlers.

**Antworten 1–3**

1. Die 45-Minuten-Grenze mit rotem Deploy reicht als begrenztes Warten; sie garantiert keine Fairness. Für die beschriebenen kurzen Intraday-Läufe vertretbar.
2. `fertig` trotz eindeutig fehlgeschlagener Empfänger ist für die beschriebene Politik vertretbar. Unklar angenommene Mails und Journalschreibfehler brauchen einen eigenen Zustand.
3. Die späte Versandsperre verursacht unnötige Berechnung, aber allein keinen Doppelversand. Kein Freigabehindernis.

**Auflagen**

- Vor Versand einen dauerhaften offenen Empfängerzustand hinterlegen; ungeklärte Annahmen bei Wiederaufnahme sperren oder abgleichen. Journalschreibfehler müssen den Lauf stoppen.
- Frist auch bei leerer Live-Menge anwenden und einen automatischen Prüftermin nach 10 Uhr Berlin vorsehen.
- Wächter und Mutationen um diese tatsächlichen Fehlerpfade erweitern.
- Gezielt read-only geprüft; 19 Health-/Betriebsprüfungen bestanden. Vollständige Linux- und Mutationstests wurden hier nicht erneut ausgeführt.


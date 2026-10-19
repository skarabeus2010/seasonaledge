**Urteil: noch nicht tragfähig.** V2 erfüllt viele Auflagen aus Runde 1; fünf Punkte bleiben:

1. **Hoch – Sitzungsachse weiterhin ungesichert.** [Plan:18–26](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-19_spot_vol_beta_plan_v2.md:18)  
   Fehlt dieselbe Sitzung in beiden Reihen, besteht die neue Nachbarprüfung trotzdem. Forward-Horizonte und Rolling-Fenster zählen dann zu wenige Sitzungen. Ausgeführtes Kalenderbeispiel: Fehlt der 13.10., wird der 14.10. zum „nächsten Tag“ nach dem 12.10. Die Nightly-Prüfung kontrolliert außerdem nur die letzten sieben Tage ([nightly_refresh.py:228](C:/dev/SeasonalEdge/scripts/nightly_refresh.py:228)).  
   **Auflage:** `SA.boersenkalender` verwenden, fehlende Sitzungen als unbekannt erhalten; Forward-Zieldatum und sämtliche Zwischenrenditen prüfen.

2. **Hoch – Drei Jahre Vorlauf sichern keine stabilen expandierenden Schwellen.** [Plan:31](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-19_spot_vol_beta_plan_v2.md:31)  
   Beim Zeitraumwechsel ändert sich der historische Beginn der Quantilberechnung. Gegenbeispiel: 752 vorherige Betas von −2 ergeben q10=−2; mit zusätzlich 5.000 älteren Werten von −10 ergibt sich q10=−10. Dasselbe aktuelle Beta −5 wird einmal Stress, einmal nicht.  
   **Auflage:** fester Historienbeginn je Paar; Schwellen und Eintritts-/Sperrzustand vollständig berechnen, erst danach den Anzeigezeitraum filtern.

3. **Mittel – Datum ersetzt keine Frischeprüfung.** [Plan:28](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-19_spot_vol_beta_plan_v2.md:28)  
   Sind beide Reihen gleich veraltet, erscheint kein Warnhinweis. Bei ungültigen jüngsten Renditen rückt weiterhin ein älterer Wert nach.  
   **Auflage:** erwartete abgeschlossene Session prüfen; Reihenende, letzter gültiger Paartag und Frische getrennt anzeigen. Laufende Sitzungen ausschließen.

4. **Mittel – Python-Datenvertrag bleibt offen.** [Plan:39](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-19_spot_vol_beta_plan_v2.md:39)  
   Nur das Rolling-Fenster anzugleichen genügt nicht: Python lädt weiterhin Yahoo-Schlusskurse, verbindet zuerst und berechnet anschließend Renditen ([spot_vol_beta.py:28](C:/dev/SeasonalEdge/shared/spot_vol_beta.py:28), [Zeile 67](C:/dev/SeasonalEdge/shared/spot_vol_beta.py:67)). Der Nightly-Aufrufer ist aktiv.  
   **Auflage:** gespeicherte Renditen und dieselbe Sitzungs-/Lückenregel auch dort verbindlich vorsehen.

5. **Mittel – Degenerierte Regression nicht geregelt.** [Plan:59](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-19_spot_vol_beta_plan_v2.md:59)  
   Festlegungen fehlen für N≤2, konstantes x und s=0. Auch bei variablem x kann perfekte Linearität s=0 ergeben.  
   **Auflage:** undefinierte Kennzahlen als „nicht bestimmbar“ behandeln; solche Fälle ausdrücklich prüfen.

Die übrigen Änderungen sind als Plan tragfähig. Die Wächter müssen zusätzlich gemeinsame Datenlücken, Zeitraumwechsel, beidseitig veraltete Reihen und den echten Python-Ladepfad abdecken.

Read-only geprüft; die genannten Gegenbeispiele wurden in Node ausgeführt. Keine Dateien geändert.
tokens used
74.613

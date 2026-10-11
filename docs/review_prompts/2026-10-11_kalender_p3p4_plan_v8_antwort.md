**Urteil**

**V9 noch nicht als Bauplan freigegeben.** Die Bootstrap-Ausnahme schließt Befund 1 aus Runde 7. Die Datensperre bleibt unvollständig.

**Befunde**

1. **Hoch — Die Einstiegssperre stoppt laufende Ladungen nicht.** [v8:21](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-11_kalender_p3p4_plan_v8.md:21) sperrt `laden`/`get`; Pagination, Warteschlange, Wiederholungen und Rückfall laufen intern weiter ([kurse.js:218](C:/dev/SeasonalEdge/landing/js/kurse.js:218), [kurse.js:322](C:/dev/SeasonalEdge/landing/js/kurse.js:322)). Im Speicher geprüft: echter Kurslader mit ergänzter Einstiegssperre, Sperrflag und DOM-Ersatz; nach Freigabe des ersten 1000-Zeilen-Blocks startet **eine weitere Kursanfrage unter Sperre**, anschließend liefert die Ladung erfolgreich 1000 Zeilen. Damit ist die Zusage aus [v8:27](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-11_kalender_p3p4_plan_v8.md:27) nicht erfüllt.

**Auflagen**

- Sperre unmittelbar vor jedem tatsächlichen Netzstart und vor Cache-/Ergebnisübernahme prüfen; laufende Ladungen entwerten. `ReleaseFehler` darf weder Wiederholung noch Rückfall auslösen.
- Proben ausdrücklich um Sperre zwischen zwei Blöcken, während Poolwartezeit/Retry und vor Ergebnisübernahme erweitern. Mutation „interne Sperrprüfung entfernt“ muss einen konkreten Vertragsverstoß nachweisen.

Ausschließlich gelesen und eine jsdom-Vertragsprobe im Speicher ausgeführt; nichts geschrieben. Keine Server-Probeläufe.

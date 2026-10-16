**FREIGABE (Plan): ja.** Die drei P2-Vertragslücken aus R1 sind geschlossen. Keine neuen P1-/P2-Befunde; ein verbleibender P3-Hinweis.

**P3 – Überschneidungen sind auch ab 16 Kandidaten möglich.**  
Die [Listenregel](C:/dev/Seasonaledge/docs/review_prompts/2026-10-16_options_b3b_plan_v2.md:41) verhindert Überschneidungen nur unterhalb von 16 Kandidaten. Bei 16 Tickern mit identischem Percentile wählen beide Sortierungen dieselben alphabetisch ersten acht. Das Gegenbeispiel ergibt acht Überschneidungen.

Empfehlung: Die tiefe Liste **immer** aus den Kandidaten bilden, die nicht bereits in der hohen stehen. Seitenprobe und Mutation zusätzlich mit mindestens 16 Kandidaten und identischen Percentiles ausführen. Das ist eine nicht blockierende Präzisierung der Darstellung.

Die wesentlichen Verträge sind jetzt tragfähig:

- `neu_rand` verwendet strikte Wertvergleiche und behandelt Gleichstände korrekt.
- `rang_status` trennt fehlenden Sessionwert, zu kurze Historie und gesperrte Historie, ohne unvollständige Rangeinträge einzuführen.
- Die Sprungregel definiert Beobachtungsabstände, aktuelle Änderung, Nullmedian und Vorgängerdatum ausdrücklich.
- IV/RV verwendet gespeicherte RV, klare Eingangsgrenzen und keinen Rückfall auf andere Herleitungen.
- Sessionbindung, Altdateien, Filter, Sprachwechsel und Leserkompatibilität sind im Prüfplan berücksichtigt.

Read-only geprüft; keine Dateien geändert. Die Freigabe betrifft den Plan, nicht die noch ausstehende Umsetzung.

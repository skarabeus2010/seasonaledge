**Drei Befunde verhindern die Freigabe:**

1. **Hoch (P1): Reparatur kann nicht freigegebene Zeilen verändern.**  
   [scripts/backfill_skew_vrp.py:250](C:/dev/Seasonaledge/scripts/backfill_skew_vrp.py:250) reduziert den zeilenweisen Diff auf ein Dictionary nach Datum. Anschließend werden **alle** Zeilen dieses Datums geändert, einschließlich ausdrücklich als „unverändert“ ausgewiesener Zeilen.

   Reproduziert mit zwei Zeilen desselben Datums: `cm` und `single`, beide bisher `vrp_pts=1`. Der Bericht genehmigt ausschließlich für `cm` den Wert `10`; tatsächlich erhalten beide `10`. Die Invariante passiert, weil auch ihre Rücksetzung nach Datum arbeitet. Zielhash und vollständiger Berichtsvergleich verhindern diesen Fehler nicht.  
   **Korrektur:** Doppelte Zieldaten vor der Berichterstellung und unter der Sperre ablehnen oder durchgehend eindeutige Zeilenidentitäten verwenden.

2. **Mittel (P2): Fehlendes `vrp_pts` lässt eine zulässige Reparatur scheitern.**  
   [scripts/backfill_skew_vrp.py:256](C:/dev/Seasonaledge/scripts/backfill_skew_vrp.py:256) unterscheidet beim Zurücksetzen nicht zwischen fehlendem Schlüssel und vorhandenem `null`. Bei einer normierten Zeile mit gültigem ATM/RV, aber ohne `vrp_pts`, sind Diff und Vorprüfung erfolgreich. Der Schreiblauf scheitert anschließend an der Invariante: Die Vergleichskopie enthält jetzt `vrp_pts: null`, der Ausgangsstand enthielt keinen Schlüssel.  
   **Korrektur:** Schlüsselanwesenheit erhalten und beim Vergleich ursprünglich fehlende Felder entfernen. Fixture für „fehlend“ und „explizit null“ ergänzen.

3. **Mittel (P2): Der geforderte Nachweis „Snapshot noch unter Sperre“ fehlt.**  
   [scripts/verify_skew_historie_sperre.py:151](C:/dev/Seasonaledge/scripts/verify_skew_historie_sperre.py:151) prüft konkurrierende History-Schreiber, aber keinen konkurrierenden Zugriff während `danach`. Die Mutation bei [scripts/verify_skew_historie_sperre_mutation.py:43](C:/dev/Seasonaledge/scripts/verify_skew_historie_sperre_mutation.py:43) verschiebt den Snapshot **vor** die History. Sie deckt nicht die ausdrücklich verlangte Mutation „Sperre nach History, vor Snapshot lösen“ ab. Diese könnte die vorhandenen Prüfungen passieren.  
   **Korrektur:** Linux-Probe mit konkurrierendem Sperrversuch innerhalb von `danach`, dazu die entsprechende Mutation.

Die übrigen Prüfaufträge ergeben:

- **Sperrmechanik:** Frisches Lesen, Schreiben und `danach` liegen im Sperrbereich; `finally` schließt den Deskriptor auch auf Fehlerpfaden. Die Frist verwendet eine monotone Uhr, mit bis zu etwa 0,5 Sekunden Polling-Nachlauf. Im Repository fand ich keinen weiteren aktiven Produktionsschreiber der History außerhalb der drei umgestellten Skripte.
- **Cron:** Der verschobene Zusammenführungsblock ist gegenüber `HEAD` **AST-identisch**. Die Closure ändert seine Berechnung nicht. Bei `SperreBelegt` bleiben beide Dateien unverändert; die unbehandelte Ausnahme liefert Exit 1. Der Workflow sammelt den Fehler und endet ebenfalls erfolglos. **Health kann trotzdem zunächst grün bleiben**, da [scripts/daily_health_check.py:415](C:/dev/Seasonaledge/scripts/daily_health_check.py:415) erst bei mehr als drei Tagen Alter wegen Frische abwertet.
- **Massive-Backfill:** Ohne `overwrite` gewinnt jetzt bewusst der frisch vorhandene Punkt; mit `overwrite` bleibt „neue Rekonstruktion gewinnt“ erhalten. `+N Punkte uebernommen` passt zum Runner-Ausdruck. Der zusätzliche Logs-Mount passt zum Compose-Mount. Bei Prozessabbruch bleibt durch atomaren Ersatz die alte oder neue vollständige History; zwischen History und Snapshot kann weiterhin der alte Snapshot stehen.
- **Reparaturvergleich:** Endliche Floats überstehen die JSON-Rundreise; im geprüften Beispiel blieb der kanonische Vergleich identisch.
- **Wächter:** Sie rufen echte `build`-/`main`-/Anwendungsfunktionen auf und ersetzen Datenbeschaffung beziehungsweise Rekonstruktion. Die beiden oben reproduzierten Reparaturfälle fehlen.

Read-only geprüft, keine Dateien geändert. Eigene Ausführungsnachweise: isolierte Originalfunktionen im Speicher und AST-Vergleich mit Python 3.14. Die gemeldeten Linux- und Mutationstestläufe habe ich nicht erneut ausgeführt.

**FREIGABE (Code): nein**

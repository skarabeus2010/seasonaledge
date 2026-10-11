**Urteil**

**V1a noch nicht freigegeben.** Auflagen 2, 3 und 5 sind im Code erfüllt; 1 und 4 bleiben teilweise offen. Diff und neue Dateien lesend geprüft, AST von 23 Python-Dateien geprüft. Nichts geschrieben, Wächter und Mutationstests nicht ausgeführt; Linux-Locknachweise nicht selbst reproduziert.

**Befunde**

1. **Hoch — Importierte Dateischreiber umgehen die Sperre weiterhin.** Beispielsweise schreibt `from scripts.build_flows_rebalancing import main; main()` trotz Aktivierungsmarke `flows_rebalancing.json`: Die Sperre sitzt ausschließlich im `__main__`-Block ([Schreibpfad:100](C:/dev/SeasonalEdge/scripts/build_flows_rebalancing.py:100)). Dasselbe gilt für Kalender-JSON/ICS, Index-Studie, Wahlen und Dekadendaten. Die Client-Hülle schützt diese Dateiausgaben nicht; der Wächter prüft diese Importaufrufe nicht.

2. **Hoch — Importierte DB-Schreiber nehmen keinen gemeinsamen Lock.** Die Client-Hülle prüft die Marke beim Aufbau der Schreibanfrage, gibt anschließend aber den echten Query-Builder zurück ([Hülle:53](C:/dev/SeasonalEdge/shared/supabase_client.py:53)). Wird danach die Aktivierung gesetzt und erst anschließend `.execute()` aufgerufen, erfolgt der Write während der Sperre. `aktivierung_setzen()` wartet auf diesen Importpfad nicht. Auch importierter Newsletter-Versand hält keinen Lock über den Versandteil.

3. **Mittel — Flows kann nach geplanter Unterdrückung weiterhin rot werden.** Der Workflow akzeptiert Exit 75, führt danach aber unverändert die Frischeprüfung aller sechs Dateien aus ([Workflow:47](C:/dev/SeasonalEdge/.github/workflows/flows_update.yml:47)). Ist die absichtlich unveränderte Rebalancing-Datei älter als 26 Stunden, setzt diese Prüfung `fail=1`. Der Wächter sucht lediglich die 75-Abbildung und erkennt das nicht.

**Auflagen**

- Importierbare Schreib-/Versandeinstiege über ihre gesamte Laufzeit unter den gemeinsamen Lock stellen; Dateiausgaben ebenfalls absichern. Den ausdrücklich erlaubten Kalender-Build erhalten.
- Importpfade und die Reihenfolge „Anfrage aufgebaut → Aktivierung gesetzt → Ausführung“ im Wächter prüfen.
- Im Flows-Workflow gezielt die Frischeprüfung des mit 75 unterdrückten Panels ausnehmen; die übrigen Panels weiterhin prüfen.
- `--dry-run` genügt dem Render-Vertrag: Beide Newsletter kehren vor Versand und `refresh_log` zurück. Für die verwendeten Client-Aufrufmuster einschließlich `_with_retry` ist statisch kein zusätzlicher Fehler ohne Marke erkennbar.

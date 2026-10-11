**Urteil**
Der Fix ist für den Einjahresfall korrekt, aber nicht vollständig robust. Ein grüner Sonntags-Audit ist damit noch nicht nachgewiesen.

**Befunde**

- Ein Jahr → `std_dev=None`; zwei gültige Jahresrenditen → korrekte Stichproben-Standardabweichung. Beide Originalfunktionen offline geprüft, JSON strikt serialisierbar.
- **P2:** `len(month_data)` zählt auch ungültige Renditen. Ein gültiges Jahr plus `0/0` ergibt weiterhin `std_dev=NaN`, zudem falsche Fallzahl und Gewinnquote ([cache_manager.py](C:/dev/SeasonalEdge/shared/cache_manager.py:104)).
- **P2:** Ein Monatsanfangskurs von null überlebt `preprocess`; dadurch werden Mittelwert, Median und Extremwerte unendlich und der gesamte Upsert scheitert weiterhin.
- **P2:** Der Upsert-Fehler wird jetzt sichtbar, bleibt aber verschluckt: Der Aufrufer erhält normale Ergebnisse; Nightly zählt keinen Schreibfehler ([cache_manager.py](C:/dev/SeasonalEdge/shared/cache_manager.py:65)).
- Einziger produktiver Aufrufer ist Nightly. Der Audit repariert `monthly_stats` auch mit `--fix` nicht selbst ([check_db_completeness.py](C:/dev/SeasonalEdge/scripts/check_db_completeness.py:692)).

**Auflagen**

- Nur gültige, endliche Monatsrenditen aggregieren; Fallzahl, Gewinnquote und Standardabweichung auf derselben Stichprobe berechnen.
- Schreibfehler an Nightly weitergeben und dort als fehlgeschlagen zählen.
- Vor Sonntag muss ein erfolgreicher Nightly mit deploytem Fix die fehlenden Zeilen erzeugen; anschließend Coverage lesend bestätigen. Andere Auditdimensionen separat prüfen.
- Keine Dateien oder Datenbankdaten geschrieben; keine Live-DB-Prüfung durchgeführt.

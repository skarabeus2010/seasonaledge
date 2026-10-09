# Codex-Antwort: Code Stress-Ampel, Runde 1

codex
1. **Mittel (P2) – Sperre greift erst nach dem Laden:** [shared/stress_score.py:257](/C:/dev/Seasonaledge/shared/stress_score.py:257). Lauf A lädt alte Kurse und pausiert; Lauf B lädt korrigierte Kurse und veröffentlicht; anschließend erhält A die Sperre und veröffentlicht seinen alten Stand als neuesten Lauf. Reproduziert mit 800 Kursen und einer Schlusskurskorrektur um −20 %: **99,87/Rot → 60,46/Grün**, obwohl die aktuelle Rechnung weiterhin Rot ergibt. **Änderung:** Sperre vor dem Laden erwerben; Laden und Berechnung in den abgesicherten `try`-/Abbruchpfad aufnehmen. Diesen Parallelfall ergänzen.

2. **Mittel (P2) – Completeness prüft unveröffentlichte Daten:** [scripts/check_db_completeness.py:263](/C:/dev/Seasonaledge/scripts/check_db_completeness.py:263). Beispiel: Der letzte fertige SPY-Lauf ist mehrere Sitzungen alt; ein neuer Lauf schreibt aktuelle Zeilen, scheitert jedoch beim Rücklesen. `_max_value` berücksichtigt dessen unveröffentlichte Zeilen und meldet trotzdem aktuelle Daten. Auch andere Ticker können fehlende SPY-Aktualität verdecken. **Änderung:** Für Stress ausschließlich den jüngsten fertigen SPY-Lauf auswählen und dessen Zeilen prüfen; ohne fertigen Lauf Rot melden.

3. **Mittel (P2) – Aufräumen liest Laufmetadaten unvollständig:** [shared/stress_score.py:311](/C:/dev/Seasonaledge/shared/stress_score.py:311). Die Abfrage ist unpaginiert; Metadaten werden nie gelöscht. Bei 1.003 fertigen Läufen und einem REST-Limit von 1.000 bleiben im reproduzierten Fall fünf statt zwei Score-Versionen erhalten. Weitere Versionen sammeln sich an; bereits geleerte Läufe verursachen weiterhin einzelne DELETE-Aufrufe. **Änderung:** Metadaten vollständig und stabil paginieren, die zwei neuesten fertigen Läufe global bestimmen und bereits bereinigte Läufe kennzeichnen oder deren Metadaten sicher entfernen.

Die **29/29 Prüfungen einschließlich Snapshot-Vergleich bestehen**, mit ausschließlich speicherbasierter Anpassung der Testeingabe. SQL-Liveprüfung und Mutationen habe ich nicht ausgeführt. Die Deploy-Reihenfolge ist grundsätzlich schlüssig; Schritt 3 muss bei fehlgeschlagener SQL-Prüfung stoppen.

FREIGABE: nein

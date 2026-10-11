**Urteil**

**V1a noch nicht freigegeben.** Diff und neue V1a-Dateien lesend geprüft; Syntax/AST der 19 Pflicht-Skripte und drei neuen Python-Dateien geprüft. Nichts geschrieben, Wächter und Mutationstest nicht ausgeführt.

**Befunde**

1. **Hoch — Importaufrufe umgehen die Sperre.** `refresh_ticker_data(...)` schreibt Kurse und Statistiken ohne eigenen Schutz. Ein `python3 -c` mit Import erreicht diesen Pfad trotz Aktivierungsmarke; die Sperre greift ausschließlich beim direkten Skript-/Modulstart ([Nightly:49](/C:/dev/SeasonalEdge/scripts/nightly_refresh.py:49), [Einbau:586](/C:/dev/SeasonalEdge/scripts/nightly_refresh.py:586)). Einen solchen aktuellen Produktionsworkflow habe ich nicht gefunden; der ausdrücklich angefragte alternative Einstieg bleibt offen.

2. **Hoch — Die Kennung erlaubt jeden Produktionsmodus.** `produktion(name)` prüft weder erlaubten Lauf noch Modus ([Sperre:66](/C:/dev/SeasonalEdge/shared/produktionssperre.py:66)). Eine passende `SA_AKTIVIERUNG` lässt auch Nightly und Newsletter-Liveversand durch. Das überschreitet v5, das nur ausdrücklich benannte Build-/Abnahmepfade und Newsletter ohne Versand/Writes erlaubt. Die Umgebungsvariable ist als Transport geeignet; ihre ungefilterte Vererbung ist problematisch.

3. **Hoch — Der Mutationstest isoliert Dateiausgaben nicht.** Bei „Marke wird nicht geprüft“ starten sämtliche echten Pflicht-Skripte. Tote Netzwerkproxies verhindern keine lokalen Writes: Kalenderbauer und Rebalancing erzeugen Dateien im tatsächlichen Projektbaum ([Probe:128](/C:/dev/SeasonalEdge/scripts/verify_produktionssperre.py:128), [Kalender:127](/C:/dev/SeasonalEdge/scripts/build_calendar_data.py:127)). Wiederhergestellt werden nur vier Quelldateien, keine Ausgaben ([Mutation:82](/C:/dev/SeasonalEdge/scripts/verify_produktionssperre_mutation.py:82)). Der dokumentierte Kopielauf schützt diesen einzelnen Lauf, der Test erzwingt ihn jedoch nicht.

4. **Mittel — Geplante Sperren erscheinen als Betriebsfehler.** Die systemd-Units haben kein `SuccessExitStatus=75`; Newsletter-/Scanner-Workflows behandeln 75 ebenfalls als Fehler. Die in v4 verlangte `refresh_log`-Zeile fehlt: geschrieben wird nur stderr ([Sperre:67](/C:/dev/SeasonalEdge/shared/produktionssperre.py:67)). Dadurch bleibt eine erwartete Unterdrückung vom gewöhnlichen Ausfall schlecht unterscheidbar.

**Auflagen**

- Importierbare Schreib-/Versandeinstiege absichern und direkte Datei-, `-m`- sowie Importaufrufe prüfen.
- Aktivierungszugang auf erlaubte Läufe/Modi begrenzen; Kennung nur gezielt weitergeben.
- Mutationstest ausschließlich in einem erzwungen isolierten Baum ausführen, einschließlich aller Ausgaben und ohne Produktionsmounts.
- Exit 75 als geplante Unterdrückung gesondert behandeln und den vorgesehenen neutralen Betriebsnachweis ergänzen; andere Fehler müssen rot bleiben.
- Eine liegengebliebene Lockdatei allein blockiert keinen Lauf. Ein offener exklusiver Lock blockiert jedoch auch passende Kennungen: vor Abnahme-Unterprozessen freigeben, während die Marke bestehen bleibt.
- Die `[ohne-deploy]`-Bedingung und die Timer-Startunterdrückung stehen an den vorgesehenen Stellen. Linux-Lockverhalten wurde hier nicht ausgeführt.

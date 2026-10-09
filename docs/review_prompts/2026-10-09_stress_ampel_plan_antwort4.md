# Codex-Antwort: Plan Stress-Ampel, Runde 4

codex
**v4 ist noch nicht freigabefähig.** Geprüft am Repository-Stand `95209ec`, ohne Codeänderungen oder Live-DB-Zugriff. X2 behebt den Einwand zu kurzen Reihen; die Versionierung löst die bisherigen Vollauf-Probleme grundsätzlich. Drei Lücken bleiben:

1. **HOCH — X1/Nightly: Sieben Vergleichstage erkennen historische Kurskorrekturen nicht zuverlässig.**

   **Konkreter Fall:** Bei 4000 Schlüssen wird Schluss Nr. 901 korrigiert. Er liegt außerhalb des gesamten Eingabefensters der letzten sieben Scores. Deren Score und S bleiben deshalb exakt gleich, obwohl frühere gespeicherte Scores falsch geworden sind. In einer synthetischen Gegenprobe änderte sich der Score am korrigierten Tag von **15,45 auf 100**, während alle sieben geprüften Endwerte identisch blieben. Datumsmenge, Zeilenzahl und Datumsgrenzen bleiben ebenfalls gleich. Nightly hängt trotzdem an; Frontend und letzter-Wert-Health-Check erkennen den veralteten Verlauf nicht.

   **Änderung:** Beim fertigen Lauf einen reproduzierbaren Fingerabdruck des gesamten verwendeten Kursprefixes speichern, einschließlich Datum und Close. Vor jedem Anhängen diesen Prefix vollständig vergleichen; jede Änderung oder Entfernung erzwingt einen Vollauf. Der Siebentagevergleich kann zusätzlich bleiben. Wächter ausdrücklich mit einer Korrektur **außerhalb** des jüngsten Referenzfensters ergänzen.

2. **HOCH — X1/Sperre und Aufräumen: Die beschriebene Prüfung ist keine atomare Schreibsperre.**

   **Konkreter Fall:** Zwei Volläufe prüfen gleichzeitig, finden keinen laufenden Eintrag und legen anschließend jeweils `laeuft` an. Beide dürfen schreiben. Das Aufräumen des zuerst fertigen Laufs kann anschließend die bereits geschriebenen Zeilen des anderen laufenden Laufs löschen. Nightly ist außerdem nicht ausdrücklich derselben Sperre unterstellt. Nach zwei Stunden kann ein noch arbeitender Prozess als abgebrochen gelten und später dennoch veröffentlichen.

   **Änderung:** Sperrerwerb atomar und für **alle** Schreiber festlegen, einschließlich Nightly und Aufräumen. Eigentümerkennung und Ablaufübernahme müssen verhindern, dass ein verdrängter Prozess weiter schreibt oder veröffentlicht. Aufräumen darf keine aktiven Läufe erfassen. Das lässt sich in der ohnehin vorgesehenen SQL-Datei mit passenden Datenbankoperationen vorsehen. Wächter: gleichzeitigen Erwerb mit einer Barriere erzwingen; zusätzlich Vollauf gegen Nightly und Weiterarbeit nach Sperrübernahme prüfen.

3. **HOCH — X1/Nightly und Leseregel: Anhängen veröffentlicht Daten vor ihrer Abnahme.**

   **Konkreter Fall:** Alle neuen Zeilen werden erfolgreich geschrieben, danach scheitert der Rücklesevergleich oder das Metadaten-Update. Anders als im Plan behauptet, fehlt dann **kein** Tag. Der Lauf steht weiterhin auf `fertig`, seine Zeilen decken die Kurse vollständig ab, und das Frontend akzeptiert bereits ungeprüfte Ergänzungen. `letztes_datum` und `n_scores` können gleichzeitig den alten Stand enthalten.

   **Änderung:** Eine verbindliche Veröffentlichungsgrenze festlegen: Leser dürfen ausschließlich bis zum bestätigten `letztes_datum` lesen. Erst nach erfolgreichem Rücklesevergleich werden Grenze, Mengen und Kursfingerabdruck gemeinsam freigegeben. Unbestätigte Zeilen bleiben unsichtbar und müssen beim Wiederanlauf ausdrücklich überprüft beziehungsweise ersetzt werden. Alternativ erhält auch Nightly eine neue vollständige Version. Wächter: alle Writes erfolgreich, anschließend Rücklesefehler beziehungsweise Metadatenfehler; tatsächliche Frontend-Datumsmenge und Wiederanlauf prüfen.

Die entschiedene Formel, Gewichtung und Mindesthistorie müssen dafür nicht erneut geöffnet werden. Die verbleibenden Einwände betreffen die zugesicherte Konsistenz im laufenden Betrieb.

FREIGABE: nein

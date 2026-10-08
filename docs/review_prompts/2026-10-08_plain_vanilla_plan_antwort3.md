# Codex-Antwort: Plan /plain-vanilla, Runde 3


codex
**Phase 1A ist noch nicht freigabefähig.** Die Verschiebung von täglicher Equity, historischem Lückenmodell und Überschneidungen nach 1B ist grundsätzlich sinnvoll. Der verbleibende Umfang enthält aber noch folgende Widersprüche und Abnahmelücken.

Geprüft wurden die drei Vorreviews und die betroffenen Repository-Stellen; zusätzlich habe ich die vorhandenen Kalender direkt ausgeführt. Keine Dateien geändert.

1. **Hoch — Punkt 5: Auch der moderne Kalender ist nicht durchgehend JS=Python.**  
   Die direkte Gegenprobe für `2027-12-31`, NYSE, ergibt **JS: kein Handelstag; Python: Handelstag**. Damit kann die geplante Monatsabschlussprüfung auch künftig unterschiedliche Offenstatus erzeugen. Außerdem kann die letzte Zeile eines eingestellten oder abgeschnittenen Datenbestands historisch sein; „ab letzter Zeile“ belegt keine moderne Kalenderabdeckung.  
   **Änderung:** Für den kleinen, tatsächlich benötigten Zeitraum bereits in 1A einen gemeinsamen, geprüften Kalenderbereich und die Börsenübergabe festlegen. Außerhalb dieses Bereichs keine neue Kalenderentscheidung treffen. Bewertungsstichtag und letztes Kursdatum getrennt führen; `noch_nicht_faellig` ausdrücklich auf den Bewertungsstichtag beziehen. Die vollständige historische Kalendervereinheitlichung kann in 1B bleiben.

2. **Hoch — Punkt 5: Der Vertrag für Eintritte und direkte Zeilenzugriffe fehlt.**  
   Ein zukünftiger **Einstieg** erzeugt keinen offenen Trade; nur ein bereits ausgeführter Einstieg mit ausstehendem Exit tut das. Beide `_makeTrade`-Implementierungen verwerfen bislang außerdem `entry == exit`: Ein Einstieg auf der letzten Kurszeile würde weiterhin verschwinden. Die genannten Hilfsfunktionen decken auch nicht alle aktuellen Monatsprobleme ab: `calc_monthly_10` bestimmt seine „letzten zwei“ Sitzungen direkt aus `days.length`.  
   **Änderung:** Eintritts- und Austrittszustände getrennt festlegen, einschließlich offener Position mit Einstieg auf der letzten Zeile und zunächst 0 % Rendite. Das Aufruferinventar bereits im Plan fachlich zuordnen: Welche direkten Zugriffe werden am laufenden Datenrand korrigiert, welche bleiben ausdrücklich ungelöst bis 1B? Historische Offset-Lücken können verschoben bleiben; bloßes Inventarisieren löst die aktuellen Randfälle nicht.

3. **Hoch — Punkt 6: „Hebel unverändert“ und „beide Zwillinge gleich“ widersprechen sich.**  
   JS-UHTS verwendet die gesamte Kursrendite × 1,5. Python-UHTS verwendet in `calc_uhts` dagegen eine aufgeteilte Rendite vor und nach einem Zwischentermin. Die geplante einheitliche Formel wäre somit bereits eine historische Modelländerung in Python.  
   **Änderung:** Entweder die JS-Formel ausdrücklich als vorläufige gemeinsame **Korrektur** beschließen und separat vermessen oder die bestehenden Unterschiede bis 1B beibehalten und die Gleichheitszusage entsprechend begrenzen. Für gestoppte Trades muss dieselbe vorläufige Renditeregel wie für regulär geschlossene Trades gelten.

4. **Hoch — Punkte 2/6 und Python-Gegenprobe: Die Grenze der Zwilling-Gleichheit bleibt offen.**  
   Python `apply_stop_loss` verwendet aktuell High/Low/Open; ein Close-Ausführungspreis allein macht daraus noch keinen Close-Stop. Auch die bekannten EMA-/MACD-Unterschiede bleiben bestehen, sodass dieselben Kursdaten nach der LBR-Vortagskorrektur weiterhin unterschiedliche Trades ergeben können.  
   **Änderung:** Einen ausdrücklich gemeinsamen Close-Modus definieren: Auslösung am Close, Trailing-Peak aus Closes, Ausführung am Close. Bestehende OHLC-Aufrufer und deren Modus abgrenzen. Für LBR in 1A den Vortagszugriff anhand identischer vorgegebener Histogrammvektoren prüfen und bestehende Indikatorunterschiede separat ausweisen; vollständige Trade-Gleichheit erst nach deren späterer Vereinheitlichung verlangen.

5. **Mittel — Punkt 6: Stop und regulärer Exit am selben Tag benötigen eine eindeutige Zuordnung.**  
   Die vorhandenen Stop-Schleifen prüfen einschließlich des regulären Ausstiegstags. Bei Ausführung zum Close haben Stop und regulärer Exit dann denselben Preis. Bei konsistenter Renditeformel dürfen sich dadurch weder Rendite noch Tradezahl ändern; lediglich die Stopkennzeichnung kann wechseln.  
   **Änderung:** Beispielsweise verbindlich festlegen: Stopprüfung einschließlich Exit-Close, bei Auslösung `stopped:true`, genau ein geschlossener Trade. Abnahme für Fixed und Trailing: Stop am regulären Exit verändert Preis und Rendite gegenüber demselben regulären Close-Exit nicht. Einen ursprünglich offenen, tatsächlich gestoppten Trade zusätzlich prüfen.

6. **Mittel — Wächter: Geladene Module beweisen die Änderungen an den Seiten nicht.**  
   Dashboardtermin, konfigurierte Streak, PF-Anzeige und Drawdowntexte liegen teilweise in Inline-Seitenlogik beziehungsweise Übersetzungen. Die Script-Liste von `/plain-vanilla` plus `seasonal-compute.js` führt diese Konsumenten nicht automatisch aus.  
   **Änderung:** Die tatsächlichen Dashboard- und Plain-Vanilla-Funktionen sowie DE/EN-Ausgaben ausdrücklich in die Abnahme aufnehmen. Jede zugehörige Mutation muss dort scheitern — etwa erneut `3*5`, Streak aus ungefilterten Trades oder `.toFixed()` auf einem `null`-PF. Für Python außerdem prüfen, dass neu eingeführte offene Trades aus Statistik und bisheriger Abschluss-Equity ausgeschlossen werden.

Der überarbeitete Snapshot-Hash und die erweiterten Trade-Tupel sind im Code nachvollziehbar. Historische Lücken und tägliche Equity müssen für diese Freigabe nicht vollständig gelöst werden; die oben genannten Abgrenzungen müssen jedoch vor Beginn von 1A feststehen.

FREIGABE: nein

# Codex-Antwort: Plan Stress-Ampel, Runde 2

codex
**v2 behebt wesentliche Einwände, ist aber noch nicht widerspruchsfrei freigabefähig.** Geprüft am Repo-Stand `95209ec`, ohne Codeänderungen oder Live-DB-Zugriff. Die ausdrücklich getroffene Gewichtungsentscheidung aus V7 ist als transparent beschriebenes heuristisches Maß vertretbar; eine zusätzliche Standardisierung ist dafür nicht erforderlich.

1. **HOCH — V2/V6/D: Zwei unterschiedliche Mindesthistorien bleiben verbindlich.**  
   **Konkreter Fall:** Ein Ticker mit 1000 gültigen Schlüssen hat nach D bereits 979 frühere Rohwerte für seinen aktuellen Rang und damit einen gültigen Score. V2 verlangt dagegen 2541 Schlüsse; V6 nennt sowohl diesen Mindestbedarf als auch den ersten Score am 777. Schluss. Der Vorrang gegenüber v1 löst diesen Widerspruch innerhalb von v2 nicht.  
   **Änderung:** Einheitlich festlegen: **777 Schlüsse für den ersten Score, 2541 für die volle Referenz mit 2520 Werten**. Fehltext entsprechend „n von 777 benötigten Kursen“. Die längere Ladehistorie dient der vollständigen Referenz, nicht der Freigabe eines Scores. Komponenten separat staffeln: `dd20` ab 20 Schlüssen, `vol20` und damit `S` erst ab **21**; mit 20 Schlüssen existieren nur 19 Renditen.

2. **HOCH — V3/V6: Die Migrationsprüfung akzeptiert erheblich unvollständige Ergebnisse.**  
   **Konkreter Fall:** Bei 3000 gültigen Schlüssen entstehen nach der 756er-Mindestregel genau **2224 Scores**. Die vorgeschlagene Schranke `90 % × (3000 − 2540)` verlangt lediglich 414. Eine Implementierung, die irrtümlich erst mit voller Zehnjahresreferenz beginnt und nur 460 Zeilen erzeugt, besteht die Prüfung und löscht anschließend 1764 berechtigte historische Scores. Auch eine verkürzt geladene Eingabe kann eine aus sich selbst abgeleitete Mengenschranke bestehen.  
   **Änderung:** Vor dem Schreiben **exakte Datumsmengen** vergleichen: Erwartet werden bei n bereinigten Schlüssen genau `max(0, n − 776)` Scorezeilen, ab Schluss Nr. 777. Vollständigkeit der geladenen Eingabe zusätzlich unabhängig absichern, etwa mit Quellzählung, Datumsgrenzen und vollständig geprüfter Pagination; Rohzeilen und bereinigte Zeilen getrennt protokollieren. Unerklärte Abweichung bedeutet Abbruch ohne Löschung.

3. **HOCH — V3: Wiederherstellung im Speicher beweist keinen belastbaren Rollback.**  
   **Konkreter Fall:** Zwei Upsert-Batches werden geschrieben, danach fällt die Verbindung aus. Derselbe Ausfall verhindert das Rückspielen. Alternativ scheitert die abschließende Löschung nach bereits gelöschten Tickern oder der Prozess wird beendet. Eine JSON-Kopie im Speicher und ein erfolgreicher Fake-Client-Test beheben diesen Produktionszustand nicht.  
   **Änderung:** Sicherung und Migrationsjournal vor dem ersten Write dauerhaft außerhalb des flüchtigen Temp-Verzeichnisses sichern. Wiederanlauf und idempotente Wiederherstellung ausdrücklich definieren, einschließlich Löschfehlern und „Server hat geschrieben, Antwort ging verloren“. Nach Migration und Wiederherstellung den tatsächlichen DB-Bestand paginiert gegen den jeweiligen Sollbestand prüfen. Bei gescheitertem Rollback bleibt die Migration als unvollständig markiert und der Schreibbetrieb gesperrt. Auch diese Fehlerpfade gehören in die Wächter.

4. **HOCH — V3/F: Veröffentlichungsablauf und Schreibsperre enden zu früh.**  
   **Konkreter Fall:** Die Migration gelingt, der Timer startet wieder, anschließend scheitert der Deploy. Der nächste Nightly schreibt erneut IF-Werte. Außerdem zeigt die alte Seite neue Werte keineswegs überall korrekt: Die Hauptampel übernimmt zwar `traffic_light`, aber die KPI-Farbe verwendet weiterhin **40/70**, der Chart ebenfalls; als Quelle erscheint „Isolation Forest“. Das ist in [crash-fruehwarnung.html](/C:/dev/Seasonaledge/landing/pages/crash-fruehwarnung.html:345) konkret sichtbar.  
   **Änderung:** Schreibsperre bis zum **erfolgreich verifizierten Deploy des neuen Schreibers und Frontends** halten. Bei Deployfehler ausdrücklich Wiederherstellung oder gesperrten Betrieb vorsehen. Timer zunächst stoppen, danach Servicezustand erneut prüfen; manuelle Starts müssen dieselbe Sperre respektieren. Für die öffentlich sichtbare Zwischenphase einen konkreten Umschaltmechanismus festlegen, beispielsweise eine Wartungsanzeige für die betroffenen Ausgaben.

5. **MITTEL — V5: Der Health-Check erkennt die alte Methode nicht zuverlässig.**  
   **Konkreter Fall:** Ein alter IF-Datensatz mit `risk_score = 0` und `traffic_light = green` erfüllt sowohl `[0,100]` als auch die neue Grenzregel. Genau dieses Paar ist für die falsch bewerteten Krisentage belegt. Auch ein alter Wert 95/rot besteht. Die Aussage „fängt eine Zeile der alten Methode“ ist deshalb falsch.  
   **Änderung:** Wertebereich und Farbregel als Konsistenzprüfung behalten, aber Methodennachweis ergänzen: etwa die letzte SPY-Zeile unabhängig mit `stress_aktuell(lade_closes("SPY"))` vergleichen, einschließlich Datum, Score mit float32-gerechter Toleranz und Rohmaß. Den vollständigen Migrationsnachweis liefert zusätzlich der Bestandsvergleich aus Punkt 3.

6. **MITTEL — V5: Live berechnet bedeutet im Wochenreport nicht automatisch aktuell.**  
   **Konkreter Fall:** Ein Top-Ticker besitzt genügend Historie, aber seit Monaten keine neuen Kurse. `stress_aktuell(lade_closes(t))` liefert trotzdem einen gültigen grünen historischen Score. Der bisherige Report filtert DB-Zeilen auf die letzten 14 Tage; beim vorgeschlagenen Ersatz entfällt diese Einschränkung, sofern sie nicht ausdrücklich übernommen wird.  
   **Änderung:** Kursdatum im Ergebnis und Report beibehalten und eine Aktualitätsregel festlegen. Veraltete, fehlende und zu kurze Reihen separat ausweisen. „Alle im grünen Bereich“ darf nur bei vollständiger **und ausreichend aktueller** Abdeckung erscheinen.

Die Änderungen an Gewichtung, Punkt-in-Zeit-Formulierung, Messereignis und Gleichstandsregel sind damit nicht erneut infrage gestellt. Die offenen Punkte betreffen den verbindlichen Datenvertrag und einen nachweisbar sicheren Übergang.

FREIGABE: nein

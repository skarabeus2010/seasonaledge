# Codex-Antwort (Schlussantwort; Rohprotokoll nicht im Repo)

1. **Hoch — [decade-compute.js:655](C:/dev/Seasonaledge/landing/js/decade-compute.js:655): Ticker-Rennen nicht vollständig abgesichert.**  
   **Fall:** A startet, danach B; B liefert zuerst, A zuletzt. Der verspätete Seitenabruf A ruft `renderAnomalyInto` zuletzt auf und erhält die gewinnende Marke, etwa in `tdom-analyse.html:1227–1242`. Im Dashboard kann der ältere Abruf `currentTicker` wieder auf A setzen; der neue Tickervergleich akzeptiert dann A. Diese vorgelagerte Rennbedingung besteht bereits, wird durch den Nachtrag aber nicht abgesichert.  
   **Änderung:** Eine fortlaufende Anfragekennung bereits beim Start von `loadTicker` vergeben und durch Seitenabruf und Radar-Nachladen prüfen.

2. **Mittel — [decade-compute.js:654](C:/dev/Seasonaledge/landing/js/decade-compute.js:654), [dashboard.html:2091](C:/dev/Seasonaledge/landing/pages/dashboard.html:2091): Vorheriges Radar bleibt sichtbar.**  
   **Fall:** B ist bereits als neue Analyse sichtbar, während dessen Historie noch lädt. Der Radar-Container enthält weiterhin A. Die Marke verhindert spätere Schreibzugriffe, entfernt aber vorhandene Ergebnisse nicht. Im DOM-Stub reproduziert.  
   **Änderung:** Beim Wechsel beziehungsweise Start der Radar-Berechnung den Inhalt durch einen Ladezustand ersetzen.

3. **Mittel — [decade-compute.js:525](C:/dev/Seasonaledge/landing/js/decade-compute.js:525): Zeilenzahl schützt nicht vor veraltetem Ergebnis.**  
   **Fall:** Übergebene Kurse enden am 30.06.2025; die umfangreichere Nachladeantwort endet am 30.05.2025. Sie gewinnt trotzdem, und das Radar berechnet einen älteren Stichtag. Mit Stub reproduziert; beispielsweise bei einem älteren Cache-Eintrag möglich.  
   **Änderung:** Nachgeladene und übergebene Kurse bereinigt zusammenführen, bei Datumsüberschneidungen die übergebenen Kurse bevorzugen.

4. **Mittel — [decade-compute.js:522](C:/dev/Seasonaledge/landing/js/decade-compute.js:522): Ungültiges Datum am Schalttag.**  
   **Fall:** Letztes Kursdatum `2024-02-29` erzeugt `&date=gte.1993-02-29`. Der ungültige Datumsfilter lässt das Nachladen scheitern; dadurch bleibt die kurze, reglerabhängige Basis bestehen. Filtererzeugung reproduziert.  
   **Änderung:** Jahresverschiebung mit Begrenzung auf den letzten gültigen Monatstag durchführen, etwa mittels vorhandener `_zielTag`-Logik.

Weitere Prüfergebnisse: Ablehnung und eine tatsächlich kürzere Antwort fallen korrekt auf die Eingangsreihe zurück. Bei kurzer Krypto-/Forex-Historie verhindert der erfolgreiche 15-Minuten-Cache weitere identische Netzwerkabrufe; gleichzeitig laufende Abrufe werden allerdings nicht zusammengefasst. Alle sichtbaren Radar-Aufrufer verwenden den neuen Pfad. Der synchrone Aufruf in `fromPrices` bekommt die volle Dekaden-Historie.

Nur gelesen; gezielte Node-Proben ausschließlich im Speicher ausgeführt. Die gemeldeten 34/34 und 18/18 wurden nicht erneut ausgeführt.

FREIGABE: nein

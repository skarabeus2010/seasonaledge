# Codex-Antwort (Schlussantwort; Rohprotokoll nicht im Repo)

1. **Hoch – UTC-Umstellung der erweiterten Jahreskurven unvollständig.**  
   [jahreszyklus.html:550](C:/dev/Seasonaledge/landing/pages/jahreszyklus.html:550), [risikozyklus.html:304](C:/dev/Seasonaledge/landing/pages/risikozyklus.html:304): Der erste Kurstag wird weiterhin gegen lokale Mitternacht gerechnet. **Reproduziert:** 20 tägliche Kurse vom 01.–20.01.2023, Schlusskurse 100 bis 119, Zeitzone New York. `days` beginnt mit `[365,2,3]`; die Kurve zeigt an Tag 21 und 365 **100 statt 119**. Bei Beginn am 02.01. entsteht dort bereits ein falscher interpolierter Wert von 100,5 statt 100.  
   **Änderung:** Auch `days[0]` über `SA.seasonal.tagNummer()` berechnen. Beide tatsächlichen HTML-Builder in den Zeitzonenwächter aufnehmen; dieser prüft bisher ausschließlich den gemeinsamen Builder.

2. **Mittel – Dashboard unterschlägt den empirischen Rang.**  
   [decade-compute.js:656](C:/dev/Seasonaledge/landing/js/decade-compute.js:656): Der Zweig `form === 'karte'` gibt vor der Rangdarstellung zurück. **Eingabefall:** Jeder berechenbare Radarwert, beispielsweise `{rang:75,…}`, zeigt im Seitenabschnitt den Rang, im Dashboard jedoch nicht. Das widerspricht C3 und der v2-Vorgabe gleicher Felder in beiden Renderern.  
   **Änderung:** Rang samt Beschriftung in die Karte aufnehmen und seine Ausgabe in beiden Renderer-Tests prüfen.

3. **Niedrig – Fehlergründe bleiben auf englischen Seiten deutsch.**  
   [decade-compute.js:645](C:/dev/Seasonaledge/landing/js/decade-compute.js:645): Nur „Nicht berechenbar“ wird übersetzt; `a.grund` wird unverändert angehängt. **Eingabefall:** Konstante historische Kurse ergeben auf EN „Not computable: keine Streuung in den Vergleichsjahren“.  
   **Änderung:** Stabile Grundcodes aus dem Kern liefern und im Renderer übersetzen; mindestens einen EN-Fehlerfall testen.

4. **Mittel – Weiterer Datumsfehler im angezeigten Overnight-Jahresverlauf, bereits vorher vorhanden.**  
   [overnight.html:316](C:/dev/Seasonaledge/landing/pages/overnight.html:316): Hier werden zwar zwei lokale Mitternachten verrechnet, aber die Sommerzeit macht den Abstand um eine Stunde kürzer. **Eingabefall:** `2025-07-01` erhält unter Europe/Berlin Tagesnummer **181 statt 182**; dieser Wert geht über `renderCumulative()` in Gruppierung und Diagrammachse ein.  
   **Änderung:** Ebenfalls `SA.seasonal.tagNummer(rows[i].date)` verwenden und einen Sommerzeitfall ergänzen. Dies ist eine zusätzliche Fundstelle zu Prüffrage 5.

Zu den übrigen Prüffragen:

- **Alte Radar-Verbraucher:** In den gepflegten Seiten keine gefunden. Die lokalen, ignorierten Dateien unter `landing/en/` enthalten noch den alten Dashboard-Renderer. Sie werden laut Deploy-Workflow durch `landing/build_en.py --write` neu erzeugt; daher kein eigener Deployment-Befund.
- **Referenz und Schleifenabbruch:** Die Python-Referenz ermittelt Endpunkte unabhängig durch vollständige Suche und nutzt `statistics.stdev`. Der gemeinsame Abbruch ist korrekt: `e` bezeichnet den globalen Reihenindex. Für ältere Zieljahre kann er nur kleiner werden. Historische Lücken führen zu `continue`, nicht zum vorzeitigen Abbruch.
- **T = 7:** Als ausdrücklich begrenzte Heuristik vertretbar; kalendergenaue Prüfung muss diesen Schritt nicht blockieren. Allerdings akzeptiert sie beispielsweise Montag→Montag trotz vier fehlender Werktagskurse. Den Tooltip „Datenlücken über mehrere Tage schließen ein Fenster aus“ deshalb durch die konkreten marktklassenspezifischen Grenzen ersetzen. T = 7 garantiert auch keine Abdeckung sämtlicher Feiertagsblöcke.
- **Testabdeckung:** Die angekündigten exakten Grenzfälle `|z| = 4/3` und `7/3` fehlen im Radarwächter.

Validierung: Zwillingswächter vollständig bestanden; Radar **28/28 ohne Snapshot**, mit ausschließlich speicherbasierter Testzuführung. Snapshot- und Mutationstests nicht erneut ausgeführt. Keine Dateien geändert.

FREIGABE: nein

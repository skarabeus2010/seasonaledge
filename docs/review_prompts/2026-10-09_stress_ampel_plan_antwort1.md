# Codex-Antwort: Plan Stress-Ampel, Runde 1

codex
**Die Richtung ist sinnvoll, der Plan ist aber noch nicht implementierungsreif.** Geprüft am Repository-Stand `95209ec`; Snapshot-Berechnungen ausschließlich im Arbeitsspeicher, keine Änderungen und kein Live-DB-Zugriff.

1. **HOCH · D/B/F — Rundung und Grenzentscheidung widersprechen sich.**  
   **Fall:** „ungerundet“ und „eine Nachkommastelle“ sind unterschiedliche Verträge. Bei 2520 Referenzwerten ergeben 2267 kleinere Werte **89,960317…**: nach Formel gelb, auf eine Nachkommastelle gerundet **90,0**, damit laut Speicherregel rot. Außerdem definiert [create_regime_scores.sql](/C:/dev/Seasonaledge/scripts/create_regime_scores.sql:8) `REAL`, keine Dezimalstelle.  
   **Änderung:** Empfehlung: ungerundeter Score entscheidet überall über die Farbe; Rundung ausschließlich zur Anzeige. Für DB-Parität `DOUBLE PRECISION` für Score und Rohmaß vorsehen. Alternativ bewusst eine gemeinsame Quantisierung samt identischer Rundungsregel festlegen und D entsprechend ändern. Grenzfälle einschließlich DB-Rücklesen testen. Ganzzahlig angezeigte „90“ bei gelber Farbe muss durch präzisere Anzeige oder Erklärung aufgelöst werden.

2. **HOCH · F/D — Gleiche Formel garantiert bei unterschiedlichen Eingaben keine gleichen Ergebnisse.**  
   **Fall:** [crash-fruehwarnung.html](/C:/dev/Seasonaledge/landing/pages/crash-fruehwarnung.html:282) lädt erst ab 2020. Nach vorgeschlagener Formel liefert das für SPY am 07.10.2026 **17,39**, mit voller Referenz **25,75**. Außerdem entfernt das derzeit vorgeschaltete `preprocess` Zeilen anhand der Renditespalte, insbesondere gegebenenfalls den ersten gültigen Schlusskurs; das widerspricht D.  
   **Änderung:** Gemeinsamen Eingabevertrag bis zu den Ladepfaden festlegen: identische Schlusskursquelle, Sortierung, eindeutige Tagesdaten und Bereinigung ausschließlich gemäß D. Für einen aktuellen Wert sind maximal **2541 gültige Schlusskurse** nötig; für den Verlauf entsprechend viel Vorlauf vor dem ersten dargestellten Tag. Erst nach der Berechnung auf den Anzeigezeitraum kürzen. Integrationstests müssen die tatsächlichen Lade-/Adapterpfade einschließen.

3. **HOCH · B — Upsert → Delete ist keine atomare Migration; JSON allein reicht nicht.**  
   **Fall:** Der bestehende Schreiber arbeitet in 500er-Batches. Ein Fehler nach zwei Batches hinterlässt eine öffentlich lesbare Mischung beider Methoden. Eine unvollständig geladene Kursreihe könnte anschließend gültige Altzeilen löschen. Ein paralleler Nightly-Lauf kann dazwischen schreiben.  
   **Änderung:** Neue Daten vollständig vorbereiten und validieren, anschließend Ersetzung einschließlich Löschung transaktional aus einer Staging-Tabelle durchführen; konkurrierende Schreiber koordinieren. Sicherung **aller betroffenen Ticker**, vollständig paginiert, mit Zeilenzahl, Prüfsumme und geprüftem Wiederherstellungsweg. Ladefehler, unerwartet verkürzte Historie und legitim zu kurze Historie müssen unterscheidbare Zustände sein. Frontend-Umschaltung und Datenmigration brauchen einen gemeinsamen Veröffentlichungsablauf.

4. **HOCH · B — `--all-relevant` deckt den Altbestand nicht garantiert ab.**  
   **Fall:** Der Schalter umfasst aktuell drei Symbolkategorien. Früher einzeln berechnete Indizes oder inzwischen entfernte Ticker können außerhalb dieser Liste liegen und alte IF-Werte behalten. Ein Ticker mit legitim weniger als 777 gültigen Kursen erzeugt keine neuen Scores; der bisherige frühe Rücksprung würde seine Altwerte erhalten.  
   **Änderung:** Migrationsmenge aus sämtlichen tatsächlich vorhandenen DB-Tickern bilden, gegebenenfalls ergänzt um das gewünschte Universum. Für jeden Ticker explizit Neuberechnung oder Entfernung protokollieren. Verifiziert zu kurze Historie bedeutet bei der Migration: Altwerte entfernen. Ein Datenladefehler bedeutet: abbrechen, nicht löschen.

5. **HOCH · F/B — Wochenreport und Betriebsprüfungen fehlen als verbindlicher Umfang.**  
   **Fall:** [weekly_report.html.j2](/C:/dev/Seasonaledge/scripts/templates/weekly_report.html.j2:251) nennt weiterhin „Isolation-Forest“, multipliziert `vol_20d` und `drawdown` nochmals mit 100 und meldet bei fehlenden gelben/roten Einträgen „Alle Top-Ticker im grünen Bereich“ – auch wenn sämtliche Scores fehlen. Ein einmaliger Universumslauf lässt diese Daten bei unverändertem Nightly nach 14 Tagen aus dem Report verschwinden. Die adaptive Completeness-Prüfung kann durch diesen Lauf vorübergehend eine regelmäßige Universumsabdeckung erwarten.  
   **Änderung:** Wochenreport einschließlich Einheiten, Datenstand und fehlender Abdeckung aufnehmen. Bei Nightly nur SPY den Report entsprechend begrenzen oder andere Ticker ausdrücklich als nicht aktuell behandeln. Completeness auf das erwartete Schreibuniversum **SPY** konfigurieren; Health-Check zusätzlich auf abgeschlossene Migration und gültige Werte prüfen. Watchlist-Summe als „Grün: x von y berechenbaren Tickern“, fehlende separat ausweisen. Generierte EN-Seiten und ihre Erzeugung ausdrücklich einschließen.

6. **MITTEL · D/F — Mindesthistorie und fehlender Wert brauchen einen vollständigen Ausgabevertrag.**  
   **Fall:** 756 Referenzwerte benötigen zunächst 20 Kurse Vorlauf für den ersten Rohwert: Der erste Score entsteht am **777. gültigen Schlusskurs**, nicht am 756. Ein zweijähriger Ticker bekommt deshalb keinen Score, obwohl seine aktuellen Volatilitäten berechenbar sind. Die bestehenden Renderer erwarten numerische Scores und `features`.  
   **Änderung:** `score = null`, grauer Status und „zu kurze Historie“ festlegen; verfügbare Komponenten trotzdem liefern. Kein `0/100`, kein Einschluss als grün. Referenzanzahl und Referenzzeitraum verfügbar machen. **2520/756 sind als feste Produktkonvention vertretbar**, aber „bis zu etwa zehn Jahre“ ist genauer als „zehn Jahre“ bei jungen Tickern.

7. **MITTEL · D — Die Gewichtung ist vertretbar, ihre Bedeutung ist noch nicht entschieden.**  
   **Fall:** Bei vol5 = vol20 = 1 % und Drawdown = −10 % stammen **4 von 4,6 Rohpunkten** aus dem Drawdown, also 87 %. Koeffizienten von 30/30/40 bedeuten keine entsprechenden tatsächlichen Einflussanteile; beide Volatilitätsfenster überlappen zusätzlich.  
   **Änderung:** Für v1 würde ich die einfache Formel beibehalten und ausdrücklich als heuristisches Maß aus Tagesvolatilität und kurzfristigem Kursrückgang beschreiben. Komponenten vorher zu ranken ist nicht zwingend besser und würde zusätzliche Referenzfenster und Mindesthistorien benötigen. Die Nutzerentscheidung zur konkreten Formel muss jedoch festgehalten werden. Ein monoton fallender Kurs kann hohe Stresswerte haben, obwohl seine Renditevolatilität null ist; das sollte ein erklärender Testfall sein.

8. **MITTEL · D/B — Punkt-in-Zeit und „Nightly deterministisch“ sind zu weit formuliert.**  
   **Fall:** Die Formel verwendet keine späteren Kurse. Nachträglich korrigierte Kurse oder eingefügte fehlende Sitzungen können historische Ergebnisse dennoch ändern. Sie sind deshalb nicht zwingend die damals tatsächlich ausgegebenen Werte. Sieben Kalendertage Upsert reparieren außerdem weder längere Ausfälle noch ältere Kurskorrekturen.  
   **Änderung:** Aussage begrenzen auf „ohne zukünftige Beobachtungen, bezogen auf den verwendeten Kursdatenstand“. Eingabestand dokumentieren. Ausfalllücken seit dem letzten erfolgreichen Lauf nachziehen; bei historischen Änderungen den betroffenen Berechnungsbereich neu schreiben oder einen Vollauf auslösen.

9. **MITTEL · Wächter — Zwillingstests allein sichern Rangfolge und Integration nicht ausreichend.**  
   **Fall:** Zwei Rohwerte können wegen unterschiedlicher Standardabweichungsalgorithmen um weniger als `1e-9` abweichen, aber bei exaktem Gleichheitsvergleich unterschiedliche Ränge erzeugen. Identische Fehler in beiden Implementierungen bestehen den Zwillingstest.  
   **Änderung:** Gemeinsame numerische Vorgehensweise und Gleichstandsregel ausdrücklich festlegen. Zusätzlich unabhängige Sollwerte, konstante und wiederholte Fenster, Präfixinvarianz bei angehängten Zukunftsdaten, aktuelle Funktion gegen letztes Verlaufselement, 776/777 Kurse, Grenzrundung und DB-Rücklesen testen. Migration durch simulierten Batchfehler und unvollständige Eingabe prüfen. Beim Backendadapter das bisherige `preprocess` gezielt als Fehlerfall abdecken.

10. **MITTEL · Messung/F — Ereignis und Nenner sind noch nicht eindeutig.**  
    **Fall:** „Rückgang ≥ 10 % in den folgenden 20 Sitzungen“ kann Endrendite, Tief gegenüber dem Bewertungsschluss oder späteren Peak-to-Trough-Verlust bedeuten. Die letzten 20 Snapshot-Tage haben kein vollständiges Folgefenster. Bei der Farbverteilung können fehlende DB-Tage den Nenner verändern.  
    **Änderung:** Vorab beispielsweise `min(c[t+1:t+21]) / c[t] − 1 ≤ −0,10` festlegen. Rotquote und Basisrate auf denselben auswertbaren Tagen messen, letzte 20 Sitzungen ausschließen, Fallzahlen nennen und überlappende Warnungen als abhängig kennzeichnen. Farbanteile nur über gültige Scores berechnen und fehlende Abdeckung anzeigen. P kann wie vorgesehen eine separate redaktionelle Entscheidung bleiben.

Die unabhängige Snapshot-Rechnung stützt die Plausibilität der Formel:

| Ticker | Grün | Gelb | Rot |
|---|---:|---:|---:|
| SPY | 66,68 % | 20,02 % | 13,30 % |
| S&P 500 | 70,30 % | 19,11 % | 10,59 % |
| QQQ | 77,82 % | 14,85 % | 7,34 % |
| Dow Jones | 70,65 % | 19,02 % | 10,33 % |
| DAX | 71,46 % | 18,60 % | 9,94 % |

Gezählt wurden alle berechenbaren Tage je verfügbarer Historie, mit ungerundeten Grenzentscheidungen. SPY und S&P 500 erfüllen alle vier vorgesehenen Datumsprüfungen. Die Rotanteile zeigen zugleich: Die 90er-Schwelle erzwingt bei einer rollierenden historischen Referenz **keine dauerhaft zehnprozentige Rotquote**.

FREIGABE: nein

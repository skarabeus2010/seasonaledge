**Der Ansatz ist jetzt für den Bau freigabefähig.** Die Heuristik bleibt eine bewusste Näherung; beim Bau muss außerdem der tatsächliche Seiten-Builder an die zugesagte Return-Behandlung angeglichen werden.

1. **Heuristik 7 / 362 / 14: als Übergang tragfähig, aber keine universelle Vollständigkeitsprüfung.**

   Ich habe die Sitzungsfolgen aller 13 Repository-Kalender für 1990–2030 im Speicher geprüft: **0 verworfene von 533 Börsenjahren**. Darunter:

   | Kalender | Spätester Jahresanfang | Frühestes Jahresende | Größter Sitzungsabstand |
   |---|---:|---:|---:|
   | CRYPTO | Tag 1 | Tag 365 | 1 Tag |
   | FOREX | Tag 3 | Tag 363 | 3 Tage |
   | NYSE | Tag 4 | Tag 363 | 7 Tage |
   | TSE | Tag 6 | Tag 362 | 11 Tage |
   | KRX | Tag 4 | Tag 362 | 11 Tage |
   | HKEX | Tag 4 | Tag 363 | 6 Tage |

   Das bestätigt die Schwellen **gegen den implementierten Kalenderbestand**, nicht gegen sämtliche historischen Börsenschließungen. Der NYSE-Kalender nennt die fehlende Prüfung vor 1971 ausdrücklich ([nyse_holidays.py:117](C:/dev/SeasonalEdge/shared/nyse_holidays.py:117)). Die Mittwochsschließungen 1968 und die einzelnen Schließungen 1969 ergeben aus der historischen NYSE-Liste keinen Widerspruch zur 14-Tage-Grenze. [NYSE-Schließungsliste, S. 12](https://www.bcm-news.de/wp-content/uploads/closings-nyse.pdf)

   **Ein historisches Gegenbeispiel gibt es dennoch: NYSE 1914.** Die mehrmonatige kriegsbedingte Schließung würde auch eine vollständig gelieferte Sitzungsreihe verwerfen. Deshalb ist „was länger fehlt, … ist ein Datenloch“ in [Plan v3:15](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-16_true_seasonal_plan_v3.md:15) sachlich falsch. Besser: „Jahre mit Beobachtungsabständen über 14 Kalendertagen werden vorsorglich ausgeschlossen; auch außergewöhnliche Börsenschließungen können darunterfallen.“ [NYSE-Schließungsliste, S. 5](https://www.bcm-news.de/wp-content/uploads/closings-nyse.pdf)

   Umgekehrt kann die Heuristik **mehrere** fehlende Sitzungen akzeptieren: Bei Crypto bleiben beispielsweise 13 fehlende Tage zwischen zwei Beobachtungen zulässig. Diese Grenze sollte der Text ebenfalls abdecken. Die Kalenderumschaltung muss dafür nicht vorgezogen werden.

2. **Kennzahl auf den Kurven: ja, die zentrale Inkonsistenz aus v2 ist behoben.**

   Erst die normierten Kurven mitteln und dann deren Änderungen berechnen entspricht der Seitenrechnung ([jahreszyklus.html:1774](C:/dev/SeasonalEdge/landing/pages/jahreszyklus.html:1774)). Pearson, Vorzeichentreffer und „immer positiv“ sind dafür als beschreibender Vergleich brauchbar. Die Fenster `[Y−N,Y−1]` und `[Y−N,Y]` sowie die Mindestmenge nach dem Filter passen zusammen.

   Zwei konkrete Abnahmepunkte:

   - **„Januar = erster bis letzter Januarschluss“ stimmt bei dieser Achse nicht immer.** Die Interpolation kann einen Februarkurs einbeziehen ([calculations.py:150](C:/dev/SeasonalEdge/shared/calculations.py:150)). Gegenprobe mit dem echten Seiten-Builder: letzter Januarschluss 100 am 29.01.2021, nächster Schluss 110 am 01.02. → Slot 31 ist **106,6667**. Deshalb konsequent „Änderungen zwischen den Monatsgrenzen der Chart-Achse“ schreiben. Die Kennzahl sollte ausdrücklich die **ungeglätteten** Kurven bewerten; die sichtbare Linie wird zusätzlich geglättet ([jahreszyklus.html:920](C:/dev/SeasonalEdge/landing/pages/jahreszyklus.html:920)).
   - **Fertige `full_365` garantieren derzeit keine korrekte Return-Behandlung.** Der Seiten-Builder prüft vorhandene Returns nicht auf Endlichkeit und verwendet bei fehlendem Return und ungeeignetem Vorgängerkurs teilweise null ([jahreszyklus.html:568](C:/dev/SeasonalEdge/landing/pages/jahreszyklus.html:568)). Der gemeinsame Builder rekonstruiert beziehungsweise verwirft dagegen ([seasonal-compute.js:343](C:/dev/SeasonalEdge/landing/js/seasonal-compute.js:343)). In zwei Gegenproben erzeugte die Seite einmal `NaN` statt eines rekonstruierten Endwerts 110 und einmal Endwert 100 statt Jahresverwerfung. Die im Plan zugesagte Behandlung muss daher **auch im Produktions-Builder umgesetzt und über die echte Seitenprobe geprüft werden**.

3. **Freigabe für den Bau: ja.**

   Die offenen Punkte erfordern keine neue Grundsatzentscheidung. Historische Ausschlüsse korrekt benennen, Achsenänderungen präzise beschriften und die bereits zugesagte Return-Behandlung im Seitenpfad herstellen. Die bisherige Funktion `true_seasonal.py` ist weiterhin nur der umzubauende Ausgangsstand.

Nur gelesen; JavaScript-Proben liefen im Speicher. Keine Dateien geändert und keine Produktionsdaten neu berechnet.

**FREIGABE (Plan): ja**

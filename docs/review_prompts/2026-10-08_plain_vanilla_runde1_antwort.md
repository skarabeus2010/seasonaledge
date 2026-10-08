# Codex-Antwort: Review /plain-vanilla, Runde 1 (gpt-6-astra)


codex
## Teil A — Befunde

**Die Freigabe scheitert an bestätigten Rechen- und Signalfehlern.** Geprüft wurde ausschließlich der Arbeitsbaum, mit ausgeführtem Original-JavaScript in Node und Python-Gegenproben. Keine Dateien wurden geändert.

Eine wichtige Korrektur deiner Annahme: Der eigentliche Python-Zwilling von `strategy-compute.js` ist **`shared/strategies/plain_vanilla.py`**. `shared/backtest_engine.py` ist eine separate Event-Engine. Ich habe beide berücksichtigt, ihre Unterschiede aber nicht pauschal als Frontendfehler gewertet.

### Hoch

**1. Fehlende zukünftige Kurse werden zu abgeschlossenen Trades — BESTÄTIGT.**  
Fundstellen: [strategy-compute.js:65](C:/dev/Seasonaledge/landing/js/strategy-compute.js:65), [strategy-compute.js:275](C:/dev/Seasonaledge/landing/js/strategy-compute.js:275).

- **Eingabe:** September-Vermeidung; Kurse vom 30.09.2025 bis 08.10.2025: `100,110,120,130,140,150,160`.
- **Ergebnis:** Abgeschlossener Trade `30.09.2025 → 08.10.2025`, Rendite **60 %**, Trefferquote **100 %**, Profit-Faktor `999`. Der regelgemäße Ausstieg wäre erst August 2026.
- **Ursache:** `_nearestBackward` liefert für ein zukünftiges Ziel die letzte vorhandene Zeile. `_makeTrade` erkennt diesen gültigen Index nicht als offenen Trade. `_lastTradingDay` verwechselt entsprechend den letzten vorhandenen mit dem letzten tatsächlichen Monatshandelstag.
- **Kleinste Korrektur:** Kalenderziel und Datenverfügbarkeit getrennt prüfen; fehlenden zukünftigen Exit ausdrücklich als offen behandeln. Historische Datenlücken dürfen ebenfalls keinen abgeschlossenen Ersatz-Trade erzeugen.

**2. Stop-Loss rechnet mit nicht erreichbaren Ausstiegspreisen — BESTÄTIGT.**  
Fundstellen: [strategy-compute.js:642](C:/dev/Seasonaledge/landing/js/strategy-compute.js:642), [backtest_engine.py:108](C:/dev/Seasonaledge/shared/backtest_engine.py:108), [plain_vanilla.py:1067](C:/dev/Seasonaledge/shared/strategies/plain_vanilla.py:1067).

- **Gap-Test:** Einstieg 100; nächster Tag `Open=High=Low=Close=80`; Stop 8 %. JavaScript und Event-Engine rechnen **92 / −8 %**. Der tatsächliche Python-Strategiezwilling liefert **80 / −20 %**. Zu 92 gab es in diesem Eingabefall keinen Handel.
- **Trailing-Test:** Einstieg 100; Folgetag `O=100,H=120,L=100,C=115`. Die Event-Engine zieht zuerst das Tageshoch heran und stoppt anschließend zu **110,40**. Der zulässige Verlauf `100 → 120 → 115` erreicht dieses Stopniveau nach dessen Entstehung überhaupt nicht. Die Intraday-Reihenfolge ist aus OHLC nicht bekannt.
- **Kleinste Korrektur:** Im ausdrücklich Close-basierten Frontend zum beobachteten Close aussteigen. Bei OHLC-Stops zuerst Gap und zuvor gültiges Stopniveau prüfen; Tageshoch erst danach für den folgenden Tag übernehmen. Ausführungsmodell dokumentieren.

**3. LBR entscheidet mit dem Schlusskurs des Ausführungstags — BESTÄTIGT.**  
Fundstellen: [strategy-compute.js:542](C:/dev/Seasonaledge/landing/js/strategy-compute.js:542), [strategy-compute.js:551](C:/dev/Seasonaledge/landing/js/strategy-compute.js:551).

- **Eingabe:** NYSE-Handelstage 01.08.2024–01.07.2025; Close 100 bis September, 120 ab Oktober, 80 ab April.
- **Ergebnis:** Einstieg am **01.10.2024 zu 120**. Histogramm am Vortag: `0`; am Einstiegstag: `5,614973262`. Auch der Ausstieg nutzt `hist[i]`.
- **Wirkung:** Die behauptete Vortagsregel gilt hier nicht. Der zur Entscheidung benötigte Schlusskurs ist zugleich der unterstellte Ausführungskurs.
- **Kleinste Korrektur:** Einstieg und Ausstieg anhand des gültigen Histogramms von `i-1` bestimmen.

**4. Regimefilter verändert historische Signale durch Zukunftsdaten — BESTÄTIGT.**  
Fundstelle: [indicators.js:182](C:/dev/Seasonaledge/landing/js/indicators.js:182).

- **Eingabe:** `close[i]=100+i+3*sin(i)`, `i=0…79`, Periode 20. Danach 100 Werte `close[79]*exp(0.04*(j+1))` anhängen.
- **Ergebnis:** Filter `Regime == Bull`, Index **38**: vorher `true`, nachher `false`; zugrunde liegendes Regime wechselt **Bull → Bear**.
- **Wirkung:** Die gesamte Zukunft bestimmt die historischen Vergleichsverteilungen. `shift(1)` beseitigt diesen Look-ahead ausdrücklich **nicht**.
- **Kleinste Korrektur:** Verteilungen ausschließlich aus der bis zum jeweiligen Entscheidungszeitpunkt verfügbaren Historie bilden. Plain Vanilla aktiviert diesen Filter aktuell nicht; der angeforderte gemeinsame Indikatorkern ist betroffen.

**5. Signaltermine und Backtestregeln stimmen nicht überein — BESTÄTIGT.**  
Fundstellen: [plain-vanilla.html:544](C:/dev/Seasonaledge/landing/pages/plain-vanilla.html:544), [plain-vanilla.html:561](C:/dev/Seasonaledge/landing/pages/plain-vanilla.html:561), [dashboard.html:1273](C:/dev/Seasonaledge/landing/pages/dashboard.html:1273).

- **First Five Days:** Mit konstanten Kursen und simuliertem Heute **02.01.2026** zeigt die ausgeführte Signalansicht Einstieg **02.01.**, Ausstieg **08.01.** Der Kern produziert keinen Trade; bei positivem Januarfilter wäre das Handelsfenster **Februar–Dezember**.
- **LBR:** Die Signalansicht setzt pauschal Ende Oktober/April an; der Kern sucht Histogrammwechsel.
- **Sell in May:** Das Dashboard verwendet `3*5`: **21.05.2026**, während Plain Vanilla und Kern den dritten Handelstag **05.05.2026** verwenden.
- **Kleinste Korrektur:** Das `3*5` zu `3` berichtigen; bedingte Strategien aus ihren wirklichen Regeln ableiten. Noch unbekannte Bedingungen als unbestätigten Kalendertermin kennzeichnen.

**6. Santa Claus: falscher Einstieg und belegte Zwilling-Abweichung — BESTÄTIGT.**  
Fundstellen: [strategy-compute.js:192](C:/dev/Seasonaledge/landing/js/strategy-compute.js:192), [plain_vanilla.py:277](C:/dev/Seasonaledge/shared/strategies/plain_vanilla.py:277).

- **Identische Eingabe:** NYSE-Handelstage 01.11.2024–10.01.2025; Close 100 vor dem 25.11., danach 110.
- **JavaScript:** Einstieg **22.11.2024**, Ausstieg 08.01.2025, **+10 %**.
- **Python:** Einstieg **25.11.2024**, gleicher Ausstieg, **0 %**.
- **Ursache:** Der JS-Anker liegt bereits auf dem Mittwoch vor Thanksgiving; zusätzlich `-3` ergibt vier statt drei Handelstage vorher. Die Signalansicht zählt hier korrekt.
- **Kleinste Korrektur:** Bei diesem Anker `-2` verwenden und sicherstellen, dass der Feiertag überhaupt innerhalb der verfügbaren Historie liegt.

**7. „Max Drawdown“ unterschlägt Verluste während offener Positionen — BESTÄTIGT.**  
Fundstellen: [strategy-compute.js:593](C:/dev/Seasonaledge/landing/js/strategy-compute.js:593), [plain-vanilla.html:183](C:/dev/Seasonaledge/landing/pages/plain-vanilla.html:183).

- **Eingabe:** Close `100 → 80 → 110`; Einstieg am ersten, Ausstieg am dritten Tag, Stop deaktiviert.
- **Ergebnis:** Angezeigter Drawdown **0 %**, tatsächlicher zwischenzeitlicher Drawdown **−20 %**.
- **Wirkung:** Der Text verspricht den größten zwischenzeitlichen Rückgang; gerechnet wird nur zwischen abgeschlossenen Trades.
- **Kleinste Korrektur:** Zunächst ehrlich „Drawdown der abgeschlossenen Trades“ nennen. Für den versprochenen Max Drawdown eine tägliche bewertete Portfoliokurve verwenden.

**8. Dashboard mittelt Constant-Fill als echte Beobachtung — BESTÄTIGT.**  
Fundstellen: [dashboard.html:2224](C:/dev/Seasonaledge/landing/pages/dashboard.html:2224), [seasonal-compute.js:378](C:/dev/Seasonaledge/landing/js/seasonal-compute.js:378).

- **Eingabe:** Vollständiges Vorjahr mit Wert 100; laufendes Jahr mit Anstieg auf 120 und `last_actual_day=20`, danach konstante Fortschreibung.
- **Ergebnis:** Saisonmittel an Tag 300: **110**, statt **100** aus dem tatsächlich abgedeckten Jahr.
- **Wirkung:** Der Konsument reicht ungefilterte Jahreskurven weiter; die korrekten Metadaten verhindern dadurch nichts.
- **Kleinste Korrektur:** Im Konsumenten pro ausgewertetem Tag beziehungsweise Zeitraum die Abdeckung prüfen. Den Produzenten nicht pauschal umschreiben.

### Mittel

**9. Weitere Strategie-Zwillinge rechnen nachweislich unterschiedlich — BESTÄTIGT.**  
Fundstellen: [indicators.js:35](C:/dev/Seasonaledge/landing/js/indicators.js:35), [shared/indicators.py:76](C:/dev/Seasonaledge/shared/indicators.py:76), [strategy-compute.js:90](C:/dev/Seasonaledge/landing/js/strategy-compute.js:90).

- **EMA-Probe:** `[100,110,90,120]`, Periode 3: JS `[null,null,100,110]`, Python `[100,105,97.5,108.75]`.
- **Auswirkung auf LBR:** NYSE-Handelstage 25.09.2024–01.07.2025, `close[i]=100+10*sin(i/5)+i/10`: JS Einstieg **01.11.**, Rendite **28,87 %**; Python Einstieg **01.10.**, Rendite **13,7758 %**. Exit jeweils 10.04.2025.
- **Rundung:** `100 → 100.004`: JS speichert **0 %**, Python **0,004 %**. Damit unterscheidet sich auch die Einstufung als Gewinn.
- **Kleinste Korrektur:** EMA-Initialisierung und Warm-up verbindlich festlegen; Renditen erst bei der Anzeige runden. Keine Seite allein aufgrund des Namens „Referenz“ überschreiben.

**10. Fehlende Werte werden nicht zuverlässig ausgeschlossen — BESTÄTIGT.**  
Fundstellen: [plain-vanilla.html:318](C:/dev/Seasonaledge/landing/pages/plain-vanilla.html:318), [strategy-compute.js:85](C:/dev/Seasonaledge/landing/js/strategy-compute.js:85), [indicators.js:245](C:/dev/Seasonaledge/landing/js/indicators.js:245).

- **Fehlender Exit:** `parseFloat(null)` wird `NaN`. `_makeTrade` akzeptiert ihn. Die Statistik zählt **einen Trade**, zeigt Drawdown **0**, Sharpe **0**, Profit-Faktor **999**, während Rendite und Kapital `NaN` sind.
- **SMA-Warm-up:** `[100,100,100]`, SMA200, `Close > SMA` ergibt `[false,true,true]`, obwohl noch kein SMA existiert: JavaScript vergleicht gegen `null` wie gegen 0.
- **Zusätzlich:** Ein gültiger Nullrendite-Trade erhält ebenfalls Profit-Faktor `999`, den die Seite als **∞** anzeigt; `0/0` ist nicht unendlich.
- **Kleinste Korrektur:** Endliche positive Preise und vorhandene Indikatorwerte verlangen; ungültige Trades nicht zählen; undefinierten Profit-Faktor als `null` ausgeben.

**11. Die Vortagsregel wird an einer Aufrufstelle doppelt angewendet — BESTÄTIGT.**  
Fundstellen: [indicators.js:245](C:/dev/Seasonaledge/landing/js/indicators.js:245), [backtest-engine.html:776](C:/dev/Seasonaledge/landing/pages/backtest-engine.html:776).

- **Eingabe:** `[100,90,110,105]`, SMA2, `Close > SMA`; Maske `[false,true,false,true]`.
- **Ergebnis:** Einstieg Index 3 liest `mask[2]=false`. Der tatsächliche Vortag Index 2 erfüllt aber `110 > 100`.
- **Wirkung:** Kein Zukunftszugriff, sondern ein unbeabsichtigter **Zwei-Tage-Lag**.
- **Kleinste Korrektur:** Den Maskenvertrag eindeutig machen. Soll `mask[entryIdx-1]` gelten, muss diese Maske unverschobene Tageszustände enthalten. Andere Konsumenten vor einer globalen Änderung prüfen.

**12. Median verwendet verbotene Indexauswahl — BESTÄTIGT.**  
Fundstelle: [seasonal-compute.js:229](C:/dev/Seasonaledge/landing/js/seasonal-compute.js:229).

- **Eingabe:** Zwei Januarserien mit jeweils 20 Zeilen; Start 100, Endwerte 110 beziehungsweise 130.
- **Ergebnis:** Renditen `[10,30]`, Median **30 %** statt interpolierter **20 %**.
- **Kleinste Korrektur:** Gemeinsame linear interpolierende Quantilfunktion verwenden. Der gleiche Indexausdruck steht auch in der Mondstatistik bei Zeile 625. Die bekannten ToM-Korrekturen melde ich nicht erneut.

**13. „Current Streak“ zählt offene Trades und ignoriert die gewählten Einstellungen — BESTÄTIGT.**  
Fundstellen: [plain-vanilla.html:490](C:/dev/Seasonaledge/landing/pages/plain-vanilla.html:490), [plain-vanilla.html:507](C:/dev/Seasonaledge/landing/pages/plain-vanilla.html:507), [dashboard.html:1201](C:/dev/Seasonaledge/landing/pages/dashboard.html:1201).

- **Eingabe:** Geschlossener Sell-in-May-Trade **+10 %**; danach offener Trade **−20 %** zum 28.02.2025; Heute 03.03.2025.
- **Ergebnis:** Signalansicht **„1 Loser“** statt **„1 Winner“** für realisierte Trades.
- **Ursache:** Es wird nur das Exitdatum geprüft, nicht `open`. Außerdem werden die Streak-Trades aus `rawRows` ohne Zeitraum- und Stopauswahl neu berechnet.
- **Kleinste Korrektur:** Dieselben konfigurierten, geschlossenen Trades wie für die Kennzahlen verwenden.

**14. Signifikanz wird ohne Hinweis auf die Auswahl mehrerer Varianten ausgewiesen — BESTÄTIGT.**  
Fundstellen: [plain-vanilla.html:442](C:/dev/Seasonaledge/landing/pages/plain-vanilla.html:442), [significance.js:76](C:/dev/Seasonaledge/landing/js/significance.js:76), [plain-vanilla.html:184](C:/dev/Seasonaledge/landing/pages/plain-vanilla.html:184).

- **Eingabe:** 20 Trades, davon 15 mit `+1 %`, fünf mit `−1 %`.
- **Ergebnis:** `p=0,021`, Label **„Signifikant“**. Die Registry bietet 22 Strategien sowie veränderbare Zeiträume und Stops; der Test behandelt nur die ausgewählte Serie.
- **Wirkung:** Bei Auswahl eines Treffers aus mehreren Varianten ist dieses Label zu stark. Beispielsweise wäre bei Bonferroni über 22 Tests die Schwelle `0,05/22≈0,00227`.
- **Kleinste Korrektur:** „Unkorrigierter Einzeltest; Mehrfachauswahl nicht berücksichtigt“ anzeigen und die Aussage entfernen, feste Regeln verhinderten Overfitting. Die historische Zahl tatsächlich ausprobierter Parameterkombinationen ist **UNGEPRÜFT**, nicht null.

**15. Newsletter und Seite verwenden unterschiedliche Strategiedefinitionen — BESTÄTIGT AM CODE.**  
Fundstellen: [daily_report.py:1190](C:/dev/Seasonaledge/shared/daily_report.py:1190), [daily_report.py:1196](C:/dev/Seasonaledge/shared/daily_report.py:1196), [strategy-compute.js:152](C:/dev/Seasonaledge/landing/js/strategy-compute.js:152).

- **Datum 04.05.2026:** Die Seite hält Sell in May noch bis **05.05.2026**. Der Newsletter-Code bezeichnet Mai bereits als schwache Sell-in-May-Phase.
- **Santa Claus:** Newsletterfenster **27. Dezember–5. Januar**, dazu pauschal „~75 % Hitrate“; die Seite untersucht ein Fenster ab November bis zum fünften Januar-Handelstag.
- **Kleinste Korrektur:** Varianten eindeutig benennen und Kennzahlen mit Zeitraum, Regeln und Datenbasis versehen. Ob diese Texte tatsächlich versandt wurden, ist **UNGEPRÜFT**.

**16. Handlungssprache und Betragssignalfarben widersprechen der vorgegebenen Darstellungspolitik — BESTÄTIGT.**  
Fundstellen: [plain-vanilla.html:353](C:/dev/Seasonaledge/landing/pages/plain-vanilla.html:353), [plain-vanilla.html:677](C:/dev/Seasonaledge/landing/pages/plain-vanilla.html:677).

- **Eingabe:** Endkapital 1.100 → grüner Betrag; 900 → roter Betrag. Künftiger Einstieg → grünes **„Einstieg (Close)“**, Ausstieg → rot.
- **Wirkung:** Unbestätigte Kalendertermine erscheinen als konkrete Handelsaktionen. Der Disclaimer beseitigt diese Darstellung nicht.
- **Kleinste Korrektur:** Beträge neutral färben; Termine als „Regeltermin / Bedingung noch ungeprüft“ kennzeichnen. Eine juristische Einordnung ist **UNGEPRÜFT**.

### Niedrig

**17. Am handelsfreien Monatsanfang überschreibt eine alte DB-Zeile die Kalenderzählung — BESTÄTIGT.**  
Fundstelle: [app.js:857](C:/dev/Seasonaledge/landing/js/app.js:857).

- **Eingabe:** Heute Sonntag **01.11.2026**, SPY; letzte Zeile 30.10.2026 mit `tdom=22`.
- **Ergebnis:** Ausgeführter Header zeigt **„TDOM 22/20“** für November.
- **Kleinste Korrektur:** Den DB-Fallback entfernen oder ausdrücklich den letzten Handelstag mit dessen eigenem Monat anzeigen.

## Teil B — ausdrücklich korrekt geprüft

- **Jahresnormalisierung und Rückwärtsdefinition der Log-Rendite:** `buildYearData` startet bei 100 und kumuliert ab Zeile 1 den Return derselben Zeile. Der vorhandene Test `scripts/verify_seasonal_twins.py` wurde ausgeführt und bestand vollständig, einschließlich Original-JS-Proben.
- **Bekannte Saisonkorrekturen:** Die getesteten ToM-Zuordnungen, Bewegungszeitpunkte und Behandlung nicht benachbarter Monate sind korrekt. Kein erneuter Befund zur bekannten Fehlerfamilie.
- **Fehlende Jahresrenditen:** Rekonstruktion aus gültigen Schlusskursen beziehungsweise Verwerfen eines nicht rekonstruierbaren Jahres funktioniert in den geprüften Saisonproben.
- **Constant-Fill-Metadaten:** `last_actual_day` wird geliefert; die geprüften `yearCovers`-Fälle stimmen mit Python überein. Der Befund betrifft den Dashboard-Konsumenten.
- **Explizit offene Trades:** `computeStats`, `buildEquityCurve` und der Signifikanztest schließen `open:true` korrekt aus. Fehlerhaft sind die Erkennung mancher offenen Trades und die separate Streak-Berechnung.
- **Down-Month-Filter:** Der Kern verwendet `entryIdx-1` und den davorliegenden 21-Tage-Rückblick. Den bekannten Parameterposten habe ich nicht erneut bewertet.
- **Positionsgröße:** Im geprüften Plain-Vanilla-Pfad gibt es keine zukunftsabhängige Größenoptimierung. UHTS verwendet einen festen Faktor 1,5; eine weitergehende wirtschaftliche Validierung dieses Hebelmodells ist damit nicht ausgesprochen.
- **JS-Trailing-Stop:** Das Aktualisieren des Peaks mit dem aktuellen Close erzeugt bei positivem Stopabstand für sich keinen Zukunftszugriff. Das Problem der unbekannten High/Low-Reihenfolge betrifft die genannten Python-OHLC-Pfade.
- **Heutiger Handelstag:** An regulären Handelstagen berechnet der gemeinsame Header TDOM/TDOY aus Kalender und Börsenerkennung. Die letzte DB-Zeile bestimmt dort nicht den heutigen Zähler. Der handelsfreie Sonderfall steht separat oben.
- **Kosten und Slippage:** Sie werden nicht abgezogen; die sichtbare Seite legt Handelskosten, Steuern und Slippage ausdrücklich als ausgeschlossen offen. Die Behauptung „Kosten fehlen ohne Hinweis“ wäre falsch.
- **EN-Schlüssel:** Alle auf der Seite verwendeten `data-i18n`-/`data-i18n-html`-Schlüssel existieren in `landing/i18n/en.json`.
- **Keine falsche Gleichsetzung von Kurven:** Eine Strategie-Equity ab 1.000 muss nicht jährlich auf 100 zurückgesetzt werden. Diese Normalisierungsregel gilt für die saisonalen Jahreskurven.

**UNGEPRÜFT:** Produktionsdaten, ausgelieferte Seiten, laufende Jobs, tatsächlich versandte Newsletter, historische Parametersuchanzahl sowie Survivorship-, Delisting-, Dividenden- und Kursadjustierungsqualität der Datenbasis. Für Survivorship fand ich auf der Seite keine konkrete methodische Offenlegung. Fehlende gitignorierte Cron-Dateien wurden nicht als Fehler gewertet.

## Teil C

FREIGABE: nein.

# Antwort Codex Runde 3 — P1 (2026-10-10)

Prompt: [2026-10-10_xetra_tdoy_plan_v3.md](2026-10-10_xetra_tdoy_plan_v3.md). model: gpt-6.1-sol

**Urteil:** Die erzeugte Kalenderdatei ist ein tragfähiger Ansatz, aber P1 ist wegen unbelegter Kalenderbereiche, widersprüchlicher Tickerzuordnung und bereits wirksamer Änderungen bestehender Verbraucher noch nicht bereit für die Umsetzung.

Geprüft: Stand `9b0e3ef`, die drei neuesten Versionseinträge, v2 und Antwort 2 sowie die relevanten Produktionspfade. Gegenproben liefen mit Python 3.14, NumPy und den echten JS-Funktionen im Speicher; der getrackte Arbeitsbaum ist unverändert. Mutationstests wurden wegen des Schreibverbots nicht ausgeführt.

**Antworten Fokusfragen**

1. **Erzeugte Datei: ja, mit zusätzlichem Lade- und Aktualitätsvertrag.**
   Der Wächter gehört auf den CI-Runner **vor** „Deploy via SSH“, neben die bestehenden Gates: [deploy.yml:58](C:/dev/SeasonalEdge/.github/workflows/deploy.yml:58).
   Er sollte im Prüfmodus erzeugte Bytes mit Arbeitsdatei **und Git-Inhalt** vergleichen, ohne die Datei zu überschreiben.
   Synchron vor `holidays.js` laden; fehlende oder unvollständige Daten müssen erkennbar scheitern. Auch Node-Prüflader benötigen diese Abhängigkeit.
   Der Dateiname passt zum bestehenden Cache-Buster: [inject_credentials.sh:79](C:/dev/SeasonalEdge/deploy/inject_credentials.sh:79); EN erbt die Referenzen nach der Injection: [deploy.yml:139](C:/dev/SeasonalEdge/.github/workflows/deploy.yml:139).
   Im geprüften nginx-Code steht keine `script-src`-Beschränkung; die vorhandene CSP betrifft `frame-ancestors`: [nginx.conf:158](C:/dev/SeasonalEdge/deploy/nginx.conf:158). Gebautes DE/EN und die tatsächliche Auslieferung bleiben Abnahmegegenstand.

2. **Den globalen Austausch der bestehenden API würde ich dem gemeinsamen Wechsel zuordnen.**
   Einzelne reine Kalenderanzeigen können als separat geprüfter Fehlerfix früher korrigiert werden; das beschriebene P1 verändert zusätzlich Statistikzuordnung, Strategie-Termine und Fehlerrouten.
   Betroffen sind sämtliche gemeinsamen Tageskopf-Verbraucher über [app.js:826](C:/dev/SeasonalEdge/landing/js/app.js:826), insbesondere Dashboard, Jahres-/Monatszyklus, TDOM-Analyse, Overnight, Plain Vanilla und weitere Analyse-Seiten.
   Darüber hinaus: Dashboard-TDOM, nächste Sitzungen und Event-/Wochentags-/Overnight-Auswahl (`dashboard.html:558,621,1281,2150,2189`), Monatsmarker (`monatszyklus.html:439`), TDOM/TDOY-Marker (`tdom-analyse.html:593,888`).
   Strategieauswertung und Signale (`plain-vanilla.html:281,527`, `watchlist.html:310`, `strategy-compute.js:898`) sowie Feiertagsanalysen (`feiertage.html:256`) ändern sich ebenfalls.
   Die JS-Datei verändert Mails nicht direkt; Änderungen der Python-Kalender können Daily-TDOM und Feiertagskontext verändern (`daily_report.py:502,947`), ebenso erzeugte Marktkalenderdaten (`build_calendar_data.py:106`).

3. **Die Nummernsemantik ist weitgehend vollständig; Validierung und Aliasvertrag fehlen noch.**
   `offen` muss ausschließlich den Kalenderstatus ausdrücken, unabhängig von vorhandenen Kursen; geschlossene Tage behalten Vorwärtszahlen und bekommen beide Rückwärtswerte `null`/`None`.
   Für offene Tage gilt rückwärts `−(Periodengesamtzahl − Vorwärtszahl + 1)`; Krypto täglich, Forex ausschließlich Mo–Fr.
   Strenges ISO-Format zusätzlich zur Datumsprüfung verlangen: Python akzeptiert mit `date.fromisoformat()` auch `20260131` und `2026-W05-6`; `datetime` ist außerdem eine Unterklasse von `date`.
   Börse/Bereich vor jeder Wochenend-/Krypto-Abkürzung validieren; Verhalten bei leerer Eingabe plus ungültiger Börse sowie `NASDAQ`, Groß-/Kleinschreibung und `NONE` ausdrücklich festlegen (`v3.md:49–58`, `exchange_holidays.py:522`).
   Reihenfolge und Duplikate erhalten; Mehrticker-Aufrufer müssen außerhalb der Funktion nach Börse gruppieren und Ergebnisse an ihre ursprünglichen Positionen zurückgeben.
   Für die bestehende API unterscheiden: ungültiger Aufruf → Ausnahme; gültige Anfrage ohne n-ten Handelstag → `null`. „`null` mit Grund“ passt nicht unverändert in ihre heutigen Rückgabetypen.

4. **(a)–(e) reichen noch nicht.**
   NumPy prüft den Zählalgorithmus, übernimmt aber dieselben möglicherweise falschen Feiertage; das exklusive Enddatum ist korrekt berücksichtigt. [NumPy-Dokumentation](https://numpy.org/doc/stable/reference/generated/numpy.busday_count.html)
   Die sieben genannten Sollfälle stimmen in meiner Nachrechnung, einschließlich XETRA `(3,193)`; sie prüfen jedoch nicht die Regeln der übrigen Börsen.
   Ergänzen: unabhängig belegte Fälle je Kalender/Regelwechsel, alle fünf Rückgabefelder, Periodenanfänge, Schaltjahre, unsortierte/mehrjährige Eingaben, Duplikate und ungültige Eingaben.
   Bestehende API separat prüfen: `isTradingDay`, Feiertagslisten und inverse Nummernfunktionen sowie Bereichsüberschreitungen von `nextTradingDay`.
   Hinzu kommen echte Seitenpfade, Ladefehler, DE/EN-Einbindung und die `NONE`-Verzweigungen; korrekte Nummern allein verhindern diese Regressionen nicht.
   Mutationen brauchen einen fachlichen Fehlernachweis mit vollständigem Prüflauf. Eine Umordnung unabhängiger Suffixe ist beispielsweise keine wirksame Mutation.

5. **Unbekannte Börsen dürfen keinen Ersatzkalender erhalten; Aufruferprüfung gehört vorher in P1.**
   Danach `get_holidays` und `is_holiday` im selben Änderungspaket strikt machen: [exchange_holidays.py:496](C:/dev/SeasonalEdge/shared/exchange_holidays.py:496).
   Auch `is_trading_day` muss zuerst die Börse prüfen: derzeit liefert eine unbekannte Börse am Samstag einfach `False` (`exchange_holidays.py:524`).
   Ein ausdrücklich dokumentierter Standardparameter `NYSE` kann bleiben; ein unbekannter übergebener Wert muss scheitern.
   Die Fehlerweitergabe mitprüfen: Daily ersetzt Kalenderfehler heute durch Mo–Fr (`daily_report.py:517`); eine Ausnahme allein beseitigt diesen stillen Ersatz nicht.
   Die weiteren Tickerauflöser (`exchange_holidays.py:651,673`) müssen dieselbe kanonische Zuordnung verwenden oder ausdrücklich als Legacy ausgeschlossen werden.

**Befunde**

1. **Hoch — 1950–2035 ist kein belegter Gültigkeitsbereich aller 13 Kalender.**
   HKEX/KRX haben vollständige Tabellen nur für 2016–2026; davor und danach werden reduzierte gregorianische Ersatzlisten verwendet: [exchange_holidays.py:442](C:/dev/SeasonalEdge/shared/exchange_holidays.py:442).
   XETRA erklärt vor 2001 ausdrücklich ungeprüftes Verhalten; die TSE-Tagundnachtgleichen-Näherung nennt erst 1980 als Beginn (`exchange_holidays.py:114,279`).
   Konkrete Gegenproben: **LSE 03.01.2028 → offen**, obwohl offiziell geschlossen; **TSE 23./24.07.2020 → offen**, obwohl die Feiertage dorthin verschoben wurden (`exchange_holidays.py:164,294,297`). [LSE-Kalender](https://www.londonstockexchange.com/equities-trading/business-days), [japanische Feiertagsverschiebungen](https://www8.cao.go.jp/chosei/shukujitsu/gaiyou.html)
   Die Generierung würde diese Fehler unverändert exportieren; Zwillingsvergleich und NumPy könnten dabei grün bleiben. Benötigt werden börsenspezifische Bereiche und ein Status für Annahmen beziehungsweise ungeprüfte Jahre.

2. **Hoch — Die neue Bereichsgrenze bricht bestehende historische Auswertungen.**
   Feiertagsstrategien rufen `get()` für jedes Jahr ihrer Kursreihe auf, ohne untere Kalendergrenze: [strategy-compute.js:536](C:/dev/SeasonalEdge/landing/js/strategy-compute.js:536).
   Mit einer ausschließlich im Speicher ergänzten 1950-Grenze brach die echte Funktion `calc_one_day_holiday()` bei einer 1949 enthaltenden Reihe ab.
   „Max“ reicht die vollständige Historie durch (`plain-vanilla.html:295`); die Oberfläche fängt den Fehler ab und erzeugt ein Ergebnis ohne Kennzahlen (`plain-vanilla.html:288`).
   Der Bereichsvertrag und die Behandlung bestehender langer Historien müssen vor dem Austausch feststehen.

3. **Hoch — Die behauptete gemeinsame Suffixregel existiert in Python nicht.**
   Unbekannte Ticker mit Punkt werden über einen Metadaten-Lookup aufgelöst; fehlt der Eintrag, folgt NYSE: [symbols.py:91](C:/dev/SeasonalEdge/shared/symbols.py:91).
   Ausgeführt: `NEW.DE`, `NEW.PA`, `NEW.L` und `air.pa` ergeben sämtlich NYSE. Die vorgeschlagene JS-Suffixliste würde davon abweichen.
   Zusätzlich widersprechen sich bestehende Python-Auflöser: `SAP` ergibt über `symbols` NYSE, über `get_exchange_for_ticker` XETRA; `ASML` entsprechend NYSE/EURONEXT (`exchange_holidays.py:35,673`).
   Eine gemeinsame, exportierbare Auflösungsregel einschließlich Normalisierung und Vorrangfolge fehlt.

4. **Hoch — Ein Eingabealias `NONE→CRYPTO` erhält die Aufrufersemantik nicht.**
   Verbraucher vergleichen den **Rückgabewert** von `detect()` mit `NONE`: [strategy-compute.js:914](C:/dev/SeasonalEdge/landing/js/strategy-compute.js:914), `watchlist.html:313,395`.
   In der Gegenprobe erzeugte die echte `regeltermine()` mit der geplanten Kennung `CRYPTO` zusätzliche Santa-Claus-/Post-Christmas-Termine; mit `NONE` waren diese Zweige ausgeschlossen.
   Betroffen sind auch die sechs Krypto-Ticker, deren täglicher Kalender bereits richtig war. Diese Kennungsanpassungen können bei globalem Austausch nicht bis P4 warten.

5. **Hoch — Neue Börsenkennungen funktionieren auf `/feiertage` nicht.**
   `HOL_NAMES` enthält nur NYSE/XETRA/LSE/NONE; unbekannte Kennungen erzeugen keine Auswahlkästchen: [feiertage.html:247](C:/dev/SeasonalEdge/landing/pages/feiertage.html:247), `feiertage.html:331`.
   Die echte `getHolidayDates()` ordnete im Speichertest EURONEXT-Daten über ihren NYSE-Ersatznamen zu: **03.04.2026 → „MLK Day“**, **01.05.2026 → „Good Friday“** (`feiertage.html:260`).
   Daten und Ereignisnamen müssen über stabile Kennungen verbunden werden. Die Position in einer sortierten Feiertagsliste ist kein Ereignisvertrag.

6. **Hoch — P1 verändert schon die Verbindung von Kalenderposition und Statistik.**
   Dashboard-Historien bleiben zeilennummeriert, während ihre Auswahl die neue Kalenderposition bekommt: [dashboard.html:472](C:/dev/SeasonalEdge/landing/pages/dashboard.html:472), `dashboard.html:558,633`.
   Der gemeinsame Tageskopf ersetzt an geschlossenen Tagen sogar frisch berechnete Werte durch bestehende `prices.tdom/tdoy`: [app.js:877](C:/dev/SeasonalEdge/landing/js/app.js:877).
   Das betrifft unmittelbar ausgegebene Zahlen und deren Zuordnung. Die Aussage „P1 aktiviert nichts“ beschreibt daher nur die neue Nummernfunktion, nicht das Änderungspaket.

7. **Mittel — Der tatsächlich genutzte API-Vertrag ist größer als die acht genannten Methoden.**
   Produktionscode verwendet zusätzlich `goodFriday`, `thanksgiving`, `_ds`, `_nthDow`, `_lastDow` und `_NYSE_SONDER`: [strategy-compute.js:328](C:/dev/SeasonalEdge/landing/js/strategy-compute.js:328), `backtest-engine.html:543`, `plain-vanilla.html:615`.
   Die Sonderliste verhindert ausdrücklich Trades auf Staatstrauer-/Katastrophenschließungen (`strategy-compute.js:334`).
   Erhalt oder Anpassung dieser Verbraucher muss festgelegt werden; eine reine Schließungszeichenkette liefert noch keine Ereignisarten.

8. **Mittel — Vorhandene Wächter laden die neue Abhängigkeit nicht.**
   Die 1A-/1B-Proben laden fest `holidays.js` als erstes Modul: [probe_plain_vanilla_1a.js:16](C:/dev/SeasonalEdge/scripts/js/probe_plain_vanilla_1a.js:16), `probe_plain_vanilla_1b.js:16`.
   Auch der bisherige Kalenderzwilling führt nur diese Datei aus (`verify_kalender_zwilling.py:85`).
   Ein neuer erfolgreicher P1-Wächter genügt nicht: bestehende Prüflader, Mutationskopien und Anker müssen mit dem Produktions-Ladevertrag weiter funktionieren.

9. **Mittel — Die Bestandszahlen sind am angegebenen Commit nicht reproduzierbar.**
   `SYMBOLS` enthält **370 Ticker**, nicht 366; die im Prompt genannten Börsenhäufigkeiten summieren sich ebenfalls auf 370.
   Vergleich der echten `detect()`-Funktion mit `symbols`: **40 von 370** haben eine andere Börse; zusätzlich verwenden **11 von 370** Forex-Ticker fälschlich die tägliche Wochenmaske — zusammen **51 von 370**, nicht 53 (`symbols.py:109`, `holidays.js:206`).
   Änderungen der LSE-Regeln und der Krypto-Kennung kommen hinzu. Testmenge und Wirkungsbericht müssen aus dem Bestand abgeleitet werden.

**Auflagen vor dem P1-Code**

- Börsenspezifische belegte Kalenderbereiche, Annahmen und ungeprüfte Jahre definieren; die belegten LSE-/TSE-Fehler korrigieren und HKEX/KRX-Ersatzlisten nicht als vollständige Kalender ausgeben.
- Eine kanonische Tickerauflösung mit Normalisierung, expliziter Map, Suffixregeln, Aliasregeln und dokumentiertem Standard festlegen; beide Sprachen und Python-Helfer daran binden.
- Grundlage und Aktivierung trennen: neue Daten/Funktion zunächst isoliert; globalen Austausch erst mit kompatiblen Verbrauchern und konsistenten Statistik-/Preislesern aktivieren.
- Bei vorgezogenem Kalenderfix dessen Umfang ausdrücklich festlegen: `NONE`-Verzweigungen, Feiertagsnamen, historische Bereiche und bestehende Fehlerrouten gehören dann bereits in dieses Paket.
- Nummernvertrag um strikte Typ-/Datumsvalidierung, Validierungsreihenfolge, Aliasbehandlung und unveränderte Rückgabezuordnung ergänzen.
- Ladevertrag für alle HTML-Einbindungen, EN-Erzeugung und bestehenden Node-/Mutationsprüflader festlegen; fehlende Daten dürfen keinen Ersatzkalender aktivieren.
- Abnahme um unabhängige Kalenderbelege, alle fünf Nummernfelder, bestehende APIs und echte Verbraucher ergänzen; Mutationen müssen fachlich wirksam sein und eine benannte Prüfung erreichen.
- Deterministische Serialisierung und vollständigen Hashumfang festlegen; CI-Prüfung vor SSH mit expliziten Node-/NumPy-Voraussetzungen und Vergleich ohne Überschreiben einplanen.

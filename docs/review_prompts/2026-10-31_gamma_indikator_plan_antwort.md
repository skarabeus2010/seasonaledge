1. **R0 ist eine GEX-Heuristik, keine beobachtete Dealer-Positionierung.**

   Der Produktionscode setzt pauschal Call-Gamma positiv und Put-Gamma negativ. Das steht ausdrücklich in [compute_gamma_exposure.py](/C:/dev/SeasonalEdge/scripts/compute_gamma_exposure.py:7). Auch das ursprüngliche [SqueezeMetrics-Papier](https://squeezemetrics.com/download/white_paper.pdf) behandelt diese Positionierungsrichtung als Annahme.

   **Änderung:** „echte GEX“ durch „OI-basierte GEX-Schätzung mit festen Dealer-Annahmen“ ersetzen. Als primäre Klassifikation ausschließlich das ungerundete Netto-GEX-Vorzeichen verwenden. „Spot über/unter Flip“ ist nicht gleichwertig: Der Code erlaubt mehrere Nullstellen und liefert die spotnächste; ohne Nullstelle im Suchbereich bleibt der Flip unbekannt. Siehe [Flip-Suche](/C:/dev/SeasonalEdge/scripts/compute_gamma_exposure.py:179).

   Außerdem festlegen, ob das Regime vom jeweiligen Titel oder vom gemeinsamen `gamma_index` stammt. Beides zu testen erweitert die Familie.

2. **Die GEX-Historie braucht eine Qualitätsprüfung vor jeder Auswertung.**

   Der Altbestand hat laut Doku mehr als einen Stempelfehler: Bis 13.10. wurde auch ein um eine Session veralteter Spot verwendet. Einfaches Umdatieren repariert diese Rechnung nicht. Siehe [OPTIONS.md](/C:/dev/SeasonalEdge/docs/OPTIONS.md:979).

   Zusätzlich dokumentiert die Datei die verlorene Session 19.10. und einen nachgeholten Snapshot für 20.10. mit IV vom Folgetagmorgen. Dieser ist zeitlich nicht gleichwertig und muss für die Studie ausgeschlossen oder separat ausgewiesen werden, unabhängig von seiner Darstellung auf der Website. Siehe [Datenschaden](/C:/dev/SeasonalEdge/docs/OPTIONS.md:1134).

   Die behaupteten 51 beziehungsweise elf Dateien konnte ich lokal nicht bestätigen: Im Checkout liegen eine Altarchivdatei und zwei Sessiondateien. Das widerlegt den gemessenen Serverbestand nicht; dessen Manifest fehlt hier als Prüfbeleg.

   **Änderung:** Ein eingefrorenes Inventar mit Hash, Session, Abrufzeit, Methodenversion, Spot-Herkunft, Abdeckung und Ausschlussgrund verlangen. Fehlende Sessions bleiben unbekannt. „250 Sessions“ ist nur ein frühester Prüfpunkt: Entscheidend sind auswertbare Ereignisse und voneinander getrennte Episoden in beiden Regimen.

3. **R1 und R2 dürfen nicht als Gamma-Regime auftreten.**

   VIX-Laufzeitstruktur und `RV21 > VIX` messen Volatilitätsmerkmale. Selbst gute Übereinstimmung mit dem kurzen R0-Bestand würde keine langfristige Gamma-Gültigkeit belegen. IV-Rang misst ebenfalls keine Positionierungsrichtung.

   **Änderung:** R1 „Volatilitätsumfeld“, R2 „tickerbezogenes IV-Umfeld“ nennen. Für die Hauptstudie zunächst nur **eine** Regel festlegen, beispielsweise `VIX/VIX3M > 1`; VIX9D und RV/VIX als explorative Alternativen behandeln. Dabei handelt es sich um eine Laufzeitstruktur von Volatilitätsindizes, nicht um VIX-Futures-Backwardation.

   Die Prüfung gegen R0 sollte Konfusionsmatrix, Trefferquote je Klasse, Mehrheitsklassen-Baseline und Unsicherheit zeigen. Eine einzige Trefferquote kann bei ungleichen Klassen täuschen.

   Einen geeigneten frei verfügbaren langfristigen Gamma-Ersatz habe ich nicht belegt. Cboe bietet historische Optionsdaten mit OI als Datenprodukt an; daraus folgt keine kostenlose vollständige Rekonstruktionsbasis. Siehe [Cboe Option EOD Summary](https://datashop.cboe.com/option-eod-summary). Die fehlende historische OI-Basis lässt sich durch IV-Inversion nicht ersetzen.

4. **Der Einstieg am Schluss des Signaltags ist für die Handelsaussage nicht zulässig.**

   Das Signal verwendet den endgültigen Schlusskurs; der GEX-Snapshot entsteht später. Diese Informationen waren für eine Ausführung zum selben Schluss nicht verfügbar. Beim DAX liegt außerdem der US-Schluss nach dem XETRA-Schluss.

   **Änderung:** Zwei Ausgaben trennen:

   - Ereignisdiagnostik: Schluss `t` bis Schluss `t+h`, ausdrücklich ohne Ausführbarkeitsbehauptung.
   - Handelsregel: frühester festgelegter Ausführungszeitpunkt nach Verfügbarkeit sämtlicher Eingaben, etwa nächstes reguläres Open.

   Für den DAX immer das zuletzt **vor seinem Entscheidungszeitpunkt** bekannte US-Regime verwenden. Alle Horizonte auf der Börsensitzungsachse des Zielinstruments zählen.

5. **Die Indikatoren sind vorab mathematisch zu vereinheitlichen.**

   Der Bestand enthält erhebliche Unterschiede:

   - JavaScript-RSI: SMA-Start, anschließend Wilder-Glättung.
   - Python-RSI: rollierende Mittel der Gewinne und Verluste.
   - JavaScript-EMA: SMA-Initialisierung nach einer Wartezeit.
   - Python-EMA/LBR: `ewm(adjust=False)` ab Reihenbeginn.

   Belege: [JavaScript](/C:/dev/SeasonalEdge/landing/js/indicators.js:29), [Python](/C:/dev/SeasonalEdge/shared/indicators.py:22).

   Ein unabhängig hergeleiteter Grenzfall bestätigt zusätzlich einen JavaScript-Fehler: Für `[1,2,3,4]` ergibt RSI(2) **99,0099 statt 100**. Auch eine vollständig flache Reihe ergibt 99,0099; Python liefert bei fehlenden Verlusten `NaN`.

   **Änderung:** RSI-Verfahren, Initialisierung, Warm-up, Nullfälle und Datenlücken ausdrücklich festlegen und beide Implementierungen gegen eine dritte Referenz prüfen. Keine ungeprüfte Übernahme des Mail-Indikators.

   LBR-Fast-/Slowline-Kreuzungen sind außerdem neue Ereignisregeln. Die bestehende Filter-Engine prüft **Fastline über/unter null**, keine Kreuzung. Siehe [LBR-Filter](/C:/dev/SeasonalEdge/landing/js/indicators.js:275).

   Für Williams %R die Formel eindeutig hinschreiben:
   `−100 × (höchstes Hoch − Schluss)/(höchstes Hoch − tiefstes Tief)`.
   Nullspanne ergibt unbekannt. Schwellenrichtung und historische Originalregel separat belegen; „< 95 % am Tief“ ist dafür zu unklar.

6. **True Seasonal liefert noch kein fertiges 20-Sitzungen-Signal.**

   [true_seasonal.py](/C:/dev/SeasonalEdge/shared/true_seasonal.py:8) mittelt normierte Jahreskurven auf einer interpolierten **365-Tage-Achse**. Das schützt vor Verwendung späterer Jahre, definiert aber noch keinen Handelstagsadapter.

   **Änderung:** Vorab festlegen:

   - Historienfenster und Mindestzahl vollständiger Vorjahre;
   - Abbildung von `t` und der 20. folgenden Börsensitzung auf die Kurve;
   - Behandlung von Schalttagen und Jahreswechseln;
   - unbekannt bei unzureichender Historie, kein stiller Ersatz.

   Am Jahreswechsel müssen beide Kurvenwerte aus dem Informationsstand von `t` entstehen. Eine für das Folgejahr nachträglich berechnete Kurve könnte sonst inzwischen abgeschlossene Daten einschleusen.

   TDOM zunächst explorativ behandeln. Sonst sind „Saison positiv/negativ“ und „Monatswechsel“ weitere unterschiedliche Spezifikationen.

7. **Familie und Hauptfrage müssen erheblich kleiner und eindeutig werden.**

   Die Universumsliste enthält **14 Titel**, nicht 15. Die Signale ergeben **acht gerichtete Regeln**, nicht sieben: je zwei für RSI(2), RSI(14), LBR und %R. Damit entstehen schon:

   `14 × 8 × 2 Regime × 2 Saisonklassen × 5 Horizonte = 2.240 Zellen`

   Bei drei Regimeklassen sind es 3.360. Weitere Proxy-, TDOM- und Richtungsvarianten kommen hinzu.

   **Mein Vorschlag:** SPY, QQQ und DIA als konfirmatorischen Kern verwenden; DAX und Einzelaktien zunächst explorativ. Nur **5 HT** konfirmatorisch testen; 1/10/15/20 HT vollständig beschreibend ausgeben. Acht Signalrichtungen behalten, aber nur ein Volatilitätsmerkmal und ein Saisonmerkmal.

   Entscheidend ist der **Zusatznutzen**: Verbessert das Regime dieselbe Indikatorregel? Verbessert Saisonalität diese nochmals? „In einer Zelle signifikant, in der anderen nicht“ beantwortet diesen Unterschied nicht. Dafür direkte Effektunterschiede beziehungsweise Interaktionen prüfen.

8. **Kontrolle und Bootstrap müssen zur Frage passen.**

   „Alle Tage desselben Regimes“ reicht für den Zusatznutzen der Saisonalität nicht: Saison- und Indikatoreffekt bleiben vermischt.

   **Änderung:** Kontrollen nach Ticker, Zeitabschnitt, Regime und – beim bedingten Indikatoreffekt – derselben Saisonklasse bilden. Zusätzlich die ungefilterte Indikatorregel vergleichen. Pooling-Gewichte vorab festlegen, damit häufige Signale einzelner Titel das Ergebnis nicht bestimmen.

   Die Williams-Vorlage bietet passende Bausteine: gemeinsame Sitzungsachse einschließlich ereignisfreier Tage, dieselben Bootstrap-Ziehungen für alle Hypothesen und Neuberechnung der Kontrollmittel. Siehe [williams_muster.py](/C:/dev/SeasonalEdge/scripts/research/williams_muster.py:239).

   Für die neue Studie würde ich einen gemeinsamen stationären Datumsbootstrap mit erwarteter Blocklänge **40 Sitzungen**, Sensitivität 20/60, vorab festlegen. Alle Titel und Hypothesen müssen dieselben Datumsziehungen erhalten. Zusätzlich unabhängige Episoden zählen; 200 Signaltage einer Krise sind keine 200 unabhängigen Beobachtungen.

   „Max-T/Holm wie Intermarket“ ist zu unbestimmt. Intermarket verwendet zirkuläre Verschiebungen und Max-T, Williams einen stationären Bootstrap und Holm. Eine konkrete Kombination samt Nullhypothese festlegen; die alten Max-T-Schranken sind nicht übertragbar. [INTERMARKET.md](/C:/dev/SeasonalEdge/docs/INTERMARKET.md:21) nennt zudem das gemeinsame Marktumfeld selbst als offene Einschränkung.

9. **Der Prüfzeitraum passt nicht zu allen Daten und ist nicht automatisch unberührt.**

   R0 beginnt 2026, R2 ungefähr 2025. Beide haben keine Entdeckung bis 2018. Ein gemeinsamer Split 2018/2019 ist deshalb unmöglich. Für R1 kann er funktionieren, sofern die tatsächlich verfügbaren Reihen ausreichend weit zurückreichen.

   **Änderung:** Je Studienarm einen Abdeckungs- und Zeitplan festlegen. Entdeckungsdaten vor jeder Aufbereitung abschneiden, Ergebnisse nicht über Abschnittsgrenzen laufen lassen und sämtliche Varianten vor Öffnung des Prüfzeitraums einfrieren. Genau diese Schutzmaßnahmen enthält die [Williams-Vorlage](/C:/dev/SeasonalEdge/scripts/research/williams_muster.py:7).

   2019–2026 kann ein reservierter historischer Test sein. Wegen bereits bekannter Projektbefunde sollte er nicht pauschal als vollständig unberührt bezeichnet werden. Eine zusätzliche prospektive Bestätigung bleibt nötig.

10. **„Profitabel“ verlangt eine ausführbare Kontokurve.**

   Mittlere Forward-Rendite und mittlerer Zwischenverlust reichen dafür nicht. Festzulegen sind Handelsrichtung, Wiederholungssignale, maximale Position, gleichzeitige Titel, Kapitalbindung, Kosten, Slippage und bei Shorts Finanzierung beziehungsweise Leihe. `^GDAXI` ist zudem kein direkt handelbares Instrument.

   **Änderung:** Pro Ereignis sowohl **MAE ab Einstieg** als auch **Peak-to-Trough-Drawdown** ausweisen; das sind unterschiedliche Größen. Für die Regel zusätzlich eine Kontokurve mit begrenztem Kapitaleinsatz und maximalem Drawdown berechnen. Tages-Schlussdaten erlauben dabei nur einen Schlusskurs-Drawdown; intraday können Verluste größer sein.

   Renditen aus `log_return` berechnen. Beim Open-Einstieg keine Kurse unterschiedlicher Bereinigungsbasis dividieren; die Williams-Vorlage erklärt dieses Problem ausdrücklich. Kostenannahmen und Belastungstest vorab einfrieren.

   Die heutigen Top-Aktien schließlich als **heute ausgewählte feste Fallstudie** bezeichnen. Für Aussagen über eine historische Top-10-Strategie wären damalige Mitgliedschaften einschließlich später ausgeschiedener Titel nötig.

**Schluss: TRAGFÄHIG MIT ÄNDERUNGEN.** Vor dem Bau müssen Datenqualität, Indikatorformeln, Informationszeitpunkt, Hauptfamilie und Handelsmodell feststehen. Danach kann die historische Studie den Zusatznutzen eines Volatilitätsumfelds prüfen. Eine belastbare Gamma-Aussage benötigt eine gesonderte, zeitlich saubere GEX-Historie und ausreichend unabhängige Ereignisse. Ich habe keine Dateien verändert.

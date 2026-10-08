# Codex-Antwort: Methodik Crash-Ampel, KI-Composite, Anomalie

codex
**Die drei Kennzahlen sind derzeit nicht als validierte Prognosesignale belastbar.** Bei der Crash-Ampel kommt ein kritischer Rechenfehler hinzu: Das Backend ordnet ungewöhnlichen Tagen niedrige Risikowerte zu. Backend und Frontend berechnen bei allen drei Kennzahlen unterschiedliche Größen.

Ich habe ausschließlich gelesen und Berechnungen im Arbeitsspeicher ausgeführt. Keine Dateien geändert, keine Datenbank abgefragt. Die Messungen unten verwenden die eingefrorenen SPY-/QQQ-Dateien bis **07.10.2026**; bei kalenderabhängigen Berechnungen wurde der Bewertungszeitpunkt auf **08.10.2026** fixiert. Sie belegen Implementierungsunterschiede, ersetzen aber keinen Prognose-Backtest.

## 1. Crash-Ampel / Crash-Frühwarnung

### Definition: Was tatsächlich gerechnet wird

**Backend:** [scripts/compute_regime_scores.py:65](C:/dev/Seasonaledge/scripts/compute_regime_scores.py:65)

Aus Schlusskursen entstehen **acht**, nicht sieben Features:

- Tagesrendite \(r_1=100(C_t/C_{t-1}-1)\).
- Standardabweichung der Tagesrenditen über 5, 10 und 20 Beobachtungen, mit Pandas-Stichprobenstandardabweichung.
- Renditen über 5, 10 und 20 Beobachtungen.
- Abstand zum höchsten Schlusskurs der letzten 20 Beobachtungen.

Nach Entfernen unvollständiger Featurezeilen müssen mindestens 100 Zeilen übrig bleiben; bei vollständigen Kursen sind dafür mindestens 120 Kurszeilen erforderlich.

Ein `IsolationForest(contamination=0.05, random_state=42)` wird auf **allen übergebenen Featurezeilen** trainiert. Es gibt keine festgelegten wirtschaftlichen Featuregewichte. Anschließend werden dieselben Zeilen bewertet.

**Der entscheidende Fehler liegt in Zeile 95:**

\[
Risk_t=100\left(1-\frac{\#\{s_i\ge s_t\}}N\right)
      =100\frac{\#\{s_i<s_t\}}N
\]

Bei `decision_function` bedeuten **niedrigere Werte ungewöhnlichere Beobachtungen**. Das bestätigt auch die [scikit-learn-Dokumentation](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html). Der Code liefert damit einen Rang der **Normalität**, den er als Risiko interpretiert.

Schwellen: **Rot ≥70**, **Gelb ≥40**, sonst Grün. Derselbe Richtungsfehler steckt in [shared/anomaly_engine.py:196](C:/dev/Seasonaledge/shared/anomaly_engine.py:196), Funktion `compute_market_regime`.

**Frontend:** [landing/js/dash-compute.js:246](C:/dev/Seasonaledge/landing/js/dash-compute.js:246)

Hier läuft kein Isolation Forest. Berechnet wird:

\[
H_t=0{,}3\sigma_5+0{,}3\sigma_{20}+0{,}4|DD_{20}|
\]

Der Score ist der gerundete Anteil historischer Vergleichswerte unter \(H_t\), aus höchstens 252 Beobachtungen. Schwellen wieder 40/70. Renditen und 10-Tage-Volatilität werden ausgegeben, gehen aber **nicht** in diesen Score ein.

Zusätzlicher Fehler: Aktuelle Volatilitäten verwenden 5/20 Renditen, historische Vergleichswerte durch inklusive Schleifen **6/21 Renditen**; beim historischen Hoch werden 21 statt 20 Schlusskurse berücksichtigt. Die Referenz enthält außerdem den aktuellen Tag. Siehe Zeilen 253–285.

### Zwillinge: nachgewiesene Unterschiede

Ausführung der bestehenden Berechnungen auf identischen Kursreihen:

| Eingabe | Backend | Frontend |
|---|---:|---:|
| SPY bis 07.10.2026, gesamte verfügbare Historie | **85,4 · Rot** | **13 · Grün** |
| QQQ bis 07.10.2026, gesamte verfügbare Historie | **73,6 · Rot** | **8 · Grün** |
| SPY abgeschnitten am 16.03.2020 | **0,0 · Grün** | **100 · Rot** |

Die eigenständige Crash-Seite bevorzugt Datenbankwerte und verwendet die JS-Berechnung nur als Fallback: [crash-fruehwarnung.html:312](C:/dev/Seasonaledge/landing/pages/crash-fruehwarnung.html:312). Das Dashboard berechnet direkt in JavaScript: [dashboard.html:2126](C:/dev/Seasonaledge/landing/pages/dashboard.html:2126). Unterschiedliche Ampelfarben sind damit systematisch möglich.

**Noch eine dritte Skala:** Der historische Chart-Fallback berechnet `round(H*10)` ohne Perzentilbildung und ohne Begrenzung auf 100. Er ist deshalb auch mit der aktuellen JS-Ampel nicht vergleichbar: [crash-fruehwarnung.html:428](C:/dev/Seasonaledge/landing/pages/crash-fruehwarnung.html:428).

### Look-ahead und Datenrand

- **Historische Backendwerte enthalten Zukunftswissen:** Sowohl Forest als auch Rangverteilung werden auf der gesamten heute übergebenen Historie gebildet. Ein Wert für 2008 ist dadurch keine Rekonstruktion des damals verfügbaren Signals.
- **Messbarer Revisionseffekt:** Für SPY am 02.12.2013 ergeben sich **79,5** bei Training bis 16.03.2020 und **42,7** bei Training bis 07.10.2026. Zwischen diesen beiden Berechnungen wechseln **1.153 von 6.811 gemeinsamen historischen Tagen** die Ampelfarbe. Beide Varianten sind für 2013 bereits rückblickend; der Vergleich zeigt zusätzlich die Instabilität.
- Der CLI-Inkrementallauf trainiert neu, schreibt aber nur neue Tage. Der Nightly überschreibt dagegen die letzten sieben Kalendertage. Die gespeicherte Historie kann somit verschiedene Modellstände mischen. Quellen: [compute_regime_scores.py:193](C:/dev/Seasonaledge/scripts/compute_regime_scores.py:193), [nightly_refresh.py:393](C:/dev/Seasonaledge/scripts/nightly_refresh.py:393).
- Die Crash-Seite verwendet den letzten vorhandenen DB-Wert auch bei veraltetem Stand. Nach mehr als vier Tagen erscheint eine Warnung; die Ampel bleibt bestehen. Fehlende historische DB-Tage werden nicht einzeln ergänzt. Quellen: [crash-fruehwarnung.html:314](C:/dev/Seasonaledge/landing/pages/crash-fruehwarnung.html:314), [crash-fruehwarnung.html:488](C:/dev/Seasonaledge/landing/pages/crash-fruehwarnung.html:488).
- Die Berechnungen zählen Kurszeilen, prüfen selbst aber keinen lückenlosen Börsenkalender. Fehlende Sitzungen verändern deshalb die tatsächliche Fensterdauer.

**Korrektur zum genannten Verwendungsumfang:** Der Wochenreport liest die neuesten DB-Werte innerhalb von 14 Tagen. Im aktuellen Tagesreport ist `market_regime` ausdrücklich leer; dessen Dateikopf beschreibt diesen Stand nicht korrekt. Quellen: [weekly_report.py:84](C:/dev/Seasonaledge/shared/weekly_report.py:84), [daily_report.py:1464](C:/dev/Seasonaledge/shared/daily_report.py:1464).

### Aussagekraft und Darstellung

Auch nach Korrektur der Rangrichtung wäre dies zunächst eine **Messung aktueller Auffälligkeit**, keine Crashprognose:

- Es gibt kein Crash-Ziel beim Training.
- Hohe Volatilität kann auch nach einem Crash oder bei starken Aufwärtsbewegungen auftreten.
- `contamination=0.05` belegt keine Crash-Basisrate. Die Rangbildung verwendet nicht die daraus folgende Ausreißerklassifikation.
- Eine Rotgrenze beim 70. Perzentil markiert ungefähr die oberen **30 %** der Referenzverteilung. „Historisch selten“ ist dafür zu stark. In der SPY-Vollberechnung sind 2.542 von 8.460 Tagen rot.

Die Seite erklärt zwar ausdrücklich, dass sie keinen Crash vorhersagt. Gleichzeitig suggerieren „Frühwarnung“, „Risk-Score“ und „Stress-Regime“ mehr als gemessen wird; die behauptete Rangrichtung widerspricht sogar dem Backend. Die Methodik nennt außerdem sieben statt acht Features: [crash-fruehwarnung.html:396](C:/dev/Seasonaledge/landing/pages/crash-fruehwarnung.html:396).

**Keine einschlägige Prognosevalidierung gefunden.** Die „Backtest“-Kacheln zählen lediglich Farben, Mittelwert und Maximum. Sie messen weder Trefferquote noch Vorlauf oder Fehlalarme: [crash-fruehwarnung.html:482](C:/dev/Seasonaledge/landing/pages/crash-fruehwarnung.html:482).

Für eine Frühwarnvalidierung wären vorab festzulegen:

- Ereignis, etwa mindestens 10 % Verlust gegenüber dem Bewertungsschlusskurs innerhalb der nächsten 20 Handelstage.
- Zusammenfassung überlappender Ereignisse und Warnungen zu Episoden.
- Zeitlich getrennte Trainings-, Kalibrierungs- und Testphasen; Training und Referenzverteilung ausschließlich aus damals verfügbaren Daten.
- Ereignis-Trefferquote, Anteil erfolgreicher Warnungen, Fehlalarmepisoden pro Jahr, Warnzeitanteil und Vorlauf.
- Vergleich mit einfachen Volatilitäts-/Drawdown-Regeln **bei gleicher Warnhäufigkeit** sowie der unbedingten Ereignisrate.

**Urteil — hohe Priorität:** Die aktuelle Crash-Warninterpretation vorübergehend abschalten. Rangrichtung, Fenster und Datenquellen vereinheitlichen; historische Werte anschließend nachvollziehbar neu erzeugen. Als **„Marktstress-Monitor“** kann die Kennzahl nach Reparatur bleiben. „Frühwarnung“ erst mit belegtem Vorlauf verwenden.

## 2. KI-Composite-Score

### Definition: Was tatsächlich gerechnet wird

Im Frontend gilt:

\[
Score=\operatorname{round}_{0{,}1}\left[2{,}5(M+F+W+T)\right]
\]

Alle vier Komponenten liegen zwischen 0 und 1. Bullish ab 6,5, Bearish bis 3,5. Quelle: [dash-compute.js:175](C:/dev/Seasonaledge/landing/js/dash-compute.js:175).

| Komponente | Tatsächliche Frontendberechnung |
|---|---|
| **Musterpfad \(M\)** | Anteil ausgewählter Match-Jahre mit positiver **Gesamtjahresrendite**. Keine unmittelbare Messung der Match-Güte. |
| **Trend \(F\)** | 30-Kalendertage-Rendite des gewichteten historischen Musterpfads; `clip((R+3)/6, 0, 1)`. |
| **Monatsquote \(W\)** | Anteil historischer Jahre mit positiver Rendite vom ersten zum letzten Slot des aktuellen Monats; laufendes Jahr ausgeschlossen. |
| **Tracking \(T\)** | \(0{,}7\max(0,\rho)+0{,}3(1-\min(1,MAE/Spannweite))\), aktueller Jahresverlauf gegen saisonalen Mittelwert. Bei Mittelwertspannweite null wird der normierte Fehler auf null gesetzt. |

Die Match-Jahre werden anhand des Jahresverlaufs **bis zum heutigen Kalendertag** ausgewählt:

- Pearson: Ähnlichkeit \(=50(\rho+1)\).
- Alternative: euklidische Distanz **nach Standardisierung beider Reihen**, Ähnlichkeit `max(0,100−5*Distanz)`.
- Anschließend Top-N, standardmäßig fünf; deren vollständige Jahreskurven werden nach Ähnlichkeit gewichtet und zentriert geglättet.

Quelle: [dash-compute.js:112](C:/dev/Seasonaledge/landing/js/dash-compute.js:112). Die Einzel-Seite erlaubt 3–10 Matches und 1–21 Glättungstage; ihre Standard-Historienauswahl ist „10 Jahre“.

Die Monatsrendite ist dabei keine übliche Monatsultimo-zu-Monatsultimo-Rendite: Sie beginnt am ersten Monatsslot. Zwischen Handelstagen können interpolierte Werte stehen.

### Zwillinge: wesentlich verschieden

Das Python-Backend verwendet dieselben Gewichte und Signalgrenzen, aber andere Komponenten:

1. **Ähnlichkeit:** `fastdtw`, falls importierbar; sonst Pearson-Korrelation. Frontend-Pearson und Backend-Pearson-Fallback sind grundsätzlich verwandt, DTW ist eine andere Methode. [ai_models.py:16](C:/dev/Seasonaledge/shared/ai_models.py:16).
2. **Prognose:** Prophet statt Musterpfad. Im Quick-Modus beziehungsweise bei fehlendem/fehlerhaftem Prophet wird die Komponente starr **0,5**, also 1,25 Gesamtpunkte. Prophet vergleicht außerdem den ersten mit dem letzten zukünftigen Prognosewert, nicht den letzten beobachteten Kurs mit dem Prognoseende. [ki_score.py:92](C:/dev/Seasonaledge/shared/ki_score.py:92), [ki_score.py:273](C:/dev/Seasonaledge/shared/ki_score.py:273).
3. **Tracking:** Python übergibt die Anzahl tatsächlicher Handelstage als Länge einer **Kalendertageskurve**. Es vergleicht dadurch einen zu kurzen Jahresabschnitt. JavaScript verwendet Kalendertage. [ki_score.py:250](C:/dev/Seasonaledge/shared/ki_score.py:250), [ki_score.py:280](C:/dev/Seasonaledge/shared/ki_score.py:280).
4. **Monatsquote:** Python prüft die Abdeckung bis zum Periodenende, JavaScript hier nicht. Ein historisches, im Oktober abgeschnittenes Jahr kann im Frontend mit fortgeschriebenem Monatsende mitzählen, während Python es ausschließt. Python schließt das laufende Jahr dagegen nicht grundsätzlich aus, sofern die Periode bereits abgedeckt ist. [calculations.py:329](C:/dev/Seasonaledge/shared/calculations.py:329).

**Konkrete Messung**, gleiche Historie 2006–07.10.2026, fünf Matches, Frontend-Pearson, Glättung fünf; Backend Quick-Modus mit lokalem Korrelationsfallback:

| Eingabe | Backend | Frontend |
|---|---:|---:|
| SPY | **7,4** | **8,8** |
| QQQ | **7,4** | **8,3** |

Bei SPY waren sogar die fünf ausgewählten Jahre identisch. Der Unterschied entsteht vor allem durch **0,5 statt 1,0 im Prognoseteil** und durch **192 statt 281 verglichene Kalenderpositionen** beim Tracking.

Zusätzlicher bedingter Defekt: Der DTW-Zweig übergibt skalare Kurspunkte an `scipy.spatial.distance.euclidean`. Der direkte Callback-Test ergibt `ValueError: Input vector should be 1-D`. `fastdtw` selbst ist lokal nicht installiert; den vollständigen Zweig konnte ich daher nicht ausführen. Tritt dieser Fehler dort auf, liefert die äußere Fehlerbehandlung einen neutralen Teilscore, keinen Korrelationsfallback.

### Look-ahead, Ausreißer und Datenrand

**Nicht jede Verwendung vollständiger Jahreskurven ist Look-ahead.** Für eine heutige Prognose dürfen die späteren Monate bereits abgeschlossener historischer Jahre verwendet werden. Die aktuelle Match-Auswahl betrachtet tatsächlich nur Jahrespräfixe.

Problematisch sind dagegen:

- **Rückwirkende Darstellung:** Die heute ausgewählten Match-Jahre erklären auch den früheren Teil des gezeichneten Musterpfads. Dieser ist kein Verlauf früher tatsächlich ausgegebener Prognosen.
- **Keine explizite Bewertungszeit:** Die Funktionen verwenden die Systemzeit. Historische Daten einfach abzuschneiden genügt für einen korrekten Backtest nicht.
- **Selbstbezug beim Tracking:** Der saisonale Mittelwert enthält auch das aktuelle Jahr. Das ist live kein Zukunftswissen, verbessert aber die gemessene Übereinstimmung teilweise mechanisch. [seasonal-compute.js:373](C:/dev/Seasonaledge/landing/js/seasonal-compute.js:373), [ki_score.py:387](C:/dev/Seasonaledge/shared/ki_score.py:387).
- **Interpolation:** Jahreskurven interpolieren zwischen Beobachtungen und schreiben nach dem letzten Kurs konstant fort. Bei rückwirkendem Abschneiden einer zuvor vollständig erzeugten Kurve können bereits spätere Kurse eingeflossen sein. Die Rohkurse müssen **vor** der Kurvenbildung abgeschnitten werden. [calculations.py:111](C:/dev/Seasonaledge/shared/calculations.py:111).
- **Veraltete Kurse:** Matching und Tracking laufen bis „heute“ statt bis zum letzten tatsächlich verfügbaren Kurs. Fortschreibung kann somit als beobachteter Verlauf eingehen.
- **Jahresende:** Ab Kalendertag 335 fällt der Frontend-Trendteil pauschal auf 0,5 zurück. Jahresübergreifende Prognosen fehlen. `truepath[td]` ist zudem gegenüber dem 1-basierten Tageszähler um einen Slot verschoben.
- **Fehlende Komponenten:** Häufig entsteht ein neutraler Zahlenwert statt „nicht verfügbar“. Ein sichtbarer Gesamtscore kann dadurch aus teilweise fehlender Information bestehen.

**Ausreißerfilter:** In den geprüften KI-Einstiegspfaden wird `filter_year_data` nicht aufgerufen. Ich kann daher keine tatsächlich aktive Ausreißerbereinigung dieser Scores behaupten.

Falls der Filter vorgeschaltet wird, verwendet er Gesamtjahresrenditen beziehungsweise vollständige Jahreskurven; Winsorizing skaliert sogar den ganzen Jahrespfad anhand der Endrendite. Das wäre bei rückwirkender Bewertung innerhalb desselben Jahres Zukunftswissen. Für abgeschlossene frühere Trainingsjahre ist es zulässig, entfernt aber möglicherweise gerade relevante Stressfälle. Quelle: [outlier_manager.py:132](C:/dev/Seasonaledge/shared/outlier_manager.py:132).

### Aussagekraft und Darstellung

**Das Hauptproblem ist die Bedeutung der Summe.**

- Die Komponenten messen unterschiedliche Horizonte: Gesamtjahr, kommende 30 Tage, aktueller Gesamtmonat und bisheriges Jahr.
- Perfektes Tracking eines **fallenden** Saisonalmusters gibt volle Trackingpunkte und erhöht damit den „bullishen“ Score.
- Positive Gesamtjahre sagen nicht unmittelbar etwas über die noch bevorstehende Rendite aus.
- Die vier Komponenten sind nicht unabhängig: Match-Auswahl und Trend verwenden dieselben Jahre; Monatsquote und Tracking nutzen dieselbe historische Basis.
- Bei fünf Matches verändert ein einziges positives statt negatives Jahr den Gesamtscore um **0,5 Punkte**. Das ist eine kleine, zusätzlich ausgewählte Stichprobe.
- Matching auf Kursniveaus kann gemeinsame Trends belohnen, ohne einen zusätzlichen Prognosevorteil gegenüber einer einfachen saisonalen Durchschnittsprognose zu liefern.

Gewichte, ±3%-Mapping und Grenzen 6,5/3,5 sind im Code gesetzt. **Eine empirische Herleitung oder OOS-Kalibrierung dieses konkreten Composite-Scores habe ich nicht gefunden.**

Die Seite nennt „Machine Learning“, „Korrelation/DTW“, „4 unabhängige Sub-Scores“ und einen „Wahrscheinlichkeits-Indikator“. Das Frontend implementiert aber weder DTW noch Prophet; Unabhängigkeit und Wahrscheinlichkeit sind unbelegt. Die angezeigten Ähnlichkeitsprozente sind Transformationen einer Korrelation beziehungsweise Distanz, keine Erfolgswahrscheinlichkeiten. Quellen: [ki-saisonalitaet.html:204](C:/dev/Seasonaledge/landing/pages/ki-saisonalitaet.html:204), [ki-saisonalitaet.html:213](C:/dev/Seasonaledge/landing/pages/ki-saisonalitaet.html:213).

Eine Validierung müsste einen gemeinsamen Prognosehorizont festlegen, jahresweise vorwärts testen und Matching, Filter und Parameter ausschließlich im jeweiligen Trainingsbestand bestimmen. Wesentliche Vergleiche: unbedingte Positivquote, einfacher saisonaler Durchschnitt und derselbe Score ohne Matching beziehungsweise Tracking. Parameterwahl und Tests über viele Ticker müssen als Mehrfachauswahl berücksichtigt werden.

**Urteil — hohe Priorität:** **Umbenennen und Methodik ändern.** Als explorativer „Saisonaler Composite“ kann die Darstellung bleiben. Die Richtungsprognose sollte von der Musterähnlichkeit getrennt werden; „Wahrscheinlichkeit“ und „unabhängig“ streichen. Python und JavaScript müssen dieselbe definierte Methode verwenden.

## 3. Anomalie-Radar

### Definition: Was tatsächlich gerechnet wird

**Backend:** [anomaly_engine.py:25](C:/dev/Seasonaledge/shared/anomaly_engine.py:25)

- Aktuelles Fenster: letzte **zehn Schlusskurse**, daraus **neun Tagesrenditen**.
- Referenz: standardmäßig letzte 20 abgeschlossene Kalenderjahre, mindestens fünf Vergleichsfenster.
- Je historischem Jahr mit mindestens 50 Zeilen: Handelstag suchen, dessen Day-of-Year dem **heutigen** am nächsten liegt, dann rückwärts zehn Kurse auswählen.
- Bei geringfügig kürzeren Fenstern werden Renditevektoren gegebenenfalls mit null aufgefüllt.
- Isolation Forest mit `contamination=0.1`, trainiert auf den historischen Renditevektoren.
- Score:

\[
A=100\left(1-\frac{\#\{s_{\mathrm{historisch}}<s_{\mathrm{aktuell}}\}}N\right)
\]

Hier ist die Rangrichtung grundsätzlich richtig. Die Behandlung gleicher Scores ist jedoch fehleranfällig.

Die Richtung wird separat aus der **Summe** der neun einfachen Renditen bestimmt: oberhalb historischer Mittelwert plus eine Standardabweichung „bullish anomaly“, unterhalb Mittelwert minus eine Standardabweichung „bearish anomaly“.

**Frontend:** [decade-compute.js:267](C:/dev/Seasonaledge/landing/js/decade-compute.js:267)

- Ebenfalls zehn Schlusskurse, also neun Renditeintervalle; nur aus dem laufenden Kalenderjahr.
- Aktuelle Gesamtrendite: \(100(C_{\mathrm{letzter}}/C_{\mathrm{erster}}-1)\).
- Historie: alle verfügbaren Jahre mit mindestens 200 Zeilen; keine 20-Jahresbegrenzung.
- Historisches Fenster endet **vor** dem ersten Handelstag mit `DOY >= aktueller DOY − 5`.
- Score:

\[
A=\min\left(100,\operatorname{round}\left[30\left|\frac{R-\bar R}{s_R}\right|\right]\right)
\]

Bei Standardabweichung null wird der Nenner auf **1 Prozentpunkt** gesetzt. Zusätzlich wird ein Renditeperzentil mit `historische Rendite <= aktuelle Rendite` ausgegeben.

„Leicht anomal“ ab 40, „stark anomal“ ab 70, entsprechend ungefähr 1,33 beziehungsweise 2,33 Standardabweichungen. Das sind gesetzte Skalierungen, keine kalibrierten Wahrscheinlichkeiten.

Das Dashboard verwendet dieses Frontendverfahren: [dashboard.html:2133](C:/dev/Seasonaledge/landing/pages/dashboard.html:2133).

### Zwillinge: konkrete Gegenbeispiele

| Eingabe | Backend | Frontend |
|---|---|---|
| QQQ, Daten bis 07.10.2026 | Score **10**, 20 Vergleichsjahre | Score **34**, 27 Vergleichsjahre |
| Durchgehend konstante Kurse von 2006 bis 07.10.2026 | Score **100**, Richtung „normal“ | Score **0**, Renditeperzentil **100** |

Der konstante Fall zeigt zwei Randprobleme:

- Im Backend sind alle Forest-Scores gleich. Wegen des strikten `<` wird keine Referenz als kleiner gezählt: **maximale Anomalie trotz identischen Verhaltens**.
- Im Frontend zählen wegen `<=` sämtliche identischen Renditen als unterhalb/gleich: **100. Perzentil trotz vollständiger Gleichheit**.

Auch die Fenster stimmen nicht überein. Für den SPY-Vergleich mit 2025 nutzte das Frontend **18.09.–01.10.2025**, das Backend **25.09.–08.10.2025**. „Gleicher Kalenderzeitpunkt“ ist deshalb derzeit nicht erfüllt.

Zusätzlich unterscheiden sich die Renditebegriffe: Bei +10 % und anschließend −10 % meldet die Backend-Summe **0 %**, die Frontend-Gesamtrendite korrekt **−1 %**.

### Look-ahead und Datenrand

- Für eine heutige Auswertung früherer Jahre entsteht durch deren vollständige Verfügbarkeit allein kein Look-ahead.
- Historische Backendtests sind ohne expliziten Bewertungszeitpunkt falsch ausgerichtet: Das aktuelle Fenster stammt vom Datenende, der historische Vergleich vom heutigen Systemdatum.
- Bei veralteten Kursen vergleicht das Backend deshalb unterschiedliche Kalenderzeitpunkte. Das Frontend orientiert den Vergleich immerhin am letzten Kursdatum.
- Anfang Januar kann das Backend aktuelle Kurse aus Dezember einbeziehen, historische Fenster aber nicht über den Jahreswechsel ziehen. Das Frontend wartet auf zehn Kurse im neuen Jahr.
- Fehlende Sitzungen werden nicht explizit geprüft; zehn Zeilen können einen längeren Zeitraum abdecken.
- Bei zu wenig Historie liefert das Frontend ein Objekt mit `score:0`, `status:'normal'`, `n_comparisons:0`. Das Dashboard zeigt dieses als **Normal** an. Der wiederverwendbare Renderer behandelt denselben Fall korrekt als nicht berechenbar. Quellen: [dashboard.html:1467](C:/dev/Seasonaledge/landing/pages/dashboard.html:1467), [decade-compute.js:589](C:/dev/Seasonaledge/landing/js/decade-compute.js:589).

### Aussagekraft und Darstellung

Der Backend-Forest bewertet standardmäßig nur **20 neundimensionale historische Vektoren**, mindestens sogar nur fünf. Die Perzentilauflösung beträgt bei 20 Fenstern fünf Punkte, bei fünf Fenstern zwanzig Punkte. Zudem werden neue Beobachtungen gegen die Scores der Trainingsbeobachtungen eingeordnet; eine kalibrierte OOS-Anomalieverteilung ist das nicht.

Das Frontend ist einfacher interpretierbar, aber:

- Mittelwert und Standardabweichung reagieren empfindlich auf historische Extremjahre.
- Bei vielen Tickern und täglichen, stark überlappenden Fenstern treten auch ohne besonderen Effekt zahlreiche Extremwerte auf.
- Ein ungewöhnlicher Rückblick begründet weder anschließende Trendfortsetzung noch Gegenbewegung.

Der Dashboard-Tooltip bezeichnet das Radar als „Contrarian-Hinweis“ und erklärt Grün/Rot als ungewöhnlich stark/schwach. Tatsächlich färbt der Renderer nach **Abweichungsstärke**, unabhängig von deren Richtung. Ein außergewöhnlicher Kursanstieg kann daher einen roten Score erhalten. Quellen: [dashboard.html:289](C:/dev/Seasonaledge/landing/pages/dashboard.html:289), [dashboard.html:1470](C:/dev/Seasonaledge/landing/pages/dashboard.html:1470).

**Keine Validierung eines Contrarian-Nutzens oder der Grenzen 40/70 gefunden.** Für einen rein beschreibenden Radar wären zunächst historische OOS-Abdeckungsraten und Stabilität zu prüfen. Für ein Handelssignal braucht es zusätzlich vorab definierte Folgerenditen, Ereigniszusammenfassung und Vergleich mit einer einfachen unbedingten beziehungsweise saisonalen Basis.

**Urteil — hohe Priorität für Fehler, mittlere für Weiterentwicklung:** Als beschreibenden **„Renditeabweichungs-Radar“ behalten**. Fenster, Renditebegriff, Gleichstände und fehlende Daten korrigieren. Vorzugsweise einen transparenten, vorzeichenbehafteten Abweichungswert plus empirischen Rang und Stichprobengröße zeigen. Den Contrarian-Anspruch bis zur Validierung entfernen.

## Weitere Vorschläge — priorisiert

1. **Hoch: Verbindliche Methodenspezifikation und gemeinsamer Berechnungskern.** Das Dashboard enthält weiterhin eigene Inline-Kopien, obwohl `dash-compute.js` existiert. Gleiche Namen garantieren derzeit weder gleiche Formeln noch gleiche Datenbasis.

2. **Hoch: Expliziten `as_of`-Zeitpunkt einführen.** Rohdaten zuerst zeitlich abschneiden; erst danach Kurven, Filter, Matches und Referenzverteilungen berechnen. Jahreswechsel, Schaltjahre und Börsenkalender einheitlich behandeln.

3. **Hoch: Fehlend, veraltet und neutral unterscheiden.** Keine Null- oder Halbpunktwerte als Ersatz für ausgefallene Berechnungen. Anzeigen sollten Kursstand, Berechnungsstand, Methode und verfügbare Komponenten nennen.

4. **Hoch: Kleine, gezielte Regressionstest-Sammlung.** Die nachgewiesenen Fälle aufnehmen: Crashtag, konstante Kurse, fehlendes Vergleichsjahr, abgeschnittenes Jahr, Dezember/Januar sowie identische Inputs für beide Sprachen.

5. **Hoch: Prognosen unveränderlich protokollieren.** Mit Datenstand, Methodenversion, Trainingsende und Parametern. Nachträglich neu berechnete historische Scores getrennt von damals tatsächlich ausgegebenen Signalen speichern.

6. **Mittel: Validierungsplan vor Optimierung festschreiben.** Je Kennzahl Ziel, Horizont, naive Vergleichsmethode und Erfolgskriterium definieren. Zeitliche OOS-Tests, überlappende Beobachtungen und Mehrfachauswahl berücksichtigen. Bereits untersuchte Zeiträume nicht anschließend als unberührten Test verkaufen.

7. **Mittel: Unsicherheit und Basisrate sichtbar machen.** „5 positive Match-Jahre“ und „20 Vergleichsfenster“ sind informativer als scheinpräzise Prozentwerte ohne Bezugsgröße. Ähnlichkeit, Seltenheit und Erfolgswahrscheinlichkeit brauchen unterschiedliche Bezeichnungen.

8. **Niedrig: Altbezeichnungen und ungenutzte Modellzweige bereinigen.** `prophet`, `dtw`, „KI“, „Backtest“ und „Frühwarnung“ sollten die tatsächlich aktive Berechnung beschreiben. Die gefundenen Newsletter-OOS-Backtests betreffen andere Scores; sie validieren diese drei Kennzahlen nicht.

# Trendfolge — Plan mit vier Alternativen

> Stand 2026-09-23 · Planungsdokument, **kein Code**. Entstanden aus einer Runde
> Claude ↔ Codex. Alle Wirkungsbehauptungen sind Hypothesen; die Abbruchkriterien
> in Abschnitt 5 stehen **vor** der ersten Rechnung fest.

---

## 0. Die Ausgangslage, und warum sie den Plan bestimmt

Zwei strukturelle Punkte entscheiden mehr als die Auswahl der Indikatoren.

**Unsere Backtest-Engine kann ein Trendfolgesystem nicht ausdrücken.**
`run_backtest(df, events, days_before, days_after)` in `shared/backtest_engine.py:208`
ist ereignisgetrieben: Ein- und Ausstieg sind feste Abstände zu einem
Kalenderereignis. Die Optimierung variiert `days_before × days_after`
(`:349`), nicht beliebige Regeln. Alle 22 Strategien in
`landing/js/strategy-compute.js` sind kalendergebunden. Trendfolge ist dagegen
**zustandsgetrieben** — drin bleiben, solange eine Bedingung hält, mit variabler
Haltedauer. Das ist keine Parametrierung, sondern eine andere Schleife.

**Es gibt nirgends Transaktionskosten.** Python rechnet direkt
`(exit−entry)/entry` (`:304`), JavaScript ebenso (`strategy-compute.js:75`).
Bei einem Trade pro Jahr ist das verzeihlich; bei einem System mit variabler
Haltedauer ist eine Nettoaussage ohne Kosten keine Aussage. Codex weist zu Recht
darauf hin, dass nicht nur der Umsatz zählt, sondern auch Spread, Kurslücken und
Cash-Verzinsung der nicht investierten Zeit.

### Sieben Defekte, die vor dem Bauen geklärt sein müssen

Drei habe ich selbst gefunden, vier kamen aus dem Codex-Review. Alle sind am Code
belegt.

| # | Defekt | Ort | Folge |
|---|---|---|---|
| 1 | **Kein Kostenmodell** | `backtest_engine.py:304`, `strategy-compute.js:75` | Blocker für jede Nettoaussage, nicht für die Konzeption |
| 2 | **`calcRegime` hat Look-ahead** — die Perzentilgrenzen entstehen über die *ganze* Reihe | `indicators.js:159`, `:182` | Der Regimefilter ist für Tests unbrauchbar. Die `[i-1]`-Verschiebung hilft nicht: sie entfernt keinen Bias, der über die Grenzen hereinkam. Der Kommentar im Code nennt das „konsistent mit SMA/RSI" — SMA und RSI sind kausal, das ist der Unterschied |
| 3 | **„LBR bullish" zweimal verschieden definiert** — Filter prüft `fastline > 0`, Saisonstrategie `histogram > 0` | `indicators.js:266` gegen `strategy-compute.js:542` | Zwei Signale unter einem Namen. Das erste heisst „schneller EMA über langsamem", das zweite „MACD-Linie über Signallinie" |
| 4 | ⚠️ **`calc_lbr_november_mai` hat Ausführungs-Look-ahead** — liest `hist[i]` und handelt zum Close **desselben** Balkens | `strategy-compute.js:542` mit `:84` | **Betrifft eine live angezeigte Strategie** auf `/plain-vanilla` und `/dashboard`. Den Histogrammwert eines Schlusskurses kennt man vor diesem Schlusskurs nicht |
| 5 | **`calcSMA`-Filter ohne Null-Prüfung** — anders als EMA, RSI, MACD | `indicators.js:245` | In JavaScript ist `5 > null` wahr. Während der 200-Tage-Aufwärmphase gilt damit **jeder** Tag als „Close > SMA". Trifft ausgerechnet den meistgenutzten Trendfilter |
| 6 | **`calcMomentum` ist nicht das Carhart-Signal** | `indicators.js:133` | Gerechnet wird `(C_t/C_{t−252}−1) − (C_t/C_{t−21}−1)`. Das Skip-Month-Momentum ist `C_{t−21}/C_{t−252}−1`. Algebraisch ist der implementierte Wert das korrekte Momentum **mal** dem Bruttofaktor des letzten Monats. Das Vorzeichen bleibt, **die Rangfolge über Ticker ändert sich** — und genau die braucht Alternative #4 |
| 7 | ⚠️ **`walk_forward` überspringt mit seinen eigenen Vorgaben alle Folds** | `backtest_engine.py:460`, `:472` | Nachgerechnet bei 30 Jahren, `n_folds=5`, `in_sample_ratio=0.7`: jedes OOS-Fenster wird 1 Jahr lang und fällt dann durch die Prüfung `len(oos_years) < 2`. **Fünf von fünf Folds übersprungen.** Mit `n_folds=3` liefe es (3-Jahres-Fenster) — der Standard tut nichts. Zusätzlich trennt die Funktion nach *Ereignisjahr*, nicht nach abgeschlossener Trainingsinformation; Trades können über die Grenze reichen |

Nummer 4 und 7 sind eigene Befunde am laufenden Betrieb und sollten unabhängig von
diesem Plan behoben werden.

---

## 1. Vier Alternativen, in der Reihenfolge, in der ich sie testen würde

Vorgaben für alle: Signal nach abgeschlossenem Tag, Ausführung frühestens am
nächsten handelbaren Open, zunächst nur long oder Cash, kein Hebel, nicht
investiertes Kapital verzinst. Die Parameter sind **vorab gewählte Startwerte,
keine behaupteten Optima**.

### Übersicht

| | Hypothese | Einstieg / Ausstieg | Grösse & Universum | Warum eine andere Wette |
|---|---|---|---|---|
| **#1 Preiskanal-Ausbruch** | **H1:** Neue längerfristige Hochs markieren ausreichend persistente Bewegungen | Kauf, wenn der Close das höchste High der **vorangegangenen 100 Handelstage** überschreitet. Halten, bis der Close unter das tiefste Low der **vorangegangenen 50 Tage** fällt. Der heutige Balken gehört nicht in den Kanal | Fester Kapitalanteil je Markt, kein Zusatzstop. Vorab festgelegter, wenig überlappender Korb liquider ETFs (Aktien, Anleihen, Rohstoffe) | Wette auf das **Überschreiten einer Extremgrenze**, mit Gedächtnis zwischen Ein- und Ausstieg. Nutzt **keinen** unserer neun Indikatoren. Bollinger ist kein Ersatz: Streuung um einen Mittelwert ist etwas anderes als ein historisches Extrem |
| **#2 SMA-Zustand** | **H2:** Die Lage zum langfristigen Durchschnitt verbessert das Verhältnis von Wachstum zu Verlustphasen | Long bei Close über SMA200, Cash darunter. Tägliche Prüfung | Wie #1 | Wette auf einen **anhaltenden Zustand**, ohne ein neues Hoch zu verlangen. Nutzt **SMA**. EMA wäre dieselbe Wette mit anderer Glättung, keine fünfte Alternative |
| **#3 Volatilitätsgesteuertes Zeitreihen-Momentum** | **H3a:** Positive Zwölfmonatsrenditen setzen sich fort. **H3b:** Weniger Kapital bei hoher Volatilität verbessert das Netto­ergebnis gegenüber demselben **unskalierten** Signal | Monatsende: positive Zwölfmonats-Gesamtrendite → long, sonst Cash | Kapitalanteil × `min(1, 10 % / annualisierte 60-Tage-Volatilität)`. Die 10 % sind ein Ziel **je Teilposition**, keine zugesicherte Portfoliovolatilität | Eigenständige Wette auf **Risikosteuerung**, zusätzlich zur Richtung. H3b muss gegen das unskalierte Gegenstück antreten, sonst ist nicht unterscheidbar, was gewirkt hat |
| **#4 Querschnittliches Gewinnerportfolio** | **H4:** Relative Gewinner schlagen den Korb, auch ohne positive absolute Trends | Monatlich nach **korrektem** 12M−1M sortieren, oberstes Quintil halten, Ausstieg beim Verlassen | Gleichgewicht, max. 5 % je Instrument und 25 % je Anlageklasse | Wette auf **relative Führung und Rotation**. Kann fallende Instrumente halten, wenn andere stärker fallen. Braucht Defekt 6 behoben und ein **historisch verfügbares** Universum |

**Warum #1 vor #2:** Der Kanalausbruch ist die reinere Frage — trägt das Signal
überhaupt? Erst danach lohnt der Vergleich mit dem langsameren Zustandssignal.
Codex weist darauf hin, dass #1 und #2 wahrscheinlich **keine starke
Diversifikation** bilden; das bleibt zu messen, ist aber kein Grund, eine der
beiden vorwegzunehmen.

**Warum in #1 zunächst kein Stop:** Ein ATR-Stop verändert die
Auszahlungsstruktur des Kanalsystems. Wer beides gleichzeitig einführt, kann
hinterher nicht sagen, was gewirkt hat. Der Stop gehört in ein eigenes Experiment.

Forschungsanker, ausdrücklich keine Validierung dieser Regeln: Moskowitz, Ooi und
Pedersen (2012) zum Zeitreihen-Momentum an Futures, Jegadeesh und Titman (1993)
zum Querschnitts-Momentum bei Aktien. Beides lässt sich nicht ungeprüft auf einen
heutigen gemischten ETF-Korb übertragen.

---

## 2. Indikatoren: was fehlt, was bleibt, was raus muss

### Die direkte Antwort auf LBR und RSI

Beide sind für das **Kernsignal** einer Trendfolge die falschen Werkzeuge, und ich
halte es für redlicher, das zu sagen als eine Rolle zu erfinden.

**LBR (3/10/16)** ist Raschkes Swing-Oszillator, also bewusst schnell. Für ein
Positionssystem, das Wochen bis Monate hält, erzeugt er zu viele Wechsel — und
jeder Wechsel kostet. Die eine verteidigbare Rolle wäre ein **Ausstiegs­beschleuniger**
innerhalb eines langsamen Systems, und das ist ein eigenes Experiment mit eigener
Hypothese. Dazu kommt: bevor LBR überhaupt spezifizierbar ist, müssen die Defekte
3 und 4 weg — solange „LBR bullish" zwei Bedeutungen hat und die bestehende
Strategie zum Signal-Close handelt, ist jede Zahl dazu wertlos.

**RSI** sättigt in starken Trends. „Überkauft → aussteigen" ist für Trendfolge
genau verkehrt; es schneidet die Gewinner ab, von denen das System lebt. Die
sinnvolle Variante wäre **RSI(14) über 50 als Zustandsfilter** statt als
Extremwert. Nur ist das dann eine langsamere Kopie von „Close über
Durchschnitt" — mehr Parameter, keine neue Wette. Für die erste Runde raus.

### Was tatsächlich fehlt

| Ergänzung | Was sie leistet, das nichts bei uns leistet | Aufwand |
|---|---|---|
| **Vergangenheitsbezogene High-/Low-Kanäle** | Definieren eine beobachtbare Extremgrenze für #1. Kein vorhandener Indikator tut das | Gering. **Sofort nötig** |
| **Rollierende Renditevolatilität** | Prozentuale Risikoskala für #3. Bollinger misst die Streuung von Preis*niveaus*, nicht von Renditen | Gering. Im Regimecode steckt die Rechnung schon (`indicators.js:169`), nur nicht als eigene Ausgabe |
| **Korrektes Skip-Month-Momentum + Rangbildung** | Vergleichbare Rangwerte für #4 | Formel gering, historisch verfügbares Universum **hoch** |
| **ATR** | Tagesspanne inklusive Abstand zum Vortagesschluss — für Stopabstände und Risikoeinheiten | Indikator gering, belastbare Stopausführung mittel. **Kein Muss für den ersten Test** |
| Keltner, ADX, weitere Oszillatoren | Für die vier Hypothesen kein zusätzlicher Informationsbaustein | Vorerst weglassen |

**ATR ist nicht die erste Ergänzung**, anders als ich zunächst annahm. #1 braucht
einen Kanal, #3 braucht Renditevolatilität — keine der beiden Grössen lässt sich
durch ATR ersetzen. Und eine ATR-Stückzahl definiert ein *geplantes* Stoprisiko,
keine Verlustobergrenze: Kurslücken und korrelierte Positionen bleiben.

### Aus dem Bestand aktiv: SMA und korrigiertes Momentum

Alles andere ist für **diese Studie** entbehrlich — was nicht „generell wertlos"
heisst. EMA, MACD und LBR sind weitgehend alternative Darstellungen von Trend
oder Trendänderung und bringen ohne eigene Hypothese nur Freiheitsgrade. Bollinger
bräuchte eine ausdrückliche Volatilitätsausbruchs-Hypothese. Regime ist in der
jetzigen Form unzulässig. **StRev** ist eine Mean-Reversion-Wette und gehört zur
Gegenfamilie — wobei die implementierte Grösse schlicht die 21-Tage-Rendite ist;
erst die Handelsrichtung macht sie konträr.

---

## 3. Der saisonale Ansatz — der skeptische Teil

Die Infrastruktur ist ein **Forschungs- und Umsetzungsvorteil**. Eine
Renditeprämie folgt daraus nicht.

Ein Kalendermerkmal ist nicht automatisch dasselbe Signal wie vergangene Preise —
insofern ist es keine Doppelverwertung. Sie entsteht aber sofort, wenn Trendregel,
Saisonfenster **und** ihre Kombination an derselben Renditehistorie ausgewählt
werden. Genau das ist der Weg, auf dem unsere Intermarket-Matrix 470 Fragen
gestellt und null bestätigte Befunde geliefert hat.

**Hypothese S:** Ein vorab festgelegter saisonaler Zustand verbessert den
zusätzlichen Netto-Nutzen eines **bereits festgelegten** Trendsystems. Das ist
eine deutlich schärfere Behauptung als „Trend plus Saison ist profitabel".

Vorgehen: zunächst **kein** Gate. Später genau **eine** wirtschaftlich begründete
Kombination, gegen vier Vergleichsarme — dauerhaft investiert, Trend allein,
Saison allein, Trend × Saison. Entscheidend ist der Zusatznutzen gegenüber den
Bestandteilen **und** gegenüber einer schlichten Verringerung der
Marktexponierung; sonst verkauft man weniger Marktzeit als Timing-Erfolg.

Und das Gate muss eindeutig sein: nur Einstiege sperren oder laufende Positionen
zwangsweise schliessen? Ich würde **nur Einstiege sperren und laufende Trends
weiterführen** — sonst beendet ein Kalenderwechsel einen intakten Trend. Diese
Entscheidung steht vor dem Ergebnis fest.

Eine eigene, davon getrennte Frage wäre **Hypothese V:** Verbessert
Kalenderinformation die *Volatilitätsprognose* zusätzlich zur jüngsten gemessenen
Volatilität? Das wäre eine Risiko-, keine Richtungshypothese — erst Prognosegüte
ausserhalb der Schätzperiode, dann Nutzen für Positionsgrössen.

---

## 4. Testdesign — der schwierigste Teil

**Weder Walk-forward noch eine andere Kennzahl erzeugt zusätzliche unabhängige
Marktphasen.** Dreissig Jahre enthalten eine Handvoll Zinszyklen, nicht dreissig.

**Zuerst der Datenvertrag.** Die 370 Symbole sind ein *heutiger* Katalog ohne
dokumentierte historische Zugehörigkeit; ausgeschiedene Titel fehlen. Darin steht
mit `^TNX` auch eine Zinsreihe, deren prozentuale Änderung keine handelbare
Anleiherendite ist. Ohne historische Mitgliedschaft bleibt **#4 auf dem breiten
Aktienuniversum explorativ**. Dazu muss die Quelle eingefroren werden — unsere
eigene Doku beschreibt unterschiedliche Adjustierungsstände zwischen Supabase und
Yahoo, und für eine OHLC-Studie ist das ein Prüfauftrag, kein Nebensatz.

**Das Protokoll:**

1. **Vorregistrierung.** Universum, Historie, die vier Primärkonfigurationen,
   Kosten, Ausführung, Zielgrösse und Abbruchregeln einfrieren. Keine „besten
   Parameter je Ticker".
2. **Chronologische Entwicklung.** Bei 30 brauchbaren Jahren etwa: erste 10 Jahre
   Entwicklung, dann fünf aufeinanderfolgende Dreijahresfenster, letzte 5 Jahre
   **gesperrter** Abschlusstest.
3. **Den Abschlusstest einmal öffnen.** Danach ist er Entwicklungsdatenbestand.
   Wenn alle Jahre schon zur Ideenwahl betrachtet wurden, gibt es keinen ehrlichen
   Lockbox-Test mehr — dann bleibt zeitliches Pseudo-OOS plus prospektive
   Beobachtung, und das gehört so benannt.
4. **Eine durchgehende Kontokurve.** Positionen über Fenstergrenzen weiterführen,
   Kosten und Cash-Zins erfassen, offene Positionen täglich bewerten.
5. **Inferenz über gemeinsame Zeitblöcke.** Strategie und Benchmark synchron
   blockweise resampeln, über alle Märkte gemeinsam, damit zeitliche und
   marktübergreifende Abhängigkeit teilweise erhalten bleibt. Vorregistrierte
   Sensitivität über 12, 24 und 36 Monate — **keinen günstigen Blockumfang
   auswählen**.

Die vorhandene `walk_forward`-Funktion würde ich **nicht** übernehmen (Defekt 7).

**Wie viele Parameterkombinationen?** Eine seriöse magische Obergrenze gibt es
nicht. Budget: **vier Primärregeln plus je zwei vorab definierte
Nachbarkonfigurationen**, also zwölf. Die Nachbarn prüfen Stabilität; sie ersetzen
keinen gescheiterten Primärkandidaten. **Tickerwahl, Zeitraumwahl, Stops und
Saisonfilter zählen ebenfalls als Versuche**, sobald anhand ihrer Ergebnisse
ausgewählt wird. Die vier Primärhypothesen bilden eine Testfamilie mit
Holm-Korrektur bei 5 %.

**Benchmarks.** Kaufen-und-Halten desselben Instruments mit Dividenden ist
notwendig und nicht ausreichend:

| System | Zusätzlich nötiger Vergleich |
|---|---|
| #1, #2 | Derselbe passive Korb **und** eine vorab aus Trainingsdaten festgelegte Aktien-/Cash-Mischung mit ähnlichem Risiko |
| #3 | Dasselbe Momentum **ohne** Skalierung und volatilitätsgesteuertes Kaufen-und-Halten |
| #4 | Regelmässig gleichgewichteter Korb, plus Kontrolle der Anlageklassen­allokation |

Kostenannahme für den ersten ETF-Test: **5 Basispunkte je gehandelter Seite, im
Stresstest 15**. Ausdrücklich Modellannahmen, keine behaupteten realen Kosten und
keine Pauschale für alle 370 Instrumente.

**Welche Kennzahl?** Sharpe ist nicht grundsätzlich falsch — die *vorhandene*
Berechnung ist es: sie mittelt über Trade-Renditen ungleicher Länge
(`backtest_engine.py:158`), und der Drawdown entsteht aus der verketteten
Trade-Kurve statt aus einer täglichen Kontokurve (`:192`).

Als Primärgrösse ein **Netto-Sicherheitsäquivalent gegenüber dem
Kontrollportfolio**, aus monatlichen Kontorenditen:

```
CE = μ(Überschuss) − (3/2) · σ²
```

Die Risikoneigung 3 ist eine gesetzte Präferenz, kein Forschungsergebnis. Dazu
CAGR, maximaler **täglicher** Drawdown, Erholungsdauer, schlechtestes Jahr,
Umsatz, Exponierung und Unsicherheitsintervalle. Eine Deflated Sharpe Ratio
(Bailey und López de Prado, 2014) kann Selektionsverzerrung diagnostizieren — sie
repariert keine Datenlecks und keine fehlenden Marktphasen.

---

## 5. Abbruchkriterien — festgelegt vor der ersten Rechnung

Gemeinsame wirtschaftliche Mindestgrösse: **0,5 Prozentpunkte jährlicher
Netto-CE-Zusatznutzen**. Eine Planungsentscheidung, keine gemessene Grösse.

Zwei Ergebnisse sind zu trennen. Liegt schon die **obere** Unsicherheitsgrenze
unter der Schwelle, spricht das gegen einen wirtschaftlich relevanten Effekt.
Liegt das Intervall breit über *und* unter der Schwelle, ist die Hypothese
**ungeklärt** — in beiden Fällen keine Umsetzung, und die Konfiguration wird
nicht nachträglich gerettet.

| Alternative | Verwerfungsregel |
|---|---|
| **#1 Kanalausbruch** | Fallen lassen, wenn der OOS-Netto-CE-Vorteil unter 0,5 pp liegt, die korrigierte Überlegenheit gegenüber null fehlt, oder der Vorteil bei 15 bp Stresskosten negativ wird. Positive Bruttotrades allein genügen nicht |
| **#2 SMA-Zustand** | Gleiche CE-Hürde, **zusätzlich** mindestens 20 % geringerer maximaler Drawdown gegenüber vollem Kaufen-und-Halten bei höchstens 2 pp CAGR-Verzicht. Wird dieser Schutzauftrag verfehlt, entfällt die Alternative |
| **#3 Volatilitätssteuerung** | Fallen lassen, wenn die Skalierung gegenüber demselben **unskalierten** Signal die CE-Hürde nicht erreicht oder gegenüber volatilitätsgesteuertem Kaufen-und-Halten keinen Zusatznutzen zeigt. Ein gutes Gesamtergebnis ohne nachweisbaren Beitrag der Skalierung bestätigt H3b **nicht** |
| **#4 Ranking** | Fallen lassen, wenn die CE-Hürde gegenüber dem passiven Korb fehlt oder der Vorteil nach Kontrolle der Anlageklassen verschwindet. Ohne historisch verfügbares Universum ist H4 mit diesen Daten nicht bestätigbar |
| **Saisonales Gate (später)** | Kein korrigiert belastbarer Zusatznutzen gegenüber Trend allein **und** gegenüber einer vergleichbaren Exponierungsreduktion → Gate streichen, unabhängig davon, ob die Kombination insgesamt verdient |

Die Schwellen gelten für den vorregistrierten primären OOS-Zeitraum; der
gesperrte Abschlusstest muss mindestens dieselbe Effektrichtung zeigen. Ein
einzelner günstiger Fold genügt nicht.

Dazu je Ansatz eine Auswertung **ohne einen Marktblock** und **ohne die grösste
Gewinnphase**. Wichtig zur Lesart: Das Entfernen des grössten Gewinners ist für
Trendfolge **kein automatisches Todesurteil** — wenige grosse Gewinne gehören zur
Hypothese. Hängt aber die ganze Evidenz an einer Episode, lautet das Ergebnis
„nicht hinreichend repliziert".

---

## 6. Baufolge

**Die kleinste sinnvolle Änderung ist ein separates Python-Forschungsskript mit
einem kleinen täglichen Positions- und Kontomodell.** Kein Umbau der
Ereignisengine, keine neue Strategieplattform, zunächst keine Seite.

1. **Datenvertrag und eingefrorenen ETF-Korb festlegen** — konsistente
   OHLC-Adjustierung, vollständige abgeschlossene Tagesbalken, dokumentierte
   Ausfälle, Gesamtrendite- und Cash-Behandlung.
2. **Nur #1 ermöglichen** — 100/50-Kanäle aus der Vergangenheit, Zustand
   Cash/Long, Ausführung am nächsten Open, Kosten auf Kauf und Verkauf, tägliche
   Bewertung inklusive offener Positionen.
3. **Passiven Kontrolllauf und identischen Bericht** — aus einer täglichen
   Kontokurve, nicht aus wiederverwendeter Trade-Statistik.
4. **Gezielt verifizieren** — später angehängte Daten dürfen frühere Signale nicht
   verändern, kein Handel vor vollständiger Historie, korrekte Ausführung am
   Folgetag, Kosten und offene Positionen richtig verbucht.
5. Erst danach #2, dann Skalierung und Ranking.

Die vorhandenen Stoproutinen **nicht** übernehmen: `backtest_engine.py:102`
aktualisiert den Trailing-Stop am heutigen High und prüft danach das heutige
Low, obwohl die Reihenfolge innerhalb des Tages unbekannt ist; ausserdem wird
immer zum Stopniveau ausgeführt, auch wenn der Kurs darunter eröffnet hätte.

Ein Übersetzer, der Trendwechsel nachträglich in Kalenderereignisse umformt,
spart die entscheidende Arbeit nicht: variable Haltedauer, Kapitalbindung,
Ausführung und tägliche Bewertung müssen ohnehin modelliert werden. **Der minimale
neue Baustein ist ein Positionskonto, keine grössere Indikatorbibliothek.**

---

## Offene Entscheidungen für den Nutzer

1. **Der ETF-Korb für #1 und #2.** Wenige, wenig überlappende, liquide Instrumente
   mit langer Historie. Vorschlag zur Diskussion: ein breiter Aktienindex, ein
   Nicht-US-Aktienindex, langlaufende Anleihen, Gold, ein breiter Rohstoffkorb.
2. **Ob die 30 Jahre wirklich unangetastet sind.** Wir haben über Jahre
   Saisonstudien auf denselben Reihen gerechnet. Wenn die Antwort „nein" ist,
   existiert kein ehrlicher Lockbox-Test, und das muss im Bericht stehen statt
   behauptet zu werden.
3. **Reihenfolge gegen die sieben Defekte.** Nummer 4 (Look-ahead in einer live
   angezeigten Strategie) und Nummer 5 (SMA-Filter in der Aufwärmphase) würde ich
   unabhängig von diesem Plan vorziehen.

---
title: "Der Turn-of-Month-Effekt hat ein Timing-Problem — und ein Down-Monat löst es"
seo_title: "Turn-of-Month timen: SPY nach Down-Monaten im Backtest"
slug: spy-turn-of-month-down-monat-reversal-backtest
date: 2026-07-31
author: SeasonAlpha Research
category: education
tags: [spy, turn-of-month, tdom, mean-reversion, backtest, short-term-reversal, seasonal-strategy, jegadeesh, carhart]
description: "SPY Turn-of-Month im 15-Jahres-Backtest: Nach einem Minus-Monat steigt die Ø-Rendite pro Trade von 0,75 % auf 1,25 % — bei geringerem Drawdown."
ticker: SPY
status: published
---

<!--
Keyword-Plan:
- Haupt-Keyword: Turn-of-Month Effekt SPY
- Neben-Keywords: Monatswechsel Strategie Backtest, Short-Term Reversal, Mean Reversion Aktienmarkt, TDOM Handelstag im Monat, SPY Saisonalität Backtest, Profit Factor Strategie, Down-Monat Filter, Momentum Filter DAX
- LSI-Keywords: Win-Rate, Sharpe Ratio, Maximum Drawdown, Handelstage, Kapitalzuflüsse, Rebalancing, Liquiditätszyklus, normalisierte Renditen, Look-ahead-Bias, Signifikanz
-->

## Nicht ob, sondern wann

Der Turn-of-Month-Effekt gehört zu den am besten dokumentierten Kalenderanomalien überhaupt: Rund um den Monatswechsel verdient der Aktienmarkt einen überproportionalen Teil seiner Jahresrendite. Die spannendere Frage lautet aber nicht, **ob** der Effekt existiert — sondern **wann** er besonders kräftig ausfällt.

Unser 15-Jahres-Backtest auf dem **SPY** liefert dazu eine klare Antwort. Handelt man jeden Monatswechsel gleich, ergeben sich über 186 Trades im Schnitt **+0,75 % pro Trade**. Filtert man aber auf Monate, in denen der Markt vorher **gefallen** war, steigt derselbe Durchschnitt auf **+1,25 % pro Trade** — ein Plus von 67 Prozent.

Und das Bemerkenswerteste: Der maximale Drawdown sinkt dabei von 22,3 % auf 18,3 %. Mehr Ertrag bei weniger Schmerz ist im Backtesting die Ausnahme, nicht die Regel.

## Der Turn-of-Month-Effekt in 60 Sekunden

Der Effekt beschreibt eine simple Beobachtung: Die letzten Handelstage eines Monats und die ersten des Folgemonats liefern historisch überdurchschnittliche Renditen — deutlich mehr, als ihr Anteil an den Handelstagen erwarten ließe.

Erstmals systematisch belegt hat das **Robert Ariel (1987)**. Er zeigte in „A Monthly Effect in Stock Returns", dass praktisch die gesamte positive Marktrendite in der ersten Monatshälfte anfiel. **Joseph Ogden (1990)** lieferte die ökonomische Erklärung nach: den **Liquiditätszyklus**. Gehälter, Renten, Zinskupons und Dividenden werden gebündelt zum Monatswechsel ausgezahlt. Ein Teil dieses Geldes fließt planmäßig in den Aktienmarkt — über Sparpläne, Pensionsfonds-Zuflüsse und institutionelles Rebalancing.

Das ist kein psychologisches Muster, sondern ein **struktureller Kapitalfluss**. Genau deshalb ist der Effekt so langlebig: Er hängt an der Zahlungsinfrastruktur der Wirtschaft, nicht an der Stimmung der Anleger. Die Grundlagen haben wir im Artikel [Turn-of-Month-Effekt erklärt](/blog/turn-of-month-effekt-erklaert/) ausführlich aufgeschlüsselt.

## Die Idee: zwei Anomalien übereinanderlegen

Wenn der Zufluss zum Monatsanfang mehr oder weniger konstant ist, dann sollte seine **Wirkung auf den Kurs** davon abhängen, in welchem Zustand der Markt ihn empfängt. Hier kommt eine zweite, unabhängig dokumentierte Anomalie ins Spiel.

**Narasimhan Jegadeesh (1990)** wies in „Evidence of Predictable Behavior of Security Returns" nach, dass kurzfristige Renditen **negativ autokorreliert** sind: Was über den letzten Monat gefallen ist, tendiert im Folgemonat überdurchschnittlich nach oben. Dieser **Short-Term Reversal** ist das Gegenstück zum bekannteren 12-Monats-Momentum und wirkt auf genau der Zeitskala, die uns hier interessiert.

Die Hypothese ist damit formuliert: Der Turn-of-Month-Zufluss trifft nach einem schwachen Monat auf einen bereits gedrückten Markt — und wirkt dort stärker. Ökonomisch plausibel ist das gleich doppelt.

**Erstens der Verkaufsdruck vor dem Monatsende.** Läuft ein Monat schlecht, steigt der Abgabedruck zum Monatsultimo zusätzlich: Fonds glätten Reportings, Risikomodelle reduzieren Positionen bei erhöhter Volatilität, Anleger realisieren Verluste. Der Markt ist am Monatsende überverkauft.

**Zweitens der unveränderte Zufluss danach.** Der Sparplan am Monatsersten wird ausgeführt, egal wie der Vormonat lief. Auf ein gedrücktes Kursniveau trifft also die gleiche Nachfrage wie sonst — und bewegt es mechanisch stärker.

## Das Setup: was genau getestet wurde

Damit die Zahlen einzuordnen sind, hier die exakte Konfiguration.

| Parameter | Einstellung |
|---|---|
| Basiswert | SPY (S&P 500 ETF) |
| Zeitraum | 15 Jahre |
| Ereignis | TDOM 17–22 (Monatsende-Fenster) |
| Einstieg | 3 Handelstage vor dem Ereignis |
| Ausstieg | 10 Handelstage nach dem Einstiegssignal |
| Preisbasis | Close-to-Close |
| Stop-Loss | keiner |
| Filter (Variante 2) | 21-Tage-Return < 0 |

**TDOM** steht für *Trading Day of Month* — den fortlaufend gezählten Handelstag innerhalb eines Monats, nicht das Kalenderdatum. Der 17. bis 22. Handelstag markiert je nach Monatslänge das Monatsende-Fenster. Diese Zählung ist wichtig: Feiertage und Wochenenden verschieben das Kalenderdatum, den Handelstag aber nicht.

Die Haltedauer umfasst damit rund 13 Handelstage, die den Monatswechsel umschließen. Der Filter prüft eine einzige Bedingung: Lag die Rendite der vergangenen 21 Handelstage — grob ein Börsenmonat — unter null?

## Die Zahlen: Baseline gegen Down-Monat-Filter

| Kennzahl | SPY ToM (ungefiltert) | SPY ToM nach Down-Monat |
|---|---|---|
| Anzahl Trades (n) | 186 | 78 |
| Win-Rate | 68,3 % | **71,8 %** |
| Ø-Rendite pro Trade | +0,75 % | **+1,25 %** |
| Profit Factor | 1,80 | **2,39** |
| Sharpe Ratio | +0,21 | **+0,34** |
| Max. Drawdown | 22,3 % | **18,3 %** |

Vier Beobachtungen stecken in dieser Tabelle.

**Die Baseline ist bereits solide.** 68,3 % Win-Rate über 186 Trades und ein Profit Factor von 1,80 — der Profit Factor setzt die Summe aller Gewinne ins Verhältnis zur Summe aller Verluste. 1,80 heißt: Auf jeden Euro Verlust kommen 1,80 Euro Gewinn. Der Turn-of-Month-Effekt funktioniert also auch ohne jeden Filter.

**Der Filter hebt jede einzelne Kennzahl.** Win-Rate, Durchschnittsrendite, Profit Factor und Sharpe Ratio verbessern sich gleichzeitig. Das ist ein wichtiges Robustheitssignal: Ein Filter, der nur eine Metrik hebt und andere drückt, ist meist ein Artefakt der Datenauswahl.

**Der Ertragssprung ist der eigentliche Befund.** Von +0,75 % auf +1,25 % pro Trade sind 67 Prozent mehr Rendite je Position — bei nur leicht höherer Trefferquote. Der Zugewinn kommt also weniger aus mehr Gewinnern als aus **größeren** Gewinnern. Genau das erwartet man bei Mean Reversion: Der Rückprall aus einem gedrückten Niveau fällt heftiger aus.

**Weniger Drawdown trotz stärkerem Edge.** 18,3 % statt 22,3 % maximaler Rückgang vom Höchststand. Der Filter hält die Strategie in Phasen aus dem Markt, in denen der Monatswechsel historisch schwächer trug.

Rechnerisch lässt sich der Gegenteil-Fall aus den Werten ableiten: Die 108 Trades **nach einem positiven Vormonat** kommen zusammen nur auf rund **+0,4 % pro Trade**. Der gesamte Renditevorsprung des Turn-of-Month-Effekts konzentriert sich damit auf jene 42 Prozent der Monatswechsel, denen ein Minus vorausging.

## Wo dieses Fenster im Jahresverlauf liegt

Der Monatswechsel ist nur eine von mehreren Zeitstrukturen im SPY. Der normalisierte Jahresverlauf zeigt, in welchem übergeordneten Muster diese Trades stattfinden:

{{chart:seasonal_yearly:SPY:15}}

Der Chart nutzt **normalisierte Renditen**: Jedes Jahr startet bei 100, die täglichen Renditen kumulieren darauf. Absolute Kursdifferenzen werden nie über Jahre addiert — sonst würden spätere Jahre mit deutlich höherem Indexstand das Bild dominieren. Das schattierte Band (±1 Standardabweichung) zeigt, wie zuverlässig der mittlere Verlauf tatsächlich ist.

Wichtig zur Einordnung: Der Down-Monat-Filter ist **kein saisonaler Filter**. Er greift nicht in bestimmten Kalendermonaten, sondern immer dann, wenn der Markt zuletzt gefallen ist — unabhängig davon, ob das im März oder im Oktober passiert.

## Der Gegentest: warum derselbe Trick beim DAX scheitert

Ein einzelnes positives Ergebnis ist wenig wert, wenn man nicht zeigt, was **nicht** funktioniert hat. Parallel haben wir einen zweiten Filter getestet: **12-Monats-Momentum abzüglich des letzten Monats** — die Standarddefinition aus dem Vier-Faktor-Modell von **Mark Carhart (1997)**. Die Idee: Nur handeln, wenn der übergeordnete Trend intakt ist.

Angewendet auf den DAX-Monatswechsel fiel die Sharpe Ratio von **0,07 auf 0,04**. Der Filter hat nicht geholfen — er hat leicht geschadet.

Der Grund liegt aber weniger im Filter als in der Basis: Eine Sharpe Ratio von 0,07 ist praktisch nicht von null zu unterscheiden. Der DAX-Turn-of-Month-Effekt war in diesem Test schlicht **zu schwach, um ihn zu verstärken**. Ein Filter kann einen vorhandenen Edge schärfen, aber keinen erzeugen, der nicht da ist.

Das deckt sich mit unserer Beobachtung aus der [ML-Regime-Analyse](/blog/ml-regime-clustering-baerenmarkt-mean-reversion/): Zusätzliche Regeln machen eine Strategie nicht automatisch besser — mehrere plausible Filter haben dort messbaren Schaden angerichtet.

## Methodik-Notiz

Drei Punkte, die für die Belastbarkeit der Zahlen entscheidend sind.

**Normalisierte Renditen.** Alle Auswertungen und Charts arbeiten mit prozentualen, auf 100 normierten Renditen. Absolute Preisänderungen über lange Zeiträume zu addieren, verzerrt jede Mehrjahresstatistik zugunsten der jüngeren Jahre.

**Handelstage statt Kalendertage.** TDOM wird börsenspezifisch aus dem Handelskalender gezählt, inklusive Feiertagen der jeweiligen Börse. Der 21-Tage-Rückblick des Filters sind ebenfalls 21 **Handels**tage.

**Look-ahead-bias-frei.** Der Filter wird auf dem Stand des **Vortags** der Einstiegskerze geprüft, nicht am Einstiegstag selbst. Ein Backtest, der die Bedingung auf der Einstiegskerze auswertet, nutzt Information, die zum Handelszeitpunkt noch nicht vollständig vorlag — einer der häufigsten Gründe für Backtests, die auf dem Papier glänzen und live enttäuschen.

## Grenzen: was diese Zahlen nicht sagen

**78 Trades sind keine große Stichprobe.** Der gefilterte Datensatz umfasst 78 Beobachtungen über 15 Jahre. Das reicht für einen Hinweis, nicht für einen Beweis. Bei kleinen Stichproben können wenige Ausreißer den Durchschnitt spürbar verschieben.

**Kosten und Steuern fehlen.** Die Strategie handelt bis zu zwölfmal jährlich. Spreads, Ordergebühren und Abgeltungsteuer sind in keiner Zahl enthalten und schmälern den Vorsprung real.

**Der Zeitraum ist US-freundlich.** 15 Jahre SPY enthalten eine historisch außergewöhnliche Aufwärtsphase. Jede Long-only-Strategie profitiert davon.

**Sharpe ohne risikofreien Zins.** Die Werte sind als reines Rendite-zu-Volatilitäts-Verhältnis gerechnet und untereinander vergleichbar, nicht mit Fremdquellen.

**Kein Stop-Loss.** Der Test läuft ohne Absicherung nach unten. Der Drawdown von 18,3 % ist real durchzuhalten.

## Selbst nachrechnen

Der interessanteste Teil an einem Backtest ist der, den man selbst variiert. In SeasonAlpha lässt sich die Konfiguration direkt nachbauen:

- **[Backtest-Engine](/backtest-engine)** — Preset **„SPY Down-Month Reversal"** laden oder manuell setzen: Ereignis TDOM, Bereich 17–22, Einstieg −3, Ausstieg +10, Filter 21-Tage-Return < 0
- **[Monatswechsel](/monatswechsel)** — die Turn-of-Month-Kurve mit Signifikanz-Tacho (t-Wert, p-Wert, Win-Rate, n) für jeden Ticker
- **[TDOM-Analyse](/tdom-analyse)** — Ø-Rendite je Handelstag im Monat, börsenspezifisch berechnet
- **[Jahreszyklus](/jahreszyklus)** — der normalisierte Jahresverlauf für SPY oder jeden anderen Wert

Interessante Variationen: Exit von +10 auf +5 Handelstage kürzen, den Filter auf 10 oder 42 Tage Rückblick ändern, oder das Ganze auf QQQ, IWM und einzelnen Sektor-ETFs prüfen. Bricht der Effekt bei kleinen Parameteränderungen zusammen, war er wahrscheinlich Rauschen.

## Fazit

Der Turn-of-Month-Effekt beim SPY ist über 15 Jahre und 186 Trades intakt: 68,3 % Win-Rate, Profit Factor 1,80, **+0,75 % pro Trade**. Wer ihn aber ausschließlich nach einem **negativen Vormonat** handelt, kommt auf 71,8 % Win-Rate, Profit Factor 2,39 und **+1,25 % pro Trade** — bei einem um vier Prozentpunkte geringeren Maximaldrawdown.

Die Erklärung braucht keine neue Theorie: Ariels Monatswechsel-Zufluss trifft auf Jegadeeshs kurzfristige Gegenbewegung. Zwei seit Jahrzehnten dokumentierte Effekte, die auf derselben Zeitskala arbeiten und sich addieren.

Der DAX-Gegentest liefert die nötige Bodenhaftung: Wo der Basis-Edge fehlt, hilft auch der beste Filter nicht. Prüfe deinen eigenen Ticker in der **[Backtest-Engine](https://seasonalpha.ai/backtest-engine)** — der Unterschied zwischen einem echten Muster und einer schönen Kurve zeigt sich erst, wenn man an den Parametern dreht.

## Häufige Fragen

### Was ist der Turn-of-Month-Effekt genau?
Der Turn-of-Month-Effekt bezeichnet die Beobachtung, dass die letzten Handelstage eines Monats und die ersten des Folgemonats historisch überdurchschnittliche Renditen liefern. Robert Ariel dokumentierte ihn 1987 erstmals systematisch, Joseph Ogden lieferte 1990 die Erklärung über den Liquiditätszyklus: Gehälter, Renten und Fondszuflüsse werden gebündelt zum Monatswechsel wirksam. In unserem SPY-Test über 15 Jahre lag die Win-Rate der ungefilterten Variante bei 68,3 %.

### Warum funktioniert der Effekt nach einem Verlustmonat besser?
Zwei Mechanismen greifen ineinander. Vor einem schwachen Monatsende steigt der Verkaufsdruck durch Reporting-Kosmetik, Risikomodelle und Verlustrealisierung — der Markt ist gedrückt. Der planmäßige Zufluss zum Monatsanfang bleibt davon unberührt und trifft auf ein niedrigeres Kursniveau. Statistisch entspricht das dem von Jegadeesh (1990) beschriebenen Short-Term Reversal. In unserem Test stieg die Ø-Rendite pro Trade dadurch von 0,75 % auf 1,25 %.

### Was bedeutet TDOM 17–22?
TDOM steht für *Trading Day of Month*, also den fortlaufend gezählten Handelstag innerhalb eines Monats. Der 17. bis 22. Handelstag markiert je nach Monatslänge das Monatsende-Fenster. Die Zählung erfolgt börsenspezifisch aus dem Handelskalender, da Feiertage das Kalenderdatum verschieben, den Handelstag aber nicht.

### Warum hat der Momentum-Filter beim DAX nicht funktioniert?
Wir haben den klassischen Carhart-Momentum-Filter (12 Monate abzüglich des letzten Monats) auf den DAX-Monatswechsel angewendet — die Sharpe Ratio fiel von 0,07 auf 0,04. Der Grund liegt in der Basis: Eine Sharpe Ratio von 0,07 ist statistisch kaum von null zu unterscheiden. Ein Filter kann einen vorhandenen Vorteil schärfen, aber keinen erzeugen, den es nicht gibt.

### Ist eine Stichprobe von 78 Trades aussagekräftig?
Nur eingeschränkt. 78 Beobachtungen über 15 Jahre liefern einen belastbaren Hinweis, aber keinen Beweis — einzelne Ausreißer können den Durchschnitt spürbar bewegen. Deshalb ist der Konsistenz-Check wichtiger als der Einzelwert: Dass Win-Rate, Durchschnittsrendite, Profit Factor und Drawdown sich gleichzeitig verbessern, spricht eher für einen echten Zusammenhang als für Zufall.

<!--
#### Social Media Snippet

**LinkedIn:** Der Turn-of-Month-Effekt ist gut dokumentiert. Die interessantere Frage ist nicht ob, sondern wann er wirkt. Unser 15-Jahres-Backtest auf dem SPY (TDOM 17-22, Einstieg -3 HT, Ausstieg +10 HT, Close-to-Close): Ungefiltert 186 Trades, Win-Rate 68,3 %, Profit Factor 1,80, +0,75 % pro Trade. Nur nach einem negativen Vormonat (21-Tage-Return < 0): 78 Trades, Win-Rate 71,8 %, Profit Factor 2,39, +1,25 % pro Trade — und der Maximaldrawdown sinkt von 22,3 % auf 18,3 %. Mehr Rendite bei weniger Drawdown ist im Backtesting selten. Die Erklärung ist keine neue Theorie, sondern die Überlagerung zweier bekannter Effekte: Ariels Monatswechsel-Liquidität (1987) trifft auf Jegadeeshs Short-Term Reversal (1990). Gegenprobe: Ein Carhart-Momentum-Filter auf dem DAX-Monatswechsel drückte die Sharpe Ratio von 0,07 auf 0,04 — wo kein Basis-Edge ist, hilft auch kein Filter. Welche Filter testet ihr auf euren Kalenderstrategien? #Saisonalität #Backtest #Trading #SeasonAlpha

**Twitter/X:** SPY Turn-of-Month, 15 Jahre Backtest: ungefiltert +0,75 %/Trade, WR 68,3 %. Nur nach einem Minus-Monat: +1,25 %/Trade, WR 71,8 %, Profit Factor 2,39 — und der MaxDD fällt von 22,3 % auf 18,3 %. Ariel trifft Jegadeesh. seasonalpha.ai #Saisonalität #Backtest #SeasonAlpha

#### Interne Verlinkung
- /backtest-engine (Preset „SPY Down-Month Reversal" nachbauen)
- /monatswechsel (Turn-of-Month-Kurve mit Signifikanz-Tacho)
- /tdom-analyse (Ø-Rendite je Handelstag im Monat)
- /jahreszyklus (normalisierter SPY-Jahresverlauf)
- /blog/turn-of-month-effekt-erklaert/ (Grundlagen des Effekts)
- /blog/turn-of-month-effekt-lebt-noch/ (Robustheits-Check)
- /blog/ml-regime-clustering-baerenmarkt-mean-reversion/ (wenn Filter schaden)
- /blog/dax-vs-sp500-saisonalitaet/ (warum die Indizes unterschiedlich ticken)

#### Content-Ideen (Folgeartikel)
- „Short-Term Reversal messen: Wie stark kehrt der Markt nach schwachen Monaten zurück?"
- „Turn-of-Month bei QQQ, IWM und Sektor-ETFs — wo der Effekt am stärksten ist"
- „Wie lange sollte man den Monatswechsel halten? Exit-Fenster im Vergleich"
- „Warum der DAX-Monatswechsel schwächer ist als der amerikanische"
-->

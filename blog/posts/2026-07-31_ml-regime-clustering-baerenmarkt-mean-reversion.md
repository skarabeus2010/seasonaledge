---
title: "Was Machine Learning auf 30 Jahren Börsendaten findet — und warum der Bärenmarkt überrascht"
seo_title: "Machine Learning Marktregime: Der Bärenmarkt überrascht"
slug: ml-regime-clustering-baerenmarkt-mean-reversion
date: 2026-07-31
author: SeasonAlpha Research
category: education
tags: [machine-learning, marktregime, clustering, mean-reversion, turn-of-month, dax, spy, walk-forward]
description: "KMeans und Logistic Regression auf 30 Jahren Börsendaten: Das Bear-Regime liefert den höchsten Sharpe — und der DAX schlägt den SPY beim ML-Filter."
ticker: ^GDAXI
status: published
---

<!--
Keyword-Plan:
- Haupt-Keyword: Machine Learning Marktregime
- Neben-Keywords: Marktregime erkennen, KMeans Clustering Börse, Mean Reversion Bärenmarkt, Turn-of-Month DAX, Logistic Regression Trading, Walk-Forward Analyse, Regime-Filter Strategie, ML Aktienmarkt Analyse
- LSI-Keywords: Rolling Volatilität, Sharpe Ratio, Maximum Drawdown, Forward Return, Cluster, unüberwachtes Lernen, Klassifikator, Overfitting, Backtest, normalisierte Renditen, Handelstage
-->

## Wir haben zwei ML-Algorithmen auf unsere Daten losgelassen

Machine Learning und Marktregime — die Kombination klingt nach einer Blackbox, die am Ende „Kaufen" ausspuckt. Genau darum geht es hier nicht. Wir haben zwei klassische, gut verstandene Algorithmen auf die SeasonAlpha-Kursdatenbank angewendet und geschaut, welche Struktur sie in 30 Jahren Börsendaten überhaupt finden.

Das interessanteste Ergebnis ist ein Widerspruch zur Intuition: Das Regime, das der Algorithmus als **„Bärenmarkt"** klassifiziert, liefert im Anschluss die **höchsten risikoadjustierten Renditen** aller drei erkannten Zustände. Und ein Regime-Filter, der genau diese Phasen meidet, verschlechtert eine ansonsten solide saisonale Strategie deutlich.

Der zweite Befund betrifft den Turn-of-Month-Effekt: Ein ML-Klassifikator auf dem Monatswechsel funktioniert beim **DAX** klar besser als beim S&P 500. Beide Ergebnisse im Detail.

## Was Regime-Clustering überhaupt macht

Ein Marktregime ist nichts anderes als eine Phase mit ähnlichem Charakter — ruhiger Aufwärtstrend, nervöse Seitwärtsbewegung, volatiler Abverkauf. Menschen erkennen so etwas im Chart intuitiv, aber ohne feste Definition.

**KMeans-Clustering** ist ein Verfahren des unüberwachten Lernens. Es bekommt keine Labels vorgegeben, sondern nur Datenpunkte und die Anzahl der gesuchten Gruppen (k). Der Algorithmus sortiert dann jeden Datenpunkt in die Gruppe, deren Mittelpunkt am nächsten liegt — und verschiebt diese Mittelpunkte so lange, bis sich nichts mehr ändert.

Unsere Konfiguration:

- **Datenbasis:** SPY, 1993 bis 2026, **8.432 Handelstage**
- **Merkmale (Features):** Rolling-Return und Rolling-Volatilität — also „wie stark ging es zuletzt hoch oder runter" und „wie unruhig war es dabei"
- **k = 3**, also drei Regime

Wichtig zur Einordnung: Beide Merkmale sind **rückwärtsgerichtet**. Der Algorithmus weiß nur, was passiert ist — nicht, was kommt. Genau das macht das Ergebnis so aufschlussreich.

## Befund 1: Drei Regime — und das schwächste ist das stärkste

Nach dem Clustering lassen sich die drei Gruppen anhand ihrer Merkmale benennen. Anschließend haben wir für jedes Regime gemessen, welche annualisierte Sharpe Ratio der Markt in den *folgenden* Tagen lieferte. Die Sharpe Ratio setzt Rendite ins Verhältnis zum eingegangenen Schwankungsrisiko — je höher, desto besser das Verhältnis.

| Regime | Anteil der Handelstage | Ann. Sharpe (Forward) |
|---|---|---|
| Bull | 15 % | **+0,01** |
| Sideways | 68 % | +0,63 |
| **Bear** | 17 % | **+0,89** |

Das Ergebnis dreht die naive Erwartung um:

**Das Bull-Regime ist praktisch wertlos.** Eine Sharpe Ratio von +0,01 bedeutet: Nach einem starken, ruhigen Anstieg passiert im Schnitt nichts mehr. Wer erst kauft, wenn der Chart bereits eindeutig gut aussieht, kauft die Bewegung, die schon gelaufen ist.

**Der Normalzustand trägt das Depot.** Mit 68 % der Handelstage stellt „Sideways" die klare Mehrheit — und liefert mit +0,63 eine solide Sharpe Ratio. Der Markt verdient sein Geld überwiegend in unspektakulären Phasen.

**Das Bear-Regime ist die stärkste Mean-Reversion-Phase.** Mit +0,89 liefert es die höchste risikoadjustierte Folgerendite aller drei Zustände — bei 17 % der Tage.

### Warum das kein Zufall ist

Der Mechanismus ist erklärbar. KMeans sieht ausschließlich den **verzögerten** negativen Trend: gefallene Kurse, gestiegene Volatilität. Der Algorithmus klassifiziert also den Zustand **nach** dem Rückgang.

Und genau dort setzt Mean Reversion an — die statistische Tendenz von Kursen, nach starken Ausschlägen zum Mittelwert zurückzukehren. Das „Bear"-Label markiert nicht den Beginn des Falls, sondern in vielen Fällen dessen Ende. Wer in diesem Zustand die Hände stillhält oder aussteigt, verpasst systematisch die Erholungs-Rallye.

## Der Praxis-Test: Wenn der Regime-Filter schadet

Ein Regime-Modell ist nur so gut wie das, was man damit macht. Wir haben es deshalb auf eine bekannte saisonale Strategie angewendet: nur in den historisch starken Monaten **April, November und Dezember** investiert sein — ein Muster, das wir im [Sektor-ETF-Artikel](/blog/sektor-etf-saisonalitaet-april-november-dezember/) ausführlich analysiert haben.

Dann die Zusatzregel: In Phasen, die das Modell als „Bear" klassifiziert, wird nicht investiert.

| Strategie | CAGR | Sharpe |
|---|---|---|
| Buy & Hold | **10,7 %** | 0,55 |
| Saisonal naiv (Apr/Nov/Dez) | 5,3 % | **1,13** |
| Saisonal + Regime-Filter (meide Bear) | 2,5 % | 0,76 |

Drei Dinge stehen in dieser Tabelle.

**Die saisonale Strategie hat die beste Effizienz.** Sharpe 1,13 gegenüber 0,55 bei Buy & Hold — mehr als doppelt so viel Ertrag pro Risikoeinheit. Der Preis: nur 5,3 % CAGR statt 10,7 %, weil das Kapital die meiste Zeit des Jahres nicht im Markt arbeitet.

**Der Regime-Filter macht alles schlechter.** Die Jahresrendite halbiert sich auf 2,5 %, die Sharpe Ratio fällt von 1,13 auf 0,76. Der Filter entfernt exakt die Phasen mit der höchsten Folgerendite — er schneidet die besten Einstiege heraus.

**Mehr Modell ist nicht automatisch besser.** Ein zusätzlicher, plausibel klingender Filter kann eine funktionierende Regel systematisch beschädigen. Das ist die vielleicht wichtigste praktische Lehre aus dem gesamten Versuch.

## Befund 2: Turn-of-Month mit ML — der DAX überrascht

Der zweite Algorithmus ist ein **Klassifikator**: Logistic Regression, ein überwachtes Verfahren, das aus historischen Merkmalen die Wahrscheinlichkeit für ein binäres Ereignis schätzt — hier: „steigt der Markt im nächsten Fenster?"

Als Fenster haben wir den [Turn-of-Month-Effekt](/blog/turn-of-month-effekt-erklaert/) gewählt: die **letzten drei und ersten drei Handelstage** eines Monats. Dieser Zeitraum gilt als eine der robustesten Kalenderanomalien überhaupt, getrieben von Gehaltszahlungen, Sparplan-Ausführungen und Fondszuflüssen zum Monatsersten.

Entscheidend ist die Testmethodik: **Walk-Forward über 2016 bis 2026**. Das Modell wird jeweils nur auf Vergangenheitsdaten trainiert und dann auf den nächsten, ungesehenen Zeitabschnitt angewendet — danach rückt das Fenster weiter. So lässt sich Overfitting weitgehend ausschließen: Das Modell kann nicht aus Daten lernen, die es beim Handeln noch gar nicht gab.

| Markt | Turn-of-Month + ML (Sharpe) | Buy & Hold (Sharpe) |
|---|---|---|
| SPY (S&P 500) | 0,40 | **0,81** |
| **DAX (^GDAXI)** | **0,85** | 0,66 |

Beim **SPY** bringt der ML-Filter keinen Vorteil — 0,40 gegen 0,81 für simples Buy & Hold. In einem Jahrzehnt, das für US-Aktien ein nahezu ununterbrochener Bullenmarkt war, verliert praktisch jede Strategie, die zeitweise an der Seitenlinie steht.

Beim **DAX** dreht sich das Bild. Sharpe 0,85 gegenüber 0,66 — und der Risikounterschied ist noch deutlicher: Der maximale Drawdown lag bei **–8,6 % statt –26,4 %**. Der Drawdown misst den größten Rückgang vom Höchststand bis zum Tiefpunkt, also die schmerzhafteste Phase für den Anleger.

Auch **GLD** (Gold-ETF) zeigt einen klaren Risikovorteil: maximaler Drawdown **–9,3 % statt –26,4 %**, wenn auch ohne den Renditevorsprung des DAX.

### Warum ausgerechnet der DAX?

Eine naheliegende Erklärung: Der DAX ist stärker von **kalendergetriebenen Kapitalflüssen** geprägt als der S&P 500. Europäische Indizes reagieren empfindlicher auf regelmäßige Zuflüsse zum Monatsanfang, während der US-Markt von wenigen global gehandelten Megacaps dominiert wird, deren Kursbildung ganzjährig von Nachrichten, Quartalszahlen und internationalen Flüssen getrieben wird.

Der saisonale Jahresverlauf des DAX über zehn Jahre zeigt das Muster, in dem die Monatswechsel-Struktur eingebettet ist:

{{chart:seasonal_yearly:^GDAXI:10}}

Der Chart nutzt **normalisierte Renditen**: Jedes Jahr startet bei 100, die täglichen Renditen kumulieren darauf. Absolute Kursdifferenzen werden nie über Jahre addiert — sonst würden spätere Jahre mit höherem Indexstand das Bild dominieren. Das schattierte Band zeigt die Streuung (±1 Standardabweichung) und damit, wie verlässlich der mittlere Verlauf tatsächlich ist.

## Grenzen: Was diese Zahlen nicht sagen

Vier Einschränkungen gehören zwingend dazu.

**Ein Regime-Label ist keine Prognose.** KMeans beschreibt den Zustand von gestern. Dass auf „Bear" historisch überdurchschnittliche Folgerenditen kamen, ist eine Beobachtung über 8.432 Handelstage — keine Garantie für den nächsten Abverkauf. In 2008 hätte dieselbe Logik über Monate hinweg zu früh eingekauft.

**Die Auswertungsperiode ist ungewöhnlich.** 2016 bis 2026 enthält für US-Aktien eine außergewöhnliche Bullenphase. Dass der SPY-Klassifikator gegen Buy & Hold verliert, sagt vor allem etwas über diesen Zeitraum aus.

**Sharpe-Werte ohne risikofreien Zins.** Alle genannten Sharpe Ratios sind als reines Rendite-zu-Volatilität-Verhältnis gerechnet. Sie sind untereinander vergleichbar, nicht mit Werten aus externen Quellen.

**Kosten und Steuern fehlen.** Die Turn-of-Month-Strategie handelt bis zu 24-mal pro Jahr. Spreads, Ordergebühren und Abgeltungsteuer sind in keiner der Zahlen enthalten und schmälern den Vorsprung spürbar.

## Was Privatanleger daraus mitnehmen können

Drei praktische Ableitungen:

**Erstens: Panik ist statistisch teuer.** Das Bear-Cluster war historisch die Phase mit den besten Folgerenditen. Wer nach starken Rückgängen verkauft, verkauft im Schnitt in die Erholung hinein.

**Zweitens: Filter brauchen einen Beleg, keine Plausibilität.** „Nicht investieren, wenn der Markt schlecht aussieht" klingt vernünftig und hat die Sharpe Ratio von 1,13 auf 0,76 gedrückt. Jede Zusatzregel gehört rückgetestet — idealerweise walk-forward.

**Drittens: Effekte sind marktabhängig.** Derselbe Turn-of-Month-Ansatz liefert beim DAX einen Edge und beim SPY nicht. Wer ein Muster übernimmt, sollte es auf dem eigenen Zielmarkt prüfen, nicht auf dem, in dem es publiziert wurde.

Nachrechnen lässt sich das direkt in SeasonAlpha:

- **[Monatswechsel](/monatswechsel)** — die Turn-of-Month-Kurve mit Signifikanz-Tacho (t-Wert, p-Wert, Win-Rate, n) für jeden Ticker
- **[TDOM-Analyse](/tdom-analyse)** — Rendite je Handelstag im Monat, börsenspezifisch gerechnet
- **[Backtest-Engine](/backtest-engine)** — eigene Kalenderregeln mit Indikator-Filtern kombinieren und auf Robustheit prüfen
- **[Jahreszyklus](/jahreszyklus)** — der normalisierte Jahresverlauf für `^GDAXI` oder jeden anderen Ticker

## Fazit

Zwei ML-Verfahren, zwei unbequeme Ergebnisse. Das vom Algorithmus als „Bear" klassifizierte Regime lieferte über 8.432 Handelstage die **höchste risikoadjustierte Folgerendite (Sharpe +0,89)** — deutlich vor dem Normalzustand (+0,63) und dem scheinbar attraktiven Bull-Regime (+0,01). Ein Filter, der diese Phasen meidet, kostete in unserem Test mehr als die Hälfte der Rendite.

Der Turn-of-Month-Klassifikator zeigt, dass Kalendereffekte nicht universell sind: Beim DAX ergab sich im Walk-Forward-Test ein echter Vorteil (Sharpe 0,85 gegen 0,66, Drawdown –8,6 % statt –26,4 %), beim SPY nicht.

Machine Learning liefert hier keine Empfehlung, sondern eine Beschreibung: Es zeigt, wo in den Daten Struktur steckt — und wo eine intuitiv sinnvolle Regel in die falsche Richtung zeigt. Prüfe die Monatswechsel-Statistik für deinen Ticker selbst auf **[seasonalpha.ai/monatswechsel](https://seasonalpha.ai/monatswechsel)**.

## Häufige Fragen

### Was ist ein Marktregime?
Ein Marktregime bezeichnet eine Marktphase mit ähnlichem Charakter, etwa hinsichtlich Trendrichtung und Schwankungsbreite. In unserer Auswertung hat KMeans-Clustering drei solcher Zustände in den SPY-Daten seit 1993 gefunden: Bull (15 % der Handelstage), Sideways (68 %) und Bear (17 %). Die Labels stammen aus den Merkmalen Rolling-Return und Rolling-Volatilität — nicht aus einer manuellen Einteilung.

### Warum liefert das Bear-Regime die besten Folgerenditen?
Weil das Modell den Zustand nach einem Rückgang beschreibt, nicht davor. Die Merkmale sind rückwärtsgerichtet, das „Bear"-Label markiert also gefallene Kurse und erhöhte Volatilität. Genau in dieser Situation setzt statistisch häufig Mean Reversion ein — die Rückkehr zum Mittelwert. Historisch ergab sich daraus die höchste annualisierte Sharpe Ratio der drei Regime (+0,89).

### Was bedeutet Walk-Forward-Analyse?
Das Modell wird nur auf Daten trainiert, die zeitlich vor dem Testzeitraum liegen, und dann auf den folgenden, ungesehenen Abschnitt angewendet. Danach rückt das Fenster weiter. Dieses Vorgehen verhindert, dass Ergebnisse durch Wissen über die Zukunft entstehen — der häufigste Grund, warum Backtests im Papier glänzen und in der Praxis versagen.

### Kann ich diese ML-Modelle in SeasonAlpha selbst nutzen?
Die hier beschriebenen Modelle sind Forschungsauswertungen auf der SeasonAlpha-Datenbasis und kein Produktfeature. Die zugrunde liegenden Muster lassen sich aber direkt prüfen: Der Turn-of-Month-Effekt inklusive Signifikanztest steht auf der Seite [Monatswechsel](/monatswechsel), eigene Regelkombinationen lassen sich in der [Backtest-Engine](/backtest-engine) testen.

<!--
#### Social Media Snippet

**LinkedIn:** Wir haben zwei klassische ML-Verfahren auf 30 Jahre Börsendaten angewendet — und das Ergebnis widerspricht der Intuition. 📊 KMeans-Clustering (SPY, 8.432 Handelstage seit 1993) findet drei Regime. Das als „Bear" klassifizierte Regime liefert die HÖCHSTE risikoadjustierte Folgerendite: Sharpe +0,89, vor Sideways (+0,63) und Bull (+0,01). Der Grund: Das Modell sieht den verzögerten Rückgang — und genau dort setzt Mean Reversion ein. Konsequenz: Ein Regime-Filter, der Bear-Phasen meidet, drückte eine saisonale Strategie von Sharpe 1,13 auf 0,76 und halbierte die Rendite. Zweiter Befund: Turn-of-Month mit Logistic Regression (Walk-Forward 2016–2026) funktioniert beim DAX (Sharpe 0,85 vs. 0,66 B&H, MaxDD –8,6 % statt –26,4 %), beim SPY nicht. Kalendereffekte sind offenbar nicht universell. Welchen Filter nutzt ihr — und habt ihr ihn rückgetestet? #MachineLearning #Saisonalität #DAX #SeasonAlpha

**Twitter/X:** ML auf 30 Jahren Börsendaten: Das vom Algorithmus als „Bear" klassifizierte Regime liefert die höchste risikoadjustierte Folgerendite (Sharpe +0,89) — vor Sideways (+0,63) und Bull (+0,01). Der Filter, der Bear meidet? Halbiert die Rendite. 📊 seasonalpha.ai #MachineLearning #Saisonalität #SeasonAlpha

#### Interne Verlinkung
- /monatswechsel (Turn-of-Month-Kurve mit Signifikanz-Tacho)
- /tdom-analyse (Rendite je Handelstag im Monat)
- /backtest-engine (eigene Regelkombinationen walk-forward prüfen)
- /jahreszyklus (normalisierter DAX-Jahresverlauf)
- /blog/turn-of-month-effekt-erklaert/ (Grundlagen des Effekts)
- /blog/turn-of-month-effekt-lebt-noch/ (aktueller Robustheits-Check)
- /blog/sektor-etf-saisonalitaet-april-november-dezember/ (die Apr/Nov/Dez-Basisstrategie)
- /blog/dax-vs-sp500-saisonalitaet/ (warum die beiden Indizes unterschiedlich ticken)

#### Content-Ideen (Folgeartikel)
- „Mean Reversion messen: Wie stark kehrt der Markt nach Rückgängen zurück?"
- „Overfitting im Backtest erkennen — 5 Warnsignale"
- „Warum der DAX kalendergetriebener ist als der S&P 500"
- „Regime-Erkennung ohne ML: Was einfache Volatilitäts-Schwellen leisten"
-->

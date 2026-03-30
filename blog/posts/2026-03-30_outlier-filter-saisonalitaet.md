---
title: "Outlier-Filter: Warum Crash-Jahre deine Analyse verzerren"
slug: outlier-filter-saisonalitaet
date: 2026-03-30
category: tutorials
tags: [outlier, ausreisser, saisonalitaet, iqr, winsorize, isolation-forest, statistik, tutorial]
description: "Crash-Jahre wie 2008 oder 2020 verzerren saisonale Muster. Der Outlier-Filter in SeasonAlpha zeigt dir, wie die Börse ohne Extremjahre wirklich tickt."
ticker: ^GSPC
status: published
---

<!--
Keyword-Plan:
- Haupt-Keyword: Outlier-Filter Saisonalität
- Neben-Keywords: Ausreißer Börse, Crash-Jahre filtern, IQR Methode Aktien, Winsorize Renditen, Isolation Forest Börse, saisonale Muster bereinigen, Extremjahre entfernen, statistische Ausreißer Aktien
- LSI-Keywords: Standardabweichung, Interquartilsabstand, Machine Learning Börse, robuste Statistik, Datenbereinigung
-->

## 2008 hat den September für immer ruiniert — oder?

Der September gilt als schlechtester Börsenmonat. Aber wie viel davon ist echtes saisonales Muster — und wie viel geht auf das Konto einzelner Crash-Jahre wie 2008 oder 2020?

Genau das ist das Problem mit Ausreißern in historischen Daten. Ein einziges Extremjahr kann den Durchschnitt so stark verzerren, dass das eigentliche saisonale Muster dahinter verschwindet. Der **Outlier-Filter** in SeasonAlpha macht diese Verzerrung sichtbar — und korrigierbar.

## Was sind Ausreißer in der Saisonalität?

Ausreißer sind Jahre, deren Kursverlauf extrem vom Normalfall abweicht. Typische Kandidaten:

- **2008** (Finanzkrise): S&P 500 verlor 38% im Jahr
- **2020** (COVID-Crash): 34% Einbruch in 23 Handelstagen, dann V-Recovery
- **2022** (Zinswende): Gleichzeitiger Aktien- und Anleihen-Crash

Diese Jahre sind historisch real und wichtig — aber sie dominieren den Durchschnitt. Wenn du 20 Jahre analysierst und ein Jahr hat -38% Rendite, zieht es den Mittelwert massiv nach unten, obwohl es nur 5% der Datenpunkte ausmacht.

Der Outlier-Filter hilft dir zu unterscheiden: **Was ist das typische saisonale Muster — und was ist der Effekt einzelner Extremereignisse?**

## Vier Methoden — von konservativ bis KI

SeasonAlpha bietet vier verschiedene Methoden, um Ausreißer zu behandeln. Jede hat ihre Stärken:

### IQR (1.5x) — Der Klassiker

Die Interquartilsabstand-Methode (IQR) ist der Standard in der Statistik. Sie berechnet den Bereich zwischen dem 25. und 75. Perzentil der Jahresrenditen und markiert alles, was mehr als das 1.5-fache darüber oder darunter liegt, als Ausreißer.

- **Effekt:** Entfernt moderate bis starke Ausreißer komplett
- **Typisch entfernt:** 2–4 Jahre bei 20 Jahren Datenhistorie
- **Geeignet für:** Einen ersten Überblick ohne Extremjahre

### IQR (3x, streng) — Nur die Extreme

Gleiche Methode, aber mit dreifachem IQR. Hier fallen nur die wirklich extremen Jahre heraus — echte Black-Swan-Events.

- **Effekt:** Entfernt nur 1–2 der krassesten Jahre
- **Geeignet für:** Konservative Analyse, wenn du nur die größten Verzerrungen eliminieren willst

### Winsorize (3 Sigma) — Clippen statt Löschen

Die Winsorisierung ist der eleganteste Ansatz: Kein Jahr wird entfernt. Stattdessen werden Extremwerte auf den Bereich Mittelwert ± 3 Standardabweichungen begrenzt.

- **Effekt:** Ein Jahr mit -38% wird z. B. auf -18% gekappt, bleibt aber in der Berechnung
- **Vorteil:** Die Stichprobengröße bleibt gleich — statistisch sauberer
- **Geeignet für:** Wenn dir die Datenbasis wichtig ist und du nichts löschen willst

### Isolation Forest (KI) — Mustererkennung

Der Isolation Forest ist ein Machine-Learning-Algorithmus aus dem Bereich der Anomalie-Erkennung. Er betrachtet nicht nur die Jahresrendite, sondern den **gesamten Kursverlauf** eines Jahres.

- **Effekt:** Erkennt Jahre mit atypischem Verlauf, auch wenn die Gesamtrendite normal aussieht
- **Beispiel:** 2020 hatte am Jahresende eine positive Rendite — aber der V-förmige Verlauf war hochgradig anomal
- **Geeignet für:** Fortgeschrittene Analyse, wenn du wirklich anomale Muster finden willst

## Wann solltest du den Outlier-Filter verwenden?

Der Filter ist kein Pflicht-Tool — aber in bestimmten Situationen macht er einen großen Unterschied:

**Verwende ihn, wenn:**

- Du saisonale Muster auf **Robustheit** prüfen willst: Bleibt der September-Effekt bestehen, wenn du 2008 rausnimmst?
- Du eine **kleine Datenbasis** hast (10–15 Jahre): Hier können einzelne Extremjahre den Durchschnitt besonders stark verschieben
- Du **verschiedene Zeiträume** vergleichst: Mit und ohne Ausreißer zeigt, wie stabil ein Muster wirklich ist
- Du den Unterschied zwischen **typischem Verlauf** und **Durchschnitt** verstehen willst

**Lass ihn aus, wenn:**

- Du bewusst die **Worst-Case-Szenarien** sehen willst (Risikomanagement)
- Du die **volle historische Realität** brauchst — mit allen Crashs
- Du nur wenige Jahre analysierst (unter 10) — dann fehlt die Basis für eine sinnvolle Erkennung

## Wie wichtig ist der Filter wirklich?

Der Outlier-Filter verändert deine Analyse nicht grundlegend — aber er **schärft den Blick**.

Stell dir einen Fotografen vor, der ein Landschaftsbild macht. Die Standardansicht zeigt die Landschaft mit ein paar extremen Lichtflecken (Ausreißer), die das Gesamtbild überblenden. Der Outlier-Filter ist wie ein Polfilter auf der Kamera: Er entfernt die Extremreflexionen und zeigt dir die Landschaft, wie sie unter normalen Bedingungen aussieht.

Konkret bedeutet das:

- **Monatliche Muster** werden klarer sichtbar, weil einzelne Crash-Monate nicht mehr den Durchschnitt dominieren
- **Win-Rates** verändern sich kaum (weil sie Ausreißer ohnehin gleich gewichten)
- **Durchschnittsrenditen** können sich dagegen deutlich verschieben — besonders bei Monaten, die von Crashs betroffen waren

## Grenzen des Outlier-Filters

So nützlich der Filter ist — er hat klare Grenzen, die du kennen solltest:

**1. Survivorship Bias:** Der Filter entfernt Extremjahre, die real passiert sind. Wenn du deine Strategie nur auf bereinigten Daten aufbaust, unterschätzt du das Risiko. Crashs kommen wieder.

**2. Kein richtig oder falsch:** Keine der vier Methoden ist objektiv besser. IQR ist simpel und transparent, Isolation Forest ist mächtig, aber schwerer nachvollziehbar. Die Wahl hängt von deiner Fragestellung ab.

**3. Subjektive Schwellenwerte:** Der IQR-Faktor 1.5 ist eine Konvention, kein Naturgesetz. Je nach Methode und Parameter fallen unterschiedliche Jahre heraus.

**4. Kleine Stichproben:** Bei weniger als 10 Jahren ist jede Ausreißer-Erkennung fragwürdig. Es fehlt schlicht die statistische Masse.

**5. Nicht für Prognosen:** Der Filter hilft beim Verstehen von Mustern — er verbessert nicht die Vorhersagekraft. Ein bereinigter Durchschnitt ist kein besserer Predictor als ein unbereinigter.

## So nutzt du den Outlier-Filter in SeasonAlpha

Der Filter ist direkt in die Sidebar integriert:

1. Öffne eine Analyseseite (z. B. **Jahreszyklus** oder **Monatszyklus**)
2. In der Sidebar findest du den Expander **Outlier-Filter**
3. Wähle eine der vier Methoden aus
4. Die Charts und Berechnungen aktualisieren sich sofort
5. Eine Info-Box zeigt dir, welche Jahre entfernt oder angepasst wurden

**Tipp:** Schalte den Filter ein und aus, um den Unterschied direkt zu sehen. So erkennst du auf einen Blick, welche Muster robust sind und welche von Extremjahren getrieben werden.

## Fazit

Der Outlier-Filter ist kein Muss — aber ein Werkzeug, das deine Analyse ehrlicher macht. Er zeigt dir, was das **typische** saisonale Muster ist, ohne dass einzelne Crash-Jahre den Blick verzerren.

Die goldene Regel: **Analysiere immer mit und ohne Filter.** Wenn ein Muster in beiden Varianten bestehen bleibt, hast du ein robustes Signal gefunden.

Probiere es selbst auf [seasonalpha.ai](https://seasonalpha.ai) — ein Klick in der Sidebar reicht.

## Häufige Fragen

### Was passiert mit meinen Daten, wenn ich den Outlier-Filter aktiviere?

Deine Originaldaten bleiben unverändert. Der Filter wirkt nur auf die Berechnung der saisonalen Durchschnittswerte. Bei IQR und Isolation Forest werden Ausreißer-Jahre aus der Mittelwertbildung ausgeschlossen. Bei Winsorize werden die Extremwerte begrenzt, aber kein Jahr entfernt.

### Welche Methode ist die beste für Einsteiger?

Starte mit **IQR (1.5x)** — die Methode ist transparent und nachvollziehbar. Du siehst sofort, welche Jahre herausfallen und warum. Wenn du tiefer einsteigen willst, probiere danach Isolation Forest für die KI-basierte Erkennung.

### Verändert der Outlier-Filter die Win-Rate?

Nur minimal. Die Win-Rate zählt, wie oft ein Monat oder Zeitraum positiv war — dabei zählt jedes Jahr gleich, egal ob +2% oder +20%. Der Filter wirkt hauptsächlich auf Durchschnittsrenditen, die von Extremwerten stark beeinflusst werden.

### Sollte ich meine Strategie auf gefilterten oder ungefilterten Daten aufbauen?

Beides ansehen. Die **gefilterten Daten** zeigen dir das typische Muster. Die **ungefilterten** zeigen dir, was im Ernstfall passieren kann. Eine robuste Strategie funktioniert in beiden Szenarien.

<!--
#### Social Media Snippet

**LinkedIn:** Crash-Jahre wie 2008 oder 2020 verzerren saisonale Muster an der Börse massiv. Ein einziges Extremjahr kann den Durchschnitt dominieren. In SeasonAlpha zeigt der Outlier-Filter mit 4 Methoden (IQR, Winsorize, Isolation Forest), wie robust ein Muster wirklich ist. Analysierst du mit oder ohne Ausreißer? seasonalpha.ai

**Twitter/X:** Der September ist der schlechteste Börsenmonat — wirklich? Oder verzerrt 2008 den Durchschnitt? Der Outlier-Filter in SeasonAlpha zeigt den Unterschied. 4 Methoden, 1 Klick. #Börse #Saisonalität #SeasonAlpha

#### Interne Verlinkung
- SeasonAlpha Jahreszyklus-Seite (Outlier-Filter aktiv in Sidebar)
- Blog: "Was ist Saisonalität?" (education, Grundlagen)
- Blog: "Wochentag-Signifikanztest Siemens" (tutorial, Statistik)

#### Content-Ideen (Folgeartikel)
- "IQR vs. Isolation Forest: Welche Ausreißer-Methode passt zu dir?" (Deep Dive)
- "Sell in May ohne 2008: Wie robust ist die Strategie wirklich?" (Marktausblick mit Outlier-Vergleich)
- "Robustheit testen: 5 Tricks für bessere saisonale Analysen" (Education)
-->

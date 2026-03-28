---
title: "Box-Plot lesen: Was der Dow Jones über Jahrzehnte verrät"
slug: boxplot-dekadenzyklus-dow-jones
date: 2026-03-28
category: tutorials
tags: [box-plot, dekadenzyklus, dow-jones, dji, saisonalität, rendite-verteilung, statistik, tutorial, 2026]
description: "Box-Plots einfach erklärt: Wie du die Rendite-Verteilung des Dow Jones nach Dekaden-Endziffer liest und welchen Vorteil dir das bringt."
ticker: ^DJI
screenshot: dekadenzyklus-boxplot-dji.png
status: published
---

<!-- Keyword-Plan
Haupt-Keyword: Box-Plot Börse erklären
Neben-Keywords: Dekadenzyklus Dow Jones, Jahresrendite nach Jahrzehnt, Rendite-Verteilung Aktien,
  Endziffer Börsenjahr, Saisonalität Dow Jones, historische Muster Aktien 2025,
  x5 Jahr Börse, Streuung Rendite verstehen, SeasonAlpha Dekadenzyklus
LSI: Median, Quartil, Ausreißer, Interquartilsabstand, Whisker, Kohorte
-->

## Durchschnitte lügen — Box-Plots nicht

„Das Jahr X war im Schnitt gut für Aktien." Solche Aussagen klingen beruhigend — verschweigen aber die entscheidende Frage: **Wie verlässlich war dieses Muster?**

Ein Durchschnitt von +10% kann aus 13 Jahren mit +15% und einem Jahr mit -50% entstehen. Der Box-Plot zeigt dir beides auf einen Blick: die typische Rendite **und** wie stark sie schwankt.

## Was ist ein Box-Plot?

Ein Box-Plot — auch Whisker-Diagramm genannt — ist eine kompakte Darstellung der Rendite-Verteilung. Er beantwortet fünf Fragen gleichzeitig:

- **Median (mittlere Linie):** Der typische Wert — genau die Hälfte der Jahre liegt darüber, die andere Hälfte darunter. Robuster als der Durchschnitt, weil Ausreißer ihn kaum beeinflussen.
- **Box (gefärbter Bereich):** Der Interquartilsabstand (IQR) — hier liegen die mittleren 50% aller Werte. Eine schmale Box = konsistentes Muster. Eine breite Box = hohe Streuung.
- **Whisker (gestrichelte Linien):** Die Spannweite der „normalen" Werte, typischerweise 1,5× der Box-Breite.
- **Punkte außerhalb:** Ausreißer — ungewöhnliche Ausnahmejahre, die aus dem Rahmen fallen.
- **Raute/Dreieck:** In SeasonAlpha der Mittelwert — oft nahe am Median, aber bei Ausreißern kann er stark abweichen.

## Der Dow Jones nach Dekaden-Endziffer

SeasonAlpha analysiert alle Jahre seit 1896 und gruppiert sie nach ihrer **Endziffer** (x0 bis x9). So entstehen Kohorten: Alle „x5-Jahre" (1925, 1935, 1945 ... 2015, 2025) werden gemeinsam ausgewertet.

![Box-Plot: Dow Jones Jahresrenditen nach Dekaden-Endziffer](dekadenzyklus-boxplot-dji.png)

Das Bild zeigt deutliche Unterschiede zwischen den Kohorten:

**x5-Jahre sind historisch die stärksten.** Der Median liegt bei rund +20%, die Box reicht durchgehend ins Positive — und selbst der Ausreißer nach oben (+60%) zeigt, welche Kraft diese Jahre entfalten können. 2025 gehört genau zu dieser Kohorte.

**x0- und x1-Jahre sind die gefährlichsten.** Beide zeigen Ausreißer von -75% bis -80% — das sind die großen Crashjahre (1930, 1931). Der Median liegt nahe null, die Box ist breit: hohes Risiko, wenig Verlässlichkeit.

**x3-, x4- und x8-Jahre** zeigen positive Mediane mit breiter Streuung — grundsätzlich freundlich, aber mit großen Schwankungen nach unten möglich.

**x9-Jahre** fallen durch eine auffällig schmale Box auf: Die mittleren 50% clustern eng um den Median. Das bedeutet: vergleichsweise konsistentes, vorhersehbares Muster — auch wenn der Median nur moderat positiv ist.

## Was sagt dir das als Anleger?

Drei Erkenntnisse, die ein Durchschnittswert allein nicht liefert:

**1. Median schlägt Mittelwert.** Bei x0 und x1 ist der Mittelwert durch die extremen Crashjahre nach unten verzerrt. Der Median ist ehrlicher: Er zeigt, was du in einem „normalen" x0-Jahr erwarten kannst.

**2. Breite Box = mehr Unsicherheit.** Ein positiver Median ist schön — aber wenn die Box von -30% bis +40% reicht, ist das kein verlässliches Muster. x5 überzeugt, weil Box **und** Median positiv sind.

**3. Ausreißer sind keine Fehler.** Sie zeigen dir das Worst-Case-Szenario. Wer in x1-Jahren (2001, 2011, 2021) investiert war, weiß: Die breite Box und der Ausreißer nach unten waren keine Theorie.

## So nutzt du den Dekadenzyklus in SeasonAlpha

1. Seite **„Dekadenzyklus"** öffnen
2. Ticker in der Sidebar eingeben (Standard: `^DJI`)
3. Den Expander **„Rendite-Verteilung nach Kohorte (Box-Plot)"** aufklappen
4. Hover über einzelne Boxen: Median, Q1, Q3, Min, Max werden angezeigt
5. Vergleiche: Welche Endziffer hat das aktuelle Jahr? Wie sieht die historische Box aus?

Das aktuelle Jahr 2026 trägt die Endziffer **x6** — eine Kohorte mit positivem Median, aber einem markanten Ausreißer nach oben (+60% in einem einzelnen Jahr). Die Box ist mittelbreit: moderate Verlässlichkeit.

## Fazit: Verteilungen statt Durchschnitte

Box-Plots sind eines der ehrlichsten Werkzeuge in der Datenanalyse — gerade an der Börse, wo ein einziges Crash-Jahr den Durchschnitt einer ganzen Dekade verzerrt. Sie zeigen dir nicht nur **was** historisch passiert ist, sondern **wie stabil** dieses Muster war.

Für das laufende Jahr 2026 (Endziffer x6): Der Median ist positiv, die Streuung moderat. Kein Grund zur Euphorie — aber auch kein Warnsignal wie bei x0 oder x1.

> **Analysiere dein aktuelles Börsenjahr auf [seasonalpha.ai](https://seasonalpha.ai)** — der Dekadenzyklus wartet auf dich.

---

## FAQ

### Was bedeutet die Endziffer beim Dekadenzyklus?
Die Endziffer eines Jahres (0–9) bestimmt seine Kohorte. Alle Jahre mit Endziffer 5 — also 1925, 1935, 1945 usw. — werden zusammen analysiert. So entsteht aus 130 Jahren Börsengeschichte eine belastbare Stichprobe von etwa 13 Jahren pro Kohorte.

### Warum ist der Median besser als der Durchschnitt?
Der Median ist der mittlere Wert einer sortierten Reihe — er wird von Ausreißern kaum beeinflusst. Ein einziger Crash wie 1931 (-53%) zieht den Durchschnitt stark nach unten, lässt den Median aber weitgehend unberührt. Für saisonale Muster ist der Median deshalb aussagekräftiger.

### Was sagt mir eine schmale Box?
Eine schmale Box (kleiner IQR) bedeutet, dass die mittleren 50% der Jahresrenditen eng beieinander liegen. Das Muster ist **konsistenter** — du weißt besser, was dich erwartet. Eine breite Box signalisiert hohe Unsicherheit, auch wenn der Median positiv ist.

### Sind x5-Jahre wirklich immer gut?
Historisch ja — aber „immer" gibt es an der Börse nicht. 2025 ist statistisch in einer starken Kohorte, aber der Box-Plot zeigt auch: Es gab x5-Jahre mit negativen Renditen. Die Statistik liefert Wahrscheinlichkeiten, keine Garantien.

### Für welche Märkte funktioniert der Dekadenzyklus?
SeasonAlpha zeigt den Dekadenzyklus für alle verfügbaren Ticker — von Dow Jones und S&P 500 über DAX und Euro Stoxx bis hin zu einzelnen Aktien und ETFs. Je länger die Datenhistorie, desto belastbarer die Aussage.

---

*Hinweis: Dieser Artikel dient ausschließlich der Information und Bildung. Er stellt keine Anlageberatung dar. Vergangene Muster garantieren keine zukünftigen Renditen.*

---

#### Social Media Snippet

**LinkedIn:**
📊 Wusstest du, dass nicht alle Börsenjahre gleich sind — je nach ihrer Endziffer?
Der Dow Jones zeigt seit 1896 ein klares Muster: x5-Jahre (wie 2025) sind historisch die stärksten Kohorten, x0- und x1-Jahre die riskantesten.
Aber ein Durchschnittswert allein reicht nicht — erst der Box-Plot zeigt, wie verlässlich ein Muster wirklich ist.
Welche Endziffer hat dein aktuelles Investmentjahr? 👇
🔗 seasonalpha.ai

**Twitter/X:**
📦 Box-Plots erklärt: Warum x5-Jahre beim Dow Jones historisch die stärksten sind — und warum der Durchschnitt dabei lügt.
👉 seasonalpha.ai #Börse #DowJones #Saisonalität #SeasonAlpha #Aktien2026

---

#### Interne Verlinkung
- Seite „Jahreszyklus" — saisonale Muster innerhalb eines Jahres
- Seite „Wochentage" — Rendite-Unterschiede nach Wochentag
- Blog: „Ist der Dienstag wirklich der beste Börsentag?" — Signifikanztests verstehen

---

#### Content-Ideen (Folgeartikel)
1. „x5 vs. x0: Die besten und schlechtesten Börsenjahrzehnte im Vergleich"
2. „Dekadenzyklus international: Gilt das Muster auch für DAX und Nikkei?"
3. „Wie viel Streuung ist zu viel? Wann du einem saisonalen Muster nicht vertrauen solltest"

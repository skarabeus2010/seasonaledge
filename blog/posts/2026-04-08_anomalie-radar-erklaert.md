---
title: "Anomalie-Radar erklärt: Warum SAP trotz −28 % im Chart 'Normal' sein kann"
seo_title: "Anomalie-Radar SeasonAlpha: Z-Score + Perzentil richtig lesen"
slug: anomalie-radar-erklaert
date: 2026-04-08
category: education
tags: [anomalie-radar, ki-score, perzentil, z-score, sap, education, statistische-anomalie, ki-analyse, abweichung, saisonalitaet]
description: "Der Anomalie-Radar zeigt fuer SAP Score 24/100 (Normal) — obwohl der Kurs 28 % unter dem Schnitt liegt. Warum Z-Score und Perzentil das richtig bewerten."
ticker: SAP
screenshot: anomalie-radar-sap-beispiel.png
status: published
---

<!--
Keyword-Plan:
- Haupt-Keyword: Anomalie-Radar erklaert
- Neben-Keywords: Z-Score Aktien, Perzentil-Rang Boerse, KI Quick-Check SeasonAlpha, statistische Anomalie Markt
- LSI: saisonale Abweichung, Standardabweichung Rendite, historischer Vergleich Aktie
-->

## Ein scheinbarer Widerspruch

Du öffnest den [Jahreszyklus für SAP](/jahreszyklus?t=SAP) und siehst auf den ersten Blick zwei widersprüchliche Dinge:

![Anomalie-Radar für SAP: Score 24/100 Normal, aber der Jahresverlauf 2026 liegt dramatisch unter dem 11-Jahres-Schnitt](anomalie-radar-sap-beispiel.png)

Oben: Der **Anomalie-Radar** zeigt einen Score von **24 / 100** — **Normal**. Alles in Butter.

Unten: Der **Saisonale Jahresverlauf** zeigt, dass SAP (goldene Linie) 2026 rund **28 Prozent unter dem 11-Jahres-Schnitt** liegt. Statt ~110 Punkten steht der Kurs bei ~72. Das sieht optisch wie ein Crash aus.

**Wie passt das zusammen?** Die Antwort ist die wichtigste Erkenntnis über den Anomalie-Radar: **Er misst nicht das, was du in diesem Chart siehst.**

## Was der Anomalie-Radar wirklich misst

Der Radar beantwortet eine sehr spezifische Frage:

> **„Ist die Rendite der letzten 10 Handelstage ungewöhnlich im Vergleich zum historischen Schnitt zur gleichen Kalenderzeit?"**

Drei Schlüsselwörter sind entscheidend:

- **Letzte 10 Tage** — nicht das ganze Jahr, nicht seit Januar, nicht der Drawdown. Nur die letzten 10 Handelstage.
- **Zur gleichen Kalenderzeit** — wir vergleichen April 2026 mit April 2015, April 2016, April 2017 und so weiter. Nicht mit Januar oder Juli.
- **Ungewöhnlich** — gemessen in Standardabweichungen (Z-Score), nicht in Prozentpunkten.

Der riesige Drawdown, den du im unteren Chart siehst, ist zum größten Teil **in Januar–März 2026 passiert**. Das war damals brutal — aber der Anomalie-Radar fragt nicht nach damals. Er fragt: Was ist in den letzten zwei Wochen los? Und die Antwort lautet: nichts besonders Dramatisches.

## Die Rechnung im Detail

Schauen wir die Zahlen aus dem Screenshot an:

| Kennzahl | Wert |
|---|---|
| **10d-Rendite SAP** (Ende März bis Anfang April 2026) | **−0,89 %** |
| **Historisch Ø** (Anfang April, 11 Jahre) | **+2,36 %** |
| **Differenz** | **−3,25 Prozentpunkte** |
| **Score** | **24 / 100** |
| **Perzentil-Rang** | **18. Perzentil** |

SAP liegt in den letzten 10 Tagen **3,25 Prozentpunkte unter** dem historischen Schnitt zur gleichen Kalenderzeit. Das klingt viel, ist es aber statistisch nicht — und hier kommt der Z-Score ins Spiel.

**Z-Score-Berechnung** (vereinfacht):

```
Z = (aktuelle Rendite − historischer Schnitt) / historische Standardabweichung
```

Wenn die historische Streuung der 10d-Returns Anfang April bei SAP zum Beispiel bei ±4 Prozentpunkten liegt, dann ist eine Abweichung von 3,25 PP nur etwa **0,8 Standardabweichungen** — also kein statistischer Ausreißer. Der Score skaliert den Betrag des Z-Scores mit Faktor 30 und deckelt bei 100:

```
Score = min(|Z| × 30, 100) = min(0,8 × 30, 100) = 24
```

**24 heißt: keine Anomalie.** Der Markt bewegt sich innerhalb des historisch normalen Rauschens.

## Warum der Perzentil-Rang trotzdem interessant ist

Der Score sagt „Normal". Der Perzentil-Rang sagt **18. Perzentil**. Das ist der Slider im Screenshot, der deutlich nach links zeigt — im gelben Randbereich, nicht mehr im grünen Normalbereich.

**Was bedeutet 18. Perzentil?**

> Von allen historischen 10-Tages-Fenstern, die Anfang April bei SAP gemessen wurden, waren nur **18 Prozent schlechter** als die aktuelle Rendite. 82 Prozent waren besser.

Das ist eine **komplementäre Sicht** zum Score:

- **Der Score** misst Abweichung vom Mittelwert in Standardabweichungen — „wie viele σ daneben?"
- **Der Perzentil-Rang** misst Position in der Verteilung — „wo stehst du im Ranking?"

Beide können unterschiedliche Signale geben. In diesem Fall:

- Score 24 = wenig Standardabweichungen daneben → nichts dramatisches
- Perzentil 18 = aber im unteren Fünftel der historischen Fälle → auffällig, nicht extrem

Diese Kombination ist genau das, was wir zeigen wollen: **Der Markt läuft schwächer als normal, aber nicht so schwach, dass es ein statistischer Ausreißer wäre.** Beides stimmt gleichzeitig.

**Farbcodierung Perzentil-Slider:**

| Perzentil | Farbe | Bedeutung |
|---|---|---|
| 20 – 80 | grün | Normal — im „mittleren Band" |
| 10 – 20 oder 80 – 90 | gold | Randbereich — auffällig |
| < 10 oder > 90 | rot | Extrem — statistisch selten |

SAP mit 18. Perzentil liegt knapp im gold-Bereich. Ein Wert von 5 oder 95 wäre rot — dann würde es wirklich krachen.

## Und der riesige Drawdown im Chart?

Der Jahresverlauf-Chart zeigt einen anderen Zeithorizont und eine andere Frage:

- **Anomalie-Radar:** Wo stehen wir in den letzten 10 Tagen gegenüber vergleichbaren Zeiträumen?
- **Saisonaler Jahresverlauf:** Wie verläuft das gesamte Jahr bis heute gegenüber dem Mehrjahres-Durchschnitt seit Januar?

SAP hatte im Januar und Februar eine heftige Korrektur — die sieht man im Verlauf sofort. Im März und April hat sich der Kurs allerdings **stabilisiert**. Er macht jetzt wieder Tagesbewegungen, die im historisch üblichen Rahmen liegen. Der Anomalie-Radar bestätigt genau das: **„Der Crash ist vorbei, die aktuelle Bewegung ist unauffällig."**

Das ist eine wichtige Info! Wer den Chart sieht und denkt „der fällt weiter", wird durch den Radar daran erinnert: Die letzten zwei Wochen waren kein Crash, sondern Seitwärts-Rauschen. Mit einer moderaten Unterperformance, aber nichts Dramatisches.

## Wann sollte der Score hoch sein?

Der Anomalie-Score springt auf ≥70 (**Stark anomal**) wenn:

- **Nach einem Flash-Crash:** Der Markt fällt in 10 Tagen 15 %, während historisch die gleiche Kalenderzeit im Schnitt +1 % macht. Differenz = −16 PP, bei einer typischen Standardabweichung von vielleicht 3 PP → Z-Score ≈ 5 → Score = 100.
- **Bei einer Parabel-Rally:** Der Markt steigt in 10 Tagen 12 %, während historisch +2 % normal wären. Differenz = +10 PP → Score = 80+.
- **Bei extrem untypischer Seitwärts-Stabilität** in einer historisch bewegten Periode — selten, aber möglich.

Der Score ist **kein Bullish/Bearish-Signal**. Er sagt nur: „Etwas Ungewöhnliches passiert, schau genauer hin." Die Richtung (nach oben oder unten) steht in den anderen Kacheln (10d-Rendite).

## Score-Schwellen im Überblick

| Score | Label | Deutung |
|---|---|---|
| **< 40** | Normal | Im historischen Rauschen |
| **40 – 69** | Leicht anomal | Auffällig, beobachten |
| **≥ 70** | Stark anomal | Statistischer Ausreißer, genauer hinschauen |

## Wofür benutze ich den Radar konkret?

Drei praktische Use-Cases:

1. **Trade-Filter:** Bevor du einen saisonalen Trade eingehst (z. B. Sell in May, Turn-of-Month), prüfe den Score. Bei ≥70 wartest du lieber — der Markt ist gerade in einem ungewöhnlichen Zustand, saisonale Muster könnten in dieser Woche weniger zuverlässig sein.
2. **Post-Mortem-Check:** Nach einer heftigen Marktbewegung: War das wirklich ein Ausreißer, oder nur Alltag? Der Perzentil-Rang und der Score geben dir eine nüchterne Einordnung.
3. **Kontext für den Chart:** Wenn dir ein Chart visuell dramatisch erscheint, prüf den Radar. Wie bei SAP hier — 28 % im Minus sieht dramatisch aus, aber die **letzten Tage** sind ruhig. Das ist eine andere Story.

## Fazit: Zwei verschiedene Fragen, zwei verschiedene Antworten

Der Anomalie-Radar und der saisonale Jahresverlauf messen **unterschiedliche Dinge**:

- **Jahresverlauf** = wo stehst du **seit Januar** gegenüber dem Mehrjahres-Mittel?
- **Anomalie-Radar** = ist deine aktuelle **10-Tages-Bewegung** statistisch ungewöhnlich?

Bei SAP im Screenshot:
- **Jahresverlauf sagt:** Das Jahr war schwierig (−28 % vs. Schnitt)
- **Anomalie-Radar sagt:** Aber aktuell ist es ruhig (−0,89 % in 10 Tagen, Score 24, 18. Perzentil)

Beides ist wahr. Beides ist nützlich. Die Kunst besteht darin, die richtige Frage zur richtigen Zeit zu stellen — und der Anomalie-Radar beantwortet eine sehr spezifische.

Wenn du selbst damit experimentieren willst: Der Radar ist auf dem [Jahreszyklus](/jahreszyklus), [Monatszyklus](/monatszyklus), [TDoM-Analyse](/tdom-analyse) und [Overnight vs. Intraday](/overnight) aktiv. Einfach den Ticker eintippen und den Score oben rechts prüfen. Die Methodik steckt im **ⓘ**-Badge neben dem Sektion-Titel — Hover drauf, und du siehst die Formel.

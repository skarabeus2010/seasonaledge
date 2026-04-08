---
title: "Turn-of-Month Effekt erklärt: Warum die letzten 3 und ersten 3 Tage des Monats anders sind"
seo_title: "Turn-of-Month Effekt: Warum Monatswechsel an der Börse besonders sind"
slug: turn-of-month-effekt-erklaert
date: 2026-04-09
category: education
tags: [turn-of-month, tom, saisonalitaet, education, sp500]
description: "Der Turn-of-Month Effekt: Warum die letzten 3 und ersten 3 Handelstage eines Monats statistisch deutlich besser laufen als der Rest. Mit Daten und Erklärung."
ticker: ^GSPC
screenshot: turn-of-month-tom-chart.png
status: published
---

<!--
Keyword-Plan:
- Haupt-Keyword: Turn of Month Effekt
- Neben-Keywords: TOM Strategie, Monatswechsel Börse, Pension Fund Effect, Window Dressing
- LSI: saisonale Strategie, Monatsultimo, intra-month Pattern
-->

## Was ist der Turn-of-Month Effekt?

Der **Turn-of-Month** (TOM) Effekt beschreibt eine der robustesten saisonalen Anomalien an den Aktienmärkten: Die letzten Handelstage eines Monats und die ersten Tage des Folgemonats liefern überdurchschnittliche Renditen — bei deutlich höherer Win-Rate als der Rest des Monats.

Konkret: Das **6-Tage-Fenster** vom drittletzten Tag des Monats bis zum dritten Handelstag des nächsten Monats macht oft mehr Rendite als die übrigen ~15 Handelstage zusammen. Das ist nicht nur ein Kuriosum — es ist eines der am besten dokumentierten Muster in der akademischen Finanzliteratur, erstmals beschrieben von Lakonishok und Smidt 1988.

## Die Daten: 30 Jahre S&P 500

Wir haben die letzten 30 Jahre des S&P 500 nach Position innerhalb des Monats ausgewertet. Jeder Handelstag wird als **TDOM** (Trading Day of Month) klassifiziert: TDOM 1 = erster Handelstag, TDOM 21 = letzter Handelstag (variiert je nach Monat).

| Position | Ø Tagesrendite | Win-Rate |
|---|---|---|
| **Letzte 3 Tage des Monats** (TDOM −3 bis −1) | **+0,15 %** | **62 %** |
| **Erste 3 Tage des Monats** (TDOM 1 bis 3) | **+0,12 %** | **60 %** |
| Mitte des Monats (TDOM 5–15) | +0,02 % | 53 % |
| Letztes Drittel (TDOM 15 bis −4) | –0,01 % | 51 % |

Das **6-Tage TOM-Fenster** macht zusammen rund **+0,8 % pro Monat** — das sind ~10 % Jahresrendite, wenn man nur diese 6 Tage handelt und den Rest in Cash sitzt. Der Markt insgesamt macht über die gleichen 30 Jahre ~9 % pro Jahr.

Anders gesagt: **Die TOM-Tage machen praktisch den gesamten Marktertrag** — die übrigen 15 Tage tragen kaum etwas bei.

![Intra-Monat TDOM-Verlauf S&P 500 mit dem typischen U-Shape am Monatswechsel](turn-of-month-tom-chart.png)

Im Chart siehst du das Muster sofort: Die Kurve fällt im letzten Drittel des Monats ab, dreht in den letzten 3 Tagen scharf nach oben und setzt diesen Aufschwung in den ersten 3 Tagen des Folgemonats fort. Genau diese 6 Tage bilden den TOM-Effekt.

## Heatmap: Welche Monate haben den stärksten TOM-Effekt?

Der Durchschnitt verschleiert, dass der TOM-Effekt nicht in jedem Monat gleich stark ist. Die folgende Heatmap zeigt für jede Monat-×-TDOM-Kombination den durchschnittlichen Tagesreturn:

![Turn-of-Month Heatmap S&P 500 — Monat × TDOM-Position](turn-of-month-heatmap.png)

Auffällig: Die TOM-Tage sind in **fast jedem Monat positiv** (grüne Felder am rechten und linken Rand jeder Zeile), aber besonders ausgeprägt in **November, Dezember und April**. Im September — dem statistisch schwächsten Monat — ist der Effekt am schwächsten und teilweise sogar negativ. Der TOM-Effekt wird also durch die saisonale Gesamtlage moduliert.

## Warum existiert der Effekt?

Es gibt drei plausible Erklärungen, die sich gegenseitig nicht ausschließen:

### 1. Pension Fund Inflows
Pensionsfonds und 401(k)-Pläne in den USA bekommen Beiträge typischerweise zum Monatsende oder Monatsanfang. Dieses Geld wird mechanisch in den Markt investiert — ein konstanter Buy-Flow, der genau zu TOM auftritt. Allein die US-Pension-Funds verwalten über 30 Billionen Dollar; selbst kleine prozentuale Zuflüsse bewegen den Markt.

### 2. Window Dressing
Fondsmanager polieren am Monatsende ihre Portfolios für die Reporting-Stichtage. Sie kaufen Outperformer und verkaufen Underperformer — was die starken Aktien noch stärker macht (Window Dressing). Ende-Quartals und Ende-Jahres-Effekte sind besonders ausgeprägt.

### 3. Liquidity Cycles
Unternehmen zahlen Gehälter zum Monatsende, Dividenden werden ausgeschüttet, Anleihezinsen fließen — der Cash-Flow im System ist um den Monatswechsel hoch. Mehr Cash = mehr Investment-Bereitschaft = höhere Nachfrage nach Aktien.

Keine dieser Erklärungen alleine reicht aus — aber zusammen erzeugen sie einen messbaren, persistenten Bias.

## Funktioniert der Effekt auch außerhalb des S&P 500?

Ja. Wir haben das gleiche Muster für **DAX, Nasdaq, Dow Jones und sogar Bitcoin** gefunden. Die Stärke variiert:

| Index | TOM-Spread (6 Tage vs Rest) |
|---|---|
| Nasdaq 100 | +0,9 % / Monat |
| S&P 500 | +0,8 % / Monat |
| DAX | +0,7 % / Monat |
| Dow Jones | +0,6 % / Monat |
| Bitcoin | +1,2 % / Monat |

Bitcoin ist überraschend deutlich — vermutlich weil dort kaum institutionelle Pension-Flows wirken, sondern Retail-Verhalten dominiert (Gehalt → DCA-Käufe).

## Wie tradest du den TOM-Effekt?

### Variante A: Strikt mechanisch
Long am drittletzten Handelstag des Monats, Close am dritten Handelstag des Folgemonats. Sechs Tage long, 15 Tage Cash. Einfach umzusetzen, aber Transaktionskosten fressen einen Teil des Edges.

### Variante B: Overnight Only
Long am Close des drittletzten Tages, jeden Tag overnight halten, Close am dritten Tag. Reduziert das Intraday-Risiko und nutzt zusätzlich den [Overnight-Effekt](/blog/overnight-intraday-split-google/).

### Variante C: Filter mit TDoM-Position
Im Dashboard zeigt dir die TDOM-Karte für die nächsten drei Handelstage Win-Rate und Ø Return. Wenn die Win-Rate >60 % ist, ist das ein TOM-Tag. Du tradest dann selektiv statt mechanisch.

## Wo der Effekt nicht funktioniert

Drei Warnungen:

1. **Crash-Monate** brechen das Muster: In Februar 2020 (COVID), September 2008 (Lehman), Oktober 2008 fiel der Markt durch — die TOM-Tage waren im freien Fall negativ. Mechanische TOM-Strategien brauchen einen Stop-Loss.
2. **Bear Markets allgemein:** In ausgeprägten Abwärtstrends ist der TOM-Effekt schwächer. Win-Rate fällt von 62 % auf ~52 %.
3. **Sehr kurze Monate** (Februar): Mit nur ~19 Handelstagen überlappen sich „Anfang" und „Ende" stärker, das Muster ist verwaschener.

## Fazit: Eine der besten saisonalen Anomalien überhaupt

Der TOM-Effekt ist real, statistisch signifikant über >130 Jahre und über Asset-Klassen hinweg konsistent. Wer ihn versteht, hat einen statistischen Edge — vorausgesetzt, er versteht auch die Grenzen.

Wenn du selbst nachschauen willst, wie der aktuelle TOM-Zustand für deinen Lieblings-Ticker aussieht: Die [Monatswechsel-Page](/monatswechsel) zeigt dir TOM-Heatmap, Signifikanztest und Streak-Analyse für jeden Ticker. Im [Dashboard](/dashboard) siehst du außerdem für die nächsten 3 Tage die TDOM-Position mit historischer Win-Rate.

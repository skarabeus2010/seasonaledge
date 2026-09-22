---
title: "Monthly-10-Strategie im Backtest: 32 Jahre SPY, 10 Handelstage pro Monat"
seo_title: "Monthly 10 Strategie: 32 Jahre SPY im Backtest"
slug: monthly-10-strategie
date: 2026-09-17
category: education
tags: [monthly-10, tdom, saisonalitaet, turn-of-month, backtest, spy]
description: "Monthly 10 Strategie im 32-Jahres-Backtest: halbe Schwankung, halbe Rendite, und der Ertrag kommt aus der Monatsmitte statt vom Monatswechsel."
ticker: SPY
status: published
---

<!--
Keyword-Plan:
- Haupt-Keyword: Monthly 10 Strategie
- Neben-Keywords: TDOM Strategie, Handelstag des Monats, Turn of Month Effekt, Monatsanfang Aktien, saisonale Handelsstrategie, Backtest SPY, Zeit im Markt, risikoadjustierte Rendite
- LSI: Handelstag, Kalendereffekt, Drawdown, Volatilität, Buy and Hold, Kasse, Trefferquote, S&P 500 ETF
-->

## Was die Monthly-10-Strategie macht

Die **Monthly-10-Strategie** hält eine Long-Position an zehn Handelstagen pro Monat und liegt die übrige Zeit in Kasse. Die Annahme dahinter: Aktien verdienen ihr Geld nicht gleichmäßig über den Monat verteilt, sondern an wiederkehrenden Tagen im Kalenderraster.

Wir haben die Regel über 32 volle Kalenderjahre SPY gerechnet: 1994 bis 2025, 8.054 Handelstage, Adjusted Close inklusive Dividenden.

Die Strategie arbeitet mit dem **Handelstag des Monats** (englisch *Trading Day of Month*, kurz TDOM). TDOM 1 ist der erste Handelstag eines Monats, TDOM 2 der zweite; Wochenenden und Börsenfeiertage zählen nicht mit. Je nach Kalender hat ein Monat 19 bis 23 Handelstage.

Long ist die Strategie an diesen Tagen:

- **TDOM 1–4** — der Monatsanfang
- **TDOM 9–12** — die Monatsmitte
- **die letzten beiden Handelstage** — das Monatsende

An allen übrigen Tagen liegt das Geld in Kasse, ohne unterstellte Verzinsung. Die markierten Tage bilden drei zusammenhängende Blöcke pro Monat, also drei Trades: Kauf zum Schluss des ersten Blocktages, Verkauf zum Schluss des letzten.

### Zeit im Markt: 33 Prozent statt 48

Zehn markierte Tage von rund 21 entsprechen knapp 48 % der Handelstage. Investiert ist die Strategie trotzdem nur **33,4 %** der Zeit. Gekauft wird zum **Schluss** des ersten Blocktages: Dieser Tag ist gelaufen, wenn die Position steht, und trägt keine Rendite mehr bei. Von zehn markierten Tagen bleiben sieben Renditetage.

Die Konvention bestimmt mit, welcher Block in der Auswertung gut aussieht. Dazu unten der Abschnitt „Grenzen dieser Zerlegung".

## Backtest SPY 1994–2025

![Monthly 10 gegen Buy & Hold: Wertentwicklung von 10.000 USD im SPY von 1994 bis 2025, logarithmische Skala — Endwert 56.883 USD gegen 259.463 USD](monthly-10-strategie/monthly10-equity-spy-de.png)

Aus 10.000 USD werden mit Buy & Hold 259.463 USD, mit Monthly 10 56.883 USD.

| Kennzahl | Monthly 10 | Buy & Hold |
|---|---:|---:|
| Gesamtrendite | 469 % | 2.495 % |
| Rendite p.a. (CAGR) | 5,58 % | 10,71 % |
| Volatilität p.a. | 10,79 % | 18,84 % |
| Rendite pro Risikoeinheit | 0,52 | 0,57 |
| Maximaler Drawdown | −41,0 % | −55,2 % |
| Zeit im Markt | 33,4 % | 100 % |
| Aus 10.000 USD wurden | 56.883 USD | 259.463 USD |

Die Strategie halbiert die Schwankungsbreite fast exakt und senkt den größten zwischenzeitlichen Verlust um 14 Prozentpunkte. Sie kostet dafür 5,13 Prozentpunkte Rendite pro Jahr.

Rendite geteilt durch Volatilität ergibt **0,52 für Monthly 10 und 0,57 für Buy & Hold**. Risikoadjustiert liegt die Strategie also leicht hinter dem Dauerinvestment. In der Jahreswertung lag sie in **10 von 32 Jahren** vorn, das sind 31 %.

## Beitrag der drei Blöcke

Jeder der drei Blöcke wurde in 32 Jahren 384-mal gehandelt. Getrennt aufgerechnet ergibt sich diese Verteilung.

![Beitrag je Block der Monthly-10-Strategie im SPY 1994–2025: Monatsanfang TDOM 1–4 +83 Prozent bei 60 Prozent Trefferquote, Monatsmitte TDOM 9–12 +287 Prozent bei 64 Prozent, Monatsende −20 Prozent bei 46 Prozent](monthly-10-strategie/monthly10-bloecke-spy-de.png)

| Block | Trades | Trefferquote | Kumulierter Beitrag |
|---|---:|---:|---:|
| Monatsanfang (TDOM 1–4) | 384 | 60 % | +83 % |
| Monatsmitte (TDOM 9–12) | 384 | 64 % | +287 % |
| Monatsende (letzte 2 Tage) | 384 | 46 % | −20 % |

Die **Monatsmitte** liefert mit +287 % mehr als das Dreifache des Monatsanfangs und hat mit 64 % die höchste Trefferquote. Der [Turn-of-Month-Effekt](/monatswechsel), also die Stärke rund um den Monatswechsel, gehört zu den bekannteren Kalendermustern; in dieser Regelkonstruktion liegt er hinter TDOM 9–12.

### Grenzen dieser Zerlegung

Das Minus im Monatsend-Block ist überwiegend ein Artefakt der Einstiegskonvention. Steigt man einen Handelstag früher ein, sodass alle markierten Tage Rendite tragen, dreht der Block von −20 % auf **+14 %** und die Trefferquote von 46 % auf 51 %.

**Wichtig:** Der Monatsend-Block verliert kein Geld systematisch. Er trägt praktisch nichts bei, und über welche Seite der Null er dabei landet, entscheidet eine technische Detailregel. Stabil über beide Konventionen bleibt die Rangfolge: TDOM 9–12 trägt am meisten, das Monatsende am wenigsten.

### Beitrag der ausgelassenen Tage

Die 67 % der Zeit, die Monthly 10 in Kasse verbringt, waren nicht wertlos: Diese Tage brachten kumuliert **+356 %**. Sie trugen zugleich den größeren Rückschlag, mit **−58,9 %** maximalem Drawdown gegenüber −41,0 % für die Strategie-Tage.

## Jahresrenditen: antizyklisches Profil

![Jahresrenditen Monthly 10 gegen Buy & Hold im SPY von 1994 bis 2025 als Balkenpaare: Vorsprung in Baissejahren wie 2000, 2001, 2002, 2008 und 2022, Rückstand in Haussejahren wie 2013, 2023 und 2024](monthly-10-strategie/monthly10-jahre-spy-de.png)

In Baissejahren liegt Monthly 10 vorn:

- **2000:** +11,4 % gegen −9,7 %
- **2001:** +8,1 % gegen −11,8 %
- **2002:** −1,2 % gegen −21,6 %
- **2008:** −27,8 % gegen −36,8 %
- **2022:** −2,5 % gegen −18,2 %

In starken Haussejahren fällt sie deutlich zurück:

- **2013:** +5,4 % gegen +32,3 %
- **2023:** +6,1 % gegen +26,2 %
- **2024:** +2,3 % gegen +24,9 %

Wer nur ein Drittel der Zeit investiert ist, nimmt in Aufwärtsphasen einen Bruchteil der Bewegung mit und in Abwärtsphasen einen Bruchteil der Verluste. 2008 markiert die Grenze des Schutzes: −27,8 % sind auch für ein Kasse-lastiges Regelwerk ein hartes Jahr.

## Einordnung für Anleger

Monthly 10 senkt Schwankung und Rendite gleichzeitig, risikoadjustiert bleibt ein kleines Minus gegenüber Buy & Hold. Als Ersatz für ein breites Aktieninvestment taugt die Regel nach diesen Daten nicht. In Frage kommt sie als Baustein für Depots, in denen die Schwankungsbreite eine harte Nebenbedingung ist, oder als Ergänzung neben einer Kernposition.

In allen Zahlen oben fehlen **Transaktionskosten**. Drei Trades pro Monat sind 36 Roundturns im Jahr. Weil die Strategie ohnehin keinen Renditevorsprung hat, geht jede Gebühr direkt von der Substanz ab. Wer die Regel ernsthaft prüft, rechnet die eigenen Konditionen ein.

Praktisch verwertbar ist die Zerlegung: Dass TDOM 9–12 den größten Teil trägt, spricht dafür, einzelne Handelstage getrennt zu betrachten, statt Regelpakete am Stück zu bewerten.

Auf SeasonAlpha lässt sich beides nachvollziehen: Monthly 10 steht in der [Backtest-Engine](/backtest-engine) unter den Monatsmustern und lässt sich auf jeden Ticker im Universum anwenden. Die Einzeltag-Sicht liefert die [Turn-of-Month-Seite](/monatswechsel), den Vergleich mehrerer Regelwerke nebeneinander die [Plain-Vanilla-Übersicht](/plain-vanilla). Wer wissen will, bei welchen Titeln ein Monatsmuster aktuell auffällig ist, startet im [Saisonal-Scanner](/scanner). Zum verwandten Thema: unser Backtest zum [Turn-of-Month nach Down-Monaten](/blog/spy-turn-of-month-down-monat-reversal-backtest/).

## Fazit

Über 32 Jahre SPY liefert die Monthly-10-Strategie 5,58 % p.a. gegen 10,71 % für Buy & Hold, bei 10,79 % statt 18,84 % Volatilität und −41,0 % statt −55,2 % maximalem Drawdown. Pro Risikoeinheit steht 0,52 gegen 0,57.

Die Zerlegung zeigt die Struktur dahinter: **Die Monatsmitte (TDOM 9–12) trägt +287 %**, der Monatsanfang +83 %, das Monatsende praktisch nichts. Die Zeit im Markt liegt wegen der Einstiegskonvention bei 33,4 % statt bei 48 %.

**Kein Signal:** Diese Zahlen sind Durchschnitte über 32 Jahre mit großer Streuung, keine Prognose für den nächsten Monat. Probiere die Regel mit deinen eigenen Tickern und Zeiträumen auf [seasonalpha.ai](https://seasonalpha.ai/backtest-engine).

Monthly 10 gehört zu den vier Regeln, die in unserer Zusammenstellung nicht halten. Die übrigen zehn stehen unter [elf Börsenregeln nachgerechnet](/blog/boersenregeln-nachgerechnet/).

## Häufige Fragen

### Was ist die Monthly-10-Strategie?

Eine regelbasierte Strategie, die nur an zehn markierten Handelstagen pro Monat long ist: TDOM 1–4, TDOM 9–12 und den letzten beiden Handelstagen. An allen übrigen Tagen wird Kasse gehalten. Gehandelt wird jeweils zum Schluss des ersten und letzten Tages eines Blocks, also drei Trades pro Monat.

### Schlägt Monthly 10 den Markt?

Nach unserem Backtest über SPY 1994–2025 nicht. Die Strategie kommt auf 5,58 % pro Jahr gegen 10,71 % für Buy & Hold und lag nur in 10 von 32 Jahren vorn. Sie senkt allerdings Volatilität (10,79 % statt 18,84 %) und maximalen Drawdown (−41,0 % statt −55,2 %). Risikoadjustiert liegt sie mit 0,52 gegen 0,57 knapp hinten.

### Was bedeutet TDOM?

TDOM steht für *Trading Day of Month*, den Handelstag des Monats. TDOM 1 ist der erste Handelstag, TDOM 2 der zweite. Wochenenden und Börsenfeiertage zählen nicht mit, weshalb TDOM je nach Monat vom Kalendertag abweicht. Maßgeblich ist der Handelsplatz mit seinem eigenen Feiertagskalender, nicht das Heimatland eines Unternehmens.

### Warum ist die Strategie nur 33 % der Zeit investiert und nicht 48 %?

Weil der Einstieg zum **Schluss** des ersten Blocktages erfolgt. Dieser Tag ist damit bereits gelaufen und trägt keine Rendite mehr bei. Von zehn markierten Tagen bleiben effektiv sieben Renditetage, also 33,4 % statt der erwarteten rund 48 %.

### Welcher Teil des Monats trägt am meisten bei?

Die Monatsmitte. Über 384 Trades je Block lieferte TDOM 9–12 kumuliert +287 % bei 64 % Trefferquote, der Monatsanfang (TDOM 1–4) +83 % bei 60 %. Das Monatsende trägt praktisch nichts bei; ob es knapp negativ oder knapp positiv ausfällt, hängt an der Einstiegskonvention.

<!--
#### Social Media Snippet

**LinkedIn:**
Die Monthly-10-Strategie ist nur an 10 Handelstagen pro Monat im Markt: TDOM 1–4, 9–12 und den letzten beiden. Wir haben sie über 32 Jahre SPY gerechnet (1994–2025, Adjusted Close).
Ergebnis: 5,58 % p.a. gegen 10,71 % für Buy & Hold. Dafür 10,79 % statt 18,84 % Volatilität und −41,0 % statt −55,2 % maximaler Drawdown. Pro Risikoeinheit 0,52 gegen 0,57.
In der Zerlegung trägt die Monatsmitte (TDOM 9–12) mit +287 % über 384 Trades den größten Teil, deutlich mehr als der Monatswechsel.
Welchen Teil des Monats beobachtet ihr? → seasonalpha.ai

**Twitter/X:**
Monthly 10 im 32-Jahres-Test (SPY): 5,58 % p.a. vs. 10,71 % Buy & Hold, bei halber Vola und −41 % statt −55 % Drawdown.
Größter Beitrag kommt aus der Monatsmitte (TDOM 9–12, +287 %), nicht vom Monatswechsel.
#Börse #Saisonalität #SeasonAlpha

#### Interne Verlinkung
- /backtest-engine (Monthly 10 live nachrechnen)
- /monatswechsel (Turn-of-Month-Einzeltagsicht)
- /plain-vanilla (Regelwerke im Vergleich)
- /scanner (auffällige Monatsmuster je Ticker)
- /blog/spy-turn-of-month-down-monat-reversal-backtest/ (verwandter Backtest)

#### Content-Ideen (Folgeartikel)
- „TDOM 9–12: Was die Monatsmitte im Index-Vergleich liefert" — Einzeltagsanalyse über mehrere Indizes
- „Monthly 10 auf DAX, Nasdaq und Gold" — hält der Befund außerhalb des S&P 500?
- „Wie viel frisst die Gebühr? 36 Roundturns pro Jahr im Kostentest"
-->

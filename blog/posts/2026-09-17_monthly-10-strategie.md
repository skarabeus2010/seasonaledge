---
title: "Die Monthly-10-Strategie im Test: 32 Jahre SPY, 10 Handelstage pro Monat — und ein überraschender Treiber"
seo_title: "Monthly 10 Strategie: 32 Jahre SPY im Backtest"
slug: monthly-10-strategie
date: 2026-09-17
category: education
tags: [monthly-10, tdom, saisonalitaet, turn-of-month, backtest, spy]
description: "Monthly 10 Strategie im 32-Jahres-Backtest: halbe Schwankung, halbe Rendite — und der Ertrag kommt aus der Monatsmitte, nicht vom Monatswechsel."
ticker: SPY
status: published
---

<!--
Keyword-Plan:
- Haupt-Keyword: Monthly 10 Strategie
- Neben-Keywords: TDOM Strategie, Handelstag des Monats, Turn of Month Effekt, Monatsanfang Aktien, saisonale Handelsstrategie, Backtest SPY, Zeit im Markt, risikoadjustierte Rendite
- LSI: Handelstag, Kalendereffekt, Drawdown, Volatilität, Buy and Hold, Kasse, Trefferquote, S&P 500 ETF
-->

## 10 von 21 Tagen im Markt — reicht das?

Die **Monthly-10-Strategie** hält eine simple Behauptung hoch: Aktien verdienen ihr Geld nicht gleichmäßig über den Monat, sondern an wenigen wiederkehrenden Handelstagen. Wer nur an diesen Tagen investiert ist und sonst in Kasse bleibt, soll den Markt mit deutlich weniger Risiko begleiten.

Wir haben die Regel auf 32 volle Kalenderjahre SPY losgelassen (1994–2025, 8.054 Handelstage, Adjusted Close inklusive Dividenden). Das Ergebnis ist nicht das, was Strategie-Marketing üblicherweise verspricht — und der interessanteste Befund steckt nicht im Monatswechsel, über den alle reden.

## Was die Monthly-10-Strategie genau macht

Die Strategie arbeitet mit dem **Handelstag des Monats** (englisch *Trading Day of Month*, kurz TDOM). TDOM 1 ist der erste Handelstag eines Monats, TDOM 2 der zweite — Wochenenden und Börsenfeiertage zählen nicht mit. Ein Monat hat je nach Kalender 19 bis 23 Handelstage.

Long ist die Strategie nur an diesen Tagen:

- **TDOM 1–4** — der Monatsanfang
- **TDOM 9–12** — die Monatsmitte
- **die letzten beiden Handelstage** — das Monatsende

An allen übrigen Tagen liegt das Geld in Kasse, ohne unterstellte Verzinsung. Aus den markierten Tagen entstehen drei zusammenhängende Blöcke pro Monat, also drei Trades: rein zum Schluss des ersten Blocktages, raus zum Schluss des letzten.

### Warum die Strategie nur 33 % der Zeit im Markt ist

Zehn markierte Tage von rund 21 — das klingt nach knapp 48 % Marktzeit. Tatsächlich sind es **33,4 %**. Der Grund liegt in der Einstiegskonvention: Gekauft wird zum **Schluss** des ersten Blocktages. Dieser Tag trägt damit selbst keine Rendite mehr bei, er ist bereits vorbei, wenn die Position steht.

Von zehn markierten Tagen bleiben so effektiv sieben Renditetage übrig. Diese Konvention klingt nach Kleinkram, sie erklärt aber einen erheblichen Teil der folgenden Zahlen — und sie bestimmt, welcher Block am Ende gut aussieht.

## Der 32-Jahres-Backtest: SPY 1994–2025

![Monthly 10 gegen Buy & Hold: Wertentwicklung von 10.000 USD im SPY von 1994 bis 2025, logarithmische Skala — Endwert 56.883 USD gegen 259.463 USD](monthly-10-strategie/monthly10-equity-spy-de.png)

Die Kurven trennen sich früh und bleiben getrennt. Buy & Hold macht aus 10.000 USD im Betrachtungszeitraum 259.463 USD, Monthly 10 kommt auf 56.883 USD.

| Kennzahl | Monthly 10 | Buy & Hold |
|---|---:|---:|
| Gesamtrendite | 469 % | 2.495 % |
| Rendite p.a. (CAGR) | 5,58 % | 10,71 % |
| Volatilität p.a. | 10,79 % | 18,84 % |
| Rendite pro Risikoeinheit | 0,52 | 0,57 |
| Maximaler Drawdown | −41,0 % | −55,2 % |
| Zeit im Markt | 33,4 % | 100 % |
| Aus 10.000 USD wurden | 56.883 USD | 259.463 USD |

Zwei Dinge fallen auf. Erstens: Die Strategie halbiert die Schwankungsbreite fast exakt und senkt den größten zwischenzeitlichen Verlust um 14 Prozentpunkte. Zweitens: Sie kostet dafür mehr als die Hälfte der Rendite.

Teilt man Rendite durch Risiko, bleibt **0,52 gegen 0,57** — Monthly 10 liegt leicht hinten. Risikoadjustiert ist die Strategie gegenüber Buy & Hold kein Gewinn, sondern ein Nullsummenspiel mit kleinem Minus.

Auch in der Jahreswertung bleibt wenig Spielraum für Begeisterung: Monthly 10 schlug Buy & Hold in **10 von 32 Jahren**, also in 31 % der Fälle.

## Der eigentliche Befund: Die Monatsmitte trägt die Strategie

Jeder der drei Blöcke wurde in 32 Jahren 384-mal gehandelt. Rechnet man deren Beiträge getrennt auf, verschiebt sich das Bild dessen, was hier eigentlich arbeitet.

![Beitrag je Block der Monthly-10-Strategie im SPY 1994–2025: Monatsanfang TDOM 1–4 +83 Prozent bei 60 Prozent Trefferquote, Monatsmitte TDOM 9–12 +287 Prozent bei 64 Prozent, Monatsende −20 Prozent bei 46 Prozent](monthly-10-strategie/monthly10-bloecke-spy-de.png)

| Block | Trades | Trefferquote | Kumulierter Beitrag |
|---|---:|---:|---:|
| Monatsanfang (TDOM 1–4) | 384 | 60 % | +83 % |
| Monatsmitte (TDOM 9–12) | 384 | 64 % | +287 % |
| Monatsende (letzte 2 Tage) | 384 | 46 % | −20 % |

Das Schwergewicht liegt in der **Monatsmitte**. TDOM 9–12 liefert mit +287 % mehr als das Dreifache des Monatsanfangs und hat mit 64 % auch die höchste Trefferquote. Der gefeierte Monatswechsel ist nicht der Motor dieser Strategie.

Das ist bemerkenswert, weil der [Turn-of-Month-Effekt](/monatswechsel) — die Stärke rund um den Monatswechsel — zu den meistzitierten Kalendermustern überhaupt gehört. In dieser konkreten Regelkonstruktion landet er auf Platz zwei.

### Grenzen dieser Zerlegung

Das Minus im Monatsend-Block ist überwiegend ein Artefakt der Einstiegskonvention. Steigt man einen Handelstag früher ein, sodass alle markierten Tage Rendite tragen, dreht der Block von −20 % auf **+14 %** und die Trefferquote von 46 % auf 51 %.

**Wichtig:** Der Monatsend-Block verliert also nicht systematisch Geld — er trägt praktisch nichts bei, und wo genau er landet, entscheidet eine technische Detailregel. Robust über beide Konventionen bleibt die eigentliche Aussage: **Die Monatsmitte trägt die Strategie, das Monatsende ist das schwächste Bein.**

### Und die ausgelassenen Tage?

Die 67 % der Zeit, die Monthly 10 in Kasse verbringt, waren nicht wertlos: Sie brachten kumuliert **+356 %**. Sie trugen allerdings auch den größeren Rückschlag — der maximale Drawdown dieser Resttage lag bei **−58,9 %** gegenüber −41,0 % für die Strategie-Tage.

Genau das ist der Tausch, den Monthly 10 vornimmt: Man verzichtet auf Ertrag, um die unruhigeren Marktphasen auszusitzen.

## Ein antizyklisches Profil

Die Jahresrenditen zeigen, wann die Strategie glänzt — und wann sie zurückfällt.

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

Das Muster ist logisch: Wer nur ein Drittel der Zeit investiert ist, nimmt in Aufwärtsphasen nur einen Bruchteil der Bewegung mit — verpasst in Abwärtsphasen aber ebenso zwei Drittel der Verluste. 2008 zeigt allerdings, dass der Schutz keine Absicherung ist: −27,8 % sind auch für ein Kasse-lastiges Regelwerk ein hartes Jahr.

## Was Anleger daraus mitnehmen können

Monthly 10 ist keine Rendite-, sondern eine Risikostrategie. Sie halbiert die Schwankung und senkt den Drawdown, bezahlt das aber mit mehr als der Hälfte der Rendite. Als Ersatz für ein breites Aktieninvestment taugt sie nach diesen Daten nicht.

Interessanter ist sie als **Baustein**: für Depots, in denen die Schwankungsbreite eine harte Nebenbedingung ist, oder als Baustein neben einer Kernposition. Ein Punkt fehlt in allen Zahlen oben: **Transaktionskosten**. Drei Trades pro Monat sind 36 Roundturns pro Jahr — bei einem CAGR-Vorsprung, den die Strategie ohnehin nicht hat, frisst das direkt an der Substanz. Wer die Strategie ernsthaft prüft, muss die eigenen Gebühren einrechnen.

Der praktisch wertvollste Befund ist die Zerlegung. Dass TDOM 9–12 den größten Teil trägt, ist ein Hinweis darauf, dass der Kalendermonat mehr Struktur hat als das eine, viel zitierte Monatswechsel-Fenster — und dass es sich lohnt, einzelne Handelstage getrennt zu betrachten statt Regelpakete am Stück zu bewerten.

Auf SeasonAlpha lässt sich beides nachvollziehen: Monthly 10 steht in der [Backtest-Engine](/backtest-engine) unter den Monatsmustern und lässt sich auf jeden Ticker im Universum anwenden. Die Einzeltag-Sicht liefert die [Turn-of-Month-Seite](/monatswechsel), den Vergleich mehrerer Regelwerke nebeneinander die [Plain-Vanilla-Übersicht](/plain-vanilla). Wer wissen will, bei welchen Titeln ein Monatsmuster aktuell auffällig ist, startet im [Saisonal-Scanner](/scanner). Zum verwandten Thema: unser Backtest zum [Turn-of-Month nach Down-Monaten](/blog/spy-turn-of-month-down-monat-reversal-backtest/).

## Fazit

Die Monthly-10-Strategie liefert über 32 Jahre SPY 5,58 % p.a. gegen 10,71 % für Buy & Hold, bei 10,79 % statt 18,84 % Volatilität und −41,0 % statt −55,2 % maximalem Drawdown. Pro Risikoeinheit bleibt 0,52 gegen 0,57 — leicht schlechter als einfach investiert zu bleiben.

Der Mehrwert liegt nicht im Gesamtergebnis, sondern in der Zerlegung: **Die Monatsmitte (TDOM 9–12) trägt mit +287 % das meiste**, der Monatsanfang folgt mit +83 %, das Monatsende trägt nichts bei. Und die Zeit im Markt beträgt wegen der Einstiegskonvention nur 33,4 %, nicht 48 %.

**Kein Signal:** Diese Zahlen sind Durchschnitte über 32 Jahre mit großer Streuung, keine Prognose für den nächsten Monat. Probiere die Regel mit deinen eigenen Tickern und Zeiträumen auf [seasonalpha.ai](https://seasonalpha.ai/backtest-engine).

## Häufige Fragen

### Was ist die Monthly-10-Strategie?

Eine regelbasierte Strategie, die nur an zehn markierten Handelstagen pro Monat long ist: TDOM 1–4, TDOM 9–12 und den letzten beiden Handelstagen. An allen übrigen Tagen wird Kasse gehalten. Gehandelt wird jeweils zum Schluss des ersten und letzten Tages eines Blocks, also drei Trades pro Monat.

### Schlägt Monthly 10 den Markt?

Nach unserem Backtest über SPY 1994–2025 nicht. Die Strategie kommt auf 5,58 % pro Jahr gegen 10,71 % für Buy & Hold und lag nur in 10 von 32 Jahren vorn. Sie senkt allerdings Volatilität (10,79 % statt 18,84 %) und maximalen Drawdown (−41,0 % statt −55,2 %). Risikoadjustiert liegt sie mit 0,52 gegen 0,57 knapp hinten.

### Was bedeutet TDOM?

TDOM steht für *Trading Day of Month*, den Handelstag des Monats. TDOM 1 ist der erste Handelstag, TDOM 2 der zweite. Wochenenden und Börsenfeiertage zählen nicht mit, weshalb TDOM je nach Monat vom Kalendertag abweicht — und weshalb der Handelsplatz mit seinem eigenen Feiertagskalender zählt, nicht das Heimatland eines Unternehmens.

### Warum ist die Strategie nur 33 % der Zeit investiert und nicht 48 %?

Weil der Einstieg zum **Schluss** des ersten Blocktages erfolgt. Dieser Tag ist damit bereits gelaufen und trägt keine Rendite mehr bei. Von zehn markierten Tagen bleiben effektiv sieben Renditetage — 33,4 % statt der erwarteten rund 48 %.

### Welcher Teil des Monats trägt am meisten bei?

Die Monatsmitte. Über 384 Trades je Block lieferte TDOM 9–12 kumuliert +287 % bei 64 % Trefferquote, der Monatsanfang (TDOM 1–4) +83 % bei 60 %. Das Monatsende trägt praktisch nichts bei — ob es knapp negativ oder knapp positiv ausfällt, hängt an der Einstiegskonvention.

<!--
#### Social Media Snippet

**LinkedIn:**
Die Monthly-10-Strategie ist nur an 10 Handelstagen pro Monat im Markt — TDOM 1–4, 9–12 und den letzten beiden. Wir haben sie über 32 Jahre SPY gerechnet (1994–2025, Adjusted Close).
Ergebnis: 5,58 % p.a. gegen 10,71 % für Buy & Hold. Dafür 10,79 % statt 18,84 % Volatilität und −41,0 % statt −55,2 % maximaler Drawdown. Pro Risikoeinheit: 0,52 gegen 0,57 — also kein Vorteil.
Der eigentliche Befund steckt in der Zerlegung: Nicht der viel zitierte Monatswechsel trägt die Strategie, sondern die Monatsmitte (TDOM 9–12) mit +287 % über 384 Trades.
Welchen Teil des Monats beobachtet ihr? → seasonalpha.ai

**Twitter/X:**
Monthly 10 im 32-Jahres-Test (SPY): 5,58 % p.a. vs. 10,71 % Buy & Hold — aber nur halbe Vola und −41 % statt −55 % Drawdown.
Der Treiber ist NICHT der Monatswechsel, sondern die Monatsmitte (TDOM 9–12, +287 %).
#Börse #Saisonalität #SeasonAlpha

#### Interne Verlinkung
- /backtest-engine (Monthly 10 live nachrechnen)
- /monatswechsel (Turn-of-Month-Einzeltagsicht)
- /plain-vanilla (Regelwerke im Vergleich)
- /scanner (auffällige Monatsmuster je Ticker)
- /blog/spy-turn-of-month-down-monat-reversal-backtest/ (verwandter Backtest)

#### Content-Ideen (Folgeartikel)
- „TDOM 9–12: Warum die Monatsmitte unterschätzt wird" — Einzeltagsanalyse über mehrere Indizes
- „Monthly 10 auf DAX, Nasdaq und Gold" — hält der Befund außerhalb des S&P 500?
- „Wie viel frisst die Gebühr? 36 Roundturns pro Jahr im Kostentest"
-->

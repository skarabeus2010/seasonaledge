---
title: "Zweig Breadth Thrust: Wie stark ist das Signal wirklich?"
seo_title: "Zweig Breadth Thrust nachgerechnet: 11 Signale seit 1971"
slug: zweig-breadth-thrust-nachgerechnet
date: 2026-10-27
category: education
tags: [marktbreite, breadth-thrust, advance-decline, indikatoren, statistik, sp500]
ticker: ^GSPC
status: published
description: "Zweig Breadth Thrust nachgerechnet: 11 Signale seit 1971, S&P 500 nach 120 Tagen im Mittel +15,7 %. Eine kleine Regeländerung ergibt 7 oder 19 Signale."
---

<!--
Keyword-Plan:
- Haupt-Keyword: Zweig Breadth Thrust (Titel, Description, erster Absatz, H2 „Die Regel")
- Neben-Keywords: Breadth Thrust Signal, Zweig Kaufsignal, Marktbreite Indikator,
  Advance-Decline-Indikator, Martin Zweig Indikator, Breadth Thrust Backtest
- LSI: steigende und fallende Aktien, NYSE, exponentieller gleitender Durchschnitt,
  überverkauft, Basisrate, Definitionsempfindlichkeit, Fallzahl, Signifikanztest
-->

## Elf Signale, elfmal danach höher

Der **Zweig Breadth Thrust** hat seit 1971 in unseren Daten elfmal ausgelöst. 120 Handelstage später stand der S&P 500 in allen elf Fällen höher, im Mittel um **+15,65 %** (Median +13,65 %, n = 11). Über alle 13 832 Handelstage von März 1965 bis Februar 2020 als Startpunkt lag derselbe Zeitraum bei +3,69 %, positiv in 68 % der Fälle.

Das ist die starke Hälfte der Geschichte. Die schwache: Hebt man die untere Schwelle von 0,40 auf 0,41, findet dieselbe Rechnung 14 Signale. Ersetzt man den exponentiellen durch einen einfachen Durchschnitt, sind es 19, und darunter sind Fälle, nach denen der Index deutlich fiel.

Wir haben den Indikator mit NYSE-Daten von 1965 bis 2020 nachgerechnet. Hier steht, was er misst, welche Signale es gab, was der Markt danach tat und wie stark das Ergebnis an der genauen Regel hängt.

## Was der Indikator misst

Der Zweig Breadth Thrust ist ein **Marktbreite-Indikator**. Marktbreite fragt, wie viele Aktien eine Bewegung mittragen, unabhängig davon, wie stark ein Index steigt. Ein S&P 500, der von zehn großen Titeln nach oben gezogen wird, hat eine schmale Breite; ein Markt, in dem fast alles steigt, eine breite.

Gemessen wird an der New York Stock Exchange. Für jeden Handelstag zählt man die Aktien, die gestiegen sind (Advances, A), und die, die gefallen sind (Declines, D). Daraus entsteht der Anteil A/(A+D). Unveränderte Titel bleiben draußen. Der Wert 0,5 heißt: gleich viele Gewinner wie Verlierer.

Weil dieser Tagesanteil stark springt, wird er geglättet: mit einem exponentiellen gleitenden Durchschnitt über zehn Tage (EMA). Ein EMA gewichtet die jüngsten Tage stärker als ältere. Damit gehört er zur Familie der **Advance-Decline-Indikatoren**. Anders als die bekannte kumulierte Advance-Decline-Linie misst er einen Umschwung über wenige Tage.

Der Name geht auf den Investor und Börsenbriefautor Martin Zweig zurück. Oft wird er seinem Buch zugeschrieben; Arthur Hill von StockCharts schreibt, dass er dort nicht steht. Wir lassen die Herkunft deshalb offen.

## Die Regel: von unter 0,40 auf über 0,615 in zehn Tagen {#regel}

Ein „Thrust" ist ein Schub. Gemeint ist der Wechsel von breiter Schwäche zu breiter Stärke in sehr kurzer Zeit. Die Regel, die wir verwenden, hat drei Teile:

- **Überverkauft:** Der 10-Tage-EMA fällt unter 0,40. Dann fallen über längere Zeit deutlich mehr Aktien, als steigen.
- **Schub:** Innerhalb von höchstens zehn Handelstagen nach dem *letzten* Tag unter 0,40 steigt der EMA über 0,615.
- **Neustart:** Nach einem Signal zählt erst ein neues Unterschreiten von 0,40 wieder als Ausgangspunkt.

Das Signal fällt auf den ersten Tag über 0,615. Für die Renditen steigen wir zum Schlusskurs dieses Tages ein und messen den S&P 500 nach 10, 30, 60, 90 und 120 Handelstagen. Der Index ist der Kursindex ohne Dividenden.

![Linienchart von Oktober 2018 bis April 2019: der 10-Tage-EMA des Anteils steigender NYSE-Aktien fällt im Dezember 2018 unter die rote Linie bei 0,40, steigt danach steil an und überschreitet am 7. Januar 2019 die grüne Linie bei 0,615; ein gold hinterlegter Bereich markiert die Zeit vom letzten Tag unter 0,40 bis zum Signal, in Blau dazu der S&P 500 auf der rechten Achse](zweig-breadth-thrust/1_ema_2019_de.png)

Das Beispiel vom Januar 2019 zeigt den typischen Ablauf. Im Dezember 2018 fiel der S&P 500 deutlich, und der Breitenanteil rutschte unter 0,40. Danach drehte der Markt so breit, dass der EMA in wenigen Tagen über 0,615 sprang. Das Signal kam am 7. Januar 2019, also nach dem Tief und nicht davor.

## Elf Signale seit 1971

Unsere Rechnung findet von 1971 bis Februar 2020 elf Signale. Die Tabelle zeigt die S&P-500-Rendite ab Schluss des Signaltags.

| Signal | 10 HT | 30 HT | 60 HT | 90 HT | 120 HT |
|---|---|---|---|---|---|
| 03.12.1971 | +3,3 % | +6,8 % | +9,8 % | +13,5 % | +13,7 % |
| 10.10.1974 | +0,6 % | −2,3 % | +1,8 % | +16,7 % | +16,8 % |
| 03.01.1975 | +0,4 % | +15,3 % | +16,9 % | +29,5 % | +33,8 % |
| 20.08.1982 | +8,5 % | +7,5 % | +21,2 % | +25,0 % | +28,3 % |
| 03.08.1984 | +1,1 % | +4,0 % | +1,5 % | +0,4 % | +8,8 % |
| 25.05.2004 | +1,6 % | −0,0 % | −1,3 % | +2,0 % | +6,4 % |
| 18.03.2009 | +2,1 % | +9,9 % | +19,1 % | +23,6 % | +29,1 % |
| 14.10.2011 | +4,9 % | −2,6 % | +5,5 % | +11,5 % | +12,9 % |
| 18.10.2013 | +1,0 % | +3,2 % | +6,0 % | +6,6 % | +4,1 % |
| 08.10.2015 | +1,9 % | +3,4 % | +0,2 % | −4,7 % | +2,9 % |
| 07.01.2019 | +3,3 % | +9,2 % | +12,7 % | +12,8 % | +15,4 % |

HT = Handelstage. Die Signale von 1974 und 1975 liegen so nah beieinander, dass sich ihre Zeiträume ab 60 Handelstagen überschneiden. Der Kursanstieg von Anfang 1975 steckt also in beiden Zeilen.

Die Liste trifft alle acht Termine, die der Analyst Greg Morris für 1965 bis 2014 veröffentlicht hat. Dazu kommen das Signal vom Mai 2004, das auch Tom McClellan nennt, sowie 2015 und 2019. Die Daten stammen aus dem frei zugänglichen Archiv von unicorn.us.com, das am 10. Februar 2020 eingestellt wurde. Tage ohne Börsenhandel und Zeilen mit null Advances und Declines haben wir entfernt.

## Was der S&P 500 nach dem Signal tat

Ein Mittelwert nach einem Signal sagt wenig, solange man nicht weiß, was der Markt ohnehin tut. Deshalb steht neben jedem Wert die **Basisrate**: dieselbe Rendite, gemessen ab jedem der 13 832 Handelstage von März 1965 bis Februar 2020.

| Horizont | Mittel nach Signal | Median | positiv | Basisrate (Mittel) | Basisrate positiv |
|---|---|---|---|---|---|
| 10 HT | +2,62 % | +1,94 % | 11/11 | +0,31 % | 58 % |
| 30 HT | +4,94 % | +4,02 % | 8/11 | +0,91 % | 61 % |
| 60 HT | +8,48 % | +5,95 % | 10/11 | +1,80 % | 64 % |
| 90 HT | +12,45 % | +12,81 % | 10/11 | +2,72 % | 65 % |
| 120 HT | +15,65 % | +13,65 % | 11/11 | +3,69 % | 68 % |

Signalspalten n = 11, Basisrate n = 13 832 Starttage.

![Balkendiagramm: mittlere S&P-500-Rendite nach elf Breadth-Thrust-Signalen in Gold gegen die Basisrate aller Handelstage 1965–2020 in Grau, für 10, 30, 60, 90 und 120 Handelstage: +2,62 % gegen +0,31 %, +4,94 % gegen +0,91 %, +8,48 % gegen +1,80 %, +12,45 % gegen +2,72 % und +15,65 % gegen +3,69 %; darunter die Zahl der positiven Fälle 11/11, 8/11, 10/11, 10/11 und 11/11](zweig-breadth-thrust/2_renditen_de.png)

Über jeden Horizont liegt das Mittel nach dem Signal beim Vier- bis gut Achtfachen der Basisrate. Am schwächsten ist der 30-Tage-Horizont: dreimal stand der Index dann tiefer (1974, 2004, 2011). Den größten Rückschlag gab es im Oktober 2015 mit −4,7 % nach 90 Handelstagen. Nach 252 Sitzungen, rund einem Börsenjahr, lagen alle elf Fälle im Plus.

Der Einstieg am Signaltag selbst ist eine Vereinfachung, denn wer das Signal erst abends sieht, kauft frühestens am Folgetag. Ab dem Schluss des Folgetags ändert sich wenig: nach 120 Handelstagen +15,51 % im Mittel, weiterhin 11 von 11 positiv.

## Eine Regel, drei Ergebnisse

Die Standardwerte 0,40, 0,615 und zehn Tage sind übernommen, nicht von uns optimiert. Trotzdem lohnt der Blick darauf, wie empfindlich das Ergebnis auf kleine Änderungen reagiert. Wir haben dieselben Daten von 1965 bis 2020 mit sieben Varianten durchgerechnet.

![Balkendiagramm mit der Zahl der Breadth-Thrust-Signale 1965–2020 je Regelvariante: Standard 11, obere Schwelle 0,61 ergibt 13, obere 0,62 ergibt 8, untere 0,39 ergibt 7, untere 0,41 ergibt 14, einfacher statt exponentieller Durchschnitt ergibt 19, Zehn-Tage-Fenster ab dem ersten statt dem letzten Tag unter 0,40 ergibt 7, unveränderte Aktien im Nenner ergeben 3](zweig-breadth-thrust/3_varianten_de.png)

### SMA oder EMA: 11 gegen 19 Signale

Der größte Unterschied entsteht beim Durchschnitt. Mit einem einfachen gleitenden Durchschnitt (SMA) über zehn Tage statt des EMA findet die Rechnung **19 Signale** statt 11. Unter den zusätzlichen sind Fälle, die schlecht ausgingen: nach dem Signal vom September 1973 lag der S&P 500 60 Handelstage später 8,7 % tiefer, nach dem vom Mai 1990 nach 90 Handelstagen 12,2 % tiefer.

### Eine Schwelle um 0,01 verschoben

Die Schwellen sind schmal. Eine obere Schwelle von 0,61 statt 0,615 liefert 13 Signale, 0,62 nur noch 8. Unten ergibt 0,39 sieben Signale und 0,41 vierzehn, darunter eines im Februar 2008, also mitten im Abwärtsmarkt vor der Finanzkrise.

### Wo das Zehn-Tage-Fenster beginnt

Auch die Zählweise des Fensters entscheidet. Beginnt es am *ersten* statt am *letzten* Tag unter 0,40, bleiben 7 Signale. Nimmt man die unveränderten Aktien in den Nenner, also A/(A+D+U), erreicht der EMA die obere Schwelle kaum noch: 3 Signale.

Das erklärt, warum die Zählungen auseinandergehen. Andere Quellen nennen 16, 18 oder 19 Signale seit den 1940er-Jahren, meist ohne genaue Definition und mit anderen Daten. Unsere elf gelten für unsere Regel und unseren Zeitraum und lassen sich mit diesen Zählungen nicht verrechnen.

## 2023 und 2025: Signale außerhalb unserer Daten

Das Archiv, auf dem unsere Rechnung beruht, endet am 10. Februar 2020. Für die Zeit danach haben wir keine Breitendaten derselben Herkunft, und eine andere Quelle würde die Definition still verändern.

Arthur Hill von StockCharts hat Signale im [November 2023](https://articles.stockcharts.com/article/articles-arthurhill-2023-11-the-zweig-breadth-thrust-trigg-609/) und im [April 2025](https://stockcharts.com/articles/arthurhill/2025/04/zweig-breadth-thrust-dominates-460.html) gemeldet. Wir geben sie als Angabe Dritter wieder und rechnen für sie keine eigenen Renditen. Sie stehen nicht in den Tabellen oben.

## Grenzen: elf Fälle, kein Signifikanztest

Elf Signale sind wenig. Zwei davon überschneiden sich (1974 und 1975), die übrigen verteilen sich auf fünf Jahrzehnte mit sehr verschiedenen Märkten. Einen [Signifikanztest](/blog/p-wert-erklaert/) rechnen wir nicht: Bei dieser Fallzahl wäre ein p-Wert Scheingenauigkeit, und die Wahl der Regelvariante hätte mehr Einfluss auf das Ergebnis als der Test selbst.

Das Muster ist ein **Erholungsmuster**. Das Signal setzt voraus, dass der Markt vorher breit gefallen ist, und es kommt erst, wenn die Erholung schon läuft. Gemessen wird also, wie es nach einem Ausverkauf mit kräftiger Gegenbewegung weiterging. Ein ähnliches Bild zeigt unsere Studie zu [Anleihen als Frühindikator](/blog/anleihen-fruehindikator-aktienmarkt/): Auch dort steht vor dem Signal ein Rückgang.

Zwei weitere Einschränkungen: Die Renditen sind reine Kursrenditen ohne Dividenden, und die Basisrate stammt aus überlappenden Zeiträumen. Dass Schwellen und Fenster die Zahl der Signale stark verändern, zeigt außerdem, wie leicht man bei solchen Regeln eine Variante findet, die gut aussieht. Mit 470 Paarungen auf der Seite [Intermarket](/intermarket) haben wir gezeigt, was davon übrig bleibt, wenn man die Zahl der Versuche mitzählt. Ähnlich bei [Bitcoin als Vorlaufindikator](/blog/laeuft-bitcoin-dem-aktienmarkt-voraus/): Dort entschied die Schwelle, ob überhaupt etwas zu sehen war.

Was bleibt: In unserer Definition stand der S&P 500 nach jedem der elf Signale 120 Handelstage später höher, bei einer Basisrate von 68 %. Das beschreibt die Vergangenheit auf kleiner Fallzahl und mit einer Regel, deren Zählung schon bei 0,01 Verschiebung wackelt. Weitere nachgerechnete Börsenregeln stehen in der Übersicht [Elf Börsenregeln nachgerechnet](/blog/boersenregeln-nachgerechnet/).

## Häufige Fragen

### Was ist der Zweig Breadth Thrust?

Ein Marktbreite-Indikator für die NYSE. Er misst den Anteil steigender an allen steigenden und fallenden Aktien und glättet ihn mit einem 10-Tage-EMA. Ein Signal entsteht, wenn dieser Wert innerhalb von zehn Handelstagen von unter 0,40 auf über 0,615 steigt.

### Wie oft gibt es ein Breadth-Thrust-Signal?

Selten. In unseren Daten von 1965 bis Februar 2020 gab es elf Signale, alle ab 1971. Zwischen 1984 und 2004 lagen fast zwanzig Jahre ohne Signal, zwischen 2009 und 2019 kamen fünf.

### Warum nennen Quellen unterschiedlich viele Signale?

Weil die Regel in Details verschieden umgesetzt wird. Ein einfacher statt eines exponentiellen Durchschnitts ergibt in denselben Daten 19 statt 11 Signale, eine untere Schwelle von 0,41 ergibt 14, ein anders gezähltes Zehn-Tage-Fenster 7. Dazu kommen verschiedene Datenquellen und Zeiträume.

### Gab es Fehlsignale?

In unserer Standardregel war der S&P 500 nach 120 Handelstagen in allen elf Fällen höher. Auf kürzeren Horizonten gab es Rückschläge: nach 30 Handelstagen dreimal ein Minus, nach 90 Handelstagen im Oktober 2015 −4,7 %. In der SMA-Variante folgten auf die Signale vom September 1973 und Mai 1990 deutliche Verluste.

### Wann war das letzte Zweig-Breadth-Thrust-Signal?

In unseren Daten am 7. Januar 2019; das Archiv endet im Februar 2020. Arthur Hill von StockCharts meldete später Signale im November 2023 und im April 2025. Für diese beiden rechnen wir keine eigenen Zahlen.

### Ist der Zweig Breadth Thrust ein Kaufsignal?

Nein. Die Zahlen beschreiben, wie sich der S&P 500 nach elf historischen Signalen entwickelt hat. Elf Fälle tragen keine Prognose, und schon kleine Änderungen an der Regel verändern, welche Fälle überhaupt mitzählen.

<!--
#### Social Media Snippet

**LinkedIn:** Der Zweig Breadth Thrust gilt als eines der seltensten Kaufsignale. Wir haben ihn mit NYSE-Daten 1965–2020 nachgerechnet: 11 Signale seit 1971, S&P 500 nach 120 Handelstagen in allen 11 Fällen höher, im Mittel +15,65 % (Basisrate +3,69 %). Aber: SMA statt EMA ergibt 19 Signale, Schwelle 0,41 statt 0,40 ergibt 14. Wie viel ist ein Signal wert, dessen Zählung an der zweiten Nachkommastelle hängt? https://seasonalpha.ai/blog/zweig-breadth-thrust-nachgerechnet/

**Twitter/X:** Zweig Breadth Thrust nachgerechnet: 11 Signale seit 1971, S&P 500 nach 120 HT 11/11 höher, Ø +15,65 % (n=11). SMA statt EMA: 19 Signale. Untere Schwelle 0,41: 14. #Börse #Marktbreite #SeasonAlpha

#### Interne Verlinkung
- /blog/p-wert-erklaert/ (Signifikanztest)
- /blog/boersenregeln-nachgerechnet/ (Übersicht)
- /blog/anleihen-fruehindikator-aktienmarkt/ (Erholungsmuster)
- /blog/laeuft-bitcoin-dem-aktienmarkt-voraus/ (Schwellenabhängigkeit)
- /intermarket (multiples Testen)

#### Content-Ideen (Folgeartikel)
- Marktbreite heute: eigene Advance-/Decline-Daten ab 2020 aufbauen und die Signale 2023/2025 nachrechnen
- Weitere Breitenindikatoren (McClellan Oscillator, Anteil über 200-Tage-Linie) mit derselben Basisraten-Methodik
- Larry-Williams-Indikatoren nachgerechnet (Fortsetzung der Indikatoren-Reihe)
-->

---
title: "Anleihen als Frühindikator für Aktien? Nur im Stress — 50 Fälle seit 2002"
seo_title: "Anleihen als Frühindikator? Nur im Stress, 50 Fälle"
slug: anleihen-fruehindikator-aktienmarkt
date: 2026-09-22
category: education
tags: [anleihen, tlt, spy, lead-lag, volatilitaet, intermarket]
description: "Flucht in langlaufende Staatsanleihen und der S&P 500 danach: 50 Fälle seit 2002 ergeben +2,09 % in zwei Wochen — aber nur in unruhigen Marktphasen."
ticker: TLT
status: published
---

<!--
Keyword-Plan:
- Haupt-Keyword: Anleihen Frühindikator Aktienmarkt
- Neben-Keywords: TLT SPY Zusammenhang, Staatsanleihen und Aktien, Flucht in Anleihen, Lead-Lag-Analyse Anleihen, langlaufende Staatsanleihen Signal, Anleihen Aktien Korrelation, realisierte Volatilität Regime, Ereignisstudie S&P 500
- LSI: Basisrate, Trefferquote, p-Wert, Zufallsverschiebung, Max-T, Duration, Risikoabbau, Erholung, Stressphase
-->

## Die Vermutung, die dahintersteckt

Der Anleihemarkt gilt als der ältere und nüchternere der beiden Märkte. Wenn Kapital in langlaufende Staatsanleihen fließt, so die verbreitete Lesart, preisen die Anleihe-Anleger eine Abkühlung ein, die der Aktienmarkt erst später versteht. Daraus wird schnell die These: Anleihen sind ein Frühindikator für den Aktienmarkt.

Diese These ist prüfbar, weil sie eine zeitliche Abfolge behauptet. Wir haben sie an 6075 gemeinsamen Handelstagen gemessen. Herausgekommen ist ein Befund, aber ein deutlich engerer als die These verlangt.

## Was gemessen wurde

Datenbasis sind die Tagesschlusskurse von TLT (ETF auf US-Staatsanleihen mit über 20 Jahren Restlaufzeit) und SPY (ETF auf den S&P 500), vom 30.07.2002 bis zum 21.09.2026.

Als Signal gilt ein **TLT-Kursanstieg von mindestens 4,1 % über 10 Handelstage**. Die Schwelle stammt aus der Verteilung selbst: 4,1 % ist das 90. Perzentil aller TLT-Bewegungen dieser Länge, also die stärksten zehn Prozent. In 24 Jahren trifft das auf **50 Ereignisse** zu, die jeweils mindestens 41 Handelstage auseinanderliegen, damit nicht eine einzelne Marktphase mehrfach gezählt wird.

Gemessen wird, was SPY **nach** dem Signal macht, verglichen mit dem, was der Markt über dieselben Zeiträume ohne jedes Signal ohnehin tut. Diese Basisrate liegt bei +0,24 % nach einer Woche, +0,48 % nach zwei, +0,72 % nach drei und +0,95 % nach vier Wochen.

Das methodische Gerüst (Basisrate, Zufallsverschiebungen, p-Wert) ist im [ersten Teil dieser Serie zu Bitcoin](/blog/laeuft-bitcoin-dem-aktienmarkt-voraus/) ausführlich erklärt. Der Code liegt in `scripts/research/bond_lead_lag.py` und `bond_kontrollen.py`.

## Der Rohbefund

| SPY nach dem Signal | Ergebnis | p | Basisrate ohne Signal |
|---|---:|---:|---:|
| 1 Woche | **+1,80 %** | 0,001 | +0,24 % |
| 2 Wochen | **+2,09 %** | 0,001 | +0,48 % |
| 3 Wochen | **+2,12 %** | 0,005 | +0,72 % |
| 4 Wochen | **+2,85 %** | 0,001 | +0,95 % |

Das Ergebnis liegt über alle vier Horizonte beim Zwei- bis Siebenfachen der Basisrate, und die p-Werte bleiben durchgehend unter 0,01. Die Trefferquote steigt von 65,7 % auf **74,0 %**, sie bewegt sich also mit. Im Bitcoin-Teil war genau das nicht der Fall: dort kam der Mehrertrag aus wenigen großen Einzelfällen, während die Trefferquote auf Marktniveau blieb.

An dieser Stelle hätte man den Artikel schreiben können, den die Überschrift nahelegt. Die Kontrollrechnungen sagen etwas anderes.

## Die Bedingung, die alles ändert: das Marktumfeld

![Zwei Balkendiagramme: links der S&P 500 zwei Wochen nach einem starken Anstieg langlaufender Staatsanleihen, getrennt nach ruhigen Phasen (+0,53 %, p = 0,935, n = 25) und unruhigen Phasen (+3,65 %, p unter 0,001, n = 25), dazu die gestrichelte Linie des Marktdurchschnitts bei +0,48 %; rechts dieselbe Messung in den Zeiträumen 2003-2019 (+1,72 %) und 2020-2025 (+2,87 %)](anleihen-fruehindikator-aktienmarkt/1_regime.png)

Die 50 Ereignisse wurden am Median der realisierten Volatilität des S&P 500 am Ereignistag geteilt, also danach, wie stark der Aktienmarkt in dieser Phase ohnehin schwankte. Der Median liegt bei 13,9 % annualisiert.

In den **25 ruhigen Fällen** kommt SPY zwei Wochen später auf **+0,53 %** bei p = 0,935. Die Basisrate beträgt +0,48 %. Das Signal trägt in ruhigen Phasen also nichts bei.

In den **25 unruhigen Fällen** sind es **+3,65 %** bei p < 0,001, mit einer Trefferquote von 80 %. Der gesamte Befund steckt in dieser Hälfte.

Der Mittelwert über alle 50 Fälle (+2,09 %) ist damit ein Durchschnitt aus einem starken und einem leeren Zustand. Wer ihn ohne die Aufteilung zitiert, beschreibt eine Größe, die so in keiner der beiden Marktlagen auftritt.

## Warum solche Kontrollen nötig sind

Starke Anleihebewegungen häufen sich in unruhigen Phasen. In unruhigen Phasen sind Aktienrenditen anders verteilt: die Ausschläge sind größer, und nach scharfen Rücksetzern sind Erholungen entsprechend kräftiger. Ein Signal, das bevorzugt in solchen Phasen auslöst, erbt diese Eigenschaft, ohne selbst Information zu tragen.

Die zweite Kontrolle betrifft den Verlauf von SPY **vor** dem Ereignis. Wäre der Aktienmarkt vorher ohnehin gelaufen, könnte der gemessene Vorlauf schlicht Momentum sein. Aufgeteilt nach dem vorangegangenen SPY-Verlauf ergibt sich:

| Teilmenge (2 Wochen, Basisrate +0,48 %) | n | SPY danach | p | Treffer |
|---|---:|---:|---:|---:|
| alle Ereignisse | 50 | +2,09 % | < 0,001 | 74 % |
| schwacher SPY-Vorlauf | 25 | **+2,68 %** | 0,004 | 76 % |
| starker SPY-Vorlauf | 25 | +1,50 % | 0,099 | 72 % |
| ruhige Phasen | 25 | +0,53 % | 0,935 | 68 % |
| unruhige Phasen | 25 | **+3,65 %** | < 0,001 | 80 % |

Die Momentum-Erklärung scheidet damit aus, allerdings mit umgekehrtem Vorzeichen zur Erwartung: Der Effekt ist nach **schwachem** Vorlauf größer (+2,68 %, p = 0,004) und nach starkem Vorlauf nicht mehr signifikant (+1,50 %, p = 0,099).

## Was vor dem Signal passiert

![Ereignispfad des S&P 500 von zehn Handelstagen vor bis 30 Handelstage nach einem TLT-Kursanstieg ab 4,1 Prozent, normiert auf den Ereignistag, n = 50: die goldene Mittellinie fällt vor dem Ereignis von rund plus 2 Prozent auf null und steigt danach auf etwa plus 2,6 Prozent, oberhalb des blauen Zufallsbands aus dem 5. bis 95. Perzentil](anleihen-fruehindikator-aktienmarkt/2_pfad.png)

Der Chart zeigt den mittleren SPY-Verlauf von zehn Handelstagen vor bis 30 Handelstage nach dem Ereignis, normiert auf den Ereignistag. Das blaue Band ist der Korridor vom 5. bis 95. Perzentil aus zufällig verschobenen Terminen, also die Spanne, in der ein beliebiges Zeitfenster landet.

Die linke Hälfte des Bildes ist die wichtigere. In den zehn Handelstagen vor dem Signal ist der S&P 500 im Median um **1,33 %** gefallen (Mittel −1,75 %, in 62 % der Fälle negativ). Die Flucht in langlaufende Staatsanleihen setzt am Ende eines Rücksetzers ein, nicht in einem ruhigen Aktienmarkt.

Damit ändert sich die Beschreibung des Befunds. Gemessen wurde ein Erholungsmuster nach Kursverlusten in nervösen Marktphasen, kein Signal, das aus heiterem Himmel eine Aufwärtsbewegung ankündigt. Rechts vom Ereignistag verlässt die Mittellinie das Zufallsband nach oben und bleibt dort, die Erholung ist also größer als das, was zufällig gewählte Zeitfenster liefern.

## Die Gegenrichtung liefert nichts

Fällt TLT stark, steigen die langen Renditen. Wäre der Anleihemarkt ein allgemeiner Frühindikator, müsste sich auch in dieser Richtung etwas zeigen, mit umgekehrtem Vorzeichen.

Es zeigt sich nichts. Über alle getesteten Schwellen und alle vier Horizonte liegen die p-Werte zwischen **0,29 und 0,97**. Kein einziger Wert kommt in die Nähe einer Signifikanzschwelle.

Diese Asymmetrie passt zur Stress-Lesart: Ein kräftiger Anstieg langlaufender Anleihen ist typischerweise ein Risikoabbau unter Druck, ein Rückgang dagegen meistens eine ruhige Zinsanpassung.

## Beide Zeiträume, und der Preis des Ausprobierens

Der Zeitraum wurde vorab am offensichtlichen Bruch geteilt: 2003-2019 gegen 2020-2025. Nicht dort, wo das Ergebnis am schönsten aussieht.

Vor 2020 liegt SPY zwei Wochen nach dem Signal bei **+1,72 %** (n = 34, p = 0,019, Treffer 65 %), ab 2020 bei **+2,87 %** (n = 16, p = 0,008, Treffer 94 %). Der Befund existiert in beiden Hälften. Die zweite Hälfte ist mit 16 Fällen dünn besetzt, und eine Trefferquote von 94 % bei dieser Fallzahl sollte man nicht als eigene Zahl lesen.

Bleibt die Frage, wie viel das viele Testen kostet. Geprüft wurden vier Schwellen, zwei Richtungen, zwei Signalgeber und vier Horizonte, zusammen **64 Kombinationen**. Der kleinste Einzel-p-Wert aus so einer Familie sagt wenig, weil bei 64 Versuchen auch reiner Zufall Treffer produziert. Der Max-T-Test fragt stattdessen, wie oft der *beste* Zufallstreffer aus einer gleich großen Familie das beobachtete Niveau erreicht. Ergebnis: **p = 0,018**. Das ist die strengste Zahl der ganzen Studie, und sie hält.

## Grenzen

**TLT ist ein Kurs, keine Rendite.** Der Zusammenhang zur Anleiherendite ist invers und eng, aber der ETF-Kurs enthält auch Duration-Effekte und das Rebalancing des zugrundeliegenden Index. Deshalb steht hier durchgehend "TLT-Kursanstieg". Die langen Renditen fielen in diesen Phasen tendenziell, gemessen wurde aber der Kurs.

**Zeitliche Abfolge ist keine Ursache.** Beide Märkte reagieren auf dieselben Makro-Impulse. Die Studie misst die Abfolge, die Ursache bleibt offen.

**Das Signal ist selten.** 50 Fälle in 24 Jahren sind etwa zwei pro Jahr, und die Hälfte davon fällt in ruhige Phasen, in denen nichts folgt.

**In ruhigen Phasen ist der Effekt null.** +0,53 % bei p = 0,935 gegen eine Basisrate von +0,48 % ist kein schwaches Ergebnis, sondern praktisch die Basisrate. Wer das Signal ohne Blick auf das Marktumfeld liest, liest Rauschen.

**Die Schwelle stammt aus den Daten, nicht aus einer runden Zahl.** Gerechnet wird mit dem exakten 90. Perzentil der TLT-Bewegungsverteilung (0,040632), im Text steht der gerundete Wert 4,1 %.

**Ex-Dividenden-Tage.** Die verwendeten Kursreihen tragen an Ex-Tagen einen kleinen künstlichen Abschlag. Bei Vier-Wochen-Fenstern betrifft das etwa einen Tag und verzerrt leicht nach unten.

## Was daraus folgt

Die Ausgangsthese hält in ihrer allgemeinen Form nicht. Ein starker Anstieg langlaufender Staatsanleihen kündigt keine Aktienbewegung an. Er beschreibt einen Zustand: Risikoabbau unter Druck, nach einem Rücksetzer, in einem nervösen Markt. In genau dieser Konstellation fiel die Erholung des S&P 500 historisch überdurchschnittlich aus, in jeder anderen nicht.

Verglichen mit dem [Bitcoin-Teil dieser Serie](/blog/laeuft-bitcoin-dem-aktienmarkt-voraus/) ist das der stärkere Befund. Dort blieb nur bei sehr großen Krypto-Bewegungen ab 20 % etwas übrig, die verbreitete 5-Prozent-These fiel durch, und die Trefferquote bewegte sich nicht. Hier bewegt sie sich, der Effekt hält in beiden Teilperioden und übersteht die Max-T-Korrektur. Der Preis dafür ist die Bedingung: ohne das Stress-Regime bleibt nichts übrig.

Angrenzende Fragestellungen lassen sich auf SeasonAlpha direkt nachschauen: [Intermarket-Schocks](/intermarket-shocks) behandelt die Übertragung zwischen Märkten, der [Risikozyklus](/risikozyklus) zeigt die Risikoneigung über den Jahresverlauf.

**Kein Signal:** Was hier steht, ist eine Messung an historischen Kursen, keine Handelsregel und keine Aussage über künftige Kurse.

## Häufige Fragen

### Sind Anleihen ein Frühindikator für den Aktienmarkt?

In der allgemeinen Form nach diesen Daten nicht. Ein TLT-Kursanstieg ab 4,1 % über 10 Handelstage geht zwar im Mittel mit einer überdurchschnittlichen Erholung des S&P 500 einher (+2,09 % in zwei Wochen gegen +0,48 % Basisrate), aber der gesamte Effekt steckt in den unruhigen Marktphasen. In ruhigen Phasen liegt das Ergebnis mit +0,53 % bei p = 0,935 praktisch auf der Basisrate.

### Was heißt "nur im Stress" konkret?

Die 50 Ereignisse wurden am Median der realisierten Volatilität des S&P 500 am Ereignistag geteilt, dieser liegt bei 13,9 % annualisiert. Oberhalb davon kommt SPY zwei Wochen später auf +3,65 % (p < 0,001, Trefferquote 80 %), unterhalb auf +0,53 % (p = 0,935).

### Gilt der Zusammenhang auch umgekehrt, wenn Anleihen fallen?

Nein. Bei fallendem TLT, also steigenden langen Renditen, liegen die p-Werte über alle Schwellen und Horizonte zwischen 0,29 und 0,97. In dieser Richtung ist kein Muster messbar.

### Warum ist das eine Erholung und keine Vorhersage?

Weil der S&P 500 vor dem Signal gefallen ist: in den zehn Handelstagen davor im Median um 1,33 % (Mittel −1,75 %, in 62 % der Fälle negativ). Das Signal markiert damit das Ende eines Rücksetzers, nicht den Beginn einer Bewegung aus der Ruhe heraus.

### Wie oft tritt das Signal auf?

50 Mal in 24 Jahren, also rund zwei Mal pro Jahr. Ereignisse liegen mindestens 41 Handelstage auseinander, damit eine einzelne Marktphase nicht mehrfach in die Rechnung eingeht.

<!--
#### Social Media Snippet

**LinkedIn:**
„Anleihen sind der Frühindikator für Aktien" — wir haben die These an 6075 gemeinsamen Handelstagen seit 2002 gemessen (TLT gegen SPY).
Rohbefund: nach einem TLT-Kursanstieg ab 4,1 % über 10 Handelstage steht der S&P 500 zwei Wochen später bei +2,09 % statt bei den üblichen +0,48 %, 50 Fälle, p = 0,001.
Die Kontrollen engen das ein: In ruhigen Phasen +0,53 % bei p = 0,935, in unruhigen +3,65 % bei p < 0,001. Und der S&P 500 ist vor dem Signal im Median um 1,33 % gefallen. Es ist ein Erholungsmuster im Stress, keine Prophezeiung.
Die Gegenrichtung (TLT fällt) zeigt gar nichts: p zwischen 0,29 und 0,97.
Welche Intermarket-Regel sollen wir als nächstes prüfen? → seasonalpha.ai

**Twitter/X:**
Sind Anleihen ein Frühindikator für Aktien? 6075 Handelstage seit 2002:
TLT +4,1 % in 10 Tagen → SPY 2 Wochen später +2,09 % (Basisrate +0,48 %).
Aber: ruhige Phasen +0,53 % (p=0,935), unruhige +3,65 % (p<0,001).
Und SPY war vorher schon gefallen. Erholung, keine Prognose.
#Anleihen #Börse #SeasonAlpha

#### Interne Verlinkung
- /blog/laeuft-bitcoin-dem-aktienmarkt-voraus/ (Teil 1 der Serie, Methodik)
- /intermarket-shocks (Übertragung zwischen Märkten)
- /risikozyklus (Risikoneigung im Jahresverlauf)
- /crash-fruehwarnung (Volatilitätsregime als Kontext)

#### Content-Ideen (Folgeartikel)
- „Der VIX als Filter: dieselbe Messung mit einem anderen Stress-Maß"
- „Gold, Kupfer, Anleihen: welcher Markt dreht wirklich zuerst?" — gleiche Methodik über mehrere Assets
- „Was der Zinsanstieg 2022 mit dem TLT-Signal gemacht hat" — Teilperioden im Detail
-->

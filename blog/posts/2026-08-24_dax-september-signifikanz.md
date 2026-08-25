---
title: "DAX im September: statistisch signifikant schwach — der Signifikanztest erklärt"
seo_title: "DAX September: signifikant schwach (Test erklärt)"
slug: dax-september-signifikanz
date: 2026-08-24
category: education
tags: [dax, september-effekt, signifikanztest, t-test, p-wert, saisonalitaet]
description: "Ist der DAX im September wirklich signifikant schwach? Ø −1,55 %, p=0,0241 — und wie t-Test, p-Wert und Effektstärke echten Effekt von Zufall trennen."
ticker: ^GDAXI
status: published
---

<!--
Keyword-Plan:
- Haupt-Keyword: DAX September signifikant
- Neben-Keywords: September-Effekt DAX, ist der DAX im September schwach, Signifikanztest Saisonalität erklärt, t-Test p-Wert Börse, DAX September Statistik, statistisch signifikant Monatsrendite
- LSI: Nullhypothese, Cohen's d, Effektstärke, Win-Rate, Relevance-Score, multiples Testen, normalisierte Renditen, Zufall vs. echter Effekt
-->

## Negativ ist nicht gleich signifikant

Der DAX verliert im September historisch im Schnitt **1,55 %** — der mit Abstand schwächste Kalendermonat. Doch die eigentlich interessante Frage lautet nicht „Wie negativ?", sondern „Ist das echt oder Zufall?". Genau hier liegt der Unterschied: Der September ist der **einzige** DAX-Monat, der statistisch signifikant **negativ** ist (p=0,0241). Dieser Artikel zeigt an echten Zahlen, **wie** ein Signifikanztest zu diesem Urteil kommt — und warum „signifikant" mehr aussagt als „im Schnitt im Minus".

## Wie stark ist der September-Effekt beim DAX?

Datenbasis ist der DAX (^GDAXI) über den maximal verfügbaren Zeitraum: eine zurückgerechnete Reihe seit den späten 1950er-Jahren, **n=68 Beobachtungen** je Kalendermonat. Wir rechnen mit **normalisierten Renditen** — jeder Monat startet rechnerisch bei 100, die täglichen Returns kumulieren darauf. So sind lange und kurze Monate über 68 Jahre vergleichbar, ohne dass alte hohe Punktestände die jüngeren verzerren.

Der folgende Chart ordnet alle zwölf Monate nach durchschnittlicher Rendite. Der September steht allein am unteren Ende.

![^GDAXI — Monats-Performance (Ø, n=68): der September ist mit −1,55 % der mit Abstand schwächste Monat](dax-september-signifikanz/dax-monatsperformance.png)

Der September verliert im Schnitt 1,55 %. Zum Vergleich: Juni und August sind ebenfalls negativ, aber nur mit −0,27 % und −0,24 % — ein Zehntel der September-Schwäche. Auf der anderen Seite stehen November (+1,56 %), April (+1,35 %) und Dezember (+1,07 %) als kräftigste Monate.

Ein niedriger Durchschnitt allein ist jedoch schwach als Beleg. Entscheidend ist, ob der Wert stabil aus vielen Jahren kommt oder von wenigen Ausreißern getragen wird. Beim September stützt die **Win-Rate** das Bild: Nur in **37 %** der 68 Jahre schloss er positiv — der schlechteste Wert aller Monate.

## Der Signifikanztest — Schritt für Schritt

Um Zufall von echtem Muster zu trennen, nutzt SeasonAlpha einen **t-Test für eine Stichprobe**. Die Idee ist simpel: Wir prüfen, ob der Monats-Mittelwert glaubwürdig von null abweicht — oder ob null gut ins Streuband der Jahre passt.

### Nullhypothese und t-Wert

Die **Nullhypothese (H0)** lautet: „Die durchschnittliche September-Rendite ist in Wahrheit null, jede Abweichung ist Rauschen." Der **t-Wert** misst, wie weit der beobachtete Mittelwert von null entfernt liegt — gemessen in Einheiten der Streuung. Er setzt das Signal (der Mittelwert) ins Verhältnis zum Lärm (die Schwankung zwischen den Jahren, geteilt durch die Wurzel aus n).

Ein großer Betrag beim t-Wert heißt: klares Signal, wenig Lärm. Für den September ergibt sich **t=−2,31**. Das Minus zeigt die Richtung (unterdurchschnittlich), der Betrag von 2,31 die Stärke.

### Der p-Wert und die Schwelle ±1,96

Der **p-Wert** übersetzt den t-Wert in eine Wahrscheinlichkeit: Wie oft würde man ein so extremes Ergebnis rein zufällig sehen, wenn es in Wahrheit gar keinen September-Effekt gibt? Für den September liegt er bei **p=0,0241** — also rund 2,4 %. Die Konvention: **p unter 0,05 gilt als signifikant.**

Bei etwa 68 Beobachtungen entspricht die 5-%-Grenze einem t-Wert von rund **±1,96**. Alles jenseits dieser Schwelle ist signifikant. Der folgende Chart zeigt jeden Monat als t-Balken mit genau diesen ±1,96-Linien.

![^GDAXI — t-Statistik je Monat mit Signifikanz-Schwelle ±1,96: nur September, April und November überschreiten sie](dax-september-signifikanz/dax-t-statistik.png)

Nur drei Monate durchbrechen die Schwelle: **September (−2,31)** nach unten, **April (+2,18)** und **November (+2,56)** nach oben. Alle anderen bleiben im neutralen Band — ihre Mittelwerte sind mit reinem Zufall vereinbar.

### Cohen's d und der Relevance-Score

Signifikanz sagt, **ob** ein Effekt existiert — nicht, wie **groß** er ist. Dafür gibt es **Cohen's d**, die Effektstärke: der Mittelwert geteilt durch die Standardabweichung. Ein kleines d heißt, der Effekt verschwindet fast in der normalen Monatsschwankung; ein großes d heißt spürbarer Unterschied.

SeasonAlpha fasst beides in einem **Relevance-Score** zusammen, einem Wert zwischen 0 und 1:

> Relevance = 50 % · (1 − p) + 30 % · Win-Rate + 20 % · min(Cohen's d, 1)

Der Score belohnt drei Dinge gleichzeitig: statistische Sicherheit (niedriges p), Trefferquote und Effektgröße. Der September erreicht **0,65** — trotz seiner negativen Richtung ein hoher Wert, weil Signifikanz und deutliche Fehlquote zusammenkommen.

## Die vollständige Monatstabelle

Die folgende Tabelle listet alle zwölf Monate mit Durchschnittsrendite, t-Wert, p-Wert, Win-Rate, Relevance-Score und Urteil. Signifikant sind nur die Monate mit p unter 0,05.

| Monat | Ø-Rendite | t-Wert | p-Wert | Win-Rate | Relevance | Urteil |
|-------|-----------|--------|--------|----------|-----------|--------|
| Januar | +1,00 % | 1,51 | 0,1345 | 54 % | 0,63 | Nicht signifikant |
| Februar | +0,31 % | 0,52 | 0,6033 | 54 % | 0,37 | Nicht signifikant |
| März | +1,03 % | 1,78 | 0,0796 | 65 % | 0,70 | Borderline |
| April | **+1,35 %** | **2,18** | **0,0331** | 59 % | 0,71 | **Signifikant** |
| Mai | +0,31 % | 0,51 | 0,6103 | 53 % | 0,37 | Nicht signifikant |
| Juni | −0,27 % | −0,47 | 0,6408 | 43 % | 0,32 | Nicht signifikant |
| Juli | +1,01 % | 1,59 | 0,1155 | 59 % | 0,66 | Nicht signifikant |
| August | −0,24 % | −0,34 | 0,7334 | 53 % | 0,30 | Nicht signifikant |
| September | **−1,55 %** | **−2,31** | **0,0241** | 37 % | 0,65 | **Signifikant** |
| Oktober | +0,70 % | 0,86 | 0,3943 | 53 % | 0,48 | Nicht signifikant |
| November | **+1,56 %** | **2,56** | **0,0128** | 65 % | 0,75 | **Signifikant** |
| Dezember | +1,07 % | 1,90 | 0,0619 | 59 % | 0,69 | Borderline |

Der September ist der **einzige signifikant negative** Monat. April und November sind signifikant positiv, März und Dezember liegen knapp über der Schwelle (Borderline). Damit ergibt sich ein kohärentes Bild: schwacher Herbstauftakt, kräftiger Jahresausklang und ein starker April im Frühjahr.

### Warum Juni und August nicht zählen

Juni (−0,27 %) und August (−0,24 %) sind ebenfalls negativ — aber mit p=0,6408 und p=0,7334 meilenweit von Signifikanz entfernt. Ihre Mittelwerte könnten genauso gut null sein; das Minus ist gut mit reinem Zufall erklärbar. Der September ist die Ausnahme: negativ **und** belastbar. Genau diesen Unterschied macht der Test sichtbar — er verhindert, dass man aus jedem zufällig roten Balken eine Regel bastelt.

## Grenzen — ehrlich betrachtet

Ein Signifikanztest ist ein Werkzeug, kein Orakel. Drei Einschränkungen gehören zwingend dazu.

**Multiples Testen.** Wir prüfen zwölf Monate. Bei einer 5-%-Schwelle würde man rein zufällig etwa **einen** falsch-positiven Treffer erwarten. Dass der September (p=0,024) mit einer plausiblen Erzählung zusammenfällt **und** weitere kohärente Monate signifikant sind (November und April positiv), stützt den Befund. Ein einzelner signifikanter Monat für sich genommen wäre aber kein Beweis.

**Datenqualität.** Die älteren Jahrzehnte der zurückgerechneten DAX-Reihe stammen aus weniger liquiden, teils rekonstruierten Kursen. Sie sind nicht mit der heutigen Marktstruktur identisch. „In der Vergangenheit signifikant" ist zudem keine Zusage für den nächsten September — bekannte saisonale Effekte werden mit der Zeit teils weggehandelt.

**Kausalität.** Warum gerade der September schwach ist, lässt sich nicht sauber beweisen. Als Kontext werden Umschichtungen nach der Sommerpause und eine historische Häufung von Krisen im Herbst genannt. Das sind Erzählungen, keine belegten Ursachen. Der Test misst ein Muster, nicht dessen Grund.

## Praxisbezug — was Anleger damit anfangen

Saisonalität liefert **Kontext**, kein Handelssignal. Die September-Schwäche erklärt, warum sich der DAX zum Herbstauftakt oft zäh anfühlt — ein Grund, ruhig zu bleiben statt nervös zu reagieren. Für aktive Trader ist eher die Asymmetrie interessant: Ein Monat mit 37 % Trefferquote hat ein anderes Chance-Risiko-Profil als der November mit 65 %.

Den Signifikanztacho mit t-Wert, p-Wert, Win-Rate und Relevance-Score gibt es in SeasonAlpha für jeden Ticker und jeden Zeitindex. Den interaktiven [Monatszyklus](/monatszyklus) kannst du selbst durchklicken. Wie wir Daten prüfen und Signifikanz berechnen, steht offen auf der [Methodik-Seite](/ueber-uns). Wer den breiten Vergleich aller Monate über die offizielle Index-Historie sucht, findet ihn in unserer Studie zum [schlechtesten DAX-Monat](/blog/schlechtester-dax-monat-saisonalitaet/).

## Fazit

Der DAX ist im September nicht nur im Schnitt schwach (−1,55 %), sondern als einziger Monat auch statistisch signifikant negativ (t=−2,31, p=0,0241). Der Signifikanztest trennt dieses Muster sauber von der zufälligen Schwäche in Juni und August. Signifikanz ist dabei kein Beweis für die Zukunft — aber sie zeigt, welche saisonalen Auffälligkeiten es wert sind, ernst genommen zu werden. Teste den Signifikanztacho selbst auf [seasonalpha.ai](https://seasonalpha.ai/monatszyklus).

## Häufige Fragen

### Ist der DAX im September wirklich signifikant schwach?
Ja. Über 68 Jahre verliert der DAX im September im Schnitt 1,55 % bei einem t-Wert von −2,31 und p=0,0241. Da p unter der 5-%-Schwelle liegt, gilt der Effekt als statistisch signifikant — der einzige signifikant negative Monat im Jahr.

### Was bedeutet ein p-Wert von 0,05 an der Börse?
Der p-Wert ist die Wahrscheinlichkeit, ein so extremes Ergebnis rein zufällig zu sehen, wenn es keinen echten Effekt gibt. Ein p unter 0,05 heißt: unter 5 % Zufallswahrscheinlichkeit — üblich als Grenze für „signifikant". Beim DAX-September sind es rund 2,4 %.

### Warum sind Juni und August nicht signifikant, obwohl sie negativ sind?
Weil ihr Minus winzig (−0,27 % bzw. −0,24 %) und statistisch nicht belastbar ist: p=0,64 und p=0,73 liegen weit über 0,05. Ihre Mittelwerte sind mit reinem Zufall vereinbar, während der September deutlich aus dem Rauschen heraussticht.

### Kann ich mich auf den September-Effekt verlassen?
Nein. Signifikanz in der Vergangenheit garantiert kein negatives Ergebnis im nächsten September. Multiples Testen, weniger liquide Altdaten und das Wegtraden bekannter Effekte begrenzen die Aussagekraft. Nutze das Muster als Kontext, nicht als Handelssignal.

<!--
#### Social Media Snippet

**LinkedIn:** Der DAX ist im September nicht nur im Schnitt schwach (−1,55 %) — er ist der einzige Monat, dessen Schwäche statistisch signifikant ist (p=0,0241). Juni und August sind auch negativ, aber reines Rauschen (p=0,64 / 0,73). Wir zeigen an echten Zahlen, wie t-Test, p-Wert und Effektstärke einen echten Effekt vom Zufall trennen. 📉 Welcher Monat überrascht dich? Charts + Signifikanztacho: seasonalpha.ai

**Twitter/X:** DAX im September: Ø −1,55 %, t=−2,31, p=0,0241 → statistisch signifikant. Der EINZIGE signifikant negative Monat. Juni/August auch negativ, aber reines Rauschen. So funktioniert der Signifikanztest 👇 #Börse #DAX #Statistik #SeasonAlpha

#### Interne Verlinkung
- /blog/schlechtester-dax-monat-saisonalitaet/ (breiter Vergleich aller Monate, 38 Jahre)
- /monatszyklus (interaktiver Monatszyklus + Signifikanztacho je Ticker)
- /ueber-uns (Methodik, Signifikanzberechnung)

#### Content-Ideen (Folgeartikel)
- "Cohen's d verständlich: Wie groß ist ein Saisonalitäts-Effekt wirklich?"
- "Multiples Testen an der Börse: Warum ein signifikanter Monat kein Beweis ist"
- "April und November: Die zwei signifikant starken DAX-Monate im Detail"
-->

---
title: "Ist der Effekt echt? Der p-Wert an sechs eigenen Messungen"
seo_title: "p-Wert verstehen: signifikant heisst nicht profitabel"
slug: p-wert-erklaert
date: 2026-09-22
category: education
tags: [statistik, signifikanz, backtest, methodik, p-wert, saisonalitaet]
ticker: SPY
status: published
description: "p = 0,127 heisst nicht „kein Effekt\", p = 0,0050 nicht „handelbar\". Der p-Wert erklärt an eigenen Studien, dazu multiples Testen und ein eigener Fehler."
---

<!--
Keyword-Plan:
- Haupt-Keyword: Backtest Signifikanz
- Neben-Keywords: statistisch signifikant Börse, Saisonalität Zufall oder Effekt,
  Signifikanzniveau 0,05 Bedeutung, multiples Testen Data Mining Börse,
  Effektstärke vs. Signifikanz, Permutationstest Bootstrap Unterschied
- LSI: Nullhypothese, Nullverteilung, Kontrollgruppe, Stichprobengrösse,
  Überoptimierung, Data Snooping, Konfidenzintervall, Trefferquote
- Positionierung: NICHT das Kopf-Keyword „p-Wert erklärt" (gehört den
  Statistik-Lehrportalen und bringt Hausarbeiten-Traffic). Die Mechanik
  (t-Wert, Schwelle ±1,96, Cohen's d) steht in dax-september-signifikanz und
  wird hier NICHT wiederholt, sondern verlinkt.
- Stabile Anker für Deep-Links aus anderen Artikeln: #p-0-0050, #p-0-127,
  #p-0-935, #p-0-0241, #multiples-testen, #bootstrap-oder-permutation
-->

## Der Satz, der alles Weitere erklärt

**0,35 Prozentpunkte bei p = 0,0050.** Das ist unser am besten belegter Einzelbefund zum Optionsverfall — signifikant, über 41.203 Beobachtungen und 30 Jahre gemessen — und so klein, dass für Spread und Gebühren kaum etwas übrig bleibt.

Wer aus „signifikant" auf „handelbar" schliesst, hat diesen Fall nicht gesehen. Und weil auf dieser Seite auf praktisch jeder Studienseite ein p-Wert steht, gehört einmal ausbuchstabiert, was dort eigentlich behauptet wird — und was nicht.

Dieser Artikel erklärt den p-Wert nicht am Münzwurf, sondern an sechs eigenen, veröffentlichten Messungen. Jede trägt eine andere Lehre. Eine davon war ein Fehler von uns.

Die Rechenmechanik — Nullhypothese, t-Wert, die Schwelle ±1,96, Cohen's d — steht ausführlich in der [DAX-September-Studie](/blog/dax-september-signifikanz/) und wird hier nicht wiederholt. Hier geht es um das, was danach kommt: wie man das Ergebnis liest.

## Was ein p-Wert sagt, in einem Satz

Der p-Wert ist die Antwort auf **eine** Frage: *Wie häufig käme ein Ergebnis dieser Grösse heraus, wenn der untersuchte Effekt gar nicht existierte?*

Man baut dafür eine Welt ohne Effekt — die Nullverteilung — und sieht nach, wie oft der gemessene Wert in dieser Welt auftritt. p = 0,0050 heisst: in einem halben Prozent der Fälle. p = 0,127 heisst: in rund dreizehn Prozent, also regelmässig.

## Was er nicht sagt

Drei Lesarten sind verbreitet und alle drei falsch.

**Er ist nicht die Wahrscheinlichkeit, dass die Regel stimmt.** p = 0,0050 heisst nicht „mit 99,5 Prozent Wahrscheinlichkeit gibt es Pinning". Die Rechnung läuft in die andere Richtung: Sie unterstellt, dass es den Effekt *nicht* gibt, und fragt, wie ungewöhnlich die Beobachtung dann wäre. Von der Wahrscheinlichkeit einer Hypothese ist nirgends die Rede.

**Er sagt nichts über die Grösse.** Ein p-Wert misst, wie deutlich ein Unterschied vom Zufall zu trennen ist — nicht, wie gross er ist. Bei genug Beobachtungen wird jeder noch so winzige Unterschied signifikant. Das ist kein Fehler des Verfahrens, das ist seine Bauart.

**0,05 ist eine Konvention, kein Naturgesetz.** Die Schwelle ist historisch gewachsen. Zwischen p = 0,049 und p = 0,051 liegt kein inhaltlicher Unterschied, und wer eine Entscheidung an dieser Kante aufhängt, hängt sie an eine Rundung.

## Sechs Messungen, sechs Lehren

### Signifikant und trotzdem wertlos {#p-0-0050}

Am dritten Freitag im Monat verfallen in den USA die klassischen Aktienoptionen, und Kurse schliessen an diesem Tag auffällig oft nah an einem Options-Strike. Gemessen an 158 Aktien über 30 Jahre: **6,88 % gegen 6,53 %** an gewöhnlichen Freitagen derselben Titel. Differenz 0,35 Prozentpunkte, **p = 0,0050**, das 95-Prozent-Intervall reicht von +0,09 bis +0,62 Prozentpunkten und schliesst die Null aus.

Ein solider Befund. Und praktisch unbrauchbar.

0,35 Prozentpunkte auf eine Basis von 6,53 % verschieben die Wahrscheinlichkeit von etwa einem Treffer in 15 Fällen auf einen Treffer in 14,5 Fällen. Gemessen ist dabei eine Differenz von Trefferquoten und keine Rendite — was eine Strategie daraus machen könnte, hängt an einer Auszahlungsstruktur, die diese Studie nicht untersucht hat. Eine Verschiebung dieser Grössenordnung lässt allerdings wenig Raum für Spread und Gebühren.

**Die Lehre:** Signifikanz und Effektstärke sind zwei getrennte Fragen, und nur die zweite entscheidet, ob eine Zahl praktisch etwas bedeutet. Der p-Wert beantwortet ausschliesslich die erste. → [Die ganze Messung](/blog/pinning-verfallstag/)

### „Nicht signifikant" heisst nicht „kein Effekt" {#p-0-127}

Die Volatilität des S&P 500 liegt in September und Oktober beim **1,059-fachen** des übrigen Jahres. Über 836 Monate ab 1957, **p = 0,127**.

Der naheliegende Schluss ist falsch. p = 0,127 heisst nicht, dass September und Oktober genauso ruhig sind wie der Rest des Jahres. Es heisst: *Diese Messung kann den Unterschied nicht von Zufall trennen.* Der gemessene Wert liegt bei 1,059 und nicht bei 1,000 — er ist nur nicht weit genug von dem entfernt, was in einer Welt ohne Kalendereffekt regelmässig vorkommt. Der Median der Zufallsziehungen liegt bei 1,004, das 95-Prozent-Quantil bei 1,084. Und 1,059 liegt darunter.

Ein nicht signifikantes Ergebnis ist damit **keine Aussage über die Welt, sondern über die Auflösung des Messgeräts.** Mit deutlich mehr Beobachtungen könnte derselbe Effekt signifikant werden — es gibt sie nur nicht, der S&P 500 hat nicht mehr als 836 Monate.

**Die Lehre:** „Nicht belegt" und „widerlegt" sind verschiedene Dinge. Wer aus einem hohen p-Wert „es gibt nichts" macht, behauptet mehr als die Rechnung hergibt. → [Volatilitäts-Saisonalität](/vola-saisonalitaet)

### Was ein p-Wert von 0,935 aussagt {#p-0-935}

Ein Anstieg langlaufender US-Staatsanleihen kündigt in unruhigen Marktphasen eine Erholung am Aktienmarkt an — mit +3,65 % in zwei Wochen und p unter 0,001. In ruhigen Phasen dagegen: **+0,53 % bei p = 0,935**, aus 25 Fällen.

Ein p-Wert nahe eins wird oft als besonders starkes Gegenargument gelesen. Er ist etwas anderes: Das Ergebnis liegt **so nah an dem, was man ohne jeden Effekt erwarten würde**, dass 93,5 Prozent aller Zufallsziehungen weiter davon entfernt lagen — der Test ist hier zweiseitig, gemessen wird also der Abstand in beide Richtungen. Die +0,53 % liegen dicht an der Basisrate von +0,48 %, und damit bleibt von dem Signal in diesem Zustand nichts übrig, was diese Messung noch auflösen könnte.

Ein hoher p-Wert ist dabei **kein Beleg für die Null**. Er sagt, dass die Daten mit „kein Effekt" gut vereinbar sind — nicht, dass es keinen gibt. Die amerikanische Statistische Gesellschaft führt diesen Punkt ausdrücklich als eigenes Prinzip.

Das ist der informativste der sechs Werte. Er sagt nicht „schwach", sondern: **die Messung findet hier nichts, was über die Basisrate hinausgeht.**

**Die Lehre:** Ein Effekt, der an eine Bedingung gebunden ist, ist ohne sie nicht mehr nachweisbar. Wer den Anleihen-Befund ohne den Zusatz „im Stress" zitiert, zitiert eine andere Messung. → [Die Anleihen-Studie](/blog/anleihen-fruehindikator-aktienmarkt/)

### Wie belastbar ist p = 0,0241? {#p-0-0241}

Der DAX liegt im September im Mittel bei −1,55 %, dem schwächsten Wert aller zwölf Monate; der nächstschwächste, der Juni, kommt auf −0,27 %. Geprüft wird gegen die Null — also gegen die Annahme, die durchschnittliche September-Rendite sei in Wahrheit null und jede Abweichung Rauschen. Dieser Test ergibt **p = 0,0241**. Das ist signifikant nach der üblichen Konvention — und es ist ein Wert in der Nähe der Kante.

Nützlich ist hier ein Gedankenexperiment: Wäre die Konvention bei 0,01 statt 0,05 gesetzt, stünde derselbe Befund als „nicht belegt" da. An den Daten hätte sich nichts geändert. Das ist der Grund, warum wir neben dem p-Wert immer die Effektstärke und die Zahl der Beobachtungen nennen: Erst zusammen tragen die drei eine Einordnung.

**Die Lehre:** Ein p-Wert ist eine graduelle Grösse, die wie ein Schalter behandelt wird. Zwischen 0,0241 und 0,0500 liegt ein Unterschied im Grad, nicht in der Art. (Kontinuierlich ist er dabei nicht immer: unsere Simulationswerte liegen zwangsläufig auf einem Raster von 1/2001.) → [DAX im September](/blog/dax-september-signifikanz/)

### Wie viele Tests darf man rechnen? {#multiples-testen}

Hier wird es unangenehm, weil dieser Punkt fast alle kursierenden Börsenregeln betrifft.

Wir haben die Frage „bewegt sich Markt B, nachdem Markt A ungewöhnlich stark gelaufen ist" nicht einmal gestellt, sondern **470 Mal** — für jede vorab festgelegte Kombination aus 18 Märkten. Bei einer Schwelle von 0,05 sind unter reinem Zufall rund **24 Treffer** zu erwarten. Nicht weil die Märkte etwas täten, sondern weil 5 Prozent von 470 eben 24 sind.

Wer aus so einer Matrix die auffälligsten Zellen herausgreift und einzeln mit p-Wert zeigt, zeigt Rauschen mit einer Zahl daneben. Genau so entstehen Intermarket-Regeln.

Die Korrektur dagegen heisst **Max-T** und arbeitet anders als die bekannte Bonferroni-Teilung. Anstatt die Schwelle durch die Zahl der Tests zu dividieren, baut man die ganze Matrix tausendfach aus Zufallsdaten neu und notiert jedes Mal nur den **grössten** Wert, der irgendwo darin auftaucht. Die Frage lautet dann nicht mehr „ist diese Zelle auffällig", sondern „wird die beste Zelle einer reinen Zufallsmatrix so gut". Bei unserer Familie liegt die Schranke bei einem standardisierten Effekt von **|t| > 3,92**.

Ergebnis: **genau eine** der 470 Zellen reisst diese Schranke — Silber abwärts, danach Versorger, mit t = 4,09 und einem korrigierten p von 0,043. Sie scheitert an einer anderen vorab festgelegten Bedingung: mindestens 20 Ereignisse in **jeder** Zeithälfte, und dort stehen 21 gegen 14. **Keine einzige Zelle erfüllt alle Kriterien** — das ist nicht dasselbe wie „keine übersteht die Schranke", und der Unterschied ist genau der Grund, warum beide Bedingungen vor dem Blick aufs Ergebnis feststanden.

Diese Grössenordnung ist keine Eigenheit unserer Rechnung. Harvey, Liu und Zhu haben 2016 vorgeschlagen, für einen **neu behaupteten Renditefaktor** angesichts der Menge publizierter Tests einen t-Wert von mindestens **3,0** statt der üblichen 1,96 zu verlangen. Unsere 3,92 sind keine Ableitung daraus, sondern das Ergebnis der eigenen Rechnung: Sie ist das 95-Prozent-Quantil der grössten Werte aus tausend Zufallsmatrizen. Dass beide Zahlen in derselben Gegend liegen, ist die eigentliche Auskunft. Die Arbeiten von Bailey und López de Prado zum Backtest-Overfitting zeigen dieselbe Mechanik von der anderen Seite und rechnen sie als Wahrscheinlichkeit aus: Wer genug Varianten durchprobiert, findet mit wachsender Zahl fast sicher eine mit hervorragenden Kennzahlen.

**Die Lehre:** Ein p-Wert ohne die Angabe, wie viele Fragen gestellt wurden, ist nicht interpretierbar. Diese Zahl gehört zum Ergebnis wie die Stichprobengrösse. → [Die Matrix mit allen 470 Paarungen](/intermarket)

### Bootstrap oder Permutationstest? {#bootstrap-oder-permutation}

Dieser Abschnitt beschreibt einen Fehler, den wir gemacht und veröffentlicht haben.

In der ersten Fassung der Pinning-Studie stand ein p-Wert, der keiner war. Gerechnet wurde ein **Bootstrap**: Aus den beobachteten Daten wird mit Zurücklegen neu gezogen, tausendfach, und man sieht sich die Streuung der Schätzung an. Als p-Wert ausgegeben wurde der Anteil der Ziehungen, deren Differenz unter null lag.

Das ist kein p-Wert, und der Grund ist strukturell. Ein Bootstrap zieht **mit den beobachteten Etiketten** — jeder Verfallstag bleibt ein Verfallstag. Die entstehende Verteilung ist deshalb um die *gemessene* Differenz zentriert, nicht um null. Der Anteil unter null beantwortet die Frage „wie unsicher ist meine Schätzung", eine durchaus sinnvolle Frage. Er beantwortet nicht „wie oft käme das ohne Effekt heraus", denn eine Welt ohne Effekt kommt in dieser Rechnung überhaupt nicht vor.

Ein **Permutationstest** baut genau diese Welt. Er lässt alles stehen, was stehen bleiben muss — die Monatsstruktur, die Zahl der Verfallstage, die Titelauswahl, das Kursniveau der Epoche — und verwürfelt nur das eine, worum es geht: welcher Freitag im Monat der Verfallstag ist. In jedem Monat wird einer ausgelost und so behandelt, als wäre er es. Erst damit ist die Nullverteilung eine Welt ohne Effekt.

Nach dem Wechsel stand p = 0,0050 statt der vorherigen Zahl. Der Befund hielt; die Begründung war vorher falsch.

**Die Lehre:** Ein Bootstrap misst die Unsicherheit einer Schätzung, ein Permutationstest die Vereinbarkeit mit dem Nichts. Beide liefern eine Zahl zwischen null und eins, und nur eine davon ist ein p-Wert. Gefunden hat den Fehler ein externer Review, nicht wir selbst.

## Drei Handgriffe, die über das Ergebnis entscheiden

### Die Richtung muss vorher feststehen

Ein einseitiger Test verlangt weniger als ein zweiseitiger: Er fragt nur, ob der Effekt in eine bestimmte Richtung geht, und fällt dadurch typischerweise kleiner aus — bei einer symmetrischen Nullverteilung und einem Ergebnis in der erwarteten Richtung etwa um die Hälfte. Zulässig ist er nur, **wenn die Richtung vor dem Blick auf das Ergebnis festgelegt war.**

Bei der Volatilitäts-Saisonalität war sie es: Die verbreitete Behauptung lautet, September und Oktober seien *unruhiger*, also wurde einseitig nach oben getestet. Wer dagegen erst rechnet, dann das Vorzeichen sieht und danach den einseitigen Test wählt, halbiert seinen p-Wert unzulässig. In unseren Krypto- und Anleihen-Studien wurde genau das nachträglich korrigiert: Dort war die Richtung nach dem Ergebnis gewählt worden, obwohl die Frage ergebnisoffen gestellt war („passiert etwas?"). Nach der Umstellung auf zweiseitige Tests verdoppelten sich die p-Werte etwa, die Einordnung hielt.

### Die Plus-eins-Korrektur

Wenn eine Nullverteilung aus 2000 Ziehungen besteht und keine davon den gemessenen Wert erreicht, ist der p-Wert nicht null. Er ist nach dieser Konvention **genau 1/2001**. Der kleinste Wert, den ein solches Simulationsverfahren ausweisen kann, ist eins geteilt durch die Zahl der Ziehungen plus eins — das ist eine Eigenschaft dieser Rechnung und keine Aussage über alle Testverfahren:

```
p = (Zahl der Ziehungen, die den Wert erreichen + 1) / (Zahl der Ziehungen + 1)
```

Ohne das Plus-eins weist ein Verfahren irgendwann „p = 0,000" aus, und das ist eine Aussage, die kein Simulationsverfahren treffen kann.

### Die Nullverteilung ist eine Modellentscheidung

Der p-Wert ist nur so gut wie die Welt ohne Effekt, gegen die er gerechnet wird — und diese Welt baut man selbst.

Ein Beispiel aus derselben Studie: Volatilität kommt in Blöcken, eine unruhige Woche besteht aus fünf unruhigen Tagen. Wer für die Nullverteilung einfach Tage mischt, zerstört dieses Clustering und erzeugt eine zu enge Verteilung — der Test wird dadurch zu liberal und lässt Unterschiede signifikant erscheinen, die es nicht sind. Wir verschieben deshalb den Kalender zirkulär gegen die Kursreihe: Das zerstört die Kalenderzuordnung und erhält die Blockstruktur.

Verschiebungen um **Vielfache von zwölf Monaten** schliessen wir dabei aus. Sie ordnen fast jeden September wieder einem September zu, verwürfeln die Kalenderzuordnung also kaum — das ist eine begründete Modellwahl und kein Zwang, denn eine Verschiebung, die die beobachtete Statistik erhält, ist unter der Nullhypothese grundsätzlich eine Möglichkeit wie jede andere. Unsere Pinning-Studie schliesst den echten Verfallstag aus genau diesem Grund ausdrücklich ein.

Wie viel dieser Ausschluss ausmacht, haben wir nachgemessen statt es anzunehmen — gepaart, also mit denselben Verschiebungen einmal mit und einmal ohne Ausschluss, über acht Startwerte: Er **hebt** den p-Wert um +0,008, von rund 0,116 auf 0,124. Klein, konsistent im Vorzeichen, und ohne Folge für das Ergebnis; beide Varianten liegen deutlich über 0,05. Im Code stand vorher die Vermutung, es sei umgekehrt.

## Wie viele Beobachtungen braucht so eine Messung?

Die Pinning-Studie ist dafür ein brauchbarer Maßstab, weil sie beide Seiten zeigt.

Über alle 158 Titel und 369 Monate zusammen sind 0,35 Prozentpunkte messbar. **Je einzelnem Titel sind sie es nicht:** Dort bleiben je nach Historie einige Dutzend bis einige Hundert Verfallstage, und in der Streuung so weniger Beobachtungen verschwindet der Effekt. Der Median der Einzeldifferenzen liegt bei +0,28 Prozentpunkten, im Plus sind 86 von 158 Titeln — eine Quote, die von einem Münzwurf kaum zu unterscheiden ist.

Derselbe wahre Effekt ist also einmal belegt und einmal unsichtbar, und der Unterschied liegt ausschliesslich in der Zahl der Beobachtungen. Wer einen Backtest über 30 Trades rechnet, braucht dafür einen entsprechend grossen Effekt — bei einem kleinen reicht diese Zahl nicht, und der p-Wert sagt dann nur, dass die Messung zu grob war.

## Wie die p-Werte auf dieser Seite zu lesen sind

Vier Punkte, die auf jede unserer Auswertungen zutreffen:

Neben jedem p-Wert steht die **Effektstärke** und die **Zahl der Beobachtungen**. Ohne diese beiden ist er nicht interpretierbar.

Bei jeder Messung steht, **wie viele Fragen gestellt wurden**. Eine Zahl aus einer Familie von 470 Tests ist anders zu lesen als eine aus einem einzelnen, vorab festgelegten Test.

Ergebnisse, die die Stichprobe nicht tragen, bekommen **keinen p-Wert**, sondern die Kennzeichnung *beschreibend* — bei 36 Ereignissen wäre ein p-Wert Scheingenauigkeit.

Und ein signifikanter Effekt ist **keine Handelsempfehlung**. Diese Seite gibt keine Anlageberatung; welche unserer Messungen nach Kosten überhaupt etwas übrig lässt, steht in der [Übersicht aller Auswertungen](/blog/boersenregeln-nachgerechnet/).

## Häufige Fragen

### Was heisst p = 0,05 konkret?

Dass ein Ergebnis dieser Grösse in einer Welt ohne den untersuchten Effekt in einem von zwanzig Fällen vorkäme. Nicht, dass die Regel mit 95 Prozent Wahrscheinlichkeit stimmt — diese Umdeutung ist die häufigste Fehllesart überhaupt.

### Kann ein Effekt signifikant und trotzdem nicht handelbar sein?

Regelmässig, und unser bestbelegter Befund ist genau so ein Fall: 0,35 Prozentpunkte bei p = 0,0050 lassen für Gebühren kaum Raum. Signifikanz misst die Unterscheidbarkeit von Zufall, nicht die Grösse. Bei genug Beobachtungen wird jeder winzige Unterschied signifikant.

### Heisst „nicht signifikant", dass es den Effekt nicht gibt?

Nein. Es heisst, dass diese Messung ihn nicht von Zufall trennen kann. Das kann am Effekt liegen oder an der Stichprobe. Bei der Volatilität im September und Oktober steht 1,059 gegen 1,000 — die Messung reicht nur nicht aus, um daraus mehr zu machen.

### Warum ist der Bootstrap-Anteil kein p-Wert?

Weil ein Bootstrap mit den beobachteten Etiketten zieht und seine Verteilung deshalb um die gemessene Schätzung zentriert ist, nicht um null. Er beantwortet „wie unsicher ist meine Schätzung". Ein p-Wert braucht eine Verteilung, die eine Welt **ohne** Effekt darstellt — dafür muss man die Etiketten verwürfeln, wie im Permutationstest.

### Wie viele Beobachtungen braucht ein Signifikanztest an Kursdaten?

Es gibt keine feste Zahl; sie hängt an der Grösse des gesuchten Effekts und an der Streuung — das ist keine Ausrede, sondern die Antwort. Ein Anhaltspunkt aus unseren Messungen: 0,35 Prozentpunkte brauchten 41.203 Beobachtungen, um messbar zu werden — auf die einzelnen Titel verteilt waren dieselben 0,35 Prozentpunkte unsichtbar.

<!--
#### Social Media Snippet

**LinkedIn:**
Unser am besten belegter Befund ist wirtschaftlich wertlos — und das ist der beste Einstieg in den p-Wert, den ich kenne.
0,35 Prozentpunkte bei p = 0,0050, über 41.203 Beobachtungen und 30 Jahre. Solide gemessen. Überlebt keine Gebühr.
Wir geben auf jeder Studienseite p-Werte an und haben sie nie erklärt. Jetzt an sechs eigenen Messungen, jede mit einer anderen Lehre:
— p = 0,0050: signifikant und trotzdem unbrauchbar
— p = 0,127: „nicht signifikant" ist eine Aussage über das Messgerät, nicht über die Welt
— p = 0,935: die informativste Zahl von allen — genau die Basisrate, keine Information
— 470 Tests, ~24 erwartete Zufallstreffer, null belastbare Befunde
— und ein eigener Fehler: der Anteil der Bootstrap-Ziehungen unter null ist kein p-Wert, weil ein Bootstrap um die Schätzung zentriert ist und nicht um null. Ersetzt durch einen Permutationstest.
Keine Anlageberatung. → seasonalpha.ai

**Twitter/X:**
Signifikant ≠ profitabel.
Unser bestbelegter Befund: 0,35 Prozentpunkte bei p = 0,0050, 41.203 Beobachtungen. Solide. Und wertlos, weil Gebühren grösser sind als der Effekt.
Der p-Wert an sechs eigenen Messungen erklärt — inklusive einem Fehler, den wir gemacht haben.
#Statistik #Börse #SeasonAlpha

#### Interne Verlinkung
- /blog/pinning-verfallstag/ (p = 0,0050, signifikant und wertlos)
- /vola-saisonalitaet (p = 0,127, nicht signifikant)
- /blog/anleihen-fruehindikator-aktienmarkt/ (p = 0,935, exakt die Basisrate)
- /blog/dax-september-signifikanz/ (die Rechenmechanik, t-Wert und Cohen's d)
- /intermarket (470 Tests, Max-T-Korrektur)
- /blog/boersenregeln-nachgerechnet/ (Übersicht aller Auswertungen)

#### Content-Ideen (Folgeartikel)
- „Effektstärke: wie gross muss ein Effekt sein, damit er Gebühren überlebt?" — Cohen's d gegen Transaktionskosten, durchgerechnet
- „Wie viele Trades braucht ein Backtest?" — Trennschärfe je Effektgrösse, als Tabelle
- „Die Kontrollgruppe: wie man eine falsche Annahme unschädlich macht" — am Strike-Raster der Pinning-Studie
-->

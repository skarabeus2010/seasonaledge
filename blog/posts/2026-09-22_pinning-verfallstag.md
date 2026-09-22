---
title: "Pinning am Verfallstag: +0,35 Prozentpunkte in 30 Jahren — und der Effekt wird stärker"
seo_title: "Pinning am Verfallstag: 30 Jahre gemessen, 158 Aktien"
slug: pinning-verfallstag
date: 2026-09-22
category: education
tags: [optionen, verfallstag, opex, pinning, delta-hedging, statistik]
description: "Schließen Aktien am Optionsverfall häufiger auf einem Strike? 158 Titel, 30 Jahre, 41.203 Beobachtungen: 6,88 % gegen 6,53 %, p = 0,0075."
ticker: SPY
status: published
---

<!--
Keyword-Plan:
- Haupt-Keyword: Pinning Verfallstag
- Neben-Keywords: Optionsverfall Aktienkurs, OPEX Effekt Aktien, Strike Pinning Studie, Delta-Hedging Kurs, dritter Freitag Optionen, Open Interest Strike, Verfallstag Statistik, Stillhalter Absicherung
- LSI: Kontrollgruppe, Bootstrap, Konfidenzintervall, p-Wert, Teilperiode, Wochenoptionen, Schlusskurs, Strike-Raster
-->

## Die Frage

Am dritten Freitag im Monat verfallen die klassischen Aktienoptionen in den USA. Eine alte Beobachtung aus dem Optionshandel besagt, dass Aktienkurse an diesem Tag ungewöhnlich oft sehr nah an einem Options-Strike schließen. Dieses Phänomen heißt Pinning.

Wir haben es an 158 optionablen US-Aktien über 30 Jahre nachgerechnet: **6,88 % der Schlusskurse liegen am Verfallsfreitag auf einem Strike gegenüber 6,53 % an allen anderen Freitagen** derselben Titel. Die Differenz beträgt +0,35 Prozentpunkte bei p = 0,0075.

## Warum ein Kurs an einem Strike kleben kann

Wer eine Option verkauft hat, sichert die Position in der Regel über die zugrundeliegende Aktie ab. Verkaufte Calls werden mit gekauften Aktien neutralisiert, verkaufte Puts mit leerverkauften. Wie viele Aktien dafür nötig sind, sagt das Delta der Option.

Kurz vor dem Verfall ändert sich dieses Delta in der Nähe des Strikes extrem schnell. Eine Option, die knapp im Geld liegt, braucht fast die volle Aktienmenge zur Absicherung, eine knapp aus dem Geld liegende fast keine. Steigt der Kurs über den Strike, müssen Stillhalter zukaufen; fällt er darunter, verkaufen sie wieder.

Diese Anpassung wirkt gegen die jeweilige Bewegung. Liegt an einem Strike viel Open Interest, kann das Absichern den Kurs in dessen Nähe halten. Diese Mechanik ist die gängige Erklärung für Pinning. Die zugehörige Marktstruktur zeigen wir laufend unter [Key Levels](/key-levels), wo die größten Open-Interest-Ansammlungen je Titel stehen.

## Das Strike-Raster kennen wir nicht — die Kontrollgruppe löst das

Für eine saubere Messung müsste man für jeden Tag der Vergangenheit wissen, an welchen Kursniveaus tatsächlich Optionen notiert waren. Diese Raster haben sich über die Jahrzehnte mehrfach geändert, sie unterscheiden sich je Titel, je Kursniveau und je Laufzeit. Historisch vollständig verfügbar sind sie nicht.

Jede Annahme darüber ist also falsch. Der Ausweg führt nicht über ein besseres Raster, sondern über die Vergleichsgruppe: Dieselbe Annahme wird auf Verfallsfreitage **und** auf alle übrigen Freitage derselben Aktien im selben Zeitraum angewandt.

Ist das unterstellte Raster zu grob, zu fein oder an den falschen Stellen, dann ist es in beiden Gruppen auf identische Weise verkehrt. Die absolute Quote verliert dadurch ihre Bedeutung, die Differenz zwischen den Gruppen bleibt interpretierbar. Als Treffer zählt ein Schlusskurs, der höchstens 0,125 $ von einem angenommenen Strike entfernt liegt.

Verglichen werden ausschließlich Freitage mit Freitagen, damit sich der bekannte Wochentagseffekt nicht in die Rechnung mischt. Datenbasis sind Tagesschlusskurse, 41.203 Beobachtungen an Verfallsfreitagen gegen 135.738 Kontrollbeobachtungen, verteilt auf 369 Kalendermonate von 1996 bis 2026.

## Die Zahlen: gesamt und in zwei Teilperioden

![Drei Balkenpaare im Vergleich: Anteil der Schlusskurse am Strike an Verfallsfreitagen gegen übrige Freitage, für den Gesamtzeitraum 1996-2026 (6,88 % gegen 6,53 %, p = 0,0075), für die Jahre bis 2009 (8,43 % gegen 8,28 %, p = 0,3188) und ab 2010 (6,06 % gegen 5,61 %, p = 0,0015)](pinning-verfallstag/1_perioden.png)

| Zeitraum | Verfallsfreitage | übrige Freitage | Differenz | p |
|---|---:|---:|---:|---:|
| 1996–2026 | **6,88 %** | 6,53 % | +0,35 pp | 0,0075 |
| bis 2009 | 8,43 % | 8,28 % | +0,15 pp | 0,3188 |
| ab 2010 | **6,06 %** | 5,61 % | +0,45 pp | 0,0015 |

Über den Gesamtzeitraum liegt das 95-Prozent-Intervall der Differenz bei **+0,07 bis +0,65 Prozentpunkten**. Es schließt die Null aus, umfasst aber eine Spanne vom Fast-Nichts bis zum knapp Doppelten des Punktschätzers.

Geprüft wurde eine einzige, vorab festgelegte Hypothese, und zwar gerichtet: Am Verfallsfreitag liegt der Anteil höher. Es wurden nicht mehrere Schwellen, Definitionen oder Zeitfenster durchprobiert, aus denen man sich anschließend das beste Ergebnis aussuchen könnte.

## Wochenoptionen haben den Monatsverfall nicht entwertet

Seit 2010 sind wöchentlich verfallende Optionen auf breiter Front verfügbar. Die naheliegende Erwartung: Das Open Interest verteilt sich auf viele Termine, der monatliche Verfallstag verliert seine Sonderstellung, der Effekt schrumpft.

Gemessen ist das Gegenteil. Vor 2010 beträgt die Differenz +0,15 Prozentpunkte bei p = 0,3188, ist also mit diesen Daten nicht von null zu unterscheiden. Ab 2010 sind es +0,45 Prozentpunkte bei p = 0,0015. Der Effekt ist in der jüngeren Hälfte dreimal so groß und erst dort statistisch belastbar.

Die Trennstelle 2010 stand vor der Rechnung fest, sie wurde nicht nachträglich dorthin gelegt, wo der Unterschied am größten aussieht. Eine Erklärung liefern diese Daten nicht mit. Denkbar ist, dass die Bedeutung des Monatsverfalls gewachsen ist, weil das gesamte Optionsvolumen seit 2010 stark zugenommen hat und der dritte Freitag weiterhin der Termin mit dem größten offenen Bestand ist.

## Warum man die Niveaus nicht vergleichen darf

Die absoluten Quoten der beiden Teilperioden liegen weit auseinander, 8,43 % gegen 6,06 %. Daraus lässt sich nichts ableiten. Die Kurse der untersuchten Aktien sind über drei Jahrzehnte deutlich gestiegen, damit ist die feste Toleranz von 0,125 $ relativ zum Kurs immer enger geworden. Der Rückgang der Quote spiegelt damit vor allem gestiegene Kursniveaus.

Dasselbe gilt für den Vergleich mit der Fachliteratur. Die bekannteste Untersuchung zum Thema, Ni, Pearson und Poteshman, findet rund **19,2 % gegen 18,0 %**. Unsere Niveaus liegen bei einem Drittel davon, weil das dort verwendete Raster das tatsächliche ist und feiner liegt als unser angenommenes. Vergleichbar ist die Differenz, nicht das Niveau. Beide Messungen finden einen Überschuss am Verfallstag in derselben Größenordnung von gut einem Prozentpunkt beziehungsweise einem Drittel Prozentpunkt bei entsprechend niedrigerer Basis.

## Je einzelnem Titel ist der Effekt im Rauschen

![Verteilung der Pinning-Differenz über die 158 untersuchten Aktien: Histogramm der Differenz zwischen dem Anteil am Strike an Verfallsfreitagen und an übrigen Freitagen je Ticker, eingipflig und leicht rechts von null, Median +0,28 Prozentpunkte, 86 der 158 Titel im Plus, ohne dominierenden Ausreißer](pinning-verfallstag/2_je_ticker.png)

Ein Mittelwert über 158 Titel könnte auch entstehen, wenn wenige Aktien einen starken Ausschlag zeigen und der Rest nichts. Einen solchen Ausreißer gibt es nicht: Die Verteilung der Einzeldifferenzen ist eingipflig und liegt mit einem Median von **+0,28 Prozentpunkten** leicht rechts von null. Im Plus liegen 86 der 158 Titel, also 54 Prozent und damit kaum mehr als ein Münzwurf.

Der Grund steckt in der Fallzahl je Aktie. Auf einen einzelnen Titel entfallen je nach Historie nur 24 bis 70 Verfallstage. Gegen die Streuung, die bei so wenigen Beobachtungen entsteht, sind 0,35 Prozentpunkte nicht zu erkennen.

Sichtbar wird der Effekt erst über 158 Titel und 369 Monate zusammen. Genau deshalb wird eine solche Messung gepoolt. An einer einzelnen Aktie lässt sich das Muster nicht nachprüfen.

## Grenzen

**Der Effekt ist klein.** +0,35 Prozentpunkte auf eine Basis von 6,53 % sind eine relative Steigerung von gut fünf Prozent. Das ist kein Handelssignal und trägt keine Strategie.

**Die Abhängigkeitsstruktur ist berücksichtigt, aber nicht aufgelöst.** 158 Aktien an demselben Freitag sind keine 158 unabhängigen Beobachtungen, der Gesamtmarkt bewegt sie gemeinsam. Das Bootstrap-Verfahren zieht deshalb ganze Monate statt einzelner Ticker-Tage. Innerhalb eines Monats bleibt die Struktur damit erhalten.

**Es sind Tagesschlusskurse.** Was im Tagesverlauf passiert, ob sich der Kurs dem Strike also im Verlauf annähert oder erst in der Schlussauktion, ist mit diesen Daten nicht messbar.

**Das Open Interest steckt nicht in der Rechnung.** Gemessen wird die Nähe zu einem angenommenen Strike, unabhängig davon, wie viele Kontrakte dort tatsächlich offen waren. Die Theorie sagt, dass der Effekt mit dem Open Interest an genau diesem Strike wächst. Das ist mit dieser Messung nicht geprüft.

**Der Zusammenhang ist kein Nachweis der Ursache.** Dass Kurse am Verfallstag etwas häufiger an einem Strike schließen, belegt nicht, dass Delta-Hedging es verursacht hat.

## Was daraus folgt

Die Beobachtung aus dem Optionshandel hält der Prüfung an 30 Jahren stand, in einer Größenordnung, die weit unterhalb dessen liegt, was der Begriff Pinning nahelegt. Ein Kurs, der am dritten Freitag "am Strike klebt", bleibt ein Ausnahmefall.

Praktisch relevant ist der Effekt dort, wo eine Position ohnehin in der Nähe eines großen Strikes ausläuft. Wo diese Niveaus aktuell liegen, steht unter [Key Levels](/key-levels); der Verfallskalender mit allen Terminen liegt unter [OPEX](/opex), und wie sich die Volatilitätsstruktur um solche Termine verhält, zeigt der [Vol-Regime-Radar](/skew).

**Kein Signal:** Was hier steht, ist eine Messung an historischen Kursen, keine Handelsregel und keine Aussage über künftige Kurse.

## Häufige Fragen

### Was bedeutet Pinning am Verfallstag?

Pinning beschreibt die Beobachtung, dass Aktienkurse am Optionsverfallstag häufiger sehr nah an einem Options-Strike schließen als an anderen Tagen. Als Erklärung gilt das Delta-Hedging der Stillhalter: Ihre Absicherungskäufe und -verkäufe wirken kurz vor Verfall gegen Bewegungen vom Strike weg.

### Wie stark ist der Effekt messbar?

Über 158 US-Aktien und 30 Jahre schließen 6,88 % der Kurse an Verfallsfreitagen innerhalb von 0,125 $ eines angenommenen Strikes, gegenüber 6,53 % an allen übrigen Freitagen. Die Differenz von +0,35 Prozentpunkten hat ein p von 0,0075, das 95-Prozent-Intervall reicht von +0,07 bis +0,65 Prozentpunkten.

### Warum liegen diese Quoten so weit unter den 19 % aus der Forschung?

Weil das hier unterstellte Strike-Raster gröber ist als das tatsächliche, das der Studie von Ni, Pearson und Poteshman zur Verfügung stand. Ein gröberes Raster erzeugt in beiden Gruppen weniger Treffer. Vergleichbar ist deshalb die Differenz zwischen Verfallstagen und Kontrolltagen; die absolute Höhe hängt am Raster.

### Haben Wochenoptionen den Monatsverfall abgelöst?

Für diesen Effekt nicht. Bis 2009 beträgt die Differenz +0,15 Prozentpunkte bei p = 0,3188, ab 2010 dagegen +0,45 Prozentpunkte bei p = 0,0015. Der Überschuss am dritten Freitag ist in der Zeit der Wochenoptionen also gewachsen.

### Lässt sich der Effekt an einer einzelnen Aktie nachvollziehen?

Nein. Je Titel liegen nur 24 bis 70 Verfallstage vor, und 0,35 Prozentpunkte verschwinden in der Streuung so weniger Beobachtungen. Der Median der Einzeldifferenzen liegt bei +0,28 Prozentpunkten, im Plus sind 86 der 158 Titel. Messbar wird der Effekt erst über alle Titel und 369 Monate zusammen.

### Lässt sich daraus eine Handelsstrategie ableiten?

Nein. Eine Erhöhung um 0,35 Prozentpunkte bei einer Basis von 6,53 % verschiebt Wahrscheinlichkeiten minimal und deckt keine Transaktionskosten. Der Wert der Messung liegt im Verständnis der Marktmechanik rund um den Verfallstag.

<!--
#### Social Media Snippet

**LinkedIn:**
„Am Verfallstag klebt der Kurs am Strike" — diese Regel aus dem Optionshandel haben wir an 158 US-Aktien über 30 Jahre nachgerechnet.
Ergebnis: 6,88 % der Schlusskurse liegen am Verfallsfreitag auf einem Strike, gegen 6,53 % an allen übrigen Freitagen derselben Titel. +0,35 Prozentpunkte, p = 0,0075, 41.203 gegen 135.738 Beobachtungen.
Die Teilperioden widersprechen der Erwartung: Seit 2010 gibt es Wochenoptionen, der Monatsverfall müsste an Gewicht verloren haben. Gemessen ist er ab 2010 dreimal so groß (+0,45 pp, p = 0,0015) wie davor (+0,15 pp, p = 0,3188).
Zur Methode: historische Strike-Raster sind nicht verfügbar. Gelöst über die Kontrollgruppe — dieselbe falsche Annahme auf beide Gruppen angewandt, dann bleibt die Differenz aussagekräftig.
Der Effekt ist klein und kein Handelssignal. → seasonalpha.ai

**Twitter/X:**
Pinning am Verfallstag, 158 US-Aktien, 30 Jahre:
6,88 % der Schlusskurse am Strike an Verfallsfreitagen, 6,53 % an anderen Freitagen. +0,35 pp, p = 0,0075.
Dazu: ab 2010 (Wochenoptionen!) ist der Effekt dreimal so groß, nicht kleiner.
Klein. Kein Handelssignal.
#Optionen #Börse #SeasonAlpha

#### Interne Verlinkung
- /key-levels (Open-Interest-Walls und Max Pain je Titel)
- /opex (Verfallskalender, dritter Freitag, Triple Witching)
- /skew (Vol-Regime-Radar, Volatilitätsstruktur um Verfallstermine)
- /dealer-positioning (Gamma-, Vanna- und Charm-Profile der Stillhalter)

#### Content-Ideen (Folgeartikel)
- „Pinning nach Open Interest: wird der Effekt an stark besetzten Strikes größer?" — dieselbe Messung mit Chain-Daten statt angenommenem Raster
- „Die Woche nach dem Verfall" — Renditeverteilung in den fünf Handelstagen nach OPEX
- „Triple Witching gegen normalen Verfall" — vier Termine im Jahr getrennt gemessen
-->

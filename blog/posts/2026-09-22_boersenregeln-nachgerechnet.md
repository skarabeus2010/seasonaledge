---
title: "Elf Börsenregeln nachgerechnet — vier halten nicht"
seo_title: "Börsenweisheiten auf dem Prüfstand: 11 Regeln getestet"
slug: boersenregeln-nachgerechnet
date: 2026-09-22
category: education
tags: [statistik, saisonalitaet, boersenweisheiten, boersenmythen, signifikanz, methodik]
ticker: SPY
status: published
description: "September als Crash-Monat? Faktor 1,059 bei p = 0,127. Elf Börsenregeln an historischen Kursdaten gemessen, jede mit Frage, Ergebnis und Datenbasis."
---

<!--
Keyword-Plan:
- Haupt-Keyword: Börsenweisheiten auf dem Prüfstand
- Entitäten im Text: Börsenweisheiten, Börsenmythen, Börsenregeln
- Neben-Keywords (als Frage-H3 umgesetzt): September Oktober Crash-Monate, Anleihen Frühindikator Aktien,
  Bitcoin läuft voraus, Pre-FOMC-Drift, Expected Move Optionspreise, Monthly 10 Strategie,
  S&P-500-Aufnahme Kurseffekt, DAX September Statistik, Pinning Verfallstag
- LSI: Signifikanztest, Permutationstest, Kontrollgruppe, Effektstärke, Stichprobe,
  vorab festgelegt, multiples Testen, Data Mining, Konfidenzintervall
-->

## September ist nicht der Crash-Monat

Die Volatilität des S&P 500 liegt in September und Oktober beim **1,059-fachen** des übrigen Jahres. Gemessen über 836 Monate ab 1957 — und von zufälliger Schwankung nicht zu unterscheiden, **p = 0,127**.

Das ist eine von elf Börsenweisheiten, die wir an eigenen Kursdaten nachgerechnet haben. Jede mit einer Frage, die vor der Rechnung feststand. **Sieben halten. Vier nicht.**

Die vier stehen hier mit derselben Ausführlichkeit wie die anderen sieben, und zwar aus einem praktischen Grund: Eine Regel, die nicht hält, ist genau die, die Geld kostet, solange man ihr folgt.

## Die Übersicht

| Regel | Ergebnis | Datenbasis |
|---|---|---|
| Pinning am Verfallstag | **belegt** · +0,35 pp, p = 0,0050 | 158 Aktien, 30 Jahre |
| DAX im September schwach | **belegt** · Ø −1,55 %, p = 0,0241 | DAX, 68 Jahre je Monat |
| Expected Move ist zu weit | **belegt** · 84,3 % statt 68,3 % | VIX/S&P 500, 1990–2026 |
| Anleihen als Frühindikator | **nur im Stress** · +2,09 % in zwei Wochen | 50 Fälle seit 2002 |
| Bitcoin läuft voraus | **erst ab 20 %** · darunter nichts | 12 Jahre, 3020 Handelstage |
| September/Oktober unruhiger | **nicht belegt** · Faktor 1,059, p = 0,127 | S&P 500 ab 1957, 836 Monate |
| Intermarket-Signale | **nicht belegt** · 0 von 470 Paarungen | 18 Märkte |
| Monthly 10 schlägt den Markt | **nicht belegt** · 5,58 % gegen 10,71 % p.a. | S&P 500, 1994–2025 |
| Pre-FOMC-Drift | *beschreibend* · +0,131 % am Vortag | S&P 500, 2006–2025 |
| Index-Aufnahme treibt den Kurs | *beschreibend* · +5,8 % bei T+20 | 36 Aufnahmen |
| Zwischenwahljahr | *beschreibend* · danach Ø +31 % | Zyklen seit 1950 |

Die drei Stufen bedeuten Verschiedenes, und der Unterschied ist der eigentliche Inhalt dieses Artikels. **Belegt** heißt: Die Frage stand vorher fest, der Unterschied ist gemessen, und er übersteht einen [Signifikanztest](/blog/p-wert-erklaert/). **Beschreibend** heißt: Das Muster ist da, aber die Zahl der Beobachtungen trägt keinen Test — bei 36 Ereignissen ist ein [p-Wert](/blog/p-wert-erklaert/#multiples-testen) Scheingenauigkeit. Dazwischen liegen die Fälle, in denen der Effekt an eine Bedingung gebunden ist, die man mitzitieren muss.

## Was hält

### Kleben Kurse am Verfallstag an einem Strike?

Ja, aber knapp. Am dritten Freitag verfallen in den USA die klassischen Aktienoptionen. An 158 Aktien über 30 Jahre gemessen: **6,88 % der Schlusskurse liegen am Verfallsfreitag auf einem Strike gegen 6,53 % an allen übrigen Freitagen** derselben Titel. Die Differenz von 0,35 Prozentpunkten übersteht einen Permutationstest mit p = 0,0050.

Die Teilperioden widersprechen der Erwartung. Seit 2010 gibt es Wochenoptionen, der Monatsverfall müsste an Gewicht verloren haben. Gemessen ist der Effekt seither dreimal so groß wie davor: +0,45 Prozentpunkte gegen +0,15, und vor 2010 war er nicht messbar (p = 0,27).

Bei aller Signifikanz: 0,35 Prozentpunkte auf eine Basis von 6,53 % verschieben Wahrscheinlichkeiten minimal und decken keine Gebühren. → [Pinning am Verfallstag, 30 Jahre gemessen](/blog/pinning-verfallstag/)

### Ist der September beim DAX statistisch auffällig?

Ja, und zwar als einziger Monat. Ø **−1,55 %** — der schwächste Wert aller zwölf Monate, der nächstschwächste (Juni) liegt bei −0,27 %. Geprüft wird gegen die Null, und dieser Test ergibt **p = 0,0241**.

Das ist ein echter Effekt und ein kleiner. Signifikant und groß sind zwei verschiedene Eigenschaften, und der September verwechselt sie gern: Ein p-Wert sagt, wie unwahrscheinlich ein Unterschied dieser Größe bei reinem Zufall wäre. Über die Größe selbst sagt er nichts. → [DAX-September im Signifikanztest](/blog/dax-september-signifikanz/)

### Wie genau ist der Expected Move aus Optionspreisen?

Er ist zu weit, und zwar verlässlich.

Aus dem Preis einer am Geld liegenden Option lässt sich ausrechnen, wie weit sich ein Markt bis zum Verfall bewegen sollte: implizite Volatilität mal Wurzel aus der Restlaufzeit. Das Ergebnis heißt Ein-Sigma-Band, und unter der Annahme normalverteilter Renditen müsste der Kurs in **68,3 %** der Fälle darin bleiben. Diese Zahl steht auf jeder Optionsplattform.

Gemessen über 1990 bis 2026, mit dem VIX als Volatilitätsmaß gegen den S&P 500, blieb der Kurs in **84,3 %** der Fälle innerhalb des Bandes. Der Vertrauensbereich reicht von 82,2 bis 86,3 Prozent und schließt die 68,3 deutlich aus. Weil sich rollierende 30-Tage-Fenster überlappen und damit die Zahl unabhängiger Beobachtungen überschätzen, haben wir es zusätzlich an nicht überlappenden Fenstern gerechnet: 83,4 %. Der Befund hängt also nicht an der Überlappung.

Eine Einschränkung gehört dazu: Der VIX ist nicht die Volatilität am Geld. Er wird über den ganzen Strip aus dem Geld liegender Optionen gebildet und liegt konstruktionsbedingt darüber. Dieser Versatz macht das Band eher noch etwas zu weit, erklärt aber nicht die gesamte Lücke — die Änderungen beider Größen laufen mit einer Korrelation von 0,857 gleich.

Die Lücke hat einen Namen und einen Empfänger: Sie ist die Volatilitäts-Risikoprämie. Optionen sind im Schnitt teurer als die Bewegung, die tatsächlich eintritt, weil jemand für das Risiko bezahlt werden will, im Ernstfall die ganze Bewegung zu tragen. Das ist der Grund, warum Optionen-Verkaufen ein Geschäftsmodell ist — und warum es in den seltenen Fällen, in denen das Band nicht hält, sehr teuer wird. → [Vol-Regime-Radar mit Expected Move je Titel](/skew)

## Was nur unter einer Bedingung gilt

### Kündigen Anleihen einen Anstieg am Aktienmarkt an?

Im Stress ja, sonst nicht. Nach einem Anstieg langlaufender US-Staatsanleihen um mindestens 4,06 % über zehn Handelstage stieg der S&P 500 in den folgenden zwei Wochen um **+2,09 %** gegen +0,48 % im Mittel. 50 Fälle seit 2002, p zwischen 0,001 und 0,005, Trefferquote 74 % gegen 65,7 %.

Die Bedingung entscheidet alles. In ruhigen Marktphasen liegt derselbe Effekt bei **exakt der Basisrate** — p = 0,935, also nichts. In unruhigen bei +3,65 %. Wer die Regel ohne diesen Zusatz zitiert, zitiert etwas anderes, als gemessen wurde.

Dazu kommt ein zweiter Zusatz, der leicht untergeht: Es ist ein **Erholungsmuster**, keine Vorhersage aus heiterem Himmel. Der S&P 500 war vor dem Ereignis im Median um 1,31 % gefallen, in 62 % der Fälle stand er im Minus. Ohne diese Hälfte liest man eine Prognose, wo eine Erholung steht. → [Die Anleihen-Studie im Detail](/blog/anleihen-fruehindikator-aktienmarkt/)

### Läuft Bitcoin dem Aktienmarkt voraus?

Erst ab sehr großen Bewegungen, und dann schwach. Die verbreitete Fassung dieser Regel nennt eine Schwelle von fünf Prozent. Genau daran scheitert sie: Fünf Prozent sind bei Bitcoin der **Median** aller Zehn-Tage-Bewegungen, also die normalste Bewegung, die es dort gibt. Eine Regel, die an der Hälfte aller Tage anschlägt, sagt nichts vorher.

Messbar wird es ab zehn Prozent, belastbar ab zwanzig: Dann folgt dem S&P 500 nach drei Wochen ein Plus von 2,29 % bei p = 0,027.

Die Zahl, die den Fall entscheidet, ist eine andere. Bei Versatz null liegt die Korrelation zwischen Krypto und Aktien bei +0,36 bis +0,45 — deutlich. Einen Tag versetzt ist sie verschwunden. Das ist keine schwache Prognose, das ist gar keine: Die Märkte bewegen sich **gleichzeitig**, weil beide am selben Risikoappetit hängen. Eine gleichzeitige Korrelation kann man beobachten, aber nicht handeln. → [Zwölf Jahre Krypto gegen Aktien](/blog/laeuft-bitcoin-dem-aktienmarkt-voraus/)

## Was nicht hält

### Sind September und Oktober wirklich die Crash-Monate?

Nein. Die Volatilität dieser beiden Monate liegt beim **1,059-fachen** des übrigen Jahres, und das ist von Zufall nicht zu unterscheiden: **p = 0,127** über 836 Monate ab 1957.

Gemessen wird die annualisierte Streuung der Tagesrenditen, die dem jeweiligen Monat gehören, und über die Jahre der Median genommen — so bestimmt kein einzelnes Krisenjahr das Bild. Volatilität statt Rendite deshalb, weil sie die verlässlichere Größe ist: Renditen sind kaum vorhersagbar, Volatilität hängt stark an ihrer eigenen Vergangenheit.

Der p-Wert entsteht aus einer Vergleichsverteilung. Dafür wird der Kalender gegen die Kursreihe verschoben und gemessen, wie oft ein beliebiges Monatspaar allein durch Zufall so weit über dem Rest liegt wie September und Oktober. 1832 solche Ziehungen, und der gemessene Wert liegt mitten im Feld: Der Median der Zufallsziehungen liegt bei 1,004, das 95-Prozent-Quantil bei 1,084 — und 1,059 liegt darunter. Verschiebungen um Vielfache von zwölf Monaten fallen dabei heraus, weil sie den Kalender wieder zur Deckung bringen und damit gar nichts verwürfeln würden.

Ein Detail entscheidet hier mit, und es ist kein technisches: Gerechnet wird am Index selbst, nicht an einem ETF. Dessen Dividendenbereinigung trägt ausgerechnet in vier Kalendermonaten künstliche Sprünge in die Renditereihe, und zwei davon sind die getesteten. Wer die Regel an SPY prüft, misst teilweise die Ausschüttungstermine mit — ein erster Anlauf von uns tat genau das und kam auf ein anderes Vorzeichen.

Was bleibt, ist ein Erinnerungseffekt. Oktober 1929, Oktober 1987, Oktober 2008: Einzelne Monate prägen das Bild, das durchschnittliche Niveau prägen sie nicht. Genau deshalb steht in der Rechnung der Median und nicht der Mittelwert. → [Monatsprofil der Volatilität für über 300 Ticker](/vola-saisonalitaet)

### Kündigt ein Markt die Bewegung eines anderen an?

Nach dieser Messung nicht. Die Vorstellung ist eingängig: Wenn sich ein Markt ungewöhnlich stark bewegt hat, müsste danach in einem verwandten Markt etwas passieren. Entscheidend ist das **danach** — eine gleichzeitige Korrelation ist keine Prognose.

Wir haben daraus eine vorab festgelegte Testfamilie gebildet. 18 Märkte über Aktien, Sektoren, Rohstoffe, Anleihen und Krypto; als Ereignis gilt eine Zehn-Tage-Bewegung im obersten Zehntel der eigenen Historie; gemessen wird die Rendite des Zielmarkts über die folgenden zehn Handelstage. Eine Zelle zählt nur, wenn sie mindestens 20 Ereignisse **in jeder Hälfte** des Zeitraums hat und in beiden Hälften in dieselbe Richtung zeigt. Das ergibt 556 auswertbare Zellen, davon 470 in der Primärfamilie.

**Keine hält.** Nicht eine übersteht die Korrektur dafür, wie viele Fragen gestellt wurden.

Zwei Entscheidungen an diesem Aufbau sind wichtiger als das Ergebnis. Erstens zählt nur, was über eine Kategoriegrenze geht: Dass der Dow dem S&P folgt, ist keine Intermarket-Hypothese, sondern derselbe Markt mit anderem Namen. Die Trennung läuft über die Kategorie und nicht über die gemessene Korrelation — sonst wäre schon die Wahl der Testfamilie eine Suche nach dem Ergebnis. Zweitens standen beide Regeln fest, bevor wir das Ergebnis gesehen haben. Die stärkste Zelle im ganzen Feld — Silber abwärts, danach Versorger, t = 4,09 — reißt die Schranke und scheitert an der Ereigniszahl je Hälfte. Ohne diese Auflage stünde dort jetzt ein Treffer.

Die Korrektur ist der Punkt. Bei 470 Tests sind rund 24 Zufallstreffer zu erwarten, selbst wenn überhaupt nichts los ist. Wer sie einzeln herausgreift und zeigt, zeigt Rauschen mit einem p-Wert daneben. Genau so entstehen die meisten Intermarket-Regeln, die man liest.

Was bleibt, ist ein Hinweis unterhalb der Schwelle, und er ist der kohärenteste im Feld: Ein Anstieg langlaufender Anleihen zeigt gegen **sechs** Aktienziele gleichzeitig in dieselbe Richtung — S&P, Nasdaq, Technologie, Finanzen, Dow, Versorger — alle mit je 52 Ereignissen, alle in beiden Hälften gleichgerichtet, alle unter der Schranke. Ein Zufallstreffer verteilt sich nicht so systematisch über verwandte Ziele. Das ist kein Befund, sondern der Grund, warum die Anleihen weiter oben eine eigene Untersuchung bekommen haben. → [Die Matrix mit allen 470 Paarungen](/intermarket)

### Schlägt die Monthly-10-Strategie Kaufen und Halten?

Nein. Die Regel: nur an zehn ausgewählten Handelstagen im Monat investiert sein — den ersten vier, den Tagen neun bis zwölf und den letzten beiden. Über 32 Jahre gerechnet liefert sie **5,58 % pro Jahr gegen 10,71 %** für Kaufen-und-Halten und lag in 10 von 32 Jahren vorn.

Sie senkt dafür die Schwankung, von 18,84 auf 10,79 Prozent, und den größten Verlust von −55,2 auf −41,0 Prozent. Pro Risikoeinheit steht sie bei 0,52 gegen 0,57, also knapp hinten. Wer weniger Schwankung will, bekommt sie — aber er bezahlt dafür mehr als die halbe Rendite.

Am aufschlussreichsten ist, **wo** der Ertrag herkommt: aus der Monatsmitte, nicht vom Monatswechsel, auf den sich die Regel beruft. Die Begründung stimmt also selbst dann nicht, wenn man das Ergebnis gelten lässt. → [Monthly 10 im 32-Jahres-Backtest](/blog/monthly-10-strategie/)

## Was ein Muster ist, aber kein Test

Drei Auswertungen zeigen ein Muster, das die Stichprobe nicht trägt. Sie stehen hier ohne p-Wert, weil ein p-Wert an dieser Stelle mehr verspricht, als er halten kann.

### Was ist der Pre-FOMC-Drift?

Der Tag vor einer Fed-Entscheidung liefert im Schnitt +0,131 %, der Entscheidungstag selbst +0,202 % — gegen +0,040 % an allen übrigen Tagen. Auf diese Tage entfallen rund 22 % der aufsummierten Tagesrendite bei einem Anteil von 6,6 % aller Handelstage. → [Pre-FOMC-Drift](/blog/pre-fomc-drift/)

### Was passiert mit einer Aktie bei Aufnahme in den S&P 500?

Zwanzig Handelstage nach der Ankündigung steht der Kurs +5,8 % höher, der Höchststand um den Wirksamkeitstag bei +7,8 %; 72 % der Fälle sind positiv. Bei 36 Ereignissen ist das ein gemittelter Pfad, kein Test. → [Index-Inklusions-Effekt](/index-effekt)

### Ist das Zwischenwahljahr anders als die übrigen drei?

Das zweite Jahr einer US-Amtszeit trägt den tiefsten Rückgang der vier, und auf diesen Tiefpunkt folgt im Mittel eine Erholung von +31 %. Rund zwanzig Zyklen seit 1950 sind zu wenige Beobachtungen für mehr als eine Beschreibung. → [Zwischenwahljahr 2026](/blog/zwischenwahljahr-2026-erholung-praesidentenzyklus/)

## Warum das Vorherfestlegen den Unterschied macht

Bei der Volatilitäts-Saisonalität standen *ein* Ticker und *ein* Monatspaar fest, bevor gerechnet wurde. Das klingt nach einer Formalie und ist der ganze Unterschied.

Hätte man frei wählen dürfen, wären zwölf Monate mal mehrere hundert Titel zur Auswahl gestanden. Bei so vielen Kombinationen ist ein auffälliges Ergebnis garantiert — nicht wahrscheinlich, garantiert. Man findet es, präsentiert es mit p-Wert, und der p-Wert ist dann eine Aussage über die Suche und nicht über den Markt.

Dasselbe in groß zeigt die Intermarket-Matrix: 470 Fragen, rund 24 erwartete Zufallstreffer, null belastbare. Wer nur die 24 zeigt, hat nichts gemessen, sondern ausgewählt.

## Was hier nicht steht

Eine Auswertung fehlt bewusst. Die Handelsrenditen von US-Kongressabgeordneten liegen gerechnet vor, stützen sich aber bisher auf zu wenige Ereignisse von zu wenigen Personen. Jede Aussage über „die Politiker" wäre eine Aussage über zwei von ihnen. Die Regel dafür stand vor der Rechnung fest: mindestens 100 Ereignisse von mindestens fünf Personen, sonst kein Urteil. Diese Schwelle ist derzeit nicht erreicht; die laufenden Meldungen sammeln sich unter [Congress Trades](/congress).

## Was diese Zahlen nicht sind

Keine Anlageberatung und keine Prognose. Drei Dinge gehören beim Lesen dazu:

Ein **signifikanter Effekt kann winzig sein**. Die 0,35 Prozentpunkte beim Pinning überleben keine Gebühren.

Ein **bedingter Effekt verschwindet ohne seine Bedingung**. Der Anleihen-Effekt gilt in unruhigen Phasen; in ruhigen liegt er exakt auf der Basisrate.

Und **vergangene Muster garantieren keine künftigen Ergebnisse** — am wenigsten dann, wenn viele Marktteilnehmer sich auf dasselbe Muster verlassen.

## Häufige Fragen

### Warum stehen die Regeln hier, die nicht funktionieren?

Weil sie dieselbe Arbeit gekostet haben und denselben Wert haben. Die Fünf-Prozent-Regel bei Bitcoin fällt erst auf, wenn jemand nachrechnet, dass fünf Prozent dort der Median aller Zehn-Tage-Bewegungen sind. Eine Regel aus dem Verkehr zu ziehen ist ein Ergebnis.

### Was heißt „vorab festgelegt"?

Dass Ticker, Zeitraum, Schwelle und Messgröße feststanden, bevor gerechnet wurde. Wer erst rechnet und dann die Variante auswählt, die am besten aussieht, findet immer etwas. Die Zahl der geprüften Varianten gehört deshalb zu jedem Ergebnis dazu — sie entscheidet darüber, wie ein p-Wert zu lesen ist.

### Sind die belegten Effekte handelbar?

Das ist eine andere Frage als die, die hier beantwortet wird, und die Antwort fällt oft nüchtern aus. Ein Effekt muss nach Gebühren, Spread und Steuern übrig bleiben, und er muss groß genug sein, dass er nicht in der Streuung einzelner Jahre untergeht. Beim Pinning ist er das nicht. Beim Expected Move ist er es — deshalb ist Optionen-Verkaufen ein Geschäftsmodell und kein Geheimtipp.

### Warum unterscheidet ihr zwischen „nicht belegt" und „beschreibend"?

Weil es zwei verschiedene Aussagen sind. „Nicht belegt" heißt: gerechnet, und der Unterschied ist von Zufall nicht zu unterscheiden. „Beschreibend" heißt: Das Muster ist sichtbar, aber die Stichprobe trägt keinen Test. Im ersten Fall spricht die Messung gegen die Regel, im zweiten reicht sie für kein Urteil.

### Kommt etwas dazu?

Unregelmäßig. Eine Auswertung entsteht, wenn eine Frage konkret genug ist, um sie falsifizierbar zu stellen, und die Datenbasis sie trägt. Beides zusammen kommt seltener vor, als die Menge der kursierenden Börsenweisheiten vermuten lässt.

<!--
#### Social Media Snippet

**LinkedIn:**
Wir haben elf bekannte Börsenweisheiten an eigenen Kursdaten nachgerechnet, jede mit einer Frage, die vorher feststand.
Vier halten nicht:
— September und Oktober sind NICHT die unruhigen Monate. Faktor 1,059 gegenüber dem Rest des Jahres, p = 0,127 über 836 Monate ab 1957.
— „Bitcoin läuft voraus" scheitert an der eigenen Schwelle: die viel zitierten 5 % sind bei Bitcoin der MEDIAN aller Zehn-Tage-Bewegungen.
— Monthly 10 liefert 5,58 % p.a. gegen 10,71 % für Kaufen-und-Halten — und der Ertrag kommt aus der Monatsmitte, nicht vom Monatswechsel, auf den sich die Regel beruft.
— Von 470 vorab festgelegten Intermarket-Paarungen hält keine einzige.
Der letzte Punkt ist der lehrreichste: bei 470 Tests sind ~24 Zufallstreffer zu erwarten, auch wenn nichts los ist. Wer nur die 24 zeigt, hat nicht gemessen, sondern ausgewählt.
Keine Anlageberatung. → seasonalpha.ai

**Twitter/X:**
Elf Börsenweisheiten nachgerechnet. Vier halten nicht:
· September/Oktober unruhiger? Faktor 1,059, p = 0,127. Nein.
· Bitcoin läuft voraus? Die zitierten 5 % sind der MEDIAN aller 10-Tage-Bewegungen.
· Monthly 10: 5,58 % vs 10,71 % p.a.
· Intermarket: 0 von 470 Paarungen.
Keine Anlageberatung.
#Börse #Statistik #SeasonAlpha

#### Interne Verlinkung
- /vola-saisonalitaet (Monatsprofil der realisierten Volatilität)
- /intermarket (die Matrix mit allen 470 Paarungen)
- /skew (Vol-Regime-Radar, Expected Move)
- /index-effekt (Index-Inklusions-Studie)
- /congress (Congress Trades, Datenbasis noch zu schmal)

#### Content-Ideen (Folgeartikel)
- „Sell in May an sechs Märkten" — dieselbe Methodik auf die bekannteste Regel überhaupt
- „Wie groß muss ein Effekt sein, damit er Gebühren überlebt?" — Signifikanz gegen Effektstärke, durchgerechnet
- „Der Montagseffekt: was von ihm übrig ist" — Wochentagsmuster über vier Jahrzehnte
-->

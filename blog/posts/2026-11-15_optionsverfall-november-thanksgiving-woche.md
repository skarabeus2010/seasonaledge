---
title: "Optionsverfall im November: Die Verfallswoche und die Thanksgiving-Woche im S&P 500 seit 1973"
seo_title: "Optionsverfall November: OPEX-Woche und Thanksgiving"
slug: optionsverfall-november-thanksgiving-woche
date: 2026-11-15
category: marktausblick
tags: [opex, optionsverfall, thanksgiving, sp500, november-2026, verfallstag]
ticker: ^GSPC
status: published
description: "Optionsverfall im November: Die Thanksgiving-Woche nach dem Verfall brachte dem S&P 500 seit 1973 im Mittel +0,60 % (30 von 45 Jahren positiv), p = 0,066."
---

<!--
Keyword-Plan:
- Haupt-Keyword: Optionsverfall November / OPEX November
- Neben-Keywords: Verfallstag November 2026, Woche nach dem Optionsverfall, Thanksgiving-Woche Börse, Verfallswoche S&P 500,
  großer Verfall Dezember 2026, Triple Witching Dezember, VIX-Verfall November
- LSI: dritter Freitag, monatlicher Verfall, Feiertagswoche, Handelstage, Permutationstest, Median, Anteil positiver Wochen
- Abgrenzung: opex-effekt-sp500-third-friday-drift (Drift am Verfallstag), opex-zyklus-erklaert (vier Phasen, Phase 4 =
  Woche nach Verfall), pinning-verfallstag (Schlusskurse am Strike). Dieser Artikel: nur der November und die Kopplung
  von Verfall und Thanksgiving, mit eigener Rechnung 1973–2025.
- Faktenblatt: scripts/research/out/opex_november_thanksgiving_fakten.json (Datenstand ^GSPC bis 13.11.2026).
-->

## Verfall am Freitag, Feiertag in der Woche danach

Am Freitag, 20. November 2026, verfallen die monatlichen Optionen an den US-Börsen. Sechs Tage später ist Thanksgiving, die New Yorker Börse bleibt am Donnerstag geschlossen und schließt am Freitag danach früher. Diese Abfolge ist kein Zufall des Kalenders 2026: In **45 von 53 Jahren** zwischen 1973 und 2025 lag Thanksgiving genau sechs Tage nach dem November-Verfall, die Woche nach dem Verfall war also die Feiertagswoche.

Wir haben beide Wochen im S&P 500 nachgerechnet. Die Thanksgiving-Woche nach dem Verfall brachte im Mittel **+0,60 %** (Median +0,85 %, positiv in 30 von 45 Jahren). Die Woche nach dem Verfall in den übrigen elf Monaten lag im Mittel bei −0,03 % (n = 583). Der Abstand ist groß, statistisch aber nicht belegt (Permutationstest p = 0,066). Die Verfallswoche selbst fällt im November nicht aus dem Rahmen.

## Warum Verfall und Thanksgiving fast immer aufeinander folgen

Der monatliche Optionsverfall in den USA fällt auf den **dritten Freitag** eines Monats, im November also auf einen Tag zwischen dem 15. und dem 21. Thanksgiving ist der **vierte Donnerstag** im November und liegt zwischen dem 22. und dem 28.

Ist der 1. November kein Freitag, kommt der erste Donnerstag des Monats vor dem ersten Freitag. Der dritte Freitag folgt dann direkt auf den dritten Donnerstag, und der vierte Donnerstag liegt sechs Tage später. Nur wenn der 1. November ein Freitag ist, fällt der Verfall auf den 15. und Thanksgiving auf den 28.: Dann liegen 13 Tage dazwischen und eine gewöhnliche Woche schiebt sich dazwischen.

Zwischen 1973 und 2025 war das acht Mal der Fall: 1974, 1985, 1991, 1996, 2002, 2013, 2019 und 2024. Das nächste Jahr mit 13 Tagen Abstand ist 2030.

Wie der Optionsverfall die Marktmechanik über den Monat prägt, steht in unserem Artikel zum [OPEX-Zyklus](/blog/opex-zyklus-erklaert/); die Woche nach dem Verfall ist dort Phase 4, die Auflösung der Absicherungen.

## So haben wir gerechnet

- **Daten:** S&P 500 als Kursindex (ohne Dividenden), Tagesrenditen aus der in SeasonAlpha gespeicherten Log-Rendite, eingefroren mit dem Schluss vom 13.11.2026. Ausgewertet werden die 636 Monate von Januar 1973 bis Dezember 2025.
- **Verfallstag:** ab Februar 2015 der von der Cboe veröffentlichte Verfallstermin, davor der dritte Freitag nach Regel (bei Börsenschließung der Handelstag davor). In keinem November musste der Termin verschoben werden.
- **Verfallswoche:** die Handelstage der Kalenderwoche bis einschließlich Verfallstag, gemessen vom letzten Schluss der Vorwoche bis zum Schluss am Verfallstag.
- **Woche danach:** die Handelstage der folgenden Kalenderwoche, gemessen vom Schluss am Verfallstag bis zum letzten Schluss dieser Woche. In den 45 Jahren mit sechs Tagen Abstand sind das genau die vier Handelstage der Thanksgiving-Woche.
- **Test:** Permutationstest auf die Differenz der Mittelwerte (20.000 Durchläufe, zweiseitig), zur Kontrolle der Welch-t-Test. Was ein p-Wert aussagt und was nicht, erklärt unser [Artikel zum p-Wert](/blog/p-wert-erklaert/).

## Die Verfallswoche im November gegen die übrigen Monate

Die Woche bis zum November-Verfall verläuft unauffällig bis leicht schwächer als in anderen Monaten.

| Verfallswoche | n | Mittel | Median | positiv |
|---|---|---|---|---|
| November | 53 | −0,04 % | +0,04 % | 28 von 53 (52,8 %) |
| übrige Monate | 583 | +0,23 % | +0,39 % | 334 von 583 (57,3 %) |

Die Differenz der Mittelwerte beträgt −0,27 Prozentpunkte, mit t = −0,88 und p = 0,43 im Permutationstest. Ein eigener November-Effekt in der Verfallswoche ist damit **nicht belegt**. In beiden Hälften des Zeitraums (1973–1999 und 2000–2025) liegt der November leicht unter den übrigen Monaten, jeweils weit von einer belastbaren Aussage entfernt (p = 0,75 und p = 0,45).

Die bekannte Aufwärtsdrift am Verfallstag selbst behandelt unser Artikel zum [OPEX-Effekt im S&P 500](/blog/opex-effekt-sp500-third-friday-drift/); dieser Artikel misst ganze Wochen.

![Mittlerer kumulierter Verlauf des S&P 500 von fünf Handelstagen vor dem Optionsverfall bis vier Handelstage danach: November mit Thanksgiving in der Folgewoche (n = 45) gegen die übrigen Monate (n = 583), 1973 bis 2025](opex-november-thanksgiving/1_pfad_de.png)

Der Chart zeigt den mittleren Verlauf von fünf Handelstagen vor dem Verfall (= 100) bis vier Handelstage danach. In den 45 Novembern mit Thanksgiving in der Folgewoche stand der Index am Tag vor dem Verfall im Mittel bei 99,75 und am Verfallstag bei 99,99. Vier Handelstage nach dem Verfall, also am Freitag nach Thanksgiving, lag er bei 100,57. In den übrigen Monaten verläuft die Linie flacher und endet bei 100,21.

## Die Woche danach: Feiertagswoche gegen die übliche Woche nach dem Verfall

| Woche nach dem Verfall | n | Mittel | Median | positiv |
|---|---|---|---|---|
| November, Folgewoche = Thanksgiving | 45 | +0,60 % | +0,85 % | 30 von 45 (66,7 %) |
| übrige Monate | 583 | −0,03 % | +0,14 % | 305 von 583 (52,3 %) |
| alle Kalenderwochen 1973–2025 | 2.766 | +0,17 % | +0,31 % | 1.561 von 2.766 (56,4 %) |

Die Thanksgiving-Woche lag im Mittel 0,63 Prozentpunkte über der üblichen Woche nach dem Verfall. Der Permutationstest ergibt p = 0,066, der Welch-t-Test p = 0,11 (t = 1,62). Beide liegen über der Schwelle von 0,05: Der Unterschied ist **nicht belegt**, auch wenn die Richtung in beiden Hälften des Zeitraums dieselbe ist (1973–1999: +0,39 % gegen −0,15 %, p = 0,22; 2000–2025: +0,82 % gegen +0,10 %, p = 0,16).

Die Thanksgiving-Woche hat nur vier Handelstage, die meisten anderen Wochen fünf (486 der 583 Vergleichswochen). Pro Handelstag gerechnet kommt die Feiertagswoche auf +0,15 % gegen −0,004 %. Der Permutationstest liefert dafür p = 0,035, der Welch-t-Test p = 0,12. Je nach Test liegt der Wert knapp unter oder über der Schwelle; als Beleg reicht das nicht.

![Mittlere und mediane Rendite in der Woche nach dem Optionsverfall: November mit Thanksgiving in der Folgewoche (n = 45), November mit 13 Tagen Abstand (n = 8), übrige Monate (n = 583) und alle Kalenderwochen (n = 2.766), 1973 bis 2025](opex-november-thanksgiving/2_woche_danach_de.png)

Zum Vergleich: Die Woche nach dem Verfall war in den übrigen Monaten im Mittel schwächer als eine beliebige Kalenderwoche (−0,03 % gegen +0,17 %, p = 0,051 im Permutationstest). Die beiden Gruppen überschneiden sich, weil jede Woche nach einem Verfall auch eine Kalenderwoche ist. Der Wert ist deshalb nur ein Hinweis.

Woher die Stärke der Thanksgiving-Woche kommt, lässt sich mit diesen Daten nicht trennen. Über alle 53 Jahre gerechnet, also auch in den acht Jahren mit 13 Tagen Abstand, brachte die Thanksgiving-Woche im Mittel +0,61 % (Median +0,85 %, positiv in 37 von 53 Jahren). Gegen alle Kalenderwochen ist auch das nicht belegt (p = 0,17). Der Handelstag vor einem Feiertag gilt in der Forschung seit Langem als freundlich; mehr dazu in unserem Artikel zu [Thanksgiving und Black Friday an der Börse](/blog/thanksgiving-boerse-black-friday/).

## Die Jahre mit 13 Tagen Abstand

In den acht Jahren mit 13 Tagen Abstand trennen sich Verfall und Feiertag. Die Woche nach dem Verfall ist dann eine gewöhnliche Woche, die Thanksgiving-Woche folgt eine Woche später.

| Jahr | Verfall | Thanksgiving | Woche nach dem Verfall | Thanksgiving-Woche |
|---|---|---|---|---|
| 1974 | 15.11. | 28.11. | −4,19 % | +1,55 % |
| 1985 | 15.11. | 28.11. | +1,72 % | +0,32 % |
| 1991 | 15.11. | 28.11. | −1,69 % | −0,24 % |
| 1996 | 15.11. | 28.11. | +1,51 % | +1,11 % |
| 2002 | 15.11. | 28.11. | +2,28 % | +0,62 % |
| 2013 | 15.11. | 28.11. | +0,37 % | +0,06 % |
| 2019 | 15.11. | 28.11. | −0,33 % | +0,99 % |
| 2024 | 15.11. | 28.11. | +1,68 % | +1,06 % |

Die Woche nach dem Verfall kam in diesen Jahren im Mittel auf +0,17 % (Median +0,94 %, positiv in 5 von 8). Die Thanksgiving-Woche lag im Mittel bei +0,68 % (Median +0,80 %) und war in 7 von 8 Jahren positiv. Mit acht Fällen ist die Gruppe zu klein für einen Test; sie zeigt nur, dass die Thanksgiving-Woche auch ohne direkt vorausgehenden Verfall meist positiv verlief.

## Termine 2026

| Termin | Datum 2026 |
|---|---|
| VIX-Settlement (Futures, Kontrakt November) | Mittwoch, 18.11. |
| Monatlicher Optionsverfall | Freitag, 20.11. |
| Thanksgiving, NYSE geschlossen | Donnerstag, 26.11. |
| Verkürzter Handel (Schluss 13:00 Uhr New Yorker Zeit) | Freitag, 27.11. |
| Großer Verfall (Triple Witching) | Freitag, 18.12. |

Der 20. November ist ein **gewöhnlicher monatlicher Verfall**. Triple Witching, der gleichzeitige Verfall von Index-Futures, Index-Optionen und Aktienoptionen, findet nur im März, Juni, September und Dezember statt; der nächste ist am 18. Dezember. Alle Termine mit Feiertagsregeln zeigen die Seiten [Optionsverfall](/opex) und [VIXpiration](/vixpiration) sowie der [Marktkalender](/kalender).

## Was die Forschung zu Verfallstagen sagt

Hans Stoll und Robert Whaley beschrieben Ende der 1980er-Jahre erhöhte Umsätze und Kursumkehrungen an Tagen, an denen Index-Futures und Index-Optionen gemeinsam verfielen. Ni, Pearson und Poteshman zeigten 2005, dass Einzelaktien mit regem Optionshandel am Verfallstag häufiger nahe einem Basispreis schließen. Unsere eigene Auswertung zu Schlusskursen am Strike steht im Artikel zum [Pinning am Verfallstag](/blog/pinning-verfallstag/).

Für die Wochen um den November-Verfall gibt es keine Studie, die den Feiertag vom Verfall trennt. Unsere Zahlen können das ebenfalls nicht: In 45 von 53 Jahren fallen beide Ereignisse zusammen.

## Grenzen dieser Auswertung

- **Kein Beleg:** Kein Vergleich in diesem Artikel unterschreitet in beiden Tests die Schwelle von p = 0,05. Die Thanksgiving-Woche lag im Mittel klar vorn, die Streuung einzelner Wochen ist aber groß (Standardabweichung rund 2,5 % in der November-Gruppe).
- **Verfall oder Feiertag:** Weil Verfall und Thanksgiving fast immer zusammenfallen, lässt sich die Stärke der Woche keinem der beiden Ereignisse zuordnen. Die acht Jahre mit 13 Tagen Abstand sind dafür zu wenige.
- **Frühe Jahre:** Börsennotierte Aktienoptionen gibt es in den USA seit 1973, Optionen auf den S&P 500 selbst erst seit 1983. In den ersten Jahren der Reihe hatte der Verfall deshalb weniger Gewicht im Index.
- **Kursindex:** Gerechnet ist ohne Dividenden und ohne Kosten. Bei einer Woche macht das wenig aus, die Zahlen sind trotzdem keine erzielbaren Renditen.
- **Vergangenheit:** 45 Jahre sind eine kleine Stichprobe für ein Wochenmuster. Ein einzelner Kurseinbruch in der Feiertagswoche kann das Mittel deutlich verschieben.

## Was das für Anleger heißt

Die Woche bis zum November-Verfall unterscheidet sich historisch kaum von anderen Verfallswochen. Die Woche danach war im November meist freundlicher als in anderen Monaten, weil sie fast immer die Thanksgiving-Woche ist. Ob der Feiertag, das Ende des Verfalls oder beides dahintersteht, beantworten die Daten nicht.

Für 2026 heißt das: Am 18. November wird der VIX abgerechnet, am 20. November verfallen die Monatsoptionen, und die folgende Woche hat nur dreieinhalb Handelstage. Der größere Termin für Absicherungen und Positionswechsel ist der 18. Dezember. Ein Handelssignal ergibt sich aus diesen Zahlen nicht.

## Häufige Fragen

### Wann ist der Optionsverfall im November 2026?

Am Freitag, 20. November 2026. Das ist der dritte Freitag des Monats und der Tag, an dem die monatlichen US-Aktien- und Indexoptionen verfallen. Das Settlement des VIX für den November-Kontrakt ist zwei Tage früher, am Mittwoch, 18. November.

### Ist der 20. November 2026 Triple Witching?

Nein. Triple Witching gibt es nur in den Quartalsmonaten März, Juni, September und Dezember. Am 20. November verfallen die monatlichen Optionen, der nächste große Quartalsverfall ist am Freitag, 18. Dezember 2026.

### Ist die Woche nach dem Optionsverfall schwächer?

In den Monaten außer November lag die Woche nach dem Verfall im S&P 500 von 1973 bis 2025 im Mittel bei −0,03 % (n = 583), etwas unter einer beliebigen Kalenderwoche mit +0,17 %. Im November, wenn Thanksgiving in diese Woche fällt, waren es +0,60 % (n = 45). Beide Unterschiede sind statistisch nicht belegt.

### Warum liegt der Optionsverfall fast immer vor Thanksgiving?

Der Verfall fällt auf den dritten Freitag, Thanksgiving auf den vierten Donnerstag im November. Außer wenn der 1. November ein Freitag ist, folgt der vierte Donnerstag genau sechs Tage auf den dritten Freitag. Zwischen 1973 und 2025 war das in 45 von 53 Jahren so, zuletzt lagen 2024 dreizehn Tage dazwischen.

### Wann ist der nächste große Verfall?

Am Freitag, 18. Dezember 2026. An diesem Triple-Witching-Tag verfallen Quartalsoptionen und Index-Futures gemeinsam, das Volumen ist deutlich größer als an einem monatlichen Termin. Die Termine stehen auf unserer Seite zum [Optionsverfall](/opex).

<!--
#### Social Media Snippet

**LinkedIn:** Am 20.11. verfallen die monatlichen US-Optionen, sechs Tage später ist Thanksgiving. Diese Abfolge gab es in 45 von 53 Jahren seit 1973. Die Woche nach dem Verfall war im November im Mittel +0,60 % (Median +0,85 %, 30 von 45 positiv), in den übrigen Monaten −0,03 % (n = 583). Statistisch nicht belegt (p = 0,066), und Verfall und Feiertag lassen sich nicht trennen. Wie lest ihr die Feiertagswoche? https://seasonalpha.ai/blog/optionsverfall-november-thanksgiving-woche/

**Twitter/X:** Optionsverfall im November liegt fast immer 6 Tage vor Thanksgiving (45 von 53 Jahren). S&P 500 in der Woche danach: +0,60 % im Mittel (n=45) gegen −0,03 % in anderen Monaten (n=583). p = 0,066, also nicht belegt. #Börse #OPEX #SeasonAlpha

#### Interne Verlinkung
- /opex, /vixpiration, /kalender
- /blog/opex-zyklus-erklaert/ (Phase 4), /blog/opex-effekt-sp500-third-friday-drift/, /blog/pinning-verfallstag/, /blog/p-wert-erklaert/
- Link auf /blog/thanksgiving-boerse-black-friday/ gesetzt (2026-11-21)

#### Content-Ideen (Folgeartikel)
- Triple Witching im Dezember: Verfallswoche und Weihnachtswoche
- Woche nach dem Verfall über alle Monate: Phase 4 des OPEX-Zyklus mit eigener Rechnung
- Feiertagswochen im S&P 500 im Vergleich (Thanksgiving, Weihnachten, Independence Day)
-->

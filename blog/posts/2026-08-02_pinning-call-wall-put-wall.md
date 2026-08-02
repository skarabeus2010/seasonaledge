---
title: 'Pinning erklärt: Warum Aktienkurse am Verfallstag an Strikes „kleben“'
seo_title: "Pinning & Call-Wall/Put-Wall am Optionsverfall"
slug: pinning-call-wall-put-wall
date: 2026-08-02
category: education
tags: [pinning, call-wall, put-wall, optionsverfall, gamma-exposure, dealer-positioning, opex, market-maker, saisonalitaet]
description: "Pinning erklärt: Warum Aktienkurse am Optionsverfall an Strikes kleben und wie du Call-Wall und Put-Wall richtig liest — fundiert durch JFE-Forschung."
ticker: SPY
status: published
---

<!--
Keyword-Plan:
- Haupt-Keyword: Pinning Optionen
- Neben-Keywords: Call Wall Put Wall erklärt, Optionsverfall, Strike Pinning, Gamma Exposure, Dealer Positioning, Zero-Gamma-Flip, Open Interest, Market Maker Hedging, dritter Freitag
- Long-Tail: warum kleben Aktienkurse an Strikes, was ist eine Call Wall, Put Wall Bedeutung, Pinning am Verfallstag erklärt, Kurs zieht zum Strike
- LSI: Delta-Hedging, Absicherung, implizite Volatilität, Triple Witching, S&P 500, Marktmikrostruktur, Journal of Financial Economics, offenes Interesse
- Suchintention: Privatanleger wollen verstehen, warum Kurse am Optionsverfall an bestimmten Strikes hängen und wie man Call-/Put-Walls liest — ohne Signal-Hype
-->

## Kleben Aktienkurse wirklich an bestimmten Preisen?

Am Optionsverfallstag passiert regelmäßig etwas Merkwürdiges: Viele Aktien schließen auffällig nah an „runden" Optionspreisen — den sogenannten Strikes. Dieses Phänomen heißt **Pinning**, und es ist kein Börsen-Mythos. Es ist seit über 20 Jahren in den führenden Finanzjournalen dokumentiert.

Ni, Pearson und Poteshman zeigten bereits 2005 im *Journal of Financial Economics*, dass Schlusskurse optionierter Aktien am Verfallstag messbar zu den Strike-Preisen gezogen werden. In diesem Artikel erklären wir, **warum** das passiert, wie du **Call-Wall** und **Put-Wall** liest — und, ganz wichtig, wo die Grenzen dieser Kennzahlen liegen.

## Was ist Pinning? Der Mechanismus hinter dem „Kleben"

Pinning entsteht durch das Absicherungsverhalten der Market Maker — bei uns kurz „Dealer" genannt. Wenn du eine Option handelst, steht dir ein Dealer gegenüber, der kein Richtungsrisiko tragen will. Er neutralisiert sein Risiko im Basiswert laufend. Das nennt man **Delta-Hedging**.

Je näher der Verfall rückt und je näher der Kurs an einem stark gehandelten Strike liegt, desto empfindlicher wird dieses Delta. Schon kleine Kursbewegungen zwingen den Dealer, Aktien zu kaufen oder zu verkaufen — und zwar **gegen** die Bewegung. Steigt der Kurs über den Strike, verkauft er; fällt er darunter, kauft er. Dieses Gegensteuern wirkt wie ein Gummiband, das den Kurs immer wieder zum Strike zurückzieht.

Avellaneda, Kasyan und Lipkin gossen diesen Rückkopplungseffekt 2011 in ein mathematisches Modell. Ihr Kernergebnis in einem Satz: Die **Wahrscheinlichkeit für Pinning steigt mit dem offenen Interesse** (Open Interest) an einem Strike — und sinkt, je leichter sich der Kurs bewegen lässt (Price Impact). Vereinfacht: viel offenes Interesse plus wenig Liquidität ergibt einen starken Pin.

## Call-Wall und Put-Wall: So definiert SeasonAlpha die „Mauern"

Aus dem gebündelten Dealer-Gamma je Ausübungspreis leiten wir drei Referenzstrikes ab. Sie zeigen, wo die Absicherungsaktivität am dichtesten ist:

- **Call-Wall** — der Strike **oberhalb** des aktuellen Kurses mit dem größten positiven Netto-Dealer-Gamma. Wirkt oft als Widerstands-Referenz.
- **Put-Wall** — der Strike **unterhalb** des Kurses mit dem stärksten Netto-Gamma auf der Absicherungsseite. Wirkt oft als Support-Referenz.
- **Absolute-Gamma-Strike** — der Strike mit dem insgesamt größten Gamma-Betrag. Das ist der „magnetischste" Pin, ganz gleich ob über oder unter dem Kurs.

Dazu kommt der **Zero-Gamma-Flip**: der Kursstand, an dem das gebündelte Netto-Gamma sein Vorzeichen wechselt — die Grenze zwischen dämpfendem und verstärkendem Dealer-Verhalten.

Ein konkretes, klar datiertes Beispiel: Am 2. August 2026 lag die Call-Wall des **SPY** bei 749, die Put-Wall bei 730 und der Zero-Gamma-Flip bei rund 748 — bei einem Kurs von etwa 747. Der SPY klebte also direkt unter Call-Wall und Zero-Gamma-Flip. Das ist eine Momentaufnahme, kein Ausblick: Diese Werte ändern sich täglich mit dem offenen Interesse.

## Was die Forschung belegt — und wie stark

Pinning gehört zu den am besten dokumentierten Beobachtungen der Marktmikrostruktur. Drei Arbeiten bilden das Fundament — zwei davon im *Journal of Financial Economics*, einem der drei renommiertesten Finanzjournale der Welt.

| Studie | Ebene | Kernbefund |
|--------|-------|-----------|
| **Ni, Pearson & Poteshman (2005), JFE** | Einzelaktien | Schlusskurse clustern an Strikes; ~16,5 bps Renditeverschiebung, aggregiert ~9 Mrd. $ |
| **Golez & Jackwerth (2012), JFE** | Index / Future | S&P-500-Future pinnt zum ATM-Strike; ≥ 115 Mio. $ Nominal je Verfall |
| **Avellaneda, Kasyan & Lipkin (2011)** | Modell | Pinning-Wahrscheinlichkeit ∝ Open Interest ÷ Price Impact |

### Einzelaktien: Ni, Pearson & Poteshman (2005)

Die kanonische Studie. Sie untersuchte tausende US-Aktien mit börsengehandelten Optionen und fand ein klares Clustering der Schlusskurse an Strikes zum Verfall. Der gemessene Renditeeffekt lag im Schnitt bei rund **16,5 Basispunkten** — aggregiert über etwa **9 Milliarden Dollar** Marktkapitalisierung. Als Ursachen nennen die Autoren das Hedge-Rebalancing der Market Maker sowie, in Teilen, gezielte Einflussnahme großer Options-Trader.

### Index-Ebene: Golez & Jackwerth (2012)

Sieben Jahre später weiteten Golez und Jackwerth den Befund auf den **S&P-500-Future** aus — also genau die Index-Ebene, auf der unsere SPY- und QQQ-Walls arbeiten. Am Verfall serieller Optionen wird der Future zum geldnächsten Strike (ATM) gezogen; die Nominal-Verschiebung beträgt mindestens **115 Millionen Dollar** je Verfall. Spannend ist ihr Nebenbefund: Unmittelbar vor dem Index-Options-Verfall wird der Kurs teils sogar **weg** vom Strike gedrückt (Anti-Cross-Pinning). Ein deutlicher Hinweis, dass Pinning kein simpler Dauermagnet ist.

### Das Modell: Avellaneda, Kasyan & Lipkin (2011)

Sie lieferten die Theorie zur Empirie: ein Feedback-Modell, in dem der Options-Hedge-Fluss den Kurs beeinflusst — und der Kurs wiederum den Hedge-Fluss. Pinning ist demnach kein Zufall, sondern eine natürliche Folge konzentrierten offenen Interesses. Genau diese Konzentration bilden unsere Walls ab.

## Der saisonale Rahmen: Der Verfallszyklus wiederholt sich jeden Monat

Pinning ist ein Ereignis des Kalenders. Der große monatliche Optionsverfall liegt immer am dritten Freitag, und viermal im Jahr — im **März, Juni, September und Dezember** — fällt er mit dem Verfall von Index-Futures und Index-Optionen zusammen (**Triple Witching**). Dann ist das offene Interesse am größten, und genau dort sind Pinning- und Wall-Effekte tendenziell am stärksten.

{{chart:monthly_cycle:SPY:20}}

Der Chart zeigt **keine** Walls — die liegen live und tagesaktuell auf unserer Dealer-Positioning-Seite. Er zeigt den saisonalen Monatsrhythmus des SPY über 20 Jahre (normierte Renditen, jedes Jahr startet bei 100), in den sich der Verfallszyklus jeden Monat einbettet. Der aktuelle Monat ist hervorgehoben. So siehst du das Zusammenspiel: Der Kalender liefert das Muster, die Dealer-Positionierung liefert den Mechanismus darunter.

Für Privatanleger heißt das: Ein Wall-Strike ist keine isolierte Zahl. Er entfaltet seine größte Bedeutung rund um die vier Triple-Witching-Termine, wenn sich das meiste offene Interesse an denselben Strikes ballt.

## Grenzen und Gegenbeispiele: Was Walls NICHT sind

Dealer Positioning ist ein YMYL-Thema (Your Money or Your Life). Deshalb sind wir hier bewusst transparent, statt eine Präzision vorzutäuschen, die die Datenbasis nicht hergibt:

- **Walls sind Konzentrations-Referenzen, keine Barrieren.** Es gibt keine Garantie, dass der Kurs an ihnen dreht. Sie markieren nur, wo Hedging-Aktivität am dichtesten liegt — **kein Kauf- oder Verkaufssignal**.
- **Der Effekt ist statistisch und klein.** 16,5 Basispunkte sind ein Mittelwert über tausende Fälle, kein handelbarer Einzeltag-Ausschlag. Pinning erklärt eine Tendenz, keine Einzelbewegung.
- **Kurse können auch weggedrückt werden.** Golez und Jackwerth dokumentierten das Anti-Cross-Pinning vor Index-Verfällen. Der „Magnet" kann sich also umkehren.
- **Wir nutzen eine naive Dealer-Heuristik** (Annahme: long Calls, short Puts) auf **EOD-Daten von Yahoo** — Open Interest und implizite Vola am Handelsende. Anbieter wie SpotGamma oder SqueezeMetrics arbeiten mit proprietären Inventory-Modellen samt Intraday- und 0DTE-Daten. **Unsere Zahlen weichen von deren Zahlen ab**; sie sind eine belastbare Näherung, kein Abbild echter Dealer-Bücher.
- **Nur US-gelistete Basiswerte.** Für den DAX, `^GDAXI` oder deutsche Aktien mit `.DE`-Endung liefert Yahoo keine Optionskette — dort gibt es kein Wall-Bild. Nutze SPY oder QQQ als liquide Referenz für den Gesamtmarkt.

Diese Grenzen sind kein Makel, sondern Teil einer ehrlichen Methode. Wer Walls ernst nimmt, muss wissen, wie belastbar die Datenbasis ist.

## So liest du Call-Wall und Put-Wall in der Praxis

Das Feature findest du auf der Seite **[Dealer Positioning](/dealer-positioning)**. Dort siehst du für die wichtigsten US-Basiswerte den aktuellen Kurs im Verhältnis zu Call-Wall, Put-Wall, Absolute-Gamma-Strike und Zero-Gamma-Flip. Als Faustregel gilt: Liegt der Kurs **zwischen** Put-Wall und Call-Wall, ist eine engere Handelsspanne wahrscheinlicher; nähert er sich einer Wall, steigt die Aufmerksamkeit für eine mögliche Reaktion — ohne Gewähr.

Den größten Mehrwert bekommst du in Kombination mit dem Kalender. Wirf in der Woche vor dem [Optionsverfall](/opex) einen Blick auf das Wall-Bild und achte besonders auf die vier Triple-Witching-Termine. So verbindest du das saisonale Muster mit dem Mechanismus, der es antreibt. Wer tiefer einsteigen will, findet die Grundlagen zu Gamma, Vanna und Charm in unserem Beitrag [Dealer Positioning erklärt](/blog/dealer-positioning-gamma-vanna-charm).

Ein Hinweis zur Interpretation: Einzelaktien-Gamma ist deutlich verrauschter als Index-Gamma, weil Dealer dort weniger dominant sind. Für belastbare Aussagen sind die großen Index-ETFs SPY und QQQ der beste Ausgangspunkt.

## Fazit

Pinning ist kein Aberglaube, sondern eine der am besten belegten Beobachtungen der Marktmikrostruktur — von den Einzelaktien (Ni, Pearson & Poteshman) über den S&P-500-Future (Golez & Jackwerth) bis ins Modell (Avellaneda, Kasyan & Lipkin). Call-Wall und Put-Wall machen sichtbar, wo sich das offene Interesse ballt und die Dealer-Absicherung am dichtesten ist.

Aber: Walls sind Referenzen, keine Barrieren. Der Effekt ist real, aber klein, und unsere Zahlen sind eine ehrliche Näherung auf EOD-Daten, kein Insiderblick in die Dealer-Bücher. Genau darin liegt der Wert — du bekommst eine fundierte Orientierung, kein falsches Versprechen. Probiere es auf **[seasonalpha.ai/dealer-positioning](/dealer-positioning)** selbst aus.

## Häufige Fragen

### Was ist Pinning bei Optionen einfach erklärt?

Pinning beschreibt, dass Aktienkurse am Optionsverfallstag dazu neigen, nah an einem stark gehandelten Strike zu schließen. Ursache ist das Delta-Hedging der Market Maker, das den Kurs wie ein Gummiband zum Strike zurückzieht. Belegt ist der Effekt unter anderem durch Ni, Pearson & Poteshman (JFE 2005).

### Was ist der Unterschied zwischen Call-Wall und Put-Wall?

Die Call-Wall ist der Strike oberhalb des Kurses mit dem größten positiven Netto-Dealer-Gamma und wirkt oft als Widerstands-Referenz. Die Put-Wall liegt unterhalb des Kurses und wirkt oft als Support-Referenz. Beide markieren Zonen hoher Hedging-Aktivität, sind aber keine festen Barrieren.

### Sind Call-Wall und Put-Wall verlässliche Handelssignale?

Nein. Es sind Konzentrations-Referenzen, keine Garantien und kein Kauf- oder Verkaufssignal. Der Pinning-Effekt ist im Mittel klein (rund 16,5 Basispunkte), und starke Nachrichten oder Makro-Ereignisse überlagern das Bild jederzeit. Nutze Walls als Orientierung, nicht als Auslöser.

### Kann ich Call- und Put-Walls auch für den DAX sehen?

Nein. Unsere Datenquelle liefert nur für US-gelistete Basiswerte eine Optionskette. Für den DAX, `^GDAXI` oder deutsche Aktien mit `.DE`-Endung gibt es kein Wall-Bild. SPY und QQQ sind die liquideste Referenz für den Gesamtmarkt.

### Warum sind Pinning-Effekte an Triple-Witching-Tagen stärker?

Weil im März, Juni, September und Dezember der Verfall von Aktienoptionen, Index-Optionen und Index-Futures zusammenfällt. Dann ist das offene Interesse am größten, und je mehr offenes Interesse an einem Strike liegt, desto stärker ist laut Avellaneda et al. (2011) die Pinning-Wahrscheinlichkeit.

<!--
#### Social Media Snippet

**LinkedIn:** „Pinning" ist kein Börsen-Mythos: Seit Ni, Pearson & Poteshman (Journal of Financial Economics, 2005) ist belegt, dass Aktienkurse am Optionsverfall an Strikes kleben — im Schnitt ~16,5 bps, aggregiert ~9 Mrd. $. Golez & Jackwerth (2012) zeigten dasselbe für den S&P-500-Future. In unserem neuen Beitrag erklären wir den Mechanismus, wie man Call-Wall und Put-Wall liest — und wo die Grenzen liegen (Referenzen, keine Barrieren, kein Signal). Ehrlich gelabelt: naive Heuristik auf EOD-Daten, nur US-Werte. Wie nutzt du Wall-Levels in deiner Analyse? https://seasonalpha.ai/blog/pinning-call-wall-put-wall

**Twitter/X:** Kleben Aktienkurse am Verfallstag an Strikes? Ja — „Pinning" ist seit 2005 in Top-Journals belegt (Ni/Pearson/Poteshman, JFE: ~16,5 bps). Wir erklären Call-Wall & Put-Wall, mit dem, was die Forschung sagt — und was Walls NICHT sind. Kein Signal, ehrlich gelabelt. seasonalpha.ai/blog/pinning-call-wall-put-wall #Optionen #Pinning #OPEX

#### Interne Verlinkung
- /dealer-positioning (Haupt-Feature: Call/Put-Walls live)
- /opex (Optionsverfall-Kalender — direkter thematischer Nachbar)
- /blog/dealer-positioning-gamma-vanna-charm (Grundlagen Gamma/Vanna/Charm)
- /vixpiration (Vola-Zyklus rund um den Verfall einordnen)

#### Content-Ideen (Folgeartikel)
- „Pinning-Distanz gemessen: Wie nah schließt der S&P am nächsten großen Strike?" (Mini-Daten-Studie)
- „Zero-Gamma-Flip erklärt: der Kipppunkt zwischen ruhigem und wildem Markt"
- „Anti-Cross-Pinning: Wenn der Magnet abstößt statt anzieht"
-->

---
title: "Turn-of-Month-Effekt: totgesagt — und doch lebendig (im richtigen Fenster)"
seo_title: "Turn-of-Month-Effekt 2026: Lebt er noch?"
slug: turn-of-month-effekt-lebt-noch
date: 2026-06-14
category: education
tags: [turn-of-month, saisonalität, kalendereffekt, monatswechsel, s&p 500]
description: "Neue Forschung 2026 und unsere eigenen Daten zeigen: der Turn-of-Month-Effekt ist nicht tot — er hat nur das Zeitfenster gewechselt. Was das für Anleger heißt."
ticker: ^GSPC
status: published
---

<!--
Keyword-Plan:
- Haupt-Keyword: Turn-of-Month-Effekt
- Neben-Keywords: Monatswechsel Börse, Kalendereffekt Aktien, Saisonalität S&P 500, turn of the month, lebt der Turn-of-Month-Effekt noch
- LSI-Keywords: Arbitrage, Rebalancing, risk deferral, Win-Rate, Signifikanz, t-Wert
-->

## Ein totgesagter Effekt, der nicht sterben will

Der Turn-of-Month-Effekt — die Tendenz der Aktienmärkte, rund um den Monatswechsel überdurchschnittlich zuzulegen — gilt vielen als „weggehandelt". Doch eine neue Studie aus dem Jahr 2026 und ein Blick in unsere eigenen Daten zeichnen ein anderes Bild: Der Effekt **lebt** — er hat nur das **Zeitfenster gewechselt**.

Wir fassen hier die aktuelle Forschung zusammen und prüfen sie an 20 Jahren S&P-500-Daten.

## Was ist der Turn-of-Month-Effekt?

Seit den späten 1980er-Jahren dokumentiert die Finanzforschung, dass ein großer Teil der monatlichen Aktienrendite auf wenige Tage rund um den Monatsultimo entfällt — den letzten Handelstag eines Monats und die ersten Tage des Folgemonats. Eine vielzitierte Untersuchung dazu stammt von John McConnell und Wei Xu ([SSRN](https://www.ssrn.com/abstract=925589)). Wenn du die Grundlagen vertiefen willst, erklärt unser Artikel [Turn-of-Month-Effekt erklärt](/blog/turn-of-month-effekt-erklaert/), warum gerade diese Tage statistisch herausstechen.

Die gängige Erklärung: An Monatswechseln fließen Gehälter, Sparpläne und institutionelle Mittel in den Markt, und große Fonds rebalancieren ihre Portfolios.

## Die neue Forschung: Der Effekt besteht fort

In einer 2026 im *Journal of International Financial Markets, Institutions and Money* erschienenen Studie untersucht **Nuri Volkan Kayaçetin** den Turn-of-Month-Effekt in rund 30 Ländern über den Zeitraum 1994–2023 ([DOI](https://doi.org/10.1016/j.intfin.2026.102309)). Sein Ergebnis: Der Effekt besteht in nahezu allen untersuchten Märkten fort — mit Japan als Ausnahme. Laut Studie liegt die mittlere Rendite am Monatswechsel bei rund zehn Basispunkten gegenüber praktisch null an gewöhnlichen Tagen. Als Mechanismus nennt Kayaçetin **seltenes Rebalancing** und eine **aufgeschobene Risikoprämie** („risk deferral").

Eine praxisnahe Analyse des pseudonymen Quant-Autors **QuantSeeker** (Februar 2025) liefert das fehlende Puzzleteil ([Quelle](https://www.quantseeker.com/p/turn-of-the-month-strategies-do-they)): Das **klassische, enge Fenster** (letzter Handelstag plus die ersten drei Tage) ist bei US-Aktien **nicht mehr statistisch signifikant** — vermutlich weggearbeitet durch Arbitrage. Das **breitere Fenster** dagegen (drei Tage vor bis drei Tage nach dem Monatswechsel) zeigt weiterhin einen signifikanten Aufschlag von rund 5 bis 12 Basispunkten.

## Der Test mit unseren Daten

Genau diese Unterscheidung lässt sich auf SeasonAlpha nachrechnen. Der folgende Chart zeigt die durchschnittliche kumulierte Renditekurve des S&P 500 um den Monatswechsel (t0 = letzter Handelstag), über die letzten 20 Jahre.

{{chart:tom_effect:^GSPC:20}}

Und das Ergebnis bestätigt die Forschung verblüffend genau:

| Fenster | Ø Rendite | Trefferquote | t-Wert | Signifikant? |
|---------|-----------|--------------|--------|--------------|
| Klassisch (t0 bis t+3) | +0,14 % | 58 % | 1,18 | nein |
| Breit (t−3 bis t+3) | +0,50 % | 62 % | **3,15** | **ja (p < 0,01)** |

Das enge Fenster liefert über 245 Monatswechsel keinen statistisch belastbaren Vorteil mehr (t = 1,18). Das breite Fenster dagegen ist mit einem t-Wert von 3,15 klar signifikant. Der Monatswechsel-Effekt ist also nicht verschwunden — er beginnt nur **früher**, schon einige Tage vor dem Monatsultimo.

## Warum verschwindet ausgerechnet das enge Fenster?

Das ist ökonomisch logisch: Je bekannter und enger ein Muster, desto eher beuten Trader es aus, bis die Überrendite verschwindet. Das breitere Fenster ist schwerer „sauber" zu handeln — und genau dort hält sich der Effekt. Kayaçetins Mechanismus passt dazu: Wird der Aufschlag teils als verzögerte Risikoprämie gezahlt, lässt er sich nicht beliebig wegarbeiten.

## Was heißt das für Anleger?

Drei nüchterne Schlussfolgerungen:

- Ein Effekt, der „verschwindet", ist oft nur **falsch gemessen** — das Fenster entscheidet.
- Selbst das breite Fenster bringt im Schnitt einen **halben Prozentpunkt** — interessant als Kontext, aber kein Freifahrtschein. Transaktionskosten und Streuung fressen viel davon.
- Saisonale Muster gehören in einen **Werkzeugkasten**, nicht an dessen Spitze.

Auf seasonalpha.ai kannst du das selbst prüfen: Öffne **Turn-of-Month**, wähle einen Ticker und das Fenster — die Signifikanz-Anzeige (t-Wert, p-Wert, Win-Rate) zeigt dir sofort, ob der Effekt belastbar ist.

## Fazit

Der Turn-of-Month-Effekt ist ein Lehrstück: Aktuelle Forschung (Kayaçetin 2026) und unsere eigenen S&P-500-Daten zeigen übereinstimmend, dass er fortbesteht — aber im breiteren Zeitfenster, nicht im klassischen engen. Wer Kalendereffekte ernst nimmt, muss genau hinschauen, wie sie gemessen werden. Probiere es selbst auf seasonalpha.ai.

## Quellen

- Kayaçetin, N. V. (2026): *Infrequent rebalancing, risk deferral, and equity returns at the turn of the month.* Journal of International Financial Markets, Institutions and Money. [DOI](https://doi.org/10.1016/j.intfin.2026.102309)
- QuantSeeker (2025): *Turn-of-the-Month Strategies: Do They Still Work?* [quantseeker.com](https://www.quantseeker.com/p/turn-of-the-month-strategies-do-they)
- McConnell, J. J. & Xu, W.: *Equity Returns at the Turn of the Month.* [SSRN](https://www.ssrn.com/abstract=925589)
- Eigene Berechnung: SeasonAlpha, S&P 500 (^GSPC), 2006–2026, 245 Monatswechsel.

## Häufige Fragen

### Ist der Turn-of-Month-Effekt noch real?
Ja — sowohl eine Studie von 2026 (Kayaçetin) als auch unsere eigene Auswertung des S&P 500 finden einen statistisch signifikanten Effekt, allerdings im breiteren Fenster (drei Tage vor bis drei Tage nach dem Monatswechsel), nicht im klassischen engen.

### Warum funktioniert das klassische enge Fenster nicht mehr?
Vermutlich wurde es durch Arbitrage weggehandelt: Je bekannter und enger ein Muster, desto schneller verschwindet die Überrendite. In unseren Daten ist das enge Fenster mit einem t-Wert von 1,18 nicht mehr signifikant.

### Kann ich damit eine Strategie bauen?
Vorsicht. Der mittlere Aufschlag ist klein, und Transaktionskosten sowie Streuung zehren ihn schnell auf. Sinnvoller ist es, den Effekt als einen von mehreren Bausteinen zu sehen, nicht als alleiniges Signal.

### Gilt das auch außerhalb der USA?
Laut der Studie von Kayaçetin besteht der Effekt in rund 30 Ländern fort — mit Japan als bemerkenswerter Ausnahme. Auf seasonalpha.ai kannst du den DAX, den Dow und viele weitere Indizes selbst prüfen.

<!--
#### Social Media Snippet

**LinkedIn:** „Der Turn-of-Month-Effekt ist tot." Wirklich? 🤔 Eine neue Studie (Kayaçetin 2026) und unsere eigenen 20 Jahre S&P-500-Daten sagen: Er lebt — nur im breiteren Fenster. Das klassische enge Fenster (t-Wert 1,18) ist nicht mehr signifikant, das breite (t-Wert 3,15) schon. Ein schönes Beispiel, wie sehr die Messung über das Ergebnis entscheidet. Mehr auf seasonalpha.ai. #Börse #Saisonalität #SeasonAlpha #Kalendereffekt

**Twitter/X:** Turn-of-Month-Effekt tot? Neue Forschung 2026 + unsere S&P-Daten: Nein — nur das enge Fenster (t=1,18, ns) ist weggehandelt. Das breite (t-3 bis t+3) lebt: +0,50 %, t=3,15. 📊 seasonalpha.ai #Börse #Saisonalität #SeasonAlpha

#### Interne Verlinkung
- /tdom-analyse (Turn-of-Month selbst nachrechnen)
- /monatswechsel (Monatswechsel-Saisonalität im Detail)
- Blog: Google im Juli (verwandtes Saisonalitäts-Thema)

#### Content-Ideen (Folgeartikel)
- „Der Monatswechsel bei DAX und Dow: Wo lebt der Effekt, wo nicht?"
- „Warum Japan die Ausnahme ist: Turn-of-Month im Nikkei"
- „Kalendereffekte und Transaktionskosten: Was vom Edge übrig bleibt"
-->

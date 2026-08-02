---
title: "Dealer Positioning erklärt: Wie Gamma, Vanna und Charm die Saisonalität antreiben"
seo_title: "Dealer Positioning: Gamma, Vanna & Charm erklärt"
slug: dealer-positioning-gamma-vanna-charm
date: 2026-08-02
category: education
tags: [dealer-positioning, gamma-exposure, gex, vanna, charm, opex, zero-gamma, call-wall, put-wall, market-maker, saisonalitaet, optionsverfall]
description: "Dealer Positioning einfach erklärt: Gamma, Vanna und Charm zeigen, warum der OPEX-Effekt existiert. Aus dem Saison-Muster wird der Mechanismus dahinter."
ticker: SPY
status: draft
---

<!--
Keyword-Plan:
- Haupt-Keyword: Dealer Positioning
- Neben-Keywords: Gamma Exposure, GEX, Vanna, Charm, Zero-Gamma-Flip, Call-Wall, Put-Wall, Market-Maker-Hedging, OPEX-Effekt, Gamma-Regime
- Long-Tail: was ist Gamma Exposure, Dealer Positioning erklärt, warum steigt der Markt vor dem Optionsverfall, Call Wall Put Wall Bedeutung, long gamma short gamma Unterschied
- LSI: Optionsverfall, dritter Freitag, Triple Witching, Volatilität, Pinning, Market Maker, Skew, implizite Volatilität, Delta-Hedging, Saisonalität
- Suchintention: Privatanleger wollen verstehen, was Dealer-/Gamma-Positionierung ist und wie sie mit dem Optionsverfall/der Saisonalität zusammenhängt
-->

## Warum steigt der Markt so oft in der Woche vor dem Optionsverfall?

Wer die Saisonalität des S&P 500 kennt, sieht das Muster immer wieder: In der Woche vor dem dritten Freitag im Monat driftet der Markt tendenziell nach oben. **Dealer Positioning** liefert die Erklärung, die reine Kalender-Statistik nicht geben kann — den **Mechanismus** hinter dem Muster.

Genau darum geht es in unserem neuen Feature. Wir berechnen, wie Optionshändler (die „Dealer" oder Market Maker) positioniert sind — über die Kennzahlen **Gamma, Vanna und Charm**. Und wir verheiraten das mit unserem börsengenauen Saisonkalender. Aus „der Markt steigt oft vor OPEX" wird „der Markt steigt vor OPEX, weil Dealer ihre Absicherungen zurückkaufen müssen".

## Was ist Dealer Positioning überhaupt?

Wenn du eine Option kaufst, verkauft sie dir jemand — meist ein Market Maker. Dieser Dealer will kein Marktrisiko tragen, sondern nur an der Geld-Brief-Spanne verdienen. Also **sichert er seine Position im Basiswert ab** (Delta-Hedging). Kauft der Markt viele Calls, muss der Dealer Aktien kaufen; kauft der Markt Puts, verkauft er Aktien.

Das Entscheidende: Diese Absicherung ist nicht statisch. Sie ändert sich, wenn der Kurs sich bewegt, wenn die Volatilität schwankt und wenn Zeit vergeht. Genau diese Veränderungsraten messen die drei „Griechen":

- **Gamma** — wie stark sich die Absicherung ändert, wenn der **Kurs** sich bewegt.
- **Vanna** — wie stark sich die Absicherung ändert, wenn die **Volatilität** sich ändert.
- **Charm** — wie stark sich die Absicherung ändert, wenn **Zeit** vergeht.

Weil Dealer sehr groß sind, werden ihre gebündelten Hedging-Ströme selbst zu einer Marktkraft. Dealer Positioning macht diese Kraft sichtbar.

## Der Markt-Gamma-Index: dämpfend oder verstärkend?

Die wichtigste Kennzahl ist der aggregierte Netto-Gamma-Wert aller offenen Optionen — bei uns der **Markt-Gamma-Index (net-GEX)**. Sein Vorzeichen entscheidet über das gesamte Marktverhalten:

- **Positives Gamma (long Gamma):** Dealer wirken **volatilitäts-reduzierend**. Steigt der Kurs, verkaufen sie; fällt er, kaufen sie. Das dämpft Bewegungen — der Markt neigt zu enger Spanne, Mean-Reversion und „Pinning" an großen Strikes.
- **Negatives Gamma (short Gamma):** Dealer wirken **volatilitäts-forcierend**. Sie kaufen in steigende Kurse hinein und verkaufen in fallende — sie verstärken den Trend. Bewegungen werden größer, Vola nimmt zu.

Der Kipppunkt zwischen beiden Regimen heißt **Zero-Gamma-Flip**: der Kursstand, an dem das Netto-Gamma sein Vorzeichen wechselt. Liegt der Spot nahe am Flip, kann das Regime jederzeit kippen — ein wichtiges Warnsignal für erhöhte Fragilität.

Diese Zwei-Regime-Logik ist keine Erfindung von uns. Der Praktiker-Begriff „GEX" stammt aus dem SqueezeMetrics-White-Paper (2016). Wissenschaftlich untermauert wird das Vorzeichen-Regime durch die Arbeit **„Gamma Fragility" von Barbon & Buraschi (2021)**: Sie zeigen, dass aggregierte Dealer-Gamma-Ungleichgewichte Intraday-Momentum (bei negativem Gamma) beziehungsweise Reversal (bei positivem Gamma) erklären — und dass der Effekt in illiquiden Phasen am stärksten ist.

## Call-Wall, Put-Wall und der stärkste Pin

Aus dem Gamma je Ausübungspreis lassen sich markante Referenzstrikes ableiten:

- **Call-Wall** — der Strike oberhalb des Kurses mit dem größten positiven Netto-Dealer-Gamma. Wirkt oft als Widerstands-Referenz.
- **Put-Wall** — der Strike unterhalb mit dem größten negativen Netto-Gamma. Wirkt oft als Support-Referenz.
- **Absolute-Gamma** — der Strike mit dem insgesamt stärksten Gamma-Betrag, also der „magnetischste" Pin.

Wichtig, und das betonen wir bewusst: **Diese Walls sind Referenzen, keine Barrieren.** Es gibt keine Garantie, dass der Kurs an ihnen dreht. Sie zeigen nur, wo die Hedging-Aktivität am dichtesten ist.

Die Idee, dass Kurse zu großen Strikes gezogen werden (Pinning), ist eine der am besten belegten Beobachtungen der Marktmikrostruktur. **Ni, Pearson & Poteshman (2005, Journal of Financial Economics)** zeigten, dass Schlusskurse optionierter Aktien am Verfallstag an den Strike-Preisen clustern — im Schnitt eine Verschiebung von rund 16,5 Basispunkten, aggregiert über etwa 9 Milliarden Dollar Marktkapitalisierung. **Golez & Jackwerth (2012, JFE)** erweiterten diesen Pinning-Befund auf den S&P-500-Future — also genau die Index-Ebene, auf der unsere SPY- und QQQ-Walls arbeiten.

## Vanna und Charm: der Motor der Pre-OPEX-Drift

Hier schließt sich der Kreis zur Saisonalität. **Vanna** und **Charm** erklären, warum der Markt vor dem großen Monatsverfall so oft nach oben driftet.

Der typische Mechanismus: Anleger und Institutionelle kaufen Index-Puts als Absicherung, Dealer sind also netto short Puts. Passiert nun zweierlei:

- **Charm (Zeit):** Je näher der Verfall rückt, desto kleiner wird das Delta der aus dem Geld liegenden Puts. Der Dealer braucht weniger Short-Absicherung und **kauft Aktien zurück**.
- **Vanna (Volatilität):** Bleibt der Markt ruhig, sinkt die implizite Vola. Auch das lässt das Put-Delta schrumpfen — der Dealer kauft ebenfalls zurück.

Beide Kräfte zwingen die Dealer in denselben Tagen zu Käufen — ein **mechanischer Aufwärts-Bid in den dritten Freitag hinein**, der sich oft Donnerstag/Freitag beschleunigt. Nach dem Verfall verschwindet diese stabilisierende Positionierung, das Hedge-Polster fällt weg — und der Markt wird richtungsoffener und volatiler (die berüchtigte **Post-OPEX-Vola**).

Auch dafür gibt es harte Belege. **Baltussen, Terstegge & Whelan (2024)** dokumentieren einen „Third Friday Price Spike": Über 2003–2021 lag der Eröffnungswert am dritten Freitag im Schnitt **18,5 Basispunkte** über dem Vortagsschluss (t-Statistik über 4,5), der Effekt ist charm-getrieben und an Triple-Witching-Tagen am stärksten. Der geschätzte Vermögenstransfer allein im SPX: rund **4 Milliarden Dollar pro Jahr**.

Eine ergänzende Kennzahl ist der **Skew** — die Differenz zwischen der impliziten Volatilität eines aus dem Geld liegenden Puts (90 %) und der eines aus dem Geld liegenden Calls (110 %). Ein steiler Put-Skew signalisiert erhöhte Absicherungsnachfrage und ist ein Baustein der Vanna-Flows.

## Der SeasonAlpha-Winkel: Saisonalität trifft Dealer-Flows

Es gibt viele Gamma-Anbieter, und es gibt viele Saisonalitäts-Seiten. **Aber niemand verheiratet beide.** Genau hier liegt unser Alleinstellungsmerkmal.

GEX-Anbieter zeigen den Flow im Jetzt. Saisonalitäts-Seiten zeigen das Kalendermuster im Mittel. SeasonAlpha besitzt beides — plus einen **börsengenauen Kalender** für OPEX, Triple Witching, VIXpiration und den Handelstag-im-Monat (TDOM). Damit können wir sagen, *warum* ein saisonales Muster existiert, statt es nur zu zeigen.

{{chart:seasonal_yearly:SPY:20}}

Der Chart zeigt den typischen Jahresverlauf des SPY über 20 Jahre (normierte Renditen, jedes Jahr startet bei 100). Das ist das saisonale Grundgerüst. Dealer Positioning legt die kausale Ebene darunter: Wo der Kalender monatliche Verfallstermine markiert, liefern Charm und Vanna die mechanische Erklärung für die wiederkehrende Pre-OPEX-Drift — und für die Vola-Spitzen danach.

Aus „Muster" wird so „Mechanismus". Für Privatanleger heißt das: Du siehst nicht nur *dass* eine Phase statistisch auffällig ist, sondern verstehst die strukturelle Ursache dahinter — und kannst besser einordnen, wann ein Muster tragfähig ist und wann Makro-Ereignisse es überlagern.

## Ehrlichkeit zuerst: was unsere Zahlen sind — und was nicht

Dealer Positioning ist ein YMYL-Thema (Your Money or Your Life). Deshalb sind wir hier bewusst transparent, statt Präzision vorzutäuschen:

- **Wir nutzen eine naive Dealer-Heuristik.** Annahme: Dealer sind long Calls und short Puts. Das ist eine bewährte erste Näherung für Index-Gamma, aber **keine echte Kenntnis der Dealer-Bücher**.
- **Wir rechnen auf EOD-Daten von Yahoo** (Open Interest und implizite Vola am Handelsende). Anbieter wie SpotGamma oder SqueezeMetrics nutzen proprietäre Inventory-Modelle mit Intraday- und 0DTE-Daten. **Unsere Zahlen weichen von deren Zahlen ab** — sie sind eine belastbare Näherung, kein Deckungsgleiches.
- **Walls sind Referenzen, keine Garantien.** Kein Kauf- oder Verkaufssignal, keine Anlageberatung.
- **Nur US-gelistete Basiswerte.** Für den DAX, `^GDAXI` oder deutsche Aktien mit `.DE`-Endung liefert Yahoo keine Optionskette — dort gibt es kein Gamma-Bild.

Diese Grenzen sind kein Makel, sondern Teil der Methode. Wer Dealer Positioning ernst nimmt, muss wissen, wie belastbar die Datenbasis ist.

## So nutzt du das Feature

Das neue Feature findest du auf der Seite **[Dealer Positioning](/dealer-positioning)**. Dort siehst du für die wichtigsten US-Basiswerte (SPY, QQQ und große Einzeltitel) den Markt-Gamma-Index, den Zero-Gamma-Flip, die Call- und Put-Walls sowie das Vanna-/Charm-Bild.

Am meisten Wert entsteht in Kombination mit dem Kalender: Schau dir das Dealer-Bild in der Woche vor dem [Optionsverfall](/opex) an, und wirf einen Blick auf die [VIXpiration](/vixpiration), um den Vola-Zyklus einzuordnen. So verbindest du das saisonale Muster mit dem Mechanismus, der es antreibt.

Ein Hinweis zur Interpretation: Einzelaktien-Gamma ist deutlich verrauschter als Index-Gamma, weil Dealer dort weniger dominant sind. Für belastbare Aussagen sind die großen Index-ETFs (SPY, QQQ) der beste Ausgangspunkt.

## Fazit

Dealer Positioning ist kein Kristallkugel-Tool, sondern eine **Erklär-Ebene**. Gamma sagt, ob Dealer Bewegungen dämpfen oder verstärken. Vanna und Charm erklären die mechanische Aufwärtsdrift in den Optionsverfall und die Vola danach. Und die Walls markieren, wo Hedging-Aktivität am dichtesten ist.

Der eigentliche Mehrwert entsteht, wenn du diese Mechanik mit unserem Saisonkalender kombinierst — dann wird aus einem statistischen Muster ein verstandener Zusammenhang. Probiere es auf **[seasonalpha.ai/dealer-positioning](/dealer-positioning)** selbst aus.

## Häufige Fragen

### Was bedeutet positives und negatives Gamma?

Positives Netto-Gamma (long Gamma) bedeutet, dass Dealer Marktbewegungen dämpfen — sie verkaufen in Stärke und kaufen in Schwäche. Der Markt neigt zu enger Spanne. Negatives Gamma (short Gamma) bedeutet das Gegenteil: Dealer verstärken Bewegungen, die Volatilität steigt.

### Sind Call-Wall und Put-Wall feste Kurs-Barrieren?

Nein. Es sind Referenz-Strikes mit der höchsten Hedging-Aktivität, an denen Kurse häufiger reagieren. Sie sind aber keine Garantie und kein Handelssignal — starke Nachrichten oder Makro-Ereignisse überlagern das Bild jederzeit.

### Warum steigt der Markt oft vor dem Optionsverfall?

Weil Dealer, die netto short Puts sind, durch Zeitverfall (Charm) und fallende Volatilität (Vanna) ihre Short-Absicherungen zurückkaufen müssen. Das erzeugt einen mechanischen Kaufdruck in den dritten Freitag hinein. Studien wie Baltussen et al. (2024) belegen den Effekt mit rund 18,5 Basispunkten.

### Kann ich Dealer Positioning auch für den DAX sehen?

Nein. Unsere Datenquelle liefert nur für US-gelistete Basiswerte eine Optionskette. Für den DAX, `^GDAXI` oder deutsche Aktien mit `.DE`-Endung gibt es kein Gamma-Bild. Nutze SPY oder QQQ als liquide Referenz für den Gesamtmarkt.

### Sind eure Zahlen dieselben wie bei SpotGamma?

Nein. Wir nutzen eine naive Dealer-Heuristik auf EOD-Daten, keine proprietären Inventory-Modelle mit Intraday- und 0DTE-Flows. Unsere Werte sind eine belastbare Näherung für das Gesamtbild, weichen aber im Detail ab.

<!--
#### Social Media Snippet

**LinkedIn:** Neues Feature auf SeasonAlpha: Dealer Positioning (Gamma, Vanna, Charm). Endlich die Erklärung, warum der OPEX-Effekt existiert — aus dem Saison-Muster wird der Mechanismus. Wir sind die Einzigen, die Dealer-Flows mit einem börsengenauen Saisonkalender verheiraten. Ehrlich gelabelt: naive Heuristik auf EOD-Daten, kein Signal. Wie nutzt du Gamma-Daten in deiner Analyse? https://seasonalpha.ai/dealer-positioning

**Twitter/X:** Neu: Dealer Positioning auf SeasonAlpha 📊 Gamma, Vanna & Charm zeigen, WARUM der Markt vor dem Optionsverfall oft steigt. Aus Muster wird Mechanismus. Belegt durch Ni/Pearson/Poteshman (JFE 2005) & Baltussen et al. (2024). Kein Signal, ehrlich gelabelt. seasonalpha.ai/dealer-positioning #Gamma #OPEX #Optionen

#### Interne Verlinkung
- /dealer-positioning (Haupt-Feature)
- /opex (Optionsverfall-Kalender — thematisch direkter Nachbar)
- /vixpiration (Vola-Zyklus einordnen)
- Blog: 2026-04-13_vixpiration-april-2026 (Vola-Kompression rund um den Verfall)

#### Content-Ideen (Folgeartikel)
- „Zero-Gamma-Flip erklärt: der Kipppunkt zwischen ruhigem und wildem Markt"
- „Pre-OPEX-Drift im Backtest: 20 Jahre S&P 500 rund um den dritten Freitag"
- „Long Gamma vs. Short Gamma: das Gamma-Regime als Saisonkalender"
-->

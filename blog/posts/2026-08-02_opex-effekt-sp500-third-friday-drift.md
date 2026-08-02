---
title: "Der Third-Friday-Effekt: Warum der S&P 500 am Optionsverfall anders eröffnet"
seo_title: "OPEX-Effekt S&P 500: Der Third-Friday-Spike"
slug: opex-effekt-sp500-third-friday-drift
date: 2026-08-02
author: SeasonAlpha Research
category: education
tags: [opex, verfallstag, sp500, third-friday-effekt, optionsverfall, charm-vanna, dealer-positioning, saisonalitaet, triple-witching]
description: "OPEX-Effekt am S&P 500: Am dritten Freitag eröffnet der Markt im Schnitt 18,5 Basispunkte höher (Baltussen 2024). Was hinter dem Third-Friday-Spike steckt."
ticker: SPY
status: published
---

<!--
Keyword-Plan:
- Haupt-Keyword: OPEX-Effekt S&P 500
- Neben-Keywords: Verfallstag Aktienmarkt, dritter Freitag Börse, Third-Friday-Spike, Optionsverfall Effekt, Pre-OPEX-Drift, Triple Witching S&P 500, Charm Vanna Dealer, SOQ Special Opening Quotation
- Long-Tail: warum steigt der Markt vor dem Optionsverfall, was passiert am dritten Freitag an der Börse, Verfallstag S&P 500 Statistik, OPEX Drift erklärt, Baltussen Derivative Payoff Bias
- LSI: Basispunkte, normalisierte Renditen, Delta-Hedging, Market Maker, Open Interest, Wochentag-Effekt, Volatilität, Saisonalität, Triple Witching
- Suchintention: Anleger wollen verstehen, ob und warum der S&P 500 rund um den Options-Verfallstag ein systematisches Muster zeigt — und wie belastbar das ist.
-->

## Am dritten Freitag ist etwas anders

Der **OPEX-Effekt am S&P 500** gehört zu den am besten dokumentierten Mikrostruktur-Mustern der Wall Street — und zu den am meisten missverstandenen. Die zentrale Zahl kommt aus einer akademischen Studie: Über die Jahre 2003 bis 2021 eröffnete der US-Aktienmarkt am **dritten Freitag** eines Monats im Schnitt **18,5 Basispunkte über dem Vortagsschluss** (Baltussen, Terstegge & Whelan, 2024). Statistisch ist das hochsignifikant (t-Wert über 4,5) — kein Zufallsrauschen.

18,5 Basispunkte klingen nach wenig. Hochgerechnet auf das im S&P-500-Optionsmarkt umgesetzte Volumen entspricht das laut den Autoren einem Vermögenstransfer von rund **4 Milliarden Dollar pro Jahr** — allein im SPX. Der dritte Freitag ist damit kein x-beliebiger Handelstag, sondern strukturell auffällig. In diesem Artikel zeigen wir, woher der Effekt kommt, wie belastbar er ist — und wo unsere eigenen Daten an ihre Grenze stoßen.

## Was am Verfallstag wirklich passiert

„Optionsverfall" oder **OPEX** (von *option expiration*) bezeichnet den Tag, an dem börsengehandelte Optionen und Futures fällig werden. In den USA ist das für die großen Index-Kontrakte der **dritte Freitag** eines Monats. Viermal im Jahr — im März, Juni, September und Dezember — verfallen Index-Optionen, Index-Futures und Aktienoptionen gleichzeitig. Diesen Großverfall nennt man **Triple Witching** (großer Verfallstag).

Ein technisches Detail ist der Schlüssel zum ganzen Effekt: Die US-Index-Derivate werden nicht zum Freitags-*Schluss* abgerechnet, sondern zur **Eröffnung** — über die sogenannte *Special Opening Quotation* (SOQ). Das ist ein am Freitagmorgen aus den Eröffnungskursen aller Indexmitglieder errechneter Settlement-Wert.

Genau in diesem dünnen Zeitfenster — Donnerstagabend-Schluss bis Freitagmorgen-Eröffnung — entsteht der Sprung. Baltussen und Kollegen beschreiben eine **zeltförmige Bewegung** (englisch *tent-shaped*): Der Kurs zieht vom Donnerstagsschluss zur Freitagseröffnung an, erreicht rund um die SOQ seinen Hochpunkt und läuft bis zum Freitagmittag teilweise wieder zurück. Der Effekt ist an Triple-Witching-Terminen am stärksten, weil dann das größte Volumen an offenen Kontrakten fällig wird.

## Die Daten: eine seit 2003 messbare Verzerrung

Der Befund ist kein Einzelfall. Er reiht sich in eine ganze Linie peer-reviewter Forschung ein, die zeigt, dass der Options-Verfall die Kurse der Basiswerte messbar bewegt.

- **Baltussen, Terstegge & Whelan (2024), „The Derivative Payoff Bias"** — der oben genannte Third-Friday-Spike: +18,5 bps SOQ gegen Vortagsschluss, t über 4,5, ~4 Mrd. $/Jahr im SPX. Wichtig: Vor 2003 war der Effekt nicht vorhanden — er entstand mit der heutigen Marktstruktur.
- **Ni, Pearson & Poteshman (2005), *Journal of Financial Economics*** — der Klassiker zum *Pinning*: Schlusskurse optionierter Einzelaktien clustern am Verfallstag an den Options-Ausübungspreisen. Die Renditen wurden dabei im Schnitt um rund **16,5 Basispunkte** verschoben, aggregiert über etwa **9 Milliarden Dollar** Marktkapitalisierung.
- **Golez & Jackwerth (2012), *JFE*** — erweiterten den Pinning-Befund auf den **S&P-500-Future**, also die Index-Ebene.

Drei unabhängige Arbeiten, zwei davon in einem der drei wichtigsten Finanzjournale der Welt. Der gemeinsame Nenner: Der Optionsverfall ist kein neutrales Ereignis. Die Absicherungsströme der Optionshändler hinterlassen eine kleine, aber systematische Spur im Kurs.

## Der Mechanismus: Charm und Vanna zwingen zum Kauf

Warum eröffnet der Markt am dritten Freitag höher? Die Erklärung liegt nicht in der Stimmung der Anleger, sondern in der Mechanik der **Dealer** — der Market Maker, die Optionen verkaufen und ihr Risiko im Basiswert absichern.

Der typische Ausgangspunkt: Fonds und institutionelle Anleger kaufen Index-Puts als Versicherung gegen fallende Kurse. Die Dealer stehen damit auf der Gegenseite — sie sind **netto short Puts** und sichern sich ab, indem sie Aktien oder Futures leerverkaufen. Diese Short-Absicherung ist aber nicht statisch. Zwei „Griechen" lassen sie in den Verfall hinein schrumpfen:

- **Charm (Zeitverfall):** Je näher der Verfall rückt, desto kleiner wird das Delta der aus dem Geld liegenden Puts. Der Dealer braucht weniger Short-Hedge und **kauft Aktien zurück**.
- **Vanna (Volatilität):** Bleibt der Markt ruhig, sinkt die implizite Volatilität. Auch das lässt das Put-Delta schrumpfen — der Dealer deckt sich ebenfalls ein.

Beide Kräfte wirken in dieselbe Richtung und in denselben Tagen: ein **mechanischer Kaufdruck in den dritten Freitag hinein**. Baltussen und Kollegen führen den Spike explizit auf dieses charm-getriebene Inventory-Management der Market Maker zurück — verstärkt durch die dünne Liquidität im Overnight-Fenster. Das ist die kausale Ebene, die reine Kalender-Statistik nicht liefern kann. Wer den Mechanismus im Detail nachlesen will, findet ihn in unserem Beitrag [Dealer Positioning erklärt](/blog/dealer-positioning-gamma-vanna-charm/).

## Was unsere Daten zeigen — und was nicht

Hier kommt die ehrliche Einordnung, die dieses Thema (Your Money or Your Life) verlangt. Der 18,5-bps-Effekt ist ein **Overnight- beziehungsweise Eröffnungs-Sprung**: gemessen vom Donnerstagsschluss zur Freitags-*Eröffnung*. SeasonAlpha rechnet mit **normalisierten Tagesschlusskursen** (Close-zu-Close, jedes Jahr auf 100 normiert). Damit lässt sich der Overnight-Sprung **nicht eins zu eins nachbauen** — dafür bräuchte man saubere Eröffnungskurse und Intraday-Daten. Wir zeigen den saisonalen Rahmen und die Wochendrift, nicht den SOQ-Sprung selbst.

Was wir zeigen können, ist die **Freitags-Dimension** des Effekts. Der folgende Chart zeigt die durchschnittliche Tagesrendite des SPY je Wochentag über 20 Jahre:

{{chart:weekday_bars:SPY:20}}

Der Balken für den Freitag ist ein *Close-zu-Close*-Mittel über **alle** Freitage — er isoliert also nicht den dritten Freitag und erst recht nicht den Eröffnungs-Sprung. Er ordnet nur ein, wie sich der Wochentag insgesamt verhält, an dem die SOQ stattfindet. Genau diese Trennung — was wir messen können und was nicht — ist der Kern seriöser Datenarbeit.

Was den Verfall mechanisch antreibt, zeigt die **Vanna-Exposure je Verfallstermin**. Vanna misst, wie sich die Dealer-Absicherung mit der impliziten Volatilität verschiebt — fällt die Vola in den Verfall hinein, kaufen short-Vanna-Dealer Basiswert nach und stützen den Kurs:

![SPY — Vanna-Exposure je Verfall: vola-getriebene Dealer-Flows in die Optionsverfalle](opex-effekt-sp500-third-friday-drift/chart-vanna-by-term-spy.png)

Jeder Balken steht für einen Verfallstermin; die Höhe zeigt, wie stark die Dealer-Absicherung dort auf Vola-Änderungen reagiert. Genau diese Vanna- und Charm-Flows sind der plausibelste Treiber hinter der ruhigen Aufwärtsdrift in die OPEX-Woche — der Kalender markiert die Termine, der Mechanismus erklärt sie.

## Grenzen und Gegenbeispiele: kein Freifahrtschein

Ein ehrlicher Data-Study-Artikel muss auch zeigen, wo das Muster kippt.

**Der Effekt hat sich abgeschwächt.** Die Baltussen-Studie deckt 2003 bis 2021 ab. In den letzten rund vier Jahren ist die OPEX-Woche-Outperformance schwächer geworden — je bekannter ein Muster, desto eher wird es weggehandelt. Ein historischer Durchschnitt ist keine Prognose für den nächsten Freitag.

**Nach dem Verfall dreht das Bild oft.** Das Praktiker-White-Paper von **Ambrus Capital / Kris Sidial („Changing Market Structure")** zeigt in seiner Figur 7 das Gegenteil der Aufwärtsdrift: Eine Strategie, die den S&P nur im OpEx-Fenster kauft, verlor über drei Jahre rund 15 Prozent. Sobald das Hedge-Polster nach dem Verfall wegfällt, wird der Markt richtungsoffener und volatiler — die berüchtigte Post-OPEX-Schwäche. Die Drift *in* den Verfall und die Schwäche *danach* sind zwei Seiten derselben Mechanik.

**Es ist ein Overnight-Effekt.** Für einen Privatanleger mit Tagesorders ist der 18,5-bps-SOQ-Sprung praktisch nicht handelbar — er entsteht in einem illiquiden Fenster außerhalb der regulären Handelszeit. Der Wert dieser Erkenntnis liegt im **Verständnis**, nicht im Klick auf „Kaufen".

**Kein Signal, keine Anlageberatung.** Der OPEX-Effekt ist struktureller Kontext, kein Handelssignal. Makro-Ereignisse — eine Fed-Sitzung, ein Inflationswert, geopolitische Nachrichten — überlagern das dünne Muster jederzeit.

## Der SeasonAlpha-Winkel: Saisonalität trifft Dealer-Flows

Es gibt viele Gamma-Anbieter, und es gibt viele Saisonalitäts-Seiten. **Kaum jemand verheiratet beide.** Genau hier liegt unser Alleinstellungsmerkmal.

Reine Saisonalitäts-Seiten zeigen das Kalendermuster im Mittel — *dass* der dritte Freitag auffällt. Reine Options-Anbieter zeigen den Dealer-Flow im Jetzt — *wie* die Absicherung gerade steht. SeasonAlpha besitzt beides: einen **börsengenauen Kalender** für OPEX, Triple Witching und VIXpiration auf der Seite [Optionsverfall](/opex), plus die Gamma-, Vanna- und Charm-Kennzahlen auf [Dealer Positioning](/dealer-positioning). Damit können wir sagen, *warum* ein saisonales Muster existiert, statt es nur zu zeigen.

Für den Anleger heißt das: Du siehst nicht nur, dass eine Phase statistisch auffällig ist, sondern verstehst die strukturelle Ursache — und kannst besser einordnen, wann ein Muster tragfähig ist und wann es überlagert wird.

## Fazit

Der OPEX-Effekt am S&P 500 ist real und akademisch belegt: +18,5 Basispunkte am dritten Freitag über 18 Jahre, hochsignifikant, charm-getrieben. Er entsteht, weil Market Maker ihre Short-Absicherungen durch Zeitverfall und fallende Volatilität in den Verfall hinein zurückkaufen müssen.

Aber die Kernzahl ist ein **Overnight-Sprung**, kein Close-zu-Close-Trade — und der Effekt hat sich zuletzt abgeschwächt. Der eigentliche Mehrwert liegt im Verständnis des Mechanismus, nicht in einem simplen Kaufsignal. Erkunde den [Optionsverfall-Kalender](/opex) und das [Dealer Positioning](/dealer-positioning) selbst auf **seasonalpha.ai** — und sieh, wie Kalender und Dealer-Flows zusammenspielen.

## Häufige Fragen

### Was ist der OPEX-Effekt am S&P 500?

Der OPEX-Effekt beschreibt eine systematische Kursverzerrung rund um den Options-Verfallstag (den dritten Freitag im Monat). Laut Baltussen, Terstegge & Whelan (2024) eröffnete der US-Markt an diesen Tagen im Schnitt 18,5 Basispunkte über dem Vortagsschluss — hochsignifikant über den Zeitraum 2003 bis 2021. Ausgelöst wird er durch das Absicherungsverhalten der Market Maker.

### Warum steigt der Markt oft vor dem Optionsverfall?

Weil Dealer, die netto short Puts sind, ihre Short-Absicherung in den Verfall hinein zurückkaufen müssen. Zeitverfall (Charm) und fallende Volatilität (Vanna) lassen das Delta ihrer Puts schrumpfen — beides zwingt sie in denselben Tagen zu Käufen. Dieser mechanische Kaufdruck erzeugt die Aufwärtsdrift in den dritten Freitag.

### Kann ich den Third-Friday-Spike selbst handeln?

Praktisch kaum. Der 18,5-bps-Effekt ist ein Overnight-Sprung vom Donnerstagsschluss zur Freitagseröffnung, gemessen an der Special Opening Quotation — in einem dünn gehandelten Fenster außerhalb der regulären Zeit. Mit gewöhnlichen Tagesorders ist er nicht abschöpfbar. Es ist struktureller Kontext, kein Handelssignal und keine Anlageberatung.

### Warum kann SeasonAlpha den 18,5-bps-Sprung nicht exakt nachrechnen?

Weil wir mit normalisierten Tagesschlusskursen arbeiten (Close-zu-Close). Der Effekt ist aber ein Eröffnungs-Sprung, der saubere Open- und Intraday-Daten voraussetzt. Wir zeigen daher den saisonalen Rahmen und die Wochendrift, nicht den Overnight-Sprung selbst — und benennen diese Grenze bewusst, statt Präzision vorzutäuschen.

### Ist der Effekt an Triple-Witching-Tagen stärker?

Ja. An den vier großen Verfallstagen im März, Juni, September und Dezember verfallen Index-Optionen, Index-Futures und Aktienoptionen gleichzeitig. Das größte Volumen an offenen Kontrakten wird fällig, entsprechend stärker sind die Hedging-Ströme — Baltussen et al. (2024) messen den Spike an diesen Tagen am deutlichsten.

<!--
#### Social Media Snippet

**LinkedIn:** Am dritten Freitag ist etwas anders. Über 2003–2021 eröffnete der S&P 500 am Options-Verfallstag im Schnitt 18,5 Basispunkte über dem Vortagsschluss (Baltussen, Terstegge & Whelan 2024, t>4,5) — ein Vermögenstransfer von rund 4 Mrd. $/Jahr allein im SPX. Der Grund ist kein Sentiment, sondern Mechanik: Market Maker kaufen ihre Short-Absicherungen durch Charm (Zeitverfall) und Vanna (fallende Vola) in den Verfall hinein zurück. Wichtig und ehrlich: Das ist ein Overnight-/Eröffnungs-Sprung (SOQ), kein Close-zu-Close-Trade — mit Tagesdaten nicht 1:1 handelbar, und der Effekt hat sich zuletzt abgeschwächt. Kein Signal, sondern struktureller Kontext. Wie ordnet ihr den Verfallstag ein? https://seasonalpha.ai/opex

**Twitter/X:** Der Third-Friday-Effekt: Über 2003–2021 eröffnete der S&P 500 am Options-Verfall im Schnitt +18,5 bps über Vortagsschluss (Baltussen 2024, t>4,5). Charm & Vanna zwingen Dealer zum Rückkauf. Aber: Overnight-Sprung, kein Close-zu-Close-Signal. seasonalpha.ai/opex #OPEX #SP500 #Optionen

#### Interne Verlinkung
- /opex (Optionsverfall-Kalender — direktes Feature)
- /dealer-positioning (Gamma/Vanna/Charm — der Mechanismus)
- /vixpiration (Vola-Zyklus rund um den Verfall einordnen)
- /blog/dealer-positioning-gamma-vanna-charm/ (Mechanismus ausführlich)
- /blog/vixpiration-april-2026/ (Vola-Kompression um den Verfall)

#### Content-Ideen (Folgeartikel)
- „Post-OpEx-Schwäche & Triple Witching: Was nach dem großen Verfall passiert (Daten-Studie)"
- „Pinning: Warum Aktien am Verfallstag an runden Strikes kleben (Ni/Pearson/Poteshman)"
- „VIXpiration: Der zweite Verfallszyklus, den kaum jemand kennt"
-->

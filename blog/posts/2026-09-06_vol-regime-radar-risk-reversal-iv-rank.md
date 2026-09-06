---
title: "Vol-Regime-Radar: Risk Reversal, IV Rank und IV Percentile lesen lernen"
seo_title: "Risk Reversal & IV Rank: Vol-Regime-Radar lesen"
slug: vol-regime-radar-risk-reversal-iv-rank
date: 2026-09-06
category: education
tags: [optionen, risk-reversal, iv-rank, iv-percentile, volatility-skew, vol-regime, implizite-volatilitaet, options-radar]
description: "Risk Reversal, IV Rank und IV Percentile einfach erklärt: So liest du den Vol-Regime-Radar auf SeasonAlpha und erkennst teure von billiger Vola."
ticker: SPY
status: published
---

<!--
Keyword-Plan:
- Haupt-Keyword: Vol-Regime-Radar (Risk Reversal × IV Rank)
- Neben-Keywords: Risk Reversal, IV Rank, IV Percentile, Volatility Skew, implizite Volatilität, Vol-Regime, 25 Delta, Put-Skew, Call-Skew
- Long-Tail: Unterschied IV Rank IV Percentile, was ist Risk Reversal, implizite Volatilität teuer oder billig, Options-Radar lesen, Volatilitäts-Skew erklärt
- LSI: Optionen, Optionsprämie, Volatilität, Delta, Put, Call, Spread, tastytrade, Percentil, Absicherung, Skew
- Suchintention: Privatanleger wollen verstehen, wie man implizite Volatilität und Skew relativ einordnet und was Rank vs. Percentile bedeutet
-->

## Ist die Optionsprämie gerade teuer oder billig?

Diese eine Frage entscheidet, ob du Optionen eher verkaufen oder kaufen willst — und sie lässt sich nicht am absoluten IV-Wert beantworten. Eine implizite Volatilität von 20 % ist für einen ruhigen Index hoch, für eine Wachstumsaktie niedrig. Der **Vol-Regime-Radar** auf [/skew](/skew) löst das, indem er jeden Ticker **relativ zur eigenen Historie** einordnet — über zwei Achsen: **Risk-Reversal-Rank** und **IV-Rank** beziehungsweise **IV-Percentile**.

Dieser Artikel erklärt die drei Bausteine — Risk Reversal, IV Rank und IV Percentile —, warum Rank und Percentile nicht dasselbe sind, und wie du den Radar in vier Quadranten liest.

## Was ist ein Risk Reversal?

Ein **Risk Reversal (RR)** misst die Schieflage der impliziten Volatilität zwischen Puts und Calls. Konkret nehmen wir die IV eines aus dem Geld liegenden Calls (25-Delta) minus die IV eines aus dem Geld liegenden Puts (25-Delta):

**RR = 25Δ-Call-IV − 25Δ-Put-IV**

Das Vorzeichen verrät die Stimmung im Optionsmarkt:

- **Negatives RR (Put-Skew):** Puts sind teurer als Calls. Anleger zahlen einen Aufschlag für Absicherung nach unten — das klassische Angst-Muster von Aktienindizes.
- **Positives RR (Call-Skew):** Calls sind teurer als Puts. Das signalisiert Upside-Spekulation oder Squeeze-Fantasie und tritt eher bei einzelnen Momentum-Aktien oder Rohstoffen auf.

Manche Anbieter drehen das Vorzeichen um und sprechen vom **Skew = Put-IV − Call-IV**; inhaltlich ist es dieselbe Kennzahl. Das Risk Reversal ist das Industrie-Standard-Maß für Skew, weil es Angebot und Nachfrage nach Absicherung in einer Zahl bündelt.

## IV Rank versus IV Percentile — der wichtige Unterschied

Der zweite Baustein ist die Frage, wie teuer die Vola gerade im eigenen historischen Kontext ist. Dafür gibt es zwei Kennzahlen, die oft verwechselt werden.

### IV Rank: wo im Spannen-Bereich?

Der **IV-Rank** setzt den aktuellen Wert ins Verhältnis zur Spanne aus Minimum und Maximum eines Fensters (bei uns ein Jahr):

**IV-Rank = (aktuell − Min) / (Max − Min) × 100**

Ein IV-Rank von 0 % heißt: Die Vola ist auf dem tiefsten Stand des Jahres. 100 % heißt: auf dem höchsten. Der Rank sagt dir, **wo** im Wertebereich du dich befindest.

### IV Percentile: wie oft war es günstiger?

Das **IV-Percentile** zählt stattdessen, an welchem Anteil der Tage im Fenster die Vola **niedriger** war als heute:

**IV-Percentile = Anteil der Tage mit IV < aktuell × 100**

Ein IV-Percentile von 70 % heißt: An 70 % der letzten 250 Handelstage war die Vola günstiger als jetzt. Das Percentile misst also die **Häufigkeit**, nicht die Position in der Spanne.

### Warum der Unterschied zählt

Der Rank hat eine Schwäche: Ein einziger Vola-Spike hebt das Maximum stark an. Danach wirkt jeder normale Wert im Verhältnis zu diesem Ausreißer künstlich niedrig — der Rank wird nach unten gedrückt, obwohl sich das Marktumfeld kaum geändert hat. Das **Percentile ist robuster**, weil es nur zählt, wie oft ein Wert unterschritten wurde, und nicht, wie extrem der höchste Ausschlag war. Diese Unterscheidung stammt aus dem tastytrade-Umfeld und ist dort seit Jahren Standard.

Der Radar zeigt beide, damit du siehst, wenn sie auseinanderlaufen — genau das passiert unten bei mehreren Tech-Werten.

## Der Radar: ein Quadrant für das Vol-Regime

Der Vol-Regime-Radar spannt beide Ideen als Streudiagramm auf:

- **X-Achse:** Risk-Reversal-Rank — links Put-Skew, rechts Call-Skew.
- **Y-Achse:** IV-Rank oder IV-Percentile — oben teure Vola, unten billige.
- **Fadenkreuz bei 50 %:** trennt den Chart in vier Quadranten.

Jeder Punkt ist ein Ticker, verortet **relativ zur eigenen Historie**. Ein SPY bei IV-Rank 4 % steht nahe seinem eigenen Vola-Tief — auch wenn seine absolute IV höher wäre als die einer trägen Anleihe.

![Vol-Regime-Radar mit Risk-Reversal-Rank auf der X-Achse und IV-Rank auf der Y-Achse für Mag7 und große ETFs](vol-regime-radar-risk-reversal-iv-rank/radar-rr-rank-iv-rank-de.png)

Der Chart zeigt zwölf große US-Basiswerte per 6. September 2026 über ein rollierendes Jahr. Auffällig: Fast alle liegen im **unteren Bereich** (IV-Rank unter 40 %) — die implizite Volatilität ist marktweit nahe ihren Jahrestiefs. SPY, IWM und NVDA kleben mit IV-Rank unter 6 % am unteren Rand. Zugleich sitzen fast alle **rechts** (RR-Rank über 70 %): Der Call-Skew ist relativ zur eigenen Historie ungewöhnlich hoch, die Puts also vergleichsweise günstig. In der Radar-Logik ist das der Quadrant „billige Vola, wenig Abwärts-Absicherungsdruck".

### Die vier Quadranten als Ideen-Gitter

Aus der Position im Radar lassen sich vier grobe Optionsstrukturen ableiten — als Einordnung, nicht als Empfehlung:

| Quadrant | Vola | Skew | Denkansatz |
|----------|------|------|------------|
| Oben rechts | teuer | Call-Skew | Call-Prämie verkaufen (Call Credit Spread) |
| Oben links | teuer | Put-Skew | Put-Prämie verkaufen (Put Credit Spread) |
| Unten rechts | billig | Call-Skew | Upside kaufen (Call Debit Spread) |
| Unten links | billig | Put-Skew | Downside kaufen (Put Debit Spread) |

Oben verkauft man tendenziell Prämie (Vola ist teuer), unten kauft man sie (Vola ist billig). Links versus rechts sagt, ob die Struktur eher auf der Put- oder Call-Seite ansetzt. Das ist ein Ausgangsraster für die Recherche — kein fertiges Setup.

## Rank und Percentile im direkten Vergleich

Der zweite Chart zeigt dieselben zwölf Ticker, aber mit **Percentile statt Rank** auf beiden Achsen. Die Punkte verschieben sich leicht — genau das macht den Unterschied greifbar.

![Derselbe Radar mit Risk-Reversal-Percentile und IV-Percentile — dieselben Ticker verschieben sich gegenüber der Rank-Ansicht](vol-regime-radar-risk-reversal-iv-rank/radar-rr-pct-iv-pct-de.png)

Drei Verschiebungen fallen auf:

- **META** springt von IV-Rank 37 % auf IV-Percentile 65 % — und wandert damit über das Fadenkreuz in den oberen Bereich. Übersetzt: In der Spanne liegt META im Mittelfeld, aber an fast zwei Dritteln der Tage war die Vola günstiger als heute. Das Percentile stuft META also als „relativ teuer" ein, der Rank noch als „mittel".
- **AAPL** rückt von IV-Rank 22 % auf Percentile 42 % nach oben.
- **AVGO** verschiebt sich horizontal: Der RR-Rank von 77 % wird zum RR-Percentile von 98 % — der Call-Skew war fast nie so ausgeprägt wie jetzt.

Solche Sprünge entstehen, wenn ein einzelner Vola- oder Skew-Ausschlag die Spanne aufbläht. Der Rank verwässert, das Percentile bleibt näher am typischen Alltag. Wer nur eine Kennzahl liest, verpasst diese Fälle. Deshalb zeigt der Radar beide und lässt dich das Fenster (3M/6M/1J/2J) umschalten — kürzere Fenster reagieren schneller, längere glätten stärker.

## So nutzt du den Radar auf SeasonAlpha

Den vollständigen Radar findest du auf **[/skew](/skew)**. Er deckt 156 US-Ticker in neun Themen-Kategorien ab — von Indizes und Mega-Caps über Halbleiter bis zu einzelnen Momentum-Namen. Über den Fenster-Schalter vergleichst du kurzfristige und langfristige Einordnung.

Der praktische Ablauf: Filtere auf eine Kategorie, suche die Ausreißer in den Ecken, und prüfe, ob Rank und Percentile dieselbe Geschichte erzählen. Laufen sie auseinander, ist ein Ausreißer in der Historie im Spiel — ein Signal, genauer hinzuschauen, nicht blind zu handeln. Kombiniere das anschließend mit der [Dealer-Positioning-Seite](/dealer-positioning), um zu sehen, wo die Hedging-Ströme liegen.

## Grenzen

Der Radar ist **rückwärtsgewandter Kontext**, kein Blick in die Zukunft. Er sagt dir, wo IV und Skew relativ zur eigenen Vergangenheit stehen — nicht, ob die Vola steigt oder fällt.

- **Kein Handelssignal.** Ein teures Vol-Regime kann teuer bleiben oder noch teurer werden. Rank und Percentile sind Einordnung, keine Auslöser.
- **Fenster-abhängig.** Dasselbe Ticker sieht im 3-Monats-Fenster anders aus als im 2-Jahres-Fenster. Vergleiche bewusst.
- **Datenbasis.** Wir rechnen auf 25-Delta-IVs aus verfügbaren Optionsketten. Das ist eine belastbare Näherung des Skew, keine tick-genaue Surface.

## Fazit

Der Vol-Regime-Radar beantwortet die Kernfrage „teuer oder billig?" nicht absolut, sondern relativ zur eigenen Historie. **Risk Reversal** zeigt die Skew-Richtung, **IV-Rank** die Position in der Spanne, **IV-Percentile** die Häufigkeit — und der Unterschied der beiden verrät, ob ein Ausreißer die Statistik verzerrt.

Aktuell liegt der Markt breit im billigen, call-lastigen Quadranten. Ob das eine Chance oder nur ein Zustand ist, entscheidet dein eigener Plan. Schau selbst auf **[seasonalpha.ai/skew](/skew)**.

## Häufige Fragen

### Was ist der Unterschied zwischen IV Rank und IV Percentile?

Der IV-Rank misst die Position in der Spanne: (aktuell − Min) / (Max − Min). Das IV-Percentile misst die Häufigkeit: den Anteil der Tage, an denen die Vola niedriger war. Ein einzelner Vola-Spike drückt den Rank stark, lässt das Percentile aber weitgehend unberührt — deshalb gilt das Percentile als robuster.

### Was bedeutet ein Risk Reversal?

Das Risk Reversal ist die IV eines 25-Delta-Calls minus die IV eines 25-Delta-Puts. Ist es negativ, sind Puts teurer (Put-Skew, Absicherungsnachfrage). Ist es positiv, sind Calls teurer (Call-Skew, Upside-Spekulation). Es ist das gängigste Maß für den Volatility Skew.

### Wie lese ich den Vol-Regime-Radar?

X-Achse ist der Risk-Reversal-Rank (links Put-Skew, rechts Call-Skew), Y-Achse der IV-Rank oder das IV-Percentile (oben teuer, unten billig). Das Fadenkreuz bei 50 % teilt den Chart in vier Quadranten. Oben verkauft man tendenziell Prämie, unten kauft man sie — als Ideen-Raster, nicht als Signal.

### Ist ein hoher IV-Rank ein Kaufsignal für Optionen?

Nein. Ein hoher IV-Rank heißt nur, dass die implizite Volatilität nahe ihrem Jahreshoch liegt — Optionen sind also relativ teuer, was eher gegen den Kauf spricht. Ob die Vola weiter steigt oder fällt, sagt der Rank nicht. Es ist Kontext, kein Auslöser.

<!--
#### Social Media Snippet

**LinkedIn:** Neu auf SeasonAlpha: der Vol-Regime-Radar (/skew). Er ordnet 156 US-Ticker über Risk-Reversal-Rank × IV-Rank/Percentile ein — jeder relativ zur eigenen Historie. Im Post erklären wir den oft verwechselten Unterschied zwischen IV Rank (Position in der Spanne) und IV Percentile (Häufigkeit) — und zeigen an echten Daten, wie META & Co. je nach Kennzahl über das Fadenkreuz wandern. Kontext, kein Signal. Wie ordnest du implizite Vola relativ ein? https://seasonalpha.ai/skew

**Twitter/X:** IV Rank ≠ IV Percentile 📊 Der eine misst die Position in der Spanne, der andere die Häufigkeit — ein Vola-Spike drückt den Rank, nicht das Percentile. Unser neuer Vol-Regime-Radar zeigt beide + Risk-Reversal-Skew für 156 Ticker. Kontext, kein Signal. seasonalpha.ai/skew #Optionen #IVRank #Volatility

#### Interne Verlinkung
- /skew (Haupt-Feature: Vol-Regime-Radar)
- /dealer-positioning (Gamma/Vanna/Charm — der Flow hinter dem Skew)
- Blog: 2026-08-02_dealer-positioning-gamma-vanna-charm (Skew als Baustein der Vanna-Flows)

#### Content-Ideen (Folgeartikel)
- „Put-Skew als Angst-Barometer: was der 25-Delta-Skew des SPX über Krisen verrät"
- „IV Rank im Backtest: Bringt Prämienverkauf bei hohem Rank wirklich mehr?"
- „Skew-Rotation zwischen Sektoren: wo Absicherung teuer und wo billig ist"
-->

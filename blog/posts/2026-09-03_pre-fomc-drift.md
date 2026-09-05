---
title: "Der Pre-FOMC-Drift: Warum die 24 Stunden vor Fed-Entscheidungen einen Großteil der Aktienrendite liefern"
seo_title: "Pre-FOMC-Drift: Fed-Entscheidung und Börse erklärt"
slug: pre-fomc-drift
date: 2026-09-03
category: education
tags: [pre-fomc-drift, fed-entscheidung, fomc, aktienmarkt, event-studie, spy]
description: "Pre-FOMC-Drift erklärt: Warum die 24 Stunden vor Fed-Entscheidungen überproportional Rendite liefern — Studienlage, echte SPY-Zahlen und die Grenzen."
ticker: SPY
status: published
---

<!--
Keyword-Plan:
- Haupt-Keyword: Pre-FOMC-Drift
- Neben-Keywords: Fed-Entscheidung Börse, FOMC Aktienmarkt, Pre-FOMC Announcement Drift, Zinsentscheidung Aktien, FOMC Sitzung Börsenreaktion, Aktienmarktrendite Fed
- LSI: Equity Premium, Lucca Moench, Risikoprämie, Overnight-Rendite, Event-Studie, Zinsentscheid, geplante FOMC-Sitzung, S&P 500 SPY
-->

## Ein schmales Zeitfenster, ein großer Teil der Rendite

Der **Pre-FOMC-Drift** beschreibt eine der auffälligsten Anomalien am US-Aktienmarkt: Ein überproportionaler Teil der langfristigen Aktienrendite entsteht nicht über die tausenden Handelstage verteilt, sondern gedrängt in den rund 24 Stunden **vor** einer geplanten Zinsentscheidung der US-Notenbank. Wenn eine Fed-Entscheidung die Börse bewegt, passiert das Interessante also oft, bevor überhaupt jemand die Entscheidung kennt.

Das ist kein saisonaler Kalendereffekt wie „September schwach" oder „Turn-of-Month". Der Drift ist **event-verankert**: Er hängt an konkreten Terminen, die die Fed lange im Voraus veröffentlicht. Genau das macht ihn spannend — und erklärt zugleich, warum er sich schwer wegdiskutieren lässt.

## Was der Pre-FOMC-Drift genau ist

FOMC steht für Federal Open Market Committee — das Gremium der US-Notenbank, das über den Leitzins entscheidet. Es tagt achtmal im Jahr zu **planmäßigen** Sitzungen, deren Termine Monate vorher feststehen. Am zweiten Sitzungstag folgt gegen 14:00 Uhr Ortszeit (New York) die Bekanntgabe.

Der Pre-FOMC-Drift bezeichnet den Umstand, dass US-Aktien im engen Fenster **vor** dieser 14:00-Uhr-Bekanntgabe im Schnitt deutlich steigen — gemessen typischerweise ab dem Nachmittag des Vortags. Die Bewegung passiert also, während die Entscheidung selbst noch unbekannt ist. Kein neuer Zinsbeschluss, keine Pressekonferenz, trotzdem ein messbarer Aufwärtsdrift.

Wichtig zur Abgrenzung: Es geht um **geplante** Sitzungen. Notfallsitzungen (etwa im März 2020) folgen einer anderen Logik und gehören nicht in dieselbe Schublade.

## Was die Forschung zeigt

Die Grundlagenstudie stammt von **David Lucca und Emanuel Moench** (2015, „The Pre-FOMC Announcement Drift", erschienen im *Journal of Finance*, zuerst als Staff Report der Federal Reserve Bank of New York). Ihr zentraler Befund: Im Untersuchungszeitraum 1994–2011 entfiel ein Großteil der gesamten Aktienmarkt-Überrendite (des sogenannten Equity Premium) auf dieses schmale 24-Stunden-Fenster vor den planmäßigen FOMC-Ankündigungen — die Größenordnung, die sie berichten, liegt bei rund **80 %**.

Diese Zahl stammt aus der externen Studie, nicht aus SeasonAlpha-Daten, und bezieht sich auf deren spezifisches Fenster und Verfahren. Sie ist deshalb kein Wert, den man eins zu eins auf jedes andere Zeitfenster überträgt. Der Punkt ist die Größenordnung: ein winziger Bruchteil der Kalendertage trägt einen unverhältnismäßig großen Teil der Rendite.

Die Debatte ist seither nicht abgeschlossen. Eine neuere Arbeit aus der Fed-Reihe (FEDS Working Paper 2026-023) greift den Effekt erneut auf und diskutiert, wie stabil er über die Zeit ist und woher er kommt. Auf Praktikerseite hat ein Backtest (QuantSeeker, 25.02.2025) durchgerechnet, was eine Strategie brächte, die SPY **nur** rund um FOMC-Tage hält: grob **4 % Rendite pro Jahr** bei einer Sharpe Ratio von etwa **0,5 bis 0,6** über 1993–2024. Auch diese Werte sind extern und dienen der Einordnung, nicht als Handelsempfehlung.

## Eine tagesbasierte Näherung aus SeasonAlpha-Daten

SeasonAlpha rechnet mit normierten **Tagesschlusskursen**. Das reine 24-Stunden-Fenster der akademischen Studien lässt sich damit nicht exakt nachbauen — dafür bräuchte man Intraday-Daten ab 14:00 Uhr des Vortags. Was sich sauber abbilden lässt, ist eine tagesbasierte Näherung: die durchschnittliche **Tagesrendite von Schlusskurs zu Schlusskurs** an drei Gruppen von Tagen.

Datenbasis ist der ETF **SPY** (S&P 500) über 2006–2025, verankert an den **165 planmäßigen FOMC-Sitzungen** dieses Zeitraums (Termine aus dem offiziellen Fed-Kalender). Wir unterscheiden:

- **Tag vor der FOMC-Entscheidung** (der Handelstag unmittelbar vor der Bekanntgabe),
- **FOMC-Tag selbst** (der Bekanntgabetag),
- **alle übrigen Handelstage** als Vergleichsmaßstab.

![Pre-FOMC-Drift bei SPY: Ø Tagesrendite am Tag vor FOMC (+0,131 %), am FOMC-Tag (+0,202 %) und an allen übrigen Tagen (+0,040 %), 2006–2025](pre-fomc-drift/pre-fomc-drift-spy-de.png)

Das Ergebnis ist deutlich. Der Tag **vor** der Entscheidung liefert im Schnitt **+0,131 %**, der FOMC-Tag selbst **+0,202 %** — gegenüber nur **+0,040 %** an allen übrigen Tagen. Der Vortag rentiert damit rund **dreimal** so stark wie ein durchschnittlicher gewöhnlicher Handelstag.

Rechnet man die additiven Tagesrenditen zusammen, entfallen auf die kombinierten Pre-FOMC- und FOMC-Tage etwa **22 %** der aufsummierten SPY-Tagesrendite des Zeitraums — bei einem Anteil von nur **6,6 %** aller Handelstage. Das ist keine 80-%-Zahl wie in der Originalstudie, aber es zeigt dieselbe Richtung: wenige, ereignisgebundene Tage tragen unverhältnismäßig viel bei. Der Unterschied zur akademischen Größenordnung erklärt sich vor allem durch das gröbere Tagesfenster und den anderen Zeitraum.

### Der Vortag hält, der Ankündigungstag schwächelt

Ein Detail lohnt den zweiten Blick. Verengt man das Fenster auf die letzten 15 Jahre (2011–2025, 121 Sitzungen), bleibt der **Vortag stark** (Ø +0,151 %), während der FOMC-Tag selbst deutlich nachlässt (Ø nur noch +0,026 %). Anders gesagt: Der Drift **vor** der Entscheidung war in der jüngeren Historie robuster als die Reaktion **an** der Entscheidung. Das passt zur Debatte, ob bekannte Muster mit der Zeit teilweise weggehandelt werden — die Reaktion auf die eigentliche Nachricht lässt eher nach als das Warten davor.

## Woher kommt der Effekt?

Eine saubere Ursache lässt sich nicht beweisen, aber es gibt zwei ernsthafte Erklärungsstränge.

**Risikoprämie.** Vor einer Zinsentscheidung ist die Unsicherheit erhöht. Anleger, die dieses Risiko tragen, verlangen dafür eine Kompensation — und die realisiert sich als Rendite im Vorfeld. In dieser Lesart ist der Drift der Preis fürs Aushalten der Ungewissheit bis zur Bekanntgabe.

**Informations- und Erwartungsmechanik.** Eine alternative Deutung betont, dass der Drift besonders stark ausfällt, wenn die Fed am Ende „gute Nachrichten" liefert. Dann wäre der Anstieg weniger reine Risikoprämie als vielmehr eine antizipierende Positionierung, die im Schnitt bestätigt wurde. Beide Erklärungen schließen sich nicht aus; welcher Mechanismus überwiegt, ist Teil der laufenden Forschungsdebatte.

Für Privatanleger ist die Ursachenfrage weniger relevant als die Konsequenz: Der Effekt ist ein statistisches Durchschnittsmuster, kein Naturgesetz. Er sagt nichts über die nächste einzelne Sitzung.

## Grenzen des Musters

Vier Einschränkungen gehören zwingend dazu.

**Es ist ein Durchschnitt.** +0,131 % am Vortag ist ein Mittelwert über 165 Sitzungen mit einer Standardabweichung von rund 1,6 % — die Streuung von Sitzung zu Sitzung ist also weit größer als der Effekt selbst. Einzelne FOMC-Vortage waren tief rot. Der Vorteil zeigt sich erst über viele Ereignisse, nicht bei einem einzelnen Termin.

**Tagesdaten ≠ 24h-Fenster.** Unsere Zahlen sind eine Näherung aus Schlusskursen. Der reine, intraday gemessene Pre-Drift der Studien ist damit nur annähernd erfasst — die Overnight- und Vormittagskomponente steckt teils in benachbarten Tagesbalken. Für die exakte akademische Größe braucht es Intraday-Daten.

**Wegtraden.** Bekannte Anomalien verlieren tendenziell an Kraft, sobald genug Kapital sie ausnutzt. Der Rückgang der reinen Ankündigungstag-Rendite in den letzten 15 Jahren ist ein Hinweis darauf. Ob der Vortags-Drift dauerhaft bestehen bleibt, ist offen.

**Kein Signal, keine Beratung.** Der Pre-FOMC-Drift ist ein Beobachtungsmuster, kein Handelssignal und keine Anlageberatung. Transaktionskosten, Steuern und die Gefahr, dass ausgerechnet der nächste Termin negativ ausfällt, sind real.

## Praxisbezug für Anleger

Der Nutzen liegt im **Kontext**, nicht im Timing. Wer weiß, dass Aktien im Vorfeld von Fed-Terminen historisch eher fest tendierten, interpretiert einen ruhigen Anstieg vor der Sitzung nüchterner — und überschätzt einen Rücksetzer direkt nach der Bekanntgabe weniger.

Die planmäßigen FOMC-Termine stehen offen im Kalender. Auf SeasonAlpha findest du sie gebündelt auf der Seite [Zentralbanken-Termine](/zentralbanken), zusammen mit EZB, BoE und BoJ. Wann welche Ereignisse im Börsenmonat anstehen — von OPEX bis Notenbanksitzung — zeigt der [Marktkalender](/kalender). Wer sich für weitere ereignisgebundene Muster interessiert, findet im Beitrag zum [OPEX-Effekt beim S&P 500](/blog/opex-effekt-sp500-third-friday-drift/) eine verwandte Analyse.

## Fazit

Der Pre-FOMC-Drift gehört zu den robustesten dokumentierten Anomalien am US-Aktienmarkt: Ein großer Teil der Rendite entsteht in den Stunden vor planmäßigen Fed-Entscheidungen, nicht danach. Die Studienlage (Lucca & Moench 2015, aktuelle Fed-Arbeiten) und unsere eigene Tagesschluss-Näherung für SPY (Vortag Ø +0,131 % vs. +0,040 % an gewöhnlichen Tagen, 2006–2025) zeigen dieselbe Richtung. Es bleibt ein Durchschnittsmuster mit großer Streuung — Kontext für die eigene Einordnung, kein Fahrplan. Die nächsten Fed-Termine kannst du dir jederzeit auf [seasonalpha.ai](https://seasonalpha.ai/zentralbanken) ansehen.

## Häufige Fragen

### Was ist der Pre-FOMC-Drift einfach erklärt?
Der Pre-FOMC-Drift ist die Beobachtung, dass US-Aktien im Schnitt in den rund 24 Stunden vor einer geplanten Zinsentscheidung der US-Notenbank steigen — also bevor die Entscheidung überhaupt bekannt ist. Ein überproportionaler Teil der langfristigen Aktienrendite fällt in dieses schmale Zeitfenster.

### Steigen Aktien vor jeder Fed-Entscheidung?
Nein. Es handelt sich um ein Durchschnittsmuster über viele Sitzungen. In unserer SPY-Näherung liegt der Tag vor FOMC bei durchschnittlich +0,131 %, aber mit einer Streuung von rund 1,6 % — einzelne Termine fielen klar negativ aus. Der Vorteil zeigt sich nur über viele Ereignisse.

### Ist der Pre-FOMC-Drift ein Handelssignal?
Nein. Der Effekt ist ein statistisches Muster, kein Handelssignal und keine Anlageberatung. Transaktionskosten, Steuern und die reale Möglichkeit eines negativen Ausgangs am nächsten Termin begrenzen die praktische Nutzbarkeit. Er dient der Einordnung, nicht dem Timing.

### Funktioniert der Effekt noch?
Teilweise. In unserer Auswertung blieb der Drift am Vortag über die letzten 15 Jahre stabil (Ø +0,151 %), während die Rendite am Ankündigungstag selbst deutlich nachließ (Ø +0,026 %). Bekannte Anomalien verlieren tendenziell an Kraft, sobald sie breit ausgenutzt werden — ob der Vortags-Drift dauerhaft besteht, ist offen.

<!--
#### Social Media Snippet

**LinkedIn:** Ein Großteil der US-Aktienrendite entsteht nicht verteilt über tausende Handelstage — sondern gedrängt in den 24 Stunden VOR geplanten Fed-Entscheidungen. Das ist der Pre-FOMC-Drift (Lucca & Moench, 2015). Unsere Tagesschluss-Näherung für SPY (2006–2025, 165 Sitzungen): der Tag vor FOMC rentiert im Schnitt +0,131 % — dreimal so viel wie ein gewöhnlicher Handelstag (+0,040 %). Kein Handelssignal, aber ein bemerkenswertes Muster. 📊 Fed-Termine + Analyse: seasonalpha.ai

**Twitter/X:** Pre-FOMC-Drift: Aktien steigen historisch VOR Fed-Entscheidungen, nicht danach. SPY-Näherung 2006–2025: Tag vor FOMC Ø +0,131 % vs. +0,040 % an gewöhnlichen Tagen. 6,6 % der Tage ≈ 22 % der Rendite. Event-basiert, kein Kalender. #Börse #Fed #FOMC #SeasonAlpha

#### Interne Verlinkung
- /zentralbanken (FOMC/EZB/BoE/BoJ-Termine gebündelt)
- /kalender (Marktkalender: OPEX, Notenbank, VIXpiration)
- /blog/opex-effekt-sp500-third-friday-drift/ (verwandtes ereignisgebundenes Muster)
- /blog/fed-cuts-2026-polymarket-prognose/ (Fed-Thema, Erwartungsbildung)

#### Content-Ideen (Folgeartikel)
- "Overnight vs. Intraday: Wo genau entsteht der Pre-FOMC-Drift?" (bräuchte Intraday-Daten)
- "EZB statt Fed: Gibt es einen Pre-Ratsentscheid-Drift im DAX?"
- "Event-Studien erklärt: Wie man Renditen um feste Termine sauber misst"
-->

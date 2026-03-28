---
title: "Ist der Dienstag wirklich der beste Börsentag? Statistik trifft Praxis"
slug: wochentag-signifikanztest-siemens
date: 2026-03-28
category: tutorials
tags: [signifikanz, wochentage, t-test, p-wert, siemens, statistik, tutorial]
description: "Welcher Wochentag bringt bei Siemens die höchste Rendite? Wir erklären statistische Signifikanztests einfach und zeigen, wie du sie in SeasonAlpha nutzt."
ticker: SIE.DE
screenshot: Screenshot.png
status: published
---

## Montag ist der schlechteste Börsentag — oder?

Viele Anleger haben das Gefühl: Montags läuft es eher schlecht an der Börse. Freitags wird verkauft. Aber stimmt das wirklich — oder ist es nur ein Bauchgefühl?

Genau hier kommt die Statistik ins Spiel. Mit SeasonAlpha kannst du für jede Aktie und jeden Index nachschauen, welche Wochentage historisch besser oder schlechter abgeschnitten haben — und vor allem: **ob der Unterschied statistisch belastbar ist oder reiner Zufall**.

Am Beispiel der Siemens-Aktie zeigen wir, wie das funktioniert.

## Was ist ein Signifikanztest?

Stell dir vor, du wirfst eine Münze 10 Mal und bekommst 7 Mal Kopf. Ist die Münze gezinkt? Vielleicht — aber 10 Würfe reichen nicht, um das sicher zu sagen. Erst bei deutlich mehr Würfen und einem klaren Muster kann man von einem echten Effekt sprechen.

An der Börse ist es genauso. Wenn Siemens an 213 Montagen im Schnitt +0,17% gestiegen ist — ist das echte Stärke oder zufälliges Rauschen?

Der **t-Test** ist das statistische Werkzeug für genau diese Frage. Er prüft, ob eine beobachtete Rendite groß genug ist, um mit hoher Wahrscheinlichkeit kein Zufall zu sein.

Die wichtigsten Kennzahlen dabei:

- **t-Wert**: Je größer (im Betrag), desto stärker das Signal. Faustregel: |t| > 2 ist ein erstes Indiz für Signifikanz.
- **p-Wert**: Die Wahrscheinlichkeit, dass das beobachtete Muster reiner Zufall ist. **p < 0,05** gilt als Schwelle für statistische Signifikanz — das heißt: weniger als 5% Wahrscheinlichkeit, dass es Zufall ist.
- **n**: Die Anzahl der ausgewerteten Handelstage. Mehr Daten = stabilere Aussage.
- **Win-Rate**: Wie oft war der Tag positiv? 54% bedeutet, an mehr als jedem zweiten Tag gab es ein Plus.

## Die Siemens-Wochentage unter der Lupe

Schauen wir uns die Ergebnisse aus SeasonAlpha für die Siemens-Aktie an:

![Statistische Signifikanz der Wochentags-Effekte bei Siemens](Images/Screenshot.png)

| Wochentag | Ø Rendite | Win-Rate | t-Wert | p-Wert | Signifikant? |
|-----------|-----------|----------|--------|--------|--------------|
| Montag    | +0,17%    | 54%      | 1,15   | 0,2531 | ❌ Nein |
| **Dienstag**  | **+0,46%**    | **53%**      | **1,99**   | **0,0476** | **✅ Ja** |
| Mittwoch  | +0,00%    | 54%      | 0,02   | 0,9846 | ❌ Nein |
| Donnerstag| -0,17%    | 49%      | -0,94  | 0,3489 | ❌ Nein |
| Freitag   | +0,78%    | 49%      | 1,15   | 0,2520 | ❌ Nein |

Das Ergebnis ist überraschend klar: **Vier von fünf Wochentagen zeigen keine statistisch belastbare Rendite.** Einzig der **Dienstag** besteht den Test — mit einem p-Wert von 0,0476, also knapp unterhalb der 5%-Schwelle.

## Was bedeutet das konkret?

Ein paar wichtige Punkte zur Einordnung:

**Der Dienstag ist statistisch signifikant** — aber das bedeutet nicht, dass Siemens jeden Dienstag steigt. Es bedeutet: Über viele hundert Handelstage hinweg war der Dienstag systematisch stärker als der Zufall erklären könnte. Der t-Wert von 1,99 liegt knapp über der kritischen Marke von 2.

**Der Freitag hat die höchste Ø-Rendite (+0,78%)** — klingt beeindruckend, ist es aber statistisch nicht. Der p-Wert von 0,2520 zeigt: Die Streuung der Freitags-Renditen ist zu groß, um von einem echten Muster zu sprechen. Das ist ein klassisches Beispiel für **„groß aber nicht signifikant"**.

**Mittwoch ist völlig neutral**: t=0,02 und p=0,9846 — das ist statistisch kaum von Null zu unterscheiden. Kein Muster, kein Signal.

**Der Donnerstag ist leicht negativ** (-0,17%, Win-Rate nur 49%) — aber auch hier ist die Datenlage nicht eindeutig genug, um daraus eine stabile Aussage abzuleiten.

## Wie nutzt du das in der Praxis?

Signifikanztests sind kein Handelssystem — aber sie helfen dir, **Bauchgefühle von echten Mustern zu trennen**.

Ein paar Denkansätze:

1. **Langfristige Investoren** können Signifikanztests nutzen, um günstige Einstiegsfenster zu identifizieren — nicht als Timing-Werkzeug, sondern als zusätzlichen Filter bei geplanten Zukäufen.

2. **Vergleiche verschiedene Aktien**: Gilt der Dienstags-Effekt nur bei Siemens, oder auch bei anderen DAX-Werten? SeasonAlpha ermöglicht genau diesen Vergleich mit wenigen Klicks.

3. **Kombiniere mit anderen Filtern**: Auf der Wochentage-Seite in SeasonAlpha kannst du Indikator-Filter (z.B. RSI, SMA) hinzuschalten — und prüfen, ob der Dienstags-Effekt nur in bestimmten Marktphasen auftritt.

So geht's in SeasonAlpha:
- **Seite „Wochentage"** öffnen
- In der Sidebar den Ticker eingeben (z.B. `SIE.DE`)
- Den Expander **„Statistische Signifikanz der Wochentags-Effekte"** aufklappen
- Die fünf Tachos zeigen dir auf einen Blick: Score, t-Wert, p-Wert, Ø-Rendite und Signifikanz

## Fazit: Statistik schützt vor teuren Irrtümern

Der Wochentags-Effekt ist real — aber nur, wenn er statistisch belastbar ist. Bei der Siemens-Aktie ist das einzig beim Dienstag der Fall. Vier andere Tage mögen optisch interessant wirken, bestehen den Test aber nicht.

Das ist die Stärke von SeasonAlpha: Nicht einfach Durchschnittswerte anzeigen, sondern zeigen, **ob man ihnen auch vertrauen darf**. Denn an der Börse ist ein gut aussehendes Muster ohne statistische Grundlage oft gefährlicher als gar kein Muster.

> **Probiere es selbst auf [seasonalpha.ai](https://seasonalpha.ai)** — wähle deine Lieblingsaktie und schau, welcher Wochentag bei ihr statistisch wirklich zählt.

---
*Hinweis: Dieser Artikel dient ausschließlich der Information und Bildung. Er stellt keine Anlageberatung dar. Vergangene Muster garantieren keine zukünftigen Renditen.*

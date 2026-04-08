---
title: "Neu: Das SeasonAlpha Dashboard — alle Signale für einen Ticker auf einer Seite"
seo_title: "SeasonAlpha Dashboard: Saisonalität, KI-Score und Strategien für jeden Ticker"
slug: dashboard-launch
date: 2026-04-08
category: tutorials
tags: [dashboard, ki-score, crash-ampel, saisonalitaet, strategien, neu]
description: "Das neue SeasonAlpha Dashboard zeigt für jeden Ticker KI-Score, Crash-Ampel, Saisonalität, Risiko, Top-Strategien und nächste Events auf einer einzigen Seite. So nutzt du es."
ticker: ^GSPC
screenshot: dashboard-hero.png
status: published
---

<!--
Keyword-Plan:
- Haupt-Keyword: SeasonAlpha Dashboard
- Neben-Keywords: Saisonalität Dashboard, KI Score Aktien, Crash Ampel, Trading Signale Übersicht
- LSI-Keywords: Ticker-Analyse, Saisonale Muster, Strategien-Übersicht, Risiko-Dashboard
-->

## Warum ein Dashboard?

Bis heute musste man auf SeasonAlpha durch fünf bis zehn Analyseseiten klicken, um sich ein vollständiges Bild eines Tickers zu machen: Jahreszyklus, Monatszyklus, Drawdown, Strategien, anstehende Events. Jede Seite hat ihre Stärke — aber keine zeigt alles auf einen Blick.

Genau das ändert das neue **Dashboard** unter [seasonalpha.ai/dashboard](https://seasonalpha.ai/dashboard). Du gibst einen Ticker ein, und in zwei bis drei Sekunden steht alles vor dir: KI-Score, Crash-Ampel, Saisonalität, Risiko, Top-Strategien und die nächsten Events — ticker-individuell berechnet.

## Was du auf einer Seite bekommst

Das Dashboard ist als **Bento-Grid** aufgebaut: elf kompakte Karten, jede mit einer eigenen Aussage. Du musst nichts aufklappen, nichts filtern — alles ist sofort sichtbar.

![Das SeasonAlpha Dashboard für ^GSPC: Hero-Zeile mit KI-Score, Crash-Ampel, Anomalie-Radar und Januar Trifecta, darunter vier Saisonalitäts-Charts](dashboard-hero.png)

### Die Hero-Zeile: vier Signale, eine Sekunde

Ganz oben siehst du vier Karten, die zusammen einen ehrlichen Health-Check für den gewählten Ticker liefern:

- **KI Composite Score (0–10)** — vier Sub-Scores werden zu einem Gesamtwert verrechnet: wie gut die historischen Match-Jahre performt haben, wie der projizierte 30-Tage-Trend aussieht, wie die Win-Rate des aktuellen Monats ist und wie eng der aktuelle Verlauf der saisonalen Norm folgt. Über 6,5 = Bullish, unter 3,5 = Bearish, dazwischen = Neutral.
- **Crash-Ampel** — drei Risiko-Features (20-Tage-Vola, 20-Tage-Drawdown, 20-Tage-Return) werden gegen die letzten 252 Handelstage des **gleichen Tickers** perzentiliert. Das Ergebnis ist ein Risk-Score 0–100 mit grün/gelb/rot Ampel.
- **Anomalie-Radar** — vergleicht den aktuellen 10-Tage-Return mit dem historischen Durchschnitt aller vergleichbaren Fenster. Wenn der Wert weit ausserhalb der Norm liegt, ist das ein Signal zum Hinschauen.
- **Januar Trifecta** — zeigt für den gewählten Ticker den Status der drei Januar-Indikatoren (Santa Claus Rally, First Five Days, January Barometer). Drei Treffer = grün, zwei = gelb, weniger = rot.

### Die Charts: Saisonalität auf einen Blick

Direkt darunter siehst du vier Charts in zwei Reihen:

- **Saisonaler Jahresverlauf** — der durchschnittliche Verlauf der letzten 15 Jahre, das aktuelle Jahr in Gold daneben, Heute-Marker eingezeichnet. Du siehst sofort, ob das Jahr saisonal nach Plan läuft oder davon abweicht.
- **Saisonaler Drawdown** — die andere Seite der Medaille: wo lag historisch das maximale Risiko zu jeder Phase des Jahres, und wie tief ist der aktuelle Drawdown im Vergleich.
- **Aktueller Monat (TDOM-Verlauf)** — Zoom auf den aktuellen Monat: durchschnittliche Performance pro Handelstag, dazu der laufende Monat und ein „Heute"-Marker.
- **TruePath** — wir suchen die fünf historisch ähnlichsten Jahresverläufe und projizieren daraus eine Forward-Prognose für die nächsten 60 Tage. Das ist kein Crystal-Ball, sondern eine Mustererkennung über 100+ Jahre Daten.

### Wochentag- und TDOM-Quickchecks

Vier Mini-Karten zeigen Win-Rate und Durchschnittsrendite für:

- **Heute (Wochentag)** — Beispiel: Mittwochs steigt der S&P 500 in 55 % der Fälle, Ø +0,06 %.
- **TDOM heute / morgen / übermorgen** — die nächsten drei Handelstage als TDoM-Position, mit historischer Win-Rate und Durchschnitts-Return.

Damit weisst du nicht nur, wo du saisonal stehst, sondern auch, was die nächsten drei Sessions historisch bedeuten.

### Two-Week Phase: wo stehen wir im 2-Wochen-Zyklus

Eine breite Karte zeigt alle 24 Halbmonats-Phasen (Jan H1, Jan H2, …, Dez H2) als Bar-Chart, und die aktuelle Phase ist gelb markiert. Daneben Status (Bullish / Neutral / Bearish), Ø Return und Rang innerhalb der 24 Phasen.

Beispiel S&P 500 für **Apr H1**: Ø +0,24 %, Status Neutral, Rang 17/24 — also ein eher unauffälliger Halbmonat.

![Two-Week Phase Card mit dem aktuellen Halbmonat Apr H1 (gelb hervorgehobener Balken), Risiko-Metriken, Top-Strategien und nächsten Events für den S&P 500](dashboard-twoweek.png)

Direkt darunter siehst du auf demselben Bild die anderen Karten, die im Beispiel-Screenshot mitgeführt sind: die vier Risiko-KPIs, die Top-Strategien-Tabelle mit Streak-Badges und die vier Event-Karten — die wir uns gleich im Detail ansehen.

### Risiko: vier KPIs, eine Wahrheit

Eine Risiko-Karte mit vier KPIs:
- **Aktueller DD** im laufenden Jahr
- **Ø Max DD** der letzten 16 Jahre
- **Aktuelle 20-Tage-Vola**
- **Vola-Perzentil** (wo steht die aktuelle Vola im Verhältnis zur eigenen Historie)

Damit weisst du nicht nur, *ob* der Markt riskant ist, sondern *wie riskant er für diesen Ticker im Vergleich zur eigenen Historie ist*.

### Top 5 Strategien mit Signal in den nächsten 30 Tagen

Aus den 22 Plain-Vanilla-Strategien werden nur die angezeigt, die in den nächsten 30 Tagen ein **Entry-Signal** liefern, sortiert nach Datum. Pro Strategie siehst du die historische Win-Rate, das nächste Datum und die aktuelle Streak (z. B. „🟢 3 Wins" oder „🔴 5 Losses"). So siehst du auf einen Blick, welche Setups demnächst aktiv werden — ohne durch alle Strategien klicken zu müssen.

### Nächste Events mit historischer Statistik

Vier Karten für die nächsten anstehenden Ereignisse:

- **FOMC-Sitzung** (Fed Zinsentscheid)
- **OPEX** (3. Freitag im Monat)
- **Vollmond / Neumond**
- **Nächster Feiertag**

Pro Event siehst du, wie der gewählte Ticker historisch in einem t-3 bis t+3 Fenster reagiert hat: Win-Rate, durchschnittlicher Return und die aktuelle Streak. Das macht aus „der Fed-Termin ist nächste Woche" eine echte, ticker-spezifische Erwartung.

## Wofür ist das Dashboard *nicht* gedacht?

Ehrliche Einordnung: Das Dashboard ist eine **Übersicht**, kein Backtest und keine Empfehlung. Wenn du ein Setup tatsächlich tradest, willst du auf die jeweilige Detail-Page wechseln (Plain Vanilla, Backtest Engine, Jahreszyklus) und dort tiefer rein. Das Dashboard sagt dir: „Hier lohnt es sich gerade hinzuschauen." Die Detail-Pages sagen dir, *wie* du hinschaust.

Wir sind auch transparent über die Grenzen:

- Die KI-Score-Sub-Scores sind pragmatisch und client-side berechnet — keine Magie.
- Bei Crypto-Tickern fehlen FOMC, OPEX und Feiertage logischerweise.
- Die Trifecta wurde für US-Indizes konzipiert, kann aber auch für Einzelaktien angewendet werden — mit der entsprechenden statistischen Vorsicht.

## Wie du es benutzt

1. Geh auf [seasonalpha.ai/dashboard](https://seasonalpha.ai/dashboard).
2. Tipp einen Ticker ein (z. B. `^GSPC`, `TSLA`, `BTC-USD`, `^GDAXI`).
3. Wähle den Zeitraum (Default 15 Jahre — für Crypto eher 5 Jahre).
4. Lies die vier Hero-Karten von links nach rechts: KI-Score → Crash-Ampel → Anomalie → Trifecta. Das ist deine 5-Sekunden-Einschätzung.
5. Wenn dich etwas Bestimmtes interessiert, klick im Header-Menü auf die passende Detail-Page (Jahreszyklus, Plain Vanilla, Backtest Engine, …).

Du kannst das Dashboard auch direkt mit Ticker aufrufen:
```
https://seasonalpha.ai/dashboard?t=TSLA
```

## Was wir als nächstes bauen

Auf der Roadmap stehen:

- **Tickervergleich** — zwei Ticker im Dashboard nebeneinander
- **Custom Watchlists** — eigene Ticker-Listen mit gespeichertem Dashboard-View
- **Alerts** — Benachrichtigung wenn KI-Score, Crash-Ampel oder Strategie-Signale die Schwelle überschreiten

Bis dahin: probier das Dashboard aus, sag uns was fehlt, und wenn dir die Idee gefällt — abonniere unten den Newsletter, dann erfährst du jede neue Funktion zuerst.

[**→ Zum Dashboard**](https://seasonalpha.ai/dashboard)

---
title: "Tutorial: So nutzt du Indikator-Filter in SeasonAlpha"
seo_title: "Indikator-Filter Tutorial: RSI, SMA & MACD kombinieren"
slug: indikator-filter-tutorial
date: 2026-03-27
category: tutorials
tags: [tutorial, indikator, filter, rsi, sma, trading, technische-analyse, bollinger-bands, macd, ema, trading-signale]
description: "Schritt-fuer-Schritt: Kombiniere Saisonalitaet mit technischen Indikatoren (RSI, SMA, MACD, Bollinger) in SeasonAlpha fuer praezisere Signale."
ticker: AAPL
status: published
---

## Warum Indikator-Filter?

Die Kernfrage: **Funktioniert ein saisonales Muster besser, wenn bestimmte Marktbedingungen erfuellt sind?**

Zum Beispiel: Ist der Vollmond-Effekt staerker, wenn der RSI unter 30 liegt? Sind Montage profitabler, wenn der Kurs ueber dem 200-Tage-Durchschnitt liegt?

Mit den Indikator-Filtern in SeasonAlpha kannst du genau das herausfinden.

## Verfuegbare Indikatoren

SeasonAlpha bietet 6 technische Indikatoren als Filter:

- **SMA** (Simple Moving Average) — Trendfilter
- **EMA** (Exponential Moving Average) — Schnellerer Trendfilter
- **RSI** (Relative Strength Index) — Momentum/Ueberkauft-Ueberverkauft
- **Bollinger Bands** — Volatilitaetsfilter
- **MACD** — Trend- und Momentum-Kombination
- **LBR Oscillator** — Linda Bradford Raschke's Kurzfrist-Indikator

## Schritt-fuer-Schritt Anleitung

### 1. Oeffne eine Page mit Indikator-Filtern

Die Filter sind verfuegbar auf: Wochentage, Monatswechsel, Mondphasen, OPEX und Zentralbanken.

### 2. Oeffne den Filter-Expander in der Sidebar

Scrolle in der Sidebar nach unten. Unter "Technische Filter" findest du den Expander. Klicke auf "Filter hinzufuegen".

### 3. Waehle Indikator + Bedingung

Beispiel-Setup:

- **Filter 1**: RSI, Periode 14, Bedingung "RSI < 30"
- **Filter 2**: SMA, Periode 200, Bedingung "Close > SMA"

Beide Filter werden mit **UND** verknuepft: Nur Tage, an denen BEIDE Bedingungen erfuellt sind, fliessen in die Berechnung ein.

### 4. Interpretiere die Ergebnisse

Oben auf der Page siehst du ein blaues Badge:

**RSI(14) < 30 | Close > SMA(200) — 1.247 / 6.300 Tage (19.8%)**

Das bedeutet: Von 6.300 Handelstagen erfuellten 1.247 beide Bedingungen. Die saisonale Analyse basiert nur auf diesen gefilterten Tagen.

## Praxis-Beispiel: Mondphasen + RSI

{{chart:seasonal_yearly:AAPL:20}}

Vergleiche den normalen Vollmond-Effekt mit dem gefilterten Ergebnis (RSI < 30). Wenn die gefilterte Version deutlich besser performt, hast du einen statistischen Hinweis, dass der Mondphasen-Effekt unter bestimmten Marktbedingungen staerker ist.

## Tipps

- **Nicht zu eng filtern**: Wenn weniger als 100 Tage uebrig bleiben, ist die statistische Aussagekraft gering
- **Shift(1) beachten**: Der Filter nutzt den Indikator-Wert vom VORTAG, um Look-Ahead-Bias zu vermeiden
- **Kombiniere klug**: SMA als Trendfilter + RSI als Timing-Filter ist eine bewaehrte Kombination

---
title: "Dealer-Positioning-Greeks (Gamma, Charm, Vanna)"
tags: [optionsdaten, greeks, dealer-positioning, black-scholes]
status: draft
created: 2026-07-10
---

## Was es ist

Aus einer vollen Options-Chain (Strikes × Expiries mit Open Interest, IV, Typ) lassen sich per Black-Scholes die **aggregierten Dealer-Greeks** rechnen (numpy/scipy):
- **Gamma** (dDelta/dSpot) → [[gamma-exposure-gex]], Regime & Pinning.
- **Charm** (dDelta/dTime): Delta-Zerfall über die Zeit → erzwingt Dealer-Rehedging v. a. gegen Verfall → [[opex-charm-flows]] (Pre-OPEX-Drift, OPEX-Freitag).
- **Vanna** (dDelta/dVol): Delta ändert sich mit der IV → Vola-getriebene Flows, relevant um VIXpiration.

Datenbedarf: Chain + Spot/Zins/Div. EOD gratis via Yahoo (`v7/finance/options`, Crumb-Session) oder CBOE; **BTC via Deribit inkl. fertiger Greeks**. Intraday = paid.

## Relevanz für SeasonAlpha

Diese Greeks sind der **Mechanismus hinter unserer bestehenden Kalender-Saisonalität** (OPEX/Triple Witching/VIXpiration). Als Overlays auf die vorhandenen Seiten machen sie aus „Muster" ein „Warum" — starker Differenzierer + Content-Hebel.

## Quellen

- [[sources/2026-07-10_vibe-trading-und-gamma-exposure]] — Machbarkeit + Datenwege; Vibe-Trading liefert nur Options-Payoff, keine Dealer-Greeks.

## Offene Fragen

- Charm/Vanna aggregiert visualisieren — als Zeitreihe um OPEX/VIX-Termine?
- Welche Underlyings zuerst (SPY/QQQ/^SPX + BTC/Deribit)?

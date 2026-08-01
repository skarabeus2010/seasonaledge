---
title: "Gamma-Exposure (GEX) & Zero-Gamma-Flip"
tags: [optionsdaten, gamma-exposure, dealer-positioning, marktregime]
status: draft
created: 2026-07-10
---

## Was es ist

**GEX** aggregiert das Dealer-Gamma über die gesamte Options-Chain: net-GEX = Σ(Call-$-Gamma) − Σ(Put-$-Gamma), je Kontrakt `γ·OI·100·S²·0,01` ($ pro 1 % Spot-Move). Der **Zero-Gamma-Flip** ist das Spot-Level, an dem net-GEX das Vorzeichen wechselt. **Über** dem Flip (long-Gamma) hedgen Dealer gegenläufig → dämpfen Moves (Mean-Reversion, Pinning). **Unter** dem Flip (short-Gamma) hedgen sie prozyklisch → verstärken Moves (Trend, Vola). **Call/Put-Walls** = Strikes mit max. Dealer-Gamma (Widerstand/Support, Pinning-Magneten, v. a. um OPEX).

## Relevanz für SeasonAlpha

Eine **GEX-Ampel** (long/short-Gamma-Regime + Flip-Level + Walls) ist eine natürliche Ergänzung der Crash-Frühwarnung und erklärt, warum OPEX-Pinning entsteht. EOD-Snapshot je Underlying → `landing/data/gex_*.json` → `/gamma`-Seite. ⚠️ Dealer-Vorzeichen ist **Heuristik** („naive": long Calls/short Puts), keine echten Bücher — transparent kennzeichnen.

## Quellen

- [[sources/2026-07-10_vibe-trading-und-gamma-exposure]] — PoC SPY: net-GEX −1,1 Mrd/1 %, short-Gamma, Zero-Gamma 748,24, Walls 750.

## Offene Fragen

- Dealer-Vorzeichen verfeinern (OI-gewichtete vs. modellierte Sign-Convention)?
- Walls gamma-gewichtet (Pin) vs. OI-basiert (ferne S/R) trennen.
- Intraday-GEX nur mit Paid-Feed — lohnt EOD für unsere Zwecke?

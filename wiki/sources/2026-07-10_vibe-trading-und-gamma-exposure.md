---
title: "HKUDS/Vibe-Trading + Gamma-Exposure-Machbarkeit für SeasonAlpha"
source_file: "raw/repos/2026-07-10_vibe-trading-und-gamma-exposure.md"
source_type: repo
date_ingested: 2026-07-10
quality: repo
tags: [optionsdaten, gamma-exposure, dealer-positioning, opex, vixpiration, wettbewerber, faktoren]
status: ingested
---

## Kern-Aussagen

- **Vibe-Trading** (HKUDS, MIT) ist ein schwergewichtiges autonomes Trading-Agent-Framework (12+ Broker, 9 Backtest-Engines, 452 Alpha-Faktoren, Swarm). ~90 % (Ausführung/Autonomie/Messaging/Multi-Markt) passt NICHT zu SeasonAlpha (Analyse+Content, keine Order-Ausführung).
- **Cherry-pick-Kandidaten:** Faktor-Bibliotheken (alpha101/gtja191) als Zusatz-Signale (testbar mit `shared/backtest_engine.py`), Options-Chain-Ingestion als Referenz. Das Repo hat **keine** fertige Gamma/Charm/GEX-Analytik — nur Options-Payoff.
- **Eigentlicher Fit = Optionsdaten-Analytik.** SeasonAlpha besitzt schon den Kalender (OPEX/Triple Witching/VIXpiration); Gamma/Charm/Vanna sind der **Mechanismus dahinter** → Vertiefung, nicht neue Richtung.
- **PoC gebaut + gelaufen** (`scripts/compute_gamma_exposure.py`): SPY net-GEX **−1,10 Mrd $/1 % → short_gamma**, Zero-Gamma-Flip **748,24** (Spot 747,03 knapp darunter), Call-/Put-Wall **750** (Pinning). Datenweg (Yahoo-Chain, Crumb) + BS-Rechnung tragen.

## Relevanz für SeasonAlpha

Optionsdaten-Analytik ist die logische Erweiterung des bestehenden OPEX/VIX-Kalenders: eine **GEX-Ampel** (`/gamma` bzw. Integration in `/opex`+`/vixpiration`) + Charm/Vanna-Overlays erklären die vorhandene Kalender-Saisonalität mechanistisch und liefern differenzierenden Content (SEO/Video: „Gamma-Exposure", „OPEX-Pinning", „0DTE"). Datenquelle EOD gratis (Yahoo/CBOE; BTC via Deribit inkl. Greeks). **Kritisch:** Dealer-Vorzeichen ist Heuristik → transparent kennzeichnen (YMYL).

## Verlinkte Konzepte

- [[gamma-exposure-gex]]
- [[dealer-positioning-greeks]]
- [[opex-charm-flows]]

---
title: "OPEX-Charm-Flows (mechanistische Erklärung der Verfalls-Saisonalität)"
tags: [opex, vixpiration, charm, vanna, saisonalitaet]
status: draft
created: 2026-07-10
---

## Was es ist

**Charm** (dDelta/dTime) beschleunigt zum Optionsverfall: Delta von OTM-Optionen läuft gegen 0, von ITM gegen ±1. Dealer müssen ihr Hedge nachziehen → systematische **Charm-Flows** in den Tagen vor OPEX (klassischer Pre-OPEX-Drift) und am OPEX-Freitag (Pinning an [[gamma-exposure-gex]]-Walls). **Vanna**-Flows wirken parallel, getrieben von IV-Bewegungen (Bezug: VIXpiration). Zusammen liefern sie eine **kausale Erklärung** für Kalendereffekte, die SeasonAlpha bislang nur statistisch zeigt.

## Relevanz für SeasonAlpha

SeasonAlpha besitzt bereits `/opex` und `/vixpiration` (3. Freitag, Triple Witching, VIXpiration-Regeln, alles börsen-/feiertags-aware). Ein Charm/Vanna-Overlay erklärt die dort gemessene Saisonalität **mechanistisch** statt nur deskriptiv — höherwertiger Content + Vertrauensanker (mit ehrlichem Heuristik-Vorbehalt beim Dealer-Vorzeichen).

## Quellen

- [[sources/2026-07-10_vibe-trading-und-gamma-exposure]] — Optionsdaten-Analytik als Vertiefung des OPEX/VIX-Kalenders; PoC (SPY-GEX) validiert den Datenweg.

## Offene Fragen

- Empirisch prüfen: korreliert unser gemessener Pre-OPEX-Drift mit hohem net-GEX / Charm-Intensität?
- Overlay-Darstellung: Zeitfenster t−5…OPEX mit Charm-Intensität je Tag?

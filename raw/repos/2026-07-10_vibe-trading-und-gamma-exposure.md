# Quelle: HKUDS/Vibe-Trading + Gamma-Exposure-Machbarkeit für SeasonAlpha

- **Typ:** Repo-Analyse + eigener Proof-of-Concept
- **URL:** https://github.com/HKUDS/Vibe-Trading (MIT, Python 3.11+, FastAPI/LangGraph/React)
- **Datum:** 2026-07-10
- **Kontext:** User fragte, was aus dem Repo zu SeasonAlpha passt und was wir mit Optionsdaten (Gamma, Charm, …) rechnen könnten.

## Was Vibe-Trading ist
Schwergewichtiges, autonomes Trading-Agent-Framework: 12+ Broker-Anbindungen mit echter Order-Ausführung,
9 Backtest-Engines (inkl. `EquityOptionsEngine`), **452 Alpha-Faktoren** (alpha101/gtja191/qlib158/academic),
18 Datenquellen, 16 Messaging-Kanäle, Swarm-Agenten, Memory-System. Ein ganzes „Trading-OS".

## Was zu SeasonAlpha passt (cherry-picken, NICHT das Framework)
SeasonAlpha = schlankes statisches Frontend + Supabase + Content, **keine Ausführung**. ~90 % (Broker,
Autonomie, Messaging, Swarm, Multi-Markt) passt nicht. Wertvoll:
- **Faktor-Bibliotheken** (alpha101/gtja191): einzelne Faktoren als Zusatz-Signale (wie LBR/RSI), testbar
  mit `shared/backtest_engine.py`. Aber Cross-Sectional-Quant, nicht saisonal → nur ergänzend.
- **Options-Chain-Ingestion** (options-chains-Tool + Finnhub/FMP/Tiingo-Connectoren): Referenz für Optionsdaten.
- **AST-gehärtete Backtest-Sandbox + Attribution:** Referenz für unsere Engine.
- **Wichtig:** Repo hat **KEINE fertige Gamma/Charm/GEX-Analytik** — nur Options-Payoff/Breakeven. Die
  Dealer-Greeks müssten wir selbst bauen — passt aber perfekt zu unserem OPEX/VIX-Kalender.

## Optionsdaten-Analytik: der eigentliche Fit
SeasonAlpha besitzt **schon den Kalender** (OPEX / Triple Witching / VIXpiration). Gamma/Charm/Vanna sind der
**Mechanismus dahinter** → logische Vertiefung + Differenzierung, keine neue Richtung.

Berechenbar (alles per Black-Scholes aus der Chain, numpy/scipy vorhanden):
- **GEX + Zero-Gamma-Flip:** über/unter Flip → Dealer dämpfen (Mean-Reversion/Pinning) vs. verstärken (Trend/Vola). Neue Ampel wie Crash-Frühwarnung.
- **Call/Put-Walls** (Max-Gamma-Strikes): Support/Resistance, OPEX-Pinning → auf die OPEX-Seite.
- **Charm** (dDelta/dTime): Delta-Zerfall → Pre-OPEX-Drift + OPEX-Freitag-Flows → erklärt unsere OPEX-Saisonalität.
- **Vanna** (dDelta/dVol): Vola-getriebene Dealer-Flows → direkt auf VIXpiration.
- **Gamma-Regime** (long=ruhig / short=volatil): Marktstatus-Flag, ergänzt Crash-Ampel/Regime.

Datenbedarf: volle Options-Chain (Strikes × Expiries mit OI + IV + Typ) + Spot/Zins/Div. Frei/EOD via
Yahoo-Options-Endpoint (`v7/finance/options`, Crumb-Session wie fetch_event_data) oder CBOE; **BTC via
Deribit gratis inkl. Greeks**. Intraday = paid (Polygon/ORATS/Tradier).

⚠️ **Kern-Vorbehalt:** Dealer-Vorzeichen (wer long/short Gamma) ist **Annahme/Heuristik** („naive": Dealer
long Calls / short Puts). Kein Feed kennt echte Dealer-Bücher — auch SpotGamma schätzt nur. Muss
transparent gekennzeichnet werden (YMYL/Ehrlichkeit).

## Proof-of-Concept (gebaut + gelaufen)
`scripts/compute_gamma_exposure.py` — holt Yahoo-Chain, rechnet BS-Gamma je Kontrakt, aggregiert net-GEX,
sweept Spot für Zero-Gamma-Flip, findet Call/Put-Walls. Ergebnis (SPY, EOD, ≤60 Tage, 12 Expiries, 3451 Kontrakte):
- **net-GEX −1,10 Mrd $ / 1 % → short_gamma** (Dealer verstärken Moves)
- **Zero-Gamma-Flip 748,24** · Spot 747,03 lag knapp darunter → Short-Gamma-Zone
- **Call-Wall = Put-Wall = 750** (runde Zahl = Pinning-Magnet)
- Output: `landing/data/gex_SPY.json`. Größenordnung für SPY plausibel → Datenweg + Rechnung tragen.

## Empfehlung / nächste Schritte
1. MVP: **EOD-GEX-Snapshot** SPY/QQQ/^SPX (+ BTC via Deribit) → vorberechnetes `landing/data/gex_*.json` →
   `/gamma`-Seite bzw. Integration in `/opex` + `/vixpiration` (net-GEX, Zero-Gamma-Level, Walls, Regime-Ampel).
2. Charm/Vanna-Overlay auf die OPEX/VIX-Seiten (erklärt die bestehende Saisonalität mechanistisch).
3. Content/SEO/Video-Hooks: „Gamma-Exposure erklärt", „OPEX-Pinning / Max Pain", „0DTE-Gamma".
4. Walls verfeinern: gamma-gewichtet (Pin) vs. OI-basiert (ferne Support/Resistance) trennen.

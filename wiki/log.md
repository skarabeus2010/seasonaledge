# Bibliothekar-Log — SeasonAlpha Wiki

> **Append-only.** Jeder Ingest- und Lint-Vorgang hängt genau einen Eintrag an.
> Format: `## [YYYY-MM-DD] <op> | <Beschreibung>`

<!-- Einträge neuester zuerst (oben anfügen) -->

## [2026-07-10] ingest | 1 Quelle verarbeitet — Vibe-Trading + Gamma-Exposure

- `raw/repos/2026-07-10_vibe-trading-und-gamma-exposure.md` → `wiki/sources/2026-07-10_vibe-trading-und-gamma-exposure.md`
- Neu angelegt: [[gamma-exposure-gex]], [[dealer-positioning-greeks]], [[opex-charm-flows]]
- Kernbefund: Vibe-Trading-Framework passt kaum (keine fertige GEX-Analytik), aber Optionsdaten-Analytik = logische Vertiefung des OPEX/VIX-Kalenders. GEX-PoC (`scripts/compute_gamma_exposure.py`) validiert: SPY short-Gamma, Zero-Gamma 748,24, Walls 750. Dealer-Vorzeichen = Heuristik (transparent kennzeichnen).

## [2026-07-15] ingest | 1 Quelle verarbeitet — Backtest Runde 2

- `(intern)` → `wiki/sources/2026-07-15_backtest-runde2-walkforward-stoploss-lbr-newticker.md`
- Konzepte berührt: [[walk-forward-validierung]], [[lbr-oscillator]], [[edelmetall-saisonalitaet]], [[bollinger-mean-reversion]]
- Kernbefund: GLD+Bollinger OOS Sharpe 2.41 (Walk-Forward robust); SI=F/SLV starke Silber-Replikation; LBR > MACD nur für BTC/QQQ/AAPL

## [2026-07-15] ingest | 1 Quelle verarbeitet — Backtest-Analyse

- `(intern)` → `wiki/sources/2026-07-15_backtest-kombinations-strategien.md`
- Konzepte berührt: [[tdom-saisonalitaet]], [[bollinger-mean-reversion]], [[profit-factor-vs-sharpe]], [[look-ahead-bias-backtest]]

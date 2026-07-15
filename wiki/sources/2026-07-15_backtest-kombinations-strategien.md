---
title: "Backtest: Saisonalität + Technische Indikatoren — Erste Ergebnisse"
source_type: analysis
date_ingested: 2026-07-15
quality: intern
tags: [backtest, saisonalitaet, tdom, rsi, macd, bollinger, gld, msft, nvda, spy, qqq]
status: ingested
---

## Kontext

Erster systematischer Test der Kombination aus **TDOM-Saisonalität + technischem Indikator**
auf 7 Benchmark-Ticker. Zeitraum: 2005–Juli 2026 (~21 Jahre; BTC ab 2014, ~12 Jahre).

Bestehende Infrastruktur: `shared/backtest_engine.py` (727 Zeilen), `shared/indicators.py`
(RSI, MACD, Bollinger, SMA, EMA, LBR), `landing/pages/backtest-engine.html` (4-Tab-UI).

---

## Getestete Strategien

| ID | Name | Saisonales Signal | Technischer Filter | Halteperiode |
|----|------|-------------------|--------------------|--------------|
| A | Seasonal-RSI Reversal | TDOM Top-20% | RSI(14) < 40 | 10 HT |
| B | Seasonal Trend Filter | TDOM Top-30% | Close > SMA(200) | 15 HT |
| C | Seasonal MACD Crossover | TDOM Top-25% | MACD bullish Cross | 10 HT |
| D | Seasonal Bollinger Bounce | TDOM Top-30% | Close < BB Lower (20, 2σ) | 15 HT |
| E | Pure Seasonality Baseline | TDOM Top-20% | — keiner — | 10 HT |

Ticker: SPY, QQQ, AAPL, GLD, BTC-USD, NVDA, MSFT

---

## Kern-Ergebnisse (Sharpe-Ratio)

| Ticker | E Baseline | A RSI<40 | C MACD-X | D Boll-Bounce |
|--------|-----------|----------|----------|---------------|
| GLD    | 0.45      | 1.30     | 0.95     | **2.50**      |
| MSFT   | 0.58      | 1.07     | 1.24     | **1.43**      |
| NVDA   | 0.47      | 0.63     | 1.18     | **2.20**      |
| SPY    | 0.62      | 0.73     | **0.88** | 0.63          |
| QQQ    | 0.41      | 0.64     | **0.94** | 0.74          |
| BTC    | 0.85      | 0.78     | **0.90** | 0.83          |
| AAPL   | 0.54      | **0.94** | 0.06 ❌  | 0.35          |

*Strategie B (SMA200) wegen Look-Ahead-Bias im TDOM-Fenster nicht in Vergleich aufgenommen.*

---

## Top-Kombinationen

| Rang | Strategie | Ticker | PF   | Sharpe | Win-Rate | N-Trades | MaxDD% |
|------|-----------|--------|------|--------|----------|----------|--------|
| 1    | D — Bollinger Bounce | GLD  | 4.82 | 2.50 | 76.1% | 46  | -9.1%  |
| 2    | D — Bollinger Bounce | NVDA | 3.85 | 2.20 | 71.0% | 31  | -21.5% |
| 3    | D — Bollinger Bounce | MSFT | 2.34 | 1.43 | 59.6% | 47  | -20.8% |
| 4    | A — RSI Reversal     | GLD  | 2.05 | 1.30 | 68.2% | 88  | —      |
| 5    | C — MACD Cross       | MSFT | 1.91 | 1.24 | 67.4% | 92  | -15.1% |
| 6    | C — MACD Cross       | NVDA | 1.85 | 1.18 | 57.5% | 87  | -46.8% |
| 7    | A — RSI Reversal     | MSFT | 1.75 | 1.07 | 61.5% | 91  | —      |
| 8    | C — MACD Cross       | QQQ  | 1.64 | 0.94 | 66.7% | 87  | -19.8% |
| 9    | A — RSI Reversal     | AAPL | 1.67 | 0.94 | 53.0% | 83  | —      |
| 10   | C — MACD Cross       | GLD  | 1.61 | 0.95 | 56.0% | 75  | -15.4% |

---

## Kern-Erkenntnisse

### 1. Technische Filter erhöhen den Edge deutlich
Die Baseline (E) liefert bei GLD Sharpe 0.45 — Strategie D bringt dasselbe Signal auf 2.50
(+456%). Technische Filter sind kein Rauschen, sie reduzieren schlechte Entry-Zeitpunkte.

### 2. GLD + Bollinger Bounce ist der stärkste Fund
- PF 4.82, Sharpe 2.50, Win-Rate 76.1%, MaxDD nur -9.1%
- 46 Trades über 21 Jahre (~2.2/Jahr) — selektiv, aber konsistent
- Interpretation: Gold reagiert auf saisonale Tiefpunkte besonders zuverlässig mit
  Mean-Reversion. Die Kombination aus "saisonales Kauffenster" + "technisch überverkauft"
  filtert genau die besten Einstiege heraus.

### 3. Bollinger Bounce bevorzugt Low-Volatility-Assets
D funktioniert bei GLD und MSFT (geringer MaxDD) sehr gut, aber NVDA hat -21.5% MaxDD
trotz gutem Sharpe — hohe Eigenvolatilität macht den BB-Bounce riskanter.

### 4. MACD-Crossover ist der vielseitigste Filter
C funktioniert auf 6 von 7 Tickern positiv (Ausnahme AAPL). Besonders stark bei
SPY/QQQ (Indizes): Sharpe 0.88/0.94 vs. Baseline 0.62/0.41.

### 5. RSI-Reversal (A) ist defensiver als D, handelbarer als C
Mehr Trades als D (83–91 statt 31–47), mehr Selektivität als E (258). Guter Kompromiss
für Ticker wie AAPL wo Bollinger und MACD schwächeln.

### 6. AAPL ist ein Ausreisser — Vorsicht
- MACD-Strategie C: Gesamt-Verlust -13.8% über 21 Jahre (PF 1.03)
- Bollinger Bounce D: PF 1.27, MaxDD -45.4%
- Nur RSI-Reversal A funktioniert (PF 1.67, Sharpe 0.94)
- Wahrscheinliche Ursache: AAPL-Earnings und Momentum-Phasen überlagern saisonale Muster.
  MACD reagiert zu spät (träger Indikator), BB-Breakouts bei AAPL sind häufiger echte Trends.

### 7. BTC-USD zeigt überraschend konsistenten Edge
- Nur 12 Jahre Daten, trotzdem solide Ergebnisse über alle Strategien
- Baseline (E) hat hier den höchsten Sharpe (0.85) — technische Filter helfen weniger
- Mean-Reversion-Logik bei BTC schwächer als bei GLD (mehr Trend-dominiert)

---

## Methodische Einschränkungen

### TDOM-Look-Ahead-Bias (alle Strategien)
Die TDOM-Stärke wird aus dem gesamten historischen Datensatz berechnet, nicht rollend.
Das bedeutet: der Backtester "weiß" im Jahr 2005 bereits, welche TDOMs bis 2026 gut waren.
**Effekt:** Win-Rates und PF sind um ~10-20% zu optimistisch.
**Fix:** Walk-Forward-Kalibrierung (TDOM-Stärke jährlich nur aus Vorjahres-Daten berechnen).

### Strategie B (SMA200) ausgeschlossen
SMA200 + breiter TDOM-Top30% → sehr viele Trades, kaum Filterung (SPY fast immer > SMA200).
Zusätzlich kein Rolling-TDOM → extreme Calmar-Werte (AAPL: 4654, BTC: 1485) — unrealistisch.

### Kleine Trade-Zahlen bei D
Strategie D hat nur 31-47 Trades über 21 Jahre. Statistische Signifikanz ist begrenzt —
ein schlechtes Jahr kann das gesamte Ergebnis kippen. Für produktiven Einsatz
Walk-Forward mit mindestens 3-5 Jahren Out-of-Sample-Periode empfohlen.

### Sharpe-Berechnung (vereinfacht)
Sharpe wird trade-by-trade berechnet, annualisiert mit sqrt(252/Halteperiode). Kein
Risiko-freier Zins abgezogen. Reale Sharpe wäre leicht niedriger (Transaktionskosten,
Slippage nicht modelliert).

---

## Offene Fragen

- Hält der GLD-Bollinger-Bounce-Edge einem echten Walk-Forward stand?
- Warum AAPL so schwach bei MACD/Bollinger? Earnings-Kalender als Zusatz-Filter?
- LBR Oscillator (Raschke, 3/10/16) noch nicht getestet — könnte MACD übertreffen
- Kombinationen mit **Stop-Loss** noch nicht untersucht (Engine unterstützt es bereits)
- Ist der NVDA-Bollinger-Bounce (PF 3.85, Sharpe 2.20) trotz 31 Trades statistisch valide?
- DAX, ^GSPC, Gold Futures (GC=F) als weitere Kandidaten?

## Verlinkte Konzepte

- [[tdom-saisonalitaet]]
- [[bollinger-mean-reversion]]
- [[profit-factor-vs-sharpe]]
- [[look-ahead-bias-backtest]]

---
title: "What Machine Learning Finds in 30 Years of Market Data — and Why the Bear Regime Surprises"
seo_title: "Machine Learning Market Regimes: The Bear Surprise"
slug: ml-regime-clustering-bear-market-mean-reversion
de_slug: ml-regime-clustering-baerenmarkt-mean-reversion
date: 2026-07-31
author: SeasonAlpha Research
category: education
tags: [machine-learning, market-regimes, clustering, mean-reversion, turn-of-month, dax, spy, walk-forward]
description: "KMeans and logistic regression on 30 years of market data: the bear regime delivers the highest Sharpe — and the DAX beats the SPY under an ML filter."
ticker: ^GDAXI
status: published
---

<!--
Keyword-Plan:
- Main keyword: machine learning market regimes
- Secondary keywords: market regime detection, KMeans clustering stocks, mean reversion bear market, turn-of-month DAX, logistic regression trading, walk-forward analysis, regime filter strategy, ML stock market analysis
- LSI keywords: rolling volatility, Sharpe ratio, maximum drawdown, forward return, cluster, unsupervised learning, classifier, overfitting, backtest, normalized returns, trading days
-->

## We Pointed Two ML Algorithms at Our Own Data

Machine learning and market regimes — the combination sounds like a black box that eventually prints "buy". That is explicitly not what this is. We applied two classical, well-understood algorithms to the SeasonAlpha price database and looked at what structure they actually find in 30 years of market data.

The most interesting result contradicts intuition. The regime the algorithm labels **"bear"** delivers the **highest risk-adjusted forward returns** of all three detected states. And a regime filter that avoids exactly those phases makes an otherwise solid seasonal strategy substantially worse.

The second finding concerns the turn-of-month effect: an ML classifier on the month boundary works clearly better on the **DAX** than on the S&P 500. Both results in detail.

## What Regime Clustering Actually Does

A market regime is simply a phase with a consistent character — a calm uptrend, a nervous sideways stretch, a volatile sell-off. Humans recognise this in a chart intuitively, but without a fixed definition.

**KMeans clustering** is an unsupervised learning method. It receives no labels, only data points and the number of groups to look for (k). The algorithm assigns each data point to the group whose centre is closest, then shifts those centres until nothing changes any more.

Our setup:

- **Data:** SPY, 1993 to 2026, **8,432 trading days**
- **Features:** rolling return and rolling volatility — in other words, "how strongly did it move recently" and "how choppy was it while doing so"
- **k = 3**, so three regimes

One point matters for interpretation: both features are **backward-looking**. The algorithm only knows what has happened, never what comes next. That is precisely what makes the result instructive.

## Finding 1: Three Regimes — and the Weakest One Is the Strongest

Once the clustering is done, the three groups can be named from their features. We then measured the annualised Sharpe ratio the market delivered in the days *following* each regime. The Sharpe ratio relates return to the volatility taken on — the higher, the better the trade-off.

| Regime | Share of trading days | Ann. Sharpe (forward) |
|---|---|---|
| Bull | 15% | **+0.01** |
| Sideways | 68% | +0.63 |
| **Bear** | 17% | **+0.89** |

The result inverts the naive expectation.

**The bull regime is essentially worthless.** A Sharpe of +0.01 means that after a strong, calm advance, on average nothing more happens. Buying only once the chart already looks unambiguously good means buying the move that has already run.

**The ordinary state carries the portfolio.** At 68% of trading days, "sideways" is the clear majority — and at +0.63 it produces a solid Sharpe ratio. The market earns most of its money in unspectacular phases.

**The bear regime is the strongest mean-reversion phase.** At +0.89 it delivers the highest risk-adjusted forward return of the three states, across 17% of all days.

### Why This Is Not a Coincidence

The mechanism is explainable. KMeans only sees the **lagged** negative trend: prices that have fallen, volatility that has risen. The algorithm therefore classifies the state **after** the decline.

And that is exactly where mean reversion operates — the statistical tendency of prices to return toward their average after large moves. The "bear" label does not mark the start of the fall; in many cases it marks its end. An investor who sits on their hands or exits in this state systematically misses the recovery rally.

## The Practical Test: When the Regime Filter Hurts

A regime model is only as good as what you do with it. So we applied it to a known seasonal strategy: stay invested only in the historically strong months **April, November and December** — a pattern we analysed in detail in our [sector ETF article](/en/blog/sector-etf-seasonality-april-november-december/).

Then the extra rule: do not invest during phases the model classifies as "bear".

| Strategy | CAGR | Sharpe |
|---|---|---|
| Buy & hold | **10.7%** | 0.55 |
| Seasonal, naive (Apr/Nov/Dec) | 5.3% | **1.13** |
| Seasonal + regime filter (avoid bear) | 2.5% | 0.76 |

Three things sit in this table.

**The seasonal strategy has the best efficiency.** A Sharpe of 1.13 against 0.55 for buy and hold — more than twice the return per unit of risk. The price: only 5.3% CAGR instead of 10.7%, because the capital sits out of the market for most of the year.

**The regime filter makes everything worse.** Annual return halves to 2.5%, the Sharpe ratio falls from 1.13 to 0.76. The filter removes precisely the phases with the highest forward returns — it cuts out the best entries.

**More model is not automatically better.** An additional, plausible-sounding filter can systematically damage a working rule. That may be the single most useful practical lesson from the whole exercise.

## Finding 2: Turn-of-Month With ML — the DAX Surprise

The second algorithm is a **classifier**: logistic regression, a supervised method that estimates the probability of a binary event from historical features — here, "will the market rise in the next window?"

As the window we chose the [turn-of-month effect](/en/blog/turn-of-month-effect-explained/): the **last three and first three trading days** of a month. This stretch is considered one of the most robust calendar anomalies there is, driven by salary payments, savings plan executions and fund inflows around the first of the month.

The testing method matters most: **walk-forward from 2016 to 2026**. The model is trained only on past data, then applied to the next, unseen segment; afterwards the window rolls forward. This largely rules out overfitting, because the model cannot learn from data that did not yet exist at the moment of the trade.

| Market | Turn-of-month + ML (Sharpe) | Buy & hold (Sharpe) |
|---|---|---|
| SPY (S&P 500) | 0.40 | **0.81** |
| **DAX (^GDAXI)** | **0.85** | 0.66 |

On **SPY** the ML filter brings no advantage — 0.40 against 0.81 for plain buy and hold. In a decade that was a near-uninterrupted bull market for US equities, almost any strategy that sits on the sidelines part of the time loses.

On the **DAX** the picture flips. Sharpe 0.85 against 0.66 — and the risk gap is even wider: maximum drawdown of **–8.6% instead of –26.4%**. The drawdown measures the largest decline from peak to trough, which is the phase investors actually feel.

**GLD** (gold ETF) also shows a clear risk advantage: maximum drawdown of **–9.3% instead of –26.4%**, though without the DAX's return edge.

### Why the DAX of All Markets?

One plausible explanation: the DAX is shaped more strongly by **calendar-driven capital flows** than the S&P 500. European indices react more sensitively to recurring inflows at the start of the month, while the US market is dominated by a handful of globally traded mega caps whose pricing is driven year-round by news, earnings and international flows.

The seasonal annual path of the DAX over ten years shows the structure in which the month-boundary pattern is embedded:

{{chart:seasonal_yearly:^GDAXI:10}}

The chart uses **normalized returns**: each year starts at 100 and daily returns compound on top. Absolute price differences are never summed across years — otherwise later years at higher index levels would dominate the picture. The shaded band shows the dispersion (±1 standard deviation) and therefore how reliable the average path actually is.

## Limits: What These Numbers Do Not Say

Four caveats belong here.

**A regime label is not a forecast.** KMeans describes yesterday's state. The fact that "bear" was historically followed by above-average returns is an observation across 8,432 trading days — not a guarantee for the next sell-off. In 2008 the same logic would have bought in far too early for months.

**The evaluation period is unusual.** 2016 to 2026 contains an exceptional bull run for US equities. That the SPY classifier loses against buy and hold says as much about this specific decade as about the method.

**Sharpe ratios without a risk-free rate.** All Sharpe figures quoted here are pure return-to-volatility ratios. They are comparable with each other, but not with numbers from external sources.

**Costs and taxes are missing.** The turn-of-month strategy trades up to 24 times a year. Spreads, commissions and capital gains tax appear in none of these figures and would visibly reduce the edge.

## What Private Investors Can Take Away

Three practical conclusions.

**First: panic is statistically expensive.** The bear cluster was historically the phase with the best forward returns. Selling after sharp declines means, on average, selling into the recovery.

**Second: filters need evidence, not plausibility.** "Do not invest when the market looks bad" sounds sensible and pushed the Sharpe ratio from 1.13 down to 0.76. Every additional rule deserves a backtest — ideally walk-forward.

**Third: effects are market-specific.** The same turn-of-month approach produces an edge on the DAX and none on the SPY. If you adopt a pattern, test it on your own target market, not on the one it was published for.

You can recompute all of this directly in SeasonAlpha:

- **[Turn of month](/en/monatswechsel)** — the turn-of-month curve with significance gauge (t-value, p-value, win rate, n) for any ticker
- **[TDOM analysis](/en/tdom-analyse)** — return per trading day of the month, computed per exchange
- **[Backtest engine](/en/backtest-engine)** — combine your own calendar rules with indicator filters and test them for robustness
- **[Annual cycle](/en/jahreszyklus)** — the normalized annual path for `^GDAXI` or any other ticker

## Conclusion

Two ML methods, two uncomfortable results. The regime the algorithm labelled "bear" delivered the **highest risk-adjusted forward return across 8,432 trading days (Sharpe +0.89)** — well ahead of the ordinary state (+0.63) and the seemingly attractive bull regime (+0.01). A filter avoiding those phases cost more than half the return in our test.

The turn-of-month classifier shows that calendar effects are not universal: on the DAX the walk-forward test produced a genuine advantage (Sharpe 0.85 versus 0.66, drawdown –8.6% instead of –26.4%), on the SPY it did not.

Machine learning delivers no recommendation here, only a description: it shows where structure sits in the data — and where an intuitively sensible rule points in the wrong direction. Check the turn-of-month statistics for your own ticker at **[seasonalpha.ai](https://seasonalpha.ai/en/monatswechsel)**.

## Frequently Asked Questions

### What is a market regime?
A market regime describes a market phase with a consistent character, for example in terms of trend direction and volatility. In our analysis, KMeans clustering found three such states in SPY data since 1993: bull (15% of trading days), sideways (68%) and bear (17%). The labels come from the rolling-return and rolling-volatility features, not from any manual classification.

### Why does the bear regime deliver the best forward returns?
Because the model describes the state after a decline, not before it. The features are backward-looking, so the "bear" label marks fallen prices and elevated volatility. That is exactly the situation in which mean reversion — the return toward the average — statistically tends to kick in. Historically this produced the highest annualised Sharpe ratio of the three regimes (+0.89).

### What does walk-forward analysis mean?
The model is trained only on data that precedes the test period, then applied to the following unseen segment; afterwards the window rolls forward. This prevents results that depend on knowledge of the future — the most common reason backtests look brilliant on paper and fail in practice.

### Can I use these ML models in SeasonAlpha myself?
The models described here are research analyses on the SeasonAlpha data set, not a product feature. The underlying patterns are directly checkable, though: the turn-of-month effect including significance testing lives on the [turn of month](/en/monatswechsel) page, and your own rule combinations can be tested in the [backtest engine](/en/backtest-engine).

<!--
#### Social Media Snippet

**LinkedIn:** We pointed two classical ML methods at 30 years of market data — and the result contradicts intuition. 📊 KMeans clustering (SPY, 8,432 trading days since 1993) finds three regimes. The one labelled "bear" delivers the HIGHEST risk-adjusted forward return: Sharpe +0.89, ahead of sideways (+0.63) and bull (+0.01). The reason: the model sees the lagged decline — and that is exactly where mean reversion kicks in. The consequence: a regime filter avoiding bear phases pushed a seasonal strategy from Sharpe 1.13 down to 0.76 and halved the return. Second finding: turn-of-month with logistic regression (walk-forward 2016–2026) works on the DAX (Sharpe 0.85 vs 0.66 B&H, max drawdown –8.6% instead of –26.4%) but not on the SPY. Calendar effects clearly are not universal. Which filters do you use — and have you backtested them? #MachineLearning #Seasonality #DAX #SeasonAlpha

**Twitter/X:** ML on 30 years of market data: the regime the algorithm labels "bear" delivers the highest risk-adjusted forward return (Sharpe +0.89) — ahead of sideways (+0.63) and bull (+0.01). The filter that avoids bear? Halves the return. 📊 seasonalpha.ai #MachineLearning #Seasonality #SeasonAlpha

#### Interne Verlinkung
- /en/monatswechsel (turn-of-month curve with significance gauge)
- /en/tdom-analyse (return per trading day of the month)
- /en/backtest-engine (walk-forward test your own rule combinations)
- /en/jahreszyklus (normalized DAX annual path)
- /en/blog/turn-of-month-effect-explained/ (fundamentals of the effect)
- /en/blog/turn-of-month-effect-still-alive/ (current robustness check)
- /en/blog/sector-etf-seasonality-april-november-december/ (the Apr/Nov/Dec base strategy)
- /en/blog/dax-vs-sp500-seasonality/ (why the two indices behave differently)

#### Content-Ideen (Folgeartikel)
- "Measuring mean reversion: how strongly does the market bounce back after declines?"
- "Spotting overfitting in a backtest — 5 warning signs"
- "Why the DAX is more calendar-driven than the S&P 500"
- "Regime detection without ML: what simple volatility thresholds achieve"
-->

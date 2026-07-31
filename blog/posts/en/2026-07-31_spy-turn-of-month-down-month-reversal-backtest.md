---
title: "The Turn-of-Month Effect Has a Timing Problem — and a Down Month Solves It"
seo_title: "SPY Turn-of-Month Works Better After Down Months"
slug: spy-turn-of-month-down-month-reversal-backtest
de_slug: spy-turn-of-month-down-monat-reversal-backtest
date: 2026-07-31
author: SeasonAlpha Research
category: education
tags: [spy, turn-of-month, tdom, mean-reversion, backtest, short-term-reversal, seasonal-strategy, jegadeesh, carhart]
description: "SPY turn-of-month over 15 years: after a negative month the average trade return rises from 0.75% to 1.25% — with a smaller maximum drawdown."
ticker: SPY
status: published
---

<!--
Keyword-Plan:
- Main keyword: SPY turn-of-month effect
- Secondary keywords: turn-of-month strategy backtest, short-term reversal, mean reversion stock market, TDOM trading day of month, SPY seasonality backtest, profit factor strategy, down month filter, momentum filter DAX
- LSI keywords: win rate, Sharpe ratio, maximum drawdown, trading days, capital inflows, rebalancing, liquidity cycle, normalized returns, look-ahead bias, statistical significance
-->

## Not Whether, but When

The turn-of-month effect is one of the best documented calendar anomalies in finance: around the month boundary, equity markets earn a disproportionate share of their annual return. The more interesting question is not **whether** the effect exists — it is **when** it hits hardest.

Our 15-year backtest on **SPY** gives a clear answer. Trade every month boundary the same way and you get an average of **+0.75% per trade** across 186 trades. Trade only those month boundaries where the market had **fallen** beforehand, and the same average climbs to **+1.25% per trade** — 67 percent higher.

The most notable part: maximum drawdown falls from 22.3% to 18.3% at the same time. More return for less pain is the exception in backtesting, not the rule.

## The Turn-of-Month Effect in 60 Seconds

The effect describes a simple observation. The final trading days of one month and the first of the next historically deliver above-average returns — far more than their share of trading days would suggest.

**Robert Ariel (1987)** was the first to document this systematically. In "A Monthly Effect in Stock Returns" he showed that essentially all of the market's positive return accrued in the first half of the month. **Joseph Ogden (1990)** supplied the economic mechanism: the **liquidity cycle**. Salaries, pensions, coupon payments and dividends are paid out in a cluster around the month boundary, and part of that money flows into equities on schedule — through savings plans, pension fund inflows and institutional rebalancing.

This is not a psychological pattern but a **structural capital flow**. That is precisely why the effect has proven durable: it is anchored in the payment infrastructure of the economy, not in investor sentiment. We covered the mechanics in detail in [The turn-of-month effect explained](/en/blog/turn-of-month-effect-explained/).

## The Idea: Stacking Two Anomalies

If the inflow at the start of the month is roughly constant, then its **effect on price** should depend on the state of the market receiving it. That is where a second, independently documented anomaly enters.

**Narasimhan Jegadeesh (1990)**, in "Evidence of Predictable Behavior of Security Returns", showed that short-horizon returns are **negatively autocorrelated**: what fell over the past month tends to rise above average in the following one. This **short-term reversal** is the counterpart to the better-known 12-month momentum factor, and it operates on exactly the time scale that matters here.

That gives us the hypothesis: the turn-of-month inflow arrives into an already depressed market after a weak month — and moves it further. There are two plausible reasons.

**First, selling pressure into month end.** When a month goes badly, pressure into the final session increases: funds tidy up reporting, risk models cut exposure as volatility rises, investors harvest losses. The market is oversold at the boundary.

**Second, the inflow does not care.** The savings plan executes on the first of the month regardless of how the previous one went. The same demand meets a lower price level — and mechanically moves it more.

## The Setup: What Exactly Was Tested

To put the numbers in context, here is the exact configuration.

| Parameter | Setting |
|---|---|
| Instrument | SPY (S&P 500 ETF) |
| Period | 15 years |
| Event | TDOM 17–22 (month-end window) |
| Entry | 3 trading days before the event |
| Exit | 10 trading days after the entry signal |
| Price basis | close to close |
| Stop loss | none |
| Filter (variant 2) | 21-day return < 0 |

**TDOM** stands for *trading day of month* — the sequentially counted trading session inside a month, not the calendar date. Depending on month length, the 17th to 22nd trading day marks the month-end window. The distinction matters: holidays and weekends shift the calendar date, but not the trading day count.

The holding period therefore spans roughly 13 trading days that straddle the month boundary. The filter checks a single condition: was the return over the past 21 trading days — roughly one market month — below zero?

## The Numbers: Baseline Versus Down-Month Filter

| Metric | SPY ToM (unfiltered) | SPY ToM after down month |
|---|---|---|
| Number of trades (n) | 186 | 78 |
| Win rate | 68.3% | **71.8%** |
| Avg return per trade | +0.75% | **+1.25%** |
| Profit factor | 1.80 | **2.39** |
| Sharpe ratio | +0.21 | **+0.34** |
| Max drawdown | 22.3% | **18.3%** |

Four observations sit in this table.

**The baseline is already solid.** A 68.3% win rate across 186 trades and a profit factor of 1.80 — the profit factor divides the sum of all gains by the sum of all losses, so 1.80 means 1.80 dollars won for every dollar lost. The turn-of-month effect works without any filter at all.

**The filter improves every single metric.** Win rate, average return, profit factor and Sharpe ratio all move in the same direction. That is a meaningful robustness signal: a filter that lifts one metric while degrading others is usually an artefact of data selection.

**The return jump is the real finding.** Going from +0.75% to +1.25% per trade is 67 percent more return per position, with only a modest gain in hit rate. The improvement therefore comes less from more winners than from **bigger** winners. That is exactly what mean reversion predicts: the bounce off a depressed level is sharper.

**Less drawdown despite a stronger edge.** 18.3% instead of 22.3% peak-to-trough decline. The filter keeps the strategy out of the market during stretches where the month boundary historically carried less weight.

The complementary case can be derived from these figures: the 108 trades **following a positive prior month** average only about **+0.4% per trade**. In other words, the entire return advantage of the turn-of-month effect concentrates in the 42 percent of month boundaries preceded by a loss.

## Where This Window Sits in the Annual Path

The month boundary is only one of several time structures inside SPY. The normalized annual path shows the larger pattern these trades take place in:

{{chart:seasonal_yearly:SPY:15}}

The chart uses **normalized returns**: each year starts at 100 and daily returns compound on top. Absolute price differences are never summed across years — otherwise later years at much higher index levels would dominate the picture. The shaded band (±1 standard deviation) shows how reliable the average path actually is.

One clarification: the down-month filter is **not a seasonal filter**. It does not trigger in specific calendar months but whenever the market has recently fallen — whether that happens in March or in October.

## The Counter-Test: Why the Same Trick Fails on the DAX

A single positive result means little unless you also show what did **not** work. In parallel we tested a second filter: **12-month momentum excluding the most recent month** — the standard definition from **Mark Carhart's (1997)** four-factor model. The idea being: only trade when the broader trend is intact.

Applied to the DAX month boundary, the Sharpe ratio dropped from **0.07 to 0.04**. The filter did not help; it did marginal harm.

The reason lies less in the filter than in the base case. A Sharpe ratio of 0.07 is practically indistinguishable from zero. In this test the DAX turn-of-month effect was simply **too weak to amplify**. A filter can sharpen an edge that exists; it cannot manufacture one that does not.

This matches what we found in our [ML regime analysis](/en/blog/ml-regime-clustering-bear-market-mean-reversion/): additional rules do not automatically improve a strategy — several plausible-sounding filters did measurable damage there.

## Methodology Note

Three points that determine how much weight these numbers can carry.

**Normalized returns.** All analyses and charts use percentage returns normalized to 100. Summing absolute price changes over long horizons biases any multi-year statistic toward the more recent years.

**Trading days, not calendar days.** TDOM is counted per exchange from the actual trading calendar, including that exchange's holidays. The filter's 21-day lookback is likewise 21 **trading** days.

**Free of look-ahead bias.** The filter is evaluated on the state of the **day before** the entry bar, not on the entry bar itself. A backtest that evaluates the condition on the entry bar uses information that was not fully available at the moment of the trade — one of the most common reasons backtests shine on paper and disappoint live.

## Limits: What These Numbers Do Not Say

**78 trades is not a large sample.** The filtered data set contains 78 observations across 15 years. That is enough for an indication, not for proof. In small samples, a handful of outliers can move the average noticeably.

**Costs and taxes are missing.** The strategy trades up to twelve times a year. Spreads, commissions and capital gains tax appear in none of these numbers and would reduce the edge in practice.

**The period is US-friendly.** Fifteen years of SPY contain a historically exceptional advance. Any long-only strategy benefits from that.

**Sharpe without a risk-free rate.** The figures are pure return-to-volatility ratios. They are comparable with each other, not with numbers from external sources.

**No stop loss.** The test runs without downside protection. The 18.3% drawdown is something you would have had to sit through.

## Recompute It Yourself

The most useful part of any backtest is the part you vary yourself. The configuration can be rebuilt directly in SeasonAlpha:

- **[Backtest engine](/en/backtest-engine)** — load the **"SPY Down-Month Reversal"** preset, or set it manually: event TDOM, range 17–22, entry −3, exit +10, filter 21-day return < 0
- **[Turn of month](/en/monatswechsel)** — the turn-of-month curve with significance gauge (t-value, p-value, win rate, n) for any ticker
- **[TDOM analysis](/en/tdom-analyse)** — average return per trading day of the month, computed per exchange
- **[Annual cycle](/en/jahreszyklus)** — the normalized annual path for SPY or any other instrument

Worthwhile variations: shorten the exit from +10 to +5 trading days, change the filter lookback to 10 or 42 days, or run the whole thing on QQQ, IWM and individual sector ETFs. If the effect collapses under small parameter changes, it was probably noise.

## Conclusion

The SPY turn-of-month effect is intact across 15 years and 186 trades: a 68.3% win rate, profit factor 1.80, **+0.75% per trade**. Trade it exclusively after a **negative prior month** and you get a 71.8% win rate, profit factor 2.39 and **+1.25% per trade** — with a maximum drawdown four percentage points lower.

The explanation needs no new theory. Ariel's month-boundary inflow meets Jegadeesh's short-term reversal: two effects documented for decades, operating on the same time scale and stacking on top of each other.

The DAX counter-test supplies the necessary humility: where the base edge is missing, no filter will save you. Test your own ticker in the **[backtest engine](https://seasonalpha.ai/en/backtest-engine)** — the difference between a real pattern and a pretty equity curve only shows up once you start moving the parameters.

## Frequently Asked Questions

### What exactly is the turn-of-month effect?
The turn-of-month effect describes the observation that the last trading days of a month and the first of the next historically deliver above-average returns. Robert Ariel documented it systematically in 1987, and Joseph Ogden explained it in 1990 through the liquidity cycle: salaries, pensions and fund inflows take effect in a cluster around the month boundary. In our 15-year SPY test, the unfiltered version had a win rate of 68.3%.

### Why does the effect work better after a losing month?
Two mechanisms interact. Ahead of a weak month end, selling pressure increases through reporting cosmetics, risk models and loss harvesting — the market is depressed. The scheduled inflow at the start of the next month is unaffected by this and meets a lower price level. Statistically this corresponds to the short-term reversal described by Jegadeesh (1990). In our test the average return per trade rose from 0.75% to 1.25% as a result.

### What does TDOM 17–22 mean?
TDOM stands for *trading day of month*, the sequentially counted trading session inside a month. Depending on the length of the month, the 17th to 22nd trading day marks the month-end window. The count is derived per exchange from the actual trading calendar, because holidays shift the calendar date but not the trading day number.

### Why did the momentum filter fail on the DAX?
We applied the classic Carhart momentum filter (12 months excluding the most recent month) to the DAX month boundary, and the Sharpe ratio fell from 0.07 to 0.04. The reason lies in the base case: a Sharpe ratio of 0.07 is statistically hard to distinguish from zero. A filter can sharpen an existing advantage, but it cannot create one that is not there.

### Is a sample of 78 trades meaningful?
Only to a limited extent. Seventy-eight observations across 15 years give a reasonable indication, not proof — individual outliers can move the average noticeably. That is why the consistency check matters more than any single figure: the fact that win rate, average return, profit factor and drawdown all improve simultaneously argues more for a genuine relationship than for chance.

<!--
#### Social Media Snippet

**LinkedIn:** The turn-of-month effect is well documented. The more interesting question is not whether it works, but when. Our 15-year SPY backtest (TDOM 17-22, entry -3 trading days, exit +10, close to close): unfiltered, 186 trades, 68.3% win rate, profit factor 1.80, +0.75% per trade. Filtered to month boundaries preceded by a negative month (21-day return < 0): 78 trades, 71.8% win rate, profit factor 2.39, +1.25% per trade — and maximum drawdown falls from 22.3% to 18.3%. More return with less drawdown is rare in backtesting. The explanation is not a new theory but the overlap of two known effects: Ariel's month-boundary liquidity (1987) meeting Jegadeesh's short-term reversal (1990). Counter-test: a Carhart momentum filter on the DAX month boundary pushed the Sharpe ratio from 0.07 down to 0.04 — where there is no base edge, no filter helps. Which filters do you test on your calendar strategies? #Seasonality #Backtesting #Trading #SeasonAlpha

**Twitter/X:** SPY turn-of-month, 15-year backtest: unfiltered +0.75%/trade, 68.3% win rate. Only after a down month: +1.25%/trade, 71.8% win rate, profit factor 2.39 — and max drawdown drops from 22.3% to 18.3%. Ariel meets Jegadeesh. seasonalpha.ai #Seasonality #Backtesting #SeasonAlpha

#### Interne Verlinkung
- /en/backtest-engine (rebuild the "SPY Down-Month Reversal" preset)
- /en/monatswechsel (turn-of-month curve with significance gauge)
- /en/tdom-analyse (average return per trading day of the month)
- /en/jahreszyklus (normalized SPY annual path)
- /en/blog/turn-of-month-effect-explained/ (fundamentals of the effect)
- /en/blog/turn-of-month-effect-still-alive/ (robustness check)
- /en/blog/ml-regime-clustering-bear-market-mean-reversion/ (when filters hurt)
- /en/blog/dax-vs-sp500-seasonality/ (why the indices behave differently)

#### Content-Ideen (Folgeartikel)
- "Measuring short-term reversal: how strongly does the market bounce after weak months?"
- "Turn-of-month on QQQ, IWM and sector ETFs — where the effect is strongest"
- "How long should you hold the month boundary? Comparing exit windows"
- "Why the DAX month boundary is weaker than the US one"
-->

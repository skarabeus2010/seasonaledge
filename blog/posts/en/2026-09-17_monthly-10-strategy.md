---
title: "The Monthly 10 Strategy Tested: 32 Years of SPY, 10 Trading Days a Month — and a Surprising Driver"
seo_title: "Monthly 10 Strategy: 32 Years of SPY Backtested"
slug: monthly-10-strategy
de_slug: monthly-10-strategie
date: 2026-09-17
category: education
tags: [monthly-10, tdom, seasonality, turn-of-month, backtest, spy]
description: "Monthly 10 strategy backtested over 32 years: half the volatility, half the return — and the gains come from mid-month, not from the turn of month."
ticker: SPY
status: published
---

<!--
Keyword-Plan:
- Main keyword: Monthly 10 strategy
- Secondary: TDOM strategy, trading day of month, turn of month effect, seasonal trading strategy, SPY backtest, time in market, risk-adjusted return
- LSI: calendar effect, drawdown, volatility, buy and hold, cash, hit rate, S&P 500 ETF
-->

## Ten days out of 21 — is that enough?

The **Monthly 10 strategy** rests on one claim: equities do not earn their return evenly across the month, but on a handful of recurring trading days. Hold the market only on those days, sit in cash otherwise, and you should track the index with far less risk.

We ran the rule over 32 full calendar years of SPY (1994–2025, 8,054 trading days, adjusted close including dividends). The outcome is not what strategy marketing usually promises — and the most interesting finding has nothing to do with the turn of month everybody talks about.

## What the Monthly 10 strategy actually does

The strategy works off the **trading day of month** (TDOM). TDOM 1 is the first trading day of a month, TDOM 2 the second; weekends and exchange holidays do not count. Depending on the calendar, a month has 19 to 23 trading days.

The strategy is long only on these days:

- **TDOM 1–4** — start of month
- **TDOM 9–12** — mid-month
- **the last two trading days** — end of month

On every other day the money sits in cash, with no interest assumed. The marked days form three contiguous blocks per month, so three trades: in at the close of the first day of a block, out at the close of the last.

### Why the strategy is only in the market 33% of the time

Ten marked days out of roughly 21 sounds like almost 48% exposure. The real figure is **33.4%**. The reason is the entry convention: you buy at the **close** of the first day of a block. That day is already over when the position exists, so it contributes no return of its own.

Ten marked days therefore leave about seven return-bearing days. The detail sounds trivial, but it explains a large part of the numbers below — and it decides which block ends up looking good.

## The 32-year backtest: SPY 1994–2025

![Monthly 10 versus buy and hold: growth of USD 10,000 in SPY from 1994 to 2025 on a log scale — final value USD 56,883 against USD 259,463](/en/blog/monthly-10-strategy/images/monthly-10-strategie/monthly10-equity-spy-en.png)

The curves separate early and stay apart. Buy and hold turns USD 10,000 into USD 259,463 over the period; Monthly 10 reaches USD 56,883.

| Metric | Monthly 10 | Buy & Hold |
|---|---:|---:|
| Total return | 469% | 2,495% |
| Return p.a. (CAGR) | 5.58% | 10.71% |
| Volatility p.a. | 10.79% | 18.84% |
| Return per unit of risk | 0.52 | 0.57 |
| Maximum drawdown | −41.0% | −55.2% |
| Time in market | 33.4% | 100% |
| USD 10,000 grew to | USD 56,883 | USD 259,463 |

Two things stand out. First, the strategy nearly halves the swing and cuts the deepest interim loss by 14 percentage points. Second, it gives up more than half the return for that.

Divide return by risk and you get **0.52 against 0.57** — Monthly 10 is slightly behind. On a risk-adjusted basis this is not an edge over buy and hold; it is a wash with a small minus.

The annual scoreboard offers little more: Monthly 10 beat buy and hold in **10 of 32 years**, or 31% of the time.

## The real finding: mid-month carries the strategy

Each of the three blocks was traded 384 times over 32 years. Compound their contributions separately and the picture of what is actually working shifts.

![Contribution per block of the Monthly 10 strategy in SPY 1994–2025: start of month TDOM 1–4 plus 83 percent at a 60 percent hit rate, mid-month TDOM 9–12 plus 287 percent at 64 percent, end of month minus 20 percent at 46 percent](/en/blog/monthly-10-strategy/images/monthly-10-strategie/monthly10-bloecke-spy-en.png)

| Block | Trades | Hit rate | Cumulative contribution |
|---|---:|---:|---:|
| Start of month (TDOM 1–4) | 384 | 60% | +83% |
| Mid-month (TDOM 9–12) | 384 | 64% | +287% |
| End of month (last 2 days) | 384 | 46% | −20% |

The heavy lifting happens **mid-month**. TDOM 9–12 delivers more than three times the start-of-month block and carries the highest hit rate at 64%. The celebrated turn of month is not the engine here.

That matters, because the [turn-of-month effect](/en/monatswechsel) — strength around the month boundary — is among the most cited calendar patterns in equity research. In this particular rule set it comes in second.

### Limits of this decomposition

The minus in the end-of-month block is largely an artefact of the entry convention. Enter one trading day earlier, so that every marked day carries return, and the block flips from −20% to **+14%**, with the hit rate moving from 46% to 51%.

**Important:** the end-of-month block does not systematically lose money — it contributes close to nothing, and a technical rule detail decides on which side of zero it lands. What survives both conventions is the core statement: **mid-month carries the strategy, end of month is the weakest leg.**

### What about the days left out?

The 67% of the time Monthly 10 spends in cash was not worthless: those days compounded to **+356%**. They also carried the deeper setback — maximum drawdown across the excluded days was **−58.9%**, against −41.0% for the strategy days.

That is exactly the trade Monthly 10 makes: give up return in order to sit out the rougher stretches of the market.

## A counter-cyclical profile

The yearly returns show when the strategy shines and when it lags.

![Annual returns of Monthly 10 versus buy and hold in SPY from 1994 to 2025 as paired bars: ahead in bear years such as 2000, 2001, 2002, 2008 and 2022, behind in bull years such as 2013, 2023 and 2024](/en/blog/monthly-10-strategy/images/monthly-10-strategie/monthly10-jahre-spy-en.png)

In bear years Monthly 10 is ahead:

- **2000:** +11.4% vs. −9.7%
- **2001:** +8.1% vs. −11.8%
- **2002:** −1.2% vs. −21.6%
- **2008:** −27.8% vs. −36.8%
- **2022:** −2.5% vs. −18.2%

In strong bull years it falls well behind:

- **2013:** +5.4% vs. +32.3%
- **2023:** +6.1% vs. +26.2%
- **2024:** +2.3% vs. +24.9%

The pattern follows from the exposure. Invested only a third of the time, you capture a fraction of an advance — and miss two thirds of a decline. Still, 2008 shows the cushion is not protection: −27.8% is a hard year even for a cash-heavy rule set.

## What investors can take from this

Monthly 10 is a risk strategy, not a return strategy. It halves volatility and reduces drawdown, and it pays for that with more than half the return. On these numbers it is no substitute for a broad equity position.

It is more interesting as a **building block**: for portfolios where the swing is a hard constraint, or alongside a core holding. One item is missing from every figure above — **transaction costs**. Three trades a month means 36 round turns a year, and with no CAGR advantage to begin with, that comes straight out of the substance. Anyone testing the rule seriously has to model their own fees.

The most useful result is the decomposition. That TDOM 9–12 does most of the work suggests the calendar month has more structure than the single much-quoted turn-of-month window — and that it pays to examine individual trading days rather than judging rule packages as a whole.

Both are reproducible on SeasonAlpha: Monthly 10 sits in the [backtest engine](/en/backtest-engine) under the monthly patterns and can be applied to any ticker in the universe. The single-day view lives on the [turn-of-month page](/en/monatswechsel), the side-by-side comparison of rule sets on the [plain vanilla overview](/en/plain-vanilla). To see which tickers currently show a notable monthly pattern, start with the [seasonal scanner](/en/scanner). Related reading: our backtest on the [turn of month after down months](/en/blog/spy-turn-of-month-down-month-reversal-backtest/).

## Conclusion

Over 32 years of SPY, the Monthly 10 strategy delivers 5.58% p.a. against 10.71% for buy and hold, at 10.79% instead of 18.84% volatility and −41.0% instead of −55.2% maximum drawdown. Per unit of risk it comes out at 0.52 against 0.57 — slightly worse than simply staying invested.

The value is not in the headline result but in the breakdown: **mid-month (TDOM 9–12) contributes the most at +287%**, start of month follows at +83%, end of month contributes nothing. And because of the entry convention, time in market is 33.4%, not 48%.

**Not a signal:** these are averages over 32 years with wide dispersion, not a forecast for next month. Test the rule on your own tickers and periods at [seasonalpha.ai](https://seasonalpha.ai/en/backtest-engine).

## Frequently asked questions

### What is the Monthly 10 strategy?

A rule-based strategy that is long only on ten marked trading days per month: TDOM 1–4, TDOM 9–12 and the final two trading days. All other days are spent in cash. Trades happen at the close of the first and last day of each block, so three trades per month.

### Does Monthly 10 beat the market?

Not in our SPY backtest for 1994–2025. The strategy returns 5.58% per year against 10.71% for buy and hold and was ahead in only 10 of 32 years. It does reduce volatility (10.79% instead of 18.84%) and maximum drawdown (−41.0% instead of −55.2%). Risk-adjusted it still trails slightly, 0.52 against 0.57.

### What does TDOM mean?

TDOM stands for trading day of month. TDOM 1 is the first trading day, TDOM 2 the second. Weekends and exchange holidays are excluded, which is why TDOM drifts away from the calendar day — and why the listing venue with its own holiday calendar matters, not a company's home country.

### Why is the strategy invested only 33% of the time instead of 48%?

Because entry happens at the **close** of the first day of each block. That day has already played out and contributes no return. Ten marked days therefore leave roughly seven return-bearing days — 33.4% instead of the expected 48%.

### Which part of the month contributes most?

Mid-month. Across 384 trades per block, TDOM 9–12 compounded to +287% at a 64% hit rate, while the start of month (TDOM 1–4) delivered +83% at 60%. End of month contributes close to nothing, and whether it lands slightly negative or slightly positive depends on the entry convention.

<!--
#### Social Media Snippet

**LinkedIn:**
The Monthly 10 strategy is in the market on just 10 trading days a month — TDOM 1–4, 9–12 and the last two. We ran it over 32 years of SPY (1994–2025, adjusted close).
Result: 5.58% p.a. against 10.71% for buy and hold. In exchange, 10.79% instead of 18.84% volatility and −41.0% instead of −55.2% maximum drawdown. Per unit of risk: 0.52 vs 0.57 — no edge.
The real finding is in the decomposition: the driver is not the much-quoted turn of month but mid-month (TDOM 9–12) at +287% across 384 trades.
Which part of the month do you watch? → seasonalpha.ai

**Twitter/X:**
Monthly 10 over 32 years of SPY: 5.58% p.a. vs 10.71% buy & hold — but half the vol and −41% instead of −55% drawdown.
The driver is NOT the turn of month. It's mid-month (TDOM 9–12, +287%).
#Stocks #Seasonality #SeasonAlpha

#### Internal links
- /en/backtest-engine (run Monthly 10 yourself)
- /en/monatswechsel (turn-of-month single-day view)
- /en/plain-vanilla (rule sets compared)
- /en/scanner (notable monthly patterns by ticker)
- /en/blog/spy-turn-of-month-down-month-reversal-backtest/ (related backtest)

#### Content ideas (follow-ups)
- "TDOM 9–12: why mid-month is underrated" — single-day analysis across several indices
- "Monthly 10 on DAX, Nasdaq and gold" — does the finding hold outside the S&P 500?
- "What do 36 round turns a year cost?" — fee sensitivity test
-->

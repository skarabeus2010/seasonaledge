---
title: "Eleven Market Rules, Measured — Four Do Not Hold"
seo_title: "Stock Market Myths Tested: 11 Rules, 4 Debunked"
slug: market-rules-tested
de_slug: boersenregeln-nachgerechnet
date: 2026-09-22
category: education
tags: [statistics, seasonality, market-myths, significance, methodology]
ticker: SPY
status: published
description: "September the crash month? Factor 1.059 at p = 0.127. Eleven market rules measured on historical price data, each with question, result and data basis."
---

<!--
Keyword plan:
- Head keyword: market myths debunked / stock market rules backtested
- Entities in the text: stock market myths, market rules, market anomalies
- Secondary (rendered as question H3s): september october crash months, do bonds lead stocks,
  does bitcoin lead the stock market, pre-FOMC drift, expected move accuracy,
  monthly 10 strategy, S&P 500 addition effect, DAX september, expiration pinning
- LSI: significance test, permutation test, control group, effect size, sample size,
  pre-specified, multiple testing, data mining, confidence interval
-->

## September is not the crash month

Volatility in the S&P 500 during September and October runs at **1.059×** the rest of the year. Measured across 836 months from 1957 — and not distinguishable from random variation, **p = 0.127**.

That is one of eleven market rules we recomputed on our own price data, each with a question fixed before anything was calculated. **Seven hold. Four do not.**

Those four appear here at the same length as the other seven, for a practical reason: a rule that does not hold is precisely the one that costs money for as long as you follow it.

## The overview

| Rule | Result | Data base |
|---|---|---|
| Expiration-day pinning | **supported** · +0.35 pp, p = 0.0050 | 158 stocks, 30 years |
| DAX weak in September | **supported** · avg −1.55 %, p = 0.0241 | DAX, 68 years per month |
| The expected move is too wide | **supported** · 84.3 % instead of 68.3 % | VIX/S&P 500, 1990–2026 |
| Bonds as a leading indicator | **only under stress** · +2.09 % in two weeks | 50 cases since 2002 |
| Bitcoin leads | **only above 20 %** · nothing below | 12 years, 3,020 trading days |
| September/October more volatile | **not supported** · 1.059×, p = 0.127 | S&P 500 from 1957, 836 months |
| Intermarket signals | **not supported** · 0 of 470 pairings | 18 markets |
| Monthly 10 beats the market | **not supported** · 5.58 % against 10.71 % p.a. | S&P 500, 1994–2025 |
| Pre-FOMC drift | *descriptive* · +0.131 % the day before | S&P 500, 2006–2025 |
| Index addition lifts the price | *descriptive* · +5.8 % at T+20 | 36 additions |
| Midterm year | *descriptive* · +31 % afterwards on average | cycles since 1950 |

The three levels mean different things, and that difference is the actual subject of this article. **Supported** means the question was fixed beforehand, the difference is measured, and it survives a [significance test](/en/blog/p-value-explained/). **Descriptive** means the pattern is there but the number of observations carries no test — at 36 events a [p-value](/en/blog/p-value-explained/#multiple-testing) is false precision. In between sit the cases where the effect is tied to a condition you have to quote along with it.

## What holds

### Do prices cling to a strike on expiration day?

Yes, but barely. US equity options expire on the third Friday. Measured across 158 stocks over 30 years: **6.88 % of closes sit on a strike on expiration Friday against 6.53 % on all other Fridays** of the same names. The gap of 0.35 percentage points survives a permutation test at p = 0.0050.

The sub-periods contradict the expectation. Weekly options have existed since 2010, so monthly expiry should have lost weight. Measured, the effect is three times larger since then: +0.45 percentage points against +0.15, and before 2010 it was not measurable at all (p = 0.27).

For all the significance: 0.35 percentage points on a base of 6.53 % shift probabilities marginally and cover no fees. → [Expiration pinning, 30 years measured](/en/blog/options-expiration-pinning/)

### Is September statistically unusual for the DAX?

Yes, and as the only month. Avg **−1.55 %** — the weakest of all twelve months, with the next weakest (June) at −0.27 %. The test runs against zero, and it yields **p = 0.0241**.

That is a real effect and a small one. Significant and large are two separate properties, and September invites confusing them: a p-value says how unlikely a difference of that size would be under pure chance. About the size itself it says nothing. → [The DAX September significance test](/en/blog/dax-september-significance/)

### How accurate is the expected move from option prices?

It is too wide, and reliably so.

From the price of an at-the-money option you can calculate how far a market should travel by expiry: implied volatility times the square root of the remaining term. The result is called the one-sigma band, and assuming normally distributed returns the price should stay inside it in **68.3 %** of cases. That figure appears on every options platform.

Measured over 1990 to 2026, using the VIX as the volatility measure against the S&P 500, the price stayed inside the band in **84.3 %** of cases. The confidence interval runs from 82.2 to 86.3 percent and excludes 68.3 by a wide margin. Because rolling 30-day windows overlap and thereby overstate the number of independent observations, we also computed it on non-overlapping windows: 83.4 %. So the result does not hang on the overlap.

One qualification belongs with it: the VIX is not at-the-money volatility. It is built across the whole strip of out-of-the-money options and sits above ATM by construction. That offset makes the band somewhat wider still, but it does not account for the entire gap — the daily changes in the two measures move together with a correlation of 0.857.

The gap has a name and a recipient: it is the volatility risk premium. Options are on average more expensive than the movement that actually follows, because somebody wants paying for the risk of carrying the whole move if it comes. That is why selling options is a business model — and why, in the rare cases when the band does not hold, it becomes very expensive. → [Vol regime radar with expected move per name](/en/skew)

## What holds only under a condition

### Do bonds announce a rise in equities?

Under stress yes, otherwise no. After a rise of at least 4.06 % in long-dated US Treasuries over ten trading days, the S&P 500 gained **+2.09 %** over the following two weeks against +0.48 % on average. 50 cases since 2002, p between 0.001 and 0.005, hit rate 74 % against 65.7 %.

The condition decides everything. In calm markets the same effect sits at **exactly the base rate** — p = 0.935, i.e. nothing. In turbulent ones at +3.65 %. Quote the rule without that addition and you are quoting something other than what was measured.

A second qualifier is easily lost: this is a **recovery pattern**, not a forecast out of a clear sky. The S&P 500 had fallen by a median 1.31 % before the event, and stood in the red in 62 % of cases. Without that half you read a forecast where a recovery stands. → [The bond study in detail](/en/blog/bonds-as-a-stock-market-indicator/)

### Does bitcoin lead the stock market?

Only above very large moves, and weakly then. The common version of this rule names a threshold of five percent. That is exactly where it fails: for bitcoin, five percent is the **median** of all ten-day moves, i.e. the most ordinary move there is. A rule that fires on half of all days forecasts nothing.

It becomes measurable from ten percent and dependable from twenty: the S&P 500 then adds 2.29 % over three weeks at p = 0.027.

The figure that settles the case is a different one. At zero lag the correlation between crypto and equities runs +0.36 to +0.45 — pronounced. Shifted by one day it is gone. That is not a weak forecast, it is no forecast at all: the two markets move **at the same time**, because both hang on the same risk appetite. A contemporaneous correlation can be observed, but not traded. → [Twelve years of crypto against equities](/en/blog/does-bitcoin-lead-the-stock-market/)

## What does not hold

### Are September and October really the crash months?

No. Volatility in those two months runs at **1.059×** the rest of the year, and that cannot be told apart from chance: **p = 0.127** across 836 months from 1957.

What is measured is the annualised dispersion of the daily returns belonging to each month, with the median taken across years — so no single crisis year sets the picture. Volatility rather than return, because it is the more dependable quantity: returns are barely predictable, volatility hangs strongly on its own past.

The p-value comes from a comparison distribution. The calendar is shifted against the price series, and we measure how often an arbitrary pair of months sits as far above the rest as September and October do by chance alone. 1,832 such draws, and the measured value lands in the middle of the field: the median of the random draws is 1.004 and the 95th percentile 1.084 — and 1.059 sits below it. Shifts by multiples of twelve months are excluded, because they bring the calendar back into alignment and would therefore scramble nothing at all.

One detail contributes here, and it is not a technicality: the computation runs on the index itself, not on an ETF. The ETF's dividend adjustment puts artificial jumps into the return series in exactly four calendar months, and two of them are the ones under test. Test the rule on SPY and you are partly measuring distribution dates — a first attempt of ours did exactly that and came out with a different sign.

What remains is a memory effect. October 1929, October 1987, October 2008: individual months shape the picture, they do not shape the average level. That is precisely why the calculation uses the median rather than the mean. → [Monthly volatility profile for over 300 tickers](/en/vola-saisonalitaet)

### Does one market announce the move of another?

Not by this measurement. The idea is appealing: when one market has moved unusually hard, something should happen afterwards in a related market. The word that matters is **afterwards** — a contemporaneous correlation is not a forecast.

We built a pre-specified test family from it. 18 markets across equities, sectors, commodities, bonds and crypto; an event is a ten-day move in the top tenth of that market's own history; what is measured is the target market's return over the following ten trading days. A cell counts only if it has at least 20 events **in each half** of the period and points the same way in both halves. That yields 556 usable cells, 470 of them in the primary family.

**None holds.** Not one survives the correction for how many questions were asked.

Two decisions in that setup matter more than the result. First, only pairs that cross a category boundary count: the Dow following the S&P is not an intermarket hypothesis, it is the same market under another name. The separation runs on category, not on measured correlation — otherwise the choice of test family would already be a search for the result. Second, both rules were fixed before we saw any outcome. The strongest cell in the whole field — silver down, utilities afterwards, t = 4.09 — clears the bar and fails on the event count per half. Without that requirement a hit would be standing there now.

The correction is the point. Across 470 tests some 24 chance hits are to be expected even when nothing whatsoever is going on. Pick them out one at a time and display them, and you are displaying noise with a p-value beside it. That is how most of the intermarket rules one reads come about.

What remains is a signal below the threshold, and it is the most coherent thing in the field: a rise in long-dated bonds points the same way against **six** equity targets at once — S&P, Nasdaq, technology, financials, Dow, utilities — each with 52 events, all aligned across both halves, all below the bar. A chance hit does not distribute itself that systematically across related targets. That is not a finding; it is the reason bonds got a study of their own further up. → [The matrix with all 470 pairings](/en/intermarket)

### Does the monthly-10 strategy beat buy and hold?

No. The rule: be invested on only ten selected trading days a month — the first four, days nine to twelve and the last two. Computed over 32 years it delivers **5.58 % a year against 10.71 %** for buy and hold, and led in 10 of 32 years.

It does cut volatility, from 18.84 to 10.79 percent, and the largest loss from −55.2 to −41.0 percent. Per unit of risk it stands at 0.52 against 0.57, narrowly behind. Anyone who wants less volatility gets it — but pays more than half the return for it.

The most revealing part is **where** the return comes from: the middle of the month, not the turn of the month the rule invokes. So the reasoning fails even if you let the result stand. → [Monthly 10 over 32 years](/en/blog/monthly-10-strategy/)

## What is a pattern but not a test

Three analyses show a pattern the sample cannot carry. They appear here without a p-value, because a p-value at this point promises more than it can deliver.

### What is the pre-FOMC drift?

The day before a Fed decision returns +0.131 % on average and the decision day itself +0.202 % — against +0.040 % on all other days. Those days account for roughly 22 % of the summed daily return while making up 6.6 % of all trading days. → [Pre-FOMC drift](/en/blog/pre-fomc-drift/)

### What happens to a stock when it joins the S&P 500?

Twenty trading days after the announcement the price stands +5.8 % higher, with a peak of +7.8 % around the effective date; 72 % of cases are positive. At 36 events that is an averaged path, not a test.

### Is the midterm year different from the other three?

The second year of a US term carries the deepest drawdown of the four, and that low is on average followed by a recovery of +31 %. Roughly twenty cycles since 1950 are too few observations for more than a description. → [Midterm year 2026](/en/blog/midterm-election-year-2026-recovery/)

## Why fixing the question in advance makes the difference

For the volatility seasonality study, *one* ticker and *one* pair of months were fixed before anything was computed. That sounds like a formality and is the whole difference.

Had the choice been free, twelve months times several hundred names would have been available. With that many combinations a striking result is guaranteed — not likely, guaranteed. You find it, present it with a p-value, and the p-value is then a statement about the search rather than about the market.

The same thing writ large is the intermarket matrix: 470 questions, some 24 expected chance hits, zero dependable ones. Show only the 24 and you have not measured anything, you have selected.

## What is not here

One analysis is deliberately absent. The trading returns of members of the US Congress have been computed, but so far rest on too few events from too few people. Any statement about "the politicians" would be a statement about two of them. The rule was fixed before the computation: at least 100 events from at least five people, otherwise no verdict. That threshold is not currently met; the ongoing filings collect under [Congress Trades](/congress).

## What these figures are not

Not investment advice and not a forecast. Three things belong with the reading:

A **significant effect can be tiny**. The 0.35 percentage points of the pinning study survive no fees.

A **conditional effect disappears without its condition**. The bond effect holds in turbulent periods; in calm ones it sits exactly on the base rate.

And **past patterns guarantee no future results** — least of all when many market participants rely on the same pattern.

## Frequently asked questions

### Why include the rules that do not work?

Because they cost the same work and carry the same value. The five-percent rule for bitcoin only comes apart when someone works out that five percent is the median of all ten-day moves there. Taking a rule out of circulation is a result.

### What does "fixed in advance" mean?

That the ticker, the period, the threshold and the measure were set before anything was computed. Compute first and then pick the variant that looks best, and you always find something. The number of variants tested therefore belongs with every result — it determines how a p-value is to be read.

### Are the supported effects tradable?

That is a different question from the one answered here, and the answer is often sobering. An effect has to survive fees, spread and tax, and it has to be large enough not to vanish in the scatter of individual years. For pinning it is not. For the expected move it is — which is why selling options is a business model rather than a secret.

### Why distinguish "not supported" from "descriptive"?

Because they are two different statements. "Not supported" means it was computed and the difference cannot be told apart from chance. "Descriptive" means the pattern is visible but the sample carries no test. In the first case the measurement argues against the rule; in the second it suffices for no verdict at all.

### Is anything being added?

Irregularly. An analysis comes about when a question is concrete enough to be put in a falsifiable form and the data base can carry it. The two together occur less often than the volume of market rules in circulation would suggest.

<!--
#### Social Media Snippet

**LinkedIn:**
We recomputed eleven well-known market rules on our own price data, each with a question fixed in advance.
Four do not hold:
— September and October are NOT the volatile months. 1.059× the rest of the year, p = 0.127 across 836 months from 1957.
— "Bitcoin leads" fails on its own threshold: the much-quoted 5 % is the MEDIAN of all ten-day moves in bitcoin.
— Monthly 10 delivers 5.58 % p.a. against 10.71 % for buy and hold — and the return comes from the middle of the month, not the turn of the month the rule invokes.
— Of 470 pre-specified intermarket pairings, not one holds.
The last point is the instructive one: across 470 tests some 24 chance hits are expected even when nothing is going on. Show only those 24 and you have not measured, you have selected.
Not investment advice. → seasonalpha.ai

**Twitter/X:**
Eleven market rules recomputed. Four do not hold:
· September/October more volatile? 1.059×, p = 0.127. No.
· Bitcoin leads? The quoted 5 % is the MEDIAN of all 10-day moves.
· Monthly 10: 5.58 % vs 10.71 % p.a.
· Intermarket: 0 of 470 pairings.
Not investment advice.
#Markets #Statistics #SeasonAlpha
-->

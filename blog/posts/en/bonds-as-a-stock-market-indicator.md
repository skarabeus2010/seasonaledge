---
title: "Do Bonds Lead the Stock Market? Only Under Stress — 50 Cases Since 2002"
seo_title: "Do Bonds Lead Stocks? Only Under Stress, 50 Cases"
slug: bonds-as-a-stock-market-indicator
de_slug: anleihen-fruehindikator-aktienmarkt
date: 2026-09-22
category: education
tags: [bonds, tlt, spy, lead-lag, volatility, intermarket]
description: "A flight into long-dated Treasuries and what the S&P 500 does next: 50 cases since 2002 give +2.09 % in two weeks, but only in volatile markets."
ticker: TLT
status: published
---

<!--
Keyword-Plan:
- Main keyword: do bonds lead the stock market
- Secondary: bonds leading indicator stocks, TLT SPY relationship, Treasuries and equities, flight to quality signal, bond equity lead-lag, long-dated Treasuries signal, realised volatility regime, S&P 500 event study
- LSI: base rate, hit rate, p-value, random shift, max-T, duration, de-risking, recovery, stress regime
-->

## The idea behind the claim

The bond market is widely treated as the older and cooler-headed of the two. When capital moves into long-dated Treasuries, the reading goes, bond investors are pricing a slowdown that equities only understand later. From there it is a short step to the claim that bonds lead the stock market.

The claim is testable, because it asserts a sequence. We measured it across 6,075 common trading days. There is a finding, and it is considerably narrower than the claim requires.

## What was measured

The data are daily closes of TLT (ETF holding US Treasuries with more than 20 years to maturity) and SPY (ETF on the S&P 500), from 30 July 2002 to 21 September 2026.

The signal is a **TLT price gain of at least 4.1 % over 10 trading days**. The threshold comes out of the distribution itself: 4.1 % is the 90th percentile of all TLT moves of that length, the strongest ten percent. Over 24 years that produces **50 events**, each at least 41 trading days apart so that a single market phase is not counted repeatedly.

What gets measured is SPY **after** the signal, against what the market does over the same horizons with no signal at all. That base rate is +0.24 % after one week, +0.48 % after two, +0.72 % after three and +0.95 % after four weeks.

The methodological scaffolding (base rate, random shifts, p-value) is set out in the [first part of this series on Bitcoin](/en/blog/does-bitcoin-lead-the-stock-market/). The code sits in `scripts/research/bond_lead_lag.py` and `bond_kontrollen.py`.

## The raw finding

| SPY after the signal | Result | p | Base rate, no signal |
|---|---:|---:|---:|
| 1 week | **+1.80 %** | 0.001 | +0.24 % |
| 2 weeks | **+2.09 %** | 0.001 | +0.48 % |
| 3 weeks | **+2.12 %** | 0.005 | +0.72 % |
| 4 weeks | **+2.85 %** | 0.001 | +0.95 % |

Across all four horizons the result runs at two to seven times the base rate, and the p-values stay below 0.01 throughout. The hit rate rises from 65.7 % to **74.0 %**, so it moves with the average. That did not happen in the Bitcoin part of this series: there the extra return came from a few large cases while the hit rate stayed at market level.

This is the point where the headline the claim invites would have been written. The control calculations say something else.

## The condition that changes everything: the market regime

![Two bar charts: on the left the S&P 500 two weeks after a strong rise in long-dated Treasuries, split into calm phases (+0.53 %, p = 0.935, n = 25) and volatile phases (+3.65 %, p below 0.001, n = 25), with the dashed market-average line at +0.48 %; on the right the same measurement for 2003-2019 (+1.72 %) and 2020-2025 (+2.87 %)](anleihen-fruehindikator-aktienmarkt/1_regime.png)

The 50 events were split at the median realised volatility of the S&P 500 on the event day, that is, by how much the equity market was already moving at the time. The median sits at 13.9 % annualised.

In the **25 calm cases** SPY stands at **+0.53 %** two weeks later, at p = 0.935. The base rate is +0.48 %. In calm markets the signal adds nothing.

In the **25 volatile cases** the figure is **+3.65 %** at p < 0.001, with a hit rate of 80 %. The entire finding sits in that half of the sample.

The average across all 50 cases (+2.09 %) is therefore a blend of a strong state and an empty one. Quoted without the split, it describes a number that occurs in neither market condition.

## Why these controls are necessary

Large bond moves cluster in volatile phases, and in volatile phases equity returns are distributed differently: the swings are wider, and rebounds after sharp drawdowns are correspondingly stronger. A signal that fires mainly in those conditions inherits that property without carrying any information of its own.

The second control concerns SPY **before** the event. If equities had already been rising, the apparent lead could simply be momentum. Split by the preceding SPY move:

| Subset (2 weeks, base rate +0.48 %) | n | SPY afterwards | p | Hit rate |
|---|---:|---:|---:|---:|
| all events | 50 | +2.09 % | < 0.001 | 74 % |
| weak prior SPY move | 25 | **+2.68 %** | 0.004 | 76 % |
| strong prior SPY move | 25 | +1.50 % | 0.099 | 72 % |
| calm phases | 25 | +0.53 % | 0.935 | 68 % |
| volatile phases | 25 | **+3.65 %** | < 0.001 | 80 % |

That rules out the momentum reading, with the opposite sign to what one would expect: the effect is larger after a **weak** prior move (+2.68 %, p = 0.004) and no longer significant after a strong one (+1.50 %, p = 0.099).

## What happens before the signal

![Event path of the S&P 500 from ten trading days before to 30 trading days after a TLT price gain of 4.1 percent or more, normalised to the event day, n = 50: the gold average line falls from around plus 2 percent to zero before the event and rises to roughly plus 2.6 percent afterwards, above the blue random band spanning the 5th to 95th percentile](anleihen-fruehindikator-aktienmarkt/2_pfad.png)

The chart shows the average SPY path from ten trading days before to 30 trading days after the event, normalised to the event day. The blue band is the 5th-to-95th percentile corridor from randomly shifted dates: the range any arbitrary window lands in.

The left half of the picture carries the argument. In the ten trading days before the signal, the S&P 500 fell by a median of **1.33 %** (mean −1.75 %, negative in 62 % of cases). The flight into long-dated Treasuries sets in at the end of a drawdown, not in a quiet equity market.

That changes how the finding has to be described. What was measured is a recovery pattern after losses in a nervous market, not a signal that announces an advance out of nowhere. To the right of the event day the average line leaves the random band upwards and stays there, so the rebound is larger than randomly chosen windows deliver.

## The opposite direction shows nothing

When TLT falls, long yields rise. If the bond market were a general leading indicator, something should appear in that direction too, with the sign reversed.

Nothing appears. Across every threshold tested and all four horizons, the p-values run between **0.29 and 0.97**. Not one comes close to a significance threshold.

The asymmetry fits the stress reading: a sharp rally in long-dated bonds is typically de-risking under pressure, while a decline is usually an orderly repricing of rates.

## Both sub-periods, and the price of searching

The sample was split in advance at the obvious break: 2003-2019 against 2020-2025. Not where the result looks best.

Before 2020, SPY stands at **+1.72 %** two weeks after the signal (n = 34, p = 0.019, hit rate 65 %); from 2020 onwards at **+2.87 %** (n = 16, p = 0.008, hit rate 94 %). The finding exists in both halves. The second half is thin at 16 cases, and a 94 % hit rate on that sample size should not be read as a figure in its own right.

That leaves the cost of testing many variants. Four thresholds, two directions, two signal sources and four horizons add up to **64 combinations**. The smallest individual p-value from a family that size says little, because 64 attempts throw up hits by chance alone. The max-T test asks instead how often the *best* chance result from an equally large family reaches the observed level. The answer: **p = 0.018**. That is the strictest number in the whole study, and it holds.

## Limits

**TLT is a price, not a yield.** The link to bond yields is inverse and tight, but the ETF price also carries duration effects and the rebalancing of the underlying index. Hence "TLT price gain" throughout. Long yields did tend to fall in these phases, but what was measured is the price.

**Sequence is not causation.** Both markets respond to the same macro impulses. The study measures the order of events; the cause stays open.

**The signal is rare.** Fifty cases in 24 years is about two a year, and half of them fall into calm phases where nothing follows.

**In calm markets the effect is zero.** +0.53 % at p = 0.935 against a base rate of +0.48 % is not a weak result; it is the base rate. Read without regard to the market regime, the signal is noise.

**The threshold comes from the data, not from a round number.** The calculation uses the exact 90th percentile of the TLT move distribution (0.040632); the text quotes the rounded 4.1 %.

**Ex-dividend days.** The price series carry a small artificial mark-down on ex-dates. Over four-week windows that is roughly one day and biases the figures slightly downwards.

## What follows from this

The claim does not hold in its general form. A strong rally in long-dated Treasuries does not announce an equity move. It describes a state: de-risking under pressure, after a drawdown, in a nervous market. In that specific constellation the S&P 500's recovery was historically above average. In any other it was not.

Set against the [Bitcoin part of this series](/en/blog/does-bitcoin-lead-the-stock-market/), this is the stronger result. There, only very large crypto moves of 20 % or more left anything behind, the popular 5 percent rule failed, and the hit rate never moved. Here it moves, the effect holds in both sub-periods and it survives the max-T correction. The price is the condition attached to it: without the stress regime, nothing remains.

Adjacent questions can be checked directly on SeasonAlpha: [Intermarket Shocks](/en/intermarket-shocks) covers transmission between markets, and the [Risk Cycle](/en/risikozyklus) shows risk appetite across the calendar year.

**Not a signal:** what stands here is a measurement on historical prices, not a trading rule and not a statement about future prices.

## Frequently asked questions

### Do bonds lead the stock market?

Not in the general form, on this data. A TLT price gain of 4.1 % or more over 10 trading days does coincide with an above-average S&P 500 recovery (+2.09 % over two weeks against a +0.48 % base rate), but the entire effect sits in volatile market phases. In calm phases the result is +0.53 % at p = 0.935, which is practically the base rate.

### What does "only under stress" mean in practice?

The 50 events were split at the median realised volatility of the S&P 500 on the event day, which is 13.9 % annualised. Above it, SPY reaches +3.65 % two weeks later (p < 0.001, hit rate 80 %); below it, +0.53 % (p = 0.935).

### Does the relationship also work in reverse, when bonds fall?

No. With TLT falling, meaning long yields rising, the p-values run between 0.29 and 0.97 across every threshold and horizon. There is no measurable pattern in that direction.

### Why is this a recovery rather than a forecast?

Because the S&P 500 had already fallen before the signal: by a median of 1.33 % over the preceding ten trading days (mean −1.75 %, negative in 62 % of cases). The signal marks the end of a drawdown, not the start of a move out of calm conditions.

### How often does the signal occur?

Fifty times in 24 years, roughly twice a year. Events are kept at least 41 trading days apart so that a single market phase does not enter the calculation more than once.

<!--
#### Social Media Snippet

**LinkedIn:**
"Bonds lead equities" — we tested the claim on 6,075 common trading days since 2002 (TLT against SPY).
Raw result: after a TLT price gain of 4.1 % or more over 10 trading days, the S&P 500 stands at +2.09 % two weeks later instead of the usual +0.48 %. 50 cases, p = 0.001.
The controls narrow it down: calm phases +0.53 % at p = 0.935, volatile phases +3.65 % at p < 0.001. And the S&P 500 had already fallen by a median of 1.33 % before the signal. It is a recovery pattern under stress, not a forecast.
The opposite direction shows nothing at all: p between 0.29 and 0.97.
Which intermarket rule should we test next? → seasonalpha.ai

**Twitter/X:**
Do bonds lead stocks? 6,075 trading days since 2002:
TLT +4.1 % in 10 days → SPY +2.09 % two weeks later (base rate +0.48 %).
But: calm phases +0.53 % (p=0.935), volatile phases +3.65 % (p<0.001).
And SPY had already fallen. Recovery, not forecast.
#Bonds #Markets #SeasonAlpha

#### Interne Verlinkung
- /en/blog/does-bitcoin-lead-the-stock-market/ (part 1, methodology)
- /en/intermarket-shocks (transmission between markets)
- /en/risikozyklus (risk appetite across the year)

#### Content-Ideen (Folgeartikel)
- "The VIX as a filter: the same measurement with a different stress gauge"
- "Gold, copper, bonds: which market actually turns first?"
- "What the 2022 rate shock did to the TLT signal"
-->

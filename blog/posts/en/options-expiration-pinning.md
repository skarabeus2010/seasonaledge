---
title: "Pinning on Expiration Day: +0.35 Percentage Points Over 30 Years — and Growing"
seo_title: "Options Expiration Pinning: 30 Years, 158 US Stocks"
slug: options-expiration-pinning
de_slug: pinning-verfallstag
date: 2026-09-22
category: education
tags: [options, expiration, opex, pinning, delta-hedging, statistics]
description: "Do stocks close near a strike more often on expiration Friday? 158 names, 30 years, 41,203 observations: 6.88 % versus 6.53 %, p = 0.0050."
ticker: SPY
status: published
---

<!--
Keyword-Plan:
- Main keyword: options expiration pinning
- Secondary: stock pinning strike, opex effect stocks, delta hedging price effect, third Friday options expiration, open interest strike level, expiration day statistics, option writers hedging
- LSI: control group, bootstrap, confidence interval, p-value, sub-period, weekly options, closing price, strike grid
-->

## The question

On the third Friday of each month, standard US equity options expire. Options desks have long observed that stock prices close unusually close to an option strike on that day. The phenomenon is called pinning.

We measured it across 158 optionable US stocks over 30 years: **6.88 % of closing prices sit on a strike on expiration Friday, against 6.53 % on every other Friday** for the same names. The difference is +0.35 percentage points at p = 0.0050.

## Why a price can stick to a strike

Whoever sold an option usually hedges the position in the underlying stock. Short calls are neutralised with long stock, short puts with short stock. The option's delta says how many shares that takes.

Close to expiry, that delta changes very fast near the strike. An option slightly in the money needs almost the full share amount as a hedge; one slightly out of the money needs almost none. When the price rises above the strike, writers have to buy; when it falls back below, they sell again.

Each adjustment works against the move that triggered it. With large open interest sitting at one strike, hedging can hold the price in its neighbourhood. This mechanism is the standard explanation for pinning; it is set out in full, together with the call wall and the put wall, in [Pinning explained](/en/blog/pinning-call-wall-put-wall/). The corresponding market structure is tracked on [Key Levels](/key-levels), where the largest open-interest clusters per name are listed.

## The strike grid is unknown — the control group handles it

A clean measurement would require knowing, for every day in the past, at which price levels options were actually listed. Those grids changed several times over the decades, and they differ by name, by price level and by maturity. Complete historical coverage is not available.

Any assumption about them is therefore wrong. The way around it is not a better grid but the comparison group: the same assumption is applied to expiration Fridays **and** to every other Friday of the same stocks over the same period.

If the assumed grid is too coarse, too fine, or placed at the wrong levels, that error hits both groups. The absolute rate therefore loses its meaning — ours sits at roughly a third of what studies with real strikes report. A hit is a closing price within 0.125 $ of an assumed strike.

That the **difference** is equally untouched does not follow automatically, and that belongs on the record: whether a close counts as a hit depends on where it sits relative to the assumed grid. If expiration days really do close nearer to real strikes, a wrong grid can sort them differently from control Fridays. Part of the measured difference could therefore come from the grid assumption — or be masked by it. Only the real historical strikes would settle that.

Only Fridays are compared with Fridays, so the known day-of-week effect does not leak into the calculation. The data are daily closing prices: 41,203 observations on expiration Fridays against 135,738 control observations, spread over 369 calendar months from 1996 to 2026.

## The numbers, overall and in two sub-periods

![Three pairs of bars comparing the share of closing prices on a strike on expiration Fridays versus other Fridays: full period 1996-2026 (6.88 % versus 6.53 %, p = 0.0050), the years up to 2009 (8.43 % versus 8.28 %, p = 0.2744) and from 2010 onwards (6.06 % versus 5.61 %, p = 0.0015)](pinning-verfallstag/1_perioden.png)

| Period | Expiration Fridays | Other Fridays | Difference | p |
|---|---:|---:|---:|---:|
| 1996–2026 | **6.88 %** | 6.53 % | +0.35 pp | 0.0050 |
| up to 2009 | 8.43 % | 8.28 % | +0.15 pp | 0.2744 |
| from 2010 | **6.06 %** | 5.61 % | +0.45 pp | 0.0015 |

Across the full period the 95 % interval for the difference runs from **+0.09 to +0.62 percentage points**. It excludes zero, while covering a range from almost nothing to nearly double the point estimate.

[The p-value](/en/blog/p-value-explained/#bootstrap-or-permutation) answers one specific question: how often would a difference of this size come up if expiration Friday were not a special Friday at all? To answer it, one Friday in each month is drawn at random and treated as if it were the expiry. That leaves untouched everything that must stay untouched — the monthly structure, the number of expiry days, the composition of names, the price level of the era — and shuffles only the one thing at issue. Across 2,000 such runs the drawn variant reached the measured +0.35 percentage points in 0.5 percent of cases.

One hypothesis was tested, fixed in advance and directional: the share is higher on expiration Friday. No set of thresholds, definitions or time windows was tried out with the best result picked afterwards.

## Weekly options did not dilute the monthly expiry

Weekly-expiring options have been broadly available since 2010. The obvious expectation: open interest spreads across many dates, the monthly expiration loses its special role, the effect shrinks.

The measurement points the other way. Before 2010 the difference is +0.15 percentage points at p = 0.2744, which these data cannot distinguish from zero. From 2010 onwards it is +0.45 percentage points at p = 0.0015. The effect is three times as large in the more recent half, and only there does it carry statistical weight.

The 2010 split was fixed before the calculation, not placed afterwards where the gap looks widest. These data carry no explanation with them. One possibility is that the monthly expiry has gained weight because total options volume has grown sharply since 2010, while the third Friday remains the date with the largest open position.

## Why the levels must not be compared

The absolute rates of the two sub-periods are far apart, 8.43 % against 6.06 %. Nothing follows from that. The prices of the stocks covered here rose substantially over three decades, so the fixed 0.125 $ tolerance became ever tighter relative to the price. The declining rate mostly reflects higher price levels.

The same caveat applies to the academic comparison. The best-known study on the subject, Ni, Pearson and Poteshman, reports roughly **19.2 % versus 18.0 %**. Our levels are about a third of that, because the grid used there is the real one and sits finer than the one assumed here. What is comparable is the difference; the absolute level depends on the grid. Both measurements find an excess on expiration day of a similar order: a good percentage point there, a third of a percentage point here on a correspondingly lower base.

## For a single stock, the effect sits inside the noise

![Distribution of the pinning difference across the 158 stocks studied: histogram of the per-ticker difference between the share on a strike on expiration Fridays and on other Fridays, unimodal and slightly to the right of zero, median +0.28 percentage points, 86 of 158 names positive, with no dominant outlier](pinning-verfallstag/2_je_ticker.png)

An average across 158 names could also arise if a few stocks showed a large swing and the rest showed nothing. There is no such outlier: the distribution of the individual differences is unimodal and sits slightly to the right of zero, with a median of **+0.28 percentage points**. 86 of the 158 names are positive, which at 54 percent is barely more than a coin flip.

The reason lies in the number of cases per stock. Depending on its history, a single name contributes only 24 to 70 expiration days. Against the scatter that so few observations produce, 0.35 percentage points cannot be seen.

The effect only becomes visible across 158 names and 369 months taken together. That is why a measurement like this is pooled. On any one stock the pattern cannot be verified.

## Limits

**The effect is small.** +0.35 percentage points on a base of 6.53 % is a relative increase of about five percent. It is not a trading signal and carries no strategy.

**The dependence structure is accounted for, not removed.** 158 stocks on the same Friday are not 158 independent observations; the broad market moves them together. The calculation therefore works over whole months rather than individual ticker-days, which keeps the structure within a month intact.

**These are daily closing prices.** What happens intraday — whether the price drifts towards the strike during the session or only in the closing auction — cannot be measured from these data.

**Open interest is not part of the calculation.** What is measured is proximity to an assumed strike, regardless of how many contracts were actually open there. Theory says the effect should grow with open interest at that exact strike. This measurement does not test that.

**An association is not proof of a cause.** That prices close on a strike somewhat more often on expiration day does not establish that delta hedging produced it.

## What follows from it

The trading-floor observation survives a test across 30 years, at a magnitude far below what the word pinning suggests. A price that "sticks to the strike" on the third Friday remains an exception.

The effect matters in practice where a position happens to expire near a large strike. Current levels are on [Key Levels](/key-levels), the full expiration calendar is on [OPEX](/opex), and how the volatility structure behaves around these dates is shown by the [vol regime radar](/skew).

**Not a signal:** what you read here is a measurement on historical prices, not a trading rule and not a statement about future prices.

Pinning is one of eleven market rules we recomputed on our own price data. Four of them do not hold — the full set is at [eleven market rules, measured](/en/blog/market-rules-tested/).

## Frequently asked questions

### What does pinning on expiration day mean?

Pinning describes the observation that stock prices close very close to an option strike more often on options expiration day than on other days. The usual explanation is delta hedging by option writers: near expiry, their hedging trades work against moves away from the strike.

### How large is the measurable effect?

Across 158 US stocks and 30 years, 6.88 % of closing prices on expiration Fridays fall within 0.125 $ of an assumed strike, against 6.53 % on all other Fridays. The difference of +0.35 percentage points has a p of 0.0050, with a 95 % interval from +0.09 to +0.62 percentage points.

### Why are these rates so far below the 19 % found in research?

Because the strike grid assumed here is coarser than the real one available to the study by Ni, Pearson and Poteshman. A coarser grid produces fewer hits in both groups. What is comparable is therefore the difference between expiration days and control days, not the absolute level.

### Have weekly options replaced the monthly expiry?

Not for this effect. Up to 2009 the difference is +0.15 percentage points at p = 0.2744; from 2010 it is +0.45 percentage points at p = 0.0015. The excess on the third Friday has grown during the era of weekly options.

### Can the effect be seen on a single stock?

No. Each name provides only 24 to 70 expiration days, and 0.35 percentage points disappear into the scatter of so few observations. The median of the individual differences is +0.28 percentage points, with 86 of the 158 names positive. The effect only becomes measurable across all names and 369 months together.

### Can a trading strategy be built on this?

No. Lifting a 6.53 % base by 0.35 percentage points shifts probabilities marginally and covers no transaction costs. The value of the measurement lies in understanding the market mechanics around expiration day.

<!--
#### Social Media Snippet

**LinkedIn:**
"On expiration day the price sticks to the strike" — we tested that trading-floor rule across 158 US stocks and 30 years.
Result: 6.88 % of closing prices sit on a strike on expiration Friday, against 6.53 % on all other Fridays for the same names. +0.35 percentage points, p = 0.0050, 41,203 versus 135,738 observations.
The sub-periods contradict the obvious expectation: weekly options arrived in 2010, so the monthly expiry should have lost weight. Measured, it is three times as large from 2010 (+0.45 pp, p = 0.0015) as before (+0.15 pp, p = 0.2744).
On method: historical strike grids are not available. Solved via the control group — apply the same wrong assumption to both groups, and the difference stays meaningful.
The effect is small and not a trading signal. → seasonalpha.ai

**Twitter/X:**
Options expiration pinning, 158 US stocks, 30 years:
6.88 % of closes on a strike on expiration Fridays vs 6.53 % on other Fridays. +0.35 pp, p = 0.0050.
And: from 2010 (weekly options era) the effect is three times as large.
Small. Not a trading signal.
#Options #Markets #SeasonAlpha

#### Interne Verlinkung
- /key-levels (open interest walls and max pain per name)
- /opex (expiration calendar, third Friday, triple witching)
- /skew (vol regime radar, volatility structure around expiries)
- /dealer-positioning (gamma, vanna and charm profiles)

#### Content-Ideen (Folgeartikel)
- "Pinning by open interest: does the effect grow at heavily loaded strikes?" — same measurement with chain data instead of an assumed grid
- "The week after expiration" — return distribution in the five trading days after OPEX
- "Triple witching versus ordinary expiry" — the four quarterly dates measured separately
-->

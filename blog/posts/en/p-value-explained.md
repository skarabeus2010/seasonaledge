---
title: "Is the effect real? P-values on six of our own studies"
seo_title: "Significant but worthless: how to read a p-value"
slug: p-value-explained
de_slug: p-wert-erklaert
date: 2026-09-22
category: education
tags: [statistics, significance, backtest, methodology, p-value, seasonality]
ticker: SPY
status: published
description: "p = 0.127 is not \"no effect\", p = 0.0050 is not \"tradable\". P-values explained on published studies, plus multiple testing and one error of our own."
---

<!--
Keyword plan:
- Head keyword: statistical significance in backtesting
- Secondary: what a p-value means for a trading strategy, significant but not tradable,
  multiple testing bias market studies, permutation test vs bootstrap trading,
  how many trades statistically significant
- LSI: null hypothesis, null distribution, control group, sample size, overfitting,
  data snooping, confidence interval, hit rate
- Positioning: NOT the head term "p-value explained" (owned by Investopedia,
  Scribbr, Statology; the traffic there writes term papers). The mechanics
  (t-value, ±1.96, Cohen's d) live in the DAX September post and are linked,
  not repeated.
- Stable anchors for deep links: #p-0-0050, #p-0-127, #p-0-935, #p-0-0241,
  #multiple-testing, #bootstrap-or-permutation
-->

## The sentence that explains the rest

**0.35 percentage points at p = 0.0050.** That is our best-evidenced single finding on options expiry — significant, measured across 41,203 observations and 30 years — and so small that little is left over for spread and fees.

Anyone who reads "significant" as "tradable" has not seen this case. And since a p-value appears on practically every study page on this site, it is worth spelling out once what is actually being claimed there — and what is not.

This article explains the p-value not on coin flips but on six of our own published measurements. Each carries a different lesson. One of them was a mistake of ours.

The arithmetic — null hypothesis, t-value, the ±1.96 threshold, Cohen's d — is set out at length in the [DAX September study](/en/blog/dax-september-significance/) and is not repeated here. This article is about what comes afterwards: how to read the result.

## What a p-value says, in one sentence

A p-value answers **one** question: *how often would a result of this size come about if the effect under investigation did not exist at all?*

To answer it you build a world without the effect — the null distribution — and check how often the measured value appears in that world. p = 0.0050 means: in half a percent of cases. p = 0.127 means: in roughly thirteen percent, so routinely.

## What it does not say

Three readings are common and all three are wrong.

**It is not the probability that the rule is true.** p = 0.0050 does not mean "pinning exists with 99.5 percent probability". The calculation runs the other way: it assumes the effect does *not* exist and asks how unusual the observation would then be. The probability of a hypothesis appears nowhere in it.

**It says nothing about size.** A p-value measures how clearly a difference can be separated from chance — not how large it is. Given enough observations, any difference however tiny becomes significant. That is not a flaw in the procedure, it is how it is built.

**0.05 is a convention, not a law of nature.** The threshold grew historically. There is no substantive difference between p = 0.049 and p = 0.051, and hanging a decision on that edge means hanging it on a rounding.

## Six measurements, six lessons

### Significant and still worthless {#p-0-0050}

US equity options expire on the third Friday of the month, and prices close conspicuously often near an option strike on that day. Measured across 158 stocks over 30 years: **6.88 % against 6.53 %** on ordinary Fridays of the same names. Difference 0.35 percentage points, **p = 0.0050**, with a 95 percent interval running from +0.09 to +0.62 percentage points that excludes zero.

A solid finding. And practically unusable.

0.35 percentage points on a base of 6.53 % shift the probability from about one hit in 15 cases to one hit in 14.5. What is measured is a difference in hit rates, not a return — what a strategy could make of it depends on a payoff structure this study did not examine. A shift of that magnitude does leave little room for spread and fees.

**The lesson:** significance and effect size are two separate questions, and only the second decides whether a number means anything in practice. A p-value answers exclusively the first. → [The full measurement](/en/blog/options-expiration-pinning/)

### "Not significant" does not mean "no effect" {#p-0-127}

Volatility in the S&P 500 during September and October runs at **1.059×** the rest of the year. Across 836 months from 1957, **p = 0.127**.

The obvious conclusion is wrong. p = 0.127 does not mean September and October are as calm as the rest of the year. It means: *this measurement cannot separate the difference from chance.* The measured value is 1.059, not 1.000 — it is simply not far enough from what occurs routinely in a world without a calendar effect. The median of the random draws is 1.004 and the 95th percentile 1.084. And 1.059 sits below it.

A non-significant result is therefore **not a statement about the world but about the resolution of the instrument.** With far more observations the same effect might become significant — there simply are no more, the S&P 500 does not have more than 836 months.

**The lesson:** "not supported" and "refuted" are different things. Turning a high p-value into "there is nothing there" claims more than the calculation delivers. → [Volatility seasonality](/en/vola-saisonalitaet)

### What a p-value of 0.935 tells you {#p-0-935}

A rise in long-dated US Treasuries announces an equity recovery in turbulent markets — +3.65 % over two weeks at p below 0.001. In calm periods, by contrast: **+0.53 % at p = 0.935**, from 25 cases.

A p-value near one is often read as a particularly strong counter-argument. It is something else: the result sits **so close to what you would expect with no effect at all** that 93.5 percent of all random draws fell further from it — the test here is two-sided, so what is measured is distance in either direction. The +0.53 % sits close to the base rate of +0.48 %, leaving nothing of the signal in this state that this measurement could still resolve.

A high p-value is **not evidence for the null**. It says the data are readily compatible with "no effect" — not that there is none. The American Statistical Association lists this as a principle of its own.

This is the most informative of the six values. It does not say "weak" but: **the measurement finds nothing here beyond the base rate.**

**The lesson:** an effect tied to a condition is no longer detectable without it. Quote the bond finding without the qualifier "under stress" and you are quoting a different measurement. → [The bond study](/en/blog/bonds-as-a-stock-market-indicator/)

### How much weight does p = 0.0241 carry? {#p-0-0241}

The DAX averages −1.55 % in September, the weakest of all twelve months; the next weakest, June, comes to −0.27 %. The test runs against zero — against the assumption that the true average September return is zero and any deviation is noise. It yields **p = 0.0241**. Significant by the usual convention — and a value close to the edge.

A thought experiment helps here: had the convention been set at 0.01 rather than 0.05, the same finding would read "not supported". Nothing about the data would have changed. That is why we always state effect size and the number of observations alongside the p-value: only together do the three carry an interpretation.

**The lesson:** a p-value is a graded quantity treated as a switch. Between 0.0241 and 0.0500 lies a difference of degree, not of kind. (It is not always continuous, either: our simulated values necessarily sit on a grid of 1/2001.)

### How many tests may you run? {#multiple-testing}

This is where it gets uncomfortable, because the point affects almost every market rule in circulation.

We did not ask the question "does market B move after market A has run unusually hard" once, but **470 times** — for every pre-specified combination among 18 markets. At a threshold of 0.05 some **24 hits** are to be expected under pure chance. Not because the markets are doing anything, but because 5 percent of 470 is 24.

Pick the most striking cells out of such a matrix and present them individually with a p-value, and you are presenting noise with a number beside it. That is exactly how intermarket rules come about.

The correction is called **max-T** and works differently from the familiar Bonferroni division. Instead of dividing the threshold by the number of tests, you rebuild the entire matrix a thousand times from random data and record only the **largest** value appearing anywhere in it. The question is then no longer "is this cell striking" but "does the best cell of a purely random matrix get this good". For our family the bar sits at a standardised effect of **|t| > 3.92**.

Result: **exactly one** of the 470 cells clears that bar — silver down, utilities afterwards, at t = 4.09 with a corrected p of 0.043. It fails on a different pre-specified condition: at least 20 events in **each** half of the period, and there it stands at 21 against 14. **No cell meets all the criteria** — which is not the same as "none clears the bar", and the difference is precisely why both conditions were fixed before anyone saw a result.

This magnitude is not a peculiarity of our calculation. Harvey, Liu and Zhu proposed in 2016 that a **newly claimed return factor** should have to clear a t-value of at least **3.0** rather than the customary 1.96, given the volume of published tests. Our 3.92 is not derived from that but is the output of our own calculation: the 95th percentile of the largest values across a thousand random matrices. That both numbers land in the same region is the actual finding. The work of Bailey and López de Prado on backtest overfitting shows the same mechanism from the other side and quantifies it as a probability: try enough variants and finding one with excellent statistics becomes almost certain.

**The lesson:** a p-value without a statement of how many questions were asked is not interpretable. That number belongs with the result just as the sample size does. → [The matrix with all 470 pairings](/en/intermarket)

### Bootstrap or permutation test? {#bootstrap-or-permutation}

This section describes a mistake we made and published.

The first version of the pinning study carried a p-value that was not one. What had been computed was a **bootstrap**: resample from the observed data with replacement, a thousand times over, and look at the spread of the estimate. Reported as the p-value was the share of draws whose difference fell below zero.

That is not a p-value, and the reason is structural. A bootstrap draws **with the observed labels** — every expiration day remains an expiration day. The resulting distribution is therefore centred on the *measured* difference, not on zero. The share below zero answers the question "how uncertain is my estimate", which is a perfectly sensible question. It does not answer "how often would this come about with no effect", because a world without the effect never appears in that calculation at all.

A **permutation test** builds exactly that world. It leaves standing everything that must stand — the monthly structure, the number of expiration days, the selection of names, the price level of the era — and scrambles only the one thing at issue: which Friday of the month is the expiration day. In each month one is drawn at random and treated as if it were. Only then is the null distribution a world without the effect.

After the switch, p = 0.0050 stood where the earlier number had been. The finding held; the justification had been wrong.

**The lesson:** a bootstrap measures the uncertainty of an estimate, a permutation test measures compatibility with nothing at all. Both return a number between zero and one, and only one of them is a p-value. The error was found by an external review, not by us.

## Three choices that decide the result

### The direction has to be fixed beforehand

A one-sided test demands less than a two-sided one: it asks only whether the effect goes in a particular direction, and therefore typically comes out smaller — roughly by half, given a symmetric null distribution and a result in the expected direction. It is legitimate only **if the direction was fixed before anyone looked at the result.**

For the volatility seasonality study it was: the common claim is that September and October are *more* volatile, so the test was one-sided upwards. Compute first, see the sign, and then choose the one-sided test, and you have halved your p-value illegitimately. In our crypto and bond studies exactly that was corrected after the fact: the direction had been chosen after seeing the result, although the question had been posed open-endedly ("does anything happen?"). After the switch to two-sided tests the p-values roughly doubled and the conclusion held.

### The plus-one correction

If a null distribution consists of 2,000 draws and none of them reaches the measured value, the p-value is not zero. By this convention it is **exactly 1/2001**. The smallest value such a simulation procedure can report is one divided by the number of draws plus one — a property of this calculation, not a statement about all tests:

```
p = (number of draws reaching the value + 1) / (number of draws + 1)
```

Without the plus one, a procedure will eventually report "p = 0.000", and that is a statement no simulation can make.

### The null distribution is a modelling choice

A p-value is only as good as the world-without-effect it is computed against — and you build that world yourself.

An example from the same study: volatility comes in blocks, a turbulent week consists of five turbulent days. Shuffle days for the null distribution and you destroy that clustering and produce a distribution that is too narrow — which makes the test too liberal and lets differences appear significant that are not. So we shift the calendar circularly against the price series instead: that destroys the calendar alignment and preserves the block structure.

Shifts by **multiples of twelve months** we exclude. They map almost every September back onto a September, so they barely scramble the calendar alignment at all — a reasoned modelling choice rather than a necessity, since a shift that preserves the observed statistic is in principle one possibility among others under the null. Our pinning study deliberately includes the real expiration day for exactly that reason.

How much that exclusion matters we measured rather than assumed — paired, i.e. the same shifts once with and once without the exclusion, across eight seeds: it **raises** the p-value by +0.008, from roughly 0.116 to 0.124. Small, consistent in sign, and with no consequence for the result; both variants sit well above 0.05. The code had previously carried the assumption that it worked the other way round.

## How many observations does such a measurement need?

The pinning study is a useful yardstick here, because it shows both sides.

Across all 158 names and 369 months together, 0.35 percentage points are measurable. **Per individual name they are not:** depending on the history, a few dozen to a few hundred expiration days remain, and in the scatter of so few observations the effect vanishes. The median of the individual differences is +0.28 percentage points, and 86 of 158 names are positive — a rate barely distinguishable from a coin flip.

So the same true effect is once established and once invisible, and the difference lies exclusively in the number of observations. Run a backtest over 30 trades and you need a correspondingly large effect — for a small one that count does not suffice, and the p-value then says only that the measurement was too coarse.

## How to read the p-values on this site

Four points that apply to every one of our analyses:

Beside every p-value stands the **effect size** and the **number of observations**. Without those two it is not interpretable.

Every measurement states **how many questions were asked**. A number from a family of 470 tests reads differently from one out of a single, pre-specified test.

Results the sample cannot carry get **no p-value** but the label *descriptive* — at 36 events a p-value would be false precision.

And a significant effect is **not a recommendation to trade**. This site gives no investment advice; which of our measurements leaves anything at all after costs is set out in the [overview of all analyses](/en/blog/market-rules-tested/).

## Frequently asked questions

### What does p = 0.05 actually mean?

That a result of this size would occur in one case out of twenty in a world without the effect under investigation. Not that the rule is true with 95 percent probability — that reinterpretation is the single most common misreading.

### Can an effect be significant and still not tradable?

Routinely, and our best-evidenced finding is exactly such a case: 0.35 percentage points at p = 0.0050 leave hardly any room for fees. Significance measures distinguishability from chance, not size. Given enough observations any tiny difference becomes significant.

### Does "not significant" mean the effect does not exist?

No. It means this measurement cannot separate it from chance. That may be down to the effect or to the sample. For volatility in September and October the figure is 1.059 against 1.000 — the measurement simply does not suffice to make more of it.

### Why is the bootstrap share not a p-value?

Because a bootstrap draws with the observed labels and its distribution is therefore centred on the measured estimate, not on zero. It answers "how uncertain is my estimate". A p-value needs a distribution representing a world **without** the effect, and for that the labels have to be scrambled, as in a permutation test.

### How many observations does a significance test on price data need?

There is no fixed number; it depends on the size of the effect sought and on the scatter. One reference point from our measurements: 0.35 percentage points needed 41,203 observations to become measurable — spread across the individual names, those same 0.35 percentage points were invisible.

<!--
#### Social Media Snippet

**LinkedIn:**
Our best-evidenced finding is economically worthless — and it is the best entry point into the p-value I know.
0.35 percentage points at p = 0.0050, across 41,203 observations and 30 years. Soundly measured. Survives no fee.
We report p-values on every study page and had never explained them. Now on six of our own measurements, each with a different lesson:
— p = 0.0050: significant and still unusable
— p = 0.127: "not significant" is a statement about the instrument, not about the world
— p = 0.935: the most informative of the lot — exactly the base rate, no information
— 470 tests, ~24 expected chance hits, zero dependable findings
— and an error of our own: the share of bootstrap draws below zero is not a p-value, because a bootstrap is centred on the estimate rather than on zero. Replaced by a permutation test.
Not investment advice. → seasonalpha.ai

**Twitter/X:**
Significant ≠ profitable.
Our best-evidenced finding: 0.35 percentage points at p = 0.0050, 41,203 observations. Sound. And worthless, because fees are larger than the effect.
P-values explained on six of our own measurements — including one error we made.
#Statistics #Markets #SeasonAlpha
-->

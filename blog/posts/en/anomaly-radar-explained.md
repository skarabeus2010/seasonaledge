---
title: "Anomaly Radar Explained: Why SAP Can Be 'Normal' Despite a −28 % Chart"
seo_title: "Anomaly Radar SeasonAlpha: Reading Z-Score + Percentile Correctly"
slug: anomaly-radar-explained
de_slug: anomalie-radar-erklaert
date: 2026-04-08
category: education
tags: [anomaly-radar, ki-score, percentile, z-score, sap, education, statistical-anomaly, ai-analysis, deviation, seasonality]
description: "The Anomaly Radar shows a score of 24/100 (Normal) for SAP — even though the price is 28 % below the historical average. Here's why Z-score and percentile rank actually get this right."
ticker: SAP
screenshot: anomalie-radar-sap-beispiel.png
status: published
---

<!--
Keyword plan:
- Main keyword: anomaly radar explained
- Secondary keywords: Z-score stocks, percentile rank stock market, AI quick check SeasonAlpha, statistical anomaly market
- LSI: seasonal deviation, standard deviation return, historical comparison stock
-->

## An Apparent Contradiction

You open the [Annual Cycle for SAP](/jahreszyklus?t=SAP) and immediately notice two seemingly contradictory things:

![Anomaly Radar for SAP: Score 24/100 Normal, but the 2026 yearly path sits dramatically below the 11-year average](anomalie-radar-sap-beispiel.png)

At the top: The **Anomaly Radar** shows a score of **24 / 100** — **Normal**. Everything looks fine.

At the bottom: The **Seasonal Annual Chart** shows that SAP (gold line) in 2026 is roughly **28 percent below the 11-year average**. Instead of ~110 points, the price sits at ~72. Visually it looks like a crash.

**How can both be true at the same time?** The answer is the most important insight about the Anomaly Radar: **It does not measure what you see in that chart.**

## What the Anomaly Radar Actually Measures

The radar answers one very specific question:

> **"Is the return of the last 10 trading days unusual compared to the historical average for the same calendar period?"**

Three keywords are critical:

- **Last 10 days** — not the whole year, not since January, not the drawdown. Only the last 10 trading days.
- **Same calendar period** — we compare April 2026 with April 2015, April 2016, April 2017, and so on. Not with January or July.
- **Unusual** — measured in standard deviations (Z-score), not in percentage points.

The large drawdown visible in the lower chart happened mostly **in January–March 2026**. That was brutal at the time — but the Anomaly Radar does not ask about back then. It asks: What has happened in the last two weeks? And the answer is: nothing particularly dramatic.

## The Calculation in Detail

Let's look at the figures from the screenshot:

| Metric | Value |
|---|---|
| **10-day return SAP** (end of March to early April 2026) | **−0.89 %** |
| **Historical average** (early April, 11 years) | **+2.36 %** |
| **Difference** | **−3.25 percentage points** |
| **Score** | **24 / 100** |
| **Percentile rank** | **18th percentile** |

SAP is **3.25 percentage points below** the historical average for the same calendar period over the last 10 days. That sounds like a lot, but statistically it is not — and this is where the Z-score comes in.

**Z-score calculation** (simplified):

```
Z = (current return − historical average) / historical standard deviation
```

If the historical spread of 10-day returns in early April for SAP is, for example, ±4 percentage points, then a deviation of 3.25 pp is only about **0.8 standard deviations** — not a statistical outlier. The score scales the absolute Z-score by a factor of 30 and caps at 100:

```
Score = min(|Z| × 30, 100) = min(0.8 × 30, 100) = 24
```

**24 means: no anomaly.** The market is moving within historically normal noise.

## Why the Percentile Rank Is Still Interesting

The score says "Normal." The percentile rank says **18th percentile**. That is the slider in the screenshot pointing noticeably to the left — in the yellow edge zone, no longer in the green normal range.

**What does the 18th percentile mean?**

> Of all historical 10-day windows measured in early April for SAP, only **18 percent were worse** than the current return. 82 percent were better.

This is a **complementary perspective** to the score:

- **The score** measures deviation from the mean in standard deviations — "how many σ off?"
- **The percentile rank** measures position in the distribution — "where do you rank?"

Both can give different signals. In this case:

- Score 24 = few standard deviations off → nothing dramatic
- Percentile 18 = but in the bottom fifth of historical cases → notable, not extreme

This combination is exactly what we want to show: **The market is running weaker than normal, but not so weak that it constitutes a statistical outlier.** Both statements are true simultaneously.

**Percentile slider color coding:**

| Percentile | Color | Meaning |
|---|---|---|
| 20 – 80 | green | Normal — within the "middle band" |
| 10 – 20 or 80 – 90 | gold | Edge zone — notable |
| < 10 or > 90 | red | Extreme — statistically rare |

SAP at the 18th percentile falls just inside the gold zone. A value of 5 or 95 would be red — that would indicate something truly striking.

## And the Large Drawdown in the Chart?

The annual chart shows a different time horizon and answers a different question:

- **Anomaly Radar:** Where do we stand over the last 10 days relative to comparable periods?
- **Seasonal Annual Chart:** How has the entire year developed up to today compared to the multi-year average since January?

SAP had a sharp correction in January and February — clearly visible in the yearly path. In March and April, however, the price has **stabilized**. It is now making daily moves that fall within the historically normal range. The Anomaly Radar confirms exactly this: **"The crash is over; current price action is unremarkable."**

That is important information! Anyone looking at the chart and thinking "it will keep falling" is reminded by the radar: The last two weeks were not a crash — they were sideways noise. With a moderate underperformance, but nothing dramatic.

## When Should the Score Be High?

The anomaly score jumps to ≥70 (**Strongly anomalous**) when:

- **After a flash crash:** The market drops 15 % in 10 days while the same calendar period historically averages +1 %. Difference = −16 pp; with a typical standard deviation of perhaps 3 pp → Z-score ≈ 5 → Score = 100.
- **During a parabolic rally:** The market rises 12 % in 10 days while historically +2 % is normal. Difference = +10 pp → Score = 80+.
- **During unusually stable sideways movement** in a historically volatile period — rare, but possible.

The score is **not a bullish/bearish signal**. It only says: "Something unusual is happening — take a closer look." The direction (up or down) is shown in the other tiles (10-day return).

## Score Thresholds at a Glance

| Score | Label | Interpretation |
|---|---|---|
| **< 40** | Normal | Within historical noise |
| **40 – 69** | Slightly anomalous | Notable, worth watching |
| **≥ 70** | Strongly anomalous | Statistical outlier — look more closely |

## How I Use the Radar in Practice

Three practical use cases:

1. **Trade filter:** Before entering a seasonal trade (e.g., Sell in May, Turn-of-Month), check the score. At ≥70 it is better to wait — the market is currently in an unusual state, and seasonal patterns may be less reliable this week.
2. **Post-mortem check:** After a sharp market move: Was it really an outlier, or just everyday volatility? The percentile rank and the score give you a sober classification.
3. **Context for the chart:** When a chart looks visually dramatic, check the radar. As with SAP here — down 28 % looks dramatic, but the **last few days** are calm. That is a different story.

## Conclusion: Two Different Questions, Two Different Answers

The Anomaly Radar and the seasonal annual chart measure **different things**:

- **Annual chart** = where do you stand **since January** relative to the multi-year average?
- **Anomaly Radar** = is your current **10-day move** statistically unusual?

For SAP in the screenshot:
- **Annual chart says:** The year has been difficult (−28 % vs. average)
- **Anomaly Radar says:** But right now it is calm (−0.89 % over 10 days, score 24, 18th percentile)

Both are true. Both are useful. The art lies in asking the right question at the right time — and the Anomaly Radar answers a very specific one.

If you want to experiment with it yourself: The radar is active on the [Annual Cycle](/jahreszyklus), [Monthly Cycle](/monatszyklus), [TDoM Analysis](/tdom-analyse) and [Overnight vs. Intraday](/overnight) pages. Simply type in the ticker and check the score in the top right. The methodology is explained in the **ⓘ** badge next to the section title — hover over it to see the formula.

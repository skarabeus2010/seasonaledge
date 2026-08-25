---
title: "The DAX in September: Statistically Significant Weakness — The Significance Test Explained"
seo_title: "DAX September: Significantly Weak (Test Explained)"
slug: dax-september-significance
de_slug: dax-september-signifikanz
date: 2026-08-24
category: education
tags: [dax, september-effect, significance-test, t-test, p-value, seasonality]
description: "Is the DAX really significantly weak in September? Avg −1.55%, p=0.0241 — and how the t-test, p-value and effect size separate a real effect from noise."
ticker: ^GDAXI
status: published
---

<!--
Keyword-Plan:
- Main keyword: DAX September significant
- Secondary: September effect DAX, is the DAX weak in September, significance test seasonality explained, t-test p-value stocks, DAX September statistics, statistically significant monthly return
- LSI: null hypothesis, Cohen's d, effect size, win rate, relevance score, multiple testing, normalized returns, chance vs real effect
-->

## Negative Is Not the Same as Significant

The DAX loses an average of **1.55%** in September — by a wide margin its weakest calendar month. Yet the real question is not "How negative?" but "Is this real or random?". That is the crux: September is the **only** DAX month that is statistically significantly **negative** (p=0.0241). This article uses real figures to show **how** a significance test reaches that verdict — and why "significant" tells you far more than "negative on average".

## How Strong Is the September Effect in the DAX?

The data is the DAX (^GDAXI) over the longest available window: a back-calculated series reaching into the late 1950s, with **n=68 observations** per calendar month. We work with **normalized returns** — each month starts at a notional 100, and daily returns compound from there. That keeps long and short months comparable across 68 years, without old high index levels distorting the more recent ones.

The chart below ranks all twelve months by average return. September stands alone at the bottom.

![^GDAXI — Monthly performance (avg, n=68): September is by far the weakest month at −1.55%](dax-september-signifikanz/dax-monatsperformance.png)

September averages −1.55%. For comparison: June and August are also negative, but only at −0.27% and −0.24% — roughly a tenth of September's weakness. On the other side sit November (+1.56%), April (+1.35%) and December (+1.07%) as the strongest months.

A low average alone is weak evidence, though. What matters is whether the value comes stably from many years or is carried by a few outliers. For September the **win rate** backs the picture: only **37%** of the 68 years closed positive — the worst reading of any month.

## The Significance Test — Step by Step

To separate chance from a real pattern, SeasonAlpha uses a **one-sample t-test**. The idea is simple: we check whether the monthly mean credibly differs from zero — or whether zero fits comfortably inside the spread across years.

### Null Hypothesis and t-Value

The **null hypothesis (H0)** states: "The average September return is truly zero; any deviation is noise." The **t-value** measures how far the observed mean sits from zero, expressed in units of variability. It sets the signal (the mean) against the noise (the year-to-year spread, divided by the square root of n).

A large absolute t-value means a clear signal with little noise. September comes out at **t=−2.31**. The minus sign shows direction (below average), the magnitude of 2.31 shows strength.

### The p-Value and the ±1.96 Threshold

The **p-value** translates the t-value into a probability: how often would you see a result this extreme purely by chance if there were no September effect at all? For September it is **p=0.0241** — about 2.4%. The convention: **p below 0.05 counts as significant.**

With roughly 68 observations, the 5% cutoff corresponds to a t-value near **±1.96**. Anything beyond that threshold is significant. The next chart plots every month as a t-bar with exactly those ±1.96 lines.

![^GDAXI — t-statistic per month with the ±1.96 significance threshold: only September, April and November cross it](dax-september-signifikanz/dax-t-statistik.png)

Only three months break through: **September (−2.31)** to the downside, **April (+2.18)** and **November (+2.56)** to the upside. All others stay inside the neutral band — their means are consistent with pure chance.

### Cohen's d and the Relevance Score

Significance tells you **whether** an effect exists — not how **large** it is. That job goes to **Cohen's d**, the effect size: the mean divided by the standard deviation. A small d means the effect nearly disappears into normal monthly noise; a large d means a tangible difference.

SeasonAlpha combines both into a **relevance score**, a value between 0 and 1:

> Relevance = 50% · (1 − p) + 30% · win rate + 20% · min(Cohen's d, 1)

The score rewards three things at once: statistical certainty (low p), hit rate and effect size. September reaches **0.65** — a high value despite its negative direction, because significance and a stark miss rate come together.

## The Full Monthly Table

The table below lists all twelve months with average return, t-value, p-value, win rate, relevance score and verdict. Only months with p below 0.05 count as significant.

| Month | Avg return | t-value | p-value | Win rate | Relevance | Verdict |
|-------|-----------|---------|---------|----------|-----------|---------|
| January | +1.00% | 1.51 | 0.1345 | 54% | 0.63 | Not significant |
| February | +0.31% | 0.52 | 0.6033 | 54% | 0.37 | Not significant |
| March | +1.03% | 1.78 | 0.0796 | 65% | 0.70 | Borderline |
| April | **+1.35%** | **2.18** | **0.0331** | 59% | 0.71 | **Significant** |
| May | +0.31% | 0.51 | 0.6103 | 53% | 0.37 | Not significant |
| June | −0.27% | −0.47 | 0.6408 | 43% | 0.32 | Not significant |
| July | +1.01% | 1.59 | 0.1155 | 59% | 0.66 | Not significant |
| August | −0.24% | −0.34 | 0.7334 | 53% | 0.30 | Not significant |
| September | **−1.55%** | **−2.31** | **0.0241** | 37% | 0.65 | **Significant** |
| October | +0.70% | 0.86 | 0.3943 | 53% | 0.48 | Not significant |
| November | **+1.56%** | **2.56** | **0.0128** | 65% | 0.75 | **Significant** |
| December | +1.07% | 1.90 | 0.0619 | 59% | 0.69 | Borderline |

September is the **only significantly negative** month. April and November are significantly positive, while March and December sit just above the threshold (borderline). The result is a coherent picture: a weak autumn start, a strong year-end and a standout April in spring.

### Why June and August Don't Count

June (−0.27%) and August (−0.24%) are also negative — but with p=0.6408 and p=0.7334 they are miles from significance. Their means could just as easily be zero; the minus is well explained by chance. September is the exception: negative **and** robust. That is exactly the distinction the test makes visible — it stops you from turning every randomly red bar into a rule.

## Limits — A Sober Assessment

A significance test is a tool, not an oracle. Three caveats belong with it.

**Multiple testing.** We test twelve months. At a 5% threshold, you would expect roughly **one** false positive by chance alone. That September (p=0.024) coincides with a plausible narrative **and** that other coherent months are significant (November and April positive) strengthens the finding. A single significant month on its own would not be proof.

**Data quality.** The older decades of the back-calculated DAX series come from less liquid, partly reconstructed prices. They are not identical to today's market structure. And "significant in the past" is no promise for the next September — known seasonal effects are partly traded away over time.

**Causality.** Why September specifically is weak cannot be proven cleanly. Common context includes reallocation after the summer lull and a historical cluster of autumn crises. Those are stories, not established causes. The test measures a pattern, not its reason.

## Practical Takeaway — What to Do With It

Seasonality provides **context**, not a trading signal. September weakness explains why the DAX often feels sluggish at the autumn start — a reason to stay calm rather than react nervously. For active traders, the asymmetry is more interesting: a month with a 37% hit rate carries a different risk-reward profile than November at 65%.

SeasonAlpha shows the significance gauge with t-value, p-value, win rate and relevance score for every ticker and time index. You can click through the interactive [monthly cycle](/en/monatszyklus) yourself. How we check data and compute significance is laid out openly on the [methodology page](/en/ueber-uns). If you want the broad comparison of all months across the official index history, see our study on the [worst DAX month](/en/blog/worst-dax-month-seasonality/).

## Conclusion

In September the DAX is not just weak on average (−1.55%) but, as the only month, statistically significantly negative (t=−2.31, p=0.0241). The significance test cleanly separates this pattern from the random weakness in June and August. Significance is no proof of the future — but it shows which seasonal quirks are worth taking seriously. Try the significance gauge yourself on [seasonalpha.ai](https://seasonalpha.ai/en/monatszyklus).

## Frequently Asked Questions

### Is the DAX really significantly weak in September?
Yes. Over 68 years the DAX loses an average of 1.55% in September, with a t-value of −2.31 and p=0.0241. Since p sits below the 5% threshold, the effect counts as statistically significant — the only significantly negative month of the year.

### What does a p-value of 0.05 mean in the stock market?
The p-value is the probability of seeing a result this extreme purely by chance if there were no real effect. A p below 0.05 means under 5% chance probability — the usual line for "significant". For the DAX in September it is about 2.4%.

### Why aren't June and August significant even though they are negative?
Because their loss is tiny (−0.27% and −0.24%) and statistically not robust: p=0.64 and p=0.73 lie far above 0.05. Their means are consistent with pure chance, whereas September clearly stands out from the noise.

### Can I rely on the September effect?
No. Past significance does not guarantee a negative outcome next September. Multiple testing, less liquid legacy data and the trading-away of known effects limit its predictive power. Use the pattern as context, not as a trading signal.

<!--
#### Social Media Snippet

**LinkedIn:** In September the DAX is not just weak on average (−1.55%) — it is the only month whose weakness is statistically significant (p=0.0241). June and August are also negative, but pure noise (p=0.64 / 0.73). We use real figures to show how the t-test, p-value and effect size separate a genuine effect from chance. 📉 Which month surprises you? Charts + significance gauge: seasonalpha.ai

**Twitter/X:** DAX in September: avg −1.55%, t=−2.31, p=0.0241 → statistically significant. The ONLY significantly negative month. June/August also negative, but pure noise. Here's how the significance test works 👇 #Stocks #DAX #Statistics #SeasonAlpha

#### Interne Verlinkung
- /en/blog/worst-dax-month-seasonality/ (broad comparison of all months, 38 years)
- /en/monatszyklus (interactive monthly cycle + significance gauge per ticker)
- /en/ueber-uns (methodology, significance computation)

#### Content-Ideen (Folgeartikel)
- "Cohen's d made simple: how large is a seasonality effect really?"
- "Multiple testing in markets: why one significant month is no proof"
- "April and November: the two significantly strong DAX months in detail"
-->

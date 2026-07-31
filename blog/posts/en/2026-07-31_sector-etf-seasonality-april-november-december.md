---
title: "8 of 9 Sector ETFs Light Up Green: What 25 Years of Research Says About April, November and December"
seo_title: "Sector ETF Seasonality: April, November, December"
slug: sector-etf-seasonality-april-november-december
de_slug: sektor-etf-saisonalitaet-april-november-dezember
date: 2026-07-31
category: education
tags: [sector-etf, seasonality, sector-rotation, monthly-heatmap, november, april, xlk, calendar-anomalies]
description: "Nine US sector ETFs, 25 years of data: in April, November and December almost all show significantly positive returns. We cross-check with our own data."
ticker: XLK
status: published
---

<!--
Keyword-Plan:
- Main keyword: sector ETF seasonality
- Secondary: calendar anomalies stock market, seasonal sector rotation, XLK seasonality, best month sector ETF, S&P 500 sectors November, monthly heatmap ETF, sector ETF April, US sector ETFs seasonality
- LSI: significance, p-value, win rate, normalized returns, Select Sector SPDR, cyclical vs defensive sectors, muted months, monthly return
-->

## It is not the market that is seasonal — the sectors are

Most seasonality work looks at the whole market: S&P 500, DAX, Nasdaq. A study published in May 2024 in the *International Review of Financial Analysis* goes one level deeper and asks about **sector ETF seasonality** — which industry delivers, and when. The answer is unusually clear-cut.

The number worth quoting: across the 25 years from 1999 to 2023, **8 of 9 US sector ETFs show statistically significant positive returns in April, November and/or December** — and not a single one does so in six other months of the year. We recomputed all of it with our own data.

## What the study actually did

Abbas Valadkhani and Barry O'Mahony examined the nine **Select Sector SPDR ETFs** tracking the S&P 500 in "Sector-specific calendar anomalies in the US equity market" ([ScienceDirect, May 2024](https://www.sciencedirect.com/science/article/abs/pii/S1057521924002795)), covering January 1999 to December 2023.

The methodological trick: these nine ETFs have **no overlapping constituents**. Every S&P 500 stock sits in exactly one of them. That lets you isolate sector effects cleanly instead of blending them inside an index.

| Ticker | Sector |
|--------|--------|
| XLB | Materials |
| XLE | Energy |
| XLF | Financials |
| XLI | Industrials |
| XLK | Technology |
| XLP | Consumer Staples |
| XLU | Utilities |
| XLV | Health Care |
| XLY | Consumer Discretionary |

Two findings stand out. First, the positive calendar anomalies cluster in **April, November and December**. Second, there are six "**muted months**" (March, May, June, August, September, October) in which **not one** ETF shows a significant positive or negative anomaly — statistically, nothing reliable happens there at all.

## The cross-check with SeasonAlpha data

We ran the same nine ETFs over the same window (1999–2023, n = 25 years per month) through our own methodology: **normalized returns** per calendar year, monthly return as the change within the month window, plus a t-test against zero.

Bold values are statistically significant (p < 0.05):

| ETF | April | November | December |
|-----|-------|----------|----------|
| XLB | **+3.6%** (p 0.021) | **+3.2%** (p 0.011) | +2.2% (p 0.056) |
| XLE | **+4.7%** (p 0.004) | +2.1% | +1.2% |
| XLF | **+3.4%** (p 0.013) | +1.4% | +1.2% |
| XLI | **+3.2%** (p 0.018) | **+3.5%** (p 0.002) | +1.4% |
| XLK | +1.7% (p 0.191) | **+2.9%** (p 0.050) | +0.5% |
| XLP | **+1.6%** (p 0.012) | **+1.9%** (p 0.001) | +0.8% |
| XLU | **+2.5%** (p 0.005) | +0.5% | +1.5% (p 0.062) |
| XLV | **+2.2%** (p 0.008) | **+2.0%** (p 0.027) | **+2.1%** (p 0.017) |
| XLY | **+3.1%** (p 0.014) | **+2.9%** (p 0.006) | +0.9% |

Our result confirms the study — and comes out slightly stronger: **all nine ETFs** have at least one significantly positive month among April, November and December.

### April is the strongest single month

April dominates: **8 of 9 ETFs** are significantly positive, averaging **+2.9%**. The one exception is Technology (XLK, p = 0.191) — the very sector most investors assume sets the seasonal tone.

November ranks second: **6 of 9** significant, averaging +2.3%. December, by contrast, clears the significance bar for exactly one ETF (XLV, p = 0.017). Its reputation as a rally month is weaker at the sector level than the broad index suggests.

### The "muted months" hold up

The counter-test is what makes this convincing. The six muted months produce 54 individual tests (9 ETFs × 6 months), and in our data **exactly one** is significant (XLP in October, p = 0.035). Across 54 tests, chance alone would predict roughly one hit.

Put differently: for half the year, US sectors show **no reliable calendar anomaly**. That matters, because it suggests the April/November strength is not an artifact of an over-eager data search.

## What the heatmap shows

The monthly heatmap colors every single monthly return by year — green for gains, red for losses. That reveals not just the average but the **consistency** of a month. Here is the technology sector:

{{chart:monthly_heatmap:XLK:10}}

Two things stand out in the November column. Across the last ten completed years (2016–2025) it is **green in eight of ten cases**, averaging **+2.8%**. The September column right next to it is the mirror image: **−1.5%** with a hit rate of only 50%.

One reading note: the top row is the current year, 2026. Months that have not happened yet appear without a value — that is not a data error.

## Where the study and the present diverge

Seasonal patterns are not carved in stone. Two shifts show up clearly when we swap 1999–2023 for the **last 20 years (2006–2025)**:

**December has evaporated.** In that more recent window, **not one** of the nine ETFs is significant in December. Energy (XLE) is even slightly negative at −0.4%. Anyone betting on a sector-level "December effect" today is leaning mostly on older data.

**July has caught up.** The authors found July as an additional month for seven ETFs in their post-financial-crisis subsample. Our data supports that even more strongly: over 2006–2025, July is significantly positive for **8 of 9 ETFs** (all but XLE), averaging +2.8% with hit rates between 70% and 90%. XLF posts a positive July in 90% of those years.

Energy generally marches to its own drum — a useful contrast to the tech heatmap:

{{chart:monthly_heatmap:XLE:10}}

## Why these patterns exist at all

Calendar anomalies do not come from nowhere. Plausible drivers include:

- **Earnings-season rhythm:** April and October/November are quarterly reporting months, which concentrates positive surprises on the calendar.
- **Tax-year effects:** Loss harvesting in autumn and reinvestment afterwards support late-year strength.
- **Capital inflows:** Bonuses, pension contributions and year-end reallocations arrive in clusters.
- **Sector specifics:** Utilities (XLU) and staples (XLP) are rate-sensitive and defensive — their seasonality follows different cycles than energy or technology.

Important caveat: none of these is a law of nature. They explain why a pattern *can* be stable, not why it *must* hold next year.

## Limits — and what this means in practice

Three constraints are non-negotiable:

1. **Averages hide dispersion.** An average of +3.2% means individual years were down double digits. An 80% hit rate also means one year in five went the other way.
2. **Known anomalies decay.** The vanished December effect is exactly that. The better known a pattern, the sooner it gets priced in.
3. **Costs and taxes matter.** Rotating monthly across nine ETFs creates fees and taxable events that raw returns do not include.

On the front-running idea: Quantpedia notes in its write-up of the study that entering **one month earlier** — October for November — historically produced better results than naively waiting for the month to start. The logic makes sense if many participants know the same pattern. Our own data, however, shows **no significance in October** for any of the nine ETFs over 2006–2025, so front-running remains a hypothesis rather than a demonstrated effect.

For investors, the sober takeaway: seasonality provides **context, not a signal**. It can calibrate your sense of timing — for instance, knowing that a sluggish September in tech is historically normal.

To check the patterns across all 324 tickers yourself: the [monthly heatmap and monthly cycle](/en/monatszyklus) are interactive for any ticker, [sector rotation](/en/sektor-rotation) compares industries side by side, and the [scanner](/en/scanner) hunts for notable calendar effects across the entire universe.

## Methodology and transparency

We calculate **normalized returns** based on adjusted closing prices: each year starts at 100 and daily returns compound on top. Monthly returns are the change within the respective month window, and significance comes from a t-test against zero (p < 0.05). How we validate data is laid out openly on our [methodology page](/en/ueber-uns).

## Conclusion

**Sector ETF seasonality** is one of the better-documented calendar patterns in the US market: April and November carry most of the seasonal return, while the summer and early-autumn months are statistically silent. Our cross-check confirms the peer-reviewed study in both directions — for the strong months and for the muted ones.

At the same time, the last 20 years show that patterns migrate. December has all but disappeared; July has become notably stronger. That is precisely why seasonality is worth re-checking regularly rather than memorizing once. The interactive heatmaps for every sector are on [seasonalpha.ai](https://seasonalpha.ai/en/monatszyklus).

## Frequently Asked Questions

### Which month is historically best for US sector ETFs?
April. Over 1999–2023, 8 of 9 Select Sector SPDR ETFs posted a statistically significant positive April return, averaging +2.9%. November follows with 6 of 9 significant ETFs and an average of +2.3%.

### Does sector seasonality apply to November 2026?
Seasonality describes probabilities drawn from the past, not a forecast. Historically, November was significantly positive for six of the nine sectors, and for technology (XLK) it was green in eight of the last ten completed years. That is context — not a guarantee for any single year.

### What are "muted months"?
That is the authors' term for the six months of March, May, June, August, September and October, in which no sector ETF shows a statistically reliable calendar anomaly. In our cross-check, exactly one of 54 individual tests was significant — roughly what chance alone would produce.

### Can I build a strategy on sector seasonality?
Statistically, seasonality is a filter rather than a complete trading system. Rotation costs, taxes and the dispersion of individual years eat into the effect. Known anomalies also decay — the December effect, which disappears in the more recent data window, is a case in point.

<!--
#### Social Media Snippet

**LinkedIn:** 📊 New peer-reviewed study (International Review of Financial Analysis, 2024): 25 years of data, 9 US sector ETFs with no overlapping constituents. Result: 8 of 9 show significantly positive returns in April, November and/or December — and not one does so in six other months of the year. We recomputed it with our own data: confirmed, with two deviations. The December effect has vanished over the last 20 years, while July has become much stronger (8 of 9 ETFs significant). Which sector are you watching into the autumn? All heatmaps: seasonalpha.ai

**Twitter/X:** 25 years, 9 US sector ETFs, 1 clear pattern: April + November carry almost the entire seasonal return. In 6 months of the year: statistically nothing. We cross-checked the study with our own data — confirmed. #Stocks #Seasonality #SeasonAlpha

#### Internal linking
- /en/monatszyklus (monthly heatmap per ticker)
- /en/sektor-rotation (industry comparison)
- /en/scanner (calendar effects across all 324 tickers)
- /en/blog/second-half-of-the-year-h2-seasonality/ (Q4 context at index level)
- /en/blog/worst-dax-month-seasonality/ (September weakness in detail)

#### Content ideas (follow-ups)
- "Defensive vs. cyclical: how XLP and XLY differ seasonally"
- "The vanished December effect: when anomalies decay"
- "July strength across US sectors: what changed after 2008"
-->

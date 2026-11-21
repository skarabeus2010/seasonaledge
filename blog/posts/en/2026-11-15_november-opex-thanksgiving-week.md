---
title: "November Options Expiration: The Expiration Week and Thanksgiving Week in the S&P 500 Since 1973"
seo_title: "November OPEX and Thanksgiving Week: S&P 500 Data"
slug: november-opex-thanksgiving-week
de_slug: optionsverfall-november-thanksgiving-woche
date: 2026-11-15
category: marktausblick
tags: [opex, options-expiration, thanksgiving, sp500, november-2026, expiration-day]
ticker: ^GSPC
status: published
description: "November options expiration: the Thanksgiving week after expiration gave the S&P 500 +0.60% on average since 1973 (30 of 45 years up), p = 0.066."
---

<!--
Keyword plan:
- Main keyword: November options expiration / November OPEX
- Secondary: options expiration date November 2026, week after options expiration, Thanksgiving week stock market,
  OPEX week S&P 500, December 2026 triple witching, VIX expiration November
- LSI: third Friday, monthly expiration, holiday week, trading days, permutation test, median, share of up weeks
- Distinct from opex-effect-sp500-third-friday-drift (expiration-day drift), opex-cycle-explained (four phases, phase 4 =
  week after expiration) and options-expiration-pinning (closes at the strike). This article: November only and the
  coupling of expiration and Thanksgiving, with our own numbers for 1973–2025.
- Fact sheet: scripts/research/out/opex_november_thanksgiving_fakten.json (^GSPC data through 2026-11-13).
-->

## Expiration on Friday, a holiday the week after

On Friday, November 20, 2026, the monthly US options expire. Six days later is Thanksgiving: the New York Stock Exchange is closed on Thursday and closes early on the Friday after. This sequence is not a quirk of the 2026 calendar. In **45 of 53 years** between 1973 and 2025, Thanksgiving fell exactly six days after the November expiration, so the week after expiration was the holiday week.

We measured both weeks in the S&P 500. The Thanksgiving week after expiration returned **+0.60%** on average (median +0.85%, up in 30 of 45 years). The week after expiration in the other eleven months averaged −0.03% (n = 583). The gap is large but not statistically established (permutation test p = 0.066). The expiration week itself does not stand out in November.

## Why expiration and Thanksgiving almost always follow each other

US monthly options expire on the **third Friday** of the month, which in November means a date between the 15th and the 21st. Thanksgiving is the **fourth Thursday** of November and falls between the 22nd and the 28th.

If November 1 is not a Friday, the month's first Thursday comes before its first Friday. The third Friday then directly follows the third Thursday, and the fourth Thursday is six days later. Only when November 1 is a Friday does expiration land on the 15th and Thanksgiving on the 28th. The gap is then 13 days, with an ordinary week in between.

Between 1973 and 2025 that happened eight times: 1974, 1985, 1991, 1996, 2002, 2013, 2019 and 2024. The next year with a 13-day gap is 2030.

How expiration shapes market mechanics over the month is covered in our article on the [OPEX cycle](/en/blog/opex-cycle-explained/); the week after expiration is phase 4 there, when hedges are unwound.

## How we measured

- **Data:** S&P 500 price index (without dividends), daily returns from the log return stored in SeasonAlpha, frozen at the close of 2026-11-13. We evaluate the 636 months from January 1973 to December 2025.
- **Expiration day:** from February 2015 the expiration date published by Cboe, before that the third Friday by rule (the prior trading day if the exchange was closed). No November date ever had to be moved.
- **Expiration week:** the trading days of the calendar week up to and including expiration day, measured from the last close of the prior week to the close on expiration day.
- **Week after:** the trading days of the following calendar week, measured from the expiration-day close to the last close of that week. In the 45 years with a six-day gap these are exactly the four trading days of Thanksgiving week.
- **Test:** permutation test on the difference in means (20,000 shuffles, two-sided), with Welch's t-test as a cross-check. What a p-value tells you and what it does not is explained in our [article on the p-value](/en/blog/p-value-explained/).

## The November expiration week versus other months

The week leading into November expiration shows nothing unusual; if anything it is slightly weaker than in other months.

| Expiration week | n | Mean | Median | Up |
|---|---|---|---|---|
| November | 53 | −0.04% | +0.04% | 28 of 53 (52.8%) |
| Other months | 583 | +0.23% | +0.39% | 334 of 583 (57.3%) |

The difference in means is −0.27 percentage points, with t = −0.88 and p = 0.43 in the permutation test. A November effect in the expiration week is therefore **not established**. In both halves of the period (1973–1999 and 2000–2025) November sits slightly below the other months, in each case far from a reliable result (p = 0.75 and p = 0.45).

The well-known upward drift on expiration day itself is the subject of our article on the [OPEX effect in the S&P 500](/en/blog/opex-effect-sp500-third-friday-drift/); this article measures whole weeks.

![Mean cumulative path of the S&P 500 from five trading days before options expiration to four trading days after: November with Thanksgiving in the following week (n = 45) versus the other months (n = 583), 1973 to 2025](opex-november-thanksgiving/1_pfad_en.png)

The chart shows the mean path from five trading days before expiration (= 100) to four trading days after. In the 45 Novembers with Thanksgiving in the following week, the index stood at 99.75 on average the day before expiration and at 99.99 on expiration day. Four trading days after expiration, the Friday after Thanksgiving, it was at 100.57. In the other months the line is flatter and ends at 100.21.

## The week after: holiday week versus the usual post-expiration week

| Week after expiration | n | Mean | Median | Up |
|---|---|---|---|---|
| November, next week = Thanksgiving | 45 | +0.60% | +0.85% | 30 of 45 (66.7%) |
| Other months | 583 | −0.03% | +0.14% | 305 of 583 (52.3%) |
| All calendar weeks 1973–2025 | 2,766 | +0.17% | +0.31% | 1,561 of 2,766 (56.4%) |

Thanksgiving week was on average 0.63 percentage points ahead of the usual week after expiration. The permutation test gives p = 0.066, Welch's t-test p = 0.11 (t = 1.62). Both are above the 0.05 threshold, so the difference is **not established**, even though the direction is the same in both halves of the period (1973–1999: +0.39% vs −0.15%, p = 0.22; 2000–2025: +0.82% vs +0.10%, p = 0.16).

Thanksgiving week has only four trading days, while most other weeks have five (486 of the 583 comparison weeks). Per trading day, the holiday week comes to +0.15% against −0.004%. The permutation test gives p = 0.035 for that, Welch's t-test p = 0.12. Depending on the test the value lands just below or above the threshold, which is not enough to call it established.

![Mean and median return in the week after options expiration: November with Thanksgiving in the following week (n = 45), November with a 13-day gap (n = 8), other months (n = 583) and all calendar weeks (n = 2,766), 1973 to 2025](opex-november-thanksgiving/2_woche_danach_en.png)

For comparison, the week after expiration in the other months was on average weaker than an arbitrary calendar week (−0.03% vs +0.17%, p = 0.051 in the permutation test). The two groups overlap, because every week after an expiration is also a calendar week, so treat this only as a hint.

Where the strength of Thanksgiving week comes from cannot be separated with these data. Across all 53 years, including the eight with a 13-day gap, Thanksgiving week averaged +0.61% (median +0.85%, up in 37 of 53 years). Against all calendar weeks that is not established either (p = 0.17). Research has long described the trading day before a holiday as friendly for stocks; more in our article on [Thanksgiving and Black Friday in the stock market](/en/blog/thanksgiving-stock-market-black-friday/).

## The years with a 13-day gap

In the eight years with a 13-day gap, expiration and the holiday come apart. The week after expiration is then an ordinary week, and Thanksgiving week follows a week later.

| Year | Expiration | Thanksgiving | Week after expiration | Thanksgiving week |
|---|---|---|---|---|
| 1974 | Nov 15 | Nov 28 | −4.19% | +1.55% |
| 1985 | Nov 15 | Nov 28 | +1.72% | +0.32% |
| 1991 | Nov 15 | Nov 28 | −1.69% | −0.24% |
| 1996 | Nov 15 | Nov 28 | +1.51% | +1.11% |
| 2002 | Nov 15 | Nov 28 | +2.28% | +0.62% |
| 2013 | Nov 15 | Nov 28 | +0.37% | +0.06% |
| 2019 | Nov 15 | Nov 28 | −0.33% | +0.99% |
| 2024 | Nov 15 | Nov 28 | +1.68% | +1.06% |

The week after expiration averaged +0.17% in these years (median +0.94%, up in 5 of 8). Thanksgiving week averaged +0.68% (median +0.80%) and was up in 7 of 8 years. With eight cases the group is too small for a test; it only shows that Thanksgiving week was mostly positive even without an expiration right before it.

## Key dates for 2026

| Event | Date in 2026 |
|---|---|
| VIX settlement (futures, November contract) | Wednesday, Nov 18 |
| Monthly options expiration | Friday, Nov 20 |
| Thanksgiving, NYSE closed | Thursday, Nov 26 |
| Early close (1:00 pm New York time) | Friday, Nov 27 |
| Major expiration (triple witching) | Friday, Dec 18 |

November 20 is an **ordinary monthly expiration**. Triple witching, the simultaneous expiration of index futures, index options and stock options, happens only in March, June, September and December; the next one is December 18. All dates including the holiday rules are on our [Options Expiration](/en/opex) and [VIXpiration](/en/vixpiration) pages.

## What research says about expiration days

Hans Stoll and Robert Whaley described elevated volume and price reversals in the late 1980s on days when index futures and index options expired together. Ni, Pearson and Poteshman showed in 2005 that individual stocks with active options trading close near a strike price more often on expiration day. Our own analysis of closes at the strike is in the article on [expiration-day pinning](/en/blog/options-expiration-pinning/).

There is no study on the weeks around November expiration that separates the holiday from the expiration. Our numbers cannot do that either: in 45 of 53 years the two events coincide.

## Limitations

- **Nothing established:** no comparison in this article falls below p = 0.05 in both tests. Thanksgiving week was clearly ahead on average, but individual weeks vary widely (standard deviation around 2.5% in the November group).
- **Expiration or holiday:** because expiration and Thanksgiving almost always coincide, the strength of the week cannot be attributed to either event. The eight years with a 13-day gap are too few for that.
- **Early years:** listed stock options have existed in the US since 1973, options on the S&P 500 itself only since 1983. In the early years of the series, expiration therefore carried less weight in the index.
- **Price index:** returns exclude dividends and costs. Over a single week that matters little, but the figures are still not achievable returns.
- **History:** 45 years is a small sample for a weekly pattern. A single sell-off in a holiday week can shift the mean noticeably.

## What this means for investors

The week leading into November expiration has historically differed little from other expiration weeks. The week after was usually friendlier in November than in other months, because it is almost always Thanksgiving week. Whether the holiday, the end of expiration or both are behind it, the data do not say.

For 2026 that means: the VIX settles on November 18, monthly options expire on November 20, and the following week has only three and a half trading days. The bigger date for hedges and position changes is December 18. These numbers do not produce a trading signal.

## Frequently asked questions

### When is options expiration in November 2026?

On Friday, November 20, 2026. It is the third Friday of the month and the day the monthly US stock and index options expire. The VIX settlement for the November contract is two days earlier, on Wednesday, November 18.

### Is November 20, 2026 triple witching?

No. Triple witching only happens in the quarterly months of March, June, September and December. On November 20 the monthly options expire; the next quarterly expiration is on Friday, December 18, 2026.

### Is the week after options expiration weaker?

In months other than November, the week after expiration in the S&P 500 averaged −0.03% from 1973 to 2025 (n = 583), slightly below an arbitrary calendar week at +0.17%. In November, when Thanksgiving falls in that week, it was +0.60% (n = 45). Neither difference is statistically established.

### Why does options expiration almost always come before Thanksgiving?

Expiration falls on the third Friday, Thanksgiving on the fourth Thursday of November. Unless November 1 is a Friday, the fourth Thursday comes exactly six days after the third Friday. Between 1973 and 2025 that was the case in 45 of 53 years; the last 13-day gap was in 2024.

### When is the next major expiration?

On Friday, December 18, 2026. On this triple-witching day quarterly options and index futures expire together, and volume is much larger than on a monthly date. The dates are on our [Options Expiration](/en/opex) page.

<!--
#### Social media snippet

**LinkedIn:** Monthly US options expire on Nov 20, and Thanksgiving is six days later. That sequence occurred in 45 of 53 years since 1973. The week after expiration averaged +0.60% in November (median +0.85%, 30 of 45 up) versus −0.03% in other months (n = 583). Not statistically established (p = 0.066), and expiration and holiday cannot be separated. How do you read the holiday week? https://seasonalpha.ai/en/blog/november-opex-thanksgiving-week/

**Twitter/X:** November OPEX lands 6 days before Thanksgiving in 45 of 53 years. S&P 500 the week after: +0.60% avg (n=45) vs −0.03% in other months (n=583). p = 0.066, so not established. #StockMarket #OPEX #SeasonAlpha

#### Internal links
- /en/opex, /en/vixpiration
- /en/blog/opex-cycle-explained/ (phase 4), /en/blog/opex-effect-sp500-third-friday-drift/, /en/blog/options-expiration-pinning/, /en/blog/p-value-explained/
- Link to /en/blog/thanksgiving-stock-market-black-friday/ added (2026-11-21)

#### Content ideas
- December triple witching: expiration week and Christmas week
- The week after expiration across all months: phase 4 of the OPEX cycle with our own numbers
- Holiday weeks in the S&P 500 compared (Thanksgiving, Christmas, Independence Day)
-->

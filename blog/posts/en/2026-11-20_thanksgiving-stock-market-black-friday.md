---
title: "Thanksgiving and the Stock Market: S&P 500 Since 1942, Black Friday and the DAX Without Wall Street"
seo_title: "Thanksgiving Stock Market: Returns, Black Friday, DAX"
slug: thanksgiving-stock-market-black-friday
de_slug: thanksgiving-boerse-black-friday
date: 2026-11-20
category: education
tags: [thanksgiving, black-friday, holiday-effect, sp500, dax, seasonality, trading-hours]
ticker: ^GSPC
status: scheduled
publish_date: 2026-11-20
description: "S&P 500 in Thanksgiving week since 1942: +0.58% on average versus +0.17% in other weeks (n = 84, p = 0.09). Plus Black Friday, the Monday after and the DAX."
---

<!--
Keyword plan:
- Primary: Thanksgiving stock market (title, description, first paragraph, trading-hours H2)
- Secondary: is the stock market open on Thanksgiving, Black Friday stock market hours, Thanksgiving week stocks,
  Monday after Thanksgiving, DAX on Thanksgiving, holiday effect S&P 500
- LSI: early close, NYSE, Nasdaq, Xetra, pre-holiday effect, daily range, hit rate, p-value
- Scope: november-opex-thanksgiving-week covers the Nov 20 expiration and the week after from an options angle.
  This article: the holiday, trading hours, the calendar effect and the DAX.
- Data: fact sheet from the frozen snapshot (Supabase, close 2026-11-13), every figure checked.
-->

## Thanksgiving week in the S&P 500: a little stronger than usual, not statistically supported

Across the **84 Thanksgiving weeks from 1942 to 2025**, the S&P 500 rose **+0.58%** on average (median +0.66%), measured from the close on the Friday before the week to the close on the Friday after the holiday. All other weeks in the same period averaged **+0.17%**. 55 of the 84 holiday weeks were positive (65.5%), against 56.8% of the other weeks.

The gap of 0.41 percentage points is not statistically supported: the p-value is **0.09**. Against other November weeks it shrinks to 0.25 points (p = 0.36). Below are the 2026 trading hours, the individual days around the holiday, the Monday after, and what the DAX does on a day when Wall Street is closed.

## Thanksgiving 2026 trading hours: NYSE, Nasdaq and Xetra

Thanksgiving falls on **Thursday, November 26, 2026**. The New York Stock Exchange and Nasdaq are closed that day. On Friday, November 27, Black Friday, both trade only until **1:00 p.m. New York time (7:00 p.m. in Germany)** instead of the usual 4:00 p.m.

| Day | NYSE / Nasdaq (New York time) | Xetra / DAX (German time) |
|---|---|---|
| Wed Nov 25 | regular, 9:30 a.m. to 4:00 p.m. | regular, 9:00 a.m. to 5:30 p.m. |
| Thu Nov 26 (Thanksgiving) | closed | regular, 9:00 a.m. to 5:30 p.m. |
| Fri Nov 27 (Black Friday) | early close, 9:30 a.m. to 1:00 p.m. | regular, 9:00 a.m. to 5:30 p.m. |
| Mon Nov 30 | regular | regular |

*At the end of November both the US and Germany are on standard time; Frankfurt is six hours ahead of New York.*

In Frankfurt, November 26 is an ordinary trading day. The DAX trades while the world's largest stock market takes the day off. All closures and early closes of the season are listed on the [holidays page](/en/feiertage).

## Thanksgiving week in the S&P 500 since 1942

Thanksgiving has been fixed on the fourth Thursday of November since 1942, so that is where the analysis starts. The basis is the S&P 500 price index (without dividends), with each daily return measured from the previous close to the day's close. Every one of the 84 holiday weeks has complete prices on all the days examined.

The chart shows the average cumulative path from the Friday before the week to the Monday after, split into 1942–1987 and 1988–2025. The grey column marks the closed Thursday.

![S&P 500 in Thanksgiving week: average cumulative path from the Friday before to the Monday after, 1942–1987 and 1988–2025](thanksgiving-boerse/1_pfad_en.png)

Both periods end Black Friday at almost the same level: +0.57% (1942–1987) and +0.58% (1988–2025). They got there differently. In the earlier period the index stood at −0.23% on average by Monday of the week and only caught up from Tuesday. Since 1988 it was already at +0.25% on Monday and at +0.49% by Wednesday. On the Monday after, both periods gave some of it back, ending at +0.21% and +0.32%.

Neither half differs significantly from the other weeks of its period: 1942–1987 +0.57% versus +0.15% (p = 0.13), 1988–2025 +0.58% versus +0.19% (p = 0.35).

## Wednesday, Black Friday and the Monday after

The week has four trading days. Three of them count as holiday days: the Wednesday before the closure, the Friday after, and the Monday after. Each is compared with all other trading days on the same weekday from 1942 to 2025.

| Day | Mean | Median | Positive | n | Ordinary day | p-value |
|---|---|---|---|---|---|---|
| Wednesday before Thanksgiving | +0.26% | +0.25% | 72.6% | 84 | +0.08% (55.1% positive) | 0.06 |
| Friday after Thanksgiving | +0.22% | +0.24% | 66.7% | 84 | +0.06% (55.3% positive) | 0.051 |
| Monday after Thanksgiving | −0.28% | −0.22% | 38.1% | 84 | −0.05% (49.1% positive) | 0.15 |

*Comparison days: 4,177 Wednesdays, 4,123 Fridays, 3,869 Mondays outside Thanksgiving week. p-value from a two-sided Welch t-test.*

The Wednesday before the holiday was positive in almost three years out of four. At p = 0.06 it sits just above the usual 0.05 threshold and therefore does not count as established. What a p-value does and does not tell you is covered in [Is the effect real? The p-value in six of our own measurements](/en/blog/p-value-explained/).

Black Friday was also stronger than an ordinary Friday on average. Since 2013 it is documented as an NYSE early-close day; in those 13 years it averaged −0.13% (median +0.06%) and was positive 7 times. The average is pulled down mainly by 2021 at −2.27%, the day the first Omicron reports hit.

Wednesday and Friday combined were positive in 63 of 74 years since 1952 (85.1%), the way the Stock Trader's Almanac usually counts it. Since 1988 it is 29 of 38 years, and the combined gain fell from +0.62% on average (since 1952) to +0.33% (since 1988).

### The Monday after Thanksgiving versus ordinary Mondays

On average it was weaker: −0.28%, with only 38.1% of years positive. Ordinary Mondays averaged −0.05%, ordinary November Mondays +0.04%. The t-test gives p = 0.15 and 0.07 respectively; a permutation test against November Mondays comes in at 0.027, below the threshold. With four measures, two comparison groups and two test methods, one value below 0.05 is to be expected even without a real effect. The worst Monday was December 1, 2008, at −8.93%.

## The DAX on a day without Wall Street

For the DAX the analysis starts in 2002, the first year for which the Xetra trading calendar is verified. That gives 24 Thanksgiving Thursdays on which the DAX traded, compared with 1,206 other Thursdays in the same years.

![DAX on Thanksgiving versus ordinary Thursdays 2002–2025: mean daily return and mean daily range](thanksgiving-boerse/2_dax_en.png)

On returns there is no established difference. The DAX rose +0.26% on Thanksgiving on average (median +0.32%), 16 times out of 24; ordinary Thursdays returned +0.01% (median +0.08%). A p-value of 0.24 is consistent with chance.

The **daily range**, the gap between the day's high and low relative to the prior close, behaves differently. On Thanksgiving it averaged 1.02% (median 0.72%), on ordinary Thursdays 1.61% (median 1.32%). The p-value is 0.002, and 0.012 in a permutation test. In 21 of 24 years the range stayed below that year's average for the other Thursdays; at the median it reached 52% of that average.

The reason is the shape of the trading day. On a normal day New York opens at 3:30 p.m. German time, and in the two hours until the Xetra close the DAX often moves with US prices. On Thanksgiving that afternoon impulse is missing. We do not analyse turnover: the index volume data are not clean enough for it.

## The last ten years

| Year | Thanksgiving | Wednesday | Friday | Monday after | Week |
|---|---|---|---|---|---|
| 2016 | Nov 24 | +0.08% | +0.39% | −0.53% | +1.44% |
| 2017 | Nov 23 | −0.08% | +0.21% | −0.04% | +0.91% |
| 2018 | Nov 22 | +0.30% | −0.66% | +1.55% | −3.79% |
| 2019 | Nov 28 | +0.42% | −0.40% | −0.86% | +0.99% |
| 2020 | Nov 26 | −0.16% | +0.24% | −0.46% | +2.27% |
| 2021 | Nov 25 | +0.23% | −2.27% | +1.32% | −2.20% |
| 2022 | Nov 24 | +0.59% | −0.03% | −1.54% | +1.53% |
| 2023 | Nov 23 | +0.41% | +0.06% | −0.20% | +1.00% |
| 2024 | Nov 28 | −0.38% | +0.56% | +0.24% | +1.06% |
| 2025 | Nov 27 | +0.69% | +0.54% | −0.53% | +3.73% |

*S&P 500 price index. Week = close on the Friday before the week to close on the Friday after Thanksgiving.*

In eight of the ten years the index rose over the whole week, by +0.69% on average. The Monday after was positive only three times (mean −0.10%). Friday averaged −0.14%, weaker than the long-run figure, again mostly because of 2021. Ten years are too few to say anything about holiday effects; the table mainly shows how widely individual years scatter.

## What research says about the holiday effect

Lakonishok and Smidt (1988) and Ariel (1990) found in US price data that days before exchange holidays returned a multiple of the ordinary daily return. Later work saw the effect weaken after it was published. A study extending the data to 2019 (Ko and Yang, 2021) reports it mainly among small companies.

The figures here fit that picture without proving it. Black Friday averaged +0.33% in 1942–1987 against +0.09% for ordinary Fridays (p = 0.026), but only +0.09% against +0.03% in 1988–2025 (p = 0.63). For the Wednesday the gap stayed similar in both halves, but is significant in neither (p = 0.13 and 0.24). The S&P 500 consists of large companies, the part of the market where the literature barely finds the effect any more.

We asked the same question for [Independence Day in the Nasdaq](/en/blog/independence-day-effect-nasdaq/); sector seasonality for November and December is in the article on [sector ETF seasonality](/en/blog/sector-etf-seasonality-april-november-december/). The November 20 options expiration and the week after are covered in [November OPEX and Thanksgiving week](/en/blog/november-opex-thanksgiving-week/).

## Limitations

- **No signal.** In the main comparison (all years, t-test) neither one of the holiday days nor the whole week differs from the ordinary case with p below 0.05. The two exceptions, Black Friday 1942–1987 and the Monday against November Mondays in the permutation test, come from sub-analyses.
- **Multiple tests.** Four measures, three periods and two comparison groups produce many p-values. Some hits below 0.05 are to be expected by chance alone.
- **Outliers.** In 2008 the week gained +12.03%, in 2011 it lost −4.69%. With n = 84, such years move the mean noticeably, which is why the median and the share of positive years are shown alongside.
- **Price index.** Dividends are not included. Over a few days this barely changes the comparison.
- **Calendar.** Our NYSE calendar is verified from 1971, before that it follows the rules. Black Friday early closes are verified from 2013; for earlier years this article only says "Friday after Thanksgiving". Until 1952 the NYSE also traded on Saturdays, so in those years the Monday after is measured from the Saturday close.
- **No costs.** Fees, spreads and taxes are ignored. Holiday strategies with fixed rules can be recalculated on the [Plain Vanilla page](/en/plain-vanilla) as a method; that is not a recommendation.

## Conclusion

Since 1942, Thanksgiving week has on average been friendlier for the S&P 500 than an ordinary week, +0.58% against +0.17%, and the Wednesday before was positive in 72.6% of years. None of these differences is statistically established, and the Black Friday edge has largely disappeared since 1988. The Monday after was weaker on average, again without a robust test.

The DAX does show an established difference, and it concerns volatility: on Thanksgiving its daily range since 2002 was a good third smaller on average than on other Thursdays (1.02% against 1.61%, p = 0.002). The direction of the day could not be read from it.

## Frequently asked questions

### Is the stock market open on Thanksgiving?

The US exchanges NYSE and Nasdaq are closed on Thanksgiving, in 2026 on Thursday, November 26. Xetra and the Frankfurt Stock Exchange trade normally from 9:00 a.m. to 5:30 p.m. German time.

### What time does the stock market close on Black Friday?

On the Friday after Thanksgiving, NYSE and Nasdaq close at 1:00 p.m. New York time, which is 7:00 p.m. in Germany. In 2026 that is November 27.

### Does the stock market go up during Thanksgiving week?

On average, yes: the S&P 500 rose +0.58% in the 84 holiday weeks from 1942 to 2025, against +0.17% in other weeks. 55 of the 84 weeks were positive. With p = 0.09 the difference is not statistically established.

### Is the Monday after Thanksgiving weak?

On average it was weaker: −0.28% and positive in only 38.1% of years, against −0.05% on ordinary Mondays. The t-test gives p = 0.15, so the effect is not established.

### Does the DAX trade on Thanksgiving?

Yes. Thanksgiving is not a German holiday and Xetra is open. Since 2002 the DAX's daily range on Thanksgiving averaged 1.02% against 1.61% on other Thursdays; returns did not differ in a way the data can support (+0.26% against +0.01%, p = 0.24).

<!--
#### Social media snippets

**LinkedIn:** Thanksgiving and the stock market, recalculated: 84 Thanksgiving weeks in the S&P 500 since 1942 averaged +0.58% versus +0.17% for other weeks. Not statistically established (p = 0.09). The DAX is clearer: on Thanksgiving, without Wall Street, a daily range of 1.02% versus 1.61% (p = 0.002). → https://seasonalpha.ai/en/blog/thanksgiving-stock-market-black-friday/

**Twitter/X:** S&P 500 in Thanksgiving week since 1942: avg +0.58% vs +0.17% (n = 84, p = 0.09). Monday after avg −0.28%, only 38.1% positive. DAX on Thanksgiving: range 1.02% vs 1.61%. #Thanksgiving #StockMarket #SeasonAlpha

#### Internal links
- /en/feiertage, /en/plain-vanilla
- /en/blog/independence-day-effect-nasdaq/
- /en/blog/sector-etf-seasonality-april-november-december/
- /en/blog/november-opex-thanksgiving-week/
- /en/blog/p-value-explained/
-->

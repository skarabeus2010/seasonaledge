---
title: "Turn-of-Month Effect Explained: Why the Last 3 and First 3 Days of the Month Are Different"
seo_title: "Turn-of-Month Effect: Why Month-End Is Special for Stocks"
slug: turn-of-month-effect-explained
de_slug: turn-of-month-effekt-erklaert
date: 2026-04-09
category: education
tags: [turn-of-month, tom, seasonality, education, sp500, pension-fund-effect, month-end, liquidity-cycle, intramonth, window-dressing]
description: "The Turn-of-Month Effect: Why the last 3 and first 3 trading days statistically outperform — with 30 years of S&P 500 data and explanation."
ticker: ^GSPC
screenshot: turn-of-month-tom-chart.png
status: published
---

<!--
Keyword-Plan:
- Main keyword: Turn of Month Effect
- Secondary keywords: TOM strategy, month-end stock market, Pension Fund Effect, Window Dressing
- LSI: seasonal strategy, month-end, intra-month pattern
-->

## What Is the Turn-of-Month Effect?

The **Turn-of-Month** (TOM) effect describes one of the most robust seasonal anomalies in equity markets: the last trading days of a month and the first days of the following month deliver above-average returns — with a significantly higher win rate than the rest of the month.

Specifically: the **6-day window** from the third-to-last day of the month through the third trading day of the next month often generates more return than the remaining ~15 trading days combined. This is not merely a curiosity — it is one of the best-documented patterns in academic finance literature, first described by Lakonishok and Smidt in 1988.

## The Data: 30 Years of S&P 500

We analyzed the last 30 years of the S&P 500 by position within the month. Each trading day is classified as a **TDOM** (Trading Day of Month): TDOM 1 = first trading day, TDOM 21 = last trading day (varies by month).

| Position | Avg. Daily Return | Win Rate |
|---|---|---|
| **Last 3 days of month** (TDOM −3 to −1) | **+0.15%** | **62%** |
| **First 3 days of month** (TDOM 1 to 3) | **+0.12%** | **60%** |
| Mid-month (TDOM 5–15) | +0.02% | 53% |
| Last third (TDOM 15 to −4) | –0.01% | 51% |

The **6-day TOM window** together delivers roughly **+0.8% per month** — that is ~10% annual return if you only trade these 6 days and stay in cash the rest of the time. The market overall returns ~9% per year over the same 30 years.

Put differently: **The TOM days account for virtually the entire market return** — the remaining 15 days contribute almost nothing.

![Intra-month TDOM progression S&P 500 with the typical U-shape at month-end](turn-of-month-tom-chart.png)

In the chart, the pattern is immediately visible: the curve declines in the last third of the month, turns sharply upward in the last 3 days, and continues this rally into the first 3 days of the following month. These exact 6 days form the TOM effect.

## Heatmap: Which Months Have the Strongest TOM Effect?

The average obscures the fact that the TOM effect is not equally strong every month. The following heatmap shows the average daily return for each month × TDOM combination:

![Turn-of-Month Heatmap S&P 500 — Month × TDOM Position](turn-of-month-heatmap.png)

Notable: the TOM days are positive in **almost every month** (green cells at the right and left edge of each row), but are particularly pronounced in **November, December, and April**. In September — the statistically weakest month — the effect is weakest and sometimes even negative. The TOM effect is thus modulated by the overall seasonal environment.

## Why Does the Effect Exist?

There are three plausible explanations, which are not mutually exclusive:

### 1. Pension Fund Inflows
Pension funds and 401(k) plans in the US typically receive contributions at month-end or month-start. This money is mechanically invested into the market — a constant buy flow that occurs precisely at TOM. US pension funds alone manage over $30 trillion; even small percentage inflows move the market.

### 2. Window Dressing
Fund managers polish their portfolios at month-end for reporting dates. They buy outperformers and sell underperformers — which makes strong stocks even stronger (window dressing). Quarter-end and year-end effects are particularly pronounced.

### 3. Liquidity Cycles
Companies pay salaries at month-end, dividends are distributed, bond interest flows — the cash flow in the system is high around the month-end. More cash = more investment readiness = higher demand for stocks.

None of these explanations alone is sufficient — but together they generate a measurable, persistent bias.

## Does the Effect Work Outside the S&P 500?

Yes. We found the same pattern for the **DAX, Nasdaq, Dow Jones, and even Bitcoin**. The strength varies:

| Index | TOM Spread (6 days vs. rest) |
|---|---|
| Nasdaq 100 | +0.9% / month |
| S&P 500 | +0.8% / month |
| DAX | +0.7% / month |
| Dow Jones | +0.6% / month |
| Bitcoin | +1.2% / month |

Bitcoin is surprisingly pronounced — likely because there are barely any institutional pension flows there, and retail behavior dominates (paycheck → DCA buys).

## How Do You Trade the TOM Effect?

### Option A: Strictly Mechanical
Long on the third-to-last trading day of the month, close on the third trading day of the following month. Six days long, 15 days cash. Simple to implement, but transaction costs eat into some of the edge.

### Option B: Overnight Only
Long at the close of the third-to-last day, hold overnight every day, close on the third day. Reduces intraday risk and additionally exploits the [Overnight Effect](/blog/overnight-intraday-split-google/).

### Option C: Filter with TDOM Position
In the dashboard, the TDOM card shows the win rate and average return for the next three trading days. If the win rate is >60%, it is a TOM day. You then trade selectively rather than mechanically.

## Where the Effect Does Not Work

Three warnings:

1. **Crash months** break the pattern: In February 2020 (COVID), September 2008 (Lehman), October 2008, the market fell through — TOM days were in free fall negative. Mechanical TOM strategies need a stop-loss.
2. **Bear markets in general:** In pronounced downtrends, the TOM effect is weaker. Win rate falls from 62% to ~52%.
3. **Very short months** (February): With only ~19 trading days, "beginning" and "end" overlap more, and the pattern is more diffuse.

## Conclusion: One of the Best Seasonal Anomalies Overall

The TOM effect is real, statistically significant over >130 years, and consistent across asset classes. Those who understand it have a statistical edge — provided they also understand its limits.

If you want to check the current TOM status for your favorite ticker yourself: the [Month-End page](/monatswechsel) shows you the TOM heatmap, significance test, and streak analysis for every ticker. In the [Dashboard](/dashboard) you also see the TDOM position with historical win rate for the next 3 days.

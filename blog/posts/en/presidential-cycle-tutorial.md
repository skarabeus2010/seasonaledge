---
title: "Tutorial: How to Use the US Presidential Cycle for Your Investment Decisions"
seo_title: "Presidential Cycle Tutorial: Using the 4-Year Cycle in Markets"
slug: presidential-cycle-tutorial
de_slug: praesidentenzyklus-tutorial
date: 2026-04-11
category: tutorials
tags: [presidential-cycle, election-cycle, tutorial, dow-jones, midterm, sp500, election-year, pre-election-rally, four-year-cycle, political-cycles]
description: "Step-by-step tutorial: how the US presidential cycle influences the stock market — with 130 years of data and SeasonAlpha analysis."
ticker: ^DJI
screenshot: praesidentenzyklus-4-cycles.png
status: published
---

<!--
Keyword-Plan:
- Main keyword: Presidential cycle stock market tutorial
- Secondary keywords: Election cycle stocks, 4-year cycle, US elections stock market, Midterm Year Stocks
- LSI: election cycle, Pre-Election Year, Post-Election Year, Election Year, Best Year Stocks
-->

## What Is the Presidential Cycle?

The **US Presidential Cycle** (or Election Cycle) is one of the oldest and best-documented seasonality patterns in equity markets. The idea: the four years of a US presidency each have their own statistically distinct return patterns. Yale Hirsch first systematically described the pattern in the 1960s — and it still works today.

The four years are classified as:

| Position | Name | Examples |
|---|---|---|
| **Year 1** | Post-Election Year | 2025, 2021, 2017 |
| **Year 2** | Midterm Year | **2026**, 2022, 2018 |
| **Year 3** | Pre-Election Year | 2027, 2023, 2019 |
| **Year 4** | Election Year | 2028, 2024, 2020 |

The current year **2026 is a Midterm Year** — historically the weakest year in the cycle.

## The Results: 130 Years of Dow Jones

We analyzed the Dow Jones Industrial Average from 1898 to 2025 — 32 complete 4-year cycles, 128 years in total. Here is the summary:

| Cycle Year | Avg. Annual Return | Avg. Max Drawdown | Win Rate (positive) |
|---|---|---|---|
| Year 1 (Post-Election) | +3.8% | –16.7% | 56% |
| **Year 2 (Midterm)** | **+5.1%** | **–17.9%** | **59%** |
| **Year 3 (Pre-Election)** | **+13.2%** | **–16.1%** | **78%** |
| Year 4 (Election) | +7.9% | –15.8% | 66% |

The pattern is **clear and persistent**:

- **Pre-Election Year (Year 3) is by far the strongest** — on average nearly 4× the return of Post-Election Years
- **Midterm Year has the deepest drawdown**
- **Election Years are solid but not spectacular**
- **Post-Election Years are the weakest return year**

![Presidential cycle 4 cycles in the Dow Jones — historical trajectories overlaid](praesidentenzyklus-4-cycles.png)

## Why Does the Pattern Exist?

Three plausible explanations:

### 1. Political Stimulus Cycles
Presidents have an incentive to stimulate the economy in the **third and fourth year** of their term — just before the next election. Tax cuts, infrastructure packages, expansionary fiscal policy tend to be passed in the second half of the term. This drives Pre-Election Years.

### 2. Uncertainty Resolution
In the **Midterm Year**, political uncertainty is highest: the president has lost power, the opposition mobilizes, reforms are blocked or rushed through. More uncertainty = higher volatility = deeper drawdowns. **After** the midterm election (i.e., from November of the Midterm Year onward), a relief rally typically returns.

### 3. Self-Fulfilling Prophecy
Many professional investors know the pattern and position accordingly. This reinforces it. If there were no fundamental effect at play, it would "trade away" — but it doesn't, because the fundamental drivers (stimulus, politics) are real.

## Tutorial: How to Use the Cycle Yourself

### Step 1: Determine Cycle Position

A year's position in the presidential cycle can be read directly from the **remainder of division by 4** — i.e., `year mod 4`:

| `Year mod 4` | Position | Meaning | Example Years |
|:---:|---|---|---|
| **0** | Election Year | Presidential election year (US election in November) | 2020, 2024, 2028 |
| **1** | Post-Election Year | 1st year of the new president's term | 2021, 2025, 2029 |
| **2** | **Midterm Year** | 2nd year — midterm congressional elections | 2022, **2026**, 2030 |
| **3** | Pre-Election Year | 3rd year — preparation for the next election | 2023, 2027, 2031 |

**Example 2026:** `2026 ÷ 4 = 506 remainder 2` → **Midterm Year**. It is the second year of the president elected in November 2024, and in November 2026 the midterm elections to the US Congress take place.

> ⚠️ **Note on convention:** Some sources count the Election Year as "Year 4" (end of the term), others as "Year 1" (beginning of the new electoral period). We use here the historically common sequence **Post-Election → Midterm → Pre-Election → Election** and compute directly via `year mod 4`, which is unambiguous.

### Step 2: Activate the Cycle Filter in SeasonAlpha

On the **[Annual Cycle page](/jahreszyklus)** you will find a "Cycle" filter in the sidebar. Choose from:

- **All years** (default) — historical average of all years
- **Midterm Years only** — only years like 2022, 2018, 2014, 2010 ...
- **Pre-Election Years only** — only years like 2023, 2019, 2015, 2011 ...

The seasonal trajectory recalculates — **with the filter you see the actual historical pattern for the current cycle position**.

### Step 3: Compare with the Overall Average

Do both in sequence: once "All years" and once with the cycle filter. Compare the trajectories. Where are the differences?

For 2026 (Midterm), the typical differences are:

- **Deeper drawdowns in spring and summer**
- **Weaker performance through September**
- **Relief rally from November onward** (after the midterm elections)

### Step 4: Adjust Risk Management Accordingly

If you actively trade and take the cycle pattern seriously:

| In Midterm Years | Recommendation |
|---|---|
| Q1–Q2 | Reduced position, higher cash allocation |
| Summer (May–Sep) | High caution, consider hedges (puts, defensive sectors) |
| Q4 (from November) | Scale up — historically the strongest period |

In **Pre-Election Years** (i.e., 2027), there is more room for more aggressive long positions.

## How Reliable Is the Pattern?

Honest assessment with data:

- **Statistical significance:** The difference between Pre-Election (+13.2%) and Post-Election (+3.8%) Years over 130 years is **highly significant** (p < 0.001 in the t-test).
- **But:** There are **massive outliers**. 2008 was an Election Year (should have been solid) — the market fell 34%. 2022 was a Pre-Election Year with further weakness.
- **The statistical expectation holds for portfolios across many years**, not for any single year.

Put differently: you can use the pattern to calibrate your **statistical expectation** — but never to guarantee a single year's forecast.

## What the Next 4 Years Mean Statistically

| Year | Position | Historical Expectation |
|---|---|---|
| **2026** | **Midterm** | **Volatile, weak summer, Q4 recovery** |
| 2027 | Pre-Election | Statistically strongest year (+13% avg.) |
| 2028 | Election | Solid (+8% avg.), but election-dependent |
| 2029 | Post-Election | Weakest year (+4% avg.) |

For long-term thinkers: **2027 has historically the best risk-return trade-off.** But that is only one data point among many — valuation, macro, and politics need to be added.

## Conclusion

The presidential cycle is one of the most robust seasonal patterns overall — statistically significant over 130 years, fundamentally explainable, stable in recent decades. Those who understand it and combine it with other filters (sector, valuation, macro) have a measurable edge in asset allocation.

Try it yourself: [Annual Cycle page](/jahreszyklus) with the cycle filter, and for a quick overview the [Dashboard](/dashboard) — the Trading Day Header shows you the current cycle position directly in the top right (e.g., "MidTerm" for 2026).

**Further reading:**
- [Midterm Drawdowns 2026](/blog/drawdown-midterm-election-2026/) — How deep did Midterm Years fall historically?
- [Sell in May 2026](/blog/sell-in-may-2026/) — What the summer seasonality concretely means
- [What Is Seasonality?](/blog/was-ist-saisonalitaet/) — Fundamentals article

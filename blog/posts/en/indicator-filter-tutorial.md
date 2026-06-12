---
title: "Tutorial: How to Use Indicator Filters in SeasonAlpha"
seo_title: "Indicator Filter Tutorial: Combining RSI, SMA & MACD"
slug: indicator-filter-tutorial
de_slug: indikator-filter-tutorial
date: 2026-03-27
category: tutorials
tags: [tutorial, indicator, filter, rsi, sma, trading, technical-analysis, bollinger-bands, macd, ema, trading-signals]
description: "Step by step: combine seasonality with technical indicators (RSI, SMA, MACD, Bollinger) in SeasonAlpha for more precise signals."
ticker: AAPL
status: published
---

## Why Indicator Filters?

The core question: **Does a seasonal pattern work better when certain market conditions are met?**

For example: Is the full moon effect stronger when the RSI is below 30? Are Mondays more profitable when the price is above the 200-day moving average?

With the indicator filters in SeasonAlpha you can find out exactly that.

## Available Indicators

SeasonAlpha offers 6 technical indicators as filters:

- **SMA** (Simple Moving Average) — trend filter
- **EMA** (Exponential Moving Average) — faster trend filter
- **RSI** (Relative Strength Index) — momentum / overbought-oversold
- **Bollinger Bands** — volatility filter
- **MACD** — trend and momentum combination
- **LBR Oscillator** — Linda Bradford Raschke's short-term indicator

## Step-by-Step Guide

### 1. Open a Page with Indicator Filters

The filters are available on: Weekdays, Month-End, Moon Phases, OPEX, and Central Banks.

### 2. Open the Filter Expander in the Sidebar

Scroll down in the sidebar. Under "Technical Filters" you will find the expander. Click "Add filter".

### 3. Choose Indicator + Condition

Example setup:

- **Filter 1**: RSI, period 14, condition "RSI < 30"
- **Filter 2**: SMA, period 200, condition "Close > SMA"

Both filters are linked with **AND**: only days on which BOTH conditions are met are included in the calculation.

### 4. Interpret the Results

At the top of the page you will see a blue badge:

**RSI(14) < 30 | Close > SMA(200) — 1,247 / 6,300 trading days (19.8%)**

This means: out of 6,300 trading days, 1,247 met both conditions. The seasonal analysis is based only on these filtered days.

## Practical Example: Moon Phases + RSI

{{chart:seasonal_yearly:AAPL:20}}

Compare the normal full moon effect with the filtered result (RSI < 30). If the filtered version performs noticeably better, you have a statistical indication that the moon phase effect is stronger under certain market conditions.

## Tips

- **Don't filter too narrowly**: When fewer than 100 days remain, the statistical significance is low
- **Note Shift(1)**: The filter uses the indicator value from the PREVIOUS day to avoid look-ahead bias
- **Combine wisely**: SMA as a trend filter + RSI as a timing filter is a proven combination

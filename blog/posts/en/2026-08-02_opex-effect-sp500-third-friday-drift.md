---
title: "The Third-Friday Effect: Why the S&P 500 Opens Differently on Options Expiration"
seo_title: "OPEX Effect on the S&P 500: The Third-Friday Spike"
slug: opex-effect-sp500-third-friday-drift
de_slug: opex-effekt-sp500-third-friday-drift
date: 2026-08-02
author: SeasonAlpha Research
category: education
tags: [opex, expiration, sp500, third-friday-effect, options-expiration, charm-vanna, dealer-positioning, seasonality, triple-witching]
description: "OPEX effect on the S&P 500: on the third Friday the market opens 18.5 basis points higher on average (Baltussen 2024). The mechanism behind the spike."
ticker: SPY
status: published
---

<!--
Keyword-Plan:
- Primary keyword: OPEX effect S&P 500
- Secondary keywords: options expiration effect, third Friday stock market, Third-Friday spike, pre-OPEX drift, Triple Witching S&P 500, charm vanna dealer flows, SOQ special opening quotation
- Long-tail: why does the market rise before options expiration, what happens on the third Friday, S&P 500 expiration day statistics, OPEX drift explained, Baltussen Derivative Payoff Bias
- LSI: basis points, normalized returns, delta hedging, market maker, open interest, weekday effect, volatility, seasonality, triple witching
- Search intent: readers want to understand whether and why the S&P 500 shows a systematic pattern around options expiration — and how reliable it is.
-->

## Something is different on the third Friday

The **OPEX effect on the S&P 500** is one of Wall Street's best-documented microstructure patterns — and one of its most misunderstood. The headline number comes from academic research: across 2003 to 2021, the US equity market opened on average **18.5 basis points above the prior close on the third Friday** of each month (Baltussen, Terstegge & Whelan, 2024). Statistically it is highly significant (t-statistic above 4.5) — not random noise.

18.5 basis points sounds trivial. Scaled to the volume traded in the S&P 500 options market, the authors estimate a wealth transfer of roughly **$4 billion per year** in SPX alone. The third Friday, in other words, is not an ordinary trading day but a structurally distinctive one. This article shows where the effect comes from, how robust it is — and where our own data hits its limit.

## What actually happens on expiration day

"Options expiration," or **OPEX**, is the day on which listed options and futures expire. In the US, for the major index contracts, that is the **third Friday** of the month. Four times a year — in March, June, September and December — index options, index futures and single-stock options all expire together. This quadruple event is known as **Triple Witching**.

One technical detail is the key to the whole effect: US index derivatives are not settled at Friday's *close* but at the **open** — via the so-called *Special Opening Quotation* (SOQ), a settlement value computed on Friday morning from the opening prices of all index constituents.

It is in exactly this thin window — Thursday close to Friday open — that the jump appears. Baltussen and colleagues describe a **tent-shaped move**: the price climbs from Thursday's close into Friday's open, peaks around the SOQ, and partially reverts by Friday midday. The effect is strongest on Triple Witching dates, when the largest amount of open interest expires at once.

## The data: a measurable distortion since 2003

The finding is no one-off. It sits in a whole line of peer-reviewed research showing that options expiration measurably moves the underlying prices.

- **Baltussen, Terstegge & Whelan (2024), "The Derivative Payoff Bias"** — the Third-Friday spike described above: +18.5 bps of SOQ over the prior close, t above 4.5, ~$4bn/year in SPX. Importantly: before 2003 the effect was absent — it emerged with today's market structure.
- **Ni, Pearson & Poteshman (2005), *Journal of Financial Economics*** — the classic paper on *pinning*: closing prices of optioned single stocks cluster at the option strike prices on expiration day. Returns were shifted by an average of roughly **16.5 basis points**, aggregated across about **$9 billion** of market capitalization.
- **Golez & Jackwerth (2012), *JFE*** — extended the pinning finding to the **S&P 500 futures**, i.e. the index level.

Three independent studies, two of them in one of the three most important finance journals in the world. The common thread: options expiration is not a neutral event. The hedging flows of options dealers leave a small but systematic footprint in the price.

## The mechanism: charm and vanna force the buying

Why does the market open higher on the third Friday? The explanation lies not in investor sentiment but in the mechanics of the **dealers** — the market makers who sell options and hedge their risk in the underlying.

The typical starting point: funds and institutions buy index puts as insurance against falling prices. Dealers are on the other side of that trade — they are **net short puts** and hedge by selling stock or futures short. But this short hedge is not static. Two "Greeks" cause it to shrink into expiration:

- **Charm (time decay):** As expiration approaches, the delta of out-of-the-money puts falls. The dealer needs less short hedge and **buys stock back**.
- **Vanna (volatility):** If the market stays calm, implied volatility declines. That too shrinks the put delta — the dealer covers as well.

Both forces push in the same direction, on the same days: a **mechanical buying pressure into the third Friday**. Baltussen and colleagues attribute the spike explicitly to this charm-driven inventory management by market makers — amplified by the thin liquidity of the overnight window. This is the causal layer that plain calendar statistics cannot deliver. If you want the mechanism in detail, see our post [Dealer Positioning Explained](/en/blog/dealer-positioning-gamma-vanna-charm/).

## What our data shows — and what it does not

Here comes the honest framing this topic (Your Money or Your Life) demands. The 18.5 bps effect is an **overnight, or opening, jump**: measured from Thursday's close to Friday's *open*. SeasonAlpha works with **normalized daily closing prices** (close-to-close, each year rebased to 100). That means we **cannot replicate the overnight jump one-to-one** — that would require clean opening prices and intraday data. We show the seasonal frame and the weekly drift, not the SOQ jump itself.

What we can show is the **Friday dimension** of the effect. The chart below shows the average daily return of SPY by weekday over 20 years:

{{chart:weekday_bars:SPY:20}}

The Friday bar is a *close-to-close* average across **all** Fridays — so it isolates neither the third Friday nor the opening jump. It only frames how the weekday on which the SOQ falls behaves overall. This distinction — what we can measure and what we cannot — is the core of serious data work.

To place it in the bigger picture, here is the normalized yearly path. The monthly options expiration is a recurring event within this underlying pattern:

{{chart:seasonal_yearly:SPY:20}}

Each year starts at 100 and daily returns compound onto it; the shaded band (±1 standard deviation) shows the dispersion. Twelve monthly expiration dates sit inside this frame — the calendar marks them, the mechanism explains them.

## Limits and counter-examples: not a free lunch

An honest data study must also show where the pattern breaks.

**The effect has weakened.** The Baltussen study covers 2003 to 2021. Over the last four years or so, OPEX-week outperformance has faded — the better known a pattern, the more it gets arbitraged away. A historical average is not a forecast for next Friday.

**After expiration the picture often flips.** The practitioner white paper by **Ambrus Capital / Kris Sidial ("Changing Market Structure")** shows the opposite of the upward drift in its Figure 7: a strategy buying the S&P only during the OpEx window lost roughly 15 percent over three years. Once the hedging cushion falls away after expiration, the market becomes more directional and more volatile — the notorious post-OPEX weakness. The drift *into* expiration and the weakness *after* it are two sides of the same mechanic.

**It is an overnight effect.** For a retail investor placing day orders, the 18.5 bps SOQ jump is effectively untradeable — it forms in an illiquid window outside regular hours. The value of this insight is in **understanding**, not in clicking "buy."

**No signal, no investment advice.** The OPEX effect is structural context, not a trading signal. Macro events — a Fed meeting, an inflation print, geopolitical news — override the thin pattern at any time.

## The SeasonAlpha angle: seasonality meets dealer flows

There are many gamma vendors, and there are many seasonality sites. **Almost no one marries the two.** That is exactly where our edge lies.

Pure seasonality sites show the calendar pattern on average — *that* the third Friday stands out. Pure options vendors show the dealer flow right now — *how* the hedge is currently positioned. SeasonAlpha has both: an **exchange-accurate calendar** for OPEX, Triple Witching and VIXpiration on our [Options Expiration](/en/opex) page, plus the gamma, vanna and charm metrics on [Dealer Positioning](/en/dealer-positioning). That lets us say *why* a seasonal pattern exists, instead of merely showing it.

For the investor, that means: you don't just see that a period is statistically distinctive, you understand the structural cause — and can better judge when a pattern is robust and when it gets overridden.

## Conclusion

The OPEX effect on the S&P 500 is real and academically documented: +18.5 basis points on the third Friday over 18 years, highly significant, charm-driven. It exists because market makers have to buy back their short hedges into expiration as time decay and falling volatility shrink their put deltas.

But the headline number is an **overnight jump**, not a close-to-close trade — and the effect has weakened lately. The real value lies in understanding the mechanism, not in a simple buy signal. Explore the [options expiration calendar](/en/opex) and [Dealer Positioning](/en/dealer-positioning) yourself on **seasonalpha.ai** — and see how calendar and dealer flows interact.

## Frequently Asked Questions

### What is the OPEX effect on the S&P 500?

The OPEX effect describes a systematic price distortion around options expiration day (the third Friday of the month). According to Baltussen, Terstegge & Whelan (2024), the US market opened on average 18.5 basis points above the prior close on those days — highly significant over 2003 to 2021. It is driven by the hedging behavior of market makers.

### Why does the market often rise before options expiration?

Because dealers who are net short puts have to buy back their short hedge into expiration. Time decay (charm) and falling volatility (vanna) shrink the delta of their puts — both force them to buy on the same days. This mechanical buying pressure creates the upward drift into the third Friday.

### Can I trade the Third-Friday spike myself?

Hardly. The 18.5 bps effect is an overnight jump from Thursday's close to Friday's open, measured at the Special Opening Quotation — inside a thinly traded window outside regular hours. Ordinary day orders cannot capture it. It is structural context, not a trading signal, and not investment advice.

### Why can't SeasonAlpha reproduce the 18.5 bps jump exactly?

Because we work with normalized daily closing prices (close-to-close). The effect, however, is an opening jump that requires clean open and intraday data. So we show the seasonal frame and the weekly drift, not the overnight jump itself — and we name that limit deliberately rather than fake precision.

### Is the effect stronger on Triple Witching days?

Yes. On the four big expiration days in March, June, September and December, index options, index futures and single-stock options all expire at once. The largest amount of open interest matures, so the hedging flows are correspondingly larger — Baltussen et al. (2024) measure the spike most clearly on those days.

<!--
#### Social Media Snippet

**LinkedIn:** Something is different on the third Friday. Across 2003–2021, the S&P 500 opened on average 18.5 basis points above the prior close on options expiration day (Baltussen, Terstegge & Whelan 2024, t>4.5) — a wealth transfer of roughly $4bn/year in SPX alone. The reason is not sentiment but mechanics: market makers buy back their short hedges into expiration through charm (time decay) and vanna (falling vol). Important and honest: this is an overnight/opening jump (SOQ), not a close-to-close trade — untradeable with daily data, and the effect has weakened lately. Not a signal, just structural context. How do you frame expiration day? https://seasonalpha.ai/en/opex

**Twitter/X:** The Third-Friday effect: across 2003–2021 the S&P 500 opened +18.5 bps above the prior close on options expiration (Baltussen 2024, t>4.5). Charm & vanna force dealers to buy back. But: overnight jump, not a close-to-close signal. seasonalpha.ai/en/opex #OPEX #SP500 #Options

#### Interne Verlinkung
- /en/opex (options expiration calendar — direct feature)
- /en/dealer-positioning (gamma/vanna/charm — the mechanism)
- /en/vixpiration (place the vol cycle around expiration)
- /en/blog/dealer-positioning-gamma-vanna-charm/ (mechanism in detail)

#### Content-Ideen (Folgeartikel)
- "Post-OpEx weakness & Triple Witching: what happens after the big expiration (data study)"
- "Pinning: why stocks cling to round strikes on expiration day (Ni/Pearson/Poteshman)"
- "VIXpiration: the second expiration cycle almost no one knows"
-->

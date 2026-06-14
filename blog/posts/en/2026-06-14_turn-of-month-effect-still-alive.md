---
title: "The Turn-of-the-Month Effect: Declared Dead — Yet Alive (in the Right Window)"
seo_title: "Turn-of-the-Month Effect 2026: Still Alive?"
slug: turn-of-month-effect-still-alive
de_slug: turn-of-month-effekt-lebt-noch
date: 2026-06-14
category: education
tags: [turn of the month, seasonality, calendar effect, month-end, s&p 500]
description: "New 2026 research and our own data show the turn-of-the-month effect isn't dead — it just changed its time window. What that means for investors."
ticker: ^GSPC
status: published
---

<!--
Keyword-Plan:
- Main keyword: turn-of-the-month effect
- Secondary keywords: month-end stock returns, calendar effect equities, S&P 500 seasonality, does the turn-of-the-month effect still work
- LSI keywords: arbitrage, rebalancing, risk deferral, win rate, statistical significance, t-statistic
-->

## A Declared-Dead Effect That Refuses to Die

The turn-of-the-month effect — the tendency of equity markets to post above-average returns around the month boundary — is widely considered "arbitraged away." But a new 2026 study and a look at our own data paint a different picture: the effect is **alive** — it has merely **shifted its time window**.

Here we summarize the current research and test it against 20 years of S&P 500 data.

## What Is the Turn-of-the-Month Effect?

Since the late 1980s, finance research has documented that a large share of monthly equity returns is concentrated in a few days around the month-end — the last trading day of a month and the first days of the next. A widely cited study on this is by John McConnell and Wei Xu ([SSRN](https://www.ssrn.com/abstract=925589)).

The common explanation: at month boundaries, salaries, savings plans and institutional flows enter the market, and large funds rebalance their portfolios.

## The New Research: The Effect Persists

In a 2026 study published in the *Journal of International Financial Markets, Institutions and Money*, **Nuri Volkan Kayaçetin** examines the turn-of-the-month effect across roughly 30 countries over 1994–2023 ([DOI](https://doi.org/10.1016/j.intfin.2026.102309)). His finding: the effect persists in nearly all markets studied — with Japan as the exception. According to the study, the average return at the turn of the month is around ten basis points, versus essentially zero on ordinary days. As a mechanism, Kayaçetin points to **infrequent rebalancing** and a deferred risk premium (**"risk deferral"**).

A practitioner analysis by the pseudonymous quant author **QuantSeeker** (February 2025) adds the missing piece ([source](https://www.quantseeker.com/p/turn-of-the-month-strategies-do-they)): the **classic, narrow window** (last trading day plus the first three days) is **no longer statistically significant** for U.S. equities — likely arbitraged away. The **broader window**, by contrast (three days before to three days after the month boundary), still shows a significant premium of roughly 5 to 12 basis points.

## The Test With Our Data

This exact distinction can be reproduced on SeasonAlpha. The chart below shows the average cumulative return curve of the S&P 500 around the month boundary (t0 = last trading day), over the past 20 years.

{{chart:tom_effect:^GSPC:20}}

And the result confirms the research strikingly well:

| Window | Avg Return | Hit Rate | t-statistic | Significant? |
|--------|------------|----------|-------------|--------------|
| Classic (t0 to t+3) | +0.14% | 58% | 1.18 | no |
| Broad (t−3 to t+3) | +0.50% | 62% | **3.15** | **yes (p < 0.01)** |

Across 245 month boundaries, the narrow window no longer delivers a statistically reliable edge (t = 1.18). The broad window, with a t-statistic of 3.15, is clearly significant. The month-boundary effect hasn't disappeared — it simply starts **earlier**, a few days before month-end.

## Why Does the Narrow Window Vanish?

This is economically logical: the better known and tighter a pattern, the sooner traders exploit it until the excess return is gone. The broader window is harder to trade "cleanly" — and that is exactly where the effect survives. Kayaçetin's mechanism fits: if part of the premium is paid as a deferred risk premium, it cannot be fully arbitraged away.

## What Does This Mean for Investors?

Three sober conclusions:

- An effect that "vanishes" is often just **mismeasured** — the window decides.
- Even the broad window averages **half a percentage point** — interesting as context, but no free lunch. Transaction costs and dispersion eat much of it.
- Seasonal patterns belong in a **toolbox**, not at its head.

On seasonalpha.ai you can check this yourself: open **Turn-of-Month**, pick a ticker and the window — the significance gauge (t-value, p-value, win rate) instantly shows whether the effect holds up.

## Conclusion

The turn-of-the-month effect is a case study: current research (Kayaçetin 2026) and our own S&P 500 data agree that it persists — but in the broader time window, not the classic narrow one. Anyone taking calendar effects seriously must look closely at how they are measured. Try it yourself on seasonalpha.ai.

## Sources

- Kayaçetin, N. V. (2026): *Infrequent rebalancing, risk deferral, and equity returns at the turn of the month.* Journal of International Financial Markets, Institutions and Money. [DOI](https://doi.org/10.1016/j.intfin.2026.102309)
- QuantSeeker (2025): *Turn-of-the-Month Strategies: Do They Still Work?* [quantseeker.com](https://www.quantseeker.com/p/turn-of-the-month-strategies-do-they)
- McConnell, J. J. & Xu, W.: *Equity Returns at the Turn of the Month.* [SSRN](https://www.ssrn.com/abstract=925589)
- Own calculation: SeasonAlpha, S&P 500 (^GSPC), 2006–2026, 245 month boundaries.

## Frequently Asked Questions

### Is the turn-of-the-month effect still real?
Yes — both a 2026 study (Kayaçetin) and our own S&P 500 analysis find a statistically significant effect, but in the broader window (three days before to three days after the month boundary), not the classic narrow one.

### Why doesn't the classic narrow window work anymore?
It was likely arbitraged away: the better known and tighter a pattern, the faster the excess return disappears. In our data the narrow window, with a t-statistic of 1.18, is no longer significant.

### Can I build a strategy on this?
Be careful. The average premium is small, and transaction costs and dispersion erode it quickly. It is more sensible to treat the effect as one of several building blocks, not as a standalone signal.

### Does this hold outside the U.S. too?
According to Kayaçetin's study, the effect persists across roughly 30 countries — with Japan as a notable exception. On seasonalpha.ai you can check the DAX, the Dow and many other indices yourself.

<!--
#### Social Media Snippet

**LinkedIn:** "The turn-of-the-month effect is dead." Really? 🤔 A new study (Kayaçetin 2026) and our own 20 years of S&P 500 data say: it's alive — just in the broader window. The classic narrow window (t-stat 1.18) is no longer significant; the broad one (t-stat 3.15) is. A nice example of how much the measurement decides the result. More on seasonalpha.ai. #Stocks #Seasonality #SeasonAlpha #CalendarEffect

**Twitter/X:** Turn-of-the-month effect dead? New 2026 research + our S&P data: no — only the narrow window (t=1.18, ns) got arbitraged away. The broad one (t-3 to t+3) lives: +0.50%, t=3.15. 📊 seasonalpha.ai #Stocks #Seasonality #SeasonAlpha

#### Interne Verlinkung
- /en/tdom-analyse (compute turn-of-month yourself)
- /en/monatswechsel (month-boundary seasonality in detail)
- Blog: Google in July (related seasonality topic)

#### Content-Ideen (Folgeartikel)
- "Month boundary in DAX and Dow: where the effect lives, where it doesn't"
- "Why Japan is the exception: turn-of-the-month in the Nikkei"
- "Calendar effects and transaction costs: what's left of the edge"
-->

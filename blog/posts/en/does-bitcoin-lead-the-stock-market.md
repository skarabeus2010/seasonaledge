---
title: "Does Bitcoin Lead the Stock Market? 12 Years and 3,020 Trading Days"
seo_title: "Does Bitcoin Lead the Stock Market? 12 Years of Data"
slug: does-bitcoin-lead-the-stock-market
de_slug: laeuft-bitcoin-dem-aktienmarkt-voraus
date: 2026-09-21
category: education
tags: [bitcoin, correlation, spy, crypto, lead-lag, risk-appetite]
description: "Does Bitcoin lead the stock market? Twelve years of data show the link is same-day. Only very large crypto rallies leave a measurable trace in SPY."
ticker: BTC-USD
status: published
---

<!--
Keyword-Plan:
- Main keyword: does Bitcoin lead the stock market
- Secondary: Bitcoin leading indicator stocks, Bitcoin S&P 500 correlation, BTC SPY correlation, crypto equity correlation, lead-lag analysis Bitcoin, Bitcoin risk appetite, Ether S&P 500
- LSI: daily returns, lag, significance, p-value, base rate, hit rate, event study, risk-on, random band
-->

## The claim you see everywhere

"Bitcoin is the leading indicator for risk appetite — crypto turns first, equities follow." The line shows up in financial media, on X and in every other market comment. It is testable, because it makes a specific prediction: what Bitcoin does today should show up in the S&P 500 tomorrow.

We measured exactly that. If Bitcoin leads the stock market, it has to appear in lagged return series — and in what equities do after large crypto moves.

## The data

The study covers **3,020 shared trading days** from 17 September 2014 to 21 September 2026, using daily closes. On the crypto side: BTC-USD and ETH-USD (from 9 November 2017). On the equity side: the ETFs SPY, QQQ and DIA. Every number below refers to SPY unless stated otherwise.

Two things were calculated separately. First, the correlation of daily returns at different lags: lag 0 means the same trading day, lag +1 means Bitcoin today against equities tomorrow. Second, an event study: what does SPY do in the weeks after a clearly defined crypto rally, compared with what it does anyway, with no signal at all?

## The link sits on the same day

![Correlation of daily BTC-USD returns against SPY by lag in trading days across three windows: flat before 2019, a sharp spike at lag 0 between +0.36 and +0.42 from 2020 onwards, and essentially nothing at lag +1](laeuft-bitcoin-dem-aktienmarkt-voraus/1_korrelation_lag.png)

The curve has exactly one peak, and it sits at lag 0. In 2020–2021 the correlation there is **+0.36**, in 2022–2023 **+0.45**, and from 2024 to today **+0.38**. The chart merges the two more recent windows and shows **+0.42**.

To the right of the peak everything collapses. At lag +1, Bitcoin today against SPY tomorrow, practically nothing is left; in 2020–2021 the value is even slightly negative at **−0.185**. This is where forecasting power would have to appear. It is empty.

The grey line carries a third result: before 2019 the same-day correlation was **+0.017**. There was no link at all. It emerged in 2020, alongside institutional crypto adoption and a shared dependence on liquidity and rate expectations.

### Why co-movement is not a forecast

A same-day correlation of +0.42 means that on days when Bitcoin rallies hard, the S&P 500 usually rallies too. But anyone who knows Bitcoin's return for the day already knows the equity return for that same day. There is nothing tradable in it.

Trading hours do not help. Bitcoin trades around the clock and closes at 00:00 UTC; the ETF close falls at 20:00 or 21:00 UTC. The two "same" days overlap without being identical. That is why the overlapping day is left out of the event study: including it would price in information that was not available at the time of the trade.

## The 5 percent rule does not hold up

The most common rule of thumb says a Bitcoin gain of roughly 5 % over two weeks signals strength in equities. Over twelve years there were **56 such cases**.

SPY afterwards: **+0.78 %** after three weeks (p = 0.857) and **+1.12 %** after four weeks (p = 0.947). With no signal at all, the market delivers **+0.85 %** and **+1.14 %** over the same horizons. The signal lands marginally below average, and the p-values sit far beyond any significance threshold.

The p-value says how often a randomly chosen window produces a result at least this striking. At p = 0.857 that is roughly six times out of seven.

Ether gives the same picture. From 5 % over ten trading days (n = 40), SPY reaches **+1.01 %** after three weeks (p = 0.898) and **+1.56 %** after four weeks (p = 0.595). Nothing there.

## Something survives at the large moves

Raising the threshold changes the picture.

![Bar chart: SPY three weeks after a crypto rally, by threshold of 3, 5, 10 and 20 percent, split into Bitcoin and Ether, with p-values below the bars — from 10 percent upwards the bars sit clearly above the market base rate of +0.85 percent](laeuft-bitcoin-dem-aktienmarkt-voraus/3_staerke_btc_eth.png)

| Signal | n | SPY after 3 weeks | p | SPY after 4 weeks | p |
|---|---:|---:|---:|---:|---:|
| BTC ≥ 5 % | 56 | +0.78 % | 0.857 | +1.12 % | 0.947 |
| BTC ≥ 10 % | 47 | **+2.06 %** | 0.022 | **+2.52 %** | 0.024 |
| BTC ≥ 20 % | 30 | **+2.29 %** | 0.027 | **+2.57 %** | 0.050 |
| ETH ≥ 5 % | 40 | +1.01 % | 0.898 | +1.56 % | 0.595 |
| ETH ≥ 20 % | 25 | **+2.85 %** | 0.020 | **+3.63 %** | 0.011 |
| Base rate, no signal | — | +0.85 % | — | +1.14 % | — |

After a crypto gain of 10 % over ten trading days, SPY stands at **+2.06 %** three weeks later instead of the usual +0.85 %, with p = 0.022. From 20 % it is **+2.29 %** (p = 0.027).

The four-week figure at the 20 % threshold is the weakest point in the series: **+2.57 %** at **p = 0.050**, sitting exactly on the usual significance threshold. A value right on the line proves nothing; it only just keeps its shape. At this threshold the three-week figure carries weight, while the four-week figure stays a borderline case.

Ether matters more here because it is an independent cross-check: different coin, different sample period, different event days. From 20 %, SPY reaches **+2.85 %** after three weeks (p = 0.020) and **+3.63 %** after four weeks (p = 0.011). Two separate series lighting up at the same point is the strongest argument against pure noise.

The chart also shows where the cross-check breaks: at the 10 % threshold Ether does **not** follow the pattern (+0.72 %, p = 0.754). Both only move together from 20 % upwards.

The next day shows nothing and one week shows little. The difference only becomes visible after three to four weeks. Anyone looking for a daily indicator in crypto is looking at the wrong horizon.

## 12 March 2020

One test in the event study initially looked like a direct hit. After a sharp Bitcoin drop (defined via standard deviation, n = 10), SPY gained **+1.29 % the next day**, highly significant, with a hit rate of 90 %.

Nine out of ten cases correct reads convincingly. One of those ten days, however, is **12 March 2020**, the COVID low. That single day contributes **+8.55 percentage points** on its own.

Without it, **+0.49 %** remains, and the significance is gone.

![Two SPY event paths around the event, left after a Bitcoin rally (n = 12), right after a Bitcoin drop (n = 10), each with the 5th-to-95th percentile band from 2,000 randomly shifted event dates — the average path never leaves the band](laeuft-bitcoin-dem-aktienmarkt-voraus/2_ereignispfad.png)

The chart shows the same thing visually. The yellow path is the average SPY course from ten trading days before to 30 trading days after the event, normalised to the event day. The blue band is the 5th-to-95th percentile from 2,000 randomly shifted event dates: the corridor any arbitrary window lands in. Both paths stay inside it. After a rally SPY runs along the upper edge, after a drop it oscillates around zero, in both cases within what chance produces.

With ten events, a single day can carry the whole result. That is why the case count sits next to every number in the tables above.

## Limits of this study

**The threshold was not set in advance.** That 10 % and 20 % work while 5 % does not came out of trying several cut-offs. Test enough thresholds and you almost always find one that looks significant. The result is exploratory and waits for confirmation on data that does not exist yet.

**The p-values are calculated the strict way.** A first pass tested one-sided and picked the direction only after looking at the result, which halves the p-value artificially. It also omitted the plus-one correction, so a randomisation over 2,000 shifts could report "p = 0.000" although the smallest value it can represent is 1/2001. Every number here comes from the corrected calculation, two-sided and with plus-one, which makes the p-values roughly twice as large. A result that survives that tightening is worth more than one that depended on it: Ether at the 20 % threshold holds at p = 0.020 and p = 0.011, while Bitcoin after four weeks slips onto the line.

**The hit rate does not move.** It runs at around 65 % in the significant cases, against a market base rate of 64.4 % over the same horizon. The extra return comes from a handful of large cases, not from winning more often. For a trade that means the same probability of being right, with a fatter right tail.

**The samples are small.** Thirty Bitcoin cases in twelve years, 25 Ether cases in nine. Very large crypto rallies are rare, which gives individual market phases considerable weight.

**Sequence is not causation.** Both markets hang on the same risk appetite. One plausible reading: a 20 % jump in Bitcoin marks a shift in the liquidity regime that works through equities more slowly. The sequence is measurable; the cause is not.

**These are daily closes.** Anything happening inside a session is invisible, and the overlapping trading day stays out for the reason given above.

## What follows from this

The opening question is answered: Bitcoin does not lead the stock market in the sense that yesterday's crypto move flags today's equity move. The link sits on the same day, and it has only existed since 2020.

What remains is a narrow result in the tail of the distribution, and that tail is rarely reached. For day-to-day market watching, Bitcoin therefore works mainly as a state gauge: a crypto market that adds 20 % in two weeks describes a level of risk appetite that historically still carried into equities for a few weeks. That is context for judgement, not an entry point.

Related questions can be checked directly on SeasonAlpha: the [risk cycle](/en/risikozyklus) shows risk appetite across the calendar year, [intermarket shocks](/en/intermarket-shocks) deals with transmission between markets, and the [seasonal scanner](/en/scanner) shows which tickers currently sit in an unusual calendar window.

## Conclusion

Across 3,020 shared trading days since 2014, the correlation between Bitcoin and SPY is highest at lag 0 (+0.36 to +0.45 depending on the window) and essentially zero at a one-day lead. Before 2019 it stood at +0.017.

The popular 5 % rule fails: +0.78 % after three weeks against a base rate of +0.85 %. Only from 10 % (+2.06 %, p = 0.022) and 20 % (+2.29 %, p = 0.027) does the result separate from chance, independently confirmed by Ether from 20 % with +2.85 % (p = 0.020). After four weeks, Bitcoin at the 20 % threshold sits exactly on the significance line at p = 0.050 and does not count as established.

**Not a signal:** the threshold was chosen after the fact, the hit rate stays at market level, and the samples are small. This is a measurement, not a trading rule. Run your own periods and tickers on [seasonalpha.ai](https://seasonalpha.ai).

## Frequently asked questions

### Does Bitcoin lead the stock market?

Across 3,020 shared trading days since 2014, no. The correlation of daily returns peaks at lag 0 (+0.36 to +0.45 since 2020) and drops to essentially zero at a one-day lead, reaching −0.185 in 2020–2021. A lead only appears after very large crypto rallies, and then only over three to four weeks.

### How strongly are Bitcoin and the S&P 500 correlated?

On the same trading day: +0.36 (2020–2021), +0.45 (2022–2023) and +0.38 (2024–2026). Before 2019 the correlation was +0.017, so there was no link. It emerged in 2020.

### Is a 5 percent Bitcoin rally a useful signal for equities?

Not according to this data. Across 56 cases, SPY gained +0.78 % over the following three weeks (p = 0.857), while the market average with no signal at all is +0.85 %. The signal landed marginally below average.

### Does that also hold for Ether at large rallies?

From 20 % it does: SPY reached +2.85 % after three weeks (p = 0.020) and +3.63 % after four weeks (p = 0.011), across 25 cases. At the 10 % threshold, though, Ether does not follow the Bitcoin pattern (+0.72 %, p = 0.754).

### Why was 12 March 2020 removed from one calculation?

Because it carried the result on its own. After a sharp Bitcoin drop, SPY rose an average of +1.29 % the next day, highly significant at a 90 % hit rate. With only ten events, the COVID low contributed +8.55 percentage points of that. Without that day, +0.49 % remains, and the value is no longer significant.

<!--
#### Social Media Snippet

**LinkedIn:**
"Bitcoin leads the stock market" — we tested the claim across 3,020 shared trading days since 2014.
Result: the BTC/SPY correlation peaks at lag 0 (+0.36 to +0.45 since 2020) and is essentially zero at a one-day lead. Before 2019: +0.017, no link at all.
The popular 5 % rule fails (+0.78 % after three weeks against a +0.85 % base rate). Something survives only at the large moves: BTC ≥ +10 % → SPY +2.06 % (p = 0.022), ETH ≥ +20 % → +2.85 % (p = 0.020). Threshold chosen after the fact, hit rate unchanged at ~65 %.
Which crypto-equity rule would you like to see tested? → seasonalpha.ai

**Twitter/X:**
Does Bitcoin lead the stock market? 3,020 trading days say no.
BTC/SPY correlation same day +0.42, one day later ~0.
The 5 % rule: +0.78 % after 3 weeks — base rate +0.85 %.
Only from +10 % does it become measurable (+2.06 %, p=0.022).
#Bitcoin #Stocks #SeasonAlpha

#### Internal links
- /en/intermarket-shocks (transmission between markets)
- /en/risikozyklus (risk appetite across the year)
- /en/scanner (unusual calendar windows by ticker)
- /en/blog/monthly-10-strategy/ (method: base rates and decomposition)

#### Content ideas (follow-ups)
- "Does Bitcoin turn first over the weekend? The Monday test" — uses 24/7 trading as a genuine information lead
- "What switched the correlation on in 2020" — liquidity, rates and institutional adoption
- "Gold, copper, Bitcoin: which market really turns first?" — same lead-lag method across assets
-->

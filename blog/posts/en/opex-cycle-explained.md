---
title: "The OPEX Cycle: How Options Expiration Structures the Trading Month"
seo_title: "The OPEX Cycle Explained: The 4 Phases"
slug: opex-cycle-explained
de_slug: opex-zyklus-erklaert
date: 2026-08-08
author: SeasonAlpha Research
category: education
tags: [opex-cycle, options-expiration, vanna, charm, dealer-positioning, pre-opex-drift, post-opex, triple-witching, seasonality]
description: "The OPEX cycle explained: the four phases of options expiration, the pre-OPEX drift, the pin and the volatility window afterward — mechanics, not a signal."
ticker: SPY
status: published
---

<!--
Keyword-Plan:
- Primary keyword: OPEX cycle
- Secondary keywords: options expiration cycle, monthly options cycle, vanna charm cycle, pre-OPEX drift, post-OPEX window, options expiration explained, dealer hedging, delta hedging, Triple Witching
- Long-tail: what is the OPEX cycle, four phases of options expiration, why does the market rise before expiration, why does it get more volatile after expiration, how options expiration structures the trading month
- LSI: market maker, hedging, gamma exposure, implied volatility, open interest, third Friday, expiration day, normalized returns, pinning
- Search intent: readers want to understand the recurring monthly rhythm around options expiration — the mechanism behind it, not a single trading signal.
-->

## What the OPEX cycle is

The stock market has a hidden metronome that most investors never see: the **OPEX cycle**. OPEX stands for *option expiration* — the monthly expiry on the third Friday of each month. Around that date the same four-phase rhythm repeats and quietly structures the trading month: first the calm build-up, then an often quiet upward drift, the pin on expiration day, and finally a more directional, more volatile window afterward.

One thing up front: the OPEX cycle is **not a trading signal**, it is structural context. It explains *why* certain seasonal patterns exist in the first place. In this article we break the cycle into its four phases, use real dealer data to show where the hedging flows cluster — and we honestly name where the pattern breaks down.

## The four phases of the options expiration cycle

The cycle is a loop, not a straight line. After each expiration it starts over. The diagram below shows the four stations: **Options Positions Build**, **Options Hedges Build**, **Options Expire** and **Options Hedges Covered**.

![The OPEX cycle as a loop: options positions build, hedges build, options expire and hedges covered — the four phases around the third Friday](opex-zyklus-erklaert/opex-cycle.png)

Translated into everyday trading, the four phases look like this:

| Phase | What happens | Market effect |
|-------|--------------|---------------|
| 1. Positions Build | Investors and funds buy options — mostly index puts as insurance | Open interest builds up |
| 2. Hedges Build | Dealers/market makers hedge their risk in the underlying (delta hedging) | A "hedging cushion" forms |
| 3. Expire | Contracts expire on the 3rd Friday (Triple Witching in Mar/Jun/Sep/Dec) | Pin at strikes, large expiry |
| 4. Hedges Covered | The hedge is bought back, tied-up capital is freed | Post-OPEX window, more directional |

### Phase 1 — Positions Build

It all starts with demand. After the last expiration, institutions and funds build fresh options positions — mostly **index puts** as insurance against falling prices. Open interest at the coming expirations grows. This demand is the real root of the whole cycle: without investors buying protection, there would be nothing for dealers to hedge.

### Phase 2 — Hedges Build

The **dealers** — the market makers who sell those options — are now on the other side. They are net short puts and must neutralize their risk in the underlying. This is **delta hedging**: they sell stock or futures short to be protected against falling prices. Over the month a "hedging cushion" builds. As long as dealers hold that cushion, they often act as stabilizers — buying into weakness and selling into strength.

### Phase 3 — Options Expire

On the **third Friday** the contracts expire. Four times a year — in March, June, September and December — index options, index futures and single-stock options expire at the same time. This large expiration is called **Triple Witching**. On that day the largest amount of open interest matures, and prices tend to "cling" to the most important strike prices — so-called [pinning](/en/blog/pinning-call-wall-put-wall/).

### Phase 4 — Hedges Covered

Once the contracts have expired, the dealer no longer needs the hedge. They **unwind the hedging cushion** and buy back the short protection. Tied-up capital is freed — and with the stabilizing cushion gone, the market loses part of its "brake." This is exactly where the cycle starts over, while market behavior noticeably changes.

## Why this becomes a monthly rhythm

These four phases produce three well-known patterns that shape the trading month.

### The calm upward drift before expiration

The hedging cushion from Phase 2 is not static — it shrinks into expiration. Two "Greeks" drive that:

- **Charm (time decay):** As expiration approaches, the delta of out-of-the-money puts falls. The dealer needs less short hedge and **buys stock back**.
- **Vanna (volatility):** If the market stays calm, implied volatility declines. That too shrinks the put delta — the dealer covers as well.

Both forces push in the same direction: a mechanical, often quiet **buying pressure into OPEX week**. This is the well-known pre-OPEX drift. We dissected the specific opening jump on the third Friday — averaging roughly +18.5 basis points over 2003–2021 — in a dedicated study on the [Third-Friday effect](/en/blog/opex-effect-sp500-third-friday-drift/).

### The pin on expiration day

On expiration day itself it is not direction that dominates but attraction. Where a lot of open interest sits at a strike price, the hedging flows keep pulling the price back toward that strike — the market "pins." This is not folklore but documented in academic research (see below).

### The post-OPEX volatility window

When the hedging cushion falls away in Phase 4, the stabilizing effect of the dealers disappears. The market becomes more directional and more prone to larger moves — the notorious post-OPEX weakness or, more neutrally, the **post-OPEX volatility window**. The calm drift *into* expiration and the higher nervousness *afterward* are two sides of the same mechanic.

## What the data shows

Where in the calendar do the hedging flows actually cluster? The chart below shows the **charm exposure of SPY by expiry** — how strongly the dealer hedge at each expiration shifts each day from time decay alone.

![SPY — charm exposure by expiry: the largest time-decay-driven hedging flows cluster at the monthly expirations](opex-zyklus-erklaert/chart-charm-by-term-spy.png)

The picture is clear: by far the largest bar sits on the **next monthly expiration (August 21)** — the third Friday. The second largest is the **September date (September 18)**, the next Triple Witching. The many smaller dates in between are barely visible. This concentration is the heart of the cycle: time decay forces dealers to adjust not evenly, but **bundled around the big expiration days**. That is the mechanical engine behind the pre-OPEX drift.

Two caveats are mandatory. First, this is a **snapshot** from end-of-day options data (as of August 8, 2026), not an average over many months. Second, the dealer sign is based on a **simplified heuristic** (long calls / short puts), not on real dealer books. The chart shows the *structure* of the hedging flows, not a trading signal.

## The academic grounding

The OPEX cycle is not just practitioner folklore. Several of its building blocks are peer-reviewed:

- **Ni, Pearson & Poteshman (2005), *Journal of Financial Economics*** — the classic paper on **pinning**: closing prices of optioned single stocks cluster at strike prices on expiration day; returns were shifted by roughly 16.5 basis points on average. This underpins Phase 3.
- **Barbon & Buraschi (2021)** — describe **gamma fragility**: how the sign of dealer positioning changes the stability of the market. This explains why the volatility window opens after expiration (Phase 4), once the stabilizing gamma cushion falls away.
- **Baltussen, Terstegge & Whelan (2024)** — the Third-Friday effect linked above: the measurable opening jump on expiration day, attributed to charm-driven hedging.

One distinction matters: pinning and the Third-Friday jump are effects documented in finance journals. The exact size of the **pre-OPEX drift** and the **post-OPEX weakness**, by contrast, depends more heavily on the market regime and belongs more to well-supported practitioner knowledge than to hard statistics.

## Limits and counter-examples

An honest look at the cycle has to show the fault lines.

**Patterns fade once everyone knows them.** The better known the pre-OPEX drift becomes, the more it gets arbitraged away. A historical average is not a forecast for next Friday.

**Macro beats mechanics.** A Fed meeting, an inflation print or geopolitical news overrides the thin OPEX rhythm at any time. The cycle is a quiet background pattern, not a dominant force.

**Positioning flips the sign.** The cycle behaves differently depending on whether dealers are net long or short gamma overall. In a [long-gamma regime](/en/blog/dealer-positioning-gamma-vanna-charm/) they dampen moves; in a short-gamma regime they amplify them — the same calendar date can act very differently.

**We work with daily closing prices.** SeasonAlpha uses normalized close-to-close returns (each year rebased to 100). We cannot replicate the opening jump on expiration day one-to-one — we show the structure of the flows and the seasonal frame, not the intraday jump itself.

## How to use the cycle on SeasonAlpha

The real value lies in **understanding**, not in clicking "buy." Anyone who knows the cycle frames market moves better: a calm upward phase before expiration is rarely a strong buy signal, and a more nervous window afterward is rarely the start of a crash — both are often simply the OPEX rhythm.

Concretely, you'll find the building blocks here: the exchange-accurate **calendar** for OPEX, Triple Witching and VIXpiration is on the [Options Expiration](/en/opex) page. The current **gamma, vanna and charm metrics** — i.e. which phase of the cycle dealers are in right now — are on [Dealer Positioning](/en/dealer-positioning). And the seasonal patterns that emerge are visible via the weekday and monthly-cycle pages. That is how SeasonAlpha marries the calendar with dealer flows: you don't just see *that* a pattern exists, you understand the structural cause behind it.

## Conclusion

The OPEX cycle is the stock market's hidden monthly metronome: positions build, dealers hedge, the contracts expire on the third Friday, and the hedge is unwound. From this come the calm pre-OPEX drift, the pin on expiration day, and the more directional window afterward.

The cycle explains *why* — it is context, not a signal. Patterns weaken, macro overrides them, and the sign of dealer positioning flips the effect. Explore the [options expiration calendar](/en/opex) and [Dealer Positioning](/en/dealer-positioning) yourself on **seasonalpha.ai** — and see which phase of the cycle the market is in right now.

## Frequently Asked Questions

### What is the OPEX cycle in simple terms?

The OPEX cycle is the recurring four-phase rhythm around monthly options expiration (the third Friday). Investors build options positions, dealers hedge in the underlying, the contracts expire on expiration day, and afterward the hedge is unwound. From this loop come the typical patterns: the calm upward drift before expiration and a more volatile window afterward.

### Why is the market often calm and slightly rising before options expiration?

Because dealers have to buy back their short hedge into expiration. Time decay (charm) and falling volatility (vanna) shrink the delta of the puts they sold — both force them to buy in the underlying. This mechanical buying pressure creates the quiet pre-OPEX drift. It is a side effect of hedging, not a view by dealers on market direction.

### Why does it often get more volatile after expiration?

After expiration, dealers unwind their hedging cushion. With it goes the stabilizing effect that had kept the market in tight ranges. The market becomes more directional and more prone to larger moves — the post-OPEX volatility window. Barbon and Buraschi (2021) describe this gamma fragility academically.

### Can I use the OPEX cycle as a trading strategy?

The cycle is structural context, not a trading signal and not investment advice. The patterns are thin, weaken once they become known, and are overridden by macro events at any time. Its value lies in framing market moves better — not in mechanically deriving buy or sell decisions from it.

<!--
#### Social Media Snippet

**LinkedIn:** The stock market has a hidden monthly metronome: the OPEX cycle. Four phases around options expiration on the third Friday — positions build, hedges build, expire, hedges covered. From this come three well-known patterns: the calm pre-OPEX drift (charm & vanna force dealers to buy back their hedge), the pin on expiration day (Ni/Pearson/Poteshman 2005) and the more directional volatility window afterward (Barbon/Buraschi 2021, gamma fragility). Our latest charm data shows it clearly: the hedging flows cluster at the monthly expirations. Important: this is mechanics and context, not a trading signal. Which phase is the market in right now? https://seasonalpha.ai/en/dealer-positioning

**Twitter/X:** The OPEX cycle: 4 phases around options expiration → pre-OPEX drift (charm/vanna), pin on expiration day, volatility window afterward. Our charm data shows hedging flows cluster at the monthly expiries. Mechanics, not a signal. seasonalpha.ai/en/dealer-positioning #OPEX #Options #SP500

#### Interne Verlinkung
- /en/opex (options expiration calendar — direct feature)
- /en/dealer-positioning (gamma/vanna/charm live — current phase of the cycle)
- /en/blog/opex-effect-sp500-third-friday-drift/ (the specific Third-Friday jump, +18.5 bps)
- /en/blog/dealer-positioning-gamma-vanna-charm/ (long vs. short gamma regime, mechanism)
- /en/blog/pinning-call-wall-put-wall/ (pinning on expiration day)
- /en/vixpiration (the second expiration cycle around the VIX)

#### Content-Ideen (Folgeartikel)
- "Post-OPEX weakness: what really happens in the week after expiration (data study)"
- "Long vs. short gamma: how the dealer sign reverses the same calendar day"
- "VIXpiration: the second expiration cycle almost no one knows"
-->

# OPTIONS.md — Dealer-Positioning-Greeks (GEX / Vanna / Charm)

> Stand: 2026-07-10 · Owner-Baustein „Options-Teil". Formeln per Finite-Differenzen bewiesen
> (`compute_gamma_exposure.py --self-test`). Konventionen gegen SpotGamma/SqueezeMetrics/MenthorQ verifiziert.

## Warum das zu SeasonAlpha passt

SeasonAlpha besitzt bereits den **Optionsverfalls-Kalender** (`/opex` Triple Witching 3. Freitag, `/vixpiration`,
Notenbank-/Earnings-Termine). **Gamma/Vanna/Charm sind der Mechanismus DAHINTER** — sie erklären *kausal*, warum
die OPEX-Saisonalität existiert (Pre-OPEX-Drift, Pinning, Post-OPEX-Vola). Damit wird aus „Muster" ein „Warum" =
Differenzierung + Content-/SEO-/Video-Hebel. Kein neues Produkt, sondern Vertiefung des Bestehenden.

## Kennzahlen

| Kennzahl | Definition | Deutung |
|---|---|---|
| **net-GEX** | Σ sign·Γ·OI·100·S²·0,01 ($ pro 1 % Move) | **>0 long-Gamma** (Dealer dämpfen, Mean-Reversion/Pinning) · **<0 short-Gamma** (verstärken, Trend/Vola) |
| **Zero-Gamma-Flip** | Spot, an dem net-GEX das Vorzeichen wechselt (Spot-Sweep, sticky-strike) | Regimegrenze; Spot nahe Flip → Regime kann kippen |
| **Call-Wall** | Strike ≥ Spot mit max. positivem Netto-Gamma | Widerstand / Pinning oben (Referenz, keine Garantie) |
| **Put-Wall** | Strike ≤ Spot mit max. negativem Netto-Gamma | Support / Pinning unten |
| **Absolute-Gamma** | Strike mit max. \|Netto-Gamma\| | magnetischster Pin insgesamt |
| **net-Vanna** | Σ sign·Vanna·OI·100·S·0,01 ($-Delta pro 1 Vol-Punkt) | Vola-getriebene Hedging-Flows |
| **net-Charm** | Σ sign·Charm·OI·100·S/365 ($-Delta-Drift pro Kalendertag) | Zeit-getriebene Hedging-Flows (OPEX-Bid) |

`sign = +1 Call, −1 Put` (naive Dealer-Konvention, s. u.).

## Black-Scholes-Formeln (mit Dividendenrendite q)

Mit `d1 = (ln(S/K)+(r−q+σ²/2)T)/(σ√T)`, `d2 = d1−σ√T`, `φ` = Normal-PDF, `N` = CDF:

```
Γ     = e^(−qT)·φ(d1)/(S·σ√T)                                   (gleich für Call/Put)
Vanna = ∂Δ/∂σ = −e^(−qT)·φ(d1)·d2/σ                             (gleich für Call/Put)
Charm = ∂Δ/∂t  (Kalenderzeit vorwärts, per Jahr → /365 für Tages-Charm):
  Call: q·e^(−qT)·N(d1)  − e^(−qT)·φ(d1)·(2(r−q)T − d2·σ√T)/(2T·σ√T)
  Put: −q·e^(−qT)·N(−d1) − e^(−qT)·φ(d1)·(2(r−q)T − d2·σ√T)/(2T·σ√T)
```
Der große Term ist für Call/Put identisch; nur der q·N-Term unterscheidet sich (bei q=0 → Charm_call = Charm_put).
**Verifiziert:** `--self-test` vergleicht alle drei Greeks gegen zentrale Finite-Differenzen von Δ (rel. Fehler < 1e-4).

## Sign-Konvention + EHRLICHKEIT (YMYL)

Wir nutzen die **naive Konvention**: Dealer **long Calls / short Puts** → Call-Gamma +, Put-Gamma −
(Herkunft: Retail/Institutionelle kaufen Index-Puts als Hedge, überschreiben Calls). **Das ist eine Heuristik.**

- **SpotGamma & SqueezeMetrics weichen ab:** proprietäre **DDOI-/Inventory-Modelle** *schätzen* die echte Dealer-Seite
  je Kontrakt aus Trade-Direction, beziehen **0DTE + Intraday** ein. Offenes OI „does not identify dealer vs customer".
- Unsere naive-Regel ist als **erste Näherung für Index-GEX robust** (Put-Buying/Call-Overwriting dominiert real),
  unterschätzt aber 0DTE, atypischen Einzeltitel-Flow und kann bei Regimewechsel das Vorzeichen einzelner Strikes verfehlen.
- **Konsequenz für die Kommunikation:** IMMER als „naive Heuristik, EOD-Daten, keine echten Dealer-Bücher, kein
  Kauf/Verkauf-Signal, Walls = Referenzen keine Barrieren" kennzeichnen. Unsere Zahlen ≠ SpotGammas Zahlen.

## Vanna/Charm-Flows in die Monats-OPEX (Karsan / MenthorQ)

- **Pre-OPEX-Drift (aufwärts):** Dealer netto short Puts. Zeitverfall lässt OTM-Put-Delta schrumpfen (**Charm**);
  in ruhigem Tape fällt die IV (**Vanna**) → beides zwingt Dealer, Short-Underlying-Hedges zurückzukaufen →
  mechanischer Aufwärts-Bid in den 3. Freitag (Beschleunigung Do/Fr).
- **Post-OPEX-Vola:** beim Verfall verschwindet die stabilisierende Positionierung → Hedge-Polster weg →
  Markt richtungsoffener/volatiler. **Daily-Charm (÷365) ist dafür ausreichend** (nur 0DTE bräuchte feiner).

## Datenquellen + Reichweite

| Domäne | Weg | Status |
|---|---|---|
| **US-Aktien/ETFs/Index** | Yahoo `v7/finance/options` (Crumb-Session wie `fetch_event_data`), EOD-OI+IV | ✅ läuft |
| **Crypto (BTC/ETH)** | **Deribit** (freie API, volle Chain **inkl. Greeks** + OI) | ⏳ zu bauen (on-brand) |
| **DAX-Index / dt. Aktien** | Yahoo liefert für `^GDAXI`/`.DE` **NICHTS** (live getestet: leer). Echtes ODAX/Eurex-GEX (Strike-Level) nur mit **Bezahl-Daten** (IVolatility, Barchart-DAX-Futures-Options, Deutsche-Börse T7/MDS) | ⚠️ nur US-ETF-Proxy (EWG dünn/GEX≈0, FEZ=EURO-STOXX-50 liquider) — mit dickem Proxy-Disclaimer, oder Budget |

**Yahoo-Options-Endpoint bedient nur US-gelistete Underlyings (OCC-Börsen).** Alle `.DE`-Suffixe + `^GDAXI` → leere Chain.

## Universum

- **Kern (Index-GEX, am belastbarsten):** SPY, QQQ, IWM, DIA + `^SPX`-Proxy.
- **Mag7 + High-Options-Aktien:** AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA, NOW, WMT, PLTR, NFLX, LLY, AVGO, ORCL, ASML, ARM.
- **SeasonAlpha-ETFs (40, `US-ETF`):** SPY/QQQ/IWM/DIA/TLT/GLD/SLV/SMH/SOXX/XLF/XLK/XLE/GDX/IBIT/ETHA/… (dünne wie CNXT/XSD/XHB → GEX schwach, vorsichtig).
- **Einzelaktien-GEX ist verrauschter** als Index-GEX (Dealer weniger dominant) → vorsichtiger interpretieren.

## Tooling

```
# Greeks beweisen (Finite-Differenzen)
PYTHONUTF8=1 py -3.14 scripts/compute_gamma_exposure.py --self-test
# Einzeln / Batch
PYTHONUTF8=1 py -3.14 scripts/compute_gamma_exposure.py --ticker SPY --max-days 90
PYTHONUTF8=1 py -3.14 scripts/compute_gamma_exposure.py --tickers SPY,QQQ,NVDA --max-days 45
```
Output: `landing/data/gex_<T>.json` (+ `gex_summary.json` im Batch). Auswertung/Interpretation: Subagent
**`options-flow-analyst`** (READ-ONLY, verknüpft mit OPEX/VIX/Earnings). `--out-dir` für separate Panels.

## Grenzen / Caveats

- **EOD, nicht intraday** (Yahoo-OI wird morgens aktualisiert). Intraday/0DTE-Präzision braucht Paid-Feed (Polygon/Tradier/Theta).
- **Naive Dealer-Vorzeichen** (s. o.) — nicht SpotGammas Inventory-Modell.
- **Sticky-strike** beim Flip-Sweep (jeder Strike behält IV) — theoretisch schwächer als sticky-delta.
- **Yahoo-IV** kann bei illiquiden Strikes verrauscht sein; dünne Namen (thin OI) → GEX nahe 0.

## Roadmap

1. **Batch-Cron** (täglich EOD) → `landing/data/gex_*.json` für Kern + Mag7 + ETFs.
2. **Deribit-Connector** (BTC/ETH-GEX, gratis Greeks).
3. **`/gamma`-Frontend** (Regime-Ampel + Flip + Walls) bzw. Overlay auf `/opex` + `/vixpiration`.
4. **Empirie-Loop:** korreliert unser gemessener Pre-OPEX-Drift mit hohem net-GEX / Charm-Intensität?
5. **Content/SEO/Video:** „Gamma-Exposure erklärt", „OPEX-Pinning / Max Pain", „0DTE-Gamma".

## Quellen

- SqueezeMetrics GEX+ Guide (DDOI, VEX, Einheiten): https://squeezemetrics.com/monitor/static/guide.pdf
- SpotGamma — GEX / Call Wall / Put Wall (Support-Center)
- MenthorQ — Vanna/Charm & Post-OPEX-Vola: https://menthorq.com/guide/why-markets-can-go-wild-after-options-expiration-vanna-and-charm-and-the-volatility-effect/
- Cem Karsan (The Derivative/RCM) — Vol-Curves & Vanna/Charm-Flows
- Macroption / Wikipedia „Greeks (finance)" — BS-Formeln (Gamma/Vanna/Charm mit q)

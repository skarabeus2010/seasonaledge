# Feature-Backlog: Optionen/Dealer-Papers → Website

- **Typ:** Feature-Ableitung aus `raw/papers/` (literatur-scout)
- **Datum:** 2026-07-10
- **Vorgänger (nicht doppeln):** `2026-07-10_papers-inventar-optionen.md`, `…_flows-auf-die-seite-produktspec.md`, `…_dealer-positioning-akademische-fundierung.md`

## Neuer akademischer Batch (klassifiziert)
- `01_squeezemetrics_gex_whitepaper` (gelesen) — GEX-Quartil → Folgetages-Varianz; „GEX schlägt VIX bei niedriger Vola".
- `02_squeezemetrics_implied_order_book` (gelesen) — GEX+VEX als Liquiditätskarte; DDOI = Dealer-Direction aus Transaktionsdaten (paid).
- `04_barbon_buraschi_gamma_fragility` (peer-adjacent) — neg. Gamma → Intraday-Momentum/Flash-Crashes, pos → Reversion; transitorisch ≤2 Tage.
- `05_baltussen_2021` (JFE) — Rest-of-day → Last-30-min-Momentum; **reiner Intraday-Effekt** (paid-Feed nötig).
- `09_avellaneda_lipkin_pinning` — Pinning an High-OI-Strikes; Ni/Pearson/Poteshman + Garleanu/Pedersen/Poteshman = kausale Fundierung.
- `08_amaya_cboe_0dte` — 0DTE-OMM-Gamma-Impact (proprietäre Cboe-Daten → nur Content).
- `20-27 Vanna-Volga/Greeks` — math. Fundierung; `27_delvalle` 3rd-Order-Greeks (Speed/Zomma/Color) optional.
- Yardeni #1-6 — Makro (Buybacks stützt Flows-Panel B, Yield-Curve = Rezessions-Kontext), kein Options-Feature.
- Unlesbar (Konvertierung nötig): DOCX/PPTX/XLSX/webp/jfif. `DealerPositioningOptions.pdf` == Volland-Whitepaper (Duplikat).

## Top-6 NEUE Features (Aufwand/Nutzen)
1. **N1 · GEX-Quartil → erwartete Tagesrange („GEX schlägt VIX")** — M. Netz-GEX-Historie in Quartile → realisierte Folgetages-Std je Bucket, vs. VIX. **Die** reproduzierbare Daten-Studie (validiert Regime-Ampel empirisch + Digital-PR/Backlink). → `/dealer-positioning` + Blog. Quelle: SqueezeMetrics GEX-WP.
2. **N2 · Gamma-Fragilitäts-Breite** — M. % des optionsfähigen US-Universums mit **negativem** Netz-GEX (Breadth, nicht Level). Rechnen GEX schon pro Ticker → Vorzeichen aggregieren. → `crash-fruehwarnung`. Quelle: Barbon/Buraschi.
3. **N3 · Pinning-Distanz / Pin-Zone** — S-M. Abstand Spot ↔ Max-OI/Max-Gamma-Strike um OPEX + Flag. Reine EOD-OI (haben wir). → `/opex`. Quelle: Avellaneda/Lipkin, Ni/Pearson/Poteshman.
4. **N4 · Gamma-Regime → Häufigkeit großer Down-Tage** — M. Bedingte Frequenz ≥−2%-Tage in neg. vs pos. Gamma-Regime (GEX-Historie + ^GSPC). Macht Crash-Ampel empirisch belastbar. Quelle: Barbon/Buraschi + Ambrus.
5. **N5 · „Liquiditäts-Karte"** — S. Per-Strike-GEX umgerahmt (grün=Support unter Spot, rot=destabilisierend). Chart-Variante auf `/dealer-positioning`. **Ehrlich:** naive Heuristik, NICHT DDOI/„Order Book". Quelle: SqueezeMetrics Implied Order Book.
6. **N6 · Dark-Pool-Short-Volume-Proxy (DIX-ähnlich)** — M-L. **FINRA Reg-SHO Daily Short Volume** (frei) als Proxy. Neuer `/flows`-Panel. Klar als Proxy labeln (echte DIX = proprietär).

## Ehrliche Daten-Grenzen (YMYL)
- Intraday-/0DTE-Paradigmen (Baltussen Last-30-min, Volland-0DTE, Amaya-OMM) = **paid** (Polygon/Tradier/Theta/Cboe). Nur Erklär-Content.
- DDOI/Implied-Order-Book (SqueezeMetrics) beruht auf Transaktionsdaten; wir haben nur OI → **naive Heuristik auf EOD-Yahoo**, kein Inventory-Modell.
- Barbon/Buraschi-Effekt ist intraday + transitorisch (≤2T) → nur Regime-Klassifikation + Häufigkeitsstatistik übernehmbar.
- DAX/`.DE` → keine Yahoo-Chain (nur US-gelistet; ETF-Proxy EWG/FEZ oder paid Eurex).
- Fremdnamen nie als Feature-Name (unsere Charts: „Gamma by Strike / Liquiditäts-Karte / Gamma-Fragilitäts-Breite").

## Quellen
- SqueezeMetrics GEX-Whitepaper · The Implied Order Book · Barbon & Buraschi „Gamma Fragility" · Baltussen et al. (JFE 2021) · Avellaneda-Kasyan-Lipkin (Pinning) · Amaya et al. (Cboe 0DTE).

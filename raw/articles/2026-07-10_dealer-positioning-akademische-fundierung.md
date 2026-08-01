# Dealer-Positioning: Akademische & Praktiker-Fundierung (E-E-A-T / YMYL-Trust)

> Quelle: Web-Recherche (WebSearch/WebFetch), erstellt 2026-08-01 · für `sa-ingest` + E-E-A-T-Content
> Ziel: Peer-reviewte / zitierfähige Literatur, die GEX/Vanna/Charm/Pinning/OPEX-Effekte **belegt** — damit unsere
> Options-Dealer-Positioning-Seiten (`/dealer-positioning`, GEX/Walls/Zero-Gamma, OPEX/VIX-Kalender) mit echten
> Zitaten (DOI/URL) statt Vendor-Marketing untermauert werden. **Peer-reviewed strikt von Vendor/Blog getrennt.**

## Kern-Erkenntnis vorab

Die Effekte, die unsere Engine schon berechnet (GEX-Vorzeichen → Vola-Regime, Call/Put-Walls, Zero-Gamma-Flip,
Vanna/Charm-Pre-OPEX-Flows, Pinning zu OPEX), sind **in Top-Finance-Journals dokumentiert** — JFE (Ni/Pearson/
Poteshman 2005, Golez/Jackwerth 2012), Working Papers von aktiven Akademikern (Barbon/Buraschi, Baltussen et al.).
Das ist der entscheidende YMYL-Trust-Hebel: Wir sind kein weiterer GEX-Vendor, sondern operationalisieren
**publizierte Mikrostruktur-Forschung**. Für jede Seite gibt es 1-2 zitierfähige Anker.

**Wichtige Abgrenzung:** SqueezeMetrics/SpotGamma/Kolanovic/Karsan sind **Praktiker-Quellen (Vendor/Sell-Side/Blog)**
— nützlich für Begriffsprägung und Framework, aber NICHT peer-reviewed. In einer Trust-Sektion als
"Praktiker-Ursprung" kennzeichnen, die **akademische Validierung** (Ni-P-P, Golez/Jackwerth, Barbon/Buraschi,
Baltussen et al., Amaya et al.) klar davon trennen.

---

## A. PEER-REVIEWED / AKADEMISCH (zitierfähig für YMYL)

### A1. Ni, Pearson & Poteshman (2005) — "Stock Price Clustering on Option Expiration Dates"
- **Journal:** Journal of Financial Economics 78(1), 49-87. **DOI:** 10.1016/j.jfineco.2004.08.005
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304405X05000577 · SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=519044
- **Kernbefund:** Zum OPEX-Verfall clustern Schlusskurse optionierter Aktien **an den Strike-Preisen** (Pinning).
  Aktienrenditen werden am Verfallstag um durchschn. ≥ 16,5 bps verschoben; aggregiert ~9 Mrd. $ Marktkapitalisierung.
  Ursachen: Hedge-Rebalancing der Market Maker + Manipulation durch Firm-Proprietary-Trader.
- **Stützt bei uns:** **DER kanonische Pinning-Beleg.** Untermauert unsere **Call/Put-Walls** und das Konzept
  "Kurs wird zu großen Strikes gezogen". Direkt zitierbar auf `/dealer-positioning` + jeder Wall-Erklärung + OPEX-Kalender-Tooltip.
- **Status:** ⭐ Peer-reviewed, Top-3-Journal. Höchste Zitier-Autorität.

### A2. Golez & Jackwerth (2012) — "Pinning in the S&P 500 Futures"
- **Journal:** Journal of Financial Economics 106(3), 566-585. **DOI:** 10.1016/j.jfineco.2012.06.010
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304405X12001365 · SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1664261
- **Kernbefund:** S&P-500-Futures werden am Verfall serieller Optionen **zum ATM-Strike gezogen** (Pinning) und
  unmittelbar vor Index-Options-Verfall vom (Cost-of-Carry-adjustierten) ATM **weggedrückt** (Anti-Cross-Pinning).
  Treiber: MM-Delta-Hedge-Rebalancing (Zeit-Decay der Hedges) + Rückverkauf/Early-Exercise von ITM-Optionen durch Retail.
  Verschiebung ≥ 115 Mio. $ Nominalwert je Verfallstag.
- **Stützt bei uns:** Erweitert Pinning von Einzelaktien auf **Index-Level** (SPX/ES) — genau unsere SPY/QQQ-Wall-Logik +
  Zero-Gamma. Zeigt, dass MM **netto short Optionen** sind und ihr Hedging den Kurs bewegt = unser GEX-Vorzeichen-Modell.
- **Status:** ⭐ Peer-reviewed, JFE. Zweiter Kern-Anker.

### A3. Barbon & Buraschi — "Gamma Fragility"
- **Typ:** Working Paper (Univ. St. Gallen / Imperial College), 2020/2021. **SSRN:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3725454
- **URL (Volltext):** https://www.alexandria.unisg.ch/entities/publication/b0c4de3d-74dd-4e62-b465-2d0337fe2904
- **Kernbefund:** Aggregierte Dealer-**Gamma-Imbalances** in illiquiden Märkten erklären Intraday-Momentum/Reversal und
  Markt-**Fragilität**. Negatives (positives) Ex-ante-Gamma × Illiquidität → Momentum (Reversal); Effekt stärker bei
  illiquidesten Underlyings. Distinkt von Informations- und Funding-Liquidity-Frictions.
- **Stützt bei uns:** **DER akademische Beleg für unser GEX-Vorzeichen-Regime** (short/neg. Gamma → Moves verstärkt/
  Momentum; long/pos. Gamma → Moves gedämpft/Reversal). Untermauert Zero-Gamma-Flip & "Gamma-Regime-Ampel".
- **Status:** ⭐ Working Paper von etablierten Akademikern (noch nicht final peer-reviewed, aber breit zitiert). Solide.

### A4. Baltussen, Terstegge & Whelan (2024) — "The Derivative Payoff Bias"
- **Typ:** Working Paper (Erasmus/Northern Trust, Copenhagen Business School, CUHK), Version Jan 2024; AFA-2025-Programm.
- **URL:** SSRN https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4562800 · AFA: https://afajof.org/management/viewp.php?n=98196
- **Kernbefund (verifizierte Zahlen aus PDF):** US-Index-Derivate settlen "a.m." am **3. Freitag** via Special Opening
  Quotation (SOQ). Über 2003-2021 übersteigt die SOQ den Vortagsschluss an 3. Freitagen im Schnitt um **18,5 bps**
  (t-Stat > 4,5); vor 2003 kein Effekt. Tent-shaped Reversal von Do-Close → Fr-Open, revertiert bis Fr-Mittag
  ("**Third Friday Price Spike**"). Futures/Call-Payoffs biased upward, Put-Payoffs downward. Geschätzter
  Wealth-Transfer **~4 Mrd. $/Jahr allein in SPX**. Stärker an Triple-Witching-Tagen. Mechanismus: MM-Inventory-
  Management (Charm) + mögliche Manipulation im illiquiden Overnight-Fenster.
- **Stützt bei uns:** Direkter Beleg für **Charm-getriebene OPEX-Drift** — buildbar als eigene Studie/Blog + Tooltip auf
  OPEX/Triple-Witching im Kalender. Konkrete, zitierfähige Zahl (18,5 bps, ~4 Mrd. $) für Content.
- **Status:** ⭐ Working Paper, hochrangige Autoren, AFA-akzeptiert. Sehr zitierfähig.

### A5. Baltussen, Da, Soebhag (& verwandt: "Hedging Demand and Market Intraday Momentum")
- **Typ:** "End-of-Day Reversal" WP (EFMA 2024) + "Hedging demand and market intraday momentum", JFE 2021 (verwandte Literatur).
- **URL:** https://academicweb.nd.edu/~zda/EOD.pdf · JFE-Verwandt: https://www.sciencedirect.com/science/article/abs/pii/S0304405X21001598
- **Kernbefund:** Gamma-Hedging-Demand rund um Index-Produkte treibt **Intraday-Momentum** (letzte 30 Min vor Close
  positiv durch Tages-Return prognostiziert, revertiert danach); je positiver das Netto-Gamma einer Aktie, desto mehr
  Intraday-Reversal, je negativer desto mehr Momentum. Stärker an OPEX-Tagen.
- **Stützt bei uns:** Bestätigt Cross-Sectional-Gamma-Effekt (unser Per-Ticker-GEX) und die OPEX-Verstärkung.
- **Status:** ⭐ Mix aus JFE-2021 (peer-reviewed) + WP. Sekundär-Anker.

### A6. Amaya, Garcia-Ares, Pearson & Vasquez (2025) — "0DTE Index Options and Market Volatility: How Large is Their Impact?"
- **Typ:** Working Paper (Wilfrid Laurier, ITAM, Univ. of Illinois/Notre Dame, Canadian Derivatives Institute), 25.01.2025.
  JEL G12/G13/G23/G24. Daten: Cboe SPX/SPXW-Trades (proprietär).
- **URL:** https://westernfinance-portal.org/viewpaper?n=950096 (verwandte 0DTE-Literatur) · Cboe-Research-Reihe.
- **Kernbefund:** Schätzt aus proprietären Trade-Daten die **aggregierte OMM-Position/Gamma** in 0DTE-SPX und den
  **maximalen** Impact des OMM-Gamma auf Index-Vola via Counterfactual-Simulation. Neil Pearson (= A1-Autor) bringt
  akademische Autorität in die 0DTE-Debatte.
- **Stützt bei uns:** Zitierfähiger, seriöser Gegenpol zu Vendor-0DTE-Hype für eine 0DTE/Marktstruktur-Sektion.
- **Status:** ⭐ Working Paper, Autor von A1 → glaubwürdig. (Cboe-eigene Studie "Much Ado About 0DTEs" ist Vendor → siehe B.)

---

## B. VENDOR / SELL-SIDE / PRAKTIKER-BLOG (NICHT peer-reviewed — als solche kennzeichnen)

### B1. SqueezeMetrics — "GEX / Gamma Exposure" White Paper (2016, rev. 2017)
- **URL:** https://squeezemetrics.com/monitor/static/guide.pdf
- **Rolle:** **Begriffsprägung "GEX".** Aggregiertes Dealer-Gamma; pos. GEX → stabilisierend (Dips kaufen/Rallies
  verkaufen, Low-Vol/Range), neg. GEX → verstärkend (in Declines verkaufen/in Rallies kaufen, größere Ranges).
- **Einordnung:** Vendor-White-Paper, **nicht peer-reviewed**. Für Begriff/Intuition zitieren, akademisch mit
  Barbon/Buraschi (A3) validieren. So kommunizieren: "Praktiker-Konzept (SqueezeMetrics 2016), akademisch bestätigt durch …".

### B2. SpotGamma — GEX / Vanna & Charm / Vol-Trigger / Walls (Primer)
- **URL:** https://spotgamma.com/gamma-exposure-gex/ · https://spotgamma.com/vanna-and-charm-explained/ · https://spotgamma.com/0dte-options-explained/
- **Rolle:** Retail-freundliche Definitionen (Call/Put-Wall, Zero-Gamma, Vol-Trigger). **Vendor.** Nur für Begriffs-Konsistenz.

### B3. Kolanovic (JPMorgan) — Vanna/Charm-Flows & "Volmageddon 2.0" / "Correlation Bubble"
- **URL:** https://www.newconstructs.com/wp-content/uploads/2010/10/JP-Morgan-and-Correlation (Correlation Bubble)
- **Rolle:** Sell-Side-Research, das Vanna/Charm-Dealer-Flows ("Vol-Reset-Rallies": fallende IV → Dealer kaufen Futures)
  in den Mainstream brachte. **Nicht peer-reviewed**, aber einflussreicher Praktiker-Ursprung des Vanna/Charm-Narrativs.

### B4. Cem Karsan (Kai Volatility) — Gamma/Vanna/Charm-Framework
- **URL:** https://www.rcmalternatives.com/2020/10/vol-curves-and-vanna-charm-with-cem-karsan-the-derivative/
- **Rolle:** Popularisierte das Vanna/Charm-Timing-Framework (Charm = ∂Δ/∂t zeit-getrieben; Vanna = ∂Δ/∂σ vola-getrieben)
  in Podcasts. **Praktiker/Interview**, keine Quelle für YMYL-Zitat — allenfalls als "Praktiker-Perspektive" nennen.

### B5. Ambrus Capital / Kris Sidial — "Changing Market Structure" (Reflexivität/Fragilität)
- Bereits im lokalen Papers-Inventar (`raw/papers/`). **Praktiker-White-Paper.** Fig. 7: "S&P während OPEX kaufen" → 3-J.-Backtest -15 %.
- **Rolle:** Reflexivitäts-/Liquidity-Cascade-Narrativ. Vendor/Praktiker, gut für Content, nicht als akademischer Anker.

### B6. Cboe — "Much Ado About 0DTEs" / Volatility Insights
- **URL:** https://www.cboe.com/insights/posts/volatility-insights-evaluating-the-market-impact-of-spx-0-dte-options
- **Rolle:** Cboe-eigene Analyse: MM-Gamma-Exposure ~170-670 Mio. $ (0,04-0,17 % der ~400 Mrd. $ täglicher ES-Liquidität)
  → 0DTE verstärken Moves **nicht** signifikant. **Börsenbetreiber = Interessenkonflikt (nicht neutral).** Neben A6 stellen.

---

## C. EMPFOHLENE 3-5 QUELLEN FÜR EINE YMYL-TRUST-SEKTION

Reihenfolge = Autorität. Diese explizit mit DOI/URL auf `/dealer-positioning` bzw. `/ueber-uns` (Methodik/E-E-A-T) setzen:

1. **Ni, Pearson & Poteshman (2005), JFE** — DOI 10.1016/j.jfineco.2004.08.005 → Pinning/Walls. *(Kern-Anker)*
2. **Golez & Jackwerth (2012), JFE** — DOI 10.1016/j.jfineco.2012.06.010 → Index-Pinning (SPX/ES). *(Kern-Anker)*
3. **Barbon & Buraschi, "Gamma Fragility"** — SSRN 3725454 → GEX-Vorzeichen/Fragilität. *(Regime-Anker)*
4. **Baltussen, Terstegge & Whelan (2024), "The Derivative Payoff Bias"** — SSRN 4562800 → Charm-OPEX-Drift, 18,5 bps. *(OPEX-Anker + Content)*
5. **Amaya, Garcia-Ares, Pearson & Vasquez (2025), "0DTE Index Options and Market Volatility"** → seriöse 0DTE-Fundierung. *(0DTE-Anker)*

**Formulierungs-Muster (Trust-Copy):** „Die von SeasonAlpha berechneten Gamma-Regime, Call/Put-Walls und Pinning-Zonen
beruhen auf publizierter Mikrostruktur-Forschung (Ni, Pearson & Poteshman, *JFE* 2005; Golez & Jackwerth, *JFE* 2012;
Barbon & Buraschi 2021) — nicht auf proprietären Vendor-Heuristiken." → hebt uns von GEX-Vendors ab, erfüllt E-E-A-T.

---

## D. ZUSÄTZLICH BUILDBARE METRIKEN (aus der Literatur abgeleitet)

| Metrik | Literatur-Anker | Buildbar mit unserem Stack |
|---|---|---|
| **OPEX-Charm-Drift-Studie** (Do-Close → Fr-Open, 3. Fr.) | Baltussen et al. (A4): 18,5 bps, t>4,5 | ✅ Yahoo/DB-Kurse + OPEX-Kalender → reproduzierbare Backtest-Studie/Blog |
| **Gamma-Regime-Ampel** (GEX>0/<0 → Vola-Verteilung) | Barbon/Buraschi (A3), SqueezeMetrics (B1) | ✅ `compute_gamma_exposure.py` vorhanden → nur Regime-Klassifikation + Vola-Split |
| **Pinning-Distanz-Metrik** (Kurs-Abstand zum nächsten großen Strike an OPEX) | Ni-P-P (A1), Golez/Jackwerth (A2) | ✅ Wall-Strikes × Spot am Verfallstag |
| **Intraday-Momentum/Reversal je Gamma-Vorzeichen** | Baltussen/Da/Soebhag (A5) | ⚠️ braucht Intraday-Daten (nicht Kern-Stack) — später |
| **Triple-Witching-Verstärkung** (Drift stärker an TW-Tagen) | Baltussen et al. (A4) | ✅ TW-Flag im Kalender vorhanden → Subgruppen-Analyse |

---

## Quellenliste (kompakt, mit URL/DOI)

**Peer-reviewed / akademisch:**
- Ni, Pearson & Poteshman (2005), *JFE* 78(1):49-87 — DOI 10.1016/j.jfineco.2004.08.005 — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=519044
- Golez & Jackwerth (2012), *JFE* 106(3):566-585 — DOI 10.1016/j.jfineco.2012.06.010 — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1664261
- Barbon & Buraschi (2021), "Gamma Fragility", WP — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3725454
- Baltussen, Terstegge & Whelan (2024), "The Derivative Payoff Bias", WP — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4562800
- Baltussen, Da & Soebhag, "End-of-Day Reversal" (2024) — https://academicweb.nd.edu/~zda/EOD.pdf ; "Hedging demand and market intraday momentum", *JFE* 2021 — https://www.sciencedirect.com/science/article/abs/pii/S0304405X21001598
- Amaya, Garcia-Ares, Pearson & Vasquez (2025), "0DTE Index Options and Market Volatility" — Cboe-Research-Reihe (proprietäre Daten)

**Vendor / Sell-Side / Praktiker (NICHT peer-reviewed):**
- SqueezeMetrics (2016/17), GEX White Paper — https://squeezemetrics.com/monitor/static/guide.pdf
- SpotGamma Primer (GEX/Vanna-Charm/0DTE) — https://spotgamma.com/gamma-exposure-gex/
- Kolanovic (JPMorgan), "Why We Have a Correlation Bubble" — https://www.newconstructs.com/wp-content/uploads/2010/10/JP-Morgan-and-Correlation
- Cem Karsan (Kai Volatility), Vanna/Charm-Interviews — https://www.rcmalternatives.com/2020/10/vol-curves-and-vanna-charm-with-cem-karsan-the-derivative/
- Ambrus Capital / Kris Sidial, "Changing Market Structure" (in `raw/papers/`)
- Cboe, "Much Ado About 0DTEs" — https://www.cboe.com/insights/posts/volatility-insights-evaluating-the-market-impact-of-spx-0-dte-options

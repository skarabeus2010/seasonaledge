# Papers-Inventar: Optionen / Gamma / Flows / Saisonalität

> Quelle: `raw/papers/` · erstellt 2026-08-01 · für späteren `sa-ingest`
> Ziel: Was können wir aus dieser Sammlung konkret auf seasonalpha.ai bauen — abgeglichen mit Bestehendem
> (`scripts/compute_gamma_exposure.py`, `docs/OPTIONS.md`, OPEX/VIX/Earnings-Kalender, Saisonalitäts-Seiten).

## Kern-Erkenntnis vorab

Die Sammlung ist im Wesentlichen die **theoretische Fundierung genau der Engine, die wir schon haben**
(GEX/Vanna/Charm/Walls/Zero-Gamma) — plus einige **neue, mit unserem Stack sofort buildbare Bausteine**:
Vanna/Charm-Pre-OPEX-Drift als *messbare Studie*, Gamma-Regime-Ampel (>0/<0 → Vola-Verteilung),
"VIX-up/Market-up"-Signal, und **Saisonalität der Fondsflüsse** (neue Achse zu unseren Kalender-Saisonalitäten).
Der große praktische Hebel ist **Content/SEO/Video** — die Papers liefern das "Warum" hinter unseren Mustern.

---

## 1. INVENTAR (alle Dateien)

### Lesbar (PDF / TXT / PNG / JPG) — Inhalt verifiziert

| Datei | Typ | Thema (1 Satz) |
|---|---|---|
| `VollandWhitePaper.pdf` | PDF ✅ | Ad Deum/DeLorenzo "Impact of option dealer flows on equity returns" — Dealer-Greeks (Δ/Γ/Vega/Vanna/Charm) vs SPX, 0DTE-Paradigmen (BofA/GEX/Anti-GEX/Sidial) mit Backtest-Trefferquoten. |
| `DealerPositioningOptions.pdf` | PDF ✅ | **Byte-identisch mit `VollandWhitePaper.pdf`** (Duplikat, 1.027.171 B). |
| `VollandUserGuide_Jun24.pdf` | PDF ✅ | Volland-Dashboard-Handbuch: Greeks-Definitionen, **Interpretations-Matrix** (Vorzeichen×Spot→bullish/bearish/support/resistance), DAG, Exposure-/Cumulative-/Heatmap-Widgets, 0DTE-Paradigmen, **Swing-Trading-Framework + Strategie-Matrix**. |
| `What is Gamma, Market Gamma and.pdf` | PDF ✅ | SpotGamma-Primer: Total Market Gamma >0 → enge Verteilung/leicht positiv; <0 → breite Verteilung/negativ. Vol-Trigger, Call/Put-Wall, Zero-Gamma, WSJ/SqueezeMetrics-Scatter. |
| `Options Volatility Checklist.pdf` | PDF ✅ | SpotGamma 3-Schritt-Checkliste: IV-Landschaft (Fixed-Strike-Matrix), Event-Check (Earnings/FOMC), Skew/Term-Structure → Trade-Setup (z.B. Calendars bei Backwardation). |
| `SG Vix-Index - Vix Up Market Up.pdf` | PDF ✅ | SocGen/SpotGamma "VIX up, Market up": Call-Kauf (Right-Tail/FOMO) kann VIX MIT steigendem Markt hochtreiben; VVIX/SKEW/Implied-Correlation als Belege. |
| `Ambrus+Capital+-+...Changing+Market+Structure...pdf` | PDF ✅ | Kris Sidial/Ambrus: Reflexivität & Fragilität (Gamma-/passiv-/strukturierte-Produkte-Flows). **Fig 7: "S&P während OpEx kaufen" → 3-J.-Backtest −15 %.** Variance-Drag, Drawdown-Häufigkeit. |
| `median month flow.jpg` | JPG ✅ | **Median-Monatsfluss in Aktien-Fonds+ETFs (% AUM, 1996-2022)** — Jan/Feb/Apr/Nov positiv, Jun/Aug/Okt negativ. Saisonalität der FLÜSSE. |
| `nasdaq 100 returns in july.jpg` | JPG ✅ | Median-2-Wochen-Nasdaq-100-Renditen seit 1983, sortiert — 1H-Juli & 1H-Feb an der Spitze. |
| `july 3 matrix.jpg` | JPG ✅ | Kalendertag-×-Monat-Rendite-Heatmap (grün/rot) — entspricht praktisch unserer TDOM/CDOM-Analyse. |
| `Seasonal yields.jpg` | JPG ✅ | S&P-Monatsrenditen-Heatmap pro Jahr (2015-2025) + 10-J.-Schnitt — unser Monats-Saisonalitäts-Muster. |
| `SPX Options ADV nadh DTE.jpg` | JPG ✅ | Cboe: SPX-Options-ADV nach Restlaufzeit — 0DTE-Anteil ~50 % → 56 % (Feb 25). Beleg für 0DTE-Dominanz. |
| `OPEX Cycle.png` | PNG ✅ | Schema: Positionen bauen → Hedges bauen → Verfall → Hedges gedeckt (der OPEX-Zyklus). |
| `Dealers Circle.png` | PNG ✅ | Schema Put-Hedging-Feedback-Loop (End-User kauft Put → Dealer verkauft Aktie → Reflexivität). |
| `Liquidity Cascade.png` | PNG ✅ | Ambrus "Market Incentive Loop" — Fed/Passive/Dealer-Hedging → Liquidity-Cascade → Crash. |
| `Demo IBKR.txt` | TXT ✅ | Nur Demo-Login-Credentials (irrelevant, ggf. löschen — enthält Klartext-Passwort). |
| `Lernmateiral.txt` | TXT ✅ | Ein Link zum CME-Options-Kurs. |
| `Options Volume.png` / `Stock Volume.png` | PNG ✅* | Volumen-Illustrationen (Optionen vs Aktien) — supplementär, nicht im Detail ausgewertet. |
| `Market Liquidity IMF.png` / `CME Grop Liquidity.png` | PNG ✅* | Liquiditäts-Illustrationen (IMF/CME) — supplementär. |
| `2024 TechStockOptionsVolume.jpg` | JPG ✅* | Tech-Aktien-Optionsvolumen 2024 — supplementär. |
| `2023-11-14 ...OptionTableVIX14.10.png` | PNG ✅* | Screenshot Options-/VIX-Tabelle — supplementär. |

\* readable, aber nur illustrativ — Kerninhalt steckt in den oben ausgewerteten Dateien.

### NICHT lesbar mit Read-Tool → **Konvertierung nötig** (nur nach Dateiname eingeordnet, Inhalt NICHT geraten)

| Datei | Typ | Vermutetes Thema (nur Dateiname!) |
|---|---|---|
| `All You Ever Wanted To Know About Gamma, Op-Ex, And Option-Driven Equity Flows.docx` | DOCX ⚠️ | Bekanntes Long-Form-Stück zu Gamma/OpEx/optionsgetriebenen Aktienflüssen. **Priorität für Konvertierung** (dürfte viel Content-Substanz haben). |
| `...Equity Flows de.docx` | DOCX ⚠️ | Deutsche Übersetzung des obigen. |
| `SG Optios Articles.docx` / `SG Optios Articles de.docx` | DOCX ⚠️ | SocGen-Options-Artikelsammlung (DE+EN). Konvertieren. |
| `SG Skew.docx` | DOCX ⚠️ | SocGen zu Skew. Konvertieren (Skew-Term-Structure-Feature). |
| `SG Vix-Index - Vix Up Market Up.docx` | DOCX ⚠️ | = Inhalt des bereits gelesenen PDFs (redundant). |
| `Dealer Gamma .docx` | DOCX ⚠️ | Dealer-Gamma-Mechanik. Konvertieren. |
| `Vol Carry.docx` | DOCX ⚠️ | Volatility-Carry / Vol-Risk-Premium. Konvertieren. |
| `1ß Truth about Options Trading Imran .docx` | DOCX ⚠️ | Vermutlich Retail-Options-Text (Autor "Imran"), unklare Relevanz. |
| `Entwurf Vorlage Options Pitch.docx` | DOCX ⚠️ | Präsentations-/Pitch-Entwurf (eigenes Material). |
| `What is Gamma, Market Gamma and.pptx` | PPTX ⚠️ | = Inhalt des bereits gelesenen SpotGamma-PDFs (redundant). |
| `Optionsseminar-.pptx` | PPTX ⚠️ | Seminar-Foliensatz (Grundlagen). |
| `Optionskalkulator_Vorstellung_15.02.24 (2).xlsx` | XLSX ⚠️ | Options-Kalkulator (Preise/Greeks?). Konvertieren, falls Formeln nützlich. |
| `Vol'Trihgger and Walls and SPX.xlsx` | XLSX ⚠️ | **Vol-Trigger + Walls + SPX** — evtl. konkrete Level-/Berechnungslogik. Priorität für Konvertierung. |
| `20230317Liquidity ES.jfif` / `Trading Map Options.jfif` | JFIF ⚠️ | ES-Liquidität / Options-Trading-Map. Read-Tool öffnet .jfif nicht → in .jpg umbenennen/konvertieren. |
| `Monthly Return Stat SPX 1964-2024.webp` | WEBP ⚠️ | SPX-Monatsrenditen-Statistik 1964-2024 — Read-Tool öffnet .webp nicht → in .png/.jpg konvertieren. |

> Konvertierung ist trivial machbar (`pandoc`/`python-docx`/`unzip` für Office, Umbenennen/`cwebp -o` für webp/jfif) — falls gewünscht, in einem Folgeschritt.

---

## 2. KERN-PAPERS: Kernidee + buildbares Feature

### Volland Whitepaper (DeLorenzo, Ad Deum) — die kausale Fundierung
- **Kernidee:** Dealer-Hedging treibt einen großen Teil der Index-Moves. **Vega/Vanna-Hedging** (nicht Gamma!) ist
  laut ihren Daten der stärkste Treiber der Spot-Vol-Korrelation; Gamma-Hedging ist notional klein ($5-10 Mrd/Pkt)
  gegen Vega (Billionen/Vol-Pkt). Dealer sind **netto short Vega** (v.a. lange Tenöre) → in Selloffs mehr Vega-Kauf.
- **0DTE-Paradigmen** (via Charm-Profil): BofA (short Strangle, "Lines in the Sand" halten, ~97 % W/L um 10:30),
  GEX (bullish, Ziel oben), Anti-GEX (bearish), Sidial (mean-revert). Mit Trefferquoten pro Tageszeit.
- **Buildbar bei uns:** (a) **Vanna/Charm zusätzlich zum GEX prominent** ausweisen (haben wir bereits berechnet,
  aber nicht als eigene Regime-Aussage). (b) **"Lines in the Sand" = größter neg. Charm-Strike unten / größter pos.
  oben** als Referenz-Range — mit unserem Charm-per-Strike direkt ableitbar (Index/EOD, kein 0DTE-Intraday).
  (c) Framing "Vega/Vanna ist der eigentliche Treiber" für Content.

### Volland User Guide — die **Interpretations-Matrix** (direkt als Tooltip/Legende verwendbar)
| Greek | (+) über Spot | (+) unter Spot | (−) über Spot | (−) unter Spot |
|---|---|---|---|---|
| Charm | bearish | bearish | bullish | bullish |
| Gamma | Widerstand | Support | permissiv | permissiv |
| Vanna | Magnet | Magnet | Repellent | Repellent |
| Vega | long Vol | long Vol | short Vol | short Vol |
- **Kernidee:** Ein sauberes, einheitliches Regelwerk, wie man Vorzeichen×Position-zu-Spot pro Greek liest, plus
  DAG (Delta-Adjusted Gamma: Vorzeichen aller Strikes > Spot flippen → grün=Dealer kauft, rot=verkauft).
- **Buildbar bei uns:** Diese Matrix als **Erklär-Legende auf einer `/gamma`-Seite** und in Blog/Video. DAG als
  zusätzliche abgeleitete Serie aus unserem Per-Strike-Gamma (billig). Swing-Framework (Halte 10-45 Tage,
  "all expirations", zweit-Ordnungs-Greeks) passt exakt zu unserem Swing-/Saison-Publikum.

### "What is Gamma / Market Gamma" (SpotGamma) — **Gamma-Regime-Ampel**
- **Kernidee:** Ein einziger Wert (Total Market Gamma) mit großem Effekt: **>0 → enge Range, leicht positiv;
  <0 → breite Verteilung, negativ.** Vol-Trigger als Schaltpunkt.
- **Buildbar bei uns (billig, hoher Wert):** Wir haben net-GEX + Zero-Gamma-Flip schon. Daraus eine
  **Regime-Ampel** (grün = long-Gamma/Mean-Reversion, rot = short-Gamma/Trend&Vola) + Distanz Spot↔Flip.
  Das ist das einprägsamste, laienverständlichste Ein-Zahl-Signal der ganzen Sammlung.

### Options Volatility Checklist (SpotGamma) — **Skew & Term-Structure**
- **Kernidee:** IV-Landschaft (Fixed-Strike-Matrix), Event-Bereinigung (Earnings/FOMC), Skew flach/steil →
  Backwardation vs Contango → Trade (Calendars, Butterflies…).
- **Buildbar bei uns:** Wir haben ATM-IV + 90/110-Skew pro Term. **Skew-Term-Structure-Chart** (IV über
  Expirationen + Skew-Kurve) ist daraus rendrbar. Event-Overlay = unser Earnings/FOMC-Kalender → **direkte
  Verknüpfung** ("near-term IV erhöht wegen Earnings am …"). Kohärent mit `/vixpiration`.

### SG "VIX up, Market up" — **antizyklisches Vola-Signal**
- **Kernidee:** VIX ist nicht nur "Angst"; starkes Call-Buying (Right-Tail/FOMO) kann VIX MIT dem Markt hochtreiben.
  Belege: VVIX/SKEW/Implied-Correlation.
- **Buildbar bei uns:** **"VIX-up/Market-up-Tage"-Detektor** (SPY-Return >0 UND VIX-Change >0 am selben Tag) →
  Häufigkeit/Saisonalität als Studie/Blog. Braucht nur SPY+^VIX (haben wir). Optional VVIX/SKEW als Kontext
  (frei bei Cboe/Yahoo, ^SKEW ist z.T. verfügbar).

### Ambrus — **strukturelle Fragilität + OpEx-Drift-Backtest**
- **Kernidee:** Reflexivität durch Dealer-Gamma, passive Flows, strukturierte Produkte, wenige Market-Maker.
  **Fig 7: Kauf des S&P nur während OpEx-Fenster verlor über 3 Jahre ~15 %** → Post-OpEx-Schwäche ist strukturell.
- **Buildbar bei uns (Killer-Studie):** Wir haben den **exakten OPEX-Kalender + normalisierte Renditen**.
  → **Reproduzierbare Studie "Pre-OPEX-Drift vs Post-OPEX-Schwäche"** über Jahrzehnte, mehrere Indizes.
  Das ist eine originäre Daten-Studie (Digital-PR/Backlink-Hebel) UND validiert unsere Gamma/Charm-These empirisch.

---

## 3. MAPPING-TABELLE (Idee × Quelle × Status × Aufwand × Anknüpfung)

| # | Idee / Metrik | Quelle(n) | Status | Aufwand | Anknüpfung |
|---|---|---|---|---|---|
| 1 | **Gamma-Regime-Ampel** (net-GEX >0/<0 + Distanz zum Zero-Gamma-Flip) | What-is-Gamma, Volland | **haben Daten, UI fehlt** | S (JSON→Ampel) | neue `/gamma` bzw. Overlay `/opex`,`/vixpiration`,`crash-fruehwarnung` |
| 2 | **Call/Put/Absolute-Wall + Zero-Gamma** als Chart | What-is-Gamma, Volland UG | **haben** (`gex_*.json`) | S | `/gamma`-Frontend (Daten liegen, Seite fehlt) |
| 3 | **Vanna & Charm prominent** (Vola-/Zeit-Flows) + Interpretations-Matrix-Legende | Volland WP+UG | **haben Daten**, nicht ausgewiesen | S-M | `/gamma` + Tooltips |
| 4 | **"Lines in the Sand"** (größter neg./pos. Charm-Strike = Range) | Volland WP+UG | **neu baubar** (aus Charm-per-Strike) | M | `/gamma`, EOD/Index (0DTE-Intraday nicht möglich) |
| 5 | **DAG** (Delta-Adjusted Gamma, Vorzeichen-Flip > Spot) | Volland UG | **neu baubar** (abgeleitet) | S | `/gamma` Zusatzserie |
| 6 | **Skew-Term-Structure-Chart** (IV je Expiration + Skew-Kurve, Backwardation-Flag) | Vol-Checklist, SG Skew(⚠) | **haben Daten** (ATM-IV/90-110-Skew) | M | `/vixpiration` + Earnings-Overlay |
| 7 | **VIX-up/Market-up-Detektor** (Saisonalität/Häufigkeit) | SG VIX-up | **neu baubar** (SPY+^VIX) | S | Blog + `crash-fruehwarnung`/Regime |
| 8 | **Pre-OPEX-Drift / Post-OPEX-Schwäche-Studie** (Ambrus Fig 7 reproduziert) | Ambrus, Volland | **neu baubar** (OPEX-Kal.+norm. Renditen) | M | `/opex`, `/monatswechsel` + Digital-PR-Studie |
| 9 | **Gamma-Regime-Backtest** (Vola/Return-Verteilung an >0 vs <0 Tagen) | What-is-Gamma, Volland | **neu baubar** (GEX-Historie nötig) | M-L | Empirie-Loop OPTIONS.md Punkt 4 |
| 10 | **Saisonalität der Fondsflüsse** (Median-Monatsfluss % AUM) | `median month flow.jpg` | **neu, braucht Bezahl-/Ext.-Daten** | M | neue Achse zu `jahreszyklus`/`monatszyklus` (ICI/EPFR-Daten) |
| 11 | **0DTE-Anteil / Options-ADV-nach-DTE-Kontext** | `SPX Options ADV…`, Ambrus | **braucht Bezahl-/Cboe-Daten** | S (statisch) | Content/Blog ("warum 0DTE zählt") |
| 12 | **0DTE-Charm-Paradigmen** (BofA/GEX/Anti-GEX intraday) | Volland WP+UG | **NICHT baubar ohne Intraday/0DTE-Feed** | — (Paid) | nur Erklär-Content |
| 13 | **VVIX/SKEW/Implied-Correlation-Panel** | SG VIX-up | **teils baubar** (^VIX/^SKEW frei; VVIX/COR paid/patchy) | M | `/vixpiration`/Regime |
| 14 | **Skew-Term-Structure aus SG-Skew/Vol-Carry** | SG Skew(⚠), Vol Carry(⚠) | **Konvertierung nötig** vor Bewertung | — | s. #6 |
| 15 | **Vol-Trigger + Walls (konkrete Level-Logik)** | `Vol'Trihgger…xlsx`(⚠) | **Konvertierung nötig** | — | evtl. Cross-Check unserer Wall-Definition |

Legende Aufwand: S = < ½ Tag · M = 1-3 Tage · L = > 3 Tage (jew. inkl. i18n + Disclaimer).

---

## 4. TOP-5-EMPFEHLUNGEN (wertvollste, mit unserem Stack umsetzbar)

1. **`/gamma`-Seite bauen (Regime-Ampel + Walls + Vanna/Charm)** — Daten (`landing/data/gex_*.json`) liegen bereits,
   nur die Frontend-Seite fehlt (OPTIONS.md Roadmap #3). Größter Hebel/Aufwand-Verhältnis. Regime-Ampel (net-GEX
   >0/<0 + Flip-Distanz) ist das laienverständlichste Ein-Zahl-Signal der Sammlung. Quelle: What-is-Gamma + Volland.
   → Aufwand S-M, sofort startbar.

2. **Pre-OPEX-Drift / Post-OPEX-Schwäche als reproduzierbare Daten-Studie** (Ambrus Fig 7). Wir haben OPEX-Kalender +
   normalisierte Renditen über Jahrzehnte → originäre Studie, die (a) unsere Gamma/Charm-These empirisch validiert und
   (b) ein Digital-PR/Backlink-Asset ist (der #1-Wachstumsengpass). Anknüpfung `/opex` + `/monatswechsel`.
   → Aufwand M.

3. **Vanna/Charm-OPEX-Flow-Erklärung + "Lines in the Sand"-Range** aus unserem Per-Strike-Charm. Macht aus dem
   OPEX-*Muster* ein *Warum* (Charm/Vanna zwingen Dealer zu Rückkäufen → Aufwärts-Bid in den 3. Freitag). Volland
   liefert die fertige Interpretations-Matrix als Legende/Tooltip. → Aufwand M, EOD/Index (0DTE-Intraday NICHT möglich).

4. **Skew-Term-Structure-Chart mit Event-Overlay** (Vol-Checklist). ATM-IV + 90/110-Skew pro Term haben wir; daraus
   IV-über-Expirationen + Skew-Kurve + Backwardation-Flag, überlagert mit Earnings/FOMC aus unserem Kalender
   ("near-term IV erhöht wegen Earnings am …"). Anknüpfung `/vixpiration`. → Aufwand M.

5. **"VIX-up/Market-up"-Detektor + Studie** (SG VIX-up). Nur SPY+^VIX nötig: Tage mit Markt↑ UND VIX↑ zählen,
   Häufigkeit/Saisonalität, Blog + Regime-Kontext. Einfachster neuer Baustein mit hohem Content-Wert, weil er
   verbreiteter Intuition ("VIX = Angst") widerspricht. → Aufwand S.

## Ehrlichkeits-/Daten-Hinweise (YMYL)
- Alles GEX/Vanna/Charm bleibt **naive Dealer-Heuristik auf EOD-Yahoo-Daten** — NICHT SpotGammas/Vollands
  Inventory-Modell (siehe `docs/OPTIONS.md`). Immer als "Referenz, keine Barriere/kein Signal" labeln.
- **0DTE-Paradigmen (BofA/GEX/Anti-GEX/Sidial) sind NICHT baubar** ohne Intraday-/0DTE-Feed (Paid: Polygon/Tradier/Theta).
- **Fondsfluss-Saisonalität (#10)** und **Options-ADV-nach-DTE (#11)** brauchen externe/Bezahl-Daten (ICI/EPFR bzw. Cboe).
- **DAX/`.DE`/`^GDAXI`**: Yahoo liefert keine Options-Chain → Gamma nur für US-gelistete Underlyings (siehe OPTIONS.md).
- Volland-WP == DealerPositioningOptions (Duplikat). `SG Vix…docx`/`What is Gamma…pptx` sind Redundanzen zu gelesenen PDFs.

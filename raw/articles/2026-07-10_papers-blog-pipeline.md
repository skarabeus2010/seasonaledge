# Blog-Post-Pipeline aus der Papers-Literatur (Optionen / Dealer-Positioning / Saisonalität)

> erstellt 2026-08-02 · Autor: SeasonAlpha-Literatur-Scout · für `sa-ingest` + späteren `blogger`-Agenten
> Basis: `raw/articles/2026-07-10_papers-inventar-optionen.md` (lesbares Inventar) +
> `raw/articles/2026-07-10_dealer-positioning-akademische-fundierung.md` (peer-reviewed Anker) +
> neu heruntergeladene Volltexte in `raw/papers/` (`_index.md`, Gruppe 1+2) + verifizierte Bilder.
> Ziel: 8 buildbare, paper-fundierte Blog-Briefs; jeder an ein reales Tool/Chart + Saisonalität angebunden, YMYL-ehrlich.
> **Nicht doppeln:** bereits publiziert „Dealer Positioning erklärt". Diese 8 bauen darauf auf / gehen in die Tiefe.

## Quellen-Grounding (nur real Gelesenes — keine erfundenen Zahlen)

Verifiziert für diese Pipeline:
- **Ni, Pearson & Poteshman (2005), JFE 78(1)** — Pinning an Strikes zum OPEX; Renditeverschiebung ≥ 16,5 bps am Verfallstag, aggregiert ~9 Mrd. $. DOI 10.1016/j.jfineco.2004.08.005. (`07_...` verwandt: Pearson/Poteshman/White 2006.)
- **Golez & Jackwerth (2012), JFE 106(3)** — S&P-500-Futures pinnen zum ATM-Strike; ≥ 115 Mio. $ Nominal-Verschiebung/Verfall. DOI 10.1016/j.jfineco.2012.06.010.
- **Avellaneda, Kasyan & Lipkin (2011)** — mathematisches Pinning-Modell (Feedback Options↔Kurs), Fig 1 „pinned vs. not". `raw/papers/09_...pdf` (Intro/Fig verifiziert).
- **Barbon & Buraschi (2021), „Gamma Fragility"** — aggregiertes Dealer-Gamma × Illiquidität erklärt Intraday-Momentum/Reversal; neg. Gamma → Momentum, pos. → Reversal. SSRN 3725454. `raw/papers/04_...pdf`.
- **Baltussen, Terstegge & Whelan (2024), „The Derivative Payoff Bias"** — 3.-Freitag-SOQ übersteigt Vortagsschluss 2003–2021 im Schnitt um **18,5 bps** (t>4,5), tent-shaped Reversal Do-Close→Fr-Open→Fr-Mittag; ~4 Mrd. $/Jahr Wealth-Transfer in SPX, stärker an Triple-Witching. SSRN 4562800.
- **Baltussen et al. (2021), „Hedging Demand and Market Intraday Momentum", JFE** — Gamma-Hedging treibt Intraday-Momentum, stärker an OPEX-Tagen. `raw/papers/05_...pdf`.
- **Gârleanu, Pedersen & Poteshman (2005), „Demand-Based Option Pricing", NBER WP 11843** — Endnutzer sind **netto long Index-Optionen, v.a. OTM-Puts** → erklärt „Expensiveness"/Smirk (Skew). Abstract verifiziert (`raw/papers/06_...pdf`).
- **Amaya, Garcia-Ares, Pearson & Vasquez (2025), „0DTE Index Options and Market Volatility"** — schätzt aus proprietären Cboe-Trades den *maximalen* 0DTE-Gamma-Impact. `raw/papers/08_...pdf` (Cboe-Research). Gegenpol: Cboe „Much Ado About 0DTEs".
- **SqueezeMetrics (2016/17), GEX White Paper** — Begriffsprägung; pos. GEX stabilisiert, neg. GEX verstärkt. `raw/papers/01_...pdf`.
- **Ambrus/Sidial, „Changing Market Structure"** — Fig 7: „S&P nur im OpEx-Fenster kaufen" → 3-J.-Backtest ~ −15 %. Reflexivität/Fragilität.
- **`median month flow.jpg` (verifiziert):** Median-Monatszufluss in US-Aktienfonds+ETFs, % AUM, 1996–2022 — Jan **+0,22 %**, Feb **+0,17 %**, Mär +0,08 %, Apr **+0,16 %**, Mai +0,04 %, Jun **−0,10 %**, Jul +0,09 %, Aug **−0,10 %**, Sep +0,02 %, Okt **−0,035 %**, Nov **+0,14 %**, Dez ~0 %. (Quelle im Bild: ICI-Fondsflüsse.)

Weiterhin **nicht lesbar** (nur einordnen, NICHT als Quelle zitieren): alle `.docx/.pptx/.xlsx/.jfif/.webp` (u.a. „All You Ever Wanted To Know About Gamma, Op-Ex…docx", `Monthly Return Stat SPX 1964-2024.webp`). Für einen Brief, der SPX-1964-Statistik bräuchte, müssten wir die Zahl **selbst aus unseren Daten** rechnen, nicht aus dem webp raten.

---

## TOP-3 (bester SEO/Backlink-Hebel — echte Daten-Studien mit peer-reviewed Anker)

### ⭐ Brief 1 — „Der Third-Friday-Spike": OPEX-Drift, über Jahrzehnte nachgerechnet  *(DATA STUDY)*
- **Arbeitstitel:** „Der Verfallstags-Effekt: Warum der S&P am 3. Freitag anders eröffnet"
- **SEO-Titel:** „OPEX-Effekt am S&P 500: Der Third-Friday-Price-Spike (Daten-Studie über 40 Jahre)" · **Haupt-Keyword:** „OPEX Effekt S&P 500" / „Verfallstag Aktienmarkt"
- **Quelle(n):** Baltussen, Terstegge & Whelan (2024) „Derivative Payoff Bias" (18,5 bps SOQ-Overnight-Spike, t>4,5, ~4 Mrd. $/Jahr SPX) als Haupt-Anker + Ambrus/Sidial Fig 7 (Post-OpEx-Schwäche, 3 J. −15 %) als Kontrast.
- **SeasonAlpha-Anknüpfung:** `/opex` + `/monatswechsel`; Datenbasis = unser **OPEX-/Triple-Witching-Kalender** × **normierte Renditen** über Jahrzehnte, mehrere Indizes. Neues Skript `scripts/study_opex_drift.py`. Chart: Balken „Ø-Rendite je Handelstag relativ zum 3. Freitag (−5…+5)", Split monatlicher OpEx vs. Quartals-Triple-Witching.
- **Kernaussage / Winkel:** Der Verfalls-Freitag ist strukturell auffällig (Charm-getriebenes Dealer-Rebalancing) — wir reproduzieren die akademische 18,5-bps-Beobachtung **mit eigenen Daten** und zeigen die tent-shape Do→Fr→Mittag. Moat: Vendoren erklären Mechanik, Seasonality-Seiten zeigen nackte Muster — wir liefern beides + Verfallstyp-Split.
- **Typ:** **Daten-Studie (Digital-PR/Backlink-Asset).** Zahl-getriebener Titel, r/options-/X-/Newsletter-tauglich.
- **Ehrlichkeit:** Der Overnight-SOQ-Effekt (18,5 bps) ist ein **Intraday-/Open-Effekt** — mit EOD-Yahoo (Close-zu-Close) nur teilweise reproduzierbar; ehrlich sagen „wir messen die Tages-/Wochen-Drift, nicht den Overnight-Sprung selbst (dafür bräuchte es saubere Open-Daten)". OpEx-Woche-Outperformance hat sich in den letzten ~4 Jahren abgeschwächt — fair erwähnen.

### ⭐ Brief 2 — „Pinning & Walls": zieht der Kurs zum großen Strike?  *(DATA STUDY + Education)*
- **Arbeitstitel:** „Pinning: Warum Aktien am Verfallstag an runden Strikes kleben"
- **SEO-Titel:** „Pinning am Optionsverfall: Call-Wall, Put-Wall & die Magnetwirkung der Strikes" · **Haupt-Keyword:** „Pinning Optionen" / „Call Wall Put Wall erklärt"
- **Quelle(n):** Ni, Pearson & Poteshman (2005) JFE (Einzelaktien-Pinning, 16,5 bps, ~9 Mrd. $) + Golez & Jackwerth (2012) JFE (Index/ES-Pinning) + Avellaneda/Kasyan/Lipkin (2011) (Feedback-Modell). Drei Anker — höchste Zitier-Autorität der ganzen Sammlung.
- **SeasonAlpha-Anknüpfung:** `/dealer-positioning` (Call/Put/Absolute-Wall + Zero-Gamma liegen in `gex_*.json`), später `/gamma`. **Buildbare Metrik: „Pinning-Distanz"** = Abstand Spot ↔ nächster großer Wall-Strike am Verfallstag, über Ticker/Zeit. Chart „Gamma by Strike" mit markierter Wall + Verfallstags-Close-Verteilung relativ zum Strike.
- **Kernaussage / Winkel:** Die von uns gezeigten Walls sind kein Vendor-Gimmick — Pinning ist seit 2005 in Top-Journals belegt. Wir machen die Distanz messbar und saisonal (stärker an Triple-Witching).
- **Typ:** Education-Kern + **kleine Daten-Studie** (Pinning-Distanz-Verteilung an OPEX-Tagen aus unseren Kursen — reproduzierbar).
- **Ehrlichkeit:** Unsere Walls = **naive Netto-Gamma-je-Strike-Heuristik auf EOD-Yahoo-OI**, nicht SpotGammas Inventory-Modell → „Referenz, keine Barriere/kein Signal". Pinning-Effekt ist statistisch/klein, kein handelbares Einzeltag-Signal. Nur US-Underlyings (Yahoo-Chain).

### ⭐ Brief 3 — „Gamma-Regime": Wann dämpft, wann verstärkt der Markt?  *(Education → Regime-Ampel)*
- **Arbeitstitel:** „Long Gamma vs. Short Gamma: das Regime, das entscheidet, ob Dips gekauft werden"
- **SEO-Titel:** „Gamma Exposure (GEX) erklärt: Long- vs. Short-Gamma-Regime & Zero-Gamma-Flip" · **Haupt-Keyword:** „Gamma Exposure erklärt" / „GEX Zero Gamma"
- **Quelle(n):** SqueezeMetrics (2016) GEX-White-Paper (Begriff/Intuition) **akademisch validiert durch** Barbon & Buraschi (2021) „Gamma Fragility" (neg. Gamma × Illiquidität → Momentum; pos. → Reversal). Trennung Praktiker vs. peer-reviewed sauber ausweisen (E-E-A-T).
- **SeasonAlpha-Anknüpfung:** `/dealer-positioning` → geplante **Gamma-Regime-Ampel** (net-GEX >0/<0 + Distanz zum Zero-Gamma-Flip; Daten in `gex_summary.json`). Cross-Link `crash-fruehwarnung`. Chart: Ampel + Zero-Gamma-Flip-Marker im „Gamma by Strike"-Profil.
- **Kernaussage / Winkel:** Ein einprägsames Ein-Zahl-Signal (Vorzeichen des Netto-Gamma) mit publizierter Fundierung: erklärt, warum manche Tage „ruhig mean-reverten" und andere „trenden". Laienverständlichster Baustein der Sammlung.
- **Typ:** Education (Evergreen, hohes Suchvolumen „GEX erklärt").
- **Ehrlichkeit:** Naive Heuristik ≠ Inventory-Modell. **GEX-Historie fehlt uns** (Snapshots erst ~seit 07/2026) → Regime-Aussage ist ein **Live-Stand, keine backtestbare Zeitreihe**; für „wie oft war der Markt short gamma" nur VIX/RV-Proxy oder „ab Snapshot-Beginn". Barbon/Buraschi ist Working Paper (breit zitiert, nicht final peer-reviewed).

---

## WEITERE 5 BRIEFS

### Brief 4 — „Warum die Put-Skew nie verschwindet"  *(Education)*
- **Arbeitstitel:** „Der ewige Put-Aufschlag: Warum Absicherung strukturell teuer ist"
- **SEO-Titel:** „Volatility Skew erklärt: Warum OTM-Puts dauerhaft teurer sind" · **Haupt-Keyword:** „Volatility Skew erklärt" / „Put Skew"
- **Quelle(n):** Gârleanu, Pedersen & Poteshman (2005) „Demand-Based Option Pricing" (NBER 11843) — Endnutzer netto long OTM-Index-Puts → Demand-Pressure erklärt den Smirk. Zitierfähig, top-Autoren.
- **SeasonAlpha-Anknüpfung:** `/dealer-positioning` **Skew-Metrik** (90/110-Skew je Term liegt in `gex_*.json`), `/vixpiration`. Chart „Skew by Term" (IV-Kurve 90 %→110 % Strikes) + optional saisonaler Verlauf (Snapshot-Cron).
- **Kernaussage / Winkel:** Skew ist kein Modellfehler, sondern Nachfrage-Druck: Vermögensverwalter kaufen Puts, Dealer tragen das Risiko und verlangen Prämie. Erklärt, warum unsere Skew-Kurve fast immer nach unten links kippt.
- **Typ:** Education (Evergreen).
- **Ehrlichkeit:** 90/110-Skew aus EOD-Yahoo-Chain = Näherung, keine vollständige Vol-Surface. Skew-**Niveau** ist deutbar, minutengenaue Änderungen nicht. Kein Handelssignal.

### Brief 5 — „VIX rauf, Markt rauf": wenn Angst-Index und Kurse steigen  *(Education + Mini-Studie)*
- **Arbeitstitel:** „VIX steigt, Markt steigt — der kontraintuitive Tag"
- **SEO-Titel:** „VIX up, Market up: Warum der Angstindex mit steigenden Kursen klettern kann" · **Haupt-Keyword:** „VIX steigt Markt steigt" / „VIX erklärt"
- **Quelle(n):** SocGen/SpotGamma „VIX up, Market up" (Call-FOMO/Right-Tail-Nachfrage treibt IV mit dem Markt; VVIX/SKEW als Belege). Vendor/Sell-Side — als solches labeln.
- **SeasonAlpha-Anknüpfung:** Mini-Studie aus **SPY + ^VIX** (haben, lange Historie): Detektor „Tage mit SPY-Return >0 UND VIX-Change >0", Häufigkeit **je Monat/TDOM** (Saisonalität!). Cross-Link `crash-fruehwarnung`, `/jahreszyklus`. Chart: Balken „Anteil VIX-up/Market-up-Tage je Monat".
- **Kernaussage / Winkel:** Widerlegt „VIX = reine Angst"; der saisonale Split (Hypothese: gehäuft in Q4-/Januar-Melt-ups) ist der originäre Dreh, den die Vendor-Quelle nicht hat.
- **Typ:** Education mit **eingebauter Mini-Daten-Studie** (Quick-Win, Aufwand S).
- **Ehrlichkeit:** SG-Quelle ist Vendor, nicht peer-reviewed. VVIX/Implied-Correlation nur patchy frei — als Kontext, nicht als Kernbeleg. Effekt beschreibend, kein Signal.

### Brief 6 — „Post-OpEx-Schwäche & Triple Witching"  *(DATA STUDY, kalendergetrieben 4×/Jahr)*
- **Arbeitstitel:** „Nach dem großen Verfall: die Post-Triple-Witching-Woche"
- **SEO-Titel:** „Triple Witching: Was nach dem großen Verfallstag mit dem S&P 500 passiert (Daten-Studie)" · **Haupt-Keyword:** „Triple Witching" / „großer Verfallstag Aktien"
- **Quelle(n):** Ambrus/Sidial Fig 7 („S&P nur im OpEx-Fenster kaufen → 3 J. −15 %") + Baltussen et al. (2024) (Effekt stärker an Triple-Witching). Reflexivität/OI-Cleanup als Mechanik.
- **SeasonAlpha-Anknüpfung:** **Triple-Witching-Flag im Kalender** (haben) × normierte Renditen. `/opex` + Kalender-Event-Tooltip. Chart: Ø-Rendite Woche-vor / Verfallswoche / Woche-danach, Quartal (TW) vs. normaler Monats-OpEx.
- **Kernaussage / Winkel:** Der größte OI-Aufbau (Quartalsverfall) hat ein messbares „Aufräum"-Nachbeben — wir quantifizieren die Post-TW-Woche über Jahrzehnte.
- **Typ:** **Daten-Studie**, zusätzlich wiederkehrender Kalender-Content-Anlass (4×/Jahr → auch YouTube-Pipeline-Futter).
- **Ehrlichkeit:** Ambrus = Praktiker-White-Paper (nicht peer-reviewed). Effekt zeit-/regimeabhängig, nicht garantiert; „struktureller Kontext, kein Signal".

### Brief 7 — „Saisonalität der Fondsflüsse"  *(DATA STUDY / Overlay)*
- **Arbeitstitel:** „Wohin das Geld im Kalenderjahr fließt — und warum der Herbst schwächelt"
- **SEO-Titel:** „Saisonalität der Aktienmärkte: Die Fondsfluss-Landkarte über das Jahr" · **Haupt-Keyword:** „Saisonalität Aktienmarkt" / „beste Monate Aktien"
- **Quelle(n):** `median month flow.jpg` (ICI, 1996–2022; verifizierte Monatswerte oben — Jan/Feb/Apr/Nov +, Jun/Aug/Okt −). Als **illustratives Muster** zitieren (kein peer-reviewed Paper).
- **SeasonAlpha-Anknüpfung:** `/monatszyklus` + `/jahreszyklus`: die publizierte Fluss-Kurve als **erklärende Overlay-Linie** über unsere eigene Monats-Saisonalität (normierte Renditen, selbst gerechnet). Chart: unsere Monats-Heatmap/Balken + Fluss-Overlay.
- **Kernaussage / Winkel:** Die Monats-Saisonalität bekommt ein „Warum": strukturelle Zuflüsse (Jahresanfang, Contributions) vs. Abflüsse (Sommer/Herbst) decken sich mit Kurs-Saisonalität. Moat: Fluss × Kalender × eigene Renditen.
- **Typ:** **Daten-Studie** (unsere Renditen) + Overlay-Erklärung.
- **Ehrlichkeit:** Fluss-Kurve = **publizierte ICI-Illustration, nicht live nachgerechnet** (echte laufende Fondsflüsse EPFR/ICI = PAID). Klar labeln „Muster nach ICI, Illustration". Korrelation ≠ Kausalität. Unsere Rendite-Zahlen selbst rechnen (Yahoo-Basis), nicht aus dem `Monthly Return Stat SPX 1964-2024.webp` raten (unlesbar).

### Brief 8 — „0DTE: Hype vs. Evidenz"  *(Education, E-E-A-T / YMYL-Trust)*
- **Arbeitstitel:** „0DTE-Optionen: Sprengen sie den Markt? Was die Forschung sagt"
- **SEO-Titel:** „0DTE-Optionen erklärt: Erhöhen Tagesverfall-Optionen die Volatilität?" · **Haupt-Keyword:** „0DTE Optionen" / „0DTE Volatilität"
- **Quelle(n):** Amaya, Garcia-Ares, Pearson & Vasquez (2025) (akademische Schätzung des max. 0DTE-Gamma-Impacts) **vs.** Cboe „Much Ado About 0DTEs" (MM-Gamma ~170–670 Mio. $, 0,04–0,17 % der ES-Liquidität → nicht signifikant) — Interessenkonflikt Börsenbetreiber offenlegen. Kontext: SPX-Options-ADV-nach-DTE (0DTE ~50 %→56 %).
- **SeasonAlpha-Anknüpfung:** Erklär-Content rund um `/dealer-positioning`; ehrlicher Rahmen, **warum wir 0DTE NICHT abbilden** (EOD-Daten). Kein neuer Chart nötig; ggf. statische ADV-nach-DTE-Illustration mit Quellenangabe.
- **Kernaussage / Winkel:** Seriöser, ausgewogener Überblick statt Vendor-Hype — genau das Trust-Signal (E-E-A-T), das eine junge YMYL-Domain braucht. Neil Pearson (Autor des Pinning-Klassikers) bringt Autorität.
- **Typ:** Education / Trust-Content (kein Backlink-Kracher, aber Autoritäts-Baustein).
- **Ehrlichkeit:** **0DTE-/Intraday-Paradigmen (BofA/GEX/Anti-GEX/Sidial) sind mit unserem EOD-Stack NICHT baubar** — braucht Paid-Intraday-Feed (Polygon/Tradier/Theta). Explizit als Datengrenze benennen. Cboe-Studie = Interessenkonflikt.

---

## Mapping-Tabelle (Brief × Quelle × Tool × Typ × Aufwand × Daten-Status)

| # | Brief | Peer-reviewed Anker | Tool/Seite + Chart | Typ | Aufwand | Daten-Status |
|---|---|---|---|---|---|---|
| 1 | Third-Friday-Spike / OPEX-Drift | Baltussen 2024 (18,5 bps) + Ambrus | `/opex` · Balken Rendite-je-HT | **Daten-Studie** | M | haben (OPEX-Kal.+norm. Renditen); Overnight-Sprung nur teilw. |
| 2 | Pinning & Walls | Ni-P-P 2005 + Golez/Jackwerth 2012 + Avellaneda 2011 | `/dealer-positioning` · „Gamma by Strike" + Pinning-Distanz | Edu + Mini-Studie | M | haben (`gex_*.json`), US-only |
| 3 | Gamma-Regime-Ampel | Barbon/Buraschi 2021 + SqueezeMetrics | `/dealer-positioning`→`/gamma` · Ampel + Zero-Gamma | Education | S | Live haben; **GEX-Historie fehlt** |
| 4 | Put-Skew / Demand-Pressure | Gârleanu/Pedersen/Poteshman 2005 | `/dealer-positioning` · „Skew by Term" | Education | S–M | haben (90/110-Skew), Näherung |
| 5 | VIX-up/Market-up | (SG Vendor) | Blog + `crash-fruehwarnung` · Balken je Monat | Edu + Mini-Studie | S | haben (SPY+^VIX) |
| 6 | Post-OpEx / Triple Witching | Ambrus + Baltussen 2024 | `/opex`+Kalender · Wochen-Rendite Split | **Daten-Studie** | S–M | haben (TW-Flag+norm. Renditen) |
| 7 | Fondsfluss-Saisonalität | (ICI-Bild, illustrativ) | `/monatszyklus` · Heatmap + Fluss-Overlay | **Daten-Studie**+Overlay | S–M | Renditen haben; Fluss = illustrativ/PAID |
| 8 | 0DTE: Hype vs. Evidenz | Amaya/Pearson 2025 (vs. Cboe) | `/dealer-positioning` · Erklär-Content | Education/Trust | S | Erklär-only; 0DTE-Bau = PAID |

Aufwand: S = <½ Tag · M = 1–3 Tage (jew. inkl. i18n + Disclaimer).

## Reihenfolge-Empfehlung für den blogger-Agenten
1. **Brief 1 (Third-Friday-Spike)** — stärkstes Backlink-Asset (peer-reviewed Zahl + eigene Reproduktion, teilbarer Titel).
2. **Brief 2 (Pinning & Walls)** — höchste Zitier-Autorität (2× JFE), stützt direkt den bereits publizierten Dealer-Positioning-Post.
3. **Brief 3 (Gamma-Regime)** — größtes Evergreen-Suchvolumen („GEX erklärt"), niedrigster Aufwand.
Danach 4 (Skew), 6 (Triple Witching, kalendergetriggert), 7 (Fondsfluss-Saison), 5 (VIX-up Quick-Win), 8 (0DTE-Trust).

## Übergreifende YMYL-Leitplanken (in JEDEN Post übernehmen)
- Naive Dealer-Heuristik auf EOD-Yahoo-OI ≠ SpotGamma/Volland-Inventory-Modell → „Referenz, keine Barriere, **kein Kauf-/Verkaufssignal**" (Linie `docs/YOUTUBE_DISCLAIMER.md`).
- Peer-reviewed (JFE/NBER) **strikt** von Vendor/Sell-Side (SpotGamma/SocGen/Ambrus/SqueezeMetrics) trennen — Vendor als „Praktiker-Ursprung", akademisch validieren.
- **PAID / nicht baubar:** 0DTE-/Intraday-Flows, echte Fondsflüsse (EPFR/ICI), echte Dealer-Bücher, historische GEX-Regime (bis Snapshot-Cron Historie hat). Nicht als „baubar" verkaufen.
- **US-only:** Gamma/Skew nur für US-gelistete Underlyings (Yahoo-Chain); DAX/`.DE`/`^GDAXI` leer → ETF-Proxy oder Paid-Eurex.
- Zahlen entweder **aus dem zitierten Paper** (mit DOI/URL) ODER **aus unseren Daten selbst gerechnet** (Yahoo-Basis, reproduzierbar) — **nie** aus unlesbaren Formaten (`.webp/.docx/.xlsx`) raten.

## Konzept-Kandidaten für `wiki/concepts/` (Vorschlag — nicht selbst angelegt)
`pinning`, `call-wall-put-wall`, `zero-gamma-flip`, `gamma-regime`, `volatility-skew`, `triple-witching`, `opex-drift`, `0dte`, `fund-flow-seasonality`. Jeweils mit peer-reviewed Anker aus obiger Grounding-Liste.

# Saisonalität × Options-/Markt-Flows — der SeasonAlpha-Moat

> Synthese-Memo · erstellt 2026-08-01 · Quellen: `raw/papers/` (Goldman/Rocky-Fishman-OpEx-Primer, Ambrus/Sidial,
> Volland WP+UG, SpotGamma), `median month flow.jpg`, Web-Recherche (OPEX-Week-Effekt, Turn-of-Month, Buyback-Blackout)
> + eigener Stack (`scripts/compute_gamma_exposure.py`, OPEX/VIX/Earnings/TDOM-Kalender, normierte Renditen).
> Ziel: KOMBINIERTE Features, die **weder reine GEX-Vendoren (SpotGamma/Volland) noch reine Saisonalitäts-Seiten** haben.

---

## 0. Die Moat-These in einem Satz

**GEX-Vendoren zeigen den Flow im Jetzt; Saisonalitäts-Seiten zeigen das Kalender-Muster im Mittel.
Niemand verheiratet beide.** SpotGamma weiß, dass „Pre-OpEx meist bullish" ist — aber nicht, wie stark
*bedingt auf das aktuelle Gamma-Regime* oder *bedingt auf den Handelstag-im-Monat (TDOM)*. Saisonalitäts-Seiten
zeigen die Monats-Heatmap — aber nicht, *warum* (Charm/Vanna/Buyback-Blackout treiben die Wochen).
Unser einziger Rohstoff, den beide Lager NICHT haben: **börsengenauer Kalender (OPEX/VIX/Triple-Witching/Earnings/TDOM)
× normierte Renditen über Jahrzehnte × naive-GEX-Engine.** Genau der Schnitt ist verteidigbar.

Das ist auch die These aus `docs/OPTIONS.md`: „Gamma/Vanna/Charm sind der **Mechanismus dahinter** — aus *Muster* wird
*Warum*." Dieses Memo zieht das konsequent auf **Kombi-Studien** durch, nicht nur auf eine `/gamma`-Seite.

**Ehrliche Daten-Leitplanke vorab** (gilt für JEDES Feature unten):
- Unsere GEX/Vanna/Charm ist **naive Dealer-Heuristik auf EOD-Yahoo-OI** — nicht SpotGammas/Vollands Inventory-Modell.
- **0DTE/Intraday-Flows, echte Dealer-Bücher, Fondsfluss-Ist-Daten (EPFR/ICI), Buyback-Ausführung sind PAID** und
  hier NICHT baubar. Wir approximieren mit Kalender-Logik + normierten Renditen. Immer als „Referenz, kein Signal" labeln.
- **GEX-Historie fehlt uns noch** (wir *snapshoten* erst seit ~2026-07; `gex_*.json` ist ein Live-Stand, keine Zeitreihe).
  Jede Studie, die *historisches* GEX-Regime braucht, muss ehrlich sagen: „Regime aktuell live, Rückrechnung nur ab
  Snapshot-Beginn" ODER auf einen **Proxy** (Realized-Vol-Regime, VIX-Level als GEX-Stellvertreter) ausweichen. Das ist
  der wichtigste Ehrlichkeits-Punkt — siehe Feature 2.

---

## 1. Die 8 Kombi-Features (nach Hebel sortiert)

### ⭐ Feature 1 — „Pre-OPEX-Drift × Gamma-Regime" (die Flaggschiff-Studie)

- **Idee:** Reproduziere den bekannten OPEX-Week-Effekt (S&P-Woche vor dem 3. Freitag hat historisch überdurchschnittliche
  Rendite — QuantifiedStrategies: ~+0,2 %/Woche, aber der *Verfalls-Freitag selbst* ist schwach), **aber bedingt auf zwei
  eigene Achsen, die kein Vendor kombiniert:** (a) net-GEX-Regime long vs. short Gamma, (b) monatlich vs. Quartals-Triple-Witching.
  Kernaussage-Kandidat: „Die Pre-OpEx-Aufwärtsdrift ist ausgeprägt in Long-Gamma-Regimen (Dealer pinnen/dämpfen) und
  **kehrt sich in Short-Gamma-Regimen um** (Dealer verstärken → Post-OpEx-Schwäche wird zur Pre-OpEx-Fragilität)."
  Ambrus Fig 7 („S&P nur im OpEx-Fenster kaufen → 3 J. −15 %") ist das Muster für die *Post*-OpEx-Schwäche-Hälfte.
- **Datenbasis:** OPEX/Triple-Witching-Kalender **(haben)** + normierte Renditen über Jahrzehnte **(haben)**.
  Das Gamma-Regime-Splitting: für die *Live*-Aussage **haben** wir es (`gex_summary.json` → `regime`); für die *historische*
  Konditionierung fehlt GEX-Historie → **Proxy nötig** (VIX-Regime / Realized-Vol-Terzil als Long/Short-Gamma-Stellvertreter,
  ehrlich gelabelt). Reine Pre/Post-OpEx-Drift ohne Regime-Split ist zu 100 % **haben** und sofort baubar.
- **Aufwand:** M (Kalender-gekoppelter Renditen-Aggregator; Regime-Split als v2). Neu: `scripts/study_opex_drift.py`.
- **Warum einzigartig:** SpotGamma erklärt Mechanik, QuantifiedStrategies zeigt den nackten Effekt — **die Kreuzung
  „Effekt × Regime × Verfallstyp über Jahrzehnte, reproduzierbar" gibt es nirgends frei.** Validiert zugleich unsere
  Charm/Vanna-These empirisch (`docs/OPTIONS.md`).
- **Digital-PR/Backlink:** Hoch. Originäre, zitierbare Daten-Studie = unser #1-Wachstumsengpass (Backlinks). Zahl-getriebener
  Titel („In Short-Gamma-Monaten dreht der OpEx-Effekt — 40 Jahre S&P") ist Reddit/r-Options-, Newsletter- und X-tauglich.

### ⭐ Feature 2 — „Gamma-Regime-Kalender" (Saisonalität des Long/Short-Gamma-Zustands)

- **Idee:** Frage direkt aus dem Prompt („saisonale Muster im Gamma-Regime?"). Heatmap **Kalendermonat/-woche × Anteil Tage
  im Short-Gamma-Regime**. Hypothese aus der Literatur: Short-Gamma/hohe-Fragilität clustert im **Spätsommer/Frühherbst
  (Aug–Okt)** — passt zu bekannter Sept/Okt-Schwäche und dünner Liquidität. Ergänzt um **Skew-Saisonalität** (ist Put-Skew
  saisonal steiler vor Q4?).
- **Datenbasis:** **Ehrliche Grenze — hier ist die Datenlage am dünnsten.** Echte GEX-Historie **haben wir NICHT** (Snapshots
  erst seit ~07/2026). Zwei ehrliche Wege: (1) **Proxy-Regime** aus VIX-Level + Realized-Vol (frei, lange Historie) als
  Short/Long-Gamma-Stellvertreter — sauber als Proxy labeln. (2) Ab jetzt **GEX-Snapshots als Zeitreihe archivieren**
  (billiger Cron: täglich `gex_summary.json` → Supabase-Tabelle `gex_history`) und die *echte* Regime-Saisonalität in
  12–24 Monaten liefern. Skew-Saisonalität: ATM-IV + 90/110-Skew **haben wir** live, Historie via denselben Snapshot-Cron.
- **Aufwand:** S (Proxy-Version + Snapshot-Cron einrichten) / L (echte Historie = Zeit, nicht Arbeit).
- **Warum einzigartig:** „Wann im Jahr ist der Markt strukturell fragil (short gamma)?" beantwortet **kein** Vendor —
  sie sind alle Momentaufnahme-Tools ohne Kalender-Aggregation. Der Snapshot-Cron ist ein **Daten-Moat, der mit der Zeit wächst**
  (in 2 Jahren haben wir eine proprietäre GEX-Regime-Zeitreihe, die niemand frei hat).
- **Digital-PR/Backlink:** Mittel jetzt (Proxy-Studie), **hoch später** (proprietäre Zeitreihe = zitier-Monopol).
  **Sofort-Action-Item unabhängig vom Feature: den Snapshot-Cron HEUTE starten**, damit die Historie zu laufen beginnt.

### ⭐ Feature 3 — „Turn-of-Month × TDOM-Flow-Fenster" (Kalender-Flow-Kopplung)

- **Idee:** Unser TDOM (Handelstag-im-Monat, börsengenau) × die **Fondsfluss-Saisonalität**. Zwei Ebenen:
  (a) **Turn-of-Month:** letzte ~1–4 + erste ~1–3 Handelstage haben erhöhte Rendite (Pension-Contributions + Monatsend-
  Rebalancing fließen zu Monatsbeginn in Aktien — belegt, Quantpedia/ScienceDirect). Wir haben TDOM **börsengenau** →
  können das Fenster *exakt in Handelstagen* definieren (nicht Kalendertagen — unser Kern-Vorteil, CLAUDE.md-Regel).
  (b) **Monats-Layer:** `median month flow.jpg` (Median-Zufluss % AUM in Aktien-Fonds+ETFs 1996–2022: Jan/Feb/Apr/Nov +,
  Jun/Aug/Okt −) als **erklärende Overlay-Kurve** über unsere Monats-Saisonalität.
- **Datenbasis:** TDOM-Kalender + normierte Renditen **(haben, börsengenau)**. Turn-of-Month-Renditefenster = **100 % haben**.
  Der Median-Monatsfluss als Kurve: die *Form* ist aus dem Bild bekannt (illustrativ zitierbar mit Quelle); **echte
  laufende Fondsfluss-Daten = PAID (EPFR/ICI/Lipper)** → wir nutzen die publizierte Muster-Kurve als Kontext, rechnen sie
  NICHT selbst nach. Ehrlich labeln: „Muster nach ICI-Daten, Illustration, nicht live."
- **Aufwand:** S–M (`study_turn_of_month.py`; TDOM-Fenster-Aggregator existiert konzeptuell in `tdom_analysis`).
- **Warum einzigartig:** Turn-of-Month-Seiten gibt es — aber **niemand rechnet es in echten Handelstagen je Börse**
  (die meisten nehmen Kalendertage → falsch bei Feiertagen) UND koppelt es mit der Fondsfluss-*Erklärung*. Das ist die
  „Warum"-Ebene, die uns von generischen Saisonalitäts-Blogs trennt.
- **Digital-PR/Backlink:** Mittel–hoch. „Der Turn-of-Month-Effekt, börsengenau nachgerechnet" + Notenbank/Contribution-
  Narrativ ist ein sauberes, seriöses Studien-Thema (weniger „Zockerei" als GEX → auch für Finanz-Medien anschlussfähig).

### ⭐ Feature 4 — „Buyback-Blackout-Saisonalität" (% des Index im Blackout je Kalendertag)

- **Idee:** Aktienrückkäufe sind der größte einzelne Nachfrager am US-Markt; sie **pausieren im Blackout-Fenster**
  (~4–5 Wochen vor Quartalsende bis 1–2 Tage nach dem Earnings-Release). Ergebnis: **Mitte Sep / Dez / Mär / Jun ist ein
  großer Teil des Index „im Blackout" (Nachfrage-Loch)**, während **Feb/Mai/Aug/Nov (kurz nach Earnings) das Rückkauf-
  Fenster offen ist** (Nachfrage-Peak). Baubares Feature: eine **Kurve „geschätzter % der S&P-500-Marktkap. im Blackout je
  Kalendertag"**, überlagert mit der S&P-Renditen-Saisonalität → visualisiert das Nachfrage-Loch als Erklärung für die
  Herbst-Schwäche.
- **Datenbasis (Scout-verifiziert):** **Solider Proxy OHNE Paid-Daten** aus `earnings_events` (pro Ticker) + Index-Konstituenten.
  Regel: **Blackout = [Earnings − 28 Kalendertage, Earnings + 2 Tage]** (28 = pragm. Mittel der „4–5-Wochen"-Praxis, parametrierbar),
  über ~500 Ticker je Kalendertag zählen → **„% im Blackout"-Tagesreihe** → `data/buyback_blackout.json`. v1 equal-weight,
  v2 Buyback-$-gewichtet (kalibrierbar über das **frei liegende S&P-DJI Buyback-Index-XLSX** auf spglobal.com — grob, quartalsverzögert).
  **Belastbare Peak-Zahl (Deutsche Bank, 04/2024): >80 % der S&P-500-Firmen gleichzeitig im Blackout am Peak vs. <5 % einen Monat davor.**
  **Grenzen (ehrlich):** (1) Wir bauen „Angebots-*Abwesenheit* des Bids", NICHT gekaufte $ (Autorisierung ≠ Ausführung).
  (2) 28-Tage-Regel mittelt firmenindividuelle Fenster — Form der 4-Peaks-Kurve robust, Ist-Level nicht. (3) Earnings-Datums-
  Qualität ist der Flaschenhals (bestätigt vs. geschätzt; Fallback „letztes Quartal + 91 T"). Echte Ausführung = **PAID**
  (S&P Global quartalsweise / Birinyi Autorisierungen / DB-Goldman-JPM tagesgenau = enterprise-only).
  **WICHTIG zur Kausalität:** Der Renditeeffekt ist umstritten — **State Street & CNBC-Faktencheck finden KEINEN signifikant
  negativen Blackout-Return-Effekt.** Also als *strukturellen Flow-Kontext* framen, NICHT als hartes Alpha-Signal.
- **Aufwand:** M (`study_buyback_blackout.py`: Earnings-Termine → Fenster-Overlap → marktkap.-gewichtete Tageskurve).
- **Warum einzigartig:** **Das hat NIEMAND als tägliche, aus Earnings-Terminen abgeleitete Kurve** — Banken publizieren nur
  gelegentliche Blackout-Kalender-Grafiken hinter Paywall. Wir bauen sie **aus eigenen Daten reproduzierbar** und koppeln
  sie an die Saisonalität. Das ist der reinste „Flow × Saisonalität"-Moat: strukturelle Nachfrage-Ebbe/Flut als Kalender.
- **Digital-PR/Backlink:** **Sehr hoch.** „Warum der Markt im September schwächelt: das Buyback-Blackout-Loch" ist ein
  starkes, medien-anschlussfähiges Narrativ (Rückkäufe sind Mainstream-Thema). Klar zitierbar, teilbar, kontrovers genug.

### Feature 5 — „Triple-Witching Post-OpEx-Schwäche" (Ambrus Fig 7, reproduziert & seziert)

- **Idee:** Fokussierte Reproduktion von Ambrus Fig 7 speziell für **Quartals-Triple-Witching** (Mär/Jun/Sep/Dez): die
  Goldman-Beobachtung „Quartals-Verfälle bauen bis ~$2 Bio OI auf; das *Aufräumen* triggert Re-Alignment" → messbar als
  **systematische Post-Triple-Witching-Woche-Schwäche** vs. normale Monats-OpEx. Split nach Verfallsgröße (Quartal vs Monat).
- **Datenbasis:** Triple-Witching-Kalender + normierte Renditen **(haben, 100 %)**. Kein Paid nötig.
- **Aufwand:** S–M (Teilmodul von Feature 1; separat als eigene Studie/Blog vermarktbar).
- **Warum einzigartig:** Verbindet die *Goldman-Mechanik-Erklärung* (großes OI, Cleanup-Catalyst) mit *unserer Langfrist-
  Empirie*. Reine Seasonality-Seiten kennen „Triple Witching" als Datum, nicht als quantifizierten Rendite-Effekt.
- **Digital-PR/Backlink:** Mittel. Guter Blog/Video-Baustein (4×/Jahr wiederkehrender, kalendergetriggerter Content-Anlass).

### Feature 6 — „VIXpiration × Skew-Term-Structure-Saisonalität"

- **Idee:** VIXpiration (OPEX-Freitag − 30 Kalendertage, unser Kalender) als eigener Flow-Termin. Kombi: **saisonales Muster
  in Skew/Term-Structure** um VIXpiration + monatlich. Chart: IV über Expirationen + 90/110-Skew-Kurve, **Backwardation-Flag**,
  überlagert mit Earnings/FOMC aus unserem Kalender („near-term IV erhöht wegen Earnings/FOMC am …") und mit dem VIXpiration-Datum.
- **Datenbasis:** ATM-IV + 90/110-Skew pro Term **live haben** (`compute_gamma_exposure.py`); VIX/VIXpiration-Kalender **haben**.
  Saisonale *Historie* der Skew → gleicher Snapshot-Cron wie Feature 2 (Proxy: ^VIX/^SKEW frei, lange Historie).
- **Aufwand:** M (Skew-Term-Chart + Event-Overlay; `/vixpiration`-Anknüpfung).
- **Warum einzigartig:** Kombiniert Vola-Struktur-Analyse (SpotGamma-Territorium) mit **unserem Verfalls-Kalender + Event-Overlay**
  in einem Bild — Vendoren zeigen Skew ohne Kalender-Kontext, Saisonalitäts-Seiten zeigen kein Skew.
- **Digital-PR/Backlink:** Niedrig–mittel (nischig, aber gut für Fach-Publikum/Substack-Erwähnungen).

### Feature 7 — „VIX-up/Market-up × Saisonalität" (antizyklischer Vola-Detektor)

- **Idee:** SG-„VIX up, Market up"-These (Call-FOMO treibt VIX MIT dem Markt). **Detektor:** Tage mit SPY-Return >0 UND
  VIX-Change >0. **Kombi-Twist:** Häufigkeit dieser Tage **je Monat/TDOM** (Saisonalität) + optional bedingt auf Gamma-Regime.
  Hypothese: gehäuft in FOMO-/Melt-up-Phasen (Q4-Jahresend-Rally, Januar).
- **Datenbasis:** SPY + ^VIX **(haben, lange Historie)** → **100 % baubar, sofort**. Optional ^SKEW/VVIX als Kontext (frei/patchy).
- **Aufwand:** S (`study_vix_up_market_up.py`).
- **Warum einzigartig:** Widerspricht der Alltags-Intuition „VIX = Angst" → starker Erklär-/Content-Hook, und der
  **saisonale + Regime-Split** ist der originäre Dreh (SG zeigt nur das Phänomen, nicht *wann im Jahr*).
- **Digital-PR/Backlink:** Mittel (kontraintuitiv = teilbar; einfachster Quick-Win der Liste).

### Feature 8 — „OpEx-Woche live: Charm-Range × TDOM-Overlay" (Produkt-Feature, nicht Studie)

- **Idee:** Auf `/opex` bzw. `/gamma`: in der laufenden OpEx-Woche das **live Charm/Vanna-Bild** („Lines in the Sand" =
  größter neg./pos. Charm-Strike als Referenz-Range) **neben** die *historische* TDOM-Drift-Kurve für genau diese Woche
  stellen. Nutzer sieht „Muster (historisch) + Mechanik (heute live)" in einem Screen.
- **Datenbasis:** Charm-per-Strike **live haben**; TDOM-Drift **haben**. EOD/Index (0DTE-Intraday NICHT möglich — ehrlich labeln).
- **Aufwand:** M (Frontend-Kombi-Panel; setzt die noch fehlende `/gamma`-Seite voraus, s. `docs/OPTIONS.md` Roadmap).
- **Warum einzigartig:** Das ist die **sichtbare Produkt-Manifestation des Moats** — Muster + Warum nebeneinander, wiederkehrend
  jede OpEx-Woche. Kein Vendor zeigt die historische Kalender-Drift; keine Saisonalitäts-Seite zeigt live Charm.
- **Digital-PR/Backlink:** Indirekt (Retention/Screenshot-Sharing, Video-Vorlage jede OpEx-Woche → YouTube-Pipeline-Futter).

---

## 2. Priorisierung (Aufwand × Hebel × Daten-Sicherheit)

| Rang | Feature | Daten sicher? | Aufwand | PR-Hebel | Sofort startbar? |
|---|---|---|---|---|---|
| 1 | **Pre-OpEx-Drift × Gamma-Regime** (F1) | Drift ja / Regime-Split via Proxy | M | ★★★ | ✅ (Drift-Kern sofort) |
| 2 | **Buyback-Blackout-Saisonalität** (F4) | Approx. aus earnings_events | M | ★★★ | ✅ (nach Scout-Check) |
| 3 | **Turn-of-Month × TDOM** (F3) | ja (Fluss-Kurve illustrativ) | S–M | ★★☆ | ✅ |
| 4 | **VIX-up/Market-up × Saison** (F7) | ja (SPY+^VIX) | S | ★★☆ | ✅ (Quick-Win) |
| 5 | **Triple-Witching-Schwäche** (F5) | ja | S–M | ★★☆ | ✅ |
| 6 | **Gamma-Regime-Kalender** (F2) | **nein** (GEX-Historie fehlt) | S jetzt / L echt | ★★☆→★★★ | ⚠️ Proxy jetzt, echt später |
| 7 | **VIXpiration × Skew-Saison** (F6) | live ja / Historie Proxy | M | ★☆☆ | teilweise |
| 8 | **OpEx-Charm × TDOM-Panel** (F8) | live ja | M | ★☆☆ (Retention) | nach `/gamma` |

---

## 3. Das eine Sofort-Action-Item (unabhängig von Feature-Reihenfolge)

**GEX-Snapshot-Cron JETZT starten:** täglich `gex_summary.json` (net-GEX, Regime, Zero-Gamma, Walls, Vanna, Charm, ATM-IV,
90/110-Skew je Ticker) in eine Supabase-Tabelle `gex_history` schreiben. Das ist billig (der Compute läuft ohnehin schon),
aber jeder Tag, den wir *nicht* archivieren, ist eine Zeitreihe, die uns für immer fehlt. In 12–24 Monaten ist das eine
**proprietäre GEX-Regime-/Skew-Zeitreihe, die kein freier Wettbewerber hat** — das ist der einzige Feature-Baustein hier,
dessen Wert rein durch *Warten ab heute* entsteht. Er entriegelt die *echten* (nicht Proxy-)Versionen von F1, F2, F6.

## 4. Ehrlichkeits-Register (YMYL — in JEDES Feature/Blog/Video übernehmen)

- Naive Dealer-Heuristik auf EOD-Yahoo-OI ≠ SpotGamma/Volland-Inventory-Modell → „Referenz, keine Barriere, kein Signal".
- **PAID / nicht baubar:** 0DTE- & Intraday-Flows; echte Fondsfluss-Ist-Daten (EPFR/ICI/Lipper); echte Buyback-Ausführung
  (S&P Global/Birinyi/Bank-Desks); echte historische GEX-Regime (bis unser Snapshot-Cron Historie aufgebaut hat).
- **Approximiert (ehrlich labeln):** Buyback-Blackout (aus Earnings-Terminen + fixer Fenster-Regel); Fondsfluss-Kurve
  (publizierte ICI-Muster als Illustration); Gamma-Regime-Historie (VIX/RV-Proxy bis echte Snapshots reichen).
- **DAX/`.DE`/`^GDAXI`:** Yahoo liefert keine Options-Chain → Gamma nur für US-gelistete Underlyings; EU nur mit Paid-Feed.
- **OPEX-Effekt-Deterioration:** die reine OpEx-Woche-Outperformance hat sich über die letzten ~4 Jahre abgeschwächt
  (QuantifiedStrategies) — in Studien-Texten fair erwähnen, nicht überverkaufen.

## 5. Quellen (Web-Recherche)

- OPEX-Week-Effekt & Verfalls-Freitag-Schwäche: [QuantifiedStrategies](https://www.quantifiedstrategies.com/options-expiration-week/),
  [Quantpedia — Option-Expiration Week Effect](https://quantpedia.com/strategies/option-expiration-week-effect),
  [gexmetrix — OPEX Quarterly Effects](https://www.gexmetrix.com/blog/opex-quarterly-effects)
- Turn-of-Month / Month-End-Rebalancing: [Quantpedia — Turn of the Month](https://quantpedia.com/strategies/turn-of-the-month-in-equity-indexes),
  [ScienceDirect — Infrequent rebalancing at the turn of the month](https://www.sciencedirect.com/science/article/abs/pii/S1042443126000259),
  [Tickmill — Goldman Month-End Rebalancing Flows](https://www.tickmill.com/blog/institutional-insights-goldman-sachs-month-end-rebalancing-flows-to-know)
- Interne Primär-Quellen: `raw/papers/` (Goldman/Rocky-Fishman „All You Ever Wanted To Know About Gamma, Op-Ex…";
  Ambrus/Sidial Fig 7; Volland WP+UG; SpotGamma „What is Gamma"/„Vol Checklist"/„VIX up Market up"; `median month flow.jpg`),
  `docs/OPTIONS.md`, `scripts/compute_gamma_exposure.py`, `landing/data/gex_summary.json`.
- Buyback-Blackout (Scout-verifiziert): [Deutsche Bank — >80 % im Blackout (Bloomberg)](https://www.bloomberg.com/news/articles/2024-04-11/s-p-500-is-heading-for-a-rough-patch-as-buyback-blackouts-arrive),
  [State Street — Blackout impact-neutral (PDF)](https://www.ssga.com/library-content/pdfs/etf/us/b27-buyback-blackout-periods-do-not-negatively-impact-performance.pdf),
  [CNBC — Blackout-Schwäche-Mythos](https://www.cnbc.com/2018/04/11/rumor-buyback-blackouts-mean-weak-stocks-fact-not-really.html),
  [S&P DJI Buyback-Index (freies XLSX/Methodik)](https://www.spglobal.com/spdji/en/indices/dividends-factors/sp-500-buyback-index/),
  [Wall Street Horizon — Buybacks top-heavy 2025](https://www.wallstreethorizon.com/blog/2025-Buyback-Spree-is-Top-Heavy-as-Fewer-Firms-Repurchase-Shares)

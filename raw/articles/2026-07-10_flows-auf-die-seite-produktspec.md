# Produkt-Spec: Strukturelle Flows auf die Website (`/flows`)

> erstellt 2026-07-10 · für `sa-ingest` · Autor: market-flows-scout
> Ziel: die bereits recherchierte Flow-Analyse in eine baubare Seite/Feature gießen — nur freie Quellen,
> Stack = Python-Batch → Supabase/`landing/data/*.json` → statisches ApexCharts-Frontend. Keine teuren Feeds.
> Abgeglichen mit Bestehendem: `compute_gamma_exposure.py`→`gex_*.json` (Dealer-Greeks, Seite fehlt noch),
> `build_calendar_data.py`→`market_calendar.json`, `fetch_event_data.py`→Supabase `earnings_events`,
> `sektor-rotation.html` (23 US-Sektor-ETFs XLK/XLF/XLE…), OPEX/VIX-Kalender, Saisonalitäts-Seiten.

---

## 0. Leitentscheidung: EINE `/flows`-Seite als Dach, KEINE Zersplitterung

`/flows` = neue statische Page (Muster: `sektor-rotation.html`). Sie bündelt 5 Panels (unten). Die schon
vorhandene **Dealer-Gamma-Engine bekommt ihre EIGENE `/gamma`-Seite** (Daten liegen, siehe Papers-Inventar) —
`/flows` verlinkt nur dorthin, dupliziert GEX nicht. Zwei Kalender-Events (Index-Rebalancing) wandern
zusätzlich in `market_calendar.json`, damit sie auch unter `/kalender` und im Daily-Newsletter auftauchen.

Grund: alle fünf Flows teilen denselben Rahmen ("mechanischer, nicht-fundamentaler Bid/Ask") und dieselben
Ehrlichkeits-Disclaimer — als eine Seite erzählbar, SEO-fokussiert ("strukturelle Marktflüsse"), ein Cron-Bündel.

---

## 1. Panels (5) — Mechanik, Chart, Datenpfad

Reihenfolge = Anordnung auf der Seite (oben = höchster Nutzen/niedrigster Aufwand).

### Panel A — Index-Rebalancing-Kalender (Timeline + "nächstes Event")
- **Mechanik:** An fixen Terminen zwingen Index-Fonds (S&P, Russell) zu mechanischem Kauf/Verkauf, um dem neuen
  Index-Gewicht zu folgen. **S&P DJI: vierteljährlicher Rebalance = 3. Freitag Mar/Jun/Sep/Dez = deckt sich EXAKT
  mit Triple Witching** (haben wir schon als `opex`/`triple_witching`). **FTSE Russell Reconstitution: einmal
  jährlich, wirksam nach Schluss am letzten Freitag im Juni** (Ankündigungen Mai/Juni) — riesiges Volumen-Event.
  Timing/Saison: Volumen-Spike am Close des Effective-Day, oft Vorlauf-Drift in den Reconstitution-Namen.
- **Chart:** horizontale Timeline (ApexCharts rangeBar oder simple Event-Liste wie `/kalender`) mit Countdown
  "nächstes Rebalancing in N Handelstagen". Badge-Farbe je Typ (S&P quarterly / Russell annual).
- **Quelle (frei):** reine Termin-Logik, KEIN Scrape nötig.
  - S&P quarterly = wir berechnen den 3. Freitag schon (`shared/nyse_holidays.get_all_opex_dates`, Triple-Witching-Monate).
  - Russell recon = "letzter Freitag im Juni" + Announcement-Termine → deterministisch in Python berechenbar.
    Offizielle Bestätigung/Schedule zum Quervergleich: FTSE Russell Reconstitution-Seite (frei, 1×/Jahr manuell prüfen).
- **Skript:** in `scripts/build_calendar_data.py` **2 neue Event-Typen** ergänzen:
  `add(dt,"sp_rebalance","S&P Rebalancing","S&P DJI Quartals-Rebalance · = Triple Witching",emoji="⚖️")` und
  `add(russell_effective,"russell_recon","Russell Reconstitution","FTSE Russell Jahres-Rekonstitution",emoji="⚖️")`.
- **Output:** fließt in bestehendes `landing/data/market_calendar.json` (Event-Schema `{date,type,name,detail,emoji}`),
  `/flows` liest denselben JSON und filtert `type in ('sp_rebalance','russell_recon','triple_witching')`.
- **Feasibility: ✅** (pure Kalender-Arithmetik, null neue Datenquelle, recyclet Kalender-Infra).

### Panel B — Buyback-Blackout-Zeitreihe ("% der Marktkap. im Blackout")
- **Mechanik:** ~4-6 Wochen vor Earnings dürfen Firmen keine eigenen Aktien zurückkaufen (Blackout). Buybacks sind
  ein struktureller Dauer-Bid; im Blackout fehlt er → der Markt ist fragiler/dünner. Aggregiert man die Blackout-
  Fenster aller großen Firmen, entsteht eine **Saison-Kurve des "fehlenden Bids"** (Hochs typ. ~2 Wochen vor der
  Masse der Quartals-Earnings, also Anfang jeder Earnings-Saison: Mitte Jan/Apr/Jul/Okt).
- **Chart:** Zeitreihe (ApexCharts area), y = "% der aggregierten Marktkap. aktuell im Blackout", x = Datum (±90 Tage),
  Peaks farbig markiert. Darunter Tabelle "diese Woche neu im Blackout".
- **Quelle (frei):** wir haben **`earnings_events` in Supabase schon befüllt** (`fetch_event_data.py`, Yahoo).
  Blackout-Fenster je Ticker = `[earnings_date − 35 Kalendertage, earnings_date + 2]` (Standard-Heuristik; echte
  Policy variiert je Firma → als Proxy labeln). Gewicht = Marktkap. (Yahoo `quote…marketCap`, einmal je Ticker cachen).
- **Skript:** neu `scripts/build_buyback_blackout.py` — liest `earnings_events` (nächste ~90 Tage) für das
  Kern-Universum (Dow-30/DAX-40/Nasdaq-100-Schnittmenge aus `symbols.py`), baut je Handelstag die Summe der
  Marktkap. im Blackout / Gesamt-Marktkap. Full-Universe-Loop → `download_data.clear()` + `gc.collect()` pro Ticker.
- **Output:** `landing/data/buyback_blackout.json`
  `{"generated_at":..., "series":[{"date":"2026-08-03","pct_mktcap_in_blackout":0.31,"n_companies":142}], "entering_this_week":[{"ticker":"AAPL","blackout_start":"...","earnings_date":"..."}], "note":"Proxy: Blackout=Earnings−35T…+2T, echte Firmen-Policy variiert; Autorisierung≠Ausführung"}`.
- **Feasibility: ✅** (Daten in-house, nur Aggregation). Wichtigster ORIGINÄRER Flow — den zeigt kein Retail-Tool frei.

### Panel C — ETF-Flow-Heatmap (Sektor-Rotation, Risk-on/off)
- **Mechanik:** Creations/Redemptions = tägliche Änderung der ausstehenden Anteile (Shares Outstanding) eines ETF.
  ΔShsOut × NAV ≈ Netto-Kapitalzufluss. Über Sektor-ETFs gelegt zeigt es **Rotation** (Geld rein XLK, raus XLE) und
  Risk-on/off (SPY/QQQ-Zuflüsse vs. Defensive/Bonds). Timing: Monatsende-/Quartals-Cluster.
- **Chart:** Heatmap Sektor × Woche (grün Zufluss / rot Abfluss), Muster wie unsere Saison-Heatmaps
  (`apply_se_heatmap_theme`-Ästhetik im Frontend via ApexCharts). Plus "Top-Zufluss/Abfluss diese Woche"-Balken.
- **Quelle (frei):** zwei Wege, beide frei:
  1. **Issuer-CSV (sauberste ShsOut):** SSGA/State Street SPDR listet je Sektor-ETF (XLK/XLF/XLE… — die 23 aus
     `sektor-rotation.html`) tägliche "Shares Outstanding" + NAV als Fund-Detail/CSV auf ssga.com/sectorspdrs.com.
     iShares (blackrock.com) und Invesco liefern analoge Holdings/ShsOut-Downloads.
  2. **Proxy ohne Scrape:** Yahoo `quote`-Feld `sharesOutstanding` je ETF täglich snapshotten → ΔShsOut × Close.
     Gröber (Yahoo aktualisiert ShsOut träge) → ehrlich als Proxy labeln.
- **Skript:** neu `scripts/build_etf_flows.py` — täglich je Sektor-ETF ShsOut + NAV holen, in Supabase-Tabelle
  `etf_flows(date,ticker,shares_out,nav,flow_usd)` upserten (Historie!), dann Wochen-Aggregat als JSON exportieren.
- **Output:** `landing/data/etf_flows.json`
  `{"generated_at":..., "weeks":["2026-W30",…], "sectors":[{"ticker":"XLK","name":"Technology","flows_usd_mn":[…perWoche…]}], "note":"Flow=ΔSharesOutstanding×NAV; Quelle Issuer-CSV bzw. Yahoo-ShsOut (träge) → Näherung"}`.
- **Feasibility: ⚠️→✅** (Issuer-CSV-Formate ändern sich gelegentlich → Scraper pflegen; Yahoo-ShsOut-Weg ist
  sofort baubar aber gröber. Start mit Yahoo-Proxy, später Issuer-CSV upgraden).

### Panel D — COT Managed-Money-Net (CTA-Proxy)
- **Mechanik:** Systematische Trendfolger (CTAs) sind long in Aufwärts-, short in Abwärtstrends; ihr Umschalten
  verstärkt Moves (Sell-Trigger bei Trendbruch/Vol-Spike). Echte CTA-Positionierung ist nicht frei — **CFTC COT
  "Managed Money" / "Leveraged Funds" im E-mini S&P 500 ist die beste freie NÄHERUNG.**
- **Chart:** Zeitreihe Net-Position (Kontrakte) + darüber gelegtes einfaches Trendsignal (Preis vs. 50/200-Tage-SMA
  aus unseren SPX-Daten) als "CTA-Ampel" (long/neutral/short-Bias).
- **Quelle (frei):** **CFTC Public Reporting — "Traders in Financial Futures" (TFF), wöchentlich, Socrata-API/CSV**
  (publicreporting.cftc.gov). Feld: Asset-Manager + Leveraged-Funds Long/Short in S&P-500-Futures.
- **Skript:** neu `scripts/build_cot_positioning.py` — Socrata-JSON (Query auf S&P-500-Kontrakt) ziehen, letzte
  ~3 Jahre, Net = Long−Short, + Trend-Overlay aus `download_data('^GSPC')`-SMA.
- **Output:** `landing/data/cot_positioning.json`
  `{"generated_at":..., "series":[{"date":"2026-07-29","lev_funds_net":-45000,"asset_mgr_net":120000}], "trend":{"sma50_above_sma200":true}, "note":"CFTC COT ≠ echte CTA-Position — nur Näherung; wöchentlich, 3 Tage Meldeverzug"}`.
- **Feasibility: ✅** (offizielle Gov-API, stabil). **Proxy-Ehrlichkeit kritisch** (COT ≠ CTA).

### Panel E — Vol-Control-Leverage-Proxy (Richtung, NICHT $-Menge)
- **Mechanik:** Target-Vol-/Risk-Parity-Fonds skalieren ihr Exposure invers zur realisierten Vola: Vola rauf →
  mechanisches De-Leveraging (Verkäufe verstärken den Selloff), Vola-Beruhigung → Re-Leveraging (Bid). Timing:
  Auslöser sind Vol-Spikes, nicht der Kalender.
- **Chart:** Zeitreihe "impliziertes Leverage" = `Ziel-Vol(z.B. 15%) / realisierte 20-Tage-Vol(^GSPC)`, gekappt bei
  ~150%. Fällt = De-Leveraging-Druck (rot), steigt = Re-Leveraging (grün). Optional VIX/VIX3M-Term-Struktur-Overlay.
- **Quelle (frei):** nur `^GSPC` (haben wir) für realisierte Vola; optional `^VIX`/`^VIX3M` (Yahoo) für Term-Struktur.
- **Skript:** neu `scripts/build_volcontrol_proxy.py` — realisierte 20T-Vola annualisiert, Leverage-Formel,
  Historie als JSON. Reiner Rechenschritt, kein externer Feed.
- **Output:** `landing/data/volcontrol_proxy.json`
  `{"generated_at":..., "series":[{"date":"2026-07-31","realized_vol_20d":0.11,"implied_leverage":1.36}], "note":"Modell-Proxy: Ziel-Vol/realisierte Vol. Zeigt RICHTUNG des De/Re-Leveragings, NICHT die $-Menge oder echte Fonds-Bücher"}`.
- **Feasibility: ✅** (nur Rechnen auf vorhandenen Daten). Aber am ehesten "Modell" statt "Messung" → klar labeln.

---

## 2. Priorisierung (Aufwand/Nutzen) — die 2 zuerst

| Panel | Flow | Beste freie Quelle | Aufwand | Nutzen | Verdikt |
|---|---|---|---|---|---|
| **B** | Buyback-Blackout | `earnings_events` (schon in DB) + Yahoo marketCap | **S** | **hoch** (originär, kein Gratis-Retail-Tool zeigt das) | ✅ **ZUERST** |
| **A** | Index-Rebalancing-Kalender | pure Kalender-Arithmetik (S&P=Triple-Witching, Russell=letzter Jun-Fr) | **S** | hoch (verzahnt Saison+OPEX+Kalender) | ✅ **ZUERST** |
| **D** | COT Managed-Money | CFTC TFF Socrata-API | M | mittel-hoch | ✅ danach |
| **E** | Vol-Control-Proxy | `^GSPC` realisierte Vola (in-house) | S | mittel (Modell) | ✅ danach |
| **C** | ETF-Flows | Issuer-CSV / Yahoo-ShsOut-Proxy | M-L | hoch, aber Scraper-Pflege | ⚠️ zuletzt (Yahoo-Proxy-Start) |

**Die zwei zuerst: B (Buyback-Blackout) + A (Rebalancing-Kalender).** Beide sind Aufwand "S", nutzen ausschließlich
bereits vorhandene Infrastruktur (Supabase `earnings_events` bzw. die Kalender-Arithmetik), brauchen KEINE neue
externe Datenquelle und liefern sofort ein originäres, saisonal verzahntes Bild. Danach D (COT, stabile Gov-API)
und E (Vol-Control, reiner Rechenschritt). C zuletzt, weil Issuer-CSV-Scraper laufende Pflege bedeuten — Start mit
dem gröberen Yahoo-ShsOut-Proxy.

---

## 3. Ehrliche Labels (Disclaimer-Block auf `/flows`, YMYL)

Fixer Info-Kasten oben auf der Seite + `note`-Feld in jedem JSON (Frontend rendert es als Tooltip/Fußnote):
- **Buyback-Blackout:** "Blackout-Fenster = Heuristik (Earnings −35 bis +2 Tage); echte Firmen-Policy variiert.
  Rückkauf-**Autorisierung ≠ Ausführung** — Firmen müssen nicht ausschöpfen. Zeigt fehlenden strukturellen Bid, kein Signal."
- **COT/CTA:** "**CFTC COT ≠ echte CTA-Positionierung** — nur Näherung über Managed-Money/Leveraged-Funds. Wöchentlich,
  ~3 Tage Meldeverzug. Kein Live-Bild."
- **Vol-Control:** "**Modell-Proxy** aus realisierter Vola. Zeigt die **Richtung** des De-/Re-Leveragings, NICHT die
  $-Menge und nicht die echten Fonds-Bücher."
- **ETF-Flows:** "Flow = ΔShares-Outstanding × NAV. Yahoo-ShsOut aktualisiert träge → Näherung; Issuer-CSV genauer."
- **Rebalancing:** "Termine sind fix; die **Größe** der Umschichtung schätzt die Seite nicht (dafür bräuchte es
  Index-Gewichtsänderungen aus Bezahl-Feeds)."
- Übergreifend: alle Panels = **strukturelle, nicht-fundamentale Flows**, keine Kauf-/Verkaufsempfehlung
  (kanonisch: `docs/YOUTUBE_DISCLAIMER.md`-Linie).

---

## 4. Anknüpfung an Saisonalität / Kalender / Regime

- **Rebalancing = Triple Witching:** Panel A macht sichtbar, dass der S&P-Quartals-Rebalance auf denselben 3. Freitag
  (Mar/Jun/Sep/Dez) fällt wie Triple Witching — direkte Brücke zu `/opex` und zur Ambrus-"Post-OPEX-Schwäche"-Studie
  (siehe `raw/articles/2026-07-10_papers-inventar-optionen.md`, Empfehlung #2). Cross-Link setzen.
- **Buyback-Saison ↔ Earnings-Kalender:** Panel B leitet sich direkt aus `earnings_events` ab → die Blackout-Peaks
  liegen definitionsgemäß am Anfang jeder Earnings-Saison. Cross-Link zu `/earnings-kalender` und zur Monats-Saisonalität
  (fehlender Buyback-Bid als mögliche Teilerklärung schwacher Fenster).
- **Monatsend-/Quartals-Flows:** Panel C (ETF-Flows) + generelles Rebalancing clustern zum Monats-/Quartalsende →
  Anknüpfung an `/monatswechsel` (Turn-of-Month-Effekt bekommt eine *Flow-Begründung*, nicht nur ein Muster).
- **Regime-Ampel:** Panel D (COT-Trend-Bias) + Panel E (Vol-Control-Leverage) sind natürliche Zusatz-Inputs für die
  Crash-Frühwarnung/Regime-Logik (`compute_regime_scores.py`): short-Gamma (aus `/gamma`) + De-Leveraging (E) +
  Blackout-Peak (B) = "fragiles Fenster". Als qualitativer Kontext-Block auf `/crash-fruehwarnung` verlinkbar.
- **Dealer-Gamma:** `/flows` verlinkt auf die separate `/gamma`-Seite (GEX/Vanna/Charm, `gex_*.json` liegt bereit) —
  nicht duplizieren.

---

## 5. Bau-Reihenfolge / Definition of Done (konkret)

1. **Panel B + A** (Sprint 1): `scripts/build_buyback_blackout.py` + Event-Erweiterung in `build_calendar_data.py`;
   `/flows`-Page-Gerüst (nach Muster `sektor-rotation.html`: Nav via `loadComponent`, Supabase-Inline-Script vor
   `app.js`, `data-i18n(-html)` + EN-Keys in `en.json`, `_EN_PAGE_META`-Eintrag in `build_en.py`, FAQPage-Schema).
   Cron: an Nightly anhängen (Blackout nach `fetch_event_data`, Kalender im Deploy via `docker exec`).
2. **Panel D + E** (Sprint 2): `build_cot_positioning.py` (wöchentlich, eigener Cron) + `build_volcontrol_proxy.py`
   (an Nightly). JSON nach `landing/data/`.
3. **Panel C** (Sprint 3): `build_etf_flows.py` — Start Yahoo-ShsOut-Proxy + Supabase-Tabelle `etf_flows` für Historie;
   später Issuer-CSV.
- **Gotchas beachten (CLAUDE.md):** Full-Universe-Loops → `download_data.clear()` + `gc.collect()` pro Ticker (OOM);
  `fetch('/data/…')` VERBOTEN → immer `/landing/data/<datei>`; JSON in Container erzeugen + `docker cp`; ApexCharts
  Multi-Serie als plain arrays mit `null`; UTC via `datetime.now(timezone.utc)`.

---

## Kurz-Fazit
`/flows` = ein neues Dach über fünf freie, ehrlich als Proxy gelabelte Flow-Panels. Zwei davon (Buyback-Blackout,
Rebalancing-Kalender) sind mit vorhandener Infrastruktur (Supabase `earnings_events`, Kalender-Arithmetik) sofort und
originär baubar — genau da starten. COT (CFTC-API) und Vol-Control (Rechenschritt) folgen billig; ETF-Flows zuletzt
über den Yahoo-ShsOut-Proxy. Dealer-Gamma bleibt separat auf `/gamma` (Daten liegen). Alles ohne teure Feeds.

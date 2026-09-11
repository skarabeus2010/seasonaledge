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

---

# Options-Plattform (Ausbau 2026-09-06, PRs #198–233)

Die Options-Analysen leben unter dem Top-Level-Nav-Punkt **„Optionen"** (neben „Strategien"): `/skew`, `/iv-surface`, `/key-levels`, `/options-flow`, `/dealer-positioning`, `/flows`, `/spot-vol-beta`. Prinzip: **eine fokussierte Seite pro Analyse** (nicht überfrachten). Alle DE+EN (`data-i18n(-html)` + `en.json` + `_EN_PAGE_META`, `verify_en` FAIL 0).

## Datenquelle: Massive.com (= Polygon.io)

- **Massive.com ist Polygon.io** (umbenannt 30.10.2025; `api.polygon.io` läuft weiter, `api.massive.com` neu). NICHT `joinmassive.com` (fremder Proxy-Dienst).
- **Massive ist die EINZIGE Options-Datenquelle.** marketdata.app wurde nur **evaluiert, nie produktiv eingesetzt** — dort kostet jeder zurückgegebene Kontrakt **1 Credit** (SPX-Voll-Chain = 22.718 Credits, SPY ~4.400 → Voll-Chain-GEX unbezahlbar, tägliches 429-Budget), deshalb der Entscheid für Massive. **Massive = Flatrate / unlimited Calls**: **ein** `GET /v3/snapshot/options/<SYM>?expiration_date.lte=<d>&limit=250` (paginiert via `next_url`, `apiKey`-Query) liefert die **ganze Chain** mit Greeks/IV/**OI** je Kontrakt. **Options-Starter $29/mo** (15-min delayed — für EOD-Crons egal). SPX-Index-Optionen (`I:SPX`) ohne Extra-Plan.
- **Grenzen:** (a) `underlying_asset.price` im Snapshot oft **leer** → Spot via `/v2/aggs/<SYM>/prev` (EOD-Close). (b) **Historisch nur Preise, keine Greeks/IV** → hist. Backfill per BS-Rekonstruktion (ebenfalls aus Massive, siehe unten). (c) Options-Endpoints brauchen den **Options-Plan** (403 NOT_AUTHORIZED sonst — auch über den MCP, der dieselbe Entitlement nutzt).
- **Key = `MASSIVE_API_KEY`** (lokale + Server-`.env`). ⚠️ **Container liest `.env` per docker-compose `env_file` beim START** → nach `.env`-Änderung **`docker compose up -d --force-recreate app`** (sonst „MASSIVE_API_KEY fehlt", 0 Ticker).
- **MCP-Server:** `uv tool install "mcp_massive @ git+https://github.com/massive-com/mcp_massive@v0.10.0"` + `claude mcp add massive -e MASSIVE_API_KEY=… -- mcp_massive` (3 Tools search_endpoints/call_api/query_data + BS-Funktionen; interaktiv, nicht im Cron). Alternative für **historische Greeks/IV**: **ThetaData** ($40-80/mo).

## Universum: `shared/options_universe.py`

**156 US-Ticker** in **9 Themen-Kategorien** (Broad-Index, Sektor-ETF, Rohstoff & Bond, Mag7, AI & Semis, Energie & Grid, Finanzen, Healthcare, Consumer & Growth), **Mehrfach-Zuordnung** (NVDA ∈ Mag7 ∩ AI). Helper `all_option_tickers()`/`categories_for()`. **NUR US** (Optionen gibt's nicht auf `.DE`/`.OL`). Alle in `symbols.py` → Kursreihen für VRP/realized vorhanden. Frontend: **Kategorie-Umschalter** filtert Radar/Tabelle/VRP/Vol-Trigger — hält die Übersicht.

## Seiten & Pipelines

| Seite | Skript → Daten | Inhalt |
|---|---|---|
| **`/skew`** | `compute_options_skew.py` → `options_skew.json` (+ `options_skew_history.json`) | **Vol-Regime-Radar** (X=RR-Rank, Y=IV-Rank **oder** IV-Percentile, Umschalter; Fenster 3M/6M/1J/2J; grün→rot-Gradient; Rand-Labels Expensive/Cheap/Bullish/Bearish; Spread-Strategien in den Ecken: oben-links Sell Put Spread, unten-links Buy Call Spread, oben-rechts Buy Put Spread, unten-rechts Sell Call Spread), **Heatmap-Metrik-Tabelle**, **Vol-Trigger-Panel** (aus `gex_summary.json`, Heatmap+Kategorie-Filter), Klick-Ticker → **Skew-Verlauf** + **IV-Term-Structure** (Contango/Backwardation) + **Volatility Smile** (IV×Delta, 30d+Front-Expiry), **VRP-Balken**, Correlation-KPIs (`^COR1M/3M`) |
| **`/iv-surface`** | `compute_iv_surface.py` → `iv_surface.json` | IV-Heatmap **Moneyness × Laufzeit** (~12 Kern-Ticker) |
| **`/key-levels`** | `compute_key_levels.py` → `key_levels.json` | **Max Pain** (Argmin Auszahlungssumme), Call/Put-Walls + Flip (aus gex_summary), OI-by-Strike, P/C-OI-Ratio, Levels-Copy-Button |
| **`/options-flow`** | `compute_options_flow.py` → `options_flow.json` (+ `oi_history/`) · **Equity-P/C aus `options_skew.json`** | **ΔOI-Flow** (Tag-über-Tag-OI = neue Positionierung, **forward-akkumuliert** — baut sich über Tage auf), **0DTE/Short-Dated** (Front-Expiry-Gamma-by-Strike, EOD-ehrlich), **Equity Put/Call Ratio** (siehe unten) |
| **`/dealer-positioning`** | `snapshot_gex_massive.py` → `gex_summary.json` + `gex_profile_<T>.json` | GEX/Zero-Gamma-Flip/Walls + **Charm-/Vanna-Profile je Strike** (Marker Spot/Flip/Walls) |

**Per-Ticker-Metriken (`compute_options_skew.py`, ein Snapshot/Ticker):** 25Δ-Skew @30d + @90d (Skew-Term), **NE-Skew** (Front-Verfall, spekulativ), ATM-IV-Term-Structure (6 Laufzeiten, Contango/Backwardation), **VRP** (ATM-IV − realisierte 1-Monats-Vola/21 HT aus Kursen; **CBOE-Formel** √(252/(N−1)·Σ(R−R̄)²), Log-Returns — Horizont passend zur 30d-IV), **25Δ-Butterfly**, **P/C-IV-Ratio**, **Expected Move** (IV·√T), **Volatility-Smile-Kurve** (IV je Delta-Grid 10-40Δ Put/Call + ATM, 30d + NE). Jeder Ticker mit `cats`-Tags. Rank vs. Percentile: `_rank`=(last−min)/(max−min), `_pctl`=Anteil Tage darunter.

**Equity Put/Call Ratio (`/options-flow`, Panel 3):** marktweite P/C übers US-Aktien-Universum — **Equity** (ohne Broad-Index-ETFs) vs. **Index** (Broad-Index), je **volumen- UND OI-basiert**. Berechnet in `compute_options_skew.py` (piggyback auf der 156-Ticker-Schleife: je Ticker `put_vol/call_vol/put_oi/call_oi` aus der ±30%-Chain, in `build()` aggregiert → `pc_ratio` in `options_skew.json`). ⚠️ **Die offizielle CBOE-Equity-P/C ist nicht mehr gratis** (Yahoo-Ticker `^CPCE/^CPC/^CPCI` tot) → das ist unsere eigene, near-the-money-basierte Ratio, **kein CBOE-Wert**. Historie: keine freie verfügbar → **forward-akkumuliert** in `options_skew_history.json['__PCR']` (`{date, eq_vol, eq_oi, idx_vol}`), baut sich ab dem 2. Handelstag auf. Deutung: >1 put-lastig/defensiv, <1 call-lastig/offensiv; Index strukturell höher (Hedging). Frontend liest `pc_ratio` aus `options_skew.json` + `__PCR` aus der History.

**GEX = Yahoo/Massive-EOD, kein marketdata:** Voll-Chain-GEX braucht ALLE Strikes → per-Kontrakt-Bepreisung unbezahlbar. `snapshot_gex_massive.py` holt die Massive-Voll-Chain (flatrate), rechnet Greeks **selbst per BS** (Engine `compute_gamma_exposure.py`, `_profile`/`_profile_by_term` = Gamma/Vanna/Charm je Strike) → gleiches `gex_summary.json`-Schema wie der Yahoo-Pfad (`snapshot_gex.py` bleibt Fallback).

## Crons

- **`options_skew.yml`** (werktags 23:00 UTC, **Timeout 50m** wegen 156 Tickern): `compute_options_skew.py` → `compute_iv_surface.py` → `compute_options_flow.py`.
- **`gex_snapshot.yml`** (werktags 22:15 UTC): `snapshot_gex_massive.py` → `compute_key_levels.py`.
- Alle `landing/data/*.json` (inkl. `oi_history/`, `gex_history/`) **gitignored** → server-produziert; nach manuellem Backfill per SSH, nicht committen.
- **`daily_health_check.py`** prüft jetzt **„Options: Skew/IV"** (Frische + Ticker-Zahl + Metrik-Abdeckung) + **„Options: GEX-Ketten"** (Frische + Flip-Abdeckung).

## Historie-Backfill (BS-Rekonstruktion)

Der Radar braucht **≥5 Historie-Punkte** je Ticker für den Rank. Neue Ticker haben anfangs nur 1 (Forward-Akku). **`scripts/backfill_skew_massive.py`** (seit 2026-09-08) füllt sie — **aus Massive**, nicht marketdata: Massive-Historie liefert nur Preise (kein IV/Greeks, Quotes sind 403 auf dem Options-Starter), deshalb **invertiert der Backfill die IV je Kontrakt per BS-Bisektion** aus den Aggregates-Bars, pickt 25Δ, normiert die Laufzeit auf konstante 30 Tage (Varianz-Interpolation `cm`/`cm_extrap`) → schreibt inkrementell pro Ticker in `options_skew_history.json`. Details + die fünf Fallen der Rekonstruktion siehe „Lessons Learned" unten. `verify_skew_iv.py` bestätigt: unsere BS-IV reproduziert die Live-IV auf **< 0,4 Vol-Punkte**.

> **Hinweis:** Der Vorgänger `scripts/backfill_skew_history.py` (marketdata.app, 1 Credit/Chain) ist **stillgelegt** — marketdata wurde nur evaluiert, nie produktiv genutzt. Der Backfill läuft jetzt komplett über Massive.

## Methodik-Abgleich mit SpotGamma (bestätigt korrekt)

25Δ-Skew (Put−Call) = Industrie-Standard-Risk-Reversal; Vorzeichen (positiv = Put-Skew/„high skew"), ATM = 50Δ-Mittel, OTM-Selektion, IV-Rank vs. IV-Percentile, **NE-Skew** (Next-Expiry), **Volatility Smile** (IV×Delta) — alles SpotGamma-äquivalent. Datengesperrt (nicht baubar ohne OPRA-Realtime/proprietär): HIRO, Live-Tape, Synthetic-OI, TRACE-Intraday.

## Lessons Learned (dieser Ausbau)

- **stdout block-buffert** bei Redirect/`| grep` → `flush=True`; Skripte schreiben die JSON erst am ENDE (kein Fortschritt sichtbar ≠ Hänger). Detached-Läufe (`nohup docker exec`) schreiben ihr eigenes Logfile, nicht die Task-Output-Datei.
- **Nicht mehrere schwere Läufe gleichzeitig** (Host 3,8 GB, mehrere Container → Thrash/„hängt"). `pkill` fehlt im Container → Host-seitige `docker exec`-Clients killen ODER App-Container neustarten. Sequentiell laufen lassen.
- **Massive-Snapshot: Spot separat** (`/v2/aggs/prev`) + **Strike-Filter ±30 % Moneyness** (`strike_price.gte/lte`) → 156-Ticker-Lauf 48→~15 Min (nur near-the-money nötig für 25Δ+ATM).
- **429 unterscheiden:** Burst-Rate-Limit (Throttle hilft) vs. **Tages-Credit-Limit** (nur Zeit hilft). Massive-Flatrate umgeht beide; kleiner Seiten-Throttle bleibt.
- **Blog-Chart-Embed:** Markdown referenziert `<slug>/datei.png` (Builder prependet `images/`; Post rendert unter `/blog/<slug>/` → finale URL `/blog/<slug>/images/<slug>/datei.png` = **200**; der doppelt aussehende Slug-Pfad ist korrekt, exakt wie beim Dealer-Post).
- **GEX-Universum = Kern-Set (~20)**, nicht die 156 (Voll-Chain-GEV pro Ticker ist schwer) → Vol-Trigger/Key-Levels/Charm nur für Indizes+Mag7; Kategorie-Filter zeigt dort ggf. „nur Kern-Ticker".
- **Realized Vol = CBOE-Formel** (Log-Returns, mittelwert-bereinigte Stichproben-Varianz ÷(N−1), ×√252) — war schon korrekt, nur als Dezimal gespeichert (Anzeige ×100). **VRP-Horizont-Bug (2026-09-08):** 30-Kalendertage-IV gegen 30-**Handels**tage-Realized (≈42 Kalendertage) verglichen → Horizonte passten nicht; Fix: **21 HT = 1 Monat** (CBOE). SPY-VRP dadurch +0,6 → +4,2 (korrekt). `_realized_vol(sym, n=21)`, Feld `rv_1m`.
- **HTML-Browser-Cache-Falle:** die Options-Seiten-Routen hatten `Cache-Control: public, max-age=3600` → Änderungen erschienen bis zu 1 h nicht (normaler Reload = alte HTML), „ich sehe nichts". Fix: die 6 Options-Routen auf **`max-age=0, must-revalidate`** (immer frisch via ETag). Bei UI-Änderungen, die „nicht ankommen": zuerst Cache prüfen (`curl -D-`), Hard-Refresh, sonst diese Header.
- **Gmail rendert Sonderzeichen nicht** (das ⌥-Options-Symbol war unsichtbar → nur der Zahlenwert blieb, „das sind keine Skews"). In E-Mails **klare Text-Labels** statt exotischer Unicode-Symbole.
- **`.env`-Änderung greift erst nach `docker compose up -d --force-recreate app`** (env_file wird beim Container-Start gelesen; ein reiner Restart reichte im Test manchmal nicht → force-recreate).
- **`_pick()` ohne Toleranz etikettiert still falsch (2026-09-08):** `min(key=|δ|−target)` liefert IMMER einen Treffer — bei dünner Kette also z.B. einen 0,40Δ-Kontrakt, der dann als „25Δ" ins JSON geht und den Ticker-übergreifenden Vergleich verfälscht, ohne dass irgendwo ein Fehler auftaucht. Fix: `_DELTA_TOL = 0.08`, darüber `None` → `_skew_at` gibt None zurück, der Ticker fällt für den Tag sauber raus (Log: „kein 25Δ@30"). **Nur auf den 25Δ-Picks**, nicht auf ATM(50Δ)/Skew-Curve — dort würde ein Guard die Abdeckung unnötig senken. Kontrolle: die Deltas stehen als `call_25d.delta`/`put_25d.delta` im JSON, damit ist die Auswahl nachträglich prüfbar.
- **Massive liefert das Underlying nicht immer** (ARM am 2026-09-08: `underlying` = 0,00, auch der Snapshot-Fallback über `underlying_asset.price` blieb leer). Skew/Zeta sind davon unberührt (kommen aus den IVs), aber Moneyness, Expected Move und der ±30 %-Strike-Filter brechen. Fix: **Fallback 2 = letzter Close aus der eigenen Kursreihe**, die `_realized_vol()` ohnehin lädt → Rückgabe ist jetzt `(rv, last_close)`, kein zweiter `download_data`-Aufruf. Gegenprobe: SPY-`last_close` 770,19 = exakt der Massive-Spot.
- **Historien-Backfill (2026-09-08, `backfill_skew_massive.py`) — vier Fallen in Folge:**
  1. **Massive führt IV/Greeks nur im Snapshot.** Jeder Endpoint mit Datumsparameter (Aggregates, Trades, Quotes) ist preis-only; jeder mit IV/Greeks (die drei Snapshots) kennt kein Datum. Historische IV muss deshalb per BS-Bisektion aus Preisen invertiert werden. **Quotes sind 403** (Options-Starter deckt sie nicht ab) → nur Aggregates.
  2. **Expiry-Wahl: `min(|dte−30|)` greift Mittwochs-Weeklies ab.** Liquide Titel haben sie, 30 Tage im Voraus handeln sie kaum → keine Trades, keine Bars (MU-Probe: 0/48). Fix: Monatsverfall (3. Freitag) bevorzugen, dann irgendein Freitag. **Gilt auch für `compute_options_skew.py::_nearest_exp`** (Parameter `prefer_monthly`, nur für die 25Δ-Picks — die Term-Structure braucht das kurze Ende).
  3. **Stale-Print-Bias.** Aggregates liefern den letzten *Trade*; bei dünnen Kontrakten Stunden vor Schluss, gepaart mit dem *Schlusskurs* des Basiswerts → IV zu tief. Skaliert mit Illiquidität: SPY/QQQ cZeta 0,4 daneben, AVGO 2,0, **MU 4,1 mit Vorzeichenwechsel** (+3,40 → −0,66). Absolute Volumenschwellen taugen nicht (200 rettet MU, zerstört SPY). Fix: **`--vol-pctl 0.5`** — Perzentil innerhalb der Kandidaten *dieses Tages*, normiert sich selbst auf den Ticker. Danach Mittel 0,79 pts.
  4. **Monatsverfall erzeugt einen Sägezahn.** DTE läuft von ~46 auf ~10 und springt beim Roll zurück, die ATM-IV folgt der Term-Struktur (MU: 0,52 bei 16 Tagen, 0,65 bei 42 — 13 Vol-Punkte). Tagesänderung von call_zeta: p90 6,8 pts. Ein Percentil darüber rankt die Position im Verfallszyklus, nicht den Skew. Fix: **zwei Verfälle wählen, die 30 Tage klammern, und linear in der TOTALEN VARIANZ interpolieren** (σ²·T, VIX-Methodik) — linear in der IV läge 3 Punkte daneben. Restfehler 0,45 pts (Krümmung der Term-Struktur). `cm_mode` hält fest, ob interpoliert wurde.
  5. **Einzelne Stützstelle bringt den Sägezahn zurück.** Erster CM-Lauf: `cm 98, single 52, None 14` — nur 60 % war wirklich normiert. Kurz vor dem Roll liegt kein Monatsverfall mehr unter 30 Tagen, also gab es kein Bracket. Fix: die **zwei nächstlängeren Verfälle nehmen und nach unten extrapolieren** (Grenze: nächste Stützstelle ≤ 15 Tage vom Ziel). Fehler 0,00–0,04 pts — **besser als die Interpolation** über weite Brackets (dort bis 0,99), weil [39,67]→30 ein kurzer Schritt entlang einer glatten Kurve ist, während [11,46] einen gekrümmten Bereich überspannt. `cm_extrap` markiert diese Tage.
  6. **`--overwrite` überschrieb nur teilweise.** Tage, die der neue Lauf nicht reproduzieren konnte, überlebten — beim Umstieg auf konstante Laufzeit blieben so 14 Sägezahn-Einträge in der neuen Reihe. Ein Überschreiben, das nur teilweise greift, ist heimtückischer als gar keins. Fix: bei `--overwrite` alle `src=massive`-Einträge **vorher verwerfen**; Provider-Einträge bleiben unangetastet.
- **Langläufer gehören in einen EIGENEN Container.** Ein `git push` löst den Auto-Deploy aus, der `docker compose up -d --build app` fährt und einen laufenden `docker exec` mitreißt — der erste Backfill starb so nach 400 von 2618 Bars, und im Log sah es aus wie ein Hänger. `landing/data` ist ein Bind-Mount vom Host, deshalb genügt:
  ```
  docker run -d --name sa-backfill \
    -v /opt/seasonaledge/.env:/app/.env:ro \
    -v /opt/seasonaledge/landing/data:/app/landing/data \
    -w /app seasonaledge-app python3 -u scripts/backfill_skew_massive.py …
  ```
  (`-u` gegen die stdout-Pufferung, `.env` als Mount statt `--env-file` — Docker parst das Format anders als `load_env()`. Der Healthcheck meldet „unhealthy", weil kein Streamlit läuft; das ist folgenlos.)
- **Diagnose „hängt oder läuft?" braucht ZWEI Messungen.** Ein einzelner frischer Zeitstempel der Logdatei beweist nichts, wenn nur alle 200 Abrufe geschrieben wird. Erst der Vergleich zweier Messungen im Abstand — oder `docker ps` mit der Laufzeit — zeigt den Stillstand. Ich habe deshalb einmal fälschlich Entwarnung gegeben.
- **Die Methode trägt nicht für jeden Ticker.** Abdeckung und Anteil normierter Tage (1 Jahr, `--vol-pctl 0.5`):

  | Ticker | Punkte | Abdeckung | normiert (cm+extrap) |
  |---|---|---|---|
  | SMH | 170 | 67 % | am höchsten (ETF) |
  | MU | 151 | 60 % | 75 % |
  | DELL | 139 | 55 % | 72 % |
  | ARM | 136 | 54 % | — |
  | **BE** | **70** | **28 %** | **40 %** |

  BE (Bloom Energy, ~95 % ATM-Vola, 25Δ entsprechend weit außen) bleiben effektiv ~28 saubere Tage im Jahr. Das ist kein Code-Problem — die Trades existieren nicht. **Für Percentile nur `cm` und `cm_extrap` zählen, `single` verwerfen**; damit fällt BE von selbst durch das Raster, statt Scheingenauigkeit zu erzeugen.
- **Code-Review Runde 2+3 (2026-09-10) — 13 Befunde, 11 behoben.** Die wichtigsten Muster:
  - **`--overwrite` löschte bei leerer API-Antwort eine ganze Ticker-Historie.** Der Purge schrieb die geleerte Liste sofort in `hist[sym]`; die frühen `return`s danach kehrten mit gelöschter Historie zurück, und `main()` schrieb das weg. 500+ Punkte weg wegen eines fehlgeschlagenen Requests. **Regel: destruktive Operationen nur auf einer lokalen Kopie, Commit erst nach Erfolg.**
  - **Nicht-atomares Schreiben.** `write_text()` kürzt erst auf 0. Der Supervisor stoppt den Container zu einem FESTEN Zeitpunkt, unabhängig vom Schreibzustand → abgeschnittene 4-MB-Datei, die der nächste Leser für leer hält. Fix: `shared/atomic_json.py` (Temp-Datei **im Zielverzeichnis**, sonst ist `os.replace` nicht atomar; flush+fsync; Aufräumen auch bei `BaseException`).
  - **Versteckte Abhängigkeit im Cron.** `gex_snapshot.yml` fährt `compute_key_levels.py` direkt nach dem Snapshot — es BRAUCHT die frische `gex_summary.json`. Ohne `pipefail` lief es bei gescheitertem Snapshot auf alten Daten weiter und die Seite zeigte gestrige Levels als heutige, bei grünem Workflow. Dort jetzt harter Abbruch; bei `options_skew.yml` (unabhängige Ausgabedateien) nur Fehlersammlung.
  - **Frontend zeigte alte Punkte als aktuell.** `_rank`/`_pctl` nehmen blind den letzten Eintrag. Ohne heutigen normierten Punkt rutschten alte Tage in diese Rolle — an Produktionsdaten gemessen 5 von 101 Tickern, DUK mit 20 Tagen Alter. Fix: Abgleich gegen `session` aus `options_skew.json`.
  - **Max Pain** nahm Strikes mit OI=0 als Kandidaten und bei flachem Minimum den niedrigsten → bei leerer OI wurde der kleinste Strike als Niveau gemeldet. Jetzt nur Strikes mit OI>0, `None` bei `total_oi==0`, `non_unique`-Flag.
  - **IV-Surface** klemmte außerhalb der Strike-Spanne auf den nächsten Strike; der Wert erschien als echte 85-%-Moneyness. Jetzt `None`. Und `grid[2]` war als „30d" hartkodiert, obwohl Zeilen entfallen können → `_row30()` wählt per `min|dte−30|`.
  - **ΔOI** aggregierte nur je Strike über alle Laufzeiten: ein Roll sah aus wie neue Positionierung, und verfallene Kontrakte fehlten in der Netto-Summe (nach jedem OPEX systematisch zu positiv). Jetzt je (Expiry, Strike) mit Iteration über die Union; Schema-Marke lässt EINEN Lauf aus statt Scheinwerte zu melden.
  - **`is_0dte = dte <= 2`** gab 1d und 2d das 0DTE-Abzeichen. Jetzt `== 0`.
  - **Falsche Quellenangabe:** `/dealer-positioning` behauptete an drei Stellen Yahoo, während der Cron Massive fährt. Korrigiert **ohne** den neuen Anbieter zu nennen (v54: Anbieternamen bewusst nicht user-sichtbar).
- **GEX-Mathematik unabhängig bestätigt** (Runde 3): Gamma, Vanna UND Charm gegen Finite-Differenzen inkl. q≠0, max. Abweichung 2,5e-9. `charm = ∂Δ/∂t = −∂Δ/∂T`, `/365` genau einmal angewandt, GEX-Skalierung = $ pro 1-%-Bewegung, Vorzeichen/Bucketing konsistent. `_skew()` im GEX-Code ist ein **90/110-%-Front-Skew**, nicht der 25Δ-Skew — kein stiller Namenskonflikt.
- **Offen: zwei Zinssätze.** `compute_gamma_exposure.py` hat eine EIGENE `bs_greeks` mit `_R = 0.04`, `shared/black_scholes.py` nutzt `R = 0.045`. Quantifiziert: 0,16 % Gamma-Abweichung am Geld, 2–3 % weit OTM. Kein aktueller Zahlenfehler (die Pfade werden nicht kombiniert), aber genau die Drift, die die BS-Vereinheitlichung beseitigen sollte — bei der `bs_greeks` übersehen wurde.
- **Verify-Gates müssen die ZIELGRÖSSE prüfen, nicht Rohwerte.** Eine Mittelung über `iv_atm`/`call_iv`/`put_iv` meldete „0,82 pts — gut", während MUs `call_zeta` das Vorzeichen drehte. Das Produkt nutzt Zeta, also prüft das Gate Zeta — mit Vorzeichenwechsel als hartem FAIL.
- **History stempelte Kalendertage.** Die Vorwärts-Akkumulation nutzte `date.today()`, der Cron läuft aber täglich um 23:00 UTC — auch Sa/So/feiertags. Ergebnis: Einträge für Labor Day mit Freitags Chain, dreifach dupliziert, und `--verify` fand keinen Provider-Tag in der Kursreihe. Fix: `out["session"]` = letzter NYSE-Handelstag; Alt-Einträge werden **umdatiert statt gelöscht** (der Wert stimmt, nur das Label war falsch).
- **Rohwert-Skew vs. SpotGamma-Compass ist kein direkter Vergleich:** der Compass plottet **Percentile in der Eigenhistorie**, nicht Rohwerte. Ein Titel kann bei negativem Roh-Call-Zeta trotzdem im hohen Call-Skew-Percentil stehen, wenn er üblicherweise noch negativer läuft (Fall BE 2026-09-08: unser Roh-Zeta −11,24/+10,40 = defensiv, SpotGamma zeigte bullish). Für den echten Abgleich braucht es belastbare Historie — die Forward-Akkumulation läuft erst seit KW36.

- **Zwei Messmethoden in einer Reihe zerstören jedes Percentile (2026-09-09).** Die Skew-Historie bestand zu >99 % aus BS-rekonstruierten Backfill-Punkten, der tägliche Live-Punkt kam aber mit der fertigen **Provider-IV** dazu. Gemessener Versatz im Zeta: **0,84–1,30 pts**, gleiche Richtung bei allen Tickern (Call-IV zu niedrig, Put-IV zu hoch). Bei NVDA war der Versatz mit 1,30 pts **so groß wie der gesamte Interquartilsabstand (1,28)** — der Live-Punkt landete dadurch im **99. Percentil**, bei SMH im 97., völlig unabhängig vom Markt. Wer nur die mittlere Abweichung anschaut („0,88 pts, klingt klein"), sieht das nicht: entscheidend ist der Versatz **relativ zur Streuung der Reihe**. Fix: der Live-Lauf invertiert die IV für die Historie **selbst** aus den Snapshot-Preisen (`_own_cands`/`_leg_own` in `compute_options_skew.py`) — gleiche Bisektion, gleicher Volumen-Perzentilfilter (0,5), gleiche Delta-Toleranz und **gleiche Spot-Quelle** (unsere Kursreihe wie `_closes` im Backfill; Massives `/prev` liefert je nach Laufzeitpunkt den Vortag). Die BS-Mathematik liegt jetzt in **`shared/black_scholes.py`**, damit beide Seiten nicht wieder auseinanderdriften. Bewusst **kein Rückfall** auf die Provider-IV — der würde die Mischung wieder einschleusen; schlägt die Inversion fehl, fehlt `cm_mode` und das Frontend lässt den Tag aus der Rangfolge. Die **angezeigten** Per-Ticker-Werte bleiben Provider-IV (genau, EOD).
- **Verify-Gate braucht eine Referenz derselben Bauart.** `--verify` vergleicht gegen History-Einträge ohne `reconstructed`. Solange das die alten Provider-Punkte waren, maß das Gate den Methodenunterschied statt der Rekonstruktionsgüte — es schlug zu Recht an, aber die Ursache lag nicht im Backfill. Die 380 nicht-normierten Legacy-Live-Punkte (148 Ticker) wurden entfernt (Backup `options_skew_history.bak.json`); sie hätten außerdem den nächsten Cron-Eintrag blockiert, weil pro Session-Datum nur einmal angehängt wird.
- **Backfill NACH dem Live-Lauf überschreibt den Live-Punkt desselben Tages (2026-09-10).** `run_ticker` dedupliziert am Ende je Datum, und dabei gewinnt der zuletzt angehängte Eintrag. Läuft der Backfill also nach dem EOD-Lauf, ersetzt seine Rekonstruktion den Live-Punkt für den überlappenden Tag. Inhaltlich unkritisch, seit beide dieselbe Methode nutzen — **aber `--verify` verliert dadurch seine Referenz**, denn es vergleicht gegen Einträge *ohne* `reconstructed`. Für die sechs neuen Ticker war das Gate deshalb nicht durchführbar; die Methode war global über SPY/QQQ/SMH/NVDA validiert. Konsequenz: Backfill für einen Ticker möglichst **vor** dem ersten Live-Lauf fahren, sonst die per-Ticker-Gegenprobe einen Cron-Zyklus später nachholen.
- **Cron-JSONs gingen unkomprimiert raus (2026-09-10).** `deploy/nginx.conf` hatte **gar keine** gzip-Direktive, und das Frontend holte die Dateien mit `cache:'no-store'` — die auf **2,65 MB** gewachsene `options_skew_history.json` wurde damit bei **jedem** Aufruf von `/skew` und `/flows` komplett neu übertragen. Das war die plausibelste Ursache des gemeldeten „/flows hängt beim Laden". Zwei Hebel: **gzip** in der `/landing/`-Location (2.649.629 → **273.669 B**, Faktor 9,7) und `no-store` → **`no-cache`** (revalidiert weiterhin immer, erlaubt dem Server aber ein 304). `no-store` einfach zu streichen wäre falsch gewesen — nginx liefert `max-age=86400`, die täglich aktualisierten Daten wären bis zu einen Tag alt ausgeliefert worden.
## Langlaufende Backfills betreiben (Supervisor + Statusmail)

Ein Backfill ueber das Radar-Universum laeuft **viele Stunden** (~10 Min/Ticker/Jahr; 110 Ticker ≈ 18 h) und ueberlappt damit zwangslaeufig mit dem naechtlichen `options_skew`-Cron. Beide schreiben **dieselbe** `options_skew_history.json` — und der Backfill haelt sie im Speicher und schreibt nach *jedem* Ticker die ganze Struktur zurueck. Alles, was der Cron in der Zwischenzeit anlegt, waere damit weg (**Lost Update**). Nur der 23:00-Cron kollidiert; der GEX-Cron (22:15) schreibt andere Dateien.

**`scripts/backfill_supervisor.sh`** loest das: er pausiert den Container kurz vor dem Cron (Default 22:50 UTC), setzt ihn danach fort (00:10 UTC), mailt alle drei Stunden einen Zwischenstand und am Ende den Abschlussbericht.

```bash
# Backfill starten (EIGENER Container, ohne --overwrite -> Live-Punkte bleiben erhalten)
docker run -d --name sa-backfill-rest   -v /opt/seasonaledge/.env:/app/.env:ro   -v /opt/seasonaledge/landing/data:/app/landing/data   -w /app seasonaledge-app   python3 -u scripts/backfill_skew_massive.py --years 1 --vol-pctl 0.5 --symbols <TICKER…>

# Supervisor als transiente systemd-Unit (ueberlebt SSH-Abbruch UND Entwickler-PC)
BASELINE=53 systemd-run --unit=sa-bfsup --description="Backfill Supervisor"   /bin/bash /opt/seasonaledge/scripts/backfill_supervisor.sh
systemctl is-active sa-bfsup.service
tail -f /var/log/sa-backfill-supervisor.log
```

**`scripts/backfill_skew_report.py`** erzeugt den Bericht. Er meldet bewusst **nicht** „exit 0", sondern die Zahl, die zaehlt: **wie viele Ticker jetzt im Radar erscheinen** (cm/cm_extrap-Punkte ≥ `MIN_NORM`), plus die Liste der weiterhin zu duennen Titel. Ein Lauf kann sauber durchlaufen und trotzdem kaum Abdeckung bringen, wenn die 25Δ-Liquiditaet fehlt. `--progress` liefert waehrend des Laufs Position und eine Restzeit-Schaetzung aus dem **tatsaechlichen** Tempo.

**Fallstricke, die Zeit gekostet haben:**
- **`pkill -f backfill_supervisor` killt die eigene Shell** — das Muster steht in der eigenen Kommandozeile. Beenden mit `systemctl stop sa-bfsup.service`.
- **`docker exec` laesst sich ueber SSH nicht detachen** (haelt den Kanal bis Prozessende offen; `nohup`/`setsid` helfen nicht). Langlaeufer deshalb per `docker run -d` in einen eigenen Container, Audits gezielt per `--ticker` oder mit ≥10 min Timeout.
- **HHMM-Zeitvergleiche brauchen `10#`** — sonst liest bash `0010` als Oktalzahl. Fensterlogik vor dem Ausrollen trocken gegen mehrere Uhrzeiten durchspielen; mein erster Entwurf hatte das Fenster faelschlich auf 23:45 statt vor den 23:00-Cron gelegt.

## Code-Review 2026-09-10 (PRs #248–#258)

Review über `shared/black_scholes.py`, `compute_options_skew.py`, `backfill_skew_massive.py`, `skew.html`, `options_universe.py`. **11 Befunde** — durchweg Restpfade, auf denen Live- und Backfill-Reihe wieder auseinanderlaufen konnten, also genau die Fehlerklasse, die der Umbau schließen sollte.

**Behoben (8, PR #258):**

| # | Befund | Warum es zählt |
|---|---|---|
| 1 | `--vol-pctl` Default `0.0`, Live filtert fest `0.5` | Der geplante 2-J-Lauf **ohne Flag** hätte die Reihe mit anders gefilterten Punkten gemischt |
| 2 | `spot_own = last_close or spot` fiel auf den `/prev`-Spot zurück | Genau die Quelle, vor der der Kommentar darüber warnt — ein falsch skalierter Punkt bekam trotzdem `cm_mode` |
| 3 | `cm`-Zeilen ohne `iv_atm` möglich | Frontend fällt dann auf `(call_iv−put_iv)/2` zurück → `put_zeta = −call_zeta`, der Quadrant kollabiert auf seine Antidiagonale |
| 4 | `_own_cands` rechnete `dte` gegen `date.today()` | Zeile wird unter `_last_session()` gestempelt → bei Nachhol-Läufen lag T bis zu 3 Tage daneben |
| 5 | `_fix_session_dates` bevorzugte pauschal den Live-Eintrag | Ein **nicht** normierter Live-Punkt konnte einen brauchbaren `cm`-Punkt verdrängen und die Stichprobe verkleinern |
| 6 | CM-Parameter + `cm_interp` als Kopie in beiden Skripten | Dasselbe Drift-Risiko, das die BS-Vereinheitlichung gerade beseitigt hatte |
| 7 | `verify_skew_iv.py` importierte BS aus dem **stillgelegten** `backfill_skew_history.py` | Das Gate zertifizierte eine dritte, produktiv gar nicht laufende Engine |
| 8 | History-Zeile mischte CM-IVs mit Front-Monats-`vrp_pts`/`pc_ratio` | Intern inkonsistente Zeile |

Gegenprobe nach dem Fix: `CM_DAYS`/`DELTA_TOL`/`SINGLE_TOL`/`VOL_PCTL` auf beiden Seiten identisch, `cm_interp` ist **dieselbe Funktion** (Identitätstest `is`), `verify` nutzt dieselbe `implied_vol`, BS-Rundlauf exakt, `_enrich` liefert weiter `cm_mode=cm`.

## Endabnahme 2026-09-11 (PR #275)

Externe Abnahme der 8 Fixes und der 3 offenen Punkte. **6 Fixes halten, 2 waren
lückenhaft**, dazu eine korrigierte Einstufung.

### Zwei Fixes waren unvollständig

**Fix 1 (`--vol-pctl`) griff nur am CLI.** Der Parser stand auf `0.5`, aber
**vier Funktionssignaturen** defaulteten weiter auf `0.0` (`_leg_ivs`,
`_reconstruct`, `run_ticker`, `verify`). Produktiv reicht die CLI den Wert durch —
ein Direktaufruf hätte still eine anders gefilterte Reihe erzeugt, also genau die
Drift-Klasse, die der Umbau schließen sollte. Jetzt kommen alle vier Defaults aus
`shared/black_scholes.VOL_PCTL`.

**Fix 3 wurde nur im Live-Pfad angewendet.** Dort prüft die *Aufrufstelle*
(`compute_options_skew.py::_enrich`), ob `cm_iv_atm` da ist. Der Backfill hat
dieselbe Erzeugerstruktur, aber keine solche Wache: `_reconstruct` setzte
`cm_mode` auch ohne `iv_atm`, das Frontend rankte die Zeile und fiel dann auf die
Näherung `(call_iv−put_iv)/2` zurück — die `put_zeta = −call_zeta` erzwingt und den
Quadranten auf seine Antidiagonale kollabieren lässt.
Jetzt verliert eine solche Zeile ihre `cm`-Kennzeichnung (Modus `noatm`) und bleibt
damit aus der Rangfolge; `skew_pts` bleibt erhalten.

> **Lesson, zum zweiten Mal in dieser Datei:** ein Fix an der *Aufrufstelle*
> schützt nur diese eine Stelle. Die Regel gehört zum **Erzeuger** — sonst fehlt
> sie beim nächsten Aufrufer.

### `_leg_own` vs. `_leg_ivs` — Einstufung korrigiert

Der Reviewer stufte den Punkt als echten Rechenfehler ein: die Ausdünnung entferne
den nächstliegenden 25Δ-Kontrakt und verschiebe den Volumenmedian, „weil Liquidität
und Strike nicht unabhängig sind".

**Der Mechanismus stimmt so nicht** — die Ausdünnung ist *gleichmäßig* über das
±30 %-Band (`step = len(ss)/24`), nicht „die 24 nächsten am Spot". Gemessen
(4000 Simulationen, glockenförmiges Volumenprofil, lognormale Streuung):

| Ausdünnung | Median-Verschiebung | Anteil positiv |
|---|---|---|
| gleichmäßig (Ist-Zustand) | **+7,2 %** (Median), Streuung 82 pp | 55 % |
| die 24 nächsten am Spot (unterstellt) | +9624 % | 100 % |

Also: eine **kleine, aber echte** systematische Verschiebung — die Volumenschwelle
liegt im Backfill rund 7 % höher als live. Meine ursprüngliche Einstufung („nur
unterschiedliche Grundmengen, kein Rechenfehler") hat das untertrieben; die
Einstufung als grober Fehler überzeichnet es um den Faktor 1000. Bleibt offen, jetzt
mit Zahl statt Vermutung.

Die beiden Darstellungsfragen wurden bestätigt: keine Rechenfehler.

### Live-Störung: atomares Schreiben machte die Ausgaben unlesbar (PR #276)

Beim Durchsehen der TODO-Liste nach der Abnahme aufgefallen: `/skew` und `/flows`
bekamen ihre Daten nicht mehr.

```
open() "/app/landing/data/options_skew_history.json" failed (13: Permission denied)
```

`tempfile.mkstemp()` legt die Temp-Datei bewusst mit **0600** an, und `os.replace()`
überträgt diesen Modus auf die Zieldatei. nginx läuft als anderer Nutzer → 403.

**Der Beweis lag in der Differenz:** betroffen waren genau die zwei Dateien, die
`write_json_atomic` nutzen (`options_skew.json`, `options_skew_history.json`); die
vier ohne atomares Schreiben (`iv_surface`, `options_flow`, `gex_summary`,
`key_levels`) lieferten weiter 200.

Behoben: vor `os.replace` die Rechte der Zieldatei übernehmen, sonst die des
normalen Schreibwegs (umask) nachbilden. Auf dem Server verifiziert — neue Dateien
0644, bestehende Rechte bleiben erhalten. Die Live-Dateien wurden sofort per
`chmod 644` repariert.

> **Zum dritten Mal in dieser Reihe: eine Korrektur kann schlimmer sein als der
> Fehler.** Der Schutz gegen Datenverlust (PR #256) baute eine Zustellstörung ein.
> Und sie fiel weder im Options-Review noch in der Endabnahme auf, weil beide den
> **Inhalt** der Dateien prüften und nicht, ob sie noch **auslieferbar** sind.
> Konsequenz: nach Änderungen am Schreibweg einer Cron-Ausgabe immer einen
> HTTP-Abruf gegen die Live-URL machen, nicht nur den Dateiinhalt ansehen.

**Bewusst NICHT behoben (3) — mit Begründung:**

- **`_leg_own` ist kein exakter Spiegel von `_leg_ivs`.** Der Backfill dünnt auf `_MAX_STRIKES=24` je Seite aus, der Live-Pfad nutzt alle Strikes der ±30 %-Kette. Dadurch laufen Delta-Pick und Volumen-Perzentil auf **unterschiedlichen Grundmengen**. Die Ausdünnung hat im Backfill einen Sachgrund (er muss je Kontrakt Bars **abrufen**, der Live-Snapshot liefert die Kette in einem Zug). Angleichen ist sinnvoll, aber kein Einzeiler und will gemessen werden.
- **Tabelle paart Front-Monats-IV mit einem Rank, dessen „aktueller" Punkt der letzte *normierte* Tag ist.** Bei dünnen Tickern kann der Wochen alt sein. Darstellungs-Entscheidung, kein Rechenfehler.
- **`renderSkewHist` chartet die ungefilterte Historie**, inkl. Sägezahn und Provider-Stufe, während die Rank-Spalte daneben genau diese Punkte ausschließt. Der Verlauf *soll* womöglich alles zeigen — aber die Diskrepanz gehört erklärt oder der Chart gefiltert.

## Integration ins Morning Briefing + Health-Check

- **Skew + Skew-Percentile je Titel im Morning Briefing** (`shared/daily_report.py`): `skew_map()` (aus `options_skew.json`) + `skew_pctl_map()` (Percentile aus `options_skew_history.json`, 1-J-Fenster) → Ticker-Zeilen (Kernliste + Watchlist) bekommen `skew_pts`/`skew_pctl`; Template `daily_report.html.j2` zeigt eine **eigene „Skew"-Spalte** (Wert + `P{pctl}`), nur US-optionierbare Titel. Cache-gelesen pro Lauf.
- **Skew-Rank/Percentile-Spalte auf `/skew`** (`_skewMetric()`), folgt dem Rank↔Percentile-Umschalter + Fenster, heatmap-gefärbt.
- **Health-Check** (`daily_health_check.py`) prüft alle Options-Dateien: „Options: Skew/IV", „Options: GEX-Ketten", „Options: Key Levels/IV-Surface/Flow" (Frische via `generated`-Datum + Ticker-Zahl, wochenend-/feiertags-tolerant).

## Offene TODOs (Options)

- [ ] **ΔOI-Flow** baut sich erst über Tage auf (OI-Historie akkumuliert ab jetzt).
- [ ] **0DTE** ist EOD-limitiert (echtes Intraday-Flow/Tape haben wir nicht).
- [ ] **Sidebar** für Kategorien/Ticker (User-Wunsch) — einheitlich über alle Options-Seiten.
- [ ] **GEX-Universum verbreitern** (mehr als Kern-Set) — Aufwand/Zeit abwägen.
- [ ] **SpotGamma-Top-3 Rest:** Options-Scanner-Layer (IV-Rank-Extreme, Flip-Nähe, ΔOI, VRP-Extreme) noch offen; Compass/Expected-Move teils da.
- [x] ~~**marketdata.app**~~ — Abo entfällt, Massive ist die einzige Options-Quelle. `backfill_skew_history.py` stillgelegt, Nachfolger `backfill_skew_massive.py` (2026-09-08).

### Skew-Historie / Vol-Regime-Radar

**Percentile/Rank = konstante 30-Tage-Laufzeit (erledigt 2026-09-09).** Ein Percentile ist nur belastbar, wenn die Historie **genauso gemessen** ist wie der heutige Wert. Gelöst:
- [x] **Live-Wert auf konstante 30 Tage normiert** (`compute_options_skew.py`): `_skew_cm()` + `_cm_interp()` (Varianz-Interpolation, identisch zu `backfill_skew_massive.py`). Die Vorwärts-Historie speichert jetzt die CM-Werte + `cm_mode`; die **angezeigten** Per-Ticker-Felder bleiben der reale Front-Monat.
- [x] **Frontend rankt nur noch `cm`/`cm_extrap`** (`_normHist()`/`MIN_NORM` in `skew.html`, sowohl Radar als auch IV-Rank/Skew-Rk-Spalten). `single` und Alt-Einträge ohne `cm_mode` (variabler Verfall) fallen raus — kein Sägezahn mehr in der Rangfolge.
- [x] **Mindestschwelle** `MIN_NORM=20` normierte Tage, sonst kein Ranking (statt Einzelfall-Ausnahme für BE). Dünne Titel fallen automatisch durch.
- [x] **Näherungs-Fallback entschärft:** `cm`/`cm_extrap`-Einträge tragen immer `call_zeta_pts`/`iv_atm` → Stufe 1 des Fallbacks greift, der kollabierende `(call_iv−put_iv)/2`-Zweig kommt nicht mehr zum Zug.

Offen:
- [ ] **2-Jahres-Backfill über das Radar-Universum laufen lassen** (`backfill_skew_massive.py`, server-seitig im eigenen Container, ~20 Min/Ticker/Jahr). **Das ist jetzt der Engpass:** mit `MIN_NORM=20` + strengem cm-Filter erscheinen nur Ticker mit genug normierter Historie — aktuell die wenigen gebackfillten (SMH/MU/DELL/ARM/BE) plus alle, die ~20 Live-Tage akkumuliert haben. Der Rest füllt sich erst über Wochen bzw. mit dem Backfill.
- [x] **Rekonstruktion ↔ Live vereinheitlicht statt kalibriert** (2026-09-09): beide Seiten nutzen dieselbe BS-Inversion (`shared/black_scholes.py`) → eine Kalibrierung ist gar nicht mehr nötig. Erwartet war eine Wartezeit von ~30 überlappenden Tagen; die Vereinheitlichung löst es sofort und dauerhaft.
- [x] **EOD-Validierung erledigt (2026-09-10):** nach dem EOD-Lauf war das Gate grün — 0 Vorzeichenwechsel, mittlere Zeta-Abweichung **0,24 pts** (vorher 0,88), max 0,62 (vorher 1,30), Richtung gemischt statt einseitig. Percentile des Live-Punkts: SPY 5 % · QQQ 36 % · SMH 57 % · NVDA 72 % (vorher 31/80/**97**/**99**) — das methodische Klumpen am oberen Rand ist weg.
- [ ] **`--verify` für SMCI/VRT/IREN/APLD/CRWV/NBIS nachholen**, sobald der nächste Cron einen Live-Punkt für sie geschrieben hat (aktuell überschrieb der spätere Backfill deren Live-Eintrag, siehe Lessons).
- [ ] **`_leg_own` und `_leg_ivs` auf dieselbe Kandidaten-Grundmenge bringen.** Gemessen 2026-09-11: die gleichmäßige Ausdünnung auf 24 Strikes/Seite hebt die Volumenschwelle im Backfill um **~7 % (Median)** gegenüber dem Live-Pfad — klein, aber systematisch (55 % der Fälle positiv). Kein grober Fehler, aber eine bekannte Asymmetrie. Angleichen lohnt, sobald der Backfill ohnehin angefasst wird.
- [ ] **Darstellung klären:** Tabelle zeigt Front-Monats-IV neben einem Rank aus dem letzten *normierten* Tag; `renderSkewHist` chartet ungefiltert (Sägezahn sichtbar), während die Rank-Spalte filtert. Entweder Chart filtern oder die Differenz im UI erklären.
- [ ] **Historie serverseitig eindampfen** auf die vom Frontend benötigten Ticker/Felder — sie ist bei 2,65 MB (gzip 274 KB) und wächst weiter.
- [ ] **`MIN_NORM` nachziehen** (20 → ggf. 80), sobald der Backfill genug Tiefe liefert.
- [ ] **`--vol-pctl 0.5` an mehreren Tagen gegenprüfen** (Wert aus 8 Vergleichen an einem Tag).
- [ ] **Health-Check um einen HTTP-Abruf erweitern.** Er prüft die Options-Dateien bisher auf Frische (Dateiinhalt), nicht auf **Erreichbarkeit**. Die 0600-Störung (PR #276) wäre dadurch sofort aufgefallen statt erst beim Nachsehen. Ein `curl -o /dev/null -w '%{http_code}'` je Datei genügt.
- [ ] Blog **Distribution/Backlinks** für den Vol-Regime-Radar-Post; GSC nach Indexierung prüfen.

## 25Δ-Skew (Alt-Verweis)

Der ursprüngliche Skew war Panel G auf `/flows` (anfänglicher marketdata-Test, 2 Credits/Ticker). **Abgelöst** durch die dedizierte `/skew`-Seite + Massive (siehe oben) — Massive ist die einzige produktive Options-Quelle.

## Quellen

- SqueezeMetrics GEX+ Guide (DDOI, VEX, Einheiten): https://squeezemetrics.com/monitor/static/guide.pdf
- SpotGamma — GEX / Call Wall / Put Wall (Support-Center)
- MenthorQ — Vanna/Charm & Post-OPEX-Vola: https://menthorq.com/guide/why-markets-can-go-wild-after-options-expiration-vanna-and-charm-and-the-volatility-effect/
- Cem Karsan (The Derivative/RCM) — Vol-Curves & Vanna/Charm-Flows
- Macroption / Wikipedia „Greeks (finance)" — BS-Formeln (Gamma/Vanna/Charm mit q)

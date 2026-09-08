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
- **Warum gewechselt (von marketdata.app):** marketdata rechnet **1 Credit pro zurückgegebenem Kontrakt** → SPX-Voll-Chain = 22.718 Credits, SPY ~4.400 → Voll-Chain-GEX unbezahlbar, tägliches 429-Budget. **Massive = Flatrate / unlimited Calls**: **ein** `GET /v3/snapshot/options/<SYM>?expiration_date.lte=<d>&limit=250` (paginiert via `next_url`, `apiKey`-Query) liefert die **ganze Chain** mit Greeks/IV/**OI** je Kontrakt. **Options-Starter $29/mo** (15-min delayed — für EOD-Crons egal). SPX-Index-Optionen (`I:SPX`) ohne Extra-Plan.
- **Grenzen:** (a) `underlying_asset.price` im Snapshot oft **leer** → Spot via `/v2/aggs/<SYM>/prev` (EOD-Close). (b) **Historisch nur Preise, keine Greeks/IV** (wie marketdata) → hist. Backfill weiter per BS-Rekonstruktion. (c) Options-Endpoints brauchen den **Options-Plan** (403 NOT_AUTHORIZED sonst — auch über den MCP, der dieselbe Entitlement nutzt).
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

Der Radar braucht **≥5 Historie-Punkte** je Ticker für den Rank. Neue Ticker haben anfangs nur 1 (Forward-Akku). `scripts/backfill_skew_history.py` füllt sie: holt die **marketdata**-historische Chain (`?date=`, 1 Credit, `strikeLimit`), **invertiert IV je Kontrakt per BS-Bisektion** aus dem Mid, pickt 25Δ → schreibt inkrementell pro Ticker in `options_skew_history.json` (`socket.setdefaulttimeout(20)`, `--years`/`--every-n-td`). **marketdata.app bleibt genau dafür aktiv** (Massive-Historie hat keine Greeks). `verify_skew_iv.py` bestätigt: unsere BS-IV reproduziert die Live-IV auf **< 0,4 Vol-Punkte**.

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
- **Verify-Gates müssen die ZIELGRÖSSE prüfen, nicht Rohwerte.** Eine Mittelung über `iv_atm`/`call_iv`/`put_iv` meldete „0,82 pts — gut", während MUs `call_zeta` das Vorzeichen drehte. Das Produkt nutzt Zeta, also prüft das Gate Zeta — mit Vorzeichenwechsel als hartem FAIL.
- **History stempelte Kalendertage.** Die Vorwärts-Akkumulation nutzte `date.today()`, der Cron läuft aber täglich um 23:00 UTC — auch Sa/So/feiertags. Ergebnis: Einträge für Labor Day mit Freitags Chain, dreifach dupliziert, und `--verify` fand keinen Provider-Tag in der Kursreihe. Fix: `out["session"]` = letzter NYSE-Handelstag; Alt-Einträge werden **umdatiert statt gelöscht** (der Wert stimmt, nur das Label war falsch).
- **Rohwert-Skew vs. SpotGamma-Compass ist kein direkter Vergleich:** der Compass plottet **Percentile in der Eigenhistorie**, nicht Rohwerte. Ein Titel kann bei negativem Roh-Call-Zeta trotzdem im hohen Call-Skew-Percentil stehen, wenn er üblicherweise noch negativer läuft (Fall BE 2026-09-08: unser Roh-Zeta −11,24/+10,40 = defensiv, SpotGamma zeigte bullish). Für den echten Abgleich braucht es belastbare Historie — die Forward-Akkumulation läuft erst seit KW36.

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

### Skew-Historie / Vol-Regime-Radar (offen nach dem Backfill 2026-09-08)

- [ ] **Frontend: Percentile nur aus `cm`/`cm_extrap` rechnen.** `single`-Einträge sind nicht auf 30 Tage normiert und tragen den Sägezahn. `renderSkewQuad()` in `landing/pages/skew.html` filtert bisher nicht danach — ohne diesen Filter mischt der Quadrant normierte und nicht normierte Punkte.
- [ ] **Frontend prüfen: greift noch der Näherungs-Fallback?** Die Rekonstruktionen liefern jetzt echtes `iv_atm`; der dreistufige Fallback in `renderSkewQuad()` (zeta → iv_atm → `(call_iv−put_iv)/2`) sollte auf Stufe 1 landen. Solange Stufe 3 greift, sind beide Achsen spiegelbildlich und der Quadrant wertlos.
- [ ] **Kalibrierung Rekonstruktion ↔ Provider.** Beide Quellen in einer Reihe sind nur zulässig, wenn der Versatz klein ist. Aktuell 1 Vergleichstag (Zeta-Mittel 0,79 pts). Ab ~30 überlappenden Tagen je Ticker messen und ggf. rückwirkend korrigieren; bis dahin gilt die Reihe für **Rangfolgen**, nicht für absolute Skew-Aussagen.
- [ ] **BE aus dem Radar nehmen oder gesondert kennzeichnen** — 28 % Abdeckung, davon 60 % nicht normiert. Gilt sinngemäß für jeden Titel mit ähnlich dünner 25Δ-Liquidität; eine Mindestschwelle (z. B. ≥ 80 normierte Tage) wäre sauberer als eine Einzelfall-Ausnahme.
- [ ] **Backfill auf 2 Jahre und weitere Ticker ausdehnen** — ~20 Min/Ticker/Jahr. Vorher klären, ob 1 Jahr für die Percentile reicht (SpotGamma-Fenster unbekannt).
- [ ] **`--vol-pctl 0.5` an mehreren Tagen gegenprüfen.** Der Wert stammt aus 8 Vergleichen an EINEM Tag — dünn. Sobald mehr Provider-Tage da sind, 0,3/0,5/0,7 erneut vergleichen.
- [ ] **`compute_options_skew.py` kennt keine konstante Laufzeit.** Die Vorwärts-Akkumulation nimmt weiter die 30-Tage-nächste Expiry (seit 2026-09-08 monatsbevorzugt) und schwankt dadurch selbst zwischen ~21 und ~39 Tagen. Für eine saubere gemeinsame Reihe müsste `_cm_interp` auch dort greifen.
- [ ] Blog **Distribution/Backlinks** für den Vol-Regime-Radar-Post; GSC nach Indexierung prüfen.

## 25Δ-Skew (Alt-Verweis)

Der ursprüngliche Skew war Panel G auf `/flows` (marketdata, 2 Credits/Ticker). **Abgelöst** durch die dedizierte `/skew`-Seite + Massive (siehe oben).

## Quellen

- SqueezeMetrics GEX+ Guide (DDOI, VEX, Einheiten): https://squeezemetrics.com/monitor/static/guide.pdf
- SpotGamma — GEX / Call Wall / Put Wall (Support-Center)
- MenthorQ — Vanna/Charm & Post-OPEX-Vola: https://menthorq.com/guide/why-markets-can-go-wild-after-options-expiration-vanna-and-charm-and-the-volatility-effect/
- Cem Karsan (The Derivative/RCM) — Vol-Curves & Vanna/Charm-Flows
- Macroption / Wikipedia „Greeks (finance)" — BS-Formeln (Gamma/Vanna/Charm mit q)

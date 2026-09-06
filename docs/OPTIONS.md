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
| **`/options-flow`** | `compute_options_flow.py` → `options_flow.json` (+ `oi_history/`) | **ΔOI-Flow** (Tag-über-Tag-OI = neue Positionierung, **forward-akkumuliert** — baut sich über Tage auf), **0DTE/Short-Dated** (Front-Expiry-Gamma-by-Strike, EOD-ehrlich) |
| **`/dealer-positioning`** | `snapshot_gex_massive.py` → `gex_summary.json` + `gex_profile_<T>.json` | GEX/Zero-Gamma-Flip/Walls + **Charm-/Vanna-Profile je Strike** (Marker Spot/Flip/Walls) |

**Per-Ticker-Metriken (`compute_options_skew.py`, ein Snapshot/Ticker):** 25Δ-Skew @30d + @90d (Skew-Term), **NE-Skew** (Front-Verfall, spekulativ), ATM-IV-Term-Structure (6 Laufzeiten, Contango/Backwardation), **VRP** (ATM-IV − realisierte 30d-Vola aus Kursen), **25Δ-Butterfly**, **P/C-IV-Ratio**, **Expected Move** (IV·√T), **Volatility-Smile-Kurve** (IV je Delta-Grid 10-40Δ Put/Call + ATM, 30d + NE). Jeder Ticker mit `cats`-Tags. Rank vs. Percentile: `_rank`=(last−min)/(max−min), `_pctl`=Anteil Tage darunter.

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

## Offene TODOs (Options)

- [ ] **ΔOI-Flow** baut sich erst über Tage auf (OI-Historie akkumuliert ab jetzt).
- [ ] **0DTE** ist EOD-limitiert (echtes Intraday-Flow/Tape haben wir nicht).
- [ ] **Sidebar** für Kategorien/Ticker (User-Wunsch) — einheitlich über alle Options-Seiten.
- [ ] **GEX-Universum verbreitern** (mehr als Kern-Set) — Aufwand/Zeit abwägen.
- [ ] **SpotGamma-Top-3 Rest:** Options-Scanner-Layer (IV-Rank-Extreme, Flip-Nähe, ΔOI, VRP-Extreme) noch offen; Compass/Expected-Move teils da.
- [ ] **marketdata.app** nur noch für Backfill nötig — prüfen, ob Abo weiterläuft/gekündigt wird (dann Massive-BS-Historie-Pfad bauen).
- [ ] Blog **Distribution/Backlinks** für den Vol-Regime-Radar-Post; GSC nach Indexierung prüfen.

## 25Δ-Skew (Alt-Verweis)

Der ursprüngliche Skew war Panel G auf `/flows` (marketdata, 2 Credits/Ticker). **Abgelöst** durch die dedizierte `/skew`-Seite + Massive (siehe oben).

## Quellen

- SqueezeMetrics GEX+ Guide (DDOI, VEX, Einheiten): https://squeezemetrics.com/monitor/static/guide.pdf
- SpotGamma — GEX / Call Wall / Put Wall (Support-Center)
- MenthorQ — Vanna/Charm & Post-OPEX-Vola: https://menthorq.com/guide/why-markets-can-go-wild-after-options-expiration-vanna-and-charm-and-the-volatility-effect/
- Cem Karsan (The Derivative/RCM) — Vol-Curves & Vanna/Charm-Flows
- Macroption / Wikipedia „Greeks (finance)" — BS-Formeln (Gamma/Vanna/Charm mit q)

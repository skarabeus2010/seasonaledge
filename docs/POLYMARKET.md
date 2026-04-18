# Polymarket Integration — SeasonAlpha

> Stand: 2026-04-18 · Phase 1+2+3 production-live

Polymarket-Prediction-Market-Daten als **zweites Koordinatensystem** neben der Saisonalität: wo Saisonalität sagt was historisch in einer Zeitphase passiert ist, sagt Polymarket was ein liquider Markt aktuell für zukünftige Ereignisse einpreist.

## Überblick

| Block | Inhalt |
|---|---|
| **Haupt-Page** | `/polymarket` — Fed-Path-Visualizer, Crypto-Ladder, Risiko-Ampel, Divergenz, Historien-Explorer |
| **Zentralbanken** | Teaser-Section mit Fed-Cuts-Verteilung |
| **Crash-Frühwarnung** | Macro-Risiko-Section (Recession, GDP, Hike, Emergency-Cut) |
| **Dashboard** | *nicht* integriert (ticker-unabhängige Daten, siehe Entscheidung unten) |

26 kuratierte Markets aus 7 Polymarket-Events in drei Kategorien: **Fed** (15), **Crypto** (9), **Macro** (2).

## Datenfluss

```
Polymarket Gamma API                Polymarket CLOB API
   (Events, Markets,                   (prices-history
    Snapshots)                          Historie pro Token)
        │                                      │
        ▼                                      ▼
 shared/polymarket_data.py  ◄─────── shared/polymarket_markets.yaml
        │                                (Katalog, 26 Markets mit
        │                                 condition_id + event_id)
        ▼
 shared/supabase_client.py
   upsert_polymarket_markets / _prices
        │
        ▼
  ┌─────────────────────────────────┐
  │  Supabase                       │
  │  polymarket_markets (26 rows)   │
  │  polymarket_prices (Zeitreihe)  │
  └─────────────────────────────────┘
        │
        ▼
 landing/js/polymarket.js (Reader + Renderer)
        │
        ▼
 landing/pages/polymarket.html  + Teaser in zentralbanken / crash-fruehwarnung
```

## Market-Katalog

Kuratiert in [`shared/polymarket_markets.yaml`](../shared/polymarket_markets.yaml). Jeder Eintrag hat `slug`, `category`, `refresh`, `condition_id`, `event_id`, `question`.

| Event-ID | Thema | # Markets | Slug-Muster |
|---|---|---|---|
| 51456 | How many Fed rate cuts in 2026? | 13 | `fed-cuts-2026-0` bis `fed-cuts-2026-12plus` |
| 101936 | Fed rate hike in 2026? | 1 | `fed-hike-2026` |
| 79124 | Fed emergency rate cut before 2027? | 1 | `fed-emergency-cut-2027` |
| 48802 | US recession by end of 2026? | 1 | `us-recession-2026` |
| 80660 | Negative GDP growth in 2026? | 1 | `us-gdp-negative-2026` |
| 89502 | Bitcoin-Preis 2026 | 5 | `btc-above-{100k,120k,150k,200k,250k}-2026` |
| 89519 | Ethereum-Preis 2026 | 4 | `eth-above-{4k,5k,6k,8k}-2026` |

**Neuer Market hinzufügen:**
1. In YAML mit leerer `condition_id` anlegen.
2. `py -3.12 scripts/polymarket_discover.py --update-yaml` füllt ID + Metadata.
3. `py -3.12 scripts/polymarket_discover.py --sync-db` schreibt in Supabase.
4. `py -3.12 scripts/polymarket_backfill.py --slug <slug>` zieht Historie.

## Datenbank

Migration: [`scripts/create_polymarket_tables.sql`](../scripts/create_polymarket_tables.sql) — idempotent, im Supabase SQL-Editor ausführen.

### `polymarket_markets`
Katalog, eine Zeile pro Slug. Wichtige Spalten:

| Spalte | Typ | Zweck |
|---|---|---|
| `condition_id` | text unique | Polymarket Condition-ID (0x...) |
| `slug` | text unique | URL-/DB-Slug, stabil |
| `question` | text | Original-Frage |
| `category` | text | `fed`, `macro`, `crypto` |
| `end_date` | timestamptz | Resolution-Deadline |
| `yes_token_id` / `no_token_id` | text | CLOB-Tokens für prices-history |
| `liquidity_usd`, `volume_total_usd` | numeric | aus Gamma `liquidityNum` / `volumeNum` |
| `meta` | jsonb | `gamma_id`, `event_id`, `outcomes`, `neg_risk` |
| `active` | bool | false = aus UI raus |

### `polymarket_prices`
Zeitreihe der YES-Preise. Unique-Key `(condition_id, ts)` — UPSERT-idempotent.

| Spalte | Typ | Zweck |
|---|---|---|
| `condition_id` | text | FK-soft zu markets |
| `ts` | timestamptz | Snapshot-Zeit |
| `yes_price` | numeric 0..1 | implizite Wahrscheinlichkeit |
| `volume_24h`, `spread` | numeric | aus Gamma Snapshot |
| `source` | text | `clob` (refresh), `prices-history` (backfill) |

### RLS + GRANTs

```sql
ALTER TABLE polymarket_markets ENABLE ROW LEVEL SECURITY;
GRANT SELECT ON polymarket_markets TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON polymarket_markets TO service_role;
CREATE POLICY "anon_read" ON polymarket_markets FOR SELECT TO anon, authenticated USING (true);
-- analog fuer polymarket_prices
```

**Wichtig:** RLS alleine reicht nicht — ohne `GRANT` gibt Postgres `42501 permission denied` auch für Reads.

## Scripts

Alle drei liegen in `scripts/`, alle nutzen `shared/polymarket_data.py` und schreiben in Supabase via `shared/supabase_client.py`.

| Script | Zweck | Typischer Aufruf |
|---|---|---|
| `polymarket_discover.py` | Gamma-Events per Tag absuchen, Kandidaten scoren, YAML füllen, Katalog in DB schreiben | `--update-yaml --sync-db` |
| `polymarket_refresh.py` | Aktuellen YES-Snapshot pro Market via Gamma Markets-Endpoint | Ohne Args (alle aktiven Markets) |
| `polymarket_backfill.py` | Volle Historie via CLOB `prices-history` (default `interval=max`) | Ohne Args (alle 26 Markets) |

## Frontend

### JS-Modul `landing/js/polymarket.js`
Gemeinsamer Reader + Chart-Renderer, von allen Pages genutzt. Exportiert unter `SA.polymarket`:

**Data Loader:**
- `loadCatalog()` — aktive Markets aus `polymarket_markets`
- `loadLatestPrices(conditionIds)` — neueste Snapshot pro Market (Dict `{cid: row}`)
- `loadHistory(conditionIds, days)` — Preis-Historie N Tage

**Compute:**
- `computeFedDistribution(markets, latest)` → `{dist, totalProb, expectedCuts, expectedBps}`
- `collectYearEndReturns(priceRows, asOfDate)` → Samples für Saisonal-Prior
- `empiricalAboveProbability(samples, targetReturn)` → Prior für "Target erreicht"

**Renderer (schreiben in DOM-IDs):**
- `renderFedDistChart`, `renderFedTrendChart` — Fed-Cuts-Viz
- `renderRiskGauges` — 4-Kachel-Ampel
- `renderCryptoLadder` — horizontale Target-Balken
- `renderCryptoDivergence` — Saisonal vs. Markt Tabelle
- `renderHistoryMulti` — Multi-Line-Zeitreihe beliebiger Markets
- `renderMarketsTable` — sortierbare 26-Row-Tabelle

### Pages
| Page | Integration |
|---|---|
| `landing/pages/polymarket.html` | Alle Sektionen: Fed-Path, Risiko, Crypto-Ladder, Divergenz, Historien-Explorer, Katalog |
| `landing/pages/zentralbanken.html` | `<details>` mit Fed-Cuts-Chart + Top-KPIs (Erwartungswert, wahrscheinlichste Outcomes) |
| `landing/pages/crash-fruehwarnung.html` | `<details>` mit Risiko-Ampel + Historien-Multi-Line |

**Dashboard absichtlich ausgeklammert:** Polymarket-Daten sind ticker-unabhängig. Im ticker-zentrierten Dashboard würde das verwirren, solange es keinen pro-Ticker-Polymarket-Score gibt.

### Navigation
Link `Polymarket Odds` in allen 4 Nav-Stellen: `components/nav.html` Events-Dropdown, `components/footer.html` Events-Spalte, `landing/index.html` Inline-Nav + Inline-Footer.

## Cron / Auto-Refresh

In [`scripts/nightly_refresh.py`](../scripts/nightly_refresh.py) als **Phase G** eingebaut. Nightly-Workflow läuft Mo–Fr 20:30 UTC (siehe `.github/workflows/nightly_refresh.yml`).

| Sub-Phase | Wann | Was |
|---|---|---|
| G1 | jeden Nightly-Run | `polymarket_refresh.py` — Snapshot aller 26 Markets (~11s) |
| G2 | nur Montags (`weekday == 0`) | `polymarket_backfill.py` — volle CLOB-Historie (~47s) |

Nightly schreibt ein Logbuch in `refresh_log`. Polymarket-Phase loggt in app.log mit `[phase-g]` / `[phase-g2]`-Präfix.

### Intraday-Tier nahe FOMC

Separater Workflow [`.github/workflows/polymarket_intraday.yml`](../.github/workflows/polymarket_intraday.yml) läuft stündlich :23. Das Script ruft sich mit `--near-fomc-only` auf und prüft intern [`shared.fed_dates.is_near_fomc`](../shared/fed_dates.py) — early-exit wenn heute nicht im FOMC-Fenster (FOMC-Tag −2 bis +1). So bekommen wir dichte Snapshots an den Tagen wo Polymarket-YES sich tatsächlich bewegt, ohne den Rest des Jahres unnötig API-Traffic zu erzeugen.

## Credentials

Zwei getrennte Keys in `/opt/seasonaledge/.env` (und lokal `C:\dev\SeasonalEdge\.env`):

```env
SUPABASE_URL=https://<ref>.supabase.co
SUPABASE_KEY=<service-role-jwt>     # Backend-Scripts (Cron, Write)
SUPABASE_ANON_KEY=<anon-jwt>        # Frontend-HTML-Injection
```

Die Trennung ist **kritisch**: `deploy/inject_credentials.sh` injiziert `SUPABASE_ANON_KEY` in jede HTML-Page. Wenn nur ein Key da ist und der service-role, würde der service-role ins Frontend leaken → globaler RLS-Bypass für alle Browser. Das Script prüft per JWT-Role-Decode und lehnt den Fallback ab.

## Deploy

Auto-Deploy via `.github/workflows/deploy.yml` bei jedem push auf `master`. Keine manuellen ssh-Befehle nötig.

Status der letzten Runs:
```
gh run list --workflow=deploy.yml --limit=5
```

## Divergenz-Score (Phase 3)

Empirischer Prior aus eigener Preis-DB gegen Polymarket-Wahrscheinlichkeit:

1. Für jeden Crypto-Market (z.B. BTC ≥ $150k by 2026 EOY): aktueller Kurs → benötigter Return.
2. Für jedes vergangene Jahr: welcher Preis am heutigen Kalendertag X.Y des Jahres, welcher am Year-End? → Year-End-Return-Sample.
3. `% der Samples mit Return ≥ required` = Saisonal-Prior.
4. Divergenz in pp = Prior − Markt YES. Positiv (grün) = Markt unterschätzt, negativ (rot) = Markt überschätzt.

**Brier-Score** steht noch aus — braucht resolved markets. Die 26 kuratierten Markets resolven erst Ende 2026/Anfang 2027. Historische resolved markets (anderer Scope) sind Kandidat für Phase 4.

## Troubleshooting

| Symptom | Ursache | Fix |
|---|---|---|
| `42501 permission denied for table` | GRANT fehlt (RLS reicht nicht) | Migration erneut laufen lassen |
| `fetch_current_price` liefert `None` | Script übergibt `yes_token_id` statt `conditionId` | conditionId nutzen — siehe `polymarket_refresh.py` |
| Backfill liefert nur 1 Datenpunkt | CLOB `interval=1d` = letzte 24h | `--interval max` (ist Default) |
| Windows `UnicodeEncodeError: \u2191` | cp1252 stdout kann `↑↓` nicht | `PYTHONIOENCODING=utf-8` |
| Service-role-Key im Frontend-HTML sichtbar | `SUPABASE_ANON_KEY` fehlt in .env | Anon-Key als separate `.env`-Zeile |
| nightly Phase G schreibt nicht | Container-Env hat anon-Key | `.env` korrigieren, `docker compose up -d --force-recreate app` |

## Roadmap

**Short-term:**
- [ ] Phase 3b: Brier-Score auf historisch resolved Polymarket-Markets (Sample-Set aufbauen)
- [ ] Fed/Macro-Divergenz (andere Baselines als Yearly-Return-Prior)
- [x] **2026-04-18** Newsletter-Sektion mit Top-Divergenzen der Woche (Crypto-Targets)
- [x] **2026-04-18** Intraday-Refresh-Tier nahe FOMC (±2d Fenster)

**Long-term:**
- [ ] Weitere Event-Kategorien (Elections, Geopolitik, Sports wenn relevant)
- [ ] Pro-Ticker Polymarket-Score via Mapping (dann auch Dashboard-Integration möglich)

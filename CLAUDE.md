# CLAUDE.md — SeasonAlpha

> Version 47.0 | 2026-08-04 | **Vibe-Trading Alpha-Zoo → 3 neue Indikator-Filter** (`indicators.js`: ML-Regime Percentil-Clustering, Carhart Momentum 12M-1M, Jegadeesh StRev 21d) · **SPY Down-Month ToM Reversal** (Backtest 15J: Sharpe 0.21→0.34, WR 68→72%, PF 1.80→2.39; `calc_downmonth_tom` in `strategy-compute.js`, SA.STRATEGIES `monat`-Kategorie, Dashboard-Signal) · **Trifecta-Chart-Bug** (x-Achse nutzte Handelstag-Zähler statt Kalendertag → Chart endete scheinbar Ende Mai; Fix: `lastCalDay` aus Datum des letzten Handelstags) · **FlashAlpha MCP** (`claude mcp add flashalpha --transport http https://lab.flashalpha.com/mcp`, 71 Tools: GEX/IV-Surface/Term-Structure/Dealer-Positioning/0DTE/Flow-Scan; **Key per Tool-Parameter**, NICHT Header; Free 5/Tag, Quota-Reset 00:00 UTC; Tools nur in neuer Konversation verfügbar) · Blog DE+EN: SPY Turn-of-Month Down-Monat Reversal Backtest
> Version 46.0 | 2026-07-10 | **Options-/Dealer-Positioning-Engine** (`scripts/compute_gamma_exposure.py`: GEX/Gamma + **Vanna + Charm** per Black-Scholes, Finite-Differenzen-`--self-test`, Call/Put/Absolute-Walls, Zero-Gamma-Flip, **Skew**, **Markt-Gamma-Index**, Per-Strike/Per-Term-Profile → Exposure-by-Strike/Term-Charts `render_gex_profile.py`) · `docs/OPTIONS.md` · 2 Agenten (`options-flow-analyst`, `market-flows-scout`) · Lessons: naive Dealer-Heuristik ≠ SpotGamma-Inventory-Modell, Yahoo-Options **nur US** (DAX/`^GDAXI`/`.DE` leer → ETF-Proxy EWG/FEZ oder paid Eurex), Walls = Netto-Gamma je Strike (Call≥Spot/Put≤Spot), Charm ÷365 = daily, matplotlib `text.parse_math=False` für `$`-Labels. **Nächster PR: `/dealer-positioning`-Frontend + Nav.** Papers-Trove in `raw/papers/`.
> Version 45.0 | 2026-07-28 | **Supabase Pro** (Free-Tier DB-Quota erschöpft → 6 Tage Write-Block → Upgrade auf Pro) · **DB Recovery** (Nightly 7d-Fenster, Full Scanner 324/324, alle Crons manuell getriggert) · Lessons Learned: Free-Tier still-schlägt-zu, "Nightly Data Update" ist Altlast (korrekt: "Nightly DB Refresh"), Completeness-JSON-URL `/landing/data/`, Polymarket-Backfill vs. Standalone, regime_scores 1/324 = Design
> Version 44.0 | 2026-07-15 | **Backtest-Kombinations-Engine** (TDOM+Indikator, 5 Strategien × 10 Ticker, Walk-Forward, Stop-Loss-Grid, LBR vs. MACD, Neue Ticker) · **UI-Integration** (TDOM Event-Typ, Preset-Karten, `loadPreset()`-API) · **Second Brain** (`raw/`+`wiki/`+`/sa-ingest`) · Lessons Learned: GLD+Bollinger Walk-Forward robust (OOS Sharpe 2.41), Edge ist Edelmetall-Phänomen, LBR asset-klassen-abhängig, Stop-Loss-Regeln je Signaltyp
> Version 43.0 | 2026-07-15 | **Stripe-Integration** (3 Supabase Edge Functions: create-checkout-session + stripe-webhook + create-portal-session, Pricing-Page aktiviert, docs/STRIPE_SETUP.md) · Lessons Learned: Edge Functions via `supabase secrets set`, CORS-Header Pflicht, portal session braucht stripe_customer_id aus DB
> Version 42.0 | 2026-07-03 | **Marktkalender** (`/kalender`, Auth-Gate + Premium-Gate, ICS-Export, 109 Events 18-Monate) · **i18n EN-Skip-Fix** (auth-gated Pages aus Link-Rewrite ausgeschlossen) · Lessons Learned: `_skipPrefixes`-Pflicht, `build_calendar_data.py` pandas-Issue, `/en/<slug>` Redirect-Pattern
> Version 41.0 | 2026-06-21 | **Daily-Newsletter-Rework** (ML-Regime → LBR/RSI/SC/TS/Gesamt-Scoring, Kernliste, alle Notenbanken, „Warum"-Zeile, Mail-Size-Fix) · **DB-Audit entrauscht** (Feiertags-/Legitim-Absenz-Logik) · **SEO-Content-Offensive** (alle 18 dünnen Tool-Seiten: Unique-Content + FAQPage, `docs/SEO_TODO.md`) · Lessons Learned in [docs/CHANGELOG.md](docs/CHANGELOG.md) + Email/i18n-Regeln ergänzt
> Version 40.0 | 2026-06-15 | Kalender-Spec vervollständigt (OPEX/VIX börsenspez. + holiday-aware, Zeit-Indizes TDOM/TDOY/CDOM/CDOY, Notenbank-Termine je Region, Asien HKEX/KRX/TSE) + **Prüfagent** (`verify_calendar_rules.py`, wöchentl. Cron) · **SEO-Foundation**: `/ueber-uns` (E-E-A-T), 1. Daten-Studie (DAX-September), SEO-Audit · **8 Subagenten** (4 neue Wachstums-Agenten + `docs/AGENTS.md`) · **Embed-Backlink-Asset** (`/embed` + Einbetten-Button auf Jahreszyklus)
> Version 39.0 | 2026-06-14 | Ticker-Universum 270→324 (Dow-30/DAX-40 vollständig, Orphan-Adoption, SAP→SAP.DE) + DB-Vollständigkeits-Audit/Onboarding-Guardrails + Klarstellung: **Streamlit produktseitig ungenutzt** (nur Container-Keep-alive), `landing/` = Frontend

## Projekt

**SeasonAlpha** — Web-Plattform für saisonale Finanzmarkt-Analyse (ETFs, Aktien, Futures, Crypto).
Freemium + Premium. **Frontend = statische HTML-App (`landing/`)** + Supabase + Stripe. Domain: `seasonalpha.ai`.
**Streamlit wird produktseitig NICHT genutzt** (kein `/app/`-Link im Frontend); `seasonal_app.py` läuft nur noch als Keep-alive-Hauptprozess des `app`-Containers, damit die Crons via `docker exec` reinkommen.

## Entwicklung

```
Pfad:   C:\Dev\Seasonaledge\
Frontend: landing/ = statisches HTML (nginx serviert; KEIN Server-Start nötig)
Python: lokal `py -3.14` (= Container-Version), für Skripte/Backfills
Streamlit: legacy/ungenutzt (`py -m streamlit run seasonal_app.py` nur falls man die Alt-App wirklich braucht)
Server: ssh root@178.104.75.46  (Docker: seasonalpha-app / seasonalpha-nginx / seasonalpha-certbot)
Host-Pfad: /opt/seasonaledge
```

## Projektstruktur (High-Level)

```
seasonal_app.py          ← Streamlit (UNGENUTZT — nur Keep-alive-Prozess des app-Containers)
shared/                  ← Berechnungs-/Daten-/UI-Module (siehe Module-Liste unten)
scripts/                 ← Batch-Jobs (Nightly, Intraday, Newsletter, Regime, Audit)
pages/                   ← Streamlit Pages (Legacy, ungenutzt)
landing/                 ← Statische HTML-App (= DAS Frontend)
  pages/                 ← 31 HTML-Feature-Pages (inkl. kalender.html — auth-only)
  ueber-uns.html         ← Methodik/About (E-E-A-T, root)
  embed.html             ← Standalone-Seasonal-Chart zum Einbetten (Route /embed, framebar)
  js/                    ← JS-Module (shared compute + charts + i18n)
  i18n/                  ← de.json + en.json (1222+ Keys, seit KW24)
  css/app.css            ← V3 Ultra Design System
  components/            ← nav.html, footer.html (JS-Include)
  data/                  ← Pre-computed JSON (inkl. market_calendar.json + .ics)
blog/                    ← Markdown-Blog-Engine
  posts/                 ← 24 DE Markdown-Posts
  posts/en/              ← 24 EN Markdown-Posts (seit KW24)
  templates/             ← bilinguales blog_post.html + blog_index.html
  output/                ← Generiertes HTML (gitignored, wird serverseitig gebaut)
seo/                     ← Programmatic SEO + statische Tool-Pages
docs/                    ← Ausgelagerte Dokumentation
.claude/agents/          ← 8 Subagenten (versioniert) — Einsatz-Anleitung: docs/AGENTS.md
```

**Subagenten (`.claude/agents/`, Anleitung [docs/AGENTS.md](docs/AGENTS.md)):** Content (`blogger`, `saisonalitaet-scout`), Daten (`daten-auditor`), SEO/Wachstum (`seo-experte`, `wachstum-distributor`, `seo-seiten-bauer`, `gsc-analyst`, `frontend-qa`), Options/Flows (`options-flow-analyst`, `market-flows-scout`), Backtest (`backtest-analyst`). Flywheel: scout→blogger→distributor→[posten]→gsc-analyst. Wachstums-Engpass = Off-Page (junge Domain, wenige Backlinks) → Embed-Backlink-Hebel (`/embed`).

### Module / Pages — Detail-Listen in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

- **Shared (`shared/`)** — Kern: `yahoo_downloader` (Stooq-Fallback, einziger Cache), `data` (Supabase-First), `charts` (`apply_se_theme`), `ki_score`, `tdom_analysis`, `anomaly_engine`, `significance_gauge` (key_prefix!), `footer`, `i18n`. ⚠️ Gelöscht (ML-Pipeline KW16): `mstl_decomposition`, `chronos_forecast`, `neural_prophet_forecast`, `ai_models`.
- **Frontend JS (`landing/js/`)** — `app.js`, `charts.js` (ApexCharts), `holidays.js` (Gauss-Ostern), `*-compute.js`, `tour.js`, `auth.js`, **`i18n.js`** (SA.i18n IIFE).
- **HTML-Pages (`landing/pages/`)** — 30 Feature-Pages (Dashboard, Zyklen, Events, Strategien, KI, Backtest …).

## Kern-Methodik: NORMALISIERTE RENDITEN

Prozentuale Renditen normiert auf 100 — NICHT absolute Preisänderungen. Jedes Jahr startet bei 100, tägliche Returns kumulieren darauf. **Niemals** TradingView-Methode (`close - close[lookback]`).

## Import-Header (nur Streamlit-Pages — Legacy/ungenutzt)

```python
import sys, os, pathlib
try:
    _project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
except NameError:
    _project_dir = os.getcwd()
if not os.path.isdir(os.path.join(_project_dir, "shared")):
    for _candidate in [os.getcwd(), os.path.dirname(os.path.abspath(sys.argv[-1])) if sys.argv else ""]:
        if os.path.isdir(os.path.join(_candidate, "shared")):
            _project_dir = _candidate; break
if _project_dir not in sys.path: sys.path.insert(0, _project_dir)
```

## Kritische Regeln (nicht-offensichtlich, aus Incidents gelernt)

### Daten / Python

- `import yfinance` VERBOTEN → `from shared.yahoo_downloader import download_data` (oder besser `shared.data`, Supabase-First)
- Cache NUR in `yahoo_downloader.py` — kein `@st.cache_data` anderswo
- `df['Date'].iloc[0].strftime()` statt `df.index[0].strftime()`
- `print()` verboten → `app_logger.debug()`
- API-Keys via `os.environ[...]` + `.env` (in `.gitignore`), `logs/` niemals in Git
- Stooq: Session-Cookie erforderlich (`session.get("https://stooq.com/")` vor CSV)
- **`download_data` ist Yahoo-primär + Stooq-Fallback → der Datenbereich kann je nach antwortender Quelle VARIIEREN.** Beispiel ^GSPC: Yahoo liefert ab **1970**, der Stooq-Fallback ab **1950** (^SPX). Für Blog-/Studien-Zahlen IMMER die reproduzierbare Yahoo-Default-Basis nutzen (`download_data.clear()` + neu laden) und **Text↔Chart konsistent** halten — der serverseitig gebaute Chart nutzt die Yahoo-Primärquelle. Bei „seit Jahr X"-Aussagen den realen Bereich verifizieren, nicht annehmen.
- OHLC Cross-Day VERBOTEN: `Open[t]/Close[t-1]` mischt adj_factors → Dividend-Bias. Overnight/Intraday per Residual: `overnight = total - intraday`
- Nightly Refresh: letzte **7 Tage** Upsert-Fenster (seit Phase D KW20). Phase D prüft zusätzlich letzte 14 Tage auf NULL `log_return` und berechnet nach.
- **Korrekter Nightly-Workflow: "Nightly DB Refresh"** (`nightly_refresh.yml`, `scripts/nightly_refresh.py`). **NICHT** "Nightly Data Update" (`nightly_update.yml`) — das ist ein Altlast-Workflow (TypeError: DownloadManager, tut nichts außer Exit 0).
- **Supabase Free Tier = Write-Block ohne Fehler**: DB-Quota-Überschreitung blockiert alle INSERT/UPSERT lautlos; nightly läuft durch (Exit 0), Heartbeat SELECT geht, schreibt aber nichts. Recovery: Pro-Upgrade → "Nightly DB Refresh" manuell triggern (7-Tage-Fenster füllt Lücken) → Full Scanner Run (KI-Scores alle 324 Ticker). Completeness-Check-JSON: `https://seasonalpha.ai/landing/data/db_completeness.json`.
- `log_return`-Spalte in Supabase wird von `preprocess()` genutzt wenn vorhanden
- Zeitstempel UTC: `datetime.now(timezone.utc)` nutzen (nicht `datetime.utcnow()`, deprecated ab 3.12)
- **Neuen Ticker aufnehmen: NUR via `py scripts/onboard_ticker.py <T>`** (nach Eintrag in `symbols.py`). Macht Yahoo-Validierung + Voll-Backfill + tickers.json-Regen + DB-Upsert in einem. NIEMALS nur Preise laden ohne `symbols.py`-Eintrag → sonst „Orphan" (wird weder auditiert noch refreshed, veraltet still). `symbols.py`/`get_all_tickers()` = einzige Quelle der Wahrheit; Backfill-Skripte ihre Ticker-Liste IMMER daraus speisen, nie aus DB-Tabellen (prices-Full-Scan timeoutet, `tickers`-Tabelle kann fehlen).
- **Lokal (Windows):** `py -3.14` nutzen (= Container-Version; Default-`py` ist 3.9 und scheitert an `X | None`-Syntax in shared-Modulen). Bei Skript-Läufen mit Datei-Umleitung `PYTHONUTF8=1` setzen (cp1252 crasht sonst an ✓/⚡-Prints).
- Vollständigkeit prüfen: `py scripts/check_db_completeness.py` (Freshness/Coverage/Gaps/Events + Orphan- & Stale-Tail-Erkennung; wöchentl. Cron `db_completeness.yml`). Orphan-Check braucht RPC `create_distinct_price_tickers_rpc.sql`.
- **Cron-erzeugte JSONs unter `landing/data/` NIEMALS committen.** `deploy.yml` macht vor dem Pull `git checkout -- landing/` (nötig für die In-Place-Änderungen von `inject_credentials.sh`). Getrackte Cron-Dateien werden dadurch bei **jedem** Deploy auf den committeten Stand zurückgeworfen — die Seite zeigte so tagealte, teils **invertierte** Regime-Daten (Gamma-Index +12,218 → −3,398). Diagnose-Trick: untrackte Dateien (`gex_history/*.json`) überleben, getrackte fallen zurück — die Differenz beweist den Deploy als Ursache. Seit 2026-08-13 sind die 13 betroffenen Dateien in `.gitignore`. Neue Cron-Outputs dort ebenfalls eintragen.
- **Yahoo-Options: `openInterest=0` im Vormittagsfenster (UTC).** Yahoo liefert dann die **volle** Chain mit HTTP 200, aber ohne Open Interest (geprüft 05./06./13.08., je ~08:50–10:15 UTC: SPY 4/1461 brauchbar = 0,3 %). Der OI-Filter wirft alles weg, und `analyze()` meldete früher trotzdem **Erfolg** mit einer Handvoll Kontrakten → plausibel aussehender Müll (`net-GEX −0.000 Mrd, short_gamma`). Seit 2026-08-13 verwirft `analyze()` die Chain, wenn bei ≥100 Roh-Kontrakten <5 % brauchbar sind, und `snapshot_gex.py` schreibt gar nichts, wenn <60 % der Ticker durchkommen. **Der Cron um 22:15 UTC liegt richtig** (konstant 20/20). Ad-hoc-Läufe am Vormittag sind wertlos — stattdessen `--snapshot <datum>` gegen das Archiv nutzen.
- **OOM in Full-Universe-Schleifen (exit 137 = SIGKILL, NICHT Supabase-Fehler):** `download_data` ist `@st.cache_data` → cached JEDE Voll-Historie im Memory. In Per-Ticker-Loops über alle 324 Ticker (Scanner/Backfills) IMMER `clear_cache()` (= `download_data.clear()`) **+ `gc.collect()` pro Ticker**, sonst OOM-Kill ab ~Ticker 70. Haben: `full_scanner_run` (seit 2026-06-14), `backfill_tdoy`/`backfill_ohlc` (gc). Bei neuen Full-Universe-Skripten mitdenken.

### Handelstage & Börsen-Awareness

- **Vollständige Spec (Regeln 1-8, Prüf-Spec für Verifikations-Agent): [docs/TRADING_CALENDAR_RULES.md](docs/TRADING_CALENDAR_RULES.md)**
- **Kalender folgt dem Handelsplatz (Ticker-Suffix), NICHT dem Heimatland.** Kein Suffix = US-gelistet → NYSE (auch ausländische ADRs wie AZN/BP/ASML/LIN/NVS/UBS!). `.DE`→XETRA, `.PA`→Euronext, `.MI`→Mailand, `.L`→LSE, `.SW`→SIX, `.ST`→Stockholm, `=X`→Forex(Mo-Fr), `-USD`→Crypto(24/7). Bei Mapping-/Kalenderänderung: `backfill_tdoy --ticker <T>` neu rechnen + Frontend `holidays.js::detect()` spiegeln.
- Immer Trading Days zählen, nie Kalendertage
- TDOM/TDOY sind **börsenspezifisch**: `render_trading_day_header(df, ticker=ticker)` — IMMER ticker übergeben
- Holiday-Kalender aus `shared/symbols.py::get_exchange_for_holidays(ticker)` → NYSE/XETRA/EURONEXT/MILAN/LSE/SIX/STOCKHOLM/TSE/FOREX/CRYPTO. NYSE inkl. einmaliger Sonderschließungen (`_NYSE_SPECIAL_CLOSURES`, z.B. 09.01.2025 Staatstrauer Carter)
- **Börsen-Feiertage ≠ Bank-Feiertage!** XETRA handelt an **Pfingstmontag + 3. Oktober** (nur 8 handelsfreie Tage); **Observed-Shift NUR bei NYSE/LSE** (EU-Börsen: kein Mo-Ersatz bei Wochenend-Feiertag). Beide Falle-Klassen produzieren *falsche* Feiertage → falsche TDOM.
- **Kalender-Regeln prüfen: `py scripts/verify_calendar_rules.py`** (deterministischer Prüfagent, alle 9 Regeln, PASS/WARN/FAIL). Rückwärts-Check (Kurs-vorhanden-trotz-Feiertag) NUR mit Einzelaktien + Clean-Ära ≥2022 (Indizes/Stooq-Alt-Daten haben Phantome). Spec: [docs/TRADING_CALENDAR_RULES.md](docs/TRADING_CALENDAR_RULES.md)
- `is_trading_day(today, exchange)` — NICHT `weekday < 5`
- Frontend: `SA.holidays.detect(ticker)` + `SA.holidays.isTradingDay(date)`, Gauss-Ostern via `SA.holidays.goodFriday(year)`
- TDOM im Frontend: IMMER aus Holiday-Kalender berechnen, NICHT aus letztem DB-Row ableiten (DB kann vor Intraday-Refresh veraltet sein)
- CRYPTO: `is_trading_day()` immer True (24/7). FOREX: Mo-Fr ohne Feiertage (Karfreitag offen)
- OPEX = Kalender-3.Freitag, bei NYSE-Feiertag auf vorherigen HT vorverlegt. Triple Witching = Mar/Jun/Sep/Dez
- VIXpiration = OPEX-Freitag − 30 Kalendertage (= Mi). Ist Basis-Fr ODER Settlement-Mi Feiertag → −1 HT
- `toISOString()` NIE für lokale Datumsvergleiche (MESZ→UTC verschiebt auf Vortag) — nutze `localDateStr`

### Charts / UI / Statistik / KI — Detail: [docs/UI_PATTERNS.md](docs/UI_PATTERNS.md)

Häufigste Stolperfallen (Rest in UI_PATTERNS.md, Plotly-Theme in CHARTS.md):
- Streamlit-Charts NUR via `apply_se_theme()`/`apply_se_heatmap_theme()`. **Inline `update_layout` VERBOTEN.** `st.metric` vermeiden → HTML-Flex-Karten.
- Frontend = ApexCharts (kein Plotly.js): Multi-Serie als **plain arrays mit null**, NICHT `{x,y}` (bricht v4). Multi-Axis → separate Instanzen mit `chart.group`.
- KPI-Standard: globale `.kpi`/`.kpi-label`/`.kpi-value`-Klassen aus `app.css`. Cards: `background:var(--card)`, KEIN Gradient. V3 Ultra: Pure Black + Gold (#e8a820), Dark Mode First.
- Info-Badge-Tooltip: pure CSS, Parent `position:relative` + KEIN `overflow:hidden`.
- **Quantile NIE Floor-Indexing** → lineare Interpolation wie numpy. **Backtest look-ahead-bias-frei: `filterMask[entryIdx-1]`, NICHT `entryIdx`.**
- Stats null vs constant-fill: `avg/std/Detrend` nutzen full_365; `Perzentil/Drawdown/Heatmap` müssen `if (d >= yo.last_actual_day) continue` filtern.
- KI Composite: 4 Sub-Scores à 0-2.5 → 0-10 (Bullish ≥6.5, Bearish ≤3.5). Anomalie-Radar misst NUR 10 Tage. Präsidentenzyklus 3=Zwischen (nicht „Mitte"), `((year-2020)%4+4)%4+1`.

### Deployment / Mobile

- Frontend = statisches HTML (`landing/`, nginx direkt). Streamlit `/app/` ist vestigial (nur Container-Keep-alive, produktseitig ungenutzt)
- Neue Pages: `loadComponent('nav-container', ...)` für Nav — NICHT manueller fetch (umgeht `initNav()` → Burger tot auf Mobile)
- Supabase-Credentials Inline-Script MUSS VOR `app.js` in jeder Page: `<script>window.__SA_SB_URL='%%SUPABASE_URL%%';window.__SA_SB_KEY='%%SUPABASE_ANON_KEY%%';</script>`
- Cache-Strategie: Nginx `/landing/*.{css,js}` → `max-age=0, must-revalidate` + ETag. `deploy/inject_credentials.sh` hängt `?v=<git-short-sha>` an alle CSS/JS-Refs
- `body.sa-sidebar-collapsed` Regeln in `@media (min-width: 1280px)` kapseln (sonst Override auf Mobile durch Spezifität)
- `.nav__links` Mobile: `height: calc(100dvh - var(--nav-h))` + `overflow-y:auto` (nicht vh, iOS-Bug)
- iOS 16px Input-Fix: Sidebar-Inputs auf Mobile explizit `font-size:16px` (sonst Auto-Zoom)
- Docker JSON-Transfer: im Container generieren, `docker cp` auf Host
- **Nginx-Config-Änderung aktivieren: `docker compose restart nginx` — NICHT `nginx -s reload`.** Single-File-Bind-Mount (`./deploy/nginx.conf:/etc/nginx/conf.d/default.conf`): `git pull` ersetzt die Datei (neuer Inode), der laufende Container hängt am alten Inode → `reload` liest STALE. `restart` re-resolved den Mount. (Symptom im Deploy 2026-06-13: `exec … nginx -s reload` blieb wirkungslos, `/en/*` zeigte trotz „Deploy success" die alte Version.)
- nginx-Config minimal/proven halten: `nginx -t`-Fehler im Deploy wird per `|| echo` verschluckt (non-fatal) → fehlerhafte Config bleibt still inaktiv, alte läuft weiter. Neue Blöcke an bereits laufenden orientieren (lokal kein `nginx -t` ohne Docker).
- Reine HTML/Asset-Änderungen (kein Config): `git pull` reicht (nginx serviert aus gemountetem `./landing` ro); ggf. Browser-Hard-Refresh
- `blog/output/` UND `landing/en/` sind gitignored — serverseitig im Deploy generiert: `blog_builder.py --build` bzw. `build_en.py --write` (beide DE+EN), letzteres auf dem Host nach `inject_credentials.sh`
- **`build_calendar_data.py` läuft in `inject_credentials.sh` via system python3 — auf dem Server fehlt `pandas` dort → non-fatal (JSON+ICS sind committed, Deploy geht durch).** Für echtes Live-Update manuell: `docker exec seasonalpha-app python3 scripts/build_calendar_data.py`. Langfristig: Schritt in `inject_credentials.sh` auf `docker exec` umstellen.

### Email / Brevo — Detail: [docs/EMAIL_TESTING.md](docs/EMAIL_TESTING.md)

- Brevo **201 = angenommen, NICHT zugestellt** — Status im Dashboard („Statistics → Email Activity") checken.
- Sender-Domain MUSS Domain-Auth haben (SPF+DKIM+DMARC); Single-Sender reicht für Newsletter nicht (Gmail/Outlook blocken).
- **Gmail kappt Mails > ~102 KB** („[Nachricht gekürzt]") → Footer/Inhalt fehlt, oft mitten in einer Zeile. Wiederkehrende Inline-Styles in `<style>`-CSS-Klassen auslagern (Daily-Newsletter: ~102 KB → 47 KB). **`daily_newsletter.py --dry-run` enthält die Watchlist NICHT** (pro Empfänger erst in `render_email` angehängt) → echte Mailgröße via `render_email`-Pfad oder `--test` messen.
- **Test-Send NICHT direkt nach PR-Merge** (`gh workflow run daily_newsletter.yml`): Auto-Deploy startet den Container neu, `docker exec` trifft Restart → kein Output, kein Versand, Workflow trotzdem „success" (Run auffällig kurz). ~1-2 Min warten.
- **Brevo-Key-Rotation (Lessons, docs/EMAIL_TESTING.md#security-api-key-rotieren):** (1) **Keys desselben Kontos teilen den Präfix** `xkeysib-5440ec2afed4…` → nur an der **Endung** (letzte ~6 Zeichen) unterscheiden, NIE am Präfix. (2) Brevo **Authorised-IPs**: API-Call von nicht-freigegebener IP → `401 „unrecognised IP address"` = **kein** Key-Fehler; Key nur von der **Server-IP** testbar. (3) Deploy überträgt `.env` NICHT → Server-`.env` (`/opt/seasonaledge/.env`) separat updaten + `docker compose up -d --force-recreate app`. (4) SSH aus Claude-Umgebung = permission denied → Server-Schritte macht der User.

### Internationalisierung (EN) — Detail: [docs/I18N.md](docs/I18N.md)

- **EN-Pages statisch vorgerendert** (`landing/build_en.py` → `landing/en/<slug>.html`), NICHT mehr Laufzeit-DOM-Swap. SEO-Head (canonical=/en/, reziprokes hreflang, og:locale, JSON-LD) **gebacken** → korrekt für Crawler OHNE JS. Deploy baut sie auf dem Host; `landing/en/` gitignored.
- **⚠️ ANTI-PATTERN: `data-i18n` (Text) auf Element MIT Inline-Kind (`<b>`/`<a>`/`<br>`) → nur letzter Textknoten übersetzt = halb deutsch** (auch live, unbemerkt). Fix: `data-i18n-html` + EN-Wert als VOLLES HTML. `scripts/fix_i18n_html_markup.py` flippt automatisch.
- **Verifizieren: `py landing/verify_en.py` (Ziel FAIL 0).** Dynamische JS-Strings via `SA.i18n.t('key','dt-Fallback')` (Script-Inhalt ist nicht backbar).
- **Neuer statischer DE-Text auf einer Tool-Seite OHNE `data-i18n`-Keys bricht den EN-Build** (`verify_en` FAIL: Deutsch auf `/en/`). Also IMMER `data-i18n(-html)` + EN-Wert in `en.json` (flach: `"prefix.key"`). `build_en.py` rendert EN nur für Seiten mit `_EN_PAGE_META`-Eintrag (manche Tool-Seiten sind DE-only, z.B. crash-fruehwarnung — dort EN-Keys harmlos ungenutzt). SEO-Hintergrund: Tool-Wert steckt im JS-Chart → für Crawler unsichtbar → „gecrawlt, nicht indexiert"; Gegenmittel = statischer Unique-Text + FAQPage-Schema (Muster: `landing/pages/*.html` `<details open>` mit `<prefix>.seo_*`, siehe `docs/SEO_TODO.md`).
- **`fetch('/data/...')` aus JS VERBOTEN** — nginx kennt keinen `/data/`-Root. Statische JSON/ICS-Dateien aus `landing/data/` immer über `/landing/data/<datei>` fetchen. Incident: `kalender-compute.js` fetche `/data/market_calendar.json` → 404 → leerer Kalender (2026-07-03).
- **`SA.auth.login(redirectPath?)` mit Zielpfad aufrufen** wenn der User nach OAuth zurück auf eine bestimmte Page soll (z.B. `/kalender`). Default-Redirect ist `/dashboard`. Ohne expliziten Pfad landet der User nach Login auf `/dashboard` und denkt, Login sei fehlgeschlagen.
- **Auth-gated/persönliche Pages ohne EN-Äquivalent MÜSSEN in `_skipPrefixes` eingetragen werden** — sowohl in `landing/js/i18n.js` als auch in `landing/build_en.py`. Andernfalls schreibt `_applyNavLinks()` im EN-Modus `/kalender` → `/en/kalender` und liefert 404, da keine EN-Version existiert. Betrifft: `/kalender`, `/profile`, `/watchlist`, `/pricing`, `/unsubscribe`. Zusätzlich: nginx `location = /en/<slug> { return 301 /<slug>; }` als Fallback. Incident: 2026-07-03 — Kalender-Link auf EN-Seiten lieferte 404.
- **Live `robots.txt`/`sitemap.xml` kommen aus `seo/output/`** (docker-compose-Mount nach `/app/static/`, Builder regeneriert bei jedem Deploy) — `static/robots.txt`/`static/sitemap.xml` im Repo sind ungenutzte Leichen. Bei robots/sitemap-Fragen die Live-Version prüfen.

### Blog / Bilingualisierung — Detail: [docs/BLOG_WORKFLOW.md](docs/BLOG_WORKFLOW.md)

- Sprachlogik komplett im Python-Builder (Template-Vars), kein `{% if is_en %}` im Template. EN-Posts in `blog/posts/en/` mit `de_slug:`-Feld (hreflang).
- nginx `location ^~ /en/blog/` MUSS VOR `^~ /en/` (längster Prefix, sonst 404). Bei EN nicht vergessen: `disclaimer_blog_en.md` + Chart-Labels via `lang="en"`.
- Nach Blog-Code-Änderung neu bauen: `docker exec seasonalpha-app python3 blog/blog_builder.py --build` + `docker compose restart nginx`.

### Sprache

- **Immer echte Umlaute** (ä ö ü), nicht ae/oe/ue. Gilt für UI, Tour, Blog, Commit-Messages, Kommentare. HTML-Entities OK. Dateinamen bleiben ASCII

## Architektur-Prinzipien

- Berechnungen → `shared/`, UI → `landing/pages/` (statisches HTML). Kein Copy-Paste zwischen Pages
- Chart-Styling nur via `apply_se_theme()` / `apply_se_heatmap_theme()`
- Alle Sektionen in Expander (Default ON/OFF je nach Relevanz)
- `info_badge` deprecated → Erklärungen auf `pages/10_Methodik.py` (Quelle: `info_texts.yaml`)
- Frontend-Charts: ApexCharts (120KB CDN) statt Plotly.js (3MB)
- Math vs Rendering trennen: `compute*()` returnt pures Objekt, `renderXxx` nur Darstellung
- Performance-Patterns: Staged Initial-Render (phasen via `setTimeout`), In-Memory Ticker-Cache, Default nur aktuelle Kohorte aktiv

## Design-Regeln

- Skills nutzen: `frontend-design`, `ui-ux-pro-max`, `21dev` (Component Inspiration)
- Keine generische AI-Ästhetik (kein Inter/Arial, kein Purple-on-White)
- Bold, distinctive Design Choices. Dark Mode First (V3 Ultra Palette)
- SVG Icons (Lucide) inline — keine Emojis/Icon-Fonts
- Accessibility: Kontrast 4.5:1, focus-visible, aria-labels, `prefers-reduced-motion`
- Touch-Targets ≥44px. Animation 150-300ms, transform/opacity only

## Tägliche Prüfungen (Session-Start)

| Was | Query / URL | Erwartung |
|-----|-------------|-----------|
| Nightly Refresh | `SELECT run_date, duration_seconds, errors FROM refresh_log ORDER BY run_date DESC LIMIT 3;` | gestern/heute, errors=`[]` |
| Regime-Scores | `SELECT date, risk_score, traffic_light FROM regime_scores WHERE ticker='SPY' ORDER BY date DESC LIMIT 3;` | letzter HT, 0–100 |
| Preise | `SELECT ticker, max(date) FROM prices WHERE ticker IN ('SPY','^DJI','AAPL') GROUP BY ticker;` | alle = gestern/heute |
| Crash-Frühwarnung | https://seasonalpha.ai/crash-fruehwarnung | Ampel + Chart konsistent |

Bei Fehlern: `docker logs seasonalpha-app --tail 50` · `docker exec -it seasonalpha-app python3 scripts/nightly_refresh.py` · Regime: `... scripts/compute_regime_scores.py --full`

## Arbeitsprotokoll

| Regel | Wann |
|-------|------|
| Auto Memory aktualisieren | Nach größeren Änderungen |
| CLAUDE.md TODOs pflegen | Erledigt `[x]` + Datum, Neues ergänzen |
| Commit-Messages aussagekräftig | WAS + WARUM |
| Vor Deploy: Syntax-Check | `py -c "import ast; ast.parse(open(f).read())"` |
| Vor Deploy: Funktionstest | Mind. 1 Import + 1 Daten-Test |

## Docs

- `ARCHITECTURE.md`, `CHARTS.md`, `UI_PATTERNS.md` (Frontend/UI/Statistik-Gotchas), `TRADING_CALENDAR_RULES.md` (Kalender/TDOM/TDOY/OPEX/VIX — Prüf-Spec), `I18N.md` (EN-Lokalisierung operativ; `I18N_ANALYSIS.md` = Planung 04-2026), `SEO_ENGINE.md`, `SEO_MARKETING.md` (Living Doc), `BLOG_WORKFLOW.md`, `REFRESH_MONITORING.md`, `MIGRATION.md`, `POLYMARKET.md`, `OPTIONS.md` (Dealer-Positioning: GEX/Vanna/Charm/Skew/Walls — Formeln + Konventionen + Datenquellen), `EMAIL_TESTING.md`, `YOUTUBE_STRATEGY.md` (faceless Social-Video-Kanal, Living Doc) + `YOUTUBE_DISCLAIMER.md` (YMYL-Rechtstexte, **kanonisch** — Disclaimer in Video/Caption/SEO-Hinweise einbauen!) + `SOCIAL_API_SETUP.md` (Meta IG/FB Auto-Posting-Setup); Pipeline in `scripts/video/` (`PLAN.md`/`README.md`), `CHANGELOG.md` (History/Meilensteine)
- `.claude/blog-tutorial.md` — Skill: SEO-Blog-Artikel (DE)

## TODO

### History → [docs/CHANGELOG.md](docs/CHANGELOG.md)

Meilensteine (KW15-KW24), abgeschlossene Aufgaben & Lessons Learned stehen im Changelog. (ML-Stilllegung vollständig abgeschlossen — `DROP TABLE ml_forecasts` erledigt 2026-06-16.)

### 🔴 SOFORT — Security (User-Action erforderlich)
- [ ] **OAuth Client-Secret rotieren** — in Session 2026-04-18 geleakt. Google Cloud Console → OAuth Clients → Secret neu generieren → in Supabase Auth Settings updaten
- [x] **Brevo-API-Key rotieren** — erledigt 2026-08-06: neuer Key aktiv in lokaler **und** Server-`.env` (`/opt/seasonaledge/.env`), App-Container neu gestartet, **Test-Mail kam an** (Endung neu `…WbWkUe`, alt `…lylWgh`). ⚠️ **NOCH offen (User-Dashboard-Aktion):** alten Key (`…lylWgh`) im Brevo-Dashboard **löschen** — er ist geleakt. **Lesson:** alter+neuer Brevo-Key teilen den Account-Präfix `xkeysib-5440ec2afed4…` → Keys NUR an der **Endung** unterscheiden, nie am Präfix. Brevo hat *Authorised-IPs* an → API-Test von nicht-freigegebener IP gibt 401 „unrecognised IP" (kein Key-Fehler); echter Test nur von Server-IP.
- [x] **Finnhub-API-Key revoken** — erledigt 2026-06-13 (war in Session 2026-04-30 geleakt; nicht mehr genutzt)

### 🔴 SOFORT — Funktional (User-Action erforderlich)
- [x] **Daily-Newsletter DB-Migration** — erledigt (`daily_subscribers` existiert + befüllt; bestätigt durch produktiven Briefing-Lauf 2026-06-16)
- [x] **Daily-Newsletter Smoke-Test** — erledigt: Daily Morning Briefing läuft produktiv (Lauf 2026-06-16 erfolgreich)
- [x] **4. TDOM-Strategy befüllt** — alle 4 Strategien mit je 6210 Rows ✓

### Marketing (manuell)
- [ ] LinkedIn + X Posts: Blog #22-24 (Polymarket, Sell in May, DAX vs S&P) + Blog EN-Launch ankündigen
- [ ] Lead-Magnet PDF "Saisonalitäts-Report 2026"
- [ ] Google Rich Results Test für die 3 Polymarket-Blog-Posts

### Technische Roadmap (längerfristig)
- [ ] **`build_calendar_data.py` via `docker exec` in `inject_credentials.sh`** statt system python3 → pandas verfügbar → JSON+ICS bei jedem Deploy automatisch aktuell (aktuell: committed-Stand, pandas fehlt in system python3)
- [ ] **Kalender: Dividenden + Earnings aus DB** — `dividend_events` + `earnings_events` Tabellen befüllen; kalender-compute.js `_loadPersonalized()` ist bereits vorbereitet
- [ ] **GSC /en/ Property einrichten** + Coverage nach 2 Wochen prüfen (erste EN-Indexierung erwartet)
- [ ] **Pretty EN slugs** (`/en/decade-cycle` statt `/en/dekadenzyklus`) — nginx rewrite map
- [ ] **EN Blog nach Deploy prüfen** — `/en/blog/` und Category-Filter korrekt? nginx-Location-Reihenfolge beachten
- [x] Stripe Checkout + Webhook anbinden — 3 Edge Functions fertig (2026-07-15); Aktivierung: docs/STRIPE_SETUP.md
- [ ] Premium-Features gated hinter Login (`[data-premium]`-Attribute auf Elemente, premium.js gated automatisch)
- [ ] Nav/Footer: Pricing-Link ergänzen
- [ ] Ticker-Vergleich im Dashboard (2 Ticker nebeneinander)
- [ ] Alerts (Push bei KI-Score/Crash-Ampel/Strategie-Schwellen)

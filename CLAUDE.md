# CLAUDE.md — SeasonAlpha

> Version 33.0 | 2026-04-15 | Gekürzt: Detail-Patterns aus Code ableitbar, nur noch nicht-offensichtliche Regeln + Architektur

## Projekt

**SeasonAlpha** — Web-Plattform für saisonale Finanzmarkt-Analyse (ETFs, Aktien, Futures, Crypto).
Freemium + Premium. Phase 1: Streamlit + Supabase + Stripe. Domain: `seasonalpha.ai`.

## Entwicklung

```
Pfad:   C:\Dev\Seasonaledge\
Start:  py -m streamlit run seasonal_app.py
Python: PowerShell → immer `py -m` (nicht `python`)
Server: ssh root@178.104.75.46  (Docker: seasonalpha-app / seasonalpha-nginx / seasonalpha-certbot)
Host-Pfad: /opt/seasonaledge
```

## Projektstruktur (High-Level)

```
seasonal_app.py          ← Streamlit-Startseite (Legacy, unter /app/)
shared/                  ← Berechnungs-/Daten-/UI-Module (siehe Module-Liste unten)
scripts/                 ← Batch-Jobs (Nightly, Intraday, Newsletter, Regime, ML)
pages/                   ← Streamlit Pages (Light Live + _disabled/ + Premium)
landing/                 ← Statische HTML-App (Haupt-Frontend)
  pages/                 ← 20 HTML-Pages (siehe HTML-Pages unten)
  js/                    ← 10 JS-Module (shared compute + charts)
  css/app.css            ← V3 Ultra Design System
  components/            ← nav.html, footer.html (JS-Include)
  data/                  ← Pre-computed JSON
blog/                    ← Markdown-Blog-Engine
seo/                     ← Programmatic SEO + statische Tool-Pages
docs/                    ← Ausgelagerte Dokumentation (ARCHITECTURE, CHARTS, AI_MODELS, …)
```

### Shared-Module Kurzübersicht

`yahoo_downloader` (Stooq-Fallback + OHLC adj_factor, einziger Cache), `data` (Supabase-First), `calculations`, `charts` (`apply_se_theme`), `ki_score` (4 Sub-Scores→0-10), `tdom_analysis`, `tdoy_analysis`, `ai_models`, `anomaly_engine`, `mstl_decomposition`, `chronos_forecast`, `neural_prophet_forecast`, `spot_vol_beta`, `outlier_manager`, `market_calendar`, `cache_manager`, `supabase_client`, `logger`, `cpi_data`, `shock_analysis`, `sector_rotation`, `significance_gauge` (key_prefix!), `percentile_bar`, `streak_analysis`, `footer`, `i18n`, `ticker_autocomplete`, `indicators`, `indicator_filter_ui`, `trading_day_header`, `drawdown_analysis`, `weekly_report`, `unsubscribe_token`, `strategies/plain_vanilla` (24), `strategies/kaeppel`.

### Frontend JS-Module (landing/js/)

`app.js` (Ticker-Input, REST, Trading-Day-Header, `makeSortable` Auto-Init, Sidebar-Toggle, Component-Loader), `charts.js` (ApexCharts-Theme + Helpers), `holidays.js` (NYSE/XETRA/LSE, Gauss-Ostern), `seasonal-compute.js`, `decade-compute.js` (+ Shared Anomalie-Radar via `renderAnomalyInto()`), `strategy-compute.js` (22 Strategien), `streak-analysis.js`, `significance.js`, `indicators.js`, `outlier.js`, `tour.js` + `tour-config.js` (23 Steps/11 Pages), `dash-compute.js`, `watchlist.js`, `auth.js` (Supabase Auth, Google OAuth), `fomc-dates.js`.

### HTML-Pages (landing/pages/)

Dashboard, Dekadenzyklus, Jahreszyklus, Monatszyklus, Wochentage, Monatswechsel, Mondphasen, Kriegszeiten, Crash-Frühwarnung, Plain-Vanilla, Trifecta, Intermarket-Shocks, Sektor-Rotation, Overnight, Zentralbanken, Feiertage, TDOM-Analyse, Spot-Vol-Beta, OPEX, KI-Saisonalität, Backtest-Engine, Unsubscribe.

## Kern-Methodik: NORMALISIERTE RENDITEN

Prozentuale Renditen normiert auf 100 — NICHT absolute Preisänderungen. Jedes Jahr startet bei 100, tägliche Returns kumulieren darauf. **Niemals** TradingView-Methode (`close - close[lookback]`).

## Import-Header (PFLICHT in jeder Streamlit-Page)

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
- API-Keys via `os.environ[...]` + Streamlit Secrets (in `.gitignore`), `logs/` niemals in Git
- Stooq: Session-Cookie erforderlich (`session.get("https://stooq.com/")` vor CSV)
- OHLC Cross-Day VERBOTEN: `Open[t]/Close[t-1]` mischt adj_factors → Dividend-Bias. Overnight/Intraday per Residual: `overnight = total - intraday`
- Nightly Refresh: nur letzte 5 Tage. Historische Daten bleiben unverändert
- `log_return`-Spalte in Supabase wird von `preprocess()` genutzt wenn vorhanden
- Zeitstempel UTC: `datetime.now(timezone.utc)` nutzen (nicht `datetime.utcnow()`, deprecated ab 3.12)

### Handelstage & Börsen-Awareness

- Immer Trading Days zählen, nie Kalendertage
- TDOM/TDOY sind **börsenspezifisch**: `render_trading_day_header(df, ticker=ticker)` — IMMER ticker übergeben
- Holiday-Kalender aus `shared/symbols.py::get_exchange_for_holidays(ticker)` → NYSE/XETRA/LSE/EURONEXT/TSE
- `is_trading_day(today, exchange)` — NICHT `weekday < 5`
- Frontend: `SA.holidays.detect(ticker)` + `SA.holidays.isTradingDay(date)`, Gauss-Ostern via `SA.holidays.goodFriday(year)`
- TDOM im Frontend: IMMER aus Holiday-Kalender berechnen, NICHT aus letztem DB-Row ableiten (DB kann vor Intraday-Refresh veraltet sein)
- CRYPTO: `is_trading_day()` immer True (24/7). FOREX: Mo-Fr ohne Feiertage (Karfreitag offen)
- OPEX = Kalender-3.Freitag, bei NYSE-Feiertag auf vorherigen HT vorverlegt. Triple Witching = Mar/Jun/Sep/Dez
- VIXpiration = OPEX-Freitag − 30 Kalendertage (= Mi). Ist Basis-Fr ODER Settlement-Mi Feiertag → −1 HT
- `toISOString()` NIE für lokale Datumsvergleiche (MESZ→UTC verschiebt auf Vortag) — nutze `localDateStr`

### Charts & UI

- Streamlit: Charts via `apply_se_theme()`, Heatmaps via `apply_se_heatmap_theme()` (+ `tickformat=None` auf Kategorie-Achsen). Inline `update_layout` VERBOTEN
- Plotly: `title=dict(text=..., font=dict(...))` statt `titlefont`. `add_shape`+`add_annotation` statt `add_vline` (crasht mit Strings)
- Heatmap Jahreslabels `f" {y} "` padden (erzwingt Kategorie), `text`+`texttemplate` statt Annotations
- `st.metric` vermeiden → HTML-Flex-Karten (10px Label, 14px Wert)
- `significance_gauge` bei Mehrfach-Aufruf: `key_prefix`
- `percentile_bar` unter Hauptcharts
- `ticker_select()` statt direkte Selects (global persistiert)
- Frontend: ApexCharts (kein Plotly.js). Für Multi-Serie-Charts **plain arrays mit null**, NICHT `{x,y}`-Objekte (bricht ApexCharts v4). Kein Mix `line`+`area`
- ApexCharts v4 Multi-Axis: `seriesName`-Array unzuverlässig → separate Chart-Instanzen mit `chart.group:'xxx'` synchronisieren
- Mixed Bar+Line Per-Wert-Coloring: `plotOptions.bar.colors.ranges:[{from:-Inf,to:-0.0001,color:RED},{from:0,to:Inf,color:GREEN}]`
- Info-Badge + Hover-Tooltip: pure CSS via `.info-badge:hover ~ .info-tooltip`. Parent MUSS `position:relative`, KEIN `overflow:hidden`. Gradient-`::before` mit `border-radius:inherit`
- KPI-Standard: globale Klasse `.kpi`/`.kpi-label`/`.kpi-value` (+ `green`/`red`/`gold`) aus `landing/css/app.css`. Keine lokalen `.kpi-card`-Definitionen
- Dashboard-Cards V3 Ultra: `background:var(--card)` (#0a0a0e), `border:1px solid var(--border)`, `padding:1rem`. KEIN `linear-gradient(135deg,#0f1923,#131d2a)`
- Farbschema V3 Ultra: Pure Black + Signal Gold (#e8a820) + Neon Red/Green. Dark Mode First
- Heatmap (Monatszyklus): `apply_se_theme` + `dtick=1` (nicht `apply_se_heatmap_theme` + `type="category"`)
- Drawdown-Heatmap: `SE_DRAWDOWN_COLORSCALE` (Rot-Gradient, zmin=worst, zmax=0, NICHT symmetrisch)
- Last-solid-Tag-Filter: `detectAnomalyEnd` + `computeDayCounts` — gelbe "wenige Daten"-Linie am Jahresrand
- Sortierbare Tabellen: Auto via `SA.makeSortable` + MutationObserver. Opt-out: `<table data-no-sort="1">`
- Footer: 5 Expander (Impressum, Datenschutz, Legal Notice EN, Financial Disclaimer, Risk) via `shared/footer.py`

### Statistik / Math

- Quantile NIE via Floor-Indexing. Lineare Interpolation wie numpy: `pos=q*(n-1); lo=floor(pos); hi=ceil(pos); return vals[lo]+(pos-lo)*(vals[hi]-vals[lo])`
- Perzentil-Bänder Stable-Range-Trim: max-Sample-pro-Tag bestimmen, Rand abschneiden bis Sample ≥90% des Max — verhindert Spikes durch Sample-Set-Wechsel
- Rolling Vola: ALLE Jahre konkatenieren → 1 Rolling-Std → wieder pro `(year, doy)` einsortieren. Sonst Warmup-NaN am Jahresanfang
- `Math.min.apply(null, arr)` ist NaN-unsafe → manuelle Loop
- TDOM-Statistiken mit n<10: ⚠ + 40% Opacity. MIN_N nur bei UNTERSCHIEDLICHEN n pro Punkt — bei Aggregat-Bars (Woche/Monat) hat jeder Balken gleiche n → immer rot/grün nach Vorzeichen, n im Tooltip
- Stats null vs constant-fill: `avg/std/Detrend` nutzen full_365 direkt (constant-fill). `Perzentil/Drawdown/Heatmap` müssen `if (d >= yo.last_actual_day) continue` filtern
- Heatmap `last_actual_day`-Filter NUR für CURRENT YEAR (sonst markiert Dezember fälschlich unvollständig wenn 31.12. Wochenende)
- Backtest-Filter look-ahead-bias-frei: `filterMask[entryIdx-1]`, NICHT `entryIdx`
- Plain Vanilla offene Trades: Mark-to-Market mit `trade.open=true` → aus Stats/Equity/Significance filtern, in Tabelle zeigen
- Dynamische Y-Achse: explizite yMin/yMax aus Daten + `forceNiceScale:true` (ApexCharts auto-scale kann zu groß ausschlagen)

### KI / Anomalie / Patterns

- Anomalie-Radar misst NUR 10 Tage (nicht YTD/Drawdown/Gesamt). Shared-Renderer `SA.decadeCompute.renderAnomalyInto(containerId, rows, ticker)` — einmal bauen, 4× nutzen
- KI Composite 4 Sub-Scores à 0-2.5 → 0-10. Bullish ≥6.5, Bearish ≤3.5. Client-side, vanilla JS
- Musterpfad: `findMatchingYears` (Pearson/Euklid) + `computeTruePath` (gewichteter Ø + Glättung) + `computeProjection` (± σ-Cone)
- Präsidentenzyklus: 1=Wahl, 2=Nach, 3=Zwischen (NICHT "Mitte"!), 4=Vor. Formel `((year-2020)%4+4)%4+1`

### Deployment / Mobile

- Landing Page statisches HTML (nginx direkt). Streamlit unter `/app/`
- Neue Pages: `loadComponent('nav-container', ...)` für Nav — NICHT manueller fetch (umgeht `initNav()` → Burger tot auf Mobile)
- Supabase-Credentials Inline-Script MUSS VOR `app.js` in jeder Page: `<script>window.__SA_SB_URL='%%SUPABASE_URL%%';window.__SA_SB_KEY='%%SUPABASE_ANON_KEY%%';</script>`
- Cache-Strategie: Nginx `/landing/*.{css,js}` → `max-age=0, must-revalidate` + ETag. `deploy/inject_credentials.sh` hängt `?v=<git-short-sha>` an alle CSS/JS-Refs
- `body.sa-sidebar-collapsed` Regeln in `@media (min-width: 1280px)` kapseln (sonst Override auf Mobile durch Spezifität)
- `.nav__links` Mobile: `height: calc(100dvh - var(--nav-h))` + `overflow-y:auto` (nicht vh, iOS-Bug)
- iOS 16px Input-Fix: Sidebar-Inputs auf Mobile explizit `font-size:16px` (sonst Auto-Zoom)
- Docker JSON-Transfer: im Container generieren, `docker cp` auf Host
- Git-Pull + Nginx-Reload für statische Änderungen: `cd /opt/seasonaledge && git pull && docker exec seasonalpha-nginx nginx -s reload`

### Email / Brevo

- Brevo 201 = angenommen, NICHT zugestellt — Status im Dashboard unter "Statistics → Email Activity" checken
- Sender-Domain MUSS Domain-Auth haben (SPF+DKIM+DMARC). Single-Sender reicht für Newsletter nicht — Gmail/Outlook blocken
- Secrets ohne Streamlit-Runtime: TOML-Fallback via `tomllib`, sucht in `<project>/.streamlit/secrets.toml` und `~/.streamlit/secrets.toml`, beide Key-Cases
- `messageId` aus Brevo-Response loggen für Debug
- `pgcrypto` in Supabase im `extensions`-Schema, nicht `public` → `SET search_path=public,extensions,pg_temp` + expliziter `extensions.digest()`-Call

### Sprache

- **Immer echte Umlaute** (ä ö ü), nicht ae/oe/ue. Gilt für UI, Tour, Blog, Commit-Messages, Kommentare. HTML-Entities OK. Dateinamen bleiben ASCII

## Architektur-Prinzipien

- Berechnungen → `shared/`, UI → `pages/` oder `landing/pages/`. Kein Copy-Paste zwischen Pages
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

- `ARCHITECTURE.md`, `CHARTS.md`, `AI_MODELS.md`, `KI_FEATURES.md`, `SEO_ENGINE.md`, `SEO_MARKETING.md` (Living Doc), `BLOG_WORKFLOW.md`, `REFRESH_MONITORING.md`, `MIGRATION.md`, `POLYMARKET.md`
- `.claude/blog-tutorial.md` — Skill: SEO-Blog-Artikel (DE)

## TODO

### Erledigt (KW 15, 07.–15.04.2026)
- [x] Dashboard Bento-Grid (11 Cards) + Risiko-Card 2. Zeile + Streak-Kacheln + WE/Feiertag-Fallback
- [x] Guided Tour (23 Steps/11 Pages, Driver.js v1.3.1)
- [x] Weekly Newsletter Pipeline (Brevo + HMAC-Unsubscribe + Phase F Cron)
- [x] SEO-Foundation (OG, Sitemap, IndexNow, Breadcrumbs, www→non-www 301)
- [x] Saisonal-Scanner MVP (269 Ticker, Weekly Cron)
- [x] Watchlist Phase 1 (localStorage + Compact-Cards V2)
- [x] Mobile Responsiveness (Sidebar-Collapse, Burger, iOS-Zoom)
- [x] TDOM-Fix Kalender-basiert, Timezone-Bugs, DD-Perzentil DOY-basiert
- [x] **2026-04-15** `refresh_log` RLS + Policies (Supabase Security Warning gefixt)

### Erledigt (KW 16, 2026-04-18 — Marathon-Session)
- [x] **Polymarket Phase 1-3 live** — 26 Markets, 4.100 Historie-Punkte, Cron Phase G, neue Page `/polymarket`, Divergenz-Score für BTC/ETH, Teaser in Zentralbanken + Crash-Frühwarnung (siehe `docs/POLYMARKET.md`)
- [x] **3 Polymarket-Blog-Posts** mit FAQPage-Schema (Fed-Cuts, BTC $150k, ETH vs BTC)
- [x] **SEO-Cleanup** — `/analyse/*` Thin-Content-Pages endgültig weg (410 Gone + Builder-Cleanup)
- [x] **.env-Refactor** — weg von `.streamlit/secrets.toml`, neuer `shared/env_loader.py`
- [x] **Google OAuth Phase 2** — OAuth-Client + Supabase Provider + URL Config (Consent noch in "Testing"-Mode)
- [x] **Cloud-Watchlist** — `user_watchlists`-Tabelle, Optimistic Sync, API-kompatibel zu bestehendem `SA.watchlist`
- [x] **Profile-Seite `/profile`** — responsive (3 Breakpoints 1024/768/480)
- [x] **Dashboard Info-Badges** — 13 Kacheln mit Hover-Tooltips (5 statische Cards + 8 Risk-KPIs)
- [x] **Tour erweitert** — 23→26 Steps (Login→Scanner→Watchliste vor Dashboard)
- [x] **Performance-Cache** — `SA.cache` (15min TTL) in app.js, `SA.TOUR_MODE` deaktiviert Chart-Animationen im Tour-Flow
- [x] **Chronos-Card** aus Dashboard entfernt (Relikt der alten ML-Pipeline)
- [x] **Info-Badge-Security-Fix** — `inject_credentials.sh` prüft per JWT-Role dass kein service-role-Key ins Frontend-HTML leakt
- [x] **nginx-Cache-Fix** — `/landing/components/*.html` nicht mehr 24h gecached (Nav-Änderungen wirken sofort)

### ✅ ML-Pipeline stillgelegt (2026-04-18)
Gecancelter Scope: Chronos-Forecast, NeuralProphet, MSTL-Monats-Heatmap.
Entfernt: `shared/mstl_decomposition.py`, `scripts/compute_ml_forecasts.py`,
`scripts/create_ml_forecasts.sql`, `.github/workflows/ml_forecasts.yml`,
`pages/_disabled/80_Erweiterte_Analyse.py` + `87_KI_Score.py`,
`docs/AI_MODELS.md`, `docs/KI_FEATURES.md`.
KI-Score wieder 4 Sub-Scores (à 2.5), Scanner ohne Forecast/Sais.Stärke-Spalte.
User-Action offen: `DROP TABLE ml_forecasts` in Supabase.

### Erledigt (KW 17, 2026-04-21 — GRANT-Incident + Monitoring-Mails)
- [x] **Supabase GRANT-Loss-Fix** — service_role hatte DML auf 15+ Alt-Tabellen verloren, anon hatte ungewollte Write-Rechte. SQL-Block mit `GRANT ALL ... TO service_role` + `REVOKE ... FROM anon` + `ALTER DEFAULT PRIVILEGES`. Incident-Doku im Memory.
- [x] **docker-compose `env_file: .env`** — BREVO_API_KEY/ADMIN_EMAIL/SENDER_* waren nach `.env`-Refactor (04-18) nicht im Container; dadurch Weekly-Newsletter 3 Tage stumm. Fix: pauschal alle `.env`-Keys durchreichen, Migration der Brevo-Werte aus `.streamlit/secrets.toml` in `.env`.
- [x] **PR #27 — Daily Health Check** — `scripts/daily_health_check.py` + Jinja2-Template + GitHub-Action Cron 07:00 UTC + Weekly-Newsletter-Manual-Trigger (`.github/workflows/weekly_newsletter_manual.yml` mit test/dry-run/live-Dropdown). 7 Checks, Ampel-Mail an `ADMIN_EMAIL`.
- [x] **PR #28 — Health-Mail Standing-Text** — permanente "Selbst testen"-Sektion (GH-Actions-Links, SSH-Commands, Brevo-Statistics, Doku-Link). Bug-Fix: `scanner_results.scan_date` statt falschem `run_date`.
- [x] **PR #29 — Intraday-Run-Logging** — `intraday_refresh.py` schreibt nach jedem erfolgreichen Run einen `refresh_log`-Eintrag mit `run_type='intraday'`. Health-Check-Coverage-Counter (Wochentag green ≥10, Wochenende green ≥3).
- [x] **docs/EMAIL_TESTING.md** — Runbook für Mail-Versand-Tests, Troubleshooting (BREVO_API_KEY fehlt, Sender rejected, permission denied), Brevo-Key-Rotation, Daten-Freshness-Check.

### 🔴 SOFORT (User-Action, klein)
- [x] **2026-04-18 OAuth Consent Screen auf "Production" publishen** (Google Cloud Console) — Nicht-Tester können sich jetzt anmelden
- [ ] **OAuth Client-Secret rotieren** — das in Session 2026-04-18 im Chat geleakte Secret entwerten, neu generieren, in Supabase updaten
- [ ] **Brevo-API-Key rotieren** — in Session 2026-04-21 im Chat geleakt (`xkeysib-5440ec2afed4...`). Brevo Dashboard → Settings → SMTP & API → Keys → neuen erstellen, alten löschen, `.env` updaten, `docker compose up -d --force-recreate app`. Anleitung: [docs/EMAIL_TESTING.md](docs/EMAIL_TESTING.md#security-api-key-rotieren)
- [ ] GSC Coverage-Check nach 1-2 Wochen: 329 → < 30 (410-Gone-Cleanup der /analyse/*)
- [ ] Google Rich Results Test für die 3 Polymarket-Blog-Posts
- [ ] **nightly_refresh.py tickers_success-Metrik fixen** (optional) — zählt "heute" fälschlich als fehlend wenn manuell vor Börsenschluss gestartet; macht Mail-Anzeige präziser aber nicht dringend

### ⚠️ OFFEN — Polymarket Phase 3b (aus aktueller Arbeit)
- [x] **2026-04-18 Brier-Score-Pipeline** — separate Tabellen `polymarket_resolved_*`, Scraper für ~1500 resolved markets (6 Tags, 2024+), `shared/brier_score.py` mit Brier + Kalibrierungs-Kurve + Zeit-Buckets, Precompute als `brier_stats.json`, UI-Sektion auf `/polymarket`. Details in `docs/POLYMARKET.md#brier-score`.
- [x] **2026-04-18 Fed/Macro-Divergenz** — historische Basisraten (Cuts-Histogramm 2000-2024 aus `FED_RATE_CHANGES`, Hike-Rate, static NBER/BEA-Basisraten für Recession/GDP/Emergency-Cut, `shared/weekly_report.py::top_fed_macro_divergences`)
- [x] **2026-04-18 Newsletter-Sektion** mit Top-Divergenzen der Woche (Crypto BTC/ETH, `shared/weekly_report.py::top_polymarket_divergences`)
- [x] **2026-04-18 Intraday-Refresh-Tier** nahe FOMC (±2d Fenster, `polymarket_intraday.yml` + `--near-fomc-only` Flag)

### ⚠️ OFFEN — Auth-Features Follow-ups
- [x] **2026-04-18 Profile-Seite: Newsletter-Toggle** — `scripts/create_profile_newsletter_rpc.sql` liefert `get_my_newsletter_status()` + `toggle_my_newsletter(bool)` (SECURITY DEFINER, `auth.jwt() ->> 'email'`), UI in `/profile` mit Switch + Status-Text. **User-Action:** Migration in Supabase SQL-Editor ausführen.
- [ ] Profile-Seite: Konto-Löschung self-service (aktuell nur Placeholder → Email an info@)

### Marketing (manuell)
- [ ] LinkedIn + X Posts der 3 Polymarket-Blog-Posts staffeln (Templates im Anhang jedes Posts)
- [ ] Newsletter-Mail an Brevo-Liste
- [ ] Lead-Magnet PDF "Saisonalitäts-Report 2026"

### Technische Roadmap (längerfristig)
- [ ] Ticker-Vergleich im Dashboard (2 Ticker nebeneinander)
- [ ] Alerts (Push bei KI-Score/Crash-Ampel/Strategie-Schwellen)
- [ ] EN-Übersetzung der HTML-Pages
- [ ] Stripe Freemium/Abo (an Supabase-User anbinden)
- [ ] Premium-Features gated hinter Login (erweiterte Backtest-Zeiträume, mehr Markets im Scanner)

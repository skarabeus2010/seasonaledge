# CLAUDE.md — SeasonAlpha

> Version 38.0 | 2026-06-13 | EN Pre-Rendering (statisch `landing/en/`, deployed) + ~70 i18n-Mixed-Content-Defekte gefixt + verify_en.py + Deploy-Lessons

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
scripts/                 ← Batch-Jobs (Nightly, Intraday, Newsletter, Regime)
pages/                   ← Streamlit Pages (Light Live + _disabled/)
landing/                 ← Statische HTML-App (Haupt-Frontend)
  pages/                 ← 29 HTML-Feature-Pages
  js/                    ← JS-Module (shared compute + charts + i18n)
  i18n/                  ← de.json + en.json (1222 Keys, seit KW24)
  css/app.css            ← V3 Ultra Design System
  components/            ← nav.html, footer.html (JS-Include)
  data/                  ← Pre-computed JSON
blog/                    ← Markdown-Blog-Engine
  posts/                 ← 24 DE Markdown-Posts
  posts/en/              ← 24 EN Markdown-Posts (seit KW24)
  templates/             ← bilinguales blog_post.html + blog_index.html
  output/                ← Generiertes HTML (gitignored, wird serverseitig gebaut)
seo/                     ← Programmatic SEO + statische Tool-Pages
docs/                    ← Ausgelagerte Dokumentation
```

### Module / Pages — Detail-Listen in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

- **Shared (`shared/`)** — Kern: `yahoo_downloader` (Stooq-Fallback, einziger Cache), `data` (Supabase-First), `charts` (`apply_se_theme`), `ki_score`, `tdom_analysis`, `anomaly_engine`, `significance_gauge` (key_prefix!), `footer`, `i18n`. ⚠️ Gelöscht (ML-Pipeline KW16): `mstl_decomposition`, `chronos_forecast`, `neural_prophet_forecast`, `ai_models`.
- **Frontend JS (`landing/js/`)** — `app.js`, `charts.js` (ApexCharts), `holidays.js` (Gauss-Ostern), `*-compute.js`, `tour.js`, `auth.js`, **`i18n.js`** (SA.i18n IIFE).
- **HTML-Pages (`landing/pages/`)** — 30 Feature-Pages (Dashboard, Zyklen, Events, Strategien, KI, Backtest …).

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
- API-Keys via `os.environ[...]` + `.env` (in `.gitignore`), `logs/` niemals in Git
- Stooq: Session-Cookie erforderlich (`session.get("https://stooq.com/")` vor CSV)
- OHLC Cross-Day VERBOTEN: `Open[t]/Close[t-1]` mischt adj_factors → Dividend-Bias. Overnight/Intraday per Residual: `overnight = total - intraday`
- Nightly Refresh: letzte **7 Tage** Upsert-Fenster (seit Phase D KW20). Phase D prüft zusätzlich letzte 14 Tage auf NULL `log_return` und berechnet nach.
- `log_return`-Spalte in Supabase wird von `preprocess()` genutzt wenn vorhanden
- Zeitstempel UTC: `datetime.now(timezone.utc)` nutzen (nicht `datetime.utcnow()`, deprecated ab 3.12)
- **Neuen Ticker aufnehmen: NUR via `py scripts/onboard_ticker.py <T>`** (nach Eintrag in `symbols.py`). Macht Yahoo-Validierung + Voll-Backfill + tickers.json-Regen + DB-Upsert in einem. NIEMALS nur Preise laden ohne `symbols.py`-Eintrag → sonst „Orphan" (wird weder auditiert noch refreshed, veraltet still). `symbols.py`/`get_all_tickers()` = einzige Quelle der Wahrheit; Backfill-Skripte ihre Ticker-Liste IMMER daraus speisen, nie aus DB-Tabellen (prices-Full-Scan timeoutet, `tickers`-Tabelle kann fehlen).
- **Lokal (Windows):** `py -3.14` nutzen (= Container-Version; Default-`py` ist 3.9 und scheitert an `X | None`-Syntax in shared-Modulen). Bei Skript-Läufen mit Datei-Umleitung `PYTHONUTF8=1` setzen (cp1252 crasht sonst an ✓/⚡-Prints).
- Vollständigkeit prüfen: `py scripts/check_db_completeness.py` (Freshness/Coverage/Gaps/Events + Orphan- & Stale-Tail-Erkennung; wöchentl. Cron `db_completeness.yml`). Orphan-Check braucht RPC `create_distinct_price_tickers_rpc.sql`.

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

- Landing Page statisches HTML (nginx direkt). Streamlit unter `/app/`
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

### Email / Brevo — Detail: [docs/EMAIL_TESTING.md](docs/EMAIL_TESTING.md)

- Brevo **201 = angenommen, NICHT zugestellt** — Status im Dashboard („Statistics → Email Activity") checken.
- Sender-Domain MUSS Domain-Auth haben (SPF+DKIM+DMARC); Single-Sender reicht für Newsletter nicht (Gmail/Outlook blocken).

### Internationalisierung (EN) — Detail: [docs/I18N.md](docs/I18N.md)

- **EN-Pages statisch vorgerendert** (`landing/build_en.py` → `landing/en/<slug>.html`), NICHT mehr Laufzeit-DOM-Swap. SEO-Head (canonical=/en/, reziprokes hreflang, og:locale, JSON-LD) **gebacken** → korrekt für Crawler OHNE JS. Deploy baut sie auf dem Host; `landing/en/` gitignored.
- **⚠️ ANTI-PATTERN: `data-i18n` (Text) auf Element MIT Inline-Kind (`<b>`/`<a>`/`<br>`) → nur letzter Textknoten übersetzt = halb deutsch** (auch live, unbemerkt). Fix: `data-i18n-html` + EN-Wert als VOLLES HTML. `scripts/fix_i18n_html_markup.py` flippt automatisch.
- **Verifizieren: `py landing/verify_en.py` (Ziel FAIL 0).** Dynamische JS-Strings via `SA.i18n.t('key','dt-Fallback')` (Script-Inhalt ist nicht backbar).

### Blog / Bilingualisierung — Detail: [docs/BLOG_WORKFLOW.md](docs/BLOG_WORKFLOW.md)

- Sprachlogik komplett im Python-Builder (Template-Vars), kein `{% if is_en %}` im Template. EN-Posts in `blog/posts/en/` mit `de_slug:`-Feld (hreflang).
- nginx `location ^~ /en/blog/` MUSS VOR `^~ /en/` (längster Prefix, sonst 404). Bei EN nicht vergessen: `disclaimer_blog_en.md` + Chart-Labels via `lang="en"`.
- Nach Blog-Code-Änderung neu bauen: `docker exec seasonalpha-app python3 blog/blog_builder.py --build` + `docker compose restart nginx`.

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

- `ARCHITECTURE.md`, `CHARTS.md`, `UI_PATTERNS.md` (Frontend/UI/Statistik-Gotchas), `I18N.md` (EN-Lokalisierung operativ; `I18N_ANALYSIS.md` = Planung 04-2026), `SEO_ENGINE.md`, `SEO_MARKETING.md` (Living Doc), `BLOG_WORKFLOW.md`, `REFRESH_MONITORING.md`, `MIGRATION.md`, `POLYMARKET.md`, `EMAIL_TESTING.md`, `CHANGELOG.md` (History/Meilensteine)
- `.claude/blog-tutorial.md` — Skill: SEO-Blog-Artikel (DE)

## TODO

### History → [docs/CHANGELOG.md](docs/CHANGELOG.md)

Meilensteine (KW15-KW24), abgeschlossene Aufgaben & Lessons Learned stehen im Changelog. **Offene User-Action aus ML-Stilllegung:** `DROP TABLE ml_forecasts` in Supabase.

### 🔴 SOFORT — Security (User-Action erforderlich)
- [ ] **OAuth Client-Secret rotieren** — in Session 2026-04-18 geleakt. Google Cloud Console → OAuth Clients → Secret neu generieren → in Supabase Auth Settings updaten
- [ ] **Brevo-API-Key rotieren** — in Session 2026-04-21 geleakt (`xkeysib-5440ec2afed4...`). Brevo Dashboard → SMTP & API → neuen Key erstellen, alten löschen, `.env` updaten, `docker compose up -d --force-recreate app`. Anleitung: [docs/EMAIL_TESTING.md](docs/EMAIL_TESTING.md#security-api-key-rotieren)
- [ ] **Finnhub-API-Key revoken** — in Session 2026-04-30 geleakt. Nicht mehr genutzt, trotzdem: Finnhub Dashboard → API Keys → löschen

### 🔴 SOFORT — Funktional (User-Action erforderlich)
- [ ] **Daily-Newsletter DB-Migration** — `scripts/create_daily_subscribers.sql` in Supabase SQL-Editor ausführen. Danach: `INSERT INTO daily_subscribers(email) VALUES ('heiko.seibel@gmail.com');`
- [ ] **Daily-Newsletter Smoke-Test** — GitHub Actions → "Daily Morning Briefing" → Run workflow → test_mode=true. Mail + alle Sektionen prüfen.
- [x] **4. TDOM-Strategy befüllt** — alle 4 Strategien mit je 6210 Rows ✓

### Marketing (manuell)
- [ ] LinkedIn + X Posts: Blog #22-24 (Polymarket, Sell in May, DAX vs S&P) + Blog EN-Launch ankündigen
- [ ] Lead-Magnet PDF "Saisonalitäts-Report 2026"
- [ ] Google Rich Results Test für die 3 Polymarket-Blog-Posts

### Technische Roadmap (längerfristig)
- [ ] **GSC /en/ Property einrichten** + Coverage nach 2 Wochen prüfen (erste EN-Indexierung erwartet)
- [ ] **Pretty EN slugs** (`/en/decade-cycle` statt `/en/dekadenzyklus`) — nginx rewrite map
- [ ] **EN Blog nach Deploy prüfen** — `/en/blog/` und Category-Filter korrekt? nginx-Location-Reihenfolge beachten
- [ ] Stripe Checkout + Webhook anbinden (Infrastruktur steht: DB + RPC + premium.js + Pricing-Page)
- [ ] Premium-Features gated hinter Login (`[data-premium]`-Attribute auf Elemente, premium.js gated automatisch)
- [ ] Nav/Footer: Pricing-Link ergänzen
- [ ] Ticker-Vergleich im Dashboard (2 Ticker nebeneinander)
- [ ] Alerts (Push bei KI-Score/Crash-Ampel/Strategie-Schwellen)

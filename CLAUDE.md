# CLAUDE.md — SeasonAlpha

> Version 37.0 | 2026-06-12 | Phase 7: Verifikations-Workflow, Blog-EN-Fix, TDOM-Fix, 1222 i18n-Keys

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

### Shared-Module Kurzübersicht

`yahoo_downloader` (Stooq-Fallback + OHLC adj_factor, einziger Cache), `data` (Supabase-First), `calculations`, `charts` (`apply_se_theme`), `ki_score` (4 Sub-Scores→0-10), `tdom_analysis`, `tdoy_analysis`, `anomaly_engine`, `spot_vol_beta`, `outlier_manager`, `market_calendar`, `cache_manager`, `supabase_client`, `logger`, `cpi_data`, `shock_analysis`, `sector_rotation`, `significance_gauge` (key_prefix!), `percentile_bar`, `streak_analysis`, `footer`, `i18n`, `ticker_autocomplete`, `indicators`, `indicator_filter_ui`, `trading_day_header`, `drawdown_analysis`, `weekly_report`, `daily_report`, `unsubscribe_token`, `strategies/plain_vanilla` (24), `strategies/kaeppel`.

> ⚠️ Gelöscht: `mstl_decomposition`, `chronos_forecast`, `neural_prophet_forecast`, `ai_models` (ML-Pipeline stillgelegt KW16)

### Frontend JS-Module (landing/js/)

`app.js` (Ticker-Input, REST, Trading-Day-Header, `makeSortable` Auto-Init, Sidebar-Toggle, Component-Loader), `charts.js` (ApexCharts-Theme + Helpers), `holidays.js` (NYSE/XETRA/LSE, Gauss-Ostern), `seasonal-compute.js`, `decade-compute.js` (+ Shared Anomalie-Radar via `renderAnomalyInto()`), `strategy-compute.js` (22 Strategien), `streak-analysis.js`, `significance.js`, `indicators.js`, `outlier.js`, `tour.js` + `tour-config.js` (26 Steps/13 Pages, `SA.TOUR_STEPS_EN` für EN), `dash-compute.js`, `watchlist.js`, `auth.js` (Supabase Auth, Google OAuth), `fomc-dates.js`, **`i18n.js`** (SA.i18n IIFE, URL-Detect, JSON-Loader, _applyDOM, _applyNavLinks, switchTo).

### HTML-Pages (landing/pages/)

Dashboard, Dekadenzyklus, Jahreszyklus, Monatszyklus, Wochentage, Monatswechsel, Mondphasen, Kriegszeiten, Crash-Frühwarnung, Plain-Vanilla, Trifecta, Intermarket-Shocks, Sektor-Rotation, Overnight, Zentralbanken, Feiertage, TDOM-Analyse, Spot-Vol-Beta, OPEX, KI-Saisonalität, Backtest-Engine, Polymarket, Dividenden-Kalender, Earnings-Kalender, Risikozyklus, VIXpiration, Pricing, Profile, Unsubscribe.

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
- `blog/output/` ist gitignored — HTML wird serverseitig via `blog_builder.py --build` generiert (baut DE + EN)

### Email / Brevo

- Brevo 201 = angenommen, NICHT zugestellt — Status im Dashboard unter "Statistics → Email Activity" checken
- Sender-Domain MUSS Domain-Auth haben (SPF+DKIM+DMARC). Single-Sender reicht für Newsletter nicht — Gmail/Outlook blocken
- Secrets ohne Streamlit-Runtime: TOML-Fallback via `tomllib`, sucht in `<project>/.streamlit/secrets.toml` und `~/.streamlit/secrets.toml`, beide Key-Cases
- `messageId` aus Brevo-Response loggen für Debug
- `pgcrypto` in Supabase im `extensions`-Schema, nicht `public` → `SET search_path=public,extensions,pg_temp` + expliziter `extensions.digest()`-Call
- Newsletter-Subprocess: `capture_output=False` — sonst Output komplett unsichtbar in docker logs

### Internationalisierung (EN-Lokalisierung)

- `SA.i18n` IIFE in `landing/js/i18n.js` — `init()` in DOMContentLoaded, `switchTo(lang)` public
- Spracherkennung via URL: `/en/*` → EN, alles andere → DE. Kein JS-Cookie, kein localStorage
- `data-i18n="key"` auf Text-Elemente, `data-i18n-placeholder` für Input-Placeholders, `data-i18n-title` für title-Attr, `data-i18n-html` für innerHTML (Elemente mit `<b>`/`<a>` Tags)
- JSON-Cache in sessionStorage mit Versionskey (`_JSON_VER='v3'`) — verhindert Stale-Cache nach Key-Änderungen
- nginx `sub_filter` tauscht `og:locale` und `lang=de` → `lang=en` für `/en/*`-Responses
- i18n-JSON: nginx `location /landing/i18n/ { ... no-store }` — KEIN max-age (sonst 24h gecachte alte Keys)
- `_applyNavLinks()` rewritet alle `document.querySelectorAll('a[href]')` — NICHT nur nav/footer Container

### Blog / Bilingualisierung

- Blog-Templates bilingual via Template-Vars (`lang`, `og_locale`, `blog_base`, `post_url`, `str_min_read`, `str_cta_h3` etc.) — NICHT `{% if is_en %}...{% else %}...{% endif %}` überall im Template. Alle Sprachlogik im Python Builder.
- EN-Posts in `blog/posts/en/` führen `de_slug:` Feld für hreflang-Rücklink zum DE-Original
- Builder: `{**post, **_extra_vars_en(post), "related_posts": ..., ...}` als ctx mergen, dann `tpl.render(**ctx)` — nie `tpl.render(**post, **override_vars)` (wirft `TypeError: duplicate keyword argument` wenn Key in beiden Dicts)
- nginx: `location ^~ /en/blog/` MUSS VOR `location ^~ /en/` stehen — nginx nimmt längsten Prefix-Match; fehlt der explizite Block, landet `/en/blog/` im generischen `/en/`-Catch-all → 404
- Workflow-Agenten für Übersetzungen: **einen Agenten pro Datei** (nicht Batches). Große Posts füllen Kontext-Fenster, Batch-Agenten schreiben dann nur partiell oder brechen still ab.
- Windows cp1252 console: `blog_builder.py --build` kann bei Sonderzeichen (`−`, `–`) in Post-Titeln UnicodeEncodeError werfen. Betrifft nur `print()`-Ausgabe, NICHT die HTML-Erzeugung. Auf dem Linux-Server (UTF-8) kein Problem.
- **Blog-Disclaimer**: `disclaimer_blog.md` gilt nur für DE. `disclaimer_blog_en.md` für EN-Posts — `load_blog_disclaimer(lang='en')` in `build_en()` aufrufen. Sonst zeigen alle EN-Posts deutschen Rechtshinweis.
- **Blog-Chart-Labels**: `markdown_to_html()` und Chart-Builder akzeptieren `lang`-Parameter. `load_posts_en()` übergibt `lang="en"`. Sonst: deutsche Monatsnamen ("Mai"/"Okt"), deutsche Chart-Titel in EN-Posts.
- **Blog-Index page_title/page_description**: Müssen in `_extra_index_vars_en()` stehen — NICHT nur im Template-Default. Template-Defaults sind immer Deutsch.
- Nach Blog-Code-Änderungen auf Server neu bauen: `docker exec seasonalpha-app python3 blog/blog_builder.py --build` + `docker exec seasonalpha-nginx nginx -s reload`

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

- `ARCHITECTURE.md`, `CHARTS.md`, `SEO_ENGINE.md`, `SEO_MARKETING.md` (Living Doc), `BLOG_WORKFLOW.md`, `REFRESH_MONITORING.md`, `MIGRATION.md`, `POLYMARKET.md`, `EMAIL_TESTING.md`
- `.claude/blog-tutorial.md` — Skill: SEO-Blog-Artikel (DE)

## TODO

### Abgeschlossene Meilensteine (Kurzübersicht)

| KW | Datum | Inhalt |
|----|-------|--------|
| KW15 | Apr 2026 | Dashboard Bento-Grid, Guided Tour (26 Steps), Weekly Newsletter, SEO-Foundation, Scanner MVP, Watchlist Phase 1, Mobile Responsiveness, TDOM-Fix |
| KW16-17 | Apr 2026 | Polymarket Integration (3 Phasen, Brier-Pipeline), Auth+Cloud-Watchlist, Profile-Page, Health-Check-Mails, ML-Pipeline stillgelegt, Blog-Posts #1-21 |
| KW18 | Apr 2026 | Dividenden + Earnings Pages, Event-Crons, Yahoo Crumb-Auth, Health-Check-Integration |
| KW20 | Mai 2026 | Nightly Backfill Phase D, moddatetime-Trigger, Stripe-Infrastruktur, GSC-Bereinigung (383→32), Blog #22-24, Newsletter Phase F Fix |
| KW22 | Mai 2026 | Daily Morning Briefing (Multi-Window-TDOM-Score 0-4, top_daily_tips, Watchlist-Personalisierung, 10 Strategie-Signale, Status-Zeile) |
| KW24 | Jun 2026 | **EN Lokalisierung Phasen 1-7** komplett: SA.i18n, 1222 Keys, 30 Pages + Verifikation aller Expander/Methodologie, Tour EN, 24 Blog-Posts EN (EN Disclaimer+Charts), Sitemap 89→113 URLs, hreflang |

### ✅ ML-Pipeline stillgelegt (2026-04-18)
Entfernte Module/Scripts: `mstl_decomposition.py`, `chronos_forecast.py`, `neural_prophet_forecast.py`, `compute_ml_forecasts.py`, `create_ml_forecasts.sql`, `ml_forecasts.yml`.
KI-Score: 4 Sub-Scores (à 2.5, 0–10). **User-Action offen:** `DROP TABLE ml_forecasts` in Supabase.

### Erledigt (KW 24, 2026-06-12 — EN Phase 6+7)
- [x] **24 Blog-Posts EN übersetzt** — `blog/posts/en/` mit `de_slug:`-Feld für hreflang-Rücklinks
- [x] **`blog_builder.py` erweitert** — `build_en()`, `load_posts_en()`, `_extra_vars_en()`, `_build_blog_sitemap_en()`. `main()` ruft automatisch beide (`build_all()` + `build_en()`)
- [x] **Bilinguales Blog-Template** — alle Sprachstrings als Template-Variablen, kein `{% if is_en %}` im HTML
- [x] **nginx `/en/blog/`** — eigener `^~`-Location-Block vor dem `/en/`-Catch-all
- [x] **Sitemap 89→113 URLs** — 24 EN Blog-Posts + `/en/blog/` Index, alle mit hreflang
- [x] **Blog EN-Fix** — `disclaimer_blog_en.md`, EN Chart-Labels, page_title/page_description in EN Index
- [x] **Verifikations-Workflow** — 21 Pages: alle Expander/Methodologie-Texte mit data-i18n versehen, en.json 793→1222 Keys
- [x] **TDOM 4. Strategie** — `open_to_next_close` im Frontend + DB (6210 Rows je Strategie)

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

# SeasonAlpha — Feature-Roadmap

> Stand: 2026-04-10 (Vormittag) | Core-Analyse abgeschlossen (20/18 HTML-Pages). Nächste Phase: **Engagement, Retention, Onboarding + Growth-Features**. **Feature #1 (Guided Tour) live · Feature #2 (Weekly Newsletter) erster Live-Test erfolgreich zugestellt.**

## Kontext

SeasonAlpha ist auf HTML-Seite zu 20/18 Pages fertig (Dashboard, Backtest Engine, Jahreszyklus, Monatszyklus, Wochentage, Plain Vanilla, Trifecta, KI-Saisonalität, Overnight, TDoM, OPEX, Sektor-Rotation, ...). Die Core-Analyse ist abgeschlossen.

Jetzt verschiebt sich der Fokus:

- **Onboarding** — neue User landen auf einer sehr funktionsreichen Seite und wissen nicht wo anfangen → Guided Tour
- **Retention** — regelmäßige Rückbesuche via Email-Alerts / Weekly Report
- **Growth** — klassische Power-User Features: Scanner, Watchlists, Portfolio-Simulation
- **Personalisierung** — User-Accounts als Enabler für alle personalisierten Features

Die Exploration hat gezeigt, dass **vieles bereits zu 60–80 % vorhanden ist** im Backend (Brevo-Integration, Scanner-Nightly-Job, Strategy-Compute-Engine). Die meisten Features brauchen primär **Frontend-UI + Glue-Code**, nicht komplette Neuentwicklung. Ausnahme: Auth-System (20 %) und Guided Tour (0 %, grüne Wiese).

## 5 geplante Features

| # | Feature | Backend | Frontend | Aufwand | Status |
|---|---------|--------:|---------:|--------:|--------|
| 1 | **Guided Tour** | N/A | 100 % | **1 Tag** | ✅ **Live seit 2026-04-09** |
| 2 | **Email-Alerts / Weekly Report** | 100 % | 100 % | **1 Tag** | ✅ **Live-Test erfolgreich 2026-04-10** — Nginx-Reload + Phase-F-Aktivierung ausstehend |
| 3 | **Saisonal-Scanner** | ~60 % (`scanner_results` Tabelle + nightly_refresh) | 0 % | **4–5 Tage** | Nächstes Feature |
| 4 | **Auth + Custom Watchlists** | 20 % (Subscriber-Tabelle, kein User-System) | 0 % | **8–10 Tage** | Welle 2 |
| 5 | **Portfolio-Backtest Combo** | ~80 % (`strategy-compute.js`, 24 Strategien) | 0 % | **6–8 Tage** | Welle 3 |

## Entwicklungs-Wellen

### Welle 1 — Quick Wins (Woche 1–2)

1. **Guided Tour** — Hoher UX-Impact, niedriger Aufwand, keine Dependencies. ✅ **Live seit 2026-04-09** (1 Tag Implementierung inkl. Post-Launch-Fixes).
2. **Email-Alerts / Weekly Report** — ✅ **Live-Test erfolgreich am 2026-04-10.** Brevo Domain-Auth (SPF/DKIM/DMARC) für `seasonalpha.ai` komplett eingerichtet, erster Newsletter mit `noreply@seasonalpha.ai` zugestellt. Offen: Nginx-Reload auf Server + Phase F Aktivierung für nächsten Sonntag + Content-Iteration.

### Welle 2 — Core Features (Woche 3–4)

3. **Saisonal-Scanner** — Daten laufen nightly in `scanner_results`, es fehlt nur die Frontend-Page `/scanner` mit Filter-UI.
4. **Auth + Watchlists** — Längster Aufwand, aber Enabler für alle personalisierten Features (Alerts, Scanner-Save, Portfolio).

### Welle 3 — Polish (Woche 5–6)

5. **Portfolio-Backtest Combo** — Aufwendigstes Feature, aber hoher USP-Wert (Multi-Strategy-Allocation + Rebalancing).

## Kritische Dateien pro Feature

### Feature #2 — Weekly Newsletter ✅ LIVE-TEST ERFOLGREICH 2026-04-10

**Implementiert (Commits b343de9 → 14e4087 → e80c818):**
- `shared/weekly_report.py` — 4 Aggregations-Funktionen (`top_ki_scores`, `regime_status`, `upcoming_events`, `tdom_bias_for_week`) + `build_report_context()` Haupt-Aggregator. Pure Funktionen, nur Supabase-Reads.
- `shared/unsubscribe_token.py` — HMAC-Token `SHA-256(lower(email)+secret)[:16]`, 1:1 kompatibel mit der SQL-RPC.
- `scripts/weekly_newsletter.py` — CLI mit `--dry-run` / `--test` / `--to` / `--top-n`, Rate-Limiting 0.35s, Admin-Alert bei >10% Fehlerrate.
- `scripts/templates/weekly_report.html.j2` — Dark-Mode Jinja2-Template, 4 Sektionen, table-based, inline CSS für Cross-Client-Kompatibilität.
- `scripts/create_unsubscribe_rpc.sql` — Postgres `unsubscribe_with_token(email, token)` mit `SECURITY DEFINER`, nutzt `extensions.digest()` (pgcrypto im extensions-Schema) und validiert Token server-side.
- `landing/pages/unsubscribe.html` — statische Page mit vanilla JS, ruft Supabase `/rpc/unsubscribe_with_token`, zeigt success/error/missing Views mit V3 Ultra Styling.
- `shared/email_brevo.py::send_html()` — neue Funktion für beliebigen HTML-Body ohne Brevo-Template, Logging mit `messageId` + HTTPError-Body für Debug.
- `scripts/nightly_refresh.py` Phase F — feuert Sonntags ≥17 UTC automatisch das `weekly_newsletter.py` Subprocess, 30 min Timeout.
- `deploy/nginx.conf` — `location = /unsubscribe` mit Rewrite auf `/landing/pages/unsubscribe.html`, `Cache-Control: no-store`.

**Post-Launch Fixes:**
- Brevo API-Key TOML-Fallback in `_get_api_key()` für Cron-Kontext ohne Streamlit-Runtime.
- `SENDER` konfigurierbar via `SENDER_EMAIL` / `SENDER_NAME` Env-Vars.
- `seasonaledge.app` → `seasonalpha.ai` in Sender-Addresses (war nur der alte Repo-Name).
- `create_unsubscribe_rpc.sql` pgcrypto aus `extensions`-Schema.
- Brevo Domain-Authentifizierung für `seasonalpha.ai` (SPF + DKIM + DMARC + Brevo-Code im DNS).

**Erster Live-Test:** Sender `noreply@seasonalpha.ai` → `heiko.seibel@gmail.com`, Brevo-Status „Zugestellt", Mail im Gmail-Posteingang korrekt angekommen.

**Offene Restarbeiten:**
1. Nginx-Reload auf dem Server (`docker exec seasonalpha-nginx nginx -s reload`)
2. End-to-End-Test des Unsubscribe-Links (Inkognito-Tab)
3. Phase F Aktivierung — prüfen ob `nightly_refresh` Sonntags läuft
4. Content-Iteration des Reports basierend auf User-Feedback
5. Launch-Blog-Post

---

### Feature #1 — Guided Tour ✅ LIVE seit 2026-04-09

**Neu (implementiert):**
- `landing/js/tour-config.js` — **23 Tour-Steps** als Daten-Array (erweitert von ursprünglich 13)
- `landing/js/tour.js` — SA.tour Wrapper mit Lazy-Load Driver.js v1.3.1 via CDN, Multi-Page-Resume via `?tour=step:N`, `_resolveDriverGlobal()` mit mehreren Fallback-Export-Pfaden, sichtbares Error-Banner statt alert

**Erweitert:**
- `landing/css/app.css` — Driver.js Popover-Theming (V3 Ultra Dark + Gold) + `.nav__tour-btn` Klasse
- `landing/index.html` — **Inline** Nav-Button + inline CSS-Theming (diese Page lädt app.css nicht!)
- `landing/components/nav.html` — Tour-Button für alle Sub-Pages
- Script-Einbindung mit Cache-Busting `?v=20260409` auf: index, dashboard, jahreszyklus, backtest-engine, dekadenzyklus, zentralbanken, feiertage, trifecta, spot-vol-beta, plain-vanilla, ki-saisonalitaet = **11 Pages**

**Tour-Flow (23 Steps über 11 Pages):**
1. **Landing** — Welcome + Dashboard-CTA
2. **Dashboard** — Ticker-Input, Trading-Day-Header (TDOM/TWOY/TDOY/Q/Cycle), KI-Score, Crash-Ampel, Jahreschart, Events (6 Steps)
3. **Dekadenzyklus** — 131 Jahre DJI Kohorten-Chart
4. **Jahreszyklus** — Hauptchart, Sidebar-Controls, **Detrend-Indikator** (3 Steps)
5. **Zentralbanken** — Fed/EZB/BoE/BoJ Event-Window
6. **Feiertage** — Börsen-spezifisches Ranking
7. **Januar Trifecta** — SCR + FFD + JanB Ampelsystem
8. **Spot-Vol Beta** — SPX vs VIX Regression + Regimes
9. **Plain Vanilla** — 24 Strategien mit Equity-Kurve
10. **KI-Saisonalität** — Composite Score + Musterpfad
11. **Backtest Engine** — **Outlier Manager**, **Technische Filter**, Event-Typ, Tab-Nav (4 Steps)
12. **Finale** (zurück auf Dashboard)

**Post-Launch Fixes:**
- CDN-Load robuster: `_resolveDriverGlobal()` probiert `window.driver`, `window.driver.js.driver`, `window.driver.driver`
- Cache-Busting, weil nginx `/landing/` mit max-age=86400 liefert
- Landing-Page hatte EIGENE Inline-Nav (nicht components/nav.html) — musste an 2 Stellen patchen

### Feature #2 — Email-Alerts / Weekly Report

**Reuse:**
- `shared/email_brevo.py` — `send_transactional`, 5 Template-IDs
- `shared/supabase_client.py` — `unsubscribe_email`, Subscriber-Tabelle

**Neu:**
- `scripts/weekly_newsletter.py` — Cron-Job (Sonntag-Abend), rendert Top-5 Strategie-Signale pro Abonnent
- `scripts/create_alerts_table.sql` — `user_alerts` DB-Tabelle
- `landing/pages/alerts.html` — User-Alerts-Management UI

### Feature #3 — Saisonal-Scanner

**Reuse:**
- `supabase_client.fetch_scanner_results()` — liefert bereits sortierte Top-Scores
- `landing/data/tickers.json` — 300+ Tickers mit Metadaten
- `shared/symbols.py` `SYMBOLS` — Kategorien

**Neu:**
- `landing/pages/scanner.html` — Haupt-UI mit Filter (Kategorie, Score-Range, Richtung)
- `landing/js/scanner-compute.js` — Client-seitiges Filtering
- `deploy/nginx.conf` — neue Route `/scanner`

### Feature #4 — Auth + Custom Watchlists

**Reuse:**
- `landing/js/app.js` — Supabase-Client-Init

**Neu:**
- `scripts/create_users_watchlists_alerts.sql` — Tabellen `users`, `watchlists`, `user_alerts` mit RLS-Policies
- `landing/js/auth.js` — Login/Signup/Session-Management
- `landing/pages/login.html`, `signup.html`, `account.html`
- Jede bestehende Page: "⭐ zu Watchlist"-Button im Header

### Feature #5 — Portfolio-Backtest Combo

**Reuse:**
- `landing/js/strategy-compute.js` `SA.strategy` — 24 Strategien, Trade-Objekte, Stats
- `landing/pages/backtest-engine.html` — Tab-Struktur, KPI-Cards

**Neu:**
- `landing/js/portfolio-compute.js` — Multi-Strategy-Aggregation, Allocation, Rebalancing
- Tab "Portfolio" in `backtest-engine.html` ODER separate Page `/portfolio-backtest`

## Offene Design-Entscheidungen (Parking Lot)

Werden bei Start der jeweiligen Welle getroffen:

1. **#4 Auth:** Supabase Native Auth vs. Google OAuth vs. Hybrid?
2. **#5 Portfolio-Combo:** Fixed Allocation (40/30/30) vs. Dynamic Rebalancing vs. beides?
3. **#3 Scanner:** Realtime-Updates (intraday) oder Daily-Snapshot?
4. **#2 Alerts:** Separater Cron oder Integration in `nightly_refresh.py`?

## Nicht im Scope der Roadmap

- i18n / EN-Übersetzungen der Tour
- A/B-Testing-Framework für Tour-Completion-Rate
- Stripe Freemium / Premium-Abo (eigenes Thema)
- Mobile-Responsive Polish (läuft separat über Plan `humming-juggling-hinton.md`)

---

**Detail-Pläne:** Siehe `.claude/plans/peppy-dancing-kay.md` (Guided Tour) und `docs/` für Architektur-Referenzen.

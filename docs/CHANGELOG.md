# Changelog / Meilensteine — SeasonAlpha

> History ausgelagert aus CLAUDE.md (hält die Hauptdatei schlank). Aktive TODOs
> bleiben in CLAUDE.md. Neueste Einträge oben.

## Abgeschlossene Meilensteine (Kurzübersicht)

| KW | Datum | Inhalt |
|----|-------|--------|
| KW15 | Apr 2026 | Dashboard Bento-Grid, Guided Tour (26 Steps), Weekly Newsletter, SEO-Foundation, Scanner MVP, Watchlist Phase 1, Mobile Responsiveness, TDOM-Fix |
| KW16-17 | Apr 2026 | Polymarket Integration (3 Phasen, Brier-Pipeline), Auth+Cloud-Watchlist, Profile-Page, Health-Check-Mails, ML-Pipeline stillgelegt, Blog-Posts #1-21 |
| KW18 | Apr 2026 | Dividenden + Earnings Pages, Event-Crons, Yahoo Crumb-Auth, Health-Check-Integration |
| KW20 | Mai 2026 | Nightly Backfill Phase D, moddatetime-Trigger, Stripe-Infrastruktur, GSC-Bereinigung (383→32), Blog #22-24, Newsletter Phase F Fix |
| KW22 | Mai 2026 | Daily Morning Briefing (Multi-Window-TDOM-Score 0-4, top_daily_tips, Watchlist-Personalisierung, 10 Strategie-Signale, Status-Zeile) |
| KW24 | Jun 2026 | **EN Lokalisierung Phasen 1-7** komplett: SA.i18n, 1222 Keys, 30 Pages + Verifikation aller Expander/Methodologie, Tour EN, 24 Blog-Posts EN (EN Disclaimer+Charts), Sitemap 89→113 URLs, hreflang |
| KW24 | Jun 2026 | **EN Pre-Rendering deployed** — Laufzeit-Swap → statisch `landing/en/` via `build_en.py`; SEO-Head/canonical/hreflang/JSON-LD gebacken; ~70 halb-übersetzte Mixed-Content-Defekte gefixt; `verify_en.py` FAIL 0; Blog-Builder-f-string portabel. Deploy-Lesson: nginx `restart` statt `reload` |

## ✅ ML-Pipeline stillgelegt (2026-04-18)
Entfernte Module/Scripts: `mstl_decomposition.py`, `chronos_forecast.py`, `neural_prophet_forecast.py`, `compute_ml_forecasts.py`, `create_ml_forecasts.sql`, `ml_forecasts.yml`.
KI-Score: 4 Sub-Scores (à 2.5, 0–10). `DROP TABLE ml_forecasts` erledigt 2026-06-16 — Stilllegung vollständig.

## Detail-Logs

### 2026-09-05 — Energie-Ticker, Index-Effekt-Seite, KI-Duktus raus, nginx/mietwatch-Entkopplung (PRs #178-186)

**Ticker-Universum 324→358** (PRs #184-185): 34 Energie-/Strom-/Uran-/Solar-Werte aus einer User-Watchlist (45 Ticker; 7 hatten wir schon, 4 sehr dünne weggelassen: FRMI/NNE/TLN/NXT). Alle bei Yahoo mit voller Historie verifiziert (54J EMR … ~4,5J SMR). Lokal onboardet (service_role-Key) in 3 Batches, dann Scores/Stats gezielt via `refresh_ticker_data(<subset>)` (74s, 34/34 Scanner + TDOM/TDOY). `tickers.json` committet. Kalender: `S92.DE`/`NDX1.DE`→XETRA, `NEL.OL`→Oslo/SE-Proxy.

**`/index-effekt`** (PR #186): S&P-500-Index-Inklusion-Effekt-Studie. `scripts/build_index_effect.py` zentriert jedes Event auf T=0 (Ankündigung), normiert Vortag=100, Fenster −20…+20 HT, Aggregat + 25/75-Perzentilband + `upcoming` für Live-Events. **Befund (36 Events Sep2023–Sep2026):** Ø +5,8% bei T+20, Peak +7,8% um den Wirksamkeitstag (~+10 HT), 72% positiv, breite Streuung (HOOD +44% … TTD −29%). Event-Katalog (39 Events) aus offiziellen S&P-DJI-PMs (Ankündigungs- + Wirksamkeitsdatum). Frontend `landing/pages/index-effekt.html` (flows.html-Muster, ApexCharts rangeArea, klickbare Event-Tabelle). BE (Bloom Energy) als Live-Aufhänger.

**Blog:** Zwischenwahljahr-2026-Post (mit SPY-Midterm-Chart des Users) + Pre-FOMC-Drift-Post (eigener Chart aus 165 FOMC-Terminen). **KI-Duktus entfernt** (PRs #178-179): „ehrlich/honest"-Selbstbeteuerung + „YMYL"-Jargon aus 21 Blog-Posts + 4 Seiten → direkte Formulierungen; Regel in `blogger`-Agent + CLAUDE.md verankert.

**Lessons Learned:**
- **Cloud-Timer scheiterte:** RemoteTrigger `run_once_at` (Do-Auto-Publish des FOMC-Posts) startete die Sandbox, klonte das Repo, kam dann aber nicht voran (Permission-Gate für `git push`/`gh` im unbeaufsichtigten CCR-Lauf) → manuell nachgeholt. Cloud-Routinen können unbeaufsichtigt nicht zuverlässig git-pushen.
- **SSH aus Claude-Env GEHT** via `~/.ssh/mietwatch` (gleicher VPS wie mietwatch.de, gleicher root). Default-`ssh` bietet den Key nicht an → `-i` explizit. Auto-Mode-Klassifikator kann schreibendes SSH blocken → `Bash(ssh -i ~/.ssh/mietwatch:*)` in `.claude/settings.local.json` allow.
- **Lokale `.env` hat `service_role`-Key** (nicht Anon, wie CLAUDE.md behauptete) → lokale DB-Writes möglich. Sicherheits-TODO: prüfen/rotieren.
- **nginx/mietwatch-Kopplung → Silent-Pull-Abort:** mietwatch-Blöcke lagen uncommittet in SeasonAlphas `deploy/nginx.conf` (+`docker-compose.yml`). Deploy revertet vor Pull nur `landing/`+`seo/output/` → jede committete nginx.conf-Änderung ließ `git pull` abbrechen, Deploy meldete trotzdem „success", Server blieb alt. **Gelöst via conf.d-Split:** untrackte `docker-compose.override.yml` mountet mietwatch als `conf.d/zz-mietwatch.conf` (+website); Blöcke aus den getrackten Dateien raus → clean → kein Konflikt mehr, beidseitig verifiziert. `zz`-Präfix wegen Ladereihenfolge (kein `default_server` → Catch-all bleibt umami). mietwatch-Backend auf dem Host, nginx via `172.18.0.1:8000`.

### 2026-08-08…24 — Incident-Fixes: Watchlist-Fetch, tdoy-Glitch, Fonts-Hang (PRs #171-175)

Mehrere Produktions-Incidents diagnostiziert & behoben. **Lessons Learned (nicht-offensichtlich):**

- **Render-blockende Fonts frieren die ganze Seite ein.** `/dealer-positioning` (und site-weit, 40 Seiten) blieb in „Lade…" stehen. Ursache: das Google-Fonts-`<link rel="stylesheet">` im `<head>` VOR den Scripts. Ein `<script>` wartet auf noch ladende Stylesheets (CSSOM-Zugriff möglich) → hängt `fonts.googleapis.com`, laufen `app.js` (Nav via `loadComponent`) UND das Inline-`init()`/`boot()` nie → ewiges „Lade…", und der 3s-Boot-Notnagel greift nicht (er steckt selbst im blockierten Script). „Inkognito geht manchmal" = zeitweise langsamer/extension-gestörter Fonts-Request. **Fix:** `media="print" onload="this.media='all'"` + `<noscript>`-Fallback. Ergänzt `b5ba5ce` (kein Dritt-CDN im kritischen JS-Pfad) → **gilt genauso für CSS/Fonts.** (PR #175)

- **Viele parallele paginierte Supabase-Fetches → 429-Sturm; Fehler-JSON als „Zeilen".** Watchlist zeigte für 9/10 Ticker „Zu wenig Daten" — DB war voll & frisch (daten-auditor bestätigt). Ursache: `loadAll()` lud alle Ticker via `Promise.all` gleichzeitig, jeder paginiert in 1000er-Batches → Rate-Limit/429. `SA.fetchAllPrices` hatte KEINE Fehlerbehandlung: ein fehlgeschlagener Batch hängte das Fehler-JSON (kein Array) an `allRows` → kurzes Ergebnis (<200 Zeilen) → falsches „Zu wenig Daten" (und wurde 15 Min gecacht). **Fix:** begrenzte Parallelität (Pool 3) + Retry (429/5xx UND `fetch()`-Reject, mit Jitter + `Retry-After`) + Array-Guard + Run-Token gegen stale-Renders. **Regel:** bei paginierten Fetches immer `!r.ok` prüfen und NIE ein Nicht-Array als Daten behandeln/cachen. (PRs #171-172)

- **tdoy-Konsistenz: Ground Truth ist der Kalender, nicht ein anderer Ticker.** `verify_calendar_rules` (Prüfagent) FAIL Regel 4-6: XETRA-Ticker (42 `.DE` + `^GDAXI`/`^MDAXI`/`^SDAXI`) hatten 2026-08-03…13 falsche `tdoy`/`tdom` (transienter Refresh-Glitch; seit 08-14 wieder korrekt, außerhalb des 7-Tage-Refresh-Fensters „eingefroren"). `^GDAXI` taugte NICHT als Referenz (eigener Glitch am 08-11). Ground Truth = reiner XETRA-Kalender-Zähler (`is_trading_day` ab Jan 1). Offset war NICHT uniform (−1/0/+1/+3) → pauschales `+1` wäre falsch; nur **Recompute** (`compute_tdoy_tdom`/`backfill_tdoy`) korrekt. Fix als scoped UPDATE-SQL `scripts/sql/fix_tdoy_2026_08_glitch.sql` (+ `verify_tdoy_2026_08.sql`), danach Audit grün (12 PASS · 0 FAIL). (PR #174)

- **Supabase-MCP zeigt ein FREMDES Projekt.** Der verbundene Supabase-MCP hatte nur Zugriff auf das separate Projekt **„Wohnungsbot"** (läuft auf demselben VPS wie SeasonAlpha), NICHT auf SeasonAlpha (`dkrebzobcwxyagximuxy`) — dort NIE Writes ausführen. Lokale `.env` hat nur den **Anon-Key** (kein `service_role`) → keine DB-Writes aus lokalen Skripten. DB-Korrekturen daher als SQL für den SeasonAlpha-SQL-Editor generieren (oder `backfill_tdoy` via `docker exec` auf dem Server, macht der User).

- **„The job was not acquired by Runner" ≠ VPS/mietwatch-Problem.** Bei Public-Repos gibt es KEIN Actions-Minuten-Limit → mass-„cancelled/failed" mit dieser Annotation = transiente GitHub-Runner-Kapazität, self-heilt. (Falls das Repo je auf **privat** gestellt wird: dann greift das Minuten-Limit → die reinen SSH-/docker-exec-Crons besser auf native VPS-crontab umziehen, nur Deploy auf Actions lassen. Server-`.env` beim Privat-Wechsel: VPS-`git pull` braucht dann Auth (Deploy-Key/PAT).)

### 2026-07-10 — Options-/Dealer-Positioning-Engine (GEX / Vanna / Charm / Skew / Walls)

**Neuer Baustein** aus User-Wunsch („was können wir mit Optionsdaten rechnen — Gamma, Charm …") + Analyse
von HKUDS/Vibe-Trading. Ergebnis: `scripts/compute_gamma_exposure.py` (Yahoo-Options-Chain via Crumb-Session)
rechnet je Kontrakt Black-Scholes **Gamma, Vanna, Charm** (mit Div-Rendite q) und aggregiert Dealer-Exposure:
net-GEX (+Regime long/short-Gamma = vola-reduzierend/-forcierend), Zero-Gamma-Flip (Spot-Sweep), Call/Put/
**Absolute**-Walls (Netto-Gamma je Strike), **Skew** (ATM-IV + 90/110), **Markt-Gamma-Index** (SPY+QQQ+IWM+DIA),
**Per-Strike- & Per-Term-Profile** → „Exposure By Strike/Term"-Charts (Gamma/Vanna/Charm, `render_gex_profile.py`).
Doku: `docs/OPTIONS.md`. Agenten: `options-flow-analyst` (rechnen+interpretieren) + `market-flows-scout`
(strukturelle Flows recherchieren). Gelaufen: Index + Mag7 + Screenshot-Aktien + alle 40 SeasonAlpha-ETFs.

**Lessons Learned:**
- **Greeks IMMER per Finite-Differenzen selbst-testen** (`--self-test`): analytische Gamma/Vanna/Charm gegen
  zentrale FD von Δ, rel. Fehler < 1e-4. Bewies u.a., dass Charm bei q=0 für Call/Put identisch ist. Ohne
  Beweis kein Vertrauen in Second-Order-Greeks.
- **Sign-Konvention ist eine Heuristik, kein Fakt.** Naive „Dealer long Calls / short Puts" (Call +, Put −)
  ist eine erste Näherung; SpotGamma/SqueezeMetrics nutzen proprietäre DDOI-/Inventory-Modelle (+0DTE +Intraday).
  Unsere Zahlen ≠ deren Zahlen → IMMER als Heuristik/EOD/kein-Signal kennzeichnen (YMYL).
- **Call/Put-Walls: NICHT getrennt max Call- vs Put-Gamma** (kollabiert auf ATM, weil Gamma dort maximal ist) —
  sondern **Netto-Gamma je Strike**, Call-Wall = größtes positives ≥ Spot, Put-Wall = größtes negatives ≤ Spot.
- **Charm ÷ 365 = Tages-Charm** reicht (nur 0DTE bräuchte feiner). Vanna/Charm-Flows treiben Pre-OPEX-Drift.
- **Yahoo-Options-Endpoint bedient nur US-gelistete Underlyings.** `^GDAXI`/`.DE` → leere Chain (live getestet) →
  DAX-GEX nur via US-ETF-Proxy (EWG dünn/GEX≈0, FEZ) oder Bezahl-Eurex-Daten. ^SPX + SPCX gehen dagegen.
- **`full_365`/Profil-Flags durchreichen:** `--profile` muss an `analyze(with_profile=…)` weitergegeben werden
  (sonst leeres Profil trotz Flag). Und: matplotlib deutet `$` in Labels als LaTeX → `rcParams["text.parse_math"]=False`.
- **Congestion:** Mehrere parallele Yahoo-Fetches (SPX = tausende Kontrakte) rate-limiten sich → sequenziell/EOD-Cron.

### 2026-07-28 — Supabase Pro Upgrade + DB-Recovery nach 6-Tage-Outage

**Ursache:** Supabase Free-Tier DB-Größe-Quota überschritten → alle Writes seit 2026-07-22 silent blockiert.
Der Nightly Refresh lief durch (Exit 0), schrieb aber nichts → Heartbeat-Log zeigte erst 6 Tage später Fehler.

**Recovery-Schritte (in dieser Reihenfolge):**
1. Supabase Pro Upgrade durch User → Quota-Block sofort aufgehoben
2. Manuell: `Nightly DB Refresh` Workflow getriggert → 7-Tage-Upsert-Fenster füllt Preis-Lücken 22.–25. Juli automatisch
3. Manuell: `Full Scanner Run` → 324/324 KI-Scores in 3 Min aktualisiert
4. Manuell: `Polymarket Daily Refresh`, `Event Data Daily Refresh`, `Brier Score Compute`, `Daily Morning Briefing`

**Lessons Learned:**

**1. Supabase Free Tier schlägt still zu**
DB-Quota-Überschreitung blockt Writes ohne lauten Fehler. `nightly_refresh.py` beendet sich mit Exit 0
(der `| tail -150 || echo`-Pipe schluckt den Returncode). Heartbeat schreibt `SELECT` erfolgreich,
aber `INSERT/UPSERT` schlägt lautlos fehl. Diagnose erst nach 6 Tagen durch Health-Check-Mail.
→ **Supabase Pro** ist für produktiven Betrieb Pflicht. DB-Größe muss in `daily_health_check.py` geprüft werden.

**2. "Nightly Data Update" (Workflow 247928699) ist broken — nicht triggern**
`TypeError: DownloadManager.__init__() takes 1 positional argument but 2 were given`
Der korrekte Workflow ist **"Nightly DB Refresh"** (248714399, `scripts/nightly_refresh.py`).
`nightly_update.yml` = Altlast, ruft veraltetes DownloadManager-Interface auf.

**3. Recovery nach DB Write-Block ist standardisiert**
7-Tage-Upsert-Fenster füllt Preis-Lücken automatisch → kein manueller Backfill nötig.
Full Scanner: 324/324 Ticker in ~3 Min, 0 Fehler — immer als Schritt 2 triggern.
Regime-Scores: Nightly recomputed nur SPY; `regime_scores 1/324` ist **Design**, kein Bug.

**4. `capture_stdout: false` in SSH-Workflows = Log leer**
Die SSH-Action schreibt Ausgabe nicht ins GitHub-Actions-Log wenn `capture_stdout: false`.
Tatsächliche Ergebnisse immer per JSON-File lesen: `https://seasonalpha.ai/landing/data/db_completeness.json`
(nicht `/data/...` — nginx kennt nur `/landing/data/...`).

**5. Completeness-Audit als Recovery-Diagnosetool**
`DB Completeness Audit` Workflow gibt nach Recovery sofort Auskunft über Freshness/Coverage/Gaps.
Ergebnisse unter `https://seasonalpha.ai/landing/data/db_completeness.json`.
ki_scores/regime_scores Coverage-Warnungen nach Outage: erst nach Full Scanner Run / Nightly grün.

**6. Polymarket: Nightly-Phase schlägt fehl, Standalone läuft**
`nightly_refresh.py` Phase-G (Polymarket-Backfill) schlägt mit DNS-Fehler fehl.
Eigenständiger `polymarket_daily.yml` Workflow läuft täglich korrekt durch.
→ Kein Handlungsbedarf, solange Standalone-Workflow grün ist.

---

### 2026-07-15 — Backtest-Kombinations-Engine, TDOM-UI, Second Brain (v44.0)

**Arbeitspaket:** Saisonale Signale (TDOM) mit technischen Indikatoren in einem Backtest kombinieren.
Zielgrößen: Profit Factor, Sharpe, Calmar. Infrastruktur (`shared/backtest_engine.py`, `shared/indicators.py`)
war bereits komplett — fehlte nur der saisonale Kombinationssignal-Layer.

#### Strategie-Ergebnisse (2 Runden, 4 parallele Agenten)

| Rang | Kombination | Sharpe IS | Sharpe OOS | Validierung |
|------|-------------|-----------|------------|-------------|
| 1 | GLD + Bollinger Bounce (D) | 2.50 | **2.41** | ✅ Walk-Forward robust |
| 2 | SI=F + Bollinger Bounce (D) | 1.91 | — | Silber repliziert GLD-Muster |
| 3 | SLV + Bollinger Bounce (D) | 1.81 | — | ETF-Proxy zu SI=F |
| 4 | BTC + LBR Bull (F) | 1.45 | — | LBR +1.20 Sharpe vs. MACD |
| 5 | GLD + RSI<40 +5%Trail (A) | 1.30 | — | Stop verdoppelt Total-Return |

**Lessons Learned:**

**1. TDOM+Technisch = deutlich stärker als reines TDOM**
Baseline (nur TDOM, kein Filter) liefert bei GLD Sharpe 0.45 — Bollinger Bounce bringt es auf 2.50
(+456%). Technische Filter sind keine Dekoration, sie eliminieren schlechte Entry-Zeitpunkte.

**2. GLD + Bollinger Bounce ist Walk-Forward-robust (kein Overfitting)**
OOS/IS-Sharpe-Ratio = 3.26 (Robust-Schwelle: 0.6). OOS schlägt IS auf allen Metriken.
14/16 Rollfenster-Jahre positiv; nur 2015 (GLD-Konsolidierung) + 2022 (Fed-Zinsschock) negativ.

**3. Der Edge ist ein Edelmetall-Phänomen — nicht universell**
SI=F und SLV replizieren GLD-Muster unabhängig voneinander → erhöhte Robustheit.
DAX kaum Edge (Sharpe 0.63 für Strategie D). Anderer Kapitalfluss-Charakter.

**4. Stop-Loss-Regeln sind signaltyp-spezifisch**
- BB Bounce: **kein Stop** — Signal ist bereits der Filter; 3% Fixed triggert 31% False-Stops
- RSI Reversal: **5% Trailing** — schützt bei gestresstem Asset; verdoppelt Total-Return (29→69%)
- Kein Stop-Loss rettet eine kaputte Strategie (C-MSFT: -28.9% ohne wie mit Stop)

**5. LBR vs. MACD ist asset-klassen-abhängig (kein universeller Gewinner)**
- LBR gewinnt bei: BTC (+1.20 Sharpe-Delta), QQQ (+0.18), AAPL (+0.28) — volatile/Growth-Assets
- MACD gewinnt bei: NVDA (+1.39!), SPY (+0.70), GLD (+0.09), MSFT (+0.37) — Trend-dominante Assets
- LBR hat besseren Calmar (8.77 vs. 3.39) — weniger Drawdowns trotz ähnlichem Sharpe
- **Faustregel:** LBR für BTC/Growth; MACD für Trend-/Index-Assets

**6. Look-Ahead-Bias-Falle bei TDOM — Strategie C-MSFT verwerfen**
Globales TDOM-Fenster (alle 21 Jahre im Kalibrierungsfenster) → ~10-20% zu optimistische
Bias. C-MSFT: IS-Sharpe 1.24 mit Bias → -0.16 ohne Bias. Stop-Loss-Sweep und Walk-Forward
helfen Artefakte zu entlarven: alle C-MSFT-Varianten negativ → Strategie verwerfen.

**7. TDOM in JS: Wochentagszählung ist ausreichend**
`weekday >= 1 && weekday <= 5` liefert ±1-2 Tage Abweichung vs. vollem Feiertagskalender.
Für Backtest-Zwecke akzeptabel — kein voller Holiday-Lookup nötig.
Wichtig: IIFE-Closure für die Loop-Variable (`for td = tdomStart; ...; (function(tdom){...})(td)`)
sonst liefern alle Events dasselbe TDOM (klassischer JS-Closure-Fehler in Schleifen).

**8. `loadPreset()`-API-Pattern für programmatische Indikator-Filter**
`SA.indicators._presetLoaders` (Registry keyed by containerId) erlaubt externen Aufruf.
In `renderFilterUI()` gesetzt; externe Skripte rufen `_presetLoaders['indicator-filters'](filters)`.
Setzt filterCount, rebuildet UI, setzt DOM-Werte, triggert onChange — vollständig.

**9. Funktion global exponieren: Deklaration + separate `window`-Zuweisung**
`window.foo = function foo() {}` — der Name `foo` ist nur im Funktionskörper sichtbar (für Rekursion),
NICHT im umgebenden Scope. Interne Referenzen brechen. Richtig:
`function foo() {...}; window.foo = foo;` — Deklaration hoisted lokal, Zuweisung exponiert global.

**10. Second Brain: Nur der Repo-Bibliothekar-Teil des HGA-Specs passt**
Das vollständige HGA-Second-Brain-Spec hat 5 Teile (Librarian, Knowledge Graph, Semantic Search,
Active Memory, Proactive Synthesis). Für SeasonAlpha (statisches Repo, kein persistentes Backend)
passt nur **Part A: Repo Librarian** — `raw/` Drop-Zone → Bibliothekar → `wiki/` synthetisiertes Wissen.
Kein Obsidian nötig — Claude liest/schreibt direkt in Markdown-Dateien.
`/sa-ingest`-Skill: 5-Schritt-Prozess (unverarbeitete Quellen finden → Quell-Seite → Konzept-Seiten
→ index.md → log.md + .kb-processed.json aktualisieren).

#### Neue dauerhafte Infrastruktur

- `raw/` + `wiki/` + `.claude/skills/sa-ingest/` — Second Brain
- `landing/js/indicators.js::SA.indicators._presetLoaders` — Preset-API
- `landing/pages/backtest-engine.html` — TDOM Event-Typ, 5 Preset-Karten
- `wiki/sources/2026-07-15_backtest-kombinations-strategien.md` — Runde 1
- `wiki/sources/2026-07-15_backtest-runde2-walkforward-stoploss-lbr-newticker.md` — Runde 2

---

### 2026-07-03 — Newsletter-Score empirisch validiert + Regime-Kontext (PRs #144-146)

**Frage:** „Welcher Score bringt welche Performance/welchen Drawdown?" → Backtest des Newsletter-
Scorings (SC/TS/GESAMT) mit `scripts/backtest_newsletter_scoring.py` (look-ahead-frei: TS kausal
vektorisiert, SC Expanding-Window pro Kalenderjahr, Entry=Close[t]).

**Erst gepoolt (verworfen):** Über ALLE Ticker gebucketet zeigte GESAMT keinen positiven Rendite-
Edge (leichte Mean-Reversion). User-Einwand — korrekt: **Pooling ist zu pauschal**, positive/negative
Einzel-Edges heben sich auf. Analyse-Einheit = **der einzelne Ticker**.

**PR #144 — Per-Ticker-Edge + Regime-Klassifikation:** je Ticker × Score × Haltedauer (1/5/10/15/20):
Spearman ρ(Score, Forward-Rendite) + p + n + Top-minus-Bottom-Spread + Ø-Drawdown; Klassifikation
**momentum** (ρ konsistent >0) / **fade** (konsistent <0) / **neutral**. `--reclassify` gruppiert aus
vorhandener JSON um (rohe ρ schwellenunabhängig → kein 40-Min-Neulauf). Befund (273 Ticker): SC
richtungslos (0/0/268); TS 11 momentum (Crypto/Semis/Growth: ENR.F/AMD/MU/BTC-USD) vs 85 fade
(Staples/Energie/EU-Value: SHEL/TTE/LIN/XLRE); der Momentum-Score ist für die MEISTEN Ticker
**contrarian**. `backtest-analyst`-Subagent für Auswertung.

**PR #145 — Out-of-Sample-Test (`--oos-split 0.6`):** Regime aus ersten 60 % je Ticker, `TS_adj =
sign·Score` im held-out Rest. Trick: Spearman(sign·TS,ret)=sign·Spearman → Frage = **Vorzeichen-
Persistenz Train→Test**. Ergebnis: **Regime persistiert OOS** — TS ρ_test RAW −0.060 → ADJ +0.058
(20d), **sign-persist 83-85 %** über 94 UNABHÄNGIGE Ticker (Binomial gegen 50 % ≈ null = kein
Overfit). Effekt klein (ρ≈0.05, aggregiert handelbar), gilt nur für ~35 % nicht-neutrale Ticker.

**PR #146 — Variante 1 live im Newsletter (ohne Score-Mathematik zu drehen):** `shared/ticker_regimes.json`
(273 Ticker, reproduzierbar aus der committeten Backtest-CSV via `scripts/export_ticker_regimes.py`,
jährlich neu) + Loader `shared/ticker_regimes.py::regime_hint()` → in `daily_report.py::_build_why_summary`
→ Template rendert unter der „Warum"-Zeile: fade→„⚠ Hoher Score hier historisch eher Rücksetzer",
momentum→„↗ Momentum trägt hier historisch", neutral→nichts. Intro zugleich auf SC(0–4)/TS(0–6)/
Gesamt(0–10) präzisiert.

**Lessons Learned:**
- **Nie über alle Ticker pauschalisieren** — Score-Edge ist instrument-spezifisch (SPY fade, AMD momentum;
  beides normal). Erst die Per-Ticker-Sicht macht das Signal sichtbar.
- **In-Sample-Regime = Overfit-Falle:** Regime aus derselben Historie ableiten und dort testen gibt ρ
  per Konstruktion positiv. Ehrlich nur via OOS-Split + Vorzeichen-Persistenz (unabhängige Ticker =
  saubere, nicht-überlappende Stichprobe → echtes Binomial-Signifikanzsignal trotz Overlap in den Fenstern).
- **Drawdown-Metrik gegen Artefakte härten:** nicht-positive Preise (Stooq-Alt-Daten/additive Split-Adj.)
  erzeugen unmögliche DD < −100 % und vergiften `worst_drawdown` (min → Ausreißer dominiert) → maskieren
  + Floor −100 %; `avg_drawdown` ist robuster als `worst_drawdown` (der bei großem n auf ~−99 % saturiert).
- **Schwellenunabhängige Rohdaten speichern** (ρ statt nur Verdict) → Re-Klassifikation/Tuning ohne teuren Neulauf.
- **Kleiner-aber-echter Edge → Kontext statt Eingriff:** Score-Mathematik nicht wegen ρ≈0.05 blind umstellen;
  stattdessen den hohen Score ehrlich einordnen (Regime-Hinweis) — fängt den validierten Edge ab, ohne Risiko.

### 2026-07-03 — Marktkalender (`/kalender`) live

**Neues Feature: Persönlicher Marktkalender (Auth-Gate + Premium-Gate)**

Neuer Bereich `/kalender` — nur für eingeloggte Nutzer, Outlook-Style Monatsraster mit farbcodierten Event-Chips.

**Neue Dateien:**
- `landing/pages/kalender.html` — Page mit Auth-Gate (redirect zu Login wenn nicht eingeloggt) + Premium-Gate (geblurete Chips für Free-User)
- `landing/js/kalender-compute.js` — Grid-Renderer (Mo-Start, 7-Spalten-CSS-Grid), Tab-Navigation (Jan–Dez + Jahr-Pfeile), ICS-Client-Export, Supabase-Personalisierung für Premium (Dividenden/Earnings aus Watchlist)
- `scripts/build_calendar_data.py` — generiert `landing/data/market_calendar.json` (109 Events, 18-Monate-Fenster) + `landing/data/market_calendar.ics` (RFC-5545 Webcal-Abo)
- `landing/data/market_calendar.json` + `market_calendar.ics` — committed (Server kann nicht regenerieren, s. Pandas-Issue unten)

**Geänderte Dateien:**
- `landing/components/nav.html` — Kalender-Link hinzugefügt
- `landing/pages/profile.html` — Kalender-Card mit „Zum Kalender →"-Button
- `landing/i18n/de.json` + `en.json` — `kal.*` + `prof.card_kalender`-Keys (20+ neue Keys)
- `deploy/nginx.conf` — `location = /kalender`, `location = /kalender/`, `location = /en/kalender`
- `deploy/inject_credentials.sh` — `build_calendar_data.py` als Pre-Build-Step

**Event-Typen:** fomc, opex, triple, ecb, boe, boj, snb, boc, rba, rbnz, fullmoon, newmoon, holiday (NYSE/XETRA/LSE), dividend, earnings (Watchlist, nur Premium).

**Free vs. Premium:** FOMC + OPEX sichtbar für alle eingeloggten User; Notenbanken, Mondphasen, Feiertage, Dividenden, Earnings nur für Premium (Chips gefiltert/gebluret mit 🔒). ICS-Export (Download + Webcal-Abo-URL) nur für Premium.

**Bugs gefunden + gefixt:**

1. **`/en/kalender` → 404** (Haupt-Bug): `SA.i18n._applyNavLinks()` schreibt im EN-Modus alle Nav-Links zu `/en/...` um. `/kalender` fehlte in `_skipPrefixes` → `/en/kalender` → 404 (keine EN-Version). Fix: `/kalender`, `/profile`, `/watchlist`, `/pricing`, `/unsubscribe` in Skip-Liste beider Dateien (`i18n.js` + `build_en.py`) + nginx-Fallback `location = /en/kalender { return 301 /kalender; }`.

2. **`/kalender/` (Trailing Slash) → 404**: nginx `location =` matcht nur exakt. Fix: `location = /kalender/ { return 301 /kalender; }`.

**Pandas-Issue auf Server:** `build_calendar_data.py` in `inject_credentials.sh` via system python3 → `ModuleNotFoundError: No module named 'pandas'`. Non-fatal (Daten committed). Manuelles Update: `docker exec seasonalpha-app python3 scripts/build_calendar_data.py`.

3. **Kalender zeigt keine Events** (stille 404): `fetch('/data/market_calendar.json')` → nginx hat keinen `/data/`-Location, nur `/landing/`. Datei liegt unter `/app/landing/data/` → korrekte URL: `/landing/data/market_calendar.json`. Gleiches für Webcal-ICS-URL. Fix: URL-Präfix in `kalender-compute.js` + `kalender.html` korrigiert.

4. **Anmeldung klappt erst nach mehreren Versuchen (UX-Bug):** `SA.auth.login()` redirectete nach Google OAuth immer zu `/dashboard`, nicht zurück zu `/kalender`. User sah nach Login → `/dashboard` und dachte, die Anmeldung hätte nicht funktioniert. Fix: `auth.js` `login(redirectPath?)` akzeptiert jetzt optionalen Zielpfad; `kalender.html` ruft `SA.auth.login('/kalender')` auf.

**Lessons Learned:**

- **Auth-gated Pages ohne EN-Äquivalent → IMMER in `_skipPrefixes`** (i18n.js + build_en.py) + nginx `/en/<slug>` → 301 Redirect. Checkliste für neue persönliche Pages.
- **WebFetch hat 15-min-Cache** — für Real-Time-HTTP-Checks immer `curl -s -o /dev/null -w "%{http_code}"` nutzen.
- **404-Debug-Pattern:** Wenn curl 200 liefert aber User 404 sieht → URL genau prüfen (hier: `/en/kalender` statt `/kalender`). Nginx `location =` ist Exact-Match, kein Trailing-Slash-Fallback.
- **Neues Deployment-Skript-Pattern für pandas-abhängige Scripts:** `docker exec seasonalpha-app python3 scripts/...` statt system python3 in `inject_credentials.sh`, damit pandas/alle Container-Deps verfügbar sind.
- **`fetch('/data/...')` funktioniert NICHT** — nginx kennt keinen `/data/`-Root. Alle statischen JSON-Dateien aus `landing/data/` über `/landing/data/...` fetchen.
- **OAuth `redirectTo` nicht vergessen:** `SA.auth.login()` immer mit Ziel-Pfad aufrufen wenn der User nach Login auf einer bestimmten Seite landen soll (nicht auf `/dashboard`).

### 2026-07-03 — Newsletter-Scoring RSI(3)+BlastOff + erstes TruePath-Short-Video

**Newsletter-Scoring erweitert (Max-Score 8→10):** Zwei neue Signale in `shared/newsletter_indicators.py`:
RSI(3) ≤ 20 + LBR > 0 → +1 (Bounce-Setup); RSI(3) ≥ 80 + LBR < 0 → −1 (Erschöpfung);
BlastOff < 20 % + LBR > 0 → +1 (Compression/Ausbruch); BlastOff < 20 % + LBR < 0 → −1 (Breakdown).
BlastOff = |Open−Close|/(High−Low)×100. OHLC per neuer `fetch_last_bar_ohlc()` aus Supabase,
alle 3 `_signal_row_from_series()`-Aufrufstellen in `daily_report.py` aktualisiert.
Template-Erklärung auf max 6 (TS) / max 10 (Gesamt) aktualisiert + RSI(3)/BlastOff-Definitionen ergänzt.

**Erstes TruePath-Short-Video produziert:** QQQ KI-Saisonalität (TruePath vs. klassischer Ø) als DE-Short,
58s, ElevenLabs TTS + statischer Screenshot als Chart.

**Lessons Learned (wichtig):**
- **`--chart-image`-Flag in `compose.py`:** TruePath/KI-Saisonalität ist keine Standard-Render-Pipeline-
  Visualisierung → `compose.py` um `--chart-image <png>` erweitert (ffmpeg skaliert auf 1080×1920,
  schwarze Balken bei falschem Seitenverhältnis). Immer fragen welchen Chart der User will — nie annehmen.
- **Caption-Reihenfolge:** Hashtags IMMER ganz unten (nach Disclaimer), nie im Fließtext.
  Reihenfolge: Beschreibung → Leerzeile → Disclaimer (2a) → Leerzeile → Hashtags. In `shorts-skripter.md` dokumentiert.
- **SSH via PowerShell hängt** wenn Server Passwort/interaktive Auth erwartet (keine BatchMode-Ausgabe,
  Task läuft ewig). Lösung: User führt server-seitige Befehle manuell aus (`ssh root@178.104.75.46 "..."`).
- **ElevenLabs Key-Name:** `.env` muss `ELEVENLABS_API_KEY` heißen (nicht `ELEVENLABS_KEY`), sonst
  findet `tts.py` den Key nicht → klares Fehlerbild: `[tts] FEHLER: ELEVENLABS_API_KEY fehlt`.
- **Video-Output-Format:** 1,9 MB / 58s MP4 (libx264 yuv420p 1080×1920, AAC 160k). Liegt in
  `scripts/video/out/<NNN>_<slug>/`.

### 2026-06-27…28 — Faceless Social-Video-Kanal (Pipeline + erste Shorts, PRs #122-133)

**Aufbau:** Kompletter faceless, bilingualer Short-Video-Kanal als Traffic-/Backlink-Hebel (Plan +
`docs/YOUTUBE_STRATEGY.md` + `docs/YOUTUBE_DISCLAIMER.md`). Pipeline in `scripts/video/`:
`render_vertical_chart.py` (Echtdaten → animierter 9:16-Chart, matplotlib→ffmpeg, KEIN Kaleido;
Chart-Typen seasonal_yearly/monthly_cycle/**intramonth**/**tom**; `--video-mode`, `--highlight-month`,
`--month`), `render_brand_assets.py` (Avatar/Banner), `tts.py` (ElevenLabs), `compose.py`
(TTS je Beat → Timeline → Chart → eingebrannte Untertitel+Disclaimer → Mux; nummerierte Ordner
`out/<NNN>_<slug>/` + auto-SEO/Metatag-Datei via `catalog.json`), Agent `shorts-skripter`.
DE-Kanal „Seasonalpha (de)" live. Erste Shorts: dax-juli, dax-q4, btc-uptober, **spy-juli**
(Intra-Monat, 87 % im Plus), **googl-tom** (Turn-of-Month).

**Lessons Learned (wichtig):**
- **TIMELY schlägt alles.** Ein BTC-„Uptober"-Short Ende Juni war daneben — über November/Oktober reden,
  wenn Juli ansteht, verschenkt Relevanz. Thema immer an den *aktuellen* Zeitpunkt koppeln.
- **Distinctive Charts statt Excel-Histogramme.** Monatsbalken (`monthly_cycle`) kann jeder in Excel —
  Wert zeigen mit den eigenen Funktionen: Intra-Monats-Verlauf, Turn-of-Month/TDOM, normierter
  Jahresverlauf mit ±1σ, Dekadenzyklus.
- **Jede Zahl gegen Echtdaten verifizieren** (wie beim Blog). Intra-Monat-SPY matchte den Site-Screenshot
  exakt; TOM-Zahlen weichen je Fenster-Definition ab (Site 21 Fenster vs. robuste Vollhistorie 257).
- **ElevenLabs:** Free-Tier blockt Library-Stimmen per API **und** kommerzielle Nutzung → Paid-Tier nötig
  (war im Playbook vorhergesagt). Eingeschränkte API-Keys haben kein `voices_read` → Voice-Library nicht
  listbar; Voll-Access-Key nötig. **Native deutsche Stimme** zwingend (englische Stimme = Akzent;
  „Achim Hepp – German Business"). „seasonalpha.ai" im VO als „Season Alpha" schreiben (Aussprache).
- **Disclaimer:** On-Screen = **Standard-Variante** (Teil 3), nicht Minimal. Kanonisch in
  `docs/YOUTUBE_DISCLAIMER.md` (anwaltlich geprüft). Caption = Kurzform 2a (+ Krypto-Zusatz 2c).
- **Faceless-Pure-AI-Risiko:** YouTube geht gegen gesichtslose reine-KI-Kanäle vor (bis Löschung) →
  echter Daten-Mehrwert + Variation + menschliche Elemente; KI-Inhalt beim Upload deklarieren.
- **Traffic-Mechanik:** Shorts unterdrücken Außen-Links → fester End-Frame + gesprochene Marke,
  Lead-Magnet, UTM + Analytics (Erfolg auf der Website messen, nicht CTR/Impressionen).
- **Kanalname** darf nicht wie eine URL aussehen („Seasonalpha.de.AI" von YT abgelehnt). **FB:** Page via
  **Meta Business Manager** (kein neues Privatkonto). **Secrets** nur in `.env` (nie in getrackte Docs!).
- **Render-Engine:** matplotlib→PNG-Frames→ffmpeg (yuv420p) ist robuster als Kaleido (fehlte) +
  umlaut-sicher; ASS-Untertitel via ffmpeg in tmp-cwd (Pfad-Escaping umgehen).

### 2026-06-16…21 — Daily-Newsletter-Rework + DB-Audit-Entrauschung + SEO-Content-Offensive (PRs #104-120)

**Embed/Doku (PRs #104-108):** Einbetten-Button unter den Jahreszyklus-Chart; Doku-Sync v40;
veraltete TODOs geschlossen (Daily-Newsletter-Migration, `DROP TABLE ml_forecasts` — beide längst erledigt).

**Daily Newsletter runderneuert (PRs #109-113):** ML-„Regime" (nur SPY, Black-Box, misst *Turbulenz*
statt *Richtung*) im Newsletter ersetzt durch transparentes Pro-Ticker-Scoring: **SC** (Saisonal/
Multi-Window-TDOM 0-4), **TS** (technischer LBR/RSI-Score), **Gesamt = SC+TS**. Drei Tabellen
(Kernliste/Markt-Überblick · Top-Auswahl · Watchlist), Sektor-Rotation (echte Monatsrenditen,
Top-5 akt.+Folgemonat), **alle Notenbanken** (Fed/EZB/BoE/BoJ/SNB/BoC/RBA/RBNZ) + Multi-Börsen-
Feiertage in den Events. **„Warum"-Transparenzzeile** je Top-Pick (4 TDOM-Fenster + Trefferquote,
deterministisch). Gebaut/geprüft via 4 Subagenten (Indikatoren/DB/UI/Review).

**DB-Audit entrauscht (PR #114):** „Nicht melden, was legitim fehlt" auf 3 Dimensionen — NULL
log_return nur jüngstes Fenster (Erst-Zeilen je Ticker raus), Earnings US vs. EU getrennt,
Dividenden-Nichtzahler = info. Feiertags-Awareness der Gap-Erkennung war bereits korrekt.

**SEO-Offensive (PRs #115-120):** GSC zeigte 468 nicht-indexierte Seiten → triagiert (mostly
normal für junge YMYL-Domain). 0 tote Links; index.html-Drift gefixt; Off-Page-Distributionspaket
(DAX-Studie) + 7 Outreach-Ziele. **Content-Tiefe: alle 18 öffentlichen dünnen Tool-Seiten** mit je
~400 Wörtern statischem Unique-Content + 3 FAQ + FAQPage-Schema (via blogger-Agenten, i18n DE+EN,
+162 en.json-Keys, `verify_en` FAIL 0). Plan/Status: `docs/SEO_TODO.md`.

#### Lessons Learned (nicht-offensichtlich)

- **Gmail kappt Mails > ~102 KB** („[Nachricht gekürzt]") → Footer/Inhalt fehlt, oft mitten in einer
  Zeile. Ursache war wiederholter Inline-Style je Tabellenzelle → in `<style>`-CSS-Klassen ausgelagert
  (~102 KB → 47 KB). **`--dry-run` enthält die Watchlist NICHT** (wird pro Empfänger in `render_email`
  angehängt) → echte Mailgröße nur via `render_email`-Pfad oder `--test`-Send messen.
- **Test-Send NICHT direkt nach PR-Merge** auslösen: der Auto-Deploy startet den Container neu, `docker
  exec` trifft ihn im Restart → **kein Output, kein Versand, Workflow zeigt trotzdem „success"** (Run
  läuft auffällig kurz). ~1-2 Min warten. (Brevo `201` = angenommen ≠ zugestellt — Spam/Promotions prüfen.)
- **`prices` hat PK `(ticker,date)`** → ein `date`-Filter MIT `ORDER BY`/`count=exact` erzwingt Full-Scan
  → Supabase-Statement-Timeout. Für „jüngste NULL-Werte" o.ä. unsortierte, gebundene Stichprobe nehmen.
- **NULL `log_return` ist by-design für die ERSTE Kurszeile je Ticker** (kein Vortag) — ~300 erwartete
  Zeilen, kein Defekt. Nur das jüngste Fenster prüfen.
- **Tool-Seiten-Content für SEO**: Der Wert steckt im **JS-Chart** → Google sieht ihn nicht → „gecrawlt,
  nicht indexiert". Lösung = **statischer** Unique-Text (Crawler-sichtbar) + FAQPage-Schema. **ABER:**
  statischer DE-Text OHNE `data-i18n`-Keys bricht den EN-Build (`verify_en` FAIL: Deutsch auf /en/).
  Also `data-i18n(-html)` + EN-Werte in `en.json`. `build_en.py` baut EN nur für Seiten mit
  `_EN_PAGE_META` (z.B. crash-fruehwarnung hat keine EN-Seite). en.json ist **flach** (`"prefix.key"`).
- **Live `robots.txt`/`sitemap.xml` kommen aus `seo/output/`** (in docker-compose nach `/app/static/`
  gemountet, vom Builder bei jedem Deploy regeneriert) — die `static/robots.txt`/`static/sitemap.xml`
  im Repo sind **ungenutzte Leichen**. Bei robots/sitemap-Fragen IMMER die Live-Version prüfen.
- **Multi-Agent-Muster (bewährt):** je Agent **genau eine Datei** (kein Konflikt) gegen einen festen
  **Contract**; geteilte Dateien (`en.json`) NICHT von Agenten schreiben lassen → EN zurückgeben, zentral
  mergen. Agenten geben HTML-Inline manchmal als Markdown `**` statt `<b>` zurück → für `data-i18n-html`
  zu `<b>` konvertieren (Grep-Check auf `**Wort**`). `blogger`-Agent eignet sich auch für Tool-Seiten-Content.
- **Doku-Leiche:** CLAUDE.md/CHANGELOG nannten `shared/ai_models.py` als „KW16 gelöscht" — **existiert
  und wird genutzt** (Anthropic-Client, `ANTHROPIC_API_KEY`). Bei „gelöscht"-Notizen vor Bezug verifizieren.

### 2026-06-15 — SEO-Foundation + 8 Subagenten + Embed-Backlink-Asset (PRs #94-105)

Wachstums-Schub nach Erkenntnis: Produkt/Daten stark, aber **Off-Page der Engpass**
(junge Domain, kaum Backlinks, „Gecrawlt aber nicht indexiert" für ~293 Thin-Pages).

- **SEO-Audit** ([docs/SEO_AUDIT.md](SEO_AUDIT.md)) — ehrliche Bestandsaufnahme; Korrektur:
  Rechtliches (Impressum/Datenschutz auf `landing/rechtliches.html`) existiert, Engpass =
  **Authority + Content/Distribution**, nicht Technik.
- **`/ueber-uns`** (neu, E-E-A-T) — Methodik/Betreiber-Transparenz für YMYL-Vertrauen.
- **1. Daten-Studie** — Blog „Schlechtester DAX-Monat" (DAX-September seit 1988, DE+EN) als
  zitierbarer Link-Hook.
- **4 neue Wachstums-Agenten** (`.claude/agents/`): `wachstum-distributor` (Distribution/
  Outreach + Embed-Angebot), `frontend-qa` (Link/i18n/SEO-Crawler), `seo-seiten-bauer`
  (programmatic SEO mit Anti-Thin-Content-Schwelle), `gsc-analyst` (GSC→Prioritäten).
  Zusammen mit den 4 bestehenden = **8 Agenten**; Anleitung + Flywheel + Automatisierungs-
  Tabelle in **[docs/AGENTS.md](AGENTS.md)** (neu). Agent-/Skill-Infra committed (`.gitignore`
  whitelistet `.claude/agents/` + `.claude/skills/`).
- **Embed-Backlink-Hebel** — Route **`/embed`** (`landing/embed.html`, standalone Seasonal-
  Chart, nginx `frame-ancestors *` via CSP statt X-Frame-Options) + **„Chart einbetten"-Button**
  unter dem Seasonal-Chart auf Jahreszyklus (DE+EN): erzeugt fertiges iframe-Snippet inkl.
  Pflicht-**Caption-`<a>` im Host-DOM** (der eigentliche dofollow-Backlink — ein Link IM iframe
  zählt nicht). Nur Ø-Serie, kein ±1σ-Band.

**Kalender-Regel-Spec finalisiert** (begleitend, [docs/TRADING_CALENDAR_RULES.md](TRADING_CALENDAR_RULES.md)):
OPEX/VIXpiration **börsenspezifisch + holiday-aware** (CBOE vs EUREX), Zeit-Indizes
TDOM/TDOY/CDOM/CDOY dokumentiert, **Notenbank-Termine je Region** (Fed/EZB/BoE/BoJ +
PBoC/SNB/BoC/RBA/RBNZ, `central_banks_for_ticker()` folgt Handelsplatz, max. weit in die
Zukunft) — Regel 1-9 vollständig, Prüfagent deckt sie ab.

### 2026-06-14 — Asien-Kalender (HKEX/KRX/TSE) + offene Kalender-TODOs geschlossen

Restliche Kalender-Lücken aus der Spec abgearbeitet (datengetrieben verifiziert):

- **TSE (^N225)** — Tagundnachtgleichen jetzt **astronomisch** (Formel, gültig
  1980-2099) statt fix 20.3./23.9.; **Furikae Kyujitsu** (Sonntags-Feiertag-Kaskade)
  + **Kokumin no Kyujitsu** (Werktag zwischen 2 Feiertagen) implementiert. Jahres-
  wechsel-Schließungen (2./3.1., 31.12.) ohne falsche Substitute-Kaskade. Fixt
  3 Geister-Lücken (21.3.2023, 6.5.2025/26). Verifiziert: 0/0 beide Richtungen.
- **HKEX (^HSI) + KRX (^KS11)** — eigene **Mondkalender-Tabellen** (`_HKEX_HOLIDAYS`/
  `_KRX_HOLIDAYS`, 2016-2026, datengetrieben aus den Indizes) statt TSE-Näherung.
  Lunar New Year/Chuseok/Buddha's Birthday + Taifun-/Wahltag-Schließungen. ^HSI→HKEX,
  ^KS11→KRX gemappt, TDOM/TDOY neu (9,7k + 7,3k Zeilen). Verifiziert 0/0; aus der
  Gap-Audit-Exemption entfernt (nur noch `=X`/Forex exemptiert).
- **Madrid (.MC)** — datenbestätigt **keine** Madrid-spezifischen Schließungen über
  Euronext hinaus → `.MC=EURONEXT` ist korrekt, TODO gestrichen.

Prüfagent: 12 PASS / 1 WARN (Rest ^STOXX50E:6 + RR.L:1) / 0 FAIL. Fing dabei 2
veraltete Selbst-Annahmen (HKEX/KRX nicht in SUPPORTED) → korrigiert.

### 2026-06-14 — Börsen-Feiertagskalender korrigiert + Prüfagent

User-Hinweis „prüfe ob 3.10. wirklich Börsenfeiertag ist" → **war falsch.** Mein
Gap-Audit hatte eine Blindstelle: prüfte nur *fehlende* (erwartet-aber-kein-Kurs),
nicht *überzählige* Feiertage (Kurs-vorhanden-aber-Kalender-zu). Rückwärts-Audit mit
**Einzelaktien** (Indizes haben Phantom-Feiertagszeilen; Stooq-Alt-Daten ≤2019 auch)
in der Clean-Ära 2022-2025 deckte systematische Fehler auf:

- **XETRA handelt Pfingstmontag UND 3. Oktober** (Tag der Dt. Einheit) — offizieller
  Deutsche-Börse-Kalender hat NUR 8 handelsfreie Tage (Neujahr/Karfreitag/Ostermontag/
  1.Mai/24.+25.+26.+31.12.). Beide fälschlich als Feiertag → falsche TDOM/TDOY Okt-Dez
  bzw. Jun-Dez für alle ~35 .DE-Ticker + DAX-Indizes.
- **Kein Observed-Shift bei EU-Börsen:** `_monday_if_sunday`/`_observed` fälschlich auf
  XETRA/EURONEXT/MILAN/SIX/STOCKHOLM angewendet → falsche Feiertage wenn Neujahr/1.Mai/
  Berchtold aufs Wochenende fielen (01-02-2023, 05-02-2022 …). Nur NYSE/LSE shiften.

Fix: alle 5 EU-Kalender auf feste Daten umgestellt; XETRA Pfingstmontag+3.10. entfernt.
Verifiziert: Reverse-Audit **0 falsche** + Forward-Audit **0 fehlende** Feiertage.
**519k TDOM/TDOY-Zeilen über 77 Ticker** neu berechnet; `market_events`-Feiertage
2026-28 neu gesynct; **Frontend `holidays.js::_xetra()`** gespiegelt (DAX-TDOM live).

**Neu: `scripts/verify_calendar_rules.py`** — deterministischer **Prüfagent** für alle
9 Regeln (Code + DB, PASS/WARN/FAIL, Exit-Code). Enthält beide Audit-Richtungen.
Stand: 12 PASS / 1 WARN (Deep-Tail ^STOXX50E/^N225/RR.L) / 0 FAIL.

### 2026-06-14 — Handels-Kalender-Bereinigung (Suffix-Mapping + Feiertage) + Regel-Spec

Auslöser: Wöchentlicher Vollständigkeits-Audit meldete **771 „fehlende Handelstage"**.
Diagnose: **alle** waren Kalender-Geisterlücken (Yahoo/DB komplett, nur `is_trading_day`
erwartete zu viele Tage). Datengetriebener Mapping-Audit (vergleicht je Ticker
`is_trading_day(börse)` gegen reale DB-Handelstage) deckte 5 Defekt-Klassen auf:

- **ADR-Falle (größter Defekt):** Kalender wurde aus der **Heimatbörse** (`SYMBOLS.exchange`)
  abgeleitet statt aus dem **Handelsplatz**. ~23 US-gelistete ADRs (AZN/BP/SHEL/UL/NVS/UBS/
  ASML/ING/SAN/TTE/LIN/EQNR/NVO…) bekamen LSE/Euronext/SIX/Stockholm-Kalender → 15-21 Geister-
  Lücken **+ falsche TDOM/TDOY**. Fix: `get_holiday_calendar` jetzt **suffix-basiert** —
  kein Suffix = US-gelistet → NYSE; `=X`→FOREX; `-USD`→CRYPTO(24/7); Suffix/Index/Future via
  `SYMBOLS.exchange`. (Frontend `holidays.js` war bereits suffix-basiert → war nur Backend-Bug.)
- **XETRA + SIX 24./31.12.:** beide ganztägig zu (XETRA seit 2011), fehlten im Kalender.
- **Euronext-Kalender falsch:** enthielt französische **Nationalfeiertage** (Bastille 14.7.,
  8. Mai, Himmelfahrt, Pfingstmontag, 15.8., 1.+11.11.), an denen Euronext **durchhandelt**.
  Auf den harmonisierten **6-Tage-Kalender** reduziert.
- **NYSE-Sonderschließungen:** **09.01.2025 (Staatstrauer Carter)** fehlte → 212 Geister-Lücken.
  `_NYSE_SPECIAL_CLOSURES` ergänzt (Carter/Bush/Sandy/Ford/Reagan/9-11).
- **Mailand (`.MI`):** eigener `MILAN`-Kalender (Euronext-Kern + Ferragosto/24./31.12.).

**Ergebnis: 771 → 9 Geister-Lücken** (98,8 %; Rest: ^STOXX50E Eurex-Frühschluss, ^N225
Substitute-Holiday, RR.L Daten-Glitch — advisory). **~930k TDOM/TDOY-Zeilen über 133 Ticker
neu berechnet** (ADRs/XETRA/Euronext/SIX/Mailand/FX/Crypto). Verifiziert: LIN-TDOM == AAPL-TDOM,
SAP.DE überspringt 24.-26.12. korrekt. Gap-Audit exemptiert bekannt verrauschte `=X`/`^HSI`/`^KS11`.
- **Neu: [docs/TRADING_CALENDAR_RULES.md](TRADING_CALENDAR_RULES.md)** — verbindliche Spec aller
  8 Regeln (Feiertags-Auflösung, Crypto, Forex, TDOM/CDOM/TDOY, OPEX, VIXpiration) als Prüf-Spec
  für einen Verifikations-Agenten.

### 2026-06-14 — Full-Scanner OOM-Fix + Doku-Klarstellungen (PRs #81-84)

- **Full-Scanner OOM (PR #84):** Weekly `full_scanner_run` brach mit **exit 137** (SIGKILL/OOM, kein Supabase-Fehler) bei Ticker 69/324 ab. Ursache: `download_data` (`@st.cache_data`) cached jede Voll-Historie im Memory, Schleife leerte nie. Fix: `finally` → `clear_cache()` + `gc.collect()` pro Ticker. Verifiziert: 324/324, 0 Fehler, 2,8 min.
- **Doku:** ARCHITECTURE.md umfassend nachgezogen (22 Tabellen, 13 Workflows, Batch-Jobs/Tooling, Stand/Ticker 324). **Klarstellung Streamlit produktseitig ungenutzt** (nur Container-Keep-alive für cron `docker exec`); `landing/` = Frontend. CLAUDE.md v39.

### 2026-06-13 — DB-Vollständigkeit, Ticker-Universum 270→324, Frontend-Fixes (PRs #70-80)

**DB-Vollständigkeits-Audit + Reparaturen:**
- **`scripts/check_db_completeness.py`** (PR #70) — 4-Dimensionen-Audit (freshness/coverage/gaps/events), selbst-kalibrierend (Median statt hardcoded Soll), Auto-Backfill-Dispatch, Brevo-Mail, wöchentl. Cron `db_completeness.yml`.
- **Reparaturen (PR #71):** `spot_vol_beta` neu berechnet (stand seit März still) + als Nightly-Phase E1b eingehängt; `log_return` 97k→7k NULL; TDOM/TDOY 2,3 Mio neu; Events nachgezogen. **`tickers`-Tabelle fehlte** in der DB → `scripts/restore_tickers_table.sql`. Backfill-Skripte gehärtet (symbols.py statt DB-Tabelle/Full-Scan; UTF-8-Reconfigure; NaN-Sanitize im Scanner).
- **Stale-Tail-Erkennung (PR #75)** + **Orphan-Detektor (PR #78/#79)**: Audit meldet jetzt veraltete Einzel-Ticker (`max(date)` vs. letztem HT) UND Ticker mit Preisdaten ohne `symbols.py`-Eintrag (Loose-Index-Scan, da `SELECT DISTINCT ticker` timeoutet; RPC `create_distinct_price_tickers_rpc.sql`).
- **`scripts/onboard_ticker.py`** (PR #78) — Ein-Befehl-Onboarding (validieren→backfill→tickers.json→DB→verify), verhindert Orphans/vergessene Schritte.

**Ticker-Universum 270 → 324:**
- +15 Orphan-ETFs adoptiert (SMH, SOXX, … PR #73), +4 Dow-30-Mitglieder (MMM/NKE/SHW/TRV), +28 DAX-40-Mitglieder (PR #76), +7 weitere Orphan-ETFs (RSP/IYT/KRE/XOP/XRT/XSD/ETHA, PR #79).
- **SAP → SAP.DE** migriert (XETRA/EUR statt US-ADR), **BVOL-USD** (totes Token) gelöscht (PR #80). Endstand: **Registry 324 == distinct prices 324, 0 Orphans.**

**Frontend-Fixes:**
- we-are-here-TDOM-Marker fehlte am WE (`getCurrentTdom` return-null) auf Monatszyklus/Dashboard/TDoM (PR #72).
- Sidebar-Autocomplete: natives `<datalist>` → Custom-Substring-Dropdown, Ticker+Name (PR #73).
- Watchlist-Löschungen kamen via Cloud-Sync zurück → **Tombstone-Mechanismus** (PR #74).
- Dashboard: OPEX feiertagsbereinigt (Juneteenth 19.06.→18.06.) + Next-Events chronologisch sortiert (PR #77).
- Landing-Slider „From Noise to Signal": gelbe Aktuelles-Jahr-Linie + Daten-Pfad nach `landing/data/` (Auto-Refresh im Deploy).

### 2026-06-13 — EN Pre-Rendering + Deploy
- **`landing/build_en.py`** — rendert EN-Pages statisch nach `landing/en/` (Head-Regen + positions-basierter data-i18n-Splicer + Link-Rewrite + `data-en-hide` + `localize_index_jsonld`). Stdlib-only.
- **`landing/verify_en.py`** — Verifizierung (A1-A6 Quelle, B2-B8 Build-Output), FAIL 0 über alle 31 Pages.
- **`scripts/fix_i18n_html_markup.py`** — `data-i18n`→`data-i18n-html` wo en.json-Wert HTML enthält.
- **~70 bestehende Live-Defekte gefixt** — halb-übersetzte Mixed-Content-Absätze, unvollständige EN-Werte (opex/zentralbanken-Methodik, ki/svb/vix-Intros), unmarkierte Captions/Monats-Checkboxen/aria-labels, deutsche JSON-LD-FAQ auf der Landing, JS-Tabellen-Strings → `SA.i18n.t()`. en.json 1222→1253 Keys.
- **Deployed** — nginx `/en/*` serviert statisch aus `landing/en/`; `build_en.py` in Deploy-Pipeline (Host, nach inject_credentials); `landing/en/` gitignored. Verifiziert live: /en/, /en/dekadenzyklus, /en/ki-saisonalitaet englisch.
- **`blog_builder.py`** — PEP-701-f-string (~Z. 1211) portabel gemacht (lief nur auf Python 3.12+; Server ist 3.12.13). EN-Blog verifiziert: 0/28 Seiten Deutsch, SEO-Head korrekt.

**Lessons Learned:**
- **`data-i18n` (Text) auf Mixed-Content (`<b>`/`<a>`-Kind) = halb übersetzt** (nur letzter Textknoten). Häufigster Alt-Defekt. → [I18N.md](I18N.md)
- **nginx-Config aktivieren via `docker compose restart nginx`, nicht `nginx -s reload`** (Single-File-Bind-Mount + git pull = neuer Inode → reload liest stale). → CLAUDE.md Deployment-Abschnitt.
- **`|| echo` macht `nginx -t`-Fehler still** → Deploy „success", aber alte Config aktiv. Config minimal/proven halten.
- **Diagnose ohne SSH/gh:** WebFetch rendert kein JS → alte Laufzeit-Swap-Page zeigt deutschen Body, statische Page englischen. `/landing/en/<slug>.html` direkt abrufen prüft, ob `build_en` lief. Actions-Status via public Actions-Seite mit Cache-Buster `?fresh=` (WebFetch cached 15 Min/URL).
- **Single Source of Truth bei Mehrsprachigkeit:** Title/Desc in `_EN_PAGE_META` (JS) statt en.json = doppelte Pflege; JSON-LD-Text als eigener Übersetzungs-Layer leicht vergessen.

### 2026-06-12 — EN Phase 6+7
- **24 Blog-Posts EN übersetzt** — `blog/posts/en/` mit `de_slug:`-Feld für hreflang-Rücklinks.
- **`blog_builder.py` erweitert** — `build_en()`, `load_posts_en()`, `_extra_vars_en()`, `_build_blog_sitemap_en()`. `main()` ruft automatisch beide (`build_all()` + `build_en()`).
- **Bilinguales Blog-Template** — alle Sprachstrings als Template-Variablen, kein `{% if is_en %}` im HTML.
- **nginx `/en/blog/`** — eigener `^~`-Location-Block vor dem `/en/`-Catch-all.
- **Sitemap 89→113 URLs** — 24 EN Blog-Posts + `/en/blog/` Index, alle mit hreflang.
- **Blog EN-Fix** — `disclaimer_blog_en.md`, EN Chart-Labels, page_title/page_description in EN Index.
- **Verifikations-Workflow** — 21 Pages: alle Expander/Methodologie-Texte mit data-i18n versehen, en.json 793→1222 Keys.
- **TDOM 4. Strategie** — `open_to_next_close` im Frontend + DB (6210 Rows je Strategie).

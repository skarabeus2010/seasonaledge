# CLAUDE.md — SeasonAlpha

> Version 56.0 | 2026-09-10 | **Options-Review abgeschlossen (3 Runden, 26 Befunde, 22 behoben — Detail: [docs/OPTIONS.md](docs/OPTIONS.md))** — **Datenintegrität:** `--overwrite` löschte bei leerer API-Antwort eine ganze Ticker-Historie (Purge wurde vor den frühen `return`s committet); `write_text()` ist nicht atomar, der Supervisor stoppt den Container aber zu einem FESTEN Zeitpunkt → neues **`shared/atomic_json.py`** (Temp-Datei **im Zielverzeichnis**, flush+fsync, `os.replace`). **Crons:** alle drei Options-Workflows verschluckten Fehler (`| tail` ohne `pipefail` + finaler `echo` als Exit-Code); `gex_snapshot` rechnete bei gescheitertem Snapshot auf ALTER `gex_summary.json` weiter → harter Abbruch. **Rechenfehler:** ATM-Fallback aus fremder Expiry, `_atm_iv` ohne Delta-Toleranz, totes IV-Band 4,0–5,0, Walls ohne Vorzeichenprüfung, Max Pain bei leerer OI, IV-Surface klemmte still, ΔOI vermischte Roll/Verfall, Frontend zeigte 20 Tage alte Punkte als aktuell. **Bestätigt korrekt:** Put-Call-Parität (2,3e-13), GEX/Vanna/Charm gegen Finite-Differenzen inkl. q≠0 (2,5e-9), `q=0` und `R` quantifiziert unkritisch. **Lessons:** destruktive Operationen nur auf lokaler Kopie, Commit erst nach Erfolg · Verify-Gates müssen die **Zielgröße** prüfen (Mittelung über rohe IV verdeckte einen Vorzeichenwechsel) · **Backend/Frontend-Zwillinge driften** (zwei BS-Implementierungen mit `R=0.045` vs. `0.04`) · Doku-Drift kostet Sessions (SSH-Key-Name, `ai_models.py` als „gelöscht" geführt obwohl von `ki_score.py` importiert). **Neu: systematischer Review-Plan in 7 Wellen** (siehe TODO) — Optionen = Welle 0, erledigt.
> Version 55.2 | 2026-09-10 | **Betrieb langlaufender Backfills (PRs #261-263)** - `scripts/backfill_supervisor.sh` + `scripts/backfill_skew_report.py`. **Problem:** ein Backfill ueber das Universum laeuft ~18 h und ueberlappt mit dem 23:00-UTC-Cron; beide schreiben dieselbe `options_skew_history.json`, und der Backfill schreibt nach JEDEM Ticker die im Speicher gehaltene Struktur zurueck -> **Lost Update**. **Loesung:** Supervisor pausiert den Container 22:50-00:10 UTC, setzt danach fort (ohne `--overwrite` gratis: fertige Ticker werden uebersprungen), mailt alle 3 h einen Zwischenstand und am Ende den Bericht. Der Bericht meldet **nicht** "exit 0", sondern **wie viele Ticker im Radar erscheinen** (mind. `MIN_NORM` normierte Punkte) - ein Lauf kann sauber durchlaufen und trotzdem kaum Abdeckung bringen. Laeuft als transiente **systemd-Unit** -> unabhaengig von SSH-Sitzung und Entwickler-PC. **Lessons:** `pkill -f <supervisor>` killt die **eigene Shell** (das Muster steht in der eigenen Kommandozeile) -> `systemctl stop`; HHMM-Vergleiche in bash brauchen **`10#`** (sonst Oktal-Deutung von `0010`), und die Fensterlogik gehoert **vor** dem Ausrollen trocken durchgespielt - mein erster Entwurf legte das Pausenfenster faelschlich hinter statt vor den kollidierenden Cron.
> Version 55.1 | 2026-09-10 | **Code-Review der Options-Arbeit (PR #258, Detail: [docs/OPTIONS.md](docs/OPTIONS.md#code-review-2026-09-10-prs-248258))** — 11 Befunde, **8 behoben**: `--vol-pctl`-Default stand im Backfill auf 0.0 während der Live-Pfad fest 0.5 filtert (der geplante 2-J-Lauf ohne Flag hätte die Reihe wieder gemischt); `spot_own` fiel auf den `/prev`-Spot zurück, vor dem der eigene Kommentar warnt; `cm`-Zeilen ohne `iv_atm` liessen das Frontend auf die Näherung zurückfallen, die den Quadranten auf die Antidiagonale kollabiert; `dte` wurde gegen `date.today()` statt gegen die Session gerechnet; `_fix_session_dates` liess einen **nicht** normierten Live-Punkt einen `cm`-Punkt verdrängen; CM-Parameter + `cm_interp` lagen als Kopie in beiden Skripten; **`verify_skew_iv.py` importierte BS aus dem stillgelegten `backfill_skew_history.py`** und zertifizierte damit eine dritte, produktiv nicht laufende Engine; History-Zeile mischte CM-IVs mit Front-Monats-VRP. **3 bewusst offen** (mit Begründung dokumentiert): `_leg_own` vs. `_leg_ivs` nutzen unterschiedliche Strike-Grundmengen; zwei Darstellungsfragen (Tabelle Front-Monat neben normiertem Rank, `renderSkewHist` ungefiltert). **Lesson:** nach einer Vereinheitlichung gezielt nach **verbliebenen Kopien und Defaults** suchen — Konstanten und CLI-Defaults driften genauso wie Code.
> Version 55.0 | 2026-09-10 | **Options-Skew abgeschlossen + verifiziert (Detail: [docs/OPTIONS.md](docs/OPTIONS.md), PRs #248-256)** — **Abnahme grün:** 0 Zeta-Vorzeichenwechsel, mittlere Abweichung **0,24 pts** (vorher 0,88), max 0,62 (vorher 1,30). Percentile des Live-Punkts SPY 5 % · QQQ 36 % · SMH 57 % · NVDA 72 % (vorher 31/80/**97**/**99**) → das methodische Klumpen am oberen Rand ist weg. **1-J-Backfill** über 53 Ticker (+6469 Pkt) + 6 neue AI-Infra-Ticker (+750 Pkt, 28-116 normierte Punkte je Ticker). **`daten-auditor` PASS** auf allen 5 Punkten (366 Preis-Ticker == 366 in symbols.py, SMCI-Orphan behoben). **`frontend-qa`**: /skew + /flows 0 P0; drei P1 behoben — fehlender `skew.view_lbl` (unübersetztes „Darstellung" auf /en/skew), Anbietername in `of.pc_note`, und **`cache:'no-store'` → `no-cache`**. **nginx-gzip für `/landing/` aktiviert** (fehlte komplett): `options_skew_history.json` 2.649.629 → **273.669 B** (Faktor 9,7) — zusammen mit `no-cache` die Ursache des „/flows hängt beim Laden". **Lessons:** Backfill **nach** dem Live-Lauf überschreibt per Dedup den Live-Punkt desselben Tages → `--verify` verliert seine Referenz (Backfill möglichst VOR dem ersten Live-Lauf); `no-store` nicht einfach streichen (nginx `max-age=86400` → bis zu tagesalte Daten) sondern `no-cache`; `docker exec` lässt sich über SSH **nicht** detachen → Audits gezielt per `--ticker` oder mit ≥10 min Timeout.
> Version 54.0 | 2026-09-09 | **Skew-Ranking auf EINE Messmethode (Detail: [docs/OPTIONS.md](docs/OPTIONS.md), PRs #248-252)** — **Ursache gefunden, warum die Percentile unbrauchbar waren:** die Historie bestand zu >99 % aus BS-rekonstruierten Backfill-Punkten, der tägliche Live-Punkt kam aber mit der fertigen **Provider-IV** dazu. Versatz im Zeta **0,84–1,30 pts**, bei NVDA **so groß wie der gesamte Interquartilsabstand** → der Live-Punkt landete methodisch im **99. Percentil** (SMH 97.). **Fix:** der Live-Lauf invertiert die IV für die Historie **selbst** (`_own_cands`/`_leg_own`), mit gleicher Bisektion, gleichem Volumen-Perzentilfilter (0,5) und **gleicher Spot-Quelle** (unsere Kursreihe, nicht Massives `/prev`); BS-Mathematik jetzt zentral in **`shared/black_scholes.py`** (kein Drift mehr). Kein Rückfall auf Provider-IV — sonst kehrt die Mischung zurück. **Angezeigte** Werte bleiben Provider-IV. Außerdem: **konstante 30-Tage-Laufzeit** live wie im Backfill (`_skew_cm`/`_cm_interp`), Frontend rankt nur `cm`/`cm_extrap` mit `MIN_NORM=20` (`_normHist`). **1-Jahres-Backfill über 53 Ticker** gelaufen (+6469 Punkte; IEF/HYG zu dünn → fallen unter die Schwelle). **Datenanbieter aus allen user-sichtbaren Texten entfernt.** Neue AI-Infra-Ticker (SMCI/VRT/IREN/APLD/CRWV/NBIS) in symbols.py + Universum (SMCI war Orphan). **Lessons:** Versatz **relativ zur Streuung** bewerten, nicht absolut („0,88 pts klingt klein" verdeckte ein 99.-Percentil-Artefakt); Verify-Gate braucht eine Referenz **derselben Bauart**; SSH-Key-Name wechselt je Maschine → **immer `ls ~/.ssh/` zuerst**.
> Version 53.0 | 2026-09-08 | **Skew-Historie aus Massive rekonstruiert + Zeta-Methodik (Detail: [docs/OPTIONS.md](docs/OPTIONS.md))** — **Zeta nach SpotGamma-Definition** (`call_zeta_pts`/`put_zeta_pts` = OTM-IV − ATM-IV je Seite unabhängig) in `compute_options_skew.py` + Call-/Put-Skew-Modus im Vol-Regime-Radar. **Massive ist die EINZIGE Options-Datenquelle** — marketdata.app wurde nur evaluiert, **nie produktiv genutzt**. **Neuer Backfill `backfill_skew_massive.py`** (`backfill_skew_history.py` = alter marketdata-Pfad, stillgelegt): BS-Inversion aus Massive-Preisen, weil IV/Greeks dort **nur im Snapshot** stehen (Quotes = 403). **Nav „Optionen" → „Flows"** + Glossar/Q&A mit 16 Begriffen auf `/flows` (DE+EN). **Homepage-Nav hatte seit v51 gar kein Options-Dropdown** (eigene, nie mitgezogene Kopie) — jetzt mit `components/nav.html` synchronisiert. **Lessons:** SSH-Key heißt **`flatradar`** (nicht `mietwatch`) — vor dem Aufgeben `ls ~/.ssh/` prüfen; **kein Massive-MCP**, Massive läuft über REST (ein Backfill ginge über MCP ohnehin nicht); Langläufer in einen **eigenen Container** (ein `git push` → Auto-Deploy → `docker compose up -d --build app` killt jeden laufenden `docker exec`); Verify-Gates müssen die **Zielgröße** prüfen (Mittelung über rohe IV meldete „gut", während MUs `call_zeta` das Vorzeichen drehte); History stempelte **Kalendertage** statt Handelstage (Cron läuft auch Sa/So/feiertags). **Offene TODOs in OPTIONS.md** (Frontend-Filter auf `cm`/`cm_extrap`, Kalibrierung Rekonstruktion↔Provider, BE zu dünn)
> Version 52.0 | 2026-09-08 | **Options-Integration + Fixes (Detail: [docs/OPTIONS.md](docs/OPTIONS.md), PRs #235-245)** — **Equity Put/Call Ratio** (`/options-flow`, Vol+OI, Equity vs. Index, forward-History `__PCR`; CBOE-Ratio ist nicht mehr gratis). **Skew + Skew-Percentile je Titel im Morning Briefing** (eigene „Skew"-Spalte, `skew_map()`/`skew_pctl_map()` in `daily_report.py`) + **Skew-Rank/Pctl-Spalte auf `/skew`**. **Health-Check** prüft alle 5 Options-Dateien. **Realized-Vol = CBOE-Formel** (war korrekt) + **VRP-Horizont-Fix**: 30-HT→**21 HT (1 Monat)**, passend zur 30d-IV (SPY-VRP +0,6→+4,2). **Lessons:** Options-Seiten-HTML war `max-age=3600` → „ich sehe nichts" trotz Deploy → auf **`must-revalidate`** (immer frisch); **Gmail rendert ⌥-Symbol nicht** → klare Text-Labels in Mails; `.env`-Änderung braucht `docker compose up -d --force-recreate app`; mehrere schwere In-Container-Läufe gleichzeitig → Thrash (`pkill` fehlt im Container → App-Container neustarten).
> Version 51.0 | 2026-09-06 | **Options-Plattform (kanonisch: [docs/OPTIONS.md](docs/OPTIONS.md), PRs #214-233)** — Nav-Hub „Optionen": **`/skew`** (Vol-Regime-Radar RR-Rank×IV-Rank/**Percentile-Umschalter**, Kategorie-Filter, Spread-Ecken, Heatmap-Tabelle, Vol-Trigger-Panel; Klick-Ticker→Skew-Verlauf+Term-Structure+**Volatility Smile** IV×Delta), **`/iv-surface`** (Moneyness×Laufzeit-Heatmap), **`/key-levels`** (**Max Pain**+OI-Walls), **`/options-flow`** (**ΔOI-Flow** forward-akku + **0DTE**), **`/dealer-positioning`** (+**Charm/Vanna-Profile**). **⚡ Datenquelle marketdata→Massive.com (=Polygon.io)**: Flatrate-Voll-Chain-Snapshot (Greeks/IV/OI, `MASSIVE_API_KEY`, Options-Starter $29) ersetzt per-Kontrakt-Bepreisung → Voll-Chain-GEX bezahlbar. **`shared/options_universe.py`** = 156 US-Ticker/9 Themen. Metriken: 25Δ-Skew@30/@90+**NE-Skew**, Term-Structure, VRP, Butterfly, P/C, Expected-Move, Correlation. Methodik SpotGamma-verifiziert. Crons: skew/iv-surface/flow 23:00, gex/key-levels 22:15; Health-Check prüft Options-Frische. Blog DE+EN „Vol-Regime-Radar" (Risk Reversal × IV Rank/Percentile, 2 Quadranten-Charts). **Lessons:** `.env`-Änderung → `docker compose up -d --force-recreate app` (env_file beim Start); Spot via `/v2/aggs/prev` + Strike-Filter ±30% (156-Lauf 48→15min); stdout block-buffert→`flush`; nicht mehrere Heavy-Läufe parallel (Host 3,8GB); Massive-Historie=nur Preise→marketdata-BS-Reko bleibt für Backfill (`verify_skew_iv.py` <0,4pt); Blog-Bild `<slug>/x.png`→`/blog/<slug>/images/<slug>/x.png`=200. **Offene TODOs in OPTIONS.md** (ΔOI baut auf, Sidebar, GEX-Universum breiter, Options-Scanner, marketdata-Abo-Klärung, Blog-Distribution)
> Version 50.0 | 2026-09-06 | **`/skew` → Vol-Cockpit + Nav-IA „Optionen"** (PRs #208-213): Radar „Vol-Regime-Radar" (grün→rot-SVG-Verlauf, Rand-Labels Expensive/Cheap/Bullish/Bearish, Cost+Direction+Spread je Feld, **RR>50=downside/bearish**), **Rank↔Percentile-Umschalter**, Klick-Ticker→Skew-Verlauf (Tabelle+Radar). **6 IV-Metriken** (`compute_options_skew.py`): IV-Term-Structure (Contango/Backwardation), VRP (IV−realized), 25Δ-Butterfly, P/C-IV-Ratio, 90d-Skew, IV-Rank/Pctl. **CBOE Implied Correlation** `^COR1M/3M/30D` (gratis Yahoo, nur letzter Wert → Forward-Akku `__CORR`). **Vol-Trigger-Panel** (Zero-Gamma-Flip aus `gex_summary.json`, kein neuer Fetch — SPY sitzt aktuell AUF dem Trigger/short-Gamma). **Nav:** neuer Top-Level „Optionen" (Skew/Dealer/Flows/Spot-Vol-Beta) aus „Mehr" gelöst. **Lessons:** marketdata rate-limitet Bursts → **Throttle 0.4s + 429-Backoff** Pflicht (8 Req/Ticker); Voll-Chain-GEX = ~4400 Credits/Ticker unbezahlbar → GEX bleibt Yahoo-EOD; `verify_skew_iv.py` (BS-IV vs marketdata <0,4pt). **Full-Scanner OOM (exit 137)** = transienter **Host**-Speicherdruck (3,8 GB, mehrere Container), KEIN Code-Leak (30-Ticker-Test sauber, Per-Ticker-`clear_cache`+`gc` ok) → `--resume`-Rerun. Agenten: options-flow-analyst (Vol-Trigger), market-flows-scout (SpotGamma-Review: Top-3 = Scanner/Compass/Key-Levels; HIRO/Tape/Synthetic-OI datengesperrt)
> Version 49.0 | 2026-09-06 | **Eigene `/skew`-Seite (DE+EN)** — Optionen-Skew-Radar unter „Mehr": Standard-Header+Satzzeile → Vol-Quadrant (Rank-Fenster + Strategie-Felder) → 25Δ-Skew-Tabelle → CBOE-SKEW/VIX-Kontext + FAQPage; bilingual (`data-i18n(-html)` + `en.json` + `_EN_PAGE_META`→build_en `/en/skew`, verify_en FAIL 0; dyn. JS-Strings via `SA.i18n.t`), Nav-Link DE+EN, nginx-Route `location = /skew`. Reuse der flows-Panel-G-Logik (`renderSkewQuad`/`renderSkew`) · **Vol-Quadrant (`/flows` Panel G)** — der 28-Linien-Skew-Verlauf war unlesbar → **Quadrant**: X=Risk-Reversal-Rank (25ΔCall−Put), Y=IV-Rank, je Ticker als **Perzentil in eigener 2-J-Historie**, 50%-Fadenkreuz + halbtransparente **Strategie-Wasserzeichen** (oben=Prämie verkaufen/unten=kaufen, Seite folgt Skew: oben-links Sell Put Spread · oben-rechts Sell Call Spread · unten-links Buy Put Spread · unten-rechts Buy Call Spread; reine Struktur-Beispiele, kein Signal) · **BS-Skew-Rekonstruktion** (`scripts/backfill_skew_history.py`): marketdata-Historie hat nur Preise (kein IV/Greeks), aber 1 Credit/Chain → IV je Kontrakt selbst per Black-Scholes-Bisektion invertiert, 25Δ gepickt; echte Handelstage, **inkrementell pro Ticker** geschrieben (überlebt Abbruch), `socket.setdefaulttimeout(20)`. `options_skew_history.json` gitignored → per SSH auf Server, nicht committen · Lessons: **stdout durch `... | grep` block-buffert** (kein Fortschritt sichtbar, wirkt wie Hänger) → `flush=True` + nicht durch grep pipen; **Datei-Redirect im Background-Command** landet in eigener Logdatei, nicht der Task-Output-Datei
> Version 48.0 | 2026-09-05 | **Ticker-Universum 324→358** (34 Energie-/Strom-/Uran-/Solar-Werte: Smartgrid/Versorger/PowerGen/Uran/Solar; 4 sehr dünne weggelassen; `S92.DE`/`NDX1.DE`→XETRA, `NEL.OL`→Oslo/SE-Proxy) · **`/index-effekt`** (S&P-500-Index-Inklusion-Effekt-Studie: 36 Events, gemittelter Pfad −20…+20 HT um Ankündigung, +5,8% bei T+20 / Peak +7,8% um Wirksamkeitstag, 72% positiv; `scripts/build_index_effect.py` + `index_effect_{events,study}.json` + `flows.html`-Muster; BE=Bloom-Energy Live-Event) · **KI-Duktus raus** (Blog+Seiten: „ehrlich/honest"-Selbstbeteuerung + „YMYL"-Jargon → direkte Formulierungen; blogger-Anti-Slop-Regel) · **nginx/mietwatch entkoppelt** (conf.d-Override statt geteilter nginx.conf) · Lessons Learned (siehe Regel-Sektionen): **SSH aus Claude-Env GEHT** via `~/.ssh/mietwatch` (gleicher VPS wie mietwatch.de); **lokale `.env` hat service_role-Key** (nicht Anon!) → lokale DB-Writes möglich; Cloud-Timer (RemoteTrigger `run_once_at`) kann unbeaufsichtigt **nicht git-pushen** (Permission-Gate) → manuell nachholen
> Version 47.0 | 2026-08-04 | **Vibe-Trading Alpha-Zoo → 3 neue Indikator-Filter** (`indicators.js`: ML-Regime Percentil-Clustering, Carhart Momentum 12M-1M, Jegadeesh StRev 21d) · **SPY Down-Month ToM Reversal** (Backtest 15J: Sharpe 0.21→0.34, WR 68→72%, PF 1.80→2.39; `calc_downmonth_tom` in `strategy-compute.js`, SA.STRATEGIES `monat`-Kategorie, Dashboard-Signal) · **Trifecta-Chart-Bug** (x-Achse nutzte Handelstag-Zähler statt Kalendertag → Chart endete scheinbar Ende Mai; Fix: `lastCalDay` aus Datum des letzten Handelstags) · ~~**FlashAlpha MCP**~~ — **für dieses Projekt NICHT aktiv** (geprüft 2026-09-08: `claude mcp get flashalpha` findet ihn nicht; der Eintrag in `~/.claude.json` hängt an einem anderen Projektpfad). **Einen Massive-MCP gibt es nicht** — Massive läuft über die REST-API mit `MASSIVE_API_KEY`, siehe `compute_options_skew.py`. Ein Backfill ginge ohnehin nicht über MCP: Tools werden einzeln vom Modell aufgerufen, ein Massenlauf braucht Tausende Abrufe in einer Server-Schleife. · Blog DE+EN: SPY Turn-of-Month Down-Monat Reversal Backtest
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

- **Shared (`shared/`)** — Kern: `yahoo_downloader` (Stooq-Fallback, einziger Cache), `data` (Supabase-First), `charts` (`apply_se_theme`), `ki_score`, `tdom_analysis`, `anomaly_engine`, `significance_gauge` (key_prefix!), `footer`, `i18n`. ⚠️ Gelöscht (ML-Pipeline KW16): `mstl_decomposition`, `chronos_forecast`, `neural_prophet_forecast`. **`ai_models.py` lebt weiter** (Korrektur 2026-09-10 — stand hier fälschlich als gelöscht): 447 Zeilen, importiert von `ki_score.py` (`find_similar_years`, `forecast_seasonal`) und `outlier_manager.py` (`detect_outlier_years`). Der KI-Score hängt also daran — vor Änderungen prüfen, was das Modul wirklich tut (Review-Welle 2).
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
- **Neuen Ticker aufnehmen: NUR via `py scripts/onboard_ticker.py <T>`** (nach Eintrag in `symbols.py`; nimmt **mehrere Ticker/Aufruf**). Macht Yahoo-Validierung + Voll-Backfill + tickers.json-Regen + DB-Upsert in einem. NIEMALS nur Preise laden ohne `symbols.py`-Eintrag → sonst „Orphan" (wird weder auditiert noch refreshed, veraltet still). `symbols.py`/`get_all_tickers()` = einzige Quelle der Wahrheit; Backfill-Skripte ihre Ticker-Liste IMMER daraus speisen, nie aus DB-Tabellen (prices-Full-Scan timeoutet, `tickers`-Tabelle kann fehlen).
- **Onboarding-Praxis (KW36-Erweiterung 324→358):** In Batches à ~12 fahren (kleiner Blast-Radius, kein OOM). Lokal möglich dank service_role-Key (siehe MCP-Scope), sonst server-seitig via `docker exec`. **Nach Backfill die abgeleiteten Stats für die NEUEN Ticker gezielt nachrechnen** statt vollen Nightly: `from scripts.nightly_refresh import refresh_ticker_data; refresh_ticker_data(<NEUE_LISTE>, years_back=20, quick_mode=True)` (pro Batch `clear_cache()`+`gc.collect()`) → füllt monthly_stats/KI-Score/TDOM/TDOY. `store_scanner_results` ist **Upsert** (`on_conflict=ticker,scan_date`) → ein Subset-Lauf lässt die anderen Ticker unberührt (kein Delete-then-insert). **`tickers.json` ist git-getrackt** → nach Onboarding committen (sonst wirft `deploy`'s `git checkout -- landing/` es auf den alten Stand zurück).
- **Kalender-Suffix bei neuen Tickern prüfen:** Oslo (`NEL.OL`) IST unterstützt (`exchange:"Oslo"`→STOCKHOLM/SE-Feiertagsproxy, nutzt EQNR); `.DE`→XETRA. US-NYSE/NASDAQ teilen NYSE-Feiertage (kalendarisch unkritisch).
- **Lokal (Windows):** `py -3.14` nutzen (= Container-Version; Default-`py` ist 3.9 und scheitert an `X | None`-Syntax in shared-Modulen). Bei Skript-Läufen mit Datei-Umleitung `PYTHONUTF8=1` setzen (cp1252 crasht sonst an ✓/⚡-Prints).
- Vollständigkeit prüfen: `py scripts/check_db_completeness.py` (Freshness/Coverage/Gaps/Events + Orphan- & Stale-Tail-Erkennung; wöchentl. Cron `db_completeness.yml`). Orphan-Check braucht RPC `create_distinct_price_tickers_rpc.sql`.
- **Cron-erzeugte JSONs unter `landing/data/` NIEMALS committen.** `deploy.yml` macht vor dem Pull `git checkout -- landing/` (nötig für die In-Place-Änderungen von `inject_credentials.sh`). Getrackte Cron-Dateien werden dadurch bei **jedem** Deploy auf den committeten Stand zurückgeworfen — die Seite zeigte so tagealte, teils **invertierte** Regime-Daten (Gamma-Index +12,218 → −3,398). Diagnose-Trick: untrackte Dateien (`gex_history/*.json`) überleben, getrackte fallen zurück — die Differenz beweist den Deploy als Ursache. Seit 2026-08-13 sind die 13 betroffenen Dateien in `.gitignore`. Neue Cron-Outputs dort ebenfalls eintragen.
- **Lokal eine datengetriebene Seite testen: JSONs von der Live-Seite ziehen.** Die Cron-Outputs unter `landing/data/` sind gitignored → ein frischer Checkout hat entweder gar keine oder monatealte Reste (Stand vor dem 2026-08-13-Gitignore). Die Seite lässt sich damit nicht realistisch prüfen. Statt Fixtures zu pflegen (veralten sofort, verdoppeln die Struktur) die echten Dateien holen:
  ```bash
  for f in flows_rebalancing buyback_blackout etf_flows cot_positioning \
           volcontrol_proxy shortvol_proxy options_skew options_skew_history; do
    curl -sf -o "landing/data/$f.json" "https://seasonalpha.ai/landing/data/$f.json" \
      && echo "  ok $f" || echo "  FEHLT $f"
  done
  ```
  Danach `landing/` per `python3 -m http.server` o.ä. servieren. **Nicht committen** (siehe Regel darüber).
- **Yahoo-Options: `openInterest=0` im Vormittagsfenster (UTC).** Yahoo liefert dann die **volle** Chain mit HTTP 200, aber ohne Open Interest (geprüft 05./06./13.08., je ~08:50–10:15 UTC: SPY 4/1461 brauchbar = 0,3 %). Der OI-Filter wirft alles weg, und `analyze()` meldete früher trotzdem **Erfolg** mit einer Handvoll Kontrakten → plausibel aussehender Müll (`net-GEX −0.000 Mrd, short_gamma`). Seit 2026-08-13 verwirft `analyze()` die Chain, wenn bei ≥100 Roh-Kontrakten <5 % brauchbar sind, und `snapshot_gex.py` schreibt gar nichts, wenn <60 % der Ticker durchkommen. **Der Cron um 22:15 UTC liegt richtig** (konstant 20/20). Ad-hoc-Läufe am Vormittag sind wertlos — stattdessen `--snapshot <datum>` gegen das Archiv nutzen.
- **OOM in Full-Universe-Schleifen (exit 137 = SIGKILL, NICHT Supabase-Fehler):** `download_data` ist `@st.cache_data` → cached JEDE Voll-Historie im Memory. In Per-Ticker-Loops über alle 324 Ticker (Scanner/Backfills) IMMER `clear_cache()` (= `download_data.clear()`) **+ `gc.collect()` pro Ticker**, sonst OOM-Kill ab ~Ticker 70. Haben: `full_scanner_run` (seit 2026-06-14), `backfill_tdoy`/`backfill_ohlc` (gc). Bei neuen Full-Universe-Skripten mitdenken.
- **Supabase-Writes / MCP-Scope:** Der verbundene Supabase-MCP zeigt ein **FREMDES** Projekt (`Wohnungsbot`, separat, läuft nur auf demselben VPS) — dort NIE Writes ausführen (SeasonAlpha-Ref = `dkrebzobcwxyagximuxy`). **⚠️ Update 2026-09-05: Die lokale `.env` enthält aktuell einen `service_role`-Key (NICHT nur Anon, wie hier früher stand!)** → lokale DB-Writes sind technisch möglich (voller Schreibzugriff). Trotzdem: **keine lokalen DB-Writes ohne ausdrückliche User-Freigabe**, und Massen-/Routine-Writes weiter server-seitig. Sicherheits-TODO: User soll prüfen, ob der service_role-Key lokal gewollt ist (Leak-Risiko), ggf. rotieren. DB-Korrekturen sonst als SQL für den SeasonAlpha-SQL-Editor (`scripts/sql/*.sql`) ODER via `docker exec` auf dem Server. **tdoy/TDOY-Ground-Truth = reiner Börsenkalender (`is_trading_day` ab Jan1), NICHT ein anderer Ticker** (^GDAXI hatte 08-2026 selbst einen Glitch); Recompute (`compute_tdoy_tdom`), nie pauschaler Offset.

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
- **SSH aus der Claude-Umgebung GEHT** — **der Key-Name variiert je Maschine/Session** und wechselte schon zwischen `~/.ssh/mietwatch` und `~/.ssh/flatradar` (2026-09-08 war flatradar da, 2026-09-09 wieder mietwatch und KEIN flatradar). **Deshalb IMMER ZUERST `ls ~/.ssh/` ausführen** und den dort vorhandenen Key nehmen — NIE auf den hier notierten Namen verlassen (jede falsche Annahme kostete eine halbe Session). Beispiel: `ssh -i ~/.ssh/<vorhandener-key> -o BatchMode=yes root@178.104.75.46 "…"` (Default-`ssh` bietet den Key nicht an → `-i` explizit). Der Auto-Mode-Klassifikator kann schreibendes SSH blocken → dann `Bash(ssh -i ~/.ssh/mietwatch:*)` in `.claude/settings.local.json` allow. **NUR `/opt/seasonaledge` anfassen, nie `/opt/mietwatch`, `/opt/flatradar` (mietwatch/Wohnungsbot) — Dateien + DB.** Damit sind Server-Fixes (Git/nginx/docker) selbst machbar, nicht nur „macht der User".
- **Langlaufende Backfills NIE unbeaufsichtigt neben die Crons legen.** Backfill und `options_skew`-Cron (23:00 UTC) schreiben dieselbe `options_skew_history.json`; der Backfill haelt sie im Speicher und schreibt nach jedem Ticker die ganze Struktur zurueck -> was der Cron dazwischen anlegt, ist weg. `scripts/backfill_supervisor.sh` pausiert den Container im Cron-Fenster und mailt Zwischenstand/Abschluss (Details: [docs/OPTIONS.md](docs/OPTIONS.md)). Start als transiente systemd-Unit (`systemd-run --unit=sa-bfsup ...`), **nicht** `nohup` - und zum Beenden `systemctl stop`, denn `pkill -f <name>` trifft die eigene Shell.
- **⚠️ Geteilter VPS mit mietwatch.de — deploy-`git pull` kann STILL abbrechen:** mietwatch.de teilt denselben nginx-Container + certbot. Früher lagen mietwatch-nginx-Blöcke uncommittet in SeasonAlphas `deploy/nginx.conf` + eine Mount-Zeile in `docker-compose.yml`. Der Deploy revertet vor dem Pull nur `landing/`+`seo/output/` → sobald ein committeter Commit `nginx.conf` änderte, brach `git pull` ab (`local changes would be overwritten — Aborting`), **Deploy meldete trotzdem „success"**, Server blieb auf altem Commit (neue Seite/Route fehlte lautlos). Diagnose: `gh run view <id> --log | grep -i "overwritten\|Aborting"`. **Seit 2026-09-05 GELÖST via conf.d-Split:** mietwatch läuft über eine **untrackte `/opt/seasonaledge/docker-compose.override.yml`** (`- /opt/mietwatch/website:/app/mietwatch:ro` + `- /opt/mietwatch/nginx/mietwatch.conf:/etc/nginx/conf.d/zz-mietwatch.conf:ro`); mietwatch-Blöcke sind aus `deploy/nginx.conf`+`docker-compose.yml` raus → beide getrackten Dateien clean → kein Pull-Konflikt mehr. `zz`-Präfix wegen conf.d-Ladereihenfolge (kein `default_server` → erster `listen 80`=Catch-all=umami; mietwatch dürfte den nicht kapern). mietwatch-Backend läuft auf dem HOST (nicht Docker), nginx erreicht es via `proxy_pass http://172.18.0.1:8000/` (Gateway-IP, Netz `seasonaledge_default`). **`deploy/nginx.conf` ist NICHT im landing-Revert** → eigene Änderungen daran werden vom Deploy behalten; Mount-Änderungen brauchen `docker compose up -d nginx` (Recreate), nicht reload.
- nginx-Config minimal/proven halten: `nginx -t`-Fehler im Deploy wird per `|| echo` verschluckt (non-fatal) → fehlerhafte Config bleibt still inaktiv, alte läuft weiter. Neue Blöcke an bereits laufenden orientieren (lokal kein `nginx -t` ohne Docker).
- Reine HTML/Asset-Änderungen (kein Config): `git pull` reicht (nginx serviert aus gemountetem `./landing` ro); ggf. Browser-Hard-Refresh
- **Kein render-blockendes Dritt-`<link rel="stylesheet">` im `<head>` (Hänge-Risiko!):** ein `<script>` wartet auf noch ladende Stylesheets (CSSOM) → hängt `fonts.googleapis.com`, blockiert es `app.js` (Nav via `loadComponent`) + das Inline-`init()`/`boot()` → Seite bleibt ewig in „Lade…" (Boot-Notnagel greift NICHT, steckt im blockierten Script). „Inkognito geht manchmal" = Symptom. Google-Fonts IMMER nicht-blockierend laden: `media="print" onload="this.media='all'"` + `<noscript>`-Fallback (Fallback-Font-Stacks in `app.css`). Analog `b5ba5ce` (self-hosted JS-Vendor) — **gilt für CSS/Fonts genauso.**
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
- **Kein KI-/Claude-Duktus in Leser-Text (Blog + Seiten):** KEINE Selbst-Beteuerungen der eigenen Redlichkeit — „ehrliche Einordnung", „Ehrlichkeit zuerst", „honestly labeled", „Honesty first", „honest assessment", „we stress this deliberately / das betonen wir bewusst", „Cleanliness/Sourcing matters here". Auch **KEIN SEO-Meta-Jargon im Fließtext** („YMYL", „Your Money or Your Life"). → Grenze/Vorbehalt **direkt** benennen („Wichtig:", „Grenzen:", „klar gekennzeichnet", „Kein Signal") ohne die Selbst-Beteuerung. Faustregel: Wenn ein Satz betont, wie ehrlich/transparent/sauber man ist, statt die Sache zu sagen → streichen. (Regel steckt auch im `blogger`-Agent-Anti-Slop-Selbstcheck; 2026-09-05 aus 21 Blog-Posts + 4 Seiten entfernt.)

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

- `ARCHITECTURE.md`, `CHARTS.md`, `UI_PATTERNS.md` (Frontend/UI/Statistik-Gotchas), `TRADING_CALENDAR_RULES.md` (Kalender/TDOM/TDOY/OPEX/VIX — Prüf-Spec), `I18N.md` (EN-Lokalisierung operativ; `I18N_ANALYSIS.md` = Planung 04-2026), `SEO_ENGINE.md`, `SEO_MARKETING.md` (Living Doc), `BLOG_WORKFLOW.md`, `REFRESH_MONITORING.md`, `MIGRATION.md`, `POLYMARKET.md`, `OPTIONS.md` (**kanonische Options-Plattform-Doku**: alle Seiten `/skew`/`/iv-surface`/`/key-levels`/`/options-flow`/`/dealer-positioning`, Massive-Datenquelle, `options_universe.py`, Pipelines/Crons, GEX/Vanna/Charm/Skew/Walls-Formeln, Methodik-Abgleich, Lessons + offene Options-TODOs), `EMAIL_TESTING.md`, `YOUTUBE_STRATEGY.md` (faceless Social-Video-Kanal, Living Doc) + `YOUTUBE_DISCLAIMER.md` (YMYL-Rechtstexte, **kanonisch** — Disclaimer in Video/Caption/SEO-Hinweise einbauen!) + `SOCIAL_API_SETUP.md` (Meta IG/FB Auto-Posting-Setup); Pipeline in `scripts/video/` (`PLAN.md`/`README.md`), `CHANGELOG.md` (History/Meilensteine)
- `.claude/blog-tutorial.md` — Skill: SEO-Blog-Artikel (DE)

## TODO

### History → [docs/CHANGELOG.md](docs/CHANGELOG.md)

Meilensteine (KW15-KW24), abgeschlossene Aufgaben & Lessons Learned stehen im Changelog. (ML-Stilllegung vollständig abgeschlossen — `DROP TABLE ml_forecasts` erledigt 2026-06-16.)

### 🔴 SOFORT — Security (User-Action erforderlich)
- [ ] **OAuth Client-Secret rotieren** — in Session 2026-04-18 geleakt. Google Cloud Console → OAuth Clients → Secret neu generieren → in Supabase Auth Settings updaten
- [x] **Brevo-API-Key rotieren** — erledigt 2026-08-06: neuer Key aktiv in lokaler **und** Server-`.env` (`/opt/seasonaledge/.env`), App-Container neu gestartet, **Test-Mail kam an** (Endung neu `…WbWkUe`, alt `…lylWgh`). ⚠️ **NOCH offen (User-Dashboard-Aktion):** alten Key (`…lylWgh`) im Brevo-Dashboard **löschen** — er ist geleakt. **Lesson:** alter+neuer Brevo-Key teilen den Account-Präfix `xkeysib-5440ec2afed4…` → Keys NUR an der **Endung** unterscheiden, nie am Präfix. Brevo hat *Authorised-IPs* an → API-Test von nicht-freigegebener IP gibt 401 „unrecognised IP" (kein Key-Fehler); echter Test nur von Server-IP.
- [x] **Finnhub-API-Key revoken** — erledigt 2026-06-13 (war in Session 2026-04-30 geleakt; nicht mehr genutzt)
- [ ] **Supabase `service_role`-Key in lokaler `.env` prüfen** (Fund 2026-09-05, daten-auditor): lokale `.env` hat einen `service_role`-Key (voller Schreibzugriff, nicht nur Anon). Im Supabase-Dashboard → API-Keys prüfen, ob gewollt; ggf. rotieren (Leak-Risiko). `.env` ist gitignored.

### 🔴 SOFORT — Funktional (User-Action erforderlich)
- [x] **Daily-Newsletter DB-Migration** — erledigt (`daily_subscribers` existiert + befüllt; bestätigt durch produktiven Briefing-Lauf 2026-06-16)
- [x] **Daily-Newsletter Smoke-Test** — erledigt: Daily Morning Briefing läuft produktiv (Lauf 2026-06-16 erfolgreich)
- [x] **4. TDOM-Strategy befüllt** — alle 4 Strategien mit je 6210 Rows ✓

### Marketing (manuell)
- [ ] LinkedIn + X Posts: Blog #22-24 (Polymarket, Sell in May, DAX vs S&P) + Blog EN-Launch ankündigen
- [ ] Lead-Magnet PDF "Saisonalitäts-Report 2026"
- [ ] Google Rich Results Test für die 3 Polymarket-Blog-Posts

### `/flows`-Ladeproblem — behoben 2026-09-10
Ursache war **nicht** die Seite selbst (frontend-qa: 0 P0, HTML/JSON-LD/Fetch-Pfade alle sauber), sondern die Datenauslieferung:
`options_skew_history.json` war durch den Backfill auf **2,65 MB** gewachsen, `deploy/nginx.conf` hatte **gar keine gzip-Direktive**, und das Frontend holte die Datei mit `cache:'no-store'` — also bei **jedem** Aufruf von `/skew` und `/flows` unkomprimiert komplett neu.
- [x] **gzip für `/landing/`** aktiviert → 2.649.629 → **273.669 B** (Faktor 9,7), verifiziert per `curl -H "Accept-Encoding: gzip"`.
- [x] **`no-store` → `no-cache`** in `skew.html`/`flows.html`: revalidiert weiterhin immer (Cron-Daten können nicht veralten), erlaubt dem Server aber ein **304**. Blosses Streichen wäre falsch — nginx liefert `max-age=86400`.
- [ ] **Mittelfristig:** die Historie serverseitig auf die vom Frontend benötigten Ticker/Felder eindampfen, bevor sie weiter wächst.

### Skew-Historie / Percentile (Detail: [docs/OPTIONS.md](docs/OPTIONS.md))
**Konstante 30-Tage-Laufzeit erledigt 2026-09-09** — Percentile/Rank nur noch aus laufzeit-normierten Punkten:
- [x] **Live auf konstante 30d normiert** (`compute_options_skew.py::_skew_cm`/`_cm_interp`, identisch zum Backfill) → Live + Backfill bilden eine Skala. Angezeigte Per-Ticker-Felder bleiben Front-Monat.
- [x] **Frontend rankt nur `cm`/`cm_extrap`** (`_normHist`/`MIN_NORM=20` in `skew.html`, Radar + IV-Rank/Skew-Rk-Spalten); `single` + Alt-Einträge ohne `cm_mode` fallen raus (kein Sägezahn). Mindestschwelle ersetzt die BE-Einzelfallausnahme. Näherungs-Fallback entschärft (cm-Einträge tragen immer `call_zeta_pts`/`iv_atm`).
- [ ] **Engpass: 2-Jahres-Backfill übers Radar-Universum** (`backfill_skew_massive.py`, server-seitig, eigener Container). Mit `MIN_NORM=20` erscheinen sonst nur die wenigen gebackfillten Ticker + die mit ~20 Live-Tagen.
- [x] **Rekonstruktion ↔ Live vereinheitlicht** (2026-09-09/10): beide Seiten nutzen dieselbe BS-Inversion (`shared/black_scholes.py`) → Kalibrierung entfällt. Abnahme grün (0,24 pts, keine Vorzeichenwechsel).
- [ ] **`--verify` für SMCI/VRT/IREN/APLD/CRWV/NBIS nachholen**, sobald der nächste Cron einen Live-Punkt für sie geschrieben hat (der spätere Backfill überschrieb deren Live-Eintrag per Dedup).
- [ ] **`MIN_NORM` 20→80 nachziehen**, sobald die Historie tief genug ist; **`--vol-pctl 0.5`** an mehreren Tagen gegenprüfen (Wert stammt aus 8 Vergleichen an einem Tag).
- [ ] **CRWV `monthly_stats`** in einigen Wochen erneut prüfen (aktuell zu junge Historie seit IPO 03/2025 — kein Defekt, Zeitfrage).
- [ ] **vorbestehender `verify_en`-FAIL `nav.kalender`** auf [index]: Key existiert in `en.json`, Ursache ist die `_skipPrefixes`-Interaktion beim EN-Build (`/kalender` ist auth-gated) → „Kalender" bleibt auf der EN-Homepage deutsch. Unabhängig von der Options-Arbeit.

### 🔬 Systematischer Code-Review in Wellen

**Vorgehen je Welle:** Prompt für den externen Reviewer schreiben (Muster: die drei
Options-Prompts — konkrete Datei/Zeilen-Anker, Domänen-Invarianten statt „prüfe mal",
Liste des bereits Bestätigten gegen Doppelmeldungen, Warnung vor absehbaren
Fehlalarmen) → Befunde **am Code gegenprüfen, nicht ungeprüft umsetzen** → fixen mit
Test je Befund → committen → Lessons in die Fach-Doku.

**Drei Fragen, die in JEDER Welle gestellt werden** — sie haben im Options-Teil die
teuersten Fehler gefunden:
1. **Backend/Frontend-Zwillinge:** Dieselbe Mathematik existiert oft zweimal (Python +
   JS). Rechnen beide dasselbe? Im Options-Teil hatten zwei Black-Scholes-Kopien
   verschiedene Zinssätze, und der Frontend-Fallback machte `put_zeta = −call_zeta`.
2. **Was passiert bei fehlenden Daten?** Wird ein Wert `None`, oder rutscht ein alter
   Wert in die Rolle des aktuellen? (DUK stand 20 Tage alt im Radar.)
3. **Meldet ein Fehlschlag sich als Fehlschlag?** Oder als grüner Job mit alten Zahlen?

- [x] **Welle 0 — Optionen/Flows** (2026-09-08/10, 3 Runden, 26 Befunde, 22 behoben).

- [ ] **Welle 1 — Kern-Methodik: normalisierte Renditen + Zeitindizes.** Höchster Hebel,
  weil alles darauf steht. `shared/calculations.py` (478) · `shared/tdom_analysis.py` ·
  `scripts/compute_tdoy_tdom.py` · **`landing/js/seasonal-compute.js` (544)**.
  Leitfrage: Rechnen Backend und Frontend nachweislich dasselbe? Die Kern-Regel
  („jedes Jahr startet bei 100, tägliche Returns kumulieren, NIE `close − close[lookback]`")
  existiert in beiden Sprachen — genau die Konstellation, die im Options-Teil driftete.
  Dazu: Schaltjahre, `last_actual_day`-Filter (Perzentil/Drawdown/Heatmap dürfen nicht
  auf constant-fill rechnen), Umgang mit Kurslücken.

- [ ] **Welle 2 — KI-Score, Anomalie, Signifikanz.** Das, was der Nutzer als Signal liest.
  `shared/ki_score.py` · **`shared/ai_models.py` (447, in der Doku fälschlich als gelöscht
  geführt)** · `shared/anomaly_engine.py` (553) · `shared/significance_gauge.py` ·
  `shared/outlier_manager.py`.
  Leitfrage: Was rechnet `ai_models` wirklich, und ist der KI-Score reproduzierbar?
  4 Sub-Scores à 0–2,5 → 0–10, Schwellen ≥6,5 bullish / ≤3,5 bearish — sind die
  Schwellen empirisch belegt oder gesetzt? Anomalie-Radar misst nur 10 Tage.

- [ ] **Welle 3 — Backtest + Strategien.** `shared/backtest_engine.py` (727) ·
  `landing/js/strategy-compute.js` (746) · `landing/js/indicators.js` (435).
  Leitfrage: Look-ahead-Bias. CLAUDE.md nennt `filterMask[entryIdx-1]` als Regel —
  gilt sie überall? Dazu Quantile ohne Floor-Indexing, Transaktionskosten,
  Survivorship, und ob Walk-Forward-Ergebnisse aus dem UI reproduzierbar sind.

- [ ] **Welle 4 — Datenpipeline + Integrität.** `scripts/nightly_refresh.py` (587) ·
  `shared/yahoo_downloader.py` · `shared/data.py` · `shared/supabase_client.py` (683) ·
  `scripts/check_db_completeness.py` (832).
  Leitfrage: stille Schreibfehler. Der Free-Tier-Write-Block hat schon einmal 6 Tage
  lang lautlos nichts geschrieben. Dazu: Stooq-Fallback ändert den Datenbereich
  (^GSPC ab 1970 vs. 1950), OOM in Full-Universe-Schleifen, `log_return`-Nachrechnung.

- [ ] **Welle 5 — Börsenkalender + Handelstage.** `shared/exchange_holidays.py` (567) ·
  `landing/js/holidays.js` · `scripts/verify_calendar_rules.py` (473).
  Leitfrage: wieder ein Backend/Frontend-Zwilling. Beide implementieren Feiertage,
  Gauss-Ostern, OPEX/VIXpiration. Weichen sie ab? Der Prüfagent deckt 9 Regeln ab —
  prüft er auch das Frontend?

- [ ] **Welle 6 — Newsletter + Reports (was das Haus verlässt).**
  `shared/daily_report.py` (1483, größte Datei in `shared/`) · `shared/weekly_report.py`
  (729) · `scripts/daily_newsletter.py`.
  Leitfrage: Stimmen die Zahlen in der Mail mit denen auf der Seite überein, und was
  passiert bei fehlenden Daten — Lücke oder alter Wert? Dazu Mailgröße (Gmail kappt
  ab ~102 KB), Empfängerfilter, Abmelde-Pfad.

- [ ] **Welle 7 — Frontend-Rendering breit.** `landing/js/app.js` (743) ·
  `decade-compute.js` (635) · `polymarket.js` (604) · `watchlist.js` (427) · die ~31 Pages.
  Leitfrage: Erzählt jede Seite das, was der Code gerechnet hat? Einheiten,
  Null-Behandlung, Achsen/Tooltip-Konsistenz, Proxy-Kennzeichnung.

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
- [ ] **Index-Effekt (`/index-effekt`) ausbauen:** Nav-Link ergänzen · wöchentlicher Scanner-Cron (neue S&P-500-Additions aus S&P-DJI-PMs auto-erkennen — announcement=PM-Datum → vorwärts automatisierbar; `index_effect_events.json` erweitern + `build_index_effect.py` neu rechnen) · DAX als 2. Panel (STOXX-PMs, wenige Events) · Nasdaq-100 zurückgestellt (dünne freie Datenlage). MVP-Kern: **Ankündigungsdatum** ist das datenkritische Feld (freie CSVs haben nur Wirksam-Datum).
- [ ] **`/opt/infra`-Ebene (geteilter VPS):** nginx+certbot+docker-compose langfristig auf neutrale `/opt/infra`-Ebene ziehen (weder SeasonAlpha noch mietwatch besitzt sie), jedes Projekt liefert nur seine `conf.d/*.conf` + Doku-Root. Kein Handlungsdruck (conf.d-Override löst 90% des Schmerzes) — nächstes größeres Wartungsfenster.

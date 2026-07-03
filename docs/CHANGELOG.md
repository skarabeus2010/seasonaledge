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

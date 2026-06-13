# SEO & Marketing — SeasonAlpha

> Living Document | Stand 2026-06-13 | Ergänzt `SEO_ENGINE.md` (Generator) um Status, Checklisten, Google-Search-Console-Workflow, Monitoring. **Aktueller Fokus** siehe Block direkt unter dem Schnellstatus.

## Schnellstatus

| Bereich | Status | Datum |
|---|---|---|
| **Landing-Page Meta-Tags** | ✅ Voll ausgestattet inkl. WebSite + SearchAction JSON-LD | 2026-04-10 |
| **21 Feature-Pages Meta-Tags** | ✅ V5 via `scripts/upgrade_page_meta.py` (SEO-optimierte Titles + Breadcrumbs) | 2026-04-10 |
| **OG-Image (1200×630)** | ✅ V3 Ultra Design, via `scripts/generate_og_images.py` | 2026-04-10 |
| **Apple-Touch-Icon + PNG-Favicons** | ✅ | 2026-04-10 |
| **Hero-Titles SEO-optimiert** | ✅ 21 Pages via `scripts/optimize_page_titles.py`, alle <62 Chars mit Ziel-Keywords | 2026-04-10 |
| **Sitemap** | ✅ **50 URLs** (Landing + 22 Features inkl. neue `/scanner` + 4 Blog-Indizes + 18 Blog-Posts + 6 statische). 270 programmatische `/analyse/*` wegen Thin-Content deaktiviert | 2026-04-10 |
| **Feature #3 Saisonal-Scanner** | ✅ Live: `/scanner` mit 269/270 Tickern, Sidebar-Filter, Weekly Full-Scan Sonntag 03:00 UTC | 2026-04-10 |
| **Sitemap Auto-Discovery** | ✅ `glob('landing/pages/*.html')` in `programmatic_seo_builder.py`, neue Pages fliessen automatisch rein | 2026-04-10 |
| **robots.txt** | ✅ Sitemap referenziert, `/app/` blockiert, AI-Crawler explizit ALLOW (15 Bots) | 2026-04-10 |
| **JSON-LD Landing** | ✅ WebSite + SearchAction + SoftwareApplication + Organization (mit sameAs Twitter) + FAQPage | 2026-04-10 |
| **JSON-LD Feature-Pages** | ✅ WebPage + BreadcrumbList (2-Level, Google-Validator-konform) | 2026-04-10 |
| **JSON-LD Blog-Posts** | ✅ BlogPosting (Google-News-eligible) + BreadcrumbList (3-Level) | 2026-04-10 |
| **Twitter Card** | ✅ `@SeasonAlph4882` auf Landing + 21 Pages + Blog-Template + im Footer sichtbar | 2026-04-10 |
| **Bing Webmaster Tools** | ✅ Setup + 10 URLs manuell submitted | 2026-04-10 |
| **IndexNow** | ✅ Key am Host-Root + 26 Core-URLs gepingt (HTTP 200) + Auto-Ping im Deploy-Step | 2026-04-10 |
| **EN-Lokalisierung** | ✅ 31 statische `/en/`-Seiten (Pre-Rendering), SEO-Head/canonical/hreflang/JSON-LD gebacken; Sitemap mit hreflang de/en/x-default (88 URLs) | 2026-06-13 |
| **llms.txt (GEO)** | ✅ Kuratiertes KI-Crawler-Inhaltsverzeichnis unter `/llms.txt` (Generator + nginx + Mount) | 2026-06-13 |
| **www → non-www Redirect** | ✅ 301 Canonicalization für HTTP + HTTPS live | 2026-04-10 |
| **Programmatische /analyse/* Pages** | ✅ **Endgültig entfernt am 2026-04-18**. Nginx liefert 410 Gone, Builder erzeugt keine Pages mehr und löscht bestehende HTML-Files beim Build (Cleanup-Schritt). Google wirft die ~270 URLs innerhalb von 1–2 Wochen aus dem Index. | 2026-04-18 |
| **Google Search Console** | 🟠 Sitemap neu eingereicht, 10+ URLs manuell (Tageslimit erreicht), Rest morgen | 2026-04-10 |
| **Analytics** | 🟠 Scaffold in `landing/components/analytics.html`, bewusst nicht aktiviert | offen |
| **Rich Results Validierung** | 🟠 Nach erstem Crawl (1-2 Wochen) prüfen | offen |

**Live-Check-Kommandos:**
```bash
# OG-Image erreichbar?
curl -sI https://seasonalpha.ai/landing/assets/images/og-image.png | head -3

# Sitemap-URL-Count (Erwartung: 49)
curl -s https://seasonalpha.ai/sitemap.xml | grep -c "<loc>"

# /analyse/* in Sitemap (Erwartung: 0 wegen Thin-Content-noindex)
curl -s https://seasonalpha.ai/sitemap.xml | grep -c "/analyse/"

# Meta-Marker in Feature-Page (aktuell V5 = SEO-optimierte Titles)
curl -s https://seasonalpha.ai/jahreszyklus | grep -c "SA_META_V5"

# noindex auf programmatischer Page?
curl -s https://seasonalpha.ai/analyse/apple-saisonalitaet | grep -i 'robots.*noindex'

# www → non-www Redirect?
curl -sI https://www.seasonalpha.ai/dashboard | grep -E "^(HTTP|Location)"

# IndexNow Key am Host-Root?
curl -sI https://seasonalpha.ai/c0d4540dc5a10d464d473960f4d20be3.txt | head -3

# Cache-Bust per Deploy?
curl -s https://seasonalpha.ai/jahreszyklus | grep -oE 'app\.css\?v=[a-z0-9]+' | head -1

# WebSite + SearchAction JSON-LD auf Landing?
curl -s https://seasonalpha.ai/ | grep -oE '"@type":"WebSite"[^<]*' | head -1

# robots.txt AI-Crawler Policy?
curl -s https://seasonalpha.ai/robots.txt | grep -c "GPTBot\|ClaudeBot\|PerplexityBot"
```

## Aktueller Fokus (2026-06-13 — nach EN-Launch + GEO)

**Heute erledigt:** EN-Pre-Rendering live (31 statische `/en/`-Seiten), Sitemap mit hreflang (de/en/x-default, 88 URLs inkl. EN), `llms.txt` für KI-Suchmaschinen.

### 🔴 GSC — DU (manuell, nächste Tage)
- [ ] **Sitemap neu einreichen** (`sitemap.xml`) — enthält jetzt /en/ + hreflang.
- [ ] **Kein separates /en/-Property nötig** — die Domain-/Prefix-Property deckt `/en/*` automatisch ab (nur ein Pfad).
- [ ] **URL-Inspection + „Indexierung beantragen"** für 6-8 EN-Kernseiten: `/en/`, `/en/dashboard`, `/en/dekadenzyklus`, `/en/jahreszyklus`, `/en/opex`, `/en/ki-saisonalitaet`, `/en/scanner`, `/en/blog/`.
- [ ] **hreflang-Validierung** nach ~1 Woche (werden EN-Seiten eigenständig indexiert statt zu DE konsolidiert?).
- [ ] **Rich Results Test** für die neue EN-FAQPage (Landing) + EN Blog-Article.
- [ ] **Live-Check nach Deploy:** `curl -s https://seasonalpha.ai/llms.txt | head` · `curl -s https://seasonalpha.ai/sitemap.xml | grep -c hreflang`.

### 🟠 GEO / KI-Suche
- [x] `llms.txt` (Generator + nginx + Mount). robots.txt KI-Allowlist (18 Bots) seit 04-2026.
- [ ] **FAQPage-JSON-LD auf Feature-Pages ausrollen** (aktuell nur Landing) — Q&A ist am zitierfähigsten für KI-Engines (ChatGPT/Perplexity/AI Overviews).
- [ ] **Definitions-Absatz** ganz oben je Feature-Page („**Saisonalität** ist …").
- [ ] **`Organization.sameAs`** erweitern (LinkedIn/Crunchbase) — echte URLs vom User nötig.

### 🟠 On-Site (Code)
- [ ] Font-Preloading (LCP), Per-Page-OG-Images, interne Verlinkung Blog↔Feature, optional Pretty EN-Slugs (`/en/decade-cycle`).

### Marketing — DU
- [ ] LinkedIn + X: EN-Launch + Blog #22-24 ankündigen. Social-Debugger re-scrape (OG-Cache). Rich Results Test für die 3 Polymarket-Posts.

---

## Offene Tasks (in Reihenfolge)

### 🔴 SOFORT (vom User selbst zu machen)
- [x] **GSC Sitemap neu eingereicht** nach der 319→49 URL Verschlankung (2026-04-10)
- [x] **GSC URL-Inspection für Feature-Pages** — 10 Requests bis zum Tageslimit gemacht (2026-04-10). Morgen ab ~9 Uhr lokal wieder ~10 Requests verfügbar.
- [x] **GSC Live-URL-Check auf `/analyse/apple-saisonalitaet`** bestätigt: `<meta name=robots content=noindex>` wirkt sofort (2026-04-10).
- [ ] **Morgen (2026-04-11)** GSC URL-Inspection für die Rest-Feature-Pages nachziehen die gestern das Tageslimit gesprengt haben:
  - `/plain-vanilla`, `/backtest-engine`, `/ki-saisonalitaet`, `/monatswechsel`, `/trifecta`, `/wochentage` je einzeln → „Indexierung beantragen"
- [ ] **Twitter Card Validator** testen: https://cards-dev.twitter.com/validator → `https://seasonalpha.ai/jahreszyklus` → muss OG-Image zeigen
- [ ] **LinkedIn Post Inspector**: https://www.linkedin.com/post-inspector/ → gleiche URL → muss Preview generieren (dabei auch den LinkedIn-Cache invalidieren)
- [ ] **Facebook Sharing Debugger**: https://developers.facebook.com/tools/debug/ → gleiche URL → „Scrape Again" drücken (Facebook cached OG-Images 30 Tage)
- [ ] **Google Rich Results Test**: https://search.google.com/test/rich-results → eine Blog-URL (z.B. `https://seasonalpha.ai/blog/anomalie-radar-erklaert/`) → muss `Article` + `BreadcrumbList` validieren

### 🟠 DIESE WOCHE (15-30 Min)
- [x] **Bing Webmaster Tools Setup + 10 URLs submitted** (2026-04-10)
  Die 10 Kern-URLs (Landing, Dashboard, Jahreszyklus, Plain Vanilla, Backtest, KI-Saisonalität, Monatswechsel, Trifecta, Blog, Wochentage) wurden manuell im Bing Webmaster Tool via „URL Submission" eingereicht. Follow-up: in 24-72h in „Search Performance → Top pages" prüfen ob sie auftauchen.
- [ ] **GSC Coverage-Check** ab 2026-04-17: Linkes Menü → Seiten → „Gefunden – zurzeit nicht indexiert" Bucket sollte von **72** auf **~0** fallen (270 `/analyse/*` sollten in „Durch noindex-Tag ausgeschlossen" wandern — das ist OK). „Indexiert" sollte von ~30 auf ~49 ansteigen (Landing + 21 Features + Blog).
- [ ] **GSC Rich-Results-Check** ab 2026-04-17 bis 2026-04-24: Linkes Menü → Verbesserungen → Article / FAQ / Breadcrumbs / WebPage — Fehler prüfen und fixen
- [ ] **Bing Follow-Up** ab 2026-04-12: Bing Webmaster → Search Performance → Top pages: schauen ob die 10 manuell submitted URLs + die 26 IndexNow-URLs Impressions bekommen
- [ ] **Domain-Quality-Score-Recovery** ab 2026-04-24: GSC Leistung → Klicks/Impressions vs. 14-Tages-Vergleich — die 21 Feature-Pages sollten nach der /analyse/ Noindex-Aktion bessere Rankings kriegen (Quality-Signal nicht mehr durch Thin-Content verwässert)

### 🟢 MITTELFRISTIG (wenn sich was bewegt)
- [ ] **Weg B: Programmatische /analyse/* Pages inhaltlich aufwerten** (aktuell auf noindex). Pro Page braucht's: echte Monats-Performance-Tabelle (12 Zeilen aus Supabase, alle unterschiedlich), SVG-Inline Chart Jahresverlauf normiert, Dekaden-Aufschlüsselung (letzte 3 Dekaden), historische Extreme (bestes Jahr, schlechtestes Jahr, max DD), CTAs auf `/dashboard?t={ticker}` + `/jahreszyklus?t={ticker}`, Fake-KI-Blur komplett entfernen, Asset-Klassen-spezifische Intros (Aktie/ETF/Crypto/FX), Schema.org `Dataset` + `Table`. Dann `seo_template.html` noindex raus + `ENABLE_PROGRAMMATIC_IN_SITEMAP = True` in `programmatic_seo_builder.py`. Aufwand: 2-4 Stunden Template-Rebuild + Supabase-Queries.
- [x] **Breadcrumb-JSON-LD** auf die 21 Feature-Pages — ✅ 2026-04-10 (2-Level, Validator-konform)
- [ ] **Analytics aktivieren** — Entscheidung zwischen Plausible Cloud (9 €/Monat, zero-config) und self-hosted Umami (kostenlos, Docker-Container). Scaffold in `landing/components/analytics.html`. Sobald aktiv: Loader-Mechanik in `app.js` einbauen oder Snippet inline in allen HTMLs
- [ ] **OG-Image pro Page** — aktuell 1 globales OG-Image für alle. Besser: 21 individuelle Banner mit Feature-spezifischem Headline („Jahreszyklus", „Dashboard" etc.). Template-Logic in `scripts/generate_og_images.py` erweitern
- [ ] **Font-Preloading** auf Landing + 21 Pages für LCP-Boost (Core Web Vitals)
- [ ] **Sitemap-Index** bei >500 URLs (aktuell 49, erst relevant wenn Weg B die 270 /analyse/* re-aktiviert)
- [ ] **hreflang-Tags** wenn EN-Version kommt
- [ ] **Image-Alt-Text-Audit** auf Blog-Bilder

### 🟢 LATER (wenn Traffic da ist, Priorität aus GSC Leistung-Report)
- [ ] Title/Description der Top-10-Impression-Pages mit schwacher CTR überarbeiten
- [ ] Content-Erweiterung auf Pages mit hohen Impressions aber schlechtem Ranking
- [ ] Interne Verlinkung zwischen Blog-Posts und Feature-Pages verstärken
- [ ] Schema-Typen erweitern: `HowTo` für Tutorial-Blog-Posts, `Review` für Strategy-Comparison-Posts

## Wie SEO-Inhalte entstehen (Pipeline)

```
Code ─► Deploy ─► Assets live ─► Sitemap live ─► Google crawlt ─► Impressions ─► Klicks ─► Traffic
  │        │          │             │              │                │            │         │
  1        2          3             4              5                6            7         8
```

1. **Code-Änderung** (z.B. neue Feature-Page, neuer Blog-Post)
2. **`git push master`** → GitHub Actions `deploy.yml` triggert automatisch (~20s)
3. **`deploy/inject_credentials.sh`** fügt Supabase-Credentials + Cache-Bust-SHA ein
4. **`seo/programmatic_seo_builder.py`** wird beim Deploy NICHT automatisch gerufen — muss manuell wenn Sitemap sich ändert! (⚠️ **TODO**: in deploy.yml ergänzen)
5. **Google Search Console** Sitemap-Submission triggert Crawl-Queue
6. **Crawl-Statistiken** (GSC → Einstellungen → Crawling-Statistiken) zeigen wann Googlebot vorbeikam
7. **GSC Leistung → Impressions** steigen nach 3-14 Tagen
8. **Klicks + Position** verbessern sich über Wochen wenn Content gut ist

## ⚠️ Bekannte Lücke: Sitemap-Rebuild beim Deploy

`seo/programmatic_seo_builder.py` wird im `deploy.yml` Workflow aufgerufen und baut dort die Sitemap neu. Das heißt: **wenn du die Liste in `build_sitemap()` änderst, fließt das automatisch mit dem nächsten Push ein.**

**Aber**: Wenn du nur einen neuen Blog-Post hinzufügst (der dynamisch aus `blog/posts/*.md` Frontmatter gelesen wird), wird er auch mit aufgenommen weil der Generator `blog/posts/` scannt.

**Nur wenn du eine neue HTML-Page in `landing/pages/` anlegst**, musst du den Slug manuell in `build_sitemap()` in die `landing_pages` Liste eintragen. **Das ist eine manuelle Checkliste-Aktion bei jeder neuen Page.**

**TODO für später:** Auto-Discovery aller `landing/pages/*.html` ins `build_sitemap()`, z.B. via `glob.glob("landing/pages/*.html")` + Slug aus Dateiname ableiten. Dann ist diese Lücke geschlossen.

## Monitoring — was regelmäßig zu checken ist

### Täglich (0 Min, nur falls was auffällt)
Nichts aktiv. Nur reagieren wenn GSC-Email-Benachrichtigung kommt.

### Wöchentlich (5 Min)
- **GSC → Leistung**: Impressions, Klicks, CTR, Position über die letzten 7 Tage
- **GSC → Seiten**: Sind neue Pages als „Indexiert" markiert?

### Monatlich (15 Min)
- **GSC → Leistung**: Top-10-Suchanfragen checken. Welche Keywords bringen Traffic? Unerwartete?
- **GSC → Verbesserungen** (Rich Results): Fehler oder Warnungen?
- **GSC → Sitemaps**: „Gefundene URLs" = erwarteter Count (aktuell 319)?
- **OG-Image Review**: Falls Design-Änderungen an der Landing, `py scripts/generate_og_images.py` neu laufen lassen. Danach LinkedIn/Facebook Debugger manuell re-scrapen (caches 30 Tage)

### Nach jedem größeren Feature
- **Neue HTML-Page anlegen?** → Slug in `seo/programmatic_seo_builder.py::build_sitemap() landing_pages` Liste nachtragen
- **Neuer Blog-Post?** → automatisch in Sitemap, aber: `og_image` in Frontmatter setzen falls Custom-Banner gewünscht
- **Meta-Tag-Änderungen?** → `scripts/upgrade_page_meta.py` ist idempotent, kann re-run werden falls Template sich ändert (Marker entfernen vorher)

## Wichtige URLs

| Tool | URL |
|---|---|
| Google Search Console | https://search.google.com/search-console/ |
| Google Rich Results Test | https://search.google.com/test/rich-results |
| Google Mobile-Friendly Test | https://search.google.com/test/mobile-friendly |
| Google PageSpeed Insights | https://pagespeed.web.dev/ |
| Bing Webmaster Tools | https://www.bing.com/webmasters |
| Twitter Card Validator | https://cards-dev.twitter.com/validator |
| LinkedIn Post Inspector | https://www.linkedin.com/post-inspector/ |
| Facebook Sharing Debugger | https://developers.facebook.com/tools/debug/ |
| Schema Markup Validator | https://validator.schema.org/ |
| Live-Sitemap | https://seasonalpha.ai/sitemap.xml |
| Live-Robots | https://seasonalpha.ai/robots.txt |

## Twitter-Handle

- **Production**: `@SeasonAlph4882`
- **Gesetzt in**: `landing/index.html`, alle 21 Feature-Pages (via `scripts/upgrade_page_meta.py`), `blog/templates/blog_post.html`

## Referenzen zu anderen Docs

- `docs/SEO_ENGINE.md` — Programmatic-SEO-Generator (technische Architektur, Templates, SYMBOLS-Integration)
- `docs/BLOG_WORKFLOW.md` — Blog-Post-Erstellung, Social-Snippets, YouTube-Scripts
- `docs/ARCHITECTURE.md` — Gesamt-Architektur (Deployment, Supabase, Docker)
- `Roadmap.md` — Feature-Roadmap (5 Wellen)
- `CLAUDE.md` — Projekt-Root-Doku mit kritischen Regeln
- `deploy/nginx.conf` — Cache-Strategy für `/landing/*.css/*.js` (must-revalidate) und statische Assets (max-age=86400)

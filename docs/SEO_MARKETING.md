# SEO & Marketing — SeasonAlpha

> Living Document | Stand 2026-04-10 | Ergänzt `SEO_ENGINE.md` (Generator) um Status, Checklisten, Google-Search-Console-Workflow, Monitoring.

## Schnellstatus

| Bereich | Status | Datum |
|---|---|---|
| **Landing-Page Meta-Tags** | ✅ Voll ausgestattet | 2026-04-10 |
| **21 Feature-Pages Meta-Tags** | ✅ Via `scripts/upgrade_page_meta.py` aufgestockt | 2026-04-10 |
| **OG-Image (1200×630)** | ✅ V3 Ultra Design, via `scripts/generate_og_images.py` | 2026-04-10 |
| **Apple-Touch-Icon (180×180)** | ✅ | 2026-04-10 |
| **PNG-Favicons (16/32)** | ✅ | 2026-04-10 |
| **Sitemap** | ✅ **319 URLs** (21 Features + 4 Blog-Indizes + 18 Blog-Posts + 270 programmatische Analyse-Pages + 6 statische) | 2026-04-10 |
| **robots.txt** | ✅ Sitemap referenziert, `/app/` blockiert | vorher |
| **JSON-LD Landing** | ✅ Organization + SoftwareApplication + FAQPage | vorher |
| **JSON-LD Feature-Pages** | ✅ WebPage-Schema mit publisher + logo | 2026-04-10 |
| **JSON-LD Blog-Posts** | ✅ BlogPosting (Google-News-eligible) + BreadcrumbList | 2026-04-10 |
| **Twitter Card** | ✅ `@SeasonAlph4882` überall | 2026-04-10 |
| **Google Search Console** | ⚠️ Sitemap-Re-Submission nach Update nötig | offen |
| **Bing Webmaster Tools** | ⚠️ Import aus GSC ausstehend | offen |
| **Analytics** | 🟠 Scaffold in `landing/components/analytics.html`, noch nicht aktiv | bewusst offen |
| **Rich Results Validierung** | ⚠️ Nach erstem Crawl (1-2 Wochen) prüfen | offen |

**Live-Check-Kommandos:**
```bash
# OG-Image erreichbar?
curl -sI https://seasonalpha.ai/landing/assets/images/og-image.png | head -3

# Sitemap-URL-Count
curl -s https://seasonalpha.ai/sitemap.xml | grep -c "<loc>"

# Meta-Marker in Feature-Page?
curl -s https://seasonalpha.ai/jahreszyklus | grep -c "SA_META_V2"

# Cache-Bust per Deploy?
curl -s https://seasonalpha.ai/jahreszyklus | grep -oE 'app\.css\?v=[a-z0-9]+' | head -1
```

## Offene Tasks (in Reihenfolge)

### 🔴 SOFORT (5-10 Min, vom User selbst zu machen)
- [ ] **Google Search Console** → `https://search.google.com/search-console/`
  1. Property `seasonalpha.ai` prüfen (Domain-Property, nicht URL-Prefix)
  2. Linkes Menü → Indexierung → Sitemaps → `sitemap.xml` erneut einreichen (falls schon drin: Drei-Punkte-Menü → „Aktualisieren")
  3. URL-Prüfung für 7 Haupt-Pages manuell triggern:
     - `/`
     - `/dashboard`
     - `/jahreszyklus`
     - `/plain-vanilla`
     - `/backtest-engine`
     - `/ki-saisonalitaet`
     - `/blog/`
     - Pro URL: eingeben → Enter → „Indexierung beantragen". Limit ~10 Requests/Tag pro Property.
- [ ] **Twitter Card Validator** testen: https://cards-dev.twitter.com/validator → `https://seasonalpha.ai/jahreszyklus` → muss OG-Image zeigen
- [ ] **LinkedIn Post Inspector**: https://www.linkedin.com/post-inspector/ → gleiche URL → muss Preview generieren (dabei auch den LinkedIn-Cache invalidieren)
- [ ] **Facebook Sharing Debugger**: https://developers.facebook.com/tools/debug/ → gleiche URL → „Scrape Again" drücken (Facebook cached OG-Images 30 Tage)
- [ ] **Google Rich Results Test**: https://search.google.com/test/rich-results → eine Blog-URL (z.B. `https://seasonalpha.ai/blog/anomalie-radar-erklaert/`) → muss `Article` + `BreadcrumbList` validieren

### 🟠 DIESE WOCHE (15-30 Min)
- [ ] **Bing Webmaster Tools** Import aus GSC: https://www.bing.com/webmasters → Anmelden mit Microsoft-Konto → „Import from Google Search Console" → Zero-Effort-Indexing für Bing (4% der DE-Suchen)
- [ ] **GSC Coverage-Check** nach 3-7 Tagen: Linkes Menü → Seiten → „Indexiert" sollte von ~30 auf ~300 steigen. „Nicht indexiert" Gründe checken
- [ ] **GSC Rich-Results-Check** nach 1-2 Wochen: Linkes Menü → Verbesserungen → Article / FAQ / Breadcrumbs / WebPage — Fehler prüfen und fixen

### 🟢 MITTELFRISTIG (wenn sich was bewegt)
- [ ] **Analytics aktivieren** — Entscheidung zwischen Plausible Cloud (9 €/Monat, zero-config) und self-hosted Umami (kostenlos, Docker-Container). Scaffold in `landing/components/analytics.html`. Sobald aktiv: Loader-Mechanik in `app.js` einbauen oder Snippet inline in allen HTMLs
- [ ] **Breadcrumb-JSON-LD** auf die 21 Feature-Pages (aktuell nur Blog hat Breadcrumbs)
- [ ] **OG-Image pro Page** — aktuell 1 globales OG-Image für alle. Besser: 21 individuelle Banner mit Feature-spezifischem Headline („Jahreszyklus", „Dashboard" etc.). Template-Logic in `scripts/generate_og_images.py` erweitern
- [ ] **Sitemap-Index** bei >500 URLs (aktuell 319, erst relevant wenn sich das verdoppelt)
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

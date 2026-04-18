# Programmatic SEO Engine — SeasonAlpha

> Stand: 2026-04-18 | Nur noch Sitemap + robots.txt + Disclaimer | **Ticker-Landingpages entfernt**

## Historie

Die SEO Engine hat zwei Iterationen durchgemacht:

| Datum | Scope |
|---|---|
| 2026-03-27 | **v1** — 94 automatisch generierte Ticker-Landingpages unter `/analyse/{slug}` (Apple, DAX, BTC etc.) |
| 2026-04-10 | **v1.5** — Pages auf `noindex` gesetzt (Thin-Content-Penalty) und aus Sitemap entfernt, physisch aber weiter erzeugt (Weg A) |
| 2026-04-18 | **v2** — Ticker-Landingpages **endgültig entfernt**. Nginx antwortet mit `410 Gone`, Builder erzeugt sie nicht mehr und löscht bestehende Files beim Build-Cleanup |

**Warum weg?** Die Pages waren reine Template-Rotation ohne echten Content (Platzhalter-Statistiken, geblurrter KI-Bereich als Lead-Magnet). Google hat sie als "Gefunden — zurzeit nicht indexiert" markiert. Das verwässert das Domain-Quality-Signal und zieht den Ranking-Schnitt echter Feature-Pages nach unten.

**Back-up-Plan "Weg B"** (nicht umgesetzt): echten Content generieren (Monats-Performance-Tabelle aus Supabase, SVG-Chart, Dekaden-Split pro Ticker). Dafür müsste eine eigene Content-Pipeline gebaut werden — Aufwand zu groß für unsicheren ROI, weitere Content-Investments gehen derzeit in den Blog.

## Aktueller Scope

Die Engine hat heute drei Aufgaben:

| Output | Zweck |
|---|---|
| `seo/output/sitemap.xml` | Master-Sitemap mit statischen Pages + 22 Feature-Pages + Blog-Index + Blog-Posts |
| `seo/output/robots.txt` | Crawler-Regeln + Sitemap-Verweis + AI-Crawler Allowlist |
| `seo/output/disclaimer.html` | YMYL-konformer Haftungsausschluss (7 Abschnitte, via `/disclaimer`-Route) |

Zusätzlich ein **Cleanup-Schritt**: beim Build werden alle `seo/output/{slug}.html` gelöscht, die zu den Ticker-Slugs aus `shared/symbols.py` passen. Damit werden Alt-Files die noch vom alten Builder-Stand übrig sind entfernt. `disclaimer.html` und `google<hash>.html` bleiben explizit erhalten.

## Dateien

| Datei | Beschreibung |
|---|---|
| `seo/programmatic_seo_builder.py` | Generator: Sitemap + robots.txt + Disclaimer + Cleanup |
| `seo/seo_template.html` | Legacy Jinja2-Template für Ticker-Pages (nicht mehr genutzt, für Referenz erhalten) |
| `seo/output/sitemap.xml` | 50+ URLs (Landing + Feature-Pages + Blog-Indizes + Blog-Posts) |
| `seo/output/robots.txt` | Crawler-Regeln |
| `seo/output/disclaimer.html` | Haftungsausschluss |
| `seo/output/google<hash>.html` | Google Search Console Verifizierung |

## Ausführen

```bash
py seo/programmatic_seo_builder.py
```

Ergebnis: `sitemap.xml` + `robots.txt` + `disclaimer.html` in `seo/output/` + Cleanup alter Ticker-Files.

## Sitemap-Quelle

Die Sitemap wird aus drei Quellen zusammengestellt:

1. **Statische Pages** (hart in `build_sitemap()` gelistet): `/`, `/pricing`, `/disclaimer`, `/datenschutz`, `/impressum`
2. **Tool-Pages** (hart gelistet): `/tools/trading-day-converter` etc.
3. **Auto-Discovery** aus `landing/pages/*.html` — jede nicht-excluded HTML-Page landet mit default Priority 0.85/weekly in der Sitemap. Per-Page-Overrides via `PRIORITY_OVERRIDES`-Dict (z.B. Dashboard 1.0/daily, Polymarket 0.95/daily).
4. **Blog-Posts** aus `blog/posts/*.md` (nur status=`published`).

## Nginx-Routen (deploy/nginx.conf)

| URL | Ziel |
|---|---|
| `/analyse/*` | `return 410 Gone` (Thin-Content-Pages endgültig weg) |
| `/disclaimer` | `seo/output/disclaimer.html` |
| `/sitemap.xml` | `seo/output/sitemap.xml` via static-Alias |
| `/robots.txt` | `seo/output/robots.txt` via static-Alias |
| `/google<hash>.html` | Google Search Console Verifizierung |
| `/dashboard`, `/jahreszyklus`, ... | `landing/pages/<name>.html` |
| `/blog/` | `blog/output/` |

## Auto-Deploy (GitHub Actions)

Bei Push auf `master` (siehe `.github/workflows/deploy.yml`):

1. `git pull origin master`
2. `bash deploy/inject_credentials.sh` (Supabase-Creds in Landing-HTML)
3. `python3 seo/programmatic_seo_builder.py` (Sitemap + Robots + Cleanup)
4. `docker compose up -d --build`
5. `docker compose exec -T app python3 blog/blog_builder.py --build`
6. `docker compose restart nginx`
7. `python3 scripts/submit_indexnow.py` (Bing/Yandex/Seznam-Ping)

## Disclaimer (YMYL)

`seo/output/disclaimer.html` enthält 7 Abschnitte:
1. Keine Anlageberatung (WpHG, KWG, §34f GewO)
2. Historische Daten & Saisonalität
3. KI-Modelle & Halluzinations-Hinweis
4. Datenquellen & Genauigkeit
5. Haftungsbeschränkung
6. Interessenkonflikte
7. Anwendbares Recht

## Google Search Console

- **Property:** seasonalpha.ai (URL-Präfix)
- **Verifizierung:** DNS-TXT bei STRATO + HTML-Meta-Tag in allen Seiten
- **Sitemap:** `https://seasonalpha.ai/sitemap.xml`

### Was in GSC zu erwarten ist (nach 2026-04-18-Cleanup)

Die bisherigen 263 "Alternative Seite mit kanonischem Tag" + 10 "Durch noindex ausgeschlossen" kommen fast ausschließlich aus den alten `/analyse/*`-Pages. Mit dem `410 Gone` werfen Google-Bots die URLs innerhalb von 1–2 Wochen raus. Erwartete Endzahlen in GSC:

- **Indexiert**: ca. 50 (Landing + Feature-Pages + Blog-Posts), steigt mit jedem neuen Blog-Post
- **Nicht indexiert**: < 30 (nur noch echte 404s, noindex-Pages wie `/watchlist`, `/unsubscribe`, und Weiterleitungen)

## Content-Strategie ab 2026-04-18

Statt massenhafter Thin-Content-Pages jetzt **qualitative Content-Investments** an einem Ort: dem Blog (`blog/posts/*.md`).

| Eigenschaft | Ticker-Pages (alt, weg) | Blog-Posts (neu, Fokus) |
|---|---|---|
| Produktion | automatisch generiert aus Template | manuell oder KI-unterstützt, echter Content |
| Umfang | ~300 Wörter, Platzhalter | 700–1.000 Wörter, konkrete Zahlen |
| Struktur | starr | Hook + Analyse + Interpretation + FAQ |
| Unique Content | niedrig | hoch (eigene Daten aus Supabase) |
| FAQPage-Schema | nein | ja (Rich Results) |
| Update-Frequenz | pro Build | pro Event (Fed-Meeting, CPI, etc.) |
| ROI | negativ (Thin-Content-Penalty) | positiv (Long-Tail Keywords) |

Details zur Blog-Engine: [docs/BLOG_WORKFLOW.md](BLOG_WORKFLOW.md)

## Metriken & Ziele

| Metrik | Ist (2026-04-18) | Ziel |
|---|---|---|
| SEO-Feature-Pages | 22 in Sitemap | stabil, einzelne auf 0.95/daily priorisieren |
| Blog-Posts | 6 | 4/Monat |
| Core Web Vitals | LCP < 1s | LCP < 1s, CLS < 0.1 |
| Top-Keywords | noch keine Top-10-Rankings | Top 10 für Long-Tail („Fed-Cuts 2026 Prognose", „BTC 150k Polymarket") |
| GSC „indexiert" | 25 | 50+ (nach Cleanup + neue Blog-Posts) |
| GSC „nicht indexiert" | 329 | < 30 (nach 1–2 Wochen 410-Crawling) |
| Kosten | 0 EUR (bestehender VPS) | 0 EUR |

## Referenzen

- [SEO_MARKETING.md](SEO_MARKETING.md) — laufende SEO-Marketing-Checkliste (Twitter, Bing, IndexNow etc.)
- [BLOG_WORKFLOW.md](BLOG_WORKFLOW.md) — wie Blog-Posts entstehen und gepflegt werden
- [POLYMARKET.md](POLYMARKET.md) — Polymarket-Integration (eigener Blog-Content-Pfeiler)

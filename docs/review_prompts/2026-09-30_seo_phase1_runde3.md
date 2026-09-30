# Review-Auftrag: SEO Phase 1 — CODE, Runde 3

Repo `C:\dev\Seasonaledge`. Runde 2: `docs/review_prompts/2026-09-30_seo_phase1_runde2.md`, FREIGABE nein, 3 Befunde.
Alle umgesetzt:

1. **DE-Pflichtseiten unabhängig vom Dateibestand:** `pflicht_artefakte()` ergänzt die DE-Quelle jeder EN-Seite aus
   `_EN_PAGE_META` und jedes Ziel aus `landing/components/nav.html`/`footer.html` (deckt `/kalender`, `/profile`,
   `/watchlist` usw. ab). Mutationen: `kalender.html` bzw. `profile.html` gelöscht → rot.
2. **Wertevergleich vollständig:** `<title>` = `seo_title|title` + „ | SeasonAlpha Blog", `og:title` = title,
   `twitter:title` = `seo_title|title`, `article:published_time`/`article:modified_time` sowie
   `BlogPosting.datePublished/dateModified` aus `veroeffentlicht_am`/`geaendert_am`. Vier Mutationen → rot.
3. **Eine hreflang-Regel für HTML und Sitemap:** neu `shared.seo_basis.blog_hreflang_ziele()` → ({de: en}, {en: de})
   nur mit veröffentlichten UND indexierbaren Gegenstücken. Blog-Builder (DE: `en_slug`, EN: neues
   `hreflang_de_slug`; das Template nutzt nicht mehr `de_slug`) und Sitemap-Builder rufen dieselbe Funktion;
   `blog_sprachpaare()` validiert weiterhin veröffentlichte Zuordnungen separat. Direkter Test mit konstruierten
   Paaren (beide indexierbar / nur EN noindex / nur DE noindex) + Mutation „hreflang auf noindex-Artikel" → rot.

Mutationstest 28/28 + Regeltest grün; lokaler Build EN + Blog + Sitemap, `verify_seo_html.py` 0 Fehler.

Prüfe Korrekturen und Gesamtstand. Antwort auf Deutsch, je Befund Schwere + Datei:Zeile + Änderung, am Ende genau
eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.

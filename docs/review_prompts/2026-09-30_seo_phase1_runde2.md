# Review-Auftrag: SEO Phase 1 — CODE, Runde 2

Repo `C:\dev\Seasonaledge`. Runde 1: `docs/review_prompts/2026-09-30_seo_phase1_runde1.md`, FREIGABE nein, 5 Befunde.
Alle umgesetzt (`git diff`, neue Dateien `shared/seo_basis.py`, `scripts/verify_seo_html.py`, `scripts/verify_seo_mutation.py`):

1. **Sitemap-Vergleich:** `sitemap_ist()` prüft Wurzel `urlset` im Sitemap-Namespace; URL-Folge wird immer
   verglichen (auch leer), bei gleicher Folge je Eintrag `lastmod` und hreflang-Alternates gegen `sitemap_eintraege()`.
2. **Pflichtartefakte:** `pflicht_artefakte()` = Sitemap-Artefakte + alle veröffentlichten Artikel DE/EN (auch noindex)
   + Blog-Übersichten/Kategorien DE/EN + alle EN-Seiten laut `_EN_PAGE_META` + feste Seiten (Startseite, Über uns,
   Rechtliches, Disclaimer, Trading-Day-Converter). Fehlende Datei = Fehler.
3. **Keine zweite Dekodierung** beim EN-Beschreibungsvergleich.
4. **Kein Tagesdatum-Fallback:** `veroeffentlicht_am()` wirft `FrontMatterFehler` ohne `date`; `geaendert_am()` =
   `updated` oder `date`; der Blog-Builder nutzt `veroeffentlicht_am` statt `meta.get("date", date.today())`.
5. **Historie:** EN-Startseitentitel „with up to 131 Years", Tour-Einstieg DE/EN „bis zu/up to"; der Wächter meldet
   „131 Jahre/years" ohne „bis zu/up to", außer in Zeilen über Dow/DJI/Dekadenzyklus (dort wörtlich richtig).

Mutationstest jetzt 21/21 (neu: leere Sitemap, falsche Wurzel, fehlendes lastmod, fehlendes hreflang, fehlender
Disclaimer, fehlender noindex-EN-Artikel, EN-Doppelmaskierung, Historie ohne „up to"). Damit die isolierte Kopie
ohne `.git` lastmod rechnen kann, liest `_git_datum` bei gesetztem `SA_GIT_WURZEL` die Historie eines anderen
Checkouts (Pfade relativ identisch; nur der Mutationstest setzt die Variable).
Lokal: Build EN + Blog + Sitemap, `verify_seo_html.py` 0 Fehler.

Prüfe Korrekturen und Gesamtstand. Antwort auf Deutsch, je Befund Schwere + Datei:Zeile + Änderung, am Ende genau
eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.

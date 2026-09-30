# Review-Auftrag: EN-Köpfe / JSON-LD — CODE, Runde 2

Repo `C:\dev\Seasonaledge`. Fortsetzung von `docs/review_prompts/2026-09-30_en_jsonld_code_runde1.md`.
Deine drei Befunde aus Runde 1 und ihre Umsetzung stehen unten. Prüfe mit `git diff` und
`py -3.14 scripts/verify_en_serverpfad.py --mutationen`. Antwort auf Deutsch, je Befund Schwere +
Datei:Zeile + Änderung, am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.

## Umsetzung der Befunde aus Runde 1
1. **Unvollständige Font-Einbindung blieb unbemerkt** → neue gemeinsame Funktion
   `shared/seo_basis.py::google_fonts_pruefung(html_teil)` (Attribute per Parser, Reihenfolge egal).
   Liefert das nicht-blockierende Paar (rel=stylesheet, media=print, onload, direkt folgender
   `<noscript>` mit Fonts-Link) und Probleme: blockierend außerhalb `<noscript>`, media=print ohne
   onload, ohne `<noscript>`. `build_en.replace_head` bricht bei jedem Problem mit `HeadFehler` ab,
   `verify_seo_html.blockierende_fonts` nutzt dieselbe Funktion (für alle Artefakte), der
   Paar-Vergleich in `pruefe_en_kopf` ebenfalls.
2. **Gültige Attributreihenfolge brach den Build** → durch 1. behoben; zusätzlich `CSS_LINK`/
   `PRECONNECT` im Wächter reihenfolgeunabhängig.
3. **`@graph` übersehen** → `schema_knoten()` (oberste Objekte, Listen, `@graph`-Mitglieder) +
   `schema_typen()` (`@type` als String oder Liste); `pruefe_en_kopf` zählt FAQPage/WebPage/
   BreadcrumbList/WebSite darüber.

## Neue Belege
- `verify_en_serverpfad.py --mutationen`: neu 0 Fehler; **12/12 Mutationen** gefangen (neu: Font ohne
  onload, Font ohne noscript, FAQPage in `@graph`, zweites WebPage in `@graph`); **4/4 Quellfälle**
  an der DE-Quelle: `rel` vor `href` baut und prüft grün; Quelle ohne onload / ohne noscript /
  blockierend → Build bricht ab. Alter Stand `2da452e`: 106 Fehler.
- `landing/verify_en.py`: B4 verlangte hreflang auch für noindex-Seiten (profile/unsubscribe/watchlist)
  und widersprach damit der Plan-Regel „noindex → keine Sprachpaare" → B4 prüft bei noindex jetzt,
  dass KEIN hreflang da ist. FAIL 0.
- `verify_seo_html.py` 0 Fehler nach Neubau Blog/EN/Sitemap.

## Offene Frage aus Runde 1
`verify_en_serverpfad.py` läuft nicht im Deploy (der Deploy baut ohnehin mit Cache-Buster und
`verify_seo_html` prüft das echte Ergebnis mit `pruefe_en_kopf`). Reicht das aus deiner Sicht?

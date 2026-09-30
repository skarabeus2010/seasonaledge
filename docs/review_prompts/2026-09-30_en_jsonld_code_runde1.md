# Review-Auftrag: EN-Köpfe / JSON-LD — CODE, Runde 1

Repo `C:\dev\Seasonaledge`. Umsetzung des freigegebenen Plans `docs/review_prompts/2026-09-30_en_jsonld_plan.md`
(Runde 3, FREIGABE). Prüfe mit `git diff` und `scripts/verify_en_serverpfad.py` (neu). Antwort auf Deutsch, je
Befund Schwere + Datei:Zeile + Änderung, am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.

## Umsetzung
- `landing/build_en.py`: `replace_head` erkennt `app.css(?:\?v=…)?` und übernimmt den CSS-Link unverändert;
  übernimmt nicht-blockierendes Font-Paar (`media="print"` + folgendes `<noscript>`) und `preconnect` wörtlich;
  Quelle ohne Fonts ist gültig; nur-blockierende Einbindung → `HeadFehler`. `robots` aus der Quelle
  (`build_en_head(..., robots)`), bei noindex keine hreflang-Tags. JSON-LD über `shared.seo_basis.json_ld`.
  `build_page`: Startseite → `localize_head_targeted` (eigener Head); alle anderen: `replace_head`, sonst
  `HeadFehler` (kein stiller Rückfall mehr). `localize_index_jsonld`: `WebSite.url` → `/en/`,
  `urlTemplate` `/dashboard…` → `/en/dashboard…`; Organisation/publisher bleiben Domainwurzel.
- `scripts/verify_seo_html.py`: neue Funktion `pruefe_en_kopf(slug, en_html, de_html)` (lang, Canonical, og:url,
  og:locale, kein FAQPage, genau ein WebPage mit url=Canonical/inLanguage en bzw. Startseite WebSite+urlTemplate,
  BreadcrumbList /en/…Canonical, noindex erhalten, hreflang vollständig oder bei noindex keines, Erhalt CSS-Link/
  Font-Paar/preconnect gegen die Quelle, keine blockierenden Fonts). Prüfung 9: für alle EN-Seiten; indexierbare
  DE-Landingseiten: lang de, og:url=Canonical, og:locale de_DE, reziprokes hreflang; alle Artefakte: keine
  blockierenden Google-Fonts.
- **Beim ersten Lauf gefunden und behoben:** Blog-Templates (`blog_post.html`, `blog_index.html`) luden Google
  Fonts render-blockierend (alle ~110 Blogseiten) → nicht-blockierend + `<noscript>`. Fehlende `og:locale`/`og:url`
  auf `/ueber-uns`, `/rechtliches`, `/tools/trading-day-converter` ergänzt.
- `scripts/verify_en_serverpfad.py`: kopiert `landing/`, setzt den Cache-Buster wie `inject_credentials.sh`
  (`?v=test`), baut alle 38 EN-Seiten mit `build_page` und prüft mit `pruefe_en_kopf`. **Neuer Code 0 Fehler,
  alter Stand (`2da452e`) 106 Fehler** (= der Live-Defekt: WebPage.url DE, deutsches FAQPage, Breadcrumbs DE).
  8 Mutationen am Ergebnis (Cache-Buster entfernt, Font-Paar entfernt, blockierende Fonts, WebPage gelöscht,
  WebPage.url DE, noindex verloren, hreflang fehlt, urlTemplate DE) → alle gefangen.
- Lokal: `verify_seo_html.py` 0 Fehler nach Neubau Blog/EN/Sitemap.

## Prüfe besonders
- Font-Regex/`HeadFehler`-Bedingung: falsch-positive oder -negative Fälle?
- Seiten mit `data-en-hide`/`strip_en_hidden` oder abweichendem Head-Aufbau: bricht `replace_head` irgendwo?
- Läuft `verify_en_serverpfad.py` im Deploy? (Nein — braucht keinen node, könnte aber; soll es?)
- Startseiten-Schema: weitere sprachabhängige URLs?

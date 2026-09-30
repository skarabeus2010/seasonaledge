# Review-Auftrag (Runde 3): EN-Seiten als GSC-„Duplikat" — JSON-LD/Head-Neubau (PLAN, noch kein Code)

Repo `C:\dev\Seasonaledge`. Antwort auf Deutsch, je Befund Schwere + Datei:Zeile + Änderung; am Ende genau eine
Zeile `FREIGABE: ja` oder `FREIGABE: nein` (Freigabe = Analyse korrekt, Plan tragfähig).

## Befund
- GSC „Duplikat – Google hat eine andere Seite als der Nutzer als kanonische Seite bestimmt": **18 URLs, alle
  EN-Landingseiten** (`/en/`, `/en/scanner`, `/en/dashboard`, `/en/jahreszyklus` …; Export
  `raw/gsc/` folgt). Google wählt vermutlich die DE-Fassung als kanonisch.
- Ursache 1 (heute behoben, Commit `9966215`): JS-Sprachweiterleitung DE→EN für Googlebot.
- **Ursache 2:** Das JSON-LD der EN-Seiten ist auf dem Server deutsch und zeigt auf DE — belegt am vom Nutzer
  gelieferten, von Google gerenderten HTML von `/en/scanner`: `WebPage.url = https://seasonalpha.ai/scanner`,
  deutscher `name`/`description`, BreadcrumbList-`item` DE, dazu ein deutsches FAQPage — bei Canonical
  `/en/scanner`. Mechanismus (seit v63 in CLAUDE.md dokumentiert): `landing/build_en.py::replace_head` sucht
  `<link rel="stylesheet" href="/landing/css/app.css">` **ohne Query**; `deploy/inject_credentials.sh` läuft vorher
  und macht `app.css?v=<sha>` daraus → Regex greift auf dem Server nie → jede EN-Seite fällt auf
  `localize_head_targeted` zurück, das nur Titel/Description/Canonical/OG ersetzt und das JSON-LD deutsch lässt.
  **Lokal** (ohne Cache-Buster) greift `replace_head` bei 37 Seiten — dort ist das JSON-LD korrekt; deshalb sieht
  es kein lokaler Test.
- **Zweiter, gefährlicher Fehler in `replace_head` (lokal aktiv, live nur wegen Ursache 2 nie ausgelöst):** die
  Font-Regex `<link\s+href="https://fonts\.googleapis\.com[^"]*"\s+rel="stylesheet">` trifft NICHT den
  nicht-blockierenden Link (`rel="stylesheet" media="print" onload=…`), sondern den Fallback INNERHALB von
  `<noscript>`; der neue Head enthält dann ein **render-blockierendes** Google-Fonts-Stylesheet ohne `<noscript>`
  (lokal belegt: `landing/en/scanner.html` Zeile 47, `<noscript>`-Anzahl 0). CLAUDE.md verbietet genau das
  (Hänge-Risiko). Außerdem verwirft `replace_head` den Cache-Buster am CSS-Link (setzt `app.css` ohne `?v=`) und
  zwei `preconnect`-Links.
- Inventar der ersetzten Head-Region in `landing/pages/*.html`: title, description, robots, canonical, hreflang,
  OG/Twitter, Icons, 107 JSON-LD-Blöcke (WebPage, BreadcrumbList, FAQPage), Fonts-Link + noscript, 2× preconnect.

## Plan (Runde 2 — deine 5 Befunde eingearbeitet)
1. `replace_head`: Regex akzeptiert `app.css(?:\?v=[^"]*)?`; der gefundene CSS-Link wird **unverändert**
   übernommen (Cache-Buster bleibt).
2. **Fonts:** Hat die Quelle keine Google-Fonts-Einbindung (z. B. `/unsubscribe`), ist das gültig. Hat sie eine, wird
   der nicht-blockierende Link (`media="print"` + `onload`) samt direkt folgendem `<noscript>…</noscript>` wörtlich
   übernommen. Nur eine ausschließlich blockierende Einbindung ist ein Build-Fehler. `preconnect`-Links (watchlist) übernehmen.
3. **Robots aus der Quelle:** `build_en_head` übernimmt den `robots`-Inhalt der DE-Quelle (statt fest
   `index, follow`); `/en/profile`, `/en/watchlist`, `/en/unsubscribe` bleiben `noindex`. Für noindex-Seiten
   keine hreflang-Verweise erzeugen (sie stehen in keiner Sitemap und sollen nicht als Sprachpartner dienen).
4. FAQPage auf EN entfällt bewusst (deutsch, FAQ-Rich-Results abgeschafft; sichtbare FAQ bleibt übersetzt).
   WebPage + BreadcrumbList aus `build_en_head` über `shared.seo_basis.json_ld`.
5. **Startseite eigener Vertrag:** bleibt beim eigenen Head (`localize_head_targeted` + `localize_index_jsonld`);
   zusätzlich `SearchAction.target.urlTemplate` → `/en/dashboard?t={search_term_string}`, `WebSite.url` →
   `/en/`. Organisations-Identität (`Organization.url`, `publisher.url`, Logo) bleibt die Domainwurzel.
   Für alle anderen Seiten ist ein Rückfall auf `targeted` ein Build-Fehler.
6. **Wächter nach Schema-Typ und Feldpfad** (läuft im Deploy nach `inject_credentials` → Serverpfad):
   EN-Feature-Seiten müssen genau einen `WebPage` (url = Canonical, inLanguage beginnt mit `en`) und genau eine
   `BreadcrumbList` (Pos. 1 = `/en/`, letzter Eintrag = Canonical) haben; `isPartOf`/`publisher`/Logo dürfen die
   Domainwurzel sein; kein FAQPage auf EN. EN-Startseite: `WebSite.url = /en/`, `urlTemplate` beginnt mit
   `/en/dashboard`, `inLanguage` en. Alle Landingseiten: `html lang` passt zur URL-Sprache. `og:url` = Canonical und passende `og:locale`
   (de_DE/en_US) sind PFLICHT für alle erzeugten EN-Seiten und alle indexierbaren DE-Landingseiten; bei
   DE-`noindex`-Seiten (profile, unsubscribe haben weder Canonical noch OG) nur Konsistenz, falls vorhanden; für indexierbare DE/EN-Landing-Paare vollständiges, reziprokes hreflang
   (de, en, x-default=DE). Kein render-blockierendes Google-Fonts-Stylesheet außerhalb von `<noscript>`.
   noindex-EN-Seiten bleiben noindex.
7. **Erhalt gegen die Quelle** (im Test UND im Wächter für EN-Seiten gegen ihre DE-Quelle): CSS-Link inkl.
   Query unverändert; vorhandenes nicht-blockierendes Font-Link-/`<noscript>`-Paar und alle `preconnect`-Links
   erhalten; fontlose Quelle (`/unsubscribe`) bleibt gültig. Mutationen „Cache-Buster entfernt" und
   „Font-Paar entfernt" müssen rot werden.
8. **Lokaler Test des Serverpfads:** DE-Quellen wie `inject_credentials.sh` mit `?v=test` versehen, `build_page`
   für alle 38 EN-Seiten aufrufen und die Regeln aus 6 prüfen — gegen alten Code rot, neuen grün;
   Positivfall fontlose Seite (`/unsubscribe`); Mutationen: WebPage gelöscht, WebPage.url DE, blockierende Fonts,
   noindex verloren, hreflang fehlt, urlTemplate DE.
9. **Vorher dokumentieren (Nutzer):** Google-gewählte Canonical für einige der 18 URLs aus der Indexansicht
   notieren; nach dem Crawl vergleichen. Der JSON-LD-Defekt ist belegt, seine Ursächlichkeit für die Auswahl nicht.

## Prüfe besonders
- Stimmt die Mechanik (Regex, Reihenfolge im Deploy: `inject_credentials.sh` vor `build_en.py`)?
- Was verwirft `replace_head` sonst noch, das erhalten bleiben muss (Umami-Script, site-verification,
  Credentials-Script — wo stehen die)?
- Ist das Entfernen von FAQPage auf EN richtig, oder lieber übersetzen?
- Fehlt etwas im Plan (z. B. hreflang, og:locale, EN-Startseite)?

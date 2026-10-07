# Review-Auftrag: Eigene EN-Adressen (`/wahlen` → `/en/elections`), Runde 1

Repo `C:\dev\Seasonaledge`. Nutzerwunsch: die englische Fassung von `/wahlen` soll `/en/elections` heißen statt
`/en/wahlen`. Bisher wurde die EN-Adresse an über zehn Stellen als `/en/<de-slug>` abgeleitet. Prüfe den
Arbeitsstand (`git diff`). Antwort auf Deutsch, je Befund Schwere + Datei:Zeile + Änderung, am Ende genau eine
Zeile `FREIGABE: ja` oder `FREIGABE: nein`.

## Umsetzung
- **Eine Quelle:** `landing/js/i18n.js` bekommt `_EN_SLUGS = {'/wahlen': '/elections'}` (neben `_EN_PAGE_META`,
  dessen Parser unverändert bleibt). Browser: `_enHref()` (DE-Href mit Query/Fragment/Schrägstrich → EN-Href)
  und `_deAusEn()` (Umkehrung) in `_zielFuer`, `pfad`, `_applyNavLinks`, `_injectHreflang`, `_updatePageTitle`.
- **Python:** `shared/seo_basis.py::en_slugs()/en_slug()/en_url()` lesen dieselbe Liste. Genutzt in
  `landing/build_en.py` (Head-URLs, Ausgabedatei `landing/en/elections.html`, Link-Umschreibung im Body,
  Aufräumen verwaister Dateien), `seo/programmatic_seo_builder.py` (Sitemap), `scripts/verify_seo_html.py`
  (Pflichtdateien, EN-Meta, DE-hreflang-Soll, `pruefe_en_kopf`, Prüfung 9 — dort wurde die Seite vorher bei
  fehlender Datei stillschweigend übersprungen), `landing/verify_en.py`, `scripts/verify_en_serverpfad.py`.
- `landing/pages/wahlen.html`: hreflang en → `/en/elections`. `deploy/nginx.conf`: `location = /en/wahlen
  { return 301 /en/elections; }` (war seit 07.10. kurz live). Die EN-Datei liefert der bestehende
  `^~ /en/`-Block (`/en/(.+)` → `/landing/en/$1.html`).
- Test `scripts/js/probe_i18n_sprache.js` um Fall 6 erweitert: Link-Umschreibung inkl. Schrägstrich/Query/Fragment,
  `pfad()`, Sprachwechsel in beide Richtungen, hreflang auf `/en/elections`.

## Belege
EN-Build schreibt `landing/en/elections.html`; `verify_en` FAIL 0; `verify_seo_html` 0 Fehler; Sitemap enthält
`/en/elections` (kein `/en/wahlen`); `verify_en_serverpfad --mutationen` 0 Fehler, 9/9 Quellfälle;
`probe_i18n_sprache` 0 Fehler.

## Prüfe besonders
- Gibt es weitere Stellen, die `/en/<slug>` ableiten (Blog-Builder, Health-Check, Embed, Tour, Agent-Skripte,
  JSON-LD der Startseite, `localize_head_targeted`)?
- Rundreise-Fälle: `/wahlen/`, `/wahlen?x`, `/en/elections/`, Startseite, Seiten ohne Eintrag.
- Kann ein Eintrag in `_EN_SLUGS` mit einem bestehenden DE-Slug kollidieren (z. B. EN-Slug gleich einem anderen
  DE-Slug) — sollte der Wächter das verbieten?

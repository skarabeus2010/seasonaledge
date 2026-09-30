# Review-Auftrag: SEO Phase 1 — CODE, Runde 1

Repo `C:\dev\Seasonaledge`. Umsetzung von Phase 1 aus `docs/SEO_UMSETZUNGSPLAN_2026-09.md` (deine Freigabe nach
3 Runden: `docs/review_prompts/2026-09-30_seo_review_plan_runde3.md`). Prüfe mit `git diff` und den neuen Dateien
`shared/seo_basis.py`, `scripts/verify_seo_html.py`, `scripts/verify_seo_mutation.py`.
Antwort auf Deutsch, je Befund Schwere + Datei:Zeile + konkrete Änderung, am Ende genau eine Zeile
`FREIGABE: ja` oder `FREIGABE: nein`. Noch nichts ist committet oder deployt.

## Umsetzung je Planpunkt

- **1a** `shared/seo_basis.json_ld` (json.dumps + JSON-Unicode-Escapes für kleiner/größer/Und/U+2028/U+2029;
  die Escape-Tabelle wird bewusst aus `chr(92)` gebaut — zwei Werkzeugschichten haben Backslash-Literale beim
  Schreiben still umgedeutet, einmal sogar zu einer wirkungslosen Tabelle `"<" -> "<"`; getestet wird die AUSGABE).
  Blog-Builder: `select_autoescape(["html","xml"])`; als sicher (`Markup`) NUR `content`, `disclaimer_short`,
  `disclaimer_long` und die drei JSON-LD-Strings; BlogPosting/BreadcrumbList/FAQPage in `_ld_kontext` als dicts;
  UI-Strings und Template-Defaults von Entities auf Unicode; JS-Zähler im Index über `|tojson`;
  `scripts/upgrade_page_meta.py` dekodiert Eingaben (`html.unescape`) und maskiert Text/Attribut getrennt, JSON-LD über `json_ld`.
- **1b** Gemeinsame Regeln in `shared/seo_basis.py`: `ist_veroeffentlicht` (Build) und `ist_indexierbar` (Sitemaps)
  getrennt; `blog_sprachpaare()` wirft bei `de_slug` ins Leere oder Doppelbelegung (Build und Sitemap scheitern dann);
  drei `de_slug` korrigiert; `en_seiten_meta()` = einzige Quelle für EN-Verfügbarkeit (von `build_en.py`, Sitemap,
  Wächter genutzt); DE-Heads von `crash-fruehwarnung`/`dealer-positioning` ohne hreflang-en.
  DE-Artikel verlinken jetzt reziprok auf ihre EN-Fassung; Blog-Startseite/Kategorien mit hreflang DE↔EN.
- **1c** `seo/programmatic_seo_builder.py::sitemap_eintraege()`: `/en/`, `/ueber-uns`, EN-Blog, Kategorien, reziprokes
  hreflang, nur indexierbare Seiten (auch statische Einträge; `/disclaimer` ist noindex und fiel dabei raus —
  vom Wächter gefunden), `lastmod` aus `git log -1 --format=%cs` der Quelldatei auf dem Host bzw. `updated`/`date`
  der Artikel, Übersichten = jüngster Artikel; ohne verlässliches Datum kein `lastmod`.
  Kategorieseiten: eigene Canonical-URL, Titel, Beschreibung, og:url. Blog-Sitemaps nach denselben Regeln.
- **1d** `deploy.yml`: build_en → compose up → blog build → Sitemap-Builder → Wächter, jeder Schritt `|| scheitern`.
- **1e** `scripts/verify_seo_html.py`: URL→Artefakt-Zuordnung, Syntax aller Artefakte, dekodierte Werte gegen
  Front Matter / `_EN_PAGE_META`, Seitentyp-Regeln (Canonical, hreflang-Ziele, noindex), sitemap.xml = Soll,
  `--live`; zusätzlich **Kennzahlen gegen den Bestand** (Basiswerte ≤ 370 und ≥ 310, Tools ≤ 38 und ≥ 28,
  Strategien = 22 aus `SA.STRATEGIES`; Obergrenzen „bis zu/up to/max." übersprungen; eine begründete Ausnahme für
  `/vola-saisonalitaet` mit eigener Teilmenge von 333 Profilen).
  `scripts/verify_seo_mutation.py`: isolierte Repo-Kopie je Mutation, 13 Fehlerklassen, alle gefangen; Grundkopie grün.
  (Im ersten Lauf verfehlte eine Mutation — sie änderte nichts, weil die gewählte Beschreibung keine maskierbaren
  Zeichen hatte; jetzt bricht eine wirkungslose Mutation den Test ab.)
- **1f** Startseite: FAQPage entfernt; SoftwareApplication ohne „15 KI-Modelle"; Zahlen auf „über 350 Basiswerte",
  „über 35 Tools", „22 Strategien", „bis zu 131 Jahre" in DE/EN, Meta, Schema, sichtbarem Text, Pricing, Tour,
  EN-Beschreibungen; Blog-CTA ohne „KI-Prognosen", Zahl aus `symbols.py`. `build_en.localize_index_jsonld` wirft
  `UnuebersetztesSchema`, wenn ein sprachabhängiges Feld (name/alternateName/description/inLanguage) keine
  Übersetzung hat.

## Nachweise (lokal)
- Blog-Build DE+EN läuft; Vergleich aller 101 Artikel gegen die Live-Seite: sichtbarer Text identisch bis auf die
  gewollte CTA-Zeile (also Disclaimer/Umlaute nicht beschädigt); p-Wert-Artikel DE+EN: description = og = twitter =
  BlogPosting = Front Matter.
- Neue Sitemap 184 URLs (vorher 139), keine Dubletten, 33 verschiedene lastmod; alle 185 URLs der Vorversion
  (inkl. `/disclaimer`) live geprüft: 200 ohne Redirect.
- `verify_seo_html.py`: 0 Fehler. Mutationstest 13/13. `landing/verify_en.py`: FAIL 0.

## Prüfe besonders
- Autoescape: gibt es weitere Template-Variablen mit HTML-Inhalt, die jetzt maskiert würden (z. B. in `related_posts`,
  Kategorie-Labels, `hero_subtitle`)? Bleibt irgendwo Doppelmaskierung?
- `ist_veroeffentlicht`: nur `published` und fällige `scheduled`; alle 102 Dateien sind `published`. Passt das
  zum bisherigen Verhalten (vorher wurde jeder Status außer draft/scheduled gebaut)?
- Deploy: `scheitern()` in einem appleboy-ssh-Skript; `docker compose exec` nach `up -d --build` (Container bereit?).
- Wächter: fehlen Prüfungen, die der Plan verlangt? Sind die Kennzahl-Regeln zu weit oder zu eng?
- Sitemap: Git-Datum auf dem Host — Deploy macht `git checkout -- landing/` und `inject_credentials.sh` ändert
  Dateien in place (kein Commit): beeinflusst das `git log`?

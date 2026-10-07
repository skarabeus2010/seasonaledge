# Review-Auftrag: Eigene EN-Adressen (`/wahlen` → `/en/elections`), Runde 2

Repo `C:\dev\Seasonaledge`. Vorgeschichte: `docs/review_prompts/2026-10-07_en_slugs_runde1.md`. Prüfe den
Arbeitsstand (`git diff`), Schwerpunkt auf den Korrekturen zu deinen drei Befunden aus Runde 1. Antwort auf
Deutsch, je Befund Schwere + Datei:Zeile + Änderung, am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.

## Korrekturen aus Runde 1
1. **Redirect verlor die Query:** `deploy/nginx.conf` → `location = /en/wahlen { return 301 /en/elections$is_args$args; }`
   (der Snapshot-Link `?snapshot=<id>` muss die Weiterleitung überleben).
2. **Schrägstrich am Ende ergab 404:** `landing/js/i18n.js::_enHref` normalisiert `/wahlen/` → `/wahlen` vor dem
   Nachschlagen und behält Query/Fragment; `landing/build_en.py::rewrite_body_links` ebenso
   (`rest = re.match(r"[^?#]*(.*)", href).group(1)`, Schrägstrich am Pfadende entfällt).
3. **Kollisionen nicht geprüft:** `shared/seo_basis.py::pruefe_en_slugs(seiten)` meldet doppelte EN-Ziele, ein
   EN-Ziel gleich einem anderen DE-Slug und Einträge ohne Seite. Aufgerufen in `build_en.py::main()` (Abbruch
   per `SystemExit`) und am Anfang von `scripts/verify_seo_html.py::pruefe()` (Fehler → Deploy rot).

## Belege
`probe_i18n_sprache.js` 0 Fehler (Fall 6: `/wahlen`, `/wahlen/`, `/wahlen?snapshot=x#tabelle` → `/en/elections…`,
`pfad()`, Wechsel beider Richtungen, hreflang); `verify_seo_html` 0 Fehler; `verify_en` FAIL 0;
`verify_en_serverpfad` 9/9; Kollisions-Einzeltests (doppeltes Ziel, Ziel = fremder DE-Slug, Eintrag ohne Seite) rot.

## Prüfe besonders
- Ist die Kollisionsprüfung vollständig (z. B. EN-Ziel gleich dem EN-Ziel einer Seite OHNE Eintrag)?
- Bleiben Stellen, die `/en/<slug>` noch selbst zusammensetzen?

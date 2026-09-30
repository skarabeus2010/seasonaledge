# Review-Auftrag: EN-Köpfe / JSON-LD — CODE, Runde 4

Repo `C:\dev\Seasonaledge`. Fortsetzung von `2026-09-30_en_jsonld_code_runde3.md`. Prüfe `git diff`
(Schwerpunkt `shared/seo_basis.py::google_fonts_pruefung`, `scripts/verify_en_serverpfad.py`). Antwort
auf Deutsch, je Befund Schwere + Datei:Zeile + Änderung, am Ende genau eine Zeile `FREIGABE: ja` oder
`FREIGABE: nein`. `verify_en_serverpfad.py` schreibt ins System-Temp; unter read-only ggf. im
Arbeitsspeicher nachstellen wie zuvor.

## Umsetzung deines Befunds aus Runde 3
Statt die Regexe weiter zu flicken, ist `google_fonts_pruefung` jetzt **vollständig strukturell**:
`_KopfTags(HTMLParser)` liefert Ereignisse (link / noscript-Anfang / noscript-Ende / Text) mit
Quelloffsets (Zeilentabelle nur an `\n`, wie HTMLParser zählt). Kommentare sind keine Tags und zählen
damit weder als Hauptlink noch als Fallback. `_ist_stylesheet`: `rel`-Token `stylesheet`, nicht
`alternate`, kein `disabled`. Fallback verlangt: `<noscript>` direkt als nächstes Ereignis nach dem
Hauptlink, darin ein aktiver Stylesheet-Link mit derselben `href` und Medium leer/`all`/`screen`.
Paar = Quelltext vom Hauptlink bis `</noscript>`.

Neue negative Quellfälle: Fallback-Link auskommentiert, Fallback-Link `disabled` → Build bricht ab.

## Belege
`verify_en_serverpfad.py --mutationen`: 0 Fehler, 13/13 Mutationen, **8/8 Quellfälle** (2 positive:
`rel` vor `href`, Werte ohne Anführungszeichen). Alter Stand `2da452e`: 106 Fehler.
`verify_seo_html.py` 0 Fehler, `landing/verify_en.py` FAIL 0, `verify_seo_mutation.py` 30/30.

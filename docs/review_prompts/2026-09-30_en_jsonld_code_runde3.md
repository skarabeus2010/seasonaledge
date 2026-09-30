# Review-Auftrag: EN-Köpfe / JSON-LD — CODE, Runde 3

Repo `C:\dev\Seasonaledge`. Fortsetzung von `2026-09-30_en_jsonld_code_runde2.md`. Prüfe `git diff`
(Schwerpunkt `shared/seo_basis.py`, `scripts/verify_en_serverpfad.py`). Antwort auf Deutsch, je Befund
Schwere + Datei:Zeile + Änderung, am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.
Hinweis: `verify_en_serverpfad.py` schreibt ins System-Temp; unter read-only ggf. wie in Runde 2 im
Arbeitsspeicher nachstellen.

## Umsetzung deiner zwei Befunde aus Runde 2
1. **`_attrs` per Regex** → jetzt `html.parser.HTMLParser` (Werte mit/ohne Anführungszeichen, Groß-/
   Kleinschreibung). `rel` wird als Token-Liste gelesen (`stylesheet` enthalten, `alternate` nicht).
   Neuer positiver Quellfall „rel ohne Anführungszeichen" (`rel=stylesheet media=print`): baut, und
   `pruefe_en_kopf` bestätigt, dass das Font-Paar im EN-Ergebnis erhalten ist.
2. **Fallback nur per Textsuche** → `_fonts_fallback_wirksam(noscript, href)`: verlangt im `<noscript>`
   einen echten Stylesheet-Link mit **derselben** Font-URL wie der Hauptlink und wirksamem Medium
   (fehlend/leer/`all`/`screen`). Neue Mutation am Ergebnis und neuer Quellfall „noscript-Link ohne rel"
   → Wächter rot bzw. Build bricht ab.

## Belege
`verify_en_serverpfad.py --mutationen`: 0 Fehler, **13/13 Mutationen**, **6/6 Quellfälle**.
`verify_seo_html.py` 0 Fehler nach Neubau, `landing/verify_en.py` FAIL 0. Deine Deploy-Frage-Antwort
(Serverpfad-Test nicht im Deploy nötig) ist übernommen.

# Review-Auftrag: EN-Köpfe / JSON-LD — CODE, Runde 5

Repo `C:\dev\Seasonaledge`. Fortsetzung von `2026-09-30_en_jsonld_code_runde4.md`. Prüfe `git diff`.
Antwort auf Deutsch, je Befund Schwere + Datei:Zeile + Änderung, am Ende genau eine Zeile
`FREIGABE: ja` oder `FREIGABE: nein`. Serverpfad-Test ggf. im Arbeitsspeicher nachstellen wie zuvor.

## Umsetzung deines Befunds aus Runde 4
- `_KopfTags.handle_endtag`: Ende von `</noscript …>` = tatsächliche Position des schließenden `>` im
  Quelltext (`self._text.index(">", start) + 1`) statt fester Länge.
- Wächter: der CSS-Link-Vergleich in `pruefe_en_kopf` ist jetzt **strukturell** — neue Funktion
  `shared.seo_basis.aktive_stylesheets()` (HTMLParser, aktive Stylesheets außerhalb `<noscript>`);
  ein durch kaputtes Markup verschluckter `app.css`-Link fehlt damit und wird gemeldet. Die alte
  `CSS_LINK`-Regex ist entfernt.
- Neuer positiver Quellfall `</noscript >` (baut, 0 Fehler inkl. app.css-Vergleich) und neue
  Mutation „app.css verschluckt" (End-Tag ohne `>` vor dem app.css-Link) → gefangen.

## Belege
`verify_en_serverpfad.py --mutationen`: 0 Fehler, **14/14 Mutationen**, **9/9 Quellfälle**.
Alter Stand `2da452e`: 106 Fehler. `verify_seo_html.py` 0, `landing/verify_en.py` FAIL 0.

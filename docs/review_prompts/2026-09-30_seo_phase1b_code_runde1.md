# Review-Auftrag: SEO Phase 1b (Indexierung) — CODE, Runde 1

Repo `C:\dev\Seasonaledge`. Umsetzung von „Phase 1b" aus `docs/SEO_UMSETZUNGSPLAN_2026-09.md` (deine Plan-Freigabe:
`docs/review_prompts/2026-09-30_gsc_indexierung_runde3.md`). Prüfe mit `git diff` und den neuen Dateien.
Antwort auf Deutsch, je Befund Schwere + Datei:Zeile + Änderung, am Ende genau eine Zeile `FREIGABE: ja` oder
`FREIGABE: nein`. Noch nicht committet/deployt.

## Umsetzung
- **G1 (`landing/js/i18n.js`):** `_detectLang` bestimmt die Sprache nur noch aus der URL; keine Weiterleitung beim
  Laden (Browsersprache und `sa_lang` werden nicht mehr gelesen). Neu `_hatEN(pfad)` (Quelle `_EN_PAGE_META`,
  ohne Query/Fragment/abschließenden Slash) und `_zielFuer(lang)`: bevorzugt das hreflang-Gegenstück aus dem
  Seitenkopf (deckt Blog-Slugs ab), sonst `_EN_PAGE_META`; `null` = kein Gegenstück.
- **G2:** `_applyNavLinks` schreibt nur Links mit EN-Fassung um; `switchTo()` navigiert nur zu `_zielFuer`, sonst
  gar nicht; `_updateLangSwitch` deaktiviert den Knopf ohne Gegenstück (`disabled`, `aria-disabled`, Titel) und
  läuft jetzt auch auf DE-Seiten nach dem Nachladen der Navigation (`_onComponentLoaded`).
  `landing/build_en.py::rewrite_body_links` schreibt nur Pfade aus `_EN_PAGE_META` um.
  Acht fest verdrahtete `/en/ueber-uns`, `/en/dealer-positioning`, `/en/about`, `/en/rechtliches` in EN-Artikeln
  (Markdown) auf die DE-Seiten korrigiert — gefunden von der neuen Wächterprüfung. (Nicht angefasst: gleiche
  URLs in HTML-Kommentaren mit Social-Media-Entwürfen, werden nicht ausgeliefert.)
- **G3/G4:** `robots.txt`-Generator ohne `Disallow: /analyse/` und `/landing/data/`; `deploy/nginx.conf` neuer
  Block `location ~* ^/landing/data/.+\.json$` mit `X-Robots-Tag: noindex` (hinter der `.bak`-Sperre).
- **Wächter `scripts/verify_seo_html.py`:** Prüfung 7 = jeder `href="/en/…"` in jeder gebauten Seite zeigt auf
  eine gebaute Seite; Prüfung 8 = `robots.txt` sperrt `/analyse/` und `/landing/data/` nicht.
- **2b `scripts/js/probe_i18n_sprache.js`:** echter `i18n.js` in node mit DOM-Nachbau: 8 Seiten × 2 Browsersprachen
  × 3 Präferenzen ohne Weiterleitung und mit URL-Sprache; Link-Umschreibung nach Nachladen; `switchTo` auf Seiten
  ohne EN-Fassung ohne Wechsel und mit deaktiviertem Knopf; Blog über hreflang; EN→DE. Neu 0 Fehler, gegen
  `39556ab:landing/js/i18n.js` 20 Fehler. **Läuft nicht im Deploy** (weder Host noch Container haben node) —
  daher im lokalen Mutationstest `scripts/verify_seo_mutation.py` (neu: `pruefe_i18n_js`, zwei neue Mutationen) — Lauf: 30/30 Mutationen, hreflang-Regel und i18n-Test (neu rc 0, alt rc 1) grün; `verify_seo_html.py` 0 Fehler.

## Prüfe besonders
- Bricht die Umstellung Nutzerfunktionen (z. B. gespeicherte Sprachwahl — ist ohne Weiterleitung noch ein
  sinnvoller Zustand übrig? Watchlist/Profil/Kalender im EN-Modus)?
- `_zielFuer` bei Seiten, deren hreflang-Tags `_injectHreflang` auf EN-Seiten ersetzt; `/en/blog/…` ohne DE-Paar.
- nginx-Block: Regex, Reihenfolge, Header-Vererbung, gzip — trägt das?
- Reicht es, dass der JS-Test nur lokal läuft?

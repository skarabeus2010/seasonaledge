# Review-Auftrag: Eigene EN-Adressen, Runde 3

Repo `C:\dev\Seasonaledge`. Vorgeschichte: `docs/review_prompts/2026-10-07_en_slugs_runde{1,2}.md`. Prüfe den
Arbeitsstand (`git diff`), Schwerpunkt Korrektur zu Runde 2. Antwort auf Deutsch, je Befund Schwere +
Datei:Zeile + Änderung, am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.

## Korrekturen aus Runde 2
1. **Kollision EN-Ziel = fremder DE-Slug** (`{'wahlen':'elections','skew':'wahlen'}` blieb grün):
   `shared/seo_basis.py::pruefe_en_slugs` prüft jetzt jedes EN-Ziel aus `_EN_SLUGS` gegen ALLE DE-Seiten
   (`landing_de_slugs()` = `landing/pages/*.html` + `landing/*.html`), unabhängig von deren eigener Zuordnung.
   Regressionstest neu: `scripts/verify_en_slugs.py` (Bestand sauber, 5 Kollisionsfälle rot, en_slug/en_url).
2. **Präfixbildung in `tour.js:146`**: nutzt jetzt `SA.i18n.enHref` (neu exportiert), Rückfall nur ohne i18n.
   `i18n.js:405` (Laufzeit-Canonical) greift nur, wenn das Canonical noch kein `/en/` enthält — EN-Seiten sind
   vorgebacken und tragen bereits `/en/elections`; `build_en.py:441` betrifft nur die Startseiten-JSON-LD.

Hinweis: der `verify_seo_html`-Fehler „blog/output/midterm-wahltag-boerse fehlt" stammt von einem gleichzeitig
entstehenden Blogartikel (Entwurf, noch nicht gebaut) und gehört nicht zu diesem Auftrag.

## Belege
`verify_en_slugs` 0 Fehler (5 Kollisionsfälle erkannt), `probe_i18n_sprache` 0, `verify_en` FAIL 0,
`verify_en_serverpfad` 0 Fehler.

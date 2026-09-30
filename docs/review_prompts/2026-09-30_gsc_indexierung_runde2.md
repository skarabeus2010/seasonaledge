# Review-Auftrag Runde 2: GSC-Indexierung — Plan

Repo `C:\dev\Seasonaledge`. Runde 1: `docs/review_prompts/2026-09-30_gsc_indexierung.md`, FREIGABE nein, 8 Befunde.
Alle übernommen. Deinen Befund zur automatischen Sprachweiterleitung habe ich am Code bestätigt
(`landing/js/i18n.js::_detectLang`, auch Startseite betroffen) und die EN-Startseite live geprüft: Links auf
`/en/crash-fruehwarnung` (404), `/en/ueber-uns` (404), `/en/congress` und `/en/index-effekt` (301).
Überarbeiteter Plan: Abschnitt **„Phase 1b"** am Ende von `docs/SEO_UMSETZUNGSPLAN_2026-09.md` (Befunde G1–G7, Plan 1–7).
Zu deinem Punkt 8: die lokalen lastmod-Abweichungen kamen von einer vor dem Commit gebauten Sitemap; auf dem
Server lief der Wächter nach dem Deploy mit 0 Fehlern.

Prüfe den Plan erneut. Antwort auf Deutsch, je Befund Schwere + Beleg + Änderung, am Ende genau eine Zeile
`FREIGABE: ja` oder `FREIGABE: nein`.

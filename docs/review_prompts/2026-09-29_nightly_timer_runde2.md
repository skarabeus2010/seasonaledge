# Review-Auftrag Runde 2: Nightly auf systemd-Timer

Repo `C:\dev\Seasonaledge`. Runde 1: `docs/review_prompts/2026-09-29_nightly_timer_runde1.md`. Deine Befunde:

1. **Polymarket doppelt** → Phase G (Snapshot + Montags-Backfill) UND Phase H (Brier) aus `scripts/nightly_refresh.py`
   entfernt. Beide hatten bereits eigene, laufende Auslöser: `polymarket_daily.yml` (täglich 21:30, letzte 5 Läufe
   success) und `brier_compute.yml` (sonntags 02:00, mit vorherigem Scrape; Health-Check „Brier zuletzt 27.09.").
   Genau ein Auslöser pro Aufgabe. Kommentar in `polymarket_daily.yml` nennt jetzt die gefundene Ursache.
2. **Log-Fehler im Newsletter verschluckt** → `_log()` gibt `bool` zurück; scheitert das Log nach einem Live-Versand,
   endet der Lauf mit Exit 6 (die Fehlerpfade 2/3/4/5 sind ohnehin ≠ 0).

Deine Hinweise: Installer-Kommentar zu `Persistent=true` präzisiert (Sofortlauf nur nach verpasstem Termin, gewollt).
Ein beim Deploy schon laufender Cron-Nightly wird nicht beendet — einmaliger Übergang, akzeptiert (der Deploy
geschieht tagsüber, der Cron-Termin ist 20:30 UTC).

Prüfe Korrekturen und Gesamtstand (`git diff`, `deploy/systemd/sa-nightly.*`). Antwort auf Deutsch, je Befund
Schwere + Datei:Zeile + Änderung, am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.

# Code-Review: drei kleine Posten (16.10.)

Read-only, Deutsch, **FREIGABE (Code): ja/nein**, Befunde P1/P2/P3. Code uncommittet (`git diff`).

1. **Health-Check prüft die Auslieferung der Options-Dateien über HTTP** (`scripts/daily_health_check.py`:
   `_http_auslieferung`, `OPTIONS_DATEIEN`; Check „Options: Auslieferung (HTTP)“). Anlass 2026-09-11: das atomare
   Schreiben setzte 0600, nginx lieferte 403, alle Inhaltsprüfungen waren grün. HEAD je Datei, ohne Weiterleitungen;
   200 = grün, jeder andere Status = rot, Netzfehler = gelb („ungeprüft“). Der Health-Lauf läuft im App-Container
   (`docker exec`), der die öffentliche Domain erreicht. Tests in `scripts/verify_gex_session.py` (5 Fälle); echter
   Abruf gegen die Live-Seite: grün, 6 Dateien.
   Frage: HEAD statt GET — liefert nginx bei HEAD dieselbe Berechtigungsprüfung (403 bei 0600)?
2. **Skew-History ohne Einrückung** (`shared/atomic_json.history_aktualisieren`: `indent=None`). Nur die Skew-History
   nutzt diese Funktion (Cron, Massive-Backfill, VRP-Reparatur). 11,0 → 8,1 MB roh, über gzip 1,07 → 1,01 MB. Kein
   Leser arbeitet zeilenweise (gesucht in scripts/, shared/, landing/js, deploy/).
3. **Marktkalender ohne Earnings** (`landing/js/kalender-compute.js`, `landing/pages/kalender.html` Legende):
   `earnings_events.report_date` ist das Quartalsende (fetch_event_data.py übernimmt `earningsHistory.quarter`), kein
   Termin — wie in der Morgen-Mail seit 14.10. (Paket A). Dividenden bleiben. Die Seite ist auth-gesperrt, ohne EN.
   Frage: fehlt etwas (ICS-Export, Filterchips), das noch Earnings erwartet?

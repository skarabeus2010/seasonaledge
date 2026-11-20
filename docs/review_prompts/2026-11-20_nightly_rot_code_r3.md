# Code-Review Runde 3: Reparatur Nightly rot — Codex, read-only
Runde 2: docs/review_prompts/2026-11-20_nightly_rot_code_r2_antwort.md. Ändere NICHTS. Deutsch. Je Befund erledigt?, neue Befunde, Urteil.
1. Strategietreffen: jetzt (2027,10,27) in FOMC_STRATEGIE_TREFFEN, (2027,11,17) regulär in FOMC_MEETING_DATES und fomc-dates.js
   (Fed-HTML: der Hinweis steht in der Oktober-Zeile, Spalte fomc-meeting__minutes); verify_calendar_rules prüft beide Richtungen.
2. Öffentliche Statistik-Upserts: verify_db_wiederholung.py Fall 10c ruft upsert_monthly_stats / upsert_tdoy_stats /
   upsert_tdom_stats (Fehler im 2. Batch) auf; dein Rückbau ohne Wiederholung macht alle drei rot.
   Nightly-Aggregation: verify_nightly_phasen.py neuer Fall — fuer_ticker wirft, das ECHTE except in refresh_ticker_data
   muss „Saison-Score (1 …" in _FEHLGESCHLAGEN schreiben; Mutation `saison_fehler.append` → `pass` macht ihn rot (37/38).

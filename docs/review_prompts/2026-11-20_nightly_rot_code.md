# Code-Review: Reparatur Nightly rot (Runde 1) — Codex, read-only

Du hast die Diagnose geliefert (docs/review_prompts/2026-11-20_nightly_rot_diagnose_antwort.md). Jetzt den Code prüfen.
Ändere NICHTS. Antworte auf Deutsch: Befunde nummeriert mit Datei:Zeile, dann Urteil FREIGABE / NICHT FREIGABEFÄHIG.

Geändert (git diff, unstaged):
- NEU shared/db_wiederholung.py — Klassifikation (57014, httpx RemoteProtocolError/TimeoutException/NetworkError über die Ursachenkette), mit_wiederholung(aufgabe(neuer_client)), 3 Versuche, Backoff.
- shared/stress_score.py — _lade_einmal (Zählung + Keyset .gt("date", letztes).order.limit(1000), Cursor streng aufsteigend), lade_kurse(ticker, client, client_factory, log): vollständiger Neuversuch, nach Transportfehler factory(force_new=True); ohne Factory → LadeFehler.
- shared/saison_score_betrieb.py fuer_ticker(client_factory=...); scripts/nightly_refresh.py und scripts/full_scanner_run.py reichen get_client als Factory.
- shared/supabase_client.py — _upsert_wiederholt für monthly_stats, tdom_stats (je Batch), tdoy_stats.
- shared/tdom_analysis.py calc_strategy_returns — nur endliche, positive Ein-/Ausstiegskurse, sonst NaN.
- scripts/verify_db_wiederholung.py (neuer Wächter, im Gate), scripts/verify_stress_ampel.py (Fake kann .gt), scripts/verify_nightly_phasen.py (Stub-Signatur), .github/workflows/deploy.yml (Gate-Schritt).
- Nebenbei im selben Commit (vorher abgestimmt): FOMC-/Minutes-Korrekturen shared/fed_dates.py, shared/central_banks.py, landing/js/fomc-dates.js, landing/pages/zentralbanken.html, scripts/verify_calendar_rules.py.

Bitte besonders prüfen:
1. Kann irgendein Pfad eine Teilreihe oder einen alten Score als Erfolg liefern?
2. Ist `_lade_einmal` mit `add_note` + re-raise korrekt (Python 3.11+ im Container)? Wird LadeFehler aus versuch() korrekt NICHT wiederholt?
3. `_upsert_wiederholt`: get_client(force_new=neu) setzt den globalen Client zurück — Nebenwirkungen auf andere Halter alter Referenzen im Nightly (z. B. `schreibe(_get_client(), …)`)?
4. Keyset: PostgREST `gt` auf `date` (Typ date) mit ISO-String; Zählung vs. Seiten; Dubletten-Prüfung als String-Vergleich.
5. calc_strategy_returns: ändert die Maskierung Ergebnisse für saubere Daten (Zwillinge/Seiten/Newsletter)? Wer nutzt die Funktion noch?
6. Deckt der Wächter die Fehlerklassen echt ab (nicht nur eigene Attrappen-Semantik)?

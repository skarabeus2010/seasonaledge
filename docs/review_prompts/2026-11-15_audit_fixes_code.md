# Code-Prüfung — Reparaturen aus dem Audit 2026-11-15 (Codex, nur lesend)

Grundlage: dein Audit ([2026-11-15_audit_codex.md](2026-11-15_audit_codex.md)), Befunde 3, 4, 5, 9, 10, 13 (teilweise)
und 1 (getAll). Der Nutzer hat vier Pakete freigegeben; Paket 1 (SOXX-Split, DB) ist erledigt und nicht Teil dieses Diffs.
Prüfe `git diff` (Arbeitsbaum gegen HEAD) und die neuen Dateien:

- `scripts/nightly_refresh.py` — refresh_log jetzt NACH Phase J/K (`refresh_log_eintrag`, `_schreibe_refresh_log`),
  gescheiterte Phasen als `PHASE: …` vorn in `errors`; Kalender/CPI/Backfill/Stress/refresh_log selbst → `_FEHLGESCHLAGEN`;
  TDOM/TDOY mit `schreibfehler_werfen=True`; neue Phase K baut den Marktkalender.
- `shared/cache_manager.py` — `schreibfehler_werfen` für tdom/tdoy (wie monthly).
- `scripts/daily_health_check.py` — `bewerte_nightly` (PHASE → rot), `bewerte_nightly_ausgaben` (Alter von
  market_calendar.json/.ics, chart-data.json, wahlen_study.json + Inhalt des Kalenders).
- `landing/js/app.js` — `getAll` lehnt eine Nicht-Liste ab statt den Teilbestand zu liefern.
- `deploy/inject_credentials.sh`, `.github/workflows/deploy.yml` — Kalender im Container statt Host-python3; zwei Wächter im Gate.
- `shared/indicators.py`, `landing/js/indicators.js` — Python an JS angeglichen (EMA SMA-Start, RSI Wilder, Bollinger
  ddof=0, MACD/LBR über `calc_ema`); JS-RSI: ohne Verlust 100, flach `null`.
- Neu: `scripts/verify_nightly_phasen.py` (+ `_mutation`, 13/13), `scripts/verify_indikator_zwillinge.py` (+ `_mutation`, 7/7).

Gemessen (Server, nur lesend): Mail-Score bei 86 von 372 Tickern ±1 durch die Indikator-Angleichung (vor allem RSI(3)).

Fragen:
1. Kann ein Nightly jetzt noch rot enden, während die Health-Mail grün zeigt? Gibt es einen Pfad ohne refresh_log-Zeile,
   der grün bleibt (die Altersprüfung greift erst nach einem Tag)?
2. Verdrängt die neue Reihenfolge etwas (Stress-Text in der Mail — Nutzerregel „keine Ampel in Mails“; Weekly-Phase F)?
3. `getAll`: bricht die Ablehnung einen Aufrufer, der bisher mit dem Teilbestand lief (`polymarket.html`, `crash-fruehwarnung.html`)?
4. Indikatoren: sind die neuen Definitionen korrekt (Wilder-Start, NaN-Behandlung in `calc_rsi`/`_ema_werte`, MACD-Signal
   über die gültige MACD-Linie wie JS)? Gibt es weitere Python-Aufrufer, die sich auf das alte Verhalten verlassen
   (z. B. `shared/strategies/plain_vanilla.py` LBR, Backtests)?
5. Prüfen die Wächter die Wirkung oder nur Text? Fehlt eine Mutation, die durchkäme?

Schluss: FREIGABE, FREIGABE MIT AUFLAGEN oder NICHT FREIGABEFÄHIG, je Befund Datei:Zeile + Fehlerfall.

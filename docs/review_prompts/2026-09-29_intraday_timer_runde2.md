# Review-Auftrag Runde 2: Stündliche Jobs auf systemd-Timer

Repo `C:\dev\Seasonaledge`. Runde 1: `docs/review_prompts/2026-09-29_intraday_timer_runde1.md`, deine drei Befunde:

1. **HOCH Polymarket 0/26 grün** → neue Funktion `bewerte_polymarket_intraday(row, now)` in
   `scripts/daily_health_check.py`: `missing_details` wird als JSON gelesen, Skip nur bei
   `{"skip": <wahr>}`; ohne Skip und `tickers_success == 0` → rot; zu alt → rot; keine Zeile → rot.
2. **MITTEL `install_timers.sh` während eines Laufs** → Timer-`SubState` wird gelesen: `running` wird
   akzeptiert, wenn der Service laut `Unit=` gerade `activating` ist; `waiting` verlangt einen nächsten
   Termin; jeder andere Zustand ist ein Fehler.
3. **MITTEL leerer Marktbestand** → im `--near-fomc-only`-Modus Log-Zeile mit Fehler + Exit 1; der tägliche
   Aufruf ohne Flag bleibt Exit 0 (unverändertes Verhalten).

Tests (lokal): `bewerte_polymarket_intraday` 8 Fälle (Skip frisch grün, Skip alt rot, 0/26 rot, 25/26 grün,
0/0 rot, kaputtes JSON rot, das Wort „skip" in einem anderen Feld rot, keine Zeile rot);
`polymarket_refresh.main` mit gestubbtem FOMC-Gate/YAML/Log: leerer Bestand FOMC → rc 1 + 1 Log,
leerer Bestand täglich → rc 0 + 0 Logs, Skip → rc 0 + Skip-Log. Alle wie erwartet.

Zu deinem Nebenbefund (täglicher Polymarket-Workflow verdeckt Fehler durch `| tail` + `echo`): vorbestehend,
außerhalb des Umfangs, wird dem Nutzer als offener Punkt gemeldet.

Prüfe die Korrekturen und den Gesamtstand erneut (`git diff`, neue Dateien unter `deploy/`).
Antwort auf Deutsch, je Befund Schwere + Datei:Zeile + Änderung. Am Ende genau eine Zeile
`FREIGABE: ja` oder `FREIGABE: nein`.

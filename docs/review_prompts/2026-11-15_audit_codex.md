# Audit 2026-11-15 — Fehler und unvollständige Daten (Codex, nur lesend)

Auftrag des Nutzers: „Wo haben wir Fehler, wo sind Daten unvollständig?“ Ich (Claude) messe parallel den
Live-Zustand auf dem Server (DB, Crons, Dateien, HTTP). Du prüfst den **Code** — nur lesend, keine Änderungen.

## Bekannt (nicht erneut melden, außer du findest einen neuen Mechanismus)
- Supabase-Ausfall 11.–13.11. (Projekt pausiert, danach Nano/fehlendes ANALYZE) — CLAUDE.md v66.28.
- Nightly 14.11. rot: Saison-Score ^GSPC `statement timeout` (57014).
- Offene Posten in CLAUDE.md-TODO (VRP-Nachrechnung, Phantomzeilen an Feiertagen, DOGE 4 Nachkommastellen,
  `dividend_events` nur Vergangenheit, Kalender V3 offen, NESN.SW → NYSE in `holidays.js::detect`).

## Fragen (je Befund: Datei:Zeile, Mechanismus, konkreter Fehlerfall, Schwere hoch/mittel/niedrig)
1. **Stille Fehler:** Wo endet ein Lauf mit Exit 0 / grün, obwohl nichts oder Altes geschrieben wurde? Prüfe
   `scripts/nightly_refresh.py`, `scripts/intraday_refresh.py`, `scripts/full_scanner_run.py`,
   `scripts/compute_options_skew.py`, `scripts/snapshot_gex_massive.py`, `scripts/compute_key_levels*.py`,
   `scripts/polymarket_*`, `scripts/daily_newsletter.py`, `scripts/daily_health_check.py` (bzw. wie die Dateien heißen).
2. **Zeitüberschreitungen:** Welche Supabase-Abfragen laden große Bereiche (ganze Historie, ohne Index-taugliche
   Filter, `count=exact`, Paginierung ohne Keyset) und kippen bei langsamer DB in `57014`? Gibt es Wiederholung?
   Wird ein Timeout als „keine Daten“ statt als Fehler behandelt?
3. **Alter Wert in der Rolle des aktuellen:** Wo fällt ein Leser bei fehlender/veralteter Quelle auf einen alten
   Wert zurück, ohne Datum oder Kennzeichnung (Mail, Seiten, JSON unter `landing/data/`)?
4. **Health-Check-Lücken:** Welche produzierten Dateien/Tabellen prüft `daily_health_check` NICHT auf Frische?
   (Vergleiche mit allen Writern unter `landing/data/` und den Tabellen, die Seiten lesen.)
5. **Zwillinge:** Python/JS-Paare mit noch abweichender Logik (z. B. RSI in `indicators.js` vs.
   `shared/indicators.py`: JS RSI(2) [1,2,3,4] = 99,0099, Python NaN — bestätigen und weitere finden).
6. **Universum:** Ticker in `shared/symbols.py` ohne Kalender-Mapping, in `options_universe.py` aber nicht in
   `symbols.py`, oder umgekehrt; ausgeschiedene Ticker (`AUSGESCHIEDEN`), die noch irgendwo gelesen werden.

Ausgabe: nummerierte Befundliste, Schwere zuerst, je mit Beleg im Code. Zum Schluss: was du NICHT prüfen konntest.

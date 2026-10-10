# Paket 3 (K3+K4) — Code-Review Runde 3 (Abnahme)

Runde 2: [Prompt](2026-10-10_kalender_paket3_code_runde2.md) · [Antwort](2026-10-10_kalender_paket3_code_antwort2.md) — keine Freigabe (drei Befunde).

<task>Prüfe, ob die drei Befunde aus Runde 2 behoben sind und nichts Neues kaputtging. Read-only. `git diff` + neue Dateien.</task>

## Umsetzung
1. **Intraday-Teilnummern** (P1): im Fehlerzweig `df = df.drop(columns=["tdoy", "tdom"], errors="ignore")` —
   die Zeilen gehen ohne Nummern raus. Probe: Kalenderfehler am zweiten Datum (Stub um `is_trading_day`) →
   Exit 1 und keine geschriebene Zeile mit `tdoy`/`tdom`.
2. **Globaler Health-Abbruch** (P2): der äußere `except` in `health_check` trägt zusätzlich einen Fehlertext
   in `errors` ein und markiert **alle** Ticker als ungeprüft. Probe: `get_client()` wirft → alle ungeprüft,
   gescheitert, Fehlerliste nicht leer.
3. **Nightly-Exit im Wächter** (P2): neuer Block führt den **echten `nightly_refresh.main()`** aus — Supabase,
   CPI, Stress, Spot-Vol-Beta, `subprocess.run`, Kalender-Sync, Ticker-Refresh und Heartbeat gestubbt.
   Grundlinie: Exit 0 und `tickers_success` = alle; mit einem SYMBOLS-Eintrag ohne Kalender: Exit 1,
   „Health-Check …“ in `_FEHLGESCHLAGEN`, `tickers_success` zählt ihn nicht. Deine Mutation
   (`_FEHLGESCHLAGEN.extend` entfernt) ist im Mutationstest — wird gefangen.
   Probe 15/15, Mutationen **11/11** (zweimal), Gegenproben 2/2.

## Fragen
1. Befunde behoben? 2. Prüfen die Stubs im Hauptlauf etwas Echtes, oder könnte der Block auch ohne die
Korrektur grün sein (z. B. weil eine gestubbte Phase `_FEHLGESCHLAGEN` ohnehin füllt)? 3. Sonst etwas?

## Ausgabevertrag
**Urteil** · **Befunde** · **Antworten**. ≤ 40 Zeilen.

# Code-Prüfung Runde 2 — Reparaturen aus dem Audit 2026-11-15 (Codex, nur lesend)

Runde 1 ([Auftrag](2026-11-15_audit_fixes_code.md)): NICHT FREIGABEFÄHIG, drei Befunde. Umgesetzt (Arbeitsbaum gegen HEAD):

1. **Lauf ohne Logzeile.** `scripts/daily_health_check.py`: `erwarteter_nightly_tag(now_utc)` (letzter Start 16:45
   New York, der ≥ 3 h zurückliegt, als UTC-Datum = `run_date`), `bewerte_nightly(…, erwartet)` → rot, wenn die letzte
   Zeile älter ist; Check 1 als `pruefe_nightly(client, now_utc)`, vom Wächter mit Attrappe ausgeführt.
   **Meine Nachrechnung zu deinem Befund:** am geplanten Health-Lauf (05:00 UTC) war die Lücke schon von der Altersregel
   gedeckt — scheitert der Eintrag des Vortags, ist die letzte Zeile 2 Tage alt → rot. Deine Reproduktion (Zeile 14.11.,
   Check 15.11.) ist der Normalfall: der Lauf des 15.11. startet erst 21:45 UTC. Mit der Erwartung bleibt kein Fenster;
   ohne sie war eines im Sommer 23:45–24:00 UTC (Start 20:45 UTC + 3 h). Bitte prüfen, ob die Rechnung stimmt.
2. **Lückenvertrag Indikatoren.** Python und JS gleich: SMA/Bollinger — Fenster mit Lücke unbestimmt; EMA/RSI/MACD/LBR —
   auf den gültigen Kursen gerechnet, Ergebnis an deren Stellen, Lücke bleibt unbestimmt. JS: `_gueltig`, `_aufGueltigen`,
   `calcSMA` mit Lückenprüfung, MACD-Signal direkt `calcEMA(macdLine)`. Dein Gegenbeispiel `[1,2,fehlend,1,3,2]` RSI(2)
   = 50 auf beiden Seiten.
3. **Histogramme.** Wächter vergleicht `macd_h`/`lbr_h` (Python = JS) und prüft Histogramm = Linie − Signal je Seite;
   Vorzeichenmutation Python und JS.

Wächter: `verify_nightly_phasen.py` 37/37, Mutationen 16/16; `verify_indikator_zwillinge.py` 141/141 (Reihen mit Lücken
vorn/innen/hinten), Mutationen 12/12. Lokales Gate grün bis auf die drei bekannten Windows-Fälle ohne `flock`.

Fragen: Sind die drei Befunde geschlossen? Neue Fehler durch die JS-Umstellung (Aufrufer von `calcSMA`/`calcEMA`, die
`null` oder Nicht-Zahlen übergeben, z. B. `indicators.js` Regime/Momentum, Seiten)? Schluss: FREIGABE, FREIGABE MIT
AUFLAGEN oder NICHT FREIGABEFÄHIG.

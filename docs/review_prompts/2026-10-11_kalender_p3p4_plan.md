# Tage nach Börsenkalender — Plan P3/P4 (Leser + Seiten), Runde 1

Grundlage: [Bestandsaufnahme](2026-10-11_kalender_p3_bestand_antwort1.md) (Codex), Plan [v3](2026-10-10_xetra_tdoy_plan_v3.md)/[v7](2026-10-10_xetra_tdoy_plan_v7.md).
Stand: P1a/P1b/P2 live (`shared/exchange_holidays.handelstag_nummern`, `landing/js/boersenkalender.js` isoliert,
Schreiber setzen `prices.tdom/tdoy` nach Kalender). **Nutzerentscheidungen 2026-10-11:** (1) betroffene
veröffentlichte Zahlen nachrechnen und Artikel mit `updated:` aktualisieren; (2) P3/P4 starten; P5 (historische
DB-Spalte) bleibt eine eigene Freigabe. Read-only.

<task>Prüfe den Plan auf Lücken, falsche Reihenfolge und fehlende Nachweise, BEVOR Code entsteht.</task>

## Gemessen (Vorab)
Down-Month-ToM-Reversal (Blog 2026-07-31 + Engine-Preset): `scripts/ml/backtest_new_filters.py` reproduziert die
veröffentlichten Zahlen exakt (SPY bis 2026-07-31: n 186/78, WR 68,3/71,8 %, PF 1,80/2,39, Sharpe 0,214/0,336,
DD 22,3/18,3 %). Mit TDOM nach NYSE-Kalender (`is_trading_day`): n 186/77, WR 70,4/72,7 %, PF 1,85/2,44, Sharpe
0,223/0,345, DD 21,6/18,1 %; 181 von ~1000 Ereignistagen 2011–2026 verschieden.

## Pakete (Vorschlag)
**P3a — Browserkalender auf `SA.boersenkalender` (Kern von P4).** `SA.holidays` (detect, isTradingDay,
nextTradingDay, goodFriday, Listen) wird eine Fassade über `SA.boersenkalender` + `symbols`-Zuordnung (dieselbe
Ticker→Börse-Regel wie Python, unbekannt → Fehler statt NYSE); `boersenkalender.js` in alle Seiten mit
`holidays.js`. Vorher/nachher je Seite mit der Seitenprobe (jsdom) — erwartete Unterschiede nur dort, wo der alte
Browserkalender falsch war (LSE 42 Tage 1994–2026, NYSE 27.04.1994, Forex, Ticker ohne Zuordnung). Die alten
Kalenderdaten in `holidays.js` entfallen.
**P3b — Header** (`app.js:772–853`): TDOM/TDOY aus `SA.boersenkalender.nummern` für das heutige Datum der Börse,
an Nicht-Handelstagen der letzte Handelstag (gleicher Monat/Jahr geprüft) statt der letzten DB-Zeile.
**P3c — Backtest-Engine** (`makeTdomEvents` Mo–Fr → Kalender der Tickerbörse; OPEX über die gemeinsame
OPEX-Regel mit Feiertagsverschiebung; eigene NYSE-Feiertagsliste raus). Presets auf der Seite (GLD/Silber/BTC/QQQ/
DAX/SPY) neu rechnen; Krypto 7 Tage.
**P3d — Newsletter**: Weekly (`weekly_report.py` Mo–Fr-TDOM, gleiche Nummer für alle Ticker) und Daily
(`daily_report.py` NYSE-TDOM für EU-Aktien in den Top-Listen) über `handelstag_nummern` je Tickerbörse.
**P3e — Converter** (`seo/tools/trading-day-converter.html`, eigene NYSE-Liste 2024–2027, UTC-Verschiebung) auf
`boersenkalender.js`; Börsenauswahl.
**P3f — Feiertage-Seite**: Literale „NYSE 10/XETRA 10/LSE 8" → aus dem Kalender je Jahr; LSE-Ersatztage.
**P3g — Statistiken (P6-Vorbereitung)**: `tdom_analysis.add_tdom_columns`/`tdoy_analysis` (Zeilenzählung) →
Kalendernummern über `handelstag_nummern`; `tdom_stats`/`tdoy_stats` hinter `methode='kalender_v1'`, Leser wählen
genau eine Generation; Umschaltung erst nach P5 (Schreibruhe → P5 → P6 → Leser), wie in v3 festgelegt.
**P3h — Veröffentlichte Zahlen**: Down-Month-Artikel DE+EN + Preset nachrechnen (Faktenblatt-Skript, eingefrorener
Stichtag 2026-07-31), `updated:`; für Monthly 10, ToM-Artikel, VIXpiration, Independence Day: Nachrechnung mit
Kalendernummern auf dem Stand des Artikels — nur bei Abweichung ändern.

Reihenfolge: P3a (Fundament) → P3b/P3c/P3e/P3f (Browser) → P3d (Python) → P3h (Texte) → P3g erst mit P5/P6.

## Fokusfragen
1. Fehlt ein Leser aus der Bestandsaufnahme (z. B. `tdom-analyse` TDOY Top 25 liest `prices.tdoy` direkt — gehört
   das zu P5)? 2. Ist P3a als EIN Schritt richtig (alle Seiten gleichzeitig) oder seitenweise? 3. OPEX/VIX auf
   `/opex` und `/vixpiration`: sollen Ereignistermine für Nicht-US-Ticker beim NYSE bleiben (Optionsverfall ist ein
   US-Ereignis), nur die Fensterzählung nach Tickerbörse? 4. Reicht für P3h die Nachrechnung auf heutigem
   Yahoo-Stand (Adjustierung wandert) oder braucht es einen Snapshot je Artikel?

## Ausgabevertrag
**Urteil** · **Antworten** · **Befunde** · **Auflagen**. ≤ 60 Zeilen.

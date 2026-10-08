# Code-Review Phase 1A /plain-vanilla, Runde 3

Repo `C:\dev\Seasonaledge`, Arbeitsstand. Vorgeschichte: `..._1a_code_runde{1,2}.md` + Antworten. Prüfe die Korrekturen
zu deinen drei Befunden aus Runde 2 und den Code auf neue Fehler. Antwort auf Deutsch: je Befund Schwere + Datei:Zeile +
konkreter Eingabefall + Änderung; am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.
Python: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`.

## Korrekturen
1. `_nthLastTradingDay` (JS) / `_nth_last_trading_day` (Python): liegt die letzte Monatssitzung laut Kalender nach der
   letzten Kurszeile (Monat unvollständig), gilt der Kalendertermin (`_terminZustand`), nicht die Rückwärtszählung ab der
   letzten Zeile. Fall: Kurse bis 29.10.2026 → Month-End-Einstieg 29.10., offen.
2. Python `calc_monthly_10` am Datenrand wie JS: vorhandene Monatszeilen + Kalendertermine nach der letzten Zeile als
   `Termin`, Blöcke daraus. Fall: Kurse 01.–21.10.2026 → geschlossen nur 01.10.→06.10. und 13.10.→16.10. (beide Sprachen).
3. Messlauf speichert die Protokolleinträge einzeln mit Datum (`protokoll`), Zähler zusätzlich (`protokoll_zaehler`).

## Belege
`verify_plain_vanilla_1a.py` 48/48, `--mutationen` 44/44 + 3/3 untaugliche verworfen; Messlauf gültig; historische Trades
bis Ende 2025 aller Strategien auf allen fünf Tickern auf 2 Stellen identisch mit dem alten Stand — ausgenommen die bewusst
korrigierten (One-Day-Holiday/UHTS durch den Kalender, Santa, LBR).

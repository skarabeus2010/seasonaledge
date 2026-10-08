# Code-Review Phase 1A /plain-vanilla, Runde 4

Repo `C:\dev\Seasonaledge`, Arbeitsstand. Vorgeschichte: `..._1a_code_runde{1,2,3}.md` + Antworten. Prüfe die Korrektur
zu deinem Befund aus Runde 3 und den Code auf neue Fehler. Antwort auf Deutsch: je Befund Schwere + Datei:Zeile +
konkreter Eingabefall + Änderung; am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.
Python: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`.

## Korrektur
1. Neu `shared/strategies/plain_vanilla.py::auswerten(df, key, *, boerse, stichtag=None, stop_df, stop_pct, stop_type)`:
   einziger Rechenweg der Python-Seite (E9, Zwilling von `SA.strategy.auswerten`). Setzt Stichtag (Standard: `heute(boerse)`
   in der Zeitzone der Börse, wie `SA.strategy.heute`) und Börse, rechnet Strategie → Stop → Kennzahlen und stellt den
   vorherigen Kontext im `finally` wieder her — auch bei Ausnahme. Ohne Börse `ValueError`.
2. `pages/09_Plain_Vanilla_Strategien.py::_calc_strategy` ruft nur noch
   `auswerten(df, key, boerse=get_exchange_for_holidays(ticker), …)`; der direkte `STRATEGIES[key]["func"](df)` ist weg.
   Weitere Python-Aufrufer, die Trades rechnen, gibt es nicht (`07_Januar_Trifecta.py` liest nur die Metadaten-Registry).

## Belege
`verify_plain_vanilla_1a.py` 50/50, neu:
- `py_xetra_kontext` — dein Fall über `auswerten`: XETRA-Kurse 01.–30.12.2025, 29.12. = 117, 30.12. = 118, Post-Christmas
  → geschlossen am 30.12. mit (118/117 − 1)·100 = +0,8547 %, Kennzahlen nicht leer; fremder Vorkontext (2020-01-01, NYSE)
  ist danach unverändert, auch nach einer Ausnahme (unbekannter Schlüssel).
- `streamlit_kontext` — statisch: `_calc_strategy` (bis zum abschließenden `return`) ruft `auswerten` mit
  `get_exchange_for_holidays(ticker)` und keinen direkten Strategieaufruf.

`--mutationen` 47/47 + 3/3 untaugliche verworfen; drei neue Mutationen: Börse nicht gesetzt, Kontext nicht
zurückgesetzt, Seite mit festem `"NYSE"`.

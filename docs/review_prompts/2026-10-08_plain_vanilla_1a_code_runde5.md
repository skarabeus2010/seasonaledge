# Code-Review Phase 1A /plain-vanilla, Runde 5

Repo `C:\dev\Seasonaledge`, Arbeitsstand. Vorgeschichte: `..._1a_code_runde{1,2,3,4}.md` + Antworten. Prüfe die
Korrekturen zu deinen zwei Befunden aus Runde 4 und den Code auf neue Fehler. Antwort auf Deutsch: je Befund Schwere +
Datei:Zeile + konkreter Eingabefall + Änderung; am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.
Python: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`.

## Korrekturen
1. **Kontext je Ausführungskontext isoliert.** `shared/strategies/plain_vanilla.py`: das modulweite `_KONTEXT`-dict ist
   ersetzt durch `_KONTEXT_VAR: ContextVar`; `set_kontext` setzt ein neues dict und liefert das Token, `_ctx` liest über
   `_kontext()`, `auswerten` setzt den Kontext und ruft im `finally` `_KONTEXT_VAR.reset(token)`. Streamlit führt jede
   Sitzung in einem eigenen Thread aus; ein neuer Thread sieht den Kontext eines anderen nicht.
2. **Veraltet-Filter in Python wie JS (E1/E7).** Neu `_daten_veraltet(df)` als Zwilling von `_datenVeraltet` (mehr als 10
   Kalendersitzungen nach der letzten Kurszeile bis zum Stichtag). `auswerten`: Strategie → Stop → bei veraltetem Bestand
   die verbliebenen OFFENEN Trades nach `unvollstaendig`; Rückgabe zusätzlich `veraltet`, `unvollstaendig`. Durch den Stop
   geschlossene Trades bleiben.

## Belege
`verify_plain_vanilla_1a.py` 52/52, neu:
- `py_kontext_parallel` — zwei Threads (XETRA / NYSE) über `auswerten` mit deinen Dezemberkursen; eine Strategie-Hülle mit
  zwei Barrieren erzwingt, dass beide rechnen, während beide Kontexte gesetzt sind. Soll: XETRA geschlossen 30.12., NYSE
  offen; Hauptkontext unverändert.
- `py_veraltet` — NYSE-Kurse 01.09.–31.12.2025: Stichtag 15.01.2026 (10 Sitzungen) → nicht veraltet, offener Trade bleibt;
  16.01.2026 (11 Sitzungen) → veraltet, offener Trade in `unvollstaendig`; dein Fall 08.10.2026 → kein offener Trade;
  mit 8-%-Stop und Kurssturz ab 15.10.2025 bleibt der Stop-Trade geschlossen erhalten.

`--mutationen` 51/51 + 3/3 untaugliche verworfen; neue Mutationen: gemeinsamer Kontext statt ContextVar, kein
Veraltet-Filter, Grenze `< 10` statt `<= 10`, Filter vor dem Stop. Die Parallel-Mutation fiel mit nur einer Barriere in
einem von drei Läufen zufällig durch (ein Thread schrieb beim Zurücksetzen den Wert des anderen zurück) — mit zwei
Barrieren 6/6 und in drei Vollläufen gefangen.

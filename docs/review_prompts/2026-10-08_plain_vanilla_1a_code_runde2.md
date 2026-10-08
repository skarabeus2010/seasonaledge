# Code-Review Phase 1A /plain-vanilla, Runde 2

Repo `C:\dev\Seasonaledge`, Arbeitsstand. Vorgeschichte: `docs/review_prompts/2026-10-08_plain_vanilla_1a_code_runde1.md`
und deine Antwort `..._1a_code_antwort1.md` (10 Befunde). Prüfe die Korrekturen und den Code auf neue Fehler. Antwort
auf Deutsch: je Befund Schwere + Datei:Zeile + konkreter Eingabefall + Änderung; am Ende genau eine Zeile
`FREIGABE: ja` oder `FREIGABE: nein`. Python: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`.

## Korrekturen
1. Sonderschließungen: `_nyseHolidays` filtert `SA.holidays._NYSE_SONDER` heraus (Sitzungskalender ≠ Feiertagsliste der
   Strategien). Messlauf: Trades 03.12.2018 / 07.01.2025 entfallen; 9/11 erzeugt keinen Trade.
2. Datenrand: `_randTermin` — liegt der Kalendertermin ≤ letzte Kurszeile, gilt das zeilenbasierte Ergebnis (auch im
   letzten Datenmonat); Monthly 10 am Rand = vorhandene Monatszeilen + Kalendertermine NACH der letzten Zeile. Python
   `_rand_termin` gleich.
3. Stops prüfen jeden Kurs (endlich, > 0) vor Auslösung; ungültige protokolliert (`stop_kurs_ungueltig`) und übergangen.
4. Stop-Handler (Checkbox, Regler, Typ) zeichnen auch `renderSignals(rawRows)` neu.
5. `renderSignals` prüft `_datenVeraltet` mit Stichtag heute (Börsenzeit) und zeigt dann statt Signalen einen Hinweis
   (DE/EN-Schlüssel `pv.signale_veraltet`).
6. Python Santa über `_sitzung(df, thanksgiving, -3, "nach")` (Kalender am Rand), kein Einstieg aus der drittletzten Zeile.
7. Python: Zustände sind `Termin(zustand, datum)`; Konsumenten, die ein Datum brauchen (`_is_near_holiday`,
   `calc_ultimate_monthly`, KTI, One-Day-Holiday, UHTS), nutzen `_als_datum()` → am Rand `None` wie vor 1A. Alle 24
   Python-Strategien laufen bis 07.10.2026 ohne Ausnahme.
8. Streamlit `pages/09_Plain_Vanilla_Strategien.py`: Sharpe `None` → „—".
9. E8: Zustände tragen ihren Regeltermin (JS-Registry eindeutiger Codes ≤ −10 → `{code, datum}`; Python `Termin`); jeder
   Trade trägt `zustand_einstieg`, `zustand_ausstieg`, `bewertungsstichtag`, `letzte_kurszeile`, offene zusätzlich
   `regeltermin_ausstieg`; nicht ausgeführte Einstiege werden mit Regeltermin protokolliert.
10. Messlauf über `SA.strategy.auswerten` (Stop, Datenende, `unvollstaendig`, `veraltet`, Protokoll), Tupel mit E8-Feldern.

## Belege
`scripts/verify_plain_vanilla_1a.py` 44/44, `--mutationen` 40/40 + 3/3 untaugliche verworfen (neue Fälle je Befund:
sonder_kein_feiertag, rand_historisch, stop_ungueltig, e8_felder, seite_stop_signale, seite_veraltet (prüft die
Bedingung, nicht das Wort), streamlit_sharpe, py_santa_rand, py_strategien_laufen, py_e8_felder);
`verify_kalender_zwilling` 0; `verify_en` FAIL 0; Messlauf gültig.

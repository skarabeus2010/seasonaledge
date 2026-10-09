# Code-Review: Saison-Score D1/D2 — Runde 2

Repo `C:\dev\Seasonaledge`, Arbeitsstand (Radar ist inzwischen als 0c96a35 committet). Vorgeschichte:
`..._kern_runde1.md` + `..._kern_antwort1.md`. Nur lesen. Gegenstand: `landing/js/saison-score.js`,
`shared/saison_score.py`, `scripts/verify_saison_score.py`, `scripts/js/probe_saison_score.js`.
Antwort auf Deutsch, je Befund Schwere + Datei:Zeile + Fall + Änderung; am Ende genau eine Zeile `FREIGABE: ja` oder
`FREIGABE: nein`.

## Korrekturen zu R1
1. **Konstanter Pfad:** beide `pearson` prüfen Konstanz über min == max **vor** der Mittelwertrechnung → null.
   Referenz nutzt `np.ptp == 0`. Dein Dezimalfall (0,17, Mo–Fr 01.01.2000–11.02.2025) ist Regression
   `fall_konstant_dezimal` → `zu_wenige_musterjahre`; Mutation „Konstanz nicht vor dem Mittelwert geprüft".
2. **Nullgewicht:** Referenz gibt `gewichte_null` zurück; dein Fall (täglich, 2000–2024 fallend, 2025 steigend bis
   20.01., Ticker BTC-USD) ist `fall_gewichte_null`; Mutation „PY: Gewichtssumme 0 nicht abgefangen".
3. **Wirkungslose Mutationen:** Gleichstand jetzt mit `fall_gleichstand` (tägliche Kurse, Pfad nur von Monat/Tag
   abhängig → alle Nicht-Schaltjahre exakt gleiches r); `soll_gleichstand_jung` verlangt, dass Gleichstände
   existieren UND absteigend nach Jahr sortiert sind. Tag-366-Mutation ersetzt durch „Matching-Präfix um einen Tag
   verschoben". Rundung deterministisch: `_runden1` in JS und Python für 1,25 / 0,25 / 0,75 / 9,94 / 2,5 →
   1,3 / 0,3 / 0,8 / 9,9 / 2,5 (Prüfung `rundung`; Mutation `round()` reißt sie).
4. **Plan-Umfang:** 30.12.2024 (`fall_schalt_3012`), analytischer Sprungfall (`fall_sprung`/`soll_sprung_analytisch`:
   jedes Jahr +10 % genau im Fenster → B1 20/20, Ø 10 %, Score 10,0), Snapshot-Raster jetzt **jeder 5.
   Handelstag** 2005–2025.

## Belege
`verify_saison_score.py --snapshot <pv_kurse>` **25/25**: **5 487** echte Stichtage JS = Python bitgleich, Status
4 833 ok, 422 zu früh im Jahr, 232 zu wenige Jahre; Referenz an jeder 35. Stichprobe gleich. Mutationstest läuft.

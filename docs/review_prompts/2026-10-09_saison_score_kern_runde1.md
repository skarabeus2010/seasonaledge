# Code-Review: Saison-Score D1/D2 (Rechenkern + Zwilling) — Runde 1

Repo `C:\dev\Seasonaledge`, Arbeitsstand. Plan: `2026-10-09_saison_score_anomalie_plan.md` + `_v2` + `_v3` (Freigabe).
Nur lesen. Python: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`.
Antwort auf Deutsch: je Befund Schwere + Datei:Zeile + konkreter Eingabefall + Änderung; am Ende genau eine Zeile
`FREIGABE: ja` oder `FREIGABE: nein`.

**Gegenstand nur:** `landing/js/saison-score.js`, `shared/saison_score.py`, `scripts/verify_saison_score.py`,
`scripts/js/probe_saison_score.js`. Noch NICHT verdrahtet (keine Seite, kein Nightly, keine Migration — das sind
D3/D4). Die Anomalie-/Ladekennungs-Änderungen im Baum sind separat im Review.

## Umsetzung gegenüber Plan v2/v3
- Vertrag wie Plan: Ticker Pflicht, `as_of` zuerst, Zieltag 29.02. → 28.02., Fenster +30 KT aus Rohkursen,
  Lückenheuristik mit derselben Marktklassen-Toleranz wie das Radar (**T = 7 Börse**, nicht 5 — in der Radar-Runde
  begründet und freigegeben), Lookback 20 / mind. 10, Top-5, Pearson ungerundet, Gleichstand → jüngeres Jahr,
  w = (r+1)/2, Gewichtssumme 0 → null, Score halb aufwärts, Musterkonformität separat, Tag 366 → d = 365,
  ab dem 20. Handelstag.
- **Bewusste Abweichung (bitte bewerten):** Der Jahrespfad wird im Kern **aus den Kursen** gebaut
  (100 · Kurs / erster Kurs des Jahres) statt über `buildYearData` mit `log_return`. Mathematisch gleich der
  kumulierten Log-Rendite, aber nur so rechnen Python und JS **bitgleich** (exp(cumsum) vs. iteriertes Produkt
  weichen sonst im 1e-13-Bereich ab und könnten bei Beinahe-Gleichständen die Musterjahr-Reihenfolge kippen). Die
  Interpolation ist dieselbe Formel wie `interpolate_to_365`; Python nutzt eine schnelle Fassung `interp365` (binäre
  Suche statt linearer), der Wächter prüft **exakte** Gleichheit auf 1 500 Zufallsfällen.
- Erster unvollständiger Jahrgang: Jahrespfad nur, wenn ≥ 20 Kurszeilen und erste Kurszeile im Januar ≤ 10.;
  ein laufendes Jahr, das später beginnt (Neulisting), → `unvollstaendiges_jahr`.

## Belege
`verify_saison_score.py --snapshot <pv_kurse>` **17/17**: 1 308 echte Stichtage (SPY, QQQ, ^DJI, ^GSPC, ^GDAXI,
jeder 21. Handelstag ab 2005) — JS und Python **bitgleich** (Score, Bausteine, Musterjahre samt r, Konformität),
naive numpy-Referenz an jeder 7. Stichprobe gleich (1e-9); Status dort 1 144 ok, 109 zu früh im Jahr, 55 zu wenige
Jahre. Randfälle: 19./20. Handelstag, Präfixinvarianz, 29.02., 31.12.2024, Fenster über den Jahreswechsel, < 10
Jahre, konstanter Pfad, Marktklasse (zweitägige Lücke: Börse ok, Krypto verwirft), später Jahresstart, fehlender
Ticker. Mutationstest läuft.

## Bitte besonders prüfen
1. Ist die Referenz unabhängig genug (oder teilt sie Annahmen, die beide falsch machen könnten)?
2. Gibt es eine Eingabe, bei der Python und JS trotz gleicher Formel verschieden runden (Summenreihenfolge, `>> 1`,
   `floor(x·10+0,5)` bei negativen Zahlen — Score ist ≥ 0)?
3. `bisIdx`/Fenster: kann `e` ein Datum **nach** `as_of` treffen (nein, Reihe ist abgeschnitten) — aber für das
   **laufende** Jahr wird nie ein Fenster gebildet; richtig so?
4. Fehlt ein Fall im Wächter, den der Plan verlangt (UI-Regler-Unabhängigkeit gehört zu D4)?

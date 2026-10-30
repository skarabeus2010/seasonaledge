# Code- und Artikelprüfung R4 — Down-Days SPY + letzte Woche vor Midterms

Antwort R3: [2026-10-30_down_days_midterm_code_r3_antwort.md](2026-10-30_down_days_midterm_code_r3_antwort.md) — NICHT FREIGABEFÄHIG (nur Wächter).

1. **Verträge vollständig gebunden** — jede Fließtextzahl verlangt Kennzahl, Verluststufe (Regex `(?<![\d,.])k(-| ?)%`,
   trifft „2 %“/„2%“/„−2-%-Tag“, nicht „−2,33 %“), Horizont und Kohorte; Mittelwerte verbieten „median“, das
   Basismittel verbietet „15/30/drei Wochen“, die Midterm-Gesamtwerte verlangen „31/1898“ und verbieten „1971/1974“.
   Die Artikelsätze, in denen Stufe oder Horizont nur im Vorsatz stand, nennen sie jetzt im selben Satz.
2. **Fallzahlen „n = X“** — `n_vertraege`: jede Fallzahl nur mit ihrer Kohorte im Satz, eine fremde Verluststufe im
   selben Satz ist verboten.
Deine fünf R3-Gegenproben sind Mutationen. Mutationen mit `str.replace` auf `_einmal` umgestellt (ein fehlender Anker
bricht ab statt still grün zu bleiben — zwei Mutationen waren durch eine Textänderung leer gelaufen). Stand **55/55**.

Bitte erneut wie in R1–R3 prüfen. Schluss: FREIGABE, FREIGABE MIT AUFLAGEN oder NICHT FREIGABEFÄHIG.

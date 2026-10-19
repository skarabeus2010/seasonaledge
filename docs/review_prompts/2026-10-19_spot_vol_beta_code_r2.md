# Code-Review /spot-vol-beta — Runde 2

Read-only. Runde 1: `docs/review_prompts/2026-10-19_spot_vol_beta_code_r1.md`, deine Antwort
`docs/review_prompts/2026-10-19_spot_vol_beta_code_r1_antwort.md` (keine Freigabe, drei P2-Befunde).

Umgesetzt:
1. **Konstante Renditen:** `ols` und `rolling` erkennen Konstanz über die Spannweite (min = max), nicht über
   `sxx > 0`. Wächter: OLS mit x = [0,1; 0,1; 0,1] und y = [0,1; 0,1; 0,1] nicht bestimmbar; Auswertung „konstant“
   (Spot-`log_return` durchgehend 0,001) → kein Rolling-Wert, OLS nicht bestimmbar. Mutationen „OLS/Rolling Konstanz
   nur über sxx“. Die Mutation „OLS ohne Var(y)-Prüfung“ ist damit äquivalent und entfernt.
2. **Ein VRP-Wert:** `zahlFmt` null-sicher, VRP-Lage „–“ ohne Quantile. Neuer Fall `kurz` in
   `scripts/js/probe_seiten_kurse.js` (22 Kurszeilen → genau ein VRP-Wert, keine Buckets, kein Rolling); der Wächter
   rendert die echte Seite (`normal`, `kurz`) und verlangt: Ende/Ruhe/keine Seitenfehler, **kein Fehlerbanner**
   („Fehler beim Laden“ — der alte Absturz landete dort, nicht als Seitenfehler), VRP-Kennzahlen, kein NaN/undefined,
   Anfragen mit `log_return` und `date=gte.1990-01-01`. Gegenprobe: die alte `zahlFmt` in einer Kopie → rot.
3. **Bucket-Horizonte:** +1/+5/+20/+60 je Eimer mit Ø, Median, Trefferquote, Max, Min, n gegen numpy.
   Mutationen „Bucket +5 verschoben“, „Bucket +60 als +20“, „Median falsch“.
Zusätzlich: die Börse ist kein Literal mehr (Kalender-V2-Inventar meldete `'NYSE'` als neue Stelle mit altem
Börsenalphabet): `opts.boerse` = `SA.boersenkalender.boerse(spotTicker)`; Mutation „Börse ignoriert“. Eine Auswertung,
die im Wächter abstürzt, wird als rote Prüfung gemeldet. `svb.daily_beta_note` ohne rohes `<` (data-i18n statt -html).

Stand: `verify_spot_vol_beta.py` 169/169, Mutationen 23/23, `verify_holidays_fassade.py` 2265/2265.

Bitte prüfen, ob die drei Befunde behoben sind, und ob neue Lücken entstanden sind.
Antwort: Befunde (Schwere, Datei:Zeile), Urteil „Freigabe“ / „keine Freigabe“.

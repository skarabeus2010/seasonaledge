# Entwurfsprüfung: NE-Skew, Skew-Term, Term-Struktur, Smile-Kurve auf eigene Rechnung

**Das ist eine Prüfung des ENTWURFS, bevor Code entsteht.** Gesucht sind Denkfehler, übersehene
Fälle und bessere Alternativen — nicht Stil.

## Ausgangslage

Seit Commit `c94c63d` (heute abgenommen) zeigt `/skew` die 25Δ/ATM-Werte aus der eigenen
30-Tage-Normierung (`_skew_cm` → `leg_from_prices`, nur Kurse aus der Session). Vier Werte laufen noch
über den alten **Anbieter-Picker** (`_byexp` → `_skew_at` / `_pick` / `_atm_iv`), der den Kontrakt über
das Anbieter-Delta wählt, das aus der IV desselben Kontrakts stammt:

| Feld | heute berechnet in `scripts/compute_options_skew.py::_enrich` |
|---|---|
| `skew_ne_pts`, `skew_ne_dte` | `_skew_at(by, 1)` |
| `skew_back_pts` (90 T.), `skew_term_pts` | `_skew_at(by, 90)`; `skew_term = s90 − s30` (s30 = Anbieter-Front-Monat) |
| `term`, `contango`, `term_slope_pts` | `_atm_iv(by[_nearest_exp(by, t)])` für t in (7, 30, 60, 90, 120, 180) |
| `skew_curve.iv30`, `.iv_ne` | `_pick` bei 10/25/40Δ + `_atm_iv`, Expiry nächst 30 bzw. 1 Tag |

Frontend: `landing/pages/skew.html::renderSkewCurve` (verträgt `null` je Punkt, braucht `iv30`),
`renderTermStructure` (verträgt **kein** `null` in `term[i].iv` — fehlende Punkte weglassen), Tabelle
Spalten NE-Skew/Skew-Term/Term.

## Messung (40 Ticker, EOD-Snapshot 2026-09-24, Anbieter-Picker vs. eigene gefilterte Leg)

- **NE-Skew** nahm IMMER die Expiry mit 22 Tagen: `_skew_at(by, 1)` bevorzugt Monatsverfälle
  (`_nearest_exp(..., prefer_monthly=True)`), der Pool enthält dann nur Monate → „nächster Verfall"
  war faktisch der Front-Monat. Die Smile-Kurve „NE" nimmt dagegen den wirklich nächsten Verfall.
  Tooltip auf `/skew` verspricht „nächster Verfall". 20/38 > 3 pts, 9 > 8 pts, 14 Vorzeichenwechsel.
- **90 Tage:** 7/31 > 3 pts, 7 Vorzeichenwechsel; bei 6 Tickern (TLT, HYG, XOM, LRCX, BX, COIN)
  scheitert die eigene Leg bei 85 Tagen.
- **Term-ATM:** 34/195 > 2 IV-Punkte, 9 > 5, systematisch am kurzen Ende zu hoch (XLF 7 T.: 20,3 %
  vs. 14,5 %). **42 Punkte ohne eigene Leg**, weil `leg_from_prices` beide 25Δ-Flügel verlangt.

## Entwurf

### A. `shared/black_scholes.py` — aufteilen, ohne `leg_from_prices` zu verändern

`leg_from_prices` nutzt auch der Backfill. Ihr Ergebnis darf sich **bit-genau nicht** ändern.

1. `_gefilterte_punkte(cands, spot, dte)` → `(punkte, iv_atm, T)` oder `None`: Schritte 1–4 der
   heutigen Funktion (IV-Inversion, Smile-Ausreißer, Parität im ATM-Band, ATM über Moneyness am Forward).
2. `leg_from_prices` = `_gefilterte_punkte` + Schritt 5 (25Δ über Referenz-Delta) + Konkav-Invariante.
3. **neu** `atm_from_prices(cands, spot, dte)` → `iv_atm` (ohne Flügelzwang) — für die Term-Struktur.
4. **neu** `smile_from_prices(cands, spot, dte, deltas=(0.10, 0.25, 0.40), delta_tol=DELTA_TOL)` →
   `{"iv_atm", "put": {δ: iv|None}, "call": {δ: iv|None}}`, Auswahl über das **Referenz-Delta** aus der
   ATM-IV (wie Schritt 5), gemeldet wird die eigene IV des gewählten Kontrakts.

Nachweis: `leg_from_prices` vorher/nachher auf allen gesicherten Rohketten (40 Ticker × alle Expiries)
und auf synthetischen Ketten — Ergebnis-Dicts müssen identisch sein.

### B. `_enrich` — alle vier Felder aus `by_own` (Session-Kurse) statt `by`

1. **NE-Skew = wirklich nächster Verfall**, `dte ≥ 1` (0DTE ausgeschlossen: T → 0, Inversion
   instabil), kein Monatsvorzug. Schlägt `leg_from_prices` dort fehl: **nächsten Verfall probieren bis
   `dte ≤ 10`**, sonst `None`. `skew_ne_dte` = tatsächlich genutzte Laufzeit.
2. **90 Tage:** Monatsverfall nächst 90 via `leg_from_prices` → `skew_back_pts`, `skew_back_dte`.
   `skew_term_pts = skew_back_pts − skew_pts` — **nur** wenn beide da sind (skew_pts ist jetzt der
   30-Tage-CM-Wert). Kein Rückfall auf den Anbieter.
3. **Term:** je Ziel nächster Verfall **ohne** Monatsvorzug (die Term-Struktur soll das kurze Ende
   zeigen), `atm_from_prices`; fehlende Punkte weglassen; doppelte Expiries entfernen.
   `contango = term[0].iv < iv_atm` mit dem angezeigten 30-Tage-`iv_atm`; `term_slope_pts` unverändert.
4. **Smile:** `iv30` = je Punkt über `cm_interp` zwischen den beiden `cm_exps` der 30-Tage-Normierung
   (damit die 25Δ-Punkte der Kurve zu den angezeigten 25Δ-Werten passen), bei `single` die eine
   Expiry, sonst `None`; `dte30 = 30`. `iv_ne` = Smile der NE-Expiry aus 1.
5. Alte Anbieterwerte der vier Felder wandern nach `front_provider` (Diagnose, Vergleich).

### C. Prüfung

- Wächter (in `scripts/verify_skew_anzeige.py` oder eigener, über `scripts/waechter_isolation.py`)
  mit synthetischer BS-Kette inkl. Tages-Verfällen; Mutationen in `verify_session_mutation.py`.
- Echter Vorher/Nachher-Vergleich auf den gesicherten Rohketten (40 Ticker).

## Fragen an dich

1. **NE-Skew:** Ist „nächster Verfall mit dte ≥ 1, sonst weiter bis dte ≤ 10" die richtige
   Definition? Bei SPY/QQQ gibt es tägliche Verfälle — ein 1-Tage-25Δ liegt extrem nah am Geld, und
   die Inversion wird dort unruhig. Alternative: Mindestlaufzeit 2–3 Tage. Was ist fachlich
   belastbarer (Referenz: SpotGamma „NE Skew")?
2. **90 Tage:** nächster Monatsverfall (heute 85 T.) oder wie bei 30 T. auf exakt 90 interpolieren
   (`cm_interp`, linear in totaler Varianz)? Ist die Differenz 30-CM minus 90-nächster-Monat eine
   saubere „Skew-Term"-Kennzahl, oder mischt sie zwei Methoden?
3. **Smile per `cm_interp` je Delta-Punkt:** Ist Interpolation der IV je festem Delta zwischen zwei
   Laufzeiten zulässig, oder müsste man über Moneyness interpolieren?
4. **`_gefilterte_punkte`:** Die Konkav-Invariante (ATM nicht über beiden Flügeln) prüft heute nur
   `leg_from_prices`. Braucht `atm_from_prices` ohne Flügel einen Ersatz-Schutz gegen einen falschen
   ATM-Anker?
5. **Übersehenes:** Wer liest `skew_ne_pts`, `skew_term_pts`, `term`, `skew_curve` sonst noch
   (`shared/daily_report.py`, Newsletter, `/flows`, Health-Check)?
6. **Rückwirkung:** Die History speichert keines der vier Felder — richtig, dass nichts rückwirkend
   neu zu rechnen ist?

## Ausgabevertrag

Je Frage 3–8 Zeilen Antwort mit Begründung (gern mit Zeilenankern). Danach „Weitere Befunde am
Entwurf" im Format `STELLE | SCHWERE | Was | Vorschlag`. Schluss: `ENTWURF TRAGFÄHIG: ja/nein`
+ ein Satz. Keine Stilkritik, kein Lob. Dateien nicht ändern.

# Wirkungsbericht B3a — Skew-Rang einmal im Cron (2026-10-16)

Eingefrorene Eingaben: Live-`options_skew_history.json` und `options_skew.json` vom 16.10. (Session 2026-10-15).
Alt = Seitenrechnung aus `HEAD` (`landing/pages/skew.html`, Fenster ab der Uhr des Lesers, hier 16.10.), im Browser-JS
ausgeführt; neu = `shared/skew_rang.py` (Fenster ab der Session), von der neuen Seite gelesen. Probe:
`scripts/js/probe_skew_rang_seite.js` (Kopie mit History-/Seitenparameter).

## Radar /skew (Kategorie „Alle“)

| Modus | Ansicht | Fenster | Punkte alt | Punkte neu | \|Δx\| Median / max | \|Δy\| Median / max | Quadrantenwechsel | nur alt | nur neu |
|---|---|---|---|---|---|---|---|---|---|
| pctl | rr_iv | 92 | 149 | 149 | 0 / 2 | 0 / 2 | 2 NEE, SOXX |  |  |
| pctl | rr_iv | 183 | 150 | 150 | 0.0 / 1 | 0.0 / 1 | 0  |  |  |
| pctl | rr_iv | 365 | 150 | 150 | 0.0 / 1 | 0.0 / 1 | 0  |  |  |
| pctl | cs_ps | 92 | 149 | 149 | 0 / 2 | 0 / 2 | 0  |  |  |
| pctl | cs_ps | 183 | 150 | 150 | 0.0 / 1 | 0.0 / 1 | 0  |  |  |
| pctl | cs_ps | 365 | 150 | 150 | 0.0 / 1 | 0.0 / 1 | 0  |  |  |
| rank | rr_iv | 92 | 149 | 149 | 0 / 30 | 0 / 24 | 0  |  |  |
| rank | rr_iv | 183 | 150 | 150 | 0.0 / 16 | 0.0 / 2 | 0  |  |  |
| rank | rr_iv | 365 | 150 | 150 | 0.0 / 11 | 0.0 / 0 | 0  |  |  |
| rank | cs_ps | 92 | 149 | 149 | 0 / 23 | 0 / 23 | 5 GOOGL, IBIT, PFE, SLV, SMH |  |  |
| rank | cs_ps | 183 | 150 | 150 | 0.0 / 12 | 0.0 / 3 | 0  |  |  |
| rank | cs_ps | 365 | 150 | 150 | 0.0 / 0 | 0.0 / 3 | 0  |  |  |
Percentile (Standard): Abweichung höchstens 1–2 Punkte, zwei Quadrantenwechsel (NEE, SOXX, beide nahe 50).
Rank: einzelne Ausreißer bis 30 Punkte im 3-M-Fenster — der Rank hängt an Minimum/Maximum, und das Fenster beginnt
jetzt an der Session statt an der Uhr (ein Randtag mehr oder weniger verschiebt min/max). Keine Ticker kommen hinzu
oder fallen weg.

## Morgen-Mail (Skew-Percentile 1 J.)

Alt (`daily_report.skew_pctl_map`, HEAD): alle Zeilen inkl. nicht normierter, Fenster ab Versanduhr, aktueller Wert =
Snapshot-Skew. Neu: `rang[t]["365"]["skew"]["pctl"]`. 150 gemeinsame Ticker, |Δ| Median 1, P90 4, max 11
(ITB 43 → 32, WMB 15 → 5, HYG 86 → 77, BE/SPY 42 → 49, KLAC 93 → 99). 148 von 150 Tickern hatten nicht normierte
Zeilen im Jahresfenster der alten Rechnung. Neu zusätzlich: ein Snapshot einer anderen Session ergibt „P—“ statt einer
Zahl; die Zelle ist einfarbig.

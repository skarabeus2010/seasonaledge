# Kalender-Umstellung V2 — Code Runde 5

Runde 4: [Vorlage](2026-10-18_kalender_v2_code_r4.md) · [Antwort](2026-10-18_kalender_v2_code_r4_antwort.md)
(keine Freigabe; der belegte Nachfolger wurde nie gelesen, weil beide Ersatzmonate offen enden). Arbeitsbaum.
Read-only.

<task>Ist der Befund aus Runde 4 erledigt? Ist V2 freigabefähig?</task>

## Zum Befund
Statt eines weiteren Ersatzmonats prüft der Wächter den Monatsübergang jetzt für JEDE Liste unabhängig davon, wie
der Monat endet (`verify_holidays_fassade.py`, Abschnitt 3b): `H.nextTradingDay(Erster des Folgemonats)` und
`K.naechste(Monatsletzter, streng)` müssen genau `erste_sitzung_folgemonat.datum` liefern; eine Liste ohne belegten
Nachfolger ist rot („UNGEPRÜFT"). Gegenprobe wie in Runde 4 (Nachfolger Mailand und LSE im Speicher auf 2099-12-31):
**4 rote Prüfungen** (je zwei Übergänge), 2261/2265. Zusätzlich als Mutation im Mutationstest („Nachfolger Mailand
verfälscht" → 02.12.). Wächter 2265 Prüfungen grün.

## Ausgabevertrag
**Urteil** · **Befunde** (nur neue/offene) · **Auflagen**. ≤ 12 Zeilen.

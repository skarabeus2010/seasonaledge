# Messung Phase 1B /plain-vanilla — Stand 1A (6170252) gegen freigegebenen Stand 1B

Erzeugt mit `scripts/js/probe_plain_vanilla_messlauf.js` auf dem eingefrorenen Kurs-Snapshot (Hash `a563a159fc2da067`, Stand 07.10.2026). Gegenüber 1A ändern sich Trades und bisherige Kennzahlen **nur bei UHTS** (30 von 30 Kombinationen: Ausstieg S⁺3 statt S⁺4 und Hebelpfad 1x → 2x ab Schluss der letzten Sitzung vor dem Feiertag). Alle übrigen Strategien sind auf allen fünf Tickern in Trades und alten Kennzahlen unverändert; die XETRA-Kalenderkorrektur verschiebt keinen historischen Trade, weil ^GDAXI an den Tagen ohnehin keine Kurszeile hatte. Neu sind die Kontowerte (täglich zum Schlusskurs, keine Stapelung überlappender Trades) und die Lückenmarken.

Unabhängige Referenz: Monthly 10 SPY 1994–2025 stimmt mit `scripts/research/monthly10_blogzahlen.py` auf denselben Zeilen in Endfaktor, Max-DD und CAGR auf 1e-9 überein (Snapshot: aus 10.000 werden 56.885,28; veröffentlicht 56.883 auf älterem Datenstand).

## UHTS alt (1A) → neu (1B), ohne Stop

| Ticker | Zeitraum | Trades | Trefferquote % | Ø % | PF | Max DD Trades % |
|---|---|---|---|---|---|---|
| SPY | 10 | 100 → 100 | 68,0 → 58,0 | 1,03 → 0,63 | 2,38 → 1,74 | -16,3 → -16,5 |
| SPY | max | 298 → 298 | 59,7 → 57,7 | 0,55 → 0,46 | 1,52 → 1,41 | -36,0 → -29,7 |
| QQQ | 10 | 100 → 100 | 68,0 → 62,0 | 1,34 → 0,98 | 2,21 → 1,85 | -21,1 → -20,6 |
| QQQ | max | 248 → 248 | 62,9 → 58,9 | 0,93 → 0,85 | 1,55 → 1,49 | -63,1 → -57,5 |
| ^DJI | 10 | 100 → 100 | 58,0 → 56,0 | 0,64 → 0,25 | 1,75 → 1,24 | -17,2 → -26,4 |
| ^DJI | max | 1058 → 1058 | 62,9 → 60,1 | 0,82 → 0,67 | 1,84 → 1,59 | -33,4 → -52,5 |
| ^GSPC | 10 | 100 → 100 | 68,0 → 56,0 | 0,96 → 0,56 | 2,25 → 1,64 | -16,4 → -16,7 |
| ^GSPC | max | 1069 → 1069 | 61,9 → 59,6 | 0,82 → 0,63 | 1,88 → 1,58 | -35,9 → -48,8 |
| ^GDAXI | 10 | 100 → 100 | 52,0 → 53,0 | 0,40 → 0,34 | 1,37 → 1,26 | -26,4 → -30,3 |
| ^GDAXI | max | 561 → 561 | 63,3 → 59,7 | 0,99 → 0,92 | 1,87 → 1,68 | -33,2 → -45,6 |

## Neu: Kontowerte täglich (Schlusskurse) neben den bisherigen Trade-Werten, SPY und ^GDAXI, ohne Stop

| Ticker | Zeitraum | Strategie | Max DD Trades % | Max DD Schlusskurse % | CAGR Trades % | CAGR Konto % |
|---|---|---|---|---|---|---|
| SPY | 10 | sell_in_may | -6,0 | -33,7 | 7,90 | 7,90 |
| SPY | 10 | september_avoid | -6,9 | -33,7 | 16,82 | 16,82 |
| SPY | 10 | nasdaq_trend | -17,0 | -33,7 | 11,42 | 11,42 |
| SPY | 10 | monthly_10 | -15,4 | -16,4 | 7,22 | 7,22 |
| SPY | 10 | month_end | -14,7 | -16,2 | 4,51 | 4,51 |
| SPY | 10 | santa_claus | -4,0 | -15,6 | 2,49 | 2,49 |
| SPY | 10 | uhts | -16,5 | -20,0 | 5,60 | 5,58 |
| SPY | 10 | one_day_holiday | -2,9 | -2,9 | 1,68 | 1,68 |
| SPY | max | sell_in_may | -12,6 | -34,8 | 7,38 | 7,38 |
| SPY | max | september_avoid | -28,9 | -52,3 | 11,46 | 11,46 |
| SPY | max | nasdaq_trend | -18,5 | -41,6 | 8,49 | 8,49 |
| SPY | max | monthly_10 | -41,0 | -41,0 | 5,37 | 5,37 |
| SPY | max | month_end | -28,3 | -28,3 | 3,82 | 3,82 |
| SPY | max | santa_claus | -7,8 | -15,6 | 2,18 | 2,18 |
| SPY | max | uhts | -29,7 | -31,0 | 3,56 | 3,52 |
| SPY | max | one_day_holiday | -7,9 | -7,9 | 0,89 | 0,89 |
| ^GDAXI | 10 | sell_in_may | -17,6 | -38,8 | 8,62 | 8,62 |
| ^GDAXI | 10 | september_avoid | -15,9 | -41,1 | 9,97 | 9,97 |
| ^GDAXI | 10 | nasdaq_trend | -18,5 | -38,8 | 9,45 | 9,45 |
| ^GDAXI | 10 | monthly_10 | -15,1 | -15,8 | 5,48 | 5,48 |
| ^GDAXI | 10 | month_end | -16,9 | -19,7 | 2,27 | 2,27 |
| ^GDAXI | 10 | santa_claus | -3,9 | -9,5 | 3,56 | 3,56 |
| ^GDAXI | 10 | uhts | -30,3 | -33,0 | 2,46 | 2,17 |
| ^GDAXI | 10 | one_day_holiday | -2,9 | -2,9 | 2,86 | 2,86 |
| ^GDAXI | max | sell_in_may | -17,6 | -40,6 | 7,27 | 7,27 |
| ^GDAXI | max | september_avoid | -33,8 | -52,9 | 8,38 | 8,38 |
| ^GDAXI | max | nasdaq_trend | -28,1 | -50,8 | 7,04 | 7,04 |
| ^GDAXI | max | monthly_10 | -40,4 | -40,9 | 4,49 | 4,49 |
| ^GDAXI | max | month_end | -37,8 | -38,9 | 5,88 | 5,88 |
| ^GDAXI | max | santa_claus | -11,4 | -18,1 | 3,17 | 3,17 |
| ^GDAXI | max | uhts | -45,6 | -46,3 | 6,99 | 6,24 |
| ^GDAXI | max | one_day_holiday | -8,0 | -8,0 | 1,82 | 1,82 |

## Lückenmarken (max, ohne Stop)

| Ticker | Strategie | Trades | mit fehlender Sitzung | mit auffälligem Abstand | Näherung |
|---|---|---|---|---|---|
| QQQ | uhts | 248 | 0 | 0 | 0 |
| QQQ | sell_in_may | 27 | 0 | 0 | 0 |
| QQQ | monthly_10 | 994 | 0 | 0 | 0 |
| SPY | uhts | 298 | 0 | 0 | 0 |
| SPY | sell_in_may | 33 | 0 | 0 | 0 |
| SPY | monthly_10 | 1213 | 0 | 0 | 0 |
| ^DJI | uhts | 1058 | 0 | 11 | 11 |
| ^DJI | sell_in_may | 129 | 0 | 6 | 0 |
| ^DJI | monthly_10 | 4680 | 0 | 5 | 0 |
| ^GDAXI | uhts | 561 | 0 | 74 | 74 |
| ^GDAXI | sell_in_may | 67 | 0 | 40 | 0 |
| ^GDAXI | monthly_10 | 2413 | 0 | 15 | 0 |
| ^GSPC | uhts | 1069 | 0 | 8 | 8 |
| ^GSPC | sell_in_may | 130 | 0 | 4 | 0 |
| ^GSPC | monthly_10 | 4732 | 0 | 4 | 0 |
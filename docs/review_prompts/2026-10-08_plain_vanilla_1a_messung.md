# Messung Phase 1A /plain-vanilla — alter Stand gegen freigegebenen Stand

Erzeugt mit `scripts/js/probe_plain_vanilla_messlauf.js` auf einem eingefrorenen Kurs-Snapshot (Stand 07.10.2026) und `scripts/research/plain_vanilla_bericht.py`. 10 Jahre, ohne Stop (Seitenstandard). Fettdruck = geändert.

Ursachen der Änderungen: offene Trades zählen nicht mehr in die Kennzahlen; Kalender ohne Phantom-Feiertage (Juneteenth/MLK vor Einführung, Sonderschließungen) → One-Day-Holiday/UHTS weniger Trades; LBR nutzt den Vortageswert; Santa steigt am Montag nach Thanksgiving ein; PF/Sharpe „—“ statt 999 bzw. Sharpe erst ab 5 Trades. Historische Trades bis Ende 2025 aller übrigen Strategien sind auf zwei Stellen identisch — die Blogzahlen (Monthly 10, Sell in May, Down-Month ToM) sind nicht betroffen.

Kurs-Snapshot a563a159fc2da067, Stichtag 2026-10-07; Module alt 72e3da2d0cb7cc28 → neu 9ec49c118963228c

### ^DJI — 10, Stop aus

| Strategie | Trades (offen) | Treffer % | Ø % | PF | Sharpe | DD % |
|---|---|---|---|---|---|---|
| lbr_november_mai | 10 (0) → 11 (1) | 70 | 5.69 → **4.93** | 3.85 → **3.05** | 0.58 → **0.5** | -15.2 → **-14.6** |
| nasdaq_trend | 10 (0) → 10 (0) | 80 | 7.8 | 5.19 → **5.18** | 0.68 | -14.1 |
| september_avoid | 11 (0) → 11 (1) | 81.8 → **80** | 11.64 → **12.75** | 17.37 → **17.29** | 1.14 → **1.21** | -6.9 |
| election_7months | 3 (0) → 3 (0) | 100 | 13.74 | 999 → **—** | 1.79 → **—** | 0 |
| last_five_days | 5 (0) → 5 (0) | 80 | 9.72 → **9.73** | 8.62 | 0.83 | -6.4 |
| santa_claus | 11 (1) → 10 (0) | 70 | 2.83 → **2.52** | 3.62 → **3.48** | 0.62 → **0.6** | -6.4 → **-4.9** |
| one_day_holiday | 107 (0) → 100 (0) | 54.2 → **56** | 0.1 → **0.11** | 1.51 → **1.57** | 0.45 → **0.47** | -4.1 → **-3.8** |
| uhts | 107 (0) → 100 (0) | 57.9 → **58** | 0.57 → **0.64** | 1.64 → **1.75** | 0.63 → **0.69** | -18.7 → **-17.2** |
| month_end | 130 (1) → 129 (0) | 61.2 | 0.3 | 1.51 | 0.55 | -13.8 |
| monthly_10 | 387 (0) → 388 (0) | 55.6 → **56.4** | 0.17 | 1.37 → **1.38** | 0.65 → **0.66** | -15 |
| downmonth_tom | 42 (1) → 42 (1) | 78 → **80.5** | 2.23 | 5.12 | 1.21 | -11.1 |
| cycle_40_week | 14 (0) → 14 (0) | 78.6 | 4.61 | 11.54 → **11.55** | 1.02 | -4.9 → **-4.8** |
| cycle_212_week | 2 (0) → 2 (0) | 100 | 11.85 | 999 → **—** | 0 → **—** | 0 |
| mid_decade | 1 (0) → 1 (0) | 100 | 9.48 | 999 → **—** | 0 → **—** | 0 |
| cycle_20_year | 1 (0) → 1 (0) | 100 | 67.32 | 999 → **—** | 0 → **—** | 0 |
| uecs | 9 (1) → 9 (1) | 100 | 10.9 → **10.89** | 999 → **—** | 1.8 | 0 |
| midterm_election | 2 (0) → 2 (0) | 100 | 3.92 | 999 → **—** | 4.88 → **—** | 0 |

Unverändert: sell_in_may, first_five_days, january_barometer, post_christmas, second_trading_day

### SPY — 10, Stop aus

| Strategie | Trades (offen) | Treffer % | Ø % | PF | Sharpe | DD % |
|---|---|---|---|---|---|---|
| sell_in_may | 10 (0) → 10 (0) | 70 | 8 | 8.37 | 0.77 | -5.9 → **-6** |
| lbr_november_mai | 10 (0) → 11 (1) | 80 | 8.13 → **7.83** | 11.09 → **15.24** | 0.88 → **0.94** | -5.9 → **-4.8** |
| nasdaq_trend | 10 (0) → 10 (0) | 90 | 11.86 | 7.99 | 0.9 | -16.9 → **-17** |
| september_avoid | 11 (0) → 11 (1) | 90.9 → **90** | 15.96 → **17.36** | 26.44 → **26.16** | 1.31 → **1.39** | -6.9 |
| election_7months | 3 (0) → 3 (0) | 100 | 14.79 | 999 → **—** | 1.31 → **—** | 0 |
| santa_claus | 11 (1) → 10 (0) | 60 → **70** | 2.61 → **2.33** | 4.18 → **4.7** | 0.66 → **0.7** | -5.6 → **-4** |
| one_day_holiday | 107 (0) → 100 (0) | 61.7 → **65** | 0.17 → **0.18** | 2.04 → **2.08** | 0.78 | -3.1 → **-2.9** |
| uhts | 107 (0) → 100 (0) | 65.4 → **68** | 0.94 → **1.03** | 2.22 → **2.38** | 0.97 → **1.01** | -18.5 → **-16.3** |
| post_christmas | 10 (0) → 10 (0) | 30 | -0.37 | 0.38 | -0.37 → **-0.38** | -4 |
| month_end | 130 (1) → 129 (0) | 65.9 | 0.39 | 1.65 | 0.66 | -14.7 |
| monthly_10 | 387 (0) → 388 (0) | 56.8 → **57.7** | 0.2 → **0.21** | 1.44 → **1.45** | 0.76 → **0.78** | -15.4 |
| downmonth_tom | 35 (1) → 35 (1) | 76.5 → **79.4** | 2.08 | 3.94 | 0.96 | -12.5 |
| cycle_212_week | 2 (0) → 2 (0) | 100 | 15.59 → **15.58** | 999 → **—** | 14.64 → **—** | 0 |
| mid_decade | 1 (0) → 1 (0) | 100 | 15.38 | 999 → **—** | 0 → **—** | 0 |
| cycle_20_year | 1 (0) → 1 (0) | 100 | 99.52 | 999 → **—** | 0 → **—** | 0 |
| uecs | 9 (1) → 9 (1) | 100 | 12.85 | 999 → **—** | 1.8 | 0 |
| midterm_election | 2 (0) → 2 (0) | 100 | 3.69 → **3.68** | 999 → **—** | 57.67 → **—** | 0 |

Unverändert: first_five_days, last_five_days, january_barometer, second_trading_day, cycle_40_week


# Forschungsbericht: Saisonalitäts-Strategien auf US-ETFs mit technischen Filtern

**Stand:** 2026-08-18 · **Engine:** `scripts/research/etf_seasonal_scan.py` · **Rohdaten:** `scan_result.json`

---

## Kernaussage

Von **5.880 getesteten Kombinationen** bestehen 160 eine korrekte Walk-Forward- und
Multiple-Testing-Prüfung. Nach Abzug realistischer Handelskosten bleiben **7 bis 11**
übrig, bei 20 Basispunkten noch **eine**, bei 40 Basispunkten **keine**.

Der gefundene Effekt ist statistisch real, sitzt aber fast vollständig **innerhalb des
Geld-Brief-Spreads**. Als handelbares Signal trägt er nur dort, wo die Rendite pro Trade
deutlich über den Kosten liegt — das ist bei genau einer Strategiefamilie der Fall.

---

## 1. Aufbau

| | |
|---|---|
| Universum | 40 US-ETFs |
| Strategien | 21, portiert aus `landing/js/strategy-compute.js` |
| Filter | LBR (3-10-16), RSI(14), Bollinger(20; 2) — je bullisch/bearisch, plus ungefiltert |
| Tests | 40 × 21 × 7 = **5.880** |
| Walk-Forward | In-Sample < 2016-01-01, Out-of-Sample danach; beide Perioden müssen positiv sein |
| Entscheidungsregel | Benjamini-Hochberg-FDR bei q = 0,10 über alle Tests |
| Zusatzinformation | Deflated Sharpe Ratio (Bailey & López de Prado 2014), annualisiert |

Die Indikatoren sind bitgenaue Ports (max. Abweichung ≈ 1e-12 über 6.902 Bars), 19 von 21
Strategie-Ports liefern trade-identische Ergebnisse gegenüber dem JavaScript-Original.
Die Statistik ist ohne scipy implementiert und gegen Tabellenwerte verifiziert.

---

## 2. Ergebnis brutto

Die Sensitivitätskurve über die Mindest-Tradezahl im Out-of-Sample ist **stabil** — das
Ergebnis hängt nicht an einer willkürlichen Schwelle:

| min. OOS-Trades | auswertbar | IS+OOS positiv | FDR-pass | Überlebende |
|---|---|---|---|---|
| 8 | 999 | 721 | 211 | 195 |
| 12 | 980 | 703 | 193 | 177 |
| **15** | **960** | **684** | **176** | **160** |
| 20 | 950 | 681 | 179 | 163 |
| 30 | 931 | 670 | 183 | 167 |

**Verteilung der 160 Überlebenden**

| Strategie | Anzahl | | Filter | Anzahl |
|---|---|---|---|---|
| downmonth_tom | 39 | | ungefiltert | 56 |
| one_day_holiday | 38 | | **lbr_bear** | **45** |
| uhts | 36 | | bb_inside | 40 |
| monthly_10 | 28 | | lbr_bull | 10 |
| month_end | 15 | | rsi_gt50 | 9 |
| second_trading_day | 4 | | | |

---

## 3. Ergebnis nach Handelskosten — der eigentliche Befund

Näherung: `Sharpe_netto = (Ø-Rendite − Kosten) / Streuung`, anschließend erneute FDR-Prüfung.

| Round-Trip-Kosten | Kombinationen mit Netto-Edge |
|---|---|
| 0 bp | 160 |
| 5 bp (SPY-artig) | 11 |
| 10 bp (liquider ETF) | 7 |
| 20 bp (mittel) | 1 |
| 40 bp (illiquide) | 0 |

Der Grund ist in der Renditeverteilung sichtbar: **58 der 160 Überlebenden verdienen unter
0,5 % pro Trade.** Bei `one_day_holiday` sind es 0,21–0,32 %, bei `monthly_10` 0,61 %. Solche
Effekte sind bei 90 bis 130 Trades pro Zeitreihe rechnerisch tot, sobald man den Spread
einrechnet.

**Was übrig bleibt:** `downmonth_tom` kombiniert mit `lbr_bear` auf Sektor-ETFs.

| Ticker | n | WR | Ø/Trade | SR ann. | p |
|---|---|---|---|---|---|
| XLI | 36 | 77,8 % | +2,62 % | 1,33 | 0,0000 |
| XLB | 38 | 78,9 % | +2,35 % | 1,24 | 0,0001 |
| RSP | 33 | 75,8 % | +2,33 % | 1,17 | 0,0002 |
| IYT | 39 | 82,1 % | +2,93 % | 1,11 | 0,0004 |

Ökonomisch ist das kohärent: `downmonth_tom` verlangt bereits einen 21-Tage-Rückgang,
`lbr_bear` fügt ein negatives LBR-Histogramm hinzu. Es ist also **Kauf von Schwäche auf
Schwäche** — eine Mean-Reversion-Prämie, kein Kalendereffekt. Dass ausgerechnet der
*bearische* Filter gewinnt und der bullische nur zehnmal vorkommt, stützt diese Lesart.

---

## 4. Was nicht getestet wurde

**15 der 21 Strategien haben keinen einzigen auswertbaren Test geliefert:** sell_in_may,
september_avoid, nasdaq_trend, santa_claus, january_barometer, first_five_days,
last_five_days, midterm_election, election_year_7m, mid_decade, cycle_20_year, cycle_212w,
cycle_40w, post_christmas, lbr_november_mai.

Grund ist keine Schwäche der Effekte, sondern eine **Datengrenze**: Jahresstrategien
erzeugen einen Trade pro Jahr. Für 20 In-Sample-Trades bei Split 2016 braucht man Kurse ab
1996 — das erfüllt von 40 ETFs nur SPY, und im Out-of-Sample-Fenster fallen dann rund zehn
Trades an. Gegen 5.880 Tests lässt sich damit nichts absichern, unabhängig davon, ob der
Effekt existiert.

Die getestete Menge ist also faktisch: **6 hochfrequente Strategien**, nicht 21.

Passend dazu aus der Literaturrecherche: Maberly & Pierce zeigen, dass der US-Halloween-
Effekt von **zwei Ausreißern** getragen wird (Oktober 1987, LTCM August 1998) und nach
deren Kontrolle insignifikant ist. Unser roher `sell_in_may`-Sharpe von 0,80 auf 33 SPY-Trades
ist mit hoher Wahrscheinlichkeit dasselbe Phänomen.

---

## 5. Methodische Korrekturen an diesem Bericht

Eine erste Fassung dieser Auswertung meldete **null** Überlebende. Diese Zahl war falsch,
und zwar nicht durch die Daten, sondern durch das Entscheidungs-Gate:

1. **Die Deflated Sharpe Ratio war fehlskaliert.** Sie verglich einen *Pro-Trade*-Sharpe
   gegen `sr0 = 0,627`. Wegen `z = (sr − sr0)·√(n−1)` sank der Wert bei `sr < sr0` mit
   *wachsender* Stichprobe — mehr Daten ergaben ein schlechteres Urteil. Von 952 Kandidaten
   war der höchste Sharpe 0,665, daraus folgt maximal DSR 0,589. Die 0,95-Hürde war
   unerreichbar. Korrigiert durch Annualisierung und Entfernen der DSR aus dem
   Entscheidungs-Gate (sie korrigiert dieselbe Multiplizität wie BH-FDR — als UND verkettet
   war es eine Doppelbestrafung).
2. **Die Mindest-Tradezahl wurde nach Sichtung der Ergebnisse gewählt.** Jetzt als
   Sensitivitätskurve über 8/12/15/20/30 berichtet.
3. **Doppelter Filter-Lag.** `filter_mask()` trägt den `i-1`-Versatz bereits in sich;
   `run_one()` prüfte nochmals `mask[e-1]`, also den Indikatorstand von `e-2`. Der Fehler
   wirkte *optimistisch* (4 → 1 Treffer bei der alten Schwelle) und ist behoben.
4. **Fehlende Abdeckungs-Transparenz.** Dass zwei Drittel des Rasters leer liefen, wies die
   Ausgabe nicht aus. Jetzt Bestandteil des Reports.

Unabhängig geprüft und **entlastet**: Indikator-Ports, 19 von 21 Strategie-Ports, alle
Statistik-Funktionen inklusive der DSR-Algebra, IS/OOS-Split am Entry-Datum,
Dividendenbereinigung. Auch die Sorge, die hohe Korrelation zwischen den Tests würde die
Deflation verzerren, ist gemessen und **widerlegt**: N_eff = 32,3 von 40; selbst mit 50
statt 1.004 effektiven Versuchen ändert sich nichts.

---

## 6. Offene Punkte

- **Kosten gehören in die Engine**, nicht in eine nachgelagerte Näherung. Erst dann ist die
  Rangliste unmittelbar interpretierbar.
- **Negativkontrollen einbauen.** Die Recherche liefert Goldstandard-Fälle (FOMC-Even-Week,
  RSP/SPY-Breadth). Wenn die Pipeline die durchwinkt, ist sie kaputt. Das ist der
  wichtigste nächste Schritt vor jeder Veröffentlichung.
- **Winsorisierter Gegentest** für alle Kandidaten: Wenn der Effekt bei Kappung des 1./99.
  Perzentils kollabiert, ist er ausreißergetrieben.
- **Produktionsinkonsistenz:** `landing/pages/backtest-engine.html:776` nutzt
  `filterMask[entryIdx-1]`, acht Analyse-Seiten indexieren ungeshiftet. Da die Maske den
  Versatz enthält, rechnet die produktive Engine mit einem Tag mehr Verzögerung. Die Regel
  in CLAUDE.md schreibt die `-1` ausdrücklich vor und beruht auf einem Missverständnis.
- **Reproduzierbarkeit der Blog-Zahl:** SPY/downmonth_tom ungefiltert ergibt Sharpe 0,15,
  nicht die dokumentierten 0,21 → 0,34 bei WR 68 → 72 %. Zwei unabhängige Tests haben die
  Zahl nicht reproduziert; sie steht in je einem veröffentlichten Artikel in DE und EN.

---

## 7. Empfehlung

**Nichts davon gehört in dieser Form auf die Website.** Ein Signal, dessen Edge im Spread
verschwindet, ist auf einer YMYL-Finanzseite kein Produkt, sondern ein Haftungsrisiko.

Weiterverfolgen würde ich genau eine Spur: **`downmonth_tom` + `lbr_bear` auf zyklischen
Sektor-ETFs** (XLB, XLI, IYT, RSP). Rendite pro Trade 2,3–2,9 %, Trefferquote 76–82 %,
Kosten dort unkritisch. Vor jeder Veröffentlichung: Winsorisierung, Kosten in der Engine,
Negativkontrollen — und eine Erklärung, warum ausgerechnet zyklische Sektoren.

# Konsolidiertes Urteil: `C:\dev\Seasonaledge\scripts\research\etf_seasonal_scan.py`

Alle Zahlen unten habe ich selbst nachgerechnet (aus `C:\dev\Seasonaledge\scripts\research\out\scan_candidates.json`) bzw. durch einen kompletten Neulauf des gepatchten Skripts gegen den 40-Ticker-Cache reproduziert.

## 1. Kurzfazit

**"Kein robuster Edge" ist als Zahl belastbar, als Aussage aber nicht.** Das Nullergebnis überlebt jede von mir getestete Reparatur — aber nur, weil das Entscheidungs-Gate so gebaut ist, dass es fast nichts durchlassen *kann*. Gleichzeitig ist die berichtete Null nicht das, was der Code ausgibt: mit `MIN_TRADES_OOS = 8` (Zeile 52) druckt das unveränderte Skript **4 Überlebende**. Die Null entsteht erst durch eine nachträglich gewählte 15-Trades-Hürde, die nirgends im Code steht und genau oberhalb der n_OOS-Werte (8, 8, 9, 11) dieser vier liegt. Das ist der schwerwiegendste Punkt für die Publizierbarkeit — unabhängig von jedem Bug.

## 2. Befunde, dedupliziert und nach Wirkung sortiert

### A — Würde das Nullergebnis umstoßen bzw. macht es unlesbar

| # | Befund | Ort | Richtung | Status |
|---|---|---|---|---|
| A1 | **DSR-Gate ist keine Signifikanz-, sondern eine Effektstärken-Schranke auf den PRO-TRADE-Sharpe.** `sr0 = 0.627`; `z = (sr − sr0)·√(n−1)` → liegt sr unter sr0, sinkt DSR mit wachsendem n. Implizite t-Hürde (denom≈1): T=15 → 4.13, T=30 → 5.11, T=127 → 8.72, T=300 → 12.51. Mehr Daten = schlechteres Urteil. | `evaluate()` Z. 682–702, `deflated_sharpe()` Z. 569–586 | Nullergebnis **erzwungen**, nicht gemessen | **verifiziert** |
| A2 | **Folge von A1: "0 Überlebende ab 15 OOS-Trades" ist arithmetisch garantiert.** Von 952 Kandidaten mit n_OOS ≥ 15 ist der höchste OOS-Sharpe 0.6654, daraus max. DSR = **0.5886**. Kein Datensatz der Welt hätte hier 0.95 erreicht. | dito | Tautologie | **verifiziert** |
| A3 | **`sr_var` poolt unvereinbare Skalen**: Halteperioden 1 Tag bis 182 Tage, n_OOS 8–383. BLdP setzt identisches T und identische Frequenz voraus. 49 % von `sr_var` sind reines Schätzrauschen (E[1/n] = 0.0181 von 0.0371). | `evaluate()` Z. 687–689 | zu pessimistisch für Vielhandler, zu optimistisch für Kleinst-n | **verifiziert** |
| A4 | **Post-hoc-Schwelle**: berichtete Null ≠ Code-Output (4 Überlebende bei `MIN_TRADES_OOS=8`). | Z. 51–52 | Reporting-Defekt | **verifiziert** |
| A5 | **DSR und BH-FDR korrigieren dieselbe Multiplizität, werden aber mit UND verkettet.** Nach Walk-Forward-Konsistenz + BH-FDR (q=0.10) + n≥15 bleiben **169 Tests** übrig; das DSR-Gate allein macht daraus 0. Verteilung: downmonth_tom 47/112 (**42 %**), one_day_holiday 38, monthly_10 33, uhts 31, month_end 19, second_trading_day 1 — ein Querschnittsmuster, kein Rauschen. | Z. 698–703 | zu pessimistisch | **verifiziert** |
| A6 | **Doppelter Filter-Lag**: `filter_mask()` baut `m[i]` schon aus `v[i-1]`, `run_one()` prüft nochmals `mask[e-1]` → Indikatorstand von **e-2**. Docstring Z. 20–21 behauptet das Gegenteil. Geerbt aus `landing\pages\backtest-engine.html:776`; die acht Analyse-Seiten (opex, monatswechsel, tdom-analyse …) indexieren die Maske korrekt ungeshiftet. | Z. 158–193 + Z. 617 | siehe unten | **verifiziert, Richtung korrigiert** |
| A7 | **2/3 des Testrasters lief leer.** 8 von 21 Strategien liefern **null** Kandidaten (sell_in_may faktisch 1, january_barometer, midterm, cycle_20_year, mid_decade, first/last_five_days, election_year_7m …), weil `MIN_TRADES=20` im IS bei Split 2016 für Jahresstrategien Kurse ab 1996 verlangt — das erfüllt von 40 ETFs nur SPY. 99 % der Kandidaten stammen aus 7 Strategien. Der Output weist das nirgends aus. | Z. 51, 677–680 | Überschrift "21 Strategien" nicht gedeckt | **verifiziert** (13 Strategien in der Kandidatenliste) |

**Zu A6, gegen zwei der Prüfer:** Ich habe den Lag-Fix (`mask[e]`) komplett durchgerechnet. Ergebnis: 999 Kandidaten / 721 konsistent / 211 FDR / **1 Überlebender** (XLK/downmonth_tom/lbr_bull, n_OOS = 10, DSR 0.987) — bei der Code-eigenen Schwelle also **4 → 1**, der Fehler wirkte im ausgelieferten Lauf also *optimistisch*, nicht pessimistisch. Bei n_OOS ≥ 15 bleiben es **0**; der von Prüfer 3 gemeldete Treffer XLI/downmonth_tom/lbr_bear kommt bei mir auf **DSR 0.806, nicht 0.960** — seine Behauptung, die Kernaussage kippe an dieser Indexierung, ist **nicht reproduzierbar**. Der Bug ist real und muss weg (er entwertet gerade die Mean-Reversion-Filter bb_below/rsi_lt30 um einen Tag), aber er trägt die Null nicht.

### B — Kosmetisch für das Nullergebnis (trotzdem fixen)

- **Overlap-Regel `e <= last_exit`** (Z. 615) existiert in `strategy-compute.js` nicht und löscht bei UHTS in jedem Jahr den Neujahrs-Trade (SPY: 39–40 von 312, davon ~35 im Dezember). Verworfene Trades: Ø −0,96 %, behaltene +0,33 % → die Engine zeigt UHTS **besser** als die Website. Kann kein Signal verstecken, macht Scan und Produkt aber unvergleichbar. Zusätzlich: sie läuft vor der Maskenprüfung, dadurch sind gefilterte Trade-Mengen keine Teilmengen der ungefilterten (UHTS-exklusiv, 163 Kandidaten).
- **Sonderschließungen** (9/11 ×4, Sandy ×2, Staatstrauer) aus `shared\nyse_holidays.py` werden als handelbare Feiertage behandelt — ex ante unbekannt, nicht handelbar, kostet uhts/one_day_holiday ~15 % OOS-Sharpe (also pessimistisch, aber nur marginal). Latent zusätzlich: Mehrfach-Duplikate desselben Trades, die derzeit nur von der Overlap-Regel verdeckt werden.
- **`n_trials = len(cand)` = 1004 statt 5880** (Z. 682) — inkonsistent, quantitativ irrelevant (siehe Abschnitt 3).
- **`MIN_TRADES_OOS=8` speist Skew/Kurtosis in die DSR** — Momente aus 8 Zahlen, die biased Kurtosis ist bei n=8 nach oben durch 6.14 beschränkt; alle 4 Original-Überlebenden haben kurt < 2. Reines Rauschen im Entscheidungskriterium.
- **`S_lbr_nov_mai`** (Z. 437–450): Entry-Fenster nur Okt–Dez statt Okt–31.03., erfundener Mai-Exit-Fallback statt Trade-Verwurf. Betrifft 9 Trades gesamt, 2 Kandidaten.
- **`S_uhts` ohne den 1,5×-Hebel** des Originals — skaleninvariante Kennzahlen unberührt, ohne Einfluss auf Überleben.
- **`filter_mask` fällt bei unbekanntem Filternamen still auf all-False** (kein `else: raise`) — genau die Fehlerklasse, die eine Null unsichtbar fabriziert. Aktuell inaktiv.
- **Test gegen µ > 0 statt gegen Buy&Hold** — 74 % aller Kandidaten sind in beiden Perioden positiv; `consistent` misst Marktdrift, nicht Saisonalität.

### C — Entlastet (von mehreren Prüfern unabhängig geprüft, deckungsgleich)

Indikator-Ports (`rsi`, `sma`, `ema`, `bollinger`, `macd`, `lbr`) sind bitgenau identisch mit `landing\js\indicators.js` (Node-Diff über 6.902 bzw. 8.444 Bars, max |Δ| ~1e-12); 19 von 21 Strategie-Ports liefern trade-identische Entry/Exit-Listen gegen `landing\js\strategy-compute.js`; `t_sf`, `_norm_ppf`, `_betai`, `bh_fdr`, `moments` und die **DSR-Algebra selbst** (inkl. 1−1/(N·e) und Nicht-Exzess-Kurtosis-Konvention) sind korrekt. IS/OOS-Split am Entry-Datum ist richtig. Kurse sind dividendenbereinigt. COVID/2022 als Erklärung wurde geprüft und **widerlegt** (Effekt ≤ 0.01 Sharpe). Der Fehler steckt ausschließlich im **Input** der DSR, nicht in ihrer Formel.

## 3. Zur Korrelationsfrage: gravierend? **Nein — das ist der falsche Verdächtige.**

Ich habe die Sensitivität direkt gemessen. `sr0` hängt nur über √(2·ln N) von der Versuchszahl ab:

| n_trials | 5880 | 1004 | 810 | 350 | 144 | 50 | 21 |
|---|---|---|---|---|---|---|---|
| sr0 | 0.718 | 0.627 | 0.615 | 0.567 | 0.512 | 0.438 | 0.370 |
| Überlebende (FDR+konsistent, n≥15) | 0 | 0 | 0 | 0 | 0 | 0 | 2 |

Selbst wenn man die 1.004 Tests auf **50 effektive** Versuche eindampft — härter als jede vertretbare Schätzung — ändert sich am Ergebnis nichts. Zum Vergleich: die gemessene mittlere Paarkorrelation der 40 ETFs (Tages-Log-Returns ab 2016) liegt bei 0.376, Cheverud/Li-Ji ergibt **N_eff = 32,3 von 40**; das Gold-/Anleihen-/Öl-/Krypto-Segment hält die Redundanz niedrig. Die Filter-Redundanz (7 Varianten je Strategie) ist der größere Hebel, aber selbst kombiniert landet man bei N_eff ≈ 300–400 → sr0 ≈ 0.57. Irrelevant.

**Der wirklich gravierende Skalen-Fehler ist ein anderer:** `sharpe` ist ein Sharpe **pro Trade**, `sr0` eine feste absolute Schranke darauf. Damit hängt die faktische Hürde an der Handelsfrequenz — annualisiert entspricht sr0 = 0.627 einem Sharpe von 2,96 für monthly_10 (22 Trades/Jahr), aber nur 0,69 für cycle_40w (1,2 Trades/Jahr): **Faktor 4,3, rein aus der Haltedauer.** Das JS-Original macht es richtig (`computeStats`: `sharpe = avg/std * sqrt(tradesPerYear)`).

**Korrekte Behandlung, in dieser Reihenfolge:**
1. Sharpes **vor** der `sr_var`-Schätzung auf eine gemeinsame Frequenz bringen (annualisiert oder Tages-Renditereihe mit n_obs = Handelstage). Ich habe das durchgerechnet: `sr_var` steigt auf 0.0943, sr0_ann = 1.00 — und die **Rangfolge kippt vollständig**: GLD/uhts/rsi_gt50 (n_OOS = 53) springt von DSR 0.404 auf **0.973** und überlebt, während alle Kleinst-n-Artefakte verschwinden. Das ist der eigentliche Beweis, dass das alte Gate das Falsche gemessen hat.
2. `sr_var` **familienweise** (homogene Halteperiode) und rauschbereinigt (Var_obs − E[1/n]) schätzen.
3. Multiplizität **einmal** korrigieren: BH-FDR über die OOS-p-Werte als Entscheidungsregel, DSR nur als berichtete Kennzahl — nicht beides als UND-Gate. `n_trials` auf die tatsächlichen 5880 setzen (oder auf die Stufe-2-Zahl bei echtem zweistufigem Walk-Forward).
4. Vor jeder Null-Aussage eine **Power-Kurve** mitliefern: synthetische Reihen mit bekanntem SR_true durch dieselbe `evaluate()`-Pipeline. Gegen die aktuelle Hürde liegt die Detektionswahrscheinlichkeit für einen exzellenten Saisonal-Edge (SR_true = 0.35/Trade) bei ~0.0002 und **fällt** mit T.

## 4. Fazit und Reihenfolge

Ehrlichste Formulierung des Laufs heute: *"169 von 1.004 auswertbaren Tests bestehen Walk-Forward-Konsistenz und BH-FDR bei q=0.10 mit ≥15 OOS-Trades, konzentriert auf downmonth_tom (42 % seiner Varianten), one_day_holiday, monthly_10, uhts und month_end. Keiner davon übersteht zusätzlich ein Deflated-Sharpe-Gate — das aber in seiner aktuellen Skalierung nichts überstehen lassen kann, was mehr als 14 Trades hat."*

Zwei ergänzende Einschränkungen, die für das Ergebnis sprechen: Der Lag-Fix und alle N_eff-Varianten ändern bei n≥15 nichts (0 Überlebende), und die Kombination Lag-Fix + Annualisierung ergibt ebenfalls 0. Ein *starker* Edge ist in diesen Daten also tatsächlich nicht sichtbar. Aber die Studie darf nicht behaupten, sie hätte danach gesucht — sie hat gegen eine Hürde getestet, die mit der Stichprobe wächst, in 2/3 des Rasters gar nicht erst gemessen und die berichtete Zahl über eine nach Sichtung gewählte Schwelle erzeugt.

**Reparaturreihenfolge vor jeder Veröffentlichung:**
1. Sharpe + `sr_var` konsistent annualisieren bzw. familienweise deflatieren (A1/A3) — allein das ändert die Kandidatenliste komplett.
2. DSR aus dem UND-Gate nehmen, BH-FDR als Entscheidungsregel; `n_trials = 5880` (A5).
3. `MIN_TRADES_OOS` a priori festlegen und als Sensitivitätskurve über 8/12/15/20/30 berichten, nicht als Einzelwert (A4).
4. Filter-Lag fixen (`mask[e]`, Z. 617), Docstring Z. 20–21 richtigstellen — **und** `landing\pages\backtest-engine.html:776` auf `filterMask[entryIdx]` angleichen, sonst rechnet die produktive Engine dauerhaft anders als die acht Analyse-Seiten (A6).
5. `MIN_TRADES` horizontabhängig setzen bzw. Jahresstrategien gepoolt testen, und je Strategie ausweisen, wie viele Tests überhaupt auswertbar waren (A7).
6. Overlap-Regel für Feiertagsstrategien abschalten, Sonderschließungen aus dem Scan-Kalender nehmen, `filter_mask` fail-loud machen (B).

Erst danach ist ein Nullergebnis eine Aussage über den Markt.
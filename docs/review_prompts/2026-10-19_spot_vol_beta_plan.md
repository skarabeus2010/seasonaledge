# Review: /spot-vol-beta nach dem SpotGamma-Artikel vom 16.10.2026 — Befund + Änderungsplan (Runde 1)

Du prüfst **read-only**. Repo: `C:\dev\SeasonalEdge`. Seite: `landing/pages/spot-vol-beta.html`
(Rechnung inline im `<script>`), Backend-Zwilling `shared/spot_vol_beta.py` (Nightly schreibt nur
`rolling_beta_60` nach `spot_vol_beta`, die Seite liest die DB-Tabelle nicht, sie rechnet selbst aus
`prices`). EN-Texte `landing/i18n/en.json` (`svb.*`), DE-Text steht in der Seite.

## Anlass

SpotGamma (16.10.2026) schreibt: (1) der VIX sei in Prozent typischerweise etwa fünfmal so volatil wie der
SPX, (2) Freitags Sprung sei rund viermal diese Rate gewesen, (3) VVIX +~20 % auf 110, (4) VIX 16 → Intraday-Hoch
22 (+40 %) in zwei Stunden, (5) Grafik „VIX points vs SPX, every day since 1990“: nur 9 Tage hatten einen
größeren VIX-Sprung (Punkte) bei kleinerem SPX-Rückgang als „heute“ (intraday VIX +3,7 Pkt, SPX −1,1 %),
9 264 Schlusskurse Jan 1990 – 15.10.2026. Dazu die Erklärung über Dealer, die ~300k gekaufte VIX-Calls
(Nov-18) short seien.

## Nachrechnung (Supabase `prices`, ^GSPC/^VIX, ab 1990-01-02; Skript lief im Container, nur lesend)

| Aussage | Unser Wert | Urteil |
|---|---|---|
| 9 264 Schlusskurse bis 15.10. | 9 264 | identisch |
| VIX „~5× so volatil“ | OLS-Beta VIX-% auf SPX-%: −4,44 (ab 1990), −5,74 (ab 2010), −5,57 (5 J.), −7,89 (1 J.); Verhältnis der Std.-Abw.: 6,3 / 7,7 / 7,4 / 9,7; Korrelation −0,70…−0,82 | stimmt als Regressionsbeta ab 1990; als Std.-Verhältnis eher 6–8× |
| Freitag „~4× die Rate“ | Schluss: SPX −1,09 %, VIX 16,46 → 19,99 = +3,53 Pkt / +21,45 %; Verhältnis 19,6 = 3,9 × 5 | stimmt |
| VVIX ~+20 % auf 110 | Yahoo ^VVIX 92,57 → 109,91 (+18,7 %), Hoch 121,17 | stimmt |
| VIX 16 → 22 (+40 %) | Eröffnung 16,02, Hoch 22,31 (+39 % ab Eröffnung, +35,5 % ab Vortagesschluss) | stimmt; „zwei Stunden“ nicht prüfbar |
| „nur 9 Tage“ | VIX > +3,7 Pkt UND SPX-Minus kleiner als 1,1 %: **5** Tage (1998-09-03, 2001-10-12, 2016-06-13, 2020-07-13, 2025-10-16); mit den Schlusswerten (+3,53 Pkt, −1,09 %): **8** | Größenordnung stimmt, 9 nicht reproduziert (Intraday-Stand, andere Datenquelle oder andere Grenze) |
| Dealer short Nov-Calls | nicht prüfbar (keine VIX-Optionsdaten); „Käufer → Dealer short“ ist Modellannahme | nicht prüfbar |

**Methodischer Einwand gegen die Grafik:** VIX-Punkte skalieren mit dem Niveau. 3 der 5 Tage starteten bei
VIX 27–37, Freitag bei 16,5. In **Prozent** (wie unsere Seite rechnet): VIX > +21,4 % bei SPX-Minus kleiner
als 1,09 % gab es 5-mal (1993-07-06, 2016-06-13, 2018-01-29, 2018-10-04, 2025-10-16). Gegen die OLS-Gerade
(VIX-% auf SPX-%): erwartet +5,3 %, Ist +21,4 %, Residuum +16,2 Pp, z = 3,2, Rang 86 von 9 264 (ab 1990);
5 Jahre: Rang 13 von 1 254. Aussage „ungewöhnlich“ hält, „extrem selten“ hängt an der Punkte-Skala.

## Defekte, die die Nachrechnung auf unserer Seite zeigt

1. **Regime-Schwellen sind für Prozent-auf-Prozent sinnlos.** `classifyBeta` (JS) und `classify_beta` (Python):
   ≤ −0,8 „stark negativ“, ≤ −0,3 „negativ“, < 0,3 „nahe null“. Das echte Beta liegt bei −4…−8 → das Badge zeigt
   immer „stark negativ“, Methodik-Text („β zwischen −0,3 und −0,8 = normal“) ist falsch.
2. **„Beta Stress“ (Rolling-60-Beta ≤ −1,0) feuert praktisch immer:** 99,4 % aller Tage seit 1990, 100 % der
   letzten 5 Jahre (Quantile Rolling-Beta: min −19,1, p5 −11,8, Median −5,6, p95 −2,2, max −1,08).
   `firstDayOfRegime` mit 10 Zeilen Mindestabstand erzeugt dann alle 10 Handelstage ein „Event“ — der Tab misst
   die unbedingte Forward-Rendite und nennt sie „Panik-Regime, Wendepunkt?“.
3. **VRP-Fenster:** Seite rechnet RV über 30 Handelstage, einfache Renditen, Populations-Std. Projektstandard
   (`shared/realized_vol.py`, v52-Lehre) ist 21 HT, Log-Renditen, ÷(N−1). Wirkung heute klein (VRP 9,96 vs 9,79,
   5-J-Median 3,70 vs 3,71), aber es ist eine zweite Formel und der Text sagt „30d“.
4. Die Frage, die der Artikel stellt („wie ungewöhnlich war der letzte Tag?“), beantwortet die Seite nicht —
   der Scatter zeigt nur einen Punkt „Heute“.

## Plan (bitte prüfen, bevor Code entsteht)

**P1 Regime relativ zur eigenen Historie** (JS + Python gleich):
- Gesamt-Beta wird als Zahl mit Lesart gezeigt: „VIX-Änderung je 1 % Spot“ (z. B. −4,4 % je 1 %). Kein festes
  Badge mehr aus absoluten Schwellen.
- Regime-Badge aus dem **aktuellen Rolling-60-Beta gegen seine eigene Verteilung im gewählten Zeitraum**:
  Rolling-Beta > 0 → „positiv (anomal)“; Perzentil ≤ 20 → „Vol reagiert stärker als üblich“; ≥ 80 → „schwächer
  als üblich“; sonst „üblich“. Perzentil mit `percentile()` (linear, wie numpy).
- Python `classify_beta` bekommt dieselbe Funktion für Rolling-Beta + Verteilung (wird nur in Metriken genutzt,
  die Nightly nicht schreibt) — oder: Python-Klassifikation entfernen, weil kein Aufrufer sie liest? (Deine Meinung.)

**P2 Beta-Stress als Perzentil:** Eingabe „Beta Stress“ wird „Beta-Stress-Perzentil“ (Standard 10 %): Event =
Rolling-Beta ≤ p10 der Rolling-Beta-Verteilung **im Zeitraum** (Look-ahead: die Schwelle kennt die Zukunft des
Fensters — wir kennzeichnen das als beschreibend; Alternative: expandierendes Perzentil nur aus Vergangenheit,
erst ab 252 Werten). Welche Variante? Ich tendiere zu expandierend (kein Look-ahead in einer Forward-Return-Tabelle).
Event-Bildung: echter Regime-Eintritt (Bedingung war am Vortag falsch) + 10 HT Mindestabstand, statt „alle 10 Zeilen,
solange die Bedingung gilt“ — gilt dann auch für Vol-Spike/Complacency (bisher: während VIX > 30 alle 10 Tage ein
neues Event → überlappende, abhängige Fenster). Python `_first_day_of_regime` (Kalendertage) entsprechend.

**P3 „Letzter Handelstag gegen die Regression“** (neuer Kasten unter dem Scatter, DE+EN):
erwartete Vol-Änderung aus α+β·Spot-Rendite (Gesamt-OLS des Zeitraums **ohne** den letzten Tag), Ist, Residuum
in Pp, z (Residuen-Std.), Rang „k von N Tagen hatten ein höheres Residuum“, dazu die Zählung im Stil der Grafik,
aber in Prozent: „Tage mit größerem Vol-Anstieg bei kleinerem Spot-Rückgang: k“ (nur wenn Spot-Rendite < 0 und
Vol-Änderung > 0, sonst Kasten-Text für den anderen Fall). Fallzahl N immer dabei. Kurzer Methodik-Satz, warum
Prozent statt Punkte (Punkte skalieren mit dem Niveau).

**P4 VRP auf 21 HT / Log / ÷(N−1)** wie `shared/realized_vol.py` (JS-Kopie der Formel, Zwillingstest gegen
`rv_reihe`), Texte „30d“ → „21 Handelstage (≈ 30 Kalendertage)“. VRP-Text „short-vol opportunity“ /
„often a precursor“ (EN) bzw. DE-Gegenstück entschärfen — das ist eine Empfehlung bzw. eine unbelegte Prognose.

**P5 Methodik-Texte** (DE in der Seite + `en.json`, `_JSON_VER` erhöhen): Interpretation der Beta-Größe
(VIX: typisch −4…−6 % je 1 %), Regime-/Stress-Definition neu.

**Wächter:** `scripts/verify_spot_vol_beta.py`: führt die Seitenfunktionen (aus dem Inline-Script gezogen, in node)
auf echten/fixen Reihen aus und vergleicht mit einer unabhängigen numpy-Referenz (OLS, Rolling, Perzentil,
Residuum/Rang, Event-Eintritte, RV21); Mutationstest; ins Gate.

## Fragen an dich
1. Stimmen meine Nachrechnung und das Urteil zu SpotGamma? Übersehe ich eine Lesart, unter der „9 Tage“ und „5×“
   exakt herauskommen?
2. Ist der Plan P1–P5 tragfähig? Insbesondere: expandierendes Perzentil vs. Zeitraum-Perzentil; ist ein Residuum
   gegen die **gesamte** OLS-Gerade des Zeitraums das richtige Maß, oder besser gegen das Rolling-Fenster (lokales Regime)?
3. Weitere Defekte auf der Seite, die ich nicht genannt habe (Bucket-Tabelle, Forward-Fenster, Joins, Zeitzonen,
   `yearsFilter` mit `toISOString`, OVX mit `CL=F`-Rollsprüngen, …)?

Antworte mit: Befunden (Schwere, Datei:Zeile, Beleg), Urteil zum Plan („tragfähig“ / „nicht tragfähig“ + Auflagen).

# Konsolidierte Shortlist — 45 Kandidaten → 12 Implementierungs-Kandidaten

**Bewertungsmassstab:** Replikations- und Out-of-Sample-Evidenz durch *fremde* Autoren auf *anderen* Daten schlägt jede Originalstudie. Cross-Country-Breite innerhalb einer Studie zählt nur teilweise (Aktienmärkte teilen einen dominanten gemeinsamen Faktor — 64 Länder sind keine 64 unabhängigen Tests).

---

## 0. Dedupe- und Ausschluss-Protokoll (45 → 12)

### Zusammengelegt (dasselbe Konzept unter anderem Namen)

| Zusammengelegt zu | Aus den Einträgen | Begründung |
|---|---|---|
| **Range-Position (IBS/%K)** | IBS · Mehrtages-%K/Williams %R · Cutler-RSI(3)+IBS-Gate | %K mit n=1 **ist** IBS. Der Cutler-Eintrag ist „vorhandener RSI + IBS-Gate" — der neue Teil ist ausschliesslich das IBS-Gate. |
| **Realized-Vol-Regime (Garman-Klass)** | Garman-Klass-Perzentil · Yang-Zhang · ATR-Perzentil · Vol-of-Vol · VTS 21/252 | Alle messen dasselbe Vola-Konstrukt mit Korrelationen 0,85–0,95. GK gewinnt empirisch (Molnár 2012, G7 2025). YZ + ATR haben zusätzlich den **Cross-Day-Adjustierungs-Bug** (`ln(O_t/C_{t-1})` bzw. `|H_t − C_{t-1}|`) → auf adjustierten Kursen bei jedem Ex-Div-Tag falsch. |
| **Vol-Targeting** | Vol-Targeting-Overlay (trend) · Inverse-Vola-Skalierung (vola) | Identische Formel, zwei Einträge. |
| **Absorption Ratio ΔAR** | ΔAR (breadth) · Absorptionsrate Sektor-ETFs (crossasset) | Identisch. Die 9-Sektor-Variante (XLB/XLE/XLF/XLI/XLK/XLP/XLU/XLV/XLY, alle ab 1998) ist die implementierbare, weil kein Universum-Sprung mitten im Backtest. |
| **RSP/SPY** | RSP/SPY (breadth) · RSP/SPY (crossasset) | Identisch, beide mit Null-Befund. |
| **Gold-Ratio** | Gold-Platin (GP) · Gold-Kupfer (GC) | Konzeptionell identisch („Gold vs. zyklisches Metall"), vermutlich hoch korreliert. GP hat die bessere Instrumentenlage (PPLT physisch, kein Roll-Bias). |
| **12M-Trendfilter** | TSMOM-12M · SMA200 · MAD · Momentum-Turning-Points (SLOW-Teil) · Cross-Asset-TSMOM (trend_SPY-Teil) · Canary 13612W (12M-Term) | Alle sind Varianten des Vorzeichens der 12-Monats-Rendite und damit **funktional euer Carhart-Filter**. Marshall/Nguyen/Visaltanachoti (2017) zeigen die Äquivalenz von MA-Regeln und TSMOM explizit. |

### Verworfen wegen Redundanz zum Bestand

- **TSMOM-12M, SMA200, MAD, Momentum-Turning-Points, Canary-DAA** — Carhart-12M-Duplikate. Kein Neuwert, nur zusätzliche Freiheitsgrade zum Overfitten.
- **ConnorsRSI (Vollversion)** — Komponente 1 ist euer RSI(3). Einzig orthogonale Komponente: **Streak-RSI(2)** (misst Dauer statt Grösse). Als Ehrenerwähnung geführt, nicht in der Top-12, weil keinerlei OOS.
- **Efficiency Ratio** — eine einzige Studie, die nicht einmal die ER selbst testet, sondern ein verwandtes Mass. Genau das Profil, das euch zweimal erwischt hat.
- **avgcor / CSD / Beta-Dispersion** — messen alle drei Facetten derselben Kovarianzstruktur wie ΔAR. Kritzman et al. begründen explizit, warum ΔAR die bessere Variante ist.

### Verworfen wegen Datenlage

- **Credit-/Yield-Curve-Proxys (HYG/LQD, TLT/SHY)** — technisch onboardbar, aber die Lead-Lag-Literatur sagt, dass **Aktien Bonds führen**, nicht umgekehrt. Ihr würdet eine verzögerte Kopie eures eigenen Aktiensignals bauen. Zusätzlich von Goyal/Welch/Zafirov (RFS 2024) explizit verworfen.
- **Vol-of-Vol** — die belegte Variante ist **optionsimplizit** und **querschnittlich**. Eure realisierte Zeitreihen-Variante ist eine ungetestete Umdeutung.
- **Gold-Kupfer** — CPER/COPX/XME sind alle keine saubere Kupfer-Proxy (Roll-Yield bzw. Aktien-Beta).

---

## (a) TOP-12 SHORTLIST

Sortiert nach Belastbarkeit der unabhängigen Evidenz, nicht nach erwarteter Rendite.

---

### #1 — Familienweiter Bootstrap-Gate + vola-standardisierter Saison-Z-Score
**Familie:** Methode (kein Handelssignal) · **Unabhängige Tests überstanden: 3/3 (als Methode)**

Das ist die direkte Antwort auf eure schmerzliche Lektion und muss **vor** allem anderen implementiert werden. Beide gescheiterten Edges wären hier hängengeblieben.

**Formel**

```
# Schritt 1: ex-ante Tagesvola (Garman-Klass, nicht annualisiert)
gk_i    = 0.5*(ln(H_i/L_i))^2 - (2*ln(2)-1)*(ln(C_i/O_i))^2
gk_i    = max(gk_i, 0)                     # Clip; Tage mit H==L verwerfen
sigma_d[t] = sqrt( mean(gk_i, i = t-20..t) )

# Schritt 2: Standardisierung (Molnár 2012: z ist bei GK naeherungsweise normal)
r[t] = ln(C[t]/C[t-1])
z[t] = r[t] / sigma_d[t-1]                 # strikt vorwaerts, kein Look-ahead

# Schritt 3: Saison-Statistik fuer Fenster S
m_S  = mean(z[t] : t in S)
t_S  = m_S / (SE_NeweyWest(z[t] : t in S))     # Lag ~ Fensterlaenge

# Schritt 4: familienweiter Bootstrap (White Reality Check / Hansen SPA)
#   Familie F = ALLE Regeln, aus denen S gewaehlt wurde
#   (z.B. alle Paare 1 <= a <= b <= 21 fuer TDOM = 231 Regeln, mal Ticker, mal Filter)
#   10.000 stationaere Block-Bootstrap-Resamples der z-Reihe, mittlere Blocklaenge ~21 HT
#   pro Resample: max(t_S) UEBER DIE GANZE FAMILIE
p_familie = Anteil der Resamples mit max(t_S) >= t_S_beobachtet
```

**Aufnahmeregel (alle drei Bedingungen müssen erfüllt sein):**
1. `p_familie < 0.05` — **nicht** der nackte Einzel-t-Wert.
2. Vorzeichen in erster und zweiter Sample-Hälfte gleich UND in beiden Hälften nominell signifikant.
3. Der z-basierte t-Wert fällt gegenüber dem roh-return-basierten um **weniger als 30 %**. Fällt er stark ab, kam die „Signifikanz" aus wenigen Hochvola-Tagen und nicht aus einem Saisonmuster.
4. Zusätzlich: **Anzahl aller jemals getesteten Kombinationen** (Ticker × Fenster × Filter) protokollieren und in `p_familie` einrechnen. Genau dieses Protokoll fehlt fast immer.

**Evidenzlage:** Connolly (JFQA 1989, Wochenendeffekt bricht unter GARCH+robusten Verfahren zusammen) · Sullivan/Timmermann/White (JF 1999 / J.Econometrics 2001, 9.452 Kalenderregeln → beste Regel schlägt Buy&Hold nach Korrektur nicht) · NAJEF 2026 („Calendar anomalies: Real patterns or data-mining artifacts?", familienweise Bootstrap-Korrektur über mehrere Anomalie-Familien und Länder). Drei unabhängige Methoden-Replikationen aus drei Ären.

**Wichtiger Gegenbefund, den ihr einbauen müsst:** Agnani & Aray (Quantitative Finance 2011) zeigen mit Markov-Regimewechsel, dass der Januar-Effekt im **Hoch**vola-Regime **grösser** ist. Ein pauschales „bei hoher Vola aussetzen"-Gate (#5) kann also für einzelne Saisoneffekte kontraproduktiv sein. Die Richtung muss **pro Effekt empirisch bestimmt** werden, nicht angenommen.

---

### #2 — Heston-Sadka Same-Calendar-Month Seasonality (annuale Lags)
**Familie:** seasonal · **Unabhängige Tests überstanden: 4 (davon 1 durch erklärte Skeptiker), 1 partieller Fehlschlag (Emerging Markets)**

Der belastbarste Einzelkandidat der gesamten Liste — und er passt direkt in euer Kerngeschäft.

**Formel**

```
# Monatsrenditen aus Tages-Closes, boersenspezifischer Kalender
r_m = Close(letzter HT in Monat m) / Close(letzter HT in Monat m-1) - 1

# Am ersten HT von Monat t, je Ticker, fuenf Lag-Aggregate (Kalendermonate):
R1a     = r[t-12]
R2_5a   = mean(r[t-24],  r[t-36],  r[t-48],  r[t-60])
R6_10a  = mean(r[t-72],  r[t-84],  r[t-96],  r[t-108], r[t-120])
R11_15a = mean(r[t-132], r[t-144], r[t-156], r[t-168], r[t-180])
R16_20a = mean(r[t-192], r[t-204], r[t-216], r[t-228], r[t-240])
# Term nur bilden, wenn >= 60 % der benoetigten Lags vorhanden, sonst NaN

# Querschnitts-Variante (bevorzugt, entspricht dem Paper):
#   je Term Perzentilrang ueber alle Ticker (LINEARE Interpolation, kein Floor-Indexing)
SEAS_SCORE = Mittelwert der verfuegbaren Raenge          # 0..100

# Zeitreihen-Variante (falls Single-Ticker Long/Flat noetig):
SEAS_Z = (R6_10a[ticker, Monat_t] - mean ueber die 12 Kalendermonate desselben Tickers)
         / std ueber diese 12 Werte
```

**Signalregel:** Monatliches Rebalancing, Position gesetzt zum Close des letzten HT des Vormonats (look-ahead-frei — alle Lags sind ≥ 12 Monate alt).
- Querschnitt: Long/Flat auf das oberste Dezil von `SEAS_SCORE` (≥ 90. Perzentil); robuster: oberstes Quintil.
- **Als Filter (unser eigentlicher Use-Case):** TDOM-/Sell-in-May-Einstieg nur zulassen, wenn `SEAS_SCORE >= 60`; unterdrücken bei `SEAS_SCORE <= 30`.
- Zeitreihen: Long bei `SEAS_Z >= +0.5`, flat bei `SEAS_Z <= -0.5`.
- **Stärkstes Einzelsignal ist `R6_10a` (Lags 6–10 Jahre), nicht `R1a`.**

**Evidenzlage:**
1. Heston & Sadka, JFE 2008 (CRSP 1965–2002) — Original.
2. Heston & Sadka, J. Empirical Finance 2010 — Kanada, Japan, 12 europäische Länder. *Geografisch OOS.*
3. Keloharju/Linnainmaa/Nyberg, JF 2016 — andere Autoren, ausgeweitet auf **Commodities und Länderindizes**. *Asset-Klassen-OOS.*
4. **Hou/Xue/Zhang, „Replicating Anomalies", RFS 2020** — bauen alles aus Rohdaten neu, NYSE-Breakpoints, value-weighted, Microcaps entschärft; **~64 % aller 452 Anomalien fallen durch**, Heston-Sadka nicht: High-minus-Low 0,65 / 0,69 / **0,83** / 0,67 / 0,56 % pro Monat (t = 3,23 / 4,00 / **4,91** / 4,66 / 3,29). Das ist eine Replikation durch erklärte Anomalie-Skeptiker.
5. Li/Zhang/Zheng, J. Empirical Finance 2018 — Advanced Markets klar, Emerging Markets deutlich schwächer. *Partieller Fehlschlag.*

**Realistische Erwartung:** McLean & Pontiff (JF 2016) Basisrate: −26 % OOS, −58 % nach Publikation. **Rechnet mit einer Halbierung.** Zusätzlich: der Effekt ist am stärksten in kleinen/illiquiden Titeln — bei 40 liquiden US-ETFs ist das obere Ende abgeschnitten. Auf euren Dow-30/DAX-40-Einzeltickern ist er stärker zu erwarten als auf ETFs.

**Abgrenzung:** HS nutzt genau die Monate, die Carhart-Momentum **ausschliesst** (Lag 12, 24, 36 …). Eure Jahreszyklus-Charts bilden die Lags 6–20 Jahre gar nicht ab.

---

### #3 — Range-Position: IBS (n=1) und Mehrtages-%K (n=3,5)
**Familie:** meanrev · **Unabhängige Tests überstanden: 2, mit 1 dokumentiertem geografischen Totalausfall**

Die einzige echte **neue Informationsquelle** aus eurem Datenbestand: alle bestehenden Indikatoren (RSI, Bollinger, MACD, LBR, Momentum, StRev) sind Close-basiert. IBS nutzt High/Low.

**Formel**

```
# n = 1  (IBS)
IBS[t] = (C[t] - L[t]) / (H[t] - L[t])
   falls H[t] == L[t]:  IBS[t] = 0.5      # NIEMALS durch 0 teilen

# n > 1  (Mehrtages-Range-Position, = Stochastik %K roh)
HH_n[t] = max(H[t-n+1..t]);  LL_n[t] = min(L[t-n+1..t])
K_n[t]  = 100 * (C[t] - LL_n[t]) / (HH_n[t] - LL_n[t])
   falls HH_n == LL_n:  K_n[t] = 50
# KEIN Glaettungs-%D — die Glaettung ist der Teil, der bei Micaletti verliert
```

**Split-/Dividenden-Sicherheit:** IBS ist invariant gegenüber proportionaler Adjustierung, solange O/H/L/C **desselben Tages** mit demselben Faktor skaliert sind. Kein Cross-Day-Problem → kompatibel mit eurer bestehenden Regel.

**Signalregel (Filter, nicht Standalone):**
- Entry-Trigger **innerhalb** eines Saison-Fensters statt blindem Kauf am TDOM-Start: `IBS[entryIdx-1] <= 0.20` bzw. `K_5[entryIdx-1] <= 20`.
- Standalone-Variante zum Kalibrieren: Long ab Close bei `IBS <= 0.20`, Exit Close t+1; oder halten solange `IBS <= 0.5`, Zwangsexit bei `IBS >= 0.80`.
- **Plateau-Test statt Punktoptimierung (Pflicht):** Entry-Schwellen 0,15–0,25 und Exit-Schwellen 0,50–0,80 müssen **alle** positiv sein. Wenn nur eine Zelle funktioniert, ist es Curve-Fitting. Genau dieser Test hat bei euren zwei gescheiterten Edges vermutlich gefehlt.

**Evidenzlage:**
1. Pagonidis (2013), 33 US-Equity-ETFs, Inception–05/2013 (SPY ab 1993, ⌀ 3.363 Beobachtungen). Unterstes IBS-Quintil +0,350 %/Tag, oberstes −0,126 %; Spread +0,476 %. Für euch relevant: SPY +0,199 %, QQQ +0,330 %, IWM +0,256 % (SPY/QQQ auf 1 %-Niveau signifikant). Up-Day-Wahrscheinlichkeit 56,8 % vs. 46,2 %.
2. **Micaletti (SSRN 4339128, 2023)** — unabhängige Replikation der Indikator**klasse** auf globalem Aktienuniversum, ~10 Jahre nach Pagonidis' Sample-Ende, über eine breite Matrix aus Parametern/Schwellen/Haltedauern. Befund: **Range-basierte Indikatoren dominieren long und short; Change-basierte (RSI, TSI) sind die schlechtesten.** Aussage über eine Klasse, nicht über einen optimierten Parametersatz → deutlich weniger Data-Mining-anfällig.
3. Kinlay (2019), SPY/EWS/XOM 1999–2016 — unabhängig, ~13 % CAGR auf SPY, **findet aber Abschwächung ab ca. 2013**. Equity-Kurve bleibt innerhalb des 99 %-Konfidenzbands, Bruch also statistisch nicht bestätigt.

**Harte geografische Einschränkung:** Pagonidis findet den Effekt **nur bei US-gelisteten ETFs**. Lokale Index-ETFs in Frankreich, Österreich, Deutschland, Spanien, Schweiz, Taiwan, UK zeigen ihn gar nicht oder schwächer — **beim deutschen DAX-ETF ist er invertiert**. Für eure `.DE`/`.PA`/`.MI`-Ticker **nicht** ungeprüft übernehmen.

**Zusatzverstärker (bei Pagonidis dokumentiert):** stärker an Tagen mit Range `(H−L)/C >= Median(500 Tage)`; stärker bei 20d-Realvola über ihrem Median; Montag am stärksten, Freitag am schwächsten.

**Messbarer Zusatznutzen (Pagonidis Tab. 15):** Das IBS-Gate entfernt ~43 % der Markttage eines RSI(3)-Systems **und** erhöht die Gesamtrendite um ~9,6 Prozentpunkte. Weniger Zeit im Markt bei mehr Rendite = echte Information, nicht nur Leverage-Reduktion. **Baut genau das:** bestehenden RSI(3) behalten, NUR das IBS-Gate ergänzen → Zusatznutzen sauber messbar.

**Walk-Forward-Pflicht:** Split bei 2013 (Kinlays Bruchpunkt).

---

### #4 — Vola-State-Gate für Mean Reversion (Nagel-Konditionierung)
**Familie:** meanrev/regime · **Unabhängige Tests überstanden: 2 (Top-3-Journal + unabhängige Instrumentenklasse), 1 Richtungs-Caveat**

Der einzige Kandidat mit einem **ökonomischen Mechanismus statt einer Musterfindung** — und deshalb der mit dem geringsten Decay-Risiko.

**Formel**

```
r[t]    = ln(C[t]/C[t-1])
RV20[t] = std(r[t-19..t], ddof=1) * sqrt(252)
RVpct[t]= Perzentilrang von RV20[t] in RV20[t-503..t]      # 504 HT = 2 Jahre
          # LINEARE Interpolation wie numpy.percentile, NICHT Floor-Indexing
          # (steht bereits in eurer UI_PATTERNS.md)

# Alternativ, falls ^VIX im Universum:
VIXstate[t] = 1 wenn Close(^VIX)[t] >= Median(Close(^VIX)[t-59..t])
```

**Signalregel — reiner Zustands-Multiplikator, kein eigener Entry:**
- Mean-Reversion-Long (IBS, %K_n, StRev) **nur** eingehen, wenn `RVpct[entryIdx-1] >= 0.50`.
- `RVpct >= 0.80` → volle Positionsgrösse; `0.50–0.80` → halbe; `< 0.50` → flat.
- Auswertung zwingend über `filterMask[entryIdx-1]`, nicht `[entryIdx]`.

**Evidenzlage:**
1. **Nagel, „Evaporating Liquidity", Review of Financial Studies 25(7), 2012.** Short-Term-Reversal-Renditen sind ein Proxy für die Rendite aus Liquiditätsbereitstellung; erwartete Rendite stark zeitvariabel und **durch den VIX prognostizierbar**. Sogar Reversal-Strategien auf Branchenportfolios, die *unkonditional nichts* verdienen, liefern bei hohem VIX hohe Sharpe Ratios. Mechanismus: Rückzug des Liquiditätsangebots durch kapitalrestringierte Intermediäre.
2. **Pagonidis (2013), Tab. 6–8** — unabhängige Bestätigung auf **anderen Instrumenten** (ETFs statt Einzelaktien-Querschnitt) und **anderem Indikator** (IBS statt Wochen-Reversal): vola-adjustierter Spread 0,276 (hohe Vola) vs. 0,178 (niedrige Vola); zusätzlich stärker nach Tagen mit grosser Range.
3. Konsistenzlinie: 252-Tage-Autokorrelation der SPX-Tagesrenditen fiel nach März 2020 unter −0,40 und blieb ~1 Jahr unter −0,35.

**Warum kein Decay zu erwarten ist:** Der Effekt ist eine **Risikoprämie für Liquiditätsbereitstellung unter Kapitalrestriktionen**, kein Preisfindungsfehler. Solche Prämien verschwinden nicht durch Publikation, weil genau dann Kapital knapp ist, wenn sie hoch sind. Realistische Erwartung: bleibt bestehen, ist aber **selten und geballt** — hohe Erträge in wenigen Stressfenstern, instabile Backtest-Sharpe, unangenehmer Drawdown-Pfad.

**Pflicht-Vorprüfung:** Perzentilisiert euer bestehender Regime-Score bereits RV20? Falls ja, ist der *Indikator* eine Dublette und nur die *Verwendung* (multiplikativer Gate auf Meanrev-Signale statt Score-Komponente) ist neu.

**Richtungs-Caveat:** Für **Saisoneffekte** gilt Nagels Richtung nicht automatisch — Agnani & Aray (2011) finden den Januar-Effekt im Hochvola-Regime **grösser**. Pro Effekt empirisch bestimmen.

---

### #5 — Garman-Klass Realized Vol (20d) als Perzentil-Regime-Gate
**Familie:** vola · **Unabhängige Tests überstanden: 3 (Messschicht) · 0 (Gate-Anwendung auf Saisonalität)**

Kein neuer Indikator, sondern ein **Upgrade eurer bestehenden Perzentil-Regime-Grösse**: ~7,4× effizienter als Close-to-Close.

**Formel**

```
# Pro Tag i, ALLE vier OHLC mit demselben Adjustierungsfaktor:
gk_i = 0.5*(ln(H_i/L_i))^2 - (2*ln(2)-1)*(ln(C_i/O_i))^2
gk_i = max(gk_i, 0)                      # Clip; Tage mit H==L verwerfen
var20[t]     = mean(gk_i, i = t-19..t)
sigma_GK[t]  = sqrt(252 * var20[t])
pct[t]       = Perzentilrang von sigma_GK[t] in sigma_GK[t-1259..t]   # 5 Jahre
               # LINEARE Interpolation. Mindesthistorie 756 HT, sonst NaN

# Robustheitsvariante (driftrobust, sonst identische Pipeline):
rs_i = ln(H_i/C_i)*ln(H_i/O_i) + ln(L_i/C_i)*ln(L_i/O_i)
```

**Kritischer Vorteil:** GK und RS nutzen **nur Intraday-Terme** (H/L/C/O desselben Tages) → proportionale Adjustierung kürzt sich raus, **kein Cross-Day-adj_factor-Mixing**. Yang-Zhang und ATR haben genau dieses Problem und sind deshalb ausgeschieden.

**Signalregel:** Saison-Strategie (ToM/Sell-in-May/Feiertag/Januar) nur ausführen, wenn `pct[entryIdx-1] <= 0.80` — oberstes Vola-Quintil überspringen, sonst flat (kein Short).

**Disziplin-Vorgabe:** Schwelle **vor** dem Test auf 0,80 festlegen und **das ganze Grid** {0,50 · 0,60 · 0,70 · 0,80 · 0,90} berichten. Wenn nur ein Punkt funktioniert → Rauschen. Realistische Erwartung: Trefferquote und Drawdown verbessern sich, **CAGR sinkt** (~20 % der Fenster ausgelassen). **Ein Sharpe-Anstieg > 0,15 ohne gleichzeitige Drawdown-Verbesserung ist ein Overfitting-Warnsignal.**

**Evidenzlage:**
- *Messschicht (stark, 3 unabhängige):* Bali & Weinbaum (2005) GK am besten · Molnár (Int. Review of Financial Analysis 2012, Multi-Markt) GK bester Range-Schätzer, mit GK normierte Renditen näherungsweise normalverteilt · Empirical Economics 2025 (G7-Indizes gegen Intraday-RV) GK durchgängig am robustesten, **RS und YZ liefern trotz höherer Komplexität keine signifikante Verbesserung**.
- *Prognoseschicht (stark):* HAR-RV (Corsi 2009) ist der am häufigsten replizierte Benchmark der Vola-Prognoseliteratur. Das ist der Grund, warum ein Vola-Gate überhaupt kausal sein *kann*: der Input ist prognostizierbar, im Gegensatz zu Renditen.
- *Filterschicht (mittel):* Harvey et al. (JPM 2018), 60 Assets 1926–2017.
- *Kombination Vola-Gate × Saisonalität:* **keine peer-reviewte Evidenz.** Der einzige gefundene explizite Test (AlgoCloud, ToM+Vola-Regime auf SPY) publiziert weder Formel noch Schwellwert noch Kennzahlen — als Evidenz wertlos.

**Decay-Warnung:** Angelidis & Tessaromatis (Journal of Financial Markets 2023, 11 Faktor- + 110 Anomalie-Portfolios): Profitabilität von Vola-Timing in US-Aktien **seit Anfang der 2000er verschwunden**. Erwartet Risikoreduktion, nicht Alpha.

---

### #6 — Turn-of-Month [-3, +3] mit settlement-adaptivem Pivot
**Familie:** seasonal · **Unabhängige Tests überstanden: 4 bestätigend, 2 dokumentieren Zerfall**

Ihr habt ToM bereits. Der Mehrwert liegt in **drei konkreten Korrekturen**.

**Formel**

```
# ALLES in Handelstagen des jeweiligen Boersenkalenders
tdom(i)     = 1..N_m                       # 1 = erster HT des Monats
pos_end(i)  = tdom(i) - N_m                # 0 = letzter HT, -1 = vorletzter

# KORREKTUR 1: settlement-adaptiver Pivot (Etula leitet T-3 aus T+3-Settlement ab)
settle_lag = 3   bis 2017-09-04
           = 2   bis 2024-05-27
           = 1   ab  2024-05-28

ToM_WINDOW   = (pos_end >= -settle_lag) ODER (tdom <= 3)
PRE_ToM_HOLE = (pos_end zwischen -(settle_lag+5) und -(settle_lag+1))

# Monitoring, rollierend 60 Monate, nur Daten bis Vormonat
ToM_SPREAD = mean(r | ToM_WINDOW) - mean(r | !ToM_WINDOW)
```

**Signalregel:**
- Long ab Close des Tages mit `pos_end = -(settle_lag+1)` bis Close bei `tdom = 3`, sonst flat.
- **KORREKTUR 2 (der meistignorierte Teil des Etula-Papers):** Keine **neuen** Long-Einstiege aus *anderen* Strategien während `PRE_ToM_HOLE` — dort sind die Durchschnittsrenditen historisch negativ.
- **KORREKTUR 3:** Das klassische `[0,+3]`-Fenster **nicht mehr als eigenständiges Signal verwenden** — es ist in US-Aktien nicht mehr signifikant.
- Konservativ: nur handeln, wenn `ToM_SPREAD > 0` (look-ahead-frei).

**Evidenzlage:**
1. Lakonishok & Smidt (1988), DJIA 1897–1986, 90 Jahre.
2. Kunkel/Compton/Beyer (2003): 15 von 19 Ländern 1988–2000; ToM-Periode ⌀ 87 % der Monatsrendite.
3. McConnell & Xu (FAJ 2008): US 1926–2005 plus **31 von 35 internationalen Märkten**.
4. **Etula/Rinne/Suominen/Vaittinen (RFS 33(1), 2020)** — liefert den **Mechanismus** statt eines Kalender-Dummys: monatlicher Zahlungszyklus (Pensionen, Dividenden, Fondsausschüttungen) + T+3-Settlement erzwingen liquiditätsgetriebene Verkäufe, die spätestens 3 HT vor Monatsende enden → Preisdruck davor, Reversal danach. Belegt über Institutional-Trade-Daten, Fund-Holdings, Cross-Section.
5. *Gegen:* Plastun et al. (NAJEF 2019, DJIA 1900–2018) — ToM seit den 1980ern verschwunden.
6. *Gegen:* QuantSeeker (2024/25, publizierter Code, SPY/QQQ/IWM + 11 Sektor- + 9 Länder-ETFs + Bonds/HY/FX/Commodities/Bitcoin) — `[0,+3]` in US-Aktien **nicht mehr signifikant**; `[-3,+3]` bei den meisten Equity-ETFs signifikant mit +5 bis +12 bp/Tag, aber **durchgehender Abwärtstrend über die letzte Dekade**. Long-only auf US-Märkten **senkte** CAGR und Sharpe gegenüber Buy&Hold (verbesserte Skew und Drawdown). Ökonomisch signifikante Outperformance nur Brasilien, Schweden, Hongkong.

**Der eigentliche Test:** Ein Backtest mit fixem T-3 über 1993–2026 mischt **drei verschiedene Marktregime** — genau die Art stiller Fehlspezifikation, die euch zweimal in die Falle geführt hat. Prüft explizit, **ob sich der Effekt nach den Umstellungsdaten 2017-09-05 und 2024-05-28 tatsächlich verschoben hat.** Falls nein, ist der Mechanismus widerlegt und ihr habt nur einen Kalender-Dummy.

---

### #7 — Vola-normalisiertes EMA-Trendsignal (CFM, 105 Tage)
**Familie:** trend · **Unabhängige Tests überstanden: 3 auf Portfolio-Ebene, 1 starke Widerlegung auf Einzel-Asset-Ebene**

**Formel**

```
n = 105                                    # ~5 Monate
lambda = 1 - 1/n

EMA_P[t] = EMA_P[t-1] + (1-lambda)*(C[t] - EMA_P[t-1])   # Init: mean der ersten n Closes
D[t]     = |C[t] - C[t-1]|
EMA_D[t] = EMA_D[t-1] + (1-lambda)*(D[t] - EMA_D[t-1])   # Init: mean der ersten n D
sigma_n[t] = EMA_D[t] * sqrt(n)
s[t]       = (C[t] - EMA_P[t]) / sigma_n[t]              # dimensionslos, ca. -2..+2
```

**Signalregel:**
- Als Saison-Filter: Trade nur wenn `s[entryIdx-1] > 0`.
- Mit Hysterese gegen Whipsaws: Einstieg bei `s > +0.25`, Ausstieg bei `s < -0.25`.
- Optional Grössensteuerung: `w[t] = clip(s[t-1]/2, 0, 1)`.

**Der eigentliche Zugewinn** ist **nicht die Richtung** — das Vorzeichen von `s` ist identisch mit „Close über/unter 105-Tage-EMA". Der Wert liegt in der **Vergleichbarkeit über alle 324 Ticker** (SPY vs. USO vs. IBIT), weil durch die eigene Vola geteilt wird. Damit sind Cross-Ticker-Rankings und **einheitliche Schwellwerte** möglich — das können RSI/MACD/Bollinger nicht.

**Evidenzlage:**
1. Moskowitz/Ooi/Pedersen (JFE 2012), 58 Instrumente 1965–2009.
2. **Lempérière/Deremble/Seager/Potters/Bouchaud (CFM, arXiv:1404.3274, 2014)** — 27 Kontrakte, 4 Assetklassen. Futures 1960–2013: t = 5,9 (entzerrt 5,0), Sharpe 0,78. **Spot-Daten zurück bis 1800**: t = 10,5 (entzerrt 9,8), Sharpe 0,72. Positiv in **jeder Dekade**; rollierende 10-Jahres-Performance in zwei Jahrhunderten nie negativ. *Andere Autorengruppe (kein AQR-Interessenkonflikt), andere Daten (Spot ab 1800), andere Signaldefinition (EMA/Vola statt 12M-Vorzeichen) — echte unabhängige Replikation.*
3. Hurst/Ooi/Pedersen (JPM 2017), dritter Datensatz ab 1880, positiv in jeder Dekade.
4. *Gegen:* **Huang/Li/Wang/Zhou (JFE 2020, „Time series momentum: Is it there?")** — Asset-für-Asset-Zeitreihenregressionen zeigen „little evidence of TSM, both in- and out-of-sample"; der grosse t-Wert der gepoolten Regression liegt **unter** den kritischen Bootstrap-Werten. **Genau euer Anwendungsfall (Einzel-Ticker Long/Flat) ist der, den diese Arbeit zerlegt.**

**Direkt handlungsleitende Erkenntnis:** Die Autoren zeigen, dass **kurze Trends (Zeitskala ~3 Tage) seit 1990 signifikant zerfallen und seit 2003 vollständig verschwunden sind**, während die 5-Monats-Skala über zwei Jahrhunderte „bemerkenswert stabil" ist. → **Baut keine Trendfilter mit Lookback < ~4 Wochen.**

**Ehrlicher Vorbehalt:** Post-2011 ist die Strategie „virtually flat"; SG Trend Index mit dem zweitgrössten Drawdown seit 2000 (−20,4 %, Mai 2024 – Mai 2025). Als Alpha-Quelle verblasst, **als Drawdown-Filter weiter brauchbar.**

---

### #8 — Inverse-Vola-Sizing (Vol-Targeting) — als **Risiko**-Layer, nicht als Alpha
**Familie:** sizing · **Unabhängige Tests: Risiko-Claim überlebt 2 · Alpha-Claim scheitert an 3**

**Formel**

```
sigma_hat[t] = sqrt(252 * mean(gk_i, i = t-19..t))     # GK aus #5, Stand t-1
sigma_target = 0.15                                     # ODER expanding Median bis t-1
w[t]         = min(w_max, sigma_target / sigma_hat[t-1])
w_max        = 1.0                                      # KEIN Hebel

Position = Saison-/Trendsignal(0/1) * w[t]
# Rebalancing NUR zum Einstieg des Saison-Fensters, nicht taeglich (Turnover!)
```

**Zwingende Vorgabe für die Auswertung:** Vol-Targeting verändert die Vola des Ergebnisses. **Vergleicht Sharpe, maxDD und Ulcer — nicht CAGR**, sonst täuscht ihr euch selbst.

**Evidenzlage — das ist ein Kandidat, bei dem ihr die Erwartung aktiv nach unten korrigieren müsst:**
- *Pro (Risiko):* Harvey et al. (JPM 2018), 60 Assets, Tagesdaten 1926–2017 inkl. Handelskosten: Sharpe-Verbesserung **nur für Risikoassets (Aktien, Credit)** über den Leverage-Effekt; für Bonds/FX/Commodities vernachlässigbar. In **allen** Assetklassen reduzierte Wahrscheinlichkeit extremer Renditen. Kim/Tse/Wald (2016) bestätigen den Mechanismus für TSMOM (Alpha fällt ohne Vol-Scaling von 1,27 % auf 0,41 %/Monat).
- *Contra (Alpha):* **Cederburg/O'Doherty/Wang/Yan (JFE 138(1), 2020)** — 103 Aktienstrategien: vola-gemanagte Portfolios schlagen ihre ungemanagten Pendants **nicht** systematisch; die positiven Alphas stammen aus Spanning-Regressionen, die in Echtzeit nicht implementierbar sind; realistische OOS-Versionen liefern **niedrigere** Certainty-Equivalent-Renditen und Sharpe Ratios als die simplen Ausgangsportfolios. Kang et al. (J. Futures Markets 2021): auf Commodities in-sample signifikant, out-of-sample keine Verbesserung. Angelidis & Tessaromatis (2023): in US-Aktien seit den frühen 2000ern verschwunden.

**Fazit:** Als **Risikosteuerung belegt, als Alpha-Quelle out-of-sample widerlegt.** Baut es als Drawdown-Feature, nicht als Performance-Feature.

**Warnung Long-only:** In dauerhaften Niedrigvola-Bullenmärkten führt ein zu niedriges Ziel ohne Hebel zu chronischer Untergewichtung. SPY-Realvola liegt langfristig bei 15–18 % → `sigma_target = 0.15`, nicht 0,10.

---

### #9 — 52-Wochen-Hoch-Nähe / Drawdown-Regime
**Familie:** breadth/regime · **Unabhängige Tests überstanden: 3 · 1 sauberer OOS-Fehlschlag exakt auf Sektor-ETFs**

**Formel**

```
# Einzelticker-Naehe
HH252[i,t] = max(High[i, t-251..t])            # ODER max(Close) - VORHER festlegen, nie wechseln
PROX[i,t]  = Close[i,t] / HH252[i,t]           # (0, 1]

# Drawdown-Zustand (aequivalent, Close-basiert, kein Adjustierungsproblem)
DD[t] = Close[t] / max(Close[t-251..t]) - 1
   R1 'nahe Hoch'  DD > -0.05
   R2 'Korrektur'  -0.15 < DD <= -0.05
   R3 'Baer'       DD <= -0.15

# Aggregierte Marktbreiten-Variante (genuin neu, geringe Ueberlappung)
BREADTH52[t] = Anteil der Ticker mit PROX[i,t] >= 0.95
```

**Signalregel:**
- Ticker-Filter: Saison-Long in Ticker *i* nur, wenn `PROX[i, entryIdx-1] >= 0.90`; überspringen bei `< 0.80`.
- Markt-Veto: keine Saison-Longs bei `BREADTH52 < 0.20`.
- Drawdown-Gate: Saison-Trade nur in R1/R2, in R3 flat. **Beide Schwellen (−5 % und −15 %) plus No-Gate-Baseline testen und alle drei berichten** — der Unterschied muss ökonomisch, nicht per Optimierung entschieden werden.

**Evidenzlage:**
1. George & Hwang (JF 2004) — Nähe zum 52-Wochen-Hoch dominiert klassische Jegadeesh-Titman-Rangfolgen.
2. Marshall & Cahan (2005) — **erster echter OOS-Test durch andere Autoren, australische Aktien**, bestätigt.
3. Liu/Liu/Ma (JIMF 2011) — **20 Märkte: in 18 profitabel, in 10 signifikant** (9 von 13 europäischen + Hongkong); überlebt Fama-French-Kontrolle, kehrt langfristig nicht um.
4. Du (QREF 2008) — **auf Indizes** (18 entwickelte Länder, 1969–2004), also auf Korb-Ebene wie eure ETFs; Preisniveau relativ zum 52-Wochen-Hoch dominiert vergangene Renditen.
5. *Gegen, und für euch entscheidend:* **Du/Craft Denning/Zhao (J. Asset Management 2014)**, explizit als „clean out-of-sample test" konzipiert: **„There is no momentum in sector ETFs, and momentum does not depend on market states in the recent decade."**

**Konsequenz:** Auf **Einzelaktien (eure Dow-30/DAX-40-Ticker)** ist das ein Rating-4-Kandidat. Auf **US-Sektor-ETFs post-2000 ist er widerlegt.** Baut ihn nur für das Einzelaktien-Universum.

**Zirkularitätsprüfung (Pflicht):** `DD` und `PROX` korrelieren stark mit Carhart-12M (Rangkorrelation typisch 0,6–0,8). Testet das Gate **immer zusätzlich in einer Variante, in der Momentum bereits als Filter aktiv ist**, sonst kauft ihr Momentum zum zweiten Mal. Empfehlung: nicht als *zusätzlicher* Filter, sondern als **alternative Spezifikation** des bestehenden Momentum-Filters im Head-to-Head-Walk-Forward. Nur `BREADTH52` ist genuin neu.

---

### #10 — Donchian-Channel-Breakout — **nur für rohstoffähnliche Ticker**
**Familie:** trend · **Unabhängige Tests überstanden: 1 in Commodities · in Aktien widerlegt**

**Formel**

```
upper[t]      = max(High[t-N..t-1])       # N = 20 (schnell) bzw. 55 (langsam)
lower_exit[t] = min(Low[t-M..t-1])        # M = N/2, also 10 bzw. 20
# Fenster enden bei t-1 -> look-ahead-frei

# ATR-Stop (Turtle)
TR[t]  = max(H[t]-L[t], |H[t]-C[t-1]|, |L[t]-C[t-1]|)   # ACHTUNG: Cross-Day-Term,
ATR14  = mean(TR[t-13..t])                              # nur mit ROHEN OHLC sauber
Stop   = Entry - 2*ATR14
```

**Signalregel:**
- Standalone: Long bei `Close[t] > upper[t]`, Exit bei `Close[t] < lower_exit[t]` oder ATR-Stop.
- **Als Saison-Filter (unser Use-Case):** Trade nur nehmen, wenn `Close[entryIdx-1] > max(High[entryIdx-21..entryIdx-2]) * 0.98` (nahe/über dem 20-Tage-Hoch).

**Warum trotz Rating 3 in der Top-12:** Wie IBS nutzt Donchian **High/Low** — die einzige OHLCV-Information, die alle eure bestehenden Indikatoren ignorieren. Konzeptionell gegensätzlich zu Bollinger (dort mean-reversion-artig gelesen, hier reines Extremwert-Breakout).

**Evidenzlage:**
1. **Szakmary/Shen/Sharma (JBF 2010)** — 28 Rohstoff-Futures, 48 Jahre. **Alle** Parametrisierungen von Dual-MA und Channel liefern positive Excess-Returns **nach Transaktionskosten** in mindestens 22 der 28 Märkte. Robust gegen Data-Mining-Adjustierung, Verteilungsannahmen und Kosten — methodisch sauberer als der Grossteil der MA-Literatur. Kein „magisches" k: alle getesteten Fenster 6–48 Monate profitabel.
2. Financial Markets and Portfolio Management (2021), „Have trend-following signals in commodity futures markets become less reliable?" — Trendregressionen auf zeitvariable Success-Ratios: **mit Ausnahme weniger Rohstoffe kein signifikantes Nachlassen** bis 2021.
3. *Gegen:* Dieselbe FMPM-Arbeit stellt fest, dass in **Aktien**märkten die Prognosekraft von Trendregeln sehr wohl abnimmt. Sullivan/Timmermann/White (1999) und Bajgrowicz/Scaillet (JFE 2012) haben die klassische Breakout-Literatur (Brock/Lakonishok/LeBaron 1992) als Data-Snooping bzw. transaktionskostenbedingt wertlos entlarvt.

**Anwendungs-Einschränkung (hart):** Die Szakmary-Evidenz gilt **nicht** für Aktien-/Sektor-ETFs. Übertragbar auf: **GLD, SLV, USO, URA, GDX, XME**, mit Abstrichen **TLT**. Für SPY/QQQ/XLK etc. nicht bauen.

---

### #11 — Absorptions-Ratio-Shift ΔAR (PCA-Kohäsion der Sektor-ETFs) — **Prototyp-Status**
**Familie:** breadth · **Unabhängige Tests überstanden: 1 für den Mechanismus · 0 für die Handelsregel**

Aufgenommen trotz schwacher Evidenz, weil es der **einzige Kandidat der Liste ist, der die Kovarianzstruktur statt eines Preispfads misst** — also die einzige echte strukturelle Ergänzung zu RSI/Bollinger/LBR/MACD/Momentum/StRev.

**Formel**

```
# Universum: die 9 Select-Sector-SPDRs mit Historie ab 1998
# XLB XLE XLF XLI XLK XLP XLU XLV XLY
# XLRE (2015) und XLC (2018) BEWUSST WEGLASSEN -> sonst springt N mitten im Backtest
#   und AR macht einen kuenstlichen Sprung

r_i[t]   = ln(C_i[t]/C_i[t-1])
Sigma[t] = Kovarianzmatrix der 9 Reihen ueber rollierende 500 HT
lambda_1 >= ... >= lambda_9 = eigvalsh(Sigma[t])
n        = round(0.2 * 9) = 2
AR[t]    = (lambda_1 + lambda_2) / sum(lambda_1..lambda_9)          # in (0,1)

# NUR die standardisierte VERSCHIEBUNG verwenden, NIEMALS das Level:
dAR[t]   = ( MA15(AR)[t] - MA500(AR)[t] ) / sd500(AR)[t]
```

**Signalregel (Zustandsautomat, 1 Tag Lag):**
- `dAR[t-1] >= +1.0` → **FLAT** (Fragilitäts-Veto)
- `dAR[t-1] <= -1.0` → **LONG**, Saison-Trade ggf. in erhöhter Grösse
- dazwischen → vorherigen Zustand beibehalten (das erzeugt die ~1,7 Trades/Jahr des Originals)
- Als Saison-Filter: Saison-Long nur eröffnen, wenn `dAR[entryIdx-1] < +1.0`. Der Indikator ist ein **Veto**, kein Entry-Trigger — hohe AR ist laut Autoren „near necessary, not sufficient" für einen Drawdown.

**Evidenzlage — ehrlich:**
1. Kritzman/Li/Page/Rigobon (JPM 2011), 51 US-Industrien, 1998–01/2010: alle 1-%-schlechtesten Monats-Drawdowns wurden von einem +1σ-ΔAR-Spike vorangegangen; Handelsregel +4,5 % p.a. bei +0,61 % mehr Risiko, Return/Risk 0,47 → 0,83.
2. **Berger & Pukthuanthong (JFE 105(3), 2012)** — eigener Fragility Index aus PCA-Ladungen über **82 Länderindizes**, unabhängige Autoren, unabhängiges Universum, unabhängige Periode (~1974–2009): hohe gemeinsame Faktorexposition erhöht die Crash-Wahrscheinlichkeit massiv. *Das repliziert den **Mechanismus**, nicht die Handelsregel.*
3. **Gegen:** Kritzman selbst hat öffentlich eingeräumt, dass AR als Reaktion auf die Finanzkrise entwickelt und **durch** die Finanzkrise zurückgetestet wurde, dass es seither nur einen Drawdown > 10 % gab und **März 2020 der erste echte Live-Test war.** Das Original hat 1,72 Trades/Jahr über 12 Jahre ≈ **20 unabhängige Entscheidungen**; Fenster (500), n (N/5), Schwelle (±1σ) und die 15/252-Fenster sind gesetzt, nicht getestet.
4. **Gegen:** portfoliooptimizer.io fand in eigener Implementierung ein **fallendes** AR vor Crashes — **Vorzeichenumkehr**, zurückgeführt auf abweichende Fensterlänge/Frequenz. Der Befund ist implementierungssensitiv.

**Verbindliche Vorbedingungen vor jedem Live-Einsatz:**
- Sensitivitätsmatrix über Fenster (250/500/750) × n (N/5 vs. fix 1..3) × Schwelle (0,75/1,0/1,5σ). **Bleibt das Vorzeichen stabil?** Wenn nein: verwerfen.
- Billigster Realtest zuerst: **Liefert ΔAR im Februar 2020 und im Bärenmarkt 2022 rechtzeitig ein Flat-Signal?** Wenn nein: sofort verwerfen, bevor irgendetwas gebaut wird.
- **Niemals das AR-Level als Schwelle.** Der Zufluss in passive Produkte hebt das Korrelationsniveau permanent an → das Level driftet nach oben, ohne dass Systemrisiko steigt. Nur `dAR`.
- Korrelation von `dAR` zum bestehenden Regime-Score messen; `|ρ| > 0.6` = redundant.

---

### #12 — Marktbreite (Netto-Advance-Quote) — aus den **324 Einzeltickern**, nicht aus 28 ETFs
**Familie:** breadth · **Unabhängige Tests überstanden: 0 (nur Cross-Country-Breite innerhalb einer Studie) · 1 Studie dokumentiert Zerfall**

Aufgenommen mit **explizit niedriger Erwartung**, weil ihr — anders als die meisten — das Papier-Konstrukt tatsächlich bauen könnt.

**Formel**

```
# Universum: die 324 Einzelticker (Dow-30, DAX-40, Rest), NICHT die 28 Sektor-ETFs.
# Grund: das Paper misst Breite ueber hunderte Konstituenten. 28 hochkorrelierte
# Sektorkoerbe sind eine viel groebere Messung als 500 Einzelwerte.

r_i[d] = ln(C_i[d]/C_i[d-1])
A[d]   = ( #{i: r_i[d] > 0} - #{i: r_i[d] < 0} ) / N_d
         # N_d = Zahl der an Tag d HANDELBAREN Ticker
         # Ticker ohne Kurs an d ausschliessen, NICHT als 0 zaehlen (Feiertagsfalle!)

BREADTH[t] = mean(A[d], d = t-20..t)                        # 21 HT
P[t]       = Perzentilrang von BREADTH[t] in den letzten 1260 HT
```

**Signalregel:** Monatsende auswerten, ersten HT des Folgemonats ausführen (`filterMask[entryIdx-1]`).
- LONG wenn `BREADTH[t] > 0` UND `P[t] >= 0.50`, sonst FLAT.
- Als Saison-Filter: Saison-Long nur eröffnen, wenn `BREADTH` am Vortag `> 0`.
- **Richtung beachten:** Das Paper findet **Fortsetzung**, nicht Reversal — hohe Breite prognostiziert **hohe** Folgerenditen (Herding-Story). Wer hier antizyklisch handelt, dreht das Signal falsch herum.

**Evidenzlage:**
- Zaremba/Szyszka/Karathanasopoulos/Mikutowski (Economic Modelling 97, 2021): 64 Länder, 1973–2018; überlebt Kontrollen für Size, Style, Volatilität, Schiefe, Momentum und Trendfolge-Signale; enthält laut Tabellenverzeichnis explizit „Time-series predictability of market returns by breadth" (Tab. 3) und „performance of timing strategy" (Tab. 4) — also genau euren Anwendungsfall.
- *Gegen:* Qi & Zhao (J. Investing 2008) — Market Breadth und TRIN hatten starke Kurzfrist-Prognosekraft, die **„drastisch abgeschwächt oder verschwunden"** ist; verbliebene Gewinne kamen aus häufigem Handel in Small Caps.
- *Kein* unabhängiger Replikationsversuch, *kein* Post-2018-Update.

**Zwei harte Vorprüfungen:**
1. **Redundanzrisiko StRev:** `BREADTH` über 21 Tage korreliert mechanisch mit dem 21-Tage-Return des Marktes → mit MACD, und mit **umgekehrtem Vorzeichen** mit eurem Jegadeesh-StRev-21d. StRev sagt „nach 21 starken Tagen untergewichten", Breadth sagt „nach 21 breiten Tagen übergewichten". **Beide gemeinsam erzeugt gegenläufige Signale statt Diversifikation.** Bei `|ρ| > 0.7` zu StRev nur einen von beiden behalten.
2. **Original-Lookback ist unverifiziert.** Der 21-Tage-Parameter ist eine Umsetzung der Paper-Definition, kein bestätigter Paper-Parameter. Testet 21/63/126 **gemeinsam** und bewertet die **Stabilität über alle drei**, nicht das Maximum.
3. Zaremba findet den Effekt am stärksten dort, wo **Arbitragegrenzen hoch** sind (kleine, illiquide Märkte). Der US-Large-Cap-Raum ist das Gegenteil → erwarteter Effekt bei euch systematisch gedämpft.

---

## (b) NEGATIVKONTROLLEN

Diese sind für euch **wertvoller als die meisten Top-12-Kandidaten**, weil sie eure Walk-Forward-Pipeline kalibrieren. Baut sie als Testfälle ein. **Wenn eure Pipeline eine davon als „gut" durchwinkt, ist die Pipeline kaputt — nicht der Markt.**

### Klasse A — Goldstandard-Negativkontrollen (spektakulär in-sample, sauber widerlegt)

| # | Kandidat | Widerlegt durch | Warum es der beste Testfall ist |
|---|---|---|---|
| **N1** | **FOMC-Even-Week-Zyklus** (Cieslak/Morse/Vissing-Jorgensen, **JF 2019**) | Uppal (Imperial College, 2025) | **Der wertvollste Testfall der ganzen Liste.** Top-3-Journal, kausale Story, internationale Bestätigung, Economist- und WSJ-Echo. Und: **der Effekt war ab 2004 tot, das Paper erschien 2019** — die Publikation lag 15 Jahre *nach* dem Ende des Effekts. Aufgedeckt durch stumpfe Sample-Verlängerung um 7 Jahre plus Ausreisser-Check. Zusätzlich: kein Effekt in Treasuries/Fed-Funds-/Eurodollar-Futures — genau den Märkten, die bei echten Leaks reagieren müssten; der postulierte Mechanismus (zweiwöchentliche Board-Meetings) existiert seit 2004 gar nicht mehr. In-sample-Illustration: 100 USD → 768 (Buy&Hold) vs. 1.522 (Even-Week) über 1994–2016. |
| **N2** | **Bremer/Sweeney Reversal nach grossem Ein-Tages-Einbruch** (JF 1991) | **Cox & Peterson (JF 1994)** — publizierte gescheiterte Replikation im *selben Journal* | Findet **keine** Evidenz für Overreaction; Aktien mit grossen Ein-Tages-Verlusten schneiden danach sogar schlecht ab. Die scheinbaren Reversals sind **Bid-Ask-Bounce**. Schon Atkins & Dyl (1990) zeigten, dass der Effekt Transaktionskosten nicht überlebt. Bei SPY/QQQ mit 1-bp-Spreads ist die Quelle physisch verschwunden → **Erwartungswert exakt null.** Perfekter Testfall: wenn eure Engine hier etwas findet, findet sie Rauschen. |
| **N3** | **Wochentags-/Montagseffekt** (French 1980, Gibbons/Hess 1981) | Sullivan/Timmermann/White (2001) · Schwert (2003) · **Olson/Mossman/Chou (QREF 2015)** | Der aussagekräftigste **Verlaufstyp**: Identifikation → Ausbeutung → Rückgang → **Vorzeichenumkehr** → Verschwinden. Wer eine solche Regel in *irgendeinem* Teilsample sucht, findet **garantiert** eine Phase, in der sie „funktioniert". |
| **N4** | **avgcor (Pollet & Wilson, JFE 2010)** | **Goyal/Welch/Zafirov (RFS 37(11), 2024, Abschn. 3.1.17)** | Musterfall eurer Falle: gutes JFE-Paper, sauberes theoretisches Argument (Roll-Kritik), OOS-R² > 3 % im Originalsample. Ergebnis der Nachprüfung bis 2021: IS-t fällt von 2,58 auf 2,31, in homologer Spezifikation **t = 0,82 (nicht signifikant)**, OOS-R² negativ vorwärts **und** rückwärts, Handelsperformance „poor". Wörtlich: *„if avgcor is extended backwards, too, then it is easy to dismiss all around."* **Der Effekt starb praktisch zeitgleich mit der Publikation.** |
| **N5** | **RSP/SPY als Breadth-Signal** | CXO Advisory (796 Wochen, 2003–2018) · TrendLabs | Pearson-Korrelation **0,03**, **R² = 0,001**. Populärster Indikator der Liste, **null Evidenz**. Extra-Wert: Die Ratio hat seit 2015 einen starken strukturellen Abwärtstrend (Mega-Cap-Konzentration). Eine SMA200-Regel darauf wäre 2022–2026 fast durchgehend flat gewesen und hätte im Backtest **wie ein erfolgreicher Risikofilter ausgesehen** — obwohl sie nur einen Drift abbildet. **Genau diese Art Scheinbefund muss eure Pipeline fangen.** |

### Klasse B — Stark abgeschwächt / nur noch defensiv nutzbar

| # | Kandidat | Status | Was noch bleibt |
|---|---|---|---|
| **N6** | **SMA200 / 10-Monats-MA** | Zakamulin (155 Jahre): **keine** signifikante Outperformance in der zweiten Sample-Hälfte; die „too good to be true"-Ergebnisse entstehen durch Look-ahead bei der Regelauswahl. Bajgrowicz/Scaillet (JFE 2012, DJIA 1897–2011, FDR-Korrektur): Performance schon *in-sample* durch geringe Kosten aufgezehrt. Fabers eigenes Post-Publication-Ergebnis: in **6 von 8 Jahren** schlechter als Aktien. | Nur als grobes Risiko-Gate. Kein Neuwert neben Carhart/Regime-Score. |
| **N7** | **Pre-Holiday-Effekt** | Vergin & McGinnis (1999): für grosse Unternehmen **verschwunden**. Plastun et al. (2019): seit den 1980ern weg. International teils **Vorzeichenumkehr**. | **Nur defensiv:** Implementiert es, um zu *verhindern*, dass andere Signale unbemerkt einen Vorfeiertags-Bias einbauen. Der Kalender liegt bei euch ohnehin vollständig vor → kostenlos. |
| **N8** | **Januar-/Turn-of-Year-Effekt** | Gu (2003): ausgeprägter Abwärtstrend seit 1988, für Russell-Indizes **verschwunden**. Plastun et al. (2019): seit den 1980ern weg. Asness et al. (JFE 2018): saubere Size-Prämie ist **nicht mehr** auf Januar konzentriert → entzieht dem Timing die Basis. | Der Ur-Effekt sitzt in Microcaps (3 % der Marktkap., 60 % der Titelzahl) — **per Konstruktion nicht in eurem Universum**. |
| **N9** | **Halloween / Sell in May** | Maberly & Pierce (2003/04): US-Effekt getragen von **zwei Ausreissern** (Oktober 1987, LTCM August 1998) — nach Kontrolle insignifikant. Dichtl & Drobetz (FRL 2014, IRFA 2015): stark abgeschwächt/verschwunden. Sullivan/Timmermann/White (2001): verschwindet im 9.452-Regel-Universum. **„36 von 37 Märkten" sind keine 37 unabhängigen Tests** — und pro Markt gibt es nur ~1 unabhängige Beobachtung pro Jahr. | Ihr habt es. **Nachrüsten: winsorisierter Gegentest (1./99. Perzentil).** Wenn `HAL_SPREAD` dadurch kollabiert, ist euer Effekt ausreissergetrieben. Umwandeln von binärem Timing in Exposure-Tilt (100 % Nov–Apr / 60 % Mai–Okt). Einziger Effekt, der die Data-Mining-Korrektur übersteht, ist der **internationale**, nicht der US-Effekt. |
| **N10** | **ATR(14)/Close-Perzentil als Regime-Gate** | **Null** peer-reviewte Evidenz. Regelklasse in Sullivan/Timmermann/White (1999, 7.846 Regeln) out-of-sample gescheitert. Korreliert > 0,9 mit GK-RV. Zusätzlich Cross-Day-Adjustierungs-Bug. | ATR **nur** als Stop-/Sizing-Einheit (`Stop = Entry − 2.5·ATR14`) — dort ist es Normierung ohne Prognoseanspruch. **Nie als Gate.** |
| **N11** | **XLU/SPY Beta-Rotation (Gayed/Bilello, Dow Award 2014)** | CXO-Replikation: Profitabilität verschwindet **oberhalb 0,1–0,2 % Kosten**, ab 0,37 % Underperformance; **nur 3–4 Wochen Lookback** konkurrenzfähig, Abweichungen brechen scharf ein; 4-Wochen-Fenster aus Vorarbeiten übernommen = Data-Snooping-verdächtig. Kein publizierter OOS-Test nach März 2014. | Zusätzlich: XLU ist seit 2023/24 durch KI-/Rechenzentrums-Strombedarf **teilweise zyklisch** geworden — die ökonomische Grundannahme („Kapital flieht bei Stress in Versorger") gilt nicht mehr sicher. |
| **N12** | **Beta-Dispersion (Kuntz, JEF 2020)** | 36 getestete Varianten, eine Stichprobe, ein Markt, **alle Ergebnisse brutto ohne Kosten**. CXO: Outperformance konzentriert sich auf 2000–02 und 2008 → effektiv **n = 2 unabhängige Ereignisse in 27 Jahren**. | Bei 28 Sektor-ETFs kollabiert die Beta-Streuung ohnehin (XLP/XLU ~0,6 bis SMH/XBI ~1,4, Rangfolge über Jahre nahezu konstant) → misst eine Konstante plus Rauschen. |
| **N13** | **CSD / Return Dispersion als Renditesignal** | GWZ (2024, Abschn. 3.1.15) zu Maios `rdsp`: vorwärts erweitert t = −1,32, in homologer Spezifikation dreht das **Vorzeichen** (t = +0,78), OOS-R² negativ, 3 von 4 Strategien verlieren absolut Geld. Wörtlich: *„We dismiss rdsp as a useful predictor of equity premiums."* Präzedenzfall: Goyal/Santa-Clara (JF 2003) → **Bali et al. (JF 2005)**, dieselbe Familie schon einmal an Sample-Erweiterung **und** Gewichtungswahl gescheitert. | **Nur** als Volatilitäts-Prognose brauchbar (Niu et al., J. Forecasting 2023 — dort IS und OOS bestätigt). Nicht als Renditesignal. |
| **N14** | **Credit-/Term-Spread-Proxys (HYG/LQD, TLT/SHY)** | GWZ (RFS 2024): Term-Spread und Default-Spread schlagen den simplen historischen Mittelwert **nicht**. Lead-Lag-Literatur: **Aktien führen HY-Bonds**, nicht umgekehrt (in- und out-of-sample, im Bärenmarkt stärker). | Ihr würdet eine um Tage bis Wochen **verzögerte Kopie eures eigenen Aktiensignals** bauen — sieht im Backtest gut aus, liefert kein zusätzliches Wissen. |
| **N15** | **Mondphasen** | CXO (S&P 500, 1990–2018, 354 Ereignisse): Neumond schlägt Vollmond im Mittel, aber die Standardabweichung der 11-Tage-Renditen liegt bei 2,94 % / 3,41 % — riesig gegenüber der Differenz. „48 Länder" = keine 48 unabhängigen Tests. **Kein ökonomischer Mechanismus.** | **Stille Kollisionsgefahr:** der synodische Monat (29,53 Tage) liegt sehr nah am Kalendermonat → korreliert mechanisch mit euren TDOM-/ToM-Signalen und driftet nur langsam. Wer beide addiert, kauft denselben Monatszyklus zweimal. |

---

## (c) UNABHÄNGIGKEITS-BILANZ DER TOP-12

„Unabhängig" = **andere Autoren**, **andere Daten oder anderer Zeitraum**, **eigene Rekonstruktion**.

| # | Kandidat | Unabh. Bestätigungen | Dokumentierte Fehlschläge | Netto-Urteil |
|---|---|---:|---:|---|
| 1 | Bootstrap-Gate (Methode) | **3** (Connolly '89, STW '99/'01, NAJEF '26) | 0 | Methode, keine Edge. **Zwingend, vor allem anderen.** |
| 2 | Heston-Sadka Seasonality | **4** (HS '10 international · Keloharju '16 Commodities+Indizes · **HXZ '20 durch Skeptiker** · Du-Linie) | **1 partiell** (Li et al. '18: Emerging Markets schwach) | **Stärkster Kandidat.** Erwartung: Halbierung ggü. Paper-Zahlen. |
| 3 | IBS / Range-Position | **2** (Micaletti '23 global +10J · Kinlay '19) | **1 hart** (nicht-US-ETFs; DAX **invertiert**) · **1 weich** (Kinlay: Abschwächung ab ~2013) | Stark für **US-ETFs**. Nur als Filter, nie standalone (Kosten). |
| 4 | Nagel Vola-State-Gate | **2** (RFS peer-review · Pagonidis '13 andere Instrumente + anderer Indikator) | 0 · **1 Richtungs-Caveat** (Agnani/Aray '11: Januar-Effekt bei *hoher* Vola grösser) | **Geringstes Decay-Risiko der Liste** (Risikoprämie, kein Preisfindungsfehler). |
| 5 | Garman-Klass RV-Perzentil | **3 Messschicht** (Bali/Weinbaum '05 · Molnár '12 · G7 '25) · HAR-RV-Literatur für die Prognoseschicht | **0** für die Gate-**Anwendung** — dort existiert überhaupt keine Evidenz | Solides **Upgrade** des bestehenden Regime-Scores. Anwendungsschicht selbst walk-forward validieren. |
| 6 | ToM [-3,+3] adaptiv | **4** (Lakonishok/Smidt · Kunkel '03 19 Länder · McConnell/Xu '08 35 Märkte · **Etula RFS '20 Mechanismus**) | **2 Zerfall** (Plastun '19 · QuantSeeker '24: `[0,+3]` in US tot, `[-3,+3]` mit klarem Abwärtstrend) | Bestätigt, aber zerfallend. Wert liegt im **Settlement-Test** und im `PRE_ToM_HOLE`. |
| 7 | CFM EMA-Trend (105d) | **3 auf Portfolio-Ebene** (MOP '12 · **CFM '14, Daten ab 1800, andere Gruppe/Signal** · HOP '17 ab 1880) | **1 stark, exakt auf eurer Ebene** (Huang et al. JFE '20: Einzel-Asset-Zeitreihe hält Bootstrap nicht stand) · Post-2011 „virtually flat" | Portfolio-Evidenz exzellent, Einzel-Ticker-Evidenz schwach. **Als Drawdown-Filter**, nicht als Alpha. |
| 8 | Vol-Targeting | **2 für Risiko** (Harvey '18 60 Assets/90J · Kim/Tse/Wald '16) | **3 für Alpha** (Cederburg JFE '20 103 Strategien · Kang '21 Commodities · Angelidis/Tessaromatis '23) | **Risiko-Layer belegt, Alpha widerlegt.** An maxDD/Ulcer messen, nie an CAGR. |
| 9 | 52-Wochen-Hoch / Drawdown | **3** (Marshall/Cahan '05 Australien · Liu/Liu/Ma '11 20 Märkte · Du '08 Indizes) | **1 sauberer OOS-Fehlschlag genau auf Sektor-ETFs** (Du et al. '14) | Nur für **Einzelaktien-Universum** bauen. Auf ETFs verworfen. |
| 10 | Donchian-Breakout | **1** (FMPM '21: kein Zerfall in Commodities) + methodisch starke Originalstudie | **2 für Aktien** (STW '99 · Bajgrowicz/Scaillet '12) | Nur **GLD/SLV/USO/URA/GDX/XME**, ggf. TLT. Nicht auf Aktien-ETFs. |
| 11 | ΔAR Absorption Ratio | **1 für den Mechanismus** (Berger/Pukthuanthong JFE '12, 82 Länder) · **0 für die Handelsregel** | **1 Vorzeichenumkehr** in unabhängiger Implementierung · Autor räumt fehlendes OOS ein · ~20 unabh. Entscheidungen im Original | **Prototyp.** Nur bauen, wenn 2020 **und** 2022 rechtzeitig Flat liefern. Einziger strukturell orthogonaler Kandidat. |
| 12 | Marktbreite (Advance-Ratio) | **0** (nur 64-Länder-Breite innerhalb einer Studie) | **1** (Qi/Zhao '08: „drastisch abgeschwächt oder verschwunden") · kein Post-2018-Update | Schwächster der Top-12. Aufgenommen, weil ihr aus 324 Einzeltickern das **echte** Konstrukt bauen könnt. Erwartung niedrig ansetzen. |

---

## Sofort prüfen — potenzieller stiller Fehler im Bestand

Aus dem Momentum-Turning-Points-Eintrag, unabhängig von der Shortlist:

> **Euer Jegadeesh-StRev-21d-Filter könnte auf ETF-Ebene das falsche Vorzeichen haben.**

Short-Term-Reversal ist ein **Einzelaktien-Querschnitts**phänomen. Auf **Index-/ETF-Ebene** wirkt die 1-Monats-Rendite in der Literatur eher **momentum-artig** (so bereits Moskowitz/Ooi/Pedersen 2012 für Futures; so auch die FAST-Komponente bei Garg/Goulding/Harvey/Mazzoleni, JFE 2023, die dieselbe Grösse mit **positivem** Vorzeichen liest).

**Aktion:** In `indicators.js` prüfen, ob StRev-21d auf ETFs mit dem Vorzeichen aus der Einzelaktien-Literatur angewendet wird. Falls ja: getrennt auf Einzelaktien vs. ETFs auswerten, bevor der Filter weiter in Backtests genutzt wird. Das ist kein Shortlist-Kandidat, sondern ein möglicher Bug in produktivem Code.

---

## Empfohlene Implementierungsreihenfolge

**Phase 1 (Infrastruktur, kein Alpha):** #1 Bootstrap-Gate → #5 Garman-Klass (liefert `sigma_d` für #1 mit) → #8 Vol-Targeting als Sizing-Layer.
Dann N1 (FOMC) und N5 (RSP/SPY) als **Pipeline-Kalibrierung** durchlaufen lassen. Erst wenn die Pipeline diese beiden ablehnt, ist sie einsatzfähig.

**Phase 2 (höchster Erwartungswert):** #2 Heston-Sadka → #3 IBS-Gate → #4 Nagel-Vola-State.

**Phase 3 (Korrekturen am Bestand):** #6 ToM settlement-adaptiv → StRev-Vorzeichenprüfung → #9 52-Wochen-Hoch nur auf Einzelaktien.

**Phase 4 (Prototypen, jederzeit verwerfbar):** #7 CFM-Trend → #10 Donchian auf Rohstoff-Ticker → #11 ΔAR → #12 Breadth.
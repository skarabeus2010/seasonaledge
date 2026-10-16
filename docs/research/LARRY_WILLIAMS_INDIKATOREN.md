# Larry Williams — Indikatoren, Muster und Timing-Werkzeuge

Stand: 2026-10-16 · Recherche ohne Code-Änderung, ohne DB-Zugriff.

**Zweck:** vollständiger Katalog dessen, was Larry Williams veröffentlicht oder unter seinem Namen vertreibt, mit
Formel, Datenbedarf und Machbarkeit für SeasonAlpha. Grundlage für eine spätere Entscheidung, nicht für eine
Implementierung.

## Belegstufen

Jede Formel trägt eine Stufe. Nur Stufe A darf ohne weitere Prüfung als „Williams-Formel“ bezeichnet werden.

| Stufe | Bedeutung |
|---|---|
| **A — Primärquelle** | Williams' eigener Text (Buchauszug, ireallytrade.com) liegt vor und deckt die Formel. |
| **B — übereinstimmend sekundär** | Mehrere unabhängige Plattformen (TA-Lib, Barchart, LuxAlgo, StockCharts …) beschreiben dieselbe Formel; Primärtext nicht eingesehen. |
| **C — Rekonstruktion** | Nur Foren-/Community-Nachbauten, die untereinander abweichen. Vor Verwendung gegen das Buch prüfen. |
| **D — unbelegt** | Nur Name und Zweck bekannt (meist Vertriebspakete von StockCharts/Symbolik); keine Formel gefunden. |

Hauptquellen Williams: *How I Made One Million Dollars … Trading Commodities* (1973), *Long-Term Secrets to
Short-Term Trading* (1999, 2. Aufl. 2011), *The Definitive Guide to Futures Trading* (1988/89), *Trade Stocks and
Commodities with the Insiders: Secrets of the COT Report* (2005), Artikel in *Technical Analysis of Stocks &
Commodities* (Ultimate Oscillator 1985) und *Active Trader* (VIX Fix, Dez. 2007), die Pakete „Larry Williams Stock
Trading Starter Pack“ (StockCharts) und „Larry Williams Futures/Stock Indicators“ (Symbolik).

## Datenlage bei SeasonAlpha (geprüft im Repo)

- `prices`: `date, open, high, low, close, volume, log_return, tdom, tdoy`. `open/high/low` werden von
  `scripts/backfill_ohlc.py` nur dort gefüllt, wo sie NULL waren — **OHLC liegt also nicht für jede Zeile vor**
  (alte Stooq-/Index-Historien teils nur Close). Ein Indikator mit High/Low braucht deshalb eine Prüfung „OHLC
  vollständig im Fenster“, sonst rechnet er auf Lücken. `volume` wird von Nightly und Backfill geschrieben (bei
  Indizes oft 0/leer).
- **Open Interest:** nicht vorhanden (weder Futures-OI noch Optionen-OI in `prices`; Options-OI nur in den
  Options-Pipelines für US-Ketten).
- **COT:** `scripts/build_cot_positioning.py` holt **nur** den CFTC-Bericht *Traders in Financial Futures* (TFF)
  für den E-mini S&P 500 (Leveraged Funds, Asset Manager), Ausgabe `landing/data/cot_positioning.json`, bereits mit
  3-Jahres-Perzentil und z-Score. **Die Gruppe „Commercials“ existiert im TFF-Bericht nicht** — sie steht im
  *Legacy*-Bericht (gleiche freie Socrata-API, eigener Datensatz). Für Williams' Commercial Index müsste der
  Legacy-Bericht neu angebunden werden.
- **Zweitmärkte im Universum (`shared/symbols.py`):** Gold `GC=F`/`GLD`, Silber `SI=F`, Anleihen `TLT`/`IEF`,
  Rendite `^TNX`, `^VIX`, `ES=F`, `EURUSD=X`. **Kein Dollar-Index** (`DX-Y.NYB`/`UUP` fehlen) — für WillVal gegen den
  Dollar wäre ein Onboarding nötig.
- **Bereits vorhanden, Williams-nah:** TDOM (`/tdom-analyse`, Monthly 10), Wochentage (`/wochentage`), TDOY und
  Jahreszyklus, Präsidentenzyklus (`shared/calculations.get_presidential_cycle_year`, UECS, Midterm), Intermarket
  Anleihen→Aktien (`shared/intermarket.py`, `/intermarket`), COT-Panel auf `/flows`, Saison-Score mit Stichtag
  (`shared/saison_score.py`, nur Vorjahre).
- **Keine einzige Williams-Formel ist implementiert.** Grep über `landing/js/indicators.js`,
  `landing/js/strategy-compute.js`, `shared/`, `scripts/` nach `williams`, `willr`, `%R`, `ultimate`, `vix fix`,
  `willval`, `cot_index`, `commercial` findet nur Fremdtreffer (Sherwin-Williams, Williams Companies, Python-`%r`).
  `indicators.js` kennt SMA, EMA, RSI, Bollinger, MACD, LBR, Momentum (Carhart), StRev, Regime — **LBR ist Linda
  Bradford Raschke**, nicht Williams. „UHTS“/„UECS“ heißen „Ultimate …“, haben mit dem Ultimate Oscillator nichts zu
  tun.

---

## A. Oszillatoren und Indikatoren

### 1. Williams %R
- **Beschreibung:** Lage des Schlusskurses in der Spanne der letzten n Tage, gemessen vom Hoch aus. 1973 erstmals
  veröffentlicht.
- **Quelle:** *How I Made One Million Dollars* (1973), Auszug auf ireallytrade.com — **Stufe A**.
- **Formel (Original):** `%R = (HH_n − C) / (HH_n − LL_n) × 100`, n = **10** Tage. Skala 0 = Schluss am Hoch
  (überkauft), 100 = Schluss am Tief (überverkauft). Beispiel im Buch: H 280,5 / L 272,5 / C 278,5 → 25 %.
  Heutige Plattformen: gleiche Formel × −100 (Skala 0 … −100), n = 14. Später empfahl Williams n = halbe Länge des
  dominanten Zyklus.
- **Williams' Regeln (Primärquelle):** im Bullenmarkt kaufen, wenn %R unter 95 % (am Tief) schließt; nach einem
  Ausschlag auf 100 % fünf Handelstage warten, dann beim nächsten Unterschreiten von 95 % kaufen; im Bärenmarkt
  short bei ≤ 10 %; Seitwärtsmarkt beide Seiten. Immer mit Stopp und Bestätigung.
- **Daten:** High, Low, Close.
- **Machbarkeit:** sofort machbar, sofern OHLC im Fenster vollständig.
- **Im Repo:** nein.

### 2. Ultimate Oscillator
- **Beschreibung:** gewichtetes Mittel aus drei Fenstern, um Fehldivergenzen eines einzelnen Fensters zu dämpfen.
- **Quelle:** *Technical Analysis of Stocks & Commodities*, 1985 — **Stufe B** (Artikel nicht eingesehen, Formel
  bei allen Plattformen identisch).
- **Formel:**
  `TL = min(L, C[−1])`, `TH = max(H, C[−1])`, `BP = C − TL`, `TR = TH − TL`
  `A7 = ΣBP₇/ΣTR₇`, `A14 = ΣBP₁₄/ΣTR₁₄`, `A28 = ΣBP₂₈/ΣTR₂₈`
  `UO = 100 × (4·A7 + 2·A14 + 1·A28) / 7`
  Erst summieren, dann teilen (manche Beschreibungen teilen je Tag — abweichend).
- **Williams' Kaufregel:** bullische Divergenz, deren erstes Tief unter 30 liegt, bestätigt erst durch Bruch des
  Zwischenhochs der Divergenz (Verkauf gespiegelt über 70).
- **Daten:** H, L, C.
- **Machbarkeit:** sofort machbar (OHLC-Prüfung).
- **Im Repo:** nein.

### 3. Williams Accumulation/Distribution (WAD)
- **Beschreibung:** kumulierte Schlussbewegung gegen die „wahre“ Spanne; Divergenzwerkzeug. Nicht Chaikins A/D.
- **Quelle:** **Stufe B** (TA-Lib `WAD`, Barchart, Incredible Charts, LuxAlgo).
- **Formel:** `TRH = max(H, C[−1])`, `TRL = min(L, C[−1])`
  `AD_t = C − TRL` wenn `C > C[−1]`; `C − TRH` wenn `C < C[−1]`; `0` sonst.
  `WAD_t = WAD_{t−1} + AD_t`. Barchart glättet zusätzlich mit SMA 14.
- **Widerspruch:** Williams' ursprüngliche Fassung multipliziert `AD_t` laut mehreren Quellen mit dem Volumen;
  Achelis ließ den Faktor weg, und das ist die heute verbreitete Fassung. Beide Varianten benennen.
- **Daten:** H, L, C (+ Volumen in der Originalvariante).
- **Machbarkeit:** sofort machbar (Volumen-Variante nur für Einzelaktien/ETFs sinnvoll).
- **Im Repo:** nein.

### 4. POIV (Price, Open Interest, Volume)
- **Beschreibung:** Kombination aus Kurs, Open Interest und On-Balance-Volume.
- **Quelle:** Williams-Biografie nennt POIV; Formel aus ProRealCode-Forum — **Stufe C**.
- **Formel (Forum):** `POIV = Σ [ OI × (C − C[−1]) / (TrueHigh − TrueLow) ] + OBV`; TrueHigh/TrueLow dort nicht
  definiert (vermutlich wie WAD).
- **Daten:** C, H, L, Volumen, **Open Interest**.
- **Machbarkeit:** Daten fehlen (kein OI).
- **Im Repo:** nein.

### 5. Pro Go
- **Beschreibung:** trennt „öffentliches“ Kaufverhalten (Übernacht-Lücke) von „professionellem“ (Bewegung während
  der Sitzung).
- **Quelle:** Williams-Zitat im ProRealCode-Forum („Many, many years ago I wrote about how to separate public
  buying from professional buying“), Seminarunterlagen; Buch nicht benannt — **Stufe C**.
- **Formel (Konsens der Nachbauten):** `Public = SMA₁₄(O − C[−1])`, `Pro = SMA₁₄(C − O)`.
  Vorzeichen in den Nachbauten uneinheitlich (teils `O − C`). Lesart: Tiefs im Kurs, die die Pro-Linie nicht
  bestätigt, sind bullisch; Kreuzungen Pro/Public als mittelfristiges Signal.
- **Daten:** Open, Close.
- **Machbarkeit:** sofort machbar — **Achtung:** CLAUDE.md verbietet `Open[t]/Close[t−1]` wegen gemischter
  Adjustierungsfaktoren (Dividenden-Bias). Die Public-Linie ist genau diese Größe; nur als Residual
  (`Gesamt − Intraday`) aus `log_return` und `ln(C/O)` sauber rechenbar.
- **Im Repo:** nein. `/overnight` zerlegt bereits Übernacht/Intraday — Pro Go wäre dort eine Glättung derselben
  Zerlegung.

### 6. WillVal (Williams Valuation Index)
- **Beschreibung:** relative Bewertung eines Marktes gegen einen Vergleichsmarkt (Gold, Anleihen, Dollar),
  normiert auf 0–100. Ab etwa 1990.
- **Quelle:** **Stufe C** (eSignal-/ProRealCode-Forum, TradingView). StockCharts-Paket: Vergleich gegen TLT, GLD
  oder UUP, Linien 75/15, Rückblick 65 Perioden — **Stufe D für die Formel**.
- **Formel (Forum, wöchentlich):**
  `S = 100 × P / P_Vergleich` · `Pal = EMA₂₂(S) − EMA₂(S)` (Reihenfolge in Quellen uneinheitlich)
  `WillVal = (Pal − min₃J(Pal)) / (max₃J(Pal) − min₃J(Pal)) × 100`.
  Abweichungen: Fenster 3 Jahre (156 Wochen), 25 Perioden oder 65 Perioden; Schwellen 15/85 oder 15/75.
- **Daten:** Close des Markts + Close des Vergleichsmarkts.
- **Machbarkeit:** sofort machbar gegen Gold und TLT; gegen Dollar Daten fehlen (Onboarding `DX-Y.NYB`/`UUP`).
- **Im Repo:** nein.

### 7. WillSpread
- **Beschreibung:** Spread-Momentum zwischen Markt und Vergleichsmarkt als Filter („Anleihen bewegen Aktien“).
- **Quelle:** *Long-Term Secrets to Short-Term Trading* laut TradingView-Beschreibung — **Stufe C**.
- **Formel:** `S = 100 × A / B` · `WillSpread = EMA₅(S) − EMA₂₀(S)` (Vorzeichenkonvention prüfen). Long-Trades in A
  nur bei WillSpread > 0; nach Nulldurchgang einen Bestätigungsbalken abwarten. Beispiel: S&P gegen Bonds.
- **Daten:** Close zweier Märkte.
- **Machbarkeit:** sofort machbar (SPY/TLT, ^GSPC/IEF, Gold/TLT).
- **Im Repo:** nein. Verwandt: `shared/intermarket.py` (TLT-Anstieg → SPY), aber ereignisbasiert, nicht als
  laufender Spread.

### 8. COT Commercials Index (WillCo, „Williams Commercial Index“)
- **Beschreibung:** Netto-Position der Commercials (Hedger) als Stochastik über ein Fenster; Extreme = Wende.
- **Quelle:** *Trade Stocks and Commodities with the Insiders* (2005); Williams wörtlich zitiert: er sei auf das
  26-Wochen-Fenster übergegangen — **Stufe B** für das Fenster, **Stufe C** für die genaue Normierung.
- **Formel (verbreitet):**
  COT-Index: `(Net − min₂₆(Net)) / (max₂₆(Net) − min₂₆(Net)) × 100`, `Net = Comm_Long − Comm_Short`.
  WillCo-Variante: erst `Net / OI` (Normierung auf das Open Interest), dann dieselbe Stochastik über 26 Wochen;
  alternativ 52 Wochen oder 3 Jahre. Schwellen ≥ 75 bullisch, ≤ 25 bearisch.
  Forennutzer berichten, die Buchdarstellung („total open interest of the last 26 weeks“) sei mehrdeutig — Summe
  oder Netto. Vor Bau am Buch klären.
- **Daten:** COT **Legacy**-Bericht (Commercials, OI), wöchentlich, CFTC Socrata, frei.
- **Machbarkeit:** Daten fehlen, aber frei beschaffbar (gleiche API wie `build_cot_positioning.py`, anderer
  Datensatz). Für Gold, Anleihen, S&P, Währungen, Rohstoffe.
- **Im Repo:** teilweise verwandt — `/flows` Panel D rechnet Leveraged-Funds-Netto/OI mit 3-Jahres-Perzentil
  (TFF). Das ist weder Commercials noch 26 Wochen.

### 9. COT Large Spec Index / Small Spec Index
- **Beschreibung:** dieselbe Stochastik für Großspekulanten (Non-Commercials) und Kleinspekulanten
  (Nonreportable); Williams liest sie gegenläufig zu den Commercials.
- **Quelle:** Symbolik-Paket (Namen) — **Stufe D** für Abweichungen von Nr. 8; plausibel identische Formel.
- **Daten / Machbarkeit:** wie Nr. 8.
- **Im Repo:** nein.

### 10. Williams Open-Interest-Indikator
- **Beschreibung:** Inhaltsverzeichnis des COT-Buchs: Kapitel 8 „The Breakthrough“ mit „My Open Interest
  Indicator“ und „Open Interest as a timing or entry tool“; dazu ein Kapitel Commercials gegen Gesamt-OI.
- **Quelle:** O'Reilly-Inhaltsverzeichnis — **Stufe D** (Formel nicht gefunden).
- **Daten:** Open Interest.
- **Machbarkeit:** Daten fehlen.
- **Im Repo:** nein.

### 11. Williams VIX Fix
- **Beschreibung:** synthetische Volatilität ohne Optionsdaten; bildet VIX-Spitzen an Tiefs nach. Stammt von
  Larry Williams (Active Trader, Dez. 2007); die verbreitete TradingView-Fassung mit Bollinger-Band ist ein
  Zusatz von ChrisMoody, nicht von Williams.
- **Quelle:** **Stufe B** (LuxAlgo, StockCharts-Paket: Standard 22 Perioden).
- **Formel:** `VIXFix = (max₂₂(C) − L) / max₂₂(C) × 100`. Gelegentlich 20 statt 22. Invertierte Fassungen für
  Hochs sind nicht von Williams.
- **Daten:** Close, Low.
- **Machbarkeit:** sofort machbar (Low nötig). Interessant für Märkte ohne Volatilitätsindex (^GDAXI vor VDAX,
  Rohstoffe, Einzelaktien).
- **Im Repo:** nein.

### 12. Williams Sentiment Index
- **Beschreibung:** Ausmaß bullischer/bearischer Berater; Extreme markieren Hochs/Tiefs. Schwellen 75 (Verkauf) /
  25 (Kauf).
- **Quelle:** StockCharts- und Symbolik-Paket — **Stufe D** (Formel nicht gefunden; vermutlich Stochastik einer
  Beraterumfrage).
- **Daten:** Stimmungsumfrage (Investors Intelligence kostenpflichtig, AAII eingeschränkt frei, Market Vane für
  Futures kostenpflichtig).
- **Machbarkeit:** Daten fehlen.
- **Im Repo:** nein.

### 13. Williams Money Flow Index
- **Beschreibung:** schätzt institutionelle Akkumulation/Distribution; Schwellen 74/26.
- **Quelle:** StockCharts-Paket — **Stufe D**. Nicht mit dem allgemeinen MFI (Quong/Soudack) verwechseln.
- **Machbarkeit:** ohne Formel nicht machbar.
- **Im Repo:** nein.

### 14. Williams Insider Accumulation Index
- **Beschreibung:** Insider-Kauf/-Verkauf **ohne Volumen**, Standardlänge 14.
- **Quelle:** StockCharts-Paket — **Stufe D**. Vermutung (unbelegt): Verwandter von WAD, der die Sitzungsbewegung
  `C − O` in die Spanne setzt.
- **Machbarkeit:** ohne Formel nicht machbar.
- **Im Repo:** nein.

### 15. Williams Pinch/Paunch
- **Beschreibung:** Kaufgelegenheiten in Abwärtstrends; Signal, wenn der Wert nach einem Anstieg über 40 wieder
  fällt.
- **Quelle:** StockCharts-/Symbolik-Paket — **Stufe D**.
- **Machbarkeit:** ohne Formel nicht machbar.
- **Im Repo:** nein.

### 16. WillTrend, Volatility Trend Stop, WillStop, Turtle Channel, Target Shooter, Paint Bars
- **Beschreibung:** Trend-Linie (Kurs über Linie = Aufwärtstrend), Volatilitäts-Stopps, Kanal, Kursziele,
  eingefärbte Balken.
- **Quelle:** nur Namen in den Paketen — **Stufe D**.
- **Machbarkeit:** ohne Formel nicht machbar.
- **Im Repo:** nein.

### 17. Williams Advance/Decline Line
- **Beschreibung:** A/D-Linie aus einer kleineren Auswahl marktbestimmender NYSE-Titel.
- **Quelle:** StockCharts-Paket — **Stufe D** (Titelauswahl unbekannt).
- **Daten:** Breitendaten bzw. Kurse der Auswahl.
- **Machbarkeit:** nicht machbar ohne Liste; eine eigene Breite aus den ~370 Tickern wäre möglich, wäre aber nicht
  Williams' Indikator.
- **Im Repo:** nein.

---

## B. Ausbruch und Range

### 18. Volatility Breakout
- **Beschreibung:** Einstieg, wenn der Kurs sich vom Open (oder Vortagesschluss) um einen Anteil der jüngsten
  Spanne entfernt. Seit 1982; Williams selbst sagt, es funktioniere in neueren Jahren schlechter.
- **Quelle:** *Long-Term Secrets*, sekundär bei LuxAlgo — **Stufe B** für das Prinzip, Parameter frei.
- **Formel:** `Long-Stopp = O + k × (H[−1] − L[−1])`, `Short-Stopp = O − k × (H[−1] − L[−1])`, k < 1 (häufig 0,5–0,6);
  Varianten mit Durchschnittsspanne mehrerer Tage oder Bezug auf C[−1]. Ausstieg häufig am ersten profitablen Open
  („bailout“).
- **Daten:** O, H, L, C — und **Intraday**, um zu wissen, ob der Stopp innerhalb der Sitzung erreicht wurde
  (Tagesbalken genügen näherungsweise: `H ≥ Stopp`).
- **Machbarkeit:** mit Tagesdaten näherungsweise machbar (OHLC-Prüfung); keine Reihenfolge Hoch/Tief bekannt.
- **Im Repo:** nein.

### 19. Greatest Swing Value (GSV)
- **Beschreibung:** Volatility Breakout, dessen Abstand aus „gescheiterten Schwüngen“ gewonnen wird; soll den
  Umkehrtag eines kurzfristigen Trends treffen.
- **Quelle:** *Long-Term Secrets* — **Stufe C** (nur Forenbeschreibungen; Formel nicht belegt).
- **Rekonstruktion (zu prüfen):** Für Käufe die Tage mit Schluss unter Open betrachten und dort den Schwung
  `H − O` messen (der Aufwärtsschwung, der scheiterte); Mittel der letzten ~4 solcher Werte = GSV_buy;
  Einstieg `O + k × GSV_buy` mit k ≈ 1,8. Spiegelbildlich `O − L` an Aufwärtstagen für Verkäufe. Einige Quellen
  verknüpfen GSV-Käufe nur mit Tagen nach einem Abwärtstag.
- **Daten:** OHLC.
- **Machbarkeit:** machbar, sobald die Formel am Buch geprüft ist.
- **Im Repo:** nein.

---

## C. Kursmuster

### 20. Oops!
- **Beschreibung:** Eröffnung mit Lücke unter dem Vortagestief, Rückkehr in die Vortagesspanne; benannt nach dem
  Anruf eines Brokers, dessen Kunden-Stopps die Lücke ausgelöst hatte.
- **Quelle:** **Stufe B** (Oxfordstrat, MQL5, Unger Academy — übereinstimmend).
- **Regel:** Long, wenn `O < L[−1]`; Buy-Stopp bei `L[−1]` (Varianten + Filter in Ticks). Short gespiegelt
  (`O > H[−1]`, Sell-Stopp bei `H[−1]`). Williams filterte nach Wochentag (Käufe Mo/Di/Fr, laut Sekundärquelle).
  Die oft zitierte „93 %“ ist unbelegt.
- **Daten:** O, H, L; Auslösung innerhalb der Sitzung → Tagesnäherung `H ≥ L[−1]`.
- **Machbarkeit:** näherungsweise machbar. **Wichtig:** die Lückenhäufigkeit hängt an der Handelszeit (Futures mit
  Nachthandel haben kaum Lücken); auf Kassa-Indizes/ETFs sinnvoller.
- **Im Repo:** nein.

### 21. Smash Day (Naked Close)
- **Beschreibung:** Schluss unter dem Vortagestief (bzw. über dem Vortageshoch) — „nackter Schluss“; Umkehr, wenn
  der Folgetag die Smash-Day-Spanne wieder überschreitet.
- **Quelle:** *Long-Term Secrets*, sekundär Oxfordstrat/ProRealCode — **Stufe B**.
- **Regel:** Kauf-Setup `C < L[−1]`; Einstieg Buy-Stopp eine Tick über `H` des Smash Day am Folgetag. Verkauf
  gespiegelt (`C > H[−1]`, Sell-Stopp unter `L`).
- **Daten:** OHLC.
- **Machbarkeit:** näherungsweise machbar.
- **Im Repo:** nein.

### 22. Hidden Smash Day
- **Beschreibung:** Tag mit Schluss im Plus, aber nahe am Tagestief (im Aufwärtstrend: neues Hoch, Schluss unten).
- **Quelle:** RoboForex-Artikel und Bücherauszüge in Foren — **Stufe C**.
- **Rekonstruktion:** Kauf-Setup `C > C[−1]` **und** `C < O` **und** Schluss im unteren Viertel der Spanne
  (`(C − L)/(H − L) ≤ 0,25`); Einstieg über `H`. Ob Williams es als Umkehr oder Fortsetzung liest, ist in den Quellen
  uneinheitlich.
- **Daten:** OHLC.
- **Machbarkeit:** machbar nach Prüfung.
- **Im Repo:** nein.

### 23. Specialist Trap
- **Beschreibung:** Fehlausbruch aus einer kleinen Seitwärtsbox (nach Wyckoff); der Ausbruch lockt Käufer, der
  Rückfall unter das Tief des Ausbruchtags (bzw. des Vortags) löst den Verkauf aus.
- **Quelle:** **Stufe C** (RoboForex, Sekundärzusammenfassungen).
- **Rekonstruktion:** Box = 5–10 Tage enge Spanne; Ausbruchstag schließt deutlich darüber; innerhalb von 1–3 Tagen
  Unterschreitung des Tiefs des Ausbruchs- bzw. Vortags → Short. Spiegelbildlich unten. Parameter unbelegt.
- **Daten:** OHLC.
- **Machbarkeit:** machbar nach Festlegung; Parameter sind frei → Data-Mining-Risiko.
- **Im Repo:** nein.

### 24. Outside Day (mit Abwärtsschluss)
- **Beschreibung:** Außenstab (`H > H[−1]`, `L < L[−1]`), der unter dem Vortagestief schließt → Kauf am nächsten
  Open. TradingView-Skript nennt *The Secrets of Short-Term Trading* und 85 % Treffer auf dem S&P (unbelegt).
- **Quelle:** **Stufe C**.
- **Daten:** OHLC. **Machbarkeit:** machbar. **Im Repo:** nein.

### 25. Inside Day
- **Beschreibung:** `H < H[−1]` und `L > L[−1]`; bei Williams vor allem als Regel, Inside-Tage in der
  Marktstruktur (Nr. 26) zu ignorieren, und als Ausgangspunkt für Breakouts.
- **Quelle:** **Stufe B** (Definition allgemein).
- **Machbarkeit:** machbar. **Im Repo:** nein.

### 26. Kurzfristige / mittelfristige / langfristige Hochs und Tiefs (Marktstruktur)
- **Beschreibung:** verschachtelte Schwünge.
- **Quelle:** *Long-Term Secrets*, mehrere übereinstimmende Zusammenfassungen — **Stufe B**.
- **Regel:** kurzfristiges Hoch = Tageshoch, dessen Nachbartage beide tiefere Hochs haben (Inside-Tage
  ignorieren); mittelfristiges Hoch = kurzfristiges Hoch mit niedrigeren kurzfristigen Hochs beiderseits;
  langfristiges Hoch = dasselbe eine Ebene höher. Tiefs gespiegelt.
- **Achtung:** ein Punkt ist erst **einen Tag (bzw. einen Schwung) später** bekannt — im Backtest Look-ahead
  vermeiden (Regel `filterMask[entryIdx-1]` gilt hier mit Verzögerung).
- **Daten:** H, L. **Machbarkeit:** sofort machbar. **Im Repo:** nein.

---

## D. Kalender, Saisonalität, Zyklen

### 27. Trading Day of the Month (TDOM)
- **Beschreibung:** Williams machte die Zählung nach Handelstag im Monat populär (S&P und Bonds; Monatsende und
  erste Tage stark).
- **Quelle:** *Long-Term Secrets* — **Stufe B** (Prinzip); konkrete Tabellen nicht eingesehen.
- **Daten:** Close + Börsenkalender. **Machbarkeit:** vorhanden.
- **Im Repo:** **ja** — `/tdom-analyse`, `tdom`-Spalte, Monthly 10, Down-Month-ToM.

### 28. Trade Day of the Week (TDW)
- **Beschreibung:** Wochentagsfilter; Montag als bester Kauftag im S&P, Wochentage als Filter für Oops! und andere
  Muster, teils kombiniert mit einem Bond-Filter.
- **Quelle:** Sekundär (TradingView-Backtest, Blogs) — **Stufe B** für Montag, **Stufe C** für die genauen Regeln.
- **Machbarkeit:** vorhanden.
- **Im Repo:** **ja** — `/wochentage`, Dashboard-Wochentagskarte. Nicht als Filter in der Backtest-Engine.

### 29. Trading Day of the Year (TDOY) / Saisonalität
- **Daten / Machbarkeit:** vorhanden. **Im Repo:** **ja** — `tdoy`, `/jahreszyklus`, Saison-Score.

### 30. Williams True Seasonal
- **Beschreibung:** Saisonmuster, das zu jedem Datum **nur die bis dahin vorliegenden Jahre** nutzt (kein
  Zukunftswissen); laut StockCharts seit 1973. Standard-Rückblick ein Jahr, was Williams selbst zu kurz nennt.
- **Quelle:** StockCharts-Artikel und Paket — **Stufe B** für das Prinzip, **Stufe D** für die genaue Rechnung.
- **Rekonstruktion:** für Stichtag t den mittleren normierten Jahrespfad aus den Jahren < Jahr(t) bilden und den
  Wert am heutigen Kalender-/Handelstag ablesen (expandierendes Fenster).
- **Daten:** Close.
- **Machbarkeit:** sofort machbar.
- **Im Repo:** **teilweise** — der Saison-Score rechnet mit `as_of` nur auf Vorjahren (`shared/saison_score.py`,
  `saison-score.js`); die Jahreszyklus-Kurven dagegen mitteln über alle Jahre im Zeitraum. Eine explizite
  „ohne Zukunft“-Kurve fehlt.

### 31. Präsidentenzyklus, Wahljahre
- **Quelle:** Williams schreibt in seinen Jahresprognosen und Büchern über den Vierjahreszyklus — **Stufe B**
  (Prinzip, allgemein bekannt).
- **Im Repo:** **ja** — `get_presidential_cycle_year`, Strategien Midterm/UECS/Wahljahr, `/wahlen`, `/dekadenzyklus`.

### 32. Bond-Filter für Aktien
- **Beschreibung:** Aktienkäufe (S&P) nur, wenn Anleihen steigen.
- **Quelle:** *Long-Term Secrets*, sekundär erwähnt — **Stufe C** (konkrete Regel nicht gefunden).
- **Rekonstruktion:** Long S&P nur, wenn `C_Bond > C_Bond[−n]` (häufig n = 20 oder Bond über SMA) bzw.
  WillSpread(S&P/Bond) > 0.
- **Daten:** TLT/IEF bzw. `^TNX` (Rendite invers).
- **Machbarkeit:** sofort machbar.
- **Im Repo:** **verwandt** — `shared/intermarket.py` (Anleihenanstieg + Vola → Signal im Briefing), `/intermarket`.
  Als Backtest-Filter in `indicators.js` nicht vorhanden.

### 33. Gold-Filter für Anleihen
- **Beschreibung:** Anleihenkäufe nur bei fallendem Gold (Gold als Inflationsanzeiger).
- **Quelle:** **Stufe C**.
- **Rekonstruktion:** Long Bonds, wenn `C_Gold < C_Gold[−n]` oder WillSpread(Bond/Gold) > 0.
- **Machbarkeit:** sofort machbar (GC=F/GLD, TLT/IEF).
- **Im Repo:** nein (die Intermarket-Matrix enthält Gold- und Anleihenpaare, aber keinen Filter).

### 34. Williams Cycle Forecast
- **Beschreibung:** drei „zuverlässigste“ kurzfristige Zyklen werden addiert und gewichtet; Projektion etwa drei
  Monate voraus (Standardverschiebung 66 Handelstage). Zeitpunkt und Richtung, keine Kursziele.
- **Quelle:** StockCharts-Artikel (2023) und Paket — **Stufe D** für die Zyklen (Längen und Gewichte nicht
  veröffentlicht).
- **Machbarkeit:** nicht ohne Rekonstruktion (Zyklen frei wählbar → hohes Data-Mining-Risiko).
- **Im Repo:** nein. Verwandt: 40-Wochen- und 212-Wochen-Zyklus in `strategy-compute.js` (nicht von Williams).

### 35. Annual Forecast
- **Beschreibung:** Williams' jährlicher Ausblick (Zyklen, Saisonalität, Wahljahr); Mitgliederbereich
  ireallytrade.com.
- **Quelle:** Stufe D — Methode nicht offengelegt.
- **Machbarkeit:** nicht machbar (keine Formel, kein Datenprodukt). **Im Repo:** nein.

---

## Übersicht

| # | Name | Belegstufe | Daten | Machbarkeit | Im Repo |
|---|---|---|---|---|---|
| 1 | Williams %R | A | HLC | sofort (OHLC-Prüfung) | nein |
| 2 | Ultimate Oscillator | B | HLC | sofort | nein |
| 3 | Williams A/D | B | HLC (+Vol) | sofort | nein |
| 4 | POIV | C | HLC, Vol, OI | Daten fehlen | nein |
| 5 | Pro Go | C | OC | sofort (nur als Residual) | nein (`/overnight` verwandt) |
| 6 | WillVal | C | C + Gold/Bond/Dollar | sofort (ohne Dollar) | nein |
| 7 | WillSpread | C | C zweier Märkte | sofort | nein |
| 8 | COT Commercials Index / WillCo | B/C | COT Legacy | Daten frei beschaffbar | nein (`/flows` TFF verwandt) |
| 9 | COT Large/Small Spec Index | D | COT Legacy | Daten frei beschaffbar | nein |
| 10 | Open-Interest-Indikator | D | OI | Daten fehlen | nein |
| 11 | VIX Fix | B | C, L | sofort | nein |
| 12 | Sentiment Index | D | Umfrage | Daten fehlen | nein |
| 13 | Money Flow Index (Williams) | D | ? | nicht machbar | nein |
| 14 | Insider Accumulation Index | D | ? | nicht machbar | nein |
| 15 | Pinch/Paunch | D | ? | nicht machbar | nein |
| 16 | WillTrend, Stops, Kanäle, Paint Bars | D | ? | nicht machbar | nein |
| 17 | Williams A/D Line (NYSE-Auswahl) | D | Breite | nicht machbar | nein |
| 18 | Volatility Breakout | B | OHLC | Näherung | nein |
| 19 | Greatest Swing Value | C | OHLC | nach Buchprüfung | nein |
| 20 | Oops! | B | OHL | Näherung | nein |
| 21 | Smash Day / Naked Close | B | OHLC | Näherung | nein |
| 22 | Hidden Smash Day | C | OHLC | nach Prüfung | nein |
| 23 | Specialist Trap | C | OHLC | nach Festlegung | nein |
| 24 | Outside Day | C | OHLC | sofort | nein |
| 25 | Inside Day | B | HL | sofort | nein |
| 26 | Marktstruktur ST/IT/LT | B | HL | sofort | nein |
| 27 | TDOM | B | C + Kalender | vorhanden | **ja** |
| 28 | Trade Day of Week | B/C | C + Kalender | vorhanden | **ja** (nicht als Filter) |
| 29 | TDOY / Saisonalität | B | C | vorhanden | **ja** |
| 30 | True Seasonal | B/D | C | sofort | teilweise (Saison-Score) |
| 31 | Präsidentenzyklus | B | C | vorhanden | **ja** |
| 32 | Bond-Filter | C | C + TLT/IEF | sofort | verwandt (`intermarket.py`) |
| 33 | Gold-Filter für Bonds | C | C + Gold | sofort | nein |
| 34 | Cycle Forecast | D | C | nur Rekonstruktion | nein |
| 35 | Annual Forecast | D | — | nicht machbar | nein |

## Priorisierung: Nutzen für eine Saisonalitätsplattform × Machbarkeit

Bewertung je 1–3 (3 = hoch). Nutzen = passt zur Kernfrage „Kalender + Bedingung“, ergänzt Bestehendes, ist für
Leser nachvollziehbar. Machbarkeit = Daten vorhanden, Formel belegt, kein neuer Datenweg.

| Kandidat | Nutzen | Machbarkeit | Produkt | Begründung |
|---|---|---|---|---|
| **True Seasonal (ohne Zukunft)** | 3 | 3 | 9 | Beantwortet die Kernfrage jeder Saisonkurve („hätte man das damals gewusst?“); Rechenkern mit `as_of` existiert schon. |
| **Bond-/Gold-Filter + WillSpread** | 3 | 3 | 9 | Williams' Kombination Kalender × Intermarket; TLT/IEF/Gold vorhanden; passt als Filter in `indicators.js`/Backtest-Engine und zur Intermarket-Arbeit. Regel muss vorab festgelegt werden. |
| **TDOM/TDW als Filter mit %R** | 3 | 3 | 9 | %R ist der einzige Eintrag mit Primärquelle; Williams' eigene Methode war genau „Kalender-Tag + Oszillator“. Braucht OHLC-Vollständigkeitsprüfung. |
| **COT Commercials Index (Legacy, 26 Wochen)** | 3 | 2 | 6 | Williams' bekanntestes Werkzeug neben %R; Saisonalität + COT ist sein Kernansatz. Neuer, aber freier Datenweg; Normierung am Buch klären. |
| **Williams VIX Fix** | 2 | 3 | 6 | Formel belegt, einfache Rechnung; nützlich für Märkte ohne Volatilitätsindex. Abgrenzung zur Stress-Ampel nötig, damit nicht zwei Angstmaße nebeneinander stehen. |
| Ultimate Oscillator | 1 | 3 | 3 | Belegt, aber ohne Bezug zur Saisonalität. |
| WillVal | 2 | 2 | 4 | Formel unsicher (drei Varianten), Dollar fehlt. |
| Oops!/Smash Day/Muster | 1 | 2 | 2 | Kurzfrist-Muster; Tagesnäherung ohne Intraday-Reihenfolge, OHLC-Lücken. |
| Pro Go | 1 | 2 | 2 | Kollidiert mit der Regel gegen `Open[t]/Close[t−1]`; `/overnight` deckt das Thema ab. |
| Sentiment, POIV, OI, Paketindikatoren | 1 | 1 | 1 | Daten oder Formel fehlen. |

### Top 5 (Empfehlung)

1. **True Seasonal** — Saisonkurve je Stichtag nur aus Vorjahren; als Umschalter auf `/jahreszyklus` oder als
   eigene Darstellung „was die Kurve damals gezeigt hätte“. Kein neuer Datenweg.
2. **Bond-Filter / Gold-Filter / WillSpread** als Filter in der Backtest-Engine (`indicators.js` +
   Python-Zwilling), Regeln vor dem Test festschreiben (vgl. Intermarket-Methodik).
3. **Williams %R** als Filter, kombiniert mit TDOM/Wochentag — Primärquelle vorhanden, Williams' eigene
   Kombination.
4. **COT Commercials Index** auf dem Legacy-Bericht (Gold, Anleihen, S&P, Währungen), 26 Wochen; Ausbau von
   `build_cot_positioning.py` statt neuer Pipeline.
5. **Williams VIX Fix** — einfache, belegte Rechnung; als Volatilitätsmaß für Ticker ohne eigenen Index.

## Unsichere Formeln — vor jedem Bau am Buch prüfen

- **WillVal:** EMA-Längen (2/22), Reihenfolge der Differenz, Normierungsfenster (25 / 65 / 156 Perioden),
  Schwellen (15/75 oder 15/85).
- **COT-Index/WillCo:** Normierung auf OI ja/nein, „total open interest of the last 26 weeks“ (Summe oder Netto),
  Fenster 26 Wochen gegen 3 Jahre.
- **Pro Go:** Vorzeichen beider Linien uneinheitlich; Glättung 14 Tage.
- **Williams A/D:** mit oder ohne Volumenfaktor.
- **VIX Fix:** 22 (Williams) gegen 20 (Plattformen).
- **GSV:** welche Tage, welcher Schwung (H − O oder O − L), Anzahl Werte, Faktor (1,8?).
- **Hidden Smash Day, Specialist Trap, Outside Day:** Parameter und Lesart nur sekundär.
- **Bond-/Gold-Filter:** konkrete Rückblicklänge nicht gefunden.
- **Formel unbekannt:** Sentiment Index, Money Flow Index, Insider Accumulation Index, Pinch/Paunch, WillTrend,
  WillStop, Volatility Trend Stop, Turtle Channel, Target Shooter, Paint Bars, Williams A/D Line, Cycle Forecast,
  Open-Interest-Indikator, Annual Forecast.

## Quellen

- Williams %R, Primärtext: <https://futures.ireallytrade.com/williamspercentr>
- Ultimate Oscillator: <https://www.luxalgo.com/library/concept/ultimate-oscillator/>
- Williams A/D: <https://ta-lib.org/functions/wad.html>,
  <https://www.incrediblecharts.com/indicators/williams_accumulation_distribution.php>,
  <https://barchartsolutions.atlassian.net/wiki/spaces/CMDTYV/pages/1094353131/Accumulation+Distribution+Williams>
- POIV: <https://prorealcode.com/topic/indicatore-poiv-di-larry-williams>
- Pro Go: <https://www.prorealcode.com/topic/pro-go-williams>,
  <https://www.tradingview.com/script/ISkKvK49-William-s-ProGo-indicator/>
- WillVal: <https://prorealcode.com/topic/wiil-val-indicator>, <https://www.tradingview.com/script/QiwEE23w/>
- WillSpread: <https://www.tradingview.com/script/Rak6df4K/>
- COT-Index/WillCo: <https://www.tradingview.com/script/9Na7z1YC-CoT-MK-WillCo-Index/>,
  <https://de.tradingview.com/script/vouxNO8g-COT-Index-Commercial-Positioning-Weekly/>,
  <https://www.metalsmine.com/thread/post/4559826>,
  <https://oreilly.com/library/view/trade-stocks-and/9780471741251>
- VIX Fix: <https://www.luxalgo.com/library/concept/williams-vix-fix/>
- Paketübersichten: <https://help.stockcharts.com/charts-and-tools/stockchartsacp-plug-ins/larry-williams-stock-trading-starter-pack-plug-in>,
  <https://symbolik.com/addons/larry-williams-futures-indicators>,
  <https://symbolik.com/addons/larry-williams-stock-indicators>
- True Seasonal: <https://articles.stockcharts.com/article/articles-chartwatchers-2023-09-optimizing-your-stock-selectio-527/>
- Cycle Forecast: <https://articles.stockcharts.com/article/articles-chartwatchers-2023-08-predicting-tomorrows-price-mov-202/>
- Volatility Breakout / GSV: <https://www.luxalgo.com/library/concept/volatility-breakout/>,
  <https://bullcharts.com.au/Forum/printer_friendly_posts.asp?TID=845>
- Oops!: <https://oxfordstrat.com/?p=4503>, <https://www.mql5.com/en/articles/21741>, <https://ungeracademy.com/?p=7737>
- Smash Day / Hidden Smash Day / Specialist Trap:
  <https://oxfordstrat.com/trading-strategies/smash-day-pattern-a2/>,
  <https://www.prorealcode.com/prorealtime-indicators/larry-williams-smash-days>,
  <https://roboforex.com/blog/education/catch-your-smash-day-with-larry-williams/>,
  <https://roboforex.com/blog/education/false-breakouts-on-financial-markets-how-to-detect-and-use/>
- Marktstruktur: <https://optionstradingiq.com/long-term-secrets-to-short-term-trading/>,
  <https://www.tradingview.com/script/3bpbtsEs-Larry-Williams-Market-Structure/>
- Wochentag/Bond-Filter: <https://my.tradingview.com/chart/ES1%21/8fei8LYr-Buy-the-E-mini-SP-500-on-Mondays-Statistics-Becktest>

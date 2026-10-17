# GitHub-Recherche: Saisonalität, strukturelle Flows, Optionen (Stand 2026-10-17)

Recherche über öffentliche GitHub-Repositories zu den drei Themen der Plattform. Gelesen wurden
READMEs und, wo es für die Bewertung nötig war, Quelltext (per api.github.com und
raw.githubusercontent.com, anonym). Kein fremder Code wurde ausgeführt. Sterne und letzter Push
stammen aus der GitHub-API vom 2026-10-17.

**Lizenzregel:** MIT/Apache/BSD = Code übernehmbar (mit Lizenzvermerk) · GPL/AGPL = nur die Idee ·
keine Lizenz oder NOASSERTION = nichts übernehmen, auch keine Codeteile.

**Allgemeiner Befund vorab:** Zu Saisonalität gibt es auf GitHub kaum Substanz — fast nur
Einzelnotebooks mit ein paar Sternen, meist ohne Lizenz, oft mit In-Sample-Auswertung. Die
Kalenderbibliotheken (`exchange_calendars`, `pandas_market_calendars`) sind das einzig Belastbare
in diesem Bereich. Bei Optionen ist das Feld groß, aber fast durchgehend „GEX-Dashboard aus der
CBOE-Delayed-Chain“ mit derselben naiven Händlerannahme; methodisch interessant sind nur wenige.
Bei Flows ist ein einziges Repo wirklich nützlich (CTA-Replikation nach Kestner).

---

## Kurzfazit — Top 5

| # | Repo | Einstufung | Warum |
|---|------|-----------|-------|
| 1 | [hobinkwak/CTA-Position-Monitoring](https://github.com/hobinkwak/CTA-Position-Monitoring) (MIT) | **übernehmen (Methode)** | Setzt Kestner (2020) „Replicating CTA Positioning“ sauber um: normiertes Momentum als t-Statistik, Kappung, inverse Vola-Gewichtung, Ensemble 16/32/52 Wochen. Unser CTA-Proxy in `build_cot_positioning.py` ist eine SMA-Mischung mit gesetzten Gewichten (20/50/100/200 → 0,15/0,25/0,30/0,30) auf nur einem Markt. **Achtung:** Standard `leverage_scaling = "in_sample"` skaliert die ganze Historie mit Zukunftswissen — nur `expanding` übernehmen. |
| 2 | [je-suis-tm/quant-trading](https://github.com/je-suis-tm/quant-trading) — `VIX Calculator.py` (Apache-2.0) | **als Gegenprüfung nutzen** | Bildet das Cboe-VIX-Verfahren nach (Forward aus geringster Call-Put-Differenz, K0 ≤ F, modellfreie Varianz aus OTM-Preisen, Interpolation auf 30 Tage). Damit ließe sich aus unserer SPY-Kette eine modellfreie 30-Tage-Varianz rechnen und gegen `^VIX` in der DB prüfen — und je Ticker ein VRP in der Definition der Literatur (Carr/Wu: modellfreie implizite Varianz − realisierte Varianz) neben unseren ATM-basierten VRP stellen. |
| 3 | [marcusdrewry/gex-forward-returns](https://github.com/marcusdrewry/gex-forward-returns) (keine Lizenz) | **als Gegenprüfung nutzen (nur Methode)** | Prüft auf der freien SqueezeMetrics-Reihe (`DIX.csv`, GEX täglich ab 2011), ob GEX Renditen vorhersagt: Newey-West, rollierender 252-Tage-z-Score ohne Zukunftswissen, Kontrolle für VIX/realisierte Vola/Momentum. Ergebnis: univariat t ≈ −2,0, nach Kontrolle Vorzeichenwechsel und nicht signifikant; GEX sagt Vola voraus, aber kaum mehr als der VIX. Genau diese Prüfung fehlt bei uns, bevor eine Seite GEX als Signal liest. Code nicht übernehmen, Prüfdesign nachbauen. |
| 4 | [gerrymanoim/exchange_calendars](https://github.com/gerrymanoim/exchange_calendars) (Apache-2.0) + [rsheftel/pandas_market_calendars](https://github.com/rsheftel/pandas_market_calendars) (MIT) | **als Gegenprüfung nutzen** | Gepflegte Kalender für XNYS, XETR, XLON, XTKS u. a. mit Sitzungszeiten und Frühschlüssen. Als unabhängiger Abgleich für `shared/boersenereignisse.py` und die offenen LSE-Halbtage brauchbar. **Nicht** als Ersatz: unsere Korrekturen (XETRA 2002–2010, TSE-Sonderfälle, NYSE 1972–1994) sind belegt; jede Abweichung braucht eine Quelle, bevor eine Seite recht bekommt. |
| 5 | [aaguiar10/gflows](https://github.com/aaguiar10/gflows) (MIT) | **als Gegenprüfung nutzen** | Rechnet Delta-, Gamma-, Vanna- und Charm-Exposure mit laufzeitabhängigem Zins aus der Treasury-Kurve und nimmt für 0/1 DTE das Vortagesvolumen statt Open Interest. Relevant für den offenen Posten „Vanna-Vorzeichen gegen FlashAlpha“: gflows skaliert Vanna mit `· S · σ` und Charm mit `· S · T` — andere Normierungen als bei uns. Zahlen verschiedener Anbieter sind ohne Normierungsabgleich nicht vergleichbar. |

---

## Thema 1: Saisonalität und Kalendereffekte

| Repo | ★ | Letzter Push | Lizenz | Was es rechnet | Belegt? | Daten bei uns? | Einstufung |
|------|---|--------------|--------|----------------|---------|----------------|------------|
| [gerrymanoim/exchange_calendars](https://github.com/gerrymanoim/exchange_calendars) | 680 | 2026-10-12 | Apache-2.0 | Börsenkalender (Sitzungen, Öffnungs-/Schlusszeiten, Pausen) für ~50 Börsen | Gepflegt, Issues mit Quellen | ja (nur Kalender) | Gegenprüfung |
| [rsheftel/pandas_market_calendars](https://github.com/rsheftel/pandas_market_calendars) | 1003 | 2026-10-05 | MIT | Spiegelt exchange_calendars, ergänzt CME/CBOE-Futures-Kalender, Frühschlüsse | wie oben | ja | Gegenprüfung |
| [LuxAlgo/edge-stats](https://github.com/LuxAlgo/edge-stats) | 135 | 2026-09-24 | MIT | Bedingte Häufigkeiten `P(Ergebnis \| Bedingungen)` mit N, 95-%-KI, Hälftenstabilität, Jahreswerten; DuckDB; Fokus Intraday | Statistikhülle sauber; keine Aussagen über Effekte | nein (Intraday-Bars) | nur Idee (Ergebnis-Hülle) |
| [paappraiser/almanac-trading-strategies](https://github.com/paappraiser/almanac-trading-strategies) | 1 | 2026-06-24 | keine | 14 Almanac-Regeln (Best Six Months, Präsidentenzyklus, ToM, Pre-Holiday, Santa …) als Composite-Score | Überschrift = In-Sample-Split; Walk-forward OOS deutlich unter Buy & Hold (SPY 6,5 % vs. 14,1 % p. a.) | ja | ignorieren |
| [lieblm/thanksgiving-alpha](https://github.com/lieblm/thanksgiving-alpha) | 5 | 2025-12-19 | NOASSERTION | Thanksgiving-/Cyber-Monday-/Santa-Fenster je Aktie, NYSE-Kalender, Benjamini-Hochberg | FDR-Korrektur gut; aber heutige Indexmitglieder bis 2000 zurück (Survivorship), „270-Aktien-Auswahl nach Datenqualität“ | ja | nur Idee |
| [dylanfoocejun2412/weekend_effect](https://github.com/dylanfoocejun2412/weekend_effect) | 0 | 2026-06-04 | keine | Montagseffekt bedingt auf Vortages-VIX, SPY + 11 Sektor-ETFs, 2015–2025 | Saubere Hypothese, VIX vom Vortag (kein Zukunftswissen), kurze Stichprobe | ja | nur Idee |
| [brian-m0k/Stock-Traders-Almanac-…](https://github.com/brian-m0k/Stock-Traders-Almanac-Financial-Markets-Seasonality-Analysis-with-Python) | 1 | 2025-09-28 | keine | Notebook-Sammlung zu Almanac-Mustern | Ankündigung, wenig Inhalt | — | ignorieren |
| [handiko/Monthly-Seasonality-Trading-Strategy-Backtest](https://github.com/handiko/Monthly-Seasonality-Trading-Strategy-Backtest) | 1 | 2026-06-07 | keine | Kauf am ersten Handelstag Monat A, Verkauf Monat B | Kein Test, keine Kosten | ja | ignorieren |
| [Ryan-Childs-1/Futures-Cyclicality-Seasonality-Analyzer](https://github.com/Ryan-Childs-1/Futures-Cyclicality-Seasonality-Analyzer) | 0 | 2026-02-17 | keine | Monats-/Wochen-Statistik für Rohstoffe, Streamlit | In-Sample als Option, ohne Kosten | teils | ignorieren |
| [WinstonZhuang/US-Election-Stock-Trend-Analysis](https://github.com/WinstonZhuang/US-Election-Stock-Trend-Analysis) | 0 | 2024-07-03 | MIT | Präsidentenzyklus-Mittelwerte S&P 500 | Deskriptiv, ohne Kontrolljahre | ja | ignorieren (unsere `/wahlen` ist strenger) |
| [aandres99/SP500-Studies](https://github.com/aandres99/SP500-Studies) | 1 | 2018-09-05 | MIT | Kalenderanomalien S&P 500 | alt, Notebook | ja | ignorieren |
| [katiapek/markets-dashboard](https://github.com/katiapek/markets-dashboard) | 3 | 2026-03-17 | keine | Futures-Dashboard: COT + Saisonüberlagerung | Darstellung, kein Test | teils | nur Idee |

**Kalender-Spreads auf Futures, OPEX-Woche, Halloween/Sell in May, True Seasonal:** Die Suche
lieferte zu diesen Stichworten nichts Verwertbares (die Treffer zu „sell in may“ und „turn of the
month“ sind Spam- oder Fremdrepos). Unsere Umsetzung (True Seasonal, Kontrolljahre bei Wahlen,
belegte Kalender) liegt über dem, was öffentlich auf GitHub steht.

## Thema 2: Strukturelle Flows

| Repo | ★ | Letzter Push | Lizenz | Was es rechnet | Belegt? | Daten bei uns? | Einstufung |
|------|---|--------------|--------|----------------|---------|----------------|------------|
| [hobinkwak/CTA-Position-Monitoring](https://github.com/hobinkwak/CTA-Position-Monitoring) | 0 | 2026-10-01 | MIT | CTA-Positionen in 16 Futures nach Kestner (2020), Szenarien, Flip-Preise, COT-Vergleich | Paper (SSRN 3674828), Modellgüte (R², Tracking Error) und 125er-Sensitivität im Repo | teils (ES=F, GC=F, CL=F, HG=F, ^N225, ^GDAXI, ^FTSE, EURUSD=X, AUDUSD=X, TLT/IEF); keine Bund/Gilt/JGB, kein SG-Trend-Index | **übernehmen** (Methode, nur `expanding`) |
| [tschm/TinyCTA](https://github.com/tschm/TinyCTA) | 18 | 2026-10-14 | MIT | Bausteine: Oszillatoren, EWMA-Crossover, vola-adjustierte Renditen, robuste Vola (MAD) | Bibliothek, Tests; keine Effektbehauptung | ja | Gegenprüfung |
| [pst-group/pysystemtrade](https://github.com/pst-group/pysystemtrade) | 3555 | 2026-10-16 | GPL-3.0 | Carvers System: EWMAC-Trend, Carry, Vola-Targeting, Forecast-Skalierung | Bücher Carver, langjährig produktiv genutzt | teils | nur Idee |
| [NDelventhal/cot_reports](https://github.com/NDelventhal/cot_reports) | 198 | 2024-04-06 | MIT | Lädt CFTC-COT (Legacy, Disaggregated, TFF, Futures/Optionen kombiniert) als DataFrame | Datenabruf, kein Effekt | ja (öffentliche CFTC-Dateien) | übernehmen (als Bibliothek oder Vorbild) |
| [philsv/pycot](https://github.com/philsv/pycot) | 19 | 2025-07-07 | MIT | dasselbe, schlanker | — | ja | Gegenprüfung |
| [isaergun/etf-flows-data](https://github.com/isaergun/etf-flows-data) | 3 | 2026-10-16 | keine | ETF-Flows aus Δ Anteile × Preis, zweimal täglich per Actions | Herkunft der Anteilsdaten unklar | — | ignorieren (Methode haben wir in `build_etf_flows.py`) |
| [kianjagtiani/QuantSC-Capstone](https://github.com/kianjagtiani/QuantSC-Capstone) | 0 | 2026-07-17 | MIT | Short beider Beine eines 3x-ETF-Paars (Volatilitätszerfall) | In-Sample-Raster, Leihkosten ignoriert (selbst benannt) | — | ignorieren |
| [Morwane/implied-correlation-dispersion](https://github.com/Morwane/implied-correlation-dispersion) | 1 | 2026-06-08 | MIT | CBOE `.COR1M/3M`, `.DSPX` vs. realisierte Sektorkorrelation, HMM-Drossel | Daten LSEG; benennt selbst, dass implizit (Top-50-Aktien) und realisiert (Sektor-ETFs) verschiedene Grundmengen sind | teils (`^COR1M` ja, LSEG nein) | Gegenprüfung (für unseren Korrelations-Text) |
| [MatCuns/Covariance-Based-Dynamic-Risk-Parity…](https://github.com/MatCuns/Covariance-Based-Dynamic-Risk-Parity-Portfolio-with-Volatility-Targeting) u. ä. Risk-Parity-Repos | 0–4 | div. | meist keine | Portfoliokonstruktion mit Ziel-Vola | Studentenprojekte | — | ignorieren |

**Buyback-Blackout, Pensions-/Quartalsend-Rebalancing, Vol-Control:** Kein einziges substanzielles
Repo. Die Suche nach „vol control fund rebalancing“, „pension rebalancing quarter end“ und „share
buyback blackout“ ergab keine Treffer bzw. nur Scraper ohne Methode. Unsere Proxys stehen damit
ohne öffentliches Gegenstück.

**Leveraged-ETF-Rebalancing:** Auf GitHub nichts Brauchbares, aber die Formel ist geschlossen und
belegt: Rebalancing-Volumen = N · D · (L² − L) (N = NAV zu Tagesbeginn, D = Tagesbewegung des
Index, L = Hebel; [Bank Underground 2023](https://bankunderground.co.uk/2023/08/31/leveraged-and-inverse-etfs-the-exotic-side-of-exchange-traded-funds/),
empirisch [Barbon/Beckmeyer/Buraschi/Moerke, SSRN 3925725](https://papers.ssrn.com/abstract=3925725)).
Für 2x/3x long und −1x/−2x/−3x short haben alle Fonds dieselbe Flussrichtung wie der Markt. Wir
haben SOXL, aber weder TQQQ/SQQQ/UPRO noch NAV/Anteile — dafür bräuchte es eine Quelle für
Fondsvermögen. Nur Idee, solange diese Quelle fehlt.

## Thema 3: Optionen

| Repo | ★ | Letzter Push | Lizenz | Was es rechnet | Belegt? | Daten bei uns? | Einstufung |
|------|---|--------------|--------|----------------|---------|----------------|------------|
| [aaguiar10/gflows](https://github.com/aaguiar10/gflows) | 115 | 2025-10-02 | MIT | DEX/GEX/VEX/CEX je Strike und Verfall, Flip über 300 Kursniveaus, laufzeitgerechter Zins, Volumen statt OI bei 0/1 DTE | Formeln nachvollziehbar, keine Validierung | ja | Gegenprüfung |
| [je-suis-tm/quant-trading](https://github.com/je-suis-tm/quant-trading) (`VIX Calculator.py`) | 11047 | 2026-06-20 | Apache-2.0 | Cboe-VIX-Methode: Forward, K0, modellfreie Varianz, 30-Tage-Interpolation | Cboe-White-Paper | ja (Massive-Kette) | Gegenprüfung |
| [marcusdrewry/gex-forward-returns](https://github.com/marcusdrewry/gex-forward-returns) | 1 | 2026-06-05 | keine | Prädiktive Regression GEX → Rendite/Vola, HAC, Kontrollen | Sauberes Ökonometrie-Design, Stambaugh-Bias benannt | ja (eigene GEX-Historie seit 2026; SqueezeMetrics-Reihe frei) | Gegenprüfung (Methode) |
| [itsfabtrading/Gex-Multi](https://github.com/itsfabtrading/Gex-Multi) | 7 | 2026-08-04 | Apache-2.0 | Flip, Walls, „Magnet“ (größtes Brutto-Gamma), 0DTE-Unterlevels, 1-Tages-Spanne, SQLite-Historie | Methodik als benannte Konstanten; T-Untergrenze 1/262 gegen Gamma-Explosion bei 0DTE | ja | Gegenprüfung |
| [gammagrid/gammagrid](https://github.com/gammagrid/gammagrid) | 86 | 2026-10-12 | AGPL-3.0 | GEX, Max Pain, OI, IV-Surface, speichert jeden Snapshot | Dashboard, Hostingangebot | ja | nur Idee |
| [FlashAlpha-lab/gex-explained](https://github.com/FlashAlpha-lab/gex-explained) | 17 | 2026-08-26 | MIT | Lehrtext + Code GEX = Γ · OI · 100 · S² · 0,01 | Standardformel; Werbe-Repo des Anbieters FlashAlpha | ja | Gegenprüfung (schwach) |
| [jensolson/SPX-Gamma-Exposure](https://github.com/jensolson/SPX-Gamma-Exposure) | 167 | 2025-07-30 | keine | SPX-GEX aus CBOE-Datei + Sensitivitätstabelle, Greeks je Strike | klassisches Vorgehen | ja | nur Idee |
| [Matteo-Ferrara/gex-tracker](https://github.com/Matteo-Ferrara/gex-tracker) | 222 | 2023-04-08 | keine | GEX gesamt/Strike/Verfall aus CBOE-JSON | Annahme „Händler long Calls, short Puts“ ohne Prüfung; Strike-Parser wirft Nachkommastellen weg | ja | ignorieren |
| [EazyDuz1t/EzOptions](https://github.com/EazyDuz1t/EzOptions) / [-Schwab](https://github.com/EazyDuz1t/EzOptions-Schwab) | 80 / 45 | 2026 | keine / GPL-3.0 | Echtzeit-Dashboard Greeks-Exposure | — | nein (Echtzeit) | ignorieren |
| [puneet-chandna/0DTE-dealer-gamma](https://github.com/puneet-chandna/0DTE-dealer-gamma) | 11 | 2026-10-16 | NOASSERTION + kommerzielle Lizenz | Echtzeit-SPX-0DTE-GEX | — | nein (Intraday) | ignorieren |
| [dhawalc/spx-gamma-levels](https://github.com/dhawalc/spx-gamma-levels) | 2 | 2026-10-16 | NOASSERTION | tägliche SPX-Levels | — | — | ignorieren |
| [XanderRobbins/Arbitrage-Free-Volatility-Surface](https://github.com/XanderRobbins/Arbitrage-Free-Volatility-Surface) | 12 | 2026-05-14 | MIT | IV (Jäckel-Startwert + Newton + Brent), Arbitrageprüfungen, SVI-Fit, Heston (COS) | Gatheral/Jacquier 2014 zitiert; 108 Tests | ja | Gegenprüfung |
| [JackJacquier/SSVI](https://github.com/JackJacquier/SSVI) | 63 | 2020-05-10 | keine | SSVI-Parametrisierung + lokale Vola (vom Mitautor des SSVI-Papers) | Paper | ja | nur Idee |
| [wangys96/SVI-Volatility-Surface-Calibration](https://github.com/wangys96/SVI-Volatility-Surface-Calibration) | 85 | 2020-05-13 | keine | SVI-Kalibrierung 50ETF | — | — | ignorieren |
| [vollib/vollib](https://github.com/vollib/vollib) / [vollib/py_vollib](https://github.com/vollib/py_vollib) | 1030 / 441 | 2023 / 2026-05 | MIT | IV-Inversion nach Jäckel „Let's be rational“, Greeks analytisch/numerisch | Referenzverfahren | ja | Gegenprüfung |
| [marcdemers/py_vollib_vectorized](https://github.com/marcdemers/py_vollib_vectorized) | 162 | 2024-12-02 | MIT | dasselbe vektorisiert | — | ja | Gegenprüfung |
| [dougransom/vix_utils](https://github.com/dougransom/vix_utils) | 64 | 2026-04-09 | MIT | VIX-Futures- und Kassa-Termstruktur aus Cboe-Historie, 30-Tage-Konstantlaufzeit der vorderen zwei Kontrakte | Cboe-Daten, benennt fehlende Tage | ja (Cboe-Dateien, ^VIX9D/^VIX3M/^VIX1D in der DB) | übernehmen (Pipeline-Vorbild) |
| [Morwane/implied-correlation-dispersion](https://github.com/Morwane/implied-correlation-dispersion) | 1 | 2026-06-08 | MIT | siehe Flows | | | Gegenprüfung |
| [YichengYang-Ethan/vol-regime-toolkit](https://github.com/YichengYang-Ethan/vol-regime-toolkit) | 4 | 2026-03-01 | MIT | IV-Perzentil, RV, GARCH, „SELL/NEUTRAL“-Scanner | Signalbehauptung ohne Test | ja | ignorieren |
| [quantgalore/spx-vol-engine](https://github.com/quantgalore/spx-vol-engine) | 14 | 2023-04-05 | keine | Strike-Auswahl für SPX-Prämienverkauf | — | — | ignorieren |
| [eigenquant53/VRP](https://github.com/eigenquant53/VRP) | 33 | 2022-12-20 | keine | Backtest einer Abschlussarbeit zur VIX-Termstruktur | README ein Satz | — | ignorieren |
| [asad70/Options-Max-Pain-Calculator](https://github.com/asad70/Options-Max-Pain-Calculator) | 23 | 2023-03-31 | keine | Max Pain | trivial | ja | ignorieren |

Zu Dispersion/impliziter Korrelation gibt es fast nur Repos mit 0–1 Sternen aus den letzten
Monaten (zum Teil offensichtlich generiert, mit Formulierungen wie „institutional-grade“). Außer
Morwane hat keines eine nachvollziehbare Datenbasis.

---

## Detailabschnitte zu den Top-Funden

### 1. CTA-Positionierung nach Kestner — hobinkwak/CTA-Position-Monitoring

- **URL / Lizenz:** https://github.com/hobinkwak/CTA-Position-Monitoring · MIT · Push 2026-10-01, 0 Sterne (neu, aber sorgfältig).
- **Rechnung:** wöchentliches Raster; `m = (Mittel der letzten L Wochenrenditen / Wochen-Vola) · √L` (= t-Statistik des Trends), gekappt bei ±1; Gewicht ∝ 1/Vola; Ensemble aus 16/1/60, 32/1/60, 52/1/60 (Wochen/Kappe/Vola-Tage); Ensemble auf die Vola des SG-Trend-Index skaliert. Erweiterungen (Szenarien, „Flip-Preise“ = Kurs, bei dem das Vorzeichen kippt, Handelsdruck) sind im Repo als Erweiterung markiert.
- **Beleg:** Kestner (2020), SSRN 3674828. Das Repo zeigt Replikations-R², Tracking Error, rollierende Güte und eine Sensitivität über 125 Parameterkombinationen — das ist mehr Selbstprüfung als bei fast allen anderen gesichteten Repos.
- **Look-ahead:** `leverage_scaling = "in_sample"` ist Standard (wie im Paper). Damit hängt die historische Positionshöhe von der Vola der ganzen Reihe ab, also auch von der Zukunft. Für eine Seite, die eine Historie zeigt, nur `expanding` (mindestens 104 Wochen) verwenden. Die Richtung (Vorzeichen von m) ist davon nicht betroffen, die Größe schon.
- **Daten:** Das Repo verlangt rückwärts verkettete Futures. Unsere `=F`-Reihen sind Front-Monate von Yahoo ohne Roll-Anpassung — Rollsprünge würden als Renditen gezählt (bei CL=F erheblich). Entweder Renditen aus ETF-Stellvertretern (SPY, TLT, GLD, USO, FX-Kassa) oder die Rollsprünge an Verfallstagen herausnehmen. Bund, Gilt, JGB und Sojabohnen fehlen; die Kalibrierung auf den SG-Trend-Index entfällt (Index nicht frei) — dann nur relative Positionierung zeigen, keine Dollarbeträge.
- **Nutzen für uns:** ersetzt den SMA-Mix in `build_cot_positioning.py` durch eine publizierte Methode, erweitert von ^GSPC auf ~10 Märkte, und liefert mit dem „Flip-Preis“ eine konkrete Zahl (ab welchem Kurs dreht das Modell). COT bleibt als unabhängige Gegenprobe (das Repo vergleicht Modell und COT selbst).
- **Einstufung:** übernehmen (Methode, Code mit MIT-Vermerk möglich); vor Veröffentlichung eigene Validierung gegen COT Leveraged Funds.

### 2. Modellfreie 30-Tage-Varianz — je-suis-tm/quant-trading, `VIX Calculator.py`

- **URL / Lizenz:** https://github.com/je-suis-tm/quant-trading · Apache-2.0 · 11 047 Sterne (für das Gesamtrepo, die meisten anderen Dateien sind einfache Indikator-Backtests ohne Belang).
- **Rechnung:** Forward über den Strike mit kleinster |Call − Put|, K0 = größter Strike ≤ F, Beitrag ΔK/K² · e^{rT} · Q(K) über OTM-Optionen bis zu zwei aufeinanderfolgenden Null-Geboten, σ² = 2/T · Σ − (F/K0 − 1)²/T, Interpolation zwischen naher und nächster Laufzeit auf 30 Tage in Minuten; Zins aus der CMT-Kurve.
- **Beleg:** Cboe VIX White Paper. Ob alle Sonderregeln (Abbruch nach zwei Null-Geboten, Mittelwert bei K0) exakt umgesetzt sind, ist im Abgleich zu prüfen, bevor Zahlen veröffentlicht werden.
- **Nutzen:** (a) Gegenprüfung unserer Kette: aus dem Massive-Snapshot für SPY die modellfreie Varianz rechnen und mit `^VIX` vergleichen — ein großer Abstand zeigt Probleme in Preisqualität oder Spot. (b) VRP: die Literatur definiert die Varianzrisikoprämie über die modellfreie implizite Varianz, nicht die ATM-IV; die ATM-IV unterschätzt die Varianz bei steilem Skew systematisch. Eine zweite VRP-Spalte (modellfrei) neben der heutigen würde die zurückgestellte VRP-Nachrechnung methodisch einordnen.
- **Grenze:** Bei Einzelaktien mit wenigen gehandelten OTM-Strikes wird die modellfreie Varianz instabil (abgeschnittene Flügel). Nur für Ticker mit dichter Kette ausweisen.
- **Einstufung:** als Gegenprüfung nutzen; Formel selbst schreiben (sie ist kurz) und den Code nur zum Abgleich lesen.

### 3. Sagt GEX etwas voraus? — marcusdrewry/gex-forward-returns

- **URL / Lizenz:** https://github.com/marcusdrewry/gex-forward-returns · keine Lizenz · 1 Stern · Push 2026-06-05.
- **Rechnung:** prädiktive Regressionen log-Rendite (1, 5, 21 Tage) auf GEX; Newey-West mit maxlags ≈ 1,5·h; GEX als rollierender 252-Tage-z-Score (nur Vergangenheit); Kontrollen log VIX, 21-Tage-RV, 21/252-Tage-Momentum, Kurs/200-Tage-Linie, DIX; Quintile mit Folgerendite und Folgevola; Teilperioden 2011–2018 / 2019–2026.
- **Ergebnis (laut Bericht im Repo, n = 3 796 Tage):** univariat 21 Tage t = −2,05, R² ≈ 1 %; mit Kontrollen +0,24 %/SD, t = +1,09; GEX allein sagt 21-Tage-RV voraus (t = −4,2), nach VIX/RV nicht mehr (t = 1,2). Teilperiode 2019–2026 nicht signifikant. Stambaugh-Bias wird benannt.
- **Daten:** `https://squeezemetrics.com/monitor/static/DIX.csv` — eine frei abrufbare tägliche Markt-GEX-Reihe ab 2011. Nutzungsbedingungen von SqueezeMetrics nicht geprüft; daher nur intern als Referenz, nicht auf einer Seite weiterverteilen.
- **Nutzen:** Prüfdesign für unseren Markt-Gamma-Index und das Vol-Trigger-Panel. Unsere eigene GEX-Historie ist kurz (Archiv seit 2026); bis sie reicht, kann die SqueezeMetrics-Reihe zeigen, was eine solche Prüfung ergibt, und unsere Seitentexte begrenzen („GEX beschreibt das Volaumfeld, keine Richtung“). Zusätzlich lässt sich unsere SPX/SPY-GEX der letzten Monate gegen die SqueezeMetrics-Werte korrelieren (Vorzeichen, Größenordnung).
- **Einstufung:** als Gegenprüfung nutzen — Design nachbauen, keinen Code übernehmen.

### 4. Börsenkalender — exchange_calendars / pandas_market_calendars

- **URLs / Lizenz:** https://github.com/gerrymanoim/exchange_calendars (Apache-2.0, 680 ★, Push 2026-10-12) · https://github.com/rsheftel/pandas_market_calendars (MIT, 1003 ★, Push 2026-10-05).
- **Inhalt:** Sitzungen, Öffnungs-/Schlusszeiten in UTC, Mittagspausen (Asien), Frühschlüsse; XNYS, XETR, XLON, XTKS, XHKG, XKRX u. a.; pandas_market_calendars spiegelt diese und ergänzt CME/CBOE-Futureskalender.
- **Nutzen:** Ein dritter, unabhängiger Abgleich für `verify_sitzungen.py`/`verify_boersenereignisse.py` — besonders für die offenen **LSE-Halbtage** (24./31.12.) und die Börsen, die bei uns `ungeprueft` sind. Ein Abweichungsbericht je Börse und Jahr wäre in einem Nachmittag gebaut (nur Lesen der Bibliothek, kein Einbau in die Produktion).
- **Vorsicht:** Auch diese Bibliotheken sind von Hand gepflegt und waren in der Vergangenheit fehlerhaft (die Issues zeigen Korrekturen zu Sonderschließungen). Unsere belegten Fälle (XETRA 24./31.12. 2002–2010, Pfingstmontag/3. Oktober-Ausnahmen, TSE 2020-10-01, NYSE 1972–1994) gehen vor; eine Abweichung ist ein Prüfauftrag, kein Fehlerbeweis. Dieselbe Regel wie bei unseren Zwillingen: Übereinstimmung zweier Kalender beweist nichts, wenn beide derselben falschen Quelle folgen.
- **Einstufung:** als Gegenprüfung nutzen.

### 5. Vanna/Charm-Konventionen — aaguiar10/gflows

- **URL / Lizenz:** https://github.com/aaguiar10/gflows · MIT · 115 ★ · Push 2025-10-02.
- **Rechnung (aus `modules/calc.py`, `modules/stats.py`):** GEX = Γ · OI · S² (Puts mit −1); Vanna-Exposure = −e^{−qT} · φ(d1) · d2/σ · OI · S · σ (für Calls und Puts gleich), Netto = Call − Put; Charm mit voller Formel inkl. r und q, skaliert mit `· S · T`; Zins je Laufzeit aus der Treasury-Kurve (FRED → Yahoo → 3 %); q = 0; für 0/1 DTE das Volumen statt Open Interest; Flip als Nullstelle eines Profils über 300 Kursniveaus zwischen 0,5·S und 1,5·S.
- **Nutzen:** Für den offenen Posten „Vanna FlashAlpha −27,7 Mrd gegen unsere +3,7 Mrd“ zeigt gflows, wie weit Konventionen auseinandergehen: Vorzeichen der Put-Seite (Netto = Call − Put), Skalierung je Vol-Punkt oder je 1 % Vol, Einheit von Charm (je Tag oder über die Restlaufzeit). Vor einem Abgleich mit einem Anbieter alle drei Konventionen festschreiben. Zweiter Punkt: laufzeitgerechter Zins statt fester Wert — bei kurzen Laufzeiten unkritisch, bei 90-Tage-Skew messbar.
- **Volumen statt OI bei 0 DTE:** Begründung im Code („Vortagesvolumen = Positionierung in den Verfallstag“) ist eine Behauptung, nicht belegt; Volumen enthält Eröffnungen und Schließungen. Nur als Idee notieren.
- **Einstufung:** als Gegenprüfung nutzen.

### 6. COT-Abruf — NDelventhal/cot_reports

- **URL / Lizenz:** https://github.com/NDelventhal/cot_reports · MIT · 198 ★ · Push 2024-04-06 (ruhig, aber die CFTC-Dateiformate ändern sich selten).
- **Inhalt:** Legacy, Disaggregated, Traders in Financial Futures, jeweils Futures-only und kombiniert; Jahres- und Historiendateien der CFTC.
- **Nutzen:** Die Larry-Williams-Kandidaten in unserer TODO-Liste (COT Commercials, Legacy-Bericht) und eine breitere CTA-Gegenprobe (Managed Money über mehrere Märkte) brauchen genau diese Berichte. Ob wir die Bibliothek einbauen oder unseren bestehenden Abruf erweitern, hängt davon ab, was `build_cot_positioning.py` heute lädt.
- **Einstufung:** übernehmen (oder als Vorbild für den eigenen Abruf).

### 7. VIX-Termstruktur — dougransom/vix_utils

- **URL / Lizenz:** https://github.com/dougransom/vix_utils · MIT · 64 ★ · Push 2026-04-09.
- **Inhalt:** lädt Cboe-VIX-Futures-Historie je Kontrakt und die Kassa-Indizes (VIX, VIX9D, VIX3M …), baut eine 30-Tage-Konstantlaufzeit aus den vorderen zwei Kontrakten; benennt fehlende Tage in den Cboe-Dateien (2006-11-10, 2007-01-03, 2021-04-02, 2021-12-24).
- **Nutzen:** Für „Opening-Setup Stufe 3: Vola-Lage“ (Kassa-Termstruktur VIX9D/VIX/VIX3M liegt in der DB; Futures-Basis fehlt). Die VX-Kontraktdateien von Cboe nutzen wir bereits als Beleg in `shared/produkttermine_listung.py` — dieselbe Quelle, also keine neue Abhängigkeit. Die Liste fehlender Tage ist ein brauchbarer Prüfpunkt.
- **Einstufung:** übernehmen (Pipeline-Vorbild).

### 8. GEX-Levels mit festgeschriebener Methodik — itsfabtrading/Gex-Multi

- **URL / Lizenz:** https://github.com/itsfabtrading/Gex-Multi · Apache-2.0 · 7 ★ · Push 2026-08-04.
- **Inhalt:** Flip (interpolierte Nullstelle nahe Spot), Call/Put-Wall (`idxmax`/`idxmin` des Netto-Gammas), „Magnet“ = Strike mit größtem Brutto-Gamma (Call + |Put|), 0DTE-Unterlevels, implizite 1-Tages-Spanne, Historie in SQLite. **T-Untergrenze 1/262**, weil BS-Gamma am Geld für T → 0 explodiert und sonst Walls und Magnet auf den Spot springen.
- **Nutzen:** Zwei konkrete Prüfpunkte für `compute_gamma_exposure.py`: (a) Haben wir eine T-Untergrenze für den Verfallstag? (b) Das Brutto-Gamma-Maximum ist eine Kennzahl, die wir nicht zeigen und die bei großen Positionen auf beiden Seiten eines runden Strikes vom Netto-Wall abweicht. Die README begründet gut, warum eine Methodik mit Versionsstand gespeichert werden muss — deckt sich mit unserer Praxis.
- **Einstufung:** als Gegenprüfung nutzen.

### 9. SVI-Fit — XanderRobbins/Arbitrage-Free-Volatility-Surface

- **URL / Lizenz:** https://github.com/XanderRobbins/Arbitrage-Free-Volatility-Surface · MIT · 12 ★ · Push 2026-05-14.
- **Inhalt:** IV-Inversion (Jäckel-Startwert, Newton, Brent-Rückfall), statische Arbitrageprüfungen (Parität, Butterfly, Kalender), Raw-SVI je Laufzeit, Heston über COS.
- **Bewertung:** Die README listet als „No-arbitrage conditions“ nur Parametergrenzen (b ≥ 0, |ρ| < 1, Mindestvarianz ≥ 0, Lee-Schranke). Das reicht für Butterfly-Arbitragefreiheit nicht — dafür braucht es die Dichtebedingung g(k) ≥ 0 nach Gatheral/Jacquier; ob der Code sie prüft, wäre vor einer Übernahme nachzulesen. Kalenderarbitrage über Laufzeiten ist mit Raw-SVI je Schnitt nicht garantiert (SSVI löst das, siehe JackJacquier/SSVI — ohne Lizenz).
- **Nutzen:** Der offene Posten „25Δ-IV interpolieren statt den nächsten Strike nehmen“ ließe sich mit einem SVI-Schnitt je Laufzeit lösen (stetige IV über Moneyness → 25Δ exakt). Ebenso eine geglättete IV-Surface statt der Rasterheatmap.
- **Einstufung:** als Gegenprüfung nutzen; bei Übernahme selbst die g(k)-Prüfung ergänzen.

### 10. Statistikhülle — LuxAlgo/edge-stats

- **URL / Lizenz:** https://github.com/LuxAlgo/edge-stats · MIT · 135 ★ · Push 2026-09-24 (TypeScript, DuckDB).
- **Inhalt:** Jede Abfrage liefert Schätzer, N, 95-%-Konfidenzintervall, Vergleich erste/zweite Hälfte („halves agree“), Werte je Jahr und den Satz „Historical conditional frequencies with sample sizes. Not predictions“. Zielt auf Intraday-Bars (Gap-Fill usw.), die wir nicht haben.
- **Nutzen:** Kein Code für uns, aber ein gutes Muster für die Ausgabe unserer Kalenderstatistiken (TDOM, Wochentag, Feiertage): Fallzahl, Intervall und Hälftenstabilität an jede Trefferquote. Das entspricht unseren Regeln („Fallzahl an jede Zahl“) und wäre eine einheitliche Darstellung über die Seiten.
- **Einstufung:** nur Idee (Ergebnis-Hülle).

---

## Was wir nicht übernehmen und warum

- **paappraiser/almanac-trading-strategies** — keine Lizenz. Die Kopfzahlen („Bull days +16,2 % p. a.“) sind ein In-Sample-Split; die eigene Walk-forward-Tabelle zeigt SPY +6,5 % gegen +14,1 % Buy & Hold. Behauptungen wie „Pre-Holiday: 10× normal returns“ oder „January Barometer: 90 %“ stehen ohne Fallzahl und Test. Das Repo erklärt die Unterrendite zur „Risikoreduktion“ — nach der Optimierung der Gewichte auf denselben Fenstern ist das nicht belastbar.
- **lieblm/thanksgiving-alpha** — Survivorship: heutige Indexmitglieder werden bis 2000 zurück ausgewertet, dazu eine Auswahl „nach Datenqualität“. Positiv ist die FDR-Korrektur (10 von 374 Titeln signifikant); die Einzeltitel-Treffer (UNH) sind trotzdem Datenschürfen. Lizenz NOASSERTION.
- **Matteo-Ferrara/gex-tracker, jensolson/SPX-Gamma-Exposure** — keine Lizenz; methodisch der naive Standard (Händler long Calls, short Puts), den wir schon haben. Matteo-Ferrara verliert zudem Nachkommastrikes beim Parsen.
- **gammagrid/gammagrid** — AGPL-3.0 (Übernahme würde die Offenlegungspflicht für den ganzen Dienst auslösen), inhaltlich deckungsgleich mit unserem Bestand; zugleich Vertriebsweg für eine gehostete Version.
- **FlashAlpha-lab/gex-explained, FlashAlpha-lab/0dte-options-analytics** — MIT, aber Werbe-Repos eines Datenanbieters; Inhalt ist die Standardformel. Nicht schädlich, bringt nichts Neues.
- **puneet-chandna/0DTE-dealer-gamma, EzOptions, EzOptions-Schwab, NineLooms/*** — Echtzeit/Intraday (wir haben keine Tickdaten), dazu keine, GPL- oder kommerzielle Lizenz.
- **YichengYang-Ethan/vol-regime-toolkit** — gibt „SELL“-Signale aus IV-Perzentil und IV−RV ohne jeden Test; genau die Art Aussage, die wir auf `/skew` bewusst vermeiden.
- **kianjagtiani/QuantSC-Capstone** — Leihkosten auf Short-LETFs ignoriert (von den Autoren selbst als größte Lücke benannt), Raster in-sample. Thema ist Volatilitätszerfall, nicht Rebalancing-Flows.
- **isaergun/etf-flows-data** — keine Lizenz, Herkunft der Anteilsdaten nicht dokumentiert.
- **Risk-Parity-/Vol-Targeting-Studentenprojekte, Dispersions-Repos mit 0 Sternen** — Portfoliokonstruktion statt Flow-Schätzung bzw. ohne nachvollziehbare Datenbasis; mehrere tragen erkennbar generierte Marketingformeln („institutional-grade“, „production-ready“) ohne Tests.
- **handiko, Ryan-Childs-1, brian-m0k, aandres99, WinstonZhuang, quantgalore, eigenquant53, asad70, dhawalc** — trivial, In-Sample ohne Kosten, nur Ankündigung oder ohne Lizenz; unser Bestand ist jeweils weiter.
- **pst-group/pysystemtrade** — fachlich die beste Quelle für Trendfolge, Carry und Vola-Targeting, aber GPL-3.0: Methode nach Carvers Büchern selbst umsetzen, keinen Code kopieren.
- **JackJacquier/SSVI, wangys96/SVI** — keine Lizenz; SSVI nach dem Paper (Gatheral/Jacquier 2014) selbst umsetzen, falls die Surface geglättet werden soll.

---

## Geprüfte Repositories (35)

exchange_calendars · pandas_market_calendars · LuxAlgo/edge-stats · almanac-trading-strategies ·
thanksgiving-alpha · weekend_effect · Stock-Traders-Almanac-Notebooks · Monthly-Seasonality-Backtest ·
Futures-Cyclicality-Seasonality-Analyzer · US-Election-Stock-Trend-Analysis · SP500-Studies ·
markets-dashboard · CTA-Position-Monitoring · TinyCTA · pysystemtrade · cot_reports · pycot ·
etf-flows-data · QuantSC-Capstone · implied-correlation-dispersion · gflows · quant-trading (VIX
Calculator) · gex-forward-returns · Gex-Multi · gammagrid · gex-explained · SPX-Gamma-Exposure ·
gex-tracker · EzOptions (+ Schwab) · 0DTE-dealer-gamma · Arbitrage-Free-Volatility-Surface · SSVI ·
vollib/py_vollib (+ vectorized) · vix_utils · vol-regime-toolkit · spx-vol-engine · VRP ·
Options-Max-Pain-Calculator · spx-gamma-levels.

Nächste sinnvolle Schritte (Vorschlag, nicht beauftragt): (1) Kestner-Replikation mit
`expanding`-Skalierung auf ETF-/Kassa-Stellvertretern als Prototyp neben dem heutigen CTA-Proxy,
Abgleich gegen COT; (2) modellfreie 30-Tage-Varianz für SPY gegen `^VIX`; (3) Kalender-
Abweichungsbericht gegen exchange_calendars für LSE und die `ungeprueft`-Börsen; (4) Prüfung
„sagt unser Markt-Gamma-Index etwas voraus“ nach dem Design von gex-forward-returns, sobald die
eigene Historie reicht (vorher auf der SqueezeMetrics-Reihe intern).

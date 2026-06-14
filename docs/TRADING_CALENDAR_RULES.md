# Handels-Kalender-Regeln — SeasonAlpha

> **Zweck:** Verbindliche Spezifikation der Zeit-/Kalender-Logik (Handelstage,
> Feiertage, TDOM/TDOY, OPEX, VIXpiration). Gedacht als **Prüf-Spec für einen
> Verifikations-Agenten**: jede Regel ist so formuliert, dass sie gegen die
> Implementierung (Backend `shared/`, Frontend `landing/js/holidays.js`) und
> gegen die realen Yahoo-/DB-Daten automatisch geprüft werden kann.
>
> Stand: 2026-06-14 (nach Kalender-Bereinigung: 771 → 9 Geister-Lücken).

## Quell-Dateien (Implementierung)

| Schicht | Datei | Rolle |
|---|---|---|
| Backend Kalender | `shared/exchange_holidays.py` | `is_trading_day(date, exchange)`, je Börse eine `_compute_*_holidays(year)` |
| Backend NYSE | `shared/nyse_holidays.py` | US-Feiertage inkl. einmaliger Sonderschließungen |
| Backend Mapping | `shared/symbols.py` | `get_holiday_calendar(ticker)` → `get_exchange_for_holidays(ticker)` |
| Backend TDOM/TDOY | `scripts/backfill_tdoy.py` | `compute_tdoy_tdom(dates, exchange)` → Spalten `prices.tdom/tdoy` |
| Frontend Kalender | `landing/js/holidays.js` | `SA.holidays.detect/isTradingDay/nthTradingDay` |
| Frontend OPEX/Events | `landing/pages/dashboard.html` | `_adjOpex()`, Event-Sort |
| Verifikation | `scripts/check_db_completeness.py --dim gaps` | vergleicht `is_trading_day` gegen reale DB-Tage |

---

## Regel 1 — Feiertage & Kalender-Auflösung (Ticker → Handelsplatz → Kalender)

**Grundsatz:** Der Feiertagskalender eines Tickers folgt dem **tatsächlichen
Handels-/Notierungsplatz** (wo die Yahoo-Kursreihe gehandelt wird) — **NICHT
dem Heimatland des Unternehmens.** Der **Ticker-Suffix** ist die Wahrheit.

> ⚠️ **Kern-Lektion (ADR-Falle):** `AZN`, `BP`, `ASML`, `LIN`, `NVS`, `UBS`,
> `EQNR`, `NVO` sind US-gelistete **ADRs** ausländischer Unternehmen. Ihre
> Kursreihe folgt dem **US-Handelskalender (NYSE)**, obwohl das Unternehmen in
> London/Paris/Zürich/Frankfurt beheimatet ist. Würde man den Kalender aus dem
> Heimatland ableiten, ergäben sich falsche Geister-Lücken UND falsche
> TDOM/TDOY-Werte. → kein Suffix = US-gelistet.

### Auflösungs-Algorithmus (`get_holiday_calendar` in `symbols.py`)

```
ticker (UPPER)
  endet auf "-USD"   → CRYPTO   (24/7, siehe Regel 2)
  endet auf "=X"     → FOREX    (Mo-Fr, siehe Regel 3)
  beginnt mit "^"  ODER enthält "." ODER endet auf "=F"
                     → SYMBOLS[ticker].exchange → EXCHANGE_TO_HOLIDAY → Code
  sonst (kein Suffix)→ US        (US-Aktie/ETF + ausländische ADRs)
```
Danach: Code → `HOLIDAY_TO_EXCHANGE` → Börsen-Kürzel → `is_trading_day(d, kürzel)`.

### Suffix → Handelsplatz → Kalender

| Suffix / Muster | Beispiel | Börse (Kalender) | Code |
|---|---|---|---|
| kein Suffix | AAPL, AZN, BP, LIN | NYSE/NASDAQ | `NYSE` |
| `.DE`, `.F` | SAP.DE, RHM.F | XETRA (Frankfurt) | `XETRA` |
| `.PA`, `.AS`, `.BR` | MC.PA, PRX.AS | Euronext (Paris/Amsterdam/Brüssel) | `EURONEXT` |
| `.MI` | ENEL.MI | Borsa Italiana (Mailand) | `MILAN` |
| `.MC` | IBE.MC | BME Madrid → **Euronext-Näherung** (TODO eigener Kalender) | `EURONEXT` |
| `.L` | RR.L | LSE (London) | `LSE` |
| `.SW` | NESN.SW | SIX (Schweiz) | `SIX` |
| `.ST` | VOLV-A.ST | Nasdaq Stockholm | `STOCKHOLM` |
| `=X` | EURUSD=X | Devisen | `FOREX` |
| `-USD` | BTC-USD | Krypto | `CRYPTO` |
| `=F` | GC=F, CL=F | Futures → US-Settlement-Kalender | `NYSE` |
| `^…` Index | ^GDAXI→XETRA, ^FTSE→LSE, ^N225→TSE, ^FCHI→EURONEXT, ^SSMI→SIX | via `SYMBOLS.exchange` | div. |

### Implementierte Börsenkalender (`exchange_holidays.py`)

- **NYSE/NASDAQ** — Neujahr, MLK (3. Mo Jan, ab 1998), Presidents' Day (3. Mo Feb),
  Karfreitag, Memorial Day (letzter Mo Mai), Juneteenth (19.6., ab 2022),
  Independence Day (4.7.), Labor Day (1. Mo Sep), Thanksgiving (4. Do Nov),
  Christmas (25.12.). **Beobachtungsregel:** Sa→Fr, So→Mo.
  **+ Einmalige Sonderschließungen** (`_NYSE_SPECIAL_CLOSURES`): 09.01.2025
  (Staatstrauer Carter), 05.12.2018 (Bush), 29.+30.10.2012 (Sandy), 02.01.2007
  (Ford), 11.06.2004 (Reagan), 11.–14.09.2001 (9/11).
- **XETRA** — Neujahr, Karfreitag, Ostermontag, 1. Mai, Pfingstmontag,
  3. Oktober, **24.12. + 31.12. (ganztägig zu, seit 2011)**, 25.+26.12.
  *Nicht* geschlossen: Christi Himmelfahrt.
- **EURONEXT** (Paris/Amsterdam/Brüssel/Lissabon) — **NUR 6 Tage:** Neujahr,
  Karfreitag, Ostermontag, 1. Mai, 25.+26.12. Euronext handelt **durch** an
  Pfingstmontag, Himmelfahrt, 8. Mai, 14. Juli, 15. Aug, 1. Nov, 11. Nov.
- **MILAN** (Borsa Italiana) — Euronext-Kern **+ Ferragosto (15.8.) + 24.12. + 31.12.**
  Andere ital. Feiertage (6.1./25.4./2.6./8.12.) handelt Mailand durch.
- **LSE** (London) — Neujahr, Karfreitag, Ostermontag, Early May BH (1. Mo Mai),
  Spring BH (letzter Mo Mai), Summer BH (letzter Mo Aug), Christmas, Boxing Day
  (mit Substitute-Regeln); Sonderfälle Jubilees 2002/2012/2022, Queen-Beerdigung
  2022, Krönung 2023.
- **SIX** (Schweiz) — Neujahr, Berchtoldstag (2.1.), Karfreitag, Ostermontag,
  1. Mai, **Christi Himmelfahrt (schließt!)**, Pfingstmontag, Bundesfeier (1.8.),
  **24.12. + 31.12. (ganztägig zu)**, 25.+26.12.
- **STOCKHOLM** — Neujahr, Heilige Drei Könige (6.1.), Karfreitag, Ostermontag,
  1. Mai, Christi Himmelfahrt, Nationaltag (6.6.), Midsommarafton, Heiligabend,
  25.+26.12., Silvester.
- **TSE** (Tokyo) — japanische Nationalfeiertage + 2./3. Jan + 31.12.,
  Beobachtungsregel So→Mo. *Bekannte Lücke:* Substitute-Kaskade (z.B. 6.5.) nicht
  modelliert.
- **FOREX** — keine Feiertage (nur Mo-Fr).
- **CRYPTO** — keine Feiertage, kein Wochenende (immer offen).
- **FEHLEND (TODO):** HKEX (`^HSI`), KRX (`^KS11`) — komplexe Mondkalender-Feiertage;
  aktuell Näherung über TSE → bekannte Geister-Lücken, im Audit exemptiert.

### „Keine Zählung als TDOM"
Feiertage **und** Wochenenden sind keine Handelstage → werden in TDOM/TDOY nicht
mitgezählt (siehe Regel 4/6).

### Neuer Ticker aus neuem Land — Checkliste
1. Suffix in `get_holiday_calendar` (`symbols.py`) auf einen Code abbilden.
2. Falls neuer Handelsplatz: `_compute_<börse>_holidays(year)` in
   `exchange_holidays.py` anlegen + in `_EXCHANGE_FUNCTIONS` registrieren +
   `EXCHANGE_TO_HOLIDAY`/`HOLIDAY_TO_EXCHANGE` ergänzen.
3. **Frontend spiegeln:** `SA.holidays.detect()` in `landing/js/holidays.js` muss
   denselben Kalender liefern (sonst Frontend-Anzeige ≠ DB).
4. `py scripts/backfill_tdoy.py --ticker <T>` neu rechnen.
5. `py scripts/check_db_completeness.py --dim gaps` → 0 echte Lücken erwarten.

---

## Regel 2 — Krypto handelt 24/7

`-USD`-Ticker (BTC-USD, ETH-USD, SOL-USD, XRP-USD, ADA-USD, DOGE-USD):
`is_trading_day` ist **immer True**, inklusive Samstag/Sonntag/Feiertag. TDOM/TDOY
zählen **alle Kalendertage**. (Backend-Code `CRYPTO`, Frontend `NONE`.)

---

## Regel 3 — Forex handelt Sonntagnacht bis Freitagnacht

`=X`-Ticker: Markt offen **Sonntag ~23:00 (CET) bis Freitag ~23:00 (CET)**. Auf
**Tagesbasis** = Handelstage **Mo–Fr, keine Feiertage** (`FOREX`-Kalender leer);
Sa/So kein Handel. *Hinweis:* Yahoos `=X`-Tagesreihen haben sporadische
Daten-Ausfälle (Datenqualität, kein Kalenderdefekt) → im Gap-Audit exemptiert.

---

## Regel 4–6 — Zeit-Indizes: TDOM · CDOM · TDOY · CDOY

Vier orthogonale Tages-Indizes (Handelstag **T** vs. Kalendertag **C**) × (Monat
**M** vs. Jahr **Y**). **T-Indizes** überspringen Wochenenden + Feiertage und sind
**börsenspezifisch**; **C-Indizes** zählen jeden Kalendertag und sind börsen-
unabhängig.

| Index | Voll | Definition | Bereich | Reset | börsen-spez.? | Quelle |
|---|---|---|---|---|---|---|
| **TDOM** | Trading Day of Month | n-ter **Handelstag** im Monat | 1 – ~23 | Monatsanfang | **ja** | `prices.tdom` |
| **CDOM** | Calendar Day of Month | Kalendertag im Monat | 1 – 31 | Monatsanfang | nein | `date.day` |
| **TDOY** | Trading Day of Year | n-ter **Handelstag** im Jahr | 1 – ~250–256 | Jahresanfang | **ja** | `prices.tdoy` |
| **CDOY** | Calendar Day of Year | Kalendertag im Jahr | 1 – 365 (366) | Jahresanfang | nein | `day_of_year` / `tm_yday` |

### Regel 4 — TDOM (Trading Day of Month)
Fortlaufende Nummer des **Handelstags innerhalb des Monats**. Erster Handelstag =
**TDOM 1**, Reset zum Monatsersten. Gezählt wird nur, wenn die zuständige Börse
offen ist (= Kurs bei Yahoo). **Ausnahme:** Feiertage + Wochenenden zählen nicht.
- **Börsenspezifisch:** am selben Datum kann `^GSPC` TDOM 7, `^GDAXI` TDOM 6 haben
  (XETRA-Feiertage abweichend). → `render_trading_day_header(df, ticker=ticker)`.
- **Frontend:** TDOM IMMER aus dem **Holiday-Kalender** berechnen
  (`SA.holidays.nthTradingDay`), nie aus dem letzten DB-Row ableiten (DB kann vor
  dem Intraday-Refresh veraltet sein → TDOM−1).

### Regel 5 — CDOM (Calendar Day of Month)
Kalendertag des Monats (**1–31**), unabhängig von Handelstagen/Feiertagen/
Wochenenden. Trivial (`date.day`), v.a. für Datumslabels.

### Regel 6 — TDOY (Trading Day of Year)
Fortlaufende Summierung der **Handelstage** ab dem ersten Handelstag im Januar
(= **TDOY 1**) bis zum letzten Handelstag des Jahres (z.B. 31.12. USA, **30.12.
XETRA** — XETRA am 31.12. geschlossen). Reset zum Jahreswechsel. Nur Handelstage,
börsenspezifisch. (Implementierung gemeinsam mit TDOM in
`scripts/backfill_tdoy.py::compute_tdoy_tdom`.)

### Regel 6b — CDOY (Calendar Day of Year)
Kalendertag des Jahres (**1–365**, im Schaltjahr 1–366; `tm_yday`). **Zentrale
Rolle:** CDOY ist die **kanonische x-Achse der normalisierten Saisonalität** —
jedes Jahr wird via `calculations.py::interpolate_to_365` auf ein gemeinsames
**365-Punkte-Raster** interpoliert (Schaltjahre absorbiert, kein Stretching der
Renditen). **TDOY und TDOM werden für Hover + „Heute"-Marker auf diese CDOY-Achse
gemappt** (`charts.py`: `tdoy_map[cdoy]`, `tdom_map[cdoy]`). Merke: Der Saison-Chart
läuft über **CDOY** (jeder Kalendertag hat einen Punkt), die Handelstags-Indizes
(TDOY/TDOM) sind die **kontextuelle Überlagerung**.

> **Konsistenz-Falle:** CDOY/CDOM dürfen NIE über `toISOString()` aus lokalen Daten
> abgeleitet werden (MESZ→UTC verschiebt auf den Vortag) — `localDateStr` nutzen.

---

## Regel 7 — OPEX (Options Expiration) — **börsenspezifisch**

### 7.1 Grundregel
Standard-Optionsverfall = **3. Freitag des Monats**. OPEX ist **kein Kalender-,
sondern ein Börsen-Ereignis** → der relevante Feiertagskalender ist der der
**Options-/Terminbörse**, nicht der des Heimatlands des Basiswerts.

### 7.2 Feiertags-Anpassung (pro Börse unterschiedlich!)
Ist der 3. Freitag an der zuständigen Börse ein **Feiertag**, verschiebt sich der
Verfall (= letzter Handelstag) auf den **vorherigen Handelstag** (rekursiv, falls
auch dieser Feiertag). **Welche Feiertage gelten, hängt von der Börse ab** — und
genau deshalb können US- und DE-OPEX am selben Monatsdritten-Freitag differieren.

### 7.3 US — CBOE / OCC (NYSE-Kalender) · *implementiert*
- Aktien-/Index-Optionen (SPX, SPY, Einzelwerte): 3. Freitag, NYSE-Kalender.
- Im 3.-Freitag-Fenster (15.–21.) können in den USA **nur zwei** Feiertage auf
  einen Freitag fallen: **Good Friday** und **Juneteenth (19.6., seit 2022)**.
- Impl.: `shared/nyse_holidays.py::get_opex_date()` (generisch via
  `is_nyse_holiday`), Frontend `landing/pages/opex.html` + `dashboard.html::_adjOpex()`.

### 7.4 DE — EUREX (XETRA-Kalender) · *spezifiziert, (noch) nicht implementiert*
- DAX-/EURO-STOXX-50-/Einzelwert-Optionen handeln an der **EUREX**; deren
  Handelskalender = **XETRA-Kalender** (Deutsche Börse).
- Verfall ebenfalls **3. Freitag**; Feiertags-Anpassung über den **XETRA**-Kalender.
- DAX-Options-Schlussabrechnung: aus der **Xetra-Intraday-Auktion** (~13:00 MEZ)
  des 3. Freitags.
- Im 3.-Freitag-Fenster kann in DE **nur Good Friday** auf einen Freitag fallen
  (Mai 1/Oct 3/24./31.12. liegen außerhalb des 15.–21.-Fensters, Himmelfahrt/
  Pfingstmontag sind Do/Mo). → DE verschiebt OPEX **ausschließlich** an Good Friday.

### 7.5 Divergenz US ↔ DE (Kernpunkt)
Da **Good Friday beide** Börsen schließt (→ beide auf Do verschoben, **keine**
Divergenz), bleibt als **einzige** Divergenzquelle **Juneteenth** (US-Feiertag,
in DE normaler Handelstag):

| Monat | 3. Freitag | US (CBOE/NYSE) | DE (EUREX/XETRA) | Divergenz? |
|---|---|---|---|---|
| 2025-04 | 18.04. = Good Friday | → Do **17.04.** | → Do **17.04.** | nein (beide zu) |
| 2026-06 | 19.06. = Juneteenth | → Do **18.06.** | Fr **19.06.** (XETRA offen) | **ja** |
| Normalmonat | z.B. 20.03.2026 | Fr 20.03. | Fr 20.03. | nein |

→ US/DE-OPEX divergieren **nur**, wenn der 3. Freitag = Juneteenth ist (frühestens
ab 2022). Sonst identisch.

### 7.6 Triple / Quadruple Witching
**März / Juni / September / Dezember** (Index-Futures + Index-Optionen +
Aktien-Optionen + Single-Stock-Futures verfallen gleichzeitig) — gilt analog für
CBOE und EUREX.

---

## Regel 8 — VIXpiration (Volatilitäts-Settlement) — **börsenspezifisch**

### 8.1 VIX — CBOE (NYSE-Kalender) · *implementiert*
CBOE-Regel (wörtlich): Final Settlement = **der Mittwoch, der 30 Kalendertage vor
dem 3. Freitag des FOLGEMONATS liegt** (= der Mittwoch 30 Tage vor dem SPX-Verfall,
auf den sich der VIX bezieht). In dieser Spec referenziert über den
SPX-Verfallsfreitag: **VIX-Settlement(Referenz-Fr) = Referenz-3.-Freitag − 30
Kalendertage** (= i.d.R. **Mittwoch im Vormonat**).

### 8.2 Feiertags-Regel (NYSE)
Ist **der Referenz-3.-Freitag ODER der Settlement-Mittwoch** ein NYSE-Feiertag →
Settlement **einen Handelstag früher** (= Dienstag; rekursiv). **Letzter
Handelstag** der VIX-Kontrakte = **Dienstag vor dem Settlement-Mittwoch**.

> Wichtig: Es zählt auch der **Referenz-Freitag** (liegt einen Monat *nach* dem
> Settlement). Beispiele:
> - **04/2025** (Referenz 18.04. = Good Friday): 18.04.−30 = Mi 19.03. → da
>   Referenz-Fr Feiertag → **Di 18.03.**
> - **06/2026** (Referenz 19.06. = Juneteenth): 19.06.−30 = Mi 20.05. → da
>   Referenz-Fr Feiertag → **Di 19.05.**
>
> Impl.: `landing/pages/vixpiration.html::getVixpirationDateStr()` (NYSE-Kalender).

### 8.3 VSTOXX / V2X — EUREX (Euronext-/EUREX-Kalender) · *Analog, nicht getrackt*
Europäisches Pendant zum VIX (Volatilität des EURO STOXX 50). Settlement-Logik
analog: **30 Tage vor dem EURO-STOXX-50-Optionsverfall** (3. Freitag), Feiertags-
Anpassung über den **EUREX/Euronext-Kalender** statt NYSE. → kann vom VIX
abweichen, wenn ein US-Feiertag (z.B. Juneteenth) den VIX-Referenz-Freitag
verschiebt, den europäischen aber nicht (und umgekehrt). SeasonAlpha trackt
VSTOXX derzeit **nicht** (kein `^V2X`-Ticker) — hier nur zur Vollständigkeit.

---

## Regel 9 — Events: nationale Feiertage + Notenbank-Sitzungen

### 9.1 Nationale Feiertage sind **ticker-/börsenspezifisch**
Feiertage sind **national** und gelten nur für die Börse des jeweiligen Tickers
(= Auflösung wie Regel 1). Der DAX (`^GDAXI`, XETRA) ruht z.B. am **1. Mai** und
**3. Oktober**, der S&P 500 (NYSE) nicht; umgekehrt handelt XETRA an Thanksgiving.
→ In der Event-/Kalender-Anzeige eines Tickers **nur die Feiertage seiner Börse**
zeigen (`market_calendar.populate_holidays` erzeugt pro Börse getrennte Rows mit
`exchange`-Tag; `get_events(exchanges=[...])` filtert). Beispiel-Divergenzen siehe
Regel-1-Kalenderliste (XETRA 1.5./3.10./Pfingstmontag/24.+31.12.; Euronext nur
6 Tage; SIX Bundesfeier 1.8. + Christi Himmelfahrt; Stockholm Midsommar etc.).

### 9.2 Notenbank-Sitzungen sind **regions-/währungsspezifisch**

**Verlinkung Ticker → Notenbank** folgt dem **Handelsplatz / der Handelswährung**
(wie der Feiertagskalender, Regel 1) — **NICHT** der Heimatwährung. Beispiel: `NVO`
ist ein US-ADR (`SYMBOLS["währung"]="DKK"`), wird aber als USD an der NYSE gehandelt
→ **Fed**. Implementierung: `central_banks.central_banks_for_ticker(ticker)`:
- **FX (`=X`):** beide Paar-Währungen → beide Notenbanken (z.B. `AUDUSD=X` → RBA+Fed).
- **Krypto (`-USD`):** keine.
- **sonst:** `get_exchange_for_holidays(ticker)` → Börse → Notenbank.

| Region / Währung | Notenbank | Quelle | Datenquelle im Code | Termine bis |
|---|---|---|---|---|
| USA / USD (auch ADRs, Futures) | **Fed (FOMC)** | federalreserve.gov | `fed_dates.py::FOMC_MEETING_DATES` | **2028-01** ✓ |
| Eurozone / EUR (DE, FR, IT, ES, NL) | **EZB / ECB** | ecb.europa.eu | `ECB_MEETING_DATES` | **2027** ✓ |
| UK / GBP (`.L`) | **BoE (MPC)** | bankofengland.co.uk | `BOE_MEETING_DATES` | **2027** ✓ |
| Japan / JPY (`.T`, `^N225`) | **BoJ** | boj.or.jp | `BOJ_MEETING_DATES` | **2026** ✓ |
| Schweiz / CHF (`.SW`, `^SSMI`) | **SNB** | snb.ch | `SNB_MEETING_DATES` | **2026-06** ⚠ (Sep/Dez TODO) |
| Kanada / CAD (`USDCAD=X`) | **BoC** | bankofcanada.ca | `BOC_MEETING_DATES` | **2026** ✓ |
| Australien / AUD (`AUDUSD=X`) | **RBA** | rba.gov.au | `RBA_MEETING_DATES` | **2026** ✓ |
| Neuseeland / NZD (`NZDUSD=X`) | **RBNZ** | rbnz.govt.nz | `RBNZ_MEETING_DATES` | **2026** ✓ |
| China / CNY | **PBoC** | pbc.gov.cn | — (monatl. LPR, ~20.) | **fehlt (TODO)** |
| Schweden / SEK (`.ST`) | **Riksbank** | riksbank.se | — | **fehlt (TODO)** |
| Norwegen / NOK | **Norges Bank** | norges-bank.no | — | **fehlt (TODO)** |
| Dänemark / DKK | **Nationalbanken** | nationalbanken.dk | — | **fehlt (TODO)** |
| Hongkong / HKD (`^HSI`) | **HKMA** (USD-Peg → folgt Fed) | hkma.gov.hk | — | **fehlt (TODO)** |
| Südkorea / KRW (`^KS11`) | **BoK** | bok.or.kr | — | **fehlt (TODO)** |

**Konventionen:**
- Gespeichertes Datum = **Entscheidungs-/Bekanntgabetag** (bei zweitägigen
  Sitzungen der **2. Tag**: FOMC/BoJ/RBA Tag 2; ECB/BoE der Donnerstag; BoC/RBNZ
  der publizierte Termin).
- **Italien u.a. Eurozonen-Länder haben KEINE eigene geldpolitische Notenbank
  mehr → immer EZB.** „Banca d'Italia" macht keine eigene Zinspolitik.
- **PBoC** hat keinen diskreten Jahres-Sitzungskalender wie die anderen, sondern
  fixt den **LPR monatlich am ~20.** (nächster Werktag bei Feiertag) → regelbasiert,
  daher (noch) nicht als Terminliste gepflegt.
- Im Event-Schema sind CB-Termine mit `exchange="ALL"` + `meta={bank,currency}`
  getaggt — die Ticker-Zuordnung erfolgt über `meta.currency` bzw.
  `central_banks_for_ticker()`.
- **SNB-Warnung:** Termine folgen KEINEM festen Wochentag (2025: Sep = 4. Do,
  Dez = 2. Do) → Sep/Dez **nicht extrapolieren**, nur offiziell Publiziertes.

**Pflege (`wir brauchen die Termine maximal weit in die Zukunft`):**
Notenbanken publizieren 1–2 Jahre im Voraus. Bei Updates die **offiziellen**
Seiten prüfen, neue Jahre anhängen — **NIE schätzen** (forward-Termine ändern sich;
nur Publiziertes übernehmen; siehe die 2026-Korrekturen, bei denen 5 von 8
ECB/BoJ-Terminen falsch waren). Stand 2026-06-14: Fed→2028-01, ECB/BoE→2027,
BoJ/BoC/RBA/RBNZ→2026, SNB→2026-06.

---

## Verifikation (für den Prüf-Agenten)

**Methode:** Pro Ticker `is_trading_day(d, get_exchange_for_holidays(ticker))` über
ein Zeitfenster gegen die **realen Yahoo-/DB-Handelstage** abgleichen.

- **Erwartet-aber-fehlt** (Börse offen laut Kalender, aber kein Kurs) = Kalender
  schließt zu wenig → potenziell fehlender Feiertag.
- **Hat-aber-zu** (Kurs vorhanden, Kalender sagt geschlossen) = Kalender schließt
  zu viel → falscher Feiertag.

**Referenz-Implementierung:** `scripts/check_db_completeness.py --dim gaps`.

**Bekannte, akzeptierte Rest-Abweichungen (kein Defekt):**
- `=X` (Forex) — Yahoo-Datenqualität → `_gap_exempt()`.
- `^HSI`, `^KS11` — HKEX/KRX-Kalender fehlen (TODO) → `_gap_exempt()`.
- `^STOXX50E` (6 Tage/2J) — Eurex-Frühschluss-Idiosynkrasien.
- `^N225` (6.5.) — japanische Substitute-Holiday-Kaskade nicht modelliert.
- `RR.L` (27.10.2025) — einzelner Yahoo-Daten-Glitch.

**Sollzustand nach Bereinigung 2026-06-14:** 3 Ticker / 9 fehlende HT (advisory),
0 Stale-Ticker. Alle anderen 321 Ticker: 0 Geister-Lücken.

## Offene TODOs (Kalender-Präzision)
- [ ] HKEX-Kalender (`^HSI`) — Chinesisches Neujahr (Mondkalender) etc.
- [ ] KRX-Kalender (`^KS11`) — Seollal/Chuseok (Mondkalender).
- [ ] BME-Madrid-Kalender (`.MC`) — aktuell Euronext-Näherung (Epiphanias 6.1. fehlt).
- [ ] TSE Substitute-Holiday-Kaskade (振替休日) bei Feiertags-Sandwiches.
- [ ] `^STOXX50E` — eigener Eurex-Index-Kalender mit Frühschluss-Tagen.

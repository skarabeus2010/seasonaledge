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

## Regel 4 — TDOM (Trading Day of Month)

Fortlaufende Nummer des Handelstags **innerhalb des Monats**. Erster Handelstag
des Monats = **TDOM 1**, Reset zum Monatsersten. Gezählt wird nur, wenn die
zuständige Börse offen ist (Kurs bei Yahoo vorhanden). **Ausnahme:** Feiertage
und Wochenenden zählen nicht.

**Wichtig (Frontend):** TDOM immer aus dem **Holiday-Kalender** berechnen, nie aus
dem letzten DB-Row ableiten (DB kann vor dem Intraday-Refresh veraltet sein).
TDOM ist **börsenspezifisch** — am selben Datum kann `^GSPC` TDOM 7, `^GDAXI`
TDOM 6 haben (XETRA-Feiertage abweichend).

---

## Regel 5 — CDOM (Calendar Day of Month)

Kalendertag des Monats (1–31), unabhängig von Handelstagen/Feiertagen/Wochenenden.

---

## Regel 6 — TDOY (Trading Day of Year)

Fortlaufende Summierung der Handelstage ab dem **ersten Handelstag im Januar
(= TDOY 1)** bis zum **letzten Handelstag des Jahres** (z.B. 31.12. USA, 30.12.
XETRA — da XETRA am 31.12. geschlossen). Reset zum Jahreswechsel. Nur Handelstage
(Feiertage/Wochenenden ausgenommen), börsenspezifisch.

---

## Regel 7 — OPEX (Options Expiration)

Jeder **3. Freitag im Monat**. Ist dieser 3. Freitag ein **Börsenfeiertag (NYSE)**,
dann OPEX auf den **vorherigen Handelstag** (i.d.R. Donnerstag davor).
**Triple/Quadruple Witching:** März/Juni/September/Dezember.

> Beispiel 2026-06: 3. Freitag = 19.06. = Juneteenth (NYSE zu) → OPEX = 18.06.
> (Frontend: `_adjOpex()` in `dashboard.html`.)

---

## Regel 8 — VIXpiration (VIX-Optionsverfall)

VIX-Settlement = **OPEX-Freitag des Monats − 30 Kalendertage** (= i.d.R. Mittwoch).
Ist der **Basis-OPEX-Freitag ODER der Settlement-Mittwoch** ein NYSE-Feiertag →
**einen Handelstag früher**.

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

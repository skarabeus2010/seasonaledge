# shared/exchange_holidays.py
# Börsenfeiertage für internationale Märkte.
#
# Unterstützte Börsen:
#   NYSE     — US (in nyse_holidays.py, hier als Wrapper)
#   XETRA    — Deutschland (DAX, MDAX, SDAX, TecDAX)
#   LSE      — London (FTSE 100, FTSE 250)
#   EURONEXT — Paris (CAC 40)
#   TSE      — Tokyo (Nikkei 225, TOPIX)
#
# Logik:
#   - Feste Feiertage regelbasiert berechnet
#   - Variable Feiertage (Ostern, Goldene Woche etc.) algorithmisch
#   - Auto-Erweiterung: funktioniert für jedes Jahr ohne Update
#   - Exchange-Zuordnung via Ticker (nutzt SYMBOLS["exchange"])
#
# Import-Beispiel:
#   from shared.exchange_holidays import get_holidays, is_holiday, get_holidays_for_ticker

from datetime import date, timedelta
import calendar
from shared.nyse_holidays import (
    _easter_sunday,
    _good_friday,
    _nth_weekday,
    _observed,
    _monday_if_sunday,
    get_nyse_holidays,
)

# ── Exchange → Ticker Mapping ──────────────────────────────────────────────────
# Wird genutzt um aus einem Ticker die richtige Börse zu ermitteln.
# Ergänze hier neue Ticker wenn nötig.

TICKER_TO_EXCHANGE = {
    # NYSE / NASDAQ
    "NYSE":    ["SPY", "QQQ", "IWM", "DIA", "TLT", "GLD", "SLV", "USO",
                "XLF", "XLK", "XLE", "XLV", "XLU", "AAPL", "MSFT", "NVDA",
                "AMZN", "GOOGL", "META", "TSLA", "JPM", "XOM",
                "^GSPC", "^DJI", "^IXIC", "^NDX", "^RUT", "^VIX",
                "GC=F", "SI=F", "CL=F", "BZ=F", "NG=F", "ZC=F", "ZW=F",
                "ES=F", "NQ=F", "BTC-USD", "ETH-USD", "SOL-USD",
                "EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X"],
    # XETRA (Deutschland)
    "XETRA":  ["^GDAXI", "^MDAXI", "^SDAXI", "^TECDAX"],
    # LSE (London)
    "LSE":    ["^FTSE", "^FTMC"],
    # Euronext Paris
    "EURONEXT": ["^FCHI"],
    # TSE (Tokyo)
    "TSE":    ["^N225", "^TOPX"],
    # SIX (Schweiz) — nutzt NYSE-ähnliche Feiertage + Schweizer Extras
    "SIX":    ["^SSMI"],
    # HKEX
    "HKEX":   ["^HSI"],
    # KRX
    "KRX":    ["^KS11"],
}

# Umgekehrtes Mapping: Ticker → Exchange
_TICKER_MAP = {
    ticker: exchange
    for exchange, tickers in TICKER_TO_EXCHANGE.items()
    for ticker in tickers
}


# ── Gemeinsame Helfer ──────────────────────────────────────────────────────────

def _whit_monday(year: int) -> date:
    """Pfingstmontag = Ostersonntag + 49 Tage."""
    return _easter_sunday(year) + timedelta(days=49)

def _easter_monday(year: int) -> date:
    """Ostermontag = Ostersonntag + 1."""
    return _easter_sunday(year) + timedelta(days=1)

def _ascension_day(year: int) -> date:
    """Christi Himmelfahrt = Ostersonntag + 39 Tage."""
    return _easter_sunday(year) + timedelta(days=39)

def _corpus_christi(year: int) -> date:
    """Fronleichnam = Ostersonntag + 60 Tage."""
    return _easter_sunday(year) + timedelta(days=60)


# ── XETRA (Deutschland) ────────────────────────────────────────────────────────

def _compute_xetra_holidays(year: int) -> list[date]:
    """
    XETRA/Frankfurt Börsenfeiertage.
    Bundesweite Feiertage — Börse Frankfurt ist geschlossen.
    """
    holidays = []

    # Neujahr — 1. Januar
    holidays.append(_monday_if_sunday(date(year, 1, 1)))

    # Karfreitag
    holidays.append(_good_friday(year))

    # Ostermontag
    holidays.append(_easter_monday(year))

    # Tag der Arbeit — 1. Mai
    holidays.append(_monday_if_sunday(date(year, 5, 1)))

    # Christi Himmelfahrt (Donnerstag, 39 Tage nach Ostern)
    # XETRA schließt an diesem Tag NICHT — daher auskommentiert
    # holidays.append(_ascension_day(year))

    # Pfingstmontag
    holidays.append(_whit_monday(year))

    # Tag der deutschen Einheit — 3. Oktober
    holidays.append(_monday_if_sunday(date(year, 10, 3)))

    # Heiligabend — 24. Dezember (halber Tag, aber XETRA schließt früh)
    # Offiziell kein Feiertag, aber Börse schließt um 14:00 Uhr
    # Für OPEX-Zwecke behandeln wir es als normalen Handelstag

    # 1. Weihnachtstag — 25. Dezember
    holidays.append(_observed(date(year, 12, 25)))

    # 2. Weihnachtstag — 26. Dezember
    holidays.append(_observed(date(year, 12, 26)))

    # Silvester — 31. Dezember
    # Kein offizieller Feiertag, Börse schließt aber früh
    # Nicht als geschlossen gewertet

    return sorted(set(holidays))


# ── LSE (London) ───────────────────────────────────────────────────────────────

def _compute_lse_holidays(year: int) -> list[date]:
    """
    LSE London Stock Exchange Feiertage (England & Wales Bank Holidays).
    """
    holidays = []

    # New Year's Day — 1. Januar
    holidays.append(_monday_if_sunday(date(year, 1, 1)))

    # Good Friday
    holidays.append(_good_friday(year))

    # Easter Monday
    holidays.append(_easter_monday(year))

    # Early May Bank Holiday — 1. Montag im Mai
    # Ausnahme: 2020 auf 8. Mai verschoben (VE Day 75th Anniversary)
    if year == 2020:
        holidays.append(date(2020, 5, 8))
    else:
        holidays.append(_nth_weekday(year, 5, 0, 1))

    # Spring Bank Holiday — letzter Montag im Mai
    # Ausnahme: 2002 (Golden Jubilee), 2012 (Diamond Jubilee), 2022 (Platinum Jubilee)
    if year == 2002:
        holidays.append(date(2002, 6, 4))
    elif year == 2012:
        holidays.append(date(2012, 6, 5))
        holidays.append(date(2012, 6, 4))  # Extra Jubilee day
    elif year == 2022:
        holidays.append(date(2022, 6, 2))
        holidays.append(date(2022, 6, 3))  # Extra Jubilee day
    else:
        holidays.append(_nth_weekday(year, 5, 0, -1))

    # Summer Bank Holiday — letzter Montag im August
    holidays.append(_nth_weekday(year, 8, 0, -1))

    # Christmas Day — 25. Dezember
    xmas = date(year, 12, 25)
    if xmas.weekday() == 5:   # Samstag → Montag
        holidays.append(date(year, 12, 27))
    elif xmas.weekday() == 6: # Sonntag → Montag
        holidays.append(date(year, 12, 26))
        holidays.append(date(year, 12, 27))  # Boxing Day auch verschoben
    else:
        holidays.append(xmas)

    # Boxing Day — 26. Dezember
    boxing = date(year, 12, 26)
    if boxing.weekday() == 5:  # Samstag → Dienstag (weil Montag = Xmas observed)
        holidays.append(date(year, 12, 28))
    elif boxing.weekday() == 6: # Sonntag → bereits oben behandelt
        pass
    elif boxing.weekday() == 0 and xmas.weekday() != 6:
        # Wenn Xmas normal Freitag war, Boxing Day = Montag
        holidays.append(boxing)
    else:
        holidays.append(boxing)

    # Sonderfeiertage
    if year == 2022:
        holidays.append(date(2022, 9, 19))  # Queen Elizabeth II Staatsbegräbnis
    if year == 2023:
        holidays.append(date(2023, 5, 8))   # King Charles III Krönung

    return sorted(set(holidays))


# ── Euronext Paris (CAC 40) ────────────────────────────────────────────────────

def _compute_euronext_holidays(year: int) -> list[date]:
    """
    Euronext Paris Börsenfeiertage (französische Feiertage).
    """
    holidays = []

    # Neujahr — 1. Januar
    holidays.append(_monday_if_sunday(date(year, 1, 1)))

    # Karfreitag (Euronext ist geschlossen)
    holidays.append(_good_friday(year))

    # Ostermontag
    holidays.append(_easter_monday(year))

    # Tag der Arbeit — 1. Mai (Fête du Travail) — wichtigster fr. Feiertag
    holidays.append(_monday_if_sunday(date(year, 5, 1)))

    # Tag des Sieges 1945 — 8. Mai
    holidays.append(_monday_if_sunday(date(year, 5, 8)))

    # Himmelfahrt — Euronext Paris schließt NICHT
    # Pfingstmontag
    holidays.append(_whit_monday(year))

    # Nationalfeiertag — 14. Juli (Bastille Day)
    holidays.append(_monday_if_sunday(date(year, 7, 14)))

    # Mariä Himmelfahrt — 15. August
    holidays.append(_monday_if_sunday(date(year, 8, 15)))

    # Allerheiligen — 1. November
    holidays.append(_monday_if_sunday(date(year, 11, 1)))

    # Waffenstillstand 1918 — 11. November
    holidays.append(_monday_if_sunday(date(year, 11, 11)))

    # Weihnachten — 25. Dezember
    holidays.append(_observed(date(year, 12, 25)))

    # 26. Dezember (Euronext Paris schließt auch an diesem Tag)
    holidays.append(_observed(date(year, 12, 26)))

    return sorted(set(holidays))


# ── TSE (Tokyo Stock Exchange) ─────────────────────────────────────────────────

def _compute_tse_holidays(year: int) -> list[date]:
    """
    TSE Tokyo Stock Exchange Feiertage (japanische Nationalfeiertage).
    Japanische Besonderheit: Wenn Feiertag auf Sonntag fällt → Montag (振替休日).
    Wenn zwei Feiertage einen normalen Tag einschließen → auch dieser ist frei (国民の休日).
    """

    def jp_observed(d: date) -> date:
        """Japanische Beobachtungsregel: Sonntag → Montag."""
        if d.weekday() == 6:
            return d + timedelta(days=1)
        return d

    holidays = []

    # Neujahr — 1. Januar
    holidays.append(jp_observed(date(year, 1, 1)))
    # Börse schließt auch 2. und 3. Januar
    holidays.append(jp_observed(date(year, 1, 2)))
    holidays.append(jp_observed(date(year, 1, 3)))

    # Erwachsenentag — 2. Montag im Januar (seit 2000)
    if year >= 2000:
        holidays.append(_nth_weekday(year, 1, 0, 2))

    # Nationalfeiertag — 11. Februar (Staatsgründung)
    holidays.append(jp_observed(date(year, 2, 11)))

    # Kaisers Geburtstag — 23. Februar (seit 2020, Naruhito)
    if year >= 2020:
        holidays.append(jp_observed(date(year, 2, 23)))
    elif year >= 1990:  # Akihito: 23. Dezember
        holidays.append(jp_observed(date(year, 12, 23)))

    # Frühlingstagundnachtgleiche — ca. 20./21. März (variabel)
    # Vereinfachung: 20. März (exakte Berechnung astronomisch komplex)
    holidays.append(jp_observed(date(year, 3, 20)))

    # Showa Day — 29. April
    holidays.append(jp_observed(date(year, 4, 29)))

    # Goldene Woche — 3./4./5. Mai
    holidays.append(jp_observed(date(year, 5, 3)))   # Verfassungstag
    holidays.append(jp_observed(date(year, 5, 4)))   # Grüner Tag
    holidays.append(jp_observed(date(year, 5, 5)))   # Kindertag

    # Meerestag — 3. Montag im Juli
    holidays.append(_nth_weekday(year, 7, 0, 3))

    # Berg-Tag — 11. August (seit 2016)
    if year >= 2016:
        holidays.append(jp_observed(date(year, 8, 11)))

    # Börse schließt auch 14./15. August (Obon — kein offiz. Feiertag, aber Praxis)
    # Nicht eingetragen da offiziell Handelstage

    # Respektstag für Senioren — 3. Montag im September
    holidays.append(_nth_weekday(year, 9, 0, 3))

    # Herbsttagundnachtgleiche — ca. 22./23. September
    holidays.append(jp_observed(date(year, 9, 23)))

    # Sporttag — 2. Montag im Oktober
    holidays.append(_nth_weekday(year, 10, 0, 2))

    # Kulturtag — 3. November
    holidays.append(jp_observed(date(year, 11, 3)))

    # Arbeitsdanktag — 23. November
    holidays.append(jp_observed(date(year, 11, 23)))

    # Jahresende — 31. Dezember (Börse geschlossen)
    holidays.append(date(year, 12, 31))

    return sorted(set(holidays))


# ── Haupt-API ──────────────────────────────────────────────────────────────────

_EXCHANGE_FUNCTIONS = {
    "NYSE":     lambda year: list(get_nyse_holidays(year, year)),
    "NASDAQ":   lambda year: list(get_nyse_holidays(year, year)),  # gleich wie NYSE
    "XETRA":    _compute_xetra_holidays,
    "LSE":      _compute_lse_holidays,
    "EURONEXT": _compute_euronext_holidays,
    "TSE":      _compute_tse_holidays,
    "SIX":      _compute_xetra_holidays,  # Schweiz ähnlich wie XETRA
}


def get_holidays(
    exchange: str,
    start_year: int,
    end_year: int,
) -> set[date]:
    """
    Gibt alle Börsenfeiertage einer Börse für einen Zeitraum zurück.

    Args:
        exchange   : Börsen-Kürzel ("NYSE","XETRA","LSE","EURONEXT","TSE")
        start_year : erstes Jahr (inklusiv)
        end_year   : letztes Jahr (inklusiv)

    Returns:
        set[date] — alle Feiertage im Zeitraum
    """
    fn = _EXCHANGE_FUNCTIONS.get(exchange.upper())
    if fn is None:
        # Fallback: NYSE
        return get_nyse_holidays(start_year, end_year)

    holidays = set()
    for year in range(start_year, end_year + 1):
        holidays.update(fn(year))
    return holidays


def is_holiday(d: date, exchange: str = "NYSE") -> bool:
    """Prüft ob ein Datum ein Feiertag an der gegebenen Börse ist."""
    fn = _EXCHANGE_FUNCTIONS.get(exchange.upper())
    if fn is None:
        fn = _EXCHANGE_FUNCTIONS["NYSE"]
    return d in fn(d.year)


def is_trading_day(d: date, exchange: str = "NYSE") -> bool:
    """Prüft ob ein Datum ein Handelstag ist (kein Wochenende, kein Feiertag)."""
    if d.weekday() >= 5:
        return False
    return not is_holiday(d, exchange)


def get_holidays_for_ticker(
    ticker: str,
    start_year: int,
    end_year: int,
) -> set[date]:
    """
    Gibt die Börsenfeiertage für einen Ticker zurück.
    Erkennt die Börse automatisch aus TICKER_TO_EXCHANGE.
    Fallback: NYSE.

    Args:
        ticker     : Ticker-Symbol (z.B. "SPY", "^GDAXI", "^FTSE")
        start_year : erstes Jahr
        end_year   : letztes Jahr

    Returns:
        set[date] — Feiertage der zugehörigen Börse
    """
    exchange = _TICKER_MAP.get(ticker.upper(), "NYSE")
    return get_holidays(exchange, start_year, end_year)


def get_exchange_for_ticker(ticker: str) -> str:
    """Gibt das Exchange-Kürzel für einen Ticker zurück. Fallback: NYSE."""
    return _TICKER_MAP.get(ticker.upper(), "NYSE")


# ── Selbsttest ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Börsenfeiertage 2025 im Vergleich:")
    print("=" * 60)

    exchanges = ["NYSE", "XETRA", "LSE", "EURONEXT", "TSE"]
    for ex in exchanges:
        fn = _EXCHANGE_FUNCTIONS[ex]
        holidays = fn(2025)
        print(f"\n{ex} ({len(holidays)} Feiertage):")
        for h in holidays:
            print(f"  {h.strftime('%d.%m.%Y')} ({h.strftime('%A')})")

    print("\n\nExchange-Erkennung via Ticker:")
    print("=" * 60)
    test_tickers = ["SPY", "^GDAXI", "^FTSE", "^FCHI", "^N225", "AAPL"]
    for t in test_tickers:
        ex = get_exchange_for_ticker(t)
        print(f"  {t:12} → {ex}")

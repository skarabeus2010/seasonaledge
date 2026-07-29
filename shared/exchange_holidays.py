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
                "XLF", "XLK", "XLE", "XLV", "XLU", "XLI", "XLC", "XLB", "XLP", "XLY",
                "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "JPM", "XOM",
                "BRK-B", "V", "JNJ", "WMT", "PG", "UNH", "HD", "MA",
                "SHY", "IEF", "HYG", "EEM", "FXI", "EWZ",
                "^GSPC", "^DJI", "^IXIC", "^NDX", "^RUT", "^VIX",
                "GC=F", "SI=F", "CL=F", "BZ=F", "NG=F", "ZC=F", "ZW=F",
                "HG=F", "PL=F", "ZS=F",
                "ES=F", "NQ=F"],
    # Forex: Mo-Fr 24h, keine Feiertage, Sa geschlossen, So ab 23:00 CET
    "FOREX":   ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X",
                "AUDUSD=X", "NZDUSD=X", "USDCAD=X",
                "EURGBP=X", "EURJPY=X", "EURCHF=X", "GBPJPY=X"],
    # Crypto: 24/7 inkl. Wochenende
    "CRYPTO":  ["BTC-USD", "ETH-USD", "SOL-USD",
                "XRP-USD", "ADA-USD", "DOGE-USD"],
    # XETRA (Deutschland)
    "XETRA":  ["^GDAXI", "^MDAXI", "^SDAXI", "^TECDAX",
               "SAP", "SIE.DE", "ALV.DE", "BAS.DE", "BMW.DE",
               "MBG.DE", "DTE.DE", "ADS.DE"],
    # LSE (London)
    "LSE":    ["^FTSE", "^FTMC"],
    # Euronext Paris
    "EURONEXT": ["^FCHI", "ASML", "MC.PA"],
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
    """Pfingstmontag = Ostersonntag + 50 Tage (Pfingstsonntag + 1)."""
    return _easter_sunday(year) + timedelta(days=50)

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
    XETRA/Frankfurt handelsfreie Tage — OFFIZIELL (Deutsche Börse Cash Market).

    Xetra handelt Mo-Fr AUSSER: Neujahr, Karfreitag, Ostermontag, 1. Mai,
    24./25./26./31. Dezember. Das ist die VOLLSTÄNDIGE Liste (8 Tage).

    ⚠️ NICHT handelsfrei (Xetra HANDELT, durch Daten + offiz. Kalender bestätigt):
       - Pfingstmontag, Christi Himmelfahrt, Fronleichnam
       - Tag der Deutschen Einheit (3. Oktober)  ← häufiger Irrtum!
    ⚠️ KEIN Observed-Shift: fällt ein Feiertag aufs Wochenende, gibt es KEINEN
       Montags-Ersatz (anders als NYSE/LSE). Daher feste Daten, kein _observed.
    """
    holidays = [
        date(year, 1, 1),       # Neujahr
        _good_friday(year),     # Karfreitag
        _easter_monday(year),   # Ostermontag
        date(year, 5, 1),       # Tag der Arbeit
        date(year, 12, 25),     # 1. Weihnachtstag
        date(year, 12, 26),     # 2. Weihnachtstag
    ]
    # Heiligabend + Silvester: Xetra seit 2011 ganztägig geschlossen
    # (davor Handelstag mit Frühschluss).
    if year >= 2011:
        holidays.append(date(year, 12, 24))
        holidays.append(date(year, 12, 31))

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
    Euronext-Handelskalender (Paris, Amsterdam, Brüssel, Lissabon, seit 2021
    auch Mailand/Borsa Italiana).

    WICHTIG: Euronext ist seit der Harmonisierung NUR an 6 Tagen geschlossen —
    NICHT an den nationalen Feiertagen der einzelnen Länder. Insbesondere wird
    DURCHGEHANDELT an: Pfingstmontag, Christi Himmelfahrt, 8. Mai, 14. Juli
    (Bastille), 15. August (Mariä Himmelfahrt), 1. November (Allerheiligen),
    11. November (Waffenstillstand). Diese fälschlich als Feiertag zu führen
    erzeugte Geister-Lücken + falsche TDOM/TDOY für alle .PA/.MI/.AS-Ticker.

    KEIN Observed-Shift: fällt ein Feiertag aufs Wochenende, kein Montags-Ersatz.
    """
    return sorted({
        date(year, 1, 1),       # Neujahr
        _good_friday(year),     # Karfreitag
        _easter_monday(year),   # Ostermontag
        date(year, 5, 1),       # Tag der Arbeit (einziger nat. Feiertag mit Schließung)
        date(year, 12, 25),     # 1. Weihnachtstag
        date(year, 12, 26),     # 2. Weihnachtstag
    })


# ── Borsa Italiana (Mailand) ───────────────────────────────────────────────────

def _compute_milan_holidays(year: int) -> list[date]:
    """
    Borsa Italiana (Mailand) — seit 2021 Teil von Euronext, handelt daher den
    Euronext-Kern. ABER drei italienische Besonderheiten, an denen Mailand
    ZUSÄTZLICH schließt (datenbestätigt für .MI-Ticker): Ferragosto (15.8.),
    Heiligabend (24.12.) und Silvester (31.12.). Andere ital. Feiertage
    (6.1./25.4./2.6./8.12.) handelt Mailand durch (Euronext-Harmonisierung).
    """
    holidays = list(_compute_euronext_holidays(year))
    holidays.append(date(year, 8, 15))   # Ferragosto
    holidays.append(date(year, 12, 24))  # Vigilia di Natale
    holidays.append(date(year, 12, 31))  # San Silvestro
    return sorted(set(holidays))


# ── TSE (Tokyo Stock Exchange) ─────────────────────────────────────────────────

def _compute_tse_holidays(year: int) -> list[date]:
    """
    TSE Tokyo Stock Exchange Feiertage (japanische Nationalfeiertage).
    Japanische Besonderheit: Wenn Feiertag auf Sonntag fällt → Montag (振替休日).
    Wenn zwei Feiertage einen normalen Tag einschließen → auch dieser ist frei (国民の休日).
    """

    def equinox(month: int) -> date:
        # Astronomische Näherung (gültig 1980-2099) — Frühlings-/Herbst-Tagundnacht-
        # gleiche schwanken zwischen 20./21. März bzw. 22./23. September.
        if month == 3:
            return date(year, 3, int(20.8431 + 0.242194 * (year - 1980) - (year - 1980) // 4))
        return date(year, 9, int(23.2488 + 0.242194 * (year - 1980) - (year - 1980) // 4))

    # ── Nationale Feiertage (ohne Shift) ──
    national: set[date] = {
        date(year, 1, 1),            # Ganjitsu (Neujahr)
        date(year, 2, 11),           # Kenkoku Kinen no Hi
        equinox(3),                  # Shunbun no Hi (Frühlingsanfang)
        date(year, 4, 29),           # Showa no Hi
        date(year, 5, 3),            # Kenpo Kinenbi
        date(year, 5, 4),            # Midori no Hi
        date(year, 5, 5),            # Kodomo no Hi
        _nth_weekday(year, 7, 0, 3), # Umi no Hi (Meerestag)
        _nth_weekday(year, 9, 0, 3), # Keiro no Hi
        equinox(9),                  # Shubun no Hi (Herbstanfang)
        _nth_weekday(year, 10, 0, 2),# Sports no Hi
        date(year, 11, 3),           # Bunka no Hi
        date(year, 11, 23),          # Kinro Kansha no Hi
    }
    if year >= 2000:
        national.add(_nth_weekday(year, 1, 0, 2))   # Seijin no Hi
    if year >= 2020:
        national.add(date(year, 2, 23))             # Tenno Tanjobi (Naruhito)
    elif year >= 1990:
        national.add(date(year, 12, 23))            # (Akihito)
    if year >= 2016:
        national.add(date(year, 8, 11))             # Yama no Hi

    holidays = set(national)

    # ── Furikae Kyujitsu (振替休日): Sonntags-Feiertag → nächster Nicht-Feiertag ──
    for h in sorted(national):
        if h.weekday() == 6:
            sub = h + timedelta(days=1)
            while sub in national:
                sub += timedelta(days=1)
            holidays.add(sub)

    # ── Kokumin no Kyujitsu (国民の休日): Werktag zwischen zwei Feiertagen ──
    for h in sorted(national):
        mid = h + timedelta(days=1)
        if (h + timedelta(days=2)) in national and mid not in national and mid.weekday() < 5:
            holidays.add(mid)

    # ── Börsen-Schließungen Jahreswechsel (keine Nationalfeiertage, kein Shift) ──
    holidays.add(date(year, 1, 2))
    holidays.add(date(year, 1, 3))
    holidays.add(date(year, 12, 31))

    return sorted(holidays)


# ── SIX (Schweiz) ──────────────────────────────────────────────────────────────

def _compute_six_holidays(year: int) -> list[date]:
    """SIX Swiss Exchange Feiertage — Schweizer Bundesfeiertage."""
    # SIX schließt Christi Himmelfahrt + Pfingstmontag (anders als XETRA!).
    # KEIN Observed-Shift (feste Daten, kein Montags-Ersatz am Wochenende).
    return sorted({
        date(year, 1, 1),       # Neujahr
        date(year, 1, 2),       # Berchtoldstag
        _good_friday(year),     # Karfreitag
        _easter_monday(year),   # Ostermontag
        date(year, 5, 1),       # Tag der Arbeit
        _ascension_day(year),   # Christi Himmelfahrt
        _whit_monday(year),     # Pfingstmontag
        date(year, 8, 1),       # Schweizer Bundesfeier
        date(year, 12, 24),     # Heiligabend
        date(year, 12, 25),     # 1. Weihnachtstag
        date(year, 12, 26),     # Stephanstag
        date(year, 12, 31),     # Silvester
    })


# ── Nasdaq Stockholm ───────────────────────────────────────────────────────────

def _compute_stockholm_holidays(year: int) -> list[date]:
    """Nasdaq Stockholm handelsfreie Tage — KEIN Observed-Shift (feste Daten)."""
    # Midsommarafton — Freitag zwischen 19. und 25. Juni
    midsommar = date(year, 6, 19)
    while midsommar.weekday() != 4:  # Freitag = 4
        midsommar += timedelta(days=1)
    return sorted({
        date(year, 1, 1),       # Nyårsdagen
        date(year, 1, 6),       # Trettondedag jul (Hl. Drei Könige)
        _good_friday(year),     # Långfredagen
        _easter_monday(year),   # Annandag påsk
        date(year, 5, 1),       # Första maj
        _ascension_day(year),   # Kristi himmelsfärdsdag
        date(year, 6, 6),       # Sveriges nationaldag
        midsommar,              # Midsommarafton
        date(year, 12, 24),     # Julafton
        date(year, 12, 25),     # Juldagen
        date(year, 12, 26),     # Annandag jul
        date(year, 12, 31),     # Nyårsafton
    })


# ── HKEX (Hongkong) + KRX (Korea) ──────────────────────────────────────────────
# Mondkalender-Feiertage (Lunar New Year, Buddha's Birthday, Mid-Autumn, Chuseok,
# Seollag …) + unregelmäßige Schließungen (Taifune, Wahltage) sind NICHT regel-
# basiert berechenbar → datengetriebene Tabelle (aus ^HSI/^KS11, Clean-Ära), wie
# _chinese_new_year. Bei neuen Jahren aus dem offiziellen HKEX/KRX-Kalender ergänzen.

_HKEX_HOLIDAYS = {
    2016: [(2,8),(2,9),(2,10),(3,25),(3,28),(4,4),(5,2),(6,9),(7,1),(8,2),(9,16),(10,10),(10,21),(12,26),(12,27)],
    2017: [(1,2),(1,30),(1,31),(4,4),(4,14),(4,17),(5,1),(5,3),(5,30),(8,23),(10,2),(10,5),(12,25),(12,26)],
    2018: [(1,1),(2,16),(2,19),(3,30),(4,2),(4,5),(5,1),(5,22),(6,18),(7,2),(9,25),(10,1),(10,17),(12,25),(12,26)],
    2019: [(1,1),(2,5),(2,6),(2,7),(4,5),(4,19),(4,22),(5,1),(5,13),(6,7),(7,1),(10,1),(10,7),(12,25),(12,26)],
    2020: [(1,1),(1,27),(1,28),(4,10),(4,13),(4,30),(5,1),(6,25),(7,1),(10,1),(10,2),(10,13),(10,26),(12,25)],
    2021: [(1,1),(2,12),(2,15),(4,2),(4,5),(4,6),(5,19),(6,14),(7,1),(9,22),(10,1),(10,13),(10,14),(12,27)],
    2022: [(2,1),(2,2),(2,3),(4,5),(4,15),(4,18),(5,2),(5,9),(6,3),(7,1),(9,12),(10,4),(12,26),(12,27)],
    2023: [(1,2),(1,23),(1,24),(1,25),(4,5),(4,7),(4,10),(5,1),(5,26),(6,22),(7,17),(9,1),(9,8),(10,2),(10,23),(12,25),(12,26)],
    2024: [(1,1),(2,12),(2,13),(3,29),(4,1),(4,4),(5,1),(5,15),(6,10),(7,1),(9,6),(9,18),(10,1),(10,11),(12,25),(12,26)],
    2025: [(1,1),(1,29),(1,30),(1,31),(4,4),(4,18),(4,21),(5,1),(5,5),(7,1),(10,1),(10,7),(10,29),(12,25),(12,26)],
    # 2026 vollständig (Quelle: calendarlabs.com/hkex + gov.hk). Sa-Einträge (9,26),(12,26)
    # sind im is_trading_day()-Pfad harmlos (weekday >= 5 filtert sie bereits raus).
    2026: [(1,1),(2,17),(2,18),(2,19),(4,3),(4,6),(4,7),(5,1),(5,25),(6,19),(7,1),(9,26),(10,1),(10,19),(12,25),(12,26)],
}

_KRX_HOLIDAYS = {
    2016: [(2,8),(2,9),(2,10),(3,1),(4,13),(5,5),(5,6),(6,6),(8,15),(9,14),(9,15),(9,16),(10,3),(12,30)],
    2017: [(1,27),(1,30),(3,1),(5,1),(5,3),(5,5),(5,9),(6,6),(8,15),(9,22),(10,2),(10,3),(10,4),(10,5),(10,6),(10,9),(12,20),(12,25),(12,29)],
    2018: [(1,1),(2,15),(2,16),(3,1),(5,1),(5,7),(5,22),(6,6),(6,13),(8,15),(9,24),(9,25),(9,26),(10,3),(10,9),(12,25),(12,31)],
    2019: [(1,1),(2,4),(2,5),(2,6),(3,1),(5,1),(5,6),(6,6),(8,15),(9,12),(9,13),(10,3),(10,9),(12,25),(12,31)],
    2020: [(1,1),(1,24),(1,27),(4,15),(4,30),(5,1),(5,5),(8,17),(9,30),(10,1),(10,2),(10,9),(12,25),(12,31)],
    2021: [(1,1),(2,11),(2,12),(3,1),(5,5),(5,19),(8,16),(9,20),(9,21),(9,22),(10,4),(10,11),(12,31)],
    2022: [(1,3),(1,31),(2,1),(2,2),(3,1),(3,9),(5,5),(5,9),(6,1),(6,6),(8,15),(9,9),(9,12),(10,3),(10,10),(12,30)],
    2023: [(1,23),(1,24),(3,1),(5,1),(5,5),(5,29),(6,6),(8,15),(9,28),(9,29),(10,2),(10,3),(10,9),(12,25),(12,29)],
    2024: [(1,1),(2,9),(2,12),(3,1),(4,10),(5,1),(5,6),(5,15),(6,6),(8,15),(9,16),(9,17),(9,18),(10,1),(10,3),(10,9),(12,25),(12,31)],
    2025: [(1,1),(1,27),(1,28),(1,29),(1,30),(3,3),(5,1),(5,5),(5,6),(6,3),(6,6),(8,15),(10,3),(10,6),(10,7),(10,8),(10,9),(12,25),(12,31)],
    # 2026 vollständig (Quelle: calendarlabs.com/krx + kstockguide.com). Highlights:
    # (7,17) 제헌절 Constitution Day (ab 2026 wieder Feiertag), (8,17) Vertretungstag
    # für 광복절 15.8. (Samstag→Montag), (10,5) Vertretungstag für 개천절 3.10. (Samstag→Montag).
    2026: [(1,1),(2,16),(2,17),(2,18),(3,2),(5,1),(5,5),(5,25),(6,3),(7,17),(8,17),(9,24),(9,25),(10,5),(10,9),(12,25),(12,31)],
}


def _compute_hkex_holidays(year: int) -> list[date]:
    """HKEX (Hongkong). Tabellengestützt; Fallback = fixe gregorianische Feiertage."""
    if year in _HKEX_HOLIDAYS:
        return sorted(date(year, m, d) for m, d in _HKEX_HOLIDAYS[year])
    return sorted({date(year, 1, 1), _good_friday(year), _easter_monday(year),
                   date(year, 5, 1), date(year, 7, 1), date(year, 10, 1),
                   date(year, 12, 25), date(year, 12, 26)})


def _compute_krx_holidays(year: int) -> list[date]:
    """KRX (Korea). Tabellengestützt; Fallback = fixe gregorianische Feiertage."""
    if year in _KRX_HOLIDAYS:
        return sorted(date(year, m, d) for m, d in _KRX_HOLIDAYS[year])
    return sorted({date(year, 1, 1), date(year, 3, 1), date(year, 5, 1), date(year, 5, 5),
                   date(year, 6, 6), date(year, 8, 15), date(year, 10, 3), date(year, 10, 9),
                   date(year, 12, 25), date(year, 12, 31)})


# ── Haupt-API ──────────────────────────────────────────────────────────────────

_EXCHANGE_FUNCTIONS = {
    "NYSE":      lambda year: list(get_nyse_holidays(year, year)),
    "NASDAQ":    lambda year: list(get_nyse_holidays(year, year)),  # gleich wie NYSE
    "XETRA":     _compute_xetra_holidays,
    "LSE":       _compute_lse_holidays,
    "EURONEXT":  _compute_euronext_holidays,
    "TSE":       _compute_tse_holidays,
    "SIX":       _compute_six_holidays,         # Schweiz — eigener Kalender (Christi Himmelfahrt!)
    "MILAN":     _compute_milan_holidays,       # Borsa Italiana — Euronext + Ferragosto/24./31.12.
    "STOCKHOLM": _compute_stockholm_holidays,   # Schweden — eigener Kalender
    "HKEX":      _compute_hkex_holidays,        # Hongkong — Mondkalender-Tabelle
    "KRX":       _compute_krx_holidays,         # Korea — Mondkalender-Tabelle
    "FOREX":     lambda year: [],               # Keine Feiertage (Mo-Fr 24h)
    "CRYPTO":    lambda year: [],               # Keine Feiertage (24/7)
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
    """Prüft ob ein Datum ein Handelstag ist (kein Wochenende, kein Feiertag).

    Sonderfaelle:
      - CRYPTO: 24/7, immer True (auch Sa/So)
      - FOREX:  Mo-Fr 24h, keine Feiertage (Sa/So geschlossen)
    """
    if exchange.upper() == "CRYPTO":
        return True  # 24/7
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
    """Gibt das Exchange-Kürzel für einen Ticker zurück.

    Prueft zuerst TICKER_TO_EXCHANGE, dann SYMBOLS["exchange"] Fallback.
    """
    ex = _TICKER_MAP.get(ticker.upper())
    if ex:
        return ex
    # Fallback: exchange-Feld aus SYMBOLS
    try:
        from shared.symbols import SYMBOLS
        sym = SYMBOLS.get(ticker, {})
        exchange = sym.get("exchange", "")
        if exchange == "Forex":
            return "FOREX"
        if exchange == "Crypto":
            return "CRYPTO"
    except Exception:
        pass
    return "NYSE"


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

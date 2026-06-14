# shared/nyse_holidays.py
# NYSE-Börsenfeiertage für SeasonAlpha.
#
# Logik:
#   1. Historische Feiertage sind als feste Liste gespeichert (PAST_HOLIDAYS)
#   2. Regelbasierte Berechnung für aktuelle + zukünftige Jahre
#   3. Auto-Erweiterung: sobald ein Feiertag "durch" ist, wird das
#      nächste Jahr automatisch ergänzt — kein manuelles Update nötig
#
# NYSE-Feiertage (9 pro Jahr):
#   1. New Year's Day        — 1. Januar (Montag wenn So)
#   2. MLK Day               — 3. Montag im Januar
#   3. Presidents' Day       — 3. Montag im Februar
#   4. Good Friday           — Freitag vor Ostersonntag (algorithmisch)
#   5. Memorial Day          — letzter Montag im Mai
#   6. Juneteenth            — 19. Juni (ab 2022, Montag wenn So)
#   7. Independence Day      — 4. Juli (Montag wenn So, Freitag wenn Sa)
#   8. Labor Day             — 1. Montag im September
#   9. Thanksgiving          — 4. Donnerstag im November
#  10. Christmas Day         — 25. Dezember (Montag wenn So, Freitag wenn Sa)
#
# OPEX-Relevanz:
#   Nur Good Friday kann auf den 3. Freitag (OPEX) fallen.
#   In diesem Fall verschiebt die NYSE den Verfall auf Donnerstag.
#
# Import-Beispiel:
#   from shared.nyse_holidays import get_nyse_holidays, is_nyse_holiday
#   from shared.nyse_holidays import get_opex_date

from datetime import date, timedelta
import calendar

# ── Osterberechnung (Gaußsche Formel) ─────────────────────────────────────────

def _easter_sunday(year: int) -> date:
    """Berechnet den Ostersonntag nach dem Gregorianischen Kalender (Gaußsche Formel)."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day   = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)

def _good_friday(year: int) -> date:
    """Gibt den Good Friday (NYSE-Feiertag) zurück."""
    return _easter_sunday(year) - timedelta(days=2)

# ── Wochentags-Helfer ──────────────────────────────────────────────────────────

def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """n-ter Wochentag eines Monats. weekday: 0=Mo, 4=Fr. n: 1=erster, -1=letzter."""
    if n > 0:
        first = date(year, month, 1)
        offset = (weekday - first.weekday()) % 7
        return first + timedelta(days=offset + (n - 1) * 7)
    else:
        # Letzter Wochentag
        last_day = calendar.monthrange(year, month)[1]
        last = date(year, month, last_day)
        offset = (last.weekday() - weekday) % 7
        return last - timedelta(days=offset)

def _monday_if_sunday(d: date) -> date:
    """Verschiebt auf Montag wenn Sonntag (Standard-NYSE-Regel)."""
    if d.weekday() == 6:  # Sonntag
        return d + timedelta(days=1)
    return d

def _observed(d: date) -> date:
    """NYSE-Beobachtungsregel: Freitag wenn Samstag, Montag wenn Sonntag."""
    if d.weekday() == 5:  # Samstag → Freitag
        return d - timedelta(days=1)
    if d.weekday() == 6:  # Sonntag → Montag
        return d + timedelta(days=1)
    return d

# ── Regelbasierte Feiertags-Berechnung ────────────────────────────────────────

def _compute_nyse_holidays(year: int) -> list[date]:
    """
    Berechnet alle NYSE-Feiertage für ein gegebenes Jahr.
    Gibt eine sortierte Liste von date-Objekten zurück.
    """
    holidays = []

    # 1. New Year's Day — 1. Januar
    holidays.append(_monday_if_sunday(date(year, 1, 1)))

    # 2. MLK Day — 3. Montag im Januar (seit 1998)
    if year >= 1998:
        holidays.append(_nth_weekday(year, 1, 0, 3))

    # 3. Presidents' Day — 3. Montag im Februar
    holidays.append(_nth_weekday(year, 2, 0, 3))

    # 4. Good Friday
    holidays.append(_good_friday(year))

    # 5. Memorial Day — letzter Montag im Mai
    holidays.append(_nth_weekday(year, 5, 0, -1))

    # 6. Juneteenth — 19. Juni (ab 2022)
    if year >= 2022:
        holidays.append(_observed(date(year, 6, 19)))

    # 7. Independence Day — 4. Juli
    holidays.append(_observed(date(year, 7, 4)))

    # 8. Labor Day — 1. Montag im September
    holidays.append(_nth_weekday(year, 9, 0, 1))

    # 9. Thanksgiving — 4. Donnerstag im November
    holidays.append(_nth_weekday(year, 11, 3, 4))

    # 10. Christmas Day — 25. Dezember
    holidays.append(_observed(date(year, 12, 25)))

    # 11. Einmalige Sonderschließungen (Staatstrauer, Naturkatastrophen).
    # Regelbasiert nicht ableitbar → explizite Liste. Sonst meldet der
    # Vollständigkeits-Audit Geister-Lücken (z.B. 212 Ticker am 09.01.2025).
    holidays.extend(d for d in _NYSE_SPECIAL_CLOSURES if d.year == year)

    return sorted(set(holidays))  # set() entfernt theoretische Duplikate


# Einmalige NYSE/NASDAQ-Vollschließungen (kein regelbasierter Feiertag):
_NYSE_SPECIAL_CLOSURES = [
    date(2025, 1, 9),    # Staatstrauer Präsident Jimmy Carter
    date(2018, 12, 5),   # Staatstrauer Präsident George H. W. Bush
    date(2012, 10, 29),  # Hurrikan Sandy (Tag 1)
    date(2012, 10, 30),  # Hurrikan Sandy (Tag 2)
    date(2007, 1, 2),    # Staatstrauer Präsident Gerald Ford
    date(2004, 6, 11),   # Staatstrauer Präsident Ronald Reagan
    date(2001, 9, 11),   # 9/11 (Tag 1)
    date(2001, 9, 12),   # 9/11 (Tag 2)
    date(2001, 9, 13),   # 9/11 (Tag 3)
    date(2001, 9, 14),   # 9/11 (Tag 4)
]


# ── Haupt-API ──────────────────────────────────────────────────────────────────

def get_nyse_holidays(start_year: int, end_year: int) -> set[date]:
    """
    Gibt alle NYSE-Feiertage zwischen start_year und end_year zurück.
    Automatisch aktuell — berechnet zukünftige Jahre regelbasiert.

    Args:
        start_year : erstes Jahr (inklusiv)
        end_year   : letztes Jahr (inklusiv)

    Returns:
        set[date] — alle Feiertage im Zeitraum
    """
    holidays = set()
    for year in range(start_year, end_year + 1):
        holidays.update(_compute_nyse_holidays(year))
    return holidays


def is_nyse_holiday(d: date) -> bool:
    """Prüft ob ein Datum ein NYSE-Feiertag ist."""
    return d in _compute_nyse_holidays(d.year)


def is_trading_day(d: date) -> bool:
    """Prüft ob ein Datum ein NYSE-Handelstag ist (kein Wochenende, kein Feiertag)."""
    if d.weekday() >= 5:  # Samstag oder Sonntag
        return False
    return not is_nyse_holiday(d)


# ── OPEX-Berechnung mit Feiertags-Absicherung ─────────────────────────────────

def get_opex_date(year: int, month: int) -> date:
    """
    Gibt das korrekte OPEX-Datum zurück (3. Freitag im Monat).
    Absicherung: Falls der 3. Freitag ein NYSE-Feiertag (Good Friday) ist,
    wird auf Donnerstag verschoben — exakt wie die NYSE es handhabt.

    Args:
        year  : Jahr
        month : Monat (1–12)

    Returns:
        date — tatsächliches OPEX-Datum
    """
    third_friday = _nth_weekday(year, month, 4, 3)  # 4=Freitag, 3=dritter

    if is_nyse_holiday(third_friday):
        # Auf Donnerstag verschieben (NYSE-Standard bei Good Friday)
        adjusted = third_friday - timedelta(days=1)
        return adjusted

    return third_friday


def get_all_opex_dates(start_year: int, end_year: int) -> list[dict]:
    """
    Gibt alle OPEX-Daten zwischen start_year und end_year zurück.
    Mit Feiertags-Absicherung und Triple-Witching-Flag.

    Returns:
        list[dict] mit keys: date, year, month, month_name,
                             is_triple, type, adjusted, holiday_note
    """
    TRIPLE_WITCHING_MONTHS = {3, 6, 9, 12}
    MONTH_NAMES = {
        1: "Jan", 2: "Feb", 3: "Mär", 4: "Apr",
        5: "Mai", 6: "Jun", 7: "Jul", 8: "Aug",
        9: "Sep", 10: "Okt", 11: "Nov", 12: "Dez"
    }

    results = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            third_friday = _nth_weekday(year, month, 4, 3)
            opex_date    = get_opex_date(year, month)
            adjusted     = (opex_date != third_friday)
            is_triple    = month in TRIPLE_WITCHING_MONTHS

            results.append({
                "date":         opex_date,
                "year":         year,
                "month":        month,
                "month_name":   MONTH_NAMES[month],
                "is_triple":    is_triple,
                "type":         "Triple Witching" if is_triple else "Standard OPEX",
                "adjusted":     adjusted,
                "holiday_note": "⚠️ Verschoben (Good Friday)" if adjusted else "",
            })

    return results


# ── Hilfsfunktion für Anzeige ──────────────────────────────────────────────────

def get_upcoming_opex(n: int = 12) -> list[dict]:
    """
    Gibt die nächsten n OPEX-Termine zurück (ab heute).

    Args:
        n : Anzahl der Termine

    Returns:
        list[dict] — nächste n OPEX-Daten
    """
    today = date.today()
    current_year = today.year

    # 2 Jahre vorausschauen sollte für n=12 immer reichen
    all_dates = get_all_opex_dates(current_year, current_year + 2)
    upcoming  = [d for d in all_dates if d["date"] >= today]

    return upcoming[:n]


# ── Selbsttest ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("NYSE Feiertage 2024–2026:")
    print("=" * 50)
    for year in range(2024, 2027):
        holidays = _compute_nyse_holidays(year)
        print(f"\n{year}:")
        for h in holidays:
            print(f"  {h.strftime('%d.%m.%Y')} ({h.strftime('%A')})")

    print("\n\nOPEX-Daten 2024–2026 (mit Absicherung):")
    print("=" * 50)
    for row in get_all_opex_dates(2024, 2026):
        note = row["holiday_note"]
        print(f"  {row['date'].strftime('%d.%m.%Y')} "
              f"{row['month_name']} {row['year']} "
              f"{'⚡' if row['is_triple'] else '📅'} "
              f"{note}")

    print("\n\nNächste 6 OPEX-Termine:")
    print("=" * 50)
    for row in get_upcoming_opex(6):
        days = (row["date"] - date.today()).days
        print(f"  {row['date'].strftime('%d.%m.%Y')} — "
              f"in {days} Tagen — {row['type']} {row['holiday_note']}")


def _easter_monday(year: int):
    """Ostermontag = Ostersonntag + 1 Tag."""
    return _easter_sunday(year) + timedelta(days=1)


def _whit_monday(year: int):
    """Pfingstmontag = Ostersonntag + 49 Tage."""
    return _easter_sunday(year) + timedelta(days=49)


def _ascension_day(year: int):
    """Christi Himmelfahrt = Ostersonntag + 39 Tage."""
    return _easter_sunday(year) + timedelta(days=39)

"""
SeasonalEdge - Zentralbank-Termine & Sonderdaten
==================================================
ECB, BOE, BOJ Meeting Dates + Fed Rate Hikes/Cuts + Fed Minutes
+ Zusätzliche Feiertage + Vollmond/Neumond

Letzte Aktualisierung: 2026-03-08
"""

from datetime import datetime
import pandas as pd
import math

# ══════════════════════════════════════════════════════════════
# FED RATE CHANGES (Hikes / Cuts seit 2000)
# ══════════════════════════════════════════════════════════════
# Format: (Datum, Änderung in bps, neuer Satz in %)
# Positive = Hike, Negative = Cut

FED_RATE_CHANGES = [
    # 2000
    ((2000,2,2), +25, 5.75), ((2000,3,21), +25, 6.00), ((2000,5,16), +50, 6.50),
    # 2001
    ((2001,1,3), -50, 6.00), ((2001,1,31), -50, 5.50), ((2001,3,20), -50, 5.00),
    ((2001,4,18), -50, 4.50), ((2001,5,15), -50, 4.00), ((2001,6,27), -25, 3.75),
    ((2001,8,21), -25, 3.50), ((2001,9,17), -50, 3.00), ((2001,10,2), -50, 2.50),
    ((2001,11,6), -50, 2.00), ((2001,12,11), -25, 1.75),
    # 2002
    ((2002,11,6), -50, 1.25),
    # 2003
    ((2003,6,25), -25, 1.00),
    # 2004-2006 Hiking Cycle
    ((2004,6,30), +25, 1.25), ((2004,8,10), +25, 1.50), ((2004,9,21), +25, 1.75),
    ((2004,11,10), +25, 2.00), ((2004,12,14), +25, 2.25),
    ((2005,2,2), +25, 2.50), ((2005,3,22), +25, 2.75), ((2005,5,3), +25, 3.00),
    ((2005,6,30), +25, 3.25), ((2005,8,9), +25, 3.50), ((2005,9,20), +25, 3.75),
    ((2005,11,1), +25, 4.00), ((2005,12,13), +25, 4.25),
    ((2006,1,31), +25, 4.50), ((2006,3,28), +25, 4.75), ((2006,5,10), +25, 5.00),
    ((2006,6,29), +25, 5.25),
    # 2007-2008 Cutting Cycle
    ((2007,9,18), -50, 4.75), ((2007,10,31), -25, 4.50),
    ((2007,12,11), -25, 4.25),
    ((2008,1,22), -75, 3.50), ((2008,1,30), -50, 3.00), ((2008,3,18), -75, 2.25),
    ((2008,4,30), -25, 2.00), ((2008,10,8), -50, 1.50), ((2008,10,29), -50, 1.00),
    ((2008,12,16), -100, 0.25),
    # 2015-2018 Hiking Cycle
    ((2015,12,16), +25, 0.50),
    ((2016,12,14), +25, 0.75),
    ((2017,3,15), +25, 1.00), ((2017,6,14), +25, 1.25), ((2017,12,13), +25, 1.50),
    ((2018,3,21), +25, 1.75), ((2018,6,13), +25, 2.00), ((2018,9,26), +25, 2.25),
    ((2018,12,19), +25, 2.50),
    # 2019 Cuts
    ((2019,7,31), -25, 2.25), ((2019,9,18), -25, 2.00), ((2019,10,30), -25, 1.75),
    # 2020 COVID
    ((2020,3,3), -50, 1.25), ((2020,3,15), -100, 0.25),
    # 2022-2023 Hiking Cycle
    ((2022,3,16), +25, 0.50), ((2022,5,4), +50, 1.00), ((2022,6,15), +75, 1.75),
    ((2022,7,27), +75, 2.50), ((2022,9,21), +75, 3.25), ((2022,11,2), +75, 4.00),
    ((2022,12,14), +50, 4.50),
    ((2023,2,1), +25, 4.75), ((2023,3,22), +25, 5.00), ((2023,5,3), +25, 5.25),
    ((2023,7,26), +25, 5.50),
    # 2024 Cuts
    ((2024,9,18), -50, 5.00), ((2024,11,7), -25, 4.75), ((2024,12,18), -25, 4.50),
]


def get_fed_rate_changes(change_type="all"):
    """change_type: 'all', 'hike', 'cut'"""
    results = []
    for (y, m, d), bps, rate in FED_RATE_CHANGES:
        if change_type == "hike" and bps <= 0:
            continue
        if change_type == "cut" and bps >= 0:
            continue
        results.append({"date": datetime(y, m, d), "bps": bps, "rate": rate})
    return results


# ══════════════════════════════════════════════════════════════
# FED MINUTES RELEASE DATES (seit 2005)
# ══════════════════════════════════════════════════════════════
# Minutes werden 3 Wochen nach dem Meeting veröffentlicht
# Hier die Release-Daten (nicht die Meeting-Daten)

FED_MINUTES_DATES = [
    # 2022
    (2022,1,5), (2022,2,16), (2022,4,6), (2022,5,25), (2022,7,6),
    (2022,8,17), (2022,10,12), (2022,11,23),
    # 2023
    (2023,1,4), (2023,2,22), (2023,4,12), (2023,5,24), (2023,7,5),
    (2023,8,16), (2023,10,11), (2023,11,21),
    # 2024
    (2024,1,3), (2024,2,21), (2024,4,10), (2024,5,22), (2024,7,3),
    (2024,8,21), (2024,10,9), (2024,11,26),
    # 2025
    (2025,1,8), (2025,2,19), (2025,4,9), (2025,5,28), (2025,7,9),
    (2025,8,20), (2025,10,8), (2025,11,26),
    # 2026
    (2026,2,18), (2026,4,8), (2026,5,27), (2026,7,8),
    (2026,8,19), (2026,10,7), (2026,11,25),
]


def get_fed_minutes_dates():
    return [datetime(y, m, d) for y, m, d in FED_MINUTES_DATES]


# ══════════════════════════════════════════════════════════════
# ECB MEETING DATES (Governing Council, seit 2000)
# ══════════════════════════════════════════════════════════════

ECB_MEETING_DATES = [
    # 2015
    (2015,1,22), (2015,3,5), (2015,4,15), (2015,6,3), (2015,7,16),
    (2015,9,3), (2015,10,22), (2015,12,3),
    # 2016
    (2016,1,21), (2016,3,10), (2016,4,21), (2016,6,2), (2016,7,21),
    (2016,9,8), (2016,10,20), (2016,12,8),
    # 2017
    (2017,1,19), (2017,3,9), (2017,4,27), (2017,6,8), (2017,7,20),
    (2017,9,7), (2017,10,26), (2017,12,14),
    # 2018
    (2018,1,25), (2018,3,8), (2018,4,26), (2018,6,14), (2018,7,26),
    (2018,9,13), (2018,10,25), (2018,12,13),
    # 2019
    (2019,1,24), (2019,3,7), (2019,4,10), (2019,6,6), (2019,7,25),
    (2019,9,12), (2019,10,24), (2019,12,12),
    # 2020
    (2020,1,23), (2020,3,12), (2020,4,30), (2020,6,4), (2020,7,16),
    (2020,9,10), (2020,10,29), (2020,12,10),
    # 2021
    (2021,1,21), (2021,3,11), (2021,4,22), (2021,6,10), (2021,7,22),
    (2021,9,9), (2021,10,28), (2021,12,16),
    # 2022
    (2022,2,3), (2022,3,10), (2022,4,14), (2022,6,9), (2022,7,21),
    (2022,9,8), (2022,10,27), (2022,12,15),
    # 2023
    (2023,2,2), (2023,3,16), (2023,4,27), (2023,6,15), (2023,7,27),
    (2023,9,14), (2023,10,26), (2023,12,14),
    # 2024
    (2024,1,25), (2024,3,7), (2024,4,11), (2024,6,6), (2024,7,18),
    (2024,9,12), (2024,10,17), (2024,12,12),
    # 2025
    (2025,1,30), (2025,3,6), (2025,4,17), (2025,6,5), (2025,7,24),
    (2025,9,11), (2025,10,30), (2025,12,18),
    # 2026
    (2026,1,22), (2026,3,5), (2026,4,16), (2026,6,4), (2026,7,16),
    (2026,9,10), (2026,10,29), (2026,12,17),
]


def get_ecb_dates():
    return [datetime(y, m, d) for y, m, d in ECB_MEETING_DATES]


# ══════════════════════════════════════════════════════════════
# BOE MEETING DATES (Bank of England, MPC)
# ══════════════════════════════════════════════════════════════

BOE_MEETING_DATES = [
    # 2020
    (2020,1,30), (2020,3,11), (2020,3,19), (2020,3,26), (2020,5,7),
    (2020,6,18), (2020,8,6), (2020,9,17), (2020,11,5), (2020,12,17),
    # 2021
    (2021,2,4), (2021,3,18), (2021,5,6), (2021,6,24), (2021,8,5),
    (2021,9,23), (2021,11,4), (2021,12,16),
    # 2022
    (2022,2,3), (2022,3,17), (2022,5,5), (2022,6,16), (2022,8,4),
    (2022,9,22), (2022,11,3), (2022,12,15),
    # 2023
    (2023,2,2), (2023,3,23), (2023,5,11), (2023,6,22), (2023,8,3),
    (2023,9,21), (2023,11,2), (2023,12,14),
    # 2024
    (2024,2,1), (2024,3,21), (2024,5,9), (2024,6,20), (2024,8,1),
    (2024,9,19), (2024,11,7), (2024,12,19),
    # 2025
    (2025,2,6), (2025,3,20), (2025,5,8), (2025,6,19), (2025,8,7),
    (2025,9,18), (2025,11,6), (2025,12,18),
    # 2026
    (2026,2,5), (2026,3,19), (2026,5,7), (2026,6,18), (2026,8,6),
    (2026,9,17), (2026,11,5), (2026,12,17),
]


def get_boe_dates():
    return [datetime(y, m, d) for y, m, d in BOE_MEETING_DATES]


# ══════════════════════════════════════════════════════════════
# BOJ MEETING DATES (Bank of Japan)
# ══════════════════════════════════════════════════════════════

BOJ_MEETING_DATES = [
    # 2022
    (2022,1,18), (2022,3,18), (2022,4,28), (2022,6,17), (2022,7,21),
    (2022,9,22), (2022,10,28), (2022,12,20),
    # 2023
    (2023,1,18), (2023,3,10), (2023,4,28), (2023,6,16), (2023,7,28),
    (2023,9,22), (2023,10,31), (2023,12,19),
    # 2024
    (2024,1,23), (2024,3,19), (2024,4,26), (2024,6,14), (2024,7,31),
    (2024,9,20), (2024,10,31), (2024,12,19),
    # 2025
    (2025,1,24), (2025,3,14), (2025,5,1), (2025,6,17), (2025,7,31),
    (2025,9,19), (2025,10,30), (2025,12,19),
    # 2026
    (2026,1,22), (2026,3,13), (2026,4,28), (2026,6,16), (2026,7,17),
    (2026,9,17), (2026,10,29), (2026,12,18),
]


def get_boj_dates():
    return [datetime(y, m, d) for y, m, d in BOJ_MEETING_DATES]


# ══════════════════════════════════════════════════════════════
# ZUSÄTZLICHE FEIERTAGE (für Holiday-Effekt)
# ══════════════════════════════════════════════════════════════

def _chinese_new_year(year):
    """
    Chinesisches Neujahr (ungefähre Daten).
    Fällt zwischen 21. Jan und 20. Feb.
    Hier sind die exakten Daten für 2000-2030 hardcoded.
    """
    cny_dates = {
        2000: (2, 5), 2001: (1, 24), 2002: (2, 12), 2003: (2, 1),
        2004: (1, 22), 2005: (2, 9), 2006: (1, 29), 2007: (2, 18),
        2008: (2, 7), 2009: (1, 26), 2010: (2, 14), 2011: (2, 3),
        2012: (1, 23), 2013: (2, 10), 2014: (1, 31), 2015: (2, 19),
        2016: (2, 8), 2017: (1, 28), 2018: (2, 16), 2019: (2, 5),
        2020: (1, 25), 2021: (2, 12), 2022: (2, 1), 2023: (1, 22),
        2024: (2, 10), 2025: (1, 29), 2026: (2, 17), 2027: (2, 6),
        2028: (1, 26), 2029: (2, 13), 2030: (2, 3),
    }
    if year in cny_dates:
        m, d = cny_dates[year]
        return datetime(year, m, d)
    return None


def _columbus_day(year):
    """Columbus Day: 2. Montag im Oktober."""
    from calendar import monthcalendar
    cal = monthcalendar(year, 10)
    mondays = [week[0] for week in cal if week[0] != 0]
    return datetime(year, 10, mondays[1])


def _yom_kippur(year):
    """
    Jom Kippur (ungefähre Daten, gregorianisch).
    Fällt zwischen September und Oktober.
    Hardcoded für 2000-2030.
    """
    yk_dates = {
        2000: (10, 9), 2001: (9, 27), 2002: (9, 16), 2003: (10, 6),
        2004: (9, 25), 2005: (10, 13), 2006: (10, 2), 2007: (9, 22),
        2008: (10, 9), 2009: (9, 28), 2010: (9, 18), 2011: (10, 8),
        2012: (9, 26), 2013: (9, 14), 2014: (10, 4), 2015: (9, 23),
        2016: (10, 12), 2017: (9, 30), 2018: (9, 19), 2019: (10, 9),
        2020: (9, 28), 2021: (9, 16), 2022: (10, 5), 2023: (9, 25),
        2024: (10, 12), 2025: (10, 2), 2026: (9, 21), 2027: (10, 11),
        2028: (9, 30), 2029: (9, 19), 2030: (10, 7),
    }
    if year in yk_dates:
        m, d = yk_dates[year]
        return datetime(year, m, d)
    return None


EXTRA_HOLIDAYS = {
    "Chinese New Year": {
        "calc": _chinese_new_year,
        "label": "Chinese New Year",
        "emoji": "🧧"
    },
    "Columbus Day": {
        "calc": _columbus_day,
        "label": "Columbus Day",
        "emoji": "⛵"
    },
    "Jom Kippur": {
        "calc": _yom_kippur,
        "label": "Yom Kippur",
        "emoji": "✡️"
    },
}


def get_extra_holidays(year):
    """Berechne die zusätzlichen Feiertage für ein Jahr."""
    results = []
    for name, defn in EXTRA_HOLIDAYS.items():
        try:
            dt = defn["calc"](year)
            if dt is None:
                continue
            results.append({
                "name": name,
                "date": pd.Timestamp(dt).normalize(),
                "label": defn["label"],
                "emoji": defn["emoji"]
            })
        except Exception:
            continue
    return results


# ══════════════════════════════════════════════════════════════
# VOLLMOND / NEUMOND (Moon Phases)
# ══════════════════════════════════════════════════════════════

def _moon_phase_dates(start_year=1990, end_year=2030):
    """
    Berechne Vollmond- und Neumond-Daten mit dem vereinfachten
    Meeus-Algorithmus. Genauigkeit: ±1 Tag.
    
    Returns:
        list of dict: [{date, phase: "full"/"new"}, ...]
    """
    results = []
    
    # Basis: Bekannter Neumond am 6. Jan 2000 (J2000.0)
    known_new_moon = datetime(2000, 1, 6, 18, 14)  # UTC
    synodic_month = 29.530588853  # Tage
    
    # Berechne Neumonde rückwärts und vorwärts
    base_jd = 2451550.1  # JD von known_new_moon
    
    # Finde den ersten Neumond vor start_year
    start_dt = datetime(start_year, 1, 1)
    delta_days = (start_dt - known_new_moon).days
    k_start = int(delta_days / synodic_month) - 1
    
    end_dt = datetime(end_year + 1, 1, 1)
    delta_days_end = (end_dt - known_new_moon).days
    k_end = int(delta_days_end / synodic_month) + 1
    
    for k in range(k_start, k_end + 1):
        # Neumond
        new_moon_days = k * synodic_month
        new_moon_dt = known_new_moon + pd.Timedelta(days=new_moon_days)
        
        if start_year <= new_moon_dt.year <= end_year:
            results.append({
                "date": pd.Timestamp(new_moon_dt.date()),
                "phase": "new"
            })
        
        # Vollmond = Neumond + halber synodischer Monat
        full_moon_days = new_moon_days + synodic_month / 2
        full_moon_dt = known_new_moon + pd.Timedelta(days=full_moon_days)
        
        if start_year <= full_moon_dt.year <= end_year:
            results.append({
                "date": pd.Timestamp(full_moon_dt.date()),
                "phase": "full"
            })
    
    # Sortieren und Duplikate entfernen
    results.sort(key=lambda x: x["date"])
    seen = set()
    unique = []
    for r in results:
        key = (r["date"], r["phase"])
        if key not in seen:
            seen.add(key)
            unique.append(r)
    
    return unique


def get_full_moon_dates(start_year=1990, end_year=2030):
    """Nur Vollmond-Daten."""
    return [r for r in _moon_phase_dates(start_year, end_year) if r["phase"] == "full"]


def get_new_moon_dates(start_year=1990, end_year=2030):
    """Nur Neumond-Daten."""
    return [r for r in _moon_phase_dates(start_year, end_year) if r["phase"] == "new"]


def get_all_moon_dates(start_year=1990, end_year=2030):
    """Alle Mond-Phasen (Voll + Neu)."""
    return _moon_phase_dates(start_year, end_year)


# ══════════════════════════════════════════════════════════════
# ZUSAMMENFASSUNG / REGISTRY
# ══════════════════════════════════════════════════════════════

CENTRAL_BANK_REGISTRY = {
    "Fed (FOMC)": {
        "module": "shared.fed_dates",
        "func": "get_fomc_dates",
        "emoji": "🇺🇸",
        "desc": "Federal Reserve - FOMC Statement"
    },
    "Fed Rate Change": {
        "func_local": get_fed_rate_changes,
        "emoji": "📈",
        "desc": "Fed Funds Rate Hikes & Cuts"
    },
    "Fed Minutes": {
        "func_local": get_fed_minutes_dates,
        "emoji": "📝",
        "desc": "FOMC Minutes Release"
    },
    "ECB": {
        "func_local": get_ecb_dates,
        "emoji": "🇪🇺",
        "desc": "European Central Bank"
    },
    "BOE": {
        "func_local": get_boe_dates,
        "emoji": "🇬🇧",
        "desc": "Bank of England MPC"
    },
    "BOJ": {
        "func_local": get_boj_dates,
        "emoji": "🇯🇵",
        "desc": "Bank of Japan"
    },
}

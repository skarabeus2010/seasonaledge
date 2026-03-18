# shared/strategies/kaeppel.py
# Jay Kaeppel Saisonalstrategien
# Quelle: "Seasonal Stock Market Trends" (2009) + Known Trend Index (KTI)
#
# Implementierte Strategien:
#   1. Ultimate Holiday System      — 6 Handelstage rund um jeden Marktfeiertag
#   2. Simple Monthly Seasonal      — Long nur in besten 4 Monaten (Nov, Dez, Apr, Jul)
#   3. Known Trend Index (KTI)      — Composite aus 5 Seasonal-Signalen (Score 0–5)
#   4. Election Cycle System        — Präsidentschaftszyklus Jahr 1–4
#   5. Years Ending in 5 Effect     — Dekadenzyklus (-5 Jahre)

import pandas as pd
import numpy as np
from datetime import date, timedelta
from typing import Optional


# ── Konstanten ─────────────────────────────────────────────────────────────────

# Kaeppel Simple Monthly Seasonal: Long-Monate
KAEPPEL_LONG_MONATE = [11, 12, 4, 7]   # Nov, Dez, Apr, Jul
KAEPPEL_LONG_MONATE_NAMEN = ["November", "Dezember", "April", "Juli"]

# KTI Score-Grenzen
KTI_AGGRESSIV_LONG  = 4   # ≥4 → 100–150% Equity
KTI_MODERAT_LONG    = 3   # ≥3 → 60–80% Equity
KTI_DEFENSIV        = 1   # ≤1 → Cash/Defensiv

# Holiday System: Tage vor/nach Feiertag
HOLIDAY_DAYS_BEFORE = 3
HOLIDAY_DAYS_AFTER  = 3

# KTI Farben
KTI_FARBEN = {
    "Aggressiv Long":  "#2ECC71",
    "Moderat Long":    "#F1C40F",
    "Neutral":         "#95A5A6",
    "Defensiv/Cash":   "#E74C3C",
}


# ── 1. Ultimate Holiday System ─────────────────────────────────────────────────

def get_holiday_windows(
    trading_days: pd.DatetimeIndex,
    holidays: list,
    days_before: int = HOLIDAY_DAYS_BEFORE,
    days_after:  int = HOLIDAY_DAYS_AFTER,
) -> list[dict]:
    """
    Berechnet die 6-Tage-Fenster (3 vor + 3 nach) rund um jeden Feiertag.

    Args:
        trading_days : Alle Handelstage als DatetimeIndex
        holidays     : Liste von date-Objekten (NYSE-Feiertage)
        days_before  : Handelstage VOR dem Feiertag (Standard: 3)
        days_after   : Handelstage NACH dem Feiertag (Standard: 3)

    Returns:
        Liste von dicts mit: holiday, window_start, window_end, trading_days_in_window
    """
    td_list = list(trading_days)
    windows = []

    for h in holidays:
        h_ts = pd.Timestamp(h)

        # Index des ersten Handelstags nach dem Feiertag
        after_idx = next(
            (i for i, d in enumerate(td_list) if d > h_ts), None
        )
        if after_idx is None:
            continue

        # Index des letzten Handelstags vor dem Feiertag
        before_idx = after_idx - 1
        if before_idx < 0:
            continue

        # Fenster: days_before VOR dem Feiertag
        start_idx = before_idx - days_before + 1
        # Fenster: days_after NACH dem Feiertag
        end_idx = after_idx + days_after - 1

        if start_idx < 0 or end_idx >= len(td_list):
            continue

        window_days = td_list[start_idx : end_idx + 1]
        windows.append({
            "holiday":                h,
            "holiday_name":           _get_holiday_name(h),
            "window_start":           window_days[0],
            "window_end":             window_days[-1],
            "trading_days_in_window": window_days,
            "total_days":             len(window_days),
        })

    return windows


def _get_holiday_name(h: date) -> str:
    """Gibt einen Kurznamen für bekannte US-Feiertage zurück (Best-Effort)."""
    month, day = h.month, h.day
    names = {
        (1, 1): "New Year's Day", (7, 4): "Independence Day",
        (12, 25): "Christmas",    (11, 11): "Veterans Day",
    }
    return names.get((month, day), f"{h.strftime('%b %d')}")


def is_in_holiday_window(
    check_date: pd.Timestamp,
    windows: list[dict],
) -> bool:
    """Prüft ob ein Datum in einem Holiday-Fenster liegt."""
    for w in windows:
        if w["window_start"] <= check_date <= w["window_end"]:
            return True
    return False


def backtest_holiday_system(
    df: pd.DataFrame,
    holidays_by_year: dict,
    days_before: int = HOLIDAY_DAYS_BEFORE,
    days_after:  int = HOLIDAY_DAYS_AFTER,
) -> pd.DataFrame:
    """
    Backtestet das Ultimate Holiday System.

    Args:
        df                : DataFrame mit DatetimeIndex, 'Open' und 'Close'
        holidays_by_year  : {year: [date, ...]} NYSE-Feiertage pro Jahr
        days_before       : Handelstage VOR Feiertag
        days_after        : Handelstage NACH Feiertag

    Returns:
        pd.DataFrame mit täglichen Signalen (in_window, rendite, kumuliert)
    """
    results = []

    for year, holidays in holidays_by_year.items():
        year_days = df[df.index.year == year]
        if len(year_days) == 0:
            continue

        windows = get_holiday_windows(year_days.index, holidays, days_before, days_after)

        for i in range(1, len(year_days)):
            today = year_days.index[i]
            prev  = year_days.index[i - 1]
            in_window = is_in_holiday_window(today, windows)
            rendite = (
                (year_days.loc[today, "Close"] - year_days.loc[prev, "Close"])
                / year_days.loc[prev, "Close"] * 100
                if in_window else 0.0
            )
            results.append({
                "date":      today,
                "in_window": in_window,
                "rendite_%": round(rendite, 4),
            })

    result_df = pd.DataFrame(results).set_index("date")
    result_df["kumuliert_%"] = (1 + result_df["rendite_%"] / 100).cumprod() * 100 - 100
    return result_df


# ── 2. Simple Monthly Seasonal ─────────────────────────────────────────────────

def is_kaeppel_long_month(month: int) -> bool:
    """Gibt True zurück wenn der Monat ein Kaeppel Long-Monat ist."""
    return month in KAEPPEL_LONG_MONATE


def get_monthly_seasonal_signal(current_date: pd.Timestamp) -> dict:
    """
    Gibt das aktuelle Simple Monthly Seasonal Signal zurück.

    Returns:
        dict mit: signal (str), monat (int), monat_name (str), ist_long_monat (bool)
    """
    monat = current_date.month
    ist_long = is_kaeppel_long_month(monat)
    monat_namen = [
        "", "Januar", "Februar", "März", "April", "Mai", "Juni",
        "Juli", "August", "September", "Oktober", "November", "Dezember"
    ]
    return {
        "signal":         "Long" if ist_long else "Flat",
        "monat":          monat,
        "monat_name":     monat_namen[monat],
        "ist_long_monat": ist_long,
        "long_monate":    KAEPPEL_LONG_MONATE_NAMEN,
    }


def backtest_simple_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """
    Backtestet die Simple Monthly Seasonal Strategie.
    Long nur in Nov, Dez, Apr, Jul — Flat sonst.

    Returns:
        pd.DataFrame mit täglichen Renditen (strategie vs. buy_hold)
    """
    daily_returns = df["Close"].pct_change() * 100
    strat_returns = daily_returns.where(
        df.index.month.isin(KAEPPEL_LONG_MONATE), other=0.0
    )

    result = pd.DataFrame({
        "rendite_bh_%":    daily_returns.round(4),
        "rendite_strat_%": strat_returns.round(4),
        "in_long_monat":   df.index.month.isin(KAEPPEL_LONG_MONATE),
    })
    result["kum_bh_%"]    = (1 + result["rendite_bh_%"] / 100).cumprod() * 100 - 100
    result["kum_strat_%"] = (1 + result["rendite_strat_%"] / 100).cumprod() * 100 - 100
    return result


# ── 3. Known Trend Index (KTI) ─────────────────────────────────────────────────

def calculate_kti_score(
    current_date: pd.Timestamp,
    df: pd.DataFrame,
    holidays_by_year: Optional[dict] = None,
    election_year: Optional[int] = None,
) -> dict:
    """
    Berechnet den KTI-Score (0–5) aus 5 Seasonal-Signalen.

    Komponenten:
        1. Holiday Effect    — aktuelles Datum in Holiday-Fenster?
        2. Turn-of-Month     — letzte 4 oder erste 3 Handelstage?
        3. Monthly Best Days — Kaeppel Long-Monat?
        4. Election Cycle    — Jahr 3 des Präsidentschaftszyklus?
        5. Decennial Cycle   — Jahr endet auf 5?

    Args:
        current_date      : Aktuelles Datum
        df                : DataFrame mit Kursdaten
        holidays_by_year  : {year: [date, ...]} für Holiday-Komponente
        election_year     : Letztes Wahljahr (z.B. 2024) für Election Cycle

    Returns:
        dict mit score (int), signal (str), farbe (str), komponenten (dict)
    """
    year  = current_date.year
    month = current_date.month

    komponenten = {}

    # 1. Holiday Effect
    if holidays_by_year and year in holidays_by_year:
        year_days = df[df.index.year == year]
        windows   = get_holiday_windows(year_days.index, holidays_by_year[year])
        komponenten["holiday_effect"] = is_in_holiday_window(current_date, windows)
    else:
        komponenten["holiday_effect"] = False

    # 2. Turn-of-Month (letzte 4 oder erste 3 Handelstage des Monats)
    komponenten["turn_of_month"] = _is_turn_of_month(current_date, df)

    # 3. Monthly Best Days (Kaeppel Long-Monat)
    komponenten["monthly_best_days"] = is_kaeppel_long_month(month)

    # 4. Election Cycle (Jahr 3 = Pre-Election Year ist bullish)
    if election_year:
        years_since = (year - election_year) % 4
        # Jahr 3 = Jahr vor Wahl (Pre-Election) → bullish
        # Jahr 2 = Mid-Term → neutral
        # Jahr 1 = Post-Election → schwach
        komponenten["election_cycle"] = (years_since == 3)
    else:
        komponenten["election_cycle"] = False

    # 5. Decennial Cycle (Jahr endet auf 5)
    komponenten["decennial_cycle"] = (year % 10 == 5)

    # Score berechnen
    score = sum(1 for v in komponenten.values() if v)

    # Signal
    if score >= KTI_AGGRESSIV_LONG:
        signal = "Aggressiv Long"
    elif score >= KTI_MODERAT_LONG:
        signal = "Moderat Long"
    elif score <= KTI_DEFENSIV:
        signal = "Defensiv/Cash"
    else:
        signal = "Neutral"

    return {
        "score":        score,
        "max_score":    5,
        "signal":       signal,
        "farbe":        KTI_FARBEN[signal],
        "komponenten":  komponenten,
        "datum":        current_date,
        "interpretation": _kti_interpretation(score),
    }


def _is_turn_of_month(current_date: pd.Timestamp, df: pd.DataFrame) -> bool:
    """Prüft ob das aktuelle Datum im Turn-of-Month-Fenster liegt."""
    year  = current_date.year
    month = current_date.month

    # Aktuelle Monathandelstage
    curr_mask  = (df.index.year == year) & (df.index.month == month)
    curr_days  = df.index[curr_mask]

    if len(curr_days) == 0:
        return False

    # Vormonat-Handelstage
    prev_month = month - 1 if month > 1 else 12
    prev_year  = year if month > 1 else year - 1
    prev_mask  = (df.index.year == prev_year) & (df.index.month == prev_month)
    prev_days  = df.index[prev_mask]

    tom_days = set()
    # Letzte 4 Handelstage des Vormonats
    if len(prev_days) >= 4:
        tom_days.update(prev_days[-4:])
    # Erste 3 Handelstage des aktuellen Monats
    if len(curr_days) >= 3:
        tom_days.update(curr_days[:3])

    return current_date in tom_days


def _kti_interpretation(score: int) -> str:
    """Gibt eine Interpretation des KTI-Scores zurück."""
    texte = {
        5: "Maximale Konfluenz — alle 5 Seasonal-Signale bullish (100–150% Equity)",
        4: "Starke Konfluenz — 4 von 5 Signale bullish (aggressiv long)",
        3: "Moderate Konfluenz — 3 von 5 Signale bullish (moderat long, 60–80%)",
        2: "Schwache Konfluenz — 2 von 5 Signale bullish (neutral)",
        1: "Kaum Unterstützung — nur 1 Signal bullish (defensiv / Cash)",
        0: "Keine Konfluenz — alle Signale neutral/bearish (Cash/Defensiv)",
    }
    return texte.get(score, "Unbekannt")


# ── 4. Election Cycle System ───────────────────────────────────────────────────

def get_election_cycle_year(year: int, last_election_year: int = 2024) -> dict:
    """
    Bestimmt das Präsidentschaftszyklus-Jahr (1–4) und das Signal.

    Jahr 1 = Post-Election (schwach)
    Jahr 2 = Mid-Term (volatile)
    Jahr 3 = Pre-Election (stark, bullish)
    Jahr 4 = Election Year (gemischt)

    Args:
        year               : Zu analysierendes Jahr
        last_election_year : Letztes Wahljahr (Standard: 2024)

    Returns:
        dict mit zyklus_jahr (1–4), signal, interpretation
    """
    zyklus_jahr = ((year - last_election_year) % 4) + 1

    signale = {
        1: ("Schwach",   "#E74C3C", "Post-Election: Historisch schwächstes Jahr"),
        2: ("Volatil",   "#E67E22", "Mid-Term: Erhöhte Volatilität, oft Jahrestief"),
        3: ("Bullish",   "#2ECC71", "Pre-Election: Stärkstes Jahr im Zyklus"),
        4: ("Gemischt",  "#F1C40F", "Election Year: Gut bis Herbst, dann unsicher"),
    }
    signal, farbe, interpretation = signale[zyklus_jahr]

    return {
        "jahr":           year,
        "zyklus_jahr":    zyklus_jahr,
        "signal":         signal,
        "farbe":          farbe,
        "interpretation": interpretation,
        "ist_bullish":    zyklus_jahr == 3,
    }


# ── 5. Years Ending in 5 Effect ────────────────────────────────────────────────

def check_decennial_5_effect(year: int) -> dict:
    """
    Prüft den 'Years Ending in 5' Effekt (Dekadenzyklus).

    Args:
        year : Zu analysierendes Jahr

    Returns:
        dict mit ist_5er_jahr (bool), signal, rendite_historisch
    """
    ist_5er = (year % 10 == 5)
    return {
        "jahr":                year,
        "letzte_ziffer":       year % 10,
        "ist_5er_jahr":        ist_5er,
        "signal":              "Extra Long" if ist_5er else "Normal",
        "farbe":               "#2ECC71" if ist_5er else "#95A5A6",
        "interpretation": (
            f"{year} endet auf 5 → historisch sehr bullish (Kaeppel Decennial Cycle)"
            if ist_5er else
            f"{year} endet auf {year % 10} → kein besonderer Dekaden-Effekt"
        ),
    }


# ── Jahres-Übersicht ───────────────────────────────────────────────────────────

def get_kaeppel_year_summary(
    year: int,
    last_election_year: int = 2024,
) -> dict:
    """
    Gibt eine Zusammenfassung aller Kaeppel-Jahressignale zurück.

    Args:
        year               : Zu analysierendes Jahr
        last_election_year : Letztes US-Wahljahr

    Returns:
        dict mit allen Kaeppel-Jahressignalen
    """
    election  = get_election_cycle_year(year, last_election_year)
    decennial = check_decennial_5_effect(year)

    # Bullish-Score (0–2 Jahressignale)
    bullish_count = sum([
        election["ist_bullish"],
        decennial["ist_5er_jahr"],
    ])

    return {
        "jahr":             year,
        "election_cycle":   election,
        "decennial_5":      decennial,
        "long_monate":      KAEPPEL_LONG_MONATE,
        "long_monate_namen": KAEPPEL_LONG_MONATE_NAMEN,
        "jahres_bullish_score": bullish_count,
        "jahres_signal": (
            "Sehr Bullish" if bullish_count == 2 else
            "Leicht Bullish" if bullish_count == 1 else
            "Neutral"
        ),
    }

"""
shared/strategies/plain_vanilla.py — 10 Plain Vanilla Saisonale Strategien
==========================================================================
Jede Strategie: calc_NAME(df) → list[dict] mit Trades.
Kein Streamlit-Import! Reine Berechnung.

Trade-Format:
    {"entry_date": pd.Timestamp, "exit_date": pd.Timestamp,
     "entry_price": float, "exit_price": float, "return_pct": float}
"""

import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional


# ══════════════════════════════════════════════════════════════
# HILFSFUNKTIONEN
# ══════════════════════════════════════════════════════════════

def _get_trading_days(df: pd.DataFrame, year: int, month: int) -> pd.DatetimeIndex:
    """Alle Handelstage eines Monats."""
    mask = (df.index.year == year) & (df.index.month == month)
    return df[mask].index.sort_values()


def _nth_trading_day(df, year, month, n):
    """n-ter Handelstag im Monat (1-basiert). None wenn nicht vorhanden."""
    days = _get_trading_days(df, year, month)
    if len(days) >= n:
        return days[n - 1]
    return None


def _last_trading_day(df, year, month):
    """Letzter Handelstag im Monat."""
    days = _get_trading_days(df, year, month)
    return days[-1] if len(days) > 0 else None


def _nth_last_trading_day(df, year, month, n):
    """n-ter vorletzter Handelstag (1 = letzter, 2 = vorletzter)."""
    days = _get_trading_days(df, year, month)
    if len(days) >= n:
        return days[-n]
    return None


def _nearest_trading_day(df, target_date, direction="forward"):
    """Nächster Handelstag an/nach (forward) oder an/vor (backward) einem Datum."""
    ts = pd.Timestamp(target_date)
    if direction == "forward":
        candidates = df[df.index >= ts]
        return candidates.index[0] if len(candidates) > 0 else None
    else:
        candidates = df[df.index <= ts]
        return candidates.index[-1] if len(candidates) > 0 else None


def _make_trade(df, entry_date, exit_date):
    """Erstellt Trade-Dict aus Entry/Exit Daten."""
    if entry_date is None or exit_date is None:
        return None
    if entry_date not in df.index or exit_date not in df.index:
        return None
    if exit_date <= entry_date:
        return None
    p_entry = float(df.loc[entry_date, "Close"])
    p_exit = float(df.loc[exit_date, "Close"])
    if p_entry <= 0:
        return None
    return {
        "entry_date": entry_date,
        "exit_date": exit_date,
        "entry_price": round(p_entry, 2),
        "exit_price": round(p_exit, 2),
        "return_pct": round((p_exit - p_entry) / p_entry * 100, 4),
    }


# ══════════════════════════════════════════════════════════════
# STRATEGIE 1: SELL IN MAY (Halloween-Effekt)
# ══════════════════════════════════════════════════════════════

def calc_sell_in_may(df: pd.DataFrame) -> list[dict]:
    """
    Einstieg: Letzter Handelstag Oktober (Close).
    Ausstieg: 3. Handelstag Mai Folgejahr (Close).
    """
    trades = []
    years = sorted(df.index.year.unique())
    for year in years:
        entry = _last_trading_day(df, year, 10)
        exit_d = _nth_trading_day(df, year + 1, 5, 3)
        trade = _make_trade(df, entry, exit_d)
        if trade:
            trades.append(trade)
    return trades


# ══════════════════════════════════════════════════════════════
# STRATEGIE 2: LBR-GEFILTERTE NOVEMBER-MAI
# ══════════════════════════════════════════════════════════════

def calc_lbr_november_mai(df: pd.DataFrame) -> list[dict]:
    """
    Einstieg: Ab 1. Oktober, sobald LBR Histogramm > 0.
    Ausstieg: Ab 1. April, sobald LBR Histogramm < 0.
    """
    from shared.indicators import calc_lbr

    lbr = calc_lbr(df["Close"])
    hist = lbr["histogram"]
    trades = []
    years = sorted(df.index.year.unique())

    for year in years:
        # Entry: Erster Tag ab 1. Oktober mit LBR > 0
        oct_start = _nearest_trading_day(df, date(year, 10, 1))
        if oct_start is None:
            continue
        entry = None
        for d in df[df.index >= oct_start].index:
            if d.month > 12 or (d.month >= 4 and d.year > year):
                break
            if d in hist.index and hist.loc[d] > 0:
                entry = d
                break

        if entry is None:
            continue

        # Exit: Erster Tag ab 1. April Folgejahr mit LBR < 0
        apr_start = _nearest_trading_day(df, date(year + 1, 4, 1))
        if apr_start is None:
            continue
        exit_d = None
        for d in df[df.index >= apr_start].index:
            if d.month > 6:
                break
            if d in hist.index and hist.loc[d] < 0:
                exit_d = d
                break

        trade = _make_trade(df, entry, exit_d)
        if trade:
            trades.append(trade)
    return trades


# ══════════════════════════════════════════════════════════════
# STRATEGIE 3: NASDAQ-TREND (November bis Juni)
# ══════════════════════════════════════════════════════════════

def calc_nasdaq_trend(df: pd.DataFrame) -> list[dict]:
    """
    Einstieg: Letzter Handelstag Oktober (Close).
    Ausstieg: Letzter Handelstag Juni Folgejahr (Close).
    """
    trades = []
    years = sorted(df.index.year.unique())
    for year in years:
        entry = _last_trading_day(df, year, 10)
        exit_d = _last_trading_day(df, year + 1, 6)
        trade = _make_trade(df, entry, exit_d)
        if trade:
            trades.append(trade)
    return trades


# ══════════════════════════════════════════════════════════════
# STRATEGIE 4: MONTH-END MUSTER
# ══════════════════════════════════════════════════════════════

def calc_month_end(df: pd.DataFrame) -> list[dict]:
    """
    Einstieg: Vorletzter Handelstag des Monats (Close).
    Ausstieg: 4. Handelstag des Folgemonats (Close).
    """
    trades = []
    years = sorted(df.index.year.unique())
    for year in years:
        for month in range(1, 13):
            entry = _nth_last_trading_day(df, year, month, 2)
            # Folgemonat
            next_year = year + 1 if month == 12 else year
            next_month = 1 if month == 12 else month + 1
            exit_d = _nth_trading_day(df, next_year, next_month, 4)
            trade = _make_trade(df, entry, exit_d)
            if trade:
                trades.append(trade)
    return trades


# ══════════════════════════════════════════════════════════════
# STRATEGIE 5: MONTHLY 10 SYSTEM
# ══════════════════════════════════════════════════════════════

def calc_monthly_10(df: pd.DataFrame) -> list[dict]:
    """
    Investiert an: TDOM 1-4, 9-12, und letzte 2 TDOM.
    Cash an allen anderen Tagen.
    Berechnung: Tägliche Close-to-Close Returns nur an aktiven Tagen.
    """
    from shared.tdom_analysis import add_tdom_columns

    df2 = add_tdom_columns(df.copy())
    df2["daily_ret"] = df2["Close"].pct_change()

    trades = []
    years = sorted(df2.index.year.unique())

    for year in years:
        for month in range(1, 13):
            month_df = df2[(df2["year"] == year) & (df2["month"] == month)].copy()
            if len(month_df) < 10:
                continue

            max_tdom = int(month_df["tdom"].max())

            # Aktive TDOMs: 1-4, 9-12, letzte 2
            active_tdoms = set(range(1, 5)) | set(range(9, 13))
            active_tdoms.add(max_tdom)
            active_tdoms.add(max_tdom - 1)

            # Finde zusammenhängende Blöcke
            sorted_tdoms = sorted(active_tdoms)
            blocks = []
            block_start = sorted_tdoms[0]
            prev = sorted_tdoms[0]
            for t in sorted_tdoms[1:]:
                if t != prev + 1:
                    blocks.append((block_start, prev))
                    block_start = t
                prev = t
            blocks.append((block_start, prev))

            for start_tdom, end_tdom in blocks:
                entry_rows = month_df[month_df["tdom"] == start_tdom]
                exit_rows = month_df[month_df["tdom"] == end_tdom]
                if len(entry_rows) > 0 and len(exit_rows) > 0:
                    trade = _make_trade(df, entry_rows.index[0], exit_rows.index[0])
                    if trade:
                        trades.append(trade)

    return trades


# ══════════════════════════════════════════════════════════════
# STRATEGIE 6: SANTA CLAUS RALLYE (Erweitert)
# ══════════════════════════════════════════════════════════════

def _get_thanksgiving(year):
    """4. Donnerstag im November."""
    nov1 = date(year, 11, 1)
    # Erster Donnerstag
    first_thu = nov1 + timedelta(days=(3 - nov1.weekday()) % 7)
    # 4. Donnerstag
    return first_thu + timedelta(weeks=3)


def calc_santa_claus(df: pd.DataFrame) -> list[dict]:
    """
    Einstieg: 3. TDOM vor Thanksgiving (Close).
    Ausstieg: 5. TDOM im Januar Folgejahr (Close).
    """
    trades = []
    years = sorted(df.index.year.unique())

    for year in years:
        thanksgiving = _get_thanksgiving(year)
        # 3 Handelstage VOR Thanksgiving
        before_thx = df[df.index < pd.Timestamp(thanksgiving)]
        if len(before_thx) < 3:
            continue
        entry = before_thx.index[-3]

        # 5. Handelstag im Januar Folgejahr
        exit_d = _nth_trading_day(df, year + 1, 1, 5)
        trade = _make_trade(df, entry, exit_d)
        if trade:
            trades.append(trade)
    return trades


# ══════════════════════════════════════════════════════════════
# STRATEGIE 7: 212-WOCHEN-ZYKLUS
# ══════════════════════════════════════════════════════════════

def calc_212_week_cycle(df: pd.DataFrame) -> list[dict]:
    """
    Einstieg: Alle 1.484 Kalendertage (ab 16. Mai 1938).
    Ausstieg: 6 Monate (182 Tage) später.
    """
    trades = []
    cycle_start = date(1938, 5, 16)
    cycle_days = 1484
    hold_days = 182

    df_start = df.index[0].date() if len(df) > 0 else date(2000, 1, 1)
    df_end = df.index[-1].date() if len(df) > 0 else date(2026, 1, 1)

    # Finde den ersten Zyklus-Entry nach Datenstart
    current = cycle_start
    while current < df_start:
        current += timedelta(days=cycle_days)

    while current < df_end:
        entry = _nearest_trading_day(df, current)
        exit_date = current + timedelta(days=hold_days)
        exit_d = _nearest_trading_day(df, exit_date)
        trade = _make_trade(df, entry, exit_d)
        if trade:
            trades.append(trade)
        current += timedelta(days=cycle_days)

    return trades


# ══════════════════════════════════════════════════════════════
# STRATEGIE 8: 40-WOCHEN-ZYKLUS (Bullische Phase)
# ══════════════════════════════════════════════════════════════

def calc_40_week_cycle(df: pd.DataFrame) -> list[dict]:
    """
    Einstieg: 280-Tage-Zyklus (ab 21. April 1967).
    Ausstieg: 140 Tage später (erste Hälfte = bullische Phase).
    """
    trades = []
    cycle_start = date(1967, 4, 21)
    cycle_days = 280
    hold_days = 140

    df_start = df.index[0].date() if len(df) > 0 else date(2000, 1, 1)
    df_end = df.index[-1].date() if len(df) > 0 else date(2026, 1, 1)

    current = cycle_start
    while current < df_start:
        current += timedelta(days=cycle_days)

    while current < df_end:
        entry = _nearest_trading_day(df, current)
        exit_date = current + timedelta(days=hold_days)
        exit_d = _nearest_trading_day(df, exit_date)
        trade = _make_trade(df, entry, exit_d)
        if trade:
            trades.append(trade)
        current += timedelta(days=cycle_days)

    return trades


# ══════════════════════════════════════════════════════════════
# STRATEGIE 9: MIDTERM ELECTION TRADE
# ══════════════════════════════════════════════════════════════

def _get_election_day(year):
    """Erster Dienstag nach dem ersten Montag im November."""
    nov1 = date(year, 11, 1)
    first_monday = nov1 + timedelta(days=(0 - nov1.weekday()) % 7)
    return first_monday + timedelta(days=1)


def calc_midterm_election(df: pd.DataFrame) -> list[dict]:
    """
    Einstieg: 5 Handelstage vor der Midterm-Wahl (Close).
    Ausstieg: 3 Handelstage nach der Wahl (Close).
    """
    from shared.calculations import get_presidential_cycle_year

    trades = []
    years = sorted(df.index.year.unique())

    for year in years:
        if get_presidential_cycle_year(year) != "Year 2 (Midterm Election)":
            continue

        election = _get_election_day(year)
        election_ts = pd.Timestamp(election)

        # 5 Handelstage VOR der Wahl
        before = df[df.index < election_ts]
        if len(before) < 5:
            continue
        entry = before.index[-5]

        # 3 Handelstage NACH der Wahl
        after = df[df.index > election_ts]
        if len(after) < 3:
            continue
        exit_d = after.index[2]

        trade = _make_trade(df, entry, exit_d)
        if trade:
            trades.append(trade)

    return trades


# ══════════════════════════════════════════════════════════════
# STRATEGIE 10: SEPTEMBER-VERMEIDUNG
# ══════════════════════════════════════════════════════════════

def calc_september_avoid(df: pd.DataFrame) -> list[dict]:
    """
    Einstieg: 30. September (nächster Handelstag, Close).
    Ausstieg: 31. August Folgejahr (nächster Handelstag, Close).
    Investiert 11 Monate, Cash im September.
    """
    trades = []
    years = sorted(df.index.year.unique())
    for year in years:
        entry = _nearest_trading_day(df, date(year, 9, 30))
        exit_d = _nearest_trading_day(df, date(year + 1, 8, 31), direction="backward")
        trade = _make_trade(df, entry, exit_d)
        if trade:
            trades.append(trade)
    return trades


# ══════════════════════════════════════════════════════════════
# STRATEGIE 11: ULTIMATE MONTHLY DAYS SYSTEM
# ══════════════════════════════════════════════════════════════

# 8 große US-Börsenfeiertage (ohne MLK)
_US_HOLIDAYS_MONTH_DAY = [
    (1, 1),   # New Year's Day
    (2, 15),  # Presidents' Day (ca.)
    (5, 25),  # Memorial Day (ca.)
    (7, 4),   # Independence Day
    (9, 1),   # Labor Day (ca.)
    (11, 25), # Thanksgiving (ca.)
    (12, 25), # Christmas
    (4, 10),  # Good Friday (ca.)
]


def _is_near_holiday(dt, df, days_before=1):
    """Prüft ob ein Tag innerhalb von days_before HT vor einem Feiertag liegt."""
    year = dt.year
    for m, d in _US_HOLIDAYS_MONTH_DAY:
        try:
            hol = _nearest_trading_day(df, date(year, m, d))
            if hol is None:
                continue
            # Handelstage vor dem Feiertag
            before = df[df.index < hol]
            if len(before) >= days_before:
                window_start = before.index[-days_before]
                if window_start <= dt <= hol:
                    return True
        except Exception:
            continue
    return False


def calc_ultimate_monthly(df: pd.DataFrame) -> list[dict]:
    """
    Ultimate Monthly Days System:
    - HT vor 8 Börsenfeiertagen
    - TDOM 1-4, 9-12, letzte 2
    - Thanksgiving bis 5. Januar
    Investiert an aktiven Tagen, Cash an allen anderen.
    """
    from shared.tdom_analysis import add_tdom_columns

    df2 = add_tdom_columns(df.copy())
    if "month" not in df2.columns:
        df2["month"] = df2.index.month

    trades = []
    years = sorted(df2.index.year.unique())

    for year in years:
        year_df = df2[df2.index.year == year].copy()
        if len(year_df) < 50:
            continue

        # Santa-Claus-Phase: Thanksgiving bis 5. Jan
        thanksgiving = _get_thanksgiving(year)
        thx_ts = pd.Timestamp(thanksgiving)
        before_thx = df2[df2.index < thx_ts]
        santa_start = before_thx.index[-3] if len(before_thx) >= 3 else None
        jan5_next = _nth_trading_day(df2, year + 1, 1, 5)

        # Markiere aktive Tage
        active_dates = set()

        for idx, row in year_df.iterrows():
            tdom = int(row["tdom"])
            max_tdom = int(year_df[year_df["month"] == row["month"]]["tdom"].max())
            is_active = False

            # TDOM 1-4, 9-12, letzte 2
            if tdom <= 4 or (9 <= tdom <= 12) or tdom >= max_tdom - 1:
                is_active = True

            # Vor Feiertag
            if _is_near_holiday(idx, df2, days_before=1):
                is_active = True

            # Santa-Claus Phase
            if santa_start and jan5_next:
                if santa_start <= idx <= jan5_next:
                    is_active = True

            if is_active:
                active_dates.add(idx)

        # Jan nächstes Jahr (Santa-Phase)
        if jan5_next:
            jan_df = df2[(df2.index.year == year + 1) & (df2.index.month == 1)]
            for idx in jan_df.index:
                if idx <= jan5_next:
                    active_dates.add(idx)

        # Zusammenhängende Blöcke bilden
        sorted_dates = sorted(active_dates)
        if not sorted_dates:
            continue

        block_start = sorted_dates[0]
        prev = sorted_dates[0]
        for d in sorted_dates[1:]:
            # Gap > 1 Handelstag → neuer Block
            gap = len(df2[(df2.index > prev) & (df2.index < d)])
            if gap > 0:
                trade = _make_trade(df, block_start, prev)
                if trade:
                    trades.append(trade)
                block_start = d
            prev = d
        # Letzter Block
        trade = _make_trade(df, block_start, prev)
        if trade:
            trades.append(trade)

    return trades


# ══════════════════════════════════════════════════════════════
# STRATEGIE 12/13: KTI-SYSTEM (Known Trends Index)
# ══════════════════════════════════════════════════════════════

def _compute_kti_daily(df: pd.DataFrame) -> pd.Series:
    """
    Berechnet den KTI-Score (0-14) für jeden Handelstag.
    Vektorisiert für Performance (~1s statt Minuten).
    """
    from shared.tdom_analysis import add_tdom_columns
    from shared.calculations import get_presidential_cycle_year

    df2 = add_tdom_columns(df.copy())
    if "month" not in df2.columns:
        df2["month"] = df2.index.month
    if "year" not in df2.columns:
        df2["year"] = df2.index.year

    kti = pd.Series(0, index=df2.index, dtype=int)
    month = df2["month"]
    year = df2["year"]
    tdom = df2["tdom"]
    decade_digit = year % 10

    # Max TDOM pro Monat (vektorisiert)
    max_tdom = df2.groupby([year, month])["tdom"].transform("max")

    # 1. Monatstage: TDOM 1-4, 9-12, letzter, vorletzter
    kti += ((tdom <= 4) | ((tdom >= 9) & (tdom <= 12)) | (tdom >= max_tdom - 1)).astype(int)

    # 2. November bis Mai
    kti += ((month >= 11) | (month <= 4) | ((month == 5) & (tdom <= 3))).astype(int)

    # 3. Sommer-Rallye
    kti += (((month == 6) & (tdom >= max_tdom - 2)) | ((month == 7) & (tdom <= 9))).astype(int)

    # 4. September-Effekt
    kti -= (month == 9).astype(int)

    # 5-8. Wahlzyklus (vektorisiert)
    cycle = year.map(get_presidential_cycle_year)

    # 5. Okt Midterm bis Sep Vorwahljahr
    kti += (((cycle == "Year 2 (Midterm Election)") & (month >= 10)) |
            ((cycle == "Year 3 (Pre-Election)") & (month <= 9))).astype(int)

    # 6. Nov-Dez Vorwahljahr
    kti += ((cycle == "Year 3 (Pre-Election)") & (month >= 11)).astype(int)

    # 7. Jun-Dez Wahljahr
    kti += ((cycle == "Year 4 (Election Year)") & (month >= 6)).astype(int)

    # 8. Mär-Jul Vorwahljahr
    kti += ((cycle == "Year 3 (Pre-Election)") & (month >= 3) & (month <= 7)).astype(int)

    # 9. Midterm-Wahl: 5 HT vor bis 3 HT nach (markiere Fenster)
    midterm_years = [y for y in year.unique() if get_presidential_cycle_year(y) == "Year 2 (Midterm Election)"]
    for y in midterm_years:
        try:
            el = _get_election_day(y)
            el_ts = pd.Timestamp(el)
            before = df2[df2.index < el_ts]
            after = df2[df2.index > el_ts]
            if len(before) >= 5 and len(after) >= 3:
                win_start, win_end = before.index[-5], after.index[2]
                mask = (df2.index >= win_start) & (df2.index <= win_end)
                kti.loc[mask] += 1
        except Exception:
            pass

    # 10. 40-Wochen-Zyklus
    _ref_40w = pd.Timestamp(date(1967, 4, 21))
    _days_since_40 = (df2.index - _ref_40w).days
    _pos_40 = _days_since_40 % 280
    kti += ((_days_since_40 >= 0) & (_pos_40 < 140)).astype(int)

    # 11. 212-Wochen-Zyklus
    _ref_212w = pd.Timestamp(date(1938, 5, 16))
    _days_since_212 = (df2.index - _ref_212w).days
    _pos_212 = _days_since_212 % 1484
    kti += ((_days_since_212 >= 0) & (_pos_212 < 182)).astype(int)

    # 12. Dekaden: Okt x4 bis Mär x6
    kti += (((decade_digit == 4) & (month >= 10)) | (decade_digit == 5) |
            ((decade_digit == 6) & (month <= 3))).astype(int)

    # 13. Dekaden: Mär x8 bis Sep x9
    kti += (((decade_digit == 8) & (month >= 3)) | ((decade_digit == 9) & (month <= 9))).astype(int)

    # 14. 20-Jahres-Zyklus
    _even_decade = ((year // 10) % 2 == 0)
    kti += ((_even_decade & (decade_digit == 2) & (month >= 10)) |
            (_even_decade & (decade_digit >= 3) & (decade_digit <= 4)) |
            (_even_decade & (decade_digit == 5))).astype(int)

    # 15. Feiertage: Vereinfacht — 3 HT vor festen Terminen
    for m, d in _US_HOLIDAYS_MONTH_DAY:
        for y in year.unique():
            try:
                hol = _nearest_trading_day(df2, date(int(y), m, d))
                if hol is None:
                    continue
                before = df2[df2.index <= hol]
                if len(before) >= 4:
                    win_start = before.index[-4]
                    mask = (df2.index >= win_start) & (df2.index <= hol)
                    kti.loc[mask] += 1
            except Exception:
                pass

    return kti


def calc_kti_long_only(df: pd.DataFrame) -> list[dict]:
    """
    KTI Long-Only: Investiert wenn KTI >= 3, Cash wenn < 3.
    """
    kti = _compute_kti_daily(df)
    trades = []
    in_trade = False
    entry_date = None

    for idx in kti.index:
        if not in_trade and kti.loc[idx] >= 3:
            entry_date = idx
            in_trade = True
        elif in_trade and kti.loc[idx] < 3:
            trade = _make_trade(df, entry_date, idx)
            if trade:
                trades.append(trade)
            in_trade = False

    # Offener Trade am Ende
    if in_trade and entry_date is not None:
        trade = _make_trade(df, entry_date, kti.index[-1])
        if trade:
            trades.append(trade)

    return trades


def calc_kti_leveraged(df: pd.DataFrame) -> list[dict]:
    """
    KTI Long + Leverage: KTI >= 5 → 2x Hebel, KTI 3-4 → 1x, < 3 → Cash.
    Returns Trades mit 'leverage' Feld.
    """
    kti = _compute_kti_daily(df)
    trades = []
    in_trade = False
    entry_date = None
    current_leverage = 0

    for idx in kti.index:
        score = kti.loc[idx]
        new_leverage = 2 if score >= 5 else (1 if score >= 3 else 0)

        if current_leverage == 0 and new_leverage > 0:
            # Neuer Einstieg
            entry_date = idx
            in_trade = True
            current_leverage = new_leverage
        elif current_leverage > 0 and new_leverage == 0:
            # Ausstieg
            trade = _make_trade(df, entry_date, idx)
            if trade:
                # Durchschnittlichen Leverage für den Trade berechnen
                window_kti = kti.loc[entry_date:idx]
                avg_lev = window_kti.apply(lambda s: 2 if s >= 5 else (1 if s >= 3 else 0)).mean()
                trade["return_pct"] = round(trade["return_pct"] * avg_lev, 4)
                trade["leverage"] = round(avg_lev, 1)
                trades.append(trade)
            in_trade = False
            current_leverage = 0
        else:
            current_leverage = new_leverage

    if in_trade and entry_date is not None:
        trade = _make_trade(df, entry_date, kti.index[-1])
        if trade:
            window_kti = kti.loc[entry_date:kti.index[-1]]
            avg_lev = window_kti.apply(lambda s: 2 if s >= 5 else (1 if s >= 3 else 0)).mean()
            trade["return_pct"] = round(trade["return_pct"] * avg_lev, 4)
            trade["leverage"] = round(avg_lev, 1)
            trades.append(trade)

    return trades


# ══════════════════════════════════════════════════════════════
# STRATEGIE 14: ULTIMATE ELECTION CYCLE SYSTEM (UECS)
# ══════════════════════════════════════════════════════════════

def calc_uecs(df: pd.DataFrame) -> list[dict]:
    """
    Ultimate Election Cycle System — Mehrere Zeitfenster im 4-Jahres-Zyklus.

    Investiert in folgenden Phasen:
    1. 5 Tage vor bis 3 Tage nach Midterm-Wahl
    2. März bis Juli des Vorwahljahres (Pre-Election Year 3)
    3. Oktober Midterm bis September Vorwahljahr
    4. November + Dezember des Vorwahljahres
    5. Juni bis Dezember des Wahljahres (Election Year 4)
    6. Gesamtes Post-Election Jahr (Year 1), wenn es auf "5" endet (Dekade)
    """
    from shared.calculations import get_presidential_cycle_year

    trades = []
    years = sorted(df.index.year.unique())

    for year in years:
        cycle = get_presidential_cycle_year(year)

        # ── Phase 1: Midterm-Wahl (Year 2) — 5 HT vor bis 3 HT nach ──
        if cycle == "Year 2 (Midterm Election)":
            election = _get_election_day(year)
            election_ts = pd.Timestamp(election)
            before = df[df.index < election_ts]
            after = df[df.index > election_ts]
            if len(before) >= 5 and len(after) >= 3:
                trade = _make_trade(df, before.index[-5], after.index[2])
                if trade:
                    trades.append(trade)

        # ── Phase 2: März bis Juli des Vorwahljahres (Year 3) ──
        if cycle == "Year 3 (Pre-Election)":
            entry = _nth_trading_day(df, year, 3, 1)  # 1. HT März
            exit_d = _last_trading_day(df, year, 7)    # Letzter HT Juli
            trade = _make_trade(df, entry, exit_d)
            if trade:
                trades.append(trade)

        # ── Phase 3: Oktober Midterm bis September Vorwahljahr ──
        if cycle == "Year 2 (Midterm Election)":
            entry = _nth_trading_day(df, year, 10, 1)      # 1. HT Oktober Midterm
            exit_d = _last_trading_day(df, year + 1, 9)    # Letzter HT September Vorwahljahr
            trade = _make_trade(df, entry, exit_d)
            if trade:
                trades.append(trade)

        # ── Phase 4: November + Dezember des Vorwahljahres (Year 3) ──
        if cycle == "Year 3 (Pre-Election)":
            entry = _nth_trading_day(df, year, 11, 1)  # 1. HT November
            exit_d = _last_trading_day(df, year, 12)   # Letzter HT Dezember
            trade = _make_trade(df, entry, exit_d)
            if trade:
                trades.append(trade)

        # ── Phase 5: Juni bis Dezember des Wahljahres (Year 4) ──
        if cycle == "Year 4 (Election Year)":
            entry = _nth_trading_day(df, year, 6, 1)   # 1. HT Juni
            exit_d = _last_trading_day(df, year, 12)   # Letzter HT Dezember
            trade = _make_trade(df, entry, exit_d)
            if trade:
                trades.append(trade)

        # ── Phase 6: Gesamtes Post-Election Jahr (Year 1), wenn auf "5" endend ──
        if cycle == "Year 1 (Post-Election)" and year % 10 == 5:
            entry = _nth_trading_day(df, year, 1, 1)   # 1. HT Januar
            exit_d = _last_trading_day(df, year, 12)   # Letzter HT Dezember
            trade = _make_trade(df, entry, exit_d)
            if trade:
                trades.append(trade)

    # Chronologisch sortieren und überlappende Trades entfernen
    trades.sort(key=lambda t: t["entry_date"])
    cleaned = []
    for t in trades:
        if cleaned and t["entry_date"] < cleaned[-1]["exit_date"]:
            # Überlappung: Merge — behalte den längeren
            if t["exit_date"] > cleaned[-1]["exit_date"]:
                cleaned[-1]["exit_date"] = t["exit_date"]
                cleaned[-1]["exit_price"] = t["exit_price"]
                cleaned[-1]["return_pct"] = round(
                    (cleaned[-1]["exit_price"] - cleaned[-1]["entry_price"]) / cleaned[-1]["entry_price"] * 100, 4
                )
        else:
            cleaned.append(t)

    return cleaned


# ══════════════════════════════════════════════════════════════
# PORTFOLIO & STATISTIK
# ══════════════════════════════════════════════════════════════

def apply_stop_loss(df, trades, stop_pct, stop_type="fixed"):
    """Wendet Stop-Loss auf alle Trades an. Returns: modifizierte Trades."""
    if stop_pct <= 0:
        return trades

    result = []
    for t in trades:
        entry_price = t["entry_price"]
        entry_date = t["entry_date"]
        exit_date = t["exit_date"]

        window = df[(df.index >= entry_date) & (df.index <= exit_date)]
        if len(window) < 2:
            result.append(t)
            continue

        stopped = False
        high_watermark = entry_price

        for i, (idx, row) in enumerate(window.iterrows()):
            if i == 0:
                continue

            if stop_type == "trailing":
                high_watermark = max(high_watermark, float(row["High"]))
                stop_price = high_watermark * (1 - stop_pct / 100)
            else:
                stop_price = entry_price * (1 - stop_pct / 100)

            if float(row["Low"]) <= stop_price:
                actual_exit = min(stop_price, float(row["Open"]))
                ret = (actual_exit - entry_price) / entry_price * 100
                result.append({
                    "entry_date": entry_date,
                    "exit_date": idx,
                    "entry_price": entry_price,
                    "exit_price": round(actual_exit, 2),
                    "return_pct": round(ret, 4),
                    "stopped": True,
                })
                stopped = True
                break

        if not stopped:
            result.append(t)

    return result


def build_equity_curve(trades, start_capital=1000.0):
    """Baut Equity-Kurve aus Trades. Returns: list[(date, value)]."""
    if not trades:
        return []

    sorted_trades = sorted(trades, key=lambda t: t["entry_date"])
    equity = start_capital
    curve = [(sorted_trades[0]["entry_date"], equity)]

    for t in sorted_trades:
        equity *= (1 + t["return_pct"] / 100)
        curve.append((t["exit_date"], round(equity, 2)))

    return curve


def compute_strategy_stats(trades, start_capital=1000.0):
    """Berechnet KPIs für eine Strategie."""
    if not trades:
        return {}

    returns = [t["return_pct"] for t in trades]
    n = len(returns)
    wins = sum(1 for r in returns if r > 0)

    # Equity-Kurve für Max-DD
    equity = [start_capital]
    for r in returns:
        equity.append(equity[-1] * (1 + r / 100))

    final = equity[-1]

    # CAGR
    first_date = min(t["entry_date"] for t in trades)
    last_date = max(t["exit_date"] for t in trades)
    years_span = (last_date - first_date).days / 365.25
    cagr = ((final / start_capital) ** (1 / years_span) - 1) * 100 if years_span > 0 else 0

    # Max Drawdown
    peak = equity[0]
    max_dd = 0
    for v in equity:
        if v > peak:
            peak = v
        dd = (v - peak) / peak * 100
        if dd < max_dd:
            max_dd = dd

    # Sharpe (annualisiert, vereinfacht)
    avg_ret = np.mean(returns)
    std_ret = np.std(returns) if len(returns) > 1 else 1
    trades_per_year = n / years_span if years_span > 0 else 1
    sharpe = (avg_ret / std_ret) * np.sqrt(trades_per_year) if std_ret > 0 else 0

    return {
        "total_return": round((final / start_capital - 1) * 100, 1),
        "cagr": round(cagr, 2),
        "max_drawdown": round(max_dd, 1),
        "win_rate": round(wins / n * 100, 1) if n > 0 else 0,
        "n_trades": n,
        "avg_return": round(avg_ret, 2),
        "sharpe": round(sharpe, 2),
        "final_equity": round(final, 2),
        "years_span": round(years_span, 1),
        "profit_factor": round(
            sum(r for r in returns if r > 0) / abs(sum(r for r in returns if r < 0))
            if sum(r for r in returns if r < 0) != 0 else 999, 2
        ),
    }


# ══════════════════════════════════════════════════════════════
# STRATEGIE-REGISTRY
# ══════════════════════════════════════════════════════════════

STRATEGIES = {
    "sell_in_may": {
        "name": "Sell in May",
        "icon": "📅",
        "func": calc_sell_in_may,
        "desc": "Einstieg: Letzter Handelstag Oktober. Ausstieg: 3. Handelstag Mai.",
        "info": "Die klassische Halloween-Strategie: November bis April investiert, Mai bis Oktober Cash.",
    },
    "lbr_november_mai": {
        "name": "LBR Nov-Mai",
        "icon": "📊",
        "func": calc_lbr_november_mai,
        "desc": "Einstieg: Ab Oktober wenn LBR > 0. Ausstieg: Ab April wenn LBR < 0.",
        "info": "Sell-in-May mit LBR-Indikator gefiltert — nur investieren wenn der Trend bullisch ist.",
    },
    "nasdaq_trend": {
        "name": "Nasdaq-Trend",
        "icon": "📈",
        "func": calc_nasdaq_trend,
        "desc": "Einstieg: Letzter HT Oktober. Ausstieg: Letzter HT Juni.",
        "info": "Erweiterte Sell-in-May Variante: 8 Monate investiert (Nov-Jun) statt 6.",
    },
    "month_end": {
        "name": "Month-End",
        "icon": "🔄",
        "func": calc_month_end,
        "desc": "Einstieg: Vorletzter HT des Monats. Ausstieg: 4. HT Folgemonat.",
        "info": "Nutzt den Turn-of-the-Month Effekt: Monatswechsel sind historisch positiv.",
    },
    "monthly_10": {
        "name": "Monthly 10",
        "icon": "🗓️",
        "func": calc_monthly_10,
        "desc": "Investiert an TDOM 1-4, 9-12 und den letzten 2 Handelstagen.",
        "info": "Kombiniert mehrere Monatsmuster: Monatsanfang, Monatsmitte und Monatsende.",
    },
    "santa_claus": {
        "name": "Santa Claus",
        "icon": "🎅",
        "func": calc_santa_claus,
        "desc": "Einstieg: 3 TDOM vor Thanksgiving. Ausstieg: 5. TDOM Januar.",
        "info": "Erweiterte Weihnachtsrallye: Thanksgiving bis Anfang Januar.",
    },
    "cycle_212_week": {
        "name": "212-Wochen-Zyklus",
        "icon": "🔁",
        "func": calc_212_week_cycle,
        "desc": "Einstieg: Alle 1.484 Kalendertage (ab 16.05.1938). Ausstieg: 6 Monate später.",
        "info": "Langfristiger Markt-Zyklus: Alle ~4 Jahre, 6 Monate investiert.",
    },
    "cycle_40_week": {
        "name": "40-Wochen-Zyklus",
        "icon": "⚡",
        "func": calc_40_week_cycle,
        "desc": "Einstieg: 280-Tage-Zyklus (ab 21.04.1967). Ausstieg: 140 Tage später.",
        "info": "Kurzfristiger Zyklus: Erste Hälfte (20 Wochen) = bullische Phase.",
    },
    "midterm_election": {
        "name": "Midterm Election",
        "icon": "🏛️",
        "func": calc_midterm_election,
        "desc": "Einstieg: 5 HT vor Midterm-Wahl. Ausstieg: 3 HT nach der Wahl.",
        "info": "Kurzfristiger Trade um die US-Zwischenwahlen (alle 4 Jahre).",
    },
    "september_avoid": {
        "name": "September-Vermeidung",
        "icon": "🚫",
        "func": calc_september_avoid,
        "desc": "Einstieg: 30. September. Ausstieg: 31. August. Cash nur im September.",
        "info": "Die einfachste Strategie: 11 Monate investiert, September = Cash.",
    },
    "uecs": {
        "name": "Election Cycle",
        "icon": "🇺🇸",
        "func": calc_uecs,
        "desc": "Investiert in 6 Phasen des 4-Jahres-Präsidentenzyklus.",
        "info": "Ultimate Election Cycle System: Midterm-Wahl, Vorwahljahr Mär-Jul + Okt-Sep + Nov-Dez, Wahljahr Jun-Dez, Dekaden-5-Jahre.",
    },
    "ultimate_monthly": {
        "name": "Ultimate Monthly",
        "icon": "💎",
        "func": calc_ultimate_monthly,
        "desc": "TDOM 1-4, 9-12, letzte 2 + Feiertage + Santa-Claus-Phase.",
        "info": "Kombiniert die stärksten Monatstage, Feiertags-Effekte und die Weihnachtsrallye in einem System.",
    },
    "kti_long": {
        "name": "KTI Long-Only",
        "icon": "📡",
        "func": calc_kti_long_only,
        "desc": "Long wenn KTI ≥ 3, Cash wenn < 3. KTI = Summe aktiver saisonaler Trends.",
        "info": "Known Trends Index (Jay Kaeppel): 14 Komponenten (Monatstage, Zyklen, Wahlzyklus, Feiertage). KTI ≥ 3 = bullisch.",
    },
    "kti_leveraged": {
        "name": "KTI + Hebel",
        "icon": "🔥",
        "func": calc_kti_leveraged,
        "desc": "KTI ≥ 5 → 2x Hebel, KTI 3-4 → 1x Long, KTI < 3 → Cash.",
        "info": "Aggressive KTI-Variante: Verdoppelt die Position wenn viele saisonale Trends gleichzeitig bullisch sind.",
    },
}

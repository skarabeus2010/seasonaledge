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
# STRATEGIE 11: ULTIMATE ELECTION CYCLE SYSTEM (UECS)
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
}

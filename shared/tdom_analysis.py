"""
shared/tdom_analysis.py — Trading Day of the Month (TDoM) Analyse
==================================================================
3 Strategien: Open→Close, Open→NextOpen, Close→NextClose
+ Multi-Day TDoM Ranges + Heatmap + Statistiken

Kein Streamlit-Import! Reine Berechnung.
"""

import numpy as np
import pandas as pd
from typing import Optional


# ── TDoM-Spalten hinzufügen ─────────────────────────

def add_tdom_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fügt tdom (vorwärts) und tdom_reverse (rückwärts) Spalten hinzu.

    tdom:         1 = erster Handelstag, 2 = zweiter, ...
    tdom_reverse: -1 = letzter Handelstag, -2 = vorletzter, ...
    """
    df = df.copy()

    if "year" not in df.columns or "month" not in df.columns:
        if "Date" in df.columns:
            df["year"] = pd.to_datetime(df["Date"]).dt.year
            df["month"] = pd.to_datetime(df["Date"]).dt.month
        elif df.index.name == "Date":
            df["year"] = df.index.year
            df["month"] = df.index.month

    # Vorwärts: TDoM 1, 2, 3, ...
    df["tdom"] = df.groupby(["year", "month"]).cumcount() + 1

    # Rückwärts: TDoM -1, -2, -3, ...
    df["tdom_reverse"] = (
        df.groupby(["year", "month"]).cumcount(ascending=False) + 1
    ) * -1

    return df


# ── Strategie-Renditen ───────────────────────────────

def calc_strategy_returns(df: pd.DataFrame, strategy: str = "open_to_close") -> pd.DataFrame:
    """
    Berechnet Renditen je nach Strategie.

    Strategien:
        "open_to_close"       — Intraday: Open → Close (gleicher Tag)
        "open_to_next_open"   — Overnight: Open → nächster Open
        "open_to_next_close"  — 2-Tages-Hold: Open → Close des Folgetags
        "close_to_next_close" — Close → nächster Close
    """
    df = df.copy()

    if strategy == "open_to_close":
        df["strat_return"] = (df["Close"] - df["Open"]) / df["Open"] * 100
    elif strategy == "open_to_next_open":
        df["strat_return"] = (df["Open"].shift(-1) - df["Open"]) / df["Open"] * 100
    elif strategy == "open_to_next_close":
        df["strat_return"] = (df["Close"].shift(-1) - df["Open"]) / df["Open"] * 100
    elif strategy == "close_to_next_close":
        df["strat_return"] = (df["Close"].shift(-1) - df["Close"]) / df["Close"] * 100
    else:
        raise ValueError(f"Unbekannte Strategie: {strategy}")

    return df


# ── TDoM Statistiken ─────────────────────────────────

def build_tdom_stats(
    df: pd.DataFrame,
    strategy: str = "open_to_close",
    direction: str = "forward",
    selected_months: list[int] = None,
) -> pd.DataFrame:
    """
    Statistiken pro TDoM: Ø Rendite, Win-Rate, Median, Std, Count.

    Args:
        df: DataFrame mit OHLC + year, month Spalten
        strategy: "open_to_close" | "open_to_next_open" | "close_to_next_close"
        direction: "forward" (TDoM 1,2,3...) oder "backward" (TDoM -1,-2,-3...)
        selected_months: Optional, nur diese Monate einbeziehen

    Returns:
        DataFrame mit Index=TDoM, Spalten: avg_return, win_rate, count, etc.
    """
    df = add_tdom_columns(df)
    df = calc_strategy_returns(df, strategy)

    if selected_months:
        df = df[df["month"].isin(selected_months)]

    tdom_col = "tdom" if direction == "forward" else "tdom_reverse"

    # Nur gültige TDoMs (Forward: 1-23, Backward: -1 bis -23)
    valid = df[df["strat_return"].notna()].copy()

    if direction == "forward":
        valid = valid[valid[tdom_col].between(1, 23)]
    else:
        valid = valid[valid[tdom_col].between(-23, -1)]

    stats = valid.groupby(tdom_col).agg(
        avg_return=("strat_return", "mean"),
        win_rate=("strat_return", lambda x: (x > 0).mean() * 100),
        count=("strat_return", "count"),
        std_dev=("strat_return", "std"),
        median_return=("strat_return", "median"),
        max_return=("strat_return", "max"),
        min_return=("strat_return", "min"),
    ).round(4)

    stats.index.name = "TDoM"
    return stats.sort_index(ascending=(direction == "forward"))


# ── Multi-Day TDoM Range ─────────────────────────────

def calc_tdom_range_return(
    df: pd.DataFrame,
    entry_tdom: int,
    exit_tdom: int,
    entry_price: str = "Open",
    exit_price: str = "Close",
) -> pd.DataFrame:
    """
    Berechnet Rendite für Halten von entry_tdom bis exit_tdom.

    Args:
        df: DataFrame mit OHLC + year, month
        entry_tdom: Positiv (1,2,3...) oder negativ (-1,-2,...)
        exit_tdom: Positiv oder negativ
        entry_price: "Open" oder "Close"
        exit_price: "Open" oder "Close"

    Returns:
        DataFrame mit: year, month, return_pct, entry_date, exit_date, etc.
    """
    df = add_tdom_columns(df)
    results = []

    entry_col = "tdom" if entry_tdom > 0 else "tdom_reverse"
    exit_col = "tdom" if exit_tdom > 0 else "tdom_reverse"

    for (year, month), group in df.groupby(["year", "month"]):
        entry_rows = group[group[entry_col] == entry_tdom]
        exit_rows = group[group[exit_col] == exit_tdom]

        if len(entry_rows) == 0 or len(exit_rows) == 0:
            continue

        entry_row = entry_rows.iloc[0]
        exit_row = exit_rows.iloc[0]

        # Exit muss nach Entry liegen
        if exit_row.name <= entry_row.name:
            continue

        p_entry = entry_row[entry_price]
        p_exit = exit_row[exit_price]

        if p_entry <= 0:
            continue

        ret = (p_exit - p_entry) / p_entry * 100

        results.append({
            "year": year,
            "month": month,
            "return_pct": round(ret, 4),
            "entry_date": entry_row.name if hasattr(entry_row, 'name') else None,
            "exit_date": exit_row.name if hasattr(exit_row, 'name') else None,
            "entry_price": round(p_entry, 2),
            "exit_price": round(p_exit, 2),
            "holding_days": len(group.loc[entry_row.name:exit_row.name]),
        })

    if not results:
        return pd.DataFrame()

    return pd.DataFrame(results)


def calc_range_stats(range_df: pd.DataFrame) -> dict:
    """Statistiken für eine TDoM-Range-Strategie."""
    if range_df.empty:
        return {}

    rets = range_df["return_pct"]
    wins = (rets > 0).sum()

    return {
        "avg_return": round(rets.mean(), 4),
        "median_return": round(rets.median(), 4),
        "win_rate": round(wins / len(rets) * 100, 1),
        "std_dev": round(rets.std(), 4),
        "max_gain": round(rets.max(), 4),
        "max_loss": round(rets.min(), 4),
        "total_trades": len(rets),
        "winning": int(wins),
        "losing": int(len(rets) - wins),
        "avg_holding": round(range_df["holding_days"].mean(), 1),
    }


# ── Monats-TDoM-Heatmap ─────────────────────────────

def build_tdom_month_matrix(
    df: pd.DataFrame,
    strategy: str = "open_to_close",
    direction: str = "forward",
    max_tdom: int = 23,
) -> pd.DataFrame:
    """
    Matrix: Zeilen=Monate (Jan-Dez), Spalten=TDoM → Ø Rendite.
    Für Heatmap-Visualisierung.
    """
    df = add_tdom_columns(df)
    df = calc_strategy_returns(df, strategy)

    tdom_col = "tdom" if direction == "forward" else "tdom_reverse"
    valid = df[df["strat_return"].notna()].copy()

    if direction == "forward":
        valid = valid[valid[tdom_col].between(1, max_tdom)]
    else:
        valid = valid[valid[tdom_col].between(-max_tdom, -1)]

    pivot = valid.pivot_table(
        values="strat_return",
        index="month",
        columns=tdom_col,
        aggfunc="mean",
    ).round(4)

    # Monatsname als Index
    from shared.constants import MONTH_NAMES_DE
    pivot.index = [MONTH_NAMES_DE[m - 1] for m in pivot.index]

    return pivot


# ── Jahres-Breakdown ─────────────────────────────────

def build_tdom_year_breakdown(
    df: pd.DataFrame,
    tdom_value: int,
    strategy: str = "open_to_close",
    direction: str = "forward",
) -> pd.DataFrame:
    """
    Jahres-Breakdown für einen bestimmten TDoM.
    Zeigt Rendite pro Jahr (Ø über alle Monate des Jahres).
    """
    df = add_tdom_columns(df)
    df = calc_strategy_returns(df, strategy)

    tdom_col = "tdom" if direction == "forward" else "tdom_reverse"
    filtered = df[df[tdom_col] == tdom_value].copy()
    filtered = filtered[filtered["strat_return"].notna()]

    if filtered.empty:
        return pd.DataFrame()

    yearly = filtered.groupby("year").agg(
        avg_return=("strat_return", "mean"),
        win_rate=("strat_return", lambda x: (x > 0).mean() * 100),
        count=("strat_return", "count"),
    ).round(4)

    yearly.index.name = "Jahr"
    return yearly


STRATEGY_LABELS = {
    "open_to_close": "Intraday (Open → Close)",
    "open_to_next_open": "Overnight (Open → Next Open)",
    "close_to_next_close": "Close → Next Close",
}

DIRECTION_LABELS = {
    "forward": "Vorwärts (TDoM 1, 2, 3...)",
    "backward": "Rückwärts (TDoM -1, -2, -3...)",
}

"""
shared/tdoy_analysis.py — Trading Day of the Year (TDoY) Analyse
=================================================================
Analog zu tdom_analysis.py: 3 Strategien, Ranges, Heatmap, Statistiken.
Dynamischer TDOY-Max (Aktien ~252, Crypto ~365).

Kein Streamlit-Import! Reine Berechnung.
"""

import numpy as np
import pandas as pd
from typing import Optional

# ── Strategie-Renditen aus TDOM wiederverwenden ────
from shared.tdom_analysis import calc_strategy_returns, calc_range_stats


# ── TDoY-Spalten hinzufügen ───────────────────────

def add_tdoy_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fügt tdoy (vorwärts) und tdoy_reverse (rückwärts) Spalten hinzu.

    tdoy:         1 = erster Handelstag des Jahres, 2 = zweiter, ...
    tdoy_reverse: -1 = letzter Handelstag, -2 = vorletzter, ...

    Funktioniert dynamisch: Aktien ~252 Tage, Crypto ~365 Tage.
    """
    df = df.copy()

    if "year" not in df.columns:
        if "Date" in df.columns:
            df["year"] = pd.to_datetime(df["Date"]).dt.year
        elif df.index.name == "Date":
            df["year"] = df.index.year

    # Vorwärts: TDoY 1, 2, 3, ...
    df["tdoy"] = df.groupby("year").cumcount() + 1

    # Rückwärts: TDoY -1, -2, -3, ...
    df["tdoy_reverse"] = (
        df.groupby("year").cumcount(ascending=False) + 1
    ) * -1

    return df


# ── TDoY Statistiken ──────────────────────────────

def build_tdoy_stats(
    df: pd.DataFrame,
    strategy: str = "open_to_close",
    direction: str = "forward",
    selected_months: Optional[list[int]] = None,
    bin_size: Optional[int] = None,
) -> pd.DataFrame:
    """
    Statistiken pro TDoY: Ø Rendite, Win-Rate, Median, Std, Count.

    Args:
        df: DataFrame mit OHLC + year Spalten
        strategy: "open_to_close" | "open_to_next_open" | "close_to_next_close"
        direction: "forward" (TDoY 1,2,3...) oder "backward" (TDoY -1,-2,-3...)
        selected_months: Optional, nur diese Monate einbeziehen
        bin_size: Optional (z.B. 5) → TDoY in Blöcke gruppieren

    Returns:
        DataFrame mit Index=TDoY (oder Bin), Spalten: avg_return, win_rate, etc.
    """
    df = add_tdoy_columns(df)
    df = calc_strategy_returns(df, strategy)

    if selected_months:
        if "month" not in df.columns:
            if df.index.name == "Date":
                df["month"] = df.index.month
            elif "Date" in df.columns:
                df["month"] = pd.to_datetime(df["Date"]).dt.month
        df = df[df["month"].isin(selected_months)]

    tdoy_col = "tdoy" if direction == "forward" else "tdoy_reverse"

    valid = df[df["strat_return"].notna()].copy()

    # Dynamischer Bereich aus den Daten
    if direction == "forward":
        tdoy_max = int(valid[tdoy_col].max()) if len(valid) > 0 else 252
        valid = valid[valid[tdoy_col].between(1, tdoy_max)]
    else:
        tdoy_min = int(valid[tdoy_col].min()) if len(valid) > 0 else -252
        valid = valid[valid[tdoy_col].between(tdoy_min, -1)]

    # Optional: Binning (z.B. 5er-Blöcke für glattere Darstellung)
    if bin_size and bin_size > 1:
        if direction == "forward":
            valid["tdoy_bin"] = ((valid[tdoy_col] - 1) // bin_size) * bin_size + 1
        else:
            valid["tdoy_bin"] = ((valid[tdoy_col] + 1) // bin_size) * bin_size - 1
        group_col = "tdoy_bin"
    else:
        group_col = tdoy_col

    stats = valid.groupby(group_col).agg(
        avg_return=("strat_return", "mean"),
        win_rate=("strat_return", lambda x: (x > 0).mean() * 100),
        count=("strat_return", "count"),
        std_dev=("strat_return", "std"),
        median_return=("strat_return", "median"),
        max_return=("strat_return", "max"),
        min_return=("strat_return", "min"),
    ).round(4)

    stats.index.name = "TDoY"
    return stats.sort_index(ascending=(direction == "forward"))


# ── Multi-Day TDoY Range ──────────────────────────

def calc_tdoy_range_return(
    df: pd.DataFrame,
    entry_tdoy: int,
    exit_tdoy: int,
    entry_price: str = "Open",
    exit_price: str = "Close",
) -> pd.DataFrame:
    """
    Berechnet Rendite für Halten von entry_tdoy bis exit_tdoy (innerhalb eines Jahres).

    Args:
        df: DataFrame mit OHLC + year
        entry_tdoy: Positiv (1,2,3...) oder negativ (-1,-2,...)
        exit_tdoy: Positiv oder negativ
        entry_price: "Open" oder "Close"
        exit_price: "Open" oder "Close"

    Returns:
        DataFrame mit: year, return_pct, entry_date, exit_date, holding_days
    """
    df = add_tdoy_columns(df)
    results = []

    entry_col = "tdoy" if entry_tdoy > 0 else "tdoy_reverse"
    exit_col = "tdoy" if exit_tdoy > 0 else "tdoy_reverse"

    for year, group in df.groupby("year"):
        entry_rows = group[group[entry_col] == entry_tdoy]
        exit_rows = group[group[exit_col] == exit_tdoy]

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
            "return_pct": round(ret, 4),
            "entry_date": entry_row.name if hasattr(entry_row, "name") else None,
            "exit_date": exit_row.name if hasattr(exit_row, "name") else None,
            "entry_price": round(p_entry, 2),
            "exit_price": round(p_exit, 2),
            "holding_days": len(group.loc[entry_row.name:exit_row.name]),
        })

    if not results:
        return pd.DataFrame()

    return pd.DataFrame(results)


# ── Monats-TDoY-Heatmap ──────────────────────────

def build_tdoy_month_matrix(
    df: pd.DataFrame,
    strategy: str = "open_to_close",
    direction: str = "forward",
    max_tdoy: Optional[int] = None,
) -> pd.DataFrame:
    """
    Matrix: Zeilen=Monate (Jan–Dez), Spalten=TDoY → Ø Rendite.
    Für Heatmap-Visualisierung.

    max_tdoy: Optional. Wenn None, dynamisch aus Daten ermittelt.
    """
    df = add_tdoy_columns(df)
    df = calc_strategy_returns(df, strategy)

    if "month" not in df.columns:
        if df.index.name == "Date":
            df["month"] = df.index.month
        elif "Date" in df.columns:
            df["month"] = pd.to_datetime(df["Date"]).dt.month

    tdoy_col = "tdoy" if direction == "forward" else "tdoy_reverse"
    valid = df[df["strat_return"].notna()].copy()

    if max_tdoy is None:
        max_tdoy = int(valid[tdoy_col].abs().max()) if len(valid) > 0 else 252

    if direction == "forward":
        valid = valid[valid[tdoy_col].between(1, max_tdoy)]
    else:
        valid = valid[valid[tdoy_col].between(-max_tdoy, -1)]

    pivot = valid.pivot_table(
        values="strat_return",
        index="month",
        columns=tdoy_col,
        aggfunc="mean",
    ).round(4)

    # Monatsname als Index
    from shared.constants import MONTH_NAMES_DE
    pivot.index = [MONTH_NAMES_DE[m - 1] for m in pivot.index]

    return pivot


# ── Jahres-Breakdown ──────────────────────────────

def build_tdoy_year_breakdown(
    df: pd.DataFrame,
    tdoy_value: int,
    strategy: str = "open_to_close",
    direction: str = "forward",
) -> pd.DataFrame:
    """
    Jahres-Breakdown für einen bestimmten TDoY.
    Zeigt Rendite pro Jahr.
    """
    df = add_tdoy_columns(df)
    df = calc_strategy_returns(df, strategy)

    tdoy_col = "tdoy" if direction == "forward" else "tdoy_reverse"
    filtered = df[df[tdoy_col] == tdoy_value].copy()
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


# ── Aktueller TDoY ────────────────────────────────

def get_current_tdoy(df: pd.DataFrame) -> Optional[int]:
    """
    Ermittelt den TDoY für heute aus den realen Daten.

    Returns:
        int (TDoY-Wert) oder None wenn nicht bestimmbar.
    """
    from datetime import datetime

    today = datetime.now()
    df = add_tdoy_columns(df)

    current = df[df["year"] == today.year]
    current = current[current.index <= pd.Timestamp(today.date())]

    if len(current) == 0:
        return None

    return int(current["tdoy"].iloc[-1])


# ── Monatsgrenzen auf TDoY-Achse ──────────────────

def get_tdoy_month_boundaries(df: pd.DataFrame) -> list[dict]:
    """
    Ermittelt für jeden Monat den ersten TDoY (Median über alle Jahre).

    Returns:
        [{"month": 1, "label": "Jan", "tdoy": 1},
         {"month": 2, "label": "Feb", "tdoy": 21}, ...]

    Dynamisch: Crypto-Monatsgrenzen (~30, ~61, ~91…) vs.
    Aktien (~21, ~42, ~63…).
    """
    from shared.constants import MONTH_NAMES_DE

    MONTH_LABELS = [
        "Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
        "Jul", "Aug", "Sep", "Okt", "Nov", "Dez",
    ]

    df = add_tdoy_columns(df)

    if "month" not in df.columns:
        if df.index.name == "Date":
            df["month"] = df.index.month
        elif "Date" in df.columns:
            df["month"] = pd.to_datetime(df["Date"]).dt.month

    boundaries = []

    for m in range(1, 13):
        # Erster TDoY jedes Monats, pro Jahr
        month_starts = df[df["month"] == m].groupby("year")["tdoy"].min()

        if len(month_starts) == 0:
            continue

        median_tdoy = int(month_starts.median())

        boundaries.append({
            "month": m,
            "label": MONTH_LABELS[m - 1],
            "label_full": MONTH_NAMES_DE[m - 1],
            "tdoy": median_tdoy,
        })

    return boundaries


# ── Konstanten ────────────────────────────────────

TDOY_BIN_SIZES = [1, 5, 10, 20]

# Re-export von tdom_analysis
from shared.tdom_analysis import STRATEGY_LABELS

DIRECTION_LABELS = {
    "forward": "Vorwärts (TDoY 1, 2, 3...)",
    "backward": "Rückwärts (TDoY -1, -2, -3...)",
}

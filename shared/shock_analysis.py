"""
shared/shock_analysis.py — Shock Analyzer für SeasonAlpha

Analyse: Wenn Asset A um X% steigt/fällt, wie performt Asset B
nach konfigurierbaren Zeiträumen?

Verwendung:
    from shared.shock_analysis import find_shocks, analyze_impact

    shocks = find_shocks(df_trigger, threshold=-5.0, direction="down")
    impact = analyze_impact(shocks, df_target, horizons=[1, 5, 10, 20, 60])
"""
import pandas as pd
import numpy as np
from typing import Literal


def find_shocks(
    df: pd.DataFrame,
    threshold: float = 5.0,
    direction: Literal["up", "down", "both"] = "down",
    column: str = "Close",
) -> pd.DataFrame:
    """
    Findet Tage an denen der Trigger-Asset einen Shock hatte.

    Args:
        df: DataFrame mit Date und Close (oder column)
        threshold: Schwellenwert in % (immer positiv angeben)
        direction: "up" (>= +threshold), "down" (<= -threshold), "both"
        column: Spaltenname für den Kurs

    Returns:
        DataFrame mit Spalten: date, daily_return_pct, close
    """
    df = df.copy()
    if "Date" in df.columns:
        df = df.set_index("Date")
    df = df.sort_index()

    # Tagesrendite berechnen
    df["daily_return_pct"] = df[column].pct_change() * 100

    threshold = abs(threshold)

    if direction == "down":
        mask = df["daily_return_pct"] <= -threshold
    elif direction == "up":
        mask = df["daily_return_pct"] >= threshold
    else:  # both
        mask = df["daily_return_pct"].abs() >= threshold

    shocks = df[mask][["daily_return_pct", column]].copy()
    shocks = shocks.rename(columns={column: "close"})
    shocks.index.name = "date"
    return shocks.reset_index()


def analyze_impact(
    shocks: pd.DataFrame,
    df_target: pd.DataFrame,
    horizons: list[int] = None,
    column: str = "Close",
) -> dict:
    """
    Analysiert die Performance des Target-Assets nach Shock-Events.

    Args:
        shocks: Output von find_shocks() (muss 'date' Spalte haben)
        df_target: DataFrame des Ziel-Assets mit Date und Close
        horizons: Liste der Zeiträume in Tagen (Default: [1, 5, 10, 20, 60])
        column: Spaltenname für den Kurs

    Returns:
        dict mit:
          - summary: DataFrame (horizon, avg_return, median_return, win_rate, n_events, std_dev)
          - events: DataFrame (alle Einzelereignisse mit Renditen pro Horizont)
    """
    if horizons is None:
        horizons = [1, 5, 10, 20, 60]

    df_t = df_target.copy()
    if "Date" in df_t.columns:
        df_t = df_t.set_index("Date")
    df_t = df_t.sort_index()

    # Trading-Day-Index für schnellen Zugriff
    trading_dates = df_t.index.tolist()
    date_to_idx = {d: i for i, d in enumerate(trading_dates)}

    events = []

    for _, shock in shocks.iterrows():
        shock_date = pd.Timestamp(shock["date"])

        # Nächsten verfügbaren Handelstag im Target finden
        idx = date_to_idx.get(shock_date)
        if idx is None:
            # Suche nächsten Handelstag nach Shock-Datum
            future_dates = [d for d in trading_dates if d >= shock_date]
            if not future_dates:
                continue
            shock_date = future_dates[0]
            idx = date_to_idx[shock_date]

        base_price = df_t.iloc[idx][column]
        event = {
            "shock_date": shock["date"],
            "trigger_return_pct": shock["daily_return_pct"],
            "target_base_price": base_price,
        }

        for h in horizons:
            future_idx = idx + h
            if future_idx < len(trading_dates):
                future_price = df_t.iloc[future_idx][column]
                ret = (future_price / base_price - 1) * 100
                event[f"return_{h}d"] = ret
            else:
                event[f"return_{h}d"] = np.nan

        events.append(event)

    if not events:
        return {
            "summary": pd.DataFrame(),
            "events": pd.DataFrame(),
            "n_events": 0,
        }

    events_df = pd.DataFrame(events)

    # Summary pro Horizont
    summary_rows = []
    for h in horizons:
        col = f"return_{h}d"
        valid = events_df[col].dropna()
        if len(valid) == 0:
            continue
        summary_rows.append({
            "horizon_days": h,
            "avg_return_pct": valid.mean(),
            "median_return_pct": valid.median(),
            "std_dev": valid.std(),
            "win_rate_pct": (valid > 0).mean() * 100,
            "max_return_pct": valid.max(),
            "min_return_pct": valid.min(),
            "n_events": len(valid),
        })

    summary_df = pd.DataFrame(summary_rows)

    return {
        "summary": summary_df,
        "events": events_df,
        "n_events": len(events_df),
    }


def shock_heatmap_data(
    df_trigger: pd.DataFrame,
    df_target: pd.DataFrame,
    thresholds: list[float] = None,
    horizons: list[int] = None,
    direction: Literal["up", "down", "both"] = "down",
) -> pd.DataFrame:
    """
    Erstellt Heatmap-Daten: Trigger-Stärke × Zeitraum → Ø Rendite.

    Args:
        thresholds: z.B. [2, 3, 5, 7, 10] (%)
        horizons: z.B. [1, 5, 10, 20, 60] (Tage)

    Returns:
        DataFrame mit Index=threshold, Columns=horizon, Values=avg_return
    """
    if thresholds is None:
        thresholds = [2, 3, 5, 7, 10]
    if horizons is None:
        horizons = [1, 5, 10, 20, 60]

    results = {}
    for t in thresholds:
        shocks = find_shocks(df_trigger, threshold=t, direction=direction)
        impact = analyze_impact(shocks, df_target, horizons=horizons)
        if not impact["summary"].empty:
            row = {}
            for _, r in impact["summary"].iterrows():
                row[f"{int(r['horizon_days'])}d"] = r["avg_return_pct"]
            results[f"{t}%"] = row
        else:
            results[f"{t}%"] = {f"{h}d": np.nan for h in horizons}

    return pd.DataFrame(results).T

"""
SeasonalEdge — Shock Analyzer (Event Study / Cross-Asset Impact)

Fragestellung:
  "Wenn Asset A an einem Tag um ±X% fällt/steigt,
   wie performt Asset B nach N Tagen?"

Verwendung:
  from shared.shock_analysis import find_shock_events, analyze_shock_impact
  from shared.shock_analysis import build_shock_heatmap_data, shock_summary_stats

  # 1. Shock-Events im Trigger-Asset finden
  events = find_shock_events(df_trigger, threshold=-5.0, direction="down")

  # 2. Impact auf Ziel-Asset analysieren
  impact = analyze_shock_impact(
      df_trigger, df_target,
      threshold=-5.0, direction="down",
      forward_days=[1, 5, 10, 20, 60],
  )

  # 3. Heatmap-Daten: Schwellenwert × Zeitraum
  heatmap = build_shock_heatmap_data(df_trigger, df_target, direction="down")
"""

import numpy as np
import pandas as pd

from shared.logger import app_logger, error_logger


# ── Shock-Events finden ──────────────────────────────────────

def find_shock_events(
    df: pd.DataFrame,
    threshold: float = -5.0,
    direction: str = "down",
    date_col: str = "Date",
    close_col: str = "Close",
) -> pd.DataFrame:
    """
    Findet Tage, an denen das Asset um ≥ threshold% gestiegen/gefallen ist.

    Args:
        df: DataFrame mit Date und Close
        threshold: Schwellenwert in % (z.B. -5.0 für -5%)
        direction: "down" (Einbruch) oder "up" (Anstieg)
        date_col: Spaltenname für Datum
        close_col: Spaltenname für Schlusskurs

    Returns:
        DataFrame mit Spalten: Date, Close, daily_return_pct, shock_magnitude
    """
    work = df.copy()

    # Datum sicherstellen
    if date_col in work.columns:
        work[date_col] = pd.to_datetime(work[date_col])
        work = work.sort_values(date_col).reset_index(drop=True)
    elif work.index.name == date_col or isinstance(work.index, pd.DatetimeIndex):
        work = work.reset_index()
        work[date_col] = pd.to_datetime(work[date_col])
        work = work.sort_values(date_col).reset_index(drop=True)

    # Tägliche Rendite berechnen
    work["daily_return_pct"] = work[close_col].pct_change() * 100

    # Filtern nach Richtung und Schwellenwert
    abs_threshold = abs(threshold)
    if direction == "down":
        mask = work["daily_return_pct"] <= -abs_threshold
    elif direction == "up":
        mask = work["daily_return_pct"] >= abs_threshold
    else:
        raise ValueError(f"direction muss 'up' oder 'down' sein, nicht '{direction}'")

    events = work[mask].copy()
    events["shock_magnitude"] = events["daily_return_pct"].abs()

    app_logger.info(
        f"Shock-Events gefunden: {len(events)} "
        f"(threshold={threshold}%, direction={direction})"
    )
    return events[[date_col, close_col, "daily_return_pct", "shock_magnitude"]]


# ── Forward Returns berechnen ────────────────────────────────

def _calc_forward_returns(
    df: pd.DataFrame,
    event_dates: list[pd.Timestamp],
    forward_days: list[int],
    date_col: str = "Date",
    close_col: str = "Close",
) -> pd.DataFrame:
    """
    Berechnet Forward-Returns für jedes Event-Datum.

    Returns:
        DataFrame: event_date, fwd_1d, fwd_5d, ... (in %)
    """
    work = df.copy()
    if date_col in work.columns:
        work[date_col] = pd.to_datetime(work[date_col])
        work = work.set_index(date_col)
    work = work.sort_index()

    results = []
    for event_date in event_dates:
        if event_date not in work.index:
            # Nächsten verfügbaren Handelstag finden
            idx = work.index.searchsorted(event_date)
            if idx >= len(work.index):
                continue
            event_date = work.index[idx]

        event_price = work.loc[event_date, close_col]
        if pd.isna(event_price) or event_price == 0:
            continue

        row = {"event_date": event_date}
        event_pos = work.index.get_loc(event_date)

        for days in forward_days:
            fwd_pos = event_pos + days
            if fwd_pos < len(work):
                fwd_price = work.iloc[fwd_pos][close_col]
                row[f"fwd_{days}d"] = ((fwd_price / event_price) - 1) * 100
            else:
                row[f"fwd_{days}d"] = np.nan

        results.append(row)

    return pd.DataFrame(results)


# ── Haupt-Analyse ────────────────────────────────────────────

def analyze_shock_impact(
    df_trigger: pd.DataFrame,
    df_target: pd.DataFrame,
    threshold: float = -5.0,
    direction: str = "down",
    forward_days: list[int] | None = None,
    date_col: str = "Date",
    close_col: str = "Close",
) -> dict:
    """
    Vollständige Shock-Impact-Analyse.

    Args:
        df_trigger: Kursdaten des Trigger-Assets (z.B. Öl)
        df_target: Kursdaten des Ziel-Assets (z.B. DAX)
        threshold: Schwellenwert in %
        direction: "down" oder "up"
        forward_days: Liste der Vorschau-Zeiträume [1, 5, 10, 20, 60]

    Returns:
        Dict mit:
          - events: DataFrame der Shock-Events
          - forward_returns: DataFrame der Forward-Returns
          - summary: Dict mit Statistiken pro Zeitraum
          - n_events: Anzahl Events
    """
    if forward_days is None:
        forward_days = [1, 5, 10, 20, 60]

    # Sortieren
    forward_days = sorted(forward_days)

    # 1. Events finden
    events = find_shock_events(df_trigger, threshold, direction, date_col, close_col)

    if events.empty:
        app_logger.warning(f"Keine Shock-Events gefunden (threshold={threshold}%)")
        return {
            "events": events,
            "forward_returns": pd.DataFrame(),
            "summary": {},
            "n_events": 0,
        }

    # 2. Forward Returns im Ziel-Asset
    event_dates = pd.to_datetime(events[date_col]).tolist()
    fwd_returns = _calc_forward_returns(
        df_target, event_dates, forward_days, date_col, close_col
    )

    # 3. Zusammenfassung pro Zeitraum
    summary = {}
    for days in forward_days:
        col = f"fwd_{days}d"
        if col in fwd_returns.columns:
            values = fwd_returns[col].dropna()
            if len(values) > 0:
                summary[days] = {
                    "avg_return": round(values.mean(), 2),
                    "median_return": round(values.median(), 2),
                    "std_dev": round(values.std(), 2),
                    "win_rate": round((values > 0).sum() / len(values) * 100, 1),
                    "max_gain": round(values.max(), 2),
                    "max_loss": round(values.min(), 2),
                    "n_observations": len(values),
                }

    app_logger.info(
        f"Shock-Analyse abgeschlossen: {len(events)} Events, "
        f"Zeiträume: {forward_days}"
    )

    return {
        "events": events,
        "forward_returns": fwd_returns,
        "summary": summary,
        "n_events": len(events),
    }


# ── Heatmap-Daten ────────────────────────────────────────────

def build_shock_heatmap_data(
    df_trigger: pd.DataFrame,
    df_target: pd.DataFrame,
    direction: str = "down",
    thresholds: list[float] | None = None,
    forward_days: list[int] | None = None,
    date_col: str = "Date",
    close_col: str = "Close",
) -> pd.DataFrame:
    """
    Baut Heatmap-Daten: Schwellenwert × Zeitraum → Avg. Return.

    Args:
        thresholds: z.B. [2, 3, 5, 7, 10] (werden je nach direction pos/neg)
        forward_days: z.B. [1, 5, 10, 20, 60]

    Returns:
        DataFrame (Index=Threshold, Columns=Forward Days, Values=Avg Return %)
    """
    if thresholds is None:
        thresholds = [2, 3, 5, 7, 10]
    if forward_days is None:
        forward_days = [1, 5, 10, 20, 60]

    rows = []
    for thresh in thresholds:
        actual_thresh = -thresh if direction == "down" else thresh
        result = analyze_shock_impact(
            df_trigger, df_target,
            threshold=actual_thresh,
            direction=direction,
            forward_days=forward_days,
            date_col=date_col,
            close_col=close_col,
        )
        row = {"threshold": f"{'≤' if direction == 'down' else '≥'}{thresh}%"}
        row["n_events"] = result["n_events"]
        for days in forward_days:
            if days in result["summary"]:
                row[f"{days}d"] = result["summary"][days]["avg_return"]
            else:
                row[f"{days}d"] = np.nan
        rows.append(row)

    heatmap_df = pd.DataFrame(rows).set_index("threshold")
    return heatmap_df


# ── Zusammenfassungs-Statistiken ─────────────────────────────

def shock_summary_stats(impact_result: dict) -> pd.DataFrame:
    """
    Formatiert die Summary-Statistiken als übersichtliche Tabelle.

    Args:
        impact_result: Ergebnis von analyze_shock_impact()

    Returns:
        DataFrame mit Zeilen pro Zeitraum und Spalten für alle Metriken
    """
    if not impact_result["summary"]:
        return pd.DataFrame()

    rows = []
    for days, stats in sorted(impact_result["summary"].items()):
        rows.append({
            "Zeitraum": f"{days}d",
            "Ø Rendite %": stats["avg_return"],
            "Median %": stats["median_return"],
            "Std. Dev.": stats["std_dev"],
            "Win-Rate %": stats["win_rate"],
            "Max Gewinn %": stats["max_gain"],
            "Max Verlust %": stats["max_loss"],
            "N": stats["n_observations"],
        })

    return pd.DataFrame(rows)

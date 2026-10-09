"""
shared/cache_manager.py — Computed Values Cache (DB → Fallback → Store)
========================================================================
Liest vorberechnete Werte aus Supabase.
Fallback: Live-Berechnung + Speicherung in DB.

Kein Streamlit-Import! Reine Berechnung + DB.
"""

import math
from datetime import date, datetime
from shared.logger import app_logger


# ── Helpers ─────────────────────────────────────────

def _today_str() -> str:
    return date.today().isoformat()


def _is_stale(updated_at: str) -> bool:
    """Prüft ob ein DB-Eintrag älter als heute ist."""
    if not updated_at:
        return True
    try:
        ts = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        return ts.date() < date.today()
    except Exception:
        return True


# ── Seasonality (Monthly Stats) ────────────────────

def get_or_compute_monthly_stats(
    ticker: str,
    df=None,
    years_back: int = 20,
) -> list[dict]:
    """
    Monatliche Statistiken aus DB laden, bei Bedarf live berechnen + speichern.

    Args:
        ticker: z.B. "SPY"
        df: Preprocessed DataFrame (nur für Fallback nötig)
        years_back: Anzahl Jahre

    Returns:
        list[dict] — 12 Einträge (Monat 1-12)
    """
    try:
        from shared.supabase_client import fetch_monthly_stats
        cached = fetch_monthly_stats(ticker, years_back)
        if cached and len(cached) == 12 and not _is_stale(cached[0].get("updated_at")):
            return cached
    except Exception as e:
        app_logger.debug(f"cache_manager: DB-Lookup monthly_stats fehlgeschlagen: {e}")

    # Fallback: Live-Berechnung
    if df is None or df.empty:
        return []

    stats = _compute_monthly_stats(ticker, df, years_back)

    # Store in DB
    try:
        from shared.supabase_client import upsert_monthly_stats
        upsert_monthly_stats(stats)
    except Exception as e:
        app_logger.debug(f"cache_manager: DB-Upsert monthly_stats fehlgeschlagen: {e}")

    return stats


def _compute_monthly_stats(ticker: str, df, years_back: int) -> list[dict]:
    """Berechnet monatliche Statistiken aus DataFrame."""
    import numpy as np
    import pandas as pd

    current_year = date.today().year
    start_year = current_year - years_back

    df_filtered = df[df.index.year >= start_year].copy()
    if df_filtered.empty:
        return []

    # Monatsrenditen berechnen
    df_filtered["month"] = df_filtered.index.month
    df_filtered["year"] = df_filtered.index.year

    monthly_returns = (
        df_filtered.groupby(["year", "month"])["Close"]
        .agg(["first", "last"])
        .reset_index()
    )
    monthly_returns["return_pct"] = (
        (monthly_returns["last"] - monthly_returns["first"])
        / monthly_returns["first"] * 100
    )

    stats = []
    for month in range(1, 13):
        month_data = monthly_returns[monthly_returns["month"] == month]["return_pct"]
        if month_data.empty:
            continue
        stats.append({
            "ticker": ticker,
            "month": month,
            "years_back": years_back,
            "avg_return": round(float(month_data.mean()), 4),
            "median_return": round(float(month_data.median()), 4),
            "win_rate": round(float((month_data > 0).mean() * 100), 1),
            "std_dev": round(float(month_data.std()), 4),
            "max_gain": round(float(month_data.max()), 4),
            "max_loss": round(float(month_data.min()), 4),
            "total_years": int(len(month_data)),
        })

    return stats


# ── KI Score ────────────────────────────────────────

# ── Scanner Results ─────────────────────────────────

# ── TDoM Stats ──────────────────────────────────────

def get_or_compute_tdom_stats(
    ticker: str,
    df=None,
    strategy: str = "open_to_close",
    direction: str = "forward",
) -> list[dict]:
    """
    TDoM-Statistiken aus DB laden, bei Bedarf live berechnen + speichern.

    Returns:
        list[dict] — TDoM-Stats pro Tag
    """
    try:
        from shared.supabase_client import fetch_tdom_stats
        cached = fetch_tdom_stats(ticker, direction, strategy)
        if cached and not _is_stale(cached[0].get("updated_at")):
            return cached
    except Exception as e:
        app_logger.debug(f"cache_manager: DB-Lookup tdom_stats fehlgeschlagen: {e}")

    # Fallback: Live-Berechnung
    if df is None or df.empty:
        return []

    from shared.tdom_analysis import build_tdom_stats
    stats_df = build_tdom_stats(df, strategy=strategy, direction=direction)

    if stats_df.empty:
        return []

    records = []
    for tdom_val, row in stats_df.iterrows():
        records.append({
            "ticker": ticker,
            "tdom": int(tdom_val),
            "direction": direction,
            "strategy": strategy,
            "avg_return": round(float(row["avg_return"]), 4),
            "median_return": round(float(row["median_return"]), 4),
            "win_rate": round(float(row["win_rate"]), 1),
            "std_dev": round(float(row["std_dev"]), 4) if not math.isnan(row["std_dev"]) else 0.0,
            "count": int(row["count"]),
        })

    # Store in DB
    try:
        from shared.supabase_client import upsert_tdom_stats
        upsert_tdom_stats(records)
    except Exception as e:
        app_logger.debug(f"cache_manager: DB-Upsert tdom_stats fehlgeschlagen: {e}")

    return records


# ── TDoY Stats ──────────────────────────────────────

def get_or_compute_tdoy_stats(
    ticker: str,
    df=None,
    strategy: str = "open_to_close",
    direction: str = "forward",
) -> list[dict]:
    """
    TDoY-Statistiken aus DB laden, bei Bedarf live berechnen + speichern.

    Returns:
        list[dict] — TDoY-Stats pro Handelstag des Jahres
    """
    try:
        from shared.supabase_client import fetch_tdoy_stats
        cached = fetch_tdoy_stats(ticker, strategy, direction)
        if cached and not _is_stale(cached[0].get("updated_at")):
            return cached
    except Exception as e:
        app_logger.debug(f"cache_manager: DB-Lookup tdoy_stats fehlgeschlagen: {e}")

    # Fallback: Live-Berechnung
    if df is None or df.empty:
        return []

    from shared.tdoy_analysis import build_tdoy_stats
    stats_df = build_tdoy_stats(df, strategy=strategy, direction=direction)

    if stats_df.empty:
        return []

    records = []
    for tdoy_val, row in stats_df.iterrows():
        records.append({
            "ticker": ticker,
            "tdoy": int(tdoy_val),
            "direction": direction,
            "strategy": strategy,
            "avg_return": round(float(row["avg_return"]), 4),
            "median_return": round(float(row["median_return"]), 4),
            "win_rate": round(float(row["win_rate"]), 1),
            "std_dev": round(float(row["std_dev"]), 4) if not math.isnan(row["std_dev"]) else 0.0,
            "count": int(row["count"]),
        })

    # Store in DB
    try:
        from shared.supabase_client import upsert_tdoy_stats
        upsert_tdoy_stats(records)
    except Exception as e:
        app_logger.debug(f"cache_manager: DB-Upsert tdoy_stats fehlgeschlagen: {e}")

    return records

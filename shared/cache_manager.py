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

def get_or_compute_ki_score(
    ticker: str,
    df=None,
    year_data: dict = None,
    avg: list = None,
    std: list = None,
    quick_mode: bool = True,
) -> dict | None:
    """
    KI Score aus DB laden, bei Bedarf live berechnen + speichern.

    Returns:
        dict mit score, signal, sub_scores, meta — oder None
    """
    today = _today_str()

    try:
        from shared.supabase_client import fetch_ki_score
        cached = fetch_ki_score(ticker, today)
        if cached:
            return cached
    except Exception as e:
        app_logger.debug(f"cache_manager: DB-Lookup ki_score fehlgeschlagen: {e}")

    # Fallback: Live-Berechnung
    if df is None or year_data is None or avg is None or std is None:
        return None

    from shared.ki_score import calculate_ki_score
    result = calculate_ki_score(ticker, df, year_data, avg, std, quick_mode=quick_mode)

    # Store in DB
    try:
        from shared.supabase_client import upsert_ki_score
        upsert_ki_score({
            "ticker": ticker,
            "score": result["score"],
            "signal": result["signal"],
            "dtw_score": result["sub_scores"]["dtw"]["weighted"],
            "prophet_score": result["sub_scores"]["prophet"]["weighted"],
            "win_rate_score": result["sub_scores"]["win_rate"]["weighted"],
            "tracking_score": result["sub_scores"]["tracking"]["weighted"],
            "details": result["sub_scores"],
            "computed_date": today,
        })
    except Exception as e:
        app_logger.debug(f"cache_manager: DB-Upsert ki_score fehlgeschlagen: {e}")

    return result


# ── Scanner Results ─────────────────────────────────

def get_scanner_results(max_age_days: int = 1) -> list[dict] | None:
    """
    Scanner-Ergebnisse aus DB laden (nur wenn nicht älter als max_age_days).

    Returns:
        list[dict] sortiert nach Score, oder None wenn zu alt/nicht vorhanden
    """
    try:
        from shared.supabase_client import fetch_scanner_results
        results = fetch_scanner_results()
        if not results:
            return None

        # Prüfe Alter
        from datetime import timedelta
        first = results[0]
        scan_date = first.get("scan_date", "")
        try:
            scan_dt = date.fromisoformat(scan_date)
            if (date.today() - scan_dt).days > max_age_days:
                return None
        except Exception:
            return None

        return results
    except Exception as e:
        app_logger.debug(f"cache_manager: DB-Lookup scanner_results fehlgeschlagen: {e}")
        return None


def store_scanner_results(results: list[dict]):
    """Scanner-Ergebnisse in DB speichern."""
    today = _today_str()
    try:
        from shared.supabase_client import upsert_scanner_results
        records = []
        for r in results:
            records.append({
                "ticker": r["ticker"],
                "score": r["score"],
                "signal": r["signal"],
                "win_rate": r.get("win_rate", 0),
                "avg_return": r.get("avg_return", 0),
                "deviation": r.get("deviation", 0),
                "scan_date": today,
            })
        upsert_scanner_results(records)
    except Exception as e:
        app_logger.debug(f"cache_manager: DB-Upsert scanner_results fehlgeschlagen: {e}")


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

"""
shared/ki_score.py — KI Seasonal Score Engine
================================================
Composite Score 1-10 aus 4 Sub-Scores:
  DTW Ähnlichkeit (0-2.5) + Prophet Prognose (0-2.5)
  + Win-Rate (0-2.5) + Tracking-Qualität (0-2.5)

Kein Streamlit-Import! Reine Berechnung.
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Optional

# ── Konstanten ────────────────────────────────────────

SCORE_WEIGHTS = {
    "dtw": 2.5,
    "prophet": 2.5,
    "win_rate": 2.5,
    "tracking": 2.5,
}

SIGNAL_THRESHOLDS = {
    "bullish": 6.5,
    "bearish": 3.5,
}

MONTH_START_DOY = {
    1: 1, 2: 32, 3: 60, 4: 91, 5: 121, 6: 152,
    7: 182, 8: 213, 9: 244, 10: 274, 11: 305, 12: 335,
}

MONTH_END_DOY = {
    1: 31, 2: 59, 3: 90, 4: 120, 5: 151, 6: 181,
    7: 212, 8: 243, 9: 273, 10: 304, 11: 334, 12: 365,
}


# ── Sub-Score 1: DTW Ähnlichkeit ─────────────────────

def score_dtw_similarity(
    current_pattern: list[float],
    all_years_data: dict[int, list[float]],
    year_returns: dict[int, float],
    top_n: int = 5,
) -> tuple[float, dict]:
    """
    DTW Sub-Score: Wie ähnlich ist das aktuelle Jahr zu historisch guten Jahren?

    Returns:
        (normalized_score 0-1, details_dict)
    """
    from shared.ai_models import find_similar_years

    if len(current_pattern) < 10 or len(all_years_data) < 3:
        return 0.5, {"error": "Zu wenig Daten", "similar_years": []}

    try:
        similar = find_similar_years(current_pattern, all_years_data, top_n=top_n)
    except Exception:
        return 0.5, {"error": "DTW-Berechnung fehlgeschlagen", "similar_years": []}

    if not similar:
        return 0.5, {"error": "Keine ähnlichen Jahre gefunden", "similar_years": []}

    # Prüfe wie viele der ähnlichen Jahre positiv waren
    similar_with_returns = []
    positive_count = 0
    for year, dist in similar:
        full_year_return = year_returns.get(year, 0)
        similar_with_returns.append({
            "year": year,
            "distance": round(dist, 2),
            "return_pct": round(full_year_return, 2),
            "positive": full_year_return > 0,
        })
        if full_year_return > 0:
            positive_count += 1

    raw_score = positive_count / len(similar) if similar else 0.5

    return raw_score, {
        "similar_years": similar_with_returns,
        "positive_ratio": f"{positive_count}/{len(similar)}",
    }


# ── Sub-Score 2: Prophet Prognose ────────────────────

def score_prophet_forecast(
    df_prices: pd.DataFrame,
    periods: int = 30,
) -> tuple[float, dict]:
    """
    Prophet Sub-Score: Ist die 30-Tage-Prognose bullish oder bearish?

    Returns:
        (normalized_score 0-1, details_dict)
    """
    from shared.ai_models import forecast_seasonal

    try:
        forecast = forecast_seasonal(df_prices, periods=periods)
    except Exception:
        forecast = None

    if forecast is None or forecast.empty:
        return 0.5, {"error": "Prophet nicht verfügbar", "forecast_return": 0}

    try:
        first_val = forecast["yhat"].iloc[0]
        last_val = forecast["yhat"].iloc[-1]

        if first_val <= 0:
            return 0.5, {"error": "Ungültige Forecast-Werte", "forecast_return": 0}

        expected_return = (last_val - first_val) / first_val * 100

        # Mapping: -3% → 0.0, 0% → 0.5, +3% → 1.0
        raw_score = np.clip((expected_return + 3) / 6, 0.0, 1.0)

        return raw_score, {
            "forecast_return": round(expected_return, 2),
            "forecast_df": forecast,
            "direction": "bullish" if expected_return > 0 else "bearish",
        }
    except Exception:
        return 0.5, {"error": "Forecast-Auswertung fehlgeschlagen", "forecast_return": 0}


# ── Sub-Score 3: Win-Rate ────────────────────────────

def score_win_rate(
    year_data: dict,
    current_month: int,
) -> tuple[float, dict]:
    """
    Win-Rate Sub-Score: Historische Win-Rate des aktuellen Monats.

    Returns:
        (normalized_score 0-1, details_dict)
    """
    from shared.calculations import calculate_period_stats

    start_day = MONTH_START_DOY.get(current_month, 1)
    end_day = MONTH_END_DOY.get(current_month, 31)

    try:
        stats = calculate_period_stats(year_data, start_day, end_day)
    except Exception:
        stats = {}

    if not stats:
        return 0.5, {"error": "Keine Statistiken verfügbar", "win_rate": 50, "avg_return": 0}

    win_rate = stats.get("win_rate", 50)
    raw_score = win_rate / 100.0

    return raw_score, {
        "win_rate": round(win_rate, 1),
        "avg_return": round(stats.get("avg_return", 0), 2),
        "median_return": round(stats.get("median_return", 0), 2),
        "total_years": stats.get("total_years", 0),
        "max_gain": round(stats.get("max_gain", 0), 2),
        "max_loss": round(stats.get("max_loss", 0), 2),
    }


# ── Sub-Score 4: Tracking-Qualität ──────────────────

def score_tracking_quality(
    current_year_curve: list[float],
    seasonal_avg: list[float],
    trading_days_so_far: int,
) -> tuple[float, dict]:
    """
    Tracking Sub-Score: Wie genau folgt das aktuelle Jahr dem Saisonalmuster?

    Returns:
        (normalized_score 0-1, details_dict)
    """
    if trading_days_so_far < 10:
        return 0.5, {"error": "Zu wenig Handelstage (<10)", "correlation": 0, "mae": 0}

    n = min(trading_days_so_far, len(current_year_curve), len(seasonal_avg))
    if n < 10:
        return 0.5, {"error": "Zu wenig Datenpunkte", "correlation": 0, "mae": 0}

    curr = np.array(current_year_curve[:n])
    avg = np.array(seasonal_avg[:n])

    # Pearson-Korrelation
    try:
        corr = np.corrcoef(curr, avg)[0, 1]
        if np.isnan(corr):
            corr = 0
    except Exception:
        corr = 0

    # Normalisierte MAE
    avg_range = max(avg) - min(avg)
    if avg_range > 0:
        mae = np.mean(np.abs(curr - avg))
        normalized_mae = np.clip(mae / avg_range, 0, 1)
    else:
        normalized_mae = 0

    # Kombination: 70% Korrelation + 30% inverse MAE
    corr_score = max(0, corr)  # negative Korrelation → 0
    combined = 0.7 * corr_score + 0.3 * (1 - normalized_mae)

    return np.clip(combined, 0, 1), {
        "correlation": round(corr, 3),
        "mae": round(mae if avg_range > 0 else 0, 3),
        "days_compared": n,
    }


# ── Composite Score ──────────────────────────────────

def calculate_ki_score(
    ticker: str,
    df: pd.DataFrame,
    year_data: dict,
    avg: list[float],
    std: list[float],
    quick_mode: bool = False,
) -> dict:
    """
    Berechnet den KI Seasonal Score (0-10).

    Args:
        ticker: z.B. "SPY"
        df: Preprocessed DataFrame (mit return, log_return, day_of_year, year)
        year_data: Output von build_year_data()
        avg: Saisonaler Durchschnitt (365 Werte)
        std: Saisonale Standardabweichung (365 Werte)
        quick_mode: True = kein Prophet, schnellere Berechnung

    Returns:
        dict mit score, signal, sub_scores, meta
    """
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    today_doy = now.timetuple().tm_yday

    # Aktuelle Jahres-Daten
    current_yd = year_data.get(current_year)
    if current_yd:
        current_pattern = current_yd["full_365"][:today_doy]
        trading_days_so_far = len(current_yd["days"])
    else:
        current_pattern = []
        trading_days_so_far = 0

    # Historische Daten (ohne aktuelles Jahr)
    hist_years = {y: yd["full_365"] for y, yd in year_data.items() if y != current_year}

    # Jahresrenditen für DTW-Bewertung
    year_returns = {}
    for y, yd in year_data.items():
        if y != current_year and len(yd["full_365"]) > 0:
            year_returns[y] = (yd["full_365"][-1] / yd["full_365"][0] - 1) * 100

    # ── Sub-Scores berechnen ──
    dtw_score, dtw_details = score_dtw_similarity(
        current_pattern, hist_years, year_returns
    )

    if quick_mode:
        prophet_score, prophet_details = 0.5, {"error": "Quick-Mode (übersprungen)"}
    else:
        prophet_score, prophet_details = score_prophet_forecast(df, periods=30)

    wr_score, wr_details = score_win_rate(year_data, current_month)

    tracking_score, tracking_details = score_tracking_quality(
        current_yd["full_365"] if current_yd else [],
        avg,
        trading_days_so_far,
    )

    # ── Composite ──
    composite = (
        dtw_score * SCORE_WEIGHTS["dtw"]
        + prophet_score * SCORE_WEIGHTS["prophet"]
        + wr_score * SCORE_WEIGHTS["win_rate"]
        + tracking_score * SCORE_WEIGHTS["tracking"]
    )
    composite = round(np.clip(composite, 0, 10), 1)

    # Signal
    if composite >= SIGNAL_THRESHOLDS["bullish"]:
        signal = "Bullish"
    elif composite <= SIGNAL_THRESHOLDS["bearish"]:
        signal = "Bearish"
    else:
        signal = "Neutral"

    return {
        "ticker": ticker,
        "score": composite,
        "signal": signal,
        "sub_scores": {
            "dtw": {
                "score": round(dtw_score, 3),
                "weighted": round(dtw_score * SCORE_WEIGHTS["dtw"], 2),
                "details": dtw_details,
            },
            "prophet": {
                "score": round(prophet_score, 3),
                "weighted": round(prophet_score * SCORE_WEIGHTS["prophet"], 2),
                "details": prophet_details,
            },
            "win_rate": {
                "score": round(wr_score, 3),
                "weighted": round(wr_score * SCORE_WEIGHTS["win_rate"], 2),
                "details": wr_details,
            },
            "tracking": {
                "score": round(tracking_score, 3),
                "weighted": round(tracking_score * SCORE_WEIGHTS["tracking"], 2),
                "details": tracking_details,
            },
        },
        "meta": {
            "current_month": current_month,
            "current_doy": today_doy,
            "total_years": len(year_data),
            "trading_days_ytd": trading_days_so_far,
        },
    }


# ── Batch Scanner ────────────────────────────────────

def scan_tickers(
    tickers: list[str],
    years_back: int = 20,
    progress_callback=None,
    quick_mode: bool = True,
) -> list[dict]:
    """
    Scannt mehrere Ticker und berechnet KI-Scores.

    Args:
        tickers: Liste von Ticker-Symbolen
        years_back: Anzahl Jahre für Berechnung
        progress_callback: Optional callback(i, total) für Progress-Bar
        quick_mode: True = schnelle Berechnung ohne Prophet

    Returns:
        Liste von Score-Dicts, sortiert nach Score absteigend
    """
    from shared.data import download_data, preprocess
    from shared.calculations import build_year_data, calculate_seasonal_average
    from shared.symbols import SYMBOLS, get_display_name

    current_year = datetime.now().year
    start_year = current_year - years_back
    results = []

    for i, ticker in enumerate(tickers):
        if progress_callback:
            progress_callback(i, len(tickers))

        try:
            raw_df = download_data(ticker)
            if raw_df is None or raw_df.empty:
                continue

            df = preprocess(raw_df)
            if df is None or df.empty:
                continue

            available_years = sorted([
                y for y in df["year"].unique()
                if start_year <= y <= current_year
            ])

            if len(available_years) < 3:
                continue

            year_data = build_year_data(df, available_years)
            if len(year_data) < 3:
                continue

            avg, std = calculate_seasonal_average(year_data)

            score_result = calculate_ki_score(
                ticker, df, year_data, avg, std, quick_mode=quick_mode
            )

            # Zusätzliche Info für Scanner
            sym_info = SYMBOLS.get(ticker, {})
            score_result["name"] = sym_info.get("name", get_display_name(ticker))
            score_result["kategorie"] = sym_info.get("kategorie", "Sonstige")

            # Aktuelle Monats-Stats aus Win-Rate Details
            wr_details = score_result["sub_scores"]["win_rate"]["details"]
            score_result["win_rate"] = wr_details.get("win_rate", 0)
            score_result["avg_return"] = wr_details.get("avg_return", 0)

            # Abweichung vom Saisonalmuster
            tracking_details = score_result["sub_scores"]["tracking"]["details"]
            score_result["deviation"] = round(
                1 - tracking_details.get("correlation", 0), 3
            )

            results.append(score_result)

        except Exception:
            continue

    if progress_callback:
        progress_callback(len(tickers), len(tickers))

    # Sortiere nach Score absteigend
    results.sort(key=lambda x: x["score"], reverse=True)
    return results

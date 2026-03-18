"""
shared/ai_models.py — KI-Modelle für SeasonalEdge

Phase 1: DTW Pattern Matching, Prophet, Isolation Forest, Claude API
Phase 2: LSTM, XGBoost (TODO)
Phase 3: Transformer (TODO)
"""
import numpy as np
import pandas as pd
from typing import Optional


# ── DTW Pattern Matching ────────────────────────────

def find_similar_years(
    current_pattern: list[float],
    all_years_data: dict[int, list[float]],
    top_n: int = 3,
) -> list[tuple[int, float]]:
    """
    Findet historische Jahre mit ähnlichstem Kursverlauf.

    Args:
        current_pattern: Normalisierte Kursreihe des aktuellen Jahres
        all_years_data: {year: normalisierte Kursreihe}
        top_n: Anzahl ähnlichster Jahre

    Returns:
        [(year, distance), ...] sortiert nach Ähnlichkeit (niedrig = ähnlich)
    """
    try:
        from fastdtw import fastdtw
        from scipy.spatial.distance import euclidean
    except ImportError:
        # Fallback: einfache Korrelation
        return _find_similar_correlation(current_pattern, all_years_data, top_n)

    scores = {}
    for year, pattern in all_years_data.items():
        # Auf gleiche Länge trimmen
        min_len = min(len(current_pattern), len(pattern))
        if min_len < 10:
            continue
        dist, _ = fastdtw(
            current_pattern[:min_len],
            pattern[:min_len],
            dist=euclidean,
        )
        scores[year] = dist

    return sorted(scores.items(), key=lambda x: x[1])[:top_n]


def _find_similar_correlation(
    current_pattern: list[float],
    all_years_data: dict[int, list[float]],
    top_n: int = 3,
) -> list[tuple[int, float]]:
    """Fallback: Korrelationsbasierte Ähnlichkeit (ohne fastdtw)."""
    scores = {}
    for year, pattern in all_years_data.items():
        min_len = min(len(current_pattern), len(pattern))
        if min_len < 10:
            continue
        corr = np.corrcoef(current_pattern[:min_len], pattern[:min_len])[0, 1]
        # Negieren, damit niedrigerer Wert = ähnlicher (wie bei DTW)
        scores[year] = -corr if not np.isnan(corr) else 999

    return sorted(scores.items(), key=lambda x: x[1])[:top_n]


# ── Prophet Forecast ────────────────────────────────

def forecast_seasonal(
    df_prices: pd.DataFrame,
    periods: int = 60,
    yearly: bool = True,
    weekly: bool = False,
) -> Optional[pd.DataFrame]:
    """
    Saisonale Prognose mit Facebook Prophet.

    Args:
        df_prices: DataFrame mit Date und Close
        periods: Anzahl Tage in die Zukunft
        yearly/weekly: Saisonalitätskomponenten

    Returns:
        DataFrame mit ds, yhat, yhat_lower, yhat_upper (oder None bei Fehler)
    """
    try:
        from prophet import Prophet
    except ImportError:
        return None

    df = df_prices.copy()
    if "Date" in df.columns:
        df = df.rename(columns={"Date": "ds", "Close": "y"})
    elif df.index.name == "Date":
        df = df.reset_index().rename(columns={"Date": "ds", "Close": "y"})

    df = df[["ds", "y"]].dropna()

    m = Prophet(
        yearly_seasonality=yearly,
        weekly_seasonality=weekly,
        daily_seasonality=False,
    )
    m.fit(df)
    future = m.make_future_dataframe(periods=periods)
    forecast = m.predict(future)

    return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(periods)


# ── Isolation Forest (Ausreißer-Jahre) ──────────────

def detect_outlier_years(
    year_returns: dict[int, list[float]],
    contamination: float = 0.1,
) -> list[int]:
    """
    Erkennt Jahre die nicht ins typische saisonale Muster passen.

    Args:
        year_returns: {year: [daily_returns]}
        contamination: Anteil erwarteter Ausreißer (0.05-0.2)

    Returns:
        Liste der Ausreißer-Jahre
    """
    try:
        from sklearn.ensemble import IsolationForest
    except ImportError:
        return []

    # Alle auf gleiche Länge bringen
    min_len = min(len(v) for v in year_returns.values())
    years = list(year_returns.keys())
    matrix = np.array([year_returns[y][:min_len] for y in years])

    clf = IsolationForest(contamination=contamination, random_state=42)
    labels = clf.fit_predict(matrix)

    return [y for y, label in zip(years, labels) if label == -1]


# ── Claude API (Natural Language Kommentar) ─────────

def generate_seasonal_commentary(
    ticker: str,
    month: str,
    avg_return: float,
    win_rate: float,
    similar_years: list[tuple[int, float]] = None,
    model: str = "claude-sonnet-4-20250514",
) -> Optional[str]:
    """
    Generiert einen KI-Kommentar zur Saisonalität.

    Args:
        ticker: z.B. "SPY"
        month: z.B. "März"
        avg_return: Durchschnittliche Rendite in %
        win_rate: Win-Rate in %
        similar_years: Output von find_similar_years()
        model: Claude-Modell

    Returns:
        Kommentar als String (oder None bei Fehler)
    """
    try:
        import anthropic
    except ImportError:
        return None

    similar_str = ""
    if similar_years:
        similar_str = f"- Ähnlichste historische Jahre: {', '.join(str(y) for y, _ in similar_years)}"

    prompt = f"""Analysiere kurz das saisonale Muster für {ticker} im Monat {month}:
- Durchschnittliche Rendite: {avg_return:.1f}%
- Win-Rate: {win_rate:.0f}%
{similar_str}
Antworte in 2-3 Sätzen auf Deutsch. Keine Anlageempfehlung."""

    try:
        import os
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            try:
                import streamlit as st
                api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
            except Exception:
                pass

        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=model,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
    except Exception:
        return None

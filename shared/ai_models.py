"""
SeasonalEdge — KI-Modelle für saisonale Analyse

Phase 1:
  - DTW Pattern Matching: Ähnliche historische Jahre finden
  - Prophet: Saisonale Prognose 60 Tage
  - Isolation Forest: Ausreißer-Jahre erkennen
  - Claude API: Natural Language Kommentar

Verwendung:
  from shared.ai_models import find_similar_years, forecast_seasonal
  from shared.ai_models import detect_outlier_years, generate_seasonal_commentary
"""

import os

import numpy as np
import pandas as pd

from shared.logger import app_logger, error_logger


# ══════════════════════════════════════════════════════════════
# 1. DTW Pattern Matching — Ähnliche historische Jahre
# ══════════════════════════════════════════════════════════════

def find_similar_years(
    current_pattern: list[float] | np.ndarray,
    all_years_data: dict[int, list[float] | np.ndarray],
    top_n: int = 3,
) -> list[tuple[int, float]]:
    """
    Findet die ähnlichsten historischen Jahre zum aktuellen Kursverlauf
    mittels Dynamic Time Warping (DTW).

    Args:
        current_pattern: Kumulierte Renditen des aktuellen Jahres (bis heute)
        all_years_data: Dict {Jahr: kumul. Renditen} aller historischen Jahre
        top_n: Anzahl der ähnlichsten Jahre

    Returns:
        Liste von (Jahr, DTW-Distanz) — kleinere Distanz = ähnlicher
    """
    try:
        from fastdtw import fastdtw
        from scipy.spatial.distance import euclidean
    except ImportError:
        error_logger.error("fastdtw/scipy nicht installiert: pip install fastdtw scipy")
        return []

    current = np.array(current_pattern, dtype=float)
    scores: dict[int, float] = {}

    for year, pattern in all_years_data.items():
        try:
            # Pattern auf gleiche Länge wie current trimmen
            hist = np.array(pattern, dtype=float)[:len(current)]
            if len(hist) < 5:
                continue
            dist, _ = fastdtw(current, hist, dist=euclidean)
            scores[year] = dist
        except Exception as e:
            app_logger.warning(f"DTW fehlgeschlagen für {year}: {e}")
            continue

    ranked = sorted(scores.items(), key=lambda x: x[1])[:top_n]
    app_logger.info(
        f"DTW Top-{top_n}: {[(y, round(d, 1)) for y, d in ranked]}"
    )
    return ranked


# ══════════════════════════════════════════════════════════════
# 2. Prophet — Saisonale Prognose
# ══════════════════════════════════════════════════════════════

def forecast_seasonal(
    df_prices: pd.DataFrame,
    periods: int = 60,
    yearly_seasonality: bool = True,
) -> pd.DataFrame | None:
    """
    Saisonale Prognose mit Facebook Prophet.

    Args:
        df_prices: DataFrame mit Spalten 'Date' und 'Close'
        periods: Vorhersage-Horizont in Tagen
        yearly_seasonality: Jährliche Saisonalität aktivieren

    Returns:
        DataFrame mit Spalten: ds, yhat, yhat_lower, yhat_upper
    """
    try:
        from prophet import Prophet
    except ImportError:
        error_logger.error("prophet nicht installiert: pip install prophet")
        return None

    try:
        # Prophet erwartet Spalten 'ds' und 'y'
        prophet_df = df_prices.rename(
            columns={"Date": "ds", "Close": "y"}
        )[["ds", "y"]].copy()
        prophet_df["ds"] = pd.to_datetime(prophet_df["ds"])
        prophet_df = prophet_df.dropna()

        model = Prophet(
            yearly_seasonality=yearly_seasonality,
            weekly_seasonality=False,
            daily_seasonality=False,
            changepoint_prior_scale=0.05,
        )
        model.fit(prophet_df)

        future = model.make_future_dataframe(periods=periods)
        forecast = model.predict(future)

        result = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(periods)
        app_logger.info(f"Prophet-Prognose: {periods} Tage berechnet")
        return result

    except Exception as e:
        error_logger.error(f"Prophet-Prognose fehlgeschlagen: {e}", exc_info=True)
        return None


# ══════════════════════════════════════════════════════════════
# 3. Isolation Forest — Ausreißer-Jahre erkennen
# ══════════════════════════════════════════════════════════════

def detect_outlier_years(
    year_returns: dict[int, list[float] | np.ndarray],
    contamination: float = 0.1,
) -> list[int]:
    """
    Erkennt Ausreißer-Jahre (z.B. 2008, 2020) mittels Isolation Forest.

    Args:
        year_returns: Dict {Jahr: tägliche Renditen}
        contamination: Erwarteter Anteil Ausreißer (0.0–0.5)

    Returns:
        Liste der Ausreißer-Jahre
    """
    try:
        from sklearn.ensemble import IsolationForest
    except ImportError:
        error_logger.error("scikit-learn nicht installiert: pip install scikit-learn")
        return []

    try:
        # Alle Jahre auf gleiche Länge bringen (min. Länge)
        years = sorted(year_returns.keys())
        min_len = min(len(year_returns[y]) for y in years)

        if min_len < 10:
            app_logger.warning("Zu wenige Datenpunkte für Isolation Forest")
            return []

        matrix = np.array([
            np.array(year_returns[y], dtype=float)[:min_len]
            for y in years
        ])

        clf = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
        )
        labels = clf.fit_predict(matrix)

        outliers = [y for y, label in zip(years, labels) if label == -1]
        app_logger.info(f"Ausreißer-Jahre erkannt: {outliers}")
        return outliers

    except Exception as e:
        error_logger.error(f"Isolation Forest fehlgeschlagen: {e}", exc_info=True)
        return []


# ══════════════════════════════════════════════════════════════
# 4. Claude API — Natural Language Kommentar
# ══════════════════════════════════════════════════════════════

def generate_seasonal_commentary(
    ticker: str,
    month: str,
    avg_return: float,
    win_rate: float,
    similar_years: list[tuple[int, float]] | None = None,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 200,
) -> str:
    """
    Generiert einen kurzen KI-Kommentar zur Saisonalität.

    Args:
        ticker: z.B. "SPY"
        month: z.B. "März"
        avg_return: Durchschnittliche Monatsrendite in %
        win_rate: Win-Rate in %
        similar_years: Optionale DTW-Ergebnisse
        model: Claude-Modell
        max_tokens: Max. Antwortlänge

    Returns:
        Kommentar-Text (2-3 Sätze, Deutsch)
    """
    try:
        import anthropic
    except ImportError:
        error_logger.error("anthropic nicht installiert: pip install anthropic")
        return ""

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        app_logger.warning("ANTHROPIC_API_KEY nicht gesetzt — Kommentar übersprungen")
        return ""

    similar_info = ""
    if similar_years:
        years_str = ", ".join(str(y) for y, _ in similar_years)
        similar_info = f"\n- Ähnlichste historische Jahre (DTW): {years_str}"

    prompt = (
        f"Analysiere kurz das saisonale Muster für {ticker} im Monat {month}:\n"
        f"- Durchschnittliche Rendite: {avg_return:.1f}%\n"
        f"- Win-Rate: {win_rate:.0f}%"
        f"{similar_info}\n"
        f"Antworte in 2-3 Sätzen auf Deutsch. Keine Anlageempfehlung."
    )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        commentary = msg.content[0].text
        app_logger.info(f"Claude-Kommentar generiert: {ticker}/{month}")
        return commentary

    except Exception as e:
        error_logger.error(f"Claude API fehlgeschlagen: {e}", exc_info=True)
        return ""

"""
shared/chronos_forecast.py — Chronos-Bolt Probabilistic Forecast
=================================================================
Amazon Chronos-Bolt-Tiny: 9M Parameter Foundation Model.
Liefert probabilistische Prognosen mit Konfidenzintervallen.
Laeuft auf CPU in unter 1 Sekunde pro Ticker.

Kein Streamlit-Import! Reine Berechnung.
"""

import numpy as np
import pandas as pd
from typing import Optional


_pipeline = None


_MODEL_FALLBACK = ["amazon/chronos-bolt-tiny", "amazon/chronos-t5-tiny"]


def _get_pipeline(model_id: str = None):
    """Lazy-Init des Chronos-Pipelines (einmal laden, dann gecacht)."""
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    try:
        from chronos import ChronosPipeline
        import torch
    except ImportError:
        return None

    models = [model_id] if model_id else _MODEL_FALLBACK
    for mid in models:
        try:
            _pipeline = ChronosPipeline.from_pretrained(
                mid,
                device_map="cpu",
                dtype=torch.float32,
            )
            return _pipeline
        except Exception:
            continue
    return None


def forecast_chronos(
    df: pd.DataFrame,
    periods: int = 30,
    quantiles: list[float] = None,
    close_col: str = "Close",
) -> Optional[pd.DataFrame]:
    """
    Probabilistische Prognose mit Chronos-Bolt-Tiny.

    Args:
        df: DataFrame mit DatetimeIndex + Close
        periods: Anzahl Tage in die Zukunft
        quantiles: Quantile fuer Konfidenzintervalle
        close_col: Name der Preis-Spalte

    Returns:
        DataFrame mit: ds, yhat, yhat_lower, yhat_upper, p_positive
        oder None bei Fehler
    """
    if quantiles is None:
        quantiles = [0.05, 0.5, 0.95]

    pipeline = _get_pipeline()
    if pipeline is None:
        return None

    try:
        import torch

        series = df[close_col].dropna().values
        if len(series) < 30:
            return None

        context = torch.tensor(series, dtype=torch.float32).unsqueeze(0)

        forecast = pipeline.predict(
            context,
            prediction_length=periods,
            num_samples=100,
            limit_prediction_length=False,
        )

        # forecast shape: (1, num_samples, prediction_length)
        samples = forecast[0].numpy()  # (num_samples, prediction_length)

        # Quantile berechnen
        q_low = np.quantile(samples, quantiles[0], axis=0)
        q_med = np.quantile(samples, quantiles[1], axis=0)
        q_high = np.quantile(samples, quantiles[2], axis=0)

        # Wahrscheinlichkeit positiv (Preis > letzter Close)
        last_close = series[-1]
        p_positive = (samples[:, -1] > last_close).mean()

        # Datumsindex fuer Forecast
        last_date = df.index[-1]
        future_dates = pd.bdate_range(start=last_date + pd.Timedelta(days=1), periods=periods)

        result = pd.DataFrame({
            "ds": future_dates[:len(q_med)],
            "yhat_lower": q_low,
            "yhat": q_med,
            "yhat_upper": q_high,
        })

        # Erwartete Rendite
        expected_return = (q_med[-1] - last_close) / last_close * 100

        result.attrs["expected_return"] = round(float(expected_return), 2)
        result.attrs["p_positive"] = round(float(p_positive * 100), 1)
        result.attrs["last_close"] = round(float(last_close), 2)

        return result

    except Exception:
        return None


def score_chronos_forecast(
    df: pd.DataFrame,
    periods: int = 30,
) -> tuple[float, dict]:
    """
    Chronos Sub-Score fuer KI Score (ersetzt Prophet).

    Returns:
        (normalized_score 0-1, details_dict)
    """
    forecast = forecast_chronos(df, periods=periods)

    if forecast is None:
        return 0.5, {"error": "Chronos nicht verfuegbar", "forecast_return": 0}

    expected_return = forecast.attrs.get("expected_return", 0)
    p_positive = forecast.attrs.get("p_positive", 50)

    # Mapping: -3% -> 0.0, 0% -> 0.5, +3% -> 1.0
    raw_score = np.clip((expected_return + 3) / 6, 0.0, 1.0)

    return raw_score, {
        "forecast_return": expected_return,
        "p_positive": p_positive,
        "direction": "bullish" if expected_return > 0 else "bearish",
        "forecast_df": forecast,
    }


def build_chronos_chart(
    df: pd.DataFrame,
    forecast: pd.DataFrame,
    ticker: str = "",
) -> "go.Figure":
    """Plotly-Chart: Historisch + Forecast mit Konfidenzband."""
    import plotly.graph_objects as go
    from shared.constants import SE_COLORS
    from shared.charts import apply_se_theme

    fig = go.Figure()

    # Letzte 60 Handelstage historisch
    hist = df.tail(60)
    fig.add_trace(go.Scatter(
        x=hist.index, y=hist["Close"],
        mode="lines", line=dict(color=SE_COLORS["text_primary"], width=1.5),
        name="Historisch",
    ))

    # Konfidenzband
    fig.add_trace(go.Scatter(
        x=forecast["ds"], y=forecast["yhat_upper"],
        mode="lines", line=dict(width=0),
        showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=forecast["ds"], y=forecast["yhat_lower"],
        mode="lines", line=dict(width=0),
        fill="tonexty", fillcolor="rgba(0,212,170,0.12)",
        showlegend=False, hoverinfo="skip",
    ))

    # Median-Forecast
    fig.add_trace(go.Scatter(
        x=forecast["ds"], y=forecast["yhat"],
        mode="lines",
        line=dict(color=SE_COLORS["accent"], width=2.5),
        name=f'Forecast ({forecast.attrs.get("p_positive", "?")}% positiv)',
        hovertemplate="%{x|%d.%m}: %{y:.2f}<extra></extra>",
    ))

    ret = forecast.attrs.get("expected_return", 0)
    title = f"{ticker} — Chronos Forecast ({ret:+.1f}%)" if ticker else f"Chronos Forecast ({ret:+.1f}%)"
    fig = apply_se_theme(fig, title=title, height=350)
    fig.update_yaxes(title="Preis")

    return fig

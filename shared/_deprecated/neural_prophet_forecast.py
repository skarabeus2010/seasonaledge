"""
shared/neural_prophet_forecast.py — NeuralProphet Saisonalitaets-Analyse
=========================================================================
PyTorch-basiertes Modell mit expliziten Saisonalitaets-Komponenten.
Fuer Einzelticker-Pages: trainiert pro Ticker (~3s), liefert zerlegte Saisonalitaet.

Kein Streamlit-Import! Reine Berechnung.
"""

import numpy as np
import pandas as pd
from typing import Optional
import logging

# NeuralProphet ist sehr gespraechig — unterdruecken
logging.getLogger("neuralprophet").setLevel(logging.WARNING)
logging.getLogger("pytorch_lightning").setLevel(logging.WARNING)


def forecast_neural_prophet(
    df: pd.DataFrame,
    periods: int = 30,
    yearly: bool = True,
    weekly: bool = True,
    close_col: str = "Close",
) -> Optional[dict]:
    """
    NeuralProphet Forecast mit expliziter Saisonalitaets-Zerlegung.

    Args:
        df: DataFrame mit DatetimeIndex + Close
        periods: Tage in die Zukunft
        yearly: Jahressaisonalitaet modellieren
        weekly: Wochensaisonalitaet modellieren
        close_col: Preis-Spalte

    Returns:
        dict mit: forecast_df, components, expected_return, seasonal_plot_data
        oder None bei Fehler
    """
    try:
        from neuralprophet import NeuralProphet, set_log_level
        set_log_level("WARNING")
    except ImportError:
        return None

    if len(df) < 100:
        return None

    try:
        # Daten vorbereiten (NeuralProphet erwartet 'ds' + 'y')
        ndf = df[[close_col]].copy()
        ndf = ndf.reset_index()
        ndf.columns = ["ds", "y"]
        ndf["ds"] = pd.to_datetime(ndf["ds"])
        ndf = ndf.dropna()

        # Modell erstellen
        m = NeuralProphet(
            yearly_seasonality=yearly,
            weekly_seasonality=weekly,
            daily_seasonality=False,
            n_forecasts=periods,
            learning_rate=0.1,
            epochs=50,
        )

        # Training (unterdrueckt Output)
        m.fit(ndf, freq="B", progress=False)

        # Forecast
        future = m.make_future_dataframe(ndf, periods=periods)
        forecast = m.predict(future)

        # Letzte periods Zeilen = eigentliche Prognose
        forecast_future = forecast.tail(periods).copy()

        # Erwartete Rendite
        last_close = ndf["y"].iloc[-1]
        last_forecast = forecast_future[f"yhat{periods}"].iloc[-1] if f"yhat{periods}" in forecast_future.columns else forecast_future["yhat1"].iloc[-1]

        expected_return = (last_forecast - last_close) / last_close * 100

        # Saisonale Komponenten extrahieren
        components = {}
        # In-sample Forecast fuer Komponentenzerlegung
        in_sample = m.predict(ndf)

        if yearly:
            yearly_cols = [c for c in in_sample.columns if c.startswith("season_yearly")]
            if yearly_cols:
                components["yearly"] = in_sample[["ds"] + yearly_cols[:1]].copy()
                components["yearly"].columns = ["ds", "yearly"]

        if weekly:
            weekly_cols = [c for c in in_sample.columns if c.startswith("season_weekly")]
            if weekly_cols:
                components["weekly"] = in_sample[["ds"] + weekly_cols[:1]].copy()
                components["weekly"].columns = ["ds", "weekly"]

        trend_cols = [c for c in in_sample.columns if c.startswith("trend")]
        if trend_cols:
            components["trend"] = in_sample[["ds"] + trend_cols[:1]].copy()
            components["trend"].columns = ["ds", "trend"]

        return {
            "forecast_df": forecast_future,
            "components": components,
            "expected_return": round(float(expected_return), 2),
            "last_close": round(float(last_close), 2),
            "model": m,
        }

    except Exception:
        return None


def build_neural_prophet_chart(
    df: pd.DataFrame,
    result: dict,
    ticker: str = "",
) -> "go.Figure":
    """Plotly-Chart: Saisonale Komponenten aus NeuralProphet."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    from shared.constants import SE_COLORS
    from shared.charts import apply_se_theme

    components = result.get("components", {})
    n_plots = len(components)

    if n_plots == 0:
        return go.Figure()

    titles = []
    for key in components:
        if key == "yearly":
            titles.append("Jahressaisonalitaet")
        elif key == "weekly":
            titles.append("Wochensaisonalitaet")
        elif key == "trend":
            titles.append("Trend")
        else:
            titles.append(key)

    fig = make_subplots(
        rows=n_plots, cols=1,
        shared_xaxes=False,
        subplot_titles=titles,
        vertical_spacing=0.12,
    )

    colors = {
        "yearly": SE_COLORS["accent_warm"],
        "weekly": SE_COLORS["accent"],
        "trend": SE_COLORS["accent_blue"],
    }

    for i, (key, comp_df) in enumerate(components.items(), 1):
        color = colors.get(key, SE_COLORS["text_primary"])
        fig.add_trace(go.Scatter(
            x=comp_df["ds"], y=comp_df[key],
            mode="lines", line=dict(color=color, width=1.5),
            name=key.title(), showlegend=False,
        ), row=i, col=1)

    title = f"{ticker} — NeuralProphet Komponenten" if ticker else "NeuralProphet Komponenten"
    fig = apply_se_theme(fig, title=title, height=220 * n_plots)

    for ann in fig.layout.annotations:
        ann.font.color = SE_COLORS["text_muted"]
        ann.font.size = 11

    return fig

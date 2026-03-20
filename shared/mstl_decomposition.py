"""
shared/mstl_decomposition.py — Multi-Saisonalitaets-Zerlegung (MSTL)
======================================================================
Zerlegt eine Kursreihe in: Trend + Wochensaisonalitaet + Jahressaisonalitaet + Residual.
Nutzt statsmodels MSTL (Multiple Seasonal-Trend decomposition using LOESS).

Kein Streamlit-Import! Reine Berechnung.
"""

import numpy as np
import pandas as pd
from typing import Optional


def decompose_mstl(
    df: pd.DataFrame,
    periods: list[int] = None,
    close_col: str = "Close",
) -> Optional[dict]:
    """
    MSTL-Zerlegung einer Kursreihe.

    Args:
        df: DataFrame mit DatetimeIndex + Close-Spalte
        periods: Saisonale Perioden in Handelstagen.
                 Default: [5, 252] (Wochen + Jahressaisonalitaet)
        close_col: Name der Preis-Spalte

    Returns:
        dict mit: trend, seasonal_weekly, seasonal_yearly, residual,
                  seasonal_strength_weekly, seasonal_strength_yearly
        oder None bei Fehler
    """
    try:
        from statsmodels.tsa.seasonal import MSTL
    except ImportError:
        return None

    if periods is None:
        periods = [5, 252]

    if len(df) < max(periods) * 2:
        return None

    series = df[close_col].dropna()
    if len(series) < max(periods) * 2:
        return None

    try:
        decomposition = MSTL(series, periods=periods).fit()
    except Exception:
        return None

    trend = decomposition.trend
    residual = decomposition.resid
    seasonal = decomposition.seasonal

    # seasonal ist ein DataFrame mit einer Spalte pro Periode
    result = {
        "trend": trend,
        "residual": residual,
        "index": series.index,
    }

    # Saisonale Komponenten extrahieren
    if isinstance(seasonal, pd.DataFrame):
        cols = seasonal.columns.tolist()
        if len(cols) >= 1:
            result["seasonal_weekly"] = seasonal.iloc[:, 0]
            result["seasonal_weekly_label"] = f"Periode {periods[0]}d"
        if len(cols) >= 2:
            result["seasonal_yearly"] = seasonal.iloc[:, 1]
            result["seasonal_yearly_label"] = f"Periode {periods[1]}d"
    else:
        result["seasonal_weekly"] = seasonal
        result["seasonal_weekly_label"] = f"Periode {periods[0]}d"

    # Saisonale Staerke berechnen (Anteil der Varianz)
    total_var = np.var(series.values)
    if total_var > 0:
        if "seasonal_weekly" in result:
            result["strength_weekly"] = round(
                float(np.var(result["seasonal_weekly"].values) / total_var * 100), 1
            )
        if "seasonal_yearly" in result:
            result["strength_yearly"] = round(
                float(np.var(result["seasonal_yearly"].values) / total_var * 100), 1
            )
        result["strength_trend"] = round(
            float(np.var(trend.values) / total_var * 100), 1
        )
    else:
        result["strength_weekly"] = 0
        result["strength_yearly"] = 0
        result["strength_trend"] = 0

    return result


def compute_seasonal_amplitude(
    df: pd.DataFrame,
    period: int = 252,
) -> float:
    """
    Berechnet die saisonale Amplitude (Staerke des Jahresmusters).
    Nützlich als Scanner-Metrik: "Wie stark ist die Saisonalitaet?"

    Returns:
        Amplitude in % der Gesamtvarianz (0-100)
    """
    result = decompose_mstl(df, periods=[period])
    if result is None:
        return 0.0
    return result.get("strength_weekly", 0.0)


def build_decomposition_figure(
    result: dict,
    ticker: str = "",
) -> "go.Figure":
    """
    Plotly-Figure mit 4 Subplots: Trend, Woche, Jahr, Residual.
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    from shared.constants import SE_COLORS
    from shared.charts import apply_se_theme

    has_yearly = "seasonal_yearly" in result
    n_rows = 4 if has_yearly else 3

    titles = ["Trend"]
    if "seasonal_weekly" in result:
        titles.append(f'Wochensaisonalitaet ({result.get("seasonal_weekly_label", "5d")})')
    if has_yearly:
        titles.append(f'Jahressaisonalitaet ({result.get("seasonal_yearly_label", "252d")})')
    titles.append("Residual")

    fig = make_subplots(
        rows=n_rows, cols=1,
        shared_xaxes=True,
        subplot_titles=titles,
        vertical_spacing=0.06,
    )

    idx = result["index"]
    row = 1

    # Trend
    fig.add_trace(go.Scatter(
        x=idx, y=result["trend"],
        mode="lines", line=dict(color=SE_COLORS["accent_blue"], width=1.5),
        name="Trend", showlegend=False,
    ), row=row, col=1)
    row += 1

    # Weekly
    if "seasonal_weekly" in result:
        fig.add_trace(go.Scatter(
            x=idx, y=result["seasonal_weekly"],
            mode="lines", line=dict(color=SE_COLORS["accent"], width=1),
            name="Woche", showlegend=False,
        ), row=row, col=1)
        row += 1

    # Yearly
    if has_yearly:
        fig.add_trace(go.Scatter(
            x=idx, y=result["seasonal_yearly"],
            mode="lines", line=dict(color=SE_COLORS["accent_warm"], width=1),
            name="Jahr", showlegend=False,
        ), row=row, col=1)
        row += 1

    # Residual
    fig.add_trace(go.Scatter(
        x=idx, y=result["residual"],
        mode="lines", line=dict(color=SE_COLORS["text_muted"], width=0.8),
        name="Residual", showlegend=False,
    ), row=row, col=1)

    title = f"{ticker} — MSTL Saisonalitaets-Zerlegung" if ticker else "MSTL Zerlegung"
    fig = apply_se_theme(fig, title=title, height=160 * n_rows)

    # Subtitle-Farben anpassen
    for ann in fig.layout.annotations:
        ann.font.color = SE_COLORS["text_muted"]
        ann.font.size = 11

    return fig

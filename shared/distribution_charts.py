"""
shared/distribution_charts.py — Wiederverwendbare Verteilungs-Charts
=====================================================================
Box-Plots, Heatmaps, Kontext-Panels für Rendite-Verteilungen.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from shared.constants import SE_COLORS
from shared.charts import apply_se_theme, apply_se_heatmap_theme, apply_se_box_theme


def _hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    """Hex-Farbe (#RRGGBB) → rgba(r,g,b,a)."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def build_box_plot(
    groups: dict[str, list[float]],
    colors: list | dict,
    title: str = "",
    x_title: str = "",
    y_title: str = "",
    current_key: str | None = None,
) -> go.Figure:
    """
    Generischer Box-Plot für mehrere Gruppen.

    Args:
        groups:      {"Label": [Renditen ...], ...}
        colors:      Liste oder Dict mit Farben pro Gruppe (Index oder Key)
        title:       Chart-Titel
        x_title:     X-Achsen-Beschriftung
        y_title:     Y-Achsen-Beschriftung
        current_key: Schlüssel der aktuell hervorgehobenen Gruppe
    """
    fig = go.Figure()

    for i, (label, values) in enumerate(groups.items()):
        if not values or len(values) < 2:
            continue

        # Farbe bestimmen
        if isinstance(colors, dict):
            color = colors.get(i, colors.get(label, "#888"))
        elif isinstance(colors, list) and i < len(colors):
            color = colors[i]
        else:
            color = "#888"

        is_current = (label == current_key)
        line_width = 2.5 if is_current else 1.5
        opacity = 1.0 if is_current else 0.75

        fig.add_trace(go.Box(
            y=values,
            name=label,
            marker_color=color,
            line=dict(width=line_width, color=color),
            fillcolor=_hex_to_rgba(color, 0.15) if isinstance(color, str) and color.startswith("#") else color,
            opacity=opacity,
            boxmean="sd",
            hovertemplate=(
                f"<b>{label}</b><br>"
                "Median: %{median:.2f}%<br>"
                "Q1: %{q1:.2f}% · Q3: %{q3:.2f}%<br>"
                "Min: %{lowerfence:.2f}% · Max: %{upperfence:.2f}%"
                "<extra></extra>"
            ),
        ))

    fig.add_hline(y=0, line_dash="dash",
                  line_color=SE_COLORS["zero_line"], line_width=1)

    fig = apply_se_box_theme(fig, title=title, height=420)
    fig.update_xaxes(title=x_title)
    fig.update_yaxes(title=y_title, tickformat="+.1f", ticksuffix="%")

    return fig


def build_decade_monthly_heatmap(
    df: pd.DataFrame,
    ticker: str = "",
) -> go.Figure:
    """
    Heatmap: Dekaden-Endziffer (Y) × Monat (X), Zellen = Ø Monatsrendite.

    Args:
        df:     DataFrame mit DatetimeIndex + 'Close'-Spalte
        ticker: Ticker für Titel
    """
    MONTH_LABELS = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
                    "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]

    # Monatsrenditen berechnen
    monthly = df["Close"].resample("ME").last().pct_change().dropna() * 100
    monthly_df = pd.DataFrame({
        "year": monthly.index.year,
        "month": monthly.index.month,
        "return": monthly.values,
    })
    monthly_df["digit"] = monthly_df["year"] % 10

    # Pivot: Ø Rendite pro Digit × Monat
    pivot = monthly_df.groupby(["digit", "month"])["return"].mean().unstack(fill_value=0)
    # Sicherstellen dass alle 12 Monate da sind
    for m in range(1, 13):
        if m not in pivot.columns:
            pivot[m] = 0.0
    pivot = pivot[list(range(1, 13))]

    # Alle 10 Ziffern sicherstellen
    for d in range(10):
        if d not in pivot.index:
            pivot.loc[d] = 0.0
    pivot = pivot.sort_index()

    z = pivot.values
    y_labels = [f"x{d}" for d in range(10)]

    fig = go.Figure(go.Heatmap(
        z=z,
        x=MONTH_LABELS,
        y=y_labels,
        colorscale=[
            [0.0, SE_COLORS["negative"]],
            [0.5, SE_COLORS["surface"]],
            [1.0, SE_COLORS["positive"]],
        ],
        zmid=0,
        text=np.round(z, 2),
        texttemplate="%{text:+.1f}%",
        textfont=dict(size=10, color=SE_COLORS["text_muted"]),
        hovertemplate=(
            "<b>%{y} · %{x}</b><br>"
            "Ø Rendite: %{z:+.2f}%<extra></extra>"
        ),
        colorbar=dict(
            title=dict(text="Ø %", font=dict(color=SE_COLORS["text_muted"])),
            ticksuffix="%",
            tickfont=dict(color=SE_COLORS["text_muted"]),
        ),
    ))

    heatmap_title = f"{ticker} — Ø Monatsrendite nach Dekaden-Endziffer" if ticker else "Ø Monatsrendite nach Dekade"
    fig = apply_se_heatmap_theme(fig, title=heatmap_title, height=420)
    fig.update_xaxes(title="Monat", side="bottom")
    fig.update_yaxes(title="Dekaden-Endziffer", autorange="reversed")

    # Aktuelle Dekaden-Zeile markieren (farbiger Rand)
    from datetime import datetime as _dt
    current_digit = _dt.now().year % 10
    # y-Achse ist reversed → Position = current_digit
    fig.add_shape(
        type="rect",
        x0=-0.5, x1=11.5,
        y0=current_digit - 0.5, y1=current_digit + 0.5,
        line=dict(color="#F1C40F", width=2.5),
        fillcolor="rgba(0,0,0,0)",
        layer="above",
    )

    return fig


def build_context_panel_data(
    groups: dict[str, list[float]],
    current_key: str,
    label: str = "Periode",
) -> dict:
    """
    Berechnet Kontext-Statistiken für eine bestimmte Gruppe relativ zu allen anderen.

    Args:
        groups:      {"Label": [Renditen ...], ...}
        current_key: Schlüssel der aktuellen Gruppe (z.B. "X6")
        label:       Beschriftung (z.B. "Jahr", "Monat")

    Returns:
        dict mit: mean, median, std, win_rate, n, best, worst, rating, all_mean
    """
    values = groups.get(current_key, [])
    if not values:
        return {
            "mean": 0, "median": 0, "std": 0, "win_rate": 0,
            "n": 0, "best": 0, "worst": 0, "rating": "Keine Daten",
            "all_mean": 0,
        }

    arr = np.array(values)
    mean = float(np.mean(arr))
    median = float(np.median(arr))
    std = float(np.std(arr))
    win_rate = float((arr > 0).sum() / len(arr) * 100)
    n = len(arr)
    best = float(np.max(arr))
    worst = float(np.min(arr))

    # Ø aller Gruppen für Vergleich
    all_vals = [v for vs in groups.values() for v in vs]
    all_mean = float(np.mean(all_vals)) if all_vals else 0.0

    # Rating
    if mean > all_mean + std:
        rating = f"Deutlich überdurchschnittlich (Ø {mean:+.1f}% vs. Gesamt-Ø {all_mean:+.1f}%)"
    elif mean > all_mean:
        rating = f"Leicht überdurchschnittlich (Ø {mean:+.1f}% vs. Gesamt-Ø {all_mean:+.1f}%)"
    elif mean > all_mean - std:
        rating = f"Leicht unterdurchschnittlich (Ø {mean:+.1f}% vs. Gesamt-Ø {all_mean:+.1f}%)"
    else:
        rating = f"Deutlich unterdurchschnittlich (Ø {mean:+.1f}% vs. Gesamt-Ø {all_mean:+.1f}%)"

    return {
        "mean": mean,
        "median": median,
        "std": std,
        "win_rate": win_rate,
        "n": n,
        "best": best,
        "worst": worst,
        "rating": rating,
        "all_mean": all_mean,
    }

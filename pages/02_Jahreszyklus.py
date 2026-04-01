"""
SeasonAlpha — Jahreszyklus (Yearly Seasonality)
=================================================
Saisonaler Jahresverlauf mit Pressure Chart, Detrend-Indikator,
Praesidentenzyklus-Overlay, Heatmap, Monats-/Quartals-Performance,
Anomalie-Radar.
"""

import sys, os, pathlib
try:
    _project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
except NameError:
    _project_dir = os.getcwd()
if not os.path.isdir(os.path.join(_project_dir, "shared")):
    for _candidate in [os.getcwd(), os.path.dirname(os.path.abspath(sys.argv[-1])) if sys.argv else ""]:
        if os.path.isdir(os.path.join(_candidate, "shared")):
            _project_dir = _candidate
            break
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

import streamlit as st

st.set_page_config(
    page_title="Jahreszyklus — SeasonAlpha",
    page_icon="📈",
    layout="wide",
)

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

from shared.ticker_select import ticker_select
from shared.constants import (
    DEFAULT_TICKER, DEFAULT_YEARS, SE_COLORS, MONTH_NAMES_DE,
    CYCLE_COLORS, PRESSURE_PERIODS, COLOR_PRESSURE,
)
from shared.data import download_data, preprocess
from shared.calculations import (
    build_year_data, calculate_seasonal_average, calculate_period_stats,
    calculate_pressure_curve, get_presidential_cycle_year,
)
from shared.charts import apply_se_theme

from shared.design import inject_se_css
from shared.footer import render_footer
inject_se_css()

MONTH_STARTS = [datetime(2024, m, 1).timetuple().tm_yday for m in range(1, 13)]
MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]

MONTH_DOY = {
    1: (1, 31), 2: (32, 59), 3: (60, 90), 4: (91, 120),
    5: (121, 151), 6: (152, 181), 7: (182, 212), 8: (213, 243),
    9: (244, 273), 10: (274, 304), 11: (305, 334), 12: (335, 365),
}
QUARTER_DOY = {"Q1": (1, 90), "Q2": (91, 181), "Q3": (182, 273), "Q4": (274, 365)}

# Plotly config: kein Modebar-Slider, Hover aktiv
_PLOTLY_CFG = {"displayModeBar": False, "scrollZoom": False}

# ── "We are here!" — zentraler Helper ─────────────────
from shared.we_are_here import annotation as _we_are_here_annotation
from shared import we_are_here as _wah
WE_ARE_HERE_COLOR = _wah.MARKER_COLOR_SOLID


# ══════════════════════════════════════════════════════════════
# CHART-BUILDER
# ══════════════════════════════════════════════════════════════

def build_yearly_chart(year_data, avg, std, df, ticker, smoothing,
                       show_individual, show_bands, show_current,
                       show_pressure, cycle_overlay, show_percentile_bands=False):
    """Haupt-Saisonalchart mit optionalem Pressure + Praesidentenzyklus."""
    fig = go.Figure()
    x_days = list(range(1, 366))
    current_year = datetime.now().year

    # Einzeljahre
    if show_individual:
        for year, yd in year_data.items():
            fig.add_trace(go.Scatter(
                x=x_days, y=yd["full_365"], mode="lines",
                line=dict(color="rgba(200,220,255,0.15)", width=0.8),
                showlegend=False, hoverinfo="skip",
            ))

    # Perzentil-Baender (25./75.)
    if show_percentile_bands and len(year_data) >= 5:
        all_curves = np.array([yd["full_365"] for yd in year_data.values()])
        p25 = np.percentile(all_curves, 25, axis=0).tolist()
        p75 = np.percentile(all_curves, 75, axis=0).tolist()
        fig.add_trace(go.Scatter(
            x=x_days, y=p75, mode="lines", line=dict(width=0),
            showlegend=False, hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=x_days, y=p25, mode="lines", line=dict(width=0),
            fill="tonexty", fillcolor="rgba(52,211,153,0.07)",
            name="25.–75. Perzentil", hoverinfo="skip",
        ))

    # Konfidenzband
    if show_bands and std:
        upper = [avg[i] + std[i] for i in range(365)]
        lower = [avg[i] - std[i] for i in range(365)]
        fig.add_trace(go.Scatter(
            x=x_days, y=upper, mode="lines", line=dict(width=0),
            showlegend=False, hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=x_days, y=lower, mode="lines", line=dict(width=0),
            fill="tonexty", fillcolor="rgba(77,159,255,0.08)",
            name="±1 Sigma", hoverinfo="skip",
        ))

    # Saisonaler Durchschnitt
    avg_smooth = avg.copy()
    if smoothing > 1:
        avg_smooth = pd.Series(avg_smooth).rolling(
            smoothing, center=True, min_periods=1
        ).mean().tolist()

    fig.add_trace(go.Scatter(
        x=x_days, y=avg_smooth, mode="lines",
        line=dict(color=SE_COLORS["accent_blue"], width=3),
        name=f"Saisonaler Ø ({len(year_data)} Jahre)",
        hovertemplate="Tag %{x}<br>Wert: %{y:.2f}<extra></extra>",
    ))

    # Praesidentenzyklus-Overlay
    if cycle_overlay:
        for cycle_name in cycle_overlay:
            cycle_years = [y for y in year_data.keys()
                           if get_presidential_cycle_year(y) == cycle_name]
            if len(cycle_years) < 2:
                continue
            cycle_curves = [year_data[y]["full_365"] for y in cycle_years]
            cycle_avg = [np.mean([c[d] for c in cycle_curves]) for d in range(365)]
            if smoothing > 1:
                cycle_avg = pd.Series(cycle_avg).rolling(
                    smoothing, center=True, min_periods=1
                ).mean().tolist()
            short_label = cycle_name.split("(")[1].rstrip(")") if "(" in cycle_name else cycle_name
            fig.add_trace(go.Scatter(
                x=x_days, y=cycle_avg, mode="lines",
                line=dict(color=CYCLE_COLORS[cycle_name], width=2, dash="dash"),
                name=f"{short_label} ({len(cycle_years)}y)",
                hovertemplate=f"{short_label}<br>Tag %{{x}}<br>%{{y:.2f}}<extra></extra>",
            ))

    # Aktuelles Jahr
    if show_current and current_year in year_data:
        yd = year_data[current_year]
        today_doy = datetime.now().timetuple().tm_yday
        display_days = [d for d in yd["days"] if d <= today_doy]
        display_vals = yd["cumulative"][:len(display_days)]
        if display_days:
            fig.add_trace(go.Scatter(
                x=display_days, y=display_vals, mode="lines",
                line=dict(color="#F1C40F", width=2.5),
                name=f"{current_year} (aktuell)",
                hovertemplate=f"{current_year}<br>Tag %{{x}}<br>%{{y:.2f}}<extra></extra>",
            ))

    fig.add_hline(y=100, line_dash="dash", line_color="rgba(255,255,255,0.2)", line_width=1)

    # Pressure als sekundaere Y-Achse
    pressure_info = None
    if show_pressure:
        p_curve, max_years, avail_periods = calculate_pressure_curve(df, smoothing_window=smoothing)
        if p_curve:
            fig.add_trace(go.Scatter(
                x=x_days, y=p_curve, mode="lines",
                line=dict(color=COLOR_PRESSURE, width=2),
                name="Pressure", yaxis="y2",
                hovertemplate="Pressure: %{y:+.2f}<extra></extra>",
            ))
            unavailable = [p for p in PRESSURE_PERIODS if p > max_years]
            if unavailable and avail_periods:
                pressure_info = (
                    f"Pressure Chart über die letzten **{max(avail_periods)} Jahre** "
                    f"(Datenreihe: {max_years} Jahre)."
                )

    fig = apply_se_theme(
        fig,
        title=f"{ticker} — Saisonaler Jahresverlauf ({len(year_data)} Jahre)",
        height=520,
    )
    fig.update_xaxes(
        tickmode="array", tickvals=MONTH_STARTS, ticktext=MONTH_LABELS,
        range=[1, 365],
    )
    fig.update_yaxes(title="Normalisiert (Start = 100)")

    if show_pressure:
        fig.update_layout(
            yaxis2=dict(
                title=dict(text="Pressure", font=dict(color=COLOR_PRESSURE, size=11)),
                tickfont=dict(color=COLOR_PRESSURE, size=10),
                overlaying="y", side="right", showgrid=False,
                tickformat="+.1f", zeroline=True,
                zerolinecolor="rgba(224,86,160,0.2)",
            )
        )

    return fig, pressure_info


def build_detrend_chart(avg, ticker, n_years):
    """
    Detrend-Indikator: Saisonaler Durchschnittsverlauf ohne Trendkomponente.

    Formel:
      daily_drift = (avg[-1] - avg[0]) / len(avg)
      detrended[i] = (avg[i] - avg[0]) - (i+1) * daily_drift

    Der lineare Jahrestrend wird subtrahiert. Was bleibt ist die reine
    saisonale Schwankung: Wann im Jahr liegt der Kurs typischerweise
    über oder unter seinem Trend?

    Skalierung: 0–100 (Midline 50). Über 50 = saisonal überdurchschnittlich,
    unter 50 = saisonal unterdurchschnittlich.
    """
    if len(avg) < 10:
        return None
    end_val = avg[-1] - avg[0]
    daily_drift = end_val / len(avg)
    raw = [(avg[i] - avg[0]) - ((i + 1) * daily_drift) for i in range(len(avg))]

    # Skalierung auf 0–100 (Midline = 50)
    r_min, r_max = min(raw), max(raw)
    r_range = r_max - r_min
    if r_range == 0:
        detrended = [50.0] * len(raw)
    else:
        detrended = [((v - r_min) / r_range) * 100 for v in raw]

    fig = go.Figure()
    x_days = list(range(1, 366))

    fig.add_trace(go.Scatter(
        x=x_days, y=detrended, mode="lines",
        line=dict(color="#FF6B6B", width=2.5),
        fill="tonexty", fillcolor="rgba(255,107,107,0.08)",
        name="Saisonaler Druck",
        hovertemplate="Tag %{x}<br>Wert: %{y:.1f}<extra></extra>",
    ))

    # Midline bei 50
    fig.add_hline(y=50, line_dash="dash", line_color="rgba(255,255,255,0.3)", line_width=1)

    # Fill: Über 50 grün, unter 50 rot (via zwei Traces)
    above = [max(v, 50) for v in detrended]
    below = [min(v, 50) for v in detrended]
    fig.add_trace(go.Scatter(
        x=x_days, y=above, mode="lines", line=dict(width=0),
        fill="tonexty", fillcolor="rgba(0,212,170,0.12)",
        showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=x_days, y=[50] * 365, mode="lines", line=dict(width=0),
        showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=x_days, y=below, mode="lines", line=dict(width=0),
        fill="tonexty", fillcolor="rgba(255,71,87,0.12)",
        showlegend=False, hoverinfo="skip",
    ))

    # Heute: "We are here!" Annotation
    today_doy = datetime.now().timetuple().tm_yday
    if 1 <= today_doy <= 365:
        today_val = detrended[today_doy - 1] if today_doy <= len(detrended) else 50
        fig.add_annotation(**_we_are_here_annotation(today_doy, today_val, above=True))

    fig = apply_se_theme(
        fig,
        title=f"{ticker} — Detrend-Indikator ({n_years} Jahre)",
        height=300, show_legend=False,
    )
    fig.update_xaxes(
        tickmode="array", tickvals=MONTH_STARTS, ticktext=MONTH_LABELS,
        range=[1, 365],
    )
    fig.update_yaxes(range=[0, 100], dtick=25)
    return fig


def build_combined_seasonal_detrend(
    year_data, avg, std, df, ticker, smoothing,
    show_individual, show_bands, show_current, show_pressure, cycle_overlay,
):
    """
    Kombinierter Chart: Saisonalchart (oben) + Detrend-Indikator (unten).
    Geteilte X-Achse → Hover-Crosshair synchronisiert sich automatisch.
    """
    from plotly.subplots import make_subplots

    if len(avg) < 10:
        return None, None

    x_days = list(range(1, 366))
    current_year = datetime.now().year

    # Detrend berechnen (0–100, Midline 50)
    end_val = avg[-1] - avg[0]
    daily_drift = end_val / len(avg)
    raw_detrend = [(avg[i] - avg[0]) - ((i + 1) * daily_drift) for i in range(len(avg))]
    r_min, r_max = min(raw_detrend), max(raw_detrend)
    r_range = r_max - r_min
    if r_range == 0:
        detrended = [50.0] * len(raw_detrend)
    else:
        detrended = [((v - r_min) / r_range) * 100 for v in raw_detrend]

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        row_heights=[0.65, 0.35],
        subplot_titles=[
            f"{ticker} — Saisonaler Jahresverlauf ({len(year_data)} Jahre)",
            f"{ticker} — Detrend-Indikator",
        ],
    )

    # ── Row 1: Saisonalchart ──────────────────────────

    # Einzeljahre
    if show_individual:
        for year, yd in year_data.items():
            fig.add_trace(go.Scatter(
                x=x_days, y=yd["full_365"], mode="lines",
                line=dict(color="rgba(200,220,255,0.12)", width=0.7),
                showlegend=False, hoverinfo="skip",
            ), row=1, col=1)

    # Konfidenzband
    if show_bands and std:
        upper = [avg[i] + std[i] for i in range(365)]
        lower = [avg[i] - std[i] for i in range(365)]
        fig.add_trace(go.Scatter(
            x=x_days, y=upper, mode="lines", line=dict(width=0),
            showlegend=False, hoverinfo="skip",
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=x_days, y=lower, mode="lines", line=dict(width=0),
            fill="tonexty", fillcolor="rgba(77,159,255,0.08)",
            name="+-1 Sigma", hoverinfo="skip",
        ), row=1, col=1)

    # Saisonaler Durchschnitt
    avg_smooth = avg.copy()
    if smoothing > 1:
        avg_smooth = pd.Series(avg_smooth).rolling(
            smoothing, center=True, min_periods=1
        ).mean().tolist()
    fig.add_trace(go.Scatter(
        x=x_days, y=avg_smooth, mode="lines",
        line=dict(color=SE_COLORS["accent_blue"], width=3),
        name=f"Saisonaler Ø ({len(year_data)} Jahre)",
        hovertemplate="Tag %{x}<br>Wert: %{y:.2f}<extra></extra>",
    ), row=1, col=1)

    # Praesidentenzyklus
    if cycle_overlay:
        for cycle_name in cycle_overlay:
            cycle_years = [y for y in year_data.keys()
                           if get_presidential_cycle_year(y) == cycle_name]
            if len(cycle_years) < 2:
                continue
            cycle_curves = [year_data[y]["full_365"] for y in cycle_years]
            cycle_avg = [np.mean([c[d] for c in cycle_curves]) for d in range(365)]
            if smoothing > 1:
                cycle_avg = pd.Series(cycle_avg).rolling(
                    smoothing, center=True, min_periods=1
                ).mean().tolist()
            short_label = cycle_name.split("(")[1].rstrip(")") if "(" in cycle_name else cycle_name
            fig.add_trace(go.Scatter(
                x=x_days, y=cycle_avg, mode="lines",
                line=dict(color=CYCLE_COLORS[cycle_name], width=2, dash="dash"),
                name=f"{short_label} ({len(cycle_years)}y)",
            ), row=1, col=1)

    # Aktuelles Jahr
    if show_current and current_year in year_data:
        yd = year_data[current_year]
        today_doy = datetime.now().timetuple().tm_yday
        display_days = [d for d in yd["days"] if d <= today_doy]
        display_vals = yd["cumulative"][:len(display_days)]
        if display_days:
            fig.add_trace(go.Scatter(
                x=display_days, y=display_vals, mode="lines",
                line=dict(color="#F1C40F", width=2.5),
                name=f"{current_year} (aktuell)",
            ), row=1, col=1)

    fig.add_hline(y=100, line_dash="dash", line_color="rgba(255,255,255,0.2)",
                  line_width=1, row=1, col=1)

    # ── Row 2: Detrend-Indikator ──────────────────────

    fig.add_trace(go.Scatter(
        x=x_days, y=detrended, mode="lines",
        line=dict(color="#FF6B6B", width=2.5),
        name="Detrend",
        hovertemplate="Tag %{x}<br>Wert: %{y:.1f}<extra></extra>",
    ), row=2, col=1)

    fig.add_hline(y=50, line_dash="dash", line_color="rgba(255,255,255,0.3)",
                  line_width=1, row=2, col=1)

    # "We are here!" auf beiden Subplots
    today_doy = datetime.now().timetuple().tm_yday
    if 1 <= today_doy <= 365:
        # Vertikale Linie ueber beide Subplots
        from shared.we_are_here import annotation as _wah_ann
        # Detrend Annotation
        today_detrend = detrended[today_doy - 1] if today_doy <= len(detrended) else 0
        fig.add_annotation(**_wah_ann(today_doy, today_detrend, above=True), row=2, col=1)

    # ── Layout ────────────────────────────────────────

    # Pressure als sekundaere Y-Achse (nur Row 1)
    pressure_info = None
    if show_pressure:
        p_curve, max_years, avail_periods = calculate_pressure_curve(df, smoothing_window=smoothing)
        if p_curve:
            fig.add_trace(go.Scatter(
                x=x_days, y=p_curve, mode="lines",
                line=dict(color=COLOR_PRESSURE, width=2),
                name="Pressure", yaxis="y3",
                hovertemplate="Pressure: %{y:+.2f}<extra></extra>",
            ), row=1, col=1)
            unavailable = [p for p in PRESSURE_PERIODS if p > max_years]
            if unavailable and avail_periods:
                pressure_info = (
                    f"Pressure Chart über die letzten **{max(avail_periods)} Jahre** "
                    f"(Datenreihe: {max_years} Jahre)."
                )

    fig = apply_se_theme(fig, title="", height=750)

    # Subplot-Titel Farbe
    for ann in fig.layout.annotations:
        ann.font.color = SE_COLORS["text_primary"]
        ann.font.size = 13

    # X-Achse nur auf unterem Subplot (shared)
    fig.update_xaxes(
        tickmode="array", tickvals=MONTH_STARTS, ticktext=MONTH_LABELS,
        range=[1, 365], row=2, col=1,
    )
    fig.update_xaxes(range=[1, 365], row=1, col=1)
    fig.update_yaxes(title="Normalisiert (Start = 100)", row=1, col=1)
    fig.update_yaxes(title="Detrend", range=[0, 100], dtick=25, row=2, col=1)

    # Crosshair: Spike-Linie synchronisiert ueber beide Subplots
    fig.update_layout(
        hovermode="closest",
        hoverlabel=dict(bgcolor=SE_COLORS["surface_alt"], font=dict(size=11)),
    )
    # Spike-Lines auf BEIDEN X-Achsen (across = durchgaengig ueber Subplots)
    for xaxis_name in ["xaxis", "xaxis2"]:
        fig.update_layout(**{
            xaxis_name: dict(
                showspikes=True,
                spikemode="across",
                spikethickness=1,
                spikecolor="rgba(255,215,0,0.5)",
                spikedash="dot",
                spikesnap="data",
            )
        })

    if show_pressure:
        fig.update_layout(
            yaxis3=dict(
                title=dict(text="Pressure", font=dict(color=COLOR_PRESSURE, size=11)),
                tickfont=dict(color=COLOR_PRESSURE, size=10),
                overlaying="y", side="right", showgrid=False,
                tickformat="+.1f", zeroline=True,
                zerolinecolor="rgba(224,86,160,0.2)",
                anchor="x",
            )
        )

    return fig, pressure_info


def build_monthly_bars(year_data, ticker):
    """Monats-Performance Balkendiagramm mit 'We are here!' Markierung."""
    current_month = datetime.now().month
    avgs, win_rates, ns = [], [], []
    for m in range(1, 13):
        s, e = MONTH_DOY[m]
        stats = calculate_period_stats(year_data, s, e)
        avgs.append(stats.get("avg_return", 0) if stats else 0)
        win_rates.append(stats.get("win_rate", 0) if stats else 0)
        ns.append(stats.get("total_years", 0) if stats else 0)

    colors = ["#4CAF50" if v >= 0 else "#F44336" for v in avgs]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=MONTH_NAMES_DE, y=avgs,
        marker=dict(color=colors),
        text=[f"{v:+.2f}%<br>WR {wr:.0f}%" for v, wr in zip(avgs, win_rates)],
        textposition="outside", textfont=dict(size=11, color="#c8d6e5"),
        hovertemplate="<b>%{x}</b><br>Ø: %{y:+.2f}%<br>n=%{customdata}<extra></extra>",
        customdata=ns,
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")

    bar_val = avgs[current_month - 1]
    fig.add_annotation(**_we_are_here_annotation(
        MONTH_NAMES_DE[current_month - 1], bar_val, above=(bar_val >= 0),
    ))

    fig = apply_se_theme(fig, title=f"{ticker} — Monats-Performance", height=420, show_legend=False)
    fig.update_layout(hovermode="x unified")
    return fig


def build_quarterly_bars(year_data, ticker):
    """Quartals-Performance Balkendiagramm mit 'We are here!' Markierung."""
    current_q = (datetime.now().month - 1) // 3 + 1
    q_labels = list(QUARTER_DOY.keys())
    avgs, win_rates, ns = [], [], []
    for q_name in q_labels:
        s, e = QUARTER_DOY[q_name]
        stats = calculate_period_stats(year_data, s, e)
        avgs.append(stats.get("avg_return", 0) if stats else 0)
        win_rates.append(stats.get("win_rate", 0) if stats else 0)
        ns.append(stats.get("total_years", 0) if stats else 0)

    colors = ["#4CAF50" if v >= 0 else "#F44336" for v in avgs]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=q_labels, y=avgs, marker=dict(color=colors),
        text=[f"{v:+.2f}%<br>WR {wr:.0f}% · n={n}" for v, wr, n in zip(avgs, win_rates, ns)],
        textposition="outside", textfont=dict(size=12, color="#c8d6e5"),
        hovertemplate="<b>%{x}</b><br>Ø: %{y:+.2f}%<extra></extra>",
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")

    bar_val = avgs[current_q - 1]
    fig.add_annotation(**_we_are_here_annotation(
        q_labels[current_q - 1], bar_val, above=(bar_val >= 0),
    ))

    fig = apply_se_theme(fig, title=f"{ticker} — Quartals-Performance", height=360, show_legend=False)
    fig.update_layout(hovermode="x unified")
    return fig


def build_monthly_heatmap(year_data, ticker):
    """10-Jahres Monats-Renditen Heatmap mit hellen Farben."""
    current_month = datetime.now().month
    current_year = datetime.now().year

    # Nur die letzten 10 Jahre
    all_years = sorted(year_data.keys(), reverse=True)
    years = all_years[:10]

    z_data = []
    y_labels = []
    for year in years:
        row = []
        for m in range(1, 13):
            s, e = MONTH_DOY[m]
            yd = year_data[year]
            start_val = yd["full_365"][s - 1]
            end_val = yd["full_365"][min(e - 1, 364)]
            ret = (end_val - start_val) / start_val * 100 if start_val != 0 else 0
            row.append(round(ret, 2))
        z_data.append(row)
        y_labels.append(str(year))

    from shared.constants import SE_HEATMAP_COLORSCALE, SE_HEATMAP_TEXT_COLOR
    colorscale = SE_HEATMAP_COLORSCALE

    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=MONTH_NAMES_DE,
        y=y_labels,
        colorscale=colorscale,
        zmid=0,
        text=[[f"{v:+.1f}%" for v in row] for row in z_data],
        texttemplate="%{text}",
        textfont=dict(size=11, color=SE_HEATMAP_TEXT_COLOR),
        hovertemplate="<b>%{y} — %{x}</b><br>Rendite: %{z:+.2f}%<extra></extra>",
        colorbar=dict(
            title=dict(text="Rendite %", font=dict(color=SE_COLORS["text_muted"], size=11)),
            tickfont=dict(color=SE_COLORS["text_muted"], size=10),
            ticksuffix="%",
        ),
    ))

    # "We are here!"
    if current_year in [int(y) for y in y_labels]:
        y_idx = y_labels.index(str(current_year))
        z_val = z_data[y_idx][current_month - 1]
        fig.add_annotation(**_we_are_here_annotation(
            MONTH_NAMES_DE[current_month - 1], str(current_year), above=True,
        ))

    fig = apply_se_theme(
        fig,
        title=f"{ticker} — 10 Jahres Heatmap",
        height=max(300, len(years) * 28 + 100),
        show_legend=False,
    )
    fig.update_yaxes(autorange="reversed", dtick=1)
    return fig


def styled_month_table(year_data):
    """Monatsstatistiken-Tabelle mit Farbcodierung."""
    rows = []
    for m in range(1, 13):
        s, e = MONTH_DOY[m]
        stats = calculate_period_stats(year_data, s, e)
        if stats:
            rows.append({
                "Monat": MONTH_NAMES_DE[m - 1],
                "Ø Rendite": f'{stats["avg_return"]:+.2f}%',
                "Median": f'{stats["median_return"]:+.2f}%',
                "Win-Rate": f'{stats["win_rate"]:.0f}%',
                "Max Gewinn": f'{stats["max_gain"]:+.1f}%',
                "Max Verlust": f'{stats["max_loss"]:+.1f}%',
                "n": stats["total_years"],
            })
    if not rows:
        return None

    mdf = pd.DataFrame(rows)
    mdf.index = range(1, len(mdf) + 1)

    def _color_val(val):
        if not isinstance(val, str) or "%" not in val:
            return ""
        try:
            num = float(val.replace("%", "").replace("+", "").strip())
        except ValueError:
            return ""
        if num > 0:
            return f"color: {SE_COLORS['positive']}"
        elif num < 0:
            return f"color: {SE_COLORS['negative']}"
        return ""

    return (
        mdf.style
        .applymap(_color_val)
        .set_properties(**{"text-align": "center"})
        .set_table_styles([
            {"selector": "th", "props": [
                ("text-align", "center"),
                ("background-color", SE_COLORS["surface"]),
                ("color", SE_COLORS["text_primary"]),
                ("border-bottom", f"1px solid {SE_COLORS['panel_border']}"),
            ]},
            {"selector": "td", "props": [
                ("border-bottom", f"1px solid {SE_COLORS['panel_border']}"),
            ]},
        ])
    )


def styled_quarter_table(year_data):
    """Quartalsstatistiken-Tabelle mit Farbcodierung (analog zu Monats-Detailtabelle)."""
    rows = []
    for q_name, (s, e) in QUARTER_DOY.items():
        stats = calculate_period_stats(year_data, s, e)
        if stats:
            rows.append({
                "Quartal": q_name,
                "Ø Rendite": f'{stats["avg_return"]:+.2f}%',
                "Median": f'{stats["median_return"]:+.2f}%',
                "Win-Rate": f'{stats["win_rate"]:.0f}%',
                "Max Gewinn": f'{stats["max_gain"]:+.1f}%',
                "Max Verlust": f'{stats["max_loss"]:+.1f}%',
                "n": stats["total_years"],
            })
    if not rows:
        return None

    qdf = pd.DataFrame(rows)
    qdf.index = range(1, len(qdf) + 1)

    def _color_val(val):
        if not isinstance(val, str) or "%" not in val:
            return ""
        try:
            num = float(val.replace("%", "").replace("+", "").strip())
        except ValueError:
            return ""
        if num > 0:
            return f"color: {SE_COLORS['positive']}"
        elif num < 0:
            return f"color: {SE_COLORS['negative']}"
        return ""

    return (
        qdf.style
        .applymap(_color_val)
        .set_properties(**{"text-align": "center"})
        .set_table_styles([
            {"selector": "th", "props": [
                ("text-align", "center"),
                ("background-color", SE_COLORS["surface"]),
                ("color", SE_COLORS["text_primary"]),
                ("border-bottom", f"1px solid {SE_COLORS['panel_border']}"),
            ]},
            {"selector": "td", "props": [
                ("border-bottom", f"1px solid {SE_COLORS['panel_border']}"),
            ]},
        ])
    )


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main():
    # ── Sidebar ──────────────────────────────────────────
    with st.sidebar:
        st.markdown("## 📈 Jahreszyklus")
        st.markdown("---")

        ticker = ticker_select(key="ys_ticker", default=DEFAULT_TICKER)

        period_options = [3, 5, 7, 10, 15, 20, 25, 30, "Max"]
        years_back_raw = st.select_slider(
            "Analyse-Zeitraum (Jahre)",
            options=period_options, value="Max",
            format_func=lambda x: str(x), key="ys_period",
        )
        years_back_is_max = (years_back_raw == "Max")

        st.markdown("---")
        st.markdown("### Saisonalchart")
        smoothing = st.slider("Glaettung (Tage)", 1, 21, 1, 2, key="ys_smooth")
        show_individual = st.checkbox("Einzelne Jahre zeigen", value=False, key="ys_indiv")
        show_bands = st.checkbox("Konfidenzband (±1 Sigma)", value=False, key="ys_bands")
        show_percentile_bands = st.checkbox("Perzentil-Baender (25./75.)", value=True, key="ys_pctile",
                                             help="Zeigt den Bereich, in dem die mittleren 50% aller Jahre liegen")
        show_current = st.checkbox("Aktuelles Jahr hervorheben", value=True, key="ys_current")

        st.markdown("---")
        st.markdown("### Präsidentenzyklus")
        cycle_overlay = st.multiselect(
            "Zyklusjahre als Overlay",
            options=list(CYCLE_COLORS.keys()),
            default=None, key="ys_cycle",
            help="Zeigt den Ø-Verlauf der gewählten Zyklusjahre als zusätzliche Linien im Chart",
        )

        st.markdown("---")
        st.markdown("### Pressure Chart")
        show_pressure = st.checkbox("Pressure im Hauptchart", value=False, key="ys_pressure",
                                    help="Addiert Ø-Tagesrenditen verschiedener Lookback-Perioden (sekundäre Y-Achse)")

        st.markdown("---")
        st.markdown("### Risiko-Analyse")
        vola_window = st.slider("Rolling-Vola Fenster (Tage)", 10, 60, 20, 5, key="ys_vola_win")
        show_dd_individual = st.checkbox("Einzeljahre im Drawdown-Chart", value=False, key="ys_dd_indiv")

        st.markdown("---")
        from shared.outlier_manager import outlier_sidebar
        outlier_method = outlier_sidebar()

    # ── Daten laden ──────────────────────────────────────
    with st.spinner(f"Lade {ticker}..."):
        raw_df = download_data(ticker)

    if raw_df is None or raw_df.empty:
        st.error(f"Keine Daten für '{ticker}'.")
        return

    df = preprocess(raw_df)
    all_years = sorted(df["year"].unique())
    current_year = datetime.now().year

    if years_back_is_max:
        selected_years = all_years
    else:
        cutoff = current_year - int(years_back_raw)
        selected_years = [y for y in all_years if y >= cutoff]

    if current_year in all_years and current_year not in selected_years:
        selected_years.append(current_year)
        selected_years.sort()

    if len(selected_years) < 2:
        st.warning("Nicht genügend Daten.")
        return

    year_data = build_year_data(df, selected_years)

    # Outlier Filter
    from shared.outlier_manager import filter_year_data, outlier_info_box
    year_data, outlier_years = filter_year_data(year_data, method=outlier_method)
    outlier_info_box(outlier_years, outlier_method)

    avg, std = calculate_seasonal_average(year_data)

    st.caption(
        f"**{ticker}** | {min(selected_years)}–{max(selected_years)} | "
        f"{len(year_data)} Jahre | Glaettung: {smoothing}d"
    )
    from shared.trading_day_header import render_trading_day_header
    render_trading_day_header(df)

    # ── 1. Saisonalchart ──────────────────────────────────
    fig, pressure_info = build_yearly_chart(
        year_data, avg, std, df, ticker, smoothing,
        show_individual, show_bands, show_current,
        show_pressure, cycle_overlay,
        show_percentile_bands=show_percentile_bands,
    )
    st.plotly_chart(fig, use_container_width=True, config=_PLOTLY_CFG)

    # ── Perzentil-Statusbar ──────────────────────────────
    if show_current and avg:
        from shared.percentile_bar import render_percentile_bar
        _cur_year = datetime.now().year
        _today_doy = datetime.now().timetuple().tm_yday
        _day_idx = min(_today_doy - 1, 364)  # 0-basiert, max 364

        if _cur_year in year_data:
            _cur_val = year_data[_cur_year]["full_365"][_day_idx] - 100  # Normiert auf 0%
            _hist_vals = [yd["full_365"][_day_idx] - 100
                          for y, yd in year_data.items() if y != _cur_year]
            if len(_hist_vals) >= 5:
                render_percentile_bar(
                    current_value=_cur_val,
                    hist_values=_hist_vals,
                    label=f"HT {_today_doy}/252 · {ticker} {_cur_year}",
                )

    if pressure_info:
        st.info(pressure_info)

    # ── 2. Detrend-Indikator (Expander) ──────────────────
    if avg:
        with st.expander("Detrend-Indikator / Saisonaler Druck", expanded=True):
            detrend_fig = build_detrend_chart(avg, ticker, len(year_data))
            if detrend_fig:
                st.plotly_chart(detrend_fig, use_container_width=True, config=_PLOTLY_CFG)
                st.caption(
                    "_Saisonaler Durchschnitt ohne Trendkomponente. "
                    "Über 50 = saisonal typisch starke Phase. Unter 50 = saisonal typisch schwache Phase._"
                )

    # ── 3. Anomalie-Radar (immer sichtbar) ──────────────
    st.markdown("---")
    st.markdown("##### Anomalie-Radar (KI)")
    try:
        from shared.anomaly_engine import compute_ticker_anomaly_score
        with st.spinner("Anomalie-Radar..."):
            radar = compute_ticker_anomaly_score(df, lookback_days=10)
        if "error" not in radar:
            r_score = radar["anomaly_score"]
            if r_score >= 70:
                r_icon, r_label = "🔴", "Stark anomal"
            elif r_score >= 40:
                r_icon, r_label = "🟡", "Leicht anomal"
            else:
                r_icon, r_label = "🟢", "Normal"

            st.markdown(
                f'<div style="display:flex;gap:1rem;flex-wrap:wrap;">'
                f'<div style="background:{SE_COLORS["surface"]};border:1px solid {SE_COLORS["panel_border"]};'
                f'border-radius:10px;padding:0.5rem 0.8rem;flex:1;min-width:120px;">'
                f'<div style="color:{SE_COLORS["accent_warm"]};font-size:0.65rem;text-transform:uppercase;letter-spacing:0.5px;">Score</div>'
                f'<div style="color:{SE_COLORS["text_primary"]};font-size:1.1rem;font-weight:700;">{r_score:.0f}/100</div></div>'
                f'<div style="background:{SE_COLORS["surface"]};border:1px solid {SE_COLORS["panel_border"]};'
                f'border-radius:10px;padding:0.5rem 0.8rem;flex:1;min-width:120px;">'
                f'<div style="color:{SE_COLORS["accent_warm"]};font-size:0.65rem;text-transform:uppercase;letter-spacing:0.5px;">Status</div>'
                f'<div style="color:{SE_COLORS["text_primary"]};font-size:1.1rem;font-weight:700;">{r_icon} {r_label}</div></div>'
                f'<div style="background:{SE_COLORS["surface"]};border:1px solid {SE_COLORS["panel_border"]};'
                f'border-radius:10px;padding:0.5rem 0.8rem;flex:1;min-width:160px;">'
                f'<div style="color:{SE_COLORS["accent_warm"]};font-size:0.65rem;text-transform:uppercase;letter-spacing:0.5px;">10d-Rendite</div>'
                f'<div style="color:{SE_COLORS["text_primary"]};font-size:0.95rem;font-weight:700;">'
                f'{radar["current_return"]:+.2f}%'
                f'<span style="color:{SE_COLORS["text_muted"]};font-size:0.75rem;font-weight:400;"> (Ø {radar["historical_avg"]:+.2f}%)</span>'
                f'</div></div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.info(radar["error"])
    except ImportError:
        st.caption("scikit-learn nicht installiert — Anomalie-Radar deaktiviert.")
    except Exception as _e:
        st.caption(f"Anomalie-Radar nicht verfügbar: {_e}")

    # ── 3b. Saisonale Muster-Brüche (KI) ──────────────────
    with st.expander("Saisonale Muster-Brüche (KI)", expanded=False):
        st.caption("Jahre in denen das saisonale Muster am stärksten gebrochen wurde — erkannt via Isolation Forest.")
        try:
            from shared.anomaly_engine import detect_pattern_breaks
            with st.spinner("Muster-Brüche analysieren..."):
                _breaks = detect_pattern_breaks(year_data, avg, top_n=5)
            if _breaks:
                _cards_html = '<div style="display:flex;flex-direction:column;gap:0.6rem;">'
                for _b in _breaks:
                    _b_icon = "⚠️" if _b["is_outlier"] else "📊"
                    _b_event = f'<span style="color:{SE_COLORS["accent_warm"]};font-weight:600;"> — {_b["event"]}</span>' if _b.get("event") else ""
                    _b_strength = _b["break_strength"]
                    if _b_strength >= 70:
                        _b_color = SE_COLORS["negative"]
                    elif _b_strength >= 40:
                        _b_color = SE_COLORS["accent_warm"]
                    else:
                        _b_color = SE_COLORS["positive"]
                    _cards_html += (
                        f'<div style="background:{SE_COLORS["surface"]};border:1px solid {SE_COLORS["panel_border"]};'
                        f'border-radius:10px;padding:0.6rem 1rem;display:flex;align-items:center;gap:1rem;flex-wrap:wrap;">'
                        f'<span style="font-size:1.2rem;">{_b_icon}</span>'
                        f'<span style="color:{SE_COLORS["text_primary"]};font-weight:700;font-size:1.05rem;min-width:3rem;">{_b["year"]}</span>'
                        f'<span style="color:{_b_color};font-weight:700;font-size:0.85rem;min-width:5rem;">Stärke: {_b_strength:.0f}/100</span>'
                        f'<span style="color:{SE_COLORS["text_muted"]};font-size:0.8rem;">'
                        f'Korr: {_b["correlation"]:.2f} · Rendite: {_b["year_return"]:+.1f}% · Max DD: {_b["max_drawdown"]:.1f}%'
                        f'</span>{_b_event}</div>'
                    )
                _cards_html += '</div>'
                st.markdown(_cards_html, unsafe_allow_html=True)
            else:
                st.caption("Keine Muster-Brüche erkannt (zu wenig Daten).")
        except ImportError:
            st.caption("scikit-learn nicht installiert — Muster-Brüche deaktiviert.")
        except Exception as _e:
            st.caption(f"Muster-Bruch-Erkennung nicht verfügbar: {_e}")

    # ── 4. Monats-Performance (Balken) ────────────────────
    st.markdown("---")
    with st.expander("Monats-Performance", expanded=True):
        st.plotly_chart(build_monthly_bars(year_data, ticker), use_container_width=True, config=_PLOTLY_CFG)
        _n_filtered = len(year_data)
        with st.expander(f"Monats-Detailtabelle ({_n_filtered} Jahre)"):
            styled = styled_month_table(year_data)
            if styled is not None:
                st.markdown(styled.to_html(), unsafe_allow_html=True)

    # ── 4b. Monats-Signifikanz (Tachos) ──────────────────
    from shared.significance_gauge import run_significance_test, render_significance_section
    _month_sig_groups = {}
    for m in range(1, 13):
        s, e = MONTH_DOY[m]
        _m_returns = []
        for _y, _yd in year_data.items():
            sv = _yd["full_365"][s - 1]
            ev = _yd["full_365"][min(e - 1, 364)]
            _m_returns.append((ev - sv) / sv * 100 if sv != 0 else 0)
        if _m_returns:
            _month_sig_groups[MONTH_NAMES_DE[m - 1]] = _m_returns

    if _month_sig_groups:
        _month_sig_results = run_significance_test(_month_sig_groups)
        render_significance_section(
            _month_sig_results,
            expander_title="📊 Statistische Signifikanz der Monats-Effekte",
            cols_per_row=4,
            sort_order=MONTH_NAMES_DE,
            key_prefix="month_sig",
            expanded=True,
        )

    # ── 4c. Signal-Robustheit (Seasonal Confidence) ────────
    with st.expander("Signal-Robustheit pro Monat (KI)", expanded=False):
        st.caption("Wie robust ist das saisonale Muster in jedem Monat? Isolation Forest bewertet die Cluster-Reinheit der historischen Rendite-Verläufe.")
        try:
            from shared.anomaly_engine import compute_seasonal_confidence
            with st.spinner("Signal-Robustheit berechnen..."):
                _conf = compute_seasonal_confidence(year_data, avg)
            if _conf and len(_conf) == 12:
                _conf_html = '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.5rem;">'
                for _c in _conf:
                    _cv = _c["confidence"]
                    if _cv >= 75:
                        _c_color = SE_COLORS["positive"]
                        _c_label = "Robust"
                    elif _cv >= 50:
                        _c_color = SE_COLORS["accent_warm"]
                        _c_label = "Mittel"
                    else:
                        _c_color = SE_COLORS["negative"]
                        _c_label = "Schwach"
                    _conf_html += (
                        f'<div style="background:{SE_COLORS["surface"]};border:1px solid {SE_COLORS["panel_border"]};'
                        f'border-radius:10px;padding:0.5rem 0.7rem;text-align:center;">'
                        f'<div style="color:{SE_COLORS["text_muted"]};font-size:0.65rem;text-transform:uppercase;letter-spacing:0.5px;">{_c["month_name"]}</div>'
                        f'<div style="color:{_c_color};font-size:1.1rem;font-weight:700;">{_cv:.0f}</div>'
                        f'<div style="color:{SE_COLORS["text_muted"]};font-size:0.6rem;">{_c_label}</div>'
                        f'<div style="color:{SE_COLORS["text_dim"]};font-size:0.55rem;margin-top:2px;">Ø {_c["avg_return"]:+.2f}% · {_c["n_years"]}J</div>'
                        f'</div>'
                    )
                _conf_html += '</div>'
                st.markdown(_conf_html, unsafe_allow_html=True)
                st.caption("Score 0–100: Hoher Wert = robustes, konsistentes Muster über viele Jahre. Niedriger Wert = von Einzelereignissen getrieben.")
            else:
                st.caption("Zu wenig Daten für Confidence-Berechnung.")
        except ImportError:
            st.caption("scikit-learn nicht installiert — Signal-Robustheit deaktiviert.")
        except Exception as _e:
            st.caption(f"Signal-Robustheit nicht verfügbar: {_e}")

    # ── 5. Quartals-Performance ───────────────────────────
    with st.expander("Quartals-Performance", expanded=False):
        st.plotly_chart(build_quarterly_bars(year_data, ticker), use_container_width=True, config=_PLOTLY_CFG)
        with st.expander(f"Quartals-Detailtabelle ({len(year_data)} Jahre)"):
            styled_q = styled_quarter_table(year_data)
            if styled_q is not None:
                st.markdown(styled_q.to_html(), unsafe_allow_html=True)

    # ── 5b. Quartals-Signifikanz ──────────────────────────
    _q_sig_groups = {}
    _q_labels = list(QUARTER_DOY.keys())
    for q_name in _q_labels:
        s, e = QUARTER_DOY[q_name]
        _q_returns = []
        for _y, _yd in year_data.items():
            sv = _yd["full_365"][s - 1]
            ev = _yd["full_365"][min(e - 1, 364)]
            _q_returns.append((ev - sv) / sv * 100 if sv != 0 else 0)
        if _q_returns:
            _q_sig_groups[q_name] = _q_returns

    if _q_sig_groups:
        _q_sig_results = run_significance_test(_q_sig_groups)
        render_significance_section(
            _q_sig_results,
            expander_title="📊 Statistische Signifikanz der Quartals-Effekte",
            cols_per_row=4,
            sort_order=_q_labels,
            key_prefix="quarter_sig",
            expanded=False,
        )

    # ── 5c. Praesidentenzyklus-Signifikanz ────────────────
    _cycle_names = list(CYCLE_COLORS.keys())
    _cycle_short = {
        "Year 1 (Post-Election)": "Post-Election",
        "Year 2 (Midterm Election)": "Midterm",
        "Year 3 (Pre-Election)": "Pre-Election",
        "Year 4 (Election Year)": "Election Year",
    }
    _cycle_sig_groups = {}
    for cn in _cycle_names:
        _cy = [y for y in year_data.keys()
               if get_presidential_cycle_year(y) == cn]
        if len(_cy) >= 3:
            _c_returns = []
            for y in _cy:
                sv = year_data[y]["full_365"][0]
                ev = year_data[y]["full_365"][364]
                _c_returns.append((ev - sv) / sv * 100 if sv != 0 else 0)
            _cycle_sig_groups[_cycle_short.get(cn, cn)] = _c_returns

    if _cycle_sig_groups:
        _cycle_sig_results = run_significance_test(_cycle_sig_groups)
        render_significance_section(
            _cycle_sig_results,
            expander_title="🏛️ Statistische Signifikanz der Präsidentenzyklus-Jahre",
            cols_per_row=4,
            sort_order=list(_cycle_short.values()),
            key_prefix="cycle_sig",
            expanded=False,
        )

    # ── 5d. Praesidentenzyklus — Best Match ──────────────
    _cur_year = datetime.now().year
    if _cur_year in year_data:
        _today_doy = datetime.now().timetuple().tm_yday
        _cur_curve = year_data[_cur_year]["full_365"][:_today_doy]

        if len(_cur_curve) >= 20:
            with st.expander("🏛️ Präsidentenzyklus — Best Match", expanded=True):
                # Ø-Kurven pro Zyklus + Alle Jahre berechnen
                _match_data = {}
                for cn in _cycle_names:
                    _cy = [y for y in year_data.keys()
                           if get_presidential_cycle_year(y) == cn and y != _cur_year]
                    if len(_cy) >= 2:
                        _curves = [year_data[y]["full_365"][:_today_doy] for y in _cy]
                        _avg_c = [float(np.mean([c[i] for c in _curves])) for i in range(_today_doy)]
                        _match_data[_cycle_short.get(cn, cn)] = {
                            "curve": _avg_c, "n": len(_cy), "color": CYCLE_COLORS[cn],
                        }

                # "Alle Jahre" als Referenz
                _all_other = [y for y in year_data.keys() if y != _cur_year]
                if len(_all_other) >= 5:
                    _all_curves = [year_data[y]["full_365"][:_today_doy] for y in _all_other]
                    _avg_all = [float(np.mean([c[i] for c in _all_curves])) for i in range(_today_doy)]
                    _match_data[f"Alle Jahre"] = {
                        "curve": _avg_all, "n": len(_all_other), "color": "#94a3b8",
                    }

                if _match_data:
                    # Korrelation + DTW berechnen
                    _match_results = []
                    _best_r = -999
                    _best_name = ""
                    for name, md in _match_data.items():
                        _r = float(np.corrcoef(_cur_curve, md["curve"])[0, 1])
                        if np.isnan(_r):
                            _r = 0.0
                        # DTW-Similarity (0-100%)
                        try:
                            from fastdtw import fastdtw
                            from scipy.spatial.distance import euclidean
                            _dist, _ = fastdtw(_cur_curve, md["curve"], dist=euclidean)
                            _max_dist = np.sqrt(len(_cur_curve)) * np.std(_cur_curve) * 2
                            _dtw_pct = max(0, min(100, (1 - _dist / _max_dist) * 100)) if _max_dist > 0 else 0
                        except ImportError:
                            _dtw_pct = max(0, min(100, (_r + 1) / 2 * 100))

                        _match_results.append({
                            "name": name, "r": _r, "dtw_pct": _dtw_pct,
                            "n": md["n"], "color": md["color"],
                        })
                        if _r > _best_r:
                            _best_r = _r
                            _best_name = name

                    # Header: Bester Match
                    _best = next((m for m in _match_results if m["name"] == _best_name), None)
                    if _best:
                        st.markdown(
                            f'<div style="text-align:center; margin-bottom:12px;">'
                            f'<span style="font-size:13px; color:#94a3b8;">Bester Match: </span>'
                            f'<span style="font-size:14px; font-weight:700; color:{_best["color"]};">'
                            f'{_best_name}</span>'
                            f'<span style="font-size:12px; color:#64748b;"> '
                            f'(r={_best["r"]:+.2f}, DTW {_best["dtw_pct"]:.0f}%, n={_best["n"]} Jahre)</span>'
                            f'</div>',
                            unsafe_allow_html=True)

                    # Gauges als kompakte Karten
                    _match_cols = st.columns(len(_match_results))
                    for i, mr in enumerate(_match_results):
                        with _match_cols[i]:
                            _is_best = (mr["name"] == _best_name)
                            _border = f"2px solid {mr['color']}" if _is_best else "1px solid rgba(255,255,255,0.07)"
                            _r_clr = "#34d399" if mr["r"] > 0.5 else ("#fbbf24" if mr["r"] > 0 else "#f87171")

                            # Radial Score (0-1 → Gauge)
                            _score = max(0, min(1, (mr["r"] + 1) / 2))
                            _pct = int(_score * 100)

                            st.markdown(
                                f'<div style="background:rgba(15,19,24,0.6);'
                                f'border:{_border}; border-radius:10px;'
                                f'padding:12px 8px; text-align:center;">'
                                f'<div style="font-size:10px; color:{mr["color"]}; font-weight:600;'
                                f'margin-bottom:6px;">{"🏆 " if _is_best else ""}{mr["name"]}</div>'
                                f'<div style="font-size:28px; font-weight:800; color:{_r_clr};'
                                f'letter-spacing:-1px; margin:4px 0;">{mr["r"]:.2f}</div>'
                                f'<div style="font-size:10px; color:#64748b; line-height:1.5;">'
                                f'<span style="color:{_r_clr};">r={mr["r"]:+.2f}</span>'
                                f' · DTW {mr["dtw_pct"]:.0f}%<br>n={mr["n"]}</div>'
                                f'</div>',
                                unsafe_allow_html=True)

    # ── 6. 10-Jahres Heatmap ─────────────────────────────
    with st.expander("10 Jahres Heatmap", expanded=True):
        st.plotly_chart(build_monthly_heatmap(year_data, ticker), use_container_width=True, config=_PLOTLY_CFG)

    # ══════════════════════════════════════════════════════
    # DRAWDOWN & RISIKO (nach allen Rendite-Sektionen)
    # ══════════════════════════════════════════════════════

    st.markdown(
        f'<div style="text-align:center; margin:2rem 0 1rem 0; padding-top:1rem; '
        f'border-top:2px solid rgba(255,68,68,0.2);">'
        f'<span style="color:#ff4444; font-size:1.3rem; font-weight:700;">'
        f'📉 Drawdown &amp; Risiko</span>'
        f'<p style="color:{SE_COLORS["text_muted"]}; font-size:0.9rem; margin-top:0.3rem;">'
        f'Wann im Jahr passieren die größten Rücksetzer? '
        f'Berechnung basiert auf den gleichen {len(year_data)} Jahren wie die Rendite-Analyse oben.</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    from shared.drawdown_analysis import (
        compute_avg_drawdown_curve, compute_drawdown_series,
        compute_drawdown_kpi, compute_drawdown_stats,
        compute_monthly_max_drawdown, compute_avg_rolling_volatility,
        compute_current_vola_stats, compute_rolling_volatility,
        SE_DRAWDOWN_COLORSCALE, MONTH_LABELS_SHORT,
    )
    from shared.charts import apply_se_heatmap_theme

    _yd_curves = [np.array(yd["full_365"]) for yd in year_data.values()]
    _yd_years = list(year_data.keys())
    _cur_year = datetime.now().year

    # ── Expander A: Ø Drawdown-Verlauf ──
    with st.expander("📉 Saisonaler Drawdown-Verlauf", expanded=True):
        avg_dd, std_dd = compute_avg_drawdown_curve(_yd_curves, base=0.0)

        if len(avg_dd) > 0:
            fig_dd = go.Figure()

            if show_dd_individual:
                for yr, yd in year_data.items():
                    dd_yr = compute_drawdown_series(np.array(yd["full_365"]), base=0.0)
                    fig_dd.add_trace(go.Scatter(
                        x=list(range(365)), y=dd_yr.tolist(),
                        name=str(yr), line=dict(color=SE_COLORS["individual"], width=0.5),
                        showlegend=False, hoverinfo="skip",
                    ))

            x_range = list(range(365))
            upper = (avg_dd + std_dd).tolist()
            lower = (avg_dd - std_dd).tolist()
            fig_dd.add_trace(go.Scatter(
                x=x_range + x_range[::-1], y=upper + lower[::-1],
                fill="toself", fillcolor="rgba(255,68,68,0.08)",
                line=dict(width=0), showlegend=False, hoverinfo="skip",
            ))

            fig_dd.add_trace(go.Scatter(
                x=x_range, y=avg_dd.tolist(),
                name="Ø Drawdown",
                fill="tozeroy", fillcolor="rgba(255,34,34,0.15)",
                line=dict(color="#ff4444", width=2.5),
                hovertemplate="Tag %{x}: %{y:.2f}%<extra></extra>",
            ))

            if show_current and _cur_year in year_data:
                _cur_curve = np.array(year_data[_cur_year]["full_365"])
                _cur_dd = compute_drawdown_series(_cur_curve, base=0.0)
                _today_doy = min(datetime.now().timetuple().tm_yday, 365)
                fig_dd.add_trace(go.Scatter(
                    x=list(range(_today_doy)), y=_cur_dd[:_today_doy].tolist(),
                    name=f"{_cur_year} (aktuell)",
                    line=dict(color=SE_COLORS["current_year"], width=2.5),
                    hovertemplate=f"{_cur_year} Tag %{{x}}: %{{y:.2f}}%<extra></extra>",
                ))

            fig_dd.update_xaxes(tickvals=MONTH_STARTS, ticktext=MONTH_LABELS)
            fig_dd.update_yaxes(ticksuffix="%")

            _cycle_info = ""
            if cycle_overlay:
                _cycle_info = f" ({cycle_overlay})"
            fig_dd = apply_se_theme(fig_dd, title=f"Ø Saisonaler Drawdown — {ticker}{_cycle_info}", height=450)
            st.plotly_chart(fig_dd, use_container_width=True, config=_PLOTLY_CFG)

            _kpi = compute_drawdown_kpi(_yd_curves, base=0.0)
            if _kpi:
                _card = (
                    'background:linear-gradient(135deg,#0f1923,#131d2a);'
                    'border:1px solid rgba(255,255,255,0.08);border-radius:10px;'
                    'padding:12px 16px;text-align:center;'
                )
                _lbl = 'color:#8899aa;font-size:10px;text-transform:uppercase;letter-spacing:1px;'
                _val = 'font-size:16px;font-weight:700;font-variant-numeric:tabular-nums;margin:2px 0;'

                _cur_dd_str = "–"
                _cur_dd_c = SE_COLORS["text_primary"]
                if show_current and _cur_year in year_data:
                    _cur_c = np.array(year_data[_cur_year]["full_365"])
                    _cur_dd_arr = compute_drawdown_series(_cur_c, base=0.0)
                    _today_idx = min(datetime.now().timetuple().tm_yday - 1, len(_cur_dd_arr) - 1)
                    _cur_dd_now = _cur_dd_arr[_today_idx]
                    _cur_dd_str = f"{_cur_dd_now:.1f}%"
                    _cur_dd_c = "#ff4444" if _cur_dd_now < -1 else "#34d399"

                k1, k2, k3 = st.columns(3)
                with k1:
                    st.markdown(f'<div style="{_card}"><div style="{_lbl}">Ø Max DD ({len(year_data)}J)</div>'
                                f'<div style="{_val}color:#ff4444;">{_kpi["avg_max_dd"]:.1f}%</div></div>',
                                unsafe_allow_html=True)
                with k2:
                    st.markdown(f'<div style="{_card}"><div style="{_lbl}">Worst DD</div>'
                                f'<div style="{_val}color:#ff2222;">{_kpi["worst_max_dd"]:.1f}%</div></div>',
                                unsafe_allow_html=True)
                with k3:
                    st.markdown(f'<div style="{_card}"><div style="{_lbl}">Aktueller DD {_cur_year}</div>'
                                f'<div style="{_val}color:{_cur_dd_c};">{_cur_dd_str}</div></div>',
                                unsafe_allow_html=True)

            if show_current and _cur_year in year_data:
                from shared.percentile_bar import render_percentile_bar
                _cur_stats = compute_drawdown_stats(np.array(year_data[_cur_year]["full_365"]), base=0.0)
                _hist_dds = [compute_drawdown_stats(c, base=0.0)["max_drawdown"] for c in _yd_curves
                             if not np.array_equal(c, np.array(year_data.get(_cur_year, {}).get("full_365", [])))]
                if len(_hist_dds) >= 5:
                    render_percentile_bar(
                        current_value=_cur_stats["max_drawdown"],
                        hist_values=_hist_dds,
                        label=f"Max DD {_cur_year} · {ticker}",
                    )

    # ── Expander B: Saisonale Volatilität (Rolling) ──
    with st.expander("📊 Saisonale Volatilität (Rolling)", expanded=False):
        vola_result = compute_avg_rolling_volatility(df, _yd_years, window=vola_window, n_points=365)

        if vola_result is not None:
            avg_v, std_v = vola_result
            fig_vol = go.Figure()

            x_range = list(range(365))
            fig_vol.add_trace(go.Scatter(
                x=x_range + x_range[::-1],
                y=(avg_v + std_v).tolist() + (avg_v - std_v).tolist()[::-1],
                fill="toself", fillcolor="rgba(0,212,170,0.08)",
                line=dict(width=0), showlegend=False, hoverinfo="skip",
            ))

            fig_vol.add_trace(go.Scatter(
                x=x_range, y=avg_v.tolist(),
                name=f"Ø {vola_window}d Vola",
                line=dict(color=SE_COLORS["accent"], width=2.5),
                hovertemplate="Tag %{x}: %{y:.1f}%<extra></extra>",
            ))

            if show_current and _cur_year in year_data:
                _cur_vola = compute_rolling_volatility(df, _cur_year, window=vola_window)
                if _cur_vola is not None:
                    _today_doy = min(datetime.now().timetuple().tm_yday, 365)
                    _n = len(_cur_vola)
                    _x_orig = np.linspace(0, 364, _n)
                    _interp = np.interp(np.arange(365), _x_orig, pd.Series(_cur_vola).ffill().bfill().values)
                    fig_vol.add_trace(go.Scatter(
                        x=list(range(min(_today_doy, 365))),
                        y=_interp[:_today_doy].tolist(),
                        name=f"{_cur_year} (aktuell)",
                        line=dict(color=SE_COLORS["current_year"], width=2.5),
                    ))

            fig_vol.update_xaxes(tickvals=MONTH_STARTS, ticktext=MONTH_LABELS)
            fig_vol.update_yaxes(ticksuffix="%")
            fig_vol = apply_se_theme(fig_vol, title=f"Ø Rolling {vola_window}d Volatilität — {ticker}", height=420)
            st.plotly_chart(fig_vol, use_container_width=True, config=_PLOTLY_CFG)

            # Vola KPI-Karten
            _vola_stats = compute_current_vola_stats(df, window=vola_window, years=_yd_years)
            if _vola_stats:
                _card = (
                    'background:linear-gradient(135deg,#0f1923,#131d2a);'
                    'border:1px solid rgba(255,255,255,0.08);border-radius:10px;'
                    'padding:12px 16px;text-align:center;'
                )
                _lbl = 'color:#8899aa;font-size:10px;text-transform:uppercase;letter-spacing:1px;'
                _val = 'font-size:16px;font-weight:700;font-variant-numeric:tabular-nums;margin:2px 0;'

                if _vola_stats["is_elevated"]:
                    _v_clr, _v_status = "#ff4444", "Erhöht"
                elif _vola_stats["is_low"]:
                    _v_clr, _v_status = "#34d399", "Niedrig"
                else:
                    _v_clr, _v_status = SE_COLORS["accent_warm"], "Normal"
                _delta_clr = "#ff4444" if _vola_stats["delta"] > 0 else "#34d399"
                _delta_sign = "+" if _vola_stats["delta"] > 0 else ""

                vc1, vc2, vc3, vc4 = st.columns(4)
                with vc1:
                    st.markdown(f'<div style="{_card}"><div style="{_lbl}">Aktuelle {vola_window}d Vola</div>'
                                f'<div style="{_val}color:{_v_clr};">{_vola_stats["current_vola"]:.1f}%</div></div>',
                                unsafe_allow_html=True)
                with vc2:
                    st.markdown(f'<div style="{_card}"><div style="{_lbl}">Historischer Ø</div>'
                                f'<div style="{_val}color:{SE_COLORS["text_primary"]};">{_vola_stats["avg_vola"]:.1f}%</div></div>',
                                unsafe_allow_html=True)
                with vc3:
                    st.markdown(f'<div style="{_card}"><div style="{_lbl}">Delta zum Ø</div>'
                                f'<div style="{_val}color:{_delta_clr};">{_delta_sign}{_vola_stats["delta"]:.1f}%</div></div>',
                                unsafe_allow_html=True)
                with vc4:
                    st.markdown(f'<div style="{_card}"><div style="{_lbl}">Perzentil ({_vola_stats["n_years"]}J)</div>'
                                f'<div style="{_val}color:{_v_clr};">{_vola_stats["percentile"]:.0f}% · {_v_status}</div></div>',
                                unsafe_allow_html=True)
        else:
            st.info("Nicht genügend Daten für Volatilitäts-Berechnung.")

    # ── Expander C: Drawdown nach Präsidentenzyklus ──
    with st.expander("🏛️ Drawdown nach Präsidentenzyklus", expanded=False):
        _cycle_labels = {
            "Year 1 (Post-Election)": "Jahr 1 (Post-Election)",
            "Year 2 (Midterm Election)": "Jahr 2 (Midterm)",
            "Year 3 (Pre-Election)": "Jahr 3 (Pre-Election)",
            "Year 4 (Election Year)": "Jahr 4 (Election)",
        }
        _cycle_colors = {
            "Year 1 (Post-Election)": "#4d9fff",
            "Year 2 (Midterm Election)": "#ff6b6b",
            "Year 3 (Pre-Election)": "#34d399",
            "Year 4 (Election Year)": "#e8a425",
        }

        # Jahre nach Zyklusposition gruppieren
        _cycle_groups = {}
        for yr in _yd_years:
            cycle = get_presidential_cycle_year(yr)
            if cycle not in _cycle_groups:
                _cycle_groups[cycle] = []
            _cycle_groups[cycle].append(yr)

        if _cycle_groups:
            # Chart: Ø DD pro Zyklusposition
            fig_cyc = go.Figure()

            for cycle_key in ["Year 1 (Post-Election)", "Year 2 (Midterm Election)",
                              "Year 3 (Pre-Election)", "Year 4 (Election Year)"]:
                if cycle_key not in _cycle_groups:
                    continue
                _cyc_years = _cycle_groups[cycle_key]
                _cyc_curves = [np.array(year_data[y]["full_365"]) for y in _cyc_years if y in year_data]

                if not _cyc_curves:
                    continue

                avg_cyc_dd, _ = compute_avg_drawdown_curve(_cyc_curves, base=0.0)
                if len(avg_cyc_dd) == 0:
                    continue

                _is_current = (get_presidential_cycle_year(datetime.now().year) == cycle_key)
                _lw = 3.0 if _is_current else 1.8

                fig_cyc.add_trace(go.Scatter(
                    x=list(range(365)),
                    y=avg_cyc_dd.tolist(),
                    name=_cycle_labels.get(cycle_key, cycle_key) + f" ({len(_cyc_years)}J)",
                    line=dict(color=_cycle_colors.get(cycle_key, "#888"), width=_lw),
                    hovertemplate="%{y:.2f}%<extra></extra>",
                ))

            fig_cyc.update_xaxes(tickvals=MONTH_STARTS, ticktext=MONTH_LABELS)
            fig_cyc.update_yaxes(ticksuffix="%")
            fig_cyc = apply_se_theme(fig_cyc, title=f"Ø Drawdown nach Präsidentenzyklus — {ticker}", height=420)
            st.plotly_chart(fig_cyc, use_container_width=True, config=_PLOTLY_CFG)

            # Tabelle: Ø DD, Best, Worst pro Zyklusposition
            _card = (
                'background:linear-gradient(135deg,#0f1923,#131d2a);'
                'border:1px solid rgba(255,255,255,0.08);border-radius:10px;'
                'padding:12px 16px;text-align:center;'
            )
            _lbl_s = 'color:#8899aa;font-size:10px;text-transform:uppercase;letter-spacing:1px;'
            _val_s = 'font-size:14px;font-weight:700;font-variant-numeric:tabular-nums;margin:2px 0;'

            _table_rows = []
            for cycle_key in ["Year 1 (Post-Election)", "Year 2 (Midterm Election)",
                              "Year 3 (Pre-Election)", "Year 4 (Election Year)"]:
                if cycle_key not in _cycle_groups:
                    continue
                _cyc_years = _cycle_groups[cycle_key]
                _cyc_dds = []
                for y in _cyc_years:
                    if y not in year_data:
                        continue
                    c = np.array(year_data[y]["full_365"])
                    dd = compute_drawdown_series(c, base=0.0)
                    _cyc_dds.append({"year": y, "max_dd": float(dd.min())})

                if not _cyc_dds:
                    continue

                _dds_vals = [d["max_dd"] for d in _cyc_dds]
                _best = min(_cyc_dds, key=lambda d: abs(d["max_dd"]))  # Kleinster DD = bestes Jahr
                _worst = min(_cyc_dds, key=lambda d: d["max_dd"])       # Tiefster DD = schlimmstes

                _table_rows.append({
                    "cycle": cycle_key,
                    "label": _cycle_labels.get(cycle_key, cycle_key),
                    "color": _cycle_colors.get(cycle_key, "#888"),
                    "n": len(_cyc_dds),
                    "avg_dd": np.mean(_dds_vals),
                    "best_dd": _best["max_dd"],
                    "best_year": _best["year"],
                    "worst_dd": _worst["max_dd"],
                    "worst_year": _worst["year"],
                })

            if _table_rows:
                _cols = st.columns(len(_table_rows))
                for i, row in enumerate(_table_rows):
                    _is_cur = (get_presidential_cycle_year(datetime.now().year) == row["cycle"])
                    _border = f'border:2px solid {row["color"]};' if _is_cur else 'border:1px solid rgba(255,255,255,0.08);'
                    with _cols[i]:
                        st.markdown(
                            f'<div style="background:linear-gradient(135deg,#0f1923,#131d2a);'
                            f'{_border}border-radius:10px;padding:14px 10px;text-align:center;">'
                            f'<div style="color:{row["color"]};font-size:12px;font-weight:700;'
                            f'margin-bottom:8px;">{row["label"]}</div>'
                            f'<div style="{_lbl_s}">Ø Max DD ({row["n"]}J)</div>'
                            f'<div style="{_val_s}color:#ff4444;">{row["avg_dd"]:.1f}%</div>'
                            f'<div style="{_lbl_s}margin-top:6px;">Best</div>'
                            f'<div style="{_val_s}color:#34d399;">{row["best_dd"]:.1f}% ({row["best_year"]})</div>'
                            f'<div style="{_lbl_s}margin-top:6px;">Worst</div>'
                            f'<div style="{_val_s}color:#ff2222;">{row["worst_dd"]:.1f}% ({row["worst_year"]})</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

    # ── Methodik ──────────────────────────────────────────
    with st.expander("ℹ️ Methodik"):
        _n_years = len(year_data)
        _first_y = min(year_data.keys()) if year_data else "?"
        _last_y = max(year_data.keys()) if year_data else "?"
        st.markdown(f"""
### Datengrundlage

- **Ticker:** {ticker}
- **Datenzeitraum:** {_first_y}–{_last_y} ({_n_years} ausgewählte Jahre)
- **Datenquellen:** Yahoo Finance (ab ~1992) + Stooq.com (historische Daten ab 1896 für ausgewählte Indizes)
- **Normierung:** Jedes Jahr startet bei 100. Tägliche Returns werden kumuliert: Wert = 100 × exp(Σ log_return).
- **Interpolation:** Jede Jahreskurve wird auf 365 Kalendertage interpoliert, damit Jahre mit unterschiedlicher Handelstag-Anzahl vergleichbar sind.

### Rendite-Analyse

- **Saisonalchart:** Durchschnitt der normalisierten Jahreskurven über alle ausgewählten Jahre. Zeigt den typischen Jahresverlauf.
- **Konfidenzband (±1σ):** Standardabweichung um den Durchschnitt — wie stark streuen die Einzeljahre?
- **Aktuelles Jahr (Gold):** Das laufende Jahr wird als Overlay eingezeichnet, um die aktuelle Position mit dem Durchschnitt zu vergleichen.
- **Glättung:** Einstellbarer Moving Average auf der Ø-Kurve (Sidebar). Glättet Tagesrauschen.
- **Präsidentenzyklus-Overlay:** Optional: Ø-Kurve nur für eine Zyklusposition (Post-Election, Midterm, Pre-Election, Election).
- **Detrend-Indikator:** Entfernt den Trend und zeigt die reine Saisonalität auf einer 0–100 Skala. Über 50 = saisonal überdurchschnittlich.
- **Monats-/Quartals-Performance:** Durchschnittliche Rendite pro Monat/Quartal über alle ausgewählten Jahre.
- **Signifikanz-Tachos:** t-Test pro Monat/Quartal. p < 0,05 = statistisch signifikant (grün).
- **10-Jahres-Heatmap:** Monatsrenditen der letzten 10–20 Jahre als Farbmatrix. Gelber Rahmen = aktuelles Jahr+Monat.

### Drawdown-Analyse

- **Definition:** Der Drawdown misst den prozentualen Rückgang vom bisherigen Jahreshoch. Formel: DD = (Kurs – Höchstkurs seit Jahresbeginn) / Höchstkurs × 100. Ein Drawdown von –20% bedeutet: Der Kurs liegt 20% unter dem bisherigen Jahreshoch.
- **Ø Drawdown-Verlauf:** Für jedes Jahr wird der Drawdown pro Tag berechnet, dann über alle ausgewählten Jahre gemittelt. Das zeigt, wann im Jahr typischerweise die größten Rücksetzer auftreten.
- **Aktuelles Jahr (Gold):** Drawdown des laufenden Jahres als Overlay.
- **KPI-Karten:** Ø Max Drawdown (Durchschnitt der schlimmsten Rücksetzer pro Jahr), Worst DD (schlimmstes Einzeljahr), Aktueller DD.
- **Perzentil-Bar:** Vergleicht den aktuellen Max-Drawdown mit der historischen Verteilung.
- **Präsidentenzyklus-Drawdown:** Ø Drawdown-Verlauf getrennt nach den 4 Zyklusjahren. Zeigt, welche Zyklusposition historisch die tiefsten Rücksetzer hat (Midterm > Election).

### Volatilitäts-Analyse

- **Rolling Volatilität:** Annualisierte Standardabweichung der täglichen Log-Returns über ein rollendes Fenster (einstellbar: {vola_window} Tage in der Sidebar). Formel: σ_annualisiert = σ_täglich × √252 × 100.
- **Darstellung:** Pro Jahr wird die Rolling-Vola berechnet, auf 365 Punkte interpoliert, dann über alle ausgewählten Jahre gemittelt.
- **KPI-Karten:** Aktuelle Vola im historischen Kontext — Perzentil zeigt: "In wie viel Prozent der vergangenen Jahre war die Vola niedriger als heute?"
- **Farbcodierung:** Rot = erhöht (> Ø + 1σ), Grün = niedrig (< Ø – 1σ), Gold = normal.
        """)

    # ── Disclaimer ──
    st.markdown("---")
    st.caption(
        "Historische Muster garantieren keine zukünftigen Ergebnisse. Keine Anlageberatung."
    )

    render_footer()


main()

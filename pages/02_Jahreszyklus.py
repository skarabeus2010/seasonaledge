"""
SeasonalEdge — Yearly Seasonality
===================================
Saisonaler Jahresverlauf: Normierte Kurve ueber alle Jahre.
Aktuelles Jahr hervorgehoben, Konfidenzband, Einzeljahre.
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
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

from shared.constants import DEFAULT_TICKER, SE_COLORS, MONTH_NAMES_DE
from shared.data import download_data, preprocess
from shared.calculations import build_year_data, calculate_seasonal_average
from shared.charts import apply_se_theme

st.set_page_config(
    page_title="Yearly Seasonality — SeasonalEdge",
    page_icon="📈",
    layout="wide",
)

from shared.design import inject_se_css
inject_se_css()

MONTH_STARTS = [datetime(2024, m, 1).timetuple().tm_yday for m in range(1, 13)]
MONTH_LABELS = ["Jan","Feb","Mar","Apr","Mai","Jun","Jul","Aug","Sep","Okt","Nov","Dez"]

# ── Sidebar ──────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📈 Yearly Seasonality")
    st.markdown("---")

    ticker = st.text_input("Ticker", value=DEFAULT_TICKER, key="ys_ticker").upper().strip()

    period_options = [3, 5, 7, 10, 15, 20, 25, 30, "Max"]
    years_back_raw = st.select_slider(
        "Analyse-Zeitraum (Jahre)",
        options=period_options, value=20,
        format_func=lambda x: str(x), key="ys_period",
    )
    years_back_is_max = (years_back_raw == "Max")

    smoothing = st.slider("Glaettung (Tage)", 1, 21, 5, 2, key="ys_smooth")
    show_individual = st.checkbox("Einzelne Jahre", value=False, key="ys_indiv")
    show_bands = st.checkbox("Konfidenzband (+-1 Sigma)", value=True, key="ys_bands")
    show_current = st.checkbox("Aktuelles Jahr hervorheben", value=True, key="ys_current")

    st.markdown("---")
    from shared.outlier_manager import outlier_sidebar
    outlier_method = outlier_sidebar()

# ── Daten laden ──────────────────────────────────────
st.markdown("## 📈 Yearly Seasonality")

with st.spinner(f"Lade {ticker}..."):
    raw_df = download_data(ticker)

if raw_df is None or raw_df.empty:
    st.error(f"Keine Daten fuer '{ticker}'.")
    st.stop()

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
    st.warning("Nicht genuegend Daten.")
    st.stop()

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

# ── Chart ────────────────────────────────────────────
fig = go.Figure()
x_days = list(range(1, 366))

# Einzeljahre
if show_individual:
    for year, yd in year_data.items():
        fig.add_trace(go.Scatter(
            x=x_days, y=yd["full_365"],
            mode="lines",
            line=dict(color="rgba(200,220,255,0.15)", width=0.8),
            showlegend=False, hoverinfo="skip",
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
        name="+-1 Sigma", hoverinfo="skip",
    ))

# Saisonaler Durchschnitt
avg_smooth = avg.copy()
if smoothing > 1:
    avg_smooth = pd.Series(avg_smooth).rolling(smoothing, center=True, min_periods=1).mean().tolist()

fig.add_trace(go.Scatter(
    x=x_days, y=avg_smooth,
    mode="lines",
    line=dict(color=SE_COLORS["accent_blue"], width=3),
    name=f"Saisonaler Durchschnitt ({len(year_data)} Jahre)",
    hovertemplate="Tag %{x}<br>Wert: %{y:.2f}<extra></extra>",
))

# Aktuelles Jahr
if show_current and current_year in year_data:
    yd = year_data[current_year]
    today_doy = datetime.now().timetuple().tm_yday
    display_days = [d for d in yd["days"] if d <= today_doy]
    display_vals = yd["cumulative"][:len(display_days)]
    if display_days:
        fig.add_trace(go.Scatter(
            x=display_days, y=display_vals,
            mode="lines",
            line=dict(color="#F1C40F", width=2.5),
            name=f"{current_year} (aktuell)",
            hovertemplate=f"{current_year}<br>Tag %{{x}}<br>%{{y:.2f}}<extra></extra>",
        ))

fig.add_hline(y=100, line_dash="dash", line_color="rgba(255,255,255,0.2)", line_width=1)

fig = apply_se_theme(
    fig,
    title=f"{ticker} — Saisonaler Jahresverlauf ({len(year_data)} Jahre)",
    height=500,
)
fig.update_xaxes(
    tickmode="array", tickvals=MONTH_STARTS, ticktext=MONTH_LABELS,
    range=[1, 365],
)
fig.update_yaxes(title="Normalisiert (Start = 100)")

st.plotly_chart(fig, use_container_width=True)

# ── Monatsstatistiken ────────────────────────────────
st.markdown("---")
st.subheader("Monatsstatistiken")

from shared.calculations import calculate_period_stats

month_doy = {
    1: (1, 31), 2: (32, 59), 3: (60, 90), 4: (91, 120),
    5: (121, 151), 6: (152, 181), 7: (182, 212), 8: (213, 243),
    9: (244, 273), 10: (274, 304), 11: (305, 334), 12: (335, 365),
}

month_rows = []
for m in range(1, 13):
    s, e = month_doy[m]
    stats = calculate_period_stats(year_data, s, e)
    if stats:
        month_rows.append({
            "Monat": MONTH_NAMES_DE[m - 1],
            "Oe Rendite": f'{stats["avg_return"]:+.2f}%',
            "Median": f'{stats["median_return"]:+.2f}%',
            "Win-Rate": f'{stats["win_rate"]:.0f}%',
            "Max Gewinn": f'{stats["max_gain"]:+.1f}%',
            "Max Verlust": f'{stats["max_loss"]:+.1f}%',
            "n": stats["total_years"],
        })

if month_rows:
    st.dataframe(pd.DataFrame(month_rows), use_container_width=True, hide_index=True)

# ── Anomalie-Radar ───────────────────────────────────
st.markdown("---")
st.subheader("Anomalie-Radar (KI)")
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

        rc1, rc2, rc3, rc4 = st.columns(4)
        rc1.metric("Anomalie-Score", f"{r_score:.0f}/100")
        rc2.metric("Status", f"{r_icon} {r_label}")
        rc3.metric("Aktuelle 10d-Rendite", f'{radar["current_return"]:+.2f}%')
        rc4.metric("Historischer Oe", f'{radar["historical_avg"]:+.2f}%')
    else:
        st.caption(radar["error"])
except Exception as _e:
    st.caption(f"Anomalie-Radar nicht verfuegbar: {_e}")

# ── Disclaimer ──
st.markdown("---")
st.caption(
    "Historische Muster garantieren keine zukuenftigen Ergebnisse. Keine Anlageberatung."
)

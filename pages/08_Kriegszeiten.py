"""
SeasonalEdge — Im Schatten des Krieges
========================================
Saisonaler Verlauf in Kriegsjahren vs. Friedensjahren.
US-Kriege seit 1898 mit historischen Renditen.
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

from shared.constants import DEFAULT_TICKER, SE_COLORS
from shared.data import download_data, preprocess
from shared.calculations import (
    build_year_data, calculate_seasonal_average,
    get_war_years, get_peace_years,
)
from shared.charts import apply_se_theme

st.set_page_config(
    page_title="Im Schatten des Krieges — SeasonalEdge",
    page_icon="⚔️",
    layout="wide",
)

from shared.design import inject_se_css
inject_se_css()

MONTH_STARTS = [datetime(2024, m, 1).timetuple().tm_yday for m in range(1, 13)]
MONTH_LABELS = ["Jan","Feb","Mar","Apr","Mai","Jun","Jul","Aug","Sep","Okt","Nov","Dez"]

US_WARS = [
    {"name": "Spanisch-Amerikanischer Krieg", "start": 1898, "end": 1898},
    {"name": "Philippinisch-Amerikanischer Krieg", "start": 1899, "end": 1902},
    {"name": "Erster Weltkrieg (US)", "start": 1917, "end": 1918},
    {"name": "Zweiter Weltkrieg (US)", "start": 1941, "end": 1945},
    {"name": "Koreakrieg", "start": 1950, "end": 1953},
    {"name": "Vietnamkrieg", "start": 1965, "end": 1975},
    {"name": "Golfkrieg", "start": 1990, "end": 1991},
    {"name": "Krieg in Afghanistan", "start": 2001, "end": 2021},
    {"name": "Irakkrieg", "start": 2003, "end": 2011},
]

# ── Sidebar ──────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚔️ Im Schatten des Krieges")
    st.markdown("---")

    ticker = st.text_input("Ticker", value="^DJI", key="war_ticker").upper().strip()

    smoothing = st.slider("Glaettung (Tage)", 1, 21, 5, 2, key="war_smooth")

    st.markdown("---")
    show_individual = st.checkbox("Einzeljahre anzeigen", value=False, key="war_indiv")
    show_bands = st.checkbox("Konfidenzband (+-1 Sigma)", value=False, key="war_bands")

    st.markdown("---")
    from shared.outlier_manager import outlier_sidebar
    outlier_method = outlier_sidebar()

# ── Daten laden ──────────────────────────────────────
st.markdown("## ⚔️ Im Schatten des Krieges")
st.caption("Wie verhaelt sich der Markt in Kriegsjahren vs. Friedensjahren?")

with st.spinner(f"Lade {ticker}..."):
    raw_df = download_data(ticker)

if raw_df is None or raw_df.empty:
    st.error(f"Keine Daten fuer '{ticker}'.")
    st.stop()

df = preprocess(raw_df)
all_years = sorted(df["year"].unique())

year_data = build_year_data(df, all_years)

# Outlier Filter
from shared.outlier_manager import filter_year_data, outlier_info_box
year_data, outlier_years = filter_year_data(year_data, method=outlier_method)
outlier_info_box(outlier_years, outlier_method)

avg, std = calculate_seasonal_average(year_data)

all_war_years = get_war_years()
all_peace_years = set(get_peace_years(list(year_data.keys())))

war_matching = [y for y in year_data.keys() if y in all_war_years]
peace_matching = [y for y in year_data.keys() if y in all_peace_years]

st.caption(
    f"**{ticker}** | {min(year_data.keys())}–{max(year_data.keys())} | "
    f"{len(year_data)} Jahre | "
    f"Kriegsjahre: {len(war_matching)} | Friedensjahre: {len(peace_matching)}"
)

# ── Metriken ─────────────────────────────────────────
x_days = list(range(1, 366))

# Durchschnittskurven berechnen
war_curves = [year_data[y]["full_365"] for y in war_matching]
peace_curves = [year_data[y]["full_365"] for y in peace_matching]

war_avg = [np.mean([c[d] for c in war_curves]) for d in range(365)] if war_curves else []
peace_avg = [np.mean([c[d] for c in peace_curves]) for d in range(365)] if peace_curves else []

if smoothing > 1:
    if war_avg:
        war_avg = pd.Series(war_avg).rolling(smoothing, center=True, min_periods=1).mean().tolist()
    if peace_avg:
        peace_avg = pd.Series(peace_avg).rolling(smoothing, center=True, min_periods=1).mean().tolist()

# Renditen
war_returns = [(year_data[y]["full_365"][-1] / year_data[y]["full_365"][0] - 1) * 100 for y in war_matching]
peace_returns = [(year_data[y]["full_365"][-1] / year_data[y]["full_365"][0] - 1) * 100 for y in peace_matching]

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Kriegsjahre", f"{len(war_matching)}", f"Oe {np.mean(war_returns):+.1f}%" if war_returns else "—")
with m2:
    st.metric("Friedensjahre", f"{len(peace_matching)}", f"Oe {np.mean(peace_returns):+.1f}%" if peace_returns else "—")
with m3:
    war_wr = (sum(1 for r in war_returns if r > 0) / len(war_returns) * 100) if war_returns else 0
    st.metric("Win-Rate Krieg", f"{war_wr:.0f}%")
with m4:
    peace_wr = (sum(1 for r in peace_returns if r > 0) / len(peace_returns) * 100) if peace_returns else 0
    st.metric("Win-Rate Frieden", f"{peace_wr:.0f}%")

# ── Hauptchart: Krieg vs. Frieden ────────────────────
st.markdown("---")
st.subheader("Saisonaler Verlauf: Krieg vs. Frieden")

fig = go.Figure()

# Einzeljahre
if show_individual:
    for y in war_matching:
        fig.add_trace(go.Scatter(
            x=x_days, y=year_data[y]["full_365"],
            mode="lines", line=dict(color="rgba(231,76,60,0.15)", width=0.7),
            showlegend=False, hoverinfo="skip",
        ))
    for y in peace_matching:
        fig.add_trace(go.Scatter(
            x=x_days, y=year_data[y]["full_365"],
            mode="lines", line=dict(color="rgba(46,204,113,0.15)", width=0.7),
            showlegend=False, hoverinfo="skip",
        ))

# Konfidenzband
if show_bands and war_curves:
    war_std = [np.std([c[d] for c in war_curves]) for d in range(365)]
    upper = [war_avg[i] + war_std[i] for i in range(365)]
    lower = [war_avg[i] - war_std[i] for i in range(365)]
    fig.add_trace(go.Scatter(x=x_days, y=upper, mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=x_days, y=lower, mode="lines", line=dict(width=0),
        fill="tonexty", fillcolor="rgba(231,76,60,0.06)", showlegend=False, hoverinfo="skip"))

# Kriegsjahre Durchschnitt
if war_avg:
    fig.add_trace(go.Scatter(
        x=x_days, y=war_avg,
        mode="lines", name=f"Kriegsjahre ({len(war_matching)})",
        line=dict(color=SE_COLORS["negative"], width=3),
        hovertemplate="Krieg<br>Tag %{x}<br>%{y:.2f}<extra></extra>",
    ))

# Friedensjahre Durchschnitt
if peace_avg:
    fig.add_trace(go.Scatter(
        x=x_days, y=peace_avg,
        mode="lines", name=f"Friedensjahre ({len(peace_matching)})",
        line=dict(color=SE_COLORS["positive"], width=3),
        hovertemplate="Frieden<br>Tag %{x}<br>%{y:.2f}<extra></extra>",
    ))

# Gesamt-Durchschnitt
avg_smooth = avg.copy()
if smoothing > 1:
    avg_smooth = pd.Series(avg_smooth).rolling(smoothing, center=True, min_periods=1).mean().tolist()
fig.add_trace(go.Scatter(
    x=x_days, y=avg_smooth,
    mode="lines", name=f"Gesamt ({len(year_data)})",
    line=dict(color=SE_COLORS["accent_blue"], width=2, dash="dash"),
))

fig.add_hline(y=100, line_dash="dot", line_color="rgba(255,255,255,0.2)", line_width=1)

fig = apply_se_theme(
    fig,
    title=f"{ticker} — Im Schatten des Krieges ({min(year_data.keys())}–{max(year_data.keys())})",
    height=500,
)
fig.update_xaxes(tickmode="array", tickvals=MONTH_STARTS, ticktext=MONTH_LABELS, range=[1, 365])
fig.update_yaxes(title="Normalisiert (Start = 100)")

st.plotly_chart(fig, use_container_width=True)

# ── Kriegsliste ──────────────────────────────────────
st.markdown("---")
st.subheader("US-Kriege mit Boerseneinfluss")

war_rows = []
for w in US_WARS:
    w_years = [y for y in range(w["start"], w["end"] + 1) if y in year_data]
    if w_years:
        w_rets = [(year_data[y]["full_365"][-1] / year_data[y]["full_365"][0] - 1) * 100 for y in w_years]
        war_rows.append({
            "Krieg": w["name"],
            "Zeitraum": f'{w["start"]}–{w["end"]}',
            "Jahre im Datensatz": len(w_years),
            "Oe Rendite": f"{np.mean(w_rets):+.1f}%",
            "Win-Rate": f"{sum(1 for r in w_rets if r > 0)/len(w_rets)*100:.0f}%",
            "Max Gewinn": f"{max(w_rets):+.1f}%",
            "Max Verlust": f"{min(w_rets):+.1f}%",
        })

if war_rows:
    st.dataframe(pd.DataFrame(war_rows), use_container_width=True, hide_index=True)

# ── Jahresrendite Chart: Krieg markiert ──────────────
st.markdown("---")
st.subheader("Jahresrenditen — Kriegsjahre markiert")

years_sorted = sorted(year_data.keys())
yr_returns = [(year_data[y]["full_365"][-1] / year_data[y]["full_365"][0] - 1) * 100 for y in years_sorted]
yr_colors = [SE_COLORS["negative"] if y in all_war_years else SE_COLORS["positive"] for y in years_sorted]

fig2 = go.Figure(go.Bar(
    x=years_sorted,
    y=yr_returns,
    marker_color=yr_colors,
    hovertemplate="<b>%{x}</b><br>Rendite: %{y:+.1f}%<extra></extra>",
))
fig2.add_hline(y=0, line_color="rgba(255,255,255,0.3)", line_width=1)
fig2 = apply_se_theme(fig2, title=f"{ticker} — Jahresrenditen (rot = Krieg)", height=380)
fig2.update_yaxes(title="Rendite (%)", tickformat="+.0f", ticksuffix="%")

st.plotly_chart(fig2, use_container_width=True)

st.caption(f"Rot = Kriegsjahre ({len(war_matching)}) | Gruen = Friedensjahre ({len(peace_matching)})")

# ── Dow Jones in realen Preisen (inflationsbereinigt) ───
st.markdown("---")
st.subheader("Dow Jones in realen Preisen (inflationsbereinigt)")
st.caption("Nominal vs. kaufkraftbereinigt (Basis: 2024-Dollar) — logarithmische Skala")

try:
    from shared.cpi_data import build_nominal_vs_real_df

    # Jahresschlusskurse aus Tagesdaten extrahieren
    nominal_prices = {}
    for y in sorted(df["year"].unique()):
        year_df = df[df["year"] == y].sort_values("Date")
        if not year_df.empty:
            nominal_prices[y] = float(year_df["Close"].iloc[-1])

    real_df = build_nominal_vs_real_df(nominal_prices, base_year=2024)

    if not real_df.empty and len(real_df) > 10:
        fig3 = go.Figure()

        # Nominal (Gold)
        fig3.add_trace(go.Scatter(
            x=real_df["year"], y=real_df["nominal"],
            mode="lines", name="Nominal",
            line=dict(color=SE_COLORS["accent_warm"], width=2.5),
            hovertemplate="<b>%{x}</b><br>Nominal: %{y:,.0f}<extra></extra>",
        ))

        # Real (Teal)
        fig3.add_trace(go.Scatter(
            x=real_df["year"], y=real_df["real"],
            mode="lines", name="Real (2024-Dollar)",
            line=dict(color=SE_COLORS["accent"], width=2.5),
            hovertemplate="<b>%{x}</b><br>Real: %{y:,.0f}<extra></extra>",
        ))

        # Kriegszonen als Shapes
        for w in US_WARS:
            fig3.add_shape(
                type="rect", xref="x", yref="paper",
                x0=w["start"] - 0.5, x1=w["end"] + 0.5,
                y0=0, y1=1,
                fillcolor="rgba(231,76,60,0.12)",
                line=dict(width=0),
            )
            mid_x = (w["start"] + w["end"]) / 2
            fig3.add_annotation(
                x=mid_x, y=1.02, xref="x", yref="paper",
                text=w["name"].split("(")[0].strip(),
                showarrow=False,
                font=dict(size=8, color="rgba(231,76,60,0.7)"),
                textangle=-45,
            )

        fig3 = apply_se_theme(
            fig3,
            title=f"{ticker} — Nominal vs. Real ({real_df['year'].min()}–{real_df['year'].max()})",
            height=520,
        )
        fig3.update_yaxes(type="log", title="Dow Jones (log)", tickformat=",.0f")
        fig3.update_xaxes(dtick=10)

        st.plotly_chart(fig3, use_container_width=True)

        # Kennzahlen
        if len(real_df) > 1:
            first_nom = real_df["nominal"].iloc[0]
            last_nom = real_df["nominal"].iloc[-1]
            first_real = real_df["real"].iloc[0]
            last_real = real_df["real"].iloc[-1]
            years_span = real_df["year"].iloc[-1] - real_df["year"].iloc[0]

            k1, k2, k3, k4 = st.columns(4)
            with k1:
                nom_gain = (last_nom / first_nom - 1) * 100
                st.metric("Nominaler Anstieg", f"{nom_gain:,.0f}%")
            with k2:
                real_gain = (last_real / first_real - 1) * 100
                st.metric("Realer Anstieg", f"{real_gain:,.0f}%")
            with k3:
                nom_cagr = ((last_nom / first_nom) ** (1 / years_span) - 1) * 100
                st.metric("Nominale CAGR", f"{nom_cagr:.1f}%")
            with k4:
                real_cagr = ((last_real / first_real) ** (1 / years_span) - 1) * 100
                st.metric("Reale CAGR", f"{real_cagr:.1f}%")

        st.caption(
            "CPI-Quelle: Bureau of Labor Statistics (1982-84 = 100). "
            "Pre-1913 Werte rekonstruiert aus historischen Preisindizes."
        )
    else:
        st.info("Nicht genuegend Daten fuer inflationsbereinigte Ansicht.")

except Exception as e:
    st.warning(f"Inflationsbereinigte Ansicht nicht verfuegbar: {e}")

# ── Disclaimer ──
st.markdown("---")
st.caption(
    "Historische Muster garantieren keine zukuenftigen Ergebnisse. Keine Anlageberatung."
)

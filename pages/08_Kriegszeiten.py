"""
SeasonAlpha — Im Schatten des Krieges
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
    page_title="Im Schatten des Krieges — SeasonAlpha",
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

# ── Dow Jones Langfristchart mit Kriegszonen ────────────
st.markdown("---")
st.subheader("Der Dow Jones im Schatten der Kriege")
st.caption("Langfristuebersicht seit 1886 — logarithmische Skala, alle groesseren US-Kriegsbeteiligungen markiert")

# Historische Dow Jones Jahresschlusskurse (rekonstruiert, Anker: 31.12.2024 = 42.544)
DOW_ANNUAL = [
    (1886,41.24),(1887,37.77),(1888,39.59),(1889,42.04),(1890,36.09),
    (1891,42.45),(1892,39.67),(1893,29.91),(1894,29.74),(1895,30.42),
    (1896,29.9),(1897,36.2),(1898,44.34),(1899,48.41),(1900,51.81),
    (1901,47.3),(1902,47.1),(1903,35.98),(1904,51.0),(1905,70.48),
    (1906,69.13),(1907,43.05),(1908,63.12),(1909,72.57),(1910,59.61),
    (1911,59.84),(1912,64.38),(1913,57.72),(1914,54.59),(1915,99.17),
    (1916,95.01),(1917,74.38),(1918,82.2),(1919,107.23),(1920,71.95),
    (1921,81.11),(1922,98.74),(1923,95.53),(1924,120.52),(1925,156.68),
    (1926,157.21),(1927,202.41),(1928,300.0),(1929,248.49),(1930,164.58),
    (1931,77.89),(1932,59.92),(1933,99.89),(1934,104.02),(1935,144.1),
    (1936,179.87),(1937,120.84),(1938,154.74),(1939,150.22),(1940,131.12),
    (1941,110.95),(1942,119.39),(1943,135.88),(1944,152.31),(1945,192.9),
    (1946,177.2),(1947,181.15),(1948,177.29),(1949,200.13),(1950,235.41),
    (1951,269.24),(1952,291.91),(1953,280.9),(1954,404.39),(1955,488.38),
    (1956,499.46),(1957,435.68),(1958,583.64),(1959,679.36),(1960,615.91),
    (1961,731.14),(1962,652.11),(1963,762.96),(1964,874.13),(1965,969.23),
    (1966,785.66),(1967,905.08),(1968,943.73),(1969,800.38),(1970,838.95),
    (1971,890.21),(1972,1020.01),(1973,850.89),(1974,616.3),(1975,852.47),
    (1976,1004.72),(1977,831.2),(1978,805.02),(1979,838.75),(1980,964.06),
    (1981,875.07),(1982,1046.59),(1983,1258.73),(1984,1211.66),(1985,1546.8),
    (1986,1896.07),(1987,1938.92),(1988,2168.68),(1989,2753.36),(1990,2633.86),
    (1991,3169.06),(1992,3301.21),(1993,3754.14),(1994,3834.48),(1995,5117.11),
    (1996,6448.07),(1997,7907.92),(1998,9181.09),(1999,11496.56),(2000,10786.07),
    (2001,10020.26),(2002,8340.87),(2003,10452.77),(2004,10782.04),(2005,10716.27),
    (2006,12461.95),(2007,13263.25),(2008,8774.97),(2009,10426.41),(2010,11575.4),
    (2011,12215.52),(2012,13102.37),(2013,16574.5),(2014,17820.9),(2015,17423.5),
    (2016,19761.73),(2017,24717.97),(2018,23326.35),(2019,28537.46),(2020,30606.42),
    (2021,36339.01),(2022,33148.44),(2023,37689.78),(2024,42544.22),(2025,48062.21),
]

# Kriege mit exakten Zeitraeumen (Fraktionsjahre)
WARS_DETAIL = [
    {"name": "Spanisch-Amerikanischer Krieg", "s": 1898.3, "e": 1898.6,
     "color": "rgba(160,155,180,0.22)", "border": "#a09bb4"},
    {"name": "Philippinisch-Amerikanischer Krieg", "s": 1899.1, "e": 1902.5,
     "color": "rgba(180,160,130,0.20)", "border": "#b4a082"},
    {"name": "Erster Weltkrieg (US)", "s": 1917.25, "e": 1918.85,
     "color": "rgba(200,85,75,0.22)", "border": "#c8554b"},
    {"name": "Zweiter Weltkrieg (US)", "s": 1941.93, "e": 1945.67,
     "color": "rgba(210,65,55,0.22)", "border": "#d24137"},
    {"name": "Koreakrieg", "s": 1950.48, "e": 1953.57,
     "color": "rgba(70,130,200,0.22)", "border": "#4682c8"},
    {"name": "Vietnamkrieg", "s": 1965.17, "e": 1975.33,
     "color": "rgba(60,170,110,0.20)", "border": "#3caa6e"},
    {"name": "Golfkrieg", "s": 1990.58, "e": 1991.16,
     "color": "rgba(200,170,60,0.22)", "border": "#c8aa3c"},
    {"name": "Krieg in Afghanistan", "s": 2001.76, "e": 2021.66,
     "color": "rgba(150,100,180,0.15)", "border": "#9664b4"},
    {"name": "Irakkrieg", "s": 2003.22, "e": 2011.96,
     "color": "rgba(200,120,60,0.18)", "border": "#c8783c"},
]

dow_years = [d[0] for d in DOW_ANNUAL]
dow_prices = [d[1] for d in DOW_ANNUAL]

def _interpolate_dow(year_frac):
    """Logarithmisch interpolierter Dow-Kurs fuer Fraktionsjahre."""
    for i in range(len(DOW_ANNUAL) - 1):
        if DOW_ANNUAL[i][0] <= year_frac < DOW_ANNUAL[i + 1][0]:
            frac = (year_frac - DOW_ANNUAL[i][0]) / (DOW_ANNUAL[i + 1][0] - DOW_ANNUAL[i][0])
            log_a = np.log(DOW_ANNUAL[i][1])
            log_b = np.log(DOW_ANNUAL[i + 1][1])
            return np.exp(log_a + frac * (log_b - log_a))
    return DOW_ANNUAL[-1][1]

fig3 = go.Figure()

# Dow Jones Linie
fig3.add_trace(go.Scatter(
    x=dow_years, y=dow_prices,
    mode="lines", name="Dow Jones",
    line=dict(color=SE_COLORS["accent_warm"], width=2.2),
    hovertemplate="<b>%{x}</b><br>Dow Jones: %{y:,.0f}<extra></extra>",
))

# Kriegszonen + Labels
label_y_pos = [0.93, 0.85, 0.93, 0.85, 0.93, 0.85, 0.93, 0.77, 0.85]
for i, w in enumerate(WARS_DETAIL):
    # Schattierung
    fig3.add_shape(
        type="rect", xref="x", yref="paper",
        x0=w["s"], x1=w["e"], y0=0, y1=1,
        fillcolor=w["color"], line=dict(width=0),
    )
    # Gepunktete Start-/Endlinien
    for x_val in [w["s"], w["e"]]:
        fig3.add_shape(
            type="line", xref="x", yref="paper",
            x0=x_val, x1=x_val, y0=0, y1=1,
            line=dict(color=w["border"], width=1, dash="dot"),
        )
    # Label
    mid_x = (w["s"] + w["e"]) / 2
    short_name = w["name"].split("(")[0].strip()
    fig3.add_annotation(
        x=mid_x, y=label_y_pos[i], xref="x", yref="paper",
        text=f"<b>{short_name}</b>",
        showarrow=False,
        font=dict(size=10, color=w["border"]),
        bgcolor="rgba(10,12,16,0.9)",
        borderpad=3, bordercolor=w["border"], borderwidth=1,
    )
    # Performance-Label
    sp = _interpolate_dow(w["s"])
    ep = _interpolate_dow(w["e"])
    pct = (ep - sp) / sp * 100
    pct_color = SE_COLORS["positive"] if pct >= 0 else SE_COLORS["negative"]
    fig3.add_annotation(
        x=mid_x, y=label_y_pos[i] - 0.05, xref="x", yref="paper",
        text=f"<b>{pct:+.1f}%</b>",
        showarrow=False,
        font=dict(size=11, color=pct_color),
        bgcolor="rgba(10,12,16,0.85)",
        borderpad=2,
    )

fig3 = apply_se_theme(
    fig3,
    title="Dow Jones im Schatten der Kriege (1886–2025)",
    height=600,
)
fig3.update_yaxes(type="log", title="Dow Jones (logarithmisch)", tickformat=",.0f")
fig3.update_xaxes(dtick=10, range=[1885, 2026])

st.plotly_chart(fig3, use_container_width=True)

st.caption(
    "Daten: Jaehrliche Schlusskurse rekonstruiert aus Dow Jones Annual Returns, "
    "Ankerpunkt: 31.12.2024 = 42.544 Punkte. Logarithmische Y-Achse."
)

# ── Disclaimer ──
st.markdown("---")
st.caption(
    "Historische Muster garantieren keine zukuenftigen Ergebnisse. Keine Anlageberatung."
)

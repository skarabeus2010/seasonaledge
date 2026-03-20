"""
SeasonalEdge — Sektor-Rotation
================================
Welche Sektoren performen wann am besten?
Heatmap: Monat × Sektor · Rotationssignal · Top/Flop Rankings
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

from shared.constants import SE_COLORS, MONTH_NAMES_DE
from shared.data import download_data, preprocess
from shared.charts import apply_se_theme
from shared.sector_rotation import (
    SECTOR_ETFS, EU_SECTOR_ETFS,
    calculate_sector_seasonality,
    get_best_sectors_by_month,
    get_worst_sectors_by_month,
    calculate_rotation_signal,
    monthly_sector_stats,
)

# ── Page Config ──────────────────────────────────────
st.set_page_config(
    page_title="Sektor-Rotation — SeasonalEdge",
    page_icon="🔄",
    layout="wide",
)

from shared.design import inject_se_css
inject_se_css()

st.markdown("## 🔄 Sektor-Rotation")
st.caption("Welche Sektoren performen historisch in welchem Monat am besten?")

# ── Sidebar ──────────────────────────────────────────
st.sidebar.markdown("### ⚙️ Einstellungen")

region = st.sidebar.selectbox("🌍 Region", ["US Sektoren (SPDR)", "EU Sektoren"],
                               help="US: XLK, XLE, XLF... · EU: iShares STOXX Europe")

if region == "US Sektoren (SPDR)":
    sector_map = SECTOR_ETFS
else:
    sector_map = EU_SECTOR_ETFS

# Sektoren auswählen
available = list(sector_map.keys())
selected_sectors = st.sidebar.multiselect(
    "📊 Sektoren",
    available,
    default=available,
    format_func=lambda x: f"{x} — {sector_map[x]}",
)

years_back = st.sidebar.slider("📅 Jahre zurück", 5, 30, 15)
min_years = st.sidebar.slider("Min. Jahre für Berechnung", 3, 10, 5)

if not selected_sectors:
    st.warning("Bitte wähle mindestens einen Sektor aus.")
    st.stop()

# ── Daten laden ──────────────────────────────────────
period = f"{years_back}y"

sector_data = {}
progress = st.progress(0, text="Lade Sektor-Daten...")

for i, ticker in enumerate(selected_sectors):
    progress.progress((i + 1) / len(selected_sectors), text=f"Lade {ticker}...")
    try:
        df = download_data(ticker, period=period)
        if df is not None and not df.empty:
            df = preprocess(df)
            sector_data[ticker] = df
    except Exception:
        st.sidebar.warning(f"⚠️ {ticker} nicht geladen")

progress.empty()

if len(sector_data) < 2:
    st.error("Mindestens 2 Sektoren müssen geladen werden.")
    st.stop()

st.success(f"✅ {len(sector_data)} von {len(selected_sectors)} Sektoren geladen "
           f"({years_back} Jahre)")

# ── Saisonalität berechnen ───────────────────────────
seasonality = calculate_sector_seasonality(sector_data, min_years=min_years)
stats = monthly_sector_stats(sector_data)

# ── Aktueller Monat: Rotationssignal ─────────────────
current_month = datetime.now().month
current_month_name = MONTH_NAMES_DE[current_month - 1] if 1 <= current_month <= 12 else str(current_month)

st.markdown("---")
st.markdown(f"### 🚦 Rotationssignal — {current_month_name}")
st.caption("Basierend auf historischer Performance: Welche Sektoren jetzt am stärksten?")

rotation = calculate_rotation_signal(seasonality, current_month, lookforward=1)

if not rotation.empty:
    sig_cols = st.columns(min(len(rotation), 4))
    for i, (_, row) in enumerate(rotation.head(4).iterrows()):
        with sig_cols[i]:
            color = "normal" if row["avg_return_pct"] >= 0 else "inverse"
            st.metric(
                f"#{row['rank']} {row['ticker']}",
                f"{row['avg_return_pct']:+.2f}%",
                delta=row["sector"],
                delta_color="off",
            )

    # Ranking-Tabelle
    with st.expander("📋 Vollständiges Ranking"):
        display_rot = rotation.copy()
        display_rot.columns = ["Ticker", "Sektor", "Ø Rendite %", "Rang"]
        st.dataframe(display_rot.style.format({"Ø Rendite %": "{:+.2f}"}),
                      use_container_width=True, hide_index=True)

# ── Heatmap: Monat × Sektor ─────────────────────────
st.markdown("---")
st.markdown("### 🗺️ Saisonale Heatmap — Monat × Sektor")

if not seasonality.empty:
    # Monatsnamen
    month_labels = [MONTH_NAMES_DE[m - 1] if 1 <= m <= 12 else str(m) for m in seasonality.index]
    sector_labels = [f"{t} ({sector_map.get(t, t)})" for t in seasonality.columns]

    z_vals = seasonality.values.tolist()

    fig_hm = go.Figure(data=go.Heatmap(
        z=z_vals,
        x=sector_labels,
        y=month_labels,
        colorscale=[[0, SE_COLORS["negative"]], [0.5, SE_COLORS["bg"]], [1, SE_COLORS["positive"]]],
        zmid=0,
        text=[[f"{v:+.1f}%" if not np.isnan(v) else "—" for v in row] for row in z_vals],
        texttemplate="%{text}",
        textfont=dict(size=11, color=SE_COLORS["text_primary"]),
        hovertemplate="Sektor: %{x}<br>Monat: %{y}<br>Ø Rendite: %{z:+.2f}%<extra></extra>",
        colorbar=dict(
            title=dict(text="Ø %", font=dict(color=SE_COLORS["text_muted"])),
            tickfont=dict(color=SE_COLORS["text_muted"]),
        ),
    ))

    fig_hm = apply_se_theme(fig_hm, title="Ø Monatsrendite pro Sektor", height=500)
    fig_hm.update_xaxes(tickangle=-45)
    st.plotly_chart(fig_hm, use_container_width=True)

# ── Top/Flop pro Monat ──────────────────────────────
st.markdown("### 🏆 Top & Flop Sektoren pro Monat")

best = get_best_sectors_by_month(seasonality, top_n=3)
worst = get_worst_sectors_by_month(seasonality, bottom_n=3)

top_col, flop_col = st.columns(2)

with top_col:
    st.markdown("**🟢 Top 3 pro Monat**")
    rows_top = []
    for month in range(1, 13):
        m_name = MONTH_NAMES_DE[month - 1] if 1 <= month <= 12 else str(month)
        if month in best:
            entries = best[month]
            for rank, (ticker, ret) in enumerate(entries, 1):
                rows_top.append({
                    "Monat": m_name,
                    "Rang": rank,
                    "Ticker": ticker,
                    "Sektor": sector_map.get(ticker, ticker),
                    "Ø Rendite %": ret,
                })
    if rows_top:
        df_top = pd.DataFrame(rows_top)
        st.dataframe(df_top.style.format({"Ø Rendite %": "{:+.2f}"}),
                      use_container_width=True, hide_index=True)

with flop_col:
    st.markdown("**🔴 Flop 3 pro Monat**")
    rows_flop = []
    for month in range(1, 13):
        m_name = MONTH_NAMES_DE[month - 1] if 1 <= month <= 12 else str(month)
        if month in worst:
            entries = worst[month]
            for rank, (ticker, ret) in enumerate(entries, 1):
                rows_flop.append({
                    "Monat": m_name,
                    "Rang": rank,
                    "Ticker": ticker,
                    "Sektor": sector_map.get(ticker, ticker),
                    "Ø Rendite %": ret,
                })
    if rows_flop:
        df_flop = pd.DataFrame(rows_flop)
        st.dataframe(df_flop.style.format({"Ø Rendite %": "{:+.2f}"}),
                      use_container_width=True, hide_index=True)

# ── Sektor-Vergleich: Jahresverlauf ──────────────────
st.markdown("---")
st.markdown("### 📈 Saisonaler Jahresverlauf pro Sektor")

compare_sectors = st.multiselect(
    "Sektoren zum Vergleich",
    list(sector_data.keys()),
    default=list(sector_data.keys())[:4],
    format_func=lambda x: f"{x} — {sector_map.get(x, x)}",
)

if compare_sectors:
    fig_line = go.Figure()

    # Farbpalette
    line_colors = [
        SE_COLORS["accent"], SE_COLORS["accent2"], "#4d9fff", "#ff6b9d",
        "#a78bfa", "#fbbf24", "#34d399", "#f87171",
        "#60a5fa", "#c084fc", "#fb923c",
    ]

    for i, ticker in enumerate(compare_sectors):
        if ticker not in seasonality.columns:
            continue

        vals = seasonality[ticker].values
        months = list(range(1, 13))
        month_names = [MONTH_NAMES_DE[m - 1] if 1 <= m <= 12 else str(m)[:3] for m in months]

        # Kumulierte Rendite
        cum_vals = np.nancumsum(vals)

        color = line_colors[i % len(line_colors)]
        fig_line.add_trace(go.Scatter(
            x=month_names,
            y=cum_vals,
            mode="lines+markers",
            name=f"{ticker} ({sector_map.get(ticker, '')})",
            line=dict(color=color, width=2),
            marker=dict(size=5, color=color),
            hovertemplate=f"{ticker}<br>Monat: %{{x}}<br>Kum. Rendite: %{{y:+.2f}}%<extra></extra>",
        ))

    fig_line = apply_se_theme(fig_line, title="Kumulierte saisonale Rendite", height=450)
    fig_line.update_yaxes(title_text="Kumulierte Ø Rendite %")
    fig_line.update_layout(legend=dict(
        orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5,
    ))
    st.plotly_chart(fig_line, use_container_width=True)

# ── Win-Rate Heatmap ─────────────────────────────────
st.markdown("### 🎯 Win-Rate Heatmap")

if not stats.empty:
    wr_pivot = stats.pivot_table(index="month", columns="ticker", values="win_rate_pct")
    if not wr_pivot.empty:
        month_labels_wr = [MONTH_NAMES_DE[m - 1] if 1 <= m <= 12 else str(m) for m in wr_pivot.index]
        sector_labels_wr = [f"{t}" for t in wr_pivot.columns]
        z_wr = wr_pivot.values.tolist()

        fig_wr = go.Figure(data=go.Heatmap(
            z=z_wr,
            x=sector_labels_wr,
            y=month_labels_wr,
            colorscale=[[0, SE_COLORS["negative"]], [0.5, "#1c2636"], [1, SE_COLORS["positive"]]],
            zmid=50,
            zmin=20, zmax=80,
            text=[[f"{v:.0f}%" if not np.isnan(v) else "—" for v in row] for row in z_wr],
            texttemplate="%{text}",
            textfont=dict(size=11, color=SE_COLORS["text_primary"]),
            hovertemplate="Sektor: %{x}<br>Monat: %{y}<br>Win-Rate: %{z:.0f}%<extra></extra>",
            colorbar=dict(
                title=dict(text="Win %", font=dict(color=SE_COLORS["text_muted"])),
                tickfont=dict(color=SE_COLORS["text_muted"]),
            ),
        ))

        fig_wr = apply_se_theme(fig_wr, title="Win-Rate pro Sektor und Monat", height=500)
        fig_wr.update_xaxes(tickangle=-45)
        st.plotly_chart(fig_wr, use_container_width=True)

# ── Footer ────────────────────────────────────────────
st.markdown("---")
st.caption(f"Daten: {len(sector_data)} Sektoren · {years_back} Jahre · "
           f"Min. {min_years} Jahre pro Berechnung · SeasonalEdge Sektor-Rotation")

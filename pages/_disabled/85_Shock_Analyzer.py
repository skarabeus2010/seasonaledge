"""
SeasonAlpha — Shock Analyzer
==============================
Wenn Asset A um X% fällt/steigt — wie performt Asset B danach?
Beispiel: Öl fällt 5% → Was passiert mit dem DAX nach 1, 5, 20, 60 Tagen?
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
from shared.charts import apply_se_theme
from shared.shock_analysis import find_shocks, analyze_impact, shock_heatmap_data

# ── Page Config ──────────────────────────────────────
st.set_page_config(
    page_title="Shock Analyzer — SeasonAlpha",
    page_icon="💥",
    layout="wide",
)

from shared.design import inject_se_css
inject_se_css()

st.markdown("## 💥 Shock Analyzer")
st.caption("Wenn Asset A um X% fällt/steigt — wie performt Asset B danach?")

# ── Sidebar ──────────────────────────────────────────
st.sidebar.markdown("### ⚙️ Einstellungen")

# Vordefinierte Szenarien
SCENARIOS = {
    "Eigene Auswahl": ("", ""),
    "Öl-Crash → DAX": ("CL=F", "^GDAXI"),
    "Öl-Crash → S&P 500": ("CL=F", "^GSPC"),
    "VIX-Spike → S&P 500": ("^VIX", "^GSPC"),
    "USD/EUR Shock → DAX": ("EURUSD=X", "^GDAXI"),
    "Gold-Crash → S&P 500": ("GC=F", "^GSPC"),
    "S&P 500 Crash → Bitcoin": ("^GSPC", "BTC-USD"),
    "China-Crash → DAX": ("^HSI", "^GDAXI"),
    "Bond-Crash → S&P 500": ("^TNX", "^GSPC"),
}

scenario = st.sidebar.selectbox("📋 Szenario", list(SCENARIOS.keys()))

if scenario == "Eigene Auswahl":
    trigger_ticker = st.sidebar.text_input("🔴 Trigger-Asset (A)", value="CL=F",
                                            help="Asset das den Shock auslöst")
    target_ticker = st.sidebar.text_input("🎯 Ziel-Asset (B)", value="^GDAXI",
                                           help="Asset dessen Reaktion gemessen wird")
else:
    trigger_ticker, target_ticker = SCENARIOS[scenario]
    st.sidebar.info(f"Trigger: **{trigger_ticker}** → Ziel: **{target_ticker}**")

st.sidebar.markdown("---")

direction = st.sidebar.selectbox("📉 Shock-Richtung", ["down", "up", "both"],
                                  format_func=lambda x: {"down": "📉 Kurseinbruch",
                                                          "up": "📈 Kurssprung",
                                                          "both": "↕️ Beides"}[x])

threshold = st.sidebar.slider("⚡ Schwellenwert (%)", 1.0, 15.0, 5.0, 0.5,
                                help="Mindest-Tagesänderung um als Shock zu gelten")

years_back = st.sidebar.slider("📅 Jahre zurück", 5, 50, 20)

horizons_str = st.sidebar.text_input("🕐 Horizonte (Tage)", "1, 5, 10, 20, 60",
                                      help="Kommagetrennt, z.B. 1, 5, 10, 20, 60")

try:
    horizons = [int(x.strip()) for x in horizons_str.split(",")]
except ValueError:
    horizons = [1, 5, 10, 20, 60]
    st.sidebar.error("Ungültige Horizonte — verwende Standardwerte")

# ── Daten laden ──────────────────────────────────────
if not trigger_ticker or not target_ticker:
    st.warning("Bitte wähle ein Szenario oder gib Trigger- und Ziel-Ticker ein.")
    st.stop()

period = f"{years_back}y"

with st.spinner(f"Lade Daten für {trigger_ticker} und {target_ticker}..."):
    try:
        df_trigger = download_data(trigger_ticker, period=period)
        df_target = download_data(target_ticker, period=period)
    except Exception as e:
        st.error(f"Fehler beim Laden: {e}")
        st.stop()

if df_trigger is None or df_trigger.empty:
    st.error(f"Keine Daten für Trigger-Asset: {trigger_ticker}")
    st.stop()
if df_target is None or df_target.empty:
    st.error(f"Keine Daten für Ziel-Asset: {target_ticker}")
    st.stop()

df_trigger = preprocess(df_trigger)
df_target = preprocess(df_target)

# ── Shocks finden ────────────────────────────────────
shocks = find_shocks(df_trigger, threshold=threshold, direction=direction)
n_shocks = len(shocks)

if n_shocks == 0:
    st.warning(f"Keine Shock-Events gefunden für {trigger_ticker} mit Schwellenwert {threshold}%. "
               "Versuche einen niedrigeren Schwellenwert.")
    st.stop()

# ── Impact analysieren ───────────────────────────────
impact = analyze_impact(shocks, df_target, horizons=horizons)
summary = impact["summary"]
events = impact["events"]

# ── KPIs ─────────────────────────────────────────────
st.markdown("---")
dir_label = {"down": "Einbrüche", "up": "Sprünge", "both": "Extreme Moves"}[direction]
st.markdown(f"### {trigger_ticker} {dir_label} ≥ {threshold}% → Auswirkung auf {target_ticker}")

kpi_cols = st.columns(4)
with kpi_cols[0]:
    st.metric("Shock-Events", f"{n_shocks}")
with kpi_cols[1]:
    if not summary.empty:
        avg_5d = summary.loc[summary["horizon_days"] == 5, "avg_return_pct"]
        val = f"{avg_5d.values[0]:+.2f}%" if len(avg_5d) > 0 else "—"
        st.metric("Ø 5-Tage Reaktion", val)
with kpi_cols[2]:
    if not summary.empty:
        avg_20d = summary.loc[summary["horizon_days"] == 20, "avg_return_pct"]
        val = f"{avg_20d.values[0]:+.2f}%" if len(avg_20d) > 0 else "—"
        st.metric("Ø 20-Tage Reaktion", val)
with kpi_cols[3]:
    if not summary.empty:
        wr_20d = summary.loc[summary["horizon_days"] == 20, "win_rate_pct"]
        val = f"{wr_20d.values[0]:.0f}%" if len(wr_20d) > 0 else "—"
        st.metric("Win-Rate (20T)", val)

# ── Summary-Tabelle ──────────────────────────────────
st.markdown("### 📊 Zusammenfassung nach Horizont")

if not summary.empty:
    display_df = summary.copy()
    display_df.columns = ["Horizont (Tage)", "Ø Rendite %", "Median %",
                           "Std.Abw.", "Win-Rate %", "Max %", "Min %", "Events"]
    st.dataframe(display_df.style.format({
        "Ø Rendite %": "{:+.2f}",
        "Median %": "{:+.2f}",
        "Std.Abw.": "{:.2f}",
        "Win-Rate %": "{:.0f}",
        "Max %": "{:+.2f}",
        "Min %": "{:+.2f}",
    }), use_container_width=True, hide_index=True)

# ── Bar-Chart: Ø Rendite pro Horizont ────────────────
st.markdown("### 📈 Durchschnittliche Reaktion nach Horizont")

if not summary.empty:
    colors = [SE_COLORS["positive"] if v >= 0 else SE_COLORS["negative"]
              for v in summary["avg_return_pct"]]

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=[f"{int(h)}T" for h in summary["horizon_days"]],
        y=summary["avg_return_pct"],
        marker_color=colors,
        text=[f"{v:+.2f}%" for v in summary["avg_return_pct"]],
        textposition="outside",
        textfont=dict(color=SE_COLORS["text_primary"], size=12),
    ))
    fig_bar = apply_se_theme(fig_bar,
                              title=f"{target_ticker} Ø Rendite nach {trigger_ticker} Shock",
                              height=400)
    fig_bar.update_yaxes(title_text="Ø Rendite %")
    fig_bar.update_xaxes(title_text="Horizont")
    st.plotly_chart(fig_bar, use_container_width=True)

# ── Scatter: Trigger-Stärke vs. Reaktion ─────────────
st.markdown("### 🔬 Trigger-Stärke vs. Reaktion")

scatter_horizon = st.selectbox("Horizont für Scatter", horizons, index=min(3, len(horizons) - 1))
ret_col = f"return_{scatter_horizon}d"

if ret_col in events.columns:
    valid_scatter = events.dropna(subset=[ret_col])

    fig_scatter = go.Figure()
    fig_scatter.add_trace(go.Scatter(
        x=valid_scatter["trigger_return_pct"],
        y=valid_scatter[ret_col],
        mode="markers",
        marker=dict(
            size=8,
            color=valid_scatter[ret_col],
            colorscale=[[0, SE_COLORS["negative"]], [0.5, SE_COLORS["text_muted"]], [1, SE_COLORS["positive"]]],
            colorbar=dict(title="Rendite %", tickfont=dict(color=SE_COLORS["text_muted"])),
            line=dict(width=0.5, color=SE_COLORS["grid"]),
        ),
        text=[f"{d.strftime('%Y-%m-%d') if hasattr(d, 'strftime') else d}"
              for d in valid_scatter["shock_date"]],
        hovertemplate=(
            f"Trigger: %{{x:+.1f}}%<br>"
            f"{target_ticker} nach {scatter_horizon}T: %{{y:+.2f}}%<br>"
            "Datum: %{text}<extra></extra>"
        ),
    ))

    # Nulllinien
    fig_scatter.add_hline(y=0, line_dash="dash", line_color=SE_COLORS["text_muted"], line_width=0.5)
    fig_scatter.add_vline(x=0, line_dash="dash", line_color=SE_COLORS["text_muted"], line_width=0.5)

    fig_scatter = apply_se_theme(fig_scatter,
                                  title=f"Trigger vs. {scatter_horizon}-Tage Reaktion",
                                  height=450)
    fig_scatter.update_xaxes(title_text=f"{trigger_ticker} Tagesrendite %")
    fig_scatter.update_yaxes(title_text=f"{target_ticker} Rendite nach {scatter_horizon}T %")
    st.plotly_chart(fig_scatter, use_container_width=True)

# ── Heatmap: Schwelle × Horizont ─────────────────────
st.markdown("### 🗺️ Heatmap: Shock-Stärke × Horizont")

with st.spinner("Berechne Heatmap..."):
    heatmap_thresholds = [2, 3, 5, 7, 10]
    hm_data = shock_heatmap_data(df_trigger, df_target,
                                  thresholds=heatmap_thresholds,
                                  horizons=horizons,
                                  direction=direction)

if not hm_data.empty:
    z_vals = hm_data.values.tolist()
    x_labels = hm_data.columns.tolist()
    y_labels = hm_data.index.tolist()

    fig_hm = go.Figure(data=go.Heatmap(
        z=z_vals,
        x=x_labels,
        y=y_labels,
        colorscale=[[0, SE_COLORS["negative"]], [0.5, SE_COLORS["bg"]], [1, SE_COLORS["positive"]]],
        zmid=0,
        text=[[f"{v:+.2f}%" if not np.isnan(v) else "—" for v in row] for row in z_vals],
        texttemplate="%{text}",
        textfont=dict(size=12, color=SE_COLORS["text_primary"]),
        hovertemplate="Schwelle: %{y}<br>Horizont: %{x}<br>Ø Rendite: %{z:+.2f}%<extra></extra>",
        colorbar=dict(
            title=dict(text="Ø %", font=dict(color=SE_COLORS["text_muted"])),
            tickfont=dict(color=SE_COLORS["text_muted"]),
        ),
    ))

    fig_hm = apply_se_theme(fig_hm,
                             title=f"{trigger_ticker} Shock → {target_ticker} Reaktion",
                             height=400)
    fig_hm.update_xaxes(title_text="Horizont (Tage)")
    fig_hm.update_yaxes(title_text="Shock-Schwelle")
    st.plotly_chart(fig_hm, use_container_width=True)

# ── Event-Liste ──────────────────────────────────────
with st.expander(f"📋 Alle {n_shocks} Shock-Events anzeigen"):
    if not events.empty:
        display_events = events.copy()
        display_events["shock_date"] = pd.to_datetime(display_events["shock_date"]).dt.strftime("%Y-%m-%d")
        display_events = display_events.rename(columns={
            "shock_date": "Datum",
            "trigger_return_pct": f"{trigger_ticker} %",
        })
        for h in horizons:
            col = f"return_{h}d"
            if col in display_events.columns:
                display_events = display_events.rename(columns={col: f"{target_ticker} +{h}T %"})
        display_events = display_events.drop(columns=["target_base_price"], errors="ignore")
        st.dataframe(display_events, use_container_width=True, hide_index=True)

# ── Footer ────────────────────────────────────────────
st.markdown("---")
st.caption(f"Daten: {trigger_ticker} + {target_ticker} · {years_back} Jahre · "
           f"{n_shocks} Events · SeasonAlpha Shock Analyzer")

"""
SeasonAlpha — Spot-Vol Beta Analyse
======================================
SPX vs. VIX: Spot-Volatilitaets-Korrelation, Rolling Beta, Scatter + Regression.
"""

# ── sys.path Fix ──────────────────────────────────────
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

# ── Imports ───────────────────────────────────────────
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, date

from shared.constants import SE_COLORS
from shared.charts import apply_se_theme
from shared.spot_vol_beta import (
    load_spot_vol_data,
    compute_spot_vol_beta,
    classify_beta,
    regime_color,
)
from shared.info_badge import render_info_badge

# ── Page Config ───────────────────────────────────────
st.set_page_config(
    page_title="Spot-Vol Beta — SeasonAlpha",
    page_icon="📉",
    layout="wide",
)

from shared.design import inject_se_css
inject_se_css()


# ══════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### 📉 Spot-Vol Beta")
    st.markdown("---")

    ticker_spot = st.text_input("Spot-Index", value="^GSPC", key="svb_spot").upper().strip()
    ticker_vol = st.text_input("Volatilitäts-Index", value="^VIX", key="svb_vol").upper().strip()

    st.markdown("---")

    rolling_window = st.slider("Rolling Window (Tage)", 20, 252, 60, key="svb_window")
    use_log = st.checkbox("Log-Returns", value=False, key="svb_log")

    st.markdown("---")
    st.subheader("Zeitraum")
    current_year = date.today().year
    start_year = st.slider("Von Jahr", 1990, current_year - 1, max(1990, current_year - 5), key="svb_start")
    end_year = st.slider("Bis Jahr", start_year + 1, current_year, current_year, key="svb_end")

    st.markdown("---")
    st.caption(
        "Spot-Vol Beta misst die Korrelation zwischen "
        "Index-Renditen und Volatilitätsänderungen. "
        "Negatives Beta = typisches 'Fear Gauge' Verhalten."
    )


# ══════════════════════════════════════════════════════
# DATEN LADEN
# ══════════════════════════════════════════════════════

st.markdown("## 📉 Spot-Vol Beta Analyse")
st.caption(f"{ticker_spot} vs. {ticker_vol} | {start_year}–{end_year}")

with st.spinner(f"Lade {ticker_spot} und {ticker_vol}..."):
    raw_df = load_spot_vol_data(ticker_spot, ticker_vol)

if raw_df is None or raw_df.empty:
    st.error(f"Keine Daten für {ticker_spot} und/oder {ticker_vol} gefunden.")
    st.stop()

# Zeitraum filtern
df_filtered = raw_df[
    (raw_df.index.year >= start_year) &
    (raw_df.index.year <= end_year)
].copy()

if len(df_filtered) < 60:
    st.warning("Zu wenig Daten im gewählten Zeitraum.")
    st.stop()

# ══════════════════════════════════════════════════════
# BERECHNUNG
# ══════════════════════════════════════════════════════

with st.spinner("Berechne Spot-Vol Beta..."):
    df_calc, metrics = compute_spot_vol_beta(
        df_filtered,
        rolling_window=rolling_window,
        use_log_returns=use_log,
    )

regime = metrics["regime"]
r_color = regime_color(regime)


# ══════════════════════════════════════════════════════
# METRIKEN
# ══════════════════════════════════════════════════════

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Spot-Vol Beta", f'{metrics["beta"]:.3f}')
m2.metric("R²", f'{metrics["r2"]:.4f}')
m3.metric("Korrelation", f'{metrics["corr"]:.3f}')
m4.metric("Regime", f'{regime}')
m5.metric("Beobachtungen", f'{metrics["n"]:,}')

st.markdown("---")


# ══════════════════════════════════════════════════════
# CHART 1: SPX + Spot-Vol Beta + VIX (3 Subplots)
# ══════════════════════════════════════════════════════

st.subheader(f"{ticker_spot}, Spot-Vol Beta und {ticker_vol}")

from plotly.subplots import make_subplots

fig1 = make_subplots(
    rows=3, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.05,
    subplot_titles=[ticker_spot, "Daily Spot-Vol Beta", ticker_vol],
    row_heights=[0.45, 0.30, 0.25],
)

# Row 1: SPX
fig1.add_trace(go.Scatter(
    x=df_calc.index, y=df_calc["spx_close"],
    mode="lines", name=ticker_spot,
    line=dict(color=SE_COLORS["accent_blue"], width=1.5),
    hovertemplate=f"{ticker_spot}: %{{y:.2f}}<extra></extra>",
), row=1, col=1)

# Row 2: Daily Spot-Vol Beta
daily_beta_valid = df_calc.dropna(subset=["daily_beta"])
# Farbe: gruen wenn negativ (normal), rot wenn positiv (anomal)
daily_colors = [
    SE_COLORS["positive"] if v < 0 else SE_COLORS["negative"]
    for v in daily_beta_valid["daily_beta"]
]
fig1.add_trace(go.Bar(
    x=daily_beta_valid.index, y=daily_beta_valid["daily_beta"],
    marker_color=daily_colors,
    name="Daily Beta",
    hovertemplate="%{x|%d.%m.%Y}: %{y:.4f}<extra></extra>",
), row=2, col=1)

# Referenzlinie
fig1.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.3)", line_width=1, row=2, col=1)

# Row 3: VIX
fig1.add_trace(go.Scatter(
    x=df_calc.index, y=df_calc["vix_close"],
    mode="lines", name=ticker_vol,
    line=dict(color=SE_COLORS["negative"], width=1.2),
    fill="tozeroy", fillcolor="rgba(255,71,87,0.08)",
    hovertemplate=f"{ticker_vol}: %{{y:.2f}}<extra></extra>",
), row=3, col=1)

fig1 = apply_se_theme(
    fig1,
    title=f"{ticker_spot} / Daily Spot-Vol Beta / {ticker_vol} ({start_year}–{end_year})",
    height=650,
)
fig1.update_yaxes(title=ticker_spot, row=1, col=1)
fig1.update_yaxes(title="Beta", row=2, col=1)
fig1.update_yaxes(title=ticker_vol, row=3, col=1)

for ann in fig1.layout.annotations:
    ann.font.color = SE_COLORS["text_muted"]
    ann.font.size = 11

st.plotly_chart(fig1, use_container_width=True)


# ══════════════════════════════════════════════════════
# CHART 2: Scatter + Beta-Fit
# ══════════════════════════════════════════════════════

st.subheader("Spot-Vol Beta (Scatter + Regression)")

fig2 = go.Figure()

# Scatter
valid = df_calc.dropna(subset=["spx_ret", "vix_chg"])
fig2.add_trace(go.Scatter(
    x=valid["spx_ret"], y=valid["vix_chg"],
    mode="markers", name="Beobachtungen",
    marker=dict(
        size=4, opacity=0.4,
        color=SE_COLORS["accent_blue"],
    ),
    hovertemplate="SPX: %{x:.4f}<br>VIX: %{y:.4f}<extra></extra>",
))

# Regressionslinie
x_min = valid["spx_ret"].min()
x_max = valid["spx_ret"].max()
x_line = np.linspace(x_min, x_max, 100)
y_line = metrics["alpha"] + metrics["beta"] * x_line

fig2.add_trace(go.Scatter(
    x=x_line, y=y_line,
    mode="lines", name=f'Beta = {metrics["beta"]:.3f}',
    line=dict(color=r_color, width=2.5),
))

# Nulllinien
fig2.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.2)", line_width=1)
fig2.add_shape(
    type="line", x0=0, x1=0, y0=0, y1=1,
    xref="x", yref="paper",
    line=dict(dash="dot", color="rgba(255,255,255,0.2)", width=1),
)

# "You are here" — aktueller Tag markieren
if len(valid) > 0:
    last_row = valid.iloc[-1]
    last_spx_ret = last_row["spx_ret"]
    last_vix_chg = last_row["vix_chg"]

    fig2.add_trace(go.Scatter(
        x=[last_spx_ret], y=[last_vix_chg],
        mode="markers",
        marker=dict(size=14, color="#F1C40F", symbol="star", line=dict(width=2, color="white")),
        name="Heute",
        hovertemplate=f"HEUTE<br>SPX: {last_spx_ret:.4f}<br>VIX: {last_vix_chg:.4f}<extra></extra>",
    ))

    fig2.add_annotation(
        x=last_spx_ret, y=last_vix_chg,
        text="We are here",
        showarrow=True,
        arrowhead=2,
        arrowcolor="#F1C40F",
        ax=50, ay=-35,
        font=dict(color="#F1C40F", size=11, family="Inter"),
        bordercolor="#F1C40F",
        borderwidth=1,
        borderpad=3,
        bgcolor="rgba(15,25,35,0.85)",
    )

fig2 = apply_se_theme(
    fig2,
    title=f"Spot-Vol Beta: {metrics['beta']:.3f} (R²={metrics['r2']:.4f})",
    height=450,
)
fig2.update_xaxes(title=f"{ticker_spot} Rendite")
fig2.update_yaxes(title=f"{ticker_vol} Änderung")
fig2.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.25, x=0))

st.plotly_chart(fig2, use_container_width=True)

# Beta-Interpretation
if metrics["beta"] < -0.3:
    st.info(
        f'**Beta = {metrics["beta"]:.3f}** — Typisches "Fear Gauge" Verhalten: '
        f'Wenn {ticker_spot} fällt, steigt {ticker_vol} überproportional. '
        f'Die Korrelation beträgt {metrics["corr"]:.3f}.',
        icon="📊",
    )
elif metrics["beta"] < 0.3:
    st.warning(
        f'**Beta = {metrics["beta"]:.3f}** — Schwache Spot-Vol Korrelation. '
        f'Das ist ungewöhnlich und kann auf Regimewechsel hindeuten.',
        icon="⚠️",
    )
else:
    st.error(
        f'**Beta = {metrics["beta"]:.3f}** — Positives Spot-Vol Beta! '
        f'Sehr selten — Volatilität steigt trotz steigender Kurse.',
        icon="🔴",
    )


# ══════════════════════════════════════════════════════
# CHART 3: Rolling Beta
# ══════════════════════════════════════════════════════

st.markdown("---")
st.subheader(f"Rolling Spot-Vol Beta ({rolling_window} Tage)")

fig3 = go.Figure()

rolling_valid = df_calc.dropna(subset=["rolling_beta"])

fig3.add_trace(go.Scatter(
    x=rolling_valid.index, y=rolling_valid["rolling_beta"],
    mode="lines", name=f"{rolling_window}d Beta",
    line=dict(color=SE_COLORS["accent_warm"], width=1.5),
    hovertemplate="%{x|%d.%m.%Y}: Beta = %{y:.3f}<extra></extra>",
))

# Referenzlinien
fig3.add_hline(
    y=metrics["beta"], line_dash="dash",
    line_color=SE_COLORS["accent_blue"], line_width=1,
    annotation=dict(
        text=f'Gesamt-Beta: {metrics["beta"]:.3f}',
        font=dict(color=SE_COLORS["accent_blue"], size=10),
    ),
)
fig3.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.2)", line_width=1)
fig3.add_hline(y=-0.8, line_dash="dot", line_color=SE_COLORS["negative"], line_width=0.8)
fig3.add_hline(y=-0.3, line_dash="dot", line_color=SE_COLORS["accent_warm"], line_width=0.8)

fig3 = apply_se_theme(
    fig3,
    title=f"Rolling {rolling_window}d Spot-Vol Beta",
    height=380,
)
fig3.update_xaxes(title="Datum")
fig3.update_yaxes(title="Beta")

st.plotly_chart(fig3, use_container_width=True)

# Aktueller Rolling-Beta Wert
if not rolling_valid.empty:
    current_rolling = rolling_valid["rolling_beta"].iloc[-1]
    current_regime = classify_beta(current_rolling)
    cr_color = regime_color(current_regime)

    rc1, rc2, rc3 = st.columns(3)
    rc1.metric("Aktuelles Rolling Beta", f"{current_rolling:.3f}")
    rc2.metric("Aktuelles Regime", current_regime)
    rc3.metric(
        "vs. Gesamt-Beta",
        f'{current_rolling - metrics["beta"]:+.3f}',
        delta_color="inverse",
    )


# ══════════════════════════════════════════════════════
# CHART 4: Regime-Wendepunkte (VIX-Extreme + Beta-Stress)
# ══════════════════════════════════════════════════════

st.markdown("---")
st.subheader("Regime-Wendepunkte: Was passiert nach Extremen?")

from shared.spot_vol_beta import analyze_vix_extremes

wpc1, wpc2, wpc3 = st.columns(3)
with wpc1:
    vix_spike_th = st.number_input("VIX Spike-Schwelle", 20.0, 80.0, 30.0, 5.0, key="svb_spike")
with wpc2:
    vix_low_th = st.number_input("VIX Complacency-Schwelle", 8.0, 20.0, 15.0, 1.0, key="svb_low")
with wpc3:
    beta_stress_th = st.number_input("Beta Stress-Schwelle", -3.0, 0.0, -1.0, 0.1, key="svb_bstress")

with st.spinner("Analysiere Regime-Wendepunkte..."):
    extremes = analyze_vix_extremes(
        df_calc.copy(),
        vix_spike_threshold=vix_spike_th,
        vix_low_threshold=vix_low_th,
        beta_stress_threshold=beta_stress_th,
    )

# Tabs fuer die 3 Analysen
wtab1, wtab2, wtab3 = st.tabs([
    f'VIX Spikes (>= {vix_spike_th:.0f})',
    f'VIX Complacency (<= {vix_low_th:.0f})',
    f'Beta Stress (<= {beta_stress_th:.1f})',
])

for wtab, key, color in [
    (wtab1, "vix_spikes", SE_COLORS["negative"]),
    (wtab2, "vix_lows", SE_COLORS["accent"]),
    (wtab3, "beta_stress", SE_COLORS["accent_warm"]),
]:
    with wtab:
        data = extremes[key]
        if data["n"] == 0:
            st.caption("Keine Events im gewählten Zeitraum.")
            continue

        st.markdown(f'**{data["n"]} Events** gefunden: {data["label"]}')

        # Forward-Return Tabelle
        if data.get("stats"):
            fwd_rows = []
            for fd, s in data["stats"].items():
                fwd_rows.append({
                    "Horizont": f"{fd} Tage",
                    "Oe Rendite": f'{s["avg_return"]:+.2f}%',
                    "Median": f'{s["median_return"]:+.2f}%',
                    "Win-Rate": f'{s["win_rate"]:.0f}%',
                    "Max Gewinn": f'{s["max_gain"]:+.2f}%',
                    "Max Verlust": f'{s["max_loss"]:+.2f}%',
                    "n": s["n"],
                })
            st.dataframe(
                pd.DataFrame(fwd_rows),
                use_container_width=True, hide_index=True,
            )

            # Forward-Return Balkendiagramm
            fig_fwd = go.Figure()
            horizonte = [f'{fd}d' for fd in data["stats"].keys()]
            avg_rets = [s["avg_return"] for s in data["stats"].values()]
            win_rates = [s["win_rate"] for s in data["stats"].values()]

            bar_colors = [
                SE_COLORS["positive"] if r >= 0 else SE_COLORS["negative"]
                for r in avg_rets
            ]

            fig_fwd.add_trace(go.Bar(
                x=horizonte, y=avg_rets,
                marker_color=bar_colors,
                text=[f'{r:+.2f}%' for r in avg_rets],
                textposition="outside",
                customdata=win_rates,
                hovertemplate="Horizont: %{x}<br>Oe Rendite: %{y:+.2f}%<br>Win-Rate: %{customdata:.0f}%<extra></extra>",
            ))

            fig_fwd.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.2)", line_width=1)
            fig_fwd = apply_se_theme(
                fig_fwd,
                title=f"SPX Forward Returns nach {data['label']}",
                height=300, show_legend=False,
            )
            fig_fwd.update_yaxes(title="Oe SPX Rendite (%)")
            st.plotly_chart(fig_fwd, use_container_width=True)

        # Event-Liste
        if data.get("events"):
            with st.expander(f"Alle {data['n']} Events anzeigen"):
                events_df = pd.DataFrame(data["events"])
                st.dataframe(events_df, use_container_width=True, hide_index=True, height=300)


# ══════════════════════════════════════════════════════
# HISTORISCHER SPX CHART
# ══════════════════════════════════════════════════════

st.markdown("---")
with st.expander(f"Historischer {ticker_spot} Chart", expanded=False):
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(
        x=df_calc.index, y=df_calc["spx_close"],
        mode="lines",
        line=dict(color=SE_COLORS["accent_blue"], width=1.2),
        fill="tozeroy", fillcolor="rgba(77,159,255,0.05)",
        name=ticker_spot,
        hovertemplate="%{x|%d.%m.%Y}: %{y:.2f}<extra></extra>",
    ))

    fig4 = apply_se_theme(
        fig4,
        title=f"{ticker_spot} ({start_year}–{end_year})",
        height=350,
        show_legend=False,
    )
    fig4.update_yaxes(title="Index")
    st.plotly_chart(fig4, use_container_width=True)


# ══════════════════════════════════════════════════════
# ERKLÄRUNG
# ══════════════════════════════════════════════════════

render_info_badge("spot_vol_beta")
with st.expander("So lesen Sie die Spot-Vol Beta Analyse"):
    st.markdown(f"""
**Was ist Spot-Vol Beta?**

Das Spot-Vol Beta misst den statistischen Zusammenhang zwischen den Renditen
eines Index ({ticker_spot}) und den Änderungen der impliziten Volatilität ({ticker_vol}).

**Interpretation:**
- **Beta < -0.8** (stark negativ): Klassisches "Fear Gauge" — starke inverse Beziehung.
  Wenn Aktien fallen, explodiert die Volatilität. Typisch für Stress-Phasen.
- **Beta -0.3 bis -0.8** (negativ): Normaler Zustand — moderate inverse Beziehung.
- **Beta nahe 0**: Keine klare Beziehung — kann auf Regimewechsel hindeuten.
- **Beta > 0** (positiv): Sehr selten — Volatilität steigt trotz steigender Kurse.

**Rolling Beta:**
Das {rolling_window}-Tage Rolling Beta zeigt wie sich die Beziehung über die Zeit verändert.
Phasen mit stärker negativem Beta deuten auf erhöhte Marktangst hin.

**R² (Bestimmtheitsmaß):**
Zeigt wie viel der VIX-Bewegung durch SPX-Renditen erklärt wird.
R² von 0.5 = 50% der VIX-Bewegung ist durch SPX-Renditen erklärbar.
""")


# ── Disclaimer ──
st.markdown("---")
st.caption(
    "⚠️ _Spot-Vol Beta basiert auf historischen Regressionen. "
    "Die Beziehung ist nicht stationär und kann sich in Krisenzeiten "
    "deutlich verändern. Keine Anlageberatung._"
)

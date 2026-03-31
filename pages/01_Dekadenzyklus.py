# pages/01_Dekadenzyklus.py
# Intra-Dekaden-Saisonalität

import sys, os, pathlib
try:
    _project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
except NameError:
    _project_dir = os.getcwd()
if not os.path.isdir(os.path.join(_project_dir, "shared")):
    for _c in [os.getcwd(), os.path.dirname(os.path.abspath(sys.argv[-1])) if sys.argv else ""]:
        if os.path.isdir(os.path.join(_c, "shared")):
            _project_dir = _c
            break
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

from shared.yahoo_downloader import download_data, preprocess
from shared.calculations_decade import (
    build_decade_data, get_decade_summary_table,
    get_decade_digit, DECADE_COLORS, DECADE_LABELS,
)
from shared.charts import apply_se_theme
from shared.constants import SE_COLORS
from shared.distribution_charts import (
    build_box_plot, build_decade_monthly_heatmap, build_context_panel_data,
)

st.set_page_config(
    page_title="SeasonAlpha – Intra-Decade Seasonality",
    page_icon="📊",
    layout="wide",
)

from shared.design import inject_se_css
from shared.footer import render_footer
inject_se_css()

TEMPLATE = "plotly_dark"
SMOOTHING = 5
CURRENT_YEAR  = datetime.now().year
CURRENT_DIGIT = get_decade_digit(CURRENT_YEAR)

# ── Monatsbeschriftungen für X-Achse ─────────────────────────────────────────
MONTH_TICKS  = [int(i * 21) for i in range(12)]
MONTH_LABELS = ["Jan","Feb","Mär","Apr","Mai","Jun",
                "Jul","Aug","Sep","Okt","Nov","Dez"]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Intra-Decade Seasonality")
    st.markdown("---")

    ticker = st.text_input(
        "Ticker",
        value="^DJI",
        help="Primär für Dow Jones (^DJI) — funktioniert mit jeder langen Zeitreihe",
    ).upper().strip()

    st.markdown("---")
    st.markdown("### Darstellung")

    show_bands = st.checkbox("±1σ Konfidenzband", value=False,
                             help="Zeigt Standardabweichung pro Kohorte")
    show_individual = st.checkbox("Einzeljahre anzeigen", value=False,
                                  help="Alle Einzeljahre dünn im Hintergrund")
    show_current_year = st.checkbox("Aktuelles Jahr hervorheben", value=True,
                                    help="Zeigt das aktuelle Jahr als eigene Linie")

    st.markdown("---")
    st.markdown("### Kohorten ein/ausblenden")
    st.caption("Welche Endziffern im Linien-Chart zeigen?")

    # Toggle-Checkboxen für alle 10 Ziffern — 2 Spalten
    show_digits: dict[int, bool] = {}
    cols = st.columns(2)
    for digit in range(10):
        label = f"x{digit} (aktuell ✨)" if digit == CURRENT_DIGIT else f"x{digit}"
        with cols[digit % 2]:
            show_digits[digit] = st.checkbox(label, value=True, key=f"dec_{digit}")

# ── Daten laden ───────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Lade Kursdaten …")
def load_data(ticker: str) -> pd.DataFrame:
    raw = download_data(ticker)
    if raw is None or len(raw) == 0:
        raise ValueError(f"Keine Daten für '{ticker}'")
    return preprocess(raw)

try:
    df = load_data(ticker)
except Exception as e:
    st.error(f"**Fehler:** {e}")
    st.stop()

# ── Berechnung ────────────────────────────────────────────────────────────────
with st.spinner("Berechne Dekaden-Kohorten …"):
    decade_data = build_decade_data(df)

summary_df = get_decade_summary_table(decade_data)
data_start = df.index[0].year
data_end   = df.index[-1].year
total_years = len([y for y in range(data_start, data_end+1)
                   if len(df[df.index.year == y]) >= 200])

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"## 📊 Intra-Decade Seasonality — {ticker}")
st.caption(
    f"Zeitreihe: **{data_start}–{data_end}** · "
    f"**{total_years} vollständige Jahre** · "
    f"Aktuelles Jahr: **{CURRENT_YEAR}** (X{CURRENT_DIGIT}-Kohorte)"
)

# ══════════════════════════════════════════════════════════════════════════════
# 1. LINIEN-CHART: Ø-Jahresverläufe pro Kohorte
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("### Ø-Jahresverlauf nach Dekaden-Endziffer")

fig = go.Figure()

for digit in range(10):
    if not show_digits.get(digit, True):
        continue
    d = decade_data[digit]
    if d["n"] == 0 or d["avg_curve"] is None:
        continue

    color = DECADE_COLORS[digit]
    is_current = (digit == CURRENT_DIGIT)
    lw = 3.0 if is_current else 1.8

    x = list(range(252))

    # Einzeljahre (dünn, transparent)
    if show_individual:
        for i, (year, curve) in enumerate(zip(d["years"], d["curves"])):
            fig.add_trace(go.Scatter(
                x=x, y=curve,
                mode="lines",
                line=dict(color=color, width=0.6),
                opacity=0.25,
                showlegend=False,
                hoverinfo="skip",
            ))

    # Glättung
    avg = pd.Series(d["avg_curve"]).rolling(SMOOTHING, center=True, min_periods=1).mean().tolist()

    # Konfidenzband
    if show_bands and d["n"] >= 3:
        std = pd.Series(d["std_curve"]).rolling(SMOOTHING, center=True, min_periods=1).mean().tolist()
        upper = [a + s for a, s in zip(avg, std)]
        lower = [a - s for a, s in zip(avg, std)]
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        fill_color = f"rgba({r},{g},{b},0.08)"
        fig.add_trace(go.Scatter(
            x=x + x[::-1],
            y=upper + lower[::-1],
            fill="toself",
            fillcolor=fill_color,
            line=dict(color="rgba(0,0,0,0)"),
            showlegend=False,
            hoverinfo="skip",
        ))

    # Ø-Kurve
    end_val = avg[-1]
    name = f"x{digit} · n={d['n']} · {end_val:+.1f}%"
    if is_current:
        name = f"✨ X{digit} (aktuell) · n={d['n']} · {end_val:+.1f}%"

    fig.add_trace(go.Scatter(
        x=x, y=avg,
        mode="lines",
        name=name,
        line=dict(
            color=color, width=lw,
            dash="solid" if not is_current else "solid",
        ),
        opacity=1.0 if is_current else 0.85,
        hovertemplate=(
            f"<b>X{digit}-Jahre</b> (n={d['n']})<br>"
            "Handelstag %{x}<br>"
            "%{y:+.2f}%<extra></extra>"
        ),
    ))

# ── Aktuelles Jahr hervorheben ──
if show_current_year:
    current_year_df = df[df.index.year == CURRENT_YEAR]
    if len(current_year_df) >= 20:
        closes = current_year_df["Close"].values.astype(float)
        if closes[0] > 0:
            log_curve = (np.log(closes) - np.log(closes[0])) * 100
            n_orig = len(log_curve)
            current_x = np.linspace(0, 251 * n_orig / 252, n_orig).tolist()
            current_y = log_curve.tolist()

            fig.add_trace(go.Scatter(
                x=current_x, y=current_y,
                mode="lines",
                name=f"{CURRENT_YEAR} (aktuell)",
                line=dict(color="#F1C40F", width=3, dash="solid"),
                hovertemplate=(
                    f"<b>{CURRENT_YEAR}</b><br>"
                    "Handelstag %{x:.0f}<br>"
                    "%{y:+.2f}%<extra></extra>"
                ),
            ))

fig.add_hline(y=0, line_dash="dash",
              line_color="rgba(255,255,255,0.25)", line_width=1)

fig = apply_se_theme(fig, title="", height=500)

st.plotly_chart(fig, use_container_width=True)

# ── Perzentil-Statusbar ──────────────────────────────────────────────────────
if show_current_year:
    from shared.percentile_bar import render_percentile_bar
    d_cur = decade_data[CURRENT_DIGIT]
    if d_cur["n"] >= 5 and len(current_year_df) >= 20:
        _cur_return = float(log_curve[-1]) if 'log_curve' in dir() else None
        if _cur_return is not None:
            _hist_returns = d_cur["returns"] if d_cur["returns"] else []
            if len(_hist_returns) >= 5:
                render_percentile_bar(
                    current_value=_cur_return,
                    hist_values=_hist_returns,
                    label=f"X{CURRENT_DIGIT}-Kohorte · {ticker} {CURRENT_YEAR}",
                )

# ══════════════════════════════════════════════════════════════════════════════
# 2. KONTEXT-PANEL: Aktuelles Jahr (kompakte Karten)
# ══════════════════════════════════════════════════════════════════════════════

d_current = decade_data[CURRENT_DIGIT]
if d_current["n"] >= 2:
    with st.expander(f"🎯 X{CURRENT_DIGIT}-Kohorte — Einordnung {CURRENT_YEAR}", expanded=True):
        groups_all = {
            f"x{digit}": decade_data[digit]["returns"]
            for digit in range(10)
            if decade_data[digit]["n"] > 0
        }
        ctx = build_context_panel_data(groups_all, f"x{CURRENT_DIGIT}", "Jahr")

        avg_clr = "#34d399" if ctx["mean"] >= 0 else "#f87171"
        med_clr = "#34d399" if ctx["median"] >= 0 else "#f87171"
        _cards = [
            ("Kohorte", f"x{CURRENT_DIGIT}-Jahre", "#e2e8f0"),
            ("Ø Rendite", f"{ctx['mean']:+.2f}%", avg_clr),
            ("Median", f"{ctx['median']:+.2f}%", med_clr),
            ("Win-Rate", f"{ctx['win_rate']:.0f}%", "#e2e8f0"),
            ("Volatilität (σ)", f"{ctx['std']:.2f}%", "#e2e8f0"),
        ]
        _cards_html = "".join(
            f'<div style="flex:1; min-width:100px; background:rgba(15,19,24,0.6);'
            f'border:1px solid rgba(255,255,255,0.07); border-radius:8px;'
            f'padding:10px 12px; text-align:center;">'
            f'<div style="font-size:10px; color:#64748b; margin-bottom:4px;">{lbl}</div>'
            f'<div style="font-size:14px; font-weight:700; color:{clr};">{val}</div>'
            f'</div>'
            for lbl, val, clr in _cards
        )
        st.markdown(
            f'<div style="display:flex; gap:8px; margin:4px 0 8px 0;">{_cards_html}</div>',
            unsafe_allow_html=True)

        rating = ctx.get("rating", "—")
        st.markdown(
            f"<div style='font-size:12px; color:#94a3b8; line-height:1.6;'>"
            f"<b style='color:#cbd5e1;'>Historische Einordnung:</b> {rating}<br>"
            f"Beste X{CURRENT_DIGIT}-Jahr: <b style='color:#34d399;'>{ctx.get('best', 0):+.1f}%</b> · "
            f"Schlechteste: <b style='color:#f87171;'>{ctx.get('worst', 0):+.1f}%</b> · "
            f"n = {ctx['n']} Jahre ({', '.join(str(y) for y in sorted(d_current['years']))})"
            f"</div>",
            unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 3. BALKEN-CHART: Ø-Jahresrendite pro Kohorte
# ══════════════════════════════════════════════════════════════════════════════

with st.expander("📊 Ø-Jahresrendite nach Dekaden-Endziffer", expanded=True):
    bar_x      = []
    bar_y      = []
    bar_colors = []
    bar_text   = []
    bar_hover  = []

    for digit in range(10):
        d = decade_data[digit]
        bar_x.append(f"x{digit}")
        val = d["avg_return"] if d["n"] > 0 else 0.0
        bar_y.append(round(val, 2) if val is not None else 0.0)

        if val is not None and val >= 0:
            bar_colors.append("#2ECC71")
        else:
            bar_colors.append("#E74C3C")

        is_current = (digit == CURRENT_DIGIT)
        wr  = d["win_rate"]  if d["n"] > 0 else None
        n   = d["n"]
        vol = d["volatility"] if d["n"] > 0 else None
        suffix = " ✨ aktuell" if is_current else ""
        bar_text.append(f"{val:+.1f}%" if val is not None else "—")
        bar_hover.append(
            f"<b>X{digit}-Jahre{suffix}</b><br>"
            f"Ø Rendite: {val:+.2f}%<br>"
            f"Win-Rate: {wr:.0f}%<br>"
            f"Volatilität: {vol:.1f}%<br>"
            f"n={n} Jahre<extra></extra>"
            if val is not None else f"<b>X{digit}-Jahre</b><br>Keine Daten<extra></extra>"
        )

    fig2 = go.Figure(go.Bar(
        x=bar_x,
        y=bar_y,
        marker_color=bar_colors,
        marker_opacity=0.88,
        text=bar_text,
        textposition="outside",
        customdata=list(range(10)),
        hovertemplate=bar_hover,
    ))

    fig2.add_hline(y=0, line_dash="dash",
                   line_color="rgba(255,255,255,0.25)", line_width=1)

    # "We are here!" Marker
    from shared.we_are_here import annotation as wah_annotation, rect as wah_rect
    current_bar_val = bar_y[CURRENT_DIGIT]
    fig2.add_annotation(**wah_annotation(
        x_val=f"x{CURRENT_DIGIT}",
        y_val=current_bar_val,
        above=current_bar_val >= 0,
    ))
    fig2.add_shape(**wah_rect(
        x0=CURRENT_DIGIT - 0.45, x1=CURRENT_DIGIT + 0.45,
        y0=0, y1=current_bar_val,
    ))

    fig2 = apply_se_theme(fig2, title="", height=380)
    st.plotly_chart(fig2, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# 4. ANOMALIE-RADAR (KI)
# ══════════════════════════════════════════════════════════════════════════════

with st.expander("🔬 Anomalie-Radar (KI)", expanded=True):
    try:
        from shared.anomaly_engine import compute_ticker_anomaly_score
        with st.spinner("Anomalie-Radar berechnet..."):
            radar = compute_ticker_anomaly_score(df, lookback_days=10)
        if "error" not in radar:
            r_score = radar["anomaly_score"]
            if r_score >= 70:
                r_icon, r_label, r_clr = "🔴", "Stark anomal", "#f87171"
            elif r_score >= 40:
                r_icon, r_label, r_clr = "🟡", "Leicht anomal", "#fbbf24"
            else:
                r_icon, r_label, r_clr = "🟢", "Normal", "#34d399"

            cur_ret_clr = "#34d399" if radar["current_return"] >= 0 else "#f87171"
            hist_clr = "#34d399" if radar["historical_avg"] >= 0 else "#f87171"
            _ar_cards = [
                ("Anomalie-Score", f"{r_score:.0f}/100", r_clr),
                ("Status", f"{r_icon} {r_label}", r_clr),
                ("Aktuelle 10d-Rendite", f'{radar["current_return"]:+.2f}%', cur_ret_clr),
                ("Historischer Ø", f'{radar["historical_avg"]:+.2f}%', hist_clr),
            ]
            _ar_html = "".join(
                f'<div style="flex:1; min-width:100px; background:rgba(15,19,24,0.6);'
                f'border:1px solid rgba(255,255,255,0.07); border-radius:8px;'
                f'padding:10px 12px; text-align:center;">'
                f'<div style="font-size:10px; color:#64748b; margin-bottom:4px;">{lbl}</div>'
                f'<div style="font-size:14px; font-weight:700; color:{clr};">{val}</div>'
                f'</div>'
                for lbl, val, clr in _ar_cards
            )
            st.markdown(
                f'<div style="display:flex; gap:8px; margin:4px 0 8px 0;">{_ar_html}</div>'
                f'<div style="font-size:11px; color:#64748b; text-align:center;">'
                f'Isolation Forest vergleicht die letzten 10 Handelstage mit '
                f'{radar["n_comparisons"]} historischen Fenstern am gleichen Kalenderzeitpunkt.</div>',
                unsafe_allow_html=True)
        else:
            st.caption(radar["error"])
    except Exception as _e:
        st.caption(f"Anomalie-Radar nicht verfügbar: {_e}")

# ══════════════════════════════════════════════════════════════════════════════
# 5. DATENTABELLE
# ══════════════════════════════════════════════════════════════════════════════

with st.expander("📋 Übersicht nach Kohorte", expanded=False):
    def _color_val(v):
        if not isinstance(v, (int, float)) or pd.isna(v):
            return ""
        if v > 0:
            return "color: #2ECC71; font-weight: bold"
        elif v < 0:
            return "color: #E74C3C; font-weight: bold"
        return ""

    display_df = summary_df.drop(columns=["Ziffer"]).reset_index(drop=True)
    _digit_map = summary_df["Ziffer"].reset_index(drop=True)

    def _highlight_current(row):
        digit = _digit_map.loc[row.name]
        if digit == CURRENT_DIGIT:
            return ["background-color: rgba(241,196,15,0.15)"] * len(row)
        return [""] * len(row)

    styled = (
        display_df.style
        .apply(_highlight_current, axis=1, subset=None)
        .applymap(_color_val, subset=["Ø Rendite %", "Median %", "Win-Rate %"])
        .format({
            "Ø Rendite %":    lambda v: f"{v:+.2f}%" if pd.notna(v) else "—",
            "Median %":       lambda v: f"{v:+.2f}%" if pd.notna(v) else "—",
            "Win-Rate %":     lambda v: f"{v:.1f}%"  if pd.notna(v) else "—",
            "Volatilität %":  lambda v: f"{v:.2f}%"  if pd.notna(v) else "—",
        })
    )

    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Kohorte":        st.column_config.TextColumn("Kohorte", width="small"),
            "Anzahl Jahre":   st.column_config.NumberColumn("n", width="small"),
            "Ø Rendite %":    st.column_config.TextColumn("Ø Rendite", width="small"),
            "Median %":       st.column_config.TextColumn("Median", width="small"),
            "Win-Rate %":     st.column_config.TextColumn("Win-Rate", width="small"),
            "Volatilität %":  st.column_config.TextColumn("Volatilität", width="small"),
            "Jahre":          st.column_config.TextColumn("Jahre in Kohorte", width="large"),
        },
    )

# ══════════════════════════════════════════════════════════════════════════════
# 6. HEATMAP: Dekade × Monat
# ══════════════════════════════════════════════════════════════════════════════

with st.expander("🗓️ Ø Monatsrendite nach Dekade", expanded=True):
    fig_heat = build_decade_monthly_heatmap(df, ticker)
    st.plotly_chart(fig_heat, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# 7. BOX-PLOT: Rendite-Verteilung pro Kohorte
# ══════════════════════════════════════════════════════════════════════════════

with st.expander("📦 Rendite-Verteilung nach Kohorte (Box-Plot)", expanded=False):
    groups = {
        f"x{digit}": decade_data[digit]["returns"]
        for digit in range(10)
        if decade_data[digit]["n"] >= 2
    }
    if groups:
        fig_box = build_box_plot(
            groups=groups,
            colors=DECADE_COLORS,
            title=f"{ticker} — Jahresrenditen nach Dekaden-Endziffer",
            x_title="Dekaden-Endziffer",
            y_title="Log-Rendite (%)",
            current_key=f"x{CURRENT_DIGIT}",
        )
        st.plotly_chart(fig_box, use_container_width=True)

        st.markdown(
            "<div style='font-size:11px; color:#64748b; line-height:1.6;'>"
            "<b style='color:#94a3b8;'>So lesen Sie Box-Plots:</b> "
            "Kasten = mittlere 50% (25.-75. Perzentil). "
            "Linie = Median. Antennen = 1.5× IQR. "
            "Punkte = Ausreißer (Crash-/Boom-Jahre)."
            "</div>",
            unsafe_allow_html=True)

# ── Methodik ──────────────────────────────────────────────────────────────────
with st.expander("ℹ️ Methodik"):
    st.markdown(f"""
    **Ticker:** {ticker}
    **Datenzeitraum:** {data_start}–{data_end} ({total_years} vollständige Jahre)
    **Normierung:** Erster Handelstag jedes Jahres = 0% (Log-Returns)
    **Interpolation:** Jede Jahreskurve wird auf 252 Handelstage normiert (lineare Interpolation)
    **Mindestlänge:** Jahre mit weniger als 200 Handelstagen werden ausgeschlossen
    **Aktuelle Kohorte:** {CURRENT_YEAR} → X{CURRENT_DIGIT} (gelb markiert)
    **Glättung:** 5-Tage zentrierter Moving Average auf Ø-Kurve
    """)

render_footer()

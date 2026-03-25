"""
SeasonalEdge - Weekday Performance
====================================
Wochentags-Performance (Mo-Fr) mit verschiedenen Rendite-Berechnungen,
Praesidentenzyklus-Filter und Monat x Wochentag Heatmap.
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

st.set_page_config(page_title="Wochentagseffekt Aktien & ETFs – SeasonAlpha", page_icon="📅", layout="wide")

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

from shared.constants import (
    DEFAULT_TICKER, DEFAULT_YEARS, MONTH_NAMES_DE, CYCLE_COLORS,
    SE_COLORS, SE_HEATMAP_COLORSCALE, SE_HEATMAP_TEXT_COLOR,
)
from shared.data import download_data
from shared.charts import apply_se_theme, apply_se_heatmap_theme
from shared.calculations import get_presidential_cycle_year

from shared.design import inject_se_css
inject_se_css()


# ══════════════════════════════════════════════════════════════
# KONSTANTEN
# ══════════════════════════════════════════════════════════════

WEEKDAY_LABELS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]
WEEKDAY_LABELS_SHORT = ["Mo", "Di", "Mi", "Do", "Fr"]

RETURN_MODES = {
    "Close → Close (t0 → t1)": {
        "desc": "Schlusskurs heute vs. Schlusskurs morgen",
        "calc": lambda df: (df["Close"].shift(-1) / df["Close"] - 1) * 100
    },
    "Close → Open (t0 → t1)": {
        "desc": "Schlusskurs heute vs. Eröffnung morgen (Overnight)",
        "calc": lambda df: (df["Open"].shift(-1) / df["Close"] - 1) * 100
    },
    "Open → Close (t0)": {
        "desc": "Eröffnung vs. Schluss am selben Tag (Intraday)",
        "calc": lambda df: (df["Close"] / df["Open"] - 1) * 100
    },
    "Open → Close (t0 → t1)": {
        "desc": "Eröffnung heute vs. Schluss morgen",
        "calc": lambda df: (df["Close"].shift(-1) / df["Open"] - 1) * 100
    },
}


# ══════════════════════════════════════════════════════════════
# BERECHNUNG
# ══════════════════════════════════════════════════════════════

def calculate_weekday_stats(df, return_mode, years_back,
                            filter_mode="Kein Filter",
                            sma_days=200, rsi_days=14, rsi_threshold=30,
                            cycle_filter=None):
    """
    Berechne Weekday-Performance mit waehlbarem Rendite-Modus und Filtern.

    Args:
        df: Raw DataFrame mit Open, Close, High, Low (DatetimeIndex)
        return_mode: Key aus RETURN_MODES
        years_back: Anzahl Jahre Lookback
        filter_mode: "Kein Filter", "Trendfilter (SMA)", "OBOS-Filter (RSI)"
        sma_days: Tage fuer SMA-Berechnung
        rsi_days: Tage fuer RSI-Berechnung
        rsi_threshold: RSI-Schwelle (kaufen wenn RSI darunter)
        cycle_filter: Liste von Praesidentenzyklus-Labels oder None

    Returns:
        dict mit by_weekday, by_month_weekday, filtered_count, total_count
    """
    df = df.copy()

    # ── Zeitraum filtern ──
    cutoff = df.index.max() - pd.DateOffset(years=years_back)
    df = df[df.index >= cutoff]

    if len(df) < 20:
        return None

    # ── Praesidentenzyklus-Filter ──
    if cycle_filter:
        df["_cycle"] = df.index.year.map(get_presidential_cycle_year)
        df = df[df["_cycle"].isin(cycle_filter)]
        df = df.drop(columns=["_cycle"])
        if len(df) < 20:
            return None

    # ── Rendite berechnen ──
    df["wd_return"] = RETURN_MODES[return_mode]["calc"](df)

    # ── Wochentag und Monat ──
    df["weekday"] = df.index.weekday  # 0=Mo, 4=Fr
    df["month"] = df.index.month

    # ── Filter anwenden ──
    df["filter_pass"] = True
    total_count = len(df)

    if filter_mode == "Trendfilter (SMA)":
        df["sma"] = df["Close"].rolling(sma_days, min_periods=sma_days).mean()
        df["filter_pass"] = df["Close"].shift(1) > df["sma"].shift(1)

    elif filter_mode == "OBOS-Filter (RSI)":
        delta = df["Close"].diff()
        gain = delta.where(delta > 0, 0.0).rolling(rsi_days).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(rsi_days).mean()
        rs = gain / loss.replace(0, np.nan)
        df["rsi"] = 100 - (100 / (1 + rs))
        df["filter_pass"] = df["rsi"].shift(1) < rsi_threshold

    # Nur Wochentage Mo-Fr und gueltige Returns
    df = df[(df["weekday"] <= 4) & df["wd_return"].notna()]

    # Gefilterte Daten
    df_filtered = df[df["filter_pass"]].copy()
    filtered_count = len(df_filtered)

    if filtered_count < 10:
        return None

    # ── Statistik pro Wochentag ──
    by_weekday = {}
    for wd in range(5):
        subset = df_filtered[df_filtered["weekday"] == wd]["wd_return"]
        if len(subset) == 0:
            by_weekday[wd] = {"avg": 0, "median": 0, "std": 0, "count": 0,
                              "win_rate": 0, "returns": []}
            continue

        wins = (subset > 0).sum()
        by_weekday[wd] = {
            "avg": subset.mean(),
            "median": subset.median(),
            "std": subset.std(),
            "count": len(subset),
            "win_rate": wins / len(subset) * 100,
            "returns": subset.tolist()
        }

    # ── Statistik pro Monat x Wochentag ──
    by_month_weekday = {}
    for month in range(1, 13):
        for wd in range(5):
            subset = df_filtered[(df_filtered["month"] == month) &
                                 (df_filtered["weekday"] == wd)]["wd_return"]
            if len(subset) == 0:
                by_month_weekday[(month, wd)] = {"avg": 0, "count": 0, "win_rate": 0}
                continue

            wins = (subset > 0).sum()
            by_month_weekday[(month, wd)] = {
                "avg": subset.mean(),
                "count": len(subset),
                "win_rate": wins / len(subset) * 100
            }

    return {
        "by_weekday": by_weekday,
        "by_month_weekday": by_month_weekday,
        "filtered_count": filtered_count,
        "total_count": total_count
    }


# ══════════════════════════════════════════════════════════════
# CHARTS
# ══════════════════════════════════════════════════════════════

def build_weekday_bar_chart(stats, ticker, return_mode):
    """Balkendiagramm: Ø Rendite + Win Rate pro Wochentag."""

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Ø Tagesrendite (%)", "Win Rate (%)"),
        horizontal_spacing=0.12
    )

    wd_data = stats["by_weekday"]
    avgs = [wd_data[wd]["avg"] for wd in range(5)]
    win_rates = [wd_data[wd]["win_rate"] for wd in range(5)]
    counts = [wd_data[wd]["count"] for wd in range(5)]

    # Farben: SE positiv/negativ
    bar_colors = [SE_COLORS["positive"] if v >= 0 else SE_COLORS["negative"] for v in avgs]

    # ── Rendite-Balken ──
    fig.add_trace(
        go.Bar(
            x=WEEKDAY_LABELS,
            y=avgs,
            marker_color=bar_colors,
            text=[f"{v:+.3f}%<br>n={c}" for v, c in zip(avgs, counts)],
            textposition="outside",
            textfont=dict(size=11),
            hovertemplate="<b>%{x}</b><br>Ø Rendite: %{y:+.4f}%<extra></extra>",
            showlegend=False
        ),
        row=1, col=1
    )

    # ── Win Rate Balken ──
    wr_colors = [SE_COLORS["positive"] if v >= 50 else SE_COLORS["negative"] for v in win_rates]
    fig.add_trace(
        go.Bar(
            x=WEEKDAY_LABELS,
            y=win_rates,
            marker_color=wr_colors,
            text=[f"{v:.1f}%" for v in win_rates],
            textposition="outside",
            textfont=dict(size=11),
            hovertemplate="<b>%{x}</b><br>Win Rate: %{y:.1f}%<extra></extra>",
            showlegend=False
        ),
        row=1, col=2
    )

    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)", row=1, col=1)
    fig.add_hline(y=50, line_dash="dash", line_color="rgba(255,255,255,0.3)", row=1, col=2)

    mode_short = return_mode.split("(")[0].strip()
    fig = apply_se_theme(fig, title=f"{ticker} — Weekday Performance · {mode_short}", height=380)

    fig.update_yaxes(tickformat="+.3f", ticksuffix="%", row=1, col=1,
                     gridcolor="rgba(255,255,255,0.06)")
    fig.update_yaxes(range=[0, 100], ticksuffix="%", row=1, col=2,
                     gridcolor="rgba(255,255,255,0.06)")

    return fig


def build_heatmap(stats, ticker):
    """Heatmap: Monat x Wochentag (Ø Rendite, farbcodiert).
    Nutzt das zentrale SE Heatmap-Design (wie Dekadenzyklus).
    Aktueller Monat + Wochentag wird mit gelbem Rahmen markiert.
    """

    mwd = stats["by_month_weekday"]
    now = datetime.now()
    current_month = now.month       # 1-12
    current_weekday = now.weekday() # 0=Mo, 4=Fr

    # Matrix aufbauen: Zeilen = Monate, Spalten = Wochentage
    z_values = []
    hover_texts = []

    for month in range(1, 13):
        row_z = []
        row_hover = []
        for wd in range(5):
            data = mwd.get((month, wd), {"avg": 0, "count": 0, "win_rate": 0})
            row_z.append(data["avg"])
            row_hover.append(
                f"<b>{MONTH_NAMES_DE[month-1]} · {WEEKDAY_LABELS[wd]}</b><br>"
                f"Ø Rendite: {data['avg']:+.3f}%<br>"
                f"Win Rate: {data['win_rate']:.0f}%<br>"
                f"n = {data['count']}"
            )
        z_values.append(row_z)
        hover_texts.append(row_hover)

    z_arr = np.array(z_values)

    fig = go.Figure(go.Heatmap(
        z=z_arr,
        x=WEEKDAY_LABELS_SHORT,
        y=MONTH_NAMES_DE,
        colorscale=SE_HEATMAP_COLORSCALE,
        zmid=0,
        text=np.round(z_arr, 2),
        texttemplate="%{text:+.2f}%",
        textfont=dict(size=10, color=SE_HEATMAP_TEXT_COLOR),
        hovertext=hover_texts,
        hovertemplate="%{hovertext}<extra></extra>",
        colorbar=dict(
            title=dict(text="Ø %", font=dict(color=SE_COLORS["text_muted"])),
            ticksuffix="%",
            tickformat="+.2f",
            tickfont=dict(color=SE_COLORS["text_muted"]),
        ),
    ))

    fig = apply_se_heatmap_theme(fig, title=f"{ticker} — Monat × Wochentag Heatmap", height=480)
    fig.update_xaxes(side="bottom", type="category")
    fig.update_yaxes(autorange="reversed", type="category")

    # ── Gelber Rahmen um aktuelle Zelle (Monat + Wochentag) ──
    if 0 <= current_weekday <= 4:
        # x-Index = Wochentag (0-4), y-Index = Monat-1 (0-11)
        fig.add_shape(
            type="rect",
            x0=current_weekday - 0.5, x1=current_weekday + 0.5,
            y0=current_month - 1 - 0.5, y1=current_month - 1 + 0.5,
            line=dict(color="#FFD700", width=3.5),
            fillcolor="rgba(0,0,0,0)",
            layer="above",
        )

    return fig


# ══════════════════════════════════════════════════════════════
# STREAMLIT UI
# ══════════════════════════════════════════════════════════════

def main():
    with st.sidebar:
        st.markdown("## 📅 Weekday Performance")
        st.markdown("---")

        ticker = st.text_input("Ticker", value=DEFAULT_TICKER, key="wd_ticker").upper().strip()

        years_back = st.slider("Analyse-Zeitraum (Jahre)", 1, 30, 10, key="wd_years")

        st.markdown("---")
        st.markdown("### Rendite-Berechnung")

        return_mode = st.radio(
            "Modus",
            options=list(RETURN_MODES.keys()),
            index=0,
            help="Welche Kurse werden fuer die Rendite-Berechnung verwendet?"
        )
        st.caption(f"_{RETURN_MODES[return_mode]['desc']}_")

        st.markdown("---")
        st.markdown("### Filter")

        filter_mode = st.radio(
            "Einstiegsfilter",
            ["Kein Filter", "Trendfilter (SMA)", "OBOS-Filter (RSI)"],
            index=0,
            help="Filtert Tage heraus, die nicht zur Bedingung passen"
        )

        sma_days = 200
        rsi_days = 14
        rsi_threshold = 30

        if filter_mode == "Trendfilter (SMA)":
            sma_days = st.slider("SMA Periode (Tage)", 20, 400, 200,
                                 help="Nur kaufen wenn Close t-1 > SMA")

        elif filter_mode == "OBOS-Filter (RSI)":
            rsi_days = st.slider("RSI Periode (Tage)", 5, 30, 14)
            rsi_threshold = st.slider("RSI Schwelle (kaufen wenn darunter)", 10, 50, 30,
                                      help="Nur kaufen wenn RSI t-1 < Schwelle")

        st.markdown("---")
        st.markdown("### Praesidentenzyklus")
        cycle_filter = st.multiselect(
            "Zyklusjahre filtern",
            options=list(CYCLE_COLORS.keys()),
            default=None, key="wd_cycle",
            help="Nur Jahre mit bestimmtem Zyklusjahr beruecksichtigen (leer = alle)"
        )

    # ── Daten laden ───────────────────────────────────
    with st.spinner(f"Lade {ticker} Daten..."):
        raw_df = download_data(ticker)

    if raw_df is None or raw_df.empty:
        st.error(f"Keine Daten fuer '{ticker}' gefunden.")
        return

    # ── Berechnung ────────────────────────────────────
    stats = calculate_weekday_stats(
        raw_df, return_mode, years_back,
        filter_mode, sma_days, rsi_days, rsi_threshold,
        cycle_filter=cycle_filter if cycle_filter else None
    )

    if stats is None:
        st.warning("Nicht genuegend Daten fuer die Analyse.")
        return

    # ── Zyklusfilter-Info ──────────────────────────────
    if cycle_filter:
        cycle_info = ", ".join([c.split("(")[1].rstrip(")") for c in cycle_filter])
        st.info(f"**Zyklusfilter aktiv:** {cycle_info}")

    # ── Filter-Info ───────────────────────────────────
    if filter_mode != "Kein Filter":
        pct = stats["filtered_count"] / stats["total_count"] * 100
        st.info(
            f"**Filter aktiv:** {filter_mode} · "
            f"{stats['filtered_count']} von {stats['total_count']} Tagen passieren den Filter ({pct:.0f}%)"
        )

    # ── Balkendiagramm ────────────────────────────────
    bar_fig = build_weekday_bar_chart(stats, ticker, return_mode)
    st.plotly_chart(bar_fig, use_container_width=True)

    # ── Signifikanztest (optional) ────────────────────
    from shared.significance_gauge import run_significance_test, render_significance_section
    sig_groups = {WEEKDAY_LABELS[wd]: stats["by_weekday"][wd]["returns"]
                  for wd in range(5) if stats["by_weekday"][wd]["returns"]}
    sig_results = run_significance_test(sig_groups)
    render_significance_section(sig_results,
        expander_title="📊 Statistische Signifikanz der Wochentags-Effekte",
        cols_per_row=5,
        sort_order=WEEKDAY_LABELS)

    # ── Detailtabelle ─────────────────────────────────
    st.markdown("#### 📋 Statistik pro Wochentag")

    wd_rows = []
    for wd in range(5):
        d = stats["by_weekday"][wd]
        wd_rows.append({
            "Wochentag": WEEKDAY_LABELS[wd],
            "Ø Rendite": f"{d['avg']:+.4f}%",
            "Median": f"{d['median']:+.4f}%",
            "Std.Abw.": f"{d['std']:.4f}%",
            "Win Rate": f"{d['win_rate']:.1f}%",
            "Anzahl": d["count"]
        })

    st.dataframe(pd.DataFrame(wd_rows), use_container_width=True, hide_index=True)

    # ── Heatmap Monat x Wochentag ────────────────────
    st.markdown("---")
    st.markdown("#### 🗓️ Monat × Wochentag Heatmap")

    heatmap_fig = build_heatmap(stats, ticker)
    st.plotly_chart(heatmap_fig, use_container_width=True)

    # ── Top / Flop Kombinationen ──────────────────────
    st.markdown("---")

    mwd = stats["by_month_weekday"]
    combos = []
    for (month, wd), data in mwd.items():
        if data["count"] >= 3:
            combos.append({
                "Monat": MONTH_NAMES_DE[month - 1],
                "Wochentag": WEEKDAY_LABELS[wd],
                "Ø Rendite": data["avg"],
                "Win Rate": data["win_rate"],
                "n": data["count"]
            })

    if combos:
        sorted_combos = sorted(combos, key=lambda x: x["Ø Rendite"], reverse=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🟢 Top 10 beste Kombinationen")
            top_df = pd.DataFrame(sorted_combos[:10])
            top_df["Ø Rendite"] = top_df["Ø Rendite"].apply(lambda x: f"{x:+.3f}%")
            top_df["Win Rate"] = top_df["Win Rate"].apply(lambda x: f"{x:.0f}%")
            st.dataframe(top_df, use_container_width=True, hide_index=True)

        with col2:
            st.markdown("#### 🔴 Top 10 schlechteste Kombinationen")
            flop_df = pd.DataFrame(sorted_combos[-10:][::-1])
            flop_df["Ø Rendite"] = flop_df["Ø Rendite"].apply(lambda x: f"{x:+.3f}%")
            flop_df["Win Rate"] = flop_df["Win Rate"].apply(lambda x: f"{x:.0f}%")
            st.dataframe(flop_df, use_container_width=True, hide_index=True)

    # ── Dateninfo ─────────────────────────────────────
    with st.expander("ℹ️ Dateninfo"):
        cycle_str = ", ".join(cycle_filter) if cycle_filter else "Kein Filter"
        st.markdown(f"""
        **Ticker:** {ticker}
        **Zeitraum:** Letzte {years_back} Jahre
        **Rendite-Modus:** {return_mode}
        **Beschreibung:** {RETURN_MODES[return_mode]['desc']}
        **Filter:** {filter_mode}
        **Praesidentenzyklus:** {cycle_str}
        **Handelstage analysiert:** {stats['filtered_count']}
        """)


# ══════════════════════════════════════════════════════════════
# START
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    main()

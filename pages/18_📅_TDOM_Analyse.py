"""
SeasonalEdge — TDoM (Trading Day of the Month) Analyse
========================================================
3 Strategien × 2 Richtungen × Monatsfilter × Multi-Day Ranges.
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
from datetime import datetime

from shared.constants import DEFAULT_TICKER, SE_COLORS, MONTH_NAMES_DE
from shared.data import download_data, preprocess
from shared.charts import apply_se_theme, apply_se_heatmap_theme
from shared.tdom_analysis import (
    build_tdom_stats, build_tdom_month_matrix,
    calc_tdom_range_return, calc_range_stats,
    build_tdom_year_breakdown,
    STRATEGY_LABELS, DIRECTION_LABELS,
)

# ── Page Config ───────────────────────────────────────
st.set_page_config(
    page_title="TDoM Analyse — SeasonalEdge",
    page_icon="📅",
    layout="wide",
)

from shared.design import inject_se_css
inject_se_css()


# ══════════════════════════════════════════════════════
# CHART-FUNKTIONEN
# ══════════════════════════════════════════════════════

def build_tdom_bar_chart(
    stats: pd.DataFrame, ticker: str, strategy: str, direction: str,
) -> go.Figure:
    """Balkendiagramm: Ø Rendite pro TDoM."""
    colors = [
        SE_COLORS["positive"] if r > 0 else SE_COLORS["negative"]
        for r in stats["avg_return"]
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[str(t) for t in stats.index],
        y=stats["avg_return"],
        marker_color=colors,
        customdata=np.column_stack([
            stats["win_rate"], stats["median_return"],
            stats["count"], stats["std_dev"],
        ]),
        hovertemplate=(
            "<b>TDoM %{x}</b><br>"
            "Ø Rendite: %{y:+.4f}%<br>"
            "Win-Rate: %{customdata[0]:.1f}%<br>"
            "Median: %{customdata[1]:+.4f}%<br>"
            "Trades: %{customdata[2]:.0f}<br>"
            "Std-Dev: %{customdata[3]:.4f}%"
            "<extra></extra>"
        ),
    ))

    fig.add_hline(y=0, line_color=SE_COLORS["zero_line"], line_width=1)

    dir_label = "Vorwärts" if direction == "forward" else "Rückwärts"
    strat_short = strategy.replace("_", " ").title()
    fig = apply_se_theme(
        fig,
        title=f"{ticker} — TDoM Ø Rendite ({dir_label} · {strat_short})",
        height=400,
    )
    fig.update_xaxes(title="Trading Day of Month", dtick=1)
    fig.update_yaxes(title="Ø Rendite (%)", tickformat="+.3f", ticksuffix="%")
    return fig


def build_tdom_winrate_chart(stats: pd.DataFrame, ticker: str) -> go.Figure:
    """Win-Rate Balkendiagramm pro TDoM."""
    colors = [
        SE_COLORS["positive"] if w >= 50 else SE_COLORS["negative"]
        for w in stats["win_rate"]
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[str(t) for t in stats.index],
        y=stats["win_rate"],
        marker_color=colors,
        hovertemplate="TDoM %{x}: %{y:.1f}%<extra></extra>",
    ))

    fig.add_hline(y=50, line_dash="dash", line_color=SE_COLORS["accent_warm"], line_width=1.5)

    fig = apply_se_theme(fig, title=f"{ticker} — Win-Rate pro TDoM", height=320)
    fig.update_xaxes(title="TDoM", dtick=1)
    fig.update_yaxes(title="Win-Rate (%)", range=[0, 100])
    return fig


def build_month_tdom_heatmap(
    matrix: pd.DataFrame, ticker: str, strategy: str,
) -> go.Figure:
    """Heatmap: Monate × TDoM mit Ø Rendite."""
    # Farbskala: rot → dunkel → grün
    max_abs = max(abs(matrix.min().min()), abs(matrix.max().max()), 0.01)

    fig = go.Figure(data=go.Heatmap(
        z=matrix.values,
        x=[str(c) for c in matrix.columns],
        y=matrix.index,
        colorscale=[
            [0, SE_COLORS["negative"]],
            [0.5, SE_COLORS["surface"]],
            [1, SE_COLORS["positive"]],
        ],
        zmid=0,
        zmin=-max_abs,
        zmax=max_abs,
        hovertemplate=(
            "Monat: %{y}<br>"
            "TDoM: %{x}<br>"
            "Ø Rendite: %{z:+.4f}%"
            "<extra></extra>"
        ),
        colorbar=dict(
            title=dict(text="Ø %", font=dict(color=SE_COLORS["text_muted"])),
            tickfont=dict(color=SE_COLORS["text_muted"]),
            tickformat="+.3f",
        ),
    ))

    strat_label = STRATEGY_LABELS.get(strategy, strategy)
    fig = apply_se_heatmap_theme(
        fig, title=f"{ticker} — TDoM × Monat ({strat_label})", height=450,
    )
    fig.update_xaxes(title="Trading Day of Month", dtick=1)
    return fig


def build_range_equity_chart(
    range_df: pd.DataFrame, ticker: str, entry_tdom: int, exit_tdom: int,
) -> go.Figure:
    """Kumulative Equity-Kurve für TDoM-Range-Strategie."""
    if range_df.empty:
        return go.Figure()

    sorted_df = range_df.sort_values(["year", "month"])
    cum_returns = (1 + sorted_df["return_pct"] / 100).cumprod() * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(cum_returns))),
        y=cum_returns.values,
        mode="lines",
        line=dict(color=SE_COLORS["accent"], width=2),
        fill="tozeroy",
        fillcolor="rgba(0,212,170,0.08)",
        hovertemplate="Trade #%{x}: %{y:.2f}<extra></extra>",
    ))

    fig.add_hline(y=100, line_dash="dash", line_color=SE_COLORS["zero_line"], line_width=1)

    fig = apply_se_theme(
        fig,
        title=f"{ticker} — Equity: TDoM {entry_tdom} → TDoM {exit_tdom}",
        height=350,
    )
    fig.update_xaxes(title="Trade #")
    fig.update_yaxes(title="Kumulativ (Start=100)")
    return fig


# ══════════════════════════════════════════════════════
# HAUPTSEITE
# ══════════════════════════════════════════════════════

def main():
    # ── Sidebar ──
    with st.sidebar:
        st.markdown("### 📅 TDoM Analyse")
        ticker = st.text_input(
            "Ticker", value=DEFAULT_TICKER, key="tdom_ticker",
        ).upper().strip()

        years_back = st.slider("📅 Jahre zurück", 3, 50, 20, key="tdom_years")

        strategy = st.selectbox(
            "Strategie",
            options=list(STRATEGY_LABELS.keys()),
            format_func=lambda s: STRATEGY_LABELS[s],
            key="tdom_strat",
        )

        direction = st.selectbox(
            "Richtung",
            options=list(DIRECTION_LABELS.keys()),
            format_func=lambda d: DIRECTION_LABELS[d],
            key="tdom_dir",
        )

        selected_months = st.multiselect(
            "Monate filtern",
            options=list(range(1, 13)),
            default=list(range(1, 13)),
            format_func=lambda m: MONTH_NAMES_DE[m - 1],
            key="tdom_months",
        )

        st.markdown("---")
        from shared.outlier_manager import outlier_sidebar
        outlier_method = outlier_sidebar()

        st.markdown("---")

        st.markdown("**📐 Multi-Day Range**")
        use_range = st.checkbox("Range-Strategie aktivieren", key="tdom_range")
        if use_range:
            entry_tdom = st.number_input("Entry TDoM", value=1, min_value=-23, max_value=23, key="tdom_entry")
            exit_tdom = st.number_input("Exit TDoM", value=-1, min_value=-23, max_value=23, key="tdom_exit")
            entry_price = st.selectbox("Entry Preis", ["Open", "Close"], key="tdom_ep")
            exit_price = st.selectbox("Exit Preis", ["Open", "Close"], index=1, key="tdom_xp")

    # ── Header ──
    st.markdown("## 📅 Trading Day of the Month (TDoM)")
    strat_label = STRATEGY_LABELS[strategy]
    dir_label = DIRECTION_LABELS[direction]
    st.caption(f"{strat_label} · {dir_label} · {years_back} Jahre")

    # ── Daten laden ──
    with st.spinner(f"Lade {ticker}..."):
        raw_df = download_data(ticker)
    if raw_df is None or raw_df.empty:
        st.error(f"Keine Daten für '{ticker}'.")
        st.stop()

    df = preprocess(raw_df)
    if df is None or df.empty:
        st.error(f"Verarbeitung fehlgeschlagen.")
        st.stop()

    current_year = datetime.now().year
    df = df[df["year"] >= (current_year - years_back)]

    if len(df) < 100:
        st.warning("Zu wenig Daten.")
        st.stop()

    # ── Outlier-Filter anwenden ──
    if outlier_method != "off":
        from shared.calculations import build_year_data, calculate_seasonal_average
        _available_years = sorted(df["year"].unique())
        _yd = build_year_data(df, _available_years)
        from shared.outlier_manager import filter_year_data, outlier_info_box
        _yd_filtered, _outlier_years = filter_year_data(_yd, method=outlier_method)
        if _outlier_years:
            df = df[~df["year"].isin(_outlier_years)]
            outlier_info_box(_outlier_years, outlier_method)

    # ══════════════════════════════════════════════════
    # SEKTION 1: TDoM Balkendiagramm
    # ══════════════════════════════════════════════════
    stats = build_tdom_stats(df, strategy, direction, selected_months)

    if stats.empty:
        st.warning("Keine TDoM-Daten für die gewählten Filter.")
        st.stop()

    fig_bars = build_tdom_bar_chart(stats, ticker, strategy, direction)

    # "You are here" — aktuellen TDoM markieren
    from shared.tdom_analysis import add_tdom_columns
    _today_df = add_tdom_columns(df)
    _today_row = _today_df.iloc[-1] if not _today_df.empty else None
    _current_tdom = None
    if _today_row is not None:
        _current_tdom = int(_today_row["tdom"]) if direction == "forward" else int(_today_row["tdom_reverse"])
        if _current_tdom in stats.index:
            _tdom_labels = [str(t) for t in stats.index]
            _tdom_pos = _tdom_labels.index(str(_current_tdom))
            fig_bars.add_annotation(
                x=str(_current_tdom),
                y=stats.loc[_current_tdom, "avg_return"],
                text="We are here",
                showarrow=True,
                arrowhead=2,
                arrowcolor="#F1C40F",
                ax=0, ay=-35,
                font=dict(color="#F1C40F", size=11, family="Inter"),
                bordercolor="#F1C40F",
                borderwidth=1,
                borderpad=3,
                bgcolor="rgba(15,25,35,0.85)",
            )

    st.plotly_chart(fig_bars, use_container_width=True)

    # ── KPIs ──
    best_tdom = stats["avg_return"].idxmax()
    worst_tdom = stats["avg_return"].idxmin()
    best_wr_tdom = stats["win_rate"].idxmax()

    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        st.metric("Bester TDoM", f"{best_tdom}",
                  f"{stats.loc[best_tdom, 'avg_return']:+.4f}%")
    with kpi_cols[1]:
        st.metric("Schlechtester TDoM", f"{worst_tdom}",
                  f"{stats.loc[worst_tdom, 'avg_return']:+.4f}%")
    with kpi_cols[2]:
        st.metric("Höchste Win-Rate", f"TDoM {best_wr_tdom}",
                  f"{stats.loc[best_wr_tdom, 'win_rate']:.1f}%")
    with kpi_cols[3]:
        total_trades = stats["count"].sum()
        st.metric("Trades gesamt", f"{total_trades:,.0f}")

    # ══════════════════════════════════════════════════
    # TDoM-Anomalien (KI) — direkt nach dem Balkendiagramm
    # ══════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("### TDoM-Anomalien (KI)")
    st.caption(
        "Isolation Forest vergleicht die letzten 3 Monate mit der historischen Norm. "
        "Hoher Z-Score = ungewoehnliches Verhalten."
    )
    try:
        from shared.anomaly_engine import detect_tdom_anomalies
        anomalies = detect_tdom_anomalies(df, strategy=strategy, recent_months=3)
        if anomalies:
            for a in anomalies[:5]:
                icon = "🟢" if a["direction"] == "bullish" else "🔴"
                st.markdown(
                    f'{icon} **TDoM {a["tdom"]}** — '
                    f'Z-Score: **{a["z_score"]:+.2f}** | '
                    f'Aktuell: {a["recent_avg"]:+.4f}% vs. '
                    f'Historisch: {a["historical_avg"]:+.4f}% '
                    f'(n={a["recent_n"]}/{a["historical_n"]})'
                )
        else:
            st.caption("Keine signifikanten TDoM-Anomalien in den letzten 3 Monaten.")
    except Exception as _e:
        st.caption(f"Anomalie-Erkennung nicht verfuegbar: {_e}")

    # ══════════════════════════════════════════════════
    # SEKTION 2: Win-Rate + Statistik-Tabelle
    # ══════════════════════════════════════════════════
    st.markdown("---")
    col_wr, col_table = st.columns([1.3, 1])

    with col_wr:
        fig_wr = build_tdom_winrate_chart(stats, ticker)
        st.plotly_chart(fig_wr, use_container_width=True)

    with col_table:
        st.markdown("#### 📋 TDoM Statistiken")
        display_stats = stats.copy()
        display_stats.columns = [
            "Ø Rendite (%)", "Win-Rate (%)", "Trades", "Std-Dev",
            "Median (%)", "Max (%)", "Min (%)",
        ]
        st.dataframe(
            display_stats,
            use_container_width=True,
            height=400,
            column_config={
                "Ø Rendite (%)": st.column_config.NumberColumn(format="%+.4f%%"),
                "Win-Rate (%)": st.column_config.NumberColumn(format="%.1f%%"),
                "Median (%)": st.column_config.NumberColumn(format="%+.4f%%"),
            },
        )

    # ══════════════════════════════════════════════════
    # SEKTION 3: Monats-TDoM-Heatmap
    # ══════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("### 🗺️ TDoM × Monat Heatmap")

    matrix = build_tdom_month_matrix(df, strategy, direction)
    if not matrix.empty:
        fig_hm = build_month_tdom_heatmap(matrix, ticker, strategy)

        # "You are here" — aktuellen Monat + TDoM markieren
        if _current_tdom is not None:
            _current_month = datetime.now().month
            _current_month_name = MONTH_NAMES_DE[_current_month - 1]
            _hm_cols = [str(c) for c in matrix.columns]
            _tdom_str = str(_current_tdom)
            if _tdom_str in _hm_cols and _current_month_name in matrix.index:
                _col_idx = _hm_cols.index(_tdom_str)
                _row_idx = list(matrix.index).index(_current_month_name)
                fig_hm.add_shape(
                    type="rect",
                    x0=_col_idx - 0.5, x1=_col_idx + 0.5,
                    y0=_row_idx - 0.5, y1=_row_idx + 0.5,
                    line=dict(color="#F1C40F", width=3),
                    fillcolor="rgba(0,0,0,0)",
                    layer="above",
                )
                fig_hm.add_annotation(
                    x=_col_idx, y=_row_idx,
                    text="We are here",
                    showarrow=True,
                    arrowhead=2,
                    arrowcolor="#F1C40F",
                    ax=40, ay=-25,
                    font=dict(color="#F1C40F", size=10, family="Inter"),
                    bordercolor="#F1C40F",
                    borderwidth=1,
                    borderpad=2,
                    bgcolor="rgba(15,25,35,0.85)",
                )

        st.plotly_chart(fig_hm, use_container_width=True)
    else:
        st.caption("Heatmap nicht verfügbar.")

    # ══════════════════════════════════════════════════
    # SEKTION 4: Multi-Day Range (optional)
    # ══════════════════════════════════════════════════
    if use_range:
        st.markdown("---")
        st.markdown(f"### 📐 TDoM Range: {entry_tdom} → {exit_tdom}")
        st.caption(f"Entry: {entry_price} an TDoM {entry_tdom} · Exit: {exit_price} an TDoM {exit_tdom}")

        range_df = calc_tdom_range_return(
            df, entry_tdom, exit_tdom, entry_price, exit_price,
        )

        if range_df.empty:
            st.warning("Keine Trades für diese Kombination gefunden.")
        else:
            range_stats = calc_range_stats(range_df)

            # KPIs
            rc = st.columns(5)
            with rc[0]:
                color = SE_COLORS["positive"] if range_stats["avg_return"] > 0 else SE_COLORS["negative"]
                st.metric("Ø Rendite", f"{range_stats['avg_return']:+.3f}%")
            with rc[1]:
                st.metric("Win-Rate", f"{range_stats['win_rate']:.1f}%")
            with rc[2]:
                st.metric("Trades", range_stats["total_trades"])
            with rc[3]:
                st.metric("Ø Haltetage", f"{range_stats['avg_holding']:.1f}")
            with rc[4]:
                st.metric("Max Gewinn", f"{range_stats['max_gain']:+.3f}%")

            # Equity-Kurve
            fig_eq = build_range_equity_chart(range_df, ticker, entry_tdom, exit_tdom)
            st.plotly_chart(fig_eq, use_container_width=True)

            # Trade-Tabelle
            with st.expander("📋 Alle Trades anzeigen"):
                display_range = range_df.copy()
                display_range["return_pct"] = display_range["return_pct"].round(4)
                st.dataframe(
                    display_range.sort_values(["year", "month"], ascending=False),
                    use_container_width=True,
                    hide_index=True,
                    height=400,
                )

    # ══════════════════════════════════════════════════
    # SEKTION 5: Jahres-Breakdown (Expander)
    # ══════════════════════════════════════════════════
    st.markdown("---")
    with st.expander("📊 Jahres-Breakdown für einzelnen TDoM"):
        sel_tdom = st.number_input(
            "TDoM auswählen",
            value=1 if direction == "forward" else -1,
            min_value=-23, max_value=23,
            key="tdom_breakdown",
        )
        yearly = build_tdom_year_breakdown(df, sel_tdom, strategy, direction)
        if yearly.empty:
            st.caption("Keine Daten.")
        else:
            st.dataframe(yearly, use_container_width=True)

    # ── Disclaimer ──
    st.markdown("---")
    st.caption(
        "⚠️ _TDoM-Analyse basiert auf historischen Mustern. "
        "Transaktionskosten, Slippage und Steuern nicht berücksichtigt. "
        "Keine Anlageberatung._"
    )


main()

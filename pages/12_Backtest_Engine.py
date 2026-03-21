"""
SeasonalAlpha — Backtest Engine & Optimierer
===============================================
Generischer Event-Backtester: Feiertage, FOMC, OPEX, Mondphasen.
Grid-Search Optimierung, Walk-Forward, KI Event-Relevanz.
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
from shared.charts import apply_se_theme, apply_se_heatmap_theme
from shared.backtest_engine import (
    run_backtest, optimize_parameters, walk_forward,
    score_event_relevance, make_holiday_events, make_fomc_events,
    make_opex_events, make_moon_events, extract_trade_features,
    filter_trades_isolation_forest, OBJECTIVES,
)

st.set_page_config(
    page_title="Backtest Engine — SeasonalAlpha",
    page_icon="🔬",
    layout="wide",
)

from shared.design import inject_se_css
inject_se_css()

_PLOTLY_CFG = {"displayModeBar": False, "scrollZoom": False}


# ══════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### Backtest Engine")
    st.markdown("---")

    ticker = st.text_input("Ticker", value=DEFAULT_TICKER, key="bt_ticker").upper().strip()

    years_back = st.slider("Jahre zurueck", 5, 50, 20, key="bt_years")

    st.markdown("---")
    st.markdown("**Event-Typ**")
    event_type = st.selectbox(
        "Welche Events backtesten?",
        ["Feiertage (NYSE)", "FOMC", "OPEX", "Triple Witching", "Vollmond", "Neumond"],
        key="bt_event_type",
    )

    st.markdown("---")
    st.markdown("**Entry / Exit**")
    entry_col = st.radio("Entry-Preis", ["Close", "Open"], key="bt_entry", horizontal=True)
    exit_col = st.radio("Exit-Preis", ["Close", "Open"], key="bt_exit", horizontal=True)

    st.markdown("---")
    with st.expander("Stop-Loss"):
        use_stop = st.checkbox("Stop-Loss aktivieren", key="bt_stop")
        stop_pct = st.slider("Stop %", 0.5, 10.0, 3.0, 0.5, key="bt_stop_pct") if use_stop else 0.0
        stop_type = st.radio("Typ", ["fixed", "trailing"], key="bt_stop_type", horizontal=True) if use_stop else "fixed"

    st.markdown("---")
    from shared.outlier_manager import outlier_sidebar
    outlier_method = outlier_sidebar()


# ══════════════════════════════════════════════════════
# DATEN LADEN
# ══════════════════════════════════════════════════════

st.markdown("## Backtest Engine")
st.caption(f"{ticker} | {event_type} | {years_back} Jahre")

with st.spinner(f"Lade {ticker}..."):
    raw_df = download_data(ticker)

if raw_df is None or raw_df.empty:
    st.error(f"Keine Daten fuer '{ticker}'.")
    st.stop()

df = preprocess(raw_df)
current_year = datetime.now().year
start_year = current_year - years_back
selected_years = [y for y in sorted(df["year"].unique()) if start_year <= y <= current_year]

# Outlier
exclude_years = []
if outlier_method != "off":
    from shared.calculations import build_year_data
    from shared.outlier_manager import filter_year_data, outlier_info_box
    yd = build_year_data(df, selected_years)
    _, exclude_years = filter_year_data(yd, method=outlier_method)
    outlier_info_box(exclude_years, outlier_method)

# Events laden
event_map = {
    "Feiertage (NYSE)": lambda: make_holiday_events("NYSE"),
    "FOMC": make_fomc_events,
    "OPEX": lambda: make_opex_events(triple_only=False),
    "Triple Witching": lambda: make_opex_events(triple_only=True),
    "Vollmond": lambda: make_moon_events("full"),
    "Neumond": lambda: make_moon_events("new"),
}
events = event_map[event_type]()


# ══════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════

tab1, tab2, tab3, tab4 = st.tabs([
    "Einzelner Backtest",
    "Parameter-Optimierung",
    "Walk-Forward",
    "Event-Relevanz (KI)",
])


# ── TAB 1: EINZELNER BACKTEST ────────────────────────

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        days_before = st.slider("Tage VOR Event (Entry)", 1, 15, 3, key="bt_before")
    with c2:
        days_after = st.slider("Tage NACH Event (Exit)", 1, 15, 3, key="bt_after")

    with st.spinner("Backtest laeuft..."):
        result = run_backtest(
            df, events,
            days_before=days_before,
            days_after=days_after,
            entry_price_col=entry_col,
            exit_price_col=exit_col,
            selected_years=selected_years,
            stop_loss_pct=stop_pct if use_stop else 0,
            stop_loss_type=stop_type,
            exclude_years=exclude_years,
        )

    if result.n_trades == 0:
        st.warning("Keine Trades im gewaehlten Zeitraum.")
    else:
        # Metriken
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Total Return", f"{result.total_return_pct:+.1f}%")
        m2.metric("Sharpe", f"{result.sharpe_ratio:.2f}")
        m3.metric("Calmar", f"{result.calmar_ratio:.2f}")
        m4.metric("Win-Rate", f"{result.win_rate_pct:.0f}%")
        m5.metric("Max Drawdown", f"{result.max_drawdown_pct:.1f}%")
        m6.metric("Trades", f"{result.n_trades}")

        # Equity Kurve
        fig_eq = go.Figure(go.Scatter(
            x=list(range(len(result.equity_curve))),
            y=result.equity_curve,
            mode="lines",
            line=dict(color=SE_COLORS["accent_blue"], width=2),
            fill="tozeroy", fillcolor="rgba(77,159,255,0.08)",
            hovertemplate="Trade #%{x}: %{y:.2f}<extra></extra>",
        ))
        fig_eq.add_hline(y=100, line_dash="dash", line_color="rgba(255,255,255,0.2)")
        fig_eq = apply_se_theme(fig_eq, title="Equity-Kurve (Start = 100)", height=350, show_legend=False)
        fig_eq.update_xaxes(title="Trade #")
        fig_eq.update_yaxes(title="Equity")
        st.plotly_chart(fig_eq, use_container_width=True, config=_PLOTLY_CFG)

        # Trade-Tabelle
        with st.expander(f"Alle {result.n_trades} Trades anzeigen"):
            trade_rows = []
            for t in result.trades:
                trade_rows.append({
                    "Event": t.event_name,
                    "Entry": str(t.entry_date),
                    "Exit": str(t.exit_date),
                    "Rendite": f"{t.return_pct:+.2f}%",
                    "Haltetage": t.holding_days,
                    "Stop": "Ja" if t.stopped_out else "",
                    "Jahr": t.year,
                })
            st.dataframe(pd.DataFrame(trade_rows), use_container_width=True, hide_index=True, height=400)


# ── TAB 2: PARAMETER-OPTIMIERUNG ─────────────────────

with tab2:
    st.subheader("Grid-Search Optimierung")

    oc1, oc2, oc3 = st.columns(3)
    with oc1:
        opt_before_range = st.slider("days_before Range", 1, 15, (1, 10), key="opt_before")
    with oc2:
        opt_after_range = st.slider("days_after Range", 1, 15, (1, 10), key="opt_after")
    with oc3:
        opt_objective = st.selectbox("Zielvariable", list(OBJECTIVES.keys()),
                                      index=2, key="opt_obj")

    if st.button("Optimierung starten", type="primary", key="opt_start"):
        param_grid = {
            "days_before": list(range(opt_before_range[0], opt_before_range[1] + 1)),
            "days_after": list(range(opt_after_range[0], opt_after_range[1] + 1)),
        }
        n_combos = len(param_grid["days_before"]) * len(param_grid["days_after"])

        progress = st.progress(0, text=f"0 / {n_combos} Kombinationen...")

        def _progress(i, total):
            progress.progress(i / total, text=f"{i} / {total} Kombinationen...")

        with st.spinner("Optimierung laeuft..."):
            opt_result = optimize_parameters(
                df, events, param_grid, opt_objective,
                entry_price_col=entry_col, exit_price_col=exit_col,
                stop_loss_pct=stop_pct if use_stop else 0,
                stop_loss_type=stop_type,
                selected_years=selected_years,
                exclude_years=exclude_years,
                progress_callback=_progress,
            )

        progress.empty()

        if opt_result.results:
            best = opt_result.best_by_objective.get(opt_objective, opt_result.results[0])
            st.success(
                f"Beste Parameter: **days_before={best.params['days_before']}**, "
                f"**days_after={best.params['days_after']}** → "
                f"{opt_objective}: **{OBJECTIVES[opt_objective](best):.2f}**"
            )

            # Heatmap
            before_vals = param_grid["days_before"]
            after_vals = param_grid["days_after"]
            z_matrix = np.zeros((len(after_vals), len(before_vals)))

            obj_fn = OBJECTIVES[opt_objective]
            for r in opt_result.results:
                bi = before_vals.index(r.params["days_before"])
                ai = after_vals.index(r.params["days_after"])
                z_matrix[ai, bi] = obj_fn(r)

            fig_hm = go.Figure(go.Heatmap(
                z=z_matrix,
                x=[str(b) for b in before_vals],
                y=[str(a) for a in after_vals],
                colorscale=[
                    [0, SE_COLORS["negative"]],
                    [0.5, SE_COLORS["surface"]],
                    [1, SE_COLORS["positive"]],
                ],
                hovertemplate="Before: %{x}<br>After: %{y}<br>Wert: %{z:.2f}<extra></extra>",
                colorbar=dict(
                    title=dict(text=opt_objective, font=dict(color="#e8edf5")),
                    tickfont=dict(color="#e8edf5"),
                ),
            ))
            fig_hm = apply_se_heatmap_theme(
                fig_hm, title=f"Optimierung: {opt_objective} (days_before x days_after)", height=400,
            )
            fig_hm.update_xaxes(title="Tage VOR Event")
            fig_hm.update_yaxes(title="Tage NACH Event")
            st.plotly_chart(fig_hm, use_container_width=True, config=_PLOTLY_CFG)

            # Top 10
            st.subheader("Top 10 Kombinationen")
            top_rows = []
            for r in opt_result.results[:10]:
                top_rows.append({
                    "Before": r.params["days_before"],
                    "After": r.params["days_after"],
                    "Return": f"{r.total_return_pct:+.1f}%",
                    "Sharpe": f"{r.sharpe_ratio:.2f}",
                    "Calmar": f"{r.calmar_ratio:.2f}",
                    "Win-Rate": f"{r.win_rate_pct:.0f}%",
                    "Max DD": f"{r.max_drawdown_pct:.1f}%",
                    "Trades": r.n_trades,
                })
            st.dataframe(pd.DataFrame(top_rows), use_container_width=True, hide_index=True)


# ── TAB 3: WALK-FORWARD ──────────────────────────────

with tab3:
    st.subheader("Walk-Forward Validierung")
    st.caption("Optimiert auf In-Sample, testet auf Out-of-Sample → realistische Performance ohne Overfitting.")

    wc1, wc2, wc3 = st.columns(3)
    with wc1:
        wf_folds = st.slider("Anzahl Folds", 3, 10, 5, key="wf_folds")
    with wc2:
        wf_ratio = st.slider("In-Sample Ratio", 0.5, 0.8, 0.7, 0.05, key="wf_ratio")
    with wc3:
        wf_objective = st.selectbox("Zielvariable", list(OBJECTIVES.keys()),
                                     index=2, key="wf_obj")

    if st.button("Walk-Forward starten", type="primary", key="wf_start"):
        progress_wf = st.progress(0, text="Walk-Forward laeuft...")

        def _wf_progress(i, total):
            progress_wf.progress(i / total, text=f"Fold {i+1} / {total}...")

        with st.spinner("Walk-Forward Validierung..."):
            wf_results = walk_forward(
                df, events,
                objective=wf_objective,
                n_folds=wf_folds,
                in_sample_ratio=wf_ratio,
                entry_price_col=entry_col,
                exit_price_col=exit_col,
                stop_loss_pct=stop_pct if use_stop else 0,
                stop_loss_type=stop_type,
                exclude_years=exclude_years,
                progress_callback=_wf_progress,
            )

        progress_wf.empty()

        if wf_results:
            # Aggregate OOS results
            all_oos_trades = []
            for r in wf_results:
                all_oos_trades.extend(r.trades)

            if all_oos_trades:
                from shared.backtest_engine import _compute_stats
                agg = _compute_stats(all_oos_trades, {"type": "walk-forward OOS"})

                st.markdown("### Out-of-Sample Ergebnis (aggregiert)")
                wm1, wm2, wm3, wm4 = st.columns(4)
                wm1.metric("OOS Return", f"{agg.total_return_pct:+.1f}%")
                wm2.metric("OOS Sharpe", f"{agg.sharpe_ratio:.2f}")
                wm3.metric("OOS Win-Rate", f"{agg.win_rate_pct:.0f}%")
                wm4.metric("OOS Trades", f"{agg.n_trades}")

                # Fold-Details
                with st.expander("Fold-Details"):
                    fold_rows = []
                    for i, r in enumerate(wf_results):
                        fold_rows.append({
                            "Fold": i + 1,
                            "Trades": r.n_trades,
                            "Return": f"{r.total_return_pct:+.1f}%",
                            "Win-Rate": f"{r.win_rate_pct:.0f}%",
                            "Params": f"b={r.params.get('days_before','?')}, a={r.params.get('days_after','?')}",
                        })
                    st.dataframe(pd.DataFrame(fold_rows), use_container_width=True, hide_index=True)
            else:
                st.warning("Keine OOS-Trades generiert.")
        else:
            st.warning("Walk-Forward konnte nicht durchgefuehrt werden (zu wenig Daten?).")


# ── TAB 4: EVENT-RELEVANZ (KI) ───────────────────────

with tab4:
    st.subheader("Event-Relevanz Ranking (KI)")
    st.caption("Welche Events sind statistisch signifikant? t-Test + Effect Size + Win-Rate → Relevanz-Score.")

    rc1, rc2 = st.columns(2)
    with rc1:
        rel_before = st.slider("Fenster: Tage vor", 1, 10, 3, key="rel_before")
    with rc2:
        rel_after = st.slider("Fenster: Tage nach", 1, 10, 3, key="rel_after")

    if st.button("Relevanz berechnen", type="primary", key="rel_start"):
        with st.spinner("Berechne Event-Relevanz..."):
            relevance_df = score_event_relevance(
                df, events,
                days_before=rel_before,
                days_after=rel_after,
                selected_years=selected_years,
            )

        if relevance_df.empty:
            st.warning("Keine Events mit genuegend Daten.")
        else:
            st.dataframe(relevance_df, use_container_width=True, hide_index=True)

            # Balkendiagramm
            fig_rel = go.Figure(go.Bar(
                x=relevance_df["Event"],
                y=relevance_df["Relevanz"],
                marker_color=[
                    SE_COLORS["positive"] if r > 0.6 else SE_COLORS["accent_warm"] if r > 0.4 else SE_COLORS["negative"]
                    for r in relevance_df["Relevanz"]
                ],
                text=[f"{r:.2f}" for r in relevance_df["Relevanz"]],
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>Relevanz: %{y:.3f}<br>Oe Rendite: %{customdata[0]:+.2f}%<br>Win-Rate: %{customdata[1]:.0f}%<extra></extra>",
                customdata=relevance_df[["Oe Rendite", "Win-Rate"]].values,
            ))
            fig_rel = apply_se_theme(fig_rel, title="Event-Relevanz Ranking", height=400, show_legend=False)
            fig_rel.update_yaxes(title="Relevanz-Score")
            st.plotly_chart(fig_rel, use_container_width=True, config=_PLOTLY_CFG)

            # Interpretation
            top = relevance_df.iloc[0]
            st.info(
                f'**Relevantestes Event: {top["Event"]}** — '
                f'Relevanz-Score: {top["Relevanz"]:.3f} | '
                f'p-Wert: {top["p-Wert"]:.4f} | '
                f'Oe Rendite: {top["Oe Rendite"]:+.2f}% | '
                f'Win-Rate: {top["Win-Rate"]:.0f}%'
            )

# ── Disclaimer ──
st.markdown("---")
st.caption(
    "Backtests basieren auf historischen Daten. Vergangene Performance ist kein Indikator "
    "fuer zukuenftige Ergebnisse. Transaktionskosten und Slippage nicht beruecksichtigt. "
    "Keine Anlageberatung."
)

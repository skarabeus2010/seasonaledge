"""
SeasonalEdge - Turn of the Month
==================================
Analyse des Monatswechsel-Effekts.
"""

import streamlit as st
import pandas as pd
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
import numpy as np
from datetime import datetime

from shared.constants import DEFAULT_TICKER, DEFAULT_YEARS, MONTH_NAMES_DE
from shared.data import download_data, preprocess
from shared.calculations import analyze_turn_of_month, build_tom_chart

st.set_page_config(page_title="SeasonalEdge - Turn of the Month", page_icon="🔄", layout="wide")

from shared.design import inject_se_css
inject_se_css()


def main():
    with st.sidebar:
        st.markdown("## 🔄 Turn of the Month")
        st.markdown("---")
        
        ticker = st.text_input("Ticker", value=DEFAULT_TICKER, key="tom_ticker").upper().strip()
        
        period_options = [3, 5, 7, 10, 15, 20, 25, 30, "Max"]
        years_back_raw = st.select_slider(
            "Analyse-Zeitraum (Jahre)",
            options=period_options, value=DEFAULT_YEARS,
            format_func=lambda x: str(x), key="tom_period"
        )
        years_back_is_max = (years_back_raw == "Max")
        
        st.markdown("---")
        
        tom_days_before = st.slider(
            "Tage VOR Monatswechsel (t-y)", 1, 10, 3,
            help="Handelstage vor dem letzten Handelstag des Monats"
        )
        tom_days_after = st.slider(
            "Tage NACH Monatswechsel (t+x)", 1, 10, 3,
            help="Handelstage nach dem Monatswechsel"
        )
        tom_months = st.multiselect(
            "Monate (Wechsel von → nach)",
            options=list(range(1, 13)),
            default=list(range(1, 13)),
            format_func=lambda m: f"{MONTH_NAMES_DE[m-1]} → {MONTH_NAMES_DE[m % 12]}",
            help="Welche Monatswechsel analysieren?"
        )
        show_individual_tom = st.checkbox("Einzelne Fenster zeigen", value=False)
    
    # ── Daten laden ───────────────────────────────────
    with st.spinner(f"Lade {ticker} Daten..."):
        raw_df = download_data(ticker)
    
    if raw_df is None or raw_df.empty:
        st.error(f"Keine Daten für '{ticker}' gefunden.")
        return
    
    df = preprocess(raw_df)
    all_years = sorted(df["year"].unique())
    
    if years_back_is_max:
        selected_years = all_years
    else:
        years_back = int(years_back_raw)
        cutoff_year = datetime.now().year - years_back
        selected_years = [y for y in all_years if y >= cutoff_year]
    
    if len(selected_years) < 2 or not tom_months:
        st.warning("Nicht genügend Daten oder keine Monate ausgewählt.")
        return
    
    # ── Analyse ───────────────────────────────────────
    tom_result = analyze_turn_of_month(df, tom_days_before, tom_days_after, tom_months, selected_years)
    
    if tom_result is None:
        st.warning("Nicht genug Daten für die Turn-of-the-Month Analyse.")
        return
    
    # ── Chart ─────────────────────────────────────────
    tom_fig = build_tom_chart(
        tom_result, ticker, tom_days_before, tom_days_after,
        tom_months, show_individual_tom
    )
    st.plotly_chart(tom_fig, use_container_width=True)
    
    # ── Metriken ──────────────────────────────────────
    tom_stats = tom_result["stats"]
    
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Win Rate", f"{tom_stats['win_rate']:.1f}%")
    with c2:
        st.metric("Ø Rendite", f"{tom_stats['avg_return']:+.3f}%")
    with c3:
        st.metric("Median", f"{tom_stats['median_return']:+.3f}%")
    with c4:
        st.metric("Max Gewinn", f"{tom_stats['max_gain']:+.2f}%")
    with c5:
        st.metric("Max Verlust", f"{tom_stats['max_loss']:+.2f}%")
    
    st.caption(
        f"Basierend auf {tom_stats['total_windows']} Monatswechsel-Fenstern · "
        f"{tom_stats['winning']} Gewinner / {tom_stats['losing']} Verlierer · "
        f"Std.Abw: {tom_stats['std_dev']:.3f}%"
    )
    
    # ── Best & Worst ──────────────────────────────────
    best = tom_result["best"]
    worst = tom_result["worst"]
    
    st.markdown("#### 🏆 Bester & schlechtester Monatswechsel")
    
    table_data = {
        "": ["🟢 Bester", "🔴 Schlechtester"],
        "Jahr": [best["year"], worst["year"]],
        "Monat": [
            f"{MONTH_NAMES_DE[best['month']-1]} → {MONTH_NAMES_DE[best['month'] % 12]}",
            f"{MONTH_NAMES_DE[worst['month']-1]} → {MONTH_NAMES_DE[worst['month'] % 12]}"
        ],
        "Rendite": [f"{best['total_return']:+.2f}%", f"{worst['total_return']:+.2f}%"]
    }
    st.table(pd.DataFrame(table_data).set_index(""))
    
    # ── Detailtabelle pro Monat ───────────────────────
    st.markdown("#### 📋 Performance pro Monatswechsel")
    st.caption(f"Rendite wenn bei t-{tom_days_before} gekauft und bei t+{tom_days_after} verkauft")
    
    month_perf = {}
    for entry in tom_result["all_curves"]:
        m = entry["month"]
        if m not in month_perf:
            month_perf[m] = []
        month_perf[m].append(entry["total_return"])
    
    perf_rows = []
    for m in sorted(month_perf.keys()):
        rets = month_perf[m]
        wins = [r for r in rets if r > 0]
        perf_rows.append({
            "Monat": f"{MONTH_NAMES_DE[m-1]} → {MONTH_NAMES_DE[m % 12]}",
            "Ø Rendite": f"{np.mean(rets):+.3f}%",
            "Median": f"{np.median(rets):+.3f}%",
            "Win Rate": f"{len(wins)/len(rets)*100:.0f}%",
            "Beste": f"{max(rets):+.2f}%",
            "Schlecht.": f"{min(rets):+.2f}%",
            "n": len(rets)
        })
    
    st.dataframe(pd.DataFrame(perf_rows), use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()

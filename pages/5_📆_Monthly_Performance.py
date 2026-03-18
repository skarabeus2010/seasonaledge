"""
SeasonalEdge - Monats- und Wochen-Performance
=============================================
Monats-Saisonalchart, Wochen-Performance, Two-Week-Analyse.
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

from shared.constants import DEFAULT_TICKER, DEFAULT_YEARS, MONTH_NAMES_DE, CYCLE_COLORS
from shared.data import download_data, preprocess
from shared.calculations import get_presidential_cycle_year

st.set_page_config(page_title="SeasonalEdge - Monthly", page_icon="📆", layout="wide")

def assign_tdom(df):
    df = df.copy()
    df["tdom"] = df.groupby(["year", "month"]).cumcount() + 1
    return df

def get_current_tdom(df):
    today = datetime.now()
    df_tdom = assign_tdom(df)
    current = df_tdom[(df_tdom["year"] == today.year) & (df_tdom["month"] == today.month)]
    current = current[current.index <= pd.Timestamp(today.date())]
    return int(current["tdom"].iloc[-1]) if len(current) > 0 else None

def calc_intramonth_curve(df, target_month, selected_years):
    df = assign_tdom(df)
    all_curves = []
    for year in selected_years:
        month_df = df[(df["year"] == year) & (df["month"] == target_month)].copy()
        if len(month_df) < 10:
            continue
        log_rets = month_df["log_return"].values
        cum = np.cumsum(np.insert(log_rets, 0, 0)[:-1])
        curve = (np.exp(cum) - 1) * 100
        all_curves.append({"year": year, "tdoms": month_df["tdom"].tolist(),
                           "curve": curve.tolist(), "total_return": curve[-1] if len(curve) > 0 else 0})
    if not all_curves:
        return None, []
    max_tdom = max(max(c["tdoms"]) for c in all_curves)
    tdom_stats = {}
    for t in range(1, max_tdom + 1):
        vals = [c["curve"][c["tdoms"].index(t)] for c in all_curves if t in c["tdoms"]]
        if vals:
            tdom_stats[t] = {"avg": np.mean(vals), "std": np.std(vals), "n": len(vals)}
    return tdom_stats, all_curves

def calc_weekly_performance(df, target_month, selected_years):
    df = assign_tdom(df)
    week_returns = {w: [] for w in range(1, 6)}
    for year in selected_years:
        month_df = df[(df["year"] == year) & (df["month"] == target_month)].copy()
        if len(month_df) < 10:
            continue
        for w in range(1, 6):
            s, e = (w-1)*5+1, w*5
            wdf = month_df[(month_df["tdom"] >= s) & (month_df["tdom"] <= e)]
            if len(wdf) >= 2:
                week_returns[w].append((wdf["Close"].iloc[-1] / wdf["Open"].iloc[0] - 1) * 100)
    results = []
    for w in range(1, 6):
        rets = week_returns[w]
        if len(rets) < 2:
            continue
        wins = [r for r in rets if r > 0]
        results.append({"week": w, "label": f"W{w} (TDOM {(w-1)*5+1}-{w*5})",
                        "avg": np.mean(rets), "median": np.median(rets),
                        "win_rate": len(wins)/len(rets)*100, "n": len(rets)})
    return results

def calc_monthly_performance(df, selected_years):
    results = []
    for month in range(1, 13):
        rets = []
        for year in selected_years:
            mdf = df[(df["year"] == year) & (df["month"] == month)]
            if len(mdf) >= 10:
                rets.append((mdf["Close"].iloc[-1] / mdf["Open"].iloc[0] - 1) * 100)
        if len(rets) < 2:
            results.append({"month": month, "avg": 0, "median": 0, "win_rate": 0, "n": 0})
            continue
        wins = [r for r in rets if r > 0]
        results.append({"month": month, "avg": np.mean(rets), "median": np.median(rets),
                        "win_rate": len(wins)/len(rets)*100, "n": len(rets)})
    return results

def calc_two_week_performance(df, selected_years, split_day=10):
    df = assign_tdom(df)
    results = []
    for month in range(1, 13):
        for half in [1, 2]:
            rets = []
            for year in selected_years:
                mdf = df[(df["year"] == year) & (df["month"] == month)].copy()
                if len(mdf) < 10:
                    continue
                hdf = mdf[mdf["tdom"] <= split_day] if half == 1 else mdf[mdf["tdom"] > split_day]
                if len(hdf) >= 3:
                    rets.append((hdf["Close"].iloc[-1] / hdf["Open"].iloc[0] - 1) * 100)
            suffix = "1st" if half == 1 else "2nd"
            label = f"{month:02d}/{suffix}"
            if len(rets) < 2:
                results.append({"label": label, "month": month, "half": half,
                                "avg": 0, "median": 0, "win_rate": 0, "n": 0})
                continue
            wins = [r for r in rets if r > 0]
            results.append({"label": label, "month": month, "half": half,
                            "avg": np.mean(rets), "median": np.median(rets),
                            "win_rate": len(wins)/len(rets)*100, "n": len(rets)})
    return results

# ── CHARTS ────────────────────────────────────────────────

def build_detrend_chart(tdom_stats, ticker, month_name):
    """Detrend-Indikator: Saisonaler Druck mit herausgerechnetem Trend."""
    tdoms = sorted(tdom_stats.keys())
    avg_curve = [tdom_stats[t]["avg"] for t in tdoms]
    
    if len(avg_curve) < 3:
        return None
    
    # Detrending: Linearen Trend entfernen
    n = len(avg_curve)
    end_val = avg_curve[-1]
    daily_drift = end_val / n
    detrended = [avg_curve[i] - ((i + 1) * daily_drift) for i in range(n)]
    
    fig = go.Figure()
    
    # Farbige Füllung
    colors_fill = ["rgba(76,175,80,0.15)" if v >= 0 else "rgba(244,67,54,0.15)" for v in detrended]
    
    fig.add_trace(go.Scatter(
        x=tdoms, y=detrended, mode="lines+markers",
        line=dict(color="#FF6B6B", width=2.5),
        marker=dict(size=4, color="#FF6B6B"),
        fill="tozeroy", fillcolor="rgba(255,107,107,0.1)",
        name="Saisonaler Druck",
        hovertemplate="TDOM %{x}<br>Druck: %{y:+.3f}%<extra></extra>"
    ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)", line_width=1)
    
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=300, margin=dict(t=50, b=40, l=60, r=30),
        title=dict(text=f"{ticker} — {month_name} Detrend-Indikator (saisonaler Druck)",
                   font=dict(size=14, color="#e0e0e0")),
        xaxis=dict(title="TDOM", gridcolor="rgba(255,255,255,0.06)", dtick=1),
        yaxis=dict(title="Abweichung vom Trend (%)", gridcolor="rgba(255,255,255,0.06)",
                   tickformat="+.2f", ticksuffix="%"),
        showlegend=False, hovermode="x unified"
    )
    return fig

def build_intramonth_chart(tdom_stats, all_curves, ticker, month_name,
                           show_individual, show_bands, current_tdom):
    fig = go.Figure()
    tdoms = sorted(tdom_stats.keys())
    avg_curve = [tdom_stats[t]["avg"] for t in tdoms]
    if show_individual:
        for entry in all_curves:
            fig.add_trace(go.Scatter(x=entry["tdoms"], y=entry["curve"], mode="lines",
                line=dict(color="rgba(150,150,150,0.15)", width=0.7), showlegend=False, hoverinfo="skip"))
    if show_bands:
        upper = [tdom_stats[t]["avg"] + tdom_stats[t]["std"] for t in tdoms]
        lower = [tdom_stats[t]["avg"] - tdom_stats[t]["std"] for t in tdoms]
        fig.add_trace(go.Scatter(x=tdoms, y=upper, mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=tdoms, y=lower, mode="lines", line=dict(width=0),
            fill="tonexty", fillcolor="rgba(0,206,209,0.12)", name="±1σ", showlegend=True, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=tdoms, y=avg_curve, mode="lines+markers",
        line=dict(color="#00CED1", width=3), marker=dict(size=5, color="#00CED1"),
        name=f"Ø {month_name}", hovertemplate="TDOM %{x}<br>%{y:+.3f}%<extra></extra>"))
    fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.3)", line_width=1)
    if current_tdom is not None and current_tdom in tdoms:
        fig.add_vline(x=current_tdom, line_dash="solid", line_color="rgba(255,255,255,0.6)", line_width=1.5)
        fig.add_annotation(x=current_tdom, y=1.0, yref="paper",
            text=f"<b>Heute (TDOM {current_tdom})</b>", showarrow=False,
            bgcolor="rgba(30,30,30,0.85)", bordercolor="rgba(255,255,255,0.3)", borderwidth=1,
            font=dict(size=9, color="#e0e0e0"), yshift=-15)
    n_years = tdom_stats[1]["n"] if 1 in tdom_stats else 0
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=400, margin=dict(t=50, b=40, l=60, r=30),
        title=dict(text=f"{ticker} — {month_name} Intra-Monat Verlauf ({n_years} Jahre)", font=dict(size=16, color="#e0e0e0")),
        xaxis=dict(title="Trading Day of Month (TDOM)", gridcolor="rgba(255,255,255,0.06)", dtick=1),
        yaxis=dict(title="Kumulative Rendite (%)", gridcolor="rgba(255,255,255,0.06)",
            tickformat="+.2f", ticksuffix="%", zeroline=True, zerolinecolor="rgba(255,255,255,0.3)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
        hovermode="x unified")
    return fig

def build_weekly_bars(weekly_stats, ticker, month_name):
    if not weekly_stats:
        return None
    labels = [w["label"] for w in weekly_stats]
    avgs = [w["avg"] for w in weekly_stats]
    colors = ["#4CAF50" if v >= 0 else "#F44336" for v in avgs]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=avgs, marker_color=colors,
        text=[f"{v:+.3f}%<br>WR {w['win_rate']:.0f}% · n={w['n']}" for v, w in zip(avgs, weekly_stats)],
        textposition="outside", textfont=dict(size=10),
        hovertemplate="<b>%{x}</b><br>Ø %{y:+.3f}%<extra></extra>"))
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=340, margin=dict(t=50, b=40, l=60, r=30),
        title=dict(text=f"{ticker} — {month_name} Wochen-Performance", font=dict(size=16, color="#e0e0e0")),
        yaxis=dict(tickformat="+.2f", ticksuffix="%", gridcolor="rgba(255,255,255,0.06)"
), showlegend=False)
    return fig

def build_monthly_bars(monthly_stats, ticker):
    current_month = datetime.now().month
    labels = MONTH_NAMES_DE
    avgs = [m["avg"] for m in monthly_stats]
    colors = ["#FFD700" if m["month"] == current_month else ("#4CAF50" if m["avg"] >= 0 else "#F44336") for m in monthly_stats]
    borders = ["rgba(255,215,0,0.8)" if m["month"] == current_month else "rgba(0,0,0,0)" for m in monthly_stats]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=avgs,
        marker=dict(color=colors, line=dict(color=borders, width=2)),
        text=[f"{v:+.2f}%<br>WR {m['win_rate']:.0f}%" for v, m in zip(avgs, monthly_stats)],
        textposition="outside", textfont=dict(size=10),
        hovertemplate="<b>%{x}</b><br>Ø %{y:+.3f}%<br>n=%{customdata}<extra></extra>",
        customdata=[m["n"] for m in monthly_stats]))
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")
    bar_val = avgs[current_month - 1]
    fig.add_annotation(x=MONTH_NAMES_DE[current_month - 1], y=bar_val,
        text="▼ aktuell", showarrow=False, font=dict(size=10, color="#FFD700"),
        yshift=45 if bar_val >= 0 else -45)
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=400, margin=dict(t=50, b=40, l=60, r=30),
        title=dict(text=f"{ticker} — Monats-Performance (Jahresübersicht)", font=dict(size=16, color="#e0e0e0")),
        yaxis=dict(tickformat="+.2f", ticksuffix="%", gridcolor="rgba(255,255,255,0.06)"), showlegend=False)
    return fig

def build_two_week_bars(tw_stats, ticker, split_day):
    today = datetime.now()
    current_label = f"{today.month:02d}/{'1st' if today.day <= 15 else '2nd'}"
    sorted_tw = sorted(tw_stats, key=lambda x: x["avg"], reverse=True)
    labels = [t["label"] for t in sorted_tw]
    avgs = [t["avg"] for t in sorted_tw]
    colors, borders = [], []
    for t in sorted_tw:
        if t["label"] == current_label:
            colors.append("#FFD700"); borders.append("rgba(255,215,0,0.8)")
        elif t["avg"] >= 0:
            colors.append("#4CAF50"); borders.append("rgba(0,0,0,0)")
        else:
            colors.append("#F44336"); borders.append("rgba(0,0,0,0)")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=avgs,
        marker=dict(color=colors, line=dict(color=borders, width=2)),
        text=[f"{v:+.3f}%" for v in avgs], textposition="outside", textfont=dict(size=9),
        hovertemplate="<b>%{x}</b><br>Ø: %{y:+.3f}%<br>WR: %{customdata[0]:.0f}%<br>n=%{customdata[1]}<extra></extra>",
        customdata=[[t["win_rate"], t["n"]] for t in sorted_tw]))
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")
    if current_label in labels:
        idx = labels.index(current_label)
        fig.add_annotation(x=current_label, y=avgs[idx], text="▼ aktuell", showarrow=False,
            font=dict(size=10, color="#FFD700"), yshift=30 if avgs[idx] >= 0 else -30)
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=450, margin=dict(t=60, b=80, l=60, r=30),
        title=dict(text=f"{ticker} — Two-Week Performance (TDOM 1–{split_day} vs. {split_day+1}+), sortiert",
                   font=dict(size=16, color="#e0e0e0")),
        xaxis=dict(tickangle=-60, tickfont=dict(size=11), gridcolor="rgba(255,255,255,0.06)"),
        yaxis=dict(tickformat="+.3f", ticksuffix="%", gridcolor="rgba(255,255,255,0.06)"), showlegend=False)
    return fig

# ── MAIN ──────────────────────────────────────────────────

def main():
    with st.sidebar:
        st.markdown("## 📆 Monats- & Wochen-Performance")
        st.markdown("---")
        ticker = st.text_input("Ticker", value=DEFAULT_TICKER, key="mp_ticker").upper().strip()
        period_options = [3, 5, 7, 10, 15, 20, 25, 30, "Max"]
        years_back_raw = st.select_slider("Analyse-Zeitraum (Jahre)", options=period_options,
            value=DEFAULT_YEARS, format_func=lambda x: str(x), key="mp_period")
        years_back_is_max = (years_back_raw == "Max")
        st.markdown("---")
        st.markdown("### Monats-Saisonalchart")
        current_month = datetime.now().month
        selected_month = st.selectbox("Monat auswählen", options=list(range(1, 13)),
            index=current_month - 1,
            format_func=lambda m: f"{MONTH_NAMES_DE[m-1]}" + (" ← aktuell" if m == current_month else ""))
        show_individual = st.checkbox("Einzelne Jahre zeigen", value=False, key="mp_indiv")
        show_bands = st.checkbox("Konfidenzband (±1σ)", value=True, key="mp_bands")
        show_detrend = st.checkbox("Detrend-Indikator anzeigen", value=False, key="mp_detrend",
            help="Zeigt den bereinigten saisonalen Druck (Trend herausgerechnet)")
        
        st.markdown("---")
        st.markdown("### Präsidentenzyklus-Filter")
        cycle_filter = st.multiselect(
            "Zyklusjahre filtern",
            options=list(CYCLE_COLORS.keys()),
            default=None, key="mp_cycle",
            help="Nur Jahre mit bestimmtem Zyklusjahr berücksichtigen (leer = alle Jahre)"
        )
        st.markdown("---")
        st.markdown("### Two-Week Split")
        split_day = st.slider("Split nach TDOM", 5, 15, 10,
            help="Teilt den Monat: 1st = TDOM 1 bis X, 2nd = TDOM X+1 bis Ende")

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
        selected_years = [y for y in all_years if y >= datetime.now().year - int(years_back_raw)]
    if len(selected_years) < 2:
        st.warning("Nicht genügend Daten.")
        return
    
    # Presidential Cycle Filter
    if cycle_filter:
        selected_years = [y for y in selected_years 
                         if get_presidential_cycle_year(y) in cycle_filter]
        if len(selected_years) < 2:
            st.warning("Nach Zyklusfilter nicht genügend Jahre übrig.")
            return
        cycle_info = ", ".join([c.split("(")[1].rstrip(")") for c in cycle_filter])
        st.info(f"**Zyklusfilter aktiv:** {cycle_info} — {len(selected_years)} Jahre")
    
    month_name = MONTH_NAMES_DE[selected_month - 1]
    current_tdom = get_current_tdom(df) if selected_month == current_month else None

    # 1. Intra-Monat
    tdom_stats, all_curves = calc_intramonth_curve(df, selected_month, selected_years)
    if tdom_stats:
        st.plotly_chart(build_intramonth_chart(tdom_stats, all_curves, ticker, month_name,
            show_individual, show_bands, current_tdom), use_container_width=True)
        
        # Detrend-Indikator
        if show_detrend and tdom_stats:
            detrend_fig = build_detrend_chart(tdom_stats, ticker, month_name)
            if detrend_fig:
                st.plotly_chart(detrend_fig, use_container_width=True)
                st.caption("_Steigt die Linie → überdurchschnittlicher saisonaler Kaufdruck. "
                          "Fällt sie → saisonaler Verkaufsdruck (auch wenn der Monat insgesamt steigt)._")

    # 2. Wochen
    weekly_stats = calc_weekly_performance(df, selected_month, selected_years)
    if weekly_stats:
        fig = build_weekly_bars(weekly_stats, ticker, month_name)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    # 3. Monats-Jahresübersicht
    st.markdown("---")
    st.plotly_chart(build_monthly_bars(calc_monthly_performance(df, selected_years), ticker), use_container_width=True)
    with st.expander("📋 Monats-Detailtabelle"):
        mstats = calc_monthly_performance(df, selected_years)
        st.dataframe(pd.DataFrame([{"Monat": MONTH_NAMES_DE[m["month"]-1], "Ø Rendite": f"{m['avg']:+.3f}%",
            "Median": f"{m['median']:+.3f}%", "Win Rate": f"{m['win_rate']:.0f}%", "n": m["n"]} for m in mstats]),
            use_container_width=True, hide_index=True)

    # 4. Two-Week
    st.markdown("---")
    st.markdown(f"### Two-Week Performance (Split: TDOM {split_day})")
    tw_valid = [t for t in calc_two_week_performance(df, selected_years, split_day) if t["n"] >= 2]
    if tw_valid:
        st.plotly_chart(build_two_week_bars(tw_valid, ticker, split_day), use_container_width=True)
        with st.expander("📋 Two-Week Detailtabelle"):
            tw_sorted = sorted(tw_valid, key=lambda x: x["avg"], reverse=True)
            st.dataframe(pd.DataFrame([{"Periode": t["label"], "Monat": MONTH_NAMES_DE[t["month"]-1],
                "Hälfte": "1st" if t["half"] == 1 else "2nd", "Ø Rendite": f"{t['avg']:+.3f}%",
                "Win Rate": f"{t['win_rate']:.0f}%", "n": t["n"]} for t in tw_sorted]),
                use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()

"""
SeasonAlpha - Monats- und Wochen-Performance
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

st.set_page_config(page_title="Monatliche Saisonalitaet – SeasonAlpha", page_icon="📆", layout="wide")

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

from shared.constants import (
    DEFAULT_TICKER, DEFAULT_YEARS, MONTH_NAMES_DE, CYCLE_COLORS,
    SE_COLORS, SE_HEATMAP_COLORSCALE, SE_HEATMAP_TEXT_COLOR,
)
from shared.data import download_data, preprocess
from shared.calculations import get_presidential_cycle_year
from shared.charts import apply_se_theme
from shared.we_are_here import annotation as wah_annotation, rect as wah_rect, vline as wah_vline

from shared.design import inject_se_css
inject_se_css()

# ── Distinkte Farbpalette fuer Einzeljahre (maximaler Kontrast) ──────
INDIVIDUAL_COLORS = [
    "#FF6B6B", "#00CEC9", "#FFE66D", "#A29BFE", "#FF9FF3",
    "#1ABC9C", "#F39C12", "#3498DB", "#E74C3C", "#2ECC71",
    "#E84393", "#00B894", "#FDCB6E", "#6C5CE7", "#FD79A8",
    "#0984E3", "#D63031", "#00D2D3", "#EE5A24", "#C8D6E5",
]

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

def build_detrend_chart(tdom_stats, ticker, month_name, current_tdom):
    """Detrend-Indikator: Saisonaler Druck mit herausgerechnetem Trend."""
    tdoms = sorted(tdom_stats.keys())
    avg_curve = [tdom_stats[t]["avg"] for t in tdoms]

    if len(avg_curve) < 3:
        return None

    n = len(avg_curve)
    end_val = avg_curve[-1]
    daily_drift = end_val / n
    detrended = [avg_curve[i] - ((i + 1) * daily_drift) for i in range(n)]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=tdoms, y=detrended, mode="lines+markers",
        line=dict(color="#FF6B6B", width=2.5),
        marker=dict(size=4, color="#FF6B6B"),
        fill="tozeroy", fillcolor="rgba(255,107,107,0.1)",
        name="Saisonaler Druck",
        hovertemplate="TDOM %{x}<br>Druck: %{y:+.3f}%<extra></extra>"
    ))

    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)", line_width=1)

    # We are here! — gleiche X-Position wie im Hauptchart
    if current_tdom is not None and current_tdom in tdoms:
        idx = tdoms.index(current_tdom)
        fig.add_shape(**wah_vline(current_tdom))
        fig.add_annotation(**wah_annotation(
            x_val=current_tdom, y_val=detrended[idx],
            above=True, text=f"We are here! TDOM {current_tdom}",
        ))

    n_years = tdom_stats[1]["n"] if 1 in tdom_stats else 0
    fig = apply_se_theme(fig, title=f"{ticker} — {month_name} Detrend-Indikator (saisonaler Druck, {n_years} Jahre)", height=300, show_legend=False)
    # Gleicher X-Achsenbereich wie Hauptchart
    fig.update_xaxes(range=[min(tdoms) - 0.5, max(tdoms) + 0.5])
    return fig

def build_intramonth_chart(tdom_stats, all_curves, ticker, month_name,
                           show_individual, show_bands, current_tdom,
                           current_month_curve=None):
    fig = go.Figure()
    tdoms = sorted(tdom_stats.keys())
    avg_curve = [tdom_stats[t]["avg"] for t in tdoms]

    # Einzeljahre mit distinkten Farben
    if show_individual:
        for i, entry in enumerate(all_curves):
            color = INDIVIDUAL_COLORS[i % len(INDIVIDUAL_COLORS)]
            fig.add_trace(go.Scatter(
                x=entry["tdoms"], y=entry["curve"], mode="lines",
                line=dict(color=color, width=1.2),
                opacity=0.6,
                name=str(entry["year"]),
                showlegend=True,
                hovertemplate=f"<b>{entry['year']}</b><br>TDOM %{{x}}<br>%{{y:+.3f}}%<extra></extra>",
            ))

    # Konfidenzband
    if show_bands:
        upper = [tdom_stats[t]["avg"] + tdom_stats[t]["std"] for t in tdoms]
        lower = [tdom_stats[t]["avg"] - tdom_stats[t]["std"] for t in tdoms]
        fig.add_trace(go.Scatter(x=tdoms, y=upper, mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=tdoms, y=lower, mode="lines", line=dict(width=0),
            fill="tonexty", fillcolor="rgba(0,206,209,0.12)", name="+-1 Sigma", showlegend=True, hoverinfo="skip"))

    # Durchschnittskurve
    fig.add_trace(go.Scatter(x=tdoms, y=avg_curve, mode="lines+markers",
        line=dict(color="#00CED1", width=3), marker=dict(size=5, color="#00CED1"),
        name=f"Oe {month_name}", hovertemplate="TDOM %{x}<br>%{y:+.3f}%<extra></extra>"))
    fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.3)", line_width=1)

    # Aktueller Monatsverlauf (gelbe Linie)
    if current_month_curve is not None:
        cm_tdoms, cm_curve = current_month_curve
        if cm_tdoms and cm_curve:
            current_year = datetime.now().year
            fig.add_trace(go.Scatter(
                x=cm_tdoms, y=cm_curve, mode="lines",
                line=dict(color="#F1C40F", width=2.5),
                name=f"{current_year} (aktuell)",
                hovertemplate=f"<b>{current_year}</b><br>TDOM %{{x}}<br>%{{y:+.3f}}%<extra></extra>",
            ))

    # We are here! (TDOM-Marker)
    if current_tdom is not None and current_tdom in tdoms:
        idx = tdoms.index(current_tdom)
        fig.add_shape(**wah_vline(current_tdom))
        fig.add_annotation(**wah_annotation(
            x_val=current_tdom, y_val=avg_curve[idx],
            above=True, text=f"We are here! TDOM {current_tdom}",
        ))

    n_years = tdom_stats[1]["n"] if 1 in tdom_stats else 0
    fig = apply_se_theme(fig, title=f"{ticker} — {month_name} Intra-Monat Verlauf ({n_years} Jahre)", height=400)
    # X-Achsenbereich fixieren (synchron mit Detrend)
    fig.update_xaxes(range=[min(tdoms) - 0.5, max(tdoms) + 0.5])
    return fig

def build_weekly_bars(weekly_stats, ticker, month_name, current_tdom):
    if not weekly_stats:
        return None
    labels = [w["label"] for w in weekly_stats]
    avgs = [w["avg"] for w in weekly_stats]
    colors = [SE_COLORS["positive"] if v >= 0 else SE_COLORS["negative"] for v in avgs]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=avgs, marker_color=colors,
        text=[f"{v:+.3f}%<br>WR {w['win_rate']:.0f}% · n={w['n']}" for v, w in zip(avgs, weekly_stats)],
        textposition="outside", textfont=dict(size=10),
        hovertemplate="<b>%{x}</b><br>Oe %{y:+.3f}%<extra></extra>"))
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")

    # We are here!
    if current_tdom is not None:
        current_week = min((current_tdom - 1) // 5 + 1, 5)
        current_label = f"W{current_week} (TDOM {(current_week-1)*5+1}-{current_week*5})"
        if current_label in labels:
            idx = labels.index(current_label)
            fig.add_annotation(**wah_annotation(
                x_val=current_label, y_val=avgs[idx],
                above=avgs[idx] >= 0, text=f"We are here! TDOM {current_tdom}",
            ))
            fig.add_shape(**wah_rect(
                x0=idx - 0.4, x1=idx + 0.4,
                y0=0, y1=avgs[idx],
            ))

    fig = apply_se_theme(fig, title=f"{ticker} — {month_name} Wochen-Performance", height=340, show_legend=False)
    return fig

def build_monthly_bars(monthly_stats, ticker, current_tdom):
    current_month = datetime.now().month
    labels = MONTH_NAMES_DE
    avgs = [m["avg"] for m in monthly_stats]
    colors = [SE_COLORS["positive"] if m["avg"] >= 0 else SE_COLORS["negative"] for m in monthly_stats]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=avgs,
        marker_color=colors,
        text=[f"{v:+.2f}%<br>WR {m['win_rate']:.0f}%" for v, m in zip(avgs, monthly_stats)],
        textposition="outside", textfont=dict(size=10),
        hovertemplate="<b>%{x}</b><br>Oe %{y:+.3f}%<br>n=%{customdata}<extra></extra>",
        customdata=[m["n"] for m in monthly_stats]))
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")

    # We are here!
    bar_val = avgs[current_month - 1]
    tdom_text = f"We are here! TDOM {current_tdom}" if current_tdom else "We are here!"
    fig.add_annotation(**wah_annotation(
        x_val=MONTH_NAMES_DE[current_month - 1], y_val=bar_val,
        above=bar_val >= 0, text=tdom_text,
    ))
    fig.add_shape(**wah_rect(
        x0=current_month - 1 - 0.4, x1=current_month - 1 + 0.4,
        y0=0, y1=bar_val,
    ))

    fig = apply_se_theme(fig, title=f"{ticker} — Monats-Performance (Jahresuebersicht)", height=400, show_legend=False)
    return fig

def build_two_week_bars(tw_stats, ticker, split_day, current_tdom):
    today = datetime.now()
    current_half = "1st" if (current_tdom or 1) <= split_day else "2nd"
    current_label = f"{today.month:02d}/{current_half}"
    sorted_tw = sorted(tw_stats, key=lambda x: x["avg"], reverse=True)
    labels = [t["label"] for t in sorted_tw]
    avgs = [t["avg"] for t in sorted_tw]
    colors = [SE_COLORS["positive"] if v >= 0 else SE_COLORS["negative"] for v in avgs]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=avgs,
        marker_color=colors,
        text=[f"{v:+.3f}%" for v in avgs], textposition="outside", textfont=dict(size=9),
        hovertemplate="<b>%{x}</b><br>Oe: %{y:+.3f}%<br>WR: %{customdata[0]:.0f}%<br>n=%{customdata[1]}<extra></extra>",
        customdata=[[t["win_rate"], t["n"]] for t in sorted_tw]))
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")

    # We are here!
    if current_label in labels:
        idx = labels.index(current_label)
        tdom_text = f"We are here! TDOM {current_tdom}" if current_tdom else "We are here!"
        fig.add_annotation(**wah_annotation(
            x_val=current_label, y_val=avgs[idx],
            above=avgs[idx] >= 0, text=tdom_text,
        ))
        fig.add_shape(**wah_rect(
            x0=idx - 0.4, x1=idx + 0.4,
            y0=0, y1=avgs[idx],
        ))

    fig = apply_se_theme(fig, title=f"{ticker} — Two-Week Performance (TDOM 1–{split_day} vs. {split_day+1}+), sortiert", height=450, show_legend=False)
    return fig


def calc_current_month_curve(df, target_month):
    """Berechnet die kumulierte Log-Rendite-Kurve des aktuellen Monats (Start=0, wie Durchschnitt)."""
    current_year = datetime.now().year
    today = pd.Timestamp(datetime.now().date())
    df_tdom = assign_tdom(df)
    month_df = df_tdom[(df_tdom["year"] == current_year) & (df_tdom["month"] == target_month)].copy()
    month_df = month_df[month_df.index <= today]
    if len(month_df) < 2:
        return None, None
    log_rets = month_df["log_return"].values
    cum = np.cumsum(np.insert(log_rets, 0, 0)[:-1])
    curve = (np.exp(cum) - 1) * 100
    return month_df["tdom"].tolist(), curve.tolist()


def build_monthly_heatmap(df, selected_years, ticker):
    """10-Jahres Monats-Renditen Heatmap (wie Jahreszyklus)."""
    current_month = datetime.now().month
    current_year = datetime.now().year

    # Letzte 10 Jahre aus selected_years
    years = sorted(selected_years, reverse=True)[:10]

    z_data = []
    y_labels = []
    for year in years:
        row = []
        for month in range(1, 13):
            mdf = df[(df["year"] == year) & (df["month"] == month)]
            if len(mdf) >= 5:
                ret = (mdf["Close"].iloc[-1] / mdf["Open"].iloc[0] - 1) * 100
            else:
                ret = 0.0
            row.append(round(ret, 2))
        z_data.append(row)
        y_labels.append(str(year))

    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=MONTH_NAMES_DE,
        y=y_labels,
        colorscale=SE_HEATMAP_COLORSCALE,
        zmid=0,
        text=[[f"{v:+.1f}%" for v in row] for row in z_data],
        texttemplate="%{text}",
        textfont=dict(size=11, color=SE_HEATMAP_TEXT_COLOR),
        hovertemplate="<b>%{y} — %{x}</b><br>Rendite: %{z:+.2f}%<extra></extra>",
        colorbar=dict(
            title=dict(text="Rendite %", font=dict(color=SE_COLORS["text_muted"], size=11)),
            tickfont=dict(color=SE_COLORS["text_muted"], size=10),
            ticksuffix="%",
        ),
    ))

    # Gelber Rahmen um aktuelle Zelle (Monat x Jahr)
    if current_year in [int(y) for y in y_labels]:
        fig.add_shape(
            type="rect",
            x0=current_month - 1 - 0.5, x1=current_month - 1 + 0.5,
            y0=y_labels.index(str(current_year)) - 0.5,
            y1=y_labels.index(str(current_year)) + 0.5,
            line=dict(color="#FFD700", width=3.5),
            fillcolor="rgba(0,0,0,0)",
            layer="above",
        )

    fig = apply_se_theme(
        fig,
        title=f"{ticker} — 10 Jahres Monats-Heatmap",
        height=max(400, len(years) * 40 + 100),
        show_legend=False,
    )
    fig.update_yaxes(autorange="reversed", type="category")
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
        selected_month = st.selectbox("Monat auswaehlen", options=list(range(1, 13)),
            index=current_month - 1,
            format_func=lambda m: f"{MONTH_NAMES_DE[m-1]}" + (" <- aktuell" if m == current_month else ""))
        show_live_chart = st.checkbox("Aktuelles Jahr einblenden", value=True, key="mp_live")
        show_individual = st.checkbox("Einzelne Jahre zeigen", value=False, key="mp_indiv")
        show_bands = st.checkbox("Konfidenzband (+-1 Sigma)", value=False, key="mp_bands")

        st.markdown("---")
        st.markdown("### Praesidentenzyklus-Filter")
        cycle_filter = st.multiselect(
            "Zyklusjahre filtern",
            options=list(CYCLE_COLORS.keys()),
            default=None, key="mp_cycle",
            help="Nur Jahre mit bestimmtem Zyklusjahr beruecksichtigen (leer = alle Jahre)"
        )
        st.markdown("---")
        st.markdown("### Two-Week Split")
        split_day = st.slider("Split nach TDOM", 5, 15, 10,
            help="Teilt den Monat: 1st = TDOM 1 bis X, 2nd = TDOM X+1 bis Ende")

        st.markdown("---")
        from shared.outlier_manager import outlier_sidebar
        outlier_method = outlier_sidebar()

    with st.spinner(f"Lade {ticker} Daten..."):
        raw_df = download_data(ticker)
    if raw_df is None or raw_df.empty:
        st.error(f"Keine Daten fuer '{ticker}' gefunden.")
        return
    df = preprocess(raw_df)
    all_years = sorted(df["year"].unique())
    if years_back_is_max:
        selected_years = all_years
    else:
        selected_years = [y for y in all_years if y >= datetime.now().year - int(years_back_raw)]
    if len(selected_years) < 2:
        st.warning("Nicht genuegend Daten.")
        return

    # Outlier-Filter
    from shared.outlier_manager import outlier_info_box
    outlier_info_box([], outlier_method)

    # Presidential Cycle Filter
    if cycle_filter:
        selected_years = [y for y in selected_years
                         if get_presidential_cycle_year(y) in cycle_filter]
        if len(selected_years) < 2:
            st.warning("Nach Zyklusfilter nicht genuegend Jahre uebrig.")
            return
        cycle_info = ", ".join([c.split("(")[1].rstrip(")") for c in cycle_filter])
        st.info(f"**Zyklusfilter aktiv:** {cycle_info} — {len(selected_years)} Jahre")

    month_name = MONTH_NAMES_DE[selected_month - 1]
    current_tdom = get_current_tdom(df) if selected_month == current_month else None

    # 1. Intra-Monat (mit optionalem Live-Overlay)
    tdom_stats, all_curves = calc_intramonth_curve(df, selected_month, selected_years)
    current_month_curve = None
    if show_live_chart and selected_month == current_month:
        cm_tdoms, cm_curve = calc_current_month_curve(df, selected_month)
        if cm_tdoms:
            current_month_curve = (cm_tdoms, cm_curve)
    if tdom_stats:
        st.plotly_chart(build_intramonth_chart(tdom_stats, all_curves, ticker, month_name,
            show_individual, show_bands, current_tdom,
            current_month_curve=current_month_curve), use_container_width=True)

        # 1b. Detrend-Indikator (Expander, wie Jahreszyklus)
        with st.expander("Detrend-Indikator / Saisonaler Druck", expanded=True):
            detrend_fig = build_detrend_chart(tdom_stats, ticker, month_name, current_tdom)
            if detrend_fig:
                st.plotly_chart(detrend_fig, use_container_width=True)
                st.caption("_Steigt die Linie → ueberdurchschnittlicher saisonaler Kaufdruck. "
                          "Faellt sie → saisonaler Verkaufsdruck (auch wenn der Monat insgesamt steigt)._")

    # 2. Wochen
    weekly_stats = calc_weekly_performance(df, selected_month, selected_years)
    if weekly_stats:
        fig = build_weekly_bars(weekly_stats, ticker, month_name, current_tdom)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    # 3. Monats-Jahresuebersicht
    st.markdown("---")
    st.plotly_chart(build_monthly_bars(calc_monthly_performance(df, selected_years), ticker, current_tdom), use_container_width=True)
    with st.expander("Monats-Detailtabelle"):
        mstats = calc_monthly_performance(df, selected_years)
        st.dataframe(pd.DataFrame([{"Monat": MONTH_NAMES_DE[m["month"]-1], "Oe Rendite": f"{m['avg']:+.3f}%",
            "Median": f"{m['median']:+.3f}%", "Win Rate": f"{m['win_rate']:.0f}%", "n": m["n"]} for m in mstats]),
            use_container_width=True, hide_index=True)

    # 4. Two-Week
    st.markdown("---")
    st.markdown(f"### Two-Week Performance (Split: TDOM {split_day})")
    tw_valid = [t for t in calc_two_week_performance(df, selected_years, split_day) if t["n"] >= 2]
    if tw_valid:
        st.plotly_chart(build_two_week_bars(tw_valid, ticker, split_day, current_tdom), use_container_width=True)
        with st.expander("Two-Week Detailtabelle"):
            tw_sorted = sorted(tw_valid, key=lambda x: x["avg"], reverse=True)
            st.dataframe(pd.DataFrame([{"Periode": t["label"], "Monat": MONTH_NAMES_DE[t["month"]-1],
                "Haelfte": "1st" if t["half"] == 1 else "2nd", "Oe Rendite": f"{t['avg']:+.3f}%",
                "Win Rate": f"{t['win_rate']:.0f}%", "n": t["n"]} for t in tw_sorted]),
                use_container_width=True, hide_index=True)

    # 5. 10-Jahres Heatmap
    st.markdown("---")
    with st.expander("10 Jahres Monats-Heatmap", expanded=True):
        st.plotly_chart(build_monthly_heatmap(df, selected_years, ticker), use_container_width=True)

main()

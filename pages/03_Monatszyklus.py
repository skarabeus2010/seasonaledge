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

from shared.ticker_select import ticker_select
from shared.constants import (
    DEFAULT_TICKER, DEFAULT_YEARS, MONTH_NAMES_DE, CYCLE_COLORS,
    SE_COLORS, SE_HEATMAP_COLORSCALE, SE_HEATMAP_TEXT_COLOR,
)
from shared.data import download_data, preprocess
from shared.calculations import get_presidential_cycle_year
from shared.charts import apply_se_theme
from shared.we_are_here import annotation as wah_annotation, rect as wah_rect, vline as wah_vline

from shared.info_badge import render_info_badge
from shared.design import inject_se_css
from shared.footer import render_footer
inject_se_css()

# ── Distinkte Farbpalette fuer Einzeljahre (maximaler Kontrast) ──────
INDIVIDUAL_COLORS = [
    "#FF6B6B", "#00CEC9", "#FFE66D", "#A29BFE", "#FF9FF3",
    "#1ABC9C", "#F39C12", "#3498DB", "#E74C3C", "#2ECC71",
    "#E84393", "#00B894", "#FDCB6E", "#6C5CE7", "#FD79A8",
    "#0984E3", "#D63031", "#00D2D3", "#EE5A24", "#C8D6E5",
]

def _heatmap_text_color(value, zmid=0, max_abs=1):
    intensity = abs(value - zmid) / max_abs if max_abs > 0 else 0
    if value > zmid and intensity > 0.3:
        return "#1a1a2e"
    if value < zmid and intensity > 0.6:
        return "#f0f0f0"
    return "#FFFFFF"


def _add_heatmap_annotations(fig, z_data, x_labels, y_labels, zmid=0, fmt="+.2f", suffix="%"):
    flat = [v for row in z_data for v in row]
    max_abs = max(abs(v - zmid) for v in flat) if flat else 1
    for i, y_label in enumerate(y_labels):
        for j, x_label in enumerate(x_labels):
            val = z_data[i][j]
            color = _heatmap_text_color(val, zmid, max_abs)
            fig.add_annotation(x=x_label, y=y_label, text=f"{val:{fmt}}{suffix}",
                showarrow=False, font=dict(size=10, color=color))


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
    """
    Detrend-Indikator: Saisonaler Intra-Monat-Verlauf ohne Trendkomponente.

    Der lineare Trend wird subtrahiert. Was bleibt ist die reine saisonale
    Schwankung innerhalb des Monats. Skalierung 0–100, Midline 50.
    """
    tdoms = sorted(tdom_stats.keys())
    avg_curve = [tdom_stats[t]["avg"] for t in tdoms]

    if len(avg_curve) < 3:
        return None

    n = len(avg_curve)
    end_val = avg_curve[-1]
    daily_drift = end_val / n
    raw = [avg_curve[i] - ((i + 1) * daily_drift) for i in range(n)]

    # Skalierung auf 0–100 (Midline = 50)
    r_min, r_max = min(raw), max(raw)
    r_range = r_max - r_min
    if r_range == 0:
        detrended = [50.0] * n
    else:
        detrended = [((v - r_min) / r_range) * 100 for v in raw]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=tdoms, y=detrended, mode="lines+markers",
        line=dict(color="#FF6B6B", width=2.5),
        marker=dict(size=4, color="#FF6B6B"),
        name="Saisonaler Druck",
        hovertemplate="TDOM %{x}<br>Wert: %{y:.1f}<extra></extra>"
    ))

    # Midline bei 50
    fig.add_hline(y=50, line_dash="dash", line_color="rgba(255,255,255,0.3)", line_width=1)

    # We are here!
    if current_tdom is not None and current_tdom in tdoms:
        idx = tdoms.index(current_tdom)
        fig.add_shape(**wah_vline(current_tdom))
        fig.add_annotation(**wah_annotation(
            x_val=current_tdom, y_val=detrended[idx],
            above=True, text=f"We are here! TDOM {current_tdom}",
        ))

    n_years = tdom_stats[1]["n"] if 1 in tdom_stats else 0
    fig = apply_se_theme(fig, title=f"{ticker} — {month_name} Detrend-Indikator ({n_years} Jahre)", height=300, show_legend=False)
    fig.update_xaxes(range=[min(tdoms) - 0.5, max(tdoms) + 0.5])
    fig.update_yaxes(range=[0, 100], dtick=25)
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

    fig = apply_se_theme(fig, title=f"{ticker} — Monats-Performance (Jahresübersicht)", height=400, show_legend=False)
    return fig

def build_two_week_bars(tw_stats, ticker, split_day, current_tdom):
    today = datetime.now()
    current_half = "1st" if (current_tdom or 1) <= split_day else "2nd"
    current_label = f"{today.month:02d}/{current_half}"
    sorted_tw = sorted(tw_stats, key=lambda x: x["avg"], reverse=True)
    labels = [t["label"] for t in sorted_tw]
    avgs = [t["avg"] for t in sorted_tw]
    colors = [SE_COLORS["positive"] if v >= 0 else SE_COLORS["negative"] for v in avgs]

    # Mindest-Balkenhöhe damit auch Werte nahe 0 sichtbar + hoverbar bleiben
    min_height = 0.04
    display_avgs = [v if abs(v) >= min_height else (min_height if v >= 0 else -min_height) for v in avgs]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=display_avgs,
        marker_color=colors,
        text=[f"{v:+.3f}%" for v in avgs], textposition="outside", textfont=dict(size=9),
        hovertemplate="<b>%{x}</b><br>Ø: %{customdata[0]:+.3f}%<br>WR: %{customdata[1]:.0f}%<br>n=%{customdata[2]}<extra></extra>",
        customdata=[[t["avg"], t["win_rate"], t["n"]] for t in sorted_tw]))
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


def calc_seasonal_match(tdom_stats, current_month_curve, all_curves):
    """
    Berechnet Korrelation, DTW-Score und t-Test zwischen aktuellem Monat und saisonalem Durchschnitt.

    Returns:
        dict mit correlation, dtw_score, t_stat, p_value, cohens_d, current_return, avg_return, n_years
        oder None wenn nicht genug Daten
    """
    if current_month_curve is None:
        return None
    cm_tdoms, cm_curve = current_month_curve
    if not cm_tdoms or len(cm_tdoms) < 3:
        return None

    # Durchschnittskurve auf gleiche TDOMs trimmen
    tdoms_common = [t for t in cm_tdoms if t in tdom_stats]
    if len(tdoms_common) < 3:
        return None

    avg_vals = np.array([tdom_stats[t]["avg"] for t in tdoms_common])
    cur_vals = np.array([cm_curve[cm_tdoms.index(t)] for t in tdoms_common])

    # 1. Pearson-Korrelation
    if np.std(cur_vals) == 0 or np.std(avg_vals) == 0:
        correlation = 0.0
    else:
        correlation = float(np.corrcoef(cur_vals, avg_vals)[0, 1])
        if np.isnan(correlation):
            correlation = 0.0

    # 2. DTW-Score (normalisiert auf 0-1, 1 = perfekter Match)
    try:
        from fastdtw import fastdtw
        from scipy.spatial.distance import euclidean
        dist, _ = fastdtw(cur_vals, avg_vals, dist=euclidean)
        # Normalisieren: DTW-Distanz relativ zur Amplitude
        amplitude = max(np.ptp(avg_vals), 0.1)
        dtw_score = max(0, 1 - dist / (amplitude * len(tdoms_common)))
    except ImportError:
        # Fallback: Score aus Korrelation ableiten
        dtw_score = max(0, (correlation + 1) / 2)

    # 3. t-Test: Liegt der aktuelle Return im historischen Bereich?
    hist_final_returns = [c["total_return"] for c in all_curves if len(c["curve"]) > 0]
    current_return = cm_curve[-1] if cm_curve else 0
    n_years = len(hist_final_returns)

    if n_years >= 5 and np.std(hist_final_returns) > 0:
        from scipy import stats
        arr = np.array(hist_final_returns)
        # z-Score: wie viele Standardabweichungen ist der aktuelle Return vom Durchschnitt entfernt?
        avg_return = float(np.mean(arr))
        std_return = float(np.std(arr, ddof=1))
        cohens_d = abs(current_return - avg_return) / std_return if std_return > 0 else 0
        # t-Test: ist der aktuelle Wert signifikant anders als der historische Durchschnitt?
        t_stat = (current_return - avg_return) / (std_return / np.sqrt(n_years))
        p_value = float(2 * (1 - stats.t.cdf(abs(t_stat), df=n_years - 1)))
    else:
        avg_return = float(np.mean(hist_final_returns)) if hist_final_returns else 0
        cohens_d = 0
        t_stat = 0
        p_value = 1.0

    return {
        "correlation": round(correlation, 3),
        "dtw_score": round(dtw_score, 3),
        "t_stat": round(t_stat, 3),
        "p_value": round(p_value, 4),
        "cohens_d": round(cohens_d, 3),
        "current_return": round(current_return, 3),
        "avg_return": round(avg_return, 3),
        "n_years": n_years,
    }


def render_seasonal_match(match, ticker, month_name):
    """Rendert die Seasonal-Match Analyse als Expander."""
    import streamlit as st
    from shared.significance_gauge import build_gauge

    if match is None:
        return

    _PLOTLY_CFG = {"displayModeBar": False, "scrollZoom": False}

    with st.expander("📊 Saisonaler Match — Aktuell vs. Durchschnitt", expanded=True):
        render_info_badge("seasonal_match")
        col1, col2, col3 = st.columns(3)

        # Korrelation Gauge
        corr_score = max(0, (match["correlation"] + 1) / 2)  # -1..+1 → 0..1
        with col1:
            st.markdown(
                "<p style='text-align:center; color:#c8d6e5; font-weight:600; "
                "font-size:13px; margin-bottom:2px;'>Korrelation</p>",
                unsafe_allow_html=True)
            st.plotly_chart(build_gauge(corr_score), use_container_width=True, config=_PLOTLY_CFG, key="match_corr")
            corr_col = "#00d4aa" if match["correlation"] > 0.5 else "#e8a425" if match["correlation"] > 0 else "#ff4757"
            st.markdown(
                f"<p style='text-align:center; margin-top:-12px; font-size:12px;'>"
                f"<span style='color:{corr_col}; font-weight:700;'>r = {match['correlation']:+.2f}</span></p>",
                unsafe_allow_html=True)

        # DTW Shape-Score Gauge
        with col2:
            st.markdown(
                "<p style='text-align:center; color:#c8d6e5; font-weight:600; "
                "font-size:13px; margin-bottom:2px;'>Shape-Match (DTW)</p>",
                unsafe_allow_html=True)
            st.plotly_chart(build_gauge(match["dtw_score"]), use_container_width=True, config=_PLOTLY_CFG, key="match_dtw")
            dtw_col = "#00d4aa" if match["dtw_score"] > 0.7 else "#e8a425" if match["dtw_score"] > 0.4 else "#ff4757"
            dtw_pct = match["dtw_score"] * 100
            st.markdown(
                f"<p style='text-align:center; margin-top:-12px; font-size:12px;'>"
                f"<span style='color:{dtw_col}; font-weight:700;'>{dtw_pct:.0f}% Match</span></p>",
                unsafe_allow_html=True)

        # Signifikanz Gauge
        with col3:
            sig_score = max(0, 1 - match["p_value"])
            if match["p_value"] < 0.05:
                sig_label, sig_col = "Signifikant abweichend", "#ff4757"
            elif match["p_value"] < 0.10:
                sig_label, sig_col = "Grenzwertig", "#e8a425"
            else:
                sig_label, sig_col = "Im Normalbereich", "#00d4aa"
            st.markdown(
                "<p style='text-align:center; color:#c8d6e5; font-weight:600; "
                "font-size:13px; margin-bottom:2px;'>Abweichungstest</p>",
                unsafe_allow_html=True)
            st.plotly_chart(build_gauge(sig_score), use_container_width=True, config=_PLOTLY_CFG, key="match_sig")
            st.markdown(
                f"<p style='text-align:center; margin-top:-12px; font-size:12px;'>"
                f"<span style='color:{sig_col}; font-weight:700;'>{sig_label}</span>"
                f"<br><span style='color:#8899aa; font-size:11px;'>p={match['p_value']:.3f}  "
                f"d={match['cohens_d']:.2f}</span></p>",
                unsafe_allow_html=True)

        # Kontext-Zeile
        sign = "+" if match["current_return"] >= 0 else ""
        sign_avg = "+" if match["avg_return"] >= 0 else ""
        st.markdown(
            f"<p style='color:#c8d6e5; font-size:12px; text-align:center; margin-top:8px;'>"
            f"Aktuell: <b style='color:#F1C40F;'>{sign}{match['current_return']:.2f}%</b> &nbsp;|&nbsp; "
            f"Saisonaler Oe: <b style='color:#00CED1;'>{sign_avg}{match['avg_return']:.2f}%</b> &nbsp;|&nbsp; "
            f"Basis: <b>{match['n_years']}</b> Jahre</p>",
            unsafe_allow_html=True)

        # Erklaerungstext
        st.markdown("---")
        st.markdown(
            "<div style='color:#FFFFFF; font-size:12px; line-height:1.6;'>"
            "<b>So liest du die Zahlen:</b><br>"
            "<b>Korrelation (r)</b> — Misst, ob sich der aktuelle Monat in die gleiche Richtung "
            "bewegt wie der saisonale Durchschnitt. "
            "r = +1.0 bedeutet perfekte Uebereinstimmung, r = 0 kein Zusammenhang, r = -1.0 genau gegenläufig. "
            "Werte ueber +0.5 deuten auf einen starken saisonalen Match hin.<br>"
            "<b>Shape-Match (DTW)</b> — Dynamic Time Warping vergleicht die Form der beiden Kurven, "
            "auch bei leichten Zeitverschiebungen. 100% = identischer Verlauf, unter 40% = kaum Aehnlichkeit.<br>"
            "<b>Abweichungstest</b> — Prueft per t-Test, ob der aktuelle Monatsreturn statistisch im "
            "Normalbereich der historischen Verteilung liegt. <span style='color:#00d4aa;'>Im Normalbereich</span> "
            "= der aktuelle Monat verhält sich typisch. <span style='color:#ff4757;'>Signifikant abweichend</span> "
            "= der aktuelle Verlauf ist ungewoehnlich (p&lt;0.05). Cohen's d misst die Effektstaerke "
            "(d&gt;0.8 = grosse Abweichung)."
            "</div>",
            unsafe_allow_html=True)


def calc_cycle_match(df, target_month, selected_years, current_month_curve):
    """
    Vergleicht den aktuellen Monatsverlauf mit jedem Praesidentenzyklus-Jahr (1-4)
    und dem Gesamtdurchschnitt. Berechnet Korrelation + DTW fuer jedes.

    Returns:
        list[dict] sortiert nach Match-Score (beste zuerst)
    """
    if current_month_curve is None:
        return None
    cm_tdoms, cm_curve = current_month_curve
    if not cm_tdoms or len(cm_tdoms) < 3:
        return None

    df_tdom = assign_tdom(df)
    results = []

    # Alle Zyklusjahre + Gesamt
    cycle_groups = {name: [] for name in CYCLE_COLORS.keys()}
    cycle_groups["Alle Jahre"] = selected_years

    for cycle_name in CYCLE_COLORS.keys():
        cycle_groups[cycle_name] = [y for y in selected_years
                                     if get_presidential_cycle_year(y) == cycle_name]

    for group_name, years in cycle_groups.items():
        if len(years) < 3:
            continue

        # Durchschnittskurve fuer diese Gruppe berechnen
        curves = []
        for year in years:
            month_df = df_tdom[(df_tdom["year"] == year) & (df_tdom["month"] == target_month)].copy()
            if len(month_df) < 10:
                continue
            log_rets = month_df["log_return"].values
            cum = np.cumsum(np.insert(log_rets, 0, 0)[:-1])
            curve = (np.exp(cum) - 1) * 100
            tdoms = month_df["tdom"].tolist()
            curves.append({"tdoms": tdoms, "curve": curve.tolist()})

        if len(curves) < 3:
            continue

        # Durchschnittskurve auf gemeinsame TDOMs
        common_tdoms = [t for t in cm_tdoms if all(t in c["tdoms"] for c in curves)]
        if len(common_tdoms) < 3:
            continue

        avg_vals = []
        for t in common_tdoms:
            vals = [c["curve"][c["tdoms"].index(t)] for c in curves if t in c["tdoms"]]
            avg_vals.append(np.mean(vals))
        avg_vals = np.array(avg_vals)
        cur_vals = np.array([cm_curve[cm_tdoms.index(t)] for t in common_tdoms])

        # Korrelation
        if np.std(cur_vals) == 0 or np.std(avg_vals) == 0:
            corr = 0.0
        else:
            corr = float(np.corrcoef(cur_vals, avg_vals)[0, 1])
            if np.isnan(corr):
                corr = 0.0

        # DTW
        try:
            from fastdtw import fastdtw
            from scipy.spatial.distance import euclidean
            dist, _ = fastdtw(cur_vals, avg_vals, dist=euclidean)
            amplitude = max(np.ptp(avg_vals), 0.1)
            dtw_score = max(0, 1 - dist / (amplitude * len(common_tdoms)))
        except ImportError:
            dtw_score = max(0, (corr + 1) / 2)

        # Kombi-Score: 60% Korrelation + 40% DTW
        match_score = 0.6 * max(0, (corr + 1) / 2) + 0.4 * dtw_score

        # Kurzname
        short_name = group_name.split("(")[1].rstrip(")") if "(" in group_name else group_name
        color = CYCLE_COLORS.get(group_name, SE_COLORS["accent_blue"])

        results.append({
            "name": short_name,
            "full_name": group_name,
            "correlation": round(corr, 3),
            "dtw_score": round(dtw_score, 3),
            "match_score": round(match_score, 3),
            "n_years": len(curves),
            "color": color,
        })

    # Feste Reihenfolge: Post-Election, Midterm, Pre-Election, Election, Alle Jahre
    fixed_order = ["Post-Election", "Midterm Election", "Pre-Election", "Election Year", "Alle Jahre"]
    order_map = {name: i for i, name in enumerate(fixed_order)}
    results.sort(key=lambda x: order_map.get(x["name"], 99))
    return results


def render_cycle_match(cycle_results, ticker, month_name):
    """Rendert den Präsidentenzyklus Best-Match als Expander."""
    import streamlit as st
    from shared.significance_gauge import build_gauge

    if not cycle_results:
        return

    _PLOTLY_CFG = {"displayModeBar": False, "scrollZoom": False}

    with st.expander("🏛️ Präsidentenzyklus — Best Match", expanded=True):
        render_info_badge("praesidentenzyklus_match")
        # Bester Match ermitteln (hoechster Score)
        best = max(cycle_results, key=lambda x: x["match_score"])
        st.markdown(
            f"<p style='color:#FFFFFF; font-size:14px; text-align:center; margin-bottom:16px;'>"
            f"Bester Match: <b style='color:{best['color']};'>{best['name']}</b> "
            f"(r={best['correlation']:+.2f}, DTW {best['dtw_score']*100:.0f}%, "
            f"n={best['n_years']} Jahre)</p>",
            unsafe_allow_html=True)

        # Ranking nach Score fuer Medaillen
        ranked = sorted(cycle_results, key=lambda x: x["match_score"], reverse=True)
        rank_map = {r["name"]: i for i, r in enumerate(ranked)}

        cols = st.columns(len(cycle_results))
        for i, (col, r) in enumerate(zip(cols, cycle_results)):
            with col:
                pos = rank_map[r["name"]]
                rank = "🥇" if pos == 0 else "🥈" if pos == 1 else "🥉" if pos == 2 else f"#{pos+1}"
                st.markdown(
                    f"<p style='text-align:center; color:{r['color']}; font-weight:700; "
                    f"font-size:13px; margin-bottom:2px;'>{rank} {r['name']}</p>",
                    unsafe_allow_html=True)
                st.plotly_chart(build_gauge(r["match_score"]),
                    use_container_width=True, config=_PLOTLY_CFG,
                    key=f"cycle_gauge_{i}")
                corr_col = "#00d4aa" if r["correlation"] > 0.5 else "#e8a425" if r["correlation"] > 0 else "#ff4757"
                st.markdown(
                    f"<p style='text-align:center; margin-top:-12px; font-size:11px;'>"
                    f"<span style='color:{corr_col};'>r={r['correlation']:+.2f}</span> · "
                    f"DTW {r['dtw_score']*100:.0f}%"
                    f"<br><span style='color:#8899aa;'>n={r['n_years']}</span></p>",
                    unsafe_allow_html=True)

        # Erklaerungstext
        st.markdown("---")
        st.markdown(
            "<div style='color:#FFFFFF; font-size:12px; line-height:1.6;'>"
            "<b>So liest du die Ergebnisse:</b><br>"
            "Für jedes Präsidentenzyklus-Jahr (Post-Election, Midterm, Pre-Election, Election) "
            "wird der historische Durchschnittsverlauf des aktuellen Monats berechnet und mit "
            "dem tatsächlichen Verlauf verglichen. "
            "Der <b>Match-Score</b> kombiniert Korrelation (60%) und Shape-Match/DTW (40%). "
            "Das Zyklusjahr mit dem hoechsten Score zeigt, welchem historischen Muster "
            "der aktuelle Monat am staerksten folgt."
            "</div>",
            unsafe_allow_html=True)


# ── TWO-WEEK ERWEITERTE ANALYSEN ─────────────────────────

def build_two_week_heatmap(tw_stats, ticker, split_day, current_tdom):
    """12x2 Heatmap: Monate x Hälften — Wo liegt das Geld im Jahr?"""
    today = datetime.now()
    current_half = 1 if (current_tdom or 1) <= split_day else 2

    # Matrix aufbauen: Zeilen = Hälften, Spalten = Monate
    z_data = [[], []]  # [0]=1st half, [1]=2nd half
    for month in range(1, 13):
        for half_idx, half in enumerate([1, 2]):
            match = [t for t in tw_stats if t["month"] == month and t["half"] == half]
            val = match[0]["avg"] if match else 0
            z_data[half_idx].append(round(val, 3))

    y_labels_tw = [f"1st (TDOM 1-{split_day})", f"2nd (TDOM {split_day+1}+)"]
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=MONTH_NAMES_DE,
        y=y_labels_tw,
        colorscale=SE_HEATMAP_COLORSCALE,
        zmid=0,
        hovertemplate="<b>%{x} — %{y}</b><br>Oe Rendite: %{z:+.3f}%<extra></extra>",
        colorbar=dict(
            title=dict(text="Rendite %", font=dict(color=SE_COLORS["text_muted"], size=11)),
            tickfont=dict(color=SE_COLORS["text_muted"], size=10),
            ticksuffix="%",
        ),
    ))

    _add_heatmap_annotations(fig, z_data, MONTH_NAMES_DE, y_labels_tw, zmid=0)

    # Gelber Rahmen um aktuelle Zelle
    half_idx = 0 if current_half == 1 else 1
    fig.add_shape(
        type="rect",
        x0=today.month - 1 - 0.5, x1=today.month - 1 + 0.5,
        y0=half_idx - 0.5, y1=half_idx + 0.5,
        line=dict(color="#FFD700", width=3.5),
        fillcolor="rgba(0,0,0,0)", layer="above",
    )

    fig = apply_se_theme(fig, title=f"{ticker} — Two-Week Heatmap (Ø Rendite je Monatshälfte)", height=250, show_legend=False)
    fig.update_yaxes(type="category")
    return fig


def calc_two_week_current_year(df, split_day):
    """Berechnet Two-Week Returns des aktuellen Jahres fuer Overlay."""
    current_year = datetime.now().year
    today = pd.Timestamp(datetime.now().date())
    df_tdom = assign_tdom(df)
    results = []
    for month in range(1, 13):
        for half in [1, 2]:
            mdf = df_tdom[(df_tdom["year"] == current_year) & (df_tdom["month"] == month)].copy()
            mdf = mdf[mdf.index <= today]
            if len(mdf) < 3:
                continue
            hdf = mdf[mdf["tdom"] <= split_day] if half == 1 else mdf[mdf["tdom"] > split_day]
            if len(hdf) >= 2:
                ret = (hdf["Close"].iloc[-1] / hdf["Open"].iloc[0] - 1) * 100
                suffix = "1st" if half == 1 else "2nd"
                results.append({"label": f"{month:02d}/{suffix}", "month": month,
                                "half": half, "avg": ret})
    return results if results else None


def build_two_week_overlay(tw_stats, tw_current, ticker, split_day, current_tdom):
    """Two-Week Bars mit aktuellem Jahr als Overlay-Markers."""
    today = datetime.now()
    current_half = "1st" if (current_tdom or 1) <= split_day else "2nd"
    current_label = f"{today.month:02d}/{current_half}"

    # Chronologische Reihenfolge
    tw_chrono = sorted(tw_stats, key=lambda x: (x["month"], x["half"]))
    labels = [t["label"] for t in tw_chrono]
    avgs = [t["avg"] for t in tw_chrono]
    colors = [SE_COLORS["positive"] if v >= 0 else SE_COLORS["negative"] for v in avgs]

    fig = go.Figure()
    # Historischer Durchschnitt als Bars
    fig.add_trace(go.Bar(x=labels, y=avgs, marker_color=colors, name="Historisch Oe",
        opacity=0.6, hovertemplate="<b>%{x}</b><br>Hist. Oe: %{y:+.3f}%<extra></extra>"))

    # Aktuelles Jahr als Linie/Markers
    cur_labels = [c["label"] for c in tw_current]
    cur_vals = [c["avg"] for c in tw_current]
    fig.add_trace(go.Scatter(x=cur_labels, y=cur_vals, mode="lines+markers",
        line=dict(color="#F1C40F", width=2.5),
        marker=dict(size=8, color="#F1C40F", symbol="diamond"),
        name=f"{today.year} (aktuell)",
        hovertemplate=f"<b>%{{x}}</b><br>{today.year}: %{{y:+.3f}}%<extra></extra>"))

    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")

    # We are here!
    if current_label in labels:
        idx = labels.index(current_label)
        fig.add_shape(**wah_vline(current_label))
        fig.add_annotation(**wah_annotation(
            x_val=current_label, y_val=avgs[idx],
            above=True, text=f"We are here! TDOM {current_tdom}",
        ))

    fig = apply_se_theme(fig, title=f"{ticker} — Two-Week: {today.year} vs. Historisch", height=400)
    return fig


def build_two_week_ranking(tw_stats, ticker, split_day):
    """Horizontale Bars: alle 24 Perioden nach Rendite sortiert."""
    tw_sorted = sorted(tw_stats, key=lambda x: x["avg"], reverse=True)
    labels = [f"{MONTH_NAMES_DE[t['month']-1]} {'1st' if t['half'] == 1 else '2nd'}" for t in tw_sorted]
    avgs = [t["avg"] for t in tw_sorted]
    colors = [SE_COLORS["positive"] if v >= 0 else SE_COLORS["negative"] for v in avgs]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=labels, x=avgs, orientation="h",
        marker_color=colors,
        text=[f"{v:+.3f}% (WR {t['win_rate']:.0f}%)" for v, t in zip(avgs, tw_sorted)],
        textposition="outside", textfont=dict(size=10),
        hovertemplate="<b>%{y}</b><br>Oe: %{x:+.3f}%<extra></extra>",
    ))
    fig.add_vline(x=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")

    fig = apply_se_theme(fig,
        title=f"{ticker} — Best Two-Weeks Ranking (TDOM Split {split_day})",
        height=max(500, len(labels) * 22 + 100), show_legend=False)
    fig.update_yaxes(autorange="reversed")
    return fig


def render_momentum_check(df, selected_years, split_day):
    """Zeigt bedingte Wahrscheinlichkeit: Wenn 1st Half pos/neg → was macht 2nd Half?"""
    df_tdom = assign_tdom(df)
    pos_pos, pos_neg, neg_pos, neg_neg = 0, 0, 0, 0
    total = 0

    for year in selected_years:
        for month in range(1, 13):
            mdf = df_tdom[(df_tdom["year"] == year) & (df_tdom["month"] == month)].copy()
            if len(mdf) < 10:
                continue
            h1 = mdf[mdf["tdom"] <= split_day]
            h2 = mdf[mdf["tdom"] > split_day]
            if len(h1) < 3 or len(h2) < 3:
                continue
            ret1 = (h1["Close"].iloc[-1] / h1["Open"].iloc[0] - 1) * 100
            ret2 = (h2["Close"].iloc[-1] / h2["Open"].iloc[0] - 1) * 100
            total += 1
            if ret1 > 0 and ret2 > 0:
                pos_pos += 1
            elif ret1 > 0 and ret2 <= 0:
                pos_neg += 1
            elif ret1 <= 0 and ret2 > 0:
                neg_pos += 1
            else:
                neg_neg += 1

    if total < 10:
        st.info("Nicht genügend Daten für den Momentum-Check.")
        return

    pos_total = pos_pos + pos_neg
    neg_total = neg_pos + neg_neg

    col1, col2 = st.columns(2)
    with col1:
        pct = pos_pos / pos_total * 100 if pos_total > 0 else 0
        color = "#00d4aa" if pct >= 55 else "#e8a425" if pct >= 45 else "#ff4757"
        st.markdown(
            f"<div style='background:rgba(0,212,170,0.08); border:1px solid rgba(0,212,170,0.3); "
            f"border-radius:12px; padding:16px; text-align:center;'>"
            f"<p style='color:#FFFFFF; font-size:13px; margin:0 0 8px 0;'>"
            f"Wenn 1st Half <b style='color:#00d4aa;'>positiv</b></p>"
            f"<p style='color:{color}; font-size:28px; font-weight:800; margin:0;'>"
            f"{pct:.0f}%</p>"
            f"<p style='color:#8899aa; font-size:11px; margin:4px 0 0 0;'>"
            f"dann auch 2nd Half positiv ({pos_pos}/{pos_total})</p></div>",
            unsafe_allow_html=True)

    with col2:
        pct = neg_neg / neg_total * 100 if neg_total > 0 else 0
        color = "#ff4757" if pct >= 55 else "#e8a425" if pct >= 45 else "#00d4aa"
        st.markdown(
            f"<div style='background:rgba(255,71,87,0.08); border:1px solid rgba(255,71,87,0.3); "
            f"border-radius:12px; padding:16px; text-align:center;'>"
            f"<p style='color:#FFFFFF; font-size:13px; margin:0 0 8px 0;'>"
            f"Wenn 1st Half <b style='color:#ff4757;'>negativ</b></p>"
            f"<p style='color:{color}; font-size:28px; font-weight:800; margin:0;'>"
            f"{pct:.0f}%</p>"
            f"<p style='color:#8899aa; font-size:11px; margin:4px 0 0 0;'>"
            f"dann auch 2nd Half negativ ({neg_neg}/{neg_total})</p></div>",
            unsafe_allow_html=True)

    # Erklaerungstext
    st.markdown(
        "<p style='color:#FFFFFF; font-size:12px; margin-top:12px; line-height:1.6;'>"
        "<b>Interpretation:</b> Zeigt, ob es innerhalb eines Monats Momentum gibt. "
        "Werte über 55% deuten auf Trendkontinuation hin — eine positive erste Hälfte "
        "zieht oft eine positive zweite nach sich (und umgekehrt). "
        f"Basis: {total} Monatshälften.</p>",
        unsafe_allow_html=True)


def render_two_week_significance(df, selected_years, split_day):
    """t-Test + Gauge fuer jede Monatshälfte (1st vs 2nd)."""
    from scipy import stats
    from shared.significance_gauge import build_gauge

    _PLOTLY_CFG = {"displayModeBar": False, "scrollZoom": False}
    df_tdom = assign_tdom(df)

    halves = [
        ("1st Half", f"TDOM 1-{split_day}", 1),
        ("2nd Half", f"TDOM {split_day+1}+", 2),
    ]

    cols = st.columns(2)
    for col, (name, desc, half_id) in zip(cols, halves):
        rets = []
        for year in selected_years:
            for month in range(1, 13):
                mdf = df_tdom[(df_tdom["year"] == year) & (df_tdom["month"] == month)].copy()
                if len(mdf) < 10:
                    continue
                hdf = mdf[mdf["tdom"] <= split_day] if half_id == 1 else mdf[mdf["tdom"] > split_day]
                if len(hdf) >= 3:
                    rets.append((hdf["Close"].iloc[-1] / hdf["Open"].iloc[0] - 1) * 100)

        with col:
            if len(rets) < 10:
                st.info(f"Nicht genügend Daten für {name}.")
                continue

            arr = np.array(rets)
            t_stat, p_value = stats.ttest_1samp(arr, 0)
            cohens_d = abs(np.mean(arr)) / np.std(arr, ddof=1) if np.std(arr, ddof=1) > 0 else 0
            sig_score = max(0, min(1, 1 - p_value))

            if p_value < 0.05:
                sig_label, sig_col = "Signifikant", "#00d4aa"
            elif p_value < 0.10:
                sig_label, sig_col = "Grenzwertig", "#e8a425"
            else:
                sig_label, sig_col = "Nicht signifikant", "#ff4757"

            avg_ret = np.mean(arr)
            avg_col = "#00d4aa" if avg_ret > 0 else "#ff4757"

            st.markdown(
                f"<p style='text-align:center; color:#FFFFFF; font-weight:700; "
                f"font-size:14px; margin-bottom:2px;'>{name} ({desc})</p>",
                unsafe_allow_html=True)
            st.plotly_chart(build_gauge(sig_score), use_container_width=True,
                            config=_PLOTLY_CFG, key=f"tw_sig_{half_id}")
            st.markdown(
                f"<p style='text-align:center; margin-top:-12px; font-size:12px;'>"
                f"<span style='color:{sig_col}; font-weight:700;'>{sig_label}</span>"
                f"<br><span style='color:{avg_col};'>Oe {avg_ret:+.3f}%</span> · "
                f"p={p_value:.3f} · d={cohens_d:.2f}"
                f"<br><span style='color:#8899aa; font-size:11px;'>n={len(rets)}</span></p>",
                unsafe_allow_html=True)

    st.markdown(
        "<p style='color:#FFFFFF; font-size:12px; margin-top:12px; line-height:1.6;'>"
        "<b>Interpretation:</b> Der t-Test prueft, ob die durchschnittliche Rendite "
        "einer Monatshälfte signifikant von Null abweicht. "
        "<span style='color:#00d4aa;'>Signifikant</span> (p&lt;0.05) = "
        "die Hälfte hat einen statistisch nachweisbaren Rendite-Bias. "
        "Cohen's d misst die Effektstärke (d&gt;0.2 = klein, d&gt;0.5 = mittel, d&gt;0.8 = groß).</p>",
        unsafe_allow_html=True)


def build_monthly_heatmap(df, selected_years, ticker):
    """10-Jahres Monats-Renditen Heatmap (identisch mit Jahreszyklus-Variante)."""
    from shared.constants import SE_HEATMAP_TEXT_COLOR
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

    fig = apply_se_theme(
        fig,
        title=f"{ticker} — 10 Jahres Monats-Heatmap",
        height=max(300, len(years) * 28 + 100),
        show_legend=False,
    )
    fig.update_yaxes(autorange="reversed", dtick=1)
    return fig


# ── MAIN ──────────────────────────────────────────────────

def main():
    with st.sidebar:
        st.markdown("## 📆 Monats- & Wochen-Performance")
        st.markdown("---")
        ticker = ticker_select(key="mp_ticker", default=DEFAULT_TICKER)
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

        st.markdown("---")
        from shared.outlier_manager import outlier_sidebar
        outlier_method = outlier_sidebar()

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

    # Outlier-Filter
    from shared.outlier_manager import outlier_info_box
    outlier_info_box([], outlier_method)

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

        # ── Perzentil-Statusbar ──────────────────────────
        if current_month_curve is not None and current_tdom and current_tdom > 0:
            from shared.percentile_bar import render_percentile_bar
            _cm_tdoms, _cm_curve = current_month_curve
            # Aktueller Wert am letzten verfuegbaren TDOM
            _cur_val = _cm_curve[-1] if _cm_curve else None
            _cur_tdom = _cm_tdoms[-1] if _cm_tdoms else None
            if _cur_val is not None and _cur_tdom is not None:
                # Historische Werte an genau diesem TDOM
                _hist_at_tdom = [c["curve"][c["tdoms"].index(_cur_tdom)]
                                 for c in all_curves
                                 if _cur_tdom in c["tdoms"]]
                if len(_hist_at_tdom) >= 5:
                    render_percentile_bar(
                        current_value=_cur_val,
                        hist_values=_hist_at_tdom,
                        label=f"TDOM {_cur_tdom} · {month_name} {datetime.now().year}",
                    )

        # 1a. Detrend-Indikator (direkt nach Chart)
        with st.expander("Detrend-Indikator / Saisonaler Druck", expanded=True):
            render_info_badge("detrend_indikator")
            detrend_fig = build_detrend_chart(tdom_stats, ticker, month_name, current_tdom)
            if detrend_fig:
                st.plotly_chart(detrend_fig, use_container_width=True)
                st.caption("_Saisonaler Intra-Monat-Verlauf ohne Trendkomponente. "
                          "Über 50 = saisonal typisch starke Phase. Unter 50 = saisonal typisch schwache Phase._")

        # 1b. Seasonal Match Analyse (wenn Live-Overlay aktiv)
        if current_month_curve is not None:
            match = calc_seasonal_match(tdom_stats, current_month_curve, all_curves)
            render_seasonal_match(match, ticker, month_name)

            # 1c. Praesidentenzyklus Best-Match
            cycle_results = calc_cycle_match(df, selected_month, selected_years, current_month_curve)
            render_cycle_match(cycle_results, ticker, month_name)

    # 2. Wochen
    weekly_stats = calc_weekly_performance(df, selected_month, selected_years)
    if weekly_stats:
        with st.expander("📅 Wochen-Performance", expanded=True):
            render_info_badge("wochen_performance")
            fig = build_weekly_bars(weekly_stats, ticker, month_name, current_tdom)
            if fig:
                st.plotly_chart(fig, use_container_width=True)

    # 3. Monats-Jahresuebersicht
    with st.expander("📊 Monats-Performance (alle 12 Monate)", expanded=True):
        render_info_badge("monats_performance")
        st.plotly_chart(build_monthly_bars(calc_monthly_performance(df, selected_years), ticker, current_tdom), use_container_width=True)
        with st.expander("Monats-Detailtabelle"):
            mstats = calc_monthly_performance(df, selected_years)
            st.dataframe(pd.DataFrame([{"Monat": MONTH_NAMES_DE[m["month"]-1], "Oe Rendite": f"{m['avg']:+.3f}%",
                "Median": f"{m['median']:+.3f}%", "Win Rate": f"{m['win_rate']:.0f}%", "n": m["n"]} for m in mstats]),
                use_container_width=True, hide_index=True)

    # 4. Two-Week
    st.markdown("---")
    tw_valid = [t for t in calc_two_week_performance(df, selected_years, split_day) if t["n"] >= 2]
    if tw_valid:
        with st.expander(f"📅 Two-Week Performance (Split: TDOM {split_day})", expanded=True):
            render_info_badge("two_week_performance")
            st.plotly_chart(build_two_week_bars(tw_valid, ticker, split_day, current_tdom),
                            use_container_width=True, key="tw_main_bars")

            # 4a. Two-Week Heatmap (12 Monate x 2 Hälften)
            with st.expander("🗓️ Two-Week Heatmap (12 Monate x 2 Hälften)", expanded=True):
                render_info_badge("two_week_heatmap")
                tw_heatmap = build_two_week_heatmap(tw_valid, ticker, split_day, current_tdom)
                if tw_heatmap:
                    st.plotly_chart(tw_heatmap, use_container_width=True, key="tw_heatmap")

            # 4b. Aktuelles Jahr Overlay
            with st.expander("📈 Aktuelles Jahr vs. Durchschnitt", expanded=True):
                tw_current = calc_two_week_current_year(df, split_day)
                if tw_current:
                    tw_overlay_fig = build_two_week_overlay(tw_valid, tw_current, ticker, split_day, current_tdom)
                    if tw_overlay_fig:
                        st.plotly_chart(tw_overlay_fig, use_container_width=True, key="tw_overlay")
                else:
                    st.info("Noch keine Daten für das aktuelle Jahr verfügbar.")

            # 4c. Best Two-Weeks Ranking
            with st.expander("🏆 Best Two-Weeks Ranking (Top 24)", expanded=True):
                tw_ranking = build_two_week_ranking(tw_valid, ticker, split_day)
                if tw_ranking:
                    st.plotly_chart(tw_ranking, use_container_width=True, key="tw_ranking")

            # 4d. Momentum-Check (1st Half → 2nd Half)
            with st.expander("⚡ Momentum-Check (1st → 2nd Half)", expanded=True):
                render_momentum_check(df, selected_years, split_day)

            # 4e. Signifikanztest pro Monatshälfte
            with st.expander("📊 Signifikanztest pro Monatshälfte", expanded=True):
                render_two_week_significance(df, selected_years, split_day)

            # Detailtabelle
            with st.expander("Two-Week Detailtabelle"):
                tw_sorted = sorted(tw_valid, key=lambda x: x["avg"], reverse=True)
                st.dataframe(pd.DataFrame([{"Periode": t["label"], "Monat": MONTH_NAMES_DE[t["month"]-1],
                    "Hälfte": "1st" if t["half"] == 1 else "2nd", "Ø Rendite": f"{t['avg']:+.3f}%",
                    "Win Rate": f"{t['win_rate']:.0f}%", "n": t["n"]} for t in tw_sorted]),
                    use_container_width=True, hide_index=True)

    # 5. 10-Jahres Heatmap
    st.markdown("---")
    with st.expander("10 Jahres Monats-Heatmap", expanded=True):
        render_info_badge("heatmap_10j")
        st.plotly_chart(build_monthly_heatmap(df, selected_years, ticker), use_container_width=True)

    render_footer()

main()

"""
SeasonAlpha - Mondphasen-Effekt
==================================
Analyse der Rendite rund um Vollmond und Neumond.
t0 = Mondphase → normiert auf 0%.
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

from shared.constants import DEFAULT_TICKER, DEFAULT_YEARS
from shared.data import download_data, preprocess
from shared.central_banks import get_full_moon_dates, get_new_moon_dates, get_all_moon_dates
from shared.charts import apply_se_theme
from shared.constants import SE_COLORS

st.set_page_config(page_title="Mondphasen & Börse – Vollmond-Effekt Analyse – SeasonAlpha", page_icon="🌕", layout="wide")

from shared.design import inject_se_css
from shared.footer import render_footer
inject_se_css()


# ══════════════════════════════════════════════════════════════
# BERECHNUNG (gleiche Logik wie Fed-Page)
# ══════════════════════════════════════════════════════════════

def analyze_moon_effect(df, moon_dates, days_before, days_after):
    """
    Mondphasen-Effekt: t0 = Mondphase (oder nächster Handelstag) → 0%.
    """
    window_size = days_before + 1 + days_after
    t0_idx = days_before
    all_curves = []
    trading_index = df.index
    
    for moon in moon_dates:
        moon_date = moon["date"]
        phase = moon["phase"]
        
        try:
            # t0 = Mondtag oder nächster Handelstag
            if moon_date in trading_index:
                t0_pos = trading_index.get_loc(moon_date)
            else:
                pre_dates = trading_index[trading_index <= moon_date]
                if len(pre_dates) == 0:
                    continue
                t0_pos = trading_index.get_loc(pre_dates[-1])
            
            start_pos = t0_pos - days_before
            end_pos = t0_pos + days_after + 1
            
            if start_pos < 0 or end_pos > len(df):
                continue
            
            window = df.iloc[start_pos:end_pos]
            if len(window) != window_size:
                continue
            
            log_rets = window["log_return"].values
            cum_log = np.cumsum(np.insert(log_rets, 0, 0)[:-1])
            raw_curve = 100 * np.exp(cum_log)
            
            t0_value = raw_curve[t0_idx]
            curve = ((raw_curve / t0_value - 1) * 100).tolist()
            total_return = curve[-1] - curve[0]
            
            all_curves.append({
                "year": moon_date.year,
                "date": moon_date.strftime("%Y-%m-%d"),
                "phase": phase,
                "phase_emoji": "🌕" if phase == "full" else "🌑",
                "curve": curve,
                "total_return": total_return
            })
        except Exception:
            continue
    
    if not all_curves:
        return None
    
    avg_curve = [np.mean([c["curve"][i] for c in all_curves]) for i in range(window_size)]
    
    labels = []
    for i in range(window_size):
        offset = i - days_before
        if offset < 0:
            labels.append(f"t{offset}")
        elif offset == 0:
            labels.append("t0")
        else:
            labels.append(f"t+{offset}")
    
    returns = [c["total_return"] for c in all_curves]
    wins = [r for r in returns if r > 0]
    
    stats = {
        "avg_return": np.mean(returns),
        "median_return": np.median(returns),
        "win_rate": len(wins) / len(returns) * 100 if returns else 0,
        "std_dev": np.std(returns),
        "max_gain": max(returns),
        "max_loss": min(returns),
        "total_windows": len(all_curves),
        "winning": len(wins),
        "losing": len(returns) - len(wins)
    }
    
    sorted_curves = sorted(all_curves, key=lambda c: c["total_return"])
    
    return {
        "avg_curve": avg_curve,
        "all_curves": all_curves,
        "labels": labels,
        "stats": stats,
        "best": sorted_curves[-1],
        "worst": sorted_curves[0]
    }


# ══════════════════════════════════════════════════════════════
# CHART
# ══════════════════════════════════════════════════════════════

def build_moon_chart(result, ticker, days_before, days_after, phase_name,
                     phase_color, show_individual=False):
    """Mondphasen-Effekt Chart (t0 = 0%)."""
    
    fig = go.Figure()
    labels = result["labels"]
    avg_curve = result["avg_curve"]
    x_indices = list(range(len(labels)))
    
    if show_individual:
        for entry in result["all_curves"]:
            fig.add_trace(go.Scatter(
                x=x_indices, y=entry["curve"], mode="lines",
                line=dict(color="rgba(150,150,150,0.10)", width=0.5),
                showlegend=False, hoverinfo="skip"
            ))
    
    t0_idx = days_before
    t0_label = "t0 (🌕 Vollmond)" if "Voll" in phase_name else "t0 (🌑 Neumond)" if "Neu" in phase_name else "t0 (Mondphase)"
    fig.add_vline(x=t0_idx, line_dash="dash",
        line_color="rgba(255,215,0,0.5)", line_width=1.5,
        annotation_text=t0_label, annotation_position="top",
        annotation_font=dict(size=10, color="#FFD700"))
    
    fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.3)", line_width=1)
    
    fig.add_trace(go.Scatter(
        x=x_indices, y=avg_curve,
        mode="lines+markers",
        line=dict(color=phase_color, width=3),
        marker=dict(size=6, color=phase_color),
        fill="tozeroy",
        fillcolor=phase_color.replace("1)", "0.08)") if "rgba" in phase_color else f"rgba(200,200,200,0.08)",
        name=f"Ø {phase_name} ({result['stats']['total_windows']} Events)",
        hovertemplate="%{text}<br>%{y:+.3f}%<extra></extra>",
        text=labels
    ))
    
    fig = apply_se_theme(fig, title=f"{ticker} — {phase_name} Effekt (t-{days_before} bis t+{days_after})", height=430)
    return fig


# ══════════════════════════════════════════════════════════════
# STREAMLIT UI
# ══════════════════════════════════════════════════════════════

def main():
    with st.sidebar:
        st.markdown("## 🌕 Mondphasen-Effekt")
        st.markdown("---")
        
        ticker = st.text_input("Ticker", value=DEFAULT_TICKER, key="moon_ticker").upper().strip()
        
        period_options = [3, 5, 7, 10, 15, 20, 25, 30, "Max"]
        years_back_raw = st.select_slider("Analyse-Zeitraum (Jahre)",
            options=period_options, value=DEFAULT_YEARS,
            format_func=lambda x: str(x), key="moon_period")
        years_back_is_max = (years_back_raw == "Max")
        
        st.markdown("---")
        st.markdown("### Mondphase")
        
        phase_mode = st.radio("Analysieren", 
            ["🌕 Vollmond", "🌑 Neumond", "🌕+🌑 Beide (getrennt)"],
            index=0, key="moon_phase")
        
        st.markdown("---")
        
        days_before = st.slider("Tage VOR Mondphase (t-y)", 1, 15, 5, key="moon_before")
        days_after = st.slider("Tage NACH Mondphase (t+x)", 1, 15, 5, key="moon_after")
        
        show_individual = st.checkbox("Einzelne Events zeigen", value=False, key="moon_indiv")

        st.markdown("---")
        from shared.outlier_manager import outlier_sidebar
        outlier_method = outlier_sidebar()

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
    
    min_year = min(selected_years) if selected_years else 2000
    max_year = max(selected_years) if selected_years else 2026

    # ── Outlier-Filter (kein year_data → nur Info) ───
    from shared.outlier_manager import filter_year_data, outlier_info_box
    outlier_info_box([], outlier_method)

    # ── Mondphasen laden ──────────────────────────────
    phases_to_analyze = []
    
    if "Vollmond" in phase_mode or "Beide" in phase_mode:
        phases_to_analyze.append({
            "name": "Vollmond",
            "dates": get_full_moon_dates(min_year, max_year),
            "color": "#FFD700",  # Gold
            "emoji": "🌕"
        })
    
    if "Neumond" in phase_mode or "Beide" in phase_mode:
        phases_to_analyze.append({
            "name": "Neumond",
            "dates": get_new_moon_dates(min_year, max_year),
            "color": "#9C27B0",  # Lila
            "emoji": "🌑"
        })
    
    for phase_info in phases_to_analyze:
        # Nur Events in selected_years
        filtered_dates = [d for d in phase_info["dates"] if d["date"].year in selected_years]
        
        st.markdown(f"### {phase_info['emoji']} {phase_info['name']}")
        st.markdown(f"**{len(filtered_dates)} Events** im Zeitraum {min_year}–{max_year}")
        
        result = analyze_moon_effect(df, filtered_dates, days_before, days_after)
        
        if result is None:
            st.warning(f"Nicht genug Daten für {phase_info['name']}.")
            continue
        
        # Chart
        fig = build_moon_chart(result, ticker, days_before, days_after,
                               phase_info["name"], phase_info["color"], show_individual)
        st.plotly_chart(fig, use_container_width=True)
        
        # Metriken
        stats = result["stats"]
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.metric("Win Rate", f"{stats['win_rate']:.1f}%")
        with c2:
            st.metric("Ø Rendite", f"{stats['avg_return']:+.3f}%")
        with c3:
            st.metric("Median", f"{stats['median_return']:+.3f}%")
        with c4:
            st.metric("Max Gewinn", f"{stats['max_gain']:+.2f}%")
        with c5:
            st.metric("Max Verlust", f"{stats['max_loss']:+.2f}%")
        
        st.caption(
            f"Basierend auf {stats['total_windows']} Mondphasen-Fenstern · "
            f"{stats['winning']} Gewinner / {stats['losing']} Verlierer · "
            f"Std.Abw: {stats['std_dev']:.3f}%"
        )
        
        # Signifikanztest (optional)
        from shared.significance_gauge import run_significance_test, render_significance_section
        phase_name = phase_info["name"]
        sig_groups = {f"{phase_name} Gesamt": [c["total_return"] for c in result["all_curves"]]}
        sig_results = run_significance_test(sig_groups)
        render_significance_section(sig_results,
            expander_title=f"📊 Statistische Signifikanz: {phase_name}-Effekt",
            cols_per_row=1)

        # Best & Worst
        best = result["best"]
        worst = result["worst"]

        st.markdown(f"#### 🏆 Bester & schlechtester {phase_info['name']}-Effekt")
        
        table_data = {
            "": ["🟢 Bester", "🔴 Schlechtester"],
            "Datum": [best["date"], worst["date"]],
            "Rendite": [f"{best['total_return']:+.2f}%", f"{worst['total_return']:+.2f}%"]
        }
        st.table(pd.DataFrame(table_data).set_index(""))
        
        st.markdown("---")
    
    # ── Nächste Mondphasen ────────────────────────────
    st.markdown("#### 📅 Nächste Mondphasen")
    
    today = pd.Timestamp(datetime.now().date())
    all_future = [m for m in get_all_moon_dates(max_year, max_year + 1) if m["date"] > today]
    all_future.sort(key=lambda x: x["date"])
    
    if all_future:
        next_rows = []
        for m in all_future[:10]:
            days_until = (m["date"] - today).days
            emoji = "🌕" if m["phase"] == "full" else "🌑"
            name = "Vollmond" if m["phase"] == "full" else "Neumond"
            next_rows.append({
                "Datum": m["date"].strftime("%d.%m.%Y"),
                "Wochentag": m["date"].strftime("%A"),
                "Phase": f"{emoji} {name}",
                "In Tagen": days_until
            })
        st.dataframe(pd.DataFrame(next_rows), use_container_width=True, hide_index=True)

    render_footer()


if __name__ == "__main__":
    main()

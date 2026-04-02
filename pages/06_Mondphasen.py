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

from shared.ticker_select import ticker_select
from shared.constants import DEFAULT_TICKER, DEFAULT_YEARS
from shared.data import download_data, preprocess
from shared.central_banks import get_full_moon_dates, get_new_moon_dates, get_all_moon_dates
from shared.charts import apply_se_theme, apply_se_heatmap_theme
from shared.constants import SE_COLORS, SE_HEATMAP_COLORSCALE

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
# HEATMAP HELPERS
# ══════════════════════════════════════════════════════════════

MONTH_NAMES_DE = ["Jan","Feb","Mär","Apr","Mai","Jun","Jul","Aug","Sep","Okt","Nov","Dez"]


def _heatmap_text_color(value, zmid=0, max_abs=None):
    if max_abs is None:
        max_abs = 1
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
            fig.add_annotation(
                x=x_label, y=y_label,
                text=f"{val:{fmt}}{suffix}",
                showarrow=False,
                font=dict(size=10, color=color),
            )


def build_moon_month_heatmap(all_curves, ticker, phase_name):
    """Heatmap: Monat × Phase (Ø Rendite pro Monat fuer Vollmond/Neumond)."""
    from collections import defaultdict
    month_returns = defaultdict(list)
    for c in all_curves:
        dt = pd.Timestamp(c["date"])
        month_returns[dt.month].append(c["total_return"])

    z_data = [[]]
    for m in range(1, 13):
        vals = month_returns.get(m, [])
        z_data[0].append(round(np.mean(vals), 2) if vals else 0)

    y_labels = [f"Ø {phase_name}"]
    fig = go.Figure(data=go.Heatmap(
        z=z_data, x=MONTH_NAMES_DE, y=y_labels,
        colorscale=SE_HEATMAP_COLORSCALE, zmid=0,
        hovertemplate="<b>%{x} — %{y}</b><br>Ø Rendite: %{z:+.2f}%<extra></extra>",
        colorbar=dict(
            title=dict(text="Rendite %", font=dict(color="#FFFFFF", size=11)),
            tickfont=dict(color="#FFFFFF", size=10), ticksuffix="%", tickformat="+.2f"),
    ))
    _add_heatmap_annotations(fig, z_data, MONTH_NAMES_DE, y_labels, zmid=0)

    now = datetime.now()
    fig.add_shape(type="rect",
        x0=now.month - 1 - 0.5, x1=now.month - 1 + 0.5,
        y0=-0.5, y1=0.5,
        line=dict(color="#FFD700", width=3.5),
        fillcolor="rgba(0,0,0,0)", layer="above")

    fig = apply_se_heatmap_theme(fig, title=f"{ticker} — Ø {phase_name}-Rendite nach Monat", height=180)
    fig.update_yaxes(type="category", tickformat=None)
    fig.update_xaxes(type="category", tickformat=None)
    return fig


def classify_supermoon(moon_date, phase):
    """Prueft ob Vollmond ein Supermond ist (Perigaeum-Naehe)."""
    known_new_moon = datetime(2000, 1, 6, 18, 14)
    synodic_month = 29.530588853
    anomalistic_month = 27.554551  # Perigaeum-Zyklus

    delta_days = (moon_date - pd.Timestamp(known_new_moon)).total_seconds() / 86400
    k = delta_days / synodic_month

    # Anomalie-Phase: 0 = Perigaeum
    anomaly_phase = (delta_days % anomalistic_month) / anomalistic_month
    # Supermond: Vollmond innerhalb 10% vom Perigaeum
    is_super = phase == "full" and (anomaly_phase < 0.10 or anomaly_phase > 0.90)
    return is_super


def get_lunar_calendar_context(moon_date):
    """Berechnet vereinfachten Lunar-Kalender Kontext (Mondmonat)."""
    known_new_moon = pd.Timestamp(datetime(2000, 1, 6))
    synodic_month = 29.530588853
    delta_days = (moon_date - known_new_moon).days
    lunar_month_num = int(delta_days / synodic_month) % 12 + 1
    lunar_day = int(delta_days % synodic_month)
    return lunar_month_num, lunar_day


# ══════════════════════════════════════════════════════════════
# STREAMLIT UI
# ══════════════════════════════════════════════════════════════

def main():
    with st.sidebar:
        st.markdown("## 🌕 Mondphasen-Effekt")
        st.markdown("---")
        
        ticker = ticker_select(key="moon_ticker", default=DEFAULT_TICKER)
        
        period_options = [3, 5, 7, 10, 15, 20, 25, 30, "Max"]
        years_back_raw = st.select_slider("Analyse-Zeitraum (Jahre)",
            options=period_options, value=DEFAULT_YEARS,
            format_func=lambda x: str(x), key="moon_period")
        years_back_is_max = (years_back_raw == "Max")
        
        st.markdown("---")
        st.markdown("### Mondphase")
        
        phase_mode = st.radio("Analysieren",
            ["🌕 Vollmond", "🌑 Neumond", "🌟 Supermond", "🌕+🌑 Beide (getrennt)"],
            index=0, key="moon_phase")
        
        st.markdown("---")
        
        days_before = st.slider("Tage VOR Mondphase (t-y)", 1, 15, 5, key="moon_before")
        days_after = st.slider("Tage NACH Mondphase (t+x)", 1, 15, 5, key="moon_after")
        
        show_individual = st.checkbox("Einzelne Events zeigen", value=False, key="moon_indiv")

        st.markdown("---")
        from shared.outlier_manager import outlier_sidebar
        outlier_method = outlier_sidebar()

        # ── Technische Filter ──────────────────────────
        from shared.indicator_filter_ui import indicator_filter_sidebar
        ind_filters = indicator_filter_sidebar(key_prefix="mp")

    # ── Daten laden ───────────────────────────────────
    with st.spinner(f"Lade {ticker} Daten..."):
        raw_df = download_data(ticker)

    if raw_df is None or raw_df.empty:
        st.error(f"Keine Daten für '{ticker}' gefunden.")
        return

    df = preprocess(raw_df)

    # ── Indikator-Filter anwenden ─────────────────────
    if ind_filters:
        from shared.indicators import apply_indicator_filter
        from shared.indicator_filter_ui import render_filter_badge
        mask = apply_indicator_filter(df, ind_filters)
        total_days = len(df)
        df = df[mask].copy()
        filtered_days = len(df)
        render_filter_badge(ind_filters, total_days, filtered_days)

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

    from shared.trading_day_header import render_trading_day_header
    render_trading_day_header(df, ticker=ticker)

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

    if "Supermond" in phase_mode:
        all_full = get_full_moon_dates(min_year, max_year)
        super_dates = [d for d in all_full if classify_supermoon(d["date"], d["phase"])]
        normal_dates = [d for d in all_full if not classify_supermoon(d["date"], d["phase"])]
        phases_to_analyze.append({
            "name": "Supermond",
            "dates": super_dates,
            "color": "#FFD700",  # Gold
            "emoji": "🌟"
        })
        phases_to_analyze.append({
            "name": "Normaler Vollmond",
            "dates": normal_dates,
            "color": "#94a3b8",  # Silbergrau
            "emoji": "🌕"
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

        # ── Perzentil-Statusbar (direkt unter Chart) ────
        from shared.percentile_bar import render_percentile_bar
        _last_return = result["all_curves"][-1]["total_return"] if result["all_curves"] else None
        _hist_rets = [c["total_return"] for c in result["all_curves"][:-1]]
        if _last_return is not None and len(_hist_rets) >= 5:
            _last_date = result["all_curves"][-1]["date"]
            render_percentile_bar(
                current_value=_last_return,
                hist_values=_hist_rets,
                label=f"Letzter {phase_info['name']} · {_last_date}",
            )

        # Metriken (kompakte Karten)
        stats = result["stats"]
        avg_clr = "#34d399" if stats["avg_return"] >= 0 else "#f87171"
        med_clr = "#34d399" if stats["median_return"] >= 0 else "#f87171"
        _cards = [
            ("Win Rate", f"{stats['win_rate']:.1f}%", "#e2e8f0"),
            ("Ø Rendite", f"{stats['avg_return']:+.3f}%", avg_clr),
            ("Median", f"{stats['median_return']:+.3f}%", med_clr),
            ("Max Gewinn", f"{stats['max_gain']:+.2f}%", "#34d399"),
            ("Max Verlust", f"{stats['max_loss']:+.2f}%", "#f87171"),
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
            f'<div style="display:flex; gap:8px; margin:8px 0 6px 0;">{_cards_html}</div>'
            f'<div style="font-size:11px; color:#64748b; text-align:center; margin-bottom:12px;">'
            f'{stats["total_windows"]} Fenster · {stats["winning"]} Gewinner / '
            f'{stats["losing"]} Verlierer · Std.Abw: {stats["std_dev"]:.3f}%</div>',
            unsafe_allow_html=True,
        )
        
        # Signifikanztest
        from shared.significance_gauge import run_significance_test, render_significance_section
        phase_name = phase_info["name"]
        sig_groups = {f"{phase_name} Gesamt": [c["total_return"] for c in result["all_curves"]]}
        sig_results = run_significance_test(sig_groups)
        render_significance_section(sig_results,
            expander_title=f"📊 Statistische Signifikanz: {phase_name}-Effekt",
            cols_per_row=1, expanded=True)

        # Best & Worst
        best = result["best"]
        worst = result["worst"]

        with st.expander(f"🏆 Bester & schlechtester {phase_info['name']}-Effekt", expanded=False):
            table_data = {
                "": ["🟢 Bester", "🔴 Schlechtester"],
                "Datum": [best["date"], worst["date"]],
                "Rendite": [f"{best['total_return']:+.2f}%", f"{worst['total_return']:+.2f}%"]
            }
            st.table(pd.DataFrame(table_data).set_index(""))

        # ── Mond-Heatmap (Monat × Phase) ────────────────
        with st.expander(f"🗓️ {phase_info['name']}-Heatmap (Monat × Ø Rendite)", expanded=False):
            hm_fig = build_moon_month_heatmap(result["all_curves"], ticker, phase_info["name"])
            st.plotly_chart(hm_fig, use_container_width=True,
                            key=f"moon_hm_{phase_info['name']}")
            st.caption("Zeigt die durchschnittliche Rendite pro Kalendermonat. "
                       "Gelber Rahmen = aktueller Monat.")

        # ── Streak-Analyse ──────────────────────────────
        with st.expander("🔥 Streak-Analyse (Gewinn-/Verlust-Serien)", expanded=True):
            from shared.streak_analysis import compute_streaks_from_list, render_streak_table
            _phase_label = phase_info["name"]
            # Gruppiere nach Monat: "Jan Vollmond", "Feb Vollmond" etc.
            _moon_label_map = {m: "{} {}".format(MONTH_NAMES_DE[m - 1], _phase_label)
                               for m in range(1, 13)}
            _moon_groups = compute_streaks_from_list(
                result["all_curves"],
                group_key="month",
                return_key="total_return",
                year_key="year",
                label_map=_moon_label_map,
            )
            render_streak_table(
                _moon_groups,
                col_header="{} Monat".format(_phase_label),
                interpretation="Zeigt die aktuelle Gewinn-/Verlust-Serie pro Monat fuer den {}-Effekt. "
                "Lange Serien deuten auf einen stabilen Mond-Effekt in diesem Monat hin.".format(_phase_label),
            )

        # ── Supermond-Analyse ────────────────────────────
        if phase_info["name"] == "Vollmond":
            with st.expander("🌟 Supermond-Analyse", expanded=False):
                super_returns = []
                normal_returns = []
                for c in result["all_curves"]:
                    dt = pd.Timestamp(c["date"])
                    if classify_supermoon(dt, c["phase"]):
                        super_returns.append(c["total_return"])
                    else:
                        normal_returns.append(c["total_return"])

                if len(super_returns) >= 2:
                    s_avg = np.mean(super_returns)
                    n_avg = np.mean(normal_returns) if normal_returns else 0
                    s_clr = "#34d399" if s_avg >= 0 else "#f87171"
                    n_clr = "#34d399" if n_avg >= 0 else "#f87171"
                    st.markdown(
                        f'<div style="display:flex; gap:12px; margin:8px 0;">'
                        f'<div style="flex:1; background:rgba(15,19,24,0.6);'
                        f'border:1px solid rgba(255,215,0,0.2); border-radius:8px;'
                        f'padding:12px; text-align:center;">'
                        f'<div style="font-size:10px; color:#FFD700; margin-bottom:4px;">🌟 Supermond (n={len(super_returns)})</div>'
                        f'<div style="font-size:16px; font-weight:700; color:{s_clr};">{s_avg:+.3f}%</div>'
                        f'</div>'
                        f'<div style="flex:1; background:rgba(15,19,24,0.6);'
                        f'border:1px solid rgba(255,255,255,0.07); border-radius:8px;'
                        f'padding:12px; text-align:center;">'
                        f'<div style="font-size:10px; color:#94a3b8; margin-bottom:4px;">🌕 Normal (n={len(normal_returns)})</div>'
                        f'<div style="font-size:16px; font-weight:700; color:{n_clr};">{n_avg:+.3f}%</div>'
                        f'</div>'
                        f'</div>',
                        unsafe_allow_html=True)
                    delta = s_avg - n_avg
                    d_clr = "#34d399" if delta >= 0 else "#f87171"
                    st.markdown(
                        f'<div style="text-align:center; font-size:12px; color:#94a3b8;">'
                        f'Differenz Supermond vs. Normal: '
                        f'<span style="color:{d_clr}; font-weight:700;">{delta:+.3f}%</span></div>',
                        unsafe_allow_html=True)
                    st.caption("Supermond = Vollmond in Perigäum-Nähe (Mond am erdnächsten Punkt). "
                               "Die Klassifikation basiert auf dem anomalistischen Mondzyklus (~27.55 Tage).")
                else:
                    st.info("Zu wenige Supermond-Events im gewählten Zeitraum.")

        # ── Lunar-Kalender Kontext ───────────────────────
        with st.expander(f"🌙 Lunar-Kalender: {phase_info['name']} nach Mondmonat", expanded=False):
            from collections import defaultdict
            lunar_month_returns = defaultdict(list)
            for c in result["all_curves"]:
                dt = pd.Timestamp(c["date"])
                lm, _ = get_lunar_calendar_context(dt)
                lunar_month_returns[lm].append(c["total_return"])

            lunar_labels = [f"LM {m}" for m in range(1, 13)]
            lunar_avgs = [round(np.mean(lunar_month_returns.get(m, [0])), 3) for m in range(1, 13)]
            lunar_ns = [len(lunar_month_returns.get(m, [])) for m in range(1, 13)]

            fig_lunar = go.Figure()
            colors = ["#34d399" if v >= 0 else "#f87171" for v in lunar_avgs]
            fig_lunar.add_trace(go.Bar(
                x=lunar_labels, y=lunar_avgs,
                marker_color=colors, marker_opacity=0.85,
                text=[f"{v:+.3f}%" for v in lunar_avgs],
                textposition="outside", textfont=dict(size=10, color="#e2e8f0"),
                hovertemplate="<b>%{x}</b><br>Ø Rendite: %{y:+.3f}%<br>n=%{customdata}<extra></extra>",
                customdata=lunar_ns,
            ))
            fig_lunar.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.25)")
            fig_lunar = apply_se_theme(fig_lunar,
                title=f"{ticker} — {phase_info['name']}-Effekt nach Mondmonat (Lunar-Kalender)",
                height=350)
            fig_lunar.update_yaxes(tickformat="+.3f", ticksuffix="%")
            st.plotly_chart(fig_lunar, use_container_width=True,
                            key=f"lunar_{phase_info['name']}")

            # Vergleich: Solar vs Lunar beste/schlechteste Monate
            solar_best_m = MONTH_NAMES_DE[max(range(12), key=lambda i: [round(np.mean(
                [c["total_return"] for c in result["all_curves"] if pd.Timestamp(c["date"]).month == i+1] or [0]), 3)
                for i in range(12)][i])]
            lunar_best_m = f"LM {max(range(1,13), key=lambda m: np.mean(lunar_month_returns.get(m, [0])))}"
            st.caption(
                f"Vergleich: Bester Solar-Monat = **{solar_best_m}**, "
                f"Bester Lunar-Monat = **{lunar_best_m}**. "
                f"Mondmonate (LM 1-12) basieren auf dem synodischen Zyklus (~29.5 Tage) "
                f"und sind unabhaengig vom Gregorianischen Kalender.")

    # ── Nächste Mondphasen ────────────────────────────
    with st.expander("📅 Nächste Mondphasen", expanded=False):
        today = pd.Timestamp(datetime.now().date())
        all_future = [m for m in get_all_moon_dates(max_year, max_year + 1) if m["date"] > today]
        all_future.sort(key=lambda x: x["date"])

        if all_future:
            next_rows = []
            for m in all_future[:10]:
                days_until = (m["date"] - today).days
                emoji = "🌕" if m["phase"] == "full" else "🌑"
                name = "Vollmond" if m["phase"] == "full" else "Neumond"
                is_super = classify_supermoon(m["date"], m["phase"])
                super_tag = " 🌟" if is_super else ""
                next_rows.append({
                    "Datum": m["date"].strftime("%d.%m.%Y"),
                    "Wochentag": m["date"].strftime("%A"),
                    "Phase": f"{emoji} {name}{super_tag}",
                    "In Tagen": days_until
                })
            st.dataframe(pd.DataFrame(next_rows), use_container_width=True, hide_index=True)
            st.caption("🌟 = Supermond (Vollmond in Perigäum-Nähe)")

    render_footer()


if __name__ == "__main__":
    main()

"""
SeasonAlpha - Turn of the Month
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

import plotly.graph_objects as go

from shared.ticker_select import ticker_select
from shared.constants import (
    DEFAULT_TICKER, DEFAULT_YEARS, MONTH_NAMES_DE, CYCLE_COLORS,
    SE_COLORS, SE_HEATMAP_COLORSCALE, SE_HEATMAP_TEXT_COLOR,
)
from shared.data import download_data, preprocess
from shared.calculations import analyze_turn_of_month, build_tom_chart, get_presidential_cycle_year
from shared.charts import apply_se_theme, apply_se_heatmap_theme

st.set_page_config(page_title="Turn of the Month Effekt – SeasonAlpha", page_icon="🔄", layout="wide")

from shared.design import inject_se_css
from shared.footer import render_footer
inject_se_css()


# ── HELPERS ──────────────────────────────────────────────

def _heatmap_text_color(value, zmid=0, max_abs=1):
    intensity = abs(value - zmid) / max_abs if max_abs > 0 else 0
    # Helle Gruen-Zellen (positive Werte) brauchen frueher dunkle Schrift
    if value > zmid and intensity > 0.3:
        return "#1a1a2e"
    # Dunkle Rot-Zellen (stark negativ) brauchen hellere Schrift
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


# ── 1. TOM HEATMAP (Monat x Jahr) ───────────────────────

def build_tom_heatmap(tom_result, ticker, selected_years):
    """10-Jahres Heatmap: Monatswechsel-Rendite pro Jahr x Monat."""
    # Jahre die tatsaechlich Daten haben
    data_years = sorted(set(e["year"] for e in tom_result["all_curves"]), reverse=True)[:10]
    if len(data_years) < 2:
        return None
    now = datetime.now()

    y_labels = [str(y) for y in data_years]
    x_labels = [f"{MONTH_NAMES_DE[m-1]}→{MONTH_NAMES_DE[m % 12]}" for m in range(1, 13)]

    # Lookup: (year, month) → total_return
    lookup = {}
    for entry in tom_result["all_curves"]:
        lookup[(entry["year"], entry["month"])] = entry["total_return"]

    z_data = []
    for year in data_years:
        row = [round(lookup.get((year, m), 0), 2) for m in range(1, 13)]
        z_data.append(row)

    fig = go.Figure(data=go.Heatmap(
        z=z_data, x=x_labels, y=y_labels,
        colorscale=SE_HEATMAP_COLORSCALE, zmid=0,
        hovertemplate="<b>%{y} — %{x}</b><br>TOM Rendite: %{z:+.2f}%<extra></extra>",
        colorbar=dict(
            title=dict(text="Rendite %", font=dict(color=SE_COLORS["text_muted"], size=11)),
            tickfont=dict(color=SE_COLORS["text_muted"], size=10), ticksuffix="%"),
    ))

    _add_heatmap_annotations(fig, z_data, x_labels, y_labels, zmid=0)

    # Gelber Rahmen auf aktuellem Monat + Jahr
    if str(now.year) in y_labels:
        fig.add_shape(type="rect",
            x0=now.month - 1 - 0.5, x1=now.month - 1 + 0.5,
            y0=y_labels.index(str(now.year)) - 0.5,
            y1=y_labels.index(str(now.year)) + 0.5,
            line=dict(color="#FFD700", width=3.5),
            fillcolor="rgba(0,0,0,0)", layer="above")

    n_years = len(data_years)
    fig = apply_se_theme(fig, title=f"{ticker} — TOM Heatmap (Monatswechsel-Rendite, {n_years} Jahre)",
                         height=max(400, n_years * 45 + 120), show_legend=False)
    fig.update_yaxes(autorange="reversed", type="category")
    fig.update_xaxes(type="category", tickangle=-45)
    return fig


# ── 3. STREAK-ANALYSE ────────────────────────────────────

def render_streak_analysis(tom_result):
    """Zeigt aktuelle Gewinn-/Verlust-Serien pro Monatswechsel."""
    # Gruppiere nach Monat, sortiere nach Jahr
    month_data = {}
    for entry in tom_result["all_curves"]:
        m = entry["month"]
        if m not in month_data:
            month_data[m] = []
        month_data[m].append({"year": entry["year"], "ret": entry["total_return"]})

    streak_rows = []
    for m in sorted(month_data.keys()):
        entries = sorted(month_data[m], key=lambda x: x["year"], reverse=True)
        # Aktuelle Streak zaehlen
        if not entries:
            continue
        streak_type = "win" if entries[0]["ret"] > 0 else "loss"
        streak_count = 0
        for e in entries:
            if (streak_type == "win" and e["ret"] > 0) or (streak_type == "loss" and e["ret"] <= 0):
                streak_count += 1
            else:
                break

        # Letzte 10 als farbige Bloecke
        blocks = ""
        for e in entries[:10]:
            color = "#00d4aa" if e["ret"] > 0 else "#ff4757"
            blocks += f"<span style='display:inline-block; width:36px; height:28px; " \
                       f"background:{color}; border-radius:5px; margin:2px; " \
                       f"text-align:center; font-size:11px; line-height:28px; " \
                       f"font-weight:700; color:#FFFFFF;' " \
                       f"title='{e['year']}: {e['ret']:+.2f}%'>" \
                       f"{'W' if e['ret'] > 0 else 'L'}</span>"

        label = f"{MONTH_NAMES_DE[m-1]} → {MONTH_NAMES_DE[m % 12]}"
        streak_color = "#00d4aa" if streak_type == "win" else "#ff4757"
        streak_text = f"{streak_count}x {'Gewinn' if streak_type == 'win' else 'Verlust'}"

        streak_rows.append(
            f"<tr>"
            f"<td style='color:#FFFFFF; font-size:13px; padding:6px 12px;'>{label}</td>"
            f"<td style='color:{streak_color}; font-weight:700; font-size:13px; "
            f"padding:6px 12px; text-align:center;'>{streak_text}</td>"
            f"<td style='padding:6px 8px;'>{blocks}</td>"
            f"</tr>"
        )

    table_html = (
        "<table style='width:100%; border-collapse:collapse;'>"
        "<tr style='border-bottom:1px solid rgba(255,255,255,0.1);'>"
        "<th style='color:#8899aa; font-size:11px; text-align:left; padding:4px 12px;'>Monatswechsel</th>"
        "<th style='color:#8899aa; font-size:11px; text-align:center; padding:4px 12px;'>Aktuelle Serie</th>"
        "<th style='color:#8899aa; font-size:11px; text-align:left; padding:4px 8px;'>Letzte 10 (neueste links)</th>"
        "</tr>"
        + "".join(streak_rows)
        + "</table>"
    )
    st.markdown(table_html, unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#FFFFFF; font-size:12px; margin-top:12px; line-height:1.6;'>"
        "<b>Interpretation:</b> Lange Gewinnserien deuten auf einen robusten saisonalen Effekt hin. "
        "Abbrechende Serien koennen auf Regimewechsel hinweisen. "
        "<span style='color:#00d4aa;'>W</span> = Gewinn, "
        "<span style='color:#ff4757;'>L</span> = Verlust.</p>",
        unsafe_allow_html=True)


# ── 4. FENSTERBREITE-OPTIMIERUNG ─────────────────────────

def calc_window_optimization(df, selected_months, selected_years):
    """Testet alle Kombinationen t-x / t+y und gibt Rendite-Matrix zurueck."""
    results = {}
    for before in range(1, 8):
        for after in range(1, 8):
            tom = analyze_turn_of_month(df, before, after, selected_months, selected_years)
            if tom and tom["stats"]["total_windows"] >= 10:
                results[(before, after)] = tom["stats"]["avg_return"]
            else:
                results[(before, after)] = 0
    return results


def build_window_heatmap(opt_results, ticker):
    """Heatmap: t-x (vor) x t+y (nach) → Ø Rendite."""
    before_range = list(range(1, 8))
    after_range = list(range(1, 8))

    x_labels = [f"t+{a}" for a in after_range]
    y_labels = [f"t-{b}" for b in before_range]

    z_data = []
    for b in before_range:
        row = [round(opt_results.get((b, a), 0), 3) for a in after_range]
        z_data.append(row)

    fig = go.Figure(data=go.Heatmap(
        z=z_data, x=x_labels, y=y_labels,
        colorscale=SE_HEATMAP_COLORSCALE, zmid=0,
        hovertemplate="<b>%{y} / %{x}</b><br>Oe Rendite: %{z:+.3f}%<extra></extra>",
        colorbar=dict(
            title=dict(text="Oe %", font=dict(color=SE_COLORS["text_muted"], size=11)),
            tickfont=dict(color=SE_COLORS["text_muted"], size=10), ticksuffix="%"),
    ))

    _add_heatmap_annotations(fig, z_data, x_labels, y_labels, zmid=0, fmt="+.3f")

    # Bestes Fenster markieren
    best_key = max(opt_results, key=opt_results.get)
    best_b, best_a = best_key
    fig.add_shape(type="rect",
        x0=best_a - 1 - 0.5, x1=best_a - 1 + 0.5,
        y0=best_b - 1 - 0.5, y1=best_b - 1 + 0.5,
        line=dict(color="#FFD700", width=3.5),
        fillcolor="rgba(0,0,0,0)", layer="above")

    fig = apply_se_theme(fig,
        title=f"{ticker} — TOM Fenster-Optimierung (Oe Rendite, gelb = bestes Fenster)",
        height=380, show_legend=False)
    fig.update_yaxes(type="category")
    fig.update_xaxes(type="category", side="bottom")
    return fig, opt_results


# ── 6. PRAESIDENTENZYKLUS MATCH ──────────────────────────

def render_cycle_tom(tom_result, df, selected_years, selected_months,
                     days_before, days_after, ticker):
    """TOM-Effekt aufgesplittet nach Praesidentenzyklus-Jahr."""
    from shared.significance_gauge import build_gauge
    _PLOTLY_CFG = {"displayModeBar": False, "scrollZoom": False}

    # Gruppen bilden
    cycle_groups = {}
    for name in CYCLE_COLORS.keys():
        cycle_groups[name] = [y for y in selected_years
                              if get_presidential_cycle_year(y) == name]

    fixed_order = [
        "Post-Election Year (Jahr 1)",
        "Midterm Election Year (Jahr 2)",
        "Pre-Election Year (Jahr 3)",
        "Election Year (Jahr 4)",
    ]

    results = []
    for group_name in fixed_order:
        years = cycle_groups.get(group_name, [])
        if len(years) < 3:
            continue

        tom = analyze_turn_of_month(df, days_before, days_after, selected_months, years)
        if tom is None or tom["stats"]["total_windows"] < 5:
            continue

        stats = tom["stats"]
        short_name = group_name.split("(")[1].rstrip(")") if "(" in group_name else group_name
        color = CYCLE_COLORS.get(group_name, SE_COLORS["accent_blue"])

        results.append({
            "name": short_name,
            "full_name": group_name,
            "avg_return": stats["avg_return"],
            "win_rate": stats["win_rate"],
            "n": stats["total_windows"],
            "color": color,
        })

    if not results:
        st.info("Nicht genuegend Daten fuer Praesidentenzyklus-Analyse.")
        return

    # Bester Zyklus
    best = max(results, key=lambda x: x["avg_return"])
    st.markdown(
        f"<p style='color:#FFFFFF; font-size:14px; text-align:center; margin-bottom:16px;'>"
        f"Staerkster TOM-Effekt: <b style='color:{best['color']};'>{best['name']}</b> "
        f"(Oe {best['avg_return']:+.3f}%, WR {best['win_rate']:.0f}%, n={best['n']})</p>",
        unsafe_allow_html=True)

    cols = st.columns(len(results))
    for i, (col, r) in enumerate(zip(cols, results)):
        with col:
            # Score: normalisiert auf 0-1
            max_avg = max(abs(x["avg_return"]) for x in results)
            score = max(0, min(1, (r["avg_return"] / max_avg + 1) / 2)) if max_avg > 0 else 0.5

            ranked = sorted(results, key=lambda x: x["avg_return"], reverse=True)
            pos = next(j for j, x in enumerate(ranked) if x["name"] == r["name"])
            rank = ["🥇", "🥈", "🥉", "#4"][pos] if pos < 4 else f"#{pos+1}"

            st.markdown(
                f"<p style='text-align:center; color:{r['color']}; font-weight:700; "
                f"font-size:13px; margin-bottom:2px;'>{rank} {r['name']}</p>",
                unsafe_allow_html=True)
            st.plotly_chart(build_gauge(score), use_container_width=True,
                            config=_PLOTLY_CFG, key=f"tom_cycle_{i}")
            avg_col = "#00d4aa" if r["avg_return"] > 0 else "#ff4757"
            st.markdown(
                f"<p style='text-align:center; margin-top:-12px; font-size:11px;'>"
                f"<span style='color:{avg_col};'>Oe {r['avg_return']:+.3f}%</span> · "
                f"WR {r['win_rate']:.0f}%"
                f"<br><span style='color:#8899aa;'>n={r['n']}</span></p>",
                unsafe_allow_html=True)

    st.markdown(
        "<p style='color:#FFFFFF; font-size:12px; margin-top:12px; line-height:1.6;'>"
        "<b>Interpretation:</b> Zeigt den TOM-Effekt aufgesplittet nach Praesidentenzyklus-Jahr. "
        "Pre-Election Years zeigen typischerweise den staerksten Monatswechsel-Effekt "
        "durch erhoehte fiskalische Stimuli.</p>",
        unsafe_allow_html=True)


def main():
    with st.sidebar:
        st.markdown("## 🔄 Turn of the Month")
        st.markdown("---")
        
        ticker = ticker_select(key="tom_ticker", default=DEFAULT_TICKER)
        
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
    
    if len(selected_years) < 2 or not tom_months:
        st.warning("Nicht genügend Daten oder keine Monate ausgewählt.")
        return

    # ── Outlier-Filter (kein year_data → nur Info) ───
    from shared.outlier_manager import filter_year_data, outlier_info_box
    outlier_info_box([], outlier_method)

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
    
    # ── Signifikanztest (optional) ────────────────────
    from shared.significance_gauge import run_significance_test, render_significance_section
    # Gesamt-TOM + pro Monatswechsel
    sig_groups = {"TOM Gesamt": [c["total_return"] for c in tom_result["all_curves"]]}
    month_perf_sig = {}
    for entry in tom_result["all_curves"]:
        m = entry["month"]
        key = f"{MONTH_NAMES_DE[m-1]} → {MONTH_NAMES_DE[m % 12]}"
        if key not in month_perf_sig:
            month_perf_sig[key] = []
        month_perf_sig[key].append(entry["total_return"])
    sig_groups.update(month_perf_sig)
    sig_results = run_significance_test(sig_groups)
    render_significance_section(sig_results,
        expander_title="📊 Statistische Signifikanz des Monatswechsel-Effekts")

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

    # ── TOM Heatmap (Monat x Jahr) ──────────────────
    st.markdown("---")
    with st.expander("🗓️ TOM Heatmap (Monatswechsel x Jahr)", expanded=True):
        tom_heatmap = build_tom_heatmap(tom_result, ticker, selected_years)
        st.plotly_chart(tom_heatmap, use_container_width=True, key="tom_heatmap")

    # ── Streak-Analyse ───────────────────────────────
    with st.expander("🔥 Streak-Analyse (Gewinn-/Verlust-Serien)", expanded=True):
        render_streak_analysis(tom_result)

    # ── Fensterbreite-Optimierung ────────────────────
    with st.expander("⚙️ Fenster-Optimierung (bestes t-x / t+y)", expanded=True):
        with st.spinner("Berechne optimale Fensterbreite..."):
            opt_results = calc_window_optimization(df, tom_months, selected_years)
            opt_fig, opt_data = build_window_heatmap(opt_results, ticker)
        st.plotly_chart(opt_fig, use_container_width=True, key="tom_window_opt")
        best_key = max(opt_data, key=opt_data.get)
        st.markdown(
            f"<p style='color:#FFFFFF; font-size:12px; line-height:1.6;'>"
            f"<b>Optimales Fenster:</b> Kauf bei <b style='color:#F1C40F;'>t-{best_key[0]}</b>, "
            f"Verkauf bei <b style='color:#F1C40F;'>t+{best_key[1]}</b> → "
            f"Oe Rendite: <b style='color:#00d4aa;'>{opt_data[best_key]:+.3f}%</b><br>"
            f"<b>Interpretation:</b> Jede Zelle zeigt die durchschnittliche Rendite fuer "
            f"eine bestimmte Kauf-/Verkauf-Kombination rund um den Monatswechsel. "
            f"Der gelbe Rahmen markiert das profitabelste Fenster.</p>",
            unsafe_allow_html=True)

    # ── Praesidentenzyklus TOM-Effekt ────────────────
    with st.expander("🏛️ Praesidentenzyklus — TOM-Effekt nach Zyklusjahr", expanded=True):
        render_cycle_tom(tom_result, df, selected_years, tom_months,
                         tom_days_before, tom_days_after, ticker)

    render_footer()


if __name__ == "__main__":
    main()

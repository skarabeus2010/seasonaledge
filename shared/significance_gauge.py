"""
shared/significance_gauge.py — Signifikanztest + Radial Gauge
================================================================
Wiederverwendbares Modul fuer statistische Signifikanztests
mit Radial Fill Gauge Visualisierung.

Verwendung:
    from shared.significance_gauge import run_significance_test, render_significance_section

    results = run_significance_test({"Montag": [...], "Freitag": [...]})
    render_significance_section(results)
"""

import numpy as np
import plotly.graph_objects as go
from scipy import stats

from shared.constants import SE_COLORS


# ══════════════════════════════════════════════════════
# SIGNIFIKANZTEST
# ══════════════════════════════════════════════════════

def run_significance_test(groups, test_value=0):
    """
    Fuehrt einen t-Test (H0: mean = test_value) fuer jede Gruppe durch
    und berechnet einen kombinierten Relevanz-Score.

    Args:
        groups: dict {name: [returns_list]} — z.B. {"Montag": [0.1, -0.2, ...]}
        test_value: Vergleichswert fuer den t-Test (default 0)

    Returns:
        list[dict] sortiert nach Relevanz (absteigend):
            - name, avg_return, win_rate, n, t_stat, p_value, cohens_d, relevance
    """
    results = []

    for name, returns in groups.items():
        returns = [r for r in returns if r is not None and not np.isnan(r)]
        if len(returns) < 5:
            continue

        arr = np.array(returns)
        avg = float(np.mean(arr))
        std = float(np.std(arr, ddof=1))
        wins = int(np.sum(arr > 0))
        n = len(arr)

        # t-Test: H0 = mean return = test_value
        t_stat, p_value = stats.ttest_1samp(arr, test_value)

        # Effect Size (Cohen's d)
        cohens_d = abs(avg - test_value) / std if std > 0 else 0

        # Relevanz-Score (gewichtet)
        significance = max(0, 1 - float(p_value))
        win_component = wins / n
        effect_component = min(float(cohens_d), 1.0)
        relevance = 0.5 * significance + 0.3 * win_component + 0.2 * effect_component

        results.append({
            "name": name,
            "avg_return": round(avg, 4),
            "win_rate": round(wins / n * 100, 1),
            "n": n,
            "t_stat": round(float(t_stat), 3),
            "p_value": round(float(p_value), 4),
            "cohens_d": round(float(cohens_d), 3),
            "relevance": round(relevance, 3),
        })

    results.sort(key=lambda x: x["relevance"], reverse=True)
    return results


# ══════════════════════════════════════════════════════
# GAUGE BUILDER
# ══════════════════════════════════════════════════════

def _score_to_gradient_color(score):
    """Fliessender Farbverlauf: 0=Tiefrot → 0.5=Orange/Gelb → 1=Sattgruen."""
    score = max(0, min(1, score))
    if score <= 0.5:
        t = score / 0.5
        r = int(204 + (232 - 204) * t)
        g = int(0 + (164 - 0) * t)
        b = int(0 + (37 - 0) * t)
    else:
        t = (score - 0.5) / 0.5
        r = int(232 + (0 - 232) * t)
        g = int(164 + (212 - 164) * t)
        b = int(37 + (170 - 37) * t)
    return f"rgb({r},{g},{b})"


def _sig_label(p_value):
    """Signifikanz-Stufe aus p-Wert."""
    if p_value is not None and p_value < 0.01:
        return "Hochsignifikant", "#00d4aa"
    elif p_value is not None and p_value < 0.05:
        return "Signifikant", "#00d4aa"
    elif p_value is not None and p_value < 0.10:
        return "Grenzwertig", "#e8a425"
    else:
        return "Nicht signifikant", "#ff4757"


def build_gauge(score, p_value=None):
    """
    Erstellt einen Radial Fill Gauge (Halbkreis) mit Gradient.

    Args:
        score: Relevanz-Score (0-1)
        p_value: p-Wert (optional, fuer Signifikanz-Label)

    Returns:
        go.Figure
    """
    # Gradient-Steps
    n_steps = 20
    gradient_steps = []
    for i in range(n_steps):
        step_start = i / n_steps
        step_end = (i + 1) / n_steps
        if step_end <= score:
            gradient_steps.append(dict(
                range=[step_start, step_end],
                color=_score_to_gradient_color((step_start + step_end) / 2),
            ))
        elif step_start < score < step_end:
            gradient_steps.append(dict(
                range=[step_start, score],
                color=_score_to_gradient_color((step_start + score) / 2),
            ))

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number=dict(
            font=dict(size=44, color="#FFFFFF", family="DIN Alternate, monospace"),
            valueformat=".2f",
        ),
        gauge=dict(
            shape="angular",
            axis=dict(
                range=[0, 1],
                tickwidth=0,
                tickcolor="rgba(0,0,0,0)",
                tickvals=[],
                showticklabels=False,
            ),
            bar=dict(color="rgba(0,0,0,0)", thickness=0.01),
            bgcolor="rgba(255,255,255,0.06)",
            borderwidth=0,
            bordercolor="rgba(0,0,0,0)",
            steps=gradient_steps,
            threshold=dict(
                line=dict(color="rgba(0,0,0,0)", width=0),
                thickness=0, value=0,
            ),
        ),
        title=dict(text="", font=dict(size=1)),
    ))

    fig.update_layout(
        paper_bgcolor=SE_COLORS["bg"],
        plot_bgcolor=SE_COLORS["bg"],
        height=200,
        margin=dict(l=20, r=20, t=30, b=10),
    )

    return fig


# ══════════════════════════════════════════════════════
# STREAMLIT RENDERING
# ══════════════════════════════════════════════════════

def render_significance_section(results, expander_title="📊 Statistische Signifikanz", cols_per_row=4):
    """
    Rendert die Signifikanz-Gauges als optionalen Expander.

    Args:
        results: Liste von dicts aus run_significance_test()
        expander_title: Titel des Expanders
        cols_per_row: Gauges pro Reihe (default 4)
    """
    import streamlit as st

    if not results:
        return

    _PLOTLY_CFG = {"displayModeBar": False, "scrollZoom": False}

    with st.expander(expander_title, expanded=False):
        n = len(results)
        cpr = min(cols_per_row, n)

        for row_start in range(0, n, cpr):
            row_end = min(row_start + cpr, n)
            cols = st.columns(cpr)

            for idx, col in zip(range(row_start, row_end), cols):
                r = results[idx]
                sig_lbl, sig_col = _sig_label(r["p_value"])
                gauge_fig = build_gauge(r["relevance"], r["p_value"])

                with col:
                    # Name ueber dem Gauge
                    st.markdown(
                        f"<p style='text-align:center; color:#c8d6e5; "
                        f"font-weight:600; font-size:13px; margin-bottom:2px;'>"
                        f"{r['name']}</p>",
                        unsafe_allow_html=True,
                    )
                    st.plotly_chart(gauge_fig, use_container_width=True, config=_PLOTLY_CFG)
                    # Status + Stats
                    t_str = f"t={r['t_stat']:.2f}  p={r['p_value']:.4f}"
                    st.markdown(
                        f"<p style='text-align:center; margin-top:-12px; font-size:11px;'>"
                        f"<span style='color:{sig_col}; font-weight:600;'>{sig_lbl}</span>"
                        f"<br><span style='color:#5a6e85;'>{t_str}</span>"
                        f"<br><span style='color:#5a6e85;'>Oe {r['avg_return']:+.3f}%  "
                        f"Win {r['win_rate']:.0f}%  n={r['n']}</span></p>",
                        unsafe_allow_html=True,
                    )

        # Erklaertext
        st.markdown("---")
        st.markdown(
            "<p style='color:#5a6e85; font-size:11px;'>"
            "<b>Relevanz-Score</b> = 50% Signifikanz (1-p) + 30% Win-Rate + 20% Effect Size (Cohen's d). "
            "<b>t-Statistik</b>: Signalstaerke vs. Null. "
            "<b>p-Wert</b>: Wahrscheinlichkeit fuer Zufallsergebnis (p&lt;0.05 = signifikant). "
            "<b>Gruen</b> = statistisch valide, <b>Rot</b> = wahrscheinlich Zufall.</p>",
            unsafe_allow_html=True,
        )

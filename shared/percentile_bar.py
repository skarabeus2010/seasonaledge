"""
SeasonAlpha — Perzentil Stat-Ribbon (Premium Dark Mode)
=======================================================
Kompakte einzeilige Stat-Leiste: Aktuelle Performance vs. historischen
Durchschnitt mit Micro-Gauge, Perzentil-Badge und Z-Score.
"""

import numpy as np
import streamlit as st


def render_percentile_bar(
    current_value: float,
    hist_values: list[float],
    label: str = "",
    value_fmt: str = "+.2f",
    suffix: str = "%",
):
    """Rendert eine kompakte einzeilige Stat-Ribbon unter einem Chart.

    Parameters
    ----------
    current_value : float
        Aktueller Wert (z.B. YTD-Rendite, TDOM-Rendite).
    hist_values : list[float]
        Historische Vergleichswerte (gleiche Metrik, gleicher Zeitpunkt).
    label : str
        Kontextlabel (z.B. "HT 58/252 · AAPL 2026", "TDOM 18 · Mär 2026").
    value_fmt : str
        Format-String fuer Werte (default: "+.2f").
    suffix : str
        Suffix fuer Werte (default: "%").
    """
    if len(hist_values) < 5:
        return

    hist_mean = float(np.mean(hist_values))
    hist_std = float(np.std(hist_values, ddof=1))
    delta = current_value - hist_mean

    below = sum(1 for v in hist_values if v < current_value)
    percentile = int(round(below / len(hist_values) * 100))

    z_score = delta / hist_std if hist_std > 0 else 0.0

    # ── Farben ───────────────────────────────────────
    cur_clr = "#34d399" if current_value >= 0 else "#f87171"
    delta_clr = "#34d399" if delta >= 0 else "#f87171"

    if percentile >= 60:
        marker_clr = "#34d399"
    elif percentile >= 40:
        marker_clr = "#94a3b8"
    else:
        marker_clr = "#f87171"

    bar_pos = max(2, min(98, percentile))

    # ── Label aufteilen ──────────────────────────────
    parts = label.split(" · ", 1)
    context_label = parts[0] if len(parts) > 0 else ""
    title_label = parts[1] if len(parts) > 1 else ""

    title_html = (f'<span style="font-size:11px; font-weight:600; color:#cbd5e1;">'
                  f'{title_label}</span>' if title_label else '')

    html = (
        # Outer Container: schmale Ribbon
        f'<div style="display:flex; align-items:center; gap:14px; flex-wrap:wrap;'
        f'padding:8px 16px; margin:2px 0 10px 0;'
        f'border-top:1px solid rgba(255,255,255,0.04);'
        f'border-bottom:1px solid rgba(255,255,255,0.04);'
        f'background:rgba(15,19,24,0.5);">'

        # 1) Kontext (links, dezent)
        f'<span style="font-size:10px; color:#475569; font-weight:500;'
        f'letter-spacing:0.3px; white-space:nowrap;">'
        f'{context_label}</span>'
        f'{title_html}'

        # 2) Performance: aktuell + Ø + Delta-Badge
        f'<span style="font-size:14px; font-weight:800; color:{cur_clr};'
        f'letter-spacing:-0.3px; white-space:nowrap;">'
        f'{current_value:{value_fmt}}{suffix}</span>'

        f'<span style="font-size:10px; color:#64748b; white-space:nowrap;">'
        f'Ø {hist_mean:{value_fmt}}{suffix}</span>'

        f'<span style="font-size:10px; font-weight:600; color:{delta_clr};'
        f'background:{delta_clr}12; padding:2px 7px; border-radius:4px;'
        f'border:1px solid {delta_clr}20; white-space:nowrap;">'
        f'{delta:{value_fmt}} vs. Ø</span>'

        # 3) Micro-Gauge (hauchdünner Balken)
        f'<div style="flex:1; min-width:80px; max-width:160px;'
        f'position:relative; height:6px;'
        f'background:linear-gradient(90deg,'
        f'rgba(248,113,113,0.25) 0%,'
        f'rgba(148,163,184,0.10) 50%,'
        f'rgba(52,211,153,0.25) 100%);'
        f'border-radius:3px; overflow:visible;">'

        # Marker
        f'<div style="position:absolute; top:-3px; left:{bar_pos}%;'
        f'transform:translateX(-50%); width:4px; height:12px;'
        f'background:{marker_clr}; border-radius:2px;'
        f'box-shadow:0 0 6px {marker_clr}90, 0 0 12px {marker_clr}40;"></div>'
        f'</div>'

        # 4) Perzentil-Badge + Stats (rechts)
        f'<span style="font-size:10px; font-weight:700; color:{marker_clr};'
        f'background:{marker_clr}10; padding:2px 8px; border-radius:4px;'
        f'border:1px solid {marker_clr}18; white-space:nowrap;">'
        f'P{percentile}</span>'

        f'<span style="font-size:9px; color:#475569; white-space:nowrap;">'
        f'{z_score:+.1f}σ · n={len(hist_values)}</span>'

        f'</div>'
    )

    st.markdown(html, unsafe_allow_html=True)

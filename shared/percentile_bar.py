"""
SeasonAlpha — Perzentil-Statusbar (Premium Dark Mode)
=====================================================
Wiederverwendbare Komponente: Zeigt aktuelle Performance vs. historischen
Durchschnitt mit elegantem Perzentil-Balken, Z-Score und Einordnung.
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
    """Rendert eine kompakte Perzentil-Statusbar unter einem Chart.

    Parameters
    ----------
    current_value : float
        Aktueller Wert (z.B. YTD-Rendite, TDOM-Rendite).
    hist_values : list[float]
        Historische Vergleichswerte (gleiche Metrik, gleicher Zeitpunkt).
    label : str
        Kontextlabel — Format: "Sekundaer · Primaer" (z.B. "HT 58/252 · AAPL 2026").
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

    if z_score > 1.5:
        z_label = "ungewoehnlich stark"
    elif z_score > 0.5:
        z_label = "ueberdurchschnittlich"
    elif z_score > -0.5:
        z_label = "durchschnittlich"
    elif z_score > -1.5:
        z_label = "unterdurchschnittlich"
    else:
        z_label = "ungewoehnlich schwach"

    cur_clr = "#34d399" if current_value >= 0 else "#f87171"
    delta_clr = "#34d399" if delta >= 0 else "#f87171"

    if percentile >= 60:
        marker_clr = "#34d399"
    elif percentile >= 40:
        marker_clr = "#94a3b8"
    else:
        marker_clr = "#f87171"

    bar_pos = max(3, min(97, percentile))

    parts = label.split(" · ", 1)
    secondary_label = parts[0] if len(parts) > 1 else ""
    primary_label = parts[1] if len(parts) > 1 else label

    sec_html = (f'<span style="font-size:11px; color:#64748b; font-weight:500; '
                f'letter-spacing:0.3px;">{secondary_label}</span>'
                if secondary_label else '')

    html = (
        f'<div style="background:linear-gradient(135deg, #0f1318 0%, #141a21 50%, #0f1318 100%);'
        f'border:1px solid rgba(255,255,255,0.07); border-radius:12px;'
        f'padding:18px 22px; margin:6px 0 18px 0;">'

        # Header
        f'<div style="display:flex; align-items:baseline; gap:10px; flex-wrap:wrap;'
        f'margin-bottom:14px;">'
        f'{sec_html}'
        f'<span style="font-size:14px; font-weight:700; color:#f1f5f9;'
        f'letter-spacing:0.2px;">{primary_label}</span>'
        f'<span style="flex:1;"></span>'
        f'<span style="font-size:18px; font-weight:800; color:{cur_clr};'
        f'letter-spacing:-0.3px;">{current_value:{value_fmt}}{suffix}</span>'
        f'</div>'

        # Kontext-Zeile
        f'<div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;'
        f'margin-bottom:14px;">'
        f'<span style="font-size:12px; color:#64748b;">'
        f'Ø historisch: <span style="color:#94a3b8; font-weight:600;">'
        f'{hist_mean:{value_fmt}}{suffix}</span></span>'
        f'<span style="font-size:12px; font-weight:600; color:{delta_clr};'
        f'background:{delta_clr}14; padding:3px 10px; border-radius:6px;'
        f'border:1px solid {delta_clr}25;">'
        f'{delta:{value_fmt}}{suffix} vs. Ø</span>'
        f'</div>'

        # Gauge-Balken
        f'<div style="position:relative; height:32px;'
        f'background:linear-gradient(90deg,'
        f'rgba(248,113,113,0.08) 0%,'
        f'rgba(148,163,184,0.06) 40%,'
        f'rgba(148,163,184,0.06) 60%,'
        f'rgba(52,211,153,0.08) 100%);'
        f'border-radius:8px; border:1px solid rgba(255,255,255,0.05);'
        f'margin-bottom:12px; overflow:visible;">'

        # Trennlinien
        f'<div style="position:absolute; top:4px; bottom:4px; left:40%;'
        f'width:1px; background:rgba(255,255,255,0.06);"></div>'
        f'<div style="position:absolute; top:4px; bottom:4px; left:60%;'
        f'width:1px; background:rgba(255,255,255,0.06);"></div>'

        # Zone-Labels
        f'<span style="position:absolute; left:12px; top:50%; transform:translateY(-50%);'
        f'font-size:10px; color:#64748b; font-weight:500; letter-spacing:0.5px;'
        f'text-transform:uppercase;">schwach</span>'
        f'<span style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%);'
        f'font-size:10px; color:#64748b; font-weight:500;">Ø</span>'
        f'<span style="position:absolute; right:12px; top:50%; transform:translateY(-50%);'
        f'font-size:10px; color:#64748b; font-weight:500; letter-spacing:0.5px;'
        f'text-transform:uppercase;">stark</span>'

        # Marker mit Glow
        f'<div style="position:absolute; top:-4px; left:{bar_pos}%;'
        f'transform:translateX(-50%); z-index:3;">'
        f'<div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);'
        f'width:16px; height:40px;'
        f'background:radial-gradient(ellipse, {marker_clr}40 0%, transparent 70%);'
        f'pointer-events:none;"></div>'
        f'<div style="width:4px; height:40px; background:{marker_clr};'
        f'border-radius:3px;'
        f'box-shadow:0 0 10px {marker_clr}80, 0 0 20px {marker_clr}30;"></div>'
        f'</div>'

        f'</div>'

        # Footer
        f'<div style="display:flex; align-items:center; justify-content:space-between;'
        f'flex-wrap:wrap; gap:8px;">'
        f'<span style="font-size:13px; font-weight:700; color:{marker_clr};'
        f'background:{marker_clr}12; padding:4px 12px; border-radius:6px;'
        f'border:1px solid {marker_clr}20;">'
        f'{percentile}. Perzentil</span>'
        f'<div style="display:flex; align-items:center; gap:12px;">'
        f'<span style="font-size:12px; color:#64748b;">'
        f'{z_score:+.1f}σ · {z_label}</span>'
        f'<span style="font-size:11px; color:#475569;">n={len(hist_values)}</span>'
        f'</div>'
        f'</div>'

        f'</div>'
    )

    st.markdown(html, unsafe_allow_html=True)

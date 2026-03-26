"""
SeasonAlpha — Perzentil-Statusbar
==================================
Wiederverwendbare Komponente: Zeigt aktuelle Performance vs. historischen
Durchschnitt mit Perzentil-Balken, Z-Score und Einordnung.
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
        Kontextlabel (z.B. "HT 58/252", "TDOM 15", "Rot-Signal").
    value_fmt : str
        Format-String fuer Werte (default: "+.2f").
    suffix : str
        Suffix fuer Werte (default: "%").
    """
    if len(hist_values) < 5:
        return  # Zu wenige Daten

    hist_mean = float(np.mean(hist_values))
    hist_std = float(np.std(hist_values, ddof=1))
    delta = current_value - hist_mean

    # Perzentil
    below = sum(1 for v in hist_values if v < current_value)
    percentile = int(round(below / len(hist_values) * 100))

    # Z-Score
    z_score = delta / hist_std if hist_std > 0 else 0.0

    # Einordnung
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

    # Farben
    cur_clr = "#00d4aa" if current_value >= 0 else "#ff4757"
    delta_clr = "#00d4aa" if delta >= 0 else "#ff4757"

    # Balken-Farbe basierend auf Perzentil
    if percentile >= 60:
        bar_clr = "#00d4aa"
        bar_bg = "linear-gradient(90deg, #1a1a2e 0%, #0d2e1f 100%)"
    elif percentile >= 40:
        bar_clr = "#8899aa"
        bar_bg = "linear-gradient(90deg, #1a1a2e 0%, #1a1a2e 100%)"
    else:
        bar_clr = "#ff4757"
        bar_bg = "linear-gradient(90deg, #1a1a2e 0%, #2e1a1a 100%)"

    # Balken-Position (clamp 2-98%)
    bar_pos = max(2, min(98, percentile))

    st.markdown(
        f"""<div style="background:linear-gradient(135deg, #0d1117 0%, #161b22 100%);
            border:1px solid rgba(255,255,255,0.06); border-radius:10px;
            padding:16px 20px; margin:4px 0 16px 0;">
            <!-- Obere Zeile: Label + Werte -->
            <div style="display:flex; align-items:center; gap:14px; flex-wrap:wrap;
                margin-bottom:12px;">
                <span style="font-size:12px; color:#FFD700; font-weight:600;">
                    📍 {label}</span>
                <span style="font-size:16px; font-weight:700; color:{cur_clr};">
                    {current_value:{value_fmt}}{suffix}</span>
                <span style="font-size:12px; color:#6e7681;">
                    Ø hist: {hist_mean:{value_fmt}}{suffix}</span>
                <span style="font-size:12px; font-weight:600; color:{delta_clr};
                    background:{delta_clr}18; padding:2px 8px; border-radius:5px;">
                    {delta:{value_fmt}}{suffix} vs. Ø</span>
            </div>
            <!-- Perzentil-Balken -->
            <div style="position:relative; height:28px; background:{bar_bg};
                border-radius:6px; border:1px solid rgba(255,255,255,0.05);
                overflow:visible; margin-bottom:8px;">
                <!-- Hintergrund-Segmente -->
                <div style="position:absolute; top:0; left:0; width:40%; height:100%;
                    background:rgba(255,71,87,0.06); border-radius:6px 0 0 6px;"></div>
                <div style="position:absolute; top:0; left:40%; width:20%; height:100%;
                    background:rgba(136,153,170,0.06);"></div>
                <div style="position:absolute; top:0; right:0; width:40%; height:100%;
                    background:rgba(0,212,170,0.06); border-radius:0 6px 6px 0;"></div>
                <!-- Marker -->
                <div style="position:absolute; top:-2px; left:{bar_pos}%;
                    transform:translateX(-50%); z-index:2;">
                    <div style="width:3px; height:32px; background:{bar_clr};
                        border-radius:2px; box-shadow:0 0 8px {bar_clr}60;"></div>
                </div>
                <!-- Labels im Balken -->
                <span style="position:absolute; left:8px; top:50%; transform:translateY(-50%);
                    font-size:9px; color:#ff475740;">schwach</span>
                <span style="position:absolute; left:50%; top:50%;
                    transform:translate(-50%,-50%);
                    font-size:9px; color:#8899aa40;">Ø</span>
                <span style="position:absolute; right:8px; top:50%; transform:translateY(-50%);
                    font-size:9px; color:#00d4aa40;">stark</span>
            </div>
            <!-- Untere Zeile: Perzentil + Z-Score -->
            <div style="display:flex; align-items:center; gap:12px; flex-wrap:wrap;">
                <span style="font-size:12px; color:{bar_clr}; font-weight:700;
                    background:rgba(255,255,255,0.04); padding:2px 8px; border-radius:5px;">
                    {percentile}. Perzentil</span>
                <span style="font-size:12px; color:#8899aa;">
                    {z_score:+.1f}σ · {z_label}</span>
                <span style="font-size:11px; color:#484f58;">n={len(hist_values)}</span>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

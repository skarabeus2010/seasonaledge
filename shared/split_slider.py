# shared/split_slider.py — v7
# ============================================================
# Achsen-Strategie: 3-Layer-Architektur
#   Layer Axes  : Nur Achsen, KEIN clip-path → immer sichtbar
#   Layer B     : Saisonal-Kurve, clip LINKS
#   Layer A     : Spaghetti-Kurven, clip RECHTS
#
# Jeder Plotly-Chart rendert mit ALLEN 3 Layern,
# aber "Axes-Chart" hat nur unsichtbare Traces (Linien opacity=0)
# → Achsen immer sichtbar, Kurven per clip gesteuert
# ============================================================

import json
import numpy as np
import pandas as pd
import streamlit.components.v1 as components
from shared.constants import SE_COLORS


def _traces_spaghetti(df: pd.DataFrame) -> tuple[str, list]:
    years = sorted(df["year"].unique())
    current_year = int(pd.Timestamp.now().year)
    traces = []
    all_y = []
    for yr in years:
        sub = df[df["year"] == yr].sort_values("trading_day")
        if len(sub) < 20:
            continue
        is_current = (int(yr) == current_year)
        y_vals = [round(v, 4) for v in sub["cum_return_pct"].tolist()]
        all_y.extend(y_vals)
        traces.append({
            "x": sub["trading_day"].tolist(),
            "y": y_vals,
            "mode": "lines",
            "type": "scatter",
            "yaxis": "y2",
            "line": {
                "color": "#FFE600" if is_current else "rgba(200,220,255,0.40)",
                "width": 2.5 if is_current else 1.0,
            },
            "hoverinfo": "skip",
            "name": str(int(yr)),
        })
    return json.dumps(traces), all_y


def _traces_average(df: pd.DataFrame) -> tuple[str, list]:
    grouped = df.groupby("trading_day")["cum_return_pct"]
    avg = grouped.agg(["mean", "count"]).reset_index()
    # Nur Handelstage mit >= 90% der max. Jahresanzahl (verhindert Knick am Jahresende)
    max_count = avg["count"].max()
    avg = avg[avg["count"] >= max_count * 0.9]
    td   = avg["trading_day"].tolist()
    mean = [round(v, 4) for v in avg["mean"].tolist()]
    traces = [{
        "x": td,
        "y": mean,
        "mode": "lines",
        "type": "scatter",
        "yaxis": "y",
        "line": {"color": "#4d9fff", "width": 3},
        "hoverinfo": "skip",
        "name": "Ø Saison",
    }]
    return json.dumps(traces), mean


def _align_zero(a_vals, b_vals, pad=0.06):
    if not a_vals or not b_vals:
        return [-50, 50], [-10, 15]
    # Einzeljahre: Clippe auf Perzentile um Crash-Ausreisser zu daempfen
    import numpy as _np
    a_min = max(min(a_vals), float(_np.percentile(a_vals, 2))) * (1 + pad)
    a_max = min(max(a_vals), float(_np.percentile(a_vals, 98))) * (1 + pad)
    b_min = min(b_vals) * (1 + pad)
    b_max = max(b_vals) * (1 + pad)
    def zero_pos(lo, hi):
        span = hi - lo
        return abs(lo) / span if span != 0 else 0.5
    pos = max(zero_pos(a_min, a_max), zero_pos(b_min, b_max))
    pos = min(max(pos, 0.15), 0.85)
    a_span = a_max - a_min
    b_span = b_max - b_min
    y1 = [round(-pos * a_span, 2), round((1 - pos) * a_span, 2)]
    y2 = [round(-pos * b_span, 2), round((1 - pos) * b_span, 2)]
    return y1, y2


def render_split_slider(df: pd.DataFrame, height: int = 480, info: str = "") -> None:
    ch = height - 70
    MARGIN = {"l": 62, "r": 66, "t": 10, "b": 46}

    traces_a_json, y_a = _traces_spaghetti(df)
    traces_b_json, y_b = _traces_average(df)
    # Zwei Y-Achsen: Links = Saisonal (eng), Rechts = Einzeljahre (weit)
    import numpy as _np
    # Saisonal-Achse: eng um die tatsaechlichen Werte
    # Ignoriere letzte 10 Handelstage (Backfill-Artefakte am Jahresende)
    y_b_clean = y_b[:-10] if len(y_b) > 20 else y_b
    b_lo = float(_np.percentile(y_b_clean, 1))
    b_hi = float(_np.percentile(y_b_clean, 99))
    b_span = b_hi - b_lo
    b_pad = max(b_span * 0.1, 0.2)
    y_b_range = [round(b_lo - b_pad, 1), round(b_hi + b_pad, 1)]
    # Einzeljahre-Achse: Voller Datenbereich, nichts abschneiden
    y_a_lo = min(y_a) * 1.05
    y_a_hi = max(y_a) * 1.05
    y_a_range = [round(y_a_lo, 1), round(y_a_hi, 1)]

    # ── Gemeinsames Basis-Layout (X + beide Y-Achsen) ────────────────
    # Dieses Layout wird von ALLEN 3 Divs geteilt → identische Achsenpositionen
    base_layout = {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor":  SE_COLORS["surface"],
        "margin": MARGIN,
        "font": {"family": "Inter, -apple-system, 'Segoe UI', sans-serif"},
        "xaxis": {
            "range": [1, 252],
            "showgrid": False,
            "zeroline": False,
            "tickmode": "array",
            "tickvals": [1, 42, 84, 126, 168, 210, 252],
            "ticktext": ["Jan", "Mrz", "Mai", "Jul", "Sep", "Nov", "Dez"],
            "tickfont": {"color": SE_COLORS["text_muted"], "size": 10},
            "linecolor": SE_COLORS["axis_line"],
            "title": {"text": "Handelstag im Jahr",
                      "font": {"color": SE_COLORS["text_muted"], "size": 11}},
        },
        "yaxis": {
            "range": y_b_range,
            "side": "left",
            "showgrid": True,
            "gridcolor": SE_COLORS["grid"],
            "griddash": "dot",
            "zeroline": True,
            "zerolinecolor": SE_COLORS["zero_line"],
            "zerolinewidth": 1,
            "tickfont": {"color": SE_COLORS["accent_blue"], "size": 10},
            "ticksuffix": "%",
            "linecolor": SE_COLORS["accent_blue"],
            "title": {"text": "Saisonal %",
                      "font": {"color": SE_COLORS["accent_blue"], "size": 10}},
        },
        "yaxis2": {
            "range": y_a_range,
            "overlaying": "y",
            "side": "right",
            "showgrid": False,
            "zeroline": False,
            "tickfont": {"color": SE_COLORS["text_muted"], "size": 10},
            "ticksuffix": "%",
            "linecolor": SE_COLORS["axis_line"],
            "title": {"text": "Einzeljahre %",
                      "font": {"color": SE_COLORS["text_muted"], "size": 10}},
        },
        "showlegend": False,
        "dragmode": False,
        "hovermode": False,
    }

    # Axes-Layer: nur leere Traces → rendert nur Achsen/Grid, keine Kurven
    traces_axes = json.dumps([
        {"x": [1], "y": [0], "mode": "lines", "type": "scatter",
         "yaxis": "y",  "line": {"color": "rgba(0,0,0,0)", "width": 0},
         "hoverinfo": "skip", "showlegend": False},
        {"x": [1], "y": [0], "mode": "lines", "type": "scatter",
         "yaxis": "y2", "line": {"color": "rgba(0,0,0,0)", "width": 0},
         "hoverinfo": "skip", "showlegend": False},
    ])

    lj = json.dumps(base_layout)
    cfg = json.dumps({"displayModeBar": False, "responsive": True})

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js" charset="utf-8"></script>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:100%; height:100%; background:{SE_COLORS["bg"]}; overflow:hidden; }}

.se-labels {{
  display:flex; justify-content:space-between; align-items:center;
  padding:0 4px 6px;
  font-family:Inter,-apple-system,'Segoe UI',sans-serif;
  font-size:11px; font-weight:600; letter-spacing:.8px; text-transform:uppercase;
}}
.lbl-b {{ color:{SE_COLORS["accent_blue"]}; }}
.lbl-i {{ color:{SE_COLORS["text_dim"]}; font-size:10px; letter-spacing:.2px;
          text-transform:none; font-weight:400; }}
.lbl-a {{ color:{SE_COLORS["text_muted"]}; }}

.split-wrap {{
  position:relative; width:100%; height:{ch}px;
  border:1px solid {SE_COLORS["panel_border"]}; border-radius:10px; overflow:hidden;
  background:{SE_COLORS["bg"]};
}}
.se-watermark {{
  position:absolute; bottom:6px; right:10px; z-index:7;
  font-family:Inter,-apple-system,sans-serif; font-size:10px;
  color:{SE_COLORS["text_dim"]}; opacity:0.5; pointer-events:none;
}}

/* ── 3 Layer übereinander ── */
.clayer {{
  position:absolute; top:0; left:0;
  width:100%; height:{ch}px;
  pointer-events:none;
}}
#div-axes {{ width:100%; height:{ch}px; }}  /* Achsen-Chart */
#div-a    {{ width:100%; height:{ch}px; }}  /* Spaghetti */
#div-b    {{ width:100%; height:{ch}px; }}  /* Saisonal  */

/* Axes-Layer: KEIN clip-path → Achsen immer vollständig sichtbar */
#layer-axes {{ z-index:1; }}

/* Saisonal: sichtbar LINKS vom Divider (Start: 100% sichtbar) */
#layer-b {{ clip-path: inset(0 0% 0 0); z-index:2; will-change:clip-path; }}

/* Einzeljahre: sichtbar RECHTS vom Divider (Start: 0% sichtbar) */
#layer-a {{ clip-path: inset(0 0 0 100%); z-index:3; will-change:clip-path; }}

/* Divider + Handle über allem */
.divider {{
  position:absolute; top:0; left:50%; width:2px; height:100%;
  background:linear-gradient(180deg,
    transparent 0%, {SE_COLORS["accent_blue"]} 15%, {SE_COLORS["accent_blue"]} 85%, transparent 100%);
  z-index:8; pointer-events:none; transform:translateX(-50%);
}}
.div-handle {{
  position:absolute; top:50%; left:50%;
  transform:translate(-50%,-50%);
  width:30px; height:30px; background:{SE_COLORS["accent_blue"]}; border-radius:50%;
  z-index:9; pointer-events:none;
  display:flex; align-items:center; justify-content:center;
  color:{SE_COLORS["bg"]}; font-size:12px; font-weight:800;
  box-shadow:0 0 14px rgba(77,159,255,0.7);
}}
input.sl-ov {{
  position:absolute; top:0; left:0; width:100%; height:100%;
  opacity:0; z-index:10; cursor:ew-resize; -webkit-appearance:none;
}}
.bar-wrap {{
  padding:8px 4px 2px;
  display:flex; align-items:center; gap:10px;
  font-family:system-ui,sans-serif;
}}
.bar-wrap input[type=range] {{
  -webkit-appearance:none; flex:1; height:4px;
  background:linear-gradient(90deg,
    rgba(77,159,255,0.6) 0%, rgba(255,255,255,0.12) 100%);
  border-radius:2px; cursor:ew-resize; outline:none; border:none;
}}
.bar-wrap input[type=range]::-webkit-slider-thumb {{
  -webkit-appearance:none; width:18px; height:18px; border-radius:50%;
  background:#fff; box-shadow:0 0 8px rgba(255,255,255,0.4);
  border:2px solid {SE_COLORS["accent_blue"]}; cursor:ew-resize;
}}
.bar-wrap input[type=range]::-moz-range-thumb {{
  width:18px; height:18px; border-radius:50%;
  background:#fff; border:2px solid {SE_COLORS["accent_blue"]}; cursor:ew-resize;
}}
.bar-icon {{ font-size:11px; color:{SE_COLORS["text_muted"]};
             white-space:nowrap; font-weight:600; }}
</style>
</head>
<body>

<div class="se-labels">
  <span class="lbl-b">◈ Ø Saisonal</span>
  <span class="lbl-i">{info}</span>
  <span class="lbl-a">◈ Einzeljahre</span>
</div>

<div class="split-wrap" id="wrap">
  <!-- Layer 1: Achsen (kein clip) -->
  <div class="clayer" id="layer-axes"><div id="div-axes"></div></div>
  <!-- Layer 2: Saisonal (clip LINKS) -->
  <div class="clayer" id="layer-b"><div id="div-b"></div></div>
  <!-- Layer 3: Einzeljahre (clip RECHTS) -->
  <div class="clayer" id="layer-a"><div id="div-a"></div></div>

  <span class="se-watermark">SeasonalEdge</span>
  <div class="divider"    id="divider" style="left:0%"></div>
  <div class="div-handle" id="handle" style="left:0%">↔</div>
  <input type="range" min="0" max="100" value="0"
         class="sl-ov" id="sl-ov">
</div>

<div class="bar-wrap">
  <span class="bar-icon">← Ø Saisonal</span>
  <input type="range" min="0" max="100" value="0" id="sl-bar">
  <span class="bar-icon">Einzeljahre →</span>
</div>

<script>
(function() {{
  var h = {ch};
  var layout  = {lj};
  var config  = {cfg};
  var tracesAxes = {traces_axes};
  var tracesA    = {traces_a_json};
  var tracesB    = {traces_b_json};

  // Alle Divs gleich groß setzen VOR Plotly.newPlot
  ['div-axes','div-a','div-b'].forEach(function(id) {{
    var el = document.getElementById(id);
    el.style.cssText = 'width:100%;height:' + h + 'px;';
  }});

  // 3 Charts mit identischem Layout → pixel-genaue Überlagerung
  Plotly.newPlot('div-axes', tracesAxes, layout, config);
  Plotly.newPlot('div-b',    tracesB,    layout, config);
  Plotly.newPlot('div-a',    tracesA,    layout, config);

  // Größe nach Render erzwingen
  setTimeout(function() {{
    var w = document.getElementById('wrap').offsetWidth;
    ['div-axes','div-a','div-b'].forEach(function(id) {{
      Plotly.relayout(id, {{width: w, height: h}});
    }});
  }}, 150);

  // ── Slider ──────────────────────────────────────────────────────
  var layerA  = document.getElementById('layer-a');
  var layerB  = document.getElementById('layer-b');
  var divider = document.getElementById('divider');
  var handle  = document.getElementById('handle');
  var slOv    = document.getElementById('sl-ov');
  var slBar   = document.getElementById('sl-bar');
  var cur = 50, raf = false;

  function apply(pct) {{
    pct = Math.round(pct);
    var right = 100 - pct;
    // Saisonal sichtbar LINKS
    layerB.style.clipPath = 'inset(0 ' + right + '% 0 0)';
    // Einzeljahre sichtbar RECHTS
    layerA.style.clipPath = 'inset(0 0 0 ' + pct + '%)';
    divider.style.left = pct + '%';
    handle.style.left  = pct + '%';
    slOv.value  = pct;
    slBar.value = pct;
  }}

  function schedule(val) {{
    cur = val;
    if (!raf) {{
      raf = true;
      requestAnimationFrame(function() {{ apply(cur); raf = false; }});
    }}
  }}

  slOv.addEventListener('input',  function(e) {{ schedule(+e.target.value); }});
  slBar.addEventListener('input', function(e) {{ schedule(+e.target.value); }});
  slOv.addEventListener('touchmove', function(e) {{ e.preventDefault(); }},
                        {{passive: false}});
  window.addEventListener('resize', function() {{
    ['div-axes','div-a','div-b'].forEach(function(id) {{
      Plotly.relayout(id, {{autosize:true}});
    }});
  }});

  apply(50);
}})();
</script>
</body>
</html>"""

    components.html(html, height=height, scrolling=False)

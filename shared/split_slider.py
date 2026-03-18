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
            "yaxis": "y",
            "line": {
                "color": "rgba(232,164,37,0.90)" if is_current else "rgba(200,220,255,0.40)",
                "width": 2.5 if is_current else 1.0,
            },
            "hoverinfo": "skip",
            "name": str(int(yr)),
        })
    return json.dumps(traces), all_y


def _traces_average(df: pd.DataFrame) -> tuple[str, list]:
    avg = (
        df.groupby("trading_day")["cum_return_pct"]
        .agg(["mean"])
        .reset_index()
    )
    td   = avg["trading_day"].tolist()
    mean = [round(v, 4) for v in avg["mean"].tolist()]
    traces = [{
        "x": td,
        "y": mean,
        "mode": "lines",
        "type": "scatter",
        "yaxis": "y2",
        "line": {"color": "#4d9fff", "width": 2.5},
        "hoverinfo": "skip",
        "name": "Ø Saison",
    }]
    return json.dumps(traces), mean


def _align_zero(a_vals, b_vals, pad=0.06):
    if not a_vals or not b_vals:
        return [-50, 50], [-10, 15]
    a_min = min(a_vals) * (1 + pad)
    a_max = max(a_vals) * (1 + pad)
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
    y1_range, y2_range = _align_zero(y_a, y_b)

    # ── Gemeinsames Basis-Layout (X + beide Y-Achsen) ────────────────
    # Dieses Layout wird von ALLEN 3 Divs geteilt → identische Achsenpositionen
    base_layout = {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor":  "rgba(0,0,0,0)",
        "margin": MARGIN,
        "xaxis": {
            "range": [1, 252],
            "showgrid": False,
            "zeroline": False,
            "tickfont": {"color": "#ffffff", "size": 10},
            "linecolor": "rgba(255,255,255,0.2)",
            "title": {"text": "Handelstag im Jahr",
                      "font": {"color": "#ffffff", "size": 11}},
        },
        "yaxis": {
            "range": y1_range,
            "side": "left",
            "showgrid": True,
            "gridcolor": "rgba(255,255,255,0.06)",
            "zeroline": True,
            "zerolinecolor": "rgba(255,255,255,0.18)",
            "zerolinewidth": 1,
            "tickfont": {"color": "rgba(200,220,255,0.80)", "size": 10},
            "ticksuffix": "%",
            "linecolor": "rgba(200,220,255,0.3)",
            "title": {"text": "Einzeljahre %",
                      "font": {"color": "rgba(200,220,255,0.80)", "size": 10}},
        },
        "yaxis2": {
            "range": y2_range,
            "overlaying": "y",
            "side": "right",
            "showgrid": False,
            "zeroline": False,
            "tickfont": {"color": "#4d9fff", "size": 10},
            "ticksuffix": "%",
            "linecolor": "#4d9fff",
            "title": {"text": "Saisonal %",
                      "font": {"color": "#4d9fff", "size": 10}},
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
html, body {{ width:100%; height:100%; background:#080b10; overflow:hidden; }}

.se-labels {{
  display:flex; justify-content:space-between; align-items:center;
  padding:0 4px 6px;
  font-family:system-ui,sans-serif;
  font-size:11px; font-weight:600; letter-spacing:.8px; text-transform:uppercase;
}}
.lbl-b {{ color:#4d9fff; }}
.lbl-i {{ color:rgba(255,255,255,0.25); font-size:10px; letter-spacing:.2px;
          text-transform:none; font-weight:400; }}
.lbl-a {{ color:rgba(200,220,255,0.65); }}

.split-wrap {{
  position:relative; width:100%; height:{ch}px;
  border:1px solid #1a2538; border-radius:10px; overflow:hidden;
  background:#080b10;
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

/* Saisonal: sichtbar LINKS vom Divider */
#layer-b {{ clip-path: inset(0 50% 0 0); z-index:2; will-change:clip-path; }}

/* Einzeljahre: sichtbar RECHTS vom Divider */
#layer-a {{ clip-path: inset(0 0 0 50%); z-index:3; will-change:clip-path; }}

/* Divider + Handle über allem */
.divider {{
  position:absolute; top:0; left:50%; width:2px; height:100%;
  background:linear-gradient(180deg,
    transparent 0%, #4d9fff 15%, #4d9fff 85%, transparent 100%);
  z-index:8; pointer-events:none; transform:translateX(-50%);
}}
.div-handle {{
  position:absolute; top:50%; left:50%;
  transform:translate(-50%,-50%);
  width:30px; height:30px; background:#4d9fff; border-radius:50%;
  z-index:9; pointer-events:none;
  display:flex; align-items:center; justify-content:center;
  color:#080b10; font-size:12px; font-weight:800;
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
  border:2px solid #4d9fff; cursor:ew-resize;
}}
.bar-wrap input[type=range]::-moz-range-thumb {{
  width:18px; height:18px; border-radius:50%;
  background:#fff; border:2px solid #4d9fff; cursor:ew-resize;
}}
.bar-icon {{ font-size:11px; color:rgba(255,255,255,0.55);
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

  <div class="divider"    id="divider"></div>
  <div class="div-handle" id="handle">↔</div>
  <input type="range" min="0" max="100" value="50"
         class="sl-ov" id="sl-ov">
</div>

<div class="bar-wrap">
  <span class="bar-icon">← Ø Saisonal</span>
  <input type="range" min="0" max="100" value="50" id="sl-bar">
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

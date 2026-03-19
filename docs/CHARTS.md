# Charts & UI — SeasonalEdge

## Plotly Custom Theme (shared/charts.py)

### Farb-Palette (Highcharts dark-unica inspiriert)
```python
SE_COLORS = {
    "bg": "#080c12", "surface": "#0f1923", "surface_alt": "#131d2a",
    "panel_border": "#1c2a3e",
    "grid": "rgba(255,255,255,0.04)", "grid_major": "rgba(255,255,255,0.07)",
    "axis_line": "rgba(255,255,255,0.12)", "zero_line": "rgba(77,159,255,0.25)",
    "text_primary": "#c8d6e5", "text_muted": "#5a6e85", "text_dim": "#3a4a5e",
    "accent": "#00d4aa", "accent_warm": "#e8a425", "accent_blue": "#4d9fff",
    "positive": "#00d4aa", "negative": "#ff4757",
    "current_year": "rgba(232,164,37,0.92)",
    "individual": "rgba(160,180,210,0.18)",
}
```

### apply_se_theme() + Varianten
```python
fig = apply_se_theme(fig, title="SPY · Saisonal", height=480, show_watermark=True)
fig = apply_se_heatmap_theme(fig, title="Heatmap", height=420)
fig = apply_se_box_theme(fig, title="Box-Plot", height=420)
line = se_line_style("#00d4aa", width=2, dash="solid", spline=True)
st.plotly_chart(fig, use_container_width=True)
```

### Dual-Axis
```python
layout = {"yaxis": {"side": "left"}, "yaxis2": {"side": "right", "overlaying": "y"}}
```

### Plotly Fallstricke
- `titlefont` deprecated → `title=dict(text=..., font=dict(...))`
- `add_vline` mit String-Labels crasht → `add_shape` + `add_annotation`
- `fillcolor` Hex→rgba: `int(hex[1:3], 16)` manuell
- Typed Arrays (v2.x): `json.dumps()` + `Plotly.newPlot`

## Split-Slider (shared/split_slider.py) — v7

### 3-Layer-Architektur
Plotly clippt Achsenbeschriftungen mit → 3 überlagerte Divs:

```
Layer 1 (layer-axes)  z-index:1  KEIN clip  → Achsen immer sichtbar
Layer 2 (layer-b)     z-index:2  clip LINKS → Ø Saisonal (#4d9fff)
Layer 3 (layer-a)     z-index:3  clip RECHTS → Einzeljahre
```

### Clip-Path
```javascript
layerB.style.clipPath = `inset(0 ${100-pct}% 0 0)`;
layerA.style.clipPath = `inset(0 0 0 ${pct}%)`;
```

### Design
- Aktuelles Jahr: `rgba(232,164,37,0.90)`, width=2.5
- Andere Jahre: `rgba(200,220,255,0.40)`, width=1.0
- Kein `fill: "toself"` / `fill: "tozeroy"`
- Kein `@st.cache_data` auf `load_dj_data`

### API
```python
from shared.split_slider import render_split_slider
render_split_slider(df, height=520, info="77 Jahre")
# df: year, trading_day, cum_return_pct
```

## Distribution Charts (shared/distribution_charts.py)

| Funktion | Beschreibung |
|----------|-------------|
| `build_box_plot()` | Generischer Box-Plot |
| `build_monthly_heatmap()` | Heatmap Jahre x Monate |
| `build_decade_monthly_heatmap()` | Heatmap Dekaden x Monate |
| `build_monthly_bar_with_vola()` | Balken + Vola (2. Y-Achse) |
| `get_current_context_stats()` | Statistiken + Rating |

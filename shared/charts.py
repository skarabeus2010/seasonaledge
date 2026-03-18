"""
shared/charts.py — Plotly Custom Theme für SeasonalEdge

Verwendung:
    fig = go.Figure(...)
    fig = apply_se_theme(fig, title="SPY · Saisonal 1993-2025")
    st.plotly_chart(fig, use_container_width=True)
"""
import plotly.graph_objects as go

# ── SeasonalEdge Farb-Palette ───────────────────────

SE_COLORS = {
    "bg":         "#080c12",
    "surface":    "#0e1520",
    "grid":       "#1c2636",
    "accent":     "#00e5c3",     # Teal
    "accent2":    "#ff6b35",     # Orange
    "text":       "#e8edf5",
    "muted":      "#4a5568",
    "positive":   "#00e5c3",
    "negative":   "#ff4757",
    "current_yr": "rgba(232,164,37,0.90)",
    "other_yr":   "rgba(200,220,255,0.40)",
}


def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    """Hex-Farbe in rgba() umwandeln."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def apply_se_theme(fig: go.Figure, title: str = "", height: int = 420) -> go.Figure:
    """1 Zeile pro Chart — einheitliches SeasonalEdge Theme."""
    fig.update_layout(
        paper_bgcolor=SE_COLORS["bg"],
        plot_bgcolor=SE_COLORS["bg"],
        height=height,
        font=dict(
            family="DM Mono, monospace",
            color=SE_COLORS["muted"],
            size=11,
        ),
        title=dict(
            text=title,
            font=dict(color=SE_COLORS["text"], size=14),
            x=0.01,
        ),
        margin=dict(t=40, r=20, b=40, l=52),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=SE_COLORS["surface"],
            bordercolor=SE_COLORS["accent"],
            font=dict(color=SE_COLORS["text"], size=12),
        ),
        legend=dict(
            bgcolor="rgba(14,21,32,0.8)",
            bordercolor=SE_COLORS["grid"],
            borderwidth=1,
            font=dict(color=SE_COLORS["muted"], size=10),
        ),
        xaxis=dict(
            gridcolor=SE_COLORS["grid"],
            linecolor=SE_COLORS["grid"],
            tickcolor=SE_COLORS["grid"],
            zeroline=False,
        ),
        yaxis=dict(
            gridcolor=SE_COLORS["grid"],
            linecolor=SE_COLORS["grid"],
            tickcolor=SE_COLORS["grid"],
            zeroline=True,
            zerolinecolor="#2d3f57",
            zerolinewidth=1,
        ),
    )
    return fig


def apply_dual_axis(fig: go.Figure) -> go.Figure:
    """Dual-Axis Layout hinzufügen (rechte Y-Achse)."""
    fig.update_layout(
        yaxis2=dict(
            side="right",
            overlaying="y",
            gridcolor=SE_COLORS["grid"],
            linecolor=SE_COLORS["grid"],
            tickcolor=SE_COLORS["grid"],
            zeroline=False,
        )
    )
    return fig

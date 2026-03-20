"""
SeasonalEdge - Zentrales UI Design
====================================
Einmal pro Page aufrufen: inject_se_css()
Alle Streamlit-Level Styles an einer Stelle.
"""

import streamlit as st
from shared.constants import SE_COLORS


# ── Global CSS ──────────────────────────────────────────────────
_SE_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Base ── */
html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}}

.stApp {{
    background-color: {SE_COLORS["bg"]};
}}

[data-testid="stSidebar"] {{
    background-color: {SE_COLORS["surface"]};
    border-right: 1px solid {SE_COLORS["panel_border"]};
}}

/* ── Header & Footer ausblenden ── */
#MainMenu, footer, header {{ visibility: hidden; }}

/* ── Block Container ── */
.block-container {{
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
}}

/* ── Plotly Charts ── */
[data-testid="stPlotlyChart"] {{
    border-radius: 8px;
    overflow: hidden;
}}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {{
    gap: 0;
    background-color: {SE_COLORS["surface"]};
    border-radius: 8px;
    padding: 4px;
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 6px;
    color: {SE_COLORS["text_muted"]};
    font-weight: 500;
}}
.stTabs [aria-selected="true"] {{
    background-color: {SE_COLORS["surface_alt"]};
    color: {SE_COLORS["text_primary"]};
}}

/* ── Metrics ── */
[data-testid="stMetric"] {{
    background-color: {SE_COLORS["surface"]};
    border: 1px solid {SE_COLORS["panel_border"]};
    border-radius: 10px;
    padding: 0.8rem 1rem;
}}
[data-testid="stMetricLabel"] {{
    color: {SE_COLORS["text_muted"]} !important;
    font-size: 0.8rem !important;
}}

/* ── Selectbox / Inputs ── */
[data-baseweb="select"] > div {{
    background-color: {SE_COLORS["surface"]} !important;
    border-color: {SE_COLORS["panel_border"]} !important;
}}

/* ── Expander ── */
.streamlit-expanderHeader {{
    background-color: {SE_COLORS["surface"]};
    border-radius: 8px;
    color: {SE_COLORS["text_primary"]} !important;
}}

/* ── DataFrames / Tables ── */
[data-testid="stDataFrame"] {{
    border: 1px solid {SE_COLORS["panel_border"]};
    border-radius: 8px;
    overflow: hidden;
}}

/* ── Multiselect Tags (ausgewählte Chips) ── */
[data-baseweb="tag"] {{
    background-color: {SE_COLORS["surface_alt"]} !important;
    border: 1px solid {SE_COLORS["accent_blue"]} !important;
    color: {SE_COLORS["text_primary"]} !important;
}}
[data-baseweb="tag"] span {{
    color: {SE_COLORS["text_primary"]} !important;
}}
[data-baseweb="tag"] svg {{
    fill: {SE_COLORS["text_muted"]} !important;
}}

/* ── Divider ── */
hr {{
    border-color: {SE_COLORS["panel_border"]} !important;
}}

/* ── Positive/Negative Werte ── */
.se-positive {{ color: {SE_COLORS["positive"]}; font-weight: 600; }}
.se-negative {{ color: {SE_COLORS["negative"]}; font-weight: 600; }}
.se-muted {{ color: {SE_COLORS["text_muted"]}; }}
</style>
"""


def inject_se_css():
    """Inject das zentrale SeasonalEdge CSS. Einmal pro Page aufrufen."""
    st.markdown(_SE_CSS, unsafe_allow_html=True)


def se_page_header(title: str, icon: str = "", subtitle: str = ""):
    """Einheitlicher Page-Header."""
    header = f"{icon} {title}" if icon else title
    st.markdown(
        f'<h2 style="color:{SE_COLORS["text_primary"]};margin-bottom:0.2rem;">{header}</h2>',
        unsafe_allow_html=True,
    )
    if subtitle:
        st.markdown(
            f'<p style="color:{SE_COLORS["text_muted"]};margin-top:0;font-size:0.9rem;">{subtitle}</p>',
            unsafe_allow_html=True,
        )


def se_metric_card(label: str, value: str, delta: str = "", positive: bool = True):
    """Styled Metric als HTML-Card."""
    delta_color = SE_COLORS["positive"] if positive else SE_COLORS["negative"]
    delta_html = f'<div style="color:{delta_color};font-size:0.85rem;font-weight:600;">{delta}</div>' if delta else ""
    st.markdown(
        f"""<div style="background:{SE_COLORS['surface']};border:1px solid {SE_COLORS['panel_border']};
        border-radius:10px;padding:0.8rem 1rem;">
            <div style="color:{SE_COLORS['text_muted']};font-size:0.75rem;text-transform:uppercase;
            letter-spacing:0.05em;margin-bottom:0.3rem;">{label}</div>
            <div style="color:{SE_COLORS['text_primary']};font-size:1.4rem;font-weight:700;">{value}</div>
            {delta_html}
        </div>""",
        unsafe_allow_html=True,
    )


def se_section_divider(title: str = ""):
    """Dezente Trennlinie mit optionalem Titel."""
    if title:
        st.markdown(
            f'<div style="border-top:1px solid {SE_COLORS["panel_border"]};'
            f'padding-top:1rem;margin-top:1.5rem;margin-bottom:0.5rem;'
            f'color:{SE_COLORS["text_muted"]};font-size:0.8rem;'
            f'text-transform:uppercase;letter-spacing:0.1em;">{title}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f'<hr style="border-color:{SE_COLORS["panel_border"]};margin:1.5rem 0;">', unsafe_allow_html=True)

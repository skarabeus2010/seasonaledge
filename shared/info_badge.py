"""
shared/info_badge.py — Info-Badge ⓘ für Expander
==================================================
Ghost-Container-Strategie: Badge wird VOR dem Expander gerendert
in einem height:0 Container. Per position:absolute + top:45px
schwebt es optisch im Header des darunterliegenden Expanders.

Verwendung:
    from shared.info_badge import render_info_badge
    render_info_badge("anomalie_radar")          # ← VOR dem Expander
    with st.expander("Anomalie-Radar (KI)", expanded=True):
        # ... Content
"""

from pathlib import Path
from functools import lru_cache

import streamlit as st
import yaml


_YAML_PATH = Path(__file__).resolve().parent / "info_texts.yaml"
_CSS_KEY = "_info_badge_css_v6"

_CSS = """
<style>
/* ── Ghost-Container: nimmt keinen Platz ein ── */
.se-badge-ghost {
    position: relative;
    height: 0px;
    width: 100%;
    z-index: 999;
    overflow: visible;
}

/* ── Badge-Overlay: schwebt nach unten in den Expander-Header ── */
.se-badge-overlay {
    position: absolute;
    top: 45px;
    right: 45px;
}

/* ── Das i-Badge ── */
.se-badge-overlay .se-ib {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.15rem;
    height: 1.15rem;
    border-radius: 50%;
    background: rgba(77,159,255,0.15);
    color: #4d9fff;
    font-size: 0.6rem;
    font-weight: 700;
    cursor: help;
    user-select: none;
    transition: background 0.2s;
    line-height: 1;
}
.se-badge-overlay .se-ib:hover {
    background: rgba(77,159,255,0.35);
}

/* ── Tooltip bei Hover ── */
.se-badge-overlay .se-tip {
    display: none;
    position: absolute;
    right: 0;
    top: 1.6rem;
    width: 320px;
    max-width: 80vw;
    background: #131d2a;
    border: 1px solid #1c2a3e;
    border-radius: 10px;
    padding: 0.75rem 1rem;
    font-size: 0.78rem;
    line-height: 1.55;
    color: #a0b0c5;
    box-shadow: 0 8px 24px rgba(0,0,0,0.4);
    z-index: 1000;
    pointer-events: auto;
}
.se-badge-overlay:hover .se-tip {
    display: block;
}
</style>
"""


@lru_cache(maxsize=1)
def _load_texts() -> dict:
    """Laedt info_texts.yaml einmal und cached das Ergebnis."""
    if not _YAML_PATH.exists():
        return {}
    with open(_YAML_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _get_lang() -> str:
    """Aktuelle Sprache aus i18n holen (Fallback: de)."""
    try:
        from shared.i18n import get_lang
        return get_lang()
    except Exception:
        return "de"


def render_info_badge(key: str) -> None:
    """
    Rendert ein ⓘ-Badge als Ghost-Container VOR dem Expander.
    Das Badge schwebt per CSS in den Header des nächsten Expanders.

    MUSS direkt VOR dem zugehörigen st.expander() aufgerufen werden.

    Args:
        key: Schlüssel aus info_texts.yaml (z.B. "anomalie_radar")
    """
    texts = _load_texts()
    entry = texts.get(key)
    if not entry:
        return

    lang = _get_lang()
    text = entry.get(lang) or entry.get("de") or ""
    if not text:
        return

    # CSS einmal pro Session injizieren
    if not st.session_state.get(_CSS_KEY):
        st.markdown(_CSS, unsafe_allow_html=True)
        st.session_state[_CSS_KEY] = True

    # Ghost-Container + Badge
    st.markdown(
        f'<div class="se-badge-ghost">'
        f'<div class="se-badge-overlay">'
        f'<span class="se-ib">i</span>'
        f'<div class="se-tip">{text}</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

"""
shared/info_badge.py — Info-Badge ⓘ für Expander
==================================================
Zeigt ein kleines ⓘ-Icon rechts oben im Expander.
Hover → Tooltip mit kurzer Erklärung erscheint.
Nimmt keinen vertikalen Platz weg (float + negativer Margin).
Texte zentral in shared/info_texts.yaml, i18n-ready (DE/EN).

Verwendung:
    from shared.info_badge import render_info_badge
    render_info_badge("anomalie_radar")          # ← VOR dem Expander!
    with st.expander("Anomalie-Radar (KI)", expanded=True):
        # ... Content
"""

from pathlib import Path
from functools import lru_cache

import streamlit as st
import yaml


_YAML_PATH = Path(__file__).resolve().parent / "info_texts.yaml"

# CSS wird einmal pro Session injiziert
_CSS_KEY = "_info_badge_css_injected"

_CSS = """
<style>
/* Info-Badge: wird VOR dem Expander gerendert.
   Das Streamlit-div hat margin-bottom → das Badge "fällt" per
   negativem margin in die nächste Zeile (= Expander-Header). */
.se-info-wrap {
    height: 0;
    overflow: visible;
    position: relative;
    z-index: 10;
    text-align: right;
    margin-bottom: 0;
    padding-right: 1rem;
    /* Schiebt das Badge in die NÄCHSTE Zeile (den Expander-Header) */
    transform: translateY(2.35rem);
}
.se-info-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.2rem;
    height: 1.2rem;
    border-radius: 50%;
    background: rgba(77,159,255,0.15);
    color: #4d9fff;
    font-size: 0.65rem;
    font-weight: 700;
    cursor: help;
    user-select: none;
    transition: background 0.2s;
    line-height: 1;
}
.se-info-badge:hover {
    background: rgba(77,159,255,0.35);
}
.se-info-tip {
    display: none;
    position: absolute;
    right: 1rem;
    top: 1.5rem;
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
    z-index: 100;
}
.se-info-wrap:hover .se-info-tip {
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
    Rendert ein ⓘ-Badge mit Hover-Tooltip.
    Nimmt keinen vertikalen Platz weg (float + negativer Margin).

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

    st.markdown(
        f'<div class="se-info-wrap">'
        f'<span class="se-info-badge">i</span>'
        f'<div class="se-info-tip">{text}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

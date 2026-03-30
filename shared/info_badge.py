"""
shared/info_badge.py — Info-Badge ⓘ für Expander
==================================================
Zeigt ein kleines ⓘ-Icon in der Expander-Header-Leiste.
Hover → Tooltip mit kurzer Erklärung.
Texte zentral in shared/info_texts.yaml, i18n-ready (DE/EN).

Technik (Pure CSS, kein JavaScript):
    1. Globales CSS setzt [data-testid="stExpander"] auf position:relative
    2. Badge wird als ERSTES Element INNERHALB des Expanders gerendert
    3. position:absolute + top:-2.35rem + right:2rem schiebt es optisch
       in die Header-Leiste hoch
    4. height:0 + overflow:visible → nimmt keinen Platz im Content weg

Verwendung:
    from shared.info_badge import render_info_badge
    with st.expander("Anomalie-Radar (KI)", expanded=True):
        render_info_badge("anomalie_radar")   # ← ERSTES Element im Expander
        # ... restlicher Content
"""

from pathlib import Path
from functools import lru_cache

import streamlit as st
import yaml


_YAML_PATH = Path(__file__).resolve().parent / "info_texts.yaml"
_CSS_KEY = "_info_badge_css_v5"

_CSS = """
<style>
/* ── Expander-Container: position:relative als Anker ── */
div[data-testid="stExpander"] {
    position: relative !important;
}

/* ── Badge-Wrapper: absolut positioniert, in Header-Höhe ── */
.se-info-wrap {
    position: absolute !important;
    top: 0.55rem;
    right: 2rem;
    z-index: 99;
    height: 0 !important;
    overflow: visible !important;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 0 !important;
}

/* ── Das i-Badge selbst ── */
.se-info-badge {
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
.se-info-badge:hover {
    background: rgba(77,159,255,0.35);
}

/* ── Tooltip bei Hover ── */
.se-info-tip {
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
    z-index: 999;
    pointer-events: auto;
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
    MUSS als ERSTES Element INNERHALB des st.expander() aufgerufen werden.

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

    # Badge — position:absolute hebt es in die Header-Leiste
    st.markdown(
        f'<div class="se-info-wrap">'
        f'<span class="se-info-badge">i</span>'
        f'<div class="se-info-tip">{text}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

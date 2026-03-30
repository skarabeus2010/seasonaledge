"""
shared/info_badge.py — Info-Badge ⓘ für Expander
==================================================
Zeigt ein kleines ⓘ-Icon rechts oben im Expander.
Bei Klick erscheint ein Popover mit einer kurzen Erklärung.
Texte zentral in shared/info_texts.yaml, i18n-ready (DE/EN).

Verwendung:
    from shared.info_badge import render_info_badge
    with st.expander("Anomalie-Radar (KI)", expanded=True):
        render_info_badge("anomalie_radar")
        # ... restlicher Content
"""

import os
from pathlib import Path
from functools import lru_cache

import streamlit as st
import yaml


_YAML_PATH = Path(__file__).resolve().parent / "info_texts.yaml"


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
    Rendert ein ⓘ-Badge als Popover mit Erklärungstext.

    Args:
        key: Schlüssel aus info_texts.yaml (z.B. "anomalie_radar")
    """
    texts = _load_texts()
    entry = texts.get(key)
    if not entry:
        return  # Key nicht gefunden → nichts rendern

    lang = _get_lang()
    text = entry.get(lang) or entry.get("de") or ""
    if not text:
        return

    # Rechts ausgerichtetes Popover mit ⓘ-Icon
    cols = st.columns([0.92, 0.08])
    with cols[1]:
        with st.popover("ⓘ"):
            st.markdown(
                f'<div style="font-size:0.85rem;line-height:1.6;color:#a0b0c5;">{text}</div>',
                unsafe_allow_html=True,
            )

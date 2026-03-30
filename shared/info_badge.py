"""
shared/info_badge.py — Info-Badge ⓘ für Expander
==================================================
MutationObserver-Strategie:

  1. render_info_badge("key") wird als ERSTE Zeile INSIDE des
     with st.expander() aufgerufen.
  2. Das Badge-HTML trägt die Klasse `se-ib-wrapper` und ist
     zunächst unsichtbar (visibility:hidden, height:0).
  3. Ein permanenter MutationObserver wartet auf
     [data-testid="stExpander"] Elemente. Sobald eines auftaucht,
     wird `.se-ib-wrapper` mit appendChild() physisch in den
     <summary>-Tag verschoben.
  4. CSS macht das Badge erst sichtbar, wenn es sich im <summary>
     befindet — Streamlit's Flexbox richtet es automatisch rechts aus.

Verwendung:
    from shared.info_badge import render_info_badge

    with st.expander("Anomalie-Radar (KI)", expanded=True):
        render_info_badge("anomalie_radar")   # ← ERSTE Zeile inside
        # ... restlicher Content
"""

from pathlib import Path
from functools import lru_cache

import streamlit as st
import yaml


_YAML_PATH = Path(__file__).resolve().parent / "info_texts.yaml"
_CSS_JS_KEY = "_info_badge_v8"

# ── CSS ────────────────────────────────────────────────────────────────────
_CSS = """
<style>
/* Badge unsichtbar solange es im Content-Bereich des Expanders liegt */
.se-ib-wrapper {
    visibility: hidden;
    height: 0;
    overflow: hidden;
    pointer-events: none;
}

/* Badge sichtbar + positioniert sobald es im <summary> ist */
[data-testid="stExpander"] summary .se-ib-wrapper {
    visibility: visible;
    height: auto;
    overflow: visible;
    pointer-events: auto;
    /* summary ist ein Flexbox in Streamlit → auto-margin schiebt nach rechts */
    margin-left: auto;
    margin-right: 2.5rem;   /* Platz für den Expand-Pfeil */
    flex-shrink: 0;
    position: relative;
    z-index: 10;
}

/* Das i-Kreis-Badge */
.se-ib-wrapper .se-ib {
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
    vertical-align: middle;
}
.se-ib-wrapper .se-ib:hover {
    background: rgba(77,159,255,0.35);
}

/* Tooltip */
.se-ib-wrapper .se-tip {
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
    z-index: 9999;
    pointer-events: auto;
    white-space: normal;
}
.se-ib-wrapper:hover .se-tip {
    display: block;
}
</style>
"""

# ── JavaScript — einmaliger permanenter MutationObserver ───────────────────
_JS = """
<script>
(function() {
    if (window.__seInfoBadgeObserver) return;   // nur einmal initialisieren

    function moveBadges() {
        document.querySelectorAll('[data-testid="stExpander"]').forEach(function(expander) {
            var summary = expander.querySelector('summary');
            if (!summary) return;

            // Alle Badges im Content-Bereich dieses Expanders suchen
            var contentArea = expander.querySelector('[data-testid="stExpanderDetails"]');
            if (!contentArea) {
                // Fallback: direkt im expander suchen (außerhalb von summary)
                contentArea = expander;
            }

            contentArea.querySelectorAll('.se-ib-wrapper').forEach(function(badge) {
                if (!summary.contains(badge)) {
                    summary.appendChild(badge);
                }
            });
        });
    }

    // Initialer Durchlauf (für bereits gerenderte Expander)
    moveBadges();

    // Observer für dynamisch nachgeladene Inhalte (Streamlit re-renders)
    var observer = new MutationObserver(function(mutations) {
        var relevant = mutations.some(function(m) {
            return m.addedNodes.length > 0;
        });
        if (relevant) moveBadges();
    });

    observer.observe(document.body, { childList: true, subtree: true });
    window.__seInfoBadgeObserver = observer;
})();
</script>
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
    Rendert ein ⓘ-Badge das per MutationObserver in den Expander-Header
    verschoben wird.

    MUSS als ERSTE Zeile INNERHALB des with st.expander() Blocks stehen:

        with st.expander("Titel", expanded=True):
            render_info_badge("mein_key")   # ← erste Zeile
            # ... restlicher Content

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

    # CSS + JS einmalig pro Session injizieren
    if not st.session_state.get(_CSS_JS_KEY):
        st.markdown(_CSS + _JS, unsafe_allow_html=True)
        st.session_state[_CSS_JS_KEY] = True

    # Badge-HTML (startet unsichtbar, wird per JS in <summary> verschoben)
    safe_key = key.replace("_", "-")
    st.markdown(
        f'<div class="se-ib-wrapper" id="se-badge-{safe_key}">'
        f'<span class="se-ib">i</span>'
        f'<div class="se-tip">{text}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

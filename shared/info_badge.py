"""
shared/info_badge.py — Info-Badge ⓘ für Expander
==================================================
Zeigt ein kleines ⓘ-Icon DIREKT in der Expander-Header-Leiste.
Hover → Tooltip mit kurzer Erklärung.
Texte zentral in shared/info_texts.yaml, i18n-ready (DE/EN).

Technik:
    Streamlit rendert <summary> (Header) und Content in getrennten
    DOM-Containern. Per st.markdown() kann man nichts in den Header
    injizieren. Lösung: Badge wird als verstecktes HTML gerendert,
    ein JS-Snippet verschiebt es in das <summary>-Element des
    nächsten Expanders.

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

# Keys für einmalige Injection pro Session
_CSS_KEY = "_info_badge_css_injected"
_JS_KEY = "_info_badge_js_injected"

# ── CSS ──────────────────────────────────────────────────
_CSS = """
<style>
/* Badge-Wrapper: Inline im <summary>, rechts angedockt */
.se-info-wrap {
    position: absolute;
    right: 2.5rem;
    top: 50%;
    transform: translateY(-50%);
    z-index: 10;
}
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
/* Tooltip */
.se-info-tip {
    display: none;
    position: absolute;
    right: 0;
    top: 1.8rem;
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
/* Verstecktes Placeholder-Element (vor JS-Verschiebung) */
.se-info-pending {
    display: none !important;
    height: 0 !important;
    overflow: hidden !important;
}
</style>
"""

# ── JavaScript ───────────────────────────────────────────
# Sucht alle .se-info-pending Elemente, findet den nächsten
# Expander-Sibling und verschiebt das Badge in dessen <summary>.
_JS = """
<script>
(function() {
    function moveInfoBadges() {
        document.querySelectorAll('.se-info-pending').forEach(function(pending) {
            // Navigiere hoch zum Streamlit element-container
            var container = pending.closest('.element-container')
                         || pending.closest('[data-testid="stMarkdown"]')
                         || pending.parentElement;
            if (!container) return;

            // Suche den nächsten Geschwister-Container mit einem Expander
            var sibling = container.nextElementSibling;
            var maxSteps = 5;
            while (sibling && maxSteps-- > 0) {
                var expander = sibling.querySelector('[data-testid="stExpander"]')
                            || sibling.querySelector('details');
                if (expander) {
                    var summary = expander.querySelector('summary');
                    if (summary) {
                        // summary braucht position:relative für das absolute Badge
                        summary.style.position = 'relative';
                        // Badge aus dem Pending-Container holen und in summary einfügen
                        var badge = pending.querySelector('.se-info-wrap');
                        if (badge) {
                            badge.style.display = '';
                            summary.appendChild(badge);
                        }
                    }
                    // Pending-Container entfernen (spart DOM-Platz)
                    pending.remove();
                    return;
                }
                sibling = sibling.nextElementSibling;
            }
        });
    }

    // Streamlit rendert asynchron → mehrere Versuche
    setTimeout(moveInfoBadges, 200);
    setTimeout(moveInfoBadges, 800);
    setTimeout(moveInfoBadges, 2000);

    // MutationObserver für dynamische Re-Renders (Tab-Wechsel etc.)
    var observer = new MutationObserver(function(mutations) {
        var hasPending = document.querySelector('.se-info-pending');
        if (hasPending) {
            setTimeout(moveInfoBadges, 100);
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });
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
    Rendert ein ⓘ-Badge das per JS in den Expander-Header verschoben wird.
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

    # CSS + JS einmal pro Session injizieren
    if not st.session_state.get(_CSS_KEY):
        st.markdown(_CSS, unsafe_allow_html=True)
        st.session_state[_CSS_KEY] = True
    if not st.session_state.get(_JS_KEY):
        st.markdown(_JS, unsafe_allow_html=True)
        st.session_state[_JS_KEY] = True

    # Badge als verstecktes Element rendern — JS verschiebt es in den Header
    st.markdown(
        f'<div class="se-info-pending">'
        f'<div class="se-info-wrap">'
        f'<span class="se-info-badge">i</span>'
        f'<div class="se-info-tip">{text}</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

"""
SeasonAlpha — Indikator-Filter UI
===================================
Sidebar-Controls fuer technische Indikator-Filter.
Rendert Pulldown-Menus, Slider und Filter-Badges.
"""

import streamlit as st
from shared.indicators import INDICATOR_REGISTRY


# ── Sidebar ──────────────────────────────────────────────────

def indicator_filter_sidebar(key_prefix: str = "ind",
                             max_filters: int = 4) -> list[dict]:
    """Rendert Sidebar-Controls fuer Indikator-Filter.

    Returns
    -------
    list[dict] — Aktive Filter, z.B.:
        [{"type": "RSI", "period": 14, "threshold": 30, "condition": "RSI < Schwelle"}]
        Leere Liste = kein Filter aktiv.
    """
    st.sidebar.markdown("---")
    with st.sidebar.expander("🔧 Technische Filter", expanded=False):
        # Anzahl aktiver Filter
        n_filters_key = f"{key_prefix}_n_filters"
        if n_filters_key not in st.session_state:
            st.session_state[n_filters_key] = 0

        n_filters = st.session_state[n_filters_key]

        filters = []
        remove_idx = None

        for i in range(n_filters):
            st.markdown(f"**Filter {i + 1}**")
            cols = st.columns([3, 1])

            # Indikator-Auswahl
            ind_names = list(INDICATOR_REGISTRY.keys())
            ind_key = f"{key_prefix}_ind_type_{i}"
            selected_ind = cols[0].selectbox(
                "Indikator", ind_names,
                key=ind_key, label_visibility="collapsed"
            )

            # Entfernen-Button
            if cols[1].button("✕", key=f"{key_prefix}_rm_{i}"):
                remove_idx = i

            reg = INDICATOR_REGISTRY[selected_ind]
            f = {"type": selected_ind}

            # Parameter-Slider
            for p in reg["params"]:
                p_key = f"{key_prefix}_p_{i}_{p['name']}"
                step = p.get("step", 1)
                if isinstance(p["default"], float):
                    val = st.slider(
                        p["label"], min_value=float(p["min"]),
                        max_value=float(p["max"]),
                        value=float(p["default"]), step=float(step),
                        key=p_key
                    )
                else:
                    val = st.slider(
                        p["label"], min_value=int(p["min"]),
                        max_value=int(p["max"]),
                        value=int(p["default"]), step=int(step),
                        key=p_key
                    )
                f[p["name"]] = val

            # Bedingung
            cond_key = f"{key_prefix}_cond_{i}"
            cond = st.selectbox(
                "Bedingung", reg["conditions"],
                key=cond_key, label_visibility="collapsed"
            )
            f["condition"] = cond
            filters.append(f)

            if i < n_filters - 1:
                st.markdown("<hr style='margin:4px 0;border-color:rgba(255,255,255,0.1)'>",
                            unsafe_allow_html=True)

        # Entfernen
        if remove_idx is not None:
            new_n = max(0, n_filters - 1)
            st.session_state[n_filters_key] = new_n
            st.rerun()

        # Hinzufuegen-Button
        if n_filters < max_filters:
            if st.button("＋ Filter hinzufügen", key=f"{key_prefix}_add_filter"):
                st.session_state[n_filters_key] = n_filters + 1
                st.rerun()

        # Info-Text wenn Filter aktiv
        if filters:
            badge_text = " **UND** ".join([_filter_label(f) for f in filters])
            st.markdown(
                f"<div style='background:rgba(77,159,255,0.1);border:1px solid "
                f"rgba(77,159,255,0.3);border-radius:6px;padding:6px 10px;"
                f"margin-top:8px;font-size:12px;color:#c8d6e5;'>"
                f"Aktiv: {badge_text}</div>",
                unsafe_allow_html=True
            )

    return filters


# ── Filter-Badge (ueber dem Chart) ──────────────────────────

def render_filter_badge(filters: list[dict], total_days: int = 0,
                        filtered_days: int = 0):
    """Zeigt aktive Filter als kompaktes Badge ueber dem Chart."""
    if not filters:
        return

    labels = [_filter_label(f) for f in filters]
    badge_text = " | ".join(labels)

    pct = ""
    if total_days > 0 and filtered_days > 0:
        pct_val = filtered_days / total_days * 100
        pct = f" — {filtered_days:,} / {total_days:,} Tage ({pct_val:.1f}%)"

    st.markdown(
        f"<div style='background:rgba(77,159,255,0.08);border:1px solid "
        f"rgba(77,159,255,0.25);border-radius:8px;padding:8px 14px;"
        f"margin-bottom:12px;display:flex;align-items:center;gap:8px;'>"
        f"<span style='font-size:14px;'>🔧</span>"
        f"<span style='color:#4d9fff;font-size:13px;font-weight:600;'>"
        f"{badge_text}</span>"
        f"<span style='color:#5a6e85;font-size:12px;'>{pct}</span>"
        f"</div>",
        unsafe_allow_html=True
    )


# ── Helpers ──────────────────────────────────────────────────

def _filter_label(f: dict) -> str:
    """Kompaktes Label fuer einen Filter, z.B. 'RSI(14) < 30'."""
    t = f["type"]
    cond = f.get("condition", "")

    if t in ("SMA", "EMA"):
        period = f.get("period", 200)
        direction = ">" if ">" in cond else "<"
        return f"Close {direction} {t}({period})"

    if t == "RSI":
        period = f.get("period", 14)
        threshold = f.get("threshold", 50)
        direction = ">" if ">" in cond else "<"
        return f"RSI({period}) {direction} {threshold}"

    if t == "Bollinger":
        period = f.get("period", 20)
        std = f.get("num_std", 2.0)
        if "Upper" in cond:
            return f"Close > BB-Upper({period},{std})"
        if "Lower" in cond:
            return f"Close < BB-Lower({period},{std})"
        return f"Close in BB({period},{std})"

    if t == "MACD":
        fast = f.get("fast", 12)
        slow = f.get("slow", 26)
        sig = f.get("signal", 9)
        direction = "bullish" if "bullish" in cond else "bearish"
        return f"MACD({fast},{slow},{sig}) {direction}"

    return t

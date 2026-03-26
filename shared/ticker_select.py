# shared/ticker_select.py — Zentraler Ticker-Autocomplete fuer die Sidebar
#
# Ersetzt st.text_input("Ticker") durch st.selectbox mit Suchfunktion
# + optionalem Freitext-Fallback fuer Ticker ausserhalb der Liste.

import streamlit as st

from shared.symbols import (
    SYMBOLS,
    KATEGORIEN,
    DEFAULT_SYMBOL,
    get_display_name,
)


def _build_options() -> list[str]:
    """Baut die sortierte Ticker-Liste: nach Kategorie, dann alphabetisch."""
    options = []
    for kat in KATEGORIEN:
        tickers_in_kat = sorted(
            [t for t, info in SYMBOLS.items() if info["kategorie"] == kat]
        )
        options.extend(tickers_in_kat)
    return options


# Einmalig beim Import berechnen
_TICKER_OPTIONS = _build_options()
_TICKER_LABELS = {t: f"{t} — {get_display_name(t)}" for t in _TICKER_OPTIONS}


def ticker_select(
    key: str,
    default: str = DEFAULT_SYMBOL,
    label: str = "Ticker",
) -> str:
    """Autocomplete-Ticker-Auswahl fuer die Sidebar.

    Parameters
    ----------
    key : str
        Eindeutiger Streamlit-Widget-Key (z.B. "ys_ticker").
    default : str
        Vorausgewaehlter Ticker (muss in SYMBOLS sein oder Freitext).
    label : str
        Label ueber dem Widget (Standard: "Ticker").

    Returns
    -------
    str
        Reiner Ticker-String (z.B. "SPY", "RHM.DE").
    """
    custom_key = f"{key}_custom"
    default_not_in_list = default not in SYMBOLS

    use_custom = st.toggle(
        "Eigenen Ticker eingeben",
        value=default_not_in_list,
        key=f"{key}_toggle",
    )

    if use_custom:
        ticker = st.text_input(
            label, value=default, key=custom_key
        ).upper().strip()
        return ticker

    # Selectbox mit eingebauter Suche
    try:
        default_idx = _TICKER_OPTIONS.index(default)
    except ValueError:
        default_idx = _TICKER_OPTIONS.index(DEFAULT_SYMBOL)

    selected = st.selectbox(
        label,
        options=_TICKER_OPTIONS,
        index=default_idx,
        format_func=lambda t: _TICKER_LABELS.get(t, t),
        key=key,
    )
    return selected

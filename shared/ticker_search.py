# shared/ticker_search.py
# ============================================================
# GLOBALE SUCH- & MAPPING-KOMPONENTE — SeasonAlpha v8.3
# ============================================================
#
# Verwendung auf JEDER Page (genau eine Zeile in der Sidebar):
#
#   from shared.ticker_search import render_ticker_search
#   ticker, asset_name = render_ticker_search(default_ticker="^GDAXI")
#
# Das zurückgegebene `ticker` ist immer ein gültiges Yahoo-Symbol,
# egal ob der User "Gold", "GC=F" oder "Edelmetall" eingetippt hat.
#
# DESIGN-PRINZIP:
#   - Diese Datei rendert UI. Sie berechnet keine Returns.
#   - Sie ist der einzige Ort für Ticker-Eingabe-Logik.
#   - Alle Pages importieren von hier — kein Copy-Paste.
# ============================================================

from __future__ import annotations
import streamlit as st
from shared.assets import ASSETS, TICKER_MAP, CATEGORIES


# ── Suchalgorithmus ───────────────────────────────────────────────────────────

def search_assets(query: str, max_results: int = 8) -> list[dict]:
    """
    Sucht in ASSETS nach Ticker, Name und Keywords.
    Gibt eine nach Relevanz sortierte Liste zurück.

    Rang-Reihenfolge (höher = besser):
      100 — Exakter Ticker-Match  (z.B. "AAPL" → Apple)
       80 — Ticker beginnt mit Query
       70 — Name beginnt mit Query
       60 — Keyword ist exakter Match
       50 — Keyword beginnt mit Query
       40 — Name enthält Query als Substring
       30 — Keyword enthält Query als Substring
    """
    if not query:
        return []

    q = query.strip().lower()
    if not q:
        return []

    scored: list[tuple[int, dict]] = []

    for asset in ASSETS:
        ticker_low = asset["ticker"].lower()
        name_low   = asset["name"].lower()
        # Keywords als Liste normalisieren
        keywords   = [k.strip().lower() for k in asset.get("keywords", "").split(",")]

        score = 0

        # Erstes Wort des Namens (z.B. "Tesla" aus "Tesla Inc.")
        first_word = name_low.split()[0] if name_low.split() else ""

        if ticker_low == q or ticker_low.replace("^", "") == q:
            score = 100
        elif ticker_low.startswith(q):
            score = 80
        elif first_word == q:
            # "tesla" == "tesla" aus "Tesla Inc." → hohe Priorität
            score = 75
        elif name_low.startswith(q):
            score = 70
        elif q in keywords:
            score = 60
        elif any(kw == q for kw in keywords):
            # Exakter Keyword-Match (einzelnes Wort)
            score = 60
        elif any(kw.startswith(q) for kw in keywords):
            score = 50
        elif q in name_low:
            score = 40
        elif any(q in kw for kw in keywords):
            score = 30

        if score > 0:
            scored.append((score, asset))

    # Primär nach Score (absteigend), sekundär nach Name (alphabetisch)
    scored.sort(key=lambda x: (-x[0], x[1]["name"]))
    return [a for _, a in scored[:max_results]]


def get_display_name(ticker: str) -> str:
    """Gibt den Anzeigenamen für einen Ticker zurück. Fallback: Ticker selbst."""
    asset = TICKER_MAP.get(ticker.upper())
    return asset["name"] if asset else ticker


# ── Haupt-Widget ──────────────────────────────────────────────────────────────

def render_ticker_search(
    default_ticker: str = "^GDAXI",
    key_prefix: str = "ts",
    show_category_filter: bool = True,
) -> tuple[str, str]:
    """
    Rendert die intelligente Ticker-Suchmaske in der Sidebar.

    Funktionsweise:
      1. User tippt Freitext  →  Suchalgorithmus findet passende Assets
      2. Ein Treffer          →  automatisch ausgewählt
      3. Mehrere Treffer      →  Dropdown zur Auswahl
      4. Kein Treffer         →  Direkteingabe als Yahoo-Ticker (Fallback)
      5. Leere Eingabe        →  Kategorie-Dropdown mit Default-Ticker

    Args:
        default_ticker:      Yahoo-Ticker der vorausgewählt ist (leere Eingabe)
        key_prefix:          Streamlit Widget-Key-Prefix (pro Page eindeutig)
        show_category_filter: Kategorie-Filter über der Suche anzeigen

    Returns:
        (ticker, display_name)
        ticker       — gültiges Yahoo Finance Symbol, immer als String
        display_name — Anzeigename für Charts und Überschriften
    """

    # ── 1. Optionaler Kategorie-Filter ────────────────────────────────────────
    if show_category_filter:
        selected_cat = st.sidebar.selectbox(
            "Kategorie",
            options=["Alle"] + CATEGORIES,
            key=f"{key_prefix}_cat",
        )
    else:
        selected_cat = "Alle"

    # ── 2. Freitexteingabe ────────────────────────────────────────────────────
    raw = st.sidebar.text_input(
        "Instrument suchen",
        value="",
        placeholder="z.B. DAX, Gold, Tesla, AAPL …",
        key=f"{key_prefix}_input",
        help=(
            "Ticker (AAPL), Name (Apple) oder Stichwort (Halbleiter) eingeben. "
            "Unbekannte Ticker werden direkt an Yahoo Finance übergeben."
        ),
    )

    query = raw.strip()

    # ── 3a. Freitextsuche aktiv ───────────────────────────────────────────────
    if query:
        results = search_assets(query, max_results=10)

        # Kategorie-Filter auf Suchergebnisse anwenden
        if selected_cat != "Alle":
            results = [r for r in results if r["category"] == selected_cat]

        if not results:
            # Kein Asset gefunden → Direkteingabe als Yahoo-Ticker
            st.sidebar.caption(
                f"⚠️ '{query}' nicht in der Asset-Liste. "
                "Wird direkt an Yahoo Finance übergeben."
            )
            return query.upper(), query.upper()

        if len(results) == 1:
            # Genau ein Treffer → automatisch
            st.sidebar.caption(f"✓ {results[0]['name']}  [{results[0]['ticker']}]")
            return results[0]["ticker"], results[0]["name"]

        # Mehrere Treffer → Dropdown
        options = [f"{r['name']}  [{r['ticker']}]" for r in results]
        chosen  = st.sidebar.selectbox(
            "Treffer auswählen",
            options=options,
            key=f"{key_prefix}_hits",
        )
        idx = options.index(chosen)
        return results[idx]["ticker"], results[idx]["name"]

    # ── 3b. Leere Eingabe → Kategorie-Dropdown ────────────────────────────────
    pool = (
        [a for a in ASSETS if a["category"] == selected_cat]
        if selected_cat != "Alle"
        else ASSETS
    )

    if not pool:
        pool = ASSETS  # Fallback: Kategorie leer → alle zeigen

    options = [f"{a['name']}  [{a['ticker']}]" for a in pool]

    # Default-Ticker in der Liste vorselektieren
    default_asset = TICKER_MAP.get(default_ticker.upper(), {})
    default_name  = default_asset.get("name", default_ticker)
    default_opt   = f"{default_name}  [{default_ticker}]"
    default_idx   = options.index(default_opt) if default_opt in options else 0

    chosen = st.sidebar.selectbox(
        "Instrument wählen",
        options=options,
        index=default_idx,
        key=f"{key_prefix}_browse",
    )
    idx = options.index(chosen)
    return pool[idx]["ticker"], pool[idx]["name"]

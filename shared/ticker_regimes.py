"""
shared/ticker_regimes.py — Regime-Lookup für die Newsletter-„Warum"-Zeile
========================================================================
Lädt `shared/ticker_regimes.json` (erzeugt von scripts/export_ticker_regimes.py) und
liefert je Ticker das OOS-validierte momentum/fade/neutral-Regime + einen kurzen Hinweistext.

Basis = **TS-Regime** (der richtungstragende Score-Teil; SC ist richtungslos und verwässert
GESAMT). Empirie: PR #144 (Per-Ticker-Edge) + PR #145 (OOS-Persistenz ~83 %). Effekt klein,
aber stabil — der Hinweis ordnet einen hohen Score ehrlich ein, dreht die Score-Mathematik NICHT.
"""
from __future__ import annotations

import json
import os

_PATH = os.path.join(os.path.dirname(__file__), "ticker_regimes.json")
_CACHE: dict | None = None

_HINTS = {
    "momentum": "Momentum trägt hier historisch (Score-Follow-through)",
    "fade": "Hoher Score hier historisch eher Rücksetzer (Mean-Reversion)",
}


def _load() -> dict:
    global _CACHE
    if _CACHE is None:
        try:
            with open(_PATH, encoding="utf-8") as f:
                _CACHE = json.load(f).get("regimes", {})
        except Exception:
            _CACHE = {}
    return _CACHE


def get_regime(ticker: str) -> "dict | None":
    """Roh-Regime-Eintrag eines Tickers ({'ts','ts_rho','gesamt','gesamt_rho'}) oder None."""
    return _load().get(ticker)


def regime_hint(ticker: str) -> "dict | None":
    """{'kind': 'momentum'|'fade', 'text': str, 'rho': float} oder None (neutral/unbekannt)."""
    r = get_regime(ticker)
    if not r:
        return None
    kind = r.get("ts")
    if kind in _HINTS:
        return {"kind": kind, "text": _HINTS[kind], "rho": r.get("ts_rho")}
    return None

"""Kursmuster für die Morgen-Mail — Smash Day (Larry Williams).

Regel und Gültigkeit wie in der Ereignisstudie `scripts/research/williams_muster.py` (Plan
docs/review_prompts/2026-10-17_williams_muster_plan_v2.md, Ergebnis in CLAUDE.md v66.23):
  Kauf-Setup     Schluss unter dem Vortagestief   (C_t < L_{t−1})
  Verkauf-Setup  Schluss über dem Vortageshoch    (C_t > H_{t−1})
Nur Aktien und ETFs (wie in der Studie), nur wenn beide Kerzen gültig sind, direkt aufeinanderfolgende Sitzungen
der Börse des Tickers bilden, auf derselben Kursbasis liegen und die jüngste Kerze von der erwarteten Session stammt.
Sonst kein Muster — nie aus einer kopierten, veralteten oder unvollständigen Kerze.

Nutzerentscheidung 2026-10-17: das Muster wird gezeigt, ohne dass der Prüfzeitraum es bestätigt haben muss. Es geht
NICHT in den Score ein.
"""
from __future__ import annotations

import math
from datetime import date

KAUF, VERKAUF = "kauf", "verkauf"


def im_universum(ticker: str) -> bool:
    """Wie die Studie: ohne Krypto, Devisen, Futures, Indizes."""
    return not (ticker.endswith("-USD") or ticker.endswith("=X") or ticker.endswith("=F") or ticker.startswith("^"))


def _f(x) -> float | None:
    if isinstance(x, bool) or x is None:
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def gueltige_kerze(k: dict) -> bool:
    """Endliche, positive OHLC, endlicher log_return, Hoch > Tief, Open/Close innerhalb der Spanne, Volumen > 0
    (wie die Studie: beide Kerzen brauchen einen endlichen Return — Codex R1)."""
    o, h, l, c, v, lr = (_f(k.get(x)) for x in ("open", "high", "low", "close", "volume", "log_return"))
    if None in (o, h, l, c, lr) or min(o, h, l, c) <= 0:
        return False
    return h > l and l <= min(o, c) and h >= max(o, c) and v is not None and v > 0


def gleiche_basis(vorher: dict, jetzt: dict) -> bool:
    """|ln(C/C_vorher) − log_return| ≤ 1e-4 + 1e-4/C — sonst liegt zwischen den Kerzen ein Wechsel der Bereinigung."""
    c0, c1, lr = _f(vorher.get("close")), _f(jetzt.get("close")), _f(jetzt.get("log_return"))
    if None in (c0, c1, lr) or c0 <= 0 or c1 <= 0:
        return False
    return abs(math.log(c1 / c0) - lr) <= 1e-4 + 1e-4 / c1


def smash_day(vorher: dict, jetzt: dict) -> str | None:
    """Nur die Geometrie + Gültigkeit zweier Kerzen; Sitzungsfolge prüft `muster_fuer`."""
    if not (gueltige_kerze(vorher) and gueltige_kerze(jetzt) and gleiche_basis(vorher, jetzt)):
        return None
    c, hv, lv = float(jetzt["close"]), float(vorher["high"]), float(vorher["low"])
    if c < lv:
        return KAUF
    if c > hv:
        return VERKAUF
    return None


def muster_fuer(ticker: str, kerzen: list[dict], session: date | str | None) -> str | None:
    """kerzen: die beiden jüngsten Kerzen [vorher, jetzt] mit date/open/high/low/close/volume/log_return.

    `session` = die zuletzt abgeschlossene Session der Börse des Tickers (Aufrufer: exchange_holidays.letzte_session).
    """
    if not im_universum(ticker) or not kerzen or len(kerzen) < 2 or session is None:
        return None
    from shared.sitzungen import vorherige
    from shared.symbols import get_exchange_for_holidays
    vorher, jetzt = kerzen[-2], kerzen[-1]
    s = session.isoformat() if isinstance(session, date) else str(session)
    if str(jetzt.get("date")) != s:
        return None                                   # jüngste Kerze nicht von der erwarteten Session
    try:
        boerse = get_exchange_for_holidays(ticker)
        if vorherige(s, boerse, einschliesslich=False).isoformat() != str(vorher.get("date")):
            return None                               # Lücke: Vorkerze ist nicht die direkte Vorsitzung
    except (ValueError, TypeError):
        return None
    return smash_day(vorher, jetzt)

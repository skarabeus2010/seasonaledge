#!/usr/bin/env python3
"""
rv_wirkung_paket_a.py — Wirkungsbericht Paket A (2026-10-14), nur lesend.

Realisierte Vola (21 Handelstage, CBOE-Formel) am letzten Kurstag je Ticker des Options-Universums:
alt = aus ln(close_t/close_{t-1}), neu = aus dem gespeicherten log_return. Läuft ohne den neuen Code (eigene Lese- und
Rechenlogik), damit er vor dem Deploy auf dem Server laufen kann. Ausgabe: JSON-Zeile mit @@ERG@@.
"""
import json
import math
import sys

sys.path.insert(0, "/app")
from shared.supabase_client import get_client          # noqa: E402
from shared.options_universe import all_option_tickers  # noqa: E402


def _rv(r):
    if len(r) < 21 or any(x is None or not math.isfinite(x) for x in r[-21:]):
        return None
    s = r[-21:]
    m = sum(s) / 21
    return math.sqrt(252 / 20 * sum((x - m) ** 2 for x in s))


def _f(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


c = get_client()
aus = []
for t in all_option_tickers():
    z = (c.table("prices").select("date,close,log_return").eq("ticker", t).order("date", desc=True)
         .limit(40).execute().data) or []
    z = z[::-1]
    if len(z) < 23:
        aus.append({"t": t, "fehlt": len(z)}); continue
    cl = [_f(x["close"]) for x in z]
    alt = [None] + [math.log(cl[i] / cl[i - 1]) if cl[i] and cl[i - 1] and cl[i] > 0 and cl[i - 1] > 0 else None
                    for i in range(1, len(cl))]
    neu = [_f(x["log_return"]) for x in z]
    ra, rn = _rv(alt), _rv(neu)
    aus.append({"t": t, "d": z[-1]["date"], "alt": ra, "neu": rn,
                "diff_pts": None if ra is None or rn is None else round((rn - ra) * 100, 3)})
print("@@ERG@@" + json.dumps(aus))

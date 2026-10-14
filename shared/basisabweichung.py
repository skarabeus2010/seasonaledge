#!/usr/bin/env python3
"""
basisabweichung.py — Tage, an denen der Schlusskurs-Sprung nicht zum gespeicherten Tagesreturn passt.

WARUM: Der Nightly schreibt nur ein Sieben-Tage-Fenster in `prices`. Ändert die Quelle bei einer Kapitalmaßnahme
(z. B. Reverse-Split) die Kursbasis, tragen die jüngsten Zeilen die neue Basis, die älteren die alte. `log_return`
stimmt (er wird je Zeile aus derselben Lieferung gerechnet), die Schlusskurse springen. Gemessen 2026-10-14
(scripts/research/basisabweichung_diagnose.py): über 370 Ticker und zwei Jahre genau ein Fall — ETHA am 2026-09-30,
Schluss 20,28 → 60,36 bei log_return −0,79 %, Faktor 3,0. Jede Rechnung, die Renditen aus Schlusskursen bildet, sah
dort +110 % (realisierte Vola 380 %, VRP −333 live auf /skew).

Die Regel hier ist nur eine **Prüfung**: sie meldet, sie repariert nicht. Eine automatische Reparatur anhand einer
Schwelle würde Datenfehler und Kapitalmaßnahmen vermischen. Rechnungen mit Renditen nutzen den gespeicherten
`log_return` (shared.data.lade_kurse + shared.realized_vol), Spot-Rollen den unveränderten Schlusskurs.
"""
from __future__ import annotations

import math

SCHWELLE = 0.05      # |ln(close_t/close_{t-1}) − log_return_t|; ~5 % Abweichung, weit über Rundungs- und Dividendeneffekten


def _endlich(x) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def basisabweichungen(zeilen, schwelle: float = SCHWELLE) -> dict:
    """Prüft aufeinanderfolgende Kurszeilen JE TICKER.

    zeilen: Iterable von dicts mit ticker, date, close, log_return (beliebige Reihenfolge).
    Rückgabe: {"treffer": [{ticker, datum, close_vor, close, log_return, basissprung, korrektur_alte_kurse}],
               "paare": n, "geprueft": n, "ohne_return": n, "ungueltiger_kurs": n}
    geprueft = paare − ohne_return − ungueltiger_kurs: nur diese Paare sind tatsächlich verglichen worden.
    basissprung = exp(ln(close_t/close_{t-1}) − log_return_t): um diesen Faktor liegt die neue Basis über der alten;
    ältere Kurse müssten mit genau diesem Faktor multipliziert werden, um zur neuen Basis zu passen.
    Unbrauchbare Paare werden gezählt, nicht still übergangen.
    """
    je = {}
    for z in zeilen:
        t, d = z.get("ticker"), z.get("date")
        if t and d:
            je.setdefault(t, []).append(z)
    out = {"treffer": [], "paare": 0, "geprueft": 0, "ohne_return": 0, "ungueltiger_kurs": 0}
    for t, reihe in je.items():
        reihe.sort(key=lambda z: str(z["date"])[:10])
        for a, b in zip(reihe, reihe[1:]):
            out["paare"] += 1
            ca, cb, lr = _endlich(a.get("close")), _endlich(b.get("close")), _endlich(b.get("log_return"))
            if lr is None:
                out["ohne_return"] += 1
                continue
            if ca is None or cb is None or ca <= 0 or cb <= 0:
                out["ungueltiger_kurs"] += 1
                continue
            out["geprueft"] += 1
            d = math.log(cb / ca) - lr
            if abs(d) > schwelle:
                out["treffer"].append({"ticker": t, "datum": str(b["date"])[:10], "close_vor": ca, "close": cb,
                                       "log_return": lr, "basissprung": round(math.exp(d), 4),
                                       "korrektur_alte_kurse": round(math.exp(d), 4)})
    out["treffer"].sort(key=lambda x: (x["datum"], x["ticker"]))
    return out

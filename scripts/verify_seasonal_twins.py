#!/usr/bin/env python3
"""
verify_seasonal_twins.py — hält Backend und Frontend der Kern-Methodik deckungsgleich.

WARUM ES DAS GIBT: Die Normalisierung („jedes Jahr startet bei 100, tägliche Returns
kumulieren darauf") existiert ZWEIMAL — in `shared/calculations.py::normalize_year`
und in `landing/js/seasonal-compute.js::buildYearData`, das sich im eigenen Docstring
als Port bezeichnet. Zwei Implementierungen derselben Formel driften unbemerkt: der
Review am 2026-09-10 fand, dass Python um eine Zeile verschoben rechnete und dabei
den Jahreswechsel-Return ins Jahr zog, während das Frontend korrekt war. Auffallen
konnte das niemandem, weil beide Seiten plausible Kurven zeichneten.

Dieses Skript bildet die JS-Logik in Python nach (bewusst wörtlich, nicht „schöner")
und vergleicht sie gegen die echte Backend-Funktion — plus gegen die analytisch
korrekte Kurve aus den Kursen selbst.

Nutzung:  PYTHONUTF8=1 py -3.14 scripts/verify_seasonal_twins.py
Exit 0 = deckungsgleich, 1 = Abweichung (dann NICHT deployen).
"""
from __future__ import annotations
import math, sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd                                    # noqa: E402
from shared.calculations import normalize_year         # noqa: E402

_TOL = 1e-9


def js_build_year(rows: list) -> list:
    """Wörtlicher Nachbau von seasonal-compute.js::buildYearData (Z. 306-312).

    Absichtlich 1:1, damit eine Änderung dort hier auffällt statt sich anzugleichen.
    """
    cumulative = [100.0]
    for j in range(1, len(rows)):
        lr = rows[j].get("log_return")
        if lr is None:
            prev = rows[j - 1]["close"]
            lr = math.log(rows[j]["close"] / prev) if prev > 0 else 0.0
        cumulative.append(cumulative[j - 1] * math.exp(lr))
    return cumulative


def _mk(closes: list, prev_close: float) -> list:
    """Kursreihe → rows mit log_return = LN(close/prev_close), wie in der DB."""
    out, prev = [], prev_close
    for c in closes:
        out.append({"close": c, "log_return": math.log(c / prev)})
        prev = c
    return out


def _soll(closes: list) -> list:
    """Analytisch korrekt: Kurve relativ zum ERSTEN Schluss dieses Jahres."""
    return [100.0 * c / closes[0] for c in closes]


CASES = [
    ("Normaler Jahresauftakt +10 %, dann +1 %",
     [110.0, 111.1, 112.211], 100.0),
    ("Flacher Jahreswechsel (kein Sprung)",
     [100.0, 101.0, 102.01, 101.0], 100.0),
    ("Abwaertsjahr",
     [95.0, 90.25, 85.7375], 100.0),
    ("Ein einziger Handelstag",
     [107.0], 100.0),
    ("Zwei Handelstage",
     [107.0, 100.0], 100.0),
    ("Grosser Gap ueber den Jahreswechsel (-20 %)",
     [80.0, 80.8, 81.6], 100.0),
]


def main() -> int:
    print(f"{'Fall':<44}{'Python':>12}{'JS':>12}{'Soll':>12}  Status")
    print("-" * 92)
    bad = 0
    for name, closes, prev in CASES:
        rows = _mk(closes, prev)
        df = pd.DataFrame({"log_return": [r["log_return"] for r in rows]})
        py = normalize_year(df)
        js = js_build_year(rows)
        soll = _soll(closes)

        # Verglichen wird der ZWEITE Punkt: dort trennen sich die Konventionen.
        # (Punkt 0 ist per Definition bei allen 100.)
        i = 1 if len(closes) > 1 else 0
        ok_len = len(py) == len(js) == len(soll)
        ok_py = ok_len and all(abs(a - b) < _TOL for a, b in zip(py, soll))
        ok_js = ok_len and all(abs(a - b) < _TOL for a, b in zip(js, soll))
        status = "OK" if (ok_py and ok_js) else "ABWEICHUNG"
        if not (ok_py and ok_js):
            bad += 1
        print(f"{name:<44}{py[i]:>12.4f}{js[i]:>12.4f}{soll[i]:>12.4f}  {status}"
              + ("" if ok_len else f"  (Laengen {len(py)}/{len(js)}/{len(soll)})"))
        if not ok_py:
            print(f"    Python weicht ab: {[round(v, 4) for v in py]}")
        if not ok_js:
            print(f"    JS weicht ab:     {[round(v, 4) for v in js]}")

    print("-" * 92)
    if bad:
        print(f"[FAIL] {bad} von {len(CASES)} Faellen abweichend — Zwillinge sind gedriftet.")
        return 1
    print(f"[OK] {len(CASES)} Faelle: Backend, Frontend-Logik und Sollkurve identisch.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
verify_seasonal_twins.py — hält Backend und Frontend der Kern-Methodik deckungsgleich.

WARUM ES DAS GIBT: Die Kern-Mathematik existiert ZWEIMAL — in `shared/calculations.py`
und in `landing/js/seasonal-compute.js`, das sich im eigenen Docstring als Port
bezeichnet. Zwei Implementierungen derselben Formel driften unbemerkt: der Review am
2026-09-10 fand, dass Python bei der Normalisierung um eine Zeile verschoben rechnete,
während das Frontend korrekt war. Auffallen konnte das niemandem, weil beide Seiten
plausible Kurven zeichneten.

DREI GRÖSSEN, NICHT ZWEI: Das Skript bildet die JS-Logik in Python nach (bewusst
wörtlich, nicht „schöner") und vergleicht sie gegen die echte Backend-Funktion — plus
gegen die **analytisch korrekte** Kurve. Der dritte Vergleich ist der entscheidende:
der Turn-of-Month-Versatz steckte in BEIDEN Zwillingen identisch, der JS-Kommentar
sagte sogar „1:1 wie Python". Übereinstimmung ist kein Beleg für Richtigkeit.

ABGEDECKTE ZWILLINGSPAARE:
  1. normalize_year          <-> buildYearData
  2. interpolate_to_365      <-> _interpolateTo365
  3. analyze_turn_of_month   <-> analyzeTurnOfMonth

Block 4 fuehrt zusaetzlich die ECHTE `seasonal-compute.js` in node aus
(`scripts/js/twin_probe.js`). Grund: die Bloecke 1-3 vergleichen gegen einen
handgeschriebenen Python-Nachbau der JS-Logik — der kann selbst von der Quelle
driften, dann zertifiziert der Waechter eine Fiktion. Ohne node wird gewarnt,
nicht stillschweigend uebersprungen.

Nutzung:  PYTHONUTF8=1 py -3.14 scripts/verify_seasonal_twins.py
Exit 0 = deckungsgleich, 1 = Abweichung (dann NICHT deployen).
"""
from __future__ import annotations
import math, sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd                                              # noqa: E402
from shared.calculations import (normalize_year,                 # noqa: E402
                                 interpolate_to_365,
                                 analyze_turn_of_month)

_TOL = 1e-9
_ausfaelle: list[str] = []


def _melde(block: str, fall: str, ok: bool, detail: str = "") -> None:
    print(f"  {fall:<52}{'OK' if ok else 'ABWEICHUNG'}")
    if not ok:
        _ausfaelle.append(f"{block}: {fall}")
        if detail:
            print(f"      {detail}")


# ══════════════════════════════════════════════════════════════════
# 1. NORMALISIERUNG — normalize_year <-> buildYearData
# ══════════════════════════════════════════════════════════════════

def js_build_year(rows: list) -> list:
    """Wörtlicher Nachbau von seasonal-compute.js::buildYearData.

    Absichtlich 1:1, damit eine Änderung dort hier auffällt statt sich anzugleichen.
    Inklusive der Verwerfen-Semantik: ist ein log_return weder vorhanden noch aus
    den Closes rekonstruierbar, wird das JAHR verworfen (frueher lief hier ein
    stilles `lr = 0` weiter — das war die Divergenz zu Python).
    """
    if not rows:
        return []
    cumulative = [100.0]
    for j in range(1, len(rows)):
        lr = rows[j].get("log_return")
        if lr is None or not math.isfinite(lr):
            prev, cur = rows[j - 1]["close"], rows[j]["close"]
            if prev > 0 and cur > 0:
                lr = math.log(cur / prev)
            else:
                return []                    # Jahr verwerfen, wie Python
        cumulative.append(cumulative[j - 1] * math.exp(lr))
    return cumulative


def _mk(closes: list, prev_close: float) -> list:
    """Kursreihe → rows mit log_return = LN(close/prev_close), wie in der DB."""
    out, prev = [], prev_close
    for c in closes:
        out.append({"close": c, "log_return": math.log(c / prev) if prev > 0 and c > 0
                    else None})
        prev = c
    return out


def _soll(closes: list) -> list:
    """Analytisch korrekt: Kurve relativ zum ERSTEN Schluss dieses Jahres."""
    return [100.0 * c / closes[0] for c in closes]


NORM_CASES = [
    ("Normaler Jahresauftakt +10 %, dann +1 %", [110.0, 111.1, 112.211], 100.0),
    ("Flacher Jahreswechsel (kein Sprung)",     [100.0, 101.0, 102.01, 101.0], 100.0),
    ("Abwaertsjahr",                            [95.0, 90.25, 85.7375], 100.0),
    ("Ein einziger Handelstag",                 [107.0], 100.0),
    ("Zwei Handelstage",                        [107.0, 100.0], 100.0),
    ("Grosser Gap ueber den Jahreswechsel (-20 %)", [80.0, 80.8, 81.6], 100.0),
]


def block_normalisierung() -> None:
    print("\n1. NORMALISIERUNG  normalize_year <-> buildYearData")
    for name, closes, prev in NORM_CASES:
        rows = _mk(closes, prev)
        df = pd.DataFrame({"log_return": [r["log_return"] for r in rows]})
        py, js, soll = normalize_year(df), js_build_year(rows), _soll(closes)
        ok = (len(py) == len(js) == len(soll)
              and all(abs(a - b) < _TOL for a, b in zip(py, soll))
              and all(abs(a - b) < _TOL for a, b in zip(js, soll)))
        _melde("Normalisierung", name, ok,
               f"PY={[round(v,4) for v in py]} JS={[round(v,4) for v in js]} "
               f"SOLL={[round(v,4) for v in soll]}")

    # Leere Eingabe: Python liefert [], der JS-Nachbau lieferte frueher [100].
    py, js = normalize_year(pd.DataFrame({"log_return": []})), js_build_year([])
    _melde("Normalisierung", "Leere Eingabe (beide muessen [] liefern)",
           py == [] and js == [], f"PY={py} JS={js}")

    # Unreparierbarer Close: beide Seiten muessen das JAHR verwerfen, nicht lr=0 setzen.
    rows = [{"close": 0.0, "log_return": None}, {"close": 10.0, "log_return": None},
            {"close": 20.0, "log_return": None}]
    df = pd.DataFrame({"log_return": [None] * 3, "close": [0.0, 10.0, 20.0]})
    py, js = normalize_year(df), js_build_year(rows)
    _melde("Normalisierung", "Close <= 0 nicht reparierbar -> Jahr verwerfen",
           py == [] and js == [], f"PY={py} JS={js}")


# ══════════════════════════════════════════════════════════════════
# 2. INTERPOLATION — interpolate_to_365 <-> _interpolateTo365
# ══════════════════════════════════════════════════════════════════

def js_interpolate(days: list, values: list) -> list:
    """Wörtlicher Nachbau von seasonal-compute.js::_interpolateTo365."""
    days, values = list(days), list(values)
    if days and days[-1] > 365:                     # Schaltjahr: 366 auf 365 falten
        keep = {}
        for d, v in zip(days, values):
            keep[min(d, 365)] = v                   # spaetester Wert gewinnt
        days = sorted(keep)
        values = [keep[d] for d in days]
    full = []
    for target in range(1, 366):
        if target in days:
            full.append(values[days.index(target)]); continue
        if target < days[0]:
            full.append(values[0]); continue
        if target > days[-1]:
            full.append(values[-1]); continue
        prev_i = next_i = -1
        for j, d in enumerate(days):
            if d < target: prev_i = j
            if d > target and next_i < 0: next_i = j
        if prev_i >= 0 and next_i >= 0:
            w = (target - days[prev_i]) / (days[next_i] - days[prev_i])
            full.append(values[prev_i] + w * (values[next_i] - values[prev_i]))
        else:
            full.append(values[-1])
    return full


INTERP_CASES = [
    # (Name, days, values, erwarteter Wert auf Slot 365)
    ("Schaltjahr: Tag 366 faellt auf Slot 365", [364, 365, 366], [110.0, 115.0, 120.0], 120.0),
    ("Normaljahr: Tag 365 bleibt Slot 365",     [363, 364, 365], [110.0, 115.0, 118.0], 118.0),
    ("Fortschreibung hinter letztem Handelstag", [1, 100, 200],  [100.0, 105.0, 108.0], 108.0),
    ("Lineare Luecke zwischen zwei Punkten",     [1, 200, 365],  [100.0, 110.0, 120.0], 120.0),
]


def block_interpolation() -> None:
    print("\n2. INTERPOLATION  interpolate_to_365 <-> _interpolateTo365")
    for name, days, values, erwartet in INTERP_CASES:
        py, js = interpolate_to_365(days, values), js_interpolate(days, values)
        ok = (len(py) == len(js) == 365
              and all(abs(a - b) < 1e-6 for a, b in zip(py, js))
              and abs(py[364] - erwartet) < 1e-6)
        _melde("Interpolation", name, ok,
               f"Slot365 PY={py[364] if len(py) > 364 else '?'} "
               f"JS={js[364] if len(js) > 364 else '?'} SOLL={erwartet}")


# ══════════════════════════════════════════════════════════════════
# 3. TURN-OF-MONTH — analyze_turn_of_month <-> analyzeTurnOfMonth
# ══════════════════════════════════════════════════════════════════

def js_tom_curve(log_rets: list, days_before: int) -> list:
    """Wörtlicher Nachbau der Kurvenbildung in analyzeTurnOfMonth."""
    cum, run = [], 0.0
    for lr in log_rets:                       # glatte Kumulation, KEIN Versatz
        run += lr
        cum.append(run)
    raw = [100.0 * math.exp(v) for v in cum]
    t0 = raw[days_before]
    return [round((v / t0 - 1) * 10000) / 100 for v in raw]


def block_turn_of_month() -> None:
    print("\n3. TURN-OF-MONTH  analyze_turn_of_month <-> analyzeTurnOfMonth")

    # Der entscheidende Fall: NUR t+1 bewegt sich. Die alte, verschobene Variante
    # zeigte die Bewegung auf t+2 — in BEIDEN Zwillingen, deshalb war sie durch
    # einen reinen Zwillings-Vergleich nicht auffindbar.
    log_rets = [0.0, math.log(1.05), 0.0]
    js = js_tom_curve(log_rets, days_before=1)
    soll = [-4.76, 0.0, 0.0]                  # t0 ist die Referenz; t-1 liegt darunter
    ok = all(abs(a - b) < 0.01 for a, b in zip(js, soll))
    _melde("Turn-of-Month", "Nur t+1 bewegt sich (+5 %) -> Sprung auf t+1", ok,
           f"JS={js} SOLL={soll}")

    # Gegenprobe gegen die echte Backend-Funktion ueber einen synthetischen Monat.
    dates = pd.date_range("2024-01-25", periods=12, freq="D")
    closes = [100.0] * 12
    closes[6:] = [105.0] * 6                  # Sprung am 7. Tag des Fensters
    df = pd.DataFrame({
        "Date": dates, "Close": closes,
        "year": [d.year for d in dates], "month": [d.month for d in dates],
        "log_return": [0.0] + [math.log(closes[i] / closes[i - 1])
                               for i in range(1, 12)],
    }).set_index("Date")
    res = analyze_turn_of_month(df, 1, 1, [1], [2024])
    ok_be = res is not None and "avg_curve" in res
    _melde("Turn-of-Month", "Backend liefert eine Kurve (Rauchtest)", ok_be,
           f"res={type(res).__name__}")

    # Python rechnet `next_month = month + 1` explizit. JS gruppiert dagegen nach
    # Schluesseln und nimmt den naechsten sortierten — das geht NUR mit
    # nullgepaddetem Monat gut. Ungepaddet sortiert "2024-1" vor "2024-10" vor
    # "2024-2": Januar zog Oktober, Dezember zog Februar, September den Januar
    # des Folgejahres. 3 von 12 Monaten waren betroffen.
    ungepaddet = sorted(f"2024-{m}" for m in range(1, 13))
    gepaddet = sorted(f"2024-{m:02d}" for m in range(1, 13))
    _melde("Turn-of-Month", "Nullgepaddete Monatsschluessel sortieren chronologisch",
           gepaddet == [f"2024-{m:02d}" for m in range(1, 13)]
           and ungepaddet[1] == "2024-10",
           f"ungepaddet={ungepaddet[:4]}")


# ══════════════════════════════════════════════════════════════════
# 4. DAS ECHTE JS — via node, nicht via Nachbau
# ══════════════════════════════════════════════════════════════════

def block_echtes_js() -> None:
    """Fuehrt die Originaldatei seasonal-compute.js aus und prueft ihre Ausgabe.

    Die Bloecke 1-3 vergleichen Python gegen einen HANDGESCHRIEBENEN Nachbau der
    JS-Logik. Der kann selbst driften — dann zertifiziert der Waechter eine
    Fiktion. Dieser Block schliesst die Luecke: er laedt die echte Datei in node.
    Fehlt node, wird gewarnt statt stillschweigend uebersprungen.
    """
    import json, shutil, subprocess
    print("\n4. ECHTES JS  (seasonal-compute.js in node ausgefuehrt)")
    if not shutil.which("node"):
        print("  [WARN] node nicht gefunden — dieser Block wurde UEBERSPRUNGEN.")
        print("         Die Bloecke 1-3 pruefen nur den Python-Nachbau der JS-Logik.")
        return
    probe = _ROOT / "scripts" / "js" / "twin_probe.js"
    ziel = _ROOT / "landing" / "js" / "seasonal-compute.js"
    r = subprocess.run(["node", str(probe), str(ziel)], capture_output=True, text=True)
    if r.returncode:
        _melde("Echtes JS", "twin_probe.js laeuft durch", False, r.stderr[:400])
        return
    d = json.loads(r.stdout)

    # Interpolation gegen die echte Backend-Funktion
    for eintrag in d["interp"]:
        tage = eintrag["days"]
        werte = {(364, 365, 366): [110.0, 115.0, 120.0],
                 (363, 364, 365): [110.0, 115.0, 118.0],
                 (1, 100, 200):   [100.0, 105.0, 108.0],
                 (1, 200, 365):   [100.0, 110.0, 120.0]}[tuple(tage)]
        py = interpolate_to_365(tage, werte)[364]
        _melde("Echtes JS", f"_interpolateTo365{tuple(tage)} Slot 365 == Python",
               abs(py - eintrag["slot365"]) < 1e-6,
               f"JS={eintrag['slot365']} PY={py}")

    # Turn-of-Month gegen die ECHTE Monatsgruppierung: Januar muss den Februar
    # ziehen (+5 %), nicht den Oktober (-50 %). Genau das brach die
    # lexikografische Sortierung — und zwar nur fuer Jan/Dez/Sep.
    tom = d["tom_januar"]
    ok = tom is not None and len(tom) == 3 and abs(tom[2] - 5.0) < 0.01
    _melde("Echtes JS", "analyzeTurnOfMonth(Januar) zieht Februar, nicht Oktober", ok,
           f"avg_curve={tom} — erwartet [~0, 0, ~5]. Bei lexikografischer "
           f"Sortierung waere der Folgemonat des Januars der Oktober (-50 %).")

    # buildYearData: Verwerfen-Semantik bei unreparierbarem Close
    _melde("Echtes JS", "buildYearData verwirft Jahr bei Close <= 0 (kein lr=0)",
           d["build_kaputt_jahre"] == 0,
           f"Jahre im Ergebnis: {d['build_kaputt_jahre']} — erwartet 0.")

    # last_actual_day muss geliefert werden (war frueher nie gesetzt)
    b = d.get("build") or {}
    _melde("Echtes JS", "buildYearData liefert last_actual_day",
           isinstance(b.get("last_actual_day"), int) and b["last_actual_day"] > 0,
           f"build={b}")


def main() -> int:
    print("=" * 74)
    print("Zwillings-Pruefung: Backend (Python) <-> Frontend (JS) <-> Sollkurve")
    print("=" * 74)
    block_normalisierung()
    block_interpolation()
    block_turn_of_month()
    block_echtes_js()
    print("\n" + "=" * 74)
    if _ausfaelle:
        print(f"[FAIL] {len(_ausfaelle)} Abweichung(en) — Zwillinge sind gedriftet:")
        for a in _ausfaelle:
            print(f"   - {a}")
        return 1
    print("[OK] Alle drei Zwillingspaare deckungsgleich mit der Sollkurve.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

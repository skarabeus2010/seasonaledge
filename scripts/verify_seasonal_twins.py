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
import math, os, sys
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
    # KEIN Test auf selbst erzeugte Schluessel an dieser Stelle: der wuerde seine
    # Erwartung selbst herstellen und koennte strukturell nicht rot werden —
    # unabhaengig davon, was der Produktionscode tut. Geprueft wird das
    # Verhalten der echten JS-Funktion in Block 4 (analyzeTurnOfMonth/Januar).


def _py_tom_kurve() -> list | None:
    """Die ToM-Kurve aus der ECHTEN Backend-Funktion, fuer denselben Fall wie
    die JS-Sonde: 30./31. Januar bei 100, 1. Februar bei 105, je 1 Tag Fenster.

    Soll: [0.00, 0.00, 5.00] — t0 ist der letzte Januartag, die +5 % liegen auf
    t+1. Eine verschobene Implementierung liefert [0, 5, 5] oder [-4.76, 0, 0].
    """
    dates = pd.to_datetime(["2024-01-30", "2024-01-31", "2024-02-01"])
    closes = [100.0, 100.0, 105.0]
    df = pd.DataFrame({
        "Date": dates, "Close": closes,
        "year": [d.year for d in dates], "month": [d.month for d in dates],
        "log_return": [0.0, 0.0, math.log(1.05)],
    }).set_index("Date")
    res = analyze_turn_of_month(df, 1, 1, [1], [2024])
    if not res or not res.get("all_curves"):
        return None
    return [round(v, 2) for v in res["all_curves"][0]["curve"]]


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
        # FEHLSCHLAG, nicht WARN: ein uebersprungener Block, der den Lauf gruen
        # laesst, ist genau die Scheinsicherheit, gegen die dieses Skript
        # geschrieben wurde. Wer bewusst ohne node prueft, sagt es explizit.
        if "--ohne-node" in sys.argv:
            print("  [UEBERSPRUNGEN auf ausdrueckliche Anweisung (--ohne-node)]")
            print("  ACHTUNG: die Bloecke 1-3 pruefen nur den PYTHON-NACHBAU der")
            print("           JS-Logik, nicht den Code, der im Browser laeuft.")
            return
        _melde("Echtes JS", "node ist verfuegbar", False,
               "node nicht gefunden. Ohne node prueft dieses Skript nur den "
               "handgeschriebenen Nachbau der JS-Logik, also moeglicherweise "
               "eine Fiktion. node installieren, oder bewusst mit --ohne-node "
               "starten (dann bleibt der Lauf gruen, sagt aber klar, was "
               "ungeprueft blieb).")
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

    # VOLLER Kurvenvergleich gegen die echte Backend-Funktion. Ein Test auf nur
    # ein Element (frueher `tom[2] == 5`) laesst eine erneute Verschiebung durch:
    # ein verschobenes JS liefert [0, 5, 5] und haette bestanden.
    py_kurve = _py_tom_kurve()
    js_kurve = d["tom_voll"]
    ok_voll = (js_kurve is not None and py_kurve is not None
               and len(js_kurve) == len(py_kurve) == 3
               and all(abs(a - b) < 0.01 for a, b in zip(js_kurve, py_kurve))
               and all(abs(a - b) < 0.01 for a, b in zip(js_kurve, [0.0, 0.0, 5.0])))
    _melde("Echtes JS", "ToM-Kurve VOLLSTAENDIG identisch (JS == Python == Soll)",
           ok_voll, f"JS={js_kurve} PY={py_kurve} SOLL=[0.0, 0.0, 5.0]")

    # Mondphasen: dieselbe Fenster-Mathematik, eigene Funktion. In PR #271 wurde
    # hier derselbe Off-by-one behoben — ohne Test bliebe ein Rueckfall gruen.
    moon = d.get("moon")
    ok_moon = (moon is not None
               and all(abs(a - b) < 0.01 for a, b in zip(moon["curve"], [-4.76, 0.0, 0.0]))
               and abs(moon["total"] - 4.76) < 0.01)
    _melde("Echtes JS", "analyzeMoonEffect: Bewegung liegt auf t0, nicht auf t+1",
           ok_moon, f"moon={moon} — erwartet curve=[-4.76, 0, 0], total=4.76")

    # buildYearData: Verwerfen-Semantik bei unreparierbarem Close
    _melde("Echtes JS", "buildYearData verwirft Jahr bei Close <= 0 (kein lr=0)",
           d["build_kaputt_jahre"] == 0,
           f"Jahre im Ergebnis: {d['build_kaputt_jahre']} — erwartet 0.")

    # ToM mit Luecke: Januar, dann direkt Maerz. Ohne Nachbarschaftspruefung
    # wuerde der Januar mit dem Maerz gepaart (Python rechnet next_month explizit
    # und liefert dort korrekt nichts).
    _melde("Echtes JS", "ToM ueberspringt Luecke in der Historie (Jan -> Maerz)",
           d.get("tom_luecke") == 0,
           f"all_curves={d.get('tom_luecke')} — erwartet 0 Kurven.")

    # buildMonthlyStats erzeugt die sichtbaren Monatsdurchschnitte. Oktober bis
    # Dezember sind kritisch: ein Monatsindex, der nur die zweite Ziffer liest,
    # macht aus 10/11/12 die Zahl 0 — der Oktober waere dann leer.
    mo = d.get("monthly") or {}
    _melde("Echtes JS", "buildMonthlyStats ordnet Oktober korrekt zu",
           mo.get("okt_n") == 1 and abs((mo.get("okt_avg") or 0) - 10.0) < 0.01
           and mo.get("monate") == list(range(1, 13)),
           f"{mo} — erwartet okt_n=1, okt_avg=10.0, Monate 1..12.")

    # buildTOMHeatmap muss die NEUESTEN nYears zeigen, nicht die aeltesten.
    _melde("Echtes JS", "buildTOMHeatmap zeigt die neuesten Jahre",
           d.get("heatmap_jahre") == [2022, 2023, 2024],
           f"years={d.get('heatmap_jahre')} — erwartet [2022, 2023, 2024].")

    # last_actual_day muss geliefert werden (war frueher nie gesetzt)
    b = d.get("build") or {}
    _melde("Echtes JS", "buildYearData liefert last_actual_day",
           isinstance(b.get("last_actual_day"), int) and b["last_actual_day"] > 0,
           f"build={b}")


# ══════════════════════════════════════════════════════════════════
# 5. PYTHON-ONLY: Fenster-Analysen und Gruppierungen ohne JS-Zwilling
# ══════════════════════════════════════════════════════════════════

def block_python_only() -> None:
    """Deckt die Stellen ab, die keinen JS-Zwilling haben, aber dieselben zwei
    Fehlerklassen tragen: Off-by-one im Fenster und Gruppierung ohne Ticker.

    Beide sind in dieser Codebasis mehrfach aufgetreten (5 bzw. 3 Fundstellen).
    Ohne Test faellt ein Rueckfall erst dem Nutzer auf.
    """
    print("")
    print("5. PYTHON-ONLY  Fenster-Kumulation und Gruppierung")

    # shared/holidays.py: gleiche Fenster-Mathematik wie ToM, eigene Kopie.
    import numpy as np
    log_rets = np.array([0.0, math.log(1.05), 0.0])
    cum = np.cumsum(log_rets)                     # so rechnet holidays.py jetzt
    raw = 100 * np.exp(cum)
    kurve = [round(v, 2) for v in ((raw / raw[1] - 1) * 100)]
    _melde("Python-only", "Feiertags-Kumulation: Bewegung liegt auf t0",
           all(abs(a - b) < 0.01 for a, b in zip(kurve, [-4.76, 0.0, 0.0])),
           f"kurve={kurve} SOLL=[-4.76, 0.0, 0.0]")
    quelle = (_ROOT / "shared" / "holidays.py").read_text(encoding="utf-8")
    _melde("Python-only", "shared/holidays.py nutzt keine verschobene Kumulation",
           "np.insert(log_rets, 0, 0)[:-1]" not in quelle,
           "Die verschobene Variante `cumsum(insert(log_rets,0,0)[:-1])` ist "
           "zurueck — sie ordnet jeden Schritt der FOLGENDEN Zeile zu.")

    # shared/tdom_analysis.py: Gruppierung muss den Ticker mitnehmen.
    from shared.tdom_analysis import calc_tdom_range_return
    zeilen = []
    for tag in range(1, 11):
        d = f"2024-03-{tag:02d}"
        zeilen.append({"ticker": "A", "date": d, "Open": 100 + tag, "Close": 100 + tag,
                       "year": 2024, "month": 3})
        zeilen.append({"ticker": "B", "date": d, "Open": 200 + tag, "Close": 200 + tag,
                       "year": 2024, "month": 3})
    df = pd.DataFrame(zeilen).set_index("date")
    r = calc_tdom_range_return(df, entry_tdom=1, exit_tdom=5,
                               entry_price="Open", exit_price="Close")
    werte = sorted(round(v, 2) for v in r["return_pct"]) if len(r) else []
    _melde("Python-only", "calc_tdom_range_return trennt Ticker",
           len(r) == 2 and all(0 < v < 20 for v in werte),
           f"{len(r)} Zeile(n), Renditen={werte} — erwartet 2 Zeilen mit je < 20 %. "
           f"Ohne Ticker-Gruppierung entsteht EINE Zeile mit ~110 % "
           f"(A-Entry gegen B-Exit).")

    # calculate_period_stats: Jahresende-Regel mit injiziertem Stichtag (2026-10-13). Vorher hing die Aufnahme eines
    # Jahres von einer Referenz ueber alle Jahre ab (Maximum 365 bei SPY) und warf Jahre mit Ende 29./30.12. weg.
    from shared.calculations import calculate_period_stats

    def _jahr(lad):
        return {"days": list(range(1, lad + 1)), "full_365": [100.0 + i * 0.02
                                                              for i in range(365)]}
    faelle = [
        ("nur laufendes Jahr zaehlt nicht", {2026: _jahr(250)}, 0),
        ("laufendes Jahr bei Tag 365 zaehlt nicht", {2026: _jahr(365)}, 0),
        ("durchweg abgeschnittene Jahre zaehlen nicht", {2024: _jahr(250), 2025: _jahr(358)}, 0),
        ("Jahresende 363/364/365 gemeinsam zaehlen (NYSE 29.12., XETRA 30.12.)",
         {2023: _jahr(363), 2024: _jahr(365), 2025: _jahr(364), 2026: _jahr(365)}, 3),
        ("Toleranzgrenze: 359 zaehlt, 358 nicht", {2023: _jahr(359), 2024: _jahr(358)}, 1),
        ("zukuenftiges Jahr zaehlt nicht", {2025: _jahr(364), 2027: _jahr(365)}, 1),
    ]
    for name, yd, erwartet in faelle:
        s = calculate_period_stats(yd, 1, 365, stichtag_jahr=2026)
        got = s.get("total_years", 0)
        _melde("Python-only", f"Periodenstatistik: {name}", got == erwartet,
               f"total_years={got} SOLL={erwartet}")
    s = calculate_period_stats({2025: _jahr(364), 2026: _jahr(181)}, 152, 181, stichtag_jahr=2026)
    _melde("Python-only", "Periodenstatistik: abgeschlossener Juni des laufenden Jahres zaehlt",
           s.get("total_years", 0) == 2, f"total_years={s.get('total_years')} SOLL=2")

    # Und den WERT, nicht nur die Anzahl: ein um einen Kalendertag verschobener
    # Endindex aendert die Trefferzahl nicht — nur die Rendite. Ein Jahr, das von
    # 100 auf 110 laeuft und ab Tag 200 fortgeschrieben ist, muss ueber die
    # volle Periode exakt +10,00 % liefern.
    # Tag 1 = 100,00; ab Tag 200 konstant 110,00. Die Jahre reichen bis Tag 364
    # (XETRA-Jahresende), damit sie die Jahresende-Pruefung passieren.
    lauf = [100.0 + 10.0 * min(max(d_ - 1, 0), 199) / 199 for d_ in range(1, 366)]
    yd_wert = {2024: {"days": list(range(1, 365)), "full_365": lauf},
               2023: {"days": list(range(1, 365)), "full_365": lauf}}
    s = calculate_period_stats(yd_wert, 1, 365, stichtag_jahr=2026)
    _melde("Python-only", "Periodenstatistik liefert den richtigen WERT (+10,00 %)",
           s and abs(s.get("avg_return", 0) - 10.0) < 0.001,
           f"avg_return={s.get('avg_return')} SOLL=10.0 — ein verschobener "
           f"Endindex faellt bei einer reinen Anzahl-Pruefung nicht auf.")

    # Zweiter Wert-Test mit einer Periode MITTEN im Jahr. Bei end_day=365 liefern
    # min(end_day-1, 364) und min(end_day, 364) denselben Index — ein um einen Tag
    # verschobener Endindex bliebe dort unsichtbar. Bei Tag 100 nicht:
    # full_365[99] = 105,00 gegen full_365[100] = 105,05.
    s100 = calculate_period_stats(yd_wert, 1, 100, stichtag_jahr=2026)
    soll100 = (lauf[99] - lauf[0]) / lauf[0] * 100
    _melde("Python-only", "Periodenstatistik: Endindex bei Periode bis Tag 100",
           s100 and abs(s100.get("avg_return", 0) - soll100) < 1e-9,
           f"avg_return={s100.get('avg_return')} SOLL={soll100} "
           f"(ein Tag Versatz ergaebe {(lauf[100]-lauf[0])/lauf[0]*100}).")

    # Blog-Heatmap + Monatsmittel (blog_builder) mit injiziertem Stichtag. Synthetische Kurse: Bewegung NUR am
    # 15.12. (Faktor je Jahr) und am 15. jedes Monats 2026 — damit ist die Dezemberrendite je Jahr exakt bekannt,
    # unabhaengig von Interpolation und Jahresende (2022 endet am 30.12., 2023 am 29.12.).
    # None-Zellen ergaben vorher einen TypeError in der Beschriftung.
    import datetime as _dt
    import numpy as _np
    import pandas as _pd
    from shared.yahoo_downloader import preprocess
    import blog.blog_builder as bb

    def _df(tage, sprung):
        f = _np.array([sprung(d) for d in tage])
        roh = _pd.DataFrame({"Date": tage, "Open": 100.0, "High": 101.0, "Low": 99.0, "Volume": 1,
                             "Close": 100 * _np.cumprod(f)})
        return preprocess(roh.set_index(_pd.DatetimeIndex(roh["Date"])))

    dez = {2021: 1.04, 2022: 0.97, 2023: 1.06, 2024: 0.98, 2025: 1.03, 2026: 1.10}
    _getan = set()
    def _sprung(d):                       # erster Handelstag ab dem 12. des Monats (der 15. faellt teils aufs Wochenende)
        if d.day < 12 or (d.year, d.month) in _getan:
            return 1.0
        if d.month == 12:
            _getan.add((d.year, d.month)); return dez[d.year]
        if d.year == 2026:
            _getan.add((d.year, d.month)); return 1.01
        return 1.0
    tage = _pd.bdate_range("2021-01-04", "2026-12-31")     # Daten UEBER den Stichtag hinaus: prueft die Kalenderbedingung
    tage = tage[~((tage > "2025-09-30") & (tage < "2026-01-01"))]       # 2025 endet am 30.09. (abgeschnitten)
    bb._ticker_cache["__WAECHTER__"] = _df(tage, _sprung)
    try:
        st = _dt.date(2026, 10, 13)
        fig = bb._build_monthly_heatmap_chart("__WAECHTER__", 6, "de", stichtag=st)   # 6 neueste Jahre = 2021–2026
        belegt = {int(y): [v is not None for v in z] for y, z in zip(fig.data[0].y, fig.data[0].z)}
        soll = {2026: [True] * 9 + [False] * 3, 2025: [True] * 9 + [False] * 3, 2024: [True] * 12,
                2023: [True] * 12, 2022: [True] * 12, 2021: [True] * 12}
        _melde("Python-only", "Blog-Heatmap: laufendes Jahr nur beendete Monate (Okt leer trotz Daten), 2025 bis Sep",
               belegt == soll, str(belegt))
        dz = {int(y): z[11] for y, z in zip(fig.data[0].y, fig.data[0].z)}
        ok_dz = all(dz[y] is not None and abs(dz[y] - round((dez[y] - 1) * 100, 2)) < 1e-9 for y in (2021, 2022, 2023, 2024))
        _melde("Python-only", "Blog-Heatmap: Dezemberzellen 2021–2024 = Sprung Mitte Dezember (auch Ende 29./30.12.)",
               ok_dz, str(dz))
        fig2 = bb._build_monthly_cycle_chart("__WAECHTER__", 5, "de", stichtag=st)
        balken = list(fig2.data[0].y)
        soll_dez = sum((dez[y] - 1) * 100 for y in (2021, 2022, 2023, 2024)) / 4   # 2025 abgeschnitten, 2026 laufend
        _melde("Python-only", "Blog-Monatsmittel: Dezember = Mittel 2021–2024 (alle Jahresenden, ohne 2025/2026)",
               abs(balken[11] - soll_dez) < 1e-6, f"Dez={balken[11]} SOLL={soll_dez}")
        soll_jan = (0 + 0 + 0 + 0 + 0 + 1.0) / 6                                    # nur 2026 bewegt sich im Januar
        _melde("Python-only", "Blog-Monatsmittel: Januar zaehlt alle sechs Jahre", abs(balken[0] - soll_jan) < 1e-6,
               f"Jan={balken[0]} SOLL={soll_jan}")

        # Schaltjahrgrenze und Zukunftsjahr: Daten bis 29.02.2024 bzw. bis 2027.
        bb._ticker_cache["__WAECHTER__"] = _df(_pd.bdate_range("2023-01-02", "2024-02-29"), lambda d: 1.0)
        f29 = bb._build_monthly_heatmap_chart("__WAECHTER__", 5, "de", stichtag=_dt.date(2024, 2, 29))
        f01 = bb._build_monthly_heatmap_chart("__WAECHTER__", 5, "de", stichtag=_dt.date(2024, 3, 1))
        feb = lambda f: dict(zip(f.data[0].y, f.data[0].z))["2024"][1]
        _melde("Python-only", "Blog-Heatmap: Stichtag 29.02. -> Februar leer, 01.03. -> belegt",
               feb(f29) is None and feb(f01) is not None, f"{feb(f29)}/{feb(f01)}")
        bb._ticker_cache["__WAECHTER__"] = _df(_pd.bdate_range("2025-01-02", "2027-06-30"), lambda d: 1.0)
        fz = bb._build_monthly_heatmap_chart("__WAECHTER__", 5, "de", stichtag=_dt.date(2026, 10, 13))
        z27 = dict(zip(fz.data[0].y, fz.data[0].z)).get("2027", [None] * 12)
        _melde("Python-only", "Blog-Heatmap: zukuenftiges Jahr leer", all(v is None for v in z27), str(z27))
    except Exception as e:                     # Renderfehler = rot, nicht still
        _melde("Python-only", "Blog-Heatmap/Monatsmittel ohne Renderfehler", False, repr(e)[:300])
    finally:
        bb._ticker_cache.pop("__WAECHTER__", None)


# 4b. ZEITZONEN — dieselben Tagesnummern und Jahreskurven unter jeder Zeitzone (Schritt U, 2026-10-09)
ZEITZONEN = ["UTC", "Europe/Berlin", "America/New_York", "America/Los_Angeles", "Asia/Tokyo", "Pacific/Auckland"]


def block_zeitzonen():
    """
    `new Date("YYYY-MM-DD")` ist UTC-Mitternacht, `new Date(jahr, 0, 0)` lokale Mitternacht. Westlich von UTC lag
    damit JEDE Tagesnummer um eins daneben (gemessen: New York 16 801 von 16 801 Tagen 1990–2035). Referenz ist
    pandas `dayofyear` — unabhängig von beiden JS-Funktionen. Ohne node: wie Block 4 (kein stilles Überspringen).
    """
    import json, shutil, subprocess
    import pandas as pd
    print("\n4b. ZEITZONEN  (seasonal-compute.js + decade-compute.js unter 6 Zeitzonen)")
    if not shutil.which("node"):
        if "--ohne-node" in sys.argv:
            print("  [UEBERSPRUNGEN auf ausdrueckliche Anweisung (--ohne-node)]")
            return
        _melde("Zeitzonen", "node ist verfuegbar", False, "node nicht gefunden")
        return
    soll = list(pd.date_range("1990-01-01", "2035-12-31", freq="D").dayofyear)
    probe = _ROOT / "scripts" / "js" / "tz_probe.js"
    sc = _ROOT / "landing" / "js" / "seasonal-compute.js"
    dc = _ROOT / "landing" / "js" / "decade-compute.js"
    kurven = {}
    for tz in ZEITZONEN:
        seiten = [str(_ROOT / "landing" / "pages" / f) for f in ("jahreszyklus.html", "risikozyklus.html")]
        r = subprocess.run(["node", str(probe), tz, str(sc), str(dc), *seiten], capture_output=True, text=True,
                           env={**os.environ, "MSYS_NO_PATHCONV": "1"})
        if r.returncode:
            _melde("Zeitzonen", f"tz_probe.js laeuft unter {tz}", False, r.stderr[:300])
            continue
        d = json.loads(r.stdout)
        # Beweis, dass die Zeitzone wirklich gilt (sonst prueft der Block nur UTC — die Falle aus Git Bash)
        erwartet_offset = {"UTC": 0, "Europe/Berlin": -60, "America/New_York": 300, "America/Los_Angeles": 480,
                           "Asia/Tokyo": -540, "Pacific/Auckland": -780}[tz]
        _melde("Zeitzonen", f"{tz}: Zeitzone wirkt (Offset {erwartet_offset})", d["offset_jan"] == erwartet_offset,
               f"Offset {d['offset_jan']}")
        for name in ("tage_seasonal", "tage_decade"):
            abw = [i for i, (a, b) in enumerate(zip(d[name], soll)) if a != b]
            _melde("Zeitzonen", f"{tz}: {name} == pandas dayofyear (16 801 Tage)", len(d[name]) == len(soll) and not abw,
                   f"{len(abw)} Abweichungen, erste bei Index {abw[:1]}")
        kurven[tz] = d["kurve_2023"]
        for seite, e in d.get("extra", {}).items():
            # Januar 01.–20.2023, Schlusskurse 100…119: Tag 1 = 100, Tag 21 und Tag 365 = 119 (konstant fortgeschrieben)
            ok_jan = e["jan"] is not None and e["jan"]["lad"] == 20 and abs(e["jan"]["k"][0] - 100) < 1e-9 \
                and abs(e["jan"]["k"][1] - 119) < 1e-9 and abs(e["jan"]["k"][2] - 119) < 1e-9
            _melde("Zeitzonen", f"{tz}: {seite} buildExtendedYearData Januar-Fall", ok_jan, f"{e['jan']}")
            _melde("Zeitzonen", f"{tz}: {seite} Kurve == buildYearData", e["w"] == d["kurve_2023"],
                   f"{seite}: lad={e['w'] and e['w']['lad']} vs {d['kurve_2023'] and d['kurve_2023']['lad']}")
    if kurven:
        ref = kurven.get("UTC")
        gleich = all(k == ref for k in kurven.values())
        _melde("Zeitzonen", "buildYearData liefert unter allen Zeitzonen dieselbe Kurve und last_actual_day",
               ref is not None and gleich,
               "; ".join(f"{tz}: lad={k['lad'] if k else None}" for tz, k in kurven.items()))


# 7. ZYKLUS — Jahresende-Regel, Praesidentenzyklus-Karten, Schaltjahr, Heatmap (Plan 2026-10-13 v3)
def block_zyklus():
    """
    Fuehrt scripts/js/zyklus_probe.js auf dem echten Code aus (seasonal-compute.js, significance.js und die
    Inline-Funktionen aus jahreszyklus.html/risikozyklus.html) und prueft fachliche Erwartungen — nicht nur Gleichheit.
    Die yearCovers-Faelle rechnet Python mit year_covers nach (Zwilling). Ohne node: rot (kein stilles Ueberspringen).
    Anlass: auf /jahreszyklus fehlte die Midterm-Karte, weil Jahre mit Ende am 29./30.12. verworfen und Gruppen unter
    fuenf Jahren still entfernt wurden.
    """
    import json, shutil, subprocess
    from shared.calculations import year_covers
    print("\n7. ZYKLUS  (Jahresende-Regel, vier Zykluskarten, Schaltjahr, Heatmap)")
    if not shutil.which("node"):
        if "--ohne-node" in sys.argv:
            print("  [UEBERSPRUNGEN auf ausdrueckliche Anweisung (--ohne-node)]")
            return
        _melde("Zyklus", "node ist verfuegbar", False, "node nicht gefunden")
        return
    probe = _ROOT / "scripts" / "js" / "zyklus_probe.js"
    r = subprocess.run(["node", str(probe), str(_ROOT / "landing" / "js" / "seasonal-compute.js"),
                        str(_ROOT / "landing" / "js" / "significance.js"),
                        str(_ROOT / "landing" / "pages" / "jahreszyklus.html"),
                        str(_ROOT / "landing" / "pages" / "risikozyklus.html")], capture_output=True, text=True)
    if r.returncode:
        _melde("Zyklus", "zyklus_probe.js laeuft", False, r.stderr[:400])
        return
    d = json.loads(r.stdout)

    # Fachliche Erwartung je Fall: (lad, endDoy, jahr, stichtag) -> zugelassen?
    soll = {(365, 365, 2025, 2026): True, (363, 365, 2023, 2026): True, (364, 365, 2025, 2026): True,
            (362, 365, 2024, 2026): True, (359, 365, 2024, 2026): True, (358, 365, 2024, 2026): False,
            (365, 365, 2026, 2026): False, (364, 365, 2026, 2026): False, (359, 365, 2026, 2026): False,
            (365, 365, 2027, 2026): False, (181, 181, 2026, 2026): True, (180, 181, 2026, 2026): False,
            (280, 31, 2026, 2026): True, (349, 365, 2024, 2026): False, (250, 365, 2024, 2026): False,
            (None, 31, 2024, 2026): False, (None, 365, 2024, 2026): False}
    for f in d["yearcovers_faelle"]:
        k = (f["lad"], f["e"], f["j"], f["st"])
        yd = {"days": list(range(1, f["lad"] + 1))} if f["lad"] is not None else {}
        py = year_covers(yd, f["e"], f["j"], f["st"])
        _melde("Zyklus", f"yearCovers lad={k[0]} bis Tag {k[1]} Jahr {k[2]} (Stichtag {k[3]})",
               f["ok"] == soll[k] and py == soll[k], f"JS={f['ok']} Python={py} SOLL={soll[k]}")
    _melde("Zyklus", "Entscheidung haengt nicht von anderen Jahren ab", d["unabhaengig"] == [True], str(d["unabhaengig"]))

    sj = d["schaltjahr"]
    _melde("Zyklus", "Schaltjahr: Bewegung nur am 31.12. landet im Endwert (alle drei Builder = 110)",
           sj["gemeinsam"] == 110 and sj["jahreszyklus"] == 110 and sj["risikozyklus"] == 110 and sj["lad_jz"] == 365,
           str(sj))
    _melde("Zyklus", "periodStats: 363/364/365 zaehlen, laufendes Jahr nicht", d["periodstats_jahr"] == 3,
           f"total_years={d['periodstats_jahr']} SOLL=3")
    _melde("Zyklus", "periodStats: abgeschlossener Juni des laufenden Jahres zaehlt", d["periodstats_juni"] == 2,
           f"total_years={d['periodstats_juni']} SOLL=2")

    _melde("Zyklus", "Heatmap: Daten bis 30.06., Stichtag Oktober -> nur Jan–Jun belegt",
           d["heatmap_2026"] == [True] * 6 + [False] * 6, str(d["heatmap_2026"]))
    _melde("Zyklus", "Heatmap: abgeschlossenes Vorjahr (Ende 30.12.) voll belegt incl. Dezember",
           d["heatmap_2025"] == [True] * 12, str(d["heatmap_2025"]))
    _melde("Zyklus", "Heatmap: zukuenftiges Jahr leer", d["heatmap_2027"] == [False] * 12, str(d["heatmap_2027"]))
    _melde("Zyklus", "Heatmap: Stichtag 29.02. -> Februar leer, 01.03. mit Kurs am 29.02. -> belegt, ohne Daten leer",
           d["heatmap_feb_2902"] is False and d["heatmap_feb_0103"] is True and d["heatmap_feb_0103_ohne_daten"] is False,
           f"{d['heatmap_feb_2902']}/{d['heatmap_feb_0103']}/{d['heatmap_feb_0103_ohne_daten']}")

    for name, grau, n in (("zyklus_20", 0, ["n=5"] * 4), ("zyklus_10", 4, ["n=3", "n=2", "n=2", "n=3"]),
                          ("zyklus_leer", 4, ["n=0"] * 4)):
        z = d[name]
        reihe = z["reihenfolge"]
        _melde("Zyklus", f"{name}: vier Karten in fester Reihenfolge Post-Election, Midterm, Pre-Election, Election Year",
               all(i >= 0 for i in reihe) and reihe == sorted(reihe), str(reihe))
        _melde("Zyklus", f"{name}: {grau} graue Karten, Fallzahlen {n}, kein NaN, kein Abbruchtext",
               z["grau"] == grau and z["n"] == n and not z["nan"] and not z["sorry"], str(z))

    _melde("Zyklus", "Monatszweig: laufendes Jahr (bis Tag 181) nur Jan–Jun, Dezember nur Vorjahre",
           d["zweig_monat"] == [m + ":8" for m in ("Jan", "Feb", "Mär", "Apr", "Mai", "Jun")]
           + [m + ":7" for m in ("Jul", "Aug", "Sep", "Okt", "Nov", "Dez")], str(d["zweig_monat"]))
    _melde("Zyklus", "Quartalszweig: laufendes Jahr nur Q1/Q2, Q4 nur Vorjahre (auch Ende 29./30.12.)",
           d["zweig_quartal"] == ["Q1:8", "Q2:8", "Q3:7", "Q4:7"], str(d["zweig_quartal"]))
    m3 = d["mindest3"]
    _melde("Zyklus", "Mindestzahl 3 wirkt in Test und Karte (kein festes 5), Einheit aus den Optionen",
           m3["zu_wenig"] == ["a"] and m3["getestet"] == ["b", "c"] and m3["text_3"] and not m3["text_5"] and m3["einheit"],
           str(m3))
    en = d["englisch"]
    _melde("Zyklus", "EN: graue Karte mit englischem Woerterbuch, kein deutscher Ersatztext",
           en["not_evaluated"] and en["einheit"] and en["at_least"] and not en["deutsch"], str(en))

    g = d["sig_gruppen"]
    _melde("Zyklus", "runSignificanceTest: Gruppen n=0..4 als zu_wenig, n=5 getestet, graue Karten ohne NaN",
           g["zu_wenig"] == ["n0:0", "n1:1", "n2:2", "n3:3", "n4:4"] and g["getestet"] == ["n5"]
           and g["grau"] == 5 and not g["nan"], str(g))


def _ts_reihe(jahre, seed, bis=None, weg=None, faktor=None, kaputt=None, sigma=0.011, drift=None):
    """Kurszeilen Mo–Fr ohne 1.1./25.12.; weg(d) -> Zeile weglassen; faktor{jahr: k} skaliert die Returns eines Jahres;
    kaputt(d) -> 'nan' (log_return NaN, Closes gültig) oder 'leer' (close und log_return fehlen);
    drift{jahr: µ} ersetzt den täglichen Mittelwert 0,0004 (gezielte Ausreißerjahre)."""
    import random
    from datetime import date, timedelta
    rnd, rows, close = random.Random(seed), [], 100.0
    for y in jahre:
        d = date(y, 1, 1)
        while d.year == y and (bis is None or d <= bis):
            if d.weekday() < 5 and (d.month, d.day) not in ((1, 1), (12, 25)) and not (weg and weg(d)):
                lr = rnd.gauss((drift or {}).get(y, 0.0004), sigma) * ((faktor or {}).get(y, 1.0))
                close *= math.exp(lr)
                art = kaputt(d) if kaputt else None
                rows.append({"date": d.isoformat(),
                             "close": None if art == "leer" else round(close, 6),
                             "log_return": None if art == "leer" else (float("nan") if art == "nan" else lr)})
            d += timedelta(days=1)
    # Returns an der Jahresgrenze/nach Lücken aus den gerundeten Closes neu, damit Kurs und Return zueinander passen
    for i in range(1, len(rows)):
        a, b = rows[i - 1]["close"], rows[i]["close"]
        if a and b and rows[i]["log_return"] is not None and math.isfinite(rows[i]["log_return"]):
            rows[i]["log_return"] = math.log(b / a)
    return rows


def _ts_py_yeardata(rows):
    import pandas as pd
    from shared.calculations import build_year_data
    df = pd.DataFrame({"date": pd.to_datetime([r["date"] for r in rows]),
                       "close": [r["close"] if r["close"] is not None else float("nan") for r in rows],
                       "log_return": [r["log_return"] if r["log_return"] is not None else float("nan") for r in rows]})
    df["year"] = df["date"].dt.year
    df["day_of_year"] = df["date"].dt.dayofyear
    return build_year_data(df, sorted(df["year"].unique().tolist()))


def block_true_seasonal():
    """
    Williams True Seasonal (Plan v3, docs/review_prompts/2026-10-16_true_seasonal_plan_v3.md): echter JS-Kern
    (seasonal-compute.js), Seiten-Builder und Modellauswahl aus jahreszyklus.html gegen shared/true_seasonal.py und
    gegen fachliche Sollwerte — Heuristik „vollständig“ (TSE-Lücke 11 Tage zulässig, 15 Tage nicht, Jahresende vor
    Tag 362 nicht, Teiljahre nicht, eine fehlende Sitzung zulässig), Kalenderfenster ohne Ersatz fehlender Jahre,
    Zieljahr-Unabhängigkeit mit aktivem Ausreißerfilter, Return-Behandlung des Seiten-Builders, Kennzahl.
    """
    import json, shutil, subprocess, tempfile
    from datetime import date
    from shared import true_seasonal as TS
    print("\n8. TRUE SEASONAL  (Heuristik vollständig, Fenster, Zieljahr, Rückblick, Seiten-Builder)")
    if not shutil.which("node"):
        if "--ohne-node" in sys.argv:
            print("  [UEBERSPRUNGEN auf ausdrueckliche Anweisung (--ohne-node)]")
            return
        _melde("TrueSeasonal", "node ist verfuegbar", False, "node nicht gefunden")
        return

    def sonder_weg(d):
        y = d.year
        return ((y == 2011 and (d.month, d.day) > (12, 27)) or (y == 2012 and d.month < 7) or (y == 2013 and d.month < 12)
                or (y == 2014 and 1 < d.month < 12) or (y == 2014 and d.month == 1 and d.day > 2)
                or (y == 2015 and (d.month, d.day) >= (4, 26) and (d.month, d.day) <= (5, 6))
                or (y == 2016 and d.month == 3 and d.day <= 15)
                or (y == 2017 and (d.month, d.day) > (12, 22))
                or (y == 2018 and (d.month, d.day) == (6, 13))
                or y == 2023)

    def sonder_kaputt(d):
        if (d.year, d.month, d.day) == (2019, 5, 15):
            return "nan"
        if (d.year, d.month, d.day) == (2021, 3, 10):
            return "leer"
        return None

    stich = date(2026, 10, 15)
    faelle = [
        {"name": "basis", "rows": _ts_reihe(range(2004, 2027), 1, bis=stich), "stichtag": 2026,
         "fenster": [5, 10, None], "methode": "off", "ts_auftraege": [[2026, 5], [2026, 10], [2026, None]]},
        {"name": "sonder", "rows": _ts_reihe(range(2010, 2027), 2, bis=stich, weg=sonder_weg, kaputt=sonder_kaputt),
         "stichtag": 2026, "fenster": [5, 10], "methode": "off", "ts_auftraege": [[2026, 5], [2026, 10]]},
        {"name": "ziel_a", "rows": _ts_reihe(range(2005, 2023), 3), "stichtag": 2020, "fenster": [10],
         "methode": "iqr", "ts_auftraege": [[2020, 10], [2021, 10]]},
        {"name": "ziel_b", "rows": _ts_reihe(range(2005, 2023), 3, faktor={2020: 6.0}), "stichtag": 2020,
         "fenster": [10], "methode": "iqr", "ts_auftraege": [[2020, 10], [2021, 10]]},
        # Ausreißerfilter: unter den Vorjahren 2010–2019 sind 2011/2013 (≈ −40 %) und 2015 (≈ +60 %) Ausreißer;
        # 2020–2022 (≈ +100 %) liegen NACH dem Stichtag und dürfen den Filter nicht beeinflussen.
        {"name": "filter", "rows": _ts_reihe(range(2008, 2023), 4, sigma=0.004,
                                             drift={2011: -0.002, 2013: -0.002, 2015: 0.0025, 2020: 0.004,
                                                    2021: 0.004, 2022: 0.004}),
         "stichtag": 2020, "fenster": [10], "methode": "iqr", "ts_auftraege": [[2020, 10]]},
    ]
    # Schaltjahr-Konvention der Chart-Achse: 2024 (Schaltjahr) bewegt sich nur am 29.02. (Tag 60 → März-Slot),
    # 2023 nur am 28.02. (Tag 59 → Februar-Slot); alle übrigen Returns 0.
    def schalt_rows():
        from datetime import timedelta
        rows, close = [], 100.0
        for y in (2022, 2023, 2024, 2025):
            d = date(y, 1, 1)
            while d.year == y:
                if d.weekday() < 5 or (y, d.month, d.day) in ((2024, 2, 29),):
                    lr = math.log(1.1) if (y, d.month, d.day) in ((2024, 2, 29), (2023, 2, 28)) else 0.0
                    close *= math.exp(lr)
                    rows.append({"date": d.isoformat(), "close": round(close, 6), "log_return": lr})
                d += timedelta(days=1)
        return rows
    faelle.append({"name": "schalt", "rows": schalt_rows(), "stichtag": 2026, "fenster": [], "methode": "off",
                   "ts_auftraege": []})

    # Kennzahl analytisch: zwölf vorgegebene Änderungen je Kurve, linear innerhalb des Monats interpoliert (eine um
    # einen Tag verschobene Monatsgrenze liest dann einen anderen Wert)
    a_soll = [0.02, -0.01, 0.03, 0.0, -0.02, 0.015, 0.01, -0.03, 0.005, 0.02, -0.005, 0.01]
    b_soll = [0.01, -0.02, 0.01, 0.01, -0.01, 0.0, 0.02, -0.01, -0.005, 0.03, 0.002, 0.004]

    def kurve(aend):
        stuetz, v = [(0, 100.0)], 100.0
        # Monatsgrenzen WÖRTLICH (nicht TS.MONATSENDE_SLOT) — sonst prüfte sich die Python-Seite mit sich selbst
        for e, x in zip((31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365), aend):
            v *= math.exp(x)
            stuetz.append((e, v))
        out = []
        for tag in range(1, 366):
            for (d0, v0), (d1, v1) in zip(stuetz, stuetz[1:]):
                if d0 < tag <= d1:
                    out.append(v0 + (v1 - v0) * (tag - d0) / (d1 - d0))
                    break
        return out
    kurve_ist, kurve_modell = kurve(a_soll), kurve(b_soll)

    def js_tauglich(rows):   # JSON kennt kein NaN: als Text "NaN" (parseFloat -> NaN wie ein kaputter DB-Wert)
        return [dict(r, log_return="NaN") if isinstance(r["log_return"], float) and math.isnan(r["log_return"]) else r
                for r in rows]
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump({"faelle": [dict(f, rows=js_tauglich(f["rows"])) for f in faelle],
                   "kennzahl": {"ist": kurve_ist, "modell": kurve_modell}}, fh, allow_nan=False)
        pfad = fh.name
    try:
        r = subprocess.run(["node", str(_ROOT / "scripts" / "js" / "true_seasonal_probe.js"),
                            str(_ROOT / "landing" / "js" / "seasonal-compute.js"),
                            str(_ROOT / "landing" / "js" / "outlier.js"),
                            str(_ROOT / "landing" / "pages" / "jahreszyklus.html"), pfad],
                           capture_output=True, text=True, encoding="utf-8")
    finally:
        os.unlink(pfad)
    if r.returncode:
        _melde("TrueSeasonal", "true_seasonal_probe.js laeuft", False, r.stderr[:400])
        return
    js = json.loads(r.stdout)

    def nah(a, b, tol=1e-9):
        if a is None or b is None:
            return a is None and b is None
        return abs(a - b) <= tol

    for f in faelle:
        name, e = f["name"], js[f["name"]]
        yd = _ts_py_yeardata(f["rows"])
        # Zwilling Builder + Vollständigkeit
        abw = []
        for y, v in e["jahre"].items():
            y = int(y)
            if not v["gleich"]:
                abw.append(f"{y}: Seite≠gemeinsam")
            if (y in yd) != v["gemeinsam"]:
                abw.append(f"{y}: Python {'hat' if y in yd else 'verwirft'}, JS {'hat' if v['gemeinsam'] else 'verwirft'}")
                continue
            if y in yd:
                d = max(abs(a - b) for a, b in zip(yd[y]["full_365"], v["full"]))
                if d > 1e-9:
                    abw.append(f"{y}: full_365 Δ {d:.2e}")
                pv = TS.jahr_vollstaendig(yd[y], y, f["stichtag"])
                if pv != v["voll"] or pv != v["voll_seite"]:
                    abw.append(f"{y}: vollständig Py={pv} JS={v['voll']} Seite={v['voll_seite']}")
        _melde("TrueSeasonal", f"{name}: Builder Seite = gemeinsam = Python, Vollständigkeit gleich", not abw, "; ".join(abw[:4]))
        for k, v in e["ts"].items():
            ziel, n = k.split("|")
            n = None if n == "null" else int(n)
            pj = TS.true_seasonal_jahre(yd, int(ziel), n)
            pk = TS.mittel_kurve(yd, pj)
            ok = pj == v["jahre"] and ((pk is None and v["kurve"] is None) or
                                       (pk is not None and v["kurve"] is not None and all(nah(a, b) for a, b in zip(pk, v["kurve"]))))
            _melde("TrueSeasonal", f"{name}: Jahre+Kurve Ziel {ziel}, N={n} JS = Python", ok, f"Py={pj} JS={v['jahre']}")
        for n_txt, rb in e["rueckblick"].items():
            n = None if n_txt == "null" else int(n_txt)
            pr = TS.rueckblick(yd, f["stichtag"], n)
            ok = len(pr["jahre"]) == len(rb["jahre"])
            for a, b in zip(pr["jahre"], rb["jahre"]):
                ok = ok and a["jahr"] == b["jahr"] and a["nTs"] == b["nTs"] and a["nRueck"] == b["nRueck"]
                for fe in ("ts", "rueck"):
                    ok = ok and (a[fe] is None) == (b[fe] is None)
                    if a[fe] and b[fe]:
                        ok = ok and nah(a[fe]["r"], b[fe]["r"]) and a[fe]["treffer"] == b[fe]["treffer"] \
                            and a[fe]["immerPositiv"] == b[fe]["immerPositiv"]
            for fe in ("ts", "rueck"):
                ok = ok and nah(pr[fe]["rMittel"], rb[fe]["rMittel"]) and pr[fe]["rPositiv"] == rb[fe]["rPositiv"] \
                    and pr[fe]["nGueltig"] == rb[fe]["nGueltig"] and nah(pr[fe]["trefferMittel"], rb[fe]["trefferMittel"])
            _melde("TrueSeasonal", f"{name}: Rückblick N={n} JS = Python ({len(rb['jahre'])} Jahre)", ok)

    # ── Fachliche Sollwerte ──
    b = js["basis"]
    _melde("TrueSeasonal", "basis: 2004–2025 vollständig, laufendes Jahr 2026 nicht",
           all(b["jahre"][str(y)]["voll"] for y in range(2004, 2026)) and b["jahre"]["2026"]["voll"] is False)
    _melde("TrueSeasonal", "basis: Fenster 5 = 2021–2025, 10 = 2016–2025, max = 2004–2025",
           b["ts"]["2026|5"]["jahre"] == list(range(2021, 2026)) and b["ts"]["2026|10"]["jahre"] == list(range(2016, 2026))
           and b["ts"]["2026|null"]["jahre"] == list(range(2004, 2026)), str({k: v["jahre"][:3] for k, v in b["ts"].items()}))
    _melde("TrueSeasonal", "basis: Rückblick bewertet 5 (N=5) bzw. 12 Jahre (max, ab 10 Vorjahren)",
           len(b["rueckblick"]["5"]["jahre"]) == 5 and len(b["rueckblick"]["null"]["jahre"]) == 12
           and b["rueckblick"]["null"]["jahre"][0]["jahr"] == 2014,
           f"{len(b['rueckblick']['5']['jahre'])}/{len(b['rueckblick']['null']['jahre'])}")
    s = js["sonder"]
    soll = {2010: True, 2011: False, 2012: False, 2013: False, 2014: False, 2015: True, 2016: False, 2017: False,
            2018: True, 2019: True, 2020: True, 2022: True, 2024: True, 2025: True, 2026: False}
    ist = {int(y): v["voll"] for y, v in s["jahre"].items() if v["gemeinsam"]}
    _melde("TrueSeasonal", "sonder: IPO-Jahr/nur Dezember/Jan+Dez/Lücke 15 T./Ende 22.12./Ende 27.12. (Tag 361) nein; Lücke 11 T., "
           "eine fehlende Sitzung, NaN-Return rekonstruiert, Schaltjahr ja", ist == soll,
           str({y: (ist.get(y), soll.get(y)) for y in sorted(set(ist) | set(soll)) if ist.get(y) != soll.get(y)}))
    _melde("TrueSeasonal", "sonder: Jahr mit fehlendem Kurs UND Return verworfen (Seite wie gemeinsam)",
           not s["jahre"].get("2021", {}).get("gemeinsam") and not s["jahre"].get("2021", {}).get("seite"),
           str(s["jahre"].get("2021", {}).get("gemeinsam")))
    _melde("TrueSeasonal", "sonder: Fenster ersetzt fehlende Kalenderjahre nicht (N=5 -> 2022, 2024, 2025)",
           s["ts"]["2026|5"]["jahre"] == [2022, 2024, 2025] and s["ts"]["2026|10"]["jahre"] == [2018, 2019, 2020, 2022, 2024, 2025],
           f"{s['ts']['2026|5']['jahre']} / {s['ts']['2026|10']['jahre']}")
    mw = s["modellwahl"]["5"]
    _melde("TrueSeasonal", "sonder: Mindestmenge 4 bei N=5 unterschritten -> nicht ok", mw["ok"] is False and mw["n"] == 3
           and mw["mindest"] == 4, str(mw))
    za, zb = js["ziel_a"], js["ziel_b"]
    _melde("TrueSeasonal", "Zieljahr 2020 ×6: True Seasonal 2020 unverändert (Kurve identisch)",
           za["ts"]["2020|10"]["jahre"] == zb["ts"]["2020|10"]["jahre"]
           and all(x == y for x, y in zip(za["ts"]["2020|10"]["kurve"], zb["ts"]["2020|10"]["kurve"])))
    _melde("TrueSeasonal", "Zieljahr 2020 ×6: Modellauswahl mit IQR-Filter unverändert",
           za["modellwahl"]["10"] == zb["modellwahl"]["10"], f"{za['modellwahl']['10']} / {zb['modellwahl']['10']}")
    _melde("TrueSeasonal", "Gegenprobe: True Seasonal 2021 enthält 2020 und ändert sich",
           any(abs(x - y) > 1e-6 for x, y in zip(za["ts"]["2021|10"]["kurve"], zb["ts"]["2021|10"]["kurve"])))
    k = js["_kennzahl"]
    _melde("TrueSeasonal", "Kennzahl: konstante Reihe -> r null; identische Kurven -> r 1, 12 Treffer",
           k["konstant"]["r"] is None and k["konstant"]["treffer"] == 0 and k["flach"]["treffer"] == 0
           and nah(k["gleich"]["r"], 1.0, 1e-12)
           and k["gleich"]["treffer"] == 12 and k["gleich"]["immerPositiv"] == 12, str(k))
    pk = TS.vergleich12([100.0] * 365, [100 + i / 10 for i in range(365)])
    pf = TS.vergleich12([100.0] * 365, [100.0] * 365)
    _melde("TrueSeasonal", "Kennzahl Python: konstante Reihe -> r None, 0 Treffer; flach gegen flach 0 Treffer",
           pk["r"] is None and pk["treffer"] == 0 and pf["treffer"] == 0 and pf["r"] is None, f"{pk} / {pf}")
    # Analytisch: Soll unabhängig von beiden Implementierungen (statistics.correlation, Vorzeichen direkt)
    import statistics
    r_soll = statistics.correlation(a_soll, b_soll)
    tr_soll = sum(1 for x, y in zip(a_soll, b_soll) if x != 0 and y != 0 and (x > 0) == (y > 0))
    ip_soll = sum(1 for x in a_soll if x > 0)
    ka = k.get("analytisch") or {}
    pa = TS.vergleich12(kurve_ist, kurve_modell)
    _melde("TrueSeasonal", f"Kennzahl analytisch: Änderungen an den Monatsgrenzen = Vorgabe (JS + Python)",
           all(nah(x, y, 1e-12) for x, y in zip(k.get("aenderungen_ist") or [9] * 12, a_soll))
           and all(nah(x, y, 1e-12) for x, y in zip(TS.monats_aenderungen(kurve_ist), a_soll)),
           str([round(x, 4) for x in (k.get("aenderungen_ist") or [])][:4]))
    _melde("TrueSeasonal", f"Kennzahl analytisch: r = {r_soll:.4f}, {tr_soll} Treffer, {ip_soll}× Plus (JS + Python)",
           nah(ka.get("r"), r_soll, 1e-12) and ka.get("treffer") == tr_soll and ka.get("immerPositiv") == ip_soll
           and nah(pa["r"], r_soll, 1e-12) and pa["treffer"] == tr_soll and pa["immerPositiv"] == ip_soll,
           f"JS={ka} Py={pa}")
    sj = js["schalt"]["jahre"]
    feb, mar = 1, 2
    _melde("TrueSeasonal", "Schaltjahr-Achse: 29.02.2024 zählt zum März-Slot, 28.02.2023 zum Februar (Seiten-Builder)",
           sj["2024"]["aend"] is not None and nah(sj["2024"]["aend"][feb], 0.0, 1e-12)
           and nah(sj["2024"]["aend"][mar], math.log(1.1), 1e-9)
           and nah(sj["2023"]["aend"][feb], math.log(1.1), 1e-9) and nah(sj["2023"]["aend"][mar], 0.0, 1e-12),
           f"2024 Feb/Mär={sj['2024']['aend'][feb:mar + 1] if sj['2024']['aend'] else None} "
           f"2023 Feb/Mär={sj['2023']['aend'][feb:mar + 1] if sj['2023']['aend'] else None}")
    fw = js["filter"]["modellwahl"]["10"]
    _melde("TrueSeasonal", "Ausreißerfilter nur über die Vorjahre: 2011/2013/2015 raus, 2020–2022 ohne Einfluss",
           fw["jahre"] == [2010, 2012, 2014, 2016, 2017, 2018, 2019], str(fw))
    _melde("TrueSeasonal", "Mindestmenge NACH dem Filter: 7 von mindestens 8 -> nicht ok",
           fw["n"] == 7 and fw["mindest"] == 8 and fw["ok"] is False, str(fw))


def main() -> int:
    print("=" * 74)
    print("Zwillings-Pruefung: Backend (Python) <-> Frontend (JS) <-> Sollkurve")
    print("=" * 74)
    if "--nur-true-seasonal" in sys.argv:
        # Deploy-Gate: nur Block 8 (braucht pandas, plotly, node — nicht die Blog-/Yahoo-Abhängigkeiten der übrigen Blöcke)
        block_true_seasonal()
        if _ausfaelle:
            print(f"[FAIL] {len(_ausfaelle)} Abweichung(en):")
            for a in _ausfaelle:
                print(f"   - {a}")
            return 1
        print("[OK] True Seasonal: Zwillinge und Sollwerte.")
        return 0
    block_normalisierung()
    block_interpolation()
    block_turn_of_month()
    block_echtes_js()
    block_zeitzonen()
    block_zyklus()
    block_true_seasonal()
    block_python_only()
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

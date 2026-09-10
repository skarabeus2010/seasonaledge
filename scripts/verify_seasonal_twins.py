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

    # yearEndRef/yearCovers: die Sperren gegen Zirkelschluss, im echten JS.
    erwartet_yc = {
        "nur_laufendes":  (0, []),
        "alle_kurz":      (0, []),
        "dez_delisting":  (0, []),
        "nur_laufendes_spaet": (0, []),
        "voll_plus_kurz": (364, ["2023", "2024"]),
        # fail-closed: ein Jahr ohne last_actual_day gilt als NICHT
        # ausreichend, nicht als vollstaendig (Python: last_actual_day -> 0).
        "fehlt_lad": (364, ["2023"]),
    }
    for schluessel, (ref_soll, akz_soll) in erwartet_yc.items():
        got = d["yearcovers"][schluessel]
        _melde("Echtes JS", f"yearCovers/{schluessel} wie Python",
               got["ref"] == ref_soll and got["akzeptiert"] == akz_soll,
               f"JS={got} SOLL=ref {ref_soll}, akzeptiert {akz_soll}")

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

    # calculate_period_stats: die Gegenbeispiele zum Zirkelschluss.
    from shared.calculations import calculate_period_stats

    def _jahr(lad):
        return {"days": list(range(1, lad + 1)), "full_365": [100.0 + i * 0.02
                                                              for i in range(365)]}
    faelle = [
        ("nur laufendes Jahr zaehlt nicht", {2026: _jahr(250)}, 0),
        ("durchweg abgeschnittene Jahre zaehlen nicht",
         {2025: _jahr(250), 2026: _jahr(250)}, 0),
        ("XETRA-Jahresende (Tag 364) zaehlt",
         {2023: _jahr(364), 2024: _jahr(364), 2026: _jahr(250)}, 2),
        # Einziges Jahr ist das laufende, aber schon bei Tag 364: es gibt kein
        # abgeschlossenes Jahr als Massstab -> darf sich nicht selbst beglaubigen.
        ("laufendes Jahr allein, Tag 364, beglaubigt sich nicht selbst",
         {2026: _jahr(364)}, 0),
    ]
    for name, yd, erwartet in faelle:
        s = calculate_period_stats(yd, 1, 365)
        got = s.get("total_years", 0)
        _melde("Python-only", f"Periodenstatistik: {name}", got == erwartet,
               f"total_years={got} SOLL={erwartet}")

    # Und den WERT, nicht nur die Anzahl: ein um einen Kalendertag verschobener
    # Endindex aendert die Trefferzahl nicht — nur die Rendite. Ein Jahr, das von
    # 100 auf 110 laeuft und ab Tag 200 fortgeschrieben ist, muss ueber die
    # volle Periode exakt +10,00 % liefern.
    # Tag 1 = 100,00; ab Tag 200 konstant 110,00. Die Jahre reichen bis Tag 364
    # (XETRA-Jahresende), damit sie die Jahresende-Pruefung passieren.
    lauf = [100.0 + 10.0 * min(max(d_ - 1, 0), 199) / 199 for d_ in range(1, 366)]
    yd_wert = {2024: {"days": list(range(1, 365)), "full_365": lauf},
               2023: {"days": list(range(1, 365)), "full_365": lauf}}
    s = calculate_period_stats(yd_wert, 1, 365)
    _melde("Python-only", "Periodenstatistik liefert den richtigen WERT (+10,00 %)",
           s and abs(s.get("avg_return", 0) - 10.0) < 0.001,
           f"avg_return={s.get('avg_return')} SOLL=10.0 — ein verschobener "
           f"Endindex faellt bei einer reinen Anzahl-Pruefung nicht auf.")

    # Zweiter Wert-Test mit einer Periode MITTEN im Jahr. Bei end_day=365 liefern
    # min(end_day-1, 364) und min(end_day, 364) denselben Index — ein um einen Tag
    # verschobener Endindex bliebe dort unsichtbar. Bei Tag 100 nicht:
    # full_365[99] = 105,00 gegen full_365[100] = 105,05.
    s100 = calculate_period_stats(yd_wert, 1, 100)
    soll100 = (lauf[99] - lauf[0]) / lauf[0] * 100
    _melde("Python-only", "Periodenstatistik: Endindex bei Periode bis Tag 100",
           s100 and abs(s100.get("avg_return", 0) - soll100) < 1e-9,
           f"avg_return={s100.get('avg_return')} SOLL={soll100} "
           f"(ein Tag Versatz ergaebe {(lauf[100]-lauf[0])/lauf[0]*100}).")


def main() -> int:
    print("=" * 74)
    print("Zwillings-Pruefung: Backend (Python) <-> Frontend (JS) <-> Sollkurve")
    print("=" * 74)
    block_normalisierung()
    block_interpolation()
    block_turn_of_month()
    block_echtes_js()
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

#!/usr/bin/env python3
"""
verify_wahlen_twin.py — Zwillingsprüfung Browser ↔ Python für die Seite /wahlen.

Baut mit scripts/build_wahlen.baue() eine Studie aus synthetischen Zufallskursen auf dem
ECHTEN Kalender und der echten Wahlliste (mit eingebauten Datenlücken), schreibt sie als
JSON (wie im Betrieb: int-Schlüssel werden zu Strings), führt die echte
landing/js/wahlen-compute.js in node aus (scripts/js/probe_wahlen.js) und vergleicht jede
Zahl mit shared/elections.aggregiere. Dazu feste Fälle: Quantile = numpy, Basisdatum,
Live-Linie bei X=5 (Basis in der Zukunft) und X=25.

    py -3.14 scripts/verify_wahlen_twin.py               # Exit 0 = grün
    py -3.14 scripts/verify_wahlen_twin.py --mutationen  # zusätzlich JS-Mutationen (müssen rot werden)
"""
from __future__ import annotations

import argparse
import json
import math
import random
import shutil
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from shared import elections as el  # noqa: E402

JS = REPO / "landing" / "js" / "wahlen-compute.js"
PROBE = REPO / "scripts" / "js" / "probe_wahlen.js"
STICHTAG = date(2026, 10, 5)

OPTIONEN = [
    {"reihe": "^GSPC", "typ": "president", "x": 20, "y": 20, "basis": "t0"},
    {"reihe": "^GSPC", "typ": "midterm", "x": 20, "y": 20, "basis": "t0"},
    {"reihe": "^DJI", "typ": "alle", "x": 60, "y": 60, "basis": "t0"},
    {"reihe": "^GSPC", "typ": "midterm", "x": 25, "y": 10, "basis": "tx"},
    {"reihe": "^GSPC", "typ": "president", "x": 5, "y": 40, "basis": "tx", "abJahr": 1950},
    {"reihe": "^DJI", "typ": "president", "x": 10, "y": 10, "basis": "t0", "wechsel": "ja"},
    {"reihe": "^GSPC", "typ": "midterm", "x": 10, "y": 30, "basis": "t0", "wechsel": "nein"},
    {"reihe": "^GSPC", "typ": "president", "x": 10, "y": 10, "basis": "t0", "wechsel": "nein"},
]


def studie(stichtag: date = STICHTAG) -> dict:
    """Synthetische Studie: Zufallsrenditen, echter Kalender, ein paar Lücken."""
    import build_wahlen as bw

    ist = el.lade_kalender("NYSE")
    zu = {el.us_wahltag(y) for y in range(1896, 1969)} | {el.us_wahltag(y) for y in (1972, 1976, 1980)}
    luecken = {date(1987, 11, 20), date(2002, 12, 10)}   # fehlende Sitzungen → fensterabhängige Ausschlüsse

    def laden(t):
        rnd = random.Random(7 if t == "^GSPC" else 11)
        daten, closes, x, v = [], [], date(1885, 1, 2) if t == "^GSPC" else date(1896, 1, 2), 100.0
        while x <= stichtag:
            s = ist(x)
            offen = (x.weekday() < 5 and x not in zu) if s is None else s
            if offen and x not in luecken:
                v *= math.exp(rnd.gauss(0.0003, 0.011))
                daten.append(x.isoformat())
                closes.append(round(v, 6))
            x += timedelta(days=1)
        return daten, closes

    st = json.loads(json.dumps(bw.baue(laden=laden, letzte=stichtag)))   # Rundreise wie im Betrieb
    # Unbekannte Ergebnisse (gibt es in der echten Liste nicht): müssen aus Ergebnisfiltern fallen.
    for w in st["wahlen"]:
        if w["id"] == "us-president-1988":
            w["machtwechsel"] = None
        if w["id"] == "us-midterm-1990":
            w["house_after"] = None
    return st


def js_lauf(st: dict, opts: list, js: Path = JS) -> list:
    with tempfile.TemporaryDirectory() as t:
        a, b = Path(t) / "st.json", Path(t) / "o.json"
        a.write_text(json.dumps(st), encoding="utf-8")
        b.write_text(json.dumps(opts), encoding="utf-8")
        env = {**__import__("os").environ, "WAHLEN_JS": str(js)}
        p = subprocess.run(["node", str(PROBE), str(a), str(b)], capture_output=True, text=True, env=env, timeout=120)
    if p.returncode != 0:
        raise RuntimeError(p.stderr[:400])
    return json.loads(p.stdout)


def gleich(a, b, pfad: str, f: list) -> None:
    if isinstance(a, dict):
        for k in a:
            gleich(a[k], b.get(k) if isinstance(b, dict) else None, f"{pfad}.{k}", f)
    elif isinstance(a, list):
        if not isinstance(b, list) or len(a) != len(b):
            f.append(f"{pfad}: Länge {len(a)} ≠ {len(b) if isinstance(b, list) else b}")
            return
        for i, (x, y) in enumerate(zip(a, b)):
            gleich(x, y, f"{pfad}[{i}]", f)
    elif a is None or b is None or isinstance(a, (str, bool)) or isinstance(b, (str, bool)):
        if a != b:
            f.append(f"{pfad}: Python {a!r} ≠ JS {b!r}")
    elif abs(a - b) > 1e-9 * max(1.0, abs(a)):
        f.append(f"{pfad}: Python {a} ≠ JS {b}")


def pruefe(st: dict, js: Path = JS) -> list[str]:
    f: list[str] = []
    ergebnisse = js_lauf(st, OPTIONEN, js)
    for o, r in zip(OPTIONEN, ergebnisse):
        py = el.aggregiere(st, o["reihe"], o["typ"], o["x"], o["y"], o.get("basis", "t0"),
                           o.get("abJahr"), o.get("wechsel", "alle"))
        name = f"{o['reihe']} {o['typ']} {o['x']}/{o['y']} {o.get('basis')} {o.get('wechsel', '')}"
        if py["kennzahlen"]["n"] == 0:
            f.append(f"{name}: leere Stichprobe — Test ohne Aussage")
        # Vollständiger Vertrag: Kurven, Kennzahlen, Einzelwerte, Ausschlüsse, Live (Codex R1)
        gleich(py, {"kurven": r["kurven"], "kennzahlen": r["kennzahlen"], "einzel": r["einzel"],
                    "ausgeschlossen": r["ausgeschlossen"], "live": r["live"]}, name, f)
        if r["offsets"] != list(range(-o["x"], o["y"] + 1)):
            f.append(f"{name}: Offsets falsch")
    # Unbekannte Ergebnisse: weder in 'ja' noch in 'nein', aber in 'alle'
    alle = el.aggregiere(st, "^GSPC", "president", 10, 10)["kennzahlen"]["n"]
    ja = el.aggregiere(st, "^GSPC", "president", 10, 10, wechsel="ja")["kennzahlen"]["n"]
    nein = el.aggregiere(st, "^GSPC", "president", 10, 10, wechsel="nein")["kennzahlen"]["n"]
    if ja + nein != alle - 1:
        f.append(f"unbekannter Machtwechsel: ja {ja} + nein {nein} ≠ alle {alle} − 1")
    # Stichprobe schrumpft mit dem Fenster (Lücke 1987/2002 betrifft nur breite Fenster)
    n20 = ergebnisse[1]["kennzahlen"]["n"]
    n60 = el.aggregiere(st, "^GSPC", "midterm", 60, 60)["kennzahlen"]["n"]
    if not n60 < n20:
        f.append(f"fensterabhängige Stichprobe: 60/60 ({n60}) nicht kleiner als 20/20 ({n20})")
    # Quantile = numpy
    try:
        import numpy as np
        rnd = random.Random(3)
        for k in (1, 2, 5, 33):
            werte = [rnd.random() for _ in range(k)]
            for q in (0.25, 0.5, 0.75):
                if abs(el._quantil(werte, q) - float(np.quantile(werte, q))) > 1e-12:
                    f.append(f"Quantil n={k} q={q} weicht von numpy ab")
    except ImportError:
        f.append("numpy fehlt — Quantilvergleich nicht geprüft")
    # Basisdatum unabhängig nachgerechnet: t0 = Ankerdatum, t−X = Datum der Kurszeile X Zeilen vorher
    for o, r in zip(OPTIONEN, ergebnisse):
        for e in r["einzel"][:5]:
            w = next(w for w in st["wahlen"] if w["id"] == e["id"])
            p = w["reihen"][o["reihe"]]["pfad"]
            soll = p["t0"] if o.get("basis") != "tx" else (
                date.fromisoformat(p["t0"]) + timedelta(days=p["tage"][st["fenster"] - o["x"]])).isoformat()
            if e["basisDatum"] != soll:
                f.append(f"Basisdatum {e['id']} ({o.get('basis')}): {e['basisDatum']} statt {soll}")
    # „alle": die chronologisch nächste Wahl (Midterm 2026, nicht Präsident 2028) ist live
    lv_alle = js_lauf(st, [{"reihe": "^GSPC", "typ": "alle", "x": 25, "y": 5, "basis": "tx"}], js)[0]["live"]
    if not lv_alle or lv_alle["id"] != "us-midterm-2026":
        f.append(f"Live bei 'alle': {lv_alle and lv_alle['id']} statt us-midterm-2026")
    # Live: Midterm 2026, Stichtag 05.10. → letzter Kurs bei Offset −21
    lv5 = js_lauf(st, [{"reihe": "^GSPC", "typ": "midterm", "x": 5, "y": 5, "basis": "tx"}], js)[0]["live"]
    lv25 = js_lauf(st, [{"reihe": "^GSPC", "typ": "midterm", "x": 25, "y": 5, "basis": "tx"}], js)[0]["live"]
    if not lv5 or lv5["kurve"] is not None:
        f.append(f"Live X=5: Basis liegt in der Zukunft, Kurve muss null sein ({lv5 and lv5['kurve']})")
    if not lv25 or not lv25["kurve"] or abs(lv25["kurve"][0] - 100) > 1e-9:
        f.append("Live X=25: Kurve fehlt oder nicht auf t−25 = 100 normiert")
    else:
        gefuellt = [i - 25 for i, v in enumerate(lv25["kurve"]) if v is not None]
        if max(gefuellt) != -21 or len(gefuellt) != 5:
            f.append(f"Live X=25: gefüllte Offsets {gefuellt}, erwartet −25…−21")
        p = next(w for w in st["wahlen"] if w["id"] == "us-midterm-2026")["reihen"]["^GSPC"]["pfad"]
        n = st["fenster"]
        soll = [100 * p["c"][n + k] / p["c"][n - 25] for k in range(-25, -20)]
        if any(abs(a - b) > 1e-9 for a, b in zip(lv25["kurve"][:5], soll)):
            f.append("Live X=25: Werte stimmen nicht mit Kurs/Kurs(t−25) überein")
    return f


def pruefe_wahltag(js: Path = JS) -> list[str]:
    """Wahltag selbst und Folgetag bei unverändertem Status 'scheduled' (Codex R1)."""
    f: list[str] = []
    for tag in (date(2026, 11, 3), date(2026, 11, 4)):
        st = studie(tag)
        lv = js_lauf(st, [{"reihe": "^GSPC", "typ": "midterm", "x": 20, "y": 5, "basis": "tx"}], js)[0]["live"]
        py = el.aggregiere(st, "^GSPC", "midterm", 20, 5, "tx")["live"]
        gleich(py, lv, f"Wahltag {tag}", f)
        if not lv or lv["stichtag"] != tag.isoformat() or lv["letzter_kurs"] != tag.isoformat():
            f.append(f"Wahltag {tag}: Datenstand {lv and (lv['stichtag'], lv['letzter_kurs'])} verloren")
        if not lv or lv["t0"] != "2026-11-03" or not lv["kurve"] or lv["kurve"][20] is None:
            f.append(f"Wahltag {tag}: t0-Kurs fehlt in der Live-Linie")
    return f


MUTATIONEN = {
    "Quantil mit Floor-Indexing": ("return a[lo] + (a[hi] - a[lo]) * (pos - lo);", "return a[lo];"),
    "unvollständige Fenster zugelassen": ("      if (v === null || v === undefined) return null;\n      out.push(v);",
                                          "      if (v === null || v === undefined) { out.push(out.length ? out[out.length - 1] : 1); continue; }\n      out.push(v);"),
    "Basis t−X statt t0": ("var basisIdx = opts.basis === 'tx' ? 0 : x;", "var basisIdx = 0;"),
    "Nachlauf auf t−X bezogen": ("nachlauf: 100 * (roh[laenge - 1] / roh[x] - 1),", "nachlauf: 100 * (roh[laenge - 1] / roh[0] - 1),"),
    "Referenz mit unvollständigem Tripel": ("if (ks.length === 2 && ks[0] && ks[1]) {", "if (ks.length === 2 && (ks[0] || ks[1])) { ks = [ks[0] || ks[1], ks[1] || ks[0]];"),
    "unbekannter Wechsel als 'nein'": ("      if (wert === null) return false;", "      if (wert === null) wert = false;"),
    "Live ohne Basisprüfung": ("    if (basis === null || basis === undefined) return aus;", "    if (basis === null || basis === undefined) basis = 1;"),
    "Live-Werte alle 100 (Codex R1)": ("      aus.kurve.push(v === null || v === undefined ? null : 100 * v / basis);",
                                        "      aus.kurve.push(v === null || v === undefined ? null : 100);"),
    "Live in Dateireihenfolge (Codex R1)": ("if (r.pfad && (!live || w.date < live.wahl.date))", "if (r.pfad && !live)"),
    "Datenstand nach Wahltag verloren (Codex R1)": ("stichtag: p.stichtag || st.letzte_session || null,", "stichtag: p.stichtag || null,"),
    "Basisdatum t−X falsch": ("basisDatum: datum(r.pfad, opts.basis === 'tx' ? -x : 0, n)", "basisDatum: datum(r.pfad, 0, n)"),
    "Ausschlussgrund verloren": ("ausgeschlossen.push({ id: w.id, grund: r.ausgeschlossen || grundImFenster(r.pfad, x, y, n) });",
                                 "ausgeschlossen.push({ id: w.id, grund: 'unvollstaendig' });"),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mutationen", action="store_true")
    a = ap.parse_args()
    if not shutil.which("node"):
        print("node fehlt — Zwillingsprüfung nicht möglich")
        return 1
    st = studie()
    f = pruefe(st) + pruefe_wahltag()
    for x in f[:20]:
        print("  FEHLER " + x)
    print(f"verify_wahlen_twin: {len(OPTIONEN)} Optionssätze, {len(f)} Fehler")
    if f or not a.mutationen:
        return 1 if f else 0
    quelle = JS.read_text(encoding="utf-8")
    verfehlt = 0
    with tempfile.TemporaryDirectory() as t:
        for name, (alt, neu) in MUTATIONEN.items():
            if alt not in quelle:
                print(f"  WIRKUNGSLOS  {name}")
                verfehlt += 1
                continue
            mut = Path(t) / "wahlen-compute.js"
            mut.write_text(quelle.replace(alt, neu, 1), encoding="utf-8")
            try:
                rot = bool(pruefe(st, mut)) or bool(pruefe_wahltag(mut))
            except Exception:  # noqa: BLE001
                rot = True
            print(("  gefangen     " if rot else "  VERFEHLT     ") + name)
            verfehlt += 0 if rot else 1
    print(f"verify_wahlen_twin --mutationen: {len(MUTATIONEN) - verfehlt}/{len(MUTATIONEN)} gefangen")
    return 1 if verfehlt else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
verify_saison_score.py — Wächter für den Saison-Score (Plan v1–v3, Codex-Freigabe 2026-10-09).

Drei Rechnungen, die übereinstimmen müssen:
  1. das ECHTE landing/js/saison-score.js in node (scripts/js/probe_saison_score.js),
  2. der Python-Zwilling shared/saison_score.py,
  3. eine naive Referenz hier im Wächter (numpy.interp, numpy.corrcoef, eigene Datumssuche — keine der Hilfsfunktionen
     von 1 oder 2).
Dazu konstruierte Randfälle (19./20. Handelstag, Präfixinvarianz, 29.02., 31.12. im Schaltjahr, Fenster über den
Jahreswechsel, < 10 Jahre, konstanter Pfad, Marktklasse, fehlender Ticker) und die exakte Gleichheit der schnellen
Interpolation mit shared.calculations.interpolate_to_365.

Nutzung:
    py -3.14 scripts/verify_saison_score.py --snapshot <ordner>     # alles (Snapshot mit SPY/QQQ/_DJI/_GSPC/_GDAXI)
    py -3.14 scripts/verify_saison_score.py --ohne-snapshot         # ohne echte Reihen (bewusst)
    py -3.14 scripts/verify_saison_score.py --mutationen            # prüft den Wächter (auf Kopien)
"""
from __future__ import annotations
import datetime as dt
import importlib.util
import json
import math
import pathlib
import random
import shutil
import subprocess
import sys
import tempfile

import numpy as np

REPO = pathlib.Path(__file__).resolve().parent.parent
SC, DC, SS = "landing/js/seasonal-compute.js", "landing/js/decade-compute.js", "landing/js/saison-score.js"
PY = "shared/saison_score.py"
PROBE = "scripts/js/probe_saison_score.js"
SNAP = {"SPY": "SPY.json", "QQQ": "QQQ.json", "^DJI": "_DJI.json", "^GSPC": "_GSPC.json", "^GDAXI": "_GDAXI.json"}


def lade_py(basis: pathlib.Path):
    sys.path.insert(0, str(REPO))       # shared.calculations kommt aus dem Repo
    spec = importlib.util.spec_from_file_location("saison_score_kopie", basis / PY)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ── naive Referenz ───────────────────────────────────────────────────────────
def referenz(daten, closes, ticker, as_of=None):
    t = str(ticker or "").strip().upper()
    if not t:
        raise ValueError("Ticker fehlt")
    T = 1 if t.endswith("-USD") else 3 if t.endswith("=X") else 7
    m = {}
    for d, c in zip(daten, closes):
        if c is None or not isinstance(c, (int, float)) or not math.isfinite(c) or c <= 0:
            continue
        if as_of and d[:10] > as_of:
            continue
        m[d[:10]] = float(c)
    ds = sorted(m)
    if not ds:
        return {"status": "nicht_berechenbar", "grund_code": "keine_kurse"}
    tage = [dt.date.fromisoformat(d) for d in ds]
    cs = [m[d] for d in ds]
    a = tage[-1]
    jahre = {}
    for i, d in enumerate(tage):
        jahre.setdefault(d.year, []).append(i)

    def pfad(y):
        idx = jahre.get(y)
        if not idx or len(idx) < 20 or tage[idx[0]].month != 1 or tage[idx[0]].day > 10:
            return None
        x = [min(tage[k].timetuple().tm_yday, 365) for k in idx]
        v = [100 * cs[k] / cs[idx[0]] for k in idx]
        dd = {}
        for xx, vv in zip(x, v):
            dd[xx] = vv                       # Tag 366 → 365, spätester Wert gewinnt
        xs = sorted(dd)
        return np.interp(np.arange(1, 366), xs, [dd[k] for k in xs])

    if a.year not in jahre or len(jahre[a.year]) < 20:
        return {"status": "nicht_berechenbar", "grund_code": "zu_frueh_im_jahr"}
    py_ = pfad(a.year)
    if py_ is None:
        return {"status": "nicht_berechenbar", "grund_code": "unvollstaendiges_jahr"}
    d = min(a.timetuple().tm_yday, 365)

    def letzte_bis(ziel):
        k = [i for i in range(len(tage)) if tage[i] <= ziel]
        return k[-1] if k else -1

    def fenster(y):
        import calendar
        z1 = dt.date(y, a.month, min(a.day, calendar.monthrange(y, a.month)[1]))
        z2 = z1 + dt.timedelta(days=30)
        s, e = letzte_bis(z1), letzte_bis(z2)
        if s < 0 or e <= s or (z1 - tage[s]).days > T or (z2 - tage[e]).days > T:
            return None
        if any((tage[k] - tage[k - 1]).days > T for k in range(s + 1, e + 1)):
            return None
        return (cs[e] / cs[s] - 1) * 100

    L = []
    for y in range(a.year - 1, tage[0].year - 1, -1):
        if len(L) >= 20:
            break
        p = pfad(y)
        if p is None:
            continue
        R = fenster(y)
        if R is None:
            continue
        L.append((y, R, p))
    if len(L) < 10:
        return {"status": "nicht_berechenbar", "grund_code": "zu_wenige_jahre"}
    cur = py_[:d]
    kand = []
    for y, R, p in L:
        if np.ptp(cur) == 0 or np.ptp(p[:d]) == 0:     # exakt konstant (nicht std: Summationsrest)
            continue
        kand.append((float(np.corrcoef(cur, p[:d])[0, 1]), y, R))
    kand.sort(key=lambda k: (-k[0], -k[1]))
    top = kand[:5]
    if len(top) < 5:
        return {"status": "nicht_berechenbar", "grund_code": "zu_wenige_musterjahre"}
    w = [(r + 1) / 2 for r, _, _ in top]
    if not sum(w) > 0:
        return {"status": "nicht_berechenbar", "grund_code": "gewichte_null"}
    b1 = sum(R > 0 for _, R, _ in L) / len(L)
    b2 = min(1, max(0, (np.mean([R for _, R, _ in L]) + 3) / 6))
    b3 = sum(R > 0 for _, _, R in top) / 5
    b4 = min(1, max(0, (sum(wi * R for wi, (_, _, R) in zip(w, top)) / sum(w) + 3) / 6))
    return {"status": "ok", "score_roh": 2.5 * (b1 + b2 + b3 + b4), "musterjahre": [y for _, y, _ in top],
            "jahre": [y for y, _, _ in L]}


# ── Fälle ────────────────────────────────────────────────────────────────────
def werktage(von, bis, f, ohne=()):
    out, d, i = [], dt.date.fromisoformat(von), 0
    while d <= dt.date.fromisoformat(bis):
        if d.weekday() < 5 and d.isoformat() not in ohne:
            out.append({"date": d.isoformat(), "close": f(i, d)})
            i += 1
        d += dt.timedelta(days=1)
    return out


def welle(i, d):
    return 100 * math.exp(0.0003 * i + 0.03 * math.sin(i / 11.0) + 0.015 * math.sin(i / 3.1) + 0.01 * math.sin(d.year * 1.7 + i / 40))


def taeglich(von, bis, f):
    out, d = [], dt.date.fromisoformat(von)
    while d <= dt.date.fromisoformat(bis):
        out.append({"date": d.isoformat(), "close": f(d)})
        d += dt.timedelta(days=1)
    return out


def faelle():
    basis = werktage("1990-01-02", "2025-06-30", welle)
    F = [
        {"id": "basis", "ticker": "SPY", "rows": basis},
        {"id": "praefix", "ticker": "SPY", "rows": basis + werktage("2025-07-01", "2025-12-31", lambda i, d: 1.0),
         "as_of": "2025-06-30", "soll": "gleich:basis"},
        {"id": "handelstag19", "ticker": "SPY", "rows": [r for r in werktage("1990-01-02", "2025-12-31", welle)
                                                        if r["date"] <= "2025-01-27"], "soll": "zu_frueh_im_jahr"},
        {"id": "handelstag20", "ticker": "SPY", "rows": [r for r in werktage("1990-01-02", "2025-12-31", welle)
                                                        if r["date"] <= "2025-01-28"], "soll": "ok"},
        {"id": "schalttag", "ticker": "SPY", "rows": werktage("1990-01-02", "2024-02-29", welle), "soll": "ok"},
        {"id": "silvester_schalt", "ticker": "SPY", "rows": werktage("1990-01-02", "2024-12-31", welle), "soll": "ok"},
        {"id": "jahreswechsel", "ticker": "SPY", "rows": werktage("1990-01-02", "2024-12-16", welle), "soll": "ok"},
        {"id": "zu_wenige_jahre", "ticker": "SPY", "rows": werktage("2017-01-02", "2025-06-30", welle), "soll": "zu_wenige_jahre"},
        {"id": "konstant", "ticker": "SPY", "rows": werktage("1990-01-02", "2025-06-30", lambda i, d: 50.0),
         "soll": "zu_wenige_musterjahre"},
        {"id": "ohne_ticker", "ticker": "", "rows": basis, "soll": "fehler"},
        # Codex Kern R1: Dezimalkurs konstant → Normierung 99.99999999999999, Summationsrest → galt als r = 1
        {"id": "konstant_dezimal", "ticker": "SPY", "rows": werktage("2000-01-01", "2025-02-11", lambda i, d: 0.17),
         "soll": "zu_wenige_musterjahre"},
        # Codex Kern R1: alle Musterjahre exakt gegenläufig → r = −1 → Gewichtssumme 0
        {"id": "gewichte_null", "ticker": "BTC-USD", "rows": taeglich("2000-01-01", "2025-01-20",
            lambda d: 100 + (d.timetuple().tm_yday - 1) / 8 if d.year == 2025 else 100 - (d.timetuple().tm_yday - 1) / 8),
         "soll": "gewichte_null"},
        {"id": "schalt_3012", "ticker": "SPY", "rows": werktage("1990-01-02", "2024-12-30", welle), "soll": "ok"},
        # Analytisch: jedes Jahr steigt der Kurs 10 Kalendertage nach dem Zieltag um genau 10 % → jede Fensterrendite
        # +10 % → B1 = B3 = 1, B2 = B4 = clip(13/6) = 1 → Score 10,0; davor eine Welle für das Matching
        {"id": "sprung", "ticker": "BTC-USD", "rows": taeglich("1995-01-01", "2025-06-15",
            lambda d: 100 * (1.1 if (d.month, d.day) > (6, 25) else 1.0) + (math.sin(d.timetuple().tm_yday / 5) if d.month < 6 else 0)),
         "soll": "ok"},
        # Gleichstand: tägliche Kurse, Pfad hängt nur vom Monat/Tag ab → alle Nicht-Schaltjahre exakt gleiches r
        {"id": "gleichstand", "ticker": "BTC-USD", "rows": taeglich("1990-01-01", "2025-08-15",
            lambda d: 100 + 3 * math.sin(d.timetuple().tm_yday / 9) + d.timetuple().tm_yday / 40), "soll": "ok"},
        # gleiche Reihe mit einer zweitägigen Lücke in jedem Fenster eines Vorjahres: Krypto verwirft die Jahre, Börse nicht
        {"id": "klasse_boerse", "ticker": "SPY", "rows": werktage("1990-01-02", "2025-06-30", welle,
                                                                   ohne={f"{y}-07-09" for y in range(1990, 2025)}), "soll": "ok"},
        {"id": "klasse_krypto", "ticker": "BTC-USD", "rows": werktage("1990-01-02", "2025-06-30", welle,
                                                                       ohne={f"{y}-07-09" for y in range(1990, 2025)}),
         "soll": "zu_wenige_jahre"},
        {"id": "spaeter_start", "ticker": "SPY", "rows": [r for r in basis if not r["date"].startswith("2025-01-0")
                                                          and not r["date"][:7] == "2025-01" or r["date"] >= "2025-01-15"],
         "soll": "unvollstaendiges_jahr"},
    ]
    return F


RUNDUNG = [1.25, 0.25, 0.75, 9.94, 2.5]
RUNDUNG_SOLL = [1.3, 0.3, 0.8, 9.9, 2.5]


def node_probe(basis, fl, tmp, reihen=None):
    p = pathlib.Path(tmp) / "faelle.json"
    p.write_text(json.dumps({"reihen": reihen or {}, "rundung": RUNDUNG,
                             "faelle": [{k: v for k, v in f.items() if k != "soll"} for f in fl]}),
                 encoding="utf-8")
    r = subprocess.run(["node", str(basis / PROBE), str(basis / SC), str(basis / DC), str(basis / SS), str(p)],
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise RuntimeError("Probe abgebrochen: " + r.stderr[-400:])
    o = json.loads(r.stdout)
    erg = {x["id"]: x for x in o["faelle"]}
    erg["__rundung__"] = o["rundung"]
    return erg


ZAHLEN = [("score_roh",), ("b1", "wert"), ("b2", "wert"), ("b2", "mittel"), ("b3", "wert"), ("b4", "wert"),
          ("b4", "mittel"), ("vergleich_ohne_matching",), ("konformitaet",)]


def _hol(e, pfad):
    for k in pfad:
        e = (e or {}).get(k)
    return e


def zwilling_gleich(js, py):
    if js.get("status") != py.get("status") or js.get("grund_code") != py.get("grund_code"):
        return False, f"Status JS {js.get('status')}/{js.get('grund_code')} PY {py.get('status')}/{py.get('grund_code')}"
    if js.get("status") != "ok":
        return True, ""
    for pf in ZAHLEN:
        a, b = _hol(js, pf), _hol(py, pf)
        if (a is None) != (b is None) or (a is not None and a != b):
            return False, f"{'.'.join(pf)}: JS {a} PY {b}"
    for k in ("score", "jahre", "as_of", "fenster"):
        if js.get(k) != py.get(k):
            return False, f"{k}: JS {js.get(k)} PY {py.get(k)}"
    if [m["jahr"] for m in js["musterjahre"]] != [m["jahr"] for m in py["musterjahre"]] or \
            any(a["r"] != b["r"] or a["rendite"] != b["rendite"] for a, b in zip(js["musterjahre"], py["musterjahre"])):
        return False, "Musterjahre weichen ab"
    return True, ""


def ref_gleich(py, ref):
    if py.get("status") != ref.get("status") or (py.get("status") != "ok" and py.get("grund_code") != ref.get("grund_code")):
        return False, f"Status PY {py.get('status')}/{py.get('grund_code')} REF {ref.get('status')}/{ref.get('grund_code')}"
    if py.get("status") != "ok":
        return True, ""
    if abs(py["score_roh"] - ref["score_roh"]) > 1e-9 or py["jahre"] != ref["jahre"] or \
            [m["jahr"] for m in py["musterjahre"]] != ref["musterjahre"]:
        return False, f"PY {py['score_roh']} {[m['jahr'] for m in py['musterjahre']]} REF {ref['score_roh']} {ref['musterjahre']}"
    return True, ""


def pruefen(basis: pathlib.Path, snap: pathlib.Path | None) -> dict:
    P = {}
    py = lade_py(basis)
    # 0) schnelle Interpolation exakt = interpolate_to_365
    from shared.calculations import interpolate_to_365
    rnd = random.Random(20261009)
    abw = 0
    for _ in range(1500):
        n = rnd.randint(1, 260)
        days = sorted(rnd.sample(range(1, 367), n))
        vals = [rnd.uniform(50, 150) for _ in days]
        abw += py.interp365(days, vals) != interpolate_to_365(days, vals)
    P["interp_exakt"] = True if abw == 0 else f"{abw}/1500 ungleich"
    with tempfile.TemporaryDirectory() as tmp:
        fl = faelle()
        js = node_probe(basis, fl, tmp)
        rj = js.pop("__rundung__")
        rp = [py._runden1(x) for x in RUNDUNG]
        P["rundung"] = True if (rj == RUNDUNG_SOLL and rp == RUNDUNG_SOLL) else f"JS {rj} PY {rp} Soll {RUNDUNG_SOLL}"
        for f in fl:
            o = js[f["id"]]
            soll = f.get("soll", "ok")
            daten, closes = [r["date"] for r in f["rows"]], [r["close"] for r in f["rows"]]
            if soll == "fehler":
                try:
                    py.berechne(daten, closes, f["ticker"])
                    pyf = False
                except ValueError:
                    pyf = True
                P[f"fall_{f['id']}"] = True if ("fehler" in o and pyf) else f"kein Fehler bei fehlendem Ticker: JS {o}, PY {pyf}"
                continue
            if "fehler" in o:
                P[f"fall_{f['id']}"] = f"JS warf: {o['fehler']}"
                continue
            e_js = o["ergebnis"]
            try:
                e_py = py.berechne(daten, closes, f["ticker"], f.get("as_of"))
            except Exception as ex:  # noqa: BLE001 — ein Absturz des Kerns ist ein Befund dieses Falls, kein Probeabbruch
                P[f"fall_{f['id']}"] = f"PY warf: {type(ex).__name__}: {ex}"
                continue
            ok1, t1 = zwilling_gleich(e_js, e_py)
            ok2, t2 = ref_gleich(e_py, referenz(daten, closes, f["ticker"], f.get("as_of")))
            if soll.startswith("gleich:"):
                ok3 = js[soll.split(":")[1]]["ergebnis"] == e_js
                t3 = "" if ok3 else "as_of nicht präfixinvariant"
            else:
                ok3 = e_js.get("status") == soll or e_js.get("grund_code") == soll
                t3 = "" if ok3 else f"erwartet {soll}, ist {e_js.get('status')}/{e_js.get('grund_code')}"
            P[f"fall_{f['id']}"] = True if (ok1 and ok2 and ok3) else "; ".join(x for x in (t1, t2, t3) if x)
        e = js["sprung"]["ergebnis"]
        P["soll_sprung_analytisch"] = True if (e.get("status") == "ok" and e.get("score") == 10.0 and e["b1"]["k"] == e["b1"]["n"] == 20
                                               and abs(e["b1"]["wert"] - 1) < 1e-12 and abs(e["b2"]["mittel"] - 10) < 1e-9) \
            else f"Sprung: score {e.get('score')} b1 {e.get('b1')} b2 {e.get('b2')}"
        e = js["gleichstand"]["ergebnis"]
        mj = e.get("musterjahre") or []
        gleich = [(a["jahr"], b["jahr"]) for a, b in zip(mj, mj[1:]) if a["r"] == b["r"]]
        P["soll_gleichstand_jung"] = True if (gleich and all(a > b for a, b in gleich)) \
            else f"Gleichstände {gleich} (müssen vorhanden und absteigend sein)"
        e = js["silvester_schalt"]["ergebnis"]
        P["soll_tag366_auf_365"] = True if (e.get("status") == "ok" and e.get("as_of") == "2024-12-31") else f"{e}"
        if snap:
            reihen, fl2 = {}, []
            for t, datei in SNAP.items():
                rows = [{"date": z["date"], "close": z["close"]} for z in json.loads((snap / datei).read_text())]
                reihen[t] = rows
                daten = [r["date"] for r in rows if r["date"] >= "2005-01-01"]
                for d in daten[::5]:
                    fl2.append({"id": f"{t}@{d}", "ticker": t, "reihe": t, "as_of": d})
            js2 = node_probe(basis, fl2, tmp, reihen)
            abw_z, abw_r, stati = [], [], {}
            for f in fl2:
                rows = reihen[f["reihe"]]
                daten, closes = [r["date"] for r in rows], [r["close"] for r in rows]
                e_py = py.berechne(daten, closes, f["ticker"], f["as_of"])
                ok1, t1 = zwilling_gleich(js2[f["id"]]["ergebnis"], e_py)
                stati[e_py["status"] if e_py["status"] == "ok" else e_py["grund_code"]] = \
                    stati.get(e_py["status"] if e_py["status"] == "ok" else e_py["grund_code"], 0) + 1
                if not ok1:
                    abw_z.append(f"{f['id']}: {t1}")
                if len(abw_r) < 3 and fl2.index(f) % 35 == 0:     # Referenz ist langsam → jede 35. Stichprobe
                    ok2, t2 = ref_gleich(e_py, referenz(daten, closes, f["ticker"], f["as_of"]))
                    if not ok2:
                        abw_r.append(f"{f['id']}: {t2}")
            P["echt_zwilling"] = True if not abw_z else f"{len(abw_z)}/{len(fl2)} ungleich, z. B. {abw_z[:2]}"
            P["echt_referenz"] = True if not abw_r else f"Referenz weicht ab: {abw_r}"
            print(f"  Info: {len(fl2)} echte Stichtage, Status {stati}")
    return P


# ── Mutationen (auf Kopien) ──────────────────────────────────────────────────
MUTATIONEN = [
    ("JS: Gesamtjahr statt Fenster", SS, "      return (r[e].close / r[s].close - 1) * 100;",
     "      return (r[Math.min(n - 1, e + 200)].close / r[s].close - 1) * 100;", "fall_basis"),
    ("PY: Lookback 15 statt 20", PY, "LOOKBACK = 20", "LOOKBACK = 15", "fall_basis"),
    ("JS: Gleichstand älteres Jahr zuerst", SS, "return b.r - a.r || b.jahr - a.jahr;", "return b.r - a.r || a.jahr - b.jahr;", "soll_gleichstand_jung"),
    ("JS: Konstanz nicht vor dem Mittelwert geprüft", SS, "    if (amin === amax || bmin === bmax) return null;\n", "", "fall_konstant_dezimal"),
    ("JS: Mindestens 15 Handelstage", SS, "MIN_HANDELSTAGE: 20,", "MIN_HANDELSTAGE: 15,", "fall_handelstag19"),
    ("PY: Schalttag ohne Monatsende", PY, "    return (dt.date(y, m, min(d, letzter)) - dt.date(1970, 1, 1)).days",
     "    return (dt.date(y, m, d) - dt.date(1970, 1, 1)).days if (m, d) != (2, 29) or y % 4 == 0 else (dt.date(y, 3, 1) - dt.date(1970, 1, 1)).days",
     "fall_schalttag"),
    ("JS: as_of nicht zuerst angewandt", SS, "    var r = DC._bereinigen(rows, asOfOpt), n = r.length;",
     "    var r = DC._bereinigen(rows, null), n = r.length;", "fall_praefix"),
    ("JS: Matching-Präfix um einen Tag verschoben", SS, "    var d = Math.min(SE.tagNummer(asOf), 365);",
     "    var d = Math.min(SE.tagNummer(asOf), 365) - 1;", "fall_basis"),
    ("PY: B2 ohne Begrenzung", PY, "    b2 = _clip01((mittel + 3) / 6)", "    b2 = (mittel + 3) / 6", "fall_sprung"),
    ("PY: Rundung halb gerade (round)", PY, "    return math.floor(x * 10 + 0.5) / 10", "    return round(x, 1)", "rundung"),
    ("PY: Gewichtssumme 0 nicht abgefangen", PY, "    if not W > 0:\n        return aus(\"gewichte_null\", \"Gewichtssumme der Musterjahre 0\")", "", "fall_gewichte_null"),
    ("PY: Lückenprüfung im Fenster aus", PY, "            if tage[k] - tage[k - 1] > T:\n                return None",
     "            pass", "fall_klasse_krypto"),
    ("PY: späte Jahresanfänge zugelassen", PY, "        if int(ds[idx[0]][8:10]) > SPAETESTER_JAHRESSTART or int(ds[idx[0]][5:7]) != 1:\n            return None",
     "        pass", "fall_spaeter_start"),
    ("PY: interp365 mit anderer Formel", PY, "            out.append(values[pv] + w * (values[nv] - values[pv]))",
     "            out.append(values[pv] * (1 - w) + values[nv] * w)", "interp_exakt"),
]
UNGUELTIG = [
    ("Anker trifft nicht", SS, "DIESER TEXT STEHT NICHT IN DER DATEI", "x", "fall_basis"),
    ("Syntaxfehler (Probe muss abbrechen)", SS, "  berechne: function(rows, ticker, opts) {", "  berechne: function(rows, ticker, opts) {{", "fall_basis"),
]


def _kopie(tmp):
    for rel in (SC, DC, SS, PY, PROBE):
        (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / rel, tmp / rel)


def _bewerte(datei, alt, neu, soll):
    q = (REPO / datei).read_text(encoding="utf-8").replace("\r\n", "\n")
    if q.count(alt) != 1:
        return "ungueltig", "Anker trifft nicht"
    with tempfile.TemporaryDirectory() as t:
        tmp = pathlib.Path(t)
        _kopie(tmp)
        (tmp / datei).write_text(q.replace(alt, neu), encoding="utf-8")
        try:
            P = pruefen(tmp, SNAP_FUER_MUT)
        except Exception as e:  # noqa: BLE001
            return "ungueltig", f"Probe abgebrochen: {str(e)[:120]}"
    rot = [k for k, v in P.items() if v is not True]
    return ("gefangen" if soll in rot else "entwischt"), str(rot)


SNAP_FUER_MUT = None


def mutationen() -> int:
    ok = u = 0
    for name, datei, alt, neu, soll in MUTATIONEN:
        urteil, info = _bewerte(datei, alt, neu, soll)
        print(f"  {urteil.upper():9} {name} → {soll} {info if urteil != 'gefangen' else ''}")
        ok += urteil == "gefangen"
    for name, datei, alt, neu, soll in UNGUELTIG:
        urteil, info = _bewerte(datei, alt, neu, soll)
        print(f"  {'OK' if urteil == 'ungueltig' else 'FEHLER'}: als ungültig erkannt? {name} → {urteil} {info[:100]}")
        u += urteil == "ungueltig"
    print(f"{ok}/{len(MUTATIONEN)} Mutationen gefangen, {u}/{len(UNGUELTIG)} untaugliche richtig verworfen")
    return 0 if ok == len(MUTATIONEN) and u == len(UNGUELTIG) else 1


def main() -> int:
    global SNAP_FUER_MUT
    if not shutil.which("node"):
        print("DURCHGEFALLEN: node fehlt")
        return 1
    snap = pathlib.Path(sys.argv[sys.argv.index("--snapshot") + 1]) if "--snapshot" in sys.argv else None
    if "--mutationen" in sys.argv:
        SNAP_FUER_MUT = None      # Rundung hat einen eigenen deterministischen Test; ohne Snapshot ~10× schneller
        return mutationen()
    if snap is None and "--ohne-snapshot" not in sys.argv:
        print("UNGEPRÜFT: ohne --snapshot <ordner> fehlen die echten Reihen (bewusst: --ohne-snapshot)")
        return 1
    P = pruefen(REPO, snap)
    for k, v in P.items():
        if v is not True:
            print(f"  FEHLER {k}: {v}")
    n_ok = sum(v is True for v in P.values())
    print(f"verify_saison_score: {n_ok}/{len(P)} Prüfungen bestanden")
    return 0 if n_ok == len(P) else 1


if __name__ == "__main__":
    sys.exit(main())

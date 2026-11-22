"""Wächter für /event-chart (landing/pages/event-chart.html, landing/js/event-chart-compute.js,
landing/data/event_termine.json aus scripts/build_event_termine.py).

Prüft:
  A  Terminliste = Erzeugerausgabe (eine Handänderung oder ein vergessener Neubau wird rot), Form, Stichproben
     mit bekannten Terminen je Art, Verfall/Quartalsende an NYSE-Handelstagen
  B  Rechenkern (echte JS-Datei in node) gegen eine unabhängige Python-Referenz (numpy) auf Fällen mit
     Feiertagstermin, Doppeltermin auf demselben Anker, unvollständigem Fenster am Rand und Startgrenze
  C  echte Seite DE und gebaute EN in jsdom: keine Seitenfehler, kein Fehlerbanner, Hauptchart mit Terminlinien,
     Kennzahlen = Referenz, EZB bei ^GDAXI automatisch an, bei SPY nicht, EN ohne deutsche Texte
  --mutation  baut bekannte Fehler in den Rechenkern ein und verlangt, dass B jeden fängt

Aufruf: py -3.14 scripts/verify_event_chart.py [--mutation]      Exit 1 bei jedem Fehler
"""
from __future__ import annotations

import bisect
import json
import random
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

import numpy as np

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(WURZEL / "scripts"))

import build_event_termine as erzeuger  # noqa: E402
from shared import sitzungen  # noqa: E402

PROBE = WURZEL / "scripts" / "js" / "probe_event_chart.js"
COMPUTE = WURZEL / "landing" / "js" / "event-chart-compute.js"
fehler: list[str] = []
geprueft = 0


def pruefe(ok: bool, text: str) -> None:
    global geprueft
    geprueft += 1
    if not ok:
        fehler.append(text)


# ── A: Terminliste ──────────────────────────────────────────────────────────────────────────────────────────
def teil_a() -> None:
    datei = erzeuger.ZIEL.read_text(encoding="utf-8")
    pruefe(datei == erzeuger.inhalt(), "A event_termine.json weicht vom Erzeuger ab (scripts/build_event_termine.py ausführen)")
    t = json.loads(datei)["termine"]
    pruefe(t == sorted(t) and len({tuple(x) for x in t}) == len(t), "A Termine nicht sortiert oder doppelt")
    codes = {c for _, c in t}
    pruefe(codes == {"FOMC", "FOMCX", "EZB", "MIN", "JOBS", "TW", "OPEX", "Q", "VIX"}, f"A unerwartete Arten {sorted(codes)}")
    menge = {(d, c) for d, c in t}
    soll = {
        "OPEX": ["2025-08-15", "2022-04-14", "2026-11-20"], "TW": ["2024-06-21", "2025-03-21", "2026-06-18"],
        "Q": ["2022-12-30", "2023-09-29"], "VIX": ["2022-03-15", "2024-06-18", "2025-03-18", "2026-11-18"],
        "MIN": ["2020-04-08", "2023-11-21", "2025-12-30", "2026-11-18"], "JOBS": ["2025-01-10", "2025-07-03", "2025-11-20", "2025-12-16"],
        "FOMC": ["2025-12-10", "2026-12-09", "2008-12-16"], "FOMCX": ["2020-03-15", "2008-01-22"], "EZB": ["2015-01-22", "2025-12-18"],
    }
    for c, ds in soll.items():
        for d in ds:
            pruefe((d, c) in menge, f"A {c} {d} fehlt")
    pruefe(("2027-10-27", "FOMC") not in menge, "A Strategietreffen 27.10.2027 als FOMC geführt")
    pruefe(("2025-11-07", "JOBS") not in menge, "A entfallener Arbeitsmarktbericht 07.11.2025 geführt")
    pruefe(not any(c == "EZB" and d < "2015" for d, c in t), "A EZB-Termin vor 2015 ohne Beleg")
    for d, c in t:
        if c in ("OPEX", "TW", "Q", "VIX") and d <= "2026-12-31":
            pruefe(sitzungen.naechste(date.fromisoformat(d), "NYSE", einschliesslich=True) == date.fromisoformat(d),
                   f"A {c} {d} ist kein NYSE-Handelstag")


# ── B: Rechenkern gegen Referenz ────────────────────────────────────────────────────────────────────────────
def referenz(daten, schluss, termine, vor, nach, start):
    S = np.array(schluss, dtype=float)
    anker = []
    for d in sorted(set(termine)):
        if d < start:
            continue
        a = bisect.bisect_left(daten, d)
        if a >= len(daten) or a < vor or a + nach > len(daten) - 1 or a in anker:
            continue
        anker.append(a)
    basis = [a for a in range(vor, len(daten) - nach) if daten[a] >= start]
    def pf(liste):
        return np.array([[S[a + k] / S[a] * 100 for k in range(-vor, nach + 1)] for a in liste]) if liste else np.zeros((0, vor + nach + 1))
    P, B = pf(anker), pf(basis)
    out = {"n": len(anker), "nBasis": len(basis), "anker": anker}
    out["mittel"] = P.mean(axis=0).tolist() if len(P) else []
    out["basis"] = B.mean(axis=0).tolist() if len(B) else []
    for k, q in (("median", 50), ("q1", 25), ("q3", 75)):
        out[k] = np.percentile(P, q, axis=0).tolist() if len(P) else []
    return out


def reihe(seed, von, bis, frei):
    rnd = random.Random(seed)
    d, daten, schluss, c = date.fromisoformat(von), [], [], 100.0
    while d <= date.fromisoformat(bis):
        if d.weekday() < 5 and d.isoformat()[5:] not in frei:
            c *= 1 + rnd.gauss(0.0003, 0.012)
            daten.append(d.isoformat()); schluss.append(round(c, 4))
        d += timedelta(1)
    return daten, schluss


def faelle():
    daten, schluss = reihe(7, "2014-01-01", "2026-11-20", {"01-01", "12-25", "07-04"})
    termine = [daten[i] for i in range(40, len(daten) - 30, 37)]
    f = [
        {"name": "normal", "termine": termine, "opts": {"vor": 10, "nach": 20, "start": "2016-11-20"}},
        {"name": "feiertag", "termine": ["2018-12-25", "2019-07-04", "2020-01-01", "2021-12-25", "2022-07-04", "2023-12-25", "2024-07-04"] + termine[:3],
         "opts": {"vor": 5, "nach": 10, "start": "2014-01-01"}},
        {"name": "doppelt", "termine": termine[:20] + termine[:20] + ["2019-12-25", "2019-12-26"], "opts": {"vor": 20, "nach": 5, "start": "2014-01-01"}},
        {"name": "rand", "termine": [daten[3], daten[19], daten[20], daten[-21], daten[-20], daten[-1], "2030-01-01"] + termine[10:16],
         "opts": {"vor": 20, "nach": 20, "start": "2000-01-01"}},
        {"name": "start", "termine": termine, "opts": {"vor": 10, "nach": 60, "start": "2025-01-01"}},
        {"name": "zuwenig", "termine": termine[-2:], "opts": {"vor": 5, "nach": 5, "start": "2026-01-01"}},
    ]
    for x in f:
        x.update(daten=daten, schluss=schluss, bis="2027-12-31", idx=["2018-12-25", daten[0], "2027-12-31", "2030-01-01"])
    return f


def rechne_js(compute: Path, fs):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as h:
        json.dump(fs, h)
    r = subprocess.run(["node", str(PROBE), "rechne", str(compute), h.name], capture_output=True, text=True, encoding="utf-8")
    Path(h.name).unlink()
    if r.returncode != 0:
        return None, r.stderr[-400:]
    return json.loads(r.stdout), None


def vergleiche(js, fs) -> list[str]:
    abw = []
    for f, j in zip(fs, js):
        if "fehler" in j:
            abw.append(f"B {f['name']}: Absturz {j['fehler']}"); continue
        o = f["opts"]
        r = referenz(f["daten"], f["schluss"], f["termine"], o["vor"], o["nach"], o["start"])
        for k in ("n", "nBasis", "anker"):
            if j[k] != r[k]:
                abw.append(f"B {f['name']}: {k} {j[k] if k != 'anker' else len(j[k])} statt {r[k] if k != 'anker' else len(r[k])}")
        for k in ("mittel", "basis", "median", "q1", "q3"):
            a, b = j[k], r[k]
            if len(a) != len(b) or any(x is None or abs(x - y) > 1e-9 for x, y in zip(a, b)):
                abw.append(f"B {f['name']}: {k} weicht ab")
        if j["achseEnde"] != "2027-12-31" or j["idx"][1] != 0 or j["idx"][3] != -1:
            abw.append(f"B {f['name']}: Achse/idxAb falsch ({j['achseEnde']}, {j['idx']})")
        if j["idx"][0] != bisect.bisect_left(f["daten"], "2018-12-25"):
            abw.append(f"B {f['name']}: Feiertag nicht auf den nächsten Handelstag gelegt")
    return abw


def teil_b() -> None:
    fs = faelle()
    js, err = rechne_js(COMPUTE, fs)
    pruefe(js is not None, f"B node-Probe gescheitert: {err}")
    if js is None:
        return
    abw = vergleiche(js, fs)
    for a in abw:
        pruefe(False, a)
    pruefe(js[0]["n"] >= 20 and js[1]["n"] >= 5, "B Fälle zu schwach (zu wenige Termine)")
    pruefe(js[2]["n"] == len(set(fs[2]["termine"][:20])) + 1, f"B Fall „doppelt“: {js[2]['n']} Anker statt 21 (20 Termine + Feiertagspaar)")
    pruefe(js[5]["n"] < 5, "B Fall „zuwenig“ hat 5 oder mehr Termine")


MUTATIONEN = [
    ("Bezug Vortag", "S[a + k] / S[a] * 100", "S[a + k] / S[a - 1] * 100"),
    ("Fensterrand", "a + nach > letzter", "a + nach >= letzter"),
    ("keine Entdoppelung", "|| gesehen[a]) return;", ") return;"),
    ("Feiertag auf Vortag", "if (a[m] < iso) lo = m + 1; else hi = m;", "if (a[m] <= iso) lo = m + 1; else hi = m;"),
    ("Quantil Floor", "var p = (s.length - 1) * q, lo = Math.floor(p), hi = Math.ceil(p);", "var p = (s.length - 1) * q, lo = Math.floor(p), hi = lo;"),
    ("Startgrenze nur Termine", "if (daten[a] >= start) alle.push(a);", "alle.push(a);"),
    ("Achse ohne Zukunft", "while (bisIso && d < bisIso)", "while (false && d < bisIso)"),
]


def mutation() -> None:
    quelle = COMPUTE.read_text(encoding="utf-8")
    fs = faelle()
    with tempfile.TemporaryDirectory() as tmp:
        for name, alt, neu in MUTATIONEN:
            if quelle.count(alt) != 1:
                pruefe(False, f"M Anker trifft nicht: {name}"); continue
            m = Path(tmp) / "m.js"
            m.write_text(quelle.replace(alt, neu), encoding="utf-8")
            js, err = rechne_js(m, fs)
            gefangen = js is None or bool(vergleiche(js, fs))
            pruefe(gefangen, f"M Mutation nicht gefangen: {name}")
            sys.stdout.write(f"  Mutation {name}: {'gefangen' if gefangen else 'NICHT gefangen'}\n")


# ── C: echte Seite ──────────────────────────────────────────────────────────────────────────────────────────
def fixtures():
    out = {}
    for t, seed, frei in (("SPY", 3, {"01-01", "12-25", "07-04"}), ("^GDAXI", 5, {"01-01", "12-24", "12-25", "12-26", "12-31"})):
        daten, schluss = reihe(seed, "1999-01-04", "2026-11-20", frei)
        rnd = random.Random(seed + 100)
        z, vor = [], schluss[0]
        for d, c in zip(daten, schluss):
            o = round(vor * (1 + rnd.gauss(0, 0.003)), 4)
            z.append({"date": d, "open": o, "high": round(max(o, c) * 1.004, 4), "low": round(min(o, c) * 0.996, 4), "close": c})
            vor = c
        out[t] = z
    return out


def seite(sprache, ticker, fix_pfad, wurzel, wechsel=None):
    r = subprocess.run(["node", str(PROBE), "seite", str(wurzel), sprache, ticker, str(fix_pfad)] + ([wechsel] if wechsel else []),
                       capture_output=True, text=True, encoding="utf-8", timeout=120)
    if r.returncode != 0:
        return None, r.stderr[-500:]
    return json.loads(r.stdout), None


def zahl(text):
    m = re.search(r"([+−-])\s*([\d.,]+)", text)
    if not m:
        return None
    v = m.group(2)
    v = v.replace(".", "").replace(",", ".") if "," in v else v.replace(",", "")
    return (-1 if m.group(1) in "−-" else 1) * float(v)


def teil_c() -> None:
    en_datei = WURZEL / "landing" / "en" / "event-chart.html"
    if not en_datei.exists():
        r = subprocess.run([sys.executable, str(WURZEL / "landing" / "build_en.py"), "--write"], capture_output=True, text=True, encoding="utf-8")
        pruefe(en_datei.exists(), f"C EN-Seite nicht gebaut: {r.stderr[-300:]}")
    fx = fixtures()
    termine = json.loads(erzeuger.ZIEL.read_text(encoding="utf-8"))["termine"]
    with tempfile.TemporaryDirectory() as tmp:
        fp = Path(tmp) / "fix.json"
        fp.write_text(json.dumps(fx), encoding="utf-8")
        for sprache, ticker in (("de", "SPY"), ("de", "^GDAXI"), ("en", "^GDAXI")):
            o, err = seite(sprache, ticker, fp, WURZEL / "landing")
            pruefe(o is not None, f"C {sprache} {ticker}: Probe gescheitert {err}")
            if o is None:
                continue
            k = f"C {sprache} {ticker}:"
            pruefe(not o["fehler"], f"{k} Seitenfehler {o['fehler'][:2]}")
            pruefe(o["banner"] is None, f"{k} Fehlerbanner {o['banner']}")
            pruefe(o["titel"] == ticker, f"{k} Titel {o['titel']}")
            haupt = [c for c in o["charts"] if c["el"] == "ec-chart"]
            avg = [c for c in o["charts"] if c["el"] == "ec-avg"]
            pruefe(bool(haupt) and haupt[-1]["typ"] == "candlestick" and haupt[-1]["punkte"][0] > 200, f"{k} Hauptchart fehlt/keine Kerzen")
            pruefe(bool(haupt) and len(haupt[-1]["annotationen"]) >= 10, f"{k} zu wenige Terminlinien")
            pruefe(bool(avg) and avg[-1]["punkte"] == [31, 31, 31, 31], f"{k} Durchschnittschart nicht 4×31 Punkte")
            ezb = [x for x in o["liste"] if x["kz"] in ("EZB", "ECB")]
            pruefe(len(ezb) == 1 and ezb[0]["an"] == (ticker == "^GDAXI"), f"{k} EZB-Automatik falsch {ezb}")
            pruefe(len(o["liste"]) == 9, f"{k} Terminliste hat {len(o['liste'])} Einträge")
            pruefe(bool(o["naechste"]) and o["naechste"][0] > "2026-11-20", f"{k} nächste Termine falsch {o['naechste'][:2]}")
            # Kennzahlen gegen die Referenz (Standard: FOMC, 10 Jahre, 10 vor, 20 nach)
            z = fx[ticker]
            daten, schluss = [x["date"] for x in z], [x["close"] for x in z]
            r = referenz(daten, schluss, [d for d, c in termine if c == "FOMC"], 10, 20, "2016-11-20")
            werte = {kp[1]: kp[2] for kp in o["kpis"]}
            n_text = werte.get("Events" if sprache == "en" else "Termine")
            pruefe(n_text == str(r["n"]), f"{k} Termine {n_text} statt {r['n']}")
            schl = next((v for l, v in werte.items() if "20" in l and ("Ø" in l or "Mean" in l)), None)
            pruefe(schl is not None and abs(zahl(schl) - (r["mittel"][30] - 100)) < 0.006, f"{k} Ø nach 20 Tagen {schl} statt {r['mittel'][30] - 100:.4f}")
            pruefe(len(o["tabelle"]) == 4, f"{k} Tabelle hat {len(o['tabelle'])} Zeilen")
            if sprache == "en":
                for wort in ("Durchschnittsverlauf", "Termine", "Arbeitsmarktbericht", "Zinsentscheid", "Nächste"):
                    pruefe(wort not in o["seiteText"] and wort not in (o["avgTitel"] or ""), f"{k} deutscher Text „{wort}“")
                pruefe(any(x["name"] == "ECB rate decision" for x in o["liste"]), f"{k} Liste nicht englisch")
            else:
                pruefe("Durchschnittsverlauf ^GDAXI" in (o["avgTitel"] or "") or ticker != "^GDAXI", f"{k} Titel Durchschnittsverlauf {o['avgTitel']}")


def teil_c_wechsel() -> None:
    """EZB-Automatik ist nicht klebrig: ^GDAXI → SPY schaltet die EZB wieder aus (gespeicherte Auswahl ohne EZB)."""
    with tempfile.TemporaryDirectory() as tmp:
        fp = Path(tmp) / "fix.json"
        fp.write_text(json.dumps(fixtures()), encoding="utf-8")
        o, err = seite("de", "^GDAXI", fp, WURZEL / "landing", "SPY")
        pruefe(o is not None, f"C Wechsel: Probe gescheitert {err}")
        if o is None:
            return
        ezb = [x for x in o["liste"] if x["kz"] == "EZB"]
        pruefe(o["titel"] == "SPY", f"C Wechsel: Titel {o['titel']}")
        pruefe(not o["fehler"] and o["banner"] is None, f"C Wechsel: Fehler {o['fehler'][:1]} {o['banner']}")
        pruefe(len(ezb) == 1 and not ezb[0]["an"], f"C Wechsel ^GDAXI → SPY: EZB bleibt an {ezb}")


def main() -> int:
    if shutil.which("node") is None:
        sys.stderr.write("node fehlt — der Wächter braucht node\n")
        return 1
    teil_a()
    teil_b()
    teil_c()
    teil_c_wechsel()
    if "--mutation" in sys.argv:
        mutation()
    for f in fehler:
        sys.stdout.write("FEHLER " + f + "\n")
    sys.stdout.write(f"verify_event_chart: {geprueft} Prüfungen, {len(fehler)} Fehler\n")
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())

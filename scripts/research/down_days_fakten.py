#!/usr/bin/env python3
"""
down_days_fakten.py — Faktenblatt für den Blogartikel „Down-Days im SPY“, gerechnet aus dem
eingefrorenen Datenstand blog/daten/spy_2026-10-29.json.

    py -3.14 scripts/research/down_days_fakten.py            # druckt das Faktenblatt (JSON)

Plan (vor dem Lauf festgelegt, Codex-Auflagen eingearbeitet): docs/review_prompts/2026-10-30_down_days_midterm_plan_v2.md.
Rein beschreibend, kein Signifikanztest. Jede Zahl, die der Artikel nennt, kommt von hier;
scripts/verify_downdays_midterm_blog.py rechnet dieselbe Funktion nach und prüft den sichtbaren Text dagegen.

Renditebasis: gespeicherter log_return aus adjustierten Schlusskursen (Gesamtrendite-Näherung). Vorwärtsrendite
F_h(t) = Schluss des Ereignistags bis Schluss der h-ten Folgesitzung — eine Beschreibung, keine Ausführungsannahme.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import statistics as S
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
DATEI = REPO / "blog" / "daten" / "spy_2026-10-29.json"
SHA256 = "00b4d0c8d3d4bccf1e0bdbd8cb2eedca4030028d166ecc2d83a5b37a7ada9917"

VON, BIS = "2006-10-30", "2026-10-29"
STUFEN = (-0.01, -0.02, -0.03, -0.04)
HORIZONTE = (15, 30, 50)
PFAD_STUFE, PFAD_H, RISIKO_H = -0.02, 50, 15
KRISEN = (("2008-09-01", "2009-06-30"), ("2020-02-15", "2020-06-30"))
HAELFTEN = (("2006-10-30", "2016-10-28"), ("2016-10-31", "2026-10-29"))


def lade(datei=DATEI, pruefen=True) -> dict:
    roh = datei.read_bytes()
    if pruefen and hashlib.sha256(roh).hexdigest() != SHA256:
        raise SystemExit(f"{datei}: Prüfsumme weicht ab — der eingefrorene Datenstand wurde verändert")
    return json.loads(roh.decode("utf-8"))


def quantil(v, q):
    """Lineare Interpolation wie numpy (Methode 'linear')."""
    s = sorted(v)
    pos = (len(s) - 1) * q
    lo = math.floor(pos)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def ausduennen(idx, h):
    """Chronologisch ausgedünnt: ein Ereignis zählt, wenn seit dem letzten GEZÄHLTEN mindestens h Sitzungen
    liegen — die Vorwärtsfenster überlappen dann nicht. Ändert die Zielgröße (bevorzugt frühe Ereignisse einer
    Häufung) und macht die Fälle nicht unabhängig (gemeinsame Regime bleiben)."""
    aus, letzt = [], None
    for i in idx:
        if letzt is None or i - letzt >= h:
            aus.append(i)
            letzt = i
    return aus


def kennzahlen(werte):
    return {"n": len(werte), "mittel": 100 * S.mean(werte), "median": 100 * S.median(werte),
            "n_positiv": sum(w > 0 for w in werte), "trefferquote": sum(w > 0 for w in werte) / len(werte),
            "p10": 100 * quantil(werte, 0.10), "p90": 100 * quantil(werte, 0.90),
            "schlechtester": 100 * min(werte), "bester": 100 * max(werte)}


class Reihe:
    def __init__(self, daten: dict):
        z = daten["zeilen"]
        self.datum = [r[0] for r in z]
        lr = [r[2] for r in z]
        if lr[0] is None:
            lr[0] = 0.0                       # erste Zeile hat keine Vorzeile; liegt vor VON, nie Ereignis
        if any(x is None for x in lr):
            raise SystemExit("log_return fehlt innerhalb der Reihe")
        self.kum = [0.0]
        for x in lr:
            self.kum.append(self.kum[-1] + x)  # kum[i+1] = Σ lr[0..i]
        self.r = [math.exp(x) - 1 for x in lr]
        self.letzt = len(z) - 1
        self.zeit = [i for i, d in enumerate(self.datum) if VON <= d <= BIS]

    def F(self, i, h):
        """Rendite vom Schluss i bis Schluss i+h."""
        return math.exp(self.kum[i + h + 1] - self.kum[i + 1]) - 1

    def fenster_frei(self, i, h, bloecke):
        """Weder der Ereignistag noch eine Folgesitzung des Fensters liegt in einem Block."""
        return not any(a <= self.datum[k] <= b for a, b in bloecke for k in range(i, i + h + 1))

    def in_haelfte(self, i, h, haelfte):
        a, b = haelfte
        return a <= self.datum[i] and self.datum[i + h] <= b


def fakten(daten: dict) -> dict:
    R = Reihe(daten)
    zeit, r = R.zeit, R.r
    jahre = {}
    for i in zeit:
        j = jahre.setdefault(R.datum[i][:4], {"sitzungen": 0})
        j["sitzungen"] += 1
    aus = {"datenstand": daten["letzte_sitzung"], "zeitraum": [R.datum[zeit[0]], R.datum[zeit[-1]]],
           "sitzungen": len(zeit), "down_days": sum(r[i] < 0 for i in zeit), "stufen": {}, "basis": {}}
    aus["down_quote"] = aus["down_days"] / aus["sitzungen"]

    def gruppe(idx, h):
        return kennzahlen([R.F(i, h) for i in idx]) if idx else None

    basis_idx = {}
    for h in HORIZONTE:
        voll = [i for i in zeit if i + h <= R.letzt]
        basis_idx[h] = voll
        aus["basis"][str(h)] = {
            "alle": gruppe(voll, h),
            "ohne_krisen": gruppe([i for i in voll if R.fenster_frei(i, h, KRISEN)], h),
            "erste_haelfte": gruppe([i for i in voll if R.in_haelfte(i, h, HAELFTEN[0])], h),
            "zweite_haelfte": gruppe([i for i in voll if R.in_haelfte(i, h, HAELFTEN[1])], h)}

    for s in STUFEN:
        schl = f"{round(-100 * s)}"
        ev = [i for i in zeit if r[i] <= s]
        st = {"n_gesamt": len(ev), "quote": len(ev) / len(zeit), "je_jahr": {}, "h": {}}
        for i in ev:
            st["je_jahr"][R.datum[i][:4]] = st["je_jahr"].get(R.datum[i][:4], 0) + 1
        st["je_jahr_quote"] = {j: st["je_jahr"].get(j, 0) / v["sitzungen"] for j, v in jahre.items()}
        st["jahre_mit_ereignis"] = len(st["je_jahr"])
        for h in HORIZONTE:
            voll = [i for i in ev if i + h <= R.letzt]
            hh = {"unvollstaendig": len(ev) - len(voll)}
            if voll:
                hh["alle"] = gruppe(voll, h)
                hh["alle"]["ueberrendite"] = hh["alle"]["mittel"] - aus["basis"][str(h)]["alle"]["mittel"]
                aus_d = ausduennen(voll, h)
                hh["ausgeduennt"] = gruppe(aus_d, h)
                hh["ausgeduennt"]["ueberrendite"] = hh["ausgeduennt"]["mittel"] - aus["basis"][str(h)]["alle"]["mittel"]
                for name, filt in (("ohne_krisen", lambda i: R.fenster_frei(i, h, KRISEN)),
                                   ("erste_haelfte", lambda i: R.in_haelfte(i, h, HAELFTEN[0])),
                                   ("zweite_haelfte", lambda i: R.in_haelfte(i, h, HAELFTEN[1]))):
                    teil = [i for i in voll if filt(i)]
                    g = gruppe(teil, h)
                    if g:
                        g["ueberrendite"] = g["mittel"] - aus["basis"][str(h)][name]["mittel"]
                        g["ausgeduennt_n"] = len(ausduennen(teil, h))
                    hh[name] = g
            st["h"][str(h)] = hh
        # größter zwischenzeitlicher Verlust gegenüber dem Ereignisschluss (Schlusskurse), min(0, F1 … F15)
        rv = [i for i in ev if i + RISIKO_H <= R.letzt]
        risiko = [100 * min(0.0, min(R.F(i, k) for k in range(1, RISIKO_H + 1))) for i in rv]
        st["risiko15"] = {"n": len(risiko), "mittel": S.mean(risiko), "median": S.median(risiko),
                          "p10": quantil(risiko, 0.10), "schlechtester": min(risiko)}
        aus["stufen"][schl] = st

    bi = [i for i in zeit if i + RISIKO_H <= R.letzt]
    rb = [100 * min(0.0, min(R.F(i, k) for k in range(1, RISIKO_H + 1))) for i in bi]
    aus["basis_risiko15"] = {"n": len(rb), "mittel": S.mean(rb), "median": S.median(rb),
                             "p10": quantil(rb, 0.10), "schlechtester": min(rb)}

    # Pfad 0 … 50: dieselbe Kohorte für jeden Offset (nur Ereignisse/Basistage mit vollständigem 50er-Fenster)
    pe = [i for i in zeit if r[i] <= PFAD_STUFE and i + PFAD_H <= R.letzt]
    pb = [i for i in zeit if i + PFAD_H <= R.letzt]
    aus["pfad"] = {"stufe": f"{round(-100 * PFAD_STUFE)}", "n_ereignisse": len(pe), "n_basis": len(pb),
                   "ereignis_mittel": [100 * S.mean(R.F(i, k) for i in pe) for k in range(PFAD_H + 1)],
                   "ereignis_median": [100 * S.median(R.F(i, k) for i in pe) for k in range(PFAD_H + 1)],
                   "basis_mittel": [100 * S.mean(R.F(i, k) for i in pb) for k in range(PFAD_H + 1)]}
    return aus


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    f = fakten(lade())
    print(json.dumps(f, indent=1, ensure_ascii=False))

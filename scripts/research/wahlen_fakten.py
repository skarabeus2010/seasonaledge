#!/usr/bin/env python3
"""
wahlen_fakten.py — Faktenblatt für Blogartikel zur Wahlstudie, gerechnet aus einem Snapshot.

    py -3.14 scripts/research/wahlen_fakten.py landing/data/wahlen_snapshots/midterm-2026-10.json

Jede Zahl, die ein Artikel nennt, kommt von hier; scripts/verify_wahlen_blog.py rechnet dieselbe
Funktion nach und prüft, dass die Werte im Text stehen. Rechenkern: shared.elections.aggregiere
(derselbe, gegen den die Seite /wahlen geprüft wird). Vorlauf-Vergleich mit den Jahren ohne Wahl
nach derselben Tripel-Regel (nur Wahlen mit beiden Kontrolljahren).
"""
from __future__ import annotations

import json
import pathlib
import statistics as S
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))
from shared import elections as el  # noqa: E402


def _stueck(p, n, x, y):
    if not p:
        return None
    w = p["c"][n - x: n + y + 1]
    return None if any(v is None for v in w) else w


def gepaart(st: dict, reihe: str, typ: str, x: int, y: int, ab_jahr=None) -> dict:
    """Gepaarter Vergleich auf den vollständigen Tripeln (Wahljahr + beide Kontrolljahre): Vorlauf t−X→t0 und
    Nachlauf t0→t+Y, jeweils Wahl gegen Mittel der Kontrollen. Der Nachlauf-Abstand muss gleich
    aggregiere()['differenz_mittel'] sein; das Wahlmittel weicht vom Gesamtmittel über ALLE Wahlen ab (Codex-Blog R1)."""
    n = st["fenster"]
    vw, vr, nw, nr = [], [], [], []
    for w in st["wahlen"]:
        if w["type"] != typ or w["status"] != "held" or (ab_jahr and int(w["date"][:4]) < ab_jahr):
            continue
        r = w["reihen"][reihe]
        s = _stueck(r.get("pfad"), n, x, y)
        ks = [_stueck(k.get("pfad"), n, x, y) for k in r.get("kontrollen", [])]
        if s and len(ks) == 2 and all(ks):
            vw.append(100 * (s[x] / s[0] - 1))
            vr.append(sum(100 * (k[x] / k[0] - 1) for k in ks) / 2)
            nw.append(100 * (s[-1] / s[x] - 1))
            nr.append(sum(100 * (k[-1] / k[x] - 1) for k in ks) / 2)
    return {"n_tripel": len(vw),
            "vorlauf_wahl": S.mean(vw), "vorlauf_ohne_wahl": S.mean(vr),
            "vorlauf_differenz": S.mean([a - b for a, b in zip(vw, vr)]), "vorlauf_wahl_positiv": sum(v > 0 for v in vw),
            "nachlauf_wahl": S.mean(nw), "nachlauf_ohne_wahl": S.mean(nr),
            "nachlauf_differenz": S.mean([a - b for a, b in zip(nw, nr)])}


def _ans(st, name):
    a = st["weitere_ansichten"][name]["ansicht"]
    return a["reihe"], a["typ"], a["x"], a["y"]


def fakten(st: dict) -> dict:
    a = st["ansicht"]
    haupt = el.aggregiere(st, a["reihe"], a["typ"], a["x"], a["y"], a["basis"])
    k = haupt["kennzahlen"]
    ein = sorted(haupt["einzel"], key=lambda e: e["id"])
    bester = max(ein, key=lambda e: e["nachlauf"])
    schlechtester = min(ein, key=lambda e: e["nachlauf"])
    ab71 = el.aggregiere(st, a["reihe"], a["typ"], a["x"], a["y"], a["basis"], ab_jahr=1971)["kennzahlen"]
    wechsel = {w: el.aggregiere(st, a["reihe"], a["typ"], a["x"], a["y"], a["basis"], wechsel=w)["kennzahlen"]
               for w in ("ja", "nein")}
    live_a = st["weitere_ansichten"]["live"]["ansicht"]
    lv = el.aggregiere(st, live_a["reihe"], live_a["typ"], live_a["x"], live_a["y"], live_a["basis"])
    gefuellt = [(i - live_a["x"], v) for i, v in enumerate(lv["live"]["kurve"]) if v is not None]
    letzt_off, letzt_wert = gefuellt[-1]
    idx = letzt_off + live_a["x"]
    return {
        "snapshot_id": st["snapshot_id"], "kursdatenstand": st["kursdatenstand"][a["reihe"]],
        "haupt": {**{key: k[key] for key in ("n", "nachlauf_mittel", "nachlauf_median", "trefferquote", "n_tripel",
                                            "referenz_nachlauf_mittel", "differenz_mittel")},
                  "n_positiv": sum(e["nachlauf"] > 0 for e in ein),
                  "p25_ende": haupt["kurven"]["p25"][-1] - 100, "p75_ende": haupt["kurven"]["p75"][-1] - 100,
                  "ausgeschlossen": haupt["ausgeschlossen"],
                  "n_kalender_ungeprueft": sum(not e["kalenderBelegt"] for e in ein)},
        "gepaart": gepaart(st, a["reihe"], a["typ"], a["x"], a["y"]),
        "gepaart_ab_1971": gepaart(st, a["reihe"], a["typ"], a["x"], a["y"], ab_jahr=1971),
        "gepaart_praesident": gepaart(st, *_ans(st, "praesident")),
        "gepaart_dow": gepaart(st, *_ans(st, "dow")),
        "ab_1971": {key: ab71[key] for key in ("n", "nachlauf_mittel", "nachlauf_median", "trefferquote",
                                               "referenz_nachlauf_mittel", "differenz_mittel", "n_tripel")},
        "extreme": {"bester": [bester["t0"][:4], bester["nachlauf"]],
                    "schlechtester": [schlechtester["t0"][:4], schlechtester["nachlauf"]]},
        "je_midterm": [[e["t0"][:4], e["vorlauf"], e["nachlauf"]] for e in ein],
        "house_wechsel": {w: {"n": v["n"], "nachlauf_mittel": v["nachlauf_mittel"], "trefferquote": v["trefferquote"]}
                          for w, v in wechsel.items()},
        "praesident": st["weitere_ansichten"]["praesident"]["kennzahlen"],
        "dow": st["weitere_ansichten"]["dow"]["kennzahlen"],
        "live": {"wahltag": lv["live"]["date"], "t0": lv["live"]["t0"], "basis_datum": lv["live"]["basisDatum"],
                 "letzter_kurs": lv["live"]["letzter_kurs"], "letzter_offset": letzt_off,
                 "seit_basis": letzt_wert - 100, "mittel_selber_offset": lv["kurven"]["mittel"][idx] - 100,
                 "p25_selber_offset": lv["kurven"]["p25"][idx] - 100, "p75_selber_offset": lv["kurven"]["p75"][idx] - 100},
    }


if __name__ == "__main__":
    st = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(json.dumps(fakten(st), ensure_ascii=False, indent=1, default=float))

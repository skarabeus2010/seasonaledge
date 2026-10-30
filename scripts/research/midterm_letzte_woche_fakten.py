#!/usr/bin/env python3
"""
midterm_letzte_woche_fakten.py — Faktenblatt für den Blogartikel „S&P 500 in der letzten Woche vor der
Midterm-Wahl“, gerechnet aus dem eingefrorenen Snapshot midterm-2026-10 (derselbe Stand wie der Artikel
midterm-wahltag-boerse).

    py -3.14 scripts/research/midterm_letzte_woche_fakten.py

Plan: docs/review_prompts/2026-10-30_down_days_midterm_plan_v2.md. Pfade, Gültigkeit und Vergleichsjahre
kommen unverändert aus dem Snapshot; gerechnet wird über shared.elections.intervall_rendite.
  Woche   = t−5 → t0: fünf Sitzungsrenditen bis zum Referenzschluss t0 (letzter Schluss am/vor dem Wahltag).
  Tag j   = t(j−1) → t(j), j = −4 … +1 (t+1 = erster Schluss nach der Wahlnacht, nur als Kontext).
Eine Wahl zählt nur, wenn alle Kurse t−5 … t+1 gültig sind (eine Kohorte für Woche UND Tage). Ein
Vergleichstripel zählt nur, wenn beide Vergleichsjahre ebenfalls vollständig sind. Indexkursrenditen.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import statistics as S
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
from shared.elections import intervall_rendite  # noqa: E402

SNAPSHOT = REPO / "landing" / "data" / "wahlen_snapshots" / "midterm-2026-10.json"
SHA256 = "a875d265e4d6853a72cc7a2b5daf6b66aecfacb200f4fc1a190e500727379586"
REIHE = "^GSPC"
TAGE = (-4, -3, -2, -1, 0, 1)


def lade(datei=SNAPSHOT, pruefen=True) -> dict:
    roh = datei.read_bytes()
    if pruefen and hashlib.sha256(roh).hexdigest() != SHA256:
        raise SystemExit(f"{datei}: Prüfsumme weicht ab — der eingefrorene Snapshot wurde verändert")
    return json.loads(roh.decode("utf-8"))


def _werte(p, n):
    """{'woche': …, 'tage': {j: …}} oder None, wenn ein Kurs t−5 … t+1 fehlt."""
    woche = intervall_rendite(p, -5, 0, n)
    tage = {j: intervall_rendite(p, j - 1, j, n) for j in TAGE}
    if woche is None or any(v is None for v in tage.values()):
        return None
    return {"woche": woche, "tage": tage}


def _kz(werte, jahre=None):
    k = {"n": len(werte), "mittel": S.mean(werte), "median": S.median(werte),
         "n_positiv": sum(v > 0 for v in werte)}
    k["trefferquote"] = k["n_positiv"] / len(werte)
    if jahre:
        i_max = max(range(len(werte)), key=werte.__getitem__)
        i_min = min(range(len(werte)), key=werte.__getitem__)
        k["bester"] = [jahre[i_max], werte[i_max]]
        k["schlechtester"] = [jahre[i_min], werte[i_min]]
    return k


def auswertung(st: dict, ab_jahr=None) -> dict:
    n = st["fenster"]
    jahre, woche, tage = [], [], {j: [] for j in TAGE}
    tripel, pw, pk, ptage, ktage = [], [], [], {j: [] for j in TAGE}, {j: [] for j in TAGE}
    t0_wahltag = 0
    offen_tag = []                       # Sitzungsrendite t0, nur wenn t0 der Wahltag selbst ist (Börse geöffnet)
    for w in st["wahlen"]:
        if w["type"] != "midterm" or w["status"] != "held":
            continue                                            # 2026 (scheduled) bleibt draußen
        jahr = int(w["date"][:4])
        if ab_jahr and jahr < ab_jahr:
            continue
        r = w["reihen"][REIHE]
        v = _werte(r.get("pfad"), n)
        if not v:
            continue
        jahre.append(jahr)
        if r["pfad"]["t0"] == w["date"]:
            t0_wahltag += 1
            offen_tag.append(v["tage"][0])
        woche.append(v["woche"])
        for j in TAGE:
            tage[j].append(v["tage"][j])
        kv = [_werte(k.get("pfad"), n) for k in r.get("kontrollen", [])]
        if len(kv) == 2 and all(kv):
            tripel.append([jahr] + [k["jahr"] for k in r["kontrollen"]])
            pw.append(v["woche"])
            pk.append(sum(k["woche"] for k in kv) / 2)
            for j in TAGE:
                ktage[j].append(sum(k["tage"][j] for k in kv) / 2)
                ptage[j].append(v["tage"][j] - ktage[j][-1])
    d = [a - b for a, b in zip(pw, pk)]
    return {"jahre": jahre, "t0_am_wahltag": t0_wahltag, "wahltag_offen": _kz(offen_tag) if offen_tag else None,
            "woche": _kz(woche, jahre), "tage": {str(j): _kz(v) for j, v in tage.items()},
            "wochen_werte": dict(zip(map(str, jahre), woche)),
            "gepaart": {"n_tripel": len(d), "tripel": tripel, "woche_wahl": S.mean(pw),
                        "woche_ohne_wahl": S.mean(pk), "woche_differenz": S.mean(d),
                        "differenz_positiv": sum(x > 0 for x in d),
                        "tage_differenz": {str(j): S.mean(v) for j, v in ptage.items()},
                        "tage_ohne_wahl": {str(j): S.mean(v) for j, v in ktage.items()}}}


def fakten(st: dict) -> dict:
    from wahlen_fakten import gepaart                    # Bezug: Vorlauf t−20 → t0 aus dem ±20-Artikel
    v20 = gepaart(st, REIHE, "midterm", 20, 20)
    return {"snapshot": st["snapshot_id"], "kursdatenstand": st["kursdatenstand"][REIHE],
            "alle": auswertung(st), "ab_1971": auswertung(st, 1971),
            "vorlauf20": {"n_tripel": v20["n_tripel"], "differenz": v20["vorlauf_differenz"]}}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(fakten(lade()), indent=1, ensure_ascii=False))

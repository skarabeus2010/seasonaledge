#!/usr/bin/env python3
"""
skew_rang.py — Rang und Percentile der Skew-Kennzahlen je Ticker, EINMAL im Options-Cron gerechnet.

WARUM (Plan docs/review_prompts/2026-10-14_options_sofortreparaturen_plan_v3.md, B3, Codex-Freigabe): /skew rechnete
Rang/Percentile im Browser, die Morgen-Mail anders in Python — die Mail nahm alle Zeilen (auch nicht normierte), ein
Fenster ab der Uhr statt ab der Session und rückte bei fehlendem heutigen Wert ältere Tage nach. Jetzt eine Rechnung;
/skew und Mail lesen nur `rang` aus options_skew.json.

Vertrag je Ticker, Session S, Fenster W ∈ FENSTER (Kalendertage):
  * Zeilen: S − W ≤ date ≤ S, cm_mode ∈ {cm, cm_extrap}, nach Datum sortiert. Datum nur als gültiges Kalenderdatum
    `YYYY-MM-DD` (kein Zeitstempel, kein „2026-08-99“); andere Werte zählen nicht und werden gemeldet.
  * Doppelte Daten unter den normierten Zeilen bis S → der GANZE Ticker bekommt keinen Rang (in keinem Fenster) und wird
    gemeldet (der Cron dedupliziert, also ist es ein Defekt).
  * Metriken: rr = call_iv − put_iv, iv = (put_iv + call_iv)/2, skew = skew_pts,
    Zeta-Paar cz/pz = call_zeta_pts/put_zeta_pts, sonst (call_iv − iv_atm)·100 bzw. (put_iv − iv_atm)·100.
  * Je Metrik eigenes n: erst gültige Werte (endliche Zahl, kein bool) filtern, dann muss der letzte gültige Wert das
    Datum S haben (kein Nachrücken älterer Tage), dann n ≥ MIN_NORM. Zeta nur als Paar (beide gültig).
  * Rank = round((x_S − min)/(max − min)·100), max = min → 50; Percentile = round(#{x_i < x_S, i vor S}/(n − 1)·100);
    round = halb nach oben (floor(v + 0.5)) wie JS-Math.round.
Ausgabe: {metrik: {n, rank, pctl, wert}} bzw. zeta: {n, cz: {rank, pctl, wert}, pz: {…}}; fehlende Metrik → Schlüssel fehlt.
Die unabhängige JS-Referenz für den Zwillingstest steht in scripts/js/skew_rang_ref.js.
"""
from __future__ import annotations

import math
from datetime import date, timedelta

FENSTER = (92, 183, 365)
MIN_NORM = 20
NORMIERT = ("cm", "cm_extrap")


def gueltig(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def runde(v: float) -> int:
    """Halb nach oben wie JS-Math.round (Python-round rundet 0,5 zur geraden Zahl)."""
    return int(math.floor(v + 0.5))


def _rank(werte: list) -> int:
    letzt, lo, hi = werte[-1], min(werte), max(werte)
    return 50 if hi == lo else runde((letzt - lo) / (hi - lo) * 100)


def _pctl(werte: list) -> int:
    letzt = werte[-1]
    unter = sum(1 for x in werte[:-1] if x < letzt)
    return runde(unter / (len(werte) - 1) * 100)


def _diff(a, b, faktor=1.0):
    return (a - b) * faktor if gueltig(a) and gueltig(b) else None


def datum_gueltig(d) -> bool:
    """Genau `YYYY-MM-DD` und ein echtes Kalenderdatum."""
    if not isinstance(d, str) or len(d) != 10 or d[4] != "-" or d[7] != "-":
        return False
    try:
        return date.fromisoformat(d).isoformat() == d
    except ValueError:
        return False


def _normiert(arr: list, session: str) -> list:
    return [e for e in arr or [] if isinstance(e, dict) and datum_gueltig(e.get("date"))
            and e.get("cm_mode") in NORMIERT and e["date"] <= session]


def pruefe_ticker(arr: list, session: str) -> list[str]:
    """Defekte, die den Rang eines Tickers verhindern oder Zeilen ausschließen (für die Meldung im Cron)."""
    meld = []
    daten = [e["date"] for e in _normiert(arr, session)]
    doppelt = sorted({d for d in daten if daten.count(d) > 1})
    if doppelt:
        meld.append("doppelte Daten: " + ", ".join(doppelt[:5]))
    falsch = [e.get("date") for e in arr or [] if isinstance(e, dict) and e.get("cm_mode") in NORMIERT
              and not datum_gueltig(e.get("date"))]
    if falsch:
        meld.append(f"{len(falsch)} Zeile(n) mit ungültigem Datum, z. B. {falsch[0]!r}")
    return meld


def _werte(e: dict) -> dict:
    ci, pi, atm = e.get("call_iv"), e.get("put_iv"), e.get("iv_atm")
    cz = e.get("call_zeta_pts") if gueltig(e.get("call_zeta_pts")) else _diff(ci, atm, 100.0)
    pz = e.get("put_zeta_pts") if gueltig(e.get("put_zeta_pts")) else _diff(pi, atm, 100.0)
    return {"rr": _diff(ci, pi), "iv": (ci + pi) / 2 if gueltig(ci) and gueltig(pi) else None,
            "skew": e.get("skew_pts"), "cz": cz, "pz": pz}


def _einzeln(reihe: list) -> dict | None:
    """reihe = [(datum, wert)] aufsteigend, nur gültige Werte; letzter muss die Session sein (vom Aufrufer geprüft)."""
    werte = [w for _, w in reihe]
    return {"n": len(werte), "rank": _rank(werte), "pctl": _pctl(werte), "wert": werte[-1]}


def rang_ticker(arr: list, session: str, fenster: int) -> dict | None:
    """Rang je Metrik für EIN Fenster. None bei doppelten Daten; {} wenn keine Metrik die Bedingungen erfüllt."""
    ab = (date.fromisoformat(session) - timedelta(days=fenster)).isoformat()
    alle = _normiert(arr, session)
    if len({e["date"] for e in alle}) != len(alle):
        return None
    zeilen = sorted((e for e in alle if ab <= e["date"]), key=lambda e: e["date"])
    daten = [e["date"] for e in zeilen]
    w = [(d, _werte(e)) for d, e in zip(daten, zeilen)]
    aus = {}
    for m in ("rr", "iv", "skew"):
        reihe = [(d, v[m]) for d, v in w if gueltig(v[m])]
        if reihe and reihe[-1][0] == session and len(reihe) >= MIN_NORM:
            aus[m] = _einzeln(reihe)
    paare = [(d, v["cz"], v["pz"]) for d, v in w if gueltig(v["cz"]) and gueltig(v["pz"])]
    if paare and paare[-1][0] == session and len(paare) >= MIN_NORM:
        cz, pz = _einzeln([(d, c) for d, c, _ in paare]), _einzeln([(d, p) for d, _, p in paare])
        aus["zeta"] = {"n": len(paare), "cz": {k: cz[k] for k in ("rank", "pctl", "wert")},
                       "pz": {k: pz[k] for k in ("rank", "pctl", "wert")}}
    return aus


def rang_gesamt(hist: dict, session: str, meldungen: list | None = None) -> dict:
    """{ticker: {"92": {...}, "183": {...}, "365": {...}}} — leere Fenster und Ticker fehlen. `meldungen` (Liste)
    bekommt je Ticker mit Defekt einen Eintrag „TICKER: …“."""
    out = {}
    for t, arr in (hist or {}).items():
        if t.startswith("__") or not isinstance(arr, list):
            continue
        if meldungen is not None:
            meldungen.extend(f"{t}: {m}" for m in pruefe_ticker(arr, session))
        je = {}
        for f in FENSTER:
            r = rang_ticker(arr, session, f)
            if r:
                je[str(f)] = r
        if je:
            out[t] = je
    return out

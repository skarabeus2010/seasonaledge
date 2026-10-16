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

B3b (Plan docs/review_prompts/2026-10-16_options_b3b_plan_v2.md, Codex-Freigabe R2):
  * Metrik ivrv = iv_atm / rv_1m (`ivrv_wert`): nur Zeilen mit GESPEICHERTEM rv_1m (Live-Zeilen ab 16.10.), keine
    Rückrechnung aus vrp_pts. iv_atm > 0, rv_1m ≥ 0,01.
  * Je Metrik zusätzlich (rr, iv, skew, ivrv): `neu_rand` = "hoch"/"tief", wenn x_S strikt über max bzw. unter min der
    Vorwerte liegt (Gleichstand ist kein Rand); `vorher_datum` = Datum des letzten gültigen Werts vor S;
    `sprung` = true, wenn |x_S − x_vorher| > SPRUNG_FAKTOR · Median(|d|) über alle Änderungen zwischen
    aufeinanderfolgenden gültigen Beobachtungen des Fensters EINSCHLIESSLICH der aktuellen (n ≥ 20 ⇒ ≥ 19
    Änderungen); Median 0 → `sprung_beurteilbar: false`. Nur ein Hinweis, keine kalibrierte Ausreißererkennung.
  * `rang_status_gesamt`: je Ticker/Fenster/Metrik ohne Rang {n, status ∈ zu_kurz | kein_wert}, bei Duplikaten
    {"*": {"status": "gesperrt"}}. `rang` selbst bleibt unverändert vollständig (Leser von B3a unberührt).
Die unabhängige JS-Referenz für den Zwillingstest steht in scripts/js/skew_rang_ref.js.
"""
from __future__ import annotations

import math
from datetime import date, timedelta

FENSTER = (92, 183, 365)
MIN_NORM = 20
SPRUNG_FAKTOR = 5.0
RV_MIN = 0.01
METRIKEN = ("rr", "iv", "skew", "ivrv")
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


def ivrv_wert(iv_atm, rv_1m):
    """IV/RV-Verhältnis (ATM-IV 30 Kalendertage / realisierte Vola 21 Handelstage) oder None."""
    if not (gueltig(iv_atm) and gueltig(rv_1m)) or iv_atm <= 0 or rv_1m < RV_MIN:
        return None
    return iv_atm / rv_1m


def _median(xs: list) -> float:
    s = sorted(xs)
    m = len(s) // 2
    return s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2


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


def _doppelt(alle: list) -> bool:
    """Ein doppeltes Datum unter den normierten Zeilen bis S sperrt den GANZEN Ticker (Rang und Status)."""
    return len({e["date"] for e in alle}) != len(alle)


def _im_fenster(alle: list, session: str, fenster: int) -> list:
    """Zeilen mit S − W ≤ date (≤ S schon durch _normiert), nach Datum sortiert — EINE Regel für Rang und Status."""
    ab = (date.fromisoformat(session) - timedelta(days=fenster)).isoformat()
    return sorted((e for e in alle if ab <= e["date"]), key=lambda e: e["date"])


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
            "skew": e.get("skew_pts"), "cz": cz, "pz": pz, "ivrv": ivrv_wert(atm, e.get("rv_1m"))}


def _einzeln(reihe: list) -> dict | None:
    """reihe = [(datum, wert)] aufsteigend, nur gültige Werte; letzter muss die Session sein (vom Aufrufer geprüft)."""
    werte = [w for _, w in reihe]
    return {"n": len(werte), "rank": _rank(werte), "pctl": _pctl(werte), "wert": werte[-1]}


def _zusatz(reihe: list) -> dict:
    """neu_rand, vorher_datum, sprung bzw. sprung_beurteilbar für eine rankbare Reihe (n ≥ MIN_NORM)."""
    werte = [w for _, w in reihe]
    letzt, vor = werte[-1], werte[:-1]
    aus = {"vorher_datum": reihe[-2][0]}
    if letzt > max(vor):
        aus["neu_rand"] = "hoch"
    elif letzt < min(vor):
        aus["neu_rand"] = "tief"
    aend = [abs(b - a) for a, b in zip(werte, werte[1:])]
    med = _median(aend)
    if med == 0:
        aus["sprung_beurteilbar"] = False
    elif aend[-1] > SPRUNG_FAKTOR * med:
        aus["sprung"] = True
    return aus


def rang_ticker(arr: list, session: str, fenster: int) -> dict | None:
    """Rang je Metrik für EIN Fenster. None bei doppelten Daten; {} wenn keine Metrik die Bedingungen erfüllt."""
    alle = _normiert(arr, session)
    if _doppelt(alle):
        return None
    zeilen = _im_fenster(alle, session, fenster)
    daten = [e["date"] for e in zeilen]
    w = [(d, _werte(e)) for d, e in zip(daten, zeilen)]
    aus = {}
    for m in METRIKEN:
        reihe = [(d, v[m]) for d, v in w if gueltig(v[m])]
        if reihe and reihe[-1][0] == session and len(reihe) >= MIN_NORM:
            aus[m] = _einzeln(reihe)
            aus[m].update(_zusatz(reihe))
    paare = [(d, v["cz"], v["pz"]) for d, v in w if gueltig(v["cz"]) and gueltig(v["pz"])]
    if paare and paare[-1][0] == session and len(paare) >= MIN_NORM:
        cz, pz = _einzeln([(d, c) for d, c, _ in paare]), _einzeln([(d, p) for d, _, p in paare])
        aus["zeta"] = {"n": len(paare), "cz": {k: cz[k] for k in ("rank", "pctl", "wert")},
                       "pz": {k: pz[k] for k in ("rank", "pctl", "wert")}}
    return aus


def status_ticker(arr: list, session: str, fenster: int) -> dict:
    """Verfügbarkeit je Metrik OHNE Rang für EIN Fenster: {metrik: {n, status}}; Duplikat → {"*": {status: gesperrt}}.
    zu_kurz = Wert an S vorhanden, aber n < MIN_NORM; kein_wert = kein gültiger Wert an S (n = gültige davor)."""
    alle = _normiert(arr, session)
    if _doppelt(alle):
        return {"*": {"status": "gesperrt"}}
    if not alle:
        return {}
    zeilen = _im_fenster(alle, session, fenster)
    w = [(e["date"], _werte(e)) for e in zeilen]
    aus = {}
    for m in METRIKEN:
        reihe = [(d, v[m]) for d, v in w if gueltig(v[m])]
        if reihe and reihe[-1][0] == session:
            if len(reihe) < MIN_NORM:
                aus[m] = {"n": len(reihe), "status": "zu_kurz"}
        else:
            aus[m] = {"n": len(reihe), "status": "kein_wert"}
    return aus


def rang_status_gesamt(hist: dict, session: str) -> dict:
    """{ticker: {"92": {...}, …}} — nur Fenster mit mindestens einer Metrik ohne Rang; Ticker ohne normierte Zeile
    fehlen."""
    out = {}
    for t, arr in (hist or {}).items():
        if t.startswith("__") or not isinstance(arr, list):
            continue
        je = {}
        for f in FENSTER:
            s = status_ticker(arr, session, f)
            if s:
                je[str(f)] = s
        if je:
            out[t] = je
    return out


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

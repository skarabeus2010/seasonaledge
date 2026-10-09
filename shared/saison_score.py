"""
shared/saison_score.py — Saison-Score (Python-Zwilling von landing/js/saison-score.js)

Ersetzt den „KI-Score" (shared/ki_score.py). Plan v1–v3 mit Codex-Freigabe 2026-10-09:
docs/review_prompts/2026-10-09_saison_score_anomalie_plan.md (+ _v2, _v3).

EINE Definition für Scanner/Mails (hier) und Seiten (JS). Zeile für Zeile in derselben Reihenfolge gerechnet wie das
JS, damit die Ergebnisse bitgleich sind; geprüft von scripts/verify_saison_score.py (echtes JS in node gegen diese
Datei und gegen eine dritte, naive Referenz).

Kurzfassung (Details im JS-Kopf und im Plan):
  * Fenster as_of → +30 Kalendertage; Fensterrendite je Vorjahr aus Rohkursen (Start/Ende = letzte Kurszeile ≤ Ziel,
    29.02. → 28.02., Lückenheuristik T = 1 Krypto / 3 Forex / 7 Börse).
  * Lookback = 20 jüngste abgeschlossene Jahre mit Fenster und vollständigem Jahrespfad; mindestens 10.
  * B1/B2 aus allen Lookback-Jahren, B3/B4 aus den 5 Musterjahren (Pearson auf dem Jahrespfad, „Pfadähnlichkeit").
  * Score = 2,5 · (B1 + B2 + B3 + B4), halb aufwärts auf eine Stelle. Keine Richtungsetiketten.
  * Nicht berechenbar statt Ersatzwert (kein 0,5 mehr).
"""
from __future__ import annotations

import datetime as dt
import math

import bisect

METHODE = "saison_v1"
HORIZONT = 30
LOOKBACK = 20
MIN_JAHRE = 10
TOP_N = 5
MIN_HANDELSTAGE = 20
SPAETESTER_JAHRESSTART = 10
TOLERANZ = {"krypto": 1, "forex": 3, "boerse": 7}   # = SA.decadeCompute.ANOMALIE.TOLERANZ


def marktklasse(ticker) -> str:
    """Wortgleich mit SA.decadeCompute.marktklasse. Kein Ticker → Fehler (kein stiller Standard)."""
    if ticker is None or str(ticker).strip() == "":
        raise ValueError("Ticker fehlt")
    t = str(ticker).strip().upper()
    if t.endswith("-USD"):
        return "krypto"
    if t.endswith("=X"):
        return "forex"
    return "boerse"


def _epoch_tag(iso: str) -> int:
    return (dt.date.fromisoformat(iso[:10]) - dt.date(1970, 1, 1)).days


def _ziel_tag(y: int, m: int, d: int) -> int:
    letzter = ((dt.date(y + (m == 12), m % 12 + 1, 1)) - dt.timedelta(days=1)).day
    return (dt.date(y, m, min(d, letzter)) - dt.date(1970, 1, 1)).days


def _tag_nummer(iso: str) -> int:
    return dt.date.fromisoformat(iso[:10]).timetuple().tm_yday


def bereinigen(daten, closes, as_of: str | None = None):
    """Wie SA.decadeCompute._bereinigen: nicht-endlich/≤ 0 raus, doppelte Daten → letzter Wert, sortiert."""
    m = {}
    for d, c in zip(daten, closes):
        if d is None or c is None:
            continue
        try:
            c = float(c)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(c) or c <= 0:
            continue
        d = str(d)[:10]
        if as_of and d > as_of:
            continue
        m[d] = c
    ds = sorted(m)
    return ds, [m[d] for d in ds]


def pearson(a, b):
    """Zweistufig wie SA.saisonScore.pearson; None bei Streuung 0."""
    n = min(len(a), len(b))
    if n < 2:
        return None
    # Konstanz VOR der Mittelwertrechnung (Summationsrest; Codex Kern R1) — wie SA.saisonScore.pearson
    if min(a[:n]) == max(a[:n]) or min(b[:n]) == max(b[:n]):
        return None
    ma = 0.0
    mb = 0.0
    for i in range(n):
        ma += a[i]
        mb += b[i]
    ma /= n
    mb /= n
    sab = saa = sbb = 0.0
    for i in range(n):
        da = a[i] - ma
        db = b[i] - mb
        sab += da * db
        saa += da * da
        sbb += db * db
    if not saa > 0 or not sbb > 0:
        return None
    return sab / math.sqrt(saa * sbb)


def interp365(days, values):
    """Schnelle Fassung von shared.calculations.interpolate_to_365 — DIESELBE Formel (prev + w·(next − prev),
    w = (Ziel − prev)/(next − prev)), Tag 366 auf 365 gefaltet, außerhalb konstant. Statt linearer Suche je Zieltag
    binäre Suche: interpolate_to_365 braucht je Jahr ~365 × Länge Vergleiche, für die Validierung über tausende
    Stichtage zu langsam. Gleichheit (exakt, nicht auf Toleranz) prüft scripts/verify_saison_score.py."""
    if days and days[-1] > 365:
        keep = {}
        for d, v in zip(days, values):
            keep[min(d, 365)] = v
        days = sorted(keep)
        values = [keep[d] for d in days]
    out = []
    n = len(days)
    for ziel in range(1, 366):
        i = bisect.bisect_left(days, ziel)
        if i < n and days[i] == ziel:
            out.append(values[i])
        elif ziel < days[0]:
            out.append(values[0])
        elif ziel > days[-1]:
            out.append(values[-1])
        else:
            pv, nv = i - 1, i
            w = (ziel - days[pv]) / (days[nv] - days[pv])
            out.append(values[pv] + w * (values[nv] - values[pv]))
    return out


def _clip01(x):
    return 0.0 if x < 0 else (1.0 if x > 1 else x)


def _runden1(x):
    return math.floor(x * 10 + 0.5) / 10


def berechne(daten, closes, ticker, as_of: str | None = None) -> dict:
    klasse = marktklasse(ticker)
    T = TOLERANZ[klasse]
    asof_opt = str(as_of)[:10] if as_of else None
    ds, cs = bereinigen(daten, closes, asof_opt)
    n = len(ds)

    def aus(code, grund):
        return {"status": "nicht_berechenbar", "grund_code": code, "grund": grund, "methode": METHODE,
                "as_of": ds[-1] if n else None, "marktklasse": klasse, "score": None}

    if not n:
        return aus("keine_kurse", "keine Kurse")
    as_of_d = ds[-1]
    Y, mA, dA = int(as_of_d[:4]), int(as_of_d[5:7]), int(as_of_d[8:10])
    tage = [_epoch_tag(d) for d in ds]

    pro_jahr: dict[int, list[int]] = {}
    for i in range(n):
        pro_jahr.setdefault(int(ds[i][:4]), []).append(i)

    def pfad(y):
        idx = pro_jahr.get(y)
        if not idx or len(idx) < MIN_HANDELSTAGE:
            return None
        if int(ds[idx[0]][8:10]) > SPAETESTER_JAHRESSTART or int(ds[idx[0]][5:7]) != 1:
            return None
        c0 = cs[idx[0]]
        return interp365([_tag_nummer(ds[k]) for k in idx], [100 * cs[k] / c0 for k in idx])

    if Y not in pro_jahr or len(pro_jahr[Y]) < MIN_HANDELSTAGE:
        return aus("zu_frueh_im_jahr", "vor dem 20. Handelstag des Jahres")
    pfad_y = pfad(Y)
    if pfad_y is None:
        return aus("unvollstaendiges_jahr", "laufendes Jahr beginnt nach dem 10. Januar")
    d = min(_tag_nummer(as_of_d), 365)

    def bis_idx(ziel):
        lo, hi, best = 0, n - 1, -1
        while lo <= hi:
            mid = (lo + hi) >> 1
            if tage[mid] <= ziel:
                best = mid
                lo = mid + 1
            else:
                hi = mid - 1
        return best

    def fenster(y):
        z1 = _ziel_tag(y, mA, dA)
        z2 = z1 + HORIZONT
        s, e = bis_idx(z1), bis_idx(z2)
        if s < 0 or e <= s or z1 - tage[s] > T or z2 - tage[e] > T:
            return None
        for k in range(s + 1, e + 1):
            if tage[k] - tage[k - 1] > T:
                return None
        return (cs[e] / cs[s] - 1) * 100

    L = []
    erster_jahr = int(ds[0][:4])
    yy = Y - 1
    while yy >= erster_jahr and len(L) < LOOKBACK:
        py = pfad(yy)
        if py is not None:
            R = fenster(yy)
            if R is not None:
                L.append({"jahr": yy, "rendite": R, "pfad": py})
        yy -= 1
    if len(L) < MIN_JAHRE:
        return aus("zu_wenige_jahre", f"weniger als {MIN_JAHRE} Vergleichsjahre")

    cur = pfad_y[:d]
    kand = []
    for j in L:
        rr = pearson(cur, j["pfad"][:d])
        if rr is not None:
            kand.append({"jahr": j["jahr"], "r": rr, "rendite": j["rendite"]})
    kand.sort(key=lambda k: (-k["r"], -k["jahr"]))
    top = kand[:TOP_N]
    if len(top) < TOP_N:
        return aus("zu_wenige_musterjahre", f"weniger als {TOP_N} Musterjahre")
    W = 0.0
    WR = 0.0
    for t in top:
        w = (t["r"] + 1) / 2
        W += w
        WR += w * t["rendite"]
    if not W > 0:
        return aus("gewichte_null", "Gewichtssumme der Musterjahre 0")

    k1 = sum(1 for j in L if j["rendite"] > 0)
    summe = 0.0
    for j in L:
        summe += j["rendite"]
    mittel = summe / len(L)
    k3 = sum(1 for t in top if t["rendite"] > 0)
    mittel_w = WR / W
    b1 = k1 / len(L)
    b2 = _clip01((mittel + 3) / 6)
    b3 = k3 / len(top)
    b4 = _clip01((mittel_w + 3) / 6)
    roh = 2.5 * (b1 + b2 + b3 + b4)

    mittelpfad = []
    for t in range(d):
        sm = 0.0
        for q in range(len(L)):
            sm += L[q]["pfad"][t]
        mittelpfad.append(sm / len(L))
    bis = (dt.date(1970, 1, 1) + dt.timedelta(days=_epoch_tag(as_of_d) + HORIZONT)).isoformat()
    return {
        "status": "ok", "grund_code": None, "grund": None, "methode": METHODE, "as_of": as_of_d, "marktklasse": klasse,
        "fenster": {"von": as_of_d, "bis": bis, "tage": HORIZONT},
        "score": _runden1(roh), "score_roh": roh,
        "b1": {"wert": b1, "k": k1, "n": len(L)},
        "b2": {"wert": b2, "mittel": mittel},
        "b3": {"wert": b3, "k": k3, "n": len(top)},
        "b4": {"wert": b4, "mittel": mittel_w},
        "vergleich_ohne_matching": 5 * (b1 + b2),
        "jahre": [j["jahr"] for j in L],
        "musterjahre": top,
        "konformitaet": pearson(cur, mittelpfad),
    }
